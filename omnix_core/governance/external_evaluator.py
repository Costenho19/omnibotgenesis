"""
OMNIX GovernanceEvaluationEngine — Domain-agnostic 6-checkpoint signal evaluator.

Accepts normalized governance signals from any domain (trading, credit, supply chain,
insurance, etc.) and runs them through the same fail-closed 6-checkpoint pipeline
used internally by the OMNIX trading engine.

ADR-028: External Signal Evaluation API
ADR-026: Multi-Vertical Governance Architecture (Domain Adapter Pattern)
"""

import logging
from typing import Any

logger = logging.getLogger("OMNIX.Governance")

CHECKPOINT_DEFAULTS = [
    {
        "id": "CP-1",
        "name": "Probability Check",
        "signal": "probability_score",
        "operator": "gte",
        "threshold": 50,
        "description": "Expected positive outcome probability must meet minimum threshold.",
    },
    {
        "id": "CP-2",
        "name": "Risk Limits",
        "signal": "risk_exposure",
        "operator": "lte",
        "threshold": 65,
        "description": "Risk exposure must remain within acceptable bounds. Lower is safer.",
    },
    {
        "id": "CP-3",
        "name": "Signal Coherence",
        "signal": "signal_coherence",
        "operator": "gte",
        "threshold": 55,
        "description": "Internal signal agreement must exceed coherence minimum.",
    },
    {
        "id": "CP-4",
        "name": "Trend Persistence",
        "signal": "trend_persistence",
        "operator": "gte",
        "threshold": 50,
        "description": "Detected trend must show sufficient temporal persistence.",
    },
    {
        "id": "CP-5",
        "name": "Stress Resilience",
        "signal": "stress_resilience",
        "operator": "gte",
        "threshold": 35,
        "description": "Decision must withstand adverse scenario stress testing.",
    },
    {
        "id": "CP-6",
        "name": "Logic Consistency",
        "signal": "logic_consistency",
        "operator": "gte",
        "threshold": 40,
        "description": "Internal signal logic must not contain structural contradictions.",
    },
]

REQUIRED_SIGNALS = [cp["signal"] for cp in CHECKPOINT_DEFAULTS]


class GovernanceEvaluationEngine:
    """
    Domain-agnostic 6-checkpoint governance evaluator.

    Takes normalized governance signals (0-100 scale, domain-independent)
    and evaluates them through a fail-closed checkpoint pipeline. Any gate
    failure results in a BLOCKED decision — no override path exists.

    Signal Schema:
        probability_score   (0-100): Probability of positive outcome
        risk_exposure       (0-100): Risk level — lower is safer
        signal_coherence    (0-100): Agreement between internal signals
        trend_persistence   (0-100): Temporal persistence of detected trend
        stress_resilience   (0-100): Resilience under adverse scenarios
        logic_consistency   (0-100): Absence of internal contradictions
    """

    def __init__(self, checkpoint_overrides: list | None = None):
        self.checkpoints = checkpoint_overrides or CHECKPOINT_DEFAULTS

    def evaluate(
        self,
        signals: dict[str, float],
        asset: str = "UNKNOWN",
        domain: str = "generic",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run the 6-checkpoint evaluation pipeline on normalized signals.

        Returns:
            {
                decision: "APPROVED" | "BLOCKED",
                asset: str,
                domain: str,
                gate_results: list[dict],
                veto_chain: list[str],
                scores: dict[str, float],
                decision_trace: list[str],
                metadata: dict
            }
        """
        metadata = metadata or {}
        gate_results = []
        veto_chain = []
        decision_trace = []
        overall_blocked = False

        for cp in self.checkpoints:
            signal_name = cp["signal"]
            threshold = cp["threshold"]
            operator = cp["operator"]
            score = signals.get(signal_name, 0.0)

            if operator == "gte":
                passed = score >= threshold
                condition_str = f"{score:.1f} ≥ {threshold}"
            elif operator == "lte":
                passed = score <= threshold
                condition_str = f"{score:.1f} ≤ {threshold}"
            else:
                passed = False
                condition_str = f"unknown operator: {operator}"

            result = "PASS" if passed else "BLOCKED"
            gate_results.append({
                "checkpoint": cp["id"],
                "name": cp["name"],
                "signal": signal_name,
                "score": score,
                "threshold": threshold,
                "condition": condition_str,
                "result": result,
                "description": cp["description"],
            })

            trace_entry = f"{cp['id']} {cp['name']}: {condition_str} → {result}"
            decision_trace.append(trace_entry)
            logger.debug(trace_entry)

            if not passed:
                overall_blocked = True
                veto_chain.append(f"{cp['id']}:{cp['name']}")

        decision = "BLOCKED" if overall_blocked else "APPROVED"

        return {
            "decision": decision,
            "asset": asset,
            "domain": domain,
            "gate_results": gate_results,
            "veto_chain": veto_chain,
            "scores": {s: signals.get(s, 0.0) for s in REQUIRED_SIGNALS},
            "decision_trace": decision_trace,
            "metadata": metadata,
            "checkpoints_total": len(self.checkpoints),
            "checkpoints_passed": sum(1 for g in gate_results if g["result"] == "PASS"),
            "checkpoints_blocked": len(veto_chain),
        }

    @staticmethod
    def validate_signals(signals: dict) -> tuple[bool, str]:
        """
        Validate that input signals contain all required fields with values in [0, 100].

        Returns:
            (is_valid: bool, error_message: str)
        """
        if not isinstance(signals, dict):
            return False, "signals must be a JSON object"

        for field in REQUIRED_SIGNALS:
            if field not in signals:
                return False, f"Missing required signal: '{field}'"
            val = signals[field]
            if not isinstance(val, (int, float)):
                return False, f"Signal '{field}' must be a number, got {type(val).__name__}"
            if not (0 <= val <= 100):
                return False, f"Signal '{field}' must be between 0 and 100, got {val}"

        return True, ""

    @staticmethod
    def get_signal_schema() -> dict:
        """Return the signal schema for client documentation."""
        return {
            "required_signals": {
                cp["signal"]: {
                    "range": "0-100",
                    "checkpoint": cp["id"],
                    "checkpoint_name": cp["name"],
                    "threshold": cp["threshold"],
                    "pass_condition": f"{'>=' if cp['operator'] == 'gte' else '<='} {cp['threshold']}",
                    "description": cp["description"],
                }
                for cp in CHECKPOINT_DEFAULTS
            },
            "optional_fields": {
                "asset": "string — asset identifier (e.g. 'BTC/USD', 'LOAN-2847', 'CLAIM-99A')",
                "domain": "string — evaluation domain (e.g. 'trading', 'credit', 'insurance')",
                "metadata": "object — arbitrary client metadata, stored in receipt",
            },
            "decision_values": ["APPROVED", "BLOCKED"],
            "fail_closed": True,
            "pqc_signed": True,
            "pqc_algorithm": "Dilithium-3 (ML-DSA-65)",
        }
