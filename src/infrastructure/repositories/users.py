from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db_models import UserRow


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int) -> UserRow:
        row = await self.session.get(UserRow, user_id)
        if row:
            return row
        row = UserRow(id=user_id, active_key=None, key_expires_at=None)
        self.session.add(row)
        await self.session.flush()
        return row

    async def set_active(self, user_id: int, key_value: str, key_expires_at: datetime | None) -> None:
        row = await self.get_or_create(user_id)
        row.active_key = key_value
        row.key_expires_at = key_expires_at
        await self.session.flush()

    async def is_active(self, user_id: int) -> bool:
        row = await self.get_or_create(user_id)
        if not row.active_key:
            return False
        if row.key_expires_at and row.key_expires_at < datetime.utcnow():
            return False
        return True
