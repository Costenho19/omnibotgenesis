#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regime-Conditioned Kelly (RCK) — ADR-035 | March 2026

Provides win_rate, avg_win, avg_loss statistics segmented by MARKET REGIME
for use as inputs to Kelly Criterion position sizing.

The core problem: using global historical win_rate (e.g. 0.55) merges
TRENDING regime performance (typically better) with VOLATILE regime
performance (typically worse). The result is a Kelly fraction that is
neither optimal for trending markets nor cautious enough for volatile ones.

SOLUTION: Query regime-segmented statistics from executed trades.

FALLBACK CHAIN (3 levels):
  1. Regime-specific stats (≥ min_samples in current regime)
  2. Global stats (any regime, ≥ min_global_samples)
  3. Conservative defaults (win_rate=0.50, avg_win=1%, avg_loss=1%)

CONFIDENCE LEVELS:
  HIGH   (≥ 30 samples, regime-specific)
  MEDIUM (10-29 samples, regime-specific)
  LOW    (< 10 samples, fallback used)

CONFIG:
  RCK_MIN_SAMPLES     — min samples for regime-specific (default 10)
  RCK_MIN_GLOBAL      — min samples for global fallback (default 5)
  RCK_LOOKBACK_DAYS   — trading history window (default 90)

Harold Nunes — OMNIX Decision Governance Infrastructure
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

RCK_MIN_SAMPLES_DEFAULT = 10
RCK_MIN_GLOBAL_DEFAULT = 5
RCK_LOOKBACK_DAYS_DEFAULT = 90

CONSERVATIVE_DEFAULTS = {
    "win_rate": 0.50,
    "avg_win": 0.01,
    "avg_loss": 0.01,
}

VALID_REGIMES = {
    "TRENDING", "UPTREND", "DOWNTREND",
    "BULLISH", "BEARISH",
    "RANGING", "NEUTRAL", "VOLATILE",
}


@dataclass
class RegimeKellyStats:
    """
    Kelly input statistics conditioned on a specific market regime.

    Fields:
        win_rate:       Fraction of winning trades [0-1].
        avg_win:        Average relative gain on winning trades (e.g. 0.025 = 2.5%).
        avg_loss:       Average relative loss on losing trades (positive, e.g. 0.015 = 1.5%).
        sample_count:   Number of trades used to compute these statistics.
        regime:         Market regime for which stats were computed.
        confidence:     "HIGH", "MEDIUM", or "LOW".
        fallback_used:  True if regime-specific stats were unavailable.
        fallback_level: "REGIME", "GLOBAL", or "DEFAULTS".
        timestamp:      ISO-8601 UTC timestamp of computation.
    """

    win_rate: float
    avg_win: float
    avg_loss: float
    sample_count: int
    regime: str
    confidence: str
    fallback_used: bool = False
    fallback_level: str = "REGIME"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "win_rate": round(self.win_rate, 4),
            "avg_win": round(self.avg_win, 6),
            "avg_loss": round(self.avg_loss, 6),
            "sample_count": self.sample_count,
            "regime": self.regime,
            "confidence": self.confidence,
            "fallback_used": self.fallback_used,
            "fallback_level": self.fallback_level,
            "timestamp": self.timestamp,
        }

    @property
    def win_loss_ratio(self) -> float:
        if self.avg_loss <= 0:
            return 1.0
        return self.avg_win / self.avg_loss

    @property
    def kelly_fraction_raw(self) -> float:
        """Raw Kelly fraction (unbounded). Use with fractional Kelly in KellyCriterionOptimizer."""
        p = self.win_rate
        q = 1.0 - p
        r = self.win_loss_ratio
        if r <= 0:
            return 0.0
        return max(0.0, (p * r - q) / r)


class RegimeConditionedKelly:
    """
    Regime-Conditioned Kelly (RCK) — ADR-035.

    Queries historical trade data segmented by HMM market regime to derive
    statistically grounded Kelly inputs specific to the current market regime.

    Usage:
        rck = RegimeConditionedKelly(db_url=os.getenv("DATABASE_URL"))
        stats = rck.get_regime_stats(regime="TRENDING", symbol="XBTUSD")
        kelly_result = kelly_optimizer.calculate_optimal_position(
            win_rate=stats.win_rate,
            avg_win=stats.avg_win,
            avg_loss=stats.avg_loss,
            ...
        )

    When DATABASE_URL is not available or there is insufficient data,
    the fallback chain ensures the system continues with conservative defaults.
    """

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.min_samples = int(os.getenv("RCK_MIN_SAMPLES", str(RCK_MIN_SAMPLES_DEFAULT)))
        self.min_global = int(os.getenv("RCK_MIN_GLOBAL", str(RCK_MIN_GLOBAL_DEFAULT)))
        self.lookback_days = int(os.getenv("RCK_LOOKBACK_DAYS", str(RCK_LOOKBACK_DAYS_DEFAULT)))

    def get_regime_stats(
        self,
        regime: str,
        symbol: Optional[str] = None,
    ) -> RegimeKellyStats:
        """
        Compute Kelly inputs for the given regime.

        Falls back to global stats, then defaults if insufficient data.
        Never raises — returns conservative defaults on any error.

        Args:
            regime:  Market regime string (e.g. "TRENDING", "VOLATILE").
            symbol:  Optional symbol filter (e.g. "XBTUSD").

        Returns:
            RegimeKellyStats with confidence level and fallback metadata.
        """
        try:
            return self._compute_stats(regime.upper(), symbol)
        except Exception as exc:
            logger.warning(
                "⚠️ [RCK] Exception computing regime stats for %s/%s: %s → defaults",
                regime, symbol, exc
            )
            return self._default_stats(regime, fallback_level="DEFAULTS")

    def _compute_stats(
        self,
        regime: str,
        symbol: Optional[str],
    ) -> RegimeKellyStats:
        if not self.db_url:
            logger.debug("[RCK] No DB URL → conservative defaults")
            return self._default_stats(regime, fallback_level="DEFAULTS")

        regime_trades = self._query_trades(regime=regime, symbol=symbol)

        if len(regime_trades) >= self.min_samples:
            stats = self._calc_stats(regime_trades)
            confidence = "HIGH" if len(regime_trades) >= 30 else "MEDIUM"
            return RegimeKellyStats(
                win_rate=stats["win_rate"],
                avg_win=stats["avg_win"],
                avg_loss=stats["avg_loss"],
                sample_count=len(regime_trades),
                regime=regime,
                confidence=confidence,
                fallback_used=False,
                fallback_level="REGIME",
            )

        global_trades = self._query_trades(regime=None, symbol=symbol)
        if len(global_trades) >= self.min_global:
            stats = self._calc_stats(global_trades)
            logger.info(
                "[RCK] Regime '%s' has only %d samples (need %d) → global fallback (%d trades)",
                regime, len(regime_trades), self.min_samples, len(global_trades)
            )
            return RegimeKellyStats(
                win_rate=stats["win_rate"],
                avg_win=stats["avg_win"],
                avg_loss=stats["avg_loss"],
                sample_count=len(global_trades),
                regime=regime,
                confidence="LOW",
                fallback_used=True,
                fallback_level="GLOBAL",
            )

        logger.info(
            "[RCK] Insufficient data (regime=%d, global=%d) → conservative defaults",
            len(regime_trades), len(global_trades)
        )
        return self._default_stats(regime, fallback_level="DEFAULTS")

    def _query_trades(
        self,
        regime: Optional[str],
        symbol: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Query paper_trading_trades for regime-segmented history.

        Extracts HMM regime from decision_trace JSON when available.
        Returns a list of trade dicts with 'profit_loss' field.
        """
        try:
            import psycopg
            conn_factory = lambda: psycopg.connect(self.db_url)
        except ImportError:
            try:
                import psycopg as pg
                conn_factory = lambda: pg.connect(self.db_url)
            except ImportError:
                logger.warning("[RCK] No DB driver (psycopg/psycopg2)")
                return []

        try:
            conn = conn_factory()
            cursor = conn.cursor()

            if regime is not None:
                query = f"""
                    SELECT profit_loss
                    FROM paper_trading_trades
                    WHERE created_at >= NOW() - INTERVAL '{self.lookback_days} days'
                    AND hmm_regime = %s
                    {("AND symbol = %s" if symbol else "")}
                    ORDER BY created_at DESC
                    LIMIT 500
                """
                params: Tuple = (regime,)
                if symbol:
                    params = params + (symbol,)
            else:
                query = f"""
                    SELECT profit_loss
                    FROM paper_trading_trades
                    WHERE created_at >= NOW() - INTERVAL '{self.lookback_days} days'
                    {("AND symbol = %s" if symbol else "")}
                    ORDER BY created_at DESC
                    LIMIT 500
                """
                params = (symbol,) if symbol else ()

            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            return [
                {"profit_loss": float(r[0]) if r[0] is not None else 0.0}
                for r in rows
                if r[0] is not None
            ]
        except Exception as exc:
            logger.warning("[RCK] DB query error: %s", exc)
            return []

    @staticmethod
    def _calc_stats(trades: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Compute win_rate, avg_win, avg_loss from trade list.

        avg_win and avg_loss are expressed as absolute fractions (positive).
        Degenerate cases (no wins/no losses) fall back to 1% each.
        """
        if not trades:
            return CONSERVATIVE_DEFAULTS.copy()

        pnls = [t["profit_loss"] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]
        total = len(pnls)

        win_rate = len(wins) / total if total > 0 else 0.50
        avg_win = sum(wins) / len(wins) if wins else 0.01
        avg_loss = sum(losses) / len(losses) if losses else 0.01

        avg_win = max(avg_win, 0.001)
        avg_loss = max(avg_loss, 0.001)

        return {
            "win_rate": max(0.0, min(1.0, win_rate)),
            "avg_win": avg_win,
            "avg_loss": avg_loss,
        }

    def _default_stats(self, regime: str, fallback_level: str = "DEFAULTS") -> RegimeKellyStats:
        return RegimeKellyStats(
            win_rate=CONSERVATIVE_DEFAULTS["win_rate"],
            avg_win=CONSERVATIVE_DEFAULTS["avg_win"],
            avg_loss=CONSERVATIVE_DEFAULTS["avg_loss"],
            sample_count=0,
            regime=regime,
            confidence="LOW",
            fallback_used=True,
            fallback_level=fallback_level,
        )
