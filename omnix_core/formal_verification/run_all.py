"""
OMNIX QUANTUM — Formal Verification Suite Runner
=================================================
Executes all Z3 SMT proofs across all four protocol modules and produces
a machine-readable JSON proof report.

Usage
-----
    python -m omnix_core.formal_verification.run_all
    python -m omnix_core.formal_verification.run_all --json > proof_report.json
    python -m omnix_core.formal_verification.run_all --strict  # exit 1 on any failure

Output Format
-------------
{
  "suite": "OMNIX-FVS-1.0",
  "generated_at": "...",
  "protocol": "ATF Open Standard (RFC-ATF-1 thru RFC-ATF-4)",
  "solver": "Z3 SMT Solver",
  "total": 19,
  "proved": 19,
  "failed": 0,
  "unknown": 0,
  "all_proved": true,
  "modules": { ... },
  "proofs": [ ... ]
}

Reference: ADR-177 — OMNIX Formal Verification Suite
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import z3

from omnix_core.formal_verification.atf_invariants_z3 import (
    prove_acyclicity_three_node,
    prove_budget_ceiling,
    prove_mar_invariant,
)
from omnix_core.formal_verification.agv_invariants_z3 import (
    prove_agv_inv001_authority_equivalence,
    prove_agv_inv003_minimum_interval,
    prove_agv_inv004_hash_commitment,
    prove_agv_inv005_no_veto_without_baseline,
    prove_agv_inv006_recalibration_freeze,
)
from omnix_core.formal_verification.ssd_invariants_z3 import (
    prove_crsi_classification_totality,
    prove_crsi_lower_bound,
    prove_crsi_upper_bound,
    prove_ssd_inv001_shift_blocks_recalibration,
    prove_ssd_inv003_minimum_history,
)
from omnix_core.formal_verification.dspp_invariants_z3 import (
    prove_dspp_inv005_rsa_determinism,
    prove_dspp_inv007_threshold_exclusivity,
    prove_dspp_inv007_threshold_partition,
    prove_sdu_lower_bound,
    prove_sdu_upper_bound,
    prove_sdu_weighted_sum_bounds,
)

SUITE_VERSION = "OMNIX-FVS-1.0"

ALL_PROOF_FUNCTIONS = [
    # ATF Layer — RFC-ATF-1 / RFC-ATF-2
    prove_mar_invariant,
    prove_budget_ceiling,
    prove_acyclicity_three_node,
    # AGVP Layer — RFC-ATF-4
    prove_agv_inv001_authority_equivalence,
    prove_agv_inv003_minimum_interval,
    prove_agv_inv004_hash_commitment,
    prove_agv_inv005_no_veto_without_baseline,
    prove_agv_inv006_recalibration_freeze,
    # SSD Layer — RFC-ATF-4
    prove_crsi_lower_bound,
    prove_crsi_upper_bound,
    prove_crsi_classification_totality,
    prove_ssd_inv001_shift_blocks_recalibration,
    prove_ssd_inv003_minimum_history,
    # DSPP Layer — RFC-ATF-4
    prove_sdu_lower_bound,
    prove_sdu_upper_bound,
    prove_sdu_weighted_sum_bounds,
    prove_dspp_inv005_rsa_determinism,
    prove_dspp_inv007_threshold_partition,
    prove_dspp_inv007_threshold_exclusivity,
]

MODULE_MAP = {
    "ATF-INV": "atf_invariants_z3",
    "RGC-INV": "atf_invariants_z3",
    "AGV-INV": "agv_invariants_z3",
    "CRSI": "ssd_invariants_z3",
    "SSD-INV": "ssd_invariants_z3",
    "SDU": "dspp_invariants_z3",
    "DSPP-INV": "dspp_invariants_z3",
}


def run_all_proofs() -> dict[str, Any]:
    """Execute all proofs and return a structured report."""
    t_start = time.perf_counter()
    results = []

    for fn in ALL_PROOF_FUNCTIONS:
        record = fn()
        results.append(record)

    elapsed_total = round((time.perf_counter() - t_start) * 1000, 1)

    proved = [r for r in results if r.proved]
    failed = [r for r in results if r.result == "SAT"]
    unknown = [r for r in results if r.result == "UNKNOWN"]

    modules: dict[str, dict] = {}
    for r in results:
        prefix = r.invariant_id.split("-INV")[0] + "-INV" if "-INV" in r.invariant_id else r.invariant_id.split("-")[0]
        mod = MODULE_MAP.get(prefix, "unknown")
        if mod not in modules:
            modules[mod] = {"proved": 0, "failed": 0, "invariants": []}
        modules[mod]["proved" if r.proved else "failed"] += 1
        modules[mod]["invariants"].append(r.invariant_id)

    report = {
        "suite": SUITE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "solver": f"Z3 {z3.get_version_string()}",
        "protocol": "OMNIX ATF Open Standard (RFC-ATF-1 · RFC-ATF-2 · RFC-ATF-3 · RFC-ATF-4)",
        "methodology": "Negation refutation: UNSAT ≡ invariant formally proved",
        "total": len(results),
        "proved": len(proved),
        "failed": len(failed),
        "unknown": len(unknown),
        "all_proved": len(failed) == 0 and len(unknown) == 0,
        "total_elapsed_ms": elapsed_total,
        "modules": modules,
        "proofs": [
            {
                "invariant_id": r.invariant_id,
                "invariant_name": r.invariant_name,
                "result": r.result,
                "proved": r.proved,
                "elapsed_ms": r.elapsed_ms,
                "description": r.description,
                "negation_asserted": r.negation_asserted,
                "adr_reference": r.adr_reference,
                "rfc_reference": r.rfc_reference,
                "model_counterexample": r.model_counterexample,
            }
            for r in results
        ],
    }

    return report


def print_human_report(report: dict[str, Any]) -> None:
    """Print a human-readable summary of the proof report."""
    width = 72
    print("=" * width)
    print(f"  OMNIX QUANTUM — Formal Verification Suite  {SUITE_VERSION}")
    print(f"  {report['protocol']}")
    print(f"  Solver: {report['solver']}")
    print(f"  Generated: {report['generated_at']}")
    print("=" * width)
    print()

    for proof in report["proofs"]:
        status = "✓ PROVED" if proof["proved"] else ("✗ FAILED" if proof["result"] == "SAT" else "? UNKNOWN")
        inv_id = proof["invariant_id"].ljust(20)
        name = proof["invariant_name"][:42].ljust(42)
        ms = f"{proof['elapsed_ms']:.1f}ms"
        print(f"  [{status}]  {inv_id} {name}  {ms}")
        if proof["model_counterexample"]:
            print(f"             COUNTEREXAMPLE: {proof['model_counterexample']}")

    print()
    print("-" * width)
    all_ok = report["all_proved"]
    verdict = "ALL INVARIANTS FORMALLY PROVED" if all_ok else "PROOF FAILURES DETECTED"
    print(f"  {verdict}")
    print(f"  {report['proved']}/{report['total']} proved · {report['total_elapsed_ms']}ms total")
    print("=" * width)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OMNIX Formal Verification Suite — Z3 SMT proof runner"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON report to stdout")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any proof fails")
    parser.add_argument("--output", type=str, help="Write JSON report to file")
    args = parser.parse_args()

    report = run_all_proofs()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human_report(report)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        if not args.json:
            print(f"\nReport written to: {args.output}")

    if args.strict and not report["all_proved"]:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
