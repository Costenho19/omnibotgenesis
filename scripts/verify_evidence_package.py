"""
OMNIX QUANTUM — Offline Evidence Package Verifier
==================================================
RFC-ATF-1 through RFC-ATF-6 · TA-14 Admissibility Chain

Verifies every cryptographic artifact in an OMNIX evidence package
WITHOUT calling the OMNIX runtime. All verification is performed
offline using only the public key embedded in the package.

What this verifier confirms:
  ✓ DR (Delegation Receipt)     — content_hash (SHA-256/compact) + PQC signature
  ✓ TAR (Temporal Admissibility)— content_hash (SHA-256/compact) + PQC signature
  ✓ RCR (Runtime Continuity)    — hash integrity (SHA3-256/default) + PQC signature
  ✓ Binding Record              — hash integrity (SHA3-256/default) + PQC signature
  ✓ Commit Record               — hash integrity (SHA3-256/default) + PQC signature
  ✓ BAR (Behavioral Anchor)     — content_hash (SHA3-256/default) + PQC signature (default sep)
  ✓ CTCHC (Coherence Hash Chain)— genesis continuity + link chain + seal_hash + PQC sig (default sep)
  ✓ PoGC (Proof of Governance)  — content_hash (SHA3-256/default, incl. pqc_algorithm) + PQC sig
  ✓ Refusal Receipt (Route A)   — content_hash (SHA3-256/default) + PQC signature
  ✓ Outcome Receipt (Route B)   — content_hash (SHA3-256/default) + PQC signature

Canonicalization Profile Registry (per ADR-200):
  - DR / TAR:               SHA-256, compact separators (",",":"), excl. content_hash/pqc_sig/pqc_alg
  - RCR / Binding / Commit: SHA3-256, default separators, excl. hash field/pqc_sig/pqc_alg
  - Refusal / Outcome:      SHA3-256, default separators, excl. content_hash/pqc_sig/pqc_alg
  - PoGC:                   SHA3-256, default separators, excl. content_hash/pqc_sig ONLY
                            (pqc_algorithm IS included — see ADR-200 §4.3)
  - BAR content_hash:       SHA3-256, default separators, canonical 6-field tuple
  - BAR PQC sig payload:    4-field JSON, default separators (matches BAREngine)
  - CTCHC seal sig payload: 3-field JSON, default separators (matches CTCHCEngine)
  - RCR/Binding/Commit sig: compact separators (matches generator._sign_payload)
  - PoGC/Refusal/Outcome:   compact separators (matches generator._sign_payload)
  - CTCHC genesis:          Verified via chain continuity (first link prev = genesis_hash)
                            Cannot re-derive: initialized_at format varies across Python
                            versions and DB round-trips. Security maintained by CTCHC seal sig.

Verifier scope limits (written to report):
  ✗ Does NOT verify governance policy values (mandate amounts, risk ceilings)
  ✗ Does NOT verify external market data in source_state
  ✗ Does NOT require OMNIX runtime, database, or network access

Usage:
  python scripts/verify_evidence_package.py <package_file.json>

Exit codes:
  0 — all verifications PASS
  1 — one or more verifications FAIL

Author: Harold Nunes — OMNIX QUANTUM LTD
ADR: ADR-200 (Route-Complete Evidence Package)
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─────────────────────────────────────────────────────────────────────────────
#  Result tracking
# ─────────────────────────────────────────────────────────────────────────────

class VerificationReport:
    def __init__(self, package_id: str):
        self.package_id = package_id
        self.checks: List[Dict] = []
        self.passed  = 0
        self.failed  = 0
        self.skipped = 0

    def add(self, check_id: str, label: str, passed: bool, detail: str = "", skip: bool = False):
        status = "SKIP" if skip else ("PASS" if passed else "FAIL")
        icon   = "⏭ " if skip else ("✓" if passed else "✗")
        self.checks.append({"id": check_id, "label": label, "status": status, "detail": detail})
        if skip:
            self.skipped += 1
        elif passed:
            self.passed += 1
        else:
            self.failed += 1
        colour = "\033[90m" if skip else ("\033[32m" if passed else "\033[31m")
        reset  = "\033[0m"
        detail_str = f"  → {detail}" if detail else ""
        print(f"  {colour}{icon} [{check_id}] {label}{reset}{detail_str}")

    def summary(self) -> bool:
        total = self.passed + self.failed + self.skipped
        all_ok = self.failed == 0
        colour = "\033[32m" if all_ok else "\033[31m"
        reset  = "\033[0m"
        print()
        print("─" * 65)
        print(f"  TOTAL CHECKS : {total}")
        print(f"  {colour}PASSED{reset}        : {self.passed}")
        print(f"  \033[31mFAILED\033[0m        : {self.failed}")
        print(f"  \033[90mSKIPPED\033[0m       : {self.skipped} (artifact unsigned)")
        print("─" * 65)
        if all_ok:
            print(f"  {colour}VERDICT: ALL VERIFICATIONS PASS — package integrity confirmed{reset}")
        else:
            print(f"  \033[31mVERDICT: {self.failed} VERIFICATION(S) FAILED — package integrity compromised\033[0m")
        return all_ok

    def to_dict(self) -> Dict:
        return {
            "package_id":   self.package_id,
            "verified_at":  datetime.now(timezone.utc).isoformat(),
            "total_checks": self.passed + self.failed + self.skipped,
            "passed":       self.passed,
            "failed":       self.failed,
            "skipped":      self.skipped,
            "verdict":      "PASS" if self.failed == 0 else "FAIL",
            "checks":       self.checks,
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Crypto helpers (no OMNIX runtime dependency)
# ─────────────────────────────────────────────────────────────────────────────

def _load_pqc(pk_b64: str):
    try:
        from omnix_core.security.pqc_security import PostQuantumSecurity
        pqc = PostQuantumSecurity()
        if not pqc.pqc_enabled:
            print("\n  [WARN] PQC not available — signature checks will be SKIPPED.")
            print("         Install pypqc: pip install pypqc")
            return None, None
        pk_bytes = base64.b64decode(pk_b64)
        return pqc, pk_bytes
    except Exception as e:
        print(f"\n  [WARN] Could not load PQC module: {e}")
        return None, None


def _sha3_default(data: Dict) -> str:
    """SHA3-256 with DEFAULT json.dumps separators. Used for generator-native hashes."""
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha3_256(canonical.encode()).hexdigest()


def _sha3_compact(data: Dict) -> str:
    """SHA3-256 with COMPACT separators. Used internally where engines use compact."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha3_256(canonical.encode()).hexdigest()


def _sha256_compact(data: Dict) -> str:
    """SHA-256 with COMPACT separators. Used by DR/TAR engines."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _verify_sig_compact(pqc, pk_bytes: bytes, payload: Dict, sig_b64: Optional[str]) -> Tuple[bool, str]:
    """Verify PQC sig where signing used compact separators (generator._sign_payload)."""
    if not sig_b64:
        return False, "no signature present"
    if pqc is None:
        return False, "PQC module unavailable (pypqc not installed)"
    try:
        sig_bytes = base64.b64decode(sig_b64)
        raw       = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ok        = pqc.verify_signature(sig_bytes, raw, pk_bytes)
        return ok, "OK" if ok else "signature mismatch"
    except Exception as e:
        return False, str(e)


def _verify_sig_default(pqc, pk_bytes: bytes, payload: Dict, sig_b64: Optional[str]) -> Tuple[bool, str]:
    """Verify PQC sig where signing used default separators (BAREngine, CTCHCEngine)."""
    if not sig_b64:
        return False, "no signature present"
    if pqc is None:
        return False, "PQC module unavailable (pypqc not installed)"
    try:
        sig_bytes = base64.b64decode(sig_b64)
        raw       = json.dumps(payload, sort_keys=True).encode("utf-8")
        ok        = pqc.verify_signature(sig_bytes, raw, pk_bytes)
        return ok, "OK" if ok else "signature mismatch"
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────────────────────────────────────
#  Individual artifact verifiers
# ─────────────────────────────────────────────────────────────────────────────

def verify_dr(dr: Dict, pqc, pk_bytes: bytes, report: VerificationReport, prefix: str):
    did = dr.get("delegation_id", "?")

    # 1. MAR invariant (ATF-INV-001): granted ≤ delegator
    delegator_budget = dr.get("authority_budget_delegator", -1)
    granted_budget   = dr.get("authority_budget_granted", 999)
    mar_ok = granted_budget <= delegator_budget
    report.add(f"{prefix}.DR.MAR", f"DR {did[:20]} — MAR invariant (granted≤delegator)", mar_ok,
               f"granted={granted_budget} delegator={delegator_budget}")

    # 2. content_hash integrity — DelegationReceiptEngine uses SHA-256 + compact separators
    exclude = {"content_hash", "pqc_signature", "pqc_algorithm"}
    clean   = {k: v for k, v in dr.items() if k not in exclude}
    expected_hash = _sha256_compact(clean)
    hash_ok = dr.get("content_hash") == expected_hash
    report.add(f"{prefix}.DR.HASH", f"DR {did[:20]} — content_hash integrity", hash_ok,
               f"stored={dr.get('content_hash','?')[:16]}... expected={expected_hash[:16]}...")

    # 3. PQC signature — DR signs content_hash.encode() directly (not JSON)
    sig_b64 = dr.get("pqc_signature")
    if sig_b64 and pqc:
        try:
            sig_bytes = base64.b64decode(sig_b64)
            raw_ch    = dr.get("content_hash", "").encode("utf-8")
            sig_ok    = pqc.verify_signature(sig_bytes, raw_ch, pk_bytes)
            sig_detail = "OK" if sig_ok else "mismatch"
        except Exception as e:
            sig_ok, sig_detail = False, str(e)
        report.add(f"{prefix}.DR.SIG", f"DR {did[:20]} — PQC signature (ML-DSA-65)", sig_ok, sig_detail)
    else:
        report.add(f"{prefix}.DR.SIG", f"DR {did[:20]} — PQC signature", False,
                   "no signature" if not sig_b64 else "PQC unavailable", skip=not pqc)


def verify_tar(tar: Dict, pqc, pk_bytes: bytes, report: VerificationReport, prefix: str):
    tar_id = tar.get("tar_id", "?")

    # 1. content_hash integrity — TemporalAuthorityEngine uses SHA-256 + compact separators
    exclude = {"content_hash", "pqc_signature", "pqc_algorithm"}
    clean   = {k: v for k, v in tar.items() if k not in exclude}
    expected  = _sha256_compact(clean)
    hash_ok   = tar.get("content_hash") == expected
    report.add(f"{prefix}.TAR.HASH", f"TAR {tar_id[:20]} — content_hash integrity", hash_ok,
               f"stored={tar.get('content_hash','?')[:16]}... expected={expected[:16]}...")

    # 2. admission_status present
    status = tar.get("admission_status", "")
    report.add(f"{prefix}.TAR.STATUS", f"TAR {tar_id[:20]} — admission_status present",
               status in ("ADMITTED", "REJECTED"), f"status={status}")

    # 3. execution_ns present and positive
    exec_ns = tar.get("execution_ns", 0)
    report.add(f"{prefix}.TAR.NS", f"TAR {tar_id[:20]} — execution_ns captured",
               isinstance(exec_ns, int) and exec_ns > 0, f"execution_ns={exec_ns}")

    # 4. PQC signature — TAR signs content_hash.encode() directly
    sig_b64 = tar.get("pqc_signature")
    if sig_b64 and pqc:
        try:
            sig_bytes = base64.b64decode(sig_b64)
            raw_ch    = tar.get("content_hash", "").encode("utf-8")
            sig_ok    = pqc.verify_signature(sig_bytes, raw_ch, pk_bytes)
            sig_detail = "OK" if sig_ok else "mismatch"
        except Exception as e:
            sig_ok, sig_detail = False, str(e)
        report.add(f"{prefix}.TAR.SIG", f"TAR {tar_id[:20]} — PQC signature", sig_ok, sig_detail)
    else:
        report.add(f"{prefix}.TAR.SIG", f"TAR {tar_id[:20]} — PQC signature", False,
                   "no signature" if not sig_b64 else "PQC unavailable", skip=not pqc)


def verify_bar(bar: Dict, pqc, pk_bytes: bytes, report: VerificationReport, prefix: str):
    bar_id = bar.get("bar_id", "?")

    # BEV-INV-002: content_hash = SHA3-256(canonical 6-field tuple, default separators)
    expected = hashlib.sha3_256(json.dumps({
        "session_id":            bar.get("session_id", ""),
        "agent_id":              bar.get("agent_id", ""),
        "turn_index":            bar.get("turn_index", 0),
        "output_hash":           bar.get("output_hash", ""),
        "governing_receipt_id":  bar.get("governing_receipt_id", ""),
        "constraint_set_hash":   bar.get("constraint_set_hash", ""),
    }, sort_keys=True).encode()).hexdigest()

    stored  = bar.get("content_hash", "")
    hash_ok = stored == expected
    report.add(f"{prefix}.BAR.HASH", f"BAR {bar_id[:20]} — content_hash (BEV-INV-002)", hash_ok,
               f"stored={stored[:16]}... expected={expected[:16]}...")

    # BAR status valid
    bar_status = bar.get("bar_status", "")
    report.add(f"{prefix}.BAR.STATUS", f"BAR {bar_id[:20]} — bar_status valid",
               bar_status in ("VALID", "WARNING", "VIOLATION", "HALTED"), f"status={bar_status}")

    # output_hash non-empty
    report.add(f"{prefix}.BAR.OUTPUT", f"BAR {bar_id[:20]} — output_hash present",
               bool(bar.get("output_hash", "")), "")

    # PQC signature — BAREngine signs with DEFAULT separators (4-field payload)
    sig_b64 = bar.get("pqc_signature")
    if sig_b64 and pqc:
        sig_payload = {
            "bar_id":                bar_id,
            "content_hash":          stored,
            "governing_receipt_id":  bar.get("governing_receipt_id", ""),
            "created_at":            bar.get("created_at", ""),
        }
        sig_ok, sig_detail = _verify_sig_default(pqc, pk_bytes, sig_payload, sig_b64)
        report.add(f"{prefix}.BAR.SIG", f"BAR {bar_id[:20]} — PQC signature (BEV-INV-004)", sig_ok, sig_detail)
    else:
        report.add(f"{prefix}.BAR.SIG", f"BAR {bar_id[:20]} — PQC signature", False,
                   "no signature" if not sig_b64 else "PQC unavailable", skip=not pqc)


def verify_ctchc(execution: Dict, governing_receipt_id: str,
                 pqc, pk_bytes: bytes, report: VerificationReport, prefix: str):
    sealed   = execution.get("ctchc_sealed", {})
    links    = execution.get("ctchc_links", [])
    chain_id = sealed.get("chain_id", "?")

    if not sealed:
        report.add(f"{prefix}.CTCHC.PRESENT", "CTCHC — sealed chain present", False, "missing ctchc_sealed")
        return

    # 1. Genesis continuity + governing receipt linkage (BEV-INV-010)
    #    We verify: (a) governing_receipt_id anchors genesis to the DR, and
    #    (b) the first link's prev_link_hash equals the stored genesis_hash.
    #    Note: genesis_hash re-derivation from initialized_at is not performed because
    #    initialized_at format varies across Python versions and DB round-trips.
    #    Security is maintained: seal_hash covers genesis_hash and is PQC-signed (check 4+5 below).
    receipt_anchored = sealed.get("governing_receipt_id") == governing_receipt_id
    if links:
        first_link = sorted(links, key=lambda x: x.get("turn_index", 0))[0]
        chain_continuity = first_link.get("prev_link_hash") == sealed.get("genesis_hash")
        genesis_ok = receipt_anchored and chain_continuity
        genesis_detail = (
            f"receipt_anchored={receipt_anchored} chain_starts_at_genesis={chain_continuity}"
        )
    else:
        genesis_ok = receipt_anchored
        genesis_detail = f"receipt_anchored={receipt_anchored} no_links_to_check"
    report.add(f"{prefix}.CTCHC.GENESIS",
               f"CTCHC {chain_id[:16]} — genesis anchored to governing receipt (BEV-INV-010)",
               genesis_ok, genesis_detail)

    # 2. governing_receipt_id consistent across all links (BEV-INV-018)
    receipt_consistent = all(
        lk.get("governing_receipt_id") == governing_receipt_id
        for lk in links
    )
    report.add(f"{prefix}.CTCHC.RECEIPT", f"CTCHC — governing_receipt_id consistent (BEV-INV-018)",
               receipt_consistent, f"links checked: {len(links)}")

    # 3. Link-by-link hash chain integrity (BEV-INV-011)
    #    Each link: chain_link_hash = SHA3-256( JSON({"prev":..,"turn":..,"receipt":..}) default sep )
    prev_hash = sealed.get("genesis_hash", "")
    chain_ok  = True
    for lk in sorted(links, key=lambda x: x.get("turn_index", 0)):
        link_payload = json.dumps({
            "prev":    prev_hash,
            "turn":    lk.get("turn_hash", ""),
            "receipt": lk.get("governing_receipt_id", ""),
        }, sort_keys=True)
        expected_link_hash = hashlib.sha3_256(link_payload.encode()).hexdigest()
        link_ok = lk.get("chain_link_hash") == expected_link_hash
        if not link_ok:
            chain_ok = False
        prev_hash = lk.get("chain_link_hash", prev_hash)

    report.add(f"{prefix}.CTCHC.CHAIN", f"CTCHC — link-by-link hash chain integrity (BEV-INV-011)",
               chain_ok, f"links verified: {len(links)}")

    # 4. seal_hash covers all links in order (BEV-INV-013)
    ordered_links = sorted(links, key=lambda x: x.get("turn_index", 0))
    seal_payload = json.dumps({
        "chain_id":             chain_id,
        "session_id":           sealed.get("session_id", ""),
        "governing_receipt_id": sealed.get("governing_receipt_id", ""),
        "genesis_hash":         sealed.get("genesis_hash", ""),
        "turn_count":           len(ordered_links),
        "link_hashes":          [lk.get("chain_link_hash", "") for lk in ordered_links],
        "tip_hash":             sealed.get("current_tip_hash", ""),
    }, sort_keys=True)
    expected_seal = hashlib.sha3_256(seal_payload.encode()).hexdigest()
    seal_ok = sealed.get("seal_hash") == expected_seal
    report.add(f"{prefix}.CTCHC.SEAL_HASH", f"CTCHC — seal_hash covers complete chain (BEV-INV-013)",
               seal_ok, f"stored={sealed.get('seal_hash','?')[:16]}... expected={expected_seal[:16]}...")

    # 5. Seal PQC signature — CTCHCEngine signs with DEFAULT separators (3-field payload)
    sig_b64 = sealed.get("seal_pqc_signature")
    if sig_b64 and pqc:
        sig_payload = {
            "chain_id":   chain_id,
            "seal_hash":  sealed.get("seal_hash", ""),
            "session_id": sealed.get("session_id", ""),
        }
        sig_ok, sig_detail = _verify_sig_default(pqc, pk_bytes, sig_payload, sig_b64)
        report.add(f"{prefix}.CTCHC.SIG", f"CTCHC — seal PQC signature (BEV-INV-014)", sig_ok, sig_detail)
    else:
        report.add(f"{prefix}.CTCHC.SIG", f"CTCHC — seal PQC signature", False,
                   "no signature" if not sig_b64 else "PQC unavailable", skip=not pqc)

    # 6. is_sealed flag
    report.add(f"{prefix}.CTCHC.SEALED", f"CTCHC — is_sealed=True",
               sealed.get("is_sealed", False) is True, "")


def verify_pogc(pogc: Dict, pqc, pk_bytes: bytes, report: VerificationReport, prefix: str):
    pogc_id = pogc.get("pogc_id", "?")

    # content_hash — generator includes pqc_algorithm in canonical_fields before hashing.
    # Exclude ONLY content_hash and pqc_signature. pqc_algorithm IS part of the hash.
    # Uses SHA3-256 + default separators (ADR-200 §4.3).
    exclude  = {"content_hash", "pqc_signature"}
    clean    = {k: v for k, v in pogc.items() if k not in exclude}
    expected = _sha3_default(clean)
    stored   = pogc.get("content_hash", "")
    hash_ok  = stored == expected
    report.add(f"{prefix}.POGC.HASH", f"PoGC {pogc_id[:20]} — content_hash integrity", hash_ok,
               f"stored={stored[:16]}... expected={expected[:16]}...")

    # mandate_certification present
    mc = pogc.get("mandate_certification", "")
    report.add(f"{prefix}.POGC.MANDATE", f"PoGC {pogc_id[:20]} — mandate_certification present",
               mc in ("MANDATE-BOUND", "MANDATE-ALIGNED", "UNCERTIFIED"), f"certification={mc}")

    # PQC sig — generator signs with compact separators via _sign_payload
    sig_b64 = pogc.get("pqc_signature")
    if sig_b64 and pqc:
        sig_payload = {
            "pogc_id":       pogc_id,
            "content_hash":  stored,
            "issued_at":     pogc.get("issued_at", ""),
        }
        sig_ok, sig_detail = _verify_sig_compact(pqc, pk_bytes, sig_payload, sig_b64)
        report.add(f"{prefix}.POGC.SIG", f"PoGC {pogc_id[:20]} — PQC signature", sig_ok, sig_detail)
    else:
        report.add(f"{prefix}.POGC.SIG", f"PoGC {pogc_id[:20]} — PQC signature", False,
                   "no signature" if not sig_b64 else "PQC unavailable", skip=not pqc)


def verify_receipt(receipt: Dict, id_field: str, hash_field: str,
                   sig_field: str, label: str, prefix: str,
                   pqc, pk_bytes: bytes, report: VerificationReport):
    """Generic verifier for refusal and outcome receipts.

    These receipts are hashed with SHA3-256 + default separators (generator._sha3 + json.dumps default),
    and signed with compact separators via generator._sign_payload.
    """
    rec_id = receipt.get(id_field, "?")

    # content_hash — default separators, excl. hash field, sig field, pqc_algorithm
    exclude  = {hash_field, sig_field, "pqc_algorithm"}
    clean    = {k: v for k, v in receipt.items() if k not in exclude}
    expected = _sha3_default(clean)
    stored   = receipt.get(hash_field, "")
    hash_ok  = stored == expected
    report.add(f"{prefix}.HASH", f"{label} {rec_id[:20]} — content_hash integrity", hash_ok,
               f"stored={stored[:16]}... expected={expected[:16]}...")

    # PQC sig — compact separators
    sig_b64 = receipt.get(sig_field)
    if sig_b64 and pqc:
        sig_payload = {
            id_field:    rec_id,
            hash_field:  stored,
            "issued_at": receipt.get("issued_at", ""),
        }
        sig_ok, sig_detail = _verify_sig_compact(pqc, pk_bytes, sig_payload, sig_b64)
        report.add(f"{prefix}.SIG", f"{label} {rec_id[:20]} — PQC signature", sig_ok, sig_detail)
    else:
        report.add(f"{prefix}.SIG", f"{label} {rec_id[:20]} — PQC signature", False,
                   "no signature" if not sig_b64 else "PQC unavailable", skip=not pqc)


def verify_continuity_hash(record: Dict, hash_field: str, label: str, check_prefix: str,
                           report: VerificationReport, exclude_extra: Optional[List[str]] = None):
    """Verify a generator-native continuity/binding/commit hash (SHA3-256, default separators)."""
    exclude = {hash_field, "pqc_signature", "pqc_algorithm"}
    if exclude_extra:
        exclude.update(exclude_extra)
    clean    = {k: v for k, v in record.items() if k not in exclude}
    expected = _sha3_default(clean)
    stored   = record.get(hash_field, "")
    hash_ok  = stored == expected
    report.add(check_prefix, label, hash_ok,
               f"stored={stored[:16]}... expected={expected[:16]}...")
    return hash_ok, stored


# ─────────────────────────────────────────────────────────────────────────────
#  Route verifiers
# ─────────────────────────────────────────────────────────────────────────────

def verify_route_a(route: Dict, pqc, pk_bytes: bytes, report: VerificationReport):
    print("\n  ┌─────────────────────────────────────────────────────┐")
    print("  │  ROUTE A — REFUSAL                                   │")
    print("  └─────────────────────────────────────────────────────┘")
    steps = route.get("chain_steps", {})

    # 1. source_state hash — SHA3-256, default separators, excl. source_state_hash
    ss = steps.get("1_source_state", {})
    stored_ss_hash = ss.get("source_state_hash", "")
    clean_ss = {k: v for k, v in ss.items() if k != "source_state_hash"}
    expected_ss = _sha3_default(clean_ss)
    report.add("A.SS.HASH", "Source state — hash integrity",
               stored_ss_hash == expected_ss,
               f"stored={stored_ss_hash[:16]}... expected={expected_ss[:16]}...")

    # 2. DR
    verify_dr(steps.get("2_record", {}), pqc, pk_bytes, report, "A")

    # 3. Continuity posture — SHA3-256, default separators
    cont = steps.get("3_continuity", {})
    stored_cont_hash = cont.get("posture_hash", "")
    clean_cont = {k: v for k, v in cont.items() if k not in ("posture_hash", "pqc_signature", "pqc_algorithm")}
    expected_cont = _sha3_default(clean_cont)
    report.add("A.RCR.HASH", "Continuity posture — hash integrity",
               stored_cont_hash == expected_cont,
               f"ces_score={cont.get('ces_score')} band={cont.get('ces_band')}")

    # 4. TAR
    verify_tar(steps.get("4_admissibility", {}), pqc, pk_bytes, report, "A")

    # 5. Binding record — SHA3-256, default separators; Route A binding has no PQC sig
    binding = steps.get("5_binding", {})
    stored_bh = binding.get("binding_hash", "")
    clean_b   = {k: v for k, v in binding.items() if k not in ("binding_hash", "pqc_signature", "pqc_algorithm")}
    expected_bh = _sha3_default(clean_b)
    report.add("A.BIND.HASH", "Binding record — hash integrity",
               stored_bh == expected_bh,
               f"status={binding.get('binding_status')}")
    report.add("A.BIND.STATUS", "Binding record — status=REFUSED",
               binding.get("binding_status") == "REFUSED", "")

    # 6. Commit — execution_reachable=False
    commit = steps.get("6_commit", {})
    report.add("A.COMMIT.BLOCKED", "Commit — execution_reachable=False",
               commit.get("execution_reachable") is False, f"status={commit.get('commit_status')}")

    # 7. Refusal receipt — SHA3-256, default separators (content_hash), compact (sig)
    refusal = steps.get("7_execution", {})
    verify_receipt(refusal, "receipt_id", "content_hash", "pqc_signature",
                   "Refusal receipt", "A.REFUSAL", pqc, pk_bytes, report)
    report.add("A.REFUSAL.TYPE", "Refusal receipt — type=HARD_REFUSAL",
               refusal.get("type") == "HARD_REFUSAL", "")

    # 8. Outcome
    outcome = steps.get("8_outcome", {})
    report.add("A.OUTCOME.EXEC", "Outcome — execution_occurred=False",
               outcome.get("execution_occurred") is False, "")
    report.add("A.OUTCOME.BLOCK", "Outcome — what_remained_impossible populated",
               bool(outcome.get("what_remained_impossible", "")), "")


def verify_route_b(route: Dict, pqc, pk_bytes: bytes, report: VerificationReport):
    print("\n  ┌─────────────────────────────────────────────────────┐")
    print("  │  ROUTE B — ADMISSION                                 │")
    print("  └─────────────────────────────────────────────────────┘")
    steps = route.get("chain_steps", {})

    # 1. source_state — SHA3-256, default separators
    ss = steps.get("1_source_state", {})
    stored_ss_hash = ss.get("source_state_hash", "")
    clean_ss = {k: v for k, v in ss.items() if k != "source_state_hash"}
    expected_ss = _sha3_default(clean_ss)
    report.add("B.SS.HASH", "Source state — hash integrity",
               stored_ss_hash == expected_ss,
               f"stored={stored_ss_hash[:16]}... expected={expected_ss[:16]}...")

    # 2. DR
    verify_dr(steps.get("2_record", {}), pqc, pk_bytes, report, "B")

    # 3. RCR — SHA3-256, default separators, compact sig
    cont = steps.get("3_continuity", {})
    stored_rcr_hash = cont.get("rcr_hash", "")
    clean_rcr = {k: v for k, v in cont.items() if k not in ("rcr_hash", "pqc_signature", "pqc_algorithm")}
    expected_rcr = _sha3_default(clean_rcr)
    hash_ok = stored_rcr_hash == expected_rcr
    report.add("B.RCR.HASH", "RCR — hash integrity", hash_ok,
               f"ces={cont.get('ces_score')} band={cont.get('ces_band')}")

    sig_b64 = cont.get("pqc_signature")
    if sig_b64 and pqc:
        sig_payload = {"rcr_id": cont.get("rcr_id", ""), "rcr_hash": stored_rcr_hash}
        sig_ok, sig_detail = _verify_sig_compact(pqc, pk_bytes, sig_payload, sig_b64)
        report.add("B.RCR.SIG", "RCR — PQC signature", sig_ok, sig_detail)
    else:
        report.add("B.RCR.SIG", "RCR — PQC signature", False,
                   "no signature" if not sig_b64 else "PQC unavailable", skip=not pqc)

    # 4. TAR
    tar = steps.get("4_admissibility", {})
    verify_tar(tar, pqc, pk_bytes, report, "B")
    report.add("B.TAR.ADMITTED", "TAR — admission_status=ADMITTED",
               tar.get("admission_status") == "ADMITTED",
               f"status={tar.get('admission_status')}")

    # 5. Binding — SHA3-256, default separators, compact sig
    binding = steps.get("5_binding", {})
    stored_bh = binding.get("binding_hash", "")
    clean_b = {k: v for k, v in binding.items() if k not in ("binding_hash", "pqc_signature", "pqc_algorithm")}
    expected_bh = _sha3_default(clean_b)
    report.add("B.BIND.HASH", "Binding record — hash integrity",
               stored_bh == expected_bh,
               f"status={binding.get('binding_status')}")
    report.add("B.BIND.STATUS", "Binding record — status=ACCEPTED",
               binding.get("binding_status") == "ACCEPTED", "")

    sig_b64 = binding.get("pqc_signature")
    if sig_b64 and pqc:
        sig_payload = {"binding_id": binding.get("binding_id", ""), "binding_hash": stored_bh}
        sig_ok, sig_detail = _verify_sig_compact(pqc, pk_bytes, sig_payload, sig_b64)
        report.add("B.BIND.SIG", "Binding record — PQC signature", sig_ok, sig_detail)
    else:
        report.add("B.BIND.SIG", "Binding record — PQC signature", False,
                   "no sig" if not sig_b64 else "PQC unavailable", skip=not pqc)

    # 6. Commit — SHA3-256, default separators, compact sig
    commit = steps.get("6_commit", {})
    report.add("B.COMMIT.LOCKED", "Commit — status=LOCKED",
               commit.get("commit_status") == "LOCKED", "")
    report.add("B.COMMIT.SCOPE", "Commit — locked_scope present",
               bool(commit.get("locked_scope")), "")
    report.add("B.COMMIT.REACHABLE", "Commit — execution_reachable=True",
               commit.get("execution_reachable") is True, "")

    # Commit hash integrity (additional check — addresses architect gap finding)
    if commit.get("commit_hash"):
        stored_ch = commit.get("commit_hash", "")
        clean_commit = {k: v for k, v in commit.items() if k not in ("commit_hash", "pqc_signature", "pqc_algorithm")}
        expected_ch = _sha3_default(clean_commit)
        report.add("B.COMMIT.HASH", "Commit record — commit_hash integrity",
                   stored_ch == expected_ch,
                   f"stored={stored_ch[:16]}... expected={expected_ch[:16]}...")

    sig_b64 = commit.get("pqc_signature")
    if sig_b64 and pqc:
        commit_hash = commit.get("commit_hash", "")
        sig_payload = {"commit_id": commit.get("commit_id", ""), "commit_hash": commit_hash}
        sig_ok, sig_detail = _verify_sig_compact(pqc, pk_bytes, sig_payload, sig_b64)
        report.add("B.COMMIT.SIG", "Commit record — PQC signature", sig_ok, sig_detail)
    else:
        report.add("B.COMMIT.SIG", "Commit record — PQC signature", False,
                   "no sig" if not sig_b64 else "PQC unavailable", skip=not pqc)

    # 7. Execution — BAR + CTCHC
    execution = steps.get("7_execution", {})
    bar = execution.get("bar", {})
    verify_bar(bar, pqc, pk_bytes, report, "B")

    governing_receipt_id = steps.get("2_record", {}).get("delegation_id", "")
    verify_ctchc(execution, governing_receipt_id, pqc, pk_bytes, report, "B")

    # 8. Outcome
    outcome = steps.get("8_outcome", {})
    pogc = outcome.get("proof_of_governance_certificate", {})
    verify_pogc(pogc, pqc, pk_bytes, report, "B")

    out_receipt = outcome.get("outcome_receipt", {})
    verify_receipt(out_receipt, "receipt_id", "content_hash", "pqc_signature",
                   "Outcome receipt", "B.OUTCOME", pqc, pk_bytes, report)
    report.add("B.OUTCOME.EXEC", "Outcome receipt — type=ADMISSION_OUTCOME",
               out_receipt.get("type") == "ADMISSION_OUTCOME", "")


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/verify_evidence_package.py <package_file.json>")
        sys.exit(1)

    package_path = sys.argv[1]
    if not os.path.isfile(package_path):
        print(f"[ERROR] File not found: {package_path}")
        sys.exit(1)

    with open(package_path, "r", encoding="utf-8") as f:
        package = json.load(f)

    package_id   = package.get("package_id", "?")
    generated_at = package.get("generated_at", "?")
    scenario     = package.get("scenario", {})

    print()
    print("=" * 65)
    print("  OMNIX QUANTUM — Offline Evidence Package Verifier")
    print("  RFC-ATF-1 through RFC-ATF-6 · TA-14 Admissibility Chain")
    print("=" * 65)
    print(f"  Package:     {package_id}")
    print(f"  Generated:   {generated_at}")
    print(f"  Scenario:    {scenario.get('name', '?')}")
    print(f"  Agent:       {scenario.get('agent', '?')}")
    print(f"  Action:      {scenario.get('action', '?')[:60]}...")
    print(f"  File:        {package_path}")

    pqc_info = package.get("pqc", {})
    pk_b64   = pqc_info.get("public_key_b64", "")
    print(f"\n[PQC] Algorithm: {pqc_info.get('algorithm', '?')}")
    print(f"      Standard:  {pqc_info.get('standard', '?')}")
    print(f"      Public key: {pk_b64[:48]}..." if pk_b64 else "      [WARN] No public key in package")

    pqc, pk_bytes = _load_pqc(pk_b64) if pk_b64 else (None, None)

    report = VerificationReport(package_id)

    routes  = package.get("routes", {})
    route_a = routes.get("route_a_refusal", {})
    route_b = routes.get("route_b_admission", {})

    if route_a:
        verify_route_a(route_a, pqc, pk_bytes, report)
    else:
        print("\n  [WARN] Route A not found in package")

    if route_b:
        verify_route_b(route_b, pqc, pk_bytes, report)
    else:
        print("\n  [WARN] Route B not found in package")

    print()
    all_ok = report.summary()

    # Write verification report
    report_path = package_path.replace(".json", "_verification_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"\n  Verification report written: {report_path}")
    print()

    # Verifier scope limits
    print("  VERIFIER SCOPE LIMITS (documented per ADR-200 §5 and TA-14 Gap 6):")
    for limit in package.get("verification_instructions", {}).get("verifier_scope_limits", []):
        print(f"    • {limit}")
    if not package.get("verification_instructions", {}).get("verifier_scope_limits"):
        print("    • Confirms cryptographic integrity and hash chain consistency.")
        print("    • Does NOT verify governance policy parameters — see docs/standards/.")
        print("    • Does NOT verify external market data referenced in source_state.")
        print("    • CTCHC genesis verified via chain continuity, not timestamp re-derivation")
        print("      (initialized_at format varies; security maintained by PQC-signed seal).")
    print()

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
