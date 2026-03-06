from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db_models import UserRow


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int) -> UserRow:
        row = await self.session.get(UserRow, user_id)
        if row:
            return row
        row = UserRow(user_id=user_id, is_active=False, masked_key=None)
        self.session.add(row)
        await self.session.flush()
        return row

    async def set_active(self, user_id: int, masked_key: str) -> None:
        row = await self.get_or_create(user_id)
        row.is_active = True
        row.masked_key = masked_key
        await self.session.flush()