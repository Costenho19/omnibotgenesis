"""
Initialize AVM (Assumption Validity Monitor) calibration snapshots for all domains.
Run this once at system startup to arm drift detection.
Called automatically by the Flask dashboard on first boot if snapshots are missing.
"""
import logging
from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor

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
    Seed AVM calibration snapshots for all domains.
    Skips domains that already have a valid snapshot unless force=True.

    Returns dict of {domain: seeded (True/False)}.
    """
    avm = AssumptionValidityMonitor()
    results = {}

    for domain, cfg in DOMAIN_BASELINES.items():
        existing = avm.load_snapshot(domain)
        if existing and not force:
            logger.info(f"[AVM.Init] Domain '{domain}' already calibrated — skipping (use force=True to recalibrate)")
            results[domain] = False
            continue

        avm.save_calibration_snapshot(
            domain=domain,
            baseline_signals=cfg["signals"],
            description=cfg["description"],
            tags=cfg["tags"],
        )
        results[domain] = True
        logger.info(f"[AVM.Init] ✅ Domain '{domain}' calibrated successfully")

    seeded = sum(results.values())
    logger.info(f"[AVM.Init] Initialization complete — {seeded}/{len(DOMAIN_BASELINES)} domains seeded")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    initialize_avm_baselines()
