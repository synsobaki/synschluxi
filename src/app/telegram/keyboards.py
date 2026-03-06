from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.utils.callbacks import pack


def access_gate_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔑 Ввести ключ", callback_data=pack("profile", "key_input", 0))
    b.button(text="📩 Запросить ключ", callback_data=pack("profile", "key_request", 0))
    b.adjust(1)
    return b.as_markup()


def menu_kb(continue_topic: tuple[int, str] | None = None, is_active: bool = True) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if continue_topic and is_active:
        topic_id, _ = continue_topic
        b.button(text="▶ Продолжить", callback_data=pack("topic", "open", topic_id))
    b.button(text="📘 Создать конспект", callback_data=pack("menu", "create", 0))
    b.button(text="📚 Ваши работы", callback_data=pack("menu", "works", 0))
    b.button(text="👤 Профиль", callback_data=pack("menu", "profile", 0))
    b.adjust(1)
    return b.as_markup()


def profile_kb(admin_url: str) -> InlineKeyboardMarkup:
    _ = admin_url
    b = InlineKeyboardBuilder()
    b.button(text="🔑 Ввести ключ", callback_data=pack("profile", "key_input", 0))
    b.button(text="📩 Запросить ключ", callback_data=pack("profile", "key_request", 0))
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def key_input_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅ Назад", callback_data=pack("nav", "back", 0))
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def key_request_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="👤 @mcknmf", url="https://t.me/mcknmf"))
    b.row(InlineKeyboardButton(text="👤 @Usikling", url="https://t.me/Usikling"))
    b.button(text="⬅ Назад", callback_data=pack("nav", "back", 0))
    b.adjust(1)
    return b.as_markup()


def topic_title_input_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📎 Загрузить файл", callback_data=pack("menu", "file", 0))
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def format_pick_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⚡ Кратко", callback_data=pack("topic", "format", f"{topic_id}|brief"))
    b.button(text="📚 Подробно", callback_data=pack("topic", "format", f"{topic_id}|detailed"))
    b.button(text="🧠 Простым языком", callback_data=pack("topic", "format", f"{topic_id}|simple"))
    b.button(text="📌 Шпаргалка", callback_data=pack("topic", "format", f"{topic_id}|cheat"))
    b.button(text="⬅ Назад", callback_data=pack("nav", "back", 0))
    b.adjust(1)
    return b.as_markup()


def topic_plan_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📘 Создать конспект", callback_data=pack("topic", "generate", topic_id))
    b.button(text="🔁 Перестроить план", callback_data=pack("topic", "plan_rebuild", topic_id))
    b.button(text="✏ Изменить тему", callback_data=pack("menu", "create", 0))
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def topic_card_kb(topic_id: int, has_many_sections: bool = False, section_idx: int = 0, at_last_section: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if has_many_sections:
        b.button(text="⬅ Предыдущий раздел", callback_data=pack("topic", "section", f"{topic_id}|{max(section_idx - 1, 0)}"))
        b.button(text="➡ Следующий раздел", callback_data=pack("topic", "section", f"{topic_id}|{section_idx + 1}"))
    b.button(text="✏ Изменить", callback_data=pack("topic", "edit", topic_id))
    if at_last_section:
        b.button(text="🧠 Пройти тест", callback_data=pack("test", "start", topic_id))
        b.button(text="📄 Скачать PDF", callback_data=pack("topic", "pdf", topic_id))
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(2, 1, 2, 1)
    return b.as_markup()


def topic_edit_kb(topic_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✂ Кратче", callback_data=pack("topic", "improve", f"{topic_id}|shorter"))
    b.button(text="📚 Больше", callback_data=pack("topic", "improve", f"{topic_id}|longer"))
    b.button(text="🧠 Переписать проще", callback_data=pack("topic", "improve", f"{topic_id}|rewrite"))
    b.button(text="⬅ Назад", callback_data=pack("topic", "open", topic_id))
    b.adjust(1)
    return b.as_markup()


def test_answers_kb(topic_id: int, options: list[str], q_idx: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for i, option in enumerate(options):
        b.button(text=option, callback_data=pack("test", "answer", f"{topic_id}|{q_idx}|{i}"))
    b.adjust(1)
    return b.as_markup()


def test_result_kb(topic_id: int, weak_section_id: str = "0") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📖 Разбор ответов", callback_data=pack("review", "nav", f"{topic_id}|0"))
    b.button(text="📖 Повторить слабый раздел", callback_data=pack("training", "open", f"{topic_id}|{weak_section_id}"))
    b.button(text="🔁 Пройти тест снова", callback_data=pack("test", "start", topic_id))
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def works_kb(topics: list, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for topic in topics:
        fmt = topic.fmt or "кратко"
        b.button(text=f"📄 {topic.title}\nКонспект • {fmt} • {topic.mastery}%", callback_data=pack("works", "open", topic.id))
    b.row(
        InlineKeyboardButton(text="⬅", callback_data=pack("works", "page", max(page - 1, 0))),
        InlineKeyboardButton(text="➡", callback_data=pack("works", "page", min(page + 1, max(total_pages - 1, 0)))),
    )
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(1)
    return b.as_markup()


def file_upload_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅ Назад", callback_data=pack("nav", "back", 0))
    return b.as_markup()


def key_review_kb(topic_id: int, idx: int, total: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if idx > 0:
        b.button(text="⬅", callback_data=pack("review", "nav", f"{topic_id}|{idx-1}"))
    if idx < total - 1:
        b.button(text="➡", callback_data=pack("review", "nav", f"{topic_id}|{idx+1}"))
    b.button(text="📖 Повторить слабый раздел", callback_data=pack("training", "open", f"{topic_id}|0"))
    b.button(text="🏠 В меню", callback_data=pack("nav", "menu", 0))
    b.adjust(2, 1, 1)
    return b.as_markup()
