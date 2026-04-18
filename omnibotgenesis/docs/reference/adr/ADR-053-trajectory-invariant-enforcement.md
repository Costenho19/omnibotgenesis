# ADR-053: Trajectory Invariant Enforcement (TIE)

**Status**: Accepted — Implemented  
**Date**: March 27, 2026  
**Authors**: Harold Nunes, OMNIX Core  
**Internal Build Reference**: 6.5.4e  

---

## Context

The OMNIX 8-checkpoint pipeline evaluates each governance decision in isolation — it checks whether the *current state* of the incoming signals satisfies all checkpoint thresholds. This reactive validation is necessary but insufficient for sustained governance integrity.

The core limitation: a system can make individually valid decisions while moving, step by step, toward a globally inadmissible region. Each step appears valid. The trajectory, however, is dangerous.

This problem was articulated externally by Rigel Randolph (investor/researcher) as the distinction between *reactive validation* and *Trajectory Invariant Enforcement* (bounded evolution). The question is not whether state S_t is valid, but whether the path S_0 → S_t → S_t+n remains within the admissible trajectory space.

### EBIP vs TIE — Architectural Distinction

OMNIX already has EBIP (ADR-045), which monitors decision distribution patterns and detects concentration risk at the execution boundary. EBIP and TIE are complementary but architecturally distinct:

| Concern | EBIP | TIE |
|---------|------|-----|
| Level | Execution boundary | Trajectory space |
| What it monitors | Distribution of decisions over windows | Signal evolution across consecutive evaluations |
| What it enforces | Concentration limits, commitment integrity | Trajectory invariants (risk drift, coherence decay, dead zones) |
| Response | Warning / CAUTION flags (never blocks) | HOLD (converts APPROVED → HOLD when trajectory is heading toward inadmissible region) |
| Scope | Global (all assets) | Per-asset + global regime collapse |

---

## Decision

Implement the Trajectory Invariant Engine (TIE) as a post-pipeline gate that:

1. Operates **after** all 8 checkpoints pass (only on APPROVED decisions)
2. Evaluates 5 trajectory-level invariants using per-asset signal history
3. Converts APPROVED → HOLD when a trajectory invariant is violated
4. Never overrides BLOCKED decisions (those are already handled by checkpoints)
5. Fails silently (exceptions → pass-through) to preserve pipeline availability

### Position in Architecture

```
Signals → CAG (ADR-050) → EBIP ACV (ADR-045) → 8 Checkpoints → TIE (ADR-053) → Final Decision
                                                 [BLOCKED]                           [BLOCKED]
                                                 [APPROVED] ──────────────────────→ [APPROVED | HOLD]
```

---

## Invariants

### I-1: RISK_MONOTONIC_ASCENT
**Trigger**: `risk_exposure > 70` AND monotonically increasing for 5+ consecutive decisions  
**Severity**: HOLD  
**Rationale**: The system is trajectory-committed to a high-risk region. Even if each individual decision "passes" at risk_exposure=71, 73, 75, 78, 80 — the trajectory shows a structural move toward catastrophic exposure. No individual checkpoint catches this.

### I-2: PROBABILITY_DEAD_ZONE
**Trigger**: `probability_score < 35` for 4+ consecutive decisions  
**Severity**: HOLD  
**Rationale**: The asset has entered a state where no trajectory exits are visible without a regime change. Continuing to approve at probability_score=33 each cycle represents path-dependent risk accumulation.

### I-3: COHERENCE_STRUCTURAL_DECAY
**Trigger**: `signal_coherence < 40` for 3+ consecutive decisions  
**Severity**: HOLD  
**Rationale**: The governance signals have entered a state of structural incoherence. When all signals are contradicting each other for multiple consecutive evaluations, any approval is built on unstable epistemic ground.

### I-4: TRAJECTORY_VOLATILITY
**Trigger**: `stdev(probability_score over last 8 decisions) > 32`  
**Severity**: WARNING (non-blocking)  
**Rationale**: High variance in probability_score suggests the system is near a regime transition boundary. This is a precursor to more serious trajectory violations — a warning allows operators to monitor before action is required.

### I-5: GLOBAL_REGIME_COLLAPSE
**Trigger**: 3+ distinct assets simultaneously have `avg_probability_score < 35` in the last 30 minutes  
**Severity**: HOLD  
**Rationale**: When multiple assets simultaneously enter the dead zone, this signals a cross-asset regime collapse — a macro event that invalidates all individual evaluations. This invariant operates across assets, not just within a single asset's trajectory.

---

## Storage

New table `trajectory_states`:

```sql
CREATE TABLE trajectory_states (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    asset VARCHAR(50) NOT NULL,
    domain VARCHAR(50) NOT NULL DEFAULT 'generic',
    decision VARCHAR(20) NOT NULL,
    probability_score NUMERIC(5,2),
    risk_exposure NUMERIC(5,2),
    signal_coherence NUMERIC(5,2),
    trend_persistence NUMERIC(5,2),
    stress_resilience NUMERIC(5,2),
    logic_consistency NUMERIC(5,2),
    receipt_id VARCHAR(100),
    tie_applied BOOLEAN DEFAULT FALSE,
    tie_hold_issued BOOLEAN DEFAULT FALSE,
    tie_violations TEXT
);
```

Rolling window: TIE stores the last 20 states per asset/domain. Older entries are pruned automatically on each write.

---

## Integration

TIE is integrated into `GovernanceEvaluationEngine.evaluate()` in `external_evaluator.py`:

- Runs after all 8 checkpoints (and optional CP-9 AML, CP-10 Fraud, CP-11 Jurisdiction gates)
- Only runs when pipeline decision is APPROVED
- Enabled by default (`TIE_ENABLED=true`)
- DB connection injected via `compliance_config["tie_db_conn"]` (optional — if not provided, runs without history persistence)
- Result included in response as `trajectory_analysis` block

### Response Schema Addition

```json
{
  "trajectory_analysis": {
    "enabled": true,
    "trajectory_decision": "APPROVED | HOLD",
    "trajectory_score": 87.5,
    "passed": true,
    "window_size": 12,
    "violations": [],
    "warnings": [
      {
        "id": "I-4",
        "name": "TRAJECTORY_VOLATILITY",
        "description": "...",
        "trigger_value": 33.2
      }
    ]
  }
}
```

---

## Consequences

### Positive
- **Bounded evolution**: The system can no longer drift into inadmissible trajectory regions through a series of individually-valid decisions.
- **Transparent governance**: Trajectory analysis is included in every evaluation response, providing a complete audit trail of trajectory health.
- **Domain-agnostic**: TIE operates on the same 6 normalized signals as the pipeline — works identically for trading, credit, and all future verticals.
- **Fail-safe**: Exceptions in TIE never block the main pipeline — fail-closed posture is preserved.

### Negative / Trade-offs
- **HOLD increase**: Some decisions that would have been APPROVED under the 8-checkpoint pipeline alone will become HOLD when trajectory invariants are violated. This is the intended behavior — it is a feature, not a limitation.
- **Storage overhead**: `trajectory_states` table grows at O(assets × window) per evaluation. With the 20-entry rolling window and prune logic, this is bounded and negligible.
- **No trajectory override**: By design, there is no operator override for trajectory invariants (unlike some checkpoint thresholds). If TIE issues a HOLD, the system cannot proceed until the trajectory exits the invariant violation zone.

---

## Competitive Shield

The TIE implementation details (invariant IDs, thresholds, window sizes, global collapse logic, DB schema) are **INTERNAL** and must not be disclosed in external documentation, API docs, or investor materials. External communication refers to "trajectory-aware governance" or "bounded evolution enforcement" without specifics.

---

## Related ADRs

- ADR-028: External Signal Evaluation API (pipeline foundation)
- ADR-044: Transparency Chain (receipt integrity)
- ADR-045: Execution Boundary Integrity Protocol (EBIP — complementary)
- ADR-050: Context Admission Gate (pre-pipeline)
- ADR-052: Islamic Credit Governance (first domain to run under TIE)
