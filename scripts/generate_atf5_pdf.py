"""
OMNIX QUANTUM — RFC-ATF-5 PDF Generator
Cognitive Governance Layer: CGE · GUGT · TGB
Run: python scripts/generate_atf5_pdf.py
Output: docs/zenodo/rfc_atf_5/RFC-ATF-5.pdf
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

# ── Brand colors ──────────────────────────────────────────────────────────────
DARK_BG      = colors.HexColor('#0d0d1a')
ACCENT_BLUE  = colors.HexColor('#5b5bd6')
ACCENT_LIGHT = colors.HexColor('#8b8bf0')
ACCENT_GOLD  = colors.HexColor('#d4a843')   # CGL tier — fifth tier gets gold accent
TEXT_WHITE   = colors.HexColor('#f0f0f0')
TEXT_GRAY    = colors.HexColor('#aaaaaa')
BORDER_GRAY  = colors.HexColor('#333355')
CODE_BG      = colors.HexColor('#1a1a2e')
TABLE_HEAD   = colors.HexColor('#1e1e3a')
TABLE_ALT    = colors.HexColor('#141428')
TABLE_BORDER = colors.HexColor('#2a2a4a')
RULE_COLOR   = colors.HexColor('#3a3a5a')
GREEN_OK     = colors.HexColor('#4ade80')
WHITE        = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(ROOT, 'omnix_web', 'public', 'logo_nobg.png')
OUT_PATH  = os.path.join(ROOT, 'docs', 'zenodo', 'rfc_atf_5', 'RFC-ATF-5.pdf')

# ── Page decorators ───────────────────────────────────────────────────────────
def cover_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, PAGE_H - 8*mm, PAGE_W, 8*mm, fill=1, stroke=0)
    canvas.setFillColor(ACCENT_GOLD)
    canvas.rect(0, 0, PAGE_W, 6*mm, fill=1, stroke=0)
    canvas.restoreState()

def normal_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, PAGE_H - 4*mm, PAGE_W, 4*mm, fill=1, stroke=0)
    canvas.setFillColor(TABLE_HEAD)
    canvas.rect(0, 0, PAGE_W, 12*mm, fill=1, stroke=0)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(TEXT_GRAY)
    canvas.drawString(MARGIN, 4*mm,
        'RFC-ATF-5 · Cognitive Governance Layer · OMNIX QUANTUM LTD · omnixquantum.net')
    canvas.drawRightString(PAGE_W - MARGIN, 4*mm, f'Page {doc.page}')
    canvas.setStrokeColor(RULE_COLOR)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 12*mm, PAGE_W - MARGIN, 12*mm)
    canvas.restoreState()

# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    s = {}
    s['cover_badge']    = ParagraphStyle('cover_badge',    fontName='Helvetica-Bold', fontSize=9,  leading=14, textColor=ACCENT_GOLD,  alignment=TA_LEFT)
    s['cover_tier']     = ParagraphStyle('cover_tier',     fontName='Helvetica-Bold', fontSize=9,  leading=14, textColor=ACCENT_LIGHT, alignment=TA_LEFT)
    s['cover_title']    = ParagraphStyle('cover_title',    fontName='Helvetica-Bold', fontSize=26, leading=34, textColor=WHITE,        alignment=TA_LEFT, spaceAfter=6)
    s['cover_subtitle'] = ParagraphStyle('cover_subtitle', fontName='Helvetica',      fontSize=15, leading=21, textColor=ACCENT_LIGHT, alignment=TA_LEFT, spaceAfter=20)
    s['cover_meta']     = ParagraphStyle('cover_meta',     fontName='Helvetica',      fontSize=10, leading=16, textColor=TEXT_GRAY,    alignment=TA_LEFT, spaceAfter=4)
    s['abstract_title'] = ParagraphStyle('abstract_title', fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=ACCENT_LIGHT, alignment=TA_LEFT, spaceAfter=4)
    s['abstract_body']  = ParagraphStyle('abstract_body',  fontName='Helvetica',      fontSize=9.5,leading=15, textColor=TEXT_WHITE,   alignment=TA_JUSTIFY, spaceAfter=6)
    s['h1']   = ParagraphStyle('h1',  fontName='Helvetica-Bold', fontSize=15,   leading=20, textColor=WHITE,        spaceBefore=18, spaceAfter=8)
    s['h2']   = ParagraphStyle('h2',  fontName='Helvetica-Bold', fontSize=11.5, leading=16, textColor=ACCENT_LIGHT, spaceBefore=14, spaceAfter=5)
    s['h3']   = ParagraphStyle('h3',  fontName='Helvetica-Bold', fontSize=10,   leading=14, textColor=TEXT_GRAY,    spaceBefore=10, spaceAfter=4)
    s['body'] = ParagraphStyle('body',fontName='Helvetica',      fontSize=9.5,  leading=15, textColor=TEXT_WHITE,   alignment=TA_JUSTIFY, spaceAfter=6)
    s['bullet']= ParagraphStyle('bullet',fontName='Helvetica',   fontSize=9.5,  leading=15, textColor=TEXT_WHITE,   leftIndent=16, firstLineIndent=-8, spaceAfter=2)
    s['code'] = ParagraphStyle('code', fontName='Courier',       fontSize=7.5,  leading=11, textColor=ACCENT_LIGHT, leftIndent=4, backColor=CODE_BG)
    s['caption']= ParagraphStyle('caption',fontName='Helvetica-Oblique',fontSize=8,leading=12,textColor=TEXT_GRAY, alignment=TA_CENTER, spaceBefore=2)
    s['inv']  = ParagraphStyle('inv',  fontName='Helvetica-Bold', fontSize=9,   leading=13, textColor=ACCENT_GOLD)
    s['ref']  = ParagraphStyle('ref',  fontName='Helvetica',      fontSize=8.5, leading=13, textColor=TEXT_GRAY,    leftIndent=16, firstLineIndent=-16, spaceAfter=2)
    s['gold'] = ParagraphStyle('gold', fontName='Helvetica-Bold', fontSize=10,  leading=14, textColor=ACCENT_GOLD)
    return s

# ── Helpers ───────────────────────────────────────────────────────────────────
def sp(n=6):   return Spacer(1, n)
def rule(S):   return HRFlowable(width='100%', thickness=0.5, color=RULE_COLOR, spaceAfter=6, spaceBefore=6)
def accent_rule(S): return HRFlowable(width='40%', thickness=1.5, color=ACCENT_BLUE, spaceAfter=20)

def code_block(text, S):
    lines = text.strip().split('\n')
    rows = [[Paragraph(l.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'), S['code'])] for l in lines]
    return Table(rows, colWidths=[PAGE_W - 2*MARGIN - 16*mm],
        style=TableStyle([
            ('BACKGROUND', (0,0),(-1,-1), CODE_BG),
            ('LEFTPADDING',(0,0),(-1,-1), 8), ('RIGHTPADDING',(0,0),(-1,-1), 8),
            ('TOPPADDING', (0,0),(-1,-1), 2), ('BOTTOMPADDING',(0,0),(-1,-1), 2),
            ('BOX',(0,0),(-1,-1), 0.5, BORDER_GRAY),
        ]))

def make_table(headers, rows, S, col_widths=None):
    hs = ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=8, leading=12, textColor=ACCENT_LIGHT)
    cs = ParagraphStyle('td', fontName='Helvetica',      fontSize=8, leading=12, textColor=TEXT_WHITE)
    cg = ParagraphStyle('tg', fontName='Helvetica',      fontSize=8, leading=12, textColor=TEXT_GRAY)
    data = [[Paragraph(h, hs) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), cg if i==0 and len(headers)>2 else cs) for i,c in enumerate(row)])
    avail = PAGE_W - 2*MARGIN - 4*mm
    if col_widths is None:
        col_widths = [avail / len(headers)] * len(headers)
    return Table(data, colWidths=col_widths, repeatRows=1,
        style=TableStyle([
            ('BACKGROUND',(0,0),(-1,0), TABLE_HEAD),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [TABLE_ALT, CODE_BG]),
            ('GRID',(0,0),(-1,-1), 0.4, TABLE_BORDER),
            ('LEFTPADDING',(0,0),(-1,-1), 6), ('RIGHTPADDING',(0,0),(-1,-1), 6),
            ('TOPPADDING',(0,0),(-1,-1), 4), ('BOTTOMPADDING',(0,0),(-1,-1), 4),
            ('VALIGN',(0,0),(-1,-1), 'TOP'),
        ]))

def highlight_box(items, S, title=None):
    content = []
    if title:
        content.append(Paragraph(title, S['abstract_title']))
    for item in items:
        content.append(Paragraph(f'• {item}', S['abstract_body']))
    return Table([[content]], colWidths=[PAGE_W - 2*MARGIN - 4*mm],
        style=TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), CODE_BG),
            ('BOX',(0,0),(-1,-1), 1, ACCENT_BLUE),
            ('LEFTPADDING',(0,0),(-1,-1), 12), ('RIGHTPADDING',(0,0),(-1,-1), 12),
            ('TOPPADDING',(0,0),(-1,-1), 10), ('BOTTOMPADDING',(0,0),(-1,-1), 10),
        ]))

def gold_box(content_list, S):
    return Table([[content_list]], colWidths=[PAGE_W - 2*MARGIN - 4*mm],
        style=TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), CODE_BG),
            ('BOX',(0,0),(-1,-1), 1.2, ACCENT_GOLD),
            ('LEFTPADDING',(0,0),(-1,-1), 14), ('RIGHTPADDING',(0,0),(-1,-1), 14),
            ('TOPPADDING',(0,0),(-1,-1), 12), ('BOTTOMPADDING',(0,0),(-1,-1), 12),
        ]))

# ── Main builder ──────────────────────────────────────────────────────────────
def build_pdf(output_path):
    S = make_styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 10*mm, bottomMargin=MARGIN + 10*mm,
        title='RFC-ATF-5: Agent Trust Fabric — Cognitive Governance Layer',
        author='Harold Alberto Nunes Rodelo, OMNIX QUANTUM LTD',
        subject='Counterfactual Governance, Universal Invariants, Temporal Bridge',
        keywords='AI governance, CGE, GUGT, TGB, ATF, ML-DSA-65, OMNIX QUANTUM',
        creator='OMNIX QUANTUM Standards · omnixquantum.net',
    )
    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(sp(28))

    logo_w = 4.5 * cm
    logo_h = logo_w * (380 / 522)
    title_col = [
        Paragraph('RFC-ATF-5', S['cover_badge']),
        sp(4),
        Paragraph('OMNIX Open Standard Series · Fifth RFC', S['cover_tier']),
        sp(8),
        Paragraph('Agent Trust Fabric', S['cover_title']),
        Paragraph('Cognitive Governance Layer', S['cover_subtitle']),
        Paragraph('Counterfactual Governance Engine · Grand Unified Governance Theory · Temporal Governance Bridge', S['cover_tier']),
    ]
    logo_cell = Image(LOGO_PATH, width=logo_w, height=logo_h) if os.path.exists(LOGO_PATH) else Paragraph('OMNIX QUANTUM', S['cover_badge'])
    cover_top = Table([[title_col, logo_cell]],
        colWidths=[PAGE_W - 2*MARGIN - logo_w - 8*mm, logo_w + 4*mm],
        style=TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    story.append(cover_top)
    story.append(sp(20))
    story.append(accent_rule(S))

    for label, value in [
        ('Document',       'RFC-ATF-5 · OMNIX QUANTUM Open Standard'),
        ('Version',        '1.0.0 — May 2026'),
        ('Author',         'Harold Alberto Nunes Rodelo'),
        ('Institution',    'OMNIX QUANTUM LTD · 71-75 Shelton Street, London WC2H 9JQ'),
        ('Contact',        'standards@omnixquantum.com'),
        ('Builds on',      'RFC-ATF-1 · RFC-ATF-2 · RFC-ATF-3 · RFC-ATF-4'),
        ('Cryptography',   'Dilithium-3 ML-DSA-65 (NIST FIPS 204)'),
        ('Formal Methods', 'Z3 SMT · TLA+ — dual methodology'),
        ('New Invariants', '18 — CGE-INV-001–007 · GUGT-INV-001–006 · TGB-INV-001–005'),
        ('Total ATF Inv.', '88 across 17 protocol families'),
        ('Designation',    'ATF-CGL-Compliant — fifth and highest compliance tier'),
        ('Status',         'DRAFT — pending Zenodo submission'),
    ]:
        story.append(Paragraph(f'<b><font color="#5b5bd6">{label}:</font></b>  {value}', S['cover_meta']))

    story.append(sp(24))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER_GRAY, spaceAfter=12))

    # Abstract box
    story.append(Table([[
        [Paragraph('Abstract', S['abstract_title']),
         Paragraph(
            'RFC-ATF-5 specifies the <b>Cognitive Governance Layer (CGL)</b> — the fifth RFC in the '
            'OMNIX Agent Trust Fabric Open Standard series. Three structural problems that no existing '
            'governance framework has previously addressed are formally closed:',
            S['abstract_body']),
         Paragraph(
            '<b>(1) The Decision Space Problem</b> — The <b>Counterfactual Governance Engine (CGE)</b> '
            'computes M cryptographically sealed alternative governance paths at every evaluation, assembled '
            'into a Counterfactual Attestation Token (CAT) bound to the primary receipt. EU AI Act Art. 9 '
            '"alternatives considered" requirement satisfied with PQC-signed artifacts, not narrative.',
            S['abstract_body']),
         Paragraph(
            '<b>(2) The Universal Completeness Problem</b> — The <b>Grand Unified Governance Theory (GUGT)</b> '
            'derives six Universal Governance Invariants (UGI-001–006) by formal intersection of EU AI Act, '
            'NIST AI RMF, GCC/DIFC, ISO/IEC 42001, and UK AISI simultaneously. ATF-compliant systems earn '
            'GUGT-L3+ATF certification by construction — the first cross-framework universal compliance receipt.',
            S['abstract_body']),
         Paragraph(
            '<b>(3) The Temporal Interpretability Problem</b> — The <b>Temporal Governance Bridge (TGB)</b> '
            'bridges nanosecond-precision runtime governance to 7-year regulatory retention cycles. A Temporal '
            'Context Snapshot (TCS) embedded at issuance captures the full regulatory context; a Regulatory '
            'Alignment Receipt (RAR) projects records to current frameworks at review time without '
            'modifying the original evidence.',
            S['abstract_body']),
        ]
    ]], colWidths=[PAGE_W - 2*MARGIN - 4*mm],
    style=TableStyle([('BACKGROUND',(0,0),(-1,-1),CODE_BG),('BOX',(0,0),(-1,-1),1.2,ACCENT_GOLD),('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12)])))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('Table of Contents', S['h1']))
    story.append(rule(S))
    toc = [
        ('1.','Introduction'), ('2.','Problem Statement: The Cognitive Governance Gap'),
        ('2.1','The Decision Space Problem'), ('2.2','The Universal Completeness Problem'),
        ('2.3','The Temporal Interpretability Problem'), ('2.4','Gap_CG = Gap_DS ∪ Gap_UC ∪ Gap_TS'),
        ('3.','Architecture: Cognitive Governance Layer'),
        ('3.1','ATF Stack — Five Layers'), ('3.2','CGL Position and Extension Relationships'),
        ('3.3','Module Independence and Failure Isolation'),
        ('4.','Counterfactual Governance Engine (CGE)'),
        ('4.1','Decision Space Architecture'), ('4.2','CFR and CAT Structures'),
        ('4.3','Variation Vector Design'), ('4.4','Offline Verifiability Protocol'),
        ('4.5','CGE Invariants: CGE-INV-001–007'),
        ('5.','Grand Unified Governance Theory (GUGT)'),
        ('5.1','Universal Invariant Architecture'), ('5.2','UGI-001–006 Formal Specification'),
        ('5.3','Universal Invariant Receipt (UIR)'), ('5.4','GUGT Conformance Levels'),
        ('5.5','Cross-Jurisdiction Framework Mapping'), ('5.6','GUGT Invariants: GUGT-INV-001–006'),
        ('6.','Temporal Governance Bridge (TGB)'),
        ('6.1','Two-Scale Architecture'), ('6.2','Temporal Context Snapshot (TCS)'),
        ('6.3','Regulatory Alignment Receipt (RAR)'), ('6.4','Temporal Migration Record (TMR)'),
        ('6.5','TGB Invariants: TGB-INV-001–005'),
        ('7.','Formal Verification (OMNIX-FVS-1.0 Extension)'),
        ('8.','Combined Invariant Summary — 88 Total'),
        ('9.','Compliance: ATF-CGL-Compliant'),
        ('10.','Security Considerations'), ('11.','Novel Contributions'),
        ('12.','Distinction from Prior Art'), ('13.','Regulatory Alignment'),
        ('14.','References'), ('A.','Appendix A — CGL Wire Formats'),
        ('B.','Appendix B — GUGT Framework Mapping'), ('C.','Appendix C — CGL Compliance Checklist'),
    ]
    for num, title in toc:
        indent = 16 if '.' in num and len(num) > 2 else 0
        bold = 'Bold' if (num.endswith('.') or '.' not in num) and len(num) <= 2 else ''
        st = ParagraphStyle('t', fontName=f'Helvetica{"-Bold" if not indent else ""}',
            fontSize=9.5, leading=16, textColor=WHITE if not indent else TEXT_WHITE, leftIndent=indent)
        story.append(Paragraph(f'{num}  {title}', st))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — INTRODUCTION
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('1.  Introduction', S['h1']))
    story.append(rule(S))
    story.append(Paragraph(
        'The Agent Trust Fabric protocol stack addresses the complete lifecycle of a governed autonomous '
        'agent action. Each prior RFC answered its defining question completely:', S['body']))
    story.append(make_table(
        ['RFC', 'Layer', 'Question Answered'],
        [['RFC-ATF-1', 'Identity & Delegation', 'Who authorized this agent, with what authority, and can that be proved offline?'],
         ['RFC-ATF-2', 'Runtime Continuity', 'Was authority continuously valid throughout execution?'],
         ['RFC-ATF-3', 'Evidence & Forensic', 'Where does evidence go and who can verify it years later without platform access?'],
         ['RFC-ATF-4', 'Proactive Governance', 'What happened between requests? Is recalibration safe? Do receipts remain semantically portable?'],
         ['RFC-ATF-5', 'Cognitive Governance', 'What else could have happened? Is the system universally complete? Will evidence remain interpretable across time?']],
        S, col_widths=[2.2*cm, 4.0*cm, 10.6*cm]))
    story.append(sp(8))
    story.append(Paragraph(
        'RFC-ATF-5 answers questions about the <b>cognitive dimension</b> of governance: the capacity to '
        'document decision alternatives (CGE), to claim universal validity across all frameworks '
        'simultaneously (GUGT), and to remain coherent across temporal boundaries spanning nanosecond '
        'execution to decade-scale regulatory review (TGB). Together, these constitute the '
        '<b>Cognitive Governance Layer</b> — the layer concerned not with what governance does, but '
        'with what governance can demonstrate about what it has done, what it could have done, and '
        'what it will mean to a reviewer in a different time and regulatory context.', S['body']))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — PROBLEM STATEMENT
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('2.  Problem Statement: The Cognitive Governance Gap', S['h1']))
    story.append(rule(S))

    story.append(Paragraph('2.1  The Decision Space Problem', S['h2']))
    story.append(Paragraph(
        'The ATF stack through RFC-ATF-4 guarantees <b>DP = SP</b> (Documented Path = Selected Path) '
        'with cryptographic certainty. It does not record the Decision Space (DS) — the full set of '
        'governance outcomes that existed at evaluation time under parametric variations of the authority '
        'configuration. This creates the <b>Decision Space Gap (Gap_DS = DS \\ {SP})</b>:', S['body']))
    gap_ds_diagram = """\
  ┌─────────────────────────────────────────────────────────────────────┐
  │                     DECISION SPACE  (DS)                            │
  │                                                                     │
  │   ┌─────────────┐   ┌─────────────┐   ┌──────────────────────┐    │
  │   │  MONITORING │   │  ■ NOMINAL  │   │      WARNING         │    │
  │   │  (CES 50-79)│   │  (selected) │   │  (CES 30-49)         │    │
  │   │             │   │  ← SP = DP  │   │                      │    │
  │   │  reachable  │   │  PQC-signed │   │  reachable by -15%   │    │
  │   │  by -20% VV │   │  in receipt │   │  authority_budget VV │    │
  │   └─────────────┘   └─────────────┘   └──────────────────────┘    │
  │                                                                     │
  │   Gap_DS = {MONITORING, WARNING} — not recorded by ATF-1/2/3/4    │
  │   CGE closes this gap: each element of Gap_DS becomes a CFR        │
  └─────────────────────────────────────────────────────────────────────┘
  Stakeholders who need Gap_DS documented:
  [A] Regulatory auditors — EU AI Act Art. 9: "alternatives considered"
  [B] Enterprise risk officers — fragility_score = |Gap_DS ∩ DS| / |DS|
  [C] Legal counsel — "could the system have reached a different outcome?"\
"""
    story.append(code_block(gap_ds_diagram, S))
    story.append(sp(6))

    story.append(Paragraph('2.2  The Universal Completeness Problem', S['h2']))
    story.append(Paragraph(
        'The ATF stack satisfies GC (Governance Completeness) for specific (Framework, Agent-type) pairs '
        'but does not formally assert MFC (Multi-Frame Completeness). Enterprise buyers deploying across '
        'EU + US + GCC + ISO jurisdictions must engage external counsel to perform the mapping — a cost '
        'barrier that directly impedes adoption. The <b>Universal Completeness Gap (Gap_UC)</b>:', S['body']))
    gap_uc_diagram = """\
  Without RFC-ATF-5:
  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
  │ EU AI Act    │   │ NIST AI RMF  │   │ GCC/DIFC     │   │ ISO 42001    │
  │ compliance   │   │ compliance   │   │ compliance   │   │ compliance   │
  │ (custom map) │   │ (custom map) │   │ (custom map) │   │ (custom map) │
  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
        ↑                  ↑                  ↑                  ↑
        ├──────────────────┴──────────────────┴──────────────────┘
        │  No single artifact certifies all simultaneously

  With RFC-ATF-5 GUGT:
  ┌──────────────────────────────────────────────────────────────────────┐
  │             Universal Invariant Receipt (UIR)                        │
  │         GUGT-L3+ATF · PQC-signed · offline-verifiable               │
  │  UGI-001: human anchor  ✓  UGI-002: offline evidence ✓             │
  │  UGI-003: exec boundary ✓  UGI-004: pre-committed   ✓             │
  │  UGI-005: no self-mod   ✓  UGI-006: self-contained  ✓             │
  └──────────────────────────────────────────────────────────────────────┘
        ↑ single PQC-signed artifact satisfies all 4 frameworks + UK AISI
        ↑ zero custom analysis required for ATF-compliant systems\
"""
    story.append(code_block(gap_uc_diagram, S))
    story.append(sp(6))

    story.append(Paragraph('2.3  The Temporal Interpretability Problem', S['h2']))
    story.append(Paragraph(
        'EU AI Act Art. 72 mandates 7-year record retention for high-risk AI. A receipt produced today '
        'under ATF Spec v1.4 and "EU AI Act 2024 v1.0" must remain interpretable when reviewed in 2031 '
        'under an amended framework. Three failure modes arise from an unresolved <b>Temporal Semantic '
        'Gap (Gap_TS)</b>:', S['body']))
    gap_ts_diagram = """\
  TIMELINE:
  ──────────────────────────────────────────────────────────────────────────▶
  T=0 (2026)          T=2yr (2028)            T=7yr (2033)
  Receipt issued      Framework revision      Regulatory audit
  EU_AI_ACT_2024_v1.0  → EU_AI_ACT_2027_v2.0  → "What did this mean in 2026?"

  WITHOUT TGB:                  WITH RFC-ATF-5 TGB:
  ┌──────────────────┐          ┌───────────────────────────────────────────┐
  │ Receipt.json     │          │ Receipt.json                              │
  │ issued_at: 2026  │          │ ├── TCS (embedded at nanosecond T=0)      │
  │ status: NOMINAL  │          │ │   ├── eu_ai_act_version: 2024_v1.0     │
  │ threshold: 80.0  │          │ │   ├── nominal_threshold: 80.0          │
  │                  │          │ │   └── tcs_seal: ML-DSA-65 ✓           │
  │ [no context]     │          │ └── RAR (produced at audit T=7yr)        │
  │ [ambiguous 2033] │          │     ├── field_projections: NOMINAL→...   │
  └──────────────────┘          │     ├── original_record_integrity:VERIFIED│
   Misclassification risk       │     └── rar_seal: ML-DSA-65 ✓           │
                                └───────────────────────────────────────────┘
                                 Zero ambiguity — self-contained projection\
"""
    story.append(code_block(gap_ts_diagram, S))
    story.append(sp(6))
    story.append(Paragraph(
        '<b>Gap_CG = Gap_DS ∪ Gap_UC ∪ Gap_TS.</b>  RFC-ATF-5 formally closes Gap_CG.', S['gold']))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — ARCHITECTURE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('3.  Architecture: Cognitive Governance Layer', S['h1']))
    story.append(rule(S))

    story.append(Paragraph('3.1  The ATF Stack — Five Layers', S['h2']))
    stack_diagram = """\
  ╔══════════════════════════════════════════════════════════════════════════╗
  ║           ATF PROTOCOL STACK — COMPLETE FIVE-LAYER ARCHITECTURE        ║
  ╠══════════════════════════════════════════════════════════════════════════╣
  ║                                                                         ║
  ║  Layer 5 ── COGNITIVE GOVERNANCE LAYER (RFC-ATF-5) ─────── ★ THIS RFC ║
  ║  ┌────────────────────────────────────────────────────────────────────┐ ║
  ║  │  CGE: Counterfactual Governance Engine                            │ ║
  ║  │    → M alternative governance paths, PQC-sealed as CAT            │ ║
  ║  │  GUGT: Grand Unified Governance Theory                            │ ║
  ║  │    → 6 UGIs · UIR certifies all frameworks simultaneously         │ ║
  ║  │  TGB: Temporal Governance Bridge                                  │ ║
  ║  │    → TCS at nanosecond issuance · RAR at 7-year review            │ ║
  ║  └────────────────────────────────────────────────────────────────────┘ ║
  ║                                                                         ║
  ║  Layer 4 ── PROACTIVE GOVERNANCE PLANE (RFC-ATF-4)                     ║
  ║  ┌────────────────────────────────────────────────────────────────────┐ ║
  ║  │  AGVP · SSD · DSPP — Proactive veto · Topology · Portability      │ ║
  ║  └────────────────────────────────────────────────────────────────────┘ ║
  ║                                                                         ║
  ║  Layer 3 ── EVIDENCE & FORENSIC PLANE (RFC-ATF-3)                      ║
  ║  ┌────────────────────────────────────────────────────────────────────┐ ║
  ║  │  GPIL · ELC · OEP · FVP — Evidence lifecycle · Forensic packages  │ ║
  ║  └────────────────────────────────────────────────────────────────────┘ ║
  ║                                                                         ║
  ║  Layer 2 ── RUNTIME CONTINUITY PLANE (RFC-ATF-2)                       ║
  ║  ┌────────────────────────────────────────────────────────────────────┐ ║
  ║  │  RCR · CES · AFG · RC — Runtime health · Drift · HALT propagation  │ ║
  ║  └────────────────────────────────────────────────────────────────────┘ ║
  ║                                                                         ║
  ║  Layer 1 ── IDENTITY & DELEGATION PLANE (RFC-ATF-1)                    ║
  ║  ┌────────────────────────────────────────────────────────────────────┐ ║
  ║  │  AIR · DR · Trust Lattice · TAR — Who authorized this agent?       │ ║
  ║  └────────────────────────────────────────────────────────────────────┘ ║
  ║                                                                         ║
  ╠══════════════════════════════════════════════════════════════════════════╣
  ║  Invariants: 6 + 8 + 40 + 16 + 18 = 88 total across 17 families       ║
  ║  Designation: ATF-CGL-Compliant — fifth and highest tier               ║
  ╚══════════════════════════════════════════════════════════════════════════╝\
"""
    story.append(code_block(stack_diagram, S))
    story.append(sp(6))

    story.append(Paragraph('3.2  CGL Module Operation and Sequencing', S['h2']))
    sequence_diagram = """\
  For every primary ATF record R:

  Step 1  ──  Issue and persist R  (Layer 1-4 record)
              ↓  R.content_hash sealed · R.pqc_signature applied · DB INSERT
  Step 2  ──  TCS embedding  [SYNCHRONOUS — part of R creation]
              ↓  TCS captures: regulatory_context · threshold_context · issued_at_ns
              ↓  tcs_hash included in R.posture_state_hash
  Step 3  ──  CGE fork computation  [ASYNC — after R persisted, CGE-INV-002]
              ↓  M CFRs computed with deterministic VVs
              ↓  CAT assembled: cat_root_hash = sha256(sorted(cfr_content_hashes))
  Step 4  ──  UIR issuance  [ON DEMAND — not at record creation time]
              ↓  GUGT assessment run for a deployment
              ↓  UIR issued with 6 UGI results, PQC-sealed

  Critical ordering invariant (CGE-INV-002 + TGB-INV-001):
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐
  │ Primary  │───▶│  TCS     │───▶│  CAT     │───▶│  UIR         │
  │ record   │    │ (sync)   │    │ (async)  │    │ (on demand)  │
  │ persisted│    │ t+100ns  │    │ t+200ns+ │    │ any time     │
  └──────────┘    └──────────┘    └──────────┘    └──────────────┘
  ANY CGL failure is non-blocking — primary record always valid\
"""
    story.append(code_block(sequence_diagram, S))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — CGE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('4.  Counterfactual Governance Engine (CGE)', S['h1']))
    story.append(rule(S))
    story.append(Paragraph(
        'The CGE computes M alternative governance paths at the moment of a primary ATF governance '
        'evaluation. M is configurable via CGE_FORK_COUNT (default: 3, range: 1–7). '
        'Each path applies a deterministic Variation Vector (VV) to the primary evaluation inputs '
        'and re-executes governance logic in read-only mode — producing no receipts, no HALTs, '
        'no escalations. Its sole output is a PQC-signed Counterfactual Fork Record (CFR).', S['body']))

    story.append(Paragraph('4.1  CGE Decision Space Architecture', S['h2']))
    cge_architecture = """\
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                  CGE EVALUATION FLOW                                    │
  │                                                                         │
  │  PRIMARY RECORD (sealed & persisted first — CGE-INV-002)               │
  │  ┌──────────────────────────────────────────────────────────────────┐  │
  │  │ outcome: NOMINAL · ces_score: 82.5 · pqc_signature: ML-DSA-65   │  │
  │  └──────────────────────────────────────────────────────────────────┘  │
  │           │                                                             │
  │           ▼  CGE begins AFTER primary persisted                        │
  │  ┌─────────────────────────────────────────────────────────────────┐   │
  │  │              VARIATION VECTOR GENERATION (deterministic)        │   │
  │  │  seed = SHA256(evaluation_id ‖ primary_receipt_id)              │   │
  │  │  VV-1: authority_budget_delta_pct = -0.20                       │   │
  │  │  VV-2: ces_threshold_nominal_override = 88.0                    │   │
  │  │  VV-3: delegation_depth_limit_override = 3                      │   │
  │  └─────────────────────────────────────────────────────────────────┘   │
  │           │                                                             │
  │     ┌─────┼─────┐                                                       │
  │     ▼     ▼     ▼   Read-only re-evaluations                           │
  │  ┌─────┐┌─────┐┌─────┐                                                 │
  │  │CFR-1││CFR-2││CFR-3│  Each: outcome + ces_score + ML-DSA-65 sig     │
  │  │MON  ││NOM  ││HALT │  diverges_from_primary: T / F / T              │
  │  └──┬──┘└──┬──┘└──┬──┘                                                 │
  │     └──────┴──────┘                                                     │
  │           │                                                             │
  │           ▼                                                             │
  │  ┌────────────────────────────────────────────────────────────────┐    │
  │  │  COUNTERFACTUAL ATTESTATION TOKEN (CAT)                        │    │
  │  │  cat_root_hash = sha256(sorted(cfr_hashes))                    │    │
  │  │  divergence_count: 2    fragility_score: 0.67                  │    │
  │  │  cat_seal: ML-DSA-65 over cat_root_hash                        │    │
  │  └────────────────────────────────────────────────────────────────┘    │
  └─────────────────────────────────────────────────────────────────────────┘
  fragility_score = divergence_count / cfr_count  ∈ [0.0, 1.0]
  0.0 = decision robust (all alternatives agree)
  1.0 = decision fragile (all alternatives diverge — parameter sensitivity)\
"""
    story.append(code_block(cge_architecture, S))
    story.append(sp(8))

    story.append(Paragraph('4.2  CGE Invariants (CGE-INV-001–007)', S['h2']))
    story.append(make_table(
        ['Invariant', 'Statement', 'Violation Consequence'],
        [
            ['CGE-INV-001', 'For every evaluation with CGE_ENABLED, a CAT with ≥1 CFR MUST be produced and persisted', 'CGE_INCOMPLETE flag on primary record'],
            ['CGE-INV-002', 'Primary decision MUST be identical whether or not CGE_ENABLED', 'Critical structural defect — CGE cannot influence primary'],
            ['CGE-INV-003', 'Every CFR MUST carry a valid ML-DSA-65 signature', 'Unsigned CFR rejected from CAT'],
            ['CGE-INV-004', 'cat_root_hash = sha256(sorted(cfr_content_hashes))', 'CAT seal verification fails if root_hash tampered'],
            ['CGE-INV-005', '|VV field delta| ≤ CGE_MAX_VARIATION_PCT (max 0.40)', 'VV rejected, logged CGE_VV_BOUND_VIOLATION'],
            ['CGE-INV-006', 'atf_counterfactual_forks and _tokens are append-only', 'UPDATE/DELETE on these tables prohibited in production'],
            ['CGE-INV-007', 'CAT must be independently verifiable without platform access', 'Verification procedure failure = structural defect'],
        ], S, col_widths=[2.8*cm, 7.5*cm, 6.5*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — GUGT
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('5.  Grand Unified Governance Theory (GUGT)', S['h1']))
    story.append(rule(S))
    story.append(Paragraph(
        'The GUGT establishes a formal meta-layer above the ATF protocol stack. It derives six '
        'Universal Governance Invariants (UGI-001–006) by formal intersection of the five major '
        'regulatory frameworks, establishing the minimal sufficient set of properties for '
        'Multi-Frame Completeness (MFC).', S['body']))

    story.append(Paragraph('5.1  UGI Derivation — Framework Intersection', S['h2']))
    framework_intersection = """\
  ┌───────────────────────────────────────────────────────────────────────────┐
  │         FIVE-FRAMEWORK INTERSECTION → SIX UNIVERSAL INVARIANTS           │
  │                                                                           │
  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────┐  ┌───────┐  │
  │  │ EU AI Act  │  │ NIST AI    │  │ GCC/DIFC   │  │ISO     │  │UK     │  │
  │  │ 2024/1689  │  │ RMF v1.0   │  │ AI Reg     │  │42001   │  │AISI   │  │
  │  │ Art.9/11   │  │ GOVERN 1.1 │  │ 2024       │  │:2023   │  │§3-5   │  │
  │  │ Art.14/72  │  │ MAP 5.1    │  │ Art.8-14   │  │§6-9    │  │       │  │
  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └───┬────┘  └──┬────┘  │
  │        │               │               │             │            │       │
  │        └───────────────┴───────────────┴─────────────┴────────────┘       │
  │                                    │                                       │
  │                         ∩ INTERSECTION                                    │
  │                                    │                                       │
  │        ┌───────────────────────────▼───────────────────────────────┐      │
  │        │  UGI-001: Human Authority Anchor                          │      │
  │        │  UGI-002: Offline-Verifiable Decision Evidence            │      │
  │        │  UGI-003: Execution-Time Boundary Enforcement             │      │
  │        │  UGI-004: Pre-Committed Posture Assessment                │      │
  │        │  UGI-005: Self-Modification Prohibition                   │      │
  │        │  UGI-006: Self-Contained Evidence Reconstruction          │      │
  │        └───────────────────────────────────────────────────────────┘      │
  │                                                                           │
  │   ATF-compliant system satisfies all 6 UGIs BY CONSTRUCTION              │
  │   → GUGT-L3+ATF certification via single PQC-signed UIR                  │
  └───────────────────────────────────────────────────────────────────────────┘\
"""
    story.append(code_block(framework_intersection, S))
    story.append(sp(6))

    story.append(Paragraph('5.2  Universal Governance Invariants UGI-001–006', S['h2']))
    story.append(make_table(
        ['UGI', 'Property', 'ATF Mechanism', 'Key Framework Clauses'],
        [
            ['UGI-001', 'Human Authority Anchor — cryptographic chain to identified human principal, offline-verifiable',
             'DR chain_root_id → Tier-1 human (ATF-INV-002, ATF-INV-006)',
             'EU Art.14/17 · NIST GOVERN 1.1 · GCC Art.8 · ISO §6.2'],
            ['UGI-002', 'Offline-Verifiable Decision Evidence — any authorized party verifies without platform contact',
             'OEP two-phase PQC seal (OEP-INV-001–006, FEA-INV-001–005)',
             'EU Art.11/12 · NIST MAP 5.2 · GCC Art.12 · ISO §9.1'],
            ['UGI-003', 'Execution-Time Boundary Enforcement — controls enforced at execution, not post-hoc',
             'RCR HALT at nanosecond precision (RGC-INV-003, RGC-INV-005)',
             'EU Art.9 · NIST MANAGE 2.2 · GCC Art.9 · ISO §8.4'],
            ['UGI-004', 'Pre-Committed Posture Assessment — input state committed before output computed',
             'posture_state_hash computed over committed fields BEFORE content_hash (ATF-INV-003)',
             'EU Art.9(7) · NIST MEASURE 2.5 · ISO §8.5'],
            ['UGI-005', 'Self-Modification Prohibition — authority parameters cannot be self-modified',
             'Auto-Modification Guard (AMG, ADR-144): max 10%/event, 30% cumulative',
             'EU Art.14(4) · NIST GOVERN 6.1 · GCC Art.10 · ISO §6.1.2'],
            ['UGI-006', 'Self-Contained Evidence Reconstruction — complete chain from receipt alone',
             'OEP package: DR→TAR→RCR→Receipt with embedded public key (ADR-165)',
             'EU Art.18/72 · NIST MAP 5.1 · GCC Art.14 · ISO §9.3'],
        ], S, col_widths=[1.5*cm, 4.8*cm, 4.5*cm, 5.5*cm]))
    story.append(sp(6))

    story.append(Paragraph('5.3  GUGT Conformance Levels', S['h2']))
    story.append(make_table(
        ['Level', 'UGIs Required', 'Additional Requirements', 'Who Qualifies'],
        [
            ['GUGT-L1 Basic', 'UGI-001 + UGI-002', 'Human anchor + offline verification', 'Any governance system with identity chain'],
            ['GUGT-L2 Runtime', 'L1 + UGI-003 + UGI-004', 'Execution enforcement + pre-committed assessment', 'Runtime-enforcement systems'],
            ['GUGT-L3 Full', 'L2 + UGI-005 + UGI-006', 'Self-mod prohibition + self-contained evidence', 'Full-stack governance systems'],
            ['GUGT-L3+ATF', 'GUGT-L3 + full ATF stack', 'All 88 ATF invariants (RFC-ATF-1 through RFC-ATF-5)', 'ATF-CGL-Compliant systems — by construction'],
        ], S, col_widths=[2.8*cm, 3.5*cm, 5.0*cm, 5.5*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 6 — TGB
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('6.  Temporal Governance Bridge (TGB)', S['h1']))
    story.append(rule(S))
    story.append(Paragraph(
        'AI governance operates simultaneously at two radically different scales: nanoseconds (runtime '
        'enforcement) and years (regulatory review). No prior governance protocol provides a formal '
        'bridge between them. The TGB provides this bridge via three record types.', S['body']))

    story.append(Paragraph('6.1  Two-Scale Architecture', S['h2']))
    tgb_architecture = """\
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                    TGB TWO-SCALE ARCHITECTURE                           │
  │                                                                         │
  │  MICRO-SCALE  ──────────────────────────────────────────────────────   │
  │  Nanoseconds to seconds                                                 │
  │  ┌──────────────────────────────────────────────────────────────────┐  │
  │  │  T=0 ns:  Primary ATF record issued                              │  │
  │  │  T=100ns: TCS embedded  ←──── Regulatory context captured here   │  │
  │  │           ├── eu_ai_act_version: "EU_AI_ACT_2024_v1.0"           │  │
  │  │           ├── atf_spec_version:  "RFC-ATF-5_v1.0"               │  │
  │  │           ├── nominal_threshold: 80.0                            │  │
  │  │           └── tcs_seal: ML-DSA-65 ✓                             │  │
  │  └──────────────────────────────────────────────────────────────────┘  │
  │           │                                                             │
  │           │ Evidence lifecycle transitions (RFC-ATF-3)                 │
  │           ▼                                                             │
  │  ┌──────────────────────────────────────────────────────────────────┐  │
  │  │  T=6 months:  HOT → WARM transition                              │  │
  │  │  TMR-001 issued: regulatory_context at transition captured        │  │
  │  │  T=3 years:   WARM → COLD transition                             │  │
  │  │  TMR-002 issued: regulatory_context at transition captured        │  │
  │  └──────────────────────────────────────────────────────────────────┘  │
  │           │                                                             │
  │  MACRO-SCALE  ──────────────────────────────────────────────────────   │
  │  Months to years (EU AI Act 7-year retention)                          │
  │  ┌──────────────────────────────────────────────────────────────────┐  │
  │  │  T=7 years:  Regulatory audit                                    │  │
  │  │  Auditor requests: "What did this NOMINAL mean in 2026?"         │  │
  │  │  RAR produced: source_tcs_id → project to EU_AI_ACT_2033_v3.0   │  │
  │  │  ├── field_projections: NOMINAL → [mapped value]                 │  │
  │  │  ├── original_record_integrity: VERIFIED                         │  │
  │  │  └── rar_seal: ML-DSA-65 ✓  (TGB-INV-002: source unchanged)    │  │
  │  └──────────────────────────────────────────────────────────────────┘  │
  │                                                                         │
  │  KEY: RAR projects context — never modifies source record              │
  └─────────────────────────────────────────────────────────────────────────┘\
"""
    story.append(code_block(tgb_architecture, S))
    story.append(sp(6))

    story.append(Paragraph('6.2  TGB Invariants (TGB-INV-001–005)', S['h2']))
    story.append(make_table(
        ['Invariant', 'Statement', 'Enforcement Mechanism'],
        [
            ['TGB-INV-001', 'Mandatory TCS embedding — every ATF record MUST carry a TCS when TGB_ENABLED=true', 'TCS construction synchronous with primary record; failure flags TGB_INCOMPLETE and retries async'],
            ['TGB-INV-002', 'RAR non-destruction — RAR MUST NOT modify any source record field or TCS', 'tcs_hash in posture_state_hash: any TCS modification detectable from primary record content_hash'],
            ['TGB-INV-003', 'Offline RAR computability — any party can compute a RAR from source record + TCS + rulebook', 'TGB projection rulebook PQC-sealed and publishable; no platform contact required'],
            ['TGB-INV-004', 'Projection monotonicity — framework revision CANNOT silently invalidate a record', 'Any invalidity requires explicit EID persisted in atf_regulatory_alignment_receipts'],
            ['TGB-INV-005', 'TMR and RAR PQC sealing — both record types require ML-DSA-65 seal', 'Unsigned TMR or RAR rejected; same key as primary records'],
        ], S, col_widths=[2.8*cm, 6.5*cm, 7.5*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 7 — FORMAL VERIFICATION
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('7.  Formal Verification (OMNIX-FVS-1.0 Extension)', S['h1']))
    story.append(rule(S))
    story.append(Paragraph(
        'RFC-ATF-5 extends OMNIX-FVS-1.0 with CGL-specific proof targets. All arithmetic '
        'invariants return UNSAT under the Z3 SMT solver. Dual methodology (Z3 + TLA+) '
        'established in RFC-ATF-4 is maintained — this remains the only AI governance standard '
        'with machine-checkable proofs across both continuous arithmetic domain and discrete '
        'state-machine traces.', S['body']))
    story.append(make_table(
        ['Proof Target', 'Solver', 'Property', 'Result'],
        [
            ['CGE-FRAGILITY-BOUND-LO', 'Z3 SMT', 'fragility_score ≥ 0.0 for all real inputs', 'UNSAT'],
            ['CGE-FRAGILITY-BOUND-HI', 'Z3 SMT', 'fragility_score ≤ 1.0 for all real inputs', 'UNSAT'],
            ['CGE-VV-BOUND',           'Z3 SMT', '|VV delta| ≤ 0.40 enforced for all fields', 'UNSAT'],
            ['CGE-PRIMARY-ISOLATION',  'Z3 SMT', 'CGE output does not modify primary record fields', 'UNSAT'],
            ['GUGT-UGI-MONOTONICITY',  'Z3 SMT', 'GUGT-Lk satisfaction implies GUGT-Lj (j < k)', 'UNSAT'],
            ['GUGT-6-UGI-COMPLETENESS','Z3 SMT', 'GUGT_COMPLIANT iff all 6 UGIs PASS', 'UNSAT'],
            ['TGB-PROJECTION-MONOTONE','Z3 SMT', 'Projection cannot increase compliance level without rule change', 'UNSAT'],
            ['TGB-NON-DESTRUCTION',    'Z3 SMT', 'RAR production leaves source_record_hash unchanged', 'UNSAT'],
            ['ATF-INV-001 (inherited)','TLA+',   'Monotonic authority reduction — re-verified for CGL extension', 'PASS'],
            ['ATF-INV-004 (inherited)','TLA+',   'Authority budget non-negative across all CGL paths', 'PASS'],
            ['RGC-INV-004 (inherited)','TLA+',   'HALT propagation preserved when TCS embedding active', 'PASS'],
        ], S, col_widths=[4.0*cm, 1.8*cm, 8.0*cm, 1.8*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 8 — COMBINED INVARIANT SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('8.  Combined Invariant Summary — 88 Total', S['h1']))
    story.append(rule(S))
    story.append(Paragraph(
        'RFC-ATF-5 introduces 18 new invariants across three protocol families. Combined with the '
        '70 invariants from RFC-ATF-1 through RFC-ATF-4, the complete ATF stack encompasses '
        '<b>88 formally specified invariants</b> across 17 protocol families.', S['body']))
    story.append(make_table(
        ['Family', 'RFC', 'Count', 'Scope'],
        [
            ['ATF-INV',  'ATF-1', '6',  'Identity & Delegation'],
            ['RGC-INV',  'ATF-2', '8',  'Runtime Continuity'],
            ['GPIL-INV', 'ATF-3', '3',  'Governance Policy Interoperability'],
            ['ELR-INV',  'ATF-3', '4',  'Evidence Lifecycle'],
            ['EAP-INV',  'ATF-3', '7',  'Evidence Archive Pipeline'],
            ['OEP-INV',  'ATF-3', '6',  'OMNIX Evidence Package'],
            ['FEA-INV',  'ATF-3', '5',  'Forensic Export Authorization'],
            ['FVP-INV',  'ATF-3', '1',  'Forensic Verification Protocol'],
            ['GECR-INV', 'ATF-3', '6',  'Governance Execution Context Record'],
            ['SGIP-INV', 'ATF-3', '4',  'Semantic Governance Interop Protocol'],
            ['DSPP-INV', 'ATF-4', '7',  'Dynamic Semantic Portability Protocol'],
            ['AGV-INV',  'ATF-4', '6',  'Anticipatory Governance Veto'],
            ['SSD-INV',  'ATF-4', '3',  'Structural Shift Detection'],
            ['FVS-INV',  'ATF-4', '3',  'Formal Verification Suite'],
            ['CGE-INV',  'ATF-5', '7',  'Counterfactual Governance Engine  ★ new'],
            ['GUGT-INV', 'ATF-5', '6',  'Grand Unified Governance Theory   ★ new'],
            ['TGB-INV',  'ATF-5', '5',  'Temporal Governance Bridge         ★ new'],
            ['TOTAL',    '—',    '88', 'Complete ATF Protocol Stack'],
        ], S, col_widths=[2.8*cm, 2.0*cm, 1.5*cm, 10.5*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 9 — COMPLIANCE DESIGNATION
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('9.  Compliance Designation: ATF-CGL-Compliant', S['h1']))
    story.append(rule(S))
    compliance_hierarchy = """\
  ATF COMPLIANCE HIERARCHY:

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  ATF-CGL-Compliant   (RFC-ATF-1+2+3+4+5) ── 88 invariants  ★ HIGHEST │
  ├─────────────────────────────────────────────────────────────────────────┤
  │  ATF-PGL-Compliant   (RFC-ATF-1+2+3+4)   ── 70 invariants             │
  ├─────────────────────────────────────────────────────────────────────────┤
  │  ATF-FEI-Compliant   (RFC-ATF-1+2+3)     ── 40 invariants             │
  ├─────────────────────────────────────────────────────────────────────────┤
  │  ATF-RGC-Compliant   (RFC-ATF-1+2)        ── 14 invariants             │
  ├─────────────────────────────────────────────────────────────────────────┤
  │  ATF-Compliant-L1/2/3 (RFC-ATF-1)         ──  6 invariants             │
  └─────────────────────────────────────────────────────────────────────────┘

  ATF-CGL-Compliant requirements (all five conditions required):
  (a) ATF-PGL-Compliant — all RFC-ATF-1/2/3/4 requirements satisfied
  (b) CGE operational — CGE_ENABLED=true, CGE_FORK_COUNT in [1,7],
      all CGE-INV-001–007 satisfied
  (c) GUGT UIR issued — at least one GUGT-L3+ATF UIR issued and
      verified for the deployment
  (d) TGB operational — TGB_ENABLED=true, all ATF records carry TCS,
      all TGB-INV-001–005 satisfied
  (e) CGL formal verification — OMNIX-FVS-1.0 extension runs all CGL
      proof targets with result = UNSAT for all Z3 proofs\
"""
    story.append(code_block(compliance_hierarchy, S))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 10 — NOVEL CONTRIBUTIONS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('10.  Novel Contributions', S['h1']))
    story.append(rule(S))
    story.append(make_table(
        ['Contribution', 'Description', 'Prior Art'],
        [
            ['Counterfactual Attestation Token (CAT)',
             'M PQC-sealed alternative governance paths per evaluation, with fragility_score and offline-verifiable decision space',
             'VeriSigil, IBM OpenScale, Microsoft Azure RAI, Google Model Cards — none record decision space'],
            ['fragility_score',
             'Continuous [0.0, 1.0] metric quantifying governance decision robustness — proportion of counterfactual paths diverging from primary',
             'No equivalent in any published governance specification'],
            ['Universal Governance Invariants (UGI-001–006)',
             'Formally derived minimal set by intersection analysis of 5 major regulatory frameworks simultaneously',
             'VeriSigil VGS, NIST AI RMF, EU AI Act guidance — all jurisdiction-specific, none derive intersection'],
            ['Universal Invariant Receipt (UIR)',
             'PQC-signed cross-framework, cross-agent-type certification artifact — one receipt for EU+US+GCC+ISO simultaneously',
             'No cross-framework PQC-signed certification artifact exists in any published specification'],
            ['Temporal Context Snapshot (TCS)',
             'First record type designed to capture complete regulatory context at nanosecond of record creation',
             'Prior frameworks embed timestamps but not the interpretive framework under which the timestamp was produced'],
            ['Regulatory Alignment Receipt (RAR)',
             'First mechanism for projecting historical governance records to current regulatory frameworks without modifying original evidence',
             'No non-destructive, offline-computable temporal projection mechanism in any governance standard'],
            ['ATF-CGL-Compliant',
             'First five-tier AI governance compliance designation spanning identity/runtime/evidence/proactive/cognitive — 88 invariants',
             'No multi-tier, formally verified, PQC-backed compliance hierarchy exists in any published AI governance specification'],
        ], S, col_widths=[3.5*cm, 7.5*cm, 5.8*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 11 — DISTINCTION FROM PRIOR ART
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('11.  Distinction from Prior Art', S['h1']))
    story.append(rule(S))
    story.append(make_table(
        ['Feature', 'RFC-ATF-5', 'VeriSigil VGS', 'IBM OpenScale', 'MS Azure RAI'],
        [
            ['Decision space evidence',    '✓ CAT (PQC)',   '✗', '✗', '✗'],
            ['Offline CAT verification',   '✓',            '✗', '✗', '✗'],
            ['fragility_score',            '✓',            '✗', '✗', '✗'],
            ['Universal invariant set',    '✓ UGI-001–006','✗', '✗', '✗'],
            ['PQC-signed UIR',             '✓ ML-DSA-65',  '✗', '✗', '✗'],
            ['Multi-jurisdiction UIR',     '✓ EU+US+GCC+ISO','Partial','✗','Partial'],
            ['TCS at record issuance',     '✓',            '✗', '✗', '✗'],
            ['Non-destructive RAR',        '✓',            '✗', '✗', '✗'],
            ['7-year retention support',   '✓ TMR',        '✗', '✗', '✗'],
            ['Formal Z3 proof targets',    '✓ 8+',         '4', '✗', '✗'],
            ['Dual Z3 + TLA+',             '✓',            '✗', '✗', '✗'],
        ], S, col_widths=[5.0*cm, 3.2*cm, 2.8*cm, 2.8*cm, 2.8*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 12 — REGULATORY ALIGNMENT
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('12.  Regulatory Alignment', S['h1']))
    story.append(rule(S))
    story.append(make_table(
        ['Framework', 'CGE', 'GUGT', 'TGB'],
        [
            ['EU AI Act Art. 9',   '"Alternatives considered" documentation — CAT satisfies with PQC artifacts', 'Complete risk management system', 'Art. 9(7): assessment integrity over time'],
            ['EU AI Act Art. 72',  '—', 'Art. 72: 7-year retention compliance', 'TMR at each lifecycle transition'],
            ['NIST AI RMF MAP 1.6','Alternative scenario documentation', 'MAP 5.1/5.2: complete impact docs', 'MAP 5.2: lifecycle documentation'],
            ['GCC/DIFC Arts. 8–14','Continuous alternatives assessment', 'Complete Art. 8–14 coverage via UIR', 'Art. 12/14: audit trail across revisions'],
            ['ISO 42001 §6.1.2',   'Risk treatment alternatives', '§6.1.2/8.4/8.5/9.3 complete coverage', '§9.1/9.3: management review with historical trends'],
            ['SOC 2 Type II CC7.2','—', 'Monitoring evidence trail', 'Change documentation'],
        ], S, col_widths=[3.5*cm, 4.8*cm, 4.0*cm, 4.5*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # REFERENCES
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('References', S['h1']))
    story.append(rule(S))
    refs = [
        ('[RFC-ATF-1]', 'Nunes, H., "RFC-ATF-1: Agent Trust Fabric Delegation Protocol", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20155016'),
        ('[RFC-ATF-2]', 'Nunes, H., "RFC-ATF-2: Agent Trust Fabric — Runtime Governance Continuity", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20241344'),
        ('[RFC-ATF-3]', 'Nunes, H., "RFC-ATF-3: Agent Trust Fabric — Governance Policy Interoperability, Evidence Lifecycle, and Forensic Verification Protocol", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20247342'),
        ('[RFC-ATF-4]', 'Nunes, H., "RFC-ATF-4: Agent Trust Fabric — Proactive Governance Layer", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20368895'),
        ('[FIPS204]',   'NIST, "Module-Lattice-Based Digital Signature Standard (ML-DSA)", FIPS 204, August 2024.'),
        ('[Z3]',        'de Moura, L. and Bjørner, N., "Z3: An Efficient SMT Solver", TACAS 2008, LNCS 4963, pp. 337-340.'),
        ('[TLA+]',      'Lamport, L., "Specifying Systems: The TLA+ Language and Tools", Addison-Wesley, 2002.'),
        ('[EU-AI-ACT]', 'European Parliament, "Regulation (EU) 2024/1689 on Artificial Intelligence", Official Journal of the EU, July 2024.'),
        ('[NIST-AI-RMF]','NIST, "Artificial Intelligence Risk Management Framework", NIST AI 100-1, January 2023.'),
        ('[ISO-42001]', 'ISO/IEC, "Artificial Intelligence — Management System", ISO/IEC 42001:2023.'),
        ('[ADR-178]',   'Nunes, H., "ADR-178: Counterfactual Governance Engine (CGE)", OMNIX QUANTUM, May 2026.'),
        ('[ADR-179]',   'Nunes, H., "ADR-179: Grand Unified Governance Theory (GUGT)", OMNIX QUANTUM, May 2026.'),
        ('[ADR-180]',   'Nunes, H., "ADR-180: Temporal Governance Bridge (TGB)", OMNIX QUANTUM, May 2026.'),
    ]
    for cite, text in refs:
        story.append(Paragraph(f'<b><font color="#8b8bf0">{cite}</font></b>  {text}', S['ref']))
        story.append(sp(2))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # AUTHOR / CLOSING
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('Author\'s Address', S['h1']))
    story.append(rule(S))
    story.append(sp(10))
    story.append(gold_box([
        Paragraph('Harold Alberto Nunes Rodelo (Editor)', S['gold']),
        sp(4),
        Paragraph('OMNIX QUANTUM LTD', S['abstract_body']),
        Paragraph('71-75 Shelton Street, Covent Garden', S['abstract_body']),
        Paragraph('London WC2H 9JQ, England', S['abstract_body']),
        Paragraph('Operational Headquarters: Abu Dhabi, UAE', S['abstract_body']),
        sp(4),
        Paragraph('Email: standards@omnixquantum.com', S['abstract_body']),
        Paragraph('Web:   omnixquantum.net', S['abstract_body']),
        sp(8),
        Paragraph('RFC-ATF-5 Version 1.0.0 — May 2026', S['caption']),
        Paragraph('Priority Records: OMNIX-PAR-2026-CGE-001 · OMNIX-PAR-2026-GUGT-001 · OMNIX-PAR-2026-TGB-001', S['caption']),
        Paragraph('DRAFT — pending submission to Zenodo', S['caption']),
    ], S))

    # ── Build ─────────────────────────────────────────────────────────────────
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
    doc.build(story,
        onFirstPage=cover_page,
        onLaterPages=normal_page)
    print(f'\n  PDF generated: {output_path}')
    print(f'  Size: {os.path.getsize(output_path) / 1024:.0f} KB')

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else OUT_PATH
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print(f'Generating RFC-ATF-5 PDF...')
    print(f'  Logo: {LOGO_PATH} {"✓" if os.path.exists(LOGO_PATH) else "✗ NOT FOUND"}')
    build_pdf(out)
