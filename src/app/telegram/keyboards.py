from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.utils.callbacks import pack


def menu_kb(
    continue_topic: tuple[int, str] | None = None,
    is_active: bool = True,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    if continue_topic and is_active:
        topic_id, title = continue_topic
        b.button(text=f"▶ Продолжить: {title}", callback_data=pack("topic", "open", topic_id))

    b.button(text="📘 Создать конспект", callback_data=pack("menu", "create", 0))
    b.button(text="📚 Архив", callback_data=pack("menu", "archive", 0))
    b.button(text="👤 Профиль", callback_data=pack("menu", "profile", 0))
    b.adjust(1)
    return b.as_markup()


def profile_kb(admin_url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔑 Ввести ключ", callback_data=pack("profile", "key_input", 0))
    b.row(InlineKeyboardButton(text="📩 Запросить ключ", callback_data=pack("profile", "key_request", 0)))
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def key_input_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="◀ Назад", callback_data=pack("nav", "back", 0))
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def topic_title_input_kb() -> InlineKeyboardMarkup:
    return key_input_kb()


def format_pick_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📄 Краткий конспект", callback_data=pack("topic", "format", f"{topic_id}|short"))
    b.button(text="📚 Полный конспект", callback_data=pack("topic", "format", f"{topic_id}|full"))
    b.button(text="🗒 Шпаргалка", callback_data=pack("topic", "format", f"{topic_id}|cheat"))
    b.button(text="💬 Простым языком", callback_data=pack("topic", "format", f"{topic_id}|simple"))
    b.button(text="◀ Назад", callback_data=pack("nav", "back", 0))
    b.adjust(1)
    return b.as_markup()


def topic_plan_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🚀 Сгенерировать конспект", callback_data=pack("topic", "generate", topic_id))
    b.button(text="✏ Изменить тему", callback_data=pack("menu", "create", 0))
    b.button(text="◀ Назад", callback_data=pack("nav", "back", 0))
    b.adjust(1)
    return b.as_markup()


def topic_card_kb(topic_id: int, has_many_sections: bool = False, section_idx: int = 0) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if has_many_sections:
        b.button(text="◀ Назад", callback_data=pack("topic", "section", f"{topic_id}|{max(section_idx - 1, 0)}"))
        b.button(text="▶ Далее", callback_data=pack("topic", "section", f"{topic_id}|{section_idx + 1}"))
    b.button(text="🧪 Пройти тест", callback_data=pack("test", "start", topic_id))
    b.button(text="🗂 В архив", callback_data=pack("menu", "archive", 0))
    b.button(text="✨ Улучшить", callback_data=pack("topic", "improve", topic_id))
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(2, 1, 1, 1)
    return b.as_markup()


def test_answers_kb(topic_id: int, options: list[str], q_idx: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for i, option in enumerate(options):
        b.button(text=option, callback_data=pack("test", "answer", f"{topic_id}|{q_idx}|{i}"))
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def test_result_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔁 Пройти ещё раз", callback_data=pack("test", "start", topic_id))
    b.button(text="📖 Повторить слабый раздел", callback_data=pack("topic", "open", topic_id))
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def archive_kb(topic_id: int | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if topic_id:
        b.button(text="📂 Открыть тему", callback_data=pack("topic", "open", topic_id))
        b.button(text="🧪 Пройти тест", callback_data=pack("test", "start", topic_id))
    else:
        b.button(text="📂 Открыть тему", callback_data=pack("topic", "open_last", 0))
    b.button(text="◀ Назад", callback_data=pack("nav", "back", 0))
    b.adjust(1)
    return b.as_markup()
