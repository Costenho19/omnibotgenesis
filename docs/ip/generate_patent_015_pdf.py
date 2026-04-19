"""
OMNIX-PAT-2026-015 — Structural Admissibility Engine
Full provisional patent PDF with diagrams and complete specification.
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

OUTPUT = 'docs/ip/provisional_applications/pdf_exports/OMNIX_PAT_2026_015_PROVISIONAL.pdf'

# ── COLORS ────────────────────────────────────────────────────────────────────
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

W, H = A4
LM = 22*mm
RM = 22*mm
CONTENT_W = W - LM - RM

# ── STYLES ────────────────────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, **kw)

h1      = S('H1',  fontName='Helvetica-Bold', fontSize=13, textColor=NAVY,
            spaceAfter=5, spaceBefore=14, borderPad=0)
h2      = S('H2',  fontName='Helvetica-Bold', fontSize=11, textColor=NAVY,
            spaceAfter=4, spaceBefore=10)
h3      = S('H3',  fontName='Helvetica-Bold', fontSize=10, textColor=DGRAY,
            spaceAfter=3, spaceBefore=7)
body    = S('Body',fontName='Helvetica', fontSize=9.5, textColor=DGRAY,
            spaceAfter=5, leading=14, alignment=TA_JUSTIFY)
bodyL   = S('BL',  fontName='Helvetica', fontSize=9.5, textColor=DGRAY,
            spaceAfter=4, leading=14, alignment=TA_LEFT)
bold_b  = S('BB',  fontName='Helvetica-Bold', fontSize=9.5, textColor=DGRAY,
            spaceAfter=3, leading=14)
center  = S('Ctr', fontName='Helvetica', fontSize=9, textColor=MGRAY,
            spaceAfter=4, alignment=TA_CENTER)
small   = S('Sm',  fontName='Helvetica', fontSize=8.5, textColor=MGRAY,
            spaceAfter=3, leading=12)
code_s  = S('Cod', fontName='Courier', fontSize=8, textColor=DGRAY,
            spaceAfter=4, leading=12, leftIndent=8,
            backColor=colors.HexColor('#F0F0F0'))
footer_s= S('Ftr', fontName='Helvetica', fontSize=7.5, textColor=MGRAY,
            alignment=TA_CENTER)
caption = S('Cap', fontName='Helvetica-Oblique', fontSize=8.5, textColor=MGRAY,
            spaceAfter=6, alignment=TA_CENTER)
note    = S('Note',fontName='Helvetica-Oblique', fontSize=9, textColor=MGRAY,
            spaceAfter=4, leading=13, leftIndent=8)
key_phrase = S('KP', fontName='Helvetica-Bold', fontSize=11, textColor=NAVY,
               spaceAfter=6, alignment=TA_CENTER,
               backColor=colors.HexColor('#EEF2FF'),
               borderPad=8)

# ── DIAGRAM HELPERS ───────────────────────────────────────────────────────────
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

# ── DIAGRAM 1: FOUR-LAYER ARCHITECTURE ────────────────────────────────────────
def diagram_four_layers(width):
    dw, dh = width, 180
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))

    layers = [
        (GREEN,  'LAYER 0',  'Structural Admissibility Engine (SAE)',
         'Pre-pipeline schema validation — Zero-bypass boundary', ''),
        (NAVY,   'LAYER 1',  'OMNIX Runtime Pipeline',
         'CP-0 through CP-11 + TIE — Sequential veto-authority checkpoints', ''),
        (BLUE,   'LAYER 2',  'Trajectory Invariant Engine (TIE)',
         'Retrospective + prospective temporal admissibility', ''),
        (MGRAY,  'LAYER 3',  'Evidence & Receipt Layer',
         'PQC-signed immutable audit receipt', ''),
    ]

    bh = 32
    gap = 4
    start_y = dh - 10 - bh
    bw = dw - 20

    for i, (clr, lnum, lname, ldesc, _) in enumerate(layers):
        y = start_y - i*(bh+gap)
        box(d, 10, y, bw, bh, fill=clr, stroke=GOLD if i==0 else CGRAY, sw=2 if i==0 else 1)
        label(d, 22, y+bh-13, lnum, size=8, bold=True, color=GOLD if i==0 else WHITE)
        label(d, 22, y+bh-23, lname, size=9, bold=True, color=WHITE if i<3 else WHITE)
        label(d, 22, y+7, ldesc, size=7.5, color=colors.HexColor('#CCCCCC'), bold=False)
        if i < 3:
            ax = bw/2 + 10
            ay = y - gap
            d.add(Line(ax, y, ax, y-gap+1, strokeColor=GOLD, strokeWidth=1.5))
            d.add(Polygon([ax-4, y-gap+5, ax+4, y-gap+5, ax, y-gap],
                          fillColor=GOLD, strokeColor=GOLD, strokeWidth=0))

    label(d, dw/2, 4, 'Figure 1 — Four-Layer Governance Architecture (OMNIX-PAT-2026-015)',
          size=7.5, color=MGRAY, align='middle')
    return d

# ── DIAGRAM 2: RUNTIME vs STRUCTURAL ──────────────────────────────────────────
def diagram_comparison(width):
    dw, dh = width, 160
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))

    half = dw / 2 - 6
    # LEFT — Prior Art (runtime)
    box(d, 8, 120, half, 28, fill=RED, stroke=CGRAY, sw=1)
    label(d, 8+half/2, 139, 'PRIOR ART: Runtime Interception', size=8, bold=True, color=WHITE)
    label(d, 8+half/2, 128, 'Input exists before evaluation', size=7.5, color=colors.HexColor('#FFCCCC'))

    boxes_l = ['Input', 'CP-01', 'CP-02', '...', 'CP-N', 'BLOCK?']
    bw_l = (half - 10) / len(boxes_l) - 2
    for j, b in enumerate(boxes_l):
        bx = 10 + j*(bw_l+2)
        by = 80
        clr = RED if b == 'BLOCK?' else colors.HexColor('#8B0000') if b in ('CP-01','CP-02','...','CP-N') else NAVY
        box(d, bx, by, bw_l, 28, fill=clr, stroke=CGRAY, sw=0.5, rx=2, ry=2)
        label(d, bx+bw_l/2, by+10, b, size=7, color=WHITE, bold=(b=='BLOCK?'))
        if j < len(boxes_l)-1:
            arrow_right(d, bx+bw_l, bx+bw_l+2, by+14, color=CGRAY, sw=1)

    label(d, 8+half/2, 64, 'Invalid request traverses pipeline before blocking.', size=7.5, color=RED, align='middle')
    label(d, 8+half/2, 54, 'Component failure = bypass.', size=7.5, color=RED, align='middle')

    # RIGHT — SAE (structural)
    rx = dw/2 + 4
    box(d, rx, 120, half, 28, fill=GREEN, stroke=GOLD, sw=2)
    label(d, rx+half/2, 139, 'PRESENT INVENTION: Structural Admissibility', size=8, bold=True, color=WHITE)
    label(d, rx+half/2, 128, 'Invalid input cannot be constructed', size=7.5, color=colors.HexColor('#CCFFCC'))

    steps = ['Proposed\nRequest', 'SAV\nLayer 0', 'EvaluationRequest\nObject', 'Pipeline\nLayer 1+']
    bw_r = (half - 10) / len(steps) - 2
    for j, b in enumerate(steps):
        bx = rx + 2 + j*(bw_r+2)
        by = 80
        clr = GREEN if j == 1 else NAVY if j == 2 else MGRAY
        box(d, bx, by, bw_r, 28, fill=clr, stroke=GOLD if j==1 else CGRAY, sw=1.5 if j==1 else 0.5, rx=2, ry=2)
        label(d, bx+bw_r/2, by+12, b.split('\n')[0], size=6.5, color=WHITE, bold=(j==1))
        if len(b.split('\n'))>1:
            label(d, bx+bw_r/2, by+5, b.split('\n')[1], size=6.5, color=WHITE)
        if j < len(steps)-1:
            arrow_right(d, bx+bw_r, bx+bw_r+2, by+14, color=GOLD if j==0 else CGRAY, sw=1)

    label(d, rx+half/2, 64, 'Inadmissible request never becomes a system object.', size=7.5, color=GREEN, align='middle')
    label(d, rx+half/2, 54, 'Zero-bypass: silence is impossible.', size=7.5, color=GREEN, align='middle')

    # Divider
    d.add(Line(dw/2, 10, dw/2, 155, strokeColor=CGRAY, strokeWidth=0.5, strokeDashArray=[3,3]))

    label(d, dw/2, 4, 'Figure 2 — Runtime Interception (Prior Art) vs. Structural Admissibility (Present Invention)',
          size=7.5, color=MGRAY, align='middle')
    return d

# ── DIAGRAM 3: CONSTRAINT SCHEMA HIERARCHY ────────────────────────────────────
def diagram_constraint_schema(width):
    dw, dh = width, 200
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))

    # Root
    rw, rh = 180, 28
    rx = dw/2 - rw/2
    ry = dh - 38
    box(d, rx, ry, rw, rh, fill=NAVY, stroke=GOLD, sw=2, rx=4, ry=4)
    label(d, dw/2, ry+18, 'Structural Constraint Schema (SCS)', size=8.5, bold=True, color=GOLD)
    label(d, dw/2, ry+8, 'Unified Constraint Registry', size=7.5, color=WHITE)

    # Four branches
    branches = [
        (BLUE,  'Class A\nJurisdiction-Asset', 'JA_CONSTRAINT(J, A)\nPERMITTED / PROHIBITED /\nCONDITIONAL'),
        (NAVY,  'Class B\nJurisdiction-Op', 'JO_CONSTRAINT(J, O)\nSpot / Leveraged /\nDerivatives / Short'),
        (GREEN, 'Class C\nEthical Compliance', 'Sharia / ESG /\nOFAC-UN-EU\nSanctions lists'),
        (MGRAY, 'Class D\nClient-Specific', 'Per-client overrides\nRestrict only —\ncannot expand'),
    ]
    bw = (dw - 20) / 4 - 4
    bh = 52
    by = 80

    for i, (clr, title, detail) in enumerate(branches):
        bx = 10 + i*(bw+4)
        box(d, bx, by, bw, bh, fill=clr, stroke=CGRAY, sw=0.8, rx=3, ry=3)
        lines = title.split('\n')
        label(d, bx+bw/2, by+bh-12, lines[0], size=7.5, bold=True, color=GOLD if clr!=MGRAY else WHITE)
        label(d, bx+bw/2, by+bh-22, lines[1] if len(lines)>1 else '', size=7, color=WHITE, bold=True)
        for li, dl in enumerate(detail.split('\n')):
            label(d, bx+bw/2, by+bh-34-li*10, dl, size=6.5, color=colors.HexColor('#DDDDDD'))

        # Arrow from root
        cx = bx + bw/2
        d.add(Line(dw/2, ry, cx, by+bh, strokeColor=CGRAY, strokeWidth=0.8, strokeDashArray=[2,2]))

    # Composition node
    cw, ch = 160, 26
    cx2 = dw/2 - cw/2
    cy2 = 28
    box(d, cx2, cy2, cw, ch, fill=GREEN, stroke=GOLD, sw=1.5, rx=3, ry=3)
    label(d, dw/2, cy2+17, 'ADMISSIBILITY(P) = ADMISSIBLE', size=8, bold=True, color=WHITE)
    label(d, dw/2, cy2+7, 'iff ALL applicable constraints pass', size=7.5, color=colors.HexColor('#CCFFCC'))

    for i in range(4):
        bx = 10 + i*((dw-20)/4)
        d.add(Line(bx+(dw-20)/8, by, dw/2, cy2+ch,
                   strokeColor=CGRAY, strokeWidth=0.8, strokeDashArray=[2,2]))

    label(d, dw/2, 4, 'Figure 3 — Structural Constraint Schema Hierarchy and Composition',
          size=7.5, color=MGRAY, align='middle')
    return d

# ── DIAGRAM 4: SAV EVALUATION FLOW ────────────────────────────────────────────
def diagram_sav_flow(width):
    dw, dh = width, 230
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))

    # Flow boxes
    bw, bh = 160, 28
    cx = dw/2

    steps = [
        (dh-30,  MGRAY,  'Proposed Decision Request P', False),
        (dh-80,  NAVY,   'Retrieve Applicable Constraints', False),
        (dh-130, GREEN,  'Evaluate: C_i(P) for all C_i in SCS', True),
        (dh-175, RED,    'Any violation found?', True),
    ]

    for y, clr, txt, bold in steps:
        box(d, cx-bw/2, y, bw, bh, fill=clr, stroke=GOLD if bold else CGRAY, sw=2 if bold else 1, rx=4, ry=4)
        label(d, cx, y+18, txt, size=8, bold=bold, color=WHITE)

    # Arrows between steps
    for i in range(len(steps)-1):
        y1 = steps[i][0]
        y2 = steps[i+1][0] + bh
        arrow_down(d, cx, y1, y2, color=GOLD, sw=1.5)

    # Diamond decision
    decision_y = dh - 175
    # YES branch — left
    box(d, 10, decision_y-40, 110, 28, fill=RED, stroke=CGRAY, sw=1, rx=4, ry=4)
    label(d, 65, decision_y-26, 'YES: Return SRCP', size=8, bold=True, color=WHITE)
    label(d, 65, decision_y-36, 'Structured Rejection Record', size=7, color=colors.HexColor('#FFCCCC'))
    d.add(Line(cx-bw/2, decision_y+14, 120, decision_y+14, strokeColor=RED, strokeWidth=1.5))
    d.add(Line(120, decision_y+14, 120, decision_y-12, strokeColor=RED, strokeWidth=1.5))
    d.add(Polygon([116, decision_y-12, 124, decision_y-12, 120, decision_y-16],
                  fillColor=RED, strokeColor=RED, strokeWidth=0))
    label(d, cx-bw/2-12, decision_y+18, 'YES', size=8, bold=True, color=RED, align='middle')

    # NO branch — right (continue)
    box(d, dw-120, decision_y-40, 110, 28, fill=GREEN, stroke=GOLD, sw=2, rx=4, ry=4)
    label(d, dw-65, decision_y-26, 'NO: Construct', size=8, bold=True, color=WHITE)
    label(d, dw-65, decision_y-36, 'EvaluationRequest Object', size=7, color=colors.HexColor('#CCFFCC'))
    d.add(Line(cx+bw/2, decision_y+14, dw-120, decision_y+14, strokeColor=GREEN, strokeWidth=1.5))
    d.add(Line(dw-120, decision_y+14, dw-120, decision_y-12, strokeColor=GREEN, strokeWidth=1.5))
    d.add(Polygon([dw-124, decision_y-12, dw-116, decision_y-12, dw-120, decision_y-16],
                  fillColor=GREEN, strokeColor=GREEN, strokeWidth=0))
    label(d, cx+bw/2+12, decision_y+18, 'NO', size=8, bold=True, color=GREEN, align='middle')

    # Arrow from EvaluationRequest to pipeline
    box(d, dw-120, decision_y-85, 110, 28, fill=NAVY, stroke=GOLD, sw=1.5, rx=4, ry=4)
    label(d, dw-65, decision_y-71, 'Forward to', size=8, color=WHITE)
    label(d, dw-65, decision_y-81, 'Layer 1 Pipeline', size=8, bold=True, color=GOLD)
    d.add(Line(dw-65, decision_y-40, dw-65, decision_y-57,
               strokeColor=GREEN, strokeWidth=1.5))
    d.add(Polygon([dw-69, decision_y-57, dw-61, decision_y-57, dw-65, decision_y-61],
                  fillColor=GREEN, strokeColor=GREEN, strokeWidth=0))

    label(d, dw/2, 4, 'Figure 4 — Structural Admissibility Validator (SAV) Evaluation Flow',
          size=7.5, color=MGRAY, align='middle')
    return d

# ── DIAGRAM 5: STRUCTURED REJECTION RECORD ────────────────────────────────────
def diagram_srcp(width):
    dw, dh = width, 150
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=colors.HexColor('#1A0A0A'), strokeColor=RED, strokeWidth=1.5, rx=4, ry=4))

    lines = [
        (GOLD,   '{'),
        (MGRAY,  '  "admissibility": '),
        (RED,    '"INADMISSIBLE",'),
        (MGRAY,  '  "rejected_at": '),
        (WHITE,  '"LAYER_0_STRUCTURAL_ADMISSIBILITY",'),
        (MGRAY,  '  "violations": [{'),
        (MGRAY,  '    "constraint_class":   '),
        (WHITE,  '"JURISDICTION_ASSET",'),
        (MGRAY,  '    "constraint_id":     '),
        (WHITE,  '"JA-UAE-XMR-001",'),
        (MGRAY,  '    "regulatory_source": '),
        (WHITE,  '"UAE VARA Regulations 2023, Schedule 1",'),
        (MGRAY,  '    "input_fields":      '),
        (WHITE,  '["asset", "jurisdiction"],'),
        (MGRAY,  '    "resolution":        '),
        (WHITE,  '"Select VARA-compliant asset for UAE."'),
        (MGRAY,  '  }],'),
        (MGRAY,  '  "pipeline_entry":        '),
        (RED,    'false,'),
        (MGRAY,  '  "layer_0_time_ms":       '),
        (GREEN,  '0.8'),
        (GOLD,   '}'),
    ]

    y = dh - 16
    x_col1 = 12
    for i in range(0, len(lines)-1, 2):
        if i+1 < len(lines):
            c1, t1 = lines[i]
            c2, t2 = lines[i+1]
            d.add(String(x_col1, y, t1, fontName='Courier', fontSize=7,
                         fillColor=c1, textAnchor='start'))
            d.add(String(x_col1 + 140, y, t2, fontName='Courier', fontSize=7,
                         fillColor=c2, textAnchor='start'))
            y -= 10
        else:
            c1, t1 = lines[i]
            d.add(String(x_col1, y, t1, fontName='Courier', fontSize=7,
                         fillColor=c1, textAnchor='start'))
            y -= 10

    return d

# ── DIAGRAM 6: MULTI-DOMAIN APPLICABILITY ─────────────────────────────────────
def diagram_domains(width):
    dw, dh = width, 120
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))

    # Center SAE
    cw, ch = 90, 34
    cx = dw/2 - cw/2
    cy = dh/2 - ch/2
    box(d, cx, cy, cw, ch, fill=NAVY, stroke=GOLD, sw=2, rx=5, ry=5)
    label(d, dw/2, cy+23, 'Structural', size=8, bold=True, color=GOLD)
    label(d, dw/2, cy+13, 'Admissibility', size=8, bold=True, color=GOLD)
    label(d, dw/2, cy+4, 'Engine', size=8, bold=True, color=GOLD)

    domains = [
        (20,  dh-25, 'Financial\nTrading'),
        (20,  25,    'Insurance\nUnderwriting'),
        (dw/2-25, dh-20, 'Medical\nAI'),
        (dw-110, dh-25, 'Real\nEstate'),
        (dw-110, 25,    'Energy\nGovernance'),
        (dw/2-25, 15,   'Autonomous\nAgents'),
    ]
    bw2, bh2 = 80, 26
    for dx, dy, dtxt in domains:
        box(d, dx, dy, bw2, bh2, fill=BLUE, stroke=CGRAY, sw=0.8, rx=3, ry=3)
        lines2 = dtxt.split('\n')
        label(d, dx+bw2/2, dy+17, lines2[0], size=7.5, bold=True, color=WHITE)
        if len(lines2) > 1:
            label(d, dx+bw2/2, dy+7, lines2[1], size=7.5, color=colors.HexColor('#AADDFF'))
        # Connect to center
        lx1 = dx + bw2/2; ly1 = dy + bh2/2
        lx2 = dw/2;        ly2 = dh/2
        d.add(Line(lx1, ly1, lx2, ly2, strokeColor=CGRAY, strokeWidth=0.8, strokeDashArray=[3,2]))

    label(d, dw/2, 4, 'Figure 5 — SAE Multi-Domain Applicability (Domain-Agnostic Layer 0)',
          size=7.5, color=MGRAY, align='middle')
    return d

# ── DOCUMENT ──────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(OUTPUT, pagesize=A4,
    leftMargin=LM, rightMargin=RM,
    topMargin=28*mm, bottomMargin=22*mm,
    title='OMNIX-PAT-2026-015 Provisional Patent Application',
    author='Harold Alberto Nunes Rodelo')

story = []

# ── PAGE 1: HEADER + TITLE + FIELD ────────────────────────────────────────────
story.append(Table(
    [[Paragraph('OMNIX QUANTUM LTD',
                S('HH', fontName='Helvetica-Bold', fontSize=20, textColor=WHITE, alignment=TA_CENTER))],
     [Paragraph('PROVISIONAL PATENT APPLICATION',
                S('HS', fontName='Helvetica', fontSize=11, textColor=GOLD, alignment=TA_CENTER))],
     [Paragraph('OMNIX-PAT-2026-015 &nbsp;&nbsp;|&nbsp;&nbsp; 35 U.S.C. \u00a7 111(b) '
                '&nbsp;&nbsp;|&nbsp;&nbsp; Micro Entity &nbsp;&nbsp;|&nbsp;&nbsp; April 19, 2026',
                S('HD', fontName='Helvetica', fontSize=8.5,
                  textColor=colors.HexColor('#AAAAAA'), alignment=TA_CENTER))]],
    colWidths=[CONTENT_W],
    style=TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), NAVY),
        ('TOPPADDING',   (0,0), (-1,0),  18),
        ('BOTTOMPADDING',(0,2), (-1,2),  14),
        ('LINEBELOW',    (0,2), (-1,2),  2, GOLD),
    ])
))
story.append(Spacer(1, 6*mm))

story.append(Paragraph(
    'STRUCTURAL ADMISSIBILITY ENGINE FOR AUTOMATED DECISION GOVERNANCE SYSTEMS '
    'WITH PRE-PIPELINE SCHEMA VALIDATION, ENUMERATED CONSTRAINT ENCODING, '
    'AND ZERO-BYPASS BOUNDARY ENFORCEMENT', h1))
story.append(HRFlowable(width='100%', thickness=2, color=GOLD, spaceAfter=5))

meta = [
    ['Inventor:', 'Harold Alberto Nunes Rodelo', 'Docket:', 'OMNIX-PAT-2026-015'],
    ['Applicant:', 'OMNIX Quantum Ltd', 'Filing Basis:', '35 U.S.C. \u00a7 111(b)'],
    ['Jurisdiction:', 'United Kingdom', 'Entity Status:', 'Micro Entity'],
    ['Date Filed:', 'April 19, 2026', 'Related Apps:',
     'OMNIX-PAT-2026-001, -011, -014'],
]
meta_tbl = Table(meta, colWidths=[28*mm, 60*mm, 28*mm, CONTENT_W-116*mm])
meta_tbl.setStyle(TableStyle([
    ('FONTNAME',     (0,0), (-1,-1), 'Helvetica'),
    ('FONTNAME',     (0,0), (0,-1), 'Helvetica-Bold'),
    ('FONTNAME',     (2,0), (2,-1), 'Helvetica-Bold'),
    ('FONTSIZE',     (0,0), (-1,-1), 8.5),
    ('TEXTCOLOR',    (0,0), (0,-1), NAVY),
    ('TEXTCOLOR',    (2,0), (2,-1), NAVY),
    ('TEXTCOLOR',    (1,0), (1,-1), DGRAY),
    ('TEXTCOLOR',    (3,0), (3,-1), DGRAY),
    ('TOPPADDING',   (0,0), (-1,-1), 3),
    ('BOTTOMPADDING',(0,0), (-1,-1), 3),
    ('LINEBELOW',    (0,-1), (-1,-1), 0.5, CGRAY),
]))
story.append(meta_tbl)
story.append(Spacer(1, 6*mm))

# Key phrase box
story.append(KeepTogether([
    Paragraph('\u201cOMNIX does not only block invalid decisions \u2014 '
              'it decides which decisions can exist.\u201d', key_phrase),
    Spacer(1, 4*mm),
]))

story.append(Paragraph('FIELD OF THE INVENTION', h1))
story.append(Paragraph(
    'The present invention relates to automated decision governance systems, and more '
    'particularly to a pre-pipeline structural admissibility layer that enforces decision '
    'admissibility at the point of input construction rather than at runtime evaluation \u2014 '
    'making structurally inadmissible decision requests unrepresentable as valid system objects. '
    'The Structural Admissibility Engine (SAE) constitutes a new architectural stratum \u2014 '
    '<b>Layer 0</b> \u2014 that precedes and gates all downstream governance processing, providing '
    'a zero-bypass guarantee that no inadmissible request can enter the evaluation pipeline '
    'regardless of the operational state of any downstream component.', body))

story.append(Paragraph(
    'The invention is domain-agnostic and applies without modification to automated governance '
    'pipelines in financial trading, insurance underwriting, medical AI, real estate, energy, '
    'and autonomous agent systems. The SAE integrates with the four-layer governance architecture '
    'documented in related applications, constituting the constitutive boundary layer that '
    'determines what requests may exist in the system before any evaluative processing occurs.',
    body))
story.append(Spacer(1, 4*mm))

# ── BACKGROUND ────────────────────────────────────────────────────────────────
story.append(Paragraph('BACKGROUND OF THE INVENTION', h1))

story.append(Paragraph('I. THE FUNDAMENTAL INADEQUACY OF RUNTIME INTERCEPTION', h2))
story.append(Paragraph(
    'Contemporary automated decision governance systems \u2014 including multi-checkpoint '
    'sequential pipelines, rule-based policy engines, and AI-driven compliance systems \u2014 '
    'share a common structural assumption: that governance is enforced by intercepting and '
    'blocking invalid decisions <i>after</i> those decisions have been formulated and submitted '
    'for evaluation. This runtime interception model has five irremediable architectural '
    'deficiencies:', body))

deficiencies = [
    ('1.1 Bypass Through Component Failure',
     'In a runtime interception model, every blocking component must be operational and correctly '
     'implemented for the governance guarantee to hold. If a governance checkpoint fails silently, '
     'is disabled for maintenance, encounters an unhandled exception, or is bypassed by a '
     'misconfigured pipeline, the invalid decision it was designed to block may proceed to '
     'execution. The governance guarantee is only as strong as the weakest component in the chain.'),
    ('1.2 Latent Invalid State Generation',
     'Because the invalid decision is formulated as a system object before any checkpoint evaluates '
     'it, the system must allocate computational resources to represent, transmit, and process a '
     'request that is definitionally inadmissible. This generates latent invalid state throughout '
     'the system \u2014 in memory, in logs, in audit trails \u2014 even when the request is '
     'ultimately blocked.'),
    ('1.3 Governance Dependency on Execution Order',
     'Runtime interception pipelines depend on correct execution ordering to guarantee governance. '
     'A checkpoint evaluating jurisdictional compliance must execute before one generating an '
     'execution commitment. Any inversion \u2014 through code defect, configuration error, or '
     'concurrent execution \u2014 may permit an inadmissible decision to receive an execution '
     'commitment before the blocking checkpoint evaluates it.'),
    ('1.4 Absence of a Constitutive Boundary',
     'In existing systems, the boundary between admissible and inadmissible requests is not '
     'constitutive \u2014 it does not determine what can exist in the system. It is merely '
     'evaluative \u2014 it determines what happens to things that already exist. No architectural '
     'mechanism prevents the construction and submission of a request for an operation that is '
     'categorically prohibited by jurisdiction, asset class, operation type, regulatory '
     'classification, or ethical constraint.'),
    ('1.5 No Constraint Provenance in Rejection',
     'When a runtime interception system blocks a request, the rejection is typically expressed '
     'as an error code or a binary BLOCKED decision. The system does not identify the specific '
     'structural constraint violated, the regulatory source from which it derives, or the '
     'combination of input fields that jointly produced the inadmissibility. This impedes '
     'regulatory audit, client communication, and system debugging.'),
]
for title, text in deficiencies:
    story.append(Paragraph(f'<b>{title}.</b> {text}', body))

story.append(Spacer(1, 3*mm))
story.append(Paragraph('II. ILLUSTRATIVE FAILURES OF RUNTIME INTERCEPTION', h2))
story.append(Paragraph(
    'The severity of the runtime interception model\'s deficiencies is illustrated by documented '
    'incidents in automated systems where governance failures occurred despite the existence of '
    'checkpoint components:', body))

failures = [
    ('Knight Capital Group (August 1, 2012)',
     'A loss of approximately $440 million USD in 45 minutes resulted from erroneous activation '
     'of a legacy software module not properly decommissioned. No architectural mechanism '
     'detected the divergence between intended and actual system behavior at the point of '
     'execution. A constitutive boundary would have prevented construction of the invalid '
     'execution context.'),
    ('Flash Crash (May 6, 2010)',
     'Automated trading algorithms responded to market conditions in mutually reinforcing '
     'patterns without any governance layer capable of detecting the systemic coherence failure. '
     'The invalid trading context existed and was processed before governance could respond.'),
    ('Zillow Offers Algorithm (2021)',
     'The system continued making commitments at prices contradicting available market signals, '
     'accumulating a $304 million write-down. A structural admissibility layer encoding market '
     'coherence constraints would have prevented invalid purchase requests from being constructed.'),
]
for title, text in failures:
    story.append(Paragraph(f'<b>{title}.</b> {text}', body))

story.append(Spacer(1, 3*mm))
story.append(Paragraph('III. PRIOR ART AND ITS LIMITATIONS', h2))
prior_art = [
    ('Runtime Checkpoint Pipelines (OMNIX-PAT-2026-001)',
     'Sequential checkpoints evaluate decisions against specific criteria and produce pass/block '
     'determinations. These systems operate entirely within the runtime interception model. They '
     'are powerful but do not prevent invalid requests from being formulated.'),
    ('Web API Schema Validation (JSON Schema, OpenAPI)',
     'These systems validate that input data conforms to a structural specification \u2014 that '
     'a field contains a string or falls within a numeric range. They validate data structure, '
     'not decision admissibility. Regulatory, jurisdictional, and ethical constraints are not '
     'encoded at the schema level.'),
    ('Type Systems in Programming Languages',
     'The principle "make illegal states unrepresentable" is known in type-theoretic literature. '
     'It has been applied to data modeling in software applications but has not been '
     'systematically applied as an architectural governance layer with regulatory constraint '
     'encoding for automated decision systems.'),
    ('Access Control Frameworks (OAuth, RBAC, ABAC)',
     'Authorization frameworks control whether an entity is permitted to submit a request. '
     'They operate at the identity and permission level, not at the decision content level. '
     'An authorized user may still submit a structurally inadmissible decision request.'),
]
for title, text in prior_art:
    story.append(Paragraph(f'<b>{title}.</b> {text}', body))
story.append(Paragraph(
    '<b>No prior art combines:</b> (a) schema-level structural validation; (b) regulatory, '
    'jurisdictional, and ethical constraint encoding; (c) zero-bypass architectural guarantee; '
    '(d) structured rejection with constraint provenance; and (e) composable cross-domain '
    'constraint architecture \u2014 as a unified pre-pipeline governance layer for automated '
    'decision systems.', body))

story.append(PageBreak())

# ── PAGE 2: DIAGRAMS 1 & 2 ───────────────────────────────────────────────────
story.append(Paragraph('SUMMARY OF THE INVENTION', h1))
story.append(Paragraph(
    'The present invention provides a Structural Admissibility Engine comprising five components '
    'that together enforce the principle that inadmissible decision requests cannot be represented '
    'as valid system objects:', body))

components_full = [
    ('Component A', 'Structural Constraint Schema (SCS)',
     'A declarative, machine-readable specification of all constraints determining whether a '
     'proposed decision request is structurally admissible. Organized into four classes: '
     '(i) Jurisdiction-Asset Constraints; (ii) Jurisdiction-Operation Constraints; '
     '(iii) Ethical Compliance Constraints (Sharia, ESG, Sanctions); and '
     '(iv) Client-Specific Constraints.'),
    ('Component B', 'Structural Admissibility Validator (SAV)',
     'A pre-construction validator that evaluates a proposed decision request against the SCS '
     'before constructing the EvaluationRequest object. If any constraint in any class is '
     'violated, the SAV does not construct the object. The invalid request is rejected at the '
     'boundary \u2014 it never becomes a valid system object.'),
    ('Component C', 'Zero-Bypass Boundary Enforcement (ZBE)',
     'An architectural guarantee that the SAV is the sole path through which a proposed '
     'decision request may be converted into an EvaluationRequest object. EvaluationRequest '
     'construction is private to the SAV. No external code path can construct an '
     'EvaluationRequest without passing through full constraint evaluation.'),
    ('Component D', 'Structured Rejection with Constraint Provenance (SRCP)',
     'A machine-readable rejection record identifying: the specific constraint violated; its '
     'constraint class; its regulatory or policy source; the specific input fields jointly '
     'responsible; and a resolution guidance field for actionable client communication.'),
    ('Component E', 'Composable Cross-Domain Constraint Architecture (CCCA)',
     'A constraint composition mechanism allowing constraints from multiple domains and sources '
     'to be combined into a single SAV evaluation without runtime branching logic. New constraint '
     'classes are added to the Constraint Registry without modifying the SAV evaluation logic.'),
]
for code, name, desc in components_full:
    story.append(Paragraph(f'<b>{code} \u2014 {name}:</b> {desc}', body))

story.append(Spacer(1, 5*mm))

# Diagram 1
story.append(diagram_four_layers(CONTENT_W))
story.append(Spacer(1, 2*mm))
story.append(Spacer(1, 5*mm))

# Diagram 2
story.append(diagram_comparison(CONTENT_W))
story.append(Spacer(1, 2*mm))
story.append(Spacer(1, 3*mm))

story.append(PageBreak())

# ── PAGE 3: DETAILED DESCRIPTION — CONSTRAINT SCHEMA + DIAGRAMS 3 & 4 ────────
story.append(Paragraph('DETAILED DESCRIPTION OF THE INVENTION', h1))

story.append(Paragraph('I. LAYER 0 IN THE FOUR-LAYER GOVERNANCE ARCHITECTURE', h2))
layer_table = [
    ['Layer', 'Name', 'Role', 'Related Patent'],
    ['0', 'Structural Admissibility Engine\n(present invention)',
     'Constitutive: determines what requests\ncan exist in the system',
     'OMNIX-PAT-2026-015'],
    ['1', 'OMNIX Runtime Pipeline',
     'Evaluative: CP-0 through CP-11 + TIE\nsequential veto-authority checkpoints',
     'OMNIX-PAT-2026-001'],
    ['2', 'Trajectory Invariant Engine',
     'Temporal: retrospective + prospective\nadmissibility assessment',
     'OMNIX-PAT-2026-014'],
    ['3', 'Evidence & Receipt Layer',
     'Cryptographic: PQC-signed immutable\naudit receipt (Dilithium-3)',
     'OMNIX-PAT-2026-001'],
]
lt = Table(layer_table, colWidths=[14*mm, 48*mm, 56*mm, CONTENT_W-118*mm])
lt.setStyle(TableStyle([
    ('BACKGROUND',   (0,0), (-1,0),  NAVY),
    ('TEXTCOLOR',    (0,0), (-1,0),  WHITE),
    ('FONTNAME',     (0,0), (-1,0),  'Helvetica-Bold'),
    ('BACKGROUND',   (0,1), (-1,1),  colors.HexColor('#E8F5E9')),
    ('FONTNAME',     (0,1), (0,1),   'Helvetica-Bold'),
    ('TEXTCOLOR',    (0,1), (0,1),   GREEN),
    ('FONTSIZE',     (0,0), (-1,-1), 8.5),
    ('ROWBACKGROUNDS',(0,2),(-1,-1), [LGRAY, WHITE]),
    ('GRID',         (0,0), (-1,-1), 0.5, CGRAY),
    ('VALIGN',       (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING',   (0,0), (-1,-1), 5),
    ('BOTTOMPADDING',(0,0), (-1,-1), 5),
    ('LEFTPADDING',  (0,0), (-1,-1), 5),
]))
story.append(lt)
story.append(Spacer(1, 3*mm))
story.append(Paragraph(
    '<b>Key architectural distinction:</b> Layers 1, 2, and 3 evaluate requests that '
    '<i>exist</i>. Layer 0 determines what <i>can exist</i>.', bold_b))
story.append(Spacer(1, 4*mm))

story.append(Paragraph('II. THE STRUCTURAL CONSTRAINT SCHEMA (SCS)', h2))
story.append(Paragraph(
    'The SCS is a declarative, in-memory specification organized in a hierarchical Constraint '
    'Registry. For each constraint class, the SCS encodes admissibility as a function of '
    'the relevant input fields:', body))

story.append(Paragraph('Class A \u2014 Jurisdiction-Asset Constraints', h3))
story.append(Paragraph(
    'For each regulatory jurisdiction J and each asset class A, the SCS specifies '
    'JA_CONSTRAINT(J, A) \u2208 {PERMITTED, PROHIBITED, CONDITIONAL}. Jurisdictions include '
    'UAE (VARA framework), EU (MiCA), US (FinCEN/SEC/CFTC), UK (FCA), GCC, SG (MAS), and GLOBAL. '
    'Privacy coins (XMR, ZEC, DASH, GRIN, BEAM, FIRO) are PROHIBITED in UAE, EU, US, UK, '
    'GCC, and SG jurisdictions under applicable AML regulations. Assets on active OFAC, EU, '
    'or UN sanctions lists are PROHIBITED in all jurisdictions regardless of other constraints.', body))

story.append(Paragraph('Class B \u2014 Jurisdiction-Operation Constraints', h3))
story.append(Paragraph(
    'For each jurisdiction J and operation type O (SPOT, LEVERAGED, DERIVATIVES, SHORT, '
    'STAKING, LENDING), JO_CONSTRAINT(J, O) \u2208 {PERMITTED, PROHIBITED, CONDITIONAL}. '
    'Examples: UAE LEVERAGED = PROHIBITED (VARA); US DERIVATIVES = CONDITIONAL (requires '
    'CFTC authorization); EU DERIVATIVES = PERMITTED (MiCA). CONDITIONAL determinations '
    'require all associated conditions to be satisfied to resolve to PERMITTED.', body))

story.append(Paragraph('Class C \u2014 Ethical Compliance Constraints', h3))
story.append(Paragraph(
    'Sharia compliance constraints encode a determination S(A, O) \u2208 {HALAL, HARAM, '
    'MASHBOOH} for each asset-operation combination. HARAM determinations are PROHIBITED '
    'for clients with Sharia compliance requirements. ESG screening constraints are '
    'configurable per client. Sanctions constraints (OFAC, EU, UN) are PROHIBITED for all '
    'clients. See also OMNIX-PAT-2026-003 (Ethical and Quantum-Secure Execution Framework).', body))

story.append(Paragraph('Class D \u2014 Client-Specific Constraints', h3))
story.append(Paragraph(
    'Per-client constraints negotiated at onboarding and stored in a client constraint record: '
    'CLIENT_CONSTRAINT(client_id, field, value) \u2192 {PERMITTED, PROHIBITED}. Client '
    'constraints may further restrict but may not expand the default structural admissibility. '
    'A client may prohibit additional assets beyond the jurisdictional default, but cannot '
    'permit assets that are categorically prohibited by jurisdiction or ethical constraint.', body))

story.append(Spacer(1, 4*mm))
story.append(diagram_constraint_schema(CONTENT_W))
story.append(Spacer(1, 2*mm))
story.append(Spacer(1, 4*mm))

story.append(Paragraph('III. THE STRUCTURAL ADMISSIBILITY VALIDATOR (SAV)', h2))
story.append(Paragraph(
    'When external code submits a proposed decision request P, the SAV performs full constraint '
    'evaluation before constructing any EvaluationRequest object:', body))

story.append(Paragraph(
    'ADMISSIBILITY(P) = \u22c2 { C_i(P) : C_i \u2208 SCS applicable to P }', code_s))
story.append(Paragraph(
    'If any applicable constraint determines P to be PROHIBITED, ADMISSIBILITY(P) = INADMISSIBLE. '
    'The SAV does not construct an EvaluationRequest object and returns a Structured Rejection '
    'Record. If ADMISSIBILITY(P) = ADMISSIBLE, the SAV constructs and returns an '
    'EvaluationRequest object \u2014 the only valid input to Layer 1 of the governance pipeline.',
    body))

story.append(Paragraph(
    'Constraint evaluation proceeds in priority order (fast-fail mode by default): '
    '(1) Sanctions constraints \u2014 unconditional PROHIBITED; '
    '(2) Jurisdiction-Asset constraints; '
    '(3) Jurisdiction-Operation constraints; '
    '(4) Ethical compliance constraints; '
    '(5) Client-specific constraints. '
    'Full-audit mode collects all violations before returning \u2014 configurable per deployment.',
    body))

story.append(Spacer(1, 4*mm))
story.append(diagram_sav_flow(CONTENT_W))
story.append(Spacer(1, 2*mm))

story.append(PageBreak())

# ── PAGE 4: ZERO-BYPASS + CODE + SRCP + DOMAINS ──────────────────────────────
story.append(Paragraph('IV. ZERO-BYPASS BOUNDARY ENFORCEMENT (ZBE)', h2))
story.append(Paragraph(
    'The zero-bypass property is the defining architectural characteristic distinguishing the '
    'SAE from all prior art runtime interception systems. It is enforced through private '
    'constructor restriction:', body))

story.append(Paragraph(
    'class EvaluationRequest:\n'
    '    """Only constructible via StructuralAdmissibilityValidator.validate_and_construct()"""\n'
    '    _SAV_CONSTRUCTION_TOKEN = object()  # Private sentinel — never exposed externally\n\n'
    '    def __init__(self, _token, asset, operation, jurisdiction, client_id, metadata):\n'
    '        if _token is not EvaluationRequest._SAV_CONSTRUCTION_TOKEN:\n'
    '            raise StructuralAdmissibilityViolation(\n'
    '                "EvaluationRequest must be constructed via "\n'
    '                "StructuralAdmissibilityValidator.validate_and_construct()"\n'
    '            )\n'
    '        self.asset        = asset\n'
    '        self.operation    = operation\n'
    '        self.jurisdiction = jurisdiction\n'
    '        self.client_id    = client_id\n'
    '        self.metadata     = metadata\n\n'
    'class StructuralAdmissibilityValidator:\n'
    '    def validate_and_construct(self, proposed_request: dict) -> EvaluationRequest:\n'
    '        violations = self._evaluate_all_constraints(proposed_request)\n'
    '        if violations:\n'
    '            raise StructuralAdmissibilityViolation(\n'
    '                constraint_provenance=violations\n'
    '            )\n'
    '        return EvaluationRequest(\n'
    '            _token=EvaluationRequest._SAV_CONSTRUCTION_TOKEN,\n'
    '            **proposed_request\n'
    '        )',
    code_s))

story.append(Paragraph(
    '<b>Architectural guarantee:</b> (a) No EvaluationRequest object can exist that has not '
    'passed through full SAV constraint evaluation. (b) No code path, configuration flag, or '
    'operational condition can produce an EvaluationRequest bypassing the SAV. (c) Any direct '
    'construction attempt raises an immediate exception that halts construction. '
    '<b>Silence is impossible:</b> an inadmissible request either raises an exception or is '
    'never constructed.', body))
story.append(Spacer(1, 4*mm))

story.append(Paragraph('V. STRUCTURED REJECTION WITH CONSTRAINT PROVENANCE (SRCP)', h2))
story.append(Paragraph(
    'When the SAV determines a proposed request is structurally inadmissible, it returns '
    'a machine-readable Structured Rejection Record with full constraint provenance:', body))

story.append(diagram_srcp(CONTENT_W))
story.append(Paragraph(
    'Figure 5 \u2014 Structured Rejection Record example: XMR (Monero) in UAE jurisdiction, '
    'rejected at Layer 0 in 0.8ms. Machine-readable provenance identifies regulatory source, '
    'responsible fields, and resolution guidance.', caption))
story.append(Spacer(1, 3*mm))

story.append(Paragraph(
    'The SRCP serves three purposes: (i) <b>Regulatory Audit</b> \u2014 complete machine-readable '
    'trail of why the decision was rejected, which regulatory source mandated the constraint, '
    'and which input fields produced the violation; (ii) <b>Client Communication</b> \u2014 the '
    'resolution field provides actionable guidance on reformulating the request; '
    '(iii) <b>System Debugging</b> \u2014 constraint_id and input_fields enable precise '
    'identification of constraint configuration errors.', body))
story.append(Spacer(1, 3*mm))

story.append(Paragraph('VI. COMPOSABLE CROSS-DOMAIN CONSTRAINT ARCHITECTURE (CCCA)', h2))
story.append(Paragraph(
    'All constraints are registered in a unified Constraint Registry at system initialization, '
    'indexed by the fields each constraint evaluates. For a proposed request P, the SAV '
    'retrieves all applicable constraints and evaluates them as a conjunction \u2014 ADMISSIBLE '
    'iff no constraint returns PROHIBITED. New constraint classes are added to the registry '
    'without modifying the SAV evaluation logic, making the architecture extensible by '
    'constraint addition, not by code modification.', body))
story.append(Spacer(1, 3*mm))

story.append(Paragraph('VII. MULTI-DOMAIN APPLICABILITY', h2))
story.append(Paragraph(
    'The SAE is domain-agnostic. The constraint classes are illustrated using financial trading '
    'but apply without modification to all OMNIX governance domains:', body))

domains_table = [
    ['Domain', 'SAE Constraint Classes Applied'],
    ['Financial Trading', 'Asset + Operation + Jurisdiction + Sanctions + Client-Specific'],
    ['Insurance Underwriting', 'Coverage line + Type + Jurisdiction + FHEO anti-discrimination'],
    ['Medical AI', 'Diagnostic category + Treatment type + FDA/CE/MHRA approval status'],
    ['Real Estate', 'Property type + Transaction type + AML structural constraints'],
    ['Energy Governance', 'Energy source + Contract type + Grid operator jurisdiction + Carbon'],
    ['Autonomous Agents', 'Agent action type + Domain + Authorization scope + Safety envelope'],
]
dt = Table(domains_table, colWidths=[42*mm, CONTENT_W-42*mm])
dt.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0),  NAVY),
    ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
    ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
    ('FONTSIZE',      (0,0), (-1,-1), 8.5),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [LGRAY, WHITE]),
    ('GRID',          (0,0), (-1,-1), 0.5, CGRAY),
    ('TOPPADDING',    (0,0), (-1,-1), 5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ('LEFTPADDING',   (0,0), (-1,-1), 6),
]))
story.append(dt)
story.append(Spacer(1, 4*mm))

story.append(diagram_domains(CONTENT_W))
story.append(Spacer(1, 2*mm))
story.append(Spacer(1, 3*mm))

story.append(Paragraph('VIII. PERFORMANCE CHARACTERISTICS', h2))
perf = [
    ['Metric', 'Value', 'Notes'],
    ['Layer 0 processing time (fast-fail)', '0.4 \u2013 2.1 ms', 'In-memory constraint tables'],
    ['Layer 0 processing time (full-audit)', '1.2 \u2013 4.8 ms', 'All violations collected'],
    ['Constraint table refresh', 'Asynchronous', 'Configurable interval; atomic update'],
    ['Evaluation complexity', 'O(k)', 'k = applicable constraints for P\'s fields'],
    ['Database query at evaluation time', 'None', 'In-memory; no DB query per request'],
    ['Dynamic constraint refresh lag', '\u226430 seconds', 'Sanctions list updates; configurable'],
]
pt = Table(perf, colWidths=[70*mm, 40*mm, CONTENT_W-110*mm])
pt.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0),  NAVY),
    ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
    ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
    ('FONTSIZE',      (0,0), (-1,-1), 8.5),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [LGRAY, WHITE]),
    ('GRID',          (0,0), (-1,-1), 0.5, CGRAY),
    ('TOPPADDING',    (0,0), (-1,-1), 5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ('LEFTPADDING',   (0,0), (-1,-1), 6),
]))
story.append(pt)

story.append(PageBreak())

# ── PAGE 5: CLAIMS + ABSTRACT ─────────────────────────────────────────────────
story.append(Paragraph('CLAIMS', h1))
story.append(HRFlowable(width='100%', thickness=1.5, color=GOLD, spaceAfter=8))

claims = [
    ('1.', 'A computer-implemented Structural Admissibility Engine for automated decision '
     'governance systems, comprising: (a) a Structural Constraint Schema encoding admissibility '
     'constraints organized into at least two constraint classes including jurisdiction-asset '
     'constraints and jurisdiction-operation constraints; (b) a Structural Admissibility '
     'Validator configured to evaluate a proposed decision request against the Structural '
     'Constraint Schema before constructing a valid EvaluationRequest object representing the '
     'proposed decision request; (c) wherein the Structural Admissibility Validator constructs '
     'the EvaluationRequest object only if the proposed decision request satisfies all applicable '
     'constraints in the Structural Constraint Schema; and (d) wherein the Structural '
     'Admissibility Validator does not construct the EvaluationRequest object if the proposed '
     'decision request violates any applicable constraint in the Structural Constraint Schema.'),

    ('2.', 'The Structural Admissibility Engine of claim 1, wherein the EvaluationRequest object '
     'type comprises a private constructor accessible exclusively through the Structural '
     'Admissibility Validator, enforcing a zero-bypass property whereby no code path external '
     'to the Structural Admissibility Validator can construct a valid EvaluationRequest object.'),

    ('3.', 'The Structural Admissibility Engine of claim 1, wherein the Structural Constraint '
     'Schema further comprises ethical compliance constraints derived from at least one of: '
     'Sharia compliance criteria, environmental, social, and governance (ESG) screening '
     'criteria, and international sanctions lists maintained by OFAC, the European Union, '
     'or the United Nations.'),

    ('4.', 'The Structural Admissibility Engine of claim 1, wherein the Structural Constraint '
     'Schema further comprises client-specific constraints encoding per-client admissibility '
     'restrictions, and wherein client-specific constraints may further restrict but may not '
     'expand the admissibility determined by jurisdiction-asset constraints and '
     'jurisdiction-operation constraints.'),

    ('5.', 'The Structural Admissibility Engine of claim 1, wherein when the Structural '
     'Admissibility Validator determines that a proposed decision request is inadmissible, '
     'the Validator returns a Structured Rejection Record comprising: a constraint identifier '
     'identifying the violated constraint; a constraint class identifier; a regulatory source '
     'citation identifying the regulatory or policy source from which the constraint derives; '
     'an identification of the specific input fields jointly responsible for the violation; '
     'and a resolution guidance field providing actionable reformulation instructions.'),

    ('6.', 'The Structural Admissibility Engine of claim 1, wherein the Structural Admissibility '
     'Validator supports a composable cross-domain constraint architecture in which constraints '
     'from multiple constraint classes are evaluated simultaneously through a unified Constraint '
     'Registry, and wherein new constraint classes are added to the registry without modification '
     'to the Structural Admissibility Validator evaluation logic.'),

    ('7.', 'The Structural Admissibility Engine of claim 1, wherein the Structural Admissibility '
     'Engine constitutes Layer 0 of a four-layer governance architecture, and wherein Layer 0 '
     'gates a Layer 1 runtime checkpoint pipeline that accepts only EvaluationRequest objects '
     'as input, ensuring that the Layer 1 pipeline cannot receive structurally inadmissible '
     'inputs regardless of the operational state of any Layer 1 checkpoint.'),

    ('8.', 'The Structural Admissibility Engine of claim 1, wherein constraint evaluation '
     'operates on in-memory constraint tables populated at system initialization, and wherein '
     'constraint table refresh for dynamic constraint classes including sanctions lists is '
     'performed asynchronously on a configurable refresh interval with atomic in-memory '
     'table updates, such that no database query is required at request evaluation time.'),

    ('9.', 'The Structural Admissibility Engine of claim 7, wherein the four-layer governance '
     'architecture further comprises Layer 2, a trajectory invariant enforcement layer '
     'evaluating the proposed decision against the historical and projected behavioral '
     'trajectory of the governance system; and Layer 3, a post-evaluation evidence and '
     'cryptographic receipt layer generating a post-quantum cryptographically sealed '
     'audit record using the Dilithium-3 (ML-DSA-65, NIST FIPS 204) signature scheme.'),

    ('10.', 'A method for enforcing structural admissibility in automated decision governance '
     'systems comprising: (a) receiving a proposed decision request comprising at least an '
     'asset identifier, an operation type, and a jurisdictional context; (b) evaluating the '
     'proposed decision request against a Structural Constraint Schema encoding at least '
     'jurisdiction-asset constraints and jurisdiction-operation constraints, the evaluation '
     'occurring prior to constructing any system object representing the proposed decision '
     'request; (c) if the proposed decision request satisfies all applicable constraints, '
     'constructing an EvaluationRequest object via a Structural Admissibility Validator '
     'and forwarding the EvaluationRequest object to a downstream governance pipeline; '
     '(d) if the proposed decision request violates any applicable constraint, returning '
     'a Structured Rejection Record identifying the violated constraints with constraint '
     'provenance and not constructing any EvaluationRequest object; and (e) enforcing '
     'a zero-bypass property by restricting EvaluationRequest object construction to '
     'the Structural Admissibility Validator.'),
]

for num, text in claims:
    story.append(KeepTogether([
        Paragraph(f'<b>{num}</b> {text}', body),
        Spacer(1, 2*mm),
    ]))

story.append(Spacer(1, 5*mm))
story.append(Paragraph('ABSTRACT', h1))
story.append(HRFlowable(width='100%', thickness=1.5, color=GOLD, spaceAfter=8))
story.append(Paragraph(
    'A Structural Admissibility Engine (SAE) for automated decision governance systems enforces '
    'decision admissibility at the point of input construction rather than at runtime evaluation, '
    'making structurally inadmissible decision requests unrepresentable as valid system objects. '
    'The SAE comprises a Structural Constraint Schema (SCS) encoding regulatory, jurisdictional, '
    'and ethical constraints in four composable classes; a Structural Admissibility Validator '
    '(SAV) that evaluates proposed decision requests against the SCS before constructing any '
    'EvaluationRequest object; and a Zero-Bypass Boundary Enforcement (ZBE) mechanism that '
    'restricts EvaluationRequest construction exclusively to the SAV via private constructor '
    'restriction. Inadmissible requests are rejected at the structural boundary with a Structured '
    'Rejection Record providing machine-readable constraint provenance identifying the specific '
    'violated constraint, its regulatory source, and the responsible input fields. '
    'The SAE constitutes Layer 0 of a four-layer governance architecture that gates a downstream '
    'runtime checkpoint pipeline (Layer 1), trajectory invariant enforcement layer (Layer 2), '
    'and post-quantum cryptographic receipt layer (Layer 3). The zero-bypass property guarantees '
    'that no inadmissible request can enter the governance pipeline regardless of the operational '
    'state of any downstream component \u2014 a categorical architectural improvement over '
    'runtime interception systems where governance guarantees are contingent on every intercepting '
    'component being operational and correctly implemented. The SAE is domain-agnostic and applies '
    'to financial trading, insurance underwriting, medical AI, real estate, energy governance, '
    'and autonomous agent systems.', body))

story.append(Spacer(1, 6*mm))
story.append(HRFlowable(width='100%', thickness=0.5, color=MGRAY, spaceAfter=5))
story.append(Paragraph(
    'OMNIX-PAT-2026-015 &nbsp;|&nbsp; Harold Alberto Nunes Rodelo &nbsp;|&nbsp; '
    'OMNIX Quantum Ltd, United Kingdom &nbsp;|&nbsp; April 19, 2026<br/>'
    'CONFIDENTIAL \u2014 FOR USPTO FILING PURPOSES ONLY',
    footer_s))

# ── BUILD ─────────────────────────────────────────────────────────────────────
doc.build(story)
print(f'PDF generado: {OUTPUT}')
