#!/usr/bin/env python3
"""
OMNIX Eureka GCC Semifinalist Report Generator
Generates professional institutional-grade PDF report.
Output: Report_OMNIX_HaroldNunes.pdf
"""

import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Image, ListFlowable, ListItem
)
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.lib.validators import Auto
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BRAND_NAVY = HexColor('#0A1628')
BRAND_BLUE = HexColor('#1E3A5F')
BRAND_ACCENT = HexColor('#2196F3')
BRAND_GOLD = HexColor('#C5A55A')
BRAND_LIGHT = HexColor('#F8F9FA')
BRAND_DARK_TEXT = HexColor('#1A1A2E')
BRAND_GRAY = HexColor('#6B7280')
BRAND_GREEN = HexColor('#10B981')
BRAND_RED = HexColor('#EF4444')
BRAND_LIGHT_BLUE = HexColor('#EBF5FF')
TABLE_HEADER_BG = HexColor('#1E3A5F')
TABLE_ALT_ROW = HexColor('#F0F4F8')
TABLE_BORDER = HexColor('#D1D5DB')

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'business', 'pdfs')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'Report_OMNIX_HaroldNunes_March2026.pdf')


def create_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CoverTitle',
        fontName='Helvetica-Bold',
        fontSize=36,
        leading=42,
        textColor=white,
        alignment=TA_LEFT,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        fontName='Helvetica',
        fontSize=16,
        leading=22,
        textColor=HexColor('#B0C4DE'),
        alignment=TA_LEFT,
        spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name='CoverTagline',
        fontName='Helvetica-Oblique',
        fontSize=13,
        leading=18,
        textColor=BRAND_GOLD,
        alignment=TA_LEFT,
        spaceAfter=30,
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=26,
        textColor=BRAND_NAVY,
        spaceBefore=24,
        spaceAfter=12,
        borderWidth=0,
        borderPadding=0,
    ))
    styles.add(ParagraphStyle(
        name='SubsectionTitle',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=BRAND_BLUE,
        spaceBefore=16,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name='BodyText2',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=BRAND_DARK_TEXT,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name='Quote',
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=15,
        textColor=BRAND_BLUE,
        leftIndent=20,
        rightIndent=20,
        spaceBefore=8,
        spaceAfter=12,
        borderWidth=2,
        borderColor=BRAND_ACCENT,
        borderPadding=10,
    ))
    styles.add(ParagraphStyle(
        name='FooterText',
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=BRAND_GRAY,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=white,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=BRAND_DARK_TEXT,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name='SmallNote',
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=BRAND_GRAY,
        alignment=TA_LEFT,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='BulletItem',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=BRAND_DARK_TEXT,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='Highlight',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=BRAND_ACCENT,
        spaceAfter=6,
    ))
    return styles


def make_table(headers, rows, col_widths=None):
    s = create_styles()
    header_cells = [Paragraph(h, s['TableHeader']) for h in headers]
    data = [header_cells]
    for row in rows:
        data.append([Paragraph(str(c), s['TableCell']) for c in row])

    w = col_widths or [None] * len(headers)
    t = Table(data, colWidths=w, repeatRows=1)

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ALT_ROW))

    t.setStyle(TableStyle(style_cmds))
    return t


def section_header(title, number, styles):
    elements = []
    line = HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT, spaceBefore=10, spaceAfter=4)
    elements.append(line)
    elements.append(Paragraph(f"{number}. {title}", styles['SectionTitle']))
    elements.append(Spacer(1, 4))
    return elements


def bullet_list(items, styles):
    elements = []
    for item in items:
        elements.append(Paragraph(f"\u2022  {item}", styles['BulletItem']))
    return elements


def draw_cover_background(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BRAND_NAVY)
    canvas.rect(0, 0, A4[0], A4[1], fill=True, stroke=False)
    canvas.setFillColor(BRAND_GOLD)
    canvas.rect(0, A4[1] - 100, A4[0], 4, fill=True, stroke=False)
    canvas.rect(0, 80, A4[0], 2, fill=True, stroke=False)
    canvas.restoreState()


def build_cover_page():
    elements = []

    s = create_styles()
    elements.append(Spacer(1, 120))
    elements.append(Paragraph("OMNIX", s['CoverTitle']))
    elements.append(Paragraph("Decision Governance Infrastructure<br/>for Automated Systems", s['CoverSubtitle']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph('"Preventing costly mistakes before they happen"', s['CoverTagline']))
    elements.append(Spacer(1, 30))

    info_style = ParagraphStyle(
        'CoverInfo', fontName='Helvetica', fontSize=11, leading=16,
        textColor=HexColor('#B0C4DE'), alignment=TA_LEFT
    )
    elements.append(Paragraph("Eureka! GCC 2026 \u2014 Semifinalist Report", info_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Startup: OMNIX", info_style))
    elements.append(Paragraph("Founder &amp; CEO: Harold Nunes", info_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Stage: MVP (Live Product)", info_style))
    elements.append(Paragraph("Pre-Seed Round: $500,000 USD", info_style))
    elements.append(Spacer(1, 30))

    contact_style = ParagraphStyle(
        'CoverContact', fontName='Helvetica', fontSize=9, leading=13,
        textColor=HexColor('#8899AA'), alignment=TA_LEFT
    )
    elements.append(Paragraph("contacto@omnixquantum.net", contact_style))
    elements.append(Paragraph("www.omnixquantum.net", contact_style))
    elements.append(Paragraph("linkedin.com/in/harold-nunes-21bb65285", contact_style))

    elements.append(Spacer(1, 40))

    date_style = ParagraphStyle(
        'CoverDate', fontName='Helvetica', fontSize=9, leading=12,
        textColor=BRAND_GOLD, alignment=TA_LEFT
    )
    elements.append(Paragraph(f"March 2026 | United Arab Emirates", date_style))
    elements.append(Paragraph("Classification: Competition Submission \u2014 Confidential", date_style))

    elements.append(PageBreak())
    return elements


def build_toc(styles):
    elements = []
    elements.append(Paragraph("Table of Contents", styles['SectionTitle']))
    elements.append(Spacer(1, 12))

    toc_items = [
        ("1", "Executive Summary", "3"),
        ("2", "Company Overview", "4"),
        ("3", "Problem & Market Opportunity", "5"),
        ("4", "Customer Validation & Insights", "7"),
        ("5", "Product & Technology", "8"),
        ("6", "Competitive Landscape & Differentiation", "10"),
        ("7", "Business Model & Unit Economics", "11"),
        ("8", "Traction & Key Metrics", "13"),
        ("9", "Go-To-Market Strategy", "14"),
        ("10", "Team & Advisors", "15"),
        ("11", "Financials & Fundraising", "16"),
        ("12", "Intellectual Property & Regulatory", "17"),
        ("13", "Risks & Challenges", "18"),
        ("14", "Appendix", "19"),
    ]

    toc_style = ParagraphStyle(
        'TOCItem', fontName='Helvetica', fontSize=11, leading=20,
        textColor=BRAND_DARK_TEXT, leftIndent=10
    )
    toc_num_style = ParagraphStyle(
        'TOCNum', fontName='Helvetica-Bold', fontSize=11, leading=20,
        textColor=BRAND_ACCENT
    )

    for num, title, page in toc_items:
        row = [
            Paragraph(num, toc_num_style),
            Paragraph(title, toc_style),
            Paragraph(page, ParagraphStyle('TOCPage', fontName='Helvetica', fontSize=11,
                                           textColor=BRAND_GRAY, alignment=TA_RIGHT))
        ]
        t = Table([row], colWidths=[30, 380, 50])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor('#E5E7EB')),
        ]))
        elements.append(t)

    elements.append(PageBreak())
    return elements


def build_section_1(styles):
    elements = []
    elements.extend(section_header("Executive Summary", "1", styles))

    elements.append(Paragraph(
        "<b>Problem:</b> High-stakes automated decision systems \u2014 from trading to supply chain to lending \u2014 "
        "lack institutional-grade governance infrastructure, leading to billions in preventable losses annually.",
        styles['BodyText2']
    ))
    elements.append(Paragraph(
        "<b>Solution:</b> OMNIX is Decision Governance Infrastructure that validates every automated decision "
        "through 6 independent checkpoints before execution, with a fail-closed architecture that defaults to "
        "protecting capital.",
        styles['BodyText2']
    ))
    elements.append(Paragraph(
        "<b>Target Customer:</b> B2B Institutional \u2014 Prop trading firms, algorithmic trading platforms, "
        "regulated funds, and lending/insurance automation systems globally. "
        "Future verticals: supply chain operators, robotics/autonomous physical systems (Year 3+).",
        styles['BodyText2']
    ))
    elements.append(Paragraph(
        "<b>Business Model:</b> B2B Decision Governance Licensing ($15K\u2013$35K/month per enterprise client) + "
        "per-validation pricing ($0.01\u2013$0.05/call) for high-volume platforms. Secondary B2C SaaS ($149\u2013$499/month).",
        styles['BodyText2']
    ))
    elements.append(Paragraph(
        "<b>Current Stage:</b> MVP (Live Product) \u2014 Running 24/7 in production since November 2025. "
        "728,868 shadow portfolio evaluations completed, 50,688 cryptographically signed governance receipts, "
        "100% post-quantum cryptography coverage.",
        styles['BodyText2']
    ))
    elements.append(Paragraph(
        "<b>Key Traction:</b> Eureka GCC 2026 Semifinalist. Live public verification system at "
        "omnixquantum.net/verify. Interactive governance demos for credit/lending "
        "and insurance underwriting verticals. Institutional website live at www.omnixquantum.net.",
        styles['BodyText2']
    ))

    elements.append(Spacer(1, 8))
    kpi_data = [
        ['728,868', 'Shadow Portfolio Evaluations', 'Governance engine operational 24/7'],
        ['50,688', 'PQC-Signed Receipts', '100% Dilithium-3 coverage'],
        ['98.5%', 'Capital Preserved', 'During BTC -7.37% volatility'],
        ['<120ms', 'Decision Latency', 'Real-time governance validation'],
        ['$49.7B+', 'Combined TAM', 'Multi-vertical addressable market (6 verticals)'],
    ]
    t = make_table(['Metric', 'Description', 'Context'], kpi_data, [90, 160, 210])
    elements.append(t)

    elements.append(PageBreak())
    return elements


def build_section_2(styles):
    elements = []
    elements.extend(section_header("Company Overview", "2", styles))

    elements.append(Paragraph("<b>Vision</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "To become the global standard for decision governance infrastructure in automated systems \u2014 "
        "ensuring that every high-stakes automated decision is validated, traceable, and accountable before execution.",
        styles['BodyText2']
    ))

    elements.append(Paragraph("<b>Business Description</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "OMNIX builds Decision Governance Infrastructure for automated systems. We provide a multi-layer "
        "pre-execution validation engine that governs decisions across domains where capital is at risk. "
        "Our 6-checkpoint architecture acts as an independent governance layer: it does not generate signals \u2014 "
        "it validates and governs them. The architecture is domain-agnostic, validated first in digital asset "
        "trading (the hardest domain due to 24/7 operation, high volatility, and zero circuit breakers), "
        "with expansion planned (Year 2\u20133+) into supply chain, credit/lending, insurance, energy trading, and robotics/autonomous systems.",
        styles['BodyText2']
    ))

    elements.append(Paragraph("<b>Product Description</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "OMNIX Decision Governance Engine is a real-time, AI-powered validation infrastructure that sits "
        "between decision systems and execution. Every decision passes through 6 independent checkpoints: "
        "Monte Carlo Validation, Risk Management System Limits, Adaptive Coherence Gate, Edge Confirmation "
        "Window, Weighted Scoring, and Final Decision. The system operates on a fail-closed principle \u2014 "
        "if any checkpoint raises concern, the decision is blocked. Every decision (executed or blocked) is "
        "cryptographically signed with NIST-standardized post-quantum algorithms (Dilithium-3) and stored "
        "with a full audit trail.",
        styles['BodyText2']
    ))

    elements.append(Paragraph("<b>Current Stage of Development</b>", styles['SubsectionTitle']))
    stage_data = [
        ['Component', 'Status'],
        ['Decision Governance Engine', 'Live \u2014 Production 24/7 since Nov 2025'],
        ['6-Checkpoint Validation', 'Live \u2014 All 6 checkpoints operational'],
        ['Post-Quantum Cryptography', 'Live \u2014 Dilithium-3 + Kyber-768 since Nov 2025'],
        ['Public Verification Server', 'Live \u2014 Public receipt verification endpoint'],
        ['Investor Dashboard', 'Live \u2014 14/14 widgets operational, real-time metrics'],
        ['Institutional Website', 'Live \u2014 www.omnixquantum.net'],
        ['Multi-Vertical Demos', 'Live \u2014 Credit/Lending + Insurance interactive demos'],
        ['Shadow Portfolio Analysis', 'Live \u2014 728,868 shadow portfolio evaluations'],
        ['Enterprise API', 'In Development \u2014 Q2 2026 target'],
    ]
    t_data = [[Paragraph(c, styles['TableCell']) for c in row] for row in stage_data]
    t_data[0] = [Paragraph(c, styles['TableHeader']) for c in stage_data[0]]
    t = Table(t_data, colWidths=[180, 280])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    for i in range(2, len(t_data), 2):
        t.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), TABLE_ALT_ROW)]))
    elements.append(t)

    elements.append(PageBreak())
    return elements


def build_section_3(styles):
    elements = []
    elements.extend(section_header("Problem & Market Opportunity", "3", styles))

    elements.append(Paragraph("<b>Problem Statement</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "Automated systems are increasingly making high-stakes decisions across multiple industries "
        "\u2014 from financial trading and credit approvals to supply chain procurement, insurance underwriting, "
        "and robotics/autonomous systems.",
        styles['BodyText2']
    ))
    elements.append(Paragraph(
        "However, most of these systems operate without a governance layer capable of validating decisions "
        "<i>before</i> execution. As a result, automated decisions can trigger cascading losses, operational "
        "disruptions, and regulatory risks at machine speed.",
        styles['BodyText2']
    ))
    elements.append(Paragraph(
        "Today, most systems focus on generating signals or optimizing performance. "
        "Very few focus on governing <b>whether a decision should actually be executed.</b>",
        styles['BodyText2']
    ))
    elements.extend(bullet_list([
        "<b>Billions in preventable losses annually</b> due to governance failures in automated decision systems",
        "<b>Machine-speed decisions without machine-speed governance</b> \u2014 humans cannot oversee decisions made in milliseconds",
        "<b>Single-layer risk checks fail</b> during tail events (flash crashes, liquidity cascades, model hallucinations)",
        "<b>No audit trail</b> for automated decisions, creating regulatory and compliance exposure",
        "<b>Institutional-grade governance</b> exists only inside the largest organizations \u2014 inaccessible to the rest of the market",
    ], styles))

    elements.append(Paragraph("<b>Examples of High-Risk Automated Decisions</b>", styles['SubsectionTitle']))
    elements.extend(bullet_list([
        "<b>Algorithmic trading</b> \u2014 executing large orders in volatile markets",
        "<b>Credit scoring systems</b> \u2014 approving or rejecting loans automatically",
        "<b>Supply chain systems</b> \u2014 triggering procurement decisions at scale",
        "<b>Insurance underwriting</b> \u2014 evaluating risk and setting premiums automatically",
        "<b>Robotics & autonomous systems</b> \u2014 executing real-world physical actions",
    ], styles))

    elements.append(Paragraph("<b>Existing Alternatives & Why They Are Inadequate</b>", styles['SubsectionTitle']))
    alt_data = [
        ['Alternative', 'Limitation', 'OMNIX Advantage'],
        ['Retail Trading Bots', 'No decision governance, single risk check', '6 independent checkpoint validation'],
        ['Quant Fund Tools', 'Minimum $10M+ capital, proprietary', 'Accessible infrastructure model'],
        ['Manual Oversight', 'Too slow for real-time (<120ms required)', 'Automated validation in <120ms'],
        ['Single-Domain Tools', 'Built for one industry only', 'Domain-agnostic governance engine'],
        ['Traditional Risk Systems', 'React after the fact', 'Pre-execution validation (fail-closed)'],
    ]
    elements.append(make_table(alt_data[0], alt_data[1:], [120, 170, 170]))

    elements.append(Paragraph("<b>Market Size</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "OMNIX addresses a multi-vertical market opportunity across decision governance for automated systems:",
        styles['BodyText2']
    ))
    market_data = [
        ['Vertical', 'Addressable Market', 'Timeline'],
        ['Digital Asset Trading (Current)', '$18.8B algorithmic trading', 'Now (Validated)'],
        ['Supply Chain Risk', '$3.2B supply chain analytics', 'Year 2\u20133'],
        ['Credit / Lending Governance', '$7.4B credit risk management', 'Year 2\u20133'],
        ['Insurance Underwriting', '$5.1B insurtech', 'Year 3+'],
        ['Energy Trading', '$2.8B energy risk management', 'Year 3+'],
        ['Robotics / Autonomous Systems', '$12.4B industrial robotics safety', 'Year 3+'],
        ['Combined TAM', '$49.7B+', 'Progressive'],
    ]
    elements.append(make_table(market_data[0], market_data[1:], [170, 160, 130]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("<b>Target Customer Segment</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "<b>Primary (80% focus):</b> B2B Institutional \u2014 prop trading firms, algorithmic trading platforms, "
        "regulated funds, lending automation platforms, and insurance underwriting systems globally.",
        styles['BodyText2']
    ))
    elements.append(Paragraph(
        "<b>Secondary (20%, post-enterprise validation):</b> B2C SaaS for advanced independent traders. "
        "<b>Regulatory tailwind:</b> MiCA (EU), EU AI Act, and global AI governance frameworks create "
        "immediate demand for auditable decision governance infrastructure.",
        styles['BodyText2']
    ))

    elements.append(Paragraph("<b>Expected Market Adoption</b>", styles['SubsectionTitle']))
    adoption_data = [
        ['Phase', 'Timeline', 'Target'],
        ['Enterprise Pilots', 'Months 1\u20136', '3 pilot agreements (prop firms/platforms)'],
        ['Paid Licenses', 'Months 6\u20139', '3 paying enterprise clients'],
        ['Regional Scale', 'Months 9\u201312', '$50K+ MRR, 15\u201330 clients in MENA'],
        ['Multi-Vertical', 'Year 2\u20133', 'Supply chain + lending governance pilots'],
        ['Global Scale', 'Year 3+', 'EU MiCA, Asia expansion'],
    ]
    elements.append(make_table(adoption_data[0], adoption_data[1:], [120, 120, 220]))

    elements.append(PageBreak())
    return elements


def build_section_4(styles):
    elements = []
    elements.extend(section_header("Customer Validation & Insights", "4", styles))

    elements.append(Paragraph("<b>Discovery Method</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "Market validation has been conducted through multiple channels: LinkedIn engagement with "
        "founders and architects building in adjacent spaces (AI governance, PQC, Zero Trust, autonomous systems), "
        "participation in the Eureka GCC competition (semifinalist status achieved), publication of the "
        "OMNIX technical paper on LinkedIn Pulse generating substantive expert responses, and live product "
        "demonstrations with the governance engine running in real-time production.",
        styles['BodyText2']
    ))

    elements.append(Paragraph("<b>Key Insights Learned</b>", styles['SubsectionTitle']))
    elements.extend(bullet_list([
        "<b>Governance, not alpha:</b> Institutional buyers care about decision accountability and audit trails, not signal generation",
        "<b>Compliance urgency:</b> MiCA regulation (2025+) creates immediate demand for decision governance documentation",
        "<b>Risk-first positioning resonates:</b> 'Preventing costly mistakes' is a stronger value proposition than 'maximizing returns'",
        "<b>Fail-closed architecture is differentiating:</b> Institutions value systems that default to protect over systems that default to act",
        "<b>Multi-vertical potential recognized:</b> The same governance engine logic applies to credit, insurance, supply chain, and robotics/autonomous systems decisions",
    ], styles))

    elements.append(Paragraph("<b>Willingness to Pay</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "Based on market research and competitive analysis of institutional risk infrastructure pricing:",
        styles['BodyText2']
    ))
    pricing_data = [
        ['Segment', 'Expected Price Range', 'Basis'],
        ['Prop Trading Firms', '$10K\u2013$15K/month (pilot)', 'Comparable to existing risk tools; drawdown prevention ROI 2\u20138x'],
        ['Trading Platforms', '$0.01\u2013$0.05/validation', 'Per-API-call model; volume-driven'],
        ['Regulated Funds', '$25K\u2013$35K/month', 'Audit trail + compliance documentation value'],
        ['B2C Advanced Traders', '$149\u2013$499/month', 'SaaS market benchmarks for institutional tools'],
    ]
    elements.append(make_table(pricing_data[0], pricing_data[1:], [120, 140, 200]))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>Market Validation \u2014 Expert & Peer Recognition</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "At pre-seed stage, validation from domain experts who independently reviewed the architecture "
        "and recognized its strategic direction is a strong signal of product-market fit. "
        "The following interactions were unsolicited or initiated by Harold via LinkedIn outreach, "
        "and resulted in substantive technical and strategic engagement:",
        styles['BodyText2']
    ))

    validation_data = [
        ['Name', 'Role', 'Channel', 'Key Feedback'],
        [
            'James Moore',
            'Founder/CEO, Nova Jema AI Systems\n(AI governance for healthcare & public infrastructure)',
            'LinkedIn\n(public comment)',
            '"Harold this is exactly the layer I\'ve been trying to articulate... Curious how OMNIX is approaching that boundary between recommendation and binding authority." — Identified the proposal-to-execution governance gap as the core structural challenge.'
        ],
        [
            'Mostafa Monsour',
            'Founder, ULTRA MATRIX\nCognitive & Strategic Architect — Sovereign Decision Design',
            'LinkedIn\n(public comment)',
            '"Your work with OMNIX Quantum appears to be exploring an important part of that stack." — Recognized OMNIX as addressing the authority + verification gap in autonomous systems.'
        ],
        [
            'HIL-AIW',
            'AI governance platform for enterprises\n(925+ LinkedIn followers)',
            'LinkedIn\n(public comment)',
            '"Your 8-checkpoint system with Monte Carlo VETO is brilliant — especially the fail-closed design... most teams aren\'t even thinking about quantum-resistant auditability yet." — Validated the fail-closed architecture and PQC approach as industry-leading.'
        ],
        [
            'Christopher Turk',
            'Quantum Security Architecture\nAgentic AI Security Architecture | Zero Trust Architecture',
            'LinkedIn\n(public comment + DM)',
            '"This is honestly pretty good." — Extended technical exchange on PQC architecture, Zero Trust applied to AI decisions, and decision provenance metadata model. Validated Dilithium-3 selection over Falcon for production stability.'
        ],
        [
            'Francisco Javier (JJ) Jimenez',
            'Founder, QuantumThreat Labs\nQuantum Temporal Dynamics\u2122 Research',
            'LinkedIn DM\n(paper review)',
            '"Governance infrastructure for autonomous systems is going to become increasingly important." — Read full OMNIX paper; his framing of probabilistic governance + trajectory coherence directly informed the design of OMNIX Checkpoint 7 (Temporal Coherence Validation, ADR-032).'
        ],
    ]
    elements.append(make_table(validation_data[0], validation_data[1:], [85, 120, 70, 185]))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Note: Public LinkedIn comments are cited as-is. JJ Jimenez interaction via private LinkedIn DM — "
        "permission confirmation in progress before final submission.",
        styles['SmallNote']
    ))

    elements.append(PageBreak())
    return elements


def build_section_5(styles):
    elements = []
    elements.extend(section_header("Product & Technology", "5", styles))

    elements.append(Paragraph("<b>Core Features Currently Built</b>", styles['SubsectionTitle']))

    features_data = [
        ['Feature', 'Status', 'Description'],
        ['6-Checkpoint Governance Engine', 'Live', 'Multi-layer pre-execution decision validation with independent veto authority per checkpoint'],
        ['Monte Carlo Validation', 'Live', '10,000 simulation paths per decision; blocks trades with negative expected return'],
        ['Adaptive Coherence Gate', 'Live', 'Dynamically calibrated signal agreement scoring based on market regime severity'],
        ['Edge Confirmation Window (ECW)', 'Live', 'Requires 2 consecutive cycles of confirmed statistical edge before execution'],
        ['Black Swan Detection', 'Live', 'Real-time tail risk monitoring with automatic exposure reduction (4 severity levels)'],
        ['Decision Contradiction Index (DCI)', 'Live', 'Measures internal signal divergence (0\u2013100); high DCI mandates HOLD'],
        ['Post-Quantum Cryptography', 'Live', 'NIST-standardized Dilithium-3 signatures + Kyber-768 key encapsulation'],
        ['Public Verification Server', 'Live', 'Public receipt verification endpoint with zero internal data exposure'],
        ['Shadow Portfolio Engine', 'Live', '728,868 shadow portfolio evaluations; veto accuracy 100% (50/50 validated outcomes, cross-referenced against 48h price action)'],
        ['Non-Markovian Memory Kernel', 'Live', 'Behavioral pattern detection beyond recency bias'],
        ['Multi-AI Orchestration', 'Live', 'Gemini 2.5 Flash + GPT-4o + Claude Sonnet 4 with automatic failover'],
        ['Investor Dashboard', 'Live', '14/14 widgets operational, real-time metrics, dual win rate framework, regime detection'],
        ['Institutional Website', 'Live', 'Public landing at www.omnixquantum.net with live market data integration'],
        ['Interactive Governance Demos', 'Live', 'Credit/Lending + Insurance underwriting demos showing multi-vertical applicability'],
        ['Execution Integrity', 'Live', 'Kraken fill reconciliation \u2014 real exchange data verification for every trade'],
        ['Mathematical Audit', 'Live', '100% P&L reconciliation (119/119 trades verified against exchange fees)'],
    ]
    elements.append(make_table(features_data[0], features_data[1:], [150, 35, 275]))

    elements.append(Paragraph("<b>What Is Live vs What Is Planned</b>", styles['SubsectionTitle']))
    roadmap_data = [
        ['Component', 'Status', 'Timeline'],
        ['Governance Engine (Digital Assets)', 'LIVE', 'Since Nov 2025'],
        ['PQC Decision Signing', 'LIVE', 'Since Nov 2025'],
        ['Public Verification System', 'LIVE', 'Since Feb 2026'],
        ['Enterprise API (Risk Guardian)', 'Planned', 'Q2 2026'],
        ['White-Label SDK', 'Planned', 'Q3 2026'],
        ['Supply Chain Domain Adapter', 'Planned', 'Year 2\u20133'],
        ['Credit/Lending Domain Adapter', 'Planned', 'Year 2\u20133'],
        ['Insurance Domain Adapter', 'Planned', 'Year 3+'],
        ['Robotics / Autonomous Systems Adapter', 'Planned', 'Year 3+'],
    ]
    elements.append(make_table(roadmap_data[0], roadmap_data[1:], [180, 60, 220]))

    elements.append(Paragraph("<b>Product Roadmap (Next 6\u201312 Months)</b>", styles['SubsectionTitle']))
    roadmap_items = [
        "<b>Q1 2026 (COMPLETED):</b> 30-day Official Track Record validated (Jan 15 \u2013 Feb 13, 2026). 0 trades executed, 4,173 execution vetoes + 149,799 shadow evaluations during Black Swan period. Institutional documentation finalized. Eureka GCC semifinalist confirmed. Phase 1 Gradual Activation started Feb 13.",
        "<b>Q2 2026:</b> Enterprise API launch (Risk Guardian API). First enterprise pilot (prop firm or trading platform). Legal & regulatory structure initiated.",
        "<b>Q3 2026:</b> Public license model launch. White-label SDK for platform integrations. Second and third enterprise clients.",
        "<b>Q4 2026:</b> Series A readiness with validated revenue metrics. Begin multi-vertical domain adapter development.",
    ]
    elements.extend(bullet_list(roadmap_items, styles))

    elements.append(Paragraph("<b>Technology Stack</b>", styles['SubsectionTitle']))
    tech_data = [
        ['Layer', 'Technology'],
        ['Language', 'Python 3.11 (core engine)'],
        ['Frontend', 'React 18 + TypeScript + Tailwind CSS + Vite'],
        ['Database', 'PostgreSQL (42+ tables, 90% FK coverage)'],
        ['Cache', 'Redis (state management, rate limiting)'],
        ['AI Models', 'Google Gemini 2.5 Flash, OpenAI GPT-4o, Anthropic Claude Sonnet 4'],
        ['Cryptography', 'CRYSTALS-Dilithium-3 (ML-DSA-65), CRYSTALS-Kyber-768 (ML-KEM-768)'],
        ['Infrastructure', 'Railway (production 24/7), Replit (development)'],
        ['Verification', 'aiohttp async server (port 8000), SHA-256 hash chain'],
        ['Architecture', 'Hexagonal (ports and adapters), 27 Architecture Decision Records'],
    ]
    elements.append(make_table(tech_data[0], tech_data[1:], [120, 340]))

    elements.append(Paragraph("<b>Key Technical or Execution Risks</b>", styles['SubsectionTitle']))
    risks = [
        "<b>Key-person dependency:</b> Solo founder. Mitigated by documented hexagonal architecture (27 ADRs, 2\u20133 week onboarding target). First 3 hires planned within Month 1\u20134 post-funding.",
        "<b>AI model dependency:</b> Reliance on third-party AI providers. Mitigated by multi-provider failover chain (Gemini \u2192 GPT-4o \u2192 Claude).",
        "<b>Market timing:</b> Enterprise sales cycles are 3\u20136 months. Conservative pipeline assumptions account for this.",
    ]
    elements.extend(bullet_list(risks, styles))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "<b>Demo Links:</b> Public verification: omnixquantum.net/verify | "
        "Website: www.omnixquantum.net | Credit governance demo: www.omnixquantum.net/governance-demo | "
        "Insurance governance demo: www.omnixquantum.net/governance-demo-insurance",
        styles['SmallNote']
    ))

    elements.append(PageBreak())
    return elements


def build_section_6(styles):
    elements = []
    elements.extend(section_header("Competitive Landscape & Differentiation", "6", styles))

    elements.append(Paragraph(
        "OMNIX operates in the decision governance infrastructure space, which is a new category. "
        "The closest comparisons come from adjacent markets:",
        styles['BodyText2']
    ))

    comp_data = [
        ['Competitor', 'Category', 'Decision Checkpoints', 'PQC Security', 'Multi-Vertical', 'Pricing'],
        ['3Commas', 'Trading Platform', '1 (basic SL/TP)', 'No', 'No', '$49\u2013$79/mo'],
        ['Gauntlet Networks', 'DeFi Risk', '2\u20133', 'No', 'DeFi only', 'Enterprise'],
        ['Chainalysis', 'Compliance', '0 (monitoring only)', 'No', 'Compliance only', '$100K+/yr'],
        ['Internal Quant Teams', 'Prop Funds', '2\u20134', 'Rare', 'No', '$1M+/yr team cost'],
        ['OMNIX', 'Decision Governance', '6 independent', 'Yes (NIST)', 'Yes (6+ verticals)', '$15K\u2013$35K/mo'],
    ]
    elements.append(make_table(comp_data[0], comp_data[1:], [85, 85, 85, 55, 65, 85]))

    elements.append(Paragraph("<b>Unique Selling Proposition (USP)</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "OMNIX is the first domain-agnostic Decision Governance Infrastructure with production-integrated "
        "post-quantum cryptography, 6 independent validation checkpoints, and a publicly verifiable decision "
        "audit trail. No competitor offers this combination.",
        styles['BodyText2']
    ))

    elements.append(Paragraph("<b>Why We Win</b>", styles['SubsectionTitle']))
    elements.append(Paragraph("<b>Today:</b>", styles['Highlight']))
    today_items = [
        "<b>Fail-closed by default:</b> Every other system defaults to execute. OMNIX defaults to protect.",
        "<b>Post-quantum security in production:</b> No competitor has PQC-signed decision receipts.",
        "<b>Full audit trail:</b> 50,688 governance receipts, publicly verifiable, zero information leakage.",
        "<b>Domain-agnostic architecture:</b> Same engine validates trading, credit, insurance, and robotics/autonomous systems decisions.",
    ]
    elements.extend(bullet_list(today_items, styles))

    elements.append(Paragraph("<b>At Scale:</b>", styles['Highlight']))
    scale_items = [
        "<b>Network effects:</b> More decisions governed = better calibration. Shadow Portfolio learns from every veto.",
        "<b>Multi-vertical expansion:</b> One architecture, multiple verticals (trading, supply chain, lending, insurance, energy, robotics). Each new domain increases TAM without rebuilding core.",
        "<b>Regulatory moat:</b> MiCA, EU AI Act, and emerging global compliance frameworks create demand for auditable decision governance.",
        "<b>Switching costs:</b> OMNIX embeds into execution flow \u2014 high switching cost once integrated.",
    ]
    elements.extend(bullet_list(scale_items, styles))

    elements.append(PageBreak())
    return elements


def build_section_7(styles):
    elements = []
    elements.extend(section_header("Business Model & Unit Economics", "7", styles))

    elements.append(Paragraph("<b>Revenue Model</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "OMNIX operates a dual revenue model: B2B Decision Governance Licensing (80% of revenue) "
        "and B2C SaaS (20%, post-enterprise validation).",
        styles['BodyText2']
    ))

    rev_data = [
        ['Product', 'Pricing', 'Target Customer'],
        ['Risk Guardian API', '$15K\u2013$35K/month', 'Prop firms, trading platforms'],
        ['White-Label Engine', '$100K+ setup + $20K/month', 'Exchanges, brokers'],
        ['Per-Validation API', '$0.01\u2013$0.05/call', 'High-volume platforms'],
        ['B2C Pro', '$149/month', 'Advanced independent traders'],
        ['B2C Advanced', '$499/month', 'Semi-professional traders, API access'],
    ]
    elements.append(make_table(rev_data[0], rev_data[1:], [140, 140, 180]))

    elements.append(Paragraph("<b>Pricing Strategy</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "Pricing is positioned below the cost of building proprietary risk governance internally "
        "($1M+ annually for a quant team) while delivering institutional-grade protection. "
        "Enterprise pilots begin at discounted rates ($10K\u2013$15K/month) with conversion to "
        "full pricing after validation period.",
        styles['BodyText2']
    ))
    elements.append(Paragraph(
        '"Institutions pay for what blocks bad decisions, not for alpha. '
        'License-based revenue. No tokens. No performance fees."',
        styles['Quote']
    ))

    elements.append(Paragraph("<b>Customer Acquisition Channels</b>", styles['SubsectionTitle']))
    channels = [
        "<b>Direct outreach:</b> 50 targeted contacts/month via LinkedIn + email (targeting 15 meetings/month)",
        "<b>Competition & accelerator network:</b> Eureka GCC, Hub71, and regional programs (5\u201310 warm intros/quarter)",
        "<b>Hub71:</b> Applied \u2014 pending response (3\u20135 qualified leads/quarter if accepted)",
        "<b>Industry events:</b> TOKEN2049 Dubai, FinTech Abu Dhabi, GITEX (10+ contacts/event)",
        "<b>Eureka GCC:</b> Competition exposure + judge network (immediate pipeline)",
    ]
    elements.extend(bullet_list(channels, styles))

    elements.append(Paragraph("<b>Unit Economics (Estimated)</b>", styles['SubsectionTitle']))
    econ_data = [
        ['Metric', 'Value', 'Basis'],
        ['CAC (Enterprise)', '$5,000\u2013$10,000', 'Direct sales, 3\u20136 month cycle, founder-led'],
        ['LTV (Enterprise)', '$180K\u2013$420K', '$15K\u2013$35K/month \u00d7 12-month minimum contract'],
        ['LTV/CAC Ratio', '18x\u201384x', 'Strong unit economics at enterprise tier'],
        ['CAC (B2C SaaS)', '$50\u2013$150', 'Content marketing + referral programs'],
        ['LTV (B2C SaaS)', '$1,788\u2013$5,988', '$149\u2013$499/month \u00d7 12-month avg retention'],
        ['Gross Margin', '83% (Y1) \u2192 86% (Y2\u2013Y5)', 'SaaS infrastructure model \u2014 low marginal cost per client'],
        ['Break-Even', 'Q4 2026 (Month 9\u201312)', 'Conservative estimate with $500K runway'],
    ]
    elements.append(make_table(econ_data[0], econ_data[1:], [120, 120, 220]))

    elements.append(PageBreak())
    return elements


def build_section_8(styles):
    elements = []
    elements.extend(section_header("Traction & Key Metrics", "8", styles))

    elements.append(Paragraph(
        "OMNIX has been running in production 24/7 since November 2025. The following metrics represent "
        "real system telemetry, not projections:",
        styles['BodyText2']
    ))

    traction_data = [
        ['Metric', 'Value', 'Significance'],
        ['Production Uptime', '24/7 since Nov 2025', 'System operational 4+ months continuously'],
        ['Shadow Portfolio Evaluations', '728,868', 'Total governance engine evaluations in production'],
        ['PQC-Signed Receipts', '50,688', 'Every decision signed with Dilithium-3 (100% coverage)'],
        ['Execution Vetoes (Track Record, first 12 days)', '4,173', 'Black Swan period Jan 15\u201327 \u2014 capital fully preserved'],
        ['Shadow Evaluations (Track Record, first 12 days)', '149,799', 'Counterfactual governance analysis during Black Swan'],
        ['Capital Preserved', '98.5%', 'During period when BTC dropped 7.37%'],
        ['Veto Accuracy', '100%', '50/50 validated outcomes confirmed correct (cross-referenced against 48h price action)'],
        ['Decision Latency', '<120ms', 'Real-time governance validation'],
        ['Database Tables', '42+', '90% foreign key coverage \u2014 institutional-grade data model'],
        ['Architecture Decisions', '27 ADRs', 'Documented engineering discipline'],
        ['Dashboard Widgets', '14/14', 'Full operational visibility'],
    ]
    elements.append(make_table(traction_data[0], traction_data[1:], [130, 110, 220]))

    elements.append(Paragraph("<b>Competition & Recognition</b>", styles['SubsectionTitle']))
    elements.extend(bullet_list([
        "<b>Eureka GCC 2026:</b> Semifinalist \u2014 competing in Abu Dhabi startup competition",
        "<b>Public verification:</b> Live at omnixquantum.net/verify",
        "<b>Institutional website:</b> Live at www.omnixquantum.net with real-time market data",
    ], styles))

    elements.append(Paragraph("<b>Key Learning Milestones</b>", styles['SubsectionTitle']))
    milestones_data = [
        ['Date', 'Milestone', 'Impact'],
        ['Nov 2025', 'PQC implemented (Dilithium-3 + Kyber-768)', 'Quantum-resistant decision signing operational'],
        ['Nov\u2013Dec 2025', 'Learning Baseline (119 trades)', 'System calibration, threshold discovery'],
        ['Jan 15, 2026', 'Official Track Record Day 1', 'Clean metrics from calibrated parameters'],
        ['Jan 21, 2026', 'Edge Confirmation Window + DCI', 'Capital patience + contradiction detection'],
        ['Jan 28, 2026', 'Institutional Website launched', 'Public credibility and demo capability'],
        ['Feb 13, 2026', '30-Day Track Record COMPLETED', '0 trades executed, 4,173 execution vetoes + 149,799 shadow evaluations, 98.5% capital preserved'],
        ['Feb 15, 2026', 'Multi-Vertical Demos (Credit + Insurance)', 'Domain-agnostic architecture demonstrated'],
        ['Feb 21, 2026', 'Public Verification Server', 'Transparent governance receipts'],
        ['Feb 23, 2026', 'Railway cost optimization (77% reduction)', 'Operational efficiency for scaling'],
        ['Feb 24, 2026', 'Execution Integrity v1', 'Kraken fill reconciliation \u2014 real exchange data verification'],
        ['Feb 24, 2026', 'Mathematical Audit', '119/119 trades P&L reconciled (100% accuracy)'],
    ]
    elements.append(make_table(milestones_data[0], milestones_data[1:], [70, 200, 190]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "Note: All metrics are from internal dataset, not externally audited. Evaluation cycles and receipts "
        "represent governance engine activity, not trading performance.",
        styles['SmallNote']
    ))

    elements.append(PageBreak())
    return elements


def build_section_9(styles):
    elements = []
    elements.extend(section_header("Go-To-Market Strategy", "9", styles))

    elements.append(Paragraph("<b>Customer Acquisition Strategy</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "OMNIX follows an enterprise-first go-to-market strategy, targeting institutional buyers "
        "globally where regulatory urgency (MiCA 2025+, EU AI Act) creates immediate demand "
        "for decision governance infrastructure.",
        styles['BodyText2']
    ))

    funnel_data = [
        ['Stage', 'Action', 'Timeline', 'Conv. Rate'],
        ['Awareness', '50 direct outreaches/month + event networking', 'Ongoing', '\u2014'],
        ['Assessment', 'Free governance health check for their system', 'Week 1\u20132', '30%'],
        ['Shadow Mode', 'OMNIX runs alongside their system (no execution)', '2\u20134 weeks', '60%'],
        ['Advisory Mode', 'OMNIX provides pre-execution recommendations', '2\u20134 weeks', '75%'],
        ['Enforcement', 'Full governance integration with veto authority', 'Ongoing', '80%'],
        ['Paid License', 'Monthly enterprise license', 'Month 3\u20136', '\u2014'],
    ]
    elements.append(make_table(funnel_data[0], funnel_data[1:], [80, 190, 80, 60]))

    elements.append(Paragraph("<b>Sales Cycle</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "Enterprise sales cycle: 3\u20136 months from first contact to paid license. "
        "The progressive onboarding model (Shadow \u2192 Advisory \u2192 Enforcement) reduces adoption risk "
        "and builds trust before requiring financial commitment. Founder-led sales during pre-seed phase.",
        styles['BodyText2']
    ))

    elements.append(Paragraph("<b>Key Partnerships (Target)</b>", styles['SubsectionTitle']))
    partners_data = [
        ['Partner Type', 'Target', 'Status'],
        ['Accelerator', 'Hub71 (UAE)', 'Applied \u2014 pending response'],
        ['Competition Network', 'Eureka GCC 2026', 'Semifinalist \u2014 active'],
        ['Technology', 'Cloud infrastructure (Railway)', 'Active'],
        ['AI Providers', 'Google, OpenAI, Anthropic', 'Active (multi-provider)'],
        ['Enterprise Targets', 'Prop firms, trading platforms globally', 'Outreach in progress'],
    ]
    elements.append(make_table(partners_data[0], partners_data[1:], [120, 170, 170]))

    elements.append(Paragraph("<b>Scaling Strategy Across Markets</b>", styles['SubsectionTitle']))
    scale_data = [
        ['Phase', 'Focus', 'Timeline'],
        ['Phase 1', 'Pilot validation \u2014 3 enterprise clients (digital assets)', 'Months 1\u20136'],
        ['Phase 2', 'Enterprise license expansion (MENA + EU) + platform partnerships', 'Months 6\u201312'],
        ['Phase 3', 'Multi-vertical expansion \u2014 supply chain, lending, robotics/autonomous systems', 'Months 12\u201324'],
        ['Phase 4', 'Global scaling (EU MiCA, Asia) + insurance, energy', 'Months 24\u201336'],
    ]
    elements.append(make_table(scale_data[0], scale_data[1:], [60, 280, 120]))

    elements.append(PageBreak())
    return elements


def build_section_10(styles):
    elements = []
    elements.extend(section_header("Team & Advisors", "10", styles))

    elements.append(Paragraph("<b>Founder</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "<b>Harold Nunes</b> \u2014 Founder &amp; CEO",
        styles['BodyText2']
    ))
    elements.extend(bullet_list([
        "Product architecture, risk logic design, and infrastructure development",
        "Built OMNIX end-to-end: from concept to production system running 24/7",
        "AI-augmented development methodology: one person with AI achieves the output of a 5-person team",
        "Deep domain expertise in algorithmic trading risk management, decision systems, and cryptographic security",
        "Designed the 6-checkpoint governance architecture, post-quantum integration, and multi-vertical domain adapter pattern",
    ], styles))

    elements.append(Paragraph("<b>Key Hires Planned (Post-Funding)</b>", styles['SubsectionTitle']))
    hires_data = [
        ['Role', 'Timeline', 'Purpose'],
        ['Senior Backend Engineer', 'Month 1\u20132', 'Enterprise API development, system scaling'],
        ['DevOps / Infrastructure', 'Month 2\u20133', 'Production reliability, deployment automation'],
        ['Business Development', 'Month 3\u20134', 'Enterprise sales, institutional ecosystem relationships'],
    ]
    elements.append(make_table(hires_data[0], hires_data[1:], [160, 100, 200]))

    elements.append(Paragraph("<b>Key-Person Risk Mitigation</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "The current key-person risk is acknowledged and actively mitigated:",
        styles['BodyText2']
    ))
    elements.extend(bullet_list([
        "<b>Documented architecture:</b> 27 Architecture Decision Records (ADRs), hexagonal architecture with clear module boundaries",
        "<b>Onboarding target:</b> 2\u20133 week onboarding for new engineers using existing documentation",
        "<b>Dependency reduction:</b> First 3 hires reduce founder dependency from 100% to ~30% by Month 4",
        "<b>IP protection:</b> IP assignment to company entity, key-person insurance, operational runbooks by Month 6",
    ], styles))

    elements.append(Paragraph("<b>Advisors</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "Advisory board is being assembled. The founder has worked with contract developers and "
        "infrastructure consultants during the development phase. Formal advisory relationships with "
        "ADGM ecosystem participants and fintech domain experts are targeted post-funding.",
        styles['BodyText2']
    ))

    elements.append(Paragraph("<b>Why This Team</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "OMNIX was built by a founder who understands both the technical complexity of multi-layer "
        "governance systems and the institutional requirements of regulated financial markets. "
        "The AI-augmented development model has enabled solo construction of a system that would "
        "typically require a 5-person engineering team \u2014 evidenced by 42+ database tables, 27 ADRs, "
        "728,868 shadow portfolio evaluations, and 4+ months of continuous production operation. Post-funding, "
        "the first hires are designed to eliminate key-person risk and accelerate enterprise sales.",
        styles['BodyText2']
    ))

    elements.append(PageBreak())
    return elements


def build_section_11(styles):
    elements = []
    elements.extend(section_header("Financials & Fundraising", "11", styles))

    elements.append(Paragraph("<b>5-Year Financial Projections</b>", styles['SubsectionTitle']))
    fin_data = [
        ['', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5'],
        ['Enterprise Clients', '2 pilots', '5\u20138 licenses', '15\u201320', '30\u201340', '50+'],
        ['B2C SaaS Users', '50\u2013100', '500\u20131,000', '2,000\u20135,000', '8,000+', '20,000+'],
        ['Revenue', '$300K', '$1.8M', '$5.5M', '$13M', '$26M'],
        ['Gross Margin', '83%', '86%', '86%', '86%', '85%'],
        ['Key Driver', 'Enterprise pilots', 'License expansion', 'Multi-vertical + SaaS', 'MENA scale', 'Global + robotics'],
    ]
    elements.append(make_table(fin_data[0], fin_data[1:], [90, 80, 85, 80, 75, 75]))

    elements.append(Paragraph("<b>Key Assumptions</b>", styles['SubsectionTitle']))
    elements.extend(bullet_list([
        "3 enterprise pilots secured within 6 months via competition network and direct enterprise outreach",
        "Average enterprise contract: $25K/month (mid-range of $15K\u2013$35K pricing)",
        "12-month minimum contract duration with 80% renewal rate",
        "B2C SaaS launched post-enterprise validation (Month 6\u20139)",
        "Infrastructure costs scale sub-linearly; gross margin 83% (Y1) expanding to 86% (Y2+)",
        "MiCA compliance urgency drives accelerated adoption in EU markets (Year 2+)",
    ], styles))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "<b>Break-even:</b> Q4 2026 (Month 9\u201312). "
        "<b>Series A:</b> $3.5M Q2 2027 at $18M pre-money. "
        "<b>Series B:</b> $12M Q1 2029 at $60M pre-money.",
        styles['SmallNote']
    ))

    elements.append(Paragraph("<b>Fundraising</b>", styles['SubsectionTitle']))
    raise_data = [
        ['Item', 'Details'],
        ['Raising', '$500,000 USD'],
        ['Equity', '16.7%'],
        ['Pre-Money Valuation', '$3M'],
        ['Funds Raised to Date', '$0 (bootstrapped)'],
        ['Instrument', 'Equity (pre-seed round)'],
    ]
    elements.append(make_table(raise_data[0], raise_data[1:], [160, 300]))

    elements.append(Paragraph("<b>Investor Returns (MOIC)</b>", styles['SubsectionTitle']))
    moic_data = [
        ['Scenario', 'Exit Year', 'Revenue at Exit', 'Valuation (5x Rev)', 'MOIC on $500K'],
        ['Conservative', 'Year 5', '$13M', '$65M', '14.7x'],
        ['Base Case', 'Year 5', '$26M', '$130M', '41x'],
        ['Optimistic', 'Year 5', '$52M', '$260M', '102x'],
    ]
    elements.append(make_table(moic_data[0], moic_data[1:], [80, 65, 90, 110, 115]))

    elements.append(Paragraph("<b>Valuation Justification</b>", styles['SubsectionTitle']))
    elements.extend(bullet_list([
        "<b>Working product in production:</b> 4+ months running 24/7 with real market data",
        "<b>Real validation data:</b> 728,868 shadow portfolio evaluations, 50,688 PQC-signed receipts",
        "<b>Defensible IP:</b> 6-checkpoint architecture + Shadow Portfolio engine + PQC integration",
        "<b>Strategic timing:</b> MiCA + EU AI Act + global AI governance regulation creating urgent demand for auditable decision infrastructure",
        "<b>Comparable:</b> Chainalysis raised at $4M pre-money at similar stage",
    ], styles))

    elements.append(Paragraph("<b>Use of Funds</b>", styles['SubsectionTitle']))
    funds_data = [
        ['Category', 'Allocation', 'Purpose'],
        ['Strategy & Risk Engine', '35%', 'Algorithm refinement, Shadow Portfolio expansion, enterprise API'],
        ['Legal & Regulatory Structure', '25%', 'Company formation, regulatory structure, compliance'],
        ['Enterprise Infrastructure', '20%', 'API for prop firms, security certifications, scaling'],
        ['Team & Operations', '15%', '2\u20133 key hires eliminating key-person risk (Month 1\u20134)'],
        ['Reserve', '5%', 'Contingency'],
    ]
    elements.append(make_table(funds_data[0], funds_data[1:], [150, 60, 250]))

    elements.append(PageBreak())
    return elements


def build_section_12(styles):
    elements = []
    elements.extend(section_header("Intellectual Property & Regulatory", "12", styles))

    elements.append(Paragraph("<b>Intellectual Property</b>", styles['SubsectionTitle']))
    elements.append(Paragraph(
        "OMNIX's intellectual property is embedded in its proprietary architecture and algorithms, "
        "not in traditional patents. The key defensible assets are:",
        styles['BodyText2']
    ))
    ip_data = [
        ['IP Asset', 'Description', 'Protection'],
        ['6-Checkpoint Governance Engine', 'Multi-layer pre-execution decision validation architecture', 'Trade secret + documented ADRs'],
        ['Adaptive Coherence Gate', 'Dynamic threshold calibration based on market regime', 'Proprietary algorithm'],
        ['Edge Confirmation Window', 'Statistical edge persistence validation (2-cycle)', 'Proprietary methodology'],
        ['Decision Contradiction Index', 'Internal signal divergence measurement (0\u2013100)', 'Proprietary metric'],
        ['Shadow Portfolio Engine', '728,868 shadow portfolio evaluations; 50 validated outcomes (100% accuracy)', 'Proprietary dataset + methodology'],
        ['Non-Markovian Memory Kernel', 'Behavioral pattern detection beyond recency bias', 'Proprietary algorithm'],
        ['PQC Integration Architecture', 'Production-integrated post-quantum decision signing', 'First-mover advantage'],
    ]
    elements.append(make_table(ip_data[0], ip_data[1:], [130, 190, 140]))

    elements.append(Paragraph(
        "Patent filing strategy will be evaluated post-funding with legal counsel. "
        "Current protection relies on trade secrets, first-mover advantage, and architectural complexity.",
        styles['SmallNote']
    ))

    elements.append(Paragraph("<b>Regulatory Framework</b>", styles['SubsectionTitle']))
    reg_data = [
        ['Framework', 'Status', 'Relevance'],
        ['MiCA (EU)', 'Creating demand', 'Decision governance documentation required for compliance'],
        ['EU AI Act', 'Creating demand', 'Mandatory human oversight + audit trails for high-risk AI systems'],
        ['GDPR', 'Controls aligned', 'Data protection and PII handling'],
        ['SOC 2 Principles', 'Aligned', 'Access control, audit logging, encryption'],
        ['MiFID II', 'Aligned', 'Decision auditability and traceability'],
        ['DORA', 'Aligned', 'Operational resilience and error isolation'],
    ]
    elements.append(make_table(reg_data[0], reg_data[1:], [120, 110, 230]))

    elements.append(Paragraph("<b>Compliance Risks & Mitigation</b>", styles['SubsectionTitle']))
    elements.extend(bullet_list([
        "<b>Regulatory classification:</b> OMNIX is infrastructure (not a financial product or fund). "
        "No asset custody, no investment advice, no token issuance.",
        "<b>Data residency:</b> PostgreSQL database with configurable deployment region. "
        "ADGM/DIFC data handling requirements addressed through cloud infrastructure selection.",
        "<b>Cryptographic compliance:</b> NIST-standardized algorithms (Dilithium-3, Kyber-768). "
        "No proprietary or unvetted cryptographic implementations.",
    ], styles))

    elements.append(PageBreak())
    return elements


def build_section_13(styles):
    elements = []
    elements.extend(section_header("Risks & Challenges", "13", styles))

    elements.append(Paragraph("<b>Top 3 Business Risks</b>", styles['SubsectionTitle']))

    risk1 = [
        Paragraph("<b>1. Key-Person Risk (HIGH)</b>", styles['BodyText2']),
        Paragraph(
            "OMNIX is currently built and operated by a solo founder. This creates dependency risk "
            "for investors and operational continuity.",
            styles['BodyText2']
        ),
        Paragraph(
            "<b>Mitigation:</b> Documented architecture (27 ADRs), hexagonal module design with clear boundaries, "
            "2\u20133 week onboarding target. First 3 hires (Month 1\u20134) reduce dependency from 100% to ~30%. "
            "IP assignment, key-person insurance, and operational runbooks by Month 6.",
            styles['BodyText2']
        ),
    ]
    elements.extend(risk1)

    risk2 = [
        Paragraph("<b>2. Enterprise Sales Cycle Risk (MEDIUM)</b>", styles['BodyText2']),
        Paragraph(
            "Enterprise sales cycles are typically 3\u20136 months. Delayed pilot agreements could "
            "impact runway and milestone timelines.",
            styles['BodyText2']
        ),
        Paragraph(
            "<b>Mitigation:</b> Progressive onboarding model (Shadow \u2192 Advisory \u2192 Enforcement) reduces "
            "adoption friction. ADGM/DIFC ecosystem provides warm introductions. MiCA compliance urgency "
            "accelerates decision-making. $500K runway provides 18\u201324 month operating buffer.",
            styles['BodyText2']
        ),
    ]
    elements.extend(risk2)

    risk3 = [
        Paragraph("<b>3. Market Timing Risk (MEDIUM)</b>", styles['BodyText2']),
        Paragraph(
            "Crypto market volatility could reduce institutional appetite for digital asset infrastructure "
            "during bear markets.",
            styles['BodyText2']
        ),
        Paragraph(
            "<b>Mitigation:</b> OMNIX is positioned as decision governance infrastructure, not a crypto product. "
            "The multi-vertical architecture (supply chain, lending, insurance, robotics/autonomous systems) reduces dependency on any single market. "
            "Bear markets actually increase demand for risk governance.",
            styles['BodyText2']
        ),
    ]
    elements.extend(risk3)

    elements.append(Paragraph("<b>Execution Challenges</b>", styles['SubsectionTitle']))
    elements.extend(bullet_list([
        "<b>Scaling from solo to team:</b> First hires must maintain code quality and architectural discipline. "
        "Hexagonal architecture and ADR documentation mitigate this.",
        "<b>Enterprise integration complexity:</b> Each client requires customized onboarding. "
        "Domain Adapter pattern standardizes this process.",
        "<b>AI provider reliability:</b> Multi-provider failover chain (Gemini \u2192 GPT-4o \u2192 Claude) "
        "ensures no single point of failure.",
    ], styles))

    elements.append(Paragraph("<b>Market & Regulatory Risks</b>", styles['SubsectionTitle']))
    elements.extend(bullet_list([
        "<b>Regulatory changes:</b> ADGM/DIFC regulations could shift. OMNIX's compliance-aligned architecture "
        "makes adaptation straightforward.",
        "<b>Competition from incumbents:</b> Large exchanges could build in-house governance. "
        "OMNIX's 4-month head start, PQC integration, and multi-vertical design (6+ verticals including robotics) create defensible position.",
        "<b>AI regulation:</b> Emerging AI governance regulations (EU AI Act) could affect multi-AI orchestration. "
        "OMNIX's transparent decision audit trail is aligned with explainability requirements.",
    ], styles))

    elements.append(PageBreak())
    return elements


def build_section_14(styles):
    elements = []
    elements.extend(section_header("Appendix", "14", styles))

    elements.append(Paragraph("<b>A. Architecture Overview</b>", styles['SubsectionTitle']))
    arch_text = """
    Decision Engine
        |
        +-- Signal Detection (EMA Regime, HMM, Kalman, Non-Markovian, Kelly)
        |
        +-- 6-Checkpoint Governance Flow:
        |       1. Monte Carlo VETO (10,000 simulations)
        |       2. RMS VETO (VaR95, drawdown limits)
        |       3. Adaptive Coherence Gate (dynamic thresholds)
        |       4. Edge Confirmation Window (2-cycle persistence)
        |       5. Weighted Scoring (5 inputs, 100 points)
        |       6. Final Decision (EXECUTE / HOLD / BLOCK)
        |
        +-- Post-Decision:
                +-- Dilithium-3 PQC Signature
                +-- SHA-256 Hash Chain
                +-- PostgreSQL Persistence
                +-- Public Verification Endpoint
    """
    arch_style = ParagraphStyle(
        'ArchCode', fontName='Courier', fontSize=8, leading=11,
        textColor=BRAND_DARK_TEXT, leftIndent=20, spaceAfter=12,
        backColor=HexColor('#F5F5F5'),
    )
    for line in arch_text.strip().split('\n'):
        elements.append(Paragraph(line.rstrip(), arch_style))

    elements.append(Paragraph("<b>B. Scoring Logic</b>", styles['SubsectionTitle']))
    scoring_data = [
        ['Input', 'Weight', 'Max Points'],
        ['EMA Regime Signal', '40%', '40 pts'],
        ['HMM Regime Detection', '25%', '25 pts'],
        ['Kalman Filter', '15%', '15 pts'],
        ['Non-Markovian Memory', '15%', '15 pts'],
        ['Kelly Criterion', '10%', '10 pts (sizing only)'],
    ]
    elements.append(make_table(scoring_data[0], scoring_data[1:], [170, 80, 80]))
    elements.append(Paragraph(
        "Separate Veto/Penalty layer (Monte Carlo, Black Swan, Sentiment, Quantum Momentum) applies only penalties \u2014 "
        "it cannot add positive score.",
        styles['SmallNote']
    ))

    elements.append(Paragraph("<b>C. Decision Receipt Example</b>", styles['SubsectionTitle']))
    receipt_example = [
        '{',
        '  "receipt_id": "RCP-2026022115...",',
        '  "timestamp": "2026-02-21T23:55:39Z",',
        '  "asset": "BTC/USD",',
        '  "decision": "HOLD",',
        '  "content_hash": "sha256:a7f3e2...",',
        '  "prev_hash": "sha256:8b4c1d... (truncated)",',
        '  "signature_algorithm": "Dilithium-3 (ML-DSA-65)",',
        '  "governance_gates": [',
        '    "MC_VETO", "RMS_CHECK", "COHERENCE_GATE",',
        '    "ECW_GATE", "SCORING", "FINAL_DECISION"',
        '  ]',
        '}',
    ]
    for line in receipt_example:
        elements.append(Paragraph(line, arch_style))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("<b>D. Links & Resources</b>", styles['SubsectionTitle']))
    links = [
        "<b>Website:</b> www.omnixquantum.net",
        "<b>Public Verification:</b> omnixquantum.net/verify",
        "<b>Credit Governance Demo:</b> www.omnixquantum.net/governance-demo",
        "<b>Insurance Governance Demo:</b> www.omnixquantum.net/governance-demo-insurance",
        "<b>LinkedIn:</b> linkedin.com/in/harold-nunes-21bb65285",
        "<b>Contact:</b> contacto@omnixquantum.net",
    ]
    elements.extend(bullet_list(links, styles))

    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_GOLD, spaceBefore=10, spaceAfter=10))
    elements.append(Paragraph(
        "OMNIX \u2014 Decision Governance Infrastructure for Automated Systems",
        ParagraphStyle('EndTag', fontName='Helvetica-Bold', fontSize=11, textColor=BRAND_NAVY, alignment=TA_CENTER)
    ))
    elements.append(Paragraph(
        '"When systems can act, but choose discipline."',
        ParagraphStyle('EndQuote', fontName='Helvetica-Oblique', fontSize=10, textColor=BRAND_GOLD, alignment=TA_CENTER, spaceAfter=6)
    ))
    elements.append(Paragraph(
        "Eureka GCC 2026 \u2014 Semifinalist | Abu Dhabi, UAE",
        ParagraphStyle('EndInfo', fontName='Helvetica', fontSize=9, textColor=BRAND_GRAY, alignment=TA_CENTER)
    ))
    elements.append(Paragraph(
        "All metrics from internal dataset, not externally audited. Past performance does not guarantee future results.",
        styles['SmallNote']
    ))

    return elements


def on_first_page(canvas, doc):
    draw_cover_background(canvas, doc)


def on_later_pages(canvas, doc):
    page_num = canvas.getPageNumber()

    canvas.saveState()
    canvas.setFillColor(BRAND_NAVY)
    canvas.rect(0, 0, A4[0], 25, fill=True, stroke=False)

    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(BRAND_GRAY)
    canvas.drawString(40, 10, "OMNIX \u2014 Decision Governance Infrastructure | Eureka GCC 2026 Semifinalist Report")
    canvas.drawRightString(A4[0] - 40, 10, f"Page {page_num}")

    canvas.setFillColor(BRAND_ACCENT)
    canvas.rect(0, A4[1] - 3, A4[0], 3, fill=True, stroke=False)

    canvas.restoreState()


def generate_report():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=40,
        title="OMNIX - Eureka GCC 2026 Semifinalist Report",
        author="Harold Nunes",
        subject="Decision Governance Infrastructure for Automated Systems",
        creator="OMNIX Report Generator",
    )

    styles = create_styles()
    elements = []

    elements.extend(build_cover_page())
    elements.extend(build_toc(styles))
    elements.extend(build_section_1(styles))
    elements.extend(build_section_2(styles))
    elements.extend(build_section_3(styles))
    elements.extend(build_section_4(styles))
    elements.extend(build_section_5(styles))
    elements.extend(build_section_6(styles))
    elements.extend(build_section_7(styles))
    elements.extend(build_section_8(styles))
    elements.extend(build_section_9(styles))
    elements.extend(build_section_10(styles))
    elements.extend(build_section_11(styles))
    elements.extend(build_section_12(styles))
    elements.extend(build_section_13(styles))
    elements.extend(build_section_14(styles))

    doc.build(elements, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    print(f"Report generated: {OUTPUT_FILE}")
    print(f"File size: {os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB")
    return OUTPUT_FILE


if __name__ == '__main__':
    generate_report()
