# ADR-151 — Memory Context Governance

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** —  
**Related:** ADR-028, ADR-074, ADR-147, ADR-148, ISR-017  
**Module:** `omnix_core/governance/memory_context_auditor.py`

---

## Why This Is Different

Most AI governance frameworks govern the **model** (training data, RLHF, fine-tuning, persistent memory).  
OMNIX governs the **decision** — the specific context window at the moment of each individual governance evaluation.

| Capability | Industry standard | OMNIX ADR-151 |
|---|---|---|
| What is governed | Model weights, training data, persistent memory | Decision-time context window of each evaluation |
| Granularity | Global / model-level | Per-decision, per-asset, per-timestamp |
| Signed artifact | None / optional audit log | PQC-signed MemoryAttestationRecord per decision |
| Defensibility score | Not computed | **Context Sovereignty Score (CSS 0–100)** |
| Drift classification | Magnitude only | Magnitude + **adversarial vs. natural pattern** |
| Bidirectional audit chain | Not present | Receipt ID ↔ MAR ID — tamper-evident both ways |
| Independent verification | Requires platform access | **Self-verifying** (public key embedded, no infrastructure needed) |
| Fail-closed on contamination | Typically advisory | CRITICAL contamination **blocks** the evaluation |
| Contamination layers | 1 (content filter) | **5 independent additive layers** — no layer can clear another |
| Injection detection | Input sanitization only | Structural detection in domain metadata + signal layer |
| Context provenance | Not captured | Immutable `ContextSnapshot` with SHA-256 integrity anchor |

**The distinction vs. "Constitutional Memory" and similar frameworks:**  
Constitutional Memory governs what the AI *retains persistently* (model-level, session-level, global).  
ADR-151 governs what the AI *knew at the moment of this specific decision* (decision-level, per-evaluation, sub-second).  
These are complementary — not overlapping. OMNIX operates at a finer granularity that no model-governance system addresses.  
The question is not "What does this model remember?" but "What did this specific evaluation see, and can you prove it?"

---

## Context

OMNIX's governance pipeline answers: *"Did the AI decide correctly?"*

The 11-checkpoint pipeline (ADR-028), the AVM (ADR-074), the LLM Isolation Boundary (ADR-148), and the Scope Authorization Engine (ADR-147) collectively ensure that when a decision is evaluated, the evaluation algorithm is correct, the scope is authorized, and no LLM artifacts contaminate the signal layer.

However, a deeper question remained unanswered: **What did the AI know at the exact moment it evaluated the decision — and was that knowledge defensible, uncontaminated, and within authorized bounds?**

A Decision Receipt proves:
> "This algorithm produced this decision on these inputs."

It does not prove:
> "These inputs were drawn from authorized sources, were fresh, were uncontaminated by injection, had not drifted from the calibration baseline, and were attested at the moment of evaluation."

This gap is the **context governance gap**. It is distinct from the decision governance gap (solved by ADR-028) and the scope governance gap (solved by ADR-147).

The analogy: a chain-of-custody form in forensic evidence. Not just "the DNA test was conducted correctly," but "this specific sample, from this specific source, at this specific time, with this chain of custody — and here is the signed attestation."

---

## Decision

Implement a **Memory Context Auditor** as `omnix_core/governance/memory_context_auditor.py` that:

1. **Captures a `ContextSnapshot`** before any governance evaluation — an immutable, hashable record of the complete AI context window (signals, history depth, external data sources, signal age, domain metadata, active scope).

2. **Detects contamination** across five independent layers:
   - **Signal Layer** — forbidden LLM artifact keys, non-numeric values, NaN/Inf guards
   - **Freshness Guard** — signal age exceeding `MAX_SIGNAL_AGE_SECONDS` (default: 300s)
   - **History Guard** — context history exceeding `MAX_AUTHORIZED_HISTORY_DEPTH` (default: 10)
   - **Source Guard** — unauthorized external data sources (not in `_AUTHORIZED_DATA_SOURCES`)
   - **Injection Guard** — prompt injection patterns in domain metadata

3. **Computes context drift** from an authorized baseline using AVM canonical signal weights (ADR-076). Drift amplified 1.4× when `risk_exposure` is rising (directional danger signal).

4. **Generates a `MemoryAttestationRecord` (MAR)** — PQC-signed (Dilithium-3 / NIST FIPS 204) record attesting the full context state. Fallback to SHA-256 in degraded mode (logged as WARNING).

5. **Embeds `mar_id`** in every Decision Receipt as `memory_attestation_id` — creating a permanent bidirectional audit chain:
   ```
   Decision Receipt ←→ Memory Attestation Record
   ```

6. **Fails closed on CRITICAL contamination** — `ContextIntegrityError` is raised, blocking the governance evaluation. This is the same principle as ADR-028 INV-001.

7. **Exposes `verify_mar()`** — independent verification path requiring no DB access, only the MAR itself and the embedded public key. Mirrors the receipt self-verification property (ADR-085).

---

## Contamination Classification

| Class | Meaning | Pipeline Action |
|---|---|---|
| `CLEAN` | No contamination detected | Evaluate normally |
| `SUSPICIOUS` | Anomalies detected (stale signals, excessive history) | Evaluate with `trust_flags.context_suspicious = True` |
| `CONTAMINATED` | Active contamination (unauthorized sources, non-numeric values) | Restricted evaluation, Tier 1 escalation |
| `CRITICAL` | Injection detected, NaN/Inf, or forbidden LLM keys | Pipeline BLOCKED — `ContextIntegrityError` raised |

---

## Architecture Position

```
[External Data Sources / Signal Feeds / History]
            │
            ▼
MemoryContextAuditor.capture_snapshot()   ← ADR-151: context captured here
            │
            ├─→ detect_contamination()    ← 5 independent detection layers
            ├─→ detect_drift()            ← weighted L1 vs. authorized baseline
            └─→ generate_mar()            ← PQC-signed Memory Attestation Record
            │
            ▼
[LLMIsolationBoundary.form_packet()]      ← ADR-148: structural signal separation
            │
            ▼
[11-Checkpoint Pipeline]                  ← ADR-028: decision evaluation
            │
            ▼
[DecisionReceiptEngine]                   ← receipt + memory_attestation_id embedded
```

---

## MemoryAttestationRecord (MAR) Schema

| Field | Type | Description |
|---|---|---|
| `mar_id` | string | `OMNIX-MAR-{12hex}` — globally unique |
| `decision_id` | string? | Links to governance decision receipt |
| `domain` | string | Governance domain |
| `asset` | string | Asset or case identifier |
| `snapshot` | object | Full `ContextSnapshot` (signals, history, sources, hashes) |
| `contamination_flags` | array | All detected contamination events |
| `contamination_class` | enum | Worst-case: CLEAN / SUSPICIOUS / CONTAMINATED / CRITICAL |
| `drift_assessment` | object | Quantified drift from baseline |
| `integrity_verdict` | string | Human-readable attestation statement |
| `content_hash` | string | SHA-256 of canonical MAR content (pre-signature) |
| `pqc_signature` | string | Base64 Dilithium-3 signature |
| `public_key` | string | Base64 public key (embedded — self-verifying) |
| `signing_algorithm` | string | `Dilithium-3 (NIST FIPS 204)` or `sha256-degraded` |
| `generated_at` | string | ISO-8601 UTC |
| `adr_reference` | string | `ADR-151` |

---

## Context Snapshot Schema

| Field | Type | Description |
|---|---|---|
| `snapshot_id` | string | `OMNIX-CTX-{12hex}` |
| `captured_at` | string | ISO-8601 UTC — exact moment of context capture |
| `context_keys` | array | Manifest of ContextKey categories present |
| `signals` | object | Exact numeric signals entering governance |
| `signal_fingerprint` | string | SHA-256 of canonical signals dict |
| `history_depth` | int | Number of prior decisions in context window |
| `history_fingerprint` | string? | SHA-256 of decision history content |
| `external_sources` | array | Data sources consulted (type, id, age, data_hash) |
| `signal_age_s` | float | Age of signals at capture time (seconds) |
| `domain_metadata` | object | Domain-specific context (applicant_type, strategy, etc.) |
| `scope_id` | string? | Active Scope Authorization ID (ADR-147) |
| `context_hash` | string | SHA-256 of full canonical context (integrity anchor) |

---

## Authorized External Data Sources

The following source categories are authorized for governance context:

`market_feed`, `credit_bureau`, `aml_database`, `regulatory_registry`,
`historical_receipts`, `calibration_snapshot`, `fraud_intelligence`,
`jurisdiction_registry`, `sharia_authority`, `actuarial_table`,
`energy_grid_feed`, `property_registry`, `defense_intelligence`,
`stablecoin_reserve_feed`, `health_records_anonymized`,
`robotics_sensor_feed`, `agent_intent_feed`, `internal_signals`

Any source not in this list is flagged `CONTAMINATED` and triggers Tier 1 escalation.

---

## Context Drift Computation

Uses AVM canonical signal weights (ADR-076) for consistency across governance layers:

| Signal | Weight |
|---|---|
| `probability_score` | 0.25 |
| `signal_coherence` | 0.25 |
| `risk_exposure` | 0.20 |
| `stress_resilience` | 0.15 |
| `trend_persistence` | 0.10 |
| `logic_consistency` | 0.05 |

**Drift amplification:** If `risk_exposure` is rising above baseline, drift score is multiplied by 1.4× (directional danger signal, consistent with AVM ADR-074).

| Drift Score | Verdict |
|---|---|
| < 15% | NEGLIGIBLE |
| 15–30% | MODERATE |
| 30–70% | SIGNIFICANT |
| > 70% | CRITICAL |

---

## Database Table

```sql
CREATE TABLE IF NOT EXISTS memory_attestation_records (
    mar_id              VARCHAR(64)  PRIMARY KEY,
    decision_id         VARCHAR(64),
    domain              VARCHAR(64)  NOT NULL,
    asset               VARCHAR(128) NOT NULL,
    snapshot_id         VARCHAR(64)  NOT NULL,
    context_hash        VARCHAR(64)  NOT NULL,
    signal_fingerprint  VARCHAR(64)  NOT NULL,
    contamination_class VARCHAR(32)  NOT NULL,
    drift_score         FLOAT        NOT NULL DEFAULT 0.0,
    drift_verdict       VARCHAR(32)  NOT NULL,
    flags_count         INTEGER      NOT NULL DEFAULT 0,
    contamination_flags JSONB,
    drift_assessment    JSONB,
    integrity_verdict   TEXT,
    content_hash        VARCHAR(64)  NOT NULL,
    pqc_signature       TEXT,
    public_key          TEXT,
    signing_algorithm   VARCHAR(128),
    generated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    adr_reference       VARCHAR(16)  NOT NULL DEFAULT 'ADR-151'
);

CREATE INDEX IF NOT EXISTS idx_mar_decision_id   ON memory_attestation_records (decision_id);
CREATE INDEX IF NOT EXISTS idx_mar_domain_ts     ON memory_attestation_records (domain, generated_at);
CREATE INDEX IF NOT EXISTS idx_mar_contamination ON memory_attestation_records (contamination_class, generated_at);
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OMNIX_MAX_CONTEXT_HISTORY` | `10` | Max authorized decision history depth |
| `OMNIX_CONTEXT_DRIFT_THRESHOLD` | `30.0` | Drift % triggering SIGNIFICANT verdict |
| `OMNIX_CONTEXT_CRITICAL_THRESHOLD` | `70.0` | Drift % triggering CRITICAL verdict |
| `OMNIX_MAX_SIGNAL_AGE_SECONDS` | `300` | Max signal freshness (5 minutes) |

**Security note:** `OMNIX_CONTEXT_CRITICAL_THRESHOLD` must never be set above 90% in production — doing so would allow severely contaminated contexts to pass as SIGNIFICANT rather than CRITICAL. Treat as a security parameter.

---

## Consequences

### Positive

- **Closes context governance gap:** Every governance decision now has a signed attestation of what the AI knew — not just what it decided.
- **Bidirectional audit chain:** `receipt_id ↔ mar_id` enables regulators and auditors to trace from receipt to context state and back.
- **Independent verification:** `verify_mar()` requires only the MAR itself — no server, no DB, no OMNIX infrastructure.
- **Defense in depth:** Five independent contamination detection layers — no single layer failure creates a gap.
- **Injection detection:** Explicit prompt injection guard in domain metadata layer.
- **Consistent with AVM:** Uses identical signal weights (ADR-076) — drift scores are directly comparable across governance layers.
- **Self-verifying:** Public key embedded in every MAR — same property as decision receipts (ADR-085).

### Negative

- **Performance overhead:** `capture_snapshot()` + `detect_contamination()` + `detect_drift()` adds ~2–5ms per evaluation. Within the <50ms pipeline budget.
- **New DB table:** `memory_attestation_records` — idempotent DDL, created on first call.
- **Caller migration:** Governance callers must now call `audit_context()` before pipeline entry. Existing callers without context data get CLEAN MAR with no sources (safe default).
- **Baseline requirement:** `detect_drift()` requires a baseline to be meaningful. Without a baseline, drift returns NEGLIGIBLE. AVM calibration snapshots (ADR-074) serve as the natural baseline source.

---

## Integration Notes

### Minimum Integration (one call)

```python
from omnix_core.governance.memory_context_auditor import audit_context

mar = audit_context(
    signals={"probability_score": 72, "risk_exposure": 45, ...},
    domain="trading",
    asset="BTC/USD",
    signal_age_s=8.3,
)
# mar.mar_id → embed in Decision Receipt as memory_attestation_id
```

### Full Integration (explicit control)

```python
from omnix_core.governance.memory_context_auditor import (
    get_memory_context_auditor, ExternalDataSource
)

auditor = get_memory_context_auditor()

snapshot = auditor.capture_snapshot(
    signals=signals,
    domain="trading",
    asset="BTC/USD",
    history_depth=3,
    external_sources=[
        ExternalDataSource("market_feed", "binance_l2",
                          queried_at=now_iso, data_age_s=2.1, authorized=True),
    ],
    scope_id="SAR-XXXXXXXXXXXX",
)

flags  = auditor.detect_contamination(snapshot)
drift  = auditor.detect_drift(snapshot, baseline_signals=avm_baseline)
mar    = auditor.generate_mar(snapshot, flags, drift, decision_id=receipt_id)
```

### Decision Receipt Enhancement

```python
receipt["memory_attestation_id"] = mar.mar_id
receipt["context_contamination"] = mar.contamination_class
receipt["context_drift_score"]   = mar.drift_assessment["drift_score"]
```

### Independent Verification

```python
from omnix_core.governance.memory_context_auditor import MemoryContextAuditor

auditor = MemoryContextAuditor()
valid = auditor.verify_mar(mar)  # True/False — no DB required
```

---

## Operational Monitoring

```python
from omnix_core.governance.memory_context_auditor import get_mar_stats, get_mar_log

stats = get_mar_stats()
# {
#   "total_mars": 142000,
#   "by_contamination": {"CLEAN": 141890, "SUSPICIOUS": 98, "CONTAMINATED": 11, "CRITICAL": 1},
#   "avg_drift_score": 4.2,
#   "clean_rate": 0.9993,
#   "critical_rate": 0.000007,
# }
```

---

*OMNIX QUANTUM — Decision Governance Infrastructure*  
*ADR-151 · Memory Context Governance · omnixquantum.net*
