"""
OMNIX-PAT-2026-014 — Bidirectional Temporal Admissibility System
Full provisional patent PDF with vector diagrams.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 HRFlowable, Table, TableStyle, PageBreak,
                                 KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.graphics.shapes import (Drawing, Rect, String, Line,
                                        Polygon, Circle, Group)
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Flowable

OUTPUT = 'docs/ip/provisional_applications/pdf_exports/OMNIX_PAT_2026_014_PROVISIONAL.pdf'

NAVY  = colors.HexColor('#0A1628')
GOLD  = colors.HexColor('#C9A84C')
WHITE = colors.white
LGRAY = colors.HexColor('#F5F5F5')
DGRAY = colors.HexColor('#333333')
MGRAY = colors.HexColor('#666666')
CGRAY = colors.HexColor('#CCCCCC')
RED   = colors.HexColor('#C0392B')
GREEN = colors.HexColor('#1A7A4A')
BLUE  = colors.HexColor('#1A4A7A')
AMBER = colors.HexColor('#E67E22')
PURPLE= colors.HexColor('#6B3FA0')
TEAL  = colors.HexColor('#0D6E6E')

W, H = A4
LM = 22*mm
RM = 22*mm
CONTENT_W = W - LM - RM

def S(name, **kw):
    return ParagraphStyle(name, **kw)

h1      = S('H1',  fontName='Helvetica-Bold', fontSize=13, textColor=NAVY,
            spaceAfter=5, spaceBefore=14)
h2      = S('H2',  fontName='Helvetica-Bold', fontSize=11, textColor=NAVY,
            spaceAfter=4, spaceBefore=10)
h3      = S('H3',  fontName='Helvetica-Bold', fontSize=10, textColor=DGRAY,
            spaceAfter=3, spaceBefore=7)
body    = S('Body',fontName='Helvetica', fontSize=9.5, textColor=DGRAY,
            spaceAfter=5, leading=14, alignment=TA_JUSTIFY)
bold_b  = S('BB',  fontName='Helvetica-Bold', fontSize=9.5, textColor=DGRAY,
            spaceAfter=3, leading=14)
caption = S('Cap', fontName='Helvetica-Oblique', fontSize=8.5, textColor=MGRAY,
            spaceAfter=6, alignment=TA_CENTER)

def box(d, x, y, w, h, fill=NAVY, stroke=GOLD, sw=1.5, rx=3, ry=3):
    d.add(Rect(x, y, w, h, rx=rx, ry=ry,
               fillColor=fill, strokeColor=stroke, strokeWidth=sw))

def label(d, x, y, txt, size=8.5, color=WHITE, bold=False, align='middle'):
    fn = 'Helvetica-Bold' if bold else 'Helvetica'
    d.add(String(x, y, txt, fontName=fn, fontSize=size,
                 fillColor=color, textAnchor=align))

def arrow_down(d, x, y1, y2, color=GOLD, sw=1.5):
    d.add(Line(x, y1, x, y2+4, strokeColor=color, strokeWidth=sw))
    d.add(Polygon([x-4, y2+4, x+4, y2+4, x, y2],
                  fillColor=color, strokeColor=color, strokeWidth=0))

def arrow_right(d, x1, x2, y, color=GOLD, sw=1.5):
    d.add(Line(x1, y, x2-4, y, strokeColor=color, strokeWidth=sw))
    d.add(Polygon([x2-4, y+4, x2-4, y-4, x2, y],
                  fillColor=color, strokeColor=color, strokeWidth=0))

def arrow_left(d, x1, x2, y, color=GOLD, sw=1.5):
    d.add(Line(x1, y, x2+4, y, strokeColor=color, strokeWidth=sw))
    d.add(Polygon([x2+4, y+4, x2+4, y-4, x2, y],
                  fillColor=color, strokeColor=color, strokeWidth=0))

# ── DIAGRAM 1: BIDIRECTIONAL TEMPORAL ENVELOPE ────────────────────────────────
def diagram_envelope(width):
    dw, dh = width, 190
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    label(d, dw/2, dh-14, 'FIG. 1 — Bidirectional Temporal Admissibility Envelope: Past (TCV) + Future (FTI)',
          size=8, color=DGRAY, bold=True, align='middle')

    # Timeline axis
    tl_y = dh/2 + 10
    d.add(Line(15, tl_y, dw-15, tl_y, strokeColor=DGRAY, strokeWidth=1.5))

    # Time points — past
    past_points = [('t-15', 0.08), ('t-12', 0.15), ('t-9', 0.22),
                   ('t-6', 0.29), ('t-3', 0.36), ('t-1', 0.43)]
    for label_t, frac in past_points:
        px = 15 + frac*(dw-30)
        d.add(Circle(px, tl_y, 4, fillColor=BLUE, strokeColor=BLUE, strokeWidth=0))
        label(d, px, tl_y-14, label_t, size=6, color=DGRAY, align='middle')

    # Decision point (t=0)
    dec_x = 15 + 0.52*(dw-30)
    d.add(Circle(dec_x, tl_y, 8, fillColor=GOLD, strokeColor=NAVY, strokeWidth=2))
    label(d, dec_x, tl_y+20, 't = 0', size=8.5, color=NAVY, bold=True, align='middle')
    label(d, dec_x, tl_y+9, 'DECISION', size=7, color=NAVY, bold=True, align='middle')

    # Future points
    future_points = [('t+1', 0.62), ('t+2', 0.69), ('t+3', 0.76),
                     ('t+4', 0.83), ('t+5', 0.90)]
    for label_t, frac in future_points:
        px = 15 + frac*(dw-30)
        d.add(Circle(px, tl_y, 4, fillColor=TEAL, strokeColor=TEAL, strokeWidth=0))
        label(d, px, tl_y-14, label_t, size=6, color=DGRAY, align='middle')

    # TCV bracket (past)
    tcv_start = 15 + 0.08*(dw-30)
    tcv_end = dec_x - 10
    bracket_y = tl_y + 38
    d.add(Rect(tcv_start, tl_y+26, tcv_end-tcv_start, 18,
               fillColor=colors.HexColor('#1A4A7A'), strokeColor=BLUE, strokeWidth=1.5, rx=2))
    label(d, (tcv_start+tcv_end)/2, tl_y+37, 'TCV — Trajectory Coherence Validator (retrospective)',
          size=7.5, color=WHITE, bold=True, align='middle')

    # FTI bracket (future)
    fti_start = dec_x + 10
    fti_end = 15 + 0.92*(dw-30)
    d.add(Rect(fti_start, tl_y+26, fti_end-fti_start, 18,
               fillColor=TEAL, strokeColor=TEAL, strokeWidth=1.5, rx=2))
    label(d, (fti_start+fti_end)/2, tl_y+37, 'FTI — Forward Trajectory Implication (prospective)',
          size=7.5, color=WHITE, bold=True, align='middle')

    # Admissibility condition
    box(d, dw/2-110, 10, 220, 22, fill=NAVY, stroke=GOLD, sw=2, rx=4, ry=4)
    label(d, dw/2, 22, 'ADMISSIBLE ↔ Consistent with past trajectory  AND  near-future trajectory',
          size=8, color=GOLD, bold=True, align='middle')
    label(d, dw/2, 12, 'Both TCV and FTI must pass — either failure → BLOCK',
          size=7, color=CGRAY, align='middle')

    # Arrows from brackets to decision
    arrow_right(d, tcv_end, dec_x-12, tl_y+35, color=BLUE, sw=1)
    arrow_left(d, fti_start, dec_x+12, tl_y+35, color=TEAL, sw=1)

    return d

# ── DIAGRAM 2: TCV THREE-DIMENSIONAL SCORING ──────────────────────────────────
def diagram_tcv(width):
    dw, dh = width, 185
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    label(d, dw/2, dh-14, 'FIG. 2 — TCV: Three-Dimensional Retrospective Trajectory Scoring',
          size=8, color=DGRAY, bold=True, align='middle')

    dims = [
        ('Direction\nCoherence', '40%', 'Monotonicity of\nsignal deltas over\nhistorical window', BLUE),
        ('Regime-Action\nAlignment', '35%', 'Action vs. dominant\nhistorical regime\nclassification', NAVY),
        ('Signal\nStability', '25%', 'Inverse direction-\nflip rate over\nhistorical window', TEAL),
    ]
    dw3 = (dw - 30) / 3 - 6
    dim_y = dh - 105

    for i, (name, weight, desc, clr) in enumerate(dims):
        dx = 10 + i*(dw3+6)
        box(d, dx, dim_y, dw3, 72, fill=clr, stroke=CGRAY, sw=1, rx=3, ry=3)
        lines = name.split('\n')
        label(d, dx+dw3/2, dim_y+62, lines[0], size=8, color=WHITE, bold=True)
        if len(lines) > 1:
            label(d, dx+dw3/2, dim_y+52, lines[1], size=8, color=WHITE, bold=True)
        label(d, dx+dw3/2, dim_y+41, f'Weight: {weight}', size=9, color=GOLD, bold=True)
        dlines = desc.split('\n')
        for j, dl in enumerate(dlines):
            label(d, dx+dw3/2, dim_y+29-j*10, dl, size=7, color=CGRAY)
        # Gold border for weight emphasis
        d.add(Rect(dx+8, dim_y+36, dw3-16, 14, rx=2, ry=2,
                   fillColor=colors.Color(0,0,0,0), strokeColor=GOLD, strokeWidth=1))

    # Arrow down to TCV result
    arrow_down(d, dw/2, dim_y, dim_y-18, color=GOLD)

    # Data sources
    ds_y = dim_y - 48
    box(d, 10, ds_y, (dw-26)/2, 26, fill=colors.HexColor('#1A3A5A'), stroke=CGRAY, sw=1, rx=3, ry=3)
    label(d, 10+(dw-26)/4, ds_y+18, 'shadow_trade_events', size=7.5, color=GOLD, bold=True)
    label(d, 10+(dw-26)/4, ds_y+7, 'Blocked decisions (veto events)', size=7, color=CGRAY)

    box(d, 16+(dw-26)/2, ds_y, (dw-26)/2, 26, fill=colors.HexColor('#1A3A5A'), stroke=CGRAY, sw=1, rx=3, ry=3)
    label(d, 16+(dw-26)/2+(dw-26)/4, ds_y+18, 'paper_trading_trades', size=7.5, color=GOLD, bold=True)
    label(d, 16+(dw-26)/2+(dw-26)/4, ds_y+7, 'Approved decisions (executed events)', size=7, color=CGRAY)

    # Combined note
    note_y = ds_y - 18
    box(d, 10, note_y, dw-20, 14, fill=GREEN, stroke=GOLD, sw=1.5, rx=2, ry=2)
    label(d, dw/2, note_y+5, 'Combined dual-source = full trajectory without survivorship bias',
          size=7.5, color=WHITE, bold=True, align='middle')

    return d

# ── DIAGRAM 3: HMM REGIME TRANSITION RISK ─────────────────────────────────────
def diagram_hmm(width):
    dw, dh = width, 185
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    label(d, dw/2, dh-14, 'FIG. 3 — FTI Dimension 1: HMM Regime Transition Risk Matrix',
          size=8, color=DGRAY, bold=True, align='middle')

    # Current regime box
    cur_y = dh - 55
    box(d, dw/2-70, cur_y, 140, 28, fill=AMBER, stroke=GOLD, sw=2, rx=4, ry=4)
    label(d, dw/2, cur_y+18, 'Current Regime: VOLATILE', size=9, color=WHITE, bold=True)
    label(d, dw/2, cur_y+7, 'persistence probability = 0.45', size=7.5, color=WHITE)
    arrow_down(d, dw/2, cur_y, cur_y-18, color=GOLD)

    # Transition probability row
    regimes = [
        ('BULLISH', '0.08', GREEN),
        ('BEARISH', '0.22', RED),
        ('TRENDING', '0.12', BLUE),
        ('VOLATILE', '0.45', AMBER),
        ('STRONG_SELL', '0.13', colors.HexColor('#8B0000')),
    ]
    reg_y = cur_y - 58
    rw = (dw - 20) / 5 - 4

    label(d, dw/2, reg_y+54, '5-step HMM Transition Probability from VOLATILE:', size=7.5, color=DGRAY, align='middle')

    for i, (name, prob, clr) in enumerate(regimes):
        rx = 10 + i*(rw+4)
        box(d, rx, reg_y, rw, 42, fill=clr, stroke=CGRAY, sw=0.8, rx=3, ry=3)
        label(d, rx+rw/2, reg_y+32, name, size=6.5, color=WHITE, bold=True)
        label(d, rx+rw/2, reg_y+20, f'P = {prob}', size=8, color=WHITE, bold=True)
        is_adverse = name in ('BEARISH', 'VOLATILE', 'STRONG_SELL')
        if is_adverse:
            label(d, rx+rw/2, reg_y+8, 'ADVERSE', size=6, color=colors.HexColor('#FFAAAA'))
            d.add(Rect(rx, reg_y, rw, 42, rx=3, ry=3,
                       fillColor=colors.Color(0,0,0,0), strokeColor=RED, strokeWidth=1.5))
        else:
            label(d, rx+rw/2, reg_y+8, 'favorable', size=6, color=colors.HexColor('#AAFFAA'))

    # Risk assessment
    adverse_total = 0.22 + 0.45 + 0.13  # BEARISH + VOLATILE + STRONG_SELL = 0.80
    arrow_down(d, dw/2, reg_y, reg_y-18, color=GOLD)
    result_y = reg_y - 40
    box(d, 10, result_y, dw-20, 30, fill=RED, stroke=GOLD, sw=2, rx=4, ry=4)
    label(d, dw/2, result_y+22, f'P(adverse regime in 5 cycles | VOLATILE) = {adverse_total:.2f} = HIGH',
          size=8.5, color=WHITE, bold=True, align='middle')
    label(d, dw/2, result_y+10, 'FTI Regime Transition Risk → LOW score  →  BUY decision: BLOCKED (prospective inadmissibility)',
          size=7.5, color=colors.HexColor('#FFCCCC'), align='middle')

    return d

# ── DIAGRAM 4: BILATERAL ADMISSIBILITY LOGIC ──────────────────────────────────
def diagram_bilateral(width):
    dw, dh = width, 185
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    label(d, dw/2, dh-14, 'FIG. 4 — Bilateral Admissibility Logic: TCV × FTI → Governance Outcome',
          size=8, color=DGRAY, bold=True, align='middle')

    # Table headers
    col_w = [42*mm, 42*mm, CONTENT_W - 84*mm]
    hdr_y = dh - 42
    headers = ['TCV Result', 'FTI Result', 'Bilateral Decision']
    hdr_x = [10, 10+col_w[0]/mm*2.835, 10+col_w[0]/mm*2.835+col_w[1]/mm*2.835]
    col_px = [10, 10 + int(col_w[0]*2.835/mm), 10 + int((col_w[0]+col_w[1])*2.835/mm)]
    cpx = [10, 118, 226]
    cwx = [108, 108, dw-10-226]

    for i, (hdr, cx, cw) in enumerate(zip(headers, cpx, cwx)):
        box(d, cx, hdr_y, cw, 20, fill=NAVY, stroke=GOLD, sw=1.5, rx=0, ry=0)
        label(d, cx+cw/2, hdr_y+7, hdr, size=8, color=GOLD, bold=True)

    rows = [
        ('ADMISSIBLE', 'PASSED', '✓ PROCEEDS — bilateral admissibility confirmed', GREEN, WHITE),
        ('NOT ADMISSIBLE', 'PASSED', '✗ BLOCKED — retrospective trajectory violation', RED, WHITE),
        ('ADMISSIBLE', 'NOT PASSED', '✗ BLOCKED — prospective regime transition risk', RED, WHITE),
        ('NOT ADMISSIBLE', 'NOT PASSED', '✗ BLOCKED — bilateral compound failure', colors.HexColor('#8B0000'), WHITE),
        ('PASS-THROUGH', 'PASSED', '⚠ PROCEEDS — TCV fail-safe mode (logged)', AMBER, WHITE),
        ('ADMISSIBLE', 'PASS-THROUGH', '⚠ PROCEEDS — FTI fail-safe mode (logged)', AMBER, WHITE),
    ]
    row_fills = [GREEN, RED, RED, colors.HexColor('#8B0000'), AMBER, AMBER]

    for i, (tcv, fti, outcome, fill, txt_c) in enumerate(rows):
        ry = hdr_y - 22*(i+1)
        bg = colors.HexColor('#F8F8F8') if i % 2 == 0 else WHITE
        box(d, cpx[0], ry, cwx[0], 20, fill=bg, stroke=CGRAY, sw=0.5, rx=0, ry=0)
        label(d, cpx[0]+cwx[0]/2, ry+7, tcv, size=7.5, color=BLUE, bold=True if 'NOT' in tcv else False)
        box(d, cpx[1], ry, cwx[1], 20, fill=bg, stroke=CGRAY, sw=0.5, rx=0, ry=0)
        label(d, cpx[1]+cwx[1]/2, ry+7, fti, size=7.5, color=TEAL, bold=True if 'NOT' in fti else False)
        box(d, cpx[2], ry, cwx[2], 20, fill=fill, stroke=CGRAY, sw=0.5, rx=0, ry=0)
        label(d, cpx[2]+cwx[2]/2, ry+7, outcome, size=7, color=txt_c)

    # Bottom border
    total_h = hdr_y + 20
    total_bottom = hdr_y - 22*len(rows)
    d.add(Rect(cpx[0], total_bottom, dw-20, total_h-total_bottom,
               fillColor=colors.Color(0,0,0,0), strokeColor=GOLD, strokeWidth=1.5))

    return d

# ── HEADER / FOOTER ────────────────────────────────────────────────────────────
def on_page(canvas_obj, doc):
    canvas_obj.saveState()
    w, h = A4
    canvas_obj.setFillColor(NAVY)
    canvas_obj.rect(0, h-16*mm, w, 16*mm, fill=1, stroke=0)
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont('Helvetica-Bold', 11)
    canvas_obj.drawString(LM, h-10*mm, 'OMNIX QUANTUM LTD')
    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont('Helvetica', 7)
    canvas_obj.drawString(LM, h-14*mm, 'DECISION GOVERNANCE INFRASTRUCTURE')
    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont('Helvetica-Bold', 9)
    canvas_obj.drawRightString(w-RM, h-9*mm, 'OMNIX-PAT-2026-014')
    canvas_obj.setFillColor(colors.HexColor('#AABDD0'))
    canvas_obj.setFont('Helvetica', 7)
    canvas_obj.drawRightString(w-RM, h-13.5*mm, 'PROVISIONAL PATENT APPLICATION')
    canvas_obj.setStrokeColor(GOLD)
    canvas_obj.setLineWidth(1.5)
    canvas_obj.line(0, h-16.5*mm, w, h-16.5*mm)
    canvas_obj.setStrokeColor(colors.HexColor('#E0E0E0'))
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(LM, 14*mm, w-RM, 14*mm)
    canvas_obj.setFillColor(MGRAY)
    canvas_obj.setFont('Helvetica', 7)
    canvas_obj.drawString(LM, 9*mm,
        'CONFIDENTIAL — PATENT PENDING — OMNIX-PAT-2026-014 — Filed: April 19, 2026')
    pn = canvas_obj.getPageNumber()
    canvas_obj.drawRightString(w-RM, 9*mm, f'Page {pn}')
    canvas_obj.restoreState()

# ── COVER PAGE ─────────────────────────────────────────────────────────────────
def build_cover():
    story = []
    story.append(Spacer(1, 18*mm))

    co_data = [[Paragraph('<font name="Helvetica-Bold" size="20" color="#0A1628">OMNIX QUANTUM LTD</font>',
                          S('c', fontName='Helvetica-Bold', fontSize=20, textColor=NAVY, alignment=TA_CENTER))]]
    co_t = Table(co_data, colWidths=[CONTENT_W])
    co_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('TOPPADDING', (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 2, GOLD),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(co_t)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('DECISION GOVERNANCE INFRASTRUCTURE',
                           S('tl', fontName='Helvetica', fontSize=10, textColor=GOLD, alignment=TA_CENTER, spaceAfter=8)))
    story.append(HRFlowable(width='80%', thickness=1, color=GOLD, spaceAfter=10))
    story.append(Paragraph('UNITED STATES PATENT AND TRADEMARK OFFICE',
                           S('ul', fontName='Helvetica', fontSize=9, textColor=MGRAY, alignment=TA_CENTER, spaceAfter=3)))
    story.append(Paragraph('PROVISIONAL PATENT APPLICATION',
                           S('ul2', fontName='Helvetica-Bold', fontSize=10, textColor=NAVY, alignment=TA_CENTER, spaceAfter=10)))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('TITLE OF INVENTION:',
                           S('toi', fontName='Helvetica', fontSize=8.5, textColor=MGRAY, alignment=TA_CENTER, spaceAfter=4)))

    title_data = [[Paragraph(
        'BIDIRECTIONAL TEMPORAL ADMISSIBILITY SYSTEM FOR AUTOMATED GOVERNANCE DECISIONS '
        'WITH RETROSPECTIVE TRAJECTORY COHERENCE SCORING, PROSPECTIVE REGIME TRANSITION '
        'RISK EVALUATION USING HIDDEN MARKOV MODEL TRANSITION MATRICES, AND DUAL-SOURCE '
        'UNBIASED HISTORY ANALYSIS',
        S('tt', fontName='Helvetica-Bold', fontSize=12, textColor=NAVY,
          alignment=TA_CENTER, leading=17))]]
    title_t = Table(title_data, colWidths=[CONTENT_W])
    title_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#E8EEF4')),
        ('TOPPADDING', (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('BOX', (0,0), (-1,-1), 1, BLUE),
    ]))
    story.append(title_t)
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='50%', thickness=0.5, color=CGRAY, spaceAfter=8))

    meta = [
        ['Docket Number:', 'OMNIX-PAT-2026-014'],
        ['Inventor:', 'Harold Alberto Nunes Rodelo'],
        ['Applicant:', 'OMNIX QUANTUM LTD (United Kingdom)'],
        ['Entity Status:', 'Micro Entity — 37 C.F.R. § 1.29'],
        ['Filing Basis:', '35 U.S.C. § 111(b) — Provisional Application'],
        ['Date Prepared:', 'April 19, 2026'],
        ['Date of Filing:', 'April 19, 2026'],
        ['Related Applications:', 'OMNIX-PAT-2026-001 (Governance Architecture), OMNIX-PAT-2026-012 (TIE), OMNIX-PAT-2026-013 (Exit Layer)'],
    ]
    meta_s = TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), NAVY),
        ('TEXTCOLOR', (1,0), (1,-1), DGRAY),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, colors.HexColor('#F5F7FA')]),
        ('BOX', (0,0), (-1,-1), 0.5, CGRAY),
        ('INNERGRID', (0,0), (-1,-1), 0.25, CGRAY),
    ])
    mt = Table(meta, colWidths=[45*mm, CONTENT_W-45*mm])
    mt.setStyle(meta_s)
    story.append(mt)
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='80%', thickness=1, color=GOLD, spaceAfter=8))
    story.append(Paragraph(
        'This document constitutes a Provisional Patent Application filed pursuant to 35 U.S.C. § 111(b). '
        'It establishes a priority date and grants twelve (12) months from the filing date to submit a '
        'corresponding non-provisional application. CONFIDENTIAL — NOT FOR DISTRIBUTION.',
        S('nt', fontName='Helvetica', fontSize=7.5, textColor=MGRAY, alignment=TA_JUSTIFY, leading=11)))
    story.append(PageBreak())
    return story

# ── MAIN STORY ─────────────────────────────────────────────────────────────────
def build_story():
    story = build_cover()

    # FIELD
    story.append(Paragraph('FIELD OF THE INVENTION', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))
    story.append(Paragraph(
        'The present invention relates to automated decision governance systems, and more '
        'particularly to a bidirectional temporal admissibility system that determines whether '
        'a proposed governance decision is temporally admissible by simultaneously evaluating '
        '<b>retrospective trajectory coherence</b> — whether the proposed decision is consistent '
        'with the recent history of the system — and <b>prospective trajectory implication</b> '
        '— whether the proposed decision is consistent with the likely near-future trajectory '
        'of the system as estimated by a Hidden Markov Model regime transition matrix. The '
        'combined bilateral temporal assessment constitutes a governance checkpoint that extends '
        'admissibility determination from the current instant to both the recent past and '
        'the probable near future.', body))

    # BACKGROUND
    story.append(Paragraph('BACKGROUND OF THE INVENTION', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))
    story.append(Paragraph(
        'Multi-checkpoint governance pipelines for automated decision systems evaluate each '
        'proposed decision against a set of criteria reflecting the current state of the '
        'system: signal quality, probabilistic confidence, risk exposure, compliance '
        'thresholds, and coherence metrics. This evaluation is instantaneous — it considers '
        'the system\'s current state but not its trajectory through time.', body))
    story.append(Paragraph(
        '<b>The temporal admissibility gap has two dimensions:</b>', bold_b))
    story.append(Paragraph(
        '<b>Dimension A — Retrospective:</b> A system may generate a nominally valid decision '
        'that contradicts the direction, regime, and signal pattern established by its recent '
        'history. A BUY decision generated after 15 consecutive cycles of bearish signals and '
        'declining regime quality is nominally valid if it passes all current-state checkpoints. '
        'It is temporally inadmissible because it is incoherent with the trajectory from '
        'which it emerged.', body))
    story.append(Paragraph(
        '<b>Dimension B — Prospective:</b> A system may generate a nominally valid decision '
        'that is likely to become inadmissible within a small number of future cycles because '
        'the detected regime is likely to transition to an adverse regime. Approving a BUY '
        'decision in a regime that has an 80% probability of transitioning to BEARISH within '
        '5 cycles approves an action that will, with high probability, be contradicted by '
        'the system\'s own future signals.', body))
    story.append(Paragraph(
        'Existing governance systems address neither dimension. No prior art checkpoint '
        'pipeline performs retrospective trajectory coherence analysis or prospective '
        'HMM-based regime transition risk evaluation as a condition of decision admissibility.', body))

    # SUMMARY
    story.append(Paragraph('SUMMARY OF THE INVENTION', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))
    story.append(Paragraph(
        'The present invention provides a Bidirectional Temporal Admissibility System '
        'comprising two integrated components that together enforce temporal coherence '
        'of automated governance decisions:', body))

    comps = [
        ('TCV', 'Trajectory Coherence Validator',
         'A retrospective module evaluating proposed decisions against three weighted dimensions '
         'of recent behavioral trajectory: direction coherence (40%), regime-action alignment '
         '(35%), and signal stability (25%). Uses dual-source history analysis combining '
         'shadow_trade_events (blocked decisions) and paper_trading_trades (approved decisions) '
         'to eliminate survivorship bias from the historical record.'),
        ('FTI', 'Forward Trajectory Implication',
         'A prospective module evaluating proposed decisions against two forward-looking risk '
         'dimensions: (1) HMM Regime Transition Risk — probability that the current regime '
         'transitions to an adverse regime within a configurable horizon; (2) Trajectory '
         'Terminus Risk — probability that continuing current trajectory leads to a '
         'governance-prohibited state within a configurable horizon.'),
    ]
    comp_data = [[Paragraph(f'<b>{c}</b>', S('ch', fontName='Helvetica-Bold', fontSize=9.5, textColor=GOLD)),
                  Paragraph(f'<b>{n}</b>', S('cn', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
                  Paragraph(d, S('cd', fontName='Helvetica', fontSize=8.5, textColor=WHITE, leading=12))]
                 for c, n, d in comps]
    comp_t = Table(comp_data, colWidths=[12*mm, 38*mm, CONTENT_W-50*mm])
    comp_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [NAVY, BLUE]),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('INNERGRID', (0,0), (-1,-1), 0.3, CGRAY),
        ('BOX', (0,0), (-1,-1), 1.5, GOLD),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(comp_t)
    story.append(Spacer(1, 5*mm))

    # Diagram 1
    story.append(KeepTogether([
        renderPDF.GraphicsFlowable(diagram_envelope(CONTENT_W)),
        Paragraph('FIG. 1 — Bidirectional Temporal Envelope: TCV evaluates past trajectory; FTI projects future trajectory', caption),
    ]))
    story.append(Spacer(1, 4*mm))

    # Diagram 2
    story.append(KeepTogether([
        renderPDF.GraphicsFlowable(diagram_tcv(CONTENT_W)),
        Paragraph('FIG. 2 — TCV Three-Dimensional Scoring with Dual-Source Unbiased History Analysis', caption),
    ]))

    story.append(PageBreak())

    # DETAILED DESCRIPTION
    story.append(Paragraph('DETAILED DESCRIPTION OF THE INVENTION', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))

    story.append(Paragraph('I. Trajectory Coherence Validator (TCV)', h2))
    story.append(Paragraph(
        'The TCV evaluates a proposed decision against the recent behavioral trajectory '
        'of the governance system across three independently weighted dimensions:', body))

    dims_table = [
        [Paragraph('<b>Dimension</b>', S('dh', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
         Paragraph('<b>Weight</b>', S('dh', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
         Paragraph('<b>Measurement</b>', S('dh', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
         Paragraph('<b>BLOCK Condition</b>', S('dh', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE))],
        ['Direction Coherence', '40%',
         'Monotonicity of signal deltas over historical window',
         'Proposed direction contradicts majority of recent signal deltas'],
        ['Regime-Action Alignment', '35%',
         'Consistency of proposed action with dominant historical regime classification',
         'Action contradicts dominant regime (e.g., BUY in persistent BEARISH regime)'],
        ['Signal Stability', '25%',
         'Inverse of direction-flip rate over historical window',
         'High flip rate indicates unstable signal environment; action blocked'],
    ]
    dims_s = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, colors.HexColor('#F0F4F8')]),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, GOLD),
        ('INNERGRID', (0,0), (-1,-1), 0.25, CGRAY),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ])
    dims_t = Table(dims_table, colWidths=[35*mm, 14*mm, 50*mm, CONTENT_W-99*mm])
    dims_t.setStyle(dims_s)
    story.append(dims_t)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        '<b>Dual-Source History Analysis:</b> The TCV eliminates survivorship bias from '
        'historical trajectory analysis by combining two data sources: '
        'shadow_trade_events (records of all BLOCKED decisions, including the proposed '
        'action that was rejected and the reason for rejection) and paper_trading_trades '
        '(records of all APPROVED decisions that proceeded to execution). The combination '
        'provides a complete, unbiased trajectory that includes both executed and '
        'counterfactual decisions.', body))

    story.append(Paragraph('II. Forward Trajectory Implication (FTI)', h2))
    story.append(Paragraph(
        'The FTI evaluates the near-future implications of a proposed decision across '
        'two prospective risk dimensions:', body))

    fti_items = [
        ('HMM Regime Transition Risk',
         'Using the Hidden Markov Model transition probability matrix calibrated to the '
         'governance system\'s historical regime sequence, the FTI computes the probability '
         'that the current regime transitions to an adverse regime (BEARISH, DOWNTREND, '
         'VOLATILE, STRONG_SELL) within a configurable forward horizon (default: 5 cycles). '
         'A BUY decision proposed in a regime with high probability of adverse transition '
         'is prospectively inadmissible regardless of current-state checkpoint results.'),
        ('Trajectory Terminus Risk',
         'The FTI projects the current behavioral trajectory forward and evaluates the '
         'probability that continuing on this trajectory would produce a governance-prohibited '
         'state (e.g., maximum drawdown breach, regulatory threshold violation) within the '
         'forward horizon. A proposed decision that accelerates convergence toward a '
         'prohibited terminus state is prospectively inadmissible.'),
    ]
    for title, desc in fti_items:
        story.append(Paragraph(f'<b>{title}:</b> {desc}', body))

    # Diagram 3
    story.append(KeepTogether([
        renderPDF.GraphicsFlowable(diagram_hmm(CONTENT_W)),
        Paragraph('FIG. 3 — HMM Regime Transition Risk: VOLATILE regime → 80% probability adverse transition in 5 cycles', caption),
    ]))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph('III. Bilateral Admissibility Determination', h2))
    story.append(Paragraph(
        'The bilateral admissibility determination combines TCV and FTI results '
        'using a conjunction logic: a proposed decision is temporally admissible '
        'only if both TCV returns ADMISSIBLE and FTI returns PASSED. Either module '
        'independently failing is sufficient to block the proposed decision. Both '
        'modules incorporate fail-safe (PASS-THROUGH) behavior: if a module cannot '
        'complete evaluation due to data unavailability, evaluation proceeds but '
        'the fail-safe event is logged for audit and threshold recalibration.', body))

    # Diagram 4
    story.append(KeepTogether([
        renderPDF.GraphicsFlowable(diagram_bilateral(CONTENT_W)),
        Paragraph('FIG. 4 — Bilateral Admissibility Logic: Six outcome combinations; only TCV-ADMISSIBLE + FTI-PASSED allows execution', caption),
    ]))
    story.append(Spacer(1, 4*mm))

    story.append(PageBreak())

    # CLAIMS
    story.append(Paragraph('CLAIMS', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))

    claims = [
        ('1.', 'A bidirectional temporal admissibility system for automated decision governance '
         'comprising: a Trajectory Coherence Validator (TCV) configured to evaluate a proposed '
         'decision against the retrospective behavioral trajectory of the governance system '
         'across at least three weighted dimensions including direction coherence, regime-action '
         'alignment, and signal stability; a Forward Trajectory Implication (FTI) module '
         'configured to evaluate the prospective implications of the proposed decision '
         'using a Hidden Markov Model regime transition matrix to estimate the probability '
         'that the current regime transitions to an adverse regime within a configurable '
         'forward horizon; and a bilateral admissibility determination unit configured to '
         'approve the proposed decision only when both the TCV returns an ADMISSIBLE result '
         'and the FTI returns a PASSED result, and to issue a BLOCK verdict when either '
         'module returns an adverse result.'),
        ('2.', 'The system of claim 1, wherein the Trajectory Coherence Validator evaluates '
         'direction coherence by computing the monotonicity of signal deltas over a configurable '
         'historical window; evaluates regime-action alignment by determining the consistency '
         'of the proposed action with the dominant regime classification observed over the '
         'historical window; and evaluates signal stability by computing the inverse of the '
         'direction-flip rate over the historical window.'),
        ('3.', 'The system of claim 1, wherein the Trajectory Coherence Validator is '
         'configured to perform dual-source history analysis by combining: a first data '
         'source comprising records of blocked governance decisions including the proposed '
         'action and the reason for rejection; and a second data source comprising records '
         'of approved governance decisions that proceeded to execution; wherein the '
         'combination eliminates survivorship bias from the historical trajectory record.'),
        ('4.', 'The system of claim 1, wherein the Forward Trajectory Implication module '
         'computes a regime transition risk score by: identifying the current detected regime; '
         'retrieving from the Hidden Markov Model transition matrix the transition probabilities '
         'from the current regime to each identified adverse regime; computing the aggregate '
         'probability of adverse regime transition within the configurable forward horizon; '
         'and classifying the regime transition risk as LOW, MEDIUM, or HIGH based on the '
         'computed aggregate probability.'),
        ('5.', 'The system of claim 1, wherein the Forward Trajectory Implication module '
         'further comprises a trajectory terminus risk component configured to project the '
         'current behavioral trajectory forward and determine the probability that the '
         'projected trajectory reaches a governance-prohibited state within the configurable '
         'forward horizon.'),
        ('6.', 'The system of claim 1, wherein each of the Trajectory Coherence Validator '
         'and Forward Trajectory Implication module is configured to enter a pass-through '
         'mode when unable to complete its evaluation due to data unavailability; wherein '
         'pass-through mode permits the proposed decision to proceed subject to logging '
         'the fail-safe event; and wherein repeated fail-safe events trigger threshold '
         'recalibration review.'),
        ('7.', 'The system of claim 1, wherein the bidirectional temporal admissibility '
         'system constitutes a governance checkpoint in a multi-checkpoint governance '
         'pipeline, such that a BLOCK verdict from the bilateral admissibility determination '
         'unit is independently sufficient to prevent the proposed decision from reaching '
         'an execution environment, regardless of the pass/block verdicts of any other '
         'checkpoint in the pipeline.'),
        ('8.', 'A method for determining temporal admissibility of proposed automated '
         'governance decisions comprising: evaluating a proposed decision against the '
         'retrospective behavioral trajectory of the governance system to produce a '
         'trajectory coherence result; evaluating the proposed decision against the '
         'prospective regime transition probabilities derived from a Hidden Markov Model '
         'transition matrix to produce a forward trajectory result; issuing an admissibility '
         'determination that approves the proposed decision only when both the trajectory '
         'coherence result is ADMISSIBLE and the forward trajectory result is PASSED; and '
         'blocking the proposed decision when either evaluation result is adverse.'),
        ('9.', 'The method of claim 8, wherein evaluating the retrospective behavioral '
         'trajectory comprises combining records of blocked decisions and records of '
         'approved decisions into a unified trajectory history that includes both '
         'executed and counterfactual governance decisions.'),
        ('10.', 'The method of claim 8, wherein the Hidden Markov Model transition matrix '
         'is calibrated to the historical regime sequence of the governance system and '
         'updated on a configurable refresh schedule, and wherein adverse regimes are '
         'configurable per deployment domain to accommodate domain-specific governance '
         'requirements in financial trading, insurance underwriting, medical AI, real '
         'estate governance, and energy systems.'),
    ]
    for num, text in claims:
        story.append(KeepTogether([
            Paragraph(f'<b>{num}</b> {text}', S('cl', fontName='Helvetica', fontSize=9,
                       textColor=DGRAY, leading=14, spaceAfter=8, leftIndent=10,
                       alignment=TA_JUSTIFY)),
            Spacer(1, 1*mm),
        ]))

    # ABSTRACT
    story.append(HRFlowable(width='100%', thickness=0.5, color=CGRAY, spaceAfter=6))
    story.append(Paragraph('ABSTRACT', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))
    story.append(Paragraph(
        'A Bidirectional Temporal Admissibility System for automated decision governance '
        'extends admissibility determination from the current instant to both the recent '
        'past and the probable near future. A Trajectory Coherence Validator (TCV) '
        'evaluates proposed decisions against three weighted retrospective dimensions — '
        'direction coherence (40%), regime-action alignment (35%), and signal stability '
        '(25%) — using dual-source history analysis combining blocked and approved decision '
        'records to eliminate survivorship bias. A Forward Trajectory Implication (FTI) '
        'module evaluates prospective regime transition risk using a Hidden Markov Model '
        'transition matrix and trajectory terminus risk analysis. A bilateral admissibility '
        'determination approves a proposed decision only when both TCV and FTI concur; '
        'either module independently can block execution. The system provides a governance '
        'guarantee that a decision is coherent with the trajectory from which it emerged '
        'and not likely to become inadmissible within the near-future projection horizon — '
        'a temporal admissibility dimension absent from all prior art governance checkpoint '
        'pipelines. The system is domain-agnostic and applies to financial trading, '
        'insurance underwriting, medical AI, real estate, and energy governance.', body))

    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=CGRAY, spaceAfter=4))
    story.append(Paragraph(
        'Application Reference: OMNIX-PAT-2026-014 | Inventor: Harold Alberto Nunes Rodelo | '
        'OMNIX QUANTUM LTD, United Kingdom | © 2026 OMNIX Quantum Ltd. CONFIDENTIAL.',
        S('ft', fontName='Helvetica', fontSize=7.5, textColor=MGRAY, alignment=TA_CENTER)))

    return story

# ── BUILD PDF ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=20*mm, bottomMargin=18*mm,
        title='OMNIX-PAT-2026-014 Provisional Patent Application',
        author='Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD',
        subject='OMNIX-PAT-2026-014',
        creator='OMNIX Patent Document Generator v2',
    )
    doc.build(build_story(), onFirstPage=on_page, onLaterPages=on_page)
    print(f'PDF generado: {OUTPUT}')
