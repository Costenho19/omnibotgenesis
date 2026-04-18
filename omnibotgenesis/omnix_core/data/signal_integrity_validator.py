#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signal Integrity Validator (SIV) — OMNIX Checkpoint 0
ADR-033 | March 2026

Validates the quality and integrity of ALL input data sources BEFORE
_analyze_market() processes them. This is Checkpoint 0 — the pre-pipeline
gate that ensures downstream analysis operates on trustworthy data.

If data is stale, incomplete, anomalous, or cross-source inconsistent,
even a perfect 7-checkpoint governance pipeline produces meaningless output.
SIV makes the implicit assumption of data quality explicit and enforced.

VALIDATION CATEGORIES (4):
  1. Data Freshness    — When was each source last successfully fetched?
  2. Completeness      — Are all required fields present and non-None?
  3. Anomaly Detection — Is the price within statistically reasonable bounds?
  4. Cross-Source      — Do multiple price sources agree within tolerance?

SCORING:
  Each category contributes to a composite score [0-100].
  score < SIV_THRESHOLD (default 60) → FAIL → pipeline returns HOLD.
  Violation severity: CRITICAL (-30), HIGH (-20), MEDIUM (-10), LOW (-5).

FAIL-SAFE:
  On any SIV module error → pass-through (admissible=True).
  Never blocks pipeline due to its own failure.

CONFIG:
  SIV_THRESHOLD (default 60) — minimum acceptable score.
  SIV_PRICE_STALE_SECS (default 300) — max price age in seconds.
  SIV_OHLC_STALE_SECS (default 900) — max OHLC data age in seconds.
  SIV_ANOMALY_THRESHOLD (default 0.20) — max single-cycle price change (20%).
  SIV_SPREAD_THRESHOLD (default 0.05) — max bid/ask spread (5%).
  SIV_CROSS_SOURCE_TOLERANCE (default 0.02) — max cross-source price diff (2%).

Harold Nunes — OMNIX Decision Governance Infrastructure
"""

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

SIV_THRESHOLD_DEFAULT = 60.0
SIV_PRICE_STALE_SECS_DEFAULT = 300.0
SIV_OHLC_STALE_SECS_DEFAULT = 900.0
SIV_ANOMALY_THRESHOLD_DEFAULT = 0.20
SIV_SPREAD_THRESHOLD_DEFAULT = 0.05
SIV_CROSS_SOURCE_TOLERANCE_DEFAULT = 0.02


class ViolationSeverity:
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


SEVERITY_DEDUCTIONS = {
    ViolationSeverity.CRITICAL: 30,
    ViolationSeverity.HIGH: 20,
    ViolationSeverity.MEDIUM: 10,
    ViolationSeverity.LOW: 5,
}


@dataclass
class SIVViolation:
    """A single data integrity violation."""
    category: str
    code: str
    severity: str
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "code": self.code,
            "severity": self.severity,
            "detail": self.detail,
        }


@dataclass
class SIVResult:
    """
    Result of Signal Integrity Validation.

    Fields:
        passed:               True if score >= threshold.
        score:                Composite integrity score [0-100].
        violations:           List of detected violations.
        sources_checked:      How many data categories were evaluated.
        threshold_used:       SIV threshold at evaluation time.
        pass_through:         True if SIV returned passed due to module error.
        reason:               ADR-066: populated on pass-through paths to explain score=0.
        timestamp:            ISO-8601 UTC timestamp.
    """
    passed: bool
    score: float
    violations: List[SIVViolation] = field(default_factory=list)
    sources_checked: int = 0
    threshold_used: float = SIV_THRESHOLD_DEFAULT
    pass_through: bool = False
    reason: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "passed": self.passed,
            "score": round(self.score, 2),
            "violations": [v.to_dict() for v in self.violations],
            "violation_count": len(self.violations),
            "sources_checked": self.sources_checked,
            "threshold_used": self.threshold_used,
            "pass_through": self.pass_through,
            "timestamp": self.timestamp,
        }
        if self.reason:
            d["reason"] = self.reason
        return d


class SignalIntegrityValidator:
    """
    Signal Integrity Validator — OMNIX Checkpoint 0 (ADR-033).

    Validates all data inputs at the START of the governance pipeline,
    before any analysis or scoring runs. If the data is not trustworthy,
    all downstream checkpoints are operating on corrupted foundations.

    Complements the existing MarketDataValidator (price freshness only,
    at execution time) with a broader, earlier, multi-category check.
    """

    def __init__(self, redis_cache=None):
        self.threshold = float(
            os.getenv("SIV_THRESHOLD", str(SIV_THRESHOLD_DEFAULT))
        )
        self.price_stale_secs = float(
            os.getenv("SIV_PRICE_STALE_SECS", str(SIV_PRICE_STALE_SECS_DEFAULT))
        )
        self.ohlc_stale_secs = float(
            os.getenv("SIV_OHLC_STALE_SECS", str(SIV_OHLC_STALE_SECS_DEFAULT))
        )
        self.anomaly_threshold = float(
            os.getenv("SIV_ANOMALY_THRESHOLD", str(SIV_ANOMALY_THRESHOLD_DEFAULT))
        )
        self.spread_threshold = float(
            os.getenv("SIV_SPREAD_THRESHOLD", str(SIV_SPREAD_THRESHOLD_DEFAULT))
        )
        self.cross_source_tolerance = float(
            os.getenv(
                "SIV_CROSS_SOURCE_TOLERANCE",
                str(SIV_CROSS_SOURCE_TOLERANCE_DEFAULT),
            )
        )
        self._redis = redis_cache
        self._price_history: Dict[str, List[float]] = {}

    def validate(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        fetch_timestamps: Optional[Dict[str, float]] = None,
        secondary_prices: Optional[Dict[str, float]] = None,
    ) -> SIVResult:
        """
        Validate signal integrity for the given symbol and market data.

        Args:
            symbol:            Trading symbol, e.g. "XBTUSD".
            market_data:       Dict from _analyze_market() containing price,
                               bid, ask, volume, ohlc, etc.
            fetch_timestamps:  Dict mapping source name → Unix timestamp of last
                               successful fetch. e.g. {"kraken": 1234567890.0}
            secondary_prices:  Optional dict of price from secondary sources.
                               e.g. {"coingecko": 84500.0}

        Returns:
            SIVResult. On any module error → passed=True, pass_through=True.
        """
        try:
            return self._validate_internal(
                symbol=symbol,
                market_data=market_data,
                fetch_timestamps=fetch_timestamps or {},
                secondary_prices=secondary_prices or {},
            )
        except Exception as exc:
            logger.warning(
                "[SIV] fail-safe triggered for %s: %s", symbol, exc, exc_info=False
            )
            return SIVResult(
                passed=True,
                score=0.0,
                violations=[],
                sources_checked=0,
                threshold_used=self.threshold,
                pass_through=True,
                reason=f"SIV_FAILSAFE: score=0 reflects module error, not data quality — {exc}",
            )

    def _validate_internal(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        fetch_timestamps: Dict[str, float],
        secondary_prices: Dict[str, float],
    ) -> SIVResult:
        violations: List[SIVViolation] = []
        sources_checked = 0
        now = time.time()

        violations += self._check_freshness(fetch_timestamps, now)
        sources_checked += 1

        price_violations, current_price = self._check_completeness(market_data)
        violations += price_violations
        sources_checked += 1

        if current_price is not None:
            violations += self._check_anomaly(symbol, current_price, market_data)
            sources_checked += 1

            if secondary_prices:
                violations += self._check_cross_source(
                    symbol, current_price, secondary_prices
                )
                sources_checked += 1

            self._update_price_history(symbol, current_price)

        score = self._compute_score(violations)
        passed = score >= self.threshold

        if not passed:
            logger.warning(
                "[SIV] FAIL %s | score=%.1f < threshold=%.0f | violations=%d",
                symbol,
                score,
                self.threshold,
                len(violations),
            )
            for v in violations:
                logger.debug(
                    "[SIV] %s %s: %s — %s",
                    v.severity,
                    v.code,
                    v.category,
                    v.detail,
                )
        else:
            logger.debug(
                "[SIV] PASS %s | score=%.1f | violations=%d",
                symbol,
                score,
                len(violations),
            )

        return SIVResult(
            passed=passed,
            score=score,
            violations=violations,
            sources_checked=sources_checked,
            threshold_used=self.threshold,
            pass_through=False,
        )

    def _check_freshness(
        self, fetch_timestamps: Dict[str, float], now: float
    ) -> List[SIVViolation]:
        violations = []

        price_ts = fetch_timestamps.get("kraken") or fetch_timestamps.get("price")
        if price_ts is not None:
            age = now - price_ts
            if age > self.price_stale_secs:
                violations.append(
                    SIVViolation(
                        category="freshness",
                        code="PRICE_DATA_STALE",
                        severity=ViolationSeverity.CRITICAL,
                        detail=(
                            f"Price data is {age:.0f}s old "
                            f"(max {self.price_stale_secs:.0f}s)"
                        ),
                    )
                )

        ohlc_ts = fetch_timestamps.get("ohlc")
        if ohlc_ts is not None:
            age = now - ohlc_ts
            if age > self.ohlc_stale_secs:
                violations.append(
                    SIVViolation(
                        category="freshness",
                        code="OHLC_DATA_STALE",
                        severity=ViolationSeverity.HIGH,
                        detail=(
                            f"OHLC data is {age:.0f}s old "
                            f"(max {self.ohlc_stale_secs:.0f}s)"
                        ),
                    )
                )

        sentiment_ts = fetch_timestamps.get("sentiment")
        if sentiment_ts is not None:
            age = now - sentiment_ts
            if age > 1800:
                violations.append(
                    SIVViolation(
                        category="freshness",
                        code="SENTIMENT_DATA_STALE",
                        severity=ViolationSeverity.LOW,
                        detail=f"Sentiment data is {age:.0f}s old (max 1800s)",
                    )
                )

        return violations

    def _check_completeness(
        self, market_data: Dict[str, Any]
    ) -> Tuple[List[SIVViolation], Optional[float]]:
        violations = []
        current_price: Optional[float] = None

        raw_price = market_data.get("price")
        if raw_price is None:
            raw_price = market_data.get("current_price")
        if raw_price is None:
            violations.append(
                SIVViolation(
                    category="completeness",
                    code="MISSING_PRICE",
                    severity=ViolationSeverity.CRITICAL,
                    detail="Current price is None — cannot evaluate any signal",
                )
            )
            return violations, None

        try:
            current_price = float(raw_price)
        except (TypeError, ValueError):
            violations.append(
                SIVViolation(
                    category="completeness",
                    code="INVALID_PRICE_TYPE",
                    severity=ViolationSeverity.CRITICAL,
                    detail=f"Price '{raw_price}' cannot be converted to float",
                )
            )
            return violations, None

        if current_price <= 0:
            violations.append(
                SIVViolation(
                    category="completeness",
                    code="NON_POSITIVE_PRICE",
                    severity=ViolationSeverity.CRITICAL,
                    detail=f"Price {current_price} is non-positive",
                )
            )
            return violations, None

        volume = market_data.get("volume") or market_data.get("volume_24h")
        if volume is None:
            violations.append(
                SIVViolation(
                    category="completeness",
                    code="MISSING_VOLUME",
                    severity=ViolationSeverity.MEDIUM,
                    detail="24h volume is None — liquidity assessment unavailable",
                )
            )

        ohlc = market_data.get("ohlc") or market_data.get("candles")
        if ohlc is None:
            violations.append(
                SIVViolation(
                    category="completeness",
                    code="MISSING_OHLC",
                    severity=ViolationSeverity.MEDIUM,
                    detail="OHLC data is None — technical analysis degraded",
                )
            )

        return violations, current_price

    def _check_anomaly(
        self,
        symbol: str,
        current_price: float,
        market_data: Dict[str, Any],
    ) -> List[SIVViolation]:
        violations = []

        history = self._price_history.get(symbol, [])
        if history:
            last_price = history[-1]
            if last_price > 0:
                change_pct = abs(current_price - last_price) / last_price
                if change_pct > self.anomaly_threshold:
                    violations.append(
                        SIVViolation(
                            category="anomaly",
                            code="PRICE_SPIKE_ANOMALY",
                            severity=ViolationSeverity.HIGH,
                            detail=(
                                f"Price changed {change_pct:.1%} in one cycle "
                                f"({last_price:.2f} → {current_price:.2f}) "
                                f"vs max {self.anomaly_threshold:.0%}"
                            ),
                        )
                    )

        bid = market_data.get("bid")
        ask = market_data.get("ask")
        if bid is not None and ask is not None:
            try:
                bid_f = float(bid)
                ask_f = float(ask)
                if bid_f > 0 and ask_f > 0:
                    spread_pct = (ask_f - bid_f) / bid_f
                    if spread_pct > self.spread_threshold:
                        violations.append(
                            SIVViolation(
                                category="anomaly",
                                code="SPREAD_ANOMALY",
                                severity=ViolationSeverity.MEDIUM,
                                detail=(
                                    f"Bid/ask spread {spread_pct:.2%} "
                                    f"exceeds {self.spread_threshold:.0%} threshold "
                                    f"(bid={bid_f:.2f}, ask={ask_f:.2f})"
                                ),
                            )
                        )
                    if bid_f >= ask_f:
                        violations.append(
                            SIVViolation(
                                category="anomaly",
                                code="INVERTED_SPREAD",
                                severity=ViolationSeverity.CRITICAL,
                                detail=(
                                    f"Inverted spread: bid {bid_f:.2f} >= ask {ask_f:.2f}"
                                ),
                            )
                        )
            except (TypeError, ValueError):
                pass

        return violations

    def _check_cross_source(
        self,
        symbol: str,
        primary_price: float,
        secondary_prices: Dict[str, float],
    ) -> List[SIVViolation]:
        violations = []
        for source, sec_price in secondary_prices.items():
            if sec_price is None or sec_price <= 0:
                continue
            try:
                sec_f = float(sec_price)
            except (TypeError, ValueError):
                continue

            diff_pct = abs(primary_price - sec_f) / primary_price
            if diff_pct > self.cross_source_tolerance:
                severity = (
                    ViolationSeverity.HIGH
                    if diff_pct > self.cross_source_tolerance * 3
                    else ViolationSeverity.MEDIUM
                )
                violations.append(
                    SIVViolation(
                        category="cross_source",
                        code="SOURCE_PRICE_DISCREPANCY",
                        severity=severity,
                        detail=(
                            f"Kraken {primary_price:.2f} vs {source} {sec_f:.2f} "
                            f"= {diff_pct:.2%} diff "
                            f"(max {self.cross_source_tolerance:.0%})"
                        ),
                    )
                )

        return violations

    def _compute_score(self, violations: List[SIVViolation]) -> float:
        score = 100.0
        for v in violations:
            deduction = SEVERITY_DEDUCTIONS.get(v.severity, 10)
            score -= deduction
        return round(max(0.0, min(100.0, score)), 2)

    def _update_price_history(self, symbol: str, price: float) -> None:
        if symbol not in self._price_history:
            self._price_history[symbol] = []
        self._price_history[symbol].append(price)
        if len(self._price_history[symbol]) > 20:
            self._price_history[symbol] = self._price_history[symbol][-20:]
