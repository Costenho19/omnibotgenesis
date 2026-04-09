"""
OMNIX — Post-Quantum Mandate Receipt Schema Specification
Velos Integration Document — 3 pages exact
"""
import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas as pdf_canvas

# ── Palette ──────────────────────────────────────────────────────────────────
DARK_BG   = HexColor('#0a0f1a')
DARK_MID  = HexColor('#0f172a')
CARD_BG   = HexColor('#1e293b')
ALT_ROW   = HexColor('#111827')
GOLD      = HexColor('#C9A227')
GOLD_LT   = HexColor('#F5D97A')
GREEN     = HexColor('#10b981')
GREEN_DIM = HexColor('#064e3b')
RED       = HexColor('#ef4444')
RED_DIM   = HexColor('#1a0000')
BLUE_DIM  = HexColor('#1e3a5f')
LGRAY     = HexColor('#94a3b8')
MGRAY     = HexColor('#475569')
WHITE     = HexColor('#ffffff')
MONO      = HexColor('#4ade80')
ORANGE    = HexColor('#f97316')

W = 7.06 * inch   # usable page width


# ── Numbered canvas with dark background ─────────────────────────────────────
class NC(pdf_canvas.Canvas):
    def __init__(self, *args, **kw):
        pdf_canvas.Canvas.__init__(self, *args, **kw)
        self._states = []

    def _startPage(self):
        pdf_canvas.Canvas._startPage(self)
        self.saveState()
        self.setFillColor(DARK_BG)
        self.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        self.restoreState()

    def showPage(self):
        self._states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._states)
        for st in self._states:
            self.__dict__.update(st)
            self.setFont("Helvetica", 6.5)
            self.setFillColor(LGRAY)
            self.drawCentredString(
                A4[0] / 2, 0.26 * inch,
                f"OMNIX Decision Governance Infrastructure  —  PQC Receipt Schema v6.5.4e  —  "
                f"Confidential / Velos  —  Page {self._pageNumber} of {n}"
            )
            self.setStrokeColor(GOLD)
            self.setLineWidth(0.4)
            self.line(0.7*inch, 0.44*inch, A4[0]-0.7*inch, 0.44*inch)
            pdf_canvas.Canvas.showPage(self)
        pdf_canvas.Canvas.save(self)


# ── Helpers ───────────────────────────────────────────────────────────────────
def P(text, **kw):
    return Paragraph(text, ParagraphStyle("_", **kw))


def sec(title, story):
    t = Table([[P(title, fontSize=8.5, textColor=GOLD, fontName='Helvetica-Bold')]], colWidths=[W])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), CARD_BG),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LINEBELOW',     (0,0),(-1,-1), 1.2, GOLD),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.05*inch))


def code_block(lines, story, fg=MONO):
    rows = [[P(l, fontSize=6.2, textColor=fg, fontName='Courier', leading=9)] for l in lines]
    t = Table(rows, colWidths=[W])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), DARK_MID),
        ('LEFTPADDING',   (0,0),(-1,-1), 9),
        ('RIGHTPADDING',  (0,0),(-1,-1), 9),
        ('TOPPADDING',    (0,0),(-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 1.5),
        ('BOX',           (0,0),(-1,-1), 0.4, MGRAY),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.05*inch))


def grid_table(header, rows, widths, story, row_bgs=None):
    if row_bgs is None:
        row_bgs = [DARK_MID, ALT_ROW]
    data = [header] + rows
    t = Table(data, colWidths=widths)
    style = [
        ('BACKGROUND',     (0,0),(-1,0),   CARD_BG),
        ('ROWBACKGROUNDS', (0,1),(-1,-1),  row_bgs),
        ('GRID',           (0,0),(-1,-1),  0.25, MGRAY),
        ('BOX',            (0,0),(-1,-1),  0.7,  GOLD),
        ('TOPPADDING',     (0,0),(-1,-1),  3),
        ('BOTTOMPADDING',  (0,0),(-1,-1),  3),
        ('LEFTPADDING',    (0,0),(-1,-1),  6),
        ('RIGHTPADDING',   (0,0),(-1,-1),  6),
        ('VALIGN',         (0,0),(-1,-1),  'TOP'),
    ]
    t.setStyle(TableStyle(style))
    story.append(t)
    story.append(Spacer(1, 0.06*inch))


def hdr_cells(labels, sizes=None):
    if sizes is None:
        sizes = [7.5] * len(labels)
    return [P(l, fontSize=s, textColor=GOLD, fontName='Helvetica-Bold')
            for l, s in zip(labels, sizes)]


# ══════════════════════════════════════════════════════════════════════════════
def build_pdf():
    out = "docs/integration/OMNIX_Velos_Schema_PQC_Receipt.pdf"
    os.makedirs("docs/integration", exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=0.7*inch, rightMargin=0.7*inch,
        topMargin=0.5*inch, bottomMargin=0.6*inch,
    )
    story = []

    # ══════════════════════════════════════════════════════════
    # PAGE 1 — COVER
    # ══════════════════════════════════════════════════════════
    story.append(Spacer(1, 0.12*inch))

    # Logo (transparent)
    logo = "omnix_web/public/logo_nobg.png"
    if not os.path.exists(logo):
        logo = "docs/omnix_quantum_logo.png"
    if os.path.exists(logo):
        lt = Table([[Image(logo, 1.1*inch, 1.1*inch)]], colWidths=[W])
        lt.setStyle(TableStyle([
            ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
            ('BACKGROUND',    (0,0),(-1,-1), DARK_BG),
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ]))
        story.append(lt)
        story.append(Spacer(1, 0.12*inch))

    # OMNIX title box
    tb = Table([[P("OMNIX", fontSize=28, textColor=GOLD,
                   fontName='Helvetica-Bold', alignment=TA_CENTER)]], colWidths=[W])
    tb.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), DARK_MID),
        ('BOX',           (0,0),(-1,-1), 2, GOLD),
        ('TOPPADDING',    (0,0),(-1,-1), 13),
        ('BOTTOMPADDING', (0,0),(-1,-1), 13),
    ]))
    story.append(tb)
    story.append(Spacer(1, 0.06*inch))
    story.append(P("Decision Governance Infrastructure",
                   fontSize=9.5, textColor=LGRAY, fontName='Helvetica', alignment=TA_CENTER))
    story.append(Spacer(1, 0.14*inch))
    story.append(HRFlowable(width="100%", thickness=1.2, color=GOLD))
    story.append(Spacer(1, 0.1*inch))
    story.append(P("POST-QUANTUM MANDATE RECEIPT — SCHEMA SPECIFICATION",
                   fontSize=13, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_CENTER))
    story.append(Spacer(1, 0.04*inch))
    story.append(P("Velos Integration Document  |  Schema v6.5.4e  |  T=0 Gateway Edition",
                   fontSize=8, textColor=GOLD_LT, fontName='Helvetica', alignment=TA_CENTER))
    story.append(Spacer(1, 0.16*inch))
    story.append(HRFlowable(width="100%", thickness=0.4, color=MGRAY))
    story.append(Spacer(1, 0.14*inch))

    # Metadata table
    meta = [
        ["For",              "Naimat Khan — Velos"],
        ["Prepared by",      "Harold Nunes — OMNIX QUANTUM LTD"],
        ["Date",             today],
        ["Classification",   "Confidential — Partner Integration Material"],
        ["Schema Version",   "v6.5.4e  (adds issued_at_ms, ttl_epoch_ms, ttl_ms, signature_format)"],
        ["Signing Standard", "NIST FIPS 204 — ML-DSA-65 (Dilithium-3) / ML-DSA-87 (Dilithium-5)"],
        ["KEM Standard",     "NIST FIPS 203 — ML-KEM-768 (Kyber-768)"],
        ["Endpoint",         "POST  https://velos-gateway.onrender.com/api/v1/intercept"],
    ]
    mt = Table(meta, colWidths=[1.7*inch, 5.36*inch])
    mt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(0,-1), CARD_BG),
        ('BACKGROUND',    (1,0),(1,-1), DARK_BG),
        ('TEXTCOLOR',     (0,0),(0,-1), GOLD),
        ('TEXTCOLOR',     (1,0),(1,-1), WHITE),
        ('FONTNAME',      (0,0),(0,-1), 'Helvetica-Bold'),
        ('FONTNAME',      (1,0),(1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,0),(-1,-1), 7.5),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('GRID',          (0,0),(-1,-1), 0.25, MGRAY),
        ('BOX',           (0,0),(-1,-1), 0.8, GOLD),
    ]))
    story.append(mt)
    story.append(Spacer(1, 0.18*inch))

    # Key note
    kn = Table([[P(
        "Every OMNIX decision produces a cryptographically signed JSON receipt encoding the "
        "complete governance trail. This document defines the exact schema Velos must implement "
        "to verify receipts at the T=0 interceptor gateway — TTL enforcement, hash integrity, "
        "and PQC signature dispatch.",
        fontSize=7.5, textColor=GOLD_LT, fontName='Helvetica-BoldOblique',
        alignment=TA_CENTER, leading=12
    )]], colWidths=[W])
    kn.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), CARD_BG),
        ('BOX',           (0,0),(-1,-1), 1.2, GOLD),
        ('TOPPADDING',    (0,0),(-1,-1), 10),
        ('BOTTOMPADDING', (0,0),(-1,-1), 10),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 14),
    ]))
    story.append(kn)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # PAGE 2 — JSON SCHEMA + FIELD REFERENCE + SIGNATURE FORMAT
    # ══════════════════════════════════════════════════════════
    sec("1.  Complete JSON Schema", story)
    code_block([
        "{",
        '  "receipt_id":          "OMNIX-A3F7C1D92B0E",',
        '  "timestamp":           "2026-04-09T14:23:01.847+00:00",',
        '  "issued_at_ms":        1744208581847,       // T=0 reference point (epoch ms)',
        '  "ttl_epoch_ms":        1744208611847,       // expiry — REJECT if now_ms > this',
        '  "ttl_ms":              30000,               // 30 s default, env: OMNIX_RECEIPT_TTL_MS',
        '  "asset":               "BTC/USDT",',
        '  "decision":            "BLOCK",             // BLOCK | ALLOW | PASS | UNKNOWN',
        '  "veto_chain":          ["AML: PASS ...", "SHARIA: BLOCK — gharar=0.81 ..."],',
        '  "policy_version":      "6.5.4e",',
        '  "engine_version":      "6.5.4e",',
        '  "prev_hash":           "a9f3c1d4...",       // SHA-256 of previous receipt (chain)',
        '  "signing_provider":    "dilithium3",        // bound into hash — anti-downgrade',
        '  "content_hash":        "3f8e7a2c...",       // SHA-256 of canonical payload',
        '  "signature":           "BASE64==...",       // encoding → see signature_format',
        '  "signature_algorithm": "Dilithium-3 (ML-DSA-65)",',
        '  "signature_format":    "base64_pqc",        // base64_pqc | hex_sha256_fallback | NONE',
        '  "public_key":          "BASE64==...",       // null in fallback mode',
        '  // Conditional (present only if gate evaluated):',
        '  "sharia_compliance":{...}, "aml_compliance":{...}, "fraud_compliance":{...},',
        '  "jurisdiction_compliance":{...}, "context_admission":{...}, "avm_result":{...}',
        "}",
    ], story)

    sec("2.  Field Reference", story)
    fh = hdr_cells(["Field", "Type", "Description"])
    fr = [
        [P("receipt_id",         fontSize=6.5, textColor=MONO,  fontName='Courier'),
         P("string",             fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("Unique ID. Format: OMNIX-{12 hex uppercase}", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("timestamp",          fontSize=6.5, textColor=MONO,  fontName='Courier'),
         P("string",             fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("ISO-8601 UTC generation time", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("issued_at_ms",       fontSize=6.5, textColor=GREEN, fontName='Courier'),
         P("integer",            fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("Unix epoch ms — canonical T=0 reference point", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("ttl_epoch_ms",       fontSize=6.5, textColor=GREEN, fontName='Courier'),
         P("integer",            fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("Expiry epoch ms. Velos MUST reject if now_ms > ttl_epoch_ms", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("ttl_ms",             fontSize=6.5, textColor=GREEN, fontName='Courier'),
         P("integer",            fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("TTL in ms. Default 30000 (30 s). Configurable via OMNIX_RECEIPT_TTL_MS", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("asset",              fontSize=6.5, textColor=MONO,  fontName='Courier'),
         P("string",             fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("Asset symbol — e.g. BTC/USDT, ETH/USD", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("decision",           fontSize=6.5, textColor=MONO,  fontName='Courier'),
         P("string",             fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("BLOCK | ALLOW | PASS | UNKNOWN. BLOCK = OMNIX vetoed, Velos must not proceed", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("veto_chain",         fontSize=6.5, textColor=MONO,  fontName='Courier'),
         P("array",              fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("Ordered gate verdicts. Format: 'GATE: RESULT — detail' (max 80 chars each)", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("prev_hash",          fontSize=6.5, textColor=MONO,  fontName='Courier'),
         P("string",             fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("SHA-256 of prior receipt — tamper-evident chain. Empty string for first receipt", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("signing_provider",   fontSize=6.5, textColor=MONO,  fontName='Courier'),
         P("string",             fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("Algorithm ID bound into signed payload (anti-downgrade). Values: dilithium3 | dilithium5 | sha256", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("content_hash",       fontSize=6.5, textColor=MONO,  fontName='Courier'),
         P("string",             fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("SHA-256 hex of canonical JSON (sort_keys=True, ensure_ascii=True). This is what gets signed", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("signature_format",   fontSize=6.5, textColor=GREEN, fontName='Courier'),
         P("string",             fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("Critical for Velos. Disambiguates signature encoding. See Section 3", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("signature",          fontSize=6.5, textColor=MONO,  fontName='Courier'),
         P("str|null",           fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("Detached signature over content_hash. Encoding depends on signature_format", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
        [P("public_key",         fontSize=6.5, textColor=MONO,  fontName='Courier'),
         P("str|null",           fontSize=6.5, textColor=LGRAY, fontName='Helvetica-Oblique'),
         P("Base64 public key for PQC verification. null when signature_format=hex_sha256_fallback", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9)],
    ]
    grid_table(fh, fr, [1.5*inch, 0.7*inch, 4.86*inch], story)

    sec("3.  signature_format — Dispatch Table", story)
    sh = hdr_cells(["signature_format", "Signature encoding", "How Velos verifies"])
    sr = [
        [P("base64_pqc",          fontSize=6.5, textColor=MONO,   fontName='Courier'),
         P("Base64-encoded raw PQC bytes",        fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9),
         P("base64.decode → Dilithium.verify(sig, content_hash, public_key)", fontSize=6.5, textColor=LGRAY, fontName='Helvetica', leading=9)],
        [P("hex_sha256_fallback",  fontSize=6.5, textColor=ORANGE, fontName='Courier'),
         P("Hex of SHA-256(content_hash). Symmetric. public_key=null", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9),
         P("sha256(content_hash.encode()).hexdigest() == signature",  fontSize=6.5, textColor=LGRAY, fontName='Helvetica', leading=9)],
        [P("NONE",                 fontSize=6.5, textColor=RED,    fontName='Courier'),
         P("Signing failed — no integrity guarantee", fontSize=6.5, textColor=WHITE, fontName='Helvetica', leading=9),
         P("REJECT unconditionally",                  fontSize=6.5, textColor=RED,   fontName='Helvetica-Bold', leading=9)],
    ]
    t = Table([sh]+sr, colWidths=[1.5*inch, 2.36*inch, 3.2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  CARD_BG),
        ('BACKGROUND',    (0,1),(-1,1),  DARK_MID),
        ('BACKGROUND',    (0,2),(-1,2),  ALT_ROW),
        ('BACKGROUND',    (0,3),(-1,3),  RED_DIM),
        ('GRID',          (0,0),(-1,-1), 0.25, MGRAY),
        ('BOX',           (0,0),(-1,-1), 0.7,  GOLD),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # PAGE 3 — ALGORITHM + TIERS + HASH CONTRACT + CHECKLIST
    # ══════════════════════════════════════════════════════════
    sec("4.  Verification Algorithm (drop-in Python  |  pip install pypqc)", story)
    code_block([
        "import json, hashlib, base64, time",
        "def verify_omnix_receipt(r):",
        "    # 1 — TTL",
        "    if r.get('ttl_epoch_ms') and int(time.time()*1000) > r['ttl_epoch_ms']:",
        "        return {'valid': False, 'reason': 'RECEIPT_EXPIRED'}",
        "    # 2 — Rebuild signed payload",
        "    M = ['receipt_id','timestamp','issued_at_ms','ttl_epoch_ms','ttl_ms',",
        "         'asset','decision','veto_chain','policy_version','engine_version',",
        "         'prev_hash','signing_provider']",
        "    C = ['sharia_compliance','aml_compliance','fraud_compliance',",
        "         'jurisdiction_compliance','context_admission','veto_type','avm_result']",
        "    p = {k: r[k] for k in M if k in r}",
        "    for k in C:",
        "        if k in r: p[k] = r[k]",
        "    # 3 — Verify content_hash",
        "    h = hashlib.sha256(json.dumps(p, sort_keys=True, ensure_ascii=True).encode()).hexdigest()",
        "    if h != r.get('content_hash'): return {'valid': False, 'reason': 'HASH_MISMATCH'}",
        "    # 4 — Verify signature",
        "    fmt, sig, msg = r.get('signature_format'), r.get('signature'), r['content_hash'].encode()",
        "    if fmt == 'base64_pqc':",
        "        prov = r.get('signing_provider', 'dilithium3')",
        "        try:",
        "            if prov == 'dilithium3':",
        "                from pqc.sign import dilithium3",
        "                dilithium3.verify(base64.b64decode(sig), msg, base64.b64decode(r['public_key']))",
        "            elif prov == 'dilithium5':",
        "                from pqc.sign import dilithium5",
        "                dilithium5.verify(base64.b64decode(sig), msg, base64.b64decode(r['public_key']))",
        "        except: return {'valid': False, 'reason': 'SIGNATURE_INVALID'}",
        "    elif fmt == 'hex_sha256_fallback':",
        "        if hashlib.sha256(r['content_hash'].encode()).hexdigest() != sig:",
        "            return {'valid': False, 'reason': 'FALLBACK_HASH_MISMATCH'}",
        "    else: return {'valid': False, 'reason': f'UNKNOWN_FORMAT:{fmt}'}",
        "    return {'valid': True}",
    ], story)

    # Tiers + Hash side by side
    tier_hdr = hdr_cells(["Tier", "signing_provider", "Algorithm", "Standard", "Security", "PK / Sig"])
    tier_rows = [
        [P("Enterprise (default)", fontSize=6.5, textColor=WHITE,  fontName='Helvetica'),
         P("dilithium3",           fontSize=6.5, textColor=MONO,   fontName='Courier'),
         P("Dilithium-3 (ML-DSA-65)", fontSize=6.5, textColor=GOLD_LT, fontName='Helvetica'),
         P("FIPS 204",             fontSize=6.5, textColor=LGRAY,  fontName='Helvetica'),
         P("~192-bit",             fontSize=6.5, textColor=WHITE,  fontName='Helvetica'),
         P("1952 B / ~3309 B",     fontSize=6.5, textColor=LGRAY,  fontName='Helvetica', leading=9)],
        [P("High-Assurance",       fontSize=6.5, textColor=WHITE,  fontName='Helvetica'),
         P("dilithium5",           fontSize=6.5, textColor=MONO,   fontName='Courier'),
         P("Dilithium-5 (ML-DSA-87)", fontSize=6.5, textColor=GOLD_LT, fontName='Helvetica'),
         P("FIPS 204",             fontSize=6.5, textColor=LGRAY,  fontName='Helvetica'),
         P("~256-bit",             fontSize=6.5, textColor=WHITE,  fontName='Helvetica'),
         P("2592 B / ~4627 B",     fontSize=6.5, textColor=LGRAY,  fontName='Helvetica', leading=9)],
        [P("No PQC fallback",      fontSize=6.5, textColor=WHITE,  fontName='Helvetica'),
         P("sha256",               fontSize=6.5, textColor=ORANGE, fontName='Courier'),
         P("SHA-256 symmetric",    fontSize=6.5, textColor=LGRAY,  fontName='Helvetica'),
         P("—",                    fontSize=6.5, textColor=LGRAY,  fontName='Helvetica'),
         P("N/A",                  fontSize=6.5, textColor=LGRAY,  fontName='Helvetica'),
         P("N/A / 64 hex",         fontSize=6.5, textColor=LGRAY,  fontName='Helvetica', leading=9)],
    ]
    grid_table(tier_hdr, tier_rows,
               [1.2*inch, 0.85*inch, 1.55*inch, 0.6*inch, 0.56*inch, 1.0*inch],
               story, row_bgs=[GREEN_DIM, BLUE_DIM, RED_DIM])

    sec("5.  content_hash — Fields Included / Excluded", story)
    lp = "\n".join([
        "IN HASH (mandatory): asset, decision, engine_version,",
        "issued_at_ms, policy_version, prev_hash, receipt_id,",
        "signing_provider, timestamp, ttl_epoch_ms, ttl_ms, veto_chain",
        "",
        "IN HASH (if present): sharia_compliance, aml_compliance,",
        "fraud_compliance, jurisdiction_compliance, context_admission,",
        "veto_type, avm_result",
    ])
    rp = "\n".join([
        "NOT IN HASH (detached signature pattern):",
        "content_hash (itself), signature,",
        "signature_algorithm, signature_format,",
        "public_key",
    ])
    hash_t = Table([
        [P(lp, fontSize=6.5, textColor=MONO,  fontName='Courier', leading=10),
         P(rp, fontSize=6.5, textColor=RED,   fontName='Courier', leading=10)]
    ], colWidths=[3.6*inch, 3.46*inch])
    hash_t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(0,0), DARK_MID),
        ('BACKGROUND',    (1,0),(1,0), RED_DIM),
        ('BOX',           (0,0),(-1,-1), 0.7, GOLD),
        ('LINEAFTER',     (0,0),(0,-1), 0.4, MGRAY),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (0,0),(-1,-1), 9),
        ('RIGHTPADDING',  (0,0),(-1,-1), 9),
    ]))
    story.append(hash_t)
    story.append(Spacer(1, 0.06*inch))

    sec("6.  Integration Checklist", story)
    ch = hdr_cells(["#", "Check", "Rule"])
    cr = [
        ["1", "now_ms > ttl_epoch_ms?",     "Reject with RECEIPT_EXPIRED"],
        ["2", "Read signature_format",       "Never hardcode — dispatch on this field"],
        ["3", "Read signing_provider",       "Determines which PQC algorithm to use"],
        ["4", "pip install pypqc",           "Required on Velos for PQC verification"],
        ["5", "Recompute content_hash",      "Exclude: signature, public_key, sig_format, sig_algorithm, content_hash itself"],
        ["6", "decision == BLOCK?",          "Do not proceed — OMNIX has vetoed this action"],
        ["7", "signature_format == NONE?",   "Reject unconditionally — no integrity guarantee"],
    ]
    cr_cells = [
        [P(r[0], fontSize=6.5, textColor=GOLD_LT, fontName='Helvetica-Bold'),
         P(r[1], fontSize=6.5, textColor=MONO,     fontName='Courier'),
         P(r[2], fontSize=6.5, textColor=WHITE,    fontName='Helvetica', leading=9)]
        for r in cr
    ]
    grid_table(ch, cr_cells, [0.24*inch, 1.82*inch, 5.0*inch], story)

    story.append(HRFlowable(width="100%", thickness=0.6, color=GOLD))
    story.append(Spacer(1, 0.05*inch))
    story.append(P(
        "Harold Nunes — OMNIX QUANTUM LTD  |  omnixquantum.com",
        fontSize=6.5, textColor=LGRAY, fontName='Helvetica', alignment=TA_CENTER
    ))

    doc.build(story, canvasmaker=NC)
    print(f"PDF generado: {out}")


if __name__ == "__main__":
    build_pdf()
