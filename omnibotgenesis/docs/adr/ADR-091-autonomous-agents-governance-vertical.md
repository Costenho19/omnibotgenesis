# ADR-091: Autonomous Agent Governance Vertical (AGL-AGT-001)

**Status:** ACCEPTED  
**Date:** April 2026  
**Internal Code:** AGL-AGT-001  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Scope:** `omnix_core/agents/` · `omnix_dashboard/blueprints/agents_governance.py` · `omnix_web/src/pages/AgentsDashboard.tsx` · `omnix_web/src/pages/AgentsGovernanceDemo.tsx`

---

## Context

Autonomous AI agents executing tasks in production environments (financial systems,
enterprise workflows, infrastructure) require the same governance discipline applied to
human decisions. Without governance, agents can take irreversible actions with blast
radii that span multiple systems, violate principal hierarchies, or operate outside
approved authorization boundaries.

OMNIX extends its 11-checkpoint pipeline to the autonomous agent domain, providing
pre-execution governance for every agent action before it is committed.

---

## Decision

Build a full-stack governance vertical for autonomous agent decisions, applying the
OMNIX 11-checkpoint pipeline adapted to the agent action domain.

---

## Signal Adapter

**File:** `omnix_core/agents/agents_signal_adapter.py`

Maps 8 agent parameters to 6 OMNIX governance signals:

| Agent Parameter | OMNIX Signal | Interpretation |
|----------------|-------------|----------------|
| `task_complexity` | `probability_score` | Viability probability |
| `scope_blast_radius` | `risk_exposure` | Action blast radius |
| `context_completeness + task_alignment` | `signal_coherence` | Context coherence |
| `goal_alignment` | `trend_persistence` | Goal trajectory stability |
| `fallback_coverage` | `stress_resilience` | Failure mode robustness |
| `authorization + ethics_score` | `logic_consistency` | Principal hierarchy compliance |

### Hard blocks (pipeline stops regardless of scores)
- `safety_critical_flag = True` → BLOCK
- `human_approval_required = True` AND `human_approved = False` → BLOCK

---

## Simulator

**File:** `omnix_core/agents/agents_simulator.py`

24/7 simulator for live data generation:

| Parameter | Value |
|-----------|-------|
| Cycle interval | 200 seconds |
| Decisions per cycle | 3–8 |
| Decision types | task_delegation (35%) · data_access (20%) · external_api_call (18%) · resource_allocation (15%) · state_modification (12%) |
| Agent types | Financial_Agent · Enterprise_Agent · Logistics_Agent · Infrastructure_Agent · Research_Agent |
| Environments | production · staging · development · sandbox (strictness amplifiers) |
| Reversibility | fully_reversible · partially_reversible · irreversible · unknown |
| Data sensitivity | low · medium · high · pii · phi |
| Tables | `agent_decisions` + `agent_cycle_metrics` |

---

## Flask Blueprint

**File:** `omnix_dashboard/blueprints/agents_governance.py`

Endpoints at `/api/agents/*`:

| Endpoint | Purpose |
|----------|---------|
| `/api/agents/metrics` | Aggregate KPIs |
| `/api/agents/decisions` | Decision list |
| `/api/agents/by-type` | Breakdown by decision type |
| `/api/agents/by-agent` | Breakdown by agent type |
| `/api/agents/by-environment` | Breakdown by environment |
| `/api/agents/timeline` | 24h timeline |
| `/api/agents/live-feed` | Last 30 decisions |
| `/api/agents/evaluate` | Single decision evaluation |
| `/api/agents/health` | Health check |

---

## Frontend

### `/governance-demo-agents` → `AgentsGovernanceDemo.tsx`
Interactive 11-checkpoint demo:
- Decision type, agent type, environment, reversibility, data sensitivity selectors
- Sliders: task complexity, scope blast radius, context completeness, goal alignment
- Hard block flags: safety_critical_flag, human_approval_required, human_approved, cross_boundary
- Animated pipeline evaluation with per-checkpoint reasoning
- Badge: **ADR-091**

### `/agents` → `AgentsDashboard.tsx`
Live operations dashboard:
- 7 KPI cards: total decisions, approved, blocked, approval rate, avg complexity, active agents, safety blocks
- Average signal health strip (6 signals)
- Breakdown tables: by decision type, by agent type, by environment
- Live decision feed (30 decisions, 10s refresh)
- 3 feature callout cards: PQC receipts, hard safety blocks, principal hierarchy

---

## Infrastructure integration

| File | Change |
|------|--------|
| `omnix_dashboard/blueprints/__init__.py` | `agents_bp` imported and exported |
| `omnix_dashboard/app.py` | Blueprint registered, tables initialized eagerly, simulator started |
| `omnix_web/src/App.tsx` | Routes `/governance-demo-agents` + `/agents` |
| `omnix_web/src/pages/ClientDashboard.tsx` | `autonomous_agent: '🧠' / #fb923c` |
| `omnix_web/src/pages/AuditDashboard.tsx` | `autonomous_agent: '🧠' / #fb923c` |
| `omnix_core/evidence/decision_receipt.py` | `"autonomous_agent": "AGT"` in `_DOMAIN_CODES` |

---

## Regulatory frameworks covered

| Framework | Alignment |
|-----------|-----------|
| EU AI Act — High-Risk AI Systems | CP-7 (ethics) + CP-11 (jurisdiction) |
| NIST AI RMF (GOVERN, MAP, MEASURE) | Full 11-checkpoint pipeline |
| ISO 42001 AI Management | Audit trail + PQC receipt |
| IEEE 7000 — Ethical AI Design | Hard blocks on safety_critical + human approval |

---

## Engine Integration (ADR-115)

As of **15 April 2026**, the Autonomous Agents vertical routes all non-blocked decisions through
`GovernanceEvaluationEngine.evaluate(domain="autonomous_agent")` — ADR-115 (Engine Unification).

Hard blocks (safety_critical_flag · human_approval_required + not approved) bypass the engine
with immediate BLOCKED at `decision_score = composite × 0.15`. All other decisions run the full
11-checkpoint pipeline including AVM, CAG, EBIP, CP-1 through CP-11.

---

## References

- ADR-041: Multi-Agent Decision Governance (foundational)
- ADR-044: Quantum-Secure Decision Receipts
- ADR-083: Enterprise Bot Security (bot command complement)
- ADR-115: Engine Unification — all 8 verticals on `GovernanceEvaluationEngine` (15 Apr 2026)
- AGL-AGT-001 entry in `replit.md`
- `docs/OMNIX-Autonomous-Governance-Layer.md` — Section 8: Implementation Reference
