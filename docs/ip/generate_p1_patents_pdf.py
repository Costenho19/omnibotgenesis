"""
OMNIX P1 Patents PDF Generator — F1, F10, F14
Reads the FULL spec text from each .md file.
Replaces ONLY the ASCII-art DRAWINGS code blocks with vector diagrams.
All other content (every word) is preserved exactly.
"""
import os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 HRFlowable, Table, TableStyle, PageBreak,
                                 KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Circle
from reportlab.graphics import renderPDF

BASE = os.path.dirname(os.path.abspath(__file__))
SPEC_DIR = os.path.join(BASE, 'provisional_applications')
OUT_DIR  = os.path.join(BASE, 'provisional_applications', 'pdf_exports')

# ── COLOURS ───────────────────────────────────────────────────────────────────
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
TEAL  = colors.HexColor('#0D6E6E')
PURPL = colors.HexColor('#6B3FA0')

W, H   = A4
LM, RM = 22*mm, 22*mm
CW     = W - LM - RM

# ── STYLES ────────────────────────────────────────────────────────────────────
def S(n, **k): return ParagraphStyle(n, **k)

H1  = S('H1', fontName='Helvetica-Bold', fontSize=13, textColor=NAVY,
         spaceBefore=14, spaceAfter=5)
H2  = S('H2', fontName='Helvetica-Bold', fontSize=11, textColor=NAVY,
         spaceBefore=10, spaceAfter=4)
H3  = S('H3', fontName='Helvetica-Bold', fontSize=10, textColor=DGRAY,
         spaceBefore=7, spaceAfter=3)
H4  = S('H4', fontName='Helvetica-BoldOblique', fontSize=9.5, textColor=DGRAY,
         spaceBefore=5, spaceAfter=2)
BD  = S('BD', fontName='Helvetica', fontSize=9.5, textColor=DGRAY,
         leading=14, spaceAfter=5, alignment=TA_JUSTIFY)
BB  = S('BB', fontName='Helvetica-Bold', fontSize=9.5, textColor=DGRAY,
         leading=14, spaceAfter=4)
BL  = S('BL', fontName='Helvetica', fontSize=9.5, textColor=DGRAY,
         leading=14, spaceAfter=3, leftIndent=14)
CAP = S('CAP', fontName='Helvetica-Oblique', fontSize=8.5, textColor=MGRAY,
         spaceAfter=6, alignment=TA_CENTER)
COD = S('COD', fontName='Courier', fontSize=7.5, textColor=NAVY,
         leading=11, spaceAfter=4, leftIndent=8,
         backColor=colors.HexColor('#EEF2F8'))
ITL = S('ITL', fontName='Helvetica-Oblique', fontSize=8.5, textColor=MGRAY,
         spaceAfter=3, leading=12)

# ── DIAGRAM PRIMITIVES ────────────────────────────────────────────────────────
def bx(d, x, y, w, h, fill=NAVY, stroke=GOLD, sw=1.5, rx=3, ry=3):
    d.add(Rect(x, y, w, h, rx=rx, ry=ry, fillColor=fill,
               strokeColor=stroke, strokeWidth=sw))

def tx(d, x, y, t, sz=8.5, col=WHITE, bold=False, anchor='middle'):
    d.add(String(x, y, t, fontName='Helvetica-Bold' if bold else 'Helvetica',
                 fontSize=sz, fillColor=col, textAnchor=anchor))

def ard(d, x, y1, y2, col=GOLD, sw=1.5):
    d.add(Line(x, y1, x, y2+4, strokeColor=col, strokeWidth=sw))
    d.add(Polygon([x-4,y2+4,x+4,y2+4,x,y2], fillColor=col, strokeColor=col, strokeWidth=0))

def arr(d, x1, x2, y, col=GOLD, sw=1.5):
    d.add(Line(x1, y, x2-4, y, strokeColor=col, strokeWidth=sw))
    d.add(Polygon([x2-4,y+4,x2-4,y-4,x2,y], fillColor=col, strokeColor=col, strokeWidth=0))

def arl(d, x1, x2, y, col=GOLD, sw=1.5):
    d.add(Line(x1, y, x2+4, y, strokeColor=col, strokeWidth=sw))
    d.add(Polygon([x2+4,y+4,x2+4,y-4,x2,y], fillColor=col, strokeColor=col, strokeWidth=0))

# ══════════════════════════════════════════════════════════════════════════════
# F1 DIAGRAMS
# ══════════════════════════════════════════════════════════════════════════════
def f1_fig1(width):
    """FIG 1 — System Architecture Overview"""
    dw, dh = width, 220
    d = Drawing(dw, dh)
    d.add(Rect(0,0,dw,dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    tx(d, dw/2, dh-13, 'FIG. 1 — OMNIX Governance Engine System Architecture',
       sz=8, col=DGRAY, bold=True)

    # Decision generation subsystem (left)
    bx(d, 8, dh-70, 80, 40, fill=BLUE, stroke=CGRAY, sw=1, rx=3)
    tx(d, 48, dh-44, 'DECISION', sz=7.5, col=WHITE, bold=True)
    tx(d, 48, dh-54, 'GENERATION', sz=7.5, col=WHITE, bold=True)
    tx(d, 48, dh-64, 'SUBSYSTEM', sz=7, col=CGRAY)
    arr(d, 88, 118, dh-50, col=GOLD, sw=1.5)

    # Domain Adapter
    bx(d, 118, dh-78, 140, 52, fill=NAVY, stroke=GOLD, sw=1.5, rx=3)
    tx(d, 188, dh-44, 'DOMAIN ADAPTER MODULE (110)', sz=7.5, col=GOLD, bold=True)
    tx(d, 188, dh-55, 'Input: Domain-Specific Data', sz=7, col=CGRAY)
    tx(d, 188, dh-65, 'Output: Normalized Signal Set', sz=7, col=CGRAY)
    tx(d, 188, dh-75, '(P, R, C, T, S, L)  in [0.0, 1.0]', sz=7, col=CGRAY)
    ard(d, 188, dh-78, dh-100, col=GOLD)

    # Sequential Checkpoint Pipeline
    bx(d, 80, dh-155, 240, 50, fill=NAVY, stroke=GOLD, sw=2, rx=4)
    tx(d, 200, dh-118, 'SEQUENTIAL CHECKPOINT PIPELINE (120)', sz=7.5, col=GOLD, bold=True)
    tx(d, 200, dh-129, 'CP-0 -> CP-1 -> CP-2 -> CP-3 -> CP-4 -> CP-5', sz=6.5, col=WHITE)
    tx(d, 200, dh-140, '-> CP-6(DCI) -> CP-7 -> CP-8 -> CP-9 -> CP-10 -> CP-11 -> TIE', sz=6.5, col=WHITE)
    tx(d, 200, dh-151, 'Each CP: Independent Veto Authority | Default: FAIL-CLOSED (BLOCK)', sz=6, col=CGRAY)

    # Two outputs from pipeline
    ard(d, 145, dh-155, dh-175, col=GOLD)
    ard(d, 270, dh-155, dh-175, col=CGRAY)

    # Decision Trace Generator
    bx(d, 80, dh-215, 110, 38, fill=GREEN, stroke=GOLD, sw=1.5, rx=3)
    tx(d, 135, dh-185, 'DECISION TRACE', sz=7.5, col=WHITE, bold=True)
    tx(d, 135, dh-196, 'GENERATOR (130)', sz=7.5, col=WHITE, bold=True)
    tx(d, 135, dh-207, 'PQC-Sealed Audit Receipt', sz=6.5, col=colors.HexColor('#CCFFCC'))

    # Shadow Portfolio
    bx(d, 210, dh-215, 110, 38, fill=TEAL, stroke=CGRAY, sw=1, rx=3)
    tx(d, 265, dh-185, 'SHADOW PORTFOLIO', sz=7.5, col=WHITE, bold=True)
    tx(d, 265, dh-196, 'SYSTEM (140)', sz=7.5, col=WHITE, bold=True)
    tx(d, 265, dh-207, 'Calibration Engine', sz=6.5, col=CGRAY)

    # Execution env
    bx(d, dw-110, dh-135, 100, 30, fill=RED, stroke=CGRAY, sw=1, rx=3)
    tx(d, dw-60, dh-113, 'EXECUTION ENV', sz=7, col=WHITE, bold=True)
    tx(d, dw-60, dh-124, '(if APPROVED)', sz=6.5, col=CGRAY)
    arr(d, 320, dw-110, dh-120, col=CGRAY, sw=1)

    return d

def f1_fig2(width):
    """FIG 2 — Sequential Checkpoint Pipeline Process Flow"""
    dw, dh = width, 240
    d = Drawing(dw, dh)
    d.add(Rect(0,0,dw,dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    tx(d, dw/2, dh-13, 'FIG. 2 — Sequential Checkpoint Pipeline Process Flow',
       sz=8, col=DGRAY, bold=True)

    cx = dw/2
    steps = [
        (GREEN,  'START: Proposed Action Received', '', False),
        (NAVY,   'CP-0: Signal Integrity Gate', 'All signals present, in range, fresh', True),
        (NAVY,   'CP-1: Context Admission Gate', 'Global operating context suitable', True),
        (NAVY,   'CP-2: Probability Threshold Gate', 'P >= 0.52 (win probability)', True),
        (NAVY,   'CP-3: Temporal Coherence Gate', 'T >= 0.40, trajectory consistent', True),
        (NAVY,   'CP-4: Risk Limits Gate', 'R <= max configured exposure', True),
        (NAVY,   'CP-5 to CP-11 (Sequential)', 'Coherence, DCI, scoring, compliance', True),
        (GREEN,  'APPROVE VERDICT — PQC-Sealed Receipt', 'EXECUTION COMMITMENT', False),
        (PURPL,  'TIE POST-EXECUTION VERIFICATION', 'Trajectory invariant audit', False),
    ]
    bw, bh = 170, 22
    y = dh - 42
    for i, (col, title, sub, has_block) in enumerate(steps):
        bx(d, cx-bw/2, y, bw, bh, fill=col, stroke=GOLD if not has_block else CGRAY,
           sw=2 if not has_block else 0.8, rx=3)
        tx(d, cx, y+bh-8, title, sz=7.5, col=WHITE, bold=True)
        if sub:
            tx(d, cx, y+5, sub, sz=6, col=CGRAY)
        if has_block:
            bx(d, cx+bw/2+4, y+4, 90, 14, fill=RED, stroke=CGRAY, sw=0.5, rx=2)
            tx(d, cx+bw/2+49, y+9, 'BLOCK -> Verdict + Trace Entry', sz=6, col=WHITE)
        if i < len(steps)-1:
            ard(d, cx, y, y-8, col=GOLD if not has_block else CGRAY, sw=1.2)
        y -= 30
        if y < 10:
            break

    return d

def f1_fig3(width):
    """FIG 3 — Counterfactual Shadow Portfolio System"""
    dw, dh = width, 215
    d = Drawing(dw, dh)
    d.add(Rect(0,0,dw,dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    tx(d, dw/2, dh-13, 'FIG. 3 — Counterfactual Shadow Portfolio System',
       sz=8, col=DGRAY, bold=True)

    cx = dw/2
    boxes = [
        (BLUE,  'BLOCK VERDICT ISSUED',
         ['Governance pipeline blocked action'], 32),
        (NAVY,  'SHADOW EVENT LOGGER',
         ['decision_id | timestamp | proposed_action',
          'governance_signals | blocking_checkpoint',
          'market_microstructure | evaluation_window'], 48),
        (TEAL,  'OUTCOME TRACKER',
         ['actual_outcome | counterfactual_pnl',
          'outcome_timestamp'], 38),
        (colors.HexColor('#1A5A3A'), 'COUNTERFACTUAL ANALYZER',
         ['CORRECT_VETO (loss prevented)',
          'INCORRECT_VETO (gain prevented)'], 38),
        (GREEN, 'CALIBRATION ENGINE',
         ['veto_accuracy_rate | opportunity_cost_rate',
          'aggregate_pnl | Threshold Adjustment Recs',
          '(Human Review Required)'], 48),
    ]
    bw = 200
    y = dh - 38
    for clr, title, lines, bh in boxes:
        bx(d, cx-bw/2, y-bh, bw, bh, fill=clr, stroke=GOLD, sw=1.5, rx=4)
        tx(d, cx, y-8, title, sz=8, col=GOLD, bold=True)
        for j, line in enumerate(lines):
            tx(d, cx, y-20-j*10, line, sz=6.5, col=WHITE)
        y -= bh
        if y > 20:
            ard(d, cx, y, y-8, col=GOLD, sw=1.2)
            y -= 8

    return d

def f1_fig4(width):
    """FIG 4 — DCI Signal State Diagram"""
    dw, dh = width, 200
    d = Drawing(dw, dh)
    d.add(Rect(0,0,dw,dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    tx(d, dw/2, dh-13, 'FIG. 4 — Decision Contradiction Index (DCI) — Signal State Diagram',
       sz=8, col=DGRAY, bold=True)

    # 5 signal sources
    sigs = ['EMA\nSIGNAL','HMM\nREGIME','KALMAN\nFILTER','NON-MARK\nKERNEL','KELLY\nCRITERION']
    sw_s = (dw-20)/5 - 4
    sy = dh-60
    for i, sig in enumerate(sigs):
        sx = 10+i*(sw_s+4)
        bx(d, sx, sy, sw_s, 32, fill=BLUE, stroke=CGRAY, sw=0.8, rx=3)
        for j, line in enumerate(sig.split('\n')):
            tx(d, sx+sw_s/2, sy+22-j*11, line, sz=7.5, col=WHITE, bold=True)
        ard(d, sx+sw_s/2, sy, sy-16, col=CGRAY, sw=0.8)

    # Pairwise divergence box
    pdb_y = sy - 58
    bx(d, dw/2-95, pdb_y, 190, 36, fill=NAVY, stroke=GOLD, sw=2, rx=4)
    tx(d, dw/2, pdb_y+27, 'PAIRWISE DIVERGENCE COMPUTATION', sz=8, col=GOLD, bold=True)
    tx(d, dw/2, pdb_y+15, 'DCI = mean of all pairwise |Si - Sj|', sz=7.5, col=WHITE)
    tx(d, dw/2, pdb_y+5,  'normalized to [0, 100]', sz=7.5, col=CGRAY)
    ard(d, dw/2, pdb_y, pdb_y-14, col=GOLD)

    # Classification bands
    bands = [
        (GREEN, 'DCI  0–34   ALIGNED',     'Normal evaluation -> proceed'),
        (AMBER, 'DCI 35–69  TENSIONED',     'Reduced position size'),
        (RED,   'DCI 70–100  CONTRADICTORY','MANDATORY BLOCK'),
    ]
    bw_b = (dw-20)/3-4
    by = pdb_y-70
    for i,(col,title,desc) in enumerate(bands):
        bx_ = 10+i*(bw_b+4)
        bx(d, bx_, by, bw_b, 46, fill=col, stroke=CGRAY, sw=1, rx=3)
        tx(d, bx_+bw_b/2, by+34, title, sz=7, col=WHITE, bold=True)
        tx(d, bx_+bw_b/2, by+20, desc, sz=6.5, col=WHITE)
        if i == 2:
            d.add(Rect(bx_, by, bw_b, 46, rx=3, ry=3,
                       fillColor=colors.Color(0,0,0,0), strokeColor=GOLD, strokeWidth=2))

    return d

# ══════════════════════════════════════════════════════════════════════════════
# F10 DIAGRAMS
# ══════════════════════════════════════════════════════════════════════════════
def f10_fig1(width):
    dw, dh = width, 175
    d = Drawing(dw, dh)
    d.add(Rect(0,0,dw,dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    tx(d, dw/2, dh-13, 'FIG. 1 — Transparency Chain: Hash-Linked Decision Receipt Entries',
       sz=8, col=DGRAY, bold=True)

    entries = ['Entry N-2', 'Entry N-1', 'Entry N']
    ew = (dw-28)/3-6
    ey, eh = dh-105, 70
    for i, name in enumerate(entries):
        ex = 10+i*(ew+6)
        clr = TEAL if i==2 else NAVY
        bdr = GOLD if i==2 else CGRAY
        bx(d, ex, ey, ew, eh, fill=clr, stroke=bdr, sw=2 if i==2 else 1, rx=3)
        tx(d, ex+ew/2, ey+eh-10, name, sz=7.5, col=GOLD if i==2 else CGRAY, bold=True)
        for j, f in enumerate(['log_id','receipt_id','payload_hash','prev_log_hash','merkle_root','PQC_sig','ts_utc']):
            tx(d, ex+ew/2, ey+eh-22-j*8, f, sz=5.5, col=WHITE if i==2 else colors.HexColor('#AABBCC'))
        if i < 2:
            arr(d, ex+ew, ex+ew+6, ey+eh/2, col=GOLD if i==1 else CGRAY, sw=1.5)

    link_y = ey - 18
    tx(d, dw/2, link_y, 'Modify any field -> hash changes -> next entry\'s prev_log_hash INVALID -> chain verification FAILS', sz=6.5, col=RED, anchor='middle')
    tx(d, dw/2, link_y-11, 'Delete any entry -> hash linkage gap -> chain verification FAILS', sz=6.5, col=RED, anchor='middle')

    bx(d, dw/2-110, link_y-38, 220, 18, fill=GREEN, stroke=GOLD, sw=1.5, rx=3)
    tx(d, dw/2, link_y-28, 'Published Merkle Root = commitment to ALL N entries — third-party verifiable', sz=7, col=WHITE, bold=True, anchor='middle')

    return d

def f10_fig2(width):
    dw, dh = width, 155
    d = Drawing(dw, dh)
    d.add(Rect(0,0,dw,dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    tx(d, dw/2, dh-13, 'FIG. 2 — Rolling Merkle Accumulator: O(1) Update Per Entry',
       sz=8, col=DGRAY, bold=True)

    steps = [('root_0','"0" x 64  (genesis)',BLUE,False),
             ('root_1','SHA256(root_0 || hash(e_1))',NAVY,False),
             ('root_2','SHA256(root_1 || hash(e_2))',NAVY,False),
             ('root_N','SHA256(root_{N-1} || hash(e_N))',TEAL,True)]
    sw_s = (dw-24)/4-6
    sy = dh-90
    for i,(name,formula,clr,key) in enumerate(steps):
        sx = 10+i*(sw_s+6)
        bx(d, sx, sy, sw_s, 52, fill=clr, stroke=GOLD if key else CGRAY, sw=2 if key else 1, rx=3)
        tx(d, sx+sw_s/2, sy+42, name, sz=8, col=GOLD if key else WHITE, bold=True)
        for j, line in enumerate(formula.split(' || ')):
            part = ('|| ' if j>0 else '')+line
            tx(d, sx+sw_s/2, sy+28-j*11, part, sz=6, col=WHITE)
        if i<3: arr(d, sx+sw_s, sx+sw_s+6, sy+26, col=GOLD, sw=1.5)

    bx(d, 10, sy-36, dw-20, 26, fill=NAVY, stroke=GOLD, sw=1.5, rx=3)
    tx(d, dw/2, sy-18, 'root_N = commitment to ALL N entries | O(1) update | published root enables third-party verification', sz=7.5, col=GOLD, bold=True, anchor='middle')
    tx(d, dw/2, sy-28, 'No blockchain | No external TSA | No network latency in governance pipeline', sz=7, col=CGRAY, anchor='middle')

    return d

def f10_fig3(width):
    dw, dh = width, 175
    d = Drawing(dw, dh)
    d.add(Rect(0,0,dw,dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    tx(d, dw/2, dh-13, 'FIG. 3 — Internal Timestamp Token: RFC 3161-Style Without External TSA',
       sz=8, col=DGRAY, bold=True)

    half = dw/2-6
    tx(d, half/2+5, dh-28, 'PRIOR ART — External TSA', sz=8, col=RED, bold=True, anchor='middle')
    prior = [(BLUE,'Governance Decision'),(colors.HexColor('#8B0000'),'Hash -> External TSA'),
             (RED,'Network Latency (50-500ms)'),(colors.HexColor('#8B0000'),'TSA Returns Token'),
             (RED,'3rd-party dependency risk')]
    for i,(clr,step) in enumerate(prior):
        sy = dh-50-i*22
        bx(d, 8, sy, half-4, 16, fill=clr, stroke=CGRAY, sw=0.5, rx=2)
        tx(d, 8+(half-4)/2, sy+5, step, sz=7, col=WHITE)
        if i<4: ard(d, 8+(half-4)/2, sy, sy-6, col=CGRAY, sw=0.8)

    d.add(Line(dw/2, 12, dw/2, dh-22, strokeColor=CGRAY, strokeWidth=1,
               strokeDashArray=[3,3]))

    rx, rw = dw/2+4, half-4
    tx(d, rx+rw/2, dh-28, 'OMNIX — Internal TST', sz=8, col=GREEN, bold=True, anchor='middle')
    fields = ['version: 1','hash_alg: "SHA-256"','payload_hash: SHA256(receipt)',
              'ts_utc: "2026-04-19T..."','nonce: <16 random bytes>','policy: "OMNIX-ADR044-v1"']
    tst_h = len(fields)*14+16
    bx(d, rx, dh-50-tst_h+14, rw, tst_h, fill=NAVY, stroke=GOLD, sw=1.5, rx=3)
    tx(d, rx+rw/2, dh-44, 'TST Structure', sz=7.5, col=GOLD, bold=True)
    for j, f in enumerate(fields):
        tx(d, rx+6, dh-58-j*14, f, sz=6.5, col=WHITE, anchor='start')

    seal_y = dh-50-tst_h
    bx(d, rx, seal_y-16, rw, 14, fill=GREEN, stroke=GOLD, sw=1.5, rx=2)
    tx(d, rx+rw/2, seal_y-10, 'tst_hash = SHA256(canonical_json(TST)) -- No external TSA required', sz=6, col=WHITE)

    return d

def f10_fig4(width):
    dw, dh = width, 175
    d = Drawing(dw, dh)
    d.add(Rect(0,0,dw,dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    tx(d, dw/2, dh-13, 'FIG. 4 — Public Verification Flow: Integrity Check Without Content Disclosure',
       sz=8, col=DGRAY, bold=True)

    col_w = (dw-20)/2-4
    lx, rx_ = 10, dw/2+4
    tx(d, lx+col_w/2, dh-28, 'EXTERNAL VERIFIER', sz=8.5, col=BLUE, bold=True, anchor='middle')
    tx(d, rx_+col_w/2, dh-28, 'OMNIX PUBLIC API', sz=8.5, col=TEAL, bold=True, anchor='middle')

    interactions = [
        ('GET /api/transparency/chain', True),
        ('<- chain entries (hashes only)', False),
        ('Recompute hash chain', True),
        ('Recompute Merkle root', True),
        ('Verify PQC signatures', True),
        ('Compare own receipt hash in chain?', True),
        ('[OK] VERIFIED  /  [BLOCK] TAMPERED', True),
    ]
    step_y = dh-48
    for i,(step,is_left) in enumerate(interactions):
        sy = step_y - i*17
        if is_left:
            bx(d, lx, sy, col_w, 13, fill=BLUE, stroke=CGRAY, sw=0.5, rx=2)
            tx(d, lx+col_w/2, sy+3, step, sz=6.5, col=WHITE)
            if i==0: arr(d, lx+col_w, rx_, sy+6, col=CGRAY, sw=0.8)
        else:
            bx(d, rx_, sy, col_w, 13, fill=TEAL, stroke=CGRAY, sw=0.5, rx=2)
            tx(d, rx_+col_w/2, sy+3, step, sz=6.5, col=WHITE)
            arl(d, rx_, lx+col_w, sy+6, col=GOLD, sw=0.8)

    note_y = step_y - len(interactions)*17 - 8
    bx(d, 10, note_y, dw-20, 14, fill=GREEN, stroke=GOLD, sw=1.5, rx=3)
    tx(d, dw/2, note_y+5, 'No receipt content disclosed — verifier confirms integrity without accessing confidential governance records',
       sz=6.5, col=WHITE, bold=True, anchor='middle')

    return d

# ══════════════════════════════════════════════════════════════════════════════
# F14 DIAGRAMS
# ══════════════════════════════════════════════════════════════════════════════
def f14_fig1(width):
    dw, dh = width, 185
    d = Drawing(dw, dh)
    d.add(Rect(0,0,dw,dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    tx(d, dw/2, dh-13, 'FIG. 1 — Bidirectional Temporal Admissibility Envelope',
       sz=8, col=DGRAY, bold=True)

    tl_y = dh/2+8
    d.add(Line(15, tl_y, dw-15, tl_y, strokeColor=DGRAY, strokeWidth=1.5))

    past = [('t-15',0.08),('t-12',0.15),('t-9',0.22),('t-6',0.29),('t-3',0.36),('t-1',0.43)]
    for lb, frac in past:
        px = 15+frac*(dw-30)
        d.add(Circle(px, tl_y, 4, fillColor=BLUE, strokeColor=BLUE, strokeWidth=0))
        tx(d, px, tl_y-14, lb, sz=6, col=DGRAY, anchor='middle')

    dec_x = 15+0.52*(dw-30)
    d.add(Circle(dec_x, tl_y, 8, fillColor=GOLD, strokeColor=NAVY, strokeWidth=2))
    tx(d, dec_x, tl_y+20, 't = 0  DECISION', sz=8, col=NAVY, bold=True, anchor='middle')

    future = [('t+1',0.62),('t+2',0.69),('t+3',0.76),('t+4',0.83),('t+5',0.90)]
    for lb, frac in future:
        px = 15+frac*(dw-30)
        d.add(Circle(px, tl_y, 4, fillColor=TEAL, strokeColor=TEAL, strokeWidth=0))
        tx(d, px, tl_y-14, lb, sz=6, col=DGRAY, anchor='middle')

    # TCV bracket
    ts, te = 15+0.08*(dw-30), dec_x-10
    d.add(Rect(ts, tl_y+24, te-ts, 16, fillColor=BLUE, strokeColor=BLUE, strokeWidth=1.5, rx=2))
    tx(d, (ts+te)/2, tl_y+34, 'TCV -- Trajectory Coherence Validator (retrospective)', sz=7, col=WHITE, bold=True, anchor='middle')

    # FTI bracket
    fs, fe = dec_x+10, 15+0.92*(dw-30)
    d.add(Rect(fs, tl_y+24, fe-fs, 16, fillColor=TEAL, strokeColor=TEAL, strokeWidth=1.5, rx=2))
    tx(d, (fs+fe)/2, tl_y+34, 'FTI -- Forward Trajectory Implication (prospective)', sz=7, col=WHITE, bold=True, anchor='middle')

    bx(d, dw/2-125, 10, 250, 20, fill=NAVY, stroke=GOLD, sw=2, rx=4)
    tx(d, dw/2, 21, 'ADMISSIBLE <-> consistent with past trajectory  AND  near-future trajectory', sz=7.5, col=GOLD, bold=True, anchor='middle')
    tx(d, dw/2, 11, 'Both TCV and FTI must pass -- either failure -> BLOCK', sz=6.5, col=CGRAY, anchor='middle')

    return d

def f14_fig2(width):
    dw, dh = width, 175
    d = Drawing(dw, dh)
    d.add(Rect(0,0,dw,dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    tx(d, dw/2, dh-13, 'FIG. 2 — TCV Three-Dimensional Retrospective Score',
       sz=8, col=DGRAY, bold=True)

    dims = [('Direction\nCoherence','40%','Monotonicity of\nsignal deltas',BLUE),
            ('Regime-Action\nAlignment','35%','Action vs. dominant\nhistorical regime',NAVY),
            ('Signal\nStability','25%','Inverse direction-\nflip rate',TEAL)]
    dw3 = (dw-24)/3-6
    dy = dh-105
    for i,(name,wt,desc,clr) in enumerate(dims):
        dx_ = 10+i*(dw3+6)
        bx(d, dx_, dy, dw3, 70, fill=clr, stroke=CGRAY, sw=1, rx=3)
        for j, line in enumerate(name.split('\n')):
            tx(d, dx_+dw3/2, dy+60-j*11, line, sz=8, col=WHITE, bold=True)
        tx(d, dx_+dw3/2, dy+37, f'Weight: {wt}', sz=9, col=GOLD, bold=True)
        d.add(Rect(dx_+6, dy+32, dw3-12, 14, rx=2, ry=2,
                   fillColor=colors.Color(0,0,0,0), strokeColor=GOLD, strokeWidth=1))
        for j, line in enumerate(desc.split('\n')):
            tx(d, dx_+dw3/2, dy+24-j*10, line, sz=7, col=CGRAY)

    # Dual-source note
    ds_y = dy-38
    bx(d, 10, ds_y, (dw-26)/2, 26, fill=colors.HexColor('#1A3A5A'), stroke=CGRAY, sw=1, rx=3)
    tx(d, 10+(dw-26)/4, ds_y+18, 'shadow_trade_events', sz=7.5, col=GOLD, bold=True)
    tx(d, 10+(dw-26)/4, ds_y+7, 'Blocked decisions (veto events)', sz=7, col=CGRAY)
    bx(d, 16+(dw-26)/2, ds_y, (dw-26)/2, 26, fill=colors.HexColor('#1A3A5A'), stroke=CGRAY, sw=1, rx=3)
    tx(d, 16+(dw-26)/2+(dw-26)/4, ds_y+18, 'paper_trading_trades', sz=7.5, col=GOLD, bold=True)
    tx(d, 16+(dw-26)/2+(dw-26)/4, ds_y+7, 'Approved decisions (executed events)', sz=7, col=CGRAY)
    bx(d, 10, ds_y-18, dw-20, 14, fill=GREEN, stroke=GOLD, sw=1.5, rx=2)
    tx(d, dw/2, ds_y-10, 'Combined dual-source = full trajectory without survivorship bias', sz=7, col=WHITE, bold=True, anchor='middle')

    return d

def f14_fig3(width):
    dw, dh = width, 185
    d = Drawing(dw, dh)
    d.add(Rect(0,0,dw,dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    tx(d, dw/2, dh-13, 'FIG. 3 — FTI HMM Regime Transition Risk',
       sz=8, col=DGRAY, bold=True)

    bx(d, dw/2-75, dh-52, 150, 26, fill=AMBER, stroke=GOLD, sw=2, rx=4)
    tx(d, dw/2, dh-33, 'Current Regime: VOLATILE (persistence = 0.45)', sz=8, col=WHITE, bold=True)
    tx(d, dw/2, dh-43, 'Proposed Action: BUY', sz=7.5, col=WHITE)
    ard(d, dw/2, dh-52, dh-68, col=GOLD)

    regimes = [('BULLISH','0.08',GREEN,False),('BEARISH','0.22',RED,True),
               ('TRENDING','0.12',BLUE,False),('VOLATILE','0.45',AMBER,True),
               ('STRONG_SELL','0.13',colors.HexColor('#8B0000'),True)]
    rw_ = (dw-24)/5-4
    ry_ = dh-120
    tx(d, dw/2, ry_+54, '5-step HMM Transition Probabilities from VOLATILE:', sz=7.5, col=DGRAY, anchor='middle')
    for i,(name,prob,clr,adverse) in enumerate(regimes):
        rx__ = 10+i*(rw_+4)
        bx(d, rx__, ry_, rw_, 42, fill=clr, stroke=CGRAY, sw=0.8, rx=3)
        tx(d, rx__+rw_/2, ry_+32, name, sz=6.5, col=WHITE, bold=True)
        tx(d, rx__+rw_/2, ry_+20, f'P = {prob}', sz=8, col=WHITE, bold=True)
        if adverse:
            tx(d, rx__+rw_/2, ry_+8, 'ADVERSE', sz=6, col=colors.HexColor('#FFAAAA'))
            d.add(Rect(rx__, ry_, rw_, 42, rx=3, ry=3,
                       fillColor=colors.Color(0,0,0,0), strokeColor=RED, strokeWidth=1.5))
        else:
            tx(d, rx__+rw_/2, ry_+8, 'favorable', sz=6, col=colors.HexColor('#AAFFAA'))

    ard(d, dw/2, ry_, ry_-18, col=GOLD)
    bx(d, 10, ry_-50, dw-20, 28, fill=RED, stroke=GOLD, sw=2, rx=4)
    tx(d, dw/2, ry_-23, 'P(adverse regime in 5 cycles | VOLATILE) = 0.80 = HIGH', sz=8.5, col=WHITE, bold=True, anchor='middle')
    tx(d, dw/2, ry_-35, 'FTI Regime Transition Risk -> LOW score -> BUY decision: BLOCKED (prospective inadmissibility)', sz=7, col=colors.HexColor('#FFCCCC'), anchor='middle')

    return d

def f14_fig4(width):
    dw, dh = width, 185
    d = Drawing(dw, dh)
    d.add(Rect(0,0,dw,dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    tx(d, dw/2, dh-13, 'FIG. 4 — Bilateral Admissibility Logic: TCV x FTI -> Governance Outcome',
       sz=8, col=DGRAY, bold=True)

    cpx = [10, 120, 230]
    cwx = [108, 108, dw-10-230]
    hdrs = ['TCV Result','FTI Result','Bilateral Decision']
    hdr_y = dh-42
    for i,(hdr,cx_,cw_) in enumerate(zip(hdrs,cpx,cwx)):
        bx(d, cx_, hdr_y, cw_, 20, fill=NAVY, stroke=GOLD, sw=1.5, rx=0)
        tx(d, cx_+cw_/2, hdr_y+7, hdr, sz=8, col=GOLD, bold=True)

    rows = [
        ('ADMISSIBLE','PASSED','[OK] PROCEEDS -- bilateral admissibility confirmed',GREEN),
        ('NOT ADMISSIBLE','PASSED','[BLOCK] BLOCKED -- retrospective trajectory violation',RED),
        ('ADMISSIBLE','NOT PASSED','[BLOCK] BLOCKED -- prospective regime transition risk',RED),
        ('NOT ADMISSIBLE','NOT PASSED','[BLOCK] BLOCKED -- bilateral compound failure',colors.HexColor('#8B0000')),
        ('PASS-THROUGH','PASSED','[!] PROCEEDS -- TCV fail-safe mode (logged)',AMBER),
        ('ADMISSIBLE','PASS-THROUGH','[!] PROCEEDS -- FTI fail-safe mode (logged)',AMBER),
    ]
    for i,(tcv,fti,outcome,fill) in enumerate(rows):
        ry_ = hdr_y-20*(i+1)
        bg = colors.HexColor('#F8F8F8') if i%2==0 else WHITE
        for j,(cx_,cw_,val,col_) in enumerate([(cpx[0],cwx[0],tcv,BLUE),(cpx[1],cwx[1],fti,TEAL),(cpx[2],cwx[2],outcome,fill)]):
            bx(d, cx_, ry_, cw_, 18, fill=fill if j==2 else bg, stroke=CGRAY, sw=0.5, rx=0)
            tx(d, cx_+cw_/2, ry_+5, val, sz=6.5 if j==2 else 7, col=WHITE if j==2 else (BLUE if j==0 else TEAL), bold=j==2)

    total_bottom = hdr_y-20*len(rows)
    d.add(Rect(10, total_bottom, dw-20, hdr_y+20-total_bottom,
               fillColor=colors.Color(0,0,0,0), strokeColor=GOLD, strokeWidth=1.5))

    return d

# ══════════════════════════════════════════════════════════════════════════════
# UNICODE SANITIZER — removes box-drawing chars that crash PDF fonts
# ══════════════════════════════════════════════════════════════════════════════
BOX_MAP = {
    '│':'|','─':'-','┌':'+','┐':'+','└':'+','┘':'+',
    '├':'+','┤':'+','┬':'+','┴':'+','┼':'+',
    '═':'=','╔':'+','╗':'+','╚':'+','╝':'+','║':'|',
    '╠':'+','╣':'+','╦':'+','╩':'+','╬':'+',
    '→':'->','←':'<-','↔':'<->','↑':'^','↓':'v',
    '►':'>','◄':'<','▲':'^','▼':'v',
    '●':'*','○':'o','◆':'*','□':'[ ]','■':'[#]',
    '✅':'[OK]','❌':'[NO]','⚠':'[!]',
    '≥':'>=','≤':'<=','≠':'!=','±':'+/-',
    '\u2014':'--', '\u2013':'-', '\u2019':"'", '\u2018':"'",
    '\u201c':'"',  '\u201d':'"',
}

def sanitize(text):
    for old, new in BOX_MAP.items():
        text = text.replace(old, new)
    return text

def esc_xml(t):
    t = t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', t)
    t = re.sub(r'`(.+?)`',       r'<font name="Courier">\1</font>', t)
    return t

# ══════════════════════════════════════════════════════════════════════════════
# HYBRID MARKDOWN CONVERTER
# Keeps 100% of spec text; replaces DRAWINGS code blocks with vector diagrams
# ══════════════════════════════════════════════════════════════════════════════
def md_to_flowables(text, diagram_fns):
    """
    diagram_fns: list of diagram functions in order.
    When the parser hits the DRAWINGS section and encounters a code block,
    it pops the next diagram from the list and inserts it instead.
    All other code blocks are sanitized and rendered.
    """
    flowables = []
    lines = text.split('\n')
    i = 0
    in_drawings = False
    diag_idx = 0

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        # Track DRAWINGS section
        if re.match(r'^#{1,3}\s+DRAWINGS?', s, re.IGNORECASE):
            in_drawings = True

        # Blank line
        if not s:
            i += 1
            continue

        # Code block
        if s.startswith('```'):
            i += 1
            block_lines = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                block_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```

            if in_drawings and diag_idx < len(diagram_fns):
                # Insert vector diagram
                fn = diagram_fns[diag_idx]
                diag_idx += 1
                flowables.append(Spacer(1, 3*mm))
                flowables.append(renderPDF.GraphicsFlowable(fn(CW)))
                flowables.append(Spacer(1, 2*mm))
            else:
                # Sanitize and render as styled code
                raw = '\n'.join(block_lines)
                safe = sanitize(raw)
                # Split into lines and render as table rows
                code_lines = safe.split('\n')
                if code_lines:
                    text_content = '<br/>'.join(
                        ln.replace(' ', '&nbsp;')
                        for ln in code_lines
                    )
                    flowables.append(Paragraph(text_content, COD))
            continue

        # HR
        if s.startswith('---') and len(s) >= 3 and all(c=='-' for c in s):
            flowables.append(HRFlowable(width='100%', thickness=0.5,
                                        color=CGRAY, spaceBefore=4, spaceAfter=4))
            i += 1
            continue

        # Headings
        if s.startswith('#### '):
            flowables.append(Paragraph(esc_xml(s[5:].strip()), H4))
            i += 1; continue
        if s.startswith('### '):
            flowables.append(Paragraph(esc_xml(s[4:].strip()), H3))
            i += 1; continue
        if s.startswith('## '):
            flowables.append(Spacer(1, 2*mm))
            flowables.append(Paragraph(esc_xml(s[3:].strip()), H2))
            flowables.append(HRFlowable(width='60%', thickness=0.5, color=CGRAY, spaceAfter=3))
            i += 1; continue
        if s.startswith('# '):
            flowables.append(Spacer(1, 3*mm))
            flowables.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=4))
            flowables.append(Paragraph(esc_xml(s[2:].strip()), H1))
            i += 1; continue

        # Bullet
        if s.startswith('- ') or s.startswith('* '):
            flowables.append(Paragraph('•&nbsp;&nbsp;' + esc_xml(s[2:].strip()), BL))
            i += 1; continue

        # Numbered list
        if re.match(r'^\d+\.', s):
            content = re.sub(r'^\d+\.\s*', '', s)
            flowables.append(Paragraph('•&nbsp;&nbsp;' + esc_xml(content), BL))
            i += 1; continue

        # Italic-only line (e.g. *End of Specification*)
        if s.startswith('*') and s.endswith('*') and not s.startswith('**'):
            flowables.append(Paragraph(esc_xml(s), ITL))
            i += 1; continue

        # Bold-bold line
        if s.startswith('**') and s.endswith('**') and s.count('**') == 2:
            flowables.append(Paragraph(esc_xml(s), BB))
            i += 1; continue

        # Normal paragraph
        flowables.append(Paragraph(esc_xml(s), BD))
        i += 1

    return flowables

# ══════════════════════════════════════════════════════════════════════════════
# HEADER / FOOTER (same as F15)
# ══════════════════════════════════════════════════════════════════════════════
def make_on_page(docket):
    def on_page(c, doc):
        c.saveState()
        w, h = A4
        c.setFillColor(NAVY)
        c.rect(0, h-16*mm, w, 16*mm, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont('Helvetica-Bold', 11)
        c.drawString(LM, h-10*mm, 'OMNIX QUANTUM LTD')
        c.setFillColor(GOLD); c.setFont('Helvetica', 7)
        c.drawString(LM, h-14*mm, 'DECISION GOVERNANCE INFRASTRUCTURE')
        c.setFillColor(GOLD); c.setFont('Helvetica-Bold', 9)
        c.drawRightString(w-RM, h-9*mm, docket)
        c.setFillColor(colors.HexColor('#AABDD0')); c.setFont('Helvetica', 7)
        c.drawRightString(w-RM, h-13.5*mm, 'PROVISIONAL PATENT APPLICATION')
        c.setStrokeColor(GOLD); c.setLineWidth(1.5)
        c.line(0, h-16.5*mm, w, h-16.5*mm)
        c.setStrokeColor(colors.HexColor('#E0E0E0')); c.setLineWidth(0.5)
        c.line(LM, 14*mm, w-RM, 14*mm)
        c.setFillColor(MGRAY); c.setFont('Helvetica', 7)
        c.drawString(LM, 9*mm,
            f'CONFIDENTIAL -- PATENT PENDING -- {docket} -- Filed: April 19, 2026')
        c.drawRightString(w-RM, 9*mm, f'Page {c.getPageNumber()}')
        c.restoreState()
    return on_page

# ══════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════════════════════
def build_cover(docket, title, related):
    story = [Spacer(1, 16*mm)]
    # Company header
    co = Table([[Paragraph(
        '<font name="Helvetica-Bold" size="20" color="#0A1628">OMNIX QUANTUM LTD</font>',
        S('c', fontName='Helvetica-Bold', fontSize=20, textColor=NAVY, alignment=TA_CENTER)
    )]], colWidths=[CW])
    co.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),NAVY),('TOPPADDING',(0,0),(-1,-1),14),
        ('BOTTOMPADDING',(0,0),(-1,-1),10),('BOX',(0,0),(-1,-1),2,GOLD),
        ('ALIGN',(0,0),(-1,-1),'CENTER')]))
    story.append(co)
    story.append(Spacer(1,3*mm))
    story.append(Paragraph('DECISION GOVERNANCE INFRASTRUCTURE',
        S('tl',fontName='Helvetica',fontSize=10,textColor=GOLD,alignment=TA_CENTER,spaceAfter=6)))
    story.append(HRFlowable(width='80%',thickness=1,color=GOLD,spaceAfter=8))
    story.append(Paragraph('UNITED STATES PATENT AND TRADEMARK OFFICE',
        S('ul',fontName='Helvetica',fontSize=9,textColor=MGRAY,alignment=TA_CENTER,spaceAfter=3)))
    story.append(Paragraph('PROVISIONAL PATENT APPLICATION',
        S('ul2',fontName='Helvetica-Bold',fontSize=10,textColor=NAVY,alignment=TA_CENTER,spaceAfter=8)))
    story.append(Spacer(1,3*mm))
    story.append(Paragraph('TITLE OF INVENTION:',
        S('toi',fontName='Helvetica',fontSize=8.5,textColor=MGRAY,alignment=TA_CENTER,spaceAfter=4)))
    tt = Table([[Paragraph(title,
        S('tt',fontName='Helvetica-Bold',fontSize=12,textColor=NAVY,alignment=TA_CENTER,leading=17)
    )]], colWidths=[CW])
    tt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#E8EEF4')),
        ('TOPPADDING',(0,0),(-1,-1),14),('BOTTOMPADDING',(0,0),(-1,-1),14),
        ('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14),
        ('BOX',(0,0),(-1,-1),1,BLUE)]))
    story.append(tt)
    story.append(Spacer(1,6*mm))
    story.append(HRFlowable(width='50%',thickness=0.5,color=CGRAY,spaceAfter=6))
    meta = [
        ['Docket Number:',    docket],
        ['Inventor:',         'Harold Alberto Nunes Rodelo'],
        ['Applicant:',        'OMNIX QUANTUM LTD (United Kingdom)'],
        ['Entity Status:',    'Micro Entity -- 37 C.F.R. § 1.29'],
        ['Filing Basis:',     '35 U.S.C. § 111(b) -- Provisional Application'],
        ['Date Prepared:',    'April 19, 2026'],
        ['Date of Filing:',   'April 19, 2026'],
        ['Related Apps:',     related],
    ]
    mt = Table(meta, colWidths=[44*mm, CW-44*mm])
    mt.setStyle(TableStyle([
        ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),('FONTNAME',(1,0),(1,-1),'Helvetica'),
        ('FONTSIZE',(0,0),(-1,-1),9),('TEXTCOLOR',(0,0),(0,-1),NAVY),
        ('TEXTCOLOR',(1,0),(1,-1),DGRAY),('TOPPADDING',(0,0),(-1,-1),4),
        ('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),8),
        ('RIGHTPADDING',(0,0),(-1,-1),8),
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[WHITE,colors.HexColor('#F5F7FA')]),
        ('BOX',(0,0),(-1,-1),0.5,CGRAY),('INNERGRID',(0,0),(-1,-1),0.25,CGRAY)]))
    story.append(mt)
    story.append(Spacer(1,6*mm))
    story.append(HRFlowable(width='80%',thickness=1,color=GOLD,spaceAfter=6))
    story.append(Paragraph(
        'This document constitutes a Provisional Patent Application filed pursuant to '
        '35 U.S.C. § 111(b). It establishes a priority date and grants twelve (12) months '
        'from the filing date to submit a corresponding non-provisional application. '
        'CONFIDENTIAL -- NOT FOR DISTRIBUTION.',
        S('nt',fontName='Helvetica',fontSize=7.5,textColor=MGRAY,alignment=TA_JUSTIFY,leading=11)))
    story.append(PageBreak())
    return story

# ══════════════════════════════════════════════════════════════════════════════
# GENERATE ONE PDF
# ══════════════════════════════════════════════════════════════════════════════
def generate(spec_rel, out_file, docket, title, related, diagram_fns):
    spec_path = os.path.join(SPEC_DIR, spec_rel)
    out_path  = os.path.join(OUT_DIR, out_file)

    with open(spec_path, encoding='utf-8') as f:
        md_text = f.read()

    story = build_cover(docket, title, related)
    story += md_to_flowables(md_text, diagram_fns)

    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=20*mm, bottomMargin=18*mm,
        title=f'{docket} Provisional Patent Application',
        author='Harold Alberto Nunes Rodelo -- OMNIX QUANTUM LTD',
        subject=docket, creator='OMNIX Patent Generator v3')

    doc.build(story, onFirstPage=make_on_page(docket),
                     onLaterPages=make_on_page(docket))
    print(f'PDF generado: {out_path}')
    return out_path

# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':

    # F1 — Governance Control Architecture
    generate(
        spec_rel    = 'family_1/SPECIFICATION_FAMILY1.md',
        out_file    = 'OMNIX_PAT_2026_001_PROVISIONAL.pdf',
        docket      = 'OMNIX-PAT-2026-001',
        title       = 'GOVERNANCE CONTROL ARCHITECTURE FOR AUTOMATED DECISION SYSTEMS '
                      'WITH SEQUENTIAL VETO-AUTHORITY CHECKPOINTS, COUNTERFACTUAL RISK '
                      'FILTER CALIBRATION, AND SIGNAL CONTRADICTION DETECTION',
        related     = 'OMNIX-PAT-2026-002 (Non-Markovian Kernel), OMNIX-PAT-2026-003 (PQC Auth)',
        diagram_fns = [f1_fig1, f1_fig2, f1_fig3, f1_fig4],
    )

    # F10 — Merkle Transparency Chain
    generate(
        spec_rel    = 'family_10/SPECIFICATION_FAMILY10.md',
        out_file    = 'OMNIX_PAT_2026_010_PROVISIONAL.pdf',
        docket      = 'OMNIX-PAT-2026-010',
        title       = 'APPEND-ONLY POST-QUANTUM MERKLE TRANSPARENCY CHAIN FOR AUTOMATED '
                      'GOVERNANCE DECISION RECEIPTS WITH INTERNAL RFC-3161-STYLE TIMESTAMPING, '
                      'ROLLING HASH ACCUMULATION, AND TAMPER-EVIDENT PUBLIC VERIFICATION',
        related     = 'OMNIX-PAT-2026-001 (Governance Architecture), OMNIX-PAT-2026-003 (PQC Auth)',
        diagram_fns = [f10_fig1, f10_fig2, f10_fig3, f10_fig4],
    )

    # F14 — Bidirectional Temporal Admissibility
    generate(
        spec_rel    = 'family_14/SPECIFICATION_FAMILY14.md',
        out_file    = 'OMNIX_PAT_2026_014_PROVISIONAL.pdf',
        docket      = 'OMNIX-PAT-2026-014',
        title       = 'BIDIRECTIONAL TEMPORAL ADMISSIBILITY SYSTEM FOR AUTOMATED GOVERNANCE '
                      'DECISIONS WITH RETROSPECTIVE TRAJECTORY COHERENCE SCORING, PROSPECTIVE '
                      'REGIME TRANSITION RISK EVALUATION USING HIDDEN MARKOV MODEL TRANSITION '
                      'MATRICES, AND DUAL-SOURCE UNBIASED HISTORY ANALYSIS',
        related     = 'OMNIX-PAT-2026-001 (Governance Architecture), OMNIX-PAT-2026-012 (TIE), '
                      'OMNIX-PAT-2026-013 (Exit Layer)',
        diagram_fns = [f14_fig1, f14_fig2, f14_fig3, f14_fig4],
    )
