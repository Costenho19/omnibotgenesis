#!/usr/bin/env python3
"""
OMNIX Investor Pitch Deck PDF Generator — March 2026
Professional 12-slide pitch deck for general investor presentations.
"""
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "business", "pdfs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_DIR = os.path.join(
    os.path.expanduser("~"),
    "workspace/.pythonlibs/lib/python3.11/site-packages/kaleido/executable/xdg/fonts/truetype/dejavu"
)
FONT_REGULAR  = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD     = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
LOGO_PATH     = os.path.join(BASE_DIR, "assets", "omnix_logo.png")

DARK      = (15, 15, 15)
ACCENT    = (20, 20, 20)
ACCENT2   = (201, 168, 55)
GOLD      = (201, 168, 55)
MID_GRAY  = (140, 140, 140)
LIGHT_BG  = (245, 240, 218)
WHITE     = (255, 255, 255)
GREEN     = (30, 140, 70)
RED_SOFT  = (180, 40, 40)


class PitchPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.slide_num = 0
        self.set_margins(18, 16, 18)
        self.set_auto_page_break(auto=True, margin=16)
        self.add_font("DejaVu",  style="",  fname=FONT_REGULAR)
        self.add_font("DejaVu",  style="B", fname=FONT_BOLD)

    def header(self):
        self.set_font("DejaVu", "B", 7)
        self.set_text_color(*ACCENT)
        self.cell(0, 5, "OMNIX -- Decision Governance Infrastructure  |  Confidential  |  March 2026",
                  align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(1)

    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 5, "omnixquantum.net  |  contacto@omnixquantum.net", align="L", new_x=XPos.RIGHT)
        self.cell(0, 5, f"{self.page_no()} / 12", align="R")

    def slide_title(self, number, title, subtitle=None):
        self.slide_num = number
        self.set_fill_color(*ACCENT)
        bar_y = self.get_y()
        self.rect(self.l_margin, bar_y, self.w - self.l_margin - self.r_margin, 14, style="F")
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(*WHITE)
        self.set_xy(self.l_margin + 3, bar_y + 2)
        num_label = f"0{number}" if number < 10 else str(number)
        self.cell(14, 10, num_label, align="L", new_x=XPos.RIGHT)
        self.cell(0, 10, title.upper(), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if subtitle:
            self.set_y(bar_y + 16)
            self.set_font("DejaVu", "", 8)
            self.set_text_color(*ACCENT2)
            self.cell(0, 5, subtitle, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)
        self.set_text_color(*DARK)

    def body(self, text, size=9):
        self.set_font("DejaVu", "", size)
        self.set_text_color(*DARK)
        self.multi_cell(0, 5.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def bold_label(self, text, size=9):
        self.set_font("DejaVu", "B", size)
        self.set_text_color(*GOLD)
        self.cell(0, 6, text, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)

    def bullet(self, items, size=8.5):
        self.set_font("DejaVu", "", size)
        self.set_text_color(*DARK)
        indent = 8
        text_w = self.w - self.l_margin - self.r_margin - indent
        for item in items:
            self.set_x(self.l_margin)
            self.cell(indent, 5.5, "-", align="L", new_x=XPos.RIGHT)
            self.multi_cell(text_w, 5.5, item, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def metric_row(self, items):
        col_w = (self.w - self.l_margin - self.r_margin) / len(items)
        self.set_fill_color(*LIGHT_BG)
        self.rect(self.l_margin, self.get_y(), self.w - self.l_margin - self.r_margin, 18, style="F")
        start_y = self.get_y()
        for i, (val, label) in enumerate(items):
            x = self.l_margin + i * col_w
            self.set_xy(x, start_y + 1)
            self.set_font("DejaVu", "B", 12)
            self.set_text_color(*ACCENT)
            self.cell(col_w, 8, val, align="C", new_x=XPos.RIGHT)
            self.set_xy(x, start_y + 9)
            self.set_font("DejaVu", "", 7)
            self.set_text_color(*MID_GRAY)
            self.cell(col_w, 6, label, align="C", new_x=XPos.RIGHT)
        self.set_xy(self.l_margin, start_y + 20)
        self.set_text_color(*DARK)

    def two_col(self, left_title, left_items, right_title, right_items):
        col_w = (self.w - self.l_margin - self.r_margin - 6) / 2
        y = self.get_y()
        self.set_font("DejaVu", "B", 8)
        self.set_text_color(*ACCENT)
        self.set_xy(self.l_margin, y)
        self.cell(col_w, 6, left_title, align="L", new_x=XPos.RIGHT)
        self.set_x(self.l_margin + col_w + 6)
        self.cell(col_w, 6, right_title, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        y2 = self.get_y()
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*DARK)
        left_y = y2
        self.set_xy(self.l_margin, left_y)
        for item in left_items:
            self.set_xy(self.l_margin, self.get_y())
            self.cell(4, 5, "-", new_x=XPos.RIGHT)
            self.multi_cell(col_w - 4, 5, item, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        right_y = y2
        self.set_xy(self.l_margin + col_w + 6, right_y)
        for item in right_items:
            cx = self.l_margin + col_w + 6
            self.set_xy(cx, self.get_y())
            self.cell(4, 5, "-", new_x=XPos.RIGHT)
            self.multi_cell(col_w - 4, 5, item, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def table(self, headers, rows, col_widths=None):
        total_w = self.w - self.l_margin - self.r_margin
        if col_widths is None:
            col_w = total_w / len(headers)
            col_widths = [col_w] * len(headers)
        self.set_fill_color(*ACCENT)
        self.set_font("DejaVu", "B", 7.5)
        self.set_text_color(*WHITE)
        x = self.l_margin
        for i, h in enumerate(headers):
            self.set_xy(x, self.get_y())
            self.cell(col_widths[i], 7, h, border=0, align="L", fill=True, new_x=XPos.RIGHT)
            x += col_widths[i]
        self.ln()
        self.set_font("DejaVu", "", 7.5)
        for ri, row in enumerate(rows):
            fill = (ri % 2 == 0)
            if fill:
                self.set_fill_color(*LIGHT_BG)
            self.set_text_color(*DARK)
            x = self.l_margin
            row_y = self.get_y()
            max_h = 6
            for ci, cell in enumerate(row):
                self.set_xy(x, row_y)
                lines = self.multi_cell(col_widths[ci], 5.5, cell, border=0,
                                        fill=fill, align="L",
                                        new_x=XPos.RIGHT, new_y=YPos.TOP,
                                        dry_run=True, output="LINES")
                h = max(6, len(lines) * 5.5)
                max_h = max(max_h, h)
                x += col_widths[ci]
            x = self.l_margin
            for ci, cell in enumerate(row):
                self.set_xy(x, row_y)
                self.multi_cell(col_widths[ci], 5.5, cell, border=0,
                                fill=fill, align="L",
                                new_x=XPos.RIGHT, new_y=YPos.TOP)
                x += col_widths[ci]
            self.set_xy(self.l_margin, row_y + max_h)
        self.ln(3)


def generate():
    pdf = PitchPDF()

    # ─── SLIDE 1: COVER ───────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(6)
    box_y = pdf.get_y()
    pdf.set_fill_color(*ACCENT)
    pdf.rect(18, box_y, pdf.w - 36, 56, style="F")
    if os.path.exists(LOGO_PATH):
        logo_w = 30
        logo_x = (pdf.w - logo_w) / 2
        pdf.image(LOGO_PATH, x=logo_x, y=box_y + 3, w=logo_w)
    pdf.set_font("DejaVu", "B", 20)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(18, box_y + 32)
    pdf.cell(pdf.w - 36, 10, "OMNIX", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(pdf.w - 36, 7, "Decision Governance Infrastructure", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(*ACCENT2)
    pdf.cell(pdf.w - 36, 6, "for Automated Financial Systems", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(12)
    pdf.set_font("DejaVu", "B", 9)
    pdf.set_text_color(*GOLD)
    pdf.cell(0, 6, "INVESTOR PRESENTATION  |  PRE-SEED  |  MARCH 2026", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.4)
    pdf.line(18, pdf.get_y(), pdf.w - 18, pdf.get_y())
    pdf.ln(5)
    info = [
        ("Founder & CEO", "Harold Nunes"),
        ("Raise", "$500,000 USD  |  16.7% equity  |  $3M pre-money"),
        ("Stage", "Pre-Seed  |  MVP Live  |  Production-grade system"),
        ("Recognition", "SEMIFINALIST -- Eureka Dubai GCC 2026"),
        ("Contact", "contacto@omnixquantum.net  |  omnixquantum.net"),
    ]
    for label, value in info:
        pdf.set_font("DejaVu", "B", 8.5)
        pdf.set_text_color(*MID_GRAY)
        pdf.cell(44, 6, label + ":", align="L", new_x=XPos.RIGHT)
        pdf.set_font("DejaVu", "", 8.5)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 6, value, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ─── SLIDE 2: PROBLEM ─────────────────────────────────────────────────────
    pdf.add_page()
    pdf.slide_title(2, "The Problem", "Automated systems fail — and they fail at machine speed")
    pdf.body(
        "Institutions and funds operating automated financial systems face a critical structural gap: "
        "there is no governance layer between the signal and the execution. Every automated decision "
        "is a risk event. Without a dedicated control architecture, a single miscalibrated signal can "
        "trigger cascading losses before any human can intervene."
    )
    pdf.bold_label("The three failure modes with no governance:")
    pdf.bullet([
        "Signal failure -- Systems act on false signals during volatile or anomalous market conditions",
        "Coherence failure -- Multiple internal signals disagree, yet the system still executes",
        "Tail risk failure -- Low-probability, high-impact events (Black Swans) are not detected in time",
    ])
    pdf.bold_label("The institutional cost:")
    pdf.bullet([
        "Prop trading firms lose 15-40% of capital in their first year of automated deployment",
        "No audit trail = no regulatory defense when decisions are challenged",
        "MiCA (EU, 2025+), ADGM, and DIFC frameworks now require decision accountability documentation",
        "Post-quantum security is already a procurement requirement in regulated GCC institutions",
    ])
    pdf.ln(2)
    pdf.set_fill_color(*LIGHT_BG)
    pdf.rect(18, pdf.get_y(), pdf.w - 36, 12, style="F")
    pdf.set_xy(18, pdf.get_y() + 2)
    pdf.set_font("DejaVu", "B", 9)
    pdf.set_text_color(*ACCENT)
    pdf.multi_cell(pdf.w - 36, 5.5,
                   "\"When automated systems fail, they do not fail slowly. They fail at machine speed.\"\n"
                   "The market needs a governance layer. Not better signals. Better supervision.",
                   align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ─── SLIDE 3: SOLUTION ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.slide_title(3, "The Solution", "A fail-closed governance engine that authorizes every decision")
    pdf.body(
        "OMNIX is Decision Governance Infrastructure -- a control architecture that sits above automated "
        "trading and investment systems, validating every decision before it reaches execution. "
        "OMNIX does not generate signals. It governs them."
    )
    pdf.two_col(
        "What OMNIX does:",
        [
            "Intercepts every trade signal before execution",
            "Runs 8 sequential validation checkpoints",
            "Blocks decisions that fail any checkpoint",
            "Signs every decision with post-quantum cryptography",
            "Maintains a verifiable, tamper-proof audit trail",
        ],
        "What OMNIX does NOT do:",
        [
            "Generate trading signals or strategies",
            "Compete with existing trading platforms",
            "Manage or hold client assets",
            "Require replacing existing infrastructure",
            "Optimize for returns -- only for capital safety",
        ]
    )
    pdf.bold_label("Core design principle: Fail-Closed")
    pdf.body(
        "When in doubt, OMNIX blocks -- never acts. The system defaults to capital protection. "
        "A decision must earn the right to execute by passing every checkpoint independently. "
        "A single failed checkpoint halts execution, regardless of signal confidence."
    )
    pdf.set_fill_color(*LIGHT_BG)
    pdf.rect(18, pdf.get_y(), pdf.w - 36, 10, style="F")
    pdf.set_xy(18, pdf.get_y() + 2)
    pdf.set_font("DejaVu", "B", 9)
    pdf.set_text_color(*ACCENT)
    pdf.cell(pdf.w - 36, 6,
             "\"Intelligence may propose. OMNIX decides whether it is allowed to act.\"",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ─── SLIDE 4: HOW IT WORKS ────────────────────────────────────────────────
    pdf.add_page()
    pdf.slide_title(4, "How It Works", "8-checkpoint entry pipeline + 3-gate exit governance")
    pdf.bold_label("Entry Governance Pipeline (8 Checkpoints):")
    checkpoints = [
        ("CP-0", "Signal Integrity Validator (SIV)", "Data quality gate -- rejects corrupted or stale market data before evaluation begins"),
        ("CP-1", "Monte Carlo VETO", "10,000 simulation paths per decision -- blocks trades with negative expected return"),
        ("CP-2", "RMS VETO", "Risk Management System -- enforces hard exposure limits and position sizing rules"),
        ("CP-3", "VETO Early Return", "Fast-fail gate -- immediate halt if critical risk thresholds are breached"),
        ("CP-4", "Coherence Engine (6-tier)", "Measures signal agreement across 6 independent dimensions -- rejects incoherent decisions"),
        ("CP-5", "Adaptive Coherence Gate", "Dynamically adjusts coherence threshold based on real-time market regime severity"),
        ("CP-7", "Temporal Coherence Validator (TCV)", "Backward trajectory analysis -- validates decision consistency with recent market history"),
        ("CP-8", "Edge Confirmation Window (ECW)", "Requires 2 consecutive cycles of confirmed statistical edge before any execution is permitted"),
    ]
    pdf.table(["", "Checkpoint", "Description"], list(checkpoints), col_widths=[14, 52, 114])
    pdf.ln(2)
    pdf.bold_label("Exit Governance Layer (3 Gates):")
    pdf.bullet([
        "Gate 1 -- Regime-Adjusted Thresholds: Exit criteria shift dynamically with market regime (bull/bear/volatile)",
        "Gate 2 -- Exit Coherence Gate: Validates that exit signal is coherent with current market conditions",
        "Gate 3 -- TCV Exit Check: Temporal consistency validation applied to exit decisions",
    ])
    pdf.body("Every decision -- entry or exit -- is cryptographically signed with NIST-standardized "
             "post-quantum algorithms (Dilithium-3) and stored in a tamper-proof audit trail.")

    # ─── SLIDE 5: TRACTION ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.slide_title(5, "Traction", "Live system with verified governance metrics")
    pdf.metric_row([
        ("50,688", "Governance decisions processed"),
        ("728,868", "Shadow portfolio evaluations"),
        ("100%", "Veto accuracy (50 validated)"),
        ("0", "Capital at risk (paper trading)"),
    ])
    pdf.ln(3)
    pdf.bold_label("System timeline:")
    pdf.table(
        ["Phase", "Period", "Type", "Key Result"],
        [
            ["Phase 0 -- Real Capital", "Jul-Aug 2025", "Real (Kraken)", "1,115 real trades. Baseline established pre-governance."],
            ["Learning Baseline", "Nov 2025 - Jan 14, 2026", "Paper (simulated)", "119 trades. Risk engine calibrated. Veto system tuned."],
            ["Official Track Record", "Jan 15, 2026 - present", "Paper (simulated)", "679,388 veto decisions. 0 executions. System in capital-preservation mode -- governance thresholds under calibration."],
        ],
        [45, 42, 30, 57]
    )
    pdf.bold_label("Veto accuracy -- 3 real examples:")
    pdf.bullet([
        "XRP/USD -- Jan 9, 2026: BLACK SWAN veto (crash probability 50%). XRP fell -1.96% in 7 days. $391 per $20K position protected.",
        "AVAX/USD -- Jan 9, 2026: COHERENCE GATE veto (coherence score 26.3%, below threshold). AVAX fell -1.08% in 24h. Internal uncertainty detected before loss.",
        "BTC/USD -- Multiple dates: 396,067 Black Swan alerts since Jan 15. Zero executions. System correctly assessed unfavorable conditions each time.",
    ])
    pdf.bold_label("External recognition:")
    pdf.bullet([
        "SEMIFINALIST -- Eureka Dubai GCC 2026 (international startup competition)",
        "6 domain experts validated the architecture via LinkedIn (AI Risk Analysts, Quantum Security, AI Governance leaders)",
    ])

    # ─── SLIDE 6: MARKET OPPORTUNITY ──────────────────────────────────────────
    pdf.add_page()
    pdf.slide_title(6, "Market Opportunity", "$5.4B governance infrastructure segment -- compliance-driven demand accelerating")
    pdf.metric_row([
        ("18,000", "Target institutional clients"),
        ("$5.4B", "Governance infrastructure segment"),
        ("$540M", "Serviceable Addressable Market"),
        ("2025+", "MiCA regulation in force"),
    ])
    pdf.ln(3)
    pdf.bold_label("Market drivers:")
    pdf.bullet([
        "MiCA (EU, 2025+): First comprehensive crypto market regulation mandating decision accountability and audit trails",
        "ADGM & DIFC (UAE/GCC): World-class regulatory frameworks actively requiring AI governance documentation",
        "Institutional adoption: Hedge funds, prop firms, and exchanges are automating faster than their governance frameworks can keep up",
        "Sharia compliance: GCC institutions require governance infrastructure that documents and validates automated decisions for regulatory and Sharia audit",
        "Post-quantum mandate: Large regulated institutions in GCC are beginning to require quantum-resistant cryptography in procurement",
    ])
    pdf.bold_label("Target segments and addressability:")
    pdf.table(
        ["Segment", "Count (est.)", "Entry Point", "Annual Value"],
        [
            ["Prop trading firms", "~4,000 globally", "Pilot at $10K-15K/mo", "$120K-180K/yr per client"],
            ["Crypto exchanges (regulated)", "~500 globally", "API model $0.01-0.05/call", "Volume-driven"],
            ["Hedge funds / family offices", "~2,000 relevant", "Compliance-driven", "$300K-420K/yr per client"],
            ["Fintech investment platforms", "~1,500 relevant", "Embedded governance", "$240K-360K/yr per client"],
        ],
        [50, 35, 44, 45]
    )

    # ─── SLIDE 7: BUSINESS MODEL ──────────────────────────────────────────────
    pdf.add_page()
    pdf.slide_title(7, "Business Model", "Recurring SaaS + API-first + institutional licensing")
    pdf.table(
        ["Tier", "Target", "Pricing", "Model"],
        [
            ["Enterprise Pilot", "Prop firms, exchanges", "$10,000-$15,000/month", "Annual contract, renewable"],
            ["Enterprise Full", "Hedge funds, regulated funds", "$20,000-$35,000/month", "Annual + SLA + audit reports"],
            ["API Platform", "Platforms, exchanges at scale", "$0.01-$0.05 per governance call", "Volume-based, prepaid credits"],
            ["B2C Advanced", "Institutional-grade retail traders", "$149-$499/month", "SaaS, monthly subscription"],
        ],
        [32, 45, 50, 47]
    )
    pdf.bold_label("Revenue projections (conservative):")
    pdf.table(
        ["Year", "Model Focus", "Revenue", "Key Milestone"],
        [
            ["Y1 (2026)", "2-3 institutional pilots", "$300,000", "First paying clients, break-even Q4"],
            ["Y2 (2027)", "10 clients + API expansion", "$1,200,000", "Product-market fit confirmed"],
            ["Y3 (2028)", "30 clients + platform tier", "$4,800,000", "Series A ready"],
            ["Y4 (2029)", "80 clients + GCC expansion", "$13,000,000", "Regional market leadership"],
            ["Y5 (2030)", "150+ clients + white-label", "$26,000,000", "Category definition"],
        ],
        [22, 50, 30, 72]
    )
    pdf.bold_label("Investor return profile:")
    pdf.bullet([
        "Conservative scenario (10x revenue): MOIC 14.7x on pre-seed entry",
        "Base scenario (20x revenue): MOIC 41x",
        "Optimistic scenario (50x revenue): MOIC 102x",
        "Break-even target: Q4 2026 -- within 12 months of funding",
    ])

    # ─── SLIDE 8: COMPETITIVE ADVANTAGE ───────────────────────────────────────
    pdf.add_page()
    pdf.slide_title(8, "Competitive Advantage", "OMNIX vs. existing solutions")
    pdf.body(
        "Existing players — Riskalyze, Numerai, QuantConnect, Talos, CoinRoutes — optimize for returns or compliance reporting. "
        "None operate as a fail-closed governance layer above the execution engine. OMNIX does not compete with them. It sits above them."
    )
    pdf.ln(2)
    pdf.table(
        ["Feature", "Retail Bots", "Quant Funds", "Risk Platforms", "OMNIX"],
        [
            ["Fail-closed architecture", "No", "No", "Partial", "YES"],
            ["Independent veto authority per checkpoint", "No", "No", "No", "YES"],
            ["Post-quantum cryptographic audit trail", "No", "No", "No", "YES"],
            ["Public verifiable receipt URL", "No", "No", "No", "YES"],
            ["Shadow portfolio counterfactual engine", "No", "Internal only", "No", "YES"],
            ["Black Swan detection (4 severity levels)", "No", "Partial", "Partial", "YES"],
            ["Regime-conditioned position sizing (RCK)", "No", "Proprietary", "No", "YES"],
            ["Designed for MiCA / ADGM compliance", "No", "No", "Partial", "YES"],
        ],
        [62, 22, 22, 24, 24]
    )
    pdf.bold_label("The fundamental difference:")
    pdf.body(
        "Most risk platforms are fail-open -- they allow decisions unless something is clearly wrong. "
        "OMNIX is fail-closed -- it blocks decisions unless everything is clearly right. "
        "This is not a feature. It is a design philosophy that changes the entire risk surface of "
        "an automated system."
    )

    # ─── SLIDE 9: EXPERT VALIDATION ───────────────────────────────────────────
    pdf.add_page()
    pdf.slide_title(9, "Expert Validation", "Independent recognition from domain leaders")
    pdf.body(
        "At pre-seed stage, unsolicited validation from domain experts who reviewed the architecture "
        "and recognized its strategic direction is a strong signal of product-market fit."
    )
    pdf.table(
        ["Expert", "Role", "Key Feedback"],
        [
            ["James Moore", "Founder/CEO, Nova Jema AI Systems\n(AI governance, healthcare & public infra)",
             "\"Harold this is exactly the layer I've been trying to articulate... Curious how OMNIX is approaching that boundary between recommendation and binding authority.\""],
            ["Mostafa Monsour", "Founder, ULTRA MATRIX\nCognitive & Strategic Architect",
             "\"Your work with OMNIX Quantum appears to be exploring an important part of that stack.\" -- Identified the authority + verification gap."],
            ["HIL-AIW", "AI governance platform\n(925+ LinkedIn followers)",
             "\"Your 8-checkpoint system with Monte Carlo VETO is brilliant... most teams aren't even thinking about quantum-resistant auditability yet.\""],
            ["Christopher Turk", "Quantum Security Architecture\nZero Trust & Agentic AI Security",
             "\"This is honestly pretty good.\" -- Extended technical exchange validating Dilithium-3 selection and decision provenance model."],
            ["Guomin Yang", "Creator, RDL Framework\nAI Governance Strategist",
             "Independently cited Harold in a published article, mapping OMNIX to his 3-layer governance model (Policy > Operational > Structural)."],
            ["William Fedorich", "AI Risk Analyst\nPublisher, The Bill Fedorich Letter",
             "\"Ensuring every AI decision is vetted through multiple checkpoints is critical for high-stakes environments like trading and insurance... foundational technology.\""],
        ],
        [38, 48, 88]
    )

    # ─── SLIDE 10: TEAM ───────────────────────────────────────────────────────
    pdf.add_page()
    pdf.slide_title(10, "Team", "Solo founder with full-stack execution")
    pdf.bold_label("Harold Nunes -- Founder & CEO")
    pdf.bullet([
        "Designed and built the entire OMNIX governance infrastructure from architecture to production deployment",
        "40 Architecture Decision Records (ADRs) documenting every design choice",
        "171 automated tests passing as of March 2026 -- full system coverage",
        "Implemented NIST-standardized post-quantum cryptography (Dilithium-3 + Kyber-768) independently",
        "Translated institutional risk governance concepts into a production-grade automated system",
        "SEMIFINALIST -- Eureka Dubai GCC 2026 as sole founder",
    ])
    pdf.ln(2)
    pdf.bold_label("Infrastructure & advisory support:")
    pdf.bullet([
        "Contract developers and infrastructure consultants engaged for specific technical deliverables",
        "Domain expert network validated architecture (see Slide 9)",
        "System runs 24/7 on Railway production infrastructure with PostgreSQL + Redis",
    ])
    pdf.ln(2)
    pdf.bold_label("What the $500K enables:")
    pdf.bullet([
        "First technical hire -- senior backend engineer to accelerate institutional integrations",
        "Legal and regulatory setup -- ADGM entity, Sharia compliance assessment for GCC market",
        "Security audit -- third-party post-quantum cryptography validation",
        "Sales infrastructure -- CRM, legal templates, pilot program structure",
    ])

    # ─── SLIDE 11: THE ASK ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.slide_title(11, "The Investment", "$500K pre-seed at $3M pre-money valuation")
    pdf.metric_row([
        ("$500K", "Raise target"),
        ("16.7%", "Equity offered"),
        ("$3M", "Pre-money valuation"),
        ("Q4 2026", "Break-even target"),
    ])
    pdf.ln(3)
    pdf.bold_label("Use of funds:")
    pdf.table(
        ["Allocation", "Amount", "Purpose"],
        [
            ["Infrastructure & Security", "$200,000 (40%)", "Production hardening, compliance certifications, PQC security audit, public verification server"],
            ["Sales & Business Development", "$175,000 (35%)", "First institutional pilots (US + GCC), legal sales infrastructure, regulatory outreach (ADGM), Sharia compliance assessment"],
            ["Team & Operations", "$125,000 (25%)", "First technical hire, legal entity setup, operating runway through Q4 2026"],
        ],
        [52, 38, 84]
    )
    pdf.bold_label("Investor return scenarios (pre-seed entry):")
    pdf.table(
        ["Scenario", "Y5 Revenue", "Valuation (5x rev)", "MOIC", "IRR (est.)"],
        [
            ["Conservative", "$13M", "$65M", "14.7x", "~72%"],
            ["Base", "$26M", "$130M", "41x", "~110%"],
            ["Optimistic", "$65M", "$325M", "102x", "~160%"],
        ],
        [35, 28, 40, 22, 25]
    )
    pdf.bold_label("Strategic value-add sought (beyond capital):")
    pdf.bullet([
        "Network access to prop trading firms, hedge funds, or regulated exchanges for pilot programs",
        "GCC / ADGM ecosystem connections for Middle East market entry",
        "FinTech, RegTech, or AI governance domain expertise",
    ])

    # ─── SLIDE 12: CLOSE ──────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(10)
    pdf.set_fill_color(*ACCENT)
    pdf.rect(18, pdf.get_y(), pdf.w - 36, 30, style="F")
    pdf.set_font("DejaVu", "B", 14)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(18, pdf.get_y() + 6)
    pdf.cell(pdf.w - 36, 10, "The governance layer is missing.", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(200, 220, 255)
    pdf.cell(pdf.w - 36, 8, "OMNIX is building it.", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)
    pdf.set_font("DejaVu", "B", 9)
    pdf.set_text_color(200, 155, 0)
    pdf.cell(pdf.w - 36, 6, "OMNIX is not a trading system.", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(200, 220, 255)
    pdf.cell(pdf.w - 36, 6, "OMNIX is the missing governance layer for automated decision systems.", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(14)
    pdf.bold_label("Why now:")
    pdf.bullet([
        "MiCA regulation active in EU -- compliance demand is immediate, not future",
        "GCC sovereign capital actively deploying into AI governance infrastructure",
        "Post-quantum cryptography becoming a procurement requirement at institutional level",
        "No competitor has built a fail-closed, multi-checkpoint governance engine with PQC audit trail",
    ])
    pdf.ln(3)
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.4)
    pdf.line(18, pdf.get_y(), pdf.w - 18, pdf.get_y())
    pdf.ln(5)
    contact = [
        ("Founder", "Harold Nunes -- Founder & CEO, OMNIX Quantum"),
        ("Email", "contacto@omnixquantum.net"),
        ("Web", "omnixquantum.net"),
        ("Verify", "omnixquantum.net/verify  (public decision receipt verification)"),
        ("Recognition", "SEMIFINALIST -- Eureka Dubai GCC 2026"),
    ]
    for label, value in contact:
        pdf.set_font("DejaVu", "B", 8.5)
        pdf.set_text_color(*MID_GRAY)
        pdf.cell(30, 6, label + ":", align="L", new_x=XPos.RIGHT)
        pdf.set_font("DejaVu", "", 8.5)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 6, value, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(*MID_GRAY)
    pdf.multi_cell(0, 4.5,
        "This document is confidential and intended solely for the recipient. All financial projections "
        "are forward-looking estimates and do not constitute a guarantee of performance. Track record "
        "data from the Learning Baseline (Nov 2025 - Jan 14, 2026) and Official Track Record "
        "(Jan 15, 2026 - present) reflects paper/simulated trading, not real capital deployment. "
        "Phase 0 (Jul-Aug 2025) involved real capital on Kraken exchange.",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    out = os.path.join(OUTPUT_DIR, "OMNIX_Investor_Pitch_Deck.pdf")
    pdf.output(out)
    size_kb = os.path.getsize(out) / 1024
    print(f"Generated: {out}")
    print(f"File size: {size_kb:.1f} KB")


if __name__ == "__main__":
    generate()
