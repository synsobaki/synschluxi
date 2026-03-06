from __future__ import annotations

from src.services.pdf_export import build_topic_pdf_bytes


class PDFService:
    def export_summary_pdf(self, title: str, fmt: str, sections: list[dict[str, str]]) -> bytes:
        numbered_sections = []
        for idx, section in enumerate(sections, start=1):
            numbered_sections.append(
                {
                    "title": f"{idx}. {section.get('title', 'Раздел')}",
                    "body": section.get("body", ""),
                }
            )
        return build_topic_pdf_bytes(f"{title} ({fmt})", numbered_sections)
