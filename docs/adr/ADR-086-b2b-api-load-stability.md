# ADR-086 — B2B API Load Stability and Hardening

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-14 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` · `omnix_web/api/server.py` |
| **Replaces** | — |

---

## Context

Following the enterprise feature expansion (ADR-080, ADR-081, ADR-082–085), the B2B API endpoint was subjected to load testing ahead of the first institutional client onboarding. Testing revealed three instabilities under concurrent load:

1. **Connection pool exhaustion** — 50 concurrent governance requests exhausted the SQLAlchemy connection pool, causing 503 errors on the 51st request.
2. **Schema validation overhead at scale** — body-level validation (ADR-080) added acceptable latency (~0.2ms) per request but created a bottleneck when 20+ validation errors occurred simultaneously, each generating a DB write to the audit log.
3. **AVM snapshot contention** — concurrent requests to the same domain triggered simultaneous AVM snapshot reads, occasionally producing duplicate recalibration triggers.

## Decision

Three targeted fixes applied:

### 1. Connection pool configuration

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,   # evict stale connections
)
```

### 2. Validation error audit log — async best-effort

Validation error audit writes are moved to a background thread (fire-and-forget). A validation error that cannot be written to the audit log does not block the API response.

### 3. AVM snapshot read lock

A per-domain `threading.Lock` prevents concurrent snapshot reads from triggering duplicate recalibrations:

```python
_AVM_LOCKS: dict[str, threading.Lock] = defaultdict(threading.Lock)

def load_avm_snapshot(domain: str) -> AVMSnapshot:
    with _AVM_LOCKS[domain]:
        return bridge.load_snapshot(domain)
```

## Load Test Results (post-fix)

| Concurrent Requests | P50 Latency | P99 Latency | Error Rate |
|---|---|---|---|
| 10 | 42ms | 89ms | 0% |
| 50 | 67ms | 201ms | 0% |
| 100 | 112ms | 380ms | 0.3% (DB timeout, not governance error) |

## Consequences

**Positive:**
- B2B endpoint verified stable under realistic institutional load.
- No governance errors introduced by concurrency fixes.

**Negative:**
- Async audit writes mean a small window exists where a validation error is not yet persisted.

## Related

- ADR-080: Body-level Schema Validation
- ADR-081: Per-Client Quota Enforcement
- ADR-123: External API Security Hardening
