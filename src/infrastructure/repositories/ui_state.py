from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db_models import UIStateRow


class UIStateRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int) -> UIStateRow:
        row = await self.session.get(UIStateRow, user_id)
        if row is None:
            row = UIStateRow(
                user_id=user_id,
                current_screen="menu",
                history_stack="",
                main_message_id=None,
                awaiting_input=None,
                awaiting_meta_json=None,
            )
            self.session.add(row)
            # flush не обязателен — commit сделает middleware
        return row

    async def set_main_message_id(self, user_id: int, message_id: int) -> None:
        row = await self.get_or_create(user_id)
        row.main_message_id = message_id
        row.updated_at = datetime.utcnow()

    async def set_screen(self, user_id: int, screen: str) -> None:
        row = await self.get_or_create(user_id)
        row.current_screen = screen
        row.updated_at = datetime.utcnow()

    async def set_awaiting(
        self,
        user_id: int,
        awaiting: Optional[str],
        meta: Optional[dict[str, Any]] = None,
    ) -> None:
        row = await self.get_or_create(user_id)
        row.awaiting_input = awaiting
        row.awaiting_meta_json = json.dumps(meta, ensure_ascii=False) if meta is not None else None
        row.updated_at = datetime.utcnow()

    def _split_stack(self, s: Optional[str]) -> List[str]:
        return [x for x in (s or "").split("|") if x]

    def _join_stack(self, items: List[str]) -> str:
        return "|".join(items)

    async def push_history(self, user_id: int, screen: str) -> None:
        """
        В историю кладём ПРЕДЫДУЩИЙ экран.
        Не кладём одинаковый подряд.
        """
        row = await self.get_or_create(user_id)
        stack = self._split_stack(row.history_stack)

        if stack and stack[-1] == screen:
            return

        stack.append(screen)
        row.history_stack = self._join_stack(stack[-30:])
        row.updated_at = datetime.utcnow()

    async def pop_history(self, user_id: int) -> Optional[str]:
        """
        Достаём последний экран (куда вернуться).
        """
        row = await self.get_or_create(user_id)
        stack = self._split_stack(row.history_stack)
        if not stack:
            return None

        last = stack.pop()
        row.history_stack = self._join_stack(stack)
        row.updated_at = datetime.utcnow()
        return last