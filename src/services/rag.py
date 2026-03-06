from __future__ import annotations

import re


class RAGService:
    """Лёгкий локальный RAG-слой без внешних зависимостей."""

    def _clean(self, text: str) -> str:
        text = re.sub(r"```[\s\S]*?```", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def build_context(self, topic: str, source_text: str | None = None) -> str:
        snippets: list[str] = []
        if source_text:
            chunks = [self._clean(c) for c in source_text.split("\n\n")]
            uniq = []
            for chunk in chunks:
                if chunk and chunk not in uniq:
                    uniq.append(chunk)
            snippets.extend(uniq[:4])

        if not snippets:
            snippets = [
                f"Определи базовые термины по теме «{topic}».",
                "Объясни структуру темы простым языком и добавь пример.",
                "Покажи, где знания применяются на практике.",
            ]

        return "\n\n".join(snippets)
