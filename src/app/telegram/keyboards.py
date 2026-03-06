from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.utils.callbacks import pack, Act


def menu_kb(
    continue_topic: tuple[int, str] | None = None,
    is_active: bool = True,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    if not is_active:
        b.button(text="👤 Профиль", callback_data=pack(Act.PROF))
        b.adjust(1)
        return b.as_markup()

    if continue_topic:
        topic_id, title = continue_topic
        b.button(text=f"▶ Продолжить: {title}", callback_data=pack(Act.CONT, topic_id))
        b.adjust(1)

    b.button(text="➕ Создать конспект", callback_data=pack(Act.NEW))
    b.button(text="📚 Архив", callback_data=pack(Act.ARCH))
    b.button(text="👤 Профиль", callback_data=pack(Act.PROF))
    b.adjust(1)
    return b.as_markup()


def profile_kb(admin_url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔑 Ввести ключ", callback_data=pack(Act.KEY))
    b.row(InlineKeyboardButton(text="📩 Запросить ключ", url=admin_url))
    b.button(text="🏠 В меню", callback_data=pack(Act.MENU))
    b.adjust(1)
    return b.as_markup()


def key_input_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="◀ Назад", callback_data=pack(Act.BACK)),
        InlineKeyboardButton(text="🏠 В меню", callback_data=pack(Act.MENU)),
    )
    return b.as_markup()


def topic_title_input_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="◀ Назад", callback_data=pack(Act.BACK)),
        InlineKeyboardButton(text="🏠 В меню", callback_data=pack(Act.MENU)),
    )
    return b.as_markup()


def format_pick_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    # <=4 контекстных кнопок
    b.button(text="🔍 Подробный разбор", callback_data=pack(Act.FMT, topic_id, "deep"))
    b.button(text="📖 Основы темы", callback_data=pack(Act.FMT, topic_id, "basics"))
    b.button(text="📝 Шпаргалка", callback_data=pack(Act.FMT, topic_id, "cheat"))
    b.adjust(1)
    b.row(
        InlineKeyboardButton(text="◀ Назад", callback_data=pack(Act.BACK)),
        InlineKeyboardButton(text="🏠 В меню", callback_data=pack(Act.MENU)),
    )
    return b.as_markup()


def topic_card_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    # пока заглушка: только меню
    b.button(text="🏠 В меню", callback_data=pack(Act.MENU))
    b.adjust(1)
    return b.as_markup()
