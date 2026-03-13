"""
OMNIX GovernanceEvaluationEngine — Domain-agnostic 8-checkpoint signal evaluator.

Accepts normalized governance signals from any domain (trading, credit, supply chain,
insurance, etc.) and runs them through the same fail-closed 8-checkpoint pipeline
used internally by the OMNIX trading engine.

ADR-028: External Signal Evaluation API
ADR-026: Multi-Vertical Governance Architecture (Domain Adapter Pattern)
ADR-037: Per-Client Configurable Thresholds
"""

import logging
from typing import Any

logger = logging.getLogger("OMNIX.Governance")

# Safety floors: absolute min/max each client is allowed to set per checkpoint.
# Prevents clients from disabling governance by setting trivially permissive thresholds.
# operator 'gte' checkpoints: threshold cannot be below min (would make it too easy to pass)
# operator 'lte' checkpoints: threshold cannot be above max (would make it too easy to pass)
# ADR-037
CHECKPOINT_SAFETY_FLOORS: dict[str, dict[str, float]] = {
    "CP-0": {"min": 40.0, "max": 95.0},
    "CP-1": {"min": 30.0, "max": 90.0},
    "CP-2": {"min": 40.0, "max": 85.0},
    "CP-3": {"min": 30.0, "max": 90.0},
    "CP-4": {"min": 25.0, "max": 90.0},
    "CP-5": {"min": 20.0, "max": 80.0},
    "CP-6": {"min": 20.0, "max": 80.0},
    "CP-7": {"min": 30.0, "max": 85.0},
}

# Required signals — must always be present in client payloads
REQUIRED_SIGNALS = [
    "probability_score",
    "risk_exposure",
    "signal_coherence",
    "trend_persistence",
    "stress_resilience",
    "logic_consistency",
]

# Optional signals — if omitted, a conservative default is applied
OPTIONAL_SIGNAL_DEFAULTS: dict[str, float] = {
    "signal_integrity": 75.0,
    "temporal_coherence": 65.0,
}


def validate_threshold_against_floor(checkpoint_id: str, threshold: float) -> tuple[bool, str]:
    """
    Validate a client-provided threshold against CHECKPOINT_SAFETY_FLOORS.
    Returns (is_valid, error_message).
    """
    floors = CHECKPOINT_SAFETY_FLOORS.get(checkpoint_id)
    if not floors:
        return False, f"Unknown checkpoint_id: {checkpoint_id}"
    if threshold < floors["min"] or threshold > floors["max"]:
        return False, (
            f"{checkpoint_id} threshold must be between {floors['min']} and {floors['max']}, "
            f"got {threshold}"
        )
    return True, ""

CHECKPOINT_DEFAULTS = [
    {
        "id": "CP-0",
        "name": "Signal Integrity Validation",
        "signal": "signal_integrity",
        "operator": "gte",
        "threshold": 60,
        "optional": True,
        "description": "Pre-pipeline data quality gate. Validates that incoming signals are structurally coherent and free from integrity anomalies.",
    },
    {
        "id": "CP-1",
        "name": "Probability Check",
        "signal": "probability_score",
        "operator": "gte",
        "threshold": 50,
        "optional": False,
        "description": "Expected positive outcome probability must meet minimum threshold.",
    },
    {
        "id": "CP-2",
        "name": "Risk Limits",
        "signal": "risk_exposure",
        "operator": "lte",
        "threshold": 65,
        "optional": False,
        "description": "Risk exposure must remain within acceptable bounds. Lower is safer.",
    },
    {
        "id": "CP-3",
        "name": "Signal Coherence",
        "signal": "signal_coherence",
        "operator": "gte",
        "threshold": 55,
        "optional": False,
        "description": "Internal signal agreement must exceed coherence minimum.",
    },
    {
        "id": "CP-4",
        "name": "Trend Persistence",
        "signal": "trend_persistence",
        "operator": "gte",
        "threshold": 50,
        "optional": False,
        "description": "Detected trend must show sufficient temporal persistence.",
    },
    {
        "id": "CP-5",
        "name": "Stress Resilience",
        "signal": "stress_resilience",
        "operator": "gte",
        "threshold": 35,
        "optional": False,
        "description": "Decision must withstand adverse scenario stress testing.",
    },
    {
        "id": "CP-6",
        "name": "Logic Consistency",
        "signal": "logic_consistency",
        "operator": "gte",
        "threshold": 40,
        "optional": False,
        "description": "Internal signal logic must not contain structural contradictions.",
    },
    {
        "id": "CP-7",
        "name": "Temporal Coherence",
        "signal": "temporal_coherence",
        "operator": "gte",
        "threshold": 45,
        "optional": True,
        "description": "Forward-backward trajectory agreement. Evaluates whether the decision holds consistency across time horizons.",
    },
]


class GovernanceEvaluationEngine:
    """
    Domain-agnostic 8-checkpoint governance evaluator.

    Takes normalized governance signals (0-100 scale, domain-independent)
    and evaluates them through a fail-closed checkpoint pipeline. Any gate
    failure results in a BLOCKED decision — no override path exists.

    Required Signal Schema:
        probability_score   (0-100): Probability of positive outcome
        risk_exposure       (0-100): Risk level — lower is safer
        signal_coherence    (0-100): Agreement between internal signals
        trend_persistence   (0-100): Temporal persistence of detected trend
        stress_resilience   (0-100): Resilience under adverse scenarios
        logic_consistency   (0-100): Absence of internal contradictions

    Optional Signal Schema (conservative defaults applied when omitted):
        signal_integrity    (0-100): Pre-pipeline data quality score [default: 75]
        temporal_coherence  (0-100): Forward-backward trajectory agreement [default: 65]
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
        Run the 8-checkpoint evaluation pipeline on normalized signals.

        Returns:
            {
                decision: "APPROVED" | "BLOCKED",
                asset: str,
                domain: str,
                gate_results: list[dict],
                veto_chain: list[str],
                scores: dict[str, float],
                decision_trace: list[str],
                metadata: dict,
                checkpoints_total: int,
                checkpoints_passed: int,
                checkpoints_blocked: int
            }
        """
        metadata = metadata or {}
        gate_results = []
        veto_chain = []
        decision_trace = []
        overall_blocked = False

        resolved_signals = dict(signals)
        for opt_signal, default_val in OPTIONAL_SIGNAL_DEFAULTS.items():
            if opt_signal not in resolved_signals:
                resolved_signals[opt_signal] = default_val

        for cp in self.checkpoints:
            signal_name = cp["signal"]
            threshold = cp["threshold"]
            operator = cp["operator"]
            score = resolved_signals.get(signal_name, 0.0)

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
                "optional": cp.get("optional", False),
            })

            trace_entry = f"{cp['id']} {cp['name']}: {condition_str} → {result}"
            decision_trace.append(trace_entry)
            logger.debug(trace_entry)

            if not passed:
                overall_blocked = True
                veto_chain.append({
                    "checkpoint_id": cp["id"],
                    "checkpoint_name": cp["name"],
                    "signal": signal_name,
                    "score": score,
                    "threshold": threshold,
                    "result": "VETO",
                })

        decision = "BLOCKED" if overall_blocked else "APPROVED"

        all_signals = list(REQUIRED_SIGNALS) + list(OPTIONAL_SIGNAL_DEFAULTS.keys())
        return {
            "decision": decision,
            "asset": asset,
            "domain": domain,
            "gate_results": gate_results,
            "veto_chain": veto_chain,
            "scores": {s: resolved_signals.get(s, 0.0) for s in all_signals},
            "decision_trace": decision_trace,
            "metadata": metadata,
            "checkpoints_total": len(self.checkpoints),
            "checkpoints_passed": sum(1 for g in gate_results if g["result"] == "PASS"),
            "checkpoints_blocked": sum(1 for g in gate_results if g["result"] == "BLOCKED"),
        }

    @staticmethod
    def validate_signals(signals: dict) -> tuple[bool, str]:
        """
        Validate that input signals contain all required fields with values in [0, 100].
        Optional signals (signal_integrity, temporal_coherence) are validated if present.

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

        for field in OPTIONAL_SIGNAL_DEFAULTS:
            if field in signals:
                val = signals[field]
                if not isinstance(val, (int, float)):
                    return False, f"Signal '{field}' must be a number, got {type(val).__name__}"
                if not (0 <= val <= 100):
                    return False, f"Signal '{field}' must be between 0 and 100, got {val}"

        return True, ""

    @staticmethod
    def get_signal_schema() -> dict:
        """Return the signal schema for client documentation."""
        required = {}
        optional = {}
        for cp in CHECKPOINT_DEFAULTS:
            entry = {
                "range": "0-100",
                "checkpoint": cp["id"],
                "checkpoint_name": cp["name"],
                "threshold": cp["threshold"],
                "pass_condition": f"{'>=' if cp['operator'] == 'gte' else '<='} {cp['threshold']}",
                "description": cp["description"],
            }
            if cp.get("optional"):
                entry["default"] = OPTIONAL_SIGNAL_DEFAULTS.get(cp["signal"], "N/A")
                optional[cp["signal"]] = entry
            else:
                required[cp["signal"]] = entry

        return {
            "required_signals": required,
            "optional_signals": optional,
            "other_optional_fields": {
                "asset": "string — asset identifier (e.g. 'BTC/USD', 'LOAN-2847', 'CLAIM-99A')",
                "domain": "string — evaluation domain (e.g. 'trading', 'credit', 'insurance')",
                "metadata": "object — arbitrary client metadata, stored in receipt",
            },
            "decision_values": ["APPROVED", "BLOCKED"],
            "fail_closed": True,
            "pqc_signed": True,
            "pqc_algorithm": "Dilithium-3 (ML-DSA-65)",
            "checkpoints_total": 8,
        }
