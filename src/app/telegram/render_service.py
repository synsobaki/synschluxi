from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.repositories.ui_state import UIStateRepo
from src.infrastructure.repositories.users import UserRepo
from src.infrastructure.repositories.topics import TopicRepo
from src.services.access_service import mask_key
from src.app.telegram.one_screen import OneScreen
from src.app.telegram import screens, keyboards


@dataclass
class RenderContext:
    chat_id: int
    user_id: int
    first_name: str = ""


class RenderService:
    def __init__(self, one_screen: OneScreen, settings: Optional[Any] = None):
        self.one_screen = one_screen
        self.settings = settings

    async def _set_screen(self, session: AsyncSession, user_id: int, target_screen: str, push_history: bool) -> None:
        ui_repo = UIStateRepo(session)
        ui = await ui_repo.get_or_create(user_id)
        current = ui.current_screen or "menu"
        if current != target_screen:
            if push_history:
                await ui_repo.push_history(user_id, current)
            await ui_repo.set_screen(user_id, target_screen)

    async def _render(self, session: AsyncSession, chat_id: int, user_id: int, text: str, kb) -> None:
        ui_repo = UIStateRepo(session)
        ui = await ui_repo.get_or_create(user_id)

        res = await self.one_screen.render(
            chat_id=chat_id,
            main_message_id=ui.main_message_id,
            text=text,
            keyboard=kb,
        )

        if ui.main_message_id != res.message_id:
            await ui_repo.set_main_message_id(user_id, res.message_id)

    async def show_menu(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "menu", push_history=push_history)
        is_active = await UserRepo(session).is_active(user_id)
        continue_topic = None
        if is_active:
            candidate = await TopicRepo(session).get_continue_candidate(user_id)
            if candidate:
                continue_topic = (candidate.id, candidate.title)
        text = screens.menu_text(is_active=is_active)
        kb = keyboards.menu_kb(continue_topic=continue_topic, is_active=is_active)
        await self._render(session, chat_id, user_id, text, kb)

    async def show_profile(self, session: AsyncSession, chat_id: int, user_id: int, first_name: str = "", push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "profile", push_history=push_history)

        user = await UserRepo(session).get_or_create(user_id)
        is_active = await UserRepo(session).is_active(user_id)
        topics = await TopicRepo(session).list_recent(user_id, limit=100)
        avg = int(sum(t.mastery for t in topics) / len(topics)) if topics else 0

        text = screens.profile_text(
            first_name=first_name,
            is_active=is_active,
            masked_key=mask_key(user.active_key) if user.active_key else None,
            topics_studied=len(topics),
            avg_result=avg,
        )

        admin_url = getattr(self.settings, "admin_url", None) or "https://t.me/umkovo_support"
        kb = keyboards.profile_kb(admin_url=admin_url)
        await self._render(session, chat_id, user_id, text, kb)

    async def show_key_input(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "key_input", push_history=push_history)
        await UIStateRepo(session).set_awaiting(user_id, "key")
        await self._render(session, chat_id, user_id, screens.key_input_text(), keyboards.key_input_kb())

    async def show_key_request(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "key_request", push_history=push_history)
        admin_url = getattr(self.settings, "admin_url", None) or "https://t.me/umkovo_support"
        await self._render(session, chat_id, user_id, screens.key_request_text(), keyboards.profile_kb(admin_url))

    async def show_archive(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "archive", push_history=push_history)
        topics = await TopicRepo(session).list_recent(user_id)
        items = [f"{t.title} — {t.mastery}%" for t in topics]
        await self._render(session, chat_id, user_id, screens.archive_text(items), keyboards.archive_kb())

    async def show_topic_title_input(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "topic_title_input", push_history=push_history)
        await UIStateRepo(session).set_awaiting(user_id, "topic_title")
        await self._render(session, chat_id, user_id, screens.topic_title_input_text(), keyboards.topic_title_input_kb())

    async def show_format_pick(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, title: str, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "topic_format", push_history=push_history)
        await self._render(session, chat_id, user_id, screens.format_pick_text(title), keyboards.format_pick_kb(topic_id))

    async def show_topic_plan(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, title: str, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "topic_plan", push_history=push_history)
        await self._render(session, chat_id, user_id, screens.topic_plan_text(title), keyboards.topic_plan_kb(topic_id))

    async def show_generation_status(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "generation", push_history=push_history)
        await self._render(session, chat_id, user_id, screens.generation_status_text(), kb=None)

    async def show_topic_card(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "topic_card", push_history=push_history)
        topic = await TopicRepo(session).get_by_id(user_id, int(topic_id))
        if not topic:
            await self.show_archive(session, chat_id, user_id, push_history=False)
            return
        text = screens.topic_card_text(topic.title, topic.fmt, topic.status, topic.mastery)
        await self._render(session, chat_id, user_id, text, keyboards.topic_card_kb(topic.id))

    async def show_by_screen(self, session: AsyncSession, chat_id: int, user_id: int, screen: str, first_name: str = "", push_history: bool = False, **_) -> None:
        if screen == "menu":
            return await self.show_menu(session, chat_id, user_id, push_history=push_history)
        if screen == "profile":
            return await self.show_profile(session, chat_id, user_id, first_name=first_name, push_history=push_history)
        if screen == "key_input":
            return await self.show_key_input(session, chat_id, user_id, push_history=push_history)
        if screen == "archive":
            return await self.show_archive(session, chat_id, user_id, push_history=push_history)
        return await self.show_menu(session, chat_id, user_id, push_history=push_history)
