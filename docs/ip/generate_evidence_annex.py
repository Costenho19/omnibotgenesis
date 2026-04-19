"""
OMNIX QUANTUM LTD
Evidence Annex Generator — LinkedIn Conversation Screenshots
Harold Alberto Nunes Rodelo vs. Mushtaque Ahmed Rajput (VITT Protocol)
UK IPO Mediation Reference

Generates: OMNIX_EVIDENCE_ANNEX.pdf
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    PageBreak, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from PIL import Image as PILImage

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS_DIR = os.path.join(BASE_DIR, "attached_assets")
LOGO_PATH  = os.path.join(BASE_DIR, "docs", "omnix_quantum_logo.png")
OUTPUT     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "OMNIX_EVIDENCE_ANNEX.pdf")

# ── Page geometry ──────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN = 2.0 * cm
USABLE_W = PAGE_W - 2 * MARGIN
USABLE_H = PAGE_H - 2 * MARGIN

# ── Colour palette ─────────────────────────────────────────────────────────
NAVY    = colors.HexColor("#0D1B2A")
BLUE    = colors.HexColor("#1B4F8A")
GOLD    = colors.HexColor("#C8A951")
RED     = colors.HexColor("#8B1A1A")
LGRAY   = colors.HexColor("#F2F4F7")
MGRAY   = colors.HexColor("#D0D5DD")
WHITE   = colors.white
BLACK   = colors.black

# ── Chronological sections with labels ────────────────────────────────────
# Each entry: (filename_prefix_partial, section_label, date_label)
SECTIONS = [
    # First 5 images — profile / early contact screenshots
    {
        "label": "SECTION 1 — INITIAL CONTACT (March 13, 2026)",
        "colour": BLUE,
        "description": (
            "Mushtaque Ahmed Rajput initiates unsolicited contact with Harold Nunes, "
            "sending VITT protocol documents and proposing a Terra/LUNA collapse forensic "
            "simulation. Harold responds with interest as a professional exchange — "
            "no agreement, no partnership, no IP transfer."
        ),
        "images": [
            "image_1776622926597.png",
            "image_1776624031395.png",
            "image_1776624158221.png",
            "image_1776624233130.png",
            "image_1776624276631.png",
        ]
    },
    {
        "label": "SECTION 2 — EXPLORATORY TECHNICAL DISCUSSION (March 13–14, 2026)",
        "colour": BLUE,
        "description": (
            "Both parties discuss technical concepts. Harold clarifies that OMNIX already "
            "possesses equivalent architectural components independently. The discussion "
            "is framed as two parallel systems, not a joint venture or integration. "
            "No formal agreement is proposed or accepted."
        ),
        "images": [
            "image_1776627212386.png",
            "image_1776627254117.png",
            "image_1776627298907.png",
            "image_1776627325011.png",
            "image_1776627357229.png",
            "image_1776627383526.png",
            "image_1776627402015.png",
            "image_1776627421278.png",
            "image_1776627448252.png",
            "image_1776627477405.png",
            "image_1776627503609.png",
            "image_1776627521246.png",
            "image_1776627552614.png",
            "image_1776627573400.png",
            "image_1776627593016.png",
            "image_1776627608932.png",
            "image_1776627631284.png",
            "image_1776627647152.png",
            "image_1776627664974.png",
            "image_1776627713759.png",
            "image_1776627746945.png",
            "image_1776627768402.png",
            "image_1776627787682.png",
            "image_1776627805426.png",
            "image_1776627822803.png",
            "image_1776627842611.png",
            "image_1776627858927.png",
            "image_1776627879306.png",
            "image_1776627901548.png",
            "image_1776627922240.png",
            "image_1776627939288.png",
            "image_1776627958489.png",
            "image_1776627975862.png",
            "image_1776627993049.png",
            "image_1776628011686.png",
            "image_1776628030764.png",
            "image_1776628049982.png",
            "image_1776628070364.png",
        ]
    },
    {
        "label": "SECTION 3 — HAROLD ASSERTS INDEPENDENCE / MUSHTAQUE AGREES (March 15, 2026)",
        "colour": GOLD,
        "description": (
            "KEY EVENT: Harold formally asks Mushtaque to remove all public LinkedIn "
            "comments referencing OMNIX, stating 'OMNIX's architecture is 100% independent "
            "and I need that to be clear.' Mushtaque complies, removes all comments and "
            "reposts, and responds: 'I'm glad we're on the same page.' This constitutes "
            "written acknowledgement that no integration or shared IP exists."
        ),
        "images": [
            "image_1776628102111.png",
        ]
    },
    {
        "label": "SECTION 4 — CORDIAL EXCHANGE / PITCH PREPARATION (March 21–22, 2026)",
        "colour": BLUE,
        "description": (
            "Both parties reconnect cordially ahead of Harold's March 31 pitch. "
            "Discussion remains exploratory and philosophical — two independent "
            "professionals discussing parallel approaches to the same problem space. "
            "Mushtaque himself says 'I have deep respect for what you are building with OMNIX.' "
            "No IP claim, no demand, no agreement discussed."
        ),
        "images": [
            "image_1776628118717.png",
        ]
    },
    {
        "label": "SECTION 5 — MUSHTAQUE DEMANDS IP CONFIRMATION / HAROLD DECLINES (March 24–25, 2026)",
        "colour": RED,
        "description": (
            "CRITICAL EVENT: On March 24, Mushtaque emails Harold requesting a 'one-paragraph "
            "confirmation reply' about 'IP alignment (VITT/OMNIX)' to be 'on record before the pitch.' "
            "Harold declines. On March 25, Mushtaque sends formal message claiming 'VITT-OMNIX "
            "Integration Logic' documentation. Harold responds formally: 'We never formalized any "
            "agreement or role between us. You have no authorization to represent OMNIX publicly.' "
            "Mushtaque attempts to cite Harold's academic phrases as IP endorsement. "
            "Harold's rebuttal: 'A technical exchange of perspectives does not constitute "
            "recognition, endorsement, or any form of shared development.'"
        ),
        "images": [
            "image_1776628135033.png",
            "image_1776628154654.png",
            "image_1776628172604.png",
            "image_1776628192166.png",
            "image_1776628209145.png",
            "image_1776628223986.png",
            "image_1776628245906.png",
        ]
    },
    {
        "label": "SECTION 6 — TERRA/LUNA SIMULATION DISPUTE (March 25, late night, 2026)",
        "colour": RED,
        "description": (
            "Mushtaque claims the Terra/LUNA Forensic Simulation Report (March 18, 2026) "
            "is 'main proof' of VITT integration into OMNIX. Harold acknowledges the simulation "
            "was produced jointly as an exploratory technical exercise, but states clearly: "
            "'A one-time collaborative test does not constitute a partnership, a licensing "
            "agreement, or any transfer of intellectual property in either direction. "
            "OMNIX Quantum's governance architecture predates our exchange.' "
            "The VITT methodology appears in that document as part of exploratory alignment, "
            "not as a dependency of OMNIX."
        ),
        "images": [
            "image_1776628264252.png",
            "image_1776628283003.png",
            "image_1776628309531.png",
            "image_1776628325933.png",
        ]
    },
    {
        "label": "SECTION 7 — ESCALATION TO LEGAL THREATS & FINANCIAL DEMANDS (April 10, 2026)",
        "colour": RED,
        "description": (
            "Mushtaque escalates dramatically: invokes US Defend Trade Secrets Act (DTSA), "
            "UAE Federal Law No. 31 of 2021, threatens FTC notification, UAE Ministry of Economy "
            "complaint, and a LinkedIn public campaign targeting OMNIX's mutual professional network. "
            "At 3:51 AM, issues formal Financial Demand: retroactive licensing fee + equity/capital "
            "participation (Carry/Equity share) claiming 'Unjust Enrichment.' Threatens to freeze "
            "incoming investment funds. Deadline: April 12, 2026. "
            "Harold responds by documenting the complete chronological record and refers all "
            "further communications to legal representatives."
        ),
        "images": [
            "image_1776628344094.png",
            "image_1776628362149.png",
            "image_1776628380459.png",
            "image_1776628396523.png",
            "image_1776628444925.png",
            "image_1776628463743.png",
            "image_1776628485107.png",
            "image_1776628515175.png",
            "image_1776628531157.png",
            "image_1776628549244.png",
            "image_1776628569622.png",
            "image_1776628588656.png",
            "image_1776628606956.png",
            "image_1776628624997.png",
            "image_1776628641673.png",
            "image_1776628669333.png",
            "image_1776628686910.png",
            "image_1776628703674.png",
            "image_1776628720663.png",
            "image_1776628736848.png",
            "image_1776628752042.png",
        ]
    },
    {
        "label": "SECTION 8 — HAROLD'S FINAL STATEMENT & CONTINUED HARASSMENT (April 10–19, 2026)",
        "colour": RED,
        "description": (
            "Harold formally refers matter to legal representatives and warns of defamation/harassment "
            "action. Mushtaque continues messaging, claiming two versions of the LUNA report exist "
            "('OMNIX + VITT Forensic Alignment' vs 'OMNIX Forensic Reconstruction'), claiming this "
            "constitutes 'documented admission of IP theft.' Mushtaque mentions awareness of "
            "OMNIX's $500K pre-seed fundraising and threatens to inform investors that their "
            "due diligence is based on 'unauthorized third-party technology.' "
            "This constitutes the pattern of harassment and reputational threat submitted to UK IPO."
        ),
        "images": [
            "image_1776628771079.png",
            "image_1776628786264.png",
            "image_1776628813395.png",
            "image_1776628828232.png",
            "image_1776628845162.png",
            "image_1776628864536.png",
        ]
    },
]

# ── Styles ─────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

style_cover_title = ParagraphStyle(
    "CoverTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=22,
    textColor=WHITE,
    alignment=TA_CENTER,
    leading=28,
)
style_cover_sub = ParagraphStyle(
    "CoverSub",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=11,
    textColor=colors.HexColor("#D0D5DD"),
    alignment=TA_CENTER,
    leading=16,
)
style_cover_gold = ParagraphStyle(
    "CoverGold",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=12,
    textColor=GOLD,
    alignment=TA_CENTER,
    leading=18,
)
style_section_title = ParagraphStyle(
    "SectionTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=11,
    textColor=WHITE,
    leading=15,
)
style_desc = ParagraphStyle(
    "Desc",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    textColor=colors.HexColor("#2D3748"),
    alignment=TA_JUSTIFY,
    leading=13,
    spaceAfter=6,
)
style_caption = ParagraphStyle(
    "Caption",
    parent=styles["Normal"],
    fontName="Helvetica-Oblique",
    fontSize=7.5,
    textColor=colors.HexColor("#718096"),
    alignment=TA_CENTER,
    leading=10,
)
style_toc = ParagraphStyle(
    "TOC",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    textColor=NAVY,
    leading=14,
    leftIndent=10,
)
style_toc_bold = ParagraphStyle(
    "TOCBold",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=9,
    textColor=BLUE,
    leading=14,
)
style_heading = ParagraphStyle(
    "Heading",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=13,
    textColor=NAVY,
    leading=18,
    spaceBefore=4,
)
style_body = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    textColor=NAVY,
    leading=13,
    alignment=TA_JUSTIFY,
)
style_bullet = ParagraphStyle(
    "Bullet",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    textColor=NAVY,
    leading=13,
    leftIndent=12,
    bulletIndent=0,
)
style_warning = ParagraphStyle(
    "Warning",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=9,
    textColor=RED,
    leading=13,
    alignment=TA_CENTER,
)

# ── Helpers ────────────────────────────────────────────────────────────────

def make_cover():
    """Navy cover page."""
    logo_w = 3.8 * cm
    logo_h = logo_w * (438 / 599)
    logo_img = RLImage(LOGO_PATH, width=logo_w, height=logo_h) if os.path.exists(LOGO_PATH) else Spacer(1, logo_h)

    cover_data = [
        [logo_img],
        [Paragraph("OMNIX QUANTUM LTD", style_cover_title)],
    ]
    cover_table = Table(cover_data, colWidths=[USABLE_W])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (0, 0), 22),
        ("BOTTOMPADDING", (0, 0), (0, 0), 6),
        ("TOPPADDING",    (1, 0), (1, 0), 0),
        ("BOTTOMPADDING", (1, 0), (1, 0), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))

    elements = [
        Spacer(1, 1.5 * cm),
        cover_table,
        Spacer(1, 0.5 * cm),
    ]

    # Gold divider
    elements.append(HRFlowable(width=USABLE_W, thickness=2, color=GOLD, spaceAfter=8))

    title_block = [
        [Paragraph("EVIDENCE ANNEX", style_cover_gold)],
        [Paragraph("LinkedIn Conversation — Complete Chronological Record", style_cover_sub)],
        [Spacer(1, 0.3 * cm)],
        [Paragraph("Harold Alberto Nunes Rodelo (OMNIX QUANTUM LTD)", style_cover_sub)],
        [Paragraph("vs.", style_cover_sub)],
        [Paragraph("Mushtaque Ahmed Rajput (VITT Protocol)", style_cover_sub)],
        [Spacer(1, 0.5 * cm)],
        [Paragraph("UK Intellectual Property Office — Mediation Reference", style_cover_gold)],
        [Spacer(1, 0.5 * cm)],
        [Paragraph("Date of Compilation: April 19, 2026", style_cover_sub)],
        [Paragraph("Prepared by: Harold Alberto Nunes Rodelo", style_cover_sub)],
        [Paragraph("OMNIX QUANTUM LTD — United Kingdom", style_cover_sub)],
        [Spacer(1, 0.5 * cm)],
    ]

    tb = Table([[p] for p in [item[0] for item in title_block]], colWidths=[USABLE_W])
    tb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
    ]))
    elements.append(tb)
    elements.append(HRFlowable(width=USABLE_W, thickness=2, color=GOLD, spaceBefore=8))
    elements.append(Spacer(1, 0.8 * cm))

    # Confidentiality notice
    notice_data = [[
        Paragraph(
            "CONFIDENTIAL — SUBMITTED UNDER UK IPO MEDIATION PROCESS\n"
            "This document contains 83 screenshots capturing the complete LinkedIn "
            "message exchange between the parties, organised in 8 chronological sections. "
            "All screenshots are originals from Harold Nunes' LinkedIn account and have "
            "not been altered. Timestamp metadata is preserved in filenames.",
            style_body
        )
    ]]
    notice_table = Table(notice_data, colWidths=[USABLE_W])
    notice_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LGRAY),
        ("BOX", (0, 0), (-1, -1), 1, MGRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    elements.append(notice_table)
    elements.append(PageBreak())
    return elements


def make_toc():
    """Table of contents."""
    elems = [
        Paragraph("TABLE OF CONTENTS", style_heading),
        HRFlowable(width=USABLE_W, thickness=1.5, color=NAVY, spaceAfter=12),
    ]
    for i, sec in enumerate(SECTIONS, 1):
        count = len(sec["images"])
        elems.append(Paragraph(
            f"<b>{sec['label']}</b>  ({count} screenshot{'s' if count > 1 else ''})",
            style_toc_bold
        ))
        elems.append(Spacer(1, 4))
    elems.append(Spacer(1, 0.5 * cm))
    total = sum(len(s["images"]) for s in SECTIONS)
    elems.append(Paragraph(f"<b>Total screenshots: {total}</b>", style_toc_bold))
    elems.append(Spacer(1, 0.8 * cm))

    # Key facts box
    key_facts = [
        [Paragraph("KEY FACTS ESTABLISHED BY THIS EVIDENCE", style_warning)],
        [Paragraph(
            "1. Mushtaque Ahmed Rajput <b>initiated all contact unsolicited</b> on March 13, 2026.\n"
            "2. Harold Nunes <b>never agreed</b> to any integration, partnership, or IP licensing.\n"
            "3. On March 15, Mushtaque <b>voluntarily removed</b> all public OMNIX references and wrote 'I'm glad we're on the same page.'\n"
            "4. On March 24, Mushtaque tried to create an <b>IP confirmation record</b> before Harold's investment pitch. Harold declined.\n"
            "5. On March 25, Mushtaque <b>accepted Harold's position in writing</b>.\n"
            "6. On April 10, Mushtaque <b>escalated to financial demands</b>: retroactive fees, equity, and threats to freeze investment funds.\n"
            "7. Harold referred all matters to <b>legal representatives</b> and warned of defamation/harassment action.\n"
            "8. <b>No signed agreement, licensing contract, or IP transfer</b> exists in any form.",
            style_bullet
        )],
    ]
    kf_table = Table(key_facts, colWidths=[USABLE_W])
    kf_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), RED),
        ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#FFF5F5")),
        ("BOX", (0, 0), (-1, -1), 1.5, RED),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    elems.append(kf_table)
    elems.append(PageBreak())
    return elems


def fit_image(path, max_w, max_h):
    """Return (w, h) fitting inside max_w × max_h preserving aspect ratio."""
    try:
        with PILImage.open(path) as img:
            iw, ih = img.size
        ratio = min(max_w / iw, max_h / ih)
        return iw * ratio, ih * ratio
    except Exception:
        return max_w, max_h * 0.5


def make_section(sec, sec_num):
    """One section: header banner + description + all screenshots."""
    elems = []

    # ── Section header banner ──
    header_data = [[Paragraph(f"{sec_num}. {sec['label']}", style_section_title)]]
    header_table = Table(header_data, colWidths=[USABLE_W])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), sec["colour"]),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [4, 4, 4, 4]),
    ]))
    elems.append(header_table)
    elems.append(Spacer(1, 0.3 * cm))

    # ── Description box ──
    desc_data = [[Paragraph(sec["description"], style_desc)]]
    desc_table = Table(desc_data, colWidths=[USABLE_W])
    desc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LGRAY),
        ("LEFTBORDER", (0, 0), (0, -1), 4, sec["colour"]),
        ("BOX", (0, 0), (-1, -1), 0.5, MGRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    elems.append(desc_table)
    elems.append(Spacer(1, 0.4 * cm))

    # ── Screenshots ──
    MAX_IMG_W = USABLE_W
    MAX_IMG_H = PAGE_H * 0.72

    for idx, fname in enumerate(sec["images"], 1):
        img_path = os.path.join(ASSETS_DIR, fname)
        if not os.path.exists(img_path):
            elems.append(Paragraph(f"[Image not found: {fname}]", style_caption))
            continue

        w, h = fit_image(img_path, MAX_IMG_W, MAX_IMG_H)
        img = RLImage(img_path, width=w, height=h)

        # Wrap in a bordered table cell
        img_data = [[img]]
        img_table = Table(img_data, colWidths=[USABLE_W])
        img_table.setStyle(TableStyle([
            ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
            ("BOX",     (0, 0), (-1, -1), 0.75, MGRAY),
            ("BACKGROUND", (0, 0), (-1, -1), WHITE),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ]))
        elems.append(img_table)
        elems.append(Paragraph(
            f"Screenshot {sec_num}.{idx} — {fname}",
            style_caption
        ))
        elems.append(Spacer(1, 0.3 * cm))

    elems.append(PageBreak())
    return elems


def make_closing():
    """Closing attestation page."""
    elems = [
        Paragraph("ATTESTATION", style_heading),
        HRFlowable(width=USABLE_W, thickness=1.5, color=NAVY, spaceAfter=12),
        Paragraph(
            "I, Harold Alberto Nunes Rodelo, Founder and Director of OMNIX QUANTUM LTD "
            "(Company No. registered in England and Wales), hereby attest that:",
            style_body
        ),
        Spacer(1, 0.3 * cm),
        Paragraph(
            "1. All screenshots contained in this Evidence Annex are authentic and unaltered "
            "captures from my personal LinkedIn account (linkedin.com/in/haroldnunes).",
            style_bullet
        ),
        Paragraph(
            "2. The screenshots represent the complete and unedited record of my LinkedIn "
            "message exchange with Mushtaque Ahmed Rajput between March 13 and April 19, 2026.",
            style_bullet
        ),
        Paragraph(
            "3. No screenshot has been cropped, edited, or manipulated to alter the meaning "
            "of any communication.",
            style_bullet
        ),
        Paragraph(
            "4. The chronological ordering corresponds to the actual sequence of messages "
            "as they appear in my LinkedIn inbox.",
            style_bullet
        ),
        Paragraph(
            "5. This document is submitted in good faith as supporting evidence to the "
            "UK Intellectual Property Office Mediation Service.",
            style_bullet
        ),
        Spacer(1, 1.0 * cm),
    ]

    sig_data = [
        ["Signature:", "_________________________________"],
        ["Name:", "Harold Alberto Nunes Rodelo"],
        ["Title:", "Founder & Director, OMNIX QUANTUM LTD"],
        ["Date:", "April 19, 2026"],
        ["Email:", "contacto@omnixquantum.net"],
        ["Website:", "omnixquantum.net"],
    ]
    sig_table = Table(sig_data, colWidths=[3 * cm, USABLE_W - 3 * cm])
    sig_table.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",  (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, MGRAY),
    ]))
    elems.append(sig_table)
    elems.append(Spacer(1, 1 * cm))

    # Final box
    final_data = [[
        Paragraph(
            "This Evidence Annex is submitted alongside the OMNIX IPO Mediation Submission "
            "(OMNIX_IPO_MEDIATION_SUBMISSION.pdf) and the OMNIX Git Evidence Timeline "
            "(OMNIX_GIT_EVIDENCE_TIMELINE.pdf). Together, these three documents constitute "
            "the complete evidentiary package of OMNIX QUANTUM LTD.",
            style_body
        )
    ]]
    final_table = Table(final_data, colWidths=[USABLE_W])
    final_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TEXTCOLOR",  (0, 0), (-1, -1), WHITE),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [6, 6, 6, 6]),
    ]))
    elems.append(final_table)
    return elems


# ── Main build ─────────────────────────────────────────────────────────────

def build_pdf():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="OMNIX Evidence Annex — LinkedIn Conversation",
        author="Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD",
        subject="UK IPO Mediation — Evidence Annex",
    )

    story = []
    story += make_cover()
    story += make_toc()
    for i, sec in enumerate(SECTIONS, 1):
        story += make_section(sec, i)
    story += make_closing()

    doc.build(story)
    print(f"\n✓ PDF generated: {OUTPUT}")
    total = sum(len(s["images"]) for s in SECTIONS)
    print(f"  Sections : {len(SECTIONS)}")
    print(f"  Screenshots: {total}")


if __name__ == "__main__":
    build_pdf()
