from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import PageBreak


OMNIX_DARK = colors.HexColor("#0D0D0D")
OMNIX_ACCENT = colors.HexColor("#00C6FF")
OMNIX_GRAY = colors.HexColor("#555555")
OMNIX_LIGHT = colors.HexColor("#F5F5F5")
WHITE = colors.white


def header_footer(canvas, doc):
    canvas.saveState()
    width, height = letter

    canvas.setFillColor(OMNIX_DARK)
    canvas.rect(0, height - 0.65 * inch, width, 0.65 * inch, fill=1, stroke=0)

    canvas.setFillColor(OMNIX_ACCENT)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(0.5 * inch, height - 0.42 * inch, "OMNIX QUANTUM")
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 0.5 * inch, height - 0.42 * inch, "Decision Governance Infrastructure")

    canvas.setFillColor(OMNIX_DARK)
    canvas.rect(0, 0, width, 0.45 * inch, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(0.5 * inch, 0.17 * inch, "OMNIX Quantum · Confidential · omnibotgenesis.up.railway.app")
    canvas.drawRightString(width - 0.5 * inch, 0.17 * inch, f"Page {doc.page}")

    canvas.restoreState()


def build_contract():
    path = "omnix_contracts/OMNIX_Governance_Services_Agreement.pdf"
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=1.1 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", parent=styles["Normal"],
        fontSize=18, fontName="Helvetica-Bold",
        textColor=OMNIX_DARK, alignment=TA_CENTER,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica",
        textColor=OMNIX_GRAY, alignment=TA_CENTER,
        spaceAfter=2
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Normal"],
        fontSize=9.5, fontName="Helvetica-Bold",
        textColor=OMNIX_DARK, spaceBefore=14, spaceAfter=4
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica",
        textColor=OMNIX_DARK, leading=14,
        alignment=TA_JUSTIFY, spaceAfter=6
    )
    field_label = ParagraphStyle(
        "FieldLabel", parent=styles["Normal"],
        fontSize=8.5, fontName="Helvetica-Bold",
        textColor=OMNIX_GRAY, spaceBefore=6
    )

    story = []

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("OMNIX GOVERNANCE SERVICES AGREEMENT", title_style))
    story.append(Paragraph("Standard Client Agreement · Confidential", subtitle_style))
    story.append(Spacer(1, 0.08 * inch))
    story.append(HRFlowable(width="100%", thickness=1.5, color=OMNIX_ACCENT))
    story.append(Spacer(1, 0.15 * inch))

    parties_data = [
        ["Provider:", "OMNIX Quantum (operated by Harold Nunes)"],
        ["Client:", "[Client Legal Name]"],
        ["Effective Date:", "[DATE]"],
    ]
    parties_table = Table(parties_data, colWidths=[1.3 * inch, 5.5 * inch])
    parties_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), OMNIX_GRAY),
        ("TEXTCOLOR", (1, 0), (1, -1), OMNIX_DARK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 0.1 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD")))

    sections = [
        ("1. SERVICES",
         'OMNIX Quantum provides a decision governance evaluation layer (the "Service"). The Service evaluates signals submitted by the Client through a multi-checkpoint pipeline and returns a cryptographically signed governance receipt for each evaluation. OMNIX does not approve, authorize, or validate decisions. It provides a governance evaluation only. OMNIX does not execute decisions, transactions, or actions on behalf of the Client.'),

        ("2. NO WARRANTY",
         'The Service is provided "as is" and "as available," without warranties of any kind, express or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, or uninterrupted availability.'),

        ("3. NO ADVISORY — CLIENT RESPONSIBILITY",
         "The Service does not constitute financial, legal, operational, or investment advice. All decisions executed by the Client remain the sole responsibility of the Client. OMNIX evaluates signals — it does not direct, recommend, or authorize any action."),

        ("4. DATA RESPONSIBILITY",
         "The Client is solely responsible for the data submitted to the Service and confirms it has the legal right to use such data. OMNIX shall not be liable for any issues arising from the content, accuracy, or legality of data provided by the Client."),

        ("5. LIMITATION OF LIABILITY",
         "OMNIX shall not be liable for any losses, damages, missed opportunities, or claims arising from decisions made or actions taken by the Client, whether or not those decisions were evaluated through the Service. In no event shall OMNIX's total liability exceed the fees paid by the Client in the three (3) months preceding the claim."),

        ("6. INDEPENDENCE FROM THIRD PARTIES",
         "OMNIX is an independent system and is not responsible for the actions, outputs, or failures of any third party, including channel partners or intermediaries through which the Client accessed the Service."),

        ("7. SERVICE AVAILABILITY",
         "OMNIX operates on a best-effort basis. Enterprise plans include a 99.9% uptime SLA. Advisory plans do not carry an uptime guarantee. OMNIX shall not be liable for damages resulting from service interruptions."),

        ("8. FORCE MAJEURE",
         "OMNIX shall not be liable for delays or failures in performance caused by events beyond its reasonable control, including but not limited to natural disasters, cyberattacks, infrastructure failures, or regulatory actions."),

        ("9. INTELLECTUAL PROPERTY",
         "All technology, algorithms, methodologies, and systems comprising OMNIX remain the exclusive property of the Provider. The Client receives a limited, non-transferable, non-sublicensable right to access the Service during the term of this Agreement. The Client shall not reverse-engineer, replicate, or disclose OMNIX's evaluation methodology."),

        ("10. CONFIDENTIALITY",
         "Both parties agree to keep the terms of this Agreement and any proprietary information exchanged strictly confidential for the duration of this Agreement and for two (2) years thereafter."),

        ("11. PAYMENT",
         "Fees are as agreed in the applicable Order Form. Overages are billed at the rate specified per plan. Invoices are due within 15 days of issuance. Failure to pay within the due date may result in immediate suspension of the Service."),

        ("12. TERM AND TERMINATION",
         "This Agreement begins on the Effective Date. Advisory plans may be cancelled with 30 days written notice. Enterprise plans are subject to the annual contract term specified in the Order Form. OMNIX may suspend or terminate access immediately for non-payment or material breach."),

        ("13. GOVERNING LAW",
         "This Agreement is governed by the laws of the Emirate of Dubai, United Arab Emirates. Any disputes shall be resolved by binding arbitration under the rules of the Dubai International Arbitration Centre (DIAC)."),
    ]

    for title, body in sections:
        story.append(Paragraph(title, section_style))
        story.append(Paragraph(body, body_style))

    story.append(Spacer(1, 0.2 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=OMNIX_ACCENT))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("SIGNATURES", section_style))

    sig_data = [
        ["OMNIX Quantum", "", "Client"],
        ["", "", ""],
        ["_" * 38, "", "_" * 38],
        ["Harold Nunes · Provider", "", "[Client Name · Title]"],
        ["Date: ___________________", "", "Date: ___________________"],
    ]
    sig_table = Table(sig_data, colWidths=[3 * inch, 0.8 * inch, 3 * inch])
    sig_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), OMNIX_DARK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Contract created: {path}")


def build_order_form():
    path = "omnix_contracts/OMNIX_Order_Form.pdf"
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=1.1 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", parent=styles["Normal"],
        fontSize=18, fontName="Helvetica-Bold",
        textColor=OMNIX_DARK, alignment=TA_CENTER, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica",
        textColor=OMNIX_GRAY, alignment=TA_CENTER, spaceAfter=2
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Normal"],
        fontSize=9.5, fontName="Helvetica-Bold",
        textColor=WHITE, spaceBefore=0, spaceAfter=0,
        leftIndent=6
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica",
        textColor=OMNIX_DARK, leading=14, spaceAfter=4
    )
    note_style = ParagraphStyle(
        "Note", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica-Oblique",
        textColor=OMNIX_GRAY, leading=12, spaceAfter=4
    )

    story = []

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("OMNIX ORDER FORM", title_style))
    story.append(Paragraph("Attachment to the OMNIX Governance Services Agreement · Confidential", subtitle_style))
    story.append(Spacer(1, 0.08 * inch))
    story.append(HRFlowable(width="100%", thickness=1.5, color=OMNIX_ACCENT))
    story.append(Spacer(1, 0.2 * inch))

    def section_header(text):
        header_table = Table([[Paragraph(text, section_style)]], colWidths=[6.85 * inch])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), OMNIX_DARK),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return header_table

    def field_row(label, value=""):
        line = "_" * 55 if not value else value
        return Table(
            [[f"{label}:", line]],
            colWidths=[1.8 * inch, 5.05 * inch]
        )

    def build_field_table(rows):
        data = []
        for label, _ in rows:
            data.append([label + ":", "_" * 52])
        t = Table(data, colWidths=[1.9 * inch, 4.95 * inch])
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), OMNIX_GRAY),
            ("TEXTCOLOR", (1, 0), (1, -1), OMNIX_DARK),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (1, 0), (1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ]))
        return t

    story.append(section_header("A. PARTIES"))
    story.append(Spacer(1, 0.08 * inch))
    story.append(build_field_table([
        ("Provider", ""),
        ("Client Legal Name", ""),
        ("Client Contact Name", ""),
        ("Client Email", ""),
        ("Client Address", ""),
    ]))
    story.append(Spacer(1, 0.18 * inch))

    story.append(section_header("B. PLAN & PRICING"))
    story.append(Spacer(1, 0.08 * inch))

    plan_data = [
        ["Plan Selected", "☐  Advisory     ☐  Enterprise Base     ☐  Enterprise Full     ☐  Custom"],
        ["Evaluations Included", ""],
        ["Overage Rate (per eval)", ""],
        ["Monthly / Annual Fee", ""],
        ["Payment Currency", "☐  USD     ☐  AED     ☐  Other: ___________"],
        ["Billing Cycle", "☐  Monthly     ☐  Annual (12 months)"],
        ["Payment Method", "☐  Wire Transfer     ☐  Stripe     ☐  Invoice"],
    ]
    t = Table(plan_data, colWidths=[2.1 * inch, 4.75 * inch])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), OMNIX_GRAY),
        ("TEXTCOLOR", (1, 0), (1, -1), OMNIX_DARK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (1, 0), (1, -1), 0.5, colors.HexColor("#CCCCCC")),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.18 * inch))

    story.append(section_header("C. TERM"))
    story.append(Spacer(1, 0.08 * inch))
    story.append(build_field_table([
        ("Start Date", ""),
        ("End Date / Renewal", ""),
        ("Notice Period for Cancellation", ""),
    ]))
    story.append(Spacer(1, 0.18 * inch))

    story.append(section_header("D. SPECIAL CONDITIONS"))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph(
        "Use this section to document any agreed pilot terms, custom SLA, referral credits, or negotiated discounts.",
        note_style
    ))
    lines = [["_" * 90]] * 5
    special_table = Table(lines, colWidths=[6.85 * inch])
    special_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (0, -1), 0.5, colors.HexColor("#CCCCCC")),
    ]))
    story.append(special_table)
    story.append(Spacer(1, 0.18 * inch))

    story.append(section_header("E. CHANNEL PARTNER (if applicable)"))
    story.append(Spacer(1, 0.08 * inch))
    story.append(build_field_table([
        ("Partner Name", ""),
        ("Partner Entity", ""),
        ("Referral Commission %", ""),
    ]))
    story.append(Spacer(1, 0.25 * inch))

    story.append(HRFlowable(width="100%", thickness=1, color=OMNIX_ACCENT))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("This Order Form is incorporated into and governed by the OMNIX Governance Services Agreement signed by both parties. In the event of any conflict, the Agreement shall prevail.", note_style))
    story.append(Spacer(1, 0.2 * inch))

    sig_data = [
        ["OMNIX Quantum", "", "Client"],
        ["", "", ""],
        ["_" * 38, "", "_" * 38],
        ["Harold Nunes · Provider", "", "[Client Name · Title]"],
        ["Date: ___________________", "", "Date: ___________________"],
    ]
    sig_table = Table(sig_data, colWidths=[3 * inch, 0.8 * inch, 3 * inch])
    sig_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), OMNIX_DARK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Order Form created: {path}")


if __name__ == "__main__":
    build_contract()
    build_order_form()
    print("Both documents generated successfully.")
