from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db_models import UserRow


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int, first_name: str | None = None, username: str | None = None) -> UserRow:
        row = await self.session.get(UserRow, user_id)
        if row:
            changed = False
            if first_name and row.first_name != first_name:
                row.first_name = first_name
                changed = True
            if username and row.username != username:
                row.username = username
                changed = True
            if changed:
                await self.session.flush()
            return row
        row = UserRow(id=user_id, first_name=first_name, username=username, active_key=None, key_expires_at=None)
        self.session.add(row)
        await self.session.flush()
        return row

    async def find_by_identity(self, query: str) -> UserRow | None:
        q = (query or "").strip().lstrip("@")
        if not q:
            return None
        if q.isdigit():
            return await self.session.get(UserRow, int(q))
        stmt = select(UserRow).where(UserRow.username == q)
        return await self.session.scalar(stmt)

    async def list_users(self, limit: int = 50) -> list[UserRow]:
        stmt = select(UserRow).order_by(UserRow.created_at.desc(), UserRow.id.desc()).limit(max(1, limit))
        rows = await self.session.scalars(stmt)
        return list(rows.all())

    async def list_by_active_key(self, key_value: str) -> list[UserRow]:
        stmt = select(UserRow).where(UserRow.active_key == key_value)
        rows = await self.session.scalars(stmt)
        return list(rows.all())

    async def set_active(self, user_id: int, key_value: str, key_expires_at: datetime | None) -> None:
        row = await self.get_or_create(user_id)
        row.active_key = key_value
        row.key_expires_at = key_expires_at
        await self.session.flush()

    async def clear_active(self, user_id: int) -> None:
        row = await self.get_or_create(user_id)
        row.active_key = None
        row.key_expires_at = None
        await self.session.flush()

    async def extend_access(self, user_id: int, days: int) -> UserRow:
        row = await self.get_or_create(user_id)
        now = datetime.utcnow()
        base = row.key_expires_at if row.key_expires_at and row.key_expires_at > now else now
        row.key_expires_at = base + timedelta(days=max(1, days))
        await self.session.flush()
        return row

    async def is_active(self, user_id: int) -> bool:
        row = await self.get_or_create(user_id)
        if not row.active_key:
            return False
        if row.key_expires_at and row.key_expires_at < datetime.utcnow():
            return False
        return True
