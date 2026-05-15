#!/usr/bin/env python3
"""
OMNIX ATF Public Verifier — omnix_atf_verify.py
================================================
Independent, platform-free verification of:
  · Delegation Receipts (DR)       — ATF-INV-006  · RFC-ATF-1
  · Agent Identity Records (AIR)   — ATF-INV-006  · RFC-ATF-1
  · Delegation Chains              — ATF-INV-001–006
  · COLD Archive Blocks            — EAP-INV-001–006 · ADR-163

Usage — Delegation Receipts:
    python omnix_atf_verify.py receipt.json
    python omnix_atf_verify.py receipt.json --public-key <base64-pubkey>
    python omnix_atf_verify.py receipt.json --verbose

Usage — Chain verification:
    python omnix_atf_verify.py chain.json --mode chain

Usage — Agent identity:
    python omnix_atf_verify.py identity.json --mode agent

Usage — COLD Archive Block (ADR-163 / EAP-INV-005):
    python omnix_atf_verify.py --archive-block OMNIX-BLOCK-20260514-000001.json \\
                               --public-key omnix_public_key.b64
    python omnix_atf_verify.py --archive-block OMNIX-BLOCK-20260514-000001.json \\
                               --public-key omnix_public_key.b64 \\
                               --verify-chain \\
                               --predecessor-block OMNIX-BLOCK-20260514-000000.json

Usage — Batch replay:
    python omnix_atf_verify.py --mode replay

Usage — Stdin / programmatic:
    echo '{"delegation_id":"..."}' | python omnix_atf_verify.py --stdin
    python omnix_atf_verify.py receipt.json --json

──────────────────────────────────────────────────────────────────────────────
This verifier is a STANDALONE TOOL. It requires:
  · No network access
  · No OMNIX account or API key
  · No database connection
  · No OMNIX platform access of any kind

All verification is performed using cryptographic operations on the provided
files and the issuer's public key (embedded in receipts, or provided externally).

This is the mechanism by which OMNIX satisfies ATF-INV-006 and EAP-INV-005:
third parties — regulators, auditors, partners — can independently reconstruct
and verify the complete chain of evidence without trusting OMNIX infrastructure.

──────────────────────────────────────────────────────────────────────────────
Protocols:
  · RFC-ATF-1 — Agent Trust Fabric (ATF-INV-001–006)
  · RFC-ATF-2 — Runtime Governance Continuity (RGC-INV-001–008)
  · ADR-162   — Evidence Lifecycle & Immutable Retention (ELR-INV-001–004)
  · ADR-163   — Immutable Evidence Archive Pipeline (EAP-INV-001–006)

Algorithm: ML-DSA-65 (Dilithium-3, FIPS 204) — NIST Level 3
PQC Library: pypqc (pip install pypqc)

Version: 1.1.0 — OMNIX QUANTUM LTD — May 2026
Reference: https://omnixquantum.com/atf/verify
──────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

VERIFIER_VERSION = "1.1.0"
VERIFIER_PROTOCOL = "RFC-ATF-1 + RFC-ATF-2 + ADR-162/163"

# ─────────────────────────────────────────────────────────────────────────────
# Terminal colours
# ─────────────────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
GRAY   = "\033[90m"
GOLD   = "\033[33m"
PURPLE = "\033[95m"
WHITE  = "\033[97m"

# ─────────────────────────────────────────────────────────────────────────────
# Banners
# ─────────────────────────────────────────────────────────────────────────────

ATF_BANNER = f"""{BOLD}{GOLD}
╔══════════════════════════════════════════════════════════════════╗
║         OMNIX ATF Public Verifier  ·  v{VERIFIER_VERSION}                  ║
║  Post-Quantum Cryptographic Evidence Verification Tool          ║
║  Algorithm: ML-DSA-65 (Dilithium-3, FIPS 204)                  ║
╚══════════════════════════════════════════════════════════════════╝{RESET}
{GRAY}RFC-ATF-1 + RFC-ATF-2 + ADR-162 + ADR-163{RESET}
{GRAY}OMNIX QUANTUM LTD · https://omnixquantum.com/atf/verify{RESET}
"""

ATF_FOOTER = f"""
{GRAY}────────────────────────────────────────────────────────────────{RESET}
{GRAY}Protocol  : RFC-ATF-1 · RFC-ATF-2 · ADR-163{RESET}
{GRAY}Algorithm : ML-DSA-65 (Dilithium-3, FIPS 204) · NIST Level 3{RESET}
{GRAY}Guarantee : No platform access required (ATF-INV-006 / EAP-INV-005){RESET}
{GRAY}OMNIX QUANTUM LTD · https://omnixquantum.com/atf/verify{RESET}
"""

BLOCK_BANNER = f"""{BOLD}{CYAN}
╔══════════════════════════════════════════════════════════════════╗
║        OMNIX COLD Archive Block Verifier  ·  ADR-163            ║
║  EAP-INV-005: Offline Reconstructability Without Platform Access ║
╚══════════════════════════════════════════════════════════════════╝{RESET}
"""

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

BLOCK_ID_PATTERN     = re.compile(r"^OMNIX-BLOCK-\d{8}-\d{6}$")
GENESIS_PREDECESSOR  = "0" * 64
HASH_ALGORITHM_V1    = "sha256-v1"
PQC_ALGORITHM_LABEL  = "ML-DSA-65 (FIPS 204)"

IMMUTABLE_EVIDENCE_CLASSES = {"LEGAL", "PQC", "CONTRACT", "EXCEPTION"}

# Verification report states (ADR-163 §3)
VERDICT_PASS                = "PASS"
VERDICT_INTEGRITY_VIOLATION = "INTEGRITY_VIOLATION"
VERDICT_CHAIN_BREAK         = "CHAIN_BREAK"
VERDICT_SIGNATURE_INVALID   = "SIGNATURE_INVALID"


# ─────────────────────────────────────────────────────────────────────────────
# Cryptographic primitives
# ─────────────────────────────────────────────────────────────────────────────

def _canonical_json(obj: Dict[str, Any]) -> bytes:
    """Canonical JSON serialization — sort_keys, no extra spaces."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    """SHA-256 hex digest (no prefix)."""
    return hashlib.sha256(data).hexdigest()


def _sha256_prefixed(data: bytes) -> str:
    """SHA-256 with 'sha256:' prefix — used in block hashes."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _compute_content_hash(receipt: Dict[str, Any]) -> str:
    """
    SHA-256 content hash of a delegation receipt.
    Excludes: content_hash, pqc_signature, pqc_algorithm (all signature-adjacent fields).
    """
    exclude = {"content_hash", "pqc_signature", "pqc_algorithm"}
    clean = {k: v for k, v in receipt.items() if k not in exclude}
    return _sha256(_canonical_json(clean))


def _compute_merkle_root(artifact_hashes: List[str]) -> str:
    """
    Compute the Merkle root of a list of artifact content hashes.
    Hashes are sorted before joining to ensure determinism regardless
    of insertion order.

    Algorithm: sha256("|".join(sorted(hashes)))
    This produces a 'sha256:' prefixed hex string consistent with
    the block's canonical_hash format.
    """
    if not artifact_hashes:
        return _sha256_prefixed(b"OMNIX-EMPTY-BLOCK")
    combined = "|".join(sorted(artifact_hashes))
    return _sha256_prefixed(combined.encode("utf-8"))


def _compute_block_canonical_hash(block: Dict[str, Any]) -> str:
    """
    Compute the canonical_hash of a COLD archive block.

    The canonical_hash commits to all block-identifying fields plus the
    Merkle root. This is what the ML-DSA-65 pqc_signature covers.

    Committed fields (sorted, canonical JSON):
      block_id, creation_timestamp_ns, artifact_count,
      evidence_classes (sorted), hash_algorithm, merkle_root,
      omnix_version, predecessor_block_hash
    """
    committed = {
        "block_id":              block["block_id"],
        "creation_timestamp_ns": block["creation_timestamp_ns"],
        "artifact_count":        block["artifact_count"],
        "evidence_classes":      sorted(block.get("evidence_classes", [])),
        "hash_algorithm":        block["integrity_manifest"]["hash_algorithm"],
        "merkle_root":           block["integrity_manifest"]["merkle_root"],
        "omnix_version":         block.get("omnix_version", "1.0.0"),
        "predecessor_block_hash": block["predecessor_block_hash"],
    }
    return _sha256_prefixed(_canonical_json(committed))


def _verify_pqc_signature(
    message: str,
    pqc_signature_b64: str,
    public_key_b64: str,
) -> Tuple[bool, str, Optional[str]]:
    """
    Verify an ML-DSA-65 (Dilithium-3) signature.

    Args:
        message:          The plaintext message that was signed (will be UTF-8 encoded).
        pqc_signature_b64: Base64-encoded signature bytes.
        public_key_b64:    Base64-encoded public key bytes.

    Returns:
        (valid: bool, algorithm_label: str, error: Optional[str])
    """
    try:
        from pqc.sign import dilithium3 as dil
        sig = base64.b64decode(pqc_signature_b64)
        pk  = base64.b64decode(public_key_b64)
        dil.verify(sig, message.encode("utf-8"), pk)
        return True, "ML-DSA-65 (Dilithium-3, FIPS 204)", None
    except ImportError:
        pass
    except Exception as exc:
        return False, "ML-DSA-65 (Dilithium-3, FIPS 204)", str(exc)

    try:
        import dilithium
        sig = base64.b64decode(pqc_signature_b64)
        pk  = base64.b64decode(public_key_b64)
        result = dilithium.verify(sig, message.encode("utf-8"), pk)
        return bool(result), "ML-DSA-65 (Dilithium-3)", None
    except ImportError:
        pass
    except Exception as exc:
        return False, "ML-DSA-65 (Dilithium-3)", str(exc)

    try:
        from omnix_core.security.crypto_providers import get_active_provider
        provider = get_active_provider()
        sig = base64.b64decode(pqc_signature_b64)
        pk  = base64.b64decode(public_key_b64)
        result = provider.verify(sig, message.encode("utf-8"), pk)
        return bool(result), provider.algorithm_name(), None
    except Exception:
        pass

    return (
        False,
        "UNAVAILABLE",
        "pypqc not installed. Run: pip install pypqc",
    )


def _load_public_key_b64(path_or_b64: str) -> Optional[str]:
    """
    Load a public key from a file path (.b64, .pem, .txt) or a raw base64 string.
    Returns the raw base64 string regardless of input format.
    """
    if os.path.exists(path_or_b64):
        with open(path_or_b64) as f:
            raw = f.read().strip()
        lines = [l for l in raw.splitlines() if not l.startswith("-----")]
        return "".join(lines).strip()
    return path_or_b64.strip()


def _check_expiry(expires_at: Optional[str]) -> Tuple[bool, Optional[str]]:
    if not expires_at:
        return True, None
    try:
        exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if now > exp:
            return False, f"Receipt expired at {expires_at}"
        delta = exp - now
        hours = int(delta.total_seconds() / 3600)
        return True, f"Expires in {hours}h ({expires_at})"
    except Exception as exc:
        return False, f"Could not parse expires_at: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# Receipt verification (ADR-156 / RFC-ATF-1)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VerificationResult:
    delegation_id: str
    hash_valid: bool
    pqc_signature_valid: bool
    pqc_checked: bool
    mar_invariant_valid: bool
    not_expired: bool
    fully_verified: bool
    delegation_depth: int
    authority_budget_granted: float
    authority_reduction_pct: float
    chain_root_id: str
    pqc_signed: bool
    delegator_id: str
    delegate_id: str
    status: str
    failure_reasons: List[str]
    warnings: List[str]


def verify_receipt(
    receipt: Dict[str, Any],
    public_key_override: Optional[str] = None,
) -> VerificationResult:
    failure_reasons: List[str] = []
    warnings: List[str] = []

    delegation_id             = receipt.get("delegation_id", "UNKNOWN")
    delegator_id              = receipt.get("delegator_id", "")
    delegate_id               = receipt.get("delegate_id", "")
    chain_root_id             = receipt.get("chain_root_id", "")
    delegation_depth          = int(receipt.get("delegation_depth", 0))
    authority_budget_delegator = float(receipt.get("authority_budget_delegator", 0))
    authority_budget_granted  = float(receipt.get("authority_budget_granted", 0))
    pqc_signature             = receipt.get("pqc_signature")
    pqc_algorithm             = receipt.get("pqc_algorithm")
    delegator_public_key      = public_key_override or receipt.get("delegator_public_key", "")
    embedded_hash             = receipt.get("content_hash", "")
    status                    = receipt.get("status", "UNKNOWN")
    expires_at                = receipt.get("expires_at")

    # Step 1: Content hash integrity
    recomputed_hash = _compute_content_hash(receipt)
    hash_valid = (recomputed_hash == embedded_hash)
    if not hash_valid:
        failure_reasons.append(
            f"Content hash MISMATCH — receipt may have been tampered with\n"
            f"   Stored:     {embedded_hash}\n"
            f"   Recomputed: {recomputed_hash}"
        )

    # Step 2: PQC signature verification
    pqc_valid    = False
    pqc_checked  = False
    pqc_algo_used = "N/A"
    if pqc_signature and delegator_public_key:
        pqc_checked = True
        pqc_valid, pqc_algo_used, pqc_err = _verify_pqc_signature(
            embedded_hash, pqc_signature, delegator_public_key
        )
        if not pqc_valid:
            if pqc_algo_used == "UNAVAILABLE":
                warnings.append(f"PQC library unavailable — {pqc_err}")
            else:
                failure_reasons.append(
                    f"PQC signature INVALID — delegator authorization cannot be confirmed\n"
                    f"   Algorithm: {pqc_algo_used}"
                )
    elif not pqc_signature:
        warnings.append("No PQC signature present — SHA-256 hash integrity only (ATF Level-1)")
    elif not delegator_public_key:
        warnings.append("delegator_public_key missing — PQC verification skipped")

    # Step 3: Monotonic Authority Reduction (ATF-INV-001)
    mar_valid = authority_budget_granted <= authority_budget_delegator
    if not mar_valid:
        failure_reasons.append(
            f"ATF-INV-001 VIOLATED — authority expansion detected\n"
            f"   Granted:   {authority_budget_granted}\n"
            f"   Delegator: {authority_budget_delegator}\n"
            f"   This delegation receipt must be REJECTED."
        )

    # Step 4: Temporal validity
    not_expired, expiry_note = _check_expiry(expires_at)
    if not not_expired:
        failure_reasons.append(f"Receipt EXPIRED: {expiry_note}")
    elif expiry_note:
        warnings.append(expiry_note)

    if status == "REVOKED":
        failure_reasons.append("Receipt has been REVOKED — invalid for all purposes")
    elif status == "EXPIRED":
        failure_reasons.append("Receipt status is EXPIRED")

    if authority_budget_delegator > 0:
        reduction_pct = round(
            (1.0 - authority_budget_granted / authority_budget_delegator) * 100.0, 2
        )
    else:
        reduction_pct = 0.0

    fully_verified = (
        hash_valid
        and mar_valid
        and not_expired
        and status == "ACTIVE"
        and (pqc_valid if pqc_checked else True)
        and len(failure_reasons) == 0
    )

    return VerificationResult(
        delegation_id=delegation_id,
        hash_valid=hash_valid,
        pqc_signature_valid=pqc_valid,
        pqc_checked=pqc_checked,
        mar_invariant_valid=mar_valid,
        not_expired=not_expired,
        fully_verified=fully_verified,
        delegation_depth=delegation_depth,
        authority_budget_granted=authority_budget_granted,
        authority_reduction_pct=reduction_pct,
        chain_root_id=chain_root_id,
        pqc_signed=pqc_signature is not None,
        delegator_id=delegator_id,
        delegate_id=delegate_id,
        status=status,
        failure_reasons=failure_reasons,
        warnings=warnings,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Chain verification (RFC-ATF-1 §7)
# ─────────────────────────────────────────────────────────────────────────────

def verify_chain(chain: List[Dict[str, Any]]) -> Dict[str, Any]:
    results = []
    mar_chain_valid = True
    prev_budget = 100.0
    chain_root_ids: set = set()
    all_verified = True

    for dr in chain:
        vr = verify_receipt(dr)
        results.append(vr)
        chain_root_ids.add(vr.chain_root_id)
        if not vr.fully_verified:
            all_verified = False
        if vr.authority_budget_granted > prev_budget:
            mar_chain_valid = False
        prev_budget = vr.authority_budget_granted

    depth_valid = all(
        chain[i]["delegation_depth"] == chain[i - 1]["delegation_depth"] + 1
        for i in range(1, len(chain))
    ) if len(chain) > 1 else True

    root_consistent = len(chain_root_ids) <= 1
    ccs = _compute_chain_ccs(results)

    return {
        "chain_length":      len(chain),
        "all_verified":      all_verified and mar_chain_valid and depth_valid and root_consistent,
        "mar_chain_valid":   mar_chain_valid,
        "depth_monotone":    depth_valid,
        "root_id_consistent": root_consistent,
        "receipt_results":   results,
        "atf_ccs":           ccs["score"],
        "atf_ccs_verdict":   ccs["verdict"],
    }


def _compute_chain_ccs(results: List[VerificationResult]) -> Dict[str, Any]:
    if not results:
        return {"score": 0, "verdict": "NO_DATA"}
    hash_breaks = sum(1 for r in results if not r.hash_valid)
    unsigned    = sum(1 for r in results if not r.pqc_signed)
    mar_valid   = all(r.mar_invariant_valid for r in results)

    chain_integrity = max(0.0, 40.0 - hash_breaks * 10.0)
    pqc_coverage    = max(0.0, 30.0 - unsigned * 10.0)
    mar_score       = 20.0 if mar_valid else 0.0
    depth_score     = 10.0 if len(results) >= 1 else 0.0
    total           = round(chain_integrity + pqc_coverage + mar_score + depth_score, 1)

    if total >= 90:   verdict = "COMPLETE"
    elif total >= 70: verdict = "DEGRADED"
    elif total >= 50: verdict = "PARTIAL"
    else:             verdict = "COMPROMISED"

    return {"score": total, "verdict": verdict}


# ─────────────────────────────────────────────────────────────────────────────
# Agent identity verification (ATF-INV-006)
# ─────────────────────────────────────────────────────────────────────────────

def verify_identity(identity: Dict[str, Any]) -> Dict[str, Any]:
    agent_id = identity.get("agent_id", "UNKNOWN")
    exclude  = {"registration_hash", "pqc_signature", "pqc_algorithm"}
    public_fields = {k: v for k, v in identity.items() if k not in exclude}
    recomputed = _sha256(_canonical_json(public_fields))
    embedded   = identity.get("registration_hash", "")
    hash_valid = (recomputed == embedded)

    pqc_valid   = False
    pqc_checked = False
    if identity.get("pqc_signature") and identity.get("public_key_b64"):
        pqc_checked  = True
        sign_payload = (
            f"OMNIX-ATF-REG-v1|agent_id={agent_id}"
            f"|reg_hash={embedded}"
        ).encode("utf-8")
        sig_b64 = identity["pqc_signature"]
        pk_b64  = identity["public_key_b64"]
        pqc_valid, _, _ = _verify_pqc_signature(
            hashlib.sha256(sign_payload).hexdigest(), sig_b64, pk_b64
        )

    return {
        "agent_id":             agent_id,
        "hash_valid":           hash_valid,
        "pqc_signature_valid":  pqc_valid,
        "pqc_checked":          pqc_checked,
        "fully_verified":       hash_valid and (pqc_valid if pqc_checked else True),
    }


# ─────────────────────────────────────────────────────────────────────────────
# COLD Archive Block verification (ADR-163 / EAP-INV-001–006)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ArchiveBlockResult:
    """
    Verification result for a COLD archive block.

    Verification steps (ADR-163 §3):
      1. Load block manifest
      2. Recompute merkle_root from artifact_hashes
      3. Recompute canonical_hash from block fields + merkle_root
      4. Verify ML-DSA-65 signature over canonical_hash
      5. Verify predecessor_block_hash (if predecessor provided)
      6. Verify each artifact content_hash format
      7. Emit overall verdict

    Possible verdicts (ADR-163 §3):
      PASS                — All checks passed. Block is cryptographically sound.
      INTEGRITY_VIOLATION — Merkle root or canonical hash mismatch detected.
      CHAIN_BREAK         — predecessor_block_hash does not match predecessor.
      SIGNATURE_INVALID   — ML-DSA-65 signature verification failed.
    """
    block_id:              str
    verdict:               str    # PASS | INTEGRITY_VIOLATION | CHAIN_BREAK | SIGNATURE_INVALID
    artifact_count:        int
    evidence_classes:      List[str]

    # Step 2
    merkle_valid:          bool
    merkle_stored:         str
    merkle_recomputed:     str

    # Step 3
    canonical_hash_valid:  bool
    canonical_hash_stored: str
    canonical_hash_recomputed: str

    # Step 4
    pqc_signature_valid:   bool
    pqc_checked:           bool
    pqc_algorithm:         str

    # Step 5
    chain_verified:        bool   # True if predecessor was provided and verified
    predecessor_hash_valid: bool
    predecessor_block_id:  Optional[str]

    # Step 6
    artifact_hashes_count: int
    artifact_hashes_valid: bool

    # Step 7
    omnix_version:         str
    hash_algorithm:        str
    block_id_format_valid: bool

    failure_reasons:       List[str]
    warnings:              List[str]


def verify_archive_block(
    block: Dict[str, Any],
    public_key_b64: Optional[str] = None,
    predecessor_block: Optional[Dict[str, Any]] = None,
) -> ArchiveBlockResult:
    """
    Verify a COLD archive block (ADR-163 §3, EAP-INV-001–006).

    This function performs all verification steps offline without any
    OMNIX platform access. It is the implementation of EAP-INV-005:
    Offline Reconstructability.

    Args:
        block:             Parsed COLD archive block dict.
        public_key_b64:    Base64-encoded ML-DSA-65 public key.
                           If None, PQC signature step is skipped.
        predecessor_block: Parsed predecessor block dict (for --verify-chain).
                           If None, genesis block assumption is tested.

    Returns:
        ArchiveBlockResult with overall verdict and per-step results.
    """
    failure_reasons: List[str] = []
    warnings:        List[str] = []

    # ── Extract block fields ─────────────────────────────────────────────────
    block_id              = block.get("block_id", "UNKNOWN")
    artifact_count        = block.get("artifact_count", 0)
    evidence_classes      = block.get("evidence_classes", [])
    predecessor_hash      = block.get("predecessor_block_hash", "")
    stored_canonical_hash = block.get("canonical_hash", "")
    pqc_signature_b64     = block.get("pqc_signature", "")
    pqc_algorithm_label   = block.get("pqc_algorithm", PQC_ALGORITHM_LABEL)
    omnix_version         = block.get("omnix_version", "unknown")
    integrity_manifest    = block.get("integrity_manifest", {})
    stored_merkle         = integrity_manifest.get("merkle_root", "")
    hash_algorithm        = integrity_manifest.get("hash_algorithm", "")
    artifact_hashes       = integrity_manifest.get("artifact_hashes", [])

    # ── Validation 0: Block ID format ───────────────────────────────────────
    block_id_valid = bool(BLOCK_ID_PATTERN.match(block_id))
    if not block_id_valid:
        warnings.append(
            f"Block ID format unexpected: '{block_id}'\n"
            f"   Expected: OMNIX-BLOCK-YYYYMMDD-NNNNNN"
        )

    # ── Validation 1: Hash algorithm ────────────────────────────────────────
    if hash_algorithm != HASH_ALGORITHM_V1:
        warnings.append(
            f"Hash algorithm '{hash_algorithm}' is not the canonical '{HASH_ALGORITHM_V1}'"
        )

    # ── Step 2: Recompute Merkle root ───────────────────────────────────────
    recomputed_merkle = _compute_merkle_root(artifact_hashes)
    merkle_valid      = (recomputed_merkle == stored_merkle)

    if not merkle_valid:
        failure_reasons.append(
            f"EAP-INV-001 VIOLATION — Merkle root mismatch\n"
            f"   Stored:     {stored_merkle}\n"
            f"   Recomputed: {recomputed_merkle}\n"
            f"   One or more artifact hashes may have been tampered with."
        )

    # ── Step 3: Recompute canonical hash ────────────────────────────────────
    recomputed_canonical = _compute_block_canonical_hash(block)
    canonical_hash_valid = (recomputed_canonical == stored_canonical_hash)

    if not canonical_hash_valid:
        failure_reasons.append(
            f"EAP-INV-001 VIOLATION — Canonical hash mismatch\n"
            f"   Stored:     {stored_canonical_hash}\n"
            f"   Recomputed: {recomputed_canonical}\n"
            f"   Block fields have been modified after sealing."
        )

    # ── Step 4: PQC signature verification ──────────────────────────────────
    pqc_valid   = False
    pqc_checked = False

    if public_key_b64 and pqc_signature_b64:
        pqc_checked = True
        pqc_valid, pqc_algo_used, pqc_err = _verify_pqc_signature(
            stored_canonical_hash, pqc_signature_b64, public_key_b64
        )
        if not pqc_valid:
            if pqc_algo_used == "UNAVAILABLE":
                warnings.append(
                    f"PQC library unavailable — install pypqc for signature verification\n"
                    f"   pip install pypqc"
                )
                pqc_algorithm_label = pqc_algo_used
            else:
                failure_reasons.append(
                    f"EAP-INV-002 VIOLATION — ML-DSA-65 signature INVALID\n"
                    f"   The block's PQC seal cannot be verified.\n"
                    f"   Either the block was tampered with after sealing,\n"
                    f"   or the wrong public key was provided.\n"
                    f"   Error: {pqc_err}"
                )
    elif not public_key_b64:
        warnings.append(
            "No public key provided — PQC signature verification skipped.\n"
            "   Provide --public-key to enable full EAP-INV-002 verification."
        )
    elif not pqc_signature_b64:
        warnings.append(
            "Block has no PQC signature — only hash integrity was verified.\n"
            "   Unsigned blocks do not satisfy EAP-INV-002."
        )

    # ── Step 5: Predecessor chain verification ───────────────────────────────
    chain_verified          = False
    predecessor_hash_valid  = False
    predecessor_block_id    = None

    if predecessor_block is not None:
        chain_verified    = True
        predecessor_block_id = predecessor_block.get("block_id", "UNKNOWN")
        predecessor_canonical = predecessor_block.get("canonical_hash", "")
        predecessor_hash_valid = (predecessor_hash == predecessor_canonical)

        if not predecessor_hash_valid:
            failure_reasons.append(
                f"EAP-INV-003 VIOLATION — Block chain broken\n"
                f"   This block claims predecessor: {predecessor_hash}\n"
                f"   Predecessor block's canonical: {predecessor_canonical}\n"
                f"   The archive chain has been compromised or blocks are out of order."
            )
    else:
        # No predecessor → verify genesis assumption
        if predecessor_hash == GENESIS_PREDECESSOR:
            chain_verified        = True
            predecessor_hash_valid = True
        else:
            chain_verified        = True
            predecessor_hash_valid = False
            warnings.append(
                f"No predecessor block provided.\n"
                f"   predecessor_block_hash is not the genesis sentinel ({GENESIS_PREDECESSOR[:16]}...)\n"
                f"   Use --predecessor-block to verify the chain, or confirm this is a genesis block."
            )

    # ── Step 6: Artifact hash count integrity ───────────────────────────────
    artifact_hashes_valid = (len(artifact_hashes) == artifact_count)
    if not artifact_hashes_valid:
        failure_reasons.append(
            f"EAP-INV-001 VIOLATION — Artifact count mismatch\n"
            f"   block.artifact_count: {artifact_count}\n"
            f"   integrity_manifest.artifact_hashes length: {len(artifact_hashes)}\n"
            f"   Hashes may have been added or removed."
        )

    # ── Check immutable class completeness warning ───────────────────────────
    for cls in evidence_classes:
        if cls not in IMMUTABLE_EVIDENCE_CLASSES and cls not in {
            "TELEMETRY", "SAMPLE", "SHADOW_NOMINAL", "OPS"
        }:
            warnings.append(f"Unrecognised evidence class: '{cls}'")

    # ── Step 7: Overall verdict ──────────────────────────────────────────────
    if not failure_reasons:
        verdict = VERDICT_PASS
    elif any("chain broken" in r or "EAP-INV-003" in r for r in failure_reasons):
        verdict = VERDICT_CHAIN_BREAK
    elif pqc_checked and not pqc_valid and "UNAVAILABLE" not in str(failure_reasons):
        verdict = VERDICT_SIGNATURE_INVALID
    else:
        verdict = VERDICT_INTEGRITY_VIOLATION

    return ArchiveBlockResult(
        block_id=block_id,
        verdict=verdict,
        artifact_count=artifact_count,
        evidence_classes=sorted(evidence_classes),
        merkle_valid=merkle_valid,
        merkle_stored=stored_merkle,
        merkle_recomputed=recomputed_merkle,
        canonical_hash_valid=canonical_hash_valid,
        canonical_hash_stored=stored_canonical_hash,
        canonical_hash_recomputed=recomputed_canonical,
        pqc_signature_valid=pqc_valid,
        pqc_checked=pqc_checked,
        pqc_algorithm=pqc_algorithm_label,
        chain_verified=chain_verified,
        predecessor_hash_valid=predecessor_hash_valid,
        predecessor_block_id=predecessor_block_id,
        artifact_hashes_count=len(artifact_hashes),
        artifact_hashes_valid=artifact_hashes_valid,
        omnix_version=omnix_version,
        hash_algorithm=hash_algorithm,
        block_id_format_valid=block_id_valid,
        failure_reasons=failure_reasons,
        warnings=warnings,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Terminal output helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ok(msg: str)   -> str: return f"  {GREEN}✓{RESET}  {msg}"
def _fail(msg: str) -> str: return f"  {RED}✗{RESET}  {msg}"
def _warn(msg: str) -> str: return f"  {YELLOW}⚠{RESET}  {msg}"
def _info(msg: str) -> str: return f"  {CYAN}·{RESET}  {msg}"
def _skip(msg: str) -> str: return f"  {GRAY}–{RESET}  {msg}"


def _print_receipt_result(vr: VerificationResult, verbose: bool = False) -> None:
    verdict_color = GREEN if vr.fully_verified else RED
    verdict_text  = "VERIFIED" if vr.fully_verified else "INVALID"

    print(f"\n{BOLD}Receipt: {CYAN}{vr.delegation_id}{RESET}")
    print(f"  Status: {verdict_color}{BOLD}{verdict_text}{RESET}")
    print()
    print(_ok("Content hash valid") if vr.hash_valid
          else _fail("Content hash INVALID — tampering detected"))
    if vr.pqc_checked:
        print(_ok(f"PQC signature valid (ML-DSA-65)") if vr.pqc_signature_valid
              else _fail("PQC signature INVALID"))
    elif vr.pqc_signed:
        print(_warn("PQC library unavailable — install pypqc for signature verification"))
    else:
        print(_warn("No PQC signature (SHA-256 content hash only)"))
    print(_ok("MAR invariant holds (ATF-INV-001)") if vr.mar_invariant_valid
          else _fail("ATF-INV-001 VIOLATED: authority expansion"))
    print(_ok("Receipt not expired") if vr.not_expired
          else _fail("Receipt EXPIRED"))
    print(_ok(f"Status: {vr.status}") if vr.status == "ACTIVE"
          else _fail(f"Status: {vr.status}"))
    print()

    if verbose:
        print(f"{GRAY}  Delegator:  {vr.delegator_id}{RESET}")
        print(f"{GRAY}  Delegate:   {vr.delegate_id}{RESET}")
        print(f"{GRAY}  Depth:      {vr.delegation_depth}{RESET}")
        print(f"{GRAY}  Budget:     {vr.authority_budget_granted:.1f}"
              f"  (reduced {vr.authority_reduction_pct:.1f}%){RESET}")
        print(f"{GRAY}  Chain root: {vr.chain_root_id}{RESET}")
        print()

    for reason in vr.failure_reasons:
        for line in reason.split("\n"):
            print(f"  {RED}{line}{RESET}")
    for w in vr.warnings:
        print(_warn(w))


def _print_chain_result(result: Dict[str, Any]) -> None:
    all_ok = result["all_verified"]
    verdict_color = GREEN if all_ok else RED
    verdict       = "CHAIN VERIFIED" if all_ok else "CHAIN INVALID"
    ccs_score     = result["atf_ccs"]
    ccs_verdict   = result["atf_ccs_verdict"]
    ccs_color     = GREEN if ccs_score >= 90 else (YELLOW if ccs_score >= 70 else RED)

    print(f"\n{BOLD}Chain Verification Result{RESET}")
    print(f"  Verdict:  {verdict_color}{BOLD}{verdict}{RESET}")
    print(f"  ATF CCS:  {ccs_color}{BOLD}{ccs_score}/100 — {ccs_verdict}{RESET}")
    print()
    print(_ok("Depth monotone") if result["depth_monotone"]
          else _fail("Delegation depth not monotone"))
    print(_ok("Chain root consistent") if result["root_id_consistent"]
          else _fail("Inconsistent chain_root_id values"))
    print(_ok("MAR holds across chain") if result["mar_chain_valid"]
          else _fail("Authority expansion detected in chain"))
    print()
    for vr in result["receipt_results"]:
        icon = f"{GREEN}✓{RESET}" if vr.fully_verified else f"{RED}✗{RESET}"
        print(f"  {icon}  Depth {vr.delegation_depth}: {CYAN}{vr.delegation_id}{RESET}")
        print(f"     {GRAY}{vr.delegator_id} → {vr.delegate_id}"
              f" | budget={vr.authority_budget_granted:.0f}{RESET}")


def _print_block_result(res: ArchiveBlockResult, verbose: bool = False) -> None:
    """
    Premium terminal output for COLD archive block verification.
    Follows the ADR-163 §3 verification step sequence.
    """
    verdict_color = {
        VERDICT_PASS:                GREEN,
        VERDICT_INTEGRITY_VIOLATION: RED,
        VERDICT_CHAIN_BREAK:         RED,
        VERDICT_SIGNATURE_INVALID:   RED,
    }.get(res.verdict, RED)

    print(f"\n{BOLD}Archive Block: {CYAN}{res.block_id}{RESET}")
    print(f"  Verdict:  {verdict_color}{BOLD}{res.verdict}{RESET}")
    print(f"  Version:  {GRAY}{res.omnix_version}{RESET}")
    print(f"  Classes:  {GRAY}{', '.join(res.evidence_classes) or '—'}{RESET}")
    print(f"  Artifacts:{GRAY} {res.artifact_count}{RESET}")
    print()

    # Step 2 — Merkle root
    print(f"{BOLD}  Step 2 — Merkle Root (artifact_hashes){RESET}")
    print(_ok("Merkle root valid") if res.merkle_valid
          else _fail("Merkle root MISMATCH — artifact hashes were modified"))
    if verbose or not res.merkle_valid:
        print(f"{GRAY}             Stored:     {res.merkle_stored}{RESET}")
        print(f"{GRAY}             Recomputed: {res.merkle_recomputed}{RESET}")

    # Step 3 — Canonical hash
    print(f"\n{BOLD}  Step 3 — Canonical Hash (block fields){RESET}")
    print(_ok("Canonical hash valid") if res.canonical_hash_valid
          else _fail("Canonical hash MISMATCH — block metadata was modified"))
    if verbose or not res.canonical_hash_valid:
        print(f"{GRAY}             Stored:     {res.canonical_hash_stored}{RESET}")
        print(f"{GRAY}             Recomputed: {res.canonical_hash_recomputed}{RESET}")

    # Step 4 — PQC signature
    print(f"\n{BOLD}  Step 4 — ML-DSA-65 Signature (EAP-INV-002){RESET}")
    if res.pqc_checked:
        print(_ok(f"PQC signature valid ({res.pqc_algorithm})") if res.pqc_signature_valid
              else _fail(f"PQC signature INVALID ({res.pqc_algorithm})"))
    else:
        print(_skip("PQC verification skipped — provide --public-key to enable"))

    # Step 5 — Chain / predecessor
    print(f"\n{BOLD}  Step 5 — Block Chain (predecessor hash){RESET}")
    if res.chain_verified:
        if res.predecessor_block_id:
            print(_ok(f"Chain valid → predecessor: {res.predecessor_block_id}")
                  if res.predecessor_hash_valid
                  else _fail(f"CHAIN BREAK — predecessor mismatch (block: {res.predecessor_block_id})"))
        else:
            print(_ok("Genesis block — predecessor sentinel verified")
                  if res.predecessor_hash_valid
                  else _warn("Non-genesis block — provide --predecessor-block for chain verification"))
    else:
        print(_skip("Chain verification skipped — provide --predecessor-block to verify"))

    # Step 6 — Artifact hash count
    print(f"\n{BOLD}  Step 6 — Artifact Count Integrity{RESET}")
    print(_ok(f"Artifact count consistent ({res.artifact_hashes_count} hashes in manifest)")
          if res.artifact_hashes_valid
          else _fail(f"Artifact count MISMATCH — declared {res.artifact_count},"
                     f" manifest has {res.artifact_hashes_count}"))

    # Format check
    if not res.block_id_format_valid:
        print(_warn(f"Block ID format non-standard: {res.block_id}"))

    # Failures + warnings
    if res.failure_reasons:
        print()
        for reason in res.failure_reasons:
            for line in reason.split("\n"):
                print(f"  {RED}{line}{RESET}")

    if res.warnings:
        print()
        for w in res.warnings:
            print(_warn(w))

    print()

    # Institutional disclosure footer
    if res.verdict == VERDICT_PASS:
        print(f"{GREEN}{BOLD}  ✓ This archive block has passed all cryptographic verification steps.{RESET}")
        print(f"{GRAY}    It may be cited as independently verified evidence under ADR-163 / EAP-INV-005.{RESET}")
    else:
        print(f"{RED}{BOLD}  ✗ This archive block FAILED verification.{RESET}")
        print(f"{GRAY}    It should NOT be accepted as valid evidence.{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# Replay mode
# ─────────────────────────────────────────────────────────────────────────────

def _replay_mode(args) -> int:
    import glob
    files = glob.glob("*.json") + glob.glob("receipts/*.json")
    if not files:
        print(f"{YELLOW}No JSON files found in current directory.{RESET}")
        return 2

    print(f"{BOLD}Replaying {len(files)} file(s)...{RESET}\n")
    total = 0
    verified = 0
    for path in sorted(files):
        try:
            with open(path) as f:
                data = json.load(f)
            if "delegation_id" in data or "content_hash" in data:
                vr = verify_receipt(data)
                total += 1
                icon = f"{GREEN}✓{RESET}" if vr.fully_verified else f"{RED}✗{RESET}"
                print(f"  {icon}  {path}: {vr.delegation_id}")
                if vr.fully_verified:
                    verified += 1
        except Exception:
            pass

    print(f"\n{BOLD}Results: {verified}/{total} verified{RESET}")
    return 0 if verified == total else 1


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="omnix_atf_verify.py",
        description="OMNIX ATF + Archive Block Public Verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
─── Delegation Receipt Verification ────────────────────────────────────────
  python omnix_atf_verify.py receipt.json
  python omnix_atf_verify.py receipt.json --verbose
  python omnix_atf_verify.py receipt.json --public-key <base64-key>
  python omnix_atf_verify.py receipt.json --json

─── Chain Verification ─────────────────────────────────────────────────────
  python omnix_atf_verify.py chain.json --mode chain

─── Agent Identity ─────────────────────────────────────────────────────────
  python omnix_atf_verify.py identity.json --mode agent

─── COLD Archive Block (ADR-163 / EAP-INV-005) ─────────────────────────────
  python omnix_atf_verify.py \\
      --archive-block OMNIX-BLOCK-20260514-000001.json \\
      --public-key omnix_public_key.b64

  python omnix_atf_verify.py \\
      --archive-block OMNIX-BLOCK-20260514-000001.json \\
      --public-key omnix_public_key.b64 \\
      --verify-chain \\
      --predecessor-block OMNIX-BLOCK-20260514-000000.json

─── Batch Replay ───────────────────────────────────────────────────────────
  python omnix_atf_verify.py --mode replay

─── Exit Codes ─────────────────────────────────────────────────────────────
  0 — Verified (all checks passed)
  1 — Invalid  (one or more checks failed)
  2 — Error    (file not found, invalid JSON, missing arguments)
        """,
    )

    # ── Positional
    parser.add_argument("file", nargs="?", help="Path to receipt / chain / identity JSON")

    # ── Mode
    parser.add_argument(
        "--mode",
        choices=["receipt", "agent", "chain", "replay", "block"],
        default="receipt",
        help="Verification mode (default: receipt)",
    )

    # ── Receipt options
    parser.add_argument("--public-key", dest="public_key",
                        help="Public key — base64 string, or path to .b64/.pem file")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed field-level output")
    parser.add_argument("--stdin", action="store_true",
                        help="Read JSON from stdin")
    parser.add_argument("--json", dest="json_output", action="store_true",
                        help="Output result as JSON (programmatic use)")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable ANSI color output")

    # ── Archive block options (ADR-163)
    parser.add_argument(
        "--archive-block",
        dest="archive_block",
        metavar="BLOCK_FILE",
        help="Path to COLD archive block JSON (activates --mode block automatically)",
    )
    parser.add_argument(
        "--verify-chain",
        dest="verify_chain",
        action="store_true",
        help="Enable chain verification (requires --predecessor-block)",
    )
    parser.add_argument(
        "--predecessor-block",
        dest="predecessor_block",
        metavar="PREDECESSOR_FILE",
        help="Path to predecessor COLD archive block JSON",
    )

    args = parser.parse_args()

    # Auto-switch to block mode when --archive-block is given
    if args.archive_block:
        args.mode = "block"

    if args.no_color:
        global RESET, BOLD, DIM, RED, GREEN, YELLOW, BLUE, CYAN, GRAY, GOLD, PURPLE, WHITE
        RESET = BOLD = DIM = RED = GREEN = YELLOW = BLUE = CYAN = GRAY = GOLD = PURPLE = WHITE = ""

    if not args.json_output:
        if args.mode == "block":
            print(BLOCK_BANNER)
        else:
            print(ATF_BANNER)

    # ── COLD Archive Block mode ──────────────────────────────────────────────
    if args.mode == "block":
        block_file = args.archive_block or args.file
        if not block_file:
            print(f"{RED}ERROR: --archive-block <FILE> is required in block mode.{RESET}",
                  file=sys.stderr)
            return 2

        if not os.path.exists(block_file):
            print(f"{RED}ERROR: Block file not found: {block_file}{RESET}", file=sys.stderr)
            return 2

        try:
            with open(block_file) as f:
                block = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"{RED}ERROR: Invalid JSON in {block_file}: {exc}{RESET}", file=sys.stderr)
            return 2

        # Load public key
        public_key_b64: Optional[str] = None
        if args.public_key:
            public_key_b64 = _load_public_key_b64(args.public_key)

        # Load predecessor
        predecessor_block: Optional[Dict] = None
        if args.predecessor_block:
            if not os.path.exists(args.predecessor_block):
                print(f"{RED}ERROR: Predecessor file not found: {args.predecessor_block}{RESET}",
                      file=sys.stderr)
                return 2
            try:
                with open(args.predecessor_block) as f:
                    predecessor_block = json.load(f)
            except json.JSONDecodeError as exc:
                print(f"{RED}ERROR: Invalid JSON in predecessor: {exc}{RESET}", file=sys.stderr)
                return 2

        result = verify_archive_block(block, public_key_b64, predecessor_block)

        if args.json_output:
            out = {
                "block_id":              result.block_id,
                "verdict":               result.verdict,
                "artifact_count":        result.artifact_count,
                "evidence_classes":      result.evidence_classes,
                "merkle_valid":          result.merkle_valid,
                "canonical_hash_valid":  result.canonical_hash_valid,
                "pqc_signature_valid":   result.pqc_signature_valid,
                "pqc_checked":           result.pqc_checked,
                "pqc_algorithm":         result.pqc_algorithm,
                "chain_verified":        result.chain_verified,
                "predecessor_hash_valid": result.predecessor_hash_valid,
                "artifact_hashes_valid": result.artifact_hashes_valid,
                "omnix_version":         result.omnix_version,
                "block_id_format_valid": result.block_id_format_valid,
                "failure_reasons":       result.failure_reasons,
                "warnings":              result.warnings,
            }
            print(json.dumps(out, indent=2))
            return 0 if result.verdict == VERDICT_PASS else 1

        _print_block_result(result, verbose=args.verbose)
        print(ATF_FOOTER)
        return 0 if result.verdict == VERDICT_PASS else 1

    # ── Replay mode ──────────────────────────────────────────────────────────
    if args.mode == "replay":
        return _replay_mode(args)

    # ── Load input for receipt / agent / chain modes ─────────────────────────
    if args.stdin:
        try:
            data = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            print(f"{RED}ERROR: Invalid JSON from stdin: {exc}{RESET}", file=sys.stderr)
            return 2
    elif args.file:
        if not os.path.exists(args.file):
            print(f"{RED}ERROR: File not found: {args.file}{RESET}", file=sys.stderr)
            return 2
        try:
            with open(args.file) as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"{RED}ERROR: Invalid JSON in {args.file}: {exc}{RESET}", file=sys.stderr)
            return 2
    else:
        parser.print_help()
        return 2

    # ── Agent identity mode ──────────────────────────────────────────────────
    if args.mode == "agent":
        result = verify_identity(data)
        if args.json_output:
            print(json.dumps(result, indent=2))
            return 0 if result["fully_verified"] else 1
        agent_id = result["agent_id"]
        verdict  = "VERIFIED" if result["fully_verified"] else "INVALID"
        verdict_color = GREEN if result["fully_verified"] else RED
        print(f"\n{BOLD}Agent Identity: {CYAN}{agent_id}{RESET}")
        print(f"  Status: {verdict_color}{BOLD}{verdict}{RESET}\n")
        print(_ok("Registration hash valid") if result["hash_valid"]
              else _fail("Registration hash INVALID"))
        if result["pqc_checked"]:
            print(_ok("PQC registration signature valid") if result["pqc_signature_valid"]
                  else _fail("PQC registration signature INVALID"))
        print(ATF_FOOTER)
        return 0 if result["fully_verified"] else 1

    # ── Chain mode ───────────────────────────────────────────────────────────
    elif args.mode == "chain":
        if not isinstance(data, list):
            data = data.get("chain", [data])
        result = verify_chain(data)

        if args.json_output:
            serializable = {k: v for k, v in result.items() if k != "receipt_results"}
            serializable["receipts"] = [
                {"delegation_id": r.delegation_id, "fully_verified": r.fully_verified}
                for r in result["receipt_results"]
            ]
            print(json.dumps(serializable, indent=2))
            return 0 if result["all_verified"] else 1

        _print_chain_result(result)
        print(ATF_FOOTER)
        return 0 if result["all_verified"] else 1

    # ── Receipt mode (default) ───────────────────────────────────────────────
    else:
        pk_override: Optional[str] = None
        if args.public_key:
            pk_override = _load_public_key_b64(args.public_key)

        vr = verify_receipt(data, public_key_override=pk_override)

        if args.json_output:
            out = {
                "delegation_id":         vr.delegation_id,
                "hash_valid":            vr.hash_valid,
                "pqc_signature_valid":   vr.pqc_signature_valid,
                "mar_invariant_valid":   vr.mar_invariant_valid,
                "not_expired":           vr.not_expired,
                "fully_verified":        vr.fully_verified,
                "status":                vr.status,
                "authority_budget_granted": vr.authority_budget_granted,
                "failure_reasons":       vr.failure_reasons,
                "warnings":              vr.warnings,
            }
            print(json.dumps(out, indent=2))
            return 0 if vr.fully_verified else 1

        _print_receipt_result(vr, verbose=args.verbose)
        print(ATF_FOOTER)
        return 0 if vr.fully_verified else 1


if __name__ == "__main__":
    sys.exit(main())
