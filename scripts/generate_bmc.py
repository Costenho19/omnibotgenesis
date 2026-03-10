#!/usr/bin/env python3
"""
OMNIX Business Model Canvas -- 1-page PDF generator. Professional design with logo.
"""
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "business", "pdfs")
LOGO_PATH  = os.path.join(BASE_DIR, "omnix_web", "public", "logo.png")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_DIR = os.path.join(
    os.path.expanduser("~"),
    "workspace/.pythonlibs/lib/python3.11/site-packages/kaleido/executable/xdg/fonts/truetype/dejavu"
)
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD    = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

DARK      = (20,  20,  40)
NAVY      = (10,  18,  40)
ACCENT    = (0,   80,  160)
ACCENT2   = (0,   110, 190)
GOLD      = (200, 155, 0)
MID_GRAY  = (150, 155, 170)
LIGHT_BG  = (240, 244, 252)
WHITE     = (255, 255, 255)
GREEN     = (20,  120, 60)
GREEN_DK  = (10,  80,  40)


class BMCPDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_fill_color(*NAVY)
        self.rect(0, self.h - 8, self.w, 8, style="F")
        self.set_y(-7)
        self.set_font("DejaVu", "", 6)
        self.set_text_color(*GOLD)
        self.cell(0, 4,
                  "omnixquantum.net  |  Pre-Seed $500,000 USD  |  Eureka Dubai GCC 2026 Semifinalist  |  Confidential",
                  align="C")


def block(pdf, x, y, w, h, title, lines, title_color=None, bg=None, header_bg=None):
    # Background fill
    bg_col = bg or WHITE
    pdf.set_fill_color(*bg_col)
    pdf.rect(x, y, w, h, style="F")
    # Colored title strip
    strip_h = 6.5
    hdr_bg = header_bg or ACCENT
    pdf.set_fill_color(*hdr_bg)
    pdf.rect(x, y, w, strip_h, style="F")
    # Border
    pdf.set_draw_color(*MID_GRAY)
    pdf.set_line_width(0.25)
    pdf.rect(x, y, w, h)
    # Title text
    tc = title_color or WHITE
    pdf.set_font("DejaVu", "B", 6.5)
    pdf.set_text_color(*tc)
    pdf.set_xy(x + 1.5, y + 0.8)
    pdf.cell(w - 3, 5, title.upper(), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    # Body lines
    pdf.set_font("DejaVu", "", 6)
    pdf.set_text_color(*DARK)
    for line in lines:
        pdf.set_xy(x + 1.5, pdf.get_y())
        prefix = "- " if not line.startswith("*") else ""
        text = line.lstrip("*")
        if text == "":
            pdf.ln(1.0)
        else:
            pdf.multi_cell(w - 3, 3.5, prefix + text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def generate():
    pdf = BMCPDF()
    pdf.set_margins(6, 6, 6)
    pdf.set_auto_page_break(auto=False)
    pdf.add_font("DejaVu", style="",  fname=FONT_REGULAR)
    pdf.add_font("DejaVu", style="B", fname=FONT_BOLD)
    pdf.add_page()

    # ── Full-bleed header bar (dark navy + gold accent stripe) ─────────────────
    HEADER_H = 22
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, pdf.w, HEADER_H, style="F")
    pdf.set_fill_color(*GOLD)
    pdf.rect(0, HEADER_H - 1.2, pdf.w, 1.2, style="F")

    # Logo (left side of header)
    logo_size = 17
    try:
        pdf.image(LOGO_PATH, x=2, y=2, h=logo_size, keep_aspect_ratio=True)
    except Exception:
        pass

    # Title text centered in header
    pdf.set_font("DejaVu", "B", 13)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(30, 3.5)
    pdf.cell(pdf.w - 60, 7, "OMNIX QUANTUM  --  Business Model Canvas", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(*GOLD)
    pdf.set_xy(30, 11)
    pdf.cell(pdf.w - 60, 5,
             "Decision Governance Infrastructure  |  Eureka Dubai GCC 2026 Semifinalist  |  Pre-Seed $500K",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_y(HEADER_H + 1)

    # Layout constants
    M = 6           # left margin
    TW = pdf.w - 12 # total width = 197
    start_y = pdf.get_y()

    # Column widths (5 columns)
    # KP | KA+KR | VP | CR+CH | CS
    c1 = 37
    c2 = 37
    c3 = 45
    c4 = 37
    c5 = TW - c1 - c2 - c3 - c4  # ~41

    row1_h = 85
    row2_h = 38

    x1 = M
    x2 = M + c1
    x3 = M + c1 + c2
    x4 = M + c1 + c2 + c3
    x5 = M + c1 + c2 + c3 + c4

    y1 = start_y
    y2 = start_y + row1_h

    # ── ROW 1 ────────────────────────────────────────────────────────────────

    # KEY PARTNERS
    block(pdf, x1, y1, c1, row1_h, "Key Partners", [
        "Regulatory & Compliance",
        "ADGM (target ecosystem)",
        "DIFC (expansion target)",
        "",
        "Technology",
        "Railway (cloud infra)",
        "Google Gemini 2.5 Flash",
        "OpenAI GPT-4o",
        "PostgreSQL / Redis",
        "",
        "Strategic Pipeline",
        "Prop trading firms (pilots)",
        "Trading platforms (API)",
        "Institutional sales network",
    ], bg=LIGHT_BG, header_bg=(0, 60, 120))

    # KEY ACTIVITIES (top half of col 2)
    block(pdf, x2, y1, c2, row1_h // 2, "Key Activities", [
        "8-Checkpoint governance engine",
        "Shadow portfolio analysis",
        "PQC-signed audit trail generation",
        "API integration for enterprise clients",
        "Compliance & telemetry monitoring",
        "Multi-vertical domain adaptation",
    ], bg=LIGHT_BG, header_bg=(0, 80, 150))

    # KEY RESOURCES (bottom half of col 2)
    block(pdf, x2, y1 + row1_h // 2, c2, row1_h - row1_h // 2, "Key Resources", [
        "Governance engine (live, production)",
        "50,688 validated decisions",
        "728,868 shadow evaluations",
        "36 Architecture Decision Records",
        "PQC cryptographic stack",
        "Harold Nunes -- Founder & CEO",
    ], bg=LIGHT_BG, header_bg=(0, 90, 160))

    # VALUE PROPOSITION (center, full height + row2) -- navy background, gold header
    vp_h = row1_h + row2_h
    pdf.set_fill_color(*NAVY)
    pdf.rect(x3, y1, c3, vp_h, style="F")
    pdf.set_fill_color(*GOLD)
    pdf.rect(x3, y1, c3, 7, style="F")
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.4)
    pdf.rect(x3, y1, c3, vp_h)
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(*NAVY)
    pdf.set_xy(x3 + 1.5, y1 + 1)
    pdf.cell(c3 - 3, 5, "VALUE PROPOSITION", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    vp_lines = [
        "*\"Preventing costly mistakes",
        "*before they happen.\"",
        "",
        "OMNIX is Decision Governance",
        "Infrastructure -- the control layer",
        "between signals and execution.",
        "",
        "Fail-closed by design:",
        "Block first, act only with",
        "confirmed edge across 8",
        "independent checkpoints.",
        "",
        "What clients get:",
        "Capital protected before loss",
        "Full PQC-signed audit trail",
        "MiCA + ADGM compliance ready",
        "Sharia governance assessment",
        "100% veto accuracy (validated)",
        "",
        "Key differentiator:",
        "NOT a trading system.",
        "The governance layer ABOVE it.",
    ]
    pdf.set_font("DejaVu", "", 6)
    for line in vp_lines:
        pdf.set_xy(x3 + 2, pdf.get_y())
        text = line.lstrip("*")
        if text == "":
            pdf.ln(1.5)
        elif line.startswith("*"):
            pdf.set_font("DejaVu", "B", 6.5)
            pdf.set_text_color(*GOLD)
            pdf.multi_cell(c3 - 4, 3.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("DejaVu", "", 6)
            pdf.set_text_color(200, 220, 255)
        else:
            pdf.set_text_color(200, 220, 255)
            pdf.multi_cell(c3 - 4, 3.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # CUSTOMER RELATIONSHIPS (top half of col 4)
    block(pdf, x4, y1, c4, row1_h // 2, "Customer Relationships", [
        "Structured onboarding + risk config",
        "Technical integration support",
        "SLA-based uptime (99.5% target)",
        "Governance review sessions",
        "Shadow Portfolio learning loop",
        "High switching cost = retention",
    ], bg=LIGHT_BG, header_bg=(0, 80, 150))

    # CHANNELS (bottom half of col 4)
    block(pdf, x4, y1 + row1_h // 2, c4, row1_h - row1_h // 2, "Channels", [
        "Direct LinkedIn outreach",
        "ADGM / DIFC ecosystem events",
        "Eureka Dubai GCC (active)",
        "omnixquantum.net demos",
        "API marketplace listings",
        "Investor intro network (current)",
    ], bg=LIGHT_BG, header_bg=(0, 90, 160))

    # CUSTOMER SEGMENTS
    block(pdf, x5, y1, c5, row1_h, "Customer Segments", [
        "PRIMARY -- B2B Institutional:",
        "Prop trading firms (200+ ADGM)",
        "Regulated crypto hedge funds",
        "Trading platforms (MiCA pressure)",
        "Family offices (MENA/Asia)",
        "",
        "SECONDARY -- B2C:",
        "Advanced independent traders",
        "High-net-worth self-directed",
        "",
        "FUTURE VERTICALS:",
        "Supply chain (Y2-3)",
        "Credit / insurance (Y3+)",
        "Autonomous systems (Y3+)",
    ], bg=LIGHT_BG, header_bg=(0, 60, 120))

    # ── ROW 2 ────────────────────────────────────────────────────────────────

    # COST STRUCTURE
    half_w = (x3 - M)
    block(pdf, x1, y2, half_w, row2_h, "Cost Structure", [
        "Infrastructure & cloud hosting (Railway/PostgreSQL)",
        "AI API costs (Gemini, OpenAI, Anthropic)",
        "Legal + regulatory + Sharia compliance assessment",
        "Sales & business development (outreach + events)",
        "First technical hire (post-funding)",
        "Security audit -- PQC third-party validation",
    ], bg=LIGHT_BG, header_bg=(100, 40, 0))

    # REVENUE STREAMS
    rev_w = TW - half_w - c3
    block(pdf, x4, y2, rev_w, row2_h, "Revenue Streams", [
        "Enterprise pilot: $10K-$15K/month",
        "Enterprise full: $20K-$35K/month",
        "API per-validation: $0.01-$0.05/call",
        "B2C SaaS: $149-$499/month",
        "White-label engine: $100K+ setup",
        "TAM $5.4B  |  SAM $540M  |  Break-even Q4 2026",
    ], bg=LIGHT_BG, header_bg=GREEN_DK)

    out = os.path.join(OUTPUT_DIR, "OMNIX_Business_Model_Canvas.pdf")
    pdf.output(out)
    size_kb = os.path.getsize(out) / 1024
    print(f"Generated: {out}")
    print(f"File size: {size_kb:.1f} KB")


if __name__ == "__main__":
    generate()
