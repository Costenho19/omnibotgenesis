"""
OMNIX Governance Simulation — Skilligen HDI Collaboration
Domain: Life Insurance Underwriting
Scenario Author: Dr. Amanulla Khan, Skilligen HDI
Simulation Executed by: Harold Alberto Nunes Rodelo, OMNIX Quantum Ltd
Date: 2026-04-22

Scenario:
    Mid-level underwriting team processing borderline-risk life insurance
    applications near quarter-end under increasing operational pressure.

    Four decision scenarios with identical applicant profiles but varying
    pressure and override conditions — to identify where admissibility
    breaks under operational stress.
"""

import sys
import os
import json
import hashlib
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omnix_core.insurance.insurance_signal_adapter import (
    InsuranceSignalAdapter,
    InsuranceClaimInput,
)
from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine

adapter = InsuranceSignalAdapter()
engine  = GovernanceEvaluationEngine()

SCENARIOS = [
    {
        "id": "SCN-A",
        "label": "Baseline — No Pressure",
        "description": (
            "Same borderline applicant. Standard review process. "
            "Full evidence documentation. No escalation pressure. "
            "Represents the control condition."
        ),
        "claim": InsuranceClaimInput(
            claimant_type="Individual",
            insurance_type="Life",
            region="EU",
            claim_amount_usd=420_000,
            policy_limit_usd=500_000,
            claimant_history_score=72.0,
            fraud_indicators=12.0,
            evidence_completeness=85.0,
            loss_ratio_trend=68.0,
            reserve_adequacy=80.0,
            policy_claim_alignment=78.0,
            incident_days_ago=21,
            prior_claims_count=0,
            is_catastrophe_event=False,
        ),
    },
    {
        "id": "SCN-B",
        "label": "Moderate Pressure — Sales Team Pushing",
        "description": (
            "Same applicant profile. Sales manager requesting approval "
            "to meet quarterly premium target. Evidence review partially "
            "expedited. Threshold interpretation relaxed informally."
        ),
        "claim": InsuranceClaimInput(
            claimant_type="Individual",
            insurance_type="Life",
            region="EU",
            claim_amount_usd=420_000,
            policy_limit_usd=500_000,
            claimant_history_score=72.0,
            fraud_indicators=22.0,
            evidence_completeness=68.0,
            loss_ratio_trend=58.0,
            reserve_adequacy=72.0,
            policy_claim_alignment=61.0,
            incident_days_ago=21,
            prior_claims_count=0,
            is_catastrophe_event=False,
        ),
    },
    {
        "id": "SCN-C",
        "label": "High Pressure — Escalation + Backlog",
        "description": (
            "Same applicant profile. Underwriting backlog increasing. "
            "Senior sales manager escalation request filed. Evidence "
            "review incomplete. Exception review clause invoked. "
            "Policy-claim alignment degraded by override pressure."
        ),
        "claim": InsuranceClaimInput(
            claimant_type="Individual",
            insurance_type="Life",
            region="EU",
            claim_amount_usd=420_000,
            policy_limit_usd=500_000,
            claimant_history_score=72.0,
            fraud_indicators=38.0,
            evidence_completeness=52.0,
            loss_ratio_trend=44.0,
            reserve_adequacy=60.0,
            policy_claim_alignment=44.0,
            incident_days_ago=21,
            prior_claims_count=0,
            is_catastrophe_event=False,
        ),
    },
    {
        "id": "SCN-D",
        "label": "Quarter-End Peak — Override Behavior Active",
        "description": (
            "Same applicant profile. Quarter-end revenue pressure at peak. "
            "Multiple escalation overrides observed across the team. "
            "Evidence documentation minimal. Exception review invoked "
            "without documented justification. Override pattern flagged."
        ),
        "claim": InsuranceClaimInput(
            claimant_type="Individual",
            insurance_type="Life",
            region="EU",
            claim_amount_usd=420_000,
            policy_limit_usd=500_000,
            claimant_history_score=72.0,
            fraud_indicators=58.0,
            evidence_completeness=35.0,
            loss_ratio_trend=28.0,
            reserve_adequacy=45.0,
            policy_claim_alignment=28.0,
            incident_days_ago=21,
            prior_claims_count=0,
            is_catastrophe_event=False,
        ),
    },
]

SEPARATOR = "=" * 72

def run_simulation():
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    results = []

    print(SEPARATOR)
    print("OMNIX QUANTUM — GOVERNANCE SIMULATION")
    print("Skilligen HDI · Life Insurance Underwriting")
    print(f"Executed: {timestamp}")
    print(f"Engine:   GovernanceEvaluationEngine · 11-Checkpoint Pipeline")
    print(f"Adapter:  InsuranceSignalAdapter · ADR-054")
    print(SEPARATOR)

    prev_hash = "0000000000000000"

    for scn in SCENARIOS:
        signals_obj = adapter.adapt(scn["claim"])
        signals     = signals_obj.to_omnix_dict()
        result      = engine.evaluate(
            signals=signals,
            asset=f"LIFE-UW-{scn['id']}",
            domain="life_insurance_underwriting",
            metadata={
                "scenario_id":   scn["id"],
                "scenario_label": scn["label"],
                "pressure_level": scn["id"],
            },
        )

        payload = json.dumps({
            "scenario_id":   scn["id"],
            "decision":      result["decision"],
            "signals":       signals,
            "gate_results":  result["gate_results"],
            "timestamp":     timestamp,
        }, sort_keys=True)
        content_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]

        record = {
            "scenario_id":         scn["id"],
            "label":               scn["label"],
            "description":         scn["description"],
            "signals":             signals,
            "recommendation":      signals_obj.recommendation,
            "decision":            result["decision"],
            "checkpoints_total":   result["checkpoints_total"],
            "checkpoints_passed":  result["checkpoints_passed"],
            "checkpoints_blocked": result["checkpoints_blocked"],
            "gate_results":        result["gate_results"],
            "veto_chain":          result["veto_chain"],
            "content_hash":        content_hash,
            "prev_hash":           prev_hash,
            "timestamp":           timestamp,
        }
        results.append(record)
        prev_hash = content_hash

        decision_symbol = "✅ APPROVED" if result["decision"] == "APPROVED" else "🔴 BLOCKED"

        print(f"\n{scn['id']} — {scn['label']}")
        print(f"  {scn['description']}")
        print(f"\n  Governance Signals:")
        for k, v in signals.items():
            print(f"    {k:<25} {v:.2f}")
        print(f"\n  Pipeline Result:  {decision_symbol}")
        print(f"  Checkpoints:      {result['checkpoints_passed']}/{result['checkpoints_total']} passed")

        if result["veto_chain"]:
            print(f"\n  Veto Chain:")
            for veto in result["veto_chain"]:
                print(f"    ⛔  {veto}")

        print(f"\n  Checkpoint Detail:")
        for gate in result["gate_results"]:
            status = gate.get("result", "UNKNOWN")
            passed = status == "PASS"
            symbol = "✓" if passed else "✗"
            score  = gate.get("score", 0.0)
            cp_id  = gate.get("checkpoint", gate.get("id", "?"))
            name   = gate.get("name", "")
            thresh = gate.get("threshold", 0)
            print(f"    {symbol} {cp_id} {name:<30}  "
                  f"score={score:.1f}  threshold={thresh}  [{status}]")

        print(f"\n  Content Hash:  {content_hash}")
        print(f"  Prev Hash:     {prev_hash if prev_hash != content_hash else '(genesis)'}")
        print(f"\n{'-' * 72}")

    print(f"\n{'=' * 72}")
    print("SIMULATION SUMMARY")
    print(f"{'=' * 72}")
    print(f"{'Scenario':<10} {'Label':<42} {'Decision':<10} {'Pass Rate'}")
    print(f"{'-' * 72}")
    for r in results:
        rate = f"{r['checkpoints_passed']}/{r['checkpoints_total']}"
        print(f"{r['scenario_id']:<10} {r['label'][:42]:<42} {r['decision']:<10} {rate}")

    blocked = [r for r in results if r["decision"] == "BLOCKED"]
    approved = [r for r in results if r["decision"] == "APPROVED"]

    print(f"\nApproved:  {len(approved)}")
    print(f"Blocked:   {len(blocked)}")

    if blocked:
        first_block = None
        for r in results:
            if r["decision"] == "BLOCKED":
                first_block = r
                break
        print(f"\nAdmissibility Breakpoint: {first_block['scenario_id']} — {first_block['label']}")
        print(f"  First veto: {first_block['veto_chain'][0] if first_block['veto_chain'] else 'see gate results'}")

    print(f"\nHash Chain Integrity:")
    for r in results:
        print(f"  {r['scenario_id']}  {r['content_hash']}")

    print(f"\nTimestamp: {timestamp}")
    print(f"Engine:    OMNIX GovernanceEvaluationEngine v6.5.4e")
    print(f"Domain:    life_insurance_underwriting")
    print(f"Verify:    omnixquantum.net/verify")
    print("=" * 72)

    return results

if __name__ == "__main__":
    run_simulation()
