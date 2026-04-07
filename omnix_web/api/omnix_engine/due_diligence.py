"""
OMNIX Due Diligence Report Generator
Generates premium PDF governance reports for M&A, PE due diligence, and regulatory audits.

Endpoint: GET /api/governance/due-diligence-report
Auth: X-API-Key required (client or admin)
"""

import io
import os
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as pdfcanvas

try:
    from api.omnix_engine.regulatory_mapping import (
        FRAMEWORK_METADATA,
        CHECKPOINT_REGULATORY_MAP,
    )
except ImportError:
    from omnix_engine.regulatory_mapping import (
        FRAMEWORK_METADATA,
        CHECKPOINT_REGULATORY_MAP,
    )

OMNIX_DARK   = colors.HexColor("#0A0A0F")
OMNIX_ACCENT = colors.HexColor("#00C6FF")
OMNIX_ACCENT2= colors.HexColor("#7B2FFF")
OMNIX_GRAY   = colors.HexColor("#555566")
OMNIX_LIGHT  = colors.HexColor("#F7F9FC")
OMNIX_GREEN  = colors.HexColor("#00C48C")
OMNIX_RED    = colors.HexColor("#FF4D6D")
OMNIX_YELLOW = colors.HexColor("#FFB020")
WHITE        = colors.white

W, H = letter
MARGIN = 0.6 * inch
TW = W - 2 * MARGIN

LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "public", "omnix_logo.png"
)


def _draw_header(c, page_num):
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
                      "CONFIDENTIAL — For Due Diligence Use Only")


def _draw_footer(c, page_num, generated_at):
    c.setFillColor(OMNIX_DARK)
    c.rect(0, 0, W, 0.42 * inch, fill=1, stroke=0)
    c.setFillColor(OMNIX_ACCENT)
    c.rect(0, 0.39 * inch, W, 0.03 * inch, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#555566"))
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN, 0.15 * inch,
                 f"OMNIX Quantum · Governance Due Diligence Report · Generated {generated_at}")
    c.drawRightString(W - MARGIN, 0.15 * inch, f"Page {page_num}")


def _section_bar(c, y, label, color=None):
    bar_color = color or OMNIX_DARK
    c.setFillColor(bar_color)
    c.rect(MARGIN, y, TW, 0.26 * inch, fill=1, stroke=0)
    c.setFillColor(OMNIX_ACCENT)
    c.rect(MARGIN, y, 0.05 * inch, 0.26 * inch, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN + 0.14 * inch, y + 0.08 * inch, label)
    return y - 0.08 * inch


def _kpi_box(c, x, y, w, h, label, value, sub, accent_color):
    c.setFillColor(OMNIX_LIGHT)
    c.roundRect(x, y, w, h, 4, fill=1, stroke=0)
    c.setFillColor(accent_color)
    c.rect(x, y + h - 0.04 * inch, w, 0.04 * inch, fill=1, stroke=0)
    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(x + w / 2, y + h * 0.38, str(value))
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(x + w / 2, y + h * 0.65, label.upper())
    c.setFont("Helvetica", 7)
    c.drawCentredString(x + w / 2, y + h * 0.18, sub)


def _wrap(text, font, size, max_w, c):
    words = text.split()
    lines, cur = [], ""
    c.setFont(font, size)
    for w in words:
        test = (cur + " " + w).strip()
        if c.stringWidth(test, font, size) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def generate_due_diligence_pdf(
    client_name: str,
    stats: dict,
    recent_receipts: list,
) -> bytes:
    """
    Generate a premium due diligence PDF report.

    Parameters
    ----------
    client_name : str
        Name of the client (for the report cover).
    stats : dict
        Keys: total_decisions, approved, blocked, hold, approval_rate,
              by_domain (dict: domain -> {total, approved, blocked})
    recent_receipts : list
        Last N receipt records: [{receipt_id, decision, domain, asset, timestamp}, ...]

    Returns
    -------
    bytes: PDF file content
    """
    buffer = io.BytesIO()
    c = pdfcanvas.Canvas(buffer, pagesize=letter)
    c.setTitle("OMNIX Governance Due Diligence Report")
    c.setAuthor("OMNIX Quantum")
    c.setSubject("Decision Governance Infrastructure — Due Diligence Package")

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    page_num = [1]

    def new_page():
        c.showPage()
        page_num[0] += 1
        _draw_header(c, page_num[0])
        _draw_footer(c, page_num[0], generated_at)
        return H - 1.0 * inch

    _draw_header(c, 1)
    _draw_footer(c, 1, generated_at)

    y = H - 1.05 * inch

    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(MARGIN, y, "GOVERNANCE DUE DILIGENCE REPORT")
    y -= 0.28 * inch
    c.setFillColor(OMNIX_ACCENT)
    c.setFont("Helvetica", 10)
    c.drawString(MARGIN, y, "Decision Governance Infrastructure  ·  OMNIX Quantum")
    y -= 0.18 * inch
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica", 8.5)
    c.drawString(MARGIN, y, f"Prepared for: {client_name}   ·   Generated: {generated_at}")
    y -= 0.12 * inch
    c.setStrokeColor(OMNIX_ACCENT)
    c.setLineWidth(1.5)
    c.line(MARGIN, y, W - MARGIN, y)
    y -= 0.25 * inch

    total = stats.get("total_decisions", 0)
    approved = stats.get("approved", 0)
    blocked = stats.get("blocked", 0)
    hold = stats.get("hold", 0)
    rate = stats.get("approval_rate", 0)

    kpi_w = (TW - 0.12 * inch * 3) / 4
    kpi_h = 0.9 * inch
    kpis = [
        ("Total Decisions", total, "Evaluated", OMNIX_ACCENT),
        ("Approved", approved, f"{round(approved/total*100) if total else 0}% of total", OMNIX_GREEN),
        ("Blocked", blocked, f"{round(blocked/total*100) if total else 0}% of total", OMNIX_RED),
        ("Approval Rate", f"{round(rate)}%", "30-day average", OMNIX_ACCENT2),
    ]
    kpi_x = MARGIN
    for label, value, sub, color in kpis:
        _kpi_box(c, kpi_x, y - kpi_h, kpi_w, kpi_h, label, value, sub, color)
        kpi_x += kpi_w + 0.12 * inch
    y -= kpi_h + 0.22 * inch

    y = _section_bar(c, y, "DOMAIN BREAKDOWN") - 0.14 * inch
    by_domain = stats.get("by_domain", {})
    if by_domain:
        col_w = TW / max(len(by_domain), 1)
        dx = MARGIN
        for domain, dstats in by_domain.items():
            dtotal = dstats.get("total", 0)
            dapproved = dstats.get("approved", 0)
            drate = round(dapproved / dtotal * 100) if dtotal else 0
            bar_max_w = col_w - 0.2 * inch
            bar_filled = bar_max_w * (drate / 100)

            c.setFillColor(OMNIX_DARK)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(dx + 0.05 * inch, y, domain.upper())
            c.setFillColor(OMNIX_GRAY)
            c.setFont("Helvetica", 7.5)
            c.drawString(dx + 0.05 * inch, y - 0.16 * inch, f"{dtotal} decisions")

            bar_y = y - 0.38 * inch
            c.setFillColor(colors.HexColor("#E0E8F0"))
            c.rect(dx + 0.05 * inch, bar_y, bar_max_w, 0.12 * inch, fill=1, stroke=0)
            c.setFillColor(OMNIX_GREEN if drate >= 70 else OMNIX_YELLOW if drate >= 40 else OMNIX_RED)
            c.rect(dx + 0.05 * inch, bar_y, bar_filled, 0.12 * inch, fill=1, stroke=0)
            c.setFillColor(OMNIX_DARK)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(dx + 0.05 * inch, bar_y - 0.16 * inch, f"{drate}% approval")
            dx += col_w
        y -= 0.65 * inch
    else:
        c.setFillColor(OMNIX_GRAY)
        c.setFont("Helvetica-Oblique", 8.5)
        c.drawString(MARGIN, y, "No domain-specific data available for this period.")
        y -= 0.25 * inch

    y -= 0.1 * inch
    y = _section_bar(c, y, "11-CHECKPOINT PIPELINE — REGULATORY COVERAGE") - 0.14 * inch

    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica", 8)
    desc = ("Each of the 11 governance checkpoints enforces specific requirements from the regulatory frameworks "
            "listed below. Every decision receipt constitutes a cryptographic attestation of compliance evaluation.")
    for line in _wrap(desc, "Helvetica", 8, TW, c):
        c.drawString(MARGIN, y, line)
        y -= 0.14 * inch
    y -= 0.08 * inch

    headers = ["Checkpoint", "Name", "Frameworks Enforced"]
    col_widths = [0.7 * inch, 1.8 * inch, TW - 2.5 * inch]
    hx = MARGIN
    c.setFillColor(colors.HexColor("#E8EEF6"))
    c.rect(MARGIN, y - 0.03 * inch, TW, 0.22 * inch, fill=1, stroke=0)
    for i, (hdr, cw) in enumerate(zip(headers, col_widths)):
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(hx + 0.04 * inch, y + 0.04 * inch, hdr)
        hx += cw
    y -= 0.26 * inch

    for cp_id, cp_data in CHECKPOINT_REGULATORY_MAP.items():
        fw_keys = list(cp_data["frameworks"].keys())
        fw_str = " · ".join(fw_keys)
        row_h = 0.20 * inch
        if y - row_h < 0.6 * inch:
            y = new_page()
            y -= 0.1 * inch

        rx = MARGIN
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(rx + 0.04 * inch, y + 0.04 * inch, cp_id)
        rx += col_widths[0]
        c.setFont("Helvetica", 7.5)
        c.drawString(rx + 0.04 * inch, y + 0.04 * inch, cp_data["name"])
        rx += col_widths[1]
        c.setFillColor(OMNIX_ACCENT2)
        c.setFont("Helvetica", 7)
        c.drawString(rx + 0.04 * inch, y + 0.04 * inch, fw_str)

        c.setStrokeColor(colors.HexColor("#E0E8F0"))
        c.setLineWidth(0.3)
        c.line(MARGIN, y, W - MARGIN, y)
        y -= row_h

    y -= 0.15 * inch
    if y - 0.3 * inch < 0.6 * inch:
        y = new_page()

    y = _section_bar(c, y, "REGULATORY FRAMEWORKS COVERED") - 0.14 * inch
    frameworks_to_show = list(FRAMEWORK_METADATA.items())
    fw_col_w = TW / 2 - 0.1 * inch
    col_positions = [MARGIN, MARGIN + fw_col_w + 0.2 * inch]
    col_idx = 0
    row_start_y = y

    for fw_key, fw_meta in frameworks_to_show:
        if y - 0.7 * inch < 0.6 * inch:
            if col_idx == 0:
                col_idx = 1
                y = row_start_y
            else:
                y = new_page()
                col_idx = 0
                row_start_y = y

        fx = col_positions[col_idx]
        c.setFillColor(OMNIX_LIGHT)
        c.roundRect(fx, y - 0.58 * inch, fw_col_w, 0.65 * inch, 3, fill=1, stroke=0)
        c.setFillColor(OMNIX_ACCENT)
        c.roundRect(fx, y + 0.04 * inch, fw_col_w, 0.04 * inch, 2, fill=1, stroke=0)
        c.setFillColor(OMNIX_DARK)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(fx + 0.1 * inch, y - 0.05 * inch, fw_meta["full_name"])
        c.setFillColor(OMNIX_GRAY)
        c.setFont("Helvetica", 7.5)
        c.drawString(fx + 0.1 * inch, y - 0.20 * inch, fw_meta["status"])
        lines = _wrap(fw_meta["applies_to"], "Helvetica", 7, fw_col_w - 0.2 * inch, c)
        for li, line in enumerate(lines[:2]):
            c.drawString(fx + 0.1 * inch, y - 0.34 * inch - li * 0.13 * inch, line)

        col_idx = 1 - col_idx
        if col_idx == 0:
            y -= 0.75 * inch

    if col_idx == 1:
        y -= 0.75 * inch

    y -= 0.1 * inch
    if y - 1.2 * inch < 0.6 * inch:
        y = new_page()

    y = _section_bar(c, y, "RECENT GOVERNANCE RECEIPTS") - 0.14 * inch
    if recent_receipts:
        receipt_headers = ["Receipt ID", "Decision", "Domain", "Asset", "Timestamp"]
        receipt_col_w = [2.0 * inch, 0.85 * inch, 0.9 * inch, 1.0 * inch, 1.55 * inch]
        rhx = MARGIN
        c.setFillColor(colors.HexColor("#E8EEF6"))
        c.rect(MARGIN, y - 0.03 * inch, TW, 0.22 * inch, fill=1, stroke=0)
        for hdr, cw in zip(receipt_headers, receipt_col_w):
            c.setFillColor(OMNIX_DARK)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawString(rhx + 0.04 * inch, y + 0.04 * inch, hdr)
            rhx += cw
        y -= 0.26 * inch

        for r in recent_receipts[:10]:
            if y - 0.20 * inch < 0.6 * inch:
                y = new_page()
            rx2 = MARGIN
            decision = r.get("decision", "")
            dec_color = OMNIX_GREEN if decision == "APPROVED" else OMNIX_RED if decision == "BLOCKED" else OMNIX_YELLOW
            vals = [
                r.get("receipt_id", ""),
                decision,
                r.get("domain", ""),
                r.get("asset", ""),
                str(r.get("timestamp", ""))[:19],
            ]
            for i, (val, cw) in enumerate(zip(vals, receipt_col_w)):
                if i == 1:
                    c.setFillColor(dec_color)
                    c.setFont("Helvetica-Bold", 7.5)
                else:
                    c.setFillColor(OMNIX_DARK)
                    c.setFont("Helvetica", 7.5)
                c.drawString(rx2 + 0.04 * inch, y + 0.04 * inch, str(val)[:28])
                rx2 += cw
            c.setStrokeColor(colors.HexColor("#E0E8F0"))
            c.setLineWidth(0.3)
            c.line(MARGIN, y, W - MARGIN, y)
            y -= 0.20 * inch
    else:
        c.setFillColor(OMNIX_GRAY)
        c.setFont("Helvetica-Oblique", 8.5)
        c.drawString(MARGIN, y, "No receipts available for this period.")
        y -= 0.25 * inch

    y -= 0.15 * inch
    if y - 0.8 * inch < 0.6 * inch:
        y = new_page()

    y = _section_bar(c, y, "ATTESTATION") - 0.14 * inch
    attest_text = (
        "This report is generated by OMNIX Quantum's automated governance infrastructure. "
        "Each governance receipt referenced herein is cryptographically signed using NIST-standardized "
        "post-quantum algorithms and chain-linked to the OMNIX Transparency Chain — an append-only, "
        "Merkle-style audit log. Receipts may be independently verified at omnixquantum.net/verify. "
        "This document constitutes a governance attestation package for M&A due diligence, "
        "investor review, and regulatory audit purposes. It does not constitute legal or financial advice."
    )
    c.setFillColor(OMNIX_DARK)
    c.setFont("Helvetica", 8.5)
    for line in _wrap(attest_text, "Helvetica", 8.5, TW, c):
        c.drawString(MARGIN, y, line)
        y -= 0.15 * inch

    y -= 0.15 * inch
    c.setStrokeColor(OMNIX_ACCENT)
    c.setLineWidth(1)
    c.line(MARGIN, y, W - MARGIN, y)
    y -= 0.12 * inch
    c.setFillColor(OMNIX_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN, y, "OMNIX Quantum")
    c.setFont("Helvetica", 7.5)
    c.drawRightString(W - MARGIN, y, "omnixquantum.net  ·  contacto@omnixquantum.net")

    c.save()
    buffer.seek(0)
    return buffer.read()
