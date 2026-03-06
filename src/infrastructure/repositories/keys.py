from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.infrastructure.db_models import KeyRow
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
    ) -> None:
        row = KeyRow(
            value=value,
            days_valid=days_valid,
            max_uses=max_uses,
            used_count=0,
            created_at=datetime.utcnow(),
        )
        self.session.add(row)
        await self.session.flush()

    async def get_by_key(self, value: str) -> KeyRow | None:
        value = normalize_key(value)
        result = await self.session.execute(
            select(KeyRow).where(KeyRow.value == value)
        )
        return result.scalar_one_or_none()

    async def activate_key(self, value: str, user_id: int) -> bool:
        value = normalize_key(value)
        row = await self.get_by_key(value)
        if not row:
            return False

        now = datetime.utcnow()

        # проверка срока действия
        if row.expires_at and row.expires_at < now:
            return False

        # если пользователь уже активировал этот же ключ — считаем успехом
        user = await UserRepo(self.session).get_or_create(user_id)
        if user.active_key == row.value:
            if user.key_expires_at is None or user.key_expires_at >= now:
                return True

        # проверка лимита
        if row.used_count >= row.max_uses:
            return False

        row.used_count += 1

        # реальный срок для конкретного пользователя
        expires_at = now + timedelta(days=row.days_valid)
        await UserRepo(self.session).set_active(
            user_id=user_id,
            key_value=row.value,
            key_expires_at=expires_at,
        )

        await self.session.flush()
        return True
