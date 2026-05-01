from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from ..types import ReportData, BrandConfig


GRAY = HexColor("#666666")
WHITE = HexColor("#ffffff")
BODY = HexColor("#222222")


def _styles(primary: str) -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle("title", fontSize=20, textColor=HexColor(primary),
            spaceAfter=6, fontName="Helvetica-Bold", alignment=TA_CENTER),
        "subtitle": ParagraphStyle("subtitle", fontSize=10, textColor=GRAY,
            spaceAfter=20, fontName="Helvetica", alignment=TA_CENTER),
        "h2": ParagraphStyle("h2", fontSize=13, textColor=HexColor(primary),
            spaceBefore=16, spaceAfter=8, fontName="Helvetica-Bold"),
        "body": ParagraphStyle("body", fontSize=9.5, textColor=BODY,
            spaceAfter=4, fontName="Helvetica", leading=13),
        "bullet": ParagraphStyle("bullet", fontSize=9.5, textColor=BODY,
            spaceAfter=3, fontName="Helvetica", leading=13,
            leftIndent=14, bulletIndent=0),
        "footer": ParagraphStyle("footer", fontSize=7, textColor=GRAY, alignment=TA_CENTER),
    }


def _build_metrics_table(metrics: dict[str, dict[str, int]], primary: str, light: str) -> Table:
    repos = list(metrics.keys())
    metric_names: list[str] = []
    seen = set()
    for vals in metrics.values():
        for k in vals.keys():
            if k not in seen:
                seen.add(k)
                metric_names.append(k)
    rows: list[list[str]] = [["Métrica"] + repos]
    for name in metric_names:
        rows.append([name] + [str(metrics[r].get(name, 0)) for r in repos])
    col_widths = [8 * cm] + [4 * cm] * len(repos)
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor(primary)),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor(light), WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def render(data: ReportData, brand: BrandConfig) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm)
    s = _styles(brand.primary_color)
    story = []

    story.append(Paragraph(data.title, s["title"]))
    story.append(Paragraph(data.subtitle, s["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor(brand.primary_color)))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Resumo Executivo", s["h2"]))
    story.append(Paragraph(data.executive_summary, s["body"]))
    story.append(Spacer(1, 6))

    if data.metrics:
        story.append(_build_metrics_table(data.metrics, brand.primary_color, brand.light_color))
        story.append(Spacer(1, 10))

    story.append(Paragraph("Detalhamento por Dia", s["h2"]))
    for day in data.days:
        story.append(Paragraph(f"<b>{day['date_label']}</b>", s["body"]))
        for item in day["items"]:
            story.append(Paragraph(f"• {item}", s["bullet"]))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Destaques Técnicos", s["h2"]))
    if data.highlights:
        for h in data.highlights:
            story.append(Paragraph(f"• {h}", s["bullet"]))
    else:
        story.append(Paragraph("—", s["body"]))

    story.append(Paragraph("Próximos Passos", s["h2"]))
    if data.next_steps:
        for n in data.next_steps:
            story.append(Paragraph(f"• {n}", s["bullet"]))
    else:
        story.append(Paragraph("—", s["body"]))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Gerado automaticamente a partir do histórico git", s["footer"]))

    doc.build(story)
    return buf.getvalue()
