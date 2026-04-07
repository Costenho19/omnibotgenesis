from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas as pdfcanvas
import os

OMNIX_DARK   = colors.HexColor("#0A0A0F")
OMNIX_ACCENT = colors.HexColor("#00C6FF")
OMNIX_GRAY   = colors.HexColor("#666666")
OMNIX_FIELD  = colors.HexColor("#F0F4FF")
OMNIX_BORDER = colors.HexColor("#C0CCE0")
WHITE        = colors.white

LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "omnix_web", "public", "omnix_logo.png"
)

W, H = letter


def draw_header(c, page_num, doc_name):
    c.setFillColor(OMNIX_DARK)
    c.rect(0, H - 0.75 * inch, W, 0.75 * inch, fill=1, stroke=0)
    c.setFillColor(OMNIX_ACCENT)
    c.rect(0, H - 0.75 * inch, W, 0.03 * inch, fill=1, stroke=0)

    logo_h = 0.44 * inch
    logo_w = logo_h * (569 / 379)
    logo_y = H - 0.75 * inch + (0.75 * inch - logo_h) / 2
    if os.path.exists(LOGO_PATH):
        c.drawImage(LOGO_PATH, 0.45 * inch, logo_y,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, mask="auto")

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica", 7.5)
    c.drawRightString(W - 0.45 * inch, H - 0.75 * inch + 0.30 * inch,
                      "Decision Governance Infrastructure")
    c.setFillColor(colors.HexColor("#444455"))
    c.setFont("Helvetica", 7)
    c.drawRightString(W - 0.45 * inch, H - 0.75 * inch + 0.16 * inch,
                      "Confidential · omnibotgenesis.up.railway.app")


def draw_footer(c, page_num, doc_name):
    c.setFillColor(OMNIX_DARK)
    c.rect(0, 0, W, 0.42 * inch, fill=1, stroke=0)
    c.setFillColor(OMNIX_ACCENT)
    c.rect(0, 0.39 * inch, W, 0.03 * inch, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#555566"))
    c.setFont("Helvetica", 7.5)
    c.drawString(0.45 * inch, 0.15 * inch,
                 f"OMNIX Quantum · {doc_name} · England & Wales")
    c.drawRightString(W - 0.45 * inch, 0.15 * inch, f"Page {page_num}")


def text_field(c, name, x, y, width, height=0.22 * inch, tooltip=""):
    c.acroForm.textfield(
        name=name,
        tooltip=tooltip,
        x=x, y=y,
        width=width, height=height,
        fontSize=9,
        textColor=OMNIX_DARK,
        fillColor=OMNIX_FIELD,
        borderColor=OMNIX_BORDER,
        borderWidth=0.5,
        fieldFlags="",
    )


def checkbox(c, name, x, y, size=10, tooltip=""):
    c.acroForm.checkbox(
        name=name,
        tooltip=tooltip,
        x=x, y=y,
        size=size,
        fillColor=OMNIX_FIELD,
        borderColor=OMNIX_BORDER,
        borderWidth=0.5,
        buttonStyle="check",
        forceBorder=True,
    )


def section_bar(c, y, label, x=0.45 * inch, bar_w=None):
    bw = bar_w or (W - 0.9 * inch)
    c.setFillColor(OMNIX_DARK)
    c.rect(x, y, bw, 0.22 * inch, fill=1, stroke=0)
    c.setFillColor(OMNIX_ACCENT)
    c.rect(x, y, 0.04 * inch, 0.22 * inch, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x + 0.12 * inch, y + 0.07 * inch, label)
    return y - 0.06 * inch


def field_row(c, label, field_name, x_label, x_field, y,
              field_w=3.6 * inch, fh=0.21 * inch, tooltip=""):
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x_label, y + 0.04 * inch, label)
    text_field(c, field_name, x_field, y, field_w, fh, tooltip=tooltip)
    return y - (fh + 0.1 * inch)


def build_contract():
    path = "omnix_contracts/OMNIX_Governance_Services_Agreement.pdf"
    c = pdfcanvas.Canvas(path, pagesize=letter)
    c.setTitle("OMNIX Governance Services Agreement")
    c.setAuthor("OMNIX Quantum")
    c.setSubject("Standard Client Agreement")

    draw_header(c, 1, "Governance Services Agreement")
    draw_footer(c, 1, "Standard Client Agreement")

    margin = 0.55 * inch
    text_w = W - 2 * margin
    y = H - 1.0 * inch

    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W / 2, y, "OMNIX GOVERNANCE SERVICES AGREEMENT")
    y -= 0.22 * inch
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, y, "Standard Client Agreement  ·  Confidential")
    y -= 0.12 * inch

    c.setStrokeColor(OMNIX_ACCENT)
    c.setLineWidth(1.5)
    c.line(margin, y, W - margin, y)
    y -= 0.20 * inch

    parties = [
        ("Provider:", "OMNIX Quantum (operated by Harold Nunes)", None),
        ("Client:", None, "client_name"),
        ("Effective Date:", None, "effective_date"),
    ]
    for label, static_val, field_name in parties:
        c.setFillColor(OMNIX_GRAY)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(margin, y + 0.04 * inch, label)
        if static_val:
            c.setFillColor(OMNIX_DARK)
            c.setFont("Helvetica", 8.5)
            c.drawString(margin + 1.1 * inch, y + 0.04 * inch, static_val)
        else:
            text_field(c, field_name, margin + 1.1 * inch, y,
                       text_w - 1.1 * inch, 0.21 * inch)
        y -= 0.30 * inch

    y -= 0.05 * inch
    c.setStrokeColor(colors.HexColor("#DDDDDD"))
    c.setLineWidth(0.5)
    c.line(margin, y, W - margin, y)
    y -= 0.16 * inch

    sections = [
        ("1. SERVICES",
         'OMNIX Quantum provides a decision governance evaluation layer (the "Service"). The Service evaluates '
         'signals submitted by the Client through a multi-checkpoint pipeline and returns a cryptographically '
         'signed governance receipt for each evaluation. OMNIX does not approve, authorize, or validate '
         'decisions. It provides a governance evaluation only. OMNIX does not execute decisions, transactions, '
         'or actions on behalf of the Client.'),
        ("2. NO WARRANTY",
         'The Service is provided "as is" and "as available," without warranties of any kind, express or '
         'implied, including but not limited to warranties of merchantability, fitness for a particular '
         'purpose, or uninterrupted availability.'),
        ("3. NO ADVISORY — CLIENT RESPONSIBILITY",
         'The Service does not constitute financial, legal, operational, or investment advice. All decisions '
         'executed by the Client remain the sole responsibility of the Client. OMNIX evaluates signals — '
         'it does not direct, recommend, or authorize any action.'),
        ("4. DATA RESPONSIBILITY",
         'The Client is solely responsible for the data submitted to the Service and confirms it has the '
         'legal right to use such data. OMNIX shall not be liable for any issues arising from the content, '
         'accuracy, or legality of data provided by the Client.'),
        ("5. LIMITATION OF LIABILITY",
         'OMNIX shall not be liable for any losses, damages, missed opportunities, or claims arising from '
         'decisions made or actions taken by the Client, whether or not those decisions were evaluated '
         'through the Service. In no event shall OMNIX\'s total liability exceed the fees paid by the '
         'Client in the three (3) months preceding the claim.'),
        ("6. INDEPENDENCE FROM THIRD PARTIES",
         'OMNIX is an independent system and is not responsible for the actions, outputs, or failures of '
         'any third party, including channel partners or intermediaries through which the Client accessed '
         'the Service.'),
        ("7. SERVICE AVAILABILITY",
         'OMNIX operates on a best-effort basis. Enterprise plans include a 99.9% uptime SLA. Advisory '
         'plans do not carry an uptime guarantee. OMNIX shall not be liable for damages resulting from '
         'service interruptions.'),
        ("8. FORCE MAJEURE",
         'OMNIX shall not be liable for delays or failures in performance caused by events beyond its '
         'reasonable control, including but not limited to natural disasters, cyberattacks, infrastructure '
         'failures, or regulatory actions.'),
        ("9. INTELLECTUAL PROPERTY",
         'All technology, algorithms, methodologies, and systems comprising OMNIX remain the exclusive '
         'property of the Provider. The Client receives a limited, non-transferable, non-sublicensable '
         'right to access the Service during the term of this Agreement. The Client shall not '
         'reverse-engineer, replicate, or disclose OMNIX\'s evaluation methodology.'),
        ("10. CONFIDENTIALITY",
         'Both parties agree to keep the terms of this Agreement and any proprietary information exchanged '
         'strictly confidential for the duration of this Agreement and for two (2) years thereafter.'),
        ("11. PAYMENT",
         'Fees are as agreed in the applicable Order Form. Overages are billed at the rate specified per '
         'plan. Invoices are due within 15 days of issuance. Failure to pay within the due date may result '
         'in immediate suspension of the Service.'),
        ("12. TERM AND TERMINATION",
         'This Agreement begins on the Effective Date. Advisory plans may be cancelled with 30 days written '
         'notice. Enterprise plans are subject to the annual contract term specified in the Order Form. '
         'OMNIX may suspend or terminate access immediately for non-payment or material breach.'),
        ("13. GOVERNING LAW",
         'This Agreement is governed by the laws of England and Wales. Any disputes shall be resolved by '
         'binding arbitration under the rules of the London Court of International Arbitration (LCIA).'),
    ]

    def wrap_text(text, font, size, max_width, canvas_obj):
        words = text.split()
        lines = []
        current = ""
        canvas_obj.setFont(font, size)
        for word in words:
            test = (current + " " + word).strip()
            if canvas_obj.stringWidth(test, font, size) <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    for title, body in sections:
        section_height = 0.22 * inch
        body_lines = wrap_text(body, "Helvetica", 8.5, text_w - 0.1 * inch, c)
        needed = section_height + 0.12 * inch + len(body_lines) * 0.145 * inch + 0.15 * inch

        if y - needed < 0.6 * inch:
            c.showPage()
            draw_header(c, c.getPageNumber(), "Governance Services Agreement")
            draw_footer(c, c.getPageNumber(), "Standard Client Agreement")
            y = H - 1.0 * inch

        y = section_bar(c, y, title) - 0.1 * inch
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica", 8.5)
        for line in body_lines:
            c.drawString(margin + 0.05 * inch, y, line)
            y -= 0.145 * inch
        y -= 0.08 * inch

    if y - 1.6 * inch < 0.6 * inch:
        c.showPage()
        draw_header(c, c.getPageNumber(), "Governance Services Agreement")
        draw_footer(c, c.getPageNumber(), "Standard Client Agreement")
        y = H - 1.0 * inch

    y -= 0.1 * inch
    c.setStrokeColor(OMNIX_ACCENT)
    c.setLineWidth(1)
    c.line(margin, y, W - margin, y)
    y -= 0.18 * inch

    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(margin, y, "SIGNATURES")
    y -= 0.28 * inch

    col1_x = margin
    col2_x = W / 2 + 0.1 * inch
    col_w = W / 2 - margin - 0.15 * inch

    for label, fname_name, fname_date, is_static, static_val in [
        ("OMNIX Quantum", "provider_sig", "provider_date", True, "Harold Nunes · Provider"),
        ("Client",        "client_sig",  "client_date",  False, ""),
    ]:
        cx = col1_x if label == "OMNIX Quantum" else col2_x
        c.setFillColor(OMNIX_GRAY)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(cx, y, label)

    y -= 0.25 * inch

    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica", 7.5)
    c.drawString(col1_x, y + 0.04 * inch, "Signature:")
    c.drawString(col2_x, y + 0.04 * inch, "Signature:")
    text_field(c, "provider_signature", col1_x + 0.75 * inch, y, col_w - 0.75 * inch)
    text_field(c, "client_signature",   col2_x + 0.75 * inch, y, col_w - 0.75 * inch)
    y -= 0.30 * inch

    c.drawString(col1_x, y + 0.04 * inch, "Name:")
    c.drawString(col2_x, y + 0.04 * inch, "Name:")
    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica", 8.5)
    c.drawString(col1_x + 0.75 * inch, y + 0.04 * inch, "Harold Nunes")
    text_field(c, "client_name_sig", col2_x + 0.75 * inch, y, col_w - 0.75 * inch)
    y -= 0.30 * inch

    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica", 7.5)
    c.drawString(col1_x, y + 0.04 * inch, "Date:")
    c.drawString(col2_x, y + 0.04 * inch, "Date:")
    text_field(c, "provider_date", col1_x + 0.75 * inch, y, col_w - 0.75 * inch)
    text_field(c, "client_date",   col2_x + 0.75 * inch, y, col_w - 0.75 * inch)

    c.save()
    print(f"Contract created: {path}")


def build_order_form():
    path = "omnix_contracts/OMNIX_Order_Form.pdf"
    c = pdfcanvas.Canvas(path, pagesize=letter)
    c.setTitle("OMNIX Order Form")
    c.setAuthor("OMNIX Quantum")
    c.setSubject("Order Form — Attachment to Governance Services Agreement")

    draw_header(c, 1, "Order Form")
    draw_footer(c, 1, "Order Form")

    margin = 0.55 * inch
    text_w = W - 2 * margin
    y = H - 1.0 * inch

    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W / 2, y, "OMNIX ORDER FORM")
    y -= 0.22 * inch
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, y,
        "Attachment to the OMNIX Governance Services Agreement  ·  Confidential")
    y -= 0.12 * inch
    c.setStrokeColor(OMNIX_ACCENT)
    c.setLineWidth(1.5)
    c.line(margin, y, W - margin, y)
    y -= 0.22 * inch

    y = section_bar(c, y, "A. PARTIES") - 0.12 * inch
    lbl_x = margin
    fld_x = margin + 1.65 * inch
    fld_w = text_w - 1.65 * inch

    party_fields = [
        ("Provider:",           "provider",       "OMNIX Quantum (operated by Harold Nunes)", True),
        ("Client Legal Name:",  "client_legal",   "", False),
        ("Contact Name:",       "contact_name",   "", False),
        ("Contact Email:",      "contact_email",  "", False),
        ("Client Address:",     "client_address", "", False),
    ]
    for label, fname, static, is_static in party_fields:
        c.setFillColor(OMNIX_GRAY)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(lbl_x, y + 0.04 * inch, label)
        if is_static:
            c.setFillColor(OMNIX_DARK)
            c.setFont("Helvetica", 8.5)
            c.drawString(fld_x, y + 0.04 * inch, static)
        else:
            text_field(c, fname, fld_x, y, fld_w)
        y -= 0.30 * inch

    y -= 0.1 * inch
    y = section_bar(c, y, "B. PLAN & PRICING") - 0.14 * inch

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y + 0.03 * inch, "Plan Selected:")

    plans = [
        ("Advisory",        "plan_advisory"),
        ("Enterprise Base", "plan_ent_base"),
        ("Enterprise Full", "plan_ent_full"),
        ("Custom",          "plan_custom"),
    ]
    px = margin + 1.65 * inch
    for plan_label, plan_fname in plans:
        checkbox(c, plan_fname, px, y, size=11, tooltip=plan_label)
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica", 8.5)
        c.drawString(px + 0.18 * inch, y + 0.01 * inch, plan_label)
        px += 1.25 * inch
    y -= 0.30 * inch

    pricing_fields = [
        ("Evaluations Included:", "evals_included"),
        ("Overage Rate / eval:",  "overage_rate"),
        ("Fee (Monthly/Annual):", "fee_amount"),
    ]
    for label, fname in pricing_fields:
        c.setFillColor(OMNIX_GRAY)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(margin, y + 0.04 * inch, label)
        text_field(c, fname, fld_x, y, fld_w)
        y -= 0.30 * inch

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y + 0.03 * inch, "Currency:")
    currencies = [("USD", "cur_usd"), ("AED", "cur_aed"), ("GBP", "cur_gbp")]
    px = fld_x
    for cur, cfname in currencies:
        checkbox(c, cfname, px, y, size=11, tooltip=cur)
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica", 8.5)
        c.drawString(px + 0.18 * inch, y + 0.01 * inch, cur)
        px += 0.75 * inch
    c.drawString(px + 0.18 * inch, y + 0.01 * inch, "Other:")
    text_field(c, "cur_other", px + 0.7 * inch, y, 1.0 * inch)
    y -= 0.30 * inch

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y + 0.03 * inch, "Billing Cycle:")
    billing = [("Monthly", "bill_monthly"), ("Annual (12 months)", "bill_annual")]
    px = fld_x
    for bl, bfname in billing:
        checkbox(c, bfname, px, y, size=11, tooltip=bl)
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica", 8.5)
        c.drawString(px + 0.18 * inch, y + 0.01 * inch, bl)
        px += 1.5 * inch
    y -= 0.30 * inch

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y + 0.03 * inch, "Payment Method:")
    payments = [("Wire Transfer", "pay_wire"), ("Stripe", "pay_stripe"), ("Invoice", "pay_invoice")]
    px = fld_x
    for pm, pfname in payments:
        checkbox(c, pfname, px, y, size=11, tooltip=pm)
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica", 8.5)
        c.drawString(px + 0.18 * inch, y + 0.01 * inch, pm)
        px += 1.2 * inch
    y -= 0.35 * inch

    y = section_bar(c, y, "C. TERM") - 0.14 * inch
    term_fields = [
        ("Start Date:",                 "start_date"),
        ("End Date / Renewal:",         "end_date"),
        ("Cancellation Notice Period:", "cancel_notice"),
    ]
    for label, fname in term_fields:
        c.setFillColor(OMNIX_GRAY)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(margin, y + 0.04 * inch, label)
        text_field(c, fname, fld_x, y, fld_w)
        y -= 0.30 * inch

    y -= 0.1 * inch
    y = section_bar(c, y, "D. SPECIAL CONDITIONS") - 0.1 * inch
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(margin, y + 0.03 * inch,
                 "Pilot terms, custom SLA, referral credits, or negotiated discounts.")
    y -= 0.22 * inch
    text_field(c, "special_conditions", margin, y, text_w, height=0.7 * inch)
    y -= 0.82 * inch

    y = section_bar(c, y, "E. CHANNEL PARTNER  (if applicable)") - 0.14 * inch
    partner_fields = [
        ("Partner Name:",       "partner_name"),
        ("Partner Entity:",     "partner_entity"),
        ("Commission %:",       "partner_commission"),
    ]
    for label, fname in partner_fields:
        c.setFillColor(OMNIX_GRAY)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(margin, y + 0.04 * inch, label)
        text_field(c, fname, fld_x, y, fld_w)
        y -= 0.30 * inch

    y -= 0.14 * inch
    c.setStrokeColor(OMNIX_ACCENT)
    c.setLineWidth(1)
    c.line(margin, y, W - margin, y)
    y -= 0.14 * inch

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(margin, y,
        "This Order Form is incorporated into and governed by the OMNIX Governance Services Agreement "
        "signed by both parties.")
    y -= 0.28 * inch

    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(margin, y, "SIGNATURES")
    y -= 0.28 * inch

    col1_x = margin
    col2_x = W / 2 + 0.1 * inch
    col_w  = W / 2 - margin - 0.15 * inch

    for label in ["OMNIX Quantum", "Client"]:
        cx = col1_x if label == "OMNIX Quantum" else col2_x
        c.setFillColor(OMNIX_GRAY)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(cx, y, label)
    y -= 0.26 * inch

    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica", 7.5)
    c.drawString(col1_x, y + 0.04 * inch, "Signature:")
    c.drawString(col2_x, y + 0.04 * inch, "Signature:")
    text_field(c, "of_provider_sig", col1_x + 0.75 * inch, y, col_w - 0.75 * inch)
    text_field(c, "of_client_sig",   col2_x + 0.75 * inch, y, col_w - 0.75 * inch)
    y -= 0.30 * inch

    c.drawString(col1_x, y + 0.04 * inch, "Name:")
    c.drawString(col2_x, y + 0.04 * inch, "Name:")
    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica", 8.5)
    c.drawString(col1_x + 0.75 * inch, y + 0.04 * inch, "Harold Nunes")
    text_field(c, "of_client_name", col2_x + 0.75 * inch, y, col_w - 0.75 * inch)
    y -= 0.30 * inch

    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica", 7.5)
    c.drawString(col1_x, y + 0.04 * inch, "Date:")
    c.drawString(col2_x, y + 0.04 * inch, "Date:")
    text_field(c, "of_provider_date", col1_x + 0.75 * inch, y, col_w - 0.75 * inch)
    text_field(c, "of_client_date",   col2_x + 0.75 * inch, y, col_w - 0.75 * inch)

    c.save()
    print(f"Order Form created: {path}")


if __name__ == "__main__":
    build_contract()
    build_order_form()
    print("Both fillable PDFs generated successfully.")
