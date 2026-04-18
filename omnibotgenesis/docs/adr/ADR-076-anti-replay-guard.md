# ADR-076: Anti-Replay Guard — In-Process Nonce Store

**Status:** ACCEPTED (Phase 1 — single-instance)  
**Date:** 2026-04-09  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Scope:** `omnix_core/evidence/anti_replay.py`

---

## Context

Harold Nunes communicated to Naimat Khan (Velos) that OMNIX would implement
nonce-based anti-replay protection to prevent receipt reuse within TTL windows.

Prior state: a nonce was generated inside `transparency_chain.py` and stored as
part of each chain entry, but was never validated against a set of seen nonces.
The anti-replay was a decorative field, not an enforcement mechanism.

This ADR formalises the Phase 1 implementation and explicitly documents its scope,
its limits, and the roadmap to Phase 2.

---

## Decision

Implement `AntiReplayStore` in `omnix_core/evidence/anti_replay.py`:

- Thread-safe in-process dict: `{ receipt_id: expiry_epoch_ms }`
- `check_and_register(receipt_id, ttl_ms)` — atomic check + register under a single `threading.Lock`
- `MIN_WINDOW_MS = 30_000` — floor on all TTLs (receipts with short TTLs still protected for 30s minimum)
- `MAX_STORE_SIZE = 100_000` — hard cap to prevent unbounded memory growth under DDoS or misconfiguration
- Lazy purge of expired entries on every `check_and_register()` call
- Process-level singleton: `from omnix_core.evidence.anti_replay import check_and_register`

---

## Scope and Limits (MUST be communicated to integrators)

> **Anti-replay enforcement is currently scoped to a single running instance
> and in-memory nonce store. Protection is effective for same-instance replay
> attempts within the configured TTL window, but does not yet survive process
> restarts or multi-instance routing.**

This means:

| Scenario | Protected |
|----------|-----------|
| Same receipt submitted twice to same running instance | ✅ `ReplayDetected` raised |
| Same receipt submitted after process restart (within TTL) | ⚠️ Not protected — store was cleared |
| Same receipt submitted to a different worker instance | ❌ Not protected — each worker has its own store |
| Receipt TTL shorter than MIN_WINDOW_MS (30s) | ✅ Effective window is always ≥ 30s |

**This is not a bug. It is a documented scope boundary.**
The system must not be advertised as global or persistent anti-replay until Phase 2.

---

## TTL Floor — MIN_WINDOW_MS

All TTL windows are floored at `MIN_WINDOW_MS = 30_000 ms`:

```python
window_ms = max(ttl_ms, MIN_WINDOW_MS)
```

**Rationale:** A receipt with `ttl_ms=1` would expire almost immediately, creating
a de-facto replay window with zero protection. Malformed or adversarially short
TTLs are caught by this floor. The effective window is always at least 30 seconds.

**Test coverage:** `test_K18_min_window_enforced_when_ttl_too_short`,
`test_K21_effective_window_is_min_window_when_ttl_shorter`.

---

## Consequences (Phase 1)

- **Positive:** Anti-replay is no longer a phantom feature — it raises `ReplayDetected` on actual replays.
- **Positive:** Thread-safe under concurrent load (100-thread race test: exactly 1 winner).
- **Positive:** Interface is stable — Phase 2 Redis swap requires no caller changes.
- **Neutral:** Single-instance scope is sufficient for current Railway single-dyno deployment.
- **Risk:** If Railway scales to multiple dynos without Phase 2 implementation, the anti-replay guarantee degrades silently. Mitigation: document in contract with Naimat; add a startup warning log if `RAILWAY_REPLICA_ID` is set and Redis is not configured.

---

## Phase 2 Roadmap — Redis Backend

When Railway scales beyond one dyno, or when the SLA requires restart-safe anti-replay:

```python
# Phase 2 — same interface, Redis backend
import redis as _redis

_redis_client = _redis.Redis.from_url(os.environ["REDIS_URL"])

def check_and_register(receipt_id: str, ttl_ms: int = MIN_WINDOW_MS) -> None:
    window_ms = max(ttl_ms, MIN_WINDOW_MS)
    registered = _redis_client.set(receipt_id, "1", px=window_ms, nx=True)
    if not registered:
        raise ReplayDetected(f"REPLAY_DETECTED receipt_id={receipt_id}")
```

One `SET NX PX` command. Atomic at Redis level. No caller changes required.

Triggers for Phase 2:
- Railway scaling to > 1 dyno
- Client contract requiring "persistent anti-replay" SLA
- Naimat / Velos requiring cross-restart enforcement

---

## Contract language for Naimat (Velos integration)

> OMNIX anti-replay guard (Phase 1) prevents same-instance receipt reuse within
> a minimum 30-second window. This protection is effective for the current
> single-instance Railway deployment. Phase 2 will extend this to persistent,
> multi-instance coverage via Redis backend. Integrators must not submit the same
> `receipt_id` twice within its `ttl_epoch_ms` window — the second submission
> will be rejected with `ReplayDetected`.

---

## Tests

- `test_K1` through `test_K20` in `tests/test_forensic_audit_ronda4.py`
- `test_K21_effective_window_is_min_window_when_ttl_shorter` — explicit proof of MIN_WINDOW_MS floor

---

## References

- ADR-075: Non-Finite Signal Guard (same audit round)
- ADR-074: Enterprise Governance Baseline
- `omnix_core/evidence/anti_replay.py`
- Forensic Audit Ronda 4 — OMNIX QUANTUM LTD, 2026-04-09
