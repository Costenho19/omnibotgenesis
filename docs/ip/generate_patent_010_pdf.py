"""
OMNIX-PAT-2026-010 — Append-Only Post-Quantum Merkle Transparency Chain
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

OUTPUT = 'docs/ip/provisional_applications/pdf_exports/OMNIX_PAT_2026_010_PROVISIONAL.pdf'

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
mono    = S('Mono',fontName='Courier', fontSize=8, textColor=NAVY,
            spaceAfter=4, leading=12, leftIndent=8,
            backColor=colors.HexColor('#F0F4F8'))

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

# ── DIAGRAM 1: MERKLE CHAIN LINKAGE ───────────────────────────────────────────
def diagram_chain(width):
    dw, dh = width, 175
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    label(d, dw/2, dh-14, 'FIG. 1 — Append-Only Transparency Chain: Hash-Linked Decision Receipt Entries',
          size=8, color=DGRAY, bold=True, align='middle')

    entries = ['Entry N-2', 'Entry N-1', 'Entry N', 'Entry N+1']
    ew = (dw - 30) / 4 - 6
    ey = dh - 95
    eh = 65

    for i, name in enumerate(entries):
        ex = 10 + i*(ew+6)
        clr = TEAL if i == 2 else NAVY
        bdr = GOLD if i == 2 else CGRAY
        box(d, ex, ey, ew, eh, fill=clr, stroke=bdr, sw=2 if i==2 else 1, rx=3, ry=3)
        label(d, ex+ew/2, ey+eh-10, name, size=7.5, color=GOLD if i==2 else CGRAY, bold=True)
        fields = ['receipt_hash', 'prev_log_hash', 'merkle_root', 'PQC_sig', 'ts_utc']
        for j, f in enumerate(fields):
            label(d, ex+ew/2, ey+eh-22-j*9, f, size=6, color=WHITE if i==2 else colors.HexColor('#AABBCC'))
        if i < len(entries)-1:
            arrow_right(d, ex+ew, ex+ew+6, ey+eh/2, color=GOLD if i==1 else CGRAY, sw=1.5)

    # Hash link explanation
    link_y = ey - 20
    label(d, dw/2, link_y, 'Modify any field → receipt_hash changes → next entry\'s prev_log_hash invalid → chain verification FAILS',
          size=7, color=RED, bold=False, align='middle')
    label(d, dw/2, link_y-12, 'Delete any entry → hash linkage gap → chain verification FAILS',
          size=7, color=RED, align='middle')

    # Chain root
    root_y = link_y - 32
    box(d, dw/2-80, root_y, 160, 22, fill=GREEN, stroke=GOLD, sw=2, rx=4, ry=4)
    label(d, dw/2, root_y+14, 'Published Merkle Root = commitment to ALL N entries', size=7.5, color=WHITE, bold=True)
    label(d, dw/2, root_y+4, 'External verifiers recompute root from chain hashes — no receipt content disclosed', size=6.5, color=colors.HexColor('#CCFFCC'))

    return d

# ── DIAGRAM 2: ROLLING MERKLE ACCUMULATOR ─────────────────────────────────────
def diagram_accumulator(width):
    dw, dh = width, 165
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    label(d, dw/2, dh-14, 'FIG. 2 — Rolling Merkle Accumulator: O(1) Update Per New Entry',
          size=8, color=DGRAY, bold=True, align='middle')

    # Accumulator steps
    steps = [
        ('root₀', '"0"×64\n(genesis)', BLUE, False),
        ('root₁', 'SHA256(root₀\n|| hash(e₁))', NAVY, False),
        ('root₂', 'SHA256(root₁\n|| hash(e₂))', NAVY, False),
        ('root_N', 'SHA256(root_{N-1}\n|| hash(e_N))', TEAL, True),
    ]
    sw_step = (dw - 20) / 4 - 8
    step_y = dh - 90

    for i, (name, formula, clr, is_key) in enumerate(steps):
        sx = 10 + i*(sw_step+8)
        box(d, sx, step_y, sw_step, 52, fill=clr,
            stroke=GOLD if is_key else CGRAY, sw=2 if is_key else 1, rx=3, ry=3)
        label(d, sx+sw_step/2, step_y+42, name, size=8, color=GOLD if is_key else WHITE, bold=True)
        lines = formula.split('\n')
        for j, line in enumerate(lines):
            label(d, sx+sw_step/2, step_y+30-j*10, line, size=6.5, color=WHITE)
        if i < len(steps)-1:
            arrow_right(d, sx+sw_step, sx+sw_step+8, step_y+26, color=GOLD, sw=1.5)

    # Properties box
    prop_y = step_y - 38
    box(d, 10, prop_y, dw-20, 28, fill=NAVY, stroke=GOLD, sw=1.5, rx=3, ry=3)
    label(d, dw/2, prop_y+20, 'root_N = commitment to ALL N entries — O(1) update — published root enables third-party verification without content disclosure',
          size=7.5, color=GOLD, bold=True, align='middle')
    label(d, dw/2, prop_y+8, 'No blockchain dependency | No external TSA | No network latency in governance pipeline',
          size=7, color=CGRAY, align='middle')

    return d

# ── DIAGRAM 3: INTERNAL TIMESTAMP TOKEN ───────────────────────────────────────
def diagram_timestamp(width):
    dw, dh = width, 175
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    label(d, dw/2, dh-14, 'FIG. 3 — Internal Timestamp Token (TST): RFC 3161-Style Without External TSA',
          size=8, color=DGRAY, bold=True, align='middle')

    half = dw/2 - 6

    # Left: External TSA (prior art)
    label(d, half/2+5, dh-30, 'PRIOR ART — External TSA', size=8, color=RED, bold=True, align='middle')
    prior_steps = [
        (BLUE, 'Governance Decision'),
        (colors.HexColor('#8B0000'), 'Hash → External TSA'),
        (RED, 'Network Latency (50-500ms)'),
        (colors.HexColor('#8B0000'), 'TSA Returns Token'),
        (RED, '3rd-party dependency risk'),
    ]
    for i, (clr, step) in enumerate(prior_steps):
        sy = dh - 55 - i*22
        box(d, 8, sy, half-4, 18, fill=clr, stroke=CGRAY, sw=0.8, rx=2, ry=2)
        label(d, 8+(half-4)/2, sy+5, step, size=7, color=WHITE)
        if i < len(prior_steps)-1:
            arrow_down(d, 8+(half-4)/2, sy, sy-4, color=CGRAY, sw=0.8)

    # Divider
    d.add(Line(dw/2, 12, dw/2, dh-22, strokeColor=CGRAY, strokeWidth=1,
               strokeDashArray=[3, 3]))

    # Right: OMNIX Internal TST
    rx = dw/2+4
    rw = half-4
    label(d, rx+rw/2, dh-30, 'OMNIX — Internal TST', size=8, color=GREEN, bold=True, align='middle')
    tst_fields = [
        (TEAL, 'version: 1'),
        (TEAL, 'hash_alg: "SHA-256"'),
        (TEAL, 'payload_hash: SHA256(receipt)'),
        (TEAL, 'ts_utc: "2026-04-19T..."'),
        (TEAL, 'nonce: <16 random bytes>'),
        (TEAL, 'policy: "OMNIX-ADR044-v1"'),
    ]
    tst_y = dh - 48
    tst_h = (len(tst_fields)*18)+8
    box(d, rx, tst_y - tst_h + 18, rw, tst_h, fill=NAVY, stroke=GOLD, sw=1.5, rx=3, ry=3)
    label(d, rx+rw/2, tst_y+10, 'TST Structure (RFC 3161-style)', size=7.5, color=GOLD, bold=True)
    for i, (clr, field) in enumerate(tst_fields):
        label(d, rx+8, tst_y - i*18 - 4, field, size=7, color=CGRAY, align='start')

    seal_y = tst_y - tst_h + 2
    box(d, rx, seal_y-18, rw, 16, fill=GREEN, stroke=GOLD, sw=1.5, rx=2, ry=2)
    label(d, rx+rw/2, seal_y-12, 'tst_hash = SHA256(canonical_json(TST)) — No external TSA required', size=6.5, color=WHITE)

    return d

# ── DIAGRAM 4: PUBLIC VERIFICATION FLOW ───────────────────────────────────────
def diagram_verification(width):
    dw, dh = width, 175
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=LGRAY, strokeColor=CGRAY, strokeWidth=0.5))
    label(d, dw/2, dh-14, 'FIG. 4 — Public Verification Flow: Third-Party Integrity Check Without Receipt Content',
          size=8, color=DGRAY, bold=True, align='middle')

    # Two columns: External Verifier | OMNIX Public API
    col_w = dw/2 - 10
    left_x = 8
    right_x = dw/2 + 4

    label(d, left_x + col_w/2, dh-30, 'EXTERNAL VERIFIER', size=8.5, color=BLUE, bold=True, align='middle')
    label(d, right_x + col_w/2, dh-30, 'OMNIX PUBLIC API', size=8.5, color=TEAL, bold=True, align='middle')

    # Sequence steps
    steps = [
        ('GET /api/transparency/chain', True, False),
        ('← chain entries (hashes only)', False, True),
        ('Recompute hash chain', True, False),
        ('Recompute Merkle root', True, False),
        ('Verify PQC signatures', True, False),
        ('Compare own receipt hash in chain?', True, False),
        ('✓ VERIFIED / ✗ TAMPERED', True, False),
    ]
    step_y = dh - 55
    for i, (step, is_left, is_right) in enumerate(steps):
        sy = step_y - i*16
        if is_left and not is_right:
            box(d, left_x, sy, col_w-4, 13, fill=BLUE, stroke=CGRAY, sw=0.5, rx=2, ry=2)
            label(d, left_x+(col_w-4)/2, sy+3, step, size=6.5, color=WHITE)
            arrow_right(d, left_x+col_w-4, right_x, sy+6, color=CGRAY, sw=0.8)
        elif is_right:
            box(d, right_x, sy, col_w-4, 13, fill=TEAL, stroke=CGRAY, sw=0.5, rx=2, ry=2)
            label(d, right_x+(col_w-4)/2, sy+3, step, size=6.5, color=WHITE)
            arrow_right(d, right_x, left_x+col_w-4, sy+6, color=GOLD, sw=0.8)
        else:
            box(d, left_x, sy, col_w-4, 13, fill=NAVY, stroke=CGRAY, sw=0.5, rx=2, ry=2)
            label(d, left_x+(col_w-4)/2, sy+3, step, size=6.5, color=WHITE)

    # Key property note
    note_y = step_y - len(steps)*16 - 10
    box(d, 10, note_y, dw-20, 16, fill=GREEN, stroke=GOLD, sw=1.5, rx=3, ry=3)
    label(d, dw/2, note_y+6, 'No receipt content disclosed — verifier confirms integrity without accessing confidential governance records',
          size=7, color=WHITE, bold=True, align='middle')

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
    canvas_obj.drawRightString(w-RM, h-9*mm, 'OMNIX-PAT-2026-010')
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
        'CONFIDENTIAL — PATENT PENDING — OMNIX-PAT-2026-010 — Filed: April 19, 2026')
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
        'APPEND-ONLY POST-QUANTUM MERKLE TRANSPARENCY CHAIN FOR AUTOMATED '
        'GOVERNANCE DECISION RECEIPTS WITH INTERNAL RFC-3161-STYLE TIMESTAMPING, '
        'ROLLING HASH ACCUMULATION, AND TAMPER-EVIDENT PUBLIC VERIFICATION',
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
        ['Docket Number:', 'OMNIX-PAT-2026-010'],
        ['Inventor:', 'Harold Alberto Nunes Rodelo'],
        ['Applicant:', 'OMNIX QUANTUM LTD (United Kingdom)'],
        ['Entity Status:', 'Micro Entity — 37 C.F.R. § 1.29'],
        ['Filing Basis:', '35 U.S.C. § 111(b) — Provisional Application'],
        ['Date Prepared:', 'April 19, 2026'],
        ['Date of Filing:', 'April 19, 2026'],
        ['Related Applications:', 'OMNIX-PAT-2026-001 (Governance Control Architecture), OMNIX-PAT-2026-003 (PQC Auth)'],
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
        'The present invention relates to cryptographic audit trail systems for automated '
        'decision governance, and more particularly to an append-only transparency chain '
        'that links governance decision receipts using a rolling Merkle-style hash '
        'accumulator, applies post-quantum cryptographic signatures to each chain entry, '
        'generates RFC 3161-style trusted timestamps without dependency on external '
        'timestamp authorities, and exposes a public verification interface enabling '
        'external parties to verify the integrity and chronological ordering of the '
        'decision record without requiring access to the contents of individual receipts.', body))

    # BACKGROUND
    story.append(Paragraph('BACKGROUND OF THE INVENTION', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))
    story.append(Paragraph(
        'Automated decision systems operating in regulated environments must produce audit '
        'records satisfying three independent requirements: completeness (every decision is '
        'recorded), integrity (records cannot be silently altered), and verifiability '
        '(third parties can confirm integrity without needing access to confidential contents). '
        'Existing audit trail mechanisms fail one or more of these requirements:', body))

    deficiencies = [
        ('Log-Based Systems',
         'Traditional logging systems record events in timestamped log files. These systems '
         'fail the integrity requirement because log files can be modified after the fact '
         'without detection — there is no cryptographic linkage between log entries that '
         'would reveal retroactive modification.'),
        ('Blockchain-Based Systems',
         'Some systems use public or permissioned blockchains as immutable ledgers. These '
         'systems require network connectivity to the blockchain, expose governance records '
         'to the blockchain\'s consensus and availability properties, and create regulatory '
         'uncertainty regarding the legal status of blockchain-recorded evidence.'),
        ('External Timestamp Authorities (TSA)',
         'RFC 3161 timestamping requires submission of document hashes to external trusted '
         'timestamp authorities. This creates dependencies on third-party services, introduces '
         'network latency into the governance pipeline, and requires ongoing contractual '
         'relationships with external parties.'),
        ('Isolated Receipt Systems',
         'Systems that generate individual cryptographic receipts per decision — without '
         'chaining those receipts — provide per-receipt integrity but cannot detect the '
         'deletion of receipts from the record. An adversary who deletes a receipt '
         'leaves no detectable gap.'),
        ('No Post-Quantum Security',
         'All known prior art audit trail systems use classical cryptographic primitives '
         '(RSA, ECDSA, Ed25519) that are vulnerable to quantum computing attacks capable '
         'of forging signatures and breaking hash function preimage resistance.'),
    ]
    for title, desc in deficiencies:
        story.append(Paragraph(f'<b>{title}:</b> {desc}', body))

    # SUMMARY + DIAGRAMS
    story.append(Paragraph('SUMMARY OF THE INVENTION', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))
    story.append(Paragraph(
        'The OMNIX Transparency Chain (OTC) provides an append-only audit trail for '
        'governance decision receipts with five key architectural properties:', body))

    props = [
        ('Hash-Linked Chain Integrity',
         'Each chain entry contains the hash of the previous entry (prev_log_hash). '
         'Modification of any entry changes its hash, invalidating all subsequent entries. '
         'Deletion of any entry creates a detectable hash gap.'),
        ('Rolling Merkle Accumulation',
         'A rolling Merkle root accumulates the hash of every entry with O(1) update cost. '
         'The current root is a commitment to all entries ever written. '
         'Published roots enable third-party verification without content disclosure.'),
        ('Internal RFC 3161-Style Timestamping',
         'Each entry includes a cryptographically bound Internal Timestamp Token (TST) '
         'generated without dependency on any external Timestamp Authority. '
         'The TST binds payload hash, timestamp, nonce, and policy identifier.'),
        ('Post-Quantum Cryptographic Signatures',
         'Each chain entry is signed using ML-DSA-65 (Dilithium-3, NIST FIPS 204), '
         'a lattice-based digital signature algorithm resistant to quantum computing attacks.'),
        ('Content-Private Public Verification',
         'A public verification API exposes chain entries as hash sequences only. '
         'External verifiers recompute the hash chain and Merkle root without accessing '
         'the confidential content of any governance decision receipt.'),
    ]
    prop_data = [[Paragraph(f'<b>{t}</b>', S('ph', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
                  Paragraph(d, S('pd', fontName='Helvetica', fontSize=8.5, textColor=WHITE, leading=12))]
                 for t, d in props]
    prop_t = Table(prop_data, colWidths=[42*mm, CONTENT_W-42*mm])
    prop_t.setStyle(TableStyle([
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
    story.append(prop_t)
    story.append(Spacer(1, 5*mm))

    story.append(KeepTogether([
        renderPDF.GraphicsFlowable(diagram_chain(CONTENT_W)),
        Paragraph('FIG. 1 — Hash-Linked Transparency Chain: Any modification or deletion detected via hash linkage failure', caption),
    ]))
    story.append(Spacer(1, 4*mm))

    story.append(KeepTogether([
        renderPDF.GraphicsFlowable(diagram_accumulator(CONTENT_W)),
        Paragraph('FIG. 2 — Rolling Merkle Accumulator: O(1) update per entry; current root commits to entire history', caption),
    ]))

    story.append(PageBreak())

    # DETAILED DESCRIPTION
    story.append(Paragraph('DETAILED DESCRIPTION OF THE INVENTION', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))

    story.append(Paragraph('I. Chain Entry Structure', h2))
    story.append(Paragraph(
        'Each entry in the OMNIX Transparency Chain comprises the following fields:', body))
    story.append(Paragraph(
        'receipt_hash: SHA-256 hash of the complete governance decision receipt payload | '
        'prev_log_hash: SHA-256 hash of the previous chain entry (hash of chain entry N-1) | '
        'merkle_root: Current rolling Merkle accumulator root after incorporating this entry | '
        'PQC_sig: ML-DSA-65 (Dilithium-3) signature over all fields | '
        'ts_utc: Internal timestamp token (TST) in ISO 8601 format | '
        'entry_id: Monotonically increasing entry sequence number | '
        'chain_version: Chain format version for forward compatibility',
        S('mono2', fontName='Courier', fontSize=8, textColor=NAVY, leading=13,
          spaceAfter=5, leftIndent=8, backColor=colors.HexColor('#F0F4F8'))))

    story.append(Paragraph('II. Internal Timestamp Token (TST)', h2))
    story.append(Paragraph(
        'The Internal Timestamp Token provides RFC 3161-equivalent trusted timestamping '
        'without dependency on external Timestamp Authorities. Each TST comprises: '
        'version (protocol version); hash_alg (hash algorithm used); payload_hash '
        '(SHA-256 of the receipt payload being timestamped); ts_utc (timestamp in '
        'ISO 8601 UTC format); nonce (16 cryptographically random bytes preventing '
        'replay); and policy (OMNIX timestamping policy identifier). The TST is '
        'then hashed: tst_hash = SHA256(canonical_json(TST)). This hash is included '
        'in the chain entry and signed with ML-DSA-65.', body))

    story.append(KeepTogether([
        renderPDF.GraphicsFlowable(diagram_timestamp(CONTENT_W)),
        Paragraph('FIG. 3 — Internal Timestamp Token vs. External TSA: OMNIX eliminates network dependency and third-party risk', caption),
    ]))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph('III. Public Verification Interface', h2))
    story.append(Paragraph(
        'The OMNIX Public Verification API exposes a read-only endpoint that returns '
        'chain entries as sequences of hash values — never the content of governance '
        'receipts. An external verifier can: (a) retrieve the complete chain hash '
        'sequence; (b) recompute the hash chain by verifying that each entry\'s hash '
        'is consistent with the previous entry\'s hash; (c) recompute the Merkle root '
        'to verify it matches the published root; (d) verify ML-DSA-65 signatures '
        'on each entry; and (e) verify that the hash of their own governance receipt '
        'is present in the chain — confirming their receipt was recorded and has not '
        'been modified — all without the API disclosing any governance decision content.', body))

    story.append(KeepTogether([
        renderPDF.GraphicsFlowable(diagram_verification(CONTENT_W)),
        Paragraph('FIG. 4 — Content-Private Public Verification: Third parties verify integrity without accessing governance record contents', caption),
    ]))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph('IV. Post-Quantum Security Properties', h2))
    story.append(Paragraph(
        'All chain integrity mechanisms use post-quantum cryptographic primitives. '
        'ML-DSA-65 (Dilithium-3, NIST FIPS 204) provides digital signatures resistant '
        'to attacks by quantum computers running Shor\'s algorithm. SHA-256 provides '
        'hash linkage and Merkle accumulation with 128-bit post-quantum security '
        'against Grover\'s algorithm. The complete chain integrity guarantee holds '
        'against both classical and quantum adversaries.', body))

    story.append(Paragraph('V. Integration with Governance Pipeline (OMNIX-PAT-2026-001)', h2))
    story.append(Paragraph(
        'The OMNIX Transparency Chain operates as the Layer 3 evidence and receipt '
        'layer in the four-layer governance architecture described in OMNIX-PAT-2026-001. '
        'Upon each governance decision — whether APPROVED or BLOCKED — the governance '
        'pipeline generates a decision receipt containing all checkpoint evaluations, '
        'verdicts, signal values, and the final admissibility determination. This '
        'receipt is immediately appended to the transparency chain, producing a new '
        'chain entry with a binding hash, ML-DSA-65 signature, and internal timestamp. '
        'The updated Merkle root is published to the public verification API. '
        'Observed chain append latency: 0.8–3.2 milliseconds per entry (in-memory '
        'accumulator update, asynchronous persistent write).', body))

    story.append(PageBreak())

    # CLAIMS
    story.append(Paragraph('CLAIMS', h1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))

    claims = [
        ('1.', 'A cryptographic audit trail system for automated decision governance comprising: '
         'an append-only transparency chain storing a plurality of chain entries, each chain '
         'entry comprising a receipt hash of a governance decision receipt, a previous entry '
         'hash linking each entry to the immediately preceding entry in the chain, a post-quantum '
         'digital signature over all chain entry fields, and an internal timestamp token '
         'generated without dependency on any external timestamp authority; a rolling Merkle '
         'accumulator that maintains a current Merkle root representing a commitment to all '
         'entries in the transparency chain, updated in O(1) operations per new entry; and '
         'a public verification interface configured to expose chain entries as hash sequences '
         'without disclosing the content of any governance decision receipt.'),
        ('2.', 'The system of claim 1, wherein the post-quantum digital signature comprises '
         'a signature generated by the ML-DSA-65 algorithm (NIST FIPS 204, Dilithium-3) '
         'over a canonical serialization of all chain entry fields, providing signature '
         'security against adversaries equipped with quantum computing capabilities.'),
        ('3.', 'The system of claim 1, wherein the internal timestamp token comprises: '
         'a version identifier; a hash algorithm identifier; a hash of the governance '
         'decision receipt payload; a timestamp in ISO 8601 UTC format; a cryptographically '
         'random nonce of at least 16 bytes; and a policy identifier; wherein the token '
         'is internally generated without transmission to any external timestamp authority, '
         'eliminating network latency and third-party availability dependencies from '
         'the governance pipeline.'),
        ('4.', 'The system of claim 1, wherein the rolling Merkle accumulator is updated '
         'according to root_N = SHA256(root_{N-1} || hash(entry_N)), wherein root_0 is '
         'a genesis value, and wherein root_N constitutes a commitment to all N entries '
         'in the transparency chain such that any modification or deletion of any entry '
         'produces a verifiably different root value.'),
        ('5.', 'The system of claim 1, wherein the public verification interface enables '
         'an external verifier to: retrieve chain entry hash sequences; recompute the '
         'hash chain and verify hash linkage integrity; recompute the Merkle accumulator '
         'root and verify it matches the published root; verify post-quantum digital '
         'signatures; and confirm that the hash of a specific governance decision receipt '
         'is present in the chain; without the interface disclosing the content of any '
         'governance decision receipt.'),
        ('6.', 'The system of claim 1, wherein modification of any chain entry causes '
         'a change in the receipt hash of that entry, which causes a mismatch in the '
         'previous entry hash field of the immediately subsequent entry, making the '
         'modification detectable through chain hash linkage verification.'),
        ('7.', 'The system of claim 1, wherein deletion of any chain entry produces '
         'a detectable gap in the hash linkage sequence, making the deletion detectable '
         'through chain hash linkage verification even without access to the deleted '
         'entry\'s content.'),
        ('8.', 'The system of claim 1, further configured to record both approved '
         'governance decisions and blocked governance decisions in the transparency '
         'chain, producing a complete and unbiased audit record that includes all '
         'proposed actions regardless of their admissibility determination.'),
        ('9.', 'A method for generating a tamper-evident audit trail for automated '
         'decision governance comprising: generating a governance decision receipt '
         'comprising all checkpoint evaluations, verdicts, and admissibility '
         'determination for each proposed automated action; computing a receipt hash '
         'of the governance decision receipt; constructing a chain entry comprising '
         'the receipt hash, a previous entry hash linking to the immediately preceding '
         'chain entry, a post-quantum digital signature, and an internal timestamp '
         'token; updating a rolling Merkle accumulator to produce a new Merkle root '
         'representing a commitment to all chain entries including the new entry; '
         'and publishing the updated Merkle root to a public verification interface.'),
        ('10.', 'The method of claim 9, wherein the post-quantum digital signature '
         'is generated using ML-DSA-65 (NIST FIPS 204), and wherein the internal '
         'timestamp token is generated without transmission to any external timestamp '
         'authority, such that chain entry generation does not introduce network '
         'latency or third-party service dependencies into the governance pipeline.'),
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
        'An append-only transparency chain for automated governance decision receipts '
        'provides cryptographically guaranteed completeness, integrity, and verifiability '
        'of the governance audit record. Each chain entry is hash-linked to the preceding '
        'entry (enabling detection of any modification or deletion), post-quantum signed '
        'using ML-DSA-65 (NIST FIPS 204), and internally timestamped using an RFC 3161-'
        'compatible Internal Timestamp Token generated without dependency on external '
        'Timestamp Authorities. A rolling Merkle accumulator maintains a current root '
        'committing to all entries with O(1) update cost. A public verification interface '
        'enables external parties to verify chain integrity and confirm the presence of '
        'their governance receipts without accessing the confidential content of any '
        'receipt. The system operates as the Layer 3 evidence and receipt layer of the '
        'OMNIX four-layer governance architecture, producing a quantum-resistant, '
        'deletion-evident, and externally verifiable audit trail for all governance '
        'decisions — both approved and blocked.', body))

    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=CGRAY, spaceAfter=4))
    story.append(Paragraph(
        'Application Reference: OMNIX-PAT-2026-010 | Inventor: Harold Alberto Nunes Rodelo | '
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
        title='OMNIX-PAT-2026-010 Provisional Patent Application',
        author='Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD',
        subject='OMNIX-PAT-2026-010',
        creator='OMNIX Patent Document Generator v2',
    )
    doc.build(build_story(), onFirstPage=on_page, onLaterPages=on_page)
    print(f'PDF generado: {OUTPUT}')
