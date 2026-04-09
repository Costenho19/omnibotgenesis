"""
OMNIX — Post-Quantum Mandate Receipt Schema Specification
Integration Document for Velos / Naimat Khan — Compact 3-page edition
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
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
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
ALT_ROW    = HexColor('#111827')


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
            self.setFont("Helvetica", 6.5)
            self.setFillColor(LIGHT_GRAY)
            self.drawCentredString(
                A4[0] / 2, 0.28 * inch,
                f"OMNIX Decision Governance Infrastructure  —  PQC Receipt Schema v6.5.4e  —  "
                f"Confidential / Velos Integration  —  Page {self._pageNumber} of {num_pages}"
            )
            self.setStrokeColor(GOLD)
            self.setLineWidth(0.4)
            self.line(0.7 * inch, 0.48 * inch, A4[0] - 0.7 * inch, 0.48 * inch)
            pdf_canvas.Canvas.showPage(self)
        pdf_canvas.Canvas.save(self)


def S(name, **kw):
    return ParagraphStyle(name, **kw)


def sec(title, story):
    tbl = Table(
        [[Paragraph(title, S('sh', fontSize=9, textColor=GOLD,
                             fontName='Helvetica-Bold'))]],
        colWidths=[7.06 * inch]
    )
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), CARD_BG),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LINEBELOW',     (0,0), (-1,-1), 1.2, GOLD),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.06 * inch))


def code(lines, story, color=MONO_GREEN):
    rows = [[Paragraph(l, S('c', fontSize=6.8, textColor=color,
                            fontName='Courier', leading=10))] for l in lines]
    tbl = Table(rows, colWidths=[7.06 * inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), DARK_MID),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 10),
        ('TOPPADDING',    (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('BOX',           (0,0), (-1,-1), 0.4, MED_GRAY),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.06 * inch))


def ftable(rows, story, widths=None):
    if widths is None:
        widths = [1.55*inch, 0.75*inch, 4.76*inch]
    hdr = [
        Paragraph(h, S('h', fontSize=7.5, textColor=GOLD, fontName='Helvetica-Bold'))
        for h in ("Field", "Type", "Description")
    ]
    data = [hdr] + [
        [
            Paragraph(r[0], S('f', fontSize=7, textColor=MONO_GREEN, fontName='Courier')),
            Paragraph(r[1], S('t', fontSize=7, textColor=LIGHT_GRAY, fontName='Helvetica-Oblique')),
            Paragraph(r[2], S('d', fontSize=7, textColor=WHITE, fontName='Helvetica', leading=10)),
        ]
        for r in rows
    ]
    tbl = Table(data, colWidths=widths)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',     (0,0), (-1,0),  CARD_BG),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [DARK_MID, ALT_ROW]),
        ('GRID',           (0,0), (-1,-1), 0.25, MED_GRAY),
        ('BOX',            (0,0), (-1,-1), 0.7,  GOLD),
        ('TOPPADDING',     (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',  (0,0), (-1,-1), 4),
        ('LEFTPADDING',    (0,0), (-1,-1), 6),
        ('RIGHTPADDING',   (0,0), (-1,-1), 6),
        ('VALIGN',         (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.07 * inch))


def build_pdf():
    output_path = "docs/integration/OMNIX_Velos_Schema_PQC_Receipt.pdf"
    os.makedirs("docs/integration", exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=0.7*inch, rightMargin=0.7*inch,
        topMargin=0.55*inch, bottomMargin=0.65*inch,
    )
    story = []

    # ══════════════════════════════════════════════════════════
    # PAGE 1 — COVER
    # ══════════════════════════════════════════════════════════
    story.append(Spacer(1, 0.15*inch))

    logo_path = "docs/omnix_quantum_logo.png"
    if os.path.exists(logo_path):
        logo_tbl = Table([[Image(logo_path, 1.3*inch, 1.3*inch)]], colWidths=[7.06*inch])
        logo_tbl.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER')]))
        story.append(logo_tbl)
        story.append(Spacer(1, 0.14*inch))

    # Title box
    title_tbl = Table(
        [[Paragraph("OMNIX", S('t', fontSize=30, textColor=GOLD,
                               fontName='Helvetica-Bold', alignment=TA_CENTER))]],
        colWidths=[7.06*inch]
    )
    title_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), DARK_MID),
        ('BOX',           (0,0),(-1,-1), 2, GOLD),
        ('TOPPADDING',    (0,0),(-1,-1), 14),
        ('BOTTOMPADDING', (0,0),(-1,-1), 14),
    ]))
    story.append(title_tbl)
    story.append(Spacer(1, 0.08*inch))
    story.append(Paragraph("Decision Governance Infrastructure",
                            S('s', fontSize=10, textColor=LIGHT_GRAY,
                              fontName='Helvetica', alignment=TA_CENTER)))
    story.append(Spacer(1, 0.16*inch))
    story.append(HRFlowable(width="100%", thickness=1.2, color=GOLD))
    story.append(Spacer(1, 0.12*inch))
    story.append(Paragraph("POST-QUANTUM MANDATE RECEIPT — SCHEMA SPECIFICATION",
                            S('dt', fontSize=14, textColor=WHITE,
                              fontName='Helvetica-Bold', alignment=TA_CENTER)))
    story.append(Spacer(1, 0.05*inch))
    story.append(Paragraph("Velos Integration Document  |  Schema v6.5.4e  |  T=0 Gateway Edition",
                            S('ds', fontSize=8.5, textColor=GOLD_LIGHT,
                              fontName='Helvetica', alignment=TA_CENTER)))
    story.append(Spacer(1, 0.2*inch))
    story.append(HRFlowable(width="100%", thickness=0.4, color=MED_GRAY))
    story.append(Spacer(1, 0.16*inch))

    meta = [
        ["For",              "Naimat Khan — Velos"],
        ["Prepared by",      "Harold Nunes — OMNIX QUANTUM LTD"],
        ["Date",             today],
        ["Classification",   "Confidential — Partner Integration Material"],
        ["Schema Version",   "v6.5.4e"],
        ["Signing Standard", "NIST FIPS 204 — ML-DSA (Dilithium-3 / Dilithium-5)"],
        ["KEM Standard",     "NIST FIPS 203 — ML-KEM (Kyber-768)"],
        ["Endpoint",         "POST https://velos-gateway.onrender.com/api/v1/intercept"],
    ]
    meta_tbl = Table(meta, colWidths=[1.8*inch, 5.26*inch])
    meta_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(0,-1), CARD_BG),
        ('BACKGROUND',    (1,0),(1,-1), DARK_BG),
        ('TEXTCOLOR',     (0,0),(0,-1), GOLD),
        ('TEXTCOLOR',     (1,0),(1,-1), WHITE),
        ('FONTNAME',      (0,0),(0,-1), 'Helvetica-Bold'),
        ('FONTNAME',      (1,0),(1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,0),(-1,-1), 8),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 9),
        ('GRID',          (0,0),(-1,-1), 0.25, MED_GRAY),
        ('BOX',           (0,0),(-1,-1), 0.8, GOLD),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 0.2*inch))

    key_tbl = Table([[Paragraph(
        "Every OMNIX decision produces a cryptographically signed JSON receipt encoding "
        "the complete governance trail. This document defines the exact schema Velos must "
        "implement to verify receipts at the T=0 interceptor gateway — including TTL enforcement, "
        "hash integrity, and PQC signature dispatch.",
        S('k', fontSize=8, textColor=GOLD_LIGHT, fontName='Helvetica-BoldOblique',
          alignment=TA_CENTER, leading=13)
    )]], colWidths=[7.06*inch])
    key_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), CARD_BG),
        ('BOX',           (0,0),(-1,-1), 1.2, GOLD),
        ('TOPPADDING',    (0,0),(-1,-1), 11),
        ('BOTTOMPADDING', (0,0),(-1,-1), 11),
        ('LEFTPADDING',   (0,0),(-1,-1), 16),
        ('RIGHTPADDING',  (0,0),(-1,-1), 16),
    ]))
    story.append(key_tbl)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # PAGE 2 — FULL JSON + FIELD REFERENCE
    # ══════════════════════════════════════════════════════════
    sec("1.  Complete JSON Schema", story)
    code([
        "{",
        '  "receipt_id":          "OMNIX-A3F7C1D92B0E",',
        '  "timestamp":           "2026-04-09T14:23:01.847291+00:00",',
        '  "issued_at_ms":        1744208581847,       // ← T=0 reference (epoch ms)',
        '  "ttl_epoch_ms":        1744208611847,       // ← expiry (epoch ms). REJECT if now_ms > this',
        '  "ttl_ms":              30000,               // ← default 30 s, configurable',
        '  "asset":               "BTC/USDT",',
        '  "decision":            "BLOCK",             // BLOCK | ALLOW | PASS | UNKNOWN',
        '  "veto_chain":          ["AML: PASS ...", "SHARIA: BLOCK -- gharar=0.81 ..."],',
        '  "policy_version":      "6.5.4e",',
        '  "engine_version":      "6.5.4e",',
        '  "prev_hash":           "a9f3c1d4...",       // SHA-256 of previous receipt (chain)',
        '  "signing_provider":    "dilithium3",        // dilithium3 | dilithium5 | sha256',
        '  "content_hash":        "3f8e7a2c...",       // SHA-256 of canonical payload (signed)',
        '  "signature":           "BASE64==...",       // encoding → see signature_format',
        '  "signature_algorithm": "Dilithium-3 (ML-DSA-65)",',
        '  "signature_format":    "base64_pqc",        // base64_pqc | hex_sha256_fallback | NONE',
        '  "public_key":          "BASE64==...",       // null in fallback mode',
        '  // Conditional — present only when gate was evaluated:',
        '  "sharia_compliance": {...},  "aml_compliance": {...},  "fraud_compliance": {...},',
        '  "jurisdiction_compliance": {...},  "context_admission": {...},  "avm_result": {...}',
        "}",
    ], story)

    sec("2.  Field Reference", story)
    ftable([
        ["receipt_id",         "string",  "Globally unique ID. Format: OMNIX-{12 hex uppercase}"],
        ["timestamp",          "string",  "ISO-8601 UTC generation time"],
        ["issued_at_ms",       "integer", "Unix epoch ms — canonical T=0 reference point"],
        ["ttl_epoch_ms",       "integer", "Expiry in epoch ms. Velos MUST reject if now_ms > ttl_epoch_ms"],
        ["ttl_ms",             "integer", "TTL in ms. Default 30000 (30 s). Set via OMNIX_RECEIPT_TTL_MS"],
        ["asset",              "string",  "Asset symbol. e.g. BTC/USDT, ETH/USD"],
        ["decision",           "string",  "BLOCK | ALLOW | PASS | UNKNOWN  (uppercased)"],
        ["veto_chain",         "array",   "Ordered gate verdicts. Format: 'GATE: RESULT — detail'"],
        ["policy_version",     "string",  "Policy version used for this evaluation"],
        ["engine_version",     "string",  "OMNIX engine version (current: 6.5.4e)"],
        ["prev_hash",          "string",  "SHA-256 of previous receipt — tamper-evident chain. '' if first"],
        ["signing_provider",   "string",  "Active algorithm ID bound into signed payload (anti-downgrade)"],
        ["content_hash",       "string",  "SHA-256 hex of canonical JSON of all signed fields"],
        ["signature",          "str|null","Detached signature over content_hash. Encoding = signature_format"],
        ["signature_algorithm","string",  "Human-readable. e.g. 'Dilithium-3 (ML-DSA-65)', 'SHA-256'"],
        ["signature_format",   "string",  "CRITICAL. base64_pqc → PQC bytes (base64). "
                                          "hex_sha256_fallback → symmetric hex. NONE → reject."],
        ["public_key",         "str|null","Base64 PK for asymmetric verification. null in fallback mode"],
    ], story)

    sec("3.  signature_format Dispatch", story)
    fmt_hdr = [Paragraph(h, S('h', fontSize=7.5, textColor=GOLD, fontName='Helvetica-Bold'))
               for h in ("signature_format", "signature encoding", "How Velos verifies")]
    fmt_rows = [
        [Paragraph("base64_pqc",
                   S('', fontSize=7, textColor=MONO_GREEN, fontName='Courier')),
         Paragraph("Base64-encoded raw PQC bytes",
                   S('', fontSize=7, textColor=WHITE, fontName='Helvetica')),
         Paragraph("base64.decode → Dilithium.verify(sig, content_hash, public_key)",
                   S('', fontSize=7, textColor=LIGHT_GRAY, fontName='Helvetica', leading=10))],
        [Paragraph("hex_sha256_fallback",
                   S('', fontSize=7, textColor=ORANGE, fontName='Courier')),
         Paragraph("Hex of SHA-256(content_hash). Symmetric. public_key = null",
                   S('', fontSize=7, textColor=WHITE, fontName='Helvetica')),
         Paragraph("sha256(content_hash.encode()).hexdigest() == signature",
                   S('', fontSize=7, textColor=LIGHT_GRAY, fontName='Helvetica', leading=10))],
        [Paragraph("NONE",
                   S('', fontSize=7, textColor=RED_ALERT, fontName='Courier')),
         Paragraph("Signing failed — no integrity guarantee",
                   S('', fontSize=7, textColor=WHITE, fontName='Helvetica')),
         Paragraph("REJECT unconditionally",
                   S('', fontSize=7, textColor=RED_ALERT, fontName='Helvetica-Bold'))],
    ]
    fmt_tbl = Table([fmt_hdr]+fmt_rows, colWidths=[1.5*inch, 2.4*inch, 3.16*inch])
    fmt_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  CARD_BG),
        ('BACKGROUND',    (0,1),(-1,1),  DARK_MID),
        ('BACKGROUND',    (0,2),(-1,2),  ALT_ROW),
        ('BACKGROUND',    (0,3),(-1,3),  HexColor('#1a0000')),
        ('GRID',          (0,0),(-1,-1), 0.25, MED_GRAY),
        ('BOX',           (0,0),(-1,-1), 0.7,  GOLD),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 7),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
    ]))
    story.append(fmt_tbl)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # PAGE 3 — VERIFICATION ALGORITHM + TIERS + CHECKLIST
    # ══════════════════════════════════════════════════════════
    sec("4.  Verification Algorithm (drop-in Python)", story)
    code([
        "import json, hashlib, base64, time",
        "",
        "def verify_omnix_receipt(receipt):",
        "    # 1 — TTL",
        "    ttl = receipt.get('ttl_epoch_ms')",
        "    if ttl and int(time.time()*1000) > ttl:",
        "        return {'valid': False, 'reason': 'RECEIPT_EXPIRED'}",
        "",
        "    # 2 — Rebuild payload for hash",
        "    MANDATORY = ['receipt_id','timestamp','issued_at_ms','ttl_epoch_ms','ttl_ms',",
        "                 'asset','decision','veto_chain','policy_version','engine_version',",
        "                 'prev_hash','signing_provider']",
        "    CONDITIONAL = ['sharia_compliance','aml_compliance','fraud_compliance',",
        "                   'jurisdiction_compliance','context_admission','veto_type','avm_result']",
        "    p = {k: receipt[k] for k in MANDATORY if k in receipt}",
        "    for k in CONDITIONAL:",
        "        if k in receipt: p[k] = receipt[k]",
        "",
        "    # 3 — Verify content_hash",
        "    computed = hashlib.sha256(json.dumps(p, sort_keys=True,",
        "                ensure_ascii=True).encode()).hexdigest()",
        "    if computed != receipt.get('content_hash'):",
        "        return {'valid': False, 'reason': 'HASH_MISMATCH'}",
        "",
        "    # 4 — Verify signature",
        "    fmt = receipt.get('signature_format','UNKNOWN')",
        "    sig = receipt.get('signature')",
        "    msg = receipt['content_hash'].encode()",
        "    if fmt == 'base64_pqc':",
        "        prov = receipt.get('signing_provider','dilithium3')",
        "        if prov == 'dilithium3':",
        "            from pqc.sign import dilithium3",
        "            try: dilithium3.verify(base64.b64decode(sig), msg,",
        "                                   base64.b64decode(receipt['public_key']))",
        "            except: return {'valid': False, 'reason': 'SIGNATURE_INVALID'}",
        "        elif prov == 'dilithium5':",
        "            from pqc.sign import dilithium5",
        "            try: dilithium5.verify(base64.b64decode(sig), msg,",
        "                                   base64.b64decode(receipt['public_key']))",
        "            except: return {'valid': False, 'reason': 'SIGNATURE_INVALID'}",
        "    elif fmt == 'hex_sha256_fallback':",
        "        if hashlib.sha256(receipt['content_hash'].encode()).hexdigest() != sig:",
        "            return {'valid': False, 'reason': 'FALLBACK_HASH_MISMATCH'}",
        "    else:",
        "        return {'valid': False, 'reason': f'UNKNOWN_FORMAT:{fmt}'}",
        "    return {'valid': True}",
    ], story)

    sec("5.  Cryptographic Assurance Tiers", story)
    tier_hdr = [Paragraph(h, S('h', fontSize=7.5, textColor=GOLD, fontName='Helvetica-Bold'))
                for h in ("Tier", "signing_provider", "Algorithm", "Standard", "Security", "PK", "Sig")]
    tier_rows = [
        ["Enterprise (default)", "dilithium3", "Dilithium-3 (ML-DSA-65)", "FIPS 204", "~192-bit", "1952 B", "~3309 B"],
        ["High-Assurance",       "dilithium5", "Dilithium-5 (ML-DSA-87)", "FIPS 204", "~256-bit", "2592 B", "~4627 B"],
        ["No PQC Available",     "sha256",     "SHA-256 symmetric fallback", "—",      "N/A",     "N/A",    "64 hex"],
    ]
    tier_bgs = [DARK_MID, ALT_ROW, HexColor('#1a0000')]
    tier_data = [tier_hdr] + [
        [Paragraph(c, S('', fontSize=7, textColor=MONO_GREEN if i==1 else WHITE,
                        fontName='Courier' if i in (0,1) else 'Helvetica'))
         for i, c in enumerate(r)]
        for r in tier_rows
    ]
    tier_tbl = Table(tier_data, colWidths=[1.3*inch,0.85*inch,1.55*inch,0.6*inch,0.6*inch,0.5*inch,0.56*inch])
    style_cmds = [
        ('BACKGROUND',    (0,0),(-1,0),  CARD_BG),
        ('GRID',          (0,0),(-1,-1), 0.25, MED_GRAY),
        ('BOX',           (0,0),(-1,-1), 0.7,  GOLD),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
    ]
    for i, bg in enumerate(tier_bgs):
        style_cmds.append(('BACKGROUND', (0,i+1),(-1,i+1), bg))
    tier_tbl.setStyle(TableStyle(style_cmds))
    story.append(tier_tbl)
    story.append(Spacer(1, 0.08*inch))

    sec("6.  content_hash Contract — What Gets Hashed", story)
    hash_cols = [3.4*inch, 3.66*inch]
    left_items = [
        ("Mandatory (always in hash):", GOLD),
        ("asset, decision, engine_version,", MONO_GREEN),
        ("issued_at_ms, policy_version, prev_hash,", MONO_GREEN),
        ("receipt_id, signing_provider, timestamp,", MONO_GREEN),
        ("ttl_epoch_ms, ttl_ms, veto_chain", MONO_GREEN),
        ("", WHITE),
        ("Conditional (if present):", GOLD),
        ("sharia_compliance, aml_compliance,", LIGHT_GRAY),
        ("fraud_compliance, jurisdiction_compliance,", LIGHT_GRAY),
        ("context_admission, veto_type, avm_result", LIGHT_GRAY),
    ]
    right_items = [
        ("NOT in hash (detached pattern):", RED_ALERT),
        ("content_hash, signature,", RED_ALERT),
        ("signature_algorithm,", RED_ALERT),
        ("signature_format, public_key", RED_ALERT),
    ]
    lp = [Paragraph(t, S('', fontSize=7, textColor=c, fontName='Courier' if c!=GOLD else 'Helvetica-Bold', leading=10)) for t,c in left_items]
    rp = [Paragraph(t, S('', fontSize=7, textColor=c, fontName='Courier' if c!=RED_ALERT else 'Courier', leading=10)) for t,c in right_items]
    while len(rp) < len(lp):
        rp.append(Spacer(1, 1))
    hash_tbl = Table([[lp, rp]], colWidths=hash_cols)
    hash_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(0,0), DARK_MID),
        ('BACKGROUND',    (1,0),(1,0), ALT_ROW),
        ('BOX',           (0,0),(-1,-1), 0.7, GOLD),
        ('LINEAFTER',     (0,0),(0,-1), 0.4, MED_GRAY),
        ('TOPPADDING',    (0,0),(-1,-1), 10),
        ('BOTTOMPADDING', (0,0),(-1,-1), 10),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 10),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
    ]))
    story.append(hash_tbl)
    story.append(Spacer(1, 0.08*inch))

    sec("7.  Integration Checklist", story)
    checklist = [
        ("1", "now_ms > ttl_epoch_ms?",           "Reject immediately with RECEIPT_EXPIRED"),
        ("2", "Read signature_format",             "Never hardcode — dispatch on this field"),
        ("3", "Read signing_provider",             "Determines PQC algorithm for verification"),
        ("4", "pip install pypqc",                 "Required on Velos side for PQC verification"),
        ("5", "Recompute content_hash",            "Exclude: signature, public_key, sig_format, sig_algorithm, content_hash"),
        ("6", "decision == BLOCK?",                "Do not proceed — OMNIX has vetoed the action"),
        ("7", "signature_format == NONE?",         "Reject unconditionally — no integrity guarantee"),
    ]
    chk_hdr = [Paragraph(h, S('h', fontSize=7.5, textColor=GOLD, fontName='Helvetica-Bold'))
               for h in ("#", "Check", "Rule")]
    chk_data = [chk_hdr] + [
        [
            Paragraph(r[0], S('', fontSize=7.5, textColor=GOLD_LIGHT, fontName='Helvetica-Bold')),
            Paragraph(r[1], S('', fontSize=7, textColor=MONO_GREEN, fontName='Courier')),
            Paragraph(r[2], S('', fontSize=7, textColor=WHITE, fontName='Helvetica', leading=10)),
        ]
        for r in checklist
    ]
    chk_tbl = Table(chk_data, colWidths=[0.25*inch, 2.0*inch, 4.81*inch])
    chk_tbl.setStyle(TableStyle([
        ('BACKGROUND',     (0,0),(-1,0),  CARD_BG),
        ('ROWBACKGROUNDS', (0,1),(-1,-1), [DARK_MID, ALT_ROW]),
        ('GRID',           (0,0),(-1,-1), 0.25, MED_GRAY),
        ('BOX',            (0,0),(-1,-1), 0.7,  GOLD),
        ('TOPPADDING',     (0,0),(-1,-1), 4),
        ('BOTTOMPADDING',  (0,0),(-1,-1), 4),
        ('LEFTPADDING',    (0,0),(-1,-1), 6),
        ('VALIGN',         (0,0),(-1,-1), 'TOP'),
    ]))
    story.append(chk_tbl)
    story.append(Spacer(1, 0.14*inch))

    story.append(HRFlowable(width="100%", thickness=0.7, color=GOLD))
    story.append(Spacer(1, 0.07*inch))
    story.append(Paragraph(
        "Harold Nunes — OMNIX QUANTUM LTD  |  Eureka GCC Dubai 2026 Semifinalist  |  "
        "Raising $500K pre-seed @ $3M valuation",
        S('f', fontSize=7, textColor=LIGHT_GRAY, fontName='Helvetica', alignment=TA_CENTER)
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    build_pdf()
