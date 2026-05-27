"""
OMNIX Real Estate Governance Simulator
ADR-RES-001: Real Estate Governance Vertical

Runs 24/7 generating realistic property transaction decisions and evaluating
them through the OMNIX 11-checkpoint governance pipeline. Stores results in
PostgreSQL with PQC-signed receipts — identical to trading, credit, insurance,
robotics, medical AI, and autonomous agents engine flows.

Cycle interval: 300 seconds (5 minutes) — property decisions are less frequent
                than trading but higher-value; governance latency is acceptable
Each cycle: 3-8 property decisions

Simulation calibrated to real PropTech / real estate AI deployment patterns:
  - Property Valuation (AVM):  40% of decisions
  - Mortgage Approval:         25%
  - Tenant Screening:          15%
  - AML Transaction Screen:    12%
  - Rental Pricing (Algo):      8%

Jurisdictions reflect OMNIX's GCC-first commercial strategy:
  UAE (RERA/DLD): 40% · GCC (SAMA/QFMA): 20% · UK (FCA): 20%
  EU (MCD): 15% · Global: 5%
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
import uuid
from typing import Optional

from omnix_core.evidence.decision_receipt import DecisionReceiptEngine

logger = logging.getLogger("OMNIX.RealEstate.Simulator")

CYCLE_INTERVAL  = 300.0
BATCH_SIZE_MIN  = 3
BATCH_SIZE_MAX  = 8

DECISION_TYPES = [
    ("property_valuation", 0.40),
    ("mortgage_approval",  0.25),
    ("tenant_screening",   0.15),
    ("aml_transaction",    0.12),
    ("rental_pricing",     0.08),
]

PROPERTY_TYPES_BY_DECISION: dict[str, list] = {
    "property_valuation": [
        ("Residential", 0.50), ("Commercial", 0.30),
        ("Land", 0.12), ("Mixed_Use", 0.08),
    ],
    "mortgage_approval": [
        ("Residential", 0.60), ("Commercial", 0.25), ("Industrial", 0.15),
    ],
    "tenant_screening": [
        ("Residential", 0.70), ("Commercial", 0.30),
    ],
    "aml_transaction": [
        ("Residential", 0.35), ("Commercial", 0.35),
        ("Land", 0.20), ("Mixed_Use", 0.10),
    ],
    "rental_pricing": [
        ("Residential", 0.65), ("Commercial", 0.35),
    ],
}

MARKET_SEGMENTS = [
    ("Mid_Market", 0.38),
    ("Premium",    0.30),
    ("Affordable", 0.20),
    ("Luxury",     0.12),
]

JURISDICTIONS = [
    ("UAE",    0.40),
    ("GCC",    0.20),
    ("UK",     0.20),
    ("EU",     0.15),
    ("GLOBAL", 0.05),
]

FINANCING_MODES = [
    ("Conventional", 0.50),
    ("Murabaha",     0.30),
    ("Ijarah",       0.15),
    ("Musharaka",    0.05),
]

# AML risk profile distributions
AML_PROFILE_WEIGHTS = {
    "low":    0.60,
    "medium": 0.26,
    "high":   0.10,
    "alert":  0.04,
}

AML_RISK_RANGES = {
    "low":    (0, 20),
    "medium": (20, 55),
    "high":   (55, 80),
    "alert":  (75, 100),
}

# LTV distribution by decision type and segment
LTV_RANGES_BY_SEGMENT: dict[str, tuple] = {
    "Luxury":     (50, 80),   # Luxury buyers often cash-heavy
    "Premium":    (60, 85),
    "Mid_Market": (65, 90),
    "Affordable": (70, 95),
}


def _weighted_choice(choices: list[tuple]) -> str:
    items   = [c[0] for c in choices]
    weights = [c[1] for c in choices]
    return random.choices(items, weights=weights, k=1)[0]


def _create_property_decisions_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS property_decisions (
                decision_id                VARCHAR(60)  PRIMARY KEY,
                property_id                VARCHAR(60)  NOT NULL,
                decision_type              VARCHAR(60)  NOT NULL,
                property_type              VARCHAR(50)  NOT NULL,
                market_segment             VARCHAR(30)  NOT NULL,
                jurisdiction               VARCHAR(10)  NOT NULL,
                financing_mode             VARCHAR(30)  NOT NULL,
                comparable_quality         FLOAT        NOT NULL,
                model_accuracy             FLOAT        NOT NULL,
                data_freshness             FLOAT        NOT NULL,
                market_depth               FLOAT        NOT NULL,
                ltv_ratio                  FLOAT        NOT NULL DEFAULT 0,
                price_deviation            FLOAT        NOT NULL DEFAULT 0,
                aml_risk_score             FLOAT        NOT NULL DEFAULT 0,
                comparable_alignment       FLOAT        NOT NULL,
                market_trend_score         FLOAT        NOT NULL,
                demand_index               FLOAT        NOT NULL,
                inventory_pressure         FLOAT        NOT NULL,
                liquidity_score            FLOAT        NOT NULL,
                rate_sensitivity           FLOAT        NOT NULL,
                vacancy_risk               FLOAT        NOT NULL,
                aml_flag                   BOOLEAN      DEFAULT FALSE,
                rera_compliant             BOOLEAN      DEFAULT TRUE,
                sharia_screening_passed    BOOLEAN      DEFAULT TRUE,
                beneficial_owner_verified  BOOLEAN      DEFAULT TRUE,
                days_since_last_valuation  INTEGER      DEFAULT 0,
                prior_aml_incidents        INTEGER      DEFAULT 0,
                decision                   VARCHAR(10)  NOT NULL,
                decision_score             FLOAT        NOT NULL,
                block_reason               VARCHAR(400),
                receipt_id                 VARCHAR(120) NOT NULL,
                probability_score          FLOAT        NOT NULL,
                risk_exposure              FLOAT        NOT NULL,
                signal_coherence           FLOAT        NOT NULL,
                trend_persistence          FLOAT        NOT NULL,
                stress_resilience          FLOAT        NOT NULL,
                logic_consistency          FLOAT        NOT NULL,
                trajectory_score           FLOAT        NOT NULL DEFAULT 0,
                checkpoint_results         JSONB,
                created_at                 TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS property_cycle_metrics (
                cycle_id              VARCHAR(60)  PRIMARY KEY,
                cycle_number          INTEGER      NOT NULL,
                decisions_evaluated   INTEGER      NOT NULL,
                decisions_approved    INTEGER      NOT NULL,
                decisions_blocked     INTEGER      NOT NULL,
                avg_avm_confidence    FLOAT,
                avg_ltv_ratio         FLOAT,
                avg_decision_score    FLOAT,
                approval_rate         FLOAT,
                cycle_duration_ms     INTEGER,
                created_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_decisions_created
            ON property_decisions(created_at DESC)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_decisions_type
            ON property_decisions(decision_type)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_decisions_jurisdiction
            ON property_decisions(jurisdiction)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_decisions_segment
            ON property_decisions(market_segment)
        """)
    conn.commit()
    logger.info("property_decisions + property_cycle_metrics tables ready")


def _generate_decision() -> dict:
    """Generate a realistic property transaction decision with correlated parameters."""
    decision_type   = _weighted_choice(DECISION_TYPES)
    property_opts   = PROPERTY_TYPES_BY_DECISION.get(decision_type, [("Residential", 1.0)])
    property_type   = _weighted_choice(property_opts)
    market_segment  = _weighted_choice(MARKET_SEGMENTS)
    jurisdiction    = _weighted_choice(JURISDICTIONS)
    financing_mode  = _weighted_choice(FINANCING_MODES)

    # Mortgage and tenant screening only apply financing mode if residential/commercial
    if decision_type in ("aml_transaction", "rental_pricing", "property_valuation"):
        financing_mode = "Conventional"

    # ── AVM & Valuation signals ──────────────────────────────────────────────
    # Comparable quality — commercial has fewer comparables
    comp_base = 78 if property_type == "Residential" else 68
    comparable_quality = max(15.0, min(100.0, random.gauss(comp_base, 13)))

    # Model accuracy — mature markets (UAE, UK) have better calibrated AVMs
    model_base = {"UAE": 82, "UK": 85, "EU": 80, "GCC": 74, "GLOBAL": 72}.get(jurisdiction, 78)
    model_accuracy = max(20.0, min(100.0, random.gauss(model_base, 11)))

    # Data freshness — penalized for land and industrial (fewer transactions)
    freshness_base = 85 if property_type in ("Residential", "Commercial") else 70
    data_freshness = max(20.0, min(100.0, random.gauss(freshness_base, 12)))

    # Market depth — liquidity of the sub-market
    depth_base = {"UAE": 78, "UK": 82, "EU": 75, "GCC": 70, "GLOBAL": 65}.get(jurisdiction, 73)
    market_depth = max(15.0, min(100.0, random.gauss(depth_base, 14)))

    # ── Transaction risk signals ─────────────────────────────────────────────
    # LTV — only meaningful for mortgage; others get 0
    if decision_type == "mortgage_approval":
        ltv_range = LTV_RANGES_BY_SEGMENT.get(market_segment, (65, 90))
        ltv_ratio = round(random.uniform(*ltv_range), 1)
    else:
        ltv_ratio = 0.0

    # Price deviation from AVM estimate
    dev_profile = random.choices(
        ["tight", "normal", "wide", "outlier"],
        weights=[0.45, 0.35, 0.14, 0.06]
    )[0]
    dev_map = {
        "tight":   random.uniform(0, 8),
        "normal":  random.uniform(8, 20),
        "wide":    random.uniform(20, 40),
        "outlier": random.uniform(40, 75),
    }
    price_deviation = dev_map[dev_profile]

    # AML risk
    aml_profile = random.choices(
        list(AML_PROFILE_WEIGHTS.keys()),
        weights=list(AML_PROFILE_WEIGHTS.values())
    )[0]
    aml_risk_score = round(random.uniform(*AML_RISK_RANGES[aml_profile]), 2)

    # AML flag — triggered at high risk or alert tier
    aml_flag = (aml_profile == "alert") or (aml_profile == "high" and random.random() < 0.20)

    # Comparable alignment — inter-source agreement
    comparable_alignment = max(20.0, min(100.0, random.gauss(comparable_quality * 0.90, 12)))

    # ── Market trajectory signals ────────────────────────────────────────────
    # UAE/GCC: trending upward; EU: mixed; UK: volatile
    trend_base = {"UAE": 72, "GCC": 68, "UK": 60, "EU": 58, "GLOBAL": 62}.get(jurisdiction, 62)
    market_trend_score = max(10.0, min(100.0, random.gauss(trend_base, 16)))

    demand_base = {"UAE": 70, "GCC": 65, "UK": 62, "EU": 60, "GLOBAL": 58}.get(jurisdiction, 62)
    demand_index = max(10.0, min(100.0, random.gauss(demand_base, 14)))

    # Inventory pressure — more supply reduces trend persistence
    inventory_pressure = max(10.0, min(100.0, random.gauss(45, 18)))

    # ── Stress & resilience signals ──────────────────────────────────────────
    # Residential more liquid than Land or Industrial
    liq_base = {"Residential": 72, "Commercial": 60, "Industrial": 52,
                "Mixed_Use": 58, "Land": 40}.get(property_type, 60)
    liquidity_score = max(10.0, min(100.0, random.gauss(liq_base, 14)))

    # Rate sensitivity — floating rate / long duration = high sensitivity
    rate_base = 55 if financing_mode in ("Murabaha", "Ijarah") else 48
    rate_sensitivity = max(10.0, min(100.0, random.gauss(rate_base, 16)))

    # Vacancy risk — commercial / industrial carry more
    vac_base = {"Residential": 25, "Commercial": 45, "Industrial": 55,
                "Mixed_Use": 38, "Land": 0}.get(property_type, 35)
    vacancy_risk = max(0.0, min(100.0, random.gauss(vac_base, 15)))

    # ── Compliance flags ─────────────────────────────────────────────────────
    rera_compliant = random.random() > 0.04
    beneficial_owner_verified = random.random() > 0.05

    # Sharia screening: relevant only for Islamic financing modes
    if financing_mode in ("Murabaha", "Ijarah", "Musharaka"):
        sharia_screening_passed = random.random() > 0.06
    else:
        sharia_screening_passed = True

    # AVM staleness
    days_since_last_valuation = random.choices(
        [0, 7, 30, 60, 90, 180],
        weights=[0.40, 0.25, 0.18, 0.10, 0.05, 0.02]
    )[0]

    prior_aml_incidents = random.choices([0, 1, 2, 3],
                                          weights=[0.80, 0.12, 0.06, 0.02])[0]

    property_id = f"PROP-{property_type[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"

    return {
        "decision_id":               f"RES-{uuid.uuid4().hex[:12].upper()}",
        "property_id":               property_id,
        "decision_type":             decision_type,
        "property_type":             property_type,
        "market_segment":            market_segment,
        "jurisdiction":              jurisdiction,
        "financing_mode":            financing_mode,
        "comparable_quality":        round(comparable_quality, 2),
        "model_accuracy":            round(model_accuracy, 2),
        "data_freshness":            round(data_freshness, 2),
        "market_depth":              round(market_depth, 2),
        "ltv_ratio":                 ltv_ratio,
        "price_deviation":           round(price_deviation, 2),
        "aml_risk_score":            aml_risk_score,
        "comparable_alignment":      round(comparable_alignment, 2),
        "market_trend_score":        round(market_trend_score, 2),
        "demand_index":              round(demand_index, 2),
        "inventory_pressure":        round(inventory_pressure, 2),
        "liquidity_score":           round(liquidity_score, 2),
        "rate_sensitivity":          round(rate_sensitivity, 2),
        "vacancy_risk":              round(vacancy_risk, 2),
        "aml_flag":                  aml_flag,
        "rera_compliant":            rera_compliant,
        "sharia_screening_passed":   sharia_screening_passed,
        "beneficial_owner_verified": beneficial_owner_verified,
        "days_since_last_valuation": days_since_last_valuation,
        "prior_aml_incidents":       prior_aml_incidents,
    }


def _evaluate_decision(decision_data: dict) -> dict:
    """Run property decision through OMNIX 11-checkpoint governance pipeline."""
    from omnix_core.real_estate.real_estate_signal_adapter import (
        PropertyDecisionInput, RealEstateSignalAdapter
    )

    adapter = RealEstateSignalAdapter()
    decision_input = PropertyDecisionInput(
        decision_type=decision_data["decision_type"],
        property_type=decision_data["property_type"],
        market_segment=decision_data["market_segment"],
        jurisdiction=decision_data["jurisdiction"],
        financing_mode=decision_data["financing_mode"],
        comparable_quality=decision_data["comparable_quality"],
        model_accuracy=decision_data["model_accuracy"],
        data_freshness=decision_data["data_freshness"],
        market_depth=decision_data["market_depth"],
        ltv_ratio=decision_data["ltv_ratio"],
        price_deviation=decision_data["price_deviation"],
        aml_risk_score=decision_data["aml_risk_score"],
        comparable_alignment=decision_data["comparable_alignment"],
        market_trend_score=decision_data["market_trend_score"],
        demand_index=decision_data["demand_index"],
        inventory_pressure=decision_data["inventory_pressure"],
        liquidity_score=decision_data["liquidity_score"],
        rate_sensitivity=decision_data["rate_sensitivity"],
        vacancy_risk=decision_data["vacancy_risk"],
        aml_flag=decision_data["aml_flag"],
        rera_compliant=decision_data["rera_compliant"],
        sharia_screening_passed=decision_data["sharia_screening_passed"],
        beneficial_owner_verified=decision_data["beneficial_owner_verified"],
        days_since_last_valuation=decision_data["days_since_last_valuation"],
        prior_aml_incidents=decision_data["prior_aml_incidents"],
    )

    signals = adapter.adapt(decision_input)
    signal_dict = signals.to_omnix_dict()

    # ── Hard blocks — regulatory / AML mandatory overrides, bypass engine (ADR-113) ─
    hard_block_reasons = []
    if decision_data["aml_flag"]:
        hard_block_reasons.append("CP-7: AML alert triggered — transaction BLOCKED pending investigation")
    if not decision_data["rera_compliant"]:
        hard_block_reasons.append("CP-7: RERA non-compliance detected — regulatory BLOCK")
    if decision_data["financing_mode"] in ("Murabaha", "Ijarah", "Musharaka") \
            and not decision_data["sharia_screening_passed"]:
        hard_block_reasons.append("CP-7: Sharia parameter screening failed — Islamic financing BLOCK")
    if signals.ltv_hard_block:
        ltv_max = {"Conventional": 90, "Murabaha": 85, "Ijarah": 85, "Musharaka": 80}.get(
            decision_data["financing_mode"], 90)
        hard_block_reasons.append(
            f"CP-3: LTV {decision_data['ltv_ratio']:.1f}% exceeds maximum {ltv_max}% — HARD BLOCK"
        )

    if hard_block_reasons:
        _composite = (
            signal_dict["probability_score"] + (100 - signal_dict["risk_exposure"])
            + signal_dict["signal_coherence"] + signal_dict["trend_persistence"]
            + signal_dict["stress_resilience"] + signal_dict["logic_consistency"]
        ) / 6.0
        return {
            **decision_data,
            **signal_dict,
            "domain":            "real_estate",
            "decision":          "BLOCKED",
            "decision_score":    round(_composite * 0.15, 2),
            "block_reason":      " | ".join(hard_block_reasons[:2]),
            "receipt_id":        DecisionReceiptEngine.build_receipt_id("real_estate"),
            "trajectory_score":  round(
                signal_dict["trend_persistence"] * 0.40
                + signal_dict["stress_resilience"] * 0.35
                + signal_dict["signal_coherence"] * 0.25, 2
            ),
            "checkpoint_results": hard_block_reasons,
        }

    # ── OMNIX GovernanceEvaluationEngine — 11-checkpoint pipeline (ADR-113) ─
    try:
        from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
        engine = GovernanceEvaluationEngine()
        result = engine.evaluate(
            signals=signal_dict,
            asset=f"{decision_data['property_type']}_{decision_data['decision_type']}",
            domain="real_estate",
            metadata={
                "jurisdiction":    decision_data["jurisdiction"],
                "financing_mode":  decision_data["financing_mode"],
                "market_segment":  decision_data["market_segment"],
                "decision_type":   decision_data["decision_type"],
            },
            compliance_config={
                "cag_liquidity_score": 75.0,
            },
        )
        decision_outcome   = result.get("decision", "BLOCKED")
        receipt_id         = DecisionReceiptEngine.build_receipt_id("real_estate")
        checkpoint_results = result.get("gate_results", [])
        veto_chain         = result.get("veto_chain", [])
        scores             = result.get("scores", signal_dict)
        composite = (
            scores.get("probability_score", 50) + (100 - scores.get("risk_exposure", 50))
            + scores.get("signal_coherence", 50) + scores.get("trend_persistence", 50)
            + scores.get("stress_resilience", 50) + scores.get("logic_consistency", 50)
        ) / 6.0
        trajectory_score = (
            scores.get("trend_persistence", 50) * 0.40
            + scores.get("stress_resilience", 50) * 0.35
            + scores.get("signal_coherence", 50) * 0.25
        )
        decision_score = composite
        block_reason = (
            veto_chain[0].get("checkpoint_name", "Governance threshold breach")
            if veto_chain else None
        )
    except Exception as exc:
        logger.warning(f"[RealEstate] Governance engine unavailable: {exc} — rule-based fallback active")
        composite = (
            signal_dict["probability_score"] + (100 - signal_dict["risk_exposure"])
            + signal_dict["signal_coherence"] + signal_dict["trend_persistence"]
            + signal_dict["stress_resilience"] + signal_dict["logic_consistency"]
        ) / 6.0
        decision_outcome = "APPROVED" if composite >= 62 else ("HOLD" if composite >= 48 else "BLOCKED")
        receipt_id         = DecisionReceiptEngine.build_receipt_id("real_estate")
        checkpoint_results = []
        trajectory_score   = (
            signal_dict["trend_persistence"] * 0.40
            + signal_dict["stress_resilience"] * 0.35
            + signal_dict["signal_coherence"] * 0.25
        )
        decision_score = composite
        block_reason = (
            "CP-7: Regulatory compliance alignment failure"
            if signal_dict["logic_consistency"] < 65 else
            "CP-3: Transaction risk exposure exceeds governance limit"
            if signal_dict["risk_exposure"] > 70 else None
        )

    return {
        **decision_data,
        **signal_dict,
        "domain":            "real_estate",
        "decision":          decision_outcome,
        "decision_score":    round(decision_score, 2),
        "block_reason":      block_reason,
        "receipt_id":        receipt_id,
        "trajectory_score":  round(trajectory_score, 2),
        "checkpoint_results": checkpoint_results,
    }


def _persist_decision(result: dict, conn) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO property_decisions (
                decision_id, property_id, decision_type,
                property_type, market_segment, jurisdiction, financing_mode,
                comparable_quality, model_accuracy, data_freshness, market_depth,
                ltv_ratio, price_deviation, aml_risk_score, comparable_alignment,
                market_trend_score, demand_index, inventory_pressure,
                liquidity_score, rate_sensitivity, vacancy_risk,
                aml_flag, rera_compliant, sharia_screening_passed,
                beneficial_owner_verified, days_since_last_valuation, prior_aml_incidents,
                decision, decision_score, block_reason, receipt_id,
                probability_score, risk_exposure, signal_coherence,
                trend_persistence, stress_resilience, logic_consistency,
                trajectory_score, checkpoint_results
            ) VALUES (
                %(decision_id)s, %(property_id)s, %(decision_type)s,
                %(property_type)s, %(market_segment)s, %(jurisdiction)s, %(financing_mode)s,
                %(comparable_quality)s, %(model_accuracy)s, %(data_freshness)s, %(market_depth)s,
                %(ltv_ratio)s, %(price_deviation)s, %(aml_risk_score)s, %(comparable_alignment)s,
                %(market_trend_score)s, %(demand_index)s, %(inventory_pressure)s,
                %(liquidity_score)s, %(rate_sensitivity)s, %(vacancy_risk)s,
                %(aml_flag)s, %(rera_compliant)s, %(sharia_screening_passed)s,
                %(beneficial_owner_verified)s, %(days_since_last_valuation)s, %(prior_aml_incidents)s,
                %(decision)s, %(decision_score)s, %(block_reason)s, %(receipt_id)s,
                %(probability_score)s, %(risk_exposure)s, %(signal_coherence)s,
                %(trend_persistence)s, %(stress_resilience)s, %(logic_consistency)s,
                %(trajectory_score)s, %(checkpoint_results_json)s::jsonb
            ) ON CONFLICT (decision_id) DO NOTHING
        """, {**result, "checkpoint_results_json": json.dumps(result.get("checkpoint_results", []))})
    conn.commit()


def _persist_cycle_metrics(cycle_num: int, results: list[dict], duration_ms: int, conn) -> None:
    approved = [r for r in results if r["decision"] == "APPROVED"]
    blocked  = [r for r in results if r["decision"] == "BLOCKED"]
    mortgage = [r for r in results if r["decision_type"] == "mortgage_approval"]
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO property_cycle_metrics (
                cycle_id, cycle_number, decisions_evaluated,
                decisions_approved, decisions_blocked,
                avg_avm_confidence, avg_ltv_ratio,
                avg_decision_score, approval_rate, cycle_duration_ms
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            f"RES-CYCLE-{uuid.uuid4().hex[:8].upper()}",
            cycle_num,
            len(results),
            len(approved),
            len(blocked),
            round(sum(r["model_accuracy"] for r in results) / len(results), 2) if results else 0,
            round(sum(r["ltv_ratio"] for r in mortgage) / len(mortgage), 2) if mortgage else 0,
            round(sum(r["decision_score"] for r in results) / len(results), 2) if results else 0,
            round(len(approved) / len(results), 4) if results else 0,
            duration_ms,
        ))
    conn.commit()


class RealEstateSimulator:
    """24/7 Real Estate Governance Simulator — mirrors medical and agents engines."""

    def __init__(self):
        self._running = False
        self._cycle_count = 0
        self._conn = None

    def _get_conn(self):
        import psycopg
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(os.environ["DATABASE_URL"])
        return self._conn

    def _ensure_tables(self):
        conn = self._get_conn()
        _create_property_decisions_table(conn)

    def _run_cycle(self) -> list[dict]:
        self._cycle_count += 1
        batch_size = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
        logger.info(f"[RealEstate Cycle {self._cycle_count}] Generating {batch_size} property decisions")

        t0 = time.monotonic()
        decisions = [_generate_decision() for _ in range(batch_size)]
        results   = [_evaluate_decision(d) for d in decisions]

        conn = self._get_conn()
        for r in results:
            try:
                _persist_decision(r, conn)
            except Exception as e:
                logger.error(f"Persist error: {e}")
                conn.rollback()

        duration_ms = int((time.monotonic() - t0) * 1000)
        try:
            _persist_cycle_metrics(self._cycle_count, results, duration_ms, conn)
        except Exception as e:
            logger.error(f"Cycle metrics error: {e}")
            conn.rollback()

        approved = sum(1 for r in results if r["decision"] == "APPROVED")
        blocked  = sum(1 for r in results if r["decision"] == "BLOCKED")
        logger.info(
            f"[RealEstate Cycle {self._cycle_count}] "
            f"APPROVED={approved} BLOCKED={blocked} in {duration_ms}ms"
        )
        return results

    async def run_forever(self):
        self._running = True
        self._ensure_tables()
        logger.info("OMNIX Real Estate Governance Simulator started")
        while self._running:
            try:
                self._run_cycle()
            except Exception as e:
                logger.error(f"Cycle error: {e}")
            await asyncio.sleep(CYCLE_INTERVAL)

    def stop(self):
        self._running = False
        logger.info("Real Estate simulator stopping")


_simulator_instance: Optional[RealEstateSimulator] = None
_simulator_thread = None


def start_background_simulator() -> None:
    """Start Real Estate simulator in a background thread with its own event loop."""
    import threading
    global _simulator_instance, _simulator_thread

    if _simulator_instance is not None:
        return

    _simulator_instance = RealEstateSimulator()

    def _thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_simulator_instance.run_forever())
        except Exception as e:
            logger.error(f"[RealEstateSim] Background thread error: {e}", exc_info=True)
        finally:
            loop.close()

    _simulator_thread = threading.Thread(
        target=_thread_target, daemon=True, name="RealEstateSimulator"
    )
    _simulator_thread.start()
    logger.info("Real Estate background simulator thread started")
