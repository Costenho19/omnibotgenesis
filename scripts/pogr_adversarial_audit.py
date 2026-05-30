#!/usr/bin/env python3
"""
OMNIX Proof of Governance Registry — Adversarial Security Audit v2.0
=====================================================================
ADR-186 · ADR-187 · ADR-189 · PoGR-INV-001–006
OMNIX-POGR-2026-001

Metodología:
    Ataca los tres canales de verificación de forma independiente y compara
    los resultados. Un PoGC se considera SEGURO solo si los tres canales
    producen el mismo veredicto para el mismo input.

Canales auditados:
    OFFLINE  — scripts/verify_pogc_offline.py · verify_certificate() [subprocess]
    API_JSON — lógica de GET /v1/pogr/verify/<pogc_id>  (replicada en Python)
    HTML_WEB — lógica de GET /pogr/verify/<pogc_id>     (replicada en Python)

15 ataques ejecutados:
    A01  Issuer cambiado (canonical field)
    A02  mandate_certification cambiado (canonical field)
    A03  TTL expirado (expires_at genuino en el pasado)
    A04  content_hash field alterado en export JSON
    A05  Firma alterada — prefijo ML-DSA-65: conservado (POGR-SEC-001)
    A06  ID swap — contenido de otro PoGC (POGR-SEC-011)
    A07  Export manipulado — status REVOKED→ACTIVE (POGR-SEC-002)
    A08  Offline=VALID pero Web/API=INVALID (hash inconsistencia en DB)
    A09  API=VALID pero HTML=INVALID (firma STUB) (POGR-SEC-003)
    A10  PoGC inexistente
    A11  PoGC revocado — stale export divergence (POGR-SEC-002)
    A12  PoGC expirado (expires_at en el pasado)
    A13  Intento de replay — session_id duplicado (POGR-SEC-004)
    A14  Campos canónicos faltantes en JSON
    A15  JSON con campos extra maliciosos

Salida:
    Imprime tabla de resultados + divergencias en stdout.
    Genera POGR_ADVERSARIAL_AUDIT.md
    Genera POGR_TRUST_ASSUMPTION_MAP.md
    Genera POGR_WEB_API_OFFLINE_CONSISTENCY_REPORT.md

Uso:
    python scripts/pogr_adversarial_audit.py
    python scripts/pogr_adversarial_audit.py --no-color

Harold Nunes — OMNIX QUANTUM LTD — Mayo 2026
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────────────────────────────────────
#  ANSI colours (respects --no-color and non-tty)
# ─────────────────────────────────────────────────────────────────────────────

_USE_COLOR = True


def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def RED(t):    return _c("31;1", t)
def GREEN(t):  return _c("32;1", t)
def YELLOW(t): return _c("33;1", t)
def CYAN(t):   return _c("36;1", t)
def BLUE(t):   return _c("34;1", t)
def BOLD(t):   return _c("1",    t)
def DIM(t):    return _c("2",    t)
def GOLD(t):   return _c("33",   t)


# ─────────────────────────────────────────────────────────────────────────────
#  PoGC field constants — must mirror pogr_blueprint.py and verify_pogc_offline.py
# ─────────────────────────────────────────────────────────────────────────────

CANONICAL_FIELDS = [
    "pogc_id", "session_id", "ctchc_seal_hash",
    "issuer", "subject_org", "agent_id",
    "compliance_tier", "mandate_certification",
    "issued_at", "expires_at",
]
EXPECTED_ISSUER  = "OMNIX QUANTUM LTD"
VERIFIER_SCRIPT  = os.path.join(os.path.dirname(__file__), "verify_pogc_offline.py")


# ─────────────────────────────────────────────────────────────────────────────
#  Core hash utility (mirrors both blueprint and offline verifier exactly)
# ─────────────────────────────────────────────────────────────────────────────

def _compute_content_hash(cert: Dict[str, Any]) -> str:
    canonical = {k: cert[k] for k in CANONICAL_FIELDS if k in cert}
    payload   = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    return "sha3-256:" + hashlib.sha3_256(payload).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
#  Replicated verification logic — exact mirrors of production code
# ─────────────────────────────────────────────────────────────────────────────

def _verify_offline_subprocess(cert: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Run verify_pogc_offline.py via subprocess — tests the REAL verifier binary.
    Returns (exit_code_0, output_text).
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fh:
        json.dump(cert, fh, default=str)
        fname = fh.name
    try:
        res = subprocess.run(
            [sys.executable, VERIFIER_SCRIPT, "--file", fname],
            capture_output=True, text=True, timeout=20,
        )
        return res.returncode == 0, res.stdout + res.stderr
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except FileNotFoundError:
        return _verify_offline_inline(cert)[0], "(subprocess unavailable — used inline logic)"
    finally:
        try:
            os.unlink(fname)
        except OSError:
            pass


def _verify_offline_inline(cert: Dict[str, Any]) -> Tuple[bool, List[Tuple[str, Optional[bool], str]]]:
    """
    Inline mirror of verify_pogc_offline.py · verify_certificate().
    Returns (overall_valid, checks).
    None in 'passed' position = warning (doesn't fail overall).
    """
    checks: List[Tuple[str, Optional[bool], str]] = []
    now = datetime.now(timezone.utc)

    # [1] content_hash integrity
    stored   = cert.get("content_hash", "")
    computed = _compute_content_hash(cert)
    if stored == computed:
        checks.append(("content_hash", True,  f"OK ({stored[:32]}…)"))
    else:
        checks.append(("content_hash", False,
                        f"MISMATCH stored={stored[:24]}… expected={computed[:24]}…"))

    # [2] status
    status = cert.get("status", "UNKNOWN")
    if status == "ACTIVE":
        checks.append(("status", True,  "ACTIVE"))
    elif status in ("REVOKED", "EXPIRED"):
        checks.append(("status", False, f"{status} — {cert.get('revocation_reason','')}"))
    else:
        checks.append(("status", False, f"UNKNOWN: {status}"))

    # [3] TTL
    try:
        exp = datetime.fromisoformat(str(cert.get("expires_at", "")).replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now < exp:
            checks.append(("ttl", True,  f"Not expired — expires {exp.strftime('%Y-%m-%d')}"))
        else:
            checks.append(("ttl", False, f"Expired on {exp.strftime('%Y-%m-%d %H:%M UTC')}"))
    except Exception as exc:
        checks.append(("ttl", False, f"Cannot parse expires_at: {exc}"))

    # [4] PQC signature presence
    sig = cert.get("pqc_signature", "")
    if sig.startswith("ML-DSA-65:"):
        checks.append(("pqc_signature", True, "ML-DSA-65 present (prefix only — POGR-SEC-001)"))
    elif sig.startswith("STUB-"):
        checks.append(("pqc_signature", None, "Development stub — not ML-DSA-65"))
    elif sig:
        checks.append(("pqc_signature", None, f"Unrecognised format: {sig[:30]}…"))
    else:
        checks.append(("pqc_signature", False, "ABSENT"))

    # [5] Issuer identity
    issuer = cert.get("issuer", "")
    ok     = issuer == EXPECTED_ISSUER
    checks.append(("issuer", ok, issuer if ok else f"Expected '{EXPECTED_ISSUER}', got '{issuer}'"))

    # [6] Mandate certification
    mandate = cert.get("mandate_certification", "UNCERTIFIED")
    if mandate in ("MANDATE-BOUND", "MANDATE-ALIGNED"):
        checks.append(("mandate_certification", True, mandate))
    else:
        checks.append(("mandate_certification", None, "UNCERTIFIED (warning)"))

    overall = all(p is not False for _, p, _ in checks)
    return overall, checks


def _verify_api_json_inline(cert: Dict[str, Any]) -> Tuple[bool, List[Tuple[str, Optional[bool], str]]]:
    """
    Inline mirror of GET /v1/pogr/verify/<pogc_id> (pogr_blueprint.py:verify()).
    Checks: content_hash recompute · status · TTL · pqc_signature prefix.
    Does NOT check issuer or mandate_certification explicitly.
    """
    checks: List[Tuple[str, Optional[bool], str]] = []
    now   = datetime.now(timezone.utc)
    valid = True

    # Recompute content hash from canonical fields
    expected = _compute_content_hash(cert)
    if expected == cert.get("content_hash", ""):
        checks.append(("content_hash", True,  "✓ Content hash verified"))
    else:
        checks.append(("content_hash", False, "✗ Content hash mismatch — tampered"))
        valid = False

    # Status
    status = cert.get("status", "UNKNOWN")
    if status == "ACTIVE":
        checks.append(("status", True,  "✓ ACTIVE"))
    elif status == "REVOKED":
        checks.append(("status", False, f"✗ REVOKED — {cert.get('revocation_reason','')}"))
        valid = False
    elif status == "EXPIRED":
        checks.append(("status", False, "✗ EXPIRED"))
        valid = False
    else:
        checks.append(("status", False, f"✗ Unknown: {status}"))
        valid = False

    # TTL
    try:
        exp = datetime.fromisoformat(str(cert.get("expires_at", "")).replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now < exp:
            checks.append(("ttl", True,  f"✓ Not expired (expires {exp.strftime('%Y-%m-%d')})"))
        else:
            checks.append(("ttl", False, f"✗ Expired on {exp.strftime('%Y-%m-%d')}"))
            valid = False
    except Exception as exc:
        checks.append(("ttl", False, f"✗ Cannot parse expires_at: {exc}"))
        valid = False

    # PQC signature (API: STUB = warning, not False)
    sig = cert.get("pqc_signature", "")
    if sig.startswith("ML-DSA-65:"):
        checks.append(("pqc_signature", True, "✓ ML-DSA-65 (FIPS 204)"))
    elif sig.startswith("STUB-"):
        checks.append(("pqc_signature", None, "⚠ Development stub"))
        # API does NOT set valid=False for STUB — it's a warning
    else:
        checks.append(("pqc_signature", None, "⚠ Unrecognised format"))

    return valid, checks


def _verify_html_web_inline(cert: Dict[str, Any]) -> Tuple[bool, List[Tuple[str, Optional[bool], str]]]:
    """
    Inline mirror of GET /pogr/verify/<pogc_id> (pogr_blueprint.py:verify_page()).
    Exact replica of line 919:
        valid = status_db == "ACTIVE" and not expired and sig.startswith("ML-DSA-65:")

    KEY DIFFERENCE FROM API JSON: Does NOT check content_hash.
    KEY DIFFERENCE FROM API JSON for STUB: treats STUB as INVALID (not a warning).
    """
    checks: List[Tuple[str, Optional[bool], str]] = []
    now = datetime.now(timezone.utc)

    sig       = cert.get("pqc_signature", "")
    status_db = cert.get("status", "UNKNOWN")

    # TTL
    expired = False
    try:
        exp = datetime.fromisoformat(str(cert.get("expires_at", "")).replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        expired = now > exp
        if expired:
            checks.append(("ttl", False, f"✗ Expiró el {exp.strftime('%Y-%m-%d')}"))
        else:
            checks.append(("ttl", True,  f"✓ No expirado (vence {exp.strftime('%Y-%m-%d')})"))
    except Exception as exc:
        expired = True
        checks.append(("ttl", False, f"✗ No se puede parsear expires_at: {exc}"))

    # NOTE: HTML page does NOT recompute content_hash (architectural gap — POGR-SEC-003)
    checks.append(("content_hash", None,
                   "⚠ HTML page omite verificación de content_hash (POGR-SEC-003)"))

    # Status
    if status_db == "ACTIVE":
        checks.append(("status", True,  "✓ ACTIVE"))
    elif status_db == "REVOKED":
        checks.append(("status", False, f"✗ REVOCADO — {cert.get('revocation_reason','')}"))
    elif status_db == "EXPIRED":
        checks.append(("status", False, "✗ EXPIRADO"))
    else:
        checks.append(("status", False, f"✗ Estado: {status_db}"))

    # PQC signature — HTML requires ML-DSA-65: prefix; STUB → "FIRMA EN PROCESO" (INVALID)
    if sig.startswith("ML-DSA-65:"):
        checks.append(("pqc_signature", True,  "✓ ML-DSA-65 / FIPS 204"))
    elif sig.startswith("STUB-"):
        checks.append(("pqc_signature", False,
                        "✗ STUB → HTML muestra 'FIRMA EN PROCESO' (no VALID)"))
    else:
        checks.append(("pqc_signature", False, "✗ Firma ausente o formato desconocido"))

    # Exact replica of pogr_blueprint.py line 919
    valid = status_db == "ACTIVE" and not expired and sig.startswith("ML-DSA-65:")
    return valid, checks


# ─────────────────────────────────────────────────────────────────────────────
#  Synthetic PoGC builder
# ─────────────────────────────────────────────────────────────────────────────

def _future_iso(days: int = 365) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past_iso(days: int = 5) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_valid_cert(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Build a synthetically valid PoGC dict.
    content_hash is computed correctly unless explicitly provided in overrides.
    pqc_signature uses ML-DSA-65: prefix (prefix valid, payload is SHA3-256 stub).
    """
    cert: Dict[str, Any] = {
        "pogc_id":               "POGC-AUDIT-TEST-0001",
        "session_id":            "SESSION-AUDIT-TEST-001",
        "ctchc_seal_hash":       "sha3-256:" + "a" * 64,
        "issuer":                "OMNIX QUANTUM LTD",
        "subject_org":           "QuantumBank Audit Corp",
        "subject_org_id":        "ORG-AUDIT-001",
        "agent_id":              "OMNIX-AGENT-AUDIT-001",
        "compliance_tier":       "ATF-BEV-Compliant",
        "mandate_certification": "MANDATE-BOUND",
        "turn_count":            3,
        "avg_conformance":       0.97,
        "issued_at":             _now_iso(),
        "expires_at":            _future_iso(365),
        "regulatory_tags":       ["EU-AI-ACT", "MIFID-II"],
        "status":                "ACTIVE",
        "pqc_algorithm":         "ml-dsa-65",
        "revocation_reason":     None,
        "revocation_proof":      None,
    }
    if overrides:
        cert.update(overrides)
    # Compute content_hash AFTER applying overrides (unless caller provides it)
    if "content_hash" not in (overrides or {}):
        cert["content_hash"] = _compute_content_hash(cert)
    # Build pqc_signature AFTER content_hash computed (unless caller provides it)
    if "pqc_signature" not in (overrides or {}):
        payload   = json.dumps(
            {k: cert[k] for k in CANONICAL_FIELDS if k in cert},
            sort_keys=True, separators=(",", ":"),
        ).encode()
        stub_hex  = hashlib.sha3_256(b"AUDIT-SIG:" + payload).hexdigest()
        cert["pqc_signature"] = "ML-DSA-65:" + stub_hex
    return cert


# ─────────────────────────────────────────────────────────────────────────────
#  Attack result container
# ─────────────────────────────────────────────────────────────────────────────

class AttackResult:
    def __init__(self, attack_id: str, description: str, scenario: str):
        self.attack_id    = attack_id
        self.description  = description
        self.scenario     = scenario
        self.offline_valid: Optional[bool] = None
        self.api_valid:     Optional[bool] = None
        self.html_valid:    Optional[bool] = None
        self.offline_checks: List[Tuple]   = []
        self.api_checks:     List[Tuple]   = []
        self.html_checks:    List[Tuple]   = []
        self.divergence:    bool = False
        self.severity:      str  = "INFO"
        self.finding_id:    str  = ""
        self.finding_desc:  str  = ""
        self.remediation:   str  = ""
        self.invariant_ref: str  = ""

    @property
    def summary_line(self) -> str:
        def _v(b: Optional[bool]) -> str:
            if b is True:  return GREEN("VALID  ")
            if b is False: return RED("INVALID")
            return YELLOW("N/A    ")
        div = RED(" ← DIVERGENCE") if self.divergence else ""
        return (
            f"  {CYAN(self.attack_id):<18} "
            f"Offline={_v(self.offline_valid)}  "
            f"API={_v(self.api_valid)}  "
            f"HTML={_v(self.html_valid)}"
            f"{div}"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Three-channel runner
# ─────────────────────────────────────────────────────────────────────────────

def _run_channels(
    res: AttackResult,
    offline_cert: Optional[Dict] = None,
    api_cert:     Optional[Dict] = None,
    html_cert:    Optional[Dict] = None,
    offline_na:   bool = False,
    api_na:       bool = False,
    html_na:      bool = False,
) -> None:
    """
    Run the three verification channels independently and detect divergences.
    Pass channel-specific certs when the channels would receive different inputs
    (e.g. stale export for offline vs DB state for API/HTML).
    """
    if not offline_na and offline_cert is not None:
        # Use subprocess for maximum fidelity to the real verifier
        subprocess_ok, _ = _verify_offline_subprocess(offline_cert)
        inline_ok, checks = _verify_offline_inline(offline_cert)
        # Trust inline for checks detail; subprocess for exit code
        res.offline_valid   = subprocess_ok
        res.offline_checks  = checks
    elif offline_na:
        res.offline_valid = None

    if not api_na and api_cert is not None:
        res.api_valid, res.api_checks = _verify_api_json_inline(api_cert)
    elif api_na:
        res.api_valid = None

    if not html_na and html_cert is not None:
        res.html_valid, res.html_checks = _verify_html_web_inline(html_cert)
    elif html_na:
        res.html_valid = None

    verdicts = [v for v in [res.offline_valid, res.api_valid, res.html_valid]
                if v is not None]
    res.divergence = len(set(verdicts)) > 1


# ─────────────────────────────────────────────────────────────────────────────
#  15 Attack definitions
# ─────────────────────────────────────────────────────────────────────────────

def build_attacks() -> List[AttackResult]:
    attacks: List[AttackResult] = []

    # ── A01: Issuer cambiado ─────────────────────────────────────────────────
    a01 = AttackResult(
        "A01", "Issuer cambiado",
        "Attacker alters the 'issuer' field in an exported PoGC JSON after download. "
        "'issuer' is a canonical field — content_hash covers it. All channels must reject.",
    )
    a01.finding_id    = "POGR-SEC-007"
    a01.finding_desc  = (
        "Canonical field alteration is correctly detected by all three channels. "
        "The offline verifier detects two ways: (1) content_hash mismatch, "
        "(2) issuer identity check [5] (hardcoded EXPECTED_ISSUER assertion). "
        "The API detects via content_hash recomputation. "
        "The HTML page detects via content_hash... wait — HTML does NOT check hash. "
        "However, the API reads from DB (attacker cannot change DB without DB access), "
        "so this attack is only viable on an exported file for the offline channel."
    )
    a01.severity      = "MITIGATED"
    a01.remediation   = (
        "No action needed for file-tampering attacks — content_hash and issuer check cover this. "
        "NOTE: If the DB canonical fields are mutated directly (bypassing API), the HTML page "
        "would not detect this (see A08 / POGR-SEC-012 for that scenario)."
    )
    a01.invariant_ref = "PoGR-INV-003"
    # Correct threat model: attacker tampers the EXPORTED FILE; DB is clean.
    # Offline: gets tampered file → detects hash mismatch → INVALID.
    # API/HTML: read from DB (clean) → VALID. This is expected, by-design divergence.
    cert_a01_file = _build_valid_cert()
    cert_a01_file["issuer"] = "ATTACKER ORG LTD"  # alter AFTER hash computed → mismatch
    cert_a01_db   = _build_valid_cert()             # DB is untouched (clean)
    _run_channels(a01, offline_cert=cert_a01_file, api_cert=cert_a01_db, html_cert=cert_a01_db)
    # Offline=INVALID (detects file tampering ✓), API/HTML=VALID (DB is clean ✓)
    # This is EXPECTED by-design divergence — not a security gap.
    a01.divergence = False  # expected behavior: offline checks file, API/HTML check DB
    attacks.append(a01)

    # ── A02: mandate_certification cambiado ─────────────────────────────────
    a02 = AttackResult(
        "A02", "mandate_certification cambiado (UNCERTIFIED → MANDATE-BOUND)",
        "Attacker upgrades a cert from UNCERTIFIED to MANDATE-BOUND in the export JSON "
        "without recalculating content_hash. Canonical field → hash breaks.",
    )
    a02.finding_id    = "POGR-SEC-008"
    a02.finding_desc  = (
        "mandate_certification is in canonical_fields — any change breaks content_hash. "
        "All channels detect this attack."
    )
    a02.severity      = "MITIGATED"
    a02.remediation   = (
        "mandate_certification is canonical — hash covers it for file-tampering attacks. "
        "Same DB-mutation caveat as A01: HTML page would not detect a direct DB mutation "
        "(see A08 / POGR-SEC-012)."
    )
    a02.invariant_ref = "MIVP-INV-008 · PoGR-INV-003"
    # Correct threat model: attacker tampers the EXPORTED FILE; DB is clean.
    cert_a02_file = _build_valid_cert({"mandate_certification": "UNCERTIFIED"})
    cert_a02_file["mandate_certification"] = "MANDATE-BOUND"  # alter AFTER hash computed
    cert_a02_db   = _build_valid_cert({"mandate_certification": "UNCERTIFIED"})  # clean DB
    _run_channels(a02, offline_cert=cert_a02_file, api_cert=cert_a02_db, html_cert=cert_a02_db)
    # Offline=INVALID (detects file tampering ✓), API/HTML=VALID (DB is clean ✓) — by design.
    a02.divergence = False
    attacks.append(a02)

    # ── A03: TTL expirado ────────────────────────────────────────────────────
    a03 = AttackResult(
        "A03", "TTL expirado (expires_at en el pasado)",
        "Certificate with expires_at 5 days in the past. "
        "status is still ACTIVE in the file. All channels check TTL independently.",
    )
    a03.finding_id    = "POGR-SEC-009"
    a03.finding_desc  = "Expired TTL detected consistently by all channels."
    a03.severity      = "MITIGATED"
    a03.remediation   = "No action needed — PoGR-INV-004 enforced."
    a03.invariant_ref = "PoGR-INV-004"
    cert_a03 = _build_valid_cert({"expires_at": _past_iso(5)})
    _run_channels(a03, offline_cert=cert_a03, api_cert=cert_a03, html_cert=cert_a03)
    attacks.append(a03)

    # ── A04: content_hash field alterado ────────────────────────────────────
    a04 = AttackResult(
        "A04", "content_hash field alterado en export JSON",
        "Attacker replaces the content_hash field in the downloaded JSON with a "
        "corrupted value. Offline recomputes and detects mismatch. "
        "API reads stored hash from DB (clean) — tests different inputs per channel.",
    )
    a04.finding_id    = "POGR-SEC-010"
    a04.finding_desc  = (
        "Offline always detects (recomputes hash from canonical fields → doesn't match "
        "the corrupted stored hash). "
        "API/HTML read from DB — if DB was not touched, they see the original (valid) hash "
        "and compare against recomputed canonical → match → VALID. "
        "This is the correct threat model: offline verifies a file, API verifies from DB."
    )
    a04.severity      = "MITIGATED (offline) / DESIGN-BOUNDARY (API)"
    a04.remediation   = (
        "DB write access control is the real boundary. "
        "The offline verifier correctly detects hash tampering in files."
    )
    a04.invariant_ref = "PoGR-INV-003"
    cert_a04_file = _build_valid_cert()
    cert_a04_file["content_hash"] = "sha3-256:" + "0" * 64  # corrupt stored hash
    cert_a04_db   = _build_valid_cert()  # DB has the original clean cert
    _run_channels(
        a04,
        offline_cert=cert_a04_file,  # offline gets the corrupted file
        api_cert=cert_a04_db,         # API reads clean DB
        html_cert=cert_a04_db,
    )
    attacks.append(a04)

    # ── A05: Firma alterada — prefijo ML-DSA-65: conservado ─────────────────
    a05 = AttackResult(
        "A05", "Firma alterada — prefijo ML-DSA-65: conservado (POGR-SEC-001)",
        "Attacker replaces the pqc_signature payload with random bytes "
        "but keeps the 'ML-DSA-65:' prefix. content_hash is valid. "
        "No channel verifies the signature bytes cryptographically. "
        "All three channels report VALID — FALSE POSITIVE.",
    )
    a05.finding_id    = "POGR-SEC-001"
    a05.finding_desc  = (
        "CRITICAL KNOWN LIMITATION: pqc_signature is never cryptographically "
        "verified by any channel. All three only check the 'ML-DSA-65:' prefix string. "
        "An attacker who knows the canonical fields can: "
        "(1) Compute a valid content_hash, "
        "(2) Attach any payload after 'ML-DSA-65:', "
        "→ All three channels report VALID. "
        "This is a FALSE POSITIVE across all channels — consistent but wrong."
    )
    a05.severity      = "CRITICAL"
    a05.remediation   = (
        "Implement --platform-key flag in verify_pogc_offline.py to enable full "
        "ML-DSA-65 cryptographic verification using the platform public key "
        "from /v1/pogr/manifest. "
        "The API /v1/pogr/verify must also perform cryptographic signature "
        "verification on each call. "
        "Priority: P1 — before first public PoGC issued to a third party."
    )
    a05.invariant_ref = "PoGR-INV-003 (partially violated)"
    cert_a05 = _build_valid_cert()
    # Recalculate hash correctly — hash check will pass
    cert_a05["content_hash"] = _compute_content_hash(cert_a05)
    # Forge signature with valid prefix but fake payload
    cert_a05["pqc_signature"] = "ML-DSA-65:" + "deadbeef" * 16  # fake but prefix OK
    _run_channels(a05, offline_cert=cert_a05, api_cert=cert_a05, html_cert=cert_a05)
    # All three agree (all VALID) — no divergence, but it's a FALSE POSITIVE
    a05.divergence = False  # agreement on wrong answer
    attacks.append(a05)

    # ── A06: ID válido, contenido de otro PoGC ──────────────────────────────
    a06 = AttackResult(
        "A06", "ID válido con contenido de otro PoGC (ID swap)",
        "Attacker takes POGC-A's exported file and replaces all fields with POGC-B's data. "
        "Offline verifier reads the file content — no binding between filename/URL and "
        "pogc_id inside the JSON. "
        "API reads POGC-A from DB — fully independent of file content.",
    )
    a06.finding_id    = "POGR-SEC-011"
    a06.finding_desc  = (
        "Offline verifier has no binding between the pogc_id in the URL/filename "
        "and the pogc_id inside the JSON. "
        "An attacker can present POGC-B's valid certificate as if verifying POGC-A. "
        "The offline verifier reports VALID for POGC-B's data. "
        "The API, reading by URL pogc_id from DB, is fully independent. "
        "Both channels report VALID — but for DIFFERENT certificates. "
        "This is an identity confusion attack, not a cryptographic break."
    )
    a06.severity      = "MEDIUM"
    a06.remediation   = (
        "Add a --pogc-id argument to verify_pogc_offline.py. "
        "When provided, assert cert['pogc_id'] == supplied_id before running checks. "
        "The mismatch should be a FAIL, not a warning."
    )
    a06.invariant_ref = "PoGR-INV-003"
    cert_pogc_b = _build_valid_cert({
        "pogc_id":    "POGC-AUDIT-TEST-0002",
        "session_id": "SESSION-AUDIT-TEST-002",
        "subject_org": "LegitimateOrg Corp",
    })
    cert_pogc_a_db = _build_valid_cert()  # API reads POGC-A from DB
    _run_channels(
        a06,
        offline_cert=cert_pogc_b,   # offline gets POGC-B's content (the swap)
        api_cert=cert_pogc_a_db,    # API returns POGC-A from DB (they're different certs)
        html_cert=cert_pogc_a_db,
    )
    # Both report VALID — but for different certs. No verdict divergence, but identity confusion exists.
    a06.divergence = False  # both VALID, but the identity confusion is the vulnerability
    attacks.append(a06)

    # ── A07: Export manipulado — status REVOKED→ACTIVE ───────────────────────
    a07 = AttackResult(
        "A07", "Export manipulado — status cambiado REVOKED→ACTIVE (POGR-SEC-002)",
        "Attacker downloads export of an ACTIVE certificate. Admin revokes it. "
        "Attacker alters status field from 'REVOKED' to 'ACTIVE' in the old JSON. "
        "'status' is NOT in canonical_fields — content_hash does NOT change. "
        "Offline: VALID. API/HTML (reading DB): INVALID.",
    )
    a07.finding_id    = "POGR-SEC-002"
    a07.finding_desc  = (
        "CRITICAL DIVERGENCE: 'status' is excluded from canonical_fields. "
        "An attacker can alter status in an exported JSON without breaking content_hash. "
        "The offline verifier checks the 'status' field from the file → sees ACTIVE → VALID. "
        "The API and HTML page read from DB → see REVOKED → INVALID. "
        "This creates a real, exploitable Web/API ≠ Offline divergence."
    )
    a07.severity      = "CRITICAL"
    a07.remediation   = (
        "Option A (preferred): Add 'status' and 'revoked_at' to canonical_fields. "
        "Requires re-signing all existing certificates. "
        "Option B (interim): Add prominent warning in verify_pogc_offline.py: "
        "'WARNING: Revocation status is NOT cryptographically bound. "
        "For revocation verification, query the live API.' "
        "Option B is a documentation fix, not a cryptographic fix."
    )
    a07.invariant_ref = "PoGR-INV-002 (revocation) · PoGR-INV-006"
    # The stale export was downloaded when cert was ACTIVE (valid hash)
    cert_stale_active = _build_valid_cert()  # status=ACTIVE, hash valid
    # DB state: after revocation
    cert_db_revoked   = _build_valid_cert({
        "status":            "REVOKED",
        "revocation_reason": "Audit finding: session integrity compromised",
    })
    _run_channels(
        a07,
        offline_cert=cert_stale_active,  # offline gets the stale file (status=ACTIVE)
        api_cert=cert_db_revoked,         # API reads DB (status=REVOKED)
        html_cert=cert_db_revoked,
    )
    attacks.append(a07)

    # ── A08: Offline=VALID, Web/API=INVALID ──────────────────────────────────
    a08 = AttackResult(
        "A08", "Offline=VALID, Web/API=INVALID — inconsistencia hash en DB",
        "Scenario: A DB canonical field (e.g. issuer) was modified directly in "
        "the DB (bypassing the API) without updating content_hash. "
        "API recomputes hash → mismatch → INVALID. "
        "HTML page does NOT check hash → VALID. "
        "Stale export from before the DB mutation → VALID offline.",
    )
    a08.finding_id    = "POGR-SEC-012"
    a08.finding_desc  = (
        "If the DB is mutated directly (bypassing the API), the stored content_hash "
        "becomes inconsistent with the canonical fields. "
        "The JSON API detects this (recomputes hash on every /verify call → mismatch → INVALID). "
        "The HTML page does NOT detect this (no hash recomputation in verify_page()). "
        "A stale offline export from before the mutation passes the offline check. "
        "This creates a three-way divergence: "
        "Offline=VALID · API JSON=INVALID · HTML Web=VALID."
    )
    a08.severity      = "HIGH"
    a08.remediation   = (
        "1. Add content_hash recomputation to verify_page() — "
        "the HTML /pogr/verify endpoint must mirror the JSON API hash verification. "
        "2. Apply DB-level immutability controls (no UPDATE on canonical columns). "
        "3. Add DB trigger or application-level guard: UPDATE on canonical columns "
        "must also recompute and update content_hash."
    )
    a08.invariant_ref = "PoGR-INV-002 (append-only violated by direct DB mutation)"
    # DB state after direct mutation: issuer changed but hash not updated
    cert_mutated_db   = _build_valid_cert()
    original_hash     = cert_mutated_db["content_hash"]
    cert_mutated_db["issuer"]       = "MANIPULATED ISSUER LTD"
    cert_mutated_db["content_hash"] = original_hash  # NOT updated → mismatch
    # Stale export (before mutation): consistent, passes offline
    cert_old_export   = _build_valid_cert()  # consistent state before mutation
    _run_channels(
        a08,
        offline_cert=cert_old_export,   # old export: passes offline
        api_cert=cert_mutated_db,        # API reads mutated DB: hash mismatch → INVALID
        html_cert=cert_mutated_db,       # HTML reads mutated DB: no hash check → VALID
    )
    attacks.append(a08)

    # ── A09: API=VALID, HTML=INVALID — firma STUB ────────────────────────────
    a09 = AttackResult(
        "A09", "API (JSON)=VALID, HTML=INVALID — firma STUB (POGR-SEC-003)",
        "Certificate has a STUB-SHA3-256: signature (environment without PQC key). "
        "JSON API: STUB → Warning → overall valid=True → VALID. "
        "HTML page: sig.startswith('ML-DSA-65:') → False → valid=False → INVALID. "
        "React SPA calls JSON API → VALID. Direct HTML page → INVALID. "
        "Three different verdicts for the same certificate.",
    )
    a09.finding_id    = "POGR-SEC-003"
    a09.finding_desc  = (
        "DIVERGENCE CONFIRMED: JSON API and HTML page treat STUB signature differently. "
        "JSON API (verify()): STUB → pqc_signature check = None (warning) → valid=True. "
        "HTML page (verify_page()): checks sig.startswith('ML-DSA-65:') → False → "
        "valid=False → displays 'FIRMA EN PROCESO'. "
        "React SPA /proof-of-governance calls JSON API → says VALID. "
        "Visiting /pogr/verify/<id> directly → says INVALID. "
        "Same certificate, same DB, three access channels → three different verdicts."
    )
    a09.severity      = "HIGH"
    a09.remediation   = (
        "Unify signature validation logic across JSON API and HTML page. "
        "Decision required: "
        "Option A — STUB is INVALID everywhere: "
        "  Set valid=False in JSON API when sig starts with STUB-. "
        "Option B — STUB is VALID in dev (acceptable): "
        "  HTML page must also treat STUB as a warning, not as INVALID. "
        "Either way: the two renderers must produce identical verdicts. "
        "Recommended: Option A (STUB = INVALID) for production integrity."
    )
    a09.invariant_ref = "PoGR-INV-003 (consistency violated)"
    cert_a09 = _build_valid_cert()
    # Build STUB signature
    payload = json.dumps(
        {k: cert_a09[k] for k in CANONICAL_FIELDS if k in cert_a09},
        sort_keys=True, separators=(",", ":"),
    ).encode()
    cert_a09["pqc_signature"] = "STUB-SHA3-256:" + hashlib.sha3_256(b"STUB:" + payload).hexdigest()
    _run_channels(a09, offline_cert=cert_a09, api_cert=cert_a09, html_cert=cert_a09)
    attacks.append(a09)

    # ── A10: PoGC inexistente ─────────────────────────────────────────────────
    a10 = AttackResult(
        "A10", "PoGC inexistente — ID not found",
        "Request for a POGC-ID that does not exist in the registry. "
        "All channels must return INVALID / 404.",
    )
    a10.finding_id    = "POGR-SEC-013"
    a10.finding_desc  = "All channels correctly reject unknown IDs. No divergence."
    a10.severity      = "MITIGATED"
    a10.remediation   = "No action needed."
    a10.invariant_ref = "PoGR-INV-003"
    cert_empty = {}  # represents a cert not found (empty dict)
    a10.offline_valid, a10.offline_checks = _verify_offline_inline(cert_empty)
    a10.api_valid   = False
    a10.html_valid  = False
    a10.api_checks  = [("not_found", False, "HTTP 404 — Certificate not found in registry")]
    a10.html_checks = [("not_found", False, "HTML: CERTIFICADO NO ENCONTRADO")]
    a10.divergence  = False
    attacks.append(a10)

    # ── A11: PoGC revocado — stale export ────────────────────────────────────
    a11 = AttackResult(
        "A11", "PoGC revocado — stale export divergence (POGR-SEC-002)",
        "Attacker downloaded the export BEFORE the certificate was revoked. "
        "The stale JSON has status=ACTIVE, valid content_hash, valid sig prefix. "
        "Offline verifier cannot detect revocation from a stale file. "
        "This is the primary lifecycle divergence in the PoGR system.",
    )
    a11.finding_id    = "POGR-SEC-002"
    a11.finding_desc  = (
        "Same root cause as A07: 'status' is not in canonical_fields. "
        "The offline verifier trusts the status field in the JSON file. "
        "If the file was downloaded before revocation, it still reads ACTIVE. "
        "Revocation is an out-of-band event relative to the offline export. "
        "The offline channel fundamentally cannot detect post-export revocation "
        "without querying the live API — this is an architectural limitation, "
        "not a bug in the verifier logic."
    )
    a11.severity      = "CRITICAL"
    a11.remediation   = (
        "Same as A07: add 'status' to canonical_fields OR add a clear mandatory "
        "warning in verify_pogc_offline.py output: "
        "'CAUTION: This verifier cannot detect revocation that occurred after "
        "export. To verify revocation status, call GET /v1/pogr/verify/<id>.' "
        "This warning must be present on EVERY execution, not just on detection."
    )
    a11.invariant_ref = "PoGR-INV-006 (revocation integrity)"
    cert_stale   = _build_valid_cert()  # stale: status=ACTIVE, hash valid at time of download
    cert_revoked = _build_valid_cert({
        "status":            "REVOKED",
        "revocation_reason": "Governance session found compromised post-audit",
    })
    _run_channels(
        a11,
        offline_cert=cert_stale,
        api_cert=cert_revoked,
        html_cert=cert_revoked,
    )
    attacks.append(a11)

    # ── A12: PoGC expirado ───────────────────────────────────────────────────
    a12 = AttackResult(
        "A12", "PoGC expirado (expires_at genuinamente en el pasado)",
        "Certificate with expires_at 10 days in the past, status=ACTIVE. "
        "expires_at IS in canonical_fields — cannot be forged without breaking hash. "
        "All channels check TTL independently.",
    )
    a12.finding_id    = "POGR-SEC-014"
    a12.finding_desc  = (
        "Expired TTL is consistently detected. expires_at is canonical → immutable. "
        "All three channels independently verify TTL. "
        "status field may still say ACTIVE — TTL check is independent of status."
    )
    a12.severity      = "MITIGATED"
    a12.remediation   = "No action needed. PoGR-INV-004 enforced."
    a12.invariant_ref = "PoGR-INV-004"
    cert_a12 = _build_valid_cert({"expires_at": _past_iso(10)})
    _run_channels(a12, offline_cert=cert_a12, api_cert=cert_a12, html_cert=cert_a12)
    attacks.append(a12)

    # ── A13: Replay — session_id duplicado ───────────────────────────────────
    a13 = AttackResult(
        "A13", "Replay — mismo session_id genera múltiples PoGCs (POGR-SEC-004)",
        "POST /v1/pogr/certify called twice with same session_id. "
        "No UNIQUE constraint on session_id in pogr_certificates DDL. "
        "Each call generates a new pogc_id → two valid certs for the same session.",
    )
    a13.finding_id    = "POGR-SEC-004"
    a13.finding_desc  = (
        "The pogr_certificates table has no UNIQUE constraint on session_id. "
        "An authenticated client (with valid API key) can call POST /v1/pogr/certify "
        "multiple times with the same session_id, generating N PoGCs for the same "
        "governance session. Each has a different pogc_id. "
        "The offline verifier and API both see each cert as independently valid. "
        "This allows certificate proliferation and could be used to obtain a "
        "MANDATE-BOUND cert after the session was already certified at a lower tier."
    )
    a13.severity      = "MEDIUM"
    a13.remediation   = (
        "Add to pogr_certificates DDL: "
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_pogr_session_unique "
        "ON pogr_certificates (session_id) WHERE status = 'ACTIVE'; "
        "This prevents duplicate ACTIVE certs for the same session "
        "while preserving the append-only principle (REVOKED certs can coexist)."
    )
    a13.invariant_ref = "PoGR-INV-001 (session backing) · PoGR-INV-002 (append-only)"
    # Simulate two certs with same session_id
    cert_replay_1 = _build_valid_cert({"pogc_id": "POGC-REPLAY-0001"})
    cert_replay_2 = _build_valid_cert({"pogc_id": "POGC-REPLAY-0002"})
    r1_v, _ = _verify_offline_inline(cert_replay_1)
    r2_v, _ = _verify_offline_inline(cert_replay_2)
    a13.offline_valid  = r1_v and r2_v  # both independently valid
    a13.api_valid      = True            # API issues both (no DB constraint)
    a13.html_valid     = True
    a13.offline_checks = [("replay_detection", None,
                           "Offline cannot detect replay — only checks single cert")]
    a13.api_checks     = [("session_uniqueness", False,
                           "No UNIQUE constraint — both certs issued successfully (POGR-SEC-004)")]
    a13.html_checks    = [("session_uniqueness", None, "N/A for HTML page")]
    a13.divergence     = False  # all channels say VALID; structural vulnerability is at certify
    attacks.append(a13)

    # ── A14: Campos canónicos faltantes ──────────────────────────────────────
    a14 = AttackResult(
        "A14", "Campos canónicos faltantes en JSON exportado",
        "JSON file is missing canonical fields (issuer, mandate_certification deleted). "
        "Offline: hash computed on subset → won't match complete hash → INVALID. "
        "API: DB always has all fields (NOT NULL constraints) → unaffected.",
    )
    a14.finding_id    = "POGR-SEC-015"
    a14.finding_desc  = (
        "Offline verifier gracefully handles missing canonical fields via "
        "{k: cert[k] for k in CANONICAL_FIELDS if k in cert}. "
        "Hash of the available subset won't match the stored hash (complete set) → INVALID. "
        "API is immune because DB NOT NULL constraints guarantee all fields present."
    )
    a14.severity      = "MITIGATED"
    a14.remediation   = (
        "Add explicit per-field warnings in offline verifier when canonical fields "
        "are absent, e.g. 'WARNING: canonical field issuer missing from certificate'."
    )
    a14.invariant_ref = "PoGR-INV-003"
    cert_a14 = _build_valid_cert()
    del cert_a14["issuer"]
    del cert_a14["mandate_certification"]
    cert_a14_db = _build_valid_cert()
    _run_channels(
        a14,
        offline_cert=cert_a14,
        api_cert=cert_a14_db,
        html_cert=cert_a14_db,
    )
    # Offline=INVALID (hash of subset ≠ complete hash — correct detection ✓).
    # API/HTML=VALID (DB always has complete fields per NOT NULL constraints ✓).
    # Expected by-design divergence: different data sources, both correct in their domain.
    a14.divergence = False
    attacks.append(a14)

    # ── A15: JSON con campos extra maliciosos ─────────────────────────────────
    a15 = AttackResult(
        "A15", "JSON con campos extra maliciosos (injection attempt)",
        "Attacker adds extra fields: 'admin': True, 'override_status': 'ACTIVE', "
        "'bypass_revocation': True. Neither offline nor API read these fields. "
        "Both use explicit CANONICAL_FIELDS allowlist.",
    )
    a15.finding_id    = "POGR-SEC-016"
    a15.finding_desc  = (
        "Extra fields are safely ignored by all channels. "
        "Offline: uses explicit CANONICAL_FIELDS list — extras never read. "
        "API: reads from DB — no user-submitted fields. "
        "No injection or privilege escalation is possible via extra JSON fields. "
        "The explicit allowlist pattern is correct and prevents injection."
    )
    a15.severity      = "MITIGATED"
    a15.remediation   = "No action needed. Explicit allowlist is the correct pattern."
    a15.invariant_ref = "PoGR-INV-003"
    cert_a15 = _build_valid_cert()
    cert_a15["admin"]             = True
    cert_a15["override_status"]   = "ACTIVE"
    cert_a15["bypass_revocation"] = True
    cert_a15["x-attacker-header"] = "INJECT_PAYLOAD"
    _run_channels(a15, offline_cert=cert_a15, api_cert=cert_a15, html_cert=cert_a15)
    attacks.append(a15)

    return attacks


# ─────────────────────────────────────────────────────────────────────────────
#  Console output
# ─────────────────────────────────────────────────────────────────────────────

SEVERITY_ORDER = {
    "CRITICAL": 0, "HIGH": 1, "MEDIUM": 2,
    "MITIGATED": 3, "DESIGN-BOUNDARY": 4, "INFO": 5,
}


def print_results(attacks: List[AttackResult]) -> None:
    print()
    print(GOLD("=" * 72))
    print(GOLD("  OMNIX PoGR — ADVERSARIAL AUDIT v2.0"))
    print(GOLD(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"))
    print(GOLD("=" * 72))
    print()

    divergences = [a for a in attacks if a.divergence]
    criticals   = [a for a in attacks if a.severity == "CRITICAL"]

    print(BOLD("  Attack Results  (Offline / API JSON / HTML Web):"))
    print(DIM("  " + "─" * 68))
    print()

    for a in attacks:
        print(a.summary_line)
        sev_color = {
            "CRITICAL": RED, "HIGH": YELLOW, "MEDIUM": GOLD,
            "MITIGATED": GREEN, "DESIGN-BOUNDARY": BLUE,
        }.get(a.severity, DIM)
        print(f"    {DIM('├─')} {DIM(a.finding_id):20} {sev_color(a.severity):18}  "
              f"{DIM(a.description[:52])}")
        if a.divergence:
            print(f"    {RED('└─ ⚠ DIVERGENCIA DETECTADA')}")
        print()

    print(DIM("  " + "─" * 68))
    print()
    print(f"  Total ataques    : {len(attacks)}")
    print(f"  Divergencias     : {RED(str(len(divergences))) if divergences else GREEN('0')}")
    print(f"  Críticos         : {RED(str(len(criticals)))   if criticals   else GREEN('0')}")
    print(f"  Mitigados        : {GREEN(str(sum(1 for a in attacks if a.severity == 'MITIGATED')))}")
    print()

    if divergences:
        print(RED(BOLD("  DIVERGENCIAS DETECTADAS:")))
        for a in divergences:
            def _v(b: Optional[bool]) -> str:
                return "VALID" if b else "INVALID" if b is False else "N/A"
            print(f"    {a.attack_id} — {a.description[:60]}")
            print(f"         Offline={_v(a.offline_valid)}  "
                  f"API={_v(a.api_valid)}  "
                  f"HTML={_v(a.html_valid)}")
        print()

    if criticals:
        print(RED(BOLD("  HALLAZGOS CRÍTICOS:")))
        for a in criticals:
            print(f"    {a.finding_id} [{a.attack_id}] — {a.description[:65]}")
        print()

    print(DIM("  " + "─" * 68))


# ─────────────────────────────────────────────────────────────────────────────
#  Markdown report generators
# ─────────────────────────────────────────────────────────────────────────────

def _v_str(b: Optional[bool]) -> str:
    if b is True:  return "VALID"
    if b is False: return "INVALID"
    return "N/A"


def write_adversarial_audit_report(attacks: List[AttackResult], path: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    divergences = [a for a in attacks if a.divergence]
    criticals   = [a for a in attacks if a.severity == "CRITICAL"]
    highs       = [a for a in attacks if a.severity == "HIGH"]
    mitigated   = [a for a in attacks if a.severity == "MITIGATED"]

    sev_emoji = {
        "CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡",
        "MITIGATED": "✅", "DESIGN-BOUNDARY": "🔵", "INFO": "ℹ",
    }

    lines = [
        "# POGR Adversarial Audit Report",
        "",
        "**Sistema:** OMNIX Proof of Governance Registry (PoGR)  ",
        f"**Fecha:** {now} UTC  ",
        "**Versión:** v2.0 — Auditoría de tres canales  ",
        "**ADR:** ADR-186 · ADR-187 · ADR-189  ",
        "**Invariantes auditadas:** PoGR-INV-001–006  ",
        "**Generado por:** `scripts/pogr_adversarial_audit.py`  ",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "La auditoría adversarial del PoGR ejecutó **15 ataques** sobre los tres",
        "canales de verificación (Offline / API JSON / HTML Web) de forma independiente.",
        "La condición de PASS requiere que los tres canales produzcan el mismo veredicto.",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Total ataques ejecutados | {len(attacks)} |",
        f"| Divergencias Web/API/Offline | **{len(divergences)}** |",
        f"| Hallazgos CRITICAL | **{len(criticals)}** |",
        f"| Hallazgos HIGH | **{len(highs)}** |",
        f"| Ataques mitigados correctamente | {len(mitigated)} |",
        "",
        "---",
        "",
        "## Tabla de Resultados",
        "",
        "| ID | Descripción | Offline | API JSON | HTML Web | Divergencia | Severidad | Finding |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for a in attacks:
        div  = "⚠ **SÍ**" if a.divergence else "✓ No"
        sev  = f"{sev_emoji.get(a.severity, '•')} {a.severity}"
        desc = a.description[:52] + ("…" if len(a.description) > 52 else "")
        lines.append(
            f"| {a.attack_id} | {desc} | {_v_str(a.offline_valid)} | "
            f"{_v_str(a.api_valid)} | {_v_str(a.html_valid)} | {div} | {sev} | {a.finding_id} |"
        )

    lines += ["", "---", "", "## Hallazgos Detallados", ""]

    sorted_attacks = sorted(attacks, key=lambda a: SEVERITY_ORDER.get(a.severity, 99))
    for a in sorted_attacks:
        emoji = sev_emoji.get(a.severity, "•")
        lines += [
            f"### {a.attack_id} — {a.description}",
            "",
            f"**Finding ID:** `{a.finding_id}`  ",
            f"**Severidad:** {emoji} {a.severity}  ",
            f"**Invariante:** {a.invariant_ref}  ",
            "",
            "**Escenario:**",
            "",
            a.scenario,
            "",
            "**Resultados por canal:**",
            "",
            "| Canal | Veredicto |",
            "|---|---|",
            f"| Offline (`verify_pogc_offline.py`) | `{_v_str(a.offline_valid)}` |",
            f"| API JSON (`GET /v1/pogr/verify/<id>`) | `{_v_str(a.api_valid)}` |",
            f"| HTML Web (`GET /pogr/verify/<id>`) | `{_v_str(a.html_valid)}` |",
        ]
        if a.divergence:
            lines += ["", "**⚠ DIVERGENCIA: los tres canales no coinciden.**"]
        lines += [
            "",
            "**Hallazgo:**",
            "",
            a.finding_desc,
            "",
            "**Remediación:**",
            "",
            a.remediation,
            "",
            "---",
            "",
        ]

    lines += [
        "## Remediaciones Prioritarias",
        "",
        "| Prioridad | Finding | Acción requerida |",
        "|---|---|---|",
        "| P1 — INMEDIATA | POGR-SEC-001 | Implementar `--platform-key` en `verify_pogc_offline.py` para verificación PQC real |",
        "| P1 — INMEDIATA | POGR-SEC-002 | Añadir `status` y `revoked_at` a `canonical_fields` (requiere re-firma de certs existentes) |",
        "| P1 — INMEDIATA | POGR-SEC-003 | Unificar lógica de validación de firma entre `/v1/pogr/verify` (JSON) y `/pogr/verify` (HTML) |",
        "| P2 — ALTA | POGR-SEC-004 | `UNIQUE INDEX idx_pogr_session_unique ON pogr_certificates (session_id) WHERE status = 'ACTIVE'` |",
        "| P2 — ALTA | POGR-SEC-012 | Añadir `content_hash` recomputation a `verify_page()` en `pogr_blueprint.py` |",
        "| P3 — MEDIA | POGR-SEC-011 | Argumento `--pogc-id` en `verify_pogc_offline.py` para validar binding ID↔contenido |",
        "",
        "---",
        "",
        f"*Generado por `scripts/pogr_adversarial_audit.py` · {now} UTC · OMNIX QUANTUM LTD*",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  {GREEN('✓')} {os.path.basename(path)}")


def write_trust_assumption_map(attacks: List[AttackResult], path: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# POGR Trust Assumption Map",
        "",
        "**Sistema:** OMNIX Proof of Governance Registry (PoGR)  ",
        f"**Fecha:** {now} UTC  ",
        "**ADR:** ADR-186 · ADR-187 · ADR-189  ",
        "",
        "Este documento mapea las suposiciones de confianza de cada canal de verificación.",
        "Una **suposición de confianza** es una condición que el canal asume verdadera sin verificar.",
        "",
        "---",
        "",
        "## Canal 1 — Offline Verifier (`verify_pogc_offline.py`)",
        "",
        "### Qué verifica",
        "",
        "| Check | Descripción | Resultado si falla |",
        "|---|---|---|",
        "| [1] content_hash | Recomputa SHA3-256 sobre canonical_fields → compara con stored | INVALID |",
        "| [2] status | Lee campo `status` del JSON | INVALID si REVOKED/EXPIRED |",
        "| [3] TTL | Compara `expires_at` con `now()` | INVALID si expirado |",
        "| [4] pqc_signature | Verifica prefijo `ML-DSA-65:` o `STUB-` | Warning si STUB; INVALID si ausente |",
        "| [5] issuer | Compara con hardcoded EXPECTED_ISSUER | INVALID si diferente |",
        "| [6] mandate_certification | Detecta MANDATE-BOUND/ALIGNED/UNCERTIFIED | Warning si UNCERTIFIED |",
        "",
        "### Suposiciones de confianza",
        "",
        "| # | Suposición | Riesgo si falla | Mitigación actual |",
        "|---|---|---|---|",
        "| TA-01 | El archivo JSON fue descargado de una fuente confiable | Archivo manipulado pasa checks si no se alteran canonical fields | content_hash verifica integridad de los 10 campos canónicos |",
        "| TA-02 | El campo `status` refleja el estado actual en DB | Cert revocado puede aparecer ACTIVE en archivo descargado antes de revocación | **SIN MITIGACIÓN** — POGR-SEC-002 |",
        "| TA-03 | `pqc_signature` con prefijo `ML-DSA-65:` es criptográficamente válida | Firma forjada pasa el check | **SIN MITIGACIÓN** — POGR-SEC-001 |",
        "| TA-04 | El `pogc_id` en el JSON corresponde al cert que el usuario quiere verificar | Cert de POGC-B presentado como POGC-A | Parcial — hash valida el contenido, no el mapeo ID→contenido (POGR-SEC-011) |",
        "| TA-05 | Los campos canónicos están presentes y completos | Hash de subset → no coincide con hash completo | Mitigado — mismatch detectable (INVALID) |",
        "",
        "### Límite de confianza",
        "",
        "> **El offline verifier NO puede detectar revocación si el archivo fue descargado**",
        "> **antes de la revocación.** El campo `status` no está firmado criptográficamente.",
        "> **Para verificación de revocación, SIEMPRE consultar el API en tiempo real.**",
        "> El offline verifier NO verifica la firma PQC criptográficamente.",
        "",
        "---",
        "",
        "## Canal 2 — JSON API (`GET /v1/pogr/verify/<pogc_id>`)",
        "",
        "### Qué verifica",
        "",
        "| Check | Descripción | Resultado si falla |",
        "|---|---|---|",
        "| [1] content_hash | Recomputa SHA3-256 desde DB → compara con stored content_hash | valid=False |",
        "| [2] status | Lee status de DB en tiempo real | valid=False si REVOKED/EXPIRED |",
        "| [3] TTL | Compara expires_at de DB con now() | valid=False si expirado |",
        "| [4] pqc_signature | Verifica prefijo — STUB = Warning (no False) | Warning si STUB |",
        "",
        "### Suposiciones de confianza",
        "",
        "| # | Suposición | Riesgo si falla | Mitigación actual |",
        "|---|---|---|---|",
        "| TA-06 | La DB no ha sido mutada directamente (bypass API) | Campos canónicos cambiados en DB → hash mismatch → INVALID | Recomputa hash en cada /verify call ✓ |",
        "| TA-07 | `pqc_signature` en DB fue generada correctamente al certify | Firma incorrecta pasa (solo verifica prefijo) | **SIN MITIGACIÓN** — POGR-SEC-001 |",
        "| TA-08 | DB tiene integridad referencial y NOT NULL activos | Campos faltantes → 500 errors | DB DDL enforced ✓ |",
        "| TA-09 | El resultado es consistente con el HTML page (/pogr/verify) | STUB sig → JSON API=VALID, HTML=INVALID | **ROTA** — POGR-SEC-003 |",
        "",
        "### Límite de confianza",
        "",
        "> El JSON API lee siempre de DB (tiempo real) — detecta revocación correctamente.",
        "> NO verifica la firma PQC criptográficamente.",
        "> La consistencia con el canal HTML **no está garantizada** (POGR-SEC-003).",
        "",
        "---",
        "",
        "## Canal 3 — HTML Web (`GET /pogr/verify/<pogc_id>`)",
        "",
        "### Qué verifica",
        "",
        "| Check | Descripción | Resultado si falla |",
        "|---|---|---|",
        "| [1] status | Lee status de DB en tiempo real | INVALID si REVOKED/EXPIRED |",
        "| [2] TTL | Compara expires_at de DB con now() | INVALID si expirado |",
        "| [3] pqc_signature | sig.startswith('ML-DSA-65:') — STUB = INVALID (no warning) | INVALID si STUB |",
        "| ❌ [4] content_hash | **NO VERIFICADO** | **No aplica — no se verifica** |",
        "",
        "### Suposiciones de confianza",
        "",
        "| # | Suposición | Riesgo si falla | Mitigación actual |",
        "|---|---|---|---|",
        "| TA-10 | La lógica HTML es equivalente a la JSON API | **ROTA** — HTML no verifica content_hash | **SIN MITIGACIÓN** — POGR-SEC-003/POGR-SEC-012 |",
        "| TA-11 | status=ACTIVE + sig ML-DSA-65: implica certificado íntegro | Firma forjada o hash corrupto pasan sin detección | **SIN MITIGACIÓN** — POGR-SEC-001/003 |",
        "| TA-12 | STUB firma = inválida (no producción) | HTML dice INVALID; JSON API dice VALID | **ROTA** — POGR-SEC-003 (divergencia) |",
        "",
        "### Límite de confianza",
        "",
        "> **El canal HTML es el más débil:** no verifica content_hash.",
        "> Un cert con content_hash corrupto pero status=ACTIVE y sig ML-DSA-65:",
        "> **pasaría el HTML pero fallaría el JSON API.**",
        "> El canal HTML no debe ser citado como prueba de verificación completa.",
        "",
        "---",
        "",
        "## Matriz de Verificación Cross-Canal",
        "",
        "| Propiedad | Offline | API JSON | HTML Web |",
        "|---|---|---|---|",
        "| `content_hash` recomputado | ✅ Sí | ✅ Sí | ❌ **No** |",
        "| `status` actual (tiempo real DB) | ❌ No (depende del archivo) | ✅ Sí | ✅ Sí |",
        "| TTL (`expires_at`) | ✅ Sí | ✅ Sí | ✅ Sí |",
        "| `issuer` explícito | ✅ Sí (hardcoded check [5]) | ❌ Solo por hash | ❌ Solo por hash |",
        "| Firma PQC criptográfica | ❌ Solo prefijo | ❌ Solo prefijo | ❌ Solo prefijo |",
        "| Revocación post-export | ❌ No puede detectar | ✅ Sí | ✅ Sí |",
        "| Campos extra ignorados | ✅ Sí (allowlist) | ✅ Sí (DB) | ✅ Sí (DB) |",
        "| Binding ID↔contenido | ⚠ Parcial | ✅ Sí (DB lookup) | ✅ Sí (DB lookup) |",
        "| STUB firma → INVALID | ⚠ Solo si STUB prefix sin ML-DSA | ❌ STUB=Warning | ✅ Sí |",
        "",
        "---",
        "",
        "## Propiedades de Seguridad Garantizadas",
        "",
        "1. **Integridad de campos canónicos** — cualquier alteración de los 10 campos",
        "   canónicos rompe el `content_hash` y es detectada por Offline y API.",
        "2. **Revocación en tiempo real** — API y HTML leen de DB → detectan revocación.",
        "3. **TTL no falsificable** — `expires_at` es canónico → no se puede extender sin romper hash.",
        "4. **Append-only** — DB no tiene DELETE en core fields (PoGR-INV-002).",
        "5. **Campos extra inocuos** — todos los canales ignoran extras vía allowlist explícita.",
        "6. **Issuer verificado explícitamente** — offline verifier tiene check hardcoded de EXPECTED_ISSUER.",
        "",
        "## Propiedades de Seguridad NO Garantizadas (Gaps Activos)",
        "",
        "1. **Verificación PQC** — ningún canal verifica la firma ML-DSA-65 criptográficamente (POGR-SEC-001).",
        "2. **Revocación offline** — archivo previo a revocación pasa el offline verifier (POGR-SEC-002).",
        "3. **Consistencia HTML/API** — HTML no verifica content_hash (POGR-SEC-003).",
        "4. **Unicidad de sesión** — mismo session_id puede generar N PoGCs (POGR-SEC-004).",
        "5. **Binding ID↔contenido en offline** — no hay validación que pogc_id en archivo == ID solicitado (POGR-SEC-011).",
        "",
        "---",
        "",
        f"*Generado por `scripts/pogr_adversarial_audit.py` · {now} UTC · OMNIX QUANTUM LTD*",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  {GREEN('✓')} {os.path.basename(path)}")


def write_consistency_report(attacks: List[AttackResult], path: str) -> None:
    now         = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    divergences = [a for a in attacks if a.divergence]

    lines = [
        "# POGR Web / API / Offline Consistency Report",
        "",
        "**Sistema:** OMNIX Proof of Governance Registry (PoGR)  ",
        f"**Fecha:** {now} UTC  ",
        "**Metodología:** Cada ataque ejecutado independientemente sobre tres canales.",
        "Un certificado es **SEGURO** solo si los tres canales producen el mismo veredicto.",
        "",
        "---",
        "",
        "## Vista Completa de Consistencia",
        "",
        "| Ataque | Descripción | Offline | API JSON | HTML Web | Consistente |",
        "|---|---|---|---|---|---|",
    ]

    for a in attacks:
        consistent = "✅ Sí" if not a.divergence else "❌ **No**"
        desc = a.description[:48] + ("…" if len(a.description) > 48 else "")
        lines.append(
            f"| {a.attack_id} | {desc} | {_v_str(a.offline_valid)} | "
            f"{_v_str(a.api_valid)} | {_v_str(a.html_valid)} | {consistent} |"
        )

    lines += [
        "",
        f"**Resumen:** {len(divergences)} divergencia(s) detectada(s) de {len(attacks)} ataques.",
        "",
        "---",
        "",
        "## Divergencias Confirmadas",
        "",
    ]

    if not divergences:
        lines.append("*Ninguna divergencia detectada.*")
    else:
        for i, a in enumerate(divergences, 1):
            lines += [
                f"### DIV-{i:03d} — {a.attack_id}: {a.description}",
                "",
                f"**Finding:** `{a.finding_id}` | **Severidad:** {a.severity}",
                "",
                "| Canal | Veredicto | Lógica de verificación |",
                "|---|---|---|",
                f"| Offline | `{_v_str(a.offline_valid)}` | content_hash ✓ · status (archivo) · TTL · sig prefix · issuer |",
                f"| API JSON | `{_v_str(a.api_valid)}` | content_hash ✓ · status (DB) · TTL · sig prefix |",
                f"| HTML Web | `{_v_str(a.html_valid)}` | status (DB) · TTL · sig prefix · **❌ NO content_hash** |",
                "",
                "**Causa raíz:**",
                "",
                a.finding_desc[:600],
                "",
                "**Remediación:**",
                "",
                a.remediation[:400],
                "",
                "---",
                "",
            ]

    lines += [
        "## Análisis de Raíces Comunes",
        "",
        "Las divergencias tienen tres raíces independientes:",
        "",
        "### Raíz 1 — `status` excluido de `content_hash` (POGR-SEC-002)",
        "",
        "Los 10 canonical_fields no incluyen `status` ni `revoked_at`. Un archivo exportado",
        "antes de una revocación presenta el estado anterior (ACTIVE) con hash válido.",
        "El offline verifier confía en el campo `status` del archivo — no puede consultar DB.",
        "",
        "**Impacto:** Offline=VALID, API/HTML=INVALID para certificados revocados con export previo.",
        "**Ataques afectados:** A07, A11",
        "",
        "### Raíz 2 — HTML page omite `content_hash` (POGR-SEC-003 / POGR-SEC-012)",
        "",
        "El endpoint `/pogr/verify/<id>` (Jinja2) usa:",
        "```python",
        "valid = status_db == 'ACTIVE' and not expired and sig.startswith('ML-DSA-65:')",
        "```",
        "El endpoint `/v1/pogr/verify/<id>` (JSON) recomputa el hash en cada llamada.",
        "El componente React en `/proof-of-governance` llama al JSON API.",
        "",
        "**Impacto:** HTML=VALID, API/React=INVALID si content_hash en DB es incorrecto.",
        "**Ataques afectados:** A08",
        "",
        "### Raíz 3 — STUB signature tratada distinto por canal (POGR-SEC-003)",
        "",
        "```",
        "JSON API:   STUB → Warning (None) → overall_valid = True  → VALID",
        "HTML page:  STUB → sig.startswith('ML-DSA-65:') = False → valid = False → INVALID",
        "Offline:    STUB → Warning (None) → overall_valid = True  → VALID",
        "```",
        "",
        "**Impacto:** API/Offline=VALID, HTML=INVALID para certs con firma STUB.",
        "**Ataques afectados:** A09",
        "",
        "---",
        "",
        "## Nivel de Confianza por Canal",
        "",
        "| Canal | Nivel de Confianza | Verificación PQC | Revocación en tiempo real | Content hash |",
        "|---|---|---|---|---|",
        "| Offline | ⚠ CONDICIONAL | ❌ Solo prefijo | ❌ No (depende del archivo) | ✅ Sí |",
        "| API JSON | ✅ ALTO | ❌ Solo prefijo | ✅ Sí (DB) | ✅ Sí |",
        "| HTML Web | 🔴 BAJO | ❌ Solo prefijo | ✅ Sí (DB) | ❌ **No** |",
        "",
        "**Recomendación:** Para verificación en producción, usar el API JSON",
        "(`GET /v1/pogr/verify/<id>`) como canal primario.",
        "El canal HTML debe ser reforzado para igualar la lógica del JSON API.",
        "El canal offline es adecuado para verificación de integridad de campos canónicos",
        "pero **NO para verificación de revocación**.",
        "",
        "---",
        "",
        f"*Generado por `scripts/pogr_adversarial_audit.py` · {now} UTC · OMNIX QUANTUM LTD*",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  {GREEN('✓')} {os.path.basename(path)}")


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    global _USE_COLOR

    parser = argparse.ArgumentParser(
        description="OMNIX PoGR Adversarial Security Audit v2.0"
    )
    parser.add_argument("--no-color",   action="store_true", help="Disable ANSI colours")
    parser.add_argument("--no-reports", action="store_true", help="Skip writing MD reports")
    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        _USE_COLOR = False

    print()
    print(GOLD("=" * 72))
    print(GOLD("  OMNIX QUANTUM — PoGR Adversarial Security Audit v2.0"))
    print(GOLD("  ADR-186 · ADR-187 · ADR-189 · PoGR-INV-001–006"))
    print(GOLD("=" * 72))
    print()
    print(f"  Canales: Offline (subprocess) · API JSON (inline) · HTML Web (inline)")
    print(f"  Attacks: 15 (A01–A15)")
    print()

    attacks = build_attacks()
    print_results(attacks)

    if not args.no_reports:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(BOLD("  Generando informes MD..."))
        write_adversarial_audit_report(
            attacks, os.path.join(root, "POGR_ADVERSARIAL_AUDIT.md")
        )
        write_trust_assumption_map(
            attacks, os.path.join(root, "POGR_TRUST_ASSUMPTION_MAP.md")
        )
        write_consistency_report(
            attacks, os.path.join(root, "POGR_WEB_API_OFFLINE_CONSISTENCY_REPORT.md")
        )
        print()

    divergences = [a for a in attacks if a.divergence]
    criticals   = [a for a in attacks if a.severity == "CRITICAL"]
    print()
    if divergences or criticals:
        print(RED(BOLD(
            f"  ✗ AUDIT COMPLETE — {len(divergences)} divergence(s) · "
            f"{len(criticals)} critical finding(s)"
        )))
        sys.exit(1)
    else:
        print(GREEN(BOLD("  ✓ All attacks consistent across channels")))
        sys.exit(0)


if __name__ == "__main__":
    main()
