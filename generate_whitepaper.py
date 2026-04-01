"""
OMNIX — Technical Whitepaper 2026
Decision Governance Infrastructure for Automated Systems
Professional PDF — Institutional Grade
"""

import os
import tempfile
from datetime import datetime
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT

# ── Color palette ─────────────────────────────────────────────────────────────
DARK_BG    = HexColor('#0a0f1a')
DARK_MID   = HexColor('#0f172a')
CARD_BG    = HexColor('#1e293b')
CARD2_BG   = HexColor('#162032')
GOLD       = HexColor('#C9A227')
GOLD_LIGHT = HexColor('#F5D97A')
RED_ALERT  = HexColor('#ef4444')
GREEN_OK   = HexColor('#10b981')
YELLOW     = HexColor('#f59e0b')
GRAY       = HexColor('#94a3b8')
GRAY2      = HexColor('#64748b')
WHITE      = HexColor('#ffffff')
BLUE       = HexColor('#3b82f6')
CYAN       = HexColor('#06b6d4')
BORDER     = HexColor('#334155')

W, H = letter
LOGO   = '/home/runner/workspace/omnix_web/public/omnix_logo.png'
OUTPUT = '/home/runner/workspace/OMNIX_Technical_Whitepaper_2026.pdf'


def prepare_logo(bg=(10, 15, 26)):
    img = PILImage.open(LOGO).convert('RGBA')
    background = PILImage.new('RGB', img.size, bg)
    background.paste(img, mask=img.split()[3])
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    background.save(tmp.name)
    return tmp.name


LOGO_DARK = prepare_logo() if os.path.exists(LOGO) else None


# ── Background callback ───────────────────────────────────────────────────────
def dark_page(c, doc):
    c.saveState()
    c.setFillColor(DARK_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, 0, 4, H, fill=1, stroke=0)
    c.setFillColor(GRAY2)
    c.setFont('Helvetica', 7)
    c.drawString(0.75 * inch, 0.35 * inch,
                 'OMNIX — Decision Governance Infrastructure  |  Confidential')
    c.drawRightString(W - 0.65 * inch, 0.35 * inch, 'omnixquantum.net')
    c.drawCentredString(W / 2, 0.35 * inch, 'April 2026  ·  Harold Nunes, Founder & CEO')
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(0.65 * inch, 0.52 * inch, W - 0.65 * inch, 0.52 * inch)
    c.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    s = getSampleStyleSheet()
    defs = [
        ParagraphStyle('CoverTitle',   fontName='Helvetica-Bold',    fontSize=30, textColor=GOLD,       spaceAfter=8,  spaceBefore=4,  alignment=TA_LEFT, leading=36),
        ParagraphStyle('CoverSub',     fontName='Helvetica',         fontSize=12, textColor=WHITE,      spaceAfter=4,  spaceBefore=4,  alignment=TA_LEFT),
        ParagraphStyle('CoverMeta',    fontName='Helvetica',         fontSize=9,  textColor=GRAY,       spaceAfter=3,  spaceBefore=3,  alignment=TA_LEFT),
        ParagraphStyle('SectionTitle', fontName='Helvetica-Bold',    fontSize=14, textColor=GOLD,       spaceAfter=8,  spaceBefore=16, alignment=TA_LEFT),
        ParagraphStyle('SectionSub',   fontName='Helvetica-Bold',    fontSize=10, textColor=CYAN,       spaceAfter=5,  spaceBefore=8,  alignment=TA_LEFT),
        ParagraphStyle('Body',         fontName='Helvetica',         fontSize=9.5, textColor=GRAY,      spaceAfter=6,  spaceBefore=2,  alignment=TA_JUSTIFY, leading=15),
        ParagraphStyle('BodyW',        fontName='Helvetica',         fontSize=9.5, textColor=WHITE,     spaceAfter=6,  spaceBefore=2,  alignment=TA_JUSTIFY, leading=15),
        ParagraphStyle('BodyLeft',     fontName='Helvetica',         fontSize=9.5, textColor=GRAY,      spaceAfter=4,  spaceBefore=2,  alignment=TA_LEFT,    leading=15),
        ParagraphStyle('Bold',         fontName='Helvetica-Bold',    fontSize=9.5, textColor=WHITE,     spaceAfter=4,  spaceBefore=2,  alignment=TA_LEFT),
        ParagraphStyle('Quote',        fontName='Helvetica-Oblique', fontSize=10,  textColor=GOLD_LIGHT, spaceAfter=8, spaceBefore=8,  alignment=TA_CENTER,  leading=16, leftIndent=24, rightIndent=24),
        ParagraphStyle('TH',           fontName='Helvetica-Bold',    fontSize=8,  textColor=GOLD,       leading=11),
        ParagraphStyle('TD',           fontName='Helvetica',         fontSize=8.5, textColor=WHITE,     leading=13),
        ParagraphStyle('TDGray',       fontName='Helvetica',         fontSize=8.5, textColor=GRAY,      leading=13),
        ParagraphStyle('TDCyan',       fontName='Helvetica-Bold',    fontSize=8.5, textColor=CYAN,      leading=13),
        ParagraphStyle('TDGold',       fontName='Helvetica-Bold',    fontSize=8.5, textColor=GOLD,      leading=13),
        ParagraphStyle('TDGreen',      fontName='Helvetica-Bold',    fontSize=8.5, textColor=GREEN_OK,  leading=13),
        ParagraphStyle('SmallGray',    fontName='Helvetica',         fontSize=7.5, textColor=GRAY,      spaceAfter=3,  alignment=TA_LEFT),
        ParagraphStyle('TOCItem',      fontName='Helvetica',         fontSize=9.5, textColor=GRAY,      spaceAfter=5,  spaceBefore=2,  alignment=TA_LEFT, leading=14),
        ParagraphStyle('TOCTitle',     fontName='Helvetica-Bold',    fontSize=9.5, textColor=WHITE,     spaceAfter=5,  spaceBefore=2,  alignment=TA_LEFT, leading=14),
        ParagraphStyle('Bullet',       fontName='Helvetica',         fontSize=9.5, textColor=GRAY,      spaceAfter=3,  spaceBefore=2,  alignment=TA_LEFT, leading=14, leftIndent=14, bulletIndent=0),
    ]
    for st in defs:
        try:
            s.add(st)
        except Exception:
            pass
    return s


ST = make_styles()


# ── Helpers ───────────────────────────────────────────────────────────────────
def th(text):     return Paragraph(text, ST['TH'])
def td(text):     return Paragraph(text, ST['TD'])
def tdg(text):    return Paragraph(text, ST['TDGray'])
def tdc(text):    return Paragraph(text, ST['TDCyan'])
def tdgold(text): return Paragraph(text, ST['TDGold'])
def tdgreen(text):return Paragraph(text, ST['TDGreen'])


BASE_TABLE = TableStyle([
    ('BACKGROUND',    (0, 0), (-1,  0), HexColor('#0d1929')),
    ('BACKGROUND',    (0, 1), (-1, -1), CARD_BG),
    ('ROWBACKGROUNDS',(0, 1), (-1, -1), [CARD_BG, CARD2_BG]),
    ('GRID',          (0, 0), (-1, -1), 0.5, BORDER),
    ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING',    (0, 0), (-1, -1), 7),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ('LEFTPADDING',   (0, 0), (-1, -1), 9),
    ('RIGHTPADDING',  (0, 0), (-1, -1), 9),
])


def gold_bar(text):
    t = Table(
        [[Paragraph(f'<b>{text}</b>',
                    ParagraphStyle('gb', fontName='Helvetica-Bold', fontSize=11,
                                   textColor=DARK_BG, spaceAfter=0))]],
        colWidths=[7.1 * inch]
    )
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
    ]))
    return t


def section(title, subtitle=None):
    items = [
        Spacer(1, 0.08 * inch),
        HRFlowable(width='100%', thickness=0.5, color=BORDER),
        Spacer(1, 0.06 * inch),
        Paragraph(title, ST['SectionTitle']),
    ]
    if subtitle:
        items.append(Paragraph(subtitle, ST['SectionSub']))
    return items


def card(rows_data, col_widths):
    t = Table(rows_data, colWidths=col_widths)
    t.setStyle(BASE_TABLE)
    return t


def bullet(text):
    return Paragraph(f'<bullet>•</bullet>  {text}', ST['Bullet'])


# ── Logo row ──────────────────────────────────────────────────────────────────
def logo_row():
    if not LOGO_DARK:
        return Paragraph('<b>OMNIX</b> Decision Governance Infrastructure', ST['Bold'])
    row = Table(
        [[Image(LOGO_DARK, width=0.85 * inch, height=0.70 * inch),
          Paragraph(
              '<font color="#C9A227"><b>OMNIX</b></font>  '
              '<font color="#94a3b8">Decision Governance Infrastructure</font>',
              ParagraphStyle('lh', fontName='Helvetica-Bold', fontSize=13,
                             textColor=WHITE, leading=18)
          )]],
        colWidths=[1.0 * inch, 6.1 * inch]
    )
    row.setStyle(TableStyle([
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING',   (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
    ]))
    return row


# ─────────────────────────────────────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        leftMargin=0.70 * inch, rightMargin=0.65 * inch,
        topMargin=0.65 * inch,  bottomMargin=0.80 * inch
    )
    E = []

    # ── COVER PAGE ────────────────────────────────────────────────────────────
    E.append(Spacer(1, 0.25 * inch))
    E.append(logo_row())
    E.append(Spacer(1, 0.30 * inch))
    E.append(HRFlowable(width='100%', thickness=2, color=GOLD))
    E.append(Spacer(1, 0.25 * inch))

    E.append(Paragraph('OMNIX', ParagraphStyle(
        'CT', fontName='Helvetica-Bold', fontSize=38,
        textColor=GOLD, spaceAfter=4, leading=42
    )))
    E.append(Paragraph(
        'Decision Governance Infrastructure<br/>for Automated Systems',
        ParagraphStyle('CT2', fontName='Helvetica-Bold', fontSize=18,
                       textColor=WHITE, spaceAfter=6, leading=24)
    ))
    E.append(Spacer(1, 0.10 * inch))
    E.append(Paragraph(
        'A Technical Whitepaper on Verifiable, Cryptographically-Sealed '
        'Governance for High-Stakes Automated Decisions',
        ParagraphStyle('CT3', fontName='Helvetica', fontSize=11,
                       textColor=GRAY, spaceAfter=6, leading=16,
                       alignment=TA_LEFT)
    ))
    E.append(Spacer(1, 0.20 * inch))
    E.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
    E.append(Spacer(1, 0.15 * inch))

    E.append(Paragraph('April 2026  ·  Confidential', ST['CoverMeta']))
    E.append(Paragraph('Harold Nunes  ·  Founder &amp; CEO', ST['CoverMeta']))
    E.append(Paragraph('contacto@omnixquantum.net  ·  omnixquantum.net', ST['CoverMeta']))
    E.append(Paragraph('Abu Dhabi, UAE', ST['CoverMeta']))
    E.append(Spacer(1, 0.25 * inch))

    # Cover badges
    badge_data = [[
        Paragraph('Eureka GCC Dubai 2026\nSemifinalist',
                  ParagraphStyle('b1', fontName='Helvetica-Bold', fontSize=8,
                                 textColor=GOLD, alignment=TA_CENTER, leading=12)),
        Paragraph('Production 24/7\nRailway Cloud',
                  ParagraphStyle('b2', fontName='Helvetica-Bold', fontSize=8,
                                 textColor=CYAN, alignment=TA_CENTER, leading=12)),
        Paragraph('SSRN Published\nabstract_id=6321298',
                  ParagraphStyle('b3', fontName='Helvetica-Bold', fontSize=8,
                                 textColor=GREEN_OK, alignment=TA_CENTER, leading=12)),
        Paragraph('Zenodo DOI\n10.5281/zenodo.19056919',
                  ParagraphStyle('b4', fontName='Helvetica-Bold', fontSize=8,
                                 textColor=WHITE, alignment=TA_CENTER, leading=12)),
    ]]
    badge_table = Table(badge_data, colWidths=[1.77 * inch] * 4)
    badge_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, 0), HexColor('#1a150a')),
        ('BACKGROUND',    (1, 0), (1, 0), HexColor('#0a1a1f')),
        ('BACKGROUND',    (2, 0), (2, 0), HexColor('#0a1a12')),
        ('BACKGROUND',    (3, 0), (3, 0), CARD_BG),
        ('BOX',           (0, 0), (0, 0), 1,   GOLD),
        ('BOX',           (1, 0), (1, 0), 1,   CYAN),
        ('BOX',           (2, 0), (2, 0), 1,   GREEN_OK),
        ('BOX',           (3, 0), (3, 0), 1,   BORDER),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    E.append(badge_table)
    E.append(Spacer(1, 0.30 * inch))

    # Cover abstract
    abstract_box = Table(
        [[Paragraph(
            'OMNIX is a domain-agnostic Decision Governance Infrastructure that '
            'governs high-stakes automated decisions across trading, Islamic credit, '
            'insurance, and robotics. Every decision passes through an 11-checkpoint '
            'governance pipeline and receives a cryptographically-sealed, publicly '
            'verifiable receipt — making automated decisions auditable, traceable, '
            'and accountable at the moment they are made.',
            ParagraphStyle('abs', fontName='Helvetica', fontSize=10, textColor=WHITE,
                           leading=16, alignment=TA_JUSTIFY)
        )]],
        colWidths=[7.1 * inch]
    )
    abstract_box.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), CARD_BG),
        ('BOX',           (0, 0), (-1, -1), 1, GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING',   (0, 0), (-1, -1), 16),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 16),
    ]))
    E.append(abstract_box)

    E.append(PageBreak())

    # ── TABLE OF CONTENTS ─────────────────────────────────────────────────────
    E.append(Spacer(1, 0.1 * inch))
    E.append(Paragraph('Table of Contents', ST['SectionTitle']))
    E.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
    E.append(Spacer(1, 0.12 * inch))

    toc = [
        ('1.', 'Executive Summary'),
        ('2.', 'The Problem: Governance Gap in Automated Systems'),
        ('3.', 'OMNIX: What It Is'),
        ('4.', 'The 11-Checkpoint Governance Pipeline'),
        ('5.', 'Four Governance Domains'),
        ('6.', 'The Verifiable Governance Receipt'),
        ('7.', 'Regulatory Alignment'),
        ('8.', 'Cryptographic Accountability'),
        ('9.', 'Academic Validation & Track Record'),
        ('10.', 'Enterprise Use Cases'),
        ('11.', 'About & Contact'),
    ]
    for num, title in toc:
        toc_row = Table(
            [[Paragraph(f'<b>{num}</b>', ST['TOCTitle']),
              Paragraph(title, ST['TOCItem'])]],
            colWidths=[0.45 * inch, 6.65 * inch]
        )
        toc_row.setStyle(TableStyle([
            ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING',  (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',   (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ]))
        E.append(toc_row)

    E.append(PageBreak())

    # ── SECTION 1: EXECUTIVE SUMMARY ──────────────────────────────────────────
    E.extend(section('1.  Executive Summary'))
    E.append(Paragraph(
        'Automated systems now make thousands of consequential decisions every second — '
        'from executing financial trades to approving credit applications and authorizing '
        'insurance payouts. Despite their scale and impact, the vast majority of these '
        'decisions leave no auditable trail. When something goes wrong, there is no receipt, '
        'no signed record, and no verifiable proof of what the system decided and why.',
        ST['Body']
    ))
    E.append(Paragraph(
        'OMNIX addresses this gap directly. It is a Decision Governance Infrastructure '
        'that intercepts automated decisions before they execute, evaluates them through '
        'an 11-checkpoint pipeline, and issues a cryptographically-sealed governance '
        'receipt that is publicly verifiable and immutable.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.08 * inch))

    exec_data = [
        [th('Dimension'), th('OMNIX Position')],
        [td('Market'),          td('$137B+ TAM across financial services, insurance, and robotics governance')],
        [td('Stage'),           td('Operational 24/7 in production — Railway cloud infrastructure')],
        [td('Funding Target'),  td('$500,000 USD pre-seed  ·  $3M pre-money valuation')],
        [td('Domains Active'),  td('Digital asset trading  ·  Islamic credit  ·  Insurance claims  ·  Robotics')],
        [td('Pipeline'),        td('11 governance checkpoints — fail-closed, no exceptions')],
        [td('Receipt Type'),    td('Post-quantum cryptographic signature  ·  Merkle chain anchored')],
        [td('Founder'),         td('Harold Nunes — Eureka GCC Dubai 2026 Semifinalist')],
    ]
    E.append(card(exec_data, [2.1 * inch, 5.0 * inch]))
    E.append(Spacer(1, 0.08 * inch))

    E.append(Paragraph(
        '"Governance infrastructure is not a feature — it is the foundation '
        'upon which trust in automated systems is built."',
        ST['Quote']
    ))

    E.append(PageBreak())

    # ── SECTION 2: THE PROBLEM ────────────────────────────────────────────────
    E.extend(section('2.  The Problem: Governance Gap in Automated Systems'))
    E.append(Paragraph(
        'The deployment of automated decision-making systems has outpaced the development '
        'of governance frameworks capable of holding those decisions accountable. '
        'This creates three interconnected failure modes that affect every sector '
        'deploying automated systems at scale.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.06 * inch))

    E.append(Paragraph('Failure Mode 1 — No Auditable Trail', ST['SectionSub']))
    E.append(Paragraph(
        'When an automated system makes a consequential decision — blocking a trade, '
        'denying a loan, rejecting an insurance claim — there is typically no signed '
        'record of what inputs were evaluated, which rules were applied, and what the '
        'system concluded. Logs can be deleted, modified, or simply never created. '
        'This makes post-hoc accountability impossible.',
        ST['Body']
    ))

    E.append(Paragraph('Failure Mode 2 — Silent Failure', ST['SectionSub']))
    E.append(Paragraph(
        'Most automated systems fail open: when a component breaks or an edge case '
        'is encountered, the system defaults to executing the action rather than '
        'halting. This behavior is catastrophic in high-stakes environments where a '
        'single unchecked decision can cause irreversible harm — financial losses, '
        'regulatory violations, or physical injury.',
        ST['Body']
    ))

    E.append(Paragraph('Failure Mode 3 — Regulatory Exposure', ST['SectionSub']))
    E.append(Paragraph(
        'The EU AI Act, NIST AI Risk Management Framework, and emerging GCC regulations '
        'are converging on a common requirement: automated systems that affect people '
        'must be explainable, auditable, and subject to human oversight. '
        'Organizations that cannot demonstrate these properties face significant '
        'legal and operational risk.',
        ST['Body']
    ))

    E.append(Spacer(1, 0.08 * inch))
    problem_data = [
        [th('Failure Mode'), th('Consequence'), th('OMNIX Response')],
        [td('No auditable trail'),   td('No accountability when decisions go wrong'),      tdc('Signed receipt per decision')],
        [td('Silent failure'),       td('Unchecked execution in error conditions'),          tdc('Fail-closed pipeline')],
        [td('Regulatory exposure'),  td('Non-compliance with AI Act / NIST RMF'),            tdc('Built-in alignment controls')],
    ]
    E.append(card(problem_data, [2.2 * inch, 2.7 * inch, 2.2 * inch]))

    E.append(PageBreak())

    # ── SECTION 3: WHAT OMNIX IS ──────────────────────────────────────────────
    E.extend(section('3.  OMNIX: What It Is'))
    E.append(Paragraph(
        'OMNIX is not a trading algorithm, a risk scoring tool, or a compliance '
        'reporting system. It is a governance layer — infrastructure that sits '
        'between the moment a decision is proposed and the moment it is executed.',
        ST['Body']
    ))
    E.append(Paragraph(
        'Any automated system — financial, medical, industrial, or otherwise — can '
        'submit a proposed decision to OMNIX. OMNIX evaluates the proposal through '
        'its governance pipeline, makes an independent determination, and returns a '
        'cryptographically-sealed receipt. The submitting system cannot proceed without '
        'that receipt. OMNIX operates fail-closed: if the pipeline cannot complete, '
        'the decision is blocked.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.08 * inch))

    what_data = [
        [th('OMNIX Is'), th('OMNIX Is Not')],
        [td('A governance layer for automated decisions'),          td('A trading algorithm or signal generator')],
        [td('A cryptographic accountability infrastructure'),       td('A risk scoring or analytics dashboard')],
        [td('A fail-closed decision pipeline'),                     td('A compliance reporting tool')],
        [td('A domain-agnostic governance engine'),                 td('A vertical-specific application')],
        [td('A verifiable receipt issuer'),                         td('A system that replaces human judgment')],
    ]
    E.append(card(what_data, [3.55 * inch, 3.55 * inch]))
    E.append(Spacer(1, 0.10 * inch))

    E.append(Paragraph(
        'OMNIX is deployed as infrastructure, not software. Enterprise clients connect '
        'to OMNIX through an authenticated API. The governance pipeline runs independently '
        'of the client system, ensuring that governance cannot be bypassed, modified, '
        'or overridden by the system being governed.',
        ST['Body']
    ))

    E.append(PageBreak())

    # ── SECTION 4: THE PIPELINE ───────────────────────────────────────────────
    E.extend(section('4.  The 11-Checkpoint Governance Pipeline'))
    E.append(Paragraph(
        'Every decision submitted to OMNIX passes through an identical, ordered sequence '
        'of 11 independent governance checkpoints. Each checkpoint evaluates the decision '
        'from a distinct governance dimension. If any checkpoint determines that the '
        'decision cannot be authorized, the pipeline halts and returns a BLOCKED receipt. '
        'There are no exceptions and no bypass mechanisms.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.08 * inch))

    cp_data = [
        [th('Checkpoint'), th('Code'), th('Governance Dimension')],
        [td('Signal Integrity Validator'),     tdc('CP-0'),  td('Verifies the structural and semantic integrity of the incoming decision signal')],
        [td('Probability Assessment'),         tdc('CP-1'),  td('Evaluates statistical confidence and distributional validity of the proposed outcome')],
        [td('Risk Quantification'),            tdc('CP-2'),  td('Measures exposure relative to authorized risk thresholds and position limits')],
        [td('Coherence Engine'),               tdc('CP-3'),  td('Detects internal contradictions across simultaneous decision signals')],
        [td('Trend & Regime Analysis'),        tdc('CP-4'),  td('Assesses alignment of the proposed decision with prevailing market or system regime')],
        [td('Stress Testing Gate'),            tdc('CP-5'),  td('Simulates extreme-scenario performance and evaluates robustness under stress conditions')],
        [td('Domain Compliance Gate'),         tdc('CP-6'),  td('Enforces domain-specific rules (Sharia principles, insurance regulations, safety protocols)')],
        [td('Trajectory Coherence Validator'), tdc('CP-7'),  td('Ensures the decision is consistent with the established trajectory of prior decisions')],
        [td('Forward Trajectory Implicator'),  tdc('CP-8'),  td('Projects the downstream consequences of execution across time horizons')],
        [td('AML Governance Gate'),            tdc('CP-9'),  td('Screens for anti-money laundering risk patterns before authorization')],
        [td('Fraud & Jurisdiction Gate'),      tdc('CP-10'), td('Validates fraud risk indicators and confirms jurisdictional compliance')],
    ]
    E.append(card(cp_data, [2.3 * inch, 0.8 * inch, 4.0 * inch]))
    E.append(Spacer(1, 0.08 * inch))

    E.append(Paragraph(
        'Following checkpoint evaluation, each decision is also subject to two additional '
        'governance layers: the Context Admission Gate (CAG), which validates the '
        'contextual boundary of the decision, and the Trajectory Invariant Enforcement '
        '(TIE) module, which ensures that governance constraints cannot be circumvented '
        'through sequential decision manipulation.',
        ST['Body']
    ))

    E.append(PageBreak())

    # ── SECTION 5: FOUR DOMAINS ───────────────────────────────────────────────
    E.extend(section('5.  Four Governance Domains'))
    E.append(Paragraph(
        'OMNIX operates the same 11-checkpoint pipeline across four distinct governance '
        'domains simultaneously. The pipeline logic is identical across all domains — '
        'only the domain-specific parameters at CP-6 differ. This architecture '
        'demonstrates the domain-agnostic nature of the governance infrastructure.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.08 * inch))

    domain_data = [
        [th('Domain'), th('Scope'), th('Status')],
        [tdgold('Digital Asset Trading'),
         td('Governance of cryptocurrency and equity trade decisions. Every proposed entry or exit passes through the full pipeline before execution. Real capital exposure on Kraken exchange.'),
         tdgreen('LIVE 24/7')],
        [tdgold('Islamic Credit (UAE / GCC)'),
         td('Governance of Murabaha and Sharia-compliant financing decisions. CP-6 enforces Islamic finance principles including prohibition of riba and gharar. Aligned with AAOIFI standards.'),
         tdgreen('OPERATIONAL')],
        [tdgold('Insurance Claims'),
         td('Governance of automated insurance claim assessment decisions. Fraud detection, coverage validation, and jurisdictional compliance evaluated at each checkpoint before determination.'),
         tdgreen('OPERATIONAL')],
        [tdgold('Robotics Pre-Execution Safety'),
         td('Governance of autonomous robotic action decisions. Safety constraints and physical trajectory validation applied before any motor command is authorized.'),
         tdgreen('OPERATIONAL')],
    ]
    E.append(card(domain_data, [1.7 * inch, 4.1 * inch, 1.3 * inch]))

    E.append(PageBreak())

    # ── SECTION 6: THE RECEIPT ────────────────────────────────────────────────
    E.extend(section('6.  The Verifiable Governance Receipt'))
    E.append(Paragraph(
        'Every decision processed by OMNIX — whether authorized or blocked — '
        'generates a governance receipt. The receipt is the central accountability '
        'artifact of the OMNIX infrastructure. It contains the full pipeline result, '
        'a cryptographic seal, and a public verification URL.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.06 * inch))

    E.append(Paragraph('Sample Receipt Structure', ST['SectionSub']))

    receipt_lines = [
        '{',
        '  "receipt_id":          "omnix-gov-20260401-a7f3c9",',
        '  "timestamp":           "2026-04-01T14:32:17.841Z",',
        '  "decision":            "APPROVED",',
        '  "asset":               "BTC/USD",',
        '  "confidence_score":    0.847,',
        '  "checkpoints_passed":  11,',
        '  "checkpoints_total":   11,',
        '  "veto_count":          0,',
        '  "governance_summary":  "All checkpoints passed",',
        '  "cryptographic_seal": {',
        '    "algorithm":         "PQC signature (OMNIX implementation)",',
        '    "merkle_root":       "a3f7c2d8e1b490fa231c...",',
        '    "signature":         "3045022100f3a7c91d...",',
        '    "verification_url":  "https://omnixquantum.net/verify/omnix-gov-20260401-a7f3c9"',
        '  }',
        '}',
    ]

    receipt_rows = [[Paragraph(
        line,
        ParagraphStyle('code', fontName='Courier', fontSize=8,
                       textColor=CYAN, leading=13, spaceAfter=0)
    )] for line in receipt_lines]

    receipt_table = Table(receipt_rows, colWidths=[7.1 * inch])
    receipt_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), HexColor('#060c16')),
        ('BOX',           (0, 0), (-1, -1), 1, GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 14),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 14),
    ]))
    E.append(receipt_table)
    E.append(Spacer(1, 0.10 * inch))

    receipt_props = [
        [th('Receipt Property'), th('Description')],
        [td('receipt_id'),          td('Unique identifier — links the receipt to the full audit trail')],
        [td('decision'),            td('APPROVED / BLOCKED / HOLD — the governance determination')],
        [td('checkpoints_passed'),  td('Number of checkpoints that authorized the decision')],
        [td('governance_summary'),  td('Human-readable summary of the pipeline result')],
        [td('merkle_root'),         td('Hash anchored to the rolling Merkle chain — tamper-evident')],
        [td('signature'),           td('Post-quantum cryptographic signature — cannot be forged')],
        [td('verification_url'),    td('Public URL — anyone can independently verify this receipt')],
    ]
    E.append(card(receipt_props, [2.1 * inch, 5.0 * inch]))

    E.append(PageBreak())

    # ── SECTION 7: REGULATORY ALIGNMENT ──────────────────────────────────────
    E.extend(section('7.  Regulatory Alignment'))
    E.append(Paragraph(
        'OMNIX was designed with regulatory alignment as a first-class architectural '
        'requirement. Three major frameworks inform the governance structure: the EU AI Act, '
        'the NIST AI Risk Management Framework, and ISO/IEC 42001. OMNIX does not '
        'claim compliance with these frameworks — it is designed to make compliance '
        'demonstrable through its receipt infrastructure.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.08 * inch))

    reg_data = [
        [th('Framework'), th('Requirement'), th('OMNIX Implementation')],
        [tdgold('EU AI Act'),
         td('High-risk AI systems must maintain logs of decision-making and enable human oversight'),
         tdc('Every decision generates an immutable, signed receipt with full pipeline trace')],
        [tdgold('NIST AI RMF'),
         td('AI systems must be measurable, explainable, and subject to governance controls'),
         tdc('11-checkpoint pipeline provides structured, measurable governance evaluation')],
        [tdgold('ISO/IEC 42001'),
         td('AI management systems require documented risk controls and incident traceability'),
         tdc('Fail-closed pipeline with public verification URL enables full incident traceability')],
        [tdgold('AAOIFI (Islamic Finance)'),
         td('Sharia-compliant financing must adhere to principles prohibiting riba and gharar'),
         tdc('CP-6 enforces Islamic finance rules before any credit decision is authorized')],
    ]
    E.append(card(reg_data, [1.5 * inch, 2.8 * inch, 2.8 * inch]))
    E.append(Spacer(1, 0.10 * inch))

    E.append(Paragraph(
        'The public verification endpoint at omnixquantum.net/verify/:receiptId '
        'allows regulators, auditors, and counterparties to independently confirm '
        'the integrity and content of any governance receipt without accessing '
        'internal OMNIX systems.',
        ST['Body']
    ))

    E.append(PageBreak())

    # ── SECTION 8: CRYPTOGRAPHIC ACCOUNTABILITY ───────────────────────────────
    E.extend(section('8.  Cryptographic Accountability'))
    E.append(Paragraph(
        'Every governance receipt issued by OMNIX is protected by a multi-layer '
        'cryptographic architecture. This architecture ensures that receipts cannot '
        'be forged, modified, or repudiated after issuance — providing a level of '
        'accountability that traditional logging systems cannot achieve.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.08 * inch))

    crypto_data = [
        [th('Layer'), th('Mechanism'), th('Purpose')],
        [td('Digital Signature'),
         tdc('NIST-standardized post-quantum\ndigital signature algorithm'),
         td('Proves authenticity — the receipt was issued by OMNIX and has not been altered')],
        [td('Merkle Chain'),
         tdc('Rolling Merkle root anchoring\neach receipt to the prior chain'),
         td('Proves integrity — any modification to any receipt invalidates the entire chain')],
        [td('Timestamp Anchoring'),
         tdc('RFC 3161-style internal\ntimestamp per receipt'),
         td('Proves existence — the decision was made at a specific, verifiable moment in time')],
        [td('Public Verification'),
         tdc('Independent verification endpoint\nat omnixquantum.net/verify/'),
         td('Proves accessibility — any party can verify any receipt without internal access')],
    ]
    E.append(card(crypto_data, [1.6 * inch, 2.3 * inch, 3.2 * inch]))
    E.append(Spacer(1, 0.10 * inch))

    E.append(Paragraph(
        'The post-quantum digital signature algorithm used by OMNIX is standardized '
        'by the U.S. National Institute of Standards and Technology (NIST). '
        'This ensures that governance receipts remain cryptographically secure '
        'against both current and future computational threats, including those '
        'posed by quantum computing systems.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.08 * inch))

    E.append(Paragraph(
        '"A governance receipt is only meaningful if it cannot be forged. '
        'Post-quantum cryptography ensures that OMNIX receipts remain trustworthy '
        'regardless of the computational environment in which they are verified."',
        ST['Quote']
    ))

    E.append(PageBreak())

    # ── SECTION 9: ACADEMIC VALIDATION ───────────────────────────────────────
    E.extend(section('9.  Academic Validation & Track Record'))
    E.append(Paragraph(
        'The OMNIX governance architecture has been formally documented and submitted '
        'to two independent academic repositories. This provides an immutable, '
        'timestamped record of the architectural decisions and their rationale, '
        'independent of any commercial claims.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.08 * inch))

    acad_data = [
        [th('Repository'), th('Reference'), th('Scope')],
        [tdgold('SSRN'),
         td('Social Science Research Network\nabstract_id=6321298'),
         td('Decision governance architecture, pipeline design, and cryptographic receipt infrastructure')],
        [tdgold('Zenodo'),
         td('DOI: 10.5281/zenodo.19056919\nCERN Open Repository'),
         td('Technical architecture documentation with version-controlled academic reference')],
    ]
    E.append(card(acad_data, [1.3 * inch, 2.6 * inch, 3.2 * inch]))
    E.append(Spacer(1, 0.12 * inch))

    E.append(Paragraph('Operational Track Record', ST['SectionSub']))
    E.append(Paragraph(
        'OMNIX has been in continuous production operation since July 2025. '
        'The system has governed decisions across all four active domains without '
        'infrastructure failure. The following timeline reflects the development '
        'and operational history of the system.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.06 * inch))

    track_data = [
        [th('Period'), th('Type'), th('Description')],
        [td('Jul – Aug 2025'),     tdgold('Real Capital'),     td('Initial deployment with real capital on Kraken exchange. Governance pipeline validated under live market conditions.')],
        [td('Nov 2025 – Jan 2026'),td('Calibration Baseline'), td('Learning Baseline phase. Pipeline parameters recalibrated across all 11 checkpoints based on observed signal patterns.')],
        [td('Jan 15, 2026 – Now'), tdgreen('Track Record'),    td('Official Track Record phase. Recalibrated pipeline operating under paper trading with governance receipts issued for every decision.')],
        [td('Nov 2025'),           tdc('PQC Implementation'),  td('Post-quantum cryptographic signature architecture deployed. All receipts from this date carry NIST-standardized PQC signatures.')],
    ]
    E.append(card(track_data, [1.4 * inch, 1.5 * inch, 4.2 * inch]))

    E.append(PageBreak())

    # ── SECTION 10: ENTERPRISE USE CASES ─────────────────────────────────────
    E.extend(section('10.  Enterprise Use Cases'))
    E.append(Paragraph(
        'OMNIX delivers measurable governance value across any organization that '
        'operates automated decision systems in regulated or high-stakes environments. '
        'The following use cases represent the primary enterprise deployment scenarios.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.08 * inch))

    use_data = [
        [th('Sector'), th('Use Case'), th('OMNIX Value Delivered')],
        [tdgold('Financial Services'),
         td('Algorithmic trading, automated credit decisions, fraud detection authorizations'),
         td('Every decision carries a signed receipt enabling regulatory audit, dispute resolution, and risk attribution')],
        [tdgold('Insurance'),
         td('Automated claim assessment, fraud screening, coverage determination'),
         td('Governance receipts eliminate the "black box" problem — every determination is traceable and verifiable')],
        [tdgold('Islamic Finance\n(UAE / GCC)'),
         td('Murabaha financing, Sharia-compliant product structuring, credit governance'),
         td('CP-6 enforces Sharia compliance at the decision level — not as a post-hoc audit but as a pre-execution gate')],
        [tdgold('Robotics & AI Systems'),
         td('Pre-execution safety validation, autonomous action authorization'),
         td('Fail-closed governance prevents unauthorized action execution — every motor command requires a valid receipt')],
        [tdgold('Regulatory Technology'),
         td('AI Act compliance infrastructure, audit trail generation, human oversight enablement'),
         td('Public verification endpoint enables regulators to independently confirm governance receipts')],
    ]
    E.append(card(use_data, [1.4 * inch, 2.5 * inch, 3.2 * inch]))
    E.append(Spacer(1, 0.10 * inch))

    E.append(Paragraph('Commercial Model', ST['SectionSub']))
    pricing_data = [
        [th('Tier'), th('Description'), th('Price')],
        [tdgold('Shadow Mode'),  td('OMNIX runs parallel to existing systems. No intervention. Full receipt generation for audit purposes.'),        tdgreen('Complimentary')],
        [tdgold('Advisory'),     td('OMNIX governance results delivered as recommendations. Human decision-maker retains final authority.'),           td('$8,000 / month')],
        [tdgold('Enterprise'),   td('Full integration. OMNIX receipt required before any automated decision executes. Fail-closed enforcement.'),     td('$20,000 – $35,000 / month')],
        [tdgold('Custom'),       td('Multi-domain deployment, private infrastructure, custom governance parameters, and SLA guarantees.'),             tdc('Contact us')],
    ]
    E.append(card(pricing_data, [1.2 * inch, 3.9 * inch, 2.0 * inch]))

    E.append(PageBreak())

    # ── SECTION 11: ABOUT & CONTACT ───────────────────────────────────────────
    E.extend(section('11.  About & Contact'))
    E.append(Paragraph(
        'OMNIX was founded and built by Harold Nunes, a solo founder with deep expertise '
        'in decision systems architecture, post-quantum cryptography implementation, '
        'and multi-domain governance infrastructure. The system has been designed, '
        'engineered, and deployed entirely as a production-grade infrastructure from '
        'the outset.',
        ST['Body']
    ))
    E.append(Spacer(1, 0.08 * inch))

    about_data = [
        [th('Detail'), th('Information')],
        [td('Founder & CEO'),         td('Harold Nunes')],
        [td('Headquarters'),          td('Abu Dhabi, UAE')],
        [td('Infrastructure'),        td('Railway Cloud — 24/7 production uptime')],
        [td('Recognition'),           td('Eureka GCC Dubai 2026 — Semifinalist')],
        [td('Academic Publications'), td('SSRN abstract_id=6321298  ·  Zenodo DOI 10.5281/zenodo.19056919')],
        [td('Email'),                 tdc('contacto@omnixquantum.net')],
        [td('Web'),                   tdc('omnixquantum.net')],
        [td('WhatsApp'),              td('+1 (650) 507-8293')],
    ]
    E.append(card(about_data, [2.1 * inch, 5.0 * inch]))
    E.append(Spacer(1, 0.15 * inch))

    # Final CTA
    cta_box = Table(
        [[Paragraph(
            '<b>OMNIX is currently raising $500,000 USD in pre-seed funding at a '
            '$3,000,000 pre-money valuation.</b><br/><br/>'
            'For investor inquiries, enterprise pilot discussions, or technical due diligence, '
            'contact Harold Nunes directly at <font color="#06b6d4">contacto@omnixquantum.net</font> '
            'or visit <font color="#06b6d4">omnixquantum.net</font>.',
            ParagraphStyle('cta', fontName='Helvetica', fontSize=10, textColor=WHITE,
                           leading=16, alignment=TA_JUSTIFY)
        )]],
        colWidths=[7.1 * inch]
    )
    cta_box.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), CARD_BG),
        ('BOX',           (0, 0), (-1, -1), 2, GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ('LEFTPADDING',   (0, 0), (-1, -1), 18),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 18),
    ]))
    E.append(cta_box)
    E.append(Spacer(1, 0.15 * inch))

    E.append(Paragraph(
        'This document is confidential and intended solely for the recipient. '
        'The information contained herein does not constitute an offer to sell or '
        'a solicitation of an offer to buy any securities.',
        ST['SmallGray']
    ))

    # ── BUILD ──────────────────────────────────────────────────────────────────
    doc.build(E, onFirstPage=dark_page, onLaterPages=dark_page)
    print(f'✅  Whitepaper generated: {OUTPUT}')


if __name__ == '__main__':
    build()
