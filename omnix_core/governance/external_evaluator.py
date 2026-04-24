"""
OMNIX GovernanceEvaluationEngine — Domain-agnostic 11-checkpoint signal evaluator.

Accepts normalized governance signals from any domain (trading, credit, supply chain,
insurance, etc.) and runs them through the same fail-closed 11-checkpoint pipeline
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

try:
    from omnix_core.governance.assumption_validity_monitor import get_avm_instance
    _AVM_AVAILABLE = True
except Exception:
    _AVM_AVAILABLE = False

try:
    from omnix_core.governance.structural_admissibility_engine import (
        StructuralAdmissibilityEngine,
        StructuredRejectionRecord,
        ProposedRequest,
        EvaluationMode,
        SAEOverride,
        get_sae,
        get_sae_override,
        get_layer0_metrics,
    )
    _SAE_AVAILABLE = True
except Exception as _sae_exc:
    _SAE_AVAILABLE = False
    logger.warning(f"[Layer 0] SAE not available: {_sae_exc} — pass-through")

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
    "CP-8": {"min": 30.0, "max": 85.0},
    "CP-9": {"min": 20.0, "max": 80.0},
    "CP-10": {"min": 20.0, "max": 80.0},
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
    {
        "id": "CP-8",
        "name": "Edge Confirmation (ECW)",
        "signal": "signal_coherence",
        "operator": "gte",
        "threshold": 48,
        "optional": False,
        "description": "Edge convergence check. Confirms that signal agreement holds at the decision boundary — a secondary coherence gate applied after trajectory evaluation.",
    },
    {
        "id": "CP-9",
        "name": "AML Gate",
        "signal": "logic_consistency",
        "operator": "gte",
        "threshold": 38,
        "optional": False,
        "description": "Anti-money laundering pattern gate. Uses internal logic consistency as a structural proxy for AML compliance screening.",
    },
    {
        "id": "CP-10",
        "name": "Fraud Detection Gate",
        "signal": "signal_integrity",
        "operator": "gte",
        "threshold": 50,
        "optional": True,
        "description": "Fraud pattern detection gate. Validates signal integrity under adversarial assumptions — a pass-through when signal_integrity is not supplied.",
    },
]


class GovernanceEvaluationEngine:
    """
    Domain-agnostic 11-checkpoint governance evaluator.

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
        Run the 11-checkpoint evaluation pipeline on normalized signals.

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

        # ── Layer 0: Structural Admissibility Engine — pre-construction gate ─────
        # Runs BEFORE everything else — constitutive, not evaluative.
        # If the request is structurally inadmissible, no EvaluationRequest is
        # constructed and the pipeline is never entered. ADR-092 / OMNIX-PAT-2026-015.
        # B2B Zero-Bypass guarantee (ADR-092 + ADR-116):
        # Client compliance_config CANNOT disable Layer 0.
        # Only SAE_ENABLED=false env var (operator-level) may disable it.
        # Default: ON. FORCE_ON override ignores env var too.
        if _SAE_AVAILABLE:
            _sae_override = get_sae_override()
            if _sae_override == SAEOverride.FORCE_ON:
                _sae_enabled = True
            else:
                _sae_enabled = os.environ.get("SAE_ENABLED", "true").lower() != "false"
            if _sae_enabled:
                try:
                    _sae_subject     = asset
                    _sae_operation   = str(cfg.get(
                        "operation_type",
                        os.environ.get("JURISDICTION_OP_TYPE", "SPOT")
                    )).upper()
                    _sae_jurisdiction = str(cfg.get(
                        "jurisdiction",
                        os.environ.get("JURISDICTION", "GLOBAL")
                    )).upper()
                    _sae_client_id   = str(cfg.get("client_id", "GENERIC"))
                    _sae_eth_flags   = list(cfg.get("ethical_flags", []))
                    _sae_domain      = domain.upper()

                    _sae = get_sae()
                    _proposed = ProposedRequest(
                        subject=_sae_subject,
                        operation=_sae_operation,
                        jurisdiction=_sae_jurisdiction,
                        domain=_sae_domain,
                        client_id=_sae_client_id,
                        ethical_flags=_sae_eth_flags,
                        metadata=metadata,
                    )
                    _layer0_mode = (
                        EvaluationMode.FULL_AUDIT
                        if cfg.get("layer0_full_audit", False)
                        else EvaluationMode.FAST_FAIL
                    )
                    _layer0_result = _sae.validate(_proposed, mode=_layer0_mode)

                    if isinstance(_layer0_result, StructuredRejectionRecord):
                        logger.warning(
                            f"[Layer 0] INADMISSIBLE — {_layer0_result} | "
                            f"asset={asset} op={_sae_operation} jur={_sae_jurisdiction}"
                        )
                        all_signals = list(REQUIRED_SIGNALS) + list(OPTIONAL_SIGNAL_DEFAULTS.keys())
                        return {
                            "decision": "BLOCKED",
                            "asset": asset,
                            "domain": domain,
                            "layer": "LAYER_0_STRUCTURAL_ADMISSIBILITY",
                            "layer_0": _layer0_result.to_dict(),
                            "gate_results": [],
                            "veto_chain": [{
                                "checkpoint_id": "LAYER_0",
                                "checkpoint_name": "Structural Admissibility Engine",
                                "result": "INADMISSIBLE",
                                "constraint_id": (
                                    _layer0_result.primary_violation.constraint_id
                                    if _layer0_result.primary_violation else "UNKNOWN"
                                ),
                                "constraint_class": (
                                    _layer0_result.primary_violation.constraint_class.value
                                    if _layer0_result.primary_violation else "UNKNOWN"
                                ),
                                "description": str(_layer0_result),
                                "audit_id": _layer0_result.audit_id,
                            }],
                            "scores": {s: signals.get(s, 0.0) for s in all_signals},
                            "decision_trace": [
                                f"LAYER_0 INADMISSIBLE: {_layer0_result}"
                            ],
                            "metadata": metadata,
                            "checkpoints_total": 0,
                            "checkpoints_passed": 0,
                            "checkpoints_blocked": 1,
                        }
                    logger.debug(
                        f"[Layer 0] ADMISSIBLE — {_layer0_result} "
                        f"→ proceeding to Layer 1"
                    )
                except Exception as _sae_err:
                    logger.error(
                        f"[Layer 0] SAE INTERNAL ERROR — failing closed: {_sae_err} | "
                        f"asset={asset} domain={domain}"
                    )
                    all_signals = list(REQUIRED_SIGNALS) + list(OPTIONAL_SIGNAL_DEFAULTS.keys())
                    return {
                        "decision": "BLOCKED",
                        "asset": asset,
                        "domain": domain,
                        "layer": "LAYER_0_STRUCTURAL_ADMISSIBILITY",
                        "gate_results": [],
                        "veto_chain": [{
                            "checkpoint_id": "LAYER_0",
                            "checkpoint_name": "Structural Admissibility Engine",
                            "result": "SAE_INTERNAL_ERROR",
                            "constraint_id": "SAE_ERROR",
                            "description": f"SAE internal error — fail-closed: {_sae_err}",
                        }],
                        "scores": {s: signals.get(s, 0.0) for s in all_signals},
                        "decision_trace": [f"LAYER_0 FAIL-CLOSED: SAE internal error: {_sae_err}"],
                        "metadata": metadata,
                        "checkpoints_total": 0,
                        "checkpoints_passed": 0,
                        "checkpoints_blocked": 1,
                    }

        # ── AVM: Assumption Validity Monitor — pre-pipeline drift gate ─────────
        # Runs after Layer 0 — before CAG, before any checkpoint.
        # If calibration assumptions have drifted beyond tolerance, no evaluation
        # is performed and no receipt can be certified. ADR-064.
        avm_block: dict[str, Any] | None = None
        if _AVM_AVAILABLE:
            try:
                avm_enabled = cfg.get("avm_enabled",
                    os.environ.get("AVM_ENABLED", "true").lower() != "false")
                if avm_enabled:
                    _avm = get_avm_instance()
                    _resolved_for_avm = {**signals, **{
                        k: v for k, v in OPTIONAL_SIGNAL_DEFAULTS.items()
                        if k not in signals
                    }}
                    avm_result = _avm.evaluate(
                        signals=_resolved_for_avm,
                        domain=domain,
                    )
                    avm_block = avm_result.to_dict()
                    if not avm_result.is_valid and not avm_result.pass_through:
                        decision_trace.append(
                            f"AVM STALE_BLOCK: drift={avm_result.drift_score:.1f} > "
                            f"threshold={avm_result.drift_threshold:.1f} | "
                            f"snapshot={avm_result.snapshot_id} | "
                            f"age={avm_result.age_hours:.1f}h"
                        )
                        veto_chain.append({
                            "checkpoint_id": "AVM",
                            "checkpoint_name": "Assumption Validity Monitor",
                            "result": "STALE_BLOCK",
                            "drift_score": avm_result.drift_score,
                            "drift_threshold": avm_result.drift_threshold,
                            "snapshot_id": avm_result.snapshot_id,
                            "parameter_version": avm_result.parameter_version,
                            "block_reason": avm_result.block_reason,
                        })
                        logger.warning(
                            f"🔍 [AVM] STALE_BLOCK: drift={avm_result.drift_score:.1f} | "
                            f"threshold={avm_result.drift_threshold:.1f} | "
                            f"domain={domain} | asset={asset} | "
                            f"snapshot={avm_result.snapshot_id} | age={avm_result.age_hours:.1f}h"
                        )
                        all_signals = list(REQUIRED_SIGNALS) + list(OPTIONAL_SIGNAL_DEFAULTS.keys())
                        return {
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
                            "avm_result": avm_block,
                        }
                    else:
                        if avm_result.warnings:
                            for w in avm_result.warnings:
                                decision_trace.append(f"AVM WARNING: {w}")
                        if avm_result.pass_through:
                            # ADR-073F: Document WHY AVM is running in pass-through mode.
                            # Silent pass-through meant receipts were issued without any
                            # calibration baseline — an important limitation to surface.
                            if avm_result.snapshot_id == "NO_BASELINE":
                                decision_trace.append(
                                    "AVM_NO_BASELINE: Assumption Validity Monitor has no calibration "
                                    "snapshot saved for this domain. Drift detection is INACTIVE — "
                                    "the pipeline cannot detect when its assumptions have become "
                                    "stale. Call AssumptionValidityMonitor.save_calibration_snapshot() "
                                    "to arm AVM. All receipts issued in this state are unvalidated "
                                    "against calibration drift."
                                )
                            elif avm_result.snapshot_id == "DISABLED":
                                decision_trace.append(
                                    "AVM_DISABLED: Assumption Validity Monitor disabled via "
                                    "AVM_ENABLED=false. Calibration drift detection is OFF. "
                                    "Receipts issued without drift validation."
                                )
                            else:
                                decision_trace.append(
                                    f"AVM_PASS_THROUGH: snapshot={avm_result.snapshot_id} — "
                                    "running in pass-through mode (no blocking)."
                                )
                        else:
                            decision_trace.append(
                                f"AVM VALID: drift={avm_result.drift_score:.1f} ≤ "
                                f"{avm_result.drift_threshold:.1f} | "
                                f"snapshot={avm_result.snapshot_id} | "
                                f"version={avm_result.parameter_version}"
                            )
            except Exception as _avm_exc:
                logger.debug(f"[AVM] Pass-through for {asset} ({domain}): {_avm_exc}")
        # ─────────────────────────────────────────────────────────────────────

        # ── CAG: Context Admission Gate — session-level pre-admission ──────────
        # Runs BEFORE any signal enters the checkpoint pipeline.
        # If CAG blocks, no executable state is formed — pipeline never starts.
        context_admission_block: dict[str, Any] | None = None
        if _CAG_AVAILABLE:
            try:
                cag_enabled = cfg.get("cag_enabled",
                    os.environ.get("CAG_ENABLED", "true").lower() != "false")
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
                    # ADR-072: CAG liquidity proxy — explicit detection and trace
                    # liquidity_score=100.0 was a silent optimistic default; use 0.0 if not provided.
                    _cag_liq_raw = cfg.get("cag_liquidity_score")
                    _cag_liq_proxy = _cag_liq_raw is None
                    _cag_liq = float(_cag_liq_raw) if _cag_liq_raw is not None else 0.0

                    cag_result = ContextAdmissionGate(cag_cfg).evaluate(
                        global_volatility=float(cfg.get("cag_global_volatility", 0.0)),
                        cross_pair_correlation=float(cfg.get("cag_cross_pair_correlation", 0.0)),
                        liquidity_score=_cag_liq,
                        macro_risk=float(cfg.get("cag_macro_risk", 0.0)),
                    )
                    context_admission_block = {
                        "check": "enabled",
                        "result": "admitted" if cag_result.admitted else "blocked",
                        "admission_score": cag_result.admission_score,
                        "evaluation_state": getattr(cag_result, 'evaluation_state', ''),
                        "violation": cag_result.violation,
                        "parameters": {
                            "global_volatility": cag_result.global_volatility,
                            "cross_pair_correlation": cag_result.cross_pair_correlation,
                            "liquidity_score": cag_result.liquidity_score,
                            "macro_risk": cag_result.macro_risk,
                        },
                        "gate_checks": cag_result.gate_checks,
                    }
                    # ADR-072: emit CAG_LIQUIDITY_PROXY_MODE when liquidity not supplied
                    if _cag_liq_proxy:
                        _liq_warn = (
                            "CAG_LIQUIDITY_PROXY_MODE: cag_liquidity_score not provided by caller; "
                            "liquidity_score=0.0 used (conservative). Real web/order-book liquidity "
                            "data unavailable. Liquidity gate checks may block even healthy sessions."
                        )
                        decision_trace.append(_liq_warn)
                        context_admission_block["liquidity_proxy_warning"] = _liq_warn
                        logger.warning(f"⚠️ [CAG][LIQUIDITY_PROXY] {_liq_warn} | asset={asset}")

                    # ── Epistemic Transparency: warn on assumed market conditions (ADR-065) ──
                    # If no real context values were supplied, CAG ran on proxy defaults.
                    # Document this in the audit trail.
                    _cag_keys_provided = {
                        k for k in ("cag_global_volatility", "cag_cross_pair_correlation",
                                    "cag_liquidity_score", "cag_macro_risk")
                        if k in cfg
                    }
                    if not _cag_keys_provided:
                        _cag_warn = (
                            "CAG_WARNING: all context parameters are proxy defaults "
                            "(vol=0.0, corr=0.0, liq=0.0, macro=0.0) — "
                            "no real market data provided. Session admitted on conservative defaults."
                        )
                        decision_trace.append(_cag_warn)
                        context_admission_block["epistemic_warning"] = _cag_warn
                        logger.warning(f"⚠️ [CAG][EPISTEMIC] {_cag_warn} | asset={asset}")
                    # ─────────────────────────────────────────────────────────────────────
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
        applied_defaults: dict[str, float] = {}
        for opt_signal, default_val in OPTIONAL_SIGNAL_DEFAULTS.items():
            if opt_signal not in resolved_signals:
                resolved_signals[opt_signal] = default_val
                applied_defaults[opt_signal] = default_val

        # ── Epistemic Transparency: log every default substitution (ADR-065) ──
        # A default is not evidence. Downstream audit must know which signals
        # were provided by the caller vs. filled by the system.
        for sig, val in applied_defaults.items():
            cp_refs = [cp["id"] for cp in self.checkpoints if cp.get("signal") == sig]
            cp_str = f" (affects gates: {', '.join(cp_refs)})" if cp_refs else ""
            decision_trace.append(
                f"SIGNAL_DEFAULT_APPLIED: {sig}={val:.1f} — not provided by caller, "
                f"conservative default substituted{cp_str}"
            )
            logger.debug(f"[EPISTEMIC] SIGNAL_DEFAULT_APPLIED: {sig}={val:.1f}{cp_str}")
        # ─────────────────────────────────────────────────────────────────────

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
                    logger.error(f"⚠️ [CP-9 AML] INTERNAL ERROR — failing closed: {e} | asset={asset}")
                    decision = "BLOCKED"
                    overall_blocked = True
                    decision_trace.append(f"CP-9 AML_ERROR_BLOCKED: {e}")
                    veto_chain.append({"checkpoint_id": "CP-9", "checkpoint_name": "AML Gate",
                                       "result": "AML_INTERNAL_ERROR", "violation": str(e)})

            if _FRAUD_AVAILABLE and cfg.get("fraud_enabled",
                    os.environ.get("FRAUD_GATE_ENABLED", "false").lower() == "true"):
                try:
                    fraud_cfg = load_fraud_config_from_env()
                    fraud_cfg.enabled = True
                    dci = resolved_signals.get("logic_consistency", 50.0)
                    fraud_dci = max(0.0, 100.0 - dci)
                    # ── Epistemic Transparency: Fraud Gate proxy mode (ADR-065) ──
                    # CP-10 inputs are derived from pipeline-approved signals, not
                    # independent fraud data. This is a structural limitation:
                    # signals that passed CP-1, CP-3, CP-6 are likely to pass CP-10 too.
                    # Document this in every audit trail for regulatory honesty.
                    _fraud_proxy_note = (
                        "FRAUD_PROXY_MODE: CP-10 inputs derived from pipeline-approved signals "
                        "(dci←logic_consistency/CP-6, technical←probability_score/CP-1, "
                        "sentiment←signal_coherence/CP-3) — not independent fraud data. "
                        "Structural limitation: independent fraud signal source not yet available."
                    )
                    decision_trace.append(_fraud_proxy_note)
                    # ─────────────────────────────────────────────────────────
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
                        "proxy_mode": True,
                        "proxy_source_signals": {
                            "dci": "logic_consistency (inverted)",
                            "technical": "probability_score",
                            "sentiment": "signal_coherence",
                        },
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
                    logger.error(f"⚠️ [CP-10 FRAUD] INTERNAL ERROR — failing closed: {e} | asset={asset}")
                    decision = "BLOCKED"
                    overall_blocked = True
                    decision_trace.append(f"CP-10 FRAUD_ERROR_BLOCKED: {e}")
                    veto_chain.append({"checkpoint_id": "CP-10", "checkpoint_name": "Fraud Gate",
                                       "result": "FRAUD_INTERNAL_ERROR", "violation": str(e)})

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
            # ADR-065: Epistemic transparency — signals that were not provided by the caller
            "applied_signal_defaults": applied_defaults if applied_defaults else {},
        }
        if compliance_blocks:
            result["compliance"] = compliance_blocks
        if context_admission_block is not None:
            result["context_admission"] = context_admission_block
        if tie_block is not None:
            result["trajectory_analysis"] = tie_block
        if avm_block is not None:
            result["avm_result"] = avm_block
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
            "checkpoints_total": 11,
        }
