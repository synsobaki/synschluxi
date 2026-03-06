from __future__ import annotations


class RAGService:
    """Лёгкий локальный RAG-слой без внешних зависимостей.

    Подмешивает релевантный контекст к теме/документу для снижения галлюцинаций.
    """

    def build_context(self, topic: str, source_text: str | None = None) -> str:
        snippets: list[str] = []
        if source_text:
            chunks = [c.strip() for c in source_text.split("\n\n") if c.strip()]
            snippets.extend(chunks[:3])

        if not snippets:
            snippets = [
                f"Определи базовые термины по теме «{topic}».",
                "Приведи объяснение на уровне учебника и короткий практический пример.",
                "Добавь алгоритм и критерии проверки правильности результата.",
            ]

        return "\n\n".join(f"Источник {i+1}: {s}" for i, s in enumerate(snippets))
