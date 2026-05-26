"""RFC-ATF-6 PDF Generator — OMNIX QUANTUM — Behavioral Execution Verification Protocol
   Replicates RFC-ATF-5 density: 16 sections + 3 appendices, full ASCII art, specs, tables.
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
    Drawing, Rect, String, Line, Polygon, Group, Circle
)
from reportlab.graphics import renderPDF

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
AVAIL_W = PAGE_W - 2 * MARGIN
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(ROOT, 'omnix_web', 'public', 'logo_nobg.png')
OUT  = os.path.join(ROOT, 'docs', 'zenodo', 'rfc_atf_6', 'RFC-ATF-6.pdf')


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
    c.drawString(MARGIN, 4*mm, 'RFC-ATF-6 -- Behavioral Execution Verification Protocol -- OMNIX QUANTUM LTD -- omnixquantum.net')
    c.drawRightString(PAGE_W - MARGIN, 4*mm, f'Page {doc.page}')
    c.setStrokeColor(RULE_COLOR); c.setLineWidth(0.5)
    c.line(MARGIN, 12*mm, PAGE_W - MARGIN, 12*mm)
    c.restoreState()

def on_page(c, doc):
    cover_page(c, doc) if doc.page == 1 else normal_page(c, doc)


def S():
    s = {}
    s['badge']   = ParagraphStyle('badge',   fontName='Helvetica-Bold',    fontSize=9,   leading=14, textColor=ACCENT_GOLD)
    s['ctitle']  = ParagraphStyle('ctitle',  fontName='Helvetica-Bold',    fontSize=26,  leading=34, textColor=WHITE, spaceAfter=6)
    s['csub']    = ParagraphStyle('csub',    fontName='Helvetica',         fontSize=15,  leading=21, textColor=ACCENT_LIGHT, spaceAfter=20)
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
    s['teal']    = ParagraphStyle('teal',    fontName='Helvetica-Bold',    fontSize=9.5, leading=14, textColor=ACCENT_TEAL)
    return s

def sp(n=6):   return Spacer(1, n)
def rule(s):   return HRFlowable(width='100%', thickness=0.5, color=RULE_COLOR, spaceAfter=6, spaceBefore=6)
def arule():   return HRFlowable(width='40%',  thickness=1.5, color=ACCENT_BLUE, spaceAfter=20)

def cb(text, s):
    lines = text.strip().split('\n')
    rows = [[Paragraph(l.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'), s['code'])] for l in lines]
    return Table(rows, colWidths=[AVAIL_W - 16*mm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
            ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING',  (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER_GRAY),
        ]))

def tbl(headers, rows, s, cw=None):
    hs = ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=8, leading=12, textColor=ACCENT_LIGHT)
    cs = ParagraphStyle('td', fontName='Helvetica',      fontSize=8, leading=12, textColor=TEXT_WHITE)
    cg = ParagraphStyle('tg', fontName='Helvetica',      fontSize=8, leading=12, textColor=TEXT_GRAY)
    data = [[Paragraph(h, hs) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), cg if i == 0 and len(headers) > 2 else cs) for i, c in enumerate(row)])
    avail = AVAIL_W - 4*mm
    if cw is None: cw = [avail / len(headers)] * len(headers)
    return Table(data, colWidths=cw, repeatRows=1,
        style=TableStyle([
            ('BACKGROUND',  (0,0), (-1,0),  TABLE_HEAD),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [TABLE_ALT, CODE_BG]),
            ('GRID',        (0,0), (-1,-1), 0.4, TABLE_BORDER),
            ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING',  (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('VALIGN',      (0,0), (-1,-1), 'TOP'),
        ]))

def dg(drawing):
    """Wrap a Drawing in a Table to guarantee ReportLab reserves its full height + padding."""
    return Table([[drawing]],
        colWidths=[AVAIL_W],
        style=TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), DARK_BG),
            ('LEFTPADDING',   (0,0), (-1,-1), 0),
            ('RIGHTPADDING',  (0,0), (-1,-1), 0),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('BOX',           (0,0), (-1,-1), 0.5, BORDER_GRAY),
        ]))


def box(items, s, title=None, border=None):
    bcolor = border or ACCENT_BLUE
    content = []
    if title: content.append(Paragraph(title, s['atitle']))
    for item in items:
        content.append(Paragraph(f'  {item}', s['abody']) if isinstance(item, str) else item)
    return Table([[content]], colWidths=[AVAIL_W - 4*mm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
            ('BOX', (0,0), (-1,-1), 1.2, bcolor),
            ('LEFTPADDING', (0,0), (-1,-1), 14), ('RIGHTPADDING', (0,0), (-1,-1), 14),
            ('TOPPADDING',  (0,0), (-1,-1), 12), ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ]))


def _drect(d, x, y, w, h, fill, stroke=None, sw=1):
    d.add(Rect(x, y, w, h, fillColor=fill, strokeColor=stroke or fill, strokeWidth=sw))

def _dtext(d, x, y, text, font='Helvetica', size=9, color=None, anchor='middle'):
    d.add(String(x, y, text, fontName=font, fontSize=size, fillColor=color or TEXT_WHITE, textAnchor=anchor))

def _darrow(d, x1, y1, x2, y2, color=None, head=6):
    c = color or ACCENT_BLUE
    d.add(Line(x1, y1, x2, y2, strokeColor=c, strokeWidth=1.5))
    if y2 < y1:
        pts = [x2, y2, x2-head/2, y2+head, x2+head/2, y2+head]
    elif y2 > y1:
        pts = [x2, y2, x2-head/2, y2-head, x2+head/2, y2-head]
    elif x2 > x1:
        pts = [x2, y2, x2-head, y2+head/2, x2-head, y2-head/2]
    else:
        pts = [x2, y2, x2+head, y2+head/2, x2+head, y2-head/2]
    d.add(Polygon(pts, fillColor=c, strokeColor=c, strokeWidth=0))

def _dbox(d, x, y, w, h, title, sub='', fill=None, border=None, tsize=9, ssize=7.5):
    fc = fill or colors.HexColor('#1e1e3a')
    bc = border or ACCENT_BLUE
    _drect(d, x, y, w, h, fc, bc, 1.5)
    mid = y + h/2
    if sub:
        _dtext(d, x+w/2, mid+5,  title, 'Helvetica-Bold', tsize, TEXT_WHITE)
        _dtext(d, x+w/2, mid-7, sub,   'Helvetica',      ssize, TEXT_GRAY)
    else:
        _dtext(d, x+w/2, mid-4,  title, 'Helvetica-Bold', tsize, TEXT_WHITE)


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 1 — ATF 6-Layer Stack
# ─────────────────────────────────────────────────────────────────────────────
def diagram_atf_stack():
    W, H = AVAIL_W, 310
    d = Drawing(W, H)
    _drect(d, 0, 0, W, H, colors.HexColor('#0a0a16'))

    layers = [
        (colors.HexColor('#1a1a2e'), ACCENT_BLUE,   'LAYER 1 -- Identity & Delegation (RFC-ATF-1)',        '6 invariants   |  AIR  DR  TAR  Trust Lattice',                    6),
        (colors.HexColor('#16162a'), ACCENT_BLUE,   'LAYER 2 -- Runtime Continuity (RFC-ATF-2)',           '8 invariants   |  RCR  CES  AFG  RC  HALT propagation',            14),
        (colors.HexColor('#131326'), ACCENT_LIGHT,  'LAYER 3 -- Evidence & Forensic (RFC-ATF-3)',          '40 invariants  |  OEP  GPIL  ELC  FVP  GECR  SGIP',               54),
        (colors.HexColor('#111124'), ACCENT_LIGHT,  'LAYER 4 -- Proactive Governance (RFC-ATF-4)',         '16 invariants  |  AGVP  SSD  DSPP  PVR  CRSI  RSA',               70),
        (colors.HexColor('#0f0f22'), colors.HexColor('#9b59b6'), 'LAYER 5 -- Cognitive Governance (RFC-ATF-5)', '18 invariants  |  CGE  GUGT  TGB  CAT  UIR  TCS  RAR', 88),
        (colors.HexColor('#1a140a'), ACCENT_GOLD,   'LAYER 6 -- Behavioral Exec. Verification (RFC-ATF-6)  THIS RFC', '18 invariants  |  BAR  CCS  CTCHC  session integrity proof',   106),
    ]

    pad = 8; lh = 38; gap = 5
    total = len(layers)*lh + (len(layers)-1)*gap + 2*pad
    start_y = (H - total)/2 + pad

    for i, (fill, border, title, sub, tot) in enumerate(layers):
        y = start_y + i*(lh+gap)
        _drect(d, pad, y, W-2*pad, lh, fill, border, 2.0 if i == 5 else 1.0)
        mid = y + lh/2
        _dtext(d, 18+pad, mid+6,  title, 'Helvetica-Bold', 8.5, TEXT_WHITE, 'start')
        _dtext(d, 18+pad, mid-7,  sub,   'Helvetica',      7.5, TEXT_GRAY,  'start')
        bx = W - pad - 64
        _drect(d, bx, y+10, 60, lh-20, border, border, 0)
        _dtext(d, bx+30, y+lh/2-5, f'{tot} inv total', 'Helvetica-Bold', 7, DARK_BG, 'middle')

    _dtext(d, W/2, H-12, 'ATF PROTOCOL STACK -- Six-Layer Architecture  (Layer 6 = RFC-ATF-6)',
           'Helvetica-Bold', 10, ACCENT_GOLD, 'middle')
    return d


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 2 — BAR Architecture Flow
# ─────────────────────────────────────────────────────────────────────────────
def diagram_bar_flow():
    W, H = AVAIL_W, 260
    d = Drawing(W, H)
    _drect(d, 0, 0, W, H, colors.HexColor('#0a0a16'))
    _dtext(d, W/2, H-14, 'BAR Architecture Flow -- PQC-Sealed Per-Turn Behavioral Attestation',
           'Helvetica-Bold', 10, ACCENT_GOLD, 'middle')

    # Pipeline row
    steps = [
        ('AGENT\nOUTPUT\nTURN i',       'output_text\n(any length)',             ACCENT_BLUE),
        ('SHA3-256\n(output_text\n.encode())', 'output_hash\n= 64-char hex',      ACCENT_TEAL),
        ('HASH\nBINDING\n3-input',      'SHA3-256(\nout_h||rcpt_id\n||str(idx))', ACCENT_LIGHT),
        ('content\n_hash\n= 64 hex',    'unique per\nturn+receipt\n+position',    colors.HexColor('#9b59b6')),
        ('ML-DSA-65\nSIGN\n(FIPS204)',  'pqc_sig =\ndilithium3\n.sign()',         ACCENT_ORANGE),
        ('SEALED\nBAR\nPERSISTED',      'DB insert\nappend-only\n+ PQC-sealed',   ACCENT_GOLD),
    ]

    bw = 52; bh = 60
    n  = len(steps)
    gap = (W - 16 - n*bw) / (n-1)
    sx  = 8
    cy  = H/2 - 5

    for i, (top, bot, col) in enumerate(steps):
        x = sx + i*(bw+gap)
        is_last = (i == n-1)
        fi = col if is_last else colors.HexColor('#%02x%02x%02x' % (
            max(0,min(255,int(col.red*255*0.18+8))),
            max(0,min(255,int(col.green*255*0.18+8))),
            max(0,min(255,int(col.blue*255*0.18+8)))))
        _drect(d, x, cy-bh/2, bw, bh, fi, col, 2.0 if is_last else 0.8)
        tc = DARK_BG if is_last else col
        for j, ln in enumerate(top.split('\n')):
            _dtext(d, x+bw/2, cy+bh/2-12-j*10, ln, 'Helvetica-Bold', 7.5, tc)
        for j, ln in enumerate(bot.split('\n')):
            _dtext(d, x+bw/2, cy-bh/2+24-j*9, ln, 'Helvetica', 6.5, tc if is_last else TEXT_GRAY)
        if i < n-1:
            ax = x+bw+2; ay = cy
            d.add(Line(ax, ay, ax+gap-6, ay, strokeColor=TEXT_GRAY, strokeWidth=1.2))
            d.add(Polygon([ax+gap-6,ay, ax+gap-2,ay+4, ax+gap-2,ay-4],
                          fillColor=TEXT_GRAY, strokeColor=TEXT_GRAY, strokeWidth=0))

    # formula bar below
    _dtext(d, W/2, 14, 'content_hash = SHA3-256( output_hash  ||  governing_receipt_id  ||  str(turn_index) )',
           'Courier', 7.5, ACCENT_TEAL, 'middle')
    _dtext(d, W/2, 26, 'BEV-INV-002: three-input binding makes output, receipt, and turn position simultaneously tamper-evident',
           'Helvetica-Oblique', 7, TEXT_GRAY, 'middle')
    return d


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 3 — CCS Score Breakdown + Verdict Ladder
# ─────────────────────────────────────────────────────────────────────────────
def diagram_ccs_score():
    W, H = AVAIL_W, 210
    d = Drawing(W, H)
    _drect(d, 0, 0, W, H, colors.HexColor('#0a0a16'))
    _dtext(d, W/2, H-14, 'CCS -- Score Components (left) and Verdict Ladder (right)',
           'Helvetica-Bold', 10, ACCENT_GOLD, 'middle')

    # Left: 4 bars
    comps = [
        ('OBS  Output Boundary Score',    40, ACCENT_BLUE,              'max(0, 40 - 10 x violations)'),
        ('CSS  Constraint Satisfaction',  30, ACCENT_TEAL,              'max(0, 30 - 8 x failures)'),
        ('SDS  Semantic Drift Score',     20, colors.HexColor('#9b59b6'),'max(0, 20 x (1 - drift_mag))'),
        ('AAS  Authority Alignment',      10, ACCENT_ORANGE,            '10 if scope_ok else 0'),
    ]
    left_w = W * 0.50
    bar_max = left_w - 72; bh = 28; gap = 8; sy = 24

    for i, (name, pts, col, formula) in enumerate(comps):
        y = sy + i*(bh+gap)
        fw = (pts/100.0)*bar_max
        _drect(d, 64, y, bar_max, bh, colors.HexColor('#111120'), BORDER_GRAY, 0.4)
        _drect(d, 64, y, fw,      bh, col, col, 0)
        _dtext(d, 62, y+bh/2+3,  f'{pts}pts', 'Helvetica-Bold', 8, col, 'end')
        _dtext(d, 68, y+bh/2+4,  name,    'Helvetica-Bold', 7.5, WHITE,    'start')
        _dtext(d, 68, y+bh/2-7,  formula, 'Courier',        6.5, TEXT_GRAY,'start')

    _dtext(d, 64+bar_max/2, sy+4*(bh+gap)+4,
           'score = (OBS+CSS+SDS+AAS) / 100  =>  conformance_score in [0.0, 1.0]',
           'Helvetica-Bold', 7.5, ACCENT_GOLD, 'middle')

    # Right: verdict ladder
    rx = left_w + 8
    verdicts = [
        ('CONFORMANT', '>= 90.0',  ACCENT_GREEN,  'outputs fully within bounds'),
        ('DRIFTING',   '70-89.9',  ACCENT_TEAL,   'AGVP PVR: MONITORING'),
        ('BREACH',     '50-69.9',  ACCENT_ORANGE,  'AGVP PVR: WARNING'),
        ('VIOLATION',  '< 50.0',   ACCENT_RED,     'HALT PROPAGATION'),
        ('NO_DATA',    '-1.0',     TEXT_GRAY,      'CCS_ENABLED=false or REDACTED'),
    ]
    vw = W - rx - 8; vh = 26; vgap = 6; vsy = 24
    for i, (v, score, col, note) in enumerate(verdicts):
        y = vsy + i*(vh+vgap)
        fi = colors.HexColor('#%02x%02x%02x' % (
            max(0,min(255,int(col.red*255*0.22+8))),
            max(0,min(255,int(col.green*255*0.22+8))),
            max(0,min(255,int(col.blue*255*0.22+8)))))
        _drect(d, rx, y, vw, vh, fi, col, 2.0 if v=='VIOLATION' else 0.8)
        _dtext(d, rx+6, y+vh/2+3,  v,     'Helvetica-Bold', 8.5, col,       'start')
        _dtext(d, rx+6, y+vh/2-7,  f'{score}  --  {note}', 'Helvetica', 7, TEXT_GRAY, 'start')

    d.add(Line(left_w+3, 18, left_w+3, H-18, strokeColor=BORDER_GRAY, strokeWidth=0.5))
    return d


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 4 — CTCHC Chain
# ─────────────────────────────────────────────────────────────────────────────
def diagram_ctchc():
    W, H = AVAIL_W, 200
    d = Drawing(W, H)
    _drect(d, 0, 0, W, H, colors.HexColor('#0a0a16'))
    _dtext(d, W/2, H-14, 'CTCHC -- Cross-Turn Coherence Hash Chain -- Session Integrity Proof (SIP)',
           'Helvetica-Bold', 10, ACCENT_GOLD, 'middle')

    nodes = [
        ('GENESIS\nHASH',   'SHA3-256(\nsess_id||\nreceipt_id||\nGENESIS)',    ACCENT_TEAL, True),
        ('LINK[0]',         'SHA3-256(\n{prev:genesis,\nturn:h0,\nreceipt})',  ACCENT_BLUE, False),
        ('LINK[1]',         'SHA3-256(\n{prev:L0,\nturn:h1,\nreceipt})',       ACCENT_BLUE, False),
        ('LINK[n]',         'SHA3-256(\n{prev:L_{n-1},\nturn:hn,\nreceipt})', ACCENT_BLUE, False),
        ('CHAIN\nSEAL\nSIP','SHA3-256(\ngenesis||\nall_links||\ntip)\nML-DSA-65', ACCENT_GOLD, True),
    ]
    bw = 58; bh = 84; n = len(nodes)
    gap = (W-16-n*bw)/(n-1); sx = 8; cy = H/2-8

    for i, (label, sub, col, highlight) in enumerate(nodes):
        x = sx + i*(bw+gap)
        fi = col if highlight else colors.HexColor('#%02x%02x%02x' % (
            max(0,min(255,int(col.red*255*0.18+8))),
            max(0,min(255,int(col.green*255*0.18+8))),
            max(0,min(255,int(col.blue*255*0.18+8)))))
        _drect(d, x, cy-bh/2, bw, bh, fi, col, 2.0 if highlight else 0.8)
        tc = DARK_BG if highlight else col
        for j, ln in enumerate(label.split('\n')):
            _dtext(d, x+bw/2, cy+bh/2-14-j*11, ln, 'Helvetica-Bold', 8, tc)
        for j, ln in enumerate(sub.split('\n')):
            _dtext(d, x+bw/2, cy-bh/2+34-j*9, ln, 'Courier', 5.8, tc if highlight else TEXT_GRAY)
        if i < n-1:
            if i == 2:  # ellipsis
                _dtext(d, x+bw+gap/2, cy, '...', 'Helvetica-Bold', 14, TEXT_GRAY)
            else:
                ax = x+bw+2; ay = cy
                d.add(Line(ax, ay, ax+gap-6, ay, strokeColor=TEXT_GRAY, strokeWidth=1.2))
                d.add(Polygon([ax+gap-6,ay, ax+gap-2,ay+4, ax+gap-2,ay-4],
                              fillColor=TEXT_GRAY, strokeColor=TEXT_GRAY, strokeWidth=0))

    _dtext(d, W/2, 12,
           'Every link: SHA3-256(json.dumps({"prev":prev_hash,"turn":output_hash,"receipt":receipt_id},sort_keys=True))',
           'Courier', 7, ACCENT_TEAL, 'middle')
    return d


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 5 — BEV Three-Gap Closure
# ─────────────────────────────────────────────────────────────────────────────
def diagram_three_gaps():
    W, H = AVAIL_W, 220
    d = Drawing(W, H)
    _drect(d, 0, 0, W, H, colors.HexColor('#0a0a16'))
    _dtext(d, W/2, H-14, 'The Behavioral Execution Gap -- Three Structural Problems Closed by BEV',
           'Helvetica-Bold', 10, ACCENT_GOLD, 'middle')

    cols_data = [
        ('Gap_BAG', 'Behavioral\nAttestation Gap', ACCENT_BLUE,
         'Authorization',   '???',    'Behavioral\nOutput',
         'BAR closes\nGap_BAG', 'BEV-INV\n001-004\n015-016'),
        ('Gap_COP', 'Conformance\nObservability\nProblem', ACCENT_TEAL,
         'Execution\nOccurs',  'No signal',  'AGVP\nblind',
         'CCS closes\nGap_COP', 'BEV-INV\n005-009\n017'),
        ('Gap_MCP', 'Multi-Turn\nCoherence\nProblem', colors.HexColor('#9b59b6'),
         'Turn 0\nBAR',   'no chain',  'Turn N\nBAR',
         'CTCHC closes\nGap_MCP', 'BEV-INV\n010-014\n018'),
    ]

    cw = (W-16)/3; sx = 8
    for i, (gap_id, name, col, left, mid, right, solution, invs) in enumerate(cols_data):
        x = sx + i*(cw+2)
        fi = colors.HexColor('#%02x%02x%02x' % (
            max(0,min(255,int(col.red*255*0.14+8))),
            max(0,min(255,int(col.green*255*0.14+8))),
            max(0,min(255,int(col.blue*255*0.14+8)))))

        # Header bar
        _drect(d, x, H-36, cw-2, 20, col, col, 0)
        _dtext(d, x+(cw-2)/2, H-22, gap_id, 'Helvetica-Bold', 10, DARK_BG)

        # Name
        for j, ln in enumerate(name.split('\n')):
            _dtext(d, x+(cw-2)/2, H-46-j*11, ln, 'Helvetica-Bold', 8, col)

        # Problem row (3 boxes with arrows)
        pby = H-110; pbh = 26; pbw = (cw-2-8)/3
        for k, (lbl, fc) in enumerate([(left, colors.HexColor('#1a0808')),
                                       (mid,  colors.HexColor('#200808')),
                                       (right,colors.HexColor('#1a0808'))]):
            bx = x + k*(pbw+4)
            _drect(d, bx, pby, pbw, pbh, fc,
                   ACCENT_RED if k==1 else BORDER_GRAY, 0.8 if k==1 else 0.4)
            for j2, ln2 in enumerate(lbl.split('\n')):
                _dtext(d, bx+pbw/2, pby+pbh/2+4-j2*10, ln2, 'Helvetica', 6.5,
                       ACCENT_RED if k==1 else TEXT_GRAY)
            if k < 2:
                ax2 = bx+pbw+2; ay2 = pby+pbh/2
                d.add(Line(ax2, ay2, ax2+2, ay2, strokeColor=TEXT_GRAY, strokeWidth=0.8))

        # Arrow down
        ay3 = pby-4
        d.add(Line(x+(cw-2)/2, ay3, x+(cw-2)/2, ay3-12,
                   strokeColor=ACCENT_GREEN, strokeWidth=1.5))
        d.add(Polygon([x+(cw-2)/2, ay3-12, x+(cw-2)/2-5, ay3-7, x+(cw-2)/2+5, ay3-7],
                      fillColor=ACCENT_GREEN, strokeColor=ACCENT_GREEN, strokeWidth=0))

        # Solution box
        sby = ay3-48; sbh = 34
        _drect(d, x, sby, cw-2, sbh, fi, col, 1.2)
        for j, ln in enumerate(solution.split('\n')):
            _dtext(d, x+(cw-2)/2, sby+sbh-12-j*11, ln, 'Helvetica-Bold', 8, col)

        # Invariant tags
        for j, ln in enumerate(invs.split('\n')):
            _dtext(d, x+(cw-2)/2, sby-10-j*11, ln, 'Courier', 7, col)

    return d


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 6 — CCS-AGVP Integration Loop
# ─────────────────────────────────────────────────────────────────────────────
def diagram_agvp_loop():
    W, H = AVAIL_W, 230
    d = Drawing(W, H)
    _drect(d, 0, 0, W, H, colors.HexColor('#0a0a16'))
    _dtext(d, W/2, H-14, 'CCS -> AGVP Integration Loop -- BEV-INV-007/008 Enforcement',
           'Helvetica-Bold', 10, ACCENT_GOLD, 'middle')

    # Pipeline
    pipe = [
        (W*0.12, 'AGENT\nTURN i',       ACCENT_BLUE),
        (W*0.38, 'BAR + CCS\nATOMIC',   ACCENT_TEAL),
        (W*0.62, 'VERDICT\nCHECK',      colors.HexColor('#9b59b6')),
    ]
    bw=76; bh=50; py=H/2+10
    for (cx, lbl, col) in pipe:
        fi = colors.HexColor('#%02x%02x%02x' % (
            max(0,min(255,int(col.red*255*0.2+8))),
            max(0,min(255,int(col.green*255*0.2+8))),
            max(0,min(255,int(col.blue*255*0.2+8)))))
        _drect(d, cx-bw/2, py-bh/2, bw, bh, fi, col, 1.5)
        for j, ln in enumerate(lbl.split('\n')):
            _dtext(d, cx, py+8-j*13, ln, 'Helvetica-Bold', 9, col)
    for i in range(len(pipe)-1):
        ax1 = pipe[i][0]+bw/2+1; ax2 = pipe[i+1][0]-bw/2-1; ay = py
        d.add(Line(ax1, ay, ax2-6, ay, strokeColor=TEXT_GRAY, strokeWidth=1.2))
        d.add(Polygon([ax2-6,ay,ax2-2,ay+4,ax2-2,ay-4],fillColor=TEXT_GRAY,strokeColor=TEXT_GRAY,strokeWidth=0))

    # Outcome branches from verdict
    vcx = pipe[2][0]; vright = vcx+bw/2
    outcomes = [
        ('CONFORMANT',  '=> next turn authorized',  ACCENT_GREEN,  py-bh/2-30,  0),
        ('DRIFTING',    '=> PVR: MONITORING',        ACCENT_TEAL,   py-bh/2-60,  8),
        ('BREACH',      '=> PVR: WARNING',           ACCENT_ORANGE, py-bh/2-90,  16),
        ('VIOLATION',   '=> HALT PROPAGATION',       ACCENT_RED,    py-bh/2-122, 24),
    ]
    ow = W - vright - 18
    for label, note, col, oy, ox in outcomes:
        bx = vright + 10 + ox
        fi = colors.HexColor('#%02x%02x%02x' % (
            max(0,min(255,int(col.red*255*0.22+6))),
            max(0,min(255,int(col.green*255*0.22+6))),
            max(0,min(255,int(col.blue*255*0.22+6)))))
        _drect(d, bx, oy, ow-ox, 22, fi, col, 1.5 if label=='VIOLATION' else 0.8)
        _dtext(d, bx+6, oy+14, label, 'Helvetica-Bold', 8, col, 'start')
        _dtext(d, bx+6, oy+4,  note,  'Helvetica',      7, TEXT_GRAY, 'start')
        d.add(Line(vright+2, py, bx-2, oy+11, strokeColor=col, strokeWidth=0.8))

    # AGVP watchdog box
    agx = W*0.38; agy = py+bh/2+30; agw = 130; agh = 28
    _drect(d, agx-agw/2, agy, agw, agh, colors.HexColor('#1a0d2e'), ACCENT_LIGHT, 1)
    _dtext(d, agx, agy+agh/2+4, 'AGVP Watchdog (RFC-ATF-4)', 'Helvetica-Bold', 8, ACCENT_LIGHT)
    _dtext(d, agx, agy+agh/2-7, 'Anticipatory Governance Veto Protocol', 'Helvetica', 7, TEXT_GRAY)
    d.add(Line(agx, agy, agx, py+bh/2, strokeColor=ACCENT_LIGHT, strokeWidth=1, strokeDashArray=[3,2]))
    return d


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 7 — Compliance Hierarchy
# ─────────────────────────────────────────────────────────────────────────────
def diagram_compliance():
    W, H = AVAIL_W, 240
    d = Drawing(W, H)
    _drect(d, 0, 0, W, H, colors.HexColor('#0a0a16'))
    _dtext(d, W/2, H-14, 'ATF Compliance Hierarchy -- Six Tiers -- 106 Invariants',
           'Helvetica-Bold', 10, ACCENT_GOLD, 'middle')

    tiers = [
        ('ATF-BEV-Compliant',   'RFC-ATF-1+2+3+4+5+6  --  BAR + CCS + CTCHC  --  THIS RFC',  '106 inv', ACCENT_GOLD, True),
        ('ATF-CGL-Compliant',   'RFC-ATF-1+2+3+4+5  --  CGE + GUGT + TGB',                    '88 inv',  colors.HexColor('#9b59b6'), False),
        ('ATF-PGL-Compliant',   'RFC-ATF-1+2+3+4  --  AGVP + SSD + DSPP',                     '70 inv',  ACCENT_LIGHT, False),
        ('ATF-FEI-Compliant',   'RFC-ATF-1+2+3  --  OEP + GPIL + Forensic verification',       '40 inv',  ACCENT_TEAL, False),
        ('ATF-RGC-Compliant',   'RFC-ATF-1+2  --  Runtime continuity + HALT propagation',      '14 inv',  ACCENT_BLUE, False),
        ('ATF-Compliant-L1/3',  'RFC-ATF-1  --  Identity + Delegation + Trust Lattice',        '6 inv',   colors.HexColor('#4a7cc7'), False),
    ]

    th=30; gap=4; base_w = W-40; sx = 20; sy = 18
    for i, (name, desc, inv, col, top) in enumerate(tiers):
        taper = (len(tiers)-1-i)*12
        tw = base_w - taper; tx = sx + taper/2
        y  = sy + i*(th+gap)
        fi = col if top else colors.HexColor('#%02x%02x%02x' % (
            max(0,min(255,int(col.red*255*0.2+10))),
            max(0,min(255,int(col.green*255*0.2+10))),
            max(0,min(255,int(col.blue*255*0.2+10)))))
        _drect(d, tx, y, tw, th, fi, col, 2.0 if top else 0.8)
        tc = DARK_BG if top else col
        _dtext(d, tx+8, y+th/2+5,  name, 'Helvetica-Bold', 8.5, tc, 'start')
        _dtext(d, tx+8, y+th/2-6,  desc, 'Helvetica',      7.0, tc if top else TEXT_GRAY, 'start')
        _dtext(d, tx+tw-8, y+th/2-3, inv, 'Helvetica-Bold', 9, ACCENT_GOLD if top else TEXT_GRAY, 'end')

    return d


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 8 — BEV Per-Turn Timeline
# ─────────────────────────────────────────────────────────────────────────────
def diagram_bev_timeline():
    W, H = AVAIL_W, 170
    d = Drawing(W, H)
    _drect(d, 0, 0, W, H, colors.HexColor('#0a0a16'))
    _dtext(d, W/2, H-14, 'BEV Per-Turn Execution Sequence -- 9 Ordered Steps',
           'Helvetica-Bold', 10, ACCENT_GOLD, 'middle')

    steps_data = [
        (1,  'Agent\nexecutes\nturn',      ACCENT_BLUE),
        (2,  'output\n_hash\nSHA3-256',    ACCENT_TEAL),
        (3,  'CCS\ncomputed\nfrom BO+CV',  colors.HexColor('#9b59b6')),
        (4,  'chain\n_link\ncomputed',     ACCENT_TEAL),
        (5,  'BAR\nassembled\n(all flds)', ACCENT_LIGHT),
        (6,  'content\n_hash\ncomputed',   ACCENT_ORANGE),
        (7,  'pqc_sig\ncomputed\nML-DSA',  ACCENT_ORANGE),
        (8,  'BAR\npersisted\nDB',         ACCENT_GREEN),
        (9,  'AGVP\ntrigger\n(if drift)',  ACCENT_RED),
    ]
    n = len(steps_data); bw = (W-16)/n-3; bh = 62; sy = H/2-bh/2+5
    for i, (num, lbl, col) in enumerate(steps_data):
        x = 8 + i*(bw+3)
        fi = colors.HexColor('#%02x%02x%02x' % (
            max(0,min(255,int(col.red*255*0.2+8))),
            max(0,min(255,int(col.green*255*0.2+8))),
            max(0,min(255,int(col.blue*255*0.2+8)))))
        _drect(d, x, sy, bw, bh, fi, col, 1.5 if num in (8,9) else 0.8)
        _dtext(d, x+bw/2, sy+bh-12, str(num), 'Helvetica-Bold', 10, col)
        for j, ln in enumerate(lbl.split('\n')):
            _dtext(d, x+bw/2, sy+bh-28-j*11, ln, 'Helvetica', 6.5, TEXT_WHITE)
        if i < n-1:
            ax = x+bw+1; ay = sy+bh/2
            d.add(Line(ax, ay, ax+2, ay, strokeColor=TEXT_GRAY, strokeWidth=0.8))
            d.add(Polygon([ax+2,ay,ax-1,ay+3,ax-1,ay-3],fillColor=TEXT_GRAY,strokeColor=TEXT_GRAY,strokeWidth=0))

    # Phase labels
    _dtext(d, 8+1.5*(bw+3)+bw/2, sy-10, 'Execution', 'Helvetica-Oblique', 7, TEXT_GRAY)
    _dtext(d, 8+5*(bw+3)+bw/2,   sy-10, 'BEV Production', 'Helvetica-Oblique', 7, TEXT_GRAY)
    _dtext(d, 8+7.5*(bw+3)+bw/2, sy-10, 'Persist + AGVP', 'Helvetica-Oblique', 7, TEXT_GRAY)

    _dtext(d, W/2, 12, 'Steps 1-8 mandatory per turn (BEV-INV-001).  Step 9 conditional on verdict >= DRIFTING (BEV-INV-007).',
           'Helvetica', 7, TEXT_GRAY, 'middle')
    return d


# ═════════════════════════════════════════════════════════════════════════════
# CONTENT
# ═════════════════════════════════════════════════════════════════════════════
def build(output):
    s = S()
    st = []

    # ── COVER ─────────────────────────────────────────────────────────────────
    if os.path.exists(LOGO):
        st += [sp(20), Image(LOGO, width=52*mm, height=52*mm, hAlign='CENTER'), sp(12)]
    else:
        st += [sp(60)]

    st += [
        Paragraph('OMNIX QUANTUM OPEN STANDARD', s['badge']), sp(4),
        Paragraph('RFC-ATF-6', s['ctitle']),
        Paragraph('Agent Trust Fabric -- Behavioral Execution Verification Protocol', s['csub']),
        Paragraph('Behavioral Anchor Record (BAR) -- Constraint Conformance Signal (CCS) -- Cross-Turn Coherence Hash Chain (CTCHC)', s['csub']),
        sp(10), rule(s), sp(8),
        Paragraph('Harold Alberto Nunes Rodelo, Editor', s['cmeta']),
        Paragraph('OMNIX QUANTUM LTD -- 71-75 Shelton Street, Covent Garden, London WC2H 9JQ, England', s['cmeta']),
        Paragraph('standards@omnixquantum.com  --  omnixquantum.net', s['cmeta']),
        sp(6),
        Paragraph('Version 1.0.0  --  May 2026  --  DOI: pending submission', s['cmeta']),
        Paragraph('Extension to RFC-ATF-1, RFC-ATF-2, RFC-ATF-3, RFC-ATF-4, and RFC-ATF-5', s['cmeta']),
        sp(14), rule(s), sp(10),
        Paragraph('Compliance Designation: <b>ATF-BEV-Compliant</b> -- Sixth and highest tier', s['gold']),
        Paragraph('18 new invariants (BEV-INV-001-018) -- 106 total ATF invariants -- 20 protocol families', s['gold']),
        sp(20), PageBreak(),
    ]

    # ── TABLE OF CONTENTS ─────────────────────────────────────────────────────
    st += [Paragraph('Table of Contents', s['h1']), rule(s)]
    toc_items = [
        ('Abstract', '2'),
        ('1.  Problem Statement -- The Behavioral Execution Gap', '2'),
        ('2.  Architecture Overview -- BEV Layer', '3'),
        ('3.  Behavioral Anchor Record (BAR)', '4'),
        ('4.  Constraint Conformance Signal (CCS)', '7'),
        ('5.  Cross-Turn Coherence Hash Chain (CTCHC)', '10'),
        ('6.  BEV Layer Composition', '13'),
        ('7.  Formal Verification (OMNIX-FVS-1.0 Extension)', '14'),
        ('8.  Combined Invariant Summary -- 106 Total', '15'),
        ('9.  ATF-BEV-Compliant Designation', '16'),
        ('10. Implementation Reference', '17'),
        ('11. Security Considerations', '18'),
        ('12. Novel Contributions', '19'),
        ('13. Distinction from Prior Art', '20'),
        ('14. Regulatory Alignment', '21'),
        ('15. Known Limitations and Open Questions', '22'),
        ('16. References', '23'),
        ('Appendix A -- BEV Wire Formats (JSON Schemas)', '24'),
        ('Appendix B -- Cross-Layer Integration Map', '26'),
        ('Appendix C -- ATF-BEV-Compliant Compliance Checklist', '27'),
        ("Author's Address", '28'),
    ]
    for item, pg in toc_items:
        st.append(tbl([item, pg], [[]], s, cw=[AVAIL_W-20*mm, 18*mm]) if False else
                  Paragraph(f'  {item}  <font color="#aaaaaa">...... {pg}</font>', s['body']))
    st += [sp(8), PageBreak()]

    # ── ABSTRACT ──────────────────────────────────────────────────────────────
    st += [Paragraph('Abstract', s['h1']), rule(s)]
    st.append(Paragraph(
        'RFC-ATF-6 specifies the <b>Behavioral Execution Verification Layer (BEV)</b> of the Agent Trust Fabric -- '
        'the sixth and final RFC in the ATF Open Standard series. RFC-ATF-6 answers the structural question '
        'that no prior RFC addresses: <i>did the agent actually behave within its authorized constraints during '
        'execution, turn by turn?</i>', s['body']))
    st.append(Paragraph(
        'The five prior RFCs establish governance infrastructure: who authorized (RFC-ATF-1), was authority '
        'continuously valid (RFC-ATF-2), where does evidence go (RFC-ATF-3), was monitoring active between '
        'requests (RFC-ATF-4), and what else could have happened (RFC-ATF-5). All five share a structural '
        'assumption: the authorized action is treated as a black box. The governance receipt authorizes. '
        'The execution receipt records. But no ATF artifact through RFC-ATF-5 contains a cryptographic record '
        'of what the agent actually produced -- the Behavioral Execution Gap (Gap_BEV).', s['body']))
    st.append(Paragraph(
        'RFC-ATF-6 closes this gap with three new protocol components: the <b>Behavioral Anchor Record (BAR)</b>, '
        'the <b>Constraint Conformance Signal (CCS)</b>, and the <b>Cross-Turn Coherence Hash Chain (CTCHC)</b>. '
        'These components are additive, backward compatible, and constitute Layer 6 of the ATF stack. Together '
        'they produce the first formally specified Session Integrity Proof (SIP) for multi-turn AI agent '
        'interactions -- independently verifiable offline using only the artifact bundle and the platform\'s '
        'Dilithium-3 (ML-DSA-65, FIPS 204) public key.', s['body']))
    st += [arule(), PageBreak()]

    # ── SECTION 1 — PROBLEM STATEMENT ────────────────────────────────────────
    st += [Paragraph('1.  Problem Statement -- The Behavioral Execution Gap', s['h1']), rule(s)]

    st.append(Paragraph('1.1  Gap_BAG -- Behavioral Attestation Gap', s['h2']))
    st.append(Paragraph(
        'Every prior ATF artifact treats the authorized action as a black box. The Governing Receipt (GR) '
        'authorizes the action. The Execution Receipt records that the action occurred. But no artifact '
        'cryptographically binds the GR to what the agent actually produced during execution -- the Behavioral '
        'Output (BO). This is Gap_BAG:', s['body']))
    st.append(cb(
"""  Gap_BAG = { (GR, BO) : no verifiable cryptographic binding exists between GR and BO }

  Consequences:
  (a) Regulatory gap:  EU AI Act Art.9 requires monitoring that AI operates within defined boundaries.
                       Gap_BAG leaves compliance assertion without behavioral evidence.
  (b) Forensic gap:    Auditor cannot reconstruct what the agent actually said or produced.
                       Governance receipts are authorization evidence, not behavioral evidence.
  (c) Liability gap:   Legal counsel cannot prove agent operated within authorized constraints.
                       Receipt says "authorized" -- not "behaved within bounds of authorization."
  (d) Audit gap:       SOC 2 Type II CC7.2 monitoring requires per-event evidence.
                       No BAR = no per-turn behavioral audit trail.""", s))

    st.append(Paragraph('1.2  Gap_COP -- Conformance Observability Problem', s['h2']))
    st.append(Paragraph(
        'The AGVP watchdog (RFC-ATF-4) issues anticipatory vetoes based on observable conformance signals. '
        'For structural governance (CES, fragmentation) and semantic drift (DSPP), signals exist. For '
        'behavioral output conformance -- whether the agent\'s actual outputs satisfy the constraint set '
        'defined in the Governing Receipt -- no governance-native signal existed before this RFC. '
        'Gap_COP left the AGVP input space incomplete for behavioral trajectories:', s['body']))
    st.append(cb(
"""  Gap_COP: AGVP_INPUT_SPACE = {CES, fragmentation_index, DSPP_drift} -- behavioral_conformance

  Without CCS:
    AGVP can detect structural failures (authority over-delegation, fragmentation).
    AGVP can detect semantic drift (token distribution shift).
    AGVP CANNOT detect: agent outputs violating defined output domains.
    AGVP CANNOT detect: agent responses breaching prohibited class constraints.
    AGVP CANNOT detect: cumulative behavioral drift across multi-turn sessions.

  With CCS (RFC-ATF-6):
    AGVP_INPUT_SPACE includes conformance_score per turn.
    Verdicts DRIFTING/BREACH/VIOLATION trigger PVR issuance (BEV-INV-007).
    CCS completes AGVP input space for behavioral governance.""", s))

    st.append(Paragraph('1.3  Gap_MCP -- Multi-Turn Coherence Problem', s['h2']))
    st.append(Paragraph(
        'A set of valid BAR records does not prove Session Coherence without a chaining mechanism. '
        'An adversary could present a subset of BARs (omitting turns where violations occurred), '
        'reorder BARs from different sessions, or substitute BARs from prior compliant sessions to '
        'construct a fraudulent compliance report. Gap_MCP is the absence of a cryptographic Session '
        'Integrity Proof (SIP) that binds the complete turn sequence:', s['body']))
    st.append(cb(
"""  Gap_MCP attacks (without CTCHC):
  (a) Omission attack:      adversary presents {BAR_0, BAR_1, BAR_3} -- BAR_2 violated constraints
  (b) Reordering attack:    adversary presents {BAR_0, BAR_2, BAR_1} -- hides violation sequence
  (c) Substitution attack:  adversary replaces BAR_i with BAR from prior compliant session
  (d) Session mixing:       adversary interleaves BARs from two different session contexts

  Without CTCHC: each BAR is independently valid -- no inter-BAR binding detects attacks (a)-(d).
  With CTCHC (RFC-ATF-6):
    link[n] = SHA3-256({prev: link[n-1], turn: output_hash_n, receipt: governing_receipt_id})
    Attacks (a)-(d) all produce link[n] != CTCHC.final_chain_hash -> VERIFIED = FALSE.""", s))

    st.append(Paragraph('1.4  Formal Definition: Gap_BEV', s['h2']))
    st.append(box([
        Paragraph('Gap_BEV = Gap_BAG ∪ Gap_COP ∪ Gap_MCP', s['gold']),
        Paragraph(
            'Gap_BEV is the Behavioral Execution Gap -- the set of all governance properties that an '
            'ATF-compliant system through RFC-ATF-5 does not formally specify. RFC-ATF-6 closes Gap_BEV '
            'completely. The Behavioral Execution Verification Layer (BEV) is the set of protocol elements, '
            'record types, invariants, and formal proofs that constitute this closure.', s['abody']),
    ], s, border=ACCENT_GOLD))
    st.append(PageBreak())

    # ── SECTION 2 — ARCHITECTURE ──────────────────────────────────────────────
    st += [Paragraph('2.  Architecture Overview -- BEV Layer', s['h1']), rule(s)]

    st.append(Paragraph('2.1  ATF Stack -- Six-Layer Architecture', s['h2']))
    st.append(dg(diagram_atf_stack()))
    st.append(Paragraph(
        'Figure 1. ATF six-layer protocol stack. Layer 6 (gold border) is introduced by RFC-ATF-6.',
        s['caption']))
    st.append(sp(10))
    st.append(cb(
"""  +=========================================================================+
  |       ATF PROTOCOL STACK -- SIX-LAYER COMPLETE ARCHITECTURE           |
  +=========================================================================+
  |                                                                         |
  | Layer 6 -- BEHAVIORAL EXECUTION VERIFICATION LAYER (RFC-ATF-6) * THIS |
  | +-----------------------------------------------------------------------+
  | | BAR: Behavioral Anchor Record                                         |
  | |   -> PQC-signed per-turn attestation of actual agent output           |
  | |   -> content_hash = SHA3-256(output_hash || receipt_id || turn_index) |
  | | CCS: Constraint Conformance Signal                                    |
  | |   -> governance-native conformance_score in [0.0, 1.0] per turn      |
  | |   -> 4 components: OBS(40) + CSS(30) + SDS(20) + AAS(10) = 100      |
  | |   -> AGVP PVR triggered for verdict DRIFTING, BREACH, VIOLATION      |
  | | CTCHC: Cross-Turn Coherence Hash Chain                                |
  | |   -> genesis hash + per-turn links + ML-DSA-65 chain seal (SIP)      |
  | |   -> offline-verifiable Session Integrity Proof                       |
  | +-----------------------------------------------------------------------+
  |                                                                         |
  | Layer 5 -- COGNITIVE GOVERNANCE LAYER (RFC-ATF-5)                       |
  | +-----------------------------------------------------------------------+
  | | CGE: Counterfactual Governance Engine  (fragility_score)              |
  | | GUGT: Grand Unified Governance Theory  (UIR, 6 UGIs)                 |
  | | TGB: Temporal Governance Bridge        (TCS, RAR, TMR)               |
  | +-----------------------------------------------------------------------+
  |                                                                         |
  | Layer 4 -- PROACTIVE GOVERNANCE PLANE (RFC-ATF-4)                       |
  | +-----------------------------------------------------------------------+
  | | AGVP: Anticipatory Governance Veto Protocol  (PVR)                   |
  | | SSD:  Structural Shift Detection  (CRSI)                              |
  | | DSPP: Dynamic Semantic Portability Protocol  (RSA, SDR)              |
  | +-----------------------------------------------------------------------+
  |                                                                         |
  | Layer 3 -- EVIDENCE AND FORENSIC PLANE (RFC-ATF-3)                      |
  | +-----------------------------------------------------------------------+
  | | GPIL: Governance Policy Interoperability Layer                        |
  | | ELC:  Evidence Lifecycle Classification (HOT/WARM/COLD)              |
  | | OEP:  OMNIX Evidence Package  -- offline-verifiable forensic bundle  |
  | | FVP:  Forensic Verification Protocol                                  |
  | +-----------------------------------------------------------------------+
  |                                                                         |
  | Layer 2 -- RUNTIME CONTINUITY PLANE (RFC-ATF-2)                         |
  | +-----------------------------------------------------------------------+
  | | RCR: Runtime Continuity Record                                        |
  | | CES: Coherence Evaluation Score (continuous health signal)            |
  | | AFG: Authority Fragmentation Guard                                    |
  | | RC:  Reauthorization Challenge with HALT propagation                  |
  | +-----------------------------------------------------------------------+
  |                                                                         |
  | Layer 1 -- IDENTITY AND DELEGATION PLANE (RFC-ATF-1)                    |
  | +-----------------------------------------------------------------------+
  | | AIR: Agent Identity Record -- AID-{DOMAIN}-{16HEX}                   |
  | | DR:  Delegation Receipt -- authority budget chain                     |
  | | TAR: Temporal Admissibility Record -- nanosecond admission proof      |
  | | Trust Lattice -- DAG of all delegation receipts                       |
  | +-----------------------------------------------------------------------+
  +=========================================================================+
  | Invariant count: L1=6, L2=8, L3=40, L4=16, L5=18, L6=18  TOTAL: 106  |
  | Compliance tier: ATF-BEV-Compliant (sixth and highest tier)            |
  +=========================================================================+""", s))

    st.append(sp(6))
    st.append(Paragraph('2.2  BEV Module Independence and Failure Isolation', s['h2']))
    st.append(Paragraph(
        'All three BEV modules are independently operable with fail-closed behavior. BAR is '
        'mandatory and blocks output delivery if unavailable. CCS and CTCHC are required for '
        'ATF-BEV-Compliant designation but individually configurable:', s['body']))
    st.append(tbl(['Module', 'Blocks output delivery?', 'Blocking on failure', 'Flag on failure'],
        [['BAR',   'YES -- BEV-INV-001 (fail-closed)',    'Blocking -- no BAR, no output',        'SESSION_HALTED'],
         ['CCS',   'NO  -- non-blocking on failure',      'Non-blocking -- CCS_INCOMPLETE flag',  'CCS_INCOMPLETE on BAR'],
         ['CTCHC', 'NO  -- non-blocking on failure',      'Non-blocking -- CTCHC_INCOMPLETE flag','CTCHC_INCOMPLETE on session']],
        s, cw=[2.5*cm, 4.5*cm, 4.5*cm, 5.3*cm]))
    st.append(sp(6))

    st.append(Paragraph('2.3  BEV Record Sequencing per Turn', s['h2']))
    st.append(cb(
"""  For every execution turn T_i of session S (BEV_ENABLED=true):

  Step 1: Agent executes turn -- produces output_text (Behavioral Output, BO)
  Step 2: output_hash = SHA3-256(output_text.encode('utf-8'))             [BEV-INV-002]
  Step 3: CCS computed from BO against Constraint Vector (CV)             [BEV-INV-005]
  Step 4: chain_link = SHA3-256(json.dumps({prev, turn, receipt}))        [BEV-INV-011]
  Step 5: BAR assembled (all fields populated including ccs_score)        [BEV-INV-001]
  Step 6: content_hash = SHA3-256(output_hash||receipt_id||str(turn_idx)) [BEV-INV-002]
  Step 7: pqc_signature = dilithium3.sign(content_hash, secret_key)      [BEV-INV-004]
  Step 8: BAR persisted to atf_behavioral_anchor_records (append-only)   [BEV-INV-004]
  Step 9: If CCS.verdict in {DRIFTING, BREACH, VIOLATION}: AGVP notified [BEV-INV-007]
  Step 10: If CCS.verdict == HALT (cumulative): session halted immediately [BEV-INV-008]

  Ordering invariant: T(BAR.persist) < T(output.delivery)  [BEV-INV-001]
  Atomicity:          BAR and CCS are produced as a single indivisible unit [BEV-INV-005]""", s))
    st.append(PageBreak())

    # ── SECTION 3 — BAR ───────────────────────────────────────────────────────
    st += [Paragraph('3.  Behavioral Anchor Record (BAR)', s['h1']), rule(s)]
    st.append(Paragraph(
        'The BAR is the first ATF artifact that closes the authorization-to-output chain. It is a '
        'PQC-signed record produced at each execution turn, binding the SHA3-256 hash of the agent\'s '
        'actual output to the governing receipt and turn index. The three-input binding '
        '(output_hash || receipt_id || turn_index) makes the output, the authorization, and the '
        'position simultaneously tamper-evident.', s['body']))

    st.append(Paragraph('3.1  BAR Architecture Flow', s['h2']))
    st.append(dg(diagram_bar_flow()))
    st.append(Paragraph(
        'Figure 2. BAR creation pipeline. Every turn\'s output is hashed, bound to the governing '
        'receipt and turn index, then ML-DSA-65 signed before the BAR is persisted.',
        s['caption']))
    st.append(sp(10))

    st.append(Paragraph('3.2  Content Hash Construction', s['h2']))
    st.append(cb(
"""  # Step-by-step BAR content hash construction (BEV-INV-002)

  output_hash  = hashlib.sha3_256(output_text.encode('utf-8')).hexdigest()
               # 64-char hex string -- SHA3-256 of raw UTF-8 output bytes

  content_hash = hashlib.sha3_256(
      (output_hash + governing_receipt_id + str(turn_index)).encode('utf-8')
  ).hexdigest()
               # Binding: output + authorization receipt + position

  pqc_signature = base64.b64encode(
      dilithium3.sign(content_hash.encode('utf-8'), platform_secret_key)
  ).decode('utf-8')
               # ML-DSA-65 (FIPS 204) over content_hash

  pqc_algorithm = 'ML-DSA-65'

  # Offline verification (any party, no network required):
  assert dilithium3.verify(
      content_hash.encode('utf-8'), pqc_signature_bytes, platform_public_key
  )""", s))
    st.append(sp(6))

    st.append(Paragraph('3.3  BAR Full Specification', s['h2']))
    st.append(cb(
"""  BAR (Behavioral Anchor Record) -- identifier: BAR-{HEX16}

  COMMITTED FIELDS (included in content_hash):
    bar_id                 : "BAR-4A2B8F1C3D5E7A9B"                    (BEV-INV-016)
    session_id             : "SESS-..."
    governing_receipt_id   : "ATFDR-..."            (binding to GR)
    agent_id               : "AID-DOMAIN-..."
    turn_index             : 3                       (0-based, strictly monotone)
    output_hash            : "a3f2b1c4d5e6f7a8..."  (SHA3-256 of output_text)
    output_hash_mode       : "FULL" | "HASHED" | "REDACTED"
    output_payload         : { ...structured output... }  (mode=FULL only)
    constraint_vector      : { ...CV from Governing Receipt... }
    ccs_score              : 87.50                   (OBS+CSS+SDS+AAS)
    ccs_verdict            : "DRIFTING"
    ccs_components         : { obs:40, css:27.5, sds:18, aas:2 }
    chain_link             : "9f3a2b1c4d5e6f7a..."  (CTCHC link for this turn)
    genesis_hash           : "..."                   (turn_index=0 only)
    session_start_ns       : 1748268000000000000     (turn_index=0 only)
    bar_timestamp_ns       : 1748268000123456789
    issued_at              : "2026-05-26T14:00:00.123456789+00:00"

  SEAL FIELDS:
    content_hash           : SHA3-256(output_hash || governing_receipt_id || str(turn_index))
    pqc_signature          : base64(ML-DSA-65.sign(content_hash.encode()))
    pqc_algorithm          : "ML-DSA-65"
    atf_spec_version       : "RFC-ATF-6_v1.0"
    bar_status             : "ACTIVE" | "HALTED" | "VIOLATION"

  METADATA:
    created_at             : TIMESTAMPTZ  (DB server timestamp at INSERT)""", s))
    st.append(sp(6))

    st.append(Paragraph('3.4  Output Hash Privacy Modes', s['h2']))
    st.append(Paragraph(
        'BAR supports three output payload modes to address GDPR, data minimization, and forensic '
        'requirements simultaneously. All modes produce a valid content_hash:', s['body']))
    st.append(tbl(['Mode', 'output_payload stored?', 'CCS computable?', 'GDPR default?', 'Use case'],
        [['FULL',     'Yes -- complete output',      'Yes -- full CV check',    'No',  'Internal forensic audit, regulated outputs'],
         ['HASHED',   'No -- hash only',             'Partial -- OBS+CSS only', 'Yes', 'Production default -- GDPR Art.5 minimization'],
         ['REDACTED', 'No -- field omitted',         'No  -- CCS_ENABLED=false','No',  'Privacy-sensitive regulated domains']],
        s, cw=[2.5*cm, 4.5*cm, 3.8*cm, 3.0*cm, 4.0*cm]))
    st.append(sp(6))

    st.append(Paragraph('3.5  BAR Invariants: BEV-INV-001-004, BEV-INV-015-016', s['h2']))
    st.append(tbl(['Invariant', 'Statement', 'Violation Consequence'],
        [['BEV-INV-001', 'Every execution turn MUST produce a BAR BEFORE output is delivered. No path delivers output without a BAR.',
          'Session flagged BEV-INCOMPLETE. Session halted immediately.'],
         ['BEV-INV-002', 'content_hash = SHA3-256(output_hash || governing_receipt_id || str(turn_index)). Three-input simultaneous binding.',
          'BAR rejected as structurally invalid. Not accepted as attestation evidence.'],
         ['BEV-INV-003', 'A BAR with bar_status=HALTED MUST immediately transition session to SESSION_HALTED. No subsequent turn permitted.',
          'Critical governance violation -- session continues past HALT.'],
         ['BEV-INV-004', 'Every BAR MUST be ML-DSA-65 signed over its content_hash. No UPDATE or DELETE on atf_behavioral_anchor_records.',
          'BAR not independently verifiable. Append-only guarantee broken.'],
         ['BEV-INV-015', 'output_text = "" or whitespace-only MUST set bar_status = VIOLATION. Silent outputs not permissible.',
          'Governance gap -- agent produces no observable output, session continues.'],
         ['BEV-INV-016', 'BAR identifier MUST conform to "BAR-{HEX16}": exactly 16 uppercase hexadecimal characters.',
          'BAR not recognizable as canonical ATF artifact. Interoperability broken.']],
        s, cw=[2.8*cm, 7.5*cm, 5.5*cm]))
    st.append(sp(6))

    st.append(Paragraph('3.6  BAR Database Schema', s['h2']))
    st.append(cb(
"""  -- Table: atf_behavioral_anchor_records  (append-only, BEV-INV-004)
  CREATE TABLE IF NOT EXISTS atf_behavioral_anchor_records (
      bar_id                 VARCHAR(64)   PRIMARY KEY,    -- BAR-{HEX16}
      session_id             VARCHAR(64)   NOT NULL,
      governing_receipt_id   VARCHAR(128)  NOT NULL,
      agent_id               VARCHAR(128)  NOT NULL,
      turn_index             INTEGER       NOT NULL,
      output_hash            VARCHAR(80)   NOT NULL,       -- sha3_256:64hex
      output_hash_mode       VARCHAR(16)   NOT NULL        -- FULL|HASHED|REDACTED
                             CHECK (output_hash_mode IN ('FULL','HASHED','REDACTED')),
      output_payload         JSONB,                        -- mode=FULL only
      constraint_vector      JSONB         NOT NULL,
      ccs_score              NUMERIC(7,4),
      ccs_verdict            VARCHAR(16),
      ccs_components         JSONB,
      chain_link             VARCHAR(64)   NOT NULL,
      genesis_hash           VARCHAR(64),
      session_start_ns       BIGINT,
      bar_timestamp_ns       BIGINT        NOT NULL,
      issued_at              TIMESTAMPTZ   NOT NULL,
      content_hash           VARCHAR(64)   NOT NULL,
      pqc_signature          TEXT          NOT NULL,
      pqc_algorithm          VARCHAR(16)   NOT NULL DEFAULT 'ML-DSA-65',
      atf_spec_version       VARCHAR(8)    NOT NULL DEFAULT '1.6',
      bar_status             VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE'
                             CHECK (bar_status IN ('ACTIVE','HALTED','VIOLATION')),
      created_at             TIMESTAMPTZ   NOT NULL DEFAULT NOW()
  );

  CREATE INDEX idx_bar_session    ON atf_behavioral_anchor_records(session_id);
  CREATE INDEX idx_bar_receipt    ON atf_behavioral_anchor_records(governing_receipt_id);
  CREATE INDEX idx_bar_turn       ON atf_behavioral_anchor_records(session_id, turn_index);
  CREATE INDEX idx_bar_status     ON atf_behavioral_anchor_records(bar_status)
                                     WHERE bar_status != 'ACTIVE';""", s))
    st.append(PageBreak())

    # ── SECTION 4 — CCS ───────────────────────────────────────────────────────
    st += [Paragraph('4.  Constraint Conformance Signal (CCS)', s['h1']), rule(s)]
    st.append(Paragraph(
        'The CCS provides a governance-native behavioral conformance measurement for each execution turn. '
        '"Governance-native" means it references the actual Constraint Vector (CV) from the PQC-signed '
        'Governing Receipt -- the receipt IS the measurement specification. This is architecturally distinct '
        'from existing monitoring solutions (Arize, WhyLabs, Evidently) which monitor against separately '
        'configured policy files, creating a receipt-to-policy binding gap.', s['body']))

    st.append(Paragraph('4.1  CCS Score Components and Verdict Ladder', s['h2']))
    st.append(dg(diagram_ccs_score()))
    st.append(Paragraph(
        'Figure 3. CCS score breakdown (left) and verdict ladder (right). Four components sum to 100 points, '
        'normalized to conformance_score in [0.0, 1.0] (BEV-INV-006).',
        s['caption']))
    st.append(sp(10))

    st.append(Paragraph('4.2  Score Formula', s['h2']))
    st.append(cb(
"""  # CCS component formulas (BEV-INV-006 requires all components >= 0)

  OBS (Output Boundary Score, max=40):
    obs_score = max(0.0, 40.0 - 10.0 * boundary_violation_count)
    boundary_violation = output crosses a defined output domain boundary or prohibited class

  CSS (Constraint Satisfaction Score, max=30):
    css_score = max(0.0, 30.0 - 8.0 * constraint_failure_count)
    constraint_failure = explicit constraint in CV.constraints[] evaluated to False

  SDS (Semantic Drift Score, max=20):
    sds_score = max(0.0, 20.0 * (1.0 - drift_magnitude))
    drift_magnitude = cosine_distance(output_embedding, authorized_profile_embedding) in [0, 1]

  AAS (Authority Alignment Score, max=10):
    aas_score = 10.0 if authority_scope_satisfied else 0.0
    authority_scope = capability/resource constraints from governing_receipt_id

  # Aggregation
  ccs_score         = obs_score + css_score + sds_score + aas_score   # range [0, 100]
  conformance_score = ccs_score / 100.0                               # range [0.0, 1.0]
  drift_delta       = 1.0 - conformance_score                         # per-turn drift
  cumulative_drift += drift_delta                                      # session accumulator

  # Verdict assignment (thresholds configurable; defaults shown)
  if   conformance_score >= 0.90: verdict = "CONFORMANT"
  elif conformance_score >= 0.70: verdict = "DRIFTING"     # -> AGVP PVR: MONITORING
  elif conformance_score >= 0.50: verdict = "BREACH"       # -> AGVP PVR: WARNING
  else:                           verdict = "VIOLATION"    # -> HALT PROPAGATION

  if cumulative_drift > CCS_DRIFT_THRESHOLD:              # default 0.35, max 0.50
      verdict = "HALT"                                     # immediate session halt""", s))
    st.append(sp(6))

    st.append(Paragraph('4.3  CCS-AGVP Integration Loop', s['h2']))
    st.append(dg(diagram_agvp_loop()))
    st.append(Paragraph(
        'Figure 4. CCS-AGVP integration. Verdicts DRIFTING, BREACH, and VIOLATION trigger escalating '
        'AGVP responses. VIOLATION and HALT terminate the session before further outputs accumulate.',
        s['caption']))
    st.append(sp(8))

    st.append(Paragraph('4.4  CCS Full Specification', s['h2']))
    st.append(cb(
"""  CCS (Constraint Conformance Signal) -- identifier: CCS-{HEX16}

  COMMITTED FIELDS:
    ccs_id                        : "CCS-7F3A2B1C4D5E6F7A"
    bar_id                        : "BAR-..."             (FK -> BAR of this turn)
    session_id                    : "SESS-..."
    governing_receipt_id          : "ATFDR-..."
    turn_index                    : 3
    conformance_score             : 0.8750               in [0.0, 1.0]
    verdict                       : "DRIFTING"
    output_boundary_score         : 40.00
    constraint_satisfaction_score : 27.50
    semantic_drift_score          : 18.00
    authority_alignment_score     : 2.00
    boundary_violation_count      : 0
    constraint_failure_count      : 1
    drift_magnitude               : 0.100
    cumulative_drift              : 0.215               (session running total)
    drift_delta                   : 0.125               (1.0 - conformance_score)
    watchdog_triggered            : true                 (verdict >= DRIFTING)
    agvp_pvr_id                   : "PVR-..."            (populated if PVR issued)
    halt_triggered                : false
    chain_link_hash               : "9f3a2b..."          (CTCHC link at this turn)
    computed_at_ns                : 1748268000456789012""", s))
    st.append(sp(6))

    st.append(Paragraph('4.5  CCS Invariants: BEV-INV-005-009, BEV-INV-017', s['h2']))
    st.append(tbl(['Invariant', 'Statement', 'Violation Consequence'],
        [['BEV-INV-005', 'BAR and CCS MUST be produced in the same atomic operation. No valid BAR without CCS when CCS_ENABLED.',
          'BAR without CCS fails ATF-BEV-Compliant. AGVP input space incomplete.'],
         ['BEV-INV-006', 'conformance_score in [0.0, 1.0]. drift_delta = 1.0 - conformance_score. All four component scores >= 0.',
          'Score out of bounds = score inflation attack vector. Verdict derived from invalid value is void.'],
         ['BEV-INV-007', 'verdict in {DRIFTING, BREACH, VIOLATION} MUST set watchdog_triggered=true and trigger AGVP PVR.',
          'Incomplete AGVP integration. ATF-BEV-Compliant certification blocked.'],
         ['BEV-INV-008', 'cumulative_drift > CCS_DRIFT_THRESHOLD (default 0.35, max 0.50) MUST set verdict=HALT and halt session.',
          'Session continues with excessive behavioral drift. Integrity failure.'],
         ['BEV-INV-009', 'CCS records are append-only, ordered by turn_index. No UPDATE or DELETE on atf_constraint_conformance_signals.',
          'Retroactive conformance falsification possible. Forensic integrity broken.'],
         ['BEV-INV-017', 'cumulative_drift accumulator is isolated per session_id. On process restart, MUST reload from last persisted CCS.',
          'Cross-session drift contamination. HALT triggered by unrelated session drift.']],
        s, cw=[2.8*cm, 7.5*cm, 5.5*cm]))
    st.append(sp(6))

    st.append(Paragraph('4.6  CCS Database Schema', s['h2']))
    st.append(cb(
"""  -- Table: atf_constraint_conformance_signals  (append-only, BEV-INV-009)
  CREATE TABLE IF NOT EXISTS atf_constraint_conformance_signals (
      ccs_id                         VARCHAR(64)  PRIMARY KEY,    -- CCS-{HEX16}
      bar_id                         VARCHAR(64)  REFERENCES atf_behavioral_anchor_records(bar_id),
      session_id                     VARCHAR(64)  NOT NULL,
      governing_receipt_id           VARCHAR(128) NOT NULL,
      turn_index                     INTEGER      NOT NULL,
      conformance_score              NUMERIC(7,4) NOT NULL
                                     CHECK (conformance_score >= 0.0 AND conformance_score <= 1.0),
      verdict                        VARCHAR(16)  NOT NULL
                                     CHECK (verdict IN ('CONFORMANT','DRIFTING','BREACH','VIOLATION','HALT','NO_DATA')),
      output_boundary_score          NUMERIC(6,3),
      constraint_satisfaction_score  NUMERIC(6,3),
      semantic_drift_score           NUMERIC(6,3),
      authority_alignment_score      NUMERIC(6,3),
      boundary_violation_count       INTEGER      DEFAULT 0,
      constraint_failure_count       INTEGER      DEFAULT 0,
      drift_magnitude                NUMERIC(7,4),
      cumulative_drift               NUMERIC(7,4) NOT NULL,
      drift_delta                    NUMERIC(7,4) NOT NULL,
      watchdog_triggered             BOOLEAN      NOT NULL DEFAULT FALSE,
      agvp_pvr_id                    VARCHAR(64),
      halt_triggered                 BOOLEAN      NOT NULL DEFAULT FALSE,
      chain_link_hash                VARCHAR(64),
      computed_at_ns                 BIGINT       NOT NULL,
      created_at                     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
  );""", s))
    st.append(PageBreak())

    # ── SECTION 5 — CTCHC ─────────────────────────────────────────────────────
    st += [Paragraph('5.  Cross-Turn Coherence Hash Chain (CTCHC)', s['h1']), rule(s)]
    st.append(Paragraph(
        'The CTCHC provides session-level behavioral integrity for multi-turn agent sessions. It chains '
        'every BAR\'s output hash with the prior link and governing receipt ID, seeding from a genesis '
        'hash bound to the session identity. The sealed CTCHC is the Session Integrity Proof (SIP) -- '
        'offline verifiable without any OMNIX infrastructure, resistant to omission, reordering, '
        'substitution, and session-mixing attacks.', s['body']))

    st.append(Paragraph('5.1  CTCHC Chain Architecture', s['h2']))
    st.append(dg(diagram_ctchc()))
    st.append(Paragraph(
        'Figure 5. CTCHC hash chain. Genesis hash binds to session_id and governing_receipt_id. '
        'Each link encodes prior link, turn output hash, and receipt. ML-DSA-65 chain seal = SIP.',
        s['caption']))
    st.append(sp(8))

    st.append(Paragraph('5.2  Chain Construction Algorithm', s['h2']))
    st.append(cb(
"""  # CTCHC construction (BEV-INV-010 through BEV-INV-014, BEV-INV-018)

  # Step 1: Genesis (BEFORE BAR_0 is produced -- BEV-INV-010)
  genesis_hash = hashlib.sha3_256(
      (session_id + '||' + governing_receipt_id + '||' + 'OMNIX-CTCHC-GENESIS').encode()
  ).hexdigest()

  # Step 2: Per-turn link (n >= 0)
  def compute_link(prev_hash, output_text, governing_receipt_id):
      output_hash = hashlib.sha3_256(output_text.encode('utf-8')).hexdigest()
      link_input  = json.dumps(
          {'prev': prev_hash, 'turn': output_hash, 'receipt': governing_receipt_id},
          sort_keys=True                          # deterministic canonical form
      ).encode('utf-8')
      return hashlib.sha3_256(link_input).hexdigest()

  link[0] = compute_link(genesis_hash, output_0, governing_receipt_id)
  link[n] = compute_link(link[n-1],   output_n, governing_receipt_id)

  # Step 3: Chain seal at session close (all N links must be present -- BEV-INV-012)
  all_links_concat = ''.join(all_link_hashes)          # ordered by turn_index
  seal_hash = hashlib.sha3_256(
      (genesis_hash + all_links_concat + link[N-1]).encode()
  ).hexdigest()

  # Step 4: ML-DSA-65 seal (BEV-INV-014)
  ctchc_seal = base64.b64encode(
      dilithium3.sign(seal_hash.encode('utf-8'), platform_secret_key)
  ).decode('utf-8')

  # BEV-INV-018: every link MUST carry same governing_receipt_id as genesis
  assert all(link.governing_receipt_id == genesis_receipt_id for link in all_links)""", s))
    st.append(sp(6))

    st.append(Paragraph('5.3  Offline Verification Procedure (6 steps)', s['h2']))
    st.append(cb(
"""  CTCHC OFFLINE VERIFICATION PROCEDURE (BEV-INV-012 + BEV-INV-013 + BEV-INV-014):

  Input: ctchc.json, bar_list.json (ordered by turn_index), public_key.pem

  Step 1 -- Verify CTCHC seal integrity
    hash_check = sha3_256((ctchc.genesis_hash + all_link_hashes_concat + ctchc.final_chain_hash).encode())
    assert hash_check == ctchc.seal_hash                            # BEV-INV-013
    verify ML-DSA-65(ctchc.ctchc_seal, ctchc.seal_hash, pubkey)    # BEV-INV-014

  Step 2 -- Verify turn completeness (BEV-INV-012)
    assert {bar.turn_index for bar in bar_list} == set(range(len(bar_list)))
    assert len(bar_list) == ctchc.turn_count
    # Gaps in turn_index -> CTCHC_VERIFICATION_FAILED (omission attack detected)

  Step 3 -- Verify each BAR individually
    for bar in bar_list:
        hash_check = sha3_256((bar.output_hash + bar.governing_receipt_id + str(bar.turn_index)).encode())
        assert hash_check == bar.content_hash
        verify ML-DSA-65(bar.pqc_signature, bar.content_hash, pubkey)

  Step 4 -- Verify genesis hash
    expected_genesis = sha3_256((session_id + '||' + governing_receipt_id + '||' + 'OMNIX-CTCHC-GENESIS').encode())
    assert expected_genesis == ctchc.genesis_hash
    # Mismatch -> session identity tampered

  Step 5 -- Reconstruct all chain links
    prev = ctchc.genesis_hash
    for bar in bar_list (ordered by turn_index):
        expected_link = sha3_256(json.dumps({'prev':prev,'turn':bar.output_hash,'receipt':governing_receipt_id},sort_keys=True).encode())
        assert expected_link == bar.chain_link              # BEV-INV-011 + BEV-INV-018
        prev = expected_link
    assert prev == ctchc.final_chain_hash
    # Mismatch -> substitution or reordering attack detected

  Step 6 -- Report
    return "VERIFIED" if all assertions passed else "NOT_VERIFIED: Step N failed [details]" """, s))
    st.append(sp(6))

    st.append(Paragraph('5.4  CTCHC Full Specification', s['h2']))
    st.append(cb(
"""  CTCHC (Cross-Turn Coherence Hash Chain) -- identifier: CTCHC-{HEX16}

  COMMITTED FIELDS:
    ctchc_id               : "CTCHC-9F3A2B1C4D5E6F7A"
    session_id             : "SESS-..."         (UNIQUE -- one CTCHC per session)
    governing_receipt_id   : "ATFDR-..."
    genesis_hash           : "a3f2b1..."        (SHA3-256 of session+receipt+GENESIS)
    final_chain_hash       : "c9d8e7..."        (link[N-1], updated per turn)
    turn_count             : 7
    all_bar_ids            : ["BAR-...", "BAR-...", ...]  (ordered by turn_index)
    session_start_ns       : 1748268000000000000
    session_close_ns       : 1748268120000000000
    session_status         : "COMPLETED" | "ACTIVE" | "HALTED" | "ABANDONED"
    failure_turn_index     : null | 4           (if halted)
    failure_reason         : null | "BEV-INV-003: bar_status=HALTED"

  SEAL FIELDS:
    seal_hash              : SHA3-256(genesis || all_links_concat || final_chain_hash)
    ctchc_seal             : base64(ML-DSA-65.sign(seal_hash))
    pqc_algorithm          : "ML-DSA-65"
    chain_sealed           : true
    atf_spec_version       : "RFC-ATF-6_v1.0"
    created_at             : TIMESTAMPTZ""", s))
    st.append(sp(6))

    st.append(Paragraph('5.5  CTCHC Invariants: BEV-INV-010-014, BEV-INV-018', s['h2']))
    st.append(tbl(['Invariant', 'Statement', 'Violation Consequence'],
        [['BEV-INV-010', 'CTCHC genesis MUST be created before BAR_0. genesis = SHA3-256(session_id||"||"||receipt_id||"||"||"OMNIX-CTCHC-GENESIS").',
          'Chain cannot be reconstructed. Session has no integrity anchor.'],
         ['BEV-INV-011', 'link[n] = SHA3-256(json.dumps({prev, turn, receipt}, sort_keys=True)). Deterministic canonical form required.',
          'Turn reordering, omission, substitution undetectable. SIP invalid.'],
         ['BEV-INV-012', 'Verification MUST fail if any turn_index in [0, N-1] is absent. N turns claimed, N-1 links = REJECTED.',
          'Partial session presented as complete. Forensic attribution incomplete.'],
         ['BEV-INV-013', 'seal_hash = SHA3-256(genesis || all_link_hashes || tip_hash). Seal covers complete chain.',
          'Partial seal accepted as complete. Tail turns unprotected.'],
         ['BEV-INV-014', 'CTCHC seal MUST be ML-DSA-65 signed before OEP export or regulatory submission.',
          'Session Integrity Proof not post-quantum secure. Regulatory submission blocked.'],
         ['BEV-INV-018', 'Every chain link MUST carry same governing_receipt_id as CTCHC genesis. Prevents cross-session splicing.',
          'Cross-session link splicing undetectable without chain recomputation.']],
        s, cw=[2.8*cm, 7.5*cm, 5.5*cm]))
    st.append(sp(6))

    st.append(Paragraph('5.6  CTCHC Database Schema', s['h2']))
    st.append(cb(
"""  -- Table: atf_coherence_hash_chains  (one row per session)
  CREATE TABLE IF NOT EXISTS atf_coherence_hash_chains (
      ctchc_id               VARCHAR(64)  PRIMARY KEY,    -- CTCHC-{HEX16}
      session_id             VARCHAR(64)  UNIQUE NOT NULL,
      governing_receipt_id   VARCHAR(128) NOT NULL,
      genesis_hash           VARCHAR(64)  NOT NULL,
      final_chain_hash       VARCHAR(64),
      turn_count             INTEGER      NOT NULL DEFAULT 0,
      all_bar_ids            JSONB,
      session_start_ns       BIGINT,
      session_close_ns       BIGINT,
      session_status         VARCHAR(32)  NOT NULL DEFAULT 'ACTIVE'
                             CHECK (session_status IN ('ACTIVE','COMPLETED','HALTED','ABANDONED')),
      failure_turn_index     INTEGER,
      failure_reason         TEXT,
      seal_hash              VARCHAR(64),
      ctchc_seal             TEXT,
      pqc_algorithm          VARCHAR(16)  NOT NULL DEFAULT 'ML-DSA-65',
      chain_sealed           BOOLEAN      NOT NULL DEFAULT FALSE,
      atf_spec_version       VARCHAR(8)   NOT NULL DEFAULT '1.6',
      created_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW()
  );""", s))
    st.append(PageBreak())

    # ── SECTION 6 — BEV COMPOSITION ───────────────────────────────────────────
    st += [Paragraph('6.  BEV Layer Composition', s['h1']), rule(s)]

    st.append(Paragraph('6.1  Per-Turn Execution Timeline', s['h2']))
    st.append(dg(diagram_bev_timeline()))
    st.append(Paragraph(
        'Figure 6. BEV per-turn execution timeline. Steps 1-8 mandatory for every turn (BEV-INV-001). '
        'Step 9 conditional on verdict (BEV-INV-007).',
        s['caption']))
    st.append(sp(8))

    st.append(Paragraph('6.2  Three-Gap Closure', s['h2']))
    st.append(dg(diagram_three_gaps()))
    st.append(Paragraph(
        'Figure 7. BEV closes the three structural behavioral governance gaps: BAR closes Gap_BAG, '
        'CCS closes Gap_COP, and CTCHC closes Gap_MCP.',
        s['caption']))
    st.append(sp(8))

    st.append(Paragraph('6.3  Cross-Layer Integration Points', s['h2']))
    st.append(tbl(['BEV component', 'Integrates with', 'RFC', 'Integration mechanism'],
        [['BAR', 'Governing Receipt (L1-L2)', 'RFC-ATF-1', 'governing_receipt_id in every BAR; queryable from any ATF receipt'],
         ['CCS', 'AGVP Watchdog (L4)', 'RFC-ATF-4', 'DRIFTING/BREACH/VIOLATION -> PVR issuance via AGVP watchdog'],
         ['CTCHC', 'OEP Forensic Package (L3)', 'RFC-ATF-3', 'CTCHC + BAR records included in OEP packages as SIP artifact'],
         ['BAR', 'TCS Temporal Context (L5)', 'RFC-ATF-5', 'bar_timestamp_ns anchors to TCS for 7yr EU AI Act Art.72 retention'],
         ['CCS', 'RAR Regulatory Projection (L5)', 'RFC-ATF-5', 'conformance history included in RAR field_projections for future review'],
         ['CTCHC', 'GUGT Universal Invariant (L5)', 'RFC-ATF-5', 'SIP provides evidence for UGI-002 (offline-verifiable decision evidence)']],
        s, cw=[3.0*cm, 4.0*cm, 2.5*cm, 7.3*cm]))
    st.append(sp(8))

    st.append(Paragraph('6.4  Session Close Protocol', s['h2']))
    st.append(cb(
"""  BEV SESSION CLOSE PROTOCOL (triggered on session end, HALT, or ABANDONED):

  Step 11: Assert all turn_indices [0, N-1] present in BAR set (BEV-INV-012)
  Step 12: Compute seal_hash = SHA3-256(genesis || all_links_concat || final_link)
  Step 13: ctchc_seal = ML-DSA-65.sign(seal_hash)                   (BEV-INV-014)
  Step 14: Update CTCHC record: chain_sealed=true, seal_hash, ctchc_seal
  Step 15: Compute session_summary: bar_count, ccs_min, ccs_max, final_cumulative_drift
  Step 16: If session was HALTED: record failure_turn_index + failure_reason
  Step 17: Archive to OEP package if evidence lifecycle = HOT -> WARM threshold reached

  CTCHC at close is the Session Integrity Proof (SIP):
    Offline verifiable by any party holding: {ctchc.json, all_bars.json, public_key.pem}
    No platform access required.  No API credentials required.  No network access required.""", s))
    st.append(PageBreak())

    # ── SECTION 7 — FORMAL VERIFICATION ───────────────────────────────────────
    st += [Paragraph('7.  Formal Verification (OMNIX-FVS-1.0 Extension)', s['h1']), rule(s)]
    st.append(Paragraph(
        'RFC-ATF-6 extends the OMNIX Formal Verification Suite (FVS-1.0) defined in RFC-ATF-4. '
        'RFC-ATF-6 maintains the dual methodology: Z3 SMT for arithmetic and structural invariants, '
        'TLA+ for state-machine safety and liveness. This is the only AI governance standard with '
        'machine-checkable formal proofs across both methodologies for behavioral execution verification.', s['body']))

    st.append(Paragraph('7.1  Z3 SMT Proof Targets', s['h2']))
    st.append(tbl(['Target ID', 'Module', 'Property Proven', 'Z3 Result'],
        [['BEV-FVS-001', 'BAR', 'content_hash uniquely bound to (output_hash, receipt_id, turn_index) triplet', 'UNSAT'],
         ['BEV-FVS-002', 'BAR', 'SHA3-256 structural uniqueness -- no two distinct inputs produce same content_hash', 'structural'],
         ['BEV-FVS-003', 'CCS', 'conformance_score in [0.0, 1.0] for all valid component inputs', 'UNSAT'],
         ['BEV-FVS-004', 'CCS', 'All four CCS components are non-negative for all valid inputs', 'UNSAT'],
         ['BEV-FVS-005', 'CTCHC', 'Chain monotonicity: link[n] cryptographically depends on link[n-1]', 'structural'],
         ['BEV-FVS-006', 'CCS', 'drift_delta = 1.0 - conformance_score is always non-negative', 'UNSAT'],
         ['BEV-FVS-007', 'CCS', 'cumulative_drift is monotonically non-decreasing across turns', 'UNSAT'],
         ['BEV-FVS-008', 'CTCHC', 'Missing turn_index in [0, N-1] causes verification = FAIL (gap attack)', 'UNSAT'],
         ['BEV-FVS-009', 'BAR', 'BAR-HALT immediately disables subsequent turns (session state machine)', 'UNSAT'],
         ['ATF-INV-001-BEV-EXT', 'Inherited', 'MAR invariant preserved under all BEV operations', 'UNSAT']],
        s, cw=[4.0*cm, 2.0*cm, 8.2*cm, 1.8*cm]))
    st.append(sp(6))

    st.append(Paragraph('7.2  BEV-FVS-003 -- CCS Score Bounds (Z3 proof)', s['h2']))
    st.append(cb(
"""  from z3 import Real, Or, Solver, And, unsat

  obs, css, sds, aas = [Real(x) for x in ['obs', 'css', 'sds', 'aas']]
  solver = Solver()

  # BEV-INV-006 component constraints
  solver.add(obs >= 0, obs <= 40)   # max(0, 40 - 10*violations) always in [0, 40]
  solver.add(css >= 0, css <= 30)   # max(0, 30 - 8*failures) always in [0, 30]
  solver.add(sds >= 0, sds <= 20)   # max(0, 20*(1-drift)) always in [0, 20]
  solver.add(And(Or(aas == 0, aas == 10)))  # binary authority check

  ccs_score = obs + css + sds + aas  # range: [0, 100]

  # Claim: ccs_score/100 is ALWAYS in [0.0, 1.0]
  # Try to find a violation:
  solver.add(Or(ccs_score < 0, ccs_score > 100))
  assert solver.check() == unsat   # No violation exists -- BEV-INV-006 holds
  print("BEV-FVS-003: UNSAT -- conformance_score in [0.0, 1.0] is guaranteed")""", s))
    st.append(sp(6))

    st.append(Paragraph('7.3  TLA+ Coverage', s['h2']))
    st.append(tbl(['TLA+ Specification', 'Property Type', 'Coverage', 'Status'],
        [['BEV_BAR.tla -- BAR_BEFORE_OUTPUT', 'Safety', 'BAR persisted before output delivery in all valid state transitions', 'PASS'],
         ['BEV_BAR.tla -- HALT_PROPAGATES', 'Safety', 'HALTED BAR causes session state = HALTED in all reachable states', 'PASS'],
         ['BEV_CCS.tla -- CCS_ATOMIC', 'Safety', 'CCS and BAR produced atomically -- no intermediate state with BAR but no CCS', 'PASS'],
         ['BEV_CCS.tla -- AGVP_TRIGGERED', 'Safety', 'AGVP watchdog_triggered=true in all states with verdict in {DRIFTING,BREACH,VIOLATION}', 'PASS'],
         ['BEV_CCS.tla -- DRIFT_MONOTONE', 'Safety', 'cumulative_drift is monotonically non-decreasing across all turn transitions', 'PASS'],
         ['BEV_CTCHC.tla -- CHAIN_INIT_FIRST', 'Safety', 'genesis_hash set before first BAR in all valid session initialization sequences', 'PASS'],
         ['BEV_CTCHC.tla -- SEAL_COMPLETENESS', 'Safety', 'chain_sealed=true only reachable when all turn_indices [0,N-1] present', 'PASS'],
         ['BEV_INTEGRATION.tla -- BEV_NON_BLOCKING', 'Safety', 'CCS/CTCHC failure does not block primary record issuance (BAR-fail only)', 'PASS']],
        s, cw=[5.5*cm, 2.5*cm, 5.5*cm, 1.8*cm]))
    st.append(Paragraph(
        'Run all proofs: <b>python omnix_core/formal_verification/run_bev_proofs.py</b>', s['gold']))
    st.append(PageBreak())

    # ── SECTION 8 — INVARIANT SUMMARY ─────────────────────────────────────────
    st += [Paragraph('8.  Combined Invariant Summary -- 106 Total', s['h1']), rule(s)]
    st.append(Paragraph(
        'RFC-ATF-6 introduces 18 new invariants across three protocol families. Combined with the '
        '88 invariants from RFC-ATF-1 through RFC-ATF-5, the complete ATF stack encompasses '
        '<b>106 formally specified invariants</b> across 20 protocol families.', s['body']))
    st.append(tbl(['Family', 'RFC', 'Count', 'Scope'],
        [['ATF-INV',  'RFC-ATF-1', '6',  'Identity & Delegation -- MAR, Acyclicity, Chain Root, Immutability, Non-Future-Dating, Offline Verifiability'],
         ['RGC-INV',  'RFC-ATF-2', '8',  'Runtime Continuity -- CES, AFG, HALT propagation, RC, RCR integrity'],
         ['GPIL-INV', 'RFC-ATF-3', '3',  'Governance Policy Interoperability Layer'],
         ['ELR-INV',  'RFC-ATF-3', '4',  'Evidence Lifecycle Record management'],
         ['EAP-INV',  'RFC-ATF-3', '7',  'Evidence Archive Pipeline'],
         ['OEP-INV',  'RFC-ATF-3', '6',  'OMNIX Evidence Package -- two-phase PQC seal, offline verification'],
         ['FEA-INV',  'RFC-ATF-3', '5',  'Forensic Export Authorization'],
         ['FVP-INV',  'RFC-ATF-3', '1',  'Forensic Verification Protocol'],
         ['GECR-INV', 'RFC-ATF-3', '6',  'Governance Execution Context Record'],
         ['SGIP-INV', 'RFC-ATF-3', '4',  'Semantic Governance Interoperability Protocol'],
         ['DSPP-INV', 'RFC-ATF-4', '7',  'Dynamic Semantic Portability Protocol -- TSA, SDR, RSA'],
         ['AGV-INV',  'RFC-ATF-4', '6',  'Anticipatory Governance Veto Protocol -- PVR'],
         ['SSD-INV',  'RFC-ATF-4', '3',  'Structural Shift Detection -- CRSI'],
         ['FVS-INV',  'RFC-ATF-4', '3',  'Formal Verification Suite extension'],
         ['CGE-INV',  'RFC-ATF-5', '7',  'Counterfactual Governance Engine'],
         ['GUGT-INV', 'RFC-ATF-5', '6',  'Grand Unified Governance Theory -- UGI-001-006'],
         ['TGB-INV',  'RFC-ATF-5', '5',  'Temporal Governance Bridge -- TCS, RAR, TMR'],
         ['BEV-INV',  'RFC-ATF-6', '18', 'Behavioral Execution Verification: BAR(001-004,015-016) + CCS(005-009,017) + CTCHC(010-014,018)  [NEW]'],
         ['TOTAL', '--', '106', 'Complete ATF Protocol Stack -- six RFCs -- 20 protocol families']],
        s, cw=[2.8*cm, 2.2*cm, 1.5*cm, 10.3*cm]))
    st.append(PageBreak())

    # ── SECTION 9 — COMPLIANCE DESIGNATION ───────────────────────────────────
    st += [Paragraph('9.  ATF-BEV-Compliant Designation', s['h1']), rule(s)]
    st.append(dg(diagram_compliance()))
    st.append(Paragraph(
        'Figure 8. ATF compliance hierarchy. ATF-BEV-Compliant (gold) is the sixth and highest tier.',
        s['caption']))
    st.append(sp(8))
    st.append(cb(
"""  ATF COMPLIANCE HIERARCHY (six tiers, strictly hierarchical):

  +------------------------------------------------------------------+
  | * ATF-BEV-Compliant  (RFC-ATF-1+2+3+4+5+6)  106 inv  HIGHEST  |
  |   BAR + CCS + CTCHC operational; BEV formal verification passing |
  +------------------------------------------------------------------+
        ^--- extends without replacing
  +------------------------------------------------------------------+
  |   ATF-CGL-Compliant  (RFC-ATF-1+2+3+4+5)     88 inv             |
  |   CGE + GUGT UIR + TGB operational                               |
  +------------------------------------------------------------------+
        ^--- extends without replacing
  +------------------------------------------------------------------+
  |   ATF-PGL-Compliant  (RFC-ATF-1+2+3+4)        70 inv             |
  |   AGVP + SSD + DSPP operational                                  |
  +------------------------------------------------------------------+
        ^--- extends without replacing
  +------------------------------------------------------------------+
  |   ATF-FEI-Compliant  (RFC-ATF-1+2+3)          40 inv             |
  |   OEP + GPIL + Forensic verification operational                 |
  +------------------------------------------------------------------+
        ^--- extends without replacing
  +------------------------------------------------------------------+
  |   ATF-RGC-Compliant  (RFC-ATF-1+2)            14 inv             |
  |   Runtime continuity + HALT propagation operational              |
  +------------------------------------------------------------------+
        ^--- extends without replacing
  +------------------------------------------------------------------+
  |   ATF-Compliant-L1/2/3 (RFC-ATF-1)             6 inv             |
  |   Identity + Delegation + Trust Lattice operational              |
  +------------------------------------------------------------------+

  ATF-BEV-Compliant requirements (all six required simultaneously):
  (a) ATF-CGL-Compliant: all RFC-ATF-1/2/3/4/5 requirements satisfied
  (b) BAR operational: BEV_ENABLED=true, all turns produce persisted BARs;
      BEV-INV-001-004, 015-016 all satisfied; output delivery blocked without BAR
  (c) CCS operational: CCS_ENABLED=true, AGVP integration active for DRIFTING+;
      BEV-INV-005-009, 017 all satisfied; drift accumulator isolated per session
  (d) CTCHC operational: CTCHC_ENABLED=true, all completed sessions sealed with SIP;
      BEV-INV-010-014, 018 all satisfied; offline verification procedure tested
  (e) BEV formal verification: run_bev_proofs.py -- all 9 Z3 targets UNSAT/structural;
      all 8 TLA+ checks PASS; FVS runner output archived as compliance evidence""", s))
    st.append(PageBreak())

    # ── SECTION 10 — IMPLEMENTATION REFERENCE ────────────────────────────────
    st += [Paragraph('10.  Implementation Reference', s['h1']), rule(s)]
    st.append(Paragraph('10.1  Reference Implementation Components', s['h2']))
    st.append(tbl(['Component', 'Role', 'Public Interface'],
        [['BAR Engine', 'Per-turn BAR production, content_hash, ML-DSA-65 signing, DB persist, BEV-INV-001-004 enforcement', '/api/atf/bev/bar/{session_id}/{turn_index}'],
         ['CCS Engine', 'CCS computation, 4-component scoring, verdict assignment, AGVP notification, BEV-INV-005-009,017', '/api/atf/bev/ccs/{session_id}/{turn_index}'],
         ['CTCHC Manager', 'Genesis init, per-turn link computation, session close sealing, SIP production, BEV-INV-010-014,018', '/api/atf/bev/ctchc/{session_id}'],
         ['BEV Session', 'Orchestrates BAR+CCS+CTCHC atomically per turn; enforces sequencing; manages session state machine', '/api/atf/bev/session/{session_id}/turn'],
         ['BAR Verifier', 'Offline BAR content_hash + ML-DSA-65 verification; no platform access required', 'python omnix_atf_verify.py --bar bar.json'],
         ['CTCHC Verifier', 'Offline 6-step SIP verification: completeness, links, genesis, seal; detects all 4 attacks', 'python omnix_atf_verify.py --ctchc ctchc.json --bars bars.json'],
         ['CCS Replayer', 'Offline CCS score recomputation from BAR payload + constraint vector', 'python omnix_bev_replay.py --bars bars.json --cv cv.json'],
         ['BEV DB Manager', '3 new tables + 4 indexes; append-only triggers; FK integrity; auto-created on first request', 'Auto-created via CREATE TABLE IF NOT EXISTS']],
        s, cw=[3.5*cm, 7.2*cm, 6.1*cm]))
    st.append(sp(6))

    st.append(Paragraph('10.2  API Endpoints', s['h2']))
    st.append(tbl(['Endpoint', 'Method', 'Description', 'Auth'],
        [['/api/atf/bev/session/start',          'POST', 'Initialize BEV session: create CTCHC genesis, return session_id + ctchc_id', 'B2B API key'],
         ['/api/atf/bev/session/{sid}/turn',     'POST', 'Execute turn: produce BAR+CCS atomically, advance CTCHC, return bar_id', 'B2B API key'],
         ['/api/atf/bev/session/{sid}/close',    'POST', 'Close session: seal CTCHC, produce SIP, return ctchc_id + seal_hash', 'B2B API key'],
         ['/api/atf/bev/bar/{bar_id}',           'GET',  'Retrieve single BAR by ID', 'B2B API key'],
         ['/api/atf/bev/session/{sid}/bars',     'GET',  'Retrieve all BARs for session (ordered by turn_index)', 'B2B API key'],
         ['/api/atf/bev/ctchc/{session_id}',     'GET',  'Retrieve CTCHC for session (includes seal when closed)', 'B2B API key'],
         ['/api/atf/bev/ctchc/{sid}/verify',     'POST', 'Online CTCHC verification (offline CLI also available)', 'B2B API key'],
         ['/api/atf/bev/session/{sid}/ccs',      'GET',  'Retrieve CCS history for session (ordered by turn_index)', 'B2B API key'],
         ['/api/atf/bev/session/{sid}/sip',      'GET',  'Export Session Integrity Proof bundle: ctchc + all_bars + public_key', 'B2B API key']],
        s, cw=[6.0*cm, 1.8*cm, 7.0*cm, 2.0*cm]))
    st.append(sp(6))

    st.append(Paragraph('10.3  Configuration Parameters', s['h2']))
    st.append(tbl(['Parameter', 'Default', 'Range', 'Description'],
        [['BEV_ENABLED',           'false', 'true/false',   'Master switch: enables BAR+CCS+CTCHC per turn'],
         ['CCS_ENABLED',           'true',  'true/false',   'CCS computation per BAR (requires BEV_ENABLED)'],
         ['CTCHC_ENABLED',         'true',  'true/false',   'Hash chain per session (requires BEV_ENABLED)'],
         ['CCS_DRIFT_THRESHOLD',   '0.35',  '0.05-0.50',    'Cumulative drift threshold triggering HALT verdict'],
         ['BAR_OUTPUT_MODE',       'HASHED','FULL/HASHED/REDACTED', 'Output payload storage mode (BEV-INV-002)'],
         ['CCS_VERDICT_THRESHOLDS','90/70/50','configurable','CONFORMANT/DRIFTING/BREACH/VIOLATION score thresholds'],
         ['BEV_AGVP_INTEGRATION',  'true',  'true/false',   'CCS verdict triggers AGVP PVR issuance (BEV-INV-007)'],
         ['BEV_ASYNC_TIMEOUT_S',   '10',    '1-120',        'Timeout for async CCS/CTCHC operations'],
         ['CTCHC_SEAL_ON_HALT',    'true',  'true/false',   'Seal CTCHC even on HALT (partial SIP)'],
         ['BEV_OEP_AUTO_INCLUDE',  'true',  'true/false',   'Auto-include BAR+CTCHC in OEP packages (RFC-ATF-3)']],
        s, cw=[4.5*cm, 2.5*cm, 3.5*cm, 6.3*cm]))
    st.append(PageBreak())

    # ── SECTION 11 — SECURITY ─────────────────────────────────────────────────
    st += [Paragraph('11.  Security Considerations', s['h1']), rule(s)]
    st.append(tbl(['Threat', 'Attack Vector', 'BEV Mitigation', 'Residual Risk'],
        [['BAR Omission (BEV-T-001)', 'Adversary presents subset of BARs, omitting turns with violations', 'CTCHC: missing turn_index in [0,N-1] -> verification=FAIL (BEV-INV-012)', 'NONE -- structural guarantee'],
         ['Output Substitution (BEV-T-002)', 'Replace BAR_i output_hash with hash from compliant session', 'CTCHC link[n] includes turn output_hash -- substituted hash breaks chain (BEV-INV-011)', 'NONE -- SHA3-256 preimage resistance'],
         ['Turn Reordering (BEV-T-003)', 'Present BARs in different order to hide violation sequence', 'chain_link = SHA3-256({prev, turn, receipt}) -- order-dependent; reordering breaks chain', 'NONE -- structural'],
         ['Session Mixing (BEV-T-004)', 'Interleave BARs from compliant session with non-compliant session', 'BEV-INV-018: link.governing_receipt_id must match genesis -- cross-session links rejected', 'NONE -- receipt binding'],
         ['CCS Score Inflation (BEV-T-005)', 'Override conformance_score to CONFORMANT without computing', 'BEV-INV-006: Z3 proof BEV-FVS-003 proves score in [0,1]; component constraints Z3-proved', 'LOW -- requires signing key compromise'],
         ['CTCHC Partial Seal (BEV-T-006)', 'Seal chain over N-1 links, claim turn_count = N', 'BEV-INV-013: seal_hash includes all_links_concat -- partial seal produces wrong hash', 'NONE -- SHA3-256 collision resistance'],
         ['BAR Replay Attack (BEV-T-007)', 'Reuse valid BAR from prior session in new session context', 'governing_receipt_id + session_id in content_hash bind BAR to specific session+receipt', 'NONE -- context binding'],
         ['PQC Key Compromise (BEV-T-008)', 'Attacker compromises ML-DSA-65 signing key; forges BAR signatures', 'Key rotation via platform secret key management; prior BARs remain verifiable with original key', 'LOW -- requires key management breach'],
         ['Conformance Drift Concealment (BEV-T-009)', 'Reset cumulative_drift by creating new session to avoid HALT', 'Each session has independent drift accumulator (BEV-INV-017); cross-session pattern detection via AGVP', 'LOW -- AGVP cross-session monitoring'],
         ['Empty Output Bypass (BEV-T-010)', 'Submit empty output_text to produce trivially compliant BAR', 'BEV-INV-015: empty/whitespace output_text -> bar_status=VIOLATION; session halted', 'NONE -- explicit check']],
        s, cw=[3.5*cm, 4.0*cm, 4.5*cm, 3.8*cm]))
    st.append(PageBreak())

    # ── SECTION 12 — NOVEL CONTRIBUTIONS ─────────────────────────────────────
    st += [Paragraph('12.  Novel Contributions', s['h1']), rule(s)]
    for i, (title, detail) in enumerate([
        ('Behavioral Anchor Record (BAR) with PQC Seal',
         'First governance artifact that cryptographically binds an AI agent\'s actual output to the '
         'governing receipt that authorized it, via a three-input SHA3-256 binding '
         '(output_hash || receipt_id || turn_index) signed with ML-DSA-65. Existing output logging '
         'systems (SageMaker Model Monitor, Azure AI Studio) capture outputs but do not bind them '
         'cryptographically to the specific authorization record. The BAR closes this binding gap.'),
        ('Constraint Conformance Signal (CCS) -- Governance-Native Behavioral Metric',
         'First behavioral conformance signal that references the actual Constraint Vector from a '
         'PQC-signed Governing Receipt as its measurement specification. Existing monitoring solutions '
         '(Arize Phoenix, WhyLabs, Evidently AI) monitor against separately configured policy files, '
         'creating a receipt-to-policy binding gap. CCS uses the receipt itself as the CV -- the '
         'authorization IS the measurement specification.'),
        ('CCS-AGVP Behavioral Integration Loop',
         'First integration of behavioral output conformance signals into a proactive veto protocol. '
         'RFC-ATF-4 AGVP covered structural (CES, fragmentation) and semantic (DSPP) signals. CCS '
         'completes the AGVP input space by adding behavioral conformance to the watchdog input stream. '
         'This enables anticipatory vetoes based on behavioral trajectory, not just structural health.'),
        ('Cross-Turn Coherence Hash Chain (CTCHC) -- Session Integrity Proof',
         'First session-level hash chain for multi-turn AI agent governance, seeded by the governing '
         'receipt ID and sealed with ML-DSA-65 as a Session Integrity Proof (SIP). Audit log hash '
         'chains exist in distributed systems; the architectural innovation is their linkage to '
         'governance receipts, enabling forensic verification of complete multi-turn behavioral '
         'sessions against their authorization records.'),
        ('Offline-Verifiable Session Integrity Proof (SIP)',
         'The CTCHC chain seal is the first AI governance artifact that proves the completeness, '
         'ordering, and receipt-binding of an entire multi-turn session, verifiable offline without '
         'network access or platform credentials. The 6-step verification procedure detects all four '
         'session manipulation attacks (omission, reordering, substitution, session-mixing).'),
        ('ATF-BEV-Compliant -- Six-Tier Formally Verified Compliance Hierarchy',
         'First six-tier AI governance compliance designation backed by 106 formally specified '
         'invariants across 20 protocol families, dual formal verification (Z3 + TLA+), and '
         'post-quantum cryptography. The BEV tier completes the ATF stack from identity through '
         'behavioral execution, closing all six identified gaps across the governance lifecycle.'),
    ], start=1):
        st.append(KeepTogether([
            Paragraph(f'{i}.  {title}', s['h3']),
            Paragraph(detail, s['body']),
            sp(4),
        ]))
    st.append(PageBreak())

    # ── SECTION 13 — PRIOR ART ────────────────────────────────────────────────
    st += [Paragraph('13.  Distinction from Prior Art', s['h1']), rule(s)]
    st.append(tbl(['Feature', 'RFC-ATF-6 (BEV)', 'Arize / WhyLabs', 'SageMaker Monitor', 'Azure AI Studio', 'NIST AI RMF'],
        [['Per-turn PQC-signed behavioral record (BAR)',         '[OK] ML-DSA-65 per turn',     '[NO]', '[NO]', '[NO]', '[NO]'],
         ['Binding to specific authorization receipt',          '[OK] content_hash triplet',    '[NO]', '[NO]', '[NO]', '[NO]'],
         ['Governance-native CCS (CV from signed receipt)',     '[OK] BEV-INV-005',             '[NO] -- separate policy', '[NO]', '[NO]', '[NO]'],
         ['AGVP behavioral integration (PVR for drift)',        '[OK] BEV-INV-007',             '[NO]', '[NO]', '[NO]', '[NO]'],
         ['Cross-turn session hash chain (CTCHC)',              '[OK] genesis + per-turn links','[NO]', '[NO]', '[NO]', '[NO]'],
         ['Offline-verifiable Session Integrity Proof (SIP)',   '[OK] 6-step procedure',        '[NO]', '[NO]', '[NO]', '[NO]'],
         ['Omission / reordering attack detection',            '[OK] CTCHC structure',         '[NO]', '[NO]', '[NO]', '[NO]'],
         ['Z3 + TLA+ formal proofs for behavioral invariants', '[OK] 9 Z3 + 8 TLA+',          '[NO]', '[NO]', '[NO]', '[NO]'],
         ['Post-quantum cryptography (ML-DSA-65)',             '[OK] FIPS 204',                '[NO]', '[NO]', '[NO]', '[NO]'],
         ['Offline full-chain verification (no platform)',     '[OK] CLI + JSON only',         '[NO]', '[NO]', '[NO]', '[NO]'],
         ['6-tier compliance hierarchy (106 invariants)',      '[OK] ATF-BEV-Compliant',       '[NO]', '[NO]', '[NO]', 'Partial']],
        s, cw=[5.0*cm, 3.5*cm, 2.5*cm, 2.8*cm, 2.5*cm, 1.5*cm]))
    st.append(PageBreak())

    # ── SECTION 14 — REGULATORY ALIGNMENT ────────────────────────────────────
    st += [Paragraph('14.  Regulatory Alignment', s['h1']), rule(s)]
    st.append(tbl(['Framework / Article', 'BAR Contribution', 'CCS Contribution', 'CTCHC Contribution'],
        [['EU AI Act Art. 9 -- Risk Management', 'Per-turn output attestation binds execution to risk management receipt', 'Continuous monitoring within governance-specified boundaries (Art.9(7))', 'Session-level integrity proof for risk management documentation'],
         ['EU AI Act Art. 12 -- Record-Keeping', 'Append-only per-turn behavioral record for mandatory technical file', 'Conformance history projection for multi-year record review', 'Complete session audit trail -- no gaps possible'],
         ['EU AI Act Art. 14 -- Human Oversight', 'Auditable output record enables human review of actual outputs', 'CCS verdict provides quantitative signal for human review trigger', 'Session coherence evidence for oversight reporting'],
         ['EU AI Act Art. 72 -- 7yr Retention', 'BAR records included in HOT/WARM/COLD lifecycle (TGB TMR)', 'CCS history archived with TCS for temporal projection via RAR', 'SIP preserved across evidence lifecycle transitions'],
         ['NIST AI RMF MEASURE 2.6 -- Monitoring', 'Attestation of actual outputs per authorized action', 'Governance-native monitoring signal bound to receipt specification', 'Session coherence evidence for MEASURE 2.6 documentation'],
         ['ISO/IEC 42001 Sec.8.4 -- Operations', 'Operational output record per Sec.8.4 controls', 'CCS is operational conformance measurement artifact', 'Turn-by-turn operational control record'],
         ['MiFID II Art. 17 -- Algo Trading', 'Pre/post-output record for algorithmic trading actions', 'Conformance signal for trading output domain verification', 'Multi-turn session integrity for trading session audit'],
         ['SOC 2 Type II CC7.2 -- Monitoring', 'Per-event behavioral monitoring evidence', 'Quantitative conformance evidence per CC7.2 monitoring controls', 'Session integrity evidence for change monitoring controls']],
        s, cw=[4.2*cm, 4.2*cm, 4.0*cm, 4.4*cm]))
    st.append(PageBreak())

    # ── SECTION 15 — LIMITATIONS ──────────────────────────────────────────────
    st += [Paragraph('15.  Known Limitations and Open Questions', s['h1']), rule(s)]
    st.append(tbl(['Limitation', 'Mitigation', 'ADR Reference', 'Status'],
        [['CCS computation requires Constraint Vector (CV) from GR; CV quality depends on GR authoring quality', 'CV validation schema enforced at GR issuance; empty CV produces AAS=0 only (never score inflation)', 'ADR-182', 'MANAGED'],
         ['SDS (semantic drift) component requires embedding model; embedding model change invalidates historical SDS scores', 'embedding_model_version field in CV; RAR projection handles model version transitions via TGB rulebook', 'ADR-182', 'OPEN'],
         ['CTCHC per-turn link adds ~50ns latency per turn on standard hardware', 'SHA3-256 is hardware-accelerated on modern CPUs; CTCHC_ENABLED=false for latency-critical non-regulated deployments', 'ADR-183', 'MANAGED'],
         ['BAR output_hash_mode=HASHED loses output content for forensic replay; mode=FULL raises GDPR concerns', 'Three-mode design (FULL/HASHED/REDACTED) addresses all deployment contexts; mode per deployment config', 'ADR-181', 'BY DESIGN'],
         ['CCS drift_threshold is session-scoped; long-running sessions accumulate drift without reset mechanism', 'Session design should scope sessions to logical governance units; CTCHC naturally bounds session length', 'ADR-182', 'OPEN'],
         ['Offline SIP verification requires all BAR records; partial export prevents verification', 'SIP export endpoint returns complete bundle; partial exports flagged as INCOMPLETE_SIP', 'ADR-183', 'MANAGED'],
         ['Multi-instance deployments require shared signing key or BAR/CTCHC per-instance shard', 'Covered by existing OMNIX signing key management (ADR-166); no BEV-specific key management required', 'ADR-181/183', 'INHERITED'],
         ['BEV does not cover tool calls or function invocations -- only text outputs', 'RFC-ATF-7 (proposed) may address structured action attestation; BEV covers LLM output domain completely', 'ADR-181', 'KNOWN GAP']],
        s, cw=[4.8*cm, 5.5*cm, 2.5*cm, 2.0*cm]))
    st.append(PageBreak())

    # ── SECTION 16 — REFERENCES ───────────────────────────────────────────────
    st += [Paragraph('16.  References', s['h1']), rule(s)]
    for cite, text in [
        ('[RFC-ATF-1]', 'Nunes, H., "RFC-ATF-1: Agent Trust Fabric Delegation Protocol", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20155016. Figshare: 10.6084/m9.figshare.32308077'),
        ('[RFC-ATF-2]', 'Nunes, H., "RFC-ATF-2: Agent Trust Fabric -- Runtime Governance Continuity", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20241344. Figshare: 10.6084/m9.figshare.32308095'),
        ('[RFC-ATF-3]', 'Nunes, H., "RFC-ATF-3: Agent Trust Fabric -- Governance Policy Interoperability, Evidence Lifecycle, and Forensic Verification Protocol", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20247342. Figshare: 10.6084/m9.figshare.32308119'),
        ('[RFC-ATF-4]', 'Nunes, H., "RFC-ATF-4: Agent Trust Fabric -- Proactive Governance Layer", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20368895. Figshare: 10.6084/m9.figshare.32394192'),
        ('[RFC-ATF-5]', 'Nunes, H., "RFC-ATF-5: Agent Trust Fabric -- Cognitive Governance Layer", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20391721'),
        ('[FIPS204]',   'National Institute of Standards and Technology, "Module-Lattice-Based Digital Signature Standard (ML-DSA)", FIPS 204, August 2024. https://doi.org/10.6028/NIST.FIPS.204'),
        ('[FIPS180-4]', 'National Institute of Standards and Technology, "Secure Hash Standard (SHS)", FIPS 180-4, August 2015.'),
        ('[Z3]',        'de Moura, L. and Bjorner, N., "Z3: An Efficient SMT Solver", TACAS 2008, LNCS 4963, pp. 337-340, 2008.'),
        ('[TLA+]',      'Lamport, L., "Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers", Addison-Wesley, 2002.'),
        ('[EU-AI-ACT]', 'European Parliament and Council, "Regulation (EU) 2024/1689 on Artificial Intelligence (EU AI Act)", Official Journal of the European Union, July 2024.'),
        ('[NIST-RMF]',  'National Institute of Standards and Technology, "Artificial Intelligence Risk Management Framework", NIST AI 100-1, January 2023.'),
        ('[ISO-42001]', 'International Organization for Standardization, "Artificial Intelligence -- Management System", ISO/IEC 42001:2023, 2023.'),
        ('[ADR-181]',   'Nunes, H., "ADR-181: Behavioral Anchor Record (BAR)", OMNIX QUANTUM, May 2026. omnixquantum.net/docs/adr/ADR-181'),
        ('[ADR-182]',   'Nunes, H., "ADR-182: Constraint Conformance Signal (CCS)", OMNIX QUANTUM, May 2026. omnixquantum.net/docs/adr/ADR-182'),
        ('[ADR-183]',   'Nunes, H., "ADR-183: Cross-Turn Coherence Hash Chain (CTCHC)", OMNIX QUANTUM, May 2026. omnixquantum.net/docs/adr/ADR-183'),
        ('[ADR-131]',   'Nunes, H., "ADR-131: Execution Integrity Layer", OMNIX QUANTUM. omnixquantum.net/docs/adr/ADR-131'),
        ('[CRYSTALS]',  'Ducas, L. et al., "CRYSTALS-Dilithium: A Lattice-Based Digital Signature Scheme", IACR TCHES 2018(1), 2018.'),
        ('[W3CVC]',     'W3C, "Verifiable Credentials Data Model 2.0", W3C Recommendation, May 2024.'),
    ]:
        st.append(Paragraph(f'<b><font color="#8b8bf0">{cite}</font></b>  {text}', s['ref']))
        st.append(sp(2))
    st.append(PageBreak())

    # ── APPENDIX A — WIRE FORMATS ─────────────────────────────────────────────
    st += [Paragraph('Appendix A -- BEV Wire Formats (JSON Schemas)', s['h1']), rule(s)]
    st.append(Paragraph('A.1  BAR Wire Format', s['h2']))
    st.append(cb(
"""  {
    "$schema": "https://omnixquantum.net/schemas/atf/bev/bar-v1.0.json",
    "bar_id":                   "BAR-[16 uppercase hex]",
    "session_id":               "[session identifier]",
    "governing_receipt_id":     "[ATF governing receipt ID]",
    "agent_id":                 "AID-[DOMAIN]-[16HEX]",
    "turn_index":               [integer >= 0, strictly monotone per session],
    "output_hash":              "[64-char hex SHA3-256 of output_text.encode('utf-8')]",
    "output_hash_mode":         "FULL" | "HASHED" | "REDACTED",
    "output_payload":           { ...structured output... },   // mode=FULL only, null otherwise
    "constraint_vector":        { ...CV from governing_receipt... },
    "ccs_score":                [decimal 0.0000 - 100.0000],
    "ccs_verdict":              "CONFORMANT" | "DRIFTING" | "BREACH" | "VIOLATION" | "HALT" | "NO_DATA",
    "ccs_components":           { "obs": [0-40], "css": [0-30], "sds": [0-20], "aas": [0 or 10] },
    "chain_link":               "[64-char hex SHA3-256 chain link for this turn]",
    "genesis_hash":             "[64-char hex] or null",       // non-null for turn_index=0
    "session_start_ns":         [integer nanosecond timestamp] or null,
    "bar_timestamp_ns":         [integer nanosecond timestamp],
    "issued_at":                "[ISO8601 with nanoseconds and timezone]",
    "content_hash":             "[64-char hex SHA3-256(output_hash||receipt_id||str(turn_index))]",
    "pqc_signature":            "[base64 ML-DSA-65 signature over content_hash.encode('utf-8')]",
    "pqc_algorithm":            "ML-DSA-65",
    "atf_spec_version":         "RFC-ATF-6_v1.0",
    "bar_status":               "ACTIVE" | "HALTED" | "VIOLATION"
  }""", s))
    st.append(sp(6))

    st.append(Paragraph('A.2  CCS Wire Format', s['h2']))
    st.append(cb(
"""  {
    "$schema": "https://omnixquantum.net/schemas/atf/bev/ccs-v1.0.json",
    "ccs_id":                          "CCS-[16 uppercase hex]",
    "bar_id":                          "BAR-[16 uppercase hex]",
    "session_id":                      "[session identifier]",
    "governing_receipt_id":            "[ATF governing receipt ID]",
    "turn_index":                      [integer >= 0],
    "conformance_score":               [decimal 0.0000 - 1.0000],
    "verdict":                         "CONFORMANT"|"DRIFTING"|"BREACH"|"VIOLATION"|"HALT"|"NO_DATA",
    "output_boundary_score":           [decimal 0.000 - 40.000],
    "constraint_satisfaction_score":   [decimal 0.000 - 30.000],
    "semantic_drift_score":            [decimal 0.000 - 20.000],
    "authority_alignment_score":       0.0 | 10.0,
    "boundary_violation_count":        [integer >= 0],
    "constraint_failure_count":        [integer >= 0],
    "drift_magnitude":                 [decimal 0.0000 - 1.0000],
    "cumulative_drift":                [decimal >= 0.0],
    "drift_delta":                     [decimal 0.0000 - 1.0000],
    "watchdog_triggered":              true | false,
    "agvp_pvr_id":                     "PVR-[16HEX]" | null,
    "halt_triggered":                  true | false,
    "chain_link_hash":                 "[64-char hex]",
    "computed_at_ns":                  [integer nanosecond timestamp]
  }""", s))
    st.append(sp(6))

    st.append(Paragraph('A.3  CTCHC Wire Format', s['h2']))
    st.append(cb(
"""  {
    "$schema": "https://omnixquantum.net/schemas/atf/bev/ctchc-v1.0.json",
    "ctchc_id":              "CTCHC-[16 uppercase hex]",
    "session_id":            "[session identifier -- UNIQUE constraint]",
    "governing_receipt_id":  "[ATF governing receipt ID]",
    "genesis_hash":          "[64-char hex SHA3-256(session_id||'||'||receipt_id||'||'||'OMNIX-CTCHC-GENESIS')]",
    "final_chain_hash":      "[64-char hex link[N-1]]" | null,
    "turn_count":            [integer >= 0],
    "all_bar_ids":           ["BAR-...", "BAR-...", ...],    // ordered by turn_index
    "session_start_ns":      [integer nanosecond timestamp] | null,
    "session_close_ns":      [integer nanosecond timestamp] | null,
    "session_status":        "ACTIVE" | "COMPLETED" | "HALTED" | "ABANDONED",
    "failure_turn_index":    [integer] | null,
    "failure_reason":        "[string]" | null,
    "seal_hash":             "[64-char hex SHA3-256(genesis||all_links_concat||final_hash)]" | null,
    "ctchc_seal":            "[base64 ML-DSA-65 signature over seal_hash.encode()]" | null,
    "pqc_algorithm":         "ML-DSA-65",
    "chain_sealed":          true | false,
    "atf_spec_version":      "RFC-ATF-6_v1.0",
    "created_at":            "[ISO8601 timestamp]"
  }""", s))
    st.append(PageBreak())

    # ── APPENDIX B — CROSS-LAYER MAP ──────────────────────────────────────────
    st += [Paragraph('Appendix B -- Cross-Layer Integration Map', s['h1']), rule(s)]
    st.append(Paragraph(
        'The following table provides the complete cross-layer integration points between BEV (Layer 6) '
        'and all prior ATF layers. BEV extends without modifying any prior layer.', s['body']))
    st.append(tbl(['BEV Component', 'Layer', 'Integrated With', 'RFC', 'Integration Field', 'Direction'],
        [['BAR', 'L1', 'Agent Identity Record (AIR)', 'RFC-ATF-1', 'agent_id in BAR bound to AIR identity', 'BAR -> AIR'],
         ['BAR', 'L1', 'Delegation Receipt (DR)', 'RFC-ATF-1', 'governing_receipt_id traces to DR chain_root_id', 'BAR -> DR'],
         ['BAR', 'L2', 'Runtime Continuity Record (RCR)', 'RFC-ATF-2', 'bar_status=HALTED propagates via RCR HALT mechanism', 'BAR -> RCR'],
         ['CCS', 'L3', 'OMNIX Evidence Package (OEP)', 'RFC-ATF-3', 'CCS records included as behavioral evidence in OEP bundle', 'CCS -> OEP'],
         ['CTCHC', 'L3', 'OEP Forensic Package', 'RFC-ATF-3', 'CTCHC seal (SIP) is root artifact in OEP behavioral section', 'CTCHC -> OEP'],
         ['CCS', 'L4', 'AGVP Watchdog', 'RFC-ATF-4', 'verdict in {DRIFTING,BREACH,VIOLATION} -> PVR issuance request', 'CCS -> AGVP'],
         ['BAR', 'L5', 'Temporal Context Snapshot (TCS)', 'RFC-ATF-5', 'bar_timestamp_ns matches TCS.issued_at_ns for 7yr retention', 'BAR <-> TCS'],
         ['CCS', 'L5', 'Regulatory Alignment Receipt (RAR)', 'RFC-ATF-5', 'CCS conformance history included in RAR field_projections', 'CCS -> RAR'],
         ['CTCHC', 'L5', 'Universal Invariant Receipt (UIR)', 'RFC-ATF-5', 'SIP provides behavioral evidence for UGI-002 assertion', 'CTCHC -> UIR'],
         ['BAR', 'L5', 'Counterfactual Attestation Token (CAT)', 'RFC-ATF-5', 'BAR records are behavioral ground truth for CGE fork comparison', 'BAR -> CAT']],
        s, cw=[2.5*cm, 1.2*cm, 4.0*cm, 2.8*cm, 4.8*cm, 2.5*cm]))
    st.append(PageBreak())

    # ── APPENDIX C — COMPLIANCE CHECKLIST ────────────────────────────────────
    st += [Paragraph('Appendix C -- ATF-BEV-Compliant Compliance Checklist', s['h1']), rule(s)]
    st.append(Paragraph(
        'The following checklist provides the complete set of requirements for achieving '
        'ATF-BEV-Compliant designation. All items are required.', s['body']))
    for section, items in [
        ('C.1  Prior RFC Compliance (ATF-CGL-Compliant required)', [
            'ATF-Compliant-L3: AIR, DR, TAR, Trust Lattice operational; ATF-INV-001-006 all satisfied',
            'ATF-RGC-Compliant: RCR, CES, AFG, RC operational; RGC-INV-001-008 all satisfied',
            'ATF-FEI-Compliant: OEP, GPIL, ELC, FVP operational; all L3 invariants satisfied',
            'ATF-PGL-Compliant: AGVP, SSD, DSPP operational; all L4 invariants satisfied',
            'ATF-CGL-Compliant: CGE, GUGT UIR, TGB operational; all L5 invariants satisfied',
        ]),
        ('C.2  BAR Requirements', [
            'BEV_ENABLED=true in production configuration',
            'BEV-INV-001: BAR produced before output delivery; no output path without BAR',
            'BEV-INV-002: content_hash = SHA3-256(output_hash || receipt_id || str(turn_index))',
            'BEV-INV-003: bar_status=HALTED -> immediate session halt; no subsequent turn permitted',
            'BEV-INV-004: ML-DSA-65 seal over content_hash; append-only enforced on atf_behavioral_anchor_records',
            'BEV-INV-015: empty output_text -> bar_status=VIOLATION enforced',
            'BEV-INV-016: BAR identifier format BAR-{HEX16} enforced at generation',
            'Z3 proof targets BEV-FVS-001, BEV-FVS-002, BEV-FVS-009: UNSAT/structural',
        ]),
        ('C.3  CCS Requirements', [
            'CCS_ENABLED=true; CCS computed atomically with each BAR (BEV-INV-005)',
            'BEV-INV-006: conformance_score in [0.0, 1.0]; all components >= 0; Z3 BEV-FVS-003: UNSAT',
            'BEV-INV-007: verdict DRIFTING/BREACH/VIOLATION -> AGVP watchdog notified; PVR issued',
            'BEV-INV-008: cumulative_drift > CCS_DRIFT_THRESHOLD -> HALT; threshold <= 0.50 in production',
            'BEV-INV-009: append-only enforced on atf_constraint_conformance_signals',
            'BEV-INV-017: cumulative_drift accumulator isolated per session_id; reload on restart',
            'Z3 proof targets BEV-FVS-006, BEV-FVS-007: UNSAT',
        ]),
        ('C.4  CTCHC Requirements', [
            'CTCHC_ENABLED=true; genesis hash created before BAR_0 (BEV-INV-010)',
            'BEV-INV-011: chain link formula SHA3-256(json.dumps({prev,turn,receipt},sort_keys=True))',
            'BEV-INV-012: gap detection operational; verification fails on missing turn_index',
            'BEV-INV-013: seal_hash = SHA3-256(genesis || all_links_concat || final_hash)',
            'BEV-INV-014: ML-DSA-65 seal applied before OEP export or regulatory submission',
            'BEV-INV-018: all links carry same governing_receipt_id as genesis; cross-session splice rejected',
            'Offline 6-step SIP verification procedure documented and tested',
            'Z3 proof targets BEV-FVS-005, BEV-FVS-008: UNSAT/structural',
        ]),
        ('C.5  Formal Verification', [
            'All 9 Z3 proof targets (BEV-FVS-001 through BEV-FVS-009): UNSAT or structural',
            'All 8 TLA+ specification checks pass (BEV_BAR, BEV_CCS, BEV_CTCHC, BEV_INTEGRATION)',
            'FVS runner output: python omnix_core/formal_verification/run_bev_proofs.py',
            'FVS output archived with UIR as supporting compliance evidence',
        ]),
    ]:
        st.append(Paragraph(section, s['h2']))
        for item in items:
            st.append(Paragraph(f'[ ]  {item}', s['bullet']))
        st.append(sp(4))

    # ── AUTHOR ADDRESS ────────────────────────────────────────────────────────
    st.append(PageBreak())
    st += [Paragraph("Author's Address", s['h1']), rule(s), sp(10)]
    st.append(box([
        Paragraph('Harold Alberto Nunes Rodelo (Editor)', s['gold']), sp(4),
        Paragraph('OMNIX QUANTUM LTD', s['abody']),
        Paragraph('71-75 Shelton Street, Covent Garden', s['abody']),
        Paragraph('London WC2H 9JQ, England', s['abody']),
        sp(4),
        Paragraph('Email: standards@omnixquantum.com', s['abody']),
        Paragraph('Web:   omnixquantum.net', s['abody']),
        sp(8),
        Paragraph('RFC-ATF-6 Version 1.0.0 -- May 2026', s['caption']),
        Paragraph('Priority Records: OMNIX-PAR-2026-BAR-001 -- OMNIX-PAR-2026-CCS-001 -- OMNIX-PAR-2026-CTCHC-001', s['caption']),
        Paragraph('DOI: pending submission', s['caption']),
    ], s, border=ACCENT_GOLD))

    doc = SimpleDocTemplate(
        output, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=2.6*cm, bottomMargin=1.8*cm,
        title='RFC-ATF-6: Behavioral Execution Verification Protocol',
        author='Harold Alberto Nunes Rodelo -- OMNIX QUANTUM LTD',
        subject='ATF-BEV-Compliant -- Sixth compliance tier -- 106 invariants',
        creator='OMNIX QUANTUM generate_atf6_pdf.py',
    )
    doc.build(st, onFirstPage=on_page, onLaterPages=on_page)
    sz = os.path.getsize(output) // 1024
    print(f'  PDF: {output}')
    print(f'  Size: {sz} KB')


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else OUT
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print('Generating RFC-ATF-6 PDF...')
    print(f'  Logo: {LOGO} {"[OK]" if os.path.exists(LOGO) else "[NOT FOUND]"}')
    build(out)
