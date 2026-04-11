"""
OMNIX x Velos — Shared Pipeline Log
Clause 4.4 — Supplement to Agreement Clause 10.1
Professional PDF — White background, gold accents
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
GOLD_LIGHT  = HexColor('#f9f0d5')
GOLD_DARK   = HexColor('#a07820')
NAVY        = HexColor('#0a0f1a')
DARK_GRAY   = HexColor('#1e293b')
MID_GRAY    = HexColor('#475569')
LIGHT_GRAY  = HexColor('#f1f5f9')
BORDER      = HexColor('#e2e8f0')
WHITE       = HexColor('#ffffff')
GREEN       = HexColor('#059669')
GREEN_LIGHT = HexColor('#d1fae5')
AMBER       = HexColor('#d97706')
AMBER_LIGHT = HexColor('#fef3c7')
BLUE        = HexColor('#2563eb')
BLUE_LIGHT  = HexColor('#dbeafe')
SLATE       = HexColor('#64748b')
RED         = HexColor('#dc2626')
RED_LIGHT   = HexColor('#fee2e2')

LOGO_PATH   = os.path.join(os.path.dirname(__file__), '..', 'assets', 'omnix_logo.png')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..',
                           'OMNIX_Velos_Pipeline_Log_v1.pdf')

W, H = A4
TODAY = date.today().strftime("%d %B %Y")


# ── PAGE TEMPLATE ─────────────────────────────────────────────────────────────
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
        "OMNIX Quantum Ltd x Velos — Strictly Confidential — Not for third-party distribution")
    canvas_obj.restoreState()


# ── STYLES ────────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()
    defs = [
        ("CoverEyebrow", dict(fontName="Helvetica", fontSize=9,
            textColor=GOLD, alignment=TA_LEFT, spaceAfter=4, leading=13)),
        ("CoverTitle", dict(fontName="Helvetica-Bold", fontSize=34,
            textColor=GOLD, alignment=TA_LEFT, spaceAfter=4, leading=40)),
        ("CoverSub", dict(fontName="Helvetica-Bold", fontSize=16,
            textColor=WHITE, alignment=TA_LEFT, spaceAfter=6, leading=22)),
        ("CoverMeta", dict(fontName="Helvetica", fontSize=9,
            textColor=HexColor('#94a3b8'), alignment=TA_LEFT, spaceAfter=3, leading=14)),
        ("Body", dict(fontName="Helvetica", fontSize=9.5,
            textColor=DARK_GRAY, alignment=TA_JUSTIFY,
            spaceAfter=5, spaceBefore=0, leading=15)),
        ("BodyBold", dict(fontName="Helvetica-Bold", fontSize=9.5,
            textColor=DARK_GRAY, alignment=TA_LEFT, spaceAfter=4, leading=15)),
        ("Small", dict(fontName="Helvetica", fontSize=8,
            textColor=MID_GRAY, alignment=TA_LEFT, spaceAfter=3, leading=12)),
        ("TH", dict(fontName="Helvetica-Bold", fontSize=8,
            textColor=WHITE, alignment=TA_LEFT, leading=11)),
        ("THCenter", dict(fontName="Helvetica-Bold", fontSize=8,
            textColor=WHITE, alignment=TA_CENTER, leading=11)),
        ("TD", dict(fontName="Helvetica", fontSize=8,
            textColor=DARK_GRAY, alignment=TA_LEFT, leading=11)),
        ("TDCenter", dict(fontName="Helvetica", fontSize=8,
            textColor=DARK_GRAY, alignment=TA_CENTER, leading=11)),
        ("TDBold", dict(fontName="Helvetica-Bold", fontSize=8,
            textColor=NAVY, alignment=TA_LEFT, leading=11)),
        ("TDSmall", dict(fontName="Helvetica", fontSize=7.5,
            textColor=MID_GRAY, alignment=TA_LEFT, leading=11)),
        ("FootNote", dict(fontName="Helvetica-Oblique", fontSize=7.5,
            textColor=MID_GRAY, alignment=TA_CENTER, spaceAfter=2, spaceBefore=6)),
        ("ClauseRef", dict(fontName="Helvetica-Bold", fontSize=9,
            textColor=GOLD_DARK, alignment=TA_LEFT, spaceAfter=4, leading=14)),
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
    def __init__(self, title, dw, color=NAVY):
        super().__init__()
        self.title = title
        self.width = dw
        self.color = color
        self.height = 30
    def draw(self):
        self.canv.setFillColor(GOLD)
        self.canv.rect(0, 0, 4, self.height, fill=1, stroke=0)
        self.canv.setFillColor(LIGHT_GRAY)
        self.canv.rect(4, 0, self.width - 4, self.height, fill=1, stroke=0)
        self.canv.setStrokeColor(BORDER)
        self.canv.setLineWidth(0.4)
        self.canv.line(4, 0, self.width, 0)
        self.canv.setFillColor(self.color)
        self.canv.setFont("Helvetica-Bold", 11)
        self.canv.drawString(14, 9, self.title)


def status_pill(label, bg, fg=WHITE):
    return Table(
        [[Paragraph(label, ParagraphStyle("SP",
            fontName="Helvetica-Bold", fontSize=7.5,
            textColor=fg, alignment=TA_CENTER))]],
        colWidths=[70]
    ), TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), bg),
        ('ROUNDEDCORNERS', [4]),
        ('TOPPADDING', (0,0),(-1,-1), 3),
        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ('LEFTPADDING', (0,0),(-1,-1), 6),
        ('RIGHTPADDING', (0,0),(-1,-1), 6),
    ])


def make_pill_para(label, bg, fg=WHITE):
    """Return a Table that renders as a coloured pill."""
    t = Table(
        [[Paragraph(label, ParagraphStyle("Pill",
            fontName="Helvetica-Bold", fontSize=7,
            textColor=fg, alignment=TA_CENTER))]],
        colWidths=[68]
    )
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


# ── PIPELINE DATA ─────────────────────────────────────────────────────────────
PIPELINE = [
    {
        "id": "VX-001",
        "prospect": "Skilligen HDI",
        "sector": "Human Development / Enterprise AI",
        "location": "UAE / International",
        "contact": "Amanulla Khan — Co-founder",
        "track": "Track B",
        "stage": "NDA SENT",
        "stage_color": AMBER,
        "stage_bg": AMBER_LIGHT,
        "omnix_layer": "OMNIX-AGT",
        "velos_role": "Modular — Velos engages direct if client requires execution layer",
        "est_value": "$4,500 / mo (Velos direct)",
        "tier": "Standard",
        "next_action": "Awaiting NDA signature. No architecture co-creation until signed.",
        "notes": "HDI = human formation upstream of OMNIX. Discussed Formation→Admissibility→Execution architecture. IP protected. Potential referral pipeline for enterprise agents.",
    },
    {
        "id": "VX-002",
        "prospect": "TBD — Eureka GCC Cohort",
        "sector": "FinTech / Multi-sector",
        "location": "Dubai / GCC",
        "contact": "Via Eureka GCC 2026 network",
        "track": "Track A / Track B",
        "stage": "PIPELINE",
        "stage_color": SLATE,
        "stage_bg": LIGHT_GRAY,
        "omnix_layer": "OMNIX-TRD / OMNIX-CRD",
        "velos_role": "To be defined per prospect",
        "est_value": "TBD",
        "tier": "TBD",
        "next_action": "Velos to flag GCC contacts with execution layer requirements. OMNIX to flag governance mandates.",
        "notes": "Eureka GCC semifinal (Harold Nunes) activates network of GCC founders and investors. Joint stack pitch relevant to any autonomous decision system in region.",
    },
    {
        "id": "VX-003",
        "prospect": "TBD — Velos Existing Client",
        "sector": "Open",
        "location": "Open",
        "contact": "Naimat Khan — Velos",
        "track": "Track B",
        "stage": "PIPELINE",
        "stage_color": SLATE,
        "stage_bg": LIGHT_GRAY,
        "omnix_layer": "OMNIX-AGT / OMNIX-TRD",
        "velos_role": "Velos leads — $4,500/mo direct. OMNIX retained 100%.",
        "est_value": "$4,500 / mo (Velos direct)",
        "tier": "Standard",
        "next_action": "Naimat to identify existing Velos clients with governance gap. Written approval from OMNIX required before engagement (per Clause 4.3).",
        "notes": "Track B modular route — Velos bills client directly for execution layer. OMNIX governance module retains 100% of its fee. Clause 4.3 governs engagement process.",
    },
]


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
    story.append(Paragraph("JOINT STACK DEPLOYMENT PIPELINE", ParagraphStyle("Eye",
        fontName="Helvetica-Bold", fontSize=9, textColor=GOLD,
        alignment=TA_LEFT, spaceAfter=6, leading=13)))
    story.append(Paragraph("OMNIX x Velos", ParagraphStyle("CT",
        fontName="Helvetica-Bold", fontSize=38, textColor=GOLD,
        alignment=TA_LEFT, spaceAfter=6, leading=44)))
    story.append(Paragraph("Shared Pipeline Log", ParagraphStyle("CS",
        fontName="Helvetica-Bold", fontSize=20, textColor=WHITE,
        alignment=TA_LEFT, spaceAfter=8, leading=26)))
    story.append(Paragraph(
        "Active and prospective joint stack opportunities — maintained per Clause 4.4 "
        "of the Supplement to Agreement Clause 10.1",
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
            [Paragraph("Date Issued", s['CoverMeta']),
             Paragraph(TODAY, ParagraphStyle("MV",
                fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
            [Paragraph("OMNIX Party", s['CoverMeta']),
             Paragraph("Harold Nunes — OMNIX Quantum Ltd",
                ParagraphStyle("MV", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
            [Paragraph("Velos Party", s['CoverMeta']),
             Paragraph("Naimat Khan — Velos",
                ParagraphStyle("MV", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
            [Paragraph("Next Update Due", s['CoverMeta']),
             Paragraph("Within 5 business days of any material development (per §4.4)",
                ParagraphStyle("MV", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
        ],
        colWidths=[DW * 0.38, DW * 0.62]
    )
    meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#111827')),
        ('BOX', (0, 0), (-1, -1), 1, GOLD),
        ('LINEAFTER', (0, 0), (0, -1), 0.4, HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.3, HexColor('#1e293b')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta)
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "STRICTLY CONFIDENTIAL — For use by OMNIX Quantum Ltd and Velos only. "
        "Not for disclosure to any third party without written consent of both parties.",
        ParagraphStyle("Conf", fontName="Helvetica-Oblique", fontSize=7.5,
        textColor=HexColor('#475569'), alignment=TA_CENTER)))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 1 — CLAUSE 4.4 CONTEXT
    # ════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("Clause 4.4 — Pipeline Transparency", DW))
    story.append(Spacer(1, 10))

    # Clause text box
    clause_box = Table(
        [[Paragraph(
            "<i>\"Both Parties agree to maintain a shared pipeline log of active and prospective "
            "joint stack opportunities, updated within 5 business days of any material development.\"</i>",
            ParagraphStyle("QB", fontName="Helvetica-Oblique", fontSize=9.5,
                textColor=NAVY, alignment=TA_JUSTIFY, leading=15))]],
        colWidths=[DW]
    )
    clause_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GOLD_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1.5, GOLD),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING', (0, 0), (-1, -1), 18),
        ('RIGHTPADDING', (0, 0), (-1, -1), 18),
    ]))
    story.append(clause_box)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "This document is the first version of the shared pipeline log required under Clause 4.4. "
        "It covers all active and prospective opportunities for the OMNIX x Velos joint stack "
        "as of the date of this document. Both parties are responsible for notifying the other "
        "within 5 business days of any material development on any listed opportunity.",
        s['Body']))
    story.append(Spacer(1, 10))

    # Track summary
    track_data = [
        ["Track", "Commercial Structure", "Who Bills Client", "OMNIX Fee", "Velos Fee"],
        ["Track A — Unified", "Single contract, single invoice through OMNIX",
         "OMNIX", "70%", "30%"],
        ["Track B — Modular", "Velos bills client directly for execution layer",
         "Velos", "100% of own module", "$4,500/mo direct"],
    ]
    track_table = Table(
        [[Paragraph(h, s['TH']) for h in track_data[0]]] +
        [[Paragraph(str(c), s['TD']) for c in row] for row in track_data[1:]],
        colWidths=[DW*0.18, DW*0.32, DW*0.18, DW*0.16, DW*0.16]
    )
    track_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_GRAY),
        ('BACKGROUND', (0, 2), (-1, 2), WHITE),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('GRID', (0, 0), (-1, -1), 0.3, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(track_table)
    story.append(Spacer(1, 18))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 2 — PIPELINE SUMMARY
    # ════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("Pipeline Summary", DW))
    story.append(Spacer(1, 10))

    summary_data = [
        ["ID", "Prospect", "Sector", "Track", "Stage", "Est. Value / mo"],
    ]
    for p in PIPELINE:
        summary_data.append([
            p["id"], p["prospect"], p["sector"],
            p["track"], p["stage"], p["est_value"]
        ])

    sum_table = Table(
        [[Paragraph(h, s['TH']) for h in summary_data[0]]] +
        [[Paragraph(str(c), s['TD']) for c in row] for row in summary_data[1:]],
        colWidths=[DW*0.10, DW*0.24, DW*0.22, DW*0.14, DW*0.14, DW*0.16]
    )
    row_bgs = [WHITE, LIGHT_GRAY, WHITE, LIGHT_GRAY]
    sum_table.setStyle(TableStyle(
        [('BACKGROUND', (0, 0), (-1, 0), NAVY),
         ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
         ('GRID', (0, 0), (-1, -1), 0.3, BORDER),
         ('TOPPADDING', (0, 0), (-1, -1), 7),
         ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
         ('LEFTPADDING', (0, 0), (-1, -1), 7),
         ('RIGHTPADDING', (0, 0), (-1, -1), 7),
         ('VALIGN', (0, 0), (-1, -1), 'TOP')] +
        [('BACKGROUND', (0, i+1), (-1, i+1), row_bgs[i]) for i in range(len(PIPELINE))]
    ))
    story.append(sum_table)
    story.append(Spacer(1, 18))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 3 — DETAILED OPPORTUNITY CARDS
    # ════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("Detailed Opportunity Records", DW))
    story.append(Spacer(1, 12))

    for p in PIPELINE:
        # Card header
        header = Table(
            [[Paragraph(f"{p['id']}  —  {p['prospect']}", ParagraphStyle("CH",
                fontName="Helvetica-Bold", fontSize=11, textColor=WHITE)),
              Paragraph(p['stage'], ParagraphStyle("CS2",
                fontName="Helvetica-Bold", fontSize=9,
                textColor=p['stage_color'],
                alignment=TA_RIGHT))]],
            colWidths=[DW * 0.72, DW * 0.28]
        )
        header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), NAVY),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1.5, GOLD),
        ]))
        story.append(header)

        # Card body
        fields = [
            ["Sector", p['sector'], "Location", p['location']],
            ["Contact", p['contact'], "OMNIX Layer", p['omnix_layer']],
            ["Commercial Track", p['track'], "Velos Role", p['velos_role']],
            ["Pricing Tier", p['tier'], "Estimated Value", p['est_value']],
        ]
        body_rows = []
        for row in fields:
            body_rows.append([
                Paragraph(row[0], ParagraphStyle("FLabel", fontName="Helvetica-Bold",
                    fontSize=8, textColor=SLATE)),
                Paragraph(row[1], s['TD']),
                Paragraph(row[2], ParagraphStyle("FLabel2", fontName="Helvetica-Bold",
                    fontSize=8, textColor=SLATE)),
                Paragraph(row[3], s['TD']),
            ])

        card_body = Table(body_rows, colWidths=[DW*0.20, DW*0.30, DW*0.20, DW*0.30])
        card_body.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), WHITE),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, LIGHT_GRAY]),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
            ('GRID', (0, 0), (-1, -1), 0.3, BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(card_body)

        # Notes row
        notes_row = Table(
            [[Paragraph("Notes", ParagraphStyle("NL", fontName="Helvetica-Bold",
                fontSize=8, textColor=SLATE)),
              Paragraph(p['notes'], s['TD'])]],
            colWidths=[DW * 0.20, DW * 0.80]
        )
        notes_row.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), GOLD_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(notes_row)

        # Next action row
        action_row = Table(
            [[Paragraph("Next Action", ParagraphStyle("AL", fontName="Helvetica-Bold",
                fontSize=8, textColor=WHITE)),
              Paragraph(p['next_action'], ParagraphStyle("AV",
                fontName="Helvetica", fontSize=8, textColor=WHITE, leading=12))]],
            colWidths=[DW * 0.20, DW * 0.80]
        )
        action_row.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DARK_GRAY),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(action_row)
        story.append(Spacer(1, 16))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 4 — UPDATE PROTOCOL
    # ════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("Update Protocol — §4.4", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Material developments requiring log update within 5 business days include: "
        "first contact made with a prospect, NDA executed, discovery call completed, "
        "proposal submitted, client decision (positive or negative), track change, "
        "pricing negotiation initiated, contract signed.",
        s['Body']))
    story.append(Spacer(1, 8))

    protocol_data = [
        ["Responsibility", "Action", "Timeline"],
        ["Either Party", "New prospect identified for joint stack", "Notify other party + add to log within 5 days"],
        ["Either Party", "Material development on existing entry", "Update log entry within 5 days"],
        ["Velos", "Track B client engagement (per §4.3)", "Written OMNIX approval before engagement"],
        ["OMNIX", "Track A proposal to client", "Notify Velos before submission"],
        ["Either Party", "Client closes or withdraws", "Mark entry CLOSED with date and reason"],
    ]
    proto_table = Table(
        [[Paragraph(h, s['TH']) for h in protocol_data[0]]] +
        [[Paragraph(str(c), s['TD']) for c in row] for row in protocol_data[1:]],
        colWidths=[DW*0.22, DW*0.38, DW*0.40]
    )
    proto_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('GRID', (0, 0), (-1, -1), 0.3, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(proto_table)
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
