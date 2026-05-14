"""
PDF Generator — RFC-ATF-2
Professional IETF-style document with OMNIX logo.
"""
import re, os, textwrap
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Image
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# ── Colours ──────────────────────────────────────────────────────────────────
OMNIX_DARK   = HexColor("#0a0a0f")
OMNIX_BLUE   = HexColor("#3b82f6")
OMNIX_CYAN   = HexColor("#06b6d4")
OMNIX_PURPLE = HexColor("#8b5cf6")
OMNIX_GRAY   = HexColor("#6b7280")
OMNIX_LIGHT  = HexColor("#f8fafc")
OMNIX_MID    = HexColor("#e2e8f0")
OMNIX_CODE   = HexColor("#1e293b")
OMNIX_CODETX = HexColor("#e2e8f0")

W, H = A4
MARGIN_L = 22*mm
MARGIN_R = 22*mm
MARGIN_T = 28*mm
MARGIN_B = 25*mm

# ── Page template ─────────────────────────────────────────────────────────────
def make_page(canvas_obj, doc):
    canvas_obj.saveState()
    page_w, page_h = A4

    # Top rule
    canvas_obj.setStrokeColor(OMNIX_BLUE)
    canvas_obj.setLineWidth(1.5)
    canvas_obj.line(MARGIN_L, page_h - MARGIN_T + 6*mm,
                    page_w - MARGIN_R, page_h - MARGIN_T + 6*mm)

    # Header text
    canvas_obj.setFont("Courier", 7.5)
    canvas_obj.setFillColor(OMNIX_GRAY)
    canvas_obj.drawString(MARGIN_L, page_h - MARGIN_T + 8*mm,
                          "OMNIX QUANTUM Open Standard")
    canvas_obj.drawRightString(page_w - MARGIN_R, page_h - MARGIN_T + 8*mm,
                               "RFC-ATF-2 — Runtime Governance Continuity")

    # Bottom rule
    canvas_obj.setStrokeColor(OMNIX_MID)
    canvas_obj.setLineWidth(0.8)
    canvas_obj.line(MARGIN_L, MARGIN_B - 4*mm,
                    page_w - MARGIN_R, MARGIN_B - 4*mm)

    # Footer
    canvas_obj.setFont("Courier", 7.5)
    canvas_obj.setFillColor(OMNIX_GRAY)
    canvas_obj.drawString(MARGIN_L, MARGIN_B - 8.5*mm, "Nunes, H.           [Standards Track]")
    canvas_obj.drawCentredString(page_w / 2, MARGIN_B - 8.5*mm,
                                 "May 2026")
    canvas_obj.drawRightString(page_w - MARGIN_R, MARGIN_B - 8.5*mm,
                               f"[Page {doc.page}]")
    canvas_obj.restoreState()


def cover_page(canvas_obj, doc):
    canvas_obj.saveState()
    page_w, page_h = A4

    # Dark background
    canvas_obj.setFillColor(OMNIX_DARK)
    canvas_obj.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Top accent bar
    canvas_obj.setFillColor(OMNIX_BLUE)
    canvas_obj.rect(0, page_h - 6*mm, page_w, 6*mm, fill=1, stroke=0)

    # Bottom accent bar
    canvas_obj.setFillColor(OMNIX_PURPLE)
    canvas_obj.rect(0, 0, page_w, 4*mm, fill=1, stroke=0)

    # Vertical left stripe
    canvas_obj.setFillColor(OMNIX_CYAN)
    canvas_obj.rect(0, 0, 3*mm, page_h, fill=1, stroke=0)

    # Logo
    logo_paths = [
        "docs/business/omnix_logo.png",
        "assets/omnix_logo.png",
        "omnix_dashboard/static/images/omnix_logo.png",
    ]
    logo_path = None
    for lp in logo_paths:
        if os.path.exists(lp):
            logo_path = lp
            break

    logo_y = page_h - 40*mm
    if logo_path:
        try:
            canvas_obj.drawImage(logo_path, MARGIN_L + 3*mm, logo_y,
                                 width=38*mm, height=14*mm,
                                 preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # OMNIX QUANTUM text fallback if logo fails
    canvas_obj.setFont("Helvetica-Bold", 11)
    canvas_obj.setFillColor(OMNIX_CYAN)
    canvas_obj.drawString(MARGIN_L + 3*mm, logo_y - 6*mm, "OMNIX QUANTUM LTD")

    # Document classification
    canvas_obj.setFont("Courier", 8)
    canvas_obj.setFillColor(OMNIX_BLUE)
    canvas_obj.drawString(MARGIN_L + 3*mm, page_h - 55*mm,
                          "STANDARDS TRACK  ·  OPEN STANDARD  ·  MAY 2026")

    # Horizontal rule
    canvas_obj.setStrokeColor(OMNIX_BLUE)
    canvas_obj.setLineWidth(0.8)
    canvas_obj.line(MARGIN_L + 3*mm, page_h - 60*mm,
                    page_w - MARGIN_R, page_h - 60*mm)

    # Main title
    canvas_obj.setFont("Helvetica-Bold", 22)
    canvas_obj.setFillColor(white)
    canvas_obj.drawString(MARGIN_L + 3*mm, page_h - 78*mm, "RFC-ATF-2")

    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.setFillColor(OMNIX_CYAN)
    canvas_obj.drawString(MARGIN_L + 3*mm, page_h - 89*mm,
                          "Agent Trust Fabric")
    canvas_obj.drawString(MARGIN_L + 3*mm, page_h - 97*mm,
                          "Runtime Governance Continuity")

    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.setFillColor(OMNIX_GRAY)
    canvas_obj.drawString(MARGIN_L + 3*mm, page_h - 108*mm,
                          "Extension to RFC-ATF-1  ·  Version 1.0.0")

    # Horizontal rule
    canvas_obj.setStrokeColor(OMNIX_PURPLE)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(MARGIN_L + 3*mm, page_h - 115*mm,
                    page_w - MARGIN_R, page_h - 115*mm)

    # Abstract box
    abs_y = page_h - 120*mm
    abs_h = 68*mm
    canvas_obj.setFillColor(HexColor("#0f1729"))
    canvas_obj.roundRect(MARGIN_L + 3*mm, abs_y - abs_h,
                         page_w - MARGIN_L - MARGIN_R - 3*mm, abs_h,
                         4*mm, fill=1, stroke=0)

    canvas_obj.setFont("Helvetica-Bold", 7.5)
    canvas_obj.setFillColor(OMNIX_BLUE)
    canvas_obj.drawString(MARGIN_L + 8*mm, abs_y - 7*mm, "ABSTRACT")

    abstract = (
        "RFC-ATF-2 extends the Agent Trust Fabric delegation protocol "
        "(RFC-ATF-1, DOI: 10.5281/zenodo.20155016) to cover the full "
        "execution lifecycle of long-running autonomous agent workflows. "
        "RFC-ATF-1 established cryptographic boundary attestation: proof "
        "that an agent possessed a valid, human-originated authority grant "
        "at the moment of execution admission. RFC-ATF-2 addresses the "
        "Runtime Governance Gap — the structural absence of continuous "
        "governability supervision between admission and completion. "
        "This extension introduces the Runtime Continuity Record (RCR), "
        "the Continuity Eligibility Score (CES), the Authority Fragmentation "
        "Guard (AFG), and the Reauthorization Challenge (RC) Protocol. "
        "Eight new invariants (RGC-INV-001–008) extend the ATF stack to "
        "14 total formally model-checkable invariants. "
        "The reference implementation is currently running in production."
    )

    canvas_obj.setFont("Helvetica", 8.2)
    canvas_obj.setFillColor(HexColor("#cbd5e1"))
    text_obj = canvas_obj.beginText(MARGIN_L + 8*mm, abs_y - 16*mm)
    text_obj.setFont("Helvetica", 8.2)
    text_obj.setFillColor(HexColor("#cbd5e1"))
    text_obj.setLeading(12)
    max_w = page_w - MARGIN_L - MARGIN_R - 13*mm
    words = abstract.split()
    line = ""
    for word in words:
        test = (line + " " + word).strip()
        if canvas_obj.stringWidth(test, "Helvetica", 8.2) < max_w:
            line = test
        else:
            text_obj.textLine(line)
            line = word
    if line:
        text_obj.textLine(line)
    canvas_obj.drawText(text_obj)

    # Metadata grid
    meta_y = page_h - 200*mm
    canvas_obj.setStrokeColor(HexColor("#1e293b"))
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(MARGIN_L + 3*mm, meta_y + 4*mm,
                    page_w - MARGIN_R, meta_y + 4*mm)

    meta = [
        ("Author", "Harold Nunes  ·  Editor"),
        ("Organization", "OMNIX QUANTUM LTD  ·  United Kingdom"),
        ("Extends", "RFC-ATF-1  (DOI: 10.5281/zenodo.20155016)"),
        ("SSRN Reference", "6757339"),
        ("Signing Algorithm", "ML-DSA-65  (Dilithium-3, FIPS 204)"),
        ("Invariants", "14 total  (ATF-INV-001–006 + RGC-INV-001–008)"),
        ("Status", "Draft — Zenodo submission in progress"),
        ("DOI", "Pending assignment"),
        ("Contact", "standards@omnixquantum.com"),
    ]

    row_h = 7.5*mm
    for i, (label, value) in enumerate(meta):
        y = meta_y - i * row_h
        if i % 2 == 0:
            canvas_obj.setFillColor(HexColor("#0f1729"))
            canvas_obj.rect(MARGIN_L + 3*mm, y - row_h + 1.5*mm,
                            page_w - MARGIN_L - MARGIN_R - 3*mm, row_h,
                            fill=1, stroke=0)
        canvas_obj.setFont("Helvetica-Bold", 7.5)
        canvas_obj.setFillColor(OMNIX_BLUE)
        canvas_obj.drawString(MARGIN_L + 8*mm, y - row_h + 4*mm, label)
        canvas_obj.setFont("Helvetica", 7.5)
        canvas_obj.setFillColor(HexColor("#e2e8f0"))
        canvas_obj.drawString(MARGIN_L + 52*mm, y - row_h + 4*mm, value)

    # Footer
    canvas_obj.setFont("Courier", 7)
    canvas_obj.setFillColor(OMNIX_GRAY)
    canvas_obj.drawCentredString(page_w / 2, 12*mm,
        "Copyright © 2026 OMNIX QUANTUM LTD  ·  This document may be reproduced for implementation purposes.")

    canvas_obj.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["body"] = ParagraphStyle("body",
        fontName="Helvetica", fontSize=9.5, leading=15,
        textColor=HexColor("#1e293b"), alignment=TA_JUSTIFY,
        spaceBefore=3, spaceAfter=4,
        leftIndent=0, rightIndent=0)

    styles["h1"] = ParagraphStyle("h1",
        fontName="Helvetica-Bold", fontSize=13, leading=18,
        textColor=OMNIX_BLUE, spaceBefore=14, spaceAfter=5,
        borderPad=0)

    styles["h2"] = ParagraphStyle("h2",
        fontName="Helvetica-Bold", fontSize=10.5, leading=15,
        textColor=HexColor("#1e40af"), spaceBefore=10, spaceAfter=4)

    styles["h3"] = ParagraphStyle("h3",
        fontName="Helvetica-Bold", fontSize=9.5, leading=14,
        textColor=HexColor("#374151"), spaceBefore=7, spaceAfter=3)

    styles["code"] = ParagraphStyle("code",
        fontName="Courier", fontSize=7.8, leading=11.5,
        textColor=OMNIX_CODETX, backColor=OMNIX_CODE,
        spaceBefore=5, spaceAfter=5,
        leftIndent=6, rightIndent=6,
        borderPad=5)

    styles["meta"] = ParagraphStyle("meta",
        fontName="Courier", fontSize=8, leading=12,
        textColor=OMNIX_GRAY, spaceBefore=2, spaceAfter=2)

    styles["bullet"] = ParagraphStyle("bullet",
        fontName="Helvetica", fontSize=9.5, leading=14,
        textColor=HexColor("#1e293b"), leftIndent=12,
        spaceBefore=1, spaceAfter=1)

    styles["toc_title"] = ParagraphStyle("toc_title",
        fontName="Helvetica-Bold", fontSize=11, leading=16,
        textColor=OMNIX_BLUE, spaceBefore=8, spaceAfter=6)

    styles["toc_entry"] = ParagraphStyle("toc_entry",
        fontName="Helvetica", fontSize=9, leading=13,
        textColor=HexColor("#374151"), leftIndent=0, spaceBefore=1)

    styles["toc_sub"] = ParagraphStyle("toc_sub",
        fontName="Helvetica", fontSize=8.5, leading=12,
        textColor=HexColor("#6b7280"), leftIndent=10, spaceBefore=0)

    styles["caption"] = ParagraphStyle("caption",
        fontName="Helvetica-Oblique", fontSize=8, leading=11,
        textColor=OMNIX_GRAY, alignment=TA_CENTER,
        spaceBefore=2, spaceAfter=6)

    return styles


# ── Content parser ────────────────────────────────────────────────────────────
def parse_and_build(md_text, styles):
    story = []
    lines = md_text.split("\n")
    i = 0
    in_code = False
    code_buf = []

    def flush_code():
        nonlocal code_buf
        if not code_buf:
            return
        raw = "\n".join(code_buf)
        # Escape XML special chars for Paragraph
        safe = raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Split into lines for readability
        for ln in safe.split("\n"):
            story.append(Paragraph(ln if ln else " ", styles["code"]))
        story.append(Spacer(1, 3))
        code_buf.clear()

    def add_section_rule():
        story.append(Spacer(1, 3))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=OMNIX_MID, spaceAfter=4))

    while i < len(lines):
        line = lines[i]

        # Code block toggle
        if line.strip().startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Skip the outer ``` wrapping of the whole RFC doc
        if stripped == "```":
            i += 1
            continue

        # Section headings (e.g. "1.  Introduction" or "4.1.  Position")
        sec_match = re.match(r'^(\d+(?:\.\d+)*)\.?\s{2,}(.+)$', stripped)
        if sec_match:
            num = sec_match.group(1)
            title = sec_match.group(2)
            depth = num.count(".")
            label = f"{num}.  {title}"
            if depth == 0:
                add_section_rule()
                story.append(Paragraph(label, styles["h1"]))
            elif depth == 1:
                story.append(Paragraph(label, styles["h2"]))
            else:
                story.append(Paragraph(label, styles["h3"]))
            i += 1
            continue

        # Appendix headings
        app_match = re.match(r'^(Appendix\s+\w+|A\.\d+|B\.\d+|C\.\d+)[\s\.]+(.+)$', stripped)
        if app_match:
            story.append(Paragraph(stripped, styles["h2"]))
            i += 1
            continue

        # Top-level non-numbered headers (Abstract, ToC, etc.)
        if stripped in ("Abstract", "Status of This Memo", "Copyright Notice",
                        "Acknowledgements", "Table of Contents",
                        "References", "Author's Address"):
            add_section_rule()
            story.append(Paragraph(stripped, styles["h1"]))
            i += 1
            continue

        # Indented text (RFC-style body, 3+ spaces)
        if line.startswith("   ") and stripped:
            safe = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            # Bold inline markers
            safe = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', safe)
            safe = re.sub(r'`(.+?)`', r'<font name="Courier" size="8.5">\1</font>', safe)

            # Detect list item  (a) (b) etc or bullet
            if re.match(r'^\([a-z]\)', safe) or re.match(r'^\d+\.', safe):
                story.append(Paragraph(safe, styles["bullet"]))
            else:
                story.append(Paragraph(safe, styles["body"]))
            i += 1
            continue

        # Non-indented lines with content
        if stripped:
            safe = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            safe = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', safe)
            safe = re.sub(r'`(.+?)`', r'<font name="Courier" size="8.5">\1</font>', safe)

            # Table-like ASCII (│ or ┌)
            if "│" in stripped or "├" in stripped or "┌" in stripped or "└" in stripped:
                story.append(Paragraph(
                    f'<font name="Courier" size="7.5">{safe}</font>',
                    styles["meta"]))
            else:
                story.append(Paragraph(safe, styles["body"]))
        else:
            story.append(Spacer(1, 4))

        i += 1

    if in_code:
        flush_code()

    return story


# ── Table of Contents ─────────────────────────────────────────────────────────
TOC_ENTRIES = [
    ("1.", "Introduction", False),
    ("2.", "Problem Statement: The Runtime Governance Gap", False),
    ("3.", "Conventions and Terminology", False),
    ("4.", "Architecture: RGC Layer", False),
    ("  4.1.", "Position in the ATF Stack", True),
    ("  4.2.", "Session Lifecycle", True),
    ("  4.3.", "Relationship to TAR", True),
    ("5.", "Runtime Continuity Record (RCR)", False),
    ("6.", "Continuity Eligibility Score (CES)", False),
    ("7.", "Continuity Chain", False),
    ("8.", "Authority Fragmentation Guard (AFG)", False),
    ("9.", "Escalation Protocol", False),
    ("10.", "Reauthorization Challenge (RC)", False),
    ("11.", "Sampling Strategy", False),
    ("12.", "RGC Invariants", False),
    ("13.", "Wire Format", False),
    ("14.", "Verification Protocol", False),
    ("15.", "Persistence Schema", False),
    ("16.", "API Endpoints", False),
    ("17.", "Security Considerations", False),
    ("18.", "Compliance Mapping", False),
    ("19.", "Extension Points", False),
    ("20.", "Relationship to RFC-ATF-1", False),
    ("21.", "References", False),
    ("22.", "Appendix A — CES Computation Examples", False),
    ("23.", "Appendix B — RGC Compliance Checklist", False),
    ("24.", "Appendix C — Implementation Notes", False),
]


def build_toc(styles):
    items = []
    items.append(Paragraph("Table of Contents", styles["toc_title"]))
    items.append(HRFlowable(width="100%", thickness=0.5,
                            color=OMNIX_MID, spaceAfter=6))
    for num, title, sub in TOC_ENTRIES:
        label = f"{num}  {title}"
        style = styles["toc_sub"] if sub else styles["toc_entry"]
        items.append(Paragraph(label, style))
    return items


# ── Invariants summary table ───────────────────────────────────────────────────
def build_invariants_table(styles):
    rows = [
        ["Invariant", "Standard", "Property"],
        ["ATF-INV-001", "RFC-ATF-1", "Monotonic Authority Reduction (MAR)"],
        ["ATF-INV-002", "RFC-ATF-1", "All DRs signed by delegating principal"],
        ["ATF-INV-003", "RFC-ATF-1", "Chain root traceability to Tier-1"],
        ["ATF-INV-004", "RFC-ATF-1", "No grant exceeds maximum authority budget"],
        ["ATF-INV-005", "RFC-ATF-1", "Receipt immutability"],
        ["ATF-INV-006", "RFC-ATF-1", "Independent verifiability without platform"],
        ["RGC-INV-001", "RFC-ATF-2", "Every RCR anchored to a valid TAR"],
        ["RGC-INV-002", "RFC-ATF-2", "CES computed from real-time values only"],
        ["RGC-INV-003", "RFC-ATF-2", "HALT terminates execution & revokes sub-tasks"],
        ["RGC-INV-004", "RFC-ATF-2", "Aggregate budget ≤ AFG limit"],
        ["RGC-INV-005", "RFC-ATF-2", "All RCRs PQC-signed and immutable"],
        ["RGC-INV-006", "RFC-ATF-2", "Continuity chain is acyclic and monotonic"],
        ["RGC-INV-007", "RFC-ATF-2", "CES inputs must meet freshness requirements"],
        ["RGC-INV-008", "RFC-ATF-2", "RC TTL enforced — auto-HALT on expiry"],
    ]

    col_w = [(W - MARGIN_L - MARGIN_R) * x for x in [0.22, 0.20, 0.58]]
    t = Table([[Paragraph(c, ParagraphStyle("tc",
                fontName="Helvetica-Bold" if r == 0 else "Courier",
                fontSize=8 if r == 0 else 7.8,
                textColor=white if r == 0 else (
                    HexColor("#1e40af") if rows[r][1] == "RFC-ATF-1"
                    else HexColor("#6d28d9")),
                leading=11)) for c in row] for r, row in enumerate(rows)],
        colWidths=col_w)

    ts = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), OMNIX_BLUE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [HexColor("#f8fafc"), HexColor("#eef2ff")]),
        ("GRID", (0, 0), (-1, -1), 0.4, OMNIX_MID),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 7), (-1, -1), HexColor("#faf5ff")),
    ])
    t.setStyle(ts)
    return t


# ── Main ──────────────────────────────────────────────────────────────────────
def generate():
    output_path = "docs/submissions/RFC-ATF-2.pdf"
    os.makedirs("docs/submissions", exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
        title="RFC-ATF-2: Agent Trust Fabric — Runtime Governance Continuity",
        author="Harold Nunes — OMNIX QUANTUM LTD",
        subject="Runtime Governance Continuity Extension to RFC-ATF-1",
        keywords="AI governance, ATF, post-quantum, runtime continuity, Dilithium-3"
    )

    styles = build_styles()
    story = []

    # Cover page (full-page canvas, no header/footer)
    story.append(PageBreak())

    # TOC
    story.extend(build_toc(styles))
    story.append(PageBreak())

    # Invariants summary
    story.append(Paragraph("Invariants Reference — All 14 ATF Invariants",
                           styles["h1"]))
    story.append(Spacer(1, 4))
    story.append(build_invariants_table(styles))
    story.append(Paragraph(
        "ATF-INV-001–006 are proven in TLA+ using the same formal methods "
        "methodology as AWS DynamoDB and Azure Cosmos DB. RGC-INV-001–008 "
        "are verified by the reference implementation test suite (82 tests).",
        styles["caption"]))
    story.append(PageBreak())

    # Main body — parse the RFC markdown
    with open("docs/standards/RFC-ATF-2.md", "r") as f:
        md = f.read()

    story.extend(parse_and_build(md, styles))

    # Build PDF
    # First page = cover (special template), rest = normal
    def first_page(c, d):
        cover_page(c, d)

    def later_pages(c, d):
        make_page(c, d)

    doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
    print(f"PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    generate()
