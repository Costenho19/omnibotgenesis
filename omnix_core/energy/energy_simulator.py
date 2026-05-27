"""
OMNIX Energy Governance Simulator
ADR-ENG-001: Energy Governance Vertical (INTERNAL)

Runs 24/7 generating realistic energy governance decisions and evaluating
them through the OMNIX 11-checkpoint governance pipeline. Stores results in
PostgreSQL with PQC-signed receipts — identical architecture to trading,
credit, insurance, robotics, medical AI, autonomous agents, and real estate.

Cycle interval : 180 seconds (3 minutes) — energy dispatch decisions are
                 frequent; grid balancing can be sub-minute in production
Batch size      : 4-10 decisions per cycle
Domain code     : EGV → receipts formatted OMNIX-EGV-{12_HEX}

Decision type distribution (calibrated to real grid operator data):
  dispatch_order    (35%) — automated generation dispatch
  curtailment_order (20%) — renewable curtailment when supply > demand
  ppa_contract      (15%) — power purchase agreement evaluation
  capacity_trade    (15%) — capacity market participation
  carbon_credit     (10%) — carbon credit purchase / sale
  balancing_action  ( 5%) — real-time grid balancing (high urgency)

Grid regions reflect OMNIX's addressable market (Naimat pilot pathway):
  PJM (25%) · UK (22%) · EU_ENTSO_E (20%) · ERCOT (15%) · GCC (12%) · AEMO (6%)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import threading
import time
import uuid
from typing import Optional

from omnix_core.energy.energy_signal_adapter import (
    EnergyDecisionInput,
    EnergySignalAdapter,
    CARBON_INTENSITY,
    SOURCE_VOLATILITY,
)
from omnix_core.evidence.decision_receipt import DecisionReceiptEngine

logger = logging.getLogger("OMNIX.Energy.Simulator")

CYCLE_INTERVAL  = 180.0
BATCH_SIZE_MIN  = 4
BATCH_SIZE_MAX  = 10

DECISION_TYPES = [
    ("dispatch_order",    0.35),
    ("curtailment_order", 0.20),
    ("ppa_contract",      0.15),
    ("capacity_trade",    0.15),
    ("carbon_credit",     0.10),
    ("balancing_action",  0.05),
]

ENERGY_SOURCES = [
    ("Natural_Gas",    0.22),
    ("Wind_Onshore",   0.18),
    ("Solar_Utility",  0.16),
    ("Wind_Offshore",  0.10),
    ("Nuclear",        0.10),
    ("Hydro",          0.08),
    ("Battery_Storage", 0.06),
    ("LNG",            0.06),
    ("Coal",           0.04),
]

GRID_REGIONS = [
    ("PJM",       0.25),
    ("UK",        0.22),
    ("EU_ENTSO_E",0.20),
    ("ERCOT",     0.15),
    ("GCC",       0.12),
    ("AEMO",      0.06),
]

# Hard block probability per scenario (small but real)
HARD_BLOCK_SCENARIOS = {
    "frequency_emergency": 0.018,   # 1.8% chance of grid emergency
    "capacity_critical":   0.025,   # 2.5% chance of low reserve
    "counterparty_default": 0.012,  # 1.2% counterparty default
    "carbon_breach":       0.015,   # 1.5% carbon cap breach
    "regulatory_violation": 0.008,  # 0.8% direct regulatory violation
    "sanctions":           0.005,   # 0.5% sanctions flag
}

# Settlement price ranges by energy source (USD/MWh or USD/MMBtu for gas)
PRICE_RANGES: dict[str, tuple] = {
    "Natural_Gas":    (28.0, 85.0),
    "Wind_Onshore":   (18.0, 52.0),
    "Solar_Utility":  (22.0, 58.0),
    "Wind_Offshore":  (28.0, 65.0),
    "Nuclear":        (25.0, 40.0),
    "Hydro":          (20.0, 45.0),
    "Battery_Storage": (55.0, 120.0),
    "LNG":            (45.0, 140.0),
    "Coal":           (35.0, 75.0),
}

# MW range by decision type
MW_RANGES: dict[str, tuple] = {
    "dispatch_order":    (50, 800),
    "curtailment_order": (20, 500),
    "ppa_contract":      (100, 2000),
    "capacity_trade":    (50, 1000),
    "carbon_credit":     (10, 200),
    "balancing_action":  (10, 150),
}


def _weighted_choice(choices: list[tuple]) -> str:
    items   = [c[0] for c in choices]
    weights = [c[1] for c in choices]
    return random.choices(items, weights=weights, k=1)[0]


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def _create_energy_tables(conn) -> None:
    """Create energy governance tables if not exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS energy_decisions (
                id                      SERIAL PRIMARY KEY,
                decision_id             VARCHAR(64)   NOT NULL UNIQUE,
                decision_type           VARCHAR(32)   NOT NULL,
                energy_source           VARCHAR(32)   NOT NULL,
                grid_region             VARCHAR(16)   NOT NULL,
                contracted_mw           FLOAT         NOT NULL,
                settlement_price_mwh    FLOAT         NOT NULL,
                contract_term_years     FLOAT         NOT NULL DEFAULT 1.0,
                decision                VARCHAR(10)   NOT NULL,
                decision_score          FLOAT,
                block_reason            TEXT,
                hard_block_reason       TEXT,
                probability_score       FLOAT,
                risk_exposure           FLOAT,
                signal_coherence        FLOAT,
                trend_persistence       FLOAT,
                stress_resilience       FLOAT,
                logic_consistency       FLOAT,
                trajectory_score        FLOAT,
                capacity_margin_pct     FLOAT,
                frequency_deviation_hz  FLOAT,
                carbon_avoided_tco2e    FLOAT         DEFAULT 0.0,
                settlement_risk_usd     FLOAT         DEFAULT 0.0,
                lmp_forecast_confidence FLOAT,
                renewable_intermittency_buffer FLOAT,
                receipt_id              VARCHAR(64),
                domain                  VARCHAR(32)   DEFAULT 'energy_governance',
                created_at              TIMESTAMPTZ   DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS energy_cycle_metrics (
                id              SERIAL PRIMARY KEY,
                cycle_id        VARCHAR(64) NOT NULL,
                total_decisions INTEGER     NOT NULL DEFAULT 0,
                approved        INTEGER     NOT NULL DEFAULT 0,
                blocked         INTEGER     NOT NULL DEFAULT 0,
                held            INTEGER     NOT NULL DEFAULT 0,
                total_mw        FLOAT       DEFAULT 0.0,
                approved_mw     FLOAT       DEFAULT 0.0,
                blocked_mw      FLOAT       DEFAULT 0.0,
                carbon_avoided_tco2e FLOAT  DEFAULT 0.0,
                duration_ms     INTEGER     DEFAULT 0,
                created_at      TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_energy_decisions_type
            ON energy_decisions (decision_type)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_energy_decisions_source
            ON energy_decisions (energy_source)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_energy_decisions_region
            ON energy_decisions (grid_region)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_energy_decisions_created
            ON energy_decisions (created_at DESC)
        """)
        conn.commit()
    logger.info("energy_decisions + energy_cycle_metrics tables ready")


def _generate_decision(
    decision_type: str,
    energy_source: str,
    grid_region: str,
    cycle_id: str,
) -> dict:
    """Generate one realistic energy governance decision."""
    adapter = EnergySignalAdapter()

    # ── Hard block scenario roll ──────────────────────────────────────────────
    freq_dev = round(random.uniform(0.0, 0.15), 3)   # Normal: 0-0.15 Hz
    cap_margin = round(random.uniform(8.0, 35.0), 1)  # Normal: 8-35%
    counterparty_default = False
    carbon_breach = False
    regulatory_flag = False
    sanctions = False

    for scenario, prob in HARD_BLOCK_SCENARIOS.items():
        if random.random() < prob:
            if scenario == "frequency_emergency":
                freq_dev = round(random.uniform(0.52, 1.20), 3)
            elif scenario == "capacity_critical":
                cap_margin = round(random.uniform(0.5, 4.8), 1)
            elif scenario == "counterparty_default":
                counterparty_default = True
            elif scenario == "carbon_breach":
                carbon_breach = True
            elif scenario == "regulatory_violation":
                regulatory_flag = True
            elif scenario == "sanctions":
                sanctions = True
            break   # Only one hard block per decision for realism

    # ── Normal operating ranges by scenario ──────────────────────────────────
    is_renewable = energy_source in ("Wind_Onshore", "Wind_Offshore", "Solar_Utility", "Hydro")
    is_coal = energy_source == "Coal"

    mw_min, mw_max = MW_RANGES.get(decision_type, (50, 500))
    contracted_mw = round(random.uniform(mw_min, mw_max), 1)

    price_lo, price_hi = PRICE_RANGES.get(energy_source, (40.0, 80.0))
    settlement_price = round(random.uniform(price_lo, price_hi), 2)

    term_years = {
        "dispatch_order":    round(random.uniform(0.1, 1.0), 2),
        "curtailment_order": round(random.uniform(0.0, 0.5), 2),
        "ppa_contract":      float(random.choice([1, 5, 10, 15, 20])),
        "capacity_trade":    float(random.choice([1, 3, 5])),
        "carbon_credit":     round(random.uniform(0.5, 3.0), 1),
        "balancing_action":  round(random.uniform(0.01, 0.1), 3),
    }.get(decision_type, 1.0)

    # ── Signal generation (realistic distributions) ───────────────────────────
    lmp_confidence = _clamp(random.gauss(72, 14), 20, 97)

    # Grid congestion: PJM/EU tend more congested
    congestion_base = {"PJM": 45, "EU_ENTSO_E": 38, "UK": 32, "ERCOT": 25, "GCC": 20, "AEMO": 22}.get(grid_region, 30)
    grid_congestion = _clamp(random.gauss(congestion_base, 18), 0, 95)

    # Renewables have higher intermittency
    rt_spread = _clamp(random.gauss(20 if is_renewable else 12, 10), 0, 80)
    futures_conv = _clamp(random.gauss(65, 18), 10, 98)
    cross_border = _clamp(random.gauss(60, 20), 15, 95)

    load_accuracy = _clamp(random.gauss(74, 12), 30, 97)
    demand_stability = _clamp(random.gauss(68, 16), 20, 95)
    seasonality_align = _clamp(random.gauss(70, 14), 25, 97)

    # Renewables need more intermittency buffer handling
    renew_buffer = _clamp(random.gauss(55 if is_renewable else 70, 18), 10, 95)
    interconnect_util = _clamp(random.gauss(55, 22), 5, 98)
    storage_ready = _clamp(random.gauss(60, 20), 10, 95)

    carbon_price = round(random.uniform(15.0, 65.0), 2)

    inp = EnergyDecisionInput(
        decision_type=decision_type,
        energy_source=energy_source,
        grid_region=grid_region,
        lmp_forecast_confidence=lmp_confidence,
        frequency_deviation_hz=freq_dev,
        grid_congestion_index=grid_congestion,
        capacity_margin_pct=cap_margin,
        day_ahead_rt_spread=rt_spread,
        futures_spot_convergence=futures_conv,
        cross_border_price_alignment=cross_border,
        load_forecast_accuracy=load_accuracy,
        demand_growth_stability=demand_stability,
        seasonality_alignment=seasonality_align,
        renewable_intermittency_buffer=renew_buffer,
        interconnect_capacity_utilization=interconnect_util,
        storage_readiness=storage_ready,
        regulatory_violation_flag=regulatory_flag,
        carbon_position_over_cap=carbon_breach,
        counterparty_credit_default=counterparty_default,
        sanctions_flag=sanctions,
        contracted_mw=contracted_mw,
        contract_term_years=term_years,
        settlement_price_mwh=settlement_price,
        carbon_price_usd_tco2=carbon_price,
    )

    signals = adapter.adapt(inp)
    sig_dict = signals.to_omnix_dict()

    decision_id = f"EGV-{cycle_id[:8].upper()}-{uuid.uuid4().hex[:8].upper()}"

    # ── Hard block — grid emergency overrides, bypass engine (ADR-112/ADR-113) ─
    if signals.hard_block_reason:
        _composite = (
            sig_dict["probability_score"] + (100.0 - sig_dict["risk_exposure"])
            + sig_dict["signal_coherence"] + sig_dict["trend_persistence"]
            + sig_dict["stress_resilience"] + sig_dict["logic_consistency"]
        ) / 6.0
        trajectory_score = _clamp(
            sig_dict["trend_persistence"] * 0.45
            + sig_dict["signal_coherence"] * 0.35
            + sig_dict["stress_resilience"] * 0.20, 0, 100
        )
        decision      = "BLOCKED"
        block_reason  = signals.hard_block_reason
        decision_score = round(_composite * 0.15, 2)
        receipt_id    = None
    else:
        # ── OMNIX GovernanceEvaluationEngine — 11-checkpoint pipeline (ADR-113) ─
        try:
            from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
            engine = GovernanceEvaluationEngine()
            result = engine.evaluate(
                signals=sig_dict,
                asset=f"{energy_source}_{decision_type}",
                domain="energy_governance",
                metadata={
                    "grid_region":          grid_region,
                    "decision_type":        decision_type,
                    "energy_source":        energy_source,
                    "capacity_margin_pct":  signals.capacity_margin_pct,
                    "frequency_deviation":  signals.frequency_deviation_hz,
                },
                compliance_config={
                    "cag_liquidity_score": 100.0,
                },
            )
            decision   = result.get("decision", "BLOCKED")
            scores     = result.get("scores", sig_dict)
            _composite = (
                scores.get("probability_score", 50) + (100.0 - scores.get("risk_exposure", 50))
                + scores.get("signal_coherence", 50) + scores.get("trend_persistence", 50)
                + scores.get("stress_resilience", 50) + scores.get("logic_consistency", 50)
            ) / 6.0
            trajectory_score = _clamp(
                scores.get("trend_persistence", 50) * 0.45
                + scores.get("signal_coherence", 50) * 0.35
                + scores.get("stress_resilience", 50) * 0.20, 0, 100
            )
            veto_chain   = result.get("veto_chain", [])
            decision_score = round(_composite, 2)
            block_reason = (
                veto_chain[0].get("checkpoint_name", "Governance threshold breach")
                if veto_chain else
                ("GRID_OPERATOR_REVIEW: composite score requires manual validation"
                 if decision == "HOLD" else None)
            )
        except Exception as exc:
            logger.warning(f"[Energy] Governance engine unavailable: {exc} — rule-based fallback active")
            _composite = (
                sig_dict["probability_score"] + (100.0 - sig_dict["risk_exposure"])
                + sig_dict["signal_coherence"] + sig_dict["trend_persistence"]
                + sig_dict["stress_resilience"] + sig_dict["logic_consistency"]
            ) / 6.0
            trajectory_score = _clamp(
                sig_dict["trend_persistence"] * 0.45
                + sig_dict["signal_coherence"] * 0.35
                + sig_dict["stress_resilience"] * 0.20, 0, 100
            )
            if _composite >= 70.0:
                decision, block_reason = "APPROVED", None
            elif _composite >= 52.0:
                decision = "HOLD"
                block_reason = "GRID_OPERATOR_REVIEW: composite score requires manual validation"
            else:
                decision = "BLOCKED"
                block_reason = "HIGH_RISK: composite governance score below execution threshold"
            decision_score = round(_composite, 2)

        receipt_id = None
        try:
            loop = asyncio.new_event_loop()
            receipt_engine = DecisionReceiptEngine()
            receipt = loop.run_until_complete(
                receipt_engine.generate_receipt(
                    decision_id=decision_id,
                    decision_type=decision_type,
                    decision=decision,
                    decision_score=decision_score,
                    block_reason=block_reason,
                    domain="energy_governance",
                    signals=sig_dict,
                )
            )
            receipt_id = receipt.get("receipt_id")
            loop.close()
        except Exception as re:
            logger.debug(f"Receipt generation skipped: {re}")

    return {
        "decision_id":             decision_id,
        "decision_type":           decision_type,
        "energy_source":           energy_source,
        "grid_region":             grid_region,
        "contracted_mw":           contracted_mw,
        "settlement_price_mwh":    settlement_price,
        "contract_term_years":     term_years,
        "decision":                decision,
        "decision_score":          decision_score,
        "block_reason":            block_reason,
        "hard_block_reason":       signals.hard_block_reason,
        "probability_score":       sig_dict["probability_score"],
        "risk_exposure":           sig_dict["risk_exposure"],
        "signal_coherence":        sig_dict["signal_coherence"],
        "trend_persistence":       sig_dict["trend_persistence"],
        "stress_resilience":       sig_dict["stress_resilience"],
        "logic_consistency":       sig_dict["logic_consistency"],
        "trajectory_score":        round(trajectory_score, 2),
        "capacity_margin_pct":     signals.capacity_margin_pct,
        "frequency_deviation_hz":  signals.frequency_deviation_hz,
        "carbon_avoided_tco2e":    signals.carbon_avoided_tco2e,
        "settlement_risk_usd":     signals.settlement_risk_usd,
        "lmp_forecast_confidence": lmp_confidence,
        "renewable_intermittency_buffer": renew_buffer,
        "receipt_id":              receipt_id,
        "domain":                  "energy_governance",
    }


def _store_decision(conn, d: dict) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO energy_decisions (
                decision_id, decision_type, energy_source, grid_region,
                contracted_mw, settlement_price_mwh, contract_term_years,
                decision, decision_score, block_reason, hard_block_reason,
                probability_score, risk_exposure, signal_coherence,
                trend_persistence, stress_resilience, logic_consistency,
                trajectory_score, capacity_margin_pct, frequency_deviation_hz,
                carbon_avoided_tco2e, settlement_risk_usd,
                lmp_forecast_confidence, renewable_intermittency_buffer,
                receipt_id, domain
            ) VALUES (
                %(decision_id)s, %(decision_type)s, %(energy_source)s, %(grid_region)s,
                %(contracted_mw)s, %(settlement_price_mwh)s, %(contract_term_years)s,
                %(decision)s, %(decision_score)s, %(block_reason)s, %(hard_block_reason)s,
                %(probability_score)s, %(risk_exposure)s, %(signal_coherence)s,
                %(trend_persistence)s, %(stress_resilience)s, %(logic_consistency)s,
                %(trajectory_score)s, %(capacity_margin_pct)s, %(frequency_deviation_hz)s,
                %(carbon_avoided_tco2e)s, %(settlement_risk_usd)s,
                %(lmp_forecast_confidence)s, %(renewable_intermittency_buffer)s,
                %(receipt_id)s, %(domain)s
            ) ON CONFLICT (decision_id) DO NOTHING
        """, d)
    conn.commit()


def _run_cycle(conn, cycle_num: int) -> None:
    cycle_id = uuid.uuid4().hex
    batch_size = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
    t0 = time.time()

    approved = blocked = held = 0
    total_mw = approved_mw = blocked_mw = carbon_total = 0.0

    logger.info(f"[Energy Cycle {cycle_num}] Generating {batch_size} energy governance decisions")

    for _ in range(batch_size):
        d_type  = _weighted_choice(DECISION_TYPES)
        source  = _weighted_choice(ENERGY_SOURCES)
        region  = _weighted_choice(GRID_REGIONS)

        try:
            d = _generate_decision(d_type, source, region, cycle_id)
            _store_decision(conn, d)
        except Exception as e:
            logger.warning(f"Decision generation error: {e}")
            continue

        total_mw += d["contracted_mw"]
        carbon_total += d["carbon_avoided_tco2e"]

        if d["decision"] == "APPROVED":
            approved += 1
            approved_mw += d["contracted_mw"]
        elif d["decision"] == "BLOCKED":
            blocked += 1
            blocked_mw += d["contracted_mw"]
        else:
            held += 1

    duration_ms = int((time.time() - t0) * 1000)

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO energy_cycle_metrics
                (cycle_id, total_decisions, approved, blocked, held,
                 total_mw, approved_mw, blocked_mw, carbon_avoided_tco2e, duration_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (cycle_id, batch_size, approved, blocked, held,
              round(total_mw, 1), round(approved_mw, 1), round(blocked_mw, 1),
              round(carbon_total, 3), duration_ms))
        conn.commit()

    logger.info(
        f"[Energy Cycle {cycle_num}] "
        f"APPROVED={approved} BLOCKED={blocked} HELD={held} | "
        f"Total {total_mw:.0f} MW | CO2 avoided {carbon_total:.1f} ktCO2e | "
        f"{duration_ms}ms"
    )


def _simulator_loop() -> None:
    import psycopg
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not set — Energy Governance simulator cannot start")
        return

    conn = psycopg.connect(db_url)
    _create_energy_tables(conn)
    logger.info("Energy Governance Simulator started — 24/7 mode")

    cycle = 1
    while True:
        try:
            _run_cycle(conn, cycle)
            cycle += 1
        except Exception as e:
            logger.error(f"Energy cycle {cycle} error: {e}")
            try:
                conn.rollback()
            except Exception:
                try:
                    conn = psycopg.connect(db_url)
                except Exception:
                    pass
        time.sleep(CYCLE_INTERVAL)


_started = False
_lock = threading.Lock()


def start_background_simulator() -> None:
    global _started
    with _lock:
        if _started:
            return
        _started = True
    t = threading.Thread(target=_simulator_loop, daemon=True, name="EnergyGovernanceSim")
    t.start()
    logger.info("Energy Governance background simulator thread started")
