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
        await self.session.flush()  # получим row.id
        return row

    async def get_by_id(self, user_id: int, topic_id: int) -> TopicRow | None:
        stmt = select(TopicRow).where(TopicRow.user_id == user_id, TopicRow.id == topic_id)
        return await self.session.scalar(stmt)

    async def set_format(self, user_id: int, topic_id: int, fmt: str) -> None:
        row = await self.get_by_id(user_id, topic_id)
        if not row:
            return
        row.fmt = fmt
        await self.session.flush()

    async def get_continue_candidate(self, user_id: int) -> TopicRow | None:
        # сначала draft, потом in_progress/attention (mastered не показываем)
        stmt = (
            select(TopicRow)
            .where(TopicRow.user_id == user_id, TopicRow.status != "mastered")
            .order_by(
                desc(TopicRow.status == "draft"),  # draft сверху
                desc(TopicRow.created_at),
            )
            .limit(1)
        )
        return await self.session.scalar(stmt)