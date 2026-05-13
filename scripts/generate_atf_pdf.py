"""
Professional PDF generator for OMNIX-WP-ATF-2026-001
RFC-ATF-1 — Agent Trust Fabric Whitepaper
"""
import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Preformatted, Image
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

# ── Colors ────────────────────────────────────────────────────────────────────
DARK_BG      = colors.HexColor('#0d0d1a')
ACCENT_BLUE  = colors.HexColor('#5b5bd6')
ACCENT_LIGHT = colors.HexColor('#8b8bf0')
TEXT_WHITE   = colors.HexColor('#f0f0f0')
TEXT_GRAY    = colors.HexColor('#aaaaaa')
BORDER_GRAY  = colors.HexColor('#333355')
CODE_BG      = colors.HexColor('#1a1a2e')
TABLE_HEAD   = colors.HexColor('#1e1e3a')
TABLE_ALT    = colors.HexColor('#141428')
TABLE_BORDER = colors.HexColor('#2a2a4a')
RULE_COLOR   = colors.HexColor('#3a3a5a')
WHITE        = colors.white
BLACK        = colors.black

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm

# ── Page decorator ────────────────────────────────────────────────────────────
def cover_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Accent bar top
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, PAGE_H - 8*mm, PAGE_W, 8*mm, fill=1, stroke=0)
    # Accent bar bottom
    canvas.rect(0, 0, PAGE_W, 6*mm, fill=1, stroke=0)
    canvas.restoreState()

def normal_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Top accent line
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, PAGE_H - 4*mm, PAGE_W, 4*mm, fill=1, stroke=0)
    # Bottom bar
    canvas.setFillColor(TABLE_HEAD)
    canvas.rect(0, 0, PAGE_W, 12*mm, fill=1, stroke=0)
    # Footer text left
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(TEXT_GRAY)
    canvas.drawString(MARGIN, 4*mm, 'OMNIX-WP-ATF-2026-001 · RFC-ATF-1 Agent Trust Fabric · OMNIX QUANTUM LTD')
    # Footer page number right
    canvas.drawRightString(PAGE_W - MARGIN, 4*mm, f'Page {doc.page}')
    # Separator line
    canvas.setStrokeColor(RULE_COLOR)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 12*mm, PAGE_W - MARGIN, 12*mm)
    canvas.restoreState()

# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    s = {}

    s['cover_title'] = ParagraphStyle('cover_title',
        fontName='Helvetica-Bold', fontSize=28, leading=36,
        textColor=WHITE, alignment=TA_LEFT, spaceAfter=6)

    s['cover_subtitle'] = ParagraphStyle('cover_subtitle',
        fontName='Helvetica', fontSize=16, leading=22,
        textColor=ACCENT_LIGHT, alignment=TA_LEFT, spaceAfter=20)

    s['cover_meta'] = ParagraphStyle('cover_meta',
        fontName='Helvetica', fontSize=10, leading=16,
        textColor=TEXT_GRAY, alignment=TA_LEFT, spaceAfter=4)

    s['cover_badge'] = ParagraphStyle('cover_badge',
        fontName='Helvetica-Bold', fontSize=9, leading=14,
        textColor=ACCENT_BLUE, alignment=TA_LEFT, spaceAfter=4)

    s['abstract_title'] = ParagraphStyle('abstract_title',
        fontName='Helvetica-Bold', fontSize=10, leading=14,
        textColor=ACCENT_LIGHT, alignment=TA_LEFT,
        spaceBefore=4, spaceAfter=4, leftIndent=0)

    s['abstract_body'] = ParagraphStyle('abstract_body',
        fontName='Helvetica', fontSize=9.5, leading=15,
        textColor=TEXT_WHITE, alignment=TA_JUSTIFY,
        spaceBefore=0, spaceAfter=6)

    s['h1'] = ParagraphStyle('h1',
        fontName='Helvetica-Bold', fontSize=15, leading=20,
        textColor=WHITE, alignment=TA_LEFT,
        spaceBefore=18, spaceAfter=8)

    s['h2'] = ParagraphStyle('h2',
        fontName='Helvetica-Bold', fontSize=11.5, leading=16,
        textColor=ACCENT_LIGHT, alignment=TA_LEFT,
        spaceBefore=14, spaceAfter=5)

    s['h3'] = ParagraphStyle('h3',
        fontName='Helvetica-Bold', fontSize=10, leading=14,
        textColor=TEXT_GRAY, alignment=TA_LEFT,
        spaceBefore=10, spaceAfter=4)

    s['body'] = ParagraphStyle('body',
        fontName='Helvetica', fontSize=9.5, leading=15,
        textColor=TEXT_WHITE, alignment=TA_JUSTIFY,
        spaceBefore=0, spaceAfter=6)

    s['bullet'] = ParagraphStyle('bullet',
        fontName='Helvetica', fontSize=9.5, leading=15,
        textColor=TEXT_WHITE, alignment=TA_LEFT,
        leftIndent=16, firstLineIndent=-8,
        spaceBefore=1, spaceAfter=1)

    s['code'] = ParagraphStyle('code',
        fontName='Courier', fontSize=7.5, leading=11,
        textColor=ACCENT_LIGHT, alignment=TA_LEFT,
        leftIndent=4, spaceBefore=0, spaceAfter=0,
        backColor=CODE_BG)

    s['caption'] = ParagraphStyle('caption',
        fontName='Helvetica-Oblique', fontSize=8, leading=12,
        textColor=TEXT_GRAY, alignment=TA_CENTER, spaceBefore=2)

    s['toc_entry'] = ParagraphStyle('toc_entry',
        fontName='Helvetica', fontSize=9.5, leading=16,
        textColor=TEXT_WHITE, leftIndent=0)

    s['toc_section'] = ParagraphStyle('toc_section',
        fontName='Helvetica-Bold', fontSize=10, leading=16,
        textColor=WHITE, leftIndent=0)

    s['ref'] = ParagraphStyle('ref',
        fontName='Helvetica', fontSize=8.5, leading=13,
        textColor=TEXT_GRAY, leftIndent=16, firstLineIndent=-16,
        spaceBefore=2, spaceAfter=0)

    return s

# ── Code block helper ─────────────────────────────────────────────────────────
def code_block(text, styles):
    lines = text.strip().split('\n')
    rows = []
    for line in lines:
        # Escape for Paragraph
        safe = line.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        rows.append(Paragraph(safe, styles['code']))
    inner = Table([[r] for r in rows],
        colWidths=[PAGE_W - 2*MARGIN - 16*mm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER_GRAY),
        ]))
    return inner

# ── Table helper ──────────────────────────────────────────────────────────────
def make_table(headers, rows, styles, col_widths=None):
    head_style = ParagraphStyle('th',
        fontName='Helvetica-Bold', fontSize=8, leading=12,
        textColor=ACCENT_LIGHT, alignment=TA_LEFT)
    cell_style = ParagraphStyle('td',
        fontName='Helvetica', fontSize=8, leading=12,
        textColor=TEXT_WHITE, alignment=TA_LEFT)
    cell_gray = ParagraphStyle('tdg',
        fontName='Helvetica', fontSize=8, leading=12,
        textColor=TEXT_GRAY, alignment=TA_LEFT)

    data = [[Paragraph(h, head_style) for h in headers]]
    for i, row in enumerate(rows):
        r = []
        for j, cell in enumerate(row):
            st = cell_gray if j == 0 and len(headers) > 2 else cell_style
            r.append(Paragraph(str(cell), st))
        data.append(r)

    avail = PAGE_W - 2*MARGIN - 4*mm
    if col_widths is None:
        w = avail / len(headers)
        col_widths = [w] * len(headers)

    ts = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TABLE_HEAD),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [TABLE_ALT, CODE_BG]),
        ('GRID', (0,0), (-1,-1), 0.4, TABLE_BORDER),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ])
    return Table(data, colWidths=col_widths, style=ts, repeatRows=1)

def rule(styles):
    return HRFlowable(width='100%', thickness=0.5, color=RULE_COLOR, spaceAfter=6, spaceBefore=6)

def sp(n=6):
    return Spacer(1, n)

# ── Build document ────────────────────────────────────────────────────────────
def build_pdf(output_path):
    S = make_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 10*mm, bottomMargin=MARGIN + 10*mm,
        title='RFC-ATF-1 — Agent Trust Fabric',
        author='Harold Nunes, OMNIX QUANTUM LTD',
        subject='Post-quantum cryptographic protocol for AI agent authority governance',
    )

    story = []

    # ── COVER PAGE ────────────────────────────────────────────────────────────
    story.append(sp(30))

    # Logo + title side by side: logo right, text left
    LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             'omnix_web', 'public', 'logo_nobg.png')
    logo_w = 4.5 * cm
    logo_h = logo_w * (380 / 522)   # maintain aspect ratio

    title_col = [
        Paragraph('RFC-ATF-1', S['cover_badge']),
        sp(6),
        Paragraph('Agent Trust Fabric', S['cover_title']),
        Paragraph('Cryptographic Authority Governance<br/>for Autonomous AI Agents', S['cover_subtitle']),
    ]
    logo_cell = Image(LOGO_PATH, width=logo_w, height=logo_h)

    cover_top = Table(
        [[title_col, logo_cell]],
        colWidths=[PAGE_W - 2*MARGIN - logo_w - 8*mm, logo_w + 4*mm],
        style=TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ])
    )
    story.append(cover_top)
    story.append(sp(20))
    story.append(HRFlowable(width='40%', thickness=1.5, color=ACCENT_BLUE, spaceAfter=20))

    meta = [
        ('Document',        'OMNIX-WP-ATF-2026-001'),
        ('Version',         '1.0.0'),
        ('Date',            'May 2026'),
        ('Author',          'Harold Nunes'),
        ('Institution',     'OMNIX QUANTUM LTD'),
        ('Contact',         'harold@omnixquantum.com'),
        ('Protocol',        'RFC-ATF-1 · ADR-156/157/158'),
        ('Classification',  'Public — Institutional Distribution'),
        ('Cryptography',    'ML-DSA-65 (NIST FIPS 204 / CRYSTALS-Dilithium)'),
        ('Formal Methods',  'TLA+ Model Checked — 5 invariants'),
        ('Repository',      'github.com/Costenho19/rfc-atf-1'),
    ]
    for label, value in meta:
        story.append(Paragraph(f'<b><font color="#5b5bd6">{label}:</font></b>  {value}', S['cover_meta']))

    story.append(sp(30))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER_GRAY, spaceAfter=12))

    abstract_box = Table([[
        [
            Paragraph('Abstract', S['abstract_title']),
            Paragraph(
                'Autonomous AI agents increasingly make consequential decisions in enterprise systems — '
                'executing trades, authorizing medical procedures, routing logistics, and managing critical '
                'infrastructure. Yet the governance of <i>who authorized these agents, under what authority, '
                'and whether that authority was valid at the moment of execution</i> remains unaddressed by '
                'existing frameworks.',
                S['abstract_body']),
            Paragraph(
                'This paper presents the OMNIX Agent Trust Fabric (ATF) — a formally specified, '
                'post-quantum cryptographic protocol that answers four questions for every AI agent execution: '
                '(1) Who authorized this agent? — via ML-DSA-65 signed Delegation Receipt; '
                '(2) What authority did it hold? — via Monotonic Authority Reduction, TLA+ verified; '
                '(3) Was the authority valid at execution? — via Temporal Admissibility Record captured '
                'before the pipeline runs; '
                '(4) Is the full chain independently verifiable? — via offline CLI verifier, no platform access required.',
                S['abstract_body']),
        ]
    ]],
    colWidths=[PAGE_W - 2*MARGIN - 4*mm],
    style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
        ('BOX', (0,0), (-1,-1), 1, ACCENT_BLUE),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(abstract_box)

    story.append(PageBreak())

    # ── TABLE OF CONTENTS ─────────────────────────────────────────────────────
    story.append(Paragraph('Table of Contents', S['h1']))
    story.append(rule(S))
    toc_entries = [
        ('1.', 'Problem Statement'),
        ('1.1', 'The AI Agent Authorization Gap'),
        ('1.2', 'The Accountability Requirement'),
        ('1.3', 'Why Existing Protocols Are Insufficient'),
        ('2.', 'The ATF Protocol Architecture'),
        ('2.1', 'Core Concepts'),
        ('2.2', 'The Authority Lifecycle'),
        ('2.3', 'Authority Budget Arithmetic'),
        ('3.', 'Formal Invariants'),
        ('4.', 'Cryptographic Specification'),
        ('4.1', 'Signature Algorithm'),
        ('4.2', 'Content Hash Construction'),
        ('4.3', 'Fallback Mode'),
        ('5.', 'Temporal Admissibility (ADR-157)'),
        ('5.1', 'Why TAR Is Necessary'),
        ('5.2', 'TAR Issuance Protocol'),
        ('6.', 'Cross-Domain Trust Portability (ADR-158)'),
        ('6.1', 'Domain Translation Receipt'),
        ('6.2', 'Standard Domain-Pair Discount Policies'),
        ('7.', 'Governance Receipt Integration'),
        ('7.1', 'The Triple Chain'),
        ('7.2', 'Verification Flow'),
        ('8.', 'Independent Verifiability (ATF-INV-006)'),
        ('9.', 'Compliance Framework'),
        ('10.', 'Interoperability'),
        ('11.', 'Implementation Reference'),
        ('12.', 'Known Limitations and Open Questions'),
        ('13.', 'Related Work'),
        ('14.', 'Conclusion'),
        ('', 'References'),
    ]
    for num, title in toc_entries:
        indent = 16 if num and '.' in num and len(num) > 2 else 0
        st = ParagraphStyle('toc', fontName='Helvetica-Bold' if (num.endswith('.') and len(num) <= 2) or not num else 'Helvetica',
            fontSize=9.5, leading=16, textColor=WHITE if not num or len(num)<=2 else TEXT_WHITE,
            leftIndent=indent)
        dot_leader = '.' * 60
        story.append(Paragraph(f'{num}  {title}', st))
    story.append(sp(8))
    story.append(PageBreak())

    # ── SECTION 1 ─────────────────────────────────────────────────────────────
    story.append(Paragraph('1.  Problem Statement', S['h1']))
    story.append(rule(S))

    story.append(Paragraph('1.1  The AI Agent Authorization Gap', S['h2']))
    story.append(Paragraph(
        'Modern AI governance frameworks address <i>what decisions are made</i> but not <i>who authorized '
        'the agent that made them</i>. When an enterprise AI agent executes a high-stakes action, '
        'the audit record typically captures:', S['body']))
    for item in [
        'What decision was made',
        'What signals influenced the decision',
        'A cryptographic hash of the decision receipt',
    ]:
        story.append(Paragraph(f'• {item}', S['bullet']))
    story.append(sp(6))
    story.append(Paragraph('What is systematically missing:', S['body']))
    for item in [
        '<b>Proof that the agent was authorized to act</b> — not just authenticated, but explicitly authorized with bounded scope',
        '<b>Proof that the authority was valid at the nanosecond of execution</b> — not valid yesterday, not valid in principle, but valid <i>then</i>',
        '<b>A verifiable chain from the AI agent back to a human principal</b> — traceable without trusting the platform',
    ]:
        story.append(Paragraph(f'• {item}', S['bullet']))
    story.append(sp(6))
    story.append(Paragraph(
        'This gap is not a limitation of existing governance frameworks — it is not their design target. '
        'OAuth 2.0 handles access delegation; W3C Verifiable Credentials handle identity claims; '
        'JWT handles session validity. None was designed to answer: <i>"Was this autonomous AI agent\'s '
        'authority mathematically bounded and verified at the moment it executed this specific '
        'governance decision?"</i>', S['body']))

    story.append(Paragraph('1.2  The Accountability Requirement', S['h2']))
    story.append(Paragraph('Regulation is closing this gap:', S['body']))
    story.append(sp(4))
    story.append(make_table(
        ['Regulation', 'Requirement', 'ATF Response'],
        [
            ['EU AI Act Art. 13', 'Transparency for high-risk AI — "who authorized this system"', 'ATF DR chain to Tier-1 human'],
            ['EU AI Act Art. 14', 'Human oversight — human principal must be identifiable', 'ATF chain_root_id → Tier-1'],
            ['DORA Art. 9', 'ICT resilience — documented controls for automated systems', 'ATF TAR proves control at execution'],
            ['MiCA Rec. 65', 'Algorithmic trading controls — authorization audit trail', 'ATF triple chain for trading decisions'],
            ['NIST AI RMF GOVERN', 'AI decisions traceable to accountable entities', 'ATF cryptographic traceability'],
            ['SOC 2 CC6', 'Logical access controls — non-repudiation', 'ATF PQC signatures'],
        ], S,
        col_widths=[3.8*cm, 6.5*cm, 6.5*cm]
    ))
    story.append(sp(8))

    story.append(Paragraph('1.3  Why Existing Protocols Are Insufficient', S['h2']))
    story.append(make_table(
        ['Protocol', 'What It Provides', 'What It Cannot Provide'],
        [
            ['OAuth 2.0', 'Access token delegation', 'Monotonic authority bound; pre-execution temporal record; human chain traceability'],
            ['JWT (RFC 7519)', 'Signed claims with expiry', 'Authority budget arithmetic; separate admissibility artifact; offline chain verification'],
            ['W3C VC', 'Signed identity claims', 'Authority bounds; temporal admissibility; mandatory cross-domain reduction'],
            ['SPIFFE/SPIRE', 'Workload identity', 'Authority delegation chain; governance receipt integration'],
            ['OpenID Connect', 'Authentication', 'Authorization chain governance; PQC signatures; formal invariants'],
        ], S,
        col_widths=[3.2*cm, 5.8*cm, 7.8*cm]
    ))
    story.append(sp(6))
    story.append(Paragraph(
        'None of these protocols is wrong — they solve different problems. ATF addresses the gap that '
        'exists at the intersection of all of them: <b>authority governance for autonomous AI agents, '
        'before and during execution</b>.', S['body']))

    story.append(PageBreak())

    # ── SECTION 2 ─────────────────────────────────────────────────────────────
    story.append(Paragraph('2.  The ATF Protocol Architecture', S['h1']))
    story.append(rule(S))

    story.append(Paragraph('2.1  Core Concepts', S['h2']))
    concepts = [
        ('Agent Identity Record (AIR)',
         'Every AI agent registered in an ATF-compliant system receives a globally unique identifier: '
         '<font face="Courier" size="9">AID-{DOMAIN}-{16HEX}</font>. The AIR contains the agent\'s '
         'authority budget cap, domain, registration tier, and public key for verification.'),
        ('Delegation Receipt (DR / ATFDR-{16HEX})',
         'A PQC-signed record issued by a principal (human or agent) to an agent, explicitly granting '
         'a bounded subset of the principal\'s authority for a defined task scope. '
         'Content-hashed (SHA-256 over canonical JSON), signed with ML-DSA-65 (Dilithium-3, NIST FIPS 204), '
         'and independently verifiable offline using the embedded delegator public key.'),
        ('Temporal Admissibility Record (TAR / ATFTAR-{16HEX})',
         'A PQC-signed record issued at the exact moment of admission to the governance pipeline — '
         '<b>before any governance logic executes</b>. The TAR proves: (1) the DR was ACTIVE at '
         '<font face="Courier" size="9">execution_ns</font> (nanosecond-resolution); '
         '(2) the admission decision was ADMITTED or REJECTED; '
         '(3) the execution_ref binds this TAR to a specific GovernanceReceipt.'),
        ('Trust Lattice',
         'The directed acyclic graph (DAG) of all delegation receipts. The lattice enforces the '
         'Acyclicity invariant (ATF-INV-002) and provides chain traversal for complete authority verification.'),
        ('GovernanceReceipt',
         'The governance decision record (ADR-028), extended with atf_context embedding the DR, TAR, '
         'and trust summary — forming the three-artifact audit chain.'),
    ]
    for title, desc in concepts:
        story.append(KeepTogether([
            Paragraph(f'<b>{title}</b>', S['h3']),
            Paragraph(desc, S['body']),
            sp(4),
        ]))

    story.append(Paragraph('2.2  The Authority Lifecycle', S['h2']))
    lifecycle = """Phase 1 — Registration
  Human Tier-1 registers agent → AIR created → authority budget assigned

Phase 2 — Delegation
  Principal signs DR → authority_budget_granted ≤ authority_budget_delegator
  DR stored in trust lattice → chain_root_id set

Phase 3 — Admission
  Agent presents DR at execution boundary
  ATFConnector.admit() called BEFORE governance pipeline
  TAR issued: execution_ns captured, DR status verified, TAR signed
  TAR.execution_ref = GovernanceReceipt.receipt_id

Phase 4 — Execution
  Governance pipeline runs (AVM, AI, veto chain)
  Decision produced with PQC-signed GovernanceReceipt
  ATF context embedded: delegation_id, tar_id, authority_budget

Phase 5 — Verification
  Any party runs: python omnix_atf_verify.py receipt.json
  DR signature verified against embedded public key
  TAR status confirmed ADMITTED
  execution_ref cross-checked with GovernanceReceipt.receipt_id
  Chain root traced to Tier-1 human principal
  Result: VERIFIED or NOT VERIFIED"""
    story.append(code_block(lifecycle, S))
    story.append(sp(8))

    story.append(Paragraph('2.3  Authority Budget Arithmetic', S['h2']))
    story.append(Paragraph(
        'The authority budget is a real number in [0.0, 100.0] representing the fraction of full '
        'authority held by an agent. The Monotonic Authority Reduction (MAR) invariant requires:', S['body']))
    mar_formula = """For all DRs D in the trust lattice:
  D.authority_budget_granted ≤ D.authority_budget_delegator

For all chains C = [DR₁, DR₂, ..., DRₙ]:
  DR₁.authority_budget_granted ≥ DR₂.authority_budget_granted ≥ ... ≥ DRₙ.authority_budget_granted"""
    story.append(code_block(mar_formula, S))
    story.append(sp(4))
    story.append(Paragraph(
        'This invariant is formally specified in TLA+ and verified by model checking over bounded '
        'state spaces (ATF-FV-1.0). It ensures that delegation cannot <i>create</i> authority — '
        'only distribute and bound it.', S['body']))
    example_chain = """HUMAN-TIER1          budget = 100.0  (full authority)
  └─ ATFDR-ROOT  →   AID-FINANCE-001  budget = 80.0   (20% reduction)
       └─ ATFDR-A  → AID-FINANCE-002  budget = 50.0   (37.5% reduction)
            └─ ATFDR-B → AID-FINANCE-003  budget = 20.0   (60% reduction)"""
    story.append(sp(4))
    story.append(Paragraph('Example delegation chain:', S['h3']))
    story.append(code_block(example_chain, S))

    story.append(PageBreak())

    # ── SECTION 3 ─────────────────────────────────────────────────────────────
    story.append(Paragraph('3.  Formal Invariants', S['h1']))
    story.append(rule(S))
    story.append(Paragraph(
        'ATF-1.0 defines six formally specified invariants. All are mandatory for '
        'ATF-COMPLIANT-LEVEL-2 and above.', S['body']))
    story.append(sp(6))
    story.append(make_table(
        ['Invariant', 'Identifier', 'Formal Statement'],
        [
            ['Monotonic Authority Reduction', 'ATF-INV-001', 'DR.budget_granted ≤ DR.budget_delegator for all DRs'],
            ['Acyclicity', 'ATF-INV-002', 'The trust lattice is a DAG — no delegation cycle exists'],
            ['Chain Root Consistency', 'ATF-INV-003', 'All DRs in a chain share the same chain_root_id'],
            ['Content Hash Immutability', 'ATF-INV-004', 'DR fields are immutable post-issuance (hash binds all fields)'],
            ['Temporal Non-Future-Dating', 'ATF-INV-005', 'TAR execution_ns ≤ current time at verification'],
            ['Independent Verifiability', 'ATF-INV-006', 'Full chain verifiable offline using only receipts and root public key'],
        ], S,
        col_widths=[4.5*cm, 3.2*cm, 9.1*cm]
    ))
    story.append(sp(8))
    story.append(Paragraph(
        '<b>TLA+ Coverage:</b> INV-001 (MARInvariant), INV-002 (AcyclicityInvariant), '
        'INV-003 (ChainRootConsistency), and INV-004 (ImmutabilityProperty) are formally '
        'specified and model-checked in <font face="Courier" size="9">docs/formal/ATF-TLA-SPEC.tla</font>. '
        'This is the same formal verification methodology used by Amazon Web Services for DynamoDB.', S['body']))

    # ── SECTION 4 ─────────────────────────────────────────────────────────────
    story.append(Paragraph('4.  Cryptographic Specification', S['h1']))
    story.append(rule(S))

    story.append(Paragraph('4.1  Signature Algorithm', S['h2']))
    story.append(make_table(
        ['Property', 'Value'],
        [
            ['Algorithm', 'ML-DSA-65 (Dilithium-3)'],
            ['Standard', 'NIST FIPS 204 (August 2024)'],
            ['Security level', 'NIST PQC Level 3'],
            ['Public key size', '1,952 bytes'],
            ['Signature size', '3,293 bytes'],
            ['Hash function', 'SHA-256 (content hash construction)'],
            ['Encoding', 'Base64 standard (signature), hex (content hash)'],
        ], S, col_widths=[5*cm, 11.8*cm]
    ))
    story.append(sp(8))

    story.append(Paragraph('4.2  Content Hash Construction', S['h2']))
    story.append(Paragraph(
        'All ATF artifacts use a deterministic content hash for signature binding:', S['body']))
    hash_code = """canonical = json.dumps(fields, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
content_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()"""
    story.append(code_block(hash_code, S))
    story.append(sp(6))
    story.append(make_table(
        ['Artifact', 'Hashed Fields'],
        [
            ['DR', 'delegation_id, delegator_id, delegate_id, task_scope, authority_budget_granted, authority_budget_delegator, chain_root_id, delegation_depth, expires_at, status, created_at'],
            ['TAR', 'tar_id, delegation_id, agent_id, execution_ref, execution_ns, dr_status_at_admission, dr_expires_at, authority_budget, domain, task_action, admission_status, chain_root_id'],
            ['DTR', 'dtr_id, source_delegation_id, source_domain, target_domain, source_agent_id, target_agent_id, source_authority_budget, translated_budget, translation_discount, chain_root_id'],
        ], S, col_widths=[2.5*cm, 14.3*cm]
    ))
    story.append(sp(6))

    story.append(Paragraph('4.3  Fallback Mode', S['h2']))
    story.append(Paragraph(
        'When ML-DSA-65 is unavailable, ATF falls back to content hash only (no PQC signature). '
        'This mode (<font face="Courier" size="9">pqc_signature = null</font>) is explicitly: '
        '<b>Permitted</b> for ATF-COMPLIANT-LEVEL-1 development/test environments; '
        '<b>Prohibited</b> for ATF-COMPLIANT-LEVEL-2+ production deployments.', S['body']))

    story.append(PageBreak())

    # ── SECTION 5 ─────────────────────────────────────────────────────────────
    story.append(Paragraph('5.  Temporal Admissibility (ADR-157)', S['h1']))
    story.append(rule(S))
    story.append(Paragraph(
        'The Temporal Admissibility Record (TAR) is ATF\'s mechanism for proving that an agent\'s '
        'authority was valid at the exact moment of execution.', S['body']))

    story.append(Paragraph('5.1  Why TAR Is Necessary', S['h2']))
    story.append(Paragraph(
        'JWT <font face="Courier" size="9">exp</font> claims verify that a token is not expired '
        'at the time of checking. This is an implicit check — there is no artifact proving the '
        'check occurred. TAR makes the check explicit and produces a signed, persistent record:', S['body']))
    story.append(sp(4))
    story.append(make_table(
        ['Property', 'JWT exp check', 'TAR (ATF-INV-005)'],
        [
            ['Existence check', 'Yes', 'Yes'],
            ['Signed artifact', 'No', 'Yes (ML-DSA-65)'],
            ['Timestamp granularity', 'Second', 'Nanosecond-resolution'],
            ['Persistence', 'No', 'Yes (database row, immutable)'],
            ['Binding to execution', 'No', 'Yes (execution_ref)'],
            ['Independent verifiability', 'No', 'Yes (offline CLI)'],
            ['Rejection record', 'No', 'Yes (REJECTED status with reason)'],
        ], S, col_widths=[5.5*cm, 4.3*cm, 7*cm]
    ))
    story.append(sp(8))

    story.append(Paragraph('5.2  TAR Issuance Protocol', S['h2']))
    tar_protocol = """Input:  DR, agent_id, task_action, execution_ref
Output: TemporalAdmissibilityRecord (ATFTAR-{16HEX})

1. execution_ns  ← time.time_ns()   # Nanosecond capture — BEFORE checks
2. Verify DR.status == ACTIVE
3. Verify execution_ts < DR.expires_at
4. Verify execution_ts >= DR.created_at
5. Set admission_status ← ADMITTED  (or REJECTED with reason)
6. Compute content_hash over all TAR fields including execution_ns
7. Sign content_hash with ML-DSA-65
8. Persist TAR to atf_temporal_records table
9. Return TAR"""
    story.append(code_block(tar_protocol, S))
    story.append(sp(4))
    story.append(Paragraph(
        '<b>Step 1 is executed before steps 2–4.</b> This ensures the '
        '<font face="Courier" size="9">execution_ns</font> reflects the actual admission time, '
        'not the outcome of the checks. The TAR documents the authority state <i>at admission</i>, '
        'before any decision logic executes.', S['body']))

    # ── SECTION 6 ─────────────────────────────────────────────────────────────
    story.append(Paragraph('6.  Cross-Domain Trust Portability (ADR-158)', S['h1']))
    story.append(rule(S))
    story.append(Paragraph(
        'In multi-domain deployments, an agent authorized in domain FINANCE may need to access '
        'resources in domain HEALTHCARE. Cross-domain trust requires explicit authority translation '
        'with mandatory reduction.', S['body']))

    story.append(Paragraph('6.1  Domain Translation Receipt (DTR / ATFDTR-{16HEX})', S['h2']))
    dtr_example = """source_budget    = 60.0   (FINANCE domain)
discount         = 0.30   (FINANCE → HEALTHCARE policy)
translated_budget = 60.0 × (1 - 0.30) = 42.0  (HEALTHCARE domain)"""
    story.append(code_block(dtr_example, S))
    story.append(sp(4))
    story.append(Paragraph(
        'The discount is mandatory — cross-domain translation <b>MUST</b> reduce authority (CDTP-INV-003). '
        'An agent cannot gain authority by crossing domains.', S['body']))

    story.append(Paragraph('6.2  Standard Domain-Pair Discount Policies', S['h2']))
    story.append(make_table(
        ['Source → Target', 'Default Discount', 'Rationale'],
        [
            ['HEALTHCARE → FINANCE', '30%', 'High sensitivity of both domains'],
            ['FINANCE → HEALTHCARE', '30%', 'Symmetric high-sensitivity'],
            ['FINANCE → INSURANCE', '15%', 'Adjacent regulatory domain'],
            ['DEFENSE → FINANCE', '40%', 'Strict isolation requirement'],
            ['DEFENSE → HEALTHCARE', '45%', 'Maximum cross-domain sensitivity'],
            ['Other pairs', '20%', 'Default cross-domain discount'],
        ], S, col_widths=[5*cm, 3.5*cm, 8.3*cm]
    ))

    story.append(PageBreak())

    # ── SECTION 7 ─────────────────────────────────────────────────────────────
    story.append(Paragraph('7.  Governance Receipt Integration', S['h1']))
    story.append(rule(S))

    story.append(Paragraph('7.1  The Triple Chain', S['h2']))
    story.append(Paragraph(
        'Every OMNIX governance decision originating from an ATF-registered agent produces '
        'three cross-referenced artifacts:', S['body']))
    triple_json = """{
  "receipt_id":     "OMNIX-FIN-20260512-A3F7B2",
  "decision":       "APPROVED",
  "pqc_signature":  "ML-DSA-65 signature ...",

  "atf_context": {
    "delegation_id":    "ATFDR-8B2C4D6E1F3A5B7C",
    "tar_id":           "ATFTAR-C4D8E2F1A3B5C7D9",
    "agent_id":         "AID-FINANCE-3A7F9B2C1D4E5F6A",
    "delegator_id":     "HUMAN-TIER1-HN-001",
    "admission_status": "ADMITTED",
    "execution_ns":     1747058400000000000,
    "authority_budget": 60.0,
    "chain_root_id":    "ATFDR-8B2C4D6E1F3A5B7C",
    "pqc_signed":       true
  }
}"""
    story.append(code_block(triple_json, S))
    story.append(sp(4))
    story.append(Paragraph(
        'This structure enables a verifier to answer all four questions using only this JSON '
        'document and the root public key.', S['body']))

    story.append(Paragraph('7.2  Verification Flow', S['h2']))
    verify_flow = """verify(receipt.json):
  1. Check receipt.pqc_signature over receipt.content_hash  → receipt integrity
  2. Fetch DR by atf_context.delegation_id                  → authority claim
  3. Verify DR.pqc_signature over DR.content_hash           → delegation integrity
  4. Verify DR.delegator_public_key signed the hash         → principal identity
  5. Fetch TAR by atf_context.tar_id                        → temporal proof
  6. Verify TAR.pqc_signature over TAR.content_hash         → TAR integrity
  7. Check TAR.admission_status == ADMITTED                  → execution admitted
  8. Check TAR.execution_ref == receipt.receipt_id           → binding holds
  9. Traverse chain to chain_root_id                         → human traceability
  Result: VERIFIED | NOT VERIFIED

  All steps can be performed offline using only the receipt artifacts."""
    story.append(code_block(verify_flow, S))

    # ── SECTION 8 ─────────────────────────────────────────────────────────────
    story.append(Paragraph('8.  Independent Verifiability (ATF-INV-006)', S['h1']))
    story.append(rule(S))

    inv6_box = Table([[
        Paragraph(
            '<i>"Any party MUST be able to verify a delegation chain using only the receipts and '
            'the root public key. No access to the issuing platform, API, account, or internet '
            'connection is required."</i>',
            ParagraphStyle('quote', fontName='Helvetica-Oblique', fontSize=10, leading=16,
                textColor=ACCENT_LIGHT, alignment=TA_CENTER))
    ]], colWidths=[PAGE_W - 2*MARGIN - 4*mm],
    style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
        ('BOX', (0,0), (-1,-1), 1.5, ACCENT_BLUE),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
        ('TOPPADDING', (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
    ]))
    story.append(inv6_box)
    story.append(sp(8))
    story.append(Paragraph(
        'This property distinguishes ATF from platform-dependent audit trails. A regulator conducting '
        'a post-incident review can:', S['body']))
    for item in [
        'Download the receipt artifacts from the institution\'s disclosure',
        'Run <font face="Courier" size="9">python omnix_atf_verify.py receipt.json</font>',
        'Receive a complete VERIFIED/NOT VERIFIED verdict with full chain analysis',
        'Without any interaction with OMNIX or the deploying institution\'s systems',
    ]:
        story.append(Paragraph(f'• {item}', S['bullet']))
    story.append(sp(6))
    story.append(Paragraph(
        'This is analogous to how anyone can verify a PGP-signed document without contacting the '
        'key issuer — but applied to the entire AI agent authority chain.', S['body']))

    story.append(PageBreak())

    # ── SECTION 9 ─────────────────────────────────────────────────────────────
    story.append(Paragraph('9.  Compliance Framework', S['h1']))
    story.append(rule(S))
    story.append(Paragraph('ATF defines three compliance levels:', S['body']))
    story.append(sp(6))

    levels = [
        ('Level 1 — Basic', 'Development and Proof-of-Concept', [
            'DR content hash (SHA-256)', 'MAR enforcement', 'Chain traversal',
            'PQC signature: SHOULD (not required)', 'TAR: OPTIONAL',
        ]),
        ('Level 2 — Standard', 'Production, Enterprise', [
            'All Level-1 requirements', 'PQC signature REQUIRED (ML-DSA-65)',
            'TAR REQUIRED for all governance-connected executions',
            'ATF CCS ≥ 80 required for high-assurance domains',
            'Independent verifiability demonstrated',
        ]),
        ('Level 3 — Sovereign', 'Regulated, Critical Infrastructure', [
            'All Level-2 requirements', 'RFC 3161 TSA timestamp counter-signature on TARs',
            'FIPS 140-3 validated cryptographic module SHOULD be used',
            'Formal verification documentation (TLA+ or equivalent)',
            'Public CLI verifier available for independent audit',
            'Cascade revocation within 1 hour of compromise detection',
        ]),
    ]
    for level, context, reqs in levels:
        story.append(KeepTogether([
            Paragraph(f'{level} <font color="#888888">({context})</font>', S['h2']),
        ] + [Paragraph(f'• {r}', S['bullet']) for r in reqs] + [sp(6)]))

    # ── SECTION 10 ────────────────────────────────────────────────────────────
    story.append(Paragraph('10.  Interoperability', S['h1']))
    story.append(rule(S))
    story.append(make_table(
        ['Framework / Protocol', 'Relationship to ATF'],
        [
            ['W3C Verifiable Credentials', 'ATF DRs share structural concepts. ATF extends with authority budget arithmetic, MAR invariant, TAR as separate signed artifact, and TLA+-verified formal invariants.'],
            ['IETF JWT (RFC 7519)', 'ATF receipts can be serialized as JWT claims. The exp claim ≈ DR.expires_at. TAR provides stronger evidence than exp — signed artifact, not just a claim.'],
            ['OpenID Connect', 'ATF agent identities can be registered as OAuth 2.0 clients. chain_root_id can be used as sub claim linking to human principal\'s OIDC identity.'],
            ['SPIFFE/SPIRE', 'ATF extends workload identity with delegation chain, authority arithmetic, and governance receipt integration.'],
            ['LangChain / AutoGen / CrewAI', 'ATF is framework-agnostic. ATFConnector integrates into any Python-based agent framework without modifying existing logic.'],
        ], S, col_widths=[4.5*cm, 12.3*cm]
    ))

    story.append(PageBreak())

    # ── SECTION 11 ────────────────────────────────────────────────────────────
    story.append(Paragraph('11.  Implementation Reference', S['h1']))
    story.append(rule(S))
    story.append(Paragraph(
        'The OMNIX ATF reference implementation consists of the following functional components. '
        'Internal module structure is proprietary; public interfaces are exposed via the REST API '
        'and the offline CLI verifier.', S['body']))
    story.append(sp(6))
    story.append(make_table(
        ['Component', 'Role', 'Public Interface'],
        [
            ['Trust Lattice Engine',
             'DAG management, AgentIdentity registration, DelegationReceipt issuance, MAR enforcement',
             '/api/atf/register · /api/atf/delegate'],
            ['Temporal Authority Engine',
             'TAR issuance and verification, nanosecond-resolution admission capture, ADMITTED/REJECTED status',
             '/api/atf/admit · /api/atf/temporal/verify'],
            ['Cross-Domain Bridge',
             'DTR issuance, domain-pair discount policy enforcement, CDTP invariant verification',
             '/api/atf/translate'],
            ['Governance Connector',
             'Integration layer binding ATF context to GovernanceReceipt — non-blocking, backward compatible',
             'Embedded in governance pipeline (internal)'],
            ['REST API Layer',
             'Full ATF lifecycle endpoints — register, delegate, admit, verify, chain traversal',
             '/api/atf/* (documented in RFC-ATF-1)'],
            ['Offline CLI Verifier',
             'Standalone verifier — DR, TAR, chain, receipt modes. Zero platform dependency (ATF-INV-006)',
             'omnix_atf_verify.py (public, open source)'],
            ['Formal Specification',
             'TLA+ model — 5 invariants, bounded state space verification, MAR + Acyclicity + ChainRoot + Immutability',
             'ATF-TLA-SPEC.tla (public repository)'],
        ], S, col_widths=[4.2*cm, 7.8*cm, 4.8*cm]
    ))

    # ── SECTION 12 ────────────────────────────────────────────────────────────
    story.append(Paragraph('12.  Known Limitations and Open Questions', S['h1']))
    story.append(rule(S))
    story.append(make_table(
        ['Limitation', 'Mitigation', 'Status'],
        [
            ['Clock trust in TAR (TM-004)', 'RFC 3161 TSA integration (planned Level-3 requirement)', 'OPEN'],
            ['Revocation propagation latency (TM-006)', 'Short DR validity + centralized revocation registry', 'PARTIAL'],
            ['Theorem-proved MAR vs model-checked', 'Port to Coq/Lean for one invariant (planned)', 'PLANNED'],
            ['FIPS 140-3 validated library', 'Library-agnostic spec; swap pqc for validated lib', 'OPEN'],
            ['Multi-instance TAR uniqueness', 'Redis SETNX / DB unique constraint', 'PARTIAL'],
        ], S, col_widths=[4.8*cm, 7.5*cm, 2.5*cm]
    ))

    # ── SECTION 13 ────────────────────────────────────────────────────────────
    story.append(Paragraph('13.  Related Work', S['h1']))
    story.append(rule(S))
    related = [
        ('W3C Verifiable Credentials', 'Identity claims with PQC extensions (emerging drafts). No authority budgets or temporal admissibility artifacts.'),
        ('SPIFFE/SPIRE', 'Workload identity for service meshes. No delegation chains or authority arithmetic.'),
        ('OpenID Connect', 'Authentication protocol. No authorization governance chain.'),
        ('NIST SP 800-207 (Zero Trust)', 'Zero Trust Architecture principles. ATF implements explicit trust verification before each execution event.'),
        ('NIST AI RMF (January 2023)', 'AI Risk Management Framework. ATF directly implements accountability requirements in the GOVERN function.'),
        ('EU AI Act (August 2024)', 'ATF addresses Arts. 13/14 (transparency and human oversight) for high-risk AI systems.'),
        ('CRYSTALS-Dilithium / ML-DSA', 'NIST FIPS 204 (August 2024). ATF adopts ML-DSA-65 as mandatory signature algorithm for Level-2+ compliance.'),
    ]
    for name, desc in related:
        story.append(Paragraph(f'<b>{name}:</b> {desc}', S['body']))
        story.append(sp(2))

    # ── SECTION 14 ────────────────────────────────────────────────────────────
    story.append(Paragraph('14.  Conclusion', S['h1']))
    story.append(rule(S))
    story.append(Paragraph(
        'The OMNIX Agent Trust Fabric addresses a specific, well-defined gap in AI governance '
        'infrastructure: the absence of cryptographic proof of <i>who authorized an AI agent, '
        'under what authority bound, when that authority was valid, and whether execution was '
        'admitted at that exact moment</i>.', S['body']))
    story.append(Paragraph(
        'ATF provides this through a three-artifact chain (DR + TAR + GovernanceReceipt), '
        'formally specified invariants (TLA+ model-checked), post-quantum cryptography '
        '(ML-DSA-65, NIST FIPS 204), and independent offline verifiability (ATF-INV-006).', S['body']))
    story.append(Paragraph(
        'The design is complementary to existing orchestration frameworks, not a replacement '
        'for them. It operates at the governance layer that precedes execution — making the '
        'authority chain verifiable before, during, and after an AI agent acts.', S['body']))
    story.append(Paragraph(
        'As autonomous AI systems take on greater responsibility in enterprise and regulated '
        'environments, this governance layer becomes a prerequisite for institutional trust. '
        'OMNIX ATF provides the formal specification, reference implementation, and public '
        'verification tooling to establish that trust on a cryptographic foundation.', S['body']))

    story.append(PageBreak())

    # ── REFERENCES ────────────────────────────────────────────────────────────
    story.append(Paragraph('References', S['h1']))
    story.append(rule(S))
    refs = [
        '[RFC-ATF-1] Nunes, H. "RFC-ATF-1: Agent Trust Fabric Delegation Protocol." OMNIX QUANTUM Open Standard, May 2026. https://github.com/Costenho19/rfc-atf-1',
        '[ADR-156] OMNIX QUANTUM. "Agent Trust Fabric (ATF)." Architecture Decision Record 156, 2026.',
        '[ADR-157] OMNIX QUANTUM. "Temporal Authority Admissibility." Architecture Decision Record 157, 2026.',
        '[ADR-158] OMNIX QUANTUM. "Cross-Domain Trust Portability." Architecture Decision Record 158, 2026.',
        '[FIPS204] NIST. "Module-Lattice-Based Digital Signature Standard." FIPS 204, August 2024. https://doi.org/10.6028/NIST.FIPS.204',
        '[W3CVC] W3C. "Verifiable Credentials Data Model 2.0." W3C Recommendation, 2024.',
        '[RFC7519] Jones, M., et al. "JSON Web Token (JWT)." IETF RFC 7519, May 2015.',
        '[RFC3161] Adams, C., et al. "Internet X.509 PKI Time-Stamp Protocol (TSP)." IETF RFC 3161, August 2001.',
        '[NISTAIRGM] NIST. "Artificial Intelligence Risk Management Framework." NIST AI 100-1, January 2023.',
        '[SP800207] NIST. "Zero Trust Architecture." SP 800-207, August 2020.',
        '[TLA] Lamport, L. "Specifying Systems: The TLA+ Language and Tools." Addison-Wesley, 2002.',
        '[EUAIACT] European Parliament. "Regulation (EU) 2024/1689 on Artificial Intelligence." Official Journal of the EU, August 2024.',
        '[CRYSTALS] Ducas, L., et al. "CRYSTALS-Dilithium: A Lattice-Based Digital Signature Scheme." IACR TCHES, 2018.',
    ]
    for ref in refs:
        story.append(Paragraph(ref, S['ref']))
        story.append(sp(3))

    story.append(sp(20))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER_GRAY))
    story.append(sp(8))

    footer_data = [
        [
            Paragraph('<b>Document ID:</b> OMNIX-WP-ATF-2026-001', S['cover_meta']),
            Paragraph('<b>Version:</b> 1.0.0', S['cover_meta']),
            Paragraph('<b>Date:</b> May 2026', S['cover_meta']),
            Paragraph('<b>Classification:</b> Public — Institutional Distribution', S['cover_meta']),
        ]
    ]
    footer_table = Table(footer_data, colWidths=[4.2*cm, 3*cm, 3*cm, 6.6*cm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), TABLE_HEAD),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER_GRAY),
        ]))
    story.append(footer_table)

    # ── Build with page decorators ─────────────────────────────────────────────
    def on_page(canvas, doc):
        if doc.page == 1:
            cover_page(canvas, doc)
        else:
            normal_page(canvas, doc)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF generated: {output_path} ({os.path.getsize(output_path):,} bytes)")

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'docs/zenodo/submission_package/OMNIX-ATF-WHITEPAPER.pdf'
    build_pdf(out)
