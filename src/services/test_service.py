from __future__ import annotations

import re

from src.services.llm_service import LLMService


class TestService:
    def _extract_fact(self, body: str, fallback: str) -> str:
        clean = re.sub(r"\s+", " ", (body or "")).strip()
        if not clean:
            return fallback
        sentence = re.split(r"[.!?]", clean)[0].strip()
        return sentence[:120] if sentence else fallback

    def generate_test_from_summary(self, summary_sections: list[dict[str, str]]) -> list[dict[str, object]]:
        llm = LLMService()
        if llm.enabled:
            generated = llm.generate_test(summary_sections)
            if generated:
                return generated

        questions: list[dict[str, object]] = []
        for idx, section in enumerate(summary_sections, start=1):
            title = str(section.get("title", f"Раздел {idx}"))
            fact = self._extract_fact(str(section.get("body", "")), f"{title} — важная часть темы")
            options = [
                f"{title} помогает понять тему глубже и применить знания на практике",
                f"{title} не связан(а) с темой и его можно пропустить",
                f"{title} нужен только для заучивания без понимания",
                f"{title} используется только в теории и никогда в задачах",
            ]
            correct = idx % 4
            rotated = options[correct:] + options[:correct]
            questions.append(
                {
                    "id": idx,
                    "question": f"Какое утверждение лучше всего описывает раздел «{title}»?",
                    "options": rotated,
                    "correct": 0,
                    "explanation": f"Верный вариант отражает суть раздела: {fact}.",
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
            "Понятное объяснение:\n"
            f"{weak_section.get('body', '')[:900]}\n\n"
            "Что сделать дальше:\n"
            "1) Повторите определение раздела.\n"
            "2) Разберите один пример.\n"
            "3) Ответьте устно на контрольный вопрос.\n\n"
            f"Где были ошибки:\n{mistakes}"
        )
