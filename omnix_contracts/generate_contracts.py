from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas
import os

OMNIX_DARK   = colors.HexColor("#0A0A0F")
OMNIX_ACCENT = colors.HexColor("#00C6FF")
OMNIX_GRAY   = colors.HexColor("#666666")
OMNIX_LIGHT_GRAY = colors.HexColor("#999999")
OMNIX_FIELD  = colors.HexColor("#F0F6FF")
OMNIX_BORDER = colors.HexColor("#B0C4DE")
WHITE        = colors.white

LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "omnix_web", "public", "omnix_logo.png"
)

W, H = letter
MARGIN = 0.55 * inch
TEXT_W = W - 2 * MARGIN


def draw_header(c, page_num, doc_name):
    c.setFillColor(OMNIX_DARK)
    c.rect(0, H - 0.75 * inch, W, 0.75 * inch, fill=1, stroke=0)
    c.setFillColor(OMNIX_ACCENT)
    c.rect(0, H - 0.75 * inch, W, 0.03 * inch, fill=1, stroke=0)
    logo_h = 0.44 * inch
    logo_w = logo_h * (569 / 379)
    logo_y = H - 0.75 * inch + (0.75 * inch - logo_h) / 2
    if os.path.exists(LOGO_PATH):
        c.drawImage(LOGO_PATH, MARGIN - 0.1 * inch, logo_y,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, mask="auto")
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica", 7.5)
    c.drawRightString(W - MARGIN + 0.1 * inch, H - 0.75 * inch + 0.30 * inch,
                      "Decision Governance Infrastructure")
    c.setFillColor(colors.HexColor("#444455"))
    c.setFont("Helvetica", 7)
    c.drawRightString(W - MARGIN + 0.1 * inch, H - 0.75 * inch + 0.16 * inch,
                      "Confidential · omnibotgenesis.up.railway.app")


def draw_footer(c, page_num, doc_name):
    c.setFillColor(OMNIX_DARK)
    c.rect(0, 0, W, 0.42 * inch, fill=1, stroke=0)
    c.setFillColor(OMNIX_ACCENT)
    c.rect(0, 0.39 * inch, W, 0.03 * inch, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#555566"))
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN, 0.15 * inch,
                 f"OMNIX Quantum  ·  {doc_name}  ·  England & Wales")
    c.drawRightString(W - MARGIN, 0.15 * inch, f"Page {page_num}")


def text_field(c, name, x, y, width, height=0.21 * inch, tooltip="", font_size=9):
    c.acroForm.textfield(
        name=name, tooltip=tooltip,
        x=x, y=y, width=width, height=height,
        fontSize=font_size,
        textColor=OMNIX_DARK,
        fillColor=OMNIX_FIELD,
        borderColor=OMNIX_BORDER,
        borderWidth=0.5,
        fieldFlags="",
    )


def checkbox_field(c, name, x, y, size=11, tooltip=""):
    c.acroForm.checkbox(
        name=name, tooltip=tooltip,
        x=x, y=y, size=size,
        fillColor=OMNIX_FIELD,
        borderColor=OMNIX_BORDER,
        borderWidth=0.5,
        buttonStyle="check",
        forceBorder=True,
    )


def section_bar(c, y, label):
    c.setFillColor(OMNIX_DARK)
    c.rect(MARGIN, y, TEXT_W, 0.23 * inch, fill=1, stroke=0)
    c.setFillColor(OMNIX_ACCENT)
    c.rect(MARGIN, y, 0.04 * inch, 0.23 * inch, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(MARGIN + 0.12 * inch, y + 0.07 * inch, label)
    return y - 0.07 * inch


def static_row(c, label, value, y, lbl_w=1.65 * inch):
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN, y + 0.04 * inch, label)
    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica", 8.5)
    c.drawString(MARGIN + lbl_w, y + 0.04 * inch, value)
    return y - 0.27 * inch


def fillable_row(c, label, fname, y, lbl_w=1.65 * inch, fh=0.21 * inch, tooltip=""):
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN, y + 0.04 * inch, label)
    text_field(c, fname, MARGIN + lbl_w, y, TEXT_W - lbl_w, fh, tooltip=tooltip)
    return y - (fh + 0.09 * inch)


def wrap_text(text, font, size, max_width, canvas_obj):
    words = text.split()
    lines, current = [], ""
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


def maybe_new_page(c, y, needed, page_ref, doc_name):
    if y - needed < 0.6 * inch:
        c.showPage()
        page_ref[0] += 1
        draw_header(c, page_ref[0], doc_name)
        draw_footer(c, page_ref[0], doc_name)
        return H - 1.0 * inch
    return y


CONTRACT_SECTIONS = [
    ("1. SERVICES",
     'OMNIX Quantum provides a decision governance evaluation layer (the "Service"). The Service evaluates '
     'signals submitted by the Client through a multi-checkpoint pipeline and returns a cryptographically '
     'signed governance receipt for each evaluation. OMNIX does not approve, authorize, or validate decisions. '
     'It provides a governance evaluation only. OMNIX does not execute decisions, transactions, or actions '
     'on behalf of the Client.'),
    ("2. NO WARRANTY",
     'The Service is provided "as is" and "as available," without warranties of any kind, express or implied, '
     'including but not limited to warranties of merchantability, fitness for a particular purpose, or '
     'uninterrupted availability.'),
    ("3. NO ADVISORY — CLIENT RESPONSIBILITY",
     'The Service does not constitute financial, legal, operational, or investment advice. All decisions '
     'executed by the Client remain the sole responsibility of the Client. OMNIX evaluates signals — it does '
     'not direct, recommend, or authorize any action.'),
    ("4. DATA RESPONSIBILITY",
     'The Client is solely responsible for the data submitted to the Service and confirms it has the legal '
     'right to use such data. OMNIX shall not be liable for any issues arising from the content, accuracy, '
     'or legality of data provided by the Client.'),
    ("5. LIMITATION OF LIABILITY",
     "OMNIX shall not be liable for any losses, damages, missed opportunities, or claims arising from "
     "decisions made or actions taken by the Client, whether or not those decisions were evaluated through "
     "the Service. In no event shall OMNIX's total liability exceed the fees paid by the Client in the "
     "three (3) months preceding the claim."),
    ("6. INDEPENDENCE FROM THIRD PARTIES",
     'OMNIX is an independent system and is not responsible for the actions, outputs, or failures of any '
     'third party, including channel partners or intermediaries through which the Client accessed the Service.'),
    ("7. SERVICE AVAILABILITY",
     'OMNIX operates on a best-effort basis. Enterprise plans include a 99.9% uptime SLA. Advisory plans do '
     'not carry an uptime guarantee. OMNIX shall not be liable for damages resulting from service interruptions.'),
    ("8. FORCE MAJEURE",
     'OMNIX shall not be liable for delays or failures in performance caused by events beyond its reasonable '
     'control, including but not limited to natural disasters, cyberattacks, infrastructure failures, or '
     'regulatory actions.'),
    ("9. INTELLECTUAL PROPERTY",
     "All technology, algorithms, methodologies, and systems comprising OMNIX remain the exclusive property "
     "of the Provider. The Client receives a limited, non-transferable, non-sublicensable right to access the "
     "Service during the term of this Agreement. The Client shall not reverse-engineer, replicate, or disclose "
     "OMNIX's evaluation methodology."),
    ("10. CONFIDENTIALITY",
     'Both parties agree to keep the terms of this Agreement and any proprietary information exchanged strictly '
     'confidential for the duration of this Agreement and for two (2) years thereafter.'),
    ("11. PAYMENT",
     'Fees are as agreed in the applicable Order Form. Overages are billed at the rate specified per plan. '
     'Invoices are due within 15 days of issuance. Failure to pay within the due date may result in '
     'immediate suspension of the Service.'),
    ("12. TERM AND TERMINATION",
     'This Agreement begins on the Effective Date. Advisory plans may be cancelled with 30 days written '
     'notice. Enterprise plans are subject to the annual contract term specified in the Order Form. OMNIX may '
     'suspend or terminate access immediately for non-payment or material breach.'),
    ("13. GOVERNING LAW",
     'This Agreement is governed by the laws of England and Wales. Any disputes shall be resolved by binding '
     'arbitration under the rules of the London Court of International Arbitration (LCIA).'),
]


def build_contract():
    path = "omnix_contracts/OMNIX_Governance_Services_Agreement.pdf"
    c = pdfcanvas.Canvas(path, pagesize=letter)
    c.setTitle("OMNIX Governance Services Agreement")
    c.setAuthor("OMNIX Quantum")
    c.setSubject("Standard Client Agreement")

    page_ref = [1]
    draw_header(c, 1, "Governance Services Agreement")
    draw_footer(c, 1, "Standard Client Agreement")

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
    c.line(MARGIN, y, W - MARGIN, y)
    y -= 0.20 * inch

    y = static_row(c, "Provider:", "OMNIX Quantum (operated by Harold Nunes)", y)
    y = fillable_row(c, "Client:", "client_name", y, tooltip="Full legal name of the client")
    y = fillable_row(c, "Effective Date:", "effective_date", y, tooltip="Agreement start date")

    y -= 0.05 * inch
    c.setStrokeColor(colors.HexColor("#DDDDDD"))
    c.setLineWidth(0.5)
    c.line(MARGIN, y, W - MARGIN, y)
    y -= 0.15 * inch

    for title, body in CONTRACT_SECTIONS:
        body_lines = wrap_text(body, "Helvetica", 8.5, TEXT_W - 0.1 * inch, c)
        needed = 0.23 * inch + 0.1 * inch + len(body_lines) * 0.145 * inch + 0.12 * inch
        y = maybe_new_page(c, y, needed, page_ref, "Governance Services Agreement")

        y = section_bar(c, y, title) - 0.1 * inch
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica", 8.5)
        for line in body_lines:
            c.drawString(MARGIN + 0.06 * inch, y, line)
            y -= 0.145 * inch
        y -= 0.07 * inch

    y = maybe_new_page(c, y, 1.8 * inch, page_ref, "Governance Services Agreement")

    y -= 0.1 * inch
    c.setStrokeColor(OMNIX_ACCENT)
    c.setLineWidth(1)
    c.line(MARGIN, y, W - MARGIN, y)
    y -= 0.18 * inch
    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(MARGIN, y, "SIGNATURES")
    y -= 0.28 * inch

    col1_x = MARGIN
    col2_x = W / 2 + 0.1 * inch
    col_w  = W / 2 - MARGIN - 0.15 * inch

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(col1_x, y, "OMNIX Quantum")
    c.drawString(col2_x, y, "Client")
    y -= 0.26 * inch

    rows = [
        ("Signature:", "provider_sig", "client_sig"),
        ("Date:",      "provider_date", "client_date"),
    ]
    for label, f1, f2 in rows:
        c.setFillColor(OMNIX_LIGHT_GRAY)
        c.setFont("Helvetica", 7.5)
        c.drawString(col1_x, y + 0.04 * inch, label)
        c.drawString(col2_x, y + 0.04 * inch, label)
        text_field(c, f1, col1_x + 0.75 * inch, y, col_w - 0.75 * inch)
        text_field(c, f2, col2_x + 0.75 * inch, y, col_w - 0.75 * inch)
        y -= 0.30 * inch

    c.setFillColor(OMNIX_LIGHT_GRAY)
    c.setFont("Helvetica", 7.5)
    c.drawString(col1_x, y + 0.04 * inch, "Name:")
    c.drawString(col2_x, y + 0.04 * inch, "Name:")
    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica", 8.5)
    c.drawString(col1_x + 0.75 * inch, y + 0.04 * inch, "Harold Nunes")
    text_field(c, "client_name_sig", col2_x + 0.75 * inch, y, col_w - 0.75 * inch,
               tooltip="Authorized signatory name")

    c.save()
    print(f"Contract created: {path}")


def build_order_form():
    path = "omnix_contracts/OMNIX_Order_Form.pdf"
    c = pdfcanvas.Canvas(path, pagesize=letter)
    c.setTitle("OMNIX Order Form")
    c.setAuthor("OMNIX Quantum")
    c.setSubject("Order Form — Attachment to Governance Services Agreement")

    page_ref = [1]
    draw_header(c, 1, "Order Form")
    draw_footer(c, 1, "Order Form")

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
    c.line(MARGIN, y, W - MARGIN, y)
    y -= 0.22 * inch

    y = section_bar(c, y, "A. PARTIES") - 0.12 * inch
    y = static_row(c, "Provider:",        "OMNIX Quantum (operated by Harold Nunes)", y)
    y = static_row(c, "Provider Email:",  "harold@omnixquantum.com", y)
    y = static_row(c, "Governing Law:",   "England and Wales  ·  LCIA Arbitration", y)
    y -= 0.05 * inch
    y = fillable_row(c, "Client Legal Name:", "client_legal",   y, tooltip="Full legal entity name")
    y = fillable_row(c, "Contact Name:",      "contact_name",   y, tooltip="Primary point of contact")
    y = fillable_row(c, "Contact Email:",     "contact_email",  y, tooltip="Email for notices and invoices")
    y = fillable_row(c, "Client Address:",    "client_address", y, tooltip="Registered address")

    y -= 0.1 * inch
    y = section_bar(c, y, "B. PLAN & PRICING") - 0.14 * inch

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN, y + 0.03 * inch, "Plan Selected:")

    plans = [
        ("Advisory",        "plan_advisory"),
        ("Enterprise Base", "plan_ent_base"),
        ("Enterprise Full", "plan_ent_full"),
        ("Custom",          "plan_custom"),
    ]
    px = MARGIN + 1.65 * inch
    for plan_label, plan_fname in plans:
        checkbox_field(c, plan_fname, px, y, tooltip=plan_label)
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica", 8.5)
        c.drawString(px + 0.18 * inch, y + 0.01 * inch, plan_label)
        px += 1.25 * inch
    y -= 0.30 * inch

    y = fillable_row(c, "Evaluations Included:", "evals_included", y,
                     tooltip="Number of evaluations included in plan")
    y = fillable_row(c, "Overage Rate / eval:",  "overage_rate",   y,
                     tooltip="Price per evaluation over the included limit")
    y = fillable_row(c, "Fee (Monthly/Annual):", "fee_amount",      y,
                     tooltip="Total agreed fee")

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN, y + 0.03 * inch, "Currency:")
    currencies = [("USD", "cur_usd"), ("AED", "cur_aed"), ("GBP", "cur_gbp")]
    px = MARGIN + 1.65 * inch
    for cur, cfname in currencies:
        checkbox_field(c, cfname, px, y, tooltip=cur)
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica", 8.5)
        c.drawString(px + 0.18 * inch, y + 0.01 * inch, cur)
        px += 0.78 * inch
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica", 8)
    c.drawString(px + 0.01 * inch, y + 0.03 * inch, "Other:")
    text_field(c, "cur_other", px + 0.52 * inch, y, 0.9 * inch, tooltip="Other currency")
    y -= 0.30 * inch

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN, y + 0.03 * inch, "Billing Cycle:")
    billing = [("Monthly", "bill_monthly"), ("Annual (12 months)", "bill_annual")]
    px = MARGIN + 1.65 * inch
    for bl, bfname in billing:
        checkbox_field(c, bfname, px, y, tooltip=bl)
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica", 8.5)
        c.drawString(px + 0.18 * inch, y + 0.01 * inch, bl)
        px += 1.55 * inch
    y -= 0.30 * inch

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN, y + 0.03 * inch, "Payment Method:")
    payments = [("Wire Transfer", "pay_wire"), ("Stripe", "pay_stripe"), ("Invoice", "pay_invoice")]
    px = MARGIN + 1.65 * inch
    for pm, pfname in payments:
        checkbox_field(c, pfname, px, y, tooltip=pm)
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica", 8.5)
        c.drawString(px + 0.18 * inch, y + 0.01 * inch, pm)
        px += 1.22 * inch
    y -= 0.35 * inch

    y = section_bar(c, y, "C. TERM") - 0.14 * inch
    y = static_row(c, "Payment Terms:",    "Net 15 days from invoice date", y)
    y = static_row(c, "Late Payment:",     "Immediate suspension of access", y)
    y = static_row(c, "Cancellation:",     "Advisory: 30 days notice  ·  Enterprise: per contract term", y)
    y -= 0.05 * inch
    y = fillable_row(c, "Start Date:",     "start_date", y, tooltip="Service start date")
    y = fillable_row(c, "End Date:",       "end_date",   y, tooltip="Contract end date or renewal date")

    y -= 0.1 * inch
    y = section_bar(c, y, "D. SPECIAL CONDITIONS") - 0.1 * inch
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(MARGIN, y + 0.03 * inch,
                 "Pilot terms, custom SLA, referral credits, or negotiated discounts. Leave blank if none.")
    y -= 0.22 * inch
    text_field(c, "special_conditions", MARGIN, y, TEXT_W, height=0.65 * inch,
               tooltip="Special conditions, pilot terms, or notes")
    y -= 0.78 * inch

    y = section_bar(c, y, "E. CHANNEL PARTNER  (if applicable)") - 0.14 * inch
    y = static_row(c, "Commission Rate:", "10% of net contract value (mutual referral)", y)
    y -= 0.05 * inch
    y = fillable_row(c, "Partner Name:",   "partner_name",       y, tooltip="Channel partner name")
    y = fillable_row(c, "Partner Entity:", "partner_entity",     y, tooltip="Legal entity of partner")

    y -= 0.12 * inch
    c.setStrokeColor(OMNIX_ACCENT)
    c.setLineWidth(1)
    c.line(MARGIN, y, W - MARGIN, y)
    y -= 0.13 * inch
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(MARGIN, y,
        "This Order Form is incorporated into and governed by the OMNIX Governance Services Agreement "
        "signed by both parties. In case of conflict, the Agreement prevails.")
    y -= 0.28 * inch

    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(MARGIN, y, "SIGNATURES")
    y -= 0.28 * inch

    col1_x = MARGIN
    col2_x = W / 2 + 0.1 * inch
    col_w  = W / 2 - MARGIN - 0.15 * inch

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(col1_x, y, "OMNIX Quantum")
    c.drawString(col2_x, y, "Client")
    y -= 0.26 * inch

    for label, f1, f2 in [("Signature:", "of_provider_sig", "of_client_sig"),
                           ("Date:",      "of_provider_date", "of_client_date")]:
        c.setFillColor(OMNIX_LIGHT_GRAY)
        c.setFont("Helvetica", 7.5)
        c.drawString(col1_x, y + 0.04 * inch, label)
        c.drawString(col2_x, y + 0.04 * inch, label)
        text_field(c, f1, col1_x + 0.75 * inch, y, col_w - 0.75 * inch)
        text_field(c, f2, col2_x + 0.75 * inch, y, col_w - 0.75 * inch)
        y -= 0.30 * inch

    c.setFillColor(OMNIX_LIGHT_GRAY)
    c.setFont("Helvetica", 7.5)
    c.drawString(col1_x, y + 0.04 * inch, "Name:")
    c.drawString(col2_x, y + 0.04 * inch, "Name:")
    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica", 8.5)
    c.drawString(col1_x + 0.75 * inch, y + 0.04 * inch, "Harold Nunes")
    text_field(c, "of_client_name", col2_x + 0.75 * inch, y, col_w - 0.75 * inch,
               tooltip="Authorized signatory name")

    c.save()
    print(f"Order Form created: {path}")


if __name__ == "__main__":
    build_contract()
    build_order_form()
    print("Both fillable PDFs generated successfully.")
