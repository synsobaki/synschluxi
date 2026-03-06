from __future__ import annotations

from io import BytesIO


def build_topic_pdf_bytes(title: str, sections: list[dict[str, str]]) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception as e:
        raise ValueError("Для экспорта PDF нужен пакет reportlab") from e

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=title)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"<b>{title}</b>", styles["Title"]), Spacer(1, 12)]

    for idx, section in enumerate(sections, 1):
        story.append(Paragraph(f"{idx}. <b>{section.get('title', 'Раздел')}</b>", styles["Heading3"]))
        story.append(Paragraph((section.get("body") or "").replace("\n", "<br/>"), styles["BodyText"]))
        story.append(Spacer(1, 10))

    doc.build(story)
    return buf.getvalue()
