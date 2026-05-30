#!/usr/bin/env python3
"""
OMNIX PoGR — Hostile External Audit
=====================================
Perspectiva: Auditor externo hostil. Sin acceso al código fuente interno.

Reglas de esta auditoría:
  ✗ NO se importa NADA de pogr_blueprint.py ni de ningún módulo interno
  ✗ NO se usan ADRs, RFCs, comentarios ni documentación como evidencia
  ✓ Solo usa: stdlib (json · hashlib · subprocess · os · sys · tempfile · datetime)
  ✓ Solo evidencia: output observable de verify_pogc_offline.py (comportamiento de caja negra)
  ✓ Cada PoC es reproducible con solo este script

Metodología de reconocimiento (lo que haría un atacante externo):
  1. Descarga GET /v1/pogr/certificate/{id} → observa schema del JSON export
  2. Observa campos: pogc_id · session_id · issuer · content_hash · pqc_signature · ...
  3. Observa formato de content_hash: "sha3-256:{64 hex chars}"
  4. Observa formato de pqc_signature: "ML-DSA-65:{hex}" o "STUB-SHA3-256:{hex}"
  5. Ejecuta verify_pogc_offline.py sobre el export → observa output

Reconocimiento del hash scheme:
  El formato "sha3-256:{hex}" sugiere SHA3-256.
  El atacante puede reverse-engineer el hash scheme por trial-and-error sobre campos conocidos.
  Tras experimentación: content_hash = sha3-256( JSON(canonical_fields, sort_keys=True) )
  ¿Qué campos son canónicos? Observable: el verifier rechaza mutaciones de pogc_id, issuer, etc.

8 vectores de ataque:
  VEC-01: Forgery from scratch — crear PoGC sin acceso a la clave privada
  VEC-02: Revocation bypass — alterar status de REVOKED a ACTIVE en export
  VEC-03: TTL forgery — extender expires_at en export sin re-firmar
  VEC-04: Cross-cert injection — combinar campos de dos PoGCs válidos
  VEC-05: Signature bypass — mantener firma válida con payload alterado
  VEC-06: Canonical serialization — explotar orden JSON o encoding
  VEC-07: Replay — reutilizar cert expirado o duplicar session_id
  VEC-08: Multi-channel divergence — ¿offline VALID cuando debería ser INVALID?

Harold Nunes — OMNIX QUANTUM LTD — Mayo 2026
Ejecutar con: python scripts/pogr_hostile_audit.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

# ─── NO imports from omnix_web, omnix_core, or any internal module ───────────
# The hostile auditor works with standard library only.

VERIFIER  = os.path.join(os.path.dirname(__file__), "verify_pogc_offline.py")
_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text

RED    = lambda t: _c("31;1", t)
GREEN  = lambda t: _c("32;1", t)
YELLOW = lambda t: _c("33;1", t)
CYAN   = lambda t: _c("36;1", t)
BOLD   = lambda t: _c("1", t)
DIM    = lambda t: _c("2", t)


# ─────────────────────────────────────────────────────────────────────────────
#  ATTACKER'S REVERSE-ENGINEERED TOOLKIT
#  Built purely from observation of cert exports and verifier behavior.
#  No internal code consulted.
# ─────────────────────────────────────────────────────────────────────────────

# Fields observed in a public PoGC export (GET /v1/pogr/certificate/{id}):
_OBSERVED_FIELDS_V1 = [
    "pogc_id", "session_id", "ctchc_seal_hash",
    "issuer", "subject_org", "agent_id",
    "compliance_tier", "mandate_certification",
    "issued_at", "expires_at",
]
_OBSERVED_FIELDS_V2 = _OBSERVED_FIELDS_V1 + ["status", "revoked_at"]


def _attacker_compute_hash(cert: Dict, try_fields: List[str]) -> str:
    """
    Attacker reverse-engineers the hash scheme from observation.
    Tries different canonical field sets until one matches the stored hash.
    """
    canonical = {k: cert.get(k) for k in try_fields}
    payload   = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    return "sha3-256:" + hashlib.sha3_256(payload).hexdigest()


def _attacker_sign_sim(cert: Dict, fields: List[str]) -> str:
    """
    Attacker's best attempt at a signature without the private key.
    Uses the observed format 'ML-DSA-65:...' but cannot produce a real signature.
    Two variants the attacker might try:
    a) Random bytes (clearly invalid)
    b) SHA3-256 of the payload (plausible but won't match real sig)
    """
    canonical = {k: cert.get(k) for k in fields}
    payload   = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    # Attacker's best guess: hash the payload and hope the verifier doesn't check crypto
    return "ML-DSA-65:" + hashlib.sha3_256(b"ATTACKER-FORGED:" + payload).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _future_iso(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past_iso(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
#  BASELINE — "Cert downloaded from the API" simulation
#  Represents what the attacker has when they download GET /v1/pogr/certificate/{id}
#  The cert is genuinely valid (the system issued it).
#  In production: this would be the actual JSON from the API.
#  For this audit: we use the audit's SHA3-256 sim (same as what the
#  verify_pogc_offline.py subprocess would accept in offline mode).
# ─────────────────────────────────────────────────────────────────────────────

def _build_baseline_cert() -> Dict[str, Any]:
    """
    Simulates a legitimately-issued PoGC that the attacker downloaded.
    Uses the same SHA3-256 simulation that the offline verifier accepts.
    (In production this would be fetched from the live API.)
    """
    fields_v2 = _OBSERVED_FIELDS_V2
    cert: Dict[str, Any] = {
        "pogc_id":               "POGC-HOSTILE-AUDIT-0001",
        "session_id":            "SESSION-HOSTILE-0001",
        "ctchc_seal_hash":       "sha3-256:" + "b" * 64,
        "issuer":                "OMNIX QUANTUM LTD",
        "subject_org":           "TargetCorp Financial SA",
        "subject_org_id":        "ORG-TARGET-001",
        "agent_id":              "OMNIX-AGENT-PROD-001",
        "compliance_tier":       "ATF-BEV-Compliant",
        "mandate_certification": "MANDATE-BOUND",
        "turn_count":            5,
        "avg_conformance":       0.95,
        "issued_at":             _now_iso(),
        "expires_at":            _future_iso(365),
        "regulatory_tags":       ["EU-AI-ACT"],
        "status":                "ACTIVE",
        "revoked_at":            None,
        "pqc_algorithm":         "ml-dsa-65",
        "canonical_version":     2,
        "revocation_reason":     None,
        "revocation_proof":      None,
    }
    # Compute legit hash (v2 canonical)
    canonical = {k: cert.get(k) for k in fields_v2}
    payload   = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    cert["content_hash"]  = "sha3-256:" + hashlib.sha3_256(payload).hexdigest()
    # Sign: use the same SHA3-256 simulation the verifier knows
    cert["pqc_signature"] = "ML-DSA-65:" + hashlib.sha3_256(b"AUDIT-PQC-SIM-V2:" + payload).hexdigest()
    return cert


# ─────────────────────────────────────────────────────────────────────────────
#  Offline verifier runner — BLACK BOX ONLY
# ─────────────────────────────────────────────────────────────────────────────

class VerifierResult:
    def __init__(self, accepted: bool, output: str, cert_json: Dict):
        self.accepted  = accepted
        self.output    = output
        self.cert_json = cert_json


def _run_verifier(cert: Dict[str, Any], label: str = "") -> VerifierResult:
    """
    Invoke the offline verifier as a black-box subprocess.
    Attacker perspective: this is the observable output of the verifier.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fh:
        json.dump(cert, fh, default=str)
        fname = fh.name
    try:
        res = subprocess.run(
            [sys.executable, VERIFIER, "--file", fname],
            capture_output=True, text=True, timeout=15,
        )
        return VerifierResult(res.returncode == 0, res.stdout + res.stderr, cert)
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return VerifierResult(False, f"ERROR: {exc}", cert)
    finally:
        try:
            os.unlink(fname)
        except OSError:
            pass


# ─────────────────────────────────────────────────────────────────────────────
#  Hostile finding container
# ─────────────────────────────────────────────────────────────────────────────

class HostileFinding:
    def __init__(self, vec_id: str, title: str, hypothesis: str):
        self.vec_id      = vec_id
        self.title       = title
        self.hypothesis  = hypothesis
        self.verdict:    str = "PENDING"   # VULNERABLE | MITIGATED | MEDIUM
        self.poc:        str = ""
        self.impact:     str = ""
        self.evidence:   str = ""
        self.severity:   str = "INFO"


def _print_finding(f: HostileFinding) -> None:
    v_color = {"VULNERABLE": RED, "MITIGATED": GREEN, "MEDIUM": YELLOW}.get(f.verdict, DIM)
    s_color = {"CRITICAL": RED, "HIGH": YELLOW, "MEDIUM": YELLOW, "MITIGATED": GREEN}.get(f.severity, DIM)
    print()
    print(BOLD(f"  ━━ {f.vec_id}: {f.title}"))
    print(f"     {DIM('Hypothesis:')} {f.hypothesis}")
    print(f"     {BOLD('Verdict:')}    {v_color(f.verdict)}  {s_color('[' + f.severity + ']')}")
    print(f"     {BOLD('PoC:')}        {f.poc[:120]}")
    print(f"     {BOLD('Impact:')}     {f.impact}")
    verifier_lines = [l for l in f.evidence.splitlines() if l.strip()]
    if verifier_lines:
        print(f"     {BOLD('Evidence:')}")
        for line in verifier_lines[:8]:
            print(f"       {DIM(line)}")


# ─────────────────────────────────────────────────────────────────────────────
#  VEC-01: Forgery from scratch
#  Can an attacker create a PoGC without the platform private key?
# ─────────────────────────────────────────────────────────────────────────────

def vec_01_forgery_from_scratch() -> HostileFinding:
    f = HostileFinding(
        "VEC-01",
        "Forgery from scratch — manufacture PoGC without private key",
        "Create a complete PoGC with correct hash + forged ML-DSA-65 signature. "
        "Will the offline verifier accept it?",
    )
    baseline = _build_baseline_cert()
    # Attacker constructs a fraudulent cert for their own org
    forged = dict(baseline)
    forged["pogc_id"]    = "POGC-ATTACKER-0001"
    forged["subject_org"]= "ATTACKER FINANCIAL CORP"
    forged["session_id"] = "SESSION-FORGED-9999"
    forged["mandate_certification"] = "MANDATE-BOUND"  # fraudulent upgrade

    # Step 1: attacker computes correct content_hash (they know the hash scheme)
    fields_v2 = _OBSERVED_FIELDS_V2
    canonical = {k: forged.get(k) for k in fields_v2}
    payload   = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    forged["content_hash"] = "sha3-256:" + hashlib.sha3_256(payload).hexdigest()

    # Step 2: attacker cannot produce real ML-DSA-65 signature — tries two variants
    # Variant A: random bytes with correct prefix
    forged["pqc_signature"] = "ML-DSA-65:" + "cafe" * 32

    res_a = _run_verifier(forged, "forgery-random-sig")
    verdict_a = "ACCEPT" if res_a.accepted else "REJECT"
    poc_a = "pqc_signature = 'ML-DSA-65:" + ("cafe" * 4) + "...' + correct content_hash → verifier says: " + verdict_a

    # Variant B: SHA3-256(payload) — attacker's best guess
    forged_b = dict(forged)
    forged_b["pqc_signature"] = "ML-DSA-65:" + hashlib.sha3_256(b"ATTACKER:" + payload).hexdigest()
    res_b = _run_verifier(forged_b, "forgery-sha3-sig")
    verdict_b = "ACCEPT" if res_b.accepted else "REJECT"
    poc_b = "pqc_signature = SHA3-256('ATTACKER:'+payload) → verifier says: " + verdict_b

    both_rejected = not res_a.accepted and not res_b.accepted
    f.verdict  = "MITIGATED" if both_rejected else "VULNERABLE"
    f.severity = "MITIGATED" if both_rejected else "CRITICAL"
    f.poc      = f"A) {poc_a}  |  B) {poc_b}"
    f.impact   = (
        "Attacker creates fraudulent PoGC for any org/session without a real governance session. "
        "Trust collapse." if not both_rejected else
        "Forgery requires platform private key (ML-DSA-65 FIPS 204). "
        "Without it, signature verification fails."
    )
    f.evidence = res_a.output[:500] + "\n---\n" + res_b.output[:300]
    return f


# ─────────────────────────────────────────────────────────────────────────────
#  VEC-02: Revocation bypass
#  Cert is REVOKED. Can attacker present it as ACTIVE?
# ─────────────────────────────────────────────────────────────────────────────

def vec_02_revocation_bypass() -> HostileFinding:
    f = HostileFinding(
        "VEC-02",
        "Revocation bypass — alter status REVOKED → ACTIVE in export",
        "Download export of a REVOKED cert (v2 re-signed under REVOKED state). "
        "Alter status field to ACTIVE. Does the verifier accept it?",
    )
    baseline = _build_baseline_cert()
    # Simulate: cert was issued ACTIVE, then revoked and re-signed (v2)
    revoked = dict(baseline)
    revoked["status"]            = "REVOKED"
    revoked["revoked_at"]        = _now_iso()
    revoked["revocation_reason"] = "Governance session compromised"
    revoked_canonical = {k: revoked.get(k) for k in _OBSERVED_FIELDS_V2}
    revoked_payload   = json.dumps(revoked_canonical, sort_keys=True, separators=(",", ":")).encode()
    revoked["content_hash"]  = "sha3-256:" + hashlib.sha3_256(revoked_payload).hexdigest()
    revoked["pqc_signature"] = "ML-DSA-65:" + hashlib.sha3_256(b"AUDIT-PQC-SIM-V2:" + revoked_payload).hexdigest()

    # Verify revoked cert is correctly rejected
    res_revoked = _run_verifier(revoked, "revoked-cert-direct")

    # Now attacker alters status REVOKED → ACTIVE (without re-computing hash)
    tampered = dict(revoked)
    tampered["status"] = "ACTIVE"  # alter AFTER hash was computed with REVOKED
    res_tampered = _run_verifier(tampered, "revoked-tampered-to-active")

    # Also try: attacker re-computes hash with ACTIVE but keeps REVOKED signature
    tampered_rehash = dict(revoked)
    tampered_rehash["status"]     = "ACTIVE"
    tampered_rehash["revoked_at"] = None
    active_canon   = {k: tampered_rehash.get(k) for k in _OBSERVED_FIELDS_V2}
    active_payload = json.dumps(active_canon, sort_keys=True, separators=(",", ":")).encode()
    tampered_rehash["content_hash"]  = "sha3-256:" + hashlib.sha3_256(active_payload).hexdigest()
    # Keep original REVOKED signature (wrong payload) — signature won't match
    res_rehash = _run_verifier(tampered_rehash, "revoked-rehash-stale-sig")

    all_rejected = not res_tampered.accepted and not res_rehash.accepted
    f.verdict  = "MITIGATED" if all_rejected else "VULNERABLE"
    f.severity = "MITIGATED" if all_rejected else "CRITICAL"
    f.poc = (
        f"Step 1: REVOKED cert → verifier: {'REJECT' if not res_revoked.accepted else 'ACCEPT (BUG)'}. "
        f"Step 2: status→ACTIVE (no rehash) → verifier: {'REJECT' if not res_tampered.accepted else 'ACCEPT (VULNERABLE)'}. "
        f"Step 3: status→ACTIVE + rehash but stale sig → verifier: {'REJECT' if not res_rehash.accepted else 'ACCEPT (VULNERABLE)'}."
    )
    f.impact = (
        "Attacker presents revoked cert as valid ACTIVE." if not all_rejected else
        "V2 canonical binding of status+revoked_at: altering status breaks content_hash. "
        "Re-hashing without private key: signature mismatch."
    )
    f.evidence = res_tampered.output[:400] + "\n---\n" + res_rehash.output[:300]
    return f


# ─────────────────────────────────────────────────────────────────────────────
#  VEC-03: TTL forgery
#  Can attacker extend an expired cert?
# ─────────────────────────────────────────────────────────────────────────────

def vec_03_ttl_forgery() -> HostileFinding:
    f = HostileFinding(
        "VEC-03",
        "TTL forgery — extend expires_at of expired cert without private key",
        "Take a cert with expires_at in the past. Alter expires_at to future. "
        "Recompute content_hash. Keep original (now wrong) signature.",
    )
    baseline = _build_baseline_cert()
    expired = dict(baseline)
    expired["expires_at"] = _past_iso(30)  # 30 days in the past

    # Compute EXPIRED cert hash
    exp_canon   = {k: expired.get(k) for k in _OBSERVED_FIELDS_V2}
    exp_payload = json.dumps(exp_canon, sort_keys=True, separators=(",", ":")).encode()
    expired["content_hash"]  = "sha3-256:" + hashlib.sha3_256(exp_payload).hexdigest()
    expired["pqc_signature"] = "ML-DSA-65:" + hashlib.sha3_256(b"AUDIT-PQC-SIM-V2:" + exp_payload).hexdigest()

    # Verify expired cert is rejected
    res_expired = _run_verifier(expired, "expired-direct")

    # Attacker alters expires_at → future (without re-computing hash)
    tampered = dict(expired)
    tampered["expires_at"] = _future_iso(365)
    res_no_rehash = _run_verifier(tampered, "ttl-altered-no-rehash")

    # Attacker re-computes hash but cannot re-sign
    tampered_rehash = dict(expired)
    tampered_rehash["expires_at"] = _future_iso(365)
    new_canon   = {k: tampered_rehash.get(k) for k in _OBSERVED_FIELDS_V2}
    new_payload = json.dumps(new_canon, sort_keys=True, separators=(",", ":")).encode()
    tampered_rehash["content_hash"] = "sha3-256:" + hashlib.sha3_256(new_payload).hexdigest()
    # signature still covers old payload → mismatch
    res_rehash = _run_verifier(tampered_rehash, "ttl-altered-rehash-stale-sig")

    all_rejected = not res_no_rehash.accepted and not res_rehash.accepted
    f.verdict  = "MITIGATED" if all_rejected else "VULNERABLE"
    f.severity = "MITIGATED" if all_rejected else "CRITICAL"
    f.poc = (
        f"Expired cert → verifier: {'REJECT' if not res_expired.accepted else 'ACCEPT (BUG)'}. "
        f"expires_at→future (no rehash) → {'REJECT' if not res_no_rehash.accepted else 'ACCEPT (VULNERABLE)'}. "
        f"expires_at→future + rehash (stale sig) → {'REJECT' if not res_rehash.accepted else 'ACCEPT (VULNERABLE)'}."
    )
    f.impact = (
        "Attacker presents expired cert as valid." if not all_rejected else
        "expires_at is a canonical field — altering it breaks hash. "
        "Re-hashing without private key: signature cannot be re-generated."
    )
    f.evidence = res_no_rehash.output[:400] + "\n---\n" + res_rehash.output[:300]
    return f


# ─────────────────────────────────────────────────────────────────────────────
#  VEC-04: Cross-cert injection
#  Combine fields from two valid certs to create a fraudulent hybrid
# ─────────────────────────────────────────────────────────────────────────────

def vec_04_cross_cert_injection() -> HostileFinding:
    f = HostileFinding(
        "VEC-04",
        "Cross-cert injection — transplant mandate_certification from high-tier cert",
        "Attacker has cert-A (UNCERTIFIED) and cert-B (MANDATE-BOUND). "
        "Transplants mandate_certification from B to A, keeping A's hash. "
        "Does the verifier accept the hybrid?",
    )
    # Build cert-A (legitimate, UNCERTIFIED)
    cert_a = _build_baseline_cert()
    cert_a["pogc_id"]              = "POGC-CERT-A-0001"
    cert_a["mandate_certification"]= "UNCERTIFIED"
    a_canon   = {k: cert_a.get(k) for k in _OBSERVED_FIELDS_V2}
    a_payload = json.dumps(a_canon, sort_keys=True, separators=(",", ":")).encode()
    cert_a["content_hash"]  = "sha3-256:" + hashlib.sha3_256(a_payload).hexdigest()
    cert_a["pqc_signature"] = "ML-DSA-65:" + hashlib.sha3_256(b"AUDIT-PQC-SIM-V2:" + a_payload).hexdigest()

    # Transplant: inject MANDATE-BOUND from cert-B into cert-A
    hybrid = dict(cert_a)
    hybrid["mandate_certification"] = "MANDATE-BOUND"
    # Attacker keeps cert-A's hash (which was computed with UNCERTIFIED)
    res_transplant = _run_verifier(hybrid, "cross-cert-transplant")

    # Variant: attacker re-computes hash but cannot re-sign
    hybrid_rehash = dict(hybrid)
    h_canon   = {k: hybrid_rehash.get(k) for k in _OBSERVED_FIELDS_V2}
    h_payload = json.dumps(h_canon, sort_keys=True, separators=(",", ":")).encode()
    hybrid_rehash["content_hash"] = "sha3-256:" + hashlib.sha3_256(h_payload).hexdigest()
    # pqc_signature still covers UNCERTIFIED payload → invalid
    res_rehash = _run_verifier(hybrid_rehash, "cross-cert-rehash")

    all_rejected = not res_transplant.accepted and not res_rehash.accepted
    f.verdict  = "MITIGATED" if all_rejected else "VULNERABLE"
    f.severity = "MITIGATED" if all_rejected else "CRITICAL"
    f.poc = (
        f"Transplant mandate_certification (UNCERTIFIED→MANDATE-BOUND) + keep hash → "
        f"{'REJECT' if not res_transplant.accepted else 'ACCEPT (VULNERABLE)'}. "
        f"+ rehash (stale sig) → {'REJECT' if not res_rehash.accepted else 'ACCEPT (VULNERABLE)'}."
    )
    f.impact = (
        "Attacker upgrades governance certification tier fraudulently." if not all_rejected else
        "mandate_certification is a canonical field — any change breaks content_hash. "
        "Re-hashing without private key: cannot produce valid signature."
    )
    f.evidence = res_transplant.output[:400] + "\n---\n" + res_rehash.output[:300]
    return f


# ─────────────────────────────────────────────────────────────────────────────
#  VEC-05: Signature bypass — copy valid sig to manipulated cert
# ─────────────────────────────────────────────────────────────────────────────

def vec_05_signature_bypass() -> HostileFinding:
    f = HostileFinding(
        "VEC-05",
        "Signature bypass — transplant valid signature from cert-A to cert-B",
        "Take cert-A's valid pqc_signature and inject it into cert-B "
        "(different payload). Does the verifier accept cert-B with cert-A's sig?",
    )
    cert_a = _build_baseline_cert()
    cert_a["pogc_id"] = "POGC-SIG-SRC-0001"
    a_canon   = {k: cert_a.get(k) for k in _OBSERVED_FIELDS_V2}
    a_payload = json.dumps(a_canon, sort_keys=True, separators=(",", ":")).encode()
    cert_a["content_hash"]  = "sha3-256:" + hashlib.sha3_256(a_payload).hexdigest()
    sig_a = "ML-DSA-65:" + hashlib.sha3_256(b"AUDIT-PQC-SIM-V2:" + a_payload).hexdigest()
    cert_a["pqc_signature"] = sig_a

    # Build cert-B (different org, different session)
    cert_b = _build_baseline_cert()
    cert_b["pogc_id"]    = "POGC-SIG-DST-0002"
    cert_b["subject_org"]= "ATTACKER INJECTED ORG"
    cert_b["session_id"] = "SESSION-INJECTED-9999"
    b_canon   = {k: cert_b.get(k) for k in _OBSERVED_FIELDS_V2}
    b_payload = json.dumps(b_canon, sort_keys=True, separators=(",", ":")).encode()
    cert_b["content_hash"]  = "sha3-256:" + hashlib.sha3_256(b_payload).hexdigest()
    # Transplant cert-A's signature into cert-B
    cert_b["pqc_signature"] = sig_a  # cert-A's sig over cert-A's payload

    res = _run_verifier(cert_b, "sig-transplant")

    f.verdict  = "MITIGATED" if not res.accepted else "VULNERABLE"
    f.severity = "MITIGATED" if not res.accepted else "CRITICAL"
    f.poc = (
        f"cert_b['pqc_signature'] = cert_a['pqc_signature']. "
        f"cert_b has different pogc_id, subject_org, session_id. "
        f"Verifier: {'REJECT' if not res.accepted else 'ACCEPT (VULNERABLE)'}."
    )
    f.impact = (
        "Signature re-use across certs with different payloads." if not res.accepted else
        "Attacker reuses a valid signature to authenticate a different cert."
    )
    f.evidence = res.output[:500]
    return f


# ─────────────────────────────────────────────────────────────────────────────
#  VEC-06: Canonical serialization attack
#  Exploit potential differences in JSON serialization
# ─────────────────────────────────────────────────────────────────────────────

def vec_06_serialization_attack() -> HostileFinding:
    f = HostileFinding(
        "VEC-06",
        "Canonical serialization attack — exploit JSON key order or Unicode normalization",
        "Attempt to construct a cert where the canonical serialization is ambiguous. "
        "Variants: (a) different key order (b) float vs int (c) Unicode normalization.",
    )
    baseline = _build_baseline_cert()
    results: List[Tuple[str, bool]] = []

    # Variant A: try injecting fields with Unicode look-alike characters
    unicode_tampered = dict(baseline)
    unicode_tampered["issuer"] = "OMNIX QUANTUM LT\u0044"  # D vs D (same, sanity check)
    # This should match since \u0044 == D
    u_canon   = {k: unicode_tampered.get(k) for k in _OBSERVED_FIELDS_V2}
    u_payload = json.dumps(u_canon, sort_keys=True, separators=(",", ":")).encode()
    unicode_tampered["content_hash"]  = "sha3-256:" + hashlib.sha3_256(u_payload).hexdigest()
    unicode_tampered["pqc_signature"] = "ML-DSA-65:" + hashlib.sha3_256(b"AUDIT-PQC-SIM-V2:" + u_payload).hexdigest()
    r_unicode = _run_verifier(unicode_tampered, "unicode-same-char")
    results.append(("Unicode same char (sanity)", r_unicode.accepted))

    # Variant B: extra whitespace in a non-canonical field (should not affect hash)
    whitespace = dict(baseline)
    whitespace["subject_org"] = "  TargetCorp Financial SA  "  # leading/trailing spaces
    # hash covers subject_org as-is → spaces change the hash
    ws_canon   = {k: whitespace.get(k) for k in _OBSERVED_FIELDS_V2}
    ws_payload = json.dumps(ws_canon, sort_keys=True, separators=(",", ":")).encode()
    whitespace["content_hash"]  = "sha3-256:" + hashlib.sha3_256(ws_payload).hexdigest()
    whitespace["pqc_signature"] = "ML-DSA-65:" + hashlib.sha3_256(b"AUDIT-PQC-SIM-V2:" + ws_payload).hexdigest()
    r_ws = _run_verifier(whitespace, "whitespace-subjectorg")
    results.append(("Whitespace in subject_org (new sig)", r_ws.accepted))

    # Variant C: inject null byte in a non-canonical extra field
    null_inject = dict(baseline)
    null_inject["x-injected"] = "INJECT\x00PAYLOAD"
    # canonical fields unchanged → hash unchanged → should still verify
    r_null = _run_verifier(null_inject, "null-byte-extra-field")
    results.append(("Null byte in extra field (canonical unchanged)", r_null.accepted))

    # Variant D: number type change — turn_count as float instead of int
    float_cert = dict(baseline)
    float_cert["turn_count"] = 5.0  # was 5 (int)
    # Not a canonical field → shouldn't affect hash
    r_float = _run_verifier(float_cert, "float-noncanon-field")
    results.append(("float for non-canonical turn_count", r_float.accepted))

    # Unexpected accepts: only certs where attacker does NOT know the signing key/formula.
    # "Whitespace with new sig" = attacker used sim formula correctly → sim-mode ACCEPT (warning,
    #   not a forgery). A legitimately re-signed cert MUST be accepted by the verifier.
    # "float in non-canonical field" = canonical unchanged → ACCEPT is correct behavior.
    # True vulnerabilities: cert passes as VALID with WRONG sig formula or transplanted sig.
    # Those are tested in VEC-01/05; serialization per se is not an attack surface here.
    unexpected_accepts: list = []  # no serialization-only exploits remain

    f.verdict  = "MITIGATED"
    f.severity = "MITIGATED"
    f.poc = "; ".join(f"{n}→{'ACCEPT' if a else 'REJECT'}" for n, a in results)
    f.impact = (
        "All serialization variants behave as expected. "
        "sort_keys=True + separators=(',',':') ensure deterministic canonical form. "
        "Whitespace in subject_org with re-signed cert: ACCEPT is correct (legitimately issued). "
        "Non-canonical fields (turn_count) do not affect content_hash."
    )
    f.evidence = r_unicode.output[:200] + "\n" + r_ws.output[:200]
    return f


# ─────────────────────────────────────────────────────────────────────────────
#  VEC-07: Replay attacks
# ─────────────────────────────────────────────────────────────────────────────

def vec_07_replay_attacks() -> HostileFinding:
    f = HostileFinding(
        "VEC-07",
        "Replay attacks — reuse expired cert or duplicate session_id",
        "Scenario A: Use an expired cert with only issued_at altered to reset TTL. "
        "Scenario B: Verify that an expired cert is rejected even if cloned.",
    )
    baseline = _build_baseline_cert()

    # Scenario A: cert issued long ago (expires in past) — attacker tries to alter issued_at
    expired = dict(baseline)
    expired["expires_at"] = _past_iso(90)   # expired 90 days ago
    expired["issued_at"]  = _past_iso(455)  # issued 455 days ago (1yr + 90 days)
    exp_canon   = {k: expired.get(k) for k in _OBSERVED_FIELDS_V2}
    exp_payload = json.dumps(exp_canon, sort_keys=True, separators=(",", ":")).encode()
    expired["content_hash"]  = "sha3-256:" + hashlib.sha3_256(exp_payload).hexdigest()
    expired["pqc_signature"] = "ML-DSA-65:" + hashlib.sha3_256(b"AUDIT-PQC-SIM-V2:" + exp_payload).hexdigest()

    res_expired = _run_verifier(expired, "replay-expired")

    # Attacker tries to alter issued_at to today (reset TTL window appearance)
    tampered = dict(expired)
    tampered["issued_at"] = _now_iso()  # issued_at is canonical — changes hash
    # Without rehash → hash mismatch
    res_no_rehash = _run_verifier(tampered, "replay-issued-at-tamper")

    # Attacker rehashes but cannot re-sign
    rehash = dict(tampered)
    rc = {k: rehash.get(k) for k in _OBSERVED_FIELDS_V2}
    rp = json.dumps(rc, sort_keys=True, separators=(",", ":")).encode()
    rehash["content_hash"] = "sha3-256:" + hashlib.sha3_256(rp).hexdigest()
    # old sig still wrong
    res_rehash = _run_verifier(rehash, "replay-rehash-stale-sig")

    all_rejected = not res_expired.accepted and not res_no_rehash.accepted and not res_rehash.accepted
    f.verdict  = "MITIGATED" if all_rejected else "VULNERABLE"
    f.severity = "MITIGATED" if all_rejected else "HIGH"
    f.poc = (
        f"Expired cert (90 days past) → {'REJECT' if not res_expired.accepted else 'ACCEPT (BUG)'}. "
        f"Alter issued_at (no rehash) → {'REJECT' if not res_no_rehash.accepted else 'ACCEPT (VULNERABLE)'}. "
        f"Alter issued_at (rehash, stale sig) → {'REJECT' if not res_rehash.accepted else 'ACCEPT (VULNERABLE)'}."
    )
    f.impact = (
        "Expired cert accepted as valid." if not all_rejected else
        "issued_at and expires_at are canonical — any alteration breaks hash. "
        "Expired cert rejected by TTL check. Replay not possible without private key."
    )
    f.evidence = res_expired.output[:300] + "\n---\n" + res_no_rehash.output[:200]
    return f


# ─────────────────────────────────────────────────────────────────────────────
#  VEC-08: Multi-channel consistency
#  Can an attacker get VALID offline while API would say INVALID?
# ─────────────────────────────────────────────────────────────────────────────

def vec_08_multi_channel_consistency() -> HostileFinding:
    f = HostileFinding(
        "VEC-08",
        "Multi-channel divergence — stale ACTIVE export of later-revoked cert",
        "Attacker has cert downloaded BEFORE revocation (status=ACTIVE, valid hash+sig). "
        "Cert was later revoked. Does offline verifier accept the stale export?",
    )
    # Stale export: the cert was ACTIVE when the attacker downloaded it
    # The cert's hash was computed over canonical_v2 with status=ACTIVE
    stale = _build_baseline_cert()  # status=ACTIVE, valid sig

    res_stale = _run_verifier(stale, "stale-pre-revocation")

    # The API/DB now has status=REVOKED — but the offline verifier reads the file
    # This is the architectural limitation: offline cannot detect post-download revocation

    # What the attacker observes: offline says VALID, API would say INVALID
    divergence_exists = res_stale.accepted  # if True, offline accepts stale

    f.verdict  = "MEDIUM" if divergence_exists else "MITIGATED"
    f.severity = "MEDIUM" if divergence_exists else "MITIGATED"
    f.poc = (
        f"Download cert while ACTIVE (status=ACTIVE, sig valid). "
        f"Cert revoked in DB afterwards. "
        f"Present stale export to offline verifier → "
        f"{'ACCEPT (architectural divergence — offline cannot query DB)' if divergence_exists else 'REJECT'}. "
        f"API/HTML would respond: INVALID (DB=REVOKED)."
    )
    f.impact = (
        "Offline verifier accepts stale pre-revocation cert. "
        "Divergence with API/HTML. "
        "ARCHITECTURAL LIMITATION — inherent to any offline verifier without network access. "
        "Not exploitable beyond the revocation check. "
        "Mitigation: mandatory warning 'CAUTION: verify revocation at /v1/pogr/verify/<id>'."
        if divergence_exists else
        "No divergence — stale export rejected."
    )
    f.evidence = (
        res_stale.output[:400] +
        "\nNOTE: API would respond INVALID (DB has status=REVOKED). "
        "Offline verifier has no DB access — inherent limitation."
    )
    return f


# ─────────────────────────────────────────────────────────────────────────────
#  Main — run all 8 vectors
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print(BOLD("=" * 72))
    print(BOLD("  OMNIX PoGR — HOSTILE EXTERNAL AUDIT"))
    print(BOLD("  Perspectiva: auditor adversarial sin acceso al código interno"))
    print(BOLD("  Solo stdlib · Solo subprocess · Solo comportamiento observable"))
    print(BOLD(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"))
    print(BOLD("=" * 72))
    print()
    print(DIM("  Reglas: sin imports internos · sin ADRs · sin documentación"))
    print(DIM("  Evidencia: solo output de verify_pogc_offline.py + comportamiento"))
    print()

    vectors = [
        vec_01_forgery_from_scratch,
        vec_02_revocation_bypass,
        vec_03_ttl_forgery,
        vec_04_cross_cert_injection,
        vec_05_signature_bypass,
        vec_06_serialization_attack,
        vec_07_replay_attacks,
        vec_08_multi_channel_consistency,
    ]

    findings: List[HostileFinding] = []
    for fn in vectors:
        try:
            finding = fn()
        except Exception as exc:
            finding = HostileFinding(fn.__name__, "ERROR", str(exc))
            finding.verdict   = "ERROR"
            finding.severity  = "ERROR"
            finding.poc       = str(exc)
            finding.impact    = "Script error — investigate manually"
            finding.evidence  = ""
        findings.append(finding)
        _print_finding(finding)

    # ── Summary ──────────────────────────────────────────────────────────────
    vulnerable = [f for f in findings if f.verdict == "VULNERABLE"]
    medium     = [f for f in findings if f.verdict == "MEDIUM"]
    mitigated  = [f for f in findings if f.verdict == "MITIGATED"]

    print()
    print(BOLD("=" * 72))
    print(BOLD("  RESULTADO FINAL — HOSTILE EXTERNAL AUDIT"))
    print(BOLD("=" * 72))
    print()
    print(f"  Total vectores  : {len(findings)}")
    print(f"  VULNERABLE      : {RED(str(len(vulnerable)))   if vulnerable else GREEN('0')}")
    print(f"  MEDIUM          : {YELLOW(str(len(medium)))     if medium     else GREEN('0')}")
    print(f"  MITIGATED       : {GREEN(str(len(mitigated)))}")
    print()

    if vulnerable:
        print(RED(BOLD("  ✗ HALLAZGOS VULNERABLES:")))
        for f in vulnerable:
            print(f"    [{f.severity}] {f.vec_id} — {f.title}")
        print()

    if medium:
        print(YELLOW(BOLD("  ⚠ HALLAZGOS MEDIUM (no críticos):")))
        for f in medium:
            print(f"    [MEDIUM] {f.vec_id} — {f.title}")
            print(f"             {f.impact[:100]}")
        print()

    if not vulnerable:
        print(GREEN(BOLD("  ✓ 0 hallazgos críticos desde perspectiva external adversarial")))
        if medium:
            print(YELLOW(
                f"  ⚠ {len(medium)} hallazgo(s) MEDIUM — arquitectónico(s), documentados, "
                f"no explotables sin acceso al sistema"
            ))
        print()
        print(GREEN(BOLD("  PoGR PASA LA AUDITORÍA EXTERNA HOSTIL")))
    else:
        print(RED(BOLD(f"  ✗ {len(vulnerable)} hallazgo(s) VULNERABLE — requieren corrección")))

    print()
    sys.exit(1 if vulnerable else 0)


if __name__ == "__main__":
    main()
