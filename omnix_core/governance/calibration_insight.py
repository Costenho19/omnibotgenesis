"""
ADR-128 — Phase 4: Calibration Insight Engine

Internal query/analysis layer on top of filter_calibration_metrics (ADR-127).
Provides drift detection, anomaly classification, per-domain comparisons,
and structured report generation for governance audit and monitoring purposes.

No UI, no write path, zero impact on the governance decision core.

Usage
─────
    from omnix_core.governance.calibration_insight import CalibrationInsightEngine
    from omnix_core.governance.filter_calibration_metrics import FilterCalibrationMetricsService

    svc    = FilterCalibrationMetricsService()
    engine = CalibrationInsightEngine(svc)

    report = engine.full_report(domain="trading")
    anomalies = engine.detect_anomalies(domain="trading")

Anomaly Thresholds
──────────────────
    BLOCK_RATE_DROP   : 1h block_rate drops >= 15pp below 1d baseline  (≥0.15)
    HOLD_SPIKE        : 1h hold_rate rises  >= 10pp above 1d baseline  (≥0.10)
    DCI_SURGE         : 1h avg DCI rises    >= 10pts above 1d baseline
    COHERENCE_DRIFT   : |1h avg coherence - 1d avg coherence| >= 10pts
    BS_HIGH_SURGE     : 1h BS_HIGH rate rises >= 5pp above 1d baseline (≥0.05)
    ESCALATION_SURGE  : 1h escalation_rate rises >= 5pp above 1d baseline

Severity Levels
───────────────
    CRITICAL  : multiple simultaneous anomalies, or single extreme deviation
    HIGH      : single significant anomaly above threshold × 2
    MEDIUM    : single anomaly at or above threshold
    LOW       : near-threshold signal (threshold × 0.5 to threshold)
    NONE      : no anomaly detected
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.CalibrationInsight")

# ── Anomaly threshold constants ─────────────────────────────────────────────
BLOCK_RATE_DROP_THRESHOLD: float = 0.15   # 15 percentage points
HOLD_SPIKE_THRESHOLD:      float = 0.10   # 10 percentage points
DCI_SURGE_THRESHOLD:       float = 10.0   # 10 DCI points (0-100 scale)
COHERENCE_DRIFT_THRESHOLD: float = 10.0   # 10 coherence points (0-100 scale)
BS_HIGH_SURGE_THRESHOLD:   float = 0.05   # 5 percentage points
ESCALATION_SURGE_THRESHOLD: float = 0.05  # 5 percentage points

# Severity scale multipliers
_CRITICAL_MULT = 2.5
_HIGH_MULT     = 2.0

# Coherence bands
COH_HIGH_THRESHOLD:   float = 70.0   # high agreement
COH_MEDIUM_THRESHOLD: float = 40.0   # medium agreement (40–69)
# below 40 = low agreement

# Supported windows in chronological comparison order
_WINDOWS: Tuple[str, ...] = ("1h", "1d", "1w")


# ── Anomaly dataclass ────────────────────────────────────────────────────────

@dataclass
class CalibrationAnomaly:
    """A single detected anomaly in calibration metrics."""
    anomaly_type: str          # BLOCK_RATE_DROP | HOLD_SPIKE | DCI_SURGE |
                               # COHERENCE_DRIFT | BS_HIGH_SURGE | ESCALATION_SURGE
    severity:     str          # CRITICAL | HIGH | MEDIUM | LOW
    domain:       Optional[str]
    description:  str
    current_value:   float
    baseline_value:  float
    deviation:       float     # absolute deviation (current - baseline)
    threshold:       float
    window_current:  str       # e.g. "1h"
    window_baseline: str       # e.g. "1d"
    detected_at:     str       # ISO timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_type":    self.anomaly_type,
            "severity":        self.severity,
            "domain":          self.domain,
            "description":     self.description,
            "current_value":   round(self.current_value, 4),
            "baseline_value":  round(self.baseline_value, 4),
            "deviation":       round(self.deviation, 4),
            "threshold":       self.threshold,
            "window_current":  self.window_current,
            "window_baseline": self.window_baseline,
            "detected_at":     self.detected_at,
        }


def _severity_from_deviation(deviation: float, threshold: float) -> str:
    """Classify severity based on how far the deviation exceeds the threshold."""
    if deviation >= threshold * _CRITICAL_MULT:
        return "CRITICAL"
    if deviation >= threshold * _HIGH_MULT:
        return "HIGH"
    return "MEDIUM"


def _empty_coherence_distribution(window: str, domain: Optional[str]) -> Dict[str, Any]:
    return {
        "window":         window,
        "domain":         domain,
        "available":      False,
        "total_with_coh": 0,
        "avg":  None, "min": None, "max": None, "p50": None, "p90": None,
        "high_count":   0, "high_rate":   0.0,
        "medium_count": 0, "medium_rate": 0.0,
        "low_count":    0, "low_rate":    0.0,
    }


def _empty_anomaly_result(domain: Optional[str]) -> Dict[str, Any]:
    return {
        "domain":      domain,
        "available":   False,
        "anomalies":   [],
        "summary":     {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
        "overall_severity": "NONE",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Main engine ──────────────────────────────────────────────────────────────

class CalibrationInsightEngine:
    """
    Internal analysis engine for governance calibration metrics.

    Wraps FilterCalibrationMetricsService (ADR-127) and provides:
    - Outcome distribution snapshots per gate and domain
    - DCI trend comparison across time windows
    - Coherence score distribution
    - Black Swan frequency trends
    - Anomaly detection with severity classification
    - Full structured reports

    All methods return structured dicts. Never raises on DB unavailability
    (returns {available: False, ...} instead).

    Thread-safe: read-only, no shared mutable state.
    """

    def __init__(self, service=None, db_url: Optional[str] = None):
        """
        Parameters
        ──────────
        service : FilterCalibrationMetricsService instance (optional).
                  If None, creates one using db_url or environment variables.
        db_url  : explicit DB URL (overrides OMNIX_DB_URL env var).
        """
        if service is not None:
            self._svc = service
        else:
            from omnix_core.governance.filter_calibration_metrics import (
                FilterCalibrationMetricsService,
            )
            _url = db_url or os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
            self._svc = FilterCalibrationMetricsService(db_url=_url)

    # ── Outcome distribution snapshot ────────────────────────────────────────

    def snapshot(
        self,
        *,
        domain: Optional[str] = None,
        window: str = "1d",
    ) -> Dict[str, Any]:
        """
        Outcome distribution snapshot for all gates in the given window.

        Wraps query_all_gate_stats() and adds a final_decision breakdown.

        Returns
        ───────
        {
            "window":           str,
            "domain":           str | None,
            "available":        bool,
            "gate_stats":       { gate_name: {pass_rate, block_rate, hold_rate, ...} },
            "decision_summary": { "APPROVED": int, "BLOCKED": int, "HOLD": int, "total": int },
            "generated_at":     str,
        }
        """
        try:
            gate_stats = self._svc.query_all_gate_stats(domain=domain, window=window)
            decision_summary = self._query_decision_summary(domain=domain, window=window)
            return {
                "window":           window,
                "domain":           domain,
                "available":        True,
                "gate_stats":       gate_stats,
                "decision_summary": decision_summary,
                "generated_at":     datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            logger.warning("[CIE] snapshot unavailable (domain=%s, window=%s): %s", domain, window, exc)
            return {
                "window":           window,
                "domain":           domain,
                "available":        False,
                "gate_stats":       {},
                "decision_summary": {},
                "generated_at":     datetime.now(timezone.utc).isoformat(),
            }

    # ── DCI trend ────────────────────────────────────────────────────────────

    def dci_trend(
        self,
        *,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        DCI trend comparison across all time windows (1h → 1d → 1w).

        Surfaces avg, p50, p90 per window and computes the short/long delta
        (1h avg minus 1d avg) to indicate directional drift.

        Returns
        ───────
        {
            "domain":      str | None,
            "available":   bool,
            "windows": {
                "1h": { total_with_dci, avg, p50, p90, aligned_rate,
                         tensioned_rate, contradictory_rate },
                "1d": { ... },
                "1w": { ... },
            },
            "delta_1h_vs_1d": float | None,   # positive = DCI rising (more contradictory)
            "delta_1d_vs_1w": float | None,
            "trend_direction": "RISING" | "FALLING" | "STABLE" | "UNKNOWN",
            "analyzed_at": str,
        }
        """
        windows_data: Dict[str, Dict[str, Any]] = {}
        available = True

        for w in _WINDOWS:
            try:
                dist = self._svc.query_dci_distribution(domain=domain, window=w)
                windows_data[w] = {
                    "total_with_dci":      dist.get("total_with_dci", 0),
                    "avg":                 dist.get("avg"),
                    "p50":                 dist.get("p50"),
                    "p90":                 dist.get("p90"),
                    "aligned_rate":        dist.get("aligned_rate", 0.0),
                    "tensioned_rate":      dist.get("tensioned_rate", 0.0),
                    "contradictory_rate":  dist.get("contradictory_rate", 0.0),
                }
            except Exception as exc:
                logger.warning("[CIE] dci_trend window=%s unavailable: %s", w, exc)
                available = False
                windows_data[w] = {
                    "total_with_dci": 0,
                    "avg": None, "p50": None, "p90": None,
                    "aligned_rate": 0.0, "tensioned_rate": 0.0, "contradictory_rate": 0.0,
                }

        avg_1h = windows_data["1h"].get("avg")
        avg_1d = windows_data["1d"].get("avg")
        avg_1w = windows_data["1w"].get("avg")

        delta_1h_vs_1d = round(avg_1h - avg_1d, 2) if (avg_1h is not None and avg_1d is not None) else None
        delta_1d_vs_1w = round(avg_1d - avg_1w, 2) if (avg_1d is not None and avg_1w is not None) else None

        trend_direction = _classify_trend(delta_1h_vs_1d, threshold=5.0)

        return {
            "domain":           domain,
            "available":        available,
            "windows":          windows_data,
            "delta_1h_vs_1d":   delta_1h_vs_1d,
            "delta_1d_vs_1w":   delta_1d_vs_1w,
            "trend_direction":  trend_direction,
            "analyzed_at":      datetime.now(timezone.utc).isoformat(),
        }

    # ── Coherence distribution ────────────────────────────────────────────────

    def coherence_distribution(
        self,
        *,
        domain: Optional[str] = None,
        window: str = "1d",
    ) -> Dict[str, Any]:
        """
        Coherence score distribution (internal signal agreement, 0-100).

        Bands:
            HIGH    : coherence_score >= 70  (strong signal agreement)
            MEDIUM  : 40 <= coherence_score < 70
            LOW     : coherence_score < 40   (weak/fragmented signal)

        Returns
        ───────
        {
            "window":         str,
            "domain":         str | None,
            "available":      bool,
            "total_with_coh": int,
            "avg":  float | None,
            "min":  float | None,
            "max":  float | None,
            "p50":  float | None,
            "p90":  float | None,
            "high_count":   int,  "high_rate":   float,
            "medium_count": int,  "medium_rate": float,
            "low_count":    int,  "low_rate":    float,
        }
        """
        try:
            return self._query_coherence_distribution(domain=domain, window=window)
        except Exception as exc:
            logger.warning("[CIE] coherence_distribution unavailable: %s", exc)
            return _empty_coherence_distribution(window, domain)

    # ── Black Swan trend ──────────────────────────────────────────────────────

    def bs_trend(
        self,
        *,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Black Swan frequency trend across all time windows.

        Returns
        ───────
        {
            "domain":    str | None,
            "available": bool,
            "windows": {
                "1h": { total, none_rate, low_rate, high_rate, unknown_count },
                "1d": { ... },
                "1w": { ... },
            },
            "delta_high_1h_vs_1d": float | None,   # positive = BS_HIGH rising
            "trend_direction":     "RISING" | "FALLING" | "STABLE" | "UNKNOWN",
            "analyzed_at": str,
        }
        """
        windows_data: Dict[str, Dict[str, Any]] = {}
        available = True

        for w in _WINDOWS:
            try:
                bs = self._svc.query_black_swan_frequency(domain=domain, window=w)
                windows_data[w] = {
                    "total":         bs.get("total", 0),
                    "none_rate":     bs.get("none_rate", 0.0),
                    "low_rate":      bs.get("low_rate", 0.0),
                    "high_rate":     bs.get("high_rate", 0.0),
                    "high_count":    bs.get("high_count", 0),
                    "unknown_count": bs.get("unknown_count", 0),
                }
            except Exception as exc:
                logger.warning("[CIE] bs_trend window=%s unavailable: %s", w, exc)
                available = False
                windows_data[w] = {
                    "total": 0, "none_rate": 0.0, "low_rate": 0.0,
                    "high_rate": 0.0, "high_count": 0, "unknown_count": 0,
                }

        high_1h = windows_data["1h"].get("high_rate")
        high_1d = windows_data["1d"].get("high_rate")

        delta_high = round(high_1h - high_1d, 4) if (high_1h is not None and high_1d is not None) else None
        trend_direction = _classify_trend(delta_high, threshold=0.03)

        return {
            "domain":               domain,
            "available":            available,
            "windows":              windows_data,
            "delta_high_1h_vs_1d":  delta_high,
            "trend_direction":      trend_direction,
            "analyzed_at":          datetime.now(timezone.utc).isoformat(),
        }

    # ── Anomaly detection ─────────────────────────────────────────────────────

    def detect_anomalies(
        self,
        *,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Multi-signal anomaly detection comparing 1h (current) vs 1d (baseline).

        Detects:
        ────────
        BLOCK_RATE_DROP   : coherence gate block_rate drops >= 15pp in 1h vs 1d
                            (could indicate filter weakening or data quality issue)
        HOLD_SPIKE        : hold rate across all gates spikes >= 10pp in 1h vs 1d
                            (decision paralysis signal)
        DCI_SURGE         : avg DCI rises >= 10pts in 1h vs 1d
                            (sudden increase in decision contradiction)
        COHERENCE_DRIFT   : avg coherence_score drifts >= 10pts in 1h vs 1d
                            (positive or negative — both are anomalous)
        BS_HIGH_SURGE     : BS_HIGH frequency rises >= 5pp in 1h vs 1d
        ESCALATION_SURGE  : escalation_rate rises >= 5pp in 1h vs 1d

        Returns
        ───────
        {
            "domain":           str | None,
            "available":        bool,
            "anomalies":        [ { anomaly_type, severity, description, ... } ],
            "summary":          { total, critical, high, medium, low },
            "overall_severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NONE",
            "analyzed_at":      str,
        }
        """
        ts = datetime.now(timezone.utc).isoformat()
        anomalies: List[CalibrationAnomaly] = []

        try:
            # 1h current data
            gate_1h = self._svc.query_all_gate_stats(domain=domain, window="1h")
            dci_1h  = self._svc.query_dci_distribution(domain=domain, window="1h")
            bs_1h   = self._svc.query_black_swan_frequency(domain=domain, window="1h")
            esc_1h  = self._svc.query_escalation_events(domain=domain, window="1h")
            coh_1h  = self._query_coherence_distribution(domain=domain, window="1h")

            # 1d baseline data
            gate_1d = self._svc.query_all_gate_stats(domain=domain, window="1d")
            dci_1d  = self._svc.query_dci_distribution(domain=domain, window="1d")
            bs_1d   = self._svc.query_black_swan_frequency(domain=domain, window="1d")
            esc_1d  = self._svc.query_escalation_events(domain=domain, window="1d")
            coh_1d  = self._query_coherence_distribution(domain=domain, window="1d")

        except Exception as exc:
            logger.warning("[CIE] detect_anomalies: data unavailable (domain=%s): %s", domain, exc)
            return _empty_anomaly_result(domain)

        # ── 1. BLOCK_RATE_DROP — coherence gate as the most sensitive indicator ─
        coh_block_1h = gate_1h.get("coherence", {}).get("block_rate", 0.0)
        coh_block_1d = gate_1d.get("coherence", {}).get("block_rate", 0.0)
        drop = coh_block_1d - coh_block_1h   # positive = rate fell
        if drop >= BLOCK_RATE_DROP_THRESHOLD:
            anomalies.append(CalibrationAnomaly(
                anomaly_type    = "BLOCK_RATE_DROP",
                severity        = _severity_from_deviation(drop, BLOCK_RATE_DROP_THRESHOLD),
                domain          = domain,
                description     = (
                    f"Coherence gate block rate dropped {drop:.1%} "
                    f"(1h={coh_block_1h:.1%} vs 1d baseline={coh_block_1d:.1%}). "
                    "May indicate filter weakening or data quality degradation."
                ),
                current_value   = coh_block_1h,
                baseline_value  = coh_block_1d,
                deviation       = drop,
                threshold       = BLOCK_RATE_DROP_THRESHOLD,
                window_current  = "1h",
                window_baseline = "1d",
                detected_at     = ts,
            ))

        # ── 2. HOLD_SPIKE — aggregate hold rate across all eligible gates ───────
        hold_1h_avg = _avg_hold_rate(gate_1h)
        hold_1d_avg = _avg_hold_rate(gate_1d)
        hold_delta = hold_1h_avg - hold_1d_avg
        if hold_delta >= HOLD_SPIKE_THRESHOLD:
            anomalies.append(CalibrationAnomaly(
                anomaly_type    = "HOLD_SPIKE",
                severity        = _severity_from_deviation(hold_delta, HOLD_SPIKE_THRESHOLD),
                domain          = domain,
                description     = (
                    f"Average HOLD rate across gates spiked +{hold_delta:.1%} "
                    f"(1h avg={hold_1h_avg:.1%} vs 1d baseline={hold_1d_avg:.1%}). "
                    "Possible decision paralysis or manual review queue saturation."
                ),
                current_value   = hold_1h_avg,
                baseline_value  = hold_1d_avg,
                deviation       = hold_delta,
                threshold       = HOLD_SPIKE_THRESHOLD,
                window_current  = "1h",
                window_baseline = "1d",
                detected_at     = ts,
            ))

        # ── 3. DCI_SURGE — average DCI rising ────────────────────────────────────
        avg_dci_1h = dci_1h.get("avg")
        avg_dci_1d = dci_1d.get("avg")
        if avg_dci_1h is not None and avg_dci_1d is not None:
            dci_delta = avg_dci_1h - avg_dci_1d
            if dci_delta >= DCI_SURGE_THRESHOLD:
                anomalies.append(CalibrationAnomaly(
                    anomaly_type    = "DCI_SURGE",
                    severity        = _severity_from_deviation(dci_delta, DCI_SURGE_THRESHOLD),
                    domain          = domain,
                    description     = (
                        f"Average DCI surged +{dci_delta:.1f}pts "
                        f"(1h avg={avg_dci_1h:.1f} vs 1d baseline={avg_dci_1d:.1f}). "
                        "Increasing decision contradiction in the last hour."
                    ),
                    current_value   = avg_dci_1h,
                    baseline_value  = avg_dci_1d,
                    deviation       = dci_delta,
                    threshold       = DCI_SURGE_THRESHOLD,
                    window_current  = "1h",
                    window_baseline = "1d",
                    detected_at     = ts,
                ))

        # ── 4. COHERENCE_DRIFT — absolute drift in coherence score ───────────────
        avg_coh_1h = coh_1h.get("avg")
        avg_coh_1d = coh_1d.get("avg")
        if avg_coh_1h is not None and avg_coh_1d is not None:
            coh_abs_delta = abs(avg_coh_1h - avg_coh_1d)
            if coh_abs_delta >= COHERENCE_DRIFT_THRESHOLD:
                direction = "dropped" if avg_coh_1h < avg_coh_1d else "spiked"
                anomalies.append(CalibrationAnomaly(
                    anomaly_type    = "COHERENCE_DRIFT",
                    severity        = _severity_from_deviation(coh_abs_delta, COHERENCE_DRIFT_THRESHOLD),
                    domain          = domain,
                    description     = (
                        f"Average coherence score {direction} {coh_abs_delta:.1f}pts "
                        f"(1h avg={avg_coh_1h:.1f} vs 1d baseline={avg_coh_1d:.1f}). "
                        "Internal signal agreement is drifting."
                    ),
                    current_value   = avg_coh_1h,
                    baseline_value  = avg_coh_1d,
                    deviation       = coh_abs_delta,
                    threshold       = COHERENCE_DRIFT_THRESHOLD,
                    window_current  = "1h",
                    window_baseline = "1d",
                    detected_at     = ts,
                ))

        # ── 5. BS_HIGH_SURGE ─────────────────────────────────────────────────────
        bs_high_1h = bs_1h.get("high_rate", 0.0)
        bs_high_1d = bs_1d.get("high_rate", 0.0)
        bs_delta = bs_high_1h - bs_high_1d
        if bs_delta >= BS_HIGH_SURGE_THRESHOLD:
            anomalies.append(CalibrationAnomaly(
                anomaly_type    = "BS_HIGH_SURGE",
                severity        = _severity_from_deviation(bs_delta, BS_HIGH_SURGE_THRESHOLD),
                domain          = domain,
                description     = (
                    f"Black Swan HIGH frequency surged +{bs_delta:.1%} "
                    f"(1h={bs_high_1h:.1%} vs 1d baseline={bs_high_1d:.1%}). "
                    "Elevated systemic risk signal in current hour."
                ),
                current_value   = bs_high_1h,
                baseline_value  = bs_high_1d,
                deviation       = bs_delta,
                threshold       = BS_HIGH_SURGE_THRESHOLD,
                window_current  = "1h",
                window_baseline = "1d",
                detected_at     = ts,
            ))

        # ── 6. ESCALATION_SURGE ──────────────────────────────────────────────────
        esc_rate_1h = esc_1h.get("escalation_rate", 0.0)
        esc_rate_1d = esc_1d.get("escalation_rate", 0.0)
        esc_delta = esc_rate_1h - esc_rate_1d
        if esc_delta >= ESCALATION_SURGE_THRESHOLD:
            anomalies.append(CalibrationAnomaly(
                anomaly_type    = "ESCALATION_SURGE",
                severity        = _severity_from_deviation(esc_delta, ESCALATION_SURGE_THRESHOLD),
                domain          = domain,
                description     = (
                    f"ADR-119 escalation rate surged +{esc_delta:.1%} "
                    f"(1h={esc_rate_1h:.1%} vs 1d baseline={esc_rate_1d:.1%}). "
                    "High BS_HIGH_COHERENCE_ESCALATION events in current hour."
                ),
                current_value   = esc_rate_1h,
                baseline_value  = esc_rate_1d,
                deviation       = esc_delta,
                threshold       = ESCALATION_SURGE_THRESHOLD,
                window_current  = "1h",
                window_baseline = "1d",
                detected_at     = ts,
            ))

        # ── Upgrade severity if multiple anomalies ───────────────────────────────
        anomaly_dicts = [a.to_dict() for a in anomalies]
        if len(anomalies) >= 3:
            for a in anomaly_dicts:
                if a["severity"] in ("MEDIUM", "HIGH"):
                    a["severity"] = _upgrade_severity(a["severity"])

        summary = _build_summary(anomaly_dicts)
        overall = _overall_severity(summary, len(anomalies))

        return {
            "domain":           domain,
            "available":        True,
            "anomalies":        anomaly_dicts,
            "summary":          summary,
            "overall_severity": overall,
            "analyzed_at":      ts,
        }

    # ── Per-domain comparison ─────────────────────────────────────────────────

    def domain_comparison(
        self,
        domains: List[str],
        *,
        window: str = "1d",
    ) -> Dict[str, Any]:
        """
        Compare key calibration metrics across multiple domains side-by-side.

        Returns
        ───────
        {
            "window":   str,
            "domains":  {
                domain_name: {
                    "available":    bool,
                    "total":        int,
                    "pass_rate":    float,   # across all gates (avg)
                    "block_rate":   float,
                    "hold_rate":    float,
                    "avg_dci":      float | None,
                    "bs_high_rate": float,
                    "escalation_rate": float,
                }
            },
            "generated_at": str,
        }
        """
        result: Dict[str, Any] = {}

        for d in domains:
            try:
                gate_stats = self._svc.query_all_gate_stats(domain=d, window=window)
                dci        = self._svc.query_dci_distribution(domain=d, window=window)
                bs         = self._svc.query_black_swan_frequency(domain=d, window=window)
                esc        = self._svc.query_escalation_events(domain=d, window=window)

                result[d] = {
                    "available":        True,
                    "total":            next(iter(gate_stats.values()), {}).get("total", 0),
                    "pass_rate":        _avg_pass_rate(gate_stats),
                    "block_rate":       _avg_block_rate(gate_stats),
                    "hold_rate":        _avg_hold_rate(gate_stats),
                    "avg_dci":          dci.get("avg"),
                    "bs_high_rate":     bs.get("high_rate", 0.0),
                    "escalation_rate":  esc.get("escalation_rate", 0.0),
                }
            except Exception as exc:
                logger.warning("[CIE] domain_comparison failed for domain=%s: %s", d, exc)
                result[d] = {
                    "available":       False,
                    "total":           0,
                    "pass_rate":       0.0,
                    "block_rate":      0.0,
                    "hold_rate":       0.0,
                    "avg_dci":         None,
                    "bs_high_rate":    0.0,
                    "escalation_rate": 0.0,
                }

        return {
            "window":       window,
            "domains":      result,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── Full report ───────────────────────────────────────────────────────────

    def full_report(
        self,
        *,
        domain: Optional[str] = None,
        window: str = "1d",
    ) -> Dict[str, Any]:
        """
        Complete calibration insight report for a domain and window.

        Combines snapshot, DCI trend, coherence distribution, BS trend,
        and anomaly detection in a single structured output.

        Returns
        ───────
        {
            "domain":    str | None,
            "window":    str,
            "available": bool,
            "snapshot":  { ... },
            "dci_trend": { ... },
            "coherence": { ... },
            "bs_trend":  { ... },
            "anomalies": { ... },
            "generated_at": str,
        }
        """
        snap     = self.snapshot(domain=domain, window=window)
        dci      = self.dci_trend(domain=domain)
        coh      = self.coherence_distribution(domain=domain, window=window)
        bs       = self.bs_trend(domain=domain)
        anomalies = self.detect_anomalies(domain=domain)

        overall_available = (
            snap.get("available", False)
            or dci.get("available", False)
            or coh.get("available", False)
        )

        return {
            "domain":       domain,
            "window":       window,
            "available":    overall_available,
            "snapshot":     snap,
            "dci_trend":    dci,
            "coherence":    coh,
            "bs_trend":     bs,
            "anomalies":    anomalies,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── Internal query helpers ────────────────────────────────────────────────

    def _query_coherence_distribution(
        self,
        *,
        domain: Optional[str] = None,
        window: str = "1d",
    ) -> Dict[str, Any]:
        """
        Direct SQL query for coherence_score distribution.
        Not exposed on FilterCalibrationMetricsService — owned by InsightEngine.
        """
        from omnix_core.governance.filter_calibration_metrics import (
            _get_db_conn,
            _window_clause,
            _TABLE,
        )

        db_url = self._svc.db_url
        if not db_url:
            raise RuntimeError("[CIE] No DB URL configured")

        domain_filter = "AND domain = %s" if domain else ""
        params = (domain,) if domain else ()

        sql = f"""
            SELECT
                COUNT(coherence_score)                                           AS total_with_coh,
                AVG(coherence_score)                                             AS avg_coh,
                MIN(coherence_score)                                             AS min_coh,
                MAX(coherence_score)                                             AS max_coh,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY coherence_score)    AS p50,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY coherence_score)    AS p90,
                COUNT(*) FILTER (WHERE coherence_score >= {COH_HIGH_THRESHOLD})   AS high_count,
                COUNT(*) FILTER (WHERE coherence_score >= {COH_MEDIUM_THRESHOLD}
                                    AND coherence_score <  {COH_HIGH_THRESHOLD})  AS medium_count,
                COUNT(*) FILTER (WHERE coherence_score <  {COH_MEDIUM_THRESHOLD}) AS low_count
            FROM {_TABLE}
            WHERE {_window_clause(window)} {domain_filter}
              AND coherence_score IS NOT NULL
        """

        conn = _get_db_conn(db_url)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            cur.close()
        finally:
            try:
                conn.close()
            except Exception:
                pass

        if row is None:
            return _empty_coherence_distribution(window, domain)

        total    = int(row[0] or 0)
        high_c   = int(row[6] or 0)
        medium_c = int(row[7] or 0)
        low_c    = int(row[8] or 0)

        def rate(n: int) -> float:
            return round(n / total, 4) if total > 0 else 0.0

        return {
            "window":         window,
            "domain":         domain,
            "available":      True,
            "total_with_coh": total,
            "avg":  round(float(row[1]), 2) if row[1] is not None else None,
            "min":  round(float(row[2]), 2) if row[2] is not None else None,
            "max":  round(float(row[3]), 2) if row[3] is not None else None,
            "p50":  round(float(row[4]), 2) if row[4] is not None else None,
            "p90":  round(float(row[5]), 2) if row[5] is not None else None,
            "high_count":   high_c,   "high_rate":   rate(high_c),
            "medium_count": medium_c, "medium_rate": rate(medium_c),
            "low_count":    low_c,    "low_rate":    rate(low_c),
        }

    def _query_decision_summary(
        self,
        *,
        domain: Optional[str] = None,
        window: str = "1d",
    ) -> Dict[str, Any]:
        """Aggregate final_decision counts for the given window."""
        from omnix_core.governance.filter_calibration_metrics import (
            _get_db_conn,
            _window_clause,
            _TABLE,
        )

        db_url = self._svc.db_url
        if not db_url:
            raise RuntimeError("[CIE] No DB URL configured")

        domain_filter = "AND domain = %s" if domain else ""
        params = (domain,) if domain else ()

        sql = f"""
            SELECT
                COUNT(*)                                                                AS total,
                COUNT(*) FILTER (WHERE final_decision = 'APPROVED')                    AS approved,
                COUNT(*) FILTER (WHERE final_decision IN ('BLOCKED', 'BLOCK'))          AS blocked,
                COUNT(*) FILTER (WHERE final_decision = 'HOLD')                         AS hold
            FROM {_TABLE}
            WHERE {_window_clause(window)} {domain_filter}
        """

        conn = _get_db_conn(db_url)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            cur.close()
        finally:
            try:
                conn.close()
            except Exception:
                pass

        if row is None:
            return {"total": 0, "APPROVED": 0, "BLOCKED": 0, "HOLD": 0}

        total    = int(row[0] or 0)
        approved = int(row[1] or 0)
        blocked  = int(row[2] or 0)
        hold     = int(row[3] or 0)

        def rate(n: int) -> float:
            return round(n / total, 4) if total > 0 else 0.0

        return {
            "total":          total,
            "APPROVED":       approved, "approved_rate": rate(approved),
            "BLOCKED":        blocked,  "blocked_rate":  rate(blocked),
            "HOLD":           hold,     "hold_rate":     rate(hold),
        }


# ── Module-level convenience function ────────────────────────────────────────

def get_insight_engine(service=None) -> CalibrationInsightEngine:
    """
    Convenience factory — returns a CalibrationInsightEngine.

    Pulls FilterCalibrationMetricsService from the global instance
    (filter_calibration_metrics.get_global_service) if no service is provided.
    """
    if service is not None:
        return CalibrationInsightEngine(service)
    try:
        from omnix_core.governance.filter_calibration_metrics import get_global_service
        return CalibrationInsightEngine(get_global_service())
    except Exception:
        return CalibrationInsightEngine()


# ── Internal calculation helpers ──────────────────────────────────────────────

def _avg_hold_rate(gate_stats: Dict[str, Dict[str, Any]]) -> float:
    """Average hold_rate across all gates that have eligible > 0."""
    rates = [
        v.get("hold_rate", 0.0)
        for v in gate_stats.values()
        if v.get("eligible", 0) > 0
    ]
    return round(sum(rates) / len(rates), 4) if rates else 0.0


def _avg_pass_rate(gate_stats: Dict[str, Dict[str, Any]]) -> float:
    rates = [
        v.get("pass_rate", 0.0)
        for v in gate_stats.values()
        if v.get("eligible", 0) > 0
    ]
    return round(sum(rates) / len(rates), 4) if rates else 0.0


def _avg_block_rate(gate_stats: Dict[str, Dict[str, Any]]) -> float:
    rates = [
        v.get("block_rate", 0.0)
        for v in gate_stats.values()
        if v.get("eligible", 0) > 0
    ]
    return round(sum(rates) / len(rates), 4) if rates else 0.0


def _classify_trend(delta: Optional[float], threshold: float) -> str:
    """Classify trend direction from a delta value."""
    if delta is None:
        return "UNKNOWN"
    if delta >= threshold:
        return "RISING"
    if delta <= -threshold:
        return "FALLING"
    return "STABLE"


def _upgrade_severity(current: str) -> str:
    """Bump severity one level upward due to co-occurrence."""
    if current == "MEDIUM":
        return "HIGH"
    if current == "HIGH":
        return "CRITICAL"
    return current


def _build_summary(anomaly_dicts: List[Dict[str, Any]]) -> Dict[str, int]:
    summary = {"total": len(anomaly_dicts), "critical": 0, "high": 0, "medium": 0, "low": 0}
    for a in anomaly_dicts:
        sev = a.get("severity", "MEDIUM").lower()
        if sev in summary:
            summary[sev] += 1
    return summary


def _overall_severity(summary: Dict[str, int], total_anomalies: int) -> str:
    if summary.get("critical", 0) > 0:
        return "CRITICAL"
    if summary.get("high", 0) > 0:
        return "HIGH"
    if summary.get("medium", 0) > 0:
        return "MEDIUM"
    if summary.get("low", 0) > 0:
        return "LOW"
    if total_anomalies > 0:
        return "MEDIUM"
    return "NONE"
