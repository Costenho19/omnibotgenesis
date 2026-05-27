"""
OMNIX Medical AI Governance Simulator
ADR-MED-001: Medical AI Governance Vertical

Runs 24/7 generating realistic clinical AI decisions and evaluating them
through the OMNIX 11-checkpoint governance pipeline. Stores results in
PostgreSQL with PQC-signed receipts — identical to trading, credit,
insurance, and robotics engine flows.

Cycle interval: 240 seconds (4 minutes)
Each cycle: 4-10 clinical AI decisions

Simulation calibrated to real medical AI deployment patterns:
  - Rehabilitation Wearables: 35% of decisions
  - Diagnostic AI:            25%
  - Remote Monitoring:        20%
  - Clinical Decision Support:12%
  - Surgical Clearance:        8%
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

logger = logging.getLogger("OMNIX.Medical.Simulator")

CYCLE_INTERVAL = 240.0
BATCH_SIZE_MIN = 4
BATCH_SIZE_MAX = 10

DECISION_TYPES = [
    ("rehabilitation_guidance", 0.35),
    ("diagnostic_alert", 0.25),
    ("monitoring_alert", 0.20),
    ("therapeutic_recommendation", 0.12),
    ("surgical_clearance", 0.08),
]

DEVICE_TYPES_BY_DECISION: dict[str, list] = {
    "rehabilitation_guidance": [("Wearable", 0.75), ("Clinical_AI", 0.25)],
    "diagnostic_alert": [("Clinical_AI", 0.60), ("Monitoring_System", 0.40)],
    "monitoring_alert": [("Monitoring_System", 0.65), ("Wearable", 0.35)],
    "therapeutic_recommendation": [("Clinical_AI", 0.80), ("Monitoring_System", 0.20)],
    "surgical_clearance": [("Clinical_AI", 0.70), ("Surgical_Robot", 0.30)],
}

PATIENT_PROFILES = [
    ("rehabilitation", 0.30),
    ("chronic_condition", 0.25),
    ("post_surgery", 0.20),
    ("acute_care", 0.12),
    ("preventive", 0.08),
    ("geriatric", 0.05),
]

JURISDICTIONS = [
    ("UAE", 0.35),
    ("EU", 0.30),
    ("USA", 0.25),
    ("UK", 0.10),
]

# Base risk by patient profile
PROFILE_RISK_BASE: dict[str, tuple] = {
    "rehabilitation": (20, 55),
    "chronic_condition": (35, 70),
    "post_surgery": (45, 80),
    "acute_care": (50, 85),
    "preventive": (5, 30),
    "geriatric": (40, 75),
    "pediatric": (30, 65),
}


def _weighted_choice(choices: list[tuple]) -> str:
    items = [c[0] for c in choices]
    weights = [c[1] for c in choices]
    return random.choices(items, weights=weights, k=1)[0]


def _create_medical_decisions_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS medical_decisions (
                decision_id VARCHAR(60) PRIMARY KEY,
                device_id VARCHAR(60) NOT NULL,
                device_type VARCHAR(50) NOT NULL,
                decision_type VARCHAR(60) NOT NULL,
                patient_profile VARCHAR(50) NOT NULL,
                jurisdiction VARCHAR(10) NOT NULL,
                sensor_confidence FLOAT NOT NULL,
                diagnostic_confidence FLOAT NOT NULL,
                patient_risk_score FLOAT NOT NULL,
                contraindication_score FLOAT NOT NULL,
                evidence_completeness FLOAT NOT NULL,
                care_plan_alignment FLOAT NOT NULL,
                recovery_trend FLOAT NOT NULL,
                comorbidity_index FLOAT NOT NULL,
                ethics_flag BOOLEAN DEFAULT FALSE,
                consent_verified BOOLEAN DEFAULT TRUE,
                off_label_use BOOLEAN DEFAULT FALSE,
                days_since_calibration INTEGER DEFAULT 1,
                prior_adverse_events INTEGER DEFAULT 0,
                decision VARCHAR(10) NOT NULL,
                decision_score FLOAT NOT NULL,
                block_reason VARCHAR(300),
                receipt_id VARCHAR(120) NOT NULL,
                probability_score FLOAT NOT NULL,
                risk_exposure FLOAT NOT NULL,
                signal_coherence FLOAT NOT NULL,
                trend_persistence FLOAT NOT NULL,
                stress_resilience FLOAT NOT NULL,
                logic_consistency FLOAT NOT NULL,
                trajectory_score FLOAT NOT NULL DEFAULT 0,
                checkpoint_results JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS medical_cycle_metrics (
                cycle_id VARCHAR(60) PRIMARY KEY,
                cycle_number INTEGER NOT NULL,
                decisions_evaluated INTEGER NOT NULL,
                decisions_approved INTEGER NOT NULL,
                decisions_blocked INTEGER NOT NULL,
                avg_diagnostic_confidence FLOAT,
                avg_patient_risk FLOAT,
                avg_decision_score FLOAT,
                approval_rate FLOAT,
                cycle_duration_ms INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_medical_decisions_created
            ON medical_decisions(created_at DESC)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_medical_decisions_type
            ON medical_decisions(decision_type)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_medical_decisions_jurisdiction
            ON medical_decisions(jurisdiction)
        """)
    conn.commit()
    logger.info("medical_decisions + medical_cycle_metrics tables ready")


def _generate_decision() -> dict:
    """Generate a realistic clinical AI decision with correlated parameters."""
    decision_type = _weighted_choice(DECISION_TYPES)
    device_options = DEVICE_TYPES_BY_DECISION.get(decision_type, [("Clinical_AI", 1.0)])
    device_type = _weighted_choice(device_options)
    patient_profile = _weighted_choice(PATIENT_PROFILES)
    jurisdiction = _weighted_choice(JURISDICTIONS)

    risk_range = PROFILE_RISK_BASE.get(patient_profile, (25, 65))

    # Sensor confidence — wearables slightly noisier
    base_sensor = 82 if device_type == "Wearable" else 88
    sensor_confidence = max(20.0, min(100.0, random.gauss(base_sensor, 12)))

    # Diagnostic confidence — varies by decision type
    diag_base = {
        "rehabilitation_guidance": 78,
        "diagnostic_alert": 85,
        "monitoring_alert": 80,
        "therapeutic_recommendation": 82,
        "surgical_clearance": 88,
    }.get(decision_type, 80)
    diagnostic_confidence = max(20.0, min(100.0, random.gauss(diag_base, 10)))

    # Patient risk — correlated with profile
    patient_risk_score = max(0.0, min(100.0, random.uniform(*risk_range)))

    # Contraindication — mostly low, occasionally high
    contra_profile = random.choices(["none", "mild", "moderate", "severe"],
                                     weights=[0.50, 0.28, 0.15, 0.07])[0]
    contra_map = {
        "none": random.uniform(0, 15),
        "mild": random.uniform(15, 40),
        "moderate": random.uniform(40, 70),
        "severe": random.uniform(70, 100),
    }
    contraindication_score = contra_map[contra_profile]

    # Evidence completeness — most systems provide good data
    evidence_completeness = max(20.0, min(100.0, random.gauss(80, 13)))

    # Care plan alignment — usually high except for edge cases
    care_plan_alignment = max(20.0, min(100.0, random.gauss(82, 12)))

    # Recovery trend — positive for rehab, mixed for acute
    recovery_base = {
        "rehabilitation": 68,
        "chronic_condition": 58,
        "post_surgery": 62,
        "acute_care": 50,
        "preventive": 85,
        "geriatric": 55,
    }.get(patient_profile, 65)
    recovery_trend = max(5.0, min(100.0, random.gauss(recovery_base, 15)))

    # Comorbidity index
    comorbidity_base = {
        "rehabilitation": 30,
        "chronic_condition": 55,
        "post_surgery": 40,
        "acute_care": 45,
        "preventive": 10,
        "geriatric": 60,
    }.get(patient_profile, 35)
    comorbidity_index = max(0.0, min(100.0, random.gauss(comorbidity_base, 15)))

    # Ethics & compliance flags — rare
    ethics_flag = random.random() < 0.03
    consent_verified = random.random() > 0.04
    off_label_use = random.random() < 0.06

    days_since_calibration = random.choices([1, 2, 3, 7, 14, 30],
                                             weights=[0.55, 0.20, 0.10, 0.08, 0.05, 0.02])[0]
    prior_adverse_events = random.choices([0, 1, 2, 3],
                                           weights=[0.72, 0.18, 0.07, 0.03])[0]

    device_id = f"DEV-{device_type[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"

    return {
        "decision_id": f"MED-{uuid.uuid4().hex[:12].upper()}",
        "device_id": device_id,
        "device_type": device_type,
        "decision_type": decision_type,
        "patient_profile": patient_profile,
        "jurisdiction": jurisdiction,
        "sensor_confidence": round(sensor_confidence, 2),
        "diagnostic_confidence": round(diagnostic_confidence, 2),
        "patient_risk_score": round(patient_risk_score, 2),
        "contraindication_score": round(contraindication_score, 2),
        "evidence_completeness": round(evidence_completeness, 2),
        "care_plan_alignment": round(care_plan_alignment, 2),
        "recovery_trend": round(recovery_trend, 2),
        "comorbidity_index": round(comorbidity_index, 2),
        "ethics_flag": ethics_flag,
        "consent_verified": consent_verified,
        "off_label_use": off_label_use,
        "days_since_calibration": days_since_calibration,
        "prior_adverse_events": prior_adverse_events,
    }


def _evaluate_decision(decision_data: dict) -> dict:
    """Run clinical AI decision through OMNIX governance pipeline."""
    from omnix_core.medical.medical_signal_adapter import (
        MedicalDecisionInput, MedicalSignalAdapter
    )

    adapter = MedicalSignalAdapter()
    decision_input = MedicalDecisionInput(
        device_type=decision_data["device_type"],
        decision_type=decision_data["decision_type"],
        patient_profile=decision_data["patient_profile"],
        jurisdiction=decision_data["jurisdiction"],
        sensor_confidence=decision_data["sensor_confidence"],
        diagnostic_confidence=decision_data["diagnostic_confidence"],
        patient_risk_score=decision_data["patient_risk_score"],
        contraindication_score=decision_data["contraindication_score"],
        evidence_completeness=decision_data["evidence_completeness"],
        care_plan_alignment=decision_data["care_plan_alignment"],
        recovery_trend=decision_data["recovery_trend"],
        comorbidity_index=decision_data["comorbidity_index"],
        ethics_flag=decision_data["ethics_flag"],
        consent_verified=decision_data["consent_verified"],
        off_label_use=decision_data["off_label_use"],
        days_since_calibration=decision_data["days_since_calibration"],
        prior_adverse_events=decision_data["prior_adverse_events"],
    )

    signals = adapter.adapt(decision_input)
    signal_dict = signals.to_omnix_dict()

    # ── Hard blocks — domain-mandatory, bypass engine (ADR-113) ─────────────
    hard_block_reasons = []
    if decision_data["ethics_flag"]:
        hard_block_reasons.append("CP-7: Ethics flag raised — clinical review required")
    if not decision_data["consent_verified"]:
        hard_block_reasons.append("CP-7: Informed consent not verified — BLOCK")

    if hard_block_reasons:
        _composite = (
            signal_dict["probability_score"] + (100 - signal_dict["risk_exposure"])
            + signal_dict["signal_coherence"] + signal_dict["trend_persistence"]
            + signal_dict["stress_resilience"] + signal_dict["logic_consistency"]
        ) / 6.0
        return {
            **decision_data,
            **signal_dict,
            "domain": "medical_ai",
            "decision": "BLOCKED",
            "decision_score": round(_composite * 0.15, 2),
            "block_reason": " | ".join(hard_block_reasons[:2]),
            "receipt_id": DecisionReceiptEngine.build_receipt_id("medical_ai"),
            "trajectory_score": round(
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
            asset=f"{decision_data['device_type']}_{decision_data['decision_type']}",
            domain="medical_ai",
            metadata={
                "patient_profile": decision_data["patient_profile"],
                "jurisdiction":    decision_data["jurisdiction"],
                "device_type":     decision_data["device_type"],
                "off_label_use":   decision_data["off_label_use"],
            },
            compliance_config={
                "cag_liquidity_score": 100.0,
            },
        )
        decision_outcome   = result.get("decision", "BLOCKED")
        receipt_id         = DecisionReceiptEngine.build_receipt_id("medical_ai")
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
        logger.warning(f"[Medical] Governance engine unavailable: {exc} — rule-based fallback active")
        composite = (
            signal_dict["probability_score"] + (100 - signal_dict["risk_exposure"])
            + signal_dict["signal_coherence"] + signal_dict["trend_persistence"]
            + signal_dict["stress_resilience"] + signal_dict["logic_consistency"]
        ) / 6.0
        decision_outcome = "APPROVED" if composite >= 65 else ("HOLD" if composite >= 50 else "BLOCKED")
        receipt_id         = DecisionReceiptEngine.build_receipt_id("medical_ai")
        checkpoint_results = []
        trajectory_score   = (
            signal_dict["trend_persistence"] * 0.40
            + signal_dict["stress_resilience"] * 0.35
            + signal_dict["signal_coherence"] * 0.25
        )
        decision_score = composite
        block_reason = (
            "CP-2: Clinical probability below governance threshold"
            if signal_dict["probability_score"] < 65 else
            "CP-3: Patient risk exposure exceeds safe limit"
            if signal_dict["risk_exposure"] > 72 else None
        )

    return {
        **decision_data,
        **signal_dict,
        "domain":            "medical_ai",
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
            INSERT INTO medical_decisions (
                decision_id, device_id, device_type, decision_type,
                patient_profile, jurisdiction,
                sensor_confidence, diagnostic_confidence,
                patient_risk_score, contraindication_score,
                evidence_completeness, care_plan_alignment,
                recovery_trend, comorbidity_index,
                ethics_flag, consent_verified, off_label_use,
                days_since_calibration, prior_adverse_events,
                decision, decision_score, block_reason, receipt_id,
                probability_score, risk_exposure, signal_coherence,
                trend_persistence, stress_resilience, logic_consistency,
                trajectory_score, checkpoint_results
            ) VALUES (
                %(decision_id)s, %(device_id)s, %(device_type)s, %(decision_type)s,
                %(patient_profile)s, %(jurisdiction)s,
                %(sensor_confidence)s, %(diagnostic_confidence)s,
                %(patient_risk_score)s, %(contraindication_score)s,
                %(evidence_completeness)s, %(care_plan_alignment)s,
                %(recovery_trend)s, %(comorbidity_index)s,
                %(ethics_flag)s, %(consent_verified)s, %(off_label_use)s,
                %(days_since_calibration)s, %(prior_adverse_events)s,
                %(decision)s, %(decision_score)s, %(block_reason)s, %(receipt_id)s,
                %(probability_score)s, %(risk_exposure)s, %(signal_coherence)s,
                %(trend_persistence)s, %(stress_resilience)s, %(logic_consistency)s,
                %(trajectory_score)s, %(checkpoint_results_json)s::jsonb
            ) ON CONFLICT (decision_id) DO NOTHING
        """, {**result, "checkpoint_results_json": json.dumps(result.get("checkpoint_results", []))})
    conn.commit()


def _persist_cycle_metrics(cycle_num: int, results: list[dict], duration_ms: int, conn) -> None:
    approved = [r for r in results if r["decision"] == "APPROVED"]
    blocked = [r for r in results if r["decision"] == "BLOCKED"]
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO medical_cycle_metrics (
                cycle_id, cycle_number, decisions_evaluated,
                decisions_approved, decisions_blocked,
                avg_diagnostic_confidence, avg_patient_risk,
                avg_decision_score, approval_rate, cycle_duration_ms
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            f"MED-CYCLE-{uuid.uuid4().hex[:8].upper()}",
            cycle_num,
            len(results),
            len(approved),
            len(blocked),
            round(sum(r["diagnostic_confidence"] for r in results) / len(results), 2) if results else 0,
            round(sum(r["patient_risk_score"] for r in results) / len(results), 2) if results else 0,
            round(sum(r["decision_score"] for r in results) / len(results), 2) if results else 0,
            round(len(approved) / len(results), 4) if results else 0,
            duration_ms,
        ))
    conn.commit()


class MedicalSimulator:
    """24/7 Medical AI Governance Simulator — mirrors insurance and robotics engines."""

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
        _create_medical_decisions_table(conn)

    def _run_cycle(self) -> list[dict]:
        self._cycle_count += 1
        batch_size = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
        logger.info(f"[Medical Cycle {self._cycle_count}] Generating {batch_size} clinical AI decisions")

        t0 = time.monotonic()
        decisions = [_generate_decision() for _ in range(batch_size)]
        results = [_evaluate_decision(d) for d in decisions]

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
        blocked = sum(1 for r in results if r["decision"] == "BLOCKED")
        logger.info(
            f"[Medical Cycle {self._cycle_count}] "
            f"APPROVED={approved} BLOCKED={blocked} in {duration_ms}ms"
        )
        return results

    async def run_forever(self):
        self._running = True
        self._ensure_tables()
        logger.info("OMNIX Medical AI Governance Simulator started")
        while self._running:
            try:
                self._run_cycle()
            except Exception as e:
                logger.error(f"Cycle error: {e}")
            await asyncio.sleep(CYCLE_INTERVAL)

    def stop(self):
        self._running = False
        logger.info("Medical simulator stopping")


_simulator_instance: Optional[MedicalSimulator] = None
_simulator_thread = None


def start_background_simulator() -> None:
    """Start Medical AI simulator in a background thread with its own event loop."""
    import threading
    global _simulator_instance, _simulator_thread

    if _simulator_instance is not None:
        return

    _simulator_instance = MedicalSimulator()

    def _thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_simulator_instance.run_forever())
        except Exception as e:
            logger.error(f"[MedicalSim] Background thread error: {e}", exc_info=True)
        finally:
            loop.close()

    _simulator_thread = threading.Thread(
        target=_thread_target, daemon=True, name="MedicalAISimulator"
    )
    _simulator_thread.start()
    logger.info("Medical AI background simulator thread started")
