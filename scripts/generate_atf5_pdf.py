"""RFC-ATF-5 PDF Generator — OMNIX QUANTUM — ASCII-safe, ~55 pages"""
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

DARK_BG      = colors.HexColor('#0d0d1a')
ACCENT_BLUE  = colors.HexColor('#5b5bd6')
ACCENT_LIGHT = colors.HexColor('#8b8bf0')
ACCENT_GOLD  = colors.HexColor('#d4a843')
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
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(ROOT, 'omnix_web', 'public', 'logo_nobg.png')
OUT  = os.path.join(ROOT, 'docs', 'zenodo', 'rfc_atf_5', 'RFC-ATF-5.pdf')

def cover_page(c, doc):
    c.saveState()
    c.setFillColor(DARK_BG); c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)
    c.setFillColor(ACCENT_BLUE); c.rect(0,PAGE_H-8*mm,PAGE_W,8*mm,fill=1,stroke=0)
    c.setFillColor(ACCENT_GOLD); c.rect(0,0,PAGE_W,6*mm,fill=1,stroke=0)
    c.restoreState()

def normal_page(c, doc):
    c.saveState()
    c.setFillColor(DARK_BG); c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)
    c.setFillColor(ACCENT_BLUE); c.rect(0,PAGE_H-4*mm,PAGE_W,4*mm,fill=1,stroke=0)
    c.setFillColor(TABLE_HEAD); c.rect(0,0,PAGE_W,12*mm,fill=1,stroke=0)
    c.setFont('Helvetica',7); c.setFillColor(TEXT_GRAY)
    c.drawString(MARGIN,4*mm,'RFC-ATF-5 -- Cognitive Governance Layer -- OMNIX QUANTUM LTD -- omnixquantum.net')
    c.drawRightString(PAGE_W-MARGIN,4*mm,f'Page {doc.page}')
    c.setStrokeColor(RULE_COLOR); c.setLineWidth(0.5)
    c.line(MARGIN,12*mm,PAGE_W-MARGIN,12*mm)
    c.restoreState()

def on_page(c, doc):
    cover_page(c, doc) if doc.page == 1 else normal_page(c, doc)

def S():
    s = {}
    s['badge']   = ParagraphStyle('badge',   fontName='Helvetica-Bold', fontSize=9,   leading=14, textColor=ACCENT_GOLD)
    s['tier']    = ParagraphStyle('tier',    fontName='Helvetica-Bold', fontSize=9,   leading=14, textColor=ACCENT_LIGHT)
    s['ctitle']  = ParagraphStyle('ctitle',  fontName='Helvetica-Bold', fontSize=26,  leading=34, textColor=WHITE, spaceAfter=6)
    s['csub']    = ParagraphStyle('csub',    fontName='Helvetica',      fontSize=15,  leading=21, textColor=ACCENT_LIGHT, spaceAfter=20)
    s['cmeta']   = ParagraphStyle('cmeta',   fontName='Helvetica',      fontSize=10,  leading=16, textColor=TEXT_GRAY, spaceAfter=4)
    s['atitle']  = ParagraphStyle('atitle',  fontName='Helvetica-Bold', fontSize=10,  leading=14, textColor=ACCENT_LIGHT, spaceAfter=4)
    s['abody']   = ParagraphStyle('abody',   fontName='Helvetica',      fontSize=9.5, leading=15, textColor=TEXT_WHITE, alignment=TA_JUSTIFY, spaceAfter=6)
    s['h1']      = ParagraphStyle('h1',      fontName='Helvetica-Bold', fontSize=15,  leading=20, textColor=WHITE, spaceBefore=18, spaceAfter=8)
    s['h2']      = ParagraphStyle('h2',      fontName='Helvetica-Bold', fontSize=11.5,leading=16, textColor=ACCENT_LIGHT, spaceBefore=14, spaceAfter=5)
    s['h3']      = ParagraphStyle('h3',      fontName='Helvetica-Bold', fontSize=10,  leading=14, textColor=TEXT_GRAY, spaceBefore=10, spaceAfter=4)
    s['body']    = ParagraphStyle('body',    fontName='Helvetica',      fontSize=9.5, leading=15, textColor=TEXT_WHITE, alignment=TA_JUSTIFY, spaceAfter=6)
    s['bullet']  = ParagraphStyle('bullet',  fontName='Helvetica',      fontSize=9.5, leading=15, textColor=TEXT_WHITE, leftIndent=16, firstLineIndent=-8, spaceAfter=2)
    s['code']    = ParagraphStyle('code',    fontName='Courier',        fontSize=7.5, leading=11, textColor=ACCENT_LIGHT, leftIndent=4, backColor=CODE_BG)
    s['caption'] = ParagraphStyle('caption', fontName='Helvetica-Oblique', fontSize=8, leading=12, textColor=TEXT_GRAY, alignment=TA_CENTER, spaceBefore=2)
    s['ref']     = ParagraphStyle('ref',     fontName='Helvetica',      fontSize=8.5, leading=13, textColor=TEXT_GRAY, leftIndent=16, firstLineIndent=-16, spaceAfter=2)
    s['gold']    = ParagraphStyle('gold',    fontName='Helvetica-Bold', fontSize=10,  leading=14, textColor=ACCENT_GOLD)
    s['quote']   = ParagraphStyle('quote',   fontName='Helvetica-Oblique', fontSize=10, leading=16, textColor=ACCENT_LIGHT, alignment=TA_CENTER)
    return s

def sp(n=6): return Spacer(1,n)
def rule(s): return HRFlowable(width='100%', thickness=0.5, color=RULE_COLOR, spaceAfter=6, spaceBefore=6)
def arule():  return HRFlowable(width='40%',  thickness=1.5, color=ACCENT_BLUE, spaceAfter=20)

def cb(text, s):
    lines = text.strip().split('\n')
    rows = [[Paragraph(l.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'), s['code'])] for l in lines]
    return Table(rows, colWidths=[PAGE_W-2*MARGIN-16*mm],
        style=TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),CODE_BG),
            ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
            ('BOX',(0,0),(-1,-1),0.5,BORDER_GRAY),
        ]))

def tbl(headers, rows, s, cw=None):
    hs = ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=8, leading=12, textColor=ACCENT_LIGHT)
    cs = ParagraphStyle('td', fontName='Helvetica',      fontSize=8, leading=12, textColor=TEXT_WHITE)
    cg = ParagraphStyle('tg', fontName='Helvetica',      fontSize=8, leading=12, textColor=TEXT_GRAY)
    data = [[Paragraph(h,hs) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), cg if i==0 and len(headers)>2 else cs) for i,c in enumerate(row)])
    avail = PAGE_W-2*MARGIN-4*mm
    if cw is None: cw = [avail/len(headers)]*len(headers)
    return Table(data, colWidths=cw, repeatRows=1,
        style=TableStyle([
            ('BACKGROUND',(0,0),(-1,0),TABLE_HEAD),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[TABLE_ALT,CODE_BG]),
            ('GRID',(0,0),(-1,-1),0.4,TABLE_BORDER),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
        ]))

def box(items, s, title=None, border=None):
    bcolor = border or ACCENT_BLUE
    content = []
    if title: content.append(Paragraph(title, s['atitle']))
    for item in items:
        if isinstance(item, str):
            content.append(Paragraph(f'  {item}', s['abody']))
        else:
            content.append(item)
    return Table([[content]], colWidths=[PAGE_W-2*MARGIN-4*mm],
        style=TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),CODE_BG),
            ('BOX',(0,0),(-1,-1),1.2,bcolor),
            ('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14),
            ('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),
        ]))

def build(output):
    s = S()
    doc = SimpleDocTemplate(output, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN+10*mm, bottomMargin=MARGIN+10*mm,
        title='RFC-ATF-5: Agent Trust Fabric -- Cognitive Governance Layer',
        author='Harold Alberto Nunes Rodelo, OMNIX QUANTUM LTD',
        subject='CGE, GUGT, TGB -- Counterfactual Governance, Universal Invariants, Temporal Bridge',
        keywords='AI governance, CGE, GUGT, TGB, ATF, ML-DSA-65, OMNIX QUANTUM, EU AI Act, NIST AI RMF',
        creator='OMNIX QUANTUM Standards -- omnixquantum.net')
    st = []

    # ==========================================================================
    # COVER
    # ==========================================================================
    st.append(sp(28))
    lw, lh = 4.5*cm, 4.5*cm*(380/522)
    tcol = [
        Paragraph('RFC-ATF-5', s['badge']), sp(4),
        Paragraph('OMNIX Open Standard Series -- Fifth RFC', s['tier']), sp(8),
        Paragraph('Agent Trust Fabric', s['ctitle']),
        Paragraph('Cognitive Governance Layer', s['csub']),
        Paragraph('Counterfactual Governance Engine  |  Grand Unified Governance Theory  |  Temporal Governance Bridge', s['tier']),
    ]
    lcell = Image(LOGO, width=lw, height=lh) if os.path.exists(LOGO) else Paragraph('OMNIX QUANTUM', s['badge'])
    st.append(Table([[tcol, lcell]], colWidths=[PAGE_W-2*MARGIN-lw-8*mm, lw+4*mm],
        style=TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
            ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)])))
    st.append(sp(20)); st.append(arule())

    for label, value in [
        ('Document',      'RFC-ATF-5 -- OMNIX QUANTUM Open Standard'),
        ('Version',       '1.0.0 -- May 2026'),
        ('Author',        'Harold Alberto Nunes Rodelo'),
        ('Institution',   'OMNIX QUANTUM LTD -- 71-75 Shelton Street, London WC2H 9JQ'),
        ('Contact',       'standards@omnixquantum.com'),
        ('Builds on',     'RFC-ATF-1 (DOI 10.5281/zenodo.20155016)'),
        ('',              'RFC-ATF-2 (DOI 10.5281/zenodo.20241344)'),
        ('',              'RFC-ATF-3 (DOI 10.5281/zenodo.20247342)'),
        ('',              'RFC-ATF-4 (DOI 10.5281/zenodo.20368895)'),
        ('Cryptography',  'Dilithium-3 ML-DSA-65 (NIST FIPS 204)'),
        ('Formal Methods','Z3 SMT + TLA+ dual methodology'),
        ('New Invariants', '18 -- CGE-INV-001-007, GUGT-INV-001-006, TGB-INV-001-005'),
        ('Total ATF Inv.','88 across 17 protocol families'),
        ('New DB Tables', '6 -- counterfactual_forks, counterfactual_tokens, universal_invariant_receipts,'),
        ('',              '     temporal_context_snapshots, regulatory_alignment_receipts, temporal_migration_records'),
        ('Designation',   'ATF-CGL-Compliant -- fifth and highest compliance tier'),
        ('Status',        'DRAFT -- pending Zenodo submission'),
    ]:
        st.append(Paragraph(f'<b><font color="#5b5bd6">{label}:</font></b>  {value}' if label else f'   {value}', s['cmeta']))

    st.append(sp(20))
    st.append(HRFlowable(width='100%', thickness=0.5, color=BORDER_GRAY, spaceAfter=12))
    st.append(box([
        Paragraph('Abstract', s['atitle']),
        Paragraph(
            'RFC-ATF-5 specifies the <b>Cognitive Governance Layer (CGL)</b> -- the fifth RFC in the '
            'OMNIX Agent Trust Fabric Open Standard series, extending RFC-ATF-1 through RFC-ATF-4. '
            'The CGL formally closes three governance gaps that no existing AI governance framework '
            '-- academic, regulatory, or commercial -- has previously addressed.',
            s['abody']),
        Paragraph(
            '<b>(1) The Decision Space Gap (Gap_DS).</b>  Prior ATF RFCs record the selected governance path '
            'with cryptographic certainty. They do not record the <i>decision space</i> -- the full set of '
            'governance outcomes reachable under parametric variation. The <b>Counterfactual Governance Engine '
            '(CGE)</b> computes M cryptographically sealed alternative paths (Counterfactual Fork Records, CFRs) '
            'at each evaluation, assembled into a Counterfactual Attestation Token (CAT) bound to the primary '
            'receipt. The CAT provides: offline-verifiable decision space evidence satisfying EU AI Act Art. 9 '
            '"alternatives considered" with PQC-signed artifacts; a <b>fragility_score</b> in [0.0, 1.0] '
            'quantifying decision robustness -- the first governance decision fragility metric in any published '
            'specification; and deterministic Variation Vectors ensuring independent reproducibility.',
            s['abody']),
        Paragraph(
            '<b>(2) The Universal Completeness Gap (Gap_UC).</b>  The <b>Grand Unified Governance Theory (GUGT)</b> '
            'derives six Universal Governance Invariants (UGI-001-006) by formal intersection of EU AI Act, '
            'NIST AI RMF, GCC/DIFC AI Regulation 2024, ISO/IEC 42001:2023, and UK AISI Evaluation Framework '
            'simultaneously. ATF-compliant systems satisfy all six UGIs by construction, earning '
            'GUGT-L3+ATF certification via a single PQC-signed Universal Invariant Receipt (UIR). '
            'This eliminates per-jurisdiction custom compliance analysis for ATF-compliant deployments.',
            s['abody']),
        Paragraph(
            '<b>(3) The Temporal Semantic Gap (Gap_TS).</b>  EU AI Act Art. 72 mandates 7-year retention '
            'for high-risk AI. The <b>Temporal Governance Bridge (TGB)</b> closes the interpretability gap '
            'between nanosecond-precision runtime governance and decade-scale regulatory review. A Temporal '
            'Context Snapshot (TCS) is embedded at nanosecond precision at the moment of every record '
            'issuance, capturing the complete regulatory and threshold context. A Regulatory Alignment '
            'Receipt (RAR) projects historical records to current frameworks at review time without '
            'modifying the original evidence (TGB-INV-002 non-destruction invariant).',
            s['abody']),
    ], s, border=ACCENT_GOLD))
    st.append(PageBreak())

    # ==========================================================================
    # TABLE OF CONTENTS
    # ==========================================================================
    st.append(Paragraph('Table of Contents', s['h1'])); st.append(rule(s))
    toc = [
        ('1.','Introduction and Motivation'),
        ('1.1','The ATF Open Standard Series'),
        ('1.2','Gap Analysis: What RFC-ATF-1/2/3/4 Left Open'),
        ('1.3','Scope of RFC-ATF-5'),
        ('2.','Problem Statement: The Cognitive Governance Gap'),
        ('2.1','The Decision Space Gap (Gap_DS)'),
        ('2.2','The Universal Completeness Gap (Gap_UC)'),
        ('2.3','The Temporal Semantic Gap (Gap_TS)'),
        ('2.4','Formal Definition: Gap_CG'),
        ('3.','Architecture Overview: Cognitive Governance Layer'),
        ('3.1','ATF Stack -- Five-Layer Architecture'),
        ('3.2','CGL Module Independence and Failure Isolation'),
        ('3.3','CGL Record Sequencing'),
        ('4.','Counterfactual Governance Engine (CGE)'),
        ('4.1','Decision Space Architecture'),
        ('4.2','Variation Vector Design and Determinism'),
        ('4.3','Counterfactual Fork Record (CFR) Specification'),
        ('4.4','Counterfactual Attestation Token (CAT) Specification'),
        ('4.5','fragility_score: Decision Robustness Metric'),
        ('4.6','Offline Verification Protocol'),
        ('4.7','CGE Invariants: CGE-INV-001-007'),
        ('4.8','CGE Database Schema'),
        ('5.','Grand Unified Governance Theory (GUGT)'),
        ('5.1','Universal Invariant Architecture'),
        ('5.2','Framework Intersection Methodology'),
        ('5.3','Universal Governance Invariants UGI-001-006'),
        ('5.4','Universal Invariant Receipt (UIR) Specification'),
        ('5.5','GUGT Conformance Levels'),
        ('5.6','Cross-Jurisdiction Framework Mapping'),
        ('5.7','GUGT Invariants: GUGT-INV-001-006'),
        ('5.8','GUGT Database Schema'),
        ('6.','Temporal Governance Bridge (TGB)'),
        ('6.1','Two-Scale Architecture: Nanoseconds to Years'),
        ('6.2','Temporal Context Snapshot (TCS) Specification'),
        ('6.3','Regulatory Alignment Receipt (RAR) Specification'),
        ('6.4','Temporal Migration Record (TMR) Specification'),
        ('6.5','TGB Projection Rulebook'),
        ('6.6','TGB Invariants: TGB-INV-001-005'),
        ('6.7','TGB Database Schema'),
        ('7.','Formal Verification (OMNIX-FVS-1.0 Extension)'),
        ('7.1','Z3 SMT Proof Targets'),
        ('7.2','TLA+ Coverage'),
        ('8.','Combined Invariant Summary -- 88 Total'),
        ('9.','ATF-CGL-Compliant Designation'),
        ('10.','Implementation Reference'),
        ('10.1','Reference Implementation Components'),
        ('10.2','API Endpoints'),
        ('10.3','Configuration Parameters'),
        ('11.','Security Considerations'),
        ('12.','Novel Contributions'),
        ('13.','Distinction from Prior Art'),
        ('14.','Regulatory Alignment'),
        ('15.','Known Limitations and Open Questions'),
        ('16.','References'),
        ('A.','Appendix A -- CGL Wire Formats (JSON Schemas)'),
        ('B.','Appendix B -- GUGT Framework Clause Mapping'),
        ('C.','Appendix C -- ATF-CGL-Compliant Checklist'),
    ]
    for num, title in toc:
        indent = 16 if '.' in num and len(num) > 2 else 0
        bold = not indent
        ps = ParagraphStyle('toc', fontName='Helvetica-Bold' if bold else 'Helvetica',
            fontSize=9.5, leading=16, textColor=WHITE if bold else TEXT_WHITE, leftIndent=indent)
        st.append(Paragraph(f'{num}  {title}', ps))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 1 -- INTRODUCTION
    # ==========================================================================
    st.append(Paragraph('1.  Introduction and Motivation', s['h1'])); st.append(rule(s))
    st.append(Paragraph('1.1  The ATF Open Standard Series', s['h2']))
    st.append(Paragraph(
        'The OMNIX Agent Trust Fabric is an open standard series for cryptographic authority governance '
        'of autonomous AI agents. Each RFC addresses a distinct, formally scoped gap in the governance '
        'infrastructure required for enterprise and regulated AI deployments.', s['body']))
    st.append(tbl(['RFC','Layer','Defining Question','Status'],
        [['RFC-ATF-1','Identity & Delegation','Who authorized this agent, with what authority, and can that be proved offline?','Published DOI: 10.5281/zenodo.20155016'],
         ['RFC-ATF-2','Runtime Continuity','Was authority continuously valid throughout execution, and was HALT propagated correctly?','Published DOI: 10.5281/zenodo.20241344'],
         ['RFC-ATF-3','Evidence & Forensic','Where does evidence go and who can verify it years later without any platform access?','Published DOI: 10.5281/zenodo.20247342'],
         ['RFC-ATF-4','Proactive Governance','What happened between requests? Is recalibration safe? Are receipts semantically portable cross-domain?','Published DOI: 10.5281/zenodo.20368895'],
         ['RFC-ATF-5','Cognitive Governance','What else could have happened? Is governance universally complete? Will evidence remain interpretable across time?','This document']],
        s, cw=[2.0*cm,3.8*cm,6.5*cm,4.5*cm]))
    st.append(sp(8))
    st.append(Paragraph('1.2  Gap Analysis: What RFC-ATF-1/2/3/4 Left Open', s['h2']))
    st.append(Paragraph(
        'The four prior RFCs collectively establish a complete, formally specified governance pipeline: '
        'identity and delegation (RFC-ATF-1), runtime integrity and HALT propagation (RFC-ATF-2), '
        'evidence lifecycle and forensic packages (RFC-ATF-3), and proactive veto plus semantic '
        'portability (RFC-ATF-4). This pipeline closes the execution governance gap.', s['body']))
    st.append(Paragraph(
        'Three structural questions remain outside the scope of Layers 1-4. These are not '
        'implementation gaps -- they are specification gaps that require new record types, new '
        'invariants, and new formal proofs. RFC-ATF-5 closes all three.', s['body']))
    for q, owner in [
        ('What other governance outcomes were possible at decision time, and can any party verify this offline?', 'Gap_DS -- closed by CGE'),
        ('Does a single governance artifact certify compliance with all major regulatory frameworks simultaneously?', 'Gap_UC -- closed by GUGT'),
        ('Will a governance record issued today remain interpretable in 2031 under an amended EU AI Act?', 'Gap_TS -- closed by TGB'),
    ]:
        st.append(Paragraph(f'  <b>Q:</b> {q}<br/>  <b>A:</b> {owner}', s['bullet'])); st.append(sp(4))
    st.append(Paragraph('1.3  Scope of RFC-ATF-5', s['h2']))
    st.append(Paragraph(
        'RFC-ATF-5 specifies: (1) the Counterfactual Governance Engine (CGE) -- new DB tables, '
        'record types CFR and CAT, 7 invariants; (2) the Grand Unified Governance Theory (GUGT) -- '
        'UGI-001-006, UIR record type, 4 conformance levels, 6 invariants; (3) the Temporal '
        'Governance Bridge (TGB) -- TCS, RAR, and TMR record types, projection rulebook, 5 invariants. '
        'Total: 18 new invariants, 6 new DB tables, 5 new record types.', s['body']))
    st.append(Paragraph(
        'All three modules are independently operable (CGL-INDEPENDENT-001). Failure of any CGL module '
        'is non-blocking for the primary ATF record. Each module degrades gracefully with flag notation '
        'on the primary record rather than halting the governance pipeline.', s['body']))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 2 -- PROBLEM STATEMENT
    # ==========================================================================
    st.append(Paragraph('2.  Problem Statement: The Cognitive Governance Gap', s['h1'])); st.append(rule(s))
    st.append(Paragraph('2.1  The Decision Space Gap (Gap_DS)', s['h2']))
    st.append(Paragraph(
        'The ATF stack through RFC-ATF-4 guarantees that DP = SP (Documented Path = Selected Path) with '
        'cryptographic certainty via PQC signatures and append-only receipts. What remains undocumented is '
        'the Decision Space (DS) -- the full set of governance outcomes that existed at evaluation time '
        'under parametric variations of the authority configuration.', s['body']))
    st.append(cb(
"""  DECISION SPACE STRUCTURE:

  DS = { NOMINAL (CES >= 80), MONITORING (CES 50-79), WARNING (CES 30-49), HALT (CES < 30) }

  For a given evaluation with CES = 82.5 (primary outcome = NOMINAL):

  +-------------------+-----------------------------+------------------------------+
  | Outcome           | Reachability                | Documenter (pre RFC-ATF-5)   |
  +-------------------+-----------------------------+------------------------------+
  | NOMINAL           | Selected -- SP = DP         | Primary receipt (PQC-signed) |
  | MONITORING        | Reachable at -20% VV        | NOT documented               |
  | WARNING           | Reachable at -15% budget VV | NOT documented               |
  | HALT              | Reachable at -40% VV        | NOT documented               |
  +-------------------+-----------------------------+------------------------------+

  Gap_DS = DS \\ {SP} = { MONITORING, WARNING, HALT }

  Stakeholders who need Gap_DS documented:
  [A] Regulatory auditors: EU AI Act Art. 9 -- "alternatives considered"
  [B] Risk officers:       fragility_score = |divergent_paths| / |total_paths|
  [C] Legal counsel:       "could the system have reached a HALT outcome?"

  CGE closes Gap_DS: each element of Gap_DS becomes a PQC-signed CFR in the CAT.""", s))
    st.append(sp(8))

    st.append(Paragraph('2.2  The Universal Completeness Gap (Gap_UC)', s['h2']))
    st.append(Paragraph(
        'The ATF stack satisfies Governance Completeness (GC) for specific (Framework, Agent-type) pairs. '
        'It does not formally assert Multi-Frame Completeness (MFC). Enterprise buyers deploying across '
        'EU + US + GCC + ISO jurisdictions must engage external counsel to verify compliance in each '
        'framework independently -- a significant cost barrier for adoption.', s['body']))
    st.append(cb(
"""  WITHOUT RFC-ATF-5 GUGT:
  +------------------+   +------------------+   +------------------+   +------------------+
  | EU AI Act        |   | NIST AI RMF      |   | GCC/DIFC         |   | ISO/IEC 42001    |
  | compliance check |   | compliance check |   | compliance check |   | compliance check |
  | (custom mapping) |   | (custom mapping) |   | (custom mapping) |   | (custom mapping) |
  +------------------+   +------------------+   +------------------+   +------------------+
  4 separate analyses, 4 separate artifacts, no unified proof

  WITH RFC-ATF-5 GUGT:
  +-----------------------------------------------------------------------+
  |  Universal Invariant Receipt (UIR)  GUGT-L3+ATF                       |
  |  UGI-001 [OK]  UGI-002 [OK]  UGI-003 [OK]                            |
  |  UGI-004 [OK]  UGI-005 [OK]  UGI-006 [OK]                            |
  |  PQC-signed ML-DSA-65 -- offline-verifiable                           |
  +-----------------------------------------------------------------------+
  1 artifact satisfies EU + US + GCC + ISO + UK AISI simultaneously
  ATF-compliant systems earn GUGT-L3+ATF by construction -- zero custom analysis""", s))
    st.append(sp(8))

    st.append(Paragraph('2.3  The Temporal Semantic Gap (Gap_TS)', s['h2']))
    st.append(Paragraph(
        'EU AI Act Art. 72 mandates 7-year retention for high-risk AI decisions. A receipt issued in '
        '2026 under "EU AI Act 2024 v1.0" with nominal_threshold = 80.0 must remain interpretable '
        'when reviewed in 2033 under an amended framework -- without access to the original platform, '
        'without the issuing team, and without guessing what the regulatory context was.', s['body']))
    st.append(Paragraph(
        'This problem was formally identified during ATF Field Specification Partner Integration: '
        '<i>"The DSPP addresses semantic divergence at a point in time. The remaining open problem is '
        'the temporal dimension -- how does an auditor five years from now interpret a receipt issued '
        'under today\'s regulatory context, without the platform, without us, and without guessing?"</i> '
        '(Antonio Socorro, CAI-EXPERT-LAB)', s['body']))
    st.append(cb(
"""  WITHOUT TGB:                         WITH RFC-ATF-5 TGB:
  +---------------------+              +---------------------------------------------+
  | receipt.json        |              | receipt.json                                |
  | issued_at: 2026     |              | +--> TCS (embedded at T=0 nanosecond)        |
  | outcome: NOMINAL    |              |      | eu_ai_act_version: EU_AI_ACT_2024_v1.0|
  | ces_score: 82.5     |              |      | nominal_threshold: 80.0               |
  | threshold: 80.0     |              |      | atf_spec_version: RFC-ATF-5_v1.0      |
  |                     |              |      | tcs_seal: ML-DSA-65 [OK]              |
  | [no context]        |              | +--> RAR (produced at T=7yr, non-destr.)     |
  | [ambiguous in 2033] |              |      | projection to EU_AI_ACT_2033_v3.0     |
  +---------------------+              |      | original_record_integrity: VERIFIED   |
   Misclassification risk              |      | rar_seal: ML-DSA-65 [OK]              |
                                       +---------------------------------------------+
                                        Zero ambiguity -- self-contained projection""", s))
    st.append(sp(8))

    st.append(Paragraph('2.4  Formal Definition: Gap_CG', s['h2']))
    st.append(box([
        Paragraph('Gap_CG = Gap_DS U Gap_UC U Gap_TS', s['gold']),
        Paragraph(
            'Gap_CG is the Cognitive Governance Gap -- the set of all governance properties that an ATF-compliant '
            'system through RFC-ATF-4 does not formally specify. RFC-ATF-5 closes Gap_CG completely. '
            'The Cognitive Governance Layer (CGL) is the set of protocol elements, record types, invariants, '
            'and formal proofs that constitute this closure.', s['abody']),
    ], s, border=ACCENT_GOLD))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 3 -- ARCHITECTURE
    # ==========================================================================
    st.append(Paragraph('3.  Architecture Overview: Cognitive Governance Layer', s['h1'])); st.append(rule(s))
    st.append(Paragraph('3.1  ATF Stack -- Five-Layer Architecture', s['h2']))
    st.append(cb(
"""  +=========================================================================+
  |         ATF PROTOCOL STACK -- FIVE-LAYER COMPLETE ARCHITECTURE         |
  +=========================================================================+
  |                                                                         |
  | Layer 5 -- COGNITIVE GOVERNANCE LAYER (RFC-ATF-5) ---------- * THIS RFC|
  | +-----------------------------------------------------------------------+
  | | CGE: Counterfactual Governance Engine                                 |
  | |   -> M alternative governance paths, PQC-sealed as CAT                |
  | |   -> fragility_score in [0.0, 1.0] -- decision robustness metric      |
  | | GUGT: Grand Unified Governance Theory                                 |
  | |   -> 6 UGIs derived by 5-framework intersection                       |
  | |   -> UIR certifies EU+NIST+GCC+ISO+UK simultaneously                  |
  | | TGB: Temporal Governance Bridge                                       |
  | |   -> TCS at nanosecond issuance -- RAR at 7-year review               |
  | |   -> TMR at each evidence lifecycle transition                        |
  | +-----------------------------------------------------------------------+
  |                                                                         |
  | Layer 4 -- PROACTIVE GOVERNANCE PLANE (RFC-ATF-4)                       |
  | +-----------------------------------------------------------------------+
  | | AGVP: Anticipatory Governance Veto Protocol                           |
  | | SSD:  Structural Shift Detection                                      |
  | | DSPP: Dynamic Semantic Portability Protocol                           |
  | +-----------------------------------------------------------------------+
  |                                                                         |
  | Layer 3 -- EVIDENCE AND FORENSIC PLANE (RFC-ATF-3)                      |
  | +-----------------------------------------------------------------------+
  | | GPIL: Governance Policy Interoperability Layer                        |
  | | ELC:  Evidence Lifecycle Classification (HOT/WARM/COLD)               |
  | | OEP:  OMNIX Evidence Package -- offline-verifiable forensic bundle    |
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
  |                                                                         |
  +=========================================================================+
  | Invariant count: L1=6, L2=8, L3=40, L4=16, L5=18  --> TOTAL: 88        |
  | Compliance tier: ATF-CGL-Compliant (5th and highest tier)               |
  +=========================================================================+""", s))
    st.append(sp(6))

    st.append(Paragraph('3.2  CGL Module Independence and Failure Isolation', s['h2']))
    st.append(Paragraph(
        'All three CGL modules are independently operable. The failure of any module does not block '
        'issuance of the primary ATF record. This is enforced by the CGL Independence Principle:', s['body']))
    st.append(tbl(['Module','Dependency on Primary Record','Blocking on Failure','Flag on Failure'],
        [['CGE','Primary record must be persisted FIRST (CGE-INV-002)','Non-blocking -- CAT is async','CGE_INCOMPLETE on primary record'],
         ['GUGT','UIR assessed against deployment configuration, not per-record','Non-blocking -- on-demand per deployment','GUGT_UNASSESSED on deployment'],
         ['TGB','TCS embedded synchronously, then bound to primary record','Non-blocking -- TCS failure retried async','TGB_INCOMPLETE on primary record']],
        s, cw=[2.5*cm,5.5*cm,3.5*cm,5.3*cm]))
    st.append(sp(6))

    st.append(Paragraph('3.3  CGL Record Sequencing', s['h2']))
    st.append(cb(
"""  For every primary ATF record R:

  Step 1 -- Issue and persist R (Layer 1-4 record, all prior invariants apply)
             R.content_hash sealed -- R.pqc_signature applied -- DB INSERT committed

  Step 2 -- TCS embedding (SYNCHRONOUS, part of R creation pipeline)
             TCS.regulatory_context captured at R.issued_at nanosecond
             tcs_hash included in R.posture_state_hash
             TCS persisted -- TCS PQC-signed

  Step 3 -- CGE fork computation (ASYNC, begins after Step 1 completes)
             M CFRs computed with deterministic VVs (seed = SHA256(eval_id || receipt_id))
             Each CFR: read-only re-evaluation, no receipts/HALTs produced
             CAT assembled: cat_root_hash = sha256(sorted(cfr_content_hashes))
             CAT PQC-signed and persisted

  Step 4 -- UIR issuance (ON DEMAND, not per-record, per deployment)
             GUGT assessment run against deployment configuration
             UIR issued with 6 UGI results, PQC-signed

  Invariant order guarantee:
  T(primary.persist) < T(tcs.persist) < T(cge.start)  [CGE-INV-002 + TGB-INV-001]
  Any CGL failure is non-blocking -- primary record always valid and immutable""", s))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 4 -- CGE
    # ==========================================================================
    st.append(Paragraph('4.  Counterfactual Governance Engine (CGE)', s['h1'])); st.append(rule(s))
    st.append(Paragraph(
        'The CGE computes M alternative governance paths at the moment of a primary ATF governance '
        'evaluation. M is configurable via CGE_FORK_COUNT (default: 3, range: 1-7). Each path applies '
        'a deterministic Variation Vector (VV) to the primary evaluation inputs and re-executes governance '
        'logic in read-only simulation mode. The CGE produces no HALTs, no escalations, and no side effects '
        'on the live system. Its sole output is a set of PQC-signed Counterfactual Fork Records (CFRs) '
        'assembled into a Counterfactual Attestation Token (CAT).', s['body']))

    st.append(Paragraph('4.1  Decision Space Architecture', s['h2']))
    st.append(cb(
"""  PRIMARY EVALUATION (sealed first -- CGE-INV-002):
  +------------------------------------------------------------------+
  | ATFDR-4A2B8F1C3D5E7A9B                                          |
  | outcome: NOMINAL   ces_score: 82.5   pqc_sig: ML-DSA-65 [OK]  |
  +------------------------------------------------------------------+
                       |  DB INSERT committed
                       v  CGE begins NOW (async)
  +------------------------------------------------------------------+
  | VARIATION VECTOR GENERATION                                      |
  | seed = SHA256(evaluation_id || primary_receipt_id)              |
  | VV-1: authority_budget_delta_pct     = -0.20                    |
  | VV-2: ces_threshold_nominal_override = 88.0                     |
  | VV-3: delegation_depth_limit         = 3                        |
  | (Deterministic: same seed always produces same VVs)             |
  +------------------------------------------------------------------+
        |                  |                  |
        v                  v                  v  (read-only re-evaluations)
  +-----------+      +-----------+      +-----------+
  | CFR-1     |      | CFR-2     |      | CFR-3     |
  | MONITORING|      | NOMINAL   |      | HALT      |
  | ces: 72.0 |      | ces: 82.5 |      | ces: 15.3 |
  | diverges: |      | diverges: |      | diverges: |
  |   true    |      |   false   |      |   true    |
  | ML-DSA-65 |      | ML-DSA-65 |      | ML-DSA-65 |
  +-----------+      +-----------+      +-----------+
        |                  |                  |
        +------------------+------------------+
                           |
  +------------------------------------------------------------------+
  | COUNTERFACTUAL ATTESTATION TOKEN (CAT)                           |
  | cat_root_hash = sha256(sort([cfr1_hash, cfr2_hash, cfr3_hash])) |
  | cfr_count: 3   divergence_count: 2                              |
  | fragility_score: 0.67  (2 out of 3 paths diverge)              |
  | cat_seal: ML-DSA-65 over cat_root_hash                          |
  | verification: offline, no platform access required              |
  +------------------------------------------------------------------+""", s))
    st.append(sp(6))

    st.append(Paragraph('4.2  Variation Vector Design and Determinism', s['h2']))
    st.append(Paragraph(
        'Variation Vectors are the only mechanism by which CGE explores the decision space. '
        'Every VV is deterministically derived from the evaluation seed, ensuring that any '
        'independent party can reproduce all CFRs given only the primary receipt and the CGE '
        'configuration. This is the basis for CGE-INV-007 (offline verifiability).', s['body']))
    st.append(tbl(['VV Field Category','Description','Bound (CGE-INV-005)','Example Delta'],
        [['authority_budget_delta_pct','Percentage change applied to authority_budget_granted','abs(delta) <= 0.40','-0.20 (20% reduction)'],
         ['ces_threshold_nominal_override','Override of the NOMINAL outcome threshold','abs(delta) <= 0.40','88.0 (raised from 80.0)'],
         ['delegation_depth_limit','Maximum delegation chain depth allowed','abs(delta) <= 0.40','3 (reduced from 5)'],
         ['monitoring_window_override','Temporal window for monitoring aggregation','abs(delta) <= 0.40','300s (reduced from 600s)'],
         ['fragmentation_limit_override','AFG fragmentation threshold','abs(delta) <= 0.40','0.75 (from 0.90)']],
        s, cw=[4.5*cm,5.5*cm,3.5*cm,3.3*cm]))
    st.append(sp(6))
    st.append(Paragraph(
        'VVs exceeding the CGE_MAX_VARIATION_PCT bound are rejected with a null CFR carrying '
        'flag REJECTED. Null CFRs do NOT count toward cfr_count for CGE-INV-001 purposes. '
        'This prevents exploration of parametric spaces so extreme they have no governance '
        'interpretive value.', s['body']))

    st.append(Paragraph('4.3  Counterfactual Fork Record (CFR) Specification', s['h2']))
    st.append(cb(
"""  CFR (Counterfactual Fork Record) -- identifier: CFR-{16HEX}

  COMMITTED FIELDS (included in posture_state_hash_cf):
    cfr_id                   : "CFR-4A2B8F1C3D5E7A9B"
    primary_receipt_id       : "ATFDR-..." (binding to primary record)
    evaluation_id            : "CGE-EVAL-..." (evaluation session)
    variation_vector         : { "authority_budget_delta_pct": -0.20, ... }
    counterfactual_ces_score : 72.0
    counterfactual_outcome   : "MONITORING"
    diverges_from_primary    : true
    issued_at                : "2026-05-26T14:00:00.123456789+00:00"

  SEAL FIELDS:
    posture_state_hash_cf    : SHA256(canonical JSON of committed fields)
    content_hash_cf          : SHA256(canonical JSON of all fields incl. posture_hash)
    pqc_algorithm            : "ML-DSA-65"
    pqc_signature            : base64(ML-DSA-65.sign(content_hash_cf))

  METADATA:
    cfr_status               : "ACCEPTED" | "REJECTED" (VV bound violation)
    vv_seed                  : SHA256(evaluation_id || primary_receipt_id)
    rejection_reason         : null | "CGE_VV_BOUND_VIOLATION"
    cat_id                   : "CAT-..." (parent token)""", s))
    st.append(sp(6))

    st.append(Paragraph('4.4  Counterfactual Attestation Token (CAT) Specification', s['h2']))
    st.append(cb(
"""  CAT (Counterfactual Attestation Token) -- identifier: CAT-{16HEX}

  COMMITTED FIELDS:
    cat_id                   : "CAT-9F3A7B2C1D4E5F6A"
    primary_receipt_id       : "ATFDR-..." (binding to primary record)
    evaluation_id            : "CGE-EVAL-..."
    cfr_ids                  : ["CFR-...", "CFR-...", "CFR-..."]
    cfr_count                : 3
    divergence_count         : 2
    cat_root_hash            : SHA256(sort([cfr_1_content_hash, cfr_2_content_hash, ...]))
    fragility_score          : 0.6667  (divergence_count / cfr_count)
    cge_fork_count_config    : 3
    issued_at                : "2026-05-26T14:00:00.200000000+00:00"

  SEAL FIELDS:
    content_hash_cat         : SHA256(canonical JSON of all fields excl. seal fields)
    pqc_algorithm            : "ML-DSA-65"
    cat_seal                 : base64(ML-DSA-65.sign(content_hash_cat))

  COMPUTATION:
    cat_root_hash = sha256("|".join(sorted([cfr.content_hash_cf for cfr in cfrs])))
    fragility_score = divergence_count / cfr_count  in [0.0, 1.0]""", s))
    st.append(sp(6))

    st.append(Paragraph('4.5  fragility_score: Decision Robustness Metric', s['h2']))
    st.append(Paragraph(
        'The fragility_score is the first formally specified decision robustness metric in any published '
        'AI governance standard. It quantifies what proportion of the explored decision space diverges '
        'from the primary governance outcome under parametric variation.', s['body']))
    st.append(tbl(['fragility_score','Interpretation','Governance Signal','Recommended Action'],
        [['0.0','All counterfactuals agree with primary outcome','Decision robust -- parameter-insensitive','No action required'],
         ['0.01 - 0.33','Minority of paths diverge','Decision moderately robust','Periodic review recommended'],
         ['0.34 - 0.66','Roughly half of paths diverge','Decision sensitive to parameters','Risk review required'],
         ['0.67 - 0.99','Majority of paths diverge','Decision fragile -- high parameter sensitivity','Escalate to human review'],
         ['1.0','All counterfactuals diverge from primary','Maximum fragility -- fully parameter-dependent','Mandatory human override']],
        s, cw=[2.8*cm,4.5*cm,4.0*cm,5.5*cm]))
    st.append(sp(6))
    st.append(cb(
"""  FRAGILITY SCORE COMPUTATION (CGE-INV-004):
    fragility_score = divergence_count / cfr_count

  Where:
    divergence_count = count(cfr for cfr in cfrs if cfr.diverges_from_primary == true)
    cfr_count        = count(cfr for cfr in cfrs if cfr.cfr_status == "ACCEPTED")

  CONSTRAINTS:
    fragility_score in [0.0, 1.0]  -- Z3 proof target CGE-FRAGILITY-BOUND-LO/HI
    fragility_score > 1.0 is rejected as a computation error (CGE-INV-004 violation)
    fragility_score is bound to CAT via content_hash_cat -- tamper-evident""", s))
    st.append(sp(6))

    st.append(Paragraph('4.6  Offline Verification Protocol', s['h2']))
    st.append(Paragraph(
        'Any party can verify a CAT and its CFRs without access to the issuing platform, without '
        'API credentials, and without network access. The following procedure is sufficient:', s['body']))
    st.append(cb(
"""  OFFLINE CAT VERIFICATION PROCEDURE (CGE-INV-007):

  Input: primary_receipt.json, cat.json, cfr_list.json, public_key.pem

  Step 1 -- Verify primary receipt integrity
    hash_check = sha256(canonical_json(primary_receipt.committed_fields))
    assert hash_check == primary_receipt.content_hash
    verify ML-DSA-65(primary_receipt.pqc_signature, primary_receipt.content_hash, pubkey)

  Step 2 -- Verify CAT integrity
    hash_check = sha256(canonical_json(cat.committed_fields))
    assert hash_check == cat.content_hash_cat
    verify ML-DSA-65(cat.cat_seal, cat.content_hash_cat, pubkey)

  Step 3 -- Verify CAT root hash
    computed_root = sha256("|".join(sorted([cfr.content_hash_cf for cfr in cfrs])))
    assert computed_root == cat.cat_root_hash

  Step 4 -- Verify each CFR
    For each cfr in cfr_list:
      hash_check = sha256(canonical_json(cfr.committed_fields))
      assert hash_check == cfr.content_hash_cf
      verify ML-DSA-65(cfr.pqc_signature, cfr.content_hash_cf, pubkey)
      assert cfr.primary_receipt_id == primary_receipt.receipt_id

  Step 5 -- Verify VV determinism
    for each cfr in cfr_list:
      expected_seed = sha256(cfr.evaluation_id + "|" + cfr.primary_receipt_id)
      assert cfr.vv_seed == expected_seed

  Step 6 -- Verify fragility_score
    computed_fragility = count(cfr for cfr in cfrs if cfr.diverges_from_primary) / len(cfrs)
    assert abs(computed_fragility - cat.fragility_score) < 0.0001

  Result: VERIFIED | NOT_VERIFIED (with specific failure step)""", s))
    st.append(sp(6))

    st.append(Paragraph('4.7  CGE Invariants: CGE-INV-001-007', s['h2']))
    st.append(tbl(['Invariant','Statement','Violation Consequence'],
        [['CGE-INV-001','For every evaluation with CGE_ENABLED=true, a CAT with at least 1 accepted CFR MUST be produced and persisted','CGE_INCOMPLETE flag written to primary record; CAT retried async'],
         ['CGE-INV-002','Primary decision outcome MUST be identical regardless of whether CGE_ENABLED is true or false','Critical structural defect -- CGE is strictly read-only post-primary-commit'],
         ['CGE-INV-003','Every accepted CFR MUST carry a valid ML-DSA-65 signature over its content_hash_cf','Unsigned or invalid-signature CFR rejected from CAT; logged as CGE_CFR_SIG_FAIL'],
         ['CGE-INV-004','cat_root_hash = sha256(sorted(cfr_content_hashes)); fragility_score = divergence_count / cfr_count in [0.0, 1.0]','Root hash mismatch or out-of-range fragility_score treated as computation error'],
         ['CGE-INV-005','abs(VV field delta) <= CGE_MAX_VARIATION_PCT (default 0.40, max 0.40)','VV rejected; null CFR with REJECTED status; logged CGE_VV_BOUND_VIOLATION'],
         ['CGE-INV-006','Tables atf_counterfactual_forks and atf_counterfactual_tokens are append-only; UPDATE and DELETE are prohibited','DB trigger rejects update/delete; event logged as CGE_IMMUTABILITY_VIOLATION'],
         ['CGE-INV-007','A CAT MUST be independently verifiable offline using only: primary receipt, cat.json, cfr_list.json, public_key.pem','Verification procedure failure indicates structural defect in CAT construction']],
        s, cw=[3.0*cm,7.2*cm,6.6*cm]))
    st.append(sp(6))

    st.append(Paragraph('4.8  CGE Database Schema', s['h2']))
    st.append(cb(
"""  -- Table: atf_counterfactual_forks  (append-only, CGE-INV-006)
  CREATE TABLE IF NOT EXISTS atf_counterfactual_forks (
      id                       SERIAL PRIMARY KEY,
      cfr_id                   VARCHAR(50)   UNIQUE NOT NULL,
      cat_id                   VARCHAR(50)   NOT NULL,
      primary_receipt_id       VARCHAR(100)  NOT NULL,
      evaluation_id            VARCHAR(100)  NOT NULL,
      variation_vector         JSONB         NOT NULL,
      counterfactual_ces_score DECIMAL(10,4),
      counterfactual_outcome   VARCHAR(30),
      diverges_from_primary    BOOLEAN       NOT NULL DEFAULT false,
      cfr_status               VARCHAR(20)   NOT NULL DEFAULT 'ACCEPTED',
      rejection_reason         VARCHAR(100),
      vv_seed                  VARCHAR(64),
      posture_state_hash_cf    VARCHAR(64)   NOT NULL,
      content_hash_cf          VARCHAR(64)   NOT NULL,
      pqc_algorithm            VARCHAR(30)   DEFAULT 'ML-DSA-65',
      pqc_signature            TEXT,
      issued_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW()
  );

  -- Table: atf_counterfactual_tokens  (append-only, CGE-INV-006)
  CREATE TABLE IF NOT EXISTS atf_counterfactual_tokens (
      id                       SERIAL PRIMARY KEY,
      cat_id                   VARCHAR(50)   UNIQUE NOT NULL,
      primary_receipt_id       VARCHAR(100)  NOT NULL,
      evaluation_id            VARCHAR(100)  NOT NULL,
      cfr_ids                  JSONB         NOT NULL,
      cfr_count                INTEGER       NOT NULL,
      divergence_count         INTEGER       NOT NULL DEFAULT 0,
      cat_root_hash            VARCHAR(64)   NOT NULL,
      fragility_score          DECIMAL(8,4)  NOT NULL
                               CHECK (fragility_score >= 0.0 AND fragility_score <= 1.0),
      cge_fork_count_config    INTEGER       NOT NULL DEFAULT 3,
      content_hash_cat         VARCHAR(64)   NOT NULL,
      pqc_algorithm            VARCHAR(30)   DEFAULT 'ML-DSA-65',
      cat_seal                 TEXT,
      issued_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW()
  );""", s))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 5 -- GUGT
    # ==========================================================================
    st.append(Paragraph('5.  Grand Unified Governance Theory (GUGT)', s['h1'])); st.append(rule(s))
    st.append(Paragraph(
        'The GUGT establishes a formal meta-layer above the ATF protocol stack. It derives six '
        'Universal Governance Invariants (UGI-001-006) by exhaustive intersection analysis of five '
        'major regulatory frameworks, establishing the minimal sufficient set of properties for '
        'Multi-Frame Completeness (MFC). The GUGT does not replace any prior ATF invariant -- it '
        'provides a unified certification artifact (UIR) that proves all six UGIs are satisfied '
        'simultaneously, for any agent type, under any covered framework.', s['body']))

    st.append(Paragraph('5.1  Universal Invariant Architecture', s['h2']))
    st.append(Paragraph(
        'The GUGT invariant derivation follows a four-step methodology: (1) extract governance '
        'requirements from each framework at the clause level; (2) map each clause to ATF protocol '
        'elements; (3) identify requirements present in all five frameworks simultaneously '
        '(the intersection); (4) formalize each intersecting requirement as a UGI with a precise '
        'ATF mechanism reference.', s['body']))
    st.append(cb(
"""  FIVE-FRAMEWORK INTERSECTION METHODOLOGY:

  Framework       | Human   | Offline | Exec    | Pre-Comm | No-Self | Self-   |
                  | Anchor  | Verify  | Bound   | Posture  | Modify  | Contain |
  ----------------+---------+---------+---------+----------+---------+---------+
  EU AI Act       | Art.14  | Art.11  | Art.9   | Art.9(7) | Art.14  | Art.18  |
  NIST AI RMF     |GOVERN1.1| MAP 5.2 |MANAGE2.2|MEASURE2.5|GOVERN6.1| MAP 5.1 |
  GCC/DIFC        | Art.8   | Art.12  | Art.9   | Art.9    | Art.10  | Art.14  |
  ISO/IEC 42001   | Sec.6.2 | Sec.9.1 | Sec.8.4 | Sec.8.5  |Sec.6.1.2| Sec.9.3 |
  UK AISI         | Sec.3   | Sec.4   | Sec.4   | Sec.4    | Sec.5   | Sec.5   |
  ----------------+---------+---------+---------+----------+---------+---------+
  INTERSECTION    | UGI-001 | UGI-002 | UGI-003 | UGI-004  | UGI-005 | UGI-006 |
  ----------------+---------+---------+---------+----------+---------+---------+

  All five frameworks require all six properties simultaneously.
  ATF-compliant systems satisfy all six by construction -> GUGT-L3+ATF by construction.""", s))
    st.append(sp(6))

    st.append(Paragraph('5.2  Framework Intersection Methodology', s['h2']))
    st.append(Paragraph(
        'The intersection was conducted at clause level, not at framework level. Each of the five '
        'frameworks was mapped to a structured requirement matrix. A requirement is included in '
        'the UGI set only if an equivalent requirement exists in all five frameworks -- weaker '
        'requirements that appear in only four or fewer frameworks are not universalized.', s['body']))
    st.append(Paragraph(
        'The intersection yields exactly six requirements. This is not a design choice -- it is the '
        'mathematical result of the cross-framework analysis. No requirements were added or removed '
        'based on ATF capability. The six UGIs represent the complete intersection of the five '
        'frameworks over the governance domain.', s['body']))

    st.append(Paragraph('5.3  Universal Governance Invariants UGI-001-006', s['h2']))
    for ugi, name, statement, mech, frameworks in [
        ('UGI-001','Human Authority Anchor',
         'Every governance decision by an autonomous AI agent MUST trace to an identified, cryptographically '
         'bound human principal via a verifiable delegation chain, provable offline.',
         'ATF DR chain_root_id -> Tier-1 human principal. ATF-INV-002 (acyclicity) + ATF-INV-006 (offline verifiability) satisfy UGI-001 by construction.',
         'EU Art.14/17, NIST GOVERN 1.1, GCC Art.8, ISO Sec.6.2, UK AISI Sec.3'),
        ('UGI-002','Offline-Verifiable Decision Evidence',
         'Every governance decision record MUST be independently verifiable by any authorized party using '
         'only the artifacts themselves, without accessing the issuing platform or any network service.',
         'OEP two-phase PQC seal (OEP-INV-001 through OEP-INV-006). FEA-INV-001 through FEA-INV-005. CLI verifier.',
         'EU Art.11/12, NIST MAP 5.2, GCC Art.12, ISO Sec.9.1, UK AISI Sec.4'),
        ('UGI-003','Execution-Time Boundary Enforcement',
         'Governance controls MUST be enforced at the moment of execution, not applied retrospectively, '
         'with a cryptographically sealed artifact produced at the exact moment of enforcement.',
         'TAR (Temporal Admissibility Record) issued BEFORE governance logic executes. RCR HALT at nanosecond precision (RGC-INV-003, RGC-INV-005).',
         'EU Art.9, NIST MANAGE 2.2, GCC Art.9, ISO Sec.8.4, UK AISI Sec.4'),
        ('UGI-004','Pre-Committed Posture Assessment',
         'The input state assessment MUST be cryptographically committed before the governance output '
         'is computed, preventing post-hoc rationalization of the decision basis.',
         'posture_state_hash computed over committed input fields BEFORE content_hash computation (ATF-INV-003). Pre-computation ordering enforced in pipeline.',
         'EU Art.9(7), NIST MEASURE 2.5, GCC Art.9, ISO Sec.8.5, UK AISI Sec.4'),
        ('UGI-005','Self-Modification Prohibition',
         'AI agent authority parameters MUST NOT be self-modifiable above defined thresholds. '
         'All modifications MUST be bounded and produce verifiable audit artifacts.',
         'Auto-Modification Guard (AMG, ADR-144): maximum 10% per event, 30% cumulative. AGVP watchdog for anticipatory veto of modification attempts.',
         'EU Art.14(4), NIST GOVERN 6.1, GCC Art.10, ISO Sec.6.1.2, UK AISI Sec.5'),
        ('UGI-006','Self-Contained Evidence Reconstruction',
         'The complete governance evidence chain MUST be reconstructable from the receipt artifacts '
         'alone, without access to any external system, service, or database.',
         'OEP package contains: DR -> TAR -> RCR -> GovernanceReceipt with embedded delegator public key (ADR-165). Full chain reconstructable from OEP alone.',
         'EU Art.18/72, NIST MAP 5.1, GCC Art.14, ISO Sec.9.3, UK AISI Sec.5'),
    ]:
        st.append(KeepTogether([
            Paragraph(f'<b>{ugi} -- {name}</b>', s['h3']),
            Paragraph(f'<b>Statement:</b> {statement}', s['body']),
            Paragraph(f'<b>ATF Mechanism:</b> {mech}', s['body']),
            Paragraph(f'<b>Framework Clauses:</b> <font color="#aaaaaa">{frameworks}</font>', s['body']),
            sp(4),
        ]))
    st.append(sp(4))

    st.append(Paragraph('5.4  Universal Invariant Receipt (UIR) Specification', s['h2']))
    st.append(cb(
"""  UIR (Universal Invariant Receipt) -- identifier: UIR-{16HEX}

  COMMITTED FIELDS:
    uir_id                   : "UIR-7F3A2B1C4D5E6F7A"
    assessed_protocol        : "ATF"  (or other governance protocol identifier)
    atf_spec_version         : "RFC-ATF-5_v1.0"
    agent_type_coverage      : ["LLM", "FINANCIAL", "MEDICAL", "ROBOTIC"]
    ugi_001_status           : "PASS"  | "PARTIAL" | "FAIL"
    ugi_001_evidence_ref     : "ATFDR-..." (binding to supporting ATF record)
    ugi_002_status           : "PASS"
    ugi_002_evidence_ref     : "OEP-..."
    ugi_003_status           : "PASS"
    ugi_003_evidence_ref     : "ATFTAR-..."
    ugi_004_status           : "PASS"
    ugi_004_evidence_ref     : "ATFDR-..." (posture_state_hash verification)
    ugi_005_status           : "PASS"
    ugi_005_evidence_ref     : "AMG-AUDIT-..."
    ugi_006_status           : "PASS"
    ugi_006_evidence_ref     : "OEP-..."
    overall_gugt_status      : "GUGT_COMPLIANT"  (all 6 PASS)
                             | "GUGT_PARTIAL"    (at least one PARTIAL, no FAIL)
                             | "GUGT_NON_COMPLIANT" (at least one FAIL)
    conformance_level        : "GUGT-L3+ATF"
    framework_coverage       : ["EU_AI_ACT_ART14", "NIST_GOVERN_1.1", ...]
    issued_at                : "2026-05-26T14:00:00.000000000+00:00"

  SEAL FIELDS:
    content_hash_uir         : SHA256(canonical JSON of committed fields)
    pqc_algorithm            : "ML-DSA-65"
    uir_seal                 : base64(ML-DSA-65.sign(content_hash_uir))""", s))
    st.append(sp(6))

    st.append(Paragraph('5.5  GUGT Conformance Levels', s['h2']))
    st.append(tbl(['Level','UGIs Required','Additional Requirements','Typical Deployer'],
        [['GUGT-L1 Basic','UGI-001 + UGI-002','Human authority anchor + offline evidence verification','Any system with identity chain and signed receipts'],
         ['GUGT-L2 Runtime','GUGT-L1 + UGI-003 + UGI-004','Execution-time boundary enforcement + pre-committed posture','Runtime-enforcement governance systems'],
         ['GUGT-L3 Full','GUGT-L2 + UGI-005 + UGI-006','Self-modification prohibition + self-contained evidence reconstruction','Full-stack governance systems (non-ATF)'],
         ['GUGT-L3+ATF','GUGT-L3 + full ATF stack','All 88 ATF invariants (RFC-ATF-1 through RFC-ATF-5); ATF-CGL-Compliant status','ATF-CGL-Compliant systems -- earned by construction']],
        s, cw=[3.0*cm,3.5*cm,5.5*cm,4.8*cm]))
    st.append(sp(6))
    st.append(Paragraph(
        'GUGT conformance levels are strictly hierarchical: GUGT-L3+ATF implies GUGT-L3, '
        'GUGT-L3 implies GUGT-L2, GUGT-L2 implies GUGT-L1. This monotonicity is enforced '
        'by GUGT-INV-006 and verified by Z3 proof target GUGT-UGI-MONOTONICITY.', s['body']))

    st.append(Paragraph('5.6  Cross-Jurisdiction Framework Mapping', s['h2']))
    st.append(tbl(['UGI','EU AI Act','NIST AI RMF','GCC/DIFC 2024','ISO/IEC 42001','UK AISI'],
        [['UGI-001','Art. 14, 17','GOVERN 1.1','Art. 8','Sec. 6.2','Sec. 3'],
         ['UGI-002','Art. 11, 12','MAP 5.2','Art. 12','Sec. 9.1','Sec. 4'],
         ['UGI-003','Art. 9','MANAGE 2.2','Art. 9','Sec. 8.4','Sec. 4'],
         ['UGI-004','Art. 9(7)','MEASURE 2.5','Art. 9','Sec. 8.5','Sec. 4'],
         ['UGI-005','Art. 14(4)','GOVERN 6.1','Art. 10','Sec. 6.1.2','Sec. 5'],
         ['UGI-006','Art. 18, 72','MAP 5.1','Art. 14','Sec. 9.3','Sec. 5']],
        s, cw=[2.0*cm,3.2*cm,3.2*cm,3.2*cm,3.2*cm,2.0*cm]))
    st.append(sp(6))

    st.append(Paragraph('5.7  GUGT Invariants: GUGT-INV-001-006', s['h2']))
    st.append(tbl(['Invariant','Statement','Enforcement'],
        [['GUGT-INV-001','UIR MUST assess all 6 UGIs; overall_gugt_status MUST reflect the minimum across all UGI statuses','UIR with fewer than 6 UGI assessments is structurally invalid and rejected'],
         ['GUGT-INV-002','Framework clause references in UIR.framework_coverage MUST be specific (FRAMEWORK_CLAUSE format, not generic framework name)','Generic references (e.g., "EU AI Act" without article) rejected as non-specific'],
         ['GUGT-INV-003','UIR MUST carry a valid ML-DSA-65 seal over content_hash_uir before persistence or distribution','Unsealed UIR rejected at DB insert level; cannot be distributed'],
         ['GUGT-INV-004','UIR MUST explicitly declare agent_type_coverage; claimed coverage MUST match declared types','Claim-coverage mismatch logged as GUGT_COVERAGE_MISMATCH and UIR invalidated'],
         ['GUGT-INV-005','GUGT_COMPLIANT status MUST NOT relax any prior ATF invariant; all 88 invariants remain in full force','Any UIR that attempts to waive an ATF invariant is rejected as GUGT_WAIVER_VIOLATION'],
         ['GUGT-INV-006','GUGT conformance levels are strictly hierarchical: GUGT-Lk implies GUGT-Lj for all j < k','Level claim failing monotonicity check rejected; Z3 proof target GUGT-UGI-MONOTONICITY']],
        s, cw=[3.0*cm,7.2*cm,6.6*cm]))
    st.append(sp(6))

    st.append(Paragraph('5.8  GUGT Database Schema', s['h2']))
    st.append(cb(
"""  -- Table: gugt_universal_invariant_receipts
  CREATE TABLE IF NOT EXISTS gugt_universal_invariant_receipts (
      id                    SERIAL PRIMARY KEY,
      uir_id                VARCHAR(50)  UNIQUE NOT NULL,
      assessed_protocol     VARCHAR(50)  NOT NULL DEFAULT 'ATF',
      atf_spec_version      VARCHAR(30),
      agent_type_coverage   JSONB        NOT NULL,
      ugi_001_status        VARCHAR(20)  NOT NULL CHECK (ugi_001_status IN ('PASS','PARTIAL','FAIL')),
      ugi_001_evidence_ref  VARCHAR(100),
      ugi_002_status        VARCHAR(20)  NOT NULL CHECK (ugi_002_status IN ('PASS','PARTIAL','FAIL')),
      ugi_002_evidence_ref  VARCHAR(100),
      ugi_003_status        VARCHAR(20)  NOT NULL CHECK (ugi_003_status IN ('PASS','PARTIAL','FAIL')),
      ugi_003_evidence_ref  VARCHAR(100),
      ugi_004_status        VARCHAR(20)  NOT NULL CHECK (ugi_004_status IN ('PASS','PARTIAL','FAIL')),
      ugi_004_evidence_ref  VARCHAR(100),
      ugi_005_status        VARCHAR(20)  NOT NULL CHECK (ugi_005_status IN ('PASS','PARTIAL','FAIL')),
      ugi_005_evidence_ref  VARCHAR(100),
      ugi_006_status        VARCHAR(20)  NOT NULL CHECK (ugi_006_status IN ('PASS','PARTIAL','FAIL')),
      ugi_006_evidence_ref  VARCHAR(100),
      overall_gugt_status   VARCHAR(30)  NOT NULL,
      conformance_level     VARCHAR(20)  NOT NULL,
      framework_coverage    JSONB        NOT NULL,
      content_hash_uir      VARCHAR(64)  NOT NULL,
      pqc_algorithm         VARCHAR(30)  DEFAULT 'ML-DSA-65',
      uir_seal              TEXT,
      issued_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW()
  );""", s))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 6 -- TGB
    # ==========================================================================
    st.append(Paragraph('6.  Temporal Governance Bridge (TGB)', s['h1'])); st.append(rule(s))
    st.append(Paragraph(
        'AI governance operates simultaneously at two radically different time scales: nanoseconds '
        '(runtime enforcement) and years (regulatory review, EU AI Act Art. 72 mandates 7-year '
        'retention for high-risk AI). No prior AI governance specification provides a formal bridge '
        'between these scales. The TGB provides this bridge through three record types: the Temporal '
        'Context Snapshot (TCS), the Regulatory Alignment Receipt (RAR), and the Temporal Migration '
        'Record (TMR).', s['body']))

    st.append(Paragraph('6.1  Two-Scale Architecture: Nanoseconds to Years', s['h2']))
    st.append(cb(
"""  TGB TWO-SCALE ARCHITECTURE:

  TIME AXIS:
  ----T=0ns-----------T=6mo-----------T=3yr-----------T=7yr-----------+
      |                |               |               |               |
  MICRO-SCALE         LIFECYCLE       LIFECYCLE       MACRO-SCALE     |
  [nanoseconds]       [months]        [years]         [7yr audit]     |
      |                |               |               |               |
  +---v---+         +--v---------+  +--v---------+  +--v-----------+  |
  |Primary|         |HOT -> WARM |  |WARM -> COLD|  | Regulatory   |  |
  |record |         |transition  |  |transition  |  | audit review |  |
  |issued |         |TMR-001     |  |TMR-002     |  | RAR produced |  |
  +---+---+         +------------+  +------------+  +------+-------+  |
      |                                                      |         |
      v (sync, T+100ns)                                      |         |
  +-------------------------------------------------------+  |         |
  | TCS embedded in primary record                        |  |         |
  |   eu_ai_act_version:   "EU_AI_ACT_2024_v1.0"         |<-+         |
  |   nist_ai_rmf_version: "NIST_AI_RMF_2023_v1.0"       |            |
  |   atf_spec_version:    "RFC-ATF-5_v1.0"              |            |
  |   nominal_threshold:   80.0                           |  RAR reads |
  |   halt_threshold:      20.0                           |  TCS as    |
  |   issued_at_ns:        1748268000123456789            |  source    |
  |   tcs_seal:            ML-DSA-65 [OK]                 |            |
  +-------------------------------------------------------+            |
                                                                        |
  KEY PROPERTIES:                                                       |
  - TCS never modified after issuance (TGB-INV-002)                     |
  - RAR projects context -- does NOT touch primary record               |
  - RAR computable offline from: record + TCS + signed rulebook         |
  - TMR issued at each lifecycle transition (HOT->WARM, WARM->COLD)     |""", s))
    st.append(sp(6))

    st.append(Paragraph('6.2  Temporal Context Snapshot (TCS) Specification', s['h2']))
    st.append(Paragraph(
        'The TCS is the core innovation of the TGB. It is the first record type in any published '
        'governance specification designed explicitly to capture the interpretive context at '
        'nanosecond precision at the moment of record issuance. Without the TCS, a receipt is '
        'a fact without context. With the TCS, the receipt is a self-interpreting artifact.', s['body']))
    st.append(cb(
"""  TCS (Temporal Context Snapshot) -- identifier: TCS-{16HEX}

  COMMITTED FIELDS:
    tcs_id                   : "TCS-9B3F2A1D4C5E7F8A"
    parent_record_id         : "ATFDR-..." (the record this TCS is embedded in)
    parent_record_type       : "DR" | "TAR" | "RCR" | "GovernanceReceipt" | ...
    issued_at_ns             : 1748268000123456789  (nanosecond UNIX timestamp)
    issued_at_iso            : "2026-05-26T14:00:00.123456789+00:00"

    regulatory_context:
      eu_ai_act_version      : "EU_AI_ACT_2024_v1.0"
      nist_ai_rmf_version    : "NIST_AI_RMF_2023_v1.0"
      gcc_difc_version       : "GCC_DIFC_AI_REG_2024_v1.0"
      iso_42001_version      : "ISO_42001_2023_v1.0"
      atf_spec_version       : "RFC-ATF-5_v1.0"
      active_adr_count       : 184

    threshold_context:
      nominal_threshold      : 80.0
      monitoring_lower       : 50.0
      warning_lower          : 30.0
      halt_threshold         : 20.0
      fragmentation_limit    : 0.90
      max_delegation_depth   : 5

    deployment_context:
      agent_type             : "LLM"
      domain                 : "FINANCE"
      jurisdiction           : "EU"

  SEAL FIELDS:
    tcs_hash                 : SHA256(canonical JSON of committed fields)
    pqc_algorithm            : "ML-DSA-65"
    tcs_seal                 : base64(ML-DSA-65.sign(tcs_hash))

  BINDING TO PARENT RECORD:
    tcs_hash is included in parent_record.posture_state_hash
    Any tampering with TCS is detectable from parent record content_hash""", s))
    st.append(sp(6))

    st.append(Paragraph('6.3  Regulatory Alignment Receipt (RAR) Specification', s['h2']))
    st.append(Paragraph(
        'The RAR is produced at review time (months or years after the original record issuance) '
        'to project a historical governance record to the current regulatory framework. The RAR '
        'is strictly non-destructive (TGB-INV-002): it does not modify the source record, the '
        'source TCS, or any other original artifact. It adds interpretive projection alongside '
        'them.', s['body']))
    st.append(cb(
"""  RAR (Regulatory Alignment Receipt) -- identifier: RAR-{16HEX}

  COMMITTED FIELDS:
    rar_id                   : "RAR-2C4E6A8B1D3F5A7C"
    source_record_id         : "ATFDR-..." (original record being projected)
    source_tcs_id            : "TCS-..." (TCS embedded at original issuance)
    original_record_hash     : SHA256(original record JSON at time of projection)
                               (tamper-evidence commitment to source state)
    source_rfv               : "EU_AI_ACT_2024_v1.0" (from TCS)
    target_rfv               : "EU_AI_ACT_2033_v3.0" (current framework at review)
    projection_timestamp     : "2033-07-14T09:30:00.000000000+00:00"
    rulebook_version         : "TGB-RAR-V1.0"
    rulebook_hash            : SHA256(projection_rulebook.json)

    field_projections:
      - field_name           : "counterfactual_outcome"
        source_value         : "NOMINAL"
        target_value         : "APPROVED_TIER_A"  (mapped per 2033 framework)
        projection_rule      : "EU_NOMINAL_TO_APPROVED_TIER_A_v1"
        projection_confidence: "HIGH"

    original_record_integrity: "VERIFIED" | "INVALIDATED" | "UNVERIFIABLE"
    invalidation_evidence_id : null | "EID-..." (if INVALIDATED)

  SEAL FIELDS:
    content_hash_rar         : SHA256(canonical JSON of committed fields)
    pqc_algorithm            : "ML-DSA-65"
    rar_seal                 : base64(ML-DSA-65.sign(content_hash_rar))""", s))
    st.append(sp(6))

    st.append(Paragraph('6.4  Temporal Migration Record (TMR) Specification', s['h2']))
    st.append(Paragraph(
        'A TMR is issued at each evidence lifecycle transition (HOT to WARM, WARM to COLD) as '
        'specified in RFC-ATF-3. The TMR captures the regulatory context at the transition moment, '
        'providing a timestamped provenance chain for the evidence lifecycle.', s['body']))
    st.append(cb(
"""  TMR (Temporal Migration Record) -- identifier: TMR-{16HEX}

  COMMITTED FIELDS:
    tmr_id                   : "TMR-8A3F2B1C4D5E6F7A"
    source_record_id         : "..." (record undergoing lifecycle transition)
    transition               : "HOT_TO_WARM" | "WARM_TO_COLD"
    transition_timestamp     : "2026-11-26T00:00:00.000000000+00:00"
    pre_transition_lifecycle : "HOT"
    post_transition_lifecycle: "WARM"
    regulatory_context_at_transition: { same structure as TCS.regulatory_context }
    threshold_context_at_transition:  { same structure as TCS.threshold_context }
    retention_policy_at_transition:   { policy_name, min_retention_years, jurisdiction }

  SEAL FIELDS:
    content_hash_tmr         : SHA256(canonical JSON of committed fields)
    pqc_algorithm            : "ML-DSA-65"
    tmr_seal                 : base64(ML-DSA-65.sign(content_hash_tmr))

  LIFECYCLE:
    HOT phase (0 to 6 months):  active, fully queryable, high-frequency access
    WARM phase (6mo to 3yr):    archival, query-accessible, TMR-001 at transition
    COLD phase (3yr to 7yr+):   long-term retention, retrieval on request, TMR-002 at transition
    At 7yr: EU AI Act Art.72 minimum retention satisfied (for high-risk AI)""", s))
    st.append(sp(6))

    st.append(Paragraph('6.5  TGB Projection Rulebook', s['h2']))
    st.append(Paragraph(
        'The TGB projection rulebook is a versioned, PQC-signed document that specifies mapping '
        'rules from source framework versions to target framework versions. The rulebook is published '
        'by OMNIX QUANTUM and is publicly verifiable. Any party can verify a RAR by obtaining the '
        'rulebook and applying the rules to the source TCS.', s['body']))
    st.append(tbl(['Rulebook Entry','Source RFV','Target RFV','Mapping Rule','Confidence'],
        [['EU_NOMINAL_TO_APPROVED_TIER_A','EU_AI_ACT_2024_v1.0','EU_AI_ACT_2027_v2.0','CES >= nominal_threshold_2024 -> APPROVED_TIER_A if threshold preserved','HIGH'],
         ['EU_HALT_TO_PROHIBITED','EU_AI_ACT_2024_v1.0','EU_AI_ACT_2027_v2.0','outcome == HALT -> SYSTEM_HALT (semantic preservation)','HIGH'],
         ['NIST_MANAGE22_TO_MANAGE23','NIST_AI_RMF_2023_v1.0','NIST_AI_RMF_2025_v2.0','MANAGE 2.2 provisions -> MANAGE 2.3 equivalent','MEDIUM'],
         ['THRESHOLD_DELTA_RISK','any','any','If target_threshold != source_threshold -> flag THRESHOLD_CONTEXT_CHANGE','N/A (flag only)']],
        s, cw=[4.0*cm,3.5*cm,3.5*cm,4.5*cm,1.3*cm]))
    st.append(sp(6))

    st.append(Paragraph('6.6  TGB Invariants: TGB-INV-001-005', s['h2']))
    st.append(tbl(['Invariant','Statement','Enforcement Mechanism'],
        [['TGB-INV-001','Every ATF record MUST carry a TCS when TGB_ENABLED=true; TCS MUST be issued and bound synchronously with the primary record','TCS construction synchronous with primary; failure flags TGB_INCOMPLETE on primary record and retries async'],
         ['TGB-INV-002','RAR MUST NOT modify any field of the source record, source TCS, or any TMR','original_record_hash in RAR provides tamper-evidence commitment; any modification to source detectable from RAR'],
         ['TGB-INV-003','Any party MUST be able to compute a RAR offline using only: source record, TCS, and TGB projection rulebook (PQC-verified)','Rulebook PQC-sealed and publishable; RAR computation requires no platform access or credentials'],
         ['TGB-INV-004','A framework revision MUST NOT silently invalidate any existing ATF record; any invalidity requires an explicit Evidential Invalidation Document (EID) persisted in RAR table','EID written to atf_regulatory_alignment_receipts with original_record_integrity = INVALIDATED'],
         ['TGB-INV-005','TMR MUST be issued at each lifecycle transition (HOT->WARM, WARM->COLD) for all records with retention_years >= 7; TMR MUST carry ML-DSA-65 seal','TMR issuance triggered automatically by lifecycle management module; unsigned TMR rejected at DB insert']],
        s, cw=[2.8*cm,6.8*cm,7.2*cm]))
    st.append(sp(6))

    st.append(Paragraph('6.7  TGB Database Schema', s['h2']))
    st.append(cb(
"""  -- Table: atf_temporal_context_snapshots  (append-only)
  CREATE TABLE IF NOT EXISTS atf_temporal_context_snapshots (
      id                    SERIAL PRIMARY KEY,
      tcs_id                VARCHAR(50)  UNIQUE NOT NULL,
      parent_record_id      VARCHAR(100) NOT NULL,
      parent_record_type    VARCHAR(30)  NOT NULL,
      issued_at_ns          BIGINT       NOT NULL,
      issued_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
      regulatory_context    JSONB        NOT NULL,
      threshold_context     JSONB        NOT NULL,
      deployment_context    JSONB,
      tcs_hash              VARCHAR(64)  NOT NULL,
      pqc_algorithm         VARCHAR(30)  DEFAULT 'ML-DSA-65',
      tcs_seal              TEXT
  );

  -- Table: atf_regulatory_alignment_receipts  (append-only)
  CREATE TABLE IF NOT EXISTS atf_regulatory_alignment_receipts (
      id                         SERIAL PRIMARY KEY,
      rar_id                     VARCHAR(50)  UNIQUE NOT NULL,
      source_record_id           VARCHAR(100) NOT NULL,
      source_tcs_id              VARCHAR(50)  NOT NULL,
      original_record_hash       VARCHAR(64)  NOT NULL,
      source_rfv                 VARCHAR(100) NOT NULL,
      target_rfv                 VARCHAR(100) NOT NULL,
      projection_timestamp       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
      rulebook_version           VARCHAR(30)  NOT NULL,
      rulebook_hash              VARCHAR(64),
      field_projections          JSONB,
      original_record_integrity  VARCHAR(20)  NOT NULL DEFAULT 'VERIFIED'
                                 CHECK (original_record_integrity IN ('VERIFIED','INVALIDATED','UNVERIFIABLE')),
      invalidation_evidence_id   VARCHAR(50),
      content_hash_rar           VARCHAR(64)  NOT NULL,
      pqc_algorithm              VARCHAR(30)  DEFAULT 'ML-DSA-65',
      rar_seal                   TEXT
  );

  -- Table: atf_temporal_migration_records
  CREATE TABLE IF NOT EXISTS atf_temporal_migration_records (
      id                              SERIAL PRIMARY KEY,
      tmr_id                          VARCHAR(50)  UNIQUE NOT NULL,
      source_record_id                VARCHAR(100) NOT NULL,
      transition                      VARCHAR(20)  NOT NULL
                                      CHECK (transition IN ('HOT_TO_WARM','WARM_TO_COLD')),
      transition_timestamp            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
      pre_transition_lifecycle        VARCHAR(10)  NOT NULL,
      post_transition_lifecycle       VARCHAR(10)  NOT NULL,
      regulatory_context_at_transition JSONB       NOT NULL,
      threshold_context_at_transition  JSONB,
      retention_policy_at_transition   JSONB,
      content_hash_tmr                VARCHAR(64)  NOT NULL,
      pqc_algorithm                   VARCHAR(30)  DEFAULT 'ML-DSA-65',
      tmr_seal                        TEXT
  );""", s))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 7 -- FORMAL VERIFICATION
    # ==========================================================================
    st.append(Paragraph('7.  Formal Verification (OMNIX-FVS-1.0 Extension)', s['h1'])); st.append(rule(s))
    st.append(Paragraph(
        'RFC-ATF-5 extends the OMNIX Formal Verification Suite (FVS-1.0) defined in RFC-ATF-4. '
        'RFC-ATF-5 maintains the dual methodology: Z3 SMT for arithmetic and structural invariants, '
        'TLA+ for state-machine safety and liveness. This is the only AI governance standard with '
        'machine-checkable formal proofs across both methodologies.', s['body']))

    st.append(Paragraph('7.1  Z3 SMT Proof Targets', s['h2']))
    st.append(tbl(['Target ID','Module','Property Proven','Z3 Result'],
        [['CGE-FRAGILITY-BOUND-LO','CGE','fragility_score >= 0.0 for all valid real inputs','UNSAT'],
         ['CGE-FRAGILITY-BOUND-HI','CGE','fragility_score <= 1.0 for all valid real inputs','UNSAT'],
         ['CGE-VV-BOUND','CGE','abs(VV.delta) <= CGE_MAX_VARIATION_PCT for all VV fields','UNSAT'],
         ['CGE-PRIMARY-ISOLATION','CGE','CGE computation cannot modify any committed field of primary record','UNSAT'],
         ['CGE-ROOT-HASH-INTEGRITY','CGE','cat_root_hash uniquely determined by sorted(cfr_content_hashes)','UNSAT'],
         ['GUGT-UGI-COMPLETENESS','GUGT','GUGT_COMPLIANT iff all 6 UGIs are PASS (no fewer, no more)','UNSAT'],
         ['GUGT-UGI-MONOTONICITY','GUGT','GUGT-Lk satisfaction logically implies GUGT-Lj for all j < k','UNSAT'],
         ['GUGT-WAIVER-PROHIBITION','GUGT','No UIR can satisfy GUGT invariants while waiving any ATF invariant','UNSAT'],
         ['TGB-NON-DESTRUCTION','TGB','RAR production cannot change original_record_hash or source TCS fields','UNSAT'],
         ['TGB-PROJECTION-MONOTONE','TGB','Framework revision cannot silently increase compliance level','UNSAT'],
         ['TGB-FRAGILITY-PRESERVATION','TGB','fragility_score value in CAT preserved unchanged by TCS/RAR operations','UNSAT'],
         ['ATF-INV-001-CGL-EXT','Inherited','MAR invariant preserved under all CGE/GUGT/TGB operations','UNSAT']],
        s, cw=[4.5*cm,2.0*cm,8.0*cm,1.8*cm]))
    st.append(sp(6))

    st.append(Paragraph('7.2  TLA+ Coverage', s['h2']))
    st.append(Paragraph(
        'The TLA+ specification for RFC-ATF-5 extends the prior ATF TLA+ model '
        '(ATF-TLA-SPEC.tla) with three new modules: CGE_MODULE.tla, GUGT_MODULE.tla, '
        'and TGB_MODULE.tla. Each module specifies state transitions, safety properties, '
        'and liveness conditions for the respective CGL component.', s['body']))
    st.append(tbl(['TLA+ Specification','Property Type','Coverage','Status'],
        [['CGE_MODULE.tla -- CGE_ISOLATION','Safety','Primary record state unchanged by CGE transitions','PASS'],
         ['CGE_MODULE.tla -- CAT_EVENTUALLY_PRODUCED','Liveness','CAT is eventually produced for every evaluation with CGE_ENABLED','PASS'],
         ['GUGT_MODULE.tla -- UIR_CONSISTENCY','Safety','UIR overall_status consistent with UGI status set at all states','PASS'],
         ['GUGT_MODULE.tla -- LEVEL_HIERARCHY','Safety','Conformance level hierarchy monotonicity preserved across all transitions','PASS'],
         ['TGB_MODULE.tla -- TCS_IMMUTABILITY','Safety','TCS fields cannot be modified after persist transition','PASS'],
         ['TGB_MODULE.tla -- RAR_NON_DESTRUCTION','Safety','Source record state unchanged by RAR production transition','PASS'],
         ['TGB_MODULE.tla -- TMR_AT_TRANSITION','Liveness','TMR is eventually produced at every lifecycle transition for retained records','PASS'],
         ['ATF_INTEGRATION.tla -- CGL_NON_BLOCKING','Safety','Primary record state ACTIVE regardless of CGL module failure states','PASS']],
        s, cw=[5.5*cm,2.5*cm,5.5*cm,1.8*cm]))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 8 -- INVARIANTS SUMMARY
    # ==========================================================================
    st.append(Paragraph('8.  Combined Invariant Summary -- 88 Total', s['h1'])); st.append(rule(s))
    st.append(Paragraph(
        'RFC-ATF-5 introduces 18 new invariants across three protocol families. Combined with '
        'the 70 invariants from RFC-ATF-1 through RFC-ATF-4, the complete ATF stack encompasses '
        '<b>88 formally specified invariants</b> across 17 protocol families.', s['body']))
    st.append(tbl(['Family','RFC','Count','Scope'],
        [['ATF-INV','RFC-ATF-1','6','Identity & Delegation -- MAR, Acyclicity, Chain Root, Immutability, Non-Future-Dating, Offline Verifiability'],
         ['RGC-INV','RFC-ATF-2','8','Runtime Continuity -- CES, AFG, HALT propagation, RC, RCR integrity'],
         ['GPIL-INV','RFC-ATF-3','3','Governance Policy Interoperability Layer'],
         ['ELR-INV','RFC-ATF-3','4','Evidence Lifecycle Record management'],
         ['EAP-INV','RFC-ATF-3','7','Evidence Archive Pipeline'],
         ['OEP-INV','RFC-ATF-3','6','OMNIX Evidence Package -- two-phase PQC seal, offline verification'],
         ['FEA-INV','RFC-ATF-3','5','Forensic Export Authorization -- caller-key controls'],
         ['FVP-INV','RFC-ATF-3','1','Forensic Verification Protocol'],
         ['GECR-INV','RFC-ATF-3','6','Governance Execution Context Record'],
         ['SGIP-INV','RFC-ATF-3','4','Semantic Governance Interoperability Protocol'],
         ['DSPP-INV','RFC-ATF-4','7','Dynamic Semantic Portability Protocol -- TSA, SDR, RSA'],
         ['AGV-INV','RFC-ATF-4','6','Anticipatory Governance Veto Protocol -- PVR'],
         ['SSD-INV','RFC-ATF-4','3','Structural Shift Detection -- CRSI'],
         ['FVS-INV','RFC-ATF-4','3','Formal Verification Suite extension'],
         ['CGE-INV','RFC-ATF-5','7','Counterfactual Governance Engine  [NEW]'],
         ['GUGT-INV','RFC-ATF-5','6','Grand Unified Governance Theory   [NEW]'],
         ['TGB-INV','RFC-ATF-5','5','Temporal Governance Bridge         [NEW]'],
         ['TOTAL','--','88','Complete ATF Protocol Stack, five RFCs, 17 families']],
        s, cw=[2.8*cm,2.2*cm,1.5*cm,10.3*cm]))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 9 -- COMPLIANCE DESIGNATION
    # ==========================================================================
    st.append(Paragraph('9.  ATF-CGL-Compliant Designation', s['h1'])); st.append(rule(s))
    st.append(cb(
"""  ATF COMPLIANCE HIERARCHY (five tiers, strictly hierarchical):

  +------------------------------------------------------------------+
  | * ATF-CGL-Compliant  (RFC-ATF-1+2+3+4+5)  88 invariants  HIGHEST|
  |   All five RFC layers operational; CGE + GUGT UIR + TGB required |
  +------------------------------------------------------------------+
        ^--- extends without replacing
  +------------------------------------------------------------------+
  |   ATF-PGL-Compliant  (RFC-ATF-1+2+3+4)    70 invariants         |
  |   AGVP + SSD + DSPP operational                                  |
  +------------------------------------------------------------------+
        ^--- extends without replacing
  +------------------------------------------------------------------+
  |   ATF-FEI-Compliant  (RFC-ATF-1+2+3)      40 invariants         |
  |   OEP + GPIL + Forensic verification operational                 |
  +------------------------------------------------------------------+
        ^--- extends without replacing
  +------------------------------------------------------------------+
  |   ATF-RGC-Compliant  (RFC-ATF-1+2)        14 invariants         |
  |   Runtime continuity + HALT propagation operational              |
  +------------------------------------------------------------------+
        ^--- extends without replacing
  +------------------------------------------------------------------+
  |   ATF-Compliant-L1/2/3 (RFC-ATF-1)         6 invariants         |
  |   Identity + Delegation + Trust Lattice operational              |
  +------------------------------------------------------------------+

  ATF-CGL-Compliant requirements (all five required simultaneously):
  (a) ATF-PGL-Compliant: all RFC-ATF-1/2/3/4 requirements satisfied
  (b) CGE operational: CGE_ENABLED=true, CGE_FORK_COUNT in [1,7],
      all CGE-INV-001-007 satisfied, CATs produced for all evaluations
  (c) GUGT UIR issued: at least one GUGT-L3+ATF UIR issued, PQC-sealed,
      and verified for the deployment
  (d) TGB operational: TGB_ENABLED=true, all records carry TCS,
      all TGB-INV-001-005 satisfied
  (e) CGL formal verification: FVS-1.0 extension runs all CGL Z3 proof
      targets returning UNSAT; TLA+ modules pass all safety/liveness checks""", s))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 10 -- IMPLEMENTATION REFERENCE
    # ==========================================================================
    st.append(Paragraph('10.  Implementation Reference', s['h1'])); st.append(rule(s))
    st.append(Paragraph('10.1  Reference Implementation Components', s['h2']))
    st.append(tbl(['Component','Role','Public Interface'],
        [['CGE Engine','CFR computation, VV generation, CAT assembly, fragility_score computation, CGE-INV enforcement','/api/atf/cge/evaluate -- /api/atf/cge/cat/{evaluation_id}'],
         ['GUGT Assessor','UGI-001-006 evaluation, UIR issuance, conformance level assignment, GUGT-INV enforcement','/api/atf/gugt/assess -- /api/atf/gugt/uir/{deployment_id}'],
         ['TGB Manager','TCS embedding, RAR production, TMR at lifecycle transitions, rulebook management','/api/atf/tgb/tcs/{record_id} -- /api/atf/tgb/rar'],
         ['CGE Verifier','Offline CAT verification: root hash, CFR signatures, VV determinism, fragility_score','python omnix_atf_verify.py --cat cat.json'],
         ['GUGT Verifier','Offline UIR verification: UGI status set, ML-DSA-65 seal, conformance level','python omnix_atf_verify.py --uir uir.json'],
         ['TGB Projector','Offline RAR computation: TCS + rulebook + source record -> RAR projection','python omnix_tgb_project.py --tcs tcs.json --record record.json --rulebook rulebook.json'],
         ['FVS Runner','Z3 + TLA+ proof execution: all CGL proof targets, result reporting','python omnix_fvs_run.py --suite cgl -- outputs: UNSAT for all Z3, PASS for all TLA+'],
         ['CGL DB Manager','6 new table creation, append-only enforcement triggers, FK integrity','Auto-created on first request via CREATE TABLE IF NOT EXISTS']],
        s, cw=[3.5*cm,7.2*cm,6.1*cm]))
    st.append(sp(6))

    st.append(Paragraph('10.2  API Endpoints', s['h2']))
    st.append(tbl(['Endpoint','Method','Description','Auth'],
        [['/api/atf/cge/evaluate','POST','Trigger CGE evaluation for a primary receipt; returns cat_id','B2B API key'],
         ['/api/atf/cge/cat/{evaluation_id}','GET','Retrieve CAT and all CFRs for an evaluation','B2B API key'],
         ['/api/atf/cge/verify','POST','Online CAT verification (offline CLI also available)','B2B API key'],
         ['/api/atf/gugt/assess','POST','Run GUGT assessment for a deployment; returns uir_id','Admin'],
         ['/api/atf/gugt/uir/{deployment_id}','GET','Retrieve most recent UIR for a deployment','B2B API key'],
         ['/api/atf/tgb/tcs/{record_id}','GET','Retrieve TCS for a specific ATF record','B2B API key'],
         ['/api/atf/tgb/rar','POST','Request RAR production for a historical record','Admin'],
         ['/api/atf/tgb/project','POST','Offline-compatible RAR projection request','Admin']],
        s, cw=[5.0*cm,2.0*cm,7.2*cm,2.6*cm]))
    st.append(sp(6))

    st.append(Paragraph('10.3  Configuration Parameters', s['h2']))
    st.append(tbl(['Parameter','Default','Range','Description'],
        [['CGE_ENABLED','false','true/false','Enable CGE counterfactual computation'],
         ['CGE_FORK_COUNT','3','1-7','Number of CFRs to compute per evaluation'],
         ['CGE_MAX_VARIATION_PCT','0.40','0.05-0.40','Maximum absolute VV field delta allowed'],
         ['CGE_ASYNC_TIMEOUT_S','30','5-300','Timeout for async CGE computation'],
         ['TGB_ENABLED','false','true/false','Enable TCS embedding and TGB operations'],
         ['TGB_SYNC_TCS','true','true/false','Embed TCS synchronously (false = async, less safe)'],
         ['TGB_RETENTION_YEARS','7','1-50','Default evidence retention period for TMR triggers'],
         ['TGB_RULEBOOK_URL','(internal)','URL','URL of signed TGB projection rulebook'],
         ['GUGT_AUTO_ASSESS','false','true/false','Auto-run GUGT assessment on deployment startup'],
         ['GUGT_CONFORMANCE_TARGET','GUGT-L3+ATF','L1/L2/L3/L3+ATF','Minimum conformance level for deployment health check']],
        s, cw=[4.5*cm,2.5*cm,2.5*cm,7.3*cm]))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 11 -- SECURITY
    # ==========================================================================
    st.append(Paragraph('11.  Security Considerations', s['h1'])); st.append(rule(s))
    st.append(tbl(['Threat','Attack Vector','CGL Mitigation','Residual Risk'],
        [['CGE Primary Manipulation (CGL-T-001)','Attacker attempts to modify primary record outcome via CGE computation path','CGE-INV-002: CGE is strictly read-only post-primary-commit; Z3 proof CGE-PRIMARY-ISOLATION','NONE -- structural guarantee'],
         ['CFR Fabrication (CGL-T-002)','Attacker injects fabricated CFRs to distort fragility_score or decision space','CGE-INV-003: all CFRs require valid ML-DSA-65 signature; CGE-INV-007: VV determinism verifiable offline','LOW -- requires key compromise'],
         ['CAT Root Hash Collision (CGL-T-003)','Attacker replaces CFRs after CAT issued, with colliding root hash','SHA-256 preimage resistance; cat_root_hash binding via cat_seal ML-DSA-65','NEGLIGIBLE -- SHA-256 + PQC'],
         ['UIR Level Inflation (CGL-T-004)','Attacker claims GUGT-L3+ATF without meeting all requirements','GUGT-INV-006: level monotonicity enforced; Z3 proof GUGT-UGI-MONOTONICITY','LOW -- requires UIR key compromise'],
         ['TCS Retroactive Modification (CGL-T-005)','Attacker modifies TCS to change historical context','TGB-INV-002: tcs_hash bound in parent record posture_state_hash; Z3 proof TGB-NON-DESTRUCTION','NONE -- tamper-evident from primary'],
         ['Temporal Downgrade (CGL-T-006)','Attacker provides outdated rulebook to produce favorable RAR projection','TGB-INV-003: rulebook PQC-sealed and versioned; rulebook_hash in RAR','LOW -- requires rulebook key compromise'],
         ['Silent Framework Invalidation (CGL-T-007)','Framework revision used to claim prior records non-compliant without notice','TGB-INV-004: EID required for any invalidity; silent invalidity rejected','NONE -- explicit EID required'],
         ['UGI Waiver Attack (CGL-T-008)','UIR claims to waive an ATF invariant via GUGT assessment override','GUGT-INV-005: waiver of any ATF invariant causes UIR rejection; Z3 proof GUGT-WAIVER-PROHIBITION','NONE -- structural guarantee']],
        s, cw=[3.5*cm,4.0*cm,4.5*cm,4.8*cm]))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 12 -- NOVEL CONTRIBUTIONS
    # ==========================================================================
    st.append(Paragraph('12.  Novel Contributions', s['h1'])); st.append(rule(s))
    for i, (title, detail) in enumerate([
        ('Counterfactual Attestation Token (CAT) with PQC Seal',
         'First governance artifact that cryptographically seals the decision space (not just the selected path) '
         'using post-quantum signatures. Existing counterfactual analysis tools (IBM OpenScale, Microsoft '
         'Responsible AI Toolbox) produce reports, not tamper-evident artifacts. The CAT is independently '
         'verifiable offline by any party holding only the receipt artifacts and the public key.'),
        ('fragility_score -- First Governance Decision Robustness Metric',
         'The fragility_score quantifies governance decision robustness as a continuous metric in [0.0, 1.0], '
         'formally defined as divergence_count / cfr_count. No published AI governance specification '
         'defines a quantitative robustness metric for governance decisions. The fragility_score is '
         'PQC-sealed within the CAT and independently reproducible from the CFR set.'),
        ('Universal Governance Invariants (UGI-001-006)',
         'First formally derived minimal set of universal governance requirements obtained by exhaustive '
         'clause-level intersection of five major regulatory frameworks simultaneously. Prior frameworks '
         '(EU AI Act guidance, NIST AI RMF profiles) are jurisdiction-specific. No published specification '
         'derives a minimal universal set via formal intersection methodology.'),
        ('Universal Invariant Receipt (UIR) -- Cross-Framework PQC Certificate',
         'First PQC-signed artifact that certifies compliance with five regulatory frameworks and six agent '
         'types simultaneously in a single verifiable record. Existing compliance certification systems '
         'are framework-specific and platform-dependent. The UIR is offline-verifiable and architecture-agnostic.'),
        ('Temporal Context Snapshot (TCS) -- Nanosecond-Precision Regulatory Context Capture',
         'First record type designed to capture the complete regulatory and threshold context at nanosecond '
         'precision at the moment of record creation. Prior governance specifications embed timestamps but '
         'not the interpretive framework under which the timestamp was produced. Without TCS, a historical '
         'receipt is a fact without context. With TCS, it is a self-interpreting artifact.'),
        ('Regulatory Alignment Receipt (RAR) -- Non-Destructive Temporal Projection',
         'First mechanism for projecting historical governance records to current regulatory frameworks '
         'without modifying the original evidence. The non-destruction invariant (TGB-INV-002) is '
         'formally proved via Z3 (TGB-NON-DESTRUCTION). No prior AI governance specification provides '
         'a non-destructive, offline-computable, PQC-signed temporal projection mechanism.'),
        ('ATF-CGL-Compliant -- Five-Tier Formally Verified Compliance Hierarchy',
         'First five-tier AI governance compliance designation backed by 88 formally specified invariants '
         'across 17 protocol families, dual formal verification (Z3 + TLA+), and post-quantum cryptography. '
         'No published AI governance standard defines a multi-tier compliance hierarchy with machine-checkable '
         'invariants across identity, runtime, evidence, proactive, and cognitive governance dimensions.'),
    ], start=1):
        st.append(KeepTogether([
            Paragraph(f'{i}.  {title}', s['h3']),
            Paragraph(detail, s['body']),
            sp(4),
        ]))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 13 -- PRIOR ART
    # ==========================================================================
    st.append(Paragraph('13.  Distinction from Prior Art', s['h1'])); st.append(rule(s))
    st.append(tbl(['Feature','RFC-ATF-5 (CGL)','VeriSigil VGS','IBM OpenScale','MS Azure RAI','NIST AI RMF'],
        [['Decision space evidence (PQC-sealed)','[OK] CAT -- offline-verifiable CFRs','[NO]','[NO]','[NO]','[NO]'],
         ['fragility_score metric','[OK] Defined, Z3-proved in [0,1]','[NO]','[NO]','[NO]','[NO]'],
         ['Universal governance invariants','[OK] UGI-001-006 by intersection','[NO]','[NO]','[NO]','Partial (single-framework)'],
         ['PQC-signed universal cert (UIR)','[OK] ML-DSA-65','[NO]','[NO]','[NO]','[NO]'],
         ['Multi-jurisdiction UIR','[OK] EU+US+GCC+ISO+UK','Partial (EU only)','[NO]','Partial','[NO]'],
         ['TCS at record issuance','[OK] Nanosecond precision','[NO]','[NO]','[NO]','[NO]'],
         ['Non-destructive RAR','[OK] TGB-INV-002 (Z3-proved)','[NO]','[NO]','[NO]','[NO]'],
         ['7-year retention support (TMR)','[OK] HOT/WARM/COLD + PQC','[NO]','[NO]','[NO]','[NO]'],
         ['Dual Z3 + TLA+ formal proofs','[OK] 12 Z3 targets + 8 TLA+','[OK] Z3 only','[NO]','[NO]','[NO]'],
         ['Offline full-chain verification','[OK] CLI -- no platform','[NO]','[NO]','[NO]','[NO]'],
         ['Post-quantum cryptography','[OK] ML-DSA-65 FIPS 204','[NO]','[NO]','[NO]','[NO]']],
        s, cw=[4.8*cm,3.8*cm,2.5*cm,2.5*cm,2.5*cm,2.3*cm]))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 14 -- REGULATORY ALIGNMENT
    # ==========================================================================
    st.append(Paragraph('14.  Regulatory Alignment', s['h1'])); st.append(rule(s))
    st.append(tbl(['Framework / Article','CGE Contribution','GUGT Contribution','TGB Contribution'],
        [['EU AI Act Art. 9 -- Risk Management','"Alternatives considered" documentation: CAT satisfies with PQC-signed artifacts, not narrative','"Risk management system" completeness: GUGT-L3+ATF certifies Art.9 complete by construction','Art.9(7) assessment integrity: TCS captures assessment context at issuance'],
         ['EU AI Act Art. 11-12 -- Technical Doc','CFR set provides full decision space documentation for technical file','UIR provides single artifact covering Art.11 requirements across systems','TCS provides issuance-time context for technical documentation accuracy'],
         ['EU AI Act Art. 72 -- Record Keeping','CAT provides decision space records for 7-year retention','UIR provides single compliance artifact for multi-year retention','TMR at lifecycle transitions + RAR at review time: 7-year bridge'],
         ['NIST AI RMF MAP 1.6 -- Impact Analysis','Alternative scenario documentation via CFR set','MAP 5.1/5.2 complete coverage: UIR certifies by construction','MAP 5.2 lifecycle documentation: TMR at each stage'],
         ['GCC/DIFC Art. 8-14 -- AI Governance','Arts. 8-14 "alternatives assessment": CAT covers','Complete UIR coverage of all GCC/DIFC requirements','Art.12/14 audit trail across framework revisions via RAR'],
         ['ISO/IEC 42001 Sec.6-9 -- AI MS','Sec.6.1.2 risk treatment alternatives: CFRs','Sec.6.1.2/8.4/8.5/9.3 complete: UIR certifies full coverage','Sec.9.1/9.3 management review with historical context via TCS'],
         ['SOC 2 Type II CC7.2 -- Monitoring','Decision space documentation for change monitoring','Evidence trail satisfying monitoring control requirements','Change documentation at each lifecycle transition via TMR'],
         ['UK AISI -- Evaluation Framework','Sec.3-5 "alternative outcomes considered" requirement','All AISI evaluation criteria satisfied: GUGT-L3+ATF includes UK AISI','Evaluation evidence preserved across temporal transitions']],
        s, cw=[4.2*cm,4.2*cm,4.0*cm,4.4*cm]))
    st.append(PageBreak())

    # ==========================================================================
    # SECTION 15 -- LIMITATIONS
    # ==========================================================================
    st.append(Paragraph('15.  Known Limitations and Open Questions', s['h1'])); st.append(rule(s))
    st.append(tbl(['Limitation','Mitigation','ADR Reference','Status'],
        [['CGE computation latency for M=7 forks on complex governance pipelines','CGE async by design; timeout configurable via CGE_ASYNC_TIMEOUT_S; partial CAT accepted (CGE-INV-001)','ADR-178','MANAGED'],
         ['Rulebook coverage gaps: not all source/target RFV pairs may have projection rules','Rulebook versioned and extensible; gap flagged as UNVERIFIABLE in RAR.original_record_integrity','ADR-180','OPEN'],
         ['TCS synchronous embedding adds ~100ns to record creation latency','Non-blocking failure mode (TGB_INCOMPLETE flag + async retry); TGB_SYNC_TCS=false for latency-critical deployments','ADR-180','MANAGED'],
         ['UIR is per-deployment, not per-record; deployment configuration changes may require UIR refresh','GUGT_AUTO_ASSESS=true triggers re-assessment on configuration change; prior UIRs are historical artifacts','ADR-179','MANAGED'],
         ['VV space exploration is parametric, not exhaustive; true decision space may be larger','fragility_score communicates this limitation explicitly; CGE_FORK_COUNT up to 7 for higher coverage','ADR-178','BY DESIGN'],
         ['RAR projection requires trusted rulebook; rulebook unavailability blocks offline RAR','Rulebook PQC-sealed and publishable independently; local cache recommended for offline environments','ADR-180','OPEN'],
         ['Multi-instance deployments require shared TCS signing key or key synchronization','Covered by existing OMNIX signing key management; no CGL-specific issue','ADR-178/179/180','INHERITED']],
        s, cw=[4.8*cm,5.5*cm,2.5*cm,2.0*cm]))
    st.append(PageBreak())

    # ==========================================================================
    # REFERENCES
    # ==========================================================================
    st.append(Paragraph('16.  References', s['h1'])); st.append(rule(s))
    for cite, text in [
        ('[RFC-ATF-1]','Nunes, H., "RFC-ATF-1: Agent Trust Fabric Delegation Protocol", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20155016. Figshare: 10.6084/m9.figshare.32308077'),
        ('[RFC-ATF-2]','Nunes, H., "RFC-ATF-2: Agent Trust Fabric -- Runtime Governance Continuity", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20241344. Figshare: 10.6084/m9.figshare.32308095'),
        ('[RFC-ATF-3]','Nunes, H., "RFC-ATF-3: Agent Trust Fabric -- Governance Policy Interoperability, Evidence Lifecycle, and Forensic Verification Protocol", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20247342. Figshare: 10.6084/m9.figshare.32308119'),
        ('[RFC-ATF-4]','Nunes, H., "RFC-ATF-4: Agent Trust Fabric -- Proactive Governance Layer", OMNIX QUANTUM Open Standard, May 2026. DOI: 10.5281/zenodo.20368895. Figshare: 10.6084/m9.figshare.32394192'),
        ('[FIPS204]','National Institute of Standards and Technology, "Module-Lattice-Based Digital Signature Standard (ML-DSA)", FIPS 204, August 2024. https://doi.org/10.6028/NIST.FIPS.204'),
        ('[Z3]','de Moura, L. and Bjorner, N., "Z3: An Efficient SMT Solver", TACAS 2008, LNCS 4963, pp. 337-340. 2008.'),
        ('[TLA+]','Lamport, L., "Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers", Addison-Wesley, 2002.'),
        ('[EU-AI-ACT]','European Parliament and Council, "Regulation (EU) 2024/1689 on Artificial Intelligence (EU AI Act)", Official Journal of the European Union, July 2024.'),
        ('[NIST-AI-RMF]','National Institute of Standards and Technology, "Artificial Intelligence Risk Management Framework", NIST AI 100-1, January 2023.'),
        ('[GCC-DIFC]','Dubai International Financial Centre, "DIFC Artificial Intelligence Regulation 2024", DIFC Law No. 2 of 2024, 2024.'),
        ('[ISO-42001]','International Organization for Standardization, "Artificial Intelligence -- Management System", ISO/IEC 42001:2023, 2023.'),
        ('[UK-AISI]','UK AI Safety Institute, "Evaluation Framework for Advanced AI Systems", Section 3-5, 2024.'),
        ('[ADR-178]','Nunes, H., "ADR-178: Counterfactual Governance Engine (CGE)", OMNIX QUANTUM Architecture Decision Record, May 2026.'),
        ('[ADR-179]','Nunes, H., "ADR-179: Grand Unified Governance Theory (GUGT)", OMNIX QUANTUM Architecture Decision Record, May 2026.'),
        ('[ADR-180]','Nunes, H., "ADR-180: Temporal Governance Bridge (TGB)", OMNIX QUANTUM Architecture Decision Record, May 2026.'),
        ('[RFC7519]','Jones, M., Bradley, J., and Sakimura, N., "JSON Web Token (JWT)", IETF RFC 7519, May 2015.'),
        ('[W3CVC]','W3C, "Verifiable Credentials Data Model 2.0", W3C Recommendation, May 2024.'),
        ('[CRYSTALS]','Ducas, L., et al., "CRYSTALS-Dilithium: A Lattice-Based Digital Signature Scheme", IACR TCHES 2018(1), 2018.'),
    ]:
        st.append(Paragraph(f'<b><font color="#8b8bf0">{cite}</font></b>  {text}', s['ref'])); st.append(sp(2))
    st.append(PageBreak())

    # ==========================================================================
    # APPENDIX A -- WIRE FORMATS
    # ==========================================================================
    st.append(Paragraph('Appendix A -- CGL Wire Formats (JSON Schemas)', s['h1'])); st.append(rule(s))
    st.append(Paragraph('A.1  CFR Wire Format', s['h2']))
    st.append(cb(
"""  {
    "$schema": "https://omnixquantum.net/schemas/atf/cgl/cfr-v1.0.json",
    "cfr_id":                   "CFR-[16 uppercase hex]",
    "cat_id":                   "CAT-[16 uppercase hex]",
    "primary_receipt_id":       "[parent record ID]",
    "evaluation_id":            "CGE-EVAL-[16 uppercase hex]",
    "variation_vector":         { "[field_name]": [numeric_delta], ... },
    "counterfactual_ces_score": [0.0 - 100.0],
    "counterfactual_outcome":   "NOMINAL|MONITORING|WARNING|HALT",
    "diverges_from_primary":    true | false,
    "cfr_status":               "ACCEPTED|REJECTED",
    "rejection_reason":         null | "CGE_VV_BOUND_VIOLATION",
    "vv_seed":                  "[64-char hex SHA256(eval_id || receipt_id)]",
    "posture_state_hash_cf":    "[64-char hex SHA256 of committed fields]",
    "content_hash_cf":          "[64-char hex SHA256 of all fields excl. sig]",
    "pqc_algorithm":            "ML-DSA-65",
    "pqc_signature":            "[base64 ML-DSA-65 signature over content_hash_cf]",
    "issued_at":                "[ISO8601 with nanoseconds and timezone]"
  }""", s))
    st.append(sp(6))
    st.append(Paragraph('A.2  CAT Wire Format', s['h2']))
    st.append(cb(
"""  {
    "$schema": "https://omnixquantum.net/schemas/atf/cgl/cat-v1.0.json",
    "cat_id":                   "CAT-[16 uppercase hex]",
    "primary_receipt_id":       "[parent record ID]",
    "evaluation_id":            "CGE-EVAL-[16 uppercase hex]",
    "cfr_ids":                  ["CFR-...", "CFR-...", ...],
    "cfr_count":                [integer 1-7],
    "divergence_count":         [integer 0 - cfr_count],
    "cat_root_hash":            "[sha256(sorted_cfr_hashes_joined_by_pipe)]",
    "fragility_score":          [decimal 0.0000 - 1.0000],
    "cge_fork_count_config":    [integer 1-7],
    "content_hash_cat":         "[64-char hex SHA256 of all fields excl. seal]",
    "pqc_algorithm":            "ML-DSA-65",
    "cat_seal":                 "[base64 ML-DSA-65 signature over content_hash_cat]",
    "issued_at":                "[ISO8601 with nanoseconds and timezone]"
  }""", s))
    st.append(sp(6))
    st.append(Paragraph('A.3  UIR Wire Format', s['h2']))
    st.append(cb(
"""  {
    "$schema": "https://omnixquantum.net/schemas/atf/cgl/uir-v1.0.json",
    "uir_id":                   "UIR-[16 uppercase hex]",
    "assessed_protocol":        "ATF",
    "atf_spec_version":         "RFC-ATF-5_v1.0",
    "agent_type_coverage":      ["LLM", "FINANCIAL", "MEDICAL", "ROBOTIC", ...],
    "ugi_001_status":           "PASS|PARTIAL|FAIL",
    "ugi_001_evidence_ref":     "[ATF record ID used as evidence]",
    "ugi_002_status":           "PASS|PARTIAL|FAIL",
    "ugi_002_evidence_ref":     "[ATF record ID]",
    "ugi_003_status":           "PASS|PARTIAL|FAIL",
    "ugi_003_evidence_ref":     "[ATF record ID]",
    "ugi_004_status":           "PASS|PARTIAL|FAIL",
    "ugi_004_evidence_ref":     "[ATF record ID]",
    "ugi_005_status":           "PASS|PARTIAL|FAIL",
    "ugi_005_evidence_ref":     "[ATF record ID]",
    "ugi_006_status":           "PASS|PARTIAL|FAIL",
    "ugi_006_evidence_ref":     "[ATF record ID]",
    "overall_gugt_status":      "GUGT_COMPLIANT|GUGT_PARTIAL|GUGT_NON_COMPLIANT",
    "conformance_level":        "GUGT-L1|GUGT-L2|GUGT-L3|GUGT-L3+ATF",
    "framework_coverage":       ["EU_AI_ACT_ART14", "NIST_GOVERN_1.1", ...],
    "content_hash_uir":         "[64-char hex SHA256 of all fields excl. seal]",
    "pqc_algorithm":            "ML-DSA-65",
    "uir_seal":                 "[base64 ML-DSA-65 signature over content_hash_uir]",
    "issued_at":                "[ISO8601 with nanoseconds and timezone]"
  }""", s))
    st.append(sp(6))
    st.append(Paragraph('A.4  TCS Wire Format', s['h2']))
    st.append(cb(
"""  {
    "$schema": "https://omnixquantum.net/schemas/atf/cgl/tcs-v1.0.json",
    "tcs_id":                   "TCS-[16 uppercase hex]",
    "parent_record_id":         "[ATF record ID this TCS is embedded in]",
    "parent_record_type":       "DR|TAR|RCR|GovernanceReceipt|...",
    "issued_at_ns":             [integer UNIX nanoseconds],
    "issued_at":                "[ISO8601 with nanoseconds and timezone]",
    "regulatory_context": {
      "eu_ai_act_version":      "[string]",
      "nist_ai_rmf_version":    "[string]",
      "gcc_difc_version":       "[string]",
      "iso_42001_version":      "[string]",
      "atf_spec_version":       "[string]",
      "active_adr_count":       [integer]
    },
    "threshold_context": {
      "nominal_threshold":      [decimal],
      "monitoring_lower":       [decimal],
      "warning_lower":          [decimal],
      "halt_threshold":         [decimal],
      "fragmentation_limit":    [decimal],
      "max_delegation_depth":   [integer]
    },
    "tcs_hash":                 "[SHA256 of committed fields]",
    "pqc_algorithm":            "ML-DSA-65",
    "tcs_seal":                 "[base64 ML-DSA-65 signature over tcs_hash]"
  }""", s))
    st.append(PageBreak())

    # ==========================================================================
    # APPENDIX B -- FRAMEWORK MAPPING
    # ==========================================================================
    st.append(Paragraph('Appendix B -- GUGT Framework Clause Mapping', s['h1'])); st.append(rule(s))
    st.append(Paragraph(
        'The following table provides the complete clause-level mapping used to derive UGI-001-006 '
        'from the five regulatory frameworks. Each cell identifies the specific clause(s) that '
        'require the corresponding universal property.', s['body']))
    st.append(tbl(['Universal Property','EU AI Act 2024','NIST AI RMF 1.0','GCC/DIFC 2024','ISO/IEC 42001:2023','UK AISI Eval Fwk'],
        [['Human authority anchor to identified principal','Art.14(4): human oversight; Art.17: governance system with identified persons','GOVERN 1.1: roles, responsibilities, and authorities defined','Art.8: human oversight requirements','Sec.6.2: objectives and planning; Sec.8.1: operational planning','Sec.3: responsible parties and accountability'],
         ['Offline-verifiable decision evidence','Art.11-12: technical documentation and record-keeping accessible to authorities','MAP 5.2: AI system testing and evaluation documentation','Art.12: documentation and audit trails available to authorities','Sec.9.1: monitoring, measurement, analysis -- evidence requirements','Sec.4: evidence standards for evaluation'],
         ['Execution-time boundary enforcement','Art.9: risk management system -- controls at point of operation','MANAGE 2.2: mechanisms for AI response to undesirable behavior','Art.9: operational controls at deployment','Sec.8.4: operational planning and control','Sec.4: runtime enforcement requirements'],
         ['Pre-committed posture assessment','Art.9(7): risk management documentation before operation','MEASURE 2.5: AI system performance evaluation before deployment','Art.9: pre-deployment assessment requirements','Sec.8.5: objectives implementation -- pre-committed documentation','Sec.4: assessment methodology requirements'],
         ['Self-modification prohibition','Art.14(4): human oversight maintains ability to override','GOVERN 6.1: policies regarding AI modification','Art.10: control of AI system modifications','Sec.6.1.2: risk assessment for AI modifications','Sec.5: control requirements for AI behavior modification'],
         ['Self-contained evidence reconstruction','Art.18: post-market monitoring -- complete evidence without platform','MAP 5.1: AI system impact assessment documentation','Art.14: complete documentation available for audit','Sec.9.3: management review with complete evidence','Sec.5: evidence sufficiency for independent review']],
        s, cw=[3.8*cm,3.0*cm,3.0*cm,2.5*cm,2.8*cm,3.2*cm]))
    st.append(PageBreak())

    # ==========================================================================
    # APPENDIX C -- COMPLIANCE CHECKLIST
    # ==========================================================================
    st.append(Paragraph('Appendix C -- ATF-CGL-Compliant Checklist', s['h1'])); st.append(rule(s))
    st.append(Paragraph(
        'The following checklist provides the complete set of requirements for achieving '
        'ATF-CGL-Compliant designation. All items are required.', s['body']))
    for section, items in [
        ('C.1  Prior RFC Compliance (ATF-PGL-Compliant required)', [
            'ATF-Compliant-L3: AIR, DR, TAR, Trust Lattice operational; ATF-INV-001-006 all satisfied',
            'ATF-RGC-Compliant: RCR, CES, AFG, RC operational; RGC-INV-001-008 all satisfied',
            'ATF-FEI-Compliant: OEP, GPIL, ELC, FVP operational; all L3 invariants satisfied',
            'ATF-PGL-Compliant: AGVP, SSD, DSPP operational; all L4 invariants satisfied',
        ]),
        ('C.2  CGE Requirements', [
            'CGE_ENABLED=true in production configuration',
            'CGE_FORK_COUNT in [1, 7]; CGE_MAX_VARIATION_PCT <= 0.40',
            'CGE-INV-001: CAT produced for every evaluation; CGE_INCOMPLETE flag operational',
            'CGE-INV-002: Primary record isolation verified; CGE reads primary post-commit only',
            'CGE-INV-003: All CFRs carry valid ML-DSA-65 signature; unsigned CFRs rejected',
            'CGE-INV-004: cat_root_hash computation correct; fragility_score in [0.0, 1.0]',
            'CGE-INV-005: VV bound enforcement operational; violations logged',
            'CGE-INV-006: DB triggers enforce append-only on counterfactual tables',
            'CGE-INV-007: Offline verification procedure documented and tested',
            'Z3 proof targets CGE-FRAGILITY-BOUND-LO/HI, CGE-VV-BOUND, CGE-PRIMARY-ISOLATION: UNSAT',
        ]),
        ('C.3  GUGT Requirements', [
            'GUGT assessment conducted for deployment; UIR issued with GUGT-L3+ATF status',
            'UIR covers all 6 UGIs; overall_gugt_status = GUGT_COMPLIANT',
            'UIR carries valid ML-DSA-65 seal; GUGT-INV-003 satisfied',
            'agent_type_coverage explicitly declared; GUGT-INV-004 satisfied',
            'framework_coverage uses specific clause references (FRAMEWORK_CLAUSE format)',
            'GUGT-INV-005: no ATF invariant waived; Z3 proof GUGT-WAIVER-PROHIBITION: UNSAT',
            'GUGT-INV-006: conformance level hierarchy monotonic; Z3 proof GUGT-UGI-MONOTONICITY: UNSAT',
        ]),
        ('C.4  TGB Requirements', [
            'TGB_ENABLED=true in production configuration',
            'TGB-INV-001: TCS embedded in every ATF record; TGB_INCOMPLETE flag operational',
            'TCS carries valid ML-DSA-65 seal; tcs_hash bound in parent record posture_state_hash',
            'TGB-INV-002: RAR production does not modify source record; Z3 proof TGB-NON-DESTRUCTION: UNSAT',
            'TGB-INV-003: Offline RAR computation procedure documented; rulebook PQC-sealed',
            'TGB-INV-004: Framework revision scan operational; EID issued on invalidity',
            'TGB-INV-005: TMR issued at HOT->WARM and WARM->COLD transitions for retained records',
        ]),
        ('C.5  Formal Verification', [
            'All 12 Z3 proof targets return UNSAT (see Section 7.1)',
            'All 8 TLA+ specification checks pass (see Section 7.2)',
            'FVS runner output archived with UIR as supporting evidence',
        ]),
    ]:
        st.append(Paragraph(section, s['h2']))
        for item in items:
            st.append(Paragraph(f'[ ]  {item}', s['bullet']))
        st.append(sp(4))

    # ==========================================================================
    # AUTHOR ADDRESS
    # ==========================================================================
    st.append(PageBreak())
    st.append(Paragraph("Author's Address", s['h1'])); st.append(rule(s)); st.append(sp(10))
    st.append(box([
        Paragraph('Harold Alberto Nunes Rodelo (Editor)', s['gold']), sp(4),
        Paragraph('OMNIX QUANTUM LTD', s['abody']),
        Paragraph('71-75 Shelton Street, Covent Garden', s['abody']),
        Paragraph('London WC2H 9JQ, England', s['abody']),
        Paragraph('Operational Headquarters: Abu Dhabi, UAE', s['abody']),
        sp(4),
        Paragraph('Email: standards@omnixquantum.com', s['abody']),
        Paragraph('Web:   omnixquantum.net', s['abody']),
        sp(8),
        Paragraph('RFC-ATF-5 Version 1.0.0 -- May 2026', s['caption']),
        Paragraph('Priority Records: OMNIX-PAR-2026-CGE-001 -- OMNIX-PAR-2026-GUGT-001 -- OMNIX-PAR-2026-TGB-001', s['caption']),
        Paragraph('DRAFT -- pending Zenodo submission', s['caption']),
    ], s, border=ACCENT_GOLD))

    doc.build(st, onFirstPage=on_page, onLaterPages=on_page)
    sz = os.path.getsize(output)/1024
    print(f'  PDF: {output}')
    print(f'  Size: {sz:.0f} KB')

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else OUT
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print('Generating RFC-ATF-5 PDF...')
    print(f'  Logo: {LOGO} {"[OK]" if os.path.exists(LOGO) else "[NOT FOUND]"}')
    build(out)
