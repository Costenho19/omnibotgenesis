# ADR-081 — Per-Client Hard Quota Enforcement

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-11 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` · `omnix_web/api/omnix_engine/b2b_auth.py` |
| **Replaces** | — |

---

## Context

B2B clients on different pricing tiers consumed governance API resources without hard enforcement of their contracted limits. A client on a Starter plan (1,000 calls/day) could send 50,000 calls/day, generating infrastructure costs not covered by their contract and degrading service quality for other clients.

The existing per-client threshold system (ADR-037) handled *governance* thresholds (sensitivity, block rate) but did not enforce *API usage* quotas.

## Decision

Implement a hard quota enforcement layer applied to every authenticated API request after schema validation (ADR-080) and before pipeline entry.

### Quota schema (in `b2b_clients` table)

```sql
ALTER TABLE b2b_clients ADD COLUMN IF NOT EXISTS daily_quota   INTEGER DEFAULT 10000;
ALTER TABLE b2b_clients ADD COLUMN IF NOT EXISTS monthly_quota INTEGER DEFAULT 200000;
ALTER TABLE b2b_clients ADD COLUMN IF NOT EXISTS calls_today   INTEGER DEFAULT 0;
ALTER TABLE b2b_clients ADD COLUMN IF NOT EXISTS calls_month   INTEGER DEFAULT 0;
ALTER TABLE b2b_clients ADD COLUMN IF NOT EXISTS quota_reset_date DATE DEFAULT CURRENT_DATE;
```

### Enforcement logic

```python
# ADR-081 enforcement — runs on every governance API call
def enforce_quota(client: B2BClient) -> None:
    if client.calls_today >= client.daily_quota:
        raise QuotaExceededError("daily", client.daily_quota)
    if client.calls_month >= client.monthly_quota:
        raise QuotaExceededError("monthly", client.monthly_quota)
    client.increment_counters()
```

### Error response

```json
{
  "status": "QUOTA_EXCEEDED",
  "quota_type": "daily",
  "limit": 1000,
  "used": 1000,
  "resets_at": "2026-04-12T00:00:00Z",
  "adr": "ADR-081"
}
```

HTTP 429 is returned. Standard `Retry-After` header is included.

### Quota tiers (default)

| Plan | Daily | Monthly |
|---|---|---|
| Sandbox | 100 | 2,000 |
| Starter | 1,000 | 20,000 |
| Professional | 10,000 | 200,000 |
| Enterprise | Configurable | Configurable |

## Consequences

**Positive:**
- Infrastructure costs are bounded per client.
- Quota headers in responses allow clients to self-manage usage.
- Enforcement is auditable — every exceeded-quota event is logged with client ID and timestamp.

**Negative:**
- Quota reset logic requires a daily background job or lazy reset on first call of the day.
- Edge case: clock skew between Railway containers could cause minor quota miscounting.

## Related

- ADR-037: Per-Client Configurable Governance Thresholds
- ADR-080: API Request Body Schema Validation
- ADR-123: External API Security Hardening
