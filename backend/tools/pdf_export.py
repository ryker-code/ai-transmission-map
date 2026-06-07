"""Generate a PDF investment memo from a MemoResponse dict."""
import io
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_DARK_BG = (0.059, 0.090, 0.145)   # slate-950 approximation for PDF
_ACCENT = (0.388, 0.400, 0.945)     # indigo-500


def generate_memo_pdf(memo: dict, thesis: str = "") -> bytes:
    """
    Render a PDF investment memo.

    Args:
        memo: Dict matching MemoResponse schema (memo_id, memo_text, regime, key_bottlenecks, etc.)
        thesis: Original analyst thesis string (may be empty).

    Returns:
        PDF bytes.
    """
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.lib import colors
    except ImportError:
        logger.error("reportlab not installed — returning stub PDF")
        return b"%PDF-1.4 stub (reportlab not installed)"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
    )

    indigo = colors.HexColor("#6366f1")
    slate_light = colors.HexColor("#94a3b8")
    white = colors.HexColor("#f1f5f9")
    dark = colors.HexColor("#0f172a")

    title_style = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=18, textColor=indigo, spaceAfter=4)
    subtitle_style = ParagraphStyle("subtitle", fontName="Helvetica", fontSize=10, textColor=slate_light, spaceAfter=16)
    heading_style = ParagraphStyle("heading", fontName="Helvetica-Bold", fontSize=12, textColor=indigo, spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle("body", fontName="Helvetica", fontSize=10, textColor=dark, leading=14, spaceAfter=6)
    meta_style = ParagraphStyle("meta", fontName="Helvetica-Oblique", fontSize=9, textColor=slate_light, spaceAfter=8)

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    regime = memo.get("regime", "AI_CAPEX_EXPANSION")
    memo_id = memo.get("memo_id", "")
    model_used = memo.get("model_used", "claude-opus-4-5")
    bottlenecks = memo.get("key_bottlenecks", [])
    affected = memo.get("affected_names", [])
    memo_text = memo.get("memo_text", "")

    story = []
    story.append(Paragraph("AI Transmission Map", title_style))
    story.append(Paragraph("Investment Intelligence Memo · US Equity Infrastructure", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=indigo))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"Memo ID: {memo_id}  ·  Regime: {regime}  ·  Generated: {now}  ·  Model: {model_used}", meta_style))

    if thesis:
        story.append(Paragraph("Analyst Thesis", heading_style))
        story.append(Paragraph(thesis.replace("\n", "<br/>"), body_style))

    story.append(Paragraph("Investment Memo", heading_style))
    for para in memo_text.split("\n\n"):
        para = para.strip()
        if para:
            story.append(Paragraph(para.replace("\n", "<br/>"), body_style))

    if bottlenecks:
        story.append(Paragraph("Key Bottlenecks", heading_style))
        items = [ListItem(Paragraph(b, body_style)) for b in bottlenecks]
        story.append(ListFlowable(items, bulletType="bullet"))

    if affected:
        story.append(Paragraph("Affected Names", heading_style))
        story.append(Paragraph(", ".join(affected), body_style))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=slate_light))
    story.append(Paragraph("This memo is for internal research purposes only. Not investment advice.", meta_style))

    doc.build(story)
    return buf.getvalue()
