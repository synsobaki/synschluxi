from __future__ import annotations

from pathlib import Path


class TextExtractService:
    SUPPORTED = {".txt", ".pdf", ".docx"}

    async def extract_text(self, file_path: str, file_name: str | None = None) -> str:
        name = file_name or file_path
        ext = Path(name).suffix.lower()
        if ext not in self.SUPPORTED:
            raise ValueError("Неподдерживаемый формат. Разрешены: txt, pdf, docx")

        if ext == ".txt":
            return Path(file_path).read_text(encoding="utf-8", errors="ignore")

        if ext == ".pdf":
            try:
                from pypdf import PdfReader
            except Exception as e:
                raise ValueError("Для PDF нужен пакет pypdf") from e
            reader = PdfReader(file_path)
            return "\n".join((page.extract_text() or "") for page in reader.pages)

        if ext == ".docx":
            try:
                from docx import Document
            except Exception as e:
                raise ValueError("Для DOCX нужен пакет python-docx") from e
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)

        return ""
