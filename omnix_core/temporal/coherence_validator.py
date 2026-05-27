#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Temporal Coherence Validation (TCV) — OMNIX Checkpoint 7
ADR-032 | March 2026

Evaluates whether a proposed decision is TEMPORALLY ADMISSIBLE given
the recent trajectory of the system. Complements probabilistic governance
(Checkpoints 1-6) with trajectory-level coherence analysis.

Inspired by QTD (Quantum Temporal Dynamics) framework — JJ Jimenez, Feb 2026.

ALGORITHM — Trajectory Coherence Score (0-100):
  Score = DirectionCoherence(40%) + RegimeAlignment(35%) + SignalStability(25%)

  1. Direction Coherence (40%):
     Sign-consistency of consecutive EMA-score deltas (monotonicity).
     Measures whether the signal is TRENDING in a consistent direction,
     not just whether it's stable at a level. High monotonicity → high score.

  2. Regime-Action Alignment (35%):
     Does the proposed action match the dominant HMM regime in recent history?
     Computed from both shadow events AND executed trades for an unbiased view.

  3. Signal Stability (25%):
     Inverse of direction-flip rate across recent signal labels (BULLISH/BEARISH).
     Rapid alternation → low stability → penalty.

DATA SOURCES (dual-source, unbiased):
  PRIMARY:   shadow_trade_events  (veto events — blocked signals)
  SECONDARY: paper_trading_trades (executed trades — approved signals)
  Combining both gives a complete picture of the decision trajectory.

FAIL-SAFE: On any error → admissible=True (never blocks on module failure).
DRIVER:    Supports psycopg v3 (primary) with psycopg2 fallback.
CONFIG:    TCV_THRESHOLD (default 20), TCV_WINDOW (default 15), TCV_MIN_EVENTS (default 3).

Harold Nunes — OMNIX Decision Governance Infrastructure
"""

import logging
import os
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

TCV_THRESHOLD_DEFAULT = 20
TCV_WINDOW_DEFAULT = 15
TCV_MIN_EVENTS_DEFAULT = 3

_SIGNAL_TO_DIRECTION: Dict[str, str] = {
    "BULLISH": "BUY",
    "LONG": "BUY",
    "BUY": "BUY",
    "STRONG_BUY": "BUY",
    "UPTREND": "BUY",
    "BEARISH": "SELL",
    "SHORT": "SELL",
    "SELL": "SELL",
    "STRONG_SELL": "SELL",
    "DOWNTREND": "SELL",
    "NEUTRAL": "HOLD",
    "NONE": "HOLD",
    "RANGING": "HOLD",
    "VOLATILE": "HOLD",
}

_REGIME_ALLOWED_ACTIONS: Dict[str, List[str]] = {
    "BULLISH": ["BUY"],
    "BEARISH": ["SELL"],
    "NEUTRAL": ["BUY", "SELL", "HOLD"],
    "VOLATILE": ["HOLD"],
    "RANGING": ["BUY", "SELL", "HOLD"],
    "TRENDING": ["BUY", "SELL"],
    "UPTREND": ["BUY"],
    "DOWNTREND": ["SELL"],
}


def _normalize_direction(raw: Optional[str]) -> str:
    """Normalize any signal/regime string to BUY / SELL / HOLD."""
    if not raw:
        return "HOLD"
    return _SIGNAL_TO_DIRECTION.get(raw.upper().strip(), "HOLD")


@dataclass
class TCVResult:
    """
    Result of Temporal Coherence Validation.

    Fields:
        admissible:         True if decision passes temporal coherence check.
        trajectory_score:   Composite score [0-100].
        reason:             Human-readable explanation.
        dimension_scores:   Breakdown of the three scoring dimensions.
        events_analyzed:    Number of events used in the evaluation.
        threshold_used:     Veto threshold at time of evaluation.
        data_sources:       Which DB sources contributed to the evaluation.
        pass_through:       True when TCV returned admissible due to insufficient
                            data or a module error (not an affirmative assessment).
        timestamp:          ISO-8601 UTC timestamp of evaluation.
    """

    admissible: bool
    trajectory_score: float
    reason: str
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    events_analyzed: int = 0
    threshold_used: float = TCV_THRESHOLD_DEFAULT
    data_sources: List[str] = field(default_factory=list)
    pass_through: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "admissible": self.admissible,
            "trajectory_score": round(self.trajectory_score, 2),
            "reason": self.reason,
            "dimension_scores": {k: round(v, 2) for k, v in self.dimension_scores.items()},
            "events_analyzed": self.events_analyzed,
            "threshold_used": self.threshold_used,
            "data_sources": self.data_sources,
            "pass_through": self.pass_through,
            "timestamp": self.timestamp,
        }


class TemporalCoherenceValidator:
    """
    Temporal Coherence Validator — OMNIX Checkpoint 7 (ADR-032).

    Validates that a proposed action is TEMPORALLY ADMISSIBLE: not just
    statistically justified in isolation (Checkpoints 1-6), but coherent
    with the direction the system has been moving in recent cycles.

    Corrected architectural issues (post-architect review, Mar 2026):
      - Evaluates the pre-ECW INTENDED action (from EMA signal direction),
        not the initialized decision["action"] which defaults to HOLD.
      - Uses psycopg v3 (psycopg2 fallback) for DB compatibility.
      - Draws from DUAL data sources (shadow_trade_events + paper_trading_trades)
        to eliminate veto-event bias in trajectory representation.
      - Direction coherence uses MONOTONICITY of score deltas, not variance.
      - Signal taxonomy normalized (BULLISH/BEARISH/LONG/SHORT/UPTREND/DOWNTREND).
    """

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.threshold = float(os.getenv("TCV_THRESHOLD", str(TCV_THRESHOLD_DEFAULT)))
        self.window = int(os.getenv("TCV_WINDOW", str(TCV_WINDOW_DEFAULT)))
        self.min_events = int(os.getenv("TCV_MIN_EVENTS", str(TCV_MIN_EVENTS_DEFAULT)))
        self._driver: Optional[str] = None

    def validate(
        self,
        proposed_action: str,
        symbol: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TCVResult:
        """
        Validate temporal admissibility of proposed_action for symbol.

        Args:
            proposed_action: Pre-normalized intended action — "BUY", "SELL", or "HOLD".
                             Caller MUST pass the EMA-signal-derived action, NOT
                             decision["action"] (which is "HOLD" at evaluation time).
            symbol:          Trading symbol, e.g. "XBTUSD".
            context:         Optional dict with current ema_score, hmm_regime,
                             ema_signal_direction, etc.

        Returns:
            TCVResult. On any error → admissible=True, pass_through=True (fail-safe).
        """
        try:
            return self._validate_internal(
                proposed_action=proposed_action,
                symbol=symbol,
                context=context or {},
            )
        except Exception as exc:
            logger.warning(
                "[TCV] fail-safe triggered for %s (%s): %s",
                symbol,
                proposed_action,
                exc,
                exc_info=False,
            )
            return TCVResult(
                admissible=True,
                trajectory_score=0.0,
                reason="TCV_FAILSAFE: module error — pass-through (score=0 reflects absence of evidence, not trajectory failure)",
                events_analyzed=0,
                threshold_used=self.threshold,
                pass_through=True,
            )

    def _validate_internal(
        self,
        proposed_action: str,
        symbol: str,
        context: Dict[str, Any],
    ) -> TCVResult:
        events, sources = self._fetch_trajectory(symbol)

        if len(events) < self.min_events:
            logger.debug(
                "[TCV] Insufficient trajectory data for %s: %d events < %d required",
                symbol, len(events), self.min_events,
            )
            return TCVResult(
                admissible=True,
                trajectory_score=0.0,
                reason=(
                    f"INSUFFICIENT_TRAJECTORY_DATA: {len(events)} events "
                    f"< {self.min_events} required — pass-through "
                    f"(score=0 reflects absence of evidence, not trajectory failure)"
                ),
                events_analyzed=len(events),
                threshold_used=self.threshold,
                data_sources=sources,
                pass_through=True,
            )

        direction_score = self._score_direction_coherence(events, context)
        alignment_score = self._score_regime_alignment(events, proposed_action, context)
        stability_score = self._score_signal_stability(events)

        trajectory_score = (
            direction_score * 0.40
            + alignment_score * 0.35
            + stability_score * 0.25
        )

        admissible = trajectory_score >= self.threshold

        if admissible:
            reason = (
                f"TEMPORALLY_ADMISSIBLE: score={trajectory_score:.1f} "
                f">= threshold={self.threshold:.0f}"
            )
        else:
            reason = (
                f"TEMPORAL_INCOHERENCE: score={trajectory_score:.1f} "
                f"< threshold={self.threshold:.0f} "
                f"[dir={direction_score:.1f}, align={alignment_score:.1f}, "
                f"stab={stability_score:.1f}]"
            )
            logger.info(
                "[TCV] VETO candidate — %s | %s | sources=%s | events=%d",
                symbol, reason, sources, len(events),
            )

        return TCVResult(
            admissible=admissible,
            trajectory_score=round(trajectory_score, 3),
            reason=reason,
            dimension_scores={
                "direction_coherence": direction_score,
                "regime_alignment": alignment_score,
                "signal_stability": stability_score,
            },
            events_analyzed=len(events),
            threshold_used=self.threshold,
            data_sources=sources,
            pass_through=False,
        )

    def _fetch_trajectory(self, symbol: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Fetch recent decision trajectory from DUAL sources:
          1. shadow_trade_events  — vetoed/blocked signals
          2. paper_trading_trades — executed/approved signals

        Combining both gives an unbiased view of recent system behavior.
        Uses psycopg v3 (psycopg2 fallback).
        """
        if not self.db_url:
            return [], []

        try:
            rows, sources = self._fetch_with_psycopg3(symbol)
            return rows, sources
        except Exception as e3:
            logger.debug("[TCV] psycopg v3 fetch failed, trying psycopg2: %s", e3)
            try:
                rows, sources = self._fetch_with_psycopg2(symbol)
                return rows, sources
            except Exception as e2:
                logger.debug("[TCV] psycopg2 fetch also failed: %s", e2)
                return [], []

    def _fetch_with_psycopg3(self, symbol: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        import psycopg
        from psycopg.rows import dict_row

        since = datetime.now(timezone.utc) - timedelta(hours=72)
        half = self.window // 2

        conn = psycopg.connect(self.db_url, row_factory=dict_row)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    created_at,
                    intended_action   AS action_raw,
                    ema_score,
                    ema_signal        AS signal_raw,
                    hmm_regime,
                    'shadow'          AS source
                FROM shadow_trade_events
                WHERE symbol = %s
                  AND created_at >= %s
                  AND ema_score IS NOT NULL
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (symbol, since, half + 3),
            )
            shadow_rows = [dict(r) for r in cur.fetchall()]

            cur.execute(
                """
                SELECT
                    created_at,
                    side              AS action_raw,
                    strategy_confidence AS ema_score,
                    ema_regime_signal AS signal_raw,
                    hmm_regime,
                    'trade'           AS source
                FROM paper_trading_trades
                WHERE symbol = %s
                  AND created_at >= %s
                  AND strategy_confidence IS NOT NULL
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (symbol, since, half + 3),
            )
            trade_rows = [dict(r) for r in cur.fetchall()]
            cur.close()
        finally:
            conn.close()

        events = self._merge_and_normalize(shadow_rows, trade_rows)
        sources = list({r.get("source", "unknown") for r in events if r})
        return events[: self.window], sources

    def _fetch_with_psycopg2(self, symbol: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        import psycopg
        
        since = datetime.now(timezone.utc) - timedelta(hours=72)
        half = self.window // 2

        conn = psycopg.connect(self.db_url)
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                SELECT
                    created_at,
                    intended_action   AS action_raw,
                    ema_score,
                    ema_signal        AS signal_raw,
                    hmm_regime,
                    'shadow'          AS source
                FROM shadow_trade_events
                WHERE symbol = %s
                  AND created_at >= %s
                  AND ema_score IS NOT NULL
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (symbol, since, half + 3),
            )
            shadow_rows = [dict(r) for r in cur.fetchall()]

            cur.execute(
                """
                SELECT
                    created_at,
                    side              AS action_raw,
                    strategy_confidence AS ema_score,
                    ema_regime_signal AS signal_raw,
                    hmm_regime,
                    'trade'           AS source
                FROM paper_trading_trades
                WHERE symbol = %s
                  AND created_at >= %s
                  AND strategy_confidence IS NOT NULL
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (symbol, since, half + 3),
            )
            trade_rows = [dict(r) for r in cur.fetchall()]
            cur.close()
        finally:
            conn.close()

        events = self._merge_and_normalize(shadow_rows, trade_rows)
        sources = list({r.get("source", "unknown") for r in events if r})
        return events[: self.window], sources

    def _merge_and_normalize(
        self,
        shadow_rows: List[Dict],
        trade_rows: List[Dict],
    ) -> List[Dict[str, Any]]:
        """
        Merge shadow and trade events, sort by time (newest first),
        and normalize the signal taxonomy.
        """
        combined = shadow_rows + trade_rows
        for row in combined:
            raw_signal = row.get("signal_raw") or ""
            row["normalized_direction"] = _normalize_direction(raw_signal)

            raw_action = row.get("action_raw") or ""
            row["normalized_action"] = _normalize_direction(raw_action)

            score = row.get("ema_score")
            try:
                row["ema_score_f"] = float(score) if score is not None else None
            except (TypeError, ValueError):
                row["ema_score_f"] = None

        combined.sort(
            key=lambda r: r.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return combined

    def _score_direction_coherence(
        self,
        events: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> float:
        """
        Score (0-100): direction coherence via delta sign-change rate.

        Measures whether consecutive EMA-score changes maintain a consistent
        direction (all-up or all-down trend → coherent) vs. rapidly reversing
        (up-down-up-down → incoherent).

        Implementation: compute the sign-change rate of consecutive deltas.
          - No sign changes   → score = 100  (perfectly monotonic trend)
          - All sign changes  → score =   0  (perfectly alternating = incoherent)
          - Partial changes   → score = (1 − rate) × 100

        This correctly penalizes alternating signals [30→70→30→70] (rate=1.0,
        score=0) while rewarding monotonic trends (rate=0, score=100) or
        mostly-stable flat series (small deltas, low flip rate).
        """
        scores: List[float] = []
        current_ema = context.get("ema_score")
        if current_ema is not None:
            try:
                scores.append(float(current_ema))
            except (TypeError, ValueError):
                pass

        for e in events:
            v = e.get("ema_score_f")
            if v is not None:
                scores.append(v)

        if len(scores) < 2:
            return 0.0  # No evidence → score 0, not assumed coherence

        deltas = [scores[i] - scores[i + 1] for i in range(len(scores) - 1)]
        if len(deltas) < 2:
            return 0.0  # Single delta → cannot assess monotonicity

        signs = [1 if d > 0 else (-1 if d < 0 else 0) for d in deltas]
        sign_changes = sum(
            1 for i in range(len(signs) - 1)
            if signs[i] != 0 and signs[i + 1] != 0 and signs[i] != signs[i + 1]
        )
        max_changes = len(signs) - 1
        if max_changes == 0:
            return 0.0  # Cannot compute sign-change rate with a single delta

        change_rate = sign_changes / max_changes
        return round((1.0 - change_rate) * 100.0, 2)

    def _score_regime_alignment(
        self,
        events: List[Dict[str, Any]],
        proposed_action: str,
        context: Dict[str, Any],
    ) -> float:
        """
        Score (0-100): alignment between proposed_action and dominant regime.

        Uses recent events (unweighted vote) + current context (1 vote).
        Dominant regime must represent >= 40% of votes to influence scoring.
        Below 40% → mixed regime → neutral score (65).
        """
        regime_counts: Dict[str, int] = {}

        current_regime = (context.get("hmm_regime") or "").upper().strip()
        if current_regime and current_regime not in ("", "NONE", "UNKNOWN"):
            regime_counts[current_regime] = regime_counts.get(current_regime, 0) + 1

        for e in events[:10]:
            r = (e.get("hmm_regime") or "").upper().strip()
            if r and r not in ("", "NONE", "UNKNOWN"):
                regime_counts[r] = regime_counts.get(r, 0) + 1

        if not regime_counts:
            return 65.0

        total_votes = sum(regime_counts.values())
        dominant_regime = max(regime_counts, key=lambda k: regime_counts[k])
        dominant_pct = regime_counts[dominant_regime] / total_votes

        if dominant_pct < 0.40:
            return 65.0

        action_upper = (proposed_action or "HOLD").upper()
        allowed = _REGIME_ALLOWED_ACTIONS.get(dominant_regime, ["BUY", "SELL", "HOLD"])

        if action_upper in allowed:
            base = 70.0 + dominant_pct * 30.0
        else:
            base = max(0.0, (1.0 - dominant_pct) * 40.0)

        return round(min(100.0, max(0.0, base)), 2)

    def _score_signal_stability(self, events: List[Dict[str, Any]]) -> float:
        """
        Score (0-100): stability of normalized signal directions over recent events.

        Measures: what fraction of consecutive signal pairs do NOT flip direction?
        All-BULLISH trajectory → 100. Alternating BULLISH/BEARISH → near 0.

        Uses normalized_direction (BUY/SELL/HOLD) for taxonomy-agnostic evaluation.
        """
        directions = [
            e.get("normalized_direction", "HOLD")
            for e in events
            if e.get("normalized_direction")
        ]

        if len(directions) < 2:
            return 0.0  # No evidence → score 0, not assumed stability

        flips = sum(
            1 for i in range(len(directions) - 1)
            if directions[i] != directions[i + 1]
        )
        max_flips = len(directions) - 1
        flip_rate = flips / max_flips if max_flips > 0 else 0.0

        return round((1.0 - flip_rate) * 100.0, 2)
