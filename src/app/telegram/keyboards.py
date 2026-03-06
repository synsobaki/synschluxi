from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.utils.callbacks import pack


def menu_kb(continue_topic: tuple[int, str] | None = None, is_active: bool = True) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if continue_topic and is_active:
        topic_id, title = continue_topic
        b.button(text=f"▶ Продолжить: {title}", callback_data=pack("topic", "open", topic_id))
    b.button(text="📘 Создать конспект", callback_data=pack("menu", "create", 0))
    b.button(text="📎 Конспект из файла", callback_data=pack("menu", "file", 0))
    b.button(text="📚 Ваши работы", callback_data=pack("menu", "archive", 0))
    b.button(text="👤 Профиль", callback_data=pack("menu", "profile", 0))
    b.adjust(1)
    return b.as_markup()


def profile_kb(admin_url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔑 Ввести ключ", callback_data=pack("profile", "key_input", 0))
    b.row(InlineKeyboardButton(text="📩 Запросить ключ", callback_data=pack("profile", "key_request", 0)))
    b.button(text="🏠 Меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def key_input_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="◀ Назад", callback_data=pack("nav", "back", 0))
    b.button(text="🏠 Меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def key_request_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="@mcknmf", url="https://t.me/mcknmf"))
    b.row(InlineKeyboardButton(text="@Usikling", url="https://t.me/Usikling"))
    b.button(text="◀ Назад", callback_data=pack("nav", "back", 0))
    b.adjust(1)
    return b.as_markup()


def topic_title_input_kb() -> InlineKeyboardMarkup:
    return key_input_kb()


def format_pick_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="кратко", callback_data=pack("topic", "format", f"{topic_id}|short"))
    b.button(text="подробно", callback_data=pack("topic", "format", f"{topic_id}|full"))
    b.button(text="простым языком", callback_data=pack("topic", "format", f"{topic_id}|simple"))
    b.button(text="шпаргалка", callback_data=pack("topic", "format", f"{topic_id}|cheat"))
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


def topic_card_kb(topic_id: int, has_many_sections: bool = False, section_idx: int = 0, at_last_section: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if has_many_sections:
        b.button(text="◀ Раздел", callback_data=pack("topic", "section", f"{topic_id}|{max(section_idx - 1, 0)}"))
        b.button(text="Раздел ▶", callback_data=pack("topic", "section", f"{topic_id}|{section_idx + 1}"))
    b.button(text="✏ Изменить", callback_data=pack("topic", "edit", topic_id))
    if at_last_section:
        b.button(text="🧪 Пройти тест", callback_data=pack("test", "start", topic_id))
    b.button(text="📄 Скачать PDF", callback_data=pack("topic", "pdf", topic_id))
    b.button(text="🗂 Ваши работы", callback_data=pack("menu", "archive", 0))
    b.button(text="🏠 Меню", callback_data=pack("nav", "menu", 0))
    b.adjust(2, 1, 1, 1)
    return b.as_markup()


def topic_edit_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Кратче", callback_data=pack("topic", "improve", f"{topic_id}|short"))
    b.button(text="Больше", callback_data=pack("topic", "improve", f"{topic_id}|full"))
    b.button(text="Переписать", callback_data=pack("topic", "improve", f"{topic_id}|simple"))
    b.button(text="◀ Назад", callback_data=pack("topic", "open", topic_id))
    b.adjust(1)
    return b.as_markup()


def test_answers_kb(topic_id: int, options: list[str], q_idx: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for i, option in enumerate(options):
        b.button(text=option, callback_data=pack("test", "answer", f"{topic_id}|{q_idx}|{i}"))
    b.button(text="🏠 Меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def test_result_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📖 Обучить слабое место", callback_data=pack("test", "train", topic_id))
    b.button(text="🔁 Повторный тест", callback_data=pack("test", "start", topic_id))
    b.button(text="🏠 Меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def archive_kb(topic_id: int | None = None, page: int = 0, has_prev: bool = False, has_next: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if topic_id:
        b.button(text="📂 Открыть тему", callback_data=pack("topic", "open", topic_id))
    if has_prev:
        b.button(text="⬅", callback_data=pack("archive", "page", page - 1))
    if has_next:
        b.button(text="➡", callback_data=pack("archive", "page", page + 1))
    b.button(text="◀ Назад", callback_data=pack("nav", "back", 0))
    b.adjust(1, 2, 1)
    return b.as_markup()


def topic_details_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📘 Открыть конспект", callback_data=pack("topic", "open", topic_id))
    b.button(text="🔁 Повторить тему", callback_data=pack("test", "start", topic_id))
    b.button(text="◀ Назад", callback_data=pack("menu", "archive", 0))
    b.adjust(1)
    return b.as_markup()


def file_upload_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="◀ Назад", callback_data=pack("nav", "back", 0))
    b.adjust(1)
    return b.as_markup()


def compress_mode_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="100 слов", callback_data=pack("file", "words", f"{topic_id}|100"))
    b.button(text="300 слов", callback_data=pack("file", "words", f"{topic_id}|300"))
    b.button(text="500 слов", callback_data=pack("file", "words", f"{topic_id}|500"))
    b.button(text="50%", callback_data=pack("file", "percent", f"{topic_id}|50"))
    b.button(text="75%", callback_data=pack("file", "percent", f"{topic_id}|75"))
    b.button(text="90%", callback_data=pack("file", "percent", f"{topic_id}|90"))
    b.button(text="◀ Назад", callback_data=pack("nav", "back", 0))
    b.adjust(3, 3, 1)
    return b.as_markup()
