# ADR-061: Persistent IP Blocklist

**Status:** Accepted  
**Date:** 2026-04-07  
**Author:** Harold Nunes  

## Context

OMNIX's governance API (ADR-028) had two security gaps in its rate-limiting and abuse-prevention layer:

1. **In-memory only**: Both `_brute_force_store` and `_rate_limit_store` live in process memory. On every Railway deployment or server restart, all active lockouts are lost. An attacker can trigger a restart (or simply wait for one) to reset their lockout window.

2. **No persistent IP blocklist**: There was no mechanism to permanently (or time-bounded) ban an IP that repeatedly abused the rate limiter. An attacker could hammer the endpoint 10 times, wait 60 seconds, and repeat indefinitely without consequence.

## Decision

Implement a **DB-backed IP blocklist** in `omnix_web/api/gov_blueprint.py` that:

1. Persists bans to a `blocked_ips` PostgreSQL table — survives restarts and deployments.
2. Uses a **30-second in-memory cache** to avoid a DB hit on every request (thread-safe, under `threading.Lock`).
3. **Auto-bans** any IP that triggers the rate limiter 3+ times within 10 minutes — duration: 1 hour.
4. **Notifies Harold via Telegram** when an IP is auto-banned (reuses `_notify_harold_telegram`).
5. Checks the blocklist at **two enforcement points**: `_require_auth()` (auth layer) and `api_governance_evaluate()` (evaluation layer) — before brute-force and rate-limit checks.

The existing `_brute_force_store` (in-memory, 15-minute lockout after 5 failed auth attempts) is kept intact — the new DB blocklist is an additional layer on top.

## Schema

```sql
CREATE TABLE IF NOT EXISTS blocked_ips (
    ip               VARCHAR(64)  PRIMARY KEY,
    blocked_until    TIMESTAMPTZ  NOT NULL,
    reason           TEXT,
    violation_count  INTEGER      NOT NULL DEFAULT 1,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_blocked_ips_until ON blocked_ips(blocked_until);
```

Table is created lazily on first use via `_ensure_blocked_ips_table()`. No migration required.

## Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `_BLOCKLIST_CACHE_TTL` | 30s | In-memory cache refresh interval |
| `_IP_BAN_VIOLATION_MAX` | 3 | Rate-limit hits before auto-ban |
| `_IP_BAN_VIOLATION_WINDOW` | 600s (10 min) | Rolling window for violation counting |
| `_IP_BAN_DURATION` | 3600s (1 hour) | Duration of each auto-ban |

## Flow

```
Incoming request
  → _require_auth()
      → _is_ip_blocked(ip)          ← DB-backed (30s cache)
          → 403 if blocked
      → _is_brute_force_locked(ip)  ← existing in-memory check
          → 429 if locked
      → authenticate_client(key)
  → api_governance_evaluate()
      → _is_ip_blocked(ip)          ← same cache, no extra DB hit
          → 403 if blocked
      → _is_rate_limited(ip)
          → if True: record violation
              → if violations ≥ 3 in 10 min: _auto_ban_ip() [daemon thread]
          → 429 if rate limited
      → pipeline evaluation
```

## Security Properties

- **Survives restarts**: Bans persist in PostgreSQL across all deployments.
- **Non-blocking**: `_auto_ban_ip()` runs in a daemon thread — never adds latency to the governance pipeline.
- **Fail-open cache**: If DB is unreachable during cache refresh, the existing cache is retained (no ban added, no ban removed).
- **Idempotent bans**: `INSERT ... ON CONFLICT DO UPDATE` — repeated violations extend the ban and increment the counter; no duplicates.
- **Complementary to brute-force**: Brute-force lockout (5 auth failures → 15 min, in-memory) remains unchanged. IP blocklist operates at a different layer (rate-limit abuse → 1 hour, DB-backed).

## Audit

Every ban event produces:
- A `WARNING` log entry: `[IP BLOCK] Auto-banned <ip> ...`
- A `blocked_ips` DB row with `reason`, `violation_count`, `created_at`, `updated_at`
- A Telegram notification to Harold (reuses `_notify_harold_telegram`)

## Files Modified

```
omnix_web/api/gov_blueprint.py
    — Constants: _blocked_ip_cache, _BLOCKLIST_CACHE_TTL, _IP_BAN_VIOLATION_MAX,
                 _IP_BAN_VIOLATION_WINDOW, _IP_BAN_DURATION, _ip_ban_violations,
                 _blocked_ips_table_ensured
    — Functions: _ensure_blocked_ips_table(), _refresh_blocked_ip_cache(),
                 _is_ip_blocked(), _auto_ban_ip()
    — Modified:  _is_rate_limited() → violation tracking + auto-ban trigger
    — Modified:  _require_auth() → _is_ip_blocked() check before brute-force
    — Modified:  api_governance_evaluate() → _is_ip_blocked() check before rate limit
docs/reference/adr/ADR-061-persistent-ip-blocklist.md
replit.md (Recent Fixes)
```

## Consequences

- Determined attackers hitting the rate limit 3+ times in 10 minutes are automatically removed from the pool for 1 hour, even after a server restart.
- Harold receives a Telegram alert for every auto-ban — visible abuse events.
- The `blocked_ips` table accumulates ban history — useful for forensics and investor security diligence.
- Legitimate clients accidentally triggering the rate limiter (e.g., a bug in a loop) will be auto-banned. The threshold (3 violations in 10 minutes) is conservative enough to avoid false positives for normal usage.
