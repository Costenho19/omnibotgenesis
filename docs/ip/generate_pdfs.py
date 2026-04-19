#!/usr/bin/env python3
"""
OMNIX QUANTUM LTD — USPTO Provisional Patent Application PDF Generator
Generates professional PDFs for all 3 patent families.
"""

import os
import re
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    HRFlowable, KeepTogether, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame

OMNIX_NAVY   = HexColor("#0A1628")
OMNIX_BLUE   = HexColor("#1E3A5F")
OMNIX_GOLD   = HexColor("#C9A84C")
OMNIX_LIGHT  = HexColor("#E8EEF4")
OMNIX_GRAY   = HexColor("#6B7280")
OMNIX_MID    = HexColor("#374151")

TODAY = date.today().strftime("%B %d, %Y")

FAMILIES = [
    {
        "docket":   "OMNIX-PAT-2026-001",
        "title":    "GOVERNANCE CONTROL ARCHITECTURE FOR AUTOMATED DECISION SYSTEMS WITH SEQUENTIAL CHECKPOINT PIPELINE AND EXECUTION BOUNDARY ENFORCEMENT",
        "short":    "Family 1 — Governance Control Architecture",
        "spec":     "family_1/SPECIFICATION_FAMILY1.md",
        "pdf":      "OMNIX_PAT_2026_001_PROVISIONAL.pdf",
    },
    {
        "docket":   "OMNIX-PAT-2026-002",
        "title":    "NON-MARKOVIAN MEMORY KERNEL FOR TIME-SERIES REGIME CLASSIFICATION WITH CONFIDENCE-ADAPTIVE DECISION MAGNITUDE MODULATION",
        "short":    "Family 2 — Non-Markovian Memory Kernel + CAES",
        "spec":     "family_2/SPECIFICATION_FAMILY2.md",
        "pdf":      "OMNIX_PAT_2026_002_PROVISIONAL.pdf",
    },
    {
        "docket":   "OMNIX-PAT-2026-003",
        "title":    "ETHICAL AND QUANTUM-SECURE EXECUTION FRAMEWORK WITH MULTI-TIER COMPLIANCE ENGINE AND DUAL-LAYER POST-QUANTUM BIOMETRIC AUTHORIZATION",
        "short":    "Family 3 — Sharia Compliance + PQC Voice Auth",
        "spec":     "family_3/SPECIFICATION_FAMILY3.md",
        "pdf":      "OMNIX_PAT_2026_003_PROVISIONAL.pdf",
    },
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPEC_DIR = os.path.join(BASE_DIR, "provisional_applications")
OUT_DIR  = os.path.join(BASE_DIR, "provisional_applications", "pdf_exports")
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Page numbering canvas
# ---------------------------------------------------------------------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        page_num = self._pageNumber
        self.setFont("Helvetica", 8)
        self.setFillColor(OMNIX_GRAY)
        self.drawRightString(
            letter[0] - 0.75 * inch,
            0.45 * inch,
            f"Page {page_num} of {page_count}"
        )


# ---------------------------------------------------------------------------
# Header / Footer
# ---------------------------------------------------------------------------
def make_header_footer(docket, title_short):
    def on_page(canvas_obj, doc):
        canvas_obj.saveState()
        w, h = letter

        # ── Top bar ──────────────────────────────────────────────────────
        canvas_obj.setFillColor(OMNIX_NAVY)
        canvas_obj.rect(0, h - 0.65 * inch, w, 0.65 * inch, fill=1, stroke=0)

        # Company name (left)
        canvas_obj.setFillColor(white)
        canvas_obj.setFont("Helvetica-Bold", 11)
        canvas_obj.drawString(0.75 * inch, h - 0.42 * inch, "OMNIX QUANTUM LTD")

        # Gold accent line under company name
        canvas_obj.setFillColor(OMNIX_GOLD)
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawString(0.75 * inch, h - 0.55 * inch, "DECISION GOVERNANCE INFRASTRUCTURE")

        # Docket (right)
        canvas_obj.setFillColor(OMNIX_GOLD)
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.drawRightString(w - 0.75 * inch, h - 0.40 * inch, docket)
        canvas_obj.setFillColor(HexColor("#AABDD0"))
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawRightString(w - 0.75 * inch, h - 0.53 * inch, "PROVISIONAL PATENT APPLICATION")

        # ── Gold rule under header ────────────────────────────────────────
        canvas_obj.setStrokeColor(OMNIX_GOLD)
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(0, h - 0.67 * inch, w, h - 0.67 * inch)

        # ── Bottom bar ───────────────────────────────────────────────────
        canvas_obj.setStrokeColor(OMNIX_LIGHT)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(0.75 * inch, 0.65 * inch, w - 0.75 * inch, 0.65 * inch)

        canvas_obj.setFillColor(OMNIX_GRAY)
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawString(0.75 * inch, 0.45 * inch,
            f"CONFIDENTIAL — PATENT PENDING — {docket} — Filed: [DATE OF FILING]")

        canvas_obj.restoreState()

    return on_page


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def build_styles():
    s = {}

    s["cover_company"] = ParagraphStyle(
        "cover_company",
        fontName="Helvetica-Bold", fontSize=22,
        textColor=OMNIX_NAVY, alignment=TA_CENTER, spaceAfter=4
    )
    s["cover_tagline"] = ParagraphStyle(
        "cover_tagline",
        fontName="Helvetica", fontSize=10,
        textColor=OMNIX_GOLD, alignment=TA_CENTER, spaceAfter=24
    )
    s["cover_label"] = ParagraphStyle(
        "cover_label",
        fontName="Helvetica", fontSize=9,
        textColor=OMNIX_GRAY, alignment=TA_CENTER, spaceAfter=4
    )
    s["cover_title"] = ParagraphStyle(
        "cover_title",
        fontName="Helvetica-Bold", fontSize=13,
        textColor=OMNIX_NAVY, alignment=TA_CENTER,
        spaceAfter=8, leading=18
    )
    s["cover_docket"] = ParagraphStyle(
        "cover_docket",
        fontName="Helvetica-Bold", fontSize=11,
        textColor=OMNIX_GOLD, alignment=TA_CENTER, spaceAfter=6
    )
    s["cover_meta"] = ParagraphStyle(
        "cover_meta",
        fontName="Helvetica", fontSize=9,
        textColor=OMNIX_MID, alignment=TA_CENTER, spaceAfter=3
    )
    s["h1"] = ParagraphStyle(
        "h1",
        fontName="Helvetica-Bold", fontSize=13,
        textColor=OMNIX_NAVY, spaceBefore=18, spaceAfter=6,
        leading=16
    )
    s["h2"] = ParagraphStyle(
        "h2",
        fontName="Helvetica-Bold", fontSize=11,
        textColor=OMNIX_BLUE, spaceBefore=14, spaceAfter=4,
        leading=14
    )
    s["h3"] = ParagraphStyle(
        "h3",
        fontName="Helvetica-Bold", fontSize=10,
        textColor=OMNIX_MID, spaceBefore=10, spaceAfter=3,
        leading=13
    )
    s["h4"] = ParagraphStyle(
        "h4",
        fontName="Helvetica-BoldOblique", fontSize=9,
        textColor=OMNIX_MID, spaceBefore=8, spaceAfter=2,
        leading=12
    )
    s["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica", fontSize=9,
        textColor=black, leading=13, spaceAfter=5,
        alignment=TA_JUSTIFY
    )
    s["body_bold"] = ParagraphStyle(
        "body_bold",
        fontName="Helvetica-Bold", fontSize=9,
        textColor=OMNIX_NAVY, leading=13, spaceAfter=4,
        alignment=TA_JUSTIFY
    )
    s["bullet"] = ParagraphStyle(
        "bullet",
        fontName="Helvetica", fontSize=9,
        textColor=black, leading=13, spaceAfter=3,
        leftIndent=18, firstLineIndent=0,
        alignment=TA_JUSTIFY
    )
    s["code"] = ParagraphStyle(
        "code",
        fontName="Courier", fontSize=8,
        textColor=OMNIX_NAVY, leading=12, spaceAfter=4,
        leftIndent=24, backColor=OMNIX_LIGHT,
        borderPadding=(4, 6, 4, 6)
    )
    s["claim"] = ParagraphStyle(
        "claim",
        fontName="Helvetica", fontSize=9,
        textColor=black, leading=13, spaceAfter=6,
        leftIndent=12, alignment=TA_JUSTIFY
    )
    return s


# ---------------------------------------------------------------------------
# Markdown → ReportLab flowables
# ---------------------------------------------------------------------------
def md_to_flowables(text, styles):
    flowables = []
    lines = text.split("\n")
    i = 0

    def esc(t):
        t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Bold **text**
        t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
        # Italic *text*
        t = re.sub(r'\*(.+?)\*', r'<i>\1</i>', t)
        # Code `text`
        t = re.sub(r'`(.+?)`', r'<font name="Courier">\1</font>', t)
        return t

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # H1
        if stripped.startswith("# "):
            text_content = esc(stripped[2:].strip())
            flowables.append(Spacer(1, 0.12 * inch))
            flowables.append(HRFlowable(width="100%", thickness=1.5,
                                        color=OMNIX_GOLD, spaceAfter=4))
            flowables.append(Paragraph(text_content, styles["h1"]))
            i += 1
            continue

        # H2
        if stripped.startswith("## "):
            text_content = esc(stripped[3:].strip())
            flowables.append(Paragraph(text_content, styles["h2"]))
            flowables.append(HRFlowable(width="60%", thickness=0.5,
                                        color=OMNIX_LIGHT, spaceAfter=2))
            i += 1
            continue

        # H3
        if stripped.startswith("### "):
            flowables.append(Paragraph(esc(stripped[4:].strip()), styles["h3"]))
            i += 1
            continue

        # H4
        if stripped.startswith("#### "):
            flowables.append(Paragraph(esc(stripped[5:].strip()), styles["h4"]))
            i += 1
            continue

        # HR
        if stripped.startswith("---"):
            flowables.append(HRFlowable(width="100%", thickness=0.5,
                                        color=OMNIX_LIGHT,
                                        spaceBefore=6, spaceAfter=6))
            i += 1
            continue

        # Code block
        if stripped.startswith("```"):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            code_text = "\n".join(code_lines)
            flowables.append(Paragraph(
                code_text.replace(" ", "&nbsp;").replace("\n", "<br/>"),
                styles["code"]
            ))
            continue

        # Bullet
        if stripped.startswith("- ") or stripped.startswith("* "):
            content = esc(stripped[2:].strip())
            flowables.append(Paragraph(f"• &nbsp;{content}", styles["bullet"]))
            i += 1
            continue

        # Numbered list
        if re.match(r'^\d+\.', stripped):
            content = esc(re.sub(r'^\d+\.\s*', '', stripped))
            flowables.append(Paragraph(f"• &nbsp;{content}", styles["bullet"]))
            i += 1
            continue

        # Bold-only line (claim / section label)
        if stripped.startswith("**") and stripped.endswith("**") and stripped.count("**") == 2:
            flowables.append(Paragraph(esc(stripped), styles["body_bold"]))
            i += 1
            continue

        # Claim lines
        if re.match(r'^\*\*Claim \d+', stripped):
            flowables.append(Paragraph(esc(stripped), styles["claim"]))
            i += 1
            continue

        # Normal paragraph
        flowables.append(Paragraph(esc(stripped), styles["body"]))
        i += 1

    return flowables


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------
def build_cover(family, styles):
    elems = []

    elems.append(Spacer(1, 0.5 * inch))

    # Navy box with company name
    data = [[Paragraph("OMNIX QUANTUM LTD", styles["cover_company"])]]
    t = Table(data, colWidths=[5.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), OMNIX_NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("BOX",           (0, 0), (-1, -1), 1.5, OMNIX_GOLD),
    ]))
    elems.append(t)

    elems.append(Spacer(1, 0.06 * inch))
    elems.append(Paragraph("DECISION GOVERNANCE INFRASTRUCTURE", styles["cover_tagline"]))
    elems.append(Spacer(1, 0.3 * inch))

    elems.append(HRFlowable(width="80%", thickness=1, color=OMNIX_GOLD,
                             spaceBefore=4, spaceAfter=16))

    elems.append(Paragraph("UNITED STATES PATENT AND TRADEMARK OFFICE", styles["cover_label"]))
    elems.append(Paragraph("PROVISIONAL PATENT APPLICATION", styles["cover_label"]))
    elems.append(Spacer(1, 0.2 * inch))

    elems.append(Paragraph("TITLE OF INVENTION:", styles["cover_label"]))
    elems.append(Spacer(1, 0.06 * inch))

    # Title box
    data2 = [[Paragraph(family["title"], styles["cover_title"])]]
    t2 = Table(data2, colWidths=[5.5 * inch])
    t2.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), OMNIX_LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("BOX",           (0, 0), (-1, -1), 0.75, OMNIX_BLUE),
    ]))
    elems.append(t2)
    elems.append(Spacer(1, 0.25 * inch))

    elems.append(HRFlowable(width="50%", thickness=0.5, color=OMNIX_LIGHT,
                             spaceBefore=4, spaceAfter=16))

    # Meta table
    meta = [
        ["Docket Number:", family["docket"]],
        ["Applicant / Inventor:", "Harold Alberto Nunes Rodelo"],
        ["Nationality:", "United Kingdom"],
        ["Entity Status:", "Micro Entity (37 C.F.R. § 1.29)"],
        ["Filing Basis:", "35 U.S.C. § 111(b) — Provisional Application"],
        ["Date Prepared:", TODAY],
        ["Date of Filing:", "April 19, 2026"],
    ]
    meta_style = [
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("TEXTCOLOR",     (0, 0), (0, -1), OMNIX_NAVY),
        ("TEXTCOLOR",     (1, 0), (1, -1), OMNIX_MID),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, OMNIX_LIGHT]),
        ("BOX",           (0, 0), (-1, -1), 0.5, OMNIX_LIGHT),
        ("INNERGRID",     (0, 0), (-1, -1), 0.25, OMNIX_LIGHT),
    ]
    mt = Table(meta, colWidths=[2.1 * inch, 3.4 * inch])
    mt.setStyle(TableStyle(meta_style))
    elems.append(mt)

    elems.append(Spacer(1, 0.35 * inch))
    elems.append(HRFlowable(width="80%", thickness=1, color=OMNIX_GOLD,
                             spaceBefore=4, spaceAfter=12))

    notice = (
        "This document constitutes a Provisional Patent Application filed pursuant to 35 U.S.C. § 111(b). "
        "It establishes a priority date and grants twelve (12) months from the filing date to submit a "
        "corresponding non-provisional application. This application has not been examined and does not "
        "confer patent rights independently. CONFIDENTIAL — NOT FOR DISTRIBUTION."
    )
    elems.append(Paragraph(notice, ParagraphStyle(
        "notice", fontName="Helvetica", fontSize=7.5,
        textColor=OMNIX_GRAY, alignment=TA_JUSTIFY, leading=11
    )))

    elems.append(PageBreak())
    return elems


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
def generate_pdf(family, styles):
    out_path = os.path.join(OUT_DIR, family["pdf"])
    spec_path = os.path.join(SPEC_DIR, family["spec"])

    with open(spec_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    on_page = make_header_footer(family["docket"], family["short"])

    doc = SimpleDocTemplate(
        out_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.75 * inch,
        title=family["title"],
        author="Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD",
        subject=family["docket"],
        creator="OMNIX Patent Document Generator",
    )

    story = []
    story += build_cover(family, styles)
    story += md_to_flowables(md_text, styles)

    doc.build(
        story,
        onFirstPage=on_page,
        onLaterPages=on_page,
        canvasmaker=NumberedCanvas,
    )
    print(f"  ✓  {family['pdf']}  →  {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    styles = build_styles()
    print(f"\nOMNIX QUANTUM LTD — USPTO Provisional Patent PDF Generator")
    print(f"Output directory: {OUT_DIR}\n")
    paths = []
    for fam in FAMILIES:
        paths.append(generate_pdf(fam, styles))
    print(f"\nDone — {len(paths)} PDFs generated.\n")
