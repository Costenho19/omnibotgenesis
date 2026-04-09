"""
OMNIX — Post-Quantum Mandate Receipt Schema Specification
Integration Document for Velos / Naimat Khan
Generated: 2026-04-09
"""
import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas as pdf_canvas

DARK_BG    = HexColor('#0a0f1a')
DARK_MID   = HexColor('#0f172a')
CARD_BG    = HexColor('#1e293b')
GOLD       = HexColor('#C9A227')
GOLD_LIGHT = HexColor('#F5D97A')
GREEN_OK   = HexColor('#10b981')
GREEN_DIM  = HexColor('#064e3b')
RED_ALERT  = HexColor('#ef4444')
BLUE       = HexColor('#3b82f6')
BLUE_DIM   = HexColor('#1e3a5f')
LIGHT_GRAY = HexColor('#94a3b8')
MED_GRAY   = HexColor('#475569')
WHITE      = HexColor('#ffffff')
MONO_GREEN = HexColor('#4ade80')
ORANGE     = HexColor('#f97316')


class NumberedCanvas(pdf_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        pdf_canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def _startPage(self):
        pdf_canvas.Canvas._startPage(self)
        self.saveState()
        self.setFillColor(DARK_BG)
        self.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        self.restoreState()

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.setFont("Helvetica", 7)
            self.setFillColor(LIGHT_GRAY)
            self.drawCentredString(
                A4[0] / 2, 0.32 * inch,
                f"OMNIX Decision Governance Infrastructure  —  Post-Quantum Schema v6.5.4e  —  "
                f"Confidential / Velos Integration  —  Page {self._pageNumber} of {num_pages}"
            )
            self.setStrokeColor(GOLD)
            self.setLineWidth(0.5)
            self.line(0.7 * inch, 0.55 * inch, A4[0] - 0.7 * inch, 0.55 * inch)
            pdf_canvas.Canvas.showPage(self)
        pdf_canvas.Canvas.save(self)


def S(name, **kw):
    return ParagraphStyle(name, **kw)


def section_header(title, story, styles):
    story.append(Spacer(1, 0.12 * inch))
    tbl = Table([[Paragraph(title, S('sh', fontSize=11, textColor=GOLD,
                                     fontName='Helvetica-Bold', spaceAfter=0)
                             )]], colWidths=[7.0 * inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), CARD_BG),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LINEBELOW',     (0, 0), (-1, -1), 1.5, GOLD),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.1 * inch))


def mono_block(lines, story, bg=DARK_MID, text_color=MONO_GREEN):
    rows = [[Paragraph(line, S('mb', fontSize=7, textColor=text_color,
                               fontName='Courier', leading=11, spaceAfter=0))]
            for line in lines]
    tbl = Table(rows, colWidths=[7.0 * inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), bg),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BOX',           (0, 0), (-1, -1), 0.5, MED_GRAY),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.08 * inch))


def field_table(rows, story, col_widths=None):
    if col_widths is None:
        col_widths = [1.6 * inch, 0.9 * inch, 4.5 * inch]
    header = [
        Paragraph("Field", S('th', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Type", S('th', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Description", S('th', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
    ]
    table_data = [header]
    for r in rows:
        table_data.append([
            Paragraph(r[0], S('tc', fontSize=8, textColor=MONO_GREEN, fontName='Courier')),
            Paragraph(r[1], S('tt', fontSize=8, textColor=LIGHT_GRAY, fontName='Helvetica-Oblique')),
            Paragraph(r[2], S('td', fontSize=8, textColor=WHITE, fontName='Helvetica', leading=12)),
        ])
    tbl = Table(table_data, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  CARD_BG),
        ('BACKGROUND',    (0, 1), (-1, -1), DARK_MID),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [DARK_MID, HexColor('#111827')]),
        ('GRID',          (0, 0), (-1, -1), 0.3, MED_GRAY),
        ('BOX',           (0, 0), (-1, -1), 0.8, GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.1 * inch))


def body(text, story, color=WHITE, size=9, indent=0, align=TA_JUSTIFY):
    story.append(Paragraph(text, S('bd', fontSize=size, textColor=color,
                                   fontName='Helvetica', leading=14,
                                   spaceAfter=6, leftIndent=indent,
                                   alignment=align)))


def bullet(text, story, color=LIGHT_GRAY):
    story.append(Paragraph(
        f"<bullet>&bull;</bullet> {text}",
        S('bl', fontSize=8.5, textColor=color, fontName='Helvetica',
          leading=13, spaceAfter=4, leftIndent=14, bulletIndent=4)
    ))


def alert_box(text, story, bg=BLUE_DIM, border=BLUE, text_color=GOLD_LIGHT):
    tbl = Table([[Paragraph(text, S('ab', fontSize=9, textColor=text_color,
                                    fontName='Helvetica-Bold', leading=14,
                                    alignment=TA_LEFT))
                  ]], colWidths=[7.0 * inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), bg),
        ('BOX',           (0, 0), (-1, -1), 1.5, border),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 14),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 14),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.1 * inch))


def build_pdf():
    output_path = "docs/integration/OMNIX_Velos_Schema_PQC_Receipt.pdf"
    os.makedirs("docs/integration", exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.65 * inch, bottomMargin=0.8 * inch,
    )

    story = []

    # ── COVER PAGE ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.2 * inch))

    logo_path = "docs/omnix_quantum_logo.png"
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=1.5 * inch, height=1.5 * inch)
        logo_tbl = Table([[logo_img]], colWidths=[7.0 * inch])
        logo_tbl.setStyle(TableStyle([
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(logo_tbl)
        story.append(Spacer(1, 0.18 * inch))

    cover_box = [[Paragraph("OMNIX", S('ct', fontSize=32, textColor=GOLD,
                                        fontName='Helvetica-Bold', alignment=TA_CENTER))]]
    cover_tbl = Table(cover_box, colWidths=[7.0 * inch])
    cover_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), DARK_MID),
        ('BOX',           (0, 0), (-1, -1), 2, GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 18),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 18),
    ]))
    story.append(cover_tbl)
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph(
        "Decision Governance Infrastructure",
        S('cs', fontSize=12, textColor=LIGHT_GRAY, fontName='Helvetica', alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 0.22 * inch))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD))
    story.append(Spacer(1, 0.18 * inch))

    story.append(Paragraph(
        "POST-QUANTUM MANDATE RECEIPT",
        S('dt', fontSize=18, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 0.06 * inch))
    story.append(Paragraph(
        "Schema Specification — Velos Integration Document",
        S('ds', fontSize=11, textColor=GOLD_LIGHT, fontName='Helvetica-Bold', alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 0.06 * inch))
    story.append(Paragraph(
        "Schema v6.5.4e  |  ADR-022, ADR-031, ADR-043, ADR-044  |  T=0 Gateway Edition",
        S('dm', fontSize=8.5, textColor=LIGHT_GRAY, fontName='Helvetica', alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 0.28 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MED_GRAY))
    story.append(Spacer(1, 0.2 * inch))

    meta_rows = [
        ["For",              "Naimat Khan — Velos"],
        ["Prepared by",      "Harold Nunes — OMNIX QUANTUM LTD"],
        ["Date",             today],
        ["Classification",   "Confidential — Partner Integration Material"],
        ["Schema Version",   "v6.5.4e"],
        ["Engine Version",   "6.5.4e"],
        ["Signing Standard", "NIST FIPS 204 — ML-DSA (Dilithium-3 / Dilithium-5)"],
        ["KEM Standard",     "NIST FIPS 203 — ML-KEM (Kyber-768)"],
        ["Purpose",          "T=0 Interceptor Gateway — Velos POST endpoint integration"],
    ]
    meta_tbl = Table(meta_rows, colWidths=[2.0 * inch, 5.0 * inch])
    meta_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, -1), CARD_BG),
        ('BACKGROUND',    (1, 0), (1, -1), DARK_BG),
        ('TEXTCOLOR',     (0, 0), (0, -1), GOLD),
        ('TEXTCOLOR',     (1, 0), (1, -1), WHITE),
        ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',      (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8.5),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('GRID',          (0, 0), (-1, -1), 0.3, MED_GRAY),
        ('BOX',           (0, 0), (-1, -1), 1, GOLD),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 0.28 * inch))

    key_box = [[Paragraph(
        "Every decision emitted by OMNIX produces a Post-Quantum Decision Receipt — "
        "a cryptographically signed JSON object encoding the complete governance trail "
        "of a single enforcement decision. This document defines the exact schema "
        "Velos must implement to correctly verify receipts at its T=0 interceptor gateway.",
        S('kb', fontSize=8.5, textColor=GOLD_LIGHT, fontName='Helvetica-BoldOblique',
          alignment=TA_CENTER, leading=14)
    )]]
    key_tbl = Table(key_box, colWidths=[7.0 * inch])
    key_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), CARD_BG),
        ('BOX',           (0, 0), (-1, -1), 1.5, GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING',   (0, 0), (-1, -1), 18),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 18),
    ]))
    story.append(key_tbl)
    story.append(PageBreak())

    # ── SECTION 1: OVERVIEW ──────────────────────────────────────────────────────
    section_header("1.  Overview", story, None)

    body("The OMNIX receipt is the atomic unit of the evidence layer. Each receipt is:", story)
    bullet("Signed using NIST FIPS 204 — Dilithium-3 (ML-DSA-65) at enterprise baseline, "
           "or Dilithium-5 (ML-DSA-87) at high-assurance tier", story)
    bullet("Chained — each receipt includes the SHA-256 hash of its predecessor, "
           "forming a tamper-evident audit trail", story)
    bullet("Time-bounded — carries explicit ttl_epoch_ms for T=0 gateway enforcement", story)
    bullet("Domain-agnostic — identical schema for trading, Islamic credit, insurance, and robotics", story)
    story.append(Spacer(1, 0.12 * inch))

    alert_box(
        "ENDPOINT:  POST  https://velos-gateway.onrender.com/api/v1/intercept\n"
        "All OMNIX receipts sent to this endpoint must pass TTL check + hash integrity + "
        "PQC signature verification before any downstream action is triggered.",
        story, bg=GREEN_DIM, border=GREEN_OK, text_color=MONO_GREEN
    )

    # ── SECTION 2: COMPLETE FIELD REFERENCE ──────────────────────────────────────
    section_header("2.  Complete JSON Field Reference", story, None)

    mono_block([
        "{",
        '  "receipt_id":          "OMNIX-A3F7C1D92B0E",',
        '  "timestamp":           "2026-04-09T14:23:01.847291+00:00",',
        '  "issued_at_ms":        1744208581847,',
        '  "ttl_epoch_ms":        1744208611847,',
        '  "ttl_ms":              30000,',
        "",
        '  "asset":               "BTC/USDT",',
        '  "decision":            "BLOCK",',
        "",
        '  "veto_chain": [',
        '    "AML: PASS — volume_score=12.4 frequency_score=0.3",',
        '    "FRAUD: PASS — sentiment_score=0.12 reversal_risk=0.04",',
        '    "SHARIA: BLOCK — gharar_score=0.81 exceeds threshold 0.35",',
        '    "CAG: SKIPPED (upstream veto)"',
        "  ],",
        "",
        '  "policy_version":      "6.5.4e",',
        '  "engine_version":      "6.5.4e",',
        '  "prev_hash":           "a9f3c1d4e8b2fc71...",',
        '  "signing_provider":    "dilithium3",',
        '  "content_hash":        "3f8e7a2c91bd...",',
        "",
        '  "signature":           "BASE64_PQC_SIGNATURE==",',
        '  "signature_algorithm": "Dilithium-3 (ML-DSA-65)",',
        '  "signature_format":    "base64_pqc",',
        '  "public_key":          "BASE64_PUBLIC_KEY==",',
        "",
        "  // Conditional — only present if gate was evaluated:",
        '  "sharia_compliance":       { ... },',
        '  "aml_compliance":          { ... },',
        '  "fraud_compliance":        { ... },',
        '  "jurisdiction_compliance": { ... },',
        '  "context_admission":       { ... },',
        '  "veto_type":               "SHARIA_BLOCK",',
        '  "avm_result":              { ... }',
        "}",
    ], story)

    # ── SECTION 3: IDENTITY + TIMING ─────────────────────────────────────────────
    section_header("3.  Identity Fields  (always present)", story, None)

    field_table([
        ["receipt_id",   "string",
         "Globally unique receipt identifier. Format: OMNIX-{12 hex chars uppercase}. "
         "Example: OMNIX-A3F7C1D92B0E"],
        ["timestamp",    "string",
         "ISO-8601 UTC timestamp of receipt generation. "
         "Example: 2026-04-09T14:23:01.847291+00:00"],
    ], story)

    section_header("4.  Timing Fields — T=0 Gateway Critical  (always present from v6.5.4e)", story, None)

    alert_box(
        "These three fields are the primary mechanism for Velos T=0 enforcement. "
        "They are part of the signed payload (included in content_hash). "
        "A receipt is expired when:  now_ms > ttl_epoch_ms",
        story, bg=BLUE_DIM, border=BLUE, text_color=GOLD_LIGHT
    )

    field_table([
        ["issued_at_ms", "integer",
         "Unix epoch milliseconds when the receipt was generated. Derived from timestamp. "
         "This is the canonical T=0 reference point for the decision."],
        ["ttl_epoch_ms", "integer",
         "Unix epoch milliseconds when the receipt expires. "
         "ttl_epoch_ms = issued_at_ms + ttl_ms. "
         "Velos MUST reject any receipt where now_ms > ttl_epoch_ms."],
        ["ttl_ms",       "integer",
         "Time-to-live in milliseconds. Default: 30000 (30 seconds). "
         "Configurable on OMNIX side via OMNIX_RECEIPT_TTL_MS environment variable."],
    ], story)

    body("Velos T=0 ingestion rule:", story, color=GOLD)
    mono_block([
        "now_ms = int(time.time() * 1000)",
        "if now_ms > receipt['ttl_epoch_ms']:",
        "    return {'status': 'REJECTED', 'reason': 'RECEIPT_EXPIRED'}",
    ], story)

    # ── SECTION 5: DECISION FIELDS ───────────────────────────────────────────────
    section_header("5.  Decision Fields  (always present)", story, None)

    field_table([
        ["asset",      "string",
         "Asset symbol. Examples: BTC/USDT, ETH/USD, UNKNOWN"],
        ["decision",   "string",
         "Final governance decision, uppercased. Values: BLOCK | ALLOW | PASS | UNKNOWN. "
         "BLOCK means OMNIX has vetoed the action — Velos must not proceed."],
        ["veto_chain", "array[string]",
         "Ordered list of gate verdicts. Each entry format: 'GATE_NAME: RESULT — detail'. "
         "Maximum 80 characters per entry. Empty array if no trace available."],
    ], story)

    # ── SECTION 6: VERSIONING ────────────────────────────────────────────────────
    section_header("6.  Versioning Fields  (always present)", story, None)

    field_table([
        ["policy_version", "string",
         "Policy version that evaluated this decision. Usually matches engine_version."],
        ["engine_version", "string",
         "OMNIX engine version. Current production version: 6.5.4e"],
        ["prev_hash",      "string",
         "SHA-256 content_hash of the immediately preceding receipt in the chain. "
         "Empty string for the first receipt. Forms the tamper-evident chain."],
    ], story)

    story.append(PageBreak())

    # ── SECTION 7: CRYPTOGRAPHIC FIELDS ──────────────────────────────────────────
    section_header("7.  Cryptographic Fields  (always present)", story, None)

    field_table([
        ["signing_provider",   "string",
         "Identifier of the active signing algorithm. Values: dilithium3 | dilithium5 | "
         "ed25519 | sha256. Bound into the signed payload — prevents algorithm confusion "
         "and downgrade attacks. Velos MUST dispatch verification based on this field."],
        ["content_hash",       "string",
         "SHA-256 hex digest of the canonical JSON of all mandatory + present conditional fields, "
         "serialized with sort_keys=True, ensure_ascii=True. This is what gets signed."],
        ["signature",          "string|null",
         "Detached digital signature over content_hash.encode('utf-8'). "
         "Encoding depends on signature_format — see Section 8."],
        ["signature_algorithm","string",
         "Human-readable algorithm name. Examples: Dilithium-3 (ML-DSA-65), SHA-256, NONE."],
        ["signature_format",   "string",
         "Critical for Velos ingestion. Disambiguates the encoding of the signature field. "
         "See Section 8 for all possible values and how to handle each."],
        ["public_key",         "string|null",
         "Base64-encoded public key for asymmetric signature verification. "
         "null in SHA-256 fallback mode (signature_format = hex_sha256_fallback)."],
    ], story)

    # ── SECTION 8: SIGNATURE FORMAT ──────────────────────────────────────────────
    section_header("8.  signature_format — Dispatch Table", story, None)

    body("This field is the key switch for how Velos must process the signature. "
         "Never assume — always read signature_format first.", story, color=WHITE)
    story.append(Spacer(1, 0.06 * inch))

    fmt_header = [
        Paragraph("Value", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Meaning", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Verification", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
    ]
    fmt_rows = [
        [
            Paragraph("base64_pqc",
                      S('v', fontSize=8, textColor=MONO_GREEN, fontName='Courier')),
            Paragraph("signature is Base64-encoded raw PQC signature bytes.",
                      S('v', fontSize=8, textColor=WHITE, fontName='Helvetica', leading=12)),
            Paragraph("base64.b64decode(signature) → verify with Dilithium/ML-DSA using public_key",
                      S('v', fontSize=8, textColor=LIGHT_GRAY, fontName='Helvetica', leading=12)),
        ],
        [
            Paragraph("hex_sha256_fallback",
                      S('v', fontSize=8, textColor=ORANGE, fontName='Courier')),
            Paragraph("signature is hex of SHA-256(content_hash). Symmetric. No asymmetric signing. "
                      "public_key will be null.",
                      S('v', fontSize=8, textColor=WHITE, fontName='Helvetica', leading=12)),
            Paragraph("sha256(content_hash.encode()).hexdigest() == signature",
                      S('v', fontSize=8, textColor=LIGHT_GRAY, fontName='Helvetica', leading=12)),
        ],
        [
            Paragraph("NONE",
                      S('v', fontSize=8, textColor=RED_ALERT, fontName='Courier')),
            Paragraph("Signing failed. Receipt has no integrity guarantee.",
                      S('v', fontSize=8, textColor=WHITE, fontName='Helvetica', leading=12)),
            Paragraph("REJECT this receipt unconditionally.",
                      S('v', fontSize=8, textColor=RED_ALERT, fontName='Helvetica-Bold', leading=12)),
        ],
    ]
    fmt_data = [fmt_header] + fmt_rows
    fmt_tbl = Table(fmt_data, colWidths=[1.6 * inch, 2.8 * inch, 2.6 * inch])
    fmt_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  CARD_BG),
        ('BACKGROUND',    (0, 1), (-1, 1),  DARK_MID),
        ('BACKGROUND',    (0, 2), (-1, 2),  HexColor('#111827')),
        ('BACKGROUND',    (0, 3), (-1, 3),  HexColor('#1a0000')),
        ('GRID',          (0, 0), (-1, -1), 0.3, MED_GRAY),
        ('BOX',           (0, 0), (-1, -1), 0.8, GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 9),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 9),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(fmt_tbl)
    story.append(Spacer(1, 0.12 * inch))

    # ── SECTION 9: CONDITIONAL BLOCKS ────────────────────────────────────────────
    section_header("9.  Conditional Governance Blocks", story, None)

    body("These blocks appear only when the corresponding gate was evaluated for the decision. "
         "Structure varies by domain and gate version.", story)

    cond_header = [
        Paragraph("Field", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Present when", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
    ]
    cond_rows = [
        ["sharia_compliance",       "Islamic finance gate was evaluated"],
        ["aml_compliance",          "AML gate was evaluated"],
        ["fraud_compliance",        "Fraud gate was evaluated"],
        ["jurisdiction_compliance", "Jurisdiction gate was evaluated"],
        ["context_admission",       "CAG (Context Admission Gate) was evaluated"],
        ["veto_type",               "context_admission is present and contains a veto_type string"],
        ["avm_result",              "AVM (Assumption Validity Monitor) was evaluated"],
    ]
    cond_data = [cond_header] + [
        [
            Paragraph(r[0], S('c', fontSize=8, textColor=MONO_GREEN, fontName='Courier')),
            Paragraph(r[1], S('c', fontSize=8, textColor=WHITE, fontName='Helvetica', leading=12)),
        ]
        for r in cond_rows
    ]
    cond_tbl = Table(cond_data, colWidths=[2.4 * inch, 4.6 * inch])
    cond_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  CARD_BG),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [DARK_MID, HexColor('#111827')]),
        ('GRID',          (0, 0), (-1, -1), 0.3, MED_GRAY),
        ('BOX',           (0, 0), (-1, -1), 0.8, GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 9),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 9),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(cond_tbl)
    story.append(Spacer(1, 0.1 * inch))

    body("avm_result sub-schema:", story, color=GOLD)
    mono_block([
        "{",
        '  "is_valid":          true,',
        '  "snapshot_id":       "snap-abc123",',
        '  "parameter_version": "v3.1",',
        '  "drift_score":       0.12,',
        '  "age_hours":         2.4,',
        '  "pass_through":      false,',
        '  "block_reason":      "DRIFT_EXCEEDED"   // only if AVM blocked',
        "}",
    ], story)

    story.append(PageBreak())

    # ── SECTION 10: CONTENT_HASH CONTRACT ────────────────────────────────────────
    section_header("10.  content_hash Contract — What Gets Hashed", story, None)

    body("The content_hash is computed before signing:", story, color=WHITE)
    mono_block([
        "canonical     = json.dumps(payload_fields, sort_keys=True, ensure_ascii=True)",
        "content_hash  = sha256(canonical.encode('utf-8')).hexdigest()",
    ], story)

    cols_w = [3.4 * inch, 3.6 * inch]
    hash_left = [
        Paragraph("Mandatory fields in hash:", S('hl', fontSize=8.5, textColor=GOLD,
                                                  fontName='Helvetica-Bold', spaceAfter=6)),
        Paragraph("asset", S('hf', fontSize=8, textColor=MONO_GREEN, fontName='Courier', spaceAfter=3)),
        Paragraph("decision", S('hf', fontSize=8, textColor=MONO_GREEN, fontName='Courier', spaceAfter=3)),
        Paragraph("engine_version", S('hf', fontSize=8, textColor=MONO_GREEN, fontName='Courier', spaceAfter=3)),
        Paragraph("issued_at_ms   (new v6.5.4e)", S('hf', fontSize=8, textColor=GREEN_OK,
                                                     fontName='Courier', spaceAfter=3)),
        Paragraph("policy_version", S('hf', fontSize=8, textColor=MONO_GREEN, fontName='Courier', spaceAfter=3)),
        Paragraph("prev_hash", S('hf', fontSize=8, textColor=MONO_GREEN, fontName='Courier', spaceAfter=3)),
        Paragraph("receipt_id", S('hf', fontSize=8, textColor=MONO_GREEN, fontName='Courier', spaceAfter=3)),
        Paragraph("signing_provider", S('hf', fontSize=8, textColor=MONO_GREEN, fontName='Courier', spaceAfter=3)),
        Paragraph("timestamp", S('hf', fontSize=8, textColor=MONO_GREEN, fontName='Courier', spaceAfter=3)),
        Paragraph("ttl_epoch_ms   (new v6.5.4e)", S('hf', fontSize=8, textColor=GREEN_OK,
                                                     fontName='Courier', spaceAfter=3)),
        Paragraph("ttl_ms         (new v6.5.4e)", S('hf', fontSize=8, textColor=GREEN_OK,
                                                     fontName='Courier', spaceAfter=3)),
        Paragraph("veto_chain", S('hf', fontSize=8, textColor=MONO_GREEN, fontName='Courier', spaceAfter=3)),
    ]
    hash_right = [
        Paragraph("Conditional (if present):", S('hl', fontSize=8.5, textColor=GOLD,
                                                  fontName='Helvetica-Bold', spaceAfter=6)),
        Paragraph("aml_compliance", S('hf', fontSize=8, textColor=LIGHT_GRAY, fontName='Courier', spaceAfter=3)),
        Paragraph("avm_result", S('hf', fontSize=8, textColor=LIGHT_GRAY, fontName='Courier', spaceAfter=3)),
        Paragraph("context_admission", S('hf', fontSize=8, textColor=LIGHT_GRAY, fontName='Courier', spaceAfter=3)),
        Paragraph("fraud_compliance", S('hf', fontSize=8, textColor=LIGHT_GRAY, fontName='Courier', spaceAfter=3)),
        Paragraph("jurisdiction_compliance", S('hf', fontSize=8, textColor=LIGHT_GRAY, fontName='Courier', spaceAfter=3)),
        Paragraph("sharia_compliance", S('hf', fontSize=8, textColor=LIGHT_GRAY, fontName='Courier', spaceAfter=3)),
        Paragraph("veto_type", S('hf', fontSize=8, textColor=LIGHT_GRAY, fontName='Courier', spaceAfter=3)),
        Spacer(1, 0.1 * inch),
        Paragraph("NOT included in hash:", S('hl', fontSize=8.5, textColor=RED_ALERT,
                                              fontName='Helvetica-Bold', spaceAfter=6)),
        Paragraph("content_hash  (itself)", S('hf', fontSize=8, textColor=RED_ALERT, fontName='Courier', spaceAfter=3)),
        Paragraph("signature", S('hf', fontSize=8, textColor=RED_ALERT, fontName='Courier', spaceAfter=3)),
        Paragraph("signature_algorithm", S('hf', fontSize=8, textColor=RED_ALERT, fontName='Courier', spaceAfter=3)),
        Paragraph("signature_format", S('hf', fontSize=8, textColor=RED_ALERT, fontName='Courier', spaceAfter=3)),
        Paragraph("public_key", S('hf', fontSize=8, textColor=RED_ALERT, fontName='Courier', spaceAfter=3)),
    ]

    max_rows = max(len(hash_left), len(hash_right))
    while len(hash_left) < max_rows:
        hash_left.append(Spacer(1, 1))
    while len(hash_right) < max_rows:
        hash_right.append(Spacer(1, 1))

    hash_tbl_data = [[hash_left, hash_right]]
    hash_tbl = Table(hash_tbl_data, colWidths=cols_w)
    hash_tbl.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (0, 0), DARK_MID),
        ('BACKGROUND',  (1, 0), (1, 0), HexColor('#111827')),
        ('BOX',         (0, 0), (-1, -1), 0.8, GOLD),
        ('LINEAFTER',   (0, 0), (0, -1), 0.5, MED_GRAY),
        ('TOPPADDING',  (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',(0, 0), (-1, -1), 12),
        ('VALIGN',      (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(hash_tbl)
    story.append(Spacer(1, 0.12 * inch))

    # ── SECTION 11: VERIFICATION ALGORITHM ───────────────────────────────────────
    section_header("11.  Full Verification Algorithm for Velos", story, None)

    body("Drop this function directly into the Velos interceptor. No external dependencies "
         "beyond pypqc (pip install pypqc).", story)

    mono_block([
        "import json, hashlib, base64, time",
        "",
        "def verify_omnix_receipt(receipt: dict) -> dict:",
        "    result = {'receipt_id': receipt.get('receipt_id'), 'valid': False, 'reason': None}",
        "",
        "    # Step 1 — TTL check",
        "    ttl_epoch_ms = receipt.get('ttl_epoch_ms')",
        "    if ttl_epoch_ms is not None:",
        "        now_ms = int(time.time() * 1000)",
        "        if now_ms > ttl_epoch_ms:",
        "            result['reason'] = 'RECEIPT_EXPIRED'",
        "            return result",
        "",
        "    # Step 2 — Reconstruct payload for hashing",
        "    MANDATORY = ['receipt_id', 'timestamp', 'issued_at_ms', 'ttl_epoch_ms', 'ttl_ms',",
        "                 'asset', 'decision', 'veto_chain',",
        "                 'policy_version', 'engine_version', 'prev_hash', 'signing_provider']",
        "    CONDITIONAL = ['sharia_compliance', 'aml_compliance', 'fraud_compliance',",
        "                   'jurisdiction_compliance', 'context_admission', 'veto_type', 'avm_result']",
        "",
        "    payload = {k: receipt[k] for k in MANDATORY if k in receipt}",
        "    if payload.get('signing_provider') is None:",
        "        payload.pop('signing_provider', None)",
        "    for k in CONDITIONAL:",
        "        if k in receipt:",
        "            payload[k] = receipt[k]",
        "",
        "    # Step 3 — Verify content_hash",
        "    canonical     = json.dumps(payload, sort_keys=True, ensure_ascii=True)",
        "    computed_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()",
        "    if computed_hash != receipt.get('content_hash'):",
        "        result['reason'] = 'HASH_MISMATCH'",
        "        return result",
        "",
        "    # Step 4 — Verify signature based on signature_format",
        "    sig_format = receipt.get('signature_format', 'UNKNOWN')",
        "    signature  = receipt.get('signature')",
        "    public_key = receipt.get('public_key')",
        "    message    = receipt['content_hash'].encode('utf-8')",
        "",
        "    if sig_format == 'base64_pqc':",
        "        provider = receipt.get('signing_provider', 'dilithium3')",
        "        if provider == 'dilithium3':",
        "            from pqc.sign import dilithium3",
        "            try:",
        "                dilithium3.verify(base64.b64decode(signature), message,",
        "                                  base64.b64decode(public_key))",
        "                result['valid'] = True",
        "            except Exception:",
        "                result['reason'] = 'SIGNATURE_INVALID'",
        "        elif provider == 'dilithium5':",
        "            from pqc.sign import dilithium5",
        "            try:",
        "                dilithium5.verify(base64.b64decode(signature), message,",
        "                                  base64.b64decode(public_key))",
        "                result['valid'] = True",
        "            except Exception:",
        "                result['reason'] = 'SIGNATURE_INVALID'",
        "",
        "    elif sig_format == 'hex_sha256_fallback':",
        "        expected        = hashlib.sha256(receipt['content_hash'].encode()).hexdigest()",
        "        result['valid'] = (expected == signature)",
        "        if not result['valid']:",
        "            result['reason'] = 'FALLBACK_HASH_MISMATCH'",
        "",
        "    else:",
        "        result['reason'] = f'UNKNOWN_SIGNATURE_FORMAT:{sig_format}'",
        "",
        "    return result",
    ], story)

    story.append(PageBreak())

    # ── SECTION 12: ASSURANCE TIERS ──────────────────────────────────────────────
    section_header("12.  Cryptographic Assurance Tiers", story, None)

    tier_header = [
        Paragraph("Tier", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Provider ID", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Algorithm", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Standard", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Security", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("PK Size", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Sig Size", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
    ]
    tier_rows_data = [
        ["Enterprise Baseline (default)", "dilithium3", "Dilithium-3 (ML-DSA-65)",
         "FIPS 204", "~192-bit", "1952 B", "~3309 B"],
        ["High-Assurance", "dilithium5", "Dilithium-5 (ML-DSA-87)",
         "FIPS 204", "~256-bit", "2592 B", "~4627 B"],
        ["Dev/Test Fallback", "ed25519", "Ed25519 (classical)",
         "—", "128-bit", "32 B", "64 B"],
        ["No PQC Available", "sha256", "SHA-256 (symmetric fallback)",
         "—", "N/A", "N/A", "64 hex"],
    ]
    tier_colors = [GREEN_DIM, BLUE_DIM, HexColor('#1a1a00'), HexColor('#1a0000')]
    tier_data = [tier_header]
    for i, r in enumerate(tier_rows_data):
        tier_data.append([
            Paragraph(r[0], S('t', fontSize=7.5, textColor=WHITE, fontName='Helvetica-Bold')),
            Paragraph(r[1], S('t', fontSize=7.5, textColor=MONO_GREEN, fontName='Courier')),
            Paragraph(r[2], S('t', fontSize=7.5, textColor=GOLD_LIGHT, fontName='Helvetica')),
            Paragraph(r[3], S('t', fontSize=7.5, textColor=LIGHT_GRAY, fontName='Helvetica')),
            Paragraph(r[4], S('t', fontSize=7.5, textColor=WHITE, fontName='Helvetica')),
            Paragraph(r[5], S('t', fontSize=7.5, textColor=LIGHT_GRAY, fontName='Helvetica')),
            Paragraph(r[6], S('t', fontSize=7.5, textColor=LIGHT_GRAY, fontName='Helvetica')),
        ])

    tier_tbl = Table(tier_data, colWidths=[1.5*inch, 0.9*inch, 1.5*inch, 0.65*inch,
                                            0.7*inch, 0.6*inch, 0.65*inch])
    style_cmds = [
        ('BACKGROUND',    (0, 0), (-1, 0),  CARD_BG),
        ('GRID',          (0, 0), (-1, -1), 0.3, MED_GRAY),
        ('BOX',           (0, 0), (-1, -1), 0.8, GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 7),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]
    for i, bg in enumerate(tier_colors):
        style_cmds.append(('BACKGROUND', (0, i + 1), (-1, i + 1), bg))
    tier_tbl.setStyle(TableStyle(style_cmds))
    story.append(tier_tbl)
    story.append(Spacer(1, 0.08 * inch))

    body("Tier is set on OMNIX side via PQC_SIGNING_LEVEL env var (3 or 5). "
         "Velos MUST dispatch verification based on the signing_provider field "
         "embedded in the receipt — do not hardcode a provider.", story, color=LIGHT_GRAY, size=8)

    # ── SECTION 13: RECEIPT CHAINING ─────────────────────────────────────────────
    section_header("13.  Receipt Chaining — Tamper-Evident Audit Trail", story, None)

    body("Each receipt carries prev_hash = content_hash of the immediately preceding receipt:", story)
    mono_block(["Receipt[n].prev_hash  ==  Receipt[n-1].content_hash"], story)

    body("A chain break indicates:", story, color=GOLD)
    bullet("A receipt was injected out of order", story)
    bullet("A receipt was tampered with", story)
    bullet("Chain was restarted — first receipt always has prev_hash = \"\"", story)

    story.append(Spacer(1, 0.14 * inch))

    # ── SECTION 14: INTEGRATION CHECKLIST ────────────────────────────────────────
    section_header("14.  Integration Checklist — Velos T=0 Gateway", story, None)

    checklist = [
        ("Extract ttl_epoch_ms",        "Reject if now_ms > ttl_epoch_ms"),
        ("Extract signature_format",     "Dispatch verification accordingly. DO NOT assume base64."),
        ("Extract signing_provider",     "Determines which PQC algorithm to use for verification."),
        ("Install pypqc",                "pip install pypqc on Velos side."),
        ("Verify content_hash",          "Recompute from payload. Exclude: signature, public_key, "
                                         "signature_format, signature_algorithm, content_hash itself."),
        ("Check decision field",         "BLOCK = OMNIX has vetoed. Velos must not proceed."),
        ("Read veto_chain",              "Identify which specific gate(s) triggered the block."),
        ("Reject signature_format NONE", "Treat as invalid receipt — no integrity guarantee."),
    ]

    chk_header = [
        Paragraph("#", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Action", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Rule", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
    ]
    chk_data = [chk_header]
    for i, (action, rule) in enumerate(checklist, 1):
        chk_data.append([
            Paragraph(str(i), S('n', fontSize=8, textColor=GOLD_LIGHT, fontName='Helvetica-Bold')),
            Paragraph(action, S('a', fontSize=8, textColor=MONO_GREEN, fontName='Courier')),
            Paragraph(rule, S('r', fontSize=8, textColor=WHITE, fontName='Helvetica', leading=12)),
        ])
    chk_tbl = Table(chk_data, colWidths=[0.3 * inch, 1.9 * inch, 4.8 * inch])
    chk_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  CARD_BG),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [DARK_MID, HexColor('#111827')]),
        ('GRID',          (0, 0), (-1, -1), 0.3, MED_GRAY),
        ('BOX',           (0, 0), (-1, -1), 0.8, GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(chk_tbl)
    story.append(Spacer(1, 0.16 * inch))

    # ── SECTION 15: EXAMPLE BLOCK RECEIPT ────────────────────────────────────────
    section_header("15.  Example — Full BLOCK Receipt (Trading Domain)", story, None)

    mono_block([
        "{",
        '  "receipt_id":          "OMNIX-A3F7C1D92B0E",',
        '  "timestamp":           "2026-04-09T14:23:01.847291+00:00",',
        '  "issued_at_ms":        1744208581847,',
        '  "ttl_epoch_ms":        1744208611847,',
        '  "ttl_ms":              30000,',
        '  "asset":               "BTC/USDT",',
        '  "decision":            "BLOCK",',
        '  "veto_chain": [',
        '    "AML: PASS -- volume_score=12.4 frequency_score=0.3",',
        '    "FRAUD: PASS -- sentiment_score=0.12 reversal_risk=0.04",',
        '    "SHARIA: BLOCK -- gharar_score=0.81 exceeds threshold 0.35",',
        '    "CAG: SKIPPED (upstream veto)"',
        "  ],",
        '  "policy_version":      "6.5.4e",',
        '  "engine_version":      "6.5.4e",',
        '  "prev_hash":           "a9f3c1d4e8b2fc71...",',
        '  "signing_provider":    "dilithium3",',
        '  "sharia_compliance": {',
        '    "admitted":          false,',
        '    "evaluation_state":  "EVALUATED",',
        '    "violation":         "GHARAR_EXCESSIVE",',
        '    "gharar_score":      0.81,',
        '    "debt_ratio":        0.0',
        "  },",
        '  "content_hash":        "3f8e7a2c91bd...",',
        '  "signature":           "BASE64_DILITHIUM3_SIGNATURE==",',
        '  "signature_algorithm": "Dilithium-3 (ML-DSA-65)",',
        '  "signature_format":    "base64_pqc",',
        '  "public_key":          "BASE64_PUBLIC_KEY=="',
        "}",
    ], story)

    story.append(Spacer(1, 0.16 * inch))

    # ── SECTION 16: BACKWARD COMPATIBILITY ───────────────────────────────────────
    section_header("16.  Backward Compatibility", story, None)

    compat_rows = [
        ["Schema v6.5.4e (this document)", "2026-04-09",
         "Added issued_at_ms, ttl_epoch_ms, ttl_ms, signature_format. "
         "Verifier now checks TTL expiry and exposes is_expired, age_ms."],
        ["Pre-v6.5.4e (legacy)", "—",
         "timestamp only. No TTL fields. signature_format absent. "
         "Assume base64_pqc if public_key present, else hex_sha256_fallback."],
    ]
    compat_header = [
        Paragraph("Schema Version", S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Released",       S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
        Paragraph("Changes",        S('h', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold')),
    ]
    compat_data = [compat_header] + [
        [
            Paragraph(r[0], S('c', fontSize=8, textColor=GOLD_LIGHT, fontName='Helvetica-Bold')),
            Paragraph(r[1], S('c', fontSize=8, textColor=LIGHT_GRAY, fontName='Helvetica')),
            Paragraph(r[2], S('c', fontSize=8, textColor=WHITE, fontName='Helvetica', leading=12)),
        ]
        for r in compat_rows
    ]
    compat_tbl = Table(compat_data, colWidths=[1.6 * inch, 0.8 * inch, 4.6 * inch])
    compat_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  CARD_BG),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [DARK_MID, HexColor('#111827')]),
        ('GRID',          (0, 0), (-1, -1), 0.3, MED_GRAY),
        ('BOX',           (0, 0), (-1, -1), 0.8, GOLD),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 9),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 9),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(compat_tbl)
    story.append(Spacer(1, 0.24 * inch))

    # ── FOOTER ───────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.8, color=GOLD))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "Document prepared by Harold Nunes — OMNIX QUANTUM LTD",
        S('f', fontSize=8, textColor=GOLD, fontName='Helvetica-Bold', alignment=TA_CENTER)
    ))
    story.append(Paragraph(
        "Eureka GCC Dubai 2026 Semifinalist  |  Recaudando $500K pre-seed @ $3M valuation",
        S('f', fontSize=7.5, textColor=LIGHT_GRAY, fontName='Helvetica', alignment=TA_CENTER)
    ))
    story.append(Paragraph(
        "OMNIX QUANTUM LTD — United Kingdom  |  omnixquantum.com",
        S('f', fontSize=7.5, textColor=MED_GRAY, fontName='Helvetica', alignment=TA_CENTER)
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    build_pdf()
