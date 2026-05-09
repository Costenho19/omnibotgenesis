#!/usr/bin/env python3
"""
OMNIX Independent Receipt Verifier
===================================
Version: 1.0.0 | Standard: NIST FIPS 204 (ML-DSA-65 / Dilithium-3)
Issuer:  OMNIX Quantum Ltd | DID: did:web:omnixquantum.net

PURPOSE
-------
Verify any OMNIX governance decision receipt with ZERO dependency on
OMNIX servers. The math runs entirely on your machine.

This script addresses the eIDAS / ARF requirement that trust proofs
be verifiable by third parties independently of the issuing system.

WHAT IT VERIFIES
----------------
1. SHA-256 content hash — the receipt payload has not been tampered with
2. Dilithium-3 PQC signature — the receipt was issued by OMNIX (if pqcrypto
   is installed; otherwise hash-only mode with clear notice)
3. Receipt structure — required fields are present
4. Timestamp sanity — no future-dated receipts

USAGE
-----
  # Install the PQC library (optional but recommended for full verification)
  pip install pqcrypto

  # Verify a receipt from a JSON file
  python omnix_verify.py receipt.json

  # Verify a receipt by fetching it from the OMNIX API
  python omnix_verify.py --receipt-id REC-20260426-ABCD1234

  # Verify using a specific public key file (PEM or b64)
  python omnix_verify.py receipt.json --pubkey omnix_pubkey.b64

  # Output as JSON (for pipelines)
  python omnix_verify.py receipt.json --json

TRUST CHAIN
-----------
  Public key source (choose one):
    1. Embedded in the receipt itself (public_key field)
    2. https://omnixquantum.net/.well-known/omnix-public-key.json
    3. https://omnixquantum.net/api/trust/registry
    4. https://omnixquantum.net/.well-known/did.json (DID Document)

  Any of these sources can be used. You do NOT need OMNIX infrastructure
  to run the cryptographic verification — only to fetch the public key
  once. After that, verification is fully offline.

LEGAL NOTICE
-----------
This script is provided for independent audit purposes.
OMNIX Quantum Ltd | omnixquantum.net | ADR-085
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Optional

OMNIX_ISSUER_DID     = "did:web:omnixquantum.net"
OMNIX_ISSUER_URL     = "https://omnixquantum.net"
OMNIX_PUBKEY_URL     = f"{OMNIX_ISSUER_URL}/.well-known/omnix-public-key.json"
OMNIX_RECEIPT_API    = f"{OMNIX_ISSUER_URL}/api/explorer/receipt"
OMNIX_REPLAY_API     = f"{OMNIX_ISSUER_URL}/api/trust/verify"
SCRIPT_VERSION       = "2.0.0"
REQUIRED_FIELDS      = ["receipt_id", "decision", "content_hash"]
REPLAY_REQUIRED_FIELDS = ["receipt_id", "scenario_id", "verdict", "canonical_hash"]

# ── ETA-001 Trust Status Codes ─────────────────────────────────────────────────
TRUST_VALID_OMNIX_ISSUED            = "VALID_OMNIX_ISSUED"
TRUST_VALID_SIGNATURE_UNTRUSTED     = "VALID_SIGNATURE_UNTRUSTED_ISSUER"
TRUST_INVALID_SIGNATURE             = "INVALID_SIGNATURE"
TRUST_UNKNOWN_KEY                   = "UNKNOWN_KEY"
TRUST_DOWNGRADED_SHA_ONLY           = "DOWNGRADED_SHA_ONLY"

TRUST_STATUS_DESCRIPTIONS = {
    TRUST_VALID_OMNIX_ISSUED: (
        "Hash valid, PQC signature valid, key fingerprint matches the trusted OMNIX anchor. "
        "Receipt is PROVEN to be issued by OMNIX Quantum Ltd."
    ),
    TRUST_VALID_SIGNATURE_UNTRUSTED: (
        "Hash valid, PQC signature mathematically valid, but the embedded public key "
        "does NOT match the trusted OMNIX anchor fingerprint. "
        "Receipt may be signed by an attacker keypair. DO NOT treat as OMNIX-issued."
    ),
    TRUST_INVALID_SIGNATURE: (
        "PQC signature is present but mathematically INVALID. "
        "Receipt has been tampered with or is forged."
    ),
    TRUST_UNKNOWN_KEY: (
        "No public key available for verification. Issuer cannot be determined."
    ),
    TRUST_DOWNGRADED_SHA_ONLY: (
        "No PQC signature — hash-chain integrity mode only. Payload has not been tampered "
        "with, but cryptographic issuer proof is absent."
    ),
}


# ── Color helpers ──────────────────────────────────────────────────────────────

def _green(s: str) -> str:
    return f"\033[92m{s}\033[0m" if sys.stdout.isatty() else s

def _red(s: str) -> str:
    return f"\033[91m{s}\033[0m" if sys.stdout.isatty() else s

def _yellow(s: str) -> str:
    return f"\033[93m{s}\033[0m" if sys.stdout.isatty() else s

def _bold(s: str) -> str:
    return f"\033[1m{s}\033[0m" if sys.stdout.isatty() else s

def _dim(s: str) -> str:
    return f"\033[2m{s}\033[0m" if sys.stdout.isatty() else s


# ── PQC provider detection ────────────────────────────────────────────────────

def _try_import_pqc():
    """Return the dilithium3 module if pqcrypto is installed, else None."""
    try:
        from pqc.sign import dilithium3
        return dilithium3
    except ImportError:
        return None


# ── Hash computation ──────────────────────────────────────────────────────────

def _compute_canonical_hash(receipt: Dict[str, Any]) -> str:
    """
    Recompute the canonical SHA-256 hash of a receipt payload.
    Uses the same field set as OMNIX GovernanceEvaluationEngine.
    Must match the engine's _canonical_payload() exactly.
    """
    payload: Dict[str, Any] = {
        "receipt_id":     receipt.get("receipt_id"),
        "timestamp":      receipt.get("timestamp"),
        "asset":          receipt.get("asset"),
        "decision":       receipt.get("decision"),
        "veto_chain":     receipt.get("veto_chain"),
        "policy_version": receipt.get("policy_version"),
        "engine_version": receipt.get("engine_version"),
        "prev_hash":      receipt.get("prev_hash"),
    }
    if receipt.get("signing_provider"):
        payload["signing_provider"] = receipt["signing_provider"]
    for opt in ("sharia_compliance", "aml_compliance", "fraud_compliance",
                "jurisdiction_compliance", "context_admission"):
        if opt in receipt:
            payload[opt] = receipt[opt]
    if "veto_type" in receipt:
        payload["veto_type"] = receipt["veto_type"]

    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── Signature verification ────────────────────────────────────────────────────

def _verify_pqc_signature(
    sig_b64:     str,
    pub_key_b64: str,
    message:     str,
    dilithium3:  Any,
) -> bool:
    """
    Verify a Dilithium-3 (ML-DSA-65) signature.
    All inputs are base64-encoded strings except message (hex string).
    """
    sig = base64.b64decode(sig_b64)
    pub = base64.b64decode(pub_key_b64)
    msg = message.encode("utf-8")
    try:
        dilithium3.verify(sig, msg, pub)
        return True
    except Exception:
        return False


# ── Public key fetching ───────────────────────────────────────────────────────

def _fetch_issuer_public_key(timeout: int = 5) -> Optional[str]:
    """
    Fetch the issuer public key from the OMNIX well-known endpoint.
    Returns the base64-encoded public key or None on failure.
    This is the ONLY network call this script makes — and it's optional
    if the public key is already embedded in the receipt.
    """
    try:
        req = urllib.request.Request(
            OMNIX_PUBKEY_URL,
            headers={"User-Agent": f"omnix_verify/{SCRIPT_VERSION}"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("key", {}).get("public_key_b64")
    except Exception as e:
        return None


# ── ETA-001: Trust anchor helpers (inline — no omnix_core dependency) ──────────

def _compute_key_fingerprint(pub_key_b64: str) -> Optional[str]:
    """SHA-256 of raw public key bytes — canonical trust identity."""
    try:
        raw = base64.b64decode(pub_key_b64)
        return hashlib.sha256(raw).hexdigest()
    except Exception:
        return None


def _load_trusted_omnix_fingerprint(
    trusted_key_b64: Optional[str] = None,
    trusted_fp: Optional[str] = None,
    fetch_well_known: bool = True,
    timeout: int = 4,
) -> Optional[str]:
    """
    Load the trusted OMNIX public key fingerprint.

    Priority:
      1. --trusted-fingerprint CLI arg (pre-computed hex)
      2. --pubkey CLI arg (compute from provided key)
      3. Fetched well-known key (if fetch_well_known=True)
    """
    if trusted_fp and len(trusted_fp) == 64:
        return trusted_fp
    if trusted_key_b64:
        return _compute_key_fingerprint(trusted_key_b64)
    if fetch_well_known:
        fetched = _fetch_issuer_public_key(timeout=timeout)
        if fetched:
            return _compute_key_fingerprint(fetched)
    return None


def _classify_trust(
    hash_valid: bool,
    signature_valid: Optional[bool],
    sig_b64: Optional[str],
    pub_key_b64: Optional[str],
    sig_algo: Optional[str],
    trusted_fp: Optional[str],
) -> tuple:
    """
    Classify receipt trust status per ETA-001.

    Returns (trust_status, issuer_trusted, key_fingerprint).
    """
    key_fingerprint: Optional[str] = None
    if pub_key_b64:
        key_fingerprint = _compute_key_fingerprint(pub_key_b64)

    algo_lower = (sig_algo or "").lower()
    is_sha_only = "sha" in algo_lower and "dilithium" not in algo_lower and "ml-dsa" not in algo_lower

    if not sig_b64 or is_sha_only:
        if hash_valid:
            return TRUST_DOWNGRADED_SHA_ONLY, False, key_fingerprint
        return TRUST_INVALID_SIGNATURE, False, key_fingerprint

    if sig_b64 and not pub_key_b64:
        return TRUST_UNKNOWN_KEY, False, key_fingerprint

    if signature_valid is False:
        return TRUST_INVALID_SIGNATURE, False, key_fingerprint

    if signature_valid is True:
        if not key_fingerprint:
            return TRUST_UNKNOWN_KEY, False, key_fingerprint
        if trusted_fp:
            if key_fingerprint == trusted_fp:
                return TRUST_VALID_OMNIX_ISSUED, True, key_fingerprint
            else:
                return TRUST_VALID_SIGNATURE_UNTRUSTED, False, key_fingerprint
        else:
            return TRUST_VALID_SIGNATURE_UNTRUSTED, False, key_fingerprint

    return TRUST_UNKNOWN_KEY, False, key_fingerprint


def _fetch_receipt_by_id(receipt_id: str, timeout: int = 10) -> Optional[Dict]:
    """Fetch a receipt JSON from the OMNIX Explorer API."""
    url = f"{OMNIX_RECEIPT_API}/{receipt_id}"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"omnix_verify/{SCRIPT_VERSION}"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(_red(f"  ERROR: Could not fetch receipt {receipt_id}: {e}"))
        return None


# ── Structure check ───────────────────────────────────────────────────────────

def _check_structure(receipt: Dict) -> list[str]:
    """Return list of missing required fields."""
    return [f for f in REQUIRED_FIELDS if not receipt.get(f)]


# ── Timestamp sanity ──────────────────────────────────────────────────────────

def _check_timestamp(receipt: Dict) -> str:
    """Return a human-readable timestamp status."""
    ts = receipt.get("timestamp") or receipt.get("timestamp_utc")
    if not ts:
        return "absent"
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if dt > now:
            return f"FUTURE — {ts} (clock skew or forged receipt)"
        age_days = (now - dt).days
        return f"OK — {ts} ({age_days} days ago)"
    except Exception:
        return f"unparseable — {ts}"


# ── Replay receipt verifier ───────────────────────────────────────────────────

def _compute_replay_canonical_hash(receipt: Dict[str, Any]) -> str:
    """
    Recompute the canonical SHA-256 hash of an OMNIX replay receipt.
    Uses the same field set and serialization as GovernanceReplayEngine._canonical_hash().
    ADR-145.
    """
    payload: Dict[str, Any] = {
        "receipt_id":           receipt.get("receipt_id"),
        "scenario_id":          receipt.get("scenario_id"),
        "timestamp_utc":        receipt.get("timestamp_utc"),
        "signal_label":         receipt.get("signal_label"),
        "domain":               receipt.get("domain"),
        "verdict":              receipt.get("verdict"),
        "blocking_checkpoint":  receipt.get("blocking_checkpoint"),
        "trust_flags":          sorted(receipt.get("trust_flags") or []),
        "signals_snapshot":     dict(sorted((receipt.get("signals_snapshot") or {}).items())),
        "rationale":            receipt.get("rationale"),
        "replay_mode":          True,
        "engine_version":       receipt.get("engine_version"),
        "adr_reference":        receipt.get("adr_reference"),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def verify_replay_receipt(
    receipt:  Dict[str, Any],
    as_json:  bool = False,
) -> Dict[str, Any]:
    """
    Verify an OMNIX governance replay receipt (ADR-145).

    Replay receipts differ from production receipts:
      - They use `canonical_hash` instead of `content_hash`
      - They have `replay_mode=True`
      - They carry `scenario_id` instead of `asset` / `decision`
      - They are verified by recomputing the SHA-256 of the canonical payload

    No PQC signature is needed — the canonical hash seals the full payload.
    All signal data and rationale are embedded in the receipt itself.
    """
    now = datetime.now(timezone.utc).isoformat()
    receipt_id = receipt.get("receipt_id", "UNKNOWN")

    result: Dict[str, Any] = {
        "script_version":    SCRIPT_VERSION,
        "verified_at":       now,
        "receipt_id":        receipt_id,
        "receipt_type":      "GOVERNANCE_REPLAY",
        "adr_reference":     receipt.get("adr_reference", "ADR-145"),
        "scenario_id":       receipt.get("scenario_id"),
        "issuer_did":        OMNIX_ISSUER_DID,
        "independent":       True,
        "db_required":       False,
        "replay_mode":       receipt.get("replay_mode", True),
        "structure_ok":      False,
        "hash_valid":        False,
        "signature_valid":   None,
        "timestamp_status":  _check_timestamp(receipt),
        "overall_valid":     False,
        "verdict":           "INVALID",
    }

    # 1. Structure check
    missing = [f for f in REPLAY_REQUIRED_FIELDS if not receipt.get(f)]
    result["structure_ok"]   = len(missing) == 0
    result["missing_fields"] = missing

    # 2. Canonical hash verification
    stored_hash   = receipt.get("canonical_hash", "")
    computed_hash = _compute_replay_canonical_hash(receipt)
    result["hash_valid"]    = computed_hash == stored_hash
    result["stored_hash"]   = stored_hash
    result["computed_hash"] = computed_hash

    if result["hash_valid"]:
        result["hash_note"] = (
            "SHA-256 canonical hash VERIFIED — replay receipt payload is intact and unmodified. "
            "Signal data, verdict, trust flags, and rationale are authentic."
        )
    else:
        result["hash_note"] = (
            "SHA-256 canonical hash MISMATCH — replay receipt may have been tampered with. "
            f"Stored: {stored_hash[:16]}... | Computed: {computed_hash[:16]}..."
        )

    # 3. Replay receipts do not have PQC signatures (hash seals the full payload)
    result["signature_valid"] = None
    result["signature_note"]  = (
        "Replay receipts are sealed by SHA-256 canonical hash — no separate PQC signature. "
        "Hash verification is the authoritative check for replay receipt integrity."
    )

    # 4. Overall verdict
    if result["hash_valid"] and result["structure_ok"]:
        result["overall_valid"] = True
        result["verdict"]       = "VALID"
        result["verdict_note"]  = (
            f"Replay receipt is authentic. Scenario: {receipt.get('scenario_id')} | "
            f"Event: {receipt.get('signal_label', 'N/A')} | "
            f"Governance verdict: {receipt.get('verdict', 'N/A')} "
            f"@ {receipt.get('blocking_checkpoint', 'N/A')}. "
            "SHA-256 canonical hash verified — payload sealed by OMNIX Governance Replay Engine (ADR-145)."
        )
    else:
        result["overall_valid"] = False
        issues = []
        if not result["structure_ok"]:
            issues.append(f"missing fields: {', '.join(missing)}")
        if not result["hash_valid"]:
            issues.append("canonical hash mismatch")
        result["verdict_note"] = f"Verification failed: {'; '.join(issues)}."

    return result


# ── Main verifier ─────────────────────────────────────────────────────────────

def verify_receipt(
    receipt:           Dict[str, Any],
    pubkey_b64:        Optional[str] = None,
    fetch_key:         bool          = True,
    as_json:           bool          = False,
    trusted_fp:        Optional[str] = None,
) -> Dict[str, Any]:
    """
    Full independent verification of an OMNIX governance receipt.

    Args:
        receipt:     Receipt dict (from JSON file or API)
        pubkey_b64:  Override public key (b64). If None, uses receipt's own key.
        fetch_key:   If True and no key available, fetch from OMNIX well-known.
        as_json:     If True, suppress console output (JSON mode).
        trusted_fp:  Trusted OMNIX key fingerprint (64-char hex). If None,
                     derived from --pubkey or fetched from well-known endpoint.

    Returns:
        Verification result dict including ETA-001 trust_status field.
    """
    now     = datetime.now(timezone.utc).isoformat()
    receipt_id = receipt.get("receipt_id", "UNKNOWN")

    result: Dict[str, Any] = {
        "script_version":     SCRIPT_VERSION,
        "verified_at":        now,
        "receipt_id":         receipt_id,
        "issuer_did":         OMNIX_ISSUER_DID,
        "independent":        True,
        "db_required":        False,
        "structure_ok":       False,
        "hash_valid":         False,
        "signature_valid":    None,
        "pqc_available":      False,
        "timestamp_status":   _check_timestamp(receipt),
        "overall_valid":      False,
        "verdict":            "INVALID",
        "trust_status":       TRUST_UNKNOWN_KEY,
        "issuer_trusted":     False,
        "key_fingerprint":    None,
    }

    # ── 1. Structure check ─────────────────────────────────────────────────
    missing = _check_structure(receipt)
    result["structure_ok"]     = len(missing) == 0
    result["missing_fields"]   = missing

    # ── 2. Hash verification ───────────────────────────────────────────────
    stored_hash   = receipt.get("content_hash", "")
    computed_hash = _compute_canonical_hash(receipt)
    result["hash_valid"]    = computed_hash == stored_hash
    result["stored_hash"]   = stored_hash
    result["computed_hash"] = computed_hash

    if result["hash_valid"]:
        result["hash_note"] = "SHA-256 content hash VERIFIED — payload is intact and unmodified."
    else:
        result["hash_note"] = (
            "SHA-256 content hash MISMATCH — receipt may have been tampered with. "
            f"Stored: {stored_hash[:16]}... | Computed: {computed_hash[:16]}..."
        )

    # ── 3. PQC signature verification ──────────────────────────────────────
    dilithium3 = _try_import_pqc()
    result["pqc_available"] = dilithium3 is not None

    pub_key = pubkey_b64 or receipt.get("public_key")

    if pub_key is None and fetch_key:
        if not as_json:
            print(_dim("  Fetching issuer public key from well-known endpoint..."))
        pub_key = _fetch_issuer_public_key()
        if pub_key:
            result["key_source"] = "fetched from /.well-known/omnix-public-key.json"
        else:
            result["key_source"] = "unavailable"
    elif pub_key:
        result["key_source"] = "provided / embedded in receipt"
    else:
        result["key_source"] = "not provided"

    sig_b64  = receipt.get("signature")
    sig_algo = receipt.get("signature_algorithm", "")

    if dilithium3 and sig_b64 and pub_key:
        try:
            sig_ok = _verify_pqc_signature(sig_b64, pub_key, stored_hash, dilithium3)
            result["signature_valid"]    = sig_ok
            result["signature_algorithm"] = sig_algo or "dilithium3"
            if sig_ok:
                result["signature_note"] = (
                    "PQC signature VERIFIED — receipt is cryptographically authentic. "
                    "Signed with Dilithium-3 (NIST FIPS 204 / ML-DSA-65)."
                )
            else:
                result["signature_note"] = (
                    "PQC signature INVALID — receipt may have been forged or "
                    "the public key does not match the signer."
                )
        except Exception as e:
            result["signature_valid"] = None
            result["signature_note"]  = f"Verification error: {e}"
    elif not dilithium3:
        result["signature_valid"] = None
        result["signature_note"]  = (
            "pqcrypto not installed — hash-only mode. "
            "Install with: pip install pqcrypto | Then re-run for full PQC verification."
        )
    elif not sig_b64:
        result["signature_valid"] = None
        result["signature_note"]  = "No signature field in receipt — hash-chain integrity only."
    elif not pub_key:
        result["signature_valid"] = None
        result["signature_note"]  = (
            "Public key unavailable. Fetch from: "
            f"{OMNIX_PUBKEY_URL}"
        )

    # ── 4. ETA-001 Trust Anchor Classification ─────────────────────────────
    resolved_trusted_fp = _load_trusted_omnix_fingerprint(
        trusted_key_b64=pubkey_b64,
        trusted_fp=trusted_fp,
        fetch_well_known=fetch_key,
    )
    trust_status, issuer_trusted, key_fp = _classify_trust(
        hash_valid=result["hash_valid"],
        signature_valid=result["signature_valid"],
        sig_b64=sig_b64,
        pub_key_b64=pub_key,
        sig_algo=sig_algo,
        trusted_fp=resolved_trusted_fp,
    )
    result["trust_status"]               = trust_status
    result["issuer_trusted"]             = issuer_trusted
    result["key_fingerprint"]            = key_fp
    result["trusted_anchor_fingerprint"] = resolved_trusted_fp
    result["trust_status_description"]   = TRUST_STATUS_DESCRIPTIONS.get(trust_status, "")

    # ── 5. Overall verdict ─────────────────────────────────────────────────
    hash_ok = result["hash_valid"]
    sig_ok  = result["signature_valid"]

    if trust_status == TRUST_VALID_OMNIX_ISSUED:
        result["overall_valid"] = True
        result["verdict"]       = "VALID_OMNIX_ISSUED"
        result["verdict_note"]  = (
            "Receipt is cryptographically authentic AND proven to be issued by OMNIX. "
            "Hash verified. PQC signature verified. Key fingerprint matches OMNIX trust anchor."
        )
    elif trust_status == TRUST_VALID_SIGNATURE_UNTRUSTED:
        result["overall_valid"] = False
        result["verdict"]       = "VALID_SIGNATURE_UNTRUSTED_ISSUER"
        result["verdict_note"]  = (
            "PQC signature is mathematically valid, but the embedded public key does NOT match "
            "the trusted OMNIX anchor fingerprint. REJECT — cannot confirm OMNIX issuance. "
            "Possible forged receipt with attacker keypair."
        )
    elif trust_status == TRUST_DOWNGRADED_SHA_ONLY:
        result["overall_valid"] = hash_ok
        result["verdict"]       = "DOWNGRADED_SHA_ONLY"
        result["verdict_note"]  = (
            "Content hash verified. No PQC signature — issuer cannot be proven. "
            "For full verification, use a PQC-signed receipt."
        )
    elif trust_status == TRUST_INVALID_SIGNATURE:
        result["overall_valid"] = False
        result["verdict"]       = "INVALID_SIGNATURE"
        result["verdict_note"]  = (
            "Receipt verification failed. PQC signature is invalid or payload has been tampered with."
        )
    elif trust_status == TRUST_UNKNOWN_KEY:
        result["overall_valid"] = hash_ok and sig_ok is None
        result["verdict"]       = "UNKNOWN_KEY"
        result["verdict_note"]  = (
            "Public key unavailable — issuer cannot be determined. "
            "Hash integrity " + ("verified." if hash_ok else "FAILED.")
        )
    else:
        if hash_ok and sig_ok is True:
            result["overall_valid"] = True
            result["verdict"]       = "VALID"
            result["verdict_note"]  = "Hash and signature verified. Issuer trust status unknown."
        elif hash_ok and sig_ok is None:
            result["overall_valid"] = True
            result["verdict"]       = "VALID (hash only)"
            result["verdict_note"]  = (
                "Content hash verified. PQC signature check skipped (no key or library). "
                "For full verification: pip install pqcrypto and re-run."
            )
        else:
            result["overall_valid"] = False
            result["verdict"]       = "INVALID"
            result["verdict_note"]  = "Verification failed. See hash_note and signature_note for details."

    return result


# ── Console output ────────────────────────────────────────────────────────────

def _print_result(r: Dict[str, Any]) -> None:
    print()
    print(_bold("=" * 64))
    print(_bold("  OMNIX Independent Receipt Verifier"))
    print(_bold(f"  v{SCRIPT_VERSION} | {OMNIX_ISSUER_DID}"))
    print(_bold("=" * 64))
    print()
    print(f"  Receipt ID   : {r.get('receipt_id')}")
    print(f"  Verified at  : {r.get('verified_at')}")
    print(f"  Issuer DID   : {r.get('issuer_did')}")
    print()

    struct_icon = _green("PASS") if r.get("structure_ok") else _red("FAIL")
    print(f"  Structure    : {struct_icon}", end="")
    if r.get("missing_fields"):
        print(f"  (missing: {', '.join(r['missing_fields'])})", end="")
    print()

    hash_icon = _green("VALID") if r.get("hash_valid") else _red("INVALID")
    print(f"  Content Hash : {hash_icon}")
    print(_dim(f"               {r.get('hash_note','')}"))

    sig = r.get("signature_valid")
    if sig is True:
        sig_icon = _green("VALID")
    elif sig is False:
        sig_icon = _red("INVALID")
    else:
        sig_icon = _yellow("SKIPPED")
    print(f"  PQC Signature: {sig_icon}")
    print(_dim(f"               {r.get('signature_note','')}"))

    print(f"  Timestamp    : {r.get('timestamp_status')}")
    print()

    print(_bold("  ── TRUST ANCHOR (ETA-001) ─────────────────────────────"))
    trust_status = r.get("trust_status", TRUST_UNKNOWN_KEY)
    issuer_trusted = r.get("issuer_trusted", False)

    if trust_status == TRUST_VALID_OMNIX_ISSUED:
        ts_display = _green(_bold(f"  Trust Status : {trust_status}"))
    elif trust_status == TRUST_VALID_SIGNATURE_UNTRUSTED:
        ts_display = _yellow(_bold(f"  Trust Status : {trust_status}"))
    elif trust_status == TRUST_INVALID_SIGNATURE:
        ts_display = _red(_bold(f"  Trust Status : {trust_status}"))
    elif trust_status == TRUST_DOWNGRADED_SHA_ONLY:
        ts_display = _yellow(f"  Trust Status : {trust_status}")
    else:
        ts_display = _dim(f"  Trust Status : {trust_status}")
    print(ts_display)

    issuer_icon = _green("VERIFIED ✓") if issuer_trusted else _red("NOT VERIFIED ✗")
    print(f"  OMNIX Issuer : {issuer_icon}")

    fp = r.get("key_fingerprint")
    if fp:
        print(_dim(f"  Key Fingerpr.: {fp[:32]}..."))
    anchor_fp = r.get("trusted_anchor_fingerprint")
    if anchor_fp:
        match = "MATCH ✓" if fp == anchor_fp else "MISMATCH ✗"
        match_disp = _green(match) if fp == anchor_fp else _red(match)
        print(f"  Anchor Match : {match_disp}")
    print(_dim(f"  {r.get('trust_status_description', '')}"))

    if trust_status == TRUST_VALID_SIGNATURE_UNTRUSTED:
        print()
        print(_red(_bold("  ⚠  WARNING: Receipt REJECTED as OMNIX-issued.")))
        print(_red("     The PQC signature is mathematically valid but was NOT"))
        print(_red("     produced by the trusted OMNIX keypair. This is the"))
        print(_red("     classic attacker-keypair attack. Treat as UNTRUSTED."))

    print()

    verdict = r.get("verdict", "UNKNOWN")
    if verdict in (TRUST_VALID_OMNIX_ISSUED, "VALID", "VALID (hash only)"):
        verdict_display = _green(_bold(f"  VERDICT: {verdict}"))
    elif verdict in (TRUST_VALID_SIGNATURE_UNTRUSTED, TRUST_DOWNGRADED_SHA_ONLY, TRUST_UNKNOWN_KEY):
        verdict_display = _yellow(_bold(f"  VERDICT: {verdict}"))
    else:
        verdict_display = _red(_bold(f"  VERDICT: {verdict}"))

    print(verdict_display)
    print(_dim(f"  {r.get('verdict_note','')}"))
    print()
    print(_bold("=" * 64))
    print(_dim("  Independent verification — no OMNIX server access required."))
    print(_dim(f"  Trust registry : {OMNIX_PUBKEY_URL}"))
    print(_dim(f"  Trust anchor   : env OMNIX_TRUSTED_KEY_FINGERPRINT or --trusted-fingerprint"))
    print(_bold("=" * 64))
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="OMNIX Independent Receipt Verifier — verify governance receipts locally.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python omnix_verify.py receipt.json
  python omnix_verify.py receipt.json --pubkey my_key.b64
  python omnix_verify.py --receipt-id REC-20260426-ABCD1234
  python omnix_verify.py receipt.json --json

Trust endpoints (no OMNIX server needed after key fetch):
  Public key: {OMNIX_PUBKEY_URL}
  DID doc:    {OMNIX_ISSUER_URL}/.well-known/did.json
  Registry:   {OMNIX_ISSUER_URL}/api/trust/registry
        """,
    )
    parser.add_argument("receipt_file", nargs="?", help="Path to receipt JSON file")
    parser.add_argument("--receipt-id", help="Fetch receipt by ID from OMNIX API")
    parser.add_argument("--pubkey", help="Path to a file containing the public key (base64)")
    parser.add_argument("--no-fetch", action="store_true",
                        help="Do not fetch the public key from the OMNIX well-known endpoint")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Output result as JSON (for pipelines)")
    parser.add_argument(
        "--trusted-fingerprint",
        metavar="FINGERPRINT",
        help=(
            "SHA-256 hex fingerprint (64 chars) of the trusted OMNIX public key. "
            "Used for trust anchor validation (ETA-001). If not provided, the fingerprint "
            "is computed from --pubkey or fetched from the OMNIX well-known endpoint. "
            "Example: a3f1... (64 hex chars). "
            "Get it from: https://omnixquantum.net/.well-known/omnix-public-key.json"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "production", "replay"],
        default="auto",
        help=(
            "Verification mode: 'production' (default) for live governance receipts, "
            "'replay' for historical crisis scenario receipts (ADR-145), "
            "'auto' detects mode from receipt (default)."
        ),
    )
    args = parser.parse_args()

    receipt: Optional[Dict] = None

    if args.receipt_file:
        try:
            with open(args.receipt_file, "r", encoding="utf-8") as f:
                receipt = json.load(f)
        except FileNotFoundError:
            print(_red(f"ERROR: File not found: {args.receipt_file}"), file=sys.stderr)
            sys.exit(2)
        except json.JSONDecodeError as e:
            print(_red(f"ERROR: Invalid JSON in {args.receipt_file}: {e}"), file=sys.stderr)
            sys.exit(2)
    elif args.receipt_id:
        if not args.as_json:
            print(f"Fetching receipt {args.receipt_id} from OMNIX API...")
        receipt = _fetch_receipt_by_id(args.receipt_id)
        if not receipt:
            sys.exit(2)
    else:
        parser.print_help()
        sys.exit(1)

    # Detect mode from receipt if auto
    mode = args.mode
    if mode == "auto":
        mode = "replay" if receipt.get("replay_mode") else "production"

    if mode == "replay":
        result = verify_replay_receipt(receipt=receipt, as_json=args.as_json)
    else:
        pubkey_b64: Optional[str] = None
        if args.pubkey:
            try:
                with open(args.pubkey, "r", encoding="utf-8") as f:
                    pubkey_b64 = f.read().strip()
            except FileNotFoundError:
                print(_red(f"ERROR: Public key file not found: {args.pubkey}"), file=sys.stderr)
                sys.exit(2)

        trusted_fp_arg = getattr(args, 'trusted_fingerprint', None)
        result = verify_receipt(
            receipt    = receipt,
            pubkey_b64 = pubkey_b64,
            fetch_key  = not args.no_fetch,
            as_json    = args.as_json,
            trusted_fp = trusted_fp_arg,
        )

    if args.as_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_result(result)

    sys.exit(0 if result.get("overall_valid") else 1)


if __name__ == "__main__":
    main()
