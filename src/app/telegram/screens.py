from __future__ import annotations


def menu_text(is_active: bool = True) -> str:
    base = (
        "✨ UMKOVO\n"
        "AI-репетитор: помогаю понять тему, закрепить знания и найти слабые места."
    )
    if is_active:
        return f"{base}\n\nВыбери действие 👇"
    return f"{base}\n\nДля доступа активируйте лицензионный ключ 🔑"


def profile_text(
    first_name: str,
    is_active: bool,
    masked_key: str | None,
    expires_at: str | None,
    topics_studied: int = 0,
    avg_result: int = 0,
) -> str:
    status = "🟢 Активен" if is_active else "🔴 Не активен"
    key_status = "✅ Подключён" if masked_key else "❌ Не подключён"
    return (
        "👤 Профиль\n\n"
        f"Имя: {first_name or 'Пользователь'}\n"
        f"Статус доступа: {status}\n"
        f"Ключ: {masked_key or 'отсутствует'} ({key_status})\n"
        f"Срок ключа: {expires_at or 'не задан'}\n\n"
        f"Количество тем: {topics_studied}\n"
        f"Средний прогресс: {avg_result}%"
    )


def key_input_text() -> str:
    return (
        "🔐 Доступ к UMKOVO\n\n"
        "Для использования бота нужен лицензионный ключ.\n\n"
        "Введите лицензионный ключ\n"
        "Формат: UMK-####-####"
    )


def key_request_text() -> str:
    return (
        "Чтобы получить ключ:\n"
        "1. Напишите администратору\n"
        "2. Запросите лицензионный ключ\n"
        "3. Введите его в боте"
    )


def topic_title_input_text() -> str:
    return (
        "📘 Создание конспекта\n\n"
        "Введите тему, которую хотите изучить."
    )


def format_pick_text(title: str) -> str:
    return f"🧩 Тема: {title}\n\nВыберите формат конспекта."


def topic_plan_text(title: str) -> str:
    return (
        f"🗺 План темы: {title}\n\n"
        "1) Основные понятия\n"
        "2) Теория\n"
        "3) Алгоритм\n"
        "4) Пример\n"
        "5) Итог"
    )


def generation_status_text(step: int = 0) -> str:
    steps = [
        "🧠 Анализируем тему",
        "📝 Формируем структуру",
        "📘 Пишем конспект",
        "🧪 Готовим тест",
    ]
    active = max(0, min(step, len(steps) - 1))
    lines = [f"{'▶' if i == active else '•'} {s}" for i, s in enumerate(steps)]
    return "\n".join(lines)


def topic_card_text(
    title: str,
    fmt: str,
    status: str,
    section_title: str,
    section_body: str,
    section_idx: int,
    total_sections: int,
) -> str:
    format_map = {
        "short": "кратко",
        "full": "подробно",
        "cheat": "шпаргалка",
        "simple": "простым языком",
    }
    return (
        f"📘 {title}\n"
        f"Формат: {format_map.get(fmt, fmt or 'базовый')}\n"
        f"Статус: {status}\n"
        "────────────\n"
        f"Раздел {section_idx + 1}/{max(total_sections, 1)}\n"
        f"<b>{section_title}</b>\n\n{section_body}"
    )


def test_question_text(title: str, index: int, total: int, question: str) -> str:
    return f"🧪 Тест: {title}\n\nВопрос {index + 1}/{total}\n\n{question}"


def test_result_text(score: int, total: int, weak_section: str) -> str:
    pct = int(score * 100 / total) if total else 0
    return (
        "🏁 Тест завершён\n\n"
        f"Результат: {score}/{total}\n"
        f"Освоение: {pct}%\n"
        f"Слабый раздел: {weak_section or 'не определён'}"
    )


def weak_section_training_text(title: str, weak_section: str) -> str:
    return (
        f"📌 Тема: {title}\n"
        f"Слабый раздел: {weak_section}\n\n"
        "Объясняем проще:\n"
        "1) Сформулируйте правило своими словами.\n"
        "2) Решите 1 короткий пример.\n"
        "3) Проверьте себя повторным тестом."
    )


def archive_text(items: list[str], page: int, total_pages: int) -> str:
    if not items:
        return "📚 Ваши работы\n\nСохранённых тем пока нет."
    rows = "\n".join(items)
    return f"📚 Ваши работы\n\n{rows}\n\nСтраница {page + 1}/{max(total_pages, 1)}"


def topic_details_text(title: str, fmt: str, status: str, progress: int) -> str:
    return (
        f"📖 {title}\n"
        f"Формат: {fmt}\n"
        f"Статус: {status}\n"
        f"Прогресс: {progress}%"
    )


def file_upload_text() -> str:
    return "📎 Загрузите файл (txt, pdf, docx), чтобы сделать конспект."


def compress_settings_text() -> str:
    return "Выберите режим сжатия: по словам или по проценту."
