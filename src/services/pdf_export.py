from __future__ import annotations

from io import BytesIO
from pathlib import Path


def build_topic_pdf_bytes(title: str, sections: list[dict[str, str]]) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception as e:
        raise ValueError("Для экспорта PDF нужен пакет reportlab") from e

    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    font_path = next((p for p in font_candidates if Path(p).exists()), None)
    if not font_path:
        raise ValueError("Не найден шрифт с поддержкой кириллицы (DejaVuSans).")

    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=title)
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle("BodyRU", parent=styles["BodyText"], fontName="DejaVuSans", leading=14)
    heading_style = ParagraphStyle("HeadingRU", parent=styles["Heading3"], fontName="DejaVuSans")
    title_style = ParagraphStyle("TitleRU", parent=styles["Title"], fontName="DejaVuSans")
    story = [Paragraph(f"<b>{title}</b>", title_style), Spacer(1, 12)]

    for idx, section in enumerate(sections, 1):
        story.append(Paragraph(f"{idx}. <b>{section.get('title', 'Раздел')}</b>", heading_style))
        story.append(Paragraph((section.get("body") or "").replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 10))

    def _page(canvas, doc_obj):
        canvas.setFont("DejaVuSans", 9)
        canvas.drawRightString(A4[0] - 30, 20, f"Стр. {doc_obj.page}")

    doc.build(story, onFirstPage=_page, onLaterPages=_page)
    return buf.getvalue()
