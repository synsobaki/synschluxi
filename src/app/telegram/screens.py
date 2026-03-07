from __future__ import annotations

from datetime import datetime


def _greeting_by_time(now: datetime | None = None) -> str:
    dt = now or datetime.now()
    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def access_gate_text(display_name: str = "") -> str:
    greet = _greeting_by_time()
    greeting_line = f"{greet}, {display_name}" if display_name else greet
    return (
        f"{greeting_line}\n\n"
        "🔑 Введите лицензионный ключ.\n\n"
        "Формат:\n"
        "UMK-####-####\n\n"
        "Если у вас нет ключа,\n"
        "запросите его у администратора."
    )


def request_key_text() -> str:
    return (
        "📩 Запрос ключа\n\n"
        "Чтобы получить лицензионный ключ, напишите одному из администраторов ниже."
    )


def menu_text(is_active: bool = True) -> str:
    base = "✨ UMKOVO\nAI-помощник для обучения: конспект → тест → дообучение."
    return f"{base}\n\nВыберите действие 👇" if is_active else access_gate_text()


def profile_text(first_name: str, is_active: bool, masked_key: str | None, expires_at: str | None, topics_studied: int = 0, avg_result: int = 0) -> str:
    status = "активен" if is_active else "не активен"
    ttl = expires_at or "бессрочно"
    return (
        f"👤 {first_name or 'Пользователь'}\n\n"
        f"Доступ: {status}\n"
        f"Ключ: {masked_key or 'не подключён'}\n"
        f"Ключ действует до: {ttl}\n\n"
        f"Изучено тем: {topics_studied}\n"
        f"Средний результат тестов: {avg_result}%"
    )


def topic_input_text() -> str:
    return "📘 Создать конспект\n\nВыберите способ: ввести тему текстом или загрузить файл (txt/pdf/docx)."


def topic_title_input_text() -> str:
    return "✍️ Введите тему, которую хотите изучить."


def format_pick_text(title: str) -> str:
    return f"🧩 Тема: {title}\n\nВыберите формат конспекта:"


def topic_plan_text(title: str, plan: list[str] | None = None) -> str:
    plan = plan or ["Ключевые понятия", "Структура темы", "Практические сценарии", "Типичные ошибки", "Итог и проверка"]
    numbered = "\n".join([f"{i}. {item}" for i, item in enumerate(plan, start=1)])
    return f"📚 Тема: {title}\n\nПлан конспекта:\n\n{numbered}"


def generation_status_text(step: int = 0) -> str:
    steps = [
        "Нормализуем тему",
        "Уточняем формулировку",
        "Анализируем тему",
        "Строим план",
        "Проверяем предметность плана",
        "Подбираем материалы",
        "Генерируем разделы",
        "Очищаем текст",
        "Выравниваем разделы",
        "Собираем итоговый конспект",
        "Генерируем тест",
    ]
    active = max(0, min(step, len(steps) - 1))
    return "\n".join([f"{'▶' if i == active else '•'} {text}" for i, text in enumerate(steps)])


def summary_section_text(title: str, fmt: str, status: str, section_title: str, section_body: str, section_idx: int, total_sections: int) -> str:
    _ = status
    return (
        f"📘 {title}\nФормат: {fmt}\n"
        f"────────────\nРаздел {section_idx + 1} из {max(total_sections, 1)}\n"
        f"<b>{section_title}</b>\n\n{section_body}"
    )


def test_question_text(title: str, index: int, total: int, question: str) -> str:
    return f"🧪 Тест по конспекту: {title}\n\nВопрос {index + 1}/{total}\n\n{question}"


def test_result_text(score: int, total: int, weak_sections: list[str]) -> str:
    wrong = max(total - score, 0)
    weak_text = ", ".join(weak_sections) if weak_sections else "не определён"
    return (
        f"Результат: {score} из {total}\n\n"
        f"Правильных: {score}\n"
        f"Ошибок: {wrong}\n\n"
        f"Слабый раздел: {weak_text}"
    )


def test_review_text(item: dict[str, str], index: int, total: int) -> str:
    return (
        f"Вопрос {index + 1}/{total}\n\n"
        f"Вопрос: {item.get('question', '')}\n\n"
        f"Ваш ответ: {item.get('user_answer', '—')}\n"
        f"Правильный ответ: {item.get('correct_answer', '—')}\n"
        f"{item.get('status', '—')}"
    )


def weak_section_training_text(title: str, weak_section: str, training_text: str) -> str:
    return f"📖 Дообучение\nТема: {title}\nСлабый раздел: {weak_section}\n\n{training_text}"


def works_text(items: list[str], page: int, total_pages: int) -> str:
    if not items:
        return "📚 Ваши работы\nВ данном разделе хранится история ваших работ.\n\nСохранённых работ пока нет."
    return f"📚 Ваши работы\nВ данном разделе хранится история ваших работ.\n\nСтраница {page + 1}/{max(total_pages, 1)}"


def key_input_text() -> str:
    return "Введите лицензионный ключ\nФормат: UMK-####-####"


def file_upload_text() -> str:
    return "📎 Отправьте файл в формате txt, pdf или docx."
