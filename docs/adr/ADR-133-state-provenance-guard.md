# ADR-133 — State Provenance Guard

**Status:** ACCEPTED (v1)
**Date:** 2026-04-27
**Author:** OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo
**Context:** Pre-bind lineage singularity check — ADR-133

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| v1 | 2026-04-27 | Initial implementation — StateProvenanceGuard, hypothesis evaluation, contradiction detection, advisory integration in /evaluate and /api/governance/evaluate |

---

## 1. Context and Problem Statement

OMNIX already verifies that incoming states are **structurally admissible** (SAE, Layer 0)
and that the **global market context allows evaluation** (CAG, ADR-050). Both checks verify
*what* the state is and *whether* the current context permits evaluation.

Neither check verifies **how the state was formed**.

Eduardo Monteiro (distributed systems researcher) identified a failure mode at the execution
boundary that OMNIX's existing checks do not address:

> "Systems that pass audit, validation, and traceability, but still act on states that don't
> resolve to a single origin. Compliant — internally consistent — but reconstructed,
> not singular. Which means execution can bind consequence over something that was never
> uniquely formed."

The minimal check Eduardo proposes:

> "Can this state be explained by more than one plausible lineage pre-bind?
> If yes → ambiguity exists before consequence. No heavy reconstruction — just a lightweight signal."

This is a **formation test**, not a content test. A state can be:
- ✅ Structurally valid (passes SAE)
- ✅ Internally consistent (passes all 11 checkpoints)
- ✅ Fully traceable (PQC receipt, WAL chain)
- ⚠️ **Ambiguous in provenance** — multiple causal hypotheses equally explain the inputs

When execution binds over an ambiguous state, the audit trail is accurate but the
decision was never actually grounded in a single causal origin.

---

## 2. Decision

Implement a **State Provenance Guard (SPG)** as a new pre-pipeline evaluation layer.

Architecture position:
```
ProposedRequest → SAE (Layer 0) → SPG (Layer 0b) → CAG → CP-0…CP-11 → TIE → PQC Receipt
```

**Layer 0b** — State Provenance Guard — runs after structural admissibility and before
any signal enters the evaluation pipeline. It is the only moment in the evaluation
lifecycle when state provenance can be assessed without binding consequence.

### 2.1 Non-negotiable design constraints

**Constraint 1: Advisory by default**
The SPG operates in ADVISORY mode. An AMBIGUOUS verdict embeds in the receipt but
does not block evaluation. This preserves backward compatibility and ensures SPG
exceptions never disrupt the governance pipeline.

**Constraint 2: Fail-safe**
Any SPG exception returns `INDETERMINATE` verdict and never blocks the pipeline.
The SPG cannot be a failure point for governance decisions.

**Constraint 3: Full audit trail**
Every evaluation produces a `state_provenance` block in the decision receipt,
including: verdict, lineage_singularity score, hypothesis fits, detected
contradictions, and a provenance_hash (tamper-evident).

**Constraint 4: Blocking mode available**
For clients that require provenance singularity enforcement, `SPGMode.BLOCKING`
is available. In this mode, `AMBIGUOUS` verdict blocks the evaluation fail-closed.

---

## 3. Architecture

### 3.1 Evaluation Components

**A — Hypothesis Registry**
Five market hypotheses representing distinct causal states:

| Hypothesis | Description |
|---|---|
| `BULLISH` | Strong positive directional state with controlled risk |
| `BEARISH` | Negative directional state with elevated risk signals |
| `RANGING` | Neutral, range-bound — no dominant directional pressure |
| `HIGH_VOLATILITY` | Elevated risk and stress with degraded resilience |
| `STABLE_LOW_RISK` | Low risk, high resilience, stable formation |

Each hypothesis defines a set of signal conditions and a `fit_floor` (minimum
proportion of conditions that must be satisfied for the hypothesis to be active).

**B — Contradiction Detector**
Four internal signal pairs with expected directional relationships:

| Pair | Expected | Tolerance | Severity |
|---|---|---|---|
| `probability_score` ↔ `risk_exposure` | Inverse | ±24 | HIGH |
| `stress_resilience` ↔ `risk_exposure` | Inverse | ±26 | HIGH |
| `signal_coherence` ↔ `logic_consistency` | Direct | ±22 | MEDIUM |
| `trend_persistence` ↔ `probability_score` | Direct | ±28 | MEDIUM |

A contradiction is detected when a pair violates its expected relationship beyond
the tolerance boundary. Contradictions are evidence of multi-source signal formation.

**C — Lineage Singularity Score (0–100)**
```
score = 100
       − 18 × (active_hypothesis_count − 1)   # penalty per extra hypothesis
       − severity_weight × contradiction_count  # HIGH=14, MEDIUM=8, LOW=4
```

Score bands:
- **80–100** → `SINGULAR` — one causal origin dominates unambiguously
- **50–79**  → `INDETERMINATE` — borderline, ambiguity possible
- **0–49**   → `AMBIGUOUS` — multiple origins plausible

**D — Verdict**

| Condition | Verdict |
|---|---|
| score ≥ 80 | `SINGULAR` |
| score < 50 OR contradictions ≥ 2 | `AMBIGUOUS` |
| otherwise | `INDETERMINATE` |

### 3.2 SPGResult block (embeds in every receipt)

```json
{
  "state_provenance": {
    "verdict":              "SINGULAR",
    "lineage_singularity":  86.0,
    "dominant_hypothesis":  "BULLISH",
    "hypothesis_fits": {
      "BULLISH":          0.75,
      "BEARISH":          0.0,
      "RANGING":          0.0,
      "HIGH_VOLATILITY":  0.0,
      "STABLE_LOW_RISK":  0.0
    },
    "contradictions":        [],
    "contradiction_count":   0,
    "evaluation_mode":       "ADVISORY",
    "blocked":               false,
    "spg_id":                "SPG-A3F2B1C9D0E4",
    "evaluated_at":          "2026-04-27T22:00:00.000000+00:00",
    "elapsed_ms":            0.41,
    "signal_count":          6,
    "adr_reference":         "ADR-133",
    "provenance_hash":       "sha256:..."
  }
}
```

### 3.3 Integration Points

| Endpoint | Integration | Mode |
|---|---|---|
| `POST /evaluate` | `proof_layer.py` — after `_build_signals()`, before `engine.evaluate()` | ADVISORY |
| `POST /api/governance/evaluate` | `gov_blueprint.py` — after `validate_signals()`, before `engine.evaluate()` | ADVISORY |

Both endpoints return `state_provenance` in the response body.

---

## 4. Answers to Eduardo's Test

Eduardo's proposed flow: **single system, clear authority, one binding decision**.
Goal: see if anything that passes audit still fails the lineage singularity condition.

| OMNIX Layer | What it verifies | Eduardo's question answered |
|---|---|---|
| SAE (Layer 0) | State structural validity | Not directly |
| **SPG (Layer 0b)** | **State causal singularity** | **Yes — directly** |
| CAG (ADR-050) | Global market context | Not directly |
| CP-0…CP-11 | Decision content and quality | Not directly |
| PQC Receipt (Layer 3) | Tamper-evident audit trail | Not directly |

The SPG is the first mechanism in OMNIX that directly tests Eduardo's condition.

### 4.1 Expected results on the test flow

For a well-formed, non-contradictory signal state (typical institutional client):
- `verdict`: `SINGULAR`
- `lineage_singularity`: 80–100
- `contradictions`: []
- `blocked`: false

For a signal state with contradictory or ambiguous formation:
- `verdict`: `AMBIGUOUS`
- `lineage_singularity`: 0–49
- `contradictions`: 1–4 entries
- `blocked`: false (ADVISORY) | true (BLOCKING)

---

## 5. Files

| File | Role |
|---|---|
| `omnix_core/governance/state_provenance_guard.py` | Core module — `StateProvenanceGuard`, `SPGResult`, `evaluate_provenance()` |
| `omnix_web/api/proof_layer.py` | Integration at `POST /evaluate` |
| `omnix_web/api/gov_blueprint.py` | Integration at `POST /api/governance/evaluate` |
| `tests/test_state_provenance_guard.py` | Full test suite |
| `docs/adr/ADR-133-state-provenance-guard.md` | This document |

---

## 6. Compliance Checklist

| Requirement | Status |
|---|---|
| Fail-closed on exception | ✅ Returns INDETERMINATE, never blocks |
| Non-blocking by default | ✅ ADVISORY mode, backward compatible |
| Full audit trail in receipt | ✅ `state_provenance` block in every response |
| Provenance hash (tamper-evident) | ✅ SHA-256(spg_id + verdict + score) |
| Thread-safe | ✅ Stateless evaluation, singleton with lock |
| TESTING mode safe | ✅ No background threads |
| Zero impact on existing tests | ✅ Advisory-only, no pipeline modification |
| Blocking mode available | ✅ `SPGMode.BLOCKING` — configurable per use case |
| Regulatory alignment | ✅ EU AI Act Art. 9, MiFID II, NIST AI RMF |
| ADR count | **42** |
