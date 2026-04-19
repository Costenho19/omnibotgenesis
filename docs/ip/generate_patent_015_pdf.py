from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUTPUT = 'docs/ip/provisional_applications/pdf_exports/OMNIX_PAT_2026_015_PROVISIONAL.pdf'

NAVY  = colors.HexColor('#0A1628')
GOLD  = colors.HexColor('#C9A84C')
WHITE = colors.white
LGRAY = colors.HexColor('#F5F5F5')
DGRAY = colors.HexColor('#333333')
MGRAY = colors.HexColor('#666666')

doc = SimpleDocTemplate(OUTPUT, pagesize=A4,
    leftMargin=22*mm, rightMargin=22*mm,
    topMargin=28*mm, bottomMargin=22*mm,
    title='OMNIX-PAT-2026-015 Provisional Patent Application',
    author='Harold Alberto Nunes Rodelo')

def S(name, **kw):
    return ParagraphStyle(name, **kw)

h1       = S('H1',  fontName='Helvetica-Bold', fontSize=13, textColor=NAVY, spaceAfter=6, spaceBefore=14)
h2       = S('H2',  fontName='Helvetica-Bold', fontSize=11, textColor=NAVY, spaceAfter=4, spaceBefore=10)
body     = S('Body',fontName='Helvetica', fontSize=9.5, textColor=DGRAY, spaceAfter=5, leading=14, alignment=TA_JUSTIFY)
bold_b   = S('BB',  fontName='Helvetica-Bold', fontSize=9.5, textColor=DGRAY, spaceAfter=3, leading=14)
center   = S('Ctr', fontName='Helvetica', fontSize=9, textColor=MGRAY, spaceAfter=4, alignment=TA_CENTER)
code_s   = S('Cod', fontName='Courier', fontSize=8, textColor=DGRAY, spaceAfter=4, leading=12, leftIndent=10)
footer_s = S('Ftr', fontName='Helvetica', fontSize=7.5, textColor=MGRAY, alignment=TA_CENTER)

story = []

# HEADER
story.append(Table(
    [[Paragraph('OMNIX QUANTUM LTD', S('HH', fontName='Helvetica-Bold', fontSize=18, textColor=WHITE, alignment=TA_CENTER))],
     [Paragraph('PROVISIONAL PATENT APPLICATION', S('HS', fontName='Helvetica', fontSize=10, textColor=GOLD, alignment=TA_CENTER))],
     [Paragraph('OMNIX-PAT-2026-015  |  35 U.S.C. \u00a7 111(b)  |  Micro Entity  |  April 19, 2026',
                S('HD', fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#AAAAAA'), alignment=TA_CENTER))]],
    colWidths=[doc.width],
    style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('TOPPADDING',    (0,0), (-1,0),  14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LINEBELOW', (0,2), (-1,2), 1.5, GOLD),
    ])
))
story.append(Spacer(1, 8*mm))

# TITLE
story.append(Paragraph(
    'STRUCTURAL ADMISSIBILITY ENGINE FOR AUTOMATED DECISION GOVERNANCE SYSTEMS '
    'WITH PRE-PIPELINE SCHEMA VALIDATION, ENUMERATED CONSTRAINT ENCODING, '
    'AND ZERO-BYPASS BOUNDARY ENFORCEMENT', h1))
story.append(HRFlowable(width='100%', thickness=1.5, color=GOLD, spaceAfter=6))
story.append(Paragraph(
    '<b>Inventor:</b> Harold Alberto Nunes Rodelo &nbsp;|&nbsp; '
    '<b>Applicant:</b> OMNIX QUANTUM LTD &nbsp;|&nbsp; '
    '<b>Docket:</b> OMNIX-PAT-2026-015', center))
story.append(Spacer(1, 4*mm))

# FIELD
story.append(Paragraph('FIELD OF THE INVENTION', h1))
story.append(Paragraph(
    'The present invention relates to automated decision governance systems, and more particularly '
    'to a pre-pipeline structural admissibility layer that enforces decision admissibility at the '
    'point of input construction rather than at runtime evaluation \u2014 making structurally '
    'inadmissible decision requests unrepresentable as valid system objects. The Structural '
    'Admissibility Engine (SAE) constitutes a new architectural stratum \u2014 Layer 0 \u2014 that '
    'precedes and gates all downstream governance processing, providing a zero-bypass guarantee '
    'that no inadmissible request can enter the evaluation pipeline regardless of the operational '
    'state of any downstream component.', body))
story.append(Spacer(1, 3*mm))

# BACKGROUND
story.append(Paragraph('BACKGROUND', h1))
story.append(Paragraph('I. THE FUNDAMENTAL INADEQUACY OF RUNTIME INTERCEPTION', h2))
story.append(Paragraph(
    'Contemporary automated decision governance systems operate within a runtime interception '
    'model: they intercept and block invalid decisions after those decisions have been formulated '
    'and submitted. This architecture has five irremediable structural deficiencies:', body))

deficiencies = [
    ('<b>1.1 Bypass Through Component Failure.</b>',
     'Every blocking component must be operational for the governance guarantee to hold. '
     'A failed, disabled, or bypassed checkpoint may allow an inadmissible decision to proceed.'),
    ('<b>1.2 Latent Invalid State Generation.</b>',
     'The invalid decision is formulated as a system object before any checkpoint evaluates it, '
     'generating latent invalid state throughout memory, logs, and audit trails.'),
    ('<b>1.3 Governance Dependency on Execution Order.</b>',
     'Any inversion of checkpoint execution order \u2014 through code defect, configuration error, '
     'or concurrent execution \u2014 may permit an inadmissible decision to receive an execution commitment.'),
    ('<b>1.4 Absence of a Constitutive Boundary.</b>',
     'No architectural mechanism prevents the construction of a request for an operation '
     'categorically prohibited by jurisdiction, asset class, or ethical constraint.'),
    ('<b>1.5 No Constraint Provenance in Rejection.</b>',
     'Runtime rejection typically produces an error code or binary BLOCKED decision, '
     'without identifying the specific structural constraint violated or its regulatory source.'),
]
for label, text in deficiencies:
    story.append(Paragraph(f'{label} {text}', body))

story.append(Spacer(1, 2*mm))
story.append(Paragraph('II. PRIOR ART AND ITS LIMITATIONS', h2))
story.append(Paragraph(
    'Prior art includes runtime checkpoint pipelines (OMNIX-PAT-2026-001), web API schema '
    'validation (JSON Schema, OpenAPI), programming language type systems, and access control '
    'frameworks (OAuth, RBAC, ABAC). No prior art combines schema-level structural validation, '
    'regulatory constraint encoding, zero-bypass guarantee, structured rejection with constraint '
    'provenance, and composable cross-domain constraint architecture as a unified pre-pipeline '
    'governance layer for automated decision systems.', body))
story.append(Spacer(1, 3*mm))

# SUMMARY
story.append(Paragraph('SUMMARY OF THE INVENTION', h1))
components = [
    ('Component A', 'Structural Constraint Schema (SCS)',
     'Declarative, machine-readable specification of all admissibility constraints in four classes: '
     'Jurisdiction-Asset, Jurisdiction-Operation, Ethical Compliance (Sharia / ESG / Sanctions), '
     'and Client-Specific constraints.'),
    ('Component B', 'Structural Admissibility Validator (SAV)',
     'Pre-construction validator that evaluates a proposed decision request against the SCS '
     'before constructing any EvaluationRequest object. If any constraint is violated, '
     'no object is constructed.'),
    ('Component C', 'Zero-Bypass Boundary Enforcement (ZBE)',
     'Architectural guarantee that the SAV is the sole path through which a proposed request '
     'may become an EvaluationRequest object. EvaluationRequest construction is private to the SAV.'),
    ('Component D', 'Structured Rejection with Constraint Provenance (SRCP)',
     'Machine-readable rejection record identifying: violated constraint, constraint class, '
     'regulatory source, responsible input fields, and resolution guidance.'),
    ('Component E', 'Composable Cross-Domain Constraint Architecture (CCCA)',
     'Constraint composition mechanism allowing constraints from multiple domains to be evaluated '
     'simultaneously via a unified Constraint Registry without runtime branching logic.'),
]
for code, name, desc in components:
    story.append(Paragraph(f'<b>{code} \u2014 {name}:</b> {desc}', body))
story.append(Spacer(1, 3*mm))

# FOUR-LAYER ARCHITECTURE
story.append(Paragraph('THE FOUR-LAYER GOVERNANCE ARCHITECTURE', h1))
story.append(Paragraph(
    'The present invention introduces Layer 0 to the governance architecture. '
    '<b>Key distinction: Layers 1\u20133 evaluate requests that exist. Layer 0 determines what can exist.</b>', body))
layers = [
    ('Layer 0', 'Structural Admissibility Engine (present invention)',
     'Determines whether a proposed request is structurally representable as a valid system object. '
     'Only admissible requests proceed. Inadmissible requests are rejected before any downstream processing.'),
    ('Layer 1', 'OMNIX Runtime Pipeline',
     'Sequential multi-checkpoint pipeline (CP-0 through CP-11, TIE) evaluating signal quality, '
     'confidence, risk, temporal coherence, and jurisdiction compliance. (OMNIX-PAT-2026-001)'),
    ('Layer 2', 'Trajectory Invariant Engine',
     'Trajectory-aware evaluation against historical and projected behavioral trajectory. (OMNIX-PAT-2026-014)'),
    ('Layer 3', 'Evidence and Receipt Layer',
     'Post-quantum cryptographically sealed decision receipt \u2014 immutable audit record. (OMNIX-PAT-2026-001)'),
]
data = [['Layer', 'Name', 'Function']] + [[l, n, d] for l, n, d in layers]
tbl = Table(data, colWidths=[18*mm, 44*mm, doc.width - 62*mm])
tbl.setStyle(TableStyle([
    ('BACKGROUND',   (0,0), (-1,0),  NAVY),
    ('TEXTCOLOR',    (0,0), (-1,0),  WHITE),
    ('FONTNAME',     (0,0), (-1,0),  'Helvetica-Bold'),
    ('FONTSIZE',     (0,0), (-1,-1), 8.5),
    ('ROWBACKGROUNDS',(0,1),(-1,-1), [LGRAY, WHITE]),
    ('GRID',         (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
    ('VALIGN',       (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING',   (0,0), (-1,-1), 5),
    ('BOTTOMPADDING',(0,0), (-1,-1), 5),
    ('LEFTPADDING',  (0,0), (-1,-1), 6),
]))
story.append(tbl)
story.append(Spacer(1, 3*mm))

# ZERO-BYPASS
story.append(Paragraph('ZERO-BYPASS BOUNDARY ENFORCEMENT', h1))
story.append(Paragraph(
    'The zero-bypass property is the defining characteristic distinguishing the SAE from prior art. '
    'EvaluationRequest is defined with a private constructor accessible exclusively via the SAV:', body))
story.append(Paragraph(
    'class EvaluationRequest:\n'
    '    _SAV_TOKEN = object()  # Private sentinel\n'
    '    def __init__(self, _token, asset, operation, jurisdiction, client_id, metadata):\n'
    '        if _token is not self._SAV_TOKEN:\n'
    '            raise StructuralAdmissibilityViolation("Must use SAV.validate_and_construct()")\n\n'
    'class StructuralAdmissibilityValidator:\n'
    '    def validate_and_construct(self, proposed):\n'
    '        violations = self._evaluate_all_constraints(proposed)\n'
    '        if violations: raise StructuralAdmissibilityViolation(violations)\n'
    '        return EvaluationRequest(_token=EvaluationRequest._SAV_TOKEN, **proposed)',
    code_s))
story.append(Paragraph(
    'Guarantee: silence is impossible \u2014 an inadmissible request either raises an exception '
    'or is never constructed. No code path, configuration flag, or operational condition '
    'can produce an EvaluationRequest without passing through the SAV.', bold_b))
story.append(Spacer(1, 3*mm))

# CLAIMS
story.append(Paragraph('CLAIMS', h1))
claims = [
    'A computer-implemented Structural Admissibility Engine comprising: (a) a Structural Constraint '
    'Schema encoding admissibility constraints in at least two classes including jurisdiction-asset '
    'and jurisdiction-operation constraints; (b) a Structural Admissibility Validator evaluating '
    'proposed decision requests against the Schema before constructing any EvaluationRequest object; '
    '(c) wherein the Validator constructs the EvaluationRequest only if all applicable constraints '
    'are satisfied; and (d) wherein the Validator does not construct the EvaluationRequest if any '
    'applicable constraint is violated.',

    'The SAE of claim 1, wherein the EvaluationRequest type comprises a private constructor '
    'accessible exclusively through the Structural Admissibility Validator, enforcing a zero-bypass '
    'property whereby no external code path can construct a valid EvaluationRequest object.',

    'The SAE of claim 1, wherein the Structural Constraint Schema further comprises ethical '
    'compliance constraints derived from at least one of: Sharia compliance criteria, ESG screening '
    'criteria, and international sanctions lists.',

    'The SAE of claim 1, wherein the Structural Constraint Schema further comprises client-specific '
    'constraints that may further restrict but may not expand the admissibility determined by '
    'jurisdiction-asset and jurisdiction-operation constraints.',

    'The SAE of claim 1, wherein structural rejection returns a Structured Rejection Record '
    'comprising: constraint identifier, constraint class, regulatory source citation, identification '
    'of responsible input fields, and a resolution guidance field.',

    'The SAE of claim 1, wherein the composable cross-domain constraint architecture evaluates '
    'constraints from multiple classes simultaneously via a unified Constraint Registry, extensible '
    'by constraint addition without modification to the Validator evaluation logic.',

    'The SAE of claim 1, constituting Layer 0 of a four-layer governance architecture, wherein '
    'Layer 0 gates a Layer 1 runtime checkpoint pipeline accepting only EvaluationRequest objects '
    '\u2014 ensuring the pipeline cannot receive inadmissible inputs regardless of the operational '
    'state of any Layer 1 checkpoint.',

    'The SAE of claim 1, wherein constraint evaluation operates on in-memory constraint tables '
    'with asynchronous refresh for dynamic constraint classes and atomic in-memory table updates.',

    'The SAE of claim 7, wherein the four-layer architecture further comprises Layer 2, a '
    'trajectory invariant enforcement layer; and Layer 3, a post-quantum cryptographically '
    'sealed audit receipt layer.',

    'A method for enforcing structural admissibility comprising: (a) receiving a proposed decision '
    'request; (b) evaluating the request against a Structural Constraint Schema before constructing '
    'any system object; (c) if admissible, constructing an EvaluationRequest via the SAV and '
    'forwarding to a downstream pipeline; (d) if inadmissible, returning a Structured Rejection '
    'Record and not constructing any object; and (e) enforcing zero-bypass by restricting '
    'EvaluationRequest construction to the SAV.',
]
for i, claim in enumerate(claims, 1):
    story.append(Paragraph(f'<b>{i}.</b> {claim}', body))
story.append(Spacer(1, 3*mm))

# ABSTRACT
story.append(Paragraph('ABSTRACT', h1))
story.append(HRFlowable(width='100%', thickness=1, color=GOLD, spaceAfter=6))
story.append(Paragraph(
    'A Structural Admissibility Engine (SAE) for automated decision governance systems enforces '
    'decision admissibility at the point of input construction rather than at runtime evaluation, '
    'making structurally inadmissible decision requests unrepresentable as valid system objects. '
    'The SAE comprises a Structural Constraint Schema encoding regulatory, jurisdictional, and '
    'ethical constraints; a Structural Admissibility Validator that evaluates proposed requests '
    'before constructing any EvaluationRequest object; and a Zero-Bypass Boundary Enforcement '
    'mechanism restricting EvaluationRequest construction exclusively to the Validator. '
    'Inadmissible requests are rejected at the structural boundary with a Structured Rejection '
    'Record providing machine-readable constraint provenance. The SAE constitutes Layer 0 of a '
    'four-layer governance architecture gating a downstream runtime checkpoint pipeline (Layer 1), '
    'trajectory invariant enforcement layer (Layer 2), and cryptographic receipt layer (Layer 3). '
    'The zero-bypass property guarantees that no inadmissible request can enter the governance '
    'pipeline regardless of the operational state of any downstream component \u2014 a categorical '
    'improvement over runtime interception architectures where governance guarantees are contingent '
    'on every intercepting component being operational and correctly implemented.', body))
story.append(Spacer(1, 4*mm))
story.append(HRFlowable(width='100%', thickness=0.5, color=MGRAY, spaceAfter=4))
story.append(Paragraph(
    'OMNIX-PAT-2026-015 &nbsp;|&nbsp; Harold Alberto Nunes Rodelo &nbsp;|&nbsp; '
    'OMNIX Quantum Ltd, United Kingdom &nbsp;|&nbsp; April 19, 2026<br/>'
    'CONFIDENTIAL \u2014 FOR USPTO FILING PURPOSES',
    footer_s))

doc.build(story)
print('PDF generado:', OUTPUT)
