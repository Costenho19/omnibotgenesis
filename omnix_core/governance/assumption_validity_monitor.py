"""
OMNIX Assumption Validity Monitor (AVM)
ADR-064: Assumption Validity Monitor — Calibration Drift Detection
ADR-075: Non-Finite Signal Guard — Fail-Closed under NaN/Inf inputs

Solves the core critique of governance under Knightian uncertainty:
OMNIX can certify a decision correctly given its calibrated parameters,
but those parameters may have been calibrated under conditions that no
longer hold. This module detects when the gap between calibration
conditions and current conditions has grown too wide to trust any
certification issued by the pipeline.

Architecture position:
    Signals → AVM (ADR-064) → CAG (ADR-050) → 11 Checkpoints → TIE (ADR-053) → Decision
              [STALE_BLOCK / NON_FINITE_BLOCK / DRIFT_BLOCK]

Key principle:
    A governance receipt is only as valid as the assumptions it was
    certified under. If those assumptions have drifted beyond a tolerance
    threshold, the pipeline must refuse to certify — regardless of whether
    the incoming signals would otherwise pass all checkpoints.

Blocking policy (strictest wins, evaluated in this order):
    1. NON_FINITE_SIGNAL  — Any NaN/Inf in input signals → is_valid=False
                            Reason: Python NaN > threshold = False → silent PASS.
                            OMNIX blocks explicitly instead. (ADR-075 §4.3)
    2. CRITICAL_STALE     — Snapshot age > critical_age_hours → is_valid=False
                            Reason: stale assumptions invalidate any certification.
    3. DRIFT_BLOCK        — Weighted drift > effective_threshold → is_valid=False
                            Reason: live conditions diverged from calibration baseline.
    4. PASS               — All checks pass → is_valid=True, pass_through=False (certified)

pass_through=True semantics (IMPORTANT for integrators):
    pass_through=True means the AVM had NO BASELINE to compare against.
    It does NOT mean the decision is certified. Downstream code MUST treat
    pass_through=True as NON_CERTIFIED — not as APPROVED.
    Valid pass_through states: AVM_DISABLED, NO_BASELINE.

Parameter Versioning:
    Every calibration snapshot receives a unique version ID embedded in
    the resulting governance receipts. If a snapshot is later invalidated,
    all receipts issued under it can be traced and flagged.

Storage: JSON snapshots in `avm_snapshots/` directory (one per domain).
         Falls back to in-memory storage when filesystem unavailable.

Fail-safe policy (ADR-075 §4.4):
    Internal AVM exceptions propagate to the caller. The pipeline-level
    exception handler must treat any AVM exception as BLOCK (fail-closed),
    never as PASS. Exceptions do NOT produce pass_through=True.

Enabled via: AVM_ENABLED env var (default: true).

Responds directly to:
    - Ioana V. (PhD Decision Architect): "Who detects when underlying
      conditions change?"
    - Jennifer's Knightian uncertainty critique: "What happens when OMNIX
      certifies under assumptions that are no longer valid?"
    - Forensic Audit Ronda 3 (2026-04-09): NaN bypass confirmed and closed.

Harold Nunes — OMNIX Decision Governance Infrastructure
Build 6.6.0 | ADR-064 + ADR-075 | April 2026
"""

from __future__ import annotations

import json
import logging
import math
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("OMNIX.AVM")

# ── Configuration ──────────────────────────────────────────────────────────────

AVM_ENABLED_DEFAULT = True
AVM_SNAPSHOTS_DIR = Path("avm_snapshots")

# Maximum weighted drift (0-100) before the pipeline is blocked.
# At 35: one signal can deviate by ~35 points without triggering.
# Combined cross-signal drift at 35 triggers fail-closed.
AVM_DRIFT_THRESHOLD_DEFAULT = 35.0

# Maximum calibration age in hours before a stale-age warning is issued.
# Beyond this, drift threshold is tightened automatically.
AVM_MAX_AGE_HOURS_DEFAULT = 168.0  # 7 days

# If calibration is older than this, treat as critical stale (block regardless of drift).
AVM_CRITICAL_AGE_HOURS_DEFAULT = 720.0  # 30 days

# ── Canonical signal schema (ADR-076) ──────────────────────────────────────────
# SINGLE SOURCE OF TRUTH for all AVM signal key names.
# All calibration snapshots, simulators, and DB tables MUST use these exact keys.
# Changing a key here REQUIRES updating: save_calibration_snapshot calls,
# all *_calibration.json files, and DB column names.
# See: docs/adr/ADR-076-avm-signal-schema-standardization.md
SIGNAL_WEIGHTS: dict[str, float] = {
    "probability_score":  0.25,
    "signal_coherence":   0.25,
    "risk_exposure":      0.20,
    "stress_resilience":  0.15,
    "trend_persistence":  0.10,
    "logic_consistency":  0.05,
}

# SIGNAL_SCHEMA: canonical ordered list of signal keys, derived from SIGNAL_WEIGHTS.
# Import this constant anywhere signal keys are needed — never hardcode the list.
SIGNAL_SCHEMA: list[str] = list(SIGNAL_WEIGHTS.keys())
_SIGNAL_SCHEMA_SET: frozenset[str] = frozenset(SIGNAL_SCHEMA)


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class CalibrationSnapshot:
    """
    A point-in-time snapshot of the conditions under which the
    governance pipeline was calibrated for a given domain.

    This snapshot is the "ground truth" against which subsequent
    evaluations are compared. If the live system diverges too far
    from these conditions, the AVM triggers a fail-closed response.
    """
    snapshot_id: str
    parameter_version: str
    domain: str
    calibrated_at: str            # ISO 8601 UTC
    calibrated_at_epoch: float    # Unix timestamp (for age computation)
    baseline_signals: dict[str, float]    # Signal values at calibration time
    checkpoint_thresholds: dict[str, float]   # CP threshold values at calibration
    drift_threshold: float        # Max drift before fail-closed
    max_age_hours: float          # Max age before stale warning
    description: str
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CalibrationSnapshot":
        return cls(**data)

    def age_hours(self) -> float:
        """Hours since this snapshot was calibrated."""
        now_epoch = datetime.now(timezone.utc).timestamp()
        return (now_epoch - self.calibrated_at_epoch) / 3600.0


@dataclass
class AVMResult:
    """
    Result of an Assumption Validity check.

    If is_valid=False, the pipeline should refuse to certify the
    incoming decision — regardless of checkpoint scores.
    """
    is_valid: bool
    snapshot_id: str
    parameter_version: str
    drift_score: float             # 0-100; higher = more drift = stalier assumptions
    drift_components: dict[str, float]   # Per-signal drift breakdown
    age_hours: float               # Age of calibration snapshot in hours
    drift_threshold: float         # Threshold used in this evaluation
    block_reason: str | None       # If is_valid=False, human-readable reason
    warnings: list[str]            # Non-blocking notices
    pass_through: bool = False     # True if AVM is disabled or has no snapshot
    probe_report: Optional[Any] = field(default=None)              # OMNIX DIFFERENTIATOR: GTPD
    structural_shift_report: Optional[Any] = field(default=None)   # OMNIX DIFFERENTIATOR: SSD (ADR-175)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "is_valid": self.is_valid,
            "snapshot_id": self.snapshot_id,
            "parameter_version": self.parameter_version,
            "drift_score": round(self.drift_score, 2),
            "drift_components": {k: round(v, 2) for k, v in self.drift_components.items()},
            "age_hours": round(self.age_hours, 1),
            "drift_threshold": self.drift_threshold,
            "block_reason": self.block_reason,
            "warnings": self.warnings,
            "pass_through": self.pass_through,
        }
        if self.probe_report is not None:
            d["probe_report"] = self.probe_report
        if self.structural_shift_report is not None:
            d["structural_shift_report"] = self.structural_shift_report
        return d


# ── OMNIX DIFFERENTIATOR: Governance Threshold Probe Detection (GTPD) ──────────
#
# GOVERNANCE RISK SOLVED:
#   An adversary can reverse-engineer the AVM's approval boundary by submitting
#   many slightly-different evaluation requests and observing which ones pass
#   vs. block.  Once they know the exact threshold, they can craft inputs that
#   always just barely pass — defeating the governance gate without triggering
#   any alarm.  This is a structural side-channel attack on governance integrity.
#   No other platform detects this because no other platform records evaluation
#   patterns across requests for the same domain.
#
# VERIFIABLE EVIDENCE:
#   ThresholdProbeReport is embedded in AVMResult and surfaced in governance
#   receipts.  A CONFIRMED verdict means ≥5 evaluations clustered within ±30%
#   of the drift threshold — a pattern that is statistically improbable by chance
#   and matches known threshold-probing attack profiles.
#
# INSTITUTIONAL EXPLANATION:
#   Imagine someone repeatedly knocking on a vault door at slightly different
#   strengths to find the exact force needed to open it.  GTPD detects when
#   someone is doing exactly that to OMNIX's governance gate.
#
# ADR-064 extension | OMNIX-GTPD-001

@dataclass
class ThresholdProbeReport:
    """
    Result of Governance Threshold Probe Detection for one AVM evaluation.

    probe_score: 0–100 (higher = more suspicious).
    probe_verdict: INSUFFICIENT_DATA | CLEAN | SUSPECTED | CONFIRMED
      - INSUFFICIENT_DATA: fewer than 3 evaluations in history window
      - CLEAN:             no clustering near threshold (< 20% of evals within margin)
      - SUSPECTED:         20–60% of recent evals cluster near threshold AND ≥3 evals
      - CONFIRMED:         >60% of recent evals cluster near threshold AND ≥5 evals
    """
    probe_id: str
    domain: str
    probe_score: float
    clustering_coefficient: float
    evaluations_analyzed: int
    evaluations_near_threshold: int
    threshold_margin: float
    probe_verdict: str
    detected_at: str

    def to_dict(self) -> dict:
        return {
            "probe_id":                    self.probe_id,
            "domain":                      self.domain,
            "probe_score":                 self.probe_score,
            "clustering_coefficient":      self.clustering_coefficient,
            "evaluations_analyzed":        self.evaluations_analyzed,
            "evaluations_near_threshold":  self.evaluations_near_threshold,
            "threshold_margin":            self.threshold_margin,
            "probe_verdict":               self.probe_verdict,
            "detected_at":                 self.detected_at,
        }


# ── OMNIX DIFFERENTIATOR: Structural Shift Detector (SSD) ─────────────────────
#
# GOVERNANCE RISK SOLVED:
#   The AVM detects THAT a domain has drifted — but not WHETHER the drift
#   represents a temporary excursion (sustained but recoverable) or a permanent
#   change in the domain's signal topology (structural, requiring human review).
#   This distinction is operationally critical: auto-recalibrating under a
#   structural shift embeds new, incoherent baselines that mask the root cause.
#   No other governance platform distinguishes these two deterioration modes
#   at the component-composition level.
#
# ALGORITHM — Component Rank Stability Index (CRSI):
#   After each evaluate(), the top-K drift components (by magnitude) are recorded.
#   CRSI is the position-weighted Jaccard overlap between the current cycle's
#   top-K ranking and the historical top-K ranking averaged over the last M cycles.
#   Position weights: rank-1 = K, rank-2 = K-1, ..., rank-K = 1 (linear decay).
#   CRSI ∈ [0, 1]: 1.0 = identical rank topology; 0.0 = completely different.
#
#   Classification thresholds:
#     CRSI >= SSD_INSTABILITY_THRESHOLD (0.70) → STABLE
#     SSD_STRUCTURAL_THRESHOLD (0.50) <= CRSI < 0.70 → DRIFT_WITH_INSTABILITY
#     CRSI < SSD_STRUCTURAL_THRESHOLD (0.50) AND >= SSD_MIN_CYCLES → STRUCTURAL_SHIFT
#     < SSD_MIN_CYCLES history entries → INSUFFICIENT_DATA
#
# SSD INVARIANTS (ADR-175):
#   SSD-INV-001: shift_class=STRUCTURAL_SHIFT blocks auto-recalibration
#                independently of and in addition to AGV-INV-006
#   SSD-INV-002: Component history ring buffer is append-only within its window;
#                no cycle entry may be modified or deleted retroactively
#   SSD-INV-003: STRUCTURAL_SHIFT verdict requires >= SSD_MIN_CYCLES cycles of
#                component history for that domain (prevents noise on cold start)
#
# VERIFIABLE EVIDENCE:
#   StructuralShiftReport is embedded in AVMResult and propagated into PVRs.
#   STRUCTURAL_SHIFT carries ssd_id, crsi, emerged_components, receded_components —
#   traceable forensic evidence of when the domain topology changed.
#
# OMNIX-SSD-001 | ADR-175

_SSD_HISTORY_SIZE          = 20    # max component snapshots retained per domain
_SSD_HISTORY_LOCK          = threading.Lock()
_component_history: dict[str, list[dict[str, float]]] = {}

SSD_TOP_K_COMPONENTS       = 3     # compare top-K components by drift magnitude
SSD_MIN_CYCLES             = 5     # minimum history cycles before STRUCTURAL_SHIFT
SSD_STRUCTURAL_THRESHOLD   = 0.50  # CRSI below this → STRUCTURAL_SHIFT
SSD_INSTABILITY_THRESHOLD  = 0.70  # CRSI below this → DRIFT_WITH_INSTABILITY


@dataclass
class StructuralShiftReport:
    """
    OMNIX DIFFERENTIATOR — Structural Shift Detector (SSD) report.

    Produced once per AVM evaluate() call. Classifies whether observed drift
    represents a sustained excursion (stable topology, high score) or a
    structural change in the domain's signal composition (topology itself
    has shifted, making the current calibration frame potentially obsolete).

    shift_class values:
      INSUFFICIENT_DATA   — fewer than SSD_MIN_CYCLES history entries; no verdict
      STABLE              — top-K component ranking is stable (CRSI >= 0.70)
      DRIFT_WITH_INSTABILITY — topology shifting but not conclusively structural
      STRUCTURAL_SHIFT    — component rank topology has changed significantly
                            (CRSI < 0.50 with >= SSD_MIN_CYCLES evidence cycles)

    crsi: Component Rank Stability Index (0–1). Weighted Jaccard overlap
          between current top-K components and historical top-K. Position-
          weighted: rank-1 contributes more than rank-K.

    emerged_components: signals that entered the top-K this cycle but were NOT
                        consistently in top-K historically. Signals a new
                        driver of governance instability.

    receded_components: signals that were consistently top-K historically but
                        are no longer dominant this cycle. Signals a previously
                        important driver has quieted.

    ADR-175 | OMNIX-SSD-001
    """
    ssd_id: str
    domain: str
    shift_class: str           # INSUFFICIENT_DATA | STABLE | DRIFT_WITH_INSTABILITY | STRUCTURAL_SHIFT
    crsi: float                # Component Rank Stability Index (0–1)
    cycles_analyzed: int       # history entries used in CRSI computation
    dominant_components_current: list   # top-K by drift magnitude this cycle
    dominant_components_baseline: list  # consensus top-K across history
    emerged_components: list           # new to top-K this cycle
    receded_components: list           # dropped from top-K this cycle
    detected_at: str

    def to_dict(self) -> dict:
        return {
            "ssd_id":                       self.ssd_id,
            "domain":                       self.domain,
            "shift_class":                  self.shift_class,
            "crsi":                         round(self.crsi, 4),
            "cycles_analyzed":              self.cycles_analyzed,
            "dominant_components_current":  self.dominant_components_current,
            "dominant_components_baseline": self.dominant_components_baseline,
            "emerged_components":           self.emerged_components,
            "receded_components":           self.receded_components,
            "detected_at":                  self.detected_at,
        }


# Module-level GTPD drift history ring buffer (thread-safe, per domain)
_GTPD_HISTORY_SIZE = 50
_GTPD_HISTORY_LOCK = threading.Lock()
_gtpd_drift_history: dict[str, list[float]] = {}


# ── Core Monitor ───────────────────────────────────────────────────────────────

class AssumptionValidityMonitor:
    """
    Detects when the assumptions embedded in OMNIX's governance pipeline
    have drifted too far from the conditions that produced them.

    Lifecycle:
        1. At calibration time: call save_calibration_snapshot() with the
           current baseline signals and checkpoint thresholds.
        2. Before every governance cycle: call evaluate() with live signals.
           - If AVM.is_valid=False → the pipeline must return BLOCKED.
           - The drift score and parameter_version are embedded in receipts.

    Storage:
        Snapshots are persisted to avm_snapshots/{domain}_calibration.json.
        Falls back to in-memory dict if the filesystem is unavailable.
    """

    def __init__(
        self,
        drift_threshold: float = AVM_DRIFT_THRESHOLD_DEFAULT,
        max_age_hours: float = AVM_MAX_AGE_HOURS_DEFAULT,
        critical_age_hours: float = AVM_CRITICAL_AGE_HOURS_DEFAULT,
        snapshots_dir: Path | None = None,
    ):
        self.drift_threshold = drift_threshold
        self.max_age_hours = max_age_hours
        self.critical_age_hours = critical_age_hours
        self._snapshots_dir = snapshots_dir or AVM_SNAPSHOTS_DIR
        self._memory_store: dict[str, CalibrationSnapshot] = {}
        # ADR-120: cache of last-seen signals per domain — used by auto-recalibrator
        self._last_seen_signals: dict[str, dict[str, float]] = {}
        self._last_seen_lock = threading.Lock()
        self._ensure_snapshots_dir()

    def _ensure_snapshots_dir(self) -> None:
        try:
            self._snapshots_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"[AVM] Cannot create snapshots dir: {e} — using in-memory only")

    def _snapshot_path(self, domain: str) -> Path:
        safe_domain = domain.replace("/", "_").replace("\\", "_").replace(" ", "_")
        return self._snapshots_dir / f"{safe_domain}_calibration.json"

    # ── Snapshot management ────────────────────────────────────────────────────

    def save_calibration_snapshot(
        self,
        domain: str,
        baseline_signals: dict[str, float],
        checkpoint_thresholds: dict[str, float] | None = None,
        description: str = "Calibration snapshot",
        tags: list[str] | None = None,
    ) -> CalibrationSnapshot:
        """
        Save a calibration snapshot for the given domain.

        Call this whenever the governance pipeline is recalibrated —
        i.e., when checkpoint thresholds are adjusted or the system
        is deployed to a new environment or market context.

        Args:
            domain: Domain identifier (e.g. "trading", "credit", "insurance")
            baseline_signals: The normalized signals (0-100) at calibration time.
                              These represent "healthy" reference conditions.
            checkpoint_thresholds: Optional map of CP-N → threshold values.
            description: Human-readable description of why recalibration occurred.
            tags: Optional list of tags (e.g. ["post-regime-change", "v2.0"])

        Returns:
            The saved CalibrationSnapshot.

        Raises:
            ValueError: If baseline_signals keys do not match SIGNAL_SCHEMA (ADR-076).
        """
        # ── ADR-076: Schema validation (fail-fast) ──────────────────────────────
        provided_keys = frozenset(baseline_signals.keys())
        if provided_keys != _SIGNAL_SCHEMA_SET:
            missing  = sorted(_SIGNAL_SCHEMA_SET - provided_keys)
            extra    = sorted(provided_keys - _SIGNAL_SCHEMA_SET)
            msg = (
                f"[AVM] SCHEMA_VIOLATION — domain={domain} | "
                f"baseline_signals keys do not match SIGNAL_SCHEMA. "
                f"Missing={missing} | Extra={extra}. "
                f"Required keys: {sorted(SIGNAL_SCHEMA)}. "
                "See ADR-076: AVM Signal Schema Standardization."
            )
            logger.error(msg)
            raise ValueError(msg)
        # ───────────────────────────────────────────────────────────────────────

        now = datetime.now(timezone.utc)
        unique_id = uuid.uuid4().hex[:10].upper()
        snapshot = CalibrationSnapshot(
            snapshot_id=f"AVM-{unique_id}",
            parameter_version=f"1.{unique_id.lower()}",
            domain=domain,
            calibrated_at=now.isoformat(),
            calibrated_at_epoch=now.timestamp(),
            baseline_signals={k: float(v) for k, v in baseline_signals.items()},
            checkpoint_thresholds=checkpoint_thresholds or {},
            drift_threshold=self.drift_threshold,
            max_age_hours=self.max_age_hours,
            description=description,
            tags=tags or [],
        )

        self._memory_store[domain] = snapshot

        try:
            path = self._snapshot_path(domain)
            with open(path, "w") as f:
                json.dump(snapshot.to_dict(), f, indent=2)
            logger.info(
                f"[AVM] Snapshot saved — domain={domain} | "
                f"id={snapshot.snapshot_id} | version={snapshot.parameter_version}"
            )
        except Exception as e:
            logger.warning(f"[AVM] Could not persist snapshot to disk: {e} — in-memory only")

        # ── Version history: every recalibration appends an immutable entry ────
        # This ensures all previous baselines are traceable and snapshots cannot
        # be silently overwritten without audit trail.
        try:
            history_path = AVM_SNAPSHOTS_DIR / f"{domain}_history.jsonl"
            history_entry = {
                "snapshot_id":      snapshot.snapshot_id,
                "parameter_version": snapshot.parameter_version,
                "domain":           snapshot.domain,
                "calibrated_at":    snapshot.calibrated_at,
                "description":      snapshot.description,
                "tags":             snapshot.tags,
                "baseline_signals": snapshot.baseline_signals,
            }
            with open(history_path, "a") as hf:
                hf.write(json.dumps(history_entry) + "\n")
            logger.info(
                f"[AVM] History entry appended — domain={domain} | "
                f"id={snapshot.snapshot_id} | history_file={history_path}"
            )
        except Exception as he:
            logger.warning(f"[AVM] Could not append to history log: {he}")

        return snapshot

    def load_snapshot(self, domain: str) -> CalibrationSnapshot | None:
        """
        Load the calibration snapshot for the given domain.

        Priority: in-memory → disk. Returns None if no snapshot exists.
        """
        if domain in self._memory_store:
            return self._memory_store[domain]

        path = self._snapshot_path(domain)
        if not path.exists():
            return None

        try:
            with open(path) as f:
                data = json.load(f)
            snapshot = CalibrationSnapshot.from_dict(data)

            # ── ADR-076: Schema validation on disk load ──────────────────────────
            loaded_keys = frozenset(snapshot.baseline_signals.keys())
            if loaded_keys and loaded_keys != _SIGNAL_SCHEMA_SET:
                missing = sorted(_SIGNAL_SCHEMA_SET - loaded_keys)
                extra   = sorted(loaded_keys - _SIGNAL_SCHEMA_SET)
                logger.error(
                    f"[AVM] SCHEMA_MISMATCH on disk load — domain={domain} | "
                    f"snapshot={snapshot.snapshot_id} | "
                    f"missing={missing} | extra={extra} | "
                    "Snapshot rejected — drift detection will not arm for this domain. "
                    "Recalibrate with SIGNAL_SCHEMA keys (ADR-076)."
                )
                return None
            # ────────────────────────────────────────────────────────────────────

            self._memory_store[domain] = snapshot
            return snapshot
        except Exception as e:
            logger.warning(f"[AVM] Could not load snapshot for domain={domain}: {e}")
            return None

    def invalidate_snapshot(self, domain: str) -> bool:
        """
        Invalidate the calibration snapshot for a domain.

        After invalidation, the AVM will pass-through (no baseline to compare against),
        but a warning will be logged. Call save_calibration_snapshot() to restore.

        Returns True if a snapshot was removed, False if none existed.
        """
        existed = domain in self._memory_store
        self._memory_store.pop(domain, None)

        path = self._snapshot_path(domain)
        if path.exists():
            try:
                path.rename(path.with_suffix(".json.invalidated"))
                existed = True
            except Exception as e:
                logger.warning(f"[AVM] Could not rename snapshot file: {e}")

        if existed:
            logger.warning(f"[AVM] Snapshot INVALIDATED for domain={domain}")
        return existed

    # ── OMNIX DIFFERENTIATOR: SSD methods (ADR-175) ────────────────────────────

    def _update_component_history(self, domain: str, drift_components: dict[str, float]) -> None:
        """
        Append current drift component snapshot to the SSD ring buffer (SSD-INV-002).
        The buffer is append-only within its window — no entry is modified retroactively.
        """
        if not drift_components:
            return
        with _SSD_HISTORY_LOCK:
            if domain not in _component_history:
                _component_history[domain] = []
            _component_history[domain].append(dict(drift_components))
            if len(_component_history[domain]) > _SSD_HISTORY_SIZE:
                _component_history[domain].pop(0)

    def _detect_structural_shift(
        self,
        domain: str,
        drift_components: dict[str, float],
    ) -> "StructuralShiftReport":
        """
        OMNIX DIFFERENTIATOR — Structural Shift Detector (SSD).

        Computes the Component Rank Stability Index (CRSI) for the domain by
        comparing the current cycle's top-K drift components against the
        historical component rankings stored in the ring buffer.

        CRSI Algorithm (position-weighted Jaccard):
          1. Rank current drift_components descending by value → top-K list
          2. For each history entry, rank components descending → historical top-K
          3. Overlap = sum of position_weights[i] for each rank-i component in
             current_top_K that also appears anywhere in the historical top-K
          4. Position weights: rank-1 = K, rank-2 = K-1, ..., rank-K = 1
          5. CRSI_entry = overlap / max_possible_overlap
          6. CRSI = mean(CRSI_entry) across all history entries

        Classification (SSD-INV-003):
          INSUFFICIENT_DATA   — fewer than SSD_MIN_CYCLES history entries
          STABLE              — CRSI >= SSD_INSTABILITY_THRESHOLD (0.70)
          DRIFT_WITH_INSTABILITY — CRSI in [SSD_STRUCTURAL_THRESHOLD, 0.70)
          STRUCTURAL_SHIFT    — CRSI < SSD_STRUCTURAL_THRESHOLD (0.50)

        Returns StructuralShiftReport (always — never raises).
        """
        ssd_id  = f"SSD-{uuid.uuid4().hex[:10].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()
        k       = SSD_TOP_K_COMPONENTS

        if not drift_components:
            return StructuralShiftReport(
                ssd_id=ssd_id, domain=domain,
                shift_class="INSUFFICIENT_DATA", crsi=0.0,
                cycles_analyzed=0,
                dominant_components_current=[],
                dominant_components_baseline=[],
                emerged_components=[], receded_components=[],
                detected_at=now_iso,
            )

        current_ranked: list[str] = [
            sig for sig, _ in sorted(
                drift_components.items(), key=lambda x: x[1], reverse=True
            )
        ][:k]

        with _SSD_HISTORY_LOCK:
            history = list(_component_history.get(domain, []))

        if len(history) < SSD_MIN_CYCLES:
            return StructuralShiftReport(
                ssd_id=ssd_id, domain=domain,
                shift_class="INSUFFICIENT_DATA", crsi=0.0,
                cycles_analyzed=len(history),
                dominant_components_current=current_ranked,
                dominant_components_baseline=[],
                emerged_components=[], receded_components=[],
                detected_at=now_iso,
            )

        # Position weights: rank-1 = k, rank-2 = k-1, ..., rank-k = 1
        position_weights = {i: float(k - i) for i in range(k)}
        max_overlap = sum(position_weights.values())

        overlap_scores: list[float] = []
        component_freq: dict[str, int] = {}

        for hist_entry in history:
            hist_ranked: list[str] = [
                sig for sig, _ in sorted(
                    hist_entry.items(), key=lambda x: x[1], reverse=True
                )
            ][:k]

            hist_set = set(hist_ranked)
            overlap = sum(
                position_weights[i]
                for i, sig in enumerate(current_ranked)
                if i < k and sig in hist_set
            )
            overlap_scores.append(overlap / max_overlap if max_overlap > 0 else 0.0)

            for sig in hist_ranked:
                component_freq[sig] = component_freq.get(sig, 0) + 1

        crsi = round(
            sum(overlap_scores) / len(overlap_scores), 4
        ) if overlap_scores else 0.0

        # Baseline dominant: components in top-K for ≥ 50% of history cycles
        n_hist = len(history)
        baseline_dominant: list[str] = sorted(
            [s for s, cnt in component_freq.items() if cnt / n_hist >= 0.5],
            key=lambda s: component_freq[s], reverse=True
        )[:k]

        baseline_set = set(baseline_dominant)
        current_set  = set(current_ranked)
        emerged  = [s for s in current_ranked  if s not in baseline_set]
        receded  = [s for s in baseline_dominant if s not in current_set]

        if crsi >= SSD_INSTABILITY_THRESHOLD:
            shift_class = "STABLE"
        elif crsi >= SSD_STRUCTURAL_THRESHOLD:
            shift_class = "DRIFT_WITH_INSTABILITY"
        else:
            shift_class = "STRUCTURAL_SHIFT"

        if shift_class == "STRUCTURAL_SHIFT":
            logger.warning(
                f"[AVM][SSD] STRUCTURAL_SHIFT — domain={domain} ssd_id={ssd_id} "
                f"crsi={crsi:.4f} < threshold={SSD_STRUCTURAL_THRESHOLD} "
                f"cycles={n_hist} emerged={emerged} receded={receded} "
                f"current_top_k={current_ranked} baseline_top_k={baseline_dominant}"
            )
        elif shift_class == "DRIFT_WITH_INSTABILITY":
            logger.info(
                f"[AVM][SSD] DRIFT_WITH_INSTABILITY — domain={domain} ssd_id={ssd_id} "
                f"crsi={crsi:.4f} in [{SSD_STRUCTURAL_THRESHOLD},{SSD_INSTABILITY_THRESHOLD})"
            )

        return StructuralShiftReport(
            ssd_id=ssd_id,
            domain=domain,
            shift_class=shift_class,
            crsi=crsi,
            cycles_analyzed=n_hist,
            dominant_components_current=current_ranked,
            dominant_components_baseline=baseline_dominant,
            emerged_components=emerged,
            receded_components=receded,
            detected_at=now_iso,
        )

    # ── OMNIX DIFFERENTIATOR: GTPD methods ────────────────────────────────────

    def _update_drift_history(self, domain: str, drift_score: float) -> None:
        """Append a drift score to the GTPD per-domain ring buffer."""
        with _GTPD_HISTORY_LOCK:
            if domain not in _gtpd_drift_history:
                _gtpd_drift_history[domain] = []
            _gtpd_drift_history[domain].append(drift_score)
            if len(_gtpd_drift_history[domain]) > _GTPD_HISTORY_SIZE:
                _gtpd_drift_history[domain].pop(0)

    def _detect_threshold_probe(
        self,
        domain: str,
        threshold: float,
        current_drift: float,
    ) -> ThresholdProbeReport:
        """
        OMNIX DIFFERENTIATOR — Governance Threshold Probe Detection.

        Detects systematic reverse-engineering of the AVM approval boundary.

        An adversary probing the threshold submits many near-threshold
        evaluations.  Natural usage produces drift scores spread across the
        full 0–100 range.  Probing produces a tight cluster near the threshold.

        Algorithm:
          1. Fetch the last N drift scores for this domain.
          2. Define "near threshold" as within ±(threshold × 0.30) points.
          3. clustering_coefficient = near_count / total_count.
          4. CLEAN:             < 20% near-threshold OR < 3 evaluations.
             SUSPECTED:         20–60% near-threshold AND ≥ 3 evaluations.
             CONFIRMED:         > 60% near-threshold AND ≥ 5 evaluations.

        This is statistically improbable by chance: with uniformly distributed
        drift scores, only 60% × (2 × 0.30 / 100) = ~0.36% of evaluations
        would naturally fall in a 30%-wide band near the threshold.
        """
        probe_id  = f"GTPD-{uuid.uuid4().hex[:10].upper()}"
        now_iso   = datetime.now(timezone.utc).isoformat()
        margin    = threshold * 0.30

        with _GTPD_HISTORY_LOCK:
            history = list(_gtpd_drift_history.get(domain, []))

        if len(history) < 3:
            return ThresholdProbeReport(
                probe_id=probe_id,
                domain=domain,
                probe_score=0.0,
                clustering_coefficient=0.0,
                evaluations_analyzed=len(history),
                evaluations_near_threshold=0,
                threshold_margin=round(margin, 1),
                probe_verdict="INSUFFICIENT_DATA",
                detected_at=now_iso,
            )

        near_count  = sum(1 for s in history if abs(s - threshold) <= margin)
        total       = len(history)
        clustering  = round(near_count / total, 3)

        # Score increases with both clustering density and total evidence count
        concentration_factor = min(1.0, total / 20.0)
        probe_score = round(clustering * 100.0 * concentration_factor, 1)

        if near_count >= 5 and clustering > 0.60:
            verdict = "CONFIRMED"
        elif near_count >= 3 and clustering > 0.20:
            verdict = "SUSPECTED"
        else:
            verdict = "CLEAN"

        if verdict in ("SUSPECTED", "CONFIRMED"):
            logger.warning(
                f"[AVM][GTPD] Threshold probe {verdict} — domain={domain} "
                f"probe_id={probe_id} clustering={clustering:.2f} "
                f"near={near_count}/{total} margin=±{margin:.1f}"
            )

        return ThresholdProbeReport(
            probe_id=probe_id,
            domain=domain,
            probe_score=probe_score,
            clustering_coefficient=clustering,
            evaluations_analyzed=total,
            evaluations_near_threshold=near_count,
            threshold_margin=round(margin, 1),
            probe_verdict=verdict,
            detected_at=now_iso,
        )

    # ── Drift computation ──────────────────────────────────────────────────────

    def _compute_drift(
        self,
        baseline: dict[str, float],
        current: dict[str, float],
    ) -> tuple[float, dict[str, float]]:
        """
        Compute the weighted drift score between baseline and current signals.

        Each signal's drift is the absolute difference on a 0-100 scale.
        The total drift is the weighted sum across SIGNAL_WEIGHTS.

        Risk exposure is inverted: lower risk at calibration and higher now
        contributes positively to drift (conditions are more dangerous).

        Returns:
            (total_drift_score, {signal: drift_value})
        """
        components: dict[str, float] = {}
        total_weight = 0.0
        weighted_drift = 0.0

        for signal, weight in SIGNAL_WEIGHTS.items():
            baseline_val = baseline.get(signal)
            current_val = current.get(signal)

            if baseline_val is None or current_val is None:
                continue

            # ── Non-finite barrier (second layer, fail-closed) ──────────────────
            # If either value is NaN or Inf, treat as maximum drift to ensure
            # the governance engine blocks rather than silently passes.
            if not math.isfinite(baseline_val) or not math.isfinite(current_val):
                components[signal] = 100.0
                weighted_drift += weight * 100.0
                total_weight += weight
                logger.warning(
                    f"[AVM] NON_FINITE_SIGNAL in _compute_drift — "
                    f"signal={signal} baseline={baseline_val} current={current_val} "
                    f"→ clamped to max drift"
                )
                continue

            raw_drift = abs(current_val - baseline_val)

            # For risk_exposure: drift direction matters more.
            # If risk has INCREASED beyond baseline, amplify the drift signal.
            if signal == "risk_exposure" and current_val > baseline_val:
                raw_drift *= 1.4

            components[signal] = round(min(raw_drift, 100.0), 2)
            weighted_drift += weight * components[signal]
            total_weight += weight

        if total_weight == 0:
            return 0.0, components

        normalized = (weighted_drift / total_weight) if total_weight > 0 else 0.0
        return round(min(normalized * (1.0 / max(total_weight, 0.01)), 100.0), 2), components

    # ── Main evaluation ────────────────────────────────────────────────────────

    def evaluate(
        self,
        signals: dict[str, float],
        domain: str = "generic",
    ) -> AVMResult:
        """
        Evaluate whether the current signals are still within the calibration
        envelope for the given domain.

        Args:
            signals: Current normalized governance signals (0-100 scale).
            domain: Domain identifier matching the calibration snapshot.

        Returns:
            AVMResult. If is_valid=False, the pipeline must block.
        """
        enabled = os.environ.get("AVM_ENABLED", "true").lower() != "false"
        if not enabled:
            return AVMResult(
                is_valid=True,
                snapshot_id="DISABLED",
                parameter_version="N/A",
                drift_score=0.0,
                drift_components={},
                age_hours=0.0,
                drift_threshold=self.drift_threshold,
                block_reason=None,
                warnings=["AVM disabled via AVM_ENABLED=false"],
                pass_through=True,
            )

        snapshot = self.load_snapshot(domain)
        if snapshot is None:
            logger.warning(
                f"[AVM] No calibration snapshot for domain={domain} — pass-through. "
                "Call save_calibration_snapshot() to enable drift detection."
            )
            return AVMResult(
                is_valid=True,
                snapshot_id="NO_BASELINE",
                parameter_version="N/A",
                drift_score=0.0,
                drift_components={},
                age_hours=0.0,
                drift_threshold=self.drift_threshold,
                block_reason=None,
                warnings=[
                    f"No calibration snapshot found for domain='{domain}'. "
                    "Drift detection inactive — call save_calibration_snapshot() to arm AVM."
                ],
                pass_through=True,
            )

        age_hours = snapshot.age_hours()
        warnings: list[str] = []

        # ── Critical age check ──────────────────────────────────────────────────
        if age_hours > self.critical_age_hours:
            reason = (
                f"Calibration snapshot is {age_hours:.0f}h old "
                f"(critical threshold: {self.critical_age_hours:.0f}h). "
                f"Assumptions are critically stale — recalibration required."
            )
            logger.error(f"[AVM] CRITICAL_STALE BLOCK — {reason}")
            return AVMResult(
                is_valid=False,
                snapshot_id=snapshot.snapshot_id,
                parameter_version=snapshot.parameter_version,
                drift_score=100.0,
                drift_components={},
                age_hours=round(age_hours, 1),
                drift_threshold=self.drift_threshold,
                block_reason=reason,
                warnings=[],
                pass_through=False,
            )

        # ── Age warning (non-blocking) ──────────────────────────────────────────
        if age_hours > self.max_age_hours:
            warnings.append(
                f"Calibration snapshot age {age_hours:.0f}h exceeds "
                f"recommended max {self.max_age_hours:.0f}h. "
                "Consider recalibration."
            )
            # Tighten drift threshold proportionally as age increases beyond max
            age_overage_ratio = min((age_hours - self.max_age_hours) / self.max_age_hours, 1.0)
            effective_threshold = self.drift_threshold * (1.0 - 0.3 * age_overage_ratio)
        else:
            effective_threshold = self.drift_threshold

        # ── Non-finite signal guard (first layer, fail-closed) ─────────────────
        # NaN or Inf in any signal makes drift computation semantically undefined.
        # Python: NaN > threshold = False → would silently PASS. We BLOCK instead.
        # ADR-074 §4.3: any non-finite signal → is_valid=False, reason NON_FINITE_SIGNAL.
        non_finite_signals = [
            f"{k}={v}"
            for k, v in signals.items()
            if isinstance(v, (int, float)) and not math.isfinite(v)
        ]
        if non_finite_signals:
            reason = (
                f"NON_FINITE_SIGNAL — governance cannot certify under non-finite inputs: "
                f"{', '.join(non_finite_signals[:4])}. "
                "All governance signals must be finite floats in [0, 100]."
            )
            logger.error(
                f"[AVM] NON_FINITE_BLOCK — domain={domain} | "
                f"non_finite={non_finite_signals[:4]}"
            )
            return AVMResult(
                is_valid=False,
                snapshot_id=snapshot.snapshot_id,
                parameter_version=snapshot.parameter_version,
                drift_score=100.0,
                drift_components={},
                age_hours=round(age_hours, 1),
                drift_threshold=self.drift_threshold,
                block_reason=reason,
                warnings=[],
                pass_through=False,
            )

        # ── ADR-076: Schema match audit (before drift computation) ─────────────
        # Compares snapshot baseline keys against SIGNAL_SCHEMA to detect
        # misalignment that would silently disable or distort drift detection.
        baseline_key_set  = frozenset(snapshot.baseline_signals.keys())
        incoming_key_set  = frozenset(signals.keys())
        schema_overlap    = baseline_key_set & _SIGNAL_SCHEMA_SET & incoming_key_set
        n_overlap         = len(schema_overlap)
        n_schema          = len(_SIGNAL_SCHEMA_SET)

        if n_overlap == n_schema:
            schema_match = "FULL"
        elif n_overlap > 0:
            schema_match = f"PARTIAL({n_overlap}/{n_schema})"
        else:
            schema_match = "NONE"

        logger.info(
            f"[AVM] AVM_SCHEMA_MATCH={schema_match} | domain={domain} | "
            f"snapshot={snapshot.snapshot_id} | age={age_hours:.1f}h"
        )

        # Anomaly detection: NONE or PARTIAL match indicates a schema drift bug.
        # These conditions silently corrupt drift calculation; surface them loudly.
        if schema_match == "NONE":
            logger.error(
                f"[AVM] SCHEMA_ANOMALY — domain={domain} | AVM_SCHEMA_MATCH=NONE | "
                f"baseline_keys={sorted(baseline_key_set)} | "
                f"expected={sorted(_SIGNAL_SCHEMA_SET)} | "
                f"drift detection DISABLED — recalibrate snapshot with correct keys "
                f"(see ADR-076). snapshot={snapshot.snapshot_id}"
            )
            warnings.append(
                f"AVM_SCHEMA_MATCH=NONE for domain='{domain}': baseline keys "
                f"do not overlap with SIGNAL_SCHEMA. Drift detection is disabled. "
                "Recalibrate with SIGNAL_SCHEMA-compliant keys."
            )
            try:
                from omnix_core.governance.avm_alerts import fire_avm_alert
                fire_avm_alert(
                    event_type="SCHEMA_ANOMALY_NONE",
                    domain=domain,
                    detail=(
                        f"AVM_SCHEMA_MATCH=NONE: zero baseline signal keys overlap "
                        f"with SIGNAL_SCHEMA.\n"
                        f"Baseline keys: {sorted(baseline_key_set)}\n"
                        f"Expected: {sorted(_SIGNAL_SCHEMA_SET)}\n"
                        "Drift detection is DISABLED. Recalibrate immediately."
                    ),
                    snapshot_id=snapshot.snapshot_id,
                )
            except Exception as _alert_exc:
                logger.warning(f"[AVM] fire_avm_alert(SCHEMA_MISMATCH) failed: {_alert_exc}")
        elif schema_match.startswith("PARTIAL"):
            logger.warning(
                f"[AVM] SCHEMA_ANOMALY — domain={domain} | AVM_SCHEMA_MATCH={schema_match} | "
                f"Only {n_overlap}/{n_schema} SIGNAL_SCHEMA keys matched. "
                f"Missing: {sorted(_SIGNAL_SCHEMA_SET - schema_overlap)} | "
                f"Drift score may be artificially amplified. snapshot={snapshot.snapshot_id}"
            )
            warnings.append(
                f"AVM_SCHEMA_MATCH={schema_match} for domain='{domain}': "
                f"partial key overlap detected. Drift score may be unreliable."
            )
            try:
                from omnix_core.governance.avm_alerts import fire_avm_alert
                fire_avm_alert(
                    event_type="SCHEMA_ANOMALY_PARTIAL",
                    domain=domain,
                    detail=(
                        f"AVM_SCHEMA_MATCH={schema_match}: partial key overlap.\n"
                        f"Missing: {sorted(_SIGNAL_SCHEMA_SET - schema_overlap)}\n"
                        "Drift score may be artificially amplified."
                    ),
                    snapshot_id=snapshot.snapshot_id,
                )
            except Exception as _alert_exc:
                logger.warning(f"[AVM] fire_avm_alert(SCHEMA_ANOMALY_PARTIAL) failed: {_alert_exc}")
        # ───────────────────────────────────────────────────────────────────────

        # ADR-120: Cache the incoming signals for this domain so the auto-recalibrator
        # can use them as the new baseline without needing to query the governance engine.
        # Only cache when signals match SIGNAL_SCHEMA (schema_match != "NONE").
        if schema_match != "NONE":
            _schema_signals = {
                k: float(v) for k, v in signals.items()
                if k in _SIGNAL_SCHEMA_SET and isinstance(v, (int, float)) and math.isfinite(v)
            }
            if len(_schema_signals) == len(_SIGNAL_SCHEMA_SET):
                with self._last_seen_lock:
                    self._last_seen_signals[domain] = _schema_signals

        # ── Drift computation ───────────────────────────────────────────────────
        drift_score, drift_components = self._compute_drift(
            snapshot.baseline_signals, signals
        )
        # GTPD: record every evaluation (pass or block) for probe detection
        self._update_drift_history(domain, drift_score)
        # SSD (ADR-175): update component composition history and compute structural shift
        self._update_component_history(domain, drift_components)
        ssd_report = self._detect_structural_shift(domain, drift_components)

        # Per-signal warnings for high individual drift
        for sig, drift_val in drift_components.items():
            if drift_val > 40.0:
                warnings.append(
                    f"High individual drift on '{sig}': {drift_val:.1f}/100 "
                    f"(baseline={snapshot.baseline_signals.get(sig, '?'):.1f}, "
                    f"current={signals.get(sig, '?'):.1f})"
                )

        # Drift anomaly: score pinned at extremes often signals a systemic bug
        if drift_score >= 99.9 and schema_match != "FULL":
            logger.error(
                f"[AVM] DRIFT_ANOMALY — domain={domain} | drift=100.0 with "
                f"AVM_SCHEMA_MATCH={schema_match} — likely schema key mismatch, "
                f"not genuine drift. Recalibrate snapshot. snapshot={snapshot.snapshot_id}"
            )
            try:
                from omnix_core.governance.avm_alerts import fire_avm_alert
                fire_avm_alert(
                    event_type="DRIFT_ANOMALY",
                    domain=domain,
                    detail=(
                        f"drift_score=100.0 with AVM_SCHEMA_MATCH={schema_match}.\n"
                        "This is likely a schema key mismatch, not genuine drift.\n"
                        f"Baseline keys: {sorted(baseline_key_set)}\n"
                        "Recalibrate snapshot immediately."
                    ),
                    snapshot_id=snapshot.snapshot_id,
                )
            except Exception as _alert_exc:
                logger.warning(f"[AVM] fire_avm_alert(DRIFT_ANOMALY) failed: {_alert_exc}")

        # ── Drift threshold check ───────────────────────────────────────────────
        if drift_score > effective_threshold:
            reason = (
                f"Assumption drift score {drift_score:.1f} exceeds threshold "
                f"{effective_threshold:.1f} (snapshot_id={snapshot.snapshot_id}, "
                f"age={age_hours:.1f}h). "
                "Pipeline assumptions are too stale to issue a valid governance receipt."
            )
            logger.warning(
                f"[AVM] DRIFT_BLOCK — domain={domain} | "
                f"drift={drift_score:.1f} > threshold={effective_threshold:.1f} | "
                f"snapshot={snapshot.snapshot_id} | age={age_hours:.1f}h"
            )
            return AVMResult(
                is_valid=False,
                snapshot_id=snapshot.snapshot_id,
                parameter_version=snapshot.parameter_version,
                drift_score=drift_score,
                drift_components=drift_components,
                age_hours=round(age_hours, 1),
                drift_threshold=effective_threshold,
                block_reason=reason,
                warnings=warnings,
                pass_through=False,
                structural_shift_report=ssd_report.to_dict(),
            )

        # ── ADR-144: AUTO_MODIFIED trust flag ──────────────────────────────────
        # If this domain's current snapshot was produced by an automated
        # modification (PHASE4_LIVE_DEPLOY, MCM_AUTO_TIGHTEN, etc.), surface a
        # warning so the trust flag propagates into governance receipts.
        auto_modified_tags = {"PHASE4_LIVE_DEPLOY", "MCM_AUTO_TIGHTEN", "AUTO_MODIFIED_SNAPSHOT", "AMG_ROLLBACK"}
        snapshot_tags = set(snapshot.tags or [])
        if snapshot_tags & auto_modified_tags:
            amg_mod_id = next(
                (t.split(":", 1)[1] for t in snapshot_tags if t.startswith("AMG:")),
                "UNKNOWN",
            )
            warnings.append(
                f"AUTO_MODIFIED_SNAPSHOT: this domain's AVM thresholds were last set "
                f"by an automated process (tags={sorted(snapshot_tags & auto_modified_tags)}). "
                f"modification_id={amg_mod_id}. "
                "Governance receipts carry trust_flags.auto_modified_snapshot=true (ADR-144)."
            )

        logger.debug(
            f"[AVM] VALID — domain={domain} | drift={drift_score:.1f} ≤ {effective_threshold:.1f} | "
            f"age={age_hours:.1f}h | snapshot={snapshot.snapshot_id}"
        )
        # GTPD: compute probe report only on VALID evaluations
        # (adversary needs passing evaluations to calibrate their attack)
        probe_report = self._detect_threshold_probe(domain, effective_threshold, drift_score)
        return AVMResult(
            is_valid=True,
            snapshot_id=snapshot.snapshot_id,
            parameter_version=snapshot.parameter_version,
            drift_score=drift_score,
            drift_components=drift_components,
            age_hours=round(age_hours, 1),
            drift_threshold=effective_threshold,
            block_reason=None,
            warnings=warnings,
            pass_through=False,
            probe_report=probe_report.to_dict(),
            structural_shift_report=ssd_report.to_dict(),
        )


    # ── ADR-120: Auto-recalibration ────────────────────────────────────────────

    def auto_recalibrate_stale_domains(
        self,
        recalib_interval_hours: float = 72.0,
        max_drift_for_auto: float = 80.0,
    ) -> list[str]:
        """
        ADR-120: Automatically recalibrate domains whose AVM snapshot is stale
        OR whose drift has exceeded the threshold, using the last-seen live signals.

        Policy:
          - Only recalibrates if we have cached signals for that domain (from a
            previous evaluate() call). If the domain has NEVER been evaluated since
            server start, we skip it — there is no live signal to anchor to.
          - Recalibration is skipped when drift > max_drift_for_auto (80%), because
            extreme drift likely indicates a genuine crisis, not normal market evolution.
          - Tags snapshot with ["AUTO_RECALIBRATION"] for audit trail.
          - Always persists to DB and JSON — same path as manual recalibration.

        AMG SCOPE BOUNDARY (ADR-144 §4):
          This method intentionally does NOT pass through the Auto-Modification Guard.
          Rationale: auto_recalibrate_stale_domains() performs BASELINE RECALIBRATION
          — it re-anchors baseline_signals to current live market state while
          PRESERVING checkpoint_thresholds unchanged (line: checkpoint_thresholds=
          snapshot.checkpoint_thresholds). The AMG is designed to protect threshold
          modifications (checkpoint_thresholds), not baseline signal re-anchoring.

          The two modification types carry different governance semantics:
            THRESHOLD MODIFICATION (AMG-protected):
              Changes the veto sensitivity of each governance checkpoint.
              A 20% threshold tightening directly changes what decisions get blocked.
              This is what run_guard() protects.

            BASELINE RECALIBRATION (outside AMG scope):
              Updates the market reference against which drift is measured.
              Does not change what gets blocked — changes what counts as "normal".
              Governed by its own safeguards: max_drift_for_auto cap (80%),
              SIGNAL_SCHEMA_MISMATCH guard, and 72h minimum interval.

          The forensic audit (May 2026) confirmed this boundary is by design
          and documented in FORENSIC_VALIDATION_REPORT.md §4.1.

        Returns:
            List of domain names that were successfully recalibrated.
        """
        recalibrated: list[str] = []

        # Collect all domains with snapshots (from memory store + disk)
        domains = set(self._memory_store.keys())
        try:
            for p in self._snapshots_dir.glob("*_calibration.json"):
                d = p.stem.replace("_calibration", "")
                domains.add(d)
        except Exception as _e:
            logger.debug(f"[AVM.AUTO] Disk glob failed (snapshots dir may not exist yet): {_e}")

        if not domains:
            logger.info("[AVM.AUTO] No snapshots found — nothing to recalibrate")
            return recalibrated

        for domain in sorted(domains):
            try:
                snapshot = self.load_snapshot(domain)
                if snapshot is None:
                    continue

                age_hours = snapshot.age_hours()
                needs_recalib_by_age = age_hours >= recalib_interval_hours

                # Get cached live signals for this domain
                with self._last_seen_lock:
                    live_signals = self._last_seen_signals.get(domain)

                if live_signals is None:
                    if needs_recalib_by_age:
                        logger.info(
                            f"[AVM.AUTO] {domain}: stale ({age_hours:.0f}h) but no live "
                            f"signals cached yet — skipping until first evaluate() call"
                        )
                    continue

                # Compute drift against live signals (this IS the current drift)
                actual_drift, drift_components = self._compute_drift(
                    snapshot.baseline_signals, live_signals
                )

                # ── Signal schema validation (datos malos guard) ───────────────────
                # If drift_components is empty but both dicts are non-empty, the signal
                # schemas have NO overlap — recalibrating would anchor to an incoherent
                # baseline that doesn't match SIGNAL_WEIGHTS. Block and warn.
                baseline_keys = set(snapshot.baseline_signals.keys())
                live_keys = set(live_signals.keys())
                if not drift_components and baseline_keys and live_keys:
                    logger.warning(
                        f"[AVM.AUTO] ⚠️ {domain}: SIGNAL_SCHEMA_MISMATCH — "
                        f"no overlapping signals between baseline {baseline_keys} "
                        f"and live {live_keys} — skipping recalibration. "
                        f"Investigate why evaluate() cached signals with different keys."
                    )
                    continue

                needs_recalib_by_drift = actual_drift >= self.drift_threshold

                if not (needs_recalib_by_age or needs_recalib_by_drift):
                    logger.debug(
                        f"[AVM.AUTO] {domain}: age={age_hours:.0f}h drift={actual_drift:.1f}% — OK, no recalibration needed"
                    )
                    continue

                # Safety guard: do NOT auto-recalibrate under extreme drift
                if actual_drift > max_drift_for_auto:
                    logger.warning(
                        f"[AVM.AUTO] ⚠️ {domain}: drift={actual_drift:.1f}% > "
                        f"max_drift_for_auto={max_drift_for_auto:.0f}% — "
                        f"SKIPPING auto-recalibration (may be genuine crisis). "
                        f"Manual review required."
                    )
                    continue

                # SSD-INV-001 (ADR-175): do NOT auto-recalibrate when STRUCTURAL_SHIFT detected.
                # A structural shift means the domain's signal topology has changed — the
                # current calibration frame may be entirely obsolete. Auto-recalibrating
                # would anchor a new baseline to an incoherent signal topology, embedding
                # unvalidated assumptions. Human review is required to determine whether
                # the new topology is legitimate before any baseline is accepted.
                # This guard is independent of and additive to AGV-INV-006 (AGVP).
                try:
                    _ssd_check = self._detect_structural_shift(domain, drift_components)
                    if _ssd_check.shift_class == "STRUCTURAL_SHIFT":
                        logger.warning(
                            f"[AVM.AUTO] SSD-INV-001: {domain}: STRUCTURAL_SHIFT detected "
                            f"(crsi={_ssd_check.crsi:.4f} < threshold={SSD_STRUCTURAL_THRESHOLD}) — "
                            f"SKIPPING auto-recalibration. Human review required before "
                            f"recalibration can proceed. ssd_id={_ssd_check.ssd_id} "
                            f"emerged={_ssd_check.emerged_components} "
                            f"receded={_ssd_check.receded_components}"
                        )
                        continue
                except Exception as _ssd_exc:
                    logger.debug(f"[AVM.AUTO] SSD check failed for {domain}: {_ssd_exc} — proceeding")

                reason = []
                if needs_recalib_by_age:
                    reason.append(f"age={age_hours:.0f}h>={recalib_interval_hours:.0f}h")
                if needs_recalib_by_drift:
                    reason.append(f"drift={actual_drift:.1f}%>={self.drift_threshold:.0f}%")

                description = (
                    f"AUTO_RECALIBRATION (ADR-120): scheduled {recalib_interval_hours:.0f}h cycle — "
                    + ", ".join(reason)
                )

                logger.warning(
                    f"[AVM.AUTO] 🔄 Recalibrando {domain}: {', '.join(reason)} "
                    f"→ anchoring to live signals"
                )

                self.save_calibration_snapshot(
                    domain=domain,
                    baseline_signals=live_signals,
                    checkpoint_thresholds=snapshot.checkpoint_thresholds or {},
                    description=description,
                    tags=["AUTO_RECALIBRATION", f"interval_{recalib_interval_hours:.0f}h",
                          f"prev_drift_{actual_drift:.1f}"],
                )

                # Also persist to DB
                try:
                    db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
                    if db_url:
                        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge
                        bridge = AVMDatabaseBridge(db_url=db_url)
                        new_snap = self.load_snapshot(domain)
                        if new_snap:
                            bridge.save_snapshot(
                                snapshot_dict=new_snap.to_dict(),
                                reason="AUTO_RECALIBRATION",
                                actor="avm_auto_recalib",
                                action="RECALIBRATE",
                            )
                except Exception as _db_exc:
                    logger.warning(f"[AVM.AUTO] DB persist failed for {domain}: {_db_exc} — JSON OK")

                recalibrated.append(domain)
                logger.info(
                    f"[AVM.AUTO] ✅ {domain}: recalibrated successfully "
                    f"(prev_age={age_hours:.0f}h, prev_drift={actual_drift:.1f}%)"
                )

            except Exception as exc:
                logger.error(f"[AVM.AUTO] ❌ {domain}: recalibration error — {exc}")

        if recalibrated:
            logger.info(f"[AVM.AUTO] Ciclo completo — recalibrados: {recalibrated}")
        else:
            logger.info("[AVM.AUTO] Ciclo completo — todos los dominios dentro de tolerancia")

        return recalibrated

    # ── ADR-120 Phase 3: Performance-Based Threshold Optimization ──────────────

    def optimize_checkpoint_thresholds(
        self,
        domain: str,
        lookback_days: int = 30,
        target_block_rate: float = 0.15,
        max_adjustment_pct: float = 0.20,
        db_url: str | None = None,
    ) -> dict[str, float] | None:
        """
        ADR-120 Phase 3: Analyze recent governance decisions and optimize
        checkpoint thresholds to achieve target_block_rate.

        Algorithm:
          1. Query decision_receipts for the last lookback_days.
          2. Compute actual block rate per checkpoint (from veto_chain).
          3. Compare each checkpoint's firing rate to target.
          4. Adjust thresholds: over-firing → loosen (+); under-firing → tighten (−).
          5. Cap adjustment at max_adjustment_pct per cycle.

        Returns:
            Dict of {checkpoint_id → optimized_threshold} or None if insufficient data.
        """
        _db_url = db_url or os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        if not _db_url:
            logger.warning(f"[AVM.PHASE3] {domain}: no DB URL — skipping")
            return None

        snapshot = self.load_snapshot(domain)
        if snapshot is None:
            logger.warning(f"[AVM.PHASE3] {domain}: no baseline snapshot found")
            return None

        current_thresholds = dict(snapshot.checkpoint_thresholds or {})
        if not current_thresholds:
            logger.info(f"[AVM.PHASE3] {domain}: no checkpoint_thresholds in snapshot — skipping")
            return None

        try:
            import psycopg
            conn = psycopg.connect(_db_url)
            cur  = conn.cursor()

            from datetime import datetime as _dt, timezone as _tz, timedelta as _td
            cutoff_ts = _dt.now(_tz.utc) - _td(days=lookback_days)
            cur.execute(
                """
                SELECT veto_chain, decision
                  FROM decision_receipts
                 WHERE domain = %s
                   AND timestamp_utc >= %s
                   AND veto_chain IS NOT NULL
                """,
                (domain, cutoff_ts),
            )
            rows = cur.fetchall()
            conn.close()

            if len(rows) < 20:
                logger.info(
                    f"[AVM.PHASE3] {domain}: only {len(rows)} receipts in last "
                    f"{lookback_days}d — need >=20 for optimization"
                )
                return None

            total          = len(rows)
            actual_blocks  = sum(1 for _, dec in rows if (dec or "").upper() == "BLOCKED")
            actual_block_rate = actual_blocks / total

            logger.info(
                f"[AVM.PHASE3] {domain}: {total} decisions | "
                f"block_rate={actual_block_rate:.1%} | target={target_block_rate:.1%}"
            )

            # Count per-checkpoint firing frequency from veto_chains
            import json as _json
            import re as _re
            cp_fires: dict[str, int] = {}
            gate_pattern = _re.compile(r"^([A-Z][A-Z0-9_()\\-]+):")
            for veto_raw, _ in rows:
                try:
                    chain = _json.loads(veto_raw) if isinstance(veto_raw, str) else (veto_raw or [])
                    for entry in (chain if isinstance(chain, list) else []):
                        if isinstance(entry, str):
                            m = gate_pattern.match(entry.strip())
                            if m:
                                cp = m.group(1)
                                cp_fires[cp] = cp_fires.get(cp, 0) + 1
                except Exception:
                    continue

            # Compute ratio (actual_rate / target_rate) — if > 1 system over-blocks
            ratio = actual_block_rate / target_block_rate if target_block_rate > 0 else 1.0

            optimized: dict[str, float] = {}
            for cp_id, current_val in current_thresholds.items():
                cp_fire_rate = cp_fires.get(cp_id, 0) / total
                if cp_fire_rate == 0:
                    # Never fired — threshold may be too high, loosen slightly
                    adj = current_val * (1.0 + max_adjustment_pct * 0.5)
                elif ratio > 1.05:
                    # Over-blocking: loosen (increase threshold)
                    adj = current_val * (1.0 + min(ratio - 1.0, max_adjustment_pct))
                elif ratio < 0.95:
                    # Under-blocking: tighten (decrease threshold)
                    adj = current_val * (1.0 - min(1.0 - ratio, max_adjustment_pct))
                else:
                    adj = current_val

                optimized[cp_id] = round(max(0.01, min(adj, 0.99)), 4)

            logger.info(
                f"[AVM.PHASE3] {domain}: optimized {len(optimized)} thresholds | "
                f"ratio={ratio:.2f} | block_delta={actual_block_rate - target_block_rate:+.1%}"
            )
            return optimized

        except Exception as exc:
            logger.error(f"[AVM.PHASE3] {domain}: threshold optimization failed — {exc}")
            return None

    def deploy_optimized_thresholds(
        self,
        domain: str,
        optimized_thresholds: dict[str, float],
        db_url: str | None = None,
        source: str = "PHASE4_OPT",
    ) -> bool:
        """
        ADR-120 Phase 4 + ADR-144: Apply optimized thresholds from Phase 3 to the
        live AVM calibration snapshot for the given domain.

        All modifications pass through the Auto-Modification Guard (ADR-144) before
        any change is written. The guard enforces:
          1. Cumulative drift cap from genesis (AVM_MAX_CUMULATIVE_DRIFT_PCT, default 30%)
          2. Signed diff proof (SHA-256 + Dilithium-3 when available)
          3. Approval gate for changes > AVM_APPROVAL_THRESHOLD_PCT (default 10%)
          4. Trust flag propagation (AUTO_MODIFIED_SNAPSHOT) to all future receipts

        Rollback eligibility is registered automatically — the guard sets a
        performance_check_at timestamp 24h after deployment.

        Returns:
            True if deployment succeeded (allowed by guard), False otherwise.
        """
        if not optimized_thresholds:
            logger.warning(f"[AVM.PHASE4] {domain}: empty thresholds dict — nothing to deploy")
            return False

        snapshot = self.load_snapshot(domain)
        if snapshot is None:
            logger.warning(f"[AVM.PHASE4] {domain}: no existing snapshot — cannot deploy")
            return False

        _db_url = db_url or os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")

        # ── ADR-144: Auto-Modification Guard ───────────────────────────────────
        if _db_url:
            try:
                from omnix_core.governance.auto_modification_guard import (
                    run_guard, check_rollback_needed, mark_modification_status
                )

                # Before deploying: check if a previous modification needs rollback
                needs_rollback, rollback_thresholds = check_rollback_needed(domain, _db_url)
                if needs_rollback and rollback_thresholds:
                    logger.warning(
                        f"[AVM.PHASE4] {domain}: AMG rollback triggered — "
                        f"restoring previous thresholds instead of deploying new ones"
                    )
                    # Deploy the rollback thresholds (bypass guard for rollbacks)
                    self._apply_thresholds_to_snapshot(
                        domain=domain,
                        snapshot=snapshot,
                        thresholds=rollback_thresholds,
                        description=f"AMG AUTO-ROLLBACK (ADR-144): performance degraded post-deployment",
                        tags=["AMG_ROLLBACK", "ADR-144"],
                    )
                    return True

                # Run the full AMG gate sequence
                amg_result = run_guard(
                    domain=domain,
                    thresholds_before=dict(snapshot.checkpoint_thresholds or {}),
                    thresholds_after=optimized_thresholds,
                    source=source,
                    db_url=_db_url,
                )

                if not amg_result.allowed:
                    logger.warning(
                        f"[AVM.PHASE4] {domain}: AMG BLOCKED deployment — "
                        f"{amg_result.blocked_reason}"
                    )
                    return False

                # Embed trust flags in tags for receipt propagation
                amg_tags = [
                    "PHASE4_LIVE_DEPLOY", "THRESHOLD_OPTIMIZATION", "ADR-120",
                    "AUTO_MODIFIED_SNAPSHOT",
                    f"AMG:{amg_result.modification_id}",
                    f"cumulative_drift_{amg_result.cumulative_drift_pct:.1f}pct",
                ]

                self._apply_thresholds_to_snapshot(
                    domain=domain,
                    snapshot=snapshot,
                    thresholds=optimized_thresholds,
                    description=(
                        f"ADR-120 Phase 4 LIVE DEPLOYMENT (ADR-144 approved): "
                        f"{len(optimized_thresholds)} checkpoints | "
                        f"mod={amg_result.modification_id} | "
                        f"cumulative_drift={amg_result.cumulative_drift_pct:.1f}%"
                    ),
                    tags=amg_tags,
                )

                # Persist to DB
                if _db_url:
                    try:
                        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge
                        bridge   = AVMDatabaseBridge(db_url=_db_url)
                        new_snap = self.load_snapshot(domain)
                        if new_snap:
                            bridge.save_snapshot(
                                snapshot_dict=new_snap.to_dict(),
                                reason=f"PHASE4_OPT|AMG:{amg_result.modification_id}",
                                actor="avm_phase4_auto",
                                action="RECALIBRATE",
                            )
                    except Exception as _db_exc:
                        logger.warning(f"[AVM.PHASE4] DB persist failed for {domain}: {_db_exc}")

                logger.info(
                    f"[AVM.PHASE4] ✅ {domain}: {len(optimized_thresholds)} thresholds deployed "
                    f"| mod={amg_result.modification_id} "
                    f"| cumulative_drift={amg_result.cumulative_drift_pct:.1f}% "
                    f"| max_delta={amg_result.max_single_delta_pct:.1f}%"
                )
                return True

            except ImportError:
                logger.warning(f"[AVM.PHASE4] AMG not available — deploying without guard (DB URL missing)")
        else:
            logger.warning(f"[AVM.PHASE4] {domain}: no DB URL — AMG guard skipped, proceeding without audit trail")

        # Fallback: no DB, deploy directly (dev/test only)
        try:
            self._apply_thresholds_to_snapshot(
                domain=domain,
                snapshot=snapshot,
                thresholds=optimized_thresholds,
                description=f"ADR-120 Phase 4 (no DB — unguarded): {len(optimized_thresholds)} checkpoints updated",
                tags=["PHASE4_LIVE_DEPLOY", "ADR-120", "UNGUARDED_NO_DB"],
            )
            logger.warning(f"[AVM.PHASE4] {domain}: deployed WITHOUT AMG guard (no DB)")
            return True
        except Exception as exc:
            logger.error(f"[AVM.PHASE4] {domain}: deploy failed — {exc}")
            return False

    def _apply_thresholds_to_snapshot(
        self,
        domain: str,
        snapshot: "CalibrationSnapshot",
        thresholds: dict[str, float],
        description: str,
        tags: list[str],
    ) -> None:
        """Internal helper: write new thresholds to AVM snapshot store."""
        self.save_calibration_snapshot(
            domain=domain,
            baseline_signals=snapshot.baseline_signals,
            checkpoint_thresholds=thresholds,
            description=description,
            tags=tags,
        )

    def run_threshold_optimization_cycle(
        self,
        domain: str,
        lookback_days: int = 30,
        target_block_rate: float = 0.15,
        db_url: str | None = None,
    ) -> dict[str, Any]:
        """
        ADR-120 Phase 3 + 4: Full optimization cycle.

        Runs Phase 3 (analysis) and — if results are ready — Phase 4 (deployment).

        Returns a status dict with keys:
          phase3_complete, phase4_complete, optimized_thresholds, message
        """
        result: dict[str, Any] = {
            "domain":              domain,
            "phase3_complete":     False,
            "phase4_complete":     False,
            "optimized_thresholds": None,
            "message":             "",
        }

        optimized = self.optimize_checkpoint_thresholds(
            domain=domain,
            lookback_days=lookback_days,
            target_block_rate=target_block_rate,
            db_url=db_url,
        )

        if optimized is None:
            result["message"] = "Phase 3 skipped — insufficient data or no snapshot"
            return result

        result["phase3_complete"]      = True
        result["optimized_thresholds"] = optimized

        deployed = self.deploy_optimized_thresholds(
            domain=domain,
            optimized_thresholds=optimized,
            db_url=db_url,
        )

        result["phase4_complete"] = deployed
        result["message"] = (
            f"Phase 3 complete ({len(optimized)} thresholds optimized). "
            + ("Phase 4 deployed to live snapshot." if deployed else "Phase 4 deployment failed.")
        )
        logger.info(f"[AVM.OPT_CYCLE] {domain}: {result['message']}")
        return result


# ── Tenant-Isolated Instance Registry (ISR-001) ────────────────────────────────
#
# Replaced process-level singleton with a per-tenant registry.
# Each tenant_id gets its own AssumptionValidityMonitor instance with:
#   - Isolated in-memory calibration store (_memory_store)
#   - Isolated snapshot directory  (avm_snapshots/{tenant_id}/)
#   - Isolated last-seen signals   (_last_seen_signals)
#
# Backward compatibility: tenant_id='default' preserves all single-tenant
# deployments without any code change at call sites that don't pass tenant_id.
#
# For full DB-level isolation, see avm_db_bridge.py ISR-001 DDL_ALTER_TENANT_ID.

_avm_registry: dict[str, AssumptionValidityMonitor] = {}
_avm_registry_lock = threading.Lock()


def get_avm_instance(tenant_id: str = "default") -> AssumptionValidityMonitor:
    """
    Return the tenant-isolated AVM instance for tenant_id.

    Each tenant gets its own AssumptionValidityMonitor with isolated calibration
    state and snapshot directory. 'default' preserves single-tenant behavior.

    ISR-001: replaces process-level singleton to prevent cross-tenant
    calibration contamination in multi-tenant deployments.
    """
    global _avm_registry
    tenant_id = (tenant_id or "default").strip()
    if tenant_id not in _avm_registry:
        with _avm_registry_lock:
            if tenant_id not in _avm_registry:
                tenant_dir = AVM_SNAPSHOTS_DIR / tenant_id
                _avm_registry[tenant_id] = AssumptionValidityMonitor(
                    drift_threshold=float(
                        os.environ.get("AVM_DRIFT_THRESHOLD", str(AVM_DRIFT_THRESHOLD_DEFAULT))
                    ),
                    max_age_hours=float(
                        os.environ.get("AVM_MAX_AGE_HOURS", str(AVM_MAX_AGE_HOURS_DEFAULT))
                    ),
                    critical_age_hours=float(
                        os.environ.get("AVM_CRITICAL_AGE_HOURS", str(AVM_CRITICAL_AGE_HOURS_DEFAULT))
                    ),
                    snapshots_dir=tenant_dir,
                )
                logger.info(
                    f"[AVM][ISR-001] New tenant AVM instance created — "
                    f"tenant_id='{tenant_id}' "
                    f"snapshots_dir='{tenant_dir}'"
                )
    return _avm_registry[tenant_id]


def get_avm_registry_stats() -> dict:
    """Return summary of active tenant AVM instances (for admin/monitoring)."""
    return {
        "active_tenants": list(_avm_registry.keys()),
        "count": len(_avm_registry),
    }
