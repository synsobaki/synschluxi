from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from src.infrastructure.db_models import KeyRow, KeyActivationRow, UserRow
from src.infrastructure.repositories.users import UserRepo
from src.services.access_service import normalize_key


class KeysRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_key(
        self,
        value: str,
        days_valid: int,
        max_uses: int,
        key_type: str = "multi",
    ) -> KeyRow:
        if key_type == "single":
            max_uses = 1
        row = KeyRow(
            value=normalize_key(value),
            days_valid=max(days_valid, 0),
            max_uses=max(max_uses, 1),
            used_count=0,
            created_at=datetime.utcnow(),
            key_type=key_type,
            is_disabled=0,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_by_key(self, value: str) -> KeyRow | None:
        value = normalize_key(value)
        result = await self.session.execute(select(KeyRow).where(KeyRow.value == value))
        return result.scalar_one_or_none()

    async def get_by_id(self, key_id: int) -> KeyRow | None:
        return await self.session.get(KeyRow, key_id)

    async def list_keys(self, limit: int = 50) -> list[KeyRow]:
        stmt = select(KeyRow).order_by(KeyRow.created_at.desc(), KeyRow.id.desc()).limit(max(1, limit))
        rows = await self.session.scalars(stmt)
        return list(rows.all())

    async def list_activations(self, key_id: int) -> list[tuple[KeyActivationRow, UserRow | None]]:
        stmt = (
            select(KeyActivationRow, UserRow)
            .outerjoin(UserRow, UserRow.id == KeyActivationRow.user_id)
            .where(KeyActivationRow.key_id == key_id)
            .order_by(KeyActivationRow.activated_at.desc())
        )
        rows = await self.session.execute(stmt)
        return list(rows.all())

    async def _record_activation(self, key_id: int, user_id: int) -> None:
        existing = await self.session.execute(
            select(KeyActivationRow).where(
                KeyActivationRow.key_id == key_id,
                KeyActivationRow.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            return
        self.session.add(KeyActivationRow(key_id=key_id, user_id=user_id, activated_at=datetime.utcnow()))
        await self.session.flush()

    async def activate_key(self, value: str, user_id: int) -> tuple[bool, KeyRow | None]:
        value = normalize_key(value)
        row = await self.get_by_key(value)
        if not row:
            return False, None

        now = datetime.utcnow()
        if row.is_disabled:
            return False, row
        if row.expires_at and row.expires_at < now:
            return False, row

        user = await UserRepo(self.session).get_or_create(user_id)
        if user.active_key == row.value and (user.key_expires_at is None or user.key_expires_at >= now):
            return True, row

        if row.used_count >= row.max_uses:
            return False, row

        row.used_count += 1
        expires_at = None if row.days_valid == 0 else now + timedelta(days=row.days_valid)
        await UserRepo(self.session).set_active(user_id=user_id, key_value=row.value, key_expires_at=expires_at)
        await self._record_activation(row.id, user_id)
        await self.session.flush()
        return True, row

    async def grant_key_to_user(self, key_id: int, user_id: int) -> tuple[bool, KeyRow | None]:
        row = await self.get_by_id(key_id)
        if not row:
            return False, None
        if row.is_disabled:
            return False, row
        if row.used_count >= row.max_uses:
            return False, row

        user = await UserRepo(self.session).get_or_create(user_id)
        now = datetime.utcnow()
        if user.active_key != row.value:
            row.used_count += 1
        expires_at = None if row.days_valid == 0 else now + timedelta(days=row.days_valid)
        await UserRepo(self.session).set_active(user_id=user_id, key_value=row.value, key_expires_at=expires_at)
        await self._record_activation(row.id, user_id)
        await self.session.flush()
        return True, row

    async def update_key(self, key_id: int, days_valid: int | None = None, max_uses: int | None = None, disable: bool | None = None) -> KeyRow | None:
        row = await self.get_by_id(key_id)
        if not row:
            return None
        if days_valid is not None:
            row.days_valid = max(0, days_valid)
        if max_uses is not None:
            row.max_uses = max(1, max_uses)
        if disable is not None:
            row.is_disabled = 1 if disable else 0
        await self.session.flush()
        return row

    async def extend_user_access(self, user_id: int, days: int) -> UserRow:
        return await UserRepo(self.session).extend_access(user_id, days)

    async def deactivate_user_access_by_key(self, key_value: str) -> list[int]:
        users = await UserRepo(self.session).list_by_active_key(key_value)
        ids = [u.id for u in users]
        for u in users:
            await UserRepo(self.session).clear_active(u.id)
        await self.session.flush()
        return ids

    async def delete_key(self, key_id: int) -> tuple[bool, str | None, list[int]]:
        row = await self.get_by_id(key_id)
        if not row:
            return False, None, []
        key_value = row.value
        affected_users = await self.deactivate_user_access_by_key(key_value)
        await self.session.execute(delete(KeyActivationRow).where(KeyActivationRow.key_id == key_id))
        await self.session.delete(row)
        await self.session.flush()
        return True, key_value, affected_users

    def key_status(self, row: KeyRow) -> str:
        now = datetime.utcnow()
        if row.is_disabled:
            return "отключён"
        if row.expires_at and row.expires_at < now:
            return "истёк"
        if row.used_count == 0:
            return "не использован"
        if row.used_count >= row.max_uses:
            return "исчерпан"
        if 0 < row.used_count < row.max_uses:
            return "частично использован"
        return "активен"
