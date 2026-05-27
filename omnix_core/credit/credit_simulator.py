"""
OMNIX Islamic Credit Governance Simulator
ADR-052: Islamic Credit Governance Vertical

Runs 24/7 generating realistic Islamic finance credit applications and evaluating
them through the OMNIX 11-checkpoint governance pipeline. Stores results in
PostgreSQL with PQC-signed receipts — identical to the trading engine flow.

Cycle interval: 300 seconds (5 minutes) — realistic credit review cadence.
Each cycle processes a batch of 3-8 applications.

Simulation is calibrated to UAE/GCC Islamic finance market:
  - SME financing: AED 100K – 5M (60% of applications)
  - Individual financing: AED 50K – 500K (30%)
  - Corporate financing: AED 1M – 50M (10%)
  - Sectors: technology, real estate, healthcare, retail, F&B, manufacturing
  - Financing types: Murabaha (60%), Ijara (20%), Musharaka (15%), Diminishing (5%)
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import time
import uuid
from dataclasses import asdict
from typing import Optional

logger = logging.getLogger("OMNIX.Credit.Simulator")

CYCLE_INTERVAL = 300.0       # 5 minutes between cycles
BATCH_SIZE_MIN = 3
BATCH_SIZE_MAX = 8

# UAE/GCC Islamic finance market calibration
APPLICANT_TYPES = [
    ("SME", 0.60),
    ("Individual", 0.30),
    ("Corporate", 0.10),
]

SECTORS = [
    ("technology", 0.18),
    ("real_estate", 0.20),
    ("healthcare", 0.12),
    ("retail", 0.15),
    ("food_beverage", 0.10),
    ("manufacturing", 0.08),
    ("logistics", 0.07),
    ("education", 0.05),
    ("construction", 0.05),
]

FINANCING_TYPES = [
    ("Murabaha", 0.60),          # Cost-plus financing — most common
    ("Ijara", 0.20),             # Lease-to-own
    ("Musharaka", 0.15),         # Partnership/equity sharing
    ("Diminishing_Musharaka", 0.05),  # Declining partnership
]

COLLATERAL_TYPES = [
    ("property", 0.50),
    ("equipment", 0.20),
    ("inventory", 0.15),
    ("guarantee", 0.10),
    ("gold", 0.05),
]

PURPOSE_BY_TYPE = {
    "SME": [
        "Working capital expansion",
        "Equipment purchase",
        "Inventory financing",
        "Business premises acquisition",
        "Export financing",
        "Technology infrastructure",
    ],
    "Individual": [
        "Home purchase (Murabaha)",
        "Vehicle financing (Ijara)",
        "Personal development",
        "Medical expenses",
        "Education financing",
    ],
    "Corporate": [
        "Capital expenditure",
        "Acquisition financing",
        "Project financing",
        "Trade finance facility",
        "Sukuk issuance support",
    ],
}

AMOUNT_RANGES = {
    "SME": (100_000, 5_000_000),
    "Individual": (50_000, 500_000),
    "Corporate": (1_000_000, 50_000_000),
}

TENOR_RANGES = {
    "SME": (12, 84),           # 1-7 years
    "Individual": (6, 300),    # 6 months - 25 years (home)
    "Corporate": (24, 120),    # 2-10 years
}


def _weighted_choice(choices: list[tuple]) -> str:
    """Select a value from weighted choices list."""
    values, weights = zip(*choices)
    r = random.random()
    cumulative = 0.0
    for v, w in zip(values, weights):
        cumulative += w
        if r <= cumulative:
            return v
    return values[-1]


def generate_credit_application(macro_stress: float = 30.0) -> "CreditApplication":
    """
    Generate a realistic Islamic finance credit application.

    Parameters are calibrated to UAE market data with some randomness.
    Macro stress level influences the distribution of applicant quality.
    """
    from omnix_core.credit.credit_signal_adapter import CreditApplication

    applicant_type = _weighted_choice(APPLICANT_TYPES)
    sector = _weighted_choice(SECTORS)
    financing_type = _weighted_choice(FINANCING_TYPES)
    collateral_type = _weighted_choice(COLLATERAL_TYPES)

    # Amount and tenor
    amt_min, amt_max = AMOUNT_RANGES[applicant_type]
    requested_amount = round(random.uniform(amt_min, amt_max), -3)  # Round to nearest 1000

    tenor_min, tenor_max = TENOR_RANGES[applicant_type]
    tenor_months = random.randint(tenor_min, tenor_max)

    # Credit quality distribution — skewed by macro stress
    # Higher stress = more applications from borderline borrowers
    stress_factor = macro_stress / 100.0
    base_cs_mean = 680.0 - stress_factor * 80.0
    credit_score = round(random.gauss(base_cs_mean, 75.0))
    credit_score = max(300, min(850, credit_score))

    # DSR — correlated with credit score and macro
    base_dsr = 0.38 - (credit_score - 500) / 3500.0 + stress_factor * 0.05
    debt_service_ratio = round(max(0.05, min(0.75, base_dsr + random.gauss(0, 0.06))), 3)

    # Asset backing — correlated with applicant quality
    base_abr = 1.10 + (credit_score - 500) / 1400.0
    asset_backing_ratio = round(max(0.30, min(2.50, base_abr + random.gauss(0, 0.20))), 2)

    # Annual revenue
    base_rev = requested_amount * random.uniform(0.4, 4.0)
    annual_revenue = round(base_rev, -3)

    # Existing obligations
    existing_obligations = round((annual_revenue / 12) * debt_service_ratio * 0.5, 2)

    # Gharar score — uncertainty in contract
    base_gharar = 30.0 + stress_factor * 20.0
    gharar_score = round(max(5.0, min(95.0, random.gauss(base_gharar, 15.0))), 1)

    # Occasionally inject borderline/failing applications for realism
    if random.random() < 0.08:  # 8% are clearly poor quality
        credit_score = random.randint(300, 430)
        debt_service_ratio = round(random.uniform(0.45, 0.75), 3)
        gharar_score = round(random.uniform(65.0, 90.0), 1)

    purpose = random.choice(PURPOSE_BY_TYPE[applicant_type])

    app_id = f"ICF-{int(time.time())}-{uuid.uuid4().hex[:8].upper()}"

    return CreditApplication(
        application_id=app_id,
        applicant_type=applicant_type,
        sector=sector,
        requested_amount=requested_amount,
        tenor_months=tenor_months,
        financing_type=financing_type,
        purpose=purpose,
        currency="AED",
        credit_score=float(credit_score),
        debt_service_ratio=debt_service_ratio,
        asset_backing_ratio=asset_backing_ratio,
        collateral_type=collateral_type,
        annual_revenue=annual_revenue,
        existing_obligations=existing_obligations,
        is_halal_sector=True,
        riba_free=True,
        gharar_score=gharar_score,
    )


async def evaluate_credit_application(app, macro) -> Optional[dict]:
    """
    Run a single credit application through the OMNIX governance pipeline.
    Returns the full evaluation result including the receipt.
    """
    from omnix_core.credit.credit_signal_adapter import CreditSignalAdapter
    from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine

    adapter = CreditSignalAdapter()
    engine = GovernanceEvaluationEngine()

    try:
        # Step 1: Adapt credit parameters to OMNIX signals
        signals = adapter.adapt(app, macro)
        signal_dict = signals.to_dict()

        # Step 2: Run through the 11-checkpoint governance pipeline
        result = engine.evaluate(
            signals=signal_dict,
            asset=f"{app.financing_type}:{app.sector.upper()}:{app.currency}",
            domain="islamic_credit",
            metadata={
                "applicant_type": app.applicant_type,
                "requested_amount": app.requested_amount,
                "currency": app.currency,
                "tenor_months": app.tenor_months,
                "financing_type": app.financing_type,
                "sector": app.sector,
                "sharia_compliant": signals.sharia_compliant,
                "sharia_violation": signals.sharia_violation,
                "pd_estimate": signals.pd_estimate,
                "lgd_estimate": signals.lgd_estimate,
                "application_id": app.application_id,
                "engine_vertical": "islamic_credit_v1",
            },
            compliance_config={
                "sharia_enabled": True,
                "sharia_sector": app.sector,
                "sharia_gharar": app.gharar_score,
                "sharia_debt_ratio": app.debt_service_ratio,
                "cag_liquidity_score": 75.0,
            },
        )

        # Step 3: Determine if Sharia compliance blocks the decision
        final_decision = result.get("decision", "BLOCKED")
        block_reason = None
        blocked_at = None

        if not signals.sharia_compliant and final_decision != "BLOCKED":
            final_decision = "BLOCKED"
            block_reason = f"Sharia: {signals.sharia_violation}"
            blocked_at = "CP-SHARIA"
        elif final_decision == "BLOCKED":
            veto_chain = result.get("veto_chain", [])
            if veto_chain:
                first_veto = veto_chain[0] if isinstance(veto_chain[0], dict) else {}
                blocked_at = first_veto.get("checkpoint_id", "CP-?")
                block_reason = first_veto.get("reason", "Governance threshold breach")

        result["final_decision"] = final_decision
        result["block_reason"] = block_reason
        result["blocked_at"] = blocked_at
        result["application"] = app
        result["signals"] = signals

        return result

    except Exception as e:
        logger.error(f"[CreditSim] Error evaluating {app.application_id}: {e}")
        return None


async def save_credit_result(result: dict, macro, conn) -> None:
    """Persist the governance decision to PostgreSQL."""
    app = result["application"]
    signals = result["signals"]
    receipt_id = result.get("receipt_id") or result.get("metadata", {}).get("receipt_id")

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO credit_applications (
                application_id, submitted_at, evaluated_at,
                applicant_type, sector, country,
                requested_amount, currency, tenor_months,
                financing_type, purpose,
                credit_score, debt_service_ratio, asset_backing_ratio,
                collateral_type, annual_revenue, existing_obligations,
                is_halal_sector, sharia_compliant, gharar_score, riba_free,
                signal_probability_score, signal_risk_exposure,
                signal_coherence, signal_trend_persistence,
                signal_stress_resilience, signal_logic_consistency,
                signal_integrity, signal_temporal_coherence,
                macro_credit_index, macro_volatility, macro_stress_level, fed_funds_rate,
                decision, receipt_id, blocked_at_checkpoint, block_reason,
                checkpoints_passed, checkpoints_total, decision_confidence,
                simulation_run, data_source
            ) VALUES (
                %s, NOW(), NOW(),
                %s, %s, 'UAE',
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                TRUE, 'simulator'
            )
            ON CONFLICT (application_id) DO NOTHING
        """, (
            app.application_id,
            app.applicant_type, app.sector,
            app.requested_amount, app.currency, app.tenor_months,
            app.financing_type, app.purpose,
            app.credit_score, app.debt_service_ratio, app.asset_backing_ratio,
            app.collateral_type, app.annual_revenue, app.existing_obligations,
            app.is_halal_sector, signals.sharia_compliant, app.gharar_score, app.riba_free,
            signals.probability_score, signals.risk_exposure,
            signals.signal_coherence, signals.trend_persistence,
            signals.stress_resilience, signals.logic_consistency,
            signals.signal_integrity, signals.temporal_coherence,
            macro.credit_conditions_index, macro.macro_volatility,
            macro.stress_level, macro.fed_funds_rate,
            result["final_decision"], receipt_id,
            result.get("blocked_at"), result.get("block_reason"),
            result.get("checkpoints_passed", 0), result.get("checkpoints_total", 11),
            result.get("decision_confidence", 0.0),
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"[CreditSim] DB save error for {app.application_id}: {e}")
    finally:
        cursor.close()


async def save_cycle_metrics(cycle_num: int, results: list, macro, conn) -> None:
    """Save aggregated cycle metrics to credit_cycle_metrics."""
    if not results:
        return

    approved = sum(1 for r in results if r.get("final_decision") == "APPROVED")
    blocked = sum(1 for r in results if r.get("final_decision") == "BLOCKED")
    hold_c = sum(1 for r in results if r.get("final_decision") == "HOLD")
    total = len(results)

    total_amt = sum(r["application"].requested_amount for r in results)
    approved_amt = sum(
        r["application"].requested_amount for r in results
        if r.get("final_decision") == "APPROVED"
    )
    blocked_amt = sum(
        r["application"].requested_amount for r in results
        if r.get("final_decision") == "BLOCKED"
    )

    sharia_ok = sum(1 for r in results if r["signals"].sharia_compliant)
    sharia_blocks = sum(
        1 for r in results
        if not r["signals"].sharia_compliant and r.get("final_decision") == "BLOCKED"
    )

    # Capital protected = blocked amount × average PD estimate
    avg_pd = sum(r["signals"].pd_estimate for r in results) / max(1, total)
    capital_protected = blocked_amt * avg_pd

    # Get cumulative count
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COALESCE(SUM(applications_evaluated), 0) FROM credit_cycle_metrics")
        prev_total = cursor.fetchone()[0] or 0

        cursor.execute("""
            INSERT INTO credit_cycle_metrics (
                cycle_number, applications_evaluated, total_applications_cumulative,
                approved, blocked, hold_count, approval_rate,
                total_amount_evaluated, total_amount_approved, total_amount_blocked,
                capital_protected, sharia_compliant_rate, sharia_blocks,
                macro_credit_index, macro_stress_level
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            cycle_num, total, int(prev_total) + total,
            approved, blocked, hold_c,
            round((approved / max(1, total)) * 100, 2),
            total_amt, approved_amt, blocked_amt,
            round(capital_protected, 2),
            round((sharia_ok / max(1, total)) * 100, 2),
            sharia_blocks,
            macro.credit_conditions_index, macro.stress_level,
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"[CreditSim] Metrics save error: {e}")
    finally:
        cursor.close()


async def run_credit_simulation_cycle(cycle_num: int, conn) -> list:
    """
    Execute one full simulation cycle:
    1. Fetch macro conditions
    2. Generate a batch of credit applications
    3. Evaluate each through the governance pipeline
    4. Save results to database
    """
    from omnix_core.credit.credit_macro_data import CreditMacroDataProvider

    macro_provider = CreditMacroDataProvider()
    macro = macro_provider.get_snapshot()

    batch_size = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
    applications = [
        generate_credit_application(macro_stress=macro.market_stress_index)
        for _ in range(batch_size)
    ]

    results = []
    for app in applications:
        result = await evaluate_credit_application(app, macro)
        if result:
            await save_credit_result(result, macro, conn)
            results.append(result)
            approved = result.get("final_decision", "BLOCKED")
            amount_aed = f"AED {app.requested_amount:,.0f}"
            cp_passed = result.get('checkpoints_passed', 0)
            cp_total = result.get('checkpoints_total', 11)
            blocked_at = result.get('blocked_at', '')
            if approved == "BLOCKED" and blocked_at == "CP-SHARIA":
                decision_label = f"BLOCKED(sharia-gate) | CP_passed={cp_passed}/{cp_total}"
            elif approved == "BLOCKED" and blocked_at:
                decision_label = f"BLOCKED@{blocked_at} | CP_passed={cp_passed}/{cp_total}"
            else:
                decision_label = f"{approved} | CP_passed={cp_passed}/{cp_total}"
            logger.info(
                f"[CreditSim] Cycle {cycle_num} | {app.application_id} | "
                f"{app.applicant_type} | {app.sector} | {amount_aed} | "
                f"{decision_label}"
            )

    await save_cycle_metrics(cycle_num, results, macro, conn)

    approved_count = sum(1 for r in results if r.get("final_decision") == "APPROVED")
    blocked_count = sum(1 for r in results if r.get("final_decision") == "BLOCKED")
    total_aed = sum(r["application"].requested_amount for r in results)
    blocked_aed = sum(
        r["application"].requested_amount for r in results
        if r.get("final_decision") == "BLOCKED"
    )

    logger.info(
        f"[CreditSim] ✅ Cycle {cycle_num} complete | "
        f"{len(results)} apps | ✅ {approved_count} | ❌ {blocked_count} | "
        f"Total AED {total_aed:,.0f} | Protected AED {blocked_aed:,.0f} | "
        f"Macro: {macro.stress_level} ({macro.credit_conditions_index:.0f})"
    )

    return results


def _ensure_tables(conn) -> None:
    """
    Create credit tables if they don't exist (idempotent).
    Runs on startup so Railway/any fresh DB works automatically.
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS credit_applications (
                id SERIAL PRIMARY KEY,
                application_id VARCHAR(64) UNIQUE NOT NULL,
                submitted_at TIMESTAMPTZ DEFAULT NOW(),
                evaluated_at TIMESTAMPTZ,
                applicant_type VARCHAR(32),
                applicant_id VARCHAR(64),
                sector VARCHAR(64),
                country VARCHAR(64),
                requested_amount NUMERIC,
                currency VARCHAR(8) DEFAULT 'AED',
                tenor_months INTEGER,
                financing_type VARCHAR(64),
                purpose TEXT,
                credit_score INTEGER,
                debt_service_ratio NUMERIC,
                asset_backing_ratio NUMERIC,
                collateral_type VARCHAR(64),
                annual_revenue NUMERIC,
                existing_obligations NUMERIC,
                is_halal_sector BOOLEAN,
                sharia_compliant BOOLEAN,
                gharar_score NUMERIC,
                riba_free BOOLEAN,
                signal_probability_score NUMERIC,
                signal_risk_exposure NUMERIC,
                signal_coherence NUMERIC,
                signal_trend_persistence NUMERIC,
                signal_stress_resilience NUMERIC,
                signal_logic_consistency NUMERIC,
                signal_integrity NUMERIC,
                signal_temporal_coherence NUMERIC,
                macro_credit_index NUMERIC,
                macro_volatility NUMERIC,
                macro_stress_level VARCHAR(32),
                fed_funds_rate NUMERIC,
                decision VARCHAR(16),
                receipt_id VARCHAR(128),
                blocked_at_checkpoint VARCHAR(16),
                block_reason TEXT,
                checkpoints_passed INTEGER,
                checkpoints_total INTEGER,
                decision_confidence NUMERIC,
                outcome VARCHAR(32),
                outcome_recorded_at TIMESTAMPTZ,
                simulation_run BOOLEAN DEFAULT TRUE,
                data_source VARCHAR(32) DEFAULT 'SIMULATION',
                notes TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS credit_cycle_metrics (
                id SERIAL PRIMARY KEY,
                recorded_at TIMESTAMPTZ DEFAULT NOW(),
                cycle_number INTEGER,
                applications_evaluated INTEGER,
                total_applications_cumulative INTEGER,
                approved INTEGER,
                blocked INTEGER,
                hold_count INTEGER,
                approval_rate NUMERIC,
                total_amount_evaluated NUMERIC,
                total_amount_approved NUMERIC,
                total_amount_blocked NUMERIC,
                capital_protected NUMERIC,
                sharia_compliant_rate NUMERIC,
                sharia_blocks INTEGER,
                macro_credit_index NUMERIC,
                macro_stress_level VARCHAR(32),
                engine_version VARCHAR(32)
            )
        """)
        conn.commit()
    logger.info("[CreditSim] ✅ Tables verified/created (credit_applications, credit_cycle_metrics)")


async def run_credit_simulation_engine():
    """
    Main 24/7 simulation engine.
    Runs indefinitely, one cycle every CYCLE_INTERVAL seconds.
    """
    import psycopg

    logger.info("🏦 [CreditSim] OMNIX Islamic Credit Governance Engine starting...")
    logger.info(f"[CreditSim] Cycle interval: {CYCLE_INTERVAL}s | Batch: {BATCH_SIZE_MIN}-{BATCH_SIZE_MAX} apps/cycle")

    conn = None
    cycle_num = 0

    try:
        conn = psycopg.connect(os.environ.get("OMNIX_DB_URL") or os.environ["DATABASE_URL"])
        logger.info("[CreditSim] ✅ PostgreSQL connected")
        _ensure_tables(conn)

        # Run initial cycle immediately
        while True:
            cycle_num += 1
            try:
                await run_credit_simulation_cycle(cycle_num, conn)
            except psycopg2.OperationalError:
                logger.warning("[CreditSim] DB connection lost, reconnecting...")
                try:
                    conn.close()
                except Exception:
                    pass
                conn = psycopg.connect(os.environ.get("OMNIX_DB_URL") or os.environ["DATABASE_URL"])
            except Exception as e:
                logger.error(f"[CreditSim] Cycle {cycle_num} error: {e}", exc_info=True)

            await asyncio.sleep(CYCLE_INTERVAL)

    finally:
        if conn:
            conn.close()
        logger.info("[CreditSim] Engine stopped.")


def start_credit_simulation_background():
    """
    Start the credit simulation engine in a background thread.
    Call from Flask app startup or standalone runner.
    """
    import threading

    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_credit_simulation_engine())
        except Exception as e:
            logger.error(f"[CreditSim] Background thread error: {e}", exc_info=True)
        finally:
            loop.close()

    thread = threading.Thread(target=_run, name="CreditSimulation", daemon=True)
    thread.start()
    logger.info("[CreditSim] Background simulation thread started")
    return thread


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_credit_simulation_engine())
