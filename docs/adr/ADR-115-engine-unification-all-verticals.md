# ADR-115: Engine Unification — All 10 Verticals on GovernanceEvaluationEngine

**Status:** ACCEPTED  
**Date:** 15 April 2026 (updated 06 May 2026 — expanded to 10 verticals via ADR-136, ADR-137)  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Scope:** `omnix_core/medical/medical_simulator.py` · `omnix_core/real_estate/real_estate_simulator.py` · `omnix_core/agents/agents_simulator.py` · `omnix_core/energy/energy_simulator.py`  
**Resolves:** Architecture gap — 4 of 8 verticals used independent local logic instead of the central governance engine

---

## Context

### Pre-ADR-115 state

Following the multi-vertical expansion (ADR-026, ADR-091, ADR-112, ADR-136, ADR-137), OMNIX now has 10 live
verticals, all on the same engine. The original gap (pre-ADR-115) was 8 verticals with two classes of engine integration:

**Class A — Fully integrated (called `GovernanceEvaluationEngine`):**
- Digital Asset Trading
- Islamic Credit (+ Sharia Gate post-engine)
- Insurance Underwriting
- Robotics Action Governance

**Class B — Local logic (simulated checkpoint output without engine):**
- Medical AI — manual threshold dict, string-based checkpoint list
- Real Estate — manual threshold dict, no AVM drift detection
- Autonomous Agents — manual threshold dict, no coherence engine
- Energy Governance — composite weighted average, no 11-checkpoint pipeline

Class B verticals produced decisions in the correct format and stored them correctly,
but the decisions did NOT pass through:
- AVM (Assumption Validity Monitor — ADR-064)
- CAG (Context Admission Gate — ADR-050)
- EBIP (Execution Boundary Integrity Protocol — ADR-045)
- CP-1 through CP-11 actual pipeline
- Coherence gate, ECW gate, TCV gate

This created a narrative gap: OMNIX claimed "same 11-checkpoint pipeline across all
8 verticals" — true for 4, not true for the other 4.

---

## Decision

Connect all 4 Class B verticals to `GovernanceEvaluationEngine.evaluate()` using the
exact same pattern established by the Robotics vertical (template). Preserve domain-specific
hard blocks as pre-engine checks that bypass the engine with immediate BLOCKED returns.
Maintain a rule-based fallback in case the engine is unavailable (defensive engineering).

**This is the architectural change that makes the statement true:**
> *"All 10 verticals run on the same 11-checkpoint OMNIX governance pipeline."*
> (8 original verticals via ADR-115; Robotics added via ADR-136; Islamic Credit standalone demo via ADR-137)

---

## Implementation Pattern

### Template (Robotics — Class A reference)

```python
try:
    from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
    engine = GovernanceEvaluationEngine()
    result = engine.evaluate(
        signals=signals_dict,
        asset=f"{robot_type}_{action_type}",
        domain="robotics",
        metadata={...},
    )
    decision         = result.get("decision", "BLOCKED")
    checkpoint_results = result.get("gate_results", [])
    veto_chain       = result.get("veto_chain", [])
    scores           = result.get("scores", signals_dict)
    ...
except Exception as exc:
    logger.warning(f"Governance engine unavailable: {exc} — rule-based fallback active")
    # composite fallback
```

### Applied to each vertical

| Vertical | Domain string | Asset string | Hard block conditions |
|----------|--------------|-------------|----------------------|
| Medical AI | `"medical_ai"` | `device_type + decision_type` | ethics_flag · consent_verified=False |
| Real Estate | `"real_estate"` | `property_type + decision_type` | aml_flag · rera_compliant=False · sharia_fail · ltv_breach |
| Autonomous Agent | `"autonomous_agent"` | `agent_type + decision_type` | safety_critical_flag · human_approval_required + not approved |
| Energy Governance | `"energy_governance"` | `energy_source + decision_type` | signals.hard_block_reason (from adapter) |

### Hard block treatment

Hard blocks return BLOCKED at `decision_score = composite × 0.15` — a penalised score
signalling mandatory regulatory override, distinct from marginal governance failure.
The full engine pipeline is NOT run for hard blocks. This is intentional:
- Hard blocks are non-negotiable — no AVM drift or coherence score can override them
- Running the engine on a consent-less clinical decision or AML-flagged transaction
  would waste compute and produce a misleading checkpoint trace

---

## What the engine adds that local logic cannot replicate

| Component | Local logic equivalent | Engine contribution |
|-----------|----------------------|---------------------|
| AVM (ADR-064) | None | Detects calibration drift in domain signals before evaluation |
| CAG (ADR-050) | None | Validates context admission (volatility, session, liquidity) |
| EBIP (ADR-045) | None | ACV contraindiction detection + ECP commitment + NPM pattern monitoring |
| CP-1 Signal Integrity | Basic threshold check | Structural coherence + non-finite guard (ADR-075) |
| CP-3 Risk | `risk > threshold` | Full VaR + Monte Carlo for applicable domains |
| CP-4 Coherence Gate | None | 6-tier veto coherence engine |
| CP-7 Logic Gate | Manual string append | AML + fraud + jurisdiction compliance pipeline |
| CP-9 AML | None | Full FATF frequency analysis (ADR-047) |
| CP-10 Fraud | None | Epistemic fraud gate (ADR-048) |
| CP-11 Jurisdiction | None | Cross-border semantic governance (ADR-085) |
| PQC Receipt | `build_receipt_id()` only | Full Dilithium-3 signed audit receipt |
| Fallback behaviour | Silent return BLOCKED | `logger.warning()` + graceful rule-based fallback |

---

## Fallback strategy

Each vertical retains a rule-based fallback (composite average → APPROVED/HOLD/BLOCKED).
The fallback activates only when the engine raises an exception (import failure, DB timeout,
configuration error). This ensures 24/7 simulator continuity — the vertical never crashes
due to an engine dependency failure.

Fallback decisions are NOT certified by the engine and do NOT receive full PQC receipts.
They are logged at WARNING level for monitoring.

---

## Post-implementation state

**All 8 verticals — Class A (fully integrated):**

| Vertical | Domain | Engine call | Hard blocks |
|----------|--------|------------|-------------|
| Digital Asset Trading | `trading` | ✅ | Black Swan · Monte Carlo veto |
| Islamic Credit | `islamic_credit` | ✅ | + Sharia Gate post-engine |
| Insurance Underwriting | `insurance` | ✅ | Fraud gate (CP-10) |
| Robotics Action | `robotics` | ✅ | None (sensor gates internal) |
| Medical AI | `medical_ai` | ✅ **ADR-115** | Ethics flag · Consent |
| Real Estate | `real_estate` | ✅ **ADR-115** | AML · RERA · Sharia · LTV |
| Autonomous Agents | `autonomous_agent` | ✅ **ADR-115** | Safety critical · Human approval |
| Energy Governance | `energy_governance` | ✅ **ADR-115** | Grid emergency (from adapter) |

---

## AVM log expectation post-ADR-115

Before ADR-115, the AVM log showed:
```
[AVM.DB] Loaded 4 snapshots — domains=['trading', 'islamic_credit', 'insurance', 'robotics']
```

After ADR-115 + `initialize_avm_baselines.py` run with 8 domains:
```
[AVM.DB] Loaded 8 snapshots — domains=['trading', 'islamic_credit', 'insurance', 'robotics',
                                        'medical_ai', 'energy_governance', 'real_estate',
                                        'autonomous_agent']
```

Running `python scripts/initialize_avm_baselines.py` in the Railway production environment
will seed the 4 new domain baselines added in the same release cycle.

---

## Investor / partner statement (post-ADR-115)

> *"All 8 OMNIX verticals — Trading, Islamic Credit, Insurance, Robotics, Medical AI,
> Real Estate, Autonomous Agents, and Energy — route every decision through the same
> 11-checkpoint GovernanceEvaluationEngine pipeline. Each decision produces a
> post-quantum cryptographically signed receipt (CRYSTALS-Dilithium3). Domain-specific
> hard blocks (AML, ethics, consent, safety-critical) operate as pre-engine mandatory
> overrides — not subject to any score-based waiver."*

---

## References

- ADR-026: Multi-vertical domain adapter architecture
- ADR-044: Quantum-Secure Decision Receipts
- ADR-045: Execution Boundary Integrity Protocol (EBIP)
- ADR-050: Context Admission Gate (CAG)
- ADR-064: Assumption Validity Monitor (AVM)
- ADR-091: Autonomous Agent Governance Vertical
- ADR-112: Energy Governance Vertical
- ADR-113: Medical AI Governance Vertical
- ADR-114: Real Estate Governance Vertical
- `scripts/initialize_avm_baselines.py` — 8-domain baseline seeding
