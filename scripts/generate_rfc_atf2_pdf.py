"""
PDF Generator — RFC-ATF-2
Professional IETF-style document with OMNIX logo.
"""
import re, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable
)
from reportlab.lib import colors

W, H = A4
MARGIN_L = 22*mm
MARGIN_R = 22*mm
MARGIN_T = 28*mm
MARGIN_B = 25*mm

OMNIX_DARK   = HexColor("#0a0a0f")
OMNIX_BLUE   = HexColor("#1e3a8a")
OMNIX_BLUE2  = HexColor("#3b82f6")
OMNIX_CYAN   = HexColor("#06b6d4")
OMNIX_PURPLE = HexColor("#6d28d9")
OMNIX_GRAY   = HexColor("#6b7280")
OMNIX_MID    = HexColor("#cbd5e1")
OMNIX_LIGHT  = HexColor("#f8fafc")
OMNIX_CODE_BG = HexColor("#1e293b")
OMNIX_CODE_FG = HexColor("#e2e8f0")


# ── Page templates ────────────────────────────────────────────────────────────
def make_page(c, doc):
    c.saveState()
    pw, ph = A4
    c.setStrokeColor(OMNIX_BLUE2)
    c.setLineWidth(1.5)
    c.line(MARGIN_L, ph - MARGIN_T + 6*mm, pw - MARGIN_R, ph - MARGIN_T + 6*mm)
    c.setFont("Courier", 7.5)
    c.setFillColor(OMNIX_GRAY)
    c.drawString(MARGIN_L, ph - MARGIN_T + 8.5*mm, "OMNIX QUANTUM Open Standard")
    c.drawRightString(pw - MARGIN_R, ph - MARGIN_T + 8.5*mm,
                      "RFC-ATF-2 — Runtime Governance Continuity")
    c.setStrokeColor(OMNIX_MID)
    c.setLineWidth(0.6)
    c.line(MARGIN_L, MARGIN_B - 4*mm, pw - MARGIN_R, MARGIN_B - 4*mm)
    c.setFont("Courier", 7.5)
    c.setFillColor(OMNIX_GRAY)
    c.drawString(MARGIN_L, MARGIN_B - 8.5*mm, "Nunes, H.           [Standards Track]")
    c.drawCentredString(pw / 2, MARGIN_B - 8.5*mm, "May 2026")
    c.drawRightString(pw - MARGIN_R, MARGIN_B - 8.5*mm, f"[Page {doc.page}]")
    c.restoreState()


def cover_page(c, doc):
    c.saveState()
    pw, ph = A4

    # Background
    c.setFillColor(OMNIX_DARK)
    c.rect(0, 0, pw, ph, fill=1, stroke=0)

    # Accent bars
    c.setFillColor(OMNIX_BLUE2)
    c.rect(0, ph - 6*mm, pw, 6*mm, fill=1, stroke=0)
    c.setFillColor(OMNIX_PURPLE)
    c.rect(0, 0, pw, 4*mm, fill=1, stroke=0)
    c.setFillColor(OMNIX_CYAN)
    c.rect(0, 0, 3*mm, ph, fill=1, stroke=0)

    # Logo
    for lp in ["docs/business/omnix_logo.png", "assets/omnix_logo.png",
               "omnix_dashboard/static/images/omnix_logo.png"]:
        if os.path.exists(lp):
            try:
                c.drawImage(lp, MARGIN_L + 4*mm, ph - 38*mm,
                            width=42*mm, height=14*mm,
                            preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
            break

    # Classification tag
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(OMNIX_CYAN)
    c.drawString(MARGIN_L + 4*mm, ph - 52*mm,
                 "STANDARDS TRACK  ·  OPEN STANDARD  ·  MAY 2026")

    # Rule
    c.setStrokeColor(OMNIX_BLUE2)
    c.setLineWidth(0.8)
    c.line(MARGIN_L + 4*mm, ph - 57*mm, pw - MARGIN_R, ph - 57*mm)

    # Title
    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(white)
    c.drawString(MARGIN_L + 4*mm, ph - 76*mm, "RFC-ATF-2")
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(OMNIX_CYAN)
    c.drawString(MARGIN_L + 4*mm, ph - 88*mm, "Agent Trust Fabric")
    c.drawString(MARGIN_L + 4*mm, ph - 97*mm, "Runtime Governance Continuity")
    c.setFont("Helvetica", 10)
    c.setFillColor(OMNIX_GRAY)
    c.drawString(MARGIN_L + 4*mm, ph - 108*mm,
                 "Extension to RFC-ATF-1  ·  Version 1.0.0")

    c.setStrokeColor(OMNIX_PURPLE)
    c.setLineWidth(0.5)
    c.line(MARGIN_L + 4*mm, ph - 114*mm, pw - MARGIN_R, ph - 114*mm)

    # Abstract box
    abs_top = ph - 119*mm
    abs_h   = 66*mm
    c.setFillColor(HexColor("#0f172a"))
    c.roundRect(MARGIN_L + 4*mm, abs_top - abs_h,
                pw - MARGIN_L - MARGIN_R - 4*mm, abs_h, 3*mm, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(OMNIX_BLUE2)
    c.drawString(MARGIN_L + 9*mm, abs_top - 7*mm, "ABSTRACT")

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
    c.setFont("Helvetica", 8.2)
    c.setFillColor(HexColor("#cbd5e1"))
    max_w = pw - MARGIN_L - MARGIN_R - 13*mm
    txt = c.beginText(MARGIN_L + 9*mm, abs_top - 17*mm)
    txt.setFont("Helvetica", 8.2)
    txt.setFillColor(HexColor("#cbd5e1"))
    txt.setLeading(12.5)
    words = abstract.split()
    line = ""
    for word in words:
        test = (line + " " + word).strip()
        if c.stringWidth(test, "Helvetica", 8.2) < max_w:
            line = test
        else:
            txt.textLine(line)
            line = word
    if line:
        txt.textLine(line)
    c.drawText(txt)

    # Metadata table
    meta_y = ph - 197*mm
    meta = [
        ("Author",            "Harold Nunes  ·  Editor"),
        ("Organization",      "OMNIX QUANTUM LTD  ·  United Kingdom"),
        ("Extends",           "RFC-ATF-1  (DOI: 10.5281/zenodo.20155016)"),
        ("SSRN Reference",    "6757339"),
        ("Algorithm",         "ML-DSA-65  (Dilithium-3, FIPS 204)"),
        ("Invariants",        "14 total  (ATF-INV-001–006 + RGC-INV-001–008)"),
        ("Status",            "Draft — Zenodo submission in progress"),
        ("DOI",               "Pending assignment"),
        ("Contact",           "standards@omnixquantum.com"),
    ]
    row_h = 7.5*mm
    for i, (label, value) in enumerate(meta):
        y = meta_y - i * row_h
        if i % 2 == 0:
            c.setFillColor(HexColor("#0f172a"))
            c.rect(MARGIN_L + 4*mm, y - row_h + 2*mm,
                   pw - MARGIN_L - MARGIN_R - 4*mm, row_h, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(OMNIX_BLUE2)
        c.drawString(MARGIN_L + 9*mm, y - row_h + 4.5*mm, label)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(HexColor("#e2e8f0"))
        c.drawString(MARGIN_L + 52*mm, y - row_h + 4.5*mm, value)

    # Bottom note
    c.setFont("Courier", 7)
    c.setFillColor(OMNIX_GRAY)
    c.drawCentredString(pw / 2, 10*mm,
        "Copyright (c) 2026 OMNIX QUANTUM LTD  "
        " This document may be reproduced for implementation purposes.")
    c.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────
def build_styles():
    S = {}
    S["body"] = ParagraphStyle("body",
        fontName="Helvetica", fontSize=9.5, leading=15,
        textColor=HexColor("#1e293b"), alignment=TA_JUSTIFY,
        spaceBefore=2, spaceAfter=3)

    S["h1"] = ParagraphStyle("h1",
        fontName="Helvetica-Bold", fontSize=13, leading=18,
        textColor=OMNIX_BLUE, spaceBefore=14, spaceAfter=5)

    S["h2"] = ParagraphStyle("h2",
        fontName="Helvetica-Bold", fontSize=10.5, leading=14,
        textColor=HexColor("#1e40af"), spaceBefore=10, spaceAfter=4)

    S["h3"] = ParagraphStyle("h3",
        fontName="Helvetica-Bold", fontSize=9.5, leading=13,
        textColor=HexColor("#374151"), spaceBefore=7, spaceAfter=3)

    S["code_line"] = ParagraphStyle("code_line",
        fontName="Courier", fontSize=8, leading=11.5,
        textColor=OMNIX_CODE_FG, backColor=OMNIX_CODE_BG,
        spaceBefore=0, spaceAfter=0,
        leftIndent=5, rightIndent=5, borderPad=2)

    S["bullet"] = ParagraphStyle("bullet",
        fontName="Helvetica", fontSize=9.5, leading=14,
        textColor=HexColor("#1e293b"),
        leftIndent=14, firstLineIndent=0,
        spaceBefore=1, spaceAfter=1)

    S["toc_h"] = ParagraphStyle("toc_h",
        fontName="Helvetica-Bold", fontSize=11, leading=16,
        textColor=OMNIX_BLUE, spaceBefore=6, spaceAfter=6)

    S["toc_e"] = ParagraphStyle("toc_e",
        fontName="Helvetica", fontSize=9, leading=13,
        textColor=HexColor("#374151"), spaceBefore=1)

    S["toc_s"] = ParagraphStyle("toc_s",
        fontName="Helvetica", fontSize=8.5, leading=12,
        textColor=OMNIX_GRAY, leftIndent=10, spaceBefore=0)

    S["caption"] = ParagraphStyle("caption",
        fontName="Helvetica-Oblique", fontSize=8, leading=11,
        textColor=OMNIX_GRAY, alignment=TA_CENTER, spaceAfter=6)

    S["meta"] = ParagraphStyle("meta",
        fontName="Courier", fontSize=8, leading=12,
        textColor=OMNIX_GRAY, spaceBefore=1, spaceAfter=1)

    return S


def safe_xml(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))


def inline_fmt(text):
    text = safe_xml(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`(.+?)`',
                  r'<font name="Courier" size="8.5">\1</font>', text)
    return text


# ── Unicode table detection & parsing ────────────────────────────────────────
TABLE_CHARS = set("│├┤┌┐└┘─┼")

def is_table_line(line):
    return any(ch in line for ch in TABLE_CHARS)

def parse_unicode_table(table_lines):
    """
    Convert Unicode box-drawing table lines into a list of row lists.
    Only data rows (containing │ with actual content) are kept.
    """
    rows = []
    for line in table_lines:
        if "│" not in line:
            continue
        # Split on │
        parts = [p.strip() for p in line.split("│")]
        # Remove empty first/last from leading/trailing │
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]
        if not parts:
            continue
        # Skip if all parts are just dashes/spaces (separator row)
        if all(re.match(r'^[-─\s]*$', p) for p in parts):
            continue
        rows.append(parts)
    return rows


def build_rl_table(rows, styles, col_weights=None):
    """Build a ReportLab Table from a list of row lists."""
    if not rows:
        return None
    n_cols = max(len(r) for r in rows)
    available = W - MARGIN_L - MARGIN_R

    if col_weights is None:
        col_weights = [1.0 / n_cols] * n_cols
    col_widths = [available * w for w in col_weights]

    # Pad rows to same width
    padded = [r + [""] * (n_cols - len(r)) for r in rows]

    def cell(text, is_header):
        safe = safe_xml(text)
        safe = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', safe)
        safe = re.sub(r'`(.+?)`',
                      r'<font name="Courier" size="7.5">\1</font>', safe)
        st = ParagraphStyle("tc",
            fontName="Helvetica-Bold" if is_header else "Helvetica",
            fontSize=8 if is_header else 8,
            textColor=white if is_header else HexColor("#1e293b"),
            leading=11, wordWrap='CJK')
        return Paragraph(safe, st)

    table_data = []
    for ri, row in enumerate(padded):
        table_data.append([cell(c, ri == 0) for c in row])

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    row_bg = [HexColor("#f8fafc"), HexColor("#eef2ff")]
    ts = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), OMNIX_BLUE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), row_bg),
        ("GRID", (0, 0), (-1, -1), 0.4, OMNIX_MID),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])
    t.setStyle(ts)
    return t


# ── Main parser ───────────────────────────────────────────────────────────────
def parse_content(md_text, styles):
    story = []
    lines = md_text.split("\n")
    i = 0
    in_code = False
    code_buf = []
    in_table = False
    table_buf = []

    def flush_code():
        if not code_buf:
            return
        story.append(Spacer(1, 4))
        for ln in code_buf:
            safe = safe_xml(ln) if ln.strip() else " "
            story.append(Paragraph(safe, styles["code_line"]))
        story.append(Spacer(1, 6))
        code_buf.clear()

    def flush_table():
        if not table_buf:
            return
        rows = parse_unicode_table(table_buf)
        if rows:
            t = build_rl_table(rows, styles)
            if t:
                story.append(Spacer(1, 4))
                story.append(t)
                story.append(Spacer(1, 6))
        table_buf.clear()

    def add_rule():
        story.append(Spacer(1, 3))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=OMNIX_MID, spaceAfter=4))

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Code block ──
        if stripped.startswith("```"):
            if in_table:
                flush_table()
                in_table = False
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

        # ── Unicode table detection ──
        if is_table_line(line):
            if not in_table:
                in_table = True
            table_buf.append(line)
            i += 1
            continue
        else:
            if in_table:
                flush_table()
                in_table = False

        # ── Section headings: "1.  Title" or "4.1.  Title" ──
        sec = re.match(r'^(\d+(?:\.\d+)*)\.?\s{2,}(.+)$', stripped)
        if sec:
            num, title = sec.group(1), sec.group(2)
            depth = num.count(".")
            label = f"{num}.  {title}"
            if depth == 0:
                add_rule()
                story.append(Paragraph(label, styles["h1"]))
            elif depth == 1:
                story.append(Paragraph(label, styles["h2"]))
            else:
                story.append(Paragraph(label, styles["h3"]))
            i += 1
            continue

        # ── Appendix sub-headings ──
        app = re.match(r'^([A-C]\.\d+)\.\s{2,}(.+)$', stripped)
        if app:
            story.append(Paragraph(f"{app.group(1)}.  {app.group(2)}",
                                   styles["h3"]))
            i += 1
            continue

        # ── Top-level headers (non-numbered) ──
        if stripped in ("Abstract", "Status of This Memo", "Copyright Notice",
                        "Acknowledgements", "Table of Contents", "References",
                        "Author's Address"):
            add_rule()
            story.append(Paragraph(stripped, styles["h1"]))
            i += 1
            continue

        # ── Body content (indented RFC style) ──
        if stripped:
            text = inline_fmt(stripped)
            # Detect lettered/numbered list items
            if re.match(r'^\([a-z]\)', stripped) or re.match(r'^\d+\.\ ', stripped):
                story.append(Paragraph(text, styles["bullet"]))
            else:
                story.append(Paragraph(text, styles["body"]))
        else:
            story.append(Spacer(1, 4))

        i += 1

    # Flush anything remaining
    if in_code:
        flush_code()
    if in_table:
        flush_table()

    return story


# ── Invariants table ──────────────────────────────────────────────────────────
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
        ["RGC-INV-004", "RFC-ATF-2", "Aggregate budget never exceeds AFG limit"],
        ["RGC-INV-005", "RFC-ATF-2", "All RCRs PQC-signed and immutable"],
        ["RGC-INV-006", "RFC-ATF-2", "Continuity chain is acyclic and monotonic"],
        ["RGC-INV-007", "RFC-ATF-2", "CES inputs must meet freshness requirements"],
        ["RGC-INV-008", "RFC-ATF-2", "RC TTL enforced — auto-HALT on expiry"],
    ]

    available = W - MARGIN_L - MARGIN_R
    col_w = [available * x for x in [0.22, 0.20, 0.58]]

    def cell(text, ri, ci):
        is_h = ri == 0
        color = white if is_h else (
            HexColor("#1e3a8a") if rows[ri][1] == "RFC-ATF-1"
            else HexColor("#4c1d95"))
        return Paragraph(safe_xml(text), ParagraphStyle("ic",
            fontName="Helvetica-Bold" if is_h else (
                "Courier" if ci == 0 else "Helvetica"),
            fontSize=8, textColor=color, leading=11))

    data = [[cell(c, ri, ci) for ci, c in enumerate(row)]
            for ri, row in enumerate(rows)]

    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), OMNIX_BLUE),
        ("ROWBACKGROUNDS", (0, 1), (-1, 6),
         [HexColor("#eff6ff"), HexColor("#dbeafe")]),
        ("ROWBACKGROUNDS", (0, 7), (-1, -1),
         [HexColor("#f5f3ff"), HexColor("#ede9fe")]),
        ("GRID", (0, 0), (-1, -1), 0.4, OMNIX_MID),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


TOC = [
    ("1.",   "Introduction", False),
    ("2.",   "Problem Statement: The Runtime Governance Gap", False),
    ("3.",   "Conventions and Terminology", False),
    ("4.",   "Architecture: RGC Layer", False),
    ("4.1.", "Position in the ATF Stack", True),
    ("4.2.", "Session Lifecycle", True),
    ("4.3.", "Relationship to TAR", True),
    ("5.",   "Runtime Continuity Record (RCR)", False),
    ("6.",   "Continuity Eligibility Score (CES)", False),
    ("7.",   "Continuity Chain", False),
    ("8.",   "Authority Fragmentation Guard (AFG)", False),
    ("9.",   "Escalation Protocol", False),
    ("10.",  "Reauthorization Challenge (RC)", False),
    ("11.",  "Sampling Strategy", False),
    ("12.",  "RGC Invariants", False),
    ("13.",  "Wire Format", False),
    ("14.",  "Verification Protocol", False),
    ("15.",  "Persistence Schema", False),
    ("16.",  "API Endpoints", False),
    ("17.",  "Security Considerations", False),
    ("18.",  "Compliance Mapping", False),
    ("19.",  "Extension Points", False),
    ("20.",  "Relationship to RFC-ATF-1", False),
    ("21.",  "References", False),
    ("22.",  "Appendix A — CES Computation Examples", False),
    ("23.",  "Appendix B — RGC Compliance Checklist", False),
    ("24.",  "Appendix C — Implementation Notes", False),
]


def build_toc(styles):
    items = [Paragraph("Table of Contents", styles["toc_h"]),
             HRFlowable(width="100%", thickness=0.5,
                        color=OMNIX_MID, spaceAfter=6)]
    for num, title, sub in TOC:
        label = f"{num}  {title}"
        items.append(Paragraph(label,
                               styles["toc_s"] if sub else styles["toc_e"]))
    return items


# ── Generate ──────────────────────────────────────────────────────────────────
def generate():
    out = "docs/submissions/RFC-ATF-2.pdf"
    os.makedirs("docs/submissions", exist_ok=True)

    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T, bottomMargin=MARGIN_B,
        title="RFC-ATF-2: Agent Trust Fabric — Runtime Governance Continuity",
        author="Harold Nunes — OMNIX QUANTUM LTD",
        subject="Runtime Governance Continuity Extension to RFC-ATF-1",
        keywords="AI governance, ATF, post-quantum, Dilithium-3, runtime continuity"
    )

    styles = build_styles()
    story = []

    # Page 1 = cover (handled by first_page callback)
    story.append(PageBreak())

    # TOC
    story.extend(build_toc(styles))
    story.append(PageBreak())

    # Invariants reference
    story.append(Paragraph("Invariants Reference — All 14 ATF Invariants",
                           styles["h1"]))
    story.append(Spacer(1, 5))
    story.append(build_invariants_table(styles))
    story.append(Paragraph(
        "ATF-INV-001–006 proven in TLA+ (same methodology as AWS DynamoDB "
        "and Azure Cosmos DB). RGC-INV-001–008 verified by reference "
        "implementation test suite (82 tests, 82 passing).",
        styles["caption"]))
    story.append(PageBreak())

    # RFC body
    with open("docs/standards/RFC-ATF-2.md") as f:
        md = f.read()

    # Strip outer ``` wrapper
    lines = md.split("\n")
    if lines and lines[0].strip() == "```":
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    md = "\n".join(lines)

    story.extend(parse_content(md, styles))

    doc.build(story,
              onFirstPage=cover_page,
              onLaterPages=make_page)
    print(f"Generated: {out}")


if __name__ == "__main__":
    generate()
