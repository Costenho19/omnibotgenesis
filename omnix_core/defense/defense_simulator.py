"""
OMNIX Autonomous Defense Governance Simulator
ADR-DEF-001: Autonomous Defense Governance Vertical (INTERNAL)

Runs 24/7 generating realistic autonomous defense governance decisions and
evaluating them through the OMNIX 11-checkpoint governance pipeline. Stores
results in PostgreSQL with PQC-signed receipts — identical architecture to
trading, credit, insurance, robotics, medical AI, agents, energy, real estate,
and stablecoin.

Cycle interval : 240 seconds (4 minutes) — autonomous systems operate at
                 lower cadence than trading; each decision carries higher stakes
Batch size      : 3-8 decisions per cycle
Domain code     : DEF → receipts formatted OMNIX-DEF-{12_HEX}

Decision type distribution (calibrated to real autonomous defense data):
  mission_authorization        (30%) — authorizing autonomous mission execution
  target_validation            (25%) — AI target ID verification before engagement
  rules_of_engagement_check    (20%) — verifying ROE compliance per theater
  autonomous_action_approval   (15%) — approving autonomous lethal/non-lethal action
  escalation_review            (10%) — escalation to human command authority

Platform types (reflect Anduril, Shield AI, Joby, L3Harris market):
  Autonomous_UAS        (30%) — fixed-wing / rotary autonomous drone
  Ground_Robot_UGV      (20%) — ground autonomous vehicle
  Maritime_USV          (15%) — unmanned surface vessel
  Directed_Energy_System(10%) — laser / microwave directed energy
  ISR_Surveillance      (15%) — intelligence, surveillance, reconnaissance
  Counter_UAS           (10%) — drone interception / electronic warfare

Operational theaters reflect OMNIX addressable market:
  Contested_Airspace    (25%)
  Urban_COIN            (20%)
  Maritime_Patrol       (20%)
  Border_Security       (15%)
  Critical_Infrastructure(12%)
  Cyber_Physical         (8%)
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import threading
import time
import uuid
from typing import Optional

from omnix_core.defense.defense_signal_adapter import (
    DefenseDecisionInput,
    DefenseSignalAdapter,
)
from omnix_core.evidence.decision_receipt import DecisionReceiptEngine

logger = logging.getLogger("OMNIX.Defense.Simulator")

CYCLE_INTERVAL  = 240.0
BATCH_SIZE_MIN  = 3
BATCH_SIZE_MAX  = 8

DECISION_TYPES = [
    ("mission_authorization",      0.30),
    ("target_validation",          0.25),
    ("rules_of_engagement_check",  0.20),
    ("autonomous_action_approval", 0.15),
    ("escalation_review",          0.10),
]

PLATFORM_TYPES = [
    ("Autonomous_UAS",         0.30),
    ("Ground_Robot_UGV",       0.20),
    ("Maritime_USV",           0.15),
    ("Directed_Energy_System", 0.10),
    ("ISR_Surveillance",       0.15),
    ("Counter_UAS",            0.10),
]

OPERATIONAL_THEATERS = [
    ("Contested_Airspace",      0.25),
    ("Urban_COIN",              0.20),
    ("Maritime_Patrol",         0.20),
    ("Border_Security",         0.15),
    ("Critical_Infrastructure", 0.12),
    ("Cyber_Physical",          0.08),
]

HARD_BLOCK_SCENARIOS = {
    "civilian_proximity":   0.022,
    "roe_violation":        0.018,
    "cyber_intrusion":      0.015,
    "friendly_fire_risk":   0.020,
    "chain_of_command":     0.012,
    "legal_prohibition":    0.008,
}

ENGAGEMENT_RANGES: dict[str, tuple] = {
    "mission_authorization":      (1.0, 120.0),
    "target_validation":          (0.2, 45.0),
    "rules_of_engagement_check":  (0.5, 80.0),
    "autonomous_action_approval": (0.1, 35.0),
    "escalation_review":          (1.0, 200.0),
}

MISSION_DURATION: dict[str, tuple] = {
    "mission_authorization":      (0.5, 8.0),
    "target_validation":          (0.1, 2.0),
    "rules_of_engagement_check":  (0.2, 4.0),
    "autonomous_action_approval": (0.05, 1.5),
    "escalation_review":          (1.0, 12.0),
}


def _weighted_choice(choices: list[tuple]) -> str:
    items   = [c[0] for c in choices]
    weights = [c[1] for c in choices]
    return random.choices(items, weights=weights, k=1)[0]


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def _create_defense_tables(conn) -> None:
    """Create defense governance tables if they do not exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS defense_decisions (
                id                          SERIAL PRIMARY KEY,
                decision_id                 VARCHAR(64)   NOT NULL UNIQUE,
                decision_type               VARCHAR(40)   NOT NULL,
                platform_type               VARCHAR(40)   NOT NULL,
                operational_theater         VARCHAR(40)   NOT NULL,
                engagement_range_km         FLOAT         NOT NULL DEFAULT 0,
                mission_duration_hrs        FLOAT         NOT NULL DEFAULT 0,
                target_confidence           FLOAT,
                target_discrimination       FLOAT,
                collateral_damage_estimate  FLOAT,
                roe_compliance_score        FLOAT,
                comms_integrity             FLOAT,
                cyber_vulnerability_score   FLOAT,
                mission_necessity_score     FLOAT,
                human_oversight_available   FLOAT,
                legal_authorization_score   FLOAT,
                environmental_conditions    FLOAT,
                platform_readiness          FLOAT,
                geofence_compliance         FLOAT,
                iff_confidence              FLOAT,
                engagement_risk_index       FLOAT         DEFAULT 0,
                civilian_proximity_flag     BOOLEAN       DEFAULT FALSE,
                roe_violation_flag          BOOLEAN       DEFAULT FALSE,
                cyber_intrusion_flag        BOOLEAN       DEFAULT FALSE,
                friendly_fire_risk_flag     BOOLEAN       DEFAULT FALSE,
                chain_of_command_break      BOOLEAN       DEFAULT FALSE,
                legal_prohibition_flag      BOOLEAN       DEFAULT FALSE,
                decision                    VARCHAR(10)   NOT NULL DEFAULT 'PENDING',
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
                receipt_id                  VARCHAR(64),
                domain                      VARCHAR(32)   DEFAULT 'defense_governance',
                created_at                  TIMESTAMPTZ   DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS defense_cycle_metrics (
                id                  SERIAL PRIMARY KEY,
                cycle_id            VARCHAR(64) NOT NULL,
                total_decisions     INTEGER     NOT NULL DEFAULT 0,
                approved            INTEGER     NOT NULL DEFAULT 0,
                blocked             INTEGER     NOT NULL DEFAULT 0,
                held                INTEGER     NOT NULL DEFAULT 0,
                hard_blocks         INTEGER     NOT NULL DEFAULT 0,
                avg_target_conf     FLOAT       DEFAULT 0,
                avg_collateral_est  FLOAT       DEFAULT 0,
                avg_roe_compliance  FLOAT       DEFAULT 0,
                missions_authorized INTEGER     DEFAULT 0,
                targets_validated   INTEGER     DEFAULT 0,
                duration_ms         INTEGER     DEFAULT 0,
                created_at          TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_defense_decisions_type
            ON defense_decisions (decision_type)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_defense_decisions_platform
            ON defense_decisions (platform_type)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_defense_decisions_theater
            ON defense_decisions (operational_theater)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_defense_decisions_created
            ON defense_decisions (created_at DESC)
        """)
        conn.commit()
    logger.info("defense_decisions + defense_cycle_metrics tables ready")


def _generate_decision(
    decision_type: str,
    platform_type: str,
    theater: str,
    cycle_id: str,
) -> dict:
    """Generate one realistic autonomous defense governance decision."""
    adapter = DefenseSignalAdapter()

    civilian_proximity   = False
    roe_violation        = False
    cyber_intrusion      = False
    friendly_fire_risk   = False
    chain_break          = False
    legal_prohibition    = False

    for scenario, prob in HARD_BLOCK_SCENARIOS.items():
        if random.random() < prob:
            if scenario == "civilian_proximity":
                civilian_proximity = True
            elif scenario == "roe_violation":
                roe_violation = True
            elif scenario == "cyber_intrusion":
                cyber_intrusion = True
            elif scenario == "friendly_fire_risk":
                friendly_fire_risk = True
            elif scenario == "chain_of_command":
                chain_break = True
            elif scenario == "legal_prohibition":
                legal_prohibition = True
            break

    is_urban     = theater == "Urban_COIN"
    is_contested = theater == "Contested_Airspace"
    is_lethal    = decision_type in ("target_validation", "autonomous_action_approval")

    target_conf    = _clamp(random.gauss(72 if not is_urban else 62, 16))
    target_discrim = _clamp(random.gauss(70 if not is_urban else 55, 18))
    collateral     = _clamp(random.gauss(78 if not is_lethal else 65, 20))
    roe_score      = _clamp(random.gauss(76, 14))
    comms          = _clamp(random.gauss(75 if not is_contested else 58, 18))
    cyber_score    = _clamp(random.gauss(70, 16))
    necessity      = _clamp(random.gauss(72, 14))
    human_avail    = _clamp(random.gauss(68, 20))
    legal_score    = _clamp(random.gauss(74, 12))
    env_conds      = _clamp(random.gauss(70, 18))
    plat_ready     = _clamp(random.gauss(80, 12))
    geofence       = _clamp(random.gauss(85, 10))
    iff_conf       = _clamp(random.gauss(74 if not friendly_fire_risk else 28, 16))

    if cyber_intrusion:
        comms = _clamp(random.uniform(5.0, 25.0))
        cyber_score = _clamp(random.uniform(5.0, 20.0))

    range_lo, range_hi = ENGAGEMENT_RANGES.get(decision_type, (1.0, 50.0))
    dur_lo, dur_hi     = MISSION_DURATION.get(decision_type, (0.5, 4.0))
    engagement_range   = round(random.uniform(range_lo, range_hi), 2)
    mission_duration   = round(random.uniform(dur_lo, dur_hi), 2)

    inp = DefenseDecisionInput(
        decision_type=decision_type,
        platform_type=platform_type,
        operational_theater=theater,
        target_confidence=target_conf,
        target_discrimination=target_discrim,
        collateral_damage_estimate=collateral,
        roe_compliance_score=roe_score,
        comms_integrity=comms,
        cyber_vulnerability_score=cyber_score,
        mission_necessity_score=necessity,
        human_oversight_available=human_avail,
        legal_authorization_score=legal_score,
        environmental_conditions=env_conds,
        platform_readiness=plat_ready,
        geofence_compliance=geofence,
        iff_confidence=iff_conf,
        civilian_proximity_flag=civilian_proximity,
        roe_violation_flag=roe_violation,
        cyber_intrusion_flag=cyber_intrusion,
        friendly_fire_risk_flag=friendly_fire_risk,
        chain_of_command_break=chain_break,
        legal_prohibition_flag=legal_prohibition,
        engagement_range_km=engagement_range,
        mission_duration_hrs=mission_duration,
    )

    signals = adapter.adapt(inp)
    sig_dict = signals.to_omnix_dict()

    decision_id = f"DEF-{cycle_id[:8].upper()}-{uuid.uuid4().hex[:8].upper()}"

    if signals.hard_block_reason:
        _composite = (
            sig_dict["probability_score"] + (100.0 - sig_dict["risk_exposure"])
            + sig_dict["signal_coherence"] + sig_dict["trend_persistence"]
            + sig_dict["stress_resilience"] + sig_dict["logic_consistency"]
        ) / 6.0
        trajectory_score = _clamp(
            sig_dict["trend_persistence"] * 0.45
            + sig_dict["signal_coherence"] * 0.35
            + sig_dict["stress_resilience"] * 0.20
        )
        decision       = "BLOCKED"
        block_reason   = signals.hard_block_reason
        decision_score = round(_composite * 0.12, 2)
        receipt_id     = None
    else:
        try:
            from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
            engine = GovernanceEvaluationEngine()
            result = engine.evaluate(
                signals=sig_dict,
                asset=f"{platform_type}_{decision_type}",
                domain="defense_governance",
                metadata={
                    "operational_theater":  theater,
                    "decision_type":        decision_type,
                    "platform_type":        platform_type,
                    "engagement_range_km":  engagement_range,
                    "roe_compliance_score": roe_score,
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
                + scores.get("stress_resilience", 50) * 0.20
            )
            veto_chain   = result.get("veto_chain", [])
            decision_score = round(_composite, 2)
            block_reason = (
                veto_chain[0].get("checkpoint_name", "Governance threshold breach")
                if veto_chain else
                ("COMMAND_REVIEW: composite score requires human commander validation"
                 if decision == "HOLD" else None)
            )
        except Exception as exc:
            logger.warning(f"[Defense] Governance engine unavailable: {exc} — rule-based fallback")
            _composite = (
                sig_dict["probability_score"] + (100.0 - sig_dict["risk_exposure"])
                + sig_dict["signal_coherence"] + sig_dict["trend_persistence"]
                + sig_dict["stress_resilience"] + sig_dict["logic_consistency"]
            ) / 6.0
            trajectory_score = _clamp(
                sig_dict["trend_persistence"] * 0.45
                + sig_dict["signal_coherence"] * 0.35
                + sig_dict["stress_resilience"] * 0.20
            )
            if _composite >= 72.0:
                decision, block_reason = "APPROVED", None
            elif _composite >= 54.0:
                decision = "HOLD"
                block_reason = "COMMAND_REVIEW: composite score requires human commander validation"
            else:
                decision = "BLOCKED"
                block_reason = "HIGH_RISK: governance score below autonomous execution threshold"
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
                    domain="defense_governance",
                    signals=sig_dict,
                )
            )
            receipt_id = receipt.get("receipt_id")
            loop.close()
        except Exception as re:
            logger.debug(f"Receipt generation skipped: {re}")

    return {
        "decision_id":                decision_id,
        "decision_type":              decision_type,
        "platform_type":              platform_type,
        "operational_theater":        theater,
        "engagement_range_km":        engagement_range,
        "mission_duration_hrs":       mission_duration,
        "target_confidence":          signals.target_confidence,
        "target_discrimination":      target_discrim,
        "collateral_damage_estimate": signals.collateral_damage_estimate,
        "roe_compliance_score":       signals.roe_compliance_score,
        "comms_integrity":            signals.comms_integrity,
        "cyber_vulnerability_score":  cyber_score,
        "mission_necessity_score":    necessity,
        "human_oversight_available":  signals.human_oversight_available,
        "legal_authorization_score":  signals.legal_authorization_score,
        "environmental_conditions":   env_conds,
        "platform_readiness":         plat_ready,
        "geofence_compliance":        geofence,
        "iff_confidence":             signals.iff_confidence,
        "engagement_risk_index":      signals.engagement_risk_index,
        "civilian_proximity_flag":    civilian_proximity,
        "roe_violation_flag":         roe_violation,
        "cyber_intrusion_flag":       cyber_intrusion,
        "friendly_fire_risk_flag":    friendly_fire_risk,
        "chain_of_command_break":     chain_break,
        "legal_prohibition_flag":     legal_prohibition,
        "decision":                   decision,
        "decision_score":             decision_score,
        "block_reason":               block_reason,
        "hard_block_reason":          signals.hard_block_reason,
        "probability_score":          sig_dict["probability_score"],
        "risk_exposure":              sig_dict["risk_exposure"],
        "signal_coherence":           sig_dict["signal_coherence"],
        "trend_persistence":          sig_dict["trend_persistence"],
        "stress_resilience":          sig_dict["stress_resilience"],
        "logic_consistency":          sig_dict["logic_consistency"],
        "trajectory_score":           round(trajectory_score, 2),
        "receipt_id":                 receipt_id,
        "domain":                     "defense_governance",
    }


def _store_decision(conn, d: dict) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO defense_decisions (
                decision_id, decision_type, platform_type, operational_theater,
                engagement_range_km, mission_duration_hrs,
                target_confidence, target_discrimination, collateral_damage_estimate,
                roe_compliance_score, comms_integrity, cyber_vulnerability_score,
                mission_necessity_score, human_oversight_available, legal_authorization_score,
                environmental_conditions, platform_readiness, geofence_compliance,
                iff_confidence, engagement_risk_index,
                civilian_proximity_flag, roe_violation_flag, cyber_intrusion_flag,
                friendly_fire_risk_flag, chain_of_command_break, legal_prohibition_flag,
                decision, decision_score, block_reason, hard_block_reason,
                probability_score, risk_exposure, signal_coherence,
                trend_persistence, stress_resilience, logic_consistency,
                trajectory_score, receipt_id, domain
            ) VALUES (
                %(decision_id)s, %(decision_type)s, %(platform_type)s, %(operational_theater)s,
                %(engagement_range_km)s, %(mission_duration_hrs)s,
                %(target_confidence)s, %(target_discrimination)s, %(collateral_damage_estimate)s,
                %(roe_compliance_score)s, %(comms_integrity)s, %(cyber_vulnerability_score)s,
                %(mission_necessity_score)s, %(human_oversight_available)s, %(legal_authorization_score)s,
                %(environmental_conditions)s, %(platform_readiness)s, %(geofence_compliance)s,
                %(iff_confidence)s, %(engagement_risk_index)s,
                %(civilian_proximity_flag)s, %(roe_violation_flag)s, %(cyber_intrusion_flag)s,
                %(friendly_fire_risk_flag)s, %(chain_of_command_break)s, %(legal_prohibition_flag)s,
                %(decision)s, %(decision_score)s, %(block_reason)s, %(hard_block_reason)s,
                %(probability_score)s, %(risk_exposure)s, %(signal_coherence)s,
                %(trend_persistence)s, %(stress_resilience)s, %(logic_consistency)s,
                %(trajectory_score)s, %(receipt_id)s, %(domain)s
            ) ON CONFLICT (decision_id) DO NOTHING
        """, d)
    conn.commit()


def _run_cycle(conn, cycle_num: int) -> None:
    cycle_id   = uuid.uuid4().hex
    batch_size = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
    t0         = time.time()

    approved = blocked = held = hard_blocks = 0
    missions_auth = targets_val = 0
    conf_sum = collateral_sum = roe_sum = 0.0

    logger.info(f"[Defense Cycle {cycle_num}] Generating {batch_size} defense governance decisions")

    for _ in range(batch_size):
        d_type   = _weighted_choice(DECISION_TYPES)
        platform = _weighted_choice(PLATFORM_TYPES)
        theater  = _weighted_choice(OPERATIONAL_THEATERS)

        try:
            d = _generate_decision(d_type, platform, theater, cycle_id)
            _store_decision(conn, d)
        except Exception as e:
            logger.warning(f"Defense decision generation error: {e}")
            continue

        conf_sum      += d["target_confidence"]
        collateral_sum += d["collateral_damage_estimate"]
        roe_sum        += d["roe_compliance_score"]

        if d["decision"] == "APPROVED":
            approved += 1
            if d_type == "mission_authorization":
                missions_auth += 1
            if d_type == "target_validation":
                targets_val += 1
        elif d["decision"] == "BLOCKED":
            blocked += 1
            if d["hard_block_reason"]:
                hard_blocks += 1
        else:
            held += 1

    n          = batch_size or 1
    duration_ms = int((time.time() - t0) * 1000)

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO defense_cycle_metrics
                (cycle_id, total_decisions, approved, blocked, held, hard_blocks,
                 avg_target_conf, avg_collateral_est, avg_roe_compliance,
                 missions_authorized, targets_validated, duration_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            cycle_id, batch_size, approved, blocked, held, hard_blocks,
            round(conf_sum / n, 2), round(collateral_sum / n, 2), round(roe_sum / n, 2),
            missions_auth, targets_val, duration_ms,
        ))
        conn.commit()

    logger.info(
        f"[Defense Cycle {cycle_num}] "
        f"APPROVED={approved} BLOCKED={blocked} HELD={held} HARD_BLOCKS={hard_blocks} | "
        f"Missions auth'd={missions_auth} Targets val'd={targets_val} | "
        f"{duration_ms}ms"
    )


def _simulator_loop() -> None:
    import psycopg
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not set — Defense Governance simulator cannot start")
        return

    conn = psycopg.connect(db_url)
    _create_defense_tables(conn)
    logger.info("Autonomous Defense Governance Simulator started — 24/7 mode")

    cycle = 1
    while True:
        try:
            _run_cycle(conn, cycle)
            cycle += 1
        except Exception as e:
            logger.error(f"Defense cycle {cycle} error: {e}")
            try:
                conn.rollback()
            except Exception:
                try:
                    conn = psycopg.connect(db_url)
                except Exception:
                    pass
        time.sleep(CYCLE_INTERVAL)


_started = False
_lock    = threading.Lock()


def start_background_simulator() -> None:
    global _started
    with _lock:
        if _started:
            return
        _started = True
    t = threading.Thread(
        target=_simulator_loop,
        daemon=True,
        name="DefenseGovernanceSim",
    )
    t.start()
    logger.info("Autonomous Defense Governance background simulator thread started")
