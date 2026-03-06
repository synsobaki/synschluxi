from __future__ import annotations

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db_models import TopicRow


class TopicRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_draft(self, user_id: int, title: str) -> TopicRow:
        row = TopicRow(user_id=user_id, title=title.strip(), fmt="", status="draft", mastery=0)
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_by_id(self, user_id: int, topic_id: int) -> TopicRow | None:
        stmt = select(TopicRow).where(TopicRow.user_id == user_id, TopicRow.id == topic_id)
        return await self.session.scalar(stmt)

    async def set_format(self, user_id: int, topic_id: int, fmt: str) -> None:
        row = await self.get_by_id(user_id, topic_id)
        if not row:
            return
        row.fmt = fmt
        row.status = "in_progress"
        await self.session.flush()

    async def set_status(self, user_id: int, topic_id: int, status: str, mastery: int | None = None) -> None:
        row = await self.get_by_id(user_id, topic_id)
        if not row:
            return
        row.status = status
        if mastery is not None:
            row.mastery = mastery
        await self.session.flush()

    async def list_recent(self, user_id: int, limit: int = 10) -> list[TopicRow]:
        stmt = (
            select(TopicRow)
            .where(TopicRow.user_id == user_id)
            .order_by(desc(TopicRow.created_at))
            .limit(limit)
        )
        rows = await self.session.scalars(stmt)
        return list(rows.all())

    async def get_continue_candidate(self, user_id: int) -> TopicRow | None:
        stmt = (
            select(TopicRow)
            .where(TopicRow.user_id == user_id, TopicRow.status != "mastered")
            .order_by(desc(TopicRow.status == "draft"), desc(TopicRow.created_at))
            .limit(1)
        )
        return await self.session.scalar(stmt)
