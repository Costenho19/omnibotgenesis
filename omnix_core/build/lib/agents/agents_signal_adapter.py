"""
OMNIX Autonomous Agent Governance Signal Adapter
ADR-AGT-001: Autonomous Agent Governance Vertical

Maps autonomous agent decision parameters to OMNIX's 6 normalized governance signals (0-100).
Same domain-agnostic pipeline that governs trading, credit, insurance, robotics, and medical AI —
now adapted for AI agents executing tasks without real-time human intervention.

Signal mapping:
  probability_score   → Task viability probability (complexity, resource feasibility, success likelihood)
  risk_exposure       → Action risk index (scope, reversibility, blast radius)
  signal_coherence    → Context-task alignment (instructions, permissions, environmental state)
  trend_persistence   → Goal trajectory stability (progress, objective stability, convergence)
  stress_resilience   → Edge-case robustness (failure modes, fallback coverage, dependency resilience)
  logic_consistency   → Authorization and ethics alignment (principal hierarchy, safety constraints)

Supported decision types:
  task_delegation, data_access, external_api_call, resource_allocation, state_modification

Hard blocks (override all scores):
  safety_critical_flag=True         → Ethics/Safety BLOCK
  human_approval_required + not approved → Authorization BLOCK
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("OMNIX.Agents.SignalAdapter")

# Task complexity thresholds by decision type
COMPLEXITY_THRESHOLDS: dict[str, float] = {
    "task_delegation": 0.68,
    "data_access": 0.72,
    "external_api_call": 0.75,
    "resource_allocation": 0.78,
    "state_modification": 0.82,
}

# Risk amplifiers by environment
ENVIRONMENT_RISK_AMPLIFIERS: dict[str, float] = {
    "production": 1.45,
    "staging": 1.15,
    "development": 0.90,
    "sandbox": 0.75,
}

# Reversibility multipliers — irreversible actions require higher scores
REVERSIBILITY_FACTORS: dict[str, float] = {
    "fully_reversible": 0.80,
    "partially_reversible": 1.10,
    "irreversible": 1.45,
    "unknown": 1.30,
}

# Agent type risk profiles
AGENT_RISK_BASE: dict[str, float] = {
    "Financial_Agent": 1.30,
    "Logistics_Agent": 1.10,
    "Enterprise_Agent": 1.15,
    "Research_Agent": 0.90,
    "Infrastructure_Agent": 1.25,
    "General_Agent": 1.00,
}


@dataclass
class AgentDecisionInput:
    """Raw autonomous agent decision parameters before signal adaptation."""
    agent_type: str                     # Financial_Agent, Logistics_Agent, Enterprise_Agent, etc.
    decision_type: str                  # task_delegation, data_access, external_api_call, etc.
    environment: str                    # production, staging, development, sandbox
    reversibility: str                  # fully_reversible, partially_reversible, irreversible, unknown

    # Task parameters (0-100 unless noted)
    task_complexity: float              # Cognitive/computational complexity of the task (0-100)
    resource_utilization: float         # Resource consumption level (0-100, higher=more resources)
    context_completeness: float         # Context/instruction completeness for the task (0-100)
    goal_alignment: float               # Alignment between task and stated agent goal (0-100)
    dependency_score: float             # External dependency risk (0-100, higher=more dependencies)
    scope_blast_radius: float           # Potential scope of impact/blast radius (0-100)
    fallback_coverage: float            # Fallback path coverage for failure modes (0-100)
    permission_scope: float             # Authorization scope granted (0-100, higher=broader)

    # Safety and authorization flags
    safety_critical_flag: bool = False  # Action involves safety-critical system — hard block
    human_approval_required: bool = False  # Requires human authorization before execution
    human_approved: bool = False        # Human has approved the action
    cross_boundary: bool = False        # Action crosses trust/security boundary
    data_sensitivity: str = "low"       # low, medium, high, pii, phi — sensitivity level

    # Metadata
    retry_count: int = 0                # Number of prior retry attempts
    agent_id: str = ""                  # Agent instance identifier


@dataclass
class AgentGovernanceSignals:
    """6 normalized OMNIX governance signals for autonomous agent domain."""
    probability_score: float    # 0-100: task viability probability
    risk_exposure: float        # 0-100: action risk index (lower = safer)
    signal_coherence: float     # 0-100: context-task alignment
    trend_persistence: float    # 0-100: goal trajectory stability
    stress_resilience: float    # 0-100: edge-case robustness
    logic_consistency: float    # 0-100: authorization and ethics alignment

    complexity_threshold: float = 0.0
    adjusted_risk: float = 0.0
    recommendation: str = ""
    environment_strictness: float = 1.0

    def to_omnix_dict(self) -> dict:
        return {
            "probability_score": round(self.probability_score, 2),
            "risk_exposure": round(self.risk_exposure, 2),
            "signal_coherence": round(self.signal_coherence, 2),
            "trend_persistence": round(self.trend_persistence, 2),
            "stress_resilience": round(self.stress_resilience, 2),
            "logic_consistency": round(self.logic_consistency, 2),
        }


class AgentSignalAdapter:
    """
    Adapts autonomous agent decision parameters to OMNIX governance signals.
    Domain-agnostic: same 11-checkpoint pipeline, agent vocabulary.
    """

    def adapt(self, decision: AgentDecisionInput) -> AgentGovernanceSignals:
        try:
            env_factor = ENVIRONMENT_RISK_AMPLIFIERS.get(decision.environment, 1.0)
            rev_factor = REVERSIBILITY_FACTORS.get(decision.reversibility, 1.30)
            agent_risk = AGENT_RISK_BASE.get(decision.agent_type, 1.0)
            complexity_threshold = COMPLEXITY_THRESHOLDS.get(decision.decision_type, 0.72)

            # Data sensitivity penalty (PHI = medical data, PII = personal data)
            sensitivity_penalty = {
                "low": 0.0, "medium": 8.0, "high": 18.0, "pii": 28.0, "phi": 35.0
            }.get(decision.data_sensitivity, 0.0)

            # Retry penalty (repeated failures signal a stuck/unsafe agent)
            retry_penalty = min(20.0, decision.retry_count * 6.0)

            # ── Signal 1: Probability Score (Task Viability) ───────────────────
            # Can this agent successfully complete this task given complexity and resources?
            complexity_factor = (100.0 - decision.task_complexity) * 0.45
            resource_factor = (100.0 - decision.resource_utilization) * 0.30
            context_factor = decision.context_completeness * 0.25

            base_prob = complexity_factor + resource_factor + context_factor - retry_penalty
            probability_score = max(0.0, min(100.0, base_prob / env_factor))

            # ── Signal 2: Risk Exposure (Action Risk Index) ────────────────────
            # What is the blast radius and reversibility of this action?
            scope_risk = decision.scope_blast_radius * 0.40
            dependency_risk = decision.dependency_score * 0.30
            permission_risk = decision.permission_scope * 0.20
            sensitivity_risk = sensitivity_penalty * 0.10

            raw_risk = (scope_risk + dependency_risk + permission_risk + sensitivity_risk) * rev_factor * agent_risk
            boundary_premium = 15.0 if decision.cross_boundary else 0.0
            risk_exposure = max(0.0, min(100.0, raw_risk + boundary_premium))

            # ── Signal 3: Signal Coherence (Context-Task Alignment) ────────────
            # Do the task instructions, permissions, and environmental state align?
            context_coherence = decision.context_completeness * 0.40
            goal_coherence = decision.goal_alignment * 0.35
            perm_coherence = (100.0 - decision.permission_scope * 0.5) * 0.15
            risk_drag = decision.scope_blast_radius * 0.10

            signal_coherence = max(0.0, min(100.0,
                context_coherence + goal_coherence + perm_coherence - risk_drag
            ))

            # ── Signal 4: Trend Persistence (Goal Trajectory) ─────────────────
            # Is the agent making progress toward its goal? Is the trajectory stable?
            goal_progress = decision.goal_alignment * 0.55
            context_stability = decision.context_completeness * 0.30
            resource_stability = (100.0 - decision.resource_utilization) * 0.15

            trend_persistence = max(0.0, min(100.0,
                goal_progress + context_stability + resource_stability - retry_penalty
            ))

            # ── Signal 5: Stress Resilience (Failure Mode Coverage) ───────────
            # Can this agent handle failure modes, dependency outages, edge cases?
            fallback_factor = decision.fallback_coverage * 0.55
            dependency_resilience = (100.0 - decision.dependency_score) * 0.30
            scope_resilience = (100.0 - decision.scope_blast_radius) * 0.15

            stress_resilience = max(0.0, min(100.0,
                fallback_factor + dependency_resilience + scope_resilience
            ))

            # ── Signal 6: Logic Consistency (Authorization & Ethics) ──────────
            # Is this action authorized? Does it align with principal hierarchy and safety?
            goal_logic = decision.goal_alignment * 0.45
            context_logic = decision.context_completeness * 0.25

            # Hard penalties
            safety_penalty = 50.0 if decision.safety_critical_flag else 0.0
            auth_penalty = 45.0 if (decision.human_approval_required and not decision.human_approved) else 0.0
            boundary_penalty = 20.0 if decision.cross_boundary else 0.0

            logic_consistency = max(0.0, min(100.0,
                goal_logic + context_logic - safety_penalty - auth_penalty
                - boundary_penalty - sensitivity_penalty * 0.3
            ))

            # Composite recommendation
            composite = (
                probability_score
                + (100.0 - risk_exposure)
                + signal_coherence
                + trend_persistence
                + stress_resilience
                + logic_consistency
            ) / 6.0

            if composite >= 70:
                rec = "LIKELY_APPROVE"
            elif composite >= 50:
                rec = "HUMAN_REVIEW"
            else:
                rec = "HIGH_RISK"

            return AgentGovernanceSignals(
                probability_score=probability_score,
                risk_exposure=risk_exposure,
                signal_coherence=signal_coherence,
                trend_persistence=trend_persistence,
                stress_resilience=stress_resilience,
                logic_consistency=logic_consistency,
                complexity_threshold=complexity_threshold * 100.0,
                adjusted_risk=min(risk_exposure * rev_factor, 100.0),
                recommendation=rec,
                environment_strictness=env_factor,
            )

        except Exception as e:
            logger.error(f"AgentSignalAdapter.adapt error: {e}")
            return AgentGovernanceSignals(
                probability_score=50.0, risk_exposure=50.0, signal_coherence=50.0,
                trend_persistence=50.0, stress_resilience=50.0, logic_consistency=50.0,
                recommendation="ERROR_FALLBACK",
            )
