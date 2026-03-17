#!/usr/bin/env python3
"""
OMNIX Quantum — Pilot Program Proposal PDF Generator
2-page professional proposal for prospective pilot clients.
"""
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "business", "pdfs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_DIR     = os.path.join(
    os.path.expanduser("~"),
    "workspace/.pythonlibs/lib/python3.11/site-packages/kaleido/executable/xdg/fonts/truetype/dejavu"
)
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD    = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
FONT_ITALIC  = os.path.join(FONT_DIR, "DejaVuSans.ttf")

NAVY     = (10, 25, 60)
GOLD     = (212, 175, 55)
WHITE    = (255, 255, 255)
LIGHT_BG = (245, 247, 252)
MID_GRAY = (120, 130, 150)
GREEN_DK = (0, 100, 60)
DARK     = (20, 20, 40)
RED_DK   = (140, 30, 30)


class PilotPDF(FPDF):
    def header(self):
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, 18, style="F")
        self.set_y(4)
        self.set_font("Bold", size=11)
        self.set_text_color(*GOLD)
        self.cell(0, 6, "OMNIX QUANTUM  --  Decision Governance Infrastructure", align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Regular", size=7)
        self.set_text_color(*WHITE)
        self.cell(0, 4, "omnixquantum.net  |  contacto@omnixquantum.net  |  Abu Dhabi, UAE", align="C")

    def footer(self):
        self.set_fill_color(*NAVY)
        self.rect(0, self.h - 10, self.w, 10, style="F")
        self.set_y(-9)
        self.set_font("Regular", size=6)
        self.set_text_color(*GOLD)
        self.cell(0, 4,
                  "Confidential -- Pilot Program Proposal  |  Harold Nunes, Founder & CEO  |  "
                  "SSRN 6321298  |  Zenodo DOI: 10.5281/zenodo.19056919",
                  align="C")


def section_title(pdf, text, color=NAVY):
    pdf.set_font("Bold", size=11)
    pdf.set_text_color(*color)
    pdf.set_fill_color(*LIGHT_BG)
    pdf.cell(0, 8, f"  {text}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)


def body(pdf, text, size=9.5):
    pdf.set_font("Regular", size=size)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(0, 5, text)
    pdf.ln(2)


def two_col_row(pdf, left_label, left_val, right_label, right_val, col_w=None):
    if col_w is None:
        col_w = (pdf.w - pdf.l_margin - pdf.r_margin) / 2 - 2
    pdf.set_font("Bold", size=8.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(col_w, 6, left_label)
    pdf.cell(4, 6, "")
    pdf.cell(col_w, 6, right_label, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Regular", size=8.5)
    pdf.set_text_color(*DARK)
    pdf.cell(col_w, 5.5, left_val)
    pdf.cell(4, 5.5, "")
    pdf.cell(col_w, 5.5, right_val, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)


def bullet_row(pdf, icon, label, desc):
    pdf.set_font("Bold", size=9)
    pdf.set_text_color(*NAVY)
    pdf.cell(6, 6, icon)
    pdf.cell(50, 6, label)
    pdf.set_font("Regular", size=9)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(0, 6, desc)
    pdf.ln(1)


def divider(pdf, color=GOLD):
    pdf.set_draw_color(*color)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)


def highlight_box(pdf, text, bg=LIGHT_BG, text_color=NAVY):
    pdf.set_fill_color(*bg)
    pdf.set_font("Bold", size=9.5)
    pdf.set_text_color(*text_color)
    pdf.multi_cell(0, 6, f"  {text}  ", fill=True)
    pdf.ln(3)


def generate():
    pdf = PilotPDF(orientation="P", unit="mm", format="A4")
    pdf.add_font("Regular", fname=FONT_REGULAR)
    pdf.add_font("Bold",    fname=FONT_BOLD)
    pdf.add_font("Italic",  fname=FONT_ITALIC)
    pdf.set_margins(18, 26, 18)
    pdf.set_auto_page_break(auto=True, margin=16)

    # ── PAGE 1 ───────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(4)

    # Hero title
    pdf.set_font("Bold", size=20)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 10, "30-Day Pilot Program", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Regular", size=11)
    pdf.set_text_color(*MID_GRAY)
    pdf.cell(0, 6, "Governance Infrastructure for Your Automated Decision Systems -- No Cost",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    divider(pdf, GOLD)

    # The offer
    section_title(pdf, "What We Are Offering")
    body(pdf,
         "OMNIX Quantum provides a 30-day complimentary pilot of our Decision Governance Infrastructure. "
         "Your automated decision pipeline connects to our governance engine, which validates each decision "
         "through an 8-checkpoint veto system before execution and generates a cryptographically signed "
         "receipt for every outcome.\n\n"
         "There is no integration fee, no licensing cost, and no commitment required. The pilot is designed "
         "for organizations that want to evaluate governance infrastructure before a procurement decision.")
    pdf.ln(2)

    # What client provides / receives — two columns
    section_title(pdf, "Pilot Structure")
    two_col_row(pdf,
                "What you provide",
                "Your decision signals (API or JSON feed)\nYour risk thresholds\n30 min onboarding call",
                "What you receive",
                "Governance receipt per decision\nFull audit trail (PQC-signed)\nGovernance report at Day 30")

    divider(pdf)

    # Checkpoints
    section_title(pdf, "The 8-Checkpoint Governance Pipeline")
    body(pdf,
         "Every decision submitted during the pilot passes through the full production pipeline in real time:")
    checkpoints = [
        ("1.", "Signal Integrity Validation",   "Is the input signal coherent and within bounds?"),
        ("2.", "Regime Assessment",              "Is the current market/operational regime appropriate?"),
        ("3.", "Monte Carlo VETO Engine",        "Does probability distribution support the action?"),
        ("4.", "Black Swan Detector",            "Are there tail-risk conditions present?"),
        ("5.", "Coherence Engine (6 tiers)",     "Is there internal consistency across all signals?"),
        ("6.", "Risk Management System (RMS)",   "Does the action satisfy portfolio risk constraints?"),
        ("7.", "Kelly Criterion Sizing",         "Is the proposed position size within safe bounds?"),
        ("8.", "Final Authorization",            "All gates passed -- governance receipt generated"),
    ]
    for num, name, desc in checkpoints:
        bullet_row(pdf, num, f"{name}:", desc)
    pdf.ln(2)

    highlight_box(pdf,
                  "Every decision that passes generates a cryptographically signed receipt -- "
                  "independently verifiable at omnixquantum.net/r/{receipt_id}",
                  bg=(230, 240, 255), text_color=NAVY)

    # ── PAGE 2 ───────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(4)

    # Why now
    section_title(pdf, "Why Governance Infrastructure Matters Now")
    body(pdf,
         "The majority of governance controls in automated systems are applied after execution -- "
         "audits, compliance reviews, and regulatory checks that arrive after the decision has already "
         "produced its outcome. When an automated system fails, it fails at machine speed.\n\n"
         "OMNIX moves governance to the execution boundary: decisions are validated before they are "
         "committed. The result is a structural governance property -- not an advisory layer that can "
         "be overridden.")
    pdf.ln(2)

    # Regulatory context
    section_title(pdf, "Regulatory Drivers")
    regs = [
        ("EU AI Act (2025+)",          "High-risk AI systems require pre-execution auditability and traceability."),
        ("MiCA (2024-2025)",           "Crypto asset service providers must demonstrate operational risk controls."),
        ("BCB Resolution 538",         "Brazil mandates cryptographic audit trails for automated financial decisions."),
        ("ADGM / SEC frameworks",      "Governance-by-design is emerging as a baseline expectation for AI in finance."),
    ]
    for reg, desc in regs:
        bullet_row(pdf, ">>", reg, desc)
    pdf.ln(2)

    divider(pdf)

    # What OMNIX produces
    section_title(pdf, "What OMNIX Has Produced in Production")
    highlights = [
        ("72,443",   "real governance decisions processed Feb 21 -- Mar 16, 2026"),
        ("100%",     "post-quantum signed (Dilithium-3 / ML-DSA-65, NIST-standardized)"),
        ("SHA-256",  "hash chain -- each receipt links to the previous, independently verifiable"),
        ("0",        "approved decisions without passing all 8 checkpoints"),
    ]
    for val, desc in highlights:
        pdf.set_font("Bold", size=10)
        pdf.set_text_color(*NAVY)
        pdf.cell(22, 7, val)
        pdf.set_font("Regular", size=9.5)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 7, desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    highlight_box(pdf,
                  "Full dataset publicly available: Zenodo DOI 10.5281/zenodo.19056919  |  "
                  "Academic preprint: SSRN Working Paper 6321298 (under peer review)",
                  bg=(240, 248, 240), text_color=GREEN_DK)

    divider(pdf)

    # Pilot terms
    section_title(pdf, "Pilot Terms")
    terms = [
        ("Duration",     "30 days from integration date"),
        ("Cost",         "No cost -- complimentary pilot"),
        ("Commitment",   "No obligation after pilot completion"),
        ("Data privacy", "Decision signals processed and stored with Fernet encryption at rest"),
        ("Output",       "Full governance audit trail + Day-30 governance performance report"),
        ("Next steps",   "30-minute onboarding call to define signal format and thresholds"),
    ]
    for label, val in terms:
        pdf.set_font("Bold", size=9)
        pdf.set_text_color(*NAVY)
        pdf.cell(38, 6, f"{label}:")
        pdf.set_font("Regular", size=9)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 6, val, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    divider(pdf)

    # Contact
    section_title(pdf, "Start the Pilot")
    pdf.set_font("Bold", size=10)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 7, "Harold Nunes  --  Founder & CEO, OMNIX Quantum",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    contact_items = [
        ("Email",     "contacto@omnixquantum.net"),
        ("WhatsApp",  "+1 (650) 481-5494"),
        ("Demo",      "omnixquantum.net/try  (live -- no login required)"),
        ("LinkedIn",  "linkedin.com/in/harold-nunes-21bb65285"),
    ]
    for label, val in contact_items:
        pdf.set_font("Bold", size=9)
        pdf.set_text_color(*MID_GRAY)
        pdf.cell(22, 6, f"{label}:")
        pdf.set_font("Regular", size=9)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 6, val, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    out = os.path.join(OUTPUT_DIR, "OMNIX_Pilot_Proposal.pdf")
    pdf.output(out)
    size_kb = os.path.getsize(out) / 1024
    print(f"Generated: {out}")
    print(f"File size: {size_kb:.1f} KB")


if __name__ == "__main__":
    generate()
