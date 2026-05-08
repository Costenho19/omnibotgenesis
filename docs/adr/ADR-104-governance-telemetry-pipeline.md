# ADR-104 — Governance Telemetry Pipeline

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-21 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_core/governance/` · `omnix_services/ai_service/` |
| **Replaces** | — |

---

## Context

Governance decisions and pipeline metrics were logged to Python's standard `logging` module. This worked for debugging but provided no structured, queryable telemetry. Key operational questions could not be answered without manual log parsing:

- What is the average pipeline latency per domain over the last 24 hours?
- Which checkpoint is responsible for the most HOLD decisions?
- Which AI model (primary/fallback) is being used and at what rate?
- How many decisions per hour are reaching the PQC signing step?

## Decision

Implement a structured telemetry pipeline that emits governance decision metadata to a `governance_telemetry` table after every evaluation.

### Schema

```sql
CREATE TABLE IF NOT EXISTS governance_telemetry (
    id              SERIAL PRIMARY KEY,
    decision_id     TEXT NOT NULL,
    domain          TEXT NOT NULL,
    outcome         TEXT NOT NULL,  -- APPROVED, BLOCKED, HOLD
    pipeline_ms     INTEGER,        -- total pipeline latency
    checkpoint_ms   JSONB,          -- per-checkpoint latency breakdown
    ai_model_used   TEXT,           -- primary or fallback model name
    avm_score       FLOAT,
    coherence_score FLOAT,
    blocking_reason TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_gt_domain_ts ON governance_telemetry (domain, created_at DESC);
```

### Telemetry emitter

Telemetry write is best-effort and non-blocking — a failure to write telemetry must never affect the governance decision outcome.

```python
try:
    emit_telemetry(decision_id=..., domain=..., outcome=..., pipeline_ms=...)
except Exception:
    logger.warning("[TELEMETRY] Failed to emit — non-critical")
```

## Consequences

**Positive:**
- Operational dashboards can answer latency, throughput, and model usage questions in real time.
- Per-checkpoint latency breakdown enables targeted optimization of slow pipeline stages.

**Negative:**
- Telemetry table grows at ~1 row per governance decision; requires periodic archival.

## Related

- ADR-127: Phase 3 Filter Calibration Metrics
- ADR-128: Phase 4 Calibration Insight Engine
- ADR-134: Governance Oscillation / Hesitation / Asymmetry
