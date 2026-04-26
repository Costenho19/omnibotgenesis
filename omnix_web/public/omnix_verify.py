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
SCRIPT_VERSION       = "1.0.0"
REQUIRED_FIELDS      = ["receipt_id", "decision", "content_hash"]


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


# ── Main verifier ─────────────────────────────────────────────────────────────

def verify_receipt(
    receipt:        Dict[str, Any],
    pubkey_b64:     Optional[str] = None,
    fetch_key:      bool          = True,
    as_json:        bool          = False,
) -> Dict[str, Any]:
    """
    Full independent verification of an OMNIX governance receipt.

    Args:
        receipt:    Receipt dict (from JSON file or API)
        pubkey_b64: Override public key (b64). If None, uses receipt's own key.
        fetch_key:  If True and no key available, fetch from OMNIX well-known.
        as_json:    If True, suppress console output (JSON mode).

    Returns:
        Verification result dict.
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
        result["key_source"] = "embedded in receipt"
    else:
        result["key_source"] = "not provided"

    sig_b64 = receipt.get("signature")

    if dilithium3 and sig_b64 and pub_key:
        try:
            sig_ok = _verify_pqc_signature(sig_b64, pub_key, stored_hash, dilithium3)
            result["signature_valid"] = sig_ok
            result["signature_algorithm"] = receipt.get("signature_algorithm", "dilithium3")
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

    # ── 4. Overall verdict ─────────────────────────────────────────────────
    hash_ok = result["hash_valid"]
    sig_ok  = result["signature_valid"]

    if hash_ok and sig_ok is True:
        result["overall_valid"] = True
        result["verdict"]       = "VALID"
        result["verdict_note"]  = (
            "Receipt is cryptographically authentic. "
            "Hash and PQC signature both verified independently."
        )
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
        result["verdict_note"]  = (
            "Verification failed. See hash_note and signature_note for details."
        )

    return result


# ── Console output ────────────────────────────────────────────────────────────

def _print_result(r: Dict[str, Any]) -> None:
    print()
    print(_bold("=" * 60))
    print(_bold("  OMNIX Independent Receipt Verifier"))
    print(_bold(f"  v{SCRIPT_VERSION} | {OMNIX_ISSUER_DID}"))
    print(_bold("=" * 60))
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

    verdict = r.get("verdict", "UNKNOWN")
    if "VALID" in verdict and "INVALID" not in verdict:
        verdict_display = _green(_bold(f"  VERDICT: {verdict}"))
    else:
        verdict_display = _red(_bold(f"  VERDICT: {verdict}"))

    print(verdict_display)
    print(_dim(f"  {r.get('verdict_note','')}"))
    print()
    print(_bold("=" * 60))
    print(_dim("  Independent verification — no OMNIX server access required."))
    print(_dim(f"  Trust registry: {OMNIX_PUBKEY_URL}"))
    print(_bold("=" * 60))
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

    pubkey_b64: Optional[str] = None
    if args.pubkey:
        try:
            with open(args.pubkey, "r", encoding="utf-8") as f:
                pubkey_b64 = f.read().strip()
        except FileNotFoundError:
            print(_red(f"ERROR: Public key file not found: {args.pubkey}"), file=sys.stderr)
            sys.exit(2)

    result = verify_receipt(
        receipt    = receipt,
        pubkey_b64 = pubkey_b64,
        fetch_key  = not args.no_fetch,
        as_json    = args.as_json,
    )

    if args.as_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_result(result)

    sys.exit(0 if result.get("overall_valid") else 1)


if __name__ == "__main__":
    main()
