import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas


DARK_BG = HexColor('#0a0f1a')
GREEN_ACCENT = HexColor('#10b981')
LIGHT_GRAY = HexColor('#6b7280')
MEDIUM_GRAY = HexColor('#374151')
LINK_BLUE = HexColor('#3b82f6')
BODY_COLOR = HexColor('#1f2937')


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.setFont("Helvetica", 8)
            self.setFillColor(LIGHT_GRAY)
            self.drawCentredString(letter[0] / 2, 0.4 * inch,
                                   f"OMNIX Decision Governance Infrastructure — Confidential — Page {self._pageNumber} of {num_pages}")
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def build_pdf():
    output_path = "OMNIX_Validation_Andres_Yie.pdf"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.7 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('OmnixTitle', parent=styles['Title'],
        fontName='Helvetica-Bold', fontSize=22, textColor=DARK_BG, spaceAfter=4, alignment=TA_LEFT)

    subtitle_style = ParagraphStyle('OmnixSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=11, textColor=LIGHT_GRAY, spaceAfter=16, alignment=TA_LEFT)

    heading_style = ParagraphStyle('OmnixHeading', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=14, textColor=DARK_BG, spaceBefore=20, spaceAfter=8)

    subheading_style = ParagraphStyle('OmnixSubheading', parent=styles['Heading3'],
        fontName='Helvetica-Bold', fontSize=11, textColor=BODY_COLOR, spaceBefore=12, spaceAfter=6)

    body_style = ParagraphStyle('OmnixBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, textColor=BODY_COLOR, leading=15, spaceAfter=8, alignment=TA_JUSTIFY)

    bullet_style = ParagraphStyle('OmnixBullet', parent=body_style,
        leftIndent=20, spaceAfter=4, bulletIndent=8)

    question_style = ParagraphStyle('OmnixQuestion', parent=body_style,
        leftIndent=24, spaceAfter=10, spaceBefore=2)

    link_style = ParagraphStyle('OmnixLink', parent=body_style,
        textColor=LINK_BLUE, spaceAfter=6, leftIndent=20)

    small_style = ParagraphStyle('OmnixSmall', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, textColor=LIGHT_GRAY, leading=11, spaceAfter=4, alignment=TA_CENTER)

    greeting_style = ParagraphStyle('OmnixGreeting', parent=body_style,
        fontSize=10.5, leading=16, spaceAfter=10)

    elements = []

    logo_path = "attached_assets/image_1771886763766.png"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=50, height=50)
        logo_text = Paragraph(
            '<font size="18" color="#0a0f1a"><b>OMNIX</b></font>'
            '<font size="10" color="#6b7280">  Decision Governance Infrastructure</font>',
            ParagraphStyle('LogoText', parent=styles['Normal'], alignment=TA_LEFT)
        )
        logo_table = Table([[logo, logo_text]], colWidths=[50, 400])
        logo_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('LEFTPADDING', (1, 0), (1, 0), 8),
        ]))
        elements.append(logo_table)
        elements.append(Spacer(1, 6))

    elements.append(HRFlowable(width="100%", thickness=2, color=GREEN_ACCENT, spaceBefore=2, spaceAfter=16))

    elements.append(Paragraph("Validation Questions", title_style))
    elements.append(Paragraph("Eureka Dubai GCC 2026 — Semifinalist Program Requirement", subtitle_style))

    recipient_data = [
        ['Prepared for:', 'Andr\u00e9s Yie'],
        ['Role:', 'CIO | Digital Transformation & Data Analytics'],
        ['Organization:', 'GHL Hoteles'],
        ['Location:', 'Bogot\u00e1, D.C., Colombia'],
        ['Date:', 'February 2026'],
    ]
    recipient_table = Table(recipient_data, colWidths=[100, 350])
    recipient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), LIGHT_GRAY),
        ('TEXTCOLOR', (1, 0), (1, -1), BODY_COLOR),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(recipient_table)
    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=MEDIUM_GRAY, spaceBefore=4, spaceAfter=16))

    elements.append(Paragraph("Dear Andr\u00e9s,", greeting_style))
    elements.append(Paragraph(
        "Thank you very much for your willingness to collaborate. I truly appreciate it.",
        greeting_style
    ))
    elements.append(Paragraph(
        "I am currently a semifinalist in the <b>Eureka Dubai GCC 2026</b> program, and one of the requirements "
        "is to validate the problem and the proposed solution with industry professionals. Since we are still "
        "in an early stage and do not have active customers, the program requires honest feedback from leaders "
        "with real experience in operations and technology.",
        body_style
    ))
    elements.append(Paragraph(
        "To give you clear context before the questions:",
        body_style
    ))

    elements.append(Paragraph("What is OMNIX?", heading_style))

    elements.append(Paragraph(
        "OMNIX is a <b>validation and governance infrastructure for automated decisions</b>.",
        body_style
    ))
    elements.append(Paragraph(
        "It is not another AI model. It is a control layer that sits <b>before</b> an automated decision is executed.",
        body_style
    ))

    elements.append(Paragraph("Its function is to:", subheading_style))
    for f in [
        "Validate rules before execution",
        "Block actions that do not meet defined criteria",
        "Record in a structured way what happened",
        "Allow precise reconstruction of decisions for future audits",
    ]:
        elements.append(Paragraph(f"\u2022 {f}", bullet_style))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "The approach is especially designed for environments where an automated decision can generate:",
        subheading_style
    ))
    for r in [
        "Operational risk",
        "Legal exposure",
        "Financial impact",
        "Compliance issues",
    ]:
        elements.append(Paragraph(f"\u2013 {r}", bullet_style))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "The core idea is to <b>reduce the risk associated with the growing automation in critical systems</b>.",
        body_style
    ))

    elements.append(Paragraph("Validation Questions", heading_style))
    elements.append(Paragraph(
        "Below are some questions that will help us validate whether this problem is real "
        "from a technology leadership perspective:",
        body_style
    ))

    questions = [
        "From your experience as CIO, do you consider that automation and AI are increasing "
        "exposure to operational or compliance risk in organizations?",

        "When an automated system makes a critical decision, how easy is it to precisely "
        "reconstruct what happened and why it happened months or years later?",

        "Have you seen cases where the lack of traceability in automated decisions has led to "
        "complex audits, internal problems, or reputational impact?",

        "Do you believe most organizations today design their systems with potential future "
        "legal disputes in mind?",

        "Would you consider it valuable to have an infrastructure that validates decisions "
        "before they are executed and leaves a structured, verifiable record?",

        "In which industries or areas do you see the greatest urgency for this type of solution?",

        "Do you believe regulated companies would be willing to allocate budget to reduce "
        "legal and operational risk associated with automated decisions?",

        "What would be the first thing you would evaluate before adopting a solution like this?",
    ]
    for i, q in enumerate(questions, 1):
        elements.append(Paragraph(f"<b>{i}.</b>  {q}", question_style))

    elements.append(Paragraph("OMNIX in Action — Interactive Demos", heading_style))
    elements.append(Paragraph(
        "So you can see how the 6-checkpoint governance engine works across different "
        "industries, here are our interactive demos:",
        body_style
    ))

    demos = [
        ("Credit / Lending Governance",
         "Credit risk evaluation with 6 independent checkpoints",
         "https://www.omnixquantum.net/governance-demo"),
        ("Insurance Governance",
         "Policy and claims evaluation with multi-layer validation",
         "https://www.omnixquantum.net/governance-demo-insurance"),
        ("Energy Trading Governance",
         "Energy trading decision evaluation (natural gas, crude oil, solar, wind, LNG, electricity)",
         "https://www.omnixquantum.net/governance-demo-energy"),
    ]
    for title, desc, url in demos:
        elements.append(Paragraph(f"<b>{title}</b>", subheading_style))
        elements.append(Paragraph(desc, body_style))
        elements.append(Paragraph(
            f'<a href="{url}" color="#3b82f6">{url}</a>', link_style
        ))

    elements.append(Paragraph("Public Governance Receipt Verification", heading_style))
    elements.append(Paragraph(
        "Every decision governed by OMNIX generates a cryptographically signed receipt using "
        "<b>Dilithium-3</b> (post-quantum cryptography, NIST-standardized algorithms). "
        "These receipts are publicly verifiable:",
        body_style
    ))
    elements.append(Paragraph(
        '<a href="https://omnibotgenesis-production.up.railway.app/verify" color="#3b82f6">'
        'https://omnibotgenesis-production.up.railway.app/verify</a>',
        link_style
    ))
    elements.append(Paragraph("Governance Metrics (Public API):", subheading_style))
    elements.append(Paragraph(
        '<a href="https://omnibotgenesis-production.up.railway.app/api/governance/metrics" color="#3b82f6">'
        'https://omnibotgenesis-production.up.railway.app/api/governance/metrics</a>',
        link_style
    ))

    elements.append(Paragraph("Institutional Website", heading_style))
    elements.append(Paragraph(
        '<a href="https://www.omnixquantum.net" color="#3b82f6">https://www.omnixquantum.net</a>',
        link_style
    ))

    elements.append(Paragraph("Telegram Bot — OMNIX Decision Governance", heading_style))
    elements.append(Paragraph(
        "You can interact directly with the governance system through our Telegram bot, "
        "where you will be able to see real-time analysis and how the 6-checkpoint engine "
        "evaluates each decision:",
        body_style
    ))
    elements.append(Paragraph(
        '<a href="https://t.me/omnixglobal2025_bot" color="#3b82f6">https://t.me/omnixglobal2025_bot</a>',
        link_style
    ))

    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=MEDIUM_GRAY, spaceBefore=8, spaceAfter=12))

    elements.append(Paragraph(
        "Thank you very much for your time and your honesty.<br/>"
        "Your responses are key to completing the program's validation process.",
        body_style
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Best regards,", body_style))
    elements.append(Paragraph("<b>Harold Nunes</b>", body_style))
    elements.append(Paragraph("Founder &amp; CEO — OMNIX", body_style))
    elements.append(Paragraph("Eureka Dubai GCC 2026 — Semifinalist", subtitle_style))

    # ===== RESPONSE FORM SECTION =====
    from reportlab.platypus import PageBreak
    elements.append(PageBreak())

    elements.append(Paragraph("Response Form", title_style))
    elements.append(Paragraph(
        "Eureka Dubai GCC 2026 — Validation Interview Record",
        subtitle_style
    ))
    elements.append(Paragraph(
        "Please complete the following sections. Your contact details are required by the "
        "Eureka program to verify that this validation was conducted with a real industry professional. "
        "Your information will only be used for program verification purposes.",
        body_style
    ))

    elements.append(Paragraph("Respondent Information", heading_style))

    field_label_style = ParagraphStyle('FieldLabel', parent=body_style,
        fontName='Helvetica-Bold', fontSize=10, spaceAfter=2)
    field_line_style = ParagraphStyle('FieldLine', parent=body_style,
        fontName='Helvetica', fontSize=10, textColor=LIGHT_GRAY, spaceAfter=14)

    contact_fields = [
        ("Full Name:", "________________________________________________________"),
        ("Role / Title:", "________________________________________________________"),
        ("Organization:", "________________________________________________________"),
        ("Email:", "________________________________________________________"),
        ("Phone:", "________________________________________________________"),
        ("LinkedIn (optional):", "________________________________________________________"),
    ]
    for label, line in contact_fields:
        elements.append(Paragraph(f"<b>{label}</b>  {line}", body_style))

    elements.append(Paragraph("Responses", heading_style))
    elements.append(Paragraph(
        "Please provide your honest answers to each question. You may respond as briefly "
        "or as extensively as you wish.",
        body_style
    ))

    for i, q in enumerate(questions, 1):
        elements.append(Paragraph(f"<b>Question {i}:</b> {q}", subheading_style))
        elements.append(Paragraph("Your response:", field_label_style))
        for _ in range(4):
            elements.append(Paragraph("___________________________________________________________________________", field_line_style))
        elements.append(Spacer(1, 6))

    elements.append(PageBreak())
    elements.append(Paragraph("Key Feedback Summary", heading_style))
    elements.append(Paragraph(
        "This section helps us consolidate your most important insights for the Eureka evaluation panel.",
        body_style
    ))

    feedback_sections = [
        ("Pain Point",
         "What is the biggest challenge or risk you see with automated decision-making in your industry today?"),
        ("Perceived Value",
         "How valuable would a governance infrastructure like OMNIX be for your organization or industry? "
         "What specific problems would it solve?"),
        ("Pricing Sensitivity",
         "Would your organization (or similar organizations) be willing to invest in a solution that reduces "
         "operational and legal risk from automated decisions? What factors would influence that decision?"),
    ]
    for title, prompt in feedback_sections:
        elements.append(Paragraph(f"<b>{title}</b>", subheading_style))
        elements.append(Paragraph(prompt, body_style))
        elements.append(Paragraph("Your response:", field_label_style))
        for _ in range(5):
            elements.append(Paragraph("___________________________________________________________________________", field_line_style))
        elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=MEDIUM_GRAY, spaceBefore=8, spaceAfter=12))

    elements.append(Paragraph(
        "<b>Authorization:</b> By completing this form, I confirm that the responses above reflect "
        "my honest professional opinion and I authorize their use for the Eureka Dubai GCC 2026 "
        "program validation process.",
        body_style
    ))

    elements.append(Spacer(1, 20))
    sig_fields = [
        ("Signature:", "________________________________________"),
        ("Date:", "________________________________________"),
    ]
    for label, line in sig_fields:
        elements.append(Paragraph(f"<b>{label}</b>  {line}", body_style))

    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        "OMNIX Decision Governance Infrastructure — Abu Dhabi, UAE<br/>"
        "Internal dataset, not externally audited. Evaluation cycles represent governance engine processing.",
        small_style
    ))

    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"PDF generated: {output_path}")
    print(f"File size: {os.path.getsize(output_path):,} bytes")
    return output_path


if __name__ == "__main__":
    build_pdf()
