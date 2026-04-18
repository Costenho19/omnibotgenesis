"""
OMNIX Quantum Ltd — Supplement to Clause 10.1
Joint Bundled Commercial Agreement: OMNIX + Velos
PDF Generator — Professional legal document style
"""

import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT

# ── COLOUR PALETTE ──────────────────────────────────────────────────────────
NAVY        = HexColor('#0a0f1a')
DARK_CARD   = HexColor('#111827')
GOLD        = HexColor('#C9A227')
GOLD_LIGHT  = HexColor('#F5D97A')
SILVER      = HexColor('#94a3b8')
OFF_WHITE   = HexColor('#e2e8f0')
PAGE_BG     = HexColor('#0d1420')
DIVIDER     = HexColor('#1e2d45')

LOGO_PATH   = os.path.join(os.path.dirname(__file__), '..', 'assets', 'omnix_logo.png')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'OMNIX_Velos_Supplement_Clause10_1.pdf')

W, H = A4  # 595 x 842 pt


# ── PAGE BACKGROUND + FOOTER ────────────────────────────────────────────────
def page_template(canvas_obj, doc):
    canvas_obj.saveState()

    # Dark background
    canvas_obj.setFillColor(PAGE_BG)
    canvas_obj.rect(0, 0, W, H, fill=1, stroke=0)

    # Gold left accent bar
    canvas_obj.setFillColor(GOLD)
    canvas_obj.rect(0, 0, 4, H, fill=1, stroke=0)

    # Footer divider line
    canvas_obj.setStrokeColor(GOLD)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(1.0 * inch, 0.55 * inch, W - 1.0 * inch, 0.55 * inch)

    # Footer text
    canvas_obj.setFillColor(SILVER)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawString(1.0 * inch, 0.38 * inch,
                          "OMNIX Quantum Ltd — Confidential Commercial Agreement")
    canvas_obj.drawRightString(W - 1.0 * inch, 0.38 * inch,
                               f"Page {canvas_obj.getPageNumber()}")
    canvas_obj.drawCentredString(W / 2, 0.38 * inch, "omnixquantum.net")

    canvas_obj.restoreState()


# ── STYLES ───────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    defs = [
        # Cover
        ("CoverTitle", dict(fontName="Helvetica-Bold", fontSize=28,
            textColor=GOLD, alignment=TA_CENTER, spaceAfter=8, spaceBefore=0, leading=34)),
        ("CoverSub", dict(fontName="Helvetica", fontSize=13,
            textColor=OFF_WHITE, alignment=TA_CENTER, spaceAfter=4, spaceBefore=4, leading=18)),
        ("CoverMeta", dict(fontName="Helvetica-Oblique", fontSize=9.5,
            textColor=SILVER, alignment=TA_CENTER, spaceAfter=3, spaceBefore=3, leading=13)),
        ("CoverPartyTitle", dict(fontName="Helvetica-Bold", fontSize=12,
            textColor=GOLD, alignment=TA_CENTER, spaceAfter=2, spaceBefore=4)),
        ("CoverPartyDetail", dict(fontName="Helvetica", fontSize=9,
            textColor=SILVER, alignment=TA_CENTER, spaceAfter=2, spaceBefore=0)),
        ("Confidential", dict(fontName="Helvetica-Oblique", fontSize=8,
            textColor=SILVER, alignment=TA_CENTER, spaceAfter=3, spaceBefore=3)),

        # Section header label (used inside SectionBanner)
        ("SecLabel", dict(fontName="Helvetica-Bold", fontSize=11,
            textColor=NAVY, alignment=TA_LEFT, spaceAfter=0, spaceBefore=0)),

        # Clause number + inline title
        ("ClauseHead", dict(fontName="Helvetica-Bold", fontSize=9.5,
            textColor=GOLD_LIGHT, alignment=TA_LEFT,
            spaceAfter=4, spaceBefore=10, leftIndent=0)),

        # Body text
        ("Body", dict(fontName="Helvetica", fontSize=9.5,
            textColor=OFF_WHITE, alignment=TA_JUSTIFY,
            spaceAfter=6, spaceBefore=0, leading=15, leftIndent=16)),

        # Bullet / sub-item
        ("Bullet", dict(fontName="Helvetica", fontSize=9.5,
            textColor=OFF_WHITE, alignment=TA_JUSTIFY,
            spaceAfter=4, spaceBefore=2, leading=14,
            leftIndent=28, firstLineIndent=-10)),

        # Bullet label (bold part)
        ("BulletLabel", dict(fontName="Helvetica-Bold", fontSize=9.5,
            textColor=GOLD_LIGHT, alignment=TA_LEFT,
            spaceAfter=2, spaceBefore=2, leftIndent=28)),

        # Track title (Track A / Track B)
        ("TrackHead", dict(fontName="Helvetica-Bold", fontSize=10,
            textColor=GOLD, alignment=TA_LEFT,
            spaceAfter=4, spaceBefore=10, leftIndent=0)),

        # Table cells
        ("TH", dict(fontName="Helvetica-Bold", fontSize=8.5,
            textColor=GOLD, alignment=TA_CENTER, leading=11)),
        ("TD", dict(fontName="Helvetica", fontSize=8.5,
            textColor=OFF_WHITE, alignment=TA_CENTER, leading=11)),

        # Signature block
        ("SigLabel", dict(fontName="Helvetica-Bold", fontSize=9,
            textColor=GOLD, alignment=TA_CENTER, spaceAfter=2)),
        ("SigValue", dict(fontName="Helvetica", fontSize=9,
            textColor=OFF_WHITE, alignment=TA_CENTER, spaceAfter=2)),
        ("SigLine", dict(fontName="Helvetica", fontSize=9,
            textColor=SILVER, alignment=TA_CENTER, spaceAfter=4)),

        # Footer note
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


# ── CUSTOM FLOWABLES ─────────────────────────────────────────────────────────
class SectionBanner(Flowable):
    """Gold banner with section number and title — no text overlap."""
    def __init__(self, num, title, doc_width):
        super().__init__()
        self.num = num
        self.title = title
        self.width = doc_width
        self.height = 28  # pt

    def draw(self):
        # Gold fill
        self.canv.setFillColor(GOLD)
        self.canv.roundRect(0, 0, self.width, self.height, 3, fill=1, stroke=0)
        # Dark text
        self.canv.setFillColor(NAVY)
        self.canv.setFont("Helvetica-Bold", 11)
        self.canv.drawString(10, 8, f"{self.num}.  {self.title.upper()}")


class GoldRule(Flowable):
    """Thin gold horizontal rule."""
    def __init__(self, doc_width, thickness=1):
        super().__init__()
        self.width = doc_width
        self.height = thickness + 2
        self.thickness = thickness

    def draw(self):
        self.canv.setFillColor(GOLD)
        self.canv.rect(0, 1, self.width, self.thickness, fill=1, stroke=0)


class DividerRule(Flowable):
    """Subtle dark divider between clauses."""
    def __init__(self, doc_width):
        super().__init__()
        self.width = doc_width
        self.height = 1

    def draw(self):
        self.canv.setStrokeColor(DIVIDER)
        self.canv.setLineWidth(0.5)
        self.canv.line(0, 0, self.width, 0)


# ── HELPER: CLAUSE BLOCK ─────────────────────────────────────────────────────
def clause(num_str, title, body_text, s, bold_title=False):
    """Returns a KeepTogether block with clause number + body."""
    items = []
    if bold_title:
        items.append(Paragraph(f"<b>{num_str}</b>  <b>{title}</b>", s['ClauseHead']))
    else:
        items.append(Paragraph(f"<b>{num_str}</b>  {title}", s['ClauseHead']))
    items.append(Paragraph(body_text, s['Body']))
    return KeepTogether(items)


# ── PDF BUILD ─────────────────────────────────────────────────────────────────
def build_pdf():
    s = build_styles()
    DW = W - 2.0 * inch  # drawable width

    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.75 * inch,
    )

    story = []

    # ── COVER ────────────────────────────────────────────────────────────────
    # Logo
    if os.path.exists(LOGO_PATH):
        from reportlab.platypus import Image
        logo = Image(LOGO_PATH, width=1.6 * inch, height=0.55 * inch)
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 18))

    story.append(GoldRule(DW, 2))
    story.append(Spacer(1, 20))
    story.append(Paragraph("SUPPLEMENT TO CLAUSE 10.1", s['CoverTitle']))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Joint Bundled Commercial Agreement", s['CoverSub']))
    story.append(Spacer(1, 20))
    story.append(GoldRule(DW, 1))
    story.append(Spacer(1, 24))

    # Parties table
    parties = Table(
        [
            [Paragraph("OMNIX QUANTUM LTD", s['CoverPartyTitle']),
             Paragraph("VELOS", s['CoverPartyTitle'])],
            [Paragraph("Incorporated in England &amp; Wales", s['CoverPartyDetail']),
             Paragraph("Technology Execution Partner", s['CoverPartyDetail'])],
            [Paragraph("(\"OMNIX\")", s['CoverPartyDetail']),
             Paragraph("(\"Velos\")", s['CoverPartyDetail'])],
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
    story.append(Paragraph(
        "Pursuant to Master Partnership Agreement v2.0 — dated 03 April 2026",
        s['CoverMeta']))
    story.append(Spacer(1, 16))
    story.append(GoldRule(DW, 1))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "CONFIDENTIAL — FOR EXECUTION ONLY — NOT FOR DISTRIBUTION",
        s['Confidential']))
    story.append(PageBreak())

    # ── SECTION 1 — PURPOSE ──────────────────────────────────────────────────
    story.append(SectionBanner("1", "Purpose", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "This Supplement governs the commercial terms applicable exclusively to Joint Bundled Sales — "
        "defined as transactions in which OMNIX and Velos present a combined technology stack to a single "
        "enterprise client, comprising the OMNIX Admissibility Governance Layer and the Velos T=0 "
        "Execution Enforcement Layer.", s['Body']))
    story.append(Paragraph(
        "This Supplement does not modify, replace, or override any other term of the Agreement, "
        "including independent referral commissions governed by Clause 5.", s['Body']))
    story.append(Spacer(1, 16))

    # ── SECTION 2 — ARCHITECTURE ─────────────────────────────────────────────
    story.append(SectionBanner("2", "Joint Stack Architecture", DW))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>2.1</b>  The joint stack consists of two distinct and complementary layers:",
        s['ClauseHead']))
    story.append(Paragraph(
        "<b>OMNIX Governance Layer:</b>  11-checkpoint admissibility engine with post-quantum "
        "cryptographic receipts (Dilithium-3), governing decision validity prior to execution.",
        s['Bullet']))
    story.append(Paragraph(
        "<b>Velos Execution Layer:</b>  T=0 physical enforcement boundary providing real-time "
        "execution halt or authorisation based on OMNIX admissibility output.",
        s['Bullet']))
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>2.2</b>  Both layers shall be disclosed to the client as distinct components of the joint "
        "stack. Velos shall not be white-labeled or obscured. Velos cryptographic execution receipts "
        "shall be explicitly visible in client-facing logs and audit trails.", s['ClauseHead']))
    story.append(Paragraph("", s['Body']))

    story.append(Paragraph(
        "<b>2.3</b>  OMNIX retains full ownership of its Governance Layer IP. Velos retains full "
        "ownership of its Execution Layer IP. No joint ownership arises from this Supplement.",
        s['ClauseHead']))
    story.append(Paragraph("", s['Body']))

    story.append(Paragraph(
        "<b>2.4  Pre-Execution Governance Authority:</b>  OMNIX operates as a pre-execution "
        "governance layer. Where integrated, Velos shall enforce OMNIX veto decisions and shall not "
        "execute any action that has been blocked or rejected by OMNIX. The OMNIX admissibility output "
        "is binding on the Velos execution boundary for all joint stack deployments.", s['ClauseHead']))
    story.append(Spacer(1, 16))

    # ── SECTION 3 — COMMERCIAL TRACKS ────────────────────────────────────────
    story.append(SectionBanner("3", "Commercial Tracks", DW))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Track A — Unified Route", s['TrackHead']))
    for num, body in [
        ("3.1", "When the client procures the joint stack through a single contract and single invoice, "
                "OMNIX acts as the prime contracting party. OMNIX issues all invoicing and maintains the "
                "primary client relationship and account ownership."),
        ("3.2", "Revenue is distributed on a <b>70/30 basis</b>: 70% to OMNIX, 30% to Velos, calculated "
                "on the total contract value invoiced to the client."),
        ("3.3", "OMNIX retains full discretion to set the final contract price to the client. The 30% "
                "Velos share is calculated on the total invoiced amount regardless of the pricing tier "
                "selected by OMNIX."),
        ("3.4", "The 70/30 split is an internal arrangement between the Parties and shall not be "
                "disclosed to the client."),
        ("3.5", "OMNIX shall transfer Velos's share within <b>15 business days</b> of receipt of "
                "client payment."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>", s['ClauseHead']))
        story.append(Paragraph(body, s['Body']))

    # Revenue split table
    story.append(Spacer(1, 8))
    th = s['TH']
    td = s['TD']
    tdata = [
        [Paragraph("Pricing Tier", th),
         Paragraph("Total Bundle", th),
         Paragraph("OMNIX (70%)", th),
         Paragraph("Velos (30%)", th)],
        [Paragraph("Institutional Node", td),
         Paragraph("$25,000 / month", td),
         Paragraph("$17,500 / month", td),
         Paragraph("$7,500 / month", td)],
        [Paragraph("Enterprise Cluster", td),
         Paragraph("$55,000 / month", td),
         Paragraph("$38,500 / month", td),
         Paragraph("$16,500 / month", td)],
        [Paragraph("Sovereign Stack", td),
         Paragraph("$95,000 / month", td),
         Paragraph("$66,500 / month", td),
         Paragraph("$28,500 / month", td)],
    ]
    tcw = [DW * 0.30, DW * 0.23, DW * 0.23, DW * 0.24]
    ttable = Table(tdata, colWidths=tcw)
    ttable.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a2d45')),
        ('BACKGROUND', (0, 1), (-1, 1), DARK_CARD),
        ('BACKGROUND', (0, 2), (-1, 2), HexColor('#141f30')),
        ('BACKGROUND', (0, 3), (-1, 3), DARK_CARD),
        ('BOX',   (0, 0), (-1, -1), 1, GOLD),
        ('GRID',  (0, 0), (-1, -1), 0.4, DIVIDER),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
    ]))
    story.append(ttable)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Track B — Modular Route", s['TrackHead']))
    for num, body in [
        ("3.6", "When the client procures governance and execution layers under separate contracts, Velos "
                "contracts directly with the client for the execution layer at a flat infrastructure fee "
                "of <b>$4,500 USD per month per enterprise node</b>."),
        ("3.7", "OMNIX contracts directly with the client for the governance layer at its applicable "
                "pricing tier. No revenue sharing between the Parties applies under this track."),
        ("3.8", "Under Track B, OMNIX retains 100% of its contract value and Velos retains 100% of its "
                "$4,500 monthly fee."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>", s['ClauseHead']))
        story.append(Paragraph(body, s['Body']))

    story.append(Spacer(1, 16))
    story.append(PageBreak())

    # ── SECTION 4 — OPERATIONAL GOVERNANCE ───────────────────────────────────
    story.append(SectionBanner("4", "Operational Governance", DW))
    story.append(Spacer(1, 10))

    for num, head, body in [
        ("4.1", "Route Selection",
         "The applicable commercial track is determined jointly by both Parties based on the client's "
         "procurement preference. Neither Party may unilaterally designate a track without the other "
         "Party's written confirmation."),
        ("4.2", "Mutual Authorisation",
         "No joint stack deployment may proceed under either track without prior written confirmation "
         "from both Parties. The OMNIX Governance Layer may not be activated in a Velos environment, "
         "and the Velos Execution Layer may not be deployed against OMNIX infrastructure, without "
         "mutual sign-off."),
        ("4.3", "Modular Route Client Engagement",
         "Velos shall notify and obtain written approval from OMNIX prior to engaging any client under "
         "the Modular Route involving the joint stack. No direct client contract under Track B may be "
         "executed without OMNIX written approval."),
        ("4.4", "Pipeline Transparency",
         "Both Parties agree to maintain a shared pipeline log of active and prospective joint stack "
         "opportunities, updated within 5 business days of any material development."),
        ("4.5", "Architectural Transparency",
         "In all Unified Route (Track A) deployments, OMNIX agrees that the Velos Execution Layer shall "
         "remain architecturally transparent, and Velos shall be explicitly identified to the end-client "
         "as the terminal enforcement provider. This transparency is a required condition for the "
         "client's cyber-insurance underwriting and audit trail validity."),
    ]:
        story.append(Paragraph(f"<b>{num}  {head}:</b>", s['ClauseHead']))
        story.append(Paragraph(body, s['Body']))

    story.append(Spacer(1, 16))

    # ── SECTION 5 — LIABILITY ─────────────────────────────────────────────────
    story.append(SectionBanner("5", "Liability", DW))
    story.append(Spacer(1, 10))

    for num, body in [
        ("5.1", "Each Party shall be solely responsible for its own systems, outputs, and performance "
                "under this Supplement. OMNIX assumes no liability for the performance or failure of the "
                "Velos Execution Layer. Velos assumes no liability for the performance or failure of the "
                "OMNIX Governance Layer."),
        ("5.2", "No joint liability is created under this Supplement. Each Party's liability to the "
                "client for its respective layer is governed solely by its own direct contractual "
                "arrangements with that client."),
        ("5.3", "In the Unified Route, OMNIX as prime contractor bears contractual liability to the "
                "client for the total bundled offering. OMNIX shall include appropriate back-to-back "
                "liability provisions in its agreement with Velos for the execution layer component."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>", s['ClauseHead']))
        story.append(Paragraph(body, s['Body']))

    story.append(Spacer(1, 16))

    # ── SECTION 6 — BRAND AND MARKETING ──────────────────────────────────────
    story.append(SectionBanner("6", "Brand and Marketing", DW))
    story.append(Spacer(1, 10))

    for num, body in [
        ("6.1", "Neither Party may use the name, brand, logo, trademarks, or technology references of "
                "the other Party in any public, client-facing, or marketing material without prior "
                "written consent from the other Party."),
        ("6.2", "Any co-branded materials, joint press releases, or public references to the partnership "
                "must be approved in writing by both Parties prior to publication or distribution."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>", s['ClauseHead']))
        story.append(Paragraph(body, s['Body']))

    story.append(Spacer(1, 16))

    # ── SECTION 7 — NON-EXCLUSIVITY ───────────────────────────────────────────
    story.append(SectionBanner("7", "Non-Exclusivity", DW))
    story.append(Spacer(1, 10))

    for num, body in [
        ("7.1", "This Supplement is non-exclusive. Both Parties remain free to engage with other "
                "partners, clients, or technology integrations independently, provided that such "
                "engagements do not breach the confidentiality obligations of the Agreement."),
        ("7.2", "Neither Party acquires any right of first refusal, exclusivity, or preferential "
                "treatment in any market or territory as a result of this Supplement."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>", s['ClauseHead']))
        story.append(Paragraph(body, s['Body']))

    story.append(Spacer(1, 16))

    # ── SECTION 8 — TERM AND TERMINATION ─────────────────────────────────────
    story.append(SectionBanner("8", "Term and Termination", DW))
    story.append(Spacer(1, 10))

    for num, body in [
        ("8.1", "This Supplement shall remain in force for the duration of the Agreement unless "
                "terminated earlier by mutual written agreement of both Parties with 60 days "
                "written notice."),
        ("8.2", "Termination of this Supplement does not affect the validity or enforceability of "
                "the Agreement or any independent arrangements thereunder."),
    ]:
        story.append(Paragraph(f"<b>{num}</b>", s['ClauseHead']))
        story.append(Paragraph(body, s['Body']))

    story.append(Spacer(1, 16))

    # ── SECTION 9 — GOVERNING LAW ────────────────────────────────────────────
    story.append(SectionBanner("9", "Governing Law", DW))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "This Supplement is governed by the laws of England and Wales. Any disputes arising from "
        "this Supplement shall be subject to the exclusive jurisdiction of the courts of "
        "England and Wales.", s['Body']))

    story.append(Spacer(1, 24))
    story.append(GoldRule(DW, 1))
    story.append(Spacer(1, 20))

    # ── SIGNATURE BLOCK ───────────────────────────────────────────────────────
    story.append(Paragraph("EXECUTION — AUTHORISED SIGNATURES", s['CoverSub']))
    story.append(Spacer(1, 16))

    sig_data = [
        [Paragraph("OMNIX QUANTUM LTD", s['SigLabel']),
         Paragraph("VELOS", s['SigLabel'])],
        [Paragraph("Harold Nunes", s['SigValue']),
         Paragraph("Naimat Khan", s['SigValue'])],
        [Paragraph("Founder &amp; CEO", s['SigValue']),
         Paragraph("________________", s['SigValue'])],
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
        "This Supplement forms an integral part of the Master Partnership Agreement v2.0 "
        "dated 03 April 2026 between OMNIX Quantum Ltd and Velos. "
        "All terms not expressly modified herein remain in full force and effect.",
        s['FootNote']))
    story.append(Paragraph(
        "OMNIX Quantum Ltd — Registered in England &amp; Wales — omnixquantum.net",
        s['FootNote']))

    doc.build(story, onFirstPage=page_template, onLaterPages=page_template)
    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
