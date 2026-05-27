"""
ADR-134 — Governance Oscillation & Hesitation Asymmetry Engine

Detects pre-capture governance degradation through four complementary
longitudinal analysis methods operating on the permanent decision record.

Architecture Position
─────────────────────
CalibrationInsightEngine (ADR-128) detects snapshot anomalies — single-window
deviations from baseline. This engine detects TEMPORAL PATTERNS across windows:
cycling behaviour, phase transitions, latency asymmetry, and amplitude dampening.

Design Principle (from conversation with Dr.(H.C.) Amanulla Khan, 2026-04-28):
"Oscillation itself becomes a transition signature — the system still detects
mismatch strongly enough to resist full normalization, but no longer possesses a
stable evaluative frame capable of resolving the tension coherently."

Four Analysis Methods
──────────────────────

1. oscillation_profile()
   HOLD rate across N rolling weekly windows.
   Computes std-dev, amplitude, pattern classification.
   Pattern: CYCLING | SETTLING | DRIFTING | STABLE | INSUFFICIENT_DATA

2. phase_segmented_analysis()
   Detects regime-change weeks (HOLD rate shift > PHASE_BOUNDARY_THRESHOLD).
   Splits the series into pre/post-boundary segments.
   Computes independent hold_rate averages for each segment.
   Prevents continuity-based regressions from masking phase transitions.

3. hesitation_asymmetry()
   Compares avg/p50/p90 processing_time_ms by decision type:
     HOLD vs BLOCK vs APPROVED
   during baseline and high-oscillation periods.
   If HOLD decisions process faster than BLOCK during oscillation,
   the evaluative frame is defaulting to deferral under load.
   Asymmetry coefficient = avg_HOLD_ms / avg_BLOCK_ms (< 1.0 = asymmetry present).

4. dampening_curve()
   Compares oscillation amplitude in the first half of the observed period
   vs the second half.
   DAMPENING  → amplitude falling  → pre-capture signal (residual recognition eroding)
   AMPLIFYING → amplitude rising   → escalating evaluative conflict
   STABLE     → no directional trend

All methods are read-only, DB-backed, fail-safe (return available=False on error).
Zero impact on the live governance pipeline.

Usage
─────
    from omnix_core.governance.oscillation_insight import OscillationInsightEngine
    engine = OscillationInsightEngine()

    profile   = engine.oscillation_profile(domain="trading")
    phases    = engine.phase_segmented_analysis(domain="trading")
    asymmetry = engine.hesitation_asymmetry(domain="trading")
    dampening = engine.dampening_curve(domain="trading")
    report    = engine.oscillation_report(domain="trading")

ADR references
──────────────
    ADR-127 — filter_calibration_events table (source of all metrics)
    ADR-128 — CalibrationInsightEngine (snapshot anomaly detection)
    ADR-129 — AnomalyResponseEngine (recommendation layer)
    ADR-134 — This module (temporal / oscillation analysis)
"""

import logging
import math
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Tuple

logger = logging.getLogger("OMNIX.OscillationInsight")

# ── Thresholds ────────────────────────────────────────────────────────────────

OSCILLATION_STD_THRESHOLD:   float = 0.08   # 8pp std-dev → CYCLING
PHASE_BOUNDARY_THRESHOLD:    float = 0.20   # 20pp week-over-week shift → phase boundary
HIGH_OSCILLATION_STD:        float = 0.10   # 10pp → "high-oscillation" period for latency
DAMPENING_AMPLITUDE_DELTA:   float = 0.04   # 4pp amplitude drop → DAMPENING signal
MIN_WINDOWS_FOR_OSCILLATION: int   = 4      # need ≥4 weekly windows for reliable pattern
MIN_DECISIONS_PER_WINDOW:    int   = 10     # skip windows with too few decisions
LATENCY_ASYMMETRY_THRESHOLD: float = 0.85   # HOLD/BLOCK ratio < 0.85 → asymmetry present

_TABLE = "filter_calibration_events"


# ── Connection pool ───────────────────────────────────────────────────────────
#
# One ThreadedConnectionPool shared across all OscillationInsightEngine instances
# and all threads spawned by ThreadPoolExecutor.
#
# Pool sizing:
#   minconn = 1  — keep one warm connection at idle
#   maxconn = 5  — 4 parallel workers + 1 buffer for sequential callers
#
# This prevents opening a new TCP connection for every DB call, which was the
# primary source of the ~800ms latency on each method invocation.

_pool      = None           # psycopg2.pool.ThreadedConnectionPool | None
_pool_lock = threading.Lock()
_pool_url  = None           # DB URL the pool was created with


def _get_pool(db_url: Optional[str] = None):
    """Return the module-level ThreadedConnectionPool, creating it if needed."""
    global _pool, _pool_url
    url = db_url or os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("No database URL configured (OMNIX_DB_URL / DATABASE_URL)")
    with _pool_lock:
        if _pool is None or _pool_url != url:
            import psycopg.pool as pgpool
            logger.info("[OIE] Initialising ThreadedConnectionPool (minconn=1 maxconn=5)")
            _pool     = pgpool.ThreadedConnectionPool(1, 5, url)
            _pool_url = url
    return _pool


@contextmanager
def _db_conn(db_url: Optional[str] = None) -> Iterator:
    """Context manager — borrow a connection from the pool and return it on exit."""
    pool = _get_pool(db_url)
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class WeeklyHoldWindow:
    """HOLD rate measurement for a single rolling 7-day window."""
    week_offset:  int    # 0 = most recent, 1 = previous week, etc.
    week_start:   str    # ISO timestamp — start of this window
    week_end:     str    # ISO timestamp — end of this window
    total:        int
    hold_count:   int
    hold_rate:    float  # 0.0–1.0
    block_rate:   float
    approved_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "week_offset":   self.week_offset,
            "week_start":    self.week_start,
            "week_end":      self.week_end,
            "total":         self.total,
            "hold_count":    self.hold_count,
            "hold_rate":     round(self.hold_rate, 4),
            "block_rate":    round(self.block_rate, 4),
            "approved_rate": round(self.approved_rate, 4),
        }


@dataclass
class PhaseSegment:
    """A continuous sub-series separated by a detected regime-change boundary."""
    segment_id:    int       # 0, 1, 2, …
    phase:         str       # "PRE_BOUNDARY" | "POST_BOUNDARY" | "BASELINE"
    start_offset:  int       # week_offset of first window in this segment
    end_offset:    int       # week_offset of last window in this segment
    window_count:  int
    avg_hold_rate: float
    avg_block_rate: float
    hold_rate_slope: Optional[float]  # pp per week (positive = rising)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id":    self.segment_id,
            "phase":         self.phase,
            "start_offset":  self.start_offset,
            "end_offset":    self.end_offset,
            "window_count":  self.window_count,
            "avg_hold_rate": round(self.avg_hold_rate, 4),
            "avg_block_rate": round(self.avg_block_rate, 4),
            "hold_rate_slope_pp_per_week": (
                round(self.hold_rate_slope, 4) if self.hold_rate_slope is not None else None
            ),
        }


# ── Main engine ───────────────────────────────────────────────────────────────

class OscillationInsightEngine:
    """
    Temporal governance degradation detector — ADR-134.

    Reads from filter_calibration_events (ADR-127).
    All methods are read-only, fail-safe, and thread-safe.
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = (
            db_url
            or os.environ.get("OMNIX_DB_URL")
            or os.environ.get("DATABASE_URL")
        )

    # ── 1. Oscillation Profile ────────────────────────────────────────────────

    def oscillation_profile(
        self,
        *,
        domain: Optional[str] = None,
        num_weeks: int = 8,
    ) -> Dict[str, Any]:
        """
        HOLD rate across N rolling weekly windows.

        Computes std-dev, amplitude, and classifies the oscillation pattern.

        Pattern Classification
        ──────────────────────
        CYCLING            — Non-monotonic series with std-dev ≥ OSCILLATION_STD_THRESHOLD.
                             The evaluative frame is alternating without settling.
                             Residual recognition capacity still present.
        DRIFTING           — Every week strictly higher than the previous (d > 0 for all diffs).
                             Slow accumulation toward deferral equilibrium.
                             Note: detected BEFORE std-dev check — a clean monotonic rise
                             with wide range is DRIFTING, not CYCLING.
        SETTLING           — Every week strictly lower than the previous (d < 0 for all diffs).
                             HOLD rate falling — resolving toward enforcement or capture.
                             Cross-reference dampening_curve() to distinguish healthy vs captured.
        STABLE             — Neither monotonic nor high-variance. No directional signal.
        INSUFFICIENT_DATA  — fewer than MIN_WINDOWS_FOR_OSCILLATION valid windows.

        Classification priority: DRIFTING/SETTLING (strict monotonic) > CYCLING (std-dev) > STABLE.
        A non-monotonic series where last < first but with direction changes is NOT SETTLING —
        it is CYCLING (if high variance) or STABLE (if low variance).

        Returns
        ───────
        {
          "domain":         str | None,
          "available":      bool,
          "num_weeks":      int,
          "windows":        [ WeeklyHoldWindow.to_dict(), … ],  (oldest first)
          "statistics": {
            "avg_hold_rate":  float,
            "std_dev":        float,
            "min_hold_rate":  float,
            "max_hold_rate":  float,
            "amplitude":      float,   # max - min
            "valid_windows":  int,
          },
          "pattern":        str,       # CYCLING | SETTLING | DRIFTING | STABLE | INSUFFICIENT_DATA
          "pattern_note":   str,       # human-readable explanation
          "analyzed_at":    str,
        }
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            windows = self._fetch_weekly_windows(domain=domain, num_weeks=num_weeks)
        except Exception as exc:
            logger.error("[OIE] oscillation_profile DB error (domain=%s): %s", domain, exc)
            return {"domain": domain, "available": False, "analyzed_at": now_iso}

        valid = [w for w in windows if w.total >= MIN_DECISIONS_PER_WINDOW]

        stats = self._compute_hold_statistics(valid)
        pattern, note = self._classify_oscillation_pattern(valid, stats)

        return {
            "domain":      domain,
            "available":   True,
            "num_weeks":   num_weeks,
            "windows":     [w.to_dict() for w in reversed(windows)],  # oldest first
            "statistics":  stats,
            "pattern":     pattern,
            "pattern_note": note,
            "analyzed_at": now_iso,
        }

    # ── 2. Phase-Segmented Analysis ───────────────────────────────────────────

    def phase_segmented_analysis(
        self,
        *,
        domain: Optional[str] = None,
        num_weeks: int = 12,
        boundary_threshold: float = PHASE_BOUNDARY_THRESHOLD,
    ) -> Dict[str, Any]:
        """
        Detect regime-change weeks and split the series into independent segments.

        A phase boundary is detected when the week-over-week HOLD rate shift
        exceeds `boundary_threshold` (default 20pp). Boundaries are treated as
        distinct governance phase transitions, not noise.

        This prevents continuity-based regressions from dampening phase-transition
        signals by averaging pre- and post-boundary observations together.

        Returns
        ───────
        {
          "domain":             str | None,
          "available":          bool,
          "boundaries_detected": int,
          "boundary_weeks":     [ { week_offset, shift_pp } ],
          "segments":           [ PhaseSegment.to_dict(), … ],
          "continuity_warning": bool,   # True if ≥1 boundary detected (continuity analysis invalid)
          "analyzed_at":        str,
        }
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            windows = self._fetch_weekly_windows(domain=domain, num_weeks=num_weeks)
        except Exception as exc:
            logger.error("[OIE] phase_segmented DB error (domain=%s): %s", domain, exc)
            return {"domain": domain, "available": False, "analyzed_at": now_iso}

        valid = [w for w in windows if w.total >= MIN_DECISIONS_PER_WINDOW]
        if len(valid) < 2:
            return {
                "domain":              domain,
                "available":           True,
                "boundaries_detected": 0,
                "boundary_weeks":      [],
                "segments":            [],
                "continuity_warning":  False,
                "note":                "Insufficient data for phase segmentation.",
                "analyzed_at":         now_iso,
            }

        # Detect boundaries (week_offset order — most recent first)
        boundary_weeks = []
        for i in range(1, len(valid)):
            shift = abs(valid[i].hold_rate - valid[i - 1].hold_rate)
            if shift >= boundary_threshold:
                boundary_weeks.append({
                    "week_offset":    valid[i].week_offset,
                    "week_start":     valid[i].week_start,
                    "hold_rate_from": round(valid[i - 1].hold_rate, 4),
                    "hold_rate_to":   round(valid[i].hold_rate, 4),
                    "shift_pp":       round(shift, 4),
                })

        # Build segments split at boundaries
        segments = self._build_phase_segments(valid, boundary_weeks)

        return {
            "domain":              domain,
            "available":           True,
            "boundaries_detected": len(boundary_weeks),
            "boundary_weeks":      boundary_weeks,
            "segments":            [s.to_dict() for s in segments],
            "continuity_warning":  len(boundary_weeks) > 0,
            "continuity_note": (
                "One or more phase boundaries detected. "
                "Continuity-based analysis (single regression across all windows) "
                "may mask transition dynamics. Use per-segment slopes instead."
                if boundary_weeks else
                "No phase boundaries detected. Continuity analysis is valid."
            ),
            "analyzed_at": now_iso,
        }

    # ── 3. Hesitation Asymmetry ───────────────────────────────────────────────

    def hesitation_asymmetry(
        self,
        *,
        domain: Optional[str] = None,
        oscillation_window: str = "7d",
    ) -> Dict[str, Any]:
        """
        Compare processing_time_ms by decision type (APPROVED / BLOCKED / HOLD).

        If HOLD decisions process consistently faster than BLOCK decisions during
        high-oscillation periods, the evaluative frame is defaulting to deferral
        under cognitive/computational load rather than resolving the tension.

        Asymmetry coefficient = avg_HOLD_ms / avg_BLOCK_ms
          < LATENCY_ASYMMETRY_THRESHOLD (0.85) → asymmetry present
          ≥ 1.0                                → HOLD processes slower (resolution-weighted)

        Returns
        ───────
        {
          "domain":         str | None,
          "available":      bool,
          "latency_by_type": {
            "APPROVED": { avg_ms, p50_ms, p90_ms, count },
            "BLOCKED":  { avg_ms, p50_ms, p90_ms, count },
            "HOLD":     { avg_ms, p50_ms, p90_ms, count },
          },
          "asymmetry_coefficient": float | None,  # avg_HOLD / avg_BLOCK
          "asymmetry_detected":    bool,
          "asymmetry_interpretation": str,
          "analyzed_at": str,
        }
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            latency = self._fetch_latency_by_decision_type(
                domain=domain, window=oscillation_window
            )
        except Exception as exc:
            logger.error("[OIE] hesitation_asymmetry DB error (domain=%s): %s", domain, exc)
            return {"domain": domain, "available": False, "analyzed_at": now_iso}

        hold_avg  = latency.get("HOLD", {}).get("avg_ms")
        block_avg = latency.get("BLOCKED", {}).get("avg_ms")

        coeff = None
        asymmetry_detected = False
        interpretation = "Insufficient data to compute asymmetry coefficient."

        if hold_avg is not None and block_avg is not None and block_avg > 0:
            coeff = round(hold_avg / block_avg, 4)
            asymmetry_detected = coeff < LATENCY_ASYMMETRY_THRESHOLD
            if asymmetry_detected:
                interpretation = (
                    f"HOLD decisions process {round((1 - coeff) * 100, 1)}% faster than BLOCK "
                    f"decisions (coefficient={coeff}). The evaluative frame is defaulting to "
                    "deferral under load rather than resolving the tension. "
                    "This is consistent with ADR-134 hesitation asymmetry — a pre-capture signal."
                )
            elif coeff >= 1.0:
                interpretation = (
                    f"HOLD decisions process slower than or equal to BLOCK decisions "
                    f"(coefficient={coeff}). No deferral shortcut detected. "
                    "Evaluative frame appears to invest effort proportionally."
                )
            else:
                interpretation = (
                    f"Asymmetry coefficient={coeff} — below detection threshold "
                    f"({LATENCY_ASYMMETRY_THRESHOLD}). Marginal deferral preference, "
                    "not yet significant."
                )

        return {
            "domain":                   domain,
            "available":                True,
            "window":                   oscillation_window,
            "latency_by_type":          latency,
            "asymmetry_coefficient":    coeff,
            "asymmetry_detected":       asymmetry_detected,
            "asymmetry_threshold":      LATENCY_ASYMMETRY_THRESHOLD,
            "asymmetry_interpretation": interpretation,
            "analyzed_at":              now_iso,
        }

    # ── 4. Dampening Curve ────────────────────────────────────────────────────

    def dampening_curve(
        self,
        *,
        domain: Optional[str] = None,
        num_weeks: int = 8,
    ) -> Dict[str, Any]:
        """
        Measure whether oscillation amplitude is decreasing over time.

        Splits the observed period in half. Compares amplitude (max-min hold_rate)
        in the first half (older) vs the second half (recent).

        DAMPENING  → amplitude falling between halves.
                     The system is losing the capacity to detect mismatch.
                     Pre-capture signal — oscillation → absorbed equilibrium.
        AMPLIFYING → amplitude rising.
                     Evaluative conflict is intensifying, not resolving.
        STABLE     → amplitude unchanged within DAMPENING_AMPLITUDE_DELTA.

        Returns
        ───────
        {
          "domain":       str | None,
          "available":    bool,
          "first_half": {
            "window_count": int,
            "amplitude":    float,
            "avg_hold_rate": float,
          },
          "second_half": {
            "window_count": int,
            "amplitude":    float,
            "avg_hold_rate": float,
          },
          "amplitude_delta":     float,   # second_half - first_half (negative = dampening)
          "curve_direction":     str,     # DAMPENING | AMPLIFYING | STABLE | INSUFFICIENT_DATA
          "curve_interpretation": str,
          "analyzed_at":         str,
        }
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            windows = self._fetch_weekly_windows(domain=domain, num_weeks=num_weeks)
        except Exception as exc:
            logger.error("[OIE] dampening_curve DB error (domain=%s): %s", domain, exc)
            return {"domain": domain, "available": False, "analyzed_at": now_iso}

        valid = [w for w in windows if w.total >= MIN_DECISIONS_PER_WINDOW]

        if len(valid) < MIN_WINDOWS_FOR_OSCILLATION:
            return {
                "domain":          domain,
                "available":       True,
                "curve_direction": "INSUFFICIENT_DATA",
                "curve_interpretation": (
                    f"Need ≥{MIN_WINDOWS_FOR_OSCILLATION} valid windows "
                    f"(found {len(valid)})."
                ),
                "analyzed_at": now_iso,
            }

        mid = len(valid) // 2
        first_half  = valid[mid:]   # older (higher week_offset = further back)
        second_half = valid[:mid]   # more recent

        def _half_stats(half: List[WeeklyHoldWindow]) -> Dict[str, Any]:
            rates = [w.hold_rate for w in half]
            if not rates:
                return {"window_count": 0, "amplitude": 0.0, "avg_hold_rate": 0.0}
            return {
                "window_count":  len(rates),
                "amplitude":     round(max(rates) - min(rates), 4),
                "avg_hold_rate": round(sum(rates) / len(rates), 4),
            }

        first_stats  = _half_stats(first_half)
        second_stats = _half_stats(second_half)

        amp_delta = round(second_stats["amplitude"] - first_stats["amplitude"], 4)

        if abs(amp_delta) < DAMPENING_AMPLITUDE_DELTA:
            direction = "STABLE"
            interp = (
                f"Oscillation amplitude unchanged between periods "
                f"(Δ={amp_delta:+.4f}pp). "
                "Evaluative conflict is holding steady — no directional signal yet."
            )
        elif amp_delta < 0:
            direction = "DAMPENING"
            interp = (
                f"Oscillation amplitude falling (Δ={amp_delta:+.4f}pp). "
                "The evaluative frame is losing capacity to generate mismatch signals. "
                "ADR-134 pre-capture signal: resistance is attenuating. "
                "Monitor for transition toward absorbed equilibrium."
            )
        else:
            direction = "AMPLIFYING"
            interp = (
                f"Oscillation amplitude rising (Δ={amp_delta:+.4f}pp). "
                "Evaluative conflict is intensifying. "
                "The governance frame has not found a stable resolution — "
                "escalation may follow before capture or enforcement stabilisation."
            )

        return {
            "domain":               domain,
            "available":            True,
            "num_weeks":            num_weeks,
            "first_half":           first_stats,
            "second_half":          second_stats,
            "amplitude_delta":      amp_delta,
            "curve_direction":      direction,
            "curve_interpretation": interp,
            "analyzed_at":          now_iso,
        }

    # ── Full Report ───────────────────────────────────────────────────────────

    def oscillation_report(
        self,
        *,
        domain: Optional[str] = None,
        num_weeks: int = 8,
    ) -> Dict[str, Any]:
        """
        Full ADR-134 oscillation report — all four analyses combined.

        Returns a structured dict with:
          - oscillation_profile
          - phase_segmented_analysis
          - hesitation_asymmetry
          - dampening_curve
          - executive_summary (plain-language synthesis)
        """
        # Run all four analyses concurrently — each method manages its own DB
        # connection, so thread-safe parallel execution is safe here.
        tasks = {
            "profile":   lambda: self.oscillation_profile(domain=domain, num_weeks=num_weeks),
            "phases":    lambda: self.phase_segmented_analysis(domain=domain, num_weeks=num_weeks + 4),
            "asymmetry": lambda: self.hesitation_asymmetry(domain=domain),
            "dampening": lambda: self.dampening_curve(domain=domain, num_weeks=num_weeks),
        }
        results: Dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(fn): key for key, fn in tasks.items()}
            for future in as_completed(futures):
                results[futures[future]] = future.result()

        profile   = results["profile"]
        phases    = results["phases"]
        asymmetry = results["asymmetry"]
        dampening = results["dampening"]

        summary = self._build_executive_summary(profile, phases, asymmetry, dampening)

        return {
            "domain":                  domain,
            "adr":                     "ADR-134 — Governance Oscillation & Hesitation Asymmetry",
            "generated_at":            datetime.now(timezone.utc).isoformat(),
            "oscillation_profile":     profile,
            "phase_segmented":         phases,
            "hesitation_asymmetry":    asymmetry,
            "dampening_curve":         dampening,
            "executive_summary":       summary,
        }

    # ── Internal — DB queries ─────────────────────────────────────────────────

    def _fetch_weekly_windows(
        self,
        domain: Optional[str],
        num_weeks: int,
    ) -> List[WeeklyHoldWindow]:
        """
        Fetch HOLD/BLOCK/APPROVED counts for N rolling 7-day windows.
        Returns list ordered most-recent-first (week_offset=0 is current week).
        """
        domain_filter = "AND domain = %s" if domain else ""
        params: list = [num_weeks]
        if domain:
            params.append(domain)

        with _db_conn(self._db_url) as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    week_offset,
                    date_trunc('week', NOW() - (week_offset * INTERVAL '7 days'))
                        AS week_start,
                    date_trunc('week', NOW() - (week_offset * INTERVAL '7 days'))
                        + INTERVAL '7 days'
                        AS week_end,
                    COUNT(*)                                                AS total,
                    SUM(CASE WHEN final_decision = 'HOLD'     THEN 1 ELSE 0 END) AS hold_count,
                    SUM(CASE WHEN final_decision = 'BLOCKED'  THEN 1 ELSE 0 END) AS block_count,
                    SUM(CASE WHEN final_decision IN ('APPROVED','APPROVED_CONDITIONAL')
                             THEN 1 ELSE 0 END)                             AS approved_count
                FROM {_TABLE},
                     generate_series(0, %s - 1) AS week_offset
                WHERE event_ts >= date_trunc('week', NOW() - (week_offset * INTERVAL '7 days'))
                  AND event_ts <  date_trunc('week', NOW() - (week_offset * INTERVAL '7 days'))
                                  + INTERVAL '7 days'
                  {domain_filter}
                GROUP BY week_offset, week_start, week_end
                ORDER BY week_offset ASC
                """,
                params,
            )
            rows = cur.fetchall()

        windows = []
        for row in rows:
            offset, ws, we, total, hold, block, approved = row
            total    = int(total or 0)
            hold     = int(hold or 0)
            block    = int(block or 0)
            approved = int(approved or 0)
            windows.append(WeeklyHoldWindow(
                week_offset   = int(offset),
                week_start    = ws.isoformat() if hasattr(ws, "isoformat") else str(ws),
                week_end      = we.isoformat() if hasattr(we, "isoformat") else str(we),
                total         = total,
                hold_count    = hold,
                hold_rate     = round(hold / total, 4) if total > 0 else 0.0,
                block_rate    = round(block / total, 4) if total > 0 else 0.0,
                approved_rate = round(approved / total, 4) if total > 0 else 0.0,
            ))
        return windows

    def _fetch_latency_by_decision_type(
        self,
        domain: Optional[str],
        window: str,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Return avg/p50/p90 processing_time_ms per decision type for the given window.
        """
        _WINDOW_MAP = {
            "1h":  "1 hour",
            "6h":  "6 hours",
            "1d":  "1 day",
            "7d":  "7 days",
            "30d": "30 days",
        }
        interval = _WINDOW_MAP.get(window, "7 days")
        domain_filter = "AND domain = %s" if domain else ""
        params: list = []
        if domain:
            params.append(domain)

        with _db_conn(self._db_url) as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    final_decision,
                    COUNT(*)                                   AS cnt,
                    AVG(processing_time_ms)                    AS avg_ms,
                    PERCENTILE_CONT(0.5) WITHIN GROUP
                        (ORDER BY processing_time_ms)          AS p50_ms,
                    PERCENTILE_CONT(0.9) WITHIN GROUP
                        (ORDER BY processing_time_ms)          AS p90_ms
                FROM {_TABLE}
                WHERE processing_time_ms IS NOT NULL
                  AND event_ts >= NOW() - INTERVAL '{interval}'
                  {domain_filter}
                GROUP BY final_decision
                """,
                params,
            )
            rows = cur.fetchall()

        result: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            dtype, cnt, avg_ms, p50_ms, p90_ms = row
            canonical = _canonical_decision(str(dtype))
            result[canonical] = {
                "count":  int(cnt or 0),
                "avg_ms": round(float(avg_ms), 1) if avg_ms is not None else None,
                "p50_ms": round(float(p50_ms), 1) if p50_ms is not None else None,
                "p90_ms": round(float(p90_ms), 1) if p90_ms is not None else None,
            }
        return result

    # ── Internal — computation helpers ────────────────────────────────────────

    @staticmethod
    def _compute_hold_statistics(
        valid: List[WeeklyHoldWindow],
    ) -> Dict[str, Any]:
        if not valid:
            return {
                "avg_hold_rate": None, "std_dev": None,
                "min_hold_rate": None, "max_hold_rate": None,
                "amplitude": None, "valid_windows": 0,
            }
        rates = [w.hold_rate for w in valid]
        avg   = sum(rates) / len(rates)
        variance = sum((r - avg) ** 2 for r in rates) / len(rates)
        std   = math.sqrt(variance)
        return {
            "avg_hold_rate":  round(avg, 4),
            "std_dev":        round(std, 4),
            "min_hold_rate":  round(min(rates), 4),
            "max_hold_rate":  round(max(rates), 4),
            "amplitude":      round(max(rates) - min(rates), 4),
            "valid_windows":  len(valid),
        }

    @staticmethod
    def _classify_oscillation_pattern(
        valid: List[WeeklyHoldWindow],
        stats: Dict[str, Any],
    ) -> Tuple[str, str]:
        if stats["valid_windows"] < MIN_WINDOWS_FOR_OSCILLATION:
            return (
                "INSUFFICIENT_DATA",
                f"Need ≥{MIN_WINDOWS_FOR_OSCILLATION} valid windows "
                f"(found {stats['valid_windows']}).",
            )
        std = stats["std_dev"]
        if std is None:
            return "INSUFFICIENT_DATA", "No standard deviation computable."

        rates = [w.hold_rate for w in valid]
        diffs = [rates[i + 1] - rates[i] for i in range(len(rates) - 1)]

        # Strict monotonic trend takes priority over std-dev threshold.
        # A clean rising drift has high variance (wide range) but is NOT cycling —
        # cycling requires alternating direction. Check monotonicity first.
        all_strictly_increasing = all(d > 0 for d in diffs)
        all_strictly_decreasing = all(d < 0 for d in diffs)

        if all_strictly_increasing:
            return (
                "DRIFTING",
                f"std-dev={std:.4f}, strict monotonic HOLD rate increase. "
                "Slow accumulation toward deferral equilibrium. "
                "Evaluate whether the evaluative frame is conditioning toward normalization capture.",
            )
        if all_strictly_decreasing:
            return (
                "SETTLING",
                f"std-dev={std:.4f}, strict monotonic HOLD rate decrease. "
                "Deferral is resolving — either toward enforcement (healthy) or "
                "toward absorbed equilibrium (captured). "
                "Cross-reference with dampening_curve() to distinguish.",
            )

        # Non-monotonic — check std-dev for cycling vs stable
        if std >= OSCILLATION_STD_THRESHOLD:
            return (
                "CYCLING",
                f"std-dev={std:.4f} ≥ threshold {OSCILLATION_STD_THRESHOLD}. "
                "The evaluative frame is cycling between enforcement and deferral "
                "without settling. Residual recognition capacity still present — "
                "the system detects mismatch but cannot resolve it coherently.",
            )

        return (
            "STABLE",
            f"std-dev={std:.4f} < threshold {OSCILLATION_STD_THRESHOLD}. "
            "No significant oscillation or directional trend detected.",
        )

    @staticmethod
    def _build_phase_segments(
        valid: List[WeeklyHoldWindow],
        boundary_weeks: List[Dict[str, Any]],
    ) -> List[PhaseSegment]:
        if not boundary_weeks:
            stats = OscillationInsightEngine._compute_hold_statistics(valid)
            slope = _linear_slope([w.hold_rate for w in valid])
            return [PhaseSegment(
                segment_id    = 0,
                phase         = "BASELINE",
                start_offset  = valid[-1].week_offset if valid else 0,
                end_offset    = valid[0].week_offset if valid else 0,
                window_count  = len(valid),
                avg_hold_rate = stats["avg_hold_rate"] or 0.0,
                avg_block_rate = round(
                    sum(w.block_rate for w in valid) / len(valid), 4
                ) if valid else 0.0,
                hold_rate_slope = slope,
            )]

        boundary_offsets = {b["week_offset"] for b in boundary_weeks}
        segments_raw: List[List[WeeklyHoldWindow]] = []
        current: List[WeeklyHoldWindow] = []
        for w in valid:
            current.append(w)
            if w.week_offset in boundary_offsets:
                segments_raw.append(current)
                current = []
        if current:
            segments_raw.append(current)

        result = []
        phase_labels = ["PRE_BOUNDARY"] + [
            f"POST_BOUNDARY_{i}" for i in range(1, len(segments_raw))
        ]
        for i, seg_windows in enumerate(segments_raw):
            if not seg_windows:
                continue
            hold_rates  = [w.hold_rate for w in seg_windows]
            block_rates = [w.block_rate for w in seg_windows]
            result.append(PhaseSegment(
                segment_id    = i,
                phase         = phase_labels[i] if i < len(phase_labels) else f"SEGMENT_{i}",
                start_offset  = seg_windows[-1].week_offset,
                end_offset    = seg_windows[0].week_offset,
                window_count  = len(seg_windows),
                avg_hold_rate = round(sum(hold_rates) / len(hold_rates), 4),
                avg_block_rate = round(sum(block_rates) / len(block_rates), 4),
                hold_rate_slope = _linear_slope(hold_rates),
            ))
        return result

    @staticmethod
    def _build_executive_summary(
        profile:   Dict[str, Any],
        phases:    Dict[str, Any],
        asymmetry: Dict[str, Any],
        dampening: Dict[str, Any],
    ) -> Dict[str, Any]:
        signals: List[str] = []
        risk_level = "LOW"

        pattern = profile.get("pattern", "UNKNOWN")
        if pattern == "CYCLING":
            signals.append("Oscillation detected — evaluative frame cycling without resolution.")
            risk_level = "MEDIUM"
        elif pattern == "DRIFTING":
            signals.append("Monotonic HOLD rate increase — slow drift toward deferral equilibrium.")
            risk_level = "MEDIUM"

        if phases.get("boundaries_detected", 0) > 0:
            n = phases["boundaries_detected"]
            signals.append(
                f"{n} phase boundary{'ies' if n > 1 else ''} detected — "
                "continuity-based analysis is invalid across these transitions."
            )
            if risk_level == "LOW":
                risk_level = "MEDIUM"

        if asymmetry.get("asymmetry_detected"):
            coeff = asymmetry.get("asymmetry_coefficient")
            signals.append(
                f"Hesitation asymmetry present (coefficient={coeff}) — "
                "evaluative frame defaulting to deferral under load."
            )
            risk_level = "HIGH" if risk_level != "CRITICAL" else "CRITICAL"

        curve = dampening.get("curve_direction", "UNKNOWN")
        asymmetry_active = asymmetry.get("asymmetry_detected", False)
        if curve == "DAMPENING":
            signals.append(
                "Oscillation amplitude dampening — residual recognition capacity attenuating. "
                "Pre-capture signal: transition from resistance to absorption may be underway."
            )
            # DAMPENING alone → HIGH; DAMPENING + hesitation asymmetry → CRITICAL.
            # Two simultaneous pre-capture signals across independent dimensions.
            risk_level = "CRITICAL" if asymmetry_active else "HIGH"
        elif curve == "AMPLIFYING":
            signals.append(
                "Oscillation amplitude amplifying — evaluative conflict intensifying."
            )
            # AMPLIFYING + hesitation asymmetry → CRITICAL.
            # Conflict is escalating AND the frame is already routing tension into
            # deferral shortcuts — two compounding destabilisation signals.
            # ADR-134 architectural decision 2026-04-28: this combination is
            # categorically equivalent to DAMPENING + ASYMMETRY for risk escalation.
            if asymmetry_active:
                risk_level = "CRITICAL"
            elif risk_level in ("LOW", "MEDIUM"):
                risk_level = "HIGH"

        if not signals:
            signals.append("No significant oscillation, phase transitions, or asymmetry detected.")

        return {
            "risk_level":   risk_level,
            "signals":      signals,
            "signal_count": len(signals),
            "recommendation": _risk_recommendation(risk_level),
        }


# ── Module-level convenience ──────────────────────────────────────────────────

def get_oscillation_engine(db_url: Optional[str] = None) -> OscillationInsightEngine:
    """Return an OscillationInsightEngine using environment DB config."""
    return OscillationInsightEngine(db_url=db_url)


# ── Pure calculation helpers ──────────────────────────────────────────────────

def _linear_slope(values: List[float]) -> Optional[float]:
    """
    Ordinary least-squares slope for a sequence of values.
    Returns None if fewer than 2 data points.
    Units: value per step (pp per week for hold_rate).
    """
    n = len(values)
    if n < 2:
        return None
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    num   = sum((xs[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denom = sum((xs[i] - x_mean) ** 2 for i in range(n))
    if denom == 0:
        return None
    return round(num / denom, 6)


def _canonical_decision(raw: str) -> str:
    """Normalise decision strings to APPROVED / BLOCKED / HOLD."""
    u = raw.upper()
    if u in ("APPROVED", "APPROVED_CONDITIONAL", "APPROVE", "PASS"):
        return "APPROVED"
    if u in ("BLOCKED", "BLOCK", "REJECT"):
        return "BLOCKED"
    if u in ("HOLD", "DEFER", "PENDING"):
        return "HOLD"
    return raw.upper()


def _risk_recommendation(level: str) -> str:
    return {
        "LOW":      "No action required. Continue routine monitoring.",
        "MEDIUM":   "Review oscillation pattern and phase segments. "
                    "Validate calibration reference legitimacy.",
        "HIGH":     "Escalate to human oversight review. "
                    "Assess whether evaluative frame is defaulting to deferral under load. "
                    "Consider second-order monitor recalibration.",
        "CRITICAL": "Immediate governance review required. "
                    "Pre-capture signals present across multiple dimensions. "
                    "External legitimacy anchoring recommended. "
                    "Engage HDI layer for independent evaluative validation.",
    }.get(level, "No recommendation available.")
