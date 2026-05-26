"""
RFC-ATF-6 PDF Generator — OMNIX QUANTUM
7 premium visual diagrams + technical content
Behavioral Execution Verification Protocol
"""
import os, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Image
)
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Polygon, Group, Circle, Wedge
)
from reportlab.graphics import renderPDF

# ── Colour palette (coherent with RFC-ATF-5) ──────────────────────────────────
DARK_BG      = colors.HexColor('#0d0d1a')
ACCENT_BLUE  = colors.HexColor('#5b5bd6')
ACCENT_LIGHT = colors.HexColor('#8b8bf0')
ACCENT_GOLD  = colors.HexColor('#d4a843')
ACCENT_TEAL  = colors.HexColor('#2db5a0')
ACCENT_RED   = colors.HexColor('#e05252')
ACCENT_ORANGE= colors.HexColor('#e07842')
ACCENT_GREEN = colors.HexColor('#3db87a')
TEXT_WHITE   = colors.HexColor('#f0f0f0')
TEXT_GRAY    = colors.HexColor('#aaaaaa')
BORDER_GRAY  = colors.HexColor('#333355')
CODE_BG      = colors.HexColor('#1a1a2e')
TABLE_HEAD   = colors.HexColor('#1e1e3a')
TABLE_ALT    = colors.HexColor('#141428')
TABLE_BORDER = colors.HexColor('#2a2a4a')
RULE_COLOR   = colors.HexColor('#3a3a5a')
WHITE        = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm
INNER_W = PAGE_W - 2 * MARGIN
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(ROOT, 'omnix_web', 'public', 'logo_nobg.png')
OUT  = os.path.join(ROOT, 'docs', 'zenodo', 'rfc_atf_6', 'RFC-ATF-6.pdf')


# ── Page templates ─────────────────────────────────────────────────────────────
def cover_page(c, doc):
    c.saveState()
    c.setFillColor(DARK_BG); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(ACCENT_BLUE); c.rect(0, PAGE_H - 8*mm, PAGE_W, 8*mm, fill=1, stroke=0)
    c.setFillColor(ACCENT_GOLD); c.rect(0, 0, PAGE_W, 6*mm, fill=1, stroke=0)
    c.restoreState()

def normal_page(c, doc):
    c.saveState()
    c.setFillColor(DARK_BG); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(ACCENT_BLUE); c.rect(0, PAGE_H - 4*mm, PAGE_W, 4*mm, fill=1, stroke=0)
    c.setFillColor(TABLE_HEAD); c.rect(0, 0, PAGE_W, 12*mm, fill=1, stroke=0)
    c.setFont('Helvetica', 7); c.setFillColor(TEXT_GRAY)
    c.drawString(MARGIN, 4*mm, 'RFC-ATF-6 — Behavioral Execution Verification Protocol — OMNIX QUANTUM LTD — omnixquantum.net')
    c.drawRightString(PAGE_W - MARGIN, 4*mm, f'Page {doc.page}')
    c.setStrokeColor(RULE_COLOR); c.setLineWidth(0.5)
    c.line(MARGIN, 12*mm, PAGE_W - MARGIN, 12*mm)
    c.restoreState()

def on_page(c, doc):
    cover_page(c, doc) if doc.page == 1 else normal_page(c, doc)


# ── Paragraph styles ───────────────────────────────────────────────────────────
def S():
    s = {}
    s['badge']   = ParagraphStyle('badge',   fontName='Helvetica-Bold',    fontSize=9,   leading=14, textColor=ACCENT_GOLD)
    s['tier']    = ParagraphStyle('tier',    fontName='Helvetica-Bold',    fontSize=9,   leading=14, textColor=ACCENT_LIGHT)
    s['ctitle']  = ParagraphStyle('ctitle',  fontName='Helvetica-Bold',    fontSize=24,  leading=32, textColor=WHITE, spaceAfter=6)
    s['csub']    = ParagraphStyle('csub',    fontName='Helvetica',         fontSize=14,  leading=20, textColor=ACCENT_LIGHT, spaceAfter=18)
    s['cmeta']   = ParagraphStyle('cmeta',   fontName='Helvetica',         fontSize=10,  leading=16, textColor=TEXT_GRAY, spaceAfter=4)
    s['atitle']  = ParagraphStyle('atitle',  fontName='Helvetica-Bold',    fontSize=10,  leading=14, textColor=ACCENT_LIGHT, spaceAfter=4)
    s['abody']   = ParagraphStyle('abody',   fontName='Helvetica',         fontSize=9.5, leading=15, textColor=TEXT_WHITE, alignment=TA_JUSTIFY, spaceAfter=6)
    s['h1']      = ParagraphStyle('h1',      fontName='Helvetica-Bold',    fontSize=15,  leading=20, textColor=WHITE, spaceBefore=18, spaceAfter=8)
    s['h2']      = ParagraphStyle('h2',      fontName='Helvetica-Bold',    fontSize=11.5,leading=16, textColor=ACCENT_LIGHT, spaceBefore=14, spaceAfter=5)
    s['h3']      = ParagraphStyle('h3',      fontName='Helvetica-Bold',    fontSize=10,  leading=14, textColor=TEXT_GRAY, spaceBefore=10, spaceAfter=4)
    s['body']    = ParagraphStyle('body',    fontName='Helvetica',         fontSize=9.5, leading=15, textColor=TEXT_WHITE, alignment=TA_JUSTIFY, spaceAfter=6)
    s['bullet']  = ParagraphStyle('bullet',  fontName='Helvetica',         fontSize=9.5, leading=15, textColor=TEXT_WHITE, leftIndent=16, firstLineIndent=-8, spaceAfter=2)
    s['code']    = ParagraphStyle('code',    fontName='Courier',           fontSize=7.5, leading=11, textColor=TEXT_WHITE, leftIndent=4, backColor=CODE_BG)
    s['caption'] = ParagraphStyle('caption', fontName='Helvetica-Oblique', fontSize=8,   leading=12, textColor=TEXT_GRAY, alignment=TA_CENTER, spaceBefore=2)
    s['ref']     = ParagraphStyle('ref',     fontName='Helvetica',         fontSize=8.5, leading=13, textColor=TEXT_GRAY, leftIndent=16, firstLineIndent=-16, spaceAfter=2)
    s['gold']    = ParagraphStyle('gold',    fontName='Helvetica-Bold',    fontSize=10,  leading=14, textColor=ACCENT_GOLD)
    s['quote']   = ParagraphStyle('quote',   fontName='Helvetica-Oblique', fontSize=10,  leading=16, textColor=ACCENT_LIGHT, alignment=TA_CENTER)
    s['inv']     = ParagraphStyle('inv',     fontName='Courier',           fontSize=8,   leading=12, textColor=ACCENT_TEAL, leftIndent=4)
    return s

def sp(n=6):   return Spacer(1, n)
def rule(s):   return HRFlowable(width='100%', thickness=0.5, color=RULE_COLOR, spaceAfter=6, spaceBefore=6)
def arule():   return HRFlowable(width='40%',  thickness=1.5, color=ACCENT_BLUE, spaceAfter=20)


def cb(text, s):
    lines = text.strip().split('\n')
    rows = [[Paragraph(l.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'), s['code'])] for l in lines]
    return Table(rows, colWidths=[INNER_W - 12*mm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
            ('LEFTPADDING', (0,0), (-1,-1), 8),  ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING',  (0,0), (-1,-1), 2),  ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER_GRAY),
        ]))


def tbl(headers, rows, s, cw=None):
    hs = ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=8, leading=12, textColor=ACCENT_LIGHT)
    cs = ParagraphStyle('td', fontName='Helvetica',      fontSize=8, leading=12, textColor=TEXT_WHITE)
    cg = ParagraphStyle('tg', fontName='Helvetica',      fontSize=8, leading=12, textColor=TEXT_GRAY)
    data = [[Paragraph(h, hs) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), cs if i < 2 else cg) for i, c in enumerate(row)])
    style = TableStyle([
        ('BACKGROUND',  (0,0), (-1,0),  TABLE_HEAD),
        ('BACKGROUND',  (0,1), (-1,-1), TABLE_ALT),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [TABLE_ALT, DARK_BG]),
        ('GRID',        (0,0), (-1,-1), 0.4, TABLE_BORDER),
        ('LEFTPADDING', (0,0), (-1,-1), 6),  ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING',  (0,0), (-1,-1), 4),  ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
    ])
    return Table(data, colWidths=cw, style=style, hAlign='LEFT', repeatRows=1)


def inv_box(inv_id, title, statement, formal, s):
    badge_style = ParagraphStyle('ibadge', fontName='Helvetica-Bold', fontSize=8, leading=10,
                                 textColor=ACCENT_TEAL)
    title_style = ParagraphStyle('ititle', fontName='Helvetica-Bold', fontSize=9, leading=13,
                                 textColor=TEXT_WHITE)
    body_style  = ParagraphStyle('ibody',  fontName='Helvetica',      fontSize=8.5, leading=13,
                                 textColor=TEXT_WHITE)
    code_style  = ParagraphStyle('icode',  fontName='Courier',        fontSize=7.5, leading=11,
                                 textColor=ACCENT_LIGHT)
    rows = [
        [Paragraph(f'{inv_id}', badge_style),
         Paragraph(f'{title}', title_style)],
        [Paragraph('Statement:', ParagraphStyle('lbl', fontName='Helvetica-Bold', fontSize=8,
                                                textColor=TEXT_GRAY)),
         Paragraph(statement, body_style)],
        [Paragraph('Formal:', ParagraphStyle('lbl', fontName='Helvetica-Bold', fontSize=8,
                                             textColor=TEXT_GRAY)),
         Paragraph(formal.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'), code_style)],
    ]
    t = Table(rows, colWidths=[28*mm, INNER_W - 28*mm - 12*mm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
            ('BOX', (0,0), (-1,-1), 0.6, ACCENT_TEAL),
            ('LINEAFTER', (0,0), (0,-1), 0.4, BORDER_GRAY),
            ('LEFTPADDING', (0,0), (-1,-1), 7), ('RIGHTPADDING', (0,0), (-1,-1), 7),
            ('TOPPADDING', (0,0), (-1,-1), 5),  ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('SPAN', (0,0), (0,0)), ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
    return KeepTogether([t, sp(6)])


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 1 — ATF 6-Layer Stack
# ══════════════════════════════════════════════════════════════════════════════
def diagram_atf_stack():
    W, H = INNER_W, 200
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=CODE_BG, strokeColor=BORDER_GRAY, strokeWidth=0.5))

    layers = [
        ("Layer 1", "RFC-ATF-1", "Identity & Delegation",      "AIR · DR",             ACCENT_BLUE),
        ("Layer 2", "RFC-ATF-2", "Runtime Continuity",         "TAR · RCR · AFG",      colors.HexColor('#4a7cc7')),
        ("Layer 3", "RFC-ATF-3", "Evidence Lifecycle",         "OEP · GPIL · FEA",     ACCENT_TEAL),
        ("Layer 4", "RFC-ATF-4", "Proactive Governance",       "AGVP · DSPP · SSD",    colors.HexColor('#7a5bb5')),
        ("Layer 5", "RFC-ATF-5", "Cognitive Governance",       "CGE · GUGT · TGB",     colors.HexColor('#9b59b6')),
        ("Layer 6", "RFC-ATF-6", "Behavioral Exec. Verif.",    "BAR · CCS · CTCHC",    ACCENT_GOLD),
    ]

    bar_h = 22
    gap   = 5
    start_y = 18
    label_x = 8

    for i, (lnum, rfc, title, comps, col) in enumerate(reversed(layers)):
        y = start_y + i * (bar_h + gap)
        is_bev = (i == 5)

        fill = col if is_bev else colors.HexColor(
            '#%02x%02x%02x' % (
                int(col.red*255*0.25 + 0.03*255),
                int(col.green*255*0.25 + 0.03*255),
                int(col.blue*255*0.25 + 0.03*255)
            )
        )
        stroke_w = 1.5 if is_bev else 0.5
        d.add(Rect(label_x, y, W - 2*label_x, bar_h,
                   fillColor=fill, strokeColor=col, strokeWidth=stroke_w))

        fc = DARK_BG if is_bev else col
        tc = DARK_BG if is_bev else TEXT_WHITE

        d.add(String(label_x + 8, y + bar_h/2 + 3,  lnum,
                     fontName='Helvetica-Bold', fontSize=7, fillColor=fc))
        d.add(String(label_x + 8, y + bar_h/2 - 5,  rfc,
                     fontName='Helvetica-Bold', fontSize=7, fillColor=fc))
        d.add(String(label_x + 55, y + bar_h/2 + 3, title,
                     fontName='Helvetica-Bold', fontSize=8.5, fillColor=tc))
        d.add(String(label_x + 55, y + bar_h/2 - 6, comps,
                     fontName='Helvetica',      fontSize=7.5, fillColor=fc if not is_bev else DARK_BG))

        inv_counts = [6, 14, 40, 70, 88, 106]
        inv_label  = f'{inv_counts[len(layers)-1-i]} inv.'
        d.add(String(W - label_x - 50, y + bar_h/2 - 3, inv_label,
                     fontName='Helvetica-Bold', fontSize=8,
                     fillColor=ACCENT_GOLD if is_bev else TEXT_GRAY))

    # Title
    d.add(String(W/2, H - 11, "ATF Protocol Stack — 6 Layers · 106 Invariants",
                 fontName='Helvetica-Bold', fontSize=9, fillColor=TEXT_WHITE,
                 textAnchor='middle'))

    return d


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 2 — BAR Architecture Flow
# ══════════════════════════════════════════════════════════════════════════════
def diagram_bar_flow():
    W, H = INNER_W, 140
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=CODE_BG, strokeColor=BORDER_GRAY, strokeWidth=0.5))

    steps = [
        ("Agent\nOutput",       "output_text",              ACCENT_BLUE),
        ("SHA3-256\n(output)",  "output_hash",              ACCENT_TEAL),
        ("Hash\nBinding",       "SHA3-256\n(out‖rcpt‖idx)", ACCENT_LIGHT),
        ("content\n_hash",      "64-char hex",              colors.HexColor('#7a5bb5')),
        ("ML-DSA-65\nSign",     "Dilithium-3",              ACCENT_ORANGE),
        ("SEALED\nBAR",         "persisted\nDB+PQC",        ACCENT_GOLD),
    ]

    box_w = 34
    box_h = 42
    gap   = (W - len(steps)*box_w - 2*8) / (len(steps) - 1)
    start_x = 8
    cy = H / 2 - 5

    for i, (top, bot, col) in enumerate(steps):
        x = start_x + i * (box_w + gap)
        is_last = (i == len(steps) - 1)
        fill = col if is_last else colors.HexColor(
            '#%02x%02x%02x' % (
                max(0, min(255, int(col.red*255*0.2 + 10))),
                max(0, min(255, int(col.green*255*0.2 + 10))),
                max(0, min(255, int(col.blue*255*0.2 + 10))),
            )
        )
        d.add(Rect(x, cy - box_h/2, box_w, box_h,
                   fillColor=fill, strokeColor=col, strokeWidth=1.5 if is_last else 0.8))

        tc = DARK_BG if is_last else col
        lines_top = top.split('\n')
        lines_bot = bot.split('\n')
        for j, ln in enumerate(lines_top):
            d.add(String(x + box_w/2, cy + box_h/4 + 5 - j*9, ln,
                         fontName='Helvetica-Bold', fontSize=7,
                         fillColor=tc, textAnchor='middle'))
        for j, ln in enumerate(lines_bot):
            d.add(String(x + box_w/2, cy - 5 - j*8, ln,
                         fontName='Helvetica', fontSize=6.5,
                         fillColor=tc if is_last else TEXT_GRAY, textAnchor='middle'))

        if i < len(steps) - 1:
            ax = x + box_w + 3
            ay = cy
            d.add(Line(ax, ay, ax + gap - 6, ay,
                       strokeColor=TEXT_GRAY, strokeWidth=1))
            d.add(Polygon([ax+gap-6, ay, ax+gap-3, ay+4, ax+gap-3, ay-4],
                          fillColor=TEXT_GRAY, strokeColor=TEXT_GRAY, strokeWidth=0))

    # Bottom annotation
    d.add(String(W/2, 10, "content_hash = SHA3-256(output_hash  ‖  governing_receipt_id  ‖  str(turn_index))   ·   pqc_algorithm = ML-DSA-65",
                 fontName='Courier', fontSize=7, fillColor=ACCENT_TEAL, textAnchor='middle'))
    d.add(String(W/2, H - 11, "Behavioral Anchor Record (BAR) — PQC-Sealed Per-Turn Attestation",
                 fontName='Helvetica-Bold', fontSize=9, fillColor=TEXT_WHITE, textAnchor='middle'))
    return d


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 3 — CCS Score Breakdown + Verdict Ladder
# ══════════════════════════════════════════════════════════════════════════════
def diagram_ccs_score():
    W, H = INNER_W, 180
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=CODE_BG, strokeColor=BORDER_GRAY, strokeWidth=0.5))

    d.add(String(W/2, H - 11, "Constraint Conformance Signal (CCS) — Score Components & Verdict Ladder",
                 fontName='Helvetica-Bold', fontSize=9, fillColor=TEXT_WHITE, textAnchor='middle'))

    # Left: 4 components as horizontal stacked bars
    left_w = W * 0.52
    comps = [
        ("Output Boundary Score (OBS)",       40, ACCENT_BLUE,    "max(0, 40 − 10×violations)"),
        ("Constraint Satisfaction Score (CSS)",30, ACCENT_TEAL,    "max(0, 30 − 8×failures)"),
        ("Semantic Drift Score (SDS)",         20, colors.HexColor('#7a5bb5'), "max(0, 20×(1−drift_mag))"),
        ("Authority Alignment Score (AAS)",    10, ACCENT_ORANGE,  "10 if in scope else 0"),
    ]

    bar_start_y = 18
    bar_h = 24
    gap   = 8
    max_pts = 100.0
    bar_max_w = left_w - 70

    for i, (name, pts, col, formula) in enumerate(comps):
        y = bar_start_y + i * (bar_h + gap)
        fill_w = (pts / max_pts) * bar_max_w
        d.add(Rect(62, y, bar_max_w, bar_h,
                   fillColor=colors.HexColor('#1a1a2e'), strokeColor=BORDER_GRAY, strokeWidth=0.4))
        d.add(Rect(62, y, fill_w, bar_h,
                   fillColor=col, strokeColor=col, strokeWidth=0))
        d.add(String(60, y + bar_h/2 + 3,  f'{pts} pts',
                     fontName='Helvetica-Bold', fontSize=8, fillColor=col, textAnchor='end'))
        # Short name + formula
        short = name.split('(')[1].rstrip(')') if '(' in name else name[:3]
        d.add(String(65, y + bar_h/2 + 3,  name.split(' Score')[0],
                     fontName='Helvetica-Bold', fontSize=7.5, fillColor=WHITE))
        d.add(String(65, y + bar_h/2 - 6,  formula,
                     fontName='Courier', fontSize=6.5, fillColor=TEXT_GRAY))

    d.add(String(62 + bar_max_w/2, bar_start_y + 4*(bar_h+gap) + 4,
                 "Total score ÷ 100  →  conformance_score ∈ [0.0, 1.0]",
                 fontName='Helvetica-Bold', fontSize=7.5, fillColor=ACCENT_GOLD, textAnchor='middle'))

    # Right: Verdict ladder
    right_x = left_w + 10
    verdicts = [
        ("CONFORMANT", "≥ 90.0", ACCENT_GREEN,  "Outputs fully within bounds"),
        ("DRIFTING",   "70–89.9", ACCENT_TEAL,  "AGVP PVR: MONITORING"),
        ("BREACH",     "50–69.9", ACCENT_ORANGE, "AGVP PVR: WARNING"),
        ("VIOLATION",  "< 50.0",  ACCENT_RED,    "HALT PROPAGATION"),
        ("NO_DATA",    "−1.0",    TEXT_GRAY,     "CCS_ENABLED=false / REDACTED"),
    ]

    v_bar_h = 24
    v_gap   = 6
    v_y_start = 18
    v_w = W - right_x - 8

    for i, (verdict, score, col, note) in enumerate(verdicts):
        y = v_y_start + i * (v_bar_h + v_gap)
        is_halt = verdict == "VIOLATION"
        d.add(Rect(right_x, y, v_w, v_bar_h,
                   fillColor=colors.HexColor(
                       '#%02x%02x%02x' % (
                           max(0, min(255, int(col.red*255*0.25 + 8))),
                           max(0, min(255, int(col.green*255*0.25 + 8))),
                           max(0, min(255, int(col.blue*255*0.25 + 8))),
                       )
                   ),
                   strokeColor=col, strokeWidth=1.5 if is_halt else 0.8))
        d.add(String(right_x + 5, y + v_bar_h/2 + 3,
                     verdict, fontName='Helvetica-Bold', fontSize=8.5, fillColor=col))
        d.add(String(right_x + 5, y + v_bar_h/2 - 6,
                     f'{score}  ·  {note}', fontName='Helvetica', fontSize=7, fillColor=TEXT_GRAY))

    # Divider
    d.add(Line(left_w + 4, 12, left_w + 4, H - 16,
               strokeColor=BORDER_GRAY, strokeWidth=0.5))
    d.add(String(right_x + v_w/2, H - 11,
                 "Verdict Thresholds", fontName='Helvetica-Bold', fontSize=8,
                 fillColor=TEXT_GRAY, textAnchor='middle'))

    return d


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 4 — CTCHC Chain Structure
# ══════════════════════════════════════════════════════════════════════════════
def diagram_ctchc_chain():
    W, H = INNER_W, 150
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=CODE_BG, strokeColor=BORDER_GRAY, strokeWidth=0.5))

    d.add(String(W/2, H - 11, "Cross-Turn Coherence Hash Chain (CTCHC) — Session Integrity Proof",
                 fontName='Helvetica-Bold', fontSize=9, fillColor=TEXT_WHITE, textAnchor='middle'))

    nodes = [
        ("GENESIS\nHASH",  "SHA3-256\n(session_id‖\nreceipt_id‖\nGENESIS)",  ACCENT_TEAL),
        ("BAR[0]\nLink",   "SHA3-256\n({prev:genesis,\nturn:h0,rcpt})",        ACCENT_BLUE),
        ("BAR[1]\nLink",   "SHA3-256\n({prev:link0,\nturn:h1,rcpt})",          ACCENT_BLUE),
        ("BAR[n]\nLink",   "SHA3-256\n({prev:link_{n-1},\nturn:hn,rcpt})",     ACCENT_BLUE),
        ("CHAIN\nSEAL",    "ML-DSA-65\nseal_hash\n(SIP)",                       ACCENT_GOLD),
    ]

    box_w = 38
    box_h = 72
    n = len(nodes)
    total_boxes = n * box_w
    total_gaps = W - 16 - total_boxes
    gap = total_gaps / (n - 1)
    start_x = 8
    cy = 40 + box_h/2

    # Ellipsis between BAR[1] and BAR[n]
    for i, (label, sub, col) in enumerate(nodes):
        x = start_x + i * (box_w + gap)
        is_last = (i == n - 1)
        is_first = (i == 0)

        fill = col if is_last or is_first else colors.HexColor(
            '#%02x%02x%02x' % (
                max(0, min(255, int(col.red*255*0.2 + 10))),
                max(0, min(255, int(col.green*255*0.2 + 10))),
                max(0, min(255, int(col.blue*255*0.2 + 10))),
            )
        )
        sw = 1.8 if (is_last or is_first) else 0.8
        d.add(Rect(x, cy - box_h/2, box_w, box_h,
                   fillColor=fill, strokeColor=col, strokeWidth=sw))

        tc = DARK_BG if (is_last or is_first) else col
        lines = label.split('\n')
        for j, ln in enumerate(lines):
            d.add(String(x + box_w/2, cy + box_h/4 + 5 - j*10, ln,
                         fontName='Helvetica-Bold', fontSize=7.5,
                         fillColor=tc, textAnchor='middle'))
        sub_lines = sub.split('\n')
        for j, ln in enumerate(sub_lines):
            d.add(String(x + box_w/2, cy - 10 - j*8.5, ln,
                         fontName='Courier', fontSize=5.8,
                         fillColor=tc if (is_last or is_first) else TEXT_GRAY,
                         textAnchor='middle'))

        # Arrow
        if i < n - 1:
            # Show "..." between index 2 and 3
            if i == 2:
                mx = x + box_w + gap/2
                d.add(String(mx, cy, "· · ·",
                             fontName='Helvetica-Bold', fontSize=12,
                             fillColor=TEXT_GRAY, textAnchor='middle'))
            else:
                ax = x + box_w + 2
                ay = cy
                d.add(Line(ax, ay, ax + gap - 8, ay,
                           strokeColor=TEXT_GRAY, strokeWidth=1.2))
                d.add(Polygon([ax+gap-8, ay, ax+gap-4, ay+4, ax+gap-4, ay-4],
                              fillColor=TEXT_GRAY, strokeColor=TEXT_GRAY, strokeWidth=0))

    # Bottom legend
    d.add(String(W/2, 10,
                 "Every link: SHA3-256({\"prev\": prev_hash, \"turn\": output_hash, \"receipt\": receipt_id}, sort_keys=True)  ·  chain_sealed=True → Session Integrity Proof (SIP)",
                 fontName='Courier', fontSize=6.5, fillColor=ACCENT_TEAL, textAnchor='middle'))
    return d


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 5 — CCS-AGVP Integration Loop
# ══════════════════════════════════════════════════════════════════════════════
def diagram_agvp_loop():
    W, H = INNER_W, 200
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=CODE_BG, strokeColor=BORDER_GRAY, strokeWidth=0.5))

    d.add(String(W/2, H - 11, "CCS ↔ AGVP Integration Loop — Behavioral Conformance → Anticipatory Veto",
                 fontName='Helvetica-Bold', fontSize=9, fillColor=TEXT_WHITE, textAnchor='middle'))

    # Main pipeline: left to right
    # Agent Turn → [BAR+CCS produced] → Verdict? → branch
    pipe_y = H/2 + 10
    boxes = [
        (22,  "Agent\nExecution\nTurn",   ACCENT_BLUE),
        (105, "BAR + CCS\nProduced\n(atomic)", ACCENT_TEAL),
        (188, "Verdict\nCheck",           colors.HexColor('#7a5bb5')),
    ]
    bw, bh = 58, 48
    for (cx, label, col) in boxes:
        fill = colors.HexColor('#%02x%02x%02x' % (
            max(0,min(255,int(col.red*255*0.2+10))),
            max(0,min(255,int(col.green*255*0.2+10))),
            max(0,min(255,int(col.blue*255*0.2+10))),
        ))
        d.add(Rect(cx - bw/2, pipe_y - bh/2, bw, bh,
                   fillColor=fill, strokeColor=col, strokeWidth=1.2))
        for j, ln in enumerate(label.split('\n')):
            d.add(String(cx, pipe_y + 8 - j*11, ln,
                         fontName='Helvetica-Bold', fontSize=8, fillColor=col,
                         textAnchor='middle'))

    # Arrows between pipeline boxes
    for i in range(len(boxes) - 1):
        ax = boxes[i][0] + bw/2 + 1
        ay = pipe_y
        ex = boxes[i+1][0] - bw/2 - 1
        d.add(Line(ax, ay, ex - 6, ay, strokeColor=TEXT_GRAY, strokeWidth=1.2))
        d.add(Polygon([ex-6, ay, ex-2, ay+4, ex-2, ay-4],
                      fillColor=TEXT_GRAY, strokeColor=TEXT_GRAY, strokeWidth=0))

    # Branch from Verdict Check
    verdict_cx = boxes[2][0]
    branch_x_right = verdict_cx + bw/2

    # CONFORMANT → Continue
    conf_y = pipe_y + bh/2 + 30
    cont_x = W - 55
    d.add(Rect(cont_x - 28, conf_y - 14, 60, 28,
               fillColor=colors.HexColor('#0d2015'), strokeColor=ACCENT_GREEN, strokeWidth=1))
    d.add(String(cont_x + 2, conf_y + 3, "CONFORMANT",
                 fontName='Helvetica-Bold', fontSize=7.5, fillColor=ACCENT_GREEN, textAnchor='middle'))
    d.add(String(cont_x + 2, conf_y - 7, "Next turn authorized",
                 fontName='Helvetica', fontSize=6.5, fillColor=TEXT_GRAY, textAnchor='middle'))
    d.add(Line(branch_x_right, pipe_y, cont_x - 28, conf_y,
               strokeColor=ACCENT_GREEN, strokeWidth=1))

    # DRIFTING → PVR MONITORING
    drift_y = conf_y + 50
    drift_x = W - 55
    d.add(Rect(drift_x - 28, drift_y - 14, 60, 28,
               fillColor=colors.HexColor('#0d1a2a'), strokeColor=ACCENT_TEAL, strokeWidth=1))
    d.add(String(drift_x + 2, drift_y + 3, "DRIFTING",
                 fontName='Helvetica-Bold', fontSize=7.5, fillColor=ACCENT_TEAL, textAnchor='middle'))
    d.add(String(drift_x + 2, drift_y - 7, "PVR: MONITORING",
                 fontName='Helvetica', fontSize=6.5, fillColor=TEXT_GRAY, textAnchor='middle'))
    d.add(Line(branch_x_right + 5, pipe_y + 8, drift_x - 28, drift_y,
               strokeColor=ACCENT_TEAL, strokeWidth=1))

    # BREACH → PVR WARNING
    breach_y = drift_y + 48
    breach_x = W - 55
    d.add(Rect(breach_x - 28, breach_y - 14, 60, 28,
               fillColor=colors.HexColor('#1e150a'), strokeColor=ACCENT_ORANGE, strokeWidth=1))
    d.add(String(breach_x + 2, breach_y + 3, "BREACH",
                 fontName='Helvetica-Bold', fontSize=7.5, fillColor=ACCENT_ORANGE, textAnchor='middle'))
    d.add(String(breach_x + 2, breach_y - 7, "PVR: WARNING",
                 fontName='Helvetica', fontSize=6.5, fillColor=TEXT_GRAY, textAnchor='middle'))
    d.add(Line(branch_x_right + 5, pipe_y + 14, breach_x - 28, breach_y,
               strokeColor=ACCENT_ORANGE, strokeWidth=1))

    # VIOLATION → HALT
    halt_y = breach_y + 45
    halt_x = W - 55
    d.add(Rect(halt_x - 28, halt_y - 16, 60, 32,
               fillColor=colors.HexColor('#200808'), strokeColor=ACCENT_RED, strokeWidth=2))
    d.add(String(halt_x + 2, halt_y + 5, "VIOLATION",
                 fontName='Helvetica-Bold', fontSize=8, fillColor=ACCENT_RED, textAnchor='middle'))
    d.add(String(halt_x + 2, halt_y - 5, "HALT PROPAGATION",
                 fontName='Helvetica-Bold', fontSize=7, fillColor=ACCENT_RED, textAnchor='middle'))
    d.add(String(halt_x + 2, halt_y - 15, "Session terminated",
                 fontName='Helvetica', fontSize=6.5, fillColor=TEXT_GRAY, textAnchor='middle'))
    d.add(Line(branch_x_right + 5, pipe_y + 18, halt_x - 28, halt_y,
               strokeColor=ACCENT_RED, strokeWidth=1.5))

    # AGVP label box (center)
    agvp_cx = 105
    agvp_y  = pipe_y - bh/2 - 42
    d.add(Rect(agvp_cx - 50, agvp_y - 14, 100, 28,
               fillColor=colors.HexColor('#1a0d2e'), strokeColor=ACCENT_LIGHT, strokeWidth=1))
    d.add(String(agvp_cx, agvp_y + 4, "AGVP Watchdog",
                 fontName='Helvetica-Bold', fontSize=8.5, fillColor=ACCENT_LIGHT, textAnchor='middle'))
    d.add(String(agvp_cx, agvp_y - 7, "Anticipatory Governance Veto Protocol (RFC-ATF-4)",
                 fontName='Helvetica', fontSize=6.5, fillColor=TEXT_GRAY, textAnchor='middle'))
    d.add(Line(agvp_cx, agvp_y + 14, agvp_cx, pipe_y - bh/2,
               strokeColor=ACCENT_LIGHT, strokeWidth=1, strokeDashArray=[3, 2]))
    d.add(String(agvp_cx - 3, (agvp_y + 14 + pipe_y - bh/2)/2 + 2,
                 "PVR issued", fontName='Helvetica', fontSize=6.5, fillColor=ACCENT_LIGHT))

    return d


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 6 — Three Behavioral Gaps → BEV Closes All
# ══════════════════════════════════════════════════════════════════════════════
def diagram_behavioral_gaps():
    W, H = INNER_W, 190
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=CODE_BG, strokeColor=BORDER_GRAY, strokeWidth=0.5))

    d.add(String(W/2, H - 11, "The Behavioral Execution Gap — Three Structural Problems Closed by BEV",
                 fontName='Helvetica-Bold', fontSize=9, fillColor=TEXT_WHITE, textAnchor='middle'))

    cols_data = [
        {
            "gap": "Gap_BAG",
            "name": "Behavioral\nAttestation Gap",
            "problem": "Authorization → ??? → Output\nNo cryptographic binding\nbetween GR and BO",
            "solution": "BAR closes Gap_BAG\nPQC-signed record of\nactual agent output\nper turn",
            "col": ACCENT_BLUE,
            "inv": "BEV-INV-001–004\nBEV-INV-015–016",
        },
        {
            "gap": "Gap_COP",
            "name": "Conformance\nObservability",
            "problem": "No governance-native\nbehavioral signal\nfor AGVP watchdog",
            "solution": "CCS closes Gap_COP\nconformance_score [0,1]\nper turn · AGVP\nintegration complete",
            "col": ACCENT_TEAL,
            "inv": "BEV-INV-005–009\nBEV-INV-017",
        },
        {
            "gap": "Gap_MCP",
            "name": "Multi-Turn\nCoherence",
            "problem": "No session integrity\nproof across turns\nOMISSION undetectable",
            "solution": "CTCHC closes Gap_MCP\nHash chain per turn\noffline-verifiable SIP\nML-DSA-65 sealed",
            "col": colors.HexColor('#9b59b6'),
            "inv": "BEV-INV-010–014\nBEV-INV-018",
        },
    ]

    col_w = (W - 24) / 3
    for i, cd in enumerate(cols_data):
        cx = 8 + i * (col_w + 4)
        col = cd['col']
        faint = colors.HexColor('#%02x%02x%02x' % (
            max(0,min(255,int(col.red*255*0.15+8))),
            max(0,min(255,int(col.green*255*0.15+8))),
            max(0,min(255,int(col.blue*255*0.15+8))),
        ))

        # Header
        d.add(Rect(cx, H - 30, col_w, 18,
                   fillColor=col, strokeColor=col, strokeWidth=0))
        d.add(String(cx + col_w/2, H - 18, cd['gap'],
                     fontName='Helvetica-Bold', fontSize=10,
                     fillColor=DARK_BG, textAnchor='middle'))

        # Name
        for j, ln in enumerate(cd['name'].split('\n')):
            d.add(String(cx + col_w/2, H - 36 - j*10, ln,
                         fontName='Helvetica-Bold', fontSize=8.5,
                         fillColor=col, textAnchor='middle'))

        # Problem box
        prob_y = H - 78
        prob_h = 52
        d.add(Rect(cx + 2, prob_y, col_w - 4, prob_h,
                   fillColor=colors.HexColor('#200808'), strokeColor=ACCENT_RED, strokeWidth=0.8))
        d.add(String(cx + col_w/2, prob_y + prob_h - 8, "PROBLEM",
                     fontName='Helvetica-Bold', fontSize=7,
                     fillColor=ACCENT_RED, textAnchor='middle'))
        for j, ln in enumerate(cd['problem'].split('\n')):
            d.add(String(cx + col_w/2, prob_y + prob_h - 20 - j*10, ln,
                         fontName='Helvetica', fontSize=7,
                         fillColor=TEXT_GRAY, textAnchor='middle'))

        # Arrow down
        ay = prob_y - 4
        d.add(Line(cx + col_w/2, ay, cx + col_w/2, ay - 10,
                   strokeColor=ACCENT_GREEN, strokeWidth=1.5))
        d.add(Polygon([cx + col_w/2, ay - 10, cx + col_w/2 - 5, ay - 5, cx + col_w/2 + 5, ay - 5],
                      fillColor=ACCENT_GREEN, strokeColor=ACCENT_GREEN, strokeWidth=0))

        # Solution box
        sol_y = 42
        sol_h = 52
        d.add(Rect(cx + 2, sol_y, col_w - 4, sol_h,
                   fillColor=faint, strokeColor=col, strokeWidth=1.2))
        d.add(String(cx + col_w/2, sol_y + sol_h - 8, "CLOSED BY BEV",
                     fontName='Helvetica-Bold', fontSize=7,
                     fillColor=ACCENT_GREEN, textAnchor='middle'))
        for j, ln in enumerate(cd['solution'].split('\n')):
            d.add(String(cx + col_w/2, sol_y + sol_h - 20 - j*10, ln,
                         fontName='Helvetica', fontSize=7,
                         fillColor=TEXT_WHITE, textAnchor='middle'))

        # Invariants
        for j, ln in enumerate(cd['inv'].split('\n')):
            d.add(String(cx + col_w/2, 28 - j*11, ln,
                         fontName='Courier', fontSize=6.5,
                         fillColor=col, textAnchor='middle'))

    return d


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 7 — ATF Compliance Hierarchy (Pyramid)
# ══════════════════════════════════════════════════════════════════════════════
def diagram_compliance_hierarchy():
    W, H = INNER_W, 210
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=CODE_BG, strokeColor=BORDER_GRAY, strokeWidth=0.5))

    d.add(String(W/2, H - 11, "ATF Compliance Hierarchy — 6 Tiers · 106 Invariants",
                 fontName='Helvetica-Bold', fontSize=9, fillColor=TEXT_WHITE, textAnchor='middle'))

    tiers = [
        ("ATF-BEV-Compliant",   "RFC-ATF-1 through RFC-ATF-6 · BAR · CCS · CTCHC", "106 inv", ACCENT_GOLD,  True),
        ("ATF-CGL-Compliant",   "RFC-ATF-5 · CGE · GUGT · TGB",                      "88 inv",  colors.HexColor('#9b59b6'), False),
        ("ATF-PGL-Compliant",   "RFC-ATF-4 · AGVP · DSPP · SSD",                     "70 inv",  colors.HexColor('#7a5bb5'), False),
        ("ATF-FEI-Compliant",   "RFC-ATF-3 · OEP · GPIL · FEA",                      "40 inv",  ACCENT_TEAL,   False),
        ("ATF-RGC-Compliant",   "RFC-ATF-2 · TAR · RCR · AFG",                       "14 inv",  ACCENT_BLUE,   False),
        ("ATF-COMPLIANT-L1/3",  "RFC-ATF-1 · Identity & Delegation · AIR · DR",      "6 inv",   colors.HexColor('#4a7cc7'), False),
    ]

    tier_h  = 24
    gap     = 4
    base_w  = W - 40
    start_y = 18

    for i, (name, desc, inv, col, top) in enumerate(tiers):
        idx = len(tiers) - 1 - i
        taper = idx * 14
        tw = base_w - taper
        tx = (W - tw) / 2
        y  = start_y + i * (tier_h + gap)

        fill = col if top else colors.HexColor('#%02x%02x%02x' % (
            max(0,min(255,int(col.red*255*0.22+10))),
            max(0,min(255,int(col.green*255*0.22+10))),
            max(0,min(255,int(col.blue*255*0.22+10))),
        ))
        sw = 2 if top else 0.8
        d.add(Rect(tx, y, tw, tier_h, fillColor=fill, strokeColor=col, strokeWidth=sw))

        tc = DARK_BG if top else col
        d.add(String(tx + 8, y + tier_h/2 + 4, name,
                     fontName='Helvetica-Bold', fontSize=8.5, fillColor=tc))
        d.add(String(tx + 8, y + tier_h/2 - 6, desc,
                     fontName='Helvetica', fontSize=7, fillColor=tc if top else TEXT_GRAY))
        d.add(String(tx + tw - 8, y + tier_h/2 - 3, inv,
                     fontName='Helvetica-Bold', fontSize=8.5, fillColor=ACCENT_GOLD if top else TEXT_GRAY,
                     textAnchor='end'))

    # Side annotation
    d.add(String(W - 6, H/2, "← Each tier adds layers",
                 fontName='Helvetica-Oblique', fontSize=7, fillColor=TEXT_GRAY,
                 textAnchor='end'))

    return d


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 8 — BEV Turn Execution Timeline (bonus diagram)
# ══════════════════════════════════════════════════════════════════════════════
def diagram_bev_timeline():
    W, H = INNER_W, 160
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=CODE_BG, strokeColor=BORDER_GRAY, strokeWidth=0.5))

    d.add(String(W/2, H - 11, "BEV Turn Execution Timeline — Ordered Steps per Turn",
                 fontName='Helvetica-Bold', fontSize=9, fillColor=TEXT_WHITE, textAnchor='middle'))

    steps = [
        (1,  "Agent executes\nturn → BO",         ACCENT_BLUE),
        (2,  "output_hash\ncomputed",              ACCENT_TEAL),
        (3,  "CCS computed\nfrom BO + CV",         colors.HexColor('#7a5bb5')),
        (4,  "chain_link\ncomputed",               ACCENT_TEAL),
        (5,  "BAR assembled\n(all fields)",        ACCENT_LIGHT),
        (6,  "content_hash\ncomputed",             ACCENT_ORANGE),
        (7,  "pqc_signature\ncomputed",            ACCENT_ORANGE),
        (8,  "BAR persisted\nto DB",               ACCENT_GREEN),
        (9,  "PVR trigger\n(if drift)",            ACCENT_RED),
    ]

    n  = len(steps)
    bw = (W - 16) / n - 3
    bh = 50
    sy = H/2 - bh/2 + 8

    for i, (num, label, col) in enumerate(steps):
        x = 8 + i * (bw + 3)
        fill = colors.HexColor('#%02x%02x%02x' % (
            max(0,min(255,int(col.red*255*0.2+8))),
            max(0,min(255,int(col.green*255*0.2+8))),
            max(0,min(255,int(col.blue*255*0.2+8))),
        ))
        sw = 1.5 if num in (8, 9) else 0.8
        d.add(Rect(x, sy, bw, bh, fillColor=fill, strokeColor=col, strokeWidth=sw))
        d.add(String(x + bw/2, sy + bh - 10, str(num),
                     fontName='Helvetica-Bold', fontSize=9, fillColor=col, textAnchor='middle'))
        for j, ln in enumerate(label.split('\n')):
            d.add(String(x + bw/2, sy + bh - 24 - j*10, ln,
                         fontName='Helvetica', fontSize=6.5,
                         fillColor=TEXT_WHITE, textAnchor='middle'))
        if i < n - 1:
            ax = x + bw + 1
            ay = sy + bh/2
            d.add(Line(ax, ay, ax + 2, ay, strokeColor=TEXT_GRAY, strokeWidth=0.8))
            d.add(Polygon([ax+2, ay, ax-1, ay+3, ax-1, ay-3],
                          fillColor=TEXT_GRAY, strokeColor=TEXT_GRAY, strokeWidth=0))

    # Phase labels
    phases = [
        (8,   66, "Execution Phase",    ACCENT_BLUE),
        (160, 106, "BEV Production Phase", ACCENT_TEAL),
        (360, 66,  "Persistence Phase", ACCENT_GREEN),
        (450, 66,  "AGVP Phase",        ACCENT_RED),
    ]
    # Simple footer
    d.add(String(W/2, 14,
                 "Steps 1–8: mandatory per turn (BEV-INV-001).  Step 9: conditional on verdict (BEV-INV-007 / BEV-INV-008).",
                 fontName='Helvetica', fontSize=7, fillColor=TEXT_GRAY, textAnchor='middle'))
    return d


# ══════════════════════════════════════════════════════════════════════════════
# CONTENT BUILDER
# ══════════════════════════════════════════════════════════════════════════════
def build(s):
    story = []
    def P(text, style='body'):  return Paragraph(text, s[style])
    def H1(t): return P(t, 'h1')
    def H2(t): return P(t, 'h2')
    def H3(t): return P(t, 'h3')

    # ── COVER ────────────────────────────────────────────────────────────────
    if os.path.exists(LOGO):
        story += [sp(18), Image(LOGO, width=52*mm, height=52*mm, hAlign='CENTER'), sp(10)]
    else:
        story += [sp(60)]

    story += [
        P("OMNIX QUANTUM OPEN STANDARD", 'badge'),
        sp(4),
        P("RFC-ATF-6", 'ctitle'),
        P("Agent Trust Fabric — Behavioral Execution Verification Protocol", 'csub'),
        P("Behavioral Anchor Record · Constraint Conformance Signal · Cross-Turn Coherence Hash Chain", 'csub'),
        sp(10),
        rule(s),
        sp(8),
        P("Harold Alberto Nunes Rodelo, Editor", 'cmeta'),
        P("OMNIX QUANTUM LTD · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ, England", 'cmeta'),
        P("standards@omnixquantum.com · omnixquantum.net", 'cmeta'),
        sp(6),
        P("Version 1.0.0 · May 2026 · DOI: pending submission", 'cmeta'),
        P("Extension to RFC-ATF-1, RFC-ATF-2, RFC-ATF-3, RFC-ATF-4, and RFC-ATF-5", 'cmeta'),
        sp(14),
        rule(s),
        sp(10),
        P("Compliance Designation: <b>ATF-BEV-Compliant</b> — Sixth and highest tier", 'gold'),
        sp(6),
        P("18 new invariants (BEV-INV-001–018) · 106 total ATF invariants across 20 protocol families", 'gold'),
        sp(20),
        PageBreak(),
    ]

    # ── ABSTRACT ─────────────────────────────────────────────────────────────
    story += [
        H1("Abstract"),
        P("RFC-ATF-6 specifies the <b>Behavioral Execution Verification Layer (BEV)</b> of the Agent Trust Fabric — the sixth and final RFC in the ATF Open Standard series. RFC-ATF-6 answers the structural question that no prior RFC addresses: <i>did the agent actually behave within its authorized constraints during execution, turn by turn?</i>"),
        sp(6),
        P("The five prior RFCs answered questions about governance infrastructure: who authorized (RFC-ATF-1), was authority continuously valid (RFC-ATF-2), where does evidence go (RFC-ATF-3), was monitoring active between requests (RFC-ATF-4), what else could have happened and is compliance universal (RFC-ATF-5). All five share a structural assumption: the authorized action is treated as a black box. The governance receipt authorizes. The execution receipt records. But no ATF artifact through RFC-ATF-5 contains a cryptographic record of what the agent actually produced — the Behavioral Execution Gap (Gap_BEV)."),
        sp(6),
        P("RFC-ATF-6 closes this gap with three new protocol components: the <b>Behavioral Anchor Record (BAR)</b>, the <b>Constraint Conformance Signal (CCS)</b>, and the <b>Cross-Turn Coherence Hash Chain (CTCHC)</b>. These components are additive, backward compatible, and constitute Layer 6 of the ATF stack."),
        sp(4),
        arule(),
    ]

    # ── DIAGRAM 1 — ATF Stack ────────────────────────────────────────────────
    story += [
        H1("Figure 1 — ATF 6-Layer Protocol Stack"),
        P("The Behavioral Execution Verification Layer (BEV) occupies Layer 6 — the topmost layer of the ATF stack. Each layer is additive: BEV does not replace or modify any prior layer. Together the six layers cover the complete lifecycle of a governed autonomous agent action."),
        sp(8),
        diagram_atf_stack(),
        P("Figure 1: ATF protocol stack showing all 6 RFC layers. Layer 6 (BEV, gold) adds behavioral attestation atop the five existing layers. Each layer's invariant count is cumulative.", 'caption'),
        sp(10),
    ]

    # ── PROBLEM STATEMENT ────────────────────────────────────────────────────
    story += [
        H1("1. Problem Statement — The Behavioral Execution Gap"),
        H2("1.1  Gap_BAG — Behavioral Attestation Gap"),
        P("Every prior ATF artifact treats the authorized action as a black box. The Governing Receipt (GR) authorizes the action. The Execution Receipt records that the action occurred. But no artifact cryptographically binds the GR to what the agent actually produced during execution — the Behavioral Output (BO). This is Gap_BAG:"),
        cb("Gap_BAG = { (GR, BO) : no verifiable binding exists between GR and BO }\n\nConsequences:\n  a) Regulatory gap:  EU AI Act Art. 9 requires monitoring that AI operates within defined boundaries\n  b) Forensic gap:    auditor cannot reconstruct what the agent actually said or did\n  c) Liability gap:   legal counsel cannot prove agent operated within authorized constraints", s),
        sp(6),
        H2("1.2  Gap_COP — Conformance Observability Problem"),
        P("The AGVP watchdog (RFC-ATF-4) issues anticipatory vetoes based on observable conformance signals. For structural governance (CES, fragmentation) and semantic drift (DSPP), signals exist. For behavioral output conformance, no signal existed before this RFC. Gap_COP left the AGVP input space incomplete for behavioral trajectories."),
        sp(6),
        H2("1.3  Gap_MCP — Multi-Turn Coherence Problem"),
        P("A set of valid BAR records does not prove Session Coherence without a chaining mechanism. An adversary could present a subset of BARs (omitting turns where violations occurred), reorder BARs, or substitute BARs from a different session. Gap_MCP is the absence of a cryptographic Session Integrity Proof."),
        sp(8),
    ]

    # ── DIAGRAM 6 — Gaps ────────────────────────────────────────────────────
    story += [
        H1("Figure 2 — Three Behavioral Gaps Closed by BEV"),
        diagram_behavioral_gaps(),
        P("Figure 2: The three structural problems RFC-ATF-6 closes. Each gap is mapped to the BEV component that resolves it: BAR closes Gap_BAG, CCS closes Gap_COP, CTCHC closes Gap_MCP.", 'caption'),
        sp(10),
        PageBreak(),
    ]

    # ── BAR ──────────────────────────────────────────────────────────────────
    story += [
        H1("2. Behavioral Anchor Record (BAR)"),
        P("The BAR is a PQC-signed record produced at each execution turn, binding the SHA3-256 hash of the agent's output to the governing receipt and turn index. It is the first ATF artifact that closes the authorization-to-output chain."),
        sp(6),
        H2("2.1  Content Hash Construction"),
        cb("output_hash  = SHA3-256(output_text.encode('utf-8'))\ncontent_hash = SHA3-256(output_hash || governing_receipt_id || str(turn_index))\npqc_signature = dilithium3.sign(content_hash.encode('utf-8'), platform_secret_key)\npqc_algorithm = 'ML-DSA-65'  # FIPS 204", s),
        sp(6),
        H2("2.2  BAR Architecture Flow"),
        diagram_bar_flow(),
        P("Figure 3: BAR creation pipeline. Every turn's output is hashed, bound to the governing receipt and turn index, then PQC-signed before the BAR is persisted. The three-input binding makes output, receipt, and position simultaneously tamper-evident.", 'caption'),
        sp(10),
        H2("2.3  Output Hash Privacy Modes"),
        tbl(
            ["Mode", "output_payload stored?", "CCS computable?", "Use case"],
            [
                ["FULL",     "Yes — full output",    "Yes", "Forensic / internal audit"],
                ["HASHED",   "No — hash only",       "Partial", "Production default (GDPR)"],
                ["REDACTED", "No — omitted",         "No",  "Privacy-sensitive regulated"],
            ],
            s, cw=[30*mm, 50*mm, 38*mm, 50*mm]
        ),
        sp(8),
        H2("2.4  BAR Invariants"),
    ]

    bar_invs = [
        ("BEV-INV-001", "Mandatory BAR Production",
         "Every execution turn MUST produce a BAR before agent output is delivered. No path delivers output without a BAR.",
         "EXISTS(BAR b) WHERE b.turn_index = i AND b.created_before_output_delivery"),
        ("BEV-INV-002", "Content Hash Binding",
         "content_hash = SHA3-256(output_hash || governing_receipt_id || str(turn_index)). All three inputs are simultaneously tamper-evident.",
         "b.content_hash = SHA3-256(b.output_hash || b.governing_receipt_id || str(b.turn_index))"),
        ("BEV-INV-003", "HALTED BAR Immediately Halts Session",
         "A BAR with bar_status=HALTED MUST immediately transition the session to SESSION_HALTED. No subsequent turn permitted.",
         "BAR(T_i).bar_status = HALTED IMPLIES session_status(S) = STATUS_HALTED"),
        ("BEV-INV-004", "BAR PQC-Sealing and Offline Verifiability",
         "Every BAR MUST be sealed with ML-DSA-65 over its content_hash. No UPDATE or DELETE on atf_behavioral_anchor_records.",
         "dilithium3.verify(b.content_hash.encode(), b.pqc_signature, platform_public_key) = True"),
        ("BEV-INV-015", "Empty Output Text Is a Violation",
         "output_text = '' or whitespace-only MUST set bar_status = VIOLATION. Silent outputs are not permissible.",
         "output_text(b).strip() = '' IMPLIES b.bar_status = VIOLATION"),
        ("BEV-INV-016", "BAR Identifier Format",
         "Every BAR id MUST conform to 'BAR-{HEX16}' — exactly 16 uppercase hexadecimal characters.",
         "MATCHES(b.bar_id, r'^BAR-[0-9A-F]{16}$')"),
    ]
    for inv_id, title, stmt, formal in bar_invs:
        story.append(inv_box(inv_id, title, stmt, formal, s))

    story += [sp(6), PageBreak()]

    # ── CCS ──────────────────────────────────────────────────────────────────
    story += [
        H1("3. Constraint Conformance Signal (CCS)"),
        P("The CCS provides a governance-native behavioral conformance measurement for each execution turn. 'Governance-native' means it references the actual Constraint Vector (CV) from the Governing Receipt — the receipt IS the measurement specification, PQC-signed and immutable."),
        sp(6),
        H2("3.1  Score Components"),
        diagram_ccs_score(),
        P("Figure 4: CCS score breakdown (left) and verdict ladder (right). Four components sum to a maximum of 100 points, normalized to [0.0, 1.0]. Each verdict threshold triggers a specific AGVP or session governance action.", 'caption'),
        sp(8),
        H2("3.2  Score Formula"),
        cb("OBS = max(0, 40 - 10 * boundary_violation_count)  # output domain / prohibited classes\nCSS = max(0, 30 -  8 * constraint_failure_count)  # explicit constraint failures\nSDS = max(0, 20 * (1 - drift_magnitude))           # cosine distance from authorized profile\nAAS = 10 if authority_scope_satisfied else 0        # capability/resource scope check\n\nccs_score        = OBS + CSS + SDS + AAS            # range: [0, 100]\nconformance_score = ccs_score / 100.0              # range: [0.0, 1.0]  (BEV-INV-006)\ndrift_delta      = 1.0 - conformance_score          # per-turn drift contribution\ncumulative_drift += drift_delta                     # session accumulator (BEV-INV-017)", s),
        sp(8),
        H2("3.3  AGVP Integration"),
        P("The CCS-AGVP integration completes the AGVP input space. Structural signals (CES, fragmentation) were covered by RFC-ATF-4. Semantic drift (DSPP) was covered by RFC-ATF-4. Behavioral output conformance is now covered by CCS:"),
        diagram_agvp_loop(),
        P("Figure 5: CCS-AGVP integration loop. Verdicts DRIFTING, BREACH, and VIOLATION each trigger escalating AGVP responses. VIOLATION triggers HALT propagation — the session is terminated before further outputs accumulate.", 'caption'),
        sp(8),
        H2("3.4  CCS Invariants"),
    ]

    ccs_invs = [
        ("BEV-INV-005", "Mandatory CCS per BAR (atomic)",
         "Every BAR MUST be accompanied by a CCS computation in the same atomic operation. No valid BAR without CCS.",
         "EXISTS(CCS c) WHERE c.bar_id = b.bar_id AND c.created_atomically_with(b)"),
        ("BEV-INV-006", "CCS Conformance Score Bounds",
         "conformance_score MUST be in [0.0, 1.0]. drift_delta = 1.0 - conformance_score. All components non-negative.",
         "0.0 <= c.conformance_score <= 1.0 AND c.drift_delta = 1.0 - c.conformance_score"),
        ("BEV-INV-007", "CRITICAL/DRIFTING Verdict Triggers AGVP",
         "verdict DRIFTING or worse MUST set watchdog_triggered=true and MUST trigger PVR issuance to AGVP watchdog.",
         "c.verdict IN {DRIFTING,BREACH,VIOLATION} IMPLIES c.watchdog_triggered=True AND EXISTS(PVR p)"),
        ("BEV-INV-008", "Cumulative Drift Triggers HALT",
         "When cumulative_drift > DRIFT_THRESHOLD (default 0.35), verdict MUST be HALT. THRESHOLD max 0.50 in production.",
         "cumulative_drift > DRIFT_THRESHOLD IMPLIES verdict=HALT AND no subsequent turn permitted"),
        ("BEV-INV-009", "CCS History Append-Only",
         "CCS records are append-only, chain-linked to CTCHC. No UPDATE or DELETE on atf_constraint_conformance_signals.",
         "CCS records ordered by turn_index are strictly monotone AND chain_link_hash matches CTCHC"),
        ("BEV-INV-017", "Drift Accumulator Isolated per Session",
         "cumulative_drift is independent per session_id. On process restart, MUST reload from last persisted CCS record.",
         "cumulative_drift(S_1) is independent of cumulative_drift(S_2) for all S_1 != S_2"),
    ]
    for inv_id, title, stmt, formal in ccs_invs:
        story.append(inv_box(inv_id, title, stmt, formal, s))

    story += [sp(6), PageBreak()]

    # ── CTCHC ────────────────────────────────────────────────────────────────
    story += [
        H1("4. Cross-Turn Coherence Hash Chain (CTCHC)"),
        P("The CTCHC provides session-level behavioral integrity for multi-turn agent sessions. It chains every BAR's output hash with the prior link and governing receipt ID, seeding from a genesis hash bound to the session identity. The resulting sealed CTCHC record is the Session Integrity Proof (SIP) — offline verifiable without any OMNIX infrastructure."),
        sp(6),
        H2("4.1  Chain Construction"),
        diagram_ctchc_chain(),
        P("Figure 6: CTCHC hash chain. The genesis hash binds the chain to session_id and governing_receipt_id. Each link encodes the previous link, current turn's output hash, and receipt. The ML-DSA-65 chain seal over the final hash is the Session Integrity Proof.", 'caption'),
        sp(8),
        H2("4.2  Chain Link Formula"),
        cb("# Genesis (turn_index = 0):\ngenesis_hash = SHA3-256(\n    session_id + '||' + governing_receipt_id + '||' + 'OMNIX-CTCHC-GENESIS'\n)\n\n# Per-turn link (n >= 0):\nlink[n] = SHA3-256(\n    json.dumps({\n        'prev':    genesis_hash if n == 0 else link[n-1],\n        'turn':    SHA3-256(output_text.encode('utf-8')),  # output_hash\n        'receipt': governing_receipt_id,\n    }, sort_keys=True).encode()\n)\n\n# Chain seal at session close:\nseal_hash  = SHA3-256(genesis_hash || all_link_hashes || final_chain_hash)\nctchc_seal = base64.b64encode(dilithium3.sign(seal_hash.encode(), platform_secret_key))", s),
        sp(8),
        H2("4.3  Offline Verification (6 steps)"),
        tbl(
            ["Step", "Check", "Failure meaning"],
            [
                ["1", "ctchc_seal over seal_hash verifies with ML-DSA-65 public key", "CTCHC record tampered"],
                ["2", "len(all_bar_ids) = turn_count, turn_index[0..N-1] complete", "Missing turns"],
                ["3", "Each BAR passes individual content_hash + pqc_signature check", "BAR tampered"],
                ["4", "Recompute genesis_hash from BAR_0 fields, compare to CTCHC.genesis_hash", "Session identity tampered"],
                ["5", "Reconstruct all link[n], compare to BAR_n.chain_link", "Turn substituted or reordered"],
                ["6", "chain_link(N-1) = CTCHC.final_chain_hash", "Chain sealed over different sequence"],
            ],
            s, cw=[12*mm, 95*mm, 62*mm]
        ),
        sp(8),
        H2("4.4  CTCHC Invariants"),
    ]

    ctchc_invs = [
        ("BEV-INV-010", "Chain Initialized Before First BAR",
         "CTCHC genesis MUST be created before BAR_0. genesis_hash = SHA3-256(session_id||'||'||receipt_id||'||'||'OMNIX-CTCHC-GENESIS').",
         "EXISTS(CTCHC C) WHERE C.session_id = S.session_id AND C.initialized_before_BAR_0"),
        ("BEV-INV-011", "Chain Link Hash Construction",
         "link[n] = SHA3-256(json.dumps({'prev': prev_hash, 'turn': output_hash, 'receipt': receipt_id}, sort_keys=True)). Deterministic.",
         "L_n.chain_link_hash = SHA3-256(canonical({prev: L_{n-1}.hash, turn: output_hash_n, receipt}))"),
        ("BEV-INV-012", "Gaps in Turn Sequence Fail Verification",
         "Verification MUST fail if any turn_index in [0, N-1] is absent. A sealed CTCHC claiming N turns but N-1 links is rejected.",
         "{L.turn_index : L in C.links} = {0, 1, ..., N-1} OR verify(C) = FAIL"),
        ("BEV-INV-013", "Seal Covers Complete Chain",
         "seal_hash = SHA3-256(genesis_hash || all_link_hashes || current_tip_hash). Partial seals invalid.",
         "C.seal_hash = SHA3-256(C.genesis_hash || all_link_hashes || C.current_tip_hash) for all N links"),
        ("BEV-INV-014", "Seal ML-DSA-65 Signed Before OEP Export",
         "CTCHC seal MUST be ML-DSA-65 signed before OEP export or regulatory submission. Unsigned seal not accepted.",
         "dilithium3.verify(C.seal_hash.encode(), C.pqc_seal_signature, platform_public_key) = True"),
        ("BEV-INV-018", "Every Link's Receipt ID Matches Chain Receipt",
         "Every chain link MUST carry the same governing_receipt_id as the CTCHC genesis. Prevents cross-session splicing.",
         "For all L in C: L.governing_receipt_id = C.governing_receipt_id"),
    ]
    for inv_id, title, stmt, formal in ctchc_invs:
        story.append(inv_box(inv_id, title, stmt, formal, s))

    story += [sp(6), PageBreak()]

    # ── BEV COMPOSITION + TIMELINE ───────────────────────────────────────────
    story += [
        H1("5. BEV Layer Composition"),
        P("BAR, CCS, and CTCHC interact at each execution turn in a strictly ordered pipeline. The ordering guarantees that the CCS is embedded in the BAR before the content_hash is computed, and the chain_link from the prior turn is incorporated before the BAR is sealed."),
        sp(6),
        H2("5.1  Per-Turn Execution Timeline"),
        diagram_bev_timeline(),
        P("Figure 7: BEV per-turn execution timeline. Steps 1–8 are mandatory for every turn (BEV-INV-001). Step 9 (AGVP trigger) is conditional on the CCS verdict. Session close adds steps 12–17 for CTCHC sealing.", 'caption'),
        sp(8),
        H2("5.2  Cross-Layer Integration Points"),
        tbl(
            ["BEV layer", "Integrates with", "Integration point"],
            [
                ["BAR",   "Governing Receipt (L1-L2)", "governing_receipt_id in every BAR; queryable from any ATF receipt"],
                ["CCS",   "AGVP (L4 RFC-ATF-4)",       "DRIFTING/BREACH/VIOLATION trigger PVR issuance via AGVP watchdog"],
                ["CTCHC", "OEP (L3 RFC-ATF-3)",        "CTCHC + BAR records included in OEP forensic packages"],
                ["BAR",   "TCS (L5 RFC-ATF-5)",        "bar_timestamp_ns anchors to Temporal Context Snapshot for 7yr retention"],
            ],
            s, cw=[28*mm, 46*mm, 96*mm]
        ),
        sp(8),
    ]

    # ── COMPLIANCE HIERARCHY ─────────────────────────────────────────────────
    story += [
        H1("6. Compliance Designation — ATF-BEV-Compliant"),
        P("An implementation is designated <b>ATF-BEV-Compliant</b> — the sixth and highest compliance tier — when it satisfies all requirements of RFC-ATF-1 through RFC-ATF-6: ATF-CGL-Compliant (baseline) plus BAR operational, CCS operational, CTCHC operational, and BEV formal verification passing."),
        sp(8),
        diagram_compliance_hierarchy(),
        P("Figure 8: ATF compliance hierarchy. ATF-BEV-Compliant (gold, top) requires compliance with all 6 RFCs and 106 invariants. Each tier is additive — BEV does not supersede prior tiers; it extends them.", 'caption'),
        sp(10),
        H2("6.1  Compliance Requirements Summary"),
        tbl(
            ["Requirement", "Condition", "BEV-INVs covered"],
            [
                ["ATF-CGL-Compliant baseline", "All RFC-ATF-1–5 requirements satisfied", "ATF-INV-001–006 + 82 prior"],
                ["BAR operational",            "BEV_ENABLED=true, all turns produce persisted BARs", "BEV-INV-001–004, 015–016"],
                ["CCS operational",            "CCS_ENABLED=true, AGVP integration active for DRIFTING+", "BEV-INV-005–009, 017"],
                ["CTCHC operational",          "CTCHC_ENABLED=true, all completed sessions sealed", "BEV-INV-010–014, 018"],
                ["BEV formal verification",    "run_bev_proofs.py: all 5 targets unsat/structural", "BEV-FVS-001–005"],
            ],
            s, cw=[55*mm, 75*mm, 40*mm]
        ),
        sp(8), PageBreak(),
    ]

    # ── INVARIANT SUMMARY TABLE ───────────────────────────────────────────────
    story += [
        H1("7. Combined Invariant Summary — RFC-ATF-6"),
        P("RFC-ATF-6 introduces 18 new invariants across the three BEV protocol families. Combined with 88 invariants from RFC-ATF-1 through RFC-ATF-5, the ATF stack reaches 106 formally specified invariants."),
        sp(8),
        tbl(
            ["Invariant", "Family", "Statement (summary)"],
            [
                ["BEV-INV-001", "BAR",   "Mandatory BAR before output delivered"],
                ["BEV-INV-002", "BAR",   "content_hash = SHA3-256(output‖receipt‖index)"],
                ["BEV-INV-003", "BAR",   "HALTED BAR → immediate session halt"],
                ["BEV-INV-004", "BAR",   "ML-DSA-65 sealing + offline verifiability + append-only"],
                ["BEV-INV-005", "CCS",   "Mandatory CCS per BAR — atomic production"],
                ["BEV-INV-006", "CCS",   "conformance_score ∈ [0.0, 1.0]; drift derived"],
                ["BEV-INV-007", "CCS",   "DRIFTING or worse → AGVP watchdog triggered"],
                ["BEV-INV-008", "CCS",   "Cumulative drift > threshold → HALT"],
                ["BEV-INV-009", "CCS",   "CCS history append-only, hash-linked to CTCHC"],
                ["BEV-INV-010", "CTCHC", "Chain initialized before first BAR"],
                ["BEV-INV-011", "CTCHC", "link = SHA3-256({prev, turn, receipt})"],
                ["BEV-INV-012", "CTCHC", "Gaps in turn sequence → verification fails"],
                ["BEV-INV-013", "CTCHC", "Seal covers complete chain (genesis to tip)"],
                ["BEV-INV-014", "CTCHC", "Seal ML-DSA-65 signed before OEP export"],
                ["BEV-INV-015", "BAR",   "Empty output_text → VIOLATION"],
                ["BEV-INV-016", "BAR",   "BAR id format: BAR-{HEX16}"],
                ["BEV-INV-017", "CCS",   "Drift accumulator isolated per session_id"],
                ["BEV-INV-018", "CTCHC", "Every link's receipt_id MUST match chain receipt"],
            ],
            s, cw=[30*mm, 22*mm, 118*mm]
        ),
        sp(12),
        H2("7.1  Complete ATF Invariant Registry"),
        tbl(
            ["Family", "RFC", "Count", "Scope"],
            [
                ["ATF-INV",  "ATF-1", "6",  "Identity & Delegation"],
                ["RGC-INV",  "ATF-2", "8",  "Runtime Continuity"],
                ["GPIL-INV", "ATF-3", "3",  "Governance Policy Interop"],
                ["ELR-INV",  "ATF-3", "4",  "Evidence Lifecycle"],
                ["EAP-INV",  "ATF-3", "7",  "Evidence Archive Pipeline"],
                ["OEP-INV",  "ATF-3", "6",  "OMNIX Evidence Package"],
                ["FEA-INV",  "ATF-3", "5",  "Forensic Export Auth"],
                ["FVP-INV",  "ATF-3", "1",  "Forensic Verification Protocol"],
                ["GECR-INV", "ATF-3", "6",  "Governance Execution Context Record"],
                ["SGIP-INV", "ATF-3", "4",  "Semantic Governance Interop Protocol"],
                ["DSPP-INV", "ATF-4", "7",  "Dynamic Semantic Portability"],
                ["AGV-INV",  "ATF-4", "6",  "Anticipatory Governance Veto"],
                ["SSD-INV",  "ATF-4", "3",  "Structural Shift Detection"],
                ["FVS-INV",  "ATF-4", "3",  "Formal Verification Suite"],
                ["CGE-INV",  "ATF-5", "7",  "Counterfactual Governance Engine"],
                ["GUGT-INV", "ATF-5", "6",  "Grand Unified Governance Theory"],
                ["TGB-INV",  "ATF-5", "5",  "Temporal Governance Bridge"],
                ["BEV-INV",  "ATF-6", "18", "Behavioral Execution Verification (BAR+CCS+CTCHC)"],
                ["TOTAL",    "1–6",   "106", "20 protocol families"],
            ],
            s, cw=[28*mm, 22*mm, 18*mm, 102*mm]
        ),
        sp(10), PageBreak(),
    ]

    # ── PERSISTENCE SCHEMA ────────────────────────────────────────────────────
    story += [
        H1("8. Persistence Schema"),
        H2("8.1  atf_behavioral_anchor_records"),
        cb("""CREATE TABLE IF NOT EXISTS atf_behavioral_anchor_records (
    bar_id                 VARCHAR(64)   PRIMARY KEY,            -- BAR-{HEX16}
    session_id             VARCHAR(64)   NOT NULL,
    governing_receipt_id   VARCHAR(128)  NOT NULL,
    agent_id               VARCHAR(128)  NOT NULL,
    turn_index             INTEGER       NOT NULL,
    output_hash            VARCHAR(80)   NOT NULL,               -- sha256:64hex
    output_hash_mode       VARCHAR(16)   NOT NULL,               -- FULL|HASHED|REDACTED
    output_payload         JSONB,                                -- mode=FULL only
    constraint_vector      JSONB         NOT NULL,
    ccs_score              NUMERIC(7,4),
    ccs_verdict            VARCHAR(16),                          -- CONFORMANT|DRIFTING|...
    ccs_components         JSONB,
    chain_link             VARCHAR(64)   NOT NULL,               -- 64 hex chars
    genesis_hash           VARCHAR(64),                          -- turn_index=0 only
    session_start_ns       BIGINT,                               -- turn_index=0 only
    bar_timestamp_ns       BIGINT        NOT NULL,
    issued_at              TIMESTAMPTZ   NOT NULL,
    content_hash       VARCHAR(64)   NOT NULL,
    pqc_signature          TEXT          NOT NULL,               -- base64 ML-DSA-65
    pqc_algorithm          VARCHAR(16)   NOT NULL DEFAULT 'ML-DSA-65',
    atf_spec_version       VARCHAR(8)    NOT NULL DEFAULT '1.6',
    bar_status             VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE',
    created_at             TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);""", s),
        sp(8),
        H2("8.2  atf_constraint_conformance_signals"),
        cb("""CREATE TABLE IF NOT EXISTS atf_constraint_conformance_signals (
    ccs_id                       VARCHAR(64)  PRIMARY KEY,       -- CCS-{HEX16}
    bar_id                       VARCHAR(64)  REFERENCES atf_behavioral_anchor_records,
    session_id                   VARCHAR(64)  NOT NULL,
    governing_receipt_id         VARCHAR(128) NOT NULL,
    turn_index                   INTEGER      NOT NULL,
    conformance_score            NUMERIC(7,4) NOT NULL,          -- [0.0, 1.0]
    verdict                      VARCHAR(16)  NOT NULL,          -- CONFORMANT|DRIFTING|...
    output_boundary_score        NUMERIC(6,3),
    constraint_satisfaction_score NUMERIC(6,3),
    semantic_drift_score         NUMERIC(6,3),
    authority_alignment_score    NUMERIC(6,3),
    boundary_violation_count     INTEGER,
    constraint_failure_count     INTEGER,
    drift_magnitude              NUMERIC(7,4),
    cumulative_drift             NUMERIC(7,4) NOT NULL,
    drift_delta                  NUMERIC(7,4) NOT NULL,
    watchdog_triggered           BOOLEAN      NOT NULL DEFAULT FALSE,
    agvp_pvr_id                  VARCHAR(64),
    halt_triggered               BOOLEAN      NOT NULL DEFAULT FALSE,
    chain_link_hash              VARCHAR(64),
    computed_at_ns               BIGINT       NOT NULL,
    created_at                   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);""", s),
        sp(8),
        H2("8.3  atf_coherence_hash_chains"),
        cb("""CREATE TABLE IF NOT EXISTS atf_coherence_hash_chains (
    ctchc_id               VARCHAR(64)   PRIMARY KEY,            -- CTCHC-{HEX16}
    session_id             VARCHAR(64)   UNIQUE NOT NULL,
    governing_receipt_id   VARCHAR(128)  NOT NULL,
    genesis_hash           VARCHAR(64)   NOT NULL,
    final_chain_hash       VARCHAR(64),
    turn_count             INTEGER       NOT NULL DEFAULT 0,
    all_bar_ids            JSONB,                                 -- ordered by turn_index
    session_start_ns       BIGINT,
    session_close_ns       BIGINT,
    session_status         VARCHAR(32)   NOT NULL DEFAULT 'ACTIVE',
    failure_turn_index     INTEGER,
    failure_reason         TEXT,
    seal_hash          VARCHAR(64),
    ctchc_seal             TEXT,                                  -- base64 ML-DSA-65
    pqc_algorithm          VARCHAR(16)   NOT NULL DEFAULT 'ML-DSA-65',
    chain_sealed           BOOLEAN       NOT NULL DEFAULT FALSE,
    atf_spec_version       VARCHAR(8)    NOT NULL DEFAULT '1.6',
    created_at             TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);""", s),
        sp(10), PageBreak(),
    ]

    # ── FORMAL VERIFICATION ───────────────────────────────────────────────────
    story += [
        H1("9. Formal Verification — OMNIX-FVS-1.0 BEV Extension"),
        P("RFC-ATF-6 extends the OMNIX Formal Verification Suite (FVS-1.0, ADR-177) with five BEV proof targets. All proofs are Z3 SMT-checkable or demonstrable via structural collision resistance arguments."),
        sp(6),
        tbl(
            ["Proof ID", "Target", "Method", "Expected result"],
            [
                ["BEV-FVS-001", "BAR binding completeness",     "Z3 boolean implication",     "unsat"],
                ["BEV-FVS-002", "Output hash structural uniqueness", "SHA-256 collision resistance", "structural"],
                ["BEV-FVS-003", "CCS score bounds [0.0, 1.0]",  "Z3 bounded real arithmetic", "unsat"],
                ["BEV-FVS-004", "CCS component non-negativity", "Z3 max(0,·) semantics",      "unsat"],
                ["BEV-FVS-005", "CTCHC chain monotonicity",     "SHA-256 structural induction","structural"],
            ],
            s, cw=[28*mm, 65*mm, 50*mm, 27*mm]
        ),
        sp(8),
        H2("9.1  BEV-FVS-003 — CCS Score Bounds (Z3)"),
        cb("""from z3 import Real, Or, Solver, And, unsat
obs, css, sds, aas = [Real(x) for x in ['obs', 'css', 'sds', 'aas']]
s = Solver()
s.add(obs >= 0, obs <= 40)
s.add(css >= 0, css <= 30)
s.add(sds >= 0, sds <= 20)
s.add(And(Or(aas == 0, aas == 10)))
ccs_score = obs + css + sds + aas
# Claim: conformance_score = ccs_score/100 is always in [0.0, 1.0]
s.add(Or(ccs_score < 0, ccs_score > 100))
assert s.check() == unsat  # No violation possible — BEV-INV-006 holds""", s),
        sp(8),
        P("Run all proofs: <b>python omnix_core/formal_verification/run_bev_proofs.py</b>", 'gold'),
        sp(10), PageBreak(),
    ]

    # ── REGULATORY ALIGNMENT ─────────────────────────────────────────────────
    story += [
        H1("10. Regulatory Alignment"),
        tbl(
            ["Regulation / Standard", "Article / Section", "BAR addresses", "CCS addresses", "CTCHC addresses"],
            [
                ["EU AI Act",      "Art. 9 — Risk management",    "Output attestation per turn", "Continuous conformance monitoring", "Session integrity proof"],
                ["EU AI Act",      "Art. 12 — Record-keeping",    "Per-turn behavioral record",  "Conformance history projection",    "Complete session audit trail"],
                ["EU AI Act",      "Art. 14 — Human oversight",   "Auditable output record",     "Drift signal for human review",     "Turn-by-turn oversight record"],
                ["NIST AI RMF",    "MEASURE 2.6 — Monitoring",    "Attestation of actual outputs","Governance-native monitoring signal","Session coherence evidence"],
                ["ISO/IEC 42001",  "§8.4 — Operational controls", "PQC-signed behavioral record","Operational conformance per §8.4",  "Turn-by-turn control record"],
                ["ISO/IEC 42001",  "§9.1 — Monitoring/evaluation","Verifiable output record",    "CCS is measurement artifact",       "Session history analysis"],
                ["MiFID II",       "Art. 17 — Algo trading",      "Pre/post-output record",      "Conformance of trading outputs",    "Multi-turn session integrity"],
                ["SOC 2 Type II",  "CC7.2 — Monitoring",          "Output monitoring evidence",  "Quantitative conformance evidence", "Session integrity in audit"],
            ],
            s, cw=[34*mm, 32*mm, 38*mm, 38*mm, 28*mm]
        ),
        sp(10),
    ]

    # ── NOVEL CONTRIBUTIONS ───────────────────────────────────────────────────
    story += [
        H1("11. Novel Contributions"),
        tbl(
            ["Contribution", "Description", "Prior art distinction"],
            [
                ["BAR — Behavioral Anchor Record",
                 "First cryptographic artifact binding agent outputs to governing receipts via PQC-signed content_hash = SHA3-256(output‖receipt‖index)",
                 "ML monitoring + output logging exist; PQC binding to governance receipt is new"],
                ["CCS — Constraint Conformance Signal",
                 "First governance-native behavioral monitoring signal referencing actual CV from PQC-signed governing receipt",
                 "Arize/WhyLabs monitor against separately configured policies; CCS uses the receipt itself"],
                ["CTCHC — Cross-Turn Coherence Hash Chain",
                 "Session-level hash chain seeded by governing receipt; SIP offline-verifiable without OMNIX infrastructure",
                 "Audit log hash chains exist; linkage to governance receipts for session-level forensic verification is new"],
                ["CCS-AGVP Integration Loop",
                 "Behavioral conformance signal feeding directly into AGVP anticipatory veto protocol for PVR issuance",
                 "Completes AGVP input space; first behavioral-to-proactive-veto integration"],
                ["Behavioral Attestation Chain",
                 "End-to-end verifiable chain: GR authorizes → BAR attests output → CCS measures conformance → CTCHC seals session",
                 "No prior standard closes authorization-to-behavioral-output chain"],
                ["ATF-BEV-Compliant",
                 "Sixth compliance tier requiring 106 invariants across all ATF layers",
                 "Supersedes ATF-CGL-Compliant (RFC-ATF-5); highest and final ATF designation"],
            ],
            s, cw=[45*mm, 70*mm, 55*mm]
        ),
        sp(10), PageBreak(),
    ]

    # ── REFERENCES ────────────────────────────────────────────────────────────
    story += [
        H1("12. References"),
    ]
    refs = [
        ("[RFC-ATF-1]",  "Nunes, H. RFC-ATF-1: Agent Trust Fabric Delegation Protocol. OMNIX QUANTUM, May 2026. DOI: 10.5281/zenodo.20155016"),
        ("[RFC-ATF-2]",  "Nunes, H. RFC-ATF-2: Agent Trust Fabric — Runtime Governance Continuity. OMNIX QUANTUM, May 2026. DOI: 10.5281/zenodo.20241344"),
        ("[RFC-ATF-3]",  "Nunes, H. RFC-ATF-3: Agent Trust Fabric — Governance Policy Interoperability, Evidence Lifecycle, and Forensic Verification Protocol. OMNIX QUANTUM, May 2026. DOI: 10.5281/zenodo.20247342"),
        ("[RFC-ATF-4]",  "Nunes, H. RFC-ATF-4: Agent Trust Fabric — Proactive Governance Layer. OMNIX QUANTUM, May 2026. DOI: 10.5281/zenodo.20368895"),
        ("[RFC-ATF-5]",  "Nunes, H. RFC-ATF-5: Agent Trust Fabric — Cognitive Governance Layer. OMNIX QUANTUM, May 2026. DOI: 10.5281/zenodo.20391721"),
        ("[FIPS204]",    "NIST. Module-Lattice-Based Digital Signature Standard (ML-DSA). FIPS 204. August 2024."),
        ("[FIPS180-4]",  "NIST. Secure Hash Standard (SHS). FIPS 180-4. August 2015."),
        ("[Z3]",         "de Moura, L. & Bjørner, N. Z3: An Efficient SMT Solver. TACAS 2008. LNCS 4963, pp. 337-340."),
        ("[EU-AI-ACT]",  "European Parliament. Regulation (EU) 2024/1689 on Artificial Intelligence. Official Journal of the European Union. July 2024."),
        ("[NIST-RMF]",   "NIST. Artificial Intelligence Risk Management Framework. NIST AI 100-1. January 2023."),
        ("[ISO-42001]",  "ISO/IEC 42001:2023. Artificial Intelligence — Management System."),
        ("[ADR-181]",    "Nunes, H. ADR-181: Behavioral Anchor Record (BAR). OMNIX QUANTUM. omnixquantum.net/docs/adr/ADR-181"),
        ("[ADR-182]",    "Nunes, H. ADR-182: Constraint Conformance Signal (CCS). OMNIX QUANTUM. omnixquantum.net/docs/adr/ADR-182"),
        ("[ADR-183]",    "Nunes, H. ADR-183: Cross-Turn Coherence Hash Chain (CTCHC). OMNIX QUANTUM. omnixquantum.net/docs/adr/ADR-183"),
        ("[ADR-131]",    "Nunes, H. ADR-131: Execution Integrity Layer. OMNIX QUANTUM. omnixquantum.net/docs/adr/ADR-131"),
    ]
    for tag, text in refs:
        story.append(P(f'<b>{tag}</b>  {text}', 'ref'))
        story.append(sp(2))

    story += [sp(10)]

    # ── AUTHOR ────────────────────────────────────────────────────────────────
    story += [
        rule(s),
        sp(8),
        P("Author's Address", 'h2'),
        P("Harold Alberto Nunes Rodelo, Editor", 'body'),
        P("OMNIX QUANTUM LTD", 'body'),
        P("71-75 Shelton Street, Covent Garden, London WC2H 9JQ, England", 'body'),
        P("standards@omnixquantum.com  ·  omnixquantum.net", 'body'),
        sp(14),
        rule(s),
        sp(6),
        P("RFC-ATF-6 Version 1.0.0 — May 2026 — OMNIX QUANTUM LTD — Harold Nunes, Editor", 'caption'),
        P("Priority Records: OMNIX-PAR-2026-BAR-001 · OMNIX-PAR-2026-CCS-001 · OMNIX-PAR-2026-CTCHC-001", 'caption'),
        P("Copyright (c) 2026 OMNIX QUANTUM LTD. All rights reserved.", 'caption'),
        P("Published under CC-BY-4.0. Permission granted to reproduce for review and implementation provided this notice is retained.", 'caption'),
    ]

    return story


# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc = SimpleDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=2.6*cm, bottomMargin=1.8*cm,
        title="RFC-ATF-6: Behavioral Execution Verification Protocol",
        author="Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD",
        subject="ATF-BEV-Compliant — Sixth compliance tier — 106 invariants",
        creator="OMNIX QUANTUM generate_atf6_pdf.py",
    )
    s = S()
    story = build(s)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    size_kb = os.path.getsize(OUT) // 1024
    print(f"Generated: {OUT}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
