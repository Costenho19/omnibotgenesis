# ADR-050: Context Admission Gate (CAG)

**Status:** ACCEPTED  
**Date:** March 26, 2026  
**Author:** Harold Nunes  
**Module:** `omnix_core/governance/context_admission_gate.py`

---

## Context

OMNIX's 8-checkpoint pipeline evaluates the quality and coherence of individual signals. However, there is a category of systemic risk that no per-signal check can catch: global market conditions so adverse that no individual evaluation should proceed regardless of signal quality.

A high-probability, high-coherence signal can still be structurally inadmissible when:
- Market volatility is extreme (regime shift, flash crash)
- Cross-asset correlation collapses diversification assumptions
- Liquidity is insufficient to execute without slippage beyond governance thresholds
- Macro risk (geopolitical, regulatory, systemic) exceeds safe operating ceilings

These conditions require a **session-level admission decision** — a gate that runs BEFORE any signal enters the pipeline, not inside it.

---

## Decision

Implement the **Context Admission Gate (CAG)** as a pre-pipeline session-level admission layer positioned logically BEFORE CP-0 in the decision governance architecture.

### Key architectural distinction

| Layer | What it evaluates | Granularity |
|-------|------------------|-------------|
| **CAG** | Global market conditions (context) | Per session/window |
| **CP-0 to CP-8** | Individual signal quality and risk | Per decision |
| **CP-9/10/11** | Compliance (AML/Fraud/Jurisdiction) | Per decision |

### Design Principles

1. **Fail-safe by default** — disabled (`CAG_ENABLED=false`); exceptions → pass-through
2. **Session-level, not signal-level** — one admission decision per evaluation window
3. **Four independent parameters** — each maps to a real-world systemic risk category
4. **Zero impact on existing clients** — default OFF; existing Railway deployment unchanged
5. **PQC receipt compatible** — CAG result block can be embedded in Dilithium-3-signed receipts

---

## Implementation

### Module: `omnix_core/governance/context_admission_gate.py`

Four checks evaluated in sequence:

| Check | Parameter | Condition | Hard Veto Code |
|-------|-----------|-----------|---------------|
| **1** | `global_volatility` | Must be < threshold (default: 80) | `GLOBAL_VOLATILITY_EXCEEDED` |
| **2** | `cross_pair_correlation` | Must be < threshold (default: 90) | `CORRELATION_REGIME_INSTABILITY` |
| **3** | `liquidity_score` | Must be ≥ minimum (default: 20) | `INSUFFICIENT_LIQUIDITY` |
| **4** | `macro_risk` | Must be < ceiling (default: 85) | `MACRO_RISK_CEILING_BREACHED` |

### Pipeline Position

```
[CAG — Session Admission]
        ↓ ADMITTED
CP-0 (SIV) → CP-1 → CP-2 → CP-3 → CP-4 → CP-5 → CP-6 (Sharia) → CP-7 (TCV) → CP-8 (ECW)
        ↓
CP-9 (AML) → CP-10 (Fraud) → CP-11 (Jurisdiction)
```

If CAG blocks: `SESSION_BLOCKED` — no signals enter the pipeline. No executable state is formed.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CAG_ENABLED` | `false` | Master enable switch |
| `CAG_VOLATILITY_THRESHOLD` | `80.0` | Max global volatility index allowed |
| `CAG_CORRELATION_THRESHOLD` | `90.0` | Max cross-pair correlation allowed |
| `CAG_LIQUIDITY_MINIMUM` | `20.0` | Min liquidity score required |
| `CAG_MACRO_RISK_CEILING` | `85.0` | Max macro risk score allowed |
| `CAG_BLOCK_ON_ANY_VIOLATION` | `true` | Block on first violation vs. score-based |

### Logging Format

```
🚫 [CAG] SESSION_BLOCKED: GLOBAL_VOLATILITY_EXCEEDED: 85.0 >= 80.0 | admission_score=75/100
✅ [CAG] SESSION_ADMITTED: all 4 checks passed | vol=20.0, corr=30.0, liq=85.0, macro=15.0
⚠️ [CAG] VOLATILITY CHECK FAILED: global_vol=85.0 >= threshold=80.0
```

### Receipt Block (when CAG is enabled)

```json
{
  "context_admission": {
    "check": "enabled",
    "result": "admitted|blocked|skipped",
    "admission_score": 95.0,
    "violation": "",
    "parameters": {
      "global_volatility": 20.0,
      "cross_pair_correlation": 30.0,
      "liquidity_score": 85.0,
      "macro_risk": 15.0
    },
    "gate_checks": [
      {"parameter": "global_volatility", "value": 20.0, "threshold": 80.0, "result": "PASS"},
      {"parameter": "cross_pair_correlation", "value": 30.0, "threshold": 90.0, "result": "PASS"},
      {"parameter": "liquidity_score", "value": 85.0, "threshold": 20.0, "result": "PASS"},
      {"parameter": "macro_risk", "value": 15.0, "threshold": 85.0, "result": "PASS"}
    ]
  }
}
```

---

## Activation Example

For institutional clients operating in volatile GCC markets:

```bash
CAG_ENABLED=true
CAG_VOLATILITY_THRESHOLD=75.0
CAG_LIQUIDITY_MINIMUM=25.0
CAG_MACRO_RISK_CEILING=80.0
```

Result: During a Black Thursday-type event (vol=92, liquidity=8, macro=90), OMNIX generates a `SESSION_BLOCKED` receipt BEFORE any signal is evaluated. The audit trail shows "No executable state was ever formed."

---

## Investor Narrative

> "When market conditions become structurally inadmissible — extreme volatility, liquidity crisis, macro shock — OMNIX doesn't just block individual signals. It blocks the entire evaluation session before it starts. The cryptographic receipt doesn't say 'we decided to wait.' It says 'no executable state was ever formed.' That distinction matters to regulators."

---

## Consequences

### Positive
- Adds session-level context governance — a layer no competitor has documented
- Directly addresses "what happens during a flash crash?" investor question
- `SESSION_BLOCKED` receipts are verifiable evidence of systemic risk governance
- Extensible: new context parameters can be added without changing the pipeline
- Directly supports UAE/GCC deployment narrative (volatile emerging markets)

### Negative / Trade-offs
- Real-time market data (VIX, liquidity indices) not yet connected — parameters must be supplied externally or via future market data integration
- Default `block_on_any_violation=True` may be conservative for some clients — configurable via env

---

## Related ADRs

- ADR-022: Post-Quantum Cryptography
- ADR-028: External Governance API
- ADR-033: Signal Integrity Validator (CP-0)
- ADR-045: Execution Boundary Integrity Protocol (EBIP)
- ADR-046: Sharia Gate (CP-6)
- ADR-047: AML Gate (CP-9)
- ADR-048: Fraud Gate (CP-10)
- ADR-049: Jurisdiction Gate (CP-11)
