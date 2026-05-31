#!/usr/bin/env python3
"""
GDCL Adversarial Audit — v1.0.0
=================================
Attempts 8 distinct attack vectors against GDCLConvergenceRecord (GCR) artifacts
to verify that the GDCL integrity model correctly detects every manipulation.

Each attack mutates a GCR in a specific way and then passes it through
both the OMNIX verifier logic AND the standalone algorithm re-derivation.
An attack is "DETECTED" if at least one check catches it.
An attack "EVADES" if no check catches it (audit finding).

Expected outcome on a well-formed package: 8/8 attacks detected, 0 evasions.

Attack inventory:
    A01  Flip composite_verdict to FULL_RELIANCE on a REFUSED GCR
    A02  Inflate dominant_sdu beyond 1.0
    A03  Remove SEMANTICALLY_INCOMPATIBLE from verdict_distribution
    A04  Inject DRIFT_CRITICAL into FULL_RELIANCE distribution
    A05  Change n_assessments without touching distribution
    A06  Add a fabricated rsa_id to rsa_ids without re-signing
    A07  Forge a GCR from scratch without signing (no content_hash)
    A08  Silently re-sign after verdict manipulation (without OMNIX keys)

Usage:
    python scripts/gdcl_adversarial_audit.py --package evidence_packages/gdcl_evidence_package_*.json
    python scripts/gdcl_adversarial_audit.py --package evidence_packages/gdcl_evidence_package_*.json --json

ADR-206 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
# Algorithm re-derivation (ADR-206 §Algorithm — identical to verifier)
# ---------------------------------------------------------------------------

_V_PORTABLE     = "SEMANTICALLY_PORTABLE"
_V_ACKNOWLEDGED = "DRIFT_ACKNOWLEDGED"
_V_CRITICAL     = "DRIFT_CRITICAL"
_V_INCOMPATIBLE = "SEMANTICALLY_INCOMPATIBLE"

_VALID_VERDICTS = frozenset({
    "FULL_RELIANCE", "QUALIFIED_RELIANCE", "LIMITED_RELIANCE",
    "CONTESTED", "REFUSED", "ESCALATION", "INDETERMINATE",
})

def _derive_verdict(distribution: Dict[str, int]) -> str:
    n_total = sum(distribution.values())
    if n_total == 0:
        return "INDETERMINATE"
    has_i = distribution.get(_V_INCOMPATIBLE, 0) > 0
    has_c = distribution.get(_V_CRITICAL,     0) > 0
    has_a = distribution.get(_V_ACKNOWLEDGED, 0) > 0
    has_p = distribution.get(_V_PORTABLE,     0) > 0
    n_i   = distribution.get(_V_INCOMPATIBLE, 0)
    if has_i and has_c:             return "ESCALATION"
    if n_i == n_total:              return "REFUSED"
    if has_i and (has_p or has_a):  return "CONTESTED"
    if has_c:                       return "LIMITED_RELIANCE"
    if has_a:                       return "QUALIFIED_RELIANCE"
    return "FULL_RELIANCE"

# ---------------------------------------------------------------------------
# Content hash (SHA3-256, canonical JSON — matches GDCLEngine._compute_hash)
# ---------------------------------------------------------------------------

_HASH_EXCLUDE = frozenset({"content_hash", "pqc_signature", "pqc_algorithm", "public_key_b64"})

def _compute_hash(gcr: Dict) -> str:
    clean = {k: v for k, v in gcr.items() if k not in _HASH_EXCLUDE}
    payload = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha3_256(payload).hexdigest()

# ---------------------------------------------------------------------------
# Detection checks used in each attack
# ---------------------------------------------------------------------------

def _detect(original: Dict, mutated: Dict, attack_id: str) -> Tuple[bool, List[str]]:
    """
    Runs all integrity checks against a mutated GCR.
    Returns (detected: bool, findings: List[str]).
    """
    findings: List[str] = []
    detected = False

    orig_hash = original.get("content_hash", "")
    mut_hash  = mutated.get("content_hash", "")

    # Check 1: content_hash integrity
    recomputed = _compute_hash(mutated)
    if recomputed != mut_hash:
        findings.append(
            f"GCR-F2 content_hash MISMATCH — stored {mut_hash[:16]}… ≠ recomputed {recomputed[:16]}…"
        )
        detected = True

    # Check 2: composite_verdict in taxonomy
    v = mutated.get("composite_verdict", "")
    if v not in _VALID_VERDICTS:
        findings.append(f"GCR-F3 composite_verdict '{v}' not in GDCL taxonomy")
        detected = True

    # Check 3: verdict re-derivation
    dist = mutated.get("verdict_distribution", {})
    derived = _derive_verdict(dist)
    stored  = mutated.get("composite_verdict", "")
    if derived != stored:
        findings.append(
            f"GCR-F4 verdict MISMATCH — stored '{stored}' ≠ derived '{derived}' "
            f"from distribution {dict(dist)}"
        )
        detected = True

    # Check 4: n_assessments consistency
    n_stored = mutated.get("n_assessments", -1)
    n_dist   = sum(dist.values())
    if n_stored != n_dist:
        findings.append(
            f"GCR-F5 n_assessments={n_stored} ≠ sum(distribution)={n_dist}"
        )
        detected = True

    # Check 5: SDU range
    for field in ("dominant_sdu", "mean_sdu", "min_portability_confidence"):
        val = mutated.get(field)
        if val is not None and not (0.0 <= float(val) <= 1.0):
            findings.append(f"GCR-F6 {field}={val} out of range [0.0, 1.0]")
            detected = True

    # Check 6: required fields present
    required = {
        "gcr_id", "composite_verdict", "content_hash",
        "n_assessments", "verdict_distribution", "converged_at",
    }
    missing = required - mutated.keys()
    if missing:
        findings.append(f"GCR-F1 missing required fields: {sorted(missing)}")
        detected = True

    return detected, findings

# ---------------------------------------------------------------------------
# Attack definitions
# ---------------------------------------------------------------------------

AttackResult = Dict[str, Any]

def _attack(
    attack_id: str,
    title: str,
    technique: str,
    target_verdict: str,
    package_scenarios: List[Dict],
    mutator,
) -> AttackResult:
    """
    Generic attack runner. Finds a GCR with the target verdict, applies
    the mutator, runs detection, returns result dict.
    """
    # Find target GCR
    target_gcr = None
    target_label = ""
    for scen in package_scenarios:
        if scen.get("verdict") == target_verdict:
            target_gcr   = copy.deepcopy(scen["gcr"])
            target_label = scen.get("title", target_verdict)
            break

    if target_gcr is None:
        return {
            "attack_id": attack_id, "title": title, "technique": technique,
            "target_verdict": target_verdict, "target_label": "NOT FOUND",
            "detected": None, "findings": ["Target GCR not found in package"],
            "status": "SKIP",
        }

    original = copy.deepcopy(target_gcr)
    mutated  = mutator(copy.deepcopy(target_gcr))
    detected, findings = _detect(original, mutated, attack_id)

    return {
        "attack_id":      attack_id,
        "title":          title,
        "technique":      technique,
        "target_verdict": target_verdict,
        "target_label":   target_label,
        "gcr_id":         original.get("gcr_id"),
        "detected":       detected,
        "findings":       findings,
        "status":         "DETECTED" if detected else "EVADED",
    }


def _run_all_attacks(scenarios: List[Dict]) -> List[AttackResult]:
    results: List[AttackResult] = []

    # A01 — Flip composite_verdict on REFUSED GCR
    def a01(gcr):
        gcr["composite_verdict"] = "FULL_RELIANCE"
        return gcr

    results.append(_attack(
        "A01",
        "Verdict Forgery — REFUSED → FULL_RELIANCE",
        "Directly overwrite composite_verdict string. "
        "Does not touch content_hash or verdict_distribution.",
        "REFUSED", scenarios, a01,
    ))

    # A02 — Inflate dominant_sdu > 1.0
    def a02(gcr):
        gcr["dominant_sdu"] = 1.42
        return gcr

    results.append(_attack(
        "A02",
        "SDU Overflow — dominant_sdu > 1.0",
        "Set dominant_sdu = 1.42, violating DSPP SDU bound [0, 1]. "
        "Does not update content_hash.",
        "LIMITED_RELIANCE", scenarios, a02,
    ))

    # A03 — Remove SEMANTICALLY_INCOMPATIBLE from distribution on CONTESTED GCR
    def a03(gcr):
        dist = dict(gcr.get("verdict_distribution", {}))
        if _V_INCOMPATIBLE in dist:
            portable = dist.get(_V_PORTABLE, 0)
            dist[_V_PORTABLE] = portable + dist.pop(_V_INCOMPATIBLE)
        gcr["verdict_distribution"] = dist
        return gcr

    results.append(_attack(
        "A03",
        "Distribution Laundering — INCOMPATIBLE absorbed into PORTABLE",
        "Move all INCOMPATIBLE counts into PORTABLE, keeping n_assessments constant. "
        "Attempts to make CONTESTED look like QUALIFIED_RELIANCE.",
        "CONTESTED", scenarios, a03,
    ))

    # A04 — Inject DRIFT_CRITICAL into FULL_RELIANCE distribution
    def a04(gcr):
        dist = dict(gcr.get("verdict_distribution", {}))
        dist[_V_CRITICAL] = dist.get(_V_CRITICAL, 0) + 1
        gcr["verdict_distribution"] = dist
        gcr["n_assessments"] = sum(dist.values())
        return gcr

    results.append(_attack(
        "A04",
        "Distribution Injection — add DRIFT_CRITICAL to FULL_RELIANCE GCR",
        "Inject one DRIFT_CRITICAL entry into a FULL_RELIANCE GCR distribution "
        "and update n_assessments. composite_verdict not updated → algorithm mismatch.",
        "FULL_RELIANCE", scenarios, a04,
    ))

    # A05 — Bump n_assessments without touching distribution
    def a05(gcr):
        gcr["n_assessments"] = gcr.get("n_assessments", 0) + 99
        return gcr

    results.append(_attack(
        "A05",
        "Coverage Inflation — n_assessments +99 without adding RSAs",
        "Increment n_assessments by 99 to suggest broader coverage. "
        "verdict_distribution unchanged → consistency check fails.",
        "QUALIFIED_RELIANCE", scenarios, a05,
    ))

    # A06 — Add fabricated rsa_id without re-signing
    def a06(gcr):
        fake_id = f"OMNIX-RSA-FORGED{uuid.uuid4().hex[:8].upper()}"
        gcr["rsa_ids"] = gcr.get("rsa_ids", []) + [fake_id]
        gcr["receipt_ids"] = gcr.get("receipt_ids", []) + [f"DR-FAKE-{uuid.uuid4().hex[:8].upper()}"]
        return gcr

    results.append(_attack(
        "A06",
        "RSA Injection — add fabricated rsa_id without re-signing",
        "Append a forged OMNIX-RSA-FORGED* ID to rsa_ids and receipt_ids. "
        "Does not update content_hash → hash mismatch detected.",
        "ESCALATION", scenarios, a06,
    ))

    # A07 — Forge a complete GCR from scratch (no content_hash, no signature)
    def a07(_gcr):
        forged = {
            "gcr_id":                     f"OMNIX-GCR-FORGED{uuid.uuid4().hex[:8].upper()}",
            "receiving_runtime_id":       "OMNIX-RUNTIME-ATTACKER",
            "rsa_ids":                    ["OMNIX-RSA-FAKE001", "OMNIX-RSA-FAKE002"],
            "receipt_ids":                ["DR-FAKE-001", "DR-FAKE-002"],
            "n_assessments":              2,
            "verdict_distribution":       {_V_PORTABLE: 2},
            "composite_verdict":          "FULL_RELIANCE",
            "dominant_sdu":               0.01,
            "mean_sdu":                   0.01,
            "min_portability_confidence": 0.99,
            "boundary_recommendation":    "Forged — attacker-generated GCR",
            "converged_at":               "2026-01-01T00:00:00+00:00",
            "created_at":                 "2026-01-01T00:00:00+00:00",
        }
        return forged

    results.append(_attack(
        "A07",
        "GCR Forgery — complete fabrication without content_hash",
        "Construct a GCR from scratch with FULL_RELIANCE verdict. "
        "No content_hash field present → required field check and hash check fail.",
        "REFUSED", scenarios, a07,
    ))

    # A08 — Mutate verdict AND re-compute content_hash with a fake key
    # (attacker computes a valid-looking content_hash but cannot forge the PQC signature)
    def a08(gcr):
        gcr["composite_verdict"] = "FULL_RELIANCE"
        # Attacker re-computes content_hash to make it consistent
        gcr["content_hash"] = _compute_hash(gcr)
        # But cannot produce a valid ML-DSA-65 signature — clears it
        gcr["pqc_signature"] = None
        return gcr

    results.append(_attack(
        "A08",
        "Re-hash Attack — mutate verdict + re-compute hash, drop PQC signature",
        "Flip composite_verdict on ESCALATION GCR, recompute content_hash to match. "
        "Drops pqc_signature. Algorithm re-derivation catches verdict ≠ distribution.",
        "ESCALATION", scenarios, a08,
    ))

    return results

# ---------------------------------------------------------------------------
# Terminal reporting
# ---------------------------------------------------------------------------

def _print_banner(quiet: bool) -> None:
    if quiet:
        return
    print()
    print(wht("  ╔══════════════════════════════════════════════════════════════════╗"))
    print(wht("  ║") + mag("  OMNIX QUANTUM — GDCL Adversarial Audit v1.0.0                   ") + wht("║"))
    print(wht("  ║") + dim("  8 attack vectors · GDCLConvergenceRecord integrity · ADR-206      ") + wht("║"))
    print(wht("  ╚══════════════════════════════════════════════════════════════════╝"))
    print()

def _print_result(r: AttackResult, quiet: bool) -> None:
    if quiet:
        return
    status = r["status"]
    if status == "DETECTED":
        badge = grn("■ DETECTED")
    elif status == "EVADED":
        badge = red("■ EVADED  ")
    else:
        badge = yel("■ SKIP    ")

    print(f"  {badge}  [{r['attack_id']}] {wht(r['title'])}")
    print(f"            {dim('Target:')} {r['target_verdict']} — {dim(r.get('target_label', ''))}")
    print(f"            {dim('Technique:')} {r['technique']}")
    if r["findings"]:
        for f in r["findings"]:
            print(f"            {dim('→')} {dim(f)}")
    print()

def _print_summary(results: List[AttackResult], quiet: bool) -> None:
    if quiet:
        return
    n_detected = sum(1 for r in results if r["status"] == "DETECTED")
    n_evaded   = sum(1 for r in results if r["status"] == "EVADED")
    n_skip     = sum(1 for r in results if r["status"] == "SKIP")
    n_total    = len(results)

    print(f"  {dim('─' * 68)}")
    print()
    print(f"  {dim('Attacks attempted:')} {n_total - n_skip}")
    print(f"  {grn('Detected:  ')} {n_detected}/{n_total - n_skip}")
    if n_evaded > 0:
        print(f"  {red('Evaded:    ')} {n_evaded}/{n_total - n_skip}  {red('← AUDIT FINDINGS')}")
    else:
        print(f"  {dim('Evaded:    ')} 0/{n_total - n_skip}  ← no evasions")
    if n_skip > 0:
        print(f"  {yel('Skipped:   ')} {n_skip} (GCR not found in package)")
    print()

    if n_evaded == 0:
        print(f"  {grn('AUDIT RESULT: PASS')} — all attacks detected, 0 evasions")
        print(f"  {dim('The GDCL integrity model correctly detects every tested manipulation.')}")
    else:
        print(f"  {red('AUDIT RESULT: FAIL')} — {n_evaded} attack(s) evaded detection")
        print(f"  {red('These evasions are audit findings requiring remediation.')}")
    print()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="GDCL Adversarial Audit — 8 attack vectors against GCR integrity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/gdcl_adversarial_audit.py --package evidence_packages/gdcl_evidence_package_*.json\n"
            "  python scripts/gdcl_adversarial_audit.py --package pkg.json --json\n\n"
            "Generate a fresh package first:\n"
            "  python scripts/generate_gdcl_evidence_package.py\n\n"
            "Exit codes:\n"
            "  0  All attacks detected (audit PASS)\n"
            "  1  One or more attacks evaded (audit FAIL — findings present)\n"
            "  2  Package not found or invalid JSON"
        ),
    )
    parser.add_argument("--package", "-p", metavar="PATH", required=True,
                        help="Path to GDCL evidence package JSON")
    parser.add_argument("--json", action="store_true",
                        help="Output machine-readable JSON result")
    args = parser.parse_args()

    path = Path(args.package)
    if not path.exists():
        print(red(f"Error: package not found: {path}"), file=sys.stderr)
        return 2

    try:
        with open(path, encoding="utf-8") as f:
            package = json.load(f)
    except json.JSONDecodeError as exc:
        print(red(f"Error: invalid JSON: {exc}"), file=sys.stderr)
        return 2

    scenarios = package.get("scenarios", [])
    if not scenarios:
        print(red("Error: no scenarios found in package"), file=sys.stderr)
        return 2

    _print_banner(args.json)

    if not args.json:
        pkg_id  = package.get("package_id", "?")
        n_scens = len(scenarios)
        print(f"  {dim('Package:')} {pkg_id}")
        print(f"  {dim('Scenarios:')} {n_scens}  {dim('Verdicts:')} "
              f"{', '.join(s.get('verdict','?') for s in scenarios)}")
        print()

    results = _run_all_attacks(scenarios)

    if args.json:
        n_detected = sum(1 for r in results if r["status"] == "DETECTED")
        n_evaded   = sum(1 for r in results if r["status"] == "EVADED")
        print(json.dumps({
            "audit_tool":    "gdcl_adversarial_audit.py",
            "version":       "1.0.0",
            "adr_reference": "ADR-206",
            "package_id":    package.get("package_id"),
            "n_attacks":     len(results),
            "n_detected":    n_detected,
            "n_evaded":      n_evaded,
            "audit_pass":    n_evaded == 0,
            "attacks":       results,
        }, indent=2))
    else:
        for r in results:
            _print_result(r, False)
        _print_summary(results, False)

    n_evaded = sum(1 for r in results if r["status"] == "EVADED")
    return 0 if n_evaded == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
