"""
OMNIX Insurance Governance Simulator
ADR-054: Insurance Governance Vertical

Runs 24/7 generating realistic global insurance claims and evaluating them
through the OMNIX 11-checkpoint governance pipeline. Stores results in
PostgreSQL with PQC-signed receipts — identical to trading and credit engine flows.

Cycle interval: 240 seconds (4 minutes) — realistic claims processing cadence.
Each cycle processes a batch of 4-10 claims.

Simulation calibrated to global commercial insurance market:
  - Auto: 25% of claims, avg $18K
  - Property: 30%, avg $85K
  - Health: 20%, avg $12K
  - Liability: 12%, avg $250K
  - Cyber: 8%, avg $420K
  - Life: 5%, avg $380K
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

logger = logging.getLogger("OMNIX.Insurance.Simulator")

CYCLE_INTERVAL = 300.0       # 5 minutes between cycles
BATCH_SIZE_MIN = 4
BATCH_SIZE_MAX = 10

INSURANCE_TYPES = [
    ("Property", 0.30),
    ("Auto", 0.25),
    ("Health", 0.20),
    ("Liability", 0.12),
    ("Cyber", 0.08),
    ("Life", 0.05),
]

CLAIMANT_TYPES = [
    ("Individual", 0.55),
    ("SME", 0.28),
    ("Corporate", 0.12),
    ("Institutional", 0.05),
]

REGIONS = [
    ("NA", 0.35),
    ("EU", 0.30),
    ("APAC", 0.20),
    ("MEA", 0.10),
    ("LATAM", 0.05),
]

# (insurance_type, claimant_type) → (min_usd, max_usd)
CLAIM_RANGES: dict[tuple, tuple] = {
    ("Auto", "Individual"): (3_000, 45_000),
    ("Auto", "SME"): (8_000, 120_000),
    ("Auto", "Corporate"): (25_000, 500_000),
    ("Property", "Individual"): (10_000, 350_000),
    ("Property", "SME"): (50_000, 2_000_000),
    ("Property", "Corporate"): (200_000, 15_000_000),
    ("Property", "Institutional"): (1_000_000, 50_000_000),
    ("Health", "Individual"): (1_000, 80_000),
    ("Health", "SME"): (5_000, 250_000),
    ("Liability", "SME"): (25_000, 800_000),
    ("Liability", "Corporate"): (100_000, 5_000_000),
    ("Liability", "Institutional"): (500_000, 20_000_000),
    ("Cyber", "SME"): (50_000, 2_500_000),
    ("Cyber", "Corporate"): (200_000, 10_000_000),
    ("Cyber", "Institutional"): (1_000_000, 50_000_000),
    ("Life", "Individual"): (100_000, 2_000_000),
}

_DEFAULT_RANGE = (10_000, 500_000)


def _ensure_insurance_tables(conn) -> None:
    """Create insurance tables if they don't exist — idempotent, safe for Railway fresh deploys."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS insurance_claims (
                id SERIAL PRIMARY KEY,
                claim_id VARCHAR(64) UNIQUE NOT NULL,
                claimant_type VARCHAR(32),
                insurance_type VARCHAR(32),
                region VARCHAR(16),
                claim_amount_usd NUMERIC(18,2),
                policy_limit_usd NUMERIC(18,2),
                coverage_ratio NUMERIC(6,4),
                claimant_history_score NUMERIC(6,2),
                fraud_indicators NUMERIC(6,2),
                evidence_completeness NUMERIC(6,2),
                loss_ratio_trend NUMERIC(6,2),
                reserve_adequacy NUMERIC(6,2),
                policy_claim_alignment NUMERIC(6,2),
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
            CREATE TABLE IF NOT EXISTS insurance_cycle_metrics (
                id SERIAL PRIMARY KEY,
                cycle_id VARCHAR(64) UNIQUE NOT NULL,
                cycle_number INTEGER,
                claims_evaluated INTEGER,
                claims_approved INTEGER,
                claims_blocked INTEGER,
                total_approved_usd NUMERIC(18,2),
                total_blocked_usd NUMERIC(18,2),
                avg_fraud_score NUMERIC(6,2),
                avg_decision_score NUMERIC(6,2),
                approval_rate NUMERIC(6,4),
                cycle_duration_ms INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_insurance_claims_decision
            ON insurance_claims (decision)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_insurance_claims_type
            ON insurance_claims (insurance_type)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_insurance_claims_created
            ON insurance_claims (created_at DESC)
        """)
    conn.commit()
    logger.info("insurance_claims + insurance_cycle_metrics tables ready")


def _weighted_choice(choices: list[tuple]) -> str:
    items = [c[0] for c in choices]
    weights = [c[1] for c in choices]
    return random.choices(items, weights=weights, k=1)[0]


def _generate_claim() -> dict:
    """Generate a realistic insurance claim with correlated parameters."""
    insurance_type = _weighted_choice(INSURANCE_TYPES)
    claimant_type = _weighted_choice(CLAIMANT_TYPES)
    region = _weighted_choice(REGIONS)

    rng = CLAIM_RANGES.get((insurance_type, claimant_type), _DEFAULT_RANGE)
    claim_amount = round(random.uniform(*rng), 2)

    # Policy limit always ≥ claim amount, usually 20-300% larger
    limit_factor = random.uniform(1.1, 3.5)
    policy_limit = round(claim_amount * limit_factor, 2)

    # Claimant history: most clients have good history
    history_profile = random.choices(
        ["excellent", "good", "average", "poor"],
        weights=[0.40, 0.35, 0.18, 0.07]
    )[0]
    history_map = {
        "excellent": random.uniform(85, 100),
        "good": random.uniform(65, 85),
        "average": random.uniform(40, 65),
        "poor": random.uniform(10, 40),
    }
    claimant_history_score = history_map[history_profile]

    # Fraud indicators — correlated with claim amount and type
    base_fraud = {
        "Auto": 18, "Property": 22, "Health": 28,
        "Liability": 15, "Cyber": 12, "Life": 8
    }.get(insurance_type, 15)

    # Large claims attract more scrutiny
    size_fraud_adj = min(20.0, (claim_amount / rng[1]) * 20.0)
    fraud_indicators = max(0.0, min(100.0,
        random.gauss(base_fraud + size_fraud_adj, 10)
    ))

    # Evidence completeness — most claimants provide good docs
    evidence_completeness = max(20.0, min(100.0,
        random.gauss(78, 14)
    ))

    # Loss ratio trend by region
    region_lr_base = {"NA": 68, "EU": 72, "APAC": 70, "MEA": 75, "LATAM": 80}.get(region, 70)
    loss_ratio_trend = max(10.0, min(100.0,
        random.gauss(100 - region_lr_base + 20, 12)
    ))

    # Reserve adequacy
    reserve_adequacy = max(20.0, min(100.0, random.gauss(72, 15)))

    # Policy-claim alignment
    policy_claim_alignment = max(20.0, min(100.0, random.gauss(80, 14)))

    # CAT events: ~5% of property claims
    is_catastrophe = insurance_type == "Property" and random.random() < 0.05
    if is_catastrophe:
        claim_amount *= random.uniform(1.5, 3.0)
        claim_amount = min(claim_amount, policy_limit)

    incident_days_ago = random.randint(1, 180)
    prior_claims_count = random.choices([0, 1, 2, 3, 4], weights=[0.50, 0.28, 0.13, 0.06, 0.03])[0]

    return {
        "claim_id": f"CLM-{uuid.uuid4().hex[:12].upper()}",
        "claimant_type": claimant_type,
        "insurance_type": insurance_type,
        "region": region,
        "claim_amount_usd": round(claim_amount, 2),
        "policy_limit_usd": round(policy_limit, 2),
        "coverage_ratio": round(min(claim_amount / max(policy_limit, 1), 1.0), 4),
        "claimant_history_score": round(claimant_history_score, 2),
        "fraud_indicators": round(fraud_indicators, 2),
        "evidence_completeness": round(evidence_completeness, 2),
        "loss_ratio_trend": round(loss_ratio_trend, 2),
        "reserve_adequacy": round(reserve_adequacy, 2),
        "policy_claim_alignment": round(policy_claim_alignment, 2),
        "incident_days_ago": incident_days_ago,
        "prior_claims_count": prior_claims_count,
        "is_catastrophe_event": is_catastrophe,
    }


def _evaluate_claim(claim_data: dict) -> dict:
    """Run claim through OMNIX governance pipeline."""
    from omnix_core.insurance.insurance_signal_adapter import (
        InsuranceClaimInput, InsuranceSignalAdapter
    )

    adapter = InsuranceSignalAdapter()
    claim_input = InsuranceClaimInput(
        claimant_type=claim_data["claimant_type"],
        insurance_type=claim_data["insurance_type"],
        region=claim_data["region"],
        claim_amount_usd=claim_data["claim_amount_usd"],
        policy_limit_usd=claim_data["policy_limit_usd"],
        claimant_history_score=claim_data["claimant_history_score"],
        fraud_indicators=claim_data["fraud_indicators"],
        evidence_completeness=claim_data["evidence_completeness"],
        loss_ratio_trend=claim_data["loss_ratio_trend"],
        reserve_adequacy=claim_data["reserve_adequacy"],
        policy_claim_alignment=claim_data["policy_claim_alignment"],
        incident_days_ago=claim_data["incident_days_ago"],
        prior_claims_count=claim_data["prior_claims_count"],
        is_catastrophe_event=claim_data["is_catastrophe_event"],
    )

    signals = adapter.adapt(claim_input)
    signals_dict = signals.to_omnix_dict()

    # Import governance engine
    try:
        from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
        engine = GovernanceEvaluationEngine()
        result = engine.evaluate(
            signals=signals_dict,
            asset=claim_data["insurance_type"],
            domain="insurance",
            metadata={"claimant_type": claim_data["claimant_type"]},
            compliance_config={
                "cag_liquidity_score": 80.0,
            },
        )
        decision = result.get("decision", "BLOCKED")
        receipt_id = DecisionReceiptEngine.build_receipt_id("insurance")
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
        # Rule-based fallback
        composite = (signals.probability_score + (100 - signals.risk_exposure) +
                     signals.signal_coherence + signals.trend_persistence +
                     signals.stress_resilience + signals.logic_consistency) / 6.0
        if composite >= 62:
            decision = "APPROVED"
        elif composite >= 45:
            decision = "HOLD"
        else:
            decision = "BLOCKED"
        receipt_id = DecisionReceiptEngine.build_receipt_id("insurance")
        checkpoint_results = []
        trajectory_score = composite
        decision_score = composite
        block_reason = "High fraud indicators" if signals.risk_exposure > 70 else None

    return {
        **claim_data,
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


def _persist_claim(result: dict, conn) -> None:
    """Persist evaluated claim to PostgreSQL."""
    import json
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO insurance_claims (
                claim_id, claimant_type, insurance_type, region,
                claim_amount_usd, policy_limit_usd, coverage_ratio,
                claimant_history_score, fraud_indicators, evidence_completeness,
                loss_ratio_trend, reserve_adequacy, policy_claim_alignment,
                decision, decision_score, block_reason, receipt_id,
                probability_score, risk_exposure, signal_coherence,
                trend_persistence, stress_resilience, logic_consistency,
                checkpoint_results, trajectory_score
            ) VALUES (
                %(claim_id)s, %(claimant_type)s, %(insurance_type)s, %(region)s,
                %(claim_amount_usd)s, %(policy_limit_usd)s, %(coverage_ratio)s,
                %(claimant_history_score)s, %(fraud_indicators)s, %(evidence_completeness)s,
                %(loss_ratio_trend)s, %(reserve_adequacy)s, %(policy_claim_alignment)s,
                %(decision)s, %(decision_score)s, %(block_reason)s, %(receipt_id)s,
                %(probability_score)s, %(risk_exposure)s, %(signal_coherence)s,
                %(trend_persistence)s, %(stress_resilience)s, %(logic_consistency)s,
                %(checkpoint_results_json)s::jsonb, %(trajectory_score)s
            ) ON CONFLICT (claim_id) DO NOTHING
        """, {**result, "checkpoint_results_json": json.dumps(result.get("checkpoint_results", []))})
    conn.commit()


def _persist_cycle_metrics(cycle_num: int, results: list[dict], duration_ms: int, conn) -> None:
    """Persist cycle-level aggregates."""
    approved = [r for r in results if r["decision"] == "APPROVED"]
    blocked = [r for r in results if r["decision"] == "BLOCKED"]

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO insurance_cycle_metrics (
                cycle_id, cycle_number, claims_evaluated, claims_approved, claims_blocked,
                total_approved_usd, total_blocked_usd, avg_fraud_score,
                avg_decision_score, approval_rate, cycle_duration_ms
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            f"INS-CYCLE-{uuid.uuid4().hex[:8].upper()}",
            cycle_num,
            len(results),
            len(approved),
            len(blocked),
            round(sum(r["claim_amount_usd"] for r in approved), 2),
            round(sum(r["claim_amount_usd"] for r in blocked), 2),
            round(sum(r["fraud_indicators"] for r in results) / len(results), 2) if results else 0,
            round(sum(r["decision_score"] for r in results) / len(results), 2) if results else 0,
            round(len(approved) / len(results), 4) if results else 0,
            duration_ms,
        ))
    conn.commit()


class InsuranceSimulator:
    """24/7 Insurance Governance Simulator — mirrors credit and trading engines."""

    def __init__(self):
        self._running = False
        self._cycle_count = 0
        self._conn = None

    def _get_conn(self):
        import psycopg
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(os.environ.get("OMNIX_DB_URL") or os.environ["DATABASE_URL"])
        return self._conn

    def run_cycle(self) -> dict:
        """Execute one evaluation cycle."""
        start = time.time()
        batch_size = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
        self._cycle_count += 1

        results = []
        for _ in range(batch_size):
            claim_data = _generate_claim()
            result = _evaluate_claim(claim_data)
            results.append(result)

        duration_ms = int((time.time() - start) * 1000)

        try:
            conn = self._get_conn()
            for r in results:
                _persist_claim(r, conn)
            _persist_cycle_metrics(self._cycle_count, results, duration_ms, conn)
        except Exception as e:
            logger.error(f"Insurance DB persist error cycle {self._cycle_count}: {e}")

        approved = sum(1 for r in results if r["decision"] == "APPROVED")
        logger.info(
            f"Insurance cycle {self._cycle_count}: {batch_size} claims, "
            f"{approved} approved, {batch_size - approved} blocked/held, "
            f"{duration_ms}ms"
        )
        return {"cycle": self._cycle_count, "evaluated": batch_size, "approved": approved}

    async def run_forever(self):
        """Async loop — runs indefinitely every CYCLE_INTERVAL seconds."""
        self._running = True
        logger.info("InsuranceSimulator started — 24/7 mode")
        while self._running:
            try:
                self.run_cycle()
            except Exception as e:
                logger.error(f"Insurance cycle error: {e}")
            await asyncio.sleep(CYCLE_INTERVAL)

    def stop(self):
        self._running = False
        if self._conn and not self._conn.closed:
            self._conn.close()


_simulator_instance: Optional[InsuranceSimulator] = None


def get_simulator() -> InsuranceSimulator:
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = InsuranceSimulator()
    return _simulator_instance


def start_background_simulator():
    """Start the simulator in a background thread — called from app.py startup."""
    import threading
    import psycopg

    try:
        conn = psycopg.connect(os.environ.get("OMNIX_DB_URL") or os.environ["DATABASE_URL"])
        _ensure_insurance_tables(conn)
        conn.close()
    except Exception as e:
        logger.warning(f"InsuranceSimulator: could not pre-create tables: {e}")

    def _thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sim = get_simulator()
        loop.run_until_complete(sim.run_forever())

    t = threading.Thread(target=_thread_target, daemon=True, name="InsuranceSimulator")
    t.start()
    logger.info("InsuranceSimulator background thread started")
    return t
