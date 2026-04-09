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
from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor
from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge

logger = logging.getLogger("OMNIX.AVM.Init")


DOMAIN_BASELINES = {
    "trading": {
        "signals": {
            "momentum_score":    65.0,
            "volume_score":      70.0,
            "volatility_score":  55.0,
            "macro_risk_score":  40.0,
            "liquidity_score":   72.0,
            "coherence_score":   78.0,
        },
        "description": "Baseline calibration — Q1 2026 moderate market conditions",
        "tags": ["initial", "q1-2026", "trading"],
    },
    "islamic_credit": {
        "signals": {
            "debt_coverage_ratio": 65.0,
            "gharar_score":        20.0,
            "liquidity_score":     68.0,
            "sectoral_risk":       40.0,
            "borrower_quality":    70.0,
            "macro_exposure":      38.0,
        },
        "description": "Baseline calibration — GCC Islamic credit market Q1 2026",
        "tags": ["initial", "q1-2026", "islamic-credit"],
    },
    "insurance": {
        "signals": {
            "fraud_probability":    20.0,
            "claimant_quality":     72.0,
            "evidence_completeness": 68.0,
            "policy_alignment":     74.0,
            "loss_ratio":           62.0,
            "claim_severity":       45.0,
        },
        "description": "Baseline calibration — insurance claims Q1 2026",
        "tags": ["initial", "q1-2026", "insurance"],
    },
    "robotics": {
        "signals": {
            "safety_score":       85.0,
            "compliance_score":   80.0,
            "risk_score":         22.0,
            "authorization_score": 78.0,
            "environmental_score": 72.0,
            "operational_score":  76.0,
        },
        "description": "Baseline calibration — robotics action governance Q1 2026",
        "tags": ["initial", "q1-2026", "robotics"],
    },
}


def initialize_avm_baselines(force: bool = False) -> dict[str, bool]:
    """
    Seed AVM calibration snapshots — enterprise persistence strategy:

    1. Ensure PostgreSQL table exists.
    2. Restore existing snapshots from DB → local JSON files.
    3. Seed only missing domains (first-time-only seeding).
    4. Persist new seeds to DB immediately.

    Args:
        force: If True, overwrite existing DB baselines (use only for manual recalibration).
               WARNING: force=True resets the drift detection baseline — use with intent.

    Returns:
        dict of {domain: seeded (True/False)}
    """
    bridge = AVMDatabaseBridge()
    avm = AssumptionValidityMonitor()
    results = {}

    # Step 1: Ensure DB table exists
    if bridge.is_available():
        bridge.ensure_table()

        # Step 2: Restore DB snapshots to local JSON (no-op if DB empty)
        restored = bridge.restore_to_json()
        if restored > 0:
            logger.info(f"[AVM.Init] Restored {restored} snapshots from PostgreSQL → local JSON")
    else:
        logger.warning("[AVM.Init] No DATABASE_URL — using JSON-only persistence (not recommended for production)")

    # Step 3: Seed only missing domains
    for domain, cfg in DOMAIN_BASELINES.items():
        existing_in_db = False
        if bridge.is_available() and not force:
            all_db = bridge.load_all_snapshots()
            existing_in_db = domain in all_db

        if existing_in_db:
            logger.info(f"[AVM.Init] Domain '{domain}' exists in DB — no recalibration (drift baseline preserved)")
            results[domain] = False
            continue

        existing_local = avm.load_snapshot(domain)
        if existing_local and not force:
            # Has local JSON but not in DB — persist it to DB now
            if bridge.is_available():
                snap_dict = {
                    "domain":             domain,
                    "snapshot_id":        existing_local.snapshot_id,
                    "parameter_version":  existing_local.parameter_version,
                    "baseline_signals":   existing_local.baseline_signals,
                    "checkpoint_thresholds": existing_local.checkpoint_thresholds,
                    "drift_threshold":    existing_local.drift_threshold,
                    "max_age_hours":      existing_local.max_age_hours,
                    "description":        existing_local.description,
                    "tags":               existing_local.tags,
                    "calibrated_at":      existing_local.calibrated_at,
                    "calibrated_at_epoch": existing_local.calibrated_at_epoch,
                }
                bridge.save_snapshot(snap_dict)
                logger.info(f"[AVM.Init] Domain '{domain}' migrated from JSON → PostgreSQL")
            results[domain] = False
            continue

        # New seed (domain not found anywhere)
        avm.save_calibration_snapshot(
            domain=domain,
            baseline_signals=cfg["signals"],
            description=cfg["description"],
            tags=cfg["tags"],
        )
        # Persist new seed to DB
        if bridge.is_available():
            new_snap = avm.load_snapshot(domain)
            if new_snap:
                snap_dict = {
                    "domain":             domain,
                    "snapshot_id":        new_snap.snapshot_id,
                    "parameter_version":  new_snap.parameter_version,
                    "baseline_signals":   new_snap.baseline_signals,
                    "checkpoint_thresholds": new_snap.checkpoint_thresholds,
                    "drift_threshold":    new_snap.drift_threshold,
                    "max_age_hours":      new_snap.max_age_hours,
                    "description":        new_snap.description,
                    "tags":               new_snap.tags,
                    "calibrated_at":      new_snap.calibrated_at,
                    "calibrated_at_epoch": new_snap.calibrated_at_epoch,
                }
                bridge.save_snapshot(snap_dict)

        results[domain] = True
        logger.info(f"[AVM.Init] ✅ Domain '{domain}' calibrated and persisted to PostgreSQL")

    seeded = sum(results.values())
    logger.info(f"[AVM.Init] Initialization complete — {seeded}/{len(DOMAIN_BASELINES)} domains seeded")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    initialize_avm_baselines()
