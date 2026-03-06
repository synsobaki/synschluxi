from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message


@dataclass
class RenderResult:
    message_id: int
    created_new: bool


class OneScreen:
    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def _is_recoverable_edit_error(msg: str) -> bool:
        """
        Только эти ошибки оправдывают создание нового main message.
        Всё остальное — баг в тексте/разметке/логике, его нельзя "лечить" спамом.
        """
        msg = msg.lower()

        recoverable_markers = [
            "message to edit not found",
            "message_id_invalid",
            "message identifier is not specified",
            "message can't be edited",
            "message cannot be edited",
        ]
        return any(m in msg for m in recoverable_markers)

    async def render(
        self,
        chat_id: int,
        main_message_id: Optional[int],
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
    ) -> RenderResult:
        # 1) Пытаемся редактировать существующее one-screen сообщение
        if main_message_id:
            try:
                await self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=main_message_id,
                    text=text,
                    reply_markup=keyboard,
                )
                return RenderResult(message_id=main_message_id, created_new=False)

            except TelegramBadRequest as e:
                msg = str(e)

                # "не изменилось" — это не ошибка: просто обновим клавиатуру
                if "message is not modified" in msg.lower():
                    try:
                        await self.bot.edit_message_reply_markup(
                            chat_id=chat_id,
                            message_id=main_message_id,
                            reply_markup=keyboard,
                        )
                    except TelegramBadRequest:
                        # если клавиатура тоже "не изменилась" — ок, просто молчим
                        pass
                    return RenderResult(message_id=main_message_id, created_new=False)

                # Создаём новое ТОЛЬКО если старое реально недоступно для редактирования
                if not self._is_recoverable_edit_error(msg):
                    # ВАЖНО: не плодим сообщения при ошибках HTML/лимитов/разметки/markup.
                    # Пусть упадёт — ты увидишь реальную причину и починишь.
                    raise

                # иначе: old message потеряно/не редактируется -> упадём в send_message ниже

        # 2) Создаём новое (первый запуск или старое сообщение реально недоступно)
        m: Message = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
        )
        return RenderResult(message_id=m.message_id, created_new=True)