"""
OMNIX x Velos — Shared Pipeline Log
Clause 4.4 — Supplement to Agreement Clause 10.1
Registro de integración y operativa conjunta
White background, gold accents, professional enterprise style
"""

import os
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# ── COLOURS ───────────────────────────────────────────────────────────────────
GOLD        = HexColor('#C9A227')
GOLD_LIGHT  = HexColor('#fef9ec')
GOLD_DARK   = HexColor('#a07820')
NAVY        = HexColor('#0a0f1a')
DARK_GRAY   = HexColor('#1e293b')
MID_GRAY    = HexColor('#475569')
LIGHT_GRAY  = HexColor('#f1f5f9')
BORDER      = HexColor('#e2e8f0')
WHITE       = HexColor('#ffffff')
GREEN       = HexColor('#059669')
GREEN_LIGHT = HexColor('#d1fae5')
SLATE       = HexColor('#64748b')

LOGO_PATH   = os.path.join(os.path.dirname(__file__), '..', 'assets', 'omnix_logo.png')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..',
                           'OMNIX_Velos_Pipeline_Log_v1.pdf')

W, H = A4
TODAY = date.today().strftime("%d %B %Y")


# ── PAGE TEMPLATES ────────────────────────────────────────────────────────────
def page_template(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFillColor(WHITE)
    canvas_obj.rect(0, 0, W, H, fill=1, stroke=0)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.rect(0, 0, 5, H, fill=1, stroke=0)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.rect(0, H - 5, W, 5, fill=1, stroke=0)
    canvas_obj.setStrokeColor(BORDER)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(1.0 * inch, 0.58 * inch, W - 1.0 * inch, 0.58 * inch)
    canvas_obj.setFillColor(MID_GRAY)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawString(1.0 * inch, 0.40 * inch,
        "OMNIX x Velos — Shared Pipeline Log — Clause 4.4 | Strictly Confidential")
    canvas_obj.drawRightString(W - 1.0 * inch, 0.40 * inch,
        f"Page {canvas_obj.getPageNumber()}")
    canvas_obj.drawCentredString(W / 2, 0.40 * inch, TODAY)
    canvas_obj.restoreState()


def cover_template(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFillColor(NAVY)
    canvas_obj.rect(0, 0, W, H, fill=1, stroke=0)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.rect(0, 0, 6, H, fill=1, stroke=0)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.rect(0, H - 6, W, 6, fill=1, stroke=0)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.rect(0, 0, W, 4, fill=1, stroke=0)
    canvas_obj.setFillColor(HexColor('#64748b'))
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawCentredString(W / 2, 0.32 * inch,
        "OMNIX Quantum Ltd x Velos — Strictly Confidential")
    canvas_obj.restoreState()


# ── STYLES ────────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()
    defs = [
        ("CoverMeta", dict(fontName="Helvetica", fontSize=9,
            textColor=HexColor('#94a3b8'), alignment=TA_LEFT, spaceAfter=3, leading=14)),
        ("Body", dict(fontName="Helvetica", fontSize=9.5,
            textColor=DARK_GRAY, alignment=TA_JUSTIFY,
            spaceAfter=5, spaceBefore=0, leading=15)),
        ("TH", dict(fontName="Helvetica-Bold", fontSize=8.5,
            textColor=WHITE, alignment=TA_LEFT, leading=12)),
        ("TD", dict(fontName="Helvetica", fontSize=8.5,
            textColor=DARK_GRAY, alignment=TA_LEFT, leading=12)),
        ("TDBold", dict(fontName="Helvetica-Bold", fontSize=8.5,
            textColor=NAVY, alignment=TA_LEFT, leading=12)),
        ("TDGreen", dict(fontName="Helvetica-Bold", fontSize=8.5,
            textColor=GREEN, alignment=TA_CENTER, leading=12)),
        ("FootNote", dict(fontName="Helvetica-Oblique", fontSize=7.5,
            textColor=MID_GRAY, alignment=TA_CENTER, spaceAfter=2, spaceBefore=6)),
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
    def __init__(self, w, t=1.2):
        super().__init__()
        self.width = w
        self.height = t + 4
        self.t = t
    def draw(self):
        self.canv.setFillColor(GOLD)
        self.canv.rect(0, 1, self.width, self.t, fill=1, stroke=0)


class SectionBanner(Flowable):
    def __init__(self, title, dw):
        super().__init__()
        self.title = title
        self.width = dw
        self.height = 30
    def draw(self):
        self.canv.setFillColor(GOLD)
        self.canv.rect(0, 0, 4, self.height, fill=1, stroke=0)
        self.canv.setFillColor(LIGHT_GRAY)
        self.canv.rect(4, 0, self.width - 4, self.height, fill=1, stroke=0)
        self.canv.setStrokeColor(BORDER)
        self.canv.setLineWidth(0.4)
        self.canv.line(4, 0, self.width, 0)
        self.canv.setFillColor(NAVY)
        self.canv.setFont("Helvetica-Bold", 11)
        self.canv.drawString(14, 9, self.title)


def make_table(headers, rows, col_widths, s):
    head_row = [Paragraph(h, s['TH']) for h in headers]
    data_rows = []
    bgs = [WHITE, LIGHT_GRAY]
    for i, row in enumerate(rows):
        data_rows.append([Paragraph(str(c), s['TD']) for c in row])
    t = Table([head_row] + data_rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('BOX',  (0, 0), (-1, -1), 0.5, BORDER),
        ('GRID', (0, 0), (-1, -1), 0.3, BORDER),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


def callout_box(text, s):
    t = Table(
        [[Paragraph(text, ParagraphStyle("CB", fontName="Helvetica-Bold",
            fontSize=10, textColor=NAVY, alignment=TA_CENTER, leading=15))]],
        colWidths=[None]
    )
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GOLD_LIGHT),
        ('BOX', (0, 0), (-1, -1), 2, GOLD),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
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
    # COVER
    # ════════════════════════════════════════════════════════════════════════
    if os.path.exists(LOGO_PATH):
        from reportlab.platypus import Image
        logo = Image(LOGO_PATH, width=1.8 * inch, height=0.62 * inch)
        logo.hAlign = "LEFT"
        story.append(logo)

    story.append(Spacer(1, 0.45 * inch))
    story.append(Paragraph("JOINT STACK — INTEGRATION LOG", ParagraphStyle("Eye",
        fontName="Helvetica-Bold", fontSize=9, textColor=GOLD,
        alignment=TA_LEFT, spaceAfter=6)))
    story.append(Paragraph("OMNIX x Velos", ParagraphStyle("CT",
        fontName="Helvetica-Bold", fontSize=38, textColor=GOLD,
        alignment=TA_LEFT, spaceAfter=6, leading=44)))
    story.append(Paragraph("Shared Pipeline Log", ParagraphStyle("CS",
        fontName="Helvetica-Bold", fontSize=20, textColor=WHITE,
        alignment=TA_LEFT, spaceAfter=8, leading=26)))
    story.append(Paragraph(
        "Architectural boundaries, commercial tracks, operational mechanics "
        "and integration status — per Clause 4.4 of the Supplement to Agreement Clause 10.1.",
        ParagraphStyle("CD", fontName="Helvetica", fontSize=11,
        textColor=HexColor('#94a3b8'), alignment=TA_LEFT, leading=17, spaceAfter=30)))

    story.append(GoldRule(DW, 1))
    story.append(Spacer(1, 0.25 * inch))

    meta = Table(
        [
            [Paragraph("Document Reference", s['CoverMeta']),
             Paragraph("OMNIX-VLS-PL-001", ParagraphStyle("MV",
                fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
            [Paragraph("Clause Reference", s['CoverMeta']),
             Paragraph("Supplement to Clause 10.1 — §4.4 Pipeline Transparency",
                ParagraphStyle("MV", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
            [Paragraph("Version", s['CoverMeta']),
             Paragraph("v1.0 — Initial log", ParagraphStyle("MV",
                fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
            [Paragraph("Date", s['CoverMeta']),
             Paragraph(TODAY, ParagraphStyle("MV",
                fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
            [Paragraph("OMNIX", s['CoverMeta']),
             Paragraph("Harold Nunes — OMNIX Quantum Ltd",
                ParagraphStyle("MV", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
            [Paragraph("Velos", s['CoverMeta']),
             Paragraph("Naimat Khan — Velos",
                ParagraphStyle("MV", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
        ],
        colWidths=[DW * 0.38, DW * 0.62]
    )
    meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#111827')),
        ('BOX', (0, 0), (-1, -1), 1, GOLD),
        ('LINEAFTER', (0, 0), (0, -1), 0.4, HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.3, HexColor('#1e293b')),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta)
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "STRICTLY CONFIDENTIAL — OMNIX Quantum Ltd and Velos only.",
        ParagraphStyle("Conf", fontName="Helvetica-Oblique", fontSize=7.5,
        textColor=HexColor('#475569'), alignment=TA_CENTER)))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 1 — WHAT WE BUILT TOGETHER
    # ════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("1.  What We Built Together", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "The OMNIX x Velos joint stack connects two complementary and non-overlapping layers "
        "into a single end-to-end governance and execution infrastructure. "
        "OMNIX governs every decision before it executes. Velos enforces the execution at T=0. "
        "Neither layer replicates the other.",
        s['Body']))
    story.append(Spacer(1, 10))

    layers = [
        ["Layer", "Owner", "Function", "Receipt / Signal"],
        ["Governance Layer", "OMNIX", "11-checkpoint pre-execution pipeline. Every decision "
         "evaluated before reaching the execution boundary. Post-quantum signed receipt issued "
         "on approval (Dilithium-3).", "OMNIX-{DOMAIN}-{12hex}"],
        ["Execution Layer", "Velos", "Physical lock enforcement at T=0. No action executes "
         "without a valid OMNIX receipt. Velos drops the lock only on APPROVED decisions.",
         "T=0 enforcement signal"],
    ]
    story.append(make_table(layers[0], layers[1:],
                            [DW*0.20, DW*0.12, DW*0.46, DW*0.22], s))
    story.append(Spacer(1, 12))

    story.append(callout_box(
        "OMNIX governs — Velos executes — no overlap — no gap.", s))
    story.append(Spacer(1, 16))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 2 — ARCHITECTURAL BOUNDARIES (LOCKED)
    # ════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("2.  Architectural Boundaries — Locked", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "The following boundaries are officially locked per the executed Supplement "
        "to Agreement Clause 10.1. These do not change without a new written agreement.",
        s['Body']))
    story.append(Spacer(1, 8))

    boundaries = [
        ["Boundary", "Definition", "Status"],
        ["OMNIX scope", "Pre-execution governance pipeline. Ends at the execution boundary. "
         "Does not control, instruct, or override Velos execution.", "LOCKED ✓"],
        ["Velos scope", "Physical execution enforcement layer. Begins where OMNIX ends. "
         "Does not evaluate, score, or replace governance logic.", "LOCKED ✓"],
        ["Receipt authority", "OMNIX is the sole issuer of governance receipts. "
         "Velos is the sole enforcer of the execution lock.", "LOCKED ✓"],
        ["Liability separation", "Each party is solely responsible for its own layer. "
         "No joint liability created.", "LOCKED ✓"],
        ["Brand visibility", "Velos is explicitly identified to the end-client "
         "as the terminal enforcement provider in all Track A deployments.", "LOCKED ✓"],
    ]
    story.append(make_table(boundaries[0], boundaries[1:],
                            [DW*0.22, DW*0.58, DW*0.20], s))
    story.append(Spacer(1, 16))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 3 — COMMERCIAL TRACKS (LOCKED)
    # ════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("3.  Commercial Tracks — Locked", DW))
    story.append(Spacer(1, 10))

    tracks = [
        ["", "Track A — Unified Route", "Track B — Modular Route"],
        ["Structure", "Single contract, single invoice through OMNIX as primary contractor",
         "Velos bills client directly for execution layer. OMNIX operates independently."],
        ["Who bills client", "OMNIX", "Velos"],
        ["OMNIX revenue", "70% of joint contract value", "100% of own module fee"],
        ["Velos revenue", "30% of joint contract value", "$4,500/month direct from client"],
        ["Written approval", "Required from both parties before any Track A deployment",
         "Velos must obtain written OMNIX approval before engaging any client (§4.3)"],
        ["Brand visibility", "Velos explicitly identified to end-client and in audit trail",
         "Velos operates independently on its layer"],
    ]

    t_head = [Paragraph(h, s['TH']) for h in tracks[0]]
    t_rows = []
    for i, row in enumerate(tracks[1:]):
        bg = WHITE if i % 2 == 0 else LIGHT_GRAY
        t_rows.append([Paragraph(str(c), s['TDBold'] if i == 0 else s['TD'])
                       for c in row])

    track_table = Table([t_head] + t_rows,
                        colWidths=[DW*0.20, DW*0.40, DW*0.40])
    track_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('BACKGROUND', (0, 1), (0, -1), LIGHT_GRAY),
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('BOX',  (0, 0), (-1, -1), 0.5, BORDER),
        ('GRID', (0, 0), (-1, -1), 0.3, BORDER),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(track_table)
    story.append(Spacer(1, 16))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 4 — HOW THE JOINT STACK WORKS IN PRACTICE
    # ════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("4.  How the Joint Stack Works in Practice", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "When a client deploys the OMNIX x Velos joint stack, every decision follows "
        "this sequence — without exception:",
        s['Body']))
    story.append(Spacer(1, 8))

    flow_steps = [
        ("Decision Input", "Client system submits decision for evaluation", DARK_GRAY),
        ("OMNIX — 11 Checkpoints", "AVM + full pipeline evaluation. BLOCKED or APPROVED.", NAVY),
        ("Receipt Issued", "OMNIX-{DOMAIN}-{12hex} — Dilithium-3 signed — immutable", HexColor('#059669')),
        ("Velos — T=0 Enforcement", "Receipt received. Physical lock dropped on APPROVED only.", HexColor('#2563eb')),
        ("Execution", "Action executes. Receipt logged. Full audit trail available.", DARK_GRAY),
    ]
    for i, (label, desc, color) in enumerate(flow_steps):
        row = Table(
            [[Paragraph(label, ParagraphStyle(f"FL{i}", fontName="Helvetica-Bold",
                fontSize=8.5, textColor=WHITE, alignment=TA_CENTER)),
              Paragraph(desc, ParagraphStyle(f"FD{i}", fontName="Helvetica",
                fontSize=8.5, textColor=DARK_GRAY))]],
            colWidths=[DW * 0.28, DW * 0.72]
        )
        row.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), color),
            ('BACKGROUND', (1, 0), (1, 0), LIGHT_GRAY),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(row)
        if i < len(flow_steps) - 1:
            arrow = Table([[Paragraph("▼", ParagraphStyle(f"AR{i}",
                fontName="Helvetica", fontSize=9, textColor=GOLD,
                alignment=TA_CENTER))]], colWidths=[DW])
            arrow.setStyle(TableStyle([
                ('TOPPADDING', (0,0),(-1,-1), 1),
                ('BOTTOMPADDING', (0,0),(-1,-1), 1),
            ]))
            story.append(arrow)

    story.append(Spacer(1, 16))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 5 — DOMAINS READY FOR JOINT DEPLOYMENT
    # ════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("5.  Domains Ready for Joint Deployment", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "The following OMNIX governance domains are operational and ready "
        "to deploy with Velos enforcement:",
        s['Body']))
    story.append(Spacer(1, 8))

    domains = [
        ["Domain", "Receipt Format", "Sectors", "Status"],
        ["Trading", "OMNIX-TRD-{12hex}", "Digital assets, algorithmic trading, HFT", "OPERATIONAL ✓"],
        ["Islamic Credit", "OMNIX-CRD-{12hex}", "Murabaha, Ijara, SME Islamic finance", "OPERATIONAL ✓"],
        ["Insurance", "OMNIX-INS-{12hex}", "Claim triage, underwriting, risk assessment", "OPERATIONAL ✓"],
        ["Robotics", "OMNIX-RBT-{12hex}", "Industrial automation, autonomous hardware", "OPERATIONAL ✓"],
        ["Medical AI", "OMNIX-MED-{12hex}", "Wearables, diagnostics, clinical decision support", "READY ✓"],
        ["Autonomous Agents", "OMNIX-AGT-{12hex}", "Enterprise AI agents, autonomous workflows", "READY ✓"],
    ]
    story.append(make_table(domains[0], domains[1:],
                            [DW*0.18, DW*0.26, DW*0.36, DW*0.20], s))
    story.append(Spacer(1, 16))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 6 — NEXT STEPS
    # ════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("6.  Next Steps — Transition to Scaling", DW))
    story.append(Spacer(1, 10))

    next_steps = [
        ["Step", "Owner", "Action"],
        ["1", "Both", "Map first joint deployment — identify client, domain, track"],
        ["2", "Velos", "Confirm physical lock integration point with OMNIX receipt endpoint"],
        ["3", "OMNIX", "Provide receipt schema and API spec for Velos integration"],
        ["4", "Both", "Agree client communication — how joint stack is presented"],
        ["5", "Both", "Execute first live deployment under agreed track"],
    ]
    story.append(make_table(next_steps[0], next_steps[1:],
                            [DW*0.08, DW*0.14, DW*0.78], s))
    story.append(Spacer(1, 20))

    # ── CLOSING ───────────────────────────────────────────────────────────────
    story.append(GoldRule(DW, 1.2))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "OMNIX Quantum Ltd   ×   Velos",
        ParagraphStyle("CL1", fontName="Helvetica-Bold", fontSize=10,
            textColor=NAVY, alignment=TA_CENTER)))
    story.append(Paragraph(
        f"Shared Pipeline Log — v1.0 — {TODAY} — Clause 4.4",
        ParagraphStyle("CL2", fontName="Helvetica", fontSize=8.5,
            textColor=MID_GRAY, alignment=TA_CENTER, spaceBefore=3)))
    story.append(Paragraph(
        "Strictly Confidential — Not for third-party distribution",
        s['FootNote']))

    def on_page(canvas_obj, doc_obj):
        if canvas_obj.getPageNumber() == 1:
            cover_template(canvas_obj, doc_obj)
        else:
            page_template(canvas_obj, doc_obj)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF generado: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
