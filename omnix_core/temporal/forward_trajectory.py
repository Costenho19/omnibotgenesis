#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Forward Trajectory Implication (FTI) — OMNIX Checkpoint 7b
ADR-034 | March 2026

Evaluates what a proposed decision IMPLIES for the N future cycles.
Complements TCV (backward-looking) with a forward-looking dimension.

Where TCV asks: "Is this decision coherent with the past?"
FTI asks:       "Is this decision coherent with the likely near future?"

ALGORITHM — Implied Score (0-100):
  Score = RegimeTransitionRisk(40%) + ImpliedDecisionConsistency(35%) + SignalMomentumSustainability(25%)

  1. Regime Transition Risk (40%):
     Using HMM transition matrix, computes the probability that the market
     transitions to an ADVERSE regime within the FTI_HORIZON cycles.
     An adverse regime for a BUY is BEARISH/VOLATILE; for a SELL it is BULLISH.
     Score = (1 - adverse_transition_probability) × 100

  2. Implied Decision Consistency (35%):
     Given the proposed action and current regime, projects whether the system
     will be able to maintain consistency (not immediately contradict) for
     the next N cycles. Uses historical regime persistence data.
     High persistence → high score.

  3. Signal Momentum Sustainability (25%):
     Evaluates the slope of recent EMA/confidence scores. A BUY decision
     with declining signal momentum is less sustainable than one with
     rising momentum.
     Score = (slope_normalized + 1) / 2 × 100

FAIL-SAFE: On any error → pass=True, pass_through=True.
CONFIG: FTI_THRESHOLD (default 25), FTI_HORIZON (default 5 cycles).

Harold Nunes — OMNIX Decision Governance Infrastructure
"""

import logging
import os
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

FTI_THRESHOLD_DEFAULT = 25
FTI_HORIZON_DEFAULT = 5

_ADVERSE_REGIMES: Dict[str, List[str]] = {
    "BUY": ["BEARISH", "DOWNTREND", "VOLATILE", "STRONG_SELL"],
    "SELL": ["BULLISH", "UPTREND", "VOLATILE", "STRONG_BUY"],
    "HOLD": [],
}

_REGIME_PERSISTENCE: Dict[str, float] = {
    "TRENDING": 0.82,
    "UPTREND": 0.78,
    "DOWNTREND": 0.76,
    "BULLISH": 0.75,
    "BEARISH": 0.74,
    "RANGING": 0.65,
    "NEUTRAL": 0.60,
    "VOLATILE": 0.45,
}
_DEFAULT_PERSISTENCE = 0.60


@dataclass
class FTIResult:
    """
    Result of Forward Trajectory Implication evaluation.

    Fields:
        passed:                   True if implied_score >= threshold.
        implied_score:            Composite forward-looking score [0-100].
        regime_transition_risk:   Probability [0-1] of adverse regime transition.
        dimension_scores:         Breakdown of 3 scoring dimensions.
        horizon_cycles:           N-cycle look-ahead used in evaluation.
        proposed_action:          The action being evaluated.
        current_regime:           Detected regime at evaluation time.
        threshold_used:           Veto threshold.
        pass_through:             True when FTI returned passed due to error.
        timestamp:                ISO-8601 UTC evaluation timestamp.
    """

    passed: bool
    implied_score: float
    regime_transition_risk: float = 0.0
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    horizon_cycles: int = FTI_HORIZON_DEFAULT
    proposed_action: str = "HOLD"
    current_regime: str = "NEUTRAL"
    threshold_used: float = FTI_THRESHOLD_DEFAULT
    pass_through: bool = False
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "implied_score": round(self.implied_score, 2),
            "regime_transition_risk": round(self.regime_transition_risk, 4),
            "dimension_scores": {k: round(v, 2) for k, v in self.dimension_scores.items()},
            "horizon_cycles": self.horizon_cycles,
            "proposed_action": self.proposed_action,
            "current_regime": self.current_regime,
            "threshold_used": self.threshold_used,
            "pass_through": self.pass_through,
            "timestamp": self.timestamp,
        }


class ForwardTrajectoryImplicator:
    """
    Forward Trajectory Implicator (FTI) — OMNIX Checkpoint 7b (ADR-034).

    Evaluates the forward implication of a proposed decision over a
    configurable look-ahead horizon (default: 5 cycles).

    Receives optional context from the bot (HMM transition matrix,
    recent EMA scores, current regime). When context is absent, each
    dimension falls back to a conservative neutral score (50/100)
    so FTI never blocks a decision based on missing data.

    Conservative threshold (25/100): FTI only vetoes when the forward
    implication is strongly negative across multiple dimensions simultaneously.
    """

    def __init__(self):
        self.threshold = float(os.getenv("FTI_THRESHOLD", str(FTI_THRESHOLD_DEFAULT)))
        self.horizon = int(os.getenv("FTI_HORIZON", str(FTI_HORIZON_DEFAULT)))

    def evaluate(
        self,
        proposed_action: str,
        symbol: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> FTIResult:
        """
        Evaluate the forward trajectory implication of proposed_action.

        Args:
            proposed_action: "BUY", "SELL", or "HOLD".
            symbol:          Trading symbol (e.g. "XBTUSD").
            context:         Optional dict with:
                             - hmm_transition_matrix: dict of regime→dict of regime→probability
                             - current_regime: str
                             - recent_ema_scores: list[float] (most recent last)
                             - recent_signal_directions: list[str]
                             - regime_history: list[str] (recent regimes, most recent last)

        Returns:
            FTIResult. On any error → passed=True, pass_through=True (fail-safe).
        """
        try:
            return self._evaluate_internal(proposed_action, symbol, context or {})
        except Exception as exc:
            logger.warning(
                "⚠️ [FTI] Exception for %s action=%s: %s → pass-through",
                symbol, proposed_action, exc
            )
            return FTIResult(
                passed=True,
                implied_score=100.0,
                pass_through=True,
                proposed_action=proposed_action,
                threshold_used=self.threshold,
                horizon_cycles=self.horizon,
            )

    def _evaluate_internal(
        self,
        proposed_action: str,
        symbol: str,
        context: Dict[str, Any],
    ) -> FTIResult:
        action = proposed_action.upper().strip()
        current_regime = str(context.get("current_regime", "NEUTRAL")).upper()

        d1, transition_risk = self._score_regime_transition_risk(
            action, current_regime, context
        )
        d2 = self._score_implied_decision_consistency(
            action, current_regime, context
        )
        d3 = self._score_signal_momentum_sustainability(action, context)

        implied_score = max(0.0, min(100.0, d1 * 0.40 + d2 * 0.35 + d3 * 0.25))
        passed = implied_score >= self.threshold

        if passed:
            logger.debug(
                "🔮 [FTI] %s | action=%s | regime=%s | score=%.1f → PASS",
                symbol, action, current_regime, implied_score
            )
        else:
            logger.warning(
                "🔮 [FTI_FAIL] %s | action=%s | regime=%s | score=%.1f < %.0f → VETO",
                symbol, action, current_regime, implied_score, self.threshold
            )

        return FTIResult(
            passed=passed,
            implied_score=implied_score,
            regime_transition_risk=transition_risk,
            dimension_scores={
                "regime_transition_risk_score": round(d1, 2),
                "implied_decision_consistency": round(d2, 2),
                "signal_momentum_sustainability": round(d3, 2),
            },
            horizon_cycles=self.horizon,
            proposed_action=action,
            current_regime=current_regime,
            threshold_used=self.threshold,
            pass_through=False,
        )

    def _score_regime_transition_risk(
        self,
        action: str,
        current_regime: str,
        context: Dict[str, Any],
    ) -> Tuple[float, float]:
        """
        Compute regime transition risk score (0-100) and raw transition probability.

        Uses HMM transition matrix if provided; otherwise uses regime persistence
        priors to estimate the probability of remaining in the current regime
        for `self.horizon` cycles.

        Returns (score, adverse_transition_probability).
        """
        adverse = _ADVERSE_REGIMES.get(action, [])
        if not adverse:
            return 75.0, 0.0

        hmm_matrix: Optional[Dict] = context.get("hmm_transition_matrix")
        if hmm_matrix and isinstance(hmm_matrix, dict):
            row = hmm_matrix.get(current_regime, {})
            if row:
                adverse_prob = sum(
                    float(row.get(a, 0.0)) for a in adverse
                )
                adverse_prob = min(1.0, max(0.0, adverse_prob))
                stay_prob = max(0.0, 1.0 - adverse_prob)
                multi_cycle_risk = 1.0 - (stay_prob ** self.horizon)
                score = (1.0 - multi_cycle_risk) * 100.0
                return max(0.0, min(100.0, score)), multi_cycle_risk

        persistence = _REGIME_PERSISTENCE.get(current_regime, _DEFAULT_PERSISTENCE)
        persist_n = persistence ** self.horizon
        adverse_prob = 1.0 - persist_n
        score = persist_n * 100.0
        return max(0.0, min(100.0, score)), adverse_prob

    def _score_implied_decision_consistency(
        self,
        action: str,
        current_regime: str,
        context: Dict[str, Any],
    ) -> float:
        """
        Score whether the action is consistent with what the system will likely
        need to do in the next N cycles.

        Uses regime history to assess persistence. If regime has been stable,
        the action aligns well. If regime has been volatile/changing, consistency
        score is penalized.
        """
        regime_history: List[str] = context.get("regime_history", [])
        if not regime_history:
            return 50.0

        recent = [r.upper() for r in regime_history[-self.horizon:]]
        if not recent:
            return 50.0

        current_count = sum(1 for r in recent if r == current_regime)
        persistence_ratio = current_count / len(recent)

        from_map = {
            "BUY": ["BULLISH", "UPTREND", "TRENDING", "NEUTRAL"],
            "SELL": ["BEARISH", "DOWNTREND", "VOLATILE"],
            "HOLD": ["NEUTRAL", "RANGING", "VOLATILE"],
        }
        compatible_regimes = from_map.get(action, [])
        compatible_count = sum(1 for r in recent if r in compatible_regimes)
        compatibility_ratio = compatible_count / len(recent) if recent else 0.5

        score = (persistence_ratio * 0.5 + compatibility_ratio * 0.5) * 100.0
        return max(0.0, min(100.0, score))

    def _score_signal_momentum_sustainability(
        self,
        action: str,
        context: Dict[str, Any],
    ) -> float:
        """
        Score whether the current signal momentum is sustainable for the horizon.

        Uses recent EMA scores to compute the slope (linear trend).
        - Positive slope + BUY → high score
        - Negative slope + BUY → lower score
        - Positive slope + SELL → lower score
        - Neutral slope → neutral score (~50)
        """
        ema_scores: List[float] = context.get("recent_ema_scores", [])
        if len(ema_scores) < 2:
            return 50.0

        slope = self._linear_slope(ema_scores)
        slope_clamped = max(-1.0, min(1.0, slope))

        if action == "BUY":
            normalized = (slope_clamped + 1.0) / 2.0
        elif action == "SELL":
            normalized = (1.0 - slope_clamped) / 2.0
        else:
            normalized = 1.0 - abs(slope_clamped)

        return max(0.0, min(100.0, normalized * 100.0))

    @staticmethod
    def _linear_slope(values: List[float]) -> float:
        """
        Compute normalized linear regression slope for a list of values.
        Returns a value in [-1, 1] representing the trend direction and strength.
        """
        n = len(values)
        if n < 2:
            return 0.0

        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / n
        y_std = statistics.pstdev(values) if len(values) > 1 else 1.0
        if y_std == 0:
            return 0.0

        x_var = sum((i - x_mean) ** 2 for i in range(n))
        if x_var == 0:
            return 0.0

        cov = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        raw_slope = cov / x_var
        range_per_step = raw_slope / y_std if y_std > 0 else 0.0
        return max(-1.0, min(1.0, range_per_step))
