from __future__ import annotations

import json
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db_models import TopicRow


class TopicRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_draft(self, user_id: int, title: str, category: str = "Общее") -> TopicRow:
        row = TopicRow(user_id=user_id, title=title.strip(), category=(category or "Общее").strip()[:64], fmt="", status="draft", mastery=0)
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

    async def save_generated_material(
        self,
        user_id: int,
        topic_id: int,
        content_sections: list[dict[str, str]],
        test_questions: list[dict[str, object]],
    ) -> TopicRow | None:
        row = await self.get_by_id(user_id, topic_id)
        if not row:
            return None
        row.content_json = json.dumps(content_sections, ensure_ascii=False)
        row.test_json = json.dumps(test_questions, ensure_ascii=False)
        row.status = "ready"
        row.mastery = max(row.mastery, 35)
        await self.session.flush()
        return row

    def get_topic_sections(self, row: TopicRow) -> list[dict[str, str]]:
        if not row.content_json:
            return []
        try:
            data = json.loads(row.content_json)
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
        except Exception:
            return []
        return []

    def get_topic_test(self, row: TopicRow) -> list[dict[str, object]]:
        if not row.test_json:
            return []
        try:
            data = json.loads(row.test_json)
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
        except Exception:
            return []
        return []

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


    async def list_page(self, user_id: int, page: int = 0, page_size: int = 5) -> tuple[list[TopicRow], int]:
        page = max(page, 0)
        page_size = max(1, page_size)
        stmt = (
            select(TopicRow)
            .where(TopicRow.user_id == user_id)
            .order_by(desc(TopicRow.created_at))
        )
        rows = list((await self.session.scalars(stmt)).all())
        total = len(rows)
        start = page * page_size
        end = start + page_size
        return rows[start:end], total
