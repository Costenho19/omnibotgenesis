"""
OMNIX — Context Admission Gate (CAG)
ADR-050: Session-Level Pre-Admission Gate for Global Market Conditions

Purpose:
    The Context Admission Gate evaluates GLOBAL market conditions BEFORE any
    individual signal enters the 8-checkpoint pipeline. It operates at the
    session level — blocking the entire evaluation window when systemic risk
    conditions make the market environment structurally inadmissible.

    Four parameters govern admission:
      1. global_volatility_threshold  — VIX-equivalent or cross-asset vol index
      2. cross_pair_correlation_threshold — abnormal correlation = regime instability
      3. liquidity_score_minimum — minimum required liquidity score (0–100)
      4. macro_risk_ceiling — composite macro risk must be below this ceiling

Design:
    - Fail-safe: if module errors or disabled → pass-through (pipeline continues)
    - Default: DISABLED (CAG_ENABLED=false) — zero impact on existing clients
    - Session-level: one admission decision per evaluation window, not per signal
    - Output: CAGResult with structured reason for PQC receipt
    - Logging: [CAG] SESSION_BLOCKED / [CAG] SESSION_ADMITTED

Regulatory alignment:
    - NIST AI RMF: Context-aware decision governance
    - EU AI Act Art. 9: Risk management for high-impact AI systems
    - MiFID II: Circuit breaker obligations in extreme market conditions

Implemented: March 2026
ADR-050
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

CAG_DEFAULT_VOLATILITY_THRESHOLD: float = 80.0
CAG_DEFAULT_CORRELATION_THRESHOLD: float = 90.0
CAG_DEFAULT_LIQUIDITY_MINIMUM: float = 20.0
CAG_DEFAULT_MACRO_RISK_CEILING: float = 85.0


@dataclass
class CAGResult:
    """Result from the Context Admission Gate evaluation."""
    admitted: bool
    pass_through: bool = False
    reason: str = ""
    admission_score: float = 100.0
    violation: str = ""
    global_volatility: float = 0.0
    cross_pair_correlation: float = 0.0
    liquidity_score: float = 100.0
    macro_risk: float = 0.0
    gate_checks: list = field(default_factory=list)


@dataclass
class CAGConfig:
    """Configuration for the Context Admission Gate."""
    enabled: bool = False
    global_volatility_threshold: float = CAG_DEFAULT_VOLATILITY_THRESHOLD
    cross_pair_correlation_threshold: float = CAG_DEFAULT_CORRELATION_THRESHOLD
    liquidity_score_minimum: float = CAG_DEFAULT_LIQUIDITY_MINIMUM
    macro_risk_ceiling: float = CAG_DEFAULT_MACRO_RISK_CEILING
    block_on_any_violation: bool = True


class ContextAdmissionGate:
    """
    CAG — Context Admission Gate

    Session-level pre-admission gate. Evaluates global market conditions
    BEFORE any signal enters the 8-checkpoint pipeline. A blocked session
    means no executable state is formed — the pipeline never starts.

    This is architecturally distinct from the 8 checkpoints:
    - Checkpoints evaluate WHAT to decide (signal quality, risk, coherence)
    - CAG evaluates WHETHER the global context allows any decision at all

    Usage:
        gate = ContextAdmissionGate(config)
        result = gate.evaluate(
            global_volatility=45.0,
            cross_pair_correlation=60.0,
            liquidity_score=75.0,
            macro_risk=30.0,
        )
        if not result.admitted and not result.pass_through:
            # SESSION_BLOCKED — no signals enter the pipeline
    """

    def __init__(self, config: Optional[CAGConfig] = None):
        self.config = config or CAGConfig()

    def evaluate(
        self,
        global_volatility: float = 0.0,
        cross_pair_correlation: float = 0.0,
        liquidity_score: float = 100.0,
        macro_risk: float = 0.0,
    ) -> CAGResult:
        """
        Evaluate global market conditions for session admission.

        Args:
            global_volatility:      Composite volatility index (0–100).
                                    Higher = more volatile. Threshold: must be BELOW config max.
            cross_pair_correlation: Cross-asset correlation index (0–100).
                                    Higher = more correlated (regime instability).
                                    Threshold: must be BELOW config max.
            liquidity_score:        Market liquidity score (0–100).
                                    Higher = more liquid. Threshold: must be ABOVE config min.
            macro_risk:             Composite macro risk score (0–100).
                                    Higher = more macro risk. Threshold: must be BELOW config ceiling.

        Returns:
            CAGResult with admitted=True if session is admitted, False if blocked.
        """
        if not self.config.enabled:
            return CAGResult(
                admitted=True,
                pass_through=True,
                reason="CAG: disabled — session admitted by default",
                admission_score=100.0,
                global_volatility=global_volatility,
                cross_pair_correlation=cross_pair_correlation,
                liquidity_score=liquidity_score,
                macro_risk=macro_risk,
            )

        try:
            return self._run_admission_checks(
                global_volatility,
                cross_pair_correlation,
                liquidity_score,
                macro_risk,
            )
        except Exception as exc:
            logger.warning(f"⚠️ [CAG] Exception during admission check: {exc} → pass-through")
            return CAGResult(
                admitted=True,
                pass_through=True,
                reason=f"CAG exception → pass-through: {exc}",
                admission_score=100.0,
            )

    def _run_admission_checks(
        self,
        global_volatility: float,
        cross_pair_correlation: float,
        liquidity_score: float,
        macro_risk: float,
    ) -> CAGResult:
        """
        Execute the 4 admission checks in sequence.
        Each check is recorded in gate_checks for PQC receipt traceability.
        """
        admission_score = 100.0
        violations = []
        gate_checks = []

        # Check 1: Global Volatility — must be BELOW threshold
        vol_pass = global_volatility < self.config.global_volatility_threshold
        vol_check = {
            "parameter": "global_volatility",
            "value": global_volatility,
            "threshold": self.config.global_volatility_threshold,
            "operator": "lt",
            "result": "PASS" if vol_pass else "FAIL",
        }
        gate_checks.append(vol_check)
        if not vol_pass:
            penalty = min(50.0, (global_volatility - self.config.global_volatility_threshold) * 0.5)
            admission_score -= penalty
            violations.append(f"GLOBAL_VOLATILITY_EXCEEDED: {global_volatility:.1f} >= {self.config.global_volatility_threshold:.1f}")
            logger.warning(
                f"🚨 [CAG] VOLATILITY CHECK FAILED: global_vol={global_volatility:.1f} "
                f">= threshold={self.config.global_volatility_threshold:.1f}"
            )

        # Check 2: Cross-Pair Correlation — must be BELOW threshold
        corr_pass = cross_pair_correlation < self.config.cross_pair_correlation_threshold
        corr_check = {
            "parameter": "cross_pair_correlation",
            "value": cross_pair_correlation,
            "threshold": self.config.cross_pair_correlation_threshold,
            "operator": "lt",
            "result": "PASS" if corr_pass else "FAIL",
        }
        gate_checks.append(corr_check)
        if not corr_pass:
            penalty = min(40.0, (cross_pair_correlation - self.config.cross_pair_correlation_threshold) * 0.4)
            admission_score -= penalty
            violations.append(f"CORRELATION_REGIME_INSTABILITY: {cross_pair_correlation:.1f} >= {self.config.cross_pair_correlation_threshold:.1f}")
            logger.warning(
                f"🚨 [CAG] CORRELATION CHECK FAILED: cross_corr={cross_pair_correlation:.1f} "
                f">= threshold={self.config.cross_pair_correlation_threshold:.1f}"
            )

        # Check 3: Liquidity Score — must be ABOVE minimum
        liq_pass = liquidity_score >= self.config.liquidity_score_minimum
        liq_check = {
            "parameter": "liquidity_score",
            "value": liquidity_score,
            "threshold": self.config.liquidity_score_minimum,
            "operator": "gte",
            "result": "PASS" if liq_pass else "FAIL",
        }
        gate_checks.append(liq_check)
        if not liq_pass:
            penalty = min(40.0, (self.config.liquidity_score_minimum - liquidity_score) * 0.4)
            admission_score -= penalty
            violations.append(f"INSUFFICIENT_LIQUIDITY: {liquidity_score:.1f} < {self.config.liquidity_score_minimum:.1f}")
            logger.warning(
                f"🚨 [CAG] LIQUIDITY CHECK FAILED: liquidity={liquidity_score:.1f} "
                f"< minimum={self.config.liquidity_score_minimum:.1f}"
            )

        # Check 4: Macro Risk — must be BELOW ceiling
        macro_pass = macro_risk < self.config.macro_risk_ceiling
        macro_check = {
            "parameter": "macro_risk",
            "value": macro_risk,
            "threshold": self.config.macro_risk_ceiling,
            "operator": "lt",
            "result": "PASS" if macro_pass else "FAIL",
        }
        gate_checks.append(macro_check)
        if not macro_pass:
            penalty = min(50.0, (macro_risk - self.config.macro_risk_ceiling) * 0.5)
            admission_score -= penalty
            violations.append(f"MACRO_RISK_CEILING_BREACHED: {macro_risk:.1f} >= {self.config.macro_risk_ceiling:.1f}")
            logger.warning(
                f"🚨 [CAG] MACRO RISK CHECK FAILED: macro_risk={macro_risk:.1f} "
                f">= ceiling={self.config.macro_risk_ceiling:.1f}"
            )

        admission_score = max(0.0, admission_score)

        if violations:
            if self.config.block_on_any_violation:
                blocked = True
            else:
                blocked = admission_score < 50.0

            primary_violation = violations[0].split(":")[0]

            if blocked:
                logger.warning(
                    f"🚫 [CAG] SESSION_BLOCKED: {'; '.join(violations)} | "
                    f"admission_score={admission_score:.0f}/100"
                )
                return CAGResult(
                    admitted=False,
                    pass_through=False,
                    reason=f"CAG SESSION_BLOCKED: {'; '.join(violations)}",
                    admission_score=admission_score,
                    violation=primary_violation,
                    global_volatility=global_volatility,
                    cross_pair_correlation=cross_pair_correlation,
                    liquidity_score=liquidity_score,
                    macro_risk=macro_risk,
                    gate_checks=gate_checks,
                )
            else:
                logger.warning(
                    f"⚠️ [CAG] SESSION_ADMITTED_WITH_WARNINGS: {'; '.join(violations)} | "
                    f"admission_score={admission_score:.0f}/100"
                )
                return CAGResult(
                    admitted=True,
                    pass_through=False,
                    reason=f"CAG SESSION_ADMITTED_WITH_WARNINGS: {'; '.join(violations)}",
                    admission_score=admission_score,
                    violation="; ".join(violations),
                    global_volatility=global_volatility,
                    cross_pair_correlation=cross_pair_correlation,
                    liquidity_score=liquidity_score,
                    macro_risk=macro_risk,
                    gate_checks=gate_checks,
                )

        logger.info(
            f"✅ [CAG] SESSION_ADMITTED: all 4 checks passed | "
            f"vol={global_volatility:.1f}, corr={cross_pair_correlation:.1f}, "
            f"liq={liquidity_score:.1f}, macro={macro_risk:.1f} | "
            f"admission_score={admission_score:.0f}/100"
        )
        return CAGResult(
            admitted=True,
            pass_through=False,
            reason=f"CAG SESSION_ADMITTED: all context parameters within bounds | score={admission_score:.0f}/100",
            admission_score=admission_score,
            global_volatility=global_volatility,
            cross_pair_correlation=cross_pair_correlation,
            liquidity_score=liquidity_score,
            macro_risk=macro_risk,
            gate_checks=gate_checks,
        )


def load_cag_config_from_env() -> CAGConfig:
    """
    Load Context Admission Gate configuration from environment variables.
    Returns default (disabled) config if CAG_ENABLED is not 'true'.

    Environment variables:
        CAG_ENABLED                     (default: false)
        CAG_VOLATILITY_THRESHOLD        (default: 80.0)
        CAG_CORRELATION_THRESHOLD       (default: 90.0)
        CAG_LIQUIDITY_MINIMUM           (default: 20.0)
        CAG_MACRO_RISK_CEILING          (default: 85.0)
        CAG_BLOCK_ON_ANY_VIOLATION      (default: true)
    """
    enabled = os.environ.get("CAG_ENABLED", "false").lower() == "true"
    if not enabled:
        return CAGConfig(enabled=False)

    return CAGConfig(
        enabled=True,
        global_volatility_threshold=float(
            os.environ.get("CAG_VOLATILITY_THRESHOLD", str(CAG_DEFAULT_VOLATILITY_THRESHOLD))
        ),
        cross_pair_correlation_threshold=float(
            os.environ.get("CAG_CORRELATION_THRESHOLD", str(CAG_DEFAULT_CORRELATION_THRESHOLD))
        ),
        liquidity_score_minimum=float(
            os.environ.get("CAG_LIQUIDITY_MINIMUM", str(CAG_DEFAULT_LIQUIDITY_MINIMUM))
        ),
        macro_risk_ceiling=float(
            os.environ.get("CAG_MACRO_RISK_CEILING", str(CAG_DEFAULT_MACRO_RISK_CEILING))
        ),
        block_on_any_violation=os.environ.get("CAG_BLOCK_ON_ANY_VIOLATION", "true").lower() == "true",
    )
