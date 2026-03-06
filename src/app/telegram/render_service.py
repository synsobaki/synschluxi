from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.repositories.ui_state import UIStateRepo
from src.infrastructure.repositories.users import UserRepo
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

    async def _set_screen(
        self,
        session: AsyncSession,
        user_id: int,
        target_screen: str,
        push_history: bool,
    ) -> None:
        """
        ЕДИНАЯ логика переключения:
        - читаем текущий экран
        - если меняется: пушим текущий в history (если push_history)
        - ставим новый current_screen
        """
        ui_repo = UIStateRepo(session)
        ui = await ui_repo.get_or_create(user_id)

        current = ui.current_screen or "menu"
        if current != target_screen:
            if push_history:
                await ui_repo.push_history(user_id, current)
            await ui_repo.set_screen(user_id, target_screen)
        else:
            # экран тот же — ничего не пушим
            if push_history:
                # даже если попросили push_history, смысла нет:
                # иначе снова появится menu|menu|menu
                pass

    async def _render(
        self,
        session: AsyncSession,
        chat_id: int,
        user_id: int,
        text: str,
        kb,
    ) -> None:
        ui_repo = UIStateRepo(session)
        ui = await ui_repo.get_or_create(user_id)

        res = await self.one_screen.render(
            chat_id=chat_id,
            main_message_id=ui.main_message_id,
            text=text,
            keyboard=kb,
        )

        # если создали новое one-screen сообщение — сохраняем его id
        if ui.main_message_id != res.message_id:
            await ui_repo.set_main_message_id(user_id, res.message_id)

    async def show_menu(
        self,
        session: AsyncSession,
        chat_id: int,
        user_id: int,
        push_history: bool = True,
        **_,
    ) -> None:
        await self._set_screen(session, user_id, "menu", push_history=push_history)
        is_active = await UserRepo(session).is_active(user_id)
        text = screens.menu_text(is_active=is_active)
        kb = keyboards.menu_kb(is_active=is_active)
        await self._render(session, chat_id, user_id, text, kb)

    async def show_profile(
        self,
        session: AsyncSession,
        chat_id: int,
        user_id: int,
        first_name: str = "",
        push_history: bool = True,
        **_,
    ) -> None:
        await self._set_screen(session, user_id, "profile", push_history=push_history)

        user = await UserRepo(session).get_or_create(user_id)
        is_active = await UserRepo(session).is_active(user_id)

        text = screens.profile_text(
            first_name=first_name,
            is_active=is_active,
            masked_key=mask_key(user.active_key) if user.active_key else None,
        )

        admin_url = getattr(self.settings, "admin_url", None) or "https://t.me/umkovo_support"
        kb = keyboards.profile_kb(admin_url=admin_url)
        await self._render(session, chat_id, user_id, text, kb)

    async def show_key_input(
        self,
        session: AsyncSession,
        chat_id: int,
        user_id: int,
        push_history: bool = True,
        **_,
    ) -> None:
        await self._set_screen(session, user_id, "key_input", push_history=push_history)

        ui_repo = UIStateRepo(session)
        await ui_repo.set_awaiting(user_id, "key")

        text = screens.key_input_text()
        kb = keyboards.key_input_kb()
        await self._render(session, chat_id, user_id, text, kb)

    async def show_key_request(
        self,
        session: AsyncSession,
        chat_id: int,
        user_id: int,
        push_history: bool = True,
        **_,
    ) -> None:
        await self._set_screen(session, user_id, "key_request", push_history=push_history)
        # Запрос ключа реализован через URL-кнопку в профиле,
        # поэтому возвращаем пользователя на экран профиля.
        await self.show_profile(
            session=session,
            chat_id=chat_id,
            user_id=user_id,
            push_history=False,
        )

    async def show_archive(
        self,
        session: AsyncSession,
        chat_id: int,
        user_id: int,
        push_history: bool = True,
        **_,
    ) -> None:
        await self._set_screen(session, user_id, "archive", push_history=push_history)
        text = "📚 Архив пока пуст. Создай первый конспект из меню."
        kb = keyboards.key_input_kb()
        await self._render(session, chat_id, user_id, text, kb)

    async def show_by_screen(
        self,
        session: AsyncSession,
        chat_id: int,
        user_id: int,
        screen: str,
        first_name: str = "",
        push_history: bool = False,
        **_,
    ) -> None:
        if screen == "menu":
            return await self.show_menu(session, chat_id, user_id, push_history=push_history)
        if screen == "profile":
            return await self.show_profile(session, chat_id, user_id, first_name=first_name, push_history=push_history)
        if screen == "key_input":
            return await self.show_key_input(session, chat_id, user_id, push_history=push_history)
        if screen == "key_request":
            return await self.show_key_request(session, chat_id, user_id, push_history=push_history)
        if screen == "archive":
            return await self.show_archive(session, chat_id, user_id, push_history=push_history)

        return await self.show_menu(session, chat_id, user_id, push_history=push_history)
