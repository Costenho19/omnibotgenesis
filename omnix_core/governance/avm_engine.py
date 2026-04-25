"""
OMNIX AVMEngine — High-level façade over AssumptionValidityMonitor (ADR-120).

Provides a clean API for external callers (audit suites, scheduled jobs,
admin endpoints) that need to:
  - Query which domains are stale or drifting beyond calibration limits.
  - Trigger auto-recalibration without touching internal AVM state.

This module does NOT duplicate logic from assumption_validity_monitor.py.
All decisions (drift computation, safety guards, persistence) remain there.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("OMNIX.AVMEngine")


class AVMEngine:
    """
    ADR-120: High-level engine for AVM governance operations.

    Wraps the AssumptionValidityMonitor singleton and the AVMDatabaseBridge
    to expose a minimal, auditor-friendly interface.

    Usage:
        engine = AVMEngine()
        stale = engine.get_stale_domains()          # e.g. ['islamic_credit', 'trading']
        if stale:
            recalibrated = engine.auto_recalibrate_stale_domains()
    """

    def __init__(
        self,
        recalib_interval_hours: float = 72.0,
        drift_threshold: float | None = None,
        max_drift_for_auto: float = 80.0,
    ) -> None:
        self._recalib_interval_hours = recalib_interval_hours
        self._max_drift_for_auto = max_drift_for_auto
        # drift_threshold=None → use AVM's own configured threshold
        self._drift_threshold_override = drift_threshold

    def _get_avm(self):
        from omnix_core.governance.assumption_validity_monitor import get_avm_instance
        return get_avm_instance()

    def _get_bridge(self):
        db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        if not db_url:
            return None
        try:
            from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge
            return AVMDatabaseBridge(db_url=db_url)
        except Exception as exc:
            logger.warning(f"[AVMEngine] DB bridge unavailable: {exc}")
            return None

    def get_stale_domains(
        self,
        recalib_interval_hours: float | None = None,
    ) -> list[str]:
        """
        Return list of domain names that need recalibration because:
          - Snapshot age >= recalib_interval_hours (default 72h), OR
          - Drift score >= drift_threshold (DRIFT_BLOCK condition).

        Checks three sources in order: memory store, disk snapshots, DB.
        DB snapshots are used directly (age from calibrated_at_epoch) when
        the domain is not in memory or on disk — this handles the case where
        the server has not yet loaded snapshots from DB into memory.

        Args:
            recalib_interval_hours: Age threshold in hours. Defaults to 72h.

        Returns:
            Sorted list of domain names requiring recalibration.
        """
        import time as _time
        interval = recalib_interval_hours or self._recalib_interval_hours
        avm = self._get_avm()
        threshold = self._drift_threshold_override or avm.drift_threshold
        stale: list[str] = []
        now = _time.time()

        # Source 1 + 2: memory store and disk files
        domains_local: set[str] = set(avm._memory_store.keys())
        try:
            for p in avm._snapshots_dir.glob("*_calibration.json"):
                domains_local.add(p.stem.replace("_calibration", ""))
        except Exception as _e:
            logger.debug(f"[AVMEngine] get_stale_domains: disk glob failed (dir may not exist yet): {_e}")

        for domain in sorted(domains_local):
            try:
                snapshot = avm.load_snapshot(domain)
                if snapshot is None:
                    continue
                age_hours = snapshot.age_hours()
                if age_hours >= interval:
                    logger.debug(f"[AVMEngine] {domain}: stale age={age_hours:.0f}h >= {interval:.0f}h")
                    stale.append(domain)
                    continue
                # Check drift vs cached live signals
                with avm._last_seen_lock:
                    live_signals = avm._last_seen_signals.get(domain)
                if live_signals is not None:
                    drift_score, _ = avm._compute_drift(snapshot.baseline_signals, live_signals)
                    if drift_score >= threshold:
                        logger.debug(f"[AVMEngine] {domain}: DRIFT_BLOCK drift={drift_score:.1f}%")
                        stale.append(domain)
            except Exception as exc:
                logger.warning(f"[AVMEngine] local check {domain}: {exc}")

        # Source 3: DB snapshots — for domains not already found in memory/disk
        bridge = self._get_bridge()
        if bridge:
            try:
                db_snaps = bridge.load_all_snapshots()   # dict[str, dict]
                for domain, snap_data in db_snaps.items():
                    if domain in domains_local or domain in stale:
                        continue  # already handled above
                    try:
                        epoch = snap_data.get("calibrated_at_epoch")
                        if epoch is None:
                            continue
                        age_hours = (now - float(epoch)) / 3600.0
                        if age_hours >= interval:
                            logger.debug(
                                f"[AVMEngine] {domain} (DB-only): stale age={age_hours:.0f}h"
                            )
                            stale.append(domain)
                    except Exception as exc2:
                        logger.debug(f"[AVMEngine] DB domain {domain}: {exc2}")
            except Exception as exc:
                logger.debug(f"[AVMEngine] DB snapshot list failed: {exc}")

        stale_sorted = sorted(set(stale))
        logger.info(
            f"[AVMEngine] get_stale_domains(interval={interval:.0f}h) → "
            f"{len(stale_sorted)} stale: {stale_sorted}"
        )
        return stale_sorted

    def auto_recalibrate_stale_domains(
        self,
        recalib_interval_hours: float | None = None,
        max_drift_for_auto: float | None = None,
    ) -> list[str]:
        """
        Auto-recalibrate all stale or drifted domains using live cached signals.

        Delegates entirely to AssumptionValidityMonitor.auto_recalibrate_stale_domains()
        so all safety guards and persistence logic remain in the canonical location.

        Returns:
            List of domain names that were successfully recalibrated.
        """
        interval = recalib_interval_hours or self._recalib_interval_hours
        max_drift = max_drift_for_auto or self._max_drift_for_auto
        avm = self._get_avm()
        logger.info(
            f"[AVMEngine] auto_recalibrate_stale_domains("
            f"interval={interval:.0f}h, max_drift_for_auto={max_drift:.0f}%)"
        )
        return avm.auto_recalibrate_stale_domains(
            recalib_interval_hours=interval,
            max_drift_for_auto=max_drift,
        )

    def get_avm_status(self) -> dict[str, Any]:
        """
        Return a summary of all AVM domains and their current health.
        Useful for /api/governance/avm-status and audit reports.
        """
        avm = self._get_avm()
        status: dict[str, Any] = {
            "drift_threshold": avm.drift_threshold,
            "max_age_hours": avm.max_age_hours,
            "recalib_interval_hours": self._recalib_interval_hours,
            "domains": {},
        }

        domains: set[str] = set(avm._memory_store.keys())
        try:
            for p in avm._snapshots_dir.glob("*_calibration.json"):
                domains.add(p.stem.replace("_calibration", ""))
        except Exception as _e:
            logger.debug(f"[AVMEngine] get_avm_status: disk glob failed (dir may not exist yet): {_e}")

        for domain in sorted(domains):
            try:
                snapshot = avm.load_snapshot(domain)
                if snapshot is None:
                    continue
                with avm._last_seen_lock:
                    live_signals = avm._last_seen_signals.get(domain)
                drift_vs_live: float | None = None
                if live_signals:
                    drift_vs_live, _ = avm._compute_drift(
                        snapshot.baseline_signals, live_signals
                    )
                status["domains"][domain] = {
                    "snapshot_id": snapshot.snapshot_id,
                    "age_hours": round(snapshot.age_hours(), 1),
                    "drift_vs_live": round(drift_vs_live, 1) if drift_vs_live is not None else None,
                    "has_live_signals": live_signals is not None,
                    "tags": snapshot.tags,
                }
            except Exception as exc:
                status["domains"][domain] = {"error": str(exc)}

        return status
