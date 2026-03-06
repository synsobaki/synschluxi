from __future__ import annotations

import re
from dataclasses import dataclass

from src.services.rag import RAGService
from src.services.pdf_service import PDFService
from src.services.llm_service import LLMService


@dataclass
class SummarySource:
    title: str
    source_type: str = "topic"
    source_text: str = ""
    file_name: str | None = None


class SummaryService:
    MODE_LABELS = {
        "brief": "кратко",
        "detailed": "подробно",
        "simple": "простым языком",
        "cheat": "как шпаргалка",
    }

    def build_plan(self, source: SummarySource, mode: str) -> list[str]:
        _ = mode
        if source.source_text:
            chunks = [x.strip() for x in source.source_text.split("\n") if x.strip()]
            if chunks:
                return [x[:80] for x in chunks[:6]]
        title_lower = source.title.lower()
        if "ооп" in title_lower or "объект" in title_lower:
            return [
                "Классы и объекты",
                "Инкапсуляция",
                "Наследование",
                "Полиморфизм",
                "Типичные ошибки в моделировании",
                "Практический мини-кейс",
            ]
        if "python" in title_lower:
            return [
                "Базовый синтаксис и типы",
                "Условия, циклы и функции",
                "Коллекции и работа с данными",
                "Модули и структура проекта",
                "Обработка ошибок",
                "Практический пример",
            ]
        return [
            f"Ключевые термины: {source.title}",
            "Внутреннее устройство и логика",
            "Базовые сценарии применения",
            "Продвинутые приёмы",
            "Типичные ошибки и ограничения",
            "Контрольные вопросы по теме",
        ]

    def _sanitize_context(self, text: str) -> str:
        cleaned = re.sub(r"```[\s\S]*?```", "", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:700]

    def _context_points(self, context: str) -> list[str]:
        parts = [p.strip(" -•") for p in re.split(r"[\n\.]+", context) if p.strip()]
        return parts[:3]

    def generate_sections(self, plan: list[str], context: str, mode: str) -> list[dict[str, str]]:
        style = self.MODE_LABELS.get(mode, "структурированно")
        ctx = self._sanitize_context(context)
        hints = self._context_points(ctx)
        sections: list[dict[str, str]] = []
        for idx, title in enumerate(plan, start=1):
            hint = hints[idx % len(hints)] if hints else ""
            paragraph = (
                f"{title} — это ключевой элемент темы. Ниже — краткое объяснение {style}: "
                f"сначала разберём смысл, затем посмотрим, как это применяется на практике."
            )
            bullets = [
                f"• Основная идея: {title}.",
                "• Что нужно запомнить: определение и назначение.",
                "• Где применяется: в учебных задачах и реальных проектах.",
            ]
            if hint:
                bullets.append(f"• Пример/подсказка: {hint}.")
            body = paragraph + "\n\n" + "\n".join(bullets)
            sections.append({"id": str(idx), "title": title, "body": body})
        return sections

    def rebalance_sections(self, sections: list[dict[str, str]], mode: str) -> list[dict[str, str]]:
        _ = mode
        if not sections:
            return sections
        words = [len((s.get("body") or "").split()) for s in sections]
        avg = max(55, int(sum(words) / len(words)))
        balanced: list[dict[str, str]] = []
        for section in sections:
            body = section.get("body", "")
            ws = body.split()
            if len(ws) > int(avg * 1.45):
                body = " ".join(ws[: int(avg * 1.25)])
            elif len(ws) < int(avg * 0.7):
                body += "\n\n• Дополнение: сформулируйте своими словами, зачем нужен этот раздел."
            balanced.append({**section, "body": body})
        return balanced

    def generate_summary(self, source: SummarySource, mode: str) -> tuple[str, list[dict[str, str]]]:
        plan = self.build_plan(source, mode)
        context = RAGService().build_context(source.title, source.source_text)
        llm = LLMService()
        mode_label = self.MODE_LABELS.get(mode, "структурированно")
        sections = llm.generate_sections(source.title, mode_label, plan, context) if llm.enabled else None
        if not sections:
            sections = self.generate_sections(plan, context, mode)
        sections = self.rebalance_sections(sections, mode)
        full = "\n\n".join([f"{s['title']}\n{s['body']}" for s in sections])
        return full, sections

    def rewrite_section(self, section: dict[str, str], rewrite_mode: str) -> dict[str, str]:
        body = section.get("body", "")
        if rewrite_mode == "shorter":
            body = " ".join(body.split()[:70])
        elif rewrite_mode == "longer":
            body += "\n\n• Дополнительно: разберите ещё один практический пример по этому разделу."
        else:
            body = f"Коротко и просто:\n\n{body}"
        return {**section, "body": body}

    def rewrite_summary(self, sections: list[dict[str, str]], rewrite_mode: str) -> list[dict[str, str]]:
        return [self.rewrite_section(section, rewrite_mode) for section in sections]

    def export_pdf(self, title: str, fmt: str, sections: list[dict[str, str]]) -> bytes:
        return PDFService().export_summary_pdf(title, fmt, sections)
