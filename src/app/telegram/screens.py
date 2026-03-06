from __future__ import annotations


def menu_text() -> str:
    return "UMKOVO\nИнтеллектуальная система освоения тем"


def profile_text(
    first_name: str = "",
    is_active: bool = False,
    masked_key: str | None = None,
) -> str:
    status = "Активирован ✅" if is_active else "Не активирован ❌"
    key_line = masked_key or "—"
    return (
        "Профиль\n\n"
        f"Имя: {first_name}\n"
        f"Статус: {status}\n"
        f"Ключ: {key_line}\n"
    )


def key_input_text() -> str:
    return "Введите ключ активации.\nПример: UMK-XXXX-XXXX"


def key_request_text() -> str:
    return "Запросить ключ можно у администратора по кнопке ниже."


def archive_text() -> str:
    return "Архив пока пуст. Когда появятся темы — они будут здесь."


def topic_title_input_text() -> str:
    return "Создать конспект\n\nОтправь тему текстом.\nПример: «SQL JOIN’ы»"


def format_pick_text(title: str) -> str:
    return (
        "Формат конспекта\n\n"
        f"Тема: <b>{title}</b>\n\n"
        "Выбери формат:"
    )


def topic_card_text(title: str, fmt: str, status: str, mastery: int) -> str:
    fmt_map = {"deep": "Подробный разбор", "basics": "Основы темы", "cheat": "Шпаргалка", "": "—"}
    status_map = {
        "draft": "Draft",
        "attention": "Требует внимания",
        "in_progress": "В процессе",
        "mastered": "Освоено",
    }
    return (
        "Тема\n\n"
        f"Название: <b>{title}</b>\n"
        f"Формат: {fmt_map.get(fmt, fmt)}\n"
        f"Статус: {status_map.get(status, status)}\n"
        f"Mastery: {mastery}%\n\n"
        "Дальше будет: план → генерация разделов → тест."
    )
