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
        res = await self.one_screen.render(chat_id=chat_id, main_message_id=ui.main_message_id, text=text, keyboard=kb)
        if ui.main_message_id != res.message_id:
            await ui_repo.set_main_message_id(user_id, res.message_id)

    async def show_access_gate(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "access_gate", push_history=push_history)
        await UIStateRepo(session).set_awaiting(user_id, "key")
        user = await UserRepo(session).get_or_create(user_id)
        display_name = (user.first_name or "").strip() or (f"@{user.username}" if user.username else "")
        await self._render(session, chat_id, user_id, screens.access_gate_text(display_name), keyboards.access_gate_kb())

    async def show_request_key(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "key_request", push_history=push_history)
        await self._render(session, chat_id, user_id, screens.request_key_text(), keyboards.key_request_kb())

    async def show_menu(self, session: AsyncSession, chat_id: int, user_id: int, first_name: str = "", push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "menu", push_history=push_history)
        is_active = await UserRepo(session).is_active(user_id)
        if not is_active:
            return await self.show_access_gate(session, chat_id, user_id, push_history=False)
        user = await UserRepo(session).get_or_create(user_id)
        continue_topic = None
        candidate = await TopicRepo(session).get_continue_candidate(user_id)
        if candidate:
            continue_topic = (candidate.id, candidate.title)
        display_name = (user.first_name or first_name or "").strip()
        continue_title = candidate.title if candidate else None
        await self._render(session, chat_id, user_id, screens.menu_text(first_name=display_name, continue_title=continue_title, is_active=is_active), keyboards.menu_kb(continue_topic, is_active=is_active))

    async def show_profile(self, session: AsyncSession, chat_id: int, user_id: int, first_name: str = "", push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "profile", push_history=push_history)
        user = await UserRepo(session).get_or_create(user_id)
        is_active = await UserRepo(session).is_active(user_id)
        topics = await TopicRepo(session).list_recent(user_id, limit=100)
        avg = int(sum(t.mastery for t in topics) / len(topics)) if topics else 0
        if user.key_expires_at:
            expires = f"до {user.key_expires_at.strftime('%d.%m.%Y')}"
        elif user.active_key:
            expires = "бессрочный"
        else:
            expires = "бессрочный"
        text = screens.profile_text(first_name, is_active, mask_key(user.active_key) if user.active_key else None, expires, len(topics), avg)
        await self._render(session, chat_id, user_id, text, keyboards.profile_kb(admin_url=""))

    async def show_key_input(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "key_input", push_history=push_history)
        await UIStateRepo(session).set_awaiting(user_id, "key")
        await self._render(session, chat_id, user_id, screens.key_input_text(), keyboards.key_input_kb())

    async def show_key_request(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        return await self.show_request_key(session, chat_id, user_id, push_history=push_history)

    async def show_topic_input(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "topic_input", push_history=push_history)
        await UIStateRepo(session).set_awaiting(user_id, "topic_title")
        await self._render(session, chat_id, user_id, screens.topic_input_text(), keyboards.topic_title_input_kb())

    async def show_topic_title_input(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "topic_title_input", push_history=push_history)
        await UIStateRepo(session).set_awaiting(user_id, "topic_title")
        await self._render(session, chat_id, user_id, screens.topic_title_input_text(), keyboards.topic_title_input_kb())


    async def show_topic_title_confirm(self, session: AsyncSession, chat_id: int, user_id: int, raw_title: str, normalized_title: str, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "topic_title_confirm", push_history=push_history)
        await self._render(session, chat_id, user_id, screens.topic_title_confirm_text(raw_title, normalized_title), keyboards.topic_title_confirm_kb(raw_title, normalized_title))

    async def show_format_pick(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, title: str, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "topic_format", push_history=push_history)
        await self._render(session, chat_id, user_id, screens.format_pick_text(title), keyboards.format_pick_kb(topic_id))

    async def show_plan_preview(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, title: str, plan: list[str], push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "topic_plan", push_history=push_history)
        await self._render(session, chat_id, user_id, screens.topic_plan_text(title, plan), keyboards.topic_plan_kb(topic_id))

    async def show_topic_plan(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, title: str, push_history: bool = True, **_) -> None:
        return await self.show_plan_preview(session, chat_id, user_id, topic_id, title, plan=[], push_history=push_history)

    async def show_generation_status(self, session: AsyncSession, chat_id: int, user_id: int, step: int = 0, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "generation", push_history=push_history)
        await self._render(session, chat_id, user_id, screens.generation_status_text(step), kb=None)

    async def show_summary_section(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, section_idx: int = 0, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "topic_card", push_history=push_history)
        repo = TopicRepo(session)
        topic = await repo.get_by_id(user_id, int(topic_id))
        if not topic:
            return await self.show_works_list(session, chat_id, user_id, push_history=False)
        sections = repo.get_topic_sections(topic) or [{"title": "Материал готовится", "body": "Содержимое темы пока недоступно."}]
        idx = max(0, min(section_idx, len(sections) - 1))
        await repo.set_active_section(user_id, topic_id, idx)
        current = sections[idx]
        text = screens.summary_section_text(topic.title, topic.fmt or "базовый", topic.status, current.get("title", "Раздел"), current.get("body", ""), idx, len(sections))
        await self._render(session, chat_id, user_id, text, keyboards.topic_card_kb(topic.id, len(sections) > 1, idx, idx == len(sections)-1))

    async def show_topic_card(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, section_idx: int = 0, push_history: bool = True, **_) -> None:
        return await self.show_summary_section(session, chat_id, user_id, topic_id, section_idx, push_history)

    async def show_summary_edit_actions(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "topic_edit", push_history=push_history)
        await self._render(session, chat_id, user_id, "Как изменить текущий раздел?", keyboards.topic_edit_kb(topic_id))

    async def show_topic_edit(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, push_history: bool = True, **_) -> None:
        return await self.show_summary_edit_actions(session, chat_id, user_id, topic_id, push_history)

    async def show_works_list(self, session: AsyncSession, chat_id: int, user_id: int, page: int = 0, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "works", push_history=push_history)
        topics, total = await TopicRepo(session).list_page(user_id, page=page, page_size=5)
        total_pages = (total + 4) // 5 if total else 1
        items = [f"{t.title} | {t.category} | {t.status}" for t in topics]
        await self._render(session, chat_id, user_id, screens.works_text(items, page, total_pages), keyboards.works_kb(topics, page, total_pages))

    async def show_archive(self, session: AsyncSession, chat_id: int, user_id: int, page: int = 0, push_history: bool = True, **_) -> None:
        return await self.show_works_list(session, chat_id, user_id, page, push_history)

    async def show_test_question(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, q_idx: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "test", push_history=push_history)
        repo = TopicRepo(session)
        topic = await repo.get_by_id(user_id, topic_id)
        if not topic:
            return await self.show_works_list(session, chat_id, user_id, push_history=False)
        test = repo.get_topic_test(topic)
        idx = max(0, min(q_idx, len(test) - 1))
        question = test[idx]
        await self._render(session, chat_id, user_id, screens.test_question_text(topic.title, idx, len(test), str(question.get("question", ""))), keyboards.test_answers_kb(topic_id, [str(x) for x in question.get("options", [])], idx))

    async def show_test_result(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, score: int, total: int, weak_sections: list[str], push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "test_result", push_history=push_history)
        await self._render(session, chat_id, user_id, screens.test_result_text(score, total, weak_sections), keyboards.test_result_kb(topic_id, weak_sections[0] if weak_sections else "0"))

    async def show_weak_section_training(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, weak_section: str, training_text: str, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "weak_training", push_history=push_history)
        topic = await TopicRepo(session).get_by_id(user_id, topic_id)
        if not topic:
            return await self.show_works_list(session, chat_id, user_id, push_history=False)
        await self._render(session, chat_id, user_id, screens.weak_section_training_text(topic.title, weak_section, training_text), keyboards.test_result_kb(topic_id, weak_section))

    async def show_weak_training(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, weak_section: str = "Ключевые понятия", push_history: bool = True, **_) -> None:
        return await self.show_weak_section_training(session, chat_id, user_id, topic_id, weak_section, "Повторите базовые определения и решите мини-пример.", push_history)


    async def show_test_review(self, session: AsyncSession, chat_id: int, user_id: int, topic_id: int, idx: int = 0, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "test_review", push_history=push_history)
        topic = await TopicRepo(session).get_by_id(user_id, topic_id)
        if not topic:
            return await self.show_works_list(session, chat_id, user_id, push_history=False)
        from json import loads
        raw = topic.latest_test_result or "{}"
        data = loads(raw) if isinstance(raw, str) else (raw or {})
        review = data.get("review", []) if isinstance(data, dict) else []
        if not review:
            return await self.show_test_result(session, chat_id, user_id, topic_id, 0, 0, [], push_history=False)
        i = max(0, min(idx, len(review)-1))
        await self._render(session, chat_id, user_id, screens.test_review_text(review[i], i, len(review)), keyboards.key_review_kb(topic_id, i, len(review)))

    async def show_file_upload(self, session: AsyncSession, chat_id: int, user_id: int, push_history: bool = True, **_) -> None:
        await self._set_screen(session, user_id, "file_upload", push_history=push_history)
        await UIStateRepo(session).set_awaiting(user_id, "file_upload")
        await self._render(session, chat_id, user_id, screens.file_upload_text(), keyboards.file_upload_kb())

    async def show_by_screen(self, session: AsyncSession, chat_id: int, user_id: int, screen: str, first_name: str = "", push_history: bool = False, **_) -> None:
        if screen == "menu":
            return await self.show_menu(session, chat_id, user_id, first_name=first_name, push_history=push_history)
        if screen == "profile":
            return await self.show_profile(session, chat_id, user_id, first_name=first_name, push_history=push_history)
        if screen in {"key_input", "access_gate"}:
            return await self.show_access_gate(session, chat_id, user_id, push_history=push_history)
        if screen in {"archive", "works"}:
            return await self.show_works_list(session, chat_id, user_id, push_history=push_history)
        if screen == "file_upload":
            return await self.show_file_upload(session, chat_id, user_id, push_history=push_history)
        return await self.show_menu(session, chat_id, user_id, push_history=push_history)
