# ADR-111 — Governance Pipeline Distributed Tracing

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-24 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` · `omnix_core/governance/` |
| **Replaces** | — |

---

## Context

When a governance decision arrived with an unexpected outcome (BLOCKED when APPROVED was expected, or vice versa), diagnosing the cause required manual log tracing across multiple modules (SAE → AVM → coherence gate → AML gate → fraud gate → jurisdiction gate → PQC signing), each logging independently with different formats.

This made root-cause analysis slow and error-prone, particularly for:
- Post-incident reviews after a client dispute
- Validating that a threshold change (ADR-037) had the intended effect
- Debugging AVM recalibration impact on live decisions

## Decision

Assign a `trace_id` to every governance evaluation and thread it through every pipeline stage.

### Trace ID generation

```python
trace_id = f"TRACE-{domain[:3].upper()}-{uuid4().hex[:12].upper()}"
# Example: TRACE-TRD-A1B2C3D4E5F6
```

### Pipeline trace record

Each checkpoint appends its result to the trace:

```python
trace.add(
    checkpoint="aml_gate",
    result="PASS",
    duration_ms=4.2,
    signals_evaluated=["tx_volume", "privacy_coin_flag"],
    reason=None  # populated if HOLD or BLOCK
)
```

### Trace storage

The complete trace is stored in `governance_pipeline_traces` (JSONB column) alongside the receipt. TTL: 90 days (matching WARM storage tier in ADR-126).

### Trace retrieval API

```
GET /api/governance/trace/<trace_id>
Authorization: Bearer <api_key>   (ADMIN role)
```

Returns the full pipeline execution trace with per-checkpoint timing, signal values, and decision rationale.

### Decision receipt linkage

Every `decision_receipt` includes a `trace_id` field, allowing auditors to pull the full pipeline trace for any receipt during a compliance review.

## Consequences

**Positive:**
- Root-cause analysis time reduced from ~30 minutes to ~30 seconds.
- Auditors can prove exactly which checkpoint blocked a decision and why.
- Threshold tuning becomes data-driven: compare traces before and after a threshold change.

**Negative:**
- Trace storage adds ~2–5KB per decision to JSONB column.
- Trace retrieval requires ADMIN role — client-facing trace access would require a separate sanitized view.

## Related

- ADR-104: Governance Telemetry Pipeline
- ADR-106: Governance Audit Export
- ADR-116: Fail-Closed Enforcement Policy
