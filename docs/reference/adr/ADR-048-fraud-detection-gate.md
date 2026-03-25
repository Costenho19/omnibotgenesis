# ADR-048: Fraud Detection Gate (CP-10)

**Status:** ACCEPTED  
**Date:** March 25, 2026  
**Author:** Harold Nunes  
**Module:** `omnix_core/governance/fraud_gate.py`

---

## Context

Automated decision systems operating in financial markets are subject to EU AI Act Article 6, which classifies them as high-risk AI systems requiring mandatory transparency and fraud prevention measures. Additionally, MiFID II (EU) and SEC Rule 10b-5 (US) impose market manipulation detection obligations on automated trading infrastructure.

OMNIX already computes the Decision Contradiction Index (DCI) internally, which quantifies signal incoherence. CP-10 formalizes this signal as a fraud/manipulation detection gate with a hard-veto capability and a PQC-signed audit record.

---

## Decision

Implement CP-10 — the **Fraud Detection Gate** — positioned AFTER CP-9 (AML Gate) in the decision pipeline.

### Design Principles

1. **Fail-safe by default** — disabled for all existing clients; exceptions → pass-through
2. **Activatable via env var** — `FRAUD_GATE_ENABLED=true`
3. **Uses existing DCI signal** — no new computation required; reuses `decision_contradiction_index`
4. **Zero impact on existing pipeline** — default OFF preserves Railway operation

---

## Implementation

### Module: `omnix_core/governance/fraud_gate.py`

Three validation checks in sequence:

| Check | Rule | Behavior |
|-------|------|----------|
| **1. Extreme DCI** | DCI ≥ 85 (default) | Hard VETO — `EXTREME_DCI` |
| **2. Signal divergence** | \|technical - sentiment\| ≥ 60 (default) | Hard VETO — `SIGNAL_DIVERGENCE` |
| **3. Rapid reversals** | Reversals in last N cycles ≥ threshold | Score deduction (-35 pts) |

### Pipeline Position

```
CP-8 (ECW) → CP-9 (AML Gate) → CP-10 (Fraud Gate) ← NEW → CP-11 (Jurisdiction Gate)
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FRAUD_GATE_ENABLED` | `false` | Master enable switch |
| `FRAUD_DCI_THRESHOLD` | `85.0` | DCI hard-veto threshold (0-100) |
| `FRAUD_DIVERGENCE_THRESHOLD` | `60.0` | Tech vs sentiment divergence threshold |
| `FRAUD_REVERSAL_WINDOW` | `3` | Max consecutive reversals before flag |
| `FRAUD_BLOCK_EXTREME_DCI` | `true` | Enable DCI hard veto |
| `FRAUD_BLOCK_SIGNAL_DIVERGENCE` | `true` | Enable divergence hard veto |

### Signal Inputs (reusing existing pipeline data)

| Signal | Source | Description |
|--------|--------|-------------|
| `dci_score` | `decision_contradiction_index` | Internal signal incoherence (0-100) |
| `technical_score` | `decision['score']` | Composite technical signal strength |
| `sentiment_score` | `v52_analysis.sentiment_score` | Market sentiment (0-100) |

### Logging Format

```
🕵️ [CP-10] FRAUD_VETO: {violation} | asset={symbol} | integrity={score}
🕵️ [CP-10] FRAUD_PASS: NONE | asset={symbol} | integrity=100/100
```

### Receipt Block

```json
{
  "fraud_compliance": {
    "check": "enabled",
    "result": "passed|failed|skipped",
    "integrity_score": 100.0,
    "violation": "",
    "asset": "BTC/USD"
  }
}
```

---

## DCI Threshold Rationale

| DCI Range | Interpretation | Action |
|-----------|----------------|--------|
| 0–49 | Normal signal coherence | Pass |
| 50–84 | Elevated instability — score deduction | Pass (with penalty) |
| ≥ 85 | Manipulation-level incoherence | Hard VETO |

The 85 threshold is set conservatively: it corresponds to extreme signal contradiction that statistically exceeds noise levels in normal market conditions. A DCI ≥ 85 with an active trade signal is a strong indicator of manipulated or corrupted input data.

---

## Consequences

### Positive
- Formalizes the DCI signal as a compliance mechanism with regulatory justification (EU AI Act)
- Every fraud veto generates a PQC-signed record — directly useful for regulatory reporting
- No new computation cost — reuses existing pipeline signals
- CP-10 slot formally assigned

### Negative / Trade-offs
- DCI threshold (85) may generate false positives in highly volatile markets — tunable via env var
- Signal divergence check uses simple absolute difference — more sophisticated correlation metrics deferred
- Recent reversals counter not yet populated from Redis history — defaulting to 0

---

## Investor Narrative

> "Every decision OMNIX evaluates is screened for manipulation patterns before execution — not after. If internal signals contradict each other beyond the statistical fraud threshold, the system stops and generates a cryptographic proof of why it stopped."

---

## Related ADRs

- ADR-022: Post-Quantum Cryptography
- ADR-023: Track Record Period Disclosure
- ADR-046: Sharia Gate (CP-6) — same pattern
- ADR-047: AML Gate (CP-9)
- ADR-049: Jurisdiction Gate (CP-11)
