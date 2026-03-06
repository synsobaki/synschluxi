from __future__ import annotations

from src.services.test_service import TestService


class TrainingService:
    def build_training_from_weak_section(
        self,
        topic_title: str,
        weak_section: dict[str, str],
        wrong_answers: list[dict[str, object]],
    ) -> str:
        return TestService().build_training_from_weak_section(topic_title, weak_section, wrong_answers)
