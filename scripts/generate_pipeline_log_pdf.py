from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import KeepTogether

OUTPUT = "docs/partners/velos/OMNIX_Velos_Pipeline_Log_v1.pdf"

DARK_BG    = colors.HexColor("#060F1E")
GOLD       = colors.HexColor("#C9A227")
LIGHT_TEXT = colors.HexColor("#E2E8F0")
MID_TEXT   = colors.HexColor("#94A3B8")
ROW_ALT    = colors.HexColor("#0D1829")
WHITE      = colors.white

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    leftMargin=18*mm,
    rightMargin=18*mm,
    topMargin=14*mm,
    bottomMargin=14*mm,
)

W, H = A4

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.restoreState()

styles = getSampleStyleSheet()

s_logo = ParagraphStyle("logo",
    fontSize=22, fontName="Helvetica-Bold",
    textColor=WHITE, alignment=TA_LEFT)

s_logo_sub = ParagraphStyle("logo_sub",
    fontSize=8, fontName="Helvetica",
    textColor=GOLD, alignment=TA_LEFT, spaceAfter=0)

s_tagline = ParagraphStyle("tagline",
    fontSize=7.5, fontName="Helvetica",
    textColor=MID_TEXT, alignment=TA_RIGHT)

s_title = ParagraphStyle("title",
    fontSize=15, fontName="Helvetica-Bold",
    textColor=GOLD, alignment=TA_LEFT, spaceBefore=6, spaceAfter=2)

s_subtitle = ParagraphStyle("subtitle",
    fontSize=9, fontName="Helvetica",
    textColor=MID_TEXT, alignment=TA_LEFT, spaceAfter=2)

s_section = ParagraphStyle("section",
    fontSize=8.5, fontName="Helvetica-Bold",
    textColor=GOLD, spaceBefore=10, spaceAfter=4)

s_body = ParagraphStyle("body",
    fontSize=8, fontName="Helvetica",
    textColor=LIGHT_TEXT, spaceAfter=3, leading=13)

s_footer = ParagraphStyle("footer",
    fontSize=7, fontName="Helvetica",
    textColor=MID_TEXT, alignment=TA_CENTER)

s_meta_label = ParagraphStyle("meta_label",
    fontSize=7.5, fontName="Helvetica-Bold",
    textColor=MID_TEXT)

s_meta_val = ParagraphStyle("meta_val",
    fontSize=7.5, fontName="Helvetica",
    textColor=LIGHT_TEXT)

story = []

header_data = [[
    Paragraph("<b>OMNIX</b> QUANTUM", s_logo),
    Paragraph("omnixquantum.net  ·  Decision Governance Infrastructure", s_tagline),
]]
header_table = Table(header_data, colWidths=[90*mm, None])
header_table.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ("TOPPADDING", (0,0), (-1,-1), 0),
]))
story.append(header_table)
story.append(Paragraph("Decision Governance Infrastructure", s_logo_sub))
story.append(Spacer(1, 3*mm))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=4))

story.append(Paragraph("JOINT STACK PIPELINE LOG", s_title))
story.append(Paragraph(
    "Clause 4.4 — Pipeline Transparency  ·  "
    "Joint Bundled Commercial Agreement Supplement  ·  "
    "Master Partnership Agreement v2.0 — 03 April 2026",
    s_subtitle))
story.append(Spacer(1, 2*mm))

meta_data = [
    [Paragraph("Issued by:", s_meta_label), Paragraph("Harold Nunes — OMNIX Quantum Ltd", s_meta_val),
     Paragraph("Date:", s_meta_label), Paragraph("22 April 2026", s_meta_val)],
    [Paragraph("Parties:", s_meta_label), Paragraph("OMNIX Quantum Ltd  &  Velos", s_meta_val),
     Paragraph("Version:", s_meta_label), Paragraph("1.0", s_meta_val)],
]
meta_table = Table(meta_data, colWidths=[25*mm, 75*mm, 20*mm, None])
meta_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), ROW_ALT),
    ("TEXTCOLOR", (0,0), (-1,-1), LIGHT_TEXT),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("ROUNDEDCORNERS", [3]),
]))
story.append(meta_table)
story.append(Spacer(1, 5*mm))

story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#1E2D45"), spaceAfter=4))
story.append(Paragraph("ACTIVE JOINT OPPORTUNITIES", s_section))

pipeline_headers = ["#", "Prospect", "Sector", "Track", "Stage", "Last Updated"]
pipeline_rows = [
    ["—", "—", "—", "—", "No active joint opportunities at this time", "22 Apr 2026"],
]

pipeline_data = [pipeline_headers] + pipeline_rows
col_widths = [8*mm, 32*mm, 28*mm, 18*mm, 62*mm, 27*mm]

pipeline_table = Table(pipeline_data, colWidths=col_widths, repeatRows=1)
pipeline_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), GOLD),
    ("TEXTCOLOR", (0,0), (-1,0), DARK_BG),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,0), 7.5),
    ("ALIGN", (0,0), (-1,0), "CENTER"),
    ("TOPPADDING", (0,0), (-1,0), 5),
    ("BOTTOMPADDING", (0,0), (-1,0), 5),

    ("BACKGROUND", (0,1), (-1,-1), ROW_ALT),
    ("TEXTCOLOR", (0,1), (-1,-1), MID_TEXT),
    ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
    ("FONTSIZE", (0,1), (-1,-1), 7.5),
    ("ALIGN", (0,1), (-1,-1), "CENTER"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,1), (-1,-1), 6),
    ("BOTTOMPADDING", (0,1), (-1,-1), 6),
    ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#1E2D45")),
    ("ROUNDEDCORNERS", [3]),
]))
story.append(pipeline_table)
story.append(Spacer(1, 5*mm))

story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#1E2D45"), spaceAfter=4))
story.append(Paragraph("LOG MAINTENANCE PROTOCOL", s_section))

protocol_items = [
    "This log is updated by both Parties within <b>5 business days</b> of any material development.",
    "Any new prospect must be added by the Party that initiated the engagement.",
    "Track selection (A or B) is confirmed jointly per <b>Clause 4.1</b>.",
    "Any Track B engagement requires prior written approval from OMNIX per <b>Clause 4.3</b>.",
]
for item in protocol_items:
    story.append(Paragraph(f"·  {item}", s_body))

story.append(Spacer(1, 5*mm))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#1E2D45"), spaceAfter=4))
story.append(Paragraph("STAGE DEFINITIONS", s_section))

stage_headers = ["Stage", "Description"]
stage_rows = [
    ["Prospect",     "Initial contact made — interest confirmed"],
    ["Qualification","Client requirements assessed — joint stack fit confirmed"],
    ["Proposal",     "Commercial proposal submitted to client"],
    ["Negotiation",  "Contract terms under discussion"],
    ["Closed",       "Agreement executed"],
    ["On Hold",      "Paused — reason logged in notes"],
]
stage_data = [stage_headers] + stage_rows
stage_table = Table(stage_data, colWidths=[40*mm, None])
stage_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), GOLD),
    ("TEXTCOLOR", (0,0), (-1,0), DARK_BG),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,0), 7.5),
    ("ALIGN", (0,0), (-1,0), "CENTER"),
    ("TOPPADDING", (0,0), (-1,0), 5),
    ("BOTTOMPADDING", (0,0), (-1,0), 5),

    ("BACKGROUND", (0,1), (-1,-1), ROW_ALT),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [ROW_ALT, DARK_BG]),
    ("TEXTCOLOR", (0,1), (0,-1), GOLD),
    ("TEXTCOLOR", (1,1), (1,-1), LIGHT_TEXT),
    ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
    ("FONTSIZE", (0,1), (-1,-1), 7.5),
    ("ALIGN", (0,1), (-1,-1), "LEFT"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,1), (-1,-1), 5),
    ("BOTTOMPADDING", (0,1), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#1E2D45")),
]))
story.append(stage_table)

story.append(Spacer(1, 8*mm))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=4))
story.append(Paragraph(
    "CONFIDENTIAL — For internal use by OMNIX Quantum Ltd and Velos only.<br/>"
    "OMNIX Quantum Ltd — Registered in England &amp; Wales — omnixquantum.net",
    s_footer))

doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"PDF generated: {OUTPUT}")
