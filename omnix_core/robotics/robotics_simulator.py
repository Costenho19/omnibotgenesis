"""
OMNIX Robotics Governance Simulator
ADR-055: Robotics & Autonomous Systems Governance Vertical

Runs 24/7 generating realistic robot action requests and evaluating them
through the OMNIX 11-checkpoint governance pipeline. Stores results in
PostgreSQL with PQC-signed receipts.

Cycle interval: 180 seconds (3 minutes) — fast cadence for high-throughput robotics.
Each cycle processes a batch of 6-15 robot actions.

Simulation calibrated to industrial robotics market:
  - Automotive: 30% of actions — welding, assembly, quality control
  - Electronics: 22% — precision pick-and-place, inspection
  - Logistics: 20% — navigation, packaging, sorting
  - Pharma: 15% — sterile handling, inspection
  - Food: 8% — packaging, sorting, quality check
  - Construction: 5% — heavy material handling
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import time
import uuid
from typing import Optional

from omnix_core.evidence.decision_receipt import DecisionReceiptEngine

logger = logging.getLogger("OMNIX.Robotics.Simulator")

CYCLE_INTERVAL = 300.0       # 5 minutes between cycles
BATCH_SIZE_MIN = 6
BATCH_SIZE_MAX = 15

INDUSTRIES = [
    ("Automotive", 0.30),
    ("Electronics", 0.22),
    ("Logistics", 0.20),
    ("Pharma", 0.15),
    ("Food", 0.08),
    ("Construction", 0.05),
]

ROBOT_TYPES_BY_INDUSTRY: dict[str, list] = {
    "Automotive": [("Industrial_Arm", 0.65), ("Cobot", 0.20), ("AGV", 0.15)],
    "Electronics": [("Industrial_Arm", 0.50), ("Cobot", 0.35), ("AMR", 0.15)],
    "Logistics": [("AMR", 0.45), ("AGV", 0.35), ("Industrial_Arm", 0.20)],
    "Pharma": [("Industrial_Arm", 0.40), ("Cobot", 0.40), ("AMR", 0.20)],
    "Food": [("Industrial_Arm", 0.45), ("Cobot", 0.30), ("AMR", 0.25)],
    "Construction": [("Industrial_Arm", 0.40), ("AMR", 0.35), ("Drone", 0.25)],
}

ACTIONS_BY_ROBOT: dict[str, list] = {
    "Industrial_Arm": [
        ("welding", 0.25), ("assembly_critical", 0.30),
        ("pick_and_place_standard", 0.25), ("pick_and_place_fragile", 0.20),
    ],
    "Cobot": [
        ("assembly_critical", 0.35), ("pick_and_place_fragile", 0.30),
        ("quality_check", 0.20), ("pick_and_place_standard", 0.15),
    ],
    "AMR": [
        ("navigation_crowded", 0.40), ("navigation_clear", 0.40),
        ("packaging", 0.20),
    ],
    "AGV": [
        ("navigation_clear", 0.60), ("navigation_crowded", 0.25),
        ("charging", 0.15),
    ],
    "Drone": [
        ("inspection", 0.55), ("navigation_clear", 0.30),
        ("navigation_crowded", 0.15),
    ],
    "Humanoid": [
        ("assembly_critical", 0.40), ("pick_and_place_standard", 0.30),
        ("navigation_crowded", 0.30),
    ],
}

ENVIRONMENTS: dict[str, list] = {
    "Automotive": [("structured", 0.70), ("semi_structured", 0.30)],
    "Electronics": [("structured", 0.80), ("semi_structured", 0.20)],
    "Logistics": [("semi_structured", 0.50), ("structured", 0.30), ("unstructured", 0.20)],
    "Pharma": [("structured", 0.90), ("semi_structured", 0.10)],
    "Food": [("structured", 0.60), ("semi_structured", 0.40)],
    "Construction": [("unstructured", 0.50), ("outdoor", 0.30), ("semi_structured", 0.20)],
}


def _ensure_robotics_tables(conn) -> None:
    """Create robotics tables if they don't exist — idempotent, safe for Railway fresh deploys."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS robot_actions (
                id SERIAL PRIMARY KEY,
                action_id VARCHAR(64) UNIQUE NOT NULL,
                robot_id VARCHAR(64),
                robot_type VARCHAR(32),
                industry VARCHAR(32),
                action_type VARCHAR(32),
                environment VARCHAR(32),
                sensor_confidence NUMERIC(6,2),
                success_probability NUMERIC(6,2),
                collision_risk NUMERIC(6,2),
                sensor_fusion_agreement NUMERIC(6,2),
                environmental_stability NUMERIC(6,2),
                mechanical_margin NUMERIC(6,2),
                mission_logic_score NUMERIC(6,2),
                payload_kg NUMERIC(8,2),
                speed_ms NUMERIC(6,2),
                proximity_cm NUMERIC(8,2),
                battery_pct NUMERIC(5,2),
                temperature_c NUMERIC(6,2),
                decision VARCHAR(16),
                decision_score NUMERIC(6,2),
                block_reason TEXT,
                receipt_id VARCHAR(128),
                probability_score NUMERIC(6,2),
                risk_exposure NUMERIC(6,2),
                signal_coherence NUMERIC(6,2),
                trend_persistence NUMERIC(6,2),
                stress_resilience NUMERIC(6,2),
                logic_consistency NUMERIC(6,2),
                checkpoint_results JSONB DEFAULT '[]',
                trajectory_score NUMERIC(6,2),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS robotics_cycle_metrics (
                id SERIAL PRIMARY KEY,
                cycle_id VARCHAR(64) UNIQUE NOT NULL,
                cycle_number INTEGER,
                actions_evaluated INTEGER,
                actions_approved INTEGER,
                actions_blocked INTEGER,
                avg_sensor_confidence NUMERIC(6,2),
                avg_collision_risk NUMERIC(6,2),
                avg_decision_score NUMERIC(6,2),
                approval_rate NUMERIC(6,4),
                safety_incidents_prevented INTEGER,
                cycle_duration_ms INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_robot_actions_decision
            ON robot_actions (decision)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_robot_actions_type
            ON robot_actions (robot_type)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_robot_actions_created
            ON robot_actions (created_at DESC)
        """)
    conn.commit()
    logger.info("robot_actions + robotics_cycle_metrics tables ready")


def _weighted_choice(choices: list[tuple]) -> str:
    items = [c[0] for c in choices]
    weights = [c[1] for c in choices]
    return random.choices(items, weights=weights, k=1)[0]


def _generate_action(robot_fleet: dict) -> dict:
    """Generate a realistic robot action request with correlated sensor data."""
    industry = _weighted_choice(INDUSTRIES)
    robot_types = ROBOT_TYPES_BY_INDUSTRY.get(industry, [("Industrial_Arm", 1.0)])
    robot_type = _weighted_choice(robot_types)
    actions = ACTIONS_BY_ROBOT.get(robot_type, [("pick_and_place_standard", 1.0)])
    action_type = _weighted_choice(actions)
    environments = ENVIRONMENTS.get(industry, [("structured", 1.0)])
    environment = _weighted_choice(environments)

    # Use persistent robot IDs to create realistic fleet
    fleet_key = f"{industry}_{robot_type}"
    if fleet_key not in robot_fleet:
        robot_fleet[fleet_key] = [f"RBT-{uuid.uuid4().hex[:8].upper()}" for _ in range(random.randint(3, 12))]
    robot_id = random.choice(robot_fleet[fleet_key])

    # Sensor profiles — usually reliable, occasionally degraded
    sensor_profile = random.choices(
        ["excellent", "good", "degraded", "faulty"],
        weights=[0.40, 0.42, 0.14, 0.04]
    )[0]
    sensor_profiles = {
        "excellent": (90, 100), "good": (72, 90),
        "degraded": (45, 72), "faulty": (10, 45)
    }
    s_min, s_max = sensor_profiles[sensor_profile]
    sensor_confidence = random.uniform(s_min, s_max)

    # LiDAR and camera generally correlate with sensor_confidence but have some variance
    lidar_agreement = max(0.0, min(100.0, sensor_confidence + random.gauss(0, 8)))
    camera_confidence = max(0.0, min(100.0, sensor_confidence + random.gauss(0, 10)))
    imu_stability = max(0.0, min(100.0, random.gauss(82, 12)))

    # Physical parameters by robot type
    payload_limits = {
        "Industrial_Arm": (0, 250), "Cobot": (0, 35),
        "AMR": (0, 1500), "AGV": (0, 5000), "Drone": (0, 5), "Humanoid": (0, 20)
    }
    speed_limits = {
        "Industrial_Arm": (0, 2.5), "Cobot": (0, 1.5),
        "AMR": (0, 2.0), "AGV": (0, 1.5), "Drone": (0, 15.0), "Humanoid": (0, 1.5)
    }
    max_payload = payload_limits.get(robot_type, (0, 100))[1]
    max_speed = speed_limits.get(robot_type, (0, 2.0))[1]

    # Typical operating point — 30-80% of capacity
    payload_kg = round(max_payload * random.uniform(0.1, 0.85), 2)
    speed_ms = round(max_speed * random.uniform(0.1, 0.90), 3)

    # Environment-dependent proximity
    env_proximity = {
        "structured": (50, 500), "semi_structured": (25, 300),
        "unstructured": (10, 200), "outdoor": (20, 1000)
    }
    prox_min, prox_max = env_proximity.get(environment, (20, 300))
    proximity_cm = round(random.uniform(prox_min, prox_max), 1)

    # System health — mostly good, occasional degraded
    battery_pct = round(random.gauss(72, 20), 1)
    battery_pct = max(5.0, min(100.0, battery_pct))

    motor_temp_c = round(random.gauss(58, 15), 1)
    motor_temp_c = max(20.0, min(95.0, motor_temp_c))

    joint_stress_pct = round(random.gauss(45, 18), 1)
    joint_stress_pct = max(0.0, min(100.0, joint_stress_pct))

    # Mission and environment context
    mission_logic_score = max(20.0, min(100.0, random.gauss(82, 14)))
    environmental_stability = max(10.0, min(100.0, random.gauss(
        75 if environment == "structured" else 58, 15
    )))
    historical_success_rate = max(40.0, min(99.0, random.gauss(88, 10)))

    return {
        "action_id": f"ACT-{uuid.uuid4().hex[:12].upper()}",
        "robot_id": robot_id,
        "robot_type": robot_type,
        "industry": industry,
        "action_type": action_type,
        "environment": environment,
        "sensor_confidence": round(sensor_confidence, 2),
        "lidar_agreement": round(lidar_agreement, 2),
        "camera_confidence": round(camera_confidence, 2),
        "imu_stability": round(imu_stability, 2),
        "proximity_cm": proximity_cm,
        "payload_kg": payload_kg,
        "max_payload_kg": max_payload,
        "speed_ms": speed_ms,
        "max_speed_ms": max_speed,
        "battery_pct": battery_pct,
        "motor_temp_c": motor_temp_c,
        "joint_stress_pct": joint_stress_pct,
        "mission_logic_score": round(mission_logic_score, 2),
        "environmental_stability": round(environmental_stability, 2),
        "historical_success_rate": round(historical_success_rate, 2),
    }


def _evaluate_action(action_data: dict) -> dict:
    """Run robot action through OMNIX governance pipeline."""
    from omnix_core.robotics.robotics_signal_adapter import (
        RobotActionInput, RoboticsSignalAdapter
    )

    adapter = RoboticsSignalAdapter()
    action_input = RobotActionInput(
        robot_id=action_data["robot_id"],
        robot_type=action_data["robot_type"],
        industry=action_data["industry"],
        action_type=action_data["action_type"],
        environment=action_data["environment"],
        sensor_confidence=action_data["sensor_confidence"],
        lidar_agreement=action_data["lidar_agreement"],
        camera_confidence=action_data["camera_confidence"],
        imu_stability=action_data["imu_stability"],
        proximity_cm=action_data["proximity_cm"],
        payload_kg=action_data["payload_kg"],
        max_payload_kg=action_data["max_payload_kg"],
        speed_ms=action_data["speed_ms"],
        max_speed_ms=action_data["max_speed_ms"],
        battery_pct=action_data["battery_pct"],
        motor_temp_c=action_data["motor_temp_c"],
        joint_stress_pct=action_data["joint_stress_pct"],
        mission_logic_score=action_data["mission_logic_score"],
        environmental_stability=action_data["environmental_stability"],
        historical_success_rate=action_data["historical_success_rate"],
    )

    signals = adapter.adapt(action_input)
    signals_dict = signals.to_omnix_dict()

    try:
        from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
        engine = GovernanceEvaluationEngine()
        result = engine.evaluate(
            signals=signals_dict,
            asset=f"{action_data['robot_type']}_{action_data['action_type']}",
            domain="robotics",
            metadata={
                "industry": action_data["industry"],
                "environment": action_data["environment"],
            },
            compliance_config={
                "cag_liquidity_score": 100.0,
            },
        )
        decision = result.get("decision", "BLOCKED")
        receipt_id = DecisionReceiptEngine.build_receipt_id("robotics")
        checkpoint_results = result.get("gate_results", [])
        veto_chain = result.get("veto_chain", [])
        cp_passed = result.get("checkpoints_passed", 0)
        scores = result.get("scores", signals_dict)
        composite = (scores.get("probability_score", 50) + (100 - scores.get("risk_exposure", 50)) +
                     scores.get("signal_coherence", 50) + scores.get("trend_persistence", 50) +
                     scores.get("stress_resilience", 50) + scores.get("logic_consistency", 50)) / 6.0
        trajectory_score = composite
        decision_score = composite
        block_reason = veto_chain[0].get("checkpoint_name", "Governance threshold breach") if veto_chain else None
    except Exception as e:
        logger.warning(f"Governance engine error: {e} — using rule-based fallback")
        composite = (signals.probability_score + (100 - signals.risk_exposure) +
                     signals.signal_coherence + signals.trend_persistence +
                     signals.stress_resilience + signals.logic_consistency) / 6.0
        if composite >= 65:
            decision = "APPROVED"
        elif composite >= 48:
            decision = "HOLD"
        else:
            decision = "BLOCKED"
        receipt_id = DecisionReceiptEngine.build_receipt_id("robotics")
        checkpoint_results = []
        trajectory_score = composite
        decision_score = composite
        block_reason = "Sensor fusion inconsistency" if signals.signal_coherence < 40 else \
                       "High collision risk" if signals.risk_exposure > 72 else None

    return {
        **action_data,
        "decision": decision,
        "decision_score": round(decision_score, 2),
        "block_reason": block_reason,
        "receipt_id": receipt_id,
        "probability_score": round(signals.probability_score, 2),
        "risk_exposure": round(signals.risk_exposure, 2),
        "signal_coherence": round(signals.signal_coherence, 2),
        "trend_persistence": round(signals.trend_persistence, 2),
        "stress_resilience": round(signals.stress_resilience, 2),
        "logic_consistency": round(signals.logic_consistency, 2),
        "checkpoint_results": checkpoint_results,
        "trajectory_score": round(trajectory_score, 2),
    }


def _persist_action(result: dict, conn) -> None:
    import json
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO robot_actions (
                action_id, robot_id, robot_type, industry, action_type, environment,
                sensor_confidence, success_probability, collision_risk,
                sensor_fusion_agreement, environmental_stability, mechanical_margin,
                mission_logic_score, payload_kg, speed_ms, proximity_cm,
                battery_pct, temperature_c,
                decision, decision_score, block_reason, receipt_id,
                probability_score, risk_exposure, signal_coherence,
                trend_persistence, stress_resilience, logic_consistency,
                checkpoint_results, trajectory_score
            ) VALUES (
                %(action_id)s, %(robot_id)s, %(robot_type)s, %(industry)s,
                %(action_type)s, %(environment)s,
                %(sensor_confidence)s, %(probability_score)s, %(risk_exposure)s,
                %(signal_coherence)s, %(environmental_stability)s, %(stress_resilience)s,
                %(mission_logic_score)s, %(payload_kg)s, %(speed_ms)s, %(proximity_cm)s,
                %(battery_pct)s, %(motor_temp_c)s,
                %(decision)s, %(decision_score)s, %(block_reason)s, %(receipt_id)s,
                %(probability_score)s, %(risk_exposure)s, %(signal_coherence)s,
                %(trend_persistence)s, %(stress_resilience)s, %(logic_consistency)s,
                %(checkpoint_results_json)s::jsonb, %(trajectory_score)s
            ) ON CONFLICT (action_id) DO NOTHING
        """, {**result, "checkpoint_results_json": json.dumps(result.get("checkpoint_results", []))})
    conn.commit()


def _persist_cycle_metrics(cycle_num: int, results: list[dict], duration_ms: int, conn) -> None:
    approved = [r for r in results if r["decision"] == "APPROVED"]
    blocked = [r for r in results if r["decision"] == "BLOCKED"]
    safety_prevented = len([r for r in blocked if r.get("risk_exposure", 0) > 65])

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO robotics_cycle_metrics (
                cycle_id, cycle_number, actions_evaluated, actions_approved, actions_blocked,
                avg_sensor_confidence, avg_collision_risk, avg_decision_score,
                approval_rate, safety_incidents_prevented, cycle_duration_ms
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            f"RBT-CYCLE-{uuid.uuid4().hex[:8].upper()}",
            cycle_num,
            len(results),
            len(approved),
            len(blocked),
            round(sum(r["sensor_confidence"] for r in results) / len(results), 2) if results else 0,
            round(sum(r["risk_exposure"] for r in results) / len(results), 2) if results else 0,
            round(sum(r["decision_score"] for r in results) / len(results), 2) if results else 0,
            round(len(approved) / len(results), 4) if results else 0,
            safety_prevented,
            duration_ms,
        ))
    conn.commit()


class RoboticsSimulator:
    """24/7 Robotics Governance Simulator."""

    def __init__(self):
        self._running = False
        self._cycle_count = 0
        self._conn = None
        self._robot_fleet: dict = {}

    def _get_conn(self):
        import psycopg
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(os.environ.get("OMNIX_DB_URL") or os.environ["DATABASE_URL"])
        return self._conn

    def run_cycle(self) -> dict:
        start = time.time()
        batch_size = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
        self._cycle_count += 1

        results = []
        for _ in range(batch_size):
            action_data = _generate_action(self._robot_fleet)
            result = _evaluate_action(action_data)
            results.append(result)

        duration_ms = int((time.time() - start) * 1000)

        try:
            conn = self._get_conn()
            for r in results:
                _persist_action(r, conn)
            _persist_cycle_metrics(self._cycle_count, results, duration_ms, conn)
        except Exception as e:
            logger.error(f"Robotics DB persist error cycle {self._cycle_count}: {e}")

        approved = sum(1 for r in results if r["decision"] == "APPROVED")
        blocked = sum(1 for r in results if r["decision"] == "BLOCKED")
        logger.info(
            f"Robotics cycle {self._cycle_count}: {batch_size} actions, "
            f"{approved} approved, {blocked} blocked, {duration_ms}ms"
        )
        return {"cycle": self._cycle_count, "evaluated": batch_size, "approved": approved}

    async def run_forever(self):
        self._running = True
        logger.info("RoboticsSimulator started — 24/7 mode")
        while self._running:
            try:
                self.run_cycle()
            except Exception as e:
                logger.error(f"Robotics cycle error: {e}")
            await asyncio.sleep(CYCLE_INTERVAL)

    def stop(self):
        self._running = False
        if self._conn and not self._conn.closed:
            self._conn.close()


_simulator_instance: Optional[RoboticsSimulator] = None


def get_simulator() -> RoboticsSimulator:
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = RoboticsSimulator()
    return _simulator_instance


def start_background_simulator():
    import threading
    import psycopg

    try:
        conn = psycopg.connect(os.environ.get("OMNIX_DB_URL") or os.environ["DATABASE_URL"])
        _ensure_robotics_tables(conn)
        conn.close()
    except Exception as e:
        logger.warning(f"RoboticsSimulator: could not pre-create tables: {e}")

    def _thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sim = get_simulator()
        loop.run_until_complete(sim.run_forever())

    t = threading.Thread(target=_thread_target, daemon=True, name="RoboticsSimulator")
    t.start()
    logger.info("RoboticsSimulator background thread started")
    return t
