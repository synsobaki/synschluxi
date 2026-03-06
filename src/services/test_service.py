from __future__ import annotations


class TestService:
    def generate_test_from_summary(self, summary_sections: list[dict[str, str]]) -> list[dict[str, object]]:
        questions: list[dict[str, object]] = []
        for idx, section in enumerate(summary_sections, start=1):
            title = str(section.get("title", f"Раздел {idx}"))
            questions.append(
                {
                    "id": idx,
                    "question": f"Что лучше всего отражает смысл раздела «{title}»?",
                    "options": [
                        "Пропустить базовые определения",
                        f"Понять основу раздела «{title}»",
                        "Запомнить без понимания",
                        "Искать ответ вне темы",
                    ],
                    "correct": 1,
                    "explanation": f"Верный ответ привязан к содержанию раздела «{title}».",
                    "section_title": title,
                    "section_id": section.get("id", str(idx)),
                }
            )
        return questions

    def check_answer(self, question: dict[str, object], answer: int) -> tuple[bool, str]:
        correct = int(question.get("correct", -1)) == answer
        return correct, str(question.get("explanation", ""))

    def calculate_result(self, questions: list[dict[str, object]], answers: dict[int, int]) -> dict[str, int]:
        correct = 0
        for i, q in enumerate(questions):
            if int(q.get("correct", -1)) == int(answers.get(i, -999)):
                correct += 1
        total = len(questions)
        return {"correct": correct, "total": total, "percent": int((correct * 100 / total) if total else 0)}

    def detect_weak_sections(self, questions: list[dict[str, object]], answers: dict[int, int]) -> list[str]:
        weak: list[str] = []
        for i, q in enumerate(questions):
            if int(q.get("correct", -1)) != int(answers.get(i, -999)):
                weak.append(str(q.get("section_title", "Раздел")))
        return weak

    def build_training_from_weak_section(
        self,
        topic_title: str,
        weak_section: dict[str, str],
        wrong_answers: list[dict[str, object]],
    ) -> str:
        mistakes = "\n".join([f"• {q.get('question', '')}" for q in wrong_answers]) or "• Ошибки не зафиксированы"
        return (
            f"📖 Дообучение по теме «{topic_title}»\n\n"
            f"Слабый раздел: {weak_section.get('title', 'Раздел')}\n\n"
            "Простое объяснение:\n"
            f"{weak_section.get('body', '')[:700]}\n\n"
            "Короткий план:\n"
            "1) Повторите ключевой термин.\n"
            "2) Разберите один простой пример.\n"
            "3) Проверьте себя вопросом по сути раздела.\n\n"
            f"Где были ошибки:\n{mistakes}"
        )
