from __future__ import annotations


def access_gate_text() -> str:
    return (
        "Доступ к UMKOVO\n\n"
        "Для использования нужен лицензионный ключ.\n\n"
        "🔑 Введите ключ формата:\n"
        "UMK-####-####\n\n"
        "Если у вас нет ключа, запросите его у администратора или саппорта."
    )


def request_key_text() -> str:
    return (
        "Запрос ключа\n\n"
        "Чтобы получить доступ, напишите администратору или в саппорт."
    )


def menu_text(is_active: bool = True) -> str:
    base = "✨ UMKOVO\nAI-помощник для обучения: конспект → тест → дообучение."
    return f"{base}\n\nВыберите действие 👇" if is_active else access_gate_text()


def profile_text(first_name: str, is_active: bool, masked_key: str | None, expires_at: str | None, topics_studied: int = 0, avg_result: int = 0) -> str:
    status = "🟢 Активен" if is_active else "🔴 Не активен"
    ttl = expires_at or "бессрочный"
    return (
        "👤 Профиль\n\n"
        f"Имя: {first_name or 'Пользователь'}\n"
        f"Статус: {status}\n"
        f"Ключ: {masked_key or 'не подключён'}\n"
        f"Срок: {ttl}\n\n"
        f"Тем изучено: {topics_studied}\n"
        f"Средний результат: {avg_result}%"
    )


def topic_input_text() -> str:
    return "📘 Создать конспект\n\nВыберите способ: ввести тему текстом или загрузить файл (txt/pdf/docx)."


def topic_title_input_text() -> str:
    return "✍️ Введите тему, которую хотите изучить."


def format_pick_text(title: str) -> str:
    return f"🧩 Тема: {title}\n\nВыберите формат конспекта:"


def topic_plan_text(title: str, plan: list[str] | None = None) -> str:
    plan = plan or ["Определение", "Основные идеи", "Алгоритм / механизм", "Примеры", "Итог"]
    numbered = "\n".join([f"{i}. {item}" for i, item in enumerate(plan, start=1)])
    return f"📚 Тема: {title}\n\nПлан конспекта:\n\n{numbered}"


def generation_status_text(step: int = 0) -> str:
    steps = [
        "Анализ темы / файла",
        "Построение структуры",
        "Извлечение контекста (RAG)",
        "Генерация разделов",
        "Выравнивание разделов",
        "Финальная сборка",
        "Генерация теста",
    ]
    active = max(0, min(step, len(steps) - 1))
    return "\n".join([f"{'▶' if i == active else '•'} {text}" for i, text in enumerate(steps)])


def summary_section_text(title: str, fmt: str, status: str, section_title: str, section_body: str, section_idx: int, total_sections: int) -> str:
    return (
        f"📘 {title}\nФормат: {fmt}\nСтатус: {status}\n"
        f"────────────\nРаздел {section_idx + 1}/{max(total_sections, 1)}\n"
        f"<b>{section_title}</b>\n\n{section_body}"
    )


def test_question_text(title: str, index: int, total: int, question: str) -> str:
    return f"🧪 Тест по конспекту: {title}\n\nВопрос {index + 1}/{total}\n\n{question}"


def test_result_text(score: int, total: int, weak_sections: list[str]) -> str:
    pct = int(score * 100 / total) if total else 0
    weak_text = ", ".join(weak_sections) if weak_sections else "не определены"
    wrong = max(total - score, 0)
    return (
        "🏁 Тест завершён\n\n"
        f"Правильных ответов: {score}/{total}\n"
        f"Неправильных: {wrong}/{total}\n"
        f"Итог: {pct}%\n\n"
        f"Слабый раздел: {weak_text}"
    )


def test_review_text(item: dict[str, str], index: int, total: int) -> str:
    return (
        f"Вопрос {index + 1}/{total}\n\n"
        f"{item.get('question', '')}\n\n"
        f"Ваш ответ: {item.get('user_answer', '—')}\n"
        f"Правильный ответ: {item.get('correct_answer', '—')}\n"
        f"Статус: {item.get('status', '—')}"
    )


def weak_section_training_text(title: str, weak_section: str, training_text: str) -> str:
    return f"📖 Дообучение\nТема: {title}\nСлабый раздел: {weak_section}\n\n{training_text}"


def works_text(items: list[str], page: int, total_pages: int) -> str:
    if not items:
        return "📚 Ваши работы\nВ данном разделе хранится история ваших работ.\n\nСохранённых работ пока нет."
    return "📚 Ваши работы\nВ данном разделе хранится история ваших работ."


def key_input_text() -> str:
    return "Введите лицензионный ключ\nФормат: UMK-####-####"


def file_upload_text() -> str:
    return "📎 Отправьте файл в формате txt, pdf или docx."
