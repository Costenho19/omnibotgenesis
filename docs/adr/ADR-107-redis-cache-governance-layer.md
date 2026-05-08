# ADR-107 — Redis Cache Layer for Governance Responses

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-22 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_core/cache/redis_cache.py` · `omnix_web/api/gov_blueprint.py` |
| **Replaces** | — |

---

## Context

Governance evaluation for identical inputs (same asset, domain, jurisdiction, operation, market conditions) produced identical outputs, yet every duplicate request executed the full 11-checkpoint pipeline (~80–200ms). Dashboard widgets refreshing every 10 seconds triggered duplicate evaluations for the same active positions, consuming unnecessary compute and AI model quota.

## Decision

Add a Redis-backed response cache for governance evaluation results with a configurable TTL.

### Cache key structure

```
omnix:gov:{domain}:{asset}:{jurisdiction}:{operation}:{signal_fingerprint}
```

`signal_fingerprint` = SHA-256 of the normalized signal inputs (rounded to 2 decimal places to absorb minor floating-point noise).

### TTL policy

| Domain | Default TTL | Rationale |
|---|---|---|
| Trading | 30 seconds | Market conditions change rapidly |
| Credit | 300 seconds | Credit scores change slowly |
| Insurance | 600 seconds | Risk profiles stable over minutes |
| Defense | 0 (no cache) | Every decision must be evaluated live |
| All others | 120 seconds | General default |

### Cache bypass

Requests with `X-OMNIX-No-Cache: true` header bypass the cache and always execute the full pipeline. Admin and WRITE+ roles only.

### Cache invalidation

AVM recalibration events (ADR-120) flush all cached entries for the affected domain to prevent stale governance decisions after threshold changes.

### Hit/miss telemetry

Cache hit/miss ratio reported in the governance telemetry table (ADR-104) for performance monitoring.

## Consequences

**Positive:**
- Repeat dashboard queries resolved in ~2ms (cache hit) vs. ~150ms (full pipeline).
- AI model quota consumption reduced by an estimated 40–60% for dashboard-driven traffic.

**Negative:**
- Defense domain cannot use cache (by design).
- Cache adds a dependency on Redis availability; cache misses on Redis failure gracefully fall through to full evaluation.

## Related

- ADR-076: Anti-Replay Guard (Redis also used here — shared connection pool)
- ADR-104: Governance Telemetry Pipeline
- ADR-120: AVM Auto-Recalibration
