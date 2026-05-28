"""
OMNIX QUANTUM — Runtime Treasury Execution Trace Verifier
=========================================================
OMNIX-RTE-001 · ADR-201 · RFC-ATF-1 through RFC-ATF-6

Verifies every cryptographic artefact in an OMNIX-RTE-001 package
WITHOUT calling the OMNIX runtime. All verification is performed
offline using only the public key embedded in the package.

Targeted commands:
  --verify-authority      DR content_hash + PQC signature (both paths)
  --verify-continuity     RCR hash + PQC + MBR + MAS (both paths)
  --verify-counterfactual CAT content_hash + CFR root hash (both paths)
  --verify-halt           Dangerous path: refusal receipt + OSG REJECTED + CTCHC HALTED
  --verify-settlement     Admissible path: PoGC + MBR Seal + OSG APPROVED + outcome receipt
  --verify-replay         Both paths: replay proof + CTCHC seal continuity
  (default: all of the above)

Canonicalization Profile (ADR-200 §4 + ADR-201):
  - DR / TAR:            SHA-256, compact separators, excl. content_hash/pqc_sig/pqc_alg
  - RCR / Binding / Commit: SHA3-256, default separators, excl. rcr_hash/pqc_sig/pqc_alg
  - MBR:                 SHA3-256, default separators, excl. mbr_content_hash/pqc_sig
  - MAS:                 SHA3-256, default separators, excl. mas_content_hash/pqc_sig
  - MBR Seal:            SHA3-256, default separators, excl. seal_content_hash/pqc_sig
  - CAT:                 SHA3-256, default separators, excl. cat_content_hash/pqc_sig
  - TCS:                 SHA3-256, default separators, excl. tcs_hash/pqc_sig
  - OSG VR:              SHA3-256, default separators, excl. vr_content_hash/pqc_sig
  - BAR content_hash:    SHA3-256, default separators, canonical 6-field tuple
  - BAR PQC sig payload: 4-field JSON, default separators
  - CTCHC seal sig:      3-field JSON, default separators
  - Refusal / Outcome:   SHA3-256, default separators, excl. content_hash/pqc_sig/pqc_alg
  - Replay proof:        SHA3-256, default separators, excl. proof_content_hash/pqc_sig
  - PoGC:                SHA3-256, default separators, excl. content_hash/pqc_sig ONLY
  - All PQC sig payloads use compact separators

Verifier scope limits:
  ✗ Does NOT verify governance policy values (FX bands, counterparty lists, mandate amounts)
  ✗ Does NOT verify external market data in source_state
  ✗ Does NOT require OMNIX runtime, database, or network access
  ✓ DOES confirm embedded public key produces valid signatures for ALL artefacts
  ✓ DOES confirm dangerous path HALTED and admissible path CLOSED

Usage:
  python scripts/verify_treasury_execution_trace.py <package.json>
  python scripts/verify_treasury_execution_trace.py <package.json> --verify-authority
  python scripts/verify_treasury_execution_trace.py <package.json> --verify-continuity
  python scripts/verify_treasury_execution_trace.py <package.json> --verify-counterfactual
  python scripts/verify_treasury_execution_trace.py <package.json> --verify-halt
  python scripts/verify_treasury_execution_trace.py <package.json> --verify-settlement
  python scripts/verify_treasury_execution_trace.py <package.json> --verify-replay
  python scripts/verify_treasury_execution_trace.py <package.json> --json   (machine-readable output)

Exit codes:
  0 — all selected verifications PASS
  1 — one or more verifications FAIL
  2 — package file not found or not a valid RTE-001 package

Author: Harold Nunes — OMNIX QUANTUM LTD
ADR: ADR-201
"""

from __future__ import annotations

import argparse
import base64
import glob
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Expected total checks when verifier runs in FULL mode against an RTE-001 package.
# Used by consistency audits and CI pipelines.
EXPECTED_TOTAL_CHECKS = 101


def _auto_detect_package() -> Optional[str]:
    """
    Locate an OMNIX-RTE-001 JSON package automatically.
    Search order:
      1. <script_dir>/evidence/OMNIX-RTE-001_*.json   — reviewer package layout
         (verify.py sits alongside evidence/ in the package root)
      2. <script_dir>/../evidence_packages/OMNIX-RTE-001_*.json — repo layout
         (verify_treasury_execution_trace.py sits in scripts/, evidence_packages/ is at repo root)
    Returns the most recent match, or None.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates: List[str] = []
    for pattern in [
        # Reviewer package layout: evidence/ is a sibling of verify.py
        os.path.join(script_dir, "evidence", "OMNIX-RTE-001_*.json"),
        # Repo layout: evidence_packages/ is at repo root, script is in scripts/
        os.path.join(script_dir, "..", "evidence_packages", "OMNIX-RTE-001_*.json"),
    ]:
        candidates.extend(sorted(glob.glob(os.path.normpath(pattern))))
    # Deduplicate while preserving order
    seen: set = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique[-1] if unique else None


# ─────────────────────────────────────────────────────────────────────────────
#  Verification report
# ─────────────────────────────────────────────────────────────────────────────

class VerificationReport:
    def __init__(self, package_id: str, target_mode: str):
        self.package_id  = package_id
        self.target_mode = target_mode
        self.checks: List[Dict] = []
        self.passed  = 0
        self.failed  = 0
        self.skipped = 0

    def add(self, check_id: str, label: str, passed: bool,
            detail: str = "", skip: bool = False, path: str = "") -> None:
        status = "SKIP" if skip else ("PASS" if passed else "FAIL")
        icon   = "·" if skip else ("✓" if passed else "✗")
        path_tag = f"[{path}] " if path else ""
        self.checks.append({
            "id": check_id, "label": label, "status": status,
            "detail": detail, "path": path,
        })
        if skip:
            self.skipped += 1
        elif passed:
            self.passed += 1
        else:
            self.failed += 1
        if skip:
            colour = "\033[90m"
        elif passed:
            colour = "\033[32m"
        else:
            colour = "\033[31m"
        reset = "\033[0m"
        detail_str = f"\n      → {detail}" if detail and not passed else ""
        print(f"  {colour}{icon} [{check_id}] {path_tag}{label}{reset}{detail_str}")

    def section(self, title: str) -> None:
        print(f"\n  {'─'*60}")
        print(f"  {title}")
        print(f"  {'─'*60}")

    def summary(self) -> bool:
        total  = self.passed + self.failed + self.skipped
        all_ok = self.failed == 0
        colour = "\033[32m" if all_ok else "\033[31m"
        reset  = "\033[0m"
        print()
        print("═" * 65)
        print(f"  OMNIX-RTE-001 VERIFICATION REPORT")
        print(f"  Package:  {self.package_id}")
        print(f"  Mode:     {self.target_mode}")
        print(f"  Time:     {datetime.now(timezone.utc).isoformat()}")
        print("─" * 65)
        print(f"  TOTAL CHECKS : {total}")
        print(f"  {colour}PASSED{reset}        : {self.passed}")
        print(f"  \033[31mFAILED\033[0m        : {self.failed}")
        skip_note = " (pip install pqc to enable)" if self.skipped > 0 else ""
        print(f"  \033[90mSKIPPED\033[0m       : {self.skipped}{skip_note}")
        print("─" * 65)
        if all_ok and self.skipped == 0:
            print(f"  {colour}VERDICT: ALL VERIFICATIONS PASS — package integrity confirmed{reset}")
        elif all_ok and self.skipped > 0:
            print(f"  {colour}VERDICT: STRUCTURAL + HASH CHECKS PASS{reset}")
            print(f"  \033[90m         {self.skipped} PQC signature check(s) skipped — install pqc: pip install pqc{reset}")
        else:
            print(f"  \033[31mVERDICT: {self.failed} VERIFICATION(S) FAILED — package integrity compromised\033[0m")
        print("═" * 65)
        return all_ok

    def to_dict(self) -> Dict:
        return {
            "package_id":   self.package_id,
            "target_mode":  self.target_mode,
            "verified_at":  datetime.now(timezone.utc).isoformat(),
            "total_checks": self.passed + self.failed + self.skipped,
            "passed":       self.passed,
            "failed":       self.failed,
            "skipped":      self.skipped,
            "verdict":      "PASS" if self.failed == 0 else "FAIL",
            "checks":       self.checks,
        }


# ─────────────────────────────────────────────────────────────────────────────
#  PQC loader (offline — uses embedded public key)
# ─────────────────────────────────────────────────────────────────────────────

def _load_pqc(pk_b64: str):
    """
    Load PQC verifier from embedded public key. No private key needed.

    Import priority:
      1. pqc  PyPI library  (pip install pqc) — available to external reviewers
      2. omnix_core internal wrapper            — available inside the OMNIX repo
    Returns (verifier_obj, pk_bytes) or (None, error_message).
    """
    pk_bytes = base64.b64decode(pk_b64)

    # — Priority 1: pqc PyPI library (standalone, no OMNIX dependency) —
    try:
        from pqc.sign import dilithium3 as _dil3

        class _PyPIVerifier:
            """Thin wrapper so the rest of the verifier sees a uniform interface."""
            pqc_enabled = True

            def verify_signature(self, sig_bytes: bytes, msg_bytes: bytes, pk: bytes) -> bool:
                try:
                    _dil3.verify(sig_bytes, msg_bytes, pk)
                    return True
                except Exception:
                    return False

        return _PyPIVerifier(), pk_bytes
    except ImportError:
        pass

    # — Priority 2: omnix_core internal (repo environment) —
    try:
        from omnix_core.security.pqc_security import PostQuantumSecurity
        pqc_obj = PostQuantumSecurity()
        if not pqc_obj.pqc_enabled:
            return None, "PQC not available (pypqc not installed)"
        return pqc_obj, pk_bytes
    except Exception:
        pass

    return None, "PQC library not found — install with: pip install pqc"


# Sentinel returned by _verify_sig* when the PQC library is absent.
# Callers check `ok is _PQC_SKIP` to distinguish "library missing" from a real failure.
_PQC_SKIP = None


def _verify_sig(pqc, pk_bytes: bytes, payload: Dict,
                sig_b64: Optional[str], compact: bool = True) -> Tuple[Optional[bool], str]:
    """
    Verify a PQC signature against a JSON payload.
    Returns (True, '') on success, (False, reason) on failure,
    or (None, hint) when PQC library is not installed — callers must treat None as SKIP.
    """
    if not sig_b64:
        return False, "signature absent"
    if pqc is None:
        return _PQC_SKIP, "PQC not available — install with: pip install pqc"
    try:
        sep       = (",", ":") if compact else (", ", ": ")
        raw       = json.dumps(payload, sort_keys=True, separators=sep).encode("utf-8")
        sig_bytes = base64.b64decode(sig_b64)
        ok        = pqc.verify_signature(sig_bytes, raw, pk_bytes)
        return ok, "" if ok else "signature mismatch"
    except Exception as e:
        return False, str(e)


def _verify_sig_bytes(pqc, pk_bytes: bytes, raw_bytes: bytes,
                      sig_b64: Optional[str]) -> Tuple[Optional[bool], str]:
    """
    Verify a PQC signature against raw bytes (DR/TAR sign content_hash directly).
    Returns (None, hint) when PQC library is not installed — callers must treat None as SKIP.
    """
    if not sig_b64:
        return False, "signature absent"
    if pqc is None:
        return _PQC_SKIP, "PQC not available — install with: pip install pqc"
    try:
        sig_bytes = base64.b64decode(sig_b64)
        ok        = pqc.verify_signature(sig_bytes, raw_bytes, pk_bytes)
        return ok, "" if ok else "signature mismatch"
    except Exception as e:
        return False, str(e)


def _verify_sig_default(pqc, pk_bytes: bytes, payload: Dict,
                        sig_b64: Optional[str]) -> Tuple[Optional[bool], str]:
    """
    Verify a PQC signature with default separators (BAREngine / CTCHCEngine profile).
    Returns (None, hint) when PQC library is not installed — callers must treat None as SKIP.
    """
    if not sig_b64:
        return False, "signature absent"
    if pqc is None:
        return _PQC_SKIP, "PQC not available — install with: pip install pqc"
    try:
        raw       = json.dumps(payload, sort_keys=True).encode("utf-8")
        sig_bytes = base64.b64decode(sig_b64)
        ok        = pqc.verify_signature(sig_bytes, raw, pk_bytes)
        return ok, "" if ok else "signature mismatch"
    except Exception as e:
        return False, str(e)


def _add_sig(report: "VerificationReport", check_id: str, label: str,
             ok: Optional[bool], detail: str, path: str = "") -> None:
    """
    Wrapper for report.add for PQC signature checks.
    Converts the None sentinel (PQC library absent) into a proper SKIP entry.
    """
    if ok is _PQC_SKIP:
        report.add(check_id, label, False, detail, skip=True, path=path)
    else:
        report.add(check_id, label, bool(ok), detail, path=path)


# ─────────────────────────────────────────────────────────────────────────────
#  Hash helpers (canonical)
# ─────────────────────────────────────────────────────────────────────────────

def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def _sha3(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()

def _hash_compact(fields: Dict, exclude: List[str]) -> str:
    """SHA-256 with compact separators (DR/TAR profile)."""
    d = {k: v for k, v in fields.items() if k not in exclude}
    return _sha256(json.dumps(d, sort_keys=True, separators=(",", ":")))

def _hash_default(fields: Dict, exclude: List[str]) -> str:
    """SHA3-256 with default separators (most artefacts)."""
    d = {k: v for k, v in fields.items() if k not in exclude}
    return _sha3(json.dumps(d, sort_keys=True))


# ─────────────────────────────────────────────────────────────────────────────
#  Individual artefact verifiers
# ─────────────────────────────────────────────────────────────────────────────

def _check_dr(report: VerificationReport, dr: Dict, pqc, pk_bytes: bytes, path: str) -> None:
    """DR: SHA-256 compact + PQC signature over content_hash bytes (DelegationReceiptEngine profile)."""
    expected = _hash_compact(dr, exclude=["content_hash", "pqc_signature", "pqc_algorithm"])
    actual   = dr.get("content_hash", "")
    hash_ok  = expected == actual
    report.add(f"DR-{path[:3]}-HASH", "DR content_hash integrity",
               hash_ok, f"expected={expected[:20]}... got={actual[:20]}...", path=path)

    # DelegationReceiptEngine signs content_hash.encode("utf-8") directly — not a JSON payload
    raw_ch = actual.encode("utf-8")
    ok, detail = _verify_sig_bytes(pqc, pk_bytes, raw_ch, dr.get("pqc_signature"))
    _add_sig(report, f"DR-{path[:3]}-SIG", "DR PQC signature (ML-DSA-65)", ok, detail, path=path)


def _check_tar(report: VerificationReport, tar: Dict, pqc, pk_bytes: bytes, path: str) -> None:
    """TAR: SHA-256 compact + PQC signature over content_hash bytes (TemporalAuthorityEngine profile)."""
    expected = _hash_compact(tar, exclude=["content_hash", "pqc_signature", "pqc_algorithm"])
    actual   = tar.get("content_hash", "")
    hash_ok  = expected == actual
    report.add(f"TAR-{path[:3]}-HASH", "TAR content_hash integrity",
               hash_ok, f"expected={expected[:20]}... got={actual[:20]}...", path=path)

    # TemporalAuthorityEngine signs content_hash.encode("utf-8") directly — not a JSON payload
    raw_ch = actual.encode("utf-8")
    ok, detail = _verify_sig_bytes(pqc, pk_bytes, raw_ch, tar.get("pqc_signature"))
    _add_sig(report, f"TAR-{path[:3]}-SIG", "TAR PQC signature (ML-DSA-65)", ok, detail, path=path)


def _check_rcr(report: VerificationReport, rcr: Dict, pqc, pk_bytes: bytes, path: str) -> None:
    """RCR: SHA3-256 default (excluding rcr_hash) + compact sig over {rcr_id, rcr_hash}."""
    expected = _hash_default(rcr, exclude=["rcr_hash", "pqc_signature", "pqc_algorithm"])
    actual   = rcr.get("rcr_hash", "")
    hash_ok  = expected == actual
    report.add(f"RCR-{path[:3]}-HASH", "RCR continuity hash integrity",
               hash_ok, f"expected={expected[:20]}... got={actual[:20]}...", path=path)

    sig_payload = {"rcr_id": rcr.get("rcr_id"), "rcr_hash": actual}
    ok, detail  = _verify_sig(pqc, pk_bytes, sig_payload, rcr.get("pqc_signature"), compact=True)
    _add_sig(report, f"RCR-{path[:3]}-SIG", "RCR PQC signature", ok, detail, path=path)


def _check_mbr(report: VerificationReport, mbr: Dict, pqc, pk_bytes: bytes, path: str) -> None:
    expected = _hash_default(mbr, exclude=["mbr_content_hash", "pqc_signature", "pqc_algorithm"])
    actual   = mbr.get("mbr_content_hash", "")
    hash_ok  = expected == actual
    report.add(f"MBR-{path[:3]}-HASH", "MBR content_hash integrity",
               hash_ok, f"expected={expected[:20]}... got={actual[:20]}...", path=path)

    sig_payload = {"mbr_id": mbr.get("mbr_id"), "mbr_content_hash": actual, "issued_at": mbr.get("issued_at")}
    ok, detail  = _verify_sig(pqc, pk_bytes, sig_payload, mbr.get("pqc_signature"), compact=True)
    _add_sig(report, f"MBR-{path[:3]}-SIG", "MBR PQC signature (MIVP-INV-001)", ok, detail, path=path)


def _check_mas(report: VerificationReport, mas: Dict, pqc, pk_bytes: bytes, path: str) -> None:
    expected = _hash_default(mas, exclude=["mas_content_hash", "pqc_signature", "pqc_algorithm"])
    actual   = mas.get("mas_content_hash", "")
    hash_ok  = expected == actual
    report.add(f"MAS-{path[:3]}-HASH", "MAS content_hash integrity",
               hash_ok, f"expected={expected[:20]}... got={actual[:20]}...", path=path)

    sig_payload = {"mas_id": mas.get("mas_id"), "mas_content_hash": actual, "issued_at": mas.get("issued_at")}
    ok, detail  = _verify_sig(pqc, pk_bytes, sig_payload, mas.get("pqc_signature"), compact=True)
    _add_sig(report, f"MAS-{path[:3]}-SIG", "MAS PQC signature (MIVP-INV-003)", ok, detail, path=path)


def _check_mbr_seal(report: VerificationReport, seal: Dict, pqc, pk_bytes: bytes, path: str) -> None:
    expected = _hash_default(seal, exclude=["seal_content_hash", "pqc_signature", "pqc_algorithm"])
    actual   = seal.get("seal_content_hash", "")
    hash_ok  = expected == actual
    report.add(f"SEAL-{path[:3]}-HASH", "MBR Seal content_hash integrity",
               hash_ok, f"expected={expected[:20]}... got={actual[:20]}...", path=path)

    sig_payload = {"seal_id": seal.get("seal_id"), "seal_content_hash": actual, "issued_at": seal.get("issued_at")}
    ok, detail  = _verify_sig(pqc, pk_bytes, sig_payload, seal.get("pqc_signature"), compact=True)
    _add_sig(report, f"SEAL-{path[:3]}-SIG", "MBR Seal PQC signature (MIVP-INV-007)", ok, detail, path=path)

    # Semantic check: dangerous path → UNCERTIFIED, admissible → MANDATE-BOUND
    tier = seal.get("certification_tier", "")
    if path == "DANGEROUS":
        correct = tier == "UNCERTIFIED"
        report.add(f"SEAL-{path[:3]}-TIER", f"MBR Seal tier=UNCERTIFIED (dangerous path)",
                   correct, f"got={tier}", path=path)
    elif path == "ADMISSIBLE":
        correct = tier == "MANDATE-BOUND"
        report.add(f"SEAL-{path[:3]}-TIER", f"MBR Seal tier=MANDATE-BOUND (admissible path, MIVP-INV-008)",
                   correct, f"got={tier}", path=path)


def _check_cat(report: VerificationReport, cat: Dict, cfrs: List[Dict],
               pqc, pk_bytes: bytes, path: str) -> None:
    """CAT: content_hash + CFR root hash covers all CFR IDs (CGE-INV-002)."""
    # CFR root hash
    expected_root = _sha3(json.dumps([c["cfr_id"] for c in cfrs], sort_keys=True))
    actual_root   = cat.get("cfr_root_hash", "")
    report.add(f"CAT-{path[:3]}-ROOT", "CAT cfr_root_hash covers all CFR IDs (CGE-INV-002)",
               expected_root == actual_root,
               f"expected={expected_root[:20]}... got={actual_root[:20]}...", path=path)

    # CFR count
    report.add(f"CAT-{path[:3]}-COUNT", f"CAT cfr_count ≥ 3 (RTE-INV-005, got {cat.get('cfr_count', 0)})",
               cat.get("cfr_count", 0) >= 3, path=path)

    # fragility scores in [0.0, 1.0] (CGE-INV-003)
    frag_ok = all(0.0 <= c.get("fragility_score", -1) <= 1.0 for c in cfrs)
    report.add(f"CAT-{path[:3]}-FRAG", "All CFR fragility_scores ∈ [0.0, 1.0] (CGE-INV-003)",
               frag_ok, path=path)

    # content_hash + PQC
    expected_hash = _hash_default(cat, exclude=["cat_content_hash", "pqc_signature", "pqc_algorithm"])
    actual_hash   = cat.get("cat_content_hash", "")
    report.add(f"CAT-{path[:3]}-HASH", "CAT content_hash integrity",
               expected_hash == actual_hash,
               f"expected={expected_hash[:20]}... got={actual_hash[:20]}...", path=path)

    sig_payload = {"cat_id": cat.get("cat_id"), "cat_content_hash": actual_hash, "issued_at": cat.get("issued_at")}
    ok, detail  = _verify_sig(pqc, pk_bytes, sig_payload, cat.get("pqc_signature"), compact=True)
    _add_sig(report, f"CAT-{path[:3]}-SIG", "CAT PQC signature (CGE-INV-007)", ok, detail, path=path)


def _check_osg_vr(report: VerificationReport, vr: Dict, expected_verdict: str,
                  pqc, pk_bytes: bytes, path: str) -> None:
    expected_hash = _hash_default(vr, exclude=["vr_content_hash", "pqc_signature", "pqc_algorithm"])
    actual_hash   = vr.get("vr_content_hash", "")
    report.add(f"OSG-{path[:3]}-HASH", "OSG VR content_hash integrity",
               expected_hash == actual_hash,
               f"expected={expected_hash[:20]}... got={actual_hash[:20]}...", path=path)

    sig_payload = {"vr_id": vr.get("vr_id"), "vr_content_hash": actual_hash, "issued_at": vr.get("issued_at")}
    ok, detail  = _verify_sig(pqc, pk_bytes, sig_payload, vr.get("pqc_signature"), compact=True)
    _add_sig(report, f"OSG-{path[:3]}-SIG", "OSG VR PQC signature", ok, detail, path=path)

    # Verdict semantic
    verdict = vr.get("verdict", "")
    report.add(f"OSG-{path[:3]}-VERDICT", f"OSG verdict={expected_verdict} ({path} path)",
               verdict == expected_verdict, f"got={verdict}", path=path)

    # fail-closed flag
    report.add(f"OSG-{path[:3]}-FAILCLOSED", "OSG fail_closed=True",
               vr.get("fail_closed") is True, path=path)


def _check_bar(report: VerificationReport, bar: Dict, pqc, pk_bytes: bytes, path: str) -> None:
    """BAR: SHA3-256 of canonical 6-field tuple (default sep) — BEV-INV-002."""
    # BEV-INV-002: content_hash = SHA3-256({session_id, agent_id, turn_index,
    #              output_hash, governing_receipt_id, constraint_set_hash}, default sep)
    fields = {
        "session_id":           bar.get("session_id"),
        "agent_id":             bar.get("agent_id"),
        "turn_index":           bar.get("turn_index"),
        "output_hash":          bar.get("output_hash"),
        "governing_receipt_id": bar.get("governing_receipt_id"),
        "constraint_set_hash":  bar.get("constraint_set_hash"),
    }
    expected = _sha3(json.dumps(fields, sort_keys=True))
    actual   = bar.get("content_hash", "")
    report.add(f"BAR-{path[:3]}-HASH", "BAR content_hash (SHA3-256 canonical 6-field, BEV-INV-002)",
               expected == actual, f"expected={expected[:20]}... got={actual[:20]}...", path=path)

    # BAREngine signs with default separators: {bar_id, content_hash, governing_receipt_id, created_at}
    sig_payload = {
        "bar_id":                bar.get("bar_id"),
        "content_hash":          actual,
        "governing_receipt_id":  bar.get("governing_receipt_id"),
        "created_at":            bar.get("created_at"),
    }
    ok, detail = _verify_sig_default(pqc, pk_bytes, sig_payload, bar.get("pqc_signature"))
    _add_sig(report, f"BAR-{path[:3]}-SIG", "BAR PQC signature (BEV-INV-004, default sep)",
             ok, detail, path=path)


def _check_ctchc(report: VerificationReport, links: List[Dict], sealed: Dict,
                 pqc, pk_bytes: bytes, path: str) -> None:
    """CTCHC: link chain hash continuity + seal_hash + PQC sig (BEV-INV-010–014)."""
    ordered = sorted(links, key=lambda x: x.get("turn_index", 0))

    # BEV-INV-010: first link's prev_link_hash = genesis_hash
    if ordered:
        genesis_ok = ordered[0].get("prev_link_hash") == sealed.get("genesis_hash")
        report.add(f"CHC-{path[:3]}-GENESIS", "CTCHC genesis: first link references genesis_hash (BEV-INV-010)",
                   genesis_ok, f"prev={ordered[0].get('prev_link_hash','?')[:16]}... genesis={sealed.get('genesis_hash','?')[:16]}...", path=path)

    # BEV-INV-011: link-by-link continuity — each link's prev = previous link's chain_link_hash
    chain_ok = True
    prev_hash = sealed.get("genesis_hash", "")
    for lk in ordered:
        expected_link_payload = json.dumps({
            "prev":    prev_hash,
            "turn":    lk.get("turn_hash", ""),
            "receipt": lk.get("governing_receipt_id", ""),
        }, sort_keys=True)
        expected_link_hash = hashlib.sha3_256(expected_link_payload.encode()).hexdigest()
        if lk.get("chain_link_hash") != expected_link_hash:
            chain_ok = False
        prev_hash = lk.get("chain_link_hash", prev_hash)
    report.add(f"CHC-{path[:3]}-CHAIN", f"CTCHC link chain continuity ({len(ordered)} links, BEV-INV-011)",
               chain_ok, path=path)

    # BEV-INV-013: seal_hash = SHA3-256({chain_id, session_id, governing_receipt_id,
    #              genesis_hash, turn_count, link_hashes, tip_hash}, default sep)
    seal_payload = json.dumps({
        "chain_id":             sealed.get("chain_id"),
        "session_id":           sealed.get("session_id"),
        "governing_receipt_id": sealed.get("governing_receipt_id"),
        "genesis_hash":         sealed.get("genesis_hash"),
        "turn_count":           len(ordered),
        "link_hashes":          [lk.get("chain_link_hash", "") for lk in ordered],
        "tip_hash":             sealed.get("current_tip_hash"),
    }, sort_keys=True)
    expected_seal = hashlib.sha3_256(seal_payload.encode()).hexdigest()
    actual_seal   = sealed.get("seal_hash", "")
    report.add(f"CHC-{path[:3]}-SEAL", "CTCHC seal_hash covers complete chain (BEV-INV-013)",
               expected_seal == actual_seal,
               f"expected={expected_seal[:20]}... got={actual_seal[:20]}...", path=path)

    # BEV-INV-014: CTCHCEngine seal signs {chain_id, seal_hash, session_id} default sep
    seal_sig_payload = {
        "chain_id":   sealed.get("chain_id"),
        "seal_hash":  actual_seal,
        "session_id": sealed.get("session_id"),
    }
    ok, detail = _verify_sig_default(pqc, pk_bytes, seal_sig_payload,
                                     sealed.get("seal_pqc_signature"))
    _add_sig(report, f"CHC-{path[:3]}-SIG", "CTCHC seal PQC signature (BEV-INV-014, default sep)",
             ok, detail, path=path)


def _check_pogc(report: VerificationReport, pogc: Dict, pqc, pk_bytes: bytes) -> None:
    """PoGC: SHA3-256 default, excl. content_hash + pqc_signature only (pqc_algorithm IS included)."""
    expected = _hash_default(pogc, exclude=["content_hash", "pqc_signature"])
    actual   = pogc.get("content_hash", "")
    report.add("POGC-HASH", "PoGC content_hash integrity (pqc_algorithm included per ADR-200 §4.3)",
               expected == actual, f"expected={expected[:20]}... got={actual[:20]}...", path="ADMISSIBLE")

    sig_payload = {"pogc_id": pogc.get("pogc_id"), "content_hash": actual, "issued_at": pogc.get("issued_at")}
    ok, detail  = _verify_sig(pqc, pk_bytes, sig_payload, pogc.get("pqc_signature"), compact=True)
    _add_sig(report, "POGC-SIG", "PoGC PQC signature (ML-DSA-65, PoGR-INV-003)", ok, detail, path="ADMISSIBLE")

    # Mandate certification
    tier = pogc.get("mandate_certification", "")
    report.add("POGC-BOUND", "PoGC mandate_certification=MANDATE-BOUND (MIVP-INV-008, RTE-INV-004)",
               tier == "MANDATE-BOUND", f"got={tier}", path="ADMISSIBLE")


def _check_tcs(report: VerificationReport, tcs: Dict, pqc, pk_bytes: bytes, path: str) -> None:
    expected = _hash_default(tcs, exclude=["tcs_hash", "pqc_signature", "pqc_algorithm"])
    actual   = tcs.get("tcs_hash", "")
    report.add(f"TCS-{path[:3]}-HASH", "TCS hash integrity (TGB-INV-001)",
               expected == actual,
               f"expected={expected[:20]}... got={actual[:20]}...", path=path)

    sig_payload = {"tcs_id": tcs.get("tcs_id"), "tcs_hash": actual, "issued_at": tcs.get("issued_at")}
    ok, detail  = _verify_sig(pqc, pk_bytes, sig_payload, tcs.get("pqc_signature"), compact=True)
    _add_sig(report, f"TCS-{path[:3]}-SIG", "TCS PQC signature", ok, detail, path=path)

    # Regulatory context present
    report.add(f"TCS-{path[:3]}-REG", "TCS regulatory_context present (TGB-INV-001)",
               bool(tcs.get("regulatory_context")), path=path)


def _check_refusal(report: VerificationReport, receipt: Dict, pqc, pk_bytes: bytes) -> None:
    expected = _hash_default(receipt, exclude=["content_hash", "pqc_signature", "pqc_algorithm"])
    actual   = receipt.get("content_hash", "")
    report.add("REF-HASH", "Refusal receipt content_hash integrity",
               expected == actual, f"expected={expected[:20]}... got={actual[:20]}...", path="DANGEROUS")

    sig_payload = {"receipt_id": receipt.get("receipt_id"), "content_hash": actual, "issued_at": receipt.get("issued_at")}
    ok, detail  = _verify_sig(pqc, pk_bytes, sig_payload, receipt.get("pqc_signature"), compact=True)
    _add_sig(report, "REF-SIG", "Refusal receipt PQC signature", ok, detail, path="DANGEROUS")

    # Type and settlement block
    report.add("REF-TYPE", "Refusal receipt type=HARD_REFUSAL",
               receipt.get("type") == "HARD_REFUSAL", path="DANGEROUS")
    report.add("REF-SETTLE", "Refusal receipt settlement_status=BLOCKED (RTE-INV-002)",
               "BLOCKED" in receipt.get("settlement_status", ""), path="DANGEROUS")
    report.add("REF-REASONS", f"Refusal receipt has ≥3 rejection_reasons (got {receipt.get('rejection_count', 0)})",
               receipt.get("rejection_count", 0) >= 3, path="DANGEROUS")


def _check_outcome(report: VerificationReport, receipt: Dict, pqc, pk_bytes: bytes) -> None:
    expected = _hash_default(receipt, exclude=["content_hash", "pqc_signature", "pqc_algorithm"])
    actual   = receipt.get("content_hash", "")
    report.add("OUT-HASH", "Outcome receipt content_hash integrity",
               expected == actual, f"expected={expected[:20]}... got={actual[:20]}...", path="ADMISSIBLE")

    sig_payload = {"receipt_id": receipt.get("receipt_id"), "content_hash": actual, "issued_at": receipt.get("issued_at")}
    ok, detail  = _verify_sig(pqc, pk_bytes, sig_payload, receipt.get("pqc_signature"), compact=True)
    _add_sig(report, "OUT-SIG", "Outcome receipt PQC signature", ok, detail, path="ADMISSIBLE")

    report.add("OUT-TYPE", "Outcome receipt type=ADMISSION_OUTCOME",
               receipt.get("type") == "ADMISSION_OUTCOME", path="ADMISSIBLE")
    report.add("OUT-CERTIF", "Outcome receipt mandate_certification=MANDATE-BOUND",
               receipt.get("mandate_certification") == "MANDATE-BOUND", path="ADMISSIBLE")
    report.add("OUT-SETTLE", "Outcome receipt has settlement_reference",
               bool(receipt.get("settlement_reference")), path="ADMISSIBLE")


def _check_replay(report: VerificationReport, proof: Dict, pqc, pk_bytes: bytes,
                  path: str, expected_status: str) -> None:
    expected = _hash_default(proof, exclude=["proof_content_hash", "pqc_signature", "pqc_algorithm"])
    actual   = proof.get("proof_content_hash", "")
    report.add(f"RPL-{path[:3]}-HASH", "Replay proof content_hash integrity",
               expected == actual, f"expected={expected[:20]}... got={actual[:20]}...", path=path)

    sig_payload = {"proof_id": proof.get("proof_id"), "proof_content_hash": actual, "issued_at": proof.get("issued_at")}
    ok, detail  = _verify_sig(pqc, pk_bytes, sig_payload, proof.get("pqc_signature"), compact=True)
    _add_sig(report, f"RPL-{path[:3]}-SIG", "Replay proof PQC signature", ok, detail, path=path)

    report.add(f"RPL-{path[:3]}-STATUS", f"Replay proof terminal_status={expected_status}",
               proof.get("terminal_status") == expected_status,
               f"got={proof.get('terminal_status')}", path=path)

    report.add(f"RPL-{path[:3]}-OFFLINE", "Replay proof offline_verifiable=True (RTE-INV-007)",
               proof.get("offline_verifiable") is True, path=path)


# ─────────────────────────────────────────────────────────────────────────────
#  Targeted verification suites
# ─────────────────────────────────────────────────────────────────────────────

def verify_authority(report: VerificationReport, pkg: Dict, pqc, pk_bytes: bytes) -> None:
    report.section("AUTHORITY — DR + MBR (both paths)")
    for path_key, path_label in [("path_dangerous", "DANGEROUS"), ("path_admissible", "ADMISSIBLE")]:
        p = pkg["paths"][path_key]
        dr = p["steps"]["2_authority"]["delegation_receipt"]
        mbr = p["steps"]["2_authority"]["mandate_binding_record"]
        _check_dr(report, dr, pqc, pk_bytes, path_label)
        _check_mbr(report, mbr, pqc, pk_bytes, path_label)

        # MAR semantic: budget_granted ≤ budget_delegator
        bg = dr.get("authority_budget_granted", -1)
        bd = dr.get("authority_budget_delegator", -1)
        report.add(f"DR-{path_label[:3]}-MAR", f"DR MAR: budget_granted({bg}) ≤ budget_delegator({bd}) (ATF-INV-001)",
                   bg <= bd, path=path_label)


def verify_continuity(report: VerificationReport, pkg: Dict, pqc, pk_bytes: bytes) -> None:
    report.section("CONTINUITY — RCR + MAS (both paths)")
    for path_key, path_label in [("path_dangerous", "DANGEROUS"), ("path_admissible", "ADMISSIBLE")]:
        p = pkg["paths"][path_key]
        rcr = p["steps"]["3_runtime"]["continuity_record"]
        mas = p["steps"]["3_runtime"]["mandate_alignment_score"]
        _check_rcr(report, rcr, pqc, pk_bytes, path_label)
        _check_mas(report, mas, pqc, pk_bytes, path_label)

        # CES components add up
        comps = rcr.get("ces_components", {})
        T, B, D, I = (comps.get("T_temporal_health_pct", 0),
                      comps.get("B_budget_health_pct", 0),
                      comps.get("D_context_fidelity_pct", 0),
                      comps.get("I_integrity_score_pct", 0))
        expected_ces = round((T * 0.30) + (B * 0.30) + (D * 0.20) + (I * 0.20), 2)
        actual_ces   = rcr.get("ces_score", -1)
        report.add(f"RCR-{path_label[:3]}-CES", f"CES formula consistent (expected≈{expected_ces}, got={actual_ces})",
                   abs(expected_ces - actual_ces) < 1.0, path=path_label)

        # Semantic: dangerous CES should be critical, admissible should be nominal
        band = rcr.get("ces_band", "")
        if path_label == "DANGEROUS":
            report.add(f"RCR-{path_label[:3]}-BAND", f"CES band CRITICAL (dangerous path, got={band})",
                       band == "CRITICAL", path=path_label)
        else:
            report.add(f"RCR-{path_label[:3]}-BAND", f"CES band NOMINAL (admissible path, got={band})",
                       band == "NOMINAL", path=path_label)


def verify_counterfactual(report: VerificationReport, pkg: Dict, pqc, pk_bytes: bytes) -> None:
    report.section("COUNTERFACTUAL — CGE CFRs + CAT (both paths)")
    for path_key, path_label in [("path_dangerous", "DANGEROUS"), ("path_admissible", "ADMISSIBLE")]:
        p    = pkg["paths"][path_key]
        cfe  = p["steps"]["4_counterfactual"]
        cfrs = cfe.get("counterfactual_fork_records", [])
        cat  = cfe.get("counterfactual_attestation_token", {})
        _check_cat(report, cat, cfrs, pqc, pk_bytes, path_label)

        # Exactly one selected CFR
        selected = [c for c in cfrs if c.get("selected_path")]
        report.add(f"CAT-{path_label[:3]}-SEL", "Exactly one CFR marked selected_path=True",
                   len(selected) == 1, f"found {len(selected)}", path=path_label)


def verify_halt(report: VerificationReport, pkg: Dict, pqc, pk_bytes: bytes) -> None:
    report.section("HALT — Dangerous path: refusal + OSG REJECTED + CTCHC HALTED (RTE-INV-002/003)")
    p    = pkg["paths"]["path_dangerous"]
    exec_ = p["steps"]["7_execution"]

    refusal = exec_.get("refusal_receipt", {})
    _check_refusal(report, refusal, pqc, pk_bytes)

    mbr_seal = exec_.get("mbr_seal", {})
    _check_mbr_seal(report, mbr_seal, pqc, pk_bytes, "DANGEROUS")

    bar    = exec_.get("bar", {})
    _check_bar(report, bar, pqc, pk_bytes, "DANGEROUS")

    links  = exec_.get("ctchc_links", [])
    sealed = exec_.get("ctchc_sealed", {})
    _check_ctchc(report, links, sealed, pqc, pk_bytes, "DANGEROUS")

    osg_vr = p["steps"]["6_gate"]
    _check_osg_vr(report, osg_vr, "REJECTED", pqc, pk_bytes, "DANGEROUS")

    # Structural: execution_occurred=False
    summary = p.get("summary", {})
    report.add("HALT-EXEC", "dangerous path: execution_occurred=False (RTE-INV-002)",
               summary.get("execution_occurred") is False, path="DANGEROUS")
    report.add("HALT-SETTLE", "dangerous path: settlement_released=False",
               summary.get("settlement_released") is False, path="DANGEROUS")


def verify_settlement(report: VerificationReport, pkg: Dict, pqc, pk_bytes: bytes) -> None:
    report.section("SETTLEMENT — Admissible path: PoGC + MBR Seal + OSG APPROVED + outcome (RTE-INV-004)")
    p    = pkg["paths"]["path_admissible"]
    gate = p["steps"]["6_gate"]
    exec_ = p["steps"]["7_execution"]

    pogc = gate.get("proof_of_governance_certificate", {})
    _check_pogc(report, pogc, pqc, pk_bytes)

    mbr_seal = gate.get("mbr_seal", {})
    _check_mbr_seal(report, mbr_seal, pqc, pk_bytes, "ADMISSIBLE")

    osg_vr = gate.get("osg_validation_receipt", {})
    _check_osg_vr(report, osg_vr, "APPROVED", pqc, pk_bytes, "ADMISSIBLE")

    bar    = exec_.get("bar", {})
    _check_bar(report, bar, pqc, pk_bytes, "ADMISSIBLE")

    links  = exec_.get("ctchc_links", [])
    sealed = exec_.get("ctchc_sealed", {})
    _check_ctchc(report, links, sealed, pqc, pk_bytes, "ADMISSIBLE")

    # TAR verdict
    verdict_step = p["steps"]["5_verdict"]
    tar = verdict_step.get("temporal_admissibility_record", {})
    if tar:
        _check_tar(report, tar, pqc, pk_bytes, "ADMISSIBLE")

    outcome = exec_.get("outcome_receipt", {})
    _check_outcome(report, outcome, pqc, pk_bytes)

    # Settlement reference present
    settle_ref = exec_.get("settlement_reference", {})
    report.add("SETTLE-SWIFT", "Settlement reference has SWIFT MT202 ref",
               bool(settle_ref.get("swift_mt202_ref")), path="ADMISSIBLE")
    report.add("SETTLE-XRPL", "Settlement reference has XRPL TxID",
               bool(settle_ref.get("xrpl_tx_id")), path="ADMISSIBLE")
    report.add("SETTLE-AMOUNT", f"Settlement amount = USD 50,000,000",
               settle_ref.get("amount_usd") == 50_000_000, path="ADMISSIBLE")

    # Structural: execution_occurred=True
    summary = p.get("summary", {})
    report.add("SETTLE-EXEC", "admissible path: execution_occurred=True",
               summary.get("execution_occurred") is True, path="ADMISSIBLE")
    report.add("SETTLE-RELEASED", "admissible path: settlement_released=True",
               summary.get("settlement_released") is True, path="ADMISSIBLE")


def verify_replay(report: VerificationReport, pkg: Dict, pqc, pk_bytes: bytes) -> None:
    report.section("REPLAY — Post-execution continuity + TCS (both paths, RTE-INV-006/007)")
    for path_key, path_label, expected_status in [
        ("path_dangerous",  "DANGEROUS",  "HALTED"),
        ("path_admissible", "ADMISSIBLE", "CLOSED"),
    ]:
        p    = pkg["paths"][path_key]
        post = p["steps"]["8_post_execution"]

        tcs  = post.get("temporal_context_snapshot", {})
        _check_tcs(report, tcs, pqc, pk_bytes, path_label)

        proof = post.get("replay_proof", {})
        _check_replay(report, proof, pqc, pk_bytes, path_label, expected_status)


# ─────────────────────────────────────────────────────────────────────────────
#  Package-level structural checks
# ─────────────────────────────────────────────────────────────────────────────

def verify_package_structure(report: VerificationReport, pkg: Dict) -> None:
    report.section("PACKAGE STRUCTURE — RTE-INV-001")
    report.add("PKG-TYPE",   "package_type=OMNIX-RTE-001",
               pkg.get("package_type") == "OMNIX-RTE-001")
    report.add("PKG-PATHS",  "Package contains both dangerous and admissible paths (RTE-INV-001)",
               "path_dangerous" in pkg.get("paths", {}) and "path_admissible" in pkg.get("paths", {}))
    report.add("PKG-PQC",    "Package contains embedded public_key_b64",
               bool(pkg.get("pqc", {}).get("public_key_b64")))
    report.add("PKG-INV",    f"Package declares ≥20 invariants ({len(pkg.get('invariants_demonstrated', []))} found)",
               len(pkg.get("invariants_demonstrated", [])) >= 20)
    report.add("PKG-CHAIN",  "Package has rte_chain_map with 8 steps",
               len(pkg.get("rte_chain_map", {})) == 8)


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="OMNIX-RTE-001 Offline Evidence Package Verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "package", nargs="?", default=None,
        help="Path to OMNIX-RTE-001 JSON package "
             "(optional — auto-detected from evidence/ if omitted)"
    )
    parser.add_argument("--verify-authority",      action="store_true", help="Verify DR + MBR (both paths)")
    parser.add_argument("--verify-continuity",     action="store_true", help="Verify RCR + MAS (both paths)")
    parser.add_argument("--verify-counterfactual", action="store_true", help="Verify CGE CAT + CFRs (both paths)")
    parser.add_argument("--verify-halt",           action="store_true", help="Verify dangerous path HALT chain")
    parser.add_argument("--verify-settlement",     action="store_true", help="Verify admissible path settlement")
    parser.add_argument("--verify-replay",         action="store_true", help="Verify replay proofs + TCS (both paths)")
    parser.add_argument("--json",                  action="store_true", help="Output machine-readable JSON report")
    args = parser.parse_args()

    # Determine mode
    targeted = any([
        args.verify_authority, args.verify_continuity, args.verify_counterfactual,
        args.verify_halt, args.verify_settlement, args.verify_replay,
    ])
    run_all = not targeted

    if run_all:
        mode = "FULL"
    else:
        flags = []
        if args.verify_authority:      flags.append("authority")
        if args.verify_continuity:     flags.append("continuity")
        if args.verify_counterfactual: flags.append("counterfactual")
        if args.verify_halt:           flags.append("halt")
        if args.verify_settlement:     flags.append("settlement")
        if args.verify_replay:         flags.append("replay")
        mode = "+".join(flags).upper()

    # Resolve package path — auto-detect when not provided
    pkg_path = args.package
    if pkg_path is None:
        pkg_path = _auto_detect_package()
        if pkg_path is None:
            print(
                "\n[ERROR] No package path given and no OMNIX-RTE-001_*.json found "
                "in evidence/ or evidence_packages/",
                file=sys.stderr,
            )
            print(
                "        Usage: python verify.py <package.json>  "
                "or place the JSON in evidence/",
                file=sys.stderr,
            )
            return 2
        print(f"[INFO]  Auto-detected package: {os.path.basename(pkg_path)}")

    # Load package
    if not os.path.exists(pkg_path):
        print(f"\n[ERROR] Package file not found: {pkg_path}", file=sys.stderr)
        return 2
    try:
        with open(pkg_path, encoding="utf-8") as f:
            pkg = json.load(f)
    except Exception as e:
        print(f"\n[ERROR] Failed to parse package: {e}", file=sys.stderr)
        return 2

    if pkg.get("package_type") != "OMNIX-RTE-001":
        print(f"\n[ERROR] Not an OMNIX-RTE-001 package (package_type={pkg.get('package_type')})", file=sys.stderr)
        print("        This verifier is for OMNIX-RTE-001 packages only.", file=sys.stderr)
        print("        For RCEP (ADR-200) packages, use: scripts/verify_evidence_package.py", file=sys.stderr)
        return 2

    package_id = pkg.get("package_id", "UNKNOWN")
    report     = VerificationReport(package_id, mode)

    print("=" * 65)
    print("  OMNIX QUANTUM — RTE-001 Offline Verifier")
    print("  RFC-ATF-1 through RFC-ATF-6 · ADR-201")
    print("=" * 65)
    print(f"  Package:  {package_id}")
    print(f"  File:     {pkg_path}")
    print(f"  Mode:     {mode}")
    print(f"  Generated:{pkg.get('generated_at', 'unknown')}")
    print(f"  Scenario: {pkg.get('scenario', {}).get('name', 'unknown')}")
    print(f"  Amount:   USD {pkg.get('scenario', {}).get('amount_usd', 0):,}")

    # Load PQC
    pk_b64     = pkg.get("pqc", {}).get("public_key_b64", "")
    pqc, pk_or_err = _load_pqc(pk_b64)
    if pqc is None:
        print(f"\n[WARN] PQC library not found: {pk_or_err}")
        print("       Signature checks will be SKIPPED — structural and hash checks proceed normally.")
        print("       To enable full verification:  pip install pqc")
        pk_bytes = None
    else:
        pk_bytes = pk_or_err
        print(f"\n  PQC:      {pkg.get('pqc', {}).get('algorithm', 'unknown')} — loaded ✓")

    print()

    # Run structural checks always
    verify_package_structure(report, pkg)

    # Run targeted or all suites
    if run_all or args.verify_authority:
        verify_authority(report, pkg, pqc, pk_bytes)

    if run_all or args.verify_continuity:
        verify_continuity(report, pkg, pqc, pk_bytes)

    if run_all or args.verify_counterfactual:
        verify_counterfactual(report, pkg, pqc, pk_bytes)

    if run_all or args.verify_halt:
        verify_halt(report, pkg, pqc, pk_bytes)

    if run_all or args.verify_settlement:
        verify_settlement(report, pkg, pqc, pk_bytes)

    if run_all or args.verify_replay:
        verify_replay(report, pkg, pqc, pk_bytes)

    # Summary
    all_ok = report.summary()

    if args.json:
        print("\n" + json.dumps(report.to_dict(), indent=2))

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
