# ADR-087 — Webhook Delivery Hardening

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-15 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` · `omnix_web/api/omnix_engine/webhook_engine.py` |
| **Replaces** | — |

---

## Context

The webhook system introduced in ADR-053 delivered governance event notifications to registered client endpoints. Post-launch monitoring identified reliability gaps:

1. **No retry logic** — if the client endpoint returned a 5xx, the event was silently dropped.
2. **No HMAC signing** — webhook payloads were unsigned; a MITM attacker could forge governance events to a client's endpoint.
3. **No delivery log** — clients had no visibility into which events were delivered, failed, or retried.
4. **Synchronous delivery** — webhook HTTP calls happened inline with the governance response, adding 200–800ms to every governance API call.

## Decision

### 1. Exponential backoff retry

Webhook delivery attempts with exponential backoff: attempts at T+0, T+30s, T+5min, T+30min, T+2h. After 5 failures, the event is marked `PERMANENTLY_FAILED` and the webhook admin is notified.

### 2. HMAC-SHA256 signing

Every webhook payload is signed with a per-client `WEBHOOK_SECRET`:

```
X-OMNIX-Signature: sha256=<hmac_hex>
X-OMNIX-Timestamp: <unix_epoch>
```

Clients verify: `HMAC-SHA256(secret, timestamp + "." + body)`.

### 3. Delivery log table

```sql
CREATE TABLE webhook_delivery_log (
    id          SERIAL PRIMARY KEY,
    client_id   TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    payload     JSONB NOT NULL,
    status      TEXT DEFAULT 'PENDING',
    attempts    INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    delivered_at    TIMESTAMPTZ,
    error_detail    TEXT
);
```

### 4. Async delivery via background thread

Webhook delivery is decoupled from the governance response path. The governance API responds immediately; delivery happens in a background thread pool.

## Consequences

**Positive:**
- Clients reliably receive governance events even through temporary outages.
- HMAC signing allows clients to reject forged events.
- Delivery log provides an audit trail for both OMNIX and client debugging.

**Negative:**
- Background thread pool adds memory overhead (~8 threads per worker process).
- PERMANENTLY_FAILED events require manual re-delivery or client re-registration.

## Related

- ADR-053: Trajectory Invariant Enforcement (webhook system origin)
- ADR-086: B2B API Load Stability
- ADR-123: External API Security Hardening
