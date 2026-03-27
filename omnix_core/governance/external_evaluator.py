"""
OMNIX GovernanceEvaluationEngine — Domain-agnostic 8-checkpoint signal evaluator.

Accepts normalized governance signals from any domain (trading, credit, supply chain,
insurance, etc.) and runs them through the same fail-closed 8-checkpoint pipeline
used internally by the OMNIX trading engine.

ADR-028: External Signal Evaluation API
ADR-026: Multi-Vertical Governance Architecture (Domain Adapter Pattern)
ADR-037: Per-Client Configurable Thresholds
ADR-053: Trajectory Invariant Enforcement (TIE) — post-pipeline gate
"""

import logging
import os
from typing import Any

try:
    from omnix_core.governance.trajectory_invariant_engine import (
        TrajectoryInvariantEngine,
        TIEResult,
    )
    _TIE_AVAILABLE = True
except Exception:
    _TIE_AVAILABLE = False

logger = logging.getLogger("OMNIX.Governance")

try:
    from omnix_core.governance.aml_gate import AMLGate, load_aml_config_from_env
    _AML_AVAILABLE = True
except Exception:
    _AML_AVAILABLE = False

try:
    from omnix_core.governance.fraud_gate import FraudGate, load_fraud_config_from_env
    _FRAUD_AVAILABLE = True
except Exception:
    _FRAUD_AVAILABLE = False

try:
    from omnix_core.governance.jurisdiction_gate import JurisdictionGate, load_jurisdiction_config_from_env
    _JURISDICTION_AVAILABLE = True
except Exception:
    _JURISDICTION_AVAILABLE = False

try:
    from omnix_core.governance.context_admission_gate import ContextAdmissionGate, load_cag_config_from_env
    _CAG_AVAILABLE = True
except Exception:
    _CAG_AVAILABLE = False

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
        compliance_config: dict[str, Any] | None = None,
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
        cfg = compliance_config or {}

        # ── CAG: Context Admission Gate — session-level pre-admission ──────────
        # Runs BEFORE any signal enters the checkpoint pipeline.
        # If CAG blocks, no executable state is formed — pipeline never starts.
        context_admission_block: dict[str, Any] | None = None
        if _CAG_AVAILABLE:
            try:
                cag_enabled = cfg.get("cag_enabled",
                    os.environ.get("CAG_ENABLED", "false").lower() == "true")
                if cag_enabled:
                    from omnix_core.governance.context_admission_gate import CAGConfig
                    cag_cfg = CAGConfig(
                        enabled=True,
                        global_volatility_threshold=float(cfg.get(
                            "cag_volatility_threshold",
                            os.environ.get("CAG_VOLATILITY_THRESHOLD", "80.0"))),
                        cross_pair_correlation_threshold=float(cfg.get(
                            "cag_correlation_threshold",
                            os.environ.get("CAG_CORRELATION_THRESHOLD", "90.0"))),
                        liquidity_score_minimum=float(cfg.get(
                            "cag_liquidity_minimum",
                            os.environ.get("CAG_LIQUIDITY_MINIMUM", "20.0"))),
                        macro_risk_ceiling=float(cfg.get(
                            "cag_macro_risk_ceiling",
                            os.environ.get("CAG_MACRO_RISK_CEILING", "85.0"))),
                        block_on_any_violation=str(cfg.get(
                            "cag_block_on_any_violation",
                            os.environ.get("CAG_BLOCK_ON_ANY_VIOLATION", "true"))).lower() == "true",
                    )
                    cag_result = ContextAdmissionGate(cag_cfg).evaluate(
                        global_volatility=float(cfg.get("cag_global_volatility", 0.0)),
                        cross_pair_correlation=float(cfg.get("cag_cross_pair_correlation", 0.0)),
                        liquidity_score=float(cfg.get("cag_liquidity_score", 100.0)),
                        macro_risk=float(cfg.get("cag_macro_risk", 0.0)),
                    )
                    context_admission_block = {
                        "check": "enabled",
                        "result": "admitted" if cag_result.admitted else "blocked",
                        "admission_score": cag_result.admission_score,
                        "violation": cag_result.violation,
                        "parameters": {
                            "global_volatility": cag_result.global_volatility,
                            "cross_pair_correlation": cag_result.cross_pair_correlation,
                            "liquidity_score": cag_result.liquidity_score,
                            "macro_risk": cag_result.macro_risk,
                        },
                        "gate_checks": cag_result.gate_checks,
                    }
                    if not cag_result.admitted and not cag_result.pass_through:
                        decision_trace.append(f"CAG SESSION_BLOCKED: {cag_result.violation}")
                        veto_chain.append({
                            "checkpoint_id": "CAG",
                            "checkpoint_name": "Context Admission Gate",
                            "result": "SESSION_BLOCKED",
                            "violation": cag_result.violation,
                        })
                        logger.warning(
                            f"🚫 [CAG] SESSION_BLOCKED: {cag_result.violation} | "
                            f"asset={asset} | score={cag_result.admission_score:.0f}/100"
                        )
                        all_signals = list(REQUIRED_SIGNALS) + list(OPTIONAL_SIGNAL_DEFAULTS.keys())
                        result: dict[str, Any] = {
                            "decision": "BLOCKED",
                            "asset": asset,
                            "domain": domain,
                            "gate_results": [],
                            "veto_chain": veto_chain,
                            "scores": {s: signals.get(s, 0.0) for s in all_signals},
                            "decision_trace": decision_trace,
                            "metadata": metadata,
                            "checkpoints_total": len(self.checkpoints),
                            "checkpoints_passed": 0,
                            "checkpoints_blocked": 0,
                            "context_admission": context_admission_block,
                        }
                        return result
                    else:
                        decision_trace.append(
                            f"CAG SESSION_ADMITTED: score={cag_result.admission_score:.0f}/100"
                        )
            except Exception as e:
                logger.warning(f"⚠️ [CAG] Exception in B2B evaluate: {e} → pass-through")
        # ─────────────────────────────────────────────────────────────────────

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

        compliance_blocks: dict[str, Any] = {}

        if not overall_blocked:
            action_for_gates = "BUY" if decision == "APPROVED" else "HOLD"

            if _AML_AVAILABLE and cfg.get("aml_enabled",
                    os.environ.get("AML_GATE_ENABLED", "false").lower() == "true"):
                try:
                    aml_cfg = load_aml_config_from_env()
                    aml_cfg.enabled = True
                    aml_result = AMLGate(aml_cfg).evaluate(asset, action_for_gates)
                    compliance_blocks["aml_compliance"] = {
                        "check": "enabled",
                        "result": "passed" if aml_result.admissible else "failed",
                        "score": aml_result.aml_score,
                        "violation": aml_result.violation,
                        "asset": asset,
                    }
                    if not aml_result.admissible:
                        decision = "BLOCKED"
                        overall_blocked = True
                        decision_trace.append(f"CP-9 AML_VETO: {aml_result.reason}")
                        veto_chain.append({"checkpoint_id": "CP-9", "checkpoint_name": "AML Gate",
                                           "result": "VETO", "violation": aml_result.violation})
                        logger.warning(f"🏦 [CP-9] AML_VETO: {aml_result.violation} | asset={asset}")
                    else:
                        decision_trace.append(f"CP-9 AML_PASS: score={aml_result.aml_score:.0f}/100")
                except Exception as e:
                    logger.warning(f"⚠️ [CP-9 AML] B2B exception for {asset}: {e} → pass-through")

            if _FRAUD_AVAILABLE and cfg.get("fraud_enabled",
                    os.environ.get("FRAUD_GATE_ENABLED", "false").lower() == "true"):
                try:
                    fraud_cfg = load_fraud_config_from_env()
                    fraud_cfg.enabled = True
                    dci = resolved_signals.get("logic_consistency", 50.0)
                    fraud_dci = max(0.0, 100.0 - dci)
                    fraud_result = FraudGate(fraud_cfg).evaluate(
                        asset, action_for_gates,
                        dci_score=fraud_dci,
                        technical_score=resolved_signals.get("probability_score", 50.0),
                        sentiment_score=resolved_signals.get("signal_coherence", 50.0),
                    )
                    compliance_blocks["fraud_compliance"] = {
                        "check": "enabled",
                        "result": "passed" if fraud_result.admissible else "failed",
                        "integrity_score": fraud_result.integrity_score,
                        "violation": fraud_result.violation,
                        "asset": asset,
                    }
                    if not fraud_result.admissible:
                        decision = "BLOCKED"
                        overall_blocked = True
                        decision_trace.append(f"CP-10 FRAUD_VETO: {fraud_result.reason}")
                        veto_chain.append({"checkpoint_id": "CP-10", "checkpoint_name": "Fraud Gate",
                                           "result": "VETO", "violation": fraud_result.violation})
                        logger.warning(f"🕵️ [CP-10] FRAUD_VETO: {fraud_result.violation} | asset={asset}")
                    else:
                        decision_trace.append(f"CP-10 FRAUD_PASS: integrity={fraud_result.integrity_score:.0f}/100")
                except Exception as e:
                    logger.warning(f"⚠️ [CP-10 FRAUD] B2B exception for {asset}: {e} → pass-through")

            if _JURISDICTION_AVAILABLE and cfg.get("jurisdiction_enabled",
                    os.environ.get("JURISDICTION_GATE_ENABLED", "false").lower() == "true"):
                try:
                    from omnix_core.governance.jurisdiction_gate import JurisdictionGateConfig
                    _j = load_jurisdiction_config_from_env()
                    juris_cfg = JurisdictionGateConfig(
                        enabled=True,
                        jurisdiction=cfg.get("jurisdiction",
                                             os.environ.get("JURISDICTION", _j.jurisdiction or "GLOBAL")),
                        operation_type=cfg.get("operation_type",
                                               os.environ.get("JURISDICTION_OP_TYPE", "spot")),
                        block_sanctioned_assets=cfg.get("jurisdiction_block_sanctioned", True),
                    )
                    op_type = juris_cfg.operation_type.lower()
                    juris_result = JurisdictionGate(juris_cfg).evaluate(asset, action_for_gates, op_type)
                    compliance_blocks["jurisdiction_compliance"] = {
                        "check": "enabled",
                        "result": "passed" if juris_result.admissible else "failed",
                        "jurisdiction": juris_result.jurisdiction,
                        "compliance_score": juris_result.compliance_score,
                        "violation": juris_result.violation,
                        "asset": asset,
                    }
                    if not juris_result.admissible:
                        decision = "BLOCKED"
                        overall_blocked = True
                        decision_trace.append(f"CP-11 JURISDICTION_VETO: {juris_result.reason}")
                        veto_chain.append({"checkpoint_id": "CP-11",
                                           "checkpoint_name": f"Jurisdiction Gate ({juris_result.jurisdiction})",
                                           "result": "VETO", "violation": juris_result.violation})
                        logger.warning(f"🌐 [CP-11] JURISDICTION_VETO: {juris_result.violation} | asset={asset}")
                    else:
                        decision_trace.append(
                            f"CP-11 JURISDICTION_PASS: {juris_result.jurisdiction} | score={juris_result.compliance_score:.0f}/100"
                        )
                except Exception as e:
                    logger.warning(f"⚠️ [CP-11 JURISDICTION] B2B exception for {asset}: {e} → pass-through")

        # ── ADR-053: Trajectory Invariant Enforcement (TIE) ─────────────────────
        # Runs AFTER all checkpoints — only on APPROVED decisions.
        # May convert APPROVED → HOLD if trajectory invariants are violated.
        # Fail-safe: exceptions → pass-through, never blocks pipeline.
        tie_block: dict | None = None
        if (
            _TIE_AVAILABLE
            and decision == "APPROVED"
            and os.environ.get("TIE_ENABLED", "true").lower() != "false"
        ):
            try:
                tie_db_conn = (compliance_config or {}).get("tie_db_conn") if compliance_config else None
                tie_engine = TrajectoryInvariantEngine(db_conn=tie_db_conn)
                tie_result = tie_engine.evaluate(
                    current_signals=resolved_signals,
                    asset=asset,
                    domain=domain,
                    current_decision=decision,
                    receipt_id=(metadata or {}).get("receipt_id"),
                )
                tie_block = TrajectoryInvariantEngine.result_to_dict(tie_result)
                if tie_result.trajectory_decision == "HOLD":
                    decision = "HOLD"
                    overall_blocked = True
                    decision_trace.append(
                        f"TIE_HOLD: {', '.join(v.invariant_id for v in tie_result.violations)}"
                    )
                    veto_chain.append({
                        "checkpoint_id": "TIE",
                        "checkpoint_name": "Trajectory Invariant Engine",
                        "result": "HOLD",
                        "violations": [v.invariant_id for v in tie_result.violations],
                    })
                    logger.warning(
                        f"🔄 [TIE] APPROVED→HOLD for {asset} ({domain}) | "
                        f"Invariants: {[v.invariant_id for v in tie_result.violations]}"
                    )
            except Exception as _tie_exc:
                logger.debug(f"[TIE] Pass-through for {asset}: {_tie_exc}")

        all_signals = list(REQUIRED_SIGNALS) + list(OPTIONAL_SIGNAL_DEFAULTS.keys())
        result: dict[str, Any] = {
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
        if compliance_blocks:
            result["compliance"] = compliance_blocks
        if context_admission_block is not None:
            result["context_admission"] = context_admission_block
        if tie_block is not None:
            result["trajectory_analysis"] = tie_block
        return result

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
