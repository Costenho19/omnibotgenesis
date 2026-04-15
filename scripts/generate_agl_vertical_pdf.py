"""
OMNIX Autonomous Governance Layer (AGL)
Medical AI & Autonomous Agent Decision Governance
PDF Generator — White background, professional enterprise style
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
 SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
 PageBreak, KeepTogether, Flowable, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT

# ── COLOURS — White background ────────────────────────────────────────────────
GOLD = HexColor('#C9A227')
GOLD_DARK = HexColor('#A07820')
NAVY = HexColor('#0a0f1a')
DARK_GRAY = HexColor('#1e293b')
MID_GRAY = HexColor('#475569')
LIGHT_GRAY = HexColor('#f1f5f9')
BORDER = HexColor('#e2e8f0')
WHITE = HexColor('#ffffff')
MED_BLUE = HexColor('#0ea5e9')
AGT_GREEN = HexColor('#10b981')
RED = HexColor('#ef4444')
GREEN = HexColor('#10b981')

LOGO_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'omnix_logo.png')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..',
 'OMNIX_Autonomous_Governance_Layer.pdf')

W, H = A4


# ── PAGE TEMPLATE ─────────────────────────────────────────────────────────────
def page_template(canvas_obj, doc):
 canvas_obj.saveState()

 # White background
 canvas_obj.setFillColor(WHITE)
 canvas_obj.rect(0, 0, W, H, fill=1, stroke=0)

 # Gold left accent bar
 canvas_obj.setFillColor(GOLD)
 canvas_obj.rect(0, 0, 5, H, fill=1, stroke=0)

 # Top gold line
 canvas_obj.setFillColor(GOLD)
 canvas_obj.rect(0, H - 5, W, 5, fill=1, stroke=0)

 # Footer line
 canvas_obj.setStrokeColor(BORDER)
 canvas_obj.setLineWidth(0.5)
 canvas_obj.line(1.0 * inch, 0.6 * inch, W - 1.0 * inch, 0.6 * inch)

 # Footer text
 canvas_obj.setFillColor(MID_GRAY)
 canvas_obj.setFont("Helvetica", 7)
 canvas_obj.drawString(1.0 * inch, 0.42 * inch,
 "OMNIX Quantum Ltd — Autonomous Governance Layer | Confidential")
 canvas_obj.drawRightString(W - 1.0 * inch, 0.42 * inch,
 f"Page {canvas_obj.getPageNumber()}")
 canvas_obj.drawCentredString(W / 2, 0.42 * inch, "omnixquantum.net")

 canvas_obj.restoreState()


def cover_template(canvas_obj, doc):
 canvas_obj.saveState()

 # Navy cover background
 canvas_obj.setFillColor(NAVY)
 canvas_obj.rect(0, 0, W, H, fill=1, stroke=0)

 # Gold accent bar left
 canvas_obj.setFillColor(GOLD)
 canvas_obj.rect(0, 0, 6, H, fill=1, stroke=0)

 # Gold top bar
 canvas_obj.setFillColor(GOLD)
 canvas_obj.rect(0, H - 6, W, 6, fill=1, stroke=0)

 # Gold bottom bar
 canvas_obj.setFillColor(GOLD)
 canvas_obj.rect(0, 0, W, 4, fill=1, stroke=0)

 # Footer text on cover
 canvas_obj.setFillColor(HexColor('#94a3b8'))
 canvas_obj.setFont("Helvetica", 7)
 canvas_obj.drawCentredString(W / 2, 0.35 * inch,
 "OMNIX Quantum Ltd — omnixquantum.net | Confidential")

 canvas_obj.restoreState()


# ── STYLES ────────────────────────────────────────────────────────────────────
def build_styles():
 base = getSampleStyleSheet()
 defs = [
 # Cover (dark bg)
 ("CoverTitle", dict(fontName="Helvetica-Bold", fontSize=30,
 textColor=GOLD, alignment=TA_LEFT, spaceAfter=8, spaceBefore=0, leading=36)),
 ("CoverTitle2", dict(fontName="Helvetica-Bold", fontSize=20,
 textColor=WHITE, alignment=TA_LEFT, spaceAfter=6, spaceBefore=0, leading=26)),
 ("CoverSub", dict(fontName="Helvetica", fontSize=12,
 textColor=HexColor('#94a3b8'), alignment=TA_LEFT, spaceAfter=4, spaceBefore=4, leading=17)),
 ("CoverMeta", dict(fontName="Helvetica", fontSize=10,
 textColor=HexColor('#64748b'), alignment=TA_LEFT, spaceAfter=3, spaceBefore=3)),
 ("CoverTag", dict(fontName="Helvetica-Bold", fontSize=9,
 textColor=GOLD, alignment=TA_LEFT, spaceAfter=2, spaceBefore=2)),

 # Section headers (white bg)
 ("SectionTitle", dict(fontName="Helvetica-Bold", fontSize=14,
 textColor=NAVY, alignment=TA_LEFT, spaceAfter=6, spaceBefore=16, leading=18)),
 ("SubTitle", dict(fontName="Helvetica-Bold", fontSize=11,
 textColor=DARK_GRAY, alignment=TA_LEFT, spaceAfter=5, spaceBefore=10, leading=15)),
 ("SubTitle2", dict(fontName="Helvetica-Bold", fontSize=10,
 textColor=MID_GRAY, alignment=TA_LEFT, spaceAfter=4, spaceBefore=8)),

 # Body
 ("Body", dict(fontName="Helvetica", fontSize=9.5,
 textColor=DARK_GRAY, alignment=TA_JUSTIFY,
 spaceAfter=5, spaceBefore=0, leading=15, leftIndent=0)),
 ("BodySmall", dict(fontName="Helvetica", fontSize=8.5,
 textColor=MID_GRAY, alignment=TA_LEFT,
 spaceAfter=3, spaceBefore=0, leading=12)),
 ("Bullet", dict(fontName="Helvetica", fontSize=9.5,
 textColor=DARK_GRAY, alignment=TA_LEFT,
 spaceAfter=3, spaceBefore=2, leading=14,
 leftIndent=16, firstLineIndent=-8)),
 ("Code", dict(fontName="Courier", fontSize=8,
 textColor=DARK_GRAY, alignment=TA_LEFT,
 spaceAfter=3, spaceBefore=3, leading=11, leftIndent=12,
 backColor=LIGHT_GRAY)),

 # Table styles
 ("TH", dict(fontName="Helvetica-Bold", fontSize=8.5,
 textColor=WHITE, alignment=TA_LEFT, leading=11)),
 ("TD", dict(fontName="Helvetica", fontSize=8.5,
 textColor=DARK_GRAY, alignment=TA_LEFT, leading=11)),
 ("TDCenter", dict(fontName="Helvetica", fontSize=8.5,
 textColor=DARK_GRAY, alignment=TA_CENTER, leading=11)),
 ("TDBold", dict(fontName="Helvetica-Bold", fontSize=8.5,
 textColor=NAVY, alignment=TA_LEFT, leading=11)),
 ("TDGold", dict(fontName="Helvetica-Bold", fontSize=8.5,
 textColor=GOLD_DARK, alignment=TA_LEFT, leading=11)),
 ("TDGreen", dict(fontName="Helvetica-Bold", fontSize=8.5,
 textColor=GREEN, alignment=TA_CENTER, leading=11)),
 ("TDBlue", dict(fontName="Helvetica-Bold", fontSize=8.5,
 textColor=MED_BLUE, alignment=TA_LEFT, leading=11)),

 # Tags / pills
 ("TagMED", dict(fontName="Helvetica-Bold", fontSize=9,
 textColor=MED_BLUE, alignment=TA_LEFT, spaceAfter=2)),
 ("TagAGT", dict(fontName="Helvetica-Bold", fontSize=9,
 textColor=AGT_GREEN, alignment=TA_LEFT, spaceAfter=2)),

 # Footer note
 ("FootNote", dict(fontName="Helvetica-Oblique", fontSize=7.5,
 textColor=MID_GRAY, alignment=TA_CENTER, spaceAfter=2, spaceBefore=4)),
 ("Callout", dict(fontName="Helvetica-Bold", fontSize=10,
 textColor=NAVY, alignment=TA_CENTER, spaceAfter=4, spaceBefore=4)),
 ]
 for name, kwargs in defs:
 style = ParagraphStyle(name, **kwargs)
 if name not in base.byName:
 base.add(style)
 else:
 base.byName[name] = style
 return base


# ── CUSTOM FLOWABLES ──────────────────────────────────────────────────────────
class GoldRule(Flowable):
 def __init__(self, doc_width, thickness=1.5):
 super().__init__()
 self.width = doc_width
 self.height = thickness + 3
 self.thickness = thickness

 def draw(self):
 self.canv.setFillColor(GOLD)
 self.canv.rect(0, 1, self.width, self.thickness, fill=1, stroke=0)


class SectionHeader(Flowable):
 def __init__(self, number, title, doc_width, color=NAVY):
 super().__init__()
 self.number = number
 self.title = title
 self.width = doc_width
 self.color = color
 self.height = 32

 def draw(self):
 # Left gold accent
 self.canv.setFillColor(GOLD)
 self.canv.rect(0, 0, 4, self.height, fill=1, stroke=0)
 # Light bg
 self.canv.setFillColor(LIGHT_GRAY)
 self.canv.rect(4, 0, self.width - 4, self.height, fill=1, stroke=0)
 # Border bottom
 self.canv.setStrokeColor(BORDER)
 self.canv.setLineWidth(0.5)
 self.canv.line(4, 0, self.width, 0)
 # Text
 self.canv.setFillColor(self.color)
 self.canv.setFont("Helvetica-Bold", 12)
 self.canv.drawString(14, 10, f"{self.number}. {self.title}")


class SubHeader(Flowable):
 def __init__(self, title, doc_width, color=DARK_GRAY):
 super().__init__()
 self.title = title
 self.width = doc_width
 self.color = color
 self.height = 24

 def draw(self):
 self.canv.setFillColor(GOLD)
 self.canv.rect(0, 6, 3, self.height - 6, fill=1, stroke=0)
 self.canv.setFillColor(self.color)
 self.canv.setFont("Helvetica-Bold", 10)
 self.canv.drawString(12, 8, self.title)


class DomainBadge(Flowable):
 def __init__(self, label, color, width=180):
 super().__init__()
 self.label = label
 self.color = color
 self.width = width
 self.height = 24

 def draw(self):
 self.canv.setFillColor(self.color)
 self.canv.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
 self.canv.setFillColor(WHITE)
 self.canv.setFont("Helvetica-Bold", 10)
 self.canv.drawCentredString(self.width / 2, 7, self.label)


# ── TABLE HELPER ──────────────────────────────────────────────────────────────
def make_table(headers, rows, col_widths, s, header_bg=NAVY):
 head_row = [Paragraph(h, s['TH']) for h in headers]
 data_rows = []
 for i, row in enumerate(rows):
 bg = WHITE if i % 2 == 0 else LIGHT_GRAY
 data_rows.append([Paragraph(str(c), s['TD']) for c in row])

 t = Table([head_row] + data_rows, colWidths=col_widths)
 t.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (-1, 0), header_bg),
 ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
 ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
 ('GRID', (0, 0), (-1, -1), 0.3, BORDER),
 ('TOPPADDING', (0, 0), (-1, -1), 6),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
 ('LEFTPADDING', (0, 0), (-1, -1), 7),
 ('RIGHTPADDING', (0, 0), (-1, -1), 7),
 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
 ]))
 return t


# ── BUILD ─────────────────────────────────────────────────────────────────────
def build_pdf():
 s = build_styles()
 DW = W - 2.0 * inch

 doc = SimpleDocTemplate(
 OUTPUT_PATH,
 pagesize=A4,
 leftMargin=1.0 * inch,
 rightMargin=1.0 * inch,
 topMargin=0.9 * inch,
 bottomMargin=0.75 * inch,
 )

 story = []

 # ════════════════════════════════════════════════════════════════════════
 # COVER PAGE (dark)
 # ════════════════════════════════════════════════════════════════════════
 if os.path.exists(LOGO_PATH):
 from reportlab.platypus import Image
 logo = Image(LOGO_PATH, width=1.8 * inch, height=0.62 * inch)
 logo.hAlign = "LEFT"
 story.append(logo)

 story.append(Spacer(1, 0.5 * inch))

 # Domain badges inline
 badge_table = Table(
 [[DomainBadge("OMNIX-MED Medical AI", MED_BLUE, 200),
 Spacer(20, 1),
 DomainBadge("OMNIX-AGT Autonomous Agents", AGT_GREEN, 210)]],
 colWidths=[205, 24, 215]
 )
 badge_table.setStyle(TableStyle([
 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
 ('TOPPADDING', (0, 0), (-1, -1), 0),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
 ]))
 story.append(badge_table)
 story.append(Spacer(1, 0.3 * inch))

 story.append(Paragraph("OMNIX", ParagraphStyle("CT1",
 fontName="Helvetica-Bold", fontSize=42, textColor=GOLD,
 alignment=TA_LEFT, leading=46)))
 story.append(Paragraph("Autonomous Governance Layer", ParagraphStyle("CT2",
 fontName="Helvetica-Bold", fontSize=22, textColor=WHITE,
 alignment=TA_LEFT, leading=28, spaceAfter=6)))
 story.append(Paragraph(
 "Decision Governance Infrastructure for Medical AI &amp; Autonomous Agent Systems",
 ParagraphStyle("CT3", fontName="Helvetica", fontSize=12,
 textColor=HexColor('#94a3b8'), alignment=TA_LEFT, leading=17, spaceAfter=30)))

 story.append(GoldRule(DW, 1))
 story.append(Spacer(1, 0.25 * inch))

 # Key facts
 facts = Table(
 [
 [Paragraph("Domain Code (Medical)", ParagraphStyle("FL",
 fontName="Helvetica", fontSize=9, textColor=HexColor('#64748b'))),
 Paragraph("OMNIX-MED-{12hex}", ParagraphStyle("FV",
 fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
 [Paragraph("Domain Code (Agent)", ParagraphStyle("FL",
 fontName="Helvetica", fontSize=9, textColor=HexColor('#64748b'))),
 Paragraph("OMNIX-AGT-{12hex}", ParagraphStyle("FV",
 fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
 [Paragraph("Cryptographic Proof", ParagraphStyle("FL",
 fontName="Helvetica", fontSize=9, textColor=HexColor('#64748b'))),
 Paragraph("Dilithium-3 Post-Quantum Signature", ParagraphStyle("FV",
 fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
 [Paragraph("Checkpoints", ParagraphStyle("FL",
 fontName="Helvetica", fontSize=9, textColor=HexColor('#64748b'))),
 Paragraph("11 sequential — all required — no override path", ParagraphStyle("FV",
 fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
 [Paragraph("Version", ParagraphStyle("FL",
 fontName="Helvetica", fontSize=9, textColor=HexColor('#64748b'))),
 Paragraph("1.0.0 — April 2026", ParagraphStyle("FV",
 fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
 [Paragraph("Author", ParagraphStyle("FL",
 fontName="Helvetica", fontSize=9, textColor=HexColor('#64748b'))),
 Paragraph("Harold Nunes — OMNIX Quantum Ltd", ParagraphStyle("FV",
 fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
 ],
 colWidths=[DW * 0.40, DW * 0.60]
 )
 facts.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (-1, -1), HexColor('#111827')),
 ('BOX', (0, 0), (-1, -1), 1, GOLD),
 ('LINEAFTER', (0, 0), (0, -1), 0.5, HexColor('#1e293b')),
 ('GRID', (0, 0), (-1, -1), 0.3, HexColor('#1e293b')),
 ('TOPPADDING', (0, 0), (-1, -1), 8),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
 ('LEFTPADDING', (0, 0), (-1, -1), 12),
 ('RIGHTPADDING', (0, 0), (-1, -1), 12),
 ]))
 story.append(facts)
 story.append(Spacer(1, 0.3 * inch))
 story.append(Paragraph(
 "CONFIDENTIAL — OMNIX Quantum Ltd — omnixquantum.net",
 ParagraphStyle("Conf", fontName="Helvetica-Oblique", fontSize=8,
 textColor=HexColor('#475569'), alignment=TA_CENTER)))

 story.append(PageBreak())

 # ════════════════════════════════════════════════════════════════════════
 # SECTION 1 — OVERVIEW
 # ════════════════════════════════════════════════════════════════════════
 story.append(SectionHeader("1", "Overview — The Admissibility Principle", DW))
 story.append(Spacer(1, 10))
 story.append(Paragraph(
 "OMNIX Autonomous Governance Layer (AGL) extends the core 11-checkpoint governance pipeline "
 "to two domains where AI makes high-stakes decisions without real-time human intervention: "
 "<b>Medical AI</b> and <b>Autonomous Agents</b>.",
 s['Body']))
 story.append(Spacer(1, 6))

 # The gap explained
 gap_data = [
 [Paragraph("What Most Systems Do", s['TH']),
 Paragraph("What OMNIX Does", s['TH'])],
 [Paragraph("Guardrails fire after output is generated", s['TD']),
 Paragraph("Governance evaluates before any execution path opens", s['TD'])],
 [Paragraph("Audit logs record what happened", s['TD']),
 Paragraph("Cryptographic receipts prove what was admissible", s['TD'])],
 [Paragraph("Monitoring detects anomalies after they propagate", s['TD']),
 Paragraph("Blocked decisions never reach the execution boundary", s['TD'])],
 [Paragraph("Human review is triggered post-failure", s['TD']),
 Paragraph("Human oversight is invoked pre-execution when required", s['TD'])],
 ]
 gap_table = Table(gap_data, colWidths=[DW / 2, DW / 2])
 gap_table.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (0, 0), RED),
 ('BACKGROUND', (1, 0), (1, 0), GREEN),
 ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
 ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
 ('GRID', (0, 0), (-1, -1), 0.3, BORDER),
 ('LINEAFTER', (0, 0), (0, -1), 0.5, BORDER),
 ('TOPPADDING', (0, 0), (-1, -1), 7),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
 ('LEFTPADDING', (0, 0), (-1, -1), 8),
 ('RIGHTPADDING', (0, 0), (-1, -1), 8),
 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
 ]))
 story.append(gap_table)
 story.append(Spacer(1, 10))

 # Callout box
 callout = Table(
 [[Paragraph(
 "If the decision is not admissible — the execution path does not exist.",
 ParagraphStyle("CB", fontName="Helvetica-Bold", fontSize=11,
 textColor=NAVY, alignment=TA_CENTER))]],
 colWidths=[DW]
 )
 callout.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (-1, -1), HexColor('#fef9ec')),
 ('BOX', (0, 0), (-1, -1), 2, GOLD),
 ('TOPPADDING', (0, 0), (-1, -1), 14),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
 ('LEFTPADDING', (0, 0), (-1, -1), 20),
 ('RIGHTPADDING', (0, 0), (-1, -1), 20),
 ]))
 story.append(callout)
 story.append(Spacer(1, 14))

 # Pipeline diagram as table
 story.append(SubHeader("The Governance Pipeline", DW))
 story.append(Spacer(1, 6))
 pipeline_steps = [
 ["INPUT", "Raw data from sensor, agent, or AI model"],
 ["AVM", "Assumption Validity Monitor — Guards: NaN, Stale, Drift"],
 ["CP-1 to CP-11", "11 Sequential Checkpoints — domain-adapted"],
 ["TIE", "Transaction Integrity Engine — PQC receipt generation"],
 ["OUTPUT", "APPROVED / BLOCKED / HOLD + Dilithium-3 signed receipt"],
 ]
 for step, desc in pipeline_steps:
 row = Table(
 [[Paragraph(step, ParagraphStyle("PS", fontName="Helvetica-Bold",
 fontSize=9, textColor=WHITE, alignment=TA_CENTER)),
 Paragraph(desc, ParagraphStyle("PD", fontName="Helvetica",
 fontSize=9, textColor=DARK_GRAY))]],
 colWidths=[DW * 0.22, DW * 0.78]
 )
 bg = NAVY if step in ["INPUT", "OUTPUT"] else (GOLD_DARK if step == "TIE" else DARK_GRAY)
 row.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (0, 0), bg),
 ('BACKGROUND', (1, 0), (1, 0), LIGHT_GRAY),
 ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
 ('TOPPADDING', (0, 0), (-1, -1), 7),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
 ('LEFTPADDING', (0, 0), (-1, -1), 8),
 ('RIGHTPADDING', (0, 0), (-1, -1), 8),
 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
 ]))
 story.append(row)
 if step != "OUTPUT":
 arrow = Table(
 [[Paragraph("▼", ParagraphStyle("AR", fontName="Helvetica",
 fontSize=10, textColor=GOLD, alignment=TA_CENTER))]],
 colWidths=[DW]
 )
 arrow.setStyle(TableStyle([
 ('TOPPADDING', (0, 0), (-1, -1), 1),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
 ]))
 story.append(arrow)
 story.append(Spacer(1, 16))
 story.append(PageBreak())

 # ════════════════════════════════════════════════════════════════════════
 # SECTION 2 — MEDICAL AI GOVERNANCE
 # ════════════════════════════════════════════════════════════════════════
 story.append(SectionHeader("2", "Medical AI Governance — OMNIX-MED", DW, MED_BLUE))
 story.append(Spacer(1, 10))

 story.append(Paragraph(
 "Clinical AI systems make decisions that directly affect patient outcomes — movement guidance, "
 "diagnostic alerts, therapeutic recommendations, surgical instructions. When these decisions "
 "execute without pre-execution governance, invalid or unsafe actions reach patients before "
 "any oversight can intervene. OMNIX-MED closes this gap.",
 s['Body']))
 story.append(Spacer(1, 10))

 # Use cases
 story.append(SubHeader("2.1 Target Use Cases", DW))
 story.append(Spacer(1, 6))
 uc_data = [
 ["Use Case", "Description", "Receipt"],
 ["Rehabilitation Wearables", "Real-time movement guidance, alert triggering for MSK patients", "OMNIX-MED"],
 ["Diagnostic AI", "Imaging analysis, symptom correlation, triage scoring", "OMNIX-MED"],
 ["Clinical Decision Support", "Treatment recommendation validation", "OMNIX-MED"],
 ["Remote Patient Monitoring", "Threshold-based alert governance", "OMNIX-MED"],
 ["Surgical Robotics", "Pre-action validation of robotic surgical decisions", "OMNIX-MED"],
 ]
 story.append(make_table(uc_data[0], uc_data[1:],
 [DW*0.28, DW*0.54, DW*0.18], s, MED_BLUE))
 story.append(Spacer(1, 12))

 # Regulatory alignment
 story.append(SubHeader("2.2 Regulatory Alignment", DW))
 story.append(Spacer(1, 6))
 reg_data = [
 ["Jurisdiction", "Regulation", "Key Requirement"],
 ["USA", "FDA 21 CFR Part 11, SaMD Guidance", "Audit trail, decision traceability"],
 ["EU", "EU MDR 2017/745, AI Act (High Risk)", "Transparency, human oversight capability"],
 ["UAE", "DOH AI Framework, DHA Digital Health Strategy", "Data governance, clinical AI accountability"],
 ["UK", "MHRA AI/ML SaMD Guidance", "Pre-market validation, post-market surveillance"],
 ]
 story.append(make_table(reg_data[0], reg_data[1:],
 [DW*0.12, DW*0.42, DW*0.46], s))
 story.append(Spacer(1, 12))

 # 11 Checkpoints MED
 story.append(SubHeader("2.3 The 11 Checkpoints — Medical Domain", DW))
 story.append(Spacer(1, 6))
 cp_data = [
 ["CP", "Checkpoint", "Medical Evaluation", "Block Condition"],
 ["CP-1", "Signal Integrity Validator", "Sensor data quality, device calibration status", "Null/corrupt data, calibration gap > 24h"],
 ["CP-2", "Clinical Probability Assessment", "Diagnostic confidence score, model certainty", "Confidence < 0.70 for therapeutic decisions"],
 ["CP-3", "Patient Risk Evaluation", "Risk stratification, contraindications, comorbidity", "High-risk flag without clinician override"],
 ["CP-4", "Clinical Coherence Engine", "Multi-signal alignment, symptom-decision consistency", "Decision Contradiction Index (DCI) > threshold"],
 ["CP-5", "Trajectory Validator", "Patient recovery trend, baseline deviation", "Adverse trajectory without escalation"],
 ["CP-6", "Stress Testing", "Edge cases, comorbidity amplification, device failure modes", "Tail-risk score > 0.85"],
 ["CP-7", "Clinical & Ethics Gate", "Ethics compliance, informed consent, off-label check", "Ethics flag raised, consent not verified"],
 ["CP-8", "Threshold & Context Validator", "Historical patient data consistency", "Context mismatch with care plan"],
 ["CP-9", "Billing & Fraud Screening", "Clinical billing integrity, insurance fraud indicators", "Anomalous billing pattern detected"],
 ["CP-10", "Data Manipulation Detection", "Clinical data integrity, tamper detection", "SHA-256 mismatch on patient record"],
 ["CP-11", "Regulatory Compliance Gate", "FDA/MDR/DOH jurisdiction validation", "Non-compliant action for jurisdiction"],
 ]
 cp_table = make_table(cp_data[0], cp_data[1:],
 [DW*0.08, DW*0.24, DW*0.36, DW*0.32], s)
 story.append(cp_table)
 story.append(Spacer(1, 12))

 # Apollo Medica integration
 story.append(SubHeader("2.4 Integration Model — Apollo Medica (MSK Wearables)", DW))
 story.append(Spacer(1, 6))
 story.append(Paragraph(
 "Apollo Medica's Large Motion Model (LOM) makes real-time movement guidance decisions for "
 "musculoskeletal rehabilitation patients. Each decision passes through OMNIX-MED before "
 "reaching the wearable output — making every guidance decision provable, auditable, and "
 "insurable by underwriters.",
 s['Body']))
 story.append(Spacer(1, 8))

 flow_steps = [
 ("Sensor Input", "Biofeedback + motion data from wearable device", DARK_GRAY),
 ("OMNIX-MED Pipeline", "11 checkpoints evaluate clinical admissibility", NAVY),
 ("BLOCKED", "No output to patient device — action logged", RED),
 ("APPROVED + Receipt", "OMNIX-MED-{12hex} issued, Dilithium-3 signed", GREEN),
 ("Wearable Executes", "Guidance delivered — receipt visible in clinician dashboard", DARK_GRAY),
 ]
 for label, desc, color in flow_steps:
 row = Table(
 [[Paragraph(label, ParagraphStyle("FL", fontName="Helvetica-Bold",
 fontSize=8.5, textColor=WHITE, alignment=TA_CENTER)),
 Paragraph(desc, ParagraphStyle("FD", fontName="Helvetica",
 fontSize=8.5, textColor=DARK_GRAY))]],
 colWidths=[DW * 0.28, DW * 0.72]
 )
 row.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (0, 0), color),
 ('BACKGROUND', (1, 0), (1, 0), LIGHT_GRAY),
 ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
 ('TOPPADDING', (0, 0), (-1, -1), 6),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
 ('LEFTPADDING', (0, 0), (-1, -1), 8),
 ('RIGHTPADDING', (0, 0), (-1, -1), 8),
 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
 ]))
 story.append(row)
 if label not in ["Wearable Executes", "BLOCKED"]:
 arrow = Table([[Paragraph("▼", ParagraphStyle("AR",
 fontName="Helvetica", fontSize=9, textColor=GOLD,
 alignment=TA_CENTER))]], colWidths=[DW])
 arrow.setStyle(TableStyle([('TOPPADDING', (0,0),(-1,-1),1),
 ('BOTTOMPADDING', (0,0),(-1,-1),1)]))
 story.append(arrow)

 story.append(Spacer(1, 16))
 story.append(PageBreak())

 # ════════════════════════════════════════════════════════════════════════
 # SECTION 3 — AUTONOMOUS AGENT GOVERNANCE
 # ════════════════════════════════════════════════════════════════════════
 story.append(SectionHeader("3", "Autonomous Agent Governance — OMNIX-AGT", DW, AGT_GREEN))
 story.append(Spacer(1, 10))

 story.append(Paragraph(
 "Autonomous AI agents execute multi-step tasks — financial transactions, data modifications, "
 "communications, workflow orchestration — without human approval for each action. As agents "
 "operate at scale and speed, the blast radius of an ungoverned decision grows exponentially. "
 "OMNIX-AGT enforces admissibility before any agent action reaches the execution boundary.",
 s['Body']))
 story.append(Spacer(1, 10))

 # Use cases
 story.append(SubHeader("3.1 Target Use Cases", DW))
 story.append(Spacer(1, 6))
 uc2_data = [
 ["Use Case", "Description", "Receipt"],
 ["Agentic AI Systems", "Multi-step AI agents executing tasks autonomously", "OMNIX-AGT"],
 ["Algorithmic Trading Bots", "High-frequency automated order execution", "OMNIX-AGT"],
 ["Cross-Border Payment Agents", "Autonomous payment routing and execution", "OMNIX-AGT"],
 ["Enterprise AI Agents", "AI modifying data, sending communications, executing workflows", "OMNIX-AGT"],
 ["Supply Chain Automation", "Autonomous procurement and logistics decisions", "OMNIX-AGT"],
 ]
 story.append(make_table(uc2_data[0], uc2_data[1:],
 [DW*0.28, DW*0.54, DW*0.18], s, AGT_GREEN))
 story.append(Spacer(1, 12))

 # 11 Checkpoints AGT
 story.append(SubHeader("3.2 The 11 Checkpoints — Autonomous Agent Domain", DW))
 story.append(Spacer(1, 6))
 cp2_data = [
 ["CP", "Checkpoint", "Agent Evaluation", "Block Condition"],
 ["CP-1", "Signal Integrity Validator", "Input data quality, prompt integrity, source validation", "Null/malformed input, unverified source"],
 ["CP-2", "Action Probability Assessment", "Success likelihood of proposed agent action", "Confidence < configured threshold"],
 ["CP-3", "Risk Evaluation", "Blast radius, exposure, reversibility check", "Irreversible action with risk score > threshold"],
 ["CP-4", "Coherence Engine", "Intent alignment, action-goal consistency", "Decision Contradiction Index (DCI) > threshold"],
 ["CP-5", "Behavior Trend Validator", "Agent behavior pattern stability, baseline drift", "Behavioral drift > configured threshold"],
 ["CP-6", "Adversarial Stress Testing", "Prompt injection resistance, edge case evaluation", "Adversarial signal detected"],
 ["CP-7", "Domain Boundary Gate", "Permission boundary check, scope limitation, role validation", "Action exceeds defined permission scope"],
 ["CP-8", "Threshold & Context Validator", "Historical action consistency, session coherence", "Context mismatch with agent charter"],
 ["CP-9", "Regulatory Compliance Screening", "AML, sanctions, data protection, sector-specific checks", "Regulatory flag for action jurisdiction"],
 ["CP-10", "Manipulation Detection", "Prompt injection, adversarial instructions, hallucination flag", "Manipulation indicator above threshold"],
 ["CP-11", "Jurisdiction Compliance Gate", "EU AI Act, UAE AI Strategy 2031, US EO validation", "Non-compliant action for jurisdiction"],
 ]
 story.append(make_table(cp2_data[0], cp2_data[1:],
 [DW*0.08, DW*0.24, DW*0.36, DW*0.32], s))
 story.append(Spacer(1, 12))

 # Velos integration
 story.append(SubHeader("3.3 Integration Model — Velos T=0 Enforcement", DW))
 story.append(Spacer(1, 6))
 story.append(Paragraph(
 "For autonomous agent deployments requiring physical execution enforcement, OMNIX-AGT "
 "integrates with Velos at the execution boundary. OMNIX governs admissibility. "
 "Velos enforces the halt or release at T=0. Neither operates without the other "
 "in the joint stack.",
 s['Body']))
 story.append(Spacer(1, 8))

 flow2_steps = [
 ("Agent Decision Proposal", "Multi-step action request from autonomous AI agent", DARK_GRAY),
 ("OMNIX-AGT Pipeline", "11 checkpoints evaluate action admissibility", NAVY),
 ("BLOCKED", "Velos T=0 halt — no execution — action logged", RED),
 ("APPROVED + Receipt", "OMNIX-AGT-{12hex} issued, Dilithium-3 signed", GREEN),
 ("Velos Executes", "T=0 enforcement — receipt cryptographically anchored", DARK_GRAY),
 ]
 for label, desc, color in flow2_steps:
 row = Table(
 [[Paragraph(label, ParagraphStyle("FL2", fontName="Helvetica-Bold",
 fontSize=8.5, textColor=WHITE, alignment=TA_CENTER)),
 Paragraph(desc, ParagraphStyle("FD2", fontName="Helvetica",
 fontSize=8.5, textColor=DARK_GRAY))]],
 colWidths=[DW * 0.28, DW * 0.72]
 )
 row.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (0, 0), color),
 ('BACKGROUND', (1, 0), (1, 0), LIGHT_GRAY),
 ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
 ('TOPPADDING', (0, 0), (-1, -1), 6),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
 ('LEFTPADDING', (0, 0), (-1, -1), 8),
 ('RIGHTPADDING', (0, 0), (-1, -1), 8),
 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
 ]))
 story.append(row)
 if label not in ["Velos Executes", "BLOCKED"]:
 arrow = Table([[Paragraph("▼", ParagraphStyle("AR2",
 fontName="Helvetica", fontSize=9, textColor=GOLD,
 alignment=TA_CENTER))]], colWidths=[DW])
 arrow.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),1),
 ('BOTTOMPADDING',(0,0),(-1,-1),1)]))
 story.append(arrow)

 story.append(Spacer(1, 16))
 story.append(PageBreak())

 # ════════════════════════════════════════════════════════════════════════
 # SECTION 4 — SHARED ARCHITECTURE
 # ════════════════════════════════════════════════════════════════════════
 story.append(SectionHeader("4", "Shared Architecture & Cryptographic Proof", DW))
 story.append(Spacer(1, 10))

 story.append(SubHeader("4.1 AVM — Assumption Validity Monitor", DW))
 story.append(Spacer(1, 6))
 story.append(Paragraph(
 "All decisions — regardless of domain — pass through the AVM before entering the "
 "11-checkpoint pipeline. The AVM enforces three blocking guards:",
 s['Body']))
 story.append(Spacer(1, 6))
 avm_data = [
 ["Guard", "Condition", "Outcome"],
 ["NON_FINITE_SIGNAL", "NaN or Inf in any input signal", "BLOCK — no pipeline entry"],
 ["CRITICAL_STALE", "Data age exceeds domain threshold", "BLOCK — stale data"],
 ["DRIFT_BLOCK", "Weighted drift exceeds baseline threshold", "BLOCK — baseline violation"],
 ["PASS", "All guards clear", "Pipeline entry — CERTIFIED"],
 ]
 story.append(make_table(avm_data[0], avm_data[1:],
 [DW*0.28, DW*0.40, DW*0.32], s))
 story.append(Spacer(1, 12))

 story.append(SubHeader("4.2 Receipt Engine & PQC Signatures", DW))
 story.append(Spacer(1, 6))
 story.append(Paragraph(
 "Every admissible decision generates a cryptographic receipt via "
 "<b>DecisionReceiptEngine.build_receipt_id(domain)</b>. The receipt is signed "
 "with Dilithium-3 post-quantum cryptography — tamper-proof and quantum-resistant.",
 s['Body']))
 story.append(Spacer(1, 6))
 receipt_data = [
 ["Domain", "Code", "Receipt Format", "Signing Algorithm"],
 ["Medical AI", "MED", "OMNIX-MED-{12hex}", "Dilithium-3 (PQC)"],
 ["Autonomous Agent", "AGT", "OMNIX-AGT-{12hex}", "Dilithium-3 (PQC)"],
 ["Trading", "TRD", "OMNIX-TRD-{12hex}", "Dilithium-3 (PQC)"],
 ["Islamic Credit", "CRD", "OMNIX-CRD-{12hex}", "Dilithium-3 (PQC)"],
 ["Insurance", "INS", "OMNIX-INS-{12hex}", "Dilithium-3 (PQC)"],
 ["Robotics", "RBT", "OMNIX-RBT-{12hex}", "Dilithium-3 (PQC)"],
 ]
 story.append(make_table(receipt_data[0], receipt_data[1:],
 [DW*0.25, DW*0.10, DW*0.35, DW*0.30], s))
 story.append(Spacer(1, 12))

 story.append(SubHeader("4.3 Fail-Closed Policy — When In Doubt, Block", DW))
 story.append(Spacer(1, 6))
 fail_data = [
 ["Scenario", "MED Behaviour", "AGT Behaviour"],
 ["DB offline", "DEGRADED warning, JSON fallback", "DEGRADED warning, JSON fallback"],
 ["TAMPERED snapshot", "BLOCK — logged, alert raised", "BLOCK — logged, alert raised"],
 ["AVM_FAIL_CLOSED=true", "RuntimeError — halt all decisions", "RuntimeError — halt all decisions"],
 ["Non-finite signal", "BLOCK — NON_FINITE_BLOCK raised", "BLOCK — NON_FINITE_BLOCK raised"],
 ]
 story.append(make_table(fail_data[0], fail_data[1:],
 [DW*0.34, DW*0.33, DW*0.33], s))
 story.append(Spacer(1, 16))

 # ════════════════════════════════════════════════════════════════════════
 # SECTION 5 — REGULATORY LANDSCAPE
 # ════════════════════════════════════════════════════════════════════════
 story.append(SectionHeader("5", "Regulatory Landscape", DW))
 story.append(Spacer(1, 10))
 story.append(Paragraph(
 "Both Medical AI and Autonomous Agent systems are explicitly categorised as High Risk AI "
 "under major regulatory frameworks. Pre-execution governance with cryptographic proof is no "
 "longer optional — it is becoming a compliance requirement.",
 s['Body']))
 story.append(Spacer(1, 8))
 reg2_data = [
 ["Framework", "MED Relevance", "AGT Relevance"],
 ["EU AI Act (2024)", "High Risk — medical device AI requires pre-execution governance", "High Risk — autonomous AI requires mandatory auditability"],
 ["UAE AI Strategy 2031", "DOH clinical AI accountability requirements", "National AI governance and traceability requirements"],
 ["FDA SaMD Guidance", "Clinical decision software validation and traceability", "N/A"],
 ["NIST AI RMF", "AI risk management for clinical systems", "AI risk management for autonomous systems"],
 ["ISO 42001 (AI Mgmt)", "Clinical AI management system standard", "Autonomous AI management system standard"],
 ]
 story.append(make_table(reg2_data[0], reg2_data[1:],
 [DW*0.25, DW*0.375, DW*0.375], s))
 story.append(Spacer(1, 16))

 # ════════════════════════════════════════════════════════════════════════
 # SECTION 6 — PRICING
 # ════════════════════════════════════════════════════════════════════════
 story.append(SectionHeader("6", "Pricing", DW))
 story.append(Spacer(1, 10))
 price_data = [
 ["Tier", "Description", "Price"],
 ["Standard", "Single domain (MED or AGT) — up to 10K governed decisions/day", "$8,000 / month"],
 ["Professional", "Dual domain — up to 100K decisions/day — compliance reporting included", "$20,000 / month"],
 ["Enterprise", "Unlimited decisions — custom checkpoints — regulatory integration", "$35,000 / month"],
 ["Velos Bundle", "OMNIX-AGT + Velos T=0 enforcement — joint bundled stack", "Custom"],
 ]
 price_table = make_table(price_data[0], price_data[1:],
 [DW*0.18, DW*0.57, DW*0.25], s)
 story.append(price_table)
 story.append(Spacer(1, 20))

 # ── CLOSING ───────────────────────────────────────────────────────────────
 story.append(GoldRule(DW, 1.5))
 story.append(Spacer(1, 10))
 story.append(Paragraph(
 "OMNIX Quantum Ltd — Decision Governance Infrastructure",
 ParagraphStyle("Close1", fontName="Helvetica-Bold", fontSize=10,
 textColor=NAVY, alignment=TA_CENTER)))
 story.append(Paragraph(
 "Harold Nunes — Founder | omnixquantum.net | 
 ParagraphStyle("Close2", fontName="Helvetica", fontSize=8.5,
 textColor=MID_GRAY, alignment=TA_CENTER, spaceBefore=3)))
 story.append(Paragraph(
 "Confidential — Not for distribution without written authorisation from OMNIX Quantum Ltd",
 s['FootNote']))

 # Build with cover template for page 1, normal for rest
 def on_page(canvas_obj, doc_obj):
 if canvas_obj.getPageNumber() == 1:
 cover_template(canvas_obj, doc_obj)
 else:
 page_template(canvas_obj, doc_obj)

 doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
 print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
 build_pdf()
