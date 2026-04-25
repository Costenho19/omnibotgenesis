"""
OMNIX — Fraud Detection Gate (CP-10)
ADR-048: Anomalous Behavior & Market Manipulation Detection Gate
ADR-069: Epistemic Transparency — score=0 on disabled/failsafe; evaluation_state field

Purpose:
    CP-10 detects patterns of market manipulation and anomalous behavior
    in automated decision signals before execution. When enabled, it screens for:
      - Extreme signal divergence (technical vs. sentiment contradiction)
      - Simultaneous contradictory signals (possible spoofing indicator)
      - Excessive DCI (Decision Contradiction Index) implying internal incoherence
      - Rapid consecutive decision reversals (flip-flopping pattern)

Design:
    - Fail-closed: if module errors → BLOCK (admissible=False, pass_through=False) — ADR-116
    - Disabled path only → pass-through (pipeline continues without fraud check)
    - Activatable via FRAUD_GATE_ENABLED env var
    - Default: DISABLED (zero impact on existing Railway operation)
    - Regulatory alignment: EU AI Act Art. 6 (high-risk AI systems)

ADR-069 (2026-04-09):
    Disabled path: integrity_score=0.0 (was 100.0) + evaluation_state="DISABLED"
    Failsafe path: integrity_score=0.0 (was 100.0 via dataclass default) + evaluation_state="FAILSAFE"
    All evaluated paths: evaluation_state="EVALUATED"
    Principle: score=100 on disabled/error fabricates fraud-detection confidence without evidence.

Implemented: March 2026
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

DCI_FRAUD_THRESHOLD_DEFAULT: float = 85.0
SIGNAL_DIVERGENCE_THRESHOLD_DEFAULT: float = 60.0
REVERSAL_WINDOW_DEFAULT: int = 3


@dataclass
class FraudVetoResult:
    """
    Result from the Fraud Detection Gate (CP-10).

    ADR-069: integrity_score defaults to 0.0.
    Disabled/failsafe paths set integrity_score=0.0 explicitly — absence of
    fraud evaluation is NOT equivalent to perfect integrity.
    evaluation_state distinguishes DISABLED / FAILSAFE / EVALUATED for audit dashboards.
    """
    admissible: bool = False          # Default fail-safe: not admitted unless explicitly set (ADR-116)
    pass_through: bool = False
    reason: str = ""
    asset: str = ""
    violation: str = ""
    fraud_score: float = 0.0
    integrity_score: float = 0.0
    evaluation_state: str = ""


@dataclass
class FraudGateConfig:
    enabled: bool = False
    dci_threshold: float = DCI_FRAUD_THRESHOLD_DEFAULT
    signal_divergence_threshold: float = SIGNAL_DIVERGENCE_THRESHOLD_DEFAULT
    reversal_window: int = REVERSAL_WINDOW_DEFAULT
    block_extreme_dci: bool = True
    block_signal_divergence: bool = True


class FraudGate:
    """
    CP-10: Fraud Detection Gate

    Detects patterns consistent with market manipulation, signal spoofing,
    or anomalous decision behavior. Positioned AFTER CP-8 (ECW) in the pipeline.

    Regulatory alignment:
      - EU AI Act Article 6 (high-risk AI systems — market infrastructure)
      - MiFID II (market manipulation detection obligations)
      - SEC Rule 10b-5 (fraud in connection with securities)

    Checks:
      1. Extreme DCI (Decision Contradiction Index ≥ 85) — internal incoherence
      2. Technical vs. sentiment divergence ≥ threshold — contradictory signals
      3. Rapid consecutive reversals — flip-flopping manipulation pattern

    Usage:
        gate = FraudGate(config)
        result = gate.evaluate(symbol, proposed_action, dci, technical_score, sentiment_score)
        if not result.admissible and not result.pass_through:
            # VETO — block the decision

    ADR-069: result.evaluation_state distinguishes "DISABLED" / "FAILSAFE" / "EVALUATED".
    integrity_score=0.0 on disabled/failsafe — absence of evaluation ≠ perfect integrity.
    """

    def __init__(self, config: Optional[FraudGateConfig] = None):
        self.config = config or FraudGateConfig()

    def evaluate(
        self,
        symbol: str,
        proposed_action: str,
        dci_score: float = 0.0,
        technical_score: float = 50.0,
        sentiment_score: float = 50.0,
        recent_reversals: int = 0,
    ) -> FraudVetoResult:
        """
        Evaluate a proposed decision for fraud/manipulation patterns.

        Args:
            symbol:           Trading pair (e.g., "BTC/USD")
            proposed_action:  "BUY", "SELL", or "HOLD"
            dci_score:        Decision Contradiction Index (0-100; higher = more incoherent)
            technical_score:  Composite technical signal strength (0-100)
            sentiment_score:  Market sentiment score (0-100)
            recent_reversals: Number of BUY→SELL or SELL→BUY reversals in last N cycles

        Returns:
            FraudVetoResult. On disabled or error → pass-through, integrity_score=0.0.

        ADR-069: disabled/failsafe paths return integrity_score=0.0, not 100.0.
            score=100 when disabled fabricates fraud-detection confidence without evidence.
        """
        if not self.config.enabled:
            logger.debug(f"[CP-10 FRAUD] disabled — pass-through for {symbol}")
            return FraudVetoResult(
                admissible=True,
                pass_through=True,
                reason=(
                    "CP-10 FRAUD_GATE_DISABLED: score=0 reflects absence of evaluation, "
                    "not absence of fraud. Enable with FRAUD_GATE_ENABLED=true."
                ),
                asset=symbol,
                integrity_score=0.0,
                evaluation_state="DISABLED",
            )

        try:
            return self._run_checks(
                symbol, proposed_action, dci_score,
                technical_score, sentiment_score, recent_reversals
            )
        except Exception as exc:
            logger.error(f"❌ [FRAUD_GATE] Exception for {symbol}: {exc} → FAIL-CLOSED (ADR-116)")
            return FraudVetoResult(
                admissible=False,
                pass_through=False,
                reason=(
                    f"CP-10 FRAUD_FAIL_CLOSED: module error — ejecución bloqueada por seguridad (ADR-116) — {exc}."
                ),
                asset=symbol,
                integrity_score=0.0,
                evaluation_state="FAIL_CLOSED",
            )

    def _run_checks(
        self,
        symbol: str,
        proposed_action: str,
        dci_score: float,
        technical_score: float,
        sentiment_score: float,
        recent_reversals: int,
    ) -> FraudVetoResult:
        integrity_score = 100.0
        violations = []

        if self.config.block_extreme_dci and dci_score >= self.config.dci_threshold:
            return FraudVetoResult(
                admissible=False,
                pass_through=False,
                reason=(
                    f"CP-10 FRAUD VETO: Extreme DCI {dci_score:.1f} ≥ {self.config.dci_threshold:.1f} "
                    f"— internal signal incoherence at manipulation threshold"
                ),
                asset=symbol,
                violation="EXTREME_DCI",
                fraud_score=dci_score,
                integrity_score=0.0,
                evaluation_state="EVALUATED",
            )

        if self.config.block_signal_divergence and proposed_action.upper() != "HOLD":
            divergence = abs(technical_score - sentiment_score)
            if divergence >= self.config.signal_divergence_threshold:
                return FraudVetoResult(
                    admissible=False,
                    pass_through=False,
                    reason=(
                        f"CP-10 FRAUD VETO: Signal divergence {divergence:.1f} ≥ {self.config.signal_divergence_threshold:.1f} "
                        f"— technical ({technical_score:.0f}) vs sentiment ({sentiment_score:.0f}) contradiction"
                    ),
                    asset=symbol,
                    violation="SIGNAL_DIVERGENCE",
                    fraud_score=divergence,
                    integrity_score=0.0,
                    evaluation_state="EVALUATED",
                )

        if recent_reversals >= self.config.reversal_window:
            integrity_score -= 35.0
            violations.append(
                f"Rapid reversals: {recent_reversals} in last window (threshold {self.config.reversal_window})"
            )

        if 50.0 <= dci_score < self.config.dci_threshold:
            integrity_score -= 20.0
            violations.append(f"Elevated DCI {dci_score:.1f} — signal instability")

        if violations:
            admissible = integrity_score >= 50.0
            return FraudVetoResult(
                admissible=admissible,
                pass_through=False,
                reason=f"CP-10 FRAUD {'PASS' if admissible else 'VETO'}: {'; '.join(violations)}",
                asset=symbol,
                violation=", ".join(violations),
                fraud_score=100.0 - integrity_score,
                integrity_score=max(0.0, integrity_score),
                evaluation_state="EVALUATED",
            )

        return FraudVetoResult(
            admissible=True,
            pass_through=False,
            reason=f"CP-10 FRAUD PASS: {symbol} — no manipulation patterns | integrity {integrity_score:.0f}/100",
            asset=symbol,
            integrity_score=integrity_score,
            evaluation_state="EVALUATED",
        )


def load_fraud_config_from_env() -> FraudGateConfig:
    """
    Load Fraud Gate configuration from environment variables.
    Returns default (disabled) config if FRAUD_GATE_ENABLED is not 'true'.
    """
    enabled = os.environ.get("FRAUD_GATE_ENABLED", "false").lower() == "true"
    if not enabled:
        return FraudGateConfig(enabled=False)

    return FraudGateConfig(
        enabled=True,
        dci_threshold=float(os.environ.get("FRAUD_DCI_THRESHOLD", "85.0")),
        signal_divergence_threshold=float(
            os.environ.get("FRAUD_DIVERGENCE_THRESHOLD", "60.0")
        ),
        reversal_window=int(os.environ.get("FRAUD_REVERSAL_WINDOW", "3")),
        block_extreme_dci=os.environ.get("FRAUD_BLOCK_EXTREME_DCI", "true").lower() == "true",
        block_signal_divergence=os.environ.get(
            "FRAUD_BLOCK_SIGNAL_DIVERGENCE", "true"
        ).lower() == "true",
    )
