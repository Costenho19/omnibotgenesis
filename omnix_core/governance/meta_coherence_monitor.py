"""
OMNIX Meta-Coherence Monitor (MCM)
ADR-117: Second-Order Governance Perception Stability

═══════════════════════════════════════════════════════════════════════════════
PROBLEM STATEMENT (Amanulla Khan, Apr 24 2026)
═══════════════════════════════════════════════════════════════════════════════

The AVM (ADR-064) detects when live conditions have drifted from the frozen
calibration baseline — that is first-order drift detection.

But there is a deeper failure mode:

    "What if the interpretive logic that *evaluates* divergence has itself
    begun adapting to the degraded state?"

If the governance evaluation frame normalizes degraded conditions, apparent
coherence can persist for long periods without reflecting actual environmental
validity. This is what institutions call "stabilized degradation" — the system
looks stable because the measurement frame drifted with the environment.

Standard drift detection operates on OUTPUTS.
The MCM operates on the EVALUATION FRAME itself.

═══════════════════════════════════════════════════════════════════════════════
THREE DETECTION MECHANISMS
═══════════════════════════════════════════════════════════════════════════════

1. VERDICT_DISTRIBUTION_DRIFT
   Compares the BLOCKED/HELD/APPROVED ratio between a reference window
   (earlier period) and the current window. A systematic shift in the BLOCK
   rate — without a corresponding change in AVM baseline conditions — is the
   primary "compensatory normalization" signature.

   Key signal: BLOCK_RATE_COLLAPSE (e.g., 13% → 1.3% in 30 days while
   AVM baselines remain unchanged → evaluator is normalizing degradation).

2. VETO_PATTERN_ASYMMETRY
   Analyzes which gates appear in decision veto_chains across both windows.
   If a gate that previously fired on 20% of decisions now fires on 2%,
   without the gate's threshold changing, it is absorbing normalization
   silently. This is the "local compensation" Amanullah describes.

3. REFERENCE_LEGITIMACY
   Validates whether the AVM calibration baseline still represents the
   operating reality it was calibrated against. Checks:
   - Calibration age vs max_age_hours (ADR-064 §4.1)
   - Whether the baseline signal_coherence reflects current blocking patterns
   - Whether a recalibration event may itself have anchored to a degraded state

═══════════════════════════════════════════════════════════════════════════════
TRANSITION SIGNATURES (pre-divergence early warning)
═══════════════════════════════════════════════════════════════════════════════

Unlike the AVM which fires on threshold breach, the MCM surfaces transition
signatures BEFORE divergence becomes explicit:

   - BLOCK_RATE_VARIANCE_SPIKE: increasing week-over-week variance in BLOCK
     rate (instability precedes mean shift)
   - HOLD_ABSORPTION: HOLD rate increasing while BLOCK rate falls
     (decisions deferred rather than resolved — classic normalization)
   - GATE_SILENCE: a previously active veto gate falls below 10% of prior
     firing frequency (gate is being bypassed or threshold normalized)
   - REFERENCE_AGE_WARNING: calibration snapshot approaching max_age_hours
   - RECALIBRATION_ANCHORING_RISK: last recalibration occurred during a
     period of low BLOCK rate (may have frozen a degraded state as baseline)

═══════════════════════════════════════════════════════════════════════════════
ARCHITECTURE POSITION
═══════════════════════════════════════════════════════════════════════════════

    AVM (ADR-064)  →  first-order drift (signals vs calibration)
    MCM (ADR-117)  →  second-order drift (evaluation frame vs reality)
                       operates independently of the pipeline it monitors

The MCM MUST NOT share state with the pipeline it monitors. It reads from
the historical record (decision_receipts, avm_calibration_snapshots) and
writes findings to governance_drift_log — never modifying pipeline state.

═══════════════════════════════════════════════════════════════════════════════
FAIL-CLOSED POLICY
═══════════════════════════════════════════════════════════════════════════════

If the MCM encounters a DB error or internal exception:
  - It logs the error at WARNING level
  - It returns a MetaCoherenceReport with evaluation_frame_stable=None
    (unknown, not True) and alert_level="UNKNOWN"
  - It NEVER returns evaluation_frame_stable=True under uncertainty

Harold Nunes — OMNIX Decision Governance Infrastructure
Build 6.6.0 | ADR-117 | April 24, 2026
"""

from __future__ import annotations

import json
import logging
import math
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("OMNIX.MCM")

# ── Constants ──────────────────────────────────────────────────────────────────

MCM_VERSION = "1.1.0"

# Verdict normalization map — decision column is inconsistent across pipeline
# versions (APPROVED/APPROVE, BLOCKED/BLOCK). Normalized to 3 categories.
_VERDICT_MAP: dict[str, str] = {
    "approved": "APPROVED",
    "approve":  "APPROVED",
    "blocked":  "BLOCKED",
    "block":    "BLOCKED",
    "held":     "HELD",
    "hold":     "HELD",
}

# Drift score weights for verdict distribution drift.
# BLOCK rate collapse is the primary normalization signature → highest weight.
_VERDICT_WEIGHTS: dict[str, float] = {
    "BLOCKED":  0.55,
    "HELD":     0.25,
    "APPROVED": 0.20,
}

# Gate silence threshold: a gate that drops below this fraction of its
# reference firing rate is considered silenced (normalization signature).
_GATE_SILENCE_RATIO = 0.15

# Alert thresholds for normalized drift score (0-100).
_THRESHOLD_WARNING  = 20.0   # significant shift requiring monitoring
_THRESHOLD_CRITICAL = 45.0   # evaluator likely adapting to degraded state

# Map internal alert levels to governance_drift_log DB constraint values.
# DB constraint: alert_level IN ('ALERT', 'WARNING', 'OK')
_DB_ALERT_MAP: dict[str, str] = {
    "CRITICAL": "ALERT",
    "WARNING":  "WARNING",
    "OK":       "OK",
    "UNKNOWN":  "OK",
}

# Reference age warning: flag when calibration is this fraction of max_age_hours
_REFERENCE_AGE_WARNING_FRACTION = 0.75  # warn at 75% of max age

# Minimum sample size to trust a distribution window.
_MIN_SAMPLE_SIZE = 50

# ── DEFERRAL_TRAJECTORY constants (MCM v1.1 — ADR-117 §3.4) ───────────────────
#
# Amanulla Khan insight (24 Apr 2026):
#   "Instability may first redistribute itself into latency, hesitation, or
#    compensatory buffering dynamics before manifesting as overt failure.
#    Longitudinal changes in absorption patterns may reveal degradation
#    trajectories earlier than direct outcome analysis."
#
# These constants govern the 4th MCM signal: time-series trajectory of the
# deferral (HOLD) rate. We compute velocity (Δhold_rate/period) and
# acceleration (Δvelocity/period) over rolling weekly windows.

# Minimum number of weekly periods required for trajectory analysis.
_MIN_TRAJECTORY_PERIODS = 4

# Granularity for trajectory bucketing (days per period).
_TRAJECTORY_GRANULARITY_DAYS = 7

# Velocity thresholds: pp/period (percentage-points per week) of HOLD growth.
_DEFERRAL_VELOCITY_WARNING  = 1.5   # ≥ 1.5 pp/week → sustained deferral growth
_DEFERRAL_VELOCITY_CRITICAL = 4.0   # ≥ 4.0 pp/week → rapid deferral accumulation

# Acceleration threshold: pp/period² — velocity itself increasing.
_DEFERRAL_ACCELERATION_WARNING = 0.5  # ≥ 0.5 pp/week² → deferral intensifying

# Volatility threshold: standard deviation of hold rates across periods.
# High volatility indicates the system is oscillating between enforcement and
# deferral — an unstable regime even if the mean looks acceptable.
_DEFERRAL_VOLATILITY_HIGH    = 12.0  # ≥ 12 pp std — oscillation signature

# Sustained trend thresholds: consecutive periods with positive velocity.
_DEFERRAL_SUSTAINED_WARNING  = 3    # 3+ consecutive weeks rising → trend forming
_DEFERRAL_SUSTAINED_CRITICAL = 5    # 5+ consecutive weeks rising → serious pattern


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class TransitionSignature:
    """
    A detected pre-divergence signal — an early warning that the evaluation
    frame may be beginning to adapt before drift becomes threshold-explicit.
    """
    signal_id:   str    # e.g. "BLOCK_RATE_COLLAPSE", "GATE_SILENCE:COHERENCE_GATE"
    description: str    # Human-readable description of what was detected
    severity:    str    # "INFO", "WARNING", "CRITICAL"
    metric_name: str    # The metric that triggered this signature
    observed:    float  # Current observed value
    reference:   float  # Reference (baseline) value
    delta:       float  # Absolute difference (observed - reference)


@dataclass
class VerdictDistributionResult:
    """
    Result of comparing verdict (APPROVED/BLOCKED/HELD) distributions
    between the reference and current observation windows.
    """
    domain:              str
    reference_window_days: int
    current_window_days:   int

    # Sample counts
    reference_total:     int   = 0
    current_total:       int   = 0
    sufficient_data:     bool  = False

    # Distribution (%) — reference window
    ref_blocked_pct:     float = 0.0
    ref_held_pct:        float = 0.0
    ref_approved_pct:    float = 0.0

    # Distribution (%) — current window
    cur_blocked_pct:     float = 0.0
    cur_held_pct:        float = 0.0
    cur_approved_pct:    float = 0.0

    # Drift scores per verdict category (0-100, higher = more drift)
    block_drift:         float = 0.0
    hold_drift:          float = 0.0
    approve_drift:       float = 0.0

    # Composite weighted drift score (0-100)
    composite_drift:     float = 0.0

    # Alert level for this analysis
    alert_level:         str   = "UNKNOWN"

    # Detected transition signatures for this dimension
    signatures:          list[TransitionSignature] = field(default_factory=list)

    # Error details if analysis failed
    error:               str | None = None


@dataclass
class VetoPatternResult:
    """
    Result of analyzing veto gate firing frequency across reference
    and current windows. Detects asymmetric gate silencing.
    """
    domain:                str
    reference_window_days: int
    current_window_days:   int

    # Gate frequencies (gate_name → proportion of decisions where it appeared)
    ref_gate_freq:         dict[str, float] = field(default_factory=dict)
    cur_gate_freq:         dict[str, float] = field(default_factory=dict)

    # Gates that dropped below _GATE_SILENCE_RATIO of their reference frequency
    silenced_gates:        list[str]  = field(default_factory=list)

    # Gates that increased significantly (compensatory concentration)
    amplified_gates:       list[str]  = field(default_factory=list)

    # Composite asymmetry score (0-100)
    asymmetry_score:       float = 0.0
    alert_level:           str   = "UNKNOWN"
    signatures:            list[TransitionSignature] = field(default_factory=list)
    error:                 str | None = None


@dataclass
class ReferenceLegitimacyResult:
    """
    Result of validating whether the AVM calibration baseline still
    represents the operating reality it was calibrated against.
    """
    domain:                str

    snapshot_id:           str   = ""
    calibrated_at:         str   = ""
    calibration_age_hours: float = 0.0
    max_age_hours:         float = 168.0
    age_fraction:          float = 0.0  # calibration_age / max_age

    # Baseline signal coherence from calibration snapshot
    baseline_signal_coherence: float = 0.0

    # Whether last recalibration occurred during a low-block-rate period
    # (risk: baseline may have been anchored to a degraded state)
    recalibration_anchoring_risk: bool = False
    recalibration_block_rate_at_calibration: float | None = None

    alert_level:           str   = "UNKNOWN"
    signatures:            list[TransitionSignature] = field(default_factory=list)
    error:                 str | None = None


@dataclass
class DeferralTrajectoryResult:
    """
    Result of time-series trajectory analysis of the HOLD (deferral) rate.

    Fourth MCM signal (v1.1) — answers Amanulla Khan's question (24 Apr 2026):

        "Whether longitudinal changes in absorption patterns, escalation
        density, or decision deferral behaviour may reveal degradation
        trajectories earlier than direct outcome analysis alone."

    Computes, per rolling time period (default: weekly):
        - hold_rate        : HOLD decisions / total decisions (%)
        - velocity         : Δhold_rate / period (pp/week)
        - acceleration     : Δvelocity / period (pp/week²)

    Key insight: HOLD rate velocity and acceleration carry predictive signal
    before the cross-window HOLD delta detected by VERDICT_DISTRIBUTION_DRIFT.
    This is the "pre-divergence early warning" layer.
    """
    domain:               str
    granularity_days:     int   = _TRAJECTORY_GRANULARITY_DAYS
    lookback_days:        int   = 56   # Total window analysed (8 weeks default)

    # Time series: ISO date labels and corresponding HOLD rates (%)
    period_labels:        list[str]   = field(default_factory=list)
    hold_rates:           list[float] = field(default_factory=list)   # pp per period
    period_totals:        list[int]   = field(default_factory=list)   # total decisions

    # Velocity series: Δhold_rate per period (pp/period)
    velocity_series:      list[float] = field(default_factory=list)

    # Summary statistics
    mean_hold_rate:       float = 0.0   # Mean HOLD rate across periods (pp)
    hold_rate_std:        float = 0.0   # Std dev — high value = oscillation
    mean_velocity:        float = 0.0   # Mean week-over-week HOLD growth (pp/period)
    peak_velocity:        float = 0.0   # Maximum single-period HOLD growth observed
    acceleration:         float = 0.0   # Mean of velocity deltas (pp/period²)

    # Trend continuity: max number of consecutive periods with positive velocity
    sustained_increasing_periods: int = 0

    # Composite trajectory score (0-100): higher = more concerning trajectory
    trajectory_score:     float = 0.0
    sufficient_data:      bool  = False

    alert_level:          str   = "UNKNOWN"
    signatures:           list[TransitionSignature] = field(default_factory=list)
    error:                str | None = None


@dataclass
class MetaCoherenceReport:
    """
    Composite second-order coherence report for a single domain.

    Answers: "Has the governance evaluation frame begun adapting to
    degraded conditions, independent of whether individual outputs
    pass first-order drift detection?"
    """
    report_id:             str   = field(default_factory=lambda: f"MCM-{uuid.uuid4().hex[:10].upper()}")
    domain:                str   = "UNKNOWN"
    generated_at:          str   = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    mcm_version:           str   = MCM_VERSION

    # Sub-results (4 detection mechanisms)
    verdict_distribution:  VerdictDistributionResult  | None = None
    veto_pattern:          VetoPatternResult           | None = None
    reference_legitimacy:  ReferenceLegitimacyResult   | None = None
    deferral_trajectory:   DeferralTrajectoryResult    | None = None   # v1.1

    # Composite score (0-100) — higher = more concern about frame stability
    composite_score:       float = 0.0

    # Top-level stability assessment
    # True  = frame appears stable
    # False = frame shows normalization signatures
    # None  = insufficient data or analysis error
    evaluation_frame_stable: bool | None = None

    # All detected transition signatures, ranked by severity
    transition_signatures: list[TransitionSignature] = field(default_factory=list)

    # Final alert level: "OK" | "WARNING" | "CRITICAL" | "UNKNOWN"
    alert_level:           str   = "UNKNOWN"

    # Human-readable summary for investor/partner communications
    executive_summary:     str   = ""


# ── Core Monitor ───────────────────────────────────────────────────────────────

class MetaCoherenceMonitor:
    """
    Second-order governance perception monitor.

    Detects when the evaluation frame assessing governance drift has
    itself begun adapting — the meta-problem that first-order drift
    detectors (AVM) cannot observe from within.

    Usage:
        monitor = MetaCoherenceMonitor(db_url)
        report  = monitor.run_full_analysis("trading")
        monitor.persist_to_db(report)
    """

    def __init__(self, db_url: str | None = None) -> None:
        import os
        self._db_url = db_url or os.environ.get("OMNIX_DB_URL", "")
        if not self._db_url:
            logger.warning("[MCM] No DB URL — operating in offline mode")

    # ── Public API ─────────────────────────────────────────────────────────────

    def run_full_analysis(
        self,
        domain: str = "trading",
        reference_days: int = 30,
        current_days:   int = 14,
        persist: bool = True,
    ) -> MetaCoherenceReport:
        """
        Run all three MCM detection mechanisms for the given domain and
        return a composite MetaCoherenceReport.

        Args:
            domain:         Governance domain (e.g., "trading", "medical_ai")
            reference_days: How many days back to use as the reference window.
                            This window starts at 2×current_days ago and
                            ends at current_days ago.
            current_days:   The recent window to compare against reference.
            persist:        If True (default), persist findings to governance_drift_log.
                            Set False for read-only analysis (audits, tests).

        Returns:
            MetaCoherenceReport with composite score, alert level, and all
            detected transition signatures.
        """
        logger.info(f"[MCM] Starting analysis | domain={domain} | "
                    f"ref={reference_days}d | cur={current_days}d")

        report = MetaCoherenceReport(domain=domain)

        try:
            report.verdict_distribution = self._analyze_verdict_distribution(
                domain, reference_days, current_days
            )
        except Exception as exc:
            logger.warning(f"[MCM] verdict_distribution failed: {exc}")
            report.verdict_distribution = VerdictDistributionResult(
                domain=domain,
                reference_window_days=reference_days,
                current_window_days=current_days,
                error=str(exc),
                alert_level="UNKNOWN",
            )

        try:
            report.veto_pattern = self._analyze_veto_pattern(
                domain, reference_days, current_days
            )
        except Exception as exc:
            logger.warning(f"[MCM] veto_pattern failed: {exc}")
            report.veto_pattern = VetoPatternResult(
                domain=domain,
                reference_window_days=reference_days,
                current_window_days=current_days,
                error=str(exc),
                alert_level="UNKNOWN",
            )

        try:
            report.reference_legitimacy = self._analyze_reference_legitimacy(
                domain, current_days
            )
        except Exception as exc:
            logger.warning(f"[MCM] reference_legitimacy failed: {exc}")
            report.reference_legitimacy = ReferenceLegitimacyResult(
                domain=domain,
                error=str(exc),
                alert_level="UNKNOWN",
            )

        try:
            lookback = reference_days + current_days
            report.deferral_trajectory = self._analyze_deferral_trajectory(
                domain,
                lookback_days=lookback,
                granularity_days=_TRAJECTORY_GRANULARITY_DAYS,
            )
        except Exception as exc:
            logger.warning(f"[MCM] deferral_trajectory failed: {exc}")
            report.deferral_trajectory = DeferralTrajectoryResult(
                domain=domain,
                error=str(exc),
                alert_level="UNKNOWN",
            )

        self._compose_report(report)

        logger.info(
            f"[MCM] Analysis complete | domain={domain} | "
            f"score={report.composite_score:.1f} | "
            f"alert={report.alert_level} | "
            f"stable={report.evaluation_frame_stable} | "
            f"signatures={len(report.transition_signatures)}"
        )

        if persist:
            self.persist_to_db(report)

        # ADR-118: auto-remediate on CRITICAL alert
        if report.alert_level == "CRITICAL":
            self.auto_remediate(report)

        return report

    def run_all_domains(
        self,
        reference_days: int = 30,
        current_days:   int = 14,
    ) -> list[MetaCoherenceReport]:
        """
        Run full analysis for all domains that have AVM calibration snapshots.
        """
        domains = self._get_active_domains()
        reports = []
        for domain in domains:
            report = self.run_full_analysis(domain, reference_days, current_days)
            reports.append(report)
        return reports

    def persist_to_db(self, report: MetaCoherenceReport) -> bool:
        """
        Write the composite MCM findings to the governance_drift_log table.
        Each signal dimension is written as a separate row.

        Returns True if at least one row was persisted, False otherwise.
        """
        if not self._db_url:
            logger.warning("[MCM] Cannot persist — no DB URL")
            return False

        try:
            import psycopg
            conn = psycopg.connect(self._db_url)
            cur  = conn.cursor()

            rows_written = 0

            # Row 1: Verdict distribution drift
            if report.verdict_distribution and not report.verdict_distribution.error:
                vd = report.verdict_distribution
                cur.execute(
                    """
                    INSERT INTO governance_drift_log
                        (client_id, signal_name, baseline_stats, current_stats,
                         drift_score, threshold, alert_level, detected_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        f"MCM:{report.domain}",
                        "VERDICT_DISTRIBUTION_DRIFT",
                        json.dumps({
                            "blocked_pct":  vd.ref_blocked_pct,
                            "held_pct":     vd.ref_held_pct,
                            "approved_pct": vd.ref_approved_pct,
                            "total":        vd.reference_total,
                            "window_days":  vd.reference_window_days,
                        }),
                        json.dumps({
                            "blocked_pct":  vd.cur_blocked_pct,
                            "held_pct":     vd.cur_held_pct,
                            "approved_pct": vd.cur_approved_pct,
                            "total":        vd.current_total,
                            "window_days":  vd.current_window_days,
                        }),
                        vd.composite_drift,
                        _THRESHOLD_WARNING,
                        _DB_ALERT_MAP.get(vd.alert_level, "OK"),
                    ),
                )
                rows_written += 1

            # Row 2: Veto pattern asymmetry
            if report.veto_pattern and not report.veto_pattern.error:
                vp = report.veto_pattern
                cur.execute(
                    """
                    INSERT INTO governance_drift_log
                        (client_id, signal_name, baseline_stats, current_stats,
                         drift_score, threshold, alert_level, detected_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        f"MCM:{report.domain}",
                        "VETO_PATTERN_ASYMMETRY",
                        json.dumps({"gate_frequencies": vp.ref_gate_freq}),
                        json.dumps({
                            "gate_frequencies": vp.cur_gate_freq,
                            "silenced_gates":   vp.silenced_gates,
                            "amplified_gates":  vp.amplified_gates,
                        }),
                        vp.asymmetry_score,
                        _THRESHOLD_WARNING,
                        _DB_ALERT_MAP.get(vp.alert_level, "OK"),
                    ),
                )
                rows_written += 1

            # Row 3: Reference legitimacy
            if report.reference_legitimacy and not report.reference_legitimacy.error:
                rl = report.reference_legitimacy
                cur.execute(
                    """
                    INSERT INTO governance_drift_log
                        (client_id, signal_name, baseline_stats, current_stats,
                         drift_score, threshold, alert_level, detected_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        f"MCM:{report.domain}",
                        "REFERENCE_LEGITIMACY",
                        json.dumps({
                            "snapshot_id":        rl.snapshot_id,
                            "calibrated_at":      rl.calibrated_at,
                            "max_age_hours":      rl.max_age_hours,
                            "baseline_coherence": rl.baseline_signal_coherence,
                        }),
                        json.dumps({
                            "calibration_age_hours": rl.calibration_age_hours,
                            "age_fraction":          rl.age_fraction,
                            "anchoring_risk":        rl.recalibration_anchoring_risk,
                        }),
                        rl.age_fraction * 100.0,
                        _REFERENCE_AGE_WARNING_FRACTION * 100.0,
                        _DB_ALERT_MAP.get(rl.alert_level, "OK"),
                    ),
                )
                rows_written += 1

            # Row 4: Deferral trajectory (v1.1)
            if (report.deferral_trajectory
                    and not report.deferral_trajectory.error
                    and report.deferral_trajectory.sufficient_data):
                dt = report.deferral_trajectory
                cur.execute(
                    """
                    INSERT INTO governance_drift_log
                        (client_id, signal_name, baseline_stats, current_stats,
                         drift_score, threshold, alert_level, detected_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        f"MCM:{report.domain}",
                        "DEFERRAL_TRAJECTORY",
                        json.dumps({
                            "periods":          len(dt.period_labels),
                            "lookback_days":    dt.lookback_days,
                            "granularity_days": dt.granularity_days,
                            "period_labels":    dt.period_labels,
                            "hold_rates":       dt.hold_rates,
                        }),
                        json.dumps({
                            "mean_hold_rate":              dt.mean_hold_rate,
                            "hold_rate_std":               dt.hold_rate_std,
                            "mean_velocity_pp_per_week":   dt.mean_velocity,
                            "peak_velocity_pp_per_week":   dt.peak_velocity,
                            "acceleration_pp_per_week_sq": dt.acceleration,
                            "sustained_increasing_periods": dt.sustained_increasing_periods,
                            "velocity_series":             dt.velocity_series,
                        }),
                        dt.trajectory_score,
                        _DEFERRAL_VELOCITY_WARNING,
                        _DB_ALERT_MAP.get(dt.alert_level, "OK"),
                    ),
                )
                rows_written += 1

            conn.commit()
            conn.close()

            logger.info(f"[MCM] Persisted {rows_written} rows to governance_drift_log | "
                        f"domain={report.domain}")
            return rows_written > 0

        except Exception as exc:
            logger.warning(f"[MCM] persist_to_db failed for domain={report.domain}: {exc}")
            return False

    # ── Analysis: Verdict Distribution Drift ──────────────────────────────────

    def _analyze_verdict_distribution(
        self,
        domain: str,
        reference_days: int,
        current_days: int,
    ) -> VerdictDistributionResult:
        """
        Compare BLOCKED/HELD/APPROVED ratios between the reference and current
        observation windows. A systematic BLOCK_RATE_COLLAPSE without a
        corresponding change in AVM baselines is the primary normalization signal.
        """
        result = VerdictDistributionResult(
            domain=domain,
            reference_window_days=reference_days,
            current_window_days=current_days,
        )

        if not self._db_url:
            result.error = "No DB URL"
            return result

        try:
            import psycopg
            conn = psycopg.connect(self._db_url)
            cur  = conn.cursor()

            # Pull verdict counts for both windows in one query.
            # Reference window: from (reference_days + current_days) to current_days ago.
            # Current window: from current_days ago to now.
            cur.execute("""
                SELECT
                    CASE
                        WHEN created_at >= NOW() - INTERVAL '1 day' * %(cur)s
                        THEN 'current'
                        ELSE 'reference'
                    END                                     AS window,
                    LOWER(TRIM(decision))                   AS raw_verdict,
                    COUNT(*)                                AS cnt
                FROM decision_receipts
                WHERE
                    (domain = %(domain)s OR %(domain)s = 'all')
                    AND created_at >= NOW() - INTERVAL '1 day' * %(total)s
                    AND created_at <= NOW()
                GROUP BY 1, 2
                ORDER BY 1, 3 DESC
            """, {
                "domain": domain,
                "cur":    current_days,
                "total":  reference_days + current_days,
            })

            rows = cur.fetchall()
            conn.close()

            # Aggregate into window → verdict → count
            windows: dict[str, dict[str, int]] = {"reference": {}, "current": {}}
            for window, raw_verdict, cnt in rows:
                normalized = _VERDICT_MAP.get(raw_verdict)
                if not normalized:
                    continue
                windows[window][normalized] = windows[window].get(normalized, 0) + cnt

            ref = windows["reference"]
            cur_w = windows["current"]

            ref_total = sum(ref.values())
            cur_total = sum(cur_w.values())

            result.reference_total = ref_total
            result.current_total   = cur_total
            result.sufficient_data = (
                ref_total >= _MIN_SAMPLE_SIZE and cur_total >= _MIN_SAMPLE_SIZE
            )

            if not result.sufficient_data:
                result.alert_level = "OK"
                result.error = (
                    f"Insufficient data: ref={ref_total} cur={cur_total} "
                    f"(min={_MIN_SAMPLE_SIZE})"
                )
                return result

            def pct(counts: dict, key: str) -> float:
                total = sum(counts.values())
                return round(counts.get(key, 0) * 100.0 / total, 2) if total > 0 else 0.0

            result.ref_blocked_pct  = pct(ref,   "BLOCKED")
            result.ref_held_pct     = pct(ref,   "HELD")
            result.ref_approved_pct = pct(ref,   "APPROVED")

            result.cur_blocked_pct  = pct(cur_w, "BLOCKED")
            result.cur_held_pct     = pct(cur_w, "HELD")
            result.cur_approved_pct = pct(cur_w, "APPROVED")

            # Per-verdict drift (0-100): normalized absolute difference.
            # Using symmetric normalization: diff / (ref + 1) × 100
            def _drift(ref_v: float, cur_v: float) -> float:
                return min(abs(cur_v - ref_v) / (ref_v + 1.0) * 100.0, 100.0)

            result.block_drift   = _drift(result.ref_blocked_pct,  result.cur_blocked_pct)
            result.hold_drift    = _drift(result.ref_held_pct,     result.cur_held_pct)
            result.approve_drift = _drift(result.ref_approved_pct, result.cur_approved_pct)

            result.composite_drift = round(
                result.block_drift   * _VERDICT_WEIGHTS["BLOCKED"]  +
                result.hold_drift    * _VERDICT_WEIGHTS["HELD"]      +
                result.approve_drift * _VERDICT_WEIGHTS["APPROVED"],
                2,
            )

            # Detect transition signatures
            sigs = result.signatures

            # Primary signal: BLOCK rate collapse
            block_delta = result.cur_blocked_pct - result.ref_blocked_pct
            if result.ref_blocked_pct > 0:
                block_ratio = result.cur_blocked_pct / result.ref_blocked_pct
                if block_ratio < 0.25 and result.ref_blocked_pct > 2.0:
                    sigs.append(TransitionSignature(
                        signal_id="BLOCK_RATE_COLLAPSE",
                        description=(
                            f"BLOCK rate dropped from {result.ref_blocked_pct:.1f}% "
                            f"to {result.cur_blocked_pct:.1f}% "
                            f"({block_ratio:.0%} of reference). "
                            "Evaluator may be normalizing conditions that previously triggered blocks."
                        ),
                        severity="CRITICAL",
                        metric_name="blocked_pct",
                        observed=result.cur_blocked_pct,
                        reference=result.ref_blocked_pct,
                        delta=block_delta,
                    ))
                elif block_ratio < 0.50 and result.ref_blocked_pct > 2.0:
                    sigs.append(TransitionSignature(
                        signal_id="BLOCK_RATE_DECLINE",
                        description=(
                            f"BLOCK rate declined to {block_ratio:.0%} of reference. "
                            f"({result.ref_blocked_pct:.1f}% → {result.cur_blocked_pct:.1f}%). "
                            "Monitor for continued decline."
                        ),
                        severity="WARNING",
                        metric_name="blocked_pct",
                        observed=result.cur_blocked_pct,
                        reference=result.ref_blocked_pct,
                        delta=block_delta,
                    ))

            # HOLD absorption: HOLD replacing BLOCK (decisions deferred not resolved)
            hold_delta = result.cur_held_pct - result.ref_held_pct
            if hold_delta > 5.0 and block_delta < -2.0:
                sigs.append(TransitionSignature(
                    signal_id="HOLD_ABSORPTION",
                    description=(
                        f"HOLD rate rose +{hold_delta:.1f}pp while BLOCK rate fell "
                        f"{block_delta:.1f}pp. Decisions are being deferred rather than "
                        "resolved — classic compensatory normalization signature."
                    ),
                    severity="WARNING",
                    metric_name="hold_absorption_delta",
                    observed=hold_delta,
                    reference=0.0,
                    delta=hold_delta,
                ))

            # Set alert level based on composite drift
            if result.composite_drift >= _THRESHOLD_CRITICAL:
                result.alert_level = "CRITICAL"
            elif result.composite_drift >= _THRESHOLD_WARNING:
                result.alert_level = "WARNING"
            else:
                result.alert_level = "OK"

            return result

        except Exception as exc:
            result.error = str(exc)
            result.alert_level = "UNKNOWN"
            return result

    # ── Analysis: Veto Pattern Asymmetry ──────────────────────────────────────

    def _analyze_veto_pattern(
        self,
        domain: str,
        reference_days: int,
        current_days: int,
    ) -> VetoPatternResult:
        """
        Compare which governance gates appear in veto_chains between the
        reference and current windows. A gate that stops firing without a
        policy change is exhibiting silent normalization.
        """
        result = VetoPatternResult(
            domain=domain,
            reference_window_days=reference_days,
            current_window_days=current_days,
        )

        if not self._db_url:
            result.error = "No DB URL"
            return result

        try:
            import psycopg
            conn = psycopg.connect(self._db_url)
            cur  = conn.cursor()

            cur.execute("""
                SELECT
                    CASE
                        WHEN created_at >= NOW() - INTERVAL '1 day' * %(cur)s
                        THEN 'current'
                        ELSE 'reference'
                    END AS window,
                    veto_chain,
                    COUNT(*) OVER (
                        PARTITION BY
                            CASE WHEN created_at >= NOW() - INTERVAL '1 day' * %(cur)s
                            THEN 'current' ELSE 'reference' END
                    ) AS window_total
                FROM decision_receipts
                WHERE
                    (domain = %(domain)s OR %(domain)s = 'all')
                    AND veto_chain IS NOT NULL
                    AND veto_chain NOT IN ('[]', 'null', '')
                    AND created_at >= NOW() - INTERVAL '1 day' * %(total)s
            """, {
                "domain": domain,
                "cur":    current_days,
                "total":  reference_days + current_days,
            })

            rows = cur.fetchall()
            conn.close()

            if not rows:
                result.error = "No veto_chain data found"
                result.alert_level = "OK"
                return result

            # Parse gate names from veto_chain entries
            ref_gate_counts: dict[str, int] = {}
            cur_gate_counts: dict[str, int] = {}
            ref_total = cur_total = 0

            for window, veto_chain, window_total in rows:
                if window == "reference":
                    ref_total = window_total
                else:
                    cur_total = window_total

                gates = self._extract_gate_names(veto_chain)
                counts = ref_gate_counts if window == "reference" else cur_gate_counts
                for gate in gates:
                    counts[gate] = counts.get(gate, 0) + 1

            if ref_total < _MIN_SAMPLE_SIZE or cur_total < _MIN_SAMPLE_SIZE:
                result.alert_level = "OK"
                result.error = f"Insufficient data: ref={ref_total} cur={cur_total}"
                return result

            # Normalize to frequency (proportion of decisions)
            result.ref_gate_freq = {
                g: round(c / ref_total, 4) for g, c in ref_gate_counts.items()
            }
            result.cur_gate_freq = {
                g: round(c / cur_total, 4) for g, c in cur_gate_counts.items()
            }

            # Detect silenced and amplified gates
            all_gates = set(result.ref_gate_freq) | set(result.cur_gate_freq)
            asymmetry_total = 0.0
            sigs = result.signatures

            for gate in all_gates:
                ref_freq = result.ref_gate_freq.get(gate, 0.0)
                cur_freq = result.cur_gate_freq.get(gate, 0.0)
                asymmetry_total += abs(cur_freq - ref_freq)

                if ref_freq > 0.01:  # gate was meaningful in reference
                    ratio = cur_freq / ref_freq if ref_freq > 0 else 0.0

                    if ratio < _GATE_SILENCE_RATIO:
                        result.silenced_gates.append(gate)
                        sigs.append(TransitionSignature(
                            signal_id=f"GATE_SILENCE:{gate}",
                            description=(
                                f"Gate '{gate}' fired on {ref_freq:.1%} of decisions "
                                f"in reference window, now {cur_freq:.1%} "
                                f"({ratio:.0%} of prior rate). "
                                "Gate may be normalized or threshold drifted."
                            ),
                            severity="WARNING",
                            metric_name=f"gate_freq:{gate}",
                            observed=cur_freq,
                            reference=ref_freq,
                            delta=cur_freq - ref_freq,
                        ))

                    elif ratio > 2.0 and cur_freq > 0.05:
                        result.amplified_gates.append(gate)
                        sigs.append(TransitionSignature(
                            signal_id=f"GATE_AMPLIFICATION:{gate}",
                            description=(
                                f"Gate '{gate}' frequency doubled "
                                f"({ref_freq:.1%} → {cur_freq:.1%}). "
                                "May indicate compensatory concentration — "
                                "other gates silencing while this one absorbs."
                            ),
                            severity="INFO",
                            metric_name=f"gate_freq:{gate}",
                            observed=cur_freq,
                            reference=ref_freq,
                            delta=cur_freq - ref_freq,
                        ))

            result.asymmetry_score = round(min(asymmetry_total * 100.0, 100.0), 2)

            if result.asymmetry_score >= _THRESHOLD_CRITICAL or len(result.silenced_gates) >= 3:
                result.alert_level = "CRITICAL"
            elif result.asymmetry_score >= _THRESHOLD_WARNING or result.silenced_gates:
                result.alert_level = "WARNING"
            else:
                result.alert_level = "OK"

            return result

        except Exception as exc:
            result.error = str(exc)
            result.alert_level = "UNKNOWN"
            return result

    # ── Analysis: Reference Legitimacy ────────────────────────────────────────

    def _analyze_reference_legitimacy(
        self,
        domain: str,
        current_days: int,
    ) -> ReferenceLegitimacyResult:
        """
        Validate whether the AVM calibration baseline still legitimately
        represents the operating reality it was designed for.

        Key risk: if the last recalibration occurred during a period of
        low BLOCK rate, the "frozen reference" may itself encode a degraded state.
        This is the deepest form of reference obsolescence.
        """
        result = ReferenceLegitimacyResult(domain=domain)

        if not self._db_url:
            result.error = "No DB URL"
            return result

        try:
            import psycopg
            conn = psycopg.connect(self._db_url)
            cur  = conn.cursor()

            # Load AVM calibration snapshot for this domain
            cur.execute("""
                SELECT
                    snapshot_id,
                    calibrated_at,
                    calibrated_at_epoch,
                    baseline_signals,
                    max_age_hours,
                    drift_threshold
                FROM avm_calibration_snapshots
                WHERE domain = %s AND is_active = true
                LIMIT 1
            """, (domain,))

            row = cur.fetchone()
            if not row:
                result.error = f"No active AVM snapshot for domain '{domain}'"
                result.alert_level = "UNKNOWN"
                conn.close()
                return result

            snap_id, cal_at, cal_epoch, baseline_raw, max_age, _ = row

            result.snapshot_id  = snap_id or ""
            result.calibrated_at = str(cal_at or "")
            result.max_age_hours = float(max_age or 168.0)

            # Calculate calibration age
            if cal_epoch:
                from time import time as _time
                age_secs = _time() - float(cal_epoch)
                result.calibration_age_hours = round(age_secs / 3600.0, 1)
            elif cal_at:
                try:
                    from datetime import datetime, timezone
                    cal_dt = datetime.fromisoformat(str(cal_at).replace("Z", "+00:00"))
                    now_dt = datetime.now(timezone.utc)
                    result.calibration_age_hours = round(
                        (now_dt - cal_dt).total_seconds() / 3600.0, 1
                    )
                except Exception as _e:
                    logger.debug(f"[MCM] calibration_age parse failed for domain snapshot: {_e}")

            result.age_fraction = round(
                result.calibration_age_hours / max(result.max_age_hours, 1.0), 3
            )

            # Extract baseline_signal_coherence
            try:
                bs = baseline_raw if isinstance(baseline_raw, dict) else json.loads(baseline_raw or "{}")
                result.baseline_signal_coherence = float(bs.get("signal_coherence", 0.0))
            except Exception as _e:
                logger.debug(f"[MCM] baseline_signal_coherence parse failed: {_e}")

            # Compute BLOCK rate at the time of calibration (±7 days around cal_at)
            if cal_at:
                cur.execute("""
                    SELECT
                        LOWER(TRIM(decision)) AS verdict,
                        COUNT(*) AS cnt
                    FROM decision_receipts
                    WHERE
                        (domain = %(domain)s OR %(domain)s = 'all')
                        AND created_at BETWEEN
                            %(cal_at)s::timestamptz - INTERVAL '7 days'
                            AND %(cal_at)s::timestamptz + INTERVAL '7 days'
                    GROUP BY 1
                """, {"domain": domain, "cal_at": str(cal_at)})

                cal_rows = cur.fetchall()
                cal_verdicts: dict[str, int] = {}
                for verdict, cnt in cal_rows:
                    norm = _VERDICT_MAP.get(verdict)
                    if norm:
                        cal_verdicts[norm] = cal_verdicts.get(norm, 0) + cnt

                cal_total = sum(cal_verdicts.values())
                if cal_total >= _MIN_SAMPLE_SIZE:
                    cal_block_pct = cal_verdicts.get("BLOCKED", 0) * 100.0 / cal_total
                    result.recalibration_block_rate_at_calibration = round(cal_block_pct, 2)
                    # If BLOCK rate at calibration was <3%, the baseline may encode degradation
                    if cal_block_pct < 3.0:
                        result.recalibration_anchoring_risk = True

            conn.close()

            # Build signatures
            sigs = result.signatures

            if result.age_fraction >= 1.0:
                sigs.append(TransitionSignature(
                    signal_id="REFERENCE_AGE_EXCEEDED",
                    description=(
                        f"Calibration snapshot is {result.calibration_age_hours:.0f}h old "
                        f"(max: {result.max_age_hours:.0f}h). "
                        "Reference exceeded its design validity window."
                    ),
                    severity="CRITICAL",
                    metric_name="calibration_age_hours",
                    observed=result.calibration_age_hours,
                    reference=result.max_age_hours,
                    delta=result.calibration_age_hours - result.max_age_hours,
                ))
            elif result.age_fraction >= _REFERENCE_AGE_WARNING_FRACTION:
                sigs.append(TransitionSignature(
                    signal_id="REFERENCE_AGE_WARNING",
                    description=(
                        f"Calibration snapshot is {result.age_fraction:.0%} through its "
                        f"validity window ({result.calibration_age_hours:.0f}h / "
                        f"{result.max_age_hours:.0f}h). Consider scheduling recalibration."
                    ),
                    severity="WARNING",
                    metric_name="calibration_age_hours",
                    observed=result.calibration_age_hours,
                    reference=result.max_age_hours,
                    delta=result.calibration_age_hours - result.max_age_hours,
                ))

            if result.recalibration_anchoring_risk:
                sigs.append(TransitionSignature(
                    signal_id="RECALIBRATION_ANCHORING_RISK",
                    description=(
                        f"Last recalibration occurred when BLOCK rate was "
                        f"{result.recalibration_block_rate_at_calibration:.1f}% "
                        "(below 3% threshold). The frozen reference may encode a "
                        "degraded state, making it an unreliable validity anchor."
                    ),
                    severity="CRITICAL",
                    metric_name="block_rate_at_calibration",
                    observed=result.recalibration_block_rate_at_calibration or 0.0,
                    reference=3.0,
                    delta=(result.recalibration_block_rate_at_calibration or 0.0) - 3.0,
                ))

            # Determine alert level
            has_critical = any(s.severity == "CRITICAL" for s in sigs)
            has_warning  = any(s.severity == "WARNING"  for s in sigs)

            if has_critical:
                result.alert_level = "CRITICAL"
            elif has_warning:
                result.alert_level = "WARNING"
            else:
                result.alert_level = "OK"

            return result

        except Exception as exc:
            result.error = str(exc)
            result.alert_level = "UNKNOWN"
            return result

    # ── Analysis: Deferral Trajectory (MCM v1.1) ───────────────────────────────

    def _analyze_deferral_trajectory(
        self,
        domain: str,
        lookback_days: int = 56,
        granularity_days: int = _TRAJECTORY_GRANULARITY_DAYS,
    ) -> DeferralTrajectoryResult:
        """
        Time-series analysis of the HOLD (deferral) rate across rolling
        weekly windows.

        Computes:
          - hold_rate per period (weekly %)
          - velocity: Δhold_rate / period (pp/week)
          - acceleration: Δvelocity / period (pp/week²)
          - volatility: standard deviation of hold rates

        Detects pre-divergence signatures:
          - DEFERRAL_VELOCITY_HIGH    : sustained HOLD growth > threshold
          - DEFERRAL_ACCELERATION     : velocity itself increasing
          - SUSTAINED_DEFERRAL_TREND  : N consecutive rising periods
          - DEFERRAL_OSCILLATION      : high std-dev (volatile, not stable)

        Amanulla Khan (24 Apr 2026):
            "Instability may first redistribute itself into latency, hesitation,
             or compensatory buffering dynamics before manifesting as overt failure."
        """
        result = DeferralTrajectoryResult(
            domain=domain,
            granularity_days=granularity_days,
            lookback_days=lookback_days,
        )

        if not self._db_url:
            result.error = "No DB URL"
            result.alert_level = "UNKNOWN"
            return result

        try:
            import psycopg
            conn = psycopg.connect(self._db_url)
            cur  = conn.cursor()

            # Pull per-period verdict counts using DATE_TRUNC for stable weekly
            # boundaries. DATE_TRUNC('week') aligns to Monday, producing
            # consistent 7-day buckets regardless of query time.
            # For non-7-day granularity we fall back to epoch-based bucketing.
            if granularity_days == 7:
                period_trunc = "week"
                cur.execute("""
                    SELECT
                        TO_CHAR(DATE_TRUNC('week', created_at), 'YYYY-MM-DD') AS period_start,
                        COUNT(*)                                               AS total,
                        SUM(CASE
                            WHEN LOWER(TRIM(decision)) IN ('held', 'hold') THEN 1
                            ELSE 0
                        END)                                                   AS holds
                    FROM decision_receipts
                    WHERE
                        (domain = %(domain)s OR %(domain)s = 'all')
                        AND created_at >= NOW() - INTERVAL '1 day' * %(lookback)s
                        AND created_at <= NOW()
                    GROUP BY 1
                    ORDER BY 1
                """, {
                    "domain":   domain,
                    "lookback": lookback_days,
                })
            else:
                # Epoch-bucket for non-weekly granularities
                cur.execute("""
                    SELECT
                        TO_CHAR(
                            TO_TIMESTAMP(
                                FLOOR(EXTRACT(EPOCH FROM created_at)
                                      / (%(gran)s * 86400)) * %(gran)s * 86400
                            ),
                            'YYYY-MM-DD'
                        )                                              AS period_start,
                        COUNT(*)                                       AS total,
                        SUM(CASE
                            WHEN LOWER(TRIM(decision)) IN ('held', 'hold') THEN 1
                            ELSE 0
                        END)                                           AS holds
                    FROM decision_receipts
                    WHERE
                        (domain = %(domain)s OR %(domain)s = 'all')
                        AND created_at >= NOW() - INTERVAL '1 day' * %(lookback)s
                        AND created_at <= NOW()
                    GROUP BY 1
                    ORDER BY 1
                """, {
                    "domain":   domain,
                    "gran":     granularity_days,
                    "lookback": lookback_days,
                })

            rows = cur.fetchall()
            conn.close()

            if not rows:
                result.error = f"No decision data for domain '{domain}'"
                result.alert_level = "OK"
                return result

            # Build time series — filter periods with enough data
            labels:  list[str]   = []
            rates:   list[float] = []
            totals:  list[int]   = []

            for period_start, total, holds in rows:
                if total < 10:   # skip near-empty buckets (incomplete weeks)
                    continue
                hold_pct = round(holds * 100.0 / total, 2)
                labels.append(str(period_start))
                rates.append(hold_pct)
                totals.append(int(total))

            result.period_labels  = labels
            result.hold_rates     = rates
            result.period_totals  = totals
            result.sufficient_data = len(rates) >= _MIN_TRAJECTORY_PERIODS

            if not result.sufficient_data:
                result.error = (
                    f"Insufficient periods: {len(rates)} "
                    f"(min={_MIN_TRAJECTORY_PERIODS})"
                )
                result.alert_level = "OK"
                return result

            # ── Statistics ────────────────────────────────────────────────────
            n = len(rates)
            result.mean_hold_rate = round(sum(rates) / n, 2)

            variance = sum((r - result.mean_hold_rate) ** 2 for r in rates) / n
            result.hold_rate_std  = round(math.sqrt(variance), 2)

            # Velocity series: Δhold_rate between consecutive periods
            velocity: list[float] = [
                round(rates[i] - rates[i - 1], 2)
                for i in range(1, n)
            ]
            result.velocity_series = velocity

            if velocity:
                result.mean_velocity = round(sum(velocity) / len(velocity), 2)
                result.peak_velocity = round(max(velocity, key=abs), 2)

            # Acceleration: mean of velocity deltas
            if len(velocity) >= 2:
                accel_series = [
                    velocity[i] - velocity[i - 1]
                    for i in range(1, len(velocity))
                ]
                result.acceleration = round(
                    sum(accel_series) / len(accel_series), 2
                )

            # Sustained increasing trend: max consecutive positive-velocity periods
            max_streak = cur_streak = 0
            for v in velocity:
                if v > 0:
                    cur_streak += 1
                    max_streak = max(max_streak, cur_streak)
                else:
                    cur_streak = 0
            result.sustained_increasing_periods = max_streak

            # ── Trajectory score (0-100) ──────────────────────────────────────
            # Weighted: velocity component + acceleration component + volatility
            vel_score   = min(abs(result.mean_velocity)  / _DEFERRAL_VELOCITY_CRITICAL * 100, 100)
            accel_score = min(abs(result.acceleration)   / (_DEFERRAL_ACCELERATION_WARNING * 2) * 100, 100)
            vol_score   = min(result.hold_rate_std       / (_DEFERRAL_VOLATILITY_HIGH * 2) * 100, 100)
            trend_score = min(result.sustained_increasing_periods / _DEFERRAL_SUSTAINED_CRITICAL * 100, 100)

            result.trajectory_score = round(
                vel_score * 0.35 +
                accel_score * 0.25 +
                vol_score * 0.25 +
                trend_score * 0.15,
                1,
            )

            # ── Transition signatures ─────────────────────────────────────────
            sigs = result.signatures

            # 1. Deferral velocity — is HOLD rate growing rapidly?
            if result.mean_velocity >= _DEFERRAL_VELOCITY_CRITICAL:
                sigs.append(TransitionSignature(
                    signal_id="DEFERRAL_VELOCITY_HIGH",
                    description=(
                        f"HOLD rate growing at {result.mean_velocity:+.1f} pp/week "
                        f"(critical threshold: {_DEFERRAL_VELOCITY_CRITICAL} pp/week). "
                        f"Mean HOLD rate: {result.mean_hold_rate:.1f}%. "
                        "Decisions are accumulating in deferral at a rate that "
                        "precedes structural output failure."
                    ),
                    severity="CRITICAL",
                    metric_name="mean_velocity_pp_per_week",
                    observed=result.mean_velocity,
                    reference=_DEFERRAL_VELOCITY_CRITICAL,
                    delta=result.mean_velocity - _DEFERRAL_VELOCITY_CRITICAL,
                ))
            elif result.mean_velocity >= _DEFERRAL_VELOCITY_WARNING:
                sigs.append(TransitionSignature(
                    signal_id="DEFERRAL_VELOCITY_RISING",
                    description=(
                        f"HOLD rate growing at {result.mean_velocity:+.1f} pp/week "
                        f"(warning threshold: {_DEFERRAL_VELOCITY_WARNING} pp/week). "
                        "Monitor for sustained growth toward critical threshold."
                    ),
                    severity="WARNING",
                    metric_name="mean_velocity_pp_per_week",
                    observed=result.mean_velocity,
                    reference=_DEFERRAL_VELOCITY_WARNING,
                    delta=result.mean_velocity - _DEFERRAL_VELOCITY_WARNING,
                ))

            # 2. Deferral acceleration — is the velocity itself increasing?
            if result.acceleration >= _DEFERRAL_ACCELERATION_WARNING:
                sigs.append(TransitionSignature(
                    signal_id="DEFERRAL_ACCELERATION",
                    description=(
                        f"HOLD rate velocity is accelerating at "
                        f"{result.acceleration:+.2f} pp/week² "
                        f"(threshold: {_DEFERRAL_ACCELERATION_WARNING} pp/week²). "
                        "The evaluation frame is progressively shifting toward "
                        "deferral — the rate of deferral growth is itself growing."
                    ),
                    severity="WARNING",
                    metric_name="deferral_acceleration_pp_per_week_sq",
                    observed=result.acceleration,
                    reference=_DEFERRAL_ACCELERATION_WARNING,
                    delta=result.acceleration - _DEFERRAL_ACCELERATION_WARNING,
                ))

            # 3. Sustained increasing trend
            if result.sustained_increasing_periods >= _DEFERRAL_SUSTAINED_CRITICAL:
                sigs.append(TransitionSignature(
                    signal_id="SUSTAINED_DEFERRAL_TREND",
                    description=(
                        f"HOLD rate increased for {result.sustained_increasing_periods} "
                        f"consecutive periods (critical: {_DEFERRAL_SUSTAINED_CRITICAL}). "
                        "Persistent unidirectional drift in deferral behaviour — "
                        "not noise, a structural trajectory."
                    ),
                    severity="CRITICAL",
                    metric_name="sustained_increasing_periods",
                    observed=float(result.sustained_increasing_periods),
                    reference=float(_DEFERRAL_SUSTAINED_CRITICAL),
                    delta=float(result.sustained_increasing_periods - _DEFERRAL_SUSTAINED_CRITICAL),
                ))
            elif result.sustained_increasing_periods >= _DEFERRAL_SUSTAINED_WARNING:
                sigs.append(TransitionSignature(
                    signal_id="SUSTAINED_DEFERRAL_TREND",
                    description=(
                        f"HOLD rate increased for {result.sustained_increasing_periods} "
                        f"consecutive periods (warning: {_DEFERRAL_SUSTAINED_WARNING}). "
                        "Early sustained deferral trend forming."
                    ),
                    severity="WARNING",
                    metric_name="sustained_increasing_periods",
                    observed=float(result.sustained_increasing_periods),
                    reference=float(_DEFERRAL_SUSTAINED_WARNING),
                    delta=float(result.sustained_increasing_periods - _DEFERRAL_SUSTAINED_WARNING),
                ))

            # 4. High oscillation — std dev flags regime instability
            if result.hold_rate_std >= _DEFERRAL_VOLATILITY_HIGH:
                sigs.append(TransitionSignature(
                    signal_id="DEFERRAL_OSCILLATION",
                    description=(
                        f"HOLD rate std dev: {result.hold_rate_std:.1f} pp "
                        f"across {len(rates)} periods "
                        f"(threshold: {_DEFERRAL_VOLATILITY_HIGH} pp). "
                        "High oscillation between enforcement and deferral — "
                        "the system is in an unstable regime, not a stable one. "
                        "Amanulla pattern: instability redistributed into "
                        "alternating latency buffers before overt failure."
                    ),
                    severity="WARNING",
                    metric_name="hold_rate_std_pp",
                    observed=result.hold_rate_std,
                    reference=_DEFERRAL_VOLATILITY_HIGH,
                    delta=result.hold_rate_std - _DEFERRAL_VOLATILITY_HIGH,
                ))

            # ── Alert level ───────────────────────────────────────────────────
            has_critical = any(s.severity == "CRITICAL" for s in sigs)
            has_warning  = any(s.severity == "WARNING"  for s in sigs)

            if has_critical:
                result.alert_level = "CRITICAL"
            elif has_warning:
                result.alert_level = "WARNING"
            else:
                result.alert_level = "OK"

            logger.info(
                f"[MCM] deferral_trajectory | domain={domain} | "
                f"periods={len(rates)} | mean_hold={result.mean_hold_rate:.1f}% | "
                f"vel={result.mean_velocity:+.2f}pp/wk | "
                f"accel={result.acceleration:+.2f}pp/wk² | "
                f"std={result.hold_rate_std:.1f}pp | "
                f"score={result.trajectory_score:.1f} | "
                f"alert={result.alert_level}"
            )

            return result

        except Exception as exc:
            result.error = str(exc)
            result.alert_level = "UNKNOWN"
            logger.warning(f"[MCM] deferral_trajectory error: {exc}")
            return result

    # ── Report Composition ─────────────────────────────────────────────────────

    def _compose_report(self, report: MetaCoherenceReport) -> None:
        """
        Aggregate sub-results into the composite MetaCoherenceReport.
        Sets composite_score, alert_level, evaluation_frame_stable,
        transition_signatures, and executive_summary.
        """
        scores:     list[float] = []
        all_sigs:   list[TransitionSignature] = []
        has_error   = False

        # Collect scores and signatures from all 4 sub-results
        all_subs = [
            report.verdict_distribution,
            report.veto_pattern,
            report.reference_legitimacy,
            report.deferral_trajectory,
        ]
        for sub in all_subs:
            if sub is None:
                continue
            if sub.error:
                has_error = True
            sigs = getattr(sub, "signatures", [])
            all_sigs.extend(sigs)

        if report.verdict_distribution and not report.verdict_distribution.error:
            scores.append(report.verdict_distribution.composite_drift)

        if report.veto_pattern and not report.veto_pattern.error:
            scores.append(report.veto_pattern.asymmetry_score)

        if report.reference_legitimacy and not report.reference_legitimacy.error:
            scores.append(report.reference_legitimacy.age_fraction * 100.0)

        if (report.deferral_trajectory
                and not report.deferral_trajectory.error
                and report.deferral_trajectory.sufficient_data):
            scores.append(report.deferral_trajectory.trajectory_score)

        # Sort signatures: CRITICAL first, then WARNING, then INFO
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        all_sigs.sort(key=lambda s: severity_order.get(s.severity, 3))
        report.transition_signatures = all_sigs

        # Composite score
        report.composite_score = round(
            sum(scores) / len(scores) if scores else 0.0, 1
        )

        # Alert level — worst of sub-results
        sub_levels = [
            getattr(r, "alert_level", "UNKNOWN")
            for r in [report.verdict_distribution, report.veto_pattern, report.reference_legitimacy]
            if r is not None
        ]
        if "CRITICAL" in sub_levels:
            report.alert_level = "CRITICAL"
        elif "WARNING" in sub_levels:
            report.alert_level = "WARNING"
        elif all(l == "OK" for l in sub_levels if l != "UNKNOWN"):
            report.alert_level = "OK"
        else:
            report.alert_level = "UNKNOWN"

        # Stability assessment
        critical_sigs = [s for s in all_sigs if s.severity == "CRITICAL"]
        warning_sigs  = [s for s in all_sigs if s.severity == "WARNING"]

        if has_error and not scores:
            report.evaluation_frame_stable = None
        elif critical_sigs:
            report.evaluation_frame_stable = False
        elif len(warning_sigs) >= 2:
            report.evaluation_frame_stable = False
        elif report.composite_score < _THRESHOLD_WARNING and not warning_sigs:
            report.evaluation_frame_stable = True
        else:
            report.evaluation_frame_stable = None  # uncertain

        # Executive summary
        report.executive_summary = self._build_executive_summary(report)

        logger.debug(
            f"[MCM] composed | domain={report.domain} | "
            f"score={report.composite_score} | "
            f"stable={report.evaluation_frame_stable} | "
            f"sigs={len(all_sigs)}"
        )

    def _build_executive_summary(self, report: MetaCoherenceReport) -> str:
        """
        Generate a human-readable executive summary appropriate for
        investor-grade documentation and partner communications.
        """
        domain  = report.domain.replace("_", " ").title()
        n_sigs  = len(report.transition_signatures)
        n_crit  = sum(1 for s in report.transition_signatures if s.severity == "CRITICAL")
        n_warn  = sum(1 for s in report.transition_signatures if s.severity == "WARNING")

        vd = report.verdict_distribution
        rl = report.reference_legitimacy

        lines: list[str] = [
            f"MCM Analysis — {domain} | {report.alert_level} | Score {report.composite_score:.1f}/100",
            "",
        ]

        if report.evaluation_frame_stable is True:
            lines.append(
                "The governance evaluation frame is operating within normal parameters. "
                "No compensatory normalization signatures detected."
            )
        elif report.evaluation_frame_stable is False:
            lines.append(
                "Second-order drift detected: the governance evaluation frame shows "
                "evidence of adapting to potentially degraded conditions. "
                "This does not indicate output-level failure, but suggests the "
                "interpretive criteria may have shifted."
            )
        else:
            lines.append("Analysis inconclusive — insufficient data or partial errors.")

        if vd and not vd.error and vd.sufficient_data:
            lines.append(
                f"\nVerdict Distribution — Ref: BLOCK {vd.ref_blocked_pct:.1f}% / "
                f"HOLD {vd.ref_held_pct:.1f}% / APPROVE {vd.ref_approved_pct:.1f}% "
                f"→ Current: BLOCK {vd.cur_blocked_pct:.1f}% / "
                f"HOLD {vd.cur_held_pct:.1f}% / APPROVE {vd.cur_approved_pct:.1f}% "
                f"| Drift score: {vd.composite_drift:.1f}"
            )

        if rl and not rl.error:
            lines.append(
                f"\nReference Legitimacy — Snapshot {rl.snapshot_id} | "
                f"Age: {rl.calibration_age_hours:.0f}h / {rl.max_age_hours:.0f}h max | "
                f"{'⚠ ANCHORING RISK' if rl.recalibration_anchoring_risk else 'Anchoring OK'}"
            )

        if n_sigs > 0:
            lines.append(
                f"\nTransition signatures detected: {n_sigs} total "
                f"({n_crit} critical, {n_warn} warning)"
            )
            for sig in report.transition_signatures[:3]:
                lines.append(f"  · [{sig.severity}] {sig.signal_id}: {sig.description[:120]}")

        return "\n".join(lines)

    # ── Utilities ──────────────────────────────────────────────────────────────

    def _extract_gate_names(self, veto_chain_raw: Any) -> list[str]:
        """
        Extract gate identifiers from a veto_chain value (JSON string or list).
        Gate names follow patterns like:
          "COHERENCE_GATE: ..."
          "SIV(CP-0): ..."
          "SHARIA_GHARAR_GATE: ..."
          "MC_SIZE_REDUCE: ..."
        """
        if not veto_chain_raw:
            return []

        try:
            if isinstance(veto_chain_raw, str):
                chain = json.loads(veto_chain_raw)
            elif isinstance(veto_chain_raw, list):
                chain = veto_chain_raw
            else:
                return []

            gate_pattern = re.compile(r"^([A-Z][A-Z0-9_()\\-]+):")
            gates: list[str] = []
            for entry in chain:
                if isinstance(entry, str):
                    m = gate_pattern.match(entry.strip())
                    if m:
                        gates.append(m.group(1))
            return gates

        except Exception:
            return []

    def _get_active_domains(self) -> list[str]:
        """Return list of domains that have active AVM snapshots."""
        if not self._db_url:
            return []
        try:
            import psycopg
            conn = psycopg.connect(self._db_url)
            cur  = conn.cursor()
            cur.execute(
                "SELECT domain FROM avm_calibration_snapshots WHERE is_active = true ORDER BY domain"
            )
            domains = [r[0] for r in cur.fetchall()]
            conn.close()
            return domains
        except Exception as exc:
            logger.warning(f"[MCM] _get_active_domains failed: {exc}")
            return []

    # ── ADR-118: Auto-Remediation ──────────────────────────────────────────────

    def auto_remediate(self, report: "MetaCoherenceReport") -> bool:
        """
        ADR-118: Automated remediation when MCM detects a CRITICAL alert.

        Remediation policy (ordered, first-applicable wins):
          1. RECALIBRATION_ANCHORING — force AVM recalibration via
             auto_recalibrate_stale_domains() with a short recalib_interval=0h.
          2. BLOCK_RATE_COLLAPSE — tighten checkpoint thresholds by 10% on the
             affected domain, recorded to mcm_remediation_log.
          3. DEFAULT — log the alert and flag the domain for human review.

        Rate-limit: at most 1 auto-remediation per domain per 6 hours.

        Returns:
            True if a remediation action was taken, False if rate-limited or skipped.
        """
        domain = report.domain

        if not self._db_url:
            logger.warning(f"[MCM.REMEDIATE] No DB URL — cannot persist remediation for {domain}")
            return False

        try:
            import psycopg
            conn = psycopg.connect(self._db_url)
            cur  = conn.cursor()

            # ── Rate-limit: 1 remediation per domain per 6h ────────────────────
            cur.execute(
                """
                SELECT COUNT(*) FROM mcm_remediation_log
                WHERE domain = %s AND triggered_at > NOW() - INTERVAL '6 hours'
                """,
                (domain,),
            )
            row = cur.fetchone()
            if row and int(row[0]) > 0:
                logger.info(f"[MCM.REMEDIATE] {domain}: rate-limited (1 per 6h) — skipping")
                conn.close()
                return False

            # ── ADR-144: Anti-loop guard ────────────────────────────────────────
            # Check before any action is determined or executed. If a MCM→MCM
            # feedback loop is detected (≥2 auto-remediations within the
            # anti-loop window), escalate to human instead of executing.
            loop_detected = False
            try:
                from omnix_core.governance.auto_modification_guard import is_auto_loop
                loop_detected = is_auto_loop(domain, self._db_url)
            except Exception as _loop_exc:
                logger.warning(f"[MCM.REMEDIATE] {domain}: anti-loop check failed — {_loop_exc}")

            if loop_detected:
                import uuid as _uuid
                loop_alert_id = f"MCM-LOOP-{domain.upper()}-{_uuid.uuid4().hex[:8].upper()}"
                logger.error(
                    f"[MCM.REMEDIATE] ⛔ LOOP DETECTED: domain={domain} — "
                    f"auto-remediation BLOCKED, escalating to human. "
                    f"loop_alert_id={loop_alert_id}"
                )
                # Write LOOP_DETECTED entry to mcm_remediation_log
                cur.execute(
                    """
                    INSERT INTO mcm_remediation_log
                        (mcm_alert_id, domain, alert_pattern, action_taken,
                         pre_remediation_state, outcome, loop_detected)
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, TRUE)
                    """,
                    (
                        loop_alert_id, domain, "LOOP_DETECTED",
                        "ESCALATE_HUMAN",
                        json.dumps({"composite_score": report.composite_score,
                                    "alert_level": report.alert_level,
                                    "loop_guard": "ADR-144"}),
                        "LOOP_BLOCKED",
                    ),
                )
                conn.commit()
                conn.close()

                # Telegram notification with explicit loop context
                try:
                    import os as _os
                    bot_token = _os.environ.get("TELEGRAM_BOT_TOKEN", "")
                    admin_id  = _os.environ.get("TELEGRAM_ADMIN_USER_ID", "")
                    if bot_token and admin_id:
                        import urllib.request as _req
                        msg = (
                            f"⛔ MCM LOOP DETECTED — HUMAN REVIEW REQUIRED\n"
                            f"Domain: {domain}\n"
                            f"Loop Alert ID: {loop_alert_id}\n"
                            f"Score: {report.composite_score:.1f}/100\n"
                            f"Reason: ≥2 auto-remediations within anti-loop window.\n"
                            f"Action: BLOCKED — auto-remediation suspended for this domain.\n"
                            f"ADR-144 §6 anti-loop guard triggered."
                        )
                        payload = json.dumps({"chat_id": admin_id, "text": msg}).encode()
                        _req.urlopen(
                            f"https://api.telegram.org/bot{bot_token}/sendMessage",
                            data=payload,
                            timeout=5,
                        )
                except Exception:
                    pass

                return False

            # ── Determine remediation action ───────────────────────────────────
            sig_ids = {s.signal_id for s in report.transition_signatures}
            rl      = report.reference_legitimacy

            if rl and rl.recalibration_anchoring_risk:
                action   = "FORCE_AVM_RECALIBRATION"
                pattern  = "RECALIBRATION_ANCHORING_RISK"
            elif "BLOCK_RATE_COLLAPSE" in sig_ids:
                action   = "TIGHTEN_CHECKPOINT_THRESHOLDS"
                pattern  = "BLOCK_RATE_COLLAPSE"
            else:
                action   = "FLAG_FOR_HUMAN_REVIEW"
                pattern  = "CRITICAL_ALERT_DEFAULT"

            pre_state = {
                "composite_score":      report.composite_score,
                "alert_level":          report.alert_level,
                "transition_signatures": [s.signal_id for s in report.transition_signatures],
                "evaluation_frame_stable": report.evaluation_frame_stable,
            }

            # ── Log to mcm_remediation_log ─────────────────────────────────────
            import uuid as _uuid
            alert_id = f"MCM-{domain.upper()}-{_uuid.uuid4().hex[:8].upper()}"
            cur.execute(
                """
                INSERT INTO mcm_remediation_log
                    (mcm_alert_id, domain, alert_pattern, action_taken,
                     pre_remediation_state, outcome)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                """,
                (alert_id, domain, pattern, action,
                 json.dumps(pre_state), "IN_PROGRESS"),
            )
            conn.commit()

            logger.warning(
                f"[MCM.REMEDIATE] ⚡ {domain}: CRITICAL alert — "
                f"action={action} pattern={pattern} alert_id={alert_id}"
            )

            # ── Execute remediation action ─────────────────────────────────────
            outcome = "UNKNOWN"
            if action == "FORCE_AVM_RECALIBRATION":
                try:
                    from omnix_core.governance.assumption_validity_monitor import get_avm_instance
                    avm = get_avm_instance()
                    recalibrated = avm.auto_recalibrate_stale_domains(
                        recalib_interval_hours=0.0,
                    )
                    outcome = f"RECALIBRATED:{','.join(recalibrated) if recalibrated else 'NONE'}"
                    logger.info(f"[MCM.REMEDIATE] {domain}: AVM recalibration result — {outcome}")
                except Exception as exc:
                    outcome = f"FAILED:{exc}"
                    logger.error(f"[MCM.REMEDIATE] {domain}: AVM recalibration error — {exc}")

            elif action == "TIGHTEN_CHECKPOINT_THRESHOLDS":
                # ADR-144: route through deploy_optimized_thresholds() so ALL
                # AMG safeguards apply (cumulative cap, diff proof, approval gate).
                # Direct save_calibration_snapshot() bypasses the guard and is
                # prohibited for automated modifications.
                try:
                    from omnix_core.governance.assumption_validity_monitor import get_avm_instance
                    avm = get_avm_instance()
                    snap = avm.load_snapshot(domain)
                    if snap and snap.checkpoint_thresholds:
                        tightened = {
                            k: round(v * 0.90, 4)
                            for k, v in snap.checkpoint_thresholds.items()
                        }
                        deployed = avm.deploy_optimized_thresholds(
                            domain=domain,
                            optimized_thresholds=tightened,
                            db_url=self._db_url,
                            source="MCM_AUTO_TIGHTEN",
                        )
                        if deployed:
                            outcome = f"THRESHOLDS_TIGHTENED:{len(tightened)}_checkpoints|AMG_APPROVED"
                        else:
                            outcome = "HELD_OR_BLOCKED_BY_AMG"
                        logger.info(f"[MCM.REMEDIATE] {domain}: tighten via AMG — {outcome}")
                    else:
                        outcome = "SKIPPED:no_snapshot_or_thresholds"
                except Exception as exc:
                    outcome = f"FAILED:{exc}"
                    logger.error(f"[MCM.REMEDIATE] {domain}: threshold tighten error — {exc}")

            else:
                outcome = "FLAGGED_FOR_HUMAN_REVIEW"
                logger.warning(
                    f"[MCM.REMEDIATE] {domain}: flagged for human review — "
                    f"score={report.composite_score:.1f} sigs={len(report.transition_signatures)}"
                )

            # ── Update outcome in remediation log ──────────────────────────────
            cur.execute(
                """
                UPDATE mcm_remediation_log
                   SET outcome = %s, resolved_at = NOW()
                 WHERE mcm_alert_id = %s
                """,
                (outcome, alert_id),
            )
            conn.commit()
            conn.close()

            # ── Telegram notification ──────────────────────────────────────────
            try:
                import os as _os
                bot_token = _os.environ.get("TELEGRAM_BOT_TOKEN", "")
                admin_id  = _os.environ.get("TELEGRAM_ADMIN_USER_ID", "")
                if bot_token and admin_id:
                    import urllib.request as _req
                    msg = (
                        f"⚠️ MCM AUTO-REMEDIATION\n"
                        f"Domain: {domain}\n"
                        f"Alert ID: {alert_id}\n"
                        f"Pattern: {pattern}\n"
                        f"Action: {action}\n"
                        f"Outcome: {outcome}\n"
                        f"Score: {report.composite_score:.1f}/100"
                    )
                    payload = json.dumps({
                        "chat_id": admin_id,
                        "text": msg,
                    }).encode()
                    _req.urlopen(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        data=payload,
                        timeout=5,
                    )
            except Exception:
                pass

            return True

        except Exception as exc:
            logger.error(f"[MCM.REMEDIATE] {domain}: auto_remediate failed — {exc}")
            return False


# ── Module-level convenience ───────────────────────────────────────────────────

def get_meta_coherence_monitor() -> MetaCoherenceMonitor:
    """Return a MetaCoherenceMonitor instance using the default DB URL."""
    import os
    return MetaCoherenceMonitor(db_url=os.environ.get("OMNIX_DB_URL", ""))
