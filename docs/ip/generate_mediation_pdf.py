import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

NAVY = colors.HexColor("#0A1628")
GOLD = colors.HexColor("#C9A84C")
WHITE = colors.white
LIGHT_GRAY = colors.HexColor("#F5F5F5")
MID_GRAY = colors.HexColor("#888888")

_HERE      = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH  = os.path.join(_HERE, "..", "omnix_quantum_logo.png")

OUTPUT = "docs/ip/OMNIX_IPO_MEDIATION_SUBMISSION.pdf"

def build_styles():
    base = getSampleStyleSheet()

    title = ParagraphStyle(
        "OmnixTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=WHITE,
        alignment=TA_CENTER,
        spaceAfter=4,
        leading=28,
    )
    subtitle = ParagraphStyle(
        "OmnixSubtitle",
        fontName="Helvetica",
        fontSize=11,
        textColor=GOLD,
        alignment=TA_CENTER,
        spaceAfter=2,
        leading=16,
    )
    meta = ParagraphStyle(
        "OmnixMeta",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#AAAAAA"),
        alignment=TA_CENTER,
        spaceAfter=0,
        leading=13,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=NAVY,
        spaceBefore=14,
        spaceAfter=6,
        leading=18,
        borderPad=0,
    )
    body = ParagraphStyle(
        "OmnixBody",
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#222222"),
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=16,
    )
    bullet = ParagraphStyle(
        "OmnixBullet",
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#222222"),
        alignment=TA_LEFT,
        spaceAfter=4,
        leading=15,
        leftIndent=16,
        bulletIndent=0,
    )
    code_style = ParagraphStyle(
        "OmnixCode",
        fontName="Courier",
        fontSize=8,
        textColor=colors.HexColor("#1A1A2E"),
        backColor=colors.HexColor("#F0F0F0"),
        alignment=TA_LEFT,
        spaceAfter=4,
        leading=13,
        leftIndent=8,
        rightIndent=8,
    )
    label = ParagraphStyle(
        "OmnixLabel",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=NAVY,
        spaceAfter=2,
        leading=13,
    )
    footer_style = ParagraphStyle(
        "OmnixFooter",
        fontName="Helvetica",
        fontSize=8,
        textColor=MID_GRAY,
        alignment=TA_CENTER,
        leading=12,
    )

    return {
        "title": title,
        "subtitle": subtitle,
        "meta": meta,
        "section_heading": section_heading,
        "body": body,
        "bullet": bullet,
        "code": code_style,
        "label": label,
        "footer": footer_style,
    }


def on_page(canvas, doc, styles):
    W, H = A4
    canvas.saveState()

    canvas.setFillColor(NAVY)
    canvas.rect(0, H - 72*mm, W, 72*mm, fill=1, stroke=0)

    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(2)
    canvas.line(20*mm, H - 72*mm, W - 20*mm, H - 72*mm)

    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica-Bold", 22)
    canvas.drawCentredString(W / 2, H - 28*mm, "OMNIX QUANTUM LTD")

    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica", 11)
    canvas.drawCentredString(W / 2, H - 38*mm, "IP Mediation Submission — Intellectual Property Office (UK)")

    canvas.setFillColor(colors.HexColor("#AAAAAA"))
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(W / 2, H - 48*mm, "Prepared by: Harold Alberto Nunes Rodelo  |  omnixquantum.net  |  April 2026")
    canvas.drawCentredString(W / 2, H - 56*mm, "CONFIDENTIAL — FOR MEDIATION PURPOSES ONLY")

    canvas.setFillColor(colors.HexColor("#EEEEEE"))
    canvas.rect(0, 0, W, 16*mm, fill=1, stroke=0)
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1)
    canvas.line(20*mm, 16*mm, W - 20*mm, 16*mm)
    canvas.setFillColor(MID_GRAY)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(W / 2, 6*mm, f"OMNIX QUANTUM LTD  |  IP Mediation Submission  |  Page {doc.page}")

    canvas.restoreState()


def build_pdf():
    styles = build_styles()
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=22*mm,
        rightMargin=22*mm,
        topMargin=80*mm,
        bottomMargin=22*mm,
        title="OMNIX QUANTUM — IP Mediation Submission",
        author="Harold Alberto Nunes Rodelo",
    )

    story = []
    S = styles

    def heading(text):
        story.append(Paragraph(text, S["section_heading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=6))

    def body(text):
        story.append(Paragraph(text, S["body"]))

    def bullet(text):
        story.append(Paragraph(f"• {text}", S["bullet"]))

    def spacer(h=6):
        story.append(Spacer(1, h))

    def code(text):
        story.append(Paragraph(text, S["code"]))

    # ── SECTION 1: PARTIES ─────────────────────────────────────────────────────
    heading("1. Parties to the Dispute")

    party_data = [
        ["", "Claimant (Submitting Party)", "Opposing Party"],
        ["Name", "Harold Alberto Nunes Rodelo", "Mushtaque Ahmed Rajput"],
        ["Entity", "OMNIX QUANTUM LTD (UK)", "VITT (unregistered label)"],
        ["Website", "omnixquantum.net", "Not publicly available"],
        ["Country", "United Kingdom", "Unspecified"],
        ["Contact", "contacto@omnixquantum.net", "LinkedIn (only channel used)"],
    ]
    party_table = Table(party_data, colWidths=[35*mm, 70*mm, 70*mm])
    party_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#E8E8E8")),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (1, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(party_table)
    spacer(10)

    # ── SECTION 2: NATURE OF DISPUTE ───────────────────────────────────────────
    heading("2. Nature of the Dispute")
    body(
        "The opposing party (Mushtaque Ahmed Rajput, operating under the label 'VITT') has made "
        "public accusations via LinkedIn (April 19, 2026) alleging that OMNIX QUANTUM LTD "
        "incorporated his intellectual property — specifically a methodology he refers to as "
        "'VITT logic' and 'Forensic Invariance' — without authorisation or attribution."
    )
    body(
        "The submitting party categorically disputes these claims. OMNIX is an independently "
        "created decision governance infrastructure, developed from July 2025 onward, with no "
        "technical dependency on any material originating from the opposing party."
    )
    spacer()

    # ── SECTION 3: WHAT IS VITT — TECHNICAL DEFINITION ─────────────────────────
    heading("3. Technical Definition — What is 'VITT'?")
    body(
        "A critical threshold issue in this dispute is the absence of any verifiable technical "
        "definition of 'VITT.' The submitting party has conducted a comprehensive review and "
        "confirms the following:"
    )
    bullet("No public code repository, algorithm, or specification for 'VITT' exists.")
    bullet("No academic paper, patent filing, or registered copyright for 'VITT' has been identified.")
    bullet("No technical documentation describing the architecture, logic, or implementation of 'VITT' has been shared with OMNIX QUANTUM LTD at any point.")
    bullet("The opposing party has not provided any verifiable artefact that constitutes 'VITT' intellectual property.")
    spacer(4)
    body(
        "<b>Formal statement:</b> There exists no definition of 'VITT logic' or 'Forensic Invariance' "
        "in any form — code, algorithm, or document — that was incorporated into OMNIX. "
        "Without a defined, documented, and independently verifiable artefact, no IP ownership "
        "claim can be substantiated."
    )
    spacer()

    # ── SECTION 4: ARCHITECTURAL COMPARISON ────────────────────────────────────
    heading("4. Architectural Comparison — OMNIX vs VITT")
    body(
        "The following table demonstrates the structural and conceptual distinction between "
        "OMNIX and any claimed 'VITT' methodology:"
    )
    spacer(4)

    comp_data = [
        ["Dimension", "OMNIX QUANTUM", "VITT (as claimed)"],
        ["Architecture", "11-checkpoint governance pipeline", "Not publicly defined"],
        ["Core function", "Decision traceability + institutional accountability", "Claimed: forensic invariance"],
        ["Codebase", "Documented in Git since July 13, 2025", "No public repository exists"],
        ["IP registration", "10 provisional patent applications (USPTO) — prepared for filing", "No filing identified"],
        ["Technical artefacts", "Python, TypeScript, PostgreSQL, Flask, React", "None provided or accessible"],
        ["Forensic simulation", "OMNIX Forensic Simulation (commit 08879d68, March 13 2026)", "Not documented independently"],
        ["Origin", "Independent creation by Harold A. Nunes Rodelo", "Unverified claim by opposing party"],
    ]
    comp_table = Table(comp_data, colWidths=[45*mm, 65*mm, 65*mm])
    comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#E8E8E8")),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (1, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("WORDWRAP", (0, 0), (-1, -1), True),
    ]))
    story.append(comp_table)
    spacer(6)
    body(
        "These systems are not the same. OMNIX and VITT do not share architecture, codebase, "
        "methodology, or implementation. They are conceptually distinct, and any claim of overlap "
        "is not supported by any verifiable technical evidence."
    )
    spacer()

    # ── SECTION 5: GIT EVIDENCE TIMELINE ───────────────────────────────────────
    heading("5. Verified Git Evidence Timeline")
    body(
        "All OMNIX source code is maintained in a version-controlled Git repository. "
        "The following commits are independently verifiable using standard cryptographic hashing "
        "(SHA-1). Each hash uniquely identifies a specific state of the codebase at a specific point in time."
    )
    spacer(4)

    git_data = [
        ["Date", "Commit Hash", "Significance"],
        ["13 Jul 2025", "4b9ab293", "OMNIX repository created — first commit. Predates any interaction with opposing party by 8+ months."],
        ["13 Mar 2026", "08879d68", "LUNA/OMNIX Forensic Simulation created exclusively by Harold Nunes Rodelo. File header reads 'OMNIX Forensic Simulation'. Zero VITT references."],
        ["18 Mar 2026", "ceca9500", "VITT label removed from internal notes. First and only appearance of VITT in git — as a deletion."],
        ["10 Apr 2026", "dc927867", "All remaining VITT references removed. VITT never appears in any addition commit — only in removal commits."],
        ["19 Apr 2026", "Current", "Live site omnixquantum.net verified clean of all VITT references (grep confirmed)."],
    ]
    git_table = Table(git_data, colWidths=[28*mm, 28*mm, 119*mm])
    git_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#E8E8E8")),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (1, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("WORDWRAP", (0, 0), (-1, -1), True),
    ]))
    story.append(git_table)
    spacer()

    # ── SECTION 6: SIX PROVEN FACTS ────────────────────────────────────────────
    heading("6. Six Independently Verifiable Facts")
    facts = [
        ("Fact 1 — OMNIX predates VITT by 8+ months",
         "The OMNIX repository was initialised on 13 July 2025 (commit 4b9ab293). The opposing party's accusations were first received on 19 April 2026. No prior formal communication, collaboration agreement, or IP transfer document exists between the parties."),
        ("Fact 2 — VITT was never added, only removed",
         "A complete search of the OMNIX git log reveals that the string 'VITT' appears exclusively in deletion commits (ceca9500 on 18 March 2026; dc927867 on 10 April 2026). VITT was never committed as part of any functional code, architectural document, or specification."),
        ("Fact 3 — Forensic simulation is original OMNIX work",
         "Commit 08879d68 (13 March 2026) created the LUNA forensic simulation. The file header explicitly reads 'OMNIX Forensic Simulation.' Author: madridpep3 (Harold Nunes Rodelo). No VITT attribution, no VITT logic, no VITT reference anywhere in that file."),
        ("Fact 4 — No VITT technical artefact was ever received",
         "The opposing party has not provided — and OMNIX QUANTUM LTD has never received — any code, algorithm, dataset, specification, or documented methodology constituting 'VITT intellectual property.' No IP transfer occurred because no IP was ever shared in technical form."),
        ("Fact 5 — Live site is clean",
         "As of 19 April 2026, omnixquantum.net contains zero references to VITT, Mushtaque Ahmed Rajput, or any claimed methodology. This was independently verified via grep across the full codebase."),
        ("Fact 6 — OMNIX architecture is original, documented, and patent-ready",
         "OMNIX has prepared 10 provisional patent applications for filing with the USPTO (Micro Entity) covering its 11-checkpoint governance pipeline, TIE scoring, forensic simulation framework, and institutional decision infrastructure. These applications are ready for submission and establish prior art entirely independent of any VITT claim."),
    ]
    for title_text, detail_text in facts:
        story.append(Paragraph(f"<b>{title_text}</b>", S["body"]))
        body(detail_text)
        spacer(4)

    # ── SECTION 7: OUTCOME SOUGHT ───────────────────────────────────────────────
    heading("7. Outcome Sought")
    body("The submitting party requests that mediation result in the following:")
    bullet("A formal acknowledgement that OMNIX QUANTUM LTD independently created the OMNIX architecture, codebase, and forensic simulation framework.")
    bullet("A written statement from the opposing party retracting the public IP theft accusations made via LinkedIn on 19 April 2026.")
    bullet("Cessation of all further public or private claims asserting VITT ownership over any component of OMNIX.")
    bullet("Confirmation that no further escalation (investor contact, public statements, regulatory complaints) will be pursued based on these unsubstantiated claims.")
    spacer()

    # ── SECTION 8: CLOSING STATEMENT ───────────────────────────────────────────
    heading("8. Closing Statement")
    body(
        "OMNIX QUANTUM LTD approaches this mediation in good faith and with full transparency. "
        "Every claim made in this submission is supported by independently verifiable, cryptographically "
        "timestamped evidence. No assertion in this document relies on subjective recollection or "
        "undocumented memory."
    )
    body(
        "The opposing party's accusations are not supported by any verifiable technical evidence. "
        "No VITT artefact was received, incorporated, or derived from. The OMNIX architecture is "
        "entirely original, built from first principles, and its development timeline is immutably "
        "recorded in version control."
    )
    spacer(4)

    closing_data = [[
        Paragraph(
            "<b>All evidence presented is independently verifiable. OMNIX architecture is original, "
            "documented, and predates any interaction with the opposing party. "
            "OMNIX QUANTUM LTD is fully prepared to submit the complete Git repository, "
            "file-level diffs, and patent application records to any independent forensic review.</b>",
            ParagraphStyle(
                "ClosingBox",
                fontName="Helvetica",
                fontSize=10,
                textColor=WHITE,
                alignment=TA_JUSTIFY,
                leading=16,
            )
        )
    ]]
    closing_table = Table(closing_data, colWidths=[175*mm])
    closing_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(closing_table)
    spacer(10)

    body(
        "Submitted by: <b>Harold Alberto Nunes Rodelo</b><br/>"
        "OMNIX QUANTUM LTD<br/>"
        "omnixquantum.net<br/>"
        "contacto@omnixquantum.net<br/>"
        "April 2026"
    )

    doc.build(
        story,
        onFirstPage=lambda c, d: on_page(c, d, styles),
        onLaterPages=lambda c, d: on_page(c, d, styles),
    )
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
