"""
OMNIX Autonomous Agent Governance Simulator
ADR-AGT-001: Autonomous Agent Governance Vertical

Runs 24/7 generating realistic autonomous agent decisions and evaluating them
through the OMNIX 11-checkpoint governance pipeline. Stores results in
PostgreSQL with PQC-signed receipts — identical to trading, credit,
insurance, robotics, and medical AI engine flows.

Cycle interval: 200 seconds (~3.3 minutes)
Each cycle: 3-8 agent decisions

Simulation calibrated to real autonomous agent deployment patterns:
  - Task Delegation:       35% of decisions
  - Data Access:           20%
  - External API Call:     18%
  - Resource Allocation:   15%
  - State Modification:    12%
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

logger = logging.getLogger("OMNIX.Agents.Simulator")

CYCLE_INTERVAL = 200.0
BATCH_SIZE_MIN = 3
BATCH_SIZE_MAX = 8

DECISION_TYPES = [
    ("task_delegation", 0.35),
    ("data_access", 0.20),
    ("external_api_call", 0.18),
    ("resource_allocation", 0.15),
    ("state_modification", 0.12),
]

AGENT_TYPES = [
    ("Financial_Agent", 0.30),
    ("Enterprise_Agent", 0.25),
    ("Logistics_Agent", 0.20),
    ("Infrastructure_Agent", 0.15),
    ("Research_Agent", 0.10),
]

ENVIRONMENTS = [
    ("production", 0.40),
    ("staging", 0.30),
    ("development", 0.20),
    ("sandbox", 0.10),
]

REVERSIBILITIES = [
    ("fully_reversible", 0.40),
    ("partially_reversible", 0.30),
    ("irreversible", 0.20),
    ("unknown", 0.10),
]

DATA_SENSITIVITIES = [
    ("low", 0.45),
    ("medium", 0.30),
    ("high", 0.15),
    ("pii", 0.07),
    ("phi", 0.03),
]

# Complexity base by decision type
COMPLEXITY_BASE: dict[str, tuple] = {
    "task_delegation": (20, 65),
    "data_access": (15, 55),
    "external_api_call": (25, 70),
    "resource_allocation": (30, 75),
    "state_modification": (35, 80),
}


def _weighted_choice(choices: list[tuple]) -> str:
    items = [c[0] for c in choices]
    weights = [c[1] for c in choices]
    return random.choices(items, weights=weights, k=1)[0]


def _create_agent_decisions_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_decisions (
                decision_id VARCHAR(60) PRIMARY KEY,
                agent_id VARCHAR(60) NOT NULL,
                agent_type VARCHAR(50) NOT NULL,
                decision_type VARCHAR(60) NOT NULL,
                environment VARCHAR(30) NOT NULL,
                reversibility VARCHAR(30) NOT NULL,
                task_complexity FLOAT NOT NULL,
                resource_utilization FLOAT NOT NULL,
                context_completeness FLOAT NOT NULL,
                goal_alignment FLOAT NOT NULL,
                dependency_score FLOAT NOT NULL,
                scope_blast_radius FLOAT NOT NULL,
                fallback_coverage FLOAT NOT NULL,
                permission_scope FLOAT NOT NULL,
                safety_critical_flag BOOLEAN DEFAULT FALSE,
                human_approval_required BOOLEAN DEFAULT FALSE,
                human_approved BOOLEAN DEFAULT FALSE,
                cross_boundary BOOLEAN DEFAULT FALSE,
                data_sensitivity VARCHAR(20) DEFAULT 'low',
                retry_count INTEGER DEFAULT 0,
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
            CREATE TABLE IF NOT EXISTS agent_cycle_metrics (
                cycle_id VARCHAR(60) PRIMARY KEY,
                cycle_number INTEGER NOT NULL,
                decisions_evaluated INTEGER NOT NULL,
                decisions_approved INTEGER NOT NULL,
                decisions_blocked INTEGER NOT NULL,
                avg_task_complexity FLOAT,
                avg_scope_risk FLOAT,
                avg_decision_score FLOAT,
                approval_rate FLOAT,
                cycle_duration_ms INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_decisions_created
            ON agent_decisions(created_at DESC)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_decisions_type
            ON agent_decisions(decision_type)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_decisions_environment
            ON agent_decisions(environment)
        """)
    conn.commit()
    logger.info("agent_decisions + agent_cycle_metrics tables ready")


def _generate_decision() -> dict:
    """Generate a realistic autonomous agent decision with correlated parameters."""
    decision_type = _weighted_choice(DECISION_TYPES)
    agent_type = _weighted_choice(AGENT_TYPES)
    environment = _weighted_choice(ENVIRONMENTS)
    reversibility = _weighted_choice(REVERSIBILITIES)
    data_sensitivity = _weighted_choice(DATA_SENSITIVITIES)

    complexity_range = COMPLEXITY_BASE.get(decision_type, (25, 65))
    task_complexity = max(0.0, min(100.0, random.uniform(*complexity_range)))

    # Resource utilization — correlates with complexity and environment
    env_resource_base = {"production": 55, "staging": 45, "development": 38, "sandbox": 25}.get(environment, 45)
    resource_utilization = max(5.0, min(100.0, random.gauss(env_resource_base + task_complexity * 0.2, 15)))

    # Context completeness — most agents start with good context
    context_completeness = max(20.0, min(100.0, random.gauss(78, 14)))

    # Goal alignment — high for most planned tasks
    goal_alignment = max(20.0, min(100.0, random.gauss(80, 13)))

    # Dependency score — external APIs and services create dependencies
    dep_base = {
        "task_delegation": 35, "data_access": 45, "external_api_call": 65,
        "resource_allocation": 40, "state_modification": 30,
    }.get(decision_type, 40)
    dependency_score = max(0.0, min(100.0, random.gauss(dep_base, 18)))

    # Scope blast radius — correlated with environment and decision type
    env_blast = {"production": 55, "staging": 35, "development": 22, "sandbox": 12}.get(environment, 35)
    scope_blast_radius = max(0.0, min(100.0, random.gauss(env_blast, 18)))

    # Fallback coverage — most well-designed agents have fallbacks
    fallback_coverage = max(10.0, min(100.0, random.gauss(72, 18)))

    # Permission scope — agents should have minimal permissions
    permission_scope = max(10.0, min(100.0, random.gauss(45, 22)))

    # Safety critical — rare but critical
    safety_critical_flag = random.random() < 0.04

    # Human approval required — state modifications and high-risk tasks
    human_approval_required = (
        decision_type == "state_modification" and random.random() < 0.35
    ) or (
        reversibility == "irreversible" and random.random() < 0.25
    ) or (
        environment == "production" and random.random() < 0.10
    )

    # Human approved — most required approvals are granted
    human_approved = human_approval_required and random.random() > 0.15

    # Cross boundary — financial and infrastructure agents more likely
    cross_boundary_prob = {
        "Financial_Agent": 0.25, "Infrastructure_Agent": 0.22,
        "Enterprise_Agent": 0.15, "Logistics_Agent": 0.12, "Research_Agent": 0.08,
    }.get(agent_type, 0.12)
    cross_boundary = random.random() < cross_boundary_prob

    retry_count = random.choices([0, 1, 2, 3], weights=[0.75, 0.15, 0.07, 0.03])[0]

    agent_id = f"AGT-{agent_type[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"

    return {
        "decision_id": f"AGT-{uuid.uuid4().hex[:12].upper()}",
        "agent_id": agent_id,
        "agent_type": agent_type,
        "decision_type": decision_type,
        "environment": environment,
        "reversibility": reversibility,
        "task_complexity": round(task_complexity, 2),
        "resource_utilization": round(resource_utilization, 2),
        "context_completeness": round(context_completeness, 2),
        "goal_alignment": round(goal_alignment, 2),
        "dependency_score": round(dependency_score, 2),
        "scope_blast_radius": round(scope_blast_radius, 2),
        "fallback_coverage": round(fallback_coverage, 2),
        "permission_scope": round(permission_scope, 2),
        "safety_critical_flag": safety_critical_flag,
        "human_approval_required": human_approval_required,
        "human_approved": human_approved,
        "cross_boundary": cross_boundary,
        "data_sensitivity": data_sensitivity,
        "retry_count": retry_count,
    }


def _evaluate_decision(decision_data: dict) -> dict:
    """Run agent decision through OMNIX governance pipeline."""
    from omnix_core.agents.agents_signal_adapter import (
        AgentDecisionInput, AgentSignalAdapter
    )

    adapter = AgentSignalAdapter()
    decision_input = AgentDecisionInput(
        agent_type=decision_data["agent_type"],
        decision_type=decision_data["decision_type"],
        environment=decision_data["environment"],
        reversibility=decision_data["reversibility"],
        task_complexity=decision_data["task_complexity"],
        resource_utilization=decision_data["resource_utilization"],
        context_completeness=decision_data["context_completeness"],
        goal_alignment=decision_data["goal_alignment"],
        dependency_score=decision_data["dependency_score"],
        scope_blast_radius=decision_data["scope_blast_radius"],
        fallback_coverage=decision_data["fallback_coverage"],
        permission_scope=decision_data["permission_scope"],
        safety_critical_flag=decision_data["safety_critical_flag"],
        human_approval_required=decision_data["human_approval_required"],
        human_approved=decision_data["human_approved"],
        cross_boundary=decision_data["cross_boundary"],
        data_sensitivity=decision_data["data_sensitivity"],
        retry_count=decision_data["retry_count"],
        agent_id=decision_data["agent_id"],
    )

    signals = adapter.adapt(decision_input)
    signal_dict = signals.to_omnix_dict()

    # ── Hard blocks — principal hierarchy overrides, bypass engine (ADR-091/ADR-113) ─
    hard_block_reasons = []
    if decision_data["safety_critical_flag"]:
        hard_block_reasons.append("CP-7: Safety-critical flag raised — human review mandatory")
    if decision_data["human_approval_required"] and not decision_data["human_approved"]:
        hard_block_reasons.append("CP-7: Human authorization required but not granted — BLOCK")

    if hard_block_reasons:
        _composite = (
            signal_dict["probability_score"] + (100 - signal_dict["risk_exposure"])
            + signal_dict["signal_coherence"] + signal_dict["trend_persistence"]
            + signal_dict["stress_resilience"] + signal_dict["logic_consistency"]
        ) / 6.0
        return {
            **decision_data,
            **signal_dict,
            "domain":            "autonomous_agent",
            "decision":          "BLOCKED",
            "decision_score":    round(_composite * 0.15, 2),
            "block_reason":      " | ".join(hard_block_reasons[:2]),
            "receipt_id":        DecisionReceiptEngine.build_receipt_id("autonomous_agent"),
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
            asset=f"{decision_data['agent_type']}_{decision_data['decision_type']}",
            domain="autonomous_agent",
            metadata={
                "environment":  decision_data["environment"],
                "reversibility": decision_data["reversibility"],
                "data_sensitivity": decision_data["data_sensitivity"],
                "cross_boundary":   decision_data["cross_boundary"],
            },
            compliance_config={
                "cag_liquidity_score": 100.0,
            },
        )
        decision_outcome   = result.get("decision", "BLOCKED")
        receipt_id         = DecisionReceiptEngine.build_receipt_id("autonomous_agent")
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
        logger.warning(f"[Agents] Governance engine unavailable: {exc} — rule-based fallback active")
        composite = (
            signal_dict["probability_score"] + (100 - signal_dict["risk_exposure"])
            + signal_dict["signal_coherence"] + signal_dict["trend_persistence"]
            + signal_dict["stress_resilience"] + signal_dict["logic_consistency"]
        ) / 6.0
        decision_outcome = "APPROVED" if composite >= 62 else ("HOLD" if composite >= 48 else "BLOCKED")
        receipt_id         = DecisionReceiptEngine.build_receipt_id("autonomous_agent")
        checkpoint_results = []
        trajectory_score   = (
            signal_dict["trend_persistence"] * 0.40
            + signal_dict["stress_resilience"] * 0.35
            + signal_dict["signal_coherence"] * 0.25
        )
        decision_score = composite
        block_reason = (
            "CP-3: Action blast radius exceeds safe governance limit"
            if signal_dict["risk_exposure"] > 70 else
            "CP-2: Task viability probability below threshold"
            if signal_dict["probability_score"] < 60 else None
        )

    return {
        **decision_data,
        **signal_dict,
        "domain":            "autonomous_agent",
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
            INSERT INTO agent_decisions (
                decision_id, agent_id, agent_type, decision_type,
                environment, reversibility,
                task_complexity, resource_utilization, context_completeness,
                goal_alignment, dependency_score, scope_blast_radius,
                fallback_coverage, permission_scope,
                safety_critical_flag, human_approval_required, human_approved,
                cross_boundary, data_sensitivity, retry_count,
                decision, decision_score, block_reason, receipt_id,
                probability_score, risk_exposure, signal_coherence,
                trend_persistence, stress_resilience, logic_consistency,
                trajectory_score, checkpoint_results
            ) VALUES (
                %(decision_id)s, %(agent_id)s, %(agent_type)s, %(decision_type)s,
                %(environment)s, %(reversibility)s,
                %(task_complexity)s, %(resource_utilization)s, %(context_completeness)s,
                %(goal_alignment)s, %(dependency_score)s, %(scope_blast_radius)s,
                %(fallback_coverage)s, %(permission_scope)s,
                %(safety_critical_flag)s, %(human_approval_required)s, %(human_approved)s,
                %(cross_boundary)s, %(data_sensitivity)s, %(retry_count)s,
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
            INSERT INTO agent_cycle_metrics (
                cycle_id, cycle_number, decisions_evaluated,
                decisions_approved, decisions_blocked,
                avg_task_complexity, avg_scope_risk,
                avg_decision_score, approval_rate, cycle_duration_ms
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            f"AGT-CYCLE-{uuid.uuid4().hex[:8].upper()}",
            cycle_num,
            len(results),
            len(approved),
            len(blocked),
            round(sum(r["task_complexity"] for r in results) / len(results), 2) if results else 0,
            round(sum(r["scope_blast_radius"] for r in results) / len(results), 2) if results else 0,
            round(sum(r["decision_score"] for r in results) / len(results), 2) if results else 0,
            round(len(approved) / len(results), 4) if results else 0,
            duration_ms,
        ))
    conn.commit()


class AgentSimulator:
    """24/7 Autonomous Agent Governance Simulator — mirrors medical, insurance and robotics engines."""

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
        _create_agent_decisions_table(conn)

    def _run_cycle(self) -> list[dict]:
        self._cycle_count += 1
        batch_size = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
        logger.info(f"[Agent Cycle {self._cycle_count}] Generating {batch_size} agent decisions")

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
            f"[Agent Cycle {self._cycle_count}] "
            f"APPROVED={approved} BLOCKED={blocked} in {duration_ms}ms"
        )
        return results

    async def run_forever(self):
        self._running = True
        self._ensure_tables()
        logger.info("OMNIX Autonomous Agent Governance Simulator started")
        while self._running:
            try:
                self._run_cycle()
            except Exception as e:
                logger.error(f"Cycle error: {e}")
            await asyncio.sleep(CYCLE_INTERVAL)

    def stop(self):
        self._running = False
        logger.info("Agent simulator stopping")


_simulator_instance: Optional[AgentSimulator] = None
_simulator_thread = None


def start_background_simulator() -> None:
    """Start Autonomous Agent simulator in a background thread with its own event loop."""
    import threading
    global _simulator_instance, _simulator_thread

    if _simulator_instance is not None:
        return

    _simulator_instance = AgentSimulator()

    def _thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_simulator_instance.run_forever())
        except Exception as e:
            logger.error(f"[AgentSim] Background thread error: {e}", exc_info=True)
        finally:
            loop.close()

    _simulator_thread = threading.Thread(
        target=_thread_target, daemon=True, name="AutonomousAgentSimulator"
    )
    _simulator_thread.start()
    logger.info("Autonomous Agent background simulator thread started")
