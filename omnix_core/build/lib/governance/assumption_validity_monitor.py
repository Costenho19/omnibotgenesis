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
from typing import Any

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

    def to_dict(self) -> dict[str, Any]:
        return {
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
            )

        logger.debug(
            f"[AVM] VALID — domain={domain} | drift={drift_score:.1f} ≤ {effective_threshold:.1f} | "
            f"age={age_hours:.1f}h | snapshot={snapshot.snapshot_id}"
        )
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


# ── Singleton ──────────────────────────────────────────────────────────────────

_avm_instance: AssumptionValidityMonitor | None = None


def get_avm_instance() -> AssumptionValidityMonitor:
    """Return the process-level singleton AVM instance."""
    global _avm_instance
    if _avm_instance is None:
        _avm_instance = AssumptionValidityMonitor(
            drift_threshold=float(
                os.environ.get("AVM_DRIFT_THRESHOLD", str(AVM_DRIFT_THRESHOLD_DEFAULT))
            ),
            max_age_hours=float(
                os.environ.get("AVM_MAX_AGE_HOURS", str(AVM_MAX_AGE_HOURS_DEFAULT))
            ),
            critical_age_hours=float(
                os.environ.get("AVM_CRITICAL_AGE_HOURS", str(AVM_CRITICAL_AGE_HOURS_DEFAULT))
            ),
        )
    return _avm_instance
