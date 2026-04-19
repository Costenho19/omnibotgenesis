"""
OMNIX QUANTUM LTD
Email Evidence Annex Generator
Harold Alberto Nunes Rodelo vs. Mushtaque Ahmed Rajput & Jorge Andrés Charlin Mardones
UK IPO Mediation Reference

Generates: OMNIX_EMAIL_EVIDENCE_ANNEX.pdf
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    PageBreak, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from PIL import Image as PILImage

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS_DIR = os.path.join(BASE_DIR, "attached_assets")
OUTPUT     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "OMNIX_EMAIL_EVIDENCE_ANNEX.pdf")

# ── Page geometry ──────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN   = 2.0 * cm
USABLE_W = PAGE_W - 2 * MARGIN

# ── Colour palette ─────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#0D1B2A")
BLUE   = colors.HexColor("#1B4F8A")
GOLD   = colors.HexColor("#C8A951")
RED    = colors.HexColor("#8B1A1A")
GREEN  = colors.HexColor("#1A5C2A")
ORANGE = colors.HexColor("#B35A00")
LGRAY  = colors.HexColor("#F2F4F7")
MGRAY  = colors.HexColor("#D0D5DD")
WHITE  = colors.white
BLACK  = colors.black

# ── Styles ─────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, **kw)

sTitle  = S("sTitle",  fontName="Helvetica-Bold",   fontSize=26, textColor=WHITE,  alignment=TA_CENTER, spaceAfter=6)
sSub    = S("sSub",    fontName="Helvetica",         fontSize=13, textColor=GOLD,   alignment=TA_CENTER, spaceAfter=4)
sMeta   = S("sMeta",   fontName="Helvetica",         fontSize=10, textColor=MGRAY,  alignment=TA_CENTER, spaceAfter=2)
sSecHdr = S("sSecHdr", fontName="Helvetica-Bold",    fontSize=13, textColor=WHITE,  alignment=TA_LEFT,   spaceAfter=4)
sBody   = S("sBody",   fontName="Helvetica",         fontSize=9,  textColor=BLACK,  alignment=TA_JUSTIFY, spaceAfter=4, leading=13)
sBold   = S("sBold",   fontName="Helvetica-Bold",    fontSize=9,  textColor=NAVY,   alignment=TA_LEFT,   spaceAfter=4)
sLabel  = S("sLabel",  fontName="Helvetica-Bold",    fontSize=8,  textColor=WHITE,  alignment=TA_CENTER)
sNote   = S("sNote",   fontName="Helvetica-Oblique", fontSize=8,  textColor=BLUE,   alignment=TA_LEFT,   spaceAfter=3)
sSmall  = S("sSmall",  fontName="Helvetica",         fontSize=7.5,textColor=colors.HexColor("#555555"), alignment=TA_LEFT)
sExhHdr = S("sExhHdr", fontName="Helvetica-Bold",    fontSize=11, textColor=NAVY,   alignment=TA_LEFT,   spaceAfter=4)
sExhBody= S("sExhBody",fontName="Helvetica",         fontSize=8,  textColor=BLACK,  alignment=TA_JUSTIFY, spaceAfter=3, leading=12)
sExhCode= S("sExhCode",fontName="Courier",           fontSize=7.5,textColor=colors.HexColor("#1A1A1A"), alignment=TA_LEFT, spaceAfter=2, leading=11)

# ── Helper: fit image to usable width (with optional max height) ───────────
def img_flowable(filename, max_h_cm=None):
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        return Paragraph(f"[IMAGE NOT FOUND: {filename}]", sNote)
    try:
        with PILImage.open(path) as im:
            w_px, h_px = im.size
        aspect = h_px / w_px
        w = USABLE_W
        h = w * aspect
        if max_h_cm:
            max_h = max_h_cm * cm
            if h > max_h:
                h = max_h
                w = h / aspect
        return RLImage(path, width=w, height=h)
    except Exception as e:
        return Paragraph(f"[ERROR loading {filename}: {e}]", sNote)

# ── Helper: section banner ─────────────────────────────────────────────────
def section_banner(label, colour, date_str, description):
    banner_data = [[Paragraph(label, sSecHdr)]]
    banner = Table(banner_data, colWidths=[USABLE_W])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colour),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING",   (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
    ]))
    items = [banner]
    if date_str:
        items.append(Spacer(1, 3))
        items.append(Paragraph(f"<b>Date/Time:</b> {date_str}", sBold))
    if description:
        items.append(Paragraph(description, sBody))
    items.append(Spacer(1, 6))
    return items

# ── Helper: key-value table ────────────────────────────────────────────────
def kv_table(rows, col1_w=5.5*cm):
    data = [[Paragraph(f"<b>{k}</b>", sSmall), Paragraph(v, sSmall)] for k,v in rows]
    t = Table(data, colWidths=[col1_w, USABLE_W - col1_w])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), LGRAY),
        ("GRID",         (0,0), (-1,-1), 0.4, MGRAY),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
    ]))
    return t

# ── Helper: highlight box ──────────────────────────────────────────────────
def highlight_box(text, colour=GOLD, bg=None):
    bg = bg or colors.HexColor("#FFFBE6")
    data = [[Paragraph(text, S("hb", fontName="Helvetica-Bold", fontSize=8.5,
                                textColor=colour, alignment=TA_LEFT, leading=13))]]
    t = Table(data, colWidths=[USABLE_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), bg),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("BOX",           (0,0), (-1,-1), 1.2, colour),
    ]))
    return t

# ══════════════════════════════════════════════════════════════════════════
def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title="OMNIX Email Evidence Annex",
        author="Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD",
    )

    story = []

    # ── COVER PAGE ─────────────────────────────────────────────────────────
    cover_data = [[
        Paragraph("OMNIX QUANTUM LTD", sTitle),
    ]]
    cover = Table(cover_data, colWidths=[USABLE_W])
    cover.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("TOPPADDING",    (0,0), (-1,-1), 30),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 20),
        ("RIGHTPADDING",  (0,0), (-1,-1), 20),
    ]))
    story.append(cover)
    story.append(Spacer(1, 0.3*cm))

    sub_data = [[Paragraph("EMAIL EVIDENCE ANNEX", sSub)]]
    sub_tbl = Table(sub_data, colWidths=[USABLE_W])
    sub_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), BLUE),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(sub_tbl)
    story.append(Spacer(1, 0.4*cm))

    meta_rows = [
        ("Matter",     "IP Ownership Dispute — OMNIX Decision Governance Infrastructure"),
        ("Claimant",   "Harold Alberto Nunes Rodelo, Founder & CEO, OMNIX QUANTUM LTD"),
        ("Respondents","Mushtaque Ahmed Rajput (VITT Protocol) &amp; Jorge Andrés Charlin Mardones"),
        ("Forum",      "UK IPO Mediation Service"),
        ("Prepared",   "April 2026"),
        ("Contents",   "17 email screenshots + Terra/LUNA Forensic Report text exhibit"),
    ]
    story.append(kv_table(meta_rows, col1_w=4.5*cm))
    story.append(Spacer(1, 0.5*cm))

    story.append(highlight_box(
        "⚠  LEGAL NOTICE: This document is submitted as evidence to the UK IPO Mediation Service. "
        "All contents are true and accurate to the best of the declarant's knowledge. "
        "Unauthorised reproduction or distribution is prohibited.",
        colour=NAVY, bg=LGRAY
    ))
    story.append(Spacer(1, 0.5*cm))

    # ── EXECUTIVE SUMMARY ──────────────────────────────────────────────────
    summary_hdr = [[Paragraph("EXECUTIVE SUMMARY — KEY FACTS", sSecHdr)]]
    sh = Table(summary_hdr, colWidths=[USABLE_W])
    sh.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NAVY),
        ("LEFTPADDING",(0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",(0,0), (-1,-1), 7),
    ]))
    story.append(sh)
    story.append(Spacer(1, 4))

    facts = [
        ("1. Independent Development",
         "OMNIX Decision Governance Infrastructure was developed independently by Harold Alberto Nunes Rodelo. "
         "All core architectural elements — fail-closed pipeline, sovereign gate logic, PQC-signed receipts — "
         "predate any contact with Mushtaque Ahmed Rajput or Jorge Andrés Charlin Mardones."),
        ("2. Unsolicited Contact",
         "Mushtaque Ahmed Rajput initiated unsolicited contact with Harold Nunes. "
         "At no point did Harold seek, request, or adopt VITT Protocol methodology into OMNIX architecture."),
        ("3. Key Email — March 24, 4:29 AM",
         "Mushtaque explicitly wrote: 'I just need the written record on my end so our IP trail is clean "
         "going into April.' This statement can be reasonably interpreted as an attempt to establish an IP "
         "record timed to coincide with Harold's investor activities, rather than a pre-existing good-faith claim."),
        ("4. Written Acceptance of OMNIX Independence — March 25, 3:31 AM",
         "Mushtaque explicitly accepted Harold's position in writing: 'I fully appreciate the strategic need "
         "to keep OMNIX Quantum's architecture and IP independent.' This acceptance was voluntary and unequivocal."),
        ("5. Escalation Despite Acceptance",
         "Only 46 minutes after accepting independence (3:31 AM), Mushtaque sent a FORMAL NOTICE at 4:17 AM "
         "on March 25 with Jorge Charlin copied — a coordinated escalation immediately contradicting his acceptance."),
        ("6. The Terra/LUNA Report",
         "The forensic simulation report (March 13, 2026) was an exploratory demonstration generated by OMNIX "
         "and shared with Mushtaque. The VITT references in that document were included by Harold as a courtesy "
         "reference to ongoing exploratory discussions — not as an architectural integration. "
         "Mushtaque's prior email on March 14 demanding IP ownership predates any claim that OMNIX 'incorporated' VITT."),
        ("7. Charlin's Communication — March 26",
         "Jorge Andrés Charlin Mardones wrote to Harold on March 26 making similar demands — "
         "citing the same Terra/LUNA report. The timing and content of both communications "
         "indicates coordinated communication between Mushtaque and Charlin."),
    ]

    for title, body in facts:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>{title}</b>", sBold))
        story.append(Paragraph(body, sBody))
    story.append(HRFlowable(width=USABLE_W, thickness=0.5, color=MGRAY))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 1 — Terra/LUNA Report Shared (March 13)
    # ═══════════════════════════════════════════════════════════════════════
    story += section_banner(
        "SECTION 1 — TERRA/LUNA REPORT SHARED WITH MUSHTAQUE (March 13, 2026 — 3:14 PM)",
        BLUE,
        "13 March 2026, 3:14 PM — From: harold nunes <contacto@omnixquantum.net> To: Mushtaque Ahmed Rajput",
        "Harold shares the OMNIX × VITT Terra/LUNA Forensic Reconstruction Report with Mushtaque. "
        "This was an exploratory courtesy document. The email confirms Mushtaque had 'Seen' it by 2:59 PM, "
        "establishing he received it directly from Harold — not that he authored or contributed to the methodology."
    )
    story.append(img_flowable("image_1776630926518.png", max_h_cm=12))
    story.append(Spacer(1, 6))
    story.append(highlight_box(
        "KEY POINT: The Terra/LUNA report was generated and shared BY HAROLD to Mushtaque as an exploratory "
        "demonstration. Mushtaque received it — he did not author or contribute to it. "
        "Any VITT references in it were included by Harold as courtesy mentions of ongoing discussions, "
        "not as a formal architectural integration. Mushtaque's March 14 IP demand came the very next day.",
        colour=BLUE, bg=colors.HexColor("#EBF0FA")
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 2 — First Formal IP Claim (March 14)
    # ═══════════════════════════════════════════════════════════════════════
    story += section_banner(
        "SECTION 2 — FIRST FORMAL IP CLAIM BY MUSHTAQUE (March 14, 2026 — 6:17 PM)",
        RED,
        "14 March 2026, 6:17 PM — From: Mushtaque Ahmed Rajput To: Harold Nunes",
        "Subject: 'Formal Statement of IP Ownership — VITT Protocol Integration in OMNIX Framework'. "
        "One day after receiving the Terra/LUNA report, Mushtaque sends a formal IP ownership claim. "
        "This sequence — receive exploratory report → immediately send formal IP demand — reveals the strategy."
    )
    story.append(img_flowable("image_1776630217866.png", max_h_cm=13))
    story.append(Spacer(1, 8))
    story.append(img_flowable("image_1776630256000.png", max_h_cm=13))
    story.append(Spacer(1, 6))
    story.append(highlight_box(
        "KEY POINT: Mushtaque's formal IP claim came within 24 hours of receiving the Terra/LUNA exploratory report. "
        "He had never previously asserted formal IP ownership. This reactive pattern demonstrates opportunistic "
        "IP construction, not a pre-existing good-faith claim.",
        colour=RED, bg=colors.HexColor("#FAF0F0")
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 3 — "IP Trail" Request (March 24, 4:29 AM)
    # ═══════════════════════════════════════════════════════════════════════
    story += section_banner(
        "SECTION 3 — \"IP TRAIL\" REQUEST (March 24, 2026 — 4:29 AM) — KEY DOCUMENT",
        RED,
        "24 March 2026, 4:29 AM — From: Mushtaque Ahmed Rajput To: Harold Nunes",
        "Mushtaque asks Harold for a written confirmation before March 31 to 'keep the IP trail clean going into April.' "
        "He adds: 'No changes to your investor narrative, no public disclosure, this stays between us.' "
        "This email can be reasonably interpreted as an attempt to establish an IP record ahead of Harold's "
        "March 31 investor activities, rather than a reflection of a pre-existing formal IP claim."
    )
    story.append(img_flowable("image_1776630484213.png", max_h_cm=14))
    story.append(Spacer(1, 6))
    story.append(highlight_box(
        "KEY DOCUMENT — EXACT QUOTE: \"I just need the written record on my end so our IP trail is clean "
        "going into April. One paragraph from you is enough.\"\n\n"
        "This statement, read in context, can be reasonably interpreted as an attempt to establish an IP "
        "record timed to April investor activities. Harold declined this request in writing on the same day.",
        colour=RED, bg=colors.HexColor("#FAF0F0")
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 4 — Harold Declines (March 24, 6:46 PM)
    # ═══════════════════════════════════════════════════════════════════════
    story += section_banner(
        "SECTION 4 — HAROLD DECLINES — OMNIX INDEPENDENCE MAINTAINED (March 24, 2026 — 6:46 PM)",
        GREEN,
        "24 March 2026, 6:46 PM — From: harold nunes <contacto@omnixquantum.net> To: Mushtaque Ahmed Rajput",
        "Harold responds to the March 24 request, clearly and professionally declining to provide any written "
        "confirmation of VITT integration. He states: 'I need to keep OMNIX Quantum's architecture and IP "
        "clearly defined and independent.' Any potential future alignment would require investor alignment first."
    )
    story.append(img_flowable("image_1776630435669.png", max_h_cm=14))
    story.append(Spacer(1, 6))
    story.append(highlight_box(
        "KEY POINT: Harold's response is professional and unambiguous. OMNIX independence is non-negotiable. "
        "No IP relationship with VITT exists or will be confirmed. Any future collaboration would require "
        "investor guidance — which was never sought or obtained.",
        colour=GREEN, bg=colors.HexColor("#F0FAF3")
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 5 — Mushtaque Accepts Independence (March 25, 3:31 AM)
    # ═══════════════════════════════════════════════════════════════════════
    story += section_banner(
        "SECTION 5 — MUSHTAQUE ACCEPTS OMNIX INDEPENDENCE IN WRITING (March 25, 2026 — 3:31 AM)",
        GREEN,
        "25 March 2026, 3:31 AM — From: Mushtaque Ahmed Rajput To: Harold Nunes",
        "In direct response to Harold's March 24 decline, Mushtaque writes: 'Thank you for the clarity. "
        "I fully appreciate the strategic need to keep OMNIX Quantum's architecture and IP independent.' "
        "He confirms VITT will remain 'a clearly defined, independent architectural layer.' "
        "This constitutes a written acknowledgment of OMNIX independence."
    )
    story.append(img_flowable("image_1776630558114.png", max_h_cm=14))
    story.append(Spacer(1, 6))
    story.append(highlight_box(
        "WRITTEN ACKNOWLEDGMENT — EXACT QUOTE: \"I fully appreciate the strategic need to keep OMNIX Quantum's "
        "architecture and IP independent... I will ensure that the VITT Protocol remains a clearly defined, "
        "independent architectural layer.\"\n\n"
        "This written acknowledgment, made voluntarily and explicitly, is inconsistent with any subsequent "
        "claim that OMNIX wrongfully appropriated VITT methodology.",
        colour=GREEN, bg=colors.HexColor("#F0FAF3")
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 6 — FORMAL NOTICE (March 25, 4:17 AM)
    # ═══════════════════════════════════════════════════════════════════════
    story += section_banner(
        "SECTION 6 — ESCALATION: FORMAL NOTICE WITH CHARLIN COPIED (March 25, 2026 — 4:17 AM)",
        RED,
        "25 March 2026, 4:17 AM — From: Mushtaque Ahmed Rajput To: Harold Nunes (+ Jorge Charlin CC'd)",
        "Only 46 minutes after accepting independence (3:31 AM), Mushtaque sends a FORMAL NOTICE at 4:17 AM "
        "with Jorge Andrés Charlin Mardones copied. This coordinated escalation directly contradicts the "
        "acceptance sent moments earlier, revealing a pre-planned strategy."
    )
    story.append(img_flowable("image_1776630296687.png", max_h_cm=10))
    story.append(Spacer(1, 6))
    story.append(img_flowable("image_1776630333219.png", max_h_cm=10))
    story.append(Spacer(1, 6))
    story.append(img_flowable("image_1776630365902.png", max_h_cm=10))
    story.append(Spacer(1, 6))
    story.append(highlight_box(
        "KEY POINT — 46 MINUTE SEQUENCE: At 3:31 AM Mushtaque provided a written acknowledgment of OMNIX "
        "independence. At 4:17 AM — 46 minutes later — he sent a FORMAL NOTICE with Charlin copied. "
        "The proximity of these two communications raises questions about the basis and timing of the "
        "formal notice, which followed immediately after a written acknowledgment of independence.",
        colour=RED, bg=colors.HexColor("#FAF0F0")
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 7 — Charlin's Direct Claim (March 26, 4:10 PM)
    # ═══════════════════════════════════════════════════════════════════════
    story += section_banner(
        "SECTION 7 — CHARLIN'S DIRECT IP CLAIM (March 26, 2026 — 4:10 PM)",
        ORANGE,
        "26 March 2026, 4:10 PM — From: Jorge Andrés Charlin Mardones <charlineasternpact@gmail.com> To: Harold Nunes",
        "Subject: 'VITT Protocol — Authorship and Intellectual Property Clarification'. "
        "Charlin writes independently to Harold claiming the Terra/LUNA report (March 13) incorporates VITT "
        "as a methodology within its framework without attribution. He cites the Zenodo DOI "
        "(10.5281/zenodo.18685499) and requests written acknowledgment. "
        "The timing of this outreach — the day after the FORMAL NOTICE — indicates coordinated communication."
    )
    story.append(img_flowable("image_1776630630490.png", max_h_cm=10))
    story.append(Spacer(1, 6))
    story.append(img_flowable("image_1776630651001.png", max_h_cm=12))
    story.append(Spacer(1, 6))
    story.append(img_flowable("image_1776630671145.png", max_h_cm=12))
    story.append(Spacer(1, 6))
    story.append(img_flowable("image_1776630686608.png", max_h_cm=10))
    story.append(Spacer(1, 6))
    story.append(highlight_box(
        "KEY POINT: Charlin's email arrives the day after Mushtaque's FORMAL NOTICE, making similar claims "
        "about the same document. The timing and alignment of both communications indicates coordinated "
        "communication between the two parties. Charlin identifies as 'Lead Author, VITT Protocol' — "
        "the same paper co-authored with Mushtaque.",
        colour=ORANGE, bg=colors.HexColor("#FFF5EB")
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 8 — Harold's Response to Charlin (March 26, 4:29 PM)
    # ═══════════════════════════════════════════════════════════════════════
    story += section_banner(
        "SECTION 8 — HAROLD'S RESPONSE TO CHARLIN (March 26, 2026 — 4:29 PM)",
        GREEN,
        "26 March 2026, 4:29 PM — From: harold nunes <contacto@omnixquantum.net> To: Charlin",
        "Harold responds clearly: OMNIX does not integrate, implement, or rely on VITT. "
        "He explicitly identifies Mushtaque as the source of any VITT association — not OMNIX itself. "
        "He states: 'At no point has OMNIX formally accepted, incorporated, or agreed to integrate "
        "the VITT Protocol or any of its components.'"
    )
    story.append(img_flowable("image_1776630705343.png", max_h_cm=14))
    story.append(Spacer(1, 6))
    story.append(highlight_box(
        "KEY STATEMENT — EXACT QUOTE: \"Any reference or association with VITT does not originate from OMNIX "
        "directly, but rather relates to an external third party, specifically Mushtaque Ahmed Rajput, who "
        "has independently expressed interest in engaging with OMNIX. At no point has OMNIX formally accepted, "
        "incorporated, or agreed to integrate the VITT Protocol or any of its components.\"",
        colour=GREEN, bg=colors.HexColor("#F0FAF3")
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 9 — Charlin's Counter-Response (March 27, 3:52 AM)
    # ═══════════════════════════════════════════════════════════════════════
    story += section_banner(
        "SECTION 9 — CHARLIN'S COUNTER-RESPONSE CITING TERRA/LUNA REPORT (March 27, 2026 — 3:52 AM)",
        ORANGE,
        "27 March 2026, 3:52 AM — From: Charlin To: Harold Nunes",
        "Charlin responds citing four specific verbatim quotes from the Terra/LUNA report: "
        "(1) Cover page methodology field; (2) Executive Summary page 2; "
        "(3) Framework Comparison table page 7 header; (4) Conclusion page 8. "
        "He argues these constitute VITT being used 'as a core part of the methodology and framework' "
        "without attribution or DOI citation."
    )
    story.append(img_flowable("image_1776630723357.png", max_h_cm=10))
    story.append(Spacer(1, 6))
    story.append(img_flowable("image_1776630742614.png", max_h_cm=12))
    story.append(Spacer(1, 6))
    story.append(img_flowable("image_1776630760747.png", max_h_cm=12))
    story.append(Spacer(1, 6))
    story.append(img_flowable("image_1776630777170.png", max_h_cm=12))
    story.append(Spacer(1, 6))
    story.append(highlight_box(
        "RESPONSE: The Terra/LUNA document was an exploratory courtesy simulation — not an architectural "
        "integration document. VITT was referenced as part of an exploratory discussion that Harold explicitly "
        "declined to formalise (March 24). The report itself was generated BEFORE Mushtaque's formal IP "
        "demands began. Furthermore, Mushtaque's own acceptance email (March 25, 3:31 AM) confirms VITT "
        "remains a 'clearly defined, independent architectural layer' — acknowledging it is NOT part of OMNIX.",
        colour=ORANGE, bg=colors.HexColor("#FFF5EB")
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════
    # EXHIBIT A — Only the 4 quotes Charlin cited from the Terra/LUNA Report
    # ═══════════════════════════════════════════════════════════════════════
    exh_hdr_data = [[Paragraph(
        "EXHIBIT A — VERBATIM PASSAGES CITED BY CHARLIN FROM THE TERRA/LUNA REPORT\n"
        "Report: OMNIX DGI — Terra/LUNA Forensic Simulation | Generated: March 13, 2026",
        sSecHdr
    )]]
    exh_hdr = Table(exh_hdr_data, colWidths=[USABLE_W])
    exh_hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(exh_hdr)
    story.append(Spacer(1, 6))
    story.append(highlight_box(
        "This exhibit reproduces only the four verbatim passages that Jorge Charlin cited in his email "
        "of 27 March 2026 (Section 9), along with the contextual clarification for each. "
        "These passages were already disclosed to both Mushtaque Ahmed Rajput (March 13, 2026) "
        "and to Charlin by his own quotation. No additional technical content is disclosed here.",
        colour=BLUE, bg=colors.HexColor("#EBF0FA")
    ))
    story.append(Spacer(1, 10))

    quoted_passages = [
        (
            "Quote 1 — Cover Page, Methodology Field",
            "\"8-Checkpoint Fail-Closed Pipeline + 3-Phase VITT Forensic Alignment\"",
            "Context: This is the methodology descriptor field on the report cover page. "
            "It reflects the exploratory framing of the simulation at the time it was drafted "
            "and shared with Mushtaque on March 13. The 8-Checkpoint Fail-Closed Pipeline is "
            "an OMNIX-native architecture. The VITT reference in this field was a courtesy "
            "descriptor for an exploratory discussion that Harold subsequently declined to formalise "
            "in writing (March 24, 6:46 PM)."
        ),
        (
            "Quote 2 — Executive Summary, Page 2",
            "\"OMNIX's 8-checkpoint fail-closed governance pipeline, combined with the VITT "
            "framework's Forensic Invariance methodology\"",
            "Context: This passage appears in the executive summary of an exploratory simulation "
            "document. It does not constitute a formal integration agreement, a co-authorship "
            "declaration, or an acknowledgment of IP rights. The document was generated by OMNIX "
            "and shared with Mushtaque. Mushtaque's own written acknowledgment of March 25 "
            "confirms VITT remains 'a clearly defined, independent architectural layer.'"
        ),
        (
            "Quote 3 — Framework Comparison Table, Page 7 (Column Header)",
            "\"OMNIX + VITT (Forensic Governance)\"",
            "Context: This is a column header in a comparative table within an exploratory "
            "simulation report. It was used as a descriptive label for the purposes of the "
            "simulation only. It does not reflect a formal architectural integration, a licensing "
            "arrangement, or any agreed IP relationship between OMNIX and VITT Protocol."
        ),
        (
            "Quote 4 — Conclusion, Page 8",
            "\"Forensic governance — as embodied in the OMNIX + VITT framework alignment\"",
            "Context: This phrase appears in the conclusion of the exploratory simulation. "
            "The word 'alignment' was used in the context of a hypothetical exploratory scenario, "
            "not as confirmation of a formal agreement. Harold declined to provide any such "
            "written confirmation when requested by Mushtaque on March 24, 2026."
        ),
    ]

    for title, quote, context in quoted_passages:
        story.append(Paragraph(f"<b>{title}</b>", sExhHdr))
        quote_data = [[Paragraph(quote, S("q", fontName="Courier-Bold", fontSize=8.5,
                                          textColor=NAVY, alignment=TA_LEFT, leading=13))]]
        quote_tbl = Table(quote_data, colWidths=[USABLE_W])
        quote_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), LGRAY),
            ("LEFTPADDING",   (0,0), (-1,-1), 12),
            ("RIGHTPADDING",  (0,0), (-1,-1), 12),
            ("TOPPADDING",    (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("BOX",           (0,0), (-1,-1), 0.8, MGRAY),
        ]))
        story.append(quote_tbl)
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Contextual clarification:</b> {context}", sExhBody))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width=USABLE_W, thickness=0.4, color=MGRAY))
        story.append(Spacer(1, 8))

    story.append(PageBreak())

    # ── ATTESTATION ────────────────────────────────────────────────────────
    att_hdr_data = [[Paragraph("ATTESTATION", sSecHdr)]]
    att_hdr = Table(att_hdr_data, colWidths=[USABLE_W])
    att_hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(att_hdr)
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "I, Harold Alberto Nunes Rodelo, Founder and CEO of OMNIX QUANTUM LTD (registered in England and Wales), "
        "hereby attest that:",
        sBody
    ))
    story.append(Spacer(1, 6))

    att_points = [
        "All screenshots and documents contained in this Email Evidence Annex are authentic and unaltered.",
        "The email communications presented represent complete, unedited exchanges between the parties identified.",
        "The Terra/LUNA Forensic Simulation Report (Exhibit A) was generated by OMNIX QUANTUM LTD on March 13, 2026 "
        "as an exploratory demonstration and shared with Mushtaque Ahmed Rajput. It was not co-authored by either "
        "Mushtaque Ahmed Rajput or Jorge Andrés Charlin Mardones.",
        "OMNIX Decision Governance Infrastructure was developed independently, and no formal IP agreement, "
        "integration agreement, or co-authorship agreement has ever existed between OMNIX QUANTUM LTD and "
        "Mushtaque Ahmed Rajput or Jorge Andrés Charlin Mardones.",
        "This annex is submitted in good faith to the UK IPO Mediation Service as supporting evidence for "
        "the mediation proceedings.",
    ]
    for i, point in enumerate(att_points, 1):
        story.append(Paragraph(f"{i}. {point}", sBody))

    story.append(Spacer(1, 24))

    sig_rows = [
        ["Declarant:", "Harold Alberto Nunes Rodelo"],
        ["Position:",  "Founder & CEO, OMNIX QUANTUM LTD"],
        ["Email:",     "contacto@omnixquantum.net"],
        ["Website:",   "omnixquantum.net"],
        ["Date:",      "April 2026"],
        ["Signature:", "________________________"],
    ]
    story.append(kv_table(sig_rows, col1_w=4.0*cm))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width=USABLE_W, thickness=0.5, color=MGRAY))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "OMNIX QUANTUM LTD — Registered in England and Wales — omnixquantum.net — "
        "UK IPO Mediation Reference — April 2026",
        S("footer", fontName="Helvetica", fontSize=7, textColor=colors.HexColor("#888888"),
          alignment=TA_CENTER)
    ))

    doc.build(story)
    print(f"✅ PDF generated: {OUTPUT}")

if __name__ == "__main__":
    build_pdf()
