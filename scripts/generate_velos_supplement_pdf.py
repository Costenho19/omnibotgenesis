"""
OMNIX Quantum Ltd — Supplement to Clause 10.1
Joint Bundled Commercial Agreement: OMNIX + Velos
PDF Generator — Eureka dark style with OMNIX branding
"""

import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import Flowable

DARK_BG    = HexColor('#0a0f1a')
DARK_MID   = HexColor('#0f172a')
CARD_BG    = HexColor('#1e293b')
GOLD       = HexColor('#C9A227')
GOLD_LIGHT = HexColor('#F5D97A')
LIGHT_GRAY = HexColor('#94a3b8')
WHITE      = HexColor('#ffffff')
RED_ALERT  = HexColor('#ef4444')
GREEN_OK   = HexColor('#10b981')

LOGO_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'omnix_logo.png')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'OMNIX_Velos_Supplement_Clause10_1.pdf')


class GoldLine(Flowable):
    def __init__(self, width=None):
        Flowable.__init__(self)
        self.width = width or 7 * inch
        self.height = 2

    def draw(self):
        self.canv.setFillColor(GOLD)
        self.canv.rect(0, 0, self.width, 2, fill=1, stroke=0)


class SectionHeader(Flowable):
    def __init__(self, number, title, width=None):
        Flowable.__init__(self)
        self.number = number
        self.title = title
        self.width = width or 7 * inch
        self.height = 0.45 * inch

    def draw(self):
        self.canv.setFillColor(GOLD)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        self.canv.setFillColor(DARK_BG)
        self.canv.setFont("Helvetica-Bold", 11)
        self.canv.drawString(0.15 * inch, 0.14 * inch,
                             f"{self.number}. {self.title.upper()}")


def dark_page(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFillColor(DARK_BG)
    canvas_obj.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawString(0.75 * inch, 0.35 * inch,
                          "OMNIX Quantum Ltd — Confidential Commercial Agreement")
    canvas_obj.drawRightString(letter[0] - 0.75 * inch, 0.35 * inch,
                               "omnixquantum.net")
    page_num = canvas_obj.getPageNumber()
    canvas_obj.drawCentredString(letter[0] / 2, 0.35 * inch,
                                 f"Page {page_num}")
    canvas_obj.restoreState()


_styles = None

def get_styles():
    global _styles
    if _styles:
        return _styles
    base = getSampleStyleSheet()
    defs = {
        'DocTitle': ParagraphStyle(
            'DocTitle', fontName='Helvetica-Bold', fontSize=26,
            textColor=GOLD, spaceAfter=6, spaceBefore=30, alignment=TA_CENTER
        ),
        'DocSubtitle': ParagraphStyle(
            'DocSubtitle', fontName='Helvetica', fontSize=12,
            textColor=LIGHT_GRAY, spaceAfter=4, spaceBefore=4, alignment=TA_CENTER
        ),
        'DocDate': ParagraphStyle(
            'DocDate', fontName='Helvetica-Oblique', fontSize=10,
            textColor=GOLD_LIGHT, spaceAfter=10, spaceBefore=4, alignment=TA_CENTER
        ),
        'PartyName': ParagraphStyle(
            'PartyName', fontName='Helvetica-Bold', fontSize=11,
            textColor=WHITE, spaceAfter=2, spaceBefore=6, alignment=TA_CENTER
        ),
        'PartyDetail': ParagraphStyle(
            'PartyDetail', fontName='Helvetica', fontSize=9,
            textColor=LIGHT_GRAY, spaceAfter=2, alignment=TA_CENTER
        ),
        'ClauseNum': ParagraphStyle(
            'ClauseNum', fontName='Helvetica-Bold', fontSize=10,
            textColor=GOLD, spaceAfter=3, spaceBefore=8, alignment=TA_LEFT
        ),
        'ClauseBody': ParagraphStyle(
            'ClauseBody', fontName='Helvetica', fontSize=9.5,
            textColor=LIGHT_GRAY, spaceAfter=5, spaceBefore=2,
            alignment=TA_JUSTIFY, leading=14, leftIndent=12
        ),
        'BulletItem': ParagraphStyle(
            'BulletItem', fontName='Helvetica', fontSize=9.5,
            textColor=LIGHT_GRAY, spaceAfter=3, spaceBefore=2,
            alignment=TA_LEFT, leading=13, leftIndent=24, bulletIndent=12
        ),
        'LayerLabel': ParagraphStyle(
            'LayerLabel', fontName='Helvetica-Bold', fontSize=9.5,
            textColor=GOLD_LIGHT, spaceAfter=2, spaceBefore=2,
            alignment=TA_LEFT, leftIndent=24
        ),
        'TrackTitle': ParagraphStyle(
            'TrackTitle', fontName='Helvetica-Bold', fontSize=10,
            textColor=WHITE, spaceAfter=4, spaceBefore=8, alignment=TA_LEFT,
            leftIndent=12
        ),
        'HighlightBox': ParagraphStyle(
            'HighlightBox', fontName='Helvetica-Bold', fontSize=10,
            textColor=GOLD, spaceAfter=6, spaceBefore=6, alignment=TA_CENTER
        ),
        'SignLabel': ParagraphStyle(
            'SignLabel', fontName='Helvetica-Bold', fontSize=9,
            textColor=GOLD, spaceAfter=2, alignment=TA_CENTER
        ),
        'SignValue': ParagraphStyle(
            'SignValue', fontName='Helvetica', fontSize=9,
            textColor=WHITE, spaceAfter=2, alignment=TA_CENTER
        ),
        'ConfidentialNote': ParagraphStyle(
            'ConfidentialNote', fontName='Helvetica-Oblique', fontSize=8,
            textColor=LIGHT_GRAY, spaceAfter=4, alignment=TA_CENTER
        ),
    }
    for name, style in defs.items():
        if name not in base.byName:
            base.add(style)
        else:
            base.byName[name] = style
    _styles = base
    return _styles


def sig_table():
    s = get_styles()
    data = [
        [Paragraph("OMNIX QUANTUM LTD", s['SignLabel']),
         Paragraph("VELOS", s['SignLabel'])],
        [Paragraph("Harold Nunes", s['SignValue']),
         Paragraph("Naimat Khan", s['SignValue'])],
        [Paragraph("Founder & CEO", s['SignValue']),
         Paragraph("________________", s['SignValue'])],
        [Paragraph("Date: _______________", s['SignValue']),
         Paragraph("Date: _______________", s['SignValue'])],
        [Paragraph("Signature: _______________", s['SignValue']),
         Paragraph("Signature: _______________", s['SignValue'])],
    ]
    t = Table(data, colWidths=[3.25 * inch, 3.25 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#1a2332')),
        ('BACKGROUND', (1, 0), (1, -1), HexColor('#1a2332')),
        ('LINEAFTER', (0, 0), (0, -1), 1, GOLD),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, GOLD),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#2d3748')),
    ]))
    return t


def build_pdf():
    s = get_styles()
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.65 * inch
    )

    story = []

    # ── COVER PAGE ──────────────────────────────────────────────────────────
    logo_exists = os.path.exists(LOGO_PATH)
    if logo_exists:
        from reportlab.platypus import Image
        story.append(Spacer(1, 0.3 * inch))
        logo = Image(LOGO_PATH, width=1.8 * inch, height=0.6 * inch)
        logo.hAlign = 'CENTER'
        story.append(logo)
        story.append(Spacer(1, 0.2 * inch))

    story.append(GoldLine())
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("SUPPLEMENT TO CLAUSE 10.1", s['DocTitle']))
    story.append(Paragraph("Joint Bundled Commercial Agreement", s['DocSubtitle']))
    story.append(Spacer(1, 0.1 * inch))
    story.append(GoldLine())
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("PARTIES TO THIS SUPPLEMENT", s['HighlightBox']))
    story.append(Spacer(1, 0.15 * inch))

    parties = Table(
        [[Paragraph("OMNIX QUANTUM LTD", s['PartyName']),
          Paragraph("VELOS", s['PartyName'])],
         [Paragraph("Incorporated in England & Wales", s['PartyDetail']),
          Paragraph("Technology Execution Partner", s['PartyDetail'])],
         [Paragraph('"OMNIX"', s['PartyDetail']),
          Paragraph('"Velos"', s['PartyDetail'])]],
        colWidths=[3.25 * inch, 3.25 * inch]
    )
    parties.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, GOLD),
        ('LINEAFTER', (0, 0), (0, -1), 1, GOLD),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(parties)
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph(
        f"Effective Date: [DATE TO BE INSERTED]", s['DocDate']
    ))
    story.append(Paragraph(
        "Pursuant to Master Partnership Agreement v2.0 — dated 03 April 2026",
        s['DocDate']
    ))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        "CONFIDENTIAL — FOR EXECUTION ONLY — NOT FOR DISTRIBUTION",
        s['ConfidentialNote']
    ))
    story.append(GoldLine())
    story.append(PageBreak())

    # ── SECTION 1 — PURPOSE ────────────────────────────────────────────────
    story.append(SectionHeader("1", "Purpose"))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "This Supplement governs the commercial terms applicable exclusively to Joint Bundled Sales — defined as "
        "transactions in which OMNIX and Velos present a combined technology stack to a single enterprise client, "
        "comprising the OMNIX Admissibility Governance Layer and the Velos T=0 Execution Enforcement Layer.",
        s['ClauseBody']
    ))
    story.append(Paragraph(
        "This Supplement does not modify, replace, or override any other term of the Agreement, including "
        "independent referral commissions governed by Clause 5.",
        s['ClauseBody']
    ))
    story.append(Spacer(1, 0.2 * inch))

    # ── SECTION 2 — ARCHITECTURE ───────────────────────────────────────────
    story.append(SectionHeader("2", "Joint Stack Architecture"))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("2.1  The joint stack consists of two distinct and complementary layers:", s['ClauseNum']))
    story.append(Paragraph(
        "<b>OMNIX Governance Layer:</b> 11-checkpoint admissibility engine with post-quantum cryptographic "
        "receipts (Dilithium-3), governing decision validity prior to execution.",
        s['BulletItem']
    ))
    story.append(Paragraph(
        "<b>Velos Execution Layer:</b> T=0 physical enforcement boundary providing real-time execution halt "
        "or authorisation based on OMNIX admissibility output.",
        s['BulletItem']
    ))
    story.append(Paragraph(
        "2.2  Both layers shall be disclosed to the client as distinct components of the joint stack. "
        "Velos shall not be white-labeled or obscured. Velos cryptographic execution receipts shall be "
        "explicitly visible in client-facing logs and audit trails.",
        s['ClauseBody']
    ))
    story.append(Paragraph(
        "2.3  OMNIX retains full ownership of its Governance Layer IP. Velos retains full ownership of "
        "its Execution Layer IP. No joint ownership arises from this Supplement.",
        s['ClauseBody']
    ))
    story.append(Paragraph("2.4  Pre-Execution Governance Authority:", s['ClauseNum']))
    story.append(Paragraph(
        "OMNIX operates as a pre-execution governance layer. Where integrated, Velos shall enforce OMNIX "
        "veto decisions and shall not execute any action that has been blocked or rejected by OMNIX. "
        "The OMNIX admissibility output is binding on the Velos execution boundary for all joint stack deployments.",
        s['ClauseBody']
    ))
    story.append(Spacer(1, 0.2 * inch))

    # ── SECTION 3 — COMMERCIAL TRACKS ─────────────────────────────────────
    story.append(SectionHeader("3", "Commercial Tracks"))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("Track A — Unified Route", s['TrackTitle']))
    for num, text in [
        ("3.1", "When the client procures the joint stack through a single contract and single invoice, OMNIX "
                "acts as the prime contracting party. OMNIX issues all invoicing and maintains the primary "
                "client relationship and account ownership."),
        ("3.2", "Revenue is distributed on a 70/30 basis: 70% to OMNIX, 30% to Velos, calculated on the "
                "total contract value invoiced to the client."),
        ("3.3", "OMNIX retains full discretion to set the final contract price to the client. The 30% Velos "
                "share is calculated on the total invoiced amount regardless of the pricing tier selected by OMNIX."),
        ("3.4", "The 70/30 split is an internal arrangement between the Parties and shall not be disclosed "
                "to the client."),
        ("3.5", "OMNIX shall transfer Velos's share within 15 business days of receipt of client payment."),
    ]:
        story.append(Paragraph(num, s['ClauseNum']))
        story.append(Paragraph(text, s['ClauseBody']))

    # Revenue split summary table
    split_data = [
        [Paragraph("Pricing Tier", s['SignLabel']),
         Paragraph("Total Bundle", s['SignLabel']),
         Paragraph("OMNIX (70%)", s['SignLabel']),
         Paragraph("Velos (30%)", s['SignLabel'])],
        [Paragraph("Institutional Node", s['SignValue']),
         Paragraph("$25,000/mo", s['SignValue']),
         Paragraph("$17,500/mo", s['SignValue']),
         Paragraph("$7,500/mo", s['SignValue'])],
        [Paragraph("Enterprise Cluster", s['SignValue']),
         Paragraph("$55,000/mo", s['SignValue']),
         Paragraph("$38,500/mo", s['SignValue']),
         Paragraph("$16,500/mo", s['SignValue'])],
        [Paragraph("Sovereign Stack", s['SignValue']),
         Paragraph("$95,000/mo", s['SignValue']),
         Paragraph("$66,500/mo", s['SignValue']),
         Paragraph("$28,500/mo", s['SignValue'])],
    ]
    split_table = Table(split_data, colWidths=[1.9*inch, 1.6*inch, 1.6*inch, 1.4*inch])
    split_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a2332')),
        ('BACKGROUND', (0, 1), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, GOLD),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#2d3748')),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(split_table)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Track B — Modular Route", s['TrackTitle']))
    for num, text in [
        ("3.6", "When the client procures governance and execution layers under separate contracts, Velos "
                "contracts directly with the client for the execution layer at a flat infrastructure fee "
                "of $4,500 USD per month per enterprise node."),
        ("3.7", "OMNIX contracts directly with the client for the governance layer at its applicable pricing "
                "tier. No revenue sharing between the Parties applies under this track."),
        ("3.8", "Under Track B, OMNIX retains 100% of its contract value and Velos retains 100% of its "
                "$4,500 monthly fee."),
    ]:
        story.append(Paragraph(num, s['ClauseNum']))
        story.append(Paragraph(text, s['ClauseBody']))

    story.append(Spacer(1, 0.2 * inch))

    # ── SECTION 4 — OPERATIONAL GOVERNANCE ────────────────────────────────
    story.append(SectionHeader("4", "Operational Governance"))
    story.append(Spacer(1, 0.1 * inch))

    for num, label, text in [
        ("4.1", "Route Selection:",
         "The applicable commercial track is determined jointly by both Parties based on the client's "
         "procurement preference. Neither Party may unilaterally designate a track without the other "
         "Party's written confirmation."),
        ("4.2", "Mutual Authorisation:",
         "No joint stack deployment may proceed under either track without prior written confirmation "
         "from both Parties. The OMNIX Governance Layer may not be activated in a Velos environment, "
         "and the Velos Execution Layer may not be deployed against OMNIX infrastructure, without "
         "mutual sign-off."),
        ("4.3", "Modular Route Client Engagement:",
         "Velos shall notify and obtain written approval from OMNIX prior to engaging any client under "
         "the Modular Route involving the joint stack. No direct client contract under Track B may be "
         "executed without OMNIX written approval."),
        ("4.4", "Pipeline Transparency:",
         "Both Parties agree to maintain a shared pipeline log of active and prospective joint stack "
         "opportunities, updated within 5 business days of any material development."),
        ("4.5", "Architectural Transparency:",
         "In all Unified Route (Track A) deployments, OMNIX agrees that the Velos Execution Layer shall "
         "remain architecturally transparent, and Velos shall be explicitly identified to the end-client "
         "as the terminal enforcement provider. This transparency is a required condition for the "
         "client's cyber-insurance underwriting and audit trail validity."),
    ]:
        story.append(Paragraph(f"{num}  {label}", s['ClauseNum']))
        story.append(Paragraph(text, s['ClauseBody']))

    story.append(Spacer(1, 0.2 * inch))
    story.append(PageBreak())

    # ── SECTION 5 — LIABILITY ──────────────────────────────────────────────
    story.append(SectionHeader("5", "Liability"))
    story.append(Spacer(1, 0.1 * inch))

    for num, text in [
        ("5.1", "Each Party shall be solely responsible for its own systems, outputs, and performance under "
                "this Supplement. OMNIX assumes no liability for the performance or failure of the Velos "
                "Execution Layer. Velos assumes no liability for the performance or failure of the OMNIX "
                "Governance Layer."),
        ("5.2", "No joint liability is created under this Supplement. Each Party's liability to the client "
                "for its respective layer is governed solely by its own direct contractual arrangements "
                "with that client."),
        ("5.3", "In the Unified Route, OMNIX as prime contractor bears contractual liability to the client "
                "for the total bundled offering. OMNIX shall include appropriate back-to-back liability "
                "provisions in its agreement with Velos for the execution layer component."),
    ]:
        story.append(Paragraph(num, s['ClauseNum']))
        story.append(Paragraph(text, s['ClauseBody']))

    story.append(Spacer(1, 0.2 * inch))

    # ── SECTION 6 — BRAND AND MARKETING ───────────────────────────────────
    story.append(SectionHeader("6", "Brand and Marketing"))
    story.append(Spacer(1, 0.1 * inch))

    for num, text in [
        ("6.1", "Neither Party may use the name, brand, logo, trademarks, or technology references of the "
                "other Party in any public, client-facing, or marketing material without prior written "
                "consent from the other Party."),
        ("6.2", "Any co-branded materials, joint press releases, or public references to the partnership "
                "must be approved in writing by both Parties prior to publication or distribution."),
    ]:
        story.append(Paragraph(num, s['ClauseNum']))
        story.append(Paragraph(text, s['ClauseBody']))

    story.append(Spacer(1, 0.2 * inch))

    # ── SECTION 7 — NON-EXCLUSIVITY ───────────────────────────────────────
    story.append(SectionHeader("7", "Non-Exclusivity"))
    story.append(Spacer(1, 0.1 * inch))

    for num, text in [
        ("7.1", "This Supplement is non-exclusive. Both Parties remain free to engage with other partners, "
                "clients, or technology integrations independently, provided that such engagements do not "
                "breach the confidentiality obligations of the Agreement."),
        ("7.2", "Neither Party acquires any right of first refusal, exclusivity, or preferential treatment "
                "in any market or territory as a result of this Supplement."),
    ]:
        story.append(Paragraph(num, s['ClauseNum']))
        story.append(Paragraph(text, s['ClauseBody']))

    story.append(Spacer(1, 0.2 * inch))

    # ── SECTION 8 — TERM AND TERMINATION ──────────────────────────────────
    story.append(SectionHeader("8", "Term and Termination"))
    story.append(Spacer(1, 0.1 * inch))

    for num, text in [
        ("8.1", "This Supplement shall remain in force for the duration of the Agreement unless terminated "
                "earlier by mutual written agreement of both Parties with 60 days written notice."),
        ("8.2", "Termination of this Supplement does not affect the validity or enforceability of the "
                "Agreement or any independent arrangements thereunder."),
    ]:
        story.append(Paragraph(num, s['ClauseNum']))
        story.append(Paragraph(text, s['ClauseBody']))

    story.append(Spacer(1, 0.2 * inch))

    # ── SECTION 9 — GOVERNING LAW ──────────────────────────────────────────
    story.append(SectionHeader("9", "Governing Law"))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "This Supplement is governed by the laws of England and Wales. Any disputes arising from this "
        "Supplement shall be subject to the exclusive jurisdiction of the courts of England and Wales.",
        s['ClauseBody']
    ))
    story.append(Spacer(1, 0.3 * inch))

    # ── SIGNATURE BLOCK ────────────────────────────────────────────────────
    story.append(GoldLine())
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("EXECUTION — AUTHORISED SIGNATURES", s['HighlightBox']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(sig_table())
    story.append(Spacer(1, 0.3 * inch))
    story.append(GoldLine())
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "This Supplement forms an integral part of the Master Partnership Agreement v2.0 dated "
        "03 April 2026 between OMNIX Quantum Ltd and Velos. All terms not expressly modified "
        "herein remain in full force and effect.",
        s['ConfidentialNote']
    ))
    story.append(Paragraph(
        "OMNIX Quantum Ltd — Registered in England & Wales — omnixquantum.net",
        s['ConfidentialNote']
    ))

    doc.build(story, onFirstPage=dark_page, onLaterPages=dark_page)
    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
