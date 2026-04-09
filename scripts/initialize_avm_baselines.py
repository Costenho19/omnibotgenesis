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
