# ADR-198 — Governance Observability Layer (GOL)

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-27  
**Related:** ADR-184 (OGR), ADR-194 (MIVP), ADR-181/182/183 (BEV), ADR-196 (SVP), ADR-197 (SRP)  
**Implements:** `omnix_core/observability/metrics.py` — `GovernanceMetricsRegistry`

---

## Context

OMNIX activates six ATF layers simultaneously in every governance session. Each
layer produces cryptographic artifacts — BAR, CCS, CTCHC, MAS — with PQC signatures.
This is computationally expensive and latency-sensitive. Yet until now, **there is
no instrumentation layer that measures any of it.**

The system currently has:
- `DatabaseGateway.get_pool_stats()` — raw pool statistics (ADR-150 health check)
- `_telemetry_loop()` in `DatabaseGateway` — logs pool stats every 5 minutes
- Per-module `logger.info()` calls — unstructured, not queryable

What is missing:
- **Governance-phase latency:** how long does `start_session` spend in CTCHC genesis
  vs MIVP MBR creation vs DB write?
- **Per-session throughput:** turns-per-minute for active sessions
- **BEV layer costs:** BAR signing time, CCS computation time, CTCHC hash time
- **MIVP alignment score distribution:** what fraction of sessions reach MANDATE-BOUND
  vs MANDATE-ALIGNED vs UNCERTIFIED?
- **DB pool health correlation:** does pool pressure correlate with governance latency?
- **Error rate by psycopg class:** OperationalError vs IntegrityError vs PoolTimeout

**Why this matters for the EU AI Act and institutional buyers:**

Article 9 (Risk management) and Article 17 (Quality management) of the EU AI Act
require continuous monitoring of AI system performance. OMNIX sells governance
infrastructure to enterprises. The observability layer is not optional — it is
the evidence layer that proves the governance stack is performing to its advertised
SLOs.

**Competing approaches:**

- **Prometheus + Grafana**: generic metric collection. No governance semantics.
  Does not understand `session_id`, `mandate_tier`, or `chain_tip_hash`.
- **OpenTelemetry**: excellent for distributed tracing. No OMNIX-native concepts.
  Requires an external collector to be useful.
- **Datadog APM**: powerful but external, cloud-dependent. Cannot run offline for
  EU data-residency deployments. No OGR lifecycle awareness.

None of the above understand that a latency spike in `record_turn` may indicate a
CCS violation about to trigger an AGVP proactive veto. OMNIX observability must
be governance-native.

---

## Decision

Introduce the **OMNIX Governance Observability Layer (GOL)** — a zero-dependency,
governance-native metrics registry that is:

1. **Governance-aware:** every metric is bound to `session_id` and
   `governing_receipt_id`.
2. **Phase-granular:** separate latency histograms for BAR, CCS, CTCHC, MIVP,
   DB write, and total session lifecycle.
3. **Trust-tagged:** sessions carry their `mandate_tier` (MANDATE-BOUND /
   MANDATE-ALIGNED / UNCERTIFIED) in every exported snapshot.
4. **Audit-ready:** snapshot serializes to deterministic JSON, traceable offline.
5. **Zero external dependencies:** runs in Railway, offline, or in `TESTING=true`
   mode without any external collector.

### Architecture

```
omnix_core/observability/
├── __init__.py               — public API surface
└── metrics.py
      │
      ├── LatencyHistogram          — rolling window, p50/p95/p99 + min/max/mean
      ├── ErrorCounter              — typed psycopg error counters per class
      ├── DBPoolStatsAdapter        — wraps DatabaseGateway.get_pool_stats()
      ├── GovernanceSessionMetric   — per-session lifecycle record
      ├── GovernancePhaseTimer      — context manager for phase timing
      └── GovernanceMetricsRegistry — singleton, thread-safe
            ├── on_session_start()
            ├── on_turn_start() / on_turn_end()
            ├── on_session_close()
            ├── on_session_halt()
            ├── on_db_error()
            ├── observe_pool_stats()
            └── export_snapshot()  → MetricsSnapshot (JSON-serializable)
```

### GovernancePhaseTimer — Context Manager

```python
with registry.phase_timer(session_id, phase="CTCHC_HASH") as t:
    chain = ctchc.add_link(...)
# t.elapsed_ms is automatically recorded in the session's phase histogram
```

### MetricsSnapshot — Export Format

```json
{
  "snapshot_id": "SNAP-3F8A2C...",
  "captured_at": "2026-05-27T09:21:00Z",
  "window_seconds": 300,
  "sessions": {
    "total_started": 142,
    "total_closed": 138,
    "total_halted": 4,
    "active": 0,
    "mandate_tiers": {
      "MANDATE-BOUND": 89,
      "MANDATE-ALIGNED": 47,
      "UNCERTIFIED": 6
    }
  },
  "latency_ms": {
    "session_start_p50": 12.4,
    "session_start_p95": 38.1,
    "session_start_p99": 71.2,
    "turn_record_p50": 4.1,
    "turn_record_p95": 11.3,
    "turn_record_p99": 28.7,
    "ctchc_hash_p50": 0.8,
    "ctchc_hash_p95": 2.1,
    "mivp_mas_p50": 1.4,
    "mivp_mas_p95": 4.6,
    "bar_sign_p50": 5.2,
    "bar_sign_p95": 14.9
  },
  "db_pool": {
    "status": "active",
    "pool_size": 10,
    "pool_available": 7,
    "requests_waiting": 0,
    "avg_query_time_ms": 3.2
  },
  "errors": {
    "OperationalError": 0,
    "IntegrityError": 0,
    "PoolTimeout": 0,
    "ForeignKeyViolation": 0,
    "UniqueViolation": 0,
    "Other": 0
  },
  "throughput": {
    "sessions_per_minute": 28.4,
    "turns_per_minute": 214.7
  }
}
```

### Integration with GovernanceRuntime (ADR-184)

The GOL is **non-invasive** — it does not require changes to `governance_runtime.py`.
Integration is through explicit hook calls in calling code or via the
`@timed_phase` decorator:

```python
# Option A: explicit hooks (no OGR change needed)
registry = GovernanceMetricsRegistry.get_instance()
session = rt.start_session(...)
registry.on_session_start(session)
...
registry.on_session_close(session)

# Option B: decorator on OGR methods (future — ADR-184 amendment)
@registry.timed("session_start")
def start_session(self, ...):
    ...
```

---

## Invariants

### OBS-INV-001 — Complete Lifecycle Coverage
*Every OGR lifecycle event (start, turn, close, halt) MUST emit a metric event to
`GovernanceMetricsRegistry`. No lifecycle transition is unobserved.*

**Verification:** Test calls `start_session / record_turn / close_session` and asserts
`registry.sessions.total_started == 1`, `registry.sessions.total_closed == 1`.

### OBS-INV-002 — Phase-Granular Latency
*Latency MUST be captured separately for each ATF layer phase:
`BAR_SIGN`, `CCS_COMPUTE`, `CTCHC_HASH`, `MIVP_MAS`, `DB_WRITE`, `SESSION_TOTAL`.*

**Verification:** After one full session, all six phase histograms have at least
one sample. No phase is aggregated together.

### OBS-INV-003 — DB Pool Observability
*`observe_pool_stats()` MUST capture `pool_size`, `pool_available`,
`requests_waiting`, and `avg_query_time_ms` from `DatabaseGateway.get_pool_stats()`
without modification or interpolation.*

**Verification:** `pool_available + requests_waiting ≤ pool_size` at all times.
Any violation indicates pool accounting bug.

### OBS-INV-004 — Typed Error Classification
*All database errors MUST be classified into one of:
`OperationalError`, `IntegrityError`, `PoolTimeout`, `ForeignKeyViolation`,
`UniqueViolation`, `Other`. No error is silently discarded.*

**Verification:** Injecting each error type increments the correct counter.

### OBS-INV-005 — No PII in Labels
*No metric label, snapshot field, or histogram bucket contains user data, session
payload, governing receipt content, agent output text, or cryptographic keys.*

**Fields explicitly excluded from snapshots:** `chain_tip_hash`, `pqc_signature`,
`output_text`, `agent_id` (session count only, never the identifier itself),
`mandate_binding.constraints` content.

**Verification:** Snapshot JSON is scanned for patterns matching PQC key formats,
email patterns, and known session ID structures.

### OBS-INV-006 — Snapshot Traceability
*Every `MetricsSnapshot` carries a `snapshot_id` (UUID4) and `captured_at`
(ISO-8601 UTC). It is deterministic for the same input window and JSON-serializable
without precision loss.*

**Verification:** Two calls to `export_snapshot()` with no intervening events
produce identical JSON (modulo `captured_at`).

---

## Consequences

**Positive:**
- OMNIX can now demonstrate governance SLO compliance to institutional buyers
  with an exportable, auditable metrics artifact
- The observability layer feeds directly into soak checkpoints (SOAK-INV-007)
  and stress reports (STRESS-INV-008)
- Phase-granular latency makes it possible to isolate PQC signing cost from DB cost

**Negative:**
- The in-process registry is not replicated across Railway dynos — each dyno
  has its own registry instance
- Snapshot export is pull-based (no push to Prometheus/InfluxDB without additional adapter)

**Future work (not in this ADR):**
- Prometheus exposition format adapter (`/metrics` endpoint)
- Cross-dyno metric aggregation via Redis (complements ADR-150 health check)
- Automated SLO breach alert via Telegram admin channel

---

## Related Records

| Record | Type | Description |
|---|---|---|
| `omnix_core/observability/metrics.py` | Implementation | GOL module |
| `omnix_core/observability/__init__.py` | Public API | Export surface |
| ADR-150 (Health Check) | Related | DB pool health endpoint |
| ADR-196 (SVP) | Consumer | Stress tests use GOL timers |
| ADR-197 (SRP) | Consumer | Soak checkpoints include GOL snapshot |
