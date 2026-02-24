#!/usr/bin/env python3
"""
OMNIX Mentor Document Package Generator
Generates personalized PDFs for mentors:
1. Business Model Canvas
2. Pitch Deck (condensed)
3. Investor Report (full Eureka)
"""

import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, ListFlowable, ListItem, Frame
)
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF

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

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

MENTORS = [
    {"name": "Mr. Agarwal", "filename_suffix": "Agarwal"},
    {"name": "Darpan Salunkhe", "filename_suffix": "Salunkhe"},
]


def create_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CoverTitle', fontName='Helvetica-Bold', fontSize=36, leading=42,
        textColor=white, alignment=TA_LEFT, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name='CoverSubtitle', fontName='Helvetica', fontSize=16, leading=22,
        textColor=HexColor('#B0C4DE'), alignment=TA_LEFT, spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name='CoverTagline', fontName='Helvetica-Oblique', fontSize=13, leading=18,
        textColor=BRAND_GOLD, alignment=TA_LEFT, spaceAfter=30,
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle', fontName='Helvetica-Bold', fontSize=20, leading=26,
        textColor=BRAND_NAVY, spaceBefore=24, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name='SubsectionTitle', fontName='Helvetica-Bold', fontSize=14, leading=18,
        textColor=BRAND_BLUE, spaceBefore=16, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name='BodyText2', fontName='Helvetica', fontSize=10, leading=14,
        textColor=BRAND_DARK_TEXT, alignment=TA_JUSTIFY, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name='Quote', fontName='Helvetica-Oblique', fontSize=11, leading=15,
        textColor=BRAND_BLUE, leftIndent=20, rightIndent=20,
        spaceBefore=8, spaceAfter=12, borderWidth=2,
        borderColor=BRAND_ACCENT, borderPadding=10,
    ))
    styles.add(ParagraphStyle(
        name='FooterText', fontName='Helvetica', fontSize=7, leading=9,
        textColor=BRAND_GRAY, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='TableHeader', fontName='Helvetica-Bold', fontSize=9, leading=12,
        textColor=white, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name='TableCell', fontName='Helvetica', fontSize=9, leading=12,
        textColor=BRAND_DARK_TEXT, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name='SmallNote', fontName='Helvetica', fontSize=8, leading=10,
        textColor=BRAND_GRAY, alignment=TA_LEFT, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='BulletItem', fontName='Helvetica', fontSize=10, leading=14,
        textColor=BRAND_DARK_TEXT, leftIndent=20, bulletIndent=10, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='Highlight', fontName='Helvetica-Bold', fontSize=10, leading=14,
        textColor=BRAND_ACCENT, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name='CanvasHeader', fontName='Helvetica-Bold', fontSize=9, leading=11,
        textColor=white, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='CanvasCell', fontName='Helvetica', fontSize=7.5, leading=10,
        textColor=BRAND_DARK_TEXT, alignment=TA_LEFT, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name='CanvasBullet', fontName='Helvetica', fontSize=7, leading=9,
        textColor=BRAND_DARK_TEXT, leftIndent=8, spaceAfter=1,
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


def draw_cover_landscape(canvas, doc):
    w, h = landscape(A4)
    canvas.saveState()
    canvas.setFillColor(BRAND_NAVY)
    canvas.rect(0, 0, w, h, fill=True, stroke=False)
    canvas.setFillColor(BRAND_GOLD)
    canvas.rect(0, h - 60, w, 4, fill=True, stroke=False)
    canvas.rect(0, 40, w, 2, fill=True, stroke=False)
    canvas.restoreState()


def on_later_pages(canvas, doc):
    page_num = canvas.getPageNumber()
    canvas.saveState()
    canvas.setFillColor(BRAND_NAVY)
    canvas.rect(0, 0, A4[0], 25, fill=True, stroke=False)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(BRAND_GRAY)
    canvas.drawString(40, 10, "OMNIX \u2014 Decision Governance Infrastructure")
    canvas.drawRightString(A4[0] - 40, 10, f"Page {page_num}")
    canvas.setFillColor(BRAND_ACCENT)
    canvas.rect(0, A4[1] - 3, A4[0], 3, fill=True, stroke=False)
    canvas.restoreState()


def on_later_pages_landscape(canvas, doc):
    w, h = landscape(A4)
    page_num = canvas.getPageNumber()
    canvas.saveState()
    canvas.setFillColor(BRAND_NAVY)
    canvas.rect(0, 0, w, 20, fill=True, stroke=False)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(BRAND_GRAY)
    canvas.drawString(30, 6, "OMNIX \u2014 Business Model Canvas")
    canvas.drawRightString(w - 30, 6, f"Page {page_num}")
    canvas.setFillColor(BRAND_ACCENT)
    canvas.rect(0, h - 3, w, 3, fill=True, stroke=False)
    canvas.restoreState()


# ============================================================
# BUSINESS MODEL CANVAS
# ============================================================

def generate_canvas(mentor_name, output_path):
    s = create_styles()
    w, h = landscape(A4)

    doc = SimpleDocTemplate(
        output_path, pagesize=landscape(A4),
        rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=30,
        title="OMNIX - Business Model Canvas",
        author="Harold Nunes",
    )

    elements = []

    elements.append(Spacer(1, 80))
    elements.append(Paragraph("OMNIX", s['CoverTitle']))
    elements.append(Paragraph("Business Model Canvas", s['CoverSubtitle']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph('"Decision Governance Infrastructure for Automated Systems"', s['CoverTagline']))
    elements.append(Spacer(1, 30))
    info_style = ParagraphStyle(
        'CoverInfo', fontName='Helvetica', fontSize=11, leading=16,
        textColor=HexColor('#B0C4DE'), alignment=TA_LEFT
    )
    elements.append(Paragraph(f"Prepared for: {mentor_name}", info_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Founder &amp; CEO: Harold Nunes", info_style))
    elements.append(Paragraph("Eureka! GCC 2026 \u2014 Semifinalist", info_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("contacto@omnixquantum.net | www.omnixquantum.net", info_style))
    elements.append(Spacer(1, 30))
    date_style = ParagraphStyle(
        'CoverDate', fontName='Helvetica', fontSize=9, leading=12,
        textColor=BRAND_GOLD, alignment=TA_LEFT
    )
    elements.append(Paragraph(f"March 2026 | Abu Dhabi, UAE", date_style))
    elements.append(Paragraph("Classification: Confidential \u2014 Mentor Review", date_style))
    elements.append(PageBreak())

    hdr = ParagraphStyle('BMCHdr', fontName='Helvetica-Bold', fontSize=8, leading=10,
                         textColor=white, alignment=TA_CENTER)
    cell = ParagraphStyle('BMCCell', fontName='Helvetica', fontSize=7, leading=9,
                          textColor=BRAND_DARK_TEXT, alignment=TA_LEFT, spaceAfter=1)
    cell_b = ParagraphStyle('BMCBold', fontName='Helvetica-Bold', fontSize=7, leading=9,
                            textColor=BRAND_BLUE, alignment=TA_LEFT, spaceAfter=2)

    def bmc_cell(title_text, items):
        content = [Paragraph(f"<b>{title_text}</b>", cell_b)]
        for item in items:
            content.append(Paragraph(f"\u2022 {item}", cell))
        return content

    kp = bmc_cell("KEY PARTNERS", [
        "ADGM/DIFC regulatory ecosystem",
        "Hub71 accelerator (applied)",
        "AI providers: Google, OpenAI, Anthropic",
        "Cloud: Railway (production 24/7)",
        "Exchange APIs: Kraken, Alpaca",
        "NIST PQC standards body",
    ])
    ka = bmc_cell("KEY ACTIVITIES", [
        "6-checkpoint governance engine R&D",
        "Enterprise API development",
        "Multi-vertical domain adapter design",
        "Shadow Portfolio counterfactual analysis",
        "PQC receipt signing (Dilithium-3)",
        "Regulatory compliance alignment",
        "Execution integrity validation",
    ])
    kr = bmc_cell("KEY RESOURCES", [
        "Proprietary 6-checkpoint architecture",
        "670,000+ evaluation cycles dataset",
        "16,000+ PQC-signed governance receipts",
        "27 Architecture Decision Records",
        "Hexagonal codebase (42+ DB tables)",
        "Shadow Portfolio engine",
        "Solo founder: Harold Nunes",
    ])
    vp = bmc_cell("VALUE PROPOSITIONS", [
        "Pre-execution decision governance (fail-closed)",
        "6 independent validation checkpoints",
        "PQC-signed audit trail (NIST-standardized)",
        "Domain-agnostic: trading, supply chain, lending, insurance, energy, robotics",
        "Real-time validation (<120ms latency)",
        "Capital preservation (98.5% during BTC -7.37%)",
        "Publicly verifiable governance receipts",
        "Mathematical audit: 100% P&L reconciliation",
    ])
    cr = bmc_cell("CUSTOMER RELATIONSHIPS", [
        "Enterprise-first, founder-led sales",
        "Progressive onboarding: Shadow \u2192 Advisory \u2192 Enforcement",
        "Live verification system (public)",
        "Interactive governance demos (credit, insurance)",
        "24/7 operational monitoring",
        "Institutional dashboard (19 widgets)",
    ])
    ch = bmc_cell("CHANNELS", [
        "ADGM/DIFC direct outreach (50/month)",
        "Eureka GCC 2026 (Semifinalist)",
        "Hub71 accelerator program",
        "Industry events: TOKEN2049, GITEX, FinTech Abu Dhabi",
        "LinkedIn + content marketing",
        "Public verification server",
        "Institutional website: omnixquantum.net",
    ])
    cs = bmc_cell("CUSTOMER SEGMENTS", [
        "<b>Primary (B2B - 80%):</b>",
        "Prop trading firms (ADGM/DIFC: 200+)",
        "Trading platforms & exchanges",
        "Regulated funds & family offices",
        "<b>Secondary (B2C - 20%):</b>",
        "Advanced independent traders",
        "<b>Future verticals (Year 2-3+):</b>",
        "Supply chain, credit/lending, insurance, energy, robotics/autonomous systems",
    ])
    cost = bmc_cell("COST STRUCTURE", [
        "AI API costs (Gemini, GPT-4o, Claude)",
        "Cloud infrastructure (Railway, Redis, PostgreSQL)",
        "Market data feeds (Kraken, Alpaca, Finnhub)",
        "Regulatory & legal (ADGM formation)",
        "Team: 3 key hires post-funding (Month 1-4)",
        "Break-even target: 18-24 months",
    ])
    rev = bmc_cell("REVENUE STREAMS", [
        "<b>B2B Enterprise Licenses:</b> $15K-$35K/month",
        "<b>Per-Validation API:</b> $0.01-$0.05/call",
        "<b>White-Label Engine:</b> $100K+ setup + $20K/month",
        "<b>B2C Pro SaaS:</b> $149/month",
        "<b>B2C Advanced SaaS:</b> $499/month",
        "LTV/CAC ratio: 18x-84x (enterprise)",
        "Target Year 1 revenue: $200K-$400K",
    ])

    col_w = (w - 60) / 5

    top_row_h = 220
    bot_row_h = 120

    def cell_table(content_list, width, height):
        t = Table([[content_list]], colWidths=[width - 4], rowHeights=[height])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return t

    def header_cell(text, width):
        t = Table([[Paragraph(text, hdr)]], colWidths=[width - 4], rowHeights=[18])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), TABLE_HEADER_BG),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        return t

    title_style = ParagraphStyle('CanvasTitle', fontName='Helvetica-Bold', fontSize=16,
                                 leading=20, textColor=BRAND_NAVY, alignment=TA_CENTER, spaceAfter=4)
    subtitle_style = ParagraphStyle('CanvasSub', fontName='Helvetica', fontSize=10,
                                    leading=14, textColor=BRAND_GRAY, alignment=TA_CENTER, spaceAfter=20)

    elements.append(Paragraph("OMNIX \u2014 Business Model Canvas", title_style))
    elements.append(Paragraph("Decision Governance Infrastructure for Automated Systems", subtitle_style))

    canvas_data = [
        [
            [header_cell("KEY PARTNERS", col_w)] + kp,
            [header_cell("KEY ACTIVITIES", col_w)] + ka + [Spacer(1, 10), header_cell("KEY RESOURCES", col_w)] + kr,
            [header_cell("VALUE PROPOSITIONS", col_w)] + vp,
            [header_cell("CUSTOMER RELATIONSHIPS", col_w)] + cr + [Spacer(1, 10), header_cell("CHANNELS", col_w)] + ch,
            [header_cell("CUSTOMER SEGMENTS", col_w)] + cs,
        ],
    ]

    main_table = Table(canvas_data, colWidths=[col_w]*5, rowHeights=[340])
    main_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, BRAND_BLUE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHT),
        ('BACKGROUND', (2, 0), (2, 0), HexColor('#E8F4FD')),
    ]))
    elements.append(main_table)

    elements.append(Spacer(1, 4))

    bottom_data = [
        [
            [header_cell("COST STRUCTURE", col_w * 2.5)] + cost,
            [header_cell("REVENUE STREAMS", col_w * 2.5)] + rev,
        ]
    ]
    bottom_table = Table(bottom_data, colWidths=[col_w * 2.5, col_w * 2.5], rowHeights=[140])
    bottom_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, BRAND_BLUE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHT),
    ]))
    elements.append(bottom_table)

    elements.append(Spacer(1, 8))
    footer_note = ParagraphStyle('CanvasFooter', fontName='Helvetica', fontSize=7,
                                 leading=9, textColor=BRAND_GRAY, alignment=TA_CENTER)
    elements.append(Paragraph(
        "OMNIX \u2014 Eureka GCC 2026 Semifinalist | Pre-Seed: $500K @ $2.5M-$3M valuation (16.7% equity) | "
        "All metrics from internal dataset, not externally audited | Abu Dhabi, UAE",
        footer_note
    ))

    elements.append(PageBreak())

    elements.append(Paragraph("Key Metrics & Validation", title_style))
    elements.append(Spacer(1, 12))

    metrics_data = [
        ['Metric', 'Value', 'Significance'],
        ['Production Uptime', '24/7 since Nov 2025', '4+ months continuous operation'],
        ['Evaluation Cycles', '670,000+', 'Governance engine processing decisions in real-time'],
        ['PQC-Signed Receipts', '16,000+', '100% Dilithium-3 coverage (NIST-standardized)'],
        ['Capital Preserved', '98.5%', 'During period when BTC dropped 7.37%'],
        ['Shadow Trade Events', '670,000+', 'Counterfactual analysis of vetoed decisions'],
        ['Decision Latency', '<120ms', 'Real-time governance validation'],
        ['P&L Reconciliation', '100%', '119/119 trades mathematically audited'],
        ['Execution Integrity', 'Kraken-verified', 'Real fill data from exchange (not estimated)'],
        ['Database Tables', '42+', '90% foreign key coverage'],
        ['Architecture Decisions', '27 ADRs', 'Documented engineering discipline'],
        ['Combined TAM', '$49.7B+', '6 verticals: trading, supply chain, lending, insurance, energy, robotics'],
    ]
    metrics_t = make_table(metrics_data[0], metrics_data[1:], [130, 130, 300])
    elements.append(metrics_t)

    elements.append(Spacer(1, 16))
    elements.append(Paragraph("Fundraising Summary", ParagraphStyle(
        'FundTitle', fontName='Helvetica-Bold', fontSize=14, leading=18,
        textColor=BRAND_NAVY, alignment=TA_CENTER, spaceAfter=8)))

    fund_data = [
        ['Item', 'Details'],
        ['Raising', '$500,000 USD (Pre-Seed)'],
        ['Equity', '16.7%'],
        ['Pre-Money Valuation', '$2.5M\u2013$3M'],
        ['Funds Raised to Date', '$0 (bootstrapped)'],
        ['Stage', 'MVP (Live Product, 24/7 production)'],
        ['Competition', 'Eureka GCC 2026 \u2014 Semifinalist'],
        ['Runway', '18+ months to Series A'],
    ]
    fund_t = make_table(fund_data[0], fund_data[1:], [180, 380])
    elements.append(fund_t)

    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        "All metrics from internal dataset, not externally audited. Past performance does not guarantee future results.",
        footer_note
    ))

    doc.build(elements, onFirstPage=draw_cover_landscape, onLaterPages=on_later_pages_landscape)
    print(f"  Canvas generated: {output_path}")
    return output_path


# ============================================================
# PITCH DECK (PDF)
# ============================================================

def generate_pitch_deck(mentor_name, output_path):
    s = create_styles()

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=40,
        title="OMNIX - Pitch Deck",
        author="Harold Nunes",
    )

    elements = []

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
    elements.append(Paragraph(f"Prepared for: {mentor_name}", info_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Founder &amp; CEO: Harold Nunes", info_style))
    elements.append(Paragraph("Eureka! GCC 2026 \u2014 Semifinalist", info_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Pre-Seed Round: $500,000 USD", info_style))
    elements.append(Paragraph("Valuation: $2.5M\u2013$3M | Equity: 16.7%", info_style))
    elements.append(Spacer(1, 30))
    contact_style = ParagraphStyle(
        'CoverContact', fontName='Helvetica', fontSize=9, leading=13,
        textColor=HexColor('#8899AA'), alignment=TA_LEFT
    )
    elements.append(Paragraph("contacto@omnixquantum.net | www.omnixquantum.net", contact_style))
    elements.append(Paragraph("linkedin.com/in/harold-nunes-21bb65285", contact_style))
    elements.append(Spacer(1, 30))
    date_style = ParagraphStyle(
        'CoverDate', fontName='Helvetica', fontSize=9, leading=12,
        textColor=BRAND_GOLD, alignment=TA_LEFT
    )
    elements.append(Paragraph("March 2026 | Abu Dhabi, UAE", date_style))
    elements.append(Paragraph("Classification: Confidential \u2014 Mentor Review", date_style))
    elements.append(PageBreak())

    # --- SLIDE 1: Problem ---
    elements.extend(section_header("The Problem", "1", s))
    elements.append(Paragraph(
        "High-stakes automated decision systems \u2014 from trading to supply chain to lending \u2014 "
        "lack institutional-grade governance infrastructure, leading to billions in preventable losses annually.",
        s['BodyText2']
    ))
    elements.extend(bullet_list([
        "<b>$68B+ lost annually</b> by traders due to undisciplined decision-making",
        "<b>95% of algorithmic systems</b> ask 'When should I act?' instead of 'When should I NOT act?'",
        "<b>Single-layer risk checks</b> fail during tail events (flash crashes, liquidity cascades)",
        "<b>No audit trail</b> for automated decisions \u2014 regulatory and compliance gaps",
        "<b>Institutional-grade governance</b> exists only inside hedge funds with $100M+ AUM",
    ], s))
    elements.append(PageBreak())

    # --- SLIDE 2: Solution ---
    elements.extend(section_header("Our Solution", "2", s))
    elements.append(Paragraph(
        "OMNIX is Decision Governance Infrastructure that validates every automated decision "
        "through 6 independent checkpoints before execution, with a fail-closed architecture "
        "that defaults to protecting capital.",
        s['BodyText2']
    ))
    sol_data = [
        ['Checkpoint', 'Function'],
        ['1. Monte Carlo Validation', '10,000 simulation paths; blocks negative expected return'],
        ['2. RMS VETO', 'VaR95, drawdown limits, portfolio risk boundaries'],
        ['3. Adaptive Coherence Gate', 'Dynamic signal agreement scoring by market regime'],
        ['4. Edge Confirmation Window', 'Requires 3 consecutive cycles of confirmed statistical edge'],
        ['5. Weighted Scoring', '5 inputs, 100 points (EMA, HMM, Kalman, Memory, Kelly)'],
        ['6. Final Decision', 'EXECUTE only if all gates pass; otherwise HOLD/BLOCK'],
    ]
    elements.append(make_table(sol_data[0], sol_data[1:], [160, 300]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "Every decision (executed or blocked) is cryptographically signed with NIST-standardized "
        "post-quantum algorithms (Dilithium-3) and stored with a full audit trail.",
        s['BodyText2']
    ))
    elements.append(PageBreak())

    # --- SLIDE 3: Traction & Metrics ---
    elements.extend(section_header("Traction & Key Metrics", "3", s))
    elements.append(Paragraph(
        "OMNIX has been running in production 24/7 since November 2025. All metrics represent "
        "real system telemetry, not projections:",
        s['BodyText2']
    ))
    traction_data = [
        ['Metric', 'Value', 'Context'],
        ['Production Uptime', '24/7 since Nov 2025', '4+ months continuous operation'],
        ['Evaluation Cycles', '670,000+', 'Governance engine operational in real-time'],
        ['PQC-Signed Receipts', '16,000+', '100% Dilithium-3 coverage'],
        ['Capital Preserved', '98.5%', 'During BTC -7.37% volatility'],
        ['Decision Latency', '<120ms', 'Real-time governance validation'],
        ['P&L Reconciliation', '100%', 'Mathematical audit: 119/119 trades verified'],
        ['Execution Integrity', 'Kraken-verified', 'Real exchange fill data, not estimated'],
        ['Combined TAM', '$49.7B+', '6 verticals addressable'],
    ]
    elements.append(make_table(traction_data[0], traction_data[1:], [120, 120, 220]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "Note: All metrics from internal dataset, not externally audited. Evaluation cycles represent "
        "governance engine activity.",
        s['SmallNote']
    ))
    elements.append(PageBreak())

    # --- SLIDE 4: Technology ---
    elements.extend(section_header("Product & Technology", "4", s))
    features_data = [
        ['Feature', 'Status', 'Description'],
        ['6-Checkpoint Governance', 'Live', 'Multi-layer pre-execution decision validation'],
        ['Post-Quantum Cryptography', 'Live', 'NIST-standardized Dilithium-3 + Kyber-768 (since Nov 2025)'],
        ['Public Verification Server', 'Live', 'Receipt verification with zero internal data exposure'],
        ['Shadow Portfolio Engine', 'Live', '670,000+ counterfactual events; veto accuracy validation'],
        ['Execution Integrity', 'Live', 'Kraken fill reconciliation; real exchange data verification'],
        ['Multi-AI Orchestration', 'Live', 'Gemini 2.5 Flash + GPT-4o + Claude with failover'],
        ['Investor Dashboard', 'Live', '19 widgets, real-time metrics, dual win rate framework'],
        ['Interactive Demos', 'Live', 'Credit/Lending + Insurance governance demos'],
        ['Enterprise API', 'Planned', 'Risk Guardian API (Q2 2026)'],
    ]
    elements.append(make_table(features_data[0], features_data[1:], [140, 40, 280]))
    elements.append(Spacer(1, 8))
    tech_data = [
        ['Layer', 'Technology'],
        ['Core Engine', 'Python 3.11 | Hexagonal architecture | 42+ DB tables'],
        ['Frontend', 'React 18 + TypeScript + Tailwind CSS + Vite'],
        ['Database', 'PostgreSQL (90% FK coverage) + Redis'],
        ['AI Models', 'Google Gemini 2.5 Flash, OpenAI GPT-4o, Anthropic Claude'],
        ['Cryptography', 'Dilithium-3 (ML-DSA-65) + Kyber-768 (ML-KEM-768)'],
        ['Infrastructure', 'Railway (production 24/7), Replit (development)'],
    ]
    elements.append(make_table(tech_data[0], tech_data[1:], [110, 350]))
    elements.append(PageBreak())

    # --- SLIDE 5: Market Opportunity ---
    elements.extend(section_header("Market Opportunity", "5", s))
    market_data = [
        ['Vertical', 'Addressable Market', 'Timeline'],
        ['Digital Asset Trading', '$18.8B algorithmic trading', 'Now (Validated)'],
        ['Supply Chain Risk', '$3.2B supply chain analytics', 'Year 2\u20133'],
        ['Credit / Lending Governance', '$7.4B credit risk management', 'Year 2\u20133'],
        ['Insurance Underwriting', '$5.1B insurtech', 'Year 3+'],
        ['Energy Trading', '$2.8B energy risk management', 'Year 3+'],
        ['Robotics / Autonomous Systems', '$12.4B industrial robotics safety', 'Year 3+'],
        ['Combined TAM', '$49.7B+', 'Progressive'],
    ]
    elements.append(make_table(market_data[0], market_data[1:], [170, 170, 120]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("<b>Target Geography:</b> ADGM/DIFC (Abu Dhabi/Dubai) \u2014 200+ prop trading firms, "
        "100+ regulated funds. Expansion: EU (MiCA), Asia-Pacific (Year 2\u20133).", s['BodyText2']))
    elements.append(PageBreak())

    # --- SLIDE 6: Competitive Landscape ---
    elements.extend(section_header("Competitive Advantage", "6", s))
    comp_data = [
        ['Feature', 'OMNIX', '3Commas', 'Gauntlet', 'Internal Quant'],
        ['Decision Checkpoints', '6 independent', '1 (SL/TP)', '2\u20133', '2\u20134'],
        ['PQC Security', 'Yes (NIST)', 'No', 'No', 'Rare'],
        ['Multi-Vertical', '6+ verticals', 'No', 'DeFi only', 'No'],
        ['Audit Trail', '16,000+ receipts', 'No', 'Limited', 'Proprietary'],
        ['Fail-Closed', 'Yes (default)', 'No', 'No', 'Variable'],
        ['Public Verification', 'Live', 'No', 'No', 'No'],
        ['Pricing', '$15K\u2013$35K/mo', '$49\u2013$79/mo', 'Enterprise', '$1M+/yr team'],
    ]
    elements.append(make_table(comp_data[0], comp_data[1:], [110, 90, 80, 80, 100]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "<b>USP:</b> First domain-agnostic Decision Governance Infrastructure with production PQC, "
        "6 independent checkpoints, and publicly verifiable decision audit trail.",
        s['BodyText2']
    ))
    elements.append(PageBreak())

    # --- SLIDE 7: Business Model ---
    elements.extend(section_header("Business Model & Unit Economics", "7", s))
    rev_data = [
        ['Product', 'Pricing', 'Target Customer'],
        ['Risk Guardian API', '$15K\u2013$35K/month', 'Prop firms, trading platforms'],
        ['White-Label Engine', '$100K+ setup + $20K/month', 'Exchanges, brokers'],
        ['Per-Validation API', '$0.01\u2013$0.05/call', 'High-volume platforms'],
        ['B2C Pro SaaS', '$149/month', 'Advanced independent traders'],
        ['B2C Advanced SaaS', '$499/month', 'Semi-professional traders'],
    ]
    elements.append(make_table(rev_data[0], rev_data[1:], [140, 150, 170]))
    elements.append(Spacer(1, 8))
    econ_data = [
        ['Metric', 'Value'],
        ['CAC (Enterprise)', '$5,000\u2013$10,000'],
        ['LTV (Enterprise)', '$180K\u2013$420K'],
        ['LTV/CAC Ratio', '18x\u201384x'],
        ['Gross Margin', '60\u201370%'],
        ['Break-Even', '18\u201324 months'],
    ]
    elements.append(make_table(econ_data[0], econ_data[1:], [200, 260]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        '"Institutions pay for what blocks bad decisions, not for alpha. '
        'License-based revenue. No tokens. No performance fees."',
        s['Quote']
    ))
    elements.append(PageBreak())

    # --- SLIDE 8: Go-To-Market ---
    elements.extend(section_header("Go-To-Market Strategy", "8", s))
    elements.append(Paragraph(
        "Enterprise-first GTM targeting ADGM/DIFC ecosystem where MiCA compliance urgency "
        "creates immediate demand for decision governance infrastructure.",
        s['BodyText2']
    ))
    funnel_data = [
        ['Stage', 'Action', 'Timeline'],
        ['Awareness', '50 direct outreaches/month + events', 'Ongoing'],
        ['Assessment', 'Free governance health check', 'Week 1\u20132'],
        ['Shadow Mode', 'OMNIX runs alongside (no execution)', '2\u20134 weeks'],
        ['Advisory Mode', 'Pre-execution recommendations', '2\u20134 weeks'],
        ['Enforcement', 'Full governance with veto authority', 'Ongoing'],
        ['Paid License', 'Monthly enterprise license', 'Month 3\u20136'],
    ]
    elements.append(make_table(funnel_data[0], funnel_data[1:], [100, 230, 130]))
    elements.append(Spacer(1, 8))
    scale_data = [
        ['Phase', 'Focus', 'Timeline'],
        ['Phase 1', '3 enterprise pilots (digital assets)', 'Months 1\u20136'],
        ['Phase 2', 'Regional expansion (ADGM/DIFC/MENA)', 'Months 6\u201312'],
        ['Phase 3', 'Multi-vertical: supply chain, lending, robotics', 'Months 12\u201324'],
        ['Phase 4', 'Global: EU MiCA, Asia + insurance, energy', 'Months 24\u201336'],
    ]
    elements.append(make_table(scale_data[0], scale_data[1:], [80, 260, 120]))
    elements.append(PageBreak())

    # --- SLIDE 9: Team ---
    elements.extend(section_header("Team", "9", s))
    elements.append(Paragraph(
        "<b>Harold Nunes</b> \u2014 Founder &amp; CEO", s['BodyText2']))
    elements.extend(bullet_list([
        "Built OMNIX end-to-end: concept to production system running 24/7",
        "Deep domain expertise in algorithmic trading, decision systems, cryptographic security",
        "AI-augmented development: one person with AI achieves the output of a 5-person team",
        "Designed 6-checkpoint governance architecture, PQC integration, multi-vertical adapter pattern",
    ], s))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("<b>Key Hires Planned (Post-Funding)</b>", s['SubsectionTitle']))
    hires_data = [
        ['Role', 'Timeline', 'Purpose'],
        ['Senior Backend Engineer', 'Month 1\u20132', 'Enterprise API, system scaling'],
        ['DevOps / Infrastructure', 'Month 2\u20133', 'Production reliability, automation'],
        ['Business Development', 'Month 3\u20134', 'Enterprise sales, ADGM relationships'],
    ]
    elements.append(make_table(hires_data[0], hires_data[1:], [160, 100, 200]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "<b>Key-Person Risk Mitigation:</b> 27 ADRs, hexagonal architecture, 2\u20133 week onboarding target. "
        "First 3 hires reduce founder dependency from 100% to ~30% by Month 4.",
        s['BodyText2']
    ))
    elements.append(PageBreak())

    # --- SLIDE 10: Financials & The Ask ---
    elements.extend(section_header("Financials & The Ask", "10", s))
    fin_data = [
        ['', 'Year 1', 'Year 2', 'Year 3'],
        ['Enterprise Clients', '3 pilots', '5\u20138 licenses', '15\u201330 licenses'],
        ['B2C SaaS Users', '50\u2013100', '500\u20131,000', '2,000\u20135,000'],
        ['Revenue', '$200K\u2013$400K', '$800K\u2013$1.2M', '$2M+'],
        ['Gross Margin', '60\u201370%', '65\u201375%', '70\u201380%'],
    ]
    elements.append(make_table(fin_data[0], fin_data[1:], [120, 120, 120, 100]))
    elements.append(Spacer(1, 12))

    raise_data = [
        ['Item', 'Details'],
        ['Raising', '$500,000 USD'],
        ['Equity', '16.7%'],
        ['Pre-Money Valuation', '$2.5M\u2013$3M'],
        ['Bootstrapped', '$0 raised to date'],
        ['Stage', 'MVP (Live Product)'],
        ['Runway', '18+ months to Series A'],
    ]
    elements.append(make_table(raise_data[0], raise_data[1:], [180, 280]))
    elements.append(Spacer(1, 8))

    funds_data = [
        ['Category', 'Allocation', 'Purpose'],
        ['Strategy & Risk Engine', '35%', 'Algorithm refinement, enterprise API'],
        ['Dubai/ADGM Legal', '25%', 'Company formation, regulatory structure'],
        ['Enterprise Infrastructure', '20%', 'API, security certifications, scaling'],
        ['Team & Operations', '15%', '3 key hires (Month 1\u20134)'],
        ['Reserve', '5%', 'Contingency'],
    ]
    elements.append(make_table(funds_data[0], funds_data[1:], [150, 60, 250]))
    elements.append(PageBreak())

    # --- SLIDE 11: Roadmap ---
    elements.extend(section_header("Roadmap", "11", s))
    roadmap_items = [
        "<b>Q1 2026 (Current):</b> Complete track record validation. Eureka GCC competition. Execution Integrity v1 (Kraken fill verification). Mathematical audit (100% P&L reconciliation).",
        "<b>Q2 2026:</b> Enterprise API launch (Risk Guardian). First enterprise pilot. ADGM regulatory structure initiated.",
        "<b>Q3 2026:</b> Public license model. White-label SDK. Second and third enterprise clients.",
        "<b>Q4 2026:</b> Series A readiness. Multi-vertical domain adapter development begins.",
        "<b>2027:</b> Series A ($5M target). Global expansion (EU MiCA, Asia). Multi-vertical scaling.",
    ]
    elements.extend(bullet_list(roadmap_items, s))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Key Milestones Achieved</b>", s['SubsectionTitle']))
    milestones_data = [
        ['Date', 'Milestone'],
        ['Nov 2025', 'PQC implemented (Dilithium-3 + Kyber-768) \u2014 production'],
        ['Nov\u2013Dec 2025', 'Learning Baseline: 119 trades, system calibration'],
        ['Jan 15, 2026', 'Official Track Record Day 1 (calibrated parameters)'],
        ['Jan 28, 2026', 'Institutional website launched (omnixquantum.net)'],
        ['Feb 15, 2026', 'Multi-vertical demos: Credit/Lending + Insurance'],
        ['Feb 21, 2026', 'Public Verification Server deployed'],
        ['Feb 24, 2026', 'Execution Integrity v1: Kraken fill reconciliation'],
        ['Feb 24, 2026', 'Mathematical Audit: 119/119 trades P&L verified'],
    ]
    elements.append(make_table(milestones_data[0], milestones_data[1:], [90, 370]))

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
        "contacto@omnixquantum.net | www.omnixquantum.net | Abu Dhabi, UAE",
        ParagraphStyle('EndInfo', fontName='Helvetica', fontSize=9, textColor=BRAND_GRAY, alignment=TA_CENTER)
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "All metrics from internal dataset, not externally audited. Past performance does not guarantee future results.",
        s['SmallNote']
    ))

    doc.build(elements, onFirstPage=draw_cover_background, onLaterPages=on_later_pages)
    print(f"  Pitch Deck generated: {output_path}")
    return output_path


# ============================================================
# INVESTOR REPORT (Full Eureka — updated)
# ============================================================

def generate_investor_report(mentor_name, output_path):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

    from generate_eureka_report import (
        create_styles as eureka_styles,
        draw_cover_background as eureka_cover_bg,
        on_later_pages as eureka_later_pages,
        build_toc, build_section_1, build_section_2, build_section_3,
        build_section_4, build_section_5, build_section_6, build_section_7,
        build_section_8, build_section_9, build_section_10, build_section_11,
        build_section_12, build_section_13, build_section_14,
    )

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=40,
        title="OMNIX - Eureka GCC 2026 Semifinalist Report",
        author="Harold Nunes",
        subject="Decision Governance Infrastructure for Automated Systems",
    )

    s = eureka_styles()
    elements = []

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
    elements.append(Paragraph(f"Prepared for: {mentor_name}", info_style))
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
    elements.append(Paragraph("March 2026 | Abu Dhabi, UAE", date_style))
    elements.append(Paragraph("Classification: Competition Submission \u2014 Confidential", date_style))
    elements.append(PageBreak())

    elements.extend(build_toc(s))
    elements.extend(build_section_1(s))
    elements.extend(build_section_2(s))
    elements.extend(build_section_3(s))
    elements.extend(build_section_4(s))
    elements.extend(build_section_5(s))
    elements.extend(build_section_6(s))
    elements.extend(build_section_7(s))
    elements.extend(build_section_8(s))
    elements.extend(build_section_9(s))
    elements.extend(build_section_10(s))
    elements.extend(build_section_11(s))
    elements.extend(build_section_12(s))
    elements.extend(build_section_13(s))
    elements.extend(build_section_14(s))

    doc.build(elements, onFirstPage=eureka_cover_bg, onLaterPages=eureka_later_pages)
    print(f"  Report generated: {output_path}")
    return output_path


# ============================================================
# MAIN
# ============================================================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 60)
    print("OMNIX Mentor Document Package Generator")
    print("=" * 60)

    generated_files = []

    for mentor in MENTORS:
        name = mentor['name']
        suffix = mentor['filename_suffix']
        print(f"\nGenerating documents for: {name}")
        print("-" * 40)

        canvas_path = os.path.join(OUTPUT_DIR, f"OMNIX_Canvas_{suffix}.pdf")
        generate_canvas(name, canvas_path)
        generated_files.append(canvas_path)

        pitch_path = os.path.join(OUTPUT_DIR, f"OMNIX_PitchDeck_{suffix}.pdf")
        generate_pitch_deck(name, pitch_path)
        generated_files.append(pitch_path)

        report_path = os.path.join(OUTPUT_DIR, f"OMNIX_Report_{suffix}.pdf")
        generate_investor_report(name, report_path)
        generated_files.append(report_path)

    print("\n" + "=" * 60)
    print(f"All {len(generated_files)} documents generated successfully!")
    print("=" * 60)
    for f in generated_files:
        size_kb = os.path.getsize(f) / 1024
        print(f"  {os.path.basename(f)}: {size_kb:.1f} KB")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    return generated_files


if __name__ == '__main__':
    main()
