"""
OMNIX Stablecoin Reserve Governance Simulator
ADR-SRG-001: Stablecoin & Tokenization Governance Vertical (INTERNAL)

Runs 24/7 generating realistic stablecoin reserve governance decisions and
evaluating them through the OMNIX 11-checkpoint governance pipeline. Stores
results in PostgreSQL with PQC-signed receipts — identical architecture to
trading, credit, insurance, robotics, medical AI, autonomous agents, real estate,
and energy.

Cycle interval : 240 seconds (4 minutes)
Batch size     : 3-7 decisions per cycle
Domain code    : SRG → receipts formatted OMNIX-SRG-{12_HEX}

Decision type distribution (calibrated to real stablecoin operator data):
  reserve_rebalancing    (35%) — routine reserve composition adjustments
  redemption_processing  (25%) — large redemption requests (>$500K)
  collateral_adjustment  (20%) — collateral ratio changes
  peg_defense            (12%) — interventions to maintain $1.00 peg
  yield_optimization     ( 8%) — yield-generating reserve deployment

Reserve assets reflect real stablecoin reserve composition (USDC, USDT, FDUSD):
  US_Treasury_Bills (30%), Repo_Agreements (22%), Money_Market_Funds (18%),
  US_Treasury_Notes (12%), USDC (8%), Commercial_Paper (5%),
  ETH_Staked (3%), BTC (2%)

Jurisdictions reflect OMNIX's regulatory addressable market:
  EU_MiCA (28%), US_NYDFS (25%), UAE_VARA (20%), SG_MAS (15%), UK_FCA (8%), GCC (4%)
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import threading
import time
import uuid

from omnix_core.stablecoin.stablecoin_signal_adapter import (
    StablecoinDecisionInput,
    StablecoinSignalAdapter,
    ASSET_RISK_SCORE,
    JURISDICTION_STRICTNESS,
)
from omnix_core.evidence.decision_receipt import DecisionReceiptEngine

logger = logging.getLogger("OMNIX.Stablecoin.Simulator")

CYCLE_INTERVAL = 240.0
BATCH_SIZE_MIN = 3
BATCH_SIZE_MAX = 7

DECISION_TYPES = [
    ("reserve_rebalancing",   0.35),
    ("redemption_processing", 0.25),
    ("collateral_adjustment", 0.20),
    ("peg_defense",           0.12),
    ("yield_optimization",    0.08),
]

RESERVE_ASSETS = [
    ("US_Treasury_Bills",   0.30),
    ("Repo_Agreements",     0.22),
    ("Money_Market_Funds",  0.18),
    ("US_Treasury_Notes",   0.12),
    ("USDC",                0.08),
    ("Commercial_Paper",    0.05),
    ("ETH_Staked",          0.03),
    ("BTC",                 0.02),
]

JURISDICTIONS = [
    ("EU_MiCA",   0.28),
    ("US_NYDFS",  0.25),
    ("UAE_VARA",  0.20),
    ("SG_MAS",    0.15),
    ("UK_FCA",    0.08),
    ("GCC",       0.04),
]

# Hard block probability per scenario
HARD_BLOCK_SCENARIOS = {
    "peg_deviation":          0.020,   # 2.0% peg depeg emergency
    "undercollateralized":    0.012,   # 1.2% reserve coverage falls below 100%
    "mica_liquid_breach":     0.018,   # 1.8% liquid reserve ratio below MiCA min
    "aml_flag":               0.015,   # 1.5% AML screening failure
    "sanctions":              0.006,   # 0.6% sanctions match
    "counterparty_default":   0.010,   # 1.0% counterparty default
}

# Transaction size ranges by decision type (USD)
TRANSACTION_RANGES: dict[str, tuple] = {
    "reserve_rebalancing":   (500_000,    50_000_000),
    "redemption_processing": (500_000,    20_000_000),
    "collateral_adjustment": (1_000_000,  30_000_000),
    "peg_defense":           (5_000_000, 100_000_000),
    "yield_optimization":    (100_000,    10_000_000),
}

# Total supply ranges by jurisdiction (USD) — market-realistic
SUPPLY_BY_JURISDICTION: dict[str, tuple] = {
    "EU_MiCA":   (50_000_000,  500_000_000),
    "US_NYDFS":  (100_000_000, 5_000_000_000),
    "UAE_VARA":  (10_000_000,  200_000_000),
    "SG_MAS":    (20_000_000,  300_000_000),
    "UK_FCA":    (30_000_000,  400_000_000),
    "GCC":       (5_000_000,   50_000_000),
}


def _weighted_choice(choices: list[tuple]) -> str:
    items   = [c[0] for c in choices]
    weights = [c[1] for c in choices]
    return random.choices(items, weights=weights, k=1)[0]


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def _create_stablecoin_tables(conn) -> None:
    """Create stablecoin governance tables if not exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stablecoin_decisions (
                id                          SERIAL PRIMARY KEY,
                decision_id                 VARCHAR(64)   NOT NULL UNIQUE,
                decision_type               VARCHAR(32)   NOT NULL,
                reserve_asset               VARCHAR(32)   NOT NULL,
                jurisdiction                VARCHAR(16)   NOT NULL,
                transaction_amount_usd      FLOAT         NOT NULL,
                total_supply_usd            FLOAT         NOT NULL DEFAULT 0,
                peg_deviation_pct           FLOAT         NOT NULL DEFAULT 0,
                reserve_coverage_ratio      FLOAT         NOT NULL DEFAULT 100,
                liquid_reserve_ratio        FLOAT         NOT NULL DEFAULT 80,
                crypto_exposure_pct         FLOAT         NOT NULL DEFAULT 0,
                decision                    VARCHAR(10)   NOT NULL,
                decision_score              FLOAT,
                block_reason                TEXT,
                hard_block_reason           TEXT,
                probability_score           FLOAT,
                risk_exposure               FLOAT,
                signal_coherence            FLOAT,
                trend_persistence           FLOAT,
                stress_resilience           FLOAT,
                logic_consistency           FLOAT,
                trajectory_score            FLOAT,
                transaction_risk_usd        FLOAT         DEFAULT 0,
                receipt_id                  VARCHAR(64),
                domain                      VARCHAR(32)   DEFAULT 'stablecoin',
                created_at                  TIMESTAMPTZ   DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stablecoin_cycle_metrics (
                id                  SERIAL PRIMARY KEY,
                cycle_id            VARCHAR(64) NOT NULL,
                total_decisions     INTEGER     NOT NULL DEFAULT 0,
                approved            INTEGER     NOT NULL DEFAULT 0,
                blocked             INTEGER     NOT NULL DEFAULT 0,
                held                INTEGER     NOT NULL DEFAULT 0,
                total_volume_usd    FLOAT       DEFAULT 0,
                approved_volume_usd FLOAT       DEFAULT 0,
                blocked_volume_usd  FLOAT       DEFAULT 0,
                duration_ms         INTEGER     DEFAULT 0,
                created_at          TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_stablecoin_decisions_type
            ON stablecoin_decisions (decision_type)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_stablecoin_decisions_asset
            ON stablecoin_decisions (reserve_asset)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_stablecoin_decisions_jurisdiction
            ON stablecoin_decisions (jurisdiction)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_stablecoin_decisions_created
            ON stablecoin_decisions (created_at DESC)
        """)
        conn.commit()
    logger.info("stablecoin_decisions + stablecoin_cycle_metrics tables ready")


def _generate_decision(
    decision_type: str,
    reserve_asset: str,
    jurisdiction: str,
    cycle_id: str,
) -> dict:
    """Generate one realistic stablecoin reserve governance decision."""
    adapter = StablecoinSignalAdapter()

    # ── Hard block scenario roll ──────────────────────────────────────────────
    peg_dev = round(random.uniform(0.0, 0.30), 3)   # Normal: 0-0.30% deviation
    reserve_cov = round(random.uniform(102.0, 115.0), 2)  # Normal: 102-115% covered
    liquid_ratio = round(random.uniform(70.0, 92.0), 1)   # Normal: 70-92% liquid
    aml_flag = False
    sanctions_flag = False
    counterparty_default = False

    for scenario, prob in HARD_BLOCK_SCENARIOS.items():
        if random.random() < prob:
            if scenario == "peg_deviation":
                peg_dev = round(random.uniform(2.05, 8.0), 3)
            elif scenario == "undercollateralized":
                reserve_cov = round(random.uniform(88.0, 99.5), 2)
            elif scenario == "mica_liquid_breach":
                liquid_ratio = round(random.uniform(35.0, 59.5), 1)
            elif scenario == "aml_flag":
                aml_flag = True
            elif scenario == "sanctions":
                sanctions_flag = True
            elif scenario == "counterparty_default":
                counterparty_default = True
            break  # Only one hard block per decision for realism

    # ── Transaction sizing ────────────────────────────────────────────────────
    t_min, t_max = TRANSACTION_RANGES.get(decision_type, (500_000, 5_000_000))
    transaction_amount = round(random.uniform(t_min, t_max), 2)

    s_min, s_max = SUPPLY_BY_JURISDICTION.get(jurisdiction, (50_000_000, 500_000_000))
    total_supply = round(random.uniform(s_min, s_max), 2)

    # ── Risk parameters ───────────────────────────────────────────────────────
    is_crypto = reserve_asset in ("ETH_Staked", "BTC")
    asset_risk = ASSET_RISK_SCORE.get(reserve_asset, 30.0)

    # Crypto assets have higher concentration and exposure
    crypto_exp = _clamp(random.gauss(35 if is_crypto else 5, 8), 0, 80)
    concentration = _clamp(random.gauss(25 if is_crypto else 20, 10), 5, 75)
    cp_risk = _clamp(random.gauss(15 + asset_risk * 0.3, 10), 0, 80)
    duration_days = {
        "US_Treasury_Bills":   round(random.uniform(1, 90)),
        "Repo_Agreements":     round(random.uniform(1, 7)),
        "Money_Market_Funds":  round(random.uniform(1, 30)),
        "US_Treasury_Notes":   round(random.uniform(180, 730)),
        "USDC":                1,
        "Commercial_Paper":    round(random.uniform(7, 180)),
        "ETH_Staked":          round(random.uniform(30, 365)),
        "BTC":                 round(random.uniform(7, 180)),
    }.get(reserve_asset, 30.0)

    # ── Peg coherence signals ─────────────────────────────────────────────────
    # Larger peg deviation → worse coherence
    on_chain_align = _clamp(random.gauss(92 - peg_dev * 20, 8), 40, 100)
    cross_exchange = _clamp(random.gauss(88 - peg_dev * 10, 10), 40, 100)
    oracle_conf    = _clamp(random.gauss(85, 10), 50, 99)

    # ── Reserve flow signals ──────────────────────────────────────────────────
    flow_stability = _clamp(random.gauss(72, 14), 30, 97)
    tvl_trend = _clamp(random.gauss(58, 18), 20, 95)   # >50 = growing
    redemption_stability = _clamp(random.gauss(68, 16), 25, 97)

    # peg_defense type — less stable flows
    if decision_type == "peg_defense":
        flow_stability = _clamp(flow_stability - 20, 10, 70)
        tvl_trend = _clamp(tvl_trend - 15, 10, 60)

    # ── Stress resilience signals ─────────────────────────────────────────────
    instant_liq = _clamp(random.gauss(70, 15), 20, 99)
    emergency_buf = _clamp(random.gauss(55, 18), 10, 95)
    credit_fac = _clamp(random.gauss(60, 20), 0, 95)

    # ── Regulatory compliance signals ─────────────────────────────────────────
    mica_score = _clamp(random.gauss(78, 12), 30, 99)
    aml_comp = _clamp(random.gauss(85, 10), 40, 100)
    audit_comp = _clamp(random.gauss(80, 12), 30, 100)

    # EU_MiCA jurisdiction tends to have higher compliance scores (self-selection)
    if jurisdiction == "EU_MiCA":
        mica_score = min(100, mica_score + 8)
        aml_comp = min(100, aml_comp + 5)

    inp = StablecoinDecisionInput(
        decision_type=decision_type,
        reserve_asset=reserve_asset,
        jurisdiction=jurisdiction,
        peg_deviation_pct=peg_dev,
        reserve_coverage_ratio=reserve_cov,
        liquid_reserve_ratio=liquid_ratio,
        crypto_exposure_pct=crypto_exp,
        concentration_risk=concentration,
        counterparty_credit_risk=cp_risk,
        reserve_duration_days=float(duration_days),
        on_chain_off_chain_alignment=on_chain_align,
        cross_exchange_consistency=cross_exchange,
        oracle_confidence=oracle_conf,
        reserve_flow_stability=flow_stability,
        tvl_trend_7d=tvl_trend,
        redemption_pattern_stability=redemption_stability,
        instant_liquidity_coverage=instant_liq,
        emergency_reserve_buffer=emergency_buf,
        credit_facility_available=credit_fac,
        mica_compliance_score=mica_score,
        aml_screening_completeness=aml_comp,
        audit_completeness=audit_comp,
        aml_flag=aml_flag,
        sanctions_flag=sanctions_flag,
        counterparty_credit_default=counterparty_default,
        transaction_amount_usd=transaction_amount,
        total_supply_usd=total_supply,
    )

    signals = adapter.adapt(inp)
    sig_dict = signals.to_omnix_dict()
    decision_id = f"SRG-{cycle_id[:8].upper()}-{uuid.uuid4().hex[:8].upper()}"

    # ── Hard block — bypass engine ────────────────────────────────────────────
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
        decision_score = round(_composite * 0.12, 2)
        receipt_id    = None
    else:
        # ── OMNIX GovernanceEvaluationEngine — 11-checkpoint pipeline ─────────
        try:
            from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
            engine = GovernanceEvaluationEngine()
            result = engine.evaluate(
                signals=sig_dict,
                asset=f"{reserve_asset}_{decision_type}",
                domain="stablecoin",
                metadata={
                    "jurisdiction":          jurisdiction,
                    "decision_type":         decision_type,
                    "reserve_asset":         reserve_asset,
                    "peg_deviation_pct":     signals.peg_deviation_pct,
                    "reserve_coverage":      signals.reserve_coverage_ratio,
                    "liquid_reserve_ratio":  signals.liquid_reserve_ratio,
                },
                compliance_config={
                    "cag_liquidity_score": round(signals.liquid_reserve_ratio * 100, 1),
                },
            )
            decision      = result.get("decision", "BLOCKED")
            scores        = result.get("scores", sig_dict)
            _composite    = (
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
                ("COMPLIANCE_OFFICER_REVIEW: composite score requires manual validation"
                 if decision == "HOLD" else None)
            )
        except Exception as exc:
            logger.warning(f"[Stablecoin] Governance engine unavailable: {exc} — rule-based fallback")
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
                block_reason = "COMPLIANCE_OFFICER_REVIEW: composite score requires manual validation"
            else:
                decision = "BLOCKED"
                block_reason = "HIGH_RISK: governance score below reserve action threshold"
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
                    domain="stablecoin",
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
        "reserve_asset":           reserve_asset,
        "jurisdiction":            jurisdiction,
        "transaction_amount_usd":  transaction_amount,
        "total_supply_usd":        total_supply,
        "peg_deviation_pct":       peg_dev,
        "reserve_coverage_ratio":  reserve_cov,
        "liquid_reserve_ratio":    liquid_ratio,
        "crypto_exposure_pct":     crypto_exp,
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
        "transaction_risk_usd":    signals.transaction_risk_usd,
        "receipt_id":              receipt_id,
        "domain":                  "stablecoin",
    }


def _store_decision(conn, d: dict) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO stablecoin_decisions (
                decision_id, decision_type, reserve_asset, jurisdiction,
                transaction_amount_usd, total_supply_usd,
                peg_deviation_pct, reserve_coverage_ratio, liquid_reserve_ratio,
                crypto_exposure_pct,
                decision, decision_score, block_reason, hard_block_reason,
                probability_score, risk_exposure, signal_coherence,
                trend_persistence, stress_resilience, logic_consistency,
                trajectory_score, transaction_risk_usd,
                receipt_id, domain
            ) VALUES (
                %(decision_id)s, %(decision_type)s, %(reserve_asset)s, %(jurisdiction)s,
                %(transaction_amount_usd)s, %(total_supply_usd)s,
                %(peg_deviation_pct)s, %(reserve_coverage_ratio)s, %(liquid_reserve_ratio)s,
                %(crypto_exposure_pct)s,
                %(decision)s, %(decision_score)s, %(block_reason)s, %(hard_block_reason)s,
                %(probability_score)s, %(risk_exposure)s, %(signal_coherence)s,
                %(trend_persistence)s, %(stress_resilience)s, %(logic_consistency)s,
                %(trajectory_score)s, %(transaction_risk_usd)s,
                %(receipt_id)s, %(domain)s
            ) ON CONFLICT (decision_id) DO NOTHING
        """, d)
    conn.commit()


def _run_cycle(conn, cycle_num: int) -> None:
    cycle_id = uuid.uuid4().hex
    batch_size = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
    t0 = time.time()

    approved = blocked = held = 0
    total_vol = approved_vol = blocked_vol = 0.0

    logger.info(f"[Stablecoin Cycle {cycle_num}] Generating {batch_size} reserve governance decisions")

    for _ in range(batch_size):
        d_type  = _weighted_choice(DECISION_TYPES)
        asset   = _weighted_choice(RESERVE_ASSETS)
        juris   = _weighted_choice(JURISDICTIONS)

        try:
            d = _generate_decision(d_type, asset, juris, cycle_id)
            _store_decision(conn, d)
        except Exception as e:
            logger.warning(f"Decision generation error: {e}")
            continue

        total_vol += d["transaction_amount_usd"]

        if d["decision"] == "APPROVED":
            approved += 1
            approved_vol += d["transaction_amount_usd"]
        elif d["decision"] == "BLOCKED":
            blocked += 1
            blocked_vol += d["transaction_amount_usd"]
        else:
            held += 1

    duration_ms = int((time.time() - t0) * 1000)

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO stablecoin_cycle_metrics
                (cycle_id, total_decisions, approved, blocked, held,
                 total_volume_usd, approved_volume_usd, blocked_volume_usd, duration_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (cycle_id, batch_size, approved, blocked, held,
              round(total_vol, 2), round(approved_vol, 2), round(blocked_vol, 2),
              duration_ms))
        conn.commit()

    logger.info(
        f"[Stablecoin Cycle {cycle_num}] "
        f"APPROVED={approved} BLOCKED={blocked} HELD={held} | "
        f"Volume ${total_vol:,.0f} | {duration_ms}ms"
    )


def _simulator_loop() -> None:
    import psycopg
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not set — Stablecoin Governance simulator cannot start")
        return

    conn = psycopg.connect(db_url)
    _create_stablecoin_tables(conn)
    logger.info("Stablecoin Reserve Governance Simulator started — 24/7 mode")

    cycle = 1
    while True:
        try:
            _run_cycle(conn, cycle)
            cycle += 1
        except Exception as e:
            logger.error(f"Stablecoin cycle {cycle} error: {e}")
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
    t = threading.Thread(target=_simulator_loop, daemon=True, name="StablecoinGovernanceSim")
    t.start()
    logger.info("Stablecoin Reserve Governance background simulator thread started")
