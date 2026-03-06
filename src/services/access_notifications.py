from __future__ import annotations

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def close_notice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Закрыть", callback_data="notify:close:0")]])


def access_changed_text(icon: str = "🔑", title: str = "Изменение доступа", body: str | None = None) -> str:
    details = body or "Ваш лицензионный ключ был обновлён администратором."
    return (
        f"{icon} {title}\n\n"
        f"{details}\n\n"
        "Если у вас есть вопросы, обратитесь в поддержку."
    )


async def notify_access_change(bot: Bot, user_id: int, icon: str = "🔑", title: str = "Изменение доступа", body: str | None = None) -> None:
    try:
        await bot.send_message(
            user_id,
            access_changed_text(icon=icon, title=title, body=body),
            reply_markup=close_notice_kb(),
        )
    except Exception:
        return
