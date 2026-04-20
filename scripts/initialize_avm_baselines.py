"""
Initialize AVM (Assumption Validity Monitor) calibration snapshots for all domains.
ADR-074: AVM DB Persistence — PostgreSQL as source of truth.

Strategy (enterprise-grade):
  1. Ensure avm_calibration_snapshots table exists in PostgreSQL.
  2. Restore any existing DB snapshots to local JSON (so AVM can read them).
  3. Seed ONLY domains that are missing from the DB (first run only).
  4. Never overwrite existing DB baselines — avoids the "auto-forgiveness" bug
     where the system redefines "normal" on every restart, killing drift detection.

Called automatically by the Flask dashboard on startup.
"""
import logging
import os
from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor
from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge

logger = logging.getLogger("OMNIX.AVM.Init")


# IMPORTANT: Signal keys MUST match SIGNAL_WEIGHTS in assumption_validity_monitor.py
# Keys: probability_score, signal_coherence, risk_exposure, stress_resilience,
#       trend_persistence, logic_consistency
# Values: calibrated from real decision averages in DB (2026-04-20)
DOMAIN_BASELINES = {
    "trading": {
        "signals": {
            "probability_score":  65.0,
            "signal_coherence":   72.0,
            "risk_exposure":      32.0,
            "stress_resilience":  60.0,
            "trend_persistence":  58.0,
            "logic_consistency":  78.0,
        },
        "description": "Baseline calibration — trading governance Q2 2026 (SIGNAL_WEIGHTS keys)",
        "tags": ["initial", "q2-2026", "trading"],
    },
    "islamic_credit": {
        "signals": {
            "probability_score":  68.0,
            "signal_coherence":   74.0,
            "risk_exposure":      28.0,
            "stress_resilience":  66.0,
            "trend_persistence":  55.0,
            "logic_consistency":  70.0,
        },
        "description": "Baseline calibration — Islamic credit market Q2 2026 (SIGNAL_WEIGHTS keys)",
        "tags": ["initial", "q2-2026", "islamic-credit"],
    },
    "insurance": {
        "signals": {
            "probability_score":  64.7,
            "signal_coherence":   77.0,
            "risk_exposure":      37.8,
            "stress_resilience":  73.9,
            "trend_persistence":  41.4,
            "logic_consistency":  58.0,
        },
        "description": "Baseline calibration — insurance claims Q2 2026 (avg 40,307 claims, SIGNAL_WEIGHTS keys)",
        "tags": ["initial", "q2-2026", "insurance"],
    },
    "robotics": {
        "signals": {
            "probability_score":  66.1,
            "signal_coherence":   83.0,
            "risk_exposure":      39.7,
            "stress_resilience":  62.5,
            "trend_persistence":  63.5,
            "logic_consistency":  72.3,
        },
        "description": "Baseline calibration — robotics governance Q2 2026 (avg 59,348 actions, SIGNAL_WEIGHTS keys)",
        "tags": ["initial", "q2-2026", "robotics"],
    },
    "medical_ai": {
        "signals": {
            "probability_score":  75.5,
            "signal_coherence":   71.4,
            "risk_exposure":      51.3,
            "stress_resilience":  64.2,
            "trend_persistence":  59.3,
            "logic_consistency":  57.5,
        },
        "description": "Baseline calibration — medical AI governance Q2 2026 (avg 21,683 decisions, SIGNAL_WEIGHTS keys)",
        "tags": ["initial", "q2-2026", "medical"],
    },
    "energy_governance": {
        "signals": {
            "probability_score":  61.1,
            "signal_coherence":   71.1,
            "risk_exposure":      25.3,
            "stress_resilience":  65.7,
            "trend_persistence":  70.7,
            "logic_consistency":  82.1,
        },
        "description": "Baseline calibration — energy grid governance Q2 2026 (avg 26,125 decisions, SIGNAL_WEIGHTS keys)",
        "tags": ["initial", "q2-2026", "energy"],
    },
    "real_estate": {
        "signals": {
            "probability_score":  69.8,
            "signal_coherence":   62.8,
            "risk_exposure":      19.9,
            "stress_resilience":  60.4,
            "trend_persistence":  63.8,
            "logic_consistency":  86.6,
        },
        "description": "Baseline calibration — real estate governance Q2 2026 (avg 13,245 decisions, SIGNAL_WEIGHTS keys)",
        "tags": ["initial", "q2-2026", "real-estate"],
    },
    "autonomous_agent": {
        "signals": {
            "probability_score":  50.1,
            "signal_coherence":   66.7,
            "risk_exposure":      50.2,
            "stress_resilience":  65.9,
            "trend_persistence":  71.7,
            "logic_consistency":  46.8,
        },
        "description": "Baseline calibration — autonomous agent governance Q2 2026 (avg 20,549 decisions, SIGNAL_WEIGHTS keys)",
        "tags": ["initial", "q2-2026", "agents"],
    },
    "stablecoin": {
        "signals": {
            "probability_score":  75.1,
            "signal_coherence":   83.2,
            "risk_exposure":      14.3,
            "stress_resilience":  69.3,
            "trend_persistence":  63.9,
            "logic_consistency":  67.0,
        },
        "description": "Baseline calibration — stablecoin reserve governance Q2 2026 (avg 1,385 decisions, SIGNAL_WEIGHTS keys)",
        "tags": ["initial", "q2-2026", "stablecoin"],
    },
}


def initialize_avm_baselines(
    force: bool = False,
    reason: str = "",
    actor: str = "system",
) -> dict[str, bool]:
    """
    Seed AVM calibration snapshots — enterprise persistence strategy:

    1. Ensure PostgreSQL tables exist (snapshots + change_log).
    2. Restore existing snapshots from DB → local JSON files (integrity-checked).
    3. Seed only missing domains (first-time-only seeding).
    4. Persist new seeds to DB with hash + change log entry.

    Args:
        force:  If True, overwrite existing DB baselines (recalibration).
                WARNING: force=True resets drift detection baseline — use with intent.
        reason: Required when force=True. Documented reason for recalibration.
        actor:  Who triggered this change (for audit log).

    Returns:
        dict of {domain: seeded (True/False)}

    Raises:
        ValueError: If force=True and reason is empty.
    """
    if force and not reason.strip():
        raise ValueError(
            "reason is required when force=True. "
            "Document why you are resetting the drift detection baseline. "
            "Example: initialize_avm_baselines(force=True, reason='Market regime change Q2 2026')"
        )

    # Fail-closed policy: AVM_FAIL_CLOSED=true means halt if DB/tamper issues
    # Default: false (pass-through warning) for resilience in production trading
    fail_closed = os.environ.get("AVM_FAIL_CLOSED", "false").lower() == "true"

    bridge = AVMDatabaseBridge()
    avm = AssumptionValidityMonitor()
    results = {}
    degraded_domains: list[str] = []

    # Step 1: Ensure DB tables exist
    if bridge.is_available():
        bridge.ensure_table()

        # Step 2: Restore DB snapshots → local JSON (integrity-checked)
        restored, tampered = bridge.restore_to_json()
        if restored > 0:
            logger.info(f"[AVM.Init] Restored {restored} snapshots from PostgreSQL → local JSON")
        if tampered > 0:
            logger.error(
                f"[AVM.Init] ⚠️ DEGRADED_MODE: {tampered} tampered snapshots rejected — "
                "those domains will operate in AVM pass-through until recalibrated"
            )
            degraded_domains.append(f"{tampered}_tampered_domains")
            if fail_closed:
                raise RuntimeError(
                    f"[AVM.Init] FAIL-CLOSED: {tampered} tampered baseline(s) detected. "
                    "Execution halted — recalibrate with initialize_avm_baselines(force=True, reason=...) "
                    "to restore governance integrity."
                )
    else:
        logger.warning(
            "[AVM.Init] DEGRADED_MODE: No DATABASE_URL — "
            "using JSON-only persistence (not recommended for production). "
            "Drift baselines will not survive container restarts."
        )
        if fail_closed:
            raise RuntimeError(
                "[AVM.Init] FAIL-CLOSED: DATABASE_URL not set. "
                "AVM cannot verify baseline integrity without PostgreSQL. "
                "Set DATABASE_URL or set AVM_FAIL_CLOSED=false to allow pass-through."
            )

    # Step 3: Load DB state once for efficiency
    all_db: dict = {}
    if bridge.is_available():
        all_db = bridge.load_all_snapshots()

    # Step 4: Seed only missing domains (or all if force=True)
    for domain, cfg in DOMAIN_BASELINES.items():
        existing_in_db = domain in all_db and all_db[domain].get("integrity_status") == "OK"

        if existing_in_db and not force:
            logger.info(
                f"[AVM.Init] Domain '{domain}' exists in DB (integrity=OK) — "
                "no recalibration (drift baseline preserved)"
            )
            results[domain] = False
            continue

        existing_local = avm.load_snapshot(domain)

        if existing_local and not force and not existing_in_db:
            # Has valid local JSON but missing from DB — migrate it
            if bridge.is_available():
                snap_dict = _snapshot_to_dict(domain, existing_local)
                bridge.save_snapshot(
                    snap_dict,
                    reason="Migrated from local JSON to PostgreSQL",
                    actor=actor,
                    action="MIGRATE",
                )
                logger.info(f"[AVM.Init] Domain '{domain}' migrated from JSON → PostgreSQL")
            results[domain] = False
            continue

        # New seed or forced recalibration
        action = "RECALIBRATE" if force else "SEED"
        seed_reason = reason if force else f"Initial calibration — {cfg['description']}"

        avm.save_calibration_snapshot(
            domain=domain,
            baseline_signals=cfg["signals"],
            description=cfg["description"],
            tags=cfg["tags"],
        )

        if bridge.is_available():
            new_snap = avm.load_snapshot(domain)
            if new_snap:
                snap_dict = _snapshot_to_dict(domain, new_snap)
                bridge.save_snapshot(
                    snap_dict,
                    reason=seed_reason,
                    actor=actor,
                    action=action,
                )

        results[domain] = True
        logger.info(f"[AVM.Init] ✅ Domain '{domain}' calibrated — action={action}")

    seeded = sum(results.values())
    logger.info(f"[AVM.Init] Initialization complete — {seeded}/{len(DOMAIN_BASELINES)} domains seeded")
    if degraded_domains:
        logger.warning(f"[AVM.Init] DEGRADED_MODE active — {degraded_domains}")
    return results


def _snapshot_to_dict(domain: str, snap) -> dict:
    return {
        "domain":             domain,
        "snapshot_id":        snap.snapshot_id,
        "parameter_version":  snap.parameter_version,
        "baseline_signals":   snap.baseline_signals,
        "checkpoint_thresholds": snap.checkpoint_thresholds,
        "drift_threshold":    snap.drift_threshold,
        "max_age_hours":      snap.max_age_hours,
        "description":        snap.description,
        "tags":               snap.tags,
        "calibrated_at":      snap.calibrated_at,
        "calibrated_at_epoch": snap.calibrated_at_epoch,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    initialize_avm_baselines()
