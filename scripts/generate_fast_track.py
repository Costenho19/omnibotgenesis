#!/usr/bin/env python3
"""
Generate OMNIX Fast Track Overview PDF (10 Key Points).
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
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD    = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

DARK      = (20, 20, 40)
ACCENT    = (0, 80, 160)
MID_GRAY  = (180, 180, 190)
LIGHT_BG  = (245, 247, 252)
WHITE     = (255, 255, 255)

POINTS = [
    (
        "1. Problem",
        "Automated financial systems increasingly execute critical decisions without a dedicated governance "
        "layer to validate, constrain, and supervise those actions. When automated systems fail, they do not "
        "fail slowly -- they fail at machine speed. This exposes institutions to operational errors, "
        "uncontrolled risk, and cascading losses before any human can intervene."
    ),
    (
        "2. Solution",
        "OMNIX is a governance infrastructure that simulates, validates, and authorizes financial decisions "
        "before execution -- creating a protective control layer for automated trading and investment systems. "
        "The engine has processed over 50,688 governance decisions and 728,868 shadow portfolio evaluations, "
        "achieving 100% veto accuracy on validated outcomes. Every decision is cryptographically signed using "
        "NIST-standardized post-quantum algorithms."
    ),
    (
        "3. Target Market",
        "OMNIX is designed for institutions operating automated financial systems: hedge funds, proprietary "
        "trading firms, crypto exchanges, fintech investment platforms, and robo-advisors. Secondary verticals "
        "include insurance, credit underwriting, and autonomous logistics systems. "
        "Regulatory demand is active: Brazil's Central Bank (BCB) Resolution 538 and CMN 5.274 (December 2025) "
        "mandate cryptographic traceability, full audit trails, and explainable automated decisions for all "
        "financial institutions -- compliance deadline March 1, 2026. Over 1,600 BCB-regulated institutions "
        "face mandatory governance requirements today."
    ),
    (
        "4. Market Size",
        "The global ecosystem of automated trading and algorithmic investment firms includes approximately "
        "18,000 potential institutional customers (source: industry estimates from BIS Quarterly Review and "
        "Tabb Group). The market is expanding as MiCA (2025+) and international AI governance regulations "
        "create compliance-driven demand for decision audit infrastructure."
    ),
    (
        "5. Estimated TAM / SAM",
        "Total Addressable Market (TAM): ~$5.4B USD (18,000 clients x $300K average annual revenue). "
        "Serviceable Addressable Market (SAM, Year 1-3): ~$540M USD -- top 10% of institutions with "
        "active automation and compliance pressure. OMNIX targets SAM first via direct outreach to "
        "crypto-native prop trading firms and regulated fintech platforms."
    ),
    (
        "6. Product Pricing",
        "Pilot institutional pricing: $10,000-$15,000 per month. "
        "Full commercial pricing: $20,000-$35,000 per month. "
        "API validation model (platforms): $0.01-$0.05 per governance call. "
        "B2C advanced traders: $149-$499 per month (SaaS tier)."
    ),
    (
        "7. Value Proposition",
        "OMNIX does not attempt to optimize trading strategies. It protects institutional capital by "
        "preventing operational mistakes, enforcing risk controls, and supervising automated decision-making. "
        "Fail-closed by design: when in doubt, the system blocks -- never acts. "
        "OMNIX is a SEMIFINALIST at Eureka Dubai GCC 2026, validating the governance infrastructure "
        "concept at an international level. "
        "Regulatory validation: Brazil's BCB already mandates what OMNIX delivers natively -- "
        "cryptographic audit trails (Resolution 538), explainable automated decisions (LGPD Art. 20), "
        "and full decision traceability (CMN 5.274). Brazil's AI Law (PL 2.338/2023, approval expected 2026) "
        "will extend these requirements across all automated systems. Regulatory demand is real and active, "
        "not projected. Banco do Brasil (80M+ customers) is already implementing AI governance infrastructure "
        "using IBM watsonx -- validating institutional appetite for exactly this solution."
    ),
    (
        "8. Client ROI (Evidence-Based)",
        "Shadow portfolio analysis across 728,868 evaluations shows that vetoed decisions would have "
        "resulted in losses at a 100% accuracy rate on validated outcomes (50 independently cross-referenced "
        "against 48h price action). An institutional client paying $300,000 annually can reasonably "
        "expect to protect $2,500,000 or more in capital from governance failures -- an estimated 8x ROI -- "
        "based on observed veto-to-loss correlation in OMNIX's live governance engine."
    ),
    (
        "9. Investment Sought + Use of Funds",
        "OMNIX is seeking $500,000 USD in exchange for 16.7% equity, implying a pre-money valuation of "
        "$3,000,000 USD. Use of funds: 40% infrastructure and security hardening ($200K), "
        "35% sales and business development -- first institutional pilots ($175K), "
        "25% team and operations ($125K). Target: break-even by Q4 2026."
    ),
    (
        "10. Key Pitch Message",
        "OMNIX does not compete with trading platforms or signal providers. It is the governance layer "
        "that sits above them -- validating, constraining, and authorizing every automated decision before "
        "it reaches execution. Intelligence may propose. OMNIX decides whether it is allowed to act."
    ),
]


class FastTrackPDF(FPDF):
    def header(self):
        self.set_font("DejaVu", "B", 8)
        self.set_text_color(*ACCENT)
        self.cell(0, 6, "OMNIX -- Decision Governance Infrastructure", align="L",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)

    def footer(self):
        self.set_y(-14)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 5, "March 2026  |  Confidential", align="L", new_x=XPos.RIGHT)
        self.cell(0, 5, f"Page {self.page_no()}", align="R")


def generate():
    pdf = FastTrackPDF()
    pdf.set_margins(20, 18, 20)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("DejaVu", style="",  fname=FONT_REGULAR)
    pdf.add_font("DejaVu", style="B", fname=FONT_BOLD)
    pdf.add_page()

    # Title block
    pdf.set_fill_color(*ACCENT)
    pdf.rect(20, pdf.get_y(), pdf.w - 40, 18, style="F")
    pdf.set_font("DejaVu", "B", 13)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(20, pdf.get_y() + 3)
    pdf.cell(pdf.w - 40, 12, "OMNIX -- Fast Track Overview", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(*MID_GRAY)
    pdf.cell(0, 5, "10 Key Points  |  Pre-Seed Round  |  $500,000 USD  |  Eureka Dubai GCC 2026 Semifinalist",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    for i, (title, body) in enumerate(POINTS):
        # Number + title bar
        pdf.set_fill_color(*LIGHT_BG)
        pdf.set_font("DejaVu", "B", 9)
        pdf.set_text_color(*ACCENT)
        fill = (i % 2 == 0)
        if fill:
            pdf.set_fill_color(*LIGHT_BG)
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.rect(x, y, pdf.w - 40, 7, style="F")
        pdf.cell(0, 7, title, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Body text
        pdf.set_font("DejaVu", "", 8.5)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(0, 5, body, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

    out = os.path.join(OUTPUT_DIR, "OMNIX_FastTrack_Overview.pdf")
    pdf.output(out)
    size_kb = os.path.getsize(out) / 1024
    print(f"Generated: {out}")
    print(f"File size: {size_kb:.1f} KB")


if __name__ == "__main__":
    generate()
