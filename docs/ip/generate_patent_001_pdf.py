"""
OMNIX-PAT-2026-001 — Governance Control Architecture
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

OUTPUT = 'docs/ip/provisional_applications/pdf_exports/OMNIX_PAT_2026_001_PROVISIONAL.pdf'

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
bodyL   = S('BL',  fontName='Helvetica', fontSize=9.5, textColor=DGRAY,
            spaceAfter=4, leading=14)
bold_b  = S('BB',  fontName='Helvetica-Bold', fontSize=9.5, textColor=DGRAY,
            spaceAfter=3, leading=14)
center  = S('Ctr', fontName='Helvetica', fontSize=9, textColor=MGRAY,
            spaceAfter=4, alignment=TA_CENTER)
caption = S('Cap', fontName='Helvetica-Oblique', fontSize=8.5, textColor=MGRAY,
            spaceAfter=6, alignment=TA_CENTER)
small   = S('Sm',  fontName='Helvetica', fontSize=8.5, textColor=MGRAY,
            spaceAfter=3, leading=12)
key_phrase = S('KP', fontName='Helvetica-Bold', fontSize=11, textColor=NAVY,
               spaceAfter=6, alignment=TA_CENTER,
               backColor=colors.HexColor('#EEF2FF'), borderPad=8)

# ── DIAGRAM HELPERS ────────────────────────────────────────────────────────────
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

# ── DIAGRAM 1: SEQUENTIAL CHECKPOINT PIPELINE ─────────────────────────────────
def diagram_pipeline(width):
    dw, dh = width, 200
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))

    # Title
    label(d, dw/2, dh-14, 'FIG. 1 — Sequential Checkpoint Pipeline (CP-0 through CP-11 + TIE)',
          size=8, color=DGRAY, bold=True, align='middle')

    # Input box
    cx = dw/2
    input_y = dh - 38
    box(d, cx-50, input_y, 100, 22, fill=BLUE, stroke=GOLD, sw=2, rx=4, ry=4)
    label(d, cx, input_y+8, 'PROPOSED ACTION', size=8, color=WHITE, bold=True)
    arrow_down(d, cx, input_y, input_y-18, color=GOLD)

    # Checkpoints row
    cps = ['CP-0','CP-1','CP-2','CP-3','CP-4','CP-5','CP-6','CP-7','CP-8','CP-9','CP-10','CP-11']
    cp_y = input_y - 50
    cp_bw = (dw - 20) / len(cps) - 3
    colors_cp = [NAVY]*12
    colors_cp[0] = colors.HexColor('#1A2E50')

    for i, cp in enumerate(cps):
        bx = 10 + i*(cp_bw+3)
        box(d, bx, cp_y, cp_bw, 28, fill=NAVY, stroke=CGRAY, sw=0.5, rx=2, ry=2)
        label(d, bx+cp_bw/2, cp_y+17, cp, size=7, color=WHITE, bold=True)
        label(d, bx+cp_bw/2, cp_y+6, 'PASS/BLOCK', size=5.5, color=CGRAY)
        if i < len(cps)-1:
            arrow_right(d, bx+cp_bw, bx+cp_bw+3, cp_y+14, color=CGRAY, sw=0.8)

    # Block arrow from any CP
    block_x = 10 + 3*(cp_bw+3) + cp_bw/2
    block_y = cp_y
    label(d, block_x, cp_y-10, 'ANY BLOCK → execution prevented', size=7, color=RED, align='middle')

    # TIE box after pipeline
    tie_y = cp_y - 52
    arrow_down(d, cx, cp_y, tie_y+28, color=GOLD)
    box(d, cx-70, tie_y, 140, 26, fill=PURPLE, stroke=GOLD, sw=2, rx=4, ry=4)
    label(d, cx, tie_y+16, 'TIE — Trajectory Invariant Enforcement', size=8, color=WHITE, bold=True)
    label(d, cx, tie_y+5, 'Post-execution behavioral trajectory audit', size=7, color=colors.HexColor('#DDCCFF'))

    # Execution box
    exec_y = tie_y - 38
    arrow_down(d, cx, tie_y, exec_y+24, color=GOLD)
    box(d, cx-55, exec_y, 110, 22, fill=GREEN, stroke=GOLD, sw=2, rx=4, ry=4)
    label(d, cx, exec_y+8, 'EXECUTION COMMITMENT', size=8, color=WHITE, bold=True)

    # Fail-closed note
    label(d, dw-12, cp_y+40, 'Fail-closed:', size=7, color=RED, align='end')
    label(d, dw-12, cp_y+30, 'BLOCK on error', size=7, color=RED, align='end')

    return d

# ── DIAGRAM 2: DCI — DECISION CONTRADICTION INDEX ─────────────────────────────
def diagram_dci(width):
    dw, dh = width, 195
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))

    label(d, dw/2, dh-14, 'FIG. 2 — Decision Contradiction Index (DCI) — Signal Divergence Detection',
          size=8, color=DGRAY, bold=True, align='middle')

    # 5 signal sources
    signals = ['EMA\nSIGNAL', 'HMM\nREGIME', 'KALMAN\nFILTER', 'NON-MARK\nKERNEL', 'KELLY\nCRITERION']
    sig_colors = [BLUE, NAVY, colors.HexColor('#1A5080'), colors.HexColor('#0D3B6E'), colors.HexColor('#163D5F')]
    sw = (dw - 20) / 5 - 4
    sig_y = dh - 52

    for i, (sig, clr) in enumerate(zip(signals, sig_colors)):
        bx = 10 + i*(sw+4)
        box(d, bx, sig_y, sw, 30, fill=clr, stroke=CGRAY, sw=0.8, rx=3, ry=3)
        lines = sig.split('\n')
        label(d, bx+sw/2, sig_y+20, lines[0], size=7.5, color=WHITE, bold=True)
        label(d, bx+sw/2, sig_y+8, lines[1], size=6.5, color=CGRAY)
        # Arrows converging down
        arrow_down(d, bx+sw/2, sig_y, sig_y-18, color=CGRAY, sw=0.8)

    # DCI computation box
    dci_y = sig_y - 48
    box(d, dw/2-90, dci_y, 180, 26, fill=NAVY, stroke=GOLD, sw=2, rx=4, ry=4)
    label(d, dw/2, dci_y+17, 'PAIRWISE DIVERGENCE COMPUTATION', size=8, color=GOLD, bold=True)
    label(d, dw/2, dci_y+5, 'DCI = mean |Si − Sj| normalized [0, 100]', size=7.5, color=CGRAY)
    arrow_down(d, dw/2, dci_y, dci_y-18, color=GOLD)

    # DCI bands
    bands = [
        (0, 34, GREEN, 'DCI 0–34   ALIGNED', 'Normal evaluation — proceed'),
        (35, 69, AMBER, 'DCI 35–69  TENSIONED', 'Reduced position size'),
        (70, 100, RED, 'DCI 70–100  CONTRADICTORY', 'MANDATORY BLOCK — execution prevented'),
    ]
    band_y = dci_y - 85
    bw = (dw - 20) / 3 - 4
    for i, (lo, hi, clr, title, desc) in enumerate(bands):
        bx = 10 + i*(bw+4)
        box(d, bx, band_y, bw, 40, fill=clr, stroke=CGRAY, sw=1, rx=3, ry=3)
        label(d, bx+bw/2, band_y+28, title, size=7, color=WHITE, bold=True)
        label(d, bx+bw/2, band_y+16, desc, size=6, color=colors.HexColor('#DDDDDD'))
        # highlight CONTRADICTORY
        if i == 2:
            d.add(Rect(bx, band_y, bw, 40, rx=3, ry=3,
                       fillColor=colors.Color(0,0,0,0),
                       strokeColor=GOLD, strokeWidth=2))

    return d

# ── DIAGRAM 3: FAIL-CLOSED GUARANTEE ──────────────────────────────────────────
def diagram_fail_closed(width):
    dw, dh = width, 155
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))

    label(d, dw/2, dh-14, 'FIG. 3 — Fail-Closed Default: Uncertainty → Prevention',
          size=8, color=DGRAY, bold=True, align='middle')

    # Two scenarios side by side
    half = dw/2 - 6

    # LEFT: Normal operation
    label(d, half/2+5, dh-32, 'NORMAL OPERATION', size=8, color=GREEN, bold=True, align='middle')
    box(d, 10, dh-60, half-5, 22, fill=BLUE, stroke=CGRAY, sw=1, rx=3, ry=3)
    label(d, 10+(half-5)/2, dh-52, 'Checkpoint receives inputs', size=7.5, color=WHITE)
    arrow_down(d, 10+(half-5)/2, dh-60, dh-84, color=GREEN, sw=1)
    box(d, 10, dh-108, half-5, 22, fill=GREEN, stroke=CGRAY, sw=1, rx=3, ry=3)
    label(d, 10+(half-5)/2, dh-100, 'Evaluation completes → PASS/BLOCK', size=7, color=WHITE)
    arrow_down(d, 10+(half-5)/2, dh-108, dh-130, color=GREEN, sw=1)
    box(d, 10, dh-152, half-5, 22, fill=GREEN, stroke=GOLD, sw=2, rx=3, ry=3)
    label(d, 10+(half-5)/2, dh-144, 'Verdict applied', size=8, color=WHITE, bold=True)

    # RIGHT: Error scenario
    rx = dw/2+4
    label(d, rx+(half-5)/2, dh-32, 'ERROR / TIMEOUT', size=8, color=RED, bold=True, align='middle')
    box(d, rx, dh-60, half-5, 22, fill=BLUE, stroke=CGRAY, sw=1, rx=3, ry=3)
    label(d, rx+(half-5)/2, dh-52, 'Checkpoint receives inputs', size=7.5, color=WHITE)
    arrow_down(d, rx+(half-5)/2, dh-60, dh-84, color=RED, sw=1)
    box(d, rx, dh-108, half-5, 22, fill=AMBER, stroke=CGRAY, sw=1, rx=3, ry=3)
    label(d, rx+(half-5)/2, dh-100, 'Exception / timeout / data missing', size=7, color=WHITE)
    arrow_down(d, rx+(half-5)/2, dh-108, dh-130, color=RED, sw=1)
    box(d, rx, dh-152, half-5, 22, fill=RED, stroke=GOLD, sw=2, rx=3, ry=3)
    label(d, rx+(half-5)/2, dh-144, 'DEFAULT → BLOCK (fail-closed)', size=8, color=WHITE, bold=True)

    # Divider
    d.add(Line(dw/2, 10, dw/2, dh-22, strokeColor=CGRAY, strokeWidth=1,
               strokeDashArray=[3, 3]))

    return d

# ── DIAGRAM 4: EXECUTION BOUNDARY PRINCIPLE ───────────────────────────────────
def diagram_execution_boundary(width):
    dw, dh = width, 150
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))

    label(d, dw/2, dh-14, 'FIG. 4 — Execution Boundary: Governance at the Point of Irreversibility',
          size=8, color=DGRAY, bold=True, align='middle')

    # Timeline
    tl_y = dh/2
    d.add(Line(20, tl_y, dw-20, tl_y, strokeColor=CGRAY, strokeWidth=1.5))

    phases = [
        (0.08, 'Model\nTraining', CGRAY, False),
        (0.25, 'Model\nDeployment', CGRAY, False),
        (0.45, 'Signal\nGeneration', CGRAY, False),
        (0.65, 'EXECUTION\nBOUNDARY', GOLD, True),
        (0.82, 'Real-World\nAction', RED, False),
    ]
    for frac, lbl, clr, is_key in phases:
        px = 20 + frac*(dw-40)
        r = 7 if is_key else 5
        d.add(Circle(px, tl_y, r, fillColor=clr, strokeColor=clr, strokeWidth=0))
        lines = lbl.split('\n')
        offset = 18 if is_key else 14
        for j, line in enumerate(lines):
            label(d, px, tl_y + offset - j*11, line, size=7 if is_key else 6.5,
                  color=DGRAY if not is_key else NAVY, bold=is_key, align='middle')

    # Governance window bracket
    g_start = 20 + 0.55*(dw-40)
    g_end   = 20 + 0.72*(dw-40)
    bracket_y = tl_y - 20
    d.add(Line(g_start, bracket_y+6, g_start, bracket_y, strokeColor=GOLD, strokeWidth=1.5))
    d.add(Line(g_start, bracket_y, g_end, bracket_y, strokeColor=GOLD, strokeWidth=1.5))
    d.add(Line(g_end, bracket_y, g_end, bracket_y+6, strokeColor=GOLD, strokeWidth=1.5))
    label(d, (g_start+g_end)/2, bracket_y-10, 'OMNIX Governance Window',
          size=7.5, color=GOLD, bold=True, align='middle')

    # Prior art validation note
    box(d, 10, 12, 140, 22, fill=colors.HexColor('#EEEEEE'), stroke=CGRAY, sw=0.5, rx=2, ry=2)
    label(d, 80, 26, 'Prior art validates HERE (too early)', size=7, color=RED, align='middle')
    label(d, 80, 15, '→ conditions may change before execution', size=6.5, color=MGRAY, align='middle')

    # OMNIX validates note
    box(d, dw-155, 12, 145, 22, fill=colors.HexColor('#E8F5EE'), stroke=GREEN, sw=1, rx=2, ry=2)
    label(d, dw-82, 26, 'OMNIX validates AT execution boundary', size=7, color=GREEN, align='middle')
    label(d, dw-82, 15, '→ final verification before irreversibility', size=6.5, color=MGRAY, align='middle')

    return d

# ── HEADER / FOOTER ────────────────────────────────────────────────────────────
class HeaderFooter(Flowable):
    def __init__(self, page_w, page_h, is_cover=False):
        Flowable.__init__(self)
        self.page_w = page_w
        self.page_h = page_h
        self.is_cover = is_cover
        self.width = 0
        self.height = 0

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
    canvas_obj.drawRightString(w-RM, h-9*mm, 'OMNIX-PAT-2026-001')
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
        'CONFIDENTIAL — PATENT PENDING — OMNIX-PAT-2026-001 — Filed: April 19, 2026')
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
        'GOVERNANCE CONTROL ARCHITECTURE FOR AUTOMATED DECISION SYSTEMS '
        'WITH SEQUENTIAL CHECKPOINT PIPELINE, DECISION CONTRADICTION INDEX, '
        'AND EXECUTION BOUNDARY ENFORCEMENT',
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
        ['Docket Number:', 'OMNIX-PAT-2026-001'],
        ['Inventor:', 'Harold Alberto Nunes Rodelo'],
        ['Applicant:', 'OMNIX QUANTUM LTD (United Kingdom)'],
        ['Entity Status:', 'Micro Entity — 37 C.F.R. § 1.29'],
        ['Filing Basis:', '35 U.S.C. § 111(b) — Provisional Application'],
        ['Date Prepared:', 'April 19, 2026'],
        ['Date of Filing:', 'April 19, 2026'],
        ['Related Applications:', 'OMNIX-PAT-2026-002, OMNIX-PAT-2026-003'],
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
        'The present invention relates to computer-implemented systems and methods for governing '
        'high-stakes automated decisions. More specifically, the invention relates to a domain-agnostic '
        'governance engine that enforces decision admissibility through a sequential pipeline of '
        'independent, veto-authority checkpoints; a counterfactual shadow portfolio system for '
        'continuous self-calibration of risk management filters; and a Decision Contradiction Index '
        '(DCI) for detecting internal signal divergence prior to execution commitment.', body))

    # BACKGROUND
    story.append(Paragraph('BACKGROUND OF THE INVENTION', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))
    story.append(Paragraph(
        'Automated decision systems operating in high-stakes environments — financial trading, '
        'insurance underwriting, medical AI, energy grid management — are capable of generating '
        'and executing large volumes of consequential decisions at speeds that preclude human '
        'review. The governance of such systems presents a fundamental engineering challenge: '
        'how to enforce admissibility requirements at the precise moment a proposed action '
        'would transition from a recommendation into an irreversible real-world commitment.', body))

    story.append(Paragraph('Critical Incidents Illustrating the Governance Gap', h2))
    incidents = [
        ('Knight Capital Group (August 1, 2012)',
         'Knight Capital lost approximately $440 million USD in 45 minutes after a legacy '
         'software module generated thousands of unintended orders for 150 stocks. No architectural '
         'mechanism could detect the divergence between intended and actual system behavior at '
         'the point of execution. The loss effectively bankrupted the firm.'),
        ('Flash Crash (May 6, 2010)',
         'The U.S. equity markets experienced a rapid 1,000-point drop (≈9%) in minutes. '
         'Automated trading algorithms responded in mutually reinforcing patterns with no '
         'governance layer capable of detecting the systemic coherence failure.'),
        ('Zillow Offers Algorithm (2021)',
         'Zillow ceased its iBuying program after its price prediction system accumulated '
         'overvalued properties, resulting in a $304 million write-down and 25% workforce '
         'reduction. The system continued to make commitments contradicting available market '
         'signals, with no checkpoint capable of detecting and blocking the divergence.'),
    ]
    for title, desc in incidents:
        story.append(Paragraph(f'<b>{title}:</b> {desc}', body))

    story.append(Paragraph('Deficiencies of Prior Art', h2))
    deficiencies = [
        ('Post-Hoc Audit Systems', 'Record decisions for subsequent review — do not prevent harm, only create records after harm has occurred.'),
        ('Single-Layer Risk Limits', 'Apply a single threshold check — structurally fragile; if the limit check is incorrect or corrupted, no alternative enforcement layer exists.'),
        ('Consensus Aggregation', 'Aggregate signals into a composite score, masking internal signal disagreement by design — a fatal flaw when signals strongly contradict.'),
        ('Static Threshold Systems', 'Apply fixed thresholds calibrated at deployment; do not adapt to changed market conditions.'),
        ('Human Review Queues', 'Incompatible with high-frequency automated environments where review latency is operationally unacceptable.'),
    ]
    for dt, dd in deficiencies:
        story.append(Paragraph(f'<b>{dt}:</b> {dd}', body))

    # SUMMARY + DIAGRAM 1
    story.append(Paragraph('SUMMARY OF THE INVENTION', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))
    story.append(Paragraph(
        'The present invention provides a multi-checkpoint governance architecture that enforces '
        'decision admissibility at the execution boundary through five integrated components:', body))

    components = [
        ('A', 'Sequential Checkpoint Pipeline (CP-0 through CP-11)',
         'A pipeline of twelve independent, sequentially-ordered checkpoints, each with independent '
         'veto authority. A BLOCK verdict from any single checkpoint prevents execution regardless '
         'of the verdicts of all other checkpoints. Default verdict on error: BLOCK (fail-closed).'),
        ('B', 'Decision Contradiction Index (DCI)',
         'A real-time signal divergence detector that computes pairwise divergence across a minimum '
         'of five independent signal sources. A DCI score of 70–100 (CONTRADICTORY classification) '
         'constitutes a mandatory BLOCK regardless of individual signal values.'),
        ('C', 'Counterfactual Shadow Portfolio',
         'A parallel shadow system that receives every proposed action — approved and blocked — '
         'enabling continuous calibration of governance threshold effectiveness without survivorship bias.'),
        ('D', 'Trajectory Invariant Enforcement (TIE)',
         'A post-execution behavioral trajectory audit layer that verifies the resulting system '
         'state is consistent with the system\'s established behavioral trajectory. Triggers '
         'circuit-breaker protocols on inadmissible deviation.'),
        ('E', 'Cryptographic Decision Trace',
         'A post-quantum cryptographically sealed (Dilithium-3 / ML-DSA-65) record of every '
         'checkpoint evaluation, verdict, and final admissibility determination.'),
    ]
    comp_data = [[Paragraph(f'<b>Component {c}</b>', S('ch', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
                  Paragraph(f'<b>{n}</b>', S('cn', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
                  Paragraph(d, S('cd', fontName='Helvetica', fontSize=8.5, textColor=WHITE, leading=12))]
                 for c, n, d in components]
    comp_t = Table(comp_data, colWidths=[15*mm, 42*mm, CONTENT_W-57*mm])
    comp_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [NAVY, BLUE]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
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
        renderPDF.GraphicsFlowable(diagram_pipeline(CONTENT_W)),
        Paragraph('FIG. 1 — Sequential Checkpoint Pipeline with Fail-Closed TIE Post-Execution Audit', caption),
    ]))
    story.append(Spacer(1, 4*mm))

    # Diagram 2
    story.append(KeepTogether([
        renderPDF.GraphicsFlowable(diagram_dci(CONTENT_W)),
        Paragraph('FIG. 2 — Decision Contradiction Index: 5-Source Pairwise Divergence → Three Classification Bands', caption),
    ]))

    story.append(PageBreak())

    # DETAILED DESCRIPTION
    story.append(Paragraph('DETAILED DESCRIPTION OF THE INVENTION', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))

    story.append(Paragraph('I. Execution Boundary Principle', h2))
    story.append(Paragraph(
        'The System is designed to operate at the execution boundary — the precise computational '
        'point at which a proposed action transitions from a computed recommendation into an '
        'irreversible real-world commitment. This placement is architecturally fundamental. '
        'A proposed action that was valid at time T may be inadmissible at time T+1 if conditions '
        'have changed; the System enforces admissibility at T+1, not at T.', body))

    # Diagram 3
    story.append(KeepTogether([
        renderPDF.GraphicsFlowable(diagram_fail_closed(CONTENT_W)),
        Paragraph('FIG. 3 — Fail-Closed Guarantee: Checkpoint error defaults to BLOCK, never PASS', caption),
    ]))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph('II. Checkpoint Pipeline Architecture', h2))
    story.append(Paragraph(
        'The sequential checkpoint pipeline comprises twelve checkpoints (CP-0 through CP-11) '
        'arranged in a predetermined sequential order. Each checkpoint: (a) operates independently '
        'of all other checkpoints; (b) has unilateral veto authority — its BLOCK verdict is '
        'individually sufficient to prevent execution; (c) defaults to BLOCK on any evaluation '
        'failure (fail-closed); and (d) records its evaluation in the cryptographic decision trace.', body))

    cp_table_data = [
        [Paragraph('<b>CP</b>', S('ch', fontName='Helvetica-Bold', fontSize=8.5, textColor=WHITE)),
         Paragraph('<b>Name</b>', S('ch', fontName='Helvetica-Bold', fontSize=8.5, textColor=WHITE)),
         Paragraph('<b>Function</b>', S('ch', fontName='Helvetica-Bold', fontSize=8.5, textColor=WHITE))],
        ['CP-0', 'Signal Completeness', 'Verifies all required governance signals are present and within freshness thresholds'],
        ['CP-1', 'Data Integrity', 'Verifies cryptographic integrity of all input data using PQC hash verification'],
        ['CP-2', 'Regime Classification', 'Evaluates current market/operational regime classification and confidence'],
        ['CP-3', 'Probabilistic Confidence', 'Verifies composite signal confidence meets minimum threshold'],
        ['CP-4', 'Risk Exposure', 'Evaluates proposed action against current portfolio/system risk exposure limits'],
        ['CP-5', 'Volatility Adjustment', 'Adjusts evaluation thresholds based on current volatility regime'],
        ['CP-6', 'DCI Evaluation', 'Computes Decision Contradiction Index across all signal sources; CONTRADICTORY → BLOCK'],
        ['CP-7', 'Non-Markovian Memory', 'Evaluates action against historical memory kernel regime classification'],
        ['CP-8', 'Kelly Position Sizing', 'Verifies proposed action size does not exceed Kelly-criterion-derived maximum'],
        ['CP-9', 'Drawdown Protection', 'Evaluates action against maximum allowable drawdown constraints'],
        ['CP-10', 'Correlation Exposure', 'Evaluates cross-asset or cross-system correlation concentration risk'],
        ['CP-11', 'Jurisdiction Compliance', 'Verifies regulatory admissibility for jurisdiction, asset class, and operation type'],
    ]
    cp_s = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, colors.HexColor('#F5F7FA')]),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,1), (0,-1), NAVY),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, GOLD),
        ('INNERGRID', (0,0), (-1,-1), 0.25, CGRAY),
    ])
    cp_t = Table(cp_table_data, colWidths=[12*mm, 35*mm, CONTENT_W-47*mm])
    cp_t.setStyle(cp_s)
    story.append(cp_t)
    story.append(Spacer(1, 4*mm))

    # Diagram 4
    story.append(KeepTogether([
        renderPDF.GraphicsFlowable(diagram_execution_boundary(CONTENT_W)),
        Paragraph('FIG. 4 — Execution Boundary: Prior art validates at training/deployment; OMNIX validates at irreversibility point', caption),
    ]))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph('III. Decision Contradiction Index (DCI)', h2))
    story.append(Paragraph(
        'The DCI is computed as the mean pairwise absolute divergence across a minimum of five '
        'independent signal sources, normalized to the interval [0, 100]. Signal sources include: '
        'EMA-based trend signal, Hidden Markov Model regime classifier, Kalman Filter state '
        'estimator, Non-Markovian Memory Kernel regime classifier, and Kelly Criterion position '
        'signal. The DCI provides a single scalar metric of internal signal coherence:', body))

    dci_data = [
        [Paragraph('<b>DCI Range</b>', S('dh', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
         Paragraph('<b>Classification</b>', S('dh', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
         Paragraph('<b>Governance Action</b>', S('dh', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE))],
        ['0 – 34', 'ALIGNED', 'Normal evaluation proceeds through remaining checkpoints'],
        ['35 – 69', 'TENSIONED', 'Position size reduced; evaluation proceeds with heightened scrutiny'],
        ['70 – 100', 'CONTRADICTORY', 'MANDATORY BLOCK — execution prevented regardless of other checkpoint verdicts'],
    ]
    dci_s = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#FDECEA')),
        ('TEXTCOLOR', (0,3), (-1,3), RED),
        ('FONTNAME', (0,3), (-1,3), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0,1), (-1,2), [WHITE, colors.HexColor('#F5F7FA')]),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1.5, GOLD),
        ('INNERGRID', (0,0), (-1,-1), 0.3, CGRAY),
    ])
    dci_t = Table(dci_data, colWidths=[25*mm, 35*mm, CONTENT_W-60*mm])
    dci_t.setStyle(dci_s)
    story.append(dci_t)
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph('IV. Counterfactual Shadow Portfolio', h2))
    story.append(Paragraph(
        'A shadow portfolio system maintains a parallel record of all proposed actions — both '
        'those approved and those blocked — enabling continuous calibration of governance '
        'threshold effectiveness. Because both approved and blocked decisions are tracked, '
        'the calibration system operates without survivorship bias: it evaluates not only '
        'the outcomes of executed decisions but also the counterfactual outcomes of decisions '
        'that were blocked. Thresholds are adjusted based on observed filter accuracy over '
        'rolling historical windows, subject to mandatory human review before any threshold change.', body))

    story.append(PageBreak())

    # CLAIMS
    story.append(Paragraph('CLAIMS', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))
    story.append(Paragraph(
        'What is claimed is:', body))

    claims = [
        ('1.', 'A computer-implemented governance system for automated decision enforcement, comprising: '
         'a sequential checkpoint pipeline comprising a plurality of independent checkpoints, each '
         'checkpoint configured to evaluate a proposed automated action against assigned admissibility '
         'criteria and issue a verdict of PASS or BLOCK; wherein a BLOCK verdict from any single '
         'checkpoint is independently sufficient to prevent the proposed action from reaching an '
         'execution environment; wherein each checkpoint is configured to issue a BLOCK verdict as '
         'a default response when unable to complete its evaluation; and a cryptographic record '
         'generator configured to produce a post-quantum cryptographically sealed record of the '
         'evaluation prior to any execution commitment.'),
        ('2.', 'The system of claim 1, wherein the sequential checkpoint pipeline comprises at least '
         'twelve checkpoints arranged in a predetermined sequential order, including a signal '
         'completeness checkpoint, a data integrity checkpoint, a regime classification checkpoint, '
         'a probabilistic confidence checkpoint, a risk exposure checkpoint, a volatility adjustment '
         'checkpoint, a Decision Contradiction Index checkpoint, a non-Markovian memory checkpoint, '
         'a position sizing checkpoint, a drawdown protection checkpoint, a correlation exposure '
         'checkpoint, and a jurisdictional compliance checkpoint.'),
        ('3.', 'The system of claim 1, further comprising a Decision Contradiction Index (DCI) '
         'computation module configured to: receive signals from at least five independent signal '
         'sources; compute pairwise absolute divergence across all signal source pairs; produce a '
         'normalized DCI score in the range [0, 100]; and issue a mandatory BLOCK verdict when '
         'the DCI score meets or exceeds a CONTRADICTORY threshold, wherein the BLOCK verdict '
         'is effective regardless of the verdicts of any other checkpoint.'),
        ('4.', 'The system of claim 3, wherein the at least five independent signal sources '
         'comprise an exponential moving average trend signal, a Hidden Markov Model regime '
         'classifier, a Kalman Filter state estimator, a Non-Markovian Memory Kernel regime '
         'classifier, and a Kelly Criterion position signal.'),
        ('5.', 'The system of claim 1, further comprising a counterfactual shadow portfolio '
         'system configured to maintain a parallel record of all proposed actions including '
         'both approved and blocked actions, and to calibrate governance threshold parameters '
         'based on the observed outcomes of both approved and blocked actions without '
         'survivorship bias.'),
        ('6.', 'The system of claim 1, further comprising a Trajectory Invariant Enforcement '
         '(TIE) layer configured to verify, after execution commitment, that the resulting '
         'system state is consistent with the system\'s established behavioral trajectory; '
         'and to trigger circuit-breaker protocols when the resulting state represents an '
         'inadmissible deviation.'),
        ('7.', 'The system of claim 1, wherein the post-quantum cryptographically sealed '
         'record comprises a digital signature generated using a lattice-based signature '
         'algorithm standardized by NIST under FIPS 204 (ML-DSA), covering all checkpoint '
         'evaluations, their verdicts, and the final admissibility determination.'),
        ('8.', 'A computer-implemented method for governing automated decisions at an execution '
         'boundary, comprising: receiving a proposed action from a decision generation subsystem; '
         'sequentially evaluating the proposed action through a plurality of independent '
         'enforcement units, each having independent veto authority; blocking the proposed '
         'action from execution if any enforcement unit issues a BLOCK verdict; defaulting to '
         'BLOCK if any enforcement unit is unable to complete its evaluation; and generating '
         'a tamper-evident record of the complete evaluation prior to any execution commitment.'),
        ('9.', 'The method of claim 8, further comprising computing a Decision Contradiction '
         'Index by determining pairwise divergence across at least five independent signal '
         'sources; and issuing a mandatory BLOCK when the computed index exceeds a '
         'CONTRADICTORY threshold.'),
        ('10.', 'The method of claim 8, wherein the execution boundary is the computational '
         'point at which the proposed action would transition from a computed recommendation '
         'into an instruction transmitted to an execution environment causing an irreversible '
         'real-world action, and wherein all evaluation units complete their evaluations '
         'before any such instruction is transmitted.'),
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
        'A governance control architecture for automated decision systems enforces decision '
        'admissibility at the execution boundary — the precise computational point at which '
        'a proposed action becomes irreversible — through a sequential pipeline of independent, '
        'fail-closed checkpoints (CP-0 through CP-11), each with unilateral veto authority. '
        'A Decision Contradiction Index (DCI) detects internal signal divergence across a '
        'minimum of five independent sources and mandatorily blocks execution when pairwise '
        'divergence exceeds the CONTRADICTORY threshold. A counterfactual shadow portfolio '
        'system enables continuous threshold calibration without survivorship bias by tracking '
        'both approved and blocked decisions. A Trajectory Invariant Enforcement (TIE) layer '
        'provides post-execution behavioral trajectory audit with circuit-breaker capability. '
        'All checkpoint evaluations are sealed in a post-quantum cryptographic decision trace '
        '(ML-DSA-65 / Dilithium-3). The architecture is domain-agnostic and applies to '
        'financial trading, insurance underwriting, medical AI, energy governance, and '
        'autonomous agent systems.', body))

    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=CGRAY, spaceAfter=4))
    story.append(Paragraph(
        'Application Reference: OMNIX-PAT-2026-001 | Inventor: Harold Alberto Nunes Rodelo | '
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
        title='OMNIX-PAT-2026-001 Provisional Patent Application',
        author='Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD',
        subject='OMNIX-PAT-2026-001',
        creator='OMNIX Patent Document Generator v2',
    )
    doc.build(build_story(), onFirstPage=on_page, onLaterPages=on_page)
    print(f'PDF generado: {OUTPUT}')
