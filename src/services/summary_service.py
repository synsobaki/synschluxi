from __future__ import annotations

import re
from dataclasses import dataclass

from src.services.rag import RAGService
from src.services.pdf_service import PDFService


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
        "cheat": "шпаргалка",
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
        cleaned = re.sub(r"(?im)^\s*источник:.*$", "", cleaned)
        cleaned = re.sub(r"(?im)^\s*source:.*$", "", cleaned)
        cleaned = re.sub(r"\bИсточник\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:700]

    def generate_sections(self, topic: str, plan: list[str], context: str, mode: str) -> list[dict[str, str]]:
        style = self.MODE_LABELS.get(mode, "структурированно")
        ctx = self._sanitize_context(context)
        sections: list[dict[str, str]] = []

        for idx, title in enumerate(plan, start=1):
            body_lines = [
                f"<i>Раздел объяснён {style}.</i>",
                "",
                f"<b>Главная идея.</b> В теме «{topic}» этот раздел раскрывает аспект: {title}.",
                "",
                "<b>Как это работает на практике.</b>",
                f"• Сформулируйте определение блока «{title}» своими словами.",
                "• Найдите 1 реальный пример применения.",
                "• Отметьте типичную ошибку и как её избежать.",
                "",
                "<b>Мини-проверка.</b> Ответьте: зачем этот раздел важен для понимания всей темы?",
            ]
            if ctx:
                body_lines.extend(["", f"<i>Полезный контекст:</i> {ctx}"])
            sections.append({"id": str(idx), "title": title, "body": "\n".join(body_lines).strip()})
        return sections

    def rebalance_sections(self, sections: list[dict[str, str]], mode: str) -> list[dict[str, str]]:
        _ = mode
        if not sections:
            return sections
        words = [len((s.get("body") or "").split()) for s in sections]
        avg = max(70, int(sum(words) / len(words)))
        balanced: list[dict[str, str]] = []
        for section in sections:
            body = section.get("body", "")
            ws = body.split()
            if len(ws) > int(avg * 1.4):
                body = " ".join(ws[: int(avg * 1.2)]) + "\n\n<i>Сокращено для равномерности разделов.</i>"
            elif len(ws) < int(avg * 0.6):
                body += "\n\n• Дополнение: свяжите этот раздел с предыдущим и приведите короткий пример."
            balanced.append({**section, "body": body})
        return balanced

    def generate_summary(self, source: SummarySource, mode: str, approved_plan: list[str] | None = None) -> tuple[str, list[dict[str, str]]]:
        plan = approved_plan or self.build_plan(source, mode)
        context = RAGService().build_context(source.title, source.source_text)
        sections = self.generate_sections(source.title, plan, context, mode)
        sections = self.rebalance_sections(sections, mode)
        full = "\n\n".join([f"{s['title']}\n{s['body']}" for s in sections])
        return full, sections

    def rewrite_section(self, section: dict[str, str], rewrite_mode: str) -> dict[str, str]:
        body = section.get("body", "")
        if rewrite_mode == "shorter":
            body = " ".join(body.split()[:90])
        elif rewrite_mode == "longer":
            body += "\n\n• Дополнительно: добавьте ещё один пример из практики и один контрпример."
        else:
            body = f"<i>Объяснение проще:</i>\n\n{body}"
        return {**section, "body": body}

    def rewrite_summary(self, sections: list[dict[str, str]], rewrite_mode: str) -> list[dict[str, str]]:
        return [self.rewrite_section(section, rewrite_mode) for section in sections]

    def export_pdf(self, title: str, fmt: str, sections: list[dict[str, str]]) -> bytes:
        return PDFService().export_summary_pdf(title, fmt, sections)
