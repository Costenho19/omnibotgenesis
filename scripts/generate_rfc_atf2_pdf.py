"""
PDF Generator — RFC-ATF-2
Professional IETF-style document with OMNIX logo.
Uses Bitstream Vera TTF for Unicode support.
"""
import re, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

W, H = A4
ML = 22*mm; MR = 22*mm; MT = 28*mm; MB = 25*mm

BLUE   = HexColor("#1e3a8a")
BLUE2  = HexColor("#3b82f6")
CYAN   = HexColor("#06b6d4")
PURPLE = HexColor("#6d28d9")
GRAY   = HexColor("#6b7280")
MID    = HexColor("#cbd5e1")
DARK   = HexColor("#0a0a0f")
CODEBG = HexColor("#1e293b")
CODEFG = HexColor("#e2e8f0")
BODY   = HexColor("#1e293b")

# ── Register Unicode-capable fonts ────────────────────────────────────────────
_RL = os.path.dirname(__import__("reportlab").__file__)
_FD = os.path.join(_RL, "fonts")

def _reg(name, file):
    path = os.path.join(_FD, file)
    if os.path.exists(path):
        pdfmetrics.registerFont(TTFont(name, path))
        return True
    return False

_reg("Vera",      "Vera.ttf")
_reg("VeraBd",    "VeraBd.ttf")
_reg("VeraIt",    "VeraIt.ttf")
_reg("VeraBI",    "VeraBI.ttf")
_reg("VeraMono",  "Vera.ttf")   # fallback mono

BODY_FONT  = "Vera"
BOLD_FONT  = "VeraBd"
MONO_FONT  = "Courier"           # Courier for code — ASCII only, sanitized

# ── Character sanitization ────────────────────────────────────────────────────
CHAR_MAP = {
    "\u2013": "--",      # en-dash
    "\u2014": "---",     # em-dash
    "\u2015": "---",     # horizontal bar
    "\u2018": "'",       # left single quote
    "\u2019": "'",       # right single quote
    "\u201c": '"',       # left double quote
    "\u201d": '"',       # right double quote
    "\u2022": "*",       # bullet
    "\u2026": "...",     # ellipsis
    "\u2192": "->",      # rightwards arrow
    "\u2190": "<-",      # leftwards arrow
    "\u21d2": "=>",      # double rightwards arrow
    "\u2265": ">=",      # greater than or equal
    "\u2264": "<=",      # less than or equal
    "\u2260": "!=",      # not equal
    "\u00d7": "x",       # multiplication sign
    "\u00f7": "/",       # division sign
    "\u03b1": "alpha",
    "\u03b2": "beta",
    "\u03b3": "gamma",
    "\u2211": "Sigma",   # sum
    "\u221e": "inf",     # infinity
    "\u00b0": "deg",     # degree
    "\u00b1": "+/-",     # plus-minus
    "\u2082": "2",       # subscript 2
    "\u2080": "0",       # subscript 0
    "\u2081": "1",       # subscript 1
    "\u2083": "3",
    "\u00ae": "(R)",
    "\u00a9": "(c)",
    "\u2122": "(TM)",
    "\u00a0": " ",       # non-breaking space
    "\u200b": "",        # zero-width space
    # Box drawing — these should not reach here (handled by table parser)
    "\u2500": "-", "\u2501": "=",
    "\u2502": "|", "\u2503": "|",
    "\u250c": "+", "\u2510": "+",
    "\u2514": "+", "\u2518": "+",
    "\u251c": "+", "\u2524": "+",
    "\u252c": "+", "\u2534": "+",
    "\u253c": "+", "\u2550": "=",
    "\u2551": "|", "\u2554": "+",
    "\u2557": "+", "\u255a": "+",
    "\u255d": "+", "\u2560": "+",
    "\u2563": "+", "\u2566": "+",
    "\u2569": "+", "\u256c": "+",
    "\u2588": "#",       # block
    "\u2591": " ",       # light shade
}

def sanitize(text):
    """Replace non-Latin1 / unsupported chars with ASCII equivalents."""
    out = []
    for ch in text:
        if ch in CHAR_MAP:
            out.append(CHAR_MAP[ch])
        elif ord(ch) > 127:
            # Try Latin-1 range (Vera supports these)
            if ord(ch) <= 0x2FF:
                out.append(ch)
            else:
                out.append("?")
        else:
            out.append(ch)
    return "".join(out)


# ── Page templates ────────────────────────────────────────────────────────────
def make_page(c, doc):
    c.saveState()
    pw, ph = A4
    c.setStrokeColor(BLUE2); c.setLineWidth(1.5)
    c.line(ML, ph - MT + 6*mm, pw - MR, ph - MT + 6*mm)
    c.setFont("Courier", 7.5); c.setFillColor(GRAY)
    c.drawString(ML, ph - MT + 8.5*mm, "OMNIX QUANTUM Open Standard")
    c.drawRightString(pw - MR, ph - MT + 8.5*mm,
                      "RFC-ATF-2 -- Runtime Governance Continuity")
    c.setStrokeColor(MID); c.setLineWidth(0.6)
    c.line(ML, MB - 4*mm, pw - MR, MB - 4*mm)
    c.setFont("Courier", 7.5); c.setFillColor(GRAY)
    c.drawString(ML, MB - 8.5*mm, "Nunes, H.           [Standards Track]")
    c.drawCentredString(pw / 2, MB - 8.5*mm, "May 2026")
    c.drawRightString(pw - MR, MB - 8.5*mm, f"[Page {doc.page}]")
    c.restoreState()


def cover_page(c, doc):
    c.saveState()
    pw, ph = A4
    c.setFillColor(DARK); c.rect(0, 0, pw, ph, fill=1, stroke=0)
    c.setFillColor(BLUE2); c.rect(0, ph - 6*mm, pw, 6*mm, fill=1, stroke=0)
    c.setFillColor(PURPLE); c.rect(0, 0, pw, 4*mm, fill=1, stroke=0)
    c.setFillColor(CYAN); c.rect(0, 0, 3*mm, ph, fill=1, stroke=0)

    for lp in ["docs/business/omnix_logo.png", "assets/omnix_logo.png",
               "omnix_dashboard/static/images/omnix_logo.png"]:
        if os.path.exists(lp):
            try:
                c.drawImage(lp, ML + 4*mm, ph - 38*mm,
                            width=42*mm, height=14*mm,
                            preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
            break

    c.setFont("Helvetica-Bold", 8); c.setFillColor(CYAN)
    c.drawString(ML+4*mm, ph-52*mm,
                 "STANDARDS TRACK  *  OPEN STANDARD  *  MAY 2026")
    c.setStrokeColor(BLUE2); c.setLineWidth(0.8)
    c.line(ML+4*mm, ph-57*mm, pw-MR, ph-57*mm)

    c.setFont("Helvetica-Bold", 26); c.setFillColor(white)
    c.drawString(ML+4*mm, ph-76*mm, "RFC-ATF-2")
    c.setFont("Helvetica-Bold", 15); c.setFillColor(CYAN)
    c.drawString(ML+4*mm, ph-88*mm, "Agent Trust Fabric")
    c.drawString(ML+4*mm, ph-97*mm, "Runtime Governance Continuity")
    c.setFont("Helvetica", 10); c.setFillColor(GRAY)
    c.drawString(ML+4*mm, ph-108*mm,
                 "Extension to RFC-ATF-1  *  Version 1.0.0")
    c.setStrokeColor(PURPLE); c.setLineWidth(0.5)
    c.line(ML+4*mm, ph-114*mm, pw-MR, ph-114*mm)

    # Abstract box
    ay = ph - 119*mm; ah = 66*mm
    c.setFillColor(HexColor("#0f172a"))
    c.roundRect(ML+4*mm, ay-ah, pw-ML-MR-4*mm, ah, 3*mm, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.5); c.setFillColor(BLUE2)
    c.drawString(ML+9*mm, ay-7*mm, "ABSTRACT")

    abstract = (
        "RFC-ATF-2 extends the Agent Trust Fabric delegation protocol "
        "(RFC-ATF-1, DOI: 10.5281/zenodo.20155016) to cover the full "
        "execution lifecycle of long-running autonomous agent workflows. "
        "RFC-ATF-1 established cryptographic boundary attestation: proof "
        "that an agent possessed a valid, human-originated authority grant "
        "at the moment of execution admission. RFC-ATF-2 addresses the "
        "Runtime Governance Gap -- the structural absence of continuous "
        "governability supervision between admission and completion. "
        "This extension introduces the Runtime Continuity Record (RCR), "
        "the Continuity Eligibility Score (CES), the Authority Fragmentation "
        "Guard (AFG), and the Reauthorization Challenge (RC) Protocol. "
        "Eight new invariants (RGC-INV-001 through RGC-INV-008) extend "
        "the ATF stack to 14 total formally model-checkable invariants. "
        "The reference implementation is currently running in production."
    )
    c.setFont("Helvetica", 8.2); c.setFillColor(HexColor("#cbd5e1"))
    mw = pw - ML - MR - 13*mm
    txt = c.beginText(ML+9*mm, ay-17*mm)
    txt.setFont("Helvetica", 8.2)
    txt.setFillColor(HexColor("#cbd5e1"))
    txt.setLeading(12.5)
    line = ""
    for word in abstract.split():
        test = (line + " " + word).strip()
        if c.stringWidth(test, "Helvetica", 8.2) < mw:
            line = test
        else:
            txt.textLine(line); line = word
    if line: txt.textLine(line)
    c.drawText(txt)

    # Metadata
    meta = [
        ("Author",       "Harold Nunes  *  Editor"),
        ("Organization", "OMNIX QUANTUM LTD  *  United Kingdom"),
        ("Extends",      "RFC-ATF-1  (DOI: 10.5281/zenodo.20155016)"),
        ("SSRN",         "6757339"),
        ("Algorithm",    "ML-DSA-65  (Dilithium-3, FIPS 204)"),
        ("Invariants",   "14 total  (ATF-INV-001-006 + RGC-INV-001-008)"),
        ("Status",       "Draft -- Zenodo submission in progress"),
        ("DOI",          "Pending assignment"),
        ("Contact",      "standards@omnixquantum.com"),
    ]
    my = ph - 197*mm; rh = 7.5*mm
    for i, (lbl, val) in enumerate(meta):
        y = my - i * rh
        if i % 2 == 0:
            c.setFillColor(HexColor("#0f172a"))
            c.rect(ML+4*mm, y-rh+2*mm, pw-ML-MR-4*mm, rh, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 7.5); c.setFillColor(BLUE2)
        c.drawString(ML+9*mm, y-rh+4.5*mm, lbl)
        c.setFont("Helvetica", 7.5); c.setFillColor(HexColor("#e2e8f0"))
        c.drawString(ML+52*mm, y-rh+4.5*mm, val)

    c.setFont("Courier", 7); c.setFillColor(GRAY)
    c.drawCentredString(pw/2, 10*mm,
        "Copyright (c) 2026 OMNIX QUANTUM LTD  "
        " This document may be reproduced for implementation purposes.")
    c.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────
def styles():
    S = {}
    S["body"] = ParagraphStyle("body",
        fontName=BODY_FONT, fontSize=9.5, leading=15,
        textColor=BODY, alignment=TA_JUSTIFY, spaceBefore=2, spaceAfter=3)
    S["h1"] = ParagraphStyle("h1",
        fontName=BOLD_FONT, fontSize=13, leading=18,
        textColor=BLUE, spaceBefore=14, spaceAfter=5)
    S["h2"] = ParagraphStyle("h2",
        fontName=BOLD_FONT, fontSize=10.5, leading=14,
        textColor=HexColor("#1e40af"), spaceBefore=10, spaceAfter=4)
    S["h3"] = ParagraphStyle("h3",
        fontName=BOLD_FONT, fontSize=9.5, leading=13,
        textColor=HexColor("#374151"), spaceBefore=7, spaceAfter=3)
    S["code"] = ParagraphStyle("code",
        fontName=MONO_FONT, fontSize=7.8, leading=11.5,
        textColor=CODEFG, backColor=CODEBG,
        spaceBefore=0, spaceAfter=0, leftIndent=5, rightIndent=5, borderPad=2)
    S["bullet"] = ParagraphStyle("bullet",
        fontName=BODY_FONT, fontSize=9.5, leading=14,
        textColor=BODY, leftIndent=14, spaceBefore=1, spaceAfter=1)
    S["toc_h"] = ParagraphStyle("toc_h",
        fontName=BOLD_FONT, fontSize=11, leading=16,
        textColor=BLUE, spaceBefore=6, spaceAfter=6)
    S["toc_e"] = ParagraphStyle("toc_e",
        fontName=BODY_FONT, fontSize=9, leading=13,
        textColor=HexColor("#374151"), spaceBefore=1)
    S["toc_s"] = ParagraphStyle("toc_s",
        fontName=BODY_FONT, fontSize=8.5, leading=12,
        textColor=GRAY, leftIndent=10, spaceBefore=0)
    S["caption"] = ParagraphStyle("caption",
        fontName=BODY_FONT, fontSize=8, leading=11,
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=6)
    return S


# ── Text helpers ──────────────────────────────────────────────────────────────
def xml_safe(text):
    text = sanitize(text)
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

def fmt(text):
    text = xml_safe(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`',
                  r'<font name="Courier" size="8.2">\1</font>', text)
    return text


# ── Table detection and parsing ───────────────────────────────────────────────
BOX = set("│├┤┌┐└┘┼╔╗╚╝╠╣╦╩╬║═")

def is_box(line):
    return any(ch in line for ch in BOX)

def parse_box_table(lines):
    rows = []
    for line in lines:
        if "│" not in line and "║" not in line:
            continue
        sep = "│" if "│" in line else "║"
        parts = [p.strip() for p in line.split(sep)]
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]
        if not parts:
            continue
        if all(re.match(r'^[-=─═\s]*$', p) for p in parts):
            continue
        rows.append([sanitize(p) for p in parts])
    return rows

def make_table(rows, ST):
    if not rows:
        return None
    nc = max(len(r) for r in rows)
    aw = W - ML - MR
    cw = [aw / nc] * nc
    padded = [r + [""] * (nc - len(r)) for r in rows]

    def cell(txt, ri, ci):
        is_h = ri == 0
        return Paragraph(
            re.sub(r'`([^`]+)`', r'<font name="Courier" size="7.5">\1</font>',
                   xml_safe(txt)),
            ParagraphStyle("tc",
                fontName=BOLD_FONT if is_h else BODY_FONT,
                fontSize=8, leading=11,
                textColor=white if is_h else BODY,
                wordWrap='CJK'))

    data = [[cell(c, ri, ci) for ci, c in enumerate(row)]
            for ri, row in enumerate(padded)]

    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [HexColor("#f8fafc"), HexColor("#eef2ff")]),
        ("GRID",         (0, 0), (-1, -1), 0.4, MID),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ]))
    return t


# ── Main parser ───────────────────────────────────────────────────────────────
def parse(md, ST):
    story = []
    lines = md.split("\n")
    i = 0
    in_code = False
    code_buf = []
    in_box = False
    box_buf = []

    def flush_code():
        if not code_buf: return
        story.append(Spacer(1, 4))
        for ln in code_buf:
            safe = sanitize(ln)
            safe = (safe.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;"))
            story.append(Paragraph(safe or " ", ST["code"]))
        story.append(Spacer(1, 6))
        code_buf.clear()

    def flush_box():
        if not box_buf: return
        rows = parse_box_table(box_buf)
        if rows:
            t = make_table(rows, ST)
            if t:
                story.append(Spacer(1, 4))
                story.append(t)
                story.append(Spacer(1, 6))
        box_buf.clear()

    def rule():
        story.append(Spacer(1, 3))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=MID, spaceAfter=4))

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        # Code fence
        if s.startswith("```"):
            if in_box: flush_box(); in_box = False
            if in_code: flush_code(); in_code = False
            else: in_code = True
            i += 1; continue

        if in_code:
            code_buf.append(line); i += 1; continue

        # Box-drawing table lines
        if is_box(line):
            if not in_box: in_box = True
            box_buf.append(line); i += 1; continue
        else:
            if in_box: flush_box(); in_box = False

        if not s:
            story.append(Spacer(1, 4)); i += 1; continue

        # Numbered sections: "1.  Title" or "4.1.  Title"
        m = re.match(r'^(\d+(?:\.\d+)*)\.?\s{2,}(.+)$', s)
        if m:
            num, title = m.group(1), sanitize(m.group(2))
            depth = num.count(".")
            label = f"{num}.  {title}"
            if depth == 0:
                rule()
                story.append(Paragraph(label, ST["h1"]))
            elif depth == 1:
                story.append(Paragraph(label, ST["h2"]))
            else:
                story.append(Paragraph(label, ST["h3"]))
            i += 1; continue

        # Appendix sub-sections: "A.1.  Title"
        m = re.match(r'^([A-C]\.\d+)\.\s+(.+)$', s)
        if m:
            story.append(Paragraph(
                f"{m.group(1)}.  {sanitize(m.group(2))}", ST["h3"]))
            i += 1; continue

        # Top-level section keywords
        if s in ("Abstract", "Status of This Memo", "Copyright Notice",
                 "Acknowledgements", "Table of Contents",
                 "References", "Author's Address"):
            rule()
            story.append(Paragraph(s, ST["h1"]))
            i += 1; continue

        # Body text
        text = fmt(s)
        if re.match(r'^\([a-z]\)', s) or re.match(r'^\d+\.\s', s):
            story.append(Paragraph(text, ST["bullet"]))
        else:
            story.append(Paragraph(text, ST["body"]))
        i += 1

    if in_code: flush_code()
    if in_box:  flush_box()
    return story


# ── Invariants table ──────────────────────────────────────────────────────────
def inv_table(ST):
    rows = [
        ["Invariant",   "Standard",   "Property"],
        ["ATF-INV-001", "RFC-ATF-1", "Monotonic Authority Reduction (MAR)"],
        ["ATF-INV-002", "RFC-ATF-1", "All DRs signed by delegating principal"],
        ["ATF-INV-003", "RFC-ATF-1", "Chain root traceability to Tier-1"],
        ["ATF-INV-004", "RFC-ATF-1", "No grant exceeds maximum authority budget"],
        ["ATF-INV-005", "RFC-ATF-1", "Receipt immutability"],
        ["ATF-INV-006", "RFC-ATF-1", "Independent verifiability without platform"],
        ["RGC-INV-001", "RFC-ATF-2", "Every RCR anchored to a valid TAR"],
        ["RGC-INV-002", "RFC-ATF-2", "CES computed from real-time values only"],
        ["RGC-INV-003", "RFC-ATF-2", "HALT terminates execution and revokes sub-tasks"],
        ["RGC-INV-004", "RFC-ATF-2", "Aggregate budget never exceeds AFG limit"],
        ["RGC-INV-005", "RFC-ATF-2", "All RCRs PQC-signed and immutable"],
        ["RGC-INV-006", "RFC-ATF-2", "Continuity chain is acyclic and monotonic"],
        ["RGC-INV-007", "RFC-ATF-2", "CES inputs must meet freshness requirements"],
        ["RGC-INV-008", "RFC-ATF-2", "RC TTL enforced -- auto-HALT on expiry"],
    ]
    aw = W - ML - MR
    cw = [aw*0.22, aw*0.20, aw*0.58]

    def c(txt, ri, ci):
        is_h = ri == 0
        color = white if is_h else (
            HexColor("#1e3a8a") if rows[ri][1] == "RFC-ATF-1"
            else HexColor("#4c1d95"))
        return Paragraph(txt, ParagraphStyle("ic",
            fontName=BOLD_FONT if is_h else (
                MONO_FONT if ci == 0 else BODY_FONT),
            fontSize=8, textColor=color, leading=11))

    data = [[c(col, ri, ci) for ci, col in enumerate(row)]
            for ri, row in enumerate(rows)]
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  BLUE),
        ("ROWBACKGROUNDS",(0,1), (-1,6),
         [HexColor("#eff6ff"), HexColor("#dbeafe")]),
        ("ROWBACKGROUNDS",(0,7), (-1,-1),
         [HexColor("#f5f3ff"), HexColor("#ede9fe")]),
        ("GRID",         (0,0), (-1,-1), 0.4, MID),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    return t


TOC = [
    ("1.",  "Introduction", False),
    ("2.",  "Problem Statement: The Runtime Governance Gap", False),
    ("3.",  "Conventions and Terminology", False),
    ("4.",  "Architecture: RGC Layer", False),
    ("4.1.","Position in the ATF Stack", True),
    ("4.2.","Session Lifecycle", True),
    ("4.3.","Relationship to TAR", True),
    ("5.",  "Runtime Continuity Record (RCR)", False),
    ("6.",  "Continuity Eligibility Score (CES)", False),
    ("7.",  "Continuity Chain", False),
    ("8.",  "Authority Fragmentation Guard (AFG)", False),
    ("9.",  "Escalation Protocol", False),
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
    ("22.", "Appendix A -- CES Computation Examples", False),
    ("23.", "Appendix B -- RGC Compliance Checklist", False),
    ("24.", "Appendix C -- Implementation Notes", False),
]


def toc(ST):
    items = [Paragraph("Table of Contents", ST["toc_h"]),
             HRFlowable(width="100%", thickness=0.5, color=MID, spaceAfter=6)]
    for num, title, sub in TOC:
        items.append(Paragraph(
            f"{num}  {title}",
            ST["toc_s"] if sub else ST["toc_e"]))
    return items


# ── Generate ──────────────────────────────────────────────────────────────────
def generate():
    out = "docs/submissions/RFC-ATF-2.pdf"
    os.makedirs("docs/submissions", exist_ok=True)

    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
        title="RFC-ATF-2: Agent Trust Fabric -- Runtime Governance Continuity",
        author="Harold Nunes -- OMNIX QUANTUM LTD",
        subject="Runtime Governance Continuity Extension to RFC-ATF-1",
        keywords="AI governance,ATF,post-quantum,Dilithium-3,runtime continuity"
    )

    ST = styles()
    story = []
    story.append(PageBreak())          # cover handled by callback

    story.extend(toc(ST))
    story.append(PageBreak())

    story.append(Paragraph(
        "Invariants Reference -- All 14 ATF Invariants", ST["h1"]))
    story.append(Spacer(1, 5))
    story.append(inv_table(ST))
    story.append(Paragraph(
        "ATF-INV-001 through ATF-INV-006 are proven in TLA+ using the same "
        "formal methods methodology as AWS DynamoDB and Azure Cosmos DB. "
        "RGC-INV-001 through RGC-INV-008 are verified by the reference "
        "implementation test suite (82 tests, 82 passing).",
        ST["caption"]))
    story.append(PageBreak())

    with open("docs/standards/RFC-ATF-2.md") as f:
        md = f.read()

    # Strip outer ``` wrapper
    lines = md.split("\n")
    if lines and lines[0].strip() == "```":
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    md = "\n".join(lines)

    story.extend(parse(md, ST))

    doc.build(story, onFirstPage=cover_page, onLaterPages=make_page)
    size = os.path.getsize(out)
    print(f"Generated: {out}  ({size//1024} KB)")


if __name__ == "__main__":
    generate()
