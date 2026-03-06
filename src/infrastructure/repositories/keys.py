from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.infrastructure.db_models import KeyRow


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
        result = await self.session.execute(
            select(KeyRow).where(KeyRow.value == value)
        )
        return result.scalar_one_or_none()

    async def activate_key(self, value: str, user_id: int) -> bool:
        row = await self.get_by_key(value)
        if not row:
            return False

        # проверка лимита
        if row.used_count >= row.max_uses:
            return False

        row.used_count += 1

        await self.session.flush()
        return True
