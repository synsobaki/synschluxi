from __future__ import annotations

from dataclasses import dataclass

from src.services.rag import RAGService


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
        return [
            "Определение",
            "Основные идеи",
            "Алгоритм / механизм",
            "Примеры",
            "Итог",
        ]

    def generate_sections(self, plan: list[str], context: str, mode: str) -> list[dict[str, str]]:
        style = self.MODE_LABELS.get(mode, "структурированно")
        sections: list[dict[str, str]] = []
        for idx, title in enumerate(plan, start=1):
            body = (
                f"{idx}. **{title}**\n"
                f"_Разбираем тему {style}._\n\n"
                f"Ключевая мысль: `{title}` в контексте темы.\n"
                f"- Что важно понять\n"
                f"- Где это применяется\n"
                f"- На что обратить внимание\n\n"
                f"Пример: короткий кейс по разделу «{title}»."
            )
            if context:
                body += f"\n\n```text\n{context[:500]}\n```"
            sections.append({"id": str(idx), "title": title, "body": body})
        return sections

    def rebalance_sections(self, sections: list[dict[str, str]], mode: str) -> list[dict[str, str]]:
        _ = mode
        if not sections:
            return sections
        avg = max(250, int(sum(len(s.get("body", "")) for s in sections) / len(sections)))
        balanced: list[dict[str, str]] = []
        for section in sections:
            body = section.get("body", "")
            if len(body) > avg * 1.4:
                body = body[: int(avg * 1.2)].rstrip() + "\n\n_Сокращено для баланса разделов._"
            elif len(body) < avg * 0.5:
                body += "\n\nДополнение: повторите термины и решите 1 мини-задачу по разделу."
            balanced.append({**section, "body": body})
        return balanced

    def generate_summary(self, source: SummarySource, mode: str) -> tuple[str, list[dict[str, str]]]:
        plan = self.build_plan(source, mode)
        context = RAGService().build_context(source.title, source.source_text)
        sections = self.generate_sections(plan, context, mode)
        sections = self.rebalance_sections(sections, mode)
        full = "\n\n".join([f"## {s['title']}\n{s['body']}" for s in sections])
        return full, sections

    def rewrite_section(self, section: dict[str, str], rewrite_mode: str) -> dict[str, str]:
        body = section.get("body", "")
        if rewrite_mode == "shorter":
            body = " ".join(body.split()[:80])
        elif rewrite_mode == "longer":
            body += "\n\nДополнительно: разберите два контрастных примера и проверьте себя вопросом «почему это работает?»."
        else:
            body = f"Объяснение простыми словами:\n\n{body}"
        return {**section, "body": body}

    def rewrite_summary(self, sections: list[dict[str, str]], rewrite_mode: str) -> list[dict[str, str]]:
        return [self.rewrite_section(section, rewrite_mode) for section in sections]
