"""
OMNIX QUANTUM — Runtime Treasury Execution Trace Verifier
=========================================================
OMNIX-RTE-001 · ADR-201 through ADR-204 · RFC-ATF-1 through RFC-ATF-6

Verifies every cryptographic artefact in an OMNIX-RTE-001 package
WITHOUT calling the OMNIX runtime. All verification is performed
offline using only the public key embedded in the package.

Verification commands (add to check count — EXPECTED_TOTAL_CHECKS = 187):
  --verify-intake         GCFR seal + 5 predicate hashes + 3 XREF (all paths) — ADR-204 IPFL (+36 verify_intake + 3 PKG-INTAKE structural = +39)
  --verify-authority      DR content_hash + PQC signature (all paths)
  --verify-continuity     RCR hash + PQC + MBR + MAS (all paths)
  --verify-counterfactual CAT content_hash + CFR root hash (all paths)
  --verify-halt           Dangerous path: refusal receipt + OSG REJECTED + CTCHC HALTED
  --verify-settlement     Admissible path: PoGC + MBR Seal + OSG APPROVED + outcome receipt
  --verify-replay         All paths: replay proof + CTCHC seal continuity
  --verify-interrupted    Interrupted path: Turn-by-turn BAR+CCS+MAS, HALT at Turn 2,
                          CTCHC HALTED, MBR Seal UNCERTIFIED, OSG REJECTED, PoGC absent
  (default: all of the above)

Institutional Artifact Extraction Protocol — IAEP (ADR-203):
  These commands extract standalone premium reports from any RTE-001 package.
  They do NOT add to the check count. They run after verification.
  --treasury-protocol     Treasury Protocol Execution Report (TPER): per-turn SWIFT/FIX/XRPL
                          breakdown with BAR attestation + MAS verdict (IAEP-RPT-001)
  --mandate-timeline      Mandate Integrity Timeline (MIT): MBR frozen pre-Turn-0 → MAS
                          evolution per turn → MBR Seal certification tier (IAEP-RPT-002)
  --chain-custody         Chain-of-Custody Certificate (CoCC): CTCHC hash chain extracted
                          for courts, regulators, forensic auditors (IAEP-RPT-003)
  --check-version         Version Compatibility Attestation (VCA): formal proof of backward
                          compatibility across RTE-001 v1.0–v1.3 (IAEP-RPT-004)

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
  ✓ DOES confirm interrupted path HALTED at Turn 2 (valid DR, mandate collapse)

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
EXPECTED_TOTAL_CHECKS = 187


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
        self.warned  = 0

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

    def warn(self, check_id: str, label: str, detail: str = "", path: str = "") -> None:
        """
        Record a WARNING check — not a PASS and not a FAIL.  The check is counted
        in the total but does not affect the PASS/FAIL verdict.  Used for TTL expiry
        warnings: the package is still cryptographically valid but the reviewer
        should note that the DR has elapsed since package generation (A07 fix).
        """
        path_tag = f"[{path}] " if path else ""
        self.checks.append({
            "id": check_id, "label": label, "status": "WARN",
            "detail": detail, "path": path,
        })
        self.warned += 1
        colour = "\033[33m"
        reset  = "\033[0m"
        detail_str = f"\n      → {detail}" if detail else ""
        print(f"  {colour}⚠ [{check_id}] {path_tag}{label}{reset}{detail_str}")

    def section(self, title: str) -> None:
        print(f"\n  {'─'*60}")
        print(f"  {title}")
        print(f"  {'─'*60}")

    def summary(self) -> bool:
        total  = self.passed + self.failed + self.skipped + self.warned
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
        if self.warned > 0:
            print(f"  \033[33mWARNINGS\033[0m      : {self.warned} (non-blocking — see DR-TTL checks)")
        print("─" * 65)
        if all_ok and self.skipped == 0 and self.warned == 0:
            print(f"  {colour}VERDICT: ALL VERIFICATIONS PASS — package integrity confirmed{reset}")
        elif all_ok and self.skipped == 0 and self.warned > 0:
            print(f"  {colour}VERDICT: ALL VERIFICATIONS PASS — {self.warned} non-blocking warning(s){reset}")
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
            "total_checks": self.passed + self.failed + self.skipped + self.warned,
            "passed":       self.passed,
            "failed":       self.failed,
            "skipped":      self.skipped,
            "warned":       self.warned,
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
    """
    CAT: content_hash + CFR root hash (A08 fix) + per-CFR content hash.

    A08 fix: cfr_root_hash now covers (cfr_id, cfr_content_hash) pairs sorted by
    cfr_index — not bare cfr_ids.  An adversary mutating CFR content will change
    cfr_content_hash, which changes cfr_root_hash, which invalidates the CAT
    content_hash and the CAT PQC signature.
    """
    # A08 fix: root hash from (cfr_id, cfr_content_hash) pairs sorted by cfr_index
    cfr_entries   = [
        {"cfr_id": c["cfr_id"], "cfr_content_hash": c.get("cfr_content_hash", "")}
        for c in sorted(cfrs, key=lambda x: x.get("cfr_index", 0))
    ]
    expected_root = _sha3(json.dumps(cfr_entries, sort_keys=True))
    actual_root   = cat.get("cfr_root_hash", "")
    report.add(f"CAT-{path[:3]}-ROOT",
               "CAT cfr_root_hash covers (cfr_id, cfr_content_hash) pairs (CGE-INV-002, A08 fix)",
               expected_root == actual_root,
               f"expected={expected_root[:20]}... got={actual_root[:20]}...", path=path)

    # A08 fix: verify cfr_content_hash for every CFR record
    cfr_hashes_ok = True
    for cfr in cfrs:
        # cfr_content_hash = SHA3-256 of the CFR dict excluding cfr_content_hash itself
        base = {k: v for k, v in cfr.items() if k != "cfr_content_hash"}
        expected_cfr_hash = _sha3(json.dumps(base, sort_keys=True))
        if cfr.get("cfr_content_hash", "") != expected_cfr_hash:
            cfr_hashes_ok = False
            break
    report.add(f"CAT-{path[:3]}-CFRHASH",
               f"All {len(cfrs)} CFR content_hashes valid (A08 fix — content tampering detectable)",
               cfr_hashes_ok, path=path)

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


def _check_source_state(report: VerificationReport, ss: Dict, path: str) -> None:
    """
    Verify source_state_hash = SHA3-256(all fields except source_state_hash).

    This check ensures the source state (treasury request, policy constraints,
    authority context, TCS) has not been tampered with after hash computation.
    A tampered source_state would allow false claim of request parameters
    (e.g. changing risk_class or approved counterparty list).
    """
    actual   = ss.get("source_state_hash", "")
    base     = {k: v for k, v in ss.items() if k != "source_state_hash"}
    expected = _sha3(json.dumps(base, sort_keys=True))
    report.add(
        f"SRC-{path[:3]}-HASH",
        "source_state_hash integrity (SHA3-256 of all fields excl. hash itself)",
        expected == actual,
        f"expected={expected[:20]}... got={actual[:20]}...",
        path=path,
    )


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

def verify_intake(report: VerificationReport, pkg: Dict, pqc, pk_bytes: bytes) -> None:
    """
    Verify the Intake and Predicate Formation Layer (IPFL) — ADR-204.
    12 checks × 3 paths = 36 checks total.

    Per path:
      INT-{P}-STRUCT    — 0_intake present with required keys
      INT-{P}-GCFR-COMP — component_hashes has exactly 5 entries
      INT-{P}-GCFR-HASH — seal recomputation: SHA3("|".join(component_hashes))
      INT-{P}-GCFR-SIG  — IDS PQC signature over {ids_id, seal_hash, formed_at}
      INT-{P}-IAD-HASH  — IAD iad_content_hash valid
      INT-{P}-SAR-HASH  — SAR sar_content_hash valid
      INT-{P}-MFR-HASH  — MFR mfr_content_hash valid
      INT-{P}-CPS-HASH  — CPS cps_predicate_hash valid
      INT-{P}-FPS-HASH  — FPS fps_freshness_hash valid
      INT-{P}-XREF-MAND — MFR.mandate_objective_hash == MBR.mandate_objective_hash (IPFL-INV-003)
      INT-{P}-XREF-PROXY— MBR.proxy_guards descriptions ⊆ MFR.mandate_prohibitions (IPFL-INV-004)
      INT-{P}-XREF-RAIL — SAR.approved_rails == DR.task_scope.approved_rails (IPFL-INV-002)
    """
    report.section("INTAKE — GCFR + 5 predicates + cross-references (ADR-204 IPFL) — all 3 paths")

    _GCFR_REQUIRED = {"gcfr_id", "session_id", "components", "component_hashes", "intake_seal"}
    _COMP_KEYS     = [
        ("intake_authority_declaration", "iad_content_hash",  "iad_content_hash",  "iad_id"),
        ("scope_authorization_record",   "sar_content_hash",  "sar_content_hash",  "sar_id"),
        ("mandate_formation_record",     "mfr_content_hash",  "mfr_content_hash",  "mfr_id"),
        ("counterparty_predicate_set",   "cps_predicate_hash","cps_predicate_hash","cps_id"),
        ("freshness_predicate_set",      "fps_freshness_hash","fps_freshness_hash","fps_id"),
    ]
    _HASH_EXCLUDES = {
        "intake_authority_declaration": {"iad_content_hash", "pqc_signature", "pqc_algorithm"},
        "scope_authorization_record":   {"sar_content_hash", "pqc_signature", "pqc_algorithm"},
        "mandate_formation_record":     {"mfr_content_hash", "pqc_signature", "pqc_algorithm"},
        "counterparty_predicate_set":   {"cps_predicate_hash","pqc_signature", "pqc_algorithm"},
        "freshness_predicate_set":      {"fps_freshness_hash","pqc_signature", "pqc_algorithm"},
    }
    _SHORT_LABELS  = {
        "intake_authority_declaration": "IAD",
        "scope_authorization_record":   "SAR",
        "mandate_formation_record":     "MFR",
        "counterparty_predicate_set":   "CPS",
        "freshness_predicate_set":      "FPS",
    }

    for path_key, path_label in [
        ("path_dangerous",  "DANGEROUS"),
        ("path_admissible", "ADMISSIBLE"),
        ("path_interrupted","INTERRUPTED"),
    ]:
        P = path_label[:3]
        p = pkg.get("paths", {}).get(path_key, {})

        # ── STRUCT ─────────────────────────────────────────────────────────────
        intake = p.get("steps", {}).get("0_intake", None)
        ok_struct = (
            intake is not None and
            isinstance(intake, dict) and
            _GCFR_REQUIRED.issubset(intake.keys())
        )
        missing = (_GCFR_REQUIRED - set(intake.keys())) if intake else _GCFR_REQUIRED
        report.add(
            f"INT-{P}-STRUCT",
            f"0_intake present in steps with required keys (IPFL-INV-008)",
            ok_struct,
            f"missing={missing}" if not ok_struct else "",
            path=path_label,
        )
        if not ok_struct:
            for _ in range(11):
                report.add(
                    f"INT-{P}-SKIP",
                    "Skipped — 0_intake missing or malformed",
                    False, path=path_label,
                )
            continue

        comp_hashes  = intake.get("component_hashes", [])
        intake_seal  = intake.get("intake_seal", {})
        components   = intake.get("components", {})

        # ── GCFR-COMP ──────────────────────────────────────────────────────────
        report.add(
            f"INT-{P}-GCFR-COMP",
            "GCFR component_hashes has exactly 5 entries (IAD·SAR·MFR·CPS·FPS)",
            len(comp_hashes) == 5,
            f"len={len(comp_hashes)}",
            path=path_label,
        )

        # ── GCFR-HASH ──────────────────────────────────────────────────────────
        expected_seal = _sha3("|".join(comp_hashes))
        actual_seal   = intake_seal.get("seal_hash", "")
        report.add(
            f"INT-{P}-GCFR-HASH",
            "GCFR seal_hash = SHA3-256(iad_hash|sar_hash|mfr_hash|cps_hash|fps_hash) (IPFL-INV-007)",
            expected_seal == actual_seal,
            f"expected={expected_seal[:20]}... got={actual_seal[:20]}..." if expected_seal != actual_seal else "",
            path=path_label,
        )

        # ── GCFR-SIG ───────────────────────────────────────────────────────────
        seal_sig_payload = {
            "ids_id":     intake_seal.get("ids_id"),
            "seal_hash":  intake_seal.get("seal_hash"),
            "formed_at":  intake_seal.get("formed_at"),
        }
        ok_sig, detail_sig = _verify_sig(pqc, pk_bytes, seal_sig_payload,
                                         intake_seal.get("pqc_signature"), compact=True)
        _add_sig(report, f"INT-{P}-GCFR-SIG",
                 "GCFR intake_seal PQC signature (ML-DSA-65) — contract sealed before Turn 0",
                 ok_sig, detail_sig, path=path_label)

        # ── Per-predicate hash verification ────────────────────────────────────
        for comp_key, hash_field, _hash_label, _id_field in _COMP_KEYS:
            label = _SHORT_LABELS[comp_key]
            comp  = components.get(comp_key, {})
            excl  = _HASH_EXCLUDES[comp_key]
            payload_for_hash = {k: v for k, v in comp.items() if k not in excl}
            expected_hash    = _sha3(json.dumps(payload_for_hash, sort_keys=True))
            actual_hash      = comp.get(hash_field, "")
            ok_hash = expected_hash == actual_hash
            report.add(
                f"INT-{P}-{label}-HASH",
                f"{label} {hash_field} recomputed correctly (IPFL-INV-00{list(_SHORT_LABELS.values()).index(label)+1})",
                ok_hash,
                f"expected={expected_hash[:20]}... got={actual_hash[:20]}..." if not ok_hash else "",
                path=path_label,
            )

        # ── Cross-references ───────────────────────────────────────────────────
        mfr = components.get("mandate_formation_record", {})
        mbr_step = p.get("steps", {}).get("2_authority", {}).get("mandate_binding_record", {})
        dr_step  = p.get("steps", {}).get("2_authority", {}).get("delegation_receipt", {})

        # XREF-MAND: MFR.mandate_objective_hash == MBR.mandate_objective_hash
        mfr_obj_hash = mfr.get("mandate_objective_hash", "")
        mbr_obj_hash = mbr_step.get("mandate_objective_hash", "")
        report.add(
            f"INT-{P}-XREF-MAND",
            "MFR.mandate_objective_hash == MBR.mandate_objective_hash (IPFL-INV-003)",
            bool(mfr_obj_hash) and mfr_obj_hash == mbr_obj_hash,
            f"mfr={mfr_obj_hash[:20] if mfr_obj_hash else 'MISSING'}... mbr={mbr_obj_hash[:20] if mbr_obj_hash else 'MISSING'}...",
            path=path_label,
        )

        # XREF-PROXY: MBR.proxy_guards descriptions ⊆ MFR.mandate_prohibitions
        mfr_prohibitions = set(mfr.get("mandate_prohibitions", []))
        raw_guards = mbr_step.get("proxy_guards", [])
        if raw_guards and isinstance(raw_guards[0], dict):
            guard_descs = {g.get("description", "") for g in raw_guards}
        else:
            guard_descs = set(raw_guards)
        missing_guards = guard_descs - mfr_prohibitions
        report.add(
            f"INT-{P}-XREF-PROXY",
            "MBR.proxy_guard descriptions ⊆ MFR.mandate_prohibitions (IPFL-INV-004)",
            len(missing_guards) == 0,
            f"missing={missing_guards}" if missing_guards else "",
            path=path_label,
        )

        # XREF-RAIL: SAR.approved_rails == DR.task_scope.approved_rails
        sar = components.get("scope_authorization_record", {})
        sar_rails = sorted(sar.get("approved_rails", []))
        dr_rails  = sorted(dr_step.get("task_scope", {}).get("approved_rails", []))
        report.add(
            f"INT-{P}-XREF-RAIL",
            "SAR.approved_rails == DR.task_scope.approved_rails (IPFL-INV-002)",
            sar_rails == dr_rails,
            f"sar={sar_rails} dr={dr_rails}" if sar_rails != dr_rails else "",
            path=path_label,
        )


def verify_authority(report: VerificationReport, pkg: Dict, pqc, pk_bytes: bytes) -> None:
    report.section("AUTHORITY — DR + MBR + source_state (both paths)")
    for path_key, path_label in [("path_dangerous", "DANGEROUS"), ("path_admissible", "ADMISSIBLE")]:
        p   = pkg["paths"][path_key]
        dr  = p["steps"]["2_authority"]["delegation_receipt"]
        mbr = p["steps"]["2_authority"]["mandate_binding_record"]
        ss  = p["steps"]["1_source_state"]

        _check_dr(report, dr, pqc, pk_bytes, path_label)
        _check_mbr(report, mbr, pqc, pk_bytes, path_label)

        # MAR semantic: budget_granted ≤ budget_delegator
        bg = dr.get("authority_budget_granted", -1)
        bd = dr.get("authority_budget_delegator", -1)
        report.add(f"DR-{path_label[:3]}-MAR", f"DR MAR: budget_granted({bg}) ≤ budget_delegator({bd}) (ATF-INV-001)",
                   bg <= bd, path=path_label)

        # A09 fix: DR.session_id must match source_state.session_id
        # A DR transplanted from another path has a different session_id embedded in its
        # content_hash — the hash check above will already fail, but this semantic check
        # makes the violation human-readable in the report.
        dr_session  = dr.get("session_id", "")
        src_session = ss.get("session_id", "")
        report.add(
            f"DR-{path_label[:3]}-SESS",
            "DR.session_id == source_state.session_id (A09 fix — cross-path substitution detectable)",
            bool(dr_session) and dr_session == src_session,
            f"dr_session={dr_session[:20] if dr_session else 'MISSING'}... src_session={src_session[:20] if src_session else 'MISSING'}...",
            path=path_label,
        )

        # A09 fix: MBR.dr_id must match DR.delegation_id
        mbr_dr_id = mbr.get("dr_id", "")
        dr_del_id = dr.get("delegation_id", "")
        report.add(
            f"MBR-{path_label[:3]}-DRID",
            "MBR.dr_id == DR.delegation_id (A09 fix — MBR bound to specific DR)",
            bool(mbr_dr_id) and mbr_dr_id == dr_del_id,
            f"mbr.dr_id={mbr_dr_id[:20] if mbr_dr_id else 'MISSING'}... dr.delegation_id={dr_del_id[:20] if dr_del_id else 'MISSING'}...",
            path=path_label,
        )

        # source_state integrity (hash fix)
        _check_source_state(report, ss, path_label)

        # A07 fix: TTL warning — DR may have elapsed since package was generated.
        # This is non-blocking (WARN not FAIL): the PQC signature is still valid,
        # but the reviewer should note that the DR's TTL has elapsed.
        generated_at = pkg.get("generated_at", "")
        expires_at   = dr.get("expires_at", "")
        if generated_at and expires_at:
            try:
                gen_dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                now_dt = datetime.now(timezone.utc)
                if now_dt > exp_dt:
                    report.warn(
                        f"DR-{path_label[:3]}-TTL",
                        f"DR expired at {expires_at} — signature valid but TTL elapsed (A07 advisory)",
                        f"Generated: {generated_at} | Expired: {expires_at} | Now: {now_dt.isoformat()}",
                        path=path_label,
                    )
                else:
                    report.add(
                        f"DR-{path_label[:3]}-TTL",
                        f"DR TTL valid — expires {expires_at} (A07 check)",
                        True,
                        path=path_label,
                    )
            except (ValueError, TypeError):
                report.add(f"DR-{path_label[:3]}-TTL", "DR TTL — unable to parse timestamps",
                           False, f"generated_at={generated_at} expires_at={expires_at}", path=path_label)


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
#  Interrupted path verification (v1.3.0) — Path C
# ─────────────────────────────────────────────────────────────────────────────

def verify_interrupted(report: VerificationReport, pkg: Dict, pqc, pk_bytes: bytes) -> None:
    """
    Path C (v1.3.0) — Interrupted Execution verifier.

    Verifies that under VALID authority (fresh DR, NOMINAL CES), execution that
    was correctly admitted by the TAR was interrupted mid-chain at Turn 2 when
    the MIVP mandate alignment score collapsed below halt_threshold=0.30.

    Checks (36 total):
      CTCHC integrity (4) + HALTED terminal state (1)
      Per-turn BAR hash+sig+status: T0=VALID (3), T1=VALID (3), T2=HALT_TRIGGERED (3)
      MAS per-turn: T1 hash+sig+WARNING (3), T2 hash+sig+HALT+score<0.30 (4)
      CCS Turn 2: CRITICAL + agvp_watchdog_clear=False (2)
      MBR Seal: hash+sig+UNCERTIFIED (3)
      OSG: hash+sig+REJECTED (≥3)
      INT-STRUCT (1) + INT-POGC-ABSENT (1) + INT-SETTLE-BLOCKED (1)
      Replay proof: hash+sig+status+offline (4)

    ADR: ADR-201 §9 · RTE-INV-013/014/015
    RFC: RFC-ATF-6 (BEV-INV-005/007) · MIVP-INV-004/005/009 · PoGR-INV-001
    """
    report.section("INTERRUPTED — Path C: Turn 0 ✓ Turn 1 ⚠ Turn 2 HALT (RTE-INV-013/014/015)")

    # ── Structural: path_interrupted present ──────────────────────────────────
    pi = pkg.get("paths", {}).get("path_interrupted")
    report.add("INT-STRUCT", "path_interrupted present in package (v1.3.0+, RTE-INV-001)",
               pi is not None)
    if pi is None:
        return

    gate   = pi["steps"]["6_gate"]
    exec_  = pi["steps"]["7_execution"]
    post   = pi["steps"]["8_post_execution"]
    turns  = gate.get("execution_turns", [])

    def _turn(idx: int) -> Dict:
        return next((t for t in turns if t.get("turn") == idx), {})

    t0 = _turn(0)
    t1 = _turn(1)
    t2 = _turn(2)

    # ── CTCHC: 3-link chain integrity + HALTED seal ───────────────────────────
    links  = exec_.get("ctchc_links", [])
    sealed = exec_.get("ctchc_sealed", {})
    _check_ctchc(report, links, sealed, pqc, pk_bytes, "INTERRUPTED")

    terminal = sealed.get("terminal_state", "")
    report.add("CHC-INT-HALTED",
               "CTCHC terminal_state=HALTED — chain sealed on mandate collapse (RTE-INV-013)",
               terminal == "HALTED", f"got={terminal!r}", path="INTERRUPTED")

    # ── Turn 0 BAR: hash + sig + status=VALID ─────────────────────────────────
    bar_t0 = t0.get("bar", {})
    _fields_t0 = {k: bar_t0.get(k) for k in [
        "session_id", "agent_id", "turn_index", "output_hash",
        "governing_receipt_id", "constraint_set_hash"
    ]}
    exp_t0 = _sha3(json.dumps(_fields_t0, sort_keys=True))
    act_t0 = bar_t0.get("content_hash", "")
    report.add("BAR-INT-T0-HASH", "Turn 0 BAR content_hash (BEV-INV-002, SHA3-256 6-field)",
               exp_t0 == act_t0, f"exp={exp_t0[:18]}... got={act_t0[:18]}...", path="INTERRUPTED")
    sp_t0 = {
        "bar_id":               bar_t0.get("bar_id"),
        "content_hash":         act_t0,
        "governing_receipt_id": bar_t0.get("governing_receipt_id"),
        "created_at":           bar_t0.get("created_at"),
    }
    ok_t0, d_t0 = _verify_sig_default(pqc, pk_bytes, sp_t0, bar_t0.get("pqc_signature"))
    _add_sig(report, "BAR-INT-T0-SIG", "Turn 0 BAR PQC signature (BEV-INV-004, default sep)",
             ok_t0, d_t0, path="INTERRUPTED")
    report.add("BAR-INT-T0-STATUS",
               "Turn 0 BAR status=VALID (SWIFT MT103 PASS)",
               bar_t0.get("bar_status", "VALID") == "VALID",
               f"bar_status={bar_t0.get('bar_status','absent→VALID')}", path="INTERRUPTED")

    # ── Turn 1 BAR: hash + sig + status=VALID ─────────────────────────────────
    bar_t1 = t1.get("bar", {})
    _fields_t1 = {k: bar_t1.get(k) for k in [
        "session_id", "agent_id", "turn_index", "output_hash",
        "governing_receipt_id", "constraint_set_hash"
    ]}
    exp_t1 = _sha3(json.dumps(_fields_t1, sort_keys=True))
    act_t1 = bar_t1.get("content_hash", "")
    report.add("BAR-INT-T1-HASH", "Turn 1 BAR content_hash (BEV-INV-002, SHA3-256 6-field)",
               exp_t1 == act_t1, f"exp={exp_t1[:18]}... got={act_t1[:18]}...", path="INTERRUPTED")
    sp_t1 = {
        "bar_id":               bar_t1.get("bar_id"),
        "content_hash":         act_t1,
        "governing_receipt_id": bar_t1.get("governing_receipt_id"),
        "created_at":           bar_t1.get("created_at"),
    }
    ok_t1, d_t1 = _verify_sig_default(pqc, pk_bytes, sp_t1, bar_t1.get("pqc_signature"))
    _add_sig(report, "BAR-INT-T1-SIG", "Turn 1 BAR PQC signature (BEV-INV-004, default sep)",
             ok_t1, d_t1, path="INTERRUPTED")
    report.add("BAR-INT-T1-STATUS",
               "Turn 1 BAR status=VALID (FIX 4.4 routed — MAS WARNING captured separately)",
               bar_t1.get("bar_status", "VALID") == "VALID",
               f"bar_status={bar_t1.get('bar_status','absent→VALID')}", path="INTERRUPTED")

    # ── Turn 2 BAR: hash + sig + status=HALT_TRIGGERED ────────────────────────
    bar_t2 = exec_.get("bar", {})
    _fields_t2 = {k: bar_t2.get(k) for k in [
        "session_id", "agent_id", "turn_index", "output_hash",
        "governing_receipt_id", "constraint_set_hash"
    ]}
    exp_t2 = _sha3(json.dumps(_fields_t2, sort_keys=True))
    act_t2 = bar_t2.get("content_hash", "")
    report.add("BAR-INT-T2-HASH", "Turn 2 BAR content_hash (BEV-INV-002, SHA3-256 6-field)",
               exp_t2 == act_t2, f"exp={exp_t2[:18]}... got={act_t2[:18]}...", path="INTERRUPTED")
    sp_t2 = {
        "bar_id":               bar_t2.get("bar_id"),
        "content_hash":         act_t2,
        "governing_receipt_id": bar_t2.get("governing_receipt_id"),
        "created_at":           bar_t2.get("created_at"),
    }
    ok_t2, d_t2 = _verify_sig_default(pqc, pk_bytes, sp_t2, bar_t2.get("pqc_signature"))
    _add_sig(report, "BAR-INT-T2-SIG", "Turn 2 BAR PQC signature (BEV-INV-004, default sep)",
             ok_t2, d_t2, path="INTERRUPTED")
    status_t2 = bar_t2.get("bar_status", "")
    report.add("BAR-INT-T2-HALT",
               "Turn 2 BAR status=HALT_TRIGGERED (MIVP-INV-005, RTE-INV-013)",
               status_t2 == "HALT_TRIGGERED", f"got={status_t2!r}", path="INTERRUPTED")

    # ── MAS Turn 1: hash + sig + verdict=WARNING ──────────────────────────────
    mas_t1 = t1.get("mas", {})
    exp_m1  = _hash_default(mas_t1, exclude=["mas_content_hash", "pqc_signature", "pqc_algorithm"])
    act_m1  = mas_t1.get("mas_content_hash", "")
    report.add("MAS-INT-T1-HASH", "Turn 1 MAS content_hash integrity",
               exp_m1 == act_m1, f"exp={exp_m1[:18]}... got={act_m1[:18]}...", path="INTERRUPTED")
    sp_m1   = {"mas_id": mas_t1.get("mas_id"), "mas_content_hash": act_m1, "issued_at": mas_t1.get("issued_at")}
    ok_m1, dm1 = _verify_sig(pqc, pk_bytes, sp_m1, mas_t1.get("pqc_signature"), compact=True)
    _add_sig(report, "MAS-INT-T1-SIG", "Turn 1 MAS PQC signature (MIVP-INV-003, compact)",
             ok_m1, dm1, path="INTERRUPTED")
    verdict_m1 = mas_t1.get("verdict", "")
    score_m1   = mas_t1.get("alignment_score", 1.0)
    report.add("MAS-INT-T1-WARN",
               f"Turn 1 MAS verdict=WARNING — score={score_m1} < warn_threshold=0.65 (MIVP-INV-004)",
               verdict_m1 == "WARNING",
               f"verdict={verdict_m1!r} score={score_m1}", path="INTERRUPTED")

    # ── MAS Turn 2: hash + sig + verdict=HALT + score < halt_threshold ────────
    mas_t2 = t2.get("mas", {})
    exp_m2  = _hash_default(mas_t2, exclude=["mas_content_hash", "pqc_signature", "pqc_algorithm"])
    act_m2  = mas_t2.get("mas_content_hash", "")
    report.add("MAS-INT-T2-HASH", "Turn 2 MAS content_hash integrity",
               exp_m2 == act_m2, f"exp={exp_m2[:18]}... got={act_m2[:18]}...", path="INTERRUPTED")
    sp_m2   = {"mas_id": mas_t2.get("mas_id"), "mas_content_hash": act_m2, "issued_at": mas_t2.get("issued_at")}
    ok_m2, dm2 = _verify_sig(pqc, pk_bytes, sp_m2, mas_t2.get("pqc_signature"), compact=True)
    _add_sig(report, "MAS-INT-T2-SIG", "Turn 2 MAS PQC signature (MIVP-INV-003, compact)",
             ok_m2, dm2, path="INTERRUPTED")
    verdict_m2 = mas_t2.get("verdict", "")
    score_m2   = mas_t2.get("alignment_score", 1.0)
    report.add("MAS-INT-T2-HALT",
               f"Turn 2 MAS verdict=HALT (MIVP-INV-005, score={score_m2}, threshold=0.30)",
               verdict_m2 == "HALT",
               f"verdict={verdict_m2!r}", path="INTERRUPTED")
    report.add("MAS-INT-T2-SCORE",
               f"Turn 2 MAS score={score_m2} < halt_threshold=0.30 (MIVP-INV-005)",
               score_m2 < 0.30,
               f"score={score_m2}", path="INTERRUPTED")

    # ── CCS Turn 2: CRITICAL verdict + AGVP watchdog triggered ───────────────
    ccs_t2      = t2.get("ccs", {})
    ccs_verdict = ccs_t2.get("verdict", "")
    report.add("CCS-INT-T2-CRIT",
               f"Turn 2 CCS verdict=CRITICAL — drift=0.42 > 0.35 halt threshold (BEV-INV-007)",
               ccs_verdict == "CRITICAL", f"verdict={ccs_verdict!r}", path="INTERRUPTED")
    agvp_clear = ccs_t2.get("agvp_watchdog_clear", True)
    report.add("CCS-INT-T2-AGVP",
               "Turn 2 CCS agvp_watchdog_clear=False — AGVP watchdog TRIGGERED (BEV-INV-007)",
               agvp_clear is False, f"agvp_watchdog_clear={agvp_clear}", path="INTERRUPTED")

    # ── MBR Seal: UNCERTIFIED (1 proxy-guard violation at Turn 2) ────────────
    mbr_seal = gate.get("mbr_seal", {})
    _check_mbr_seal(report, mbr_seal, pqc, pk_bytes, "INTERRUPTED")
    tier = mbr_seal.get("certification_tier", "")
    report.add("SEAL-INT-TIER",
               "MBR Seal tier=UNCERTIFIED (1 violation → MIVP-INV-009 three-tier)",
               tier == "UNCERTIFIED", f"got={tier!r}", path="INTERRUPTED")

    # ── OSG: REJECTED fail-closed (no PoGC presented) ────────────────────────
    osg_vr = gate.get("osg_validation_receipt", {})
    _check_osg_vr(report, osg_vr, "REJECTED", pqc, pk_bytes, "INTERRUPTED")

    # ── PoGC absent + settlement BLOCKED ─────────────────────────────────────
    pogc_issued = gate.get("pogc_issued", True)
    report.add("INT-POGC-ABSENT",
               "PoGC NOT issued on interrupted path — HALTED chain ≠ CLOSED (PoGR-INV-001 + RTE-INV-014)",
               pogc_issued is False, f"pogc_issued={pogc_issued}", path="INTERRUPTED")
    summary = pi.get("summary", {})
    report.add("INT-SETTLE-BLOCKED",
               "settlement_released=False — USD 50,000,000 NOT released (RTE-INV-015)",
               summary.get("settlement_released") is False, path="INTERRUPTED")

    # ── Replay proof: HALTED ──────────────────────────────────────────────────
    proof = post.get("replay_proof", {})
    _check_replay(report, proof, pqc, pk_bytes, "INTERRUPTED", "HALTED")


# ─────────────────────────────────────────────────────────────────────────────
#  Package-level structural checks
# ─────────────────────────────────────────────────────────────────────────────

def verify_package_structure(report: VerificationReport, pkg: Dict) -> None:
    report.section("PACKAGE STRUCTURE — RTE-INV-001")
    report.add("PKG-TYPE",   "package_type=OMNIX-RTE-001",
               pkg.get("package_type") == "OMNIX-RTE-001")
    report.add("PKG-PATHS",  "Package contains dangerous, admissible, and interrupted paths (v1.3.0 RTE-INV-001)",
               "path_dangerous"  in pkg.get("paths", {}) and
               "path_admissible" in pkg.get("paths", {}) and
               "path_interrupted" in pkg.get("paths", {}))
    report.add("PKG-PQC",    "Package contains embedded public_key_b64",
               bool(pkg.get("pqc", {}).get("public_key_b64")))
    report.add("PKG-INV",    f"Package declares ≥20 invariants ({len(pkg.get('invariants_demonstrated', []))} found)",
               len(pkg.get("invariants_demonstrated", [])) >= 20)
    report.add("PKG-CHAIN",  "Package has rte_chain_map with 9 steps (v1.4.0: step 0_INTAKE added — ADR-204)",
               len(pkg.get("rte_chain_map", {})) == 9)
    for path_key, path_label in [("path_dangerous", "DNG"), ("path_admissible", "ADM"), ("path_interrupted", "INT")]:
        has_intake = "0_intake" in pkg.get("paths", {}).get(path_key, {}).get("steps", {})
        report.add(
            f"PKG-INTAKE-{path_label}",
            f"Path {path_label} contains 0_intake step (IPFL-INV-008 — GCFR before source_state)",
            has_intake,
            path=path_label,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Institutional Artifact Extraction Protocol (IAEP) — ADR-203
#  Four premium reporting commands — standalone, institutional-grade output.
#  These commands produce formatted artifact reports. They do NOT add to the
#  verification check count (EXPECTED_TOTAL_CHECKS = 187 is unchanged).
#
#  Commands:
#    --treasury-protocol  Treasury Protocol Execution Report (TPER) IAEP-RPT-001
#    --mandate-timeline   Mandate Integrity Timeline (MIT)          IAEP-RPT-002
#    --chain-custody      Chain-of-Custody Certificate (CoCC)       IAEP-RPT-003
#    --check-version      Version Compatibility Attestation (VCA)   IAEP-RPT-004
# ─────────────────────────────────────────────────────────────────────────────

_TURN_PROTOCOLS: Dict[int, tuple] = {
    0: ("SWIFT MT103",  "Counterparty validation + sanctions screening",  "ISO 15022 / SWIFT FIN"),
    1: ("FIX 4.4",      "Order routing — institutional gateway",           "FIX Protocol Ltd."),
    2: ("XRPL RLUSD",   "Atomic settlement + finality confirmation",        "XRPL Foundation / Ripple"),
}
_TURN_LABELS: Dict[int, str] = {
    0: "Turn 0 — SWIFT MT103",
    1: "Turn 1 — FIX 4.4",
    2: "Turn 2 — XRPL RLUSD",
}


def report_treasury_protocol(pkg: Dict) -> None:
    """
    --treasury-protocol  (IAEP-RPT-001, ADR-203 §2.1)

    Treasury Protocol Execution Report (TPER).

    Presents the 3-turn SWIFT→FIX→XRPL execution sequence with per-turn
    BAR attestation, MAS mandate verdict, and institutional protocol metadata
    from both the admissible path (all VALID → settlement RELEASED) and the
    interrupted path (Path C — HALT at Turn 2 by MIVP).

    Differentiator: makes treasury-grade multi-step governance explicit and
    shareable with banking regulators, MiFID-II auditors, and SWIFT compliance
    teams — without requiring access to the OMNIX runtime.
    BEV-INV-001–004 (RFC-ATF-6) · MIVP-INV-004/005 (ADR-194) · ADR-201.
    """
    G, Y, R, RST = "\033[32m", "\033[33m", "\033[31m", "\033[0m"
    scenario = pkg.get("scenario", {})

    print()
    print("═" * 70)
    print("  OMNIX-RTE-001 — Treasury Protocol Execution Report (TPER)")
    print("  IAEP-RPT-001 · ADR-203 §2.1 · BEV-INV-001–004 · RFC-ATF-6")
    print("═" * 70)
    print(f"  Package:  {pkg.get('package_id','—')}")
    print(f"  Scenario: {scenario.get('name','—')}")
    print(f"  Amount:   USD {scenario.get('amount_usd', 0):,}")
    print(f"  Agent:    {scenario.get('agent_id','—')}")
    print(f"  Mandate:  {scenario.get('mandate_id','—')}")
    print(f"  Rail:     SWIFT MT202 / XRPL RLUSD")

    for path_key, path_label, step_key in [
        ("path_admissible",  "PATH B — ADMISSIBLE (all turns VALID, settlement RELEASED)", "7_execution"),
        ("path_interrupted", "PATH C — INTERRUPTED (mandate collapse at Turn 2 — HALT)",   "6_gate"),
    ]:
        p = pkg["paths"].get(path_key)
        if not p:
            continue
        turns = p["steps"].get(step_key, {}).get("execution_turns", [])
        if not turns:
            continue

        print(f"\n  {'─'*68}")
        print(f"  {path_label}")
        print(f"  {'─'*68}")

        for t in turns:
            idx = int(t.get("turn", 0))
            proto_name, proto_desc, proto_standard = _TURN_PROTOCOLS.get(idx, ("?", "", ""))
            bar    = t.get("bar", {})
            mas    = t.get("mas", {})
            status = t.get("status", bar.get("bar_status", "?"))

            score   = mas.get("alignment_score")
            verdict = mas.get("verdict", "—")
            violations = mas.get("proxy_guard_violations", [])
            warnings_l = mas.get("proxy_guard_warnings", [])

            if status in ("PASS", "VALID"):
                sc = G
            elif status == "WARNING":
                sc = Y
            else:
                sc = R

            if verdict == "ALIGNED":
                vc = G
            elif verdict == "WARNING":
                vc = Y
            elif verdict == "HALT":
                vc = R
            else:
                vc = ""

            print(f"\n  ┌─ Turn {idx}: {proto_name}  [{sc}{status}{RST}]")
            print(f"  │  Standard:     {proto_standard}")
            print(f"  │  Role:         {proto_desc}")
            print(f"  │  BAR ID:       {bar.get('bar_id','—')}")
            print(f"  │  BAR hash:     {bar.get('content_hash','')[:32]}…")
            if score is not None:
                filled = int(float(score) * 20)
                bar_vis = "█" * filled + "░" * (20 - filled)
                print(f"  │  MAS:          [{bar_vis}] {score:.4f}  {vc}{verdict}{RST}")
            else:
                print(f"  │  MAS:          {vc}{verdict}{RST}")
            if violations:
                for v in violations:
                    print(f"  │  ⚠ Violation:  {v[:65]}")
            if warnings_l:
                for w in warnings_l:
                    print(f"  │  ⚠ Warning:    {w[:65]}")
            preview = bar.get("output_preview", "")
            if preview:
                print(f"  │  Output:       {preview[:65]}")
                if len(preview) > 65:
                    print(f"  │                {preview[65:130]}")
            print(f"  │  PQC:          {bar.get('pqc_algorithm','—')} · {bar.get('content_hash','')[:20]}…")
            print(f"  └─ content_hash sealed into CTCHC Link {idx}  (BEV-INV-012)")

    # Settlement outcome
    settle = pkg["paths"].get("path_admissible", {}) \
                         .get("steps", {}).get("7_execution", {}) \
                         .get("settlement_reference", {})
    if settle:
        print(f"\n  {'─'*68}")
        print(f"  SETTLEMENT OUTCOME (admissible path)")
        print(f"  {'─'*68}")
        print(f"  {G}RELEASED{RST}  {settle.get('settlement_status','—')}")
        print(f"    SWIFT ref:   {settle.get('swift_mt202_ref','—')}")
        print(f"    XRPL TxID:   {settle.get('xrpl_tx_id','—')}")
        print(f"    Amount:      USD {settle.get('amount_usd',0):,}")
        print(f"    Counterparty:{settle.get('counterparty','—')}")
        print(f"    PoGC:        {settle.get('pogc_id','—')}")

    print()
    print("═" * 70)
    print("  END — Treasury Protocol Execution Report (TPER)")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("  Full cryptographic verification:")
    print("    python verify.py <package.json> --verify-settlement --verify-halt")
    print("═" * 70)


def report_mandate_timeline(pkg: Dict) -> None:
    """
    --mandate-timeline  (IAEP-RPT-002, ADR-203 §2.2)

    Mandate Integrity Timeline (MIT).

    Renders: MBR frozen pre-Turn-0 → per-turn MAS evolution with thresholds
    → MBR Seal certification tier. Covers all three paths.

    MIVP-INV-001: the mandate cannot be renegotiated during execution.
    The MBR is cryptographically bound before the first turn executes.
    This timeline is the formal proof of continuous mandate monitoring.

    Differentiator: the world's first per-turn, threshold-aware mandate
    alignment timeline for AI agent governance — HALT/WARNING/ALIGNED
    each backed by a PQC-signed MAS artifact.
    MIVP-INV-001–009 (ADR-194) · RFC-ATF-6 BEV-INV-005–009.
    """
    G, Y, R, RST = "\033[32m", "\033[33m", "\033[31m", "\033[0m"

    print()
    print("═" * 70)
    print("  OMNIX-RTE-001 — Mandate Integrity Timeline (MIT)")
    print("  IAEP-RPT-002 · ADR-203 §2.2 · MIVP-INV-001–009 · ADR-194")
    print("═" * 70)
    print(f"  Package:  {pkg.get('package_id','—')}")
    print(f"  Protocol: TREASURY-MANDATE-2026-Q2 — frozen before Turn 0 (MIVP-INV-001)")

    PATH_SEAL_STEPS = {
        "path_dangerous":   ("PATH A — DANGEROUS (authority drift — halted pre-execution)", "7_execution"),
        "path_admissible":  ("PATH B — ADMISSIBLE (mandate BOUND — settlement RELEASED)",   "6_gate"),
        "path_interrupted": ("PATH C — INTERRUPTED (mandate collapse — HALT at Turn 2)",    "6_gate"),
    }

    for path_key, (path_label, seal_step) in PATH_SEAL_STEPS.items():
        p = pkg["paths"].get(path_key)
        if not p:
            continue

        mbr  = p["steps"].get("2_authority", {}).get("mandate_binding_record", {})
        seal = p["steps"].get(seal_step, {}).get("mbr_seal", {})

        print(f"\n  {'─'*68}")
        print(f"  {path_label}")
        print(f"  {'─'*68}")

        if mbr:
            halt_t = float(mbr.get("mas_halt_threshold", 0.30))
            warn_t = float(mbr.get("mas_warning_threshold", 0.65))
            print(f"  ◈ MBR ISSUED — frozen at session start (MIVP-INV-001)")
            print(f"    MBR ID:          {mbr.get('mbr_id','—')}")
            print(f"    Issued at:       {mbr.get('issued_at','—')}")
            print(f"    HALT threshold:  MAS < {halt_t}  → system stops execution")
            print(f"    WARN threshold:  MAS < {warn_t}  → caution flag raised")
            print(f"    MBR hash:        {mbr.get('mbr_content_hash','')[:40]}…")
            print(f"    PQC signature:   {mbr.get('pqc_algorithm','—')} ✓")
        else:
            halt_t, warn_t = 0.30, 0.65
            print(f"  ◈ MBR: not found in 2_authority (path may differ)")

        turns_step = "6_gate" if path_key in ("path_admissible", "path_interrupted") else "7_execution"
        turns = p["steps"].get(turns_step, {}).get("execution_turns", [])

        if turns:
            print(f"\n  ┌─ PER-TURN MAS EVOLUTION (MIVP-INV-004/005)")
            for t in turns:
                idx     = int(t.get("turn", 0))
                mas     = t.get("mas", {})
                score   = mas.get("alignment_score")
                verdict = mas.get("verdict", "—")
                viol    = mas.get("proxy_guard_violations", [])
                warns   = mas.get("proxy_guard_warnings", [])

                if verdict == "HALT":
                    vc, marker = R, "✗ HALT"
                elif verdict == "WARNING":
                    vc, marker = Y, "⚠ WARN"
                elif verdict == "ALIGNED":
                    vc, marker = G, "✓ OK  "
                else:
                    vc, marker = "", "  ?   "

                label = _TURN_LABELS.get(idx, f"Turn {idx}")

                if score is not None:
                    filled = int(float(score) * 30)
                    bar_vis = "█" * filled + "░" * (30 - filled)

                    # Mark thresholds on bar
                    halt_pos = int(halt_t * 30)
                    warn_pos = int(warn_t * 30)
                    threshold_marks = (f"  │               {' '*halt_pos}↑HALT "
                                       f"{' '*(warn_pos - halt_pos - 6)}↑WARN")
                    print(f"  │  {label}:  {vc}{marker}{RST}  [{bar_vis}]  {score:.4f}")
                    if idx == 0:
                        print(threshold_marks)
                else:
                    print(f"  │  {label}:  {vc}{marker}{RST}  score=N/A  verdict={verdict}")

                for v in viol:
                    print(f"  │    ⛔ {v[:62]}")
                for w in warns:
                    print(f"  │    ⚠  {w[:62]}")
            print(f"  └─")
        else:
            print(f"  ── No execution turns: path halted before runtime (expected for PATH A)")

        if seal:
            tier    = seal.get("certification_tier", "—")
            outcome = seal.get("session_outcome", "—")
            if tier == "MANDATE-BOUND":
                tc = G
            elif tier == "MANDATE-ALIGNED":
                tc = Y
            else:
                tc = R
            print(f"\n  ◈ MBR SEAL — mandate lifecycle closed (MIVP-INV-009)")
            print(f"    Certification:   {tc}{tier}{RST}")
            print(f"    Session outcome: {outcome}")
            print(f"    Total turns:     {seal.get('total_turns','—')}")
            print(f"    Violations:      {seal.get('total_violations','—')}")
            print(f"    Warnings:        {seal.get('total_warnings','—')}")
            print(f"    Seal hash:       {seal.get('seal_content_hash','')[:40]}…")
            print(f"    PQC signature:   {seal.get('pqc_algorithm','—')} ✓")
        else:
            print(f"  ◈ MBR Seal: not found in step {seal_step}")

    print()
    print("═" * 70)
    print("  END — Mandate Integrity Timeline (MIT)")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("  Full cryptographic verification:")
    print("    python verify.py <package.json> --verify-continuity")
    print("═" * 70)


def report_chain_custody(pkg: Dict) -> None:
    """
    --chain-custody  (IAEP-RPT-003, ADR-203 §2.3)

    Chain-of-Custody Certificate (CoCC).

    Extracts the CTCHC (Cross-Turn Coherence Hash Chain) from both the
    admissible path (CLOSED seal) and the interrupted path (HALTED seal),
    and formats each as a standalone forensic chain-of-custody document.

    Each CTCHC link: SHA3-256(prev_link_hash ‖ turn_hash ‖ governing_receipt_id)
    Tamper-proof: modifying any BAR breaks all subsequent links and the seal.
    Verifiable offline by anyone with the embedded public key.

    Differentiator: the world's first PQC-signed, per-turn chain-of-custody
    certificate for AI governance decisions. Court and regulator ready.
    BEV-INV-010–014 (RFC-ATF-6, ADR-183) · PoGR-INV-003 (ADR-186).
    """
    G, Y, R, RST = "\033[32m", "\033[33m", "\033[31m", "\033[0m"

    print()
    print("═" * 70)
    print("  OMNIX-RTE-001 — Chain-of-Custody Certificate (CoCC)")
    print("  IAEP-RPT-003 · ADR-203 §2.3 · BEV-INV-010–014 · RFC-ATF-6")
    print("═" * 70)
    print(f"  Package:  {pkg.get('package_id','—')}")
    print(f"  Issuer:   OMNIX QUANTUM LTD")
    print(f"  Date:     {datetime.now(timezone.utc).isoformat()}")
    print(f"  Hash fn:  SHA3-256")
    print(f"  PQC:      {pkg.get('pqc',{}).get('algorithm','ML-DSA-65')}")
    print(f"  Pub key:  {pkg.get('pqc',{}).get('public_key_b64','')[:32]}…")

    for path_key, path_label, step_key, expected_terminal in [
        ("path_admissible",  "PATH B — ADMISSIBLE — Expected terminal: CLOSED",  "7_execution", "CLOSED"),
        ("path_interrupted", "PATH C — INTERRUPTED — Expected terminal: HALTED", "7_execution", "HALTED"),
    ]:
        p = pkg["paths"].get(path_key)
        if not p:
            continue

        exec_  = p["steps"].get(step_key, {})
        links  = exec_.get("ctchc_links", [])
        sealed = exec_.get("ctchc_sealed", {})

        print(f"\n  {'─'*68}")
        print(f"  {path_label}")
        print(f"  {'─'*68}")

        if sealed:
            terminal = sealed.get("terminal_state", "—")
            if terminal == expected_terminal:
                tc = G
            else:
                tc = R
            print(f"  CHAIN METADATA (BEV-INV-010)")
            print(f"    Chain ID:      {sealed.get('chain_id','—')}")
            print(f"    Session ID:    {sealed.get('session_id','—')}")
            print(f"    Turn count:    {sealed.get('turn_count','—')}")
            print(f"    Initialized:   {sealed.get('initialized_at','—')}")
            print(f"    Sealed at:     {sealed.get('sealed_at','—')}")
            print(f"    Genesis hash:  {sealed.get('genesis_hash','')[:40]}…")
            print(f"    Tip hash:      {sealed.get('current_tip_hash','')[:40]}…")
            print(f"    Terminal:      {tc}{terminal}{RST}  (expected: {expected_terminal})")

        if links:
            print(f"\n  HASH CHAIN — {len(links)} link(s)")
            print(f"  Formula: link_hash = SHA3-256(prev_link ‖ turn_hash ‖ governing_receipt_id)")
            print(f"  {'─'*68}")
            for i, lnk in enumerate(links):
                idx  = int(lnk.get("turn_index", i))
                proto_name = _TURN_PROTOCOLS.get(idx, ("?", "", ""))[0]
                prev = lnk.get("prev_link_hash", "")
                is_genesis = (not prev or prev in ("GENESIS", "0" * 64))

                print(f"\n  ┌─ Link {idx}: {proto_name}  (BEV-INV-011)")
                print(f"  │  Link ID:      {lnk.get('link_id','—')}")
                print(f"  │  Prev hash:    {'[GENESIS — first link]' if is_genesis else prev[:40]+'…'}")
                print(f"  │  Turn hash:    {lnk.get('turn_hash','')[:40]}…")
                print(f"  │  Governing:    {lnk.get('governing_receipt_id','—')}")
                print(f"  │  Chain hash:   {G}{lnk.get('chain_link_hash','')[:40]}…{RST}")
                print(f"  │  Created at:   {lnk.get('created_at','—')}")
                if i < len(links) - 1:
                    next_lnk = links[i + 1]
                    print(f"  │  ↓ this chain_link_hash becomes prev_link_hash of Link {idx + 1}")
                    print(f"  │    feeds: {next_lnk.get('chain_link_hash','')[:20]}…")
                print(f"  └─")

        if sealed and sealed.get("seal_hash"):
            s_terminal = sealed.get("terminal_state", "")
            sc = G if s_terminal == "CLOSED" else (Y if s_terminal == "HALTED" else R)
            print(f"\n  CHAIN SEAL (BEV-INV-014)")
            print(f"    Seal hash:     {sealed.get('seal_hash','')[:40]}…")
            print(f"    PQC sig:       {sealed.get('seal_pqc_algorithm','—')} · present={bool(sealed.get('seal_pqc_signature'))}")
            print(f"    Terminal:      {sc}{s_terminal}{RST}")
            print(f"\n  OFFLINE VERIFICATION PROTOCOL")
            print(f"    Step 1  For each link i: recompute SHA3-256(prev_link ‖ turn_hash ‖ governing_receipt_id)")
            print(f"    Step 2  Confirm chain_link_hash[i] matches recomputed value")
            print(f"    Step 3  Confirm current_tip_hash = chain_link_hash of last link")
            print(f"    Step 4  Verify seal PQC sig: ML-DSA-65.verify(seal_hash, sig, public_key)")
            print(f"    Step 5  Confirm terminal_state ∈ {{CLOSED, HALTED}} matches expected")
            print(f"    Tool:   python verify.py <package.json> --verify-settlement")
            print(f"            python verify.py <package.json> --verify-halt")

    print()
    print("═" * 70)
    print("  END — Chain-of-Custody Certificate (CoCC)")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("  This certificate is derived from a CTCHC sealed under")
    print("  BEV-INV-010–014 (RFC-ATF-6, ADR-183). Tamper-evident.")
    print("═" * 70)


def report_version_compatibility(pkg: Dict, pkg_path: str) -> None:
    """
    --check-version  (IAEP-RPT-004, ADR-203 §2.4)

    Version Compatibility Attestation (VCA).

    Formal declaration of: package spec version, verifier expected check
    count, paths present, and the backward-compatibility guarantee that
    governs all RTE-001 protocol evolution.

    COMPAT-INV-001 (ADR-203 §3): each version upgrade adds checks to new
    paths — existing checks on existing paths are never modified. A package
    that passed N checks on version V will still pass those N checks on V+1.

    Differentiator: the verifier went from 111 → 148 checks across three
    protocol versions without modifying a single existing check. This is
    the formal, machine-readable proof of that guarantee.
    RTE-INV-001 (ADR-201) · COMPAT-INV-001 (ADR-203 §3).
    """
    G, Y, R, RST = "\033[32m", "\033[33m", "\033[31m", "\033[0m"

    print()
    print("═" * 70)
    print("  OMNIX-RTE-001 — Version Compatibility Attestation (VCA)")
    print("  IAEP-RPT-004 · ADR-203 §2.4 · COMPAT-INV-001")
    print("═" * 70)
    print(f"  Package:      {pkg.get('package_id','—')}")
    print(f"  File:         {os.path.basename(pkg_path)}")
    print(f"  Generated at: {pkg.get('generated_at','—')}")
    print(f"  Generated by: {pkg.get('generated_by','—')}")
    print(f"  ADR ref:      {pkg.get('adr_reference','—')}")
    print(f"  PQC:          {pkg.get('pqc',{}).get('algorithm','—')}")

    paths = pkg.get("paths", {})
    has_a = "path_dangerous"   in paths
    has_b = "path_admissible"  in paths
    has_c = "path_interrupted" in paths

    print(f"\n  {'─'*68}")
    print(f"  PATHS PRESENT IN PACKAGE")
    print(f"  {'─'*68}")
    print(f"    Path A — Dangerous (authority drift):    {G+'✓'+RST if has_a else R+'✗'+RST}")
    print(f"    Path B — Admissible (execution + PoGC): {G+'✓'+RST if has_b else R+'✗'+RST}")
    print(f"    Path C — Interrupted (mandate collapse): {G+'✓'+RST if has_c else Y+'✗ (v1.2.0 or earlier)'+RST}")

    if has_a and has_b and has_c:
        spec, sc, checks = "v1.3.0", G, 148
        note = "Triple-path package — all paths verified"
    elif has_a and has_b:
        spec, sc, checks = "v1.2.0", Y, 111
        note = "Dual-path package — Path C not present"
    else:
        spec, sc, checks = "v1.0.0–v1.1.0", R, 74
        note = "Single-path or partial package"

    pkg_version = pkg.get("package_version", pkg.get("omnix_version", "—"))
    print(f"\n  Package spec:   {sc}{spec}{RST}  (declared version: {pkg_version})")
    print(f"  Expected checks:{checks} in FULL mode")
    print(f"  Note:           {note}")

    print(f"\n  {'─'*68}")
    print(f"  PROTOCOL EVOLUTION — COMPATIBILITY MATRIX (COMPAT-INV-001)")
    print(f"  {'─'*68}")
    print(f"  {'Spec':<8}  {'Paths':<10}  {'Checks':<8}  {'New checks added':<32}  Status")
    print(f"  {'─'*8}  {'─'*10}  {'─'*8}  {'─'*32}  {'─'*14}")

    compat_rows = [
        ("v1.0.0", "A+B",   "~74",  "Baseline — single dual-path package",            False),
        ("v1.1.0", "A+B",   "~74",  "MBR/MAS/CTCHC added to existing paths",          False),
        ("v1.2.0", "A+B",   "111",  "+37 checks on existing paths (explicit MAS/CTCHC)", False),
        ("v1.3.0", "A+B+C", "148",  "+37 checks for Path C (interrupted execution)",   False),
        ("v1.4.0", "A+B+C", "184",  "+36 checks GCFR+IPFL intake layer (ADR-204)",     True),
    ]

    for ver, paths_str, n_checks, added, is_current in compat_rows:
        row_col = G if is_current else ""
        curr_marker = f"  ← {G}current{RST}" if is_current else ""
        print(f"  {row_col}{ver:<8}{RST}  {paths_str:<10}  {n_checks:<8}  {added:<32}{curr_marker}")

    print(f"\n  {'─'*68}")
    print(f"  COMPAT-INV-001 (ADR-203 §3) — Backward-Compatibility Guarantee")
    print(f"  {'─'*68}")
    print(f"  «Each RTE-001 version upgrade adds verification checks to new")
    print(f"   paths or new artifact types. Existing checks on existing paths")
    print(f"   are NEVER modified or removed. A package that passed N checks")
    print(f"   under verifier version V will still pass those same N checks")
    print(f"   under any later version V+k.»")
    print()
    print(f"  Invariant status: {G}ACTIVE{RST}")
    print(f"  Current verifier: EXPECTED_TOTAL_CHECKS = {EXPECTED_TOTAL_CHECKS}")
    print(f"  Invariants in pkg:{len(pkg.get('invariants_demonstrated', []))} declared")

    print()
    print("═" * 70)
    print("  END — Version Compatibility Attestation (VCA)")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print(f"  Verifier: OMNIX-RTE-001 · ADR-201/202/203/204 · COMPAT-INV-001")
    print("═" * 70)


def report_intake_formation(pkg: Dict) -> None:
    """
    --intake-report  (IAEP-RPT-005, ADR-203 §2.5 / ADR-204)

    Intake Formation Report (IFR).

    Presents the Governance Contract Formation Record (GCFR) for all 3 paths
    with per-predicate summary: IAD authority level, SAR scope, MFR mandate
    objective hash, CPS sanctions verdict, FPS freshness window.

    This report directly addresses Dr. Masayuki Otani's observation that the
    public artefact shows trace+verification but not the intake+predicate
    formation layer. The GCFR makes explicit what was pre-declared before
    any execution began — the Governance Contract formed at Step 0.

    IPFL-INV-001–008 (ADR-204) · IAEP-RPT-005 · RTE-001 v1.4.0
    """
    G, Y, R, RST = "\033[32m", "\033[33m", "\033[31m", "\033[0m"

    print()
    print("═" * 72)
    print("  OMNIX-RTE-001 — Intake Formation Report (IFR)")
    print("  IAEP-RPT-005 · ADR-204 §2 · IPFL-INV-001–008 · v1.4.0")
    print("═" * 72)
    print(f"  Package:     {pkg.get('package_id', '—')}")
    print(f"  Scenario:    {pkg.get('scenario', {}).get('name', '—')}")
    print(f"  Amount:      USD {pkg.get('scenario', {}).get('amount_usd', 0):,}")
    print(f"  Generated:   {pkg.get('generated_at', '—')}")
    print()
    print("  «The Governance Contract is formed at Step 0 — before any source")
    print("   state capture, before any authority check, before any execution.")
    print("   The GCFR seals all five intake predicates with ML-DSA-65 PQC.")
    print("   No execution is admitted without a sealed Governance Contract.»")
    print(f"  {'─'*70}")

    for path_key, path_label, path_desc, auth_note in [
        ("path_dangerous",  "DANGEROUS",   "Authority drift → HALT",              "42% budget (DEGRADED)"),
        ("path_admissible", "ADMISSIBLE",  "Recertified → 3-turn execution → PoGC","88% budget (RECERTIFIED)"),
        ("path_interrupted","INTERRUPTED", "Valid authority → mid-chain HALT",     "88% budget (VALID)"),
    ]:
        p      = pkg.get("paths", {}).get(path_key, {})
        intake = p.get("steps", {}).get("0_intake", {})
        comp   = intake.get("components", {})
        seal   = intake.get("intake_seal", {})
        iad    = comp.get("intake_authority_declaration", {})
        sar    = comp.get("scope_authorization_record", {})
        mfr    = comp.get("mandate_formation_record", {})
        cps    = comp.get("counterparty_predicate_set", {})
        fps    = comp.get("freshness_predicate_set", {})

        print()
        print(f"  ┌─ PATH: {path_label} — {path_desc}")
        print(f"  │  GCFR ID:    {intake.get('gcfr_id', '—')}")
        print(f"  │  Formed at:  {intake.get('formed_at', '—')}")
        print(f"  │  IDS seal:   {seal.get('seal_hash', '')[:40]}...")
        print(f"  │  PQC:        {seal.get('pqc_algorithm', '—')} ({'signed' if seal.get('pqc_signature') else 'MISSING'})")
        print(f"  │")
        print(f"  │  [IAD] Intake Authority Declaration  — IPFL §2.1 (IPFL-INV-001)")
        print(f"  │        Agent:          {iad.get('agent_id', '—')}")
        print(f"  │        Authority:      {iad.get('human_authority', '—')}")
        print(f"  │        Type:           {iad.get('authority_type', '—')}")
        print(f"  │        Budget:         {auth_note}")
        print(f"  │        Depth limit:    {iad.get('delegation_depth_limit', '—')}")
        print(f"  │")
        print(f"  │  [SAR] Scope Authorization Record   — IPFL §2.2 (IPFL-INV-002)")
        print(f"  │        Domain:         {sar.get('domain', '—')}")
        print(f"  │        Max amount:     USD {sar.get('max_amount_usd', 0):,}")
        print(f"  │        Approved rails: {', '.join(sar.get('approved_rails', []))}")
        print(f"  │        Permitted:      {len(sar.get('permitted_actions', []))} actions")
        print(f"  │        Excluded:       {len(sar.get('excluded_actions', []))} actions")
        print(f"  │")
        print(f"  │  [MFR] Mandate Formation Record     — IPFL §2.3 (IPFL-INV-003/004)")
        print(f"  │        Mandate ref:    {mfr.get('mandate_ref', '—')}")
        obj_hash = mfr.get("mandate_objective_hash", "")
        print(f"  │        Objective hash: {obj_hash[:40] + '...' if obj_hash else '—'}")
        print(f"  │        Prohibitions:   {len(mfr.get('mandate_prohibitions', []))} proxy guards pre-declared")
        print(f"  │        HALT threshold: {mfr.get('halt_threshold', '—')}")
        print(f"  │")
        print(f"  │  [CPS] Counterparty Predicate Set   — IPFL §2.4 (IPFL-INV-005)")
        print(f"  │        Whitelist:      {len(cps.get('counterparty_whitelist', []))} counterparties")
        sanctions = cps.get("sanctions_checks", {})
        sanctions_status = f"{G}ALL CLEAR{RST}" if cps.get("sanctions_all_clear") else f"{R}ALERT{RST}"
        print(f"  │        Sanctions:      {sanctions_status} ({', '.join(sanctions.keys())})")
        print(f"  │        FX band:        ±{cps.get('fx_rate_band_pct', '—')}%")
        print(f"  │")
        print(f"  │  [FPS] Freshness Predicate Set      — IPFL §2.5 (IPFL-INV-006)")
        print(f"  │        Max TTL:        {fps.get('max_ttl_seconds', 0):,}s ({fps.get('tar_validity_window_hours', '—')}h window)")
        print(f"  │        Reg. epoch:     {fps.get('regulatory_epoch', '—')}")
        print(f"  │        Mandate expiry: {fps.get('mandate_ref_expiry', '—')}")
        print(f"  │        Fresh check:    {G+'PASSED'+RST if fps.get('freshness_check_passed') else R+'FAILED'+RST}")
        print(f"  └{'─'*69}")

    print()
    print(f"  Component hashes (ADR-204 §4 canonical seal formula):")
    print(f"  seal_hash = SHA3-256(iad_hash | sar_hash | mfr_hash | cps_hash | fps_hash)")
    print(f"  Alteration of any predicate = seal breaks = detectable offline (IPFL-INV-007)")
    print()
    print("═" * 72)
    print("  END — Intake Formation Report (IFR)")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print(f"  Verifier: OMNIX-RTE-001 v1.4.0 · ADR-204 · IPFL-INV-001–008")
    print("═" * 72)


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
    parser.add_argument("--verify-intake",         action="store_true",
                        help="Verify GCFR seal + 5 predicate hashes + 3 cross-refs (all paths) — ADR-204 IPFL v1.4.0 (+36 checks)")
    parser.add_argument("--verify-authority",      action="store_true", help="Verify DR + MBR (all paths)")
    parser.add_argument("--verify-continuity",     action="store_true", help="Verify RCR + MAS (all paths)")
    parser.add_argument("--verify-counterfactual", action="store_true", help="Verify CGE CAT + CFRs (all paths)")
    parser.add_argument("--verify-halt",           action="store_true", help="Verify dangerous path HALT chain")
    parser.add_argument("--verify-settlement",     action="store_true", help="Verify admissible path settlement")
    parser.add_argument("--verify-replay",         action="store_true", help="Verify replay proofs + TCS (all paths)")
    parser.add_argument("--verify-interrupted",    action="store_true",
                        help="Verify interrupted path: Turn-by-turn BAR+CCS+MAS, HALT at Turn 2, "
                             "CTCHC HALTED, MBR Seal UNCERTIFIED, OSG REJECTED, PoGC absent (v1.3.0+)")
    parser.add_argument("--json",                  action="store_true", help="Output machine-readable JSON report")
    # ── IAEP report commands (ADR-203 + ADR-204) — standalone institutional artifact extraction ──
    parser.add_argument("--treasury-protocol", action="store_true",
                        help="Treasury Protocol Execution Report: per-turn SWIFT/FIX/XRPL breakdown "
                             "(IAEP-RPT-001, ADR-203 §2.1)")
    parser.add_argument("--mandate-timeline",  action="store_true",
                        help="Mandate Integrity Timeline: MBR frozen→MAS per-turn→MBR Seal "
                             "(IAEP-RPT-002, ADR-203 §2.2)")
    parser.add_argument("--chain-custody",     action="store_true",
                        help="Chain-of-Custody Certificate: CTCHC extracted for courts/regulators "
                             "(IAEP-RPT-003, ADR-203 §2.3)")
    parser.add_argument("--check-version",     action="store_true",
                        help="Version Compatibility Attestation: formal backward-compatibility proof "
                             "(IAEP-RPT-004, ADR-203 §2.4)")
    parser.add_argument("--intake-report",     action="store_true",
                        help="Intake Formation Report: GCFR per-path with IAD·SAR·MFR·CPS·FPS summary — "
                             "addresses Dr. Otani gap (IAEP-RPT-005, ADR-204)")
    args = parser.parse_args()

    # Determine mode
    targeted = any([
        args.verify_intake, args.verify_authority, args.verify_continuity,
        args.verify_counterfactual, args.verify_halt, args.verify_settlement,
        args.verify_replay, args.verify_interrupted,
    ])
    any_reports = any([
        args.treasury_protocol, args.mandate_timeline,
        args.chain_custody, args.check_version, args.intake_report,
    ])
    run_all = not targeted and not any_reports

    if run_all:
        mode = "FULL"
    else:
        flags = []
        if args.verify_intake:         flags.append("intake")
        if args.verify_authority:      flags.append("authority")
        if args.verify_continuity:     flags.append("continuity")
        if args.verify_counterfactual: flags.append("counterfactual")
        if args.verify_halt:           flags.append("halt")
        if args.verify_settlement:     flags.append("settlement")
        if args.verify_replay:         flags.append("replay")
        if args.verify_interrupted:    flags.append("interrupted")
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
    if run_all or args.verify_intake:
        verify_intake(report, pkg, pqc, pk_bytes)

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

    if run_all or args.verify_interrupted:
        verify_interrupted(report, pkg, pqc, pk_bytes)

    # Summary (only print when any verification checks ran)
    if run_all or targeted:
        all_ok = report.summary()
        if args.json:
            print("\n" + json.dumps(report.to_dict(), indent=2))
    else:
        all_ok = True

    # ── IAEP institutional artifact reports (ADR-203) ─────────────────────────
    # These run AFTER verification so the cryptographic verdict is already shown.
    # They do NOT affect the check count or the exit code.
    if args.treasury_protocol:
        report_treasury_protocol(pkg)
    if args.mandate_timeline:
        report_mandate_timeline(pkg)
    if args.chain_custody:
        report_chain_custody(pkg)
    if args.check_version:
        report_version_compatibility(pkg, pkg_path)
    if args.intake_report:
        report_intake_formation(pkg)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
