#!/usr/bin/env python3
"""
OMNIX ATF Standalone Receipt Verifier
======================================
Version: 1.2.0
ADR references: ADR-156 (DR) · ADR-157 (TAR) · ADR-158 (DTR) ·
                ADR-159 (RCR) · ADR-171 (SAC) · RFC-ATF-1/2/3

Verifies any ATF receipt type (DR, TAR, DTR, RCR, SAC) without requiring
the OMNIX platform or any OMNIX Python imports.

ZERO external dependencies for hash verification.
Optional: oqs-python or pypqc for Dilithium-3 / ML-DSA-65 signature verification.

Verification layers:
  L1 — Content hash (SHA-256 canonical JSON)    — always available
  L2 — PQC signature (ML-DSA-65 / Dilithium-3)  — requires oqs/pypqc
  L3 — Structural invariants (field presence)   — always available
  L4 — SAC semantic alignment map                — always available for SAC type

Canonical JSON algorithm (ATF-INV-006 / conformance_vectors.json):
  json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
  encoded as UTF-8, then SHA-256.

PQC signature note:
  Signatures are computed over content_hash.encode("utf-8") —
  i.e., the HEX STRING of the SHA-256 digest, not the raw digest bytes.

Usage:
  python omnix_atf_verify.py --receipt receipt.json [--type DR|TAR|DTR|RCR|SAC]
  python omnix_atf_verify.py --receipt receipt.json --public-key pub.b64
  python omnix_atf_verify.py --receipt receipt.json --type SAC --sac sac.json

Output: JSON verification report to stdout.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

__version__ = "1.2.0"

HASH_EXCLUDE_FIELDS = {
    "content_hash",
    "pqc_signature",
    "pqc_algorithm",
    "pqc_signature_a",
    "pqc_signature_b",
    "sac_content_hash",
    "spv_hash",
}

REQUIRED_FIELDS: Dict[str, List[str]] = {
    "DR": [
        "delegation_id", "delegator_id", "delegate_id", "task_scope",
        "authority_budget_delegator", "authority_budget_granted",
        "chain_root_id", "delegation_depth", "content_hash",
    ],
    "TAR": [
        "tar_id", "delegation_id", "agent_id", "execution_ns",
        "execution_ts", "admission_status", "content_hash",
    ],
    "DTR": [
        "dtr_id", "source_delegation_id", "source_domain", "target_domain",
        "source_agent_id", "target_agent_id", "translated_budget",
        "content_hash",
    ],
    "RCR": [
        "rcr_id", "tar_id", "delegation_id", "agent_id", "chain_root_id",
        "ces_score", "continuity_status", "content_hash",
    ],
    "SAC": [
        "sac_id", "runtime_a", "runtime_b", "semantic_alignment_map",
        "sac_content_hash",
    ],
    "STR": [
        "str_entry_id", "runtime_id", "term_id", "definition", "content_hash",
    ],
    "SPV": [
        "spv_id", "runtime_id", "atf_core_term_set", "spv_hash",
    ],
}

ATF_CORE_TERMS = (
    "AUTHORITY", "ADMISSIBILITY", "TRUST", "SOVEREIGNTY",
    "RISK", "ESCALATION", "REVOCATION", "LEGITIMACY",
)

RECEIPT_TYPE_PREFIXES = {
    "ATFDR-": "DR",
    "ATFTAR": "TAR",
    "ATFDTR": "DTR",
    "ATFRCR": "RCR",
    "OMNIX-SAC-": "SAC",
    "STR-": "STR",
    "OMNIX-SPV-": "SPV",
}

ID_FIELDS = {
    "DR": "delegation_id",
    "TAR": "tar_id",
    "DTR": "dtr_id",
    "RCR": "rcr_id",
    "SAC": "sac_id",
    "STR": "str_entry_id",
    "SPV": "spv_id",
}

HASH_FIELD = {
    "DR": "content_hash",
    "TAR": "content_hash",
    "DTR": "content_hash",
    "RCR": "content_hash",
    "SAC": "sac_content_hash",
    "STR": "content_hash",
    "SPV": "spv_hash",
}

PUBLIC_KEY_FIELD = {
    "DR": "delegator_public_key",
}


def canonical_json(obj: Dict[str, Any]) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def compute_content_hash(receipt: Dict[str, Any], receipt_type: str) -> str:
    if receipt_type == "SAC":
        parties_and_map = {
            "parties": {
                "runtime_a": {
                    "runtime_id": receipt.get("runtime_a", {}).get("runtime_id"),
                    "spv_id": receipt.get("runtime_a", {}).get("spv_id"),
                    "spv_hash": receipt.get("runtime_a", {}).get("spv_hash"),
                },
                "runtime_b": {
                    "runtime_id": receipt.get("runtime_b", {}).get("runtime_id"),
                    "spv_id": receipt.get("runtime_b", {}).get("spv_id"),
                    "spv_hash": receipt.get("runtime_b", {}).get("spv_hash"),
                },
            },
            "semantic_alignment_map": receipt.get("semantic_alignment_map", {}),
        }
        return hashlib.sha256(canonical_json(parties_and_map)).hexdigest()
    elif receipt_type == "SPV":
        core = receipt.get("atf_core_term_set", {})
        return hashlib.sha256(canonical_json(core)).hexdigest()
    else:
        clean = {k: v for k, v in receipt.items() if k not in HASH_EXCLUDE_FIELDS}
        return hashlib.sha256(canonical_json(clean)).hexdigest()


def autodetect_type(receipt: Dict[str, Any]) -> Optional[str]:
    for id_field in ("delegation_id", "tar_id", "dtr_id", "rcr_id",
                     "sac_id", "str_entry_id", "spv_id"):
        val = receipt.get(id_field, "")
        if val:
            for prefix, rtype in RECEIPT_TYPE_PREFIXES.items():
                if str(val).startswith(prefix):
                    return rtype
    return None


def load_pqc_verifier():
    try:
        import oqs
        class OQSVerifier:
            def verify(self, signature: bytes, message: bytes, public_key: bytes) -> bool:
                with oqs.Signature("Dilithium3") as sig:
                    return sig.verify(message, signature, public_key)
            def name(self) -> str:
                return "oqs-python/Dilithium3"
        return OQSVerifier()
    except ImportError:
        pass

    try:
        from pypqc import sign
        class PyPQCVerifier:
            def verify(self, signature: bytes, message: bytes, public_key: bytes) -> bool:
                from pypqc.sign import mldsa65
                return mldsa65.verify(message, signature, public_key)
            def name(self) -> str:
                return "pypqc/ML-DSA-65"
        return PyPQCVerifier()
    except (ImportError, Exception):
        pass

    return None


def verify_pqc_signature(
    signature_b64: str,
    message: str,
    public_key_b64: str,
    verifier: Any,
) -> Tuple[bool, str]:
    if verifier is None:
        return False, "SKIPPED — no PQC library (install oqs-python or pypqc)"
    try:
        sig = base64.b64decode(signature_b64)
        pub = base64.b64decode(public_key_b64)
        msg = message.encode("utf-8")
        valid = verifier.verify(sig, msg, pub)
        return valid, f"{'VALID' if valid else 'INVALID'} via {verifier.name()}"
    except Exception as exc:
        return False, f"ERROR: {exc}"


def check_invariants(receipt: Dict[str, Any], receipt_type: str) -> Dict[str, Any]:
    issues: List[str] = []

    if receipt_type == "DR":
        granted = receipt.get("authority_budget_granted", 0)
        delegator = receipt.get("authority_budget_delegator", 0)
        if granted > delegator:
            issues.append(
                f"ATF-INV-001 VIOLATED: budget_granted ({granted}) > "
                f"budget_delegator ({delegator})"
            )
        depth = receipt.get("delegation_depth", 0)
        if depth < 0:
            issues.append("ATF-INV-001: delegation_depth cannot be negative")

    elif receipt_type == "TAR":
        admission = receipt.get("admission_status", "")
        if admission not in ("ADMITTED", "REJECTED"):
            issues.append(f"TAR: admission_status must be ADMITTED or REJECTED, got '{admission}'")
        exec_ns = receipt.get("execution_ns")
        if exec_ns is not None and exec_ns < 0:
            issues.append("TAR: execution_ns cannot be negative")

    elif receipt_type == "DTR":
        src_budget = receipt.get("source_authority_budget", 1)
        translated = receipt.get("translated_budget", 0)
        if translated > src_budget:
            issues.append(
                f"CDTP-INV-001 VIOLATED: translated_budget ({translated}) > "
                f"source_authority_budget ({src_budget})"
            )

    elif receipt_type == "RCR":
        ces = receipt.get("ces_score", -1)
        if not (0 <= ces <= 100):
            issues.append(f"RGC-INV-002: ces_score must be 0–100, got {ces}")
        status = receipt.get("continuity_status", "")
        if status not in ("NOMINAL", "MONITORING", "WARNING", "CRITICAL", "HALT"):
            issues.append(f"RGC: continuity_status invalid: '{status}'")
        frag = receipt.get("fragmentation_score", 0)
        if frag > 0.95:
            issues.append(
                f"RGC-INV-004: fragmentation_score ({frag}) > AFG hard max 0.95"
            )

    elif receipt_type == "SAC":
        alignment_map = receipt.get("semantic_alignment_map", {})
        missing_terms = [t for t in ATF_CORE_TERMS if t not in alignment_map]
        if missing_terms:
            issues.append(
                f"SGIP-INV-002: semantic_alignment_map missing terms: {missing_terms}"
            )
        for term, entry in alignment_map.items():
            status = entry.get("status", "")
            if status not in ("ALIGNED", "ACKNOWLEDGED_DIVERGENCE", "UNRESOLVED"):
                issues.append(f"SGIP: invalid alignment status '{status}' for {term}")

    return {
        "invariant_violations": issues,
        "invariants_pass": len(issues) == 0,
    }


def verify_receipt(
    receipt: Dict[str, Any],
    receipt_type: str,
    public_key_b64: Optional[str] = None,
    pqc_verifier: Optional[Any] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "verifier_version": __version__,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "receipt_type": receipt_type,
        "receipt_id": receipt.get(ID_FIELDS.get(receipt_type, "id"), "UNKNOWN"),
    }

    missing_fields = [
        f for f in REQUIRED_FIELDS.get(receipt_type, [])
        if f not in receipt
    ]
    result["structural_check"] = {
        "missing_required_fields": missing_fields,
        "structural_valid": len(missing_fields) == 0,
    }

    hash_field = HASH_FIELD.get(receipt_type, "content_hash")
    stored_hash = receipt.get(hash_field, "")
    recomputed = compute_content_hash(receipt, receipt_type)
    hash_valid = recomputed == stored_hash

    result["hash_verification"] = {
        "hash_field": hash_field,
        "stored_hash": stored_hash,
        "recomputed_hash": recomputed,
        "hash_valid": hash_valid,
        "tamper_detected": not hash_valid,
    }

    embedded_pub = (
        receipt.get(PUBLIC_KEY_FIELD.get(receipt_type, "__none__"))
        or receipt.get("runtime_a", {}).get("issuer_public_key")
    )
    pub_key = public_key_b64 or embedded_pub

    pqc_results: Dict[str, Any] = {}
    sig_fields = []
    if receipt_type == "SAC":
        sig_fields = [("pqc_signature_a", "Runtime A"), ("pqc_signature_b", "Runtime B")]
    elif "pqc_signature" in receipt:
        sig_fields = [("pqc_signature", "Issuer")]

    for sig_field, label in sig_fields:
        sig_b64 = receipt.get(sig_field)
        if not sig_b64:
            pqc_results[sig_field] = {"status": "ABSENT", "label": label}
            continue
        if pub_key:
            valid, detail = verify_pqc_signature(sig_b64, stored_hash, pub_key, pqc_verifier)
            pqc_results[sig_field] = {
                "status": "VALID" if valid else "INVALID",
                "label": label,
                "detail": detail,
                "pqc_verified": valid,
            }
        else:
            pqc_results[sig_field] = {
                "status": "SKIPPED",
                "label": label,
                "detail": "No public key provided. Use --public-key or ensure it is embedded.",
            }

    result["pqc_verification"] = pqc_results

    result["invariant_check"] = check_invariants(receipt, receipt_type)

    all_pqc_valid = all(
        v.get("pqc_verified", False)
        for v in pqc_results.values()
        if isinstance(v, dict) and v.get("status") != "ABSENT"
    )
    any_pqc_verified = any(
        v.get("pqc_verified", False)
        for v in pqc_results.values()
        if isinstance(v, dict)
    )
    any_pqc_skipped = any(
        v.get("status") == "SKIPPED"
        for v in pqc_results.values()
        if isinstance(v, dict)
    )

    result["summary"] = {
        "structural_valid": result["structural_check"]["structural_valid"],
        "hash_valid": hash_valid,
        "pqc_verified": any_pqc_verified and all_pqc_valid,
        "invariants_pass": result["invariant_check"]["invariants_pass"],
        "pqc_skipped": any_pqc_skipped,
        "fully_verified": (
            result["structural_check"]["structural_valid"]
            and hash_valid
            and any_pqc_verified
            and all_pqc_valid
            and result["invariant_check"]["invariants_pass"]
            and not any_pqc_skipped
        ),
        "verification_level": (
            "FULL"
            if (hash_valid and any_pqc_verified and all_pqc_valid
                and result["invariant_check"]["invariants_pass"])
            else "HASH_ONLY" if hash_valid
            else "FAILED"
        ),
        "note": (
            "fully_verified=true requires successful PQC signature verification. "
            "Install oqs-python or pypqc for ML-DSA-65 verification."
            if any_pqc_skipped and hash_valid else ""
        ),
    }

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            f"OMNIX ATF Standalone Receipt Verifier v{__version__}\n"
            "Verifies ATF receipts offline without OMNIX platform access."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python omnix_atf_verify.py --receipt dr.json
  python omnix_atf_verify.py --receipt tar.json --type TAR
  python omnix_atf_verify.py --receipt dr.json --public-key pub.b64
  python omnix_atf_verify.py --receipt sac.json --type SAC
  python omnix_atf_verify.py --receipt dr.json --output-format pretty

Verification levels:
  FULL        — hash valid + PQC signature valid + invariants pass
  HASH_ONLY   — hash valid, but PQC library not available or no public key
  FAILED      — hash invalid (tampering detected)
        """,
    )
    parser.add_argument(
        "--receipt", required=True,
        help="Path to receipt JSON file"
    )
    parser.add_argument(
        "--type", choices=["DR", "TAR", "DTR", "RCR", "SAC", "STR", "SPV"],
        help="Receipt type (auto-detected from ID prefix if omitted)"
    )
    parser.add_argument(
        "--public-key",
        help="Path to file containing base64-encoded ML-DSA-65 public key"
    )
    parser.add_argument(
        "--public-key-b64",
        help="Base64-encoded ML-DSA-65 public key (inline)"
    )
    parser.add_argument(
        "--output-format", choices=["json", "pretty"], default="pretty",
        help="Output format (default: pretty)"
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if not fully_verified"
    )

    args = parser.parse_args()

    try:
        with open(args.receipt, "r", encoding="utf-8") as fh:
            receipt = json.load(fh)
    except Exception as exc:
        print(json.dumps({"error": f"Cannot load receipt: {exc}"}), file=sys.stderr)
        sys.exit(2)

    receipt_type = args.type or autodetect_type(receipt)
    if not receipt_type:
        print(json.dumps({
            "error": "Cannot auto-detect receipt type. Use --type DR|TAR|DTR|RCR|SAC|STR|SPV"
        }), file=sys.stderr)
        sys.exit(2)

    pub_key_b64: Optional[str] = None
    if args.public_key:
        try:
            with open(args.public_key, "r", encoding="utf-8") as fh:
                pub_key_b64 = fh.read().strip()
        except Exception as exc:
            print(json.dumps({"error": f"Cannot load public key: {exc}"}), file=sys.stderr)
            sys.exit(2)
    elif args.public_key_b64:
        pub_key_b64 = args.public_key_b64.strip()

    pqc_verifier = load_pqc_verifier()

    result = verify_receipt(
        receipt=receipt,
        receipt_type=receipt_type,
        public_key_b64=pub_key_b64,
        pqc_verifier=pqc_verifier,
    )

    if args.output_format == "pretty":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))

    if args.exit_code and not result["summary"]["fully_verified"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
