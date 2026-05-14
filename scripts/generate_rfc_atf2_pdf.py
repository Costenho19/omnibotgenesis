"""
PDF Generator — RFC-ATF-2
Full dark theme — consistent with RFC-ATF-1 visual identity.
"""
import re, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

W, H  = A4
ML = 22*mm; MR = 22*mm; MT = 28*mm; MB = 25*mm

# ── Dark palette ───────────────────────────────────────────────────────────────
BG       = HexColor("#0a0a0f")   # page background
SURFACE  = HexColor("#0f172a")   # card / box surface
SURFACE2 = HexColor("#1e293b")   # alternate row / code bg
BLUE     = HexColor("#3b82f6")   # primary accent
BLUE_DIM = HexColor("#1e3a8a")   # dark blue
CYAN     = HexColor("#06b6d4")   # secondary accent
PURPLE   = HexColor("#8b5cf6")   # tertiary accent
GRAY     = HexColor("#94a3b8")   # muted text
LIGHT    = HexColor("#e2e8f0")   # body text on dark
WHITE    = HexColor("#f8fafc")   # headings
DIM      = HexColor("#475569")   # very muted / rules
CODE_FG  = HexColor("#7dd3fc")   # code text (light blue)
CODE_BG  = HexColor("#1e293b")   # code background

# ── Fonts ──────────────────────────────────────────────────────────────────────
_RL = os.path.dirname(__import__("reportlab").__file__)
_FD = os.path.join(_RL, "fonts")

def _reg(name, file):
    p = os.path.join(_FD, file)
    if os.path.exists(p):
        pdfmetrics.registerFont(TTFont(name, p))

_reg("Vera",   "Vera.ttf")
_reg("VeraBd", "VeraBd.ttf")
_reg("VeraIt", "VeraIt.ttf")

BF = "Vera"       # body font
HF = "VeraBd"     # heading font
MF = "Courier"    # mono

# ── Character sanitization ─────────────────────────────────────────────────────
CMAP = {
    "\u2013":"--", "\u2014":"---", "\u2015":"---",
    "\u2018":"'",  "\u2019":"'",   "\u201c":'"',  "\u201d":'"',
    "\u2022":"*",  "\u2026":"...",
    "\u2192":"->", "\u2190":"<-",  "\u21d2":"=>",
    "\u2265":">=", "\u2264":"<=",  "\u2260":"!=",
    "\u00d7":"x",  "\u00f7":"/",   "\u00b1":"+/-",
    "\u00b0":"deg","\u00ae":"(R)", "\u00a9":"(c)","\u2122":"(TM)",
    "\u00a0":" ",  "\u200b":"",
    "\u2082":"2",  "\u2080":"0",   "\u2081":"1",  "\u2083":"3",
    # box drawing — should not reach renderer but as safety net
    "\u2500":"-","\u2501":"=","\u2502":"|","\u2503":"|",
    "\u250c":"+","\u2510":"+","\u2514":"+","\u2518":"+",
    "\u251c":"+","\u2524":"+","\u252c":"+","\u2534":"+",
    "\u253c":"+","\u2550":"=","\u2551":"|","\u2554":"+",
    "\u2557":"+","\u255a":"+","\u255d":"+","\u2560":"+",
    "\u2563":"+","\u2566":"+","\u2569":"+","\u256c":"+",
    "\u2588":"#","\u2591":" ",
    # Greek used in math
    "\u03b1":"alpha","\u03b2":"beta","\u03b3":"gamma","\u2211":"Sigma",
}

def san(text):
    out = []
    for ch in text:
        if ch in CMAP:
            out.append(CMAP[ch])
        elif ord(ch) > 0x2FF:
            out.append("?")
        else:
            out.append(ch)
    return "".join(out)

def xsafe(text):
    text = san(text)
    return text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def fmt(text):
    text = xsafe(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`',
                  r'<font name="Courier" color="#7dd3fc" size="8.2">\1</font>',
                  text)
    return text


# ── Dark page background ───────────────────────────────────────────────────────
def dark_bg(c, doc):
    """Paint full dark background + header/footer on every body page."""
    pw, ph = A4
    c.saveState()

    # Full dark fill
    c.setFillColor(BG)
    c.rect(0, 0, pw, ph, fill=1, stroke=0)

    # Left cyan stripe
    c.setFillColor(CYAN)
    c.rect(0, 0, 2.5*mm, ph, fill=1, stroke=0)

    # Header rule
    c.setStrokeColor(BLUE)
    c.setLineWidth(1.2)
    c.line(ML, ph - MT + 6*mm, pw - MR, ph - MT + 6*mm)

    c.setFont("Courier", 7.5)
    c.setFillColor(GRAY)
    c.drawString(ML, ph - MT + 8.5*mm, "OMNIX QUANTUM Open Standard")
    c.drawRightString(pw - MR, ph - MT + 8.5*mm,
                      "RFC-ATF-2 -- Runtime Governance Continuity")

    # Footer rule
    c.setStrokeColor(DIM)
    c.setLineWidth(0.5)
    c.line(ML, MB - 4*mm, pw - MR, MB - 4*mm)

    c.setFont("Courier", 7.5)
    c.setFillColor(GRAY)
    c.drawString(ML, MB - 8.5*mm, "Nunes, H.           [Standards Track]")
    c.drawCentredString(pw/2, MB - 8.5*mm, "May 2026")
    c.drawRightString(pw - MR, MB - 8.5*mm, f"[Page {doc.page}]")

    c.restoreState()


def cover_page(c, doc):
    pw, ph = A4
    c.saveState()

    # Background
    c.setFillColor(BG)
    c.rect(0, 0, pw, ph, fill=1, stroke=0)

    # Accent bars
    c.setFillColor(BLUE)
    c.rect(0, ph - 6*mm, pw, 6*mm, fill=1, stroke=0)
    c.setFillColor(PURPLE)
    c.rect(0, 0, pw, 4*mm, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(0, 0, 3*mm, ph, fill=1, stroke=0)

    # Logo
    for lp in ["docs/business/omnix_logo.png", "assets/omnix_logo.png",
               "omnix_dashboard/static/images/omnix_logo.png"]:
        if os.path.exists(lp):
            try:
                c.drawImage(lp, ML+4*mm, ph-38*mm, width=44*mm, height=15*mm,
                            preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
            break

    c.setFont("Helvetica-Bold", 8); c.setFillColor(CYAN)
    c.drawString(ML+4*mm, ph-52*mm,
                 "STANDARDS TRACK  *  OPEN STANDARD  *  MAY 2026")

    c.setStrokeColor(BLUE); c.setLineWidth(0.8)
    c.line(ML+4*mm, ph-57*mm, pw-MR, ph-57*mm)

    c.setFont("Helvetica-Bold", 28); c.setFillColor(WHITE)
    c.drawString(ML+4*mm, ph-76*mm, "RFC-ATF-2")
    c.setFont("Helvetica-Bold", 15); c.setFillColor(CYAN)
    c.drawString(ML+4*mm, ph-89*mm, "Agent Trust Fabric")
    c.drawString(ML+4*mm, ph-99*mm, "Runtime Governance Continuity")
    c.setFont("Helvetica", 10); c.setFillColor(GRAY)
    c.drawString(ML+4*mm, ph-110*mm,
                 "Extension to RFC-ATF-1  *  Version 1.0.0")

    c.setStrokeColor(PURPLE); c.setLineWidth(0.5)
    c.line(ML+4*mm, ph-116*mm, pw-MR, ph-116*mm)

    # Abstract
    ay=ph-120*mm; ah=66*mm
    c.setFillColor(SURFACE)
    c.roundRect(ML+4*mm, ay-ah, pw-ML-MR-4*mm, ah, 3*mm, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.5); c.setFillColor(BLUE)
    c.drawString(ML+9*mm, ay-7*mm, "ABSTRACT")

    ab = (
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
    mw = pw-ML-MR-13*mm
    txt = c.beginText(ML+9*mm, ay-17*mm)
    txt.setFont("Helvetica", 8.2); txt.setFillColor(LIGHT); txt.setLeading(12.5)
    line=""
    for word in ab.split():
        test=(line+" "+word).strip()
        if c.stringWidth(test,"Helvetica",8.2)<mw: line=test
        else: txt.textLine(line); line=word
    if line: txt.textLine(line)
    c.drawText(txt)

    # Meta
    meta=[
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
    my=ph-197*mm; rh=7.5*mm
    for i,(lbl,val) in enumerate(meta):
        y=my-i*rh
        if i%2==0:
            c.setFillColor(SURFACE)
            c.rect(ML+4*mm,y-rh+2*mm,pw-ML-MR-4*mm,rh,fill=1,stroke=0)
        c.setFont("Helvetica-Bold",7.5); c.setFillColor(BLUE)
        c.drawString(ML+9*mm,y-rh+4.5*mm,lbl)
        c.setFont("Helvetica",7.5); c.setFillColor(LIGHT)
        c.drawString(ML+52*mm,y-rh+4.5*mm,val)

    c.setFont("Courier",7); c.setFillColor(DIM)
    c.drawCentredString(pw/2,10*mm,
        "Copyright (c) 2026 OMNIX QUANTUM LTD  "
        " This document may be reproduced for implementation purposes.")
    c.restoreState()


# ── Dark styles ────────────────────────────────────────────────────────────────
def build_styles():
    S={}
    S["body"]  = ParagraphStyle("body",  fontName=BF, fontSize=9.5, leading=15,
        textColor=LIGHT, alignment=TA_JUSTIFY, spaceBefore=2, spaceAfter=3,
        backColor=None)
    S["h1"]    = ParagraphStyle("h1",    fontName=HF, fontSize=13, leading=18,
        textColor=BLUE,  spaceBefore=14, spaceAfter=5)
    S["h2"]    = ParagraphStyle("h2",    fontName=HF, fontSize=10.5, leading=14,
        textColor=CYAN,  spaceBefore=10, spaceAfter=4)
    S["h3"]    = ParagraphStyle("h3",    fontName=HF, fontSize=9.5, leading=13,
        textColor=GRAY,  spaceBefore=7,  spaceAfter=3)
    S["code"]  = ParagraphStyle("code",  fontName=MF, fontSize=7.8, leading=11.5,
        textColor=CODE_FG, backColor=CODE_BG,
        spaceBefore=0, spaceAfter=0, leftIndent=5, rightIndent=5, borderPad=2)
    S["bullet"]= ParagraphStyle("bullet",fontName=BF, fontSize=9.5, leading=14,
        textColor=LIGHT, leftIndent=14, spaceBefore=1, spaceAfter=1)
    S["toc_h"] = ParagraphStyle("toc_h", fontName=HF, fontSize=11, leading=16,
        textColor=BLUE,  spaceBefore=6,  spaceAfter=6)
    S["toc_e"] = ParagraphStyle("toc_e", fontName=BF, fontSize=9,  leading=13,
        textColor=LIGHT, spaceBefore=1)
    S["toc_s"] = ParagraphStyle("toc_s", fontName=BF, fontSize=8.5,leading=12,
        textColor=GRAY,  leftIndent=10,  spaceBefore=0)
    S["cap"]   = ParagraphStyle("cap",   fontName=BF, fontSize=8, leading=11,
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=6)
    return S


# ── Table detection & parsing ──────────────────────────────────────────────────
BOX = set("│├┤┌┐└┘┼║═╔╗╚╝╠╣╦╩╬")

def is_box(line):
    return any(ch in line for ch in BOX)

def parse_box_table(lines):
    rows=[]
    for line in lines:
        sep = "│" if "│" in line else ("║" if "║" in line else None)
        if not sep: continue
        parts=[p.strip() for p in line.split(sep)]
        if parts and parts[0]=="":  parts=parts[1:]
        if parts and parts[-1]=="": parts=parts[:-1]
        if not parts: continue
        if all(re.match(r'^[-=─═\s]*$',p) for p in parts): continue
        rows.append([san(p) for p in parts])
    return rows

def make_table(rows, S):
    if not rows: return None
    nc = max(len(r) for r in rows)
    aw = W - ML - MR
    cw = [aw/nc]*nc
    padded = [r+[""]*(nc-len(r)) for r in rows]

    tbl_bg  = HexColor("#0f172a")
    row_alt = [HexColor("#1a2540"), HexColor("#162035")]
    head_bg = BLUE_DIM

    def cell(txt, ri, ci):
        is_h = ri==0
        safe = re.sub(r'`([^`]+)`',
            r'<font name="Courier" color="#7dd3fc" size="7.5">\1</font>',
            xsafe(txt))
        return Paragraph(safe, ParagraphStyle("tc",
            fontName=HF if is_h else BF, fontSize=8,
            textColor=WHITE if is_h else LIGHT,
            leading=11, wordWrap='CJK'))

    data=[[cell(c,ri,ci) for ci,c in enumerate(row)]
          for ri,row in enumerate(padded)]
    t=Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0),  BLUE_DIM),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),row_alt),
        ("GRID",         (0,0),(-1,-1), 0.4, DIM),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",  (0,0),(-1,-1), 6),
        ("RIGHTPADDING", (0,0),(-1,-1), 6),
        ("VALIGN",       (0,0),(-1,-1),"TOP"),
    ]))
    return t


# ── Parser ─────────────────────────────────────────────────────────────────────
def parse(md, S):
    story=[]
    lines=md.split("\n")
    i=0; in_code=False; code_buf=[]; in_box=False; box_buf=[]

    def flush_code():
        if not code_buf: return
        story.append(Spacer(1,4))
        for ln in code_buf:
            safe=san(ln); safe=safe.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            story.append(Paragraph(safe or " ", S["code"]))
        story.append(Spacer(1,6)); code_buf.clear()

    def flush_box():
        if not box_buf: return
        rows=parse_box_table(box_buf)
        if rows:
            t=make_table(rows,S)
            if t:
                story.append(Spacer(1,4)); story.append(t); story.append(Spacer(1,6))
        box_buf.clear()

    def rule():
        story.append(Spacer(1,3))
        story.append(HRFlowable(width="100%",thickness=0.5,color=DIM,spaceAfter=4))

    while i<len(lines):
        line=lines[i]; s=line.strip()

        if s.startswith("```"):
            if in_box: flush_box(); in_box=False
            if in_code: flush_code(); in_code=False
            else: in_code=True
            i+=1; continue

        if in_code:
            code_buf.append(line); i+=1; continue

        if is_box(line):
            if not in_box: in_box=True
            box_buf.append(line); i+=1; continue
        else:
            if in_box: flush_box(); in_box=False

        if not s:
            story.append(Spacer(1,4)); i+=1; continue

        m=re.match(r'^(\d+(?:\.\d+)*)\.?\s{2,}(.+)$',s)
        if m:
            num,title=m.group(1),san(m.group(2)); depth=num.count(".")
            label=f"{num}.  {title}"
            if depth==0:   rule(); story.append(Paragraph(label,S["h1"]))
            elif depth==1: story.append(Paragraph(label,S["h2"]))
            else:          story.append(Paragraph(label,S["h3"]))
            i+=1; continue

        m=re.match(r'^([A-C]\.\d+)\.\s+(.+)$',s)
        if m:
            story.append(Paragraph(f"{m.group(1)}.  {san(m.group(2))}",S["h3"]))
            i+=1; continue

        if s in ("Abstract","Status of This Memo","Copyright Notice",
                 "Acknowledgements","Table of Contents","References","Author's Address"):
            rule(); story.append(Paragraph(s,S["h1"])); i+=1; continue

        text=fmt(s)
        if re.match(r'^\([a-z]\)',s) or re.match(r'^\d+\.\s',s):
            story.append(Paragraph(text,S["bullet"]))
        else:
            story.append(Paragraph(text,S["body"]))
        i+=1

    if in_code: flush_code()
    if in_box:  flush_box()
    return story


# ── Invariants table ───────────────────────────────────────────────────────────
def inv_table(S):
    rows=[
        ["Invariant",  "Standard",  "Property"],
        ["ATF-INV-001","RFC-ATF-1","Monotonic Authority Reduction (MAR)"],
        ["ATF-INV-002","RFC-ATF-1","All DRs signed by delegating principal"],
        ["ATF-INV-003","RFC-ATF-1","Chain root traceability to Tier-1"],
        ["ATF-INV-004","RFC-ATF-1","No grant exceeds maximum authority budget"],
        ["ATF-INV-005","RFC-ATF-1","Receipt immutability"],
        ["ATF-INV-006","RFC-ATF-1","Independent verifiability without platform"],
        ["RGC-INV-001","RFC-ATF-2","Every RCR anchored to a valid TAR"],
        ["RGC-INV-002","RFC-ATF-2","CES computed from real-time values only"],
        ["RGC-INV-003","RFC-ATF-2","HALT terminates execution and revokes sub-tasks"],
        ["RGC-INV-004","RFC-ATF-2","Aggregate budget never exceeds AFG limit"],
        ["RGC-INV-005","RFC-ATF-2","All RCRs PQC-signed and immutable"],
        ["RGC-INV-006","RFC-ATF-2","Continuity chain is acyclic and monotonic"],
        ["RGC-INV-007","RFC-ATF-2","CES inputs must meet freshness requirements"],
        ["RGC-INV-008","RFC-ATF-2","RC TTL enforced -- auto-HALT on expiry"],
    ]
    aw=W-ML-MR; cw=[aw*0.22,aw*0.20,aw*0.58]

    def c(txt,ri,ci):
        is_h=ri==0
        color=WHITE if is_h else (BLUE if rows[ri][1]=="RFC-ATF-1" else PURPLE)
        return Paragraph(txt, ParagraphStyle("ic",
            fontName=HF if is_h else (MF if ci==0 else BF),
            fontSize=8, textColor=color, leading=11))

    data=[[c(col,ri,ci) for ci,col in enumerate(row)]
          for ri,row in enumerate(rows)]
    t=Table(data,colWidths=cw,repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  BLUE_DIM),
        ("ROWBACKGROUNDS",(0,1),(-1,6),
         [HexColor("#0f1a35"),HexColor("#0a1428")]),
        ("ROWBACKGROUNDS",(0,7),(-1,-1),
         [HexColor("#1a0f35"),HexColor("#140a28")]),
        ("GRID",         (0,0),(-1,-1),0.4,DIM),
        ("TOPPADDING",   (0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",  (0,0),(-1,-1),6),
        ("RIGHTPADDING", (0,0),(-1,-1),6),
    ]))
    return t


TOC=[
    ("1.", "Introduction",False),
    ("2.", "Problem Statement: The Runtime Governance Gap",False),
    ("3.", "Conventions and Terminology",False),
    ("4.", "Architecture: RGC Layer",False),
    ("4.1.","Position in the ATF Stack",True),
    ("4.2.","Session Lifecycle",True),
    ("4.3.","Relationship to TAR",True),
    ("5.", "Runtime Continuity Record (RCR)",False),
    ("6.", "Continuity Eligibility Score (CES)",False),
    ("7.", "Continuity Chain",False),
    ("8.", "Authority Fragmentation Guard (AFG)",False),
    ("9.", "Escalation Protocol",False),
    ("10.","Reauthorization Challenge (RC)",False),
    ("11.","Sampling Strategy",False),
    ("12.","RGC Invariants",False),
    ("13.","Wire Format",False),
    ("14.","Verification Protocol",False),
    ("15.","Persistence Schema",False),
    ("16.","API Endpoints",False),
    ("17.","Security Considerations",False),
    ("18.","Compliance Mapping",False),
    ("19.","Extension Points",False),
    ("20.","Relationship to RFC-ATF-1",False),
    ("21.","References",False),
    ("22.","Appendix A -- CES Computation Examples",False),
    ("23.","Appendix B -- RGC Compliance Checklist",False),
    ("24.","Appendix C -- Implementation Notes",False),
]


def build_toc(S):
    items=[Paragraph("Table of Contents",S["toc_h"]),
           HRFlowable(width="100%",thickness=0.5,color=DIM,spaceAfter=6)]
    for num,title,sub in TOC:
        items.append(Paragraph(f"{num}  {title}",
                               S["toc_s"] if sub else S["toc_e"]))
    return items


# ── Generate ───────────────────────────────────────────────────────────────────
def generate():
    out="docs/submissions/RFC-ATF-2.pdf"
    os.makedirs("docs/submissions",exist_ok=True)

    doc=SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
        title="RFC-ATF-2: Agent Trust Fabric -- Runtime Governance Continuity",
        author="Harold Nunes -- OMNIX QUANTUM LTD",
        subject="Runtime Governance Continuity Extension to RFC-ATF-1",
        keywords="AI governance,ATF,post-quantum,Dilithium-3,runtime continuity"
    )

    S=build_styles()
    story=[]
    story.append(PageBreak())   # page 1 = cover (callback)

    story.extend(build_toc(S))
    story.append(PageBreak())

    story.append(Paragraph("Invariants Reference -- All 14 ATF Invariants",S["h1"]))
    story.append(Spacer(1,5))
    story.append(inv_table(S))
    story.append(Paragraph(
        "ATF-INV-001 through ATF-INV-006 proven in TLA+ (same methodology as "
        "AWS DynamoDB and Azure Cosmos DB). RGC-INV-001 through RGC-INV-008 "
        "verified by reference implementation test suite (82 tests, 82 passing).",
        S["cap"]))
    story.append(PageBreak())

    with open("docs/standards/RFC-ATF-2.md") as f:
        md=f.read()
    lines=md.split("\n")
    if lines and lines[0].strip()=="```":   lines=lines[1:]
    if lines and lines[-1].strip()=="```":  lines=lines[:-1]
    md="\n".join(lines)

    story.extend(parse(md,S))

    doc.build(story, onFirstPage=cover_page, onLaterPages=dark_bg)
    size=os.path.getsize(out)
    print(f"Generated: {out}  ({size//1024} KB)")


if __name__=="__main__":
    generate()
