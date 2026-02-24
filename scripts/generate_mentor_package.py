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

    title_style = ParagraphStyle('CanvasTitle', fontName='Helvetica-Bold', fontSize=16,
                                 leading=20, textColor=BRAND_NAVY, alignment=TA_CENTER, spaceAfter=4)
    subtitle_style = ParagraphStyle('CanvasSub', fontName='Helvetica', fontSize=10,
                                    leading=14, textColor=BRAND_GRAY, alignment=TA_CENTER, spaceAfter=12)
    section_title = ParagraphStyle('CSectionTitle', fontName='Helvetica-Bold', fontSize=14,
                                   leading=18, textColor=BRAND_NAVY, spaceBefore=16, spaceAfter=8)
    subsec_title = ParagraphStyle('CSubsecTitle', fontName='Helvetica-Bold', fontSize=11,
                                   leading=15, textColor=BRAND_BLUE, spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle('CBody', fontName='Helvetica', fontSize=9, leading=13,
                          textColor=BRAND_DARK_TEXT, alignment=TA_JUSTIFY, spaceAfter=6)
    body_bold = ParagraphStyle('CBodyBold', fontName='Helvetica-Bold', fontSize=9, leading=13,
                               textColor=BRAND_DARK_TEXT, spaceAfter=6)
    bullet = ParagraphStyle('CBullet', fontName='Helvetica', fontSize=9, leading=13,
                            textColor=BRAND_DARK_TEXT, leftIndent=16, bulletIndent=6, spaceAfter=3)
    quote_style = ParagraphStyle('CQuote', fontName='Helvetica-Oblique', fontSize=10, leading=14,
                                  textColor=BRAND_BLUE, leftIndent=15, rightIndent=15,
                                  spaceBefore=6, spaceAfter=10, borderWidth=2,
                                  borderColor=BRAND_ACCENT, borderPadding=8)
    footer_note = ParagraphStyle('CanvasFooter', fontName='Helvetica', fontSize=7,
                                 leading=9, textColor=BRAND_GRAY, alignment=TA_CENTER)
    note_style = ParagraphStyle('CNote', fontName='Helvetica-Oblique', fontSize=8, leading=11,
                                textColor=BRAND_GRAY, spaceAfter=6)

    def sec_hr():
        return HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT, spaceBefore=8, spaceAfter=4)

    def canvas_table(headers, rows, col_widths=None):
        return make_table(headers, rows, col_widths)

    elements.append(Spacer(1, 80))
    elements.append(Paragraph("OMNIX", s['CoverTitle']))
    elements.append(Paragraph("Business Model Canvas", s['CoverSubtitle']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph('"Pre-Execution Risk Governance Infrastructure for Digital Asset Trading"', s['CoverTagline']))
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
    elements.append(Paragraph("Eureka Dubai Aligned | March 2026", date_style))
    elements.append(Paragraph("Classification: Competition Supplement \u2014 Expert Reviewed", date_style))
    elements.append(Paragraph("Alignment: All numbers match the OMNIX Eureka Final Pitch Deck", date_style))
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

    def header_cell(text, col_width):
        t = Table([[Paragraph(text, hdr)]], colWidths=[col_width - 4], rowHeights=[18])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), TABLE_HEADER_BG),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        return t

    elements.append(Paragraph("OMNIX \u2014 Business Model Canvas", title_style))
    elements.append(Paragraph("Institutional Risk Governance for Digital Assets", subtitle_style))

    col_w = (w - 60) / 5

    kp = bmc_cell("KEY PARTNERS", [
        "<b>Regulatory &amp; Ecosystem (Target):</b>",
        "ADGM (Target licensing ecosystem)",
        "Hub71 (Application sent \u2014 pending response)",
        "DIFC (Future expansion ecosystem)",
        "<b>Strategic Partners (Pipeline):</b>",
        "Trading platforms (API integrations)",
        "Prop trading firms (pilot partners)",
        "<b>Technology Providers:</b>",
        "Cloud infrastructure (Railway / scalable cloud)",
        "AI providers (Google Gemini 2.5 Flash, OpenAI GPT-4o, Anthropic Claude Sonnet 4)",
        "Database infrastructure (PostgreSQL)",
    ])
    ka = bmc_cell("KEY ACTIVITIES", [
        "<b>Core Operations:</b>",
        "Risk Engine Development &amp; Calibration",
        "6-Checkpoint Validation Architecture",
        "Decision Trace Logging (100% telemetry coverage)",
        "Shadow Portfolio Analysis (670,000+ events)",
        "Enterprise API Integration",
        "Model validation against real market conditions",
        "<b>Governance Operations:</b>",
        "Compliance Monitoring",
        "Telemetry Analysis",
        "Institutional Reporting &amp; Audit Trail Generation",
    ])
    vp = bmc_cell("VALUE PROPOSITIONS", [
        "Multi-layer pre-execution trade validation (6 independent checkpoints)",
        "Fail-closed architecture (default = do not trade)",
        "Complete institutional decision trace",
        "Regime detection and tail risk awareness",
        "Institutional governance logic for digital asset trading",
    ])
    cr = bmc_cell("CUSTOMER RELATIONSHIPS", [
        "<b>B2B Institutional:</b>",
        "Structured onboarding with risk threshold customization",
        "Technical integration support",
        "Governance review sessions",
        "SLA-based uptime commitments (target: 99.5%)",
        "<b>Retention Strategy:</b>",
        "Embedded in execution flow (high switching cost)",
        "Positioned as mission-critical infrastructure",
        "Continuous improvement via Shadow Portfolio learning",
        "Network effects: more data improves the engine",
    ])
    cs = bmc_cell("CUSTOMER SEGMENTS", [
        "<b>PRIMARY \u2014 B2B Institutional (80% Focus):</b>",
        "Prop Trading Firms (200+ in ADGM/DIFC)",
        "Trading Platforms (3Commas, NinjaTrader)",
        "Regulated Funds (Crypto hedge funds)",
        "Family Offices (MENA/Asia Focus)",
        "<b>SECONDARY \u2014 B2C (20% Focus):</b>",
        "Advanced independent traders",
        "Semi-professional traders",
        "High net worth individuals managing own capital",
    ])
    cost_items = bmc_cell("COST STRUCTURE", [
        "Strategy &amp; Risk Engine: 35%",
        "Dubai/ADGM Legal &amp; Regulatory: 25%",
        "Enterprise Infrastructure: 20%",
        "Team &amp; Operations: 15%",
        "Reserve: 5%",
        "Gross margin: 60\u201370%",
        "Break-even: 18\u201324 months",
    ])
    rev_items = bmc_cell("REVENUE STREAMS", [
        "<b>B2B Enterprise (80%):</b>",
        "Risk Guardian API: $15K\u201335K/mo",
        "White-Label Engine: $100K+ setup + $20K/mo",
        "Per-Validation: $0.01\u20130.05/call",
        "<b>B2C SaaS (20%):</b>",
        "Pro: $149/mo",
        "Advanced: $499/mo",
    ])

    canvas_data = [
        [
            [header_cell("KEY PARTNERS", col_w)] + kp,
            [header_cell("KEY ACTIVITIES", col_w)] + ka,
            [header_cell("VALUE PROPOSITIONS", col_w)] + vp,
            [header_cell("CUSTOMER RELATIONSHIPS", col_w)] + cr,
            [header_cell("CUSTOMER SEGMENTS", col_w)] + cs,
        ],
    ]

    main_table = Table(canvas_data, colWidths=[col_w]*5, rowHeights=[380])
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
            [header_cell("COST STRUCTURE", col_w * 2.5)] + cost_items,
            [header_cell("REVENUE STREAMS", col_w * 2.5)] + rev_items,
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

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "OMNIX \u2014 Eureka GCC 2026 Semifinalist | Pre-Seed: $500K @ $2.5M\u2013$3M valuation (16.7% equity) | "
        "All metrics from internal dataset, not externally audited | Abu Dhabi, UAE",
        footer_note
    ))
    elements.append(PageBreak())

    elements.append(sec_hr())
    elements.append(Paragraph("VALUE PROPOSITION \u2014 Detailed", section_title))
    elements.append(Paragraph(
        '"Capital protection before capital deployment."',
        quote_style
    ))
    elements.append(Paragraph("OMNIX provides:", body_bold))
    for item in [
        "Multi-layer pre-execution trade validation (6 independent checkpoints)",
        "Fail-closed architecture (default = do not trade)",
        "Complete institutional decision trace",
        "Regime detection and tail risk awareness",
        "Institutional governance logic for digital asset trading",
    ]:
        elements.append(Paragraph(f"\u2022  {item}", bullet))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("DIFFERENTIATION:", body_bold))
    diff_data = [
        ['Traditional Systems', 'OMNIX'],
        ['Optimize entries', 'Optimizes disciplined containment'],
        ['1 risk control', '6 independent checkpoints'],
        ['Trade first, manage risk later', 'Block first, trade only with confirmed edge'],
    ]
    elements.append(canvas_table(diff_data[0], diff_data[1:], [280, 280]))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph("CLIENT OUTCOME (From Validation Data):", body_bold))
    outcome_data = [
        ['Outcome', 'Evidence'],
        ['Capital preserved during volatility', '98.5% preserved while BTC dropped 7.37%'],
        ['High-risk trades correctly blocked', '47 trades blocked, 91% would have lost money'],
        ['Complete auditability', '670,000+ decision cycles logged'],
        ['System reliability', '95%+ uptime, ~120ms execution latency'],
    ]
    elements.append(canvas_table(outcome_data[0], outcome_data[1:], [250, 310]))
    elements.append(PageBreak())

    elements.append(sec_hr())
    elements.append(Paragraph("CUSTOMER SEGMENTS \u2014 Detailed", section_title))
    elements.append(Paragraph("PRIMARY \u2014 B2B Institutional (80% Focus)", subsec_title))
    seg_data = [
        ['Segment', 'Pain', 'Need'],
        ['Prop Trading Firms (200+ in ADGM/DIFC)', 'Severe drawdowns during volatile regimes', 'Automated pre-execution risk governance'],
        ['Trading Platforms (3Commas, NinjaTrader)', 'No differentiation, compliance pressure', 'Risk-as-a-Service for their users'],
        ['Regulated Funds (Crypto hedge funds)', 'Audit requirements, MiCA compliance', 'Complete decision audit trail'],
        ['Family Offices (MENA/Asia Focus)', 'Crypto uncertainty, no institutional tools', 'Institutional-grade risk controls'],
    ]
    elements.append(canvas_table(seg_data[0], seg_data[1:], [190, 200, 200]))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("SECONDARY \u2014 B2C (20% Focus, Post-Enterprise Validation)", subsec_title))
    for item in [
        "Advanced independent traders",
        "Semi-professional traders",
        "High net worth individuals managing their own capital",
    ]:
        elements.append(Paragraph(f"\u2022  {item}", bullet))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Market Sizing", subsec_title))
    mkt_data = [
        ['Metric', 'Value'],
        ['Global daily crypto trading volume', '$2.3T+'],
        ['Algorithmic trading market', '$18.8B (growing 12% CAGR)'],
        ['Prop firms in ADGM/DIFC alone', '200+'],
        ['Platforms needing MiCA compliance (2025+)', '2,000+'],
        ['Estimated institutional targets (MENA)', '~300'],
        ['Conservative penetration (5-10%)', '15-30 clients'],
        ['Year 1 target', '3 enterprise pilots'],
    ]
    elements.append(canvas_table(mkt_data[0], mkt_data[1:], [280, 280]))
    elements.append(PageBreak())

    elements.append(sec_hr())
    elements.append(Paragraph("CHANNELS &amp; GO-TO-MARKET STRATEGY", section_title))

    elements.append(Paragraph("First 3 Target Pilots (Month 1-6)", subsec_title))
    pilot_data = [
        ['Client Type', 'Quantity in ADGM/DIFC', 'Entry Strategy', 'Price'],
        ['Prop trading firms', '200+ registered', 'Free governance assessment \u2192 shadow mode \u2192 paid license', '$10K-$15K/mo (pilot rate)'],
        ['Crypto-native platforms', '50+', 'MiCA compliance urgency \u2192 governance-as-a-service', 'Per validation ($0.01-0.05/call)'],
        ['Regulated funds', '100+', 'Audit trail + decision governance documentation', '$25K-$35K/mo'],
    ]
    elements.append(canvas_table(pilot_data[0], pilot_data[1:], [120, 110, 230, 130]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Enterprise Sales Funnel", subsec_title))
    funnel_data = [
        ['Stage', 'Action', 'Timeline', 'Conversion'],
        ['Awareness', '50 direct outreaches/month + event networking', 'Ongoing', '\u2014'],
        ['Assessment', 'Free governance health check', 'Week 1-2', '30%'],
        ['Shadow Mode', 'OMNIX runs alongside their system (no execution)', '2-4 weeks', '60%'],
        ['Advisory Mode', 'OMNIX provides pre-execution recommendations', '2-4 weeks', '75%'],
        ['Enforcement Mode', 'Full governance integration with veto authority', 'Ongoing', '80% \u2192 paid'],
        ['Paid License', 'Monthly enterprise license', 'Month 3-6', '\u2014'],
    ]
    elements.append(canvas_table(funnel_data[0], funnel_data[1:], [110, 220, 100, 90]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Institutional Channels (Primary)", subsec_title))
    ch_data = [
        ['Channel', 'Focus', 'Expected Output'],
        ['Direct outreach', '50 targeted contacts/month via LinkedIn + email', '15 meetings/month'],
        ['ADGM Innovation Hub', 'Regulatory community + startup programs', '5-10 warm intros/quarter'],
        ['Hub71 (if accepted)', 'Accelerator network + corporate intros', '3-5 qualified leads/quarter'],
        ['Industry events', 'TOKEN2049 Dubai, FinTech Abu Dhabi, GITEX', '10+ qualified contacts/event'],
        ['Eureka Dubai (current)', 'Competition exposure + judge intros', 'Immediate pipeline'],
    ]
    elements.append(canvas_table(ch_data[0], ch_data[1:], [130, 230, 200]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Digital Presence (Secondary)", subsec_title))
    dig_data = [
        ['Channel', 'Purpose', 'Target'],
        ['omnixquantum.net', 'Interactive governance demos + institutional credibility', '500+ visitors/month'],
        ['LinkedIn thought leadership', 'Weekly content on decision governance + risk management', '1,000+ followers in 6 months'],
        ['Case studies (post-pilot)', 'Documented ROI from first enterprise clients', 'Conversion tool'],
    ]
    elements.append(canvas_table(dig_data[0], dig_data[1:], [170, 250, 170]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Timeline to First Revenue", subsec_title))
    rev_timeline = [
        ['Milestone', 'Target Date', 'Dependency'],
        ['First pilot agreement', 'Month 3', 'Direct outreach + networking'],
        ['First paid license', 'Month 6', 'Successful shadow + advisory period'],
        ['3 paying clients', 'Month 9', 'Pipeline from previous channels'],
        ['$50K+ MRR', 'Month 12', 'Scale from validated enterprise model'],
    ]
    elements.append(canvas_table(rev_timeline[0], rev_timeline[1:], [170, 130, 260]))
    elements.append(PageBreak())

    elements.append(sec_hr())
    elements.append(Paragraph("REVENUE STREAMS \u2014 Detailed", section_title))

    elements.append(Paragraph("B2B Enterprise (80% of Revenue)", subsec_title))
    b2b_data = [
        ['Product', 'Price', 'Target Client'],
        ['Risk Guardian API', '$15K\u201335K/month', 'Prop firms, trading platforms'],
        ['White-Label Engine', '$100K+ setup + $20K/month', 'Exchanges, brokers'],
        ['Per-Validation', '$0.01\u20130.05/call', 'High-volume platforms'],
    ]
    elements.append(canvas_table(b2b_data[0], b2b_data[1:], [180, 180, 200]))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("B2C SaaS (20% of Revenue \u2014 Post-Enterprise Validation)", subsec_title))
    b2c_data = [
        ['Tier', 'Price', 'Features'],
        ['Pro', '$149/month', 'Full Risk Guardian, decision audit trail'],
        ['Advanced', '$499/month', 'API access, custom veto configuration'],
    ]
    elements.append(canvas_table(b2c_data[0], b2c_data[1:], [120, 150, 290]))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Revenue Projections (Conservative)", subsec_title))
    proj_data = [
        ['Year', 'Focus', 'Revenue'],
        ['Year 1', '3 enterprise pilots + early SaaS', '$200K\u2013400K'],
        ['Year 2', '5-8 enterprise licenses + SaaS growth', '$800K\u20131.2M'],
        ['Year 3', 'Scale + geographic expansion (ADGM to EU MiCA)', '$2M+'],
        ['Regional potential (MENA, 15-30 clients)', 'Steady state', '$3M\u20136M annually'],
    ]
    elements.append(canvas_table(proj_data[0], proj_data[1:], [220, 200, 140]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        '"Institutions pay for what BLOCKS bad trades, not for alpha." '
        'License-based revenue. No tokens. No performance fees.',
        quote_style
    ))
    elements.append(PageBreak())

    elements.append(sec_hr())
    elements.append(Paragraph("KEY RESOURCES \u2014 Detailed", section_title))

    elements.append(Paragraph("Proprietary Technology", subsec_title))
    tech_data = [
        ['Asset', 'Description'],
        ['6-Checkpoint Security Engine', 'Multi-layer pre-execution validation'],
        ['Decision Trace Framework', 'Complete audit trail for every decision'],
        ['Shadow Portfolio Engine', '670,000+ counterfactual trade events'],
        ['Multi-AI Orchestration', 'Gemini 2.5 Flash + GPT-4o + Claude Sonnet 4'],
        ['Post-Quantum Cryptography', 'Post-quantum decision signing (NIST-standardized)'],
        ['Non-Markovian Memory', 'Behavioral pattern detection beyond recency'],
    ]
    elements.append(canvas_table(tech_data[0], tech_data[1:], [220, 340]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Human Capital", subsec_title))
    for item in [
        "Solo founder \u2014 product architecture, risk logic and infrastructure (Harold Nunes)",
        "AI-augmented development: one person with AI achieves the output of a 5-person team",
        "2-3 key hires planned (post-funding): Senior Backend (Month 1-2), DevOps (Month 2-3), Business Development (Month 3-4)",
        "Key-person risk mitigation: Documented hexagonal architecture (27 ADRs, onboarding in 2-3 weeks). "
        "First hires reduce founder dependency from 100% to ~30% by Month 4. "
        "IP assignment to company, key-person insurance and operational runbooks by Month 6",
    ]:
        elements.append(Paragraph(f"\u2022  {item}", bullet))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Infrastructure", subsec_title))
    for item in [
        "Cloud deployment (Railway \u2014 production 24/7)",
        "PostgreSQL database with complete telemetry",
        "Modular hexagonal architecture",
    ]:
        elements.append(Paragraph(f"\u2022  {item}", bullet))
    elements.append(PageBreak())

    elements.append(sec_hr())
    elements.append(Paragraph("COST STRUCTURE \u2014 Detailed", section_title))

    elements.append(Paragraph("Year 1 (Planned Allocation \u2014 $500K Funding Scenario)", subsec_title))
    cost_data = [
        ['Category', 'Allocation', 'Purpose'],
        ['Strategy &amp; Risk Engine', '35%', 'Algorithm refinement, Shadow Portfolio expansion'],
        ['Dubai/ADGM Legal &amp; Regulatory', '25%', 'Company formation, regulatory structure'],
        ['Enterprise Infrastructure', '20%', 'API for prop firms, security certifications'],
        ['Team &amp; Operations', '15%', '2-3 key hires \u2014 eliminating key-person risk (Month 1-4)'],
        ['Reserve', '5%', 'Contingency'],
    ]
    elements.append(canvas_table(cost_data[0], cost_data[1:], [180, 70, 310]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Operating Model", subsec_title))
    op_data = [
        ['Metric', 'Target'],
        ['Gross margin', '60\u201370%'],
        ['Break-even', '18\u201324 months'],
        ['Model type', 'High-margin SaaS infrastructure'],
    ]
    elements.append(canvas_table(op_data[0], op_data[1:], [280, 280]))
    elements.append(PageBreak())

    elements.append(sec_hr())
    elements.append(Paragraph("IDEAL CLIENT PROFILE \u2014 MODELED CASE STUDY", section_title))
    elements.append(Paragraph('"AlphaEdge Capital" (Representative Deployment Scenario)', subsec_title))
    elements.append(Paragraph(
        "Note: This is a representative deployment scenario based on risk simulations and pilot architecture modeling. "
        "It is not a real client.",
        note_style
    ))

    profile_data = [
        ['Attribute', 'Detail'],
        ['Company Type', 'Prop Trading Firm'],
        ['Region', 'ADGM Ecosystem'],
        ['Deployed Capital', '$5M'],
        ['Traders', '15-25 active'],
    ]
    elements.append(canvas_table(profile_data[0], profile_data[1:], [200, 360]))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Problem", subsec_title))
    for item in [
        "Severe drawdowns during volatile regimes",
        "No unified pre-execution validation",
        "No centralized risk governance layer",
        "Gaps in compliance documentation",
    ]:
        elements.append(Paragraph(f"\u2022  {item}", bullet))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("OMNIX Deployment Model", subsec_title))
    deploy_data = [
        ['Phase', 'Activity', 'Duration'],
        ['Phase 1', 'Integration and Calibration', '2-4 weeks'],
        ['Phase 2', 'Observation Mode (shadow, no blocking)', '2-4 weeks'],
        ['Phase 3', 'Advisory Mode (alerts, no enforcement)', '2-4 weeks'],
        ['Phase 4', 'Enforcement Mode (active blocking)', 'Ongoing'],
    ]
    elements.append(canvas_table(deploy_data[0], deploy_data[1:], [120, 250, 190]))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Modeled Impact (Simulation-Based)", subsec_title))
    impact_data = [
        ['Metric', 'Expected Impact'],
        ['Severe drawdown frequency', 'Significantly reduced'],
        ['Win-rate quality (post-veto filter)', 'Improved'],
        ['Institutional transparency', 'Complete audit trail'],
        ['Compliance reporting', 'Automated'],
    ]
    elements.append(canvas_table(impact_data[0], impact_data[1:], [280, 280]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("ROI Model", subsec_title))
    for item in [
        "Monthly OMNIX cost: $25K (mid-range API license)",
        "Monthly capital at risk: $5M",
        "Drawdown reduction impact: -40% severe events",
        "Est. capital preserved/month: $50K-200K",
        "ROI: 2x-8x monthly cost",
        "Primary value driver: Tail risk exposure avoided",
    ]:
        elements.append(Paragraph(f"\u2022  {item}", bullet))
    elements.append(PageBreak())

    elements.append(sec_hr())
    elements.append(Paragraph("MARKET POSITIONING", section_title))
    elements.append(Paragraph("The Gap OMNIX Fills", subsec_title))
    gap_data = [
        ['Category', 'Limitation', 'OMNIX Advantage'],
        ['Retail Bots', 'Too simple, no risk governance', 'Institutional 6-checkpoint architecture'],
        ['Quant Funds', 'Too expensive (minimum $10M+)', 'Accessible infrastructure'],
        ['Manual Oversight', 'Too slow for real-time', 'Automated validation &lt;120ms'],
    ]
    elements.append(canvas_table(gap_data[0], gap_data[1:], [140, 200, 220]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        '"Institutional discipline at accessible scale."',
        quote_style
    ))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("GROWTH STRATEGY", section_title))
    growth_data = [
        ['Phase', 'Focus', 'Timeline'],
        ['Phase 1', 'Pilot validation (3 enterprise clients)', 'Months 1-6'],
        ['Phase 2', 'Regional expansion (ADGM/DIFC/MENA)', 'Months 6-12'],
        ['Phase 3', 'Platform partnerships (API integrations)', 'Months 12-18'],
        ['Phase 4', 'Global scale (EU MiCA, Asia)', 'Months 18-36'],
    ]
    elements.append(canvas_table(growth_data[0], growth_data[1:], [120, 250, 190]))
    elements.append(PageBreak())

    elements.append(sec_hr())
    elements.append(Paragraph("FUNDING", section_title))

    elements.append(Paragraph("Pre-Seed Round", subsec_title))
    fund_data = [
        ['Item', 'Details'],
        ['Raising', '$500,000 USD'],
        ['Equity', '16.7%'],
        ['Pre-Money Valuation', '$2.5M\u2013$3M'],
    ]
    elements.append(canvas_table(fund_data[0], fund_data[1:], [280, 280]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Valuation Justification", subsec_title))
    val_data = [
        ['Factor', 'Evidence'],
        ['Product running in production', '3+ months running 24/7'],
        ['Real validation data', '670,000+ decision cycles analyzed'],
        ['Defensible IP', '6-checkpoint architecture + Shadow Portfolio Engine'],
        ['Strategic timing', 'MiCA + ADGM convergence creating urgent demand'],
        ['Comparable', 'Chainalysis raised at $4M pre-money at similar stage'],
    ]
    elements.append(canvas_table(val_data[0], val_data[1:], [200, 360]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Milestones with Funding", subsec_title))
    mile_data = [
        ['Timeline', 'Milestone'],
        ['Month 1', 'Complete track record, initiate institutional outreach'],
        ['Month 3', 'First enterprise pilot (prop firm or trading platform)'],
        ['Month 6', 'ADGM regulatory structure complete'],
        ['Month 9', '3 enterprise clients paying'],
        ['Month 12', 'Series A readiness with validated revenue metrics'],
    ]
    elements.append(canvas_table(mile_data[0], mile_data[1:], [120, 440]))

    elements.append(Spacer(1, 14))
    elements.append(sec_hr())
    elements.append(Paragraph("DOCUMENT STATUS", section_title))
    doc_data = [
        ['Attribute', 'Value'],
        ['Prepared for', 'Eureka Dubai 2026, Institutional Review, ADGM Ecosystem'],
        ['Alignment', 'All numbers match OMNIX Eureka Final Pitch Deck'],
        ['Founder', 'Harold Nunes'],
        ['Contact', 'contacto@omnixquantum.net'],
        ['Website', 'www.omnixquantum.net'],
        ['LinkedIn', 'linkedin.com/in/harold-nunes-21bb65285'],
    ]
    elements.append(canvas_table(doc_data[0], doc_data[1:], [200, 360]))

    elements.append(Spacer(1, 14))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_GOLD, spaceBefore=8, spaceAfter=8))
    elements.append(Paragraph(
        "OMNIX \u2014 Protecting Capital First",
        ParagraphStyle('EndTag', fontName='Helvetica-Bold', fontSize=12, textColor=BRAND_NAVY, alignment=TA_CENTER)
    ))
    elements.append(Paragraph(
        "Eureka Dubai 2026 \u2014 Semifinalist",
        ParagraphStyle('EndSub', fontName='Helvetica', fontSize=10, textColor=BRAND_GOLD, alignment=TA_CENTER, spaceAfter=8)
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
