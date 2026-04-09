"""
OMNIX Assumption Validity Monitor (AVM)
ADR-064: Assumption Validity Monitor — Calibration Drift Detection

Solves the core critique of governance under Knightian uncertainty:
OMNIX can certify a decision correctly given its calibrated parameters,
but those parameters may have been calibrated under conditions that no
longer hold. This module detects when the gap between calibration
conditions and current conditions has grown too wide to trust any
certification issued by the pipeline.

Architecture position:
    Signals → AVM (ADR-064) → CAG (ADR-050) → 11 Checkpoints → TIE (ADR-053) → Decision
              [STALE_BLOCK]

Key principle:
    A governance receipt is only as valid as the assumptions it was
    certified under. If those assumptions have drifted beyond a tolerance
    threshold, the pipeline must refuse to certify — regardless of whether
    the incoming signals would otherwise pass all checkpoints.

Parameter Versioning:
    Every calibration snapshot receives a unique version ID embedded in
    the resulting governance receipts. If a snapshot is later invalidated,
    all receipts issued under it can be traced and flagged.

Storage: JSON snapshots in `avm_snapshots/` directory (one per domain).
         Falls back to in-memory storage when filesystem unavailable.
Fail-safe: AVM exceptions → pass-through (pipeline availability preserved).
Enabled via: AVM_ENABLED env var (default: true).

Responds directly to:
    - Ioana V. (PhD Decision Architect): "Who detects when underlying
      conditions change?"
    - Jennifer's Knightian uncertainty critique: "What happens when OMNIX
      certifies under assumptions that are no longer valid?"

Harold Nunes — OMNIX Decision Governance Infrastructure
Build 6.5.5 | ADR-064 | April 2026
"""

from __future__ import annotations

import json
import logging
import os
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

# Signal weights for drift computation (must sum to 1.0).
# Higher weight = that signal's drift contributes more to total drift score.
SIGNAL_WEIGHTS: dict[str, float] = {
    "probability_score":  0.25,
    "signal_coherence":   0.25,
    "risk_exposure":      0.20,
    "stress_resilience":  0.15,
    "trend_persistence":  0.10,
    "logic_consistency":  0.05,
}


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
        """
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
