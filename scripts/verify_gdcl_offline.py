#!/usr/bin/env python3
"""
GDCL Offline Verifier — v1.0.0
================================
Standalone verifier for GDCLConvergenceRecord (GCR) artifacts produced by
the Governance Decision Convergence Layer (ADR-206, OMNIX QUANTUM LTD).

This script has ZERO dependency on OMNIX infrastructure, APIs, accounts,
or proprietary code. It reimplements the GDCL convergence algorithm
verbatim from ADR-206 §Algorithm (15 lines of pure Python logic) and
applies 7 independent integrity checks to any GCR or evidence package.

Requirements:
    Python 3.8+
    pip install oqs-python   ← optional; enables PQC signature verification

Usage:
    # Verify a single GCR JSON file
    python verify_gdcl_offline.py --file certificate.json

    # Verify all GCRs inside a GDCL evidence package
    python verify_gdcl_offline.py --file gdcl_evidence_package_*.json

    # Machine-readable JSON output
    python verify_gdcl_offline.py --file certificate.json --json

    # Provide the PQC public key manually (overrides embedded key)
    python verify_gdcl_offline.py --file certificate.json --platform-key <base64>

Exit codes:
    0  All checks passed (VERIFIED)
    1  One or more checks failed (INVALID)
    2  File not found or not parseable

ADR-206 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

VERIFIER_VERSION = "1.0.0"
ADR_REFERENCE    = "ADR-206"
TOOL_NAME        = "verify_gdcl_offline.py"

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

_TTY = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _TTY else text

def grn(t: str) -> str: return _c("32;1", t)
def red(t: str) -> str: return _c("31;1", t)
def yel(t: str) -> str: return _c("33;1", t)
def cyn(t: str) -> str: return _c("36;1", t)
def wht(t: str) -> str: return _c("97;1", t)
def dim(t: str) -> str: return _c("2",    t)
def mag(t: str) -> str: return _c("35;1", t)

# ---------------------------------------------------------------------------
# GDCL convergence algorithm — reimplemented from ADR-206 §Algorithm
#
# This is the complete, canonical algorithm in 15 lines.
# Any third party may copy this function and verify any GCR independently.
# Property: GDCL-INV-003 Determinism — pure function of verdict_distribution.
# ---------------------------------------------------------------------------

_V_PORTABLE     = "SEMANTICALLY_PORTABLE"
_V_ACKNOWLEDGED = "DRIFT_ACKNOWLEDGED"
_V_CRITICAL     = "DRIFT_CRITICAL"
_V_INCOMPATIBLE = "SEMANTICALLY_INCOMPATIBLE"

_VALID_VERDICTS = frozenset({
    "FULL_RELIANCE", "QUALIFIED_RELIANCE", "LIMITED_RELIANCE",
    "CONTESTED", "REFUSED", "ESCALATION", "INDETERMINATE",
})

_VALID_DSPP = frozenset({_V_PORTABLE, _V_ACKNOWLEDGED, _V_CRITICAL, _V_INCOMPATIBLE})


def _derive_verdict(distribution: Dict[str, int]) -> str:
    """
    ADR-206 §Algorithm — reproduced verbatim.
    Input:  verdict_distribution from GCR (e.g. {"DRIFT_CRITICAL": 1, "SEMANTICALLY_PORTABLE": 3})
    Output: one of seven GDCLCompositeVerdict values.

    This is a pure function. Given the same distribution, the output is always identical.
    Any implementation of this function in any language produces the same result.
    """
    n_total = sum(distribution.values())
    if n_total == 0:
        return "INDETERMINATE"

    has_i = distribution.get(_V_INCOMPATIBLE,  0) > 0
    has_c = distribution.get(_V_CRITICAL,      0) > 0
    has_a = distribution.get(_V_ACKNOWLEDGED,  0) > 0
    has_p = distribution.get(_V_PORTABLE,      0) > 0
    n_i   = distribution.get(_V_INCOMPATIBLE,  0)

    if has_i and has_c:             return "ESCALATION"
    if n_i == n_total:              return "REFUSED"
    if has_i and (has_p or has_a):  return "CONTESTED"
    if has_c:                       return "LIMITED_RELIANCE"
    if has_a:                       return "QUALIFIED_RELIANCE"
    return "FULL_RELIANCE"


# ---------------------------------------------------------------------------
# Content hash — SHA3-256 over canonical JSON (mirrors GDCLEngine._compute_hash)
# ---------------------------------------------------------------------------

_HASH_EXCLUDE = frozenset({"content_hash", "pqc_signature", "pqc_algorithm",
                            "public_key_b64"})

def _compute_content_hash(gcr: Dict[str, Any]) -> str:
    clean = {k: v for k, v in gcr.items() if k not in _HASH_EXCLUDE}
    payload = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha3_256(payload).hexdigest()


# ---------------------------------------------------------------------------
# PQC signature verification — optional (oqs-python)
# ---------------------------------------------------------------------------

def _verify_pqc(sig_b64: str, content_hash: str, pk_b64: str) -> Tuple[bool, str]:
    try:
        import oqs
    except ImportError:
        return True, "SKIP — oqs-python not installed (pip install oqs-python to enable)"
    try:
        sig = base64.b64decode(sig_b64)
        pk  = base64.b64decode(pk_b64)
        verifier = oqs.Signature("Dilithium3")
        ok = verifier.verify(content_hash.encode(), sig, pk)
        if ok:
            return True, "ML-DSA-65 (Dilithium3, FIPS 204) signature valid ✓"
        return False, "ML-DSA-65 signature INVALID — payload may have been tampered"
    except Exception as exc:
        return False, f"PQC verification error: {exc}"


# ---------------------------------------------------------------------------
# Seven integrity checks (one per GCR)
# ---------------------------------------------------------------------------

CheckResult = Tuple[str, bool, str]   # (check_id, passed, message)

def _check_required_fields(gcr: Dict) -> CheckResult:
    required = {
        "gcr_id", "receiving_runtime_id", "rsa_ids", "receipt_ids",
        "n_assessments", "verdict_distribution", "composite_verdict",
        "dominant_sdu", "mean_sdu", "min_portability_confidence",
        "boundary_recommendation", "converged_at", "content_hash",
    }
    missing = required - gcr.keys()
    if missing:
        return ("GCR-F1", False, f"Missing required fields: {sorted(missing)}")
    return ("GCR-F1", True, "All required fields present")


def _check_content_hash(gcr: Dict) -> CheckResult:
    stored   = gcr.get("content_hash", "")
    computed = _compute_content_hash(gcr)
    if stored == computed:
        return ("GCR-F2", True, f"SHA3-256 content_hash verified: {stored[:16]}…")
    return ("GCR-F2", False,
            f"content_hash MISMATCH — stored: {stored[:16]}… computed: {computed[:16]}… "
            "— GCR fields may have been altered after signing")


def _check_verdict_taxonomy(gcr: Dict) -> CheckResult:
    v = gcr.get("composite_verdict", "")
    if v in _VALID_VERDICTS:
        return ("GCR-F3", True, f"composite_verdict '{v}' is a valid GDCL taxonomy value")
    return ("GCR-F3", False,
            f"composite_verdict '{v}' is NOT in GDCL taxonomy. "
            f"Valid values: {sorted(_VALID_VERDICTS)}")


def _check_verdict_derivation(gcr: Dict) -> CheckResult:
    dist  = gcr.get("verdict_distribution", {})
    stored_verdict  = gcr.get("composite_verdict", "")
    derived_verdict = _derive_verdict(dist)
    if stored_verdict == derived_verdict:
        return ("GCR-F4", True,
                f"Algorithm re-derivation: {derived_verdict} ← distribution {dict(dist)} ✓")
    return ("GCR-F4", False,
            f"Verdict MISMATCH — stored: '{stored_verdict}' vs "
            f"algorithm re-derived: '{derived_verdict}' from distribution {dict(dist)}. "
            "The composite_verdict was not produced by the ADR-206 algorithm.")


def _check_n_assessments(gcr: Dict) -> CheckResult:
    n_stored = gcr.get("n_assessments", -1)
    dist     = gcr.get("verdict_distribution", {})
    n_dist   = sum(dist.values())
    if n_stored == n_dist:
        return ("GCR-F5", True,
                f"n_assessments={n_stored} consistent with sum(verdict_distribution)={n_dist}")
    return ("GCR-F5", False,
            f"n_assessments={n_stored} ≠ sum(verdict_distribution)={n_dist}. "
            "Distribution may have been modified without updating n_assessments.")


def _check_sdu_range(gcr: Dict) -> CheckResult:
    issues = []
    for field in ("dominant_sdu", "mean_sdu", "min_portability_confidence"):
        val = gcr.get(field)
        if val is None:
            issues.append(f"{field} missing")
        elif not (0.0 <= float(val) <= 1.0):
            issues.append(f"{field}={val} out of range [0.0, 1.0]")
    if issues:
        return ("GCR-F6", False, "SDU range violation: " + "; ".join(issues))
    return ("GCR-F6", True,
            f"SDU values in range: dominant={gcr.get('dominant_sdu'):.4f} "
            f"mean={gcr.get('mean_sdu'):.4f} "
            f"min_conf={gcr.get('min_portability_confidence'):.4f}")


def _check_pqc_signature(gcr: Dict, pk_override: Optional[str]) -> CheckResult:
    sig = gcr.get("pqc_signature")
    if not sig:
        return ("GCR-F7", True,
                "SKIP — no pqc_signature present (unsigned GCR — content_hash still verified)")

    pk_b64 = pk_override or gcr.get("public_key_b64") or gcr.get("platform_public_key_b64")
    if not pk_b64:
        return ("GCR-F7", True,
                "SKIP — pqc_signature present but no public key provided. "
                "Use --platform-key <base64> to verify the signature.")

    ok, msg = _verify_pqc(sig, gcr["content_hash"], pk_b64)
    return ("GCR-F7", ok, msg)


def _run_all_checks(gcr: Dict, pk_override: Optional[str]) -> List[CheckResult]:
    return [
        _check_required_fields(gcr),
        _check_content_hash(gcr),
        _check_verdict_taxonomy(gcr),
        _check_verdict_derivation(gcr),
        _check_n_assessments(gcr),
        _check_sdu_range(gcr),
        _check_pqc_signature(gcr, pk_override),
    ]


# ---------------------------------------------------------------------------
# Verdict badge
# ---------------------------------------------------------------------------

_BADGE = {
    "FULL_RELIANCE":      grn("FULL_RELIANCE"),
    "QUALIFIED_RELIANCE": grn("QUALIFIED_RELIANCE"),
    "LIMITED_RELIANCE":   yel("LIMITED_RELIANCE"),
    "CONTESTED":          yel("CONTESTED"),
    "REFUSED":            red("REFUSED"),
    "ESCALATION":         red("ESCALATION"),
    "INDETERMINATE":      dim("INDETERMINATE"),
}


# ---------------------------------------------------------------------------
# Single GCR report
# ---------------------------------------------------------------------------

def _report_gcr(gcr: Dict, checks: List[CheckResult], json_mode: bool,
                label: str = "") -> bool:
    passed = [c for c in checks if c[1]]
    failed = [c for c in checks if not c[1]]
    skipped = [c for c in checks if c[1] and c[2].startswith("SKIP")]
    n_real_pass = len(passed) - len(skipped)
    valid = len(failed) == 0

    if json_mode:
        return valid

    verdict_str = gcr.get("composite_verdict", "UNKNOWN")
    badge       = _BADGE.get(verdict_str, verdict_str)

    print()
    if label:
        print(f"  {dim('Scenario:')} {wht(label)}")
    print(f"  {dim('GCR:')} {wht(gcr.get('gcr_id', '?'))}")
    print(f"  {dim('Composite Verdict:')} {badge}")
    print(f"  {dim('n_assessments:')} {gcr.get('n_assessments', '?')}  "
          f"{dim('dominant_sdu:')} {gcr.get('dominant_sdu', '?'):.4f}  "
          f"{dim('mean_sdu:')} {gcr.get('mean_sdu', '?'):.4f}")
    print()
    for check_id, ok, msg in checks:
        icon = grn("✓") if ok else red("✗")
        color = dim if (ok and msg.startswith("SKIP")) else (dim if ok else red)
        print(f"  {icon} [{check_id}] {color(msg)}")

    print()
    if valid:
        print(f"  {grn('VERIFIED')} — {n_real_pass}/{len(checks)} checks passed "
              f"({len(skipped)} skipped)")
    else:
        print(f"  {red('INVALID')} — {len(failed)} check(s) FAILED")
        for _, _, msg in failed:
            print(f"  {red('  →')} {msg}")
    return valid


# ---------------------------------------------------------------------------
# Package support (evidence_package JSON containing multiple GCRs)
# ---------------------------------------------------------------------------

def _is_package(data: Dict) -> bool:
    return "scenarios" in data and "package_id" in data


def _extract_gcrs_from_package(data: Dict) -> List[Tuple[str, Dict]]:
    """Returns list of (label, gcr_dict) from a GDCL evidence package."""
    results = []
    for scen in data.get("scenarios", []):
        label = f"{scen.get('scenario_id', '?')} — {scen.get('title', '?')}"
        gcr   = scen.get("gcr")
        if gcr:
            results.append((label, gcr))
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description=(
            "Standalone offline verifier for GDCL Convergence Records (GCR).\n"
            "Zero OMNIX dependencies. Reimplements ADR-206 algorithm from spec.\n"
            "Run against any GCR JSON or GDCL evidence package."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python verify_gdcl_offline.py --file gcr.json\n"
            "  python verify_gdcl_offline.py --file gdcl_evidence_package_*.json\n"
            "  python verify_gdcl_offline.py --file gcr.json --json\n"
            "  python verify_gdcl_offline.py --file gcr.json --platform-key <base64>\n\n"
            "Exit codes:\n"
            "  0  All checks passed (VERIFIED)\n"
            "  1  One or more checks failed (INVALID)\n"
            "  2  File not found or unparseable JSON\n\n"
            f"Algorithm reference: {ADR_REFERENCE} §Algorithm\n"
            "OMNIX QUANTUM LTD — https://omnixquantum.com"
        ),
    )
    parser.add_argument("--file", "-f", metavar="PATH", required=True,
                        help="Path to a GCR JSON or GDCL evidence package JSON")
    parser.add_argument("--json", action="store_true",
                        help="Output machine-readable JSON result (one object per GCR)")
    parser.add_argument("--platform-key", metavar="B64",
                        help="Base64-encoded ML-DSA-65 public key (overrides embedded key)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(red(f"Error: file not found: {path}"), file=sys.stderr)
        return 2

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        print(red(f"Error: not valid JSON: {exc}"), file=sys.stderr)
        return 2

    pk_override = args.platform_key

    # -------------------------------------------------------------------
    # Determine input type: single GCR or evidence package
    # -------------------------------------------------------------------

    if _is_package(data):
        gcr_list = _extract_gcrs_from_package(data)
        if not args.json:
            print()
            print(wht(f"  OMNIX GDCL Offline Verifier {VERIFIER_VERSION}"))
            print(dim(f"  Evidence package: {data.get('package_id', '?')}"))
            print(dim(f"  Generated: {data.get('generated_at', '?')}"))
            print(dim(f"  {ADR_REFERENCE} — {len(gcr_list)} GCRs to verify"))
            print(dim(f"  Algorithm: reimplemented from {ADR_REFERENCE} §Algorithm (zero OMNIX deps)"))
    else:
        gcr_list = [("", data)]
        if not args.json:
            print()
            print(wht(f"  OMNIX GDCL Offline Verifier {VERIFIER_VERSION}"))
            print(dim(f"  File: {path}"))
            print(dim(f"  {ADR_REFERENCE} — single GCR"))

    # -------------------------------------------------------------------
    # Run checks on all GCRs
    # -------------------------------------------------------------------

    all_results = []
    all_valid   = True

    for label, gcr in gcr_list:
        checks = _run_all_checks(gcr, pk_override)
        valid  = _report_gcr(gcr, checks, args.json, label=label)
        all_valid = all_valid and valid

        if args.json:
            all_results.append({
                "gcr_id":           gcr.get("gcr_id"),
                "composite_verdict":gcr.get("composite_verdict"),
                "valid":            valid,
                "checks": [
                    {"id": c[0], "passed": c[1], "message": c[2]} for c in checks
                ],
                "n_passed":  sum(1 for c in checks if c[1]),
                "n_failed":  sum(1 for c in checks if not c[1]),
                "n_checks":  len(checks),
            })

    # -------------------------------------------------------------------
    # Final summary
    # -------------------------------------------------------------------

    if args.json:
        print(json.dumps({
            "verifier":      TOOL_NAME,
            "version":       VERIFIER_VERSION,
            "adr_reference": ADR_REFERENCE,
            "file":          str(path),
            "n_gcrs":        len(gcr_list),
            "all_valid":     all_valid,
            "results":       all_results,
        }, indent=2))
    else:
        if len(gcr_list) > 1:
            n_pass = sum(1 for _, gcr in gcr_list
                         if len([c for c in _run_all_checks(gcr, pk_override) if not c[1]]) == 0)
            print()
            print(f"  {dim('─' * 60)}")
            print()
            if all_valid:
                print(f"  {grn('ALL VERIFIED')} — {n_pass}/{len(gcr_list)} GCRs passed all checks")
            else:
                n_fail = len(gcr_list) - n_pass
                print(f"  {red('PARTIAL FAILURE')} — {n_fail}/{len(gcr_list)} GCRs failed")
        print()

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
