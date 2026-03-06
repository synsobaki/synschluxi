from __future__ import annotations


def menu_text(is_active: bool = True) -> str:
    base = (
        "✨ UMKOVO\n"
        "Твой учебный помощник: понятные конспекты и тренировка знаний."
    )
    if is_active:
        return f"{base}\n\nВыбери, с чего начнём 👇"
    return f"{base}\n\nДля полного доступа активируй ключ в профиле 🔑"


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
        f"Доступ: {status}\n"
        f"Ключ: {masked_key or 'отсутствует'} ({key_status})\n"
        f"Срок доступа: {expires_at or 'не задан'}\n\n"
        "📈 Прогресс обучения\n"
        f"Изучено тем: {topics_studied}\n"
        f"Средний прогресс: {avg_result}%"
    )


def key_input_text() -> str:
    return "🔑 Введите лицензионный ключ.\nПример: UMK-92F1-A7B3"


def key_request_text() -> str:
    return (
        "📩 Нужен доступ?\n"
        "Нажмите кнопку ниже, чтобы запросить ключ у администратора."
    )


def topic_title_input_text() -> str:
    return (
        "📘 Создание конспекта\n\n"
        "Введите тему, которую хотите изучить.\n\n"
        "Примеры:\n"
        "• Метод Гаусса\n"
        "• Интерполяция Лагранжа\n"
        "• SQL индексы"
    )


def format_pick_text(title: str) -> str:
    return f"🧩 Тема: {title}\n\nВыберите удобный формат изучения."


def topic_plan_text(title: str) -> str:
    return (
        f"🗺 План темы: {title}\n\n"
        "1) Ключевые понятия\n"
        "2) Теоретическая база\n"
        "3) Алгоритм применения\n"
        "4) Примеры\n"
        "5) Краткий итог"
    )


def generation_status_text(step: int = 0) -> str:
    steps = [
        "⏳ Готовим конспект...",
        "🧠 Анализируем тему",
        "📝 Формируем структуру",
        "📘 Пишем материал",
        "✅ Почти готово",
    ]
    active = max(0, min(step, len(steps) - 1))
    lines = []
    for idx, line in enumerate(steps):
        prefix = "▶" if idx == active else "•"
        lines.append(f"{prefix} {line}")
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
        "short": "Краткий конспект",
        "full": "Полный конспект",
        "cheat": "Шпаргалка",
        "simple": "Простым языком",
    }
    return (
        f"📘 {title}\n"
        f"Формат: {format_map.get(fmt, fmt or 'базовый')}\n"
        f"Статус: {status}\n"
        "────────────\n"
        f"📍 Раздел {section_idx + 1} из {max(total_sections, 1)}\n"
        f"<b>{section_title}</b>\n\n"
        f"{section_body}\n\n"
        "🧷 Структурированный учебный конспект"
    )


def test_question_text(title: str, index: int, total: int, question: str) -> str:
    return (
        f"🧪 Тест по теме: {title}\n\n"
        f"Вопрос {index + 1} из {total}\n"
        "Выберите правильный вариант:\n\n"
        f"{question}"
    )


def test_feedback_text(correct: bool, explanation: str, score: int, answered: int, total: int) -> str:
    mark = "✅ Верно" if correct else "❌ Неверно"
    return (
        f"{mark}\n"
        f"{explanation}\n\n"
        f"Промежуточный результат: {score}/{answered}\n"
        f"Осталось вопросов: {total - answered}"
    )


def test_result_text(score: int, total: int, weak_section: str) -> str:
    pct = int(score * 100 / total) if total else 0
    return (
        "🏁 Тест завершён\n\n"
        f"Результат: {score}/{total} ({pct}%)\n"
        f"Слабый раздел: {weak_section or 'не определён'}\n\n"
        "Рекомендуем повторить материал и пройти тест снова."
    )


def archive_text(items: list[str]) -> str:
    if not items:
        return "📚 Архив\n\nСохранённых тем пока нет."
    rows = "\n".join(items)
    return f"📚 Архив тем\n\n{rows}"
