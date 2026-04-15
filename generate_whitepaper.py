"""
OMNIX — Commercial Whitepaper 2026
Decision Governance Infrastructure for Automated Systems
Commercial Grade — CISO & Executive Audience
"""

import os
import tempfile
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
 SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
 HRFlowable, PageBreak, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ── Palette ───────────────────────────────────────────────────────────────────
DARK_BG = HexColor('#0a0f1a')
CARD_BG = HexColor('#1e293b')
CARD2_BG = HexColor('#162032')
GOLD = HexColor('#C9A227')
GOLD_LIGHT = HexColor('#F5D97A')
RED_ALERT = HexColor('#ef4444')
GREEN_OK = HexColor('#10b981')
GRAY = HexColor('#94a3b8')
GRAY2 = HexColor('#64748b')
WHITE = HexColor('#ffffff')
BLUE = HexColor('#3b82f6')
CYAN = HexColor('#06b6d4')
BORDER = HexColor('#334155')
DARK_RED = HexColor('#2d0f0f')
DARK_GREEN = HexColor('#0a1f14')

W, H = letter
LOGO = '/home/runner/workspace/omnix_web/public/omnix_logo.png'
OUTPUT = '/home/runner/workspace/OMNIX_Technical_Whitepaper_2026.pdf'


def prepare_logo(bg=(10, 15, 26)):
 img = PILImage.open(LOGO).convert('RGBA')
 background = PILImage.new('RGB', img.size, bg)
 background.paste(img, mask=img.split()[3])
 tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
 background.save(tmp.name)
 return tmp.name


LOGO_DARK = prepare_logo() if os.path.exists(LOGO) else None


# ── Page background ───────────────────────────────────────────────────────────
def dark_page(c, doc):
 c.saveState()
 c.setFillColor(DARK_BG)
 c.rect(0, 0, W, H, fill=1, stroke=0)
 c.setFillColor(GOLD)
 c.rect(0, 0, 4, H, fill=1, stroke=0)
 c.setFillColor(GRAY2)
 c.setFont('Helvetica', 7)
 c.drawString(0.75 * inch, 0.35 * inch,
 'OMNIX — Decision Governance Infrastructure | Confidential')
 c.drawRightString(W - 0.65 * inch, 0.35 * inch, 'omnixquantum.net')
 c.drawCentredString(W / 2, 0.35 * inch, 'April 2026 · Harold Nunes, Founder & CEO')
 c.setStrokeColor(BORDER)
 c.setLineWidth(0.5)
 c.line(0.65 * inch, 0.52 * inch, W - 0.65 * inch, 0.52 * inch)
 c.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
 s = getSampleStyleSheet()
 defs = [
 ParagraphStyle('CoverMeta', fontName='Helvetica', fontSize=9, textColor=GRAY, spaceAfter=3, spaceBefore=2, alignment=TA_LEFT),
 ParagraphStyle('SectionTitle', fontName='Helvetica-Bold', fontSize=15, textColor=GOLD, spaceAfter=8, spaceBefore=14, alignment=TA_LEFT),
 ParagraphStyle('SectionSub', fontName='Helvetica-Bold', fontSize=10, textColor=CYAN, spaceAfter=5, spaceBefore=8, alignment=TA_LEFT),
 ParagraphStyle('Body', fontName='Helvetica', fontSize=9.5, textColor=GRAY, spaceAfter=6, spaceBefore=2, alignment=TA_JUSTIFY, leading=15),
 ParagraphStyle('BodyW', fontName='Helvetica', fontSize=9.5, textColor=WHITE, spaceAfter=6, spaceBefore=2, alignment=TA_JUSTIFY, leading=15),
 ParagraphStyle('BigStat', fontName='Helvetica-Bold', fontSize=28, textColor=GOLD, spaceAfter=2, spaceBefore=2, alignment=TA_CENTER, leading=32),
 ParagraphStyle('StatLabel', fontName='Helvetica', fontSize=8, textColor=GRAY, spaceAfter=0, spaceBefore=0, alignment=TA_CENTER, leading=11),
 ParagraphStyle('Quote', fontName='Helvetica-Oblique', fontSize=11, textColor=GOLD_LIGHT, spaceAfter=8, spaceBefore=8, alignment=TA_CENTER, leading=17, leftIndent=20, rightIndent=20),
 ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8, textColor=GOLD, leading=11),
 ParagraphStyle('TD', fontName='Helvetica', fontSize=8.5, textColor=WHITE, leading=13),
 ParagraphStyle('TDGray', fontName='Helvetica', fontSize=8.5, textColor=GRAY, leading=13),
 ParagraphStyle('TDCyan', fontName='Helvetica-Bold', fontSize=8.5, textColor=CYAN, leading=13),
 ParagraphStyle('TDGold', fontName='Helvetica-Bold', fontSize=8.5, textColor=GOLD, leading=13),
 ParagraphStyle('TDGreen', fontName='Helvetica-Bold', fontSize=8.5, textColor=GREEN_OK, leading=13),
 ParagraphStyle('TDRed', fontName='Helvetica-Bold', fontSize=8.5, textColor=RED_ALERT, leading=13),
 ParagraphStyle('SmallGray', fontName='Helvetica', fontSize=7.5, textColor=GRAY, spaceAfter=3, alignment=TA_LEFT),
 ParagraphStyle('Bullet', fontName='Helvetica', fontSize=9.5, textColor=GRAY, spaceAfter=4, spaceBefore=1, alignment=TA_LEFT, leading=14, leftIndent=12),
 ParagraphStyle('ImpactNum', fontName='Helvetica-Bold', fontSize=22, textColor=RED_ALERT, spaceAfter=2, spaceBefore=2, alignment=TA_CENTER, leading=26),
 ParagraphStyle('ImpactLabel', fontName='Helvetica', fontSize=8, textColor=GRAY, spaceAfter=0, spaceBefore=0, alignment=TA_CENTER, leading=11),
 ParagraphStyle('GreenNum', fontName='Helvetica-Bold', fontSize=22, textColor=GREEN_OK, spaceAfter=2, spaceBefore=2, alignment=TA_CENTER, leading=26),
 ]
 for st in defs:
 try:
 s.add(st)
 except Exception:
 pass
 return s


ST = make_styles()


# ── Helpers ───────────────────────────────────────────────────────────────────
def th(t): return Paragraph(t, ST['TH'])
def td(t): return Paragraph(t, ST['TD'])
def tdg(t): return Paragraph(t, ST['TDGray'])
def tdc(t): return Paragraph(t, ST['TDCyan'])
def tdgold(t): return Paragraph(t, ST['TDGold'])
def tdgreen(t): return Paragraph(t, ST['TDGreen'])
def tdred(t): return Paragraph(t, ST['TDRed'])


BASE_TS = TableStyle([
 ('BACKGROUND', (0, 0), (-1, 0), HexColor('#0d1929')),
 ('ROWBACKGROUNDS',(0, 1), (-1, -1), [CARD_BG, CARD2_BG]),
 ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
 ('TOPPADDING', (0, 0), (-1, -1), 7),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
 ('LEFTPADDING', (0, 0), (-1, -1), 9),
 ('RIGHTPADDING', (0, 0), (-1, -1), 9),
])


def card(rows, cols):
 t = Table(rows, colWidths=cols)
 t.setStyle(BASE_TS)
 return t


def gold_bar(text):
 t = Table(
 [[Paragraph(f'<b>{text}</b>',
 ParagraphStyle('gb', fontName='Helvetica-Bold', fontSize=11,
 textColor=DARK_BG))]],
 colWidths=[7.1 * inch]
 )
 t.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (-1, -1), GOLD),
 ('TOPPADDING', (0, 0), (-1, -1), 8),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
 ('LEFTPADDING', (0, 0), (-1, -1), 12),
 ]))
 return t


def section(title):
 return [
 Spacer(1, 0.06 * inch),
 HRFlowable(width='100%', thickness=0.5, color=BORDER),
 Spacer(1, 0.04 * inch),
 Paragraph(title, ST['SectionTitle']),
 ]


def impact_box(num, label, color=RED_ALERT, bg=None):
 bg = bg or DARK_RED
 num_style = ParagraphStyle('n', fontName='Helvetica-Bold', fontSize=22,
 textColor=color, alignment=TA_CENTER, leading=26)
 lbl_style = ParagraphStyle('l', fontName='Helvetica', fontSize=8,
 textColor=GRAY, alignment=TA_CENTER, leading=12)
 t = Table([[Paragraph(num, num_style)], [Paragraph(label, lbl_style)]],
 colWidths=[2.3 * inch],
 rowHeights=[44, 38])
 t.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (-1, -1), bg),
 ('BOX', (0, 0), (-1, -1), 1, color),
 ('TOPPADDING', (0, 0), (-1, -1), 8),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
 ('LEFTPADDING', (0, 0), (-1, -1), 6),
 ('RIGHTPADDING', (0, 0), (-1, -1), 6),
 ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
 ]))
 return t


def logo_header():
 if not LOGO_DARK:
 return Paragraph('<b>OMNIX</b> Decision Governance Infrastructure',
 ParagraphStyle('lh', fontName='Helvetica-Bold',
 fontSize=13, textColor=WHITE))
 row = Table(
 [[Image(LOGO_DARK, width=0.85 * inch, height=0.70 * inch),
 Paragraph(
 '<font color="#C9A227"><b>OMNIX</b></font> '
 '<font color="#94a3b8">Decision Governance Infrastructure</font>',
 ParagraphStyle('lh', fontName='Helvetica-Bold', fontSize=13,
 textColor=WHITE, leading=18)
 )]],
 colWidths=[1.0 * inch, 6.1 * inch]
 )
 row.setStyle(TableStyle([
 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
 ('LEFTPADDING', (0, 0), (-1, -1), 0),
 ('RIGHTPADDING', (0, 0), (-1, -1), 0),
 ('TOPPADDING', (0, 0), (-1, -1), 0),
 ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
 ]))
 return row


# ─────────────────────────────────────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────────────────────────────────────
def build():
 doc = SimpleDocTemplate(
 OUTPUT, pagesize=letter,
 leftMargin=0.70 * inch, rightMargin=0.65 * inch,
 topMargin=0.65 * inch, bottomMargin=0.80 * inch
 )
 E = []

 # ═══════════════════════════════════════════════════════════════════════════
 # COVER
 # ═══════════════════════════════════════════════════════════════════════════
 E.append(Spacer(1, 0.20 * inch))
 E.append(logo_header())
 E.append(Spacer(1, 0.28 * inch))
 E.append(HRFlowable(width='100%', thickness=2, color=GOLD))
 E.append(Spacer(1, 0.22 * inch))

 E.append(Paragraph(
 'What Happens When an<br/>Automated System Makes<br/>the Wrong Decision<br/>'
 '<font color="#C9A227">— And There Is No Record?</font>',
 ParagraphStyle('CH', fontName='Helvetica-Bold', fontSize=22,
 textColor=WHITE, leading=30, spaceAfter=10)
 ))
 E.append(Spacer(1, 0.10 * inch))
 E.append(Paragraph(
 'OMNIX is the governance infrastructure that ensures every automated decision '
 'is evaluated, authorized, and cryptographically sealed — before it executes.',
 ParagraphStyle('CS', fontName='Helvetica', fontSize=11,
 textColor=GRAY, leading=17, alignment=TA_LEFT)
 ))
 E.append(Spacer(1, 0.22 * inch))
 E.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
 E.append(Spacer(1, 0.14 * inch))

 E.append(Paragraph('April 2026 · Confidential', ST['CoverMeta']))
 E.append(Paragraph('Harold Nunes · Founder &amp; CEO', ST['CoverMeta']))
 E.append(Paragraph('contacto@omnixquantum.net · omnixquantum.net', ST['CoverMeta']))
 E.append(Spacer(1, 0.22 * inch))

 # Cover stats row
 stats_row = Table(
 [[impact_box('$137B+', 'Total Addressable\nMarket', GOLD, HexColor('#1a150a')),
 impact_box('11', 'Governance\nCheckpoints per Decision', CYAN, HexColor('#0a1520')),
 impact_box('24/7', 'Production\nOperation — Live Now', GREEN_OK, DARK_GREEN)]],
 colWidths=[2.37 * inch, 2.37 * inch, 2.37 * inch]
 )
 stats_row.setStyle(TableStyle([
 ('LEFTPADDING', (0, 0), (-1, -1), 0),
 ('RIGHTPADDING', (0, 0), (-1, -1), 0),
 ('TOPPADDING', (0, 0), (-1, -1), 0),
 ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
 ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
 ]))
 E.append(stats_row)
 E.append(Spacer(1, 0.18 * inch))

 # Cover badges
 badge_data = [[
 Paragraph('\nSemifinalist',
 ParagraphStyle('b1', fontName='Helvetica-Bold', fontSize=8,
 textColor=GOLD, alignment=TA_CENTER, leading=12)),
 Paragraph('SSRN · 2 Papers\n6321298 · 6507559',
 ParagraphStyle('b2', fontName='Helvetica-Bold', fontSize=8,
 textColor=GREEN_OK, alignment=TA_CENTER, leading=12)),
 Paragraph('Zenodo · 2 DOIs\n19056919 · 19375792',
 ParagraphStyle('b3', fontName='Helvetica-Bold', fontSize=8,
 textColor=CYAN, alignment=TA_CENTER, leading=12)),
 Paragraph('Pre-Seed Round\n$500K at $3M pre-money',
 ParagraphStyle('b4', fontName='Helvetica-Bold', fontSize=8,
 textColor=WHITE, alignment=TA_CENTER, leading=12)),
 ]]
 badge_t = Table(badge_data, colWidths=[1.77 * inch] * 4)
 badge_t.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (0, 0), HexColor('#1a150a')),
 ('BACKGROUND', (1, 0), (1, 0), HexColor('#0a1a12')),
 ('BACKGROUND', (2, 0), (2, 0), HexColor('#0a1520')),
 ('BACKGROUND', (3, 0), (3, 0), CARD_BG),
 ('BOX', (0, 0), (0, 0), 1, GOLD),
 ('BOX', (1, 0), (1, 0), 1, GREEN_OK),
 ('BOX', (2, 0), (2, 0), 1, CYAN),
 ('BOX', (3, 0), (3, 0), 1, BORDER),
 ('TOPPADDING', (0, 0), (-1, -1), 9),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
 ('LEFTPADDING', (0, 0), (-1, -1), 5),
 ('RIGHTPADDING', (0, 0), (-1, -1), 5),
 ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
 ]))
 E.append(badge_t)

 E.append(PageBreak())

 # ═══════════════════════════════════════════════════════════════════════════
 # THE COST OF UNAUDITED DECISIONS
 # ═══════════════════════════════════════════════════════════════════════════
 E.extend(section('The Real Cost of One Unaudited Decision'))
 E.append(Paragraph(
 'Every day, automated systems execute thousands of decisions that carry '
 'direct financial, legal, and reputational exposure. The question is not '
 'whether something will go wrong — it is whether you will be able to prove '
 'what happened when it does.',
 ST['Body']
 ))
 E.append(Spacer(1, 0.10 * inch))

 cost_row = Table(
 [[impact_box('€35M', 'Maximum fine under\nEU AI Act per incident', RED_ALERT, DARK_RED),
 impact_box('$50M+', 'Regulatory fine per\nAML enforcement action', RED_ALERT, DARK_RED),
 impact_box('3+', 'Regulatory frameworks\nrequiring AI audit trails', RED_ALERT, DARK_RED)]],
 colWidths=[2.37 * inch, 2.37 * inch, 2.37 * inch]
 )
 cost_row.setStyle(TableStyle([
 ('LEFTPADDING', (0, 0), (-1, -1), 0),
 ('RIGHTPADDING', (0, 0), (-1, -1), 0),
 ('TOPPADDING', (0, 0), (-1, -1), 0),
 ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
 ]))
 E.append(cost_row)
 E.append(Spacer(1, 0.12 * inch))

 E.append(Paragraph(
 '"When regulators ask what the system decided, why it decided it, '
 'and who authorized it — most organizations cannot answer any of the three."',
 ST['Quote']
 ))
 E.append(Spacer(1, 0.08 * inch))

 scenario_data = [
 [th('Scenario'), th('Without OMNIX'), th('With OMNIX')],
 [td('Automated trade executes incorrectly'),
 tdred('No signed record. Dispute resolution takes months. Potential liability.'),
 tdgreen('Signed receipt proves what was evaluated and authorized. Dispute resolved in hours.')],
 [td('Regulator requests AI decision audit'),
 tdred('Logs may be incomplete or missing. No cryptographic proof. Non-compliance risk.'),
 tdgreen('Every decision carries a tamper-evident receipt. Full audit trail delivered instantly.')],
 [td('Insurance claim denied by automated system'),
 tdred('Client disputes denial. No verifiable record of evaluation criteria applied.'),
 tdgreen('Receipt shows all 11 checkpoints passed or which one blocked the decision.')],
 [td('Autonomous system takes unauthorized action'),
 tdred('No pre-execution gate. System acted without independent governance approval.'),
 tdgreen('Fail-closed pipeline blocked execution. Receipt proves governance was applied.')],
 ]
 E.append(card(scenario_data, [1.9 * inch, 2.6 * inch, 2.6 * inch]))

 E.append(PageBreak())

 # ═══════════════════════════════════════════════════════════════════════════
 # WHAT OMNIX DOES
 # ═══════════════════════════════════════════════════════════════════════════
 E.extend(section('What OMNIX Does'))
 E.append(Paragraph(
 'OMNIX sits between your automated system and the moment a decision executes. '
 'It evaluates every proposed decision through 11 independent governance checkpoints '
 'and issues a cryptographically-sealed receipt. No receipt — no execution.',
 ST['Body']
 ))
 E.append(Spacer(1, 0.10 * inch))

 # Flow diagram using table
 flow_data = [
 [Paragraph('AUTOMATED\nSYSTEM',
 ParagraphStyle('fw', fontName='Helvetica-Bold', fontSize=9,
 textColor=GRAY, alignment=TA_CENTER, leading=13)),
 Paragraph('→',
 ParagraphStyle('arr', fontName='Helvetica-Bold', fontSize=18,
 textColor=GOLD, alignment=TA_CENTER)),
 Paragraph('OMNIX\n11 CHECKPOINTS',
 ParagraphStyle('fw2', fontName='Helvetica-Bold', fontSize=9,
 textColor=GOLD, alignment=TA_CENTER, leading=13)),
 Paragraph('→',
 ParagraphStyle('arr', fontName='Helvetica-Bold', fontSize=18,
 textColor=GOLD, alignment=TA_CENTER)),
 Paragraph('SIGNED\nRECEIPT',
 ParagraphStyle('fw3', fontName='Helvetica-Bold', fontSize=9,
 textColor=CYAN, alignment=TA_CENTER, leading=13)),
 Paragraph('→',
 ParagraphStyle('arr', fontName='Helvetica-Bold', fontSize=18,
 textColor=GOLD, alignment=TA_CENTER)),
 Paragraph('EXECUTION\nAUTHORIZED',
 ParagraphStyle('fw4', fontName='Helvetica-Bold', fontSize=9,
 textColor=GREEN_OK, alignment=TA_CENTER, leading=13)),
 ]
 ]
 flow_t = Table(flow_data, colWidths=[1.1*inch, 0.4*inch, 1.6*inch,
 0.4*inch, 1.1*inch, 0.4*inch, 1.6*inch])
 flow_t.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (0, 0), CARD_BG),
 ('BACKGROUND', (2, 0), (2, 0), HexColor('#1a150a')),
 ('BACKGROUND', (4, 0), (4, 0), HexColor('#0a1520')),
 ('BACKGROUND', (6, 0), (6, 0), DARK_GREEN),
 ('BOX', (0, 0), (0, 0), 1, BORDER),
 ('BOX', (2, 0), (2, 0), 1, GOLD),
 ('BOX', (4, 0), (4, 0), 1, CYAN),
 ('BOX', (6, 0), (6, 0), 1, GREEN_OK),
 ('TOPPADDING', (0, 0), (-1, -1), 12),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
 ('LEFTPADDING', (0, 0), (-1, -1), 4),
 ('RIGHTPADDING', (0, 0), (-1, -1), 4),
 ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
 ]))
 E.append(flow_t)
 E.append(Spacer(1, 0.06 * inch))
 E.append(Paragraph(
 'If any checkpoint fails → pipeline halts → decision is BLOCKED → signed receipt issued.',
 ParagraphStyle('note', fontName='Helvetica-Oblique', fontSize=8.5,
 textColor=GRAY, alignment=TA_CENTER, leading=12)
 ))
 E.append(Spacer(1, 0.12 * inch))

 three_outcomes = [
 [th('Decision Result'), th('What It Means'), th('Receipt Issued?')],
 [tdgreen('APPROVED'),
 td('All 11 checkpoints authorized the decision. Execution proceeds.'),
 tdgreen('Yes — signed proof of authorization')],
 [tdred('BLOCKED'),
 td('One or more checkpoints identified a governance violation. Execution halted.'),
 tdred('Yes — signed proof of rejection and reason')],
 [Paragraph('<b>HOLD</b>',
 ParagraphStyle('hold', fontName='Helvetica-Bold', fontSize=8.5,
 textColor=GOLD_LIGHT, leading=13)),
 td('Internal signal contradiction detected. Human review required before proceeding.'),
 Paragraph('<b>Yes — signed escalation record</b>',
 ParagraphStyle('holdy', fontName='Helvetica-Bold', fontSize=8.5,
 textColor=GOLD_LIGHT, leading=13))],
 ]
 E.append(card(three_outcomes, [1.3 * inch, 3.8 * inch, 2.0 * inch]))

 E.append(PageBreak())

 # ═══════════════════════════════════════════════════════════════════════════
 # 11 CHECKPOINTS
 # ═══════════════════════════════════════════════════════════════════════════
 E.extend(section('The 11 Governance Checkpoints'))
 E.append(Paragraph(
 'Each decision submitted to OMNIX passes through 11 independent checkpoints in sequence. '
 'Every checkpoint operates autonomously — a failure at any stage halts the pipeline '
 'immediately and issues a signed rejection receipt. No checkpoint can be bypassed or overridden.',
 ST['Body']
 ))
 E.append(Spacer(1, 0.10 * inch))

 cp_data = [
 [th('CP'), th('Checkpoint'), th('What It Evaluates'), th('If It Fails')],
 [tdc('CP-1'), tdgold('Signal Integrity\nValidator (SIV)'),
 td('Verifies data quality, completeness, and input integrity before any evaluation begins.'),
 tdred('Rejected at entry.\nPipeline never opens.')],
 [tdc('CP-2'), tdgold('Probability\nAssessment'),
 td('Evaluates statistical confidence in the proposed decision outcome against authorized thresholds.'),
 tdred('Blocked.\nInsufficient confidence.')],
 [tdc('CP-3'), tdgold('Risk\nEvaluation'),
 td('Quantifies downside exposure and compares against the authorized risk envelope for the domain.'),
 tdred('Blocked.\nRisk limit exceeded.')],
 [tdc('CP-4'), tdgold('Coherence\nEngine'),
 td('Detects internal contradictions across all active signals. Decision Contradiction Index (DCI) ≥ 70 mandates escalation.'),
 tdred('HOLD.\nHuman review required.')],
 [tdc('CP-5'), tdgold('Trend\nValidator'),
 td('Confirms alignment between the proposed decision and the prevailing operational or market regime.'),
 tdred('Blocked.\nRegime contradiction.')],
 [tdc('CP-6'), tdgold('Stress\nTesting'),
 td('Simulates adverse conditions (liquidity shocks, volatility spikes) to validate decision robustness.'),
 tdred('Blocked.\nFails under stress.')],
 [tdc('CP-7'), tdgold('Ethics &\nDomain Gate'),
 td('Enforces domain-specific ethical constraints: Sharia compliance (riba, gharar), safety limits for robotics, bias controls for credit.'),
 tdred('Blocked.\nEthics violation recorded.')],
 [tdc('CP-8'), tdgold('Threshold &\nContext Validator'),
 td('Validates all decision parameters against authorized operational boundaries and contextual constraints.'),
 tdred('Blocked.\nParameter out of range.')],
 [tdc('CP-9'), tdgold('AML\nScreening'),
 td('Screens for anti-money laundering indicators, suspicious transaction patterns, and sanctioned entity exposure.'),
 tdred('Blocked.\nSuspicious activity flagged.')],
 [tdc('CP-10'), tdgold('Fraud\nDetection'),
 td('Multi-layer fraud signal analysis across behavioral, transactional, and systemic patterns.'),
 tdred('Blocked.\nFraud flag escalated.')],
 [tdc('CP-11'), tdgold('Jurisdiction\nCompliance'),
 td('Verifies regulatory jurisdiction eligibility before any cross-border or regulated decision executes.'),
 tdred('Blocked.\nJurisdiction violation.')],
 ]
 E.append(card(cp_data, [0.45 * inch, 1.25 * inch, 3.3 * inch, 2.1 * inch]))
 E.append(Spacer(1, 0.10 * inch))
 E.append(Paragraph(
 '"Every checkpoint is independent. The system cannot approve a decision because 10 out of 11 passed. '
 'All 11 must pass. This is what fail-closed governance means."',
 ST['Quote']
 ))

 E.append(PageBreak())

 # ═══════════════════════════════════════════════════════════════════════════
 # ROI
 # ═══════════════════════════════════════════════════════════════════════════
 E.extend(section('The Business Case: ROI & Value Delivered'))
 E.append(Paragraph(
 'OMNIX is not a cost center — it is a risk-reduction investment with a '
 'quantifiable return. The value delivered falls into three categories: '
 'regulatory protection, operational efficiency, and reputational capital.',
 ST['Body']
 ))
 E.append(Spacer(1, 0.10 * inch))

 # ROI stats
 roi_row = Table(
 [[impact_box('$500K+', 'Minimum regulatory fine\navoided per incident', GREEN_OK, DARK_GREEN),
 impact_box('100%', 'Audit trail coverage\nfor every decision', GREEN_OK, DARK_GREEN),
 impact_box('Always', 'Fail-closed — no receipt\nmeans no execution', GREEN_OK, DARK_GREEN)]],
 colWidths=[2.37 * inch, 2.37 * inch, 2.37 * inch]
 )
 roi_row.setStyle(TableStyle([
 ('LEFTPADDING', (0, 0), (-1, -1), 0),
 ('RIGHTPADDING', (0, 0), (-1, -1), 0),
 ('TOPPADDING', (0, 0), (-1, -1), 0),
 ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
 ]))
 E.append(roi_row)
 E.append(Spacer(1, 0.12 * inch))

 roi_data = [
 [th('Value Category'), th('Without OMNIX'), th('With OMNIX'), th('Estimated Impact')],
 [tdgold('Regulatory Fines'),
 tdred('No audit trail.\nFull exposure.'),
 tdgreen('Signed receipt\nper decision.'),
 td('€35M EU AI Act\nexposure eliminated')],
 [tdgold('Incident Response'),
 tdred('Weeks of log\nreconstruction.'),
 tdgreen('Instant receipt\nretrieval.'),
 td('80% reduction in\nresponse time')],
 [tdgold('Legal Disputes'),
 tdred('He said / she said.\nNo proof.'),
 tdgreen('Cryptographic proof\nof what was decided.'),
 td('Disputes resolved\nin hours, not months')],
 [tdgold('Compliance Reporting'),
 tdred('Manual, error-prone,\nexpensive to produce.'),
 tdgreen('Automated, signed,\ninstantly accessible.'),
 td('60–80% reduction\nin compliance cost')],
 [tdgold('Client Trust'),
 tdred('Black box —\ncannot explain decisions.'),
 tdgreen('Public verification URL\nper decision.'),
 td('Measurable increase\nin client retention')],
 ]
 E.append(card(roi_data, [1.4 * inch, 1.7 * inch, 1.7 * inch, 2.3 * inch]))
 E.append(Spacer(1, 0.10 * inch))

 # ROI calculation box
 roi_box = Table(
 [[Paragraph(
 '<b>Simple ROI Calculation</b><br/><br/>'
 'OMNIX Enterprise cost: <font color="#C9A227">$20,000 – $35,000 / month</font><br/>'
 'One avoided EU AI Act fine: <font color="#10b981">€35,000,000</font><br/>'
 'Break-even point: <font color="#10b981">1 avoided incident = 145 years of OMNIX cost</font><br/><br/>'
 'The question is not whether OMNIX is expensive.<br/>'
 'The question is whether you can afford to operate without it.',
 ParagraphStyle('roi', fontName='Helvetica', fontSize=10, textColor=WHITE,
 leading=17, alignment=TA_JUSTIFY)
 )]],
 colWidths=[7.1 * inch]
 )
 roi_box.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
 ('BOX', (0, 0), (-1, -1), 2, GOLD),
 ('TOPPADDING', (0, 0), (-1, -1), 14),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
 ('LEFTPADDING', (0, 0), (-1, -1), 16),
 ('RIGHTPADDING', (0, 0), (-1, -1), 16),
 ]))
 E.append(roi_box)

 E.append(PageBreak())

 # ═══════════════════════════════════════════════════════════════════════════
 # FOUR DOMAINS
 # ═══════════════════════════════════════════════════════════════════════════
 E.extend(section('Four Active Governance Domains'))
 E.append(Paragraph(
 'The same governance pipeline operates across four distinct industries simultaneously. '
 'OMNIX does not need to be rebuilt for each domain — it is configured. '
 'This is what makes it infrastructure, not software.',
 ST['Body']
 ))
 E.append(Spacer(1, 0.08 * inch))

 domain_data = [
 [th('Domain'), th('What OMNIX Governs'), th('Key Risk Eliminated'), th('Status')],
 [tdgold('Digital Asset\nTrading'),
 td('Every trade entry and exit decision. Real capital on Kraken exchange.'),
 tdred('Unauthorized execution\nunder adverse conditions'),
 tdgreen('LIVE 24/7')],
 [tdgold('Islamic Credit\nGCC / MENA'),
 td('Murabaha financing decisions. Sharia compliance enforced at CP-6.'),
 tdred('Riba violation and\nnon-compliant structuring'),
 tdgreen('OPERATIONAL')],
 [tdgold('Insurance\nClaims'),
 td('Automated claim assessment and fraud screening decisions.'),
 tdred('Fraudulent approval\nand unaudited denial'),
 tdgreen('OPERATIONAL')],
 [tdgold('Robotics\nPre-Execution'),
 td('Autonomous action authorization before any physical command executes.'),
 tdred('Unauthorized physical\naction — safety breach'),
 tdgreen('OPERATIONAL')],
 ]
 E.append(card(domain_data, [1.3 * inch, 2.5 * inch, 2.0 * inch, 1.3 * inch]))
 E.append(Spacer(1, 0.10 * inch))

 E.append(Paragraph(
 '"The same 11-checkpoint pipeline that governs a crypto trade also governs '
 'a Murabaha credit decision. Domain changes. Governance does not."',
 ST['Quote']
 ))

 E.append(PageBreak())

 # ═══════════════════════════════════════════════════════════════════════════
 # THE RECEIPT
 # ═══════════════════════════════════════════════════════════════════════════
 E.extend(section('The Governance Receipt: Your Proof of Accountability'))
 E.append(Paragraph(
 'Every decision processed by OMNIX generates a receipt. This receipt is the '
 'evidence that governance was applied. It is cryptographically signed, '
 'tamper-evident, and independently verifiable by anyone — '
 'regulators, auditors, counterparties, or clients.',
 ST['Body']
 ))
 E.append(Spacer(1, 0.08 * inch))

 receipt_lines = [
 ('{', WHITE),
 (' "receipt_id": "omnix-gov-20260401-a7f3c9",', CYAN),
 (' "timestamp": "2026-04-01T14:32:17.841Z",', GRAY),
 (' "decision": "APPROVED",', GREEN_OK),
 (' "checkpoints_passed": 11,', WHITE),
 (' "checkpoints_total": 11,', WHITE),
 (' "veto_count": 0,', WHITE),
 (' "governance_summary": "All checkpoints passed",', GRAY),
 (' "cryptographic_seal": {', WHITE),
 (' "algorithm": "PQC signature (OMNIX implementation)",', CYAN),
 (' "merkle_root": "a3f7c2d8e1b490fa231c...",', GRAY),
 (' "verification_url": "https://omnixquantum.net/verify/..."', GOLD),
 (' }', WHITE),
 ('}', WHITE),
 ]

 receipt_rows = [[Paragraph(
 line,
 ParagraphStyle('code', fontName='Courier', fontSize=8,
 textColor=color, leading=13, spaceAfter=0)
 )] for line, color in receipt_lines]

 receipt_t = Table(receipt_rows, colWidths=[7.1 * inch])
 receipt_t.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (-1, -1), HexColor('#060c16')),
 ('BOX', (0, 0), (-1, -1), 1, GOLD),
 ('TOPPADDING', (0, 0), (-1, -1), 3),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
 ('LEFTPADDING', (0, 0), (-1, -1), 14),
 ('RIGHTPADDING', (0, 0), (-1, -1), 14),
 ]))
 E.append(receipt_t)
 E.append(Spacer(1, 0.10 * inch))

 receipt_props = [
 [th('Field'), th('What It Proves')],
 [tdc('receipt_id'), td('Unique link to the complete decision audit record')],
 [tdc('decision'), td('The governance determination: APPROVED, BLOCKED, or HOLD')],
 [tdc('checkpoints_passed'), td('How many of the 11 checkpoints independently authorized the decision')],
 [tdc('cryptographic_seal'), td('Post-quantum signature — mathematically impossible to forge or alter after issuance')],
 [tdc('verification_url'), td('Public link — any third party can independently confirm this receipt at any time')],
 ]
 E.append(card(receipt_props, [2.0 * inch, 5.1 * inch]))

 E.append(PageBreak())

 # ═══════════════════════════════════════════════════════════════════════════
 # REGULATORY
 # ═══════════════════════════════════════════════════════════════════════════
 E.extend(section('Regulatory Protection Built In'))
 E.append(Paragraph(
 'Governance receipts are the evidence layer that regulators are beginning to '
 'require. OMNIX was designed with these frameworks as first-class requirements — '
 'not added as an afterthought.',
 ST['Body']
 ))
 E.append(Spacer(1, 0.08 * inch))

 reg_data = [
 [th('Framework'), th('Requirement'), th('OMNIX Coverage')],
 [tdgold('EU AI Act'),
 td('High-risk AI systems must maintain decision logs and enable human oversight.'),
 tdgreen('Every decision: immutable signed receipt + HOLD escalation for human review')],
 [tdgold('NIST AI RMF'),
 td('AI systems must be measurable, explainable, and subject to governance controls.'),
 tdgreen('11 checkpoints provide structured, measurable evaluation. Receipts enable explainability.')],
 [tdgold('ISO/IEC 42001'),
 td('AI management systems require documented risk controls and incident traceability.'),
 tdgreen('Fail-closed pipeline + public verification URL = full incident traceability')],
 [tdgold('AAOIFI (Islamic)'),
 td('Sharia-compliant products must adhere to riba and gharar prohibitions.'),
 tdgreen('CP-6 enforces Sharia principles as a pre-execution governance gate')],
 ]
 E.append(card(reg_data, [1.5 * inch, 2.8 * inch, 2.8 * inch]))

 E.append(PageBreak())

 # ═══════════════════════════════════════════════════════════════════════════
 # COMPETITIVE DIFFERENTIATION
 # ═══════════════════════════════════════════════════════════════════════════
 E.extend(section('Why Not Just Use What You Already Have?'))
 E.append(Paragraph(
 'Every organization already has some form of logging, monitoring, or compliance tooling. '
 'The question is not whether those tools exist — it is whether they provide '
 'pre-execution governance with cryptographic accountability. They do not.',
 ST['Body']
 ))
 E.append(Spacer(1, 0.10 * inch))

 diff_data = [
 [th('Alternative'), th('What It Does'), th("What's Missing"), th('OMNIX Difference')],
 [tdgold('Audit Logs'),
 td('Record what happened after execution has already occurred.'),
 tdred('Evidence created after the fact. Cannot prevent a bad decision.'),
 tdgreen('OMNIX governs BEFORE execution. The receipt proves authorization, not reconstruction.')],
 [tdgold('SIEM /\nMonitoring'),
 td('Alert teams to anomalies once they are detected.'),
 tdred('Cannot halt execution. Cannot produce signed proof of evaluation. Observation only.'),
 tdgreen('OMNIX halts. Fail-closed by design. No signed receipt = no execution. Ever.')],
 [tdgold('Compliance\nPlatforms'),
 td('Report policy adherence and flag violations after the fact.'),
 tdred('Policy check ≠ governance gate. No cryptographic seal. Cannot be independently verified.'),
 tdgreen('OMNIX enforces. Every decision carries a tamper-evident, publicly verifiable signed receipt.')],
 [tdgold('Custom Internal\nValidation'),
 td('Domain-specific code checks written by internal engineering teams.'),
 tdred('Non-standardized. No independent verification. Cannot audit externally. Breaks across domains.'),
 tdgreen('OMNIX is domain-agnostic infrastructure. Same pipeline, same receipt standard, across every vertical.')],
 [tdgold('Human Review\nCommittees'),
 td('Manual oversight for high-stakes decisions by designated reviewers.'),
 tdred('Does not scale. Inconsistent. No cryptographic record of what was reviewed and why.'),
 tdgreen('OMNIX escalates to human review only when the Coherence Engine detects contradiction (CP-4 HOLD).')],
 ]
 E.append(card(diff_data, [1.1 * inch, 1.6 * inch, 2.1 * inch, 2.3 * inch]))
 E.append(Spacer(1, 0.10 * inch))
 E.append(Paragraph(
 '"The difference between an audit trail and governance infrastructure is the same as '
 'the difference between a black box recorder and a pilot. '
 'One tells you what happened. The other determines whether it should happen at all."',
 ST['Quote']
 ))

 E.append(PageBreak())

 # ═══════════════════════════════════════════════════════════════════════════
 # PRICING
 # ═══════════════════════════════════════════════════════════════════════════
 E.extend(section('How to Start'))
 E.append(Paragraph(
 'OMNIX is designed to integrate without disrupting your existing systems. '
 'The Shadow Mode tier allows full governance evaluation in parallel with '
 'your current operations — zero risk, immediate visibility.',
 ST['Body']
 ))
 E.append(Spacer(1, 0.08 * inch))

 pricing_data = [
 [th('Tier'), th('How It Works'), th('Best For'), th('Investment')],
 [tdgold('Shadow Mode'),
 td('OMNIX runs in parallel. Evaluates every decision. No intervention. Full receipt generation.'),
 td('Organizations that want visibility before committing to full governance.'),
 tdgreen('Complimentary')],
 [tdgold('Advisory'),
 td('OMNIX results delivered as recommendations. Your team retains final decision authority.'),
 td('Regulated environments where human oversight is currently mandatory.'),
 td('$8,000 / month')],
 [tdgold('Enterprise'),
 td('Full integration. OMNIX receipt required before any automated decision executes. Fail-closed.'),
 td('Organizations with significant regulatory exposure or high-stakes automated operations.'),
 tdgold('$20,000 – $35,000\n/ month')],
 [tdgold('Custom'),
 td('Multi-domain deployment, private infrastructure, custom governance parameters, SLA guarantees.'),
 td('Financial institutions, government, and infrastructure operators at scale.'),
 tdc('Contact us')],
 ]
 E.append(card(pricing_data, [1.2 * inch, 2.4 * inch, 2.1 * inch, 1.4 * inch]))
 E.append(Spacer(1, 0.10 * inch))

 # ═══════════════════════════════════════════════════════════════════════════
 # TRACK RECORD
 # ═══════════════════════════════════════════════════════════════════════════
 E.append(PageBreak())
 E.extend(section('Operational Track Record'))
 E.append(Paragraph(
 'OMNIX has been in continuous production operation since July 2025, '
 'with the governance pipeline actively evaluating decisions across all four domains. '
 'The system has maintained 24/7 uptime with zero infrastructure failures.',
 ST['Body']
 ))
 E.append(Spacer(1, 0.06 * inch))
 E.append(Paragraph(
 '<i>Note: Digital asset trading operates with real capital on Kraken exchange. '
 'Islamic credit, insurance, and robotics domains operate in a controlled validation environment — '
 'governance logic is identical; domain-specific parameters are under calibration for production deployment.</i>',
 ParagraphStyle('note', fontName='Helvetica-Oblique', fontSize=8.5,
 textColor=GRAY, leading=13, leftIndent=6)
 ))
 E.append(Spacer(1, 0.08 * inch))

 track_data = [
 [th('Milestone'), th('Date'), th('Significance')],
 [tdgreen('Production deployment'), td('July 2025'), td('Live operation with real capital on Kraken exchange. Governance pipeline validated under live market conditions.')],
 [tdgreen('PQC implementation'), td('November 2025'), td('Post-quantum cryptographic signature deployed. All receipts carry NIST-standardized PQC signatures.')],
 [tdgreen('Multi-domain expansion'), td('March 2026'), td('Islamic credit, insurance, and robotics domains activated in validation environment. Same pipeline across all four sectors.')],
 [tdgreen('Track Record phase'), td('January 2026'), td('Recalibrated pipeline activated. Official governance performance measurement period begins.')],
 [tdgreen('Academic publications'), td('March 2026'), td('4 peer-indexed publications: SSRN abstract_id=6321298 (PQC architecture) and 6507559 (governance whitepaper); Zenodo DOI 10.5281/zenodo.19056919 and 10.5281/zenodo.19375792.')],
 [tdgreen(' Semifinalist'), td('2026'), td('Selected as Semifinalist for — competitive pan-GCC innovation program.')],
 ]
 E.append(card(track_data, [1.8 * inch, 1.1 * inch, 4.2 * inch]))

 E.append(PageBreak())

 # ═══════════════════════════════════════════════════════════════════════════
 # WHY NOW + FOUNDER
 # ═══════════════════════════════════════════════════════════════════════════
 E.extend(section('Why Now: The Regulatory Window Is Closing'))
 E.append(Paragraph(
 'For the first time, AI governance is not a recommendation — it is a legal mandate. '
 'Organizations that acquire governance infrastructure now will be compliant '
 'by default. Those that wait will face retrofit costs that dwarf the investment.',
 ST['Body']
 ))
 E.append(Spacer(1, 0.08 * inch))

 timing_data = [
 [th('Framework / Event'), th('Deadline / Status'), th('Implication for Automated Systems')],
 [tdgold('EU AI Act — High-Risk AI'),
 tdc('August 2026'),
 td('Mandatory audit trails, human oversight mechanisms, and explainability for all high-risk AI systems.')],
 [tdgold('NIST AI RMF'),
 tdc('Adopted — 2023'),
 td('De facto standard for US federal agencies and regulated industries. Measurability and governance controls required.')],
 [tdgold('UAE AI Governance Framework'),
 tdc('Active — 2025'),
 td('UAE mandates AI accountability standards across financial services, healthcare, and public sector.')],
 [tdgold('SEC / FCA / MAS Guidance'),
 tdc('Published — 2024–2025'),
 td('Financial regulators across US, UK, and Singapore have published AI governance expectations for trading and credit systems.')],
 [tdgold('ISO/IEC 42001'),
 tdc('Published — 2023'),
 td('International AI management system standard. Requires documented risk controls and incident traceability.')],
 ]
 E.append(card(timing_data, [1.9 * inch, 1.3 * inch, 3.9 * inch]))
 E.append(Spacer(1, 0.12 * inch))

 E.extend(section('The Founder'))
 E.append(Spacer(1, 0.06 * inch))

 founder_box = Table(
 [[Paragraph(
 '<b>Harold Nunes</b><br/>'
 '<font color="#C9A227">Solo Founder &amp; CEO — OMNIX</font><br/><br/>'
 'While building automated trading systems, Harold identified '
 'a gap that no existing product addressed: the absence of pre-execution governance '
 'with cryptographic accountability across any domain.<br/><br/>'
 'Rather than wait for someone else to build it, he built it himself — '
 'from architecture to production deployment, without a corporate engineering team.<br/><br/>'
 '<font color="#10b981">What he built:</font> An 11-checkpoint governance pipeline, '
 'post-quantum cryptographic signatures (NIST-standardized), multi-domain deployment across '
 'trading, Islamic credit, insurance, and robotics — and 4 peer-indexed academic publications '
 'documenting the architecture.<br/><br/>'
 '<font color="#06b6d4">"I couldn\'t find infrastructure that governed automated decisions '
 'with cryptographic accountability. So I built it."</font><br/><br/>'
 'Currently seeking: <b>$500K pre-seed · Strategic co-founder · First enterprise clients</b>',
 ParagraphStyle('founder', fontName='Helvetica', fontSize=9.5,
 textColor=WHITE, leading=16, alignment=TA_LEFT)
 )]],
 colWidths=[7.1 * inch]
 )
 founder_box.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
 ('BOX', (0, 0), (-1, -1), 2, GOLD),
 ('TOPPADDING', (0, 0), (-1, -1), 16),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
 ('LEFTPADDING', (0, 0), (-1, -1), 18),
 ('RIGHTPADDING', (0, 0), (-1, -1), 18),
 ]))
 E.append(founder_box)

 E.append(PageBreak())

 # ═══════════════════════════════════════════════════════════════════════════
 # CONTACT
 # ═══════════════════════════════════════════════════════════════════════════
 E.extend(section('Contact & Next Steps'))
 E.append(Spacer(1, 0.06 * inch))

 contact_box = Table(
 [[Paragraph(
 '<b>Harold Nunes</b><br/>'
 'Founder &amp; CEO — OMNIX<br/><br/>'
 '<font color="#06b6d4">contacto@omnixquantum.net</font><br/>'
 '<font color="#06b6d4">omnixquantum.net</font><br/>'
 'WhatsApp: +1 (650) 507-8293',
 ParagraphStyle('contact', fontName='Helvetica', fontSize=10.5,
 textColor=WHITE, leading=18, alignment=TA_LEFT)
 ),
 Paragraph(
 '<b>Three ways to move forward:</b><br/><br/>'
 '1. <font color="#10b981">Start with Shadow Mode</font> — '
 'free, no disruption, immediate governance visibility.<br/><br/>'
 '2. <font color="#C9A227">Schedule a technical demo</font> — '
 'see the pipeline evaluate a real decision live.<br/><br/>'
 '3. <font color="#06b6d4">Request the full technical specification</font> — '
 'available under NDA for institutional due diligence.',
 ParagraphStyle('next', fontName='Helvetica', fontSize=9.5,
 textColor=WHITE, leading=16, alignment=TA_LEFT)
 )]],
 colWidths=[3.1 * inch, 4.0 * inch]
 )
 contact_box.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
 ('BOX', (0, 0), (-1, -1), 2, GOLD),
 ('TOPPADDING', (0, 0), (-1, -1), 16),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
 ('LEFTPADDING', (0, 0), (-1, -1), 16),
 ('RIGHTPADDING', (0, 0), (-1, -1), 16),
 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
 ('LINEAFTER', (0, 0), (0, -1), 0.5, BORDER),
 ]))
 E.append(contact_box)
 E.append(Spacer(1, 0.14 * inch))

 cta = Table(
 [[Paragraph(
 'OMNIX is raising <b>$500,000 USD pre-seed</b> at a <b>$3,000,000 pre-money valuation</b>. '
 'For investor inquiries contact Harold Nunes directly.',
 ParagraphStyle('cta', fontName='Helvetica', fontSize=10, textColor=GOLD,
 leading=15, alignment=TA_CENTER)
 )]],
 colWidths=[7.1 * inch]
 )
 cta.setStyle(TableStyle([
 ('BACKGROUND', (0, 0), (-1, -1), HexColor('#1a150a')),
 ('BOX', (0, 0), (-1, -1), 1, GOLD),
 ('TOPPADDING', (0, 0), (-1, -1), 12),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
 ('LEFTPADDING', (0, 0), (-1, -1), 16),
 ('RIGHTPADDING', (0, 0), (-1, -1), 16),
 ]))
 E.append(cta)
 E.append(Spacer(1, 0.12 * inch))

 E.append(Paragraph(
 'This document is confidential and intended solely for the recipient. '
 'It does not constitute an offer to sell or a solicitation of any securities.',
 ST['SmallGray']
 ))

 doc.build(E, onFirstPage=dark_page, onLaterPages=dark_page)
 print(f'✅ Whitepaper generated: {OUTPUT}')


if __name__ == '__main__':
 build()
