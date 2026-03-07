from __future__ import annotations


class TestService:
    def _target_questions_count(self, mode: str, sections_count: int) -> int:
        mode = (mode or "").strip()
        if mode == "brief":
            base = 8
        elif mode == "cheat":
            base = 9
        elif mode == "simple":
            base = 10
        else:
            base = 12
        return max(8, min(12, max(base, sections_count)))

    def generate_test_from_summary(self, summary_sections: list[dict[str, str]], mode: str = "detailed") -> list[dict[str, object]]:
        if not summary_sections:
            return []
        questions: list[dict[str, object]] = []
        target = self._target_questions_count(mode, len(summary_sections))
        for idx in range(target):
            section = summary_sections[idx % len(summary_sections)]
            title = str(section.get("title", f"Раздел {idx + 1}"))
            questions.append(
                {
                    "id": idx + 1,
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
                    "section_id": section.get("id", str(idx + 1)),
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
