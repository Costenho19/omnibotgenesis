"""
OMNIX Quantum Ltd — Mutual NDA & IP Protection Agreement
OMNIX Quantum Ltd x Skilligen HDI
PDF Generator — Professional legal document, OMNIX dark style
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ── COLOURS ──────────────────────────────────────────────────────────────────
NAVY      = HexColor('#0a0f1a')
DARK_CARD = HexColor('#111827')
PAGE_BG   = HexColor('#0d1420')
DIVIDER   = HexColor('#1e2d45')
GOLD      = HexColor('#C9A227')
GOLD_LT   = HexColor('#F5D97A')
SILVER    = HexColor('#94a3b8')
OFF_WHITE = HexColor('#e2e8f0')

LOGO_PATH   = os.path.join(os.path.dirname(__file__), '..', 'assets', 'omnix_logo.png')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'OMNIX_Skilligen_NDA.pdf')

W, H = A4


# ── PAGE TEMPLATE ─────────────────────────────────────────────────────────────
def page_template(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFillColor(PAGE_BG)
    canvas_obj.rect(0, 0, W, H, fill=1, stroke=0)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.rect(0, 0, 4, H, fill=1, stroke=0)
    canvas_obj.setStrokeColor(GOLD)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(1.0 * inch, 0.55 * inch, W - 1.0 * inch, 0.55 * inch)
    canvas_obj.setFillColor(SILVER)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawString(1.0 * inch, 0.38 * inch,
                          "OMNIX Quantum Ltd x Skilligen HDI — Mutual NDA & IP Protection Agreement")
    canvas_obj.drawRightString(W - 1.0 * inch, 0.38 * inch,
                               f"Page {canvas_obj.getPageNumber()}")
    canvas_obj.drawCentredString(W / 2, 0.38 * inch, "Confidential")
    canvas_obj.restoreState()


# ── STYLES ────────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()
    defs = [
        ("CoverTitle", dict(fontName="Helvetica-Bold", fontSize=24,
            textColor=GOLD, alignment=TA_CENTER, spaceAfter=8, spaceBefore=0, leading=30)),
        ("CoverSub", dict(fontName="Helvetica", fontSize=12,
            textColor=OFF_WHITE, alignment=TA_CENTER, spaceAfter=4, spaceBefore=4, leading=17)),
        ("CoverMeta", dict(fontName="Helvetica-Oblique", fontSize=9.5,
            textColor=SILVER, alignment=TA_CENTER, spaceAfter=3, spaceBefore=3, leading=13)),
        ("CoverPartyTitle", dict(fontName="Helvetica-Bold", fontSize=12,
            textColor=GOLD, alignment=TA_CENTER, spaceAfter=2, spaceBefore=4)),
        ("CoverPartyDetail", dict(fontName="Helvetica", fontSize=9,
            textColor=SILVER, alignment=TA_CENTER, spaceAfter=2)),
        ("Confidential", dict(fontName="Helvetica-Oblique", fontSize=8,
            textColor=SILVER, alignment=TA_CENTER, spaceAfter=3, spaceBefore=3)),
        ("ClauseHead", dict(fontName="Helvetica-Bold", fontSize=9.5,
            textColor=GOLD_LT, alignment=TA_LEFT,
            spaceAfter=4, spaceBefore=8, leftIndent=0)),
        ("Body", dict(fontName="Helvetica", fontSize=9.5,
            textColor=OFF_WHITE, alignment=TA_JUSTIFY,
            spaceAfter=6, spaceBefore=0, leading=15, leftIndent=16)),
        ("Bullet", dict(fontName="Helvetica", fontSize=9.5,
            textColor=OFF_WHITE, alignment=TA_JUSTIFY,
            spaceAfter=4, spaceBefore=2, leading=14,
            leftIndent=28, firstLineIndent=-10)),
        ("SigLabel", dict(fontName="Helvetica-Bold", fontSize=9,
            textColor=GOLD, alignment=TA_CENTER, spaceAfter=2)),
        ("SigValue", dict(fontName="Helvetica", fontSize=9,
            textColor=OFF_WHITE, alignment=TA_CENTER, spaceAfter=2)),
        ("SigLine", dict(fontName="Helvetica", fontSize=9,
            textColor=SILVER, alignment=TA_CENTER, spaceAfter=4)),
        ("FootNote", dict(fontName="Helvetica-Oblique", fontSize=7.5,
            textColor=SILVER, alignment=TA_CENTER, spaceAfter=2, spaceBefore=4)),
    ]
    for name, kwargs in defs:
        style = ParagraphStyle(name, **kwargs)
        if name not in base.byName:
            base.add(style)
        else:
            base.byName[name] = style
    return base


# ── CUSTOM FLOWABLES ──────────────────────────────────────────────────────────
class SectionBanner(Flowable):
    def __init__(self, num, title, doc_width):
        super().__init__()
        self.num = num
        self.title = title
        self.width = doc_width
        self.height = 28

    def draw(self):
        self.canv.setFillColor(GOLD)
        self.canv.roundRect(0, 0, self.width, self.height, 3, fill=1, stroke=0)
        self.canv.setFillColor(NAVY)
        self.canv.setFont("Helvetica-Bold", 11)
        self.canv.drawString(10, 8, f"{self.num}.  {self.title.upper()}")


class GoldRule(Flowable):
    def __init__(self, doc_width, thickness=1):
        super().__init__()
        self.width = doc_width
        self.height = thickness + 2
        self.thickness = thickness

    def draw(self):
        self.canv.setFillColor(GOLD)
        self.canv.rect(0, 1, self.width, self.thickness, fill=1, stroke=0)


# ── BUILD PDF ─────────────────────────────────────────────────────────────────
def build_pdf():
    s = build_styles()
    DW = W - 2.0 * inch

    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.75 * inch,
    )

    story = []

    # ── COVER ─────────────────────────────────────────────────────────────────
    if os.path.exists(LOGO_PATH):
        from reportlab.platypus import Image
        logo = Image(LOGO_PATH, width=1.6 * inch, height=0.55 * inch)
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 18))

    story.append(GoldRule(DW, 2))
    story.append(Spacer(1, 20))
    story.append(Paragraph("MUTUAL NON-DISCLOSURE", s['CoverTitle']))
    story.append(Paragraph("AND IP PROTECTION AGREEMENT", s['CoverTitle']))
    story.append(Spacer(1, 6))
    story.append(Paragraph("OMNIX Quantum Ltd  ×  Skilligen HDI", s['CoverSub']))
    story.append(Spacer(1, 20))
    story.append(GoldRule(DW, 1))
    story.append(Spacer(1, 24))

    parties = Table(
        [
            [Paragraph("OMNIX QUANTUM LTD", s['CoverPartyTitle']),
             Paragraph("SKILLIGEN HDI", s['CoverPartyTitle'])],
            [Paragraph("Incorporated in England &amp; Wales", s['CoverPartyDetail']),
             Paragraph("Decision Architecture &amp; Governance", s['CoverPartyDetail'])],
            [Paragraph("Harold Nunes — Founder &amp; CEO", s['CoverPartyDetail']),
             Paragraph("Amanulla Khan — Founder", s['CoverPartyDetail'])],
            [Paragraph("(\"OMNIX\")", s['CoverPartyDetail']),
             Paragraph("(\"Skilligen\")", s['CoverPartyDetail'])],
        ],
        colWidths=[DW / 2, DW / 2],
    )
    parties.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK_CARD),
        ('LINEAFTER',  (0, 0), (0, -1), 1, GOLD),
        ('BOX',        (0, 0), (-1, -1), 1, GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
    ]))
    story.append(parties)
    story.append(Spacer(1, 24))

    story.append(Paragraph("Effective Date: [DATE TO BE INSERTED]", s['CoverMeta']))
    story.append(Spacer(1, 16))
    story.append(GoldRule(DW, 1))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "CONFIDENTIAL — FOR SIGNATURE ONLY — NOT FOR DISTRIBUTION",
        s['Confidential']))
    story.append(PageBreak())

    # ── SECTION 1 — PURPOSE ───────────────────────────────────────────────────
    story.append(SectionBanner("1", "Purpose", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "The Parties wish to explore a potential collaboration around decision governance architecture, "
        "combining their respective frameworks — OMNIX's admissibility engine and Skilligen's Human "
        "Decision Infrastructure. This Agreement establishes the terms under which confidential "
        "information and intellectual property may be exchanged during that exploration.",
        s['Body']))
    story.append(Spacer(1, 14))

    # ── SECTION 2 — CONFIDENTIAL INFORMATION ─────────────────────────────────
    story.append(SectionBanner("2", "Definition of Confidential Information", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Confidential Information means any technical, commercial, architectural, or strategic "
        "information disclosed by either Party to the other in the course of this collaboration, "
        "whether in writing, verbally, or in any other form, including but not limited to:",
        s['Body']))
    for item in [
        "Proprietary frameworks, methodologies, and system architectures",
        "Business strategies, pricing models, and client relationships",
        "Technical implementations, algorithms, and processes",
        "Any documents, diagrams, or materials shared between the Parties",
    ]:
        story.append(Paragraph(f"• {item}", s['Bullet']))
    story.append(Spacer(1, 14))

    # ── SECTION 3 — OBLIGATIONS ───────────────────────────────────────────────
    story.append(SectionBanner("3", "Obligations", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Each Party agrees to:", s['Body']))
    story.append(Spacer(1, 4))

    for num, body in [
        ("3.1", "Keep all Confidential Information strictly confidential and not disclose it to any "
                "third party without prior written consent from the disclosing Party."),
        ("3.2", "Use the Confidential Information solely for the purpose of evaluating and developing "
                "the potential collaboration described in Section 1."),
        ("3.3", "Protect the Confidential Information with the same degree of care it uses to protect "
                "its own confidential information, and no less than reasonable care."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>", s['ClauseHead']))
        story.append(Paragraph(body, s['Body']))

    story.append(Spacer(1, 14))

    # ── SECTION 4 — INTELLECTUAL PROPERTY ────────────────────────────────────
    story.append(SectionBanner("4", "Intellectual Property", DW))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>4.1</b>  Each Party retains full and exclusive ownership of its own "
                           "pre-existing intellectual property, including but not limited to:",
                           s['ClauseHead']))
    story.append(Paragraph(
        "<b>OMNIX</b> retains sole ownership of its admissibility engine, 11-checkpoint governance "
        "framework, post-quantum cryptographic receipt system (Dilithium-3), and all related IP.",
        s['Bullet']))
    story.append(Paragraph(
        "<b>Skilligen</b> retains sole ownership of its Human Decision Infrastructure framework, "
        "decision conditioning methodologies, and all related IP.",
        s['Bullet']))
    story.append(Spacer(1, 6))

    for num, body in [
        ("4.2", "No licence, transfer, or assignment of IP is granted by either Party to the other "
                "under this Agreement."),
        ("4.3", "Any jointly developed concepts, frameworks, or materials arising from this "
                "collaboration shall be subject to a separate written agreement defining ownership, "
                "rights, and commercialisation terms <b>before</b> any such joint development begins."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>", s['ClauseHead']))
        story.append(Paragraph(body, s['Body']))

    story.append(Spacer(1, 14))

    # ── SECTION 5 — EXCLUSIONS ────────────────────────────────────────────────
    story.append(SectionBanner("5", "Exclusions", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph("This Agreement does not apply to information that:", s['Body']))
    story.append(Spacer(1, 4))

    for num, body in [
        ("5.1", "Is or becomes publicly available through no fault of the receiving Party."),
        ("5.2", "Was already known to the receiving Party prior to disclosure."),
        ("5.3", "Is independently developed by the receiving Party without use of the "
                "Confidential Information."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>", s['ClauseHead']))
        story.append(Paragraph(body, s['Body']))

    story.append(Spacer(1, 14))

    # ── SECTION 6 — TERM ─────────────────────────────────────────────────────
    story.append(SectionBanner("6", "Term", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "This Agreement shall remain in force for a period of <b>two (2) years</b> from the Effective "
        "Date, unless terminated earlier by mutual written agreement with 30 days written notice.",
        s['Body']))
    story.append(Spacer(1, 14))

    # ── SECTION 7 — GOVERNING LAW ─────────────────────────────────────────────
    story.append(SectionBanner("7", "Governing Law", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "This Agreement is governed by the laws of England and Wales. Any disputes arising from "
        "this Agreement shall be subject to the exclusive jurisdiction of the courts of "
        "England and Wales.",
        s['Body']))

    story.append(Spacer(1, 24))
    story.append(GoldRule(DW, 1))
    story.append(Spacer(1, 20))

    # ── SIGNATURE BLOCK ───────────────────────────────────────────────────────
    story.append(Paragraph("EXECUTION — AUTHORISED SIGNATURES", s['CoverSub']))
    story.append(Spacer(1, 16))

    sig_data = [
        [Paragraph("OMNIX QUANTUM LTD", s['SigLabel']),
         Paragraph("SKILLIGEN HDI", s['SigLabel'])],
        [Paragraph("Harold Nunes", s['SigValue']),
         Paragraph("Amanulla Khan", s['SigValue'])],
        [Paragraph("Founder &amp; CEO", s['SigValue']),
         Paragraph("Founder", s['SigValue'])],
        [Paragraph("Date: ___________________________", s['SigLine']),
         Paragraph("Date: ___________________________", s['SigLine'])],
        [Paragraph("Signature: ______________________", s['SigLine']),
         Paragraph("Signature: ______________________", s['SigLine'])],
    ]
    sig_table = Table(sig_data, colWidths=[DW / 2, DW / 2])
    sig_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK_CARD),
        ('LINEAFTER',  (0, 0), (0, -1), 1, GOLD),
        ('BOX',        (0, 0), (-1, -1), 1, GOLD),
        ('GRID',       (0, 0), (-1, -1), 0.3, DIVIDER),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 14),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 14),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 20))
    story.append(GoldRule(DW, 1))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "This Agreement constitutes the entire understanding between the Parties with respect to "
        "confidentiality and IP protection for the purpose described herein. "
        "Any amendment must be made in writing and signed by both Parties.",
        s['FootNote']))
    story.append(Paragraph(
        "OMNIX Quantum Ltd — Registered in England &amp; Wales — omnixquantum.net",
        s['FootNote']))

    doc.build(story, onFirstPage=page_template, onLaterPages=page_template)
    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
