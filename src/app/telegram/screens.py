from __future__ import annotations


def menu_text(is_active: bool = True) -> str:
    base = "UMKOVO\nИнтеллектуальная система освоения тем"
    if is_active:
        return base
    return f"{base}\n\nДля доступа к функциям активируй ключ в профиле."


def profile_text(
    first_name: str,
    is_active: bool,
    masked_key: str | None,
    topics_studied: int = 0,
    avg_result: int = 0,
) -> str:
    status = "активирован" if is_active else "не активирован"
    return (
        "Профиль\n\n"
        f"Имя: {first_name or 'Пользователь'}\n"
        f"Статус: {status}\n"
        f"Ключ: {masked_key or 'отсутствует'}\n\n"
        "Статистика:\n"
        f"Тем изучено: {topics_studied}\n"
        f"Средний результат: {avg_result}%"
    )


def key_input_text() -> str:
    return "Введите лицензионный ключ.\nПример: UMK-92F1-A7B3"


def key_request_text() -> str:
    return (
        "Чтобы получить доступ, свяжитесь с администратором.\n"
        "Нажмите кнопку ниже, чтобы написать администратору."
    )


def topic_title_input_text() -> str:
    return (
        "Введите тему, которую хотите изучить.\n\n"
        "Пример:\n"
        "• Метод Гаусса\n"
        "• Интерполяция Лагранжа\n"
        "• SQL индексы"
    )


def format_pick_text(title: str) -> str:
    return f"Тема: {title}\n\nВыберите формат изучения темы."


def topic_plan_text(title: str) -> str:
    return (
        f"План темы: {title}\n\n"
        "1) Основные понятия\n"
        "2) Теоретическая база\n"
        "3) Методы решения\n"
        "4) Примеры\n"
        "5) Итог"
    )


def generation_status_text() -> str:
    return (
        "Генерация конспекта...\n\n"
        "Статус:\n"
        "• Создание плана\n"
        "• Проверка достоверности\n"
        "• Формирование текста\n"
        "• Создание теста"
    )


def topic_card_text(title: str, fmt: str, status: str, mastery: int) -> str:
    format_map = {
        "short": "Краткий конспект",
        "full": "Полный конспект",
        "cheat": "Шпаргалка",
        "simple": "Простым языком",
    }
    return (
        f"Тема: {title}\n\n"
        "Определение\n"
        "Краткий структурированный материал будет показан здесь.\n\n"
        f"Формат: {format_map.get(fmt, fmt)}\n"
        f"Статус: {status}\n"
        f"Достоверность: {max(75, mastery)}%"
    )


def archive_text(items: list[str]) -> str:
    if not items:
        return "Архив\n\nСписок сохранённых тем пока пуст."
    rows = "\n".join(f"• {x}" for x in items)
    return f"Архив\n\n{rows}"
