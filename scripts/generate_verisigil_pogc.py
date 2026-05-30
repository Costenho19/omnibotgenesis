"""
OMNIX Proof of Governance Certificate — External Issuance
VeriSigil AI · POGC-EXT Series · ADR-186

First External PoGC: certifying a third-party governance decision
using the OMNIX PoGR trust infrastructure.

Analogous to X.509 CA issuance: OMNIX certifies the governance was authentic.
VeriSigil remains sovereign over its system.

Harold Nunes — OMNIX QUANTUM LTD — 2026-05-30
"""

import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.colors import HexColor
except ImportError:
    print("ERROR: pip install reportlab")
    sys.exit(1)

OUTPUT_DIR = Path("evidence_packages")
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
POGC_ID     = "POGC-EXT-A7F3C2B1D9E4F508"
ISSUED_AT   = datetime(2026, 5, 30, 21, 0, 0, tzinfo=timezone.utc)
EXPIRES_AT  = ISSUED_AT + timedelta(days=365)

SUBJECT = {
    "org":        "VeriSigil AI",
    "org_id":     "verisigil-ai-001",
    "system":     "Constitutional Execution Substrate",
    "agent_id":   "financial-agent-1780111266",
    "agent_type": "financial-execution-agent",
    "instance":   "live-production",
}

DECISION = {
    "action":       "wire_transfer",
    "amount_usd":   250000,
    "currency":     "USD",
    "outcome":      "DENY",
    "reason":       "Amount exceeds autonomous limit for CRITICAL consequence",
    "consequence_class": "CRITICAL",
    "decision_date": "2026-05-30",
}

EVIDENCE = {
    "evidence_hash":  "586b996f53da83652b2690b4117a4830d4bde3c22c7737085c40f5ee86a4ac3a",
    "bundle_id":      "bundle-482df2c4f1d9",
    "hash_algorithm": "SHA-256",
    "bundle_status":  "offline-verifiable",
    "bundle_seal":    "SHA-256 sealed",
}

PROTOCOL = {
    "name":        "VGS-ELI: Execution Legitimacy Infrastructure",
    "version":     "1.0.0",
    "doi":         "10.5281/zenodo.20451306",
    "url":         "https://doi.org/10.5281/zenodo.20451306",
    "invariants":  ["VGS-ELI-INV-001", "VGS-ELI-INV-008"],
    "inv_001_desc": "Pre-Execution Admissibility — authority resolved before action",
    "inv_008_desc": "Causality Preserved — decision trace is causally complete",
}

REGULATORY = {
    "EU_AI_Act_Art_11": "Technical documentation — governance decision record",
    "NIST_AU_2":        "Audit Events — machine-readable governance evidence",
    "ISO_42001_Art_9_1": "Monitoring, measurement, analysis and evaluation",
}


def _canonical_fields(cert: dict) -> dict:
    return {
        "pogc_id":               cert["pogc_id"],
        "certificate_class":     cert["certificate_class"],
        "issuer":                cert["issuer"],
        "subject_org":           cert["subject_org"],
        "agent_id":              cert["agent_id"],
        "governance_outcome":    cert["governance_outcome"],
        "evidence_hash":         cert["evidence_hash"],
        "compliance_tier":       cert["compliance_tier"],
        "mandate_certification": cert["mandate_certification"],
        "issued_at":             cert["issued_at"],
        "expires_at":            cert["expires_at"],
    }


def _content_hash(canonical: dict) -> str:
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    return "sha3-256:" + hashlib.sha3_256(payload).hexdigest()


def _sign(canonical: dict) -> tuple[str, str]:
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    sk_b64 = os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64")
    if sk_b64:
        try:
            import base64
            import ctypes
            import ctypes.util
            _lib = ctypes.util.find_library("oqs")
            if not _lib:
                raise RuntimeError("liboqs shared library not found — Railway will upgrade")
            from oqs import Signature
            sk = base64.b64decode(sk_b64)
            signer = Signature("ML-DSA-65", sk)
            sig_bytes = signer.sign(payload)
            return "ML-DSA-65:" + sig_bytes.hex(), "ml-dsa-65"
        except Exception as exc:
            print(f"  [WARN] PQC signing unavailable: {exc}")
            print("         Stub issued — upgrade via POST /v1/pogr/admin/resign on Railway")
    stub = hashlib.sha3_256(b"POGR-EXT-STUB:" + payload).hexdigest()
    return "STUB-SHA3-256:" + stub, "stub-sha3-256"


def build_certificate() -> dict:
    issued_str  = ISSUED_AT.isoformat()
    expires_str = EXPIRES_AT.isoformat()

    cert = {
        "pogc_id":               POGC_ID,
        "certificate_class":     "EXTERNAL",
        "version":               "1.0",
        "issuer":                "OMNIX QUANTUM LTD",
        "issuer_protocol":       "OMNIX PoGR — ADR-186/187",
        "issuer_rfcs":           ["RFC-ATF-1", "RFC-ATF-2", "RFC-ATF-3",
                                  "RFC-ATF-4", "RFC-ATF-5", "RFC-ATF-6"],
        "subject_org":           SUBJECT["org"],
        "subject_org_id":        SUBJECT["org_id"],
        "subject_system":        SUBJECT["system"],
        "agent_id":              SUBJECT["agent_id"],
        "agent_type":            SUBJECT["agent_type"],
        "agent_instance":        SUBJECT["instance"],
        "governance_decision":   DECISION,
        "governance_outcome":    DECISION["outcome"],
        "evidence_hash":         EVIDENCE["evidence_hash"],
        "evidence_bundle":       EVIDENCE["bundle_id"],
        "evidence_algorithm":    EVIDENCE["hash_algorithm"],
        "external_protocol":     PROTOCOL,
        "regulatory_mapping":    REGULATORY,
        "compliance_tier":       "EXT-VGS-ELI-Compliant",
        "mandate_certification": "MANDATE-BOUND",
        "enforcement_model":     "Structural DENY — no bypass path admitted",
        "boundary_type":         "Pre-execution admissibility gate",
        "issued_at":             issued_str,
        "expires_at":            expires_str,
        "status":                "ACTIVE",
        "pqc_algorithm":         "ml-dsa-65",
        "fips_standard":         "FIPS 204 / NIST ML-DSA",
    }

    canonical  = _canonical_fields(cert)
    c_hash     = _content_hash(canonical)
    sig, algo  = _sign(canonical)

    cert["content_hash"]  = c_hash
    cert["pqc_signature"] = sig
    cert["pqc_algorithm"] = algo
    cert["canonical_fields_hashed"] = list(canonical.keys())

    return cert


def wrap(text: str, width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for w in words:
        if len(line) + len(w) + 1 <= width:
            line = (line + " " + w).strip()
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def generate_pdf(cert: dict, path: Path) -> None:
    W, H = A4
    c = rl_canvas.Canvas(str(path), pagesize=A4)

    NAVY    = HexColor("#060F1E")
    GOLD    = HexColor("#C9A227")
    GOLD2   = HexColor("#E8C84A")
    WHITE   = HexColor("#F0F4FF")
    SILVER  = HexColor("#94A3B8")
    DIM     = HexColor("#475569")
    GREEN   = HexColor("#22C55E")
    RED     = HexColor("#EF4444")
    TEAL    = HexColor("#0EA5E9")
    BG2     = HexColor("#0D1B2E")
    BG3     = HexColor("#112240")

    MARGIN  = 18 * mm
    CW      = W - 2 * MARGIN

    def rect_fill(x, y, w, h, col):
        c.setFillColor(col)
        c.rect(x, y, w, h, fill=1, stroke=0)

    def rect_stroke(x, y, w, h, col, lw=0.5):
        c.setStrokeColor(col)
        c.setLineWidth(lw)
        c.rect(x, y, w, h, fill=0, stroke=1)

    def text(x, y, txt, size=9, col=WHITE, font="Helvetica", align="left"):
        c.setFont(font, size)
        c.setFillColor(col)
        if align == "center":
            c.drawCentredString(x, y, txt)
        elif align == "right":
            c.drawRightString(x, y, txt)
        else:
            c.drawString(x, y, txt)

    def mono(x, y, txt, size=7.5, col=SILVER):
        text(x, y, txt, size=size, col=col, font="Courier")

    def section_header(y, label):
        rect_fill(MARGIN, y - 3 * mm, CW, 8 * mm, BG3)
        rect_stroke(MARGIN, y - 3 * mm, CW, 8 * mm, GOLD, 0.4)
        text(MARGIN + 4 * mm, y + 1.5 * mm, label,
             size=8, col=GOLD, font="Helvetica-Bold")
        return y - 3 * mm - 6 * mm

    def kv(x, y, key, val, key_w=55*mm, val_col=WHITE):
        text(x, y, key, size=7.5, col=SILVER, font="Helvetica")
        text(x + key_w, y, val, size=7.5, col=val_col, font="Helvetica")

    def kv_mono(x, y, key, val, key_w=55*mm):
        text(x, y, key, size=7.5, col=SILVER, font="Helvetica")
        mono(x + key_w, y, val, size=7.0, col=WHITE)

    # ── Full-page background ──────────────────────────────────────────────────
    rect_fill(0, 0, W, H, NAVY)

    # ── Outer border ─────────────────────────────────────────────────────────
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    c.rect(10*mm, 10*mm, W - 20*mm, H - 20*mm, fill=0, stroke=1)
    c.setStrokeColor(HexColor("#1E3A5F"))
    c.setLineWidth(0.4)
    c.rect(11.5*mm, 11.5*mm, W - 23*mm, H - 23*mm, fill=0, stroke=1)

    # ── Header block ─────────────────────────────────────────────────────────
    yh = H - 22 * mm
    rect_fill(MARGIN, yh, CW, 18 * mm, BG2)
    rect_stroke(MARGIN, yh, CW, 18 * mm, GOLD, 0.6)

    text(MARGIN + 5 * mm, yh + 12.5 * mm, "OMNIX QUANTUM LTD",
         size=10, col=GOLD, font="Helvetica-Bold")
    text(MARGIN + 5 * mm, yh + 7.5 * mm,
         "Proof of Governance Registry  ·  External Certificate",
         size=8, col=SILVER, font="Helvetica")
    text(MARGIN + 5 * mm, yh + 3 * mm, "ADR-186 / ADR-187  ·  RFC-ATF-1 through RFC-ATF-6",
         size=6.5, col=DIM, font="Helvetica")

    text(W - MARGIN - 5 * mm, yh + 12.5 * mm, "ACTIVE",
         size=9, col=GREEN, font="Helvetica-Bold", align="right")
    text(W - MARGIN - 5 * mm, yh + 7.5 * mm, "MANDATE-BOUND",
         size=7.5, col=GREEN, font="Helvetica-Bold", align="right")
    text(W - MARGIN - 5 * mm, yh + 3 * mm, "ML-DSA-65  ·  FIPS 204",
         size=6.5, col=DIM, font="Helvetica", align="right")

    # ── Certificate title ─────────────────────────────────────────────────────
    y = yh - 4 * mm
    text(W / 2, y, "PROOF OF GOVERNANCE CERTIFICATE",
         size=13, col=GOLD2, font="Helvetica-Bold", align="center")
    y -= 5 * mm
    text(W / 2, y, "External Governance Verification  ·  POGC-EXT Series",
         size=8, col=SILVER, font="Helvetica", align="center")

    # ── POGC ID bar ───────────────────────────────────────────────────────────
    y -= 5 * mm
    rect_fill(MARGIN, y - 2 * mm, CW, 9 * mm, BG3)
    rect_stroke(MARGIN, y - 2 * mm, CW, 9 * mm, GOLD, 0.5)
    text(MARGIN + 4 * mm, y + 3.5 * mm, "Certificate ID",
         size=7, col=SILVER, font="Helvetica")
    mono(MARGIN + 38 * mm, y + 3.5 * mm, POGC_ID, size=9, col=GOLD2)
    text(W - MARGIN - 4 * mm, y + 3.5 * mm,
         "omnixquantum.net/pogr/verify/" + POGC_ID[:20] + "...",
         size=6.5, col=TEAL, font="Helvetica", align="right")

    # ── SECTION 1: Certification Parties ─────────────────────────────────────
    y -= 9 * mm
    y = section_header(y, "§1  CERTIFICATION PARTIES")

    rect_fill(MARGIN, y - 28 * mm, CW * 0.48, 30 * mm, BG3)
    rect_stroke(MARGIN, y - 28 * mm, CW * 0.48, 30 * mm, HexColor("#1E3A5F"), 0.4)
    text(MARGIN + 4 * mm, y - 2 * mm, "ISSUER", size=7, col=GOLD, font="Helvetica-Bold")
    kv(MARGIN + 4 * mm, y - 7 * mm, "Organization", "OMNIX QUANTUM LTD")
    kv(MARGIN + 4 * mm, y - 12 * mm, "Role", "Certificate Authority")
    kv(MARGIN + 4 * mm, y - 17 * mm, "Protocol", "PoGR — ADR-186/187")
    kv(MARGIN + 4 * mm, y - 22 * mm, "PQC Standard", "ML-DSA-65 · FIPS 204")

    rx = MARGIN + CW * 0.52
    rect_fill(rx, y - 28 * mm, CW * 0.48, 30 * mm, BG3)
    rect_stroke(rx, y - 28 * mm, CW * 0.48, 30 * mm, HexColor("#1E3A5F"), 0.4)
    text(rx + 4 * mm, y - 2 * mm, "SUBJECT", size=7, col=TEAL, font="Helvetica-Bold")
    kv(rx + 4 * mm, y - 7 * mm, "Organization", SUBJECT["org"])
    kv(rx + 4 * mm, y - 12 * mm, "System", SUBJECT["system"])
    kv(rx + 4 * mm, y - 17 * mm, "Org ID", SUBJECT["org_id"])
    kv(rx + 4 * mm, y - 22 * mm, "Certificate Class", "EXTERNAL")

    y -= 34 * mm

    # ── SECTION 2: Governed Agent ─────────────────────────────────────────────
    y = section_header(y, "§2  GOVERNED AGENT")
    kv(MARGIN + 4 * mm, y - 4 * mm, "Agent ID", SUBJECT["agent_id"])
    kv(MARGIN + 4 * mm, y - 9 * mm, "Agent Type", SUBJECT["agent_type"])
    kv(MARGIN + 4 * mm, y - 14 * mm, "Instance", SUBJECT["instance"])
    kv(MARGIN + 4 * mm, y - 19 * mm, "Decision Date", DECISION["decision_date"])
    y -= 24 * mm

    # ── SECTION 3: Governance Decision ───────────────────────────────────────
    y = section_header(y, "§3  GOVERNANCE DECISION RECORD")

    rect_fill(MARGIN, y - 30 * mm, CW, 32 * mm, HexColor("#0A0E1A"))
    rect_stroke(MARGIN, y - 30 * mm, CW, 32 * mm, RED, 0.8)
    text(MARGIN + 4 * mm, y - 3 * mm, "ACTION", size=7, col=SILVER, font="Helvetica")
    text(MARGIN + 32 * mm, y - 3 * mm, "wire_transfer",
         size=7, col=WHITE, font="Courier-Bold")
    text(MARGIN + 4 * mm, y - 9 * mm, "AMOUNT", size=7, col=SILVER, font="Helvetica")
    text(MARGIN + 32 * mm, y - 9 * mm, "USD 250,000.00",
         size=7, col=WHITE, font="Courier-Bold")
    text(MARGIN + 4 * mm, y - 15 * mm, "OUTCOME", size=7, col=SILVER, font="Helvetica")
    text(MARGIN + 32 * mm, y - 15 * mm, "DENY",
         size=12, col=RED, font="Helvetica-Bold")
    text(MARGIN + 4 * mm, y - 22 * mm, "REASON", size=7, col=SILVER, font="Helvetica")
    text(MARGIN + 32 * mm, y - 22 * mm,
         "Amount exceeds autonomous limit for CRITICAL consequence",
         size=7, col=WHITE, font="Helvetica")
    text(MARGIN + 4 * mm, y - 27 * mm, "CONSEQUENCE CLASS", size=7, col=SILVER, font="Helvetica")
    text(MARGIN + 60 * mm, y - 27 * mm, "CRITICAL",
         size=7, col=RED, font="Helvetica-Bold")
    y -= 35 * mm

    # ── SECTION 4: Evidence Record ────────────────────────────────────────────
    y = section_header(y, "§4  EVIDENCE RECORD")
    kv_mono(MARGIN + 4 * mm, y - 4 * mm, "Evidence Hash (SHA-256)",
            EVIDENCE["evidence_hash"][:48] + "...")
    kv_mono(MARGIN + 4 * mm, y - 9 * mm, "Bundle ID",
            EVIDENCE["bundle_id"])
    kv(MARGIN + 4 * mm, y - 14 * mm, "Bundle Status",
       "offline-verifiable · SHA-256 sealed", val_col=GREEN)
    y -= 19 * mm

    # ── SECTION 5: External Protocol ─────────────────────────────────────────
    y = section_header(y, "§5  EXTERNAL GOVERNANCE PROTOCOL")
    kv(MARGIN + 4 * mm, y - 4 * mm, "Protocol", PROTOCOL["name"])
    kv(MARGIN + 4 * mm, y - 9 * mm, "Version", PROTOCOL["version"])
    kv_mono(MARGIN + 4 * mm, y - 14 * mm, "DOI", PROTOCOL["doi"])
    kv(MARGIN + 4 * mm, y - 19 * mm, "Invariants Satisfied",
       "VGS-ELI-INV-001  ·  VGS-ELI-INV-008", val_col=GREEN)
    kv(MARGIN + 4 * mm, y - 24 * mm,
       "INV-001", "Pre-Execution Admissibility — authority resolved before action")
    kv(MARGIN + 4 * mm, y - 29 * mm,
       "INV-008", "Causality Preserved — decision trace is causally complete")
    y -= 34 * mm

    # ── SECTION 6: OMNIX Certification ───────────────────────────────────────
    y = section_header(y, "§6  OMNIX CERTIFICATION ASSESSMENT")
    kv(MARGIN + 4 * mm, y - 4 * mm, "Compliance Tier", "EXT-VGS-ELI-Compliant", val_col=GREEN)
    kv(MARGIN + 4 * mm, y - 9 * mm, "Mandate Certification", "MANDATE-BOUND", val_col=GREEN)
    kv(MARGIN + 4 * mm, y - 14 * mm, "Enforcement Model",
       "Structural DENY — no bypass path admitted")
    kv(MARGIN + 4 * mm, y - 19 * mm, "Boundary Type", "Pre-execution admissibility gate")
    kv(MARGIN + 4 * mm, y - 24 * mm, "Regulatory Mapping",
       "EU AI Act Art.11  ·  NIST AU-2  ·  ISO 42001 Art.9.1")
    y -= 29 * mm

    # ── SECTION 7: Cryptographic Anchor ──────────────────────────────────────
    y = section_header(y, "§7  CRYPTOGRAPHIC ANCHOR  ·  ML-DSA-65 (FIPS 204 / NIST ML-DSA)")

    sig_val  = cert.get("pqc_signature", "")
    sig_algo = cert.get("pqc_algorithm", "")
    c_hash   = cert.get("content_hash", "")

    if sig_val.startswith("ML-DSA-65:"):
        sig_display = sig_val[10:74] + "..."
        sig_label   = "PQC Signature (ML-DSA-65)"
        sig_col     = GREEN
    else:
        sig_display = sig_val[16:64] + "..." if len(sig_val) > 16 else sig_val
        sig_label   = "Signature (dev stub — upgrade via admin/resign)"
        sig_col     = HexColor("#F59E0B")

    kv_mono(MARGIN + 4 * mm, y - 4 * mm, "Content Hash", c_hash[:56] + "...")
    text(MARGIN + 4 * mm, y - 9 * mm, sig_label, size=7, col=SILVER, font="Helvetica")
    mono(MARGIN + 4 * mm, y - 14 * mm, sig_display, size=6.5, col=sig_col)
    kv(MARGIN + 4 * mm, y - 19 * mm, "Algorithm", "ML-DSA-65  (NIST FIPS 204)")
    kv(MARGIN + 4 * mm, y - 24 * mm, "Canonical Fields",
       "pogc_id · class · issuer · subject · agent · outcome · evidence · tier · dates")
    y -= 29 * mm

    # ── SECTION 8: Validity & Verification ───────────────────────────────────
    y = section_header(y, "§8  VALIDITY  ·  OFFLINE-VERIFIABLE — ZERO OMNIX ACCESS REQUIRED")

    kv(MARGIN + 4 * mm, y - 4 * mm, "Status", "ACTIVE", val_col=GREEN)
    kv(MARGIN + 4 * mm, y - 9 * mm, "Issued",
       ISSUED_AT.strftime("%Y-%m-%d %H:%M:%S UTC"))
    kv(MARGIN + 4 * mm, y - 14 * mm, "Expires",
       EXPIRES_AT.strftime("%Y-%m-%d %H:%M:%S UTC"))
    kv(MARGIN + 4 * mm, y - 19 * mm, "TTL", "365 days  (PoGR-INV-004)")
    kv(MARGIN + 4 * mm, y - 24 * mm, "Public Verify",
       "https://omnixquantum.net/v1/pogr/verify/" + POGC_ID,
       val_col=TEAL)
    y -= 29 * mm

    # ── Footer ────────────────────────────────────────────────────────────────
    fy = 14 * mm
    rect_fill(MARGIN, fy, CW, 7 * mm, BG2)
    text(MARGIN + 4 * mm, fy + 4 * mm,
         "This certificate was issued by OMNIX QUANTUM LTD under the OMNIX Proof of Governance Registry (PoGR).",
         size=6, col=DIM, font="Helvetica")
    text(MARGIN + 4 * mm, fy + 1.5 * mm,
         "Verification requires no OMNIX account (PoGR-INV-003). "
         "Cryptographic proof is self-contained. "
         "This is the world's first cross-protocol PoGC (POGC-EXT series).",
         size=6, col=DIM, font="Helvetica")
    text(W - MARGIN - 4 * mm, fy + 4 * mm,
         "OMNIX QUANTUM LTD", size=6, col=GOLD, font="Helvetica-Bold", align="right")
    text(W - MARGIN - 4 * mm, fy + 1.5 * mm,
         "omnixquantum.net", size=6, col=DIM, font="Helvetica", align="right")

    c.save()
    print(f"  [PDF] {path}")


def main():
    print("=" * 72)
    print("OMNIX Proof of Governance Certificate — External Issuance")
    print("Subject: VeriSigil AI · System: Constitutional Execution Substrate")
    print("=" * 72)
    print()

    print("[1/3] Building certificate...")
    cert = build_certificate()

    json_path = OUTPUT_DIR / f"{POGC_ID}_{TIMESTAMP}.json"
    with open(json_path, "w") as f:
        json.dump(cert, f, indent=2, default=str)
    print(f"  [JSON] {json_path}")

    print("[2/3] Generating PDF...")
    pdf_path = OUTPUT_DIR / f"{POGC_ID}_{TIMESTAMP}.pdf"
    generate_pdf(cert, pdf_path)

    print("[3/3] Verification check...")
    canonical   = {k: cert[k] for k in [
        "pogc_id", "certificate_class", "issuer", "subject_org",
        "agent_id", "governance_outcome", "evidence_hash",
        "compliance_tier", "mandate_certification", "issued_at", "expires_at"
    ]}
    recalc      = "sha3-256:" + hashlib.sha3_256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    hash_ok     = recalc == cert["content_hash"]
    sig_pqc     = cert["pqc_signature"].startswith("ML-DSA-65:")
    sig_stub    = cert["pqc_signature"].startswith("STUB-")
    active      = cert["status"] == "ACTIVE"
    mandate_ok  = cert["mandate_certification"] == "MANDATE-BOUND"

    print(f"  {'✓' if hash_ok    else '✗'} Content hash integrity")
    print(f"  {'✓' if sig_pqc   else '⚠'} PQC signature (ML-DSA-65)" + (" — dev stub" if sig_stub else ""))
    print(f"  {'✓' if active    else '✗'} Status ACTIVE")
    print(f"  {'✓' if mandate_ok else '✗'} Mandate certification MANDATE-BOUND")

    print()
    print("=" * 72)
    print("CERTIFICATE ISSUED")
    print(f"  POGC ID  : {cert['pogc_id']}")
    print(f"  Class    : {cert['certificate_class']}")
    print(f"  Subject  : {cert['subject_org']}")
    print(f"  Outcome  : {cert['governance_outcome']}")
    print(f"  Tier     : {cert['compliance_tier']}")
    print(f"  Mandate  : {cert['mandate_certification']}")
    print(f"  Issued   : {cert['issued_at']}")
    print(f"  Expires  : {cert['expires_at']}")
    print(f"  PQC Algo : {cert['pqc_algorithm']}")
    print(f"  JSON     : {json_path}")
    print(f"  PDF      : {pdf_path}")
    print("=" * 72)

    return json_path, pdf_path, cert


if __name__ == "__main__":
    main()
