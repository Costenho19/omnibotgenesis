# ADR-077: Anti-Replay Guard — Redis Backend (Phase 2)

**Status:** ACCEPTED  
**Date:** 2026-04-09  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Scope:** `omnix_core/evidence/anti_replay.py`  
**Supersedes:** ADR-076 Phase 1 scope limitation (extends, does not replace)

---

## Context

ADR-076 (Phase 1) established an in-process anti-replay store with documented limitations:
- Does not survive process restarts
- Does not protect across multiple worker instances

ADR-076 explicitly designed the Phase 2 upgrade path with the same public interface.
This ADR formalises the Phase 2 Redis implementation and the runtime policy model.

---

## Decision

Extend `AntiReplayStore` with an optional Redis backend, activated automatically
when `REDIS_URL` is present in the environment.

### Runtime Modes

`OMNIX_ANTI_REPLAY_MODE` environment variable controls behaviour when Redis is
configured but unavailable:

| Mode | Redis present + available | Redis present + fails | Redis absent |
|------|--------------------------|----------------------|--------------|
| `strict` | Redis enforced ✅ | Fail-closed — registration rejected ❌ | In-memory fallback ✅ |
| `best_effort` (default) | Redis enforced ✅ | In-memory fallback + WARNING ⚠️ | In-memory fallback ✅ |

**Rationale for `best_effort` as default:**  
The current single-dyno Railway deployment does not require `strict` mode.
For multi-instance deployments where replay guarantees are SLA-critical,
operators set `OMNIX_ANTI_REPLAY_MODE=strict` to prevent silent degradation.

### Redis Key Design

```
omnix:ar:{receipt_id}
```

Value: `"1"` (presence is the signal)  
TTL: `max(ttl_ms, MIN_WINDOW_MS)` milliseconds — set via `SET NX PX`

**Atomic semantics:**  
`SET key 1 NX PX ttl_ms` is atomic at the Redis level. No `WATCH`/`MULTI` required.
A return value of `None` means the key already existed → `ReplayDetected` raised.

### Interface

Public interface is unchanged (ADR-076 guarantee):

```python
from omnix_core.evidence.anti_replay import check_and_register, is_replay, get_store

check_and_register(receipt_id, ttl_ms=30_000)   # raises ReplayDetected on replay
is_replay(receipt_id)                            # bool, read-only advisory
get_store()                                      # AntiReplayStore singleton
```

No caller changes required.

---

## Consequences

### Positive
- Same receipt rejected across all running instances within TTL window
- Survives process restarts (Redis persists entries across dyno restarts)
- Thread-safe: Redis atomicity replaces threading.Lock for the critical path
- In-memory store retained as degraded-mode fallback

### Negative / Risks
- Redis single point of failure in `strict` mode — mitigated by Railway managed Redis
- Redis connection adds ~1ms latency to every `check_and_register()` call
- Large receipt volumes fill Redis keyspace; TTL expiry is automatic

### Telemetry
Every backend switch (Redis → in-memory) logs at WARNING level with reason.
Every capacity event (Redis or in-memory) logs at ERROR level.

---

## Tests

- `tests/test_anti_replay_phase2.py` — Redis mock-based tests
- ADR-076 tests (`test_K1` through `test_K21`) remain valid — in-memory path unchanged

---

## References

- ADR-076: Anti-Replay Guard Phase 1
- `omnix_core/evidence/anti_replay.py`
- `omnix_core/cache/redis_cache.py` — existing Redis infrastructure
