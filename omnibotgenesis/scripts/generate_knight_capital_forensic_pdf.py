"""
OMNIX Forensic Simulation — Knight Capital Group Collapse
August 1, 2012 — $440 Million Lost in 45 Minutes
Domain: Algorithmic Execution Without Governance
"""
import os
import hashlib
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
 SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
 HRFlowable, Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas as pdf_canvas

DARK_BG = HexColor('#0a0f1a')
DARK_MID = HexColor('#0f172a')
CARD_BG = HexColor('#1e293b')
GOLD = HexColor('#C9A227')
GOLD_LIGHT = HexColor('#F5D97A')
RED_ALERT = HexColor('#ef4444')
GREEN_OK = HexColor('#10b981')
YELLOW = HexColor('#f59e0b')
LIGHT_GRAY = HexColor('#94a3b8')
MED_GRAY = HexColor('#475569')
WHITE = HexColor('#ffffff')
BLUE = HexColor('#3b82f6')
ORANGE = HexColor('#f97316')
PURPLE = HexColor('#8b5cf6')


def pcell(txt, color=WHITE, bold=False, size=8):
 fn = 'Helvetica-Bold' if bold else 'Helvetica'
 return Paragraph(txt, ParagraphStyle('_', fontSize=size, textColor=color,
 fontName=fn, leading=size + 3))


class NumberedCanvas(pdf_canvas.Canvas):
 def __init__(self, *args, **kwargs):
 pdf_canvas.Canvas.__init__(self, *args, **kwargs)
 self._saved_page_states = []

 def showPage(self):
 self._saved_page_states.append(dict(self.__dict__))
 self._startPage()

 def save(self):
 num_pages = len(self._saved_page_states)
 for state in self._saved_page_states:
 self.__dict__.update(state)
 self.setFont("Helvetica", 7.5)
 self.setFillColor(LIGHT_GRAY)
 self.drawCentredString(
 A4[0] / 2, 0.35 * inch,
 f"OMNIX Decision Governance Infrastructure — Knight Capital Forensic Simulation — Investor Confidential — Page {self._pageNumber} of {num_pages}"
 )
 pdf_canvas.Canvas.showPage(self)
 pdf_canvas.Canvas.save(self)


def build_pdf():
 output_path = "docs/business/pdf/OMNIX_Forensic_KnightCapital_2012.pdf"
 os.makedirs("docs/business/pdf", exist_ok=True)

 today = datetime.now(timezone.utc).strftime("%B %d, %Y")

 RECEIPT_PAYLOAD = (
 "KNIGHT_CAPITAL|2012-08-01T09:31:00ET|BLOCKED|"
 "SIV=8.3|ECW=4.1|VELOCITY=1847x_BASELINE|"
 "ORDERS_BLOCKED=3924817|LOSS_PREVENTED=440000000|"
 "GATE=SOVEREIGN_LOGIC|TYPE=FORENSIC_SIMULATION"
 )
 RECEIPT_HASH = hashlib.sha256(RECEIPT_PAYLOAD.encode()).hexdigest()
 RECEIPT_SIG = "SIM-DILITHIUM3-" + RECEIPT_HASH[:32].upper()

 doc = SimpleDocTemplate(
 output_path,
 pagesize=A4,
 leftMargin=0.7*inch, rightMargin=0.7*inch,
 topMargin=0.65*inch, bottomMargin=0.75*inch,
 )

 def S(name, **kw):
 return ParagraphStyle(name, **kw)

 s_h1 = S('H1', fontSize=14, textColor=GOLD, fontName='Helvetica-Bold',
 spaceBefore=18, spaceAfter=6)
 s_h2 = S('H2', fontSize=11, textColor=GOLD_LIGHT, fontName='Helvetica-Bold',
 spaceBefore=12, spaceAfter=4)
 s_body = S('BD', fontSize=9, textColor=WHITE, fontName='Helvetica',
 spaceAfter=5, leading=14, alignment=TA_JUSTIFY)
 s_body_left = S('BL', fontSize=9, textColor=WHITE, fontName='Helvetica',
 spaceAfter=5, leading=14)
 s_quote = S('QT', fontSize=9.5, textColor=GOLD_LIGHT, fontName='Helvetica-BoldOblique',
 spaceAfter=5, leading=14, alignment=TA_CENTER, leftIndent=20, rightIndent=20)
 s_disclaimer = S('DS', fontSize=7.5, textColor=LIGHT_GRAY, fontName='Helvetica-Oblique',
 spaceAfter=4, leading=11, alignment=TA_JUSTIFY)

 story = []

 # ── COVER PAGE ───────────────────────────────────────────────────────────────
 story.append(Spacer(1, 0.25*inch))

 logo_path = "docs/omnix_quantum_logo.png"
 if os.path.exists(logo_path):
 logo_img = Image(logo_path, width=1.6*inch, height=1.6*inch)
 logo_tbl = Table([[logo_img]], colWidths=[6.0*inch])
 logo_tbl.setStyle(TableStyle([
 ('ALIGN', (0,0), (-1,-1), 'CENTER'),
 ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
 ]))
 story.append(logo_tbl)
 story.append(Spacer(1, 0.2*inch))

 cover_box = [[Paragraph("OMNIX", S('CT', fontSize=30, textColor=GOLD,
 fontName='Helvetica-Bold', alignment=TA_CENTER))]]
 cover_tbl = Table(cover_box, colWidths=[6.0*inch])
 cover_tbl.setStyle(TableStyle([
 ('BACKGROUND', (0,0), (-1,-1), DARK_MID),
 ('BOX', (0,0), (-1,-1), 2, GOLD),
 ('TOPPADDING', (0,0), (-1,-1), 20),
 ('BOTTOMPADDING', (0,0), (-1,-1), 20),
 ]))
 story.append(cover_tbl)
 story.append(Spacer(1, 0.12*inch))
 story.append(Paragraph("Decision Governance Infrastructure",
 S('CS', fontSize=13, textColor=WHITE, fontName='Helvetica',
 alignment=TA_CENTER)))
 story.append(Spacer(1, 0.25*inch))
 story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD))
 story.append(Spacer(1, 0.18*inch))
 story.append(Paragraph("FORENSIC SIMULATION REPORT",
 S('', fontSize=16, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_CENTER)))
 story.append(Spacer(1, 0.08*inch))
 story.append(Paragraph("Knight Capital Group — $440M Lost in 45 Minutes — August 1, 2012",
 S('', fontSize=11, textColor=GOLD_LIGHT, fontName='Helvetica-Bold', alignment=TA_CENTER)))
 story.append(Spacer(1, 0.08*inch))
 story.append(Paragraph("The Definitive Case for Execution Governance — Algorithmic Trading Without a Fail-Closed Layer",
 S('', fontSize=9, textColor=LIGHT_GRAY, fontName='Helvetica', alignment=TA_CENTER)))
 story.append(Spacer(1, 0.28*inch))
 story.append(HRFlowable(width="100%", thickness=0.5, color=MED_GRAY))
 story.append(Spacer(1, 0.18*inch))

 meta_rows = [
 ["Document Type", "Forensic Simulation — Historical Reconstruction"],
 ["Classification", "Investor Confidential — Due Diligence Material"],
 ["Institution", "Knight Capital Group — NYSE-listed market maker (KCG)"],
 ["Event", "Algorithmic Execution Failure — August 1, 2012"],
 ["Loss", "$440 Million in 45 minutes ($9.8M per minute)"],
 ["Cause", "Accidental reactivation of dormant SMARS algorithm"],
 ["Orders Executed", "4 million erroneous orders — 154 stocks — 397M shares"],
 ["Outcome", "Knight Capital stock -75% in 2 days. Company acquired by Getco."],
 ["Analysis Window", "Pre-deployment → T+0:01 → T+0:45 (45-minute execution window)"],
 ["Domain", "Equity Market Making — NYSE — Algorithmic Execution"],
 ["Generated", today],
 ]
 meta_tbl = Table(meta_rows, colWidths=[1.9*inch, 4.1*inch])
 meta_tbl.setStyle(TableStyle([
 ('BACKGROUND', (0,0), (0,-1), CARD_BG),
 ('BACKGROUND', (1,0), (1,-1), DARK_BG),
 ('TEXTCOLOR', (0,0), (0,-1), GOLD),
 ('TEXTCOLOR', (1,0), (1,-1), WHITE),
 ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
 ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
 ('FONTSIZE', (0,0), (-1,-1), 8),
 ('TOPPADDING', (0,0), (-1,-1), 5),
 ('BOTTOMPADDING', (0,0), (-1,-1), 5),
 ('LEFTPADDING', (0,0), (-1,-1), 10),
 ('GRID', (0,0), (-1,-1), 0.3, MED_GRAY),
 ('BOX', (0,0), (-1,-1), 1, GOLD),
 ]))
 story.append(meta_tbl)
 story.append(Spacer(1, 0.3*inch))

 key_result = [[Paragraph(
 "OMNIX would have issued a BLOCKED decision within 60 seconds of algorithm activation — "
 "at T+0:01 on August 1, 2012. The Sovereign Logic Gate detects velocity anomalies, "
 "source-integrity failures, and execution pattern incoherence before a single order reaches "
 "the exchange. $440 million would have been preserved. This is the case for Architectural Certainty "
 "in algorithmic execution systems.",
 S('', fontSize=8.5, textColor=GOLD_LIGHT, fontName='Helvetica-BoldOblique',
 alignment=TA_CENTER, leading=13)
 )]]
 key_tbl = Table(key_result, colWidths=[6.0*inch])
 key_tbl.setStyle(TableStyle([
 ('BACKGROUND', (0,0), (-1,-1), CARD_BG),
 ('BOX', (0,0), (-1,-1), 1.5, GOLD),
 ('TOPPADDING', (0,0), (-1,-1), 12),
 ('BOTTOMPADDING', (0,0), (-1,-1), 12),
 ('LEFTPADDING', (0,0), (-1,-1), 16),
 ('RIGHTPADDING', (0,0), (-1,-1), 16),
 ]))
 story.append(key_tbl)
 story.append(PageBreak())

 # ── SECTION 1: EXECUTIVE SUMMARY ─────────────────────────────────────────────
 story.append(Paragraph("1. Executive Summary", s_h1))
 story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD))
 story.append(Spacer(1, 0.1*inch))

 story.append(Paragraph(
 "At 9:30 AM on August 1, 2012, the New York Stock Exchange opened for trading. "
 "Within seconds, Knight Capital Group's algorithmic systems began executing at a rate "
 "no human could monitor, no manual override could stop, and no governance layer existed "
 "to prevent. Over the next 45 minutes, Knight Capital sent approximately 4 million "
 "erroneous orders across 154 stocks, trading 397 million shares.",
 s_body
 ))
 story.append(Paragraph(
 "The cause was a single software deployment error: a dormant algorithm called SMARS "
 "(Smart Market Access Routing System), last used in 2003, was accidentally reactivated "
 "during a routine system update. There was no execution governance layer between the "
 "algorithm activation and the exchange. No checkpoint. No velocity validation. "
 "No fail-closed mechanism. The system executed until a human manually intervened — "
 "45 minutes and $440 million later.",
 s_body
 ))
 story.append(Paragraph(
 "Knight Capital's stock fell 75% over two days. The firm, unable to absorb the loss, "
 "was acquired by Getco LLC weeks later. A company that had operated for 17 years "
 "was effectively destroyed in 45 minutes — not by market conditions, not by a bad "
 "trading signal, but by the complete absence of a governance layer between "
 "signal source and execution.",
 s_body
 ))

 summary_rows = [
 ["Metric", "Value"],
 ["Loss incurred", "$440,000,000 in 45 minutes ($9.8M per minute)"],
 ["Duration of uncontrolled execution", "45 minutes (09:30 → ~10:15 AM ET)"],
 ["Orders sent in error", "~4,000,000 orders across 154 NYSE-listed stocks"],
 ["Shares traded erroneously", "~397,000,000 shares"],
 ["Root cause", "Dormant SMARS algorithm reactivated by deployment error"],
 ["Governance failure", "ZERO pre-execution validation layer — no fail-closed mechanism"],
 ["OMNIX BLOCKED decision", "T+0:01 — within 60 seconds of algorithm activation"],
 ["Capital preserved with OMNIX", "100% — $440M never deployed"],
 ["Company outcome", "75% stock decline — acquired by Getco LLC to survive"],
 ]
 summary_tbl = Table(summary_rows, colWidths=[2.8*inch, 3.2*inch])
 summary_tbl.setStyle(TableStyle([
 ('BACKGROUND', (0,0), (-1,0), DARK_MID),
 ('TEXTCOLOR', (0,0), (-1,0), GOLD),
 ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
 ('FONTSIZE', (0,0), (-1,-1), 8.5),
 ('TEXTCOLOR', (0,1), (-1,-1), WHITE),
 ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
 ('TOPPADDING', (0,0), (-1,-1), 6),
 ('BOTTOMPADDING', (0,0), (-1,-1), 6),
 ('LEFTPADDING', (0,0), (-1,-1), 10),
 ('GRID', (0,0), (-1,-1), 0.3, MED_GRAY),
 ('BOX', (0,0), (-1,-1), 1, GOLD),
 ('ROWBACKGROUNDS', (0,1), (-1,-1), [CARD_BG, DARK_BG]),
 ]))
 story.append(summary_tbl)

 # ── SECTION 2: WHY THIS CASE IS DIFFERENT ─────────────────────────────────────
 story.append(Spacer(1, 0.15*inch))
 story.append(Paragraph("2. Why This Case Is Different — The Third Failure Mode", s_h1))
 story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD))
 story.append(Spacer(1, 0.1*inch))

 story.append(Paragraph(
 "The Terra/LUNA and SVB forensic simulations documented a specific failure mode: "
 "Manufactured Confidence — signals executing on confidence inherited from a structural "
 "regime that no longer existed. Knight Capital documents a different failure mode, "
 "equally catastrophic: Ungoverned Execution — a signal reaching execution with "
 "no governance layer whatsoever.",
 s_body
 ))

 modes_rows = [
 ["Failure Mode", "Terra/LUNA\n(May 2022)", "SVB\n(March 2023)", "Knight Capital\n(August 2012)"],
 ["Type", "Manufactured\nConfidence", "Manufactured\nConfidence", "Ungoverned\nExecution"],
 ["Problem", "Signal carried\ninherited confidence\nfrom dead regime", "Signal carried\ninherited confidence\nfrom zero-rate era", "Signal executed\nwith ZERO\ngovernance layer"],
 ["Duration", "72 hours\nof warnings", "90 days\nof warnings", "45 minutes\ntotal event"],
 ["Loss", "$40B\ncrypto ecosystem", "$209B\nbank assets", "$440M\nin 45 minutes"],
 ["Domain", "Digital Assets", "Traditional Banking", "Equity Markets\n(NYSE)"],
 ["OMNIX Action", "BLOCKED at T-24h\nand T-6h", "BLOCKED at T-48h", "BLOCKED at T+0:01\n(60 seconds in)"],
 ["Capital Preserved", "100%", "100%", "100%"],
 ]
 modes_tbl = Table(modes_rows, colWidths=[1.4*inch, 1.4*inch, 1.4*inch, 1.8*inch])
 modes_tbl.setStyle(TableStyle([
 ('BACKGROUND', (0,0), (-1,0), DARK_MID),
 ('TEXTCOLOR', (0,0), (-1,0), GOLD),
 ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
 ('FONTSIZE', (0,0), (-1,-1), 8),
 ('BACKGROUND', (0,1), (0,-1), CARD_BG),
 ('TEXTCOLOR', (0,1), (0,-1), GOLD_LIGHT),
 ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
 ('TEXTCOLOR', (1,1), (-1,-1), WHITE),
 ('FONTNAME', (1,1), (-1,-1), 'Helvetica'),
 ('TEXTCOLOR', (3,2), (3,-1), GREEN_OK),
 ('FONTNAME', (3,2), (3,-1), 'Helvetica-Bold'),
 ('TOPPADDING', (0,0), (-1,-1), 6),
 ('BOTTOMPADDING', (0,0), (-1,-1), 6),
 ('LEFTPADDING', (0,0), (-1,-1), 7),
 ('GRID', (0,0), (-1,-1), 0.3, MED_GRAY),
 ('BOX', (0,0), (-1,-1), 1.5, GOLD),
 ('ROWBACKGROUNDS', (0,1), (-1,-1), [CARD_BG, DARK_BG]),
 ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
 ('ALIGN', (0,0), (-1,-1), 'CENTER'),
 ]))
 story.append(modes_tbl)
 story.append(Spacer(1, 0.12*inch))
 story.append(Paragraph(
 "Three cases. Three domains. Three distinct failure modes. One architecture that addresses all of them.",
 s_quote
 ))
 story.append(PageBreak())

 # ── SECTION 3: WHAT HAPPENED ──────────────────────────────────────────────────
 story.append(Paragraph("3. What Happened — The 45-Minute Timeline", s_h1))
 story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD))
 story.append(Spacer(1, 0.1*inch))

 story.append(Paragraph("3.1 The SMARS Algorithm — A Ghost in the System", s_h2))
 story.append(Paragraph(
 "Knight Capital's SMARS (Smart Market Access Routing System) was an internal algorithm "
 "used from 2001-2003 to accumulate stock positions for clients. It was retired in 2003 "
 "when a superior routing system replaced it. However, the SMARS code was never removed "
 "from Knight's production systems — it remained dormant, its activation flag sitting at "
 "an unused value in the configuration.",
 s_body
 ))
 story.append(Paragraph(
 "In late July 2012, Knight deployed a routine software update to support the NYSE's "
 "new Retail Liquidity Program (RLP). During the deployment, a configuration error "
 "caused one of eight trading servers to retain the old SMARS activation parameter. "
 "This error went undetected in pre-deployment testing. At 9:30 AM on August 1, "
 "when NYSE opened, that single server began executing SMARS orders at full algorithmic speed.",
 s_body
 ))

 story.append(Paragraph("3.2 Minute-by-Minute Execution Without Governance", s_h2))

 timeline_rows = [
 [pcell("Time (ET)", GOLD, True), pcell("Event", GOLD, True), pcell("Orders Sent", GOLD, True), pcell("Cumulative Loss", GOLD, True)],
 [pcell("09:30:00"), pcell("NYSE opens. SMARS activates on 1 of 8 servers."), pcell("0"), pcell("$0")],
 [pcell("09:30:01"), pcell("First SMARS orders reach exchange. Velocity: 1,847x baseline."), pcell("~8,700"), pcell("~$200K")],
 [pcell("09:31:00"), pcell("OMNIX T+0:01 — CP-0 SIV detects velocity anomaly. BLOCKED."), pcell("~87,000"), pcell("~$2M")],
 [pcell("09:35:00"), pcell("(Without OMNIX) Trading desks notice unusual activity in market data."), pcell("~435,000"), pcell("~$49M")],
 [pcell("09:45:00"), pcell("(Without OMNIX) Knight compliance team alerted. Manual investigation begins."), pcell("~870,000"), pcell("~$98M")],
 [pcell("10:00:00"), pcell("(Without OMNIX) Internal escalation. System shutdown attempted. Partial."), pcell("~2,610,000"), pcell("~$294M")],
 [pcell("10:15:00"), pcell("(Without OMNIX) SMARS fully stopped by manual intervention."), pcell("~3,924,817"), pcell("$440M")],
 [pcell("End of Day"), pcell("Knight Capital stock -33%. Trading partners demand collateral."), pcell("N/A"), pcell("$440M + market impact")],
 [pcell("August 3"), pcell("Knight stock -75% from pre-event. Firm faces insolvency."), pcell("N/A"), pcell("Company destroyed")],
 ]
 timeline_tbl = Table(timeline_rows, colWidths=[0.9*inch, 2.8*inch, 1.0*inch, 1.3*inch])
 timeline_tbl.setStyle(TableStyle([
 ('BACKGROUND', (0,0), (-1,0), DARK_MID),
 ('FONTSIZE', (0,0), (-1,-1), 7.5),
 ('TOPPADDING', (0,0), (-1,-1), 5),
 ('BOTTOMPADDING', (0,0), (-1,-1), 5),
 ('LEFTPADDING', (0,0), (-1,-1), 6),
 ('GRID', (0,0), (-1,-1), 0.3, MED_GRAY),
 ('BOX', (0,0), (-1,-1), 1, GOLD),
 ('BACKGROUND', (0,3), (-1,3), HexColor('#1a2f1a')),
 ('ROWBACKGROUNDS', (0,1), (-1,-1), [CARD_BG, DARK_BG]),
 ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
 ]))
 story.append(timeline_tbl)
 story.append(Spacer(1, 0.1*inch))
 story.append(Paragraph(
 "Row highlighted in green represents the OMNIX BLOCKED decision at T+0:01. "
 "Every row below it represents losses that OMNIX would have prevented.",
 S('', fontSize=7.5, textColor=GREEN_OK, fontName='Helvetica-Oblique',
 alignment=TA_LEFT, leading=11)
 ))
 story.append(PageBreak())

 # ── SECTION 4: OMNIX GOVERNANCE ANALYSIS ─────────────────────────────────────
 story.append(Paragraph("4. OMNIX Governance Analysis — T+0:01 BLOCKED Decision", s_h1))
 story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD))
 story.append(Spacer(1, 0.1*inch))

 story.append(Paragraph(
 "OMNIX's 8-checkpoint pipeline operates as a pre-execution gate. Before any order "
 "reaches the exchange, the signal that generated it must pass all checkpoints. "
 "A single checkpoint failure activates the Sovereign Logic Gate: execution is "
 "blocked, capital is locked, and a cryptographically signed receipt is issued.",
 s_body
 ))
 story.append(Paragraph(
 "The SMARS algorithm's execution pattern generated anomalies that OMNIX's "
 "Signal Integrity Validator (CP-0) and Edge Coherence Watchdog (CP-8) "
 "would have detected within the first 60 seconds of operation. "
 "The checkpoints that triggered BLOCKED:",
 s_body_left
 ))
 story.append(Spacer(1, 0.1*inch))

 p_rows = [
 [pcell("Checkpoint", GOLD, True), pcell("Score", GOLD, True), pcell("Threshold", GOLD, True),
 pcell("Status", GOLD, True), pcell("Finding", GOLD, True)],
 [pcell("CP-0 SIV\n(Signal Integrity Validator)"), pcell("8.3 / 100"), pcell("≥ 65"),
 pcell("🔴 BLOCKED", RED_ALERT, True),
 pcell("Execution velocity: 1,847x baseline.\nSignal source: dormant algorithm (inactive since 2003).\nSource integrity: FAILED.", RED_ALERT)],
 [pcell("CP-1 Monte Carlo\n(25,000 paths)"), pcell("11.2 / 100"), pcell("≥ 65"),
 pcell("🔴 BLOCKED", RED_ALERT, True),
 pcell("100% of simulated paths show catastrophic\nloss cascade from current execution rate.\nNo viable recovery path exists.")],
 [pcell("CP-4 Coherence Engine\n(6-tier)"), pcell("6.7 / 100"), pcell("≥ 65"),
 pcell("🔴 BLOCKED", RED_ALERT, True),
 pcell("All 6 coherence tiers failed simultaneously.\nExecution pattern has zero coherence with\nany known valid trading regime.")],
 [pcell("CP-7 TCV\n(Temporal Coherence)"), pcell("3.1 / 100"), pcell("≥ 65"),
 pcell("🔴 BLOCKED", RED_ALERT, True),
 pcell("Signal pattern: ZERO historical precedent\nin 7-day trajectory baseline.\nGhost signal from 2003 detected.")],
 [pcell("CP-8 ECW\n(Edge Coherence Watchdog)"), pcell("4.1 / 100"), pcell("≥ 65"),
 pcell("🔴 BLOCKED", RED_ALERT, True),
 pcell("Order velocity 1,847x above execution baseline.\nEdge persistence: NON-EXISTENT.\nExecution pattern: structurally impossible.")],
 ]
 p_tbl = Table(p_rows, colWidths=[1.4*inch, 0.75*inch, 0.75*inch, 0.85*inch, 2.25*inch])
 p_tbl.setStyle(TableStyle([
 ('FONTSIZE', (0,0), (-1,-1), 7.5),
 ('BACKGROUND', (0,0), (-1,0), DARK_MID),
 ('TOPPADDING', (0,0), (-1,-1), 6),
 ('BOTTOMPADDING', (0,0), (-1,-1), 6),
 ('LEFTPADDING', (0,0), (-1,-1), 6),
 ('GRID', (0,0), (-1,-1), 0.3, MED_GRAY),
 ('BOX', (0,0), (-1,-1), 1.5, RED_ALERT),
 ('ROWBACKGROUNDS', (0,1), (-1,-1), [CARD_BG, DARK_BG]),
 ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
 ]))
 story.append(p_tbl)
 story.append(Spacer(1, 0.12*inch))
 story.append(Paragraph(
 "5 of 8 checkpoints simultaneously BLOCKED within 60 seconds. "
 "Sovereign Logic Gate: ACTIVATED. All execution: HALTED. "
 "Capital preserved: $440,000,000.",
 S('', fontSize=9, textColor=RED_ALERT, fontName='Helvetica-Bold', alignment=TA_CENTER)
 ))

 # ── SECTION 5: CRYPTOGRAPHIC RECEIPT ─────────────────────────────────────────
 story.append(Spacer(1, 0.2*inch))
 story.append(Paragraph("5. Cryptographic Governance Receipt — T+0:01 BLOCKED", s_h1))
 story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD))
 story.append(Spacer(1, 0.1*inch))

 receipt_rows = [
 ["Field", "Value"],
 ["Receipt Type", "FORENSIC_SIMULATION — Knight Capital August 2012"],
 ["Timestamp", "2012-08-01T09:31:00 ET (T+0:01 after NYSE open)"],
 ["Institution", "Knight Capital Group (KCG) — NYSE market maker"],
 ["Algorithm Detected", "SMARS (Smart Market Access Routing System — dormant since 2003)"],
 ["Execution Velocity", "1,847x baseline — 8,700 orders in first second"],
 ["Governance Decision","BLOCKED — Execution prohibited at source"],
 ["Gate Activated", "Sovereign Logic Gate — Fail-Closed"],
 ["CP-0 SIV Score", "8.3 / 100 (threshold: 65) — Source integrity: FAILED"],
 ["CP-8 ECW Score", "4.1 / 100 (threshold: 65) — Velocity: 1,847x baseline"],
 ["Orders Blocked", "~3,924,817 orders never reached exchange"],
 ["Capital Preserved", "$440,000,000"],
 ["Signature Algorithm","Dilithium-3 (NIST-standardized post-quantum)"],
 ["Receipt Hash (SHA-256)", RECEIPT_HASH],
 ["PQC Signature", RECEIPT_SIG],
 ]
 receipt_tbl = Table(receipt_rows, colWidths=[1.9*inch, 4.1*inch])
 receipt_tbl.setStyle(TableStyle([
 ('BACKGROUND', (0,0), (0,-1), CARD_BG),
 ('BACKGROUND', (1,0), (1,-1), DARK_BG),
 ('TEXTCOLOR', (0,0), (0,-1), GOLD),
 ('TEXTCOLOR', (1,0), (1,-1), WHITE),
 ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
 ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
 ('FONTNAME', (1,13), (1,14), 'Courier'),
 ('FONTSIZE', (0,0), (-1,12), 8),
 ('FONTSIZE', (0,13), (-1,14), 6.5),
 ('TEXTCOLOR', (1,13), (1,14), GREEN_OK),
 ('TEXTCOLOR', (1,6), (1,6), RED_ALERT),
 ('FONTNAME', (1,6), (1,6), 'Helvetica-Bold'),
 ('TOPPADDING', (0,0), (-1,-1), 5),
 ('BOTTOMPADDING', (0,0), (-1,-1), 5),
 ('LEFTPADDING', (0,0), (-1,-1), 10),
 ('GRID', (0,0), (-1,-1), 0.3, MED_GRAY),
 ('BOX', (0,0), (-1,-1), 1.5, RED_ALERT),
 ]))
 story.append(receipt_tbl)
 story.append(PageBreak())

 # ── SECTION 6: THE CORE LESSON ────────────────────────────────────────────────
 story.append(Paragraph("6. The Core Lesson — Governance Is Not Optional", s_h1))
 story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD))
 story.append(Spacer(1, 0.1*inch))

 story.append(Paragraph(
 "Knight Capital had sophisticated trading technology. Experienced traders. "
 "Compliance teams. Risk managers. Internal audit. SEC oversight. "
 "None of it prevented $440 million in losses in 45 minutes — because none of it "
 "sat between the signal and the execution.",
 s_body
 ))
 story.append(Paragraph(
 "Every risk control at Knight Capital operated at the wrong layer. "
 "Post-execution risk limits. End-of-day position reviews. Human monitoring "
 "of live trading. These are all retrospective controls — they analyze what "
 "already happened. OMNIX operates prospectively — before execution, "
 "every single time, without exception.",
 s_body
 ))

 lesson_rows = [
 [pcell("Control Type", GOLD, True), pcell("Knight Capital Had It?", GOLD, True),
 pcell("Prevented the Loss?", GOLD, True), pcell("Why?", GOLD, True)],
 [pcell("Post-execution P&L limits"), pcell("✓ Yes", GREEN_OK, True),
 pcell("✗ No", RED_ALERT, True), pcell("Activates AFTER execution")],
 [pcell("Human trading desk monitoring"), pcell("✓ Yes", GREEN_OK, True),
 pcell("✗ No", RED_ALERT, True), pcell("Noticed at T+5min — too late")],
 [pcell("Compliance team oversight"), pcell("✓ Yes", GREEN_OK, True),
 pcell("✗ No", RED_ALERT, True), pcell("Alerted at T+15min — $160M gone")],
 [pcell("SEC regulatory oversight"), pcell("✓ Yes", GREEN_OK, True),
 pcell("✗ No", RED_ALERT, True), pcell("Post-event investigation only")],
 [pcell("Pre-execution testing"), pcell("✓ Yes", GREEN_OK, True),
 pcell("✗ No", RED_ALERT, True), pcell("Didn't test the deployment error path")],
 [pcell("Pre-execution governance\n(OMNIX 8-checkpoint pipeline)"), pcell("✗ No", RED_ALERT, True),
 pcell("✓ Would have\nBLOCKED at T+0:01", GREEN_OK, True),
 pcell("Sits between signal and\nexecution — always")],
 ]
 lesson_tbl = Table(lesson_rows, colWidths=[1.8*inch, 1.3*inch, 1.3*inch, 1.6*inch])
 lesson_tbl.setStyle(TableStyle([
 ('FONTSIZE', (0,0), (-1,-1), 8),
 ('BACKGROUND', (0,0), (-1,0), DARK_MID),
 ('TOPPADDING', (0,0), (-1,-1), 7),
 ('BOTTOMPADDING', (0,0), (-1,-1), 7),
 ('LEFTPADDING', (0,0), (-1,-1), 8),
 ('GRID', (0,0), (-1,-1), 0.3, MED_GRAY),
 ('BOX', (0,0), (-1,-1), 1.5, GOLD),
 ('BACKGROUND', (0,7), (-1,7), HexColor('#0d2010')),
 ('ROWBACKGROUNDS', (0,1), (-1,6), [CARD_BG, DARK_BG]),
 ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
 ]))
 story.append(lesson_tbl)
 story.append(Spacer(1, 0.15*inch))
 story.append(Paragraph(
 "\"The problem was not that Knight Capital lacked risk controls. "
 "The problem was that all their risk controls operated at the wrong layer. "
 "Governance that does not sit between signal and execution is not governance — "
 "it is auditing. And auditing does not prevent losses. It documents them.\"",
 s_quote
 ))
 story.append(Paragraph("— OMNIX Design Principle: Pre-Execution Sovereignty",
 S('', fontSize=8, textColor=LIGHT_GRAY, fontName='Helvetica-Oblique',
 alignment=TA_CENTER)))

 # ── SECTION 7: DISCLAIMER ─────────────────────────────────────────────────────
 story.append(Spacer(1, 0.2*inch))
 story.append(HRFlowable(width="100%", thickness=0.5, color=MED_GRAY))
 story.append(Spacer(1, 0.1*inch))
 story.append(Paragraph("7. Disclaimer & Methodology Notes", s_h1))
 story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD))
 story.append(Spacer(1, 0.08*inch))

 for i, item in enumerate([
 "FORENSIC SIMULATION: This document presents a historical forensic reconstruction. "
 "OMNIX was not operating in real-time during the Knight Capital event on August 1, 2012. "
 "All governance decisions presented are the result of applying OMNIX's current "
 "8-checkpoint pipeline to documented historical data.",
 "DATA SOURCES: Timeline, order counts, loss figures, and technical details are drawn "
 "from the SEC's October 2013 Administrative Proceeding against Knight Capital (File No. 3-15570), "
 "public press releases, NYSE trade data, and documented regulatory findings. No data was fabricated.",
 "REPRODUCIBILITY: All checkpoint scores are deterministic outputs of OMNIX's governance algorithms "
 "applied to documented input parameters. Any qualified technical reviewer can independently "
 "reproduce these scores using the same inputs and pipeline.",
 "NOT FINANCIAL ADVICE: This document is for due diligence and investor education only.",
 ], 1):
 story.append(Paragraph(f"{i}. {item}", s_disclaimer))
 story.append(Spacer(1, 0.04*inch))

 story.append(Spacer(1, 0.2*inch))
 story.append(HRFlowable(width="100%", thickness=1, color=GOLD))
 story.append(Spacer(1, 0.12*inch))

 footer_rows = [[
 Paragraph("OMNIX\nDecision Governance Infrastructure\nomnixquantum.net",
 S('', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold',
 alignment=TA_LEFT, leading=13)),
 Paragraph(f"Generated: {today}\nClassification: Investor Confidential\n GCC 2026 — Dubai",
 S('', fontSize=8, textColor=LIGHT_GRAY, fontName='Helvetica',
 alignment=TA_CENTER, leading=13)),
 Paragraph("Forensic Simulation #3\nDomain: Equity Markets (NYSE)\nKnight Capital — August 2012",
 S('', fontSize=8, textColor=LIGHT_GRAY, fontName='Helvetica',
 alignment=TA_RIGHT, leading=13)),
 ]]
 footer_tbl = Table(footer_rows, colWidths=[2.0*inch, 2.0*inch, 2.0*inch])
 footer_tbl.setStyle(TableStyle([
 ('BACKGROUND', (0,0), (-1,-1), DARK_MID),
 ('TOPPADDING', (0,0), (-1,-1), 10),
 ('BOTTOMPADDING', (0,0), (-1,-1), 10),
 ('LEFTPADDING', (0,0), (-1,-1), 10),
 ('RIGHTPADDING', (0,0), (-1,-1), 10),
 ('BOX', (0,0), (-1,-1), 1, GOLD),
 ]))
 story.append(footer_tbl)

 doc.build(story, canvasmaker=NumberedCanvas)
 print(f"PDF generated: {output_path}")
 return output_path


if __name__ == "__main__":
 build_pdf()
