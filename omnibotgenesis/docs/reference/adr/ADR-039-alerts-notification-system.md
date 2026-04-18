# ADR-039 — Alerts and Notification System

**Status**: IMPLEMENTED — March 12, 2026  
**Author**: Harold Nunes (Founder — OMNIX Quantum)  
**Tags**: B2B, alerts, notifications, retention, observability

---

## Context

B2B clients using the OMNIX governance API have no visibility into events between API calls. If a system is blocked or a high-risk score fires at 2am, the client only discovers it the next time they query the receipts endpoint.

Real-time alerts convert OMNIX from a passive API into an active governance partner — increasing client retention and reducing the time-to-response for high-risk events.

## Decision

Implement a configurable alert system with the following design:

### Alert Types

| Type | Trigger |
|------|---------|
| `decision_blocked` | Any HOLD/REJECT/VETO decision outcome |
| `high_risk_score` | Decision score ≥ configurable threshold (default: 80) |
| `checkpoint_veto` | Specific checkpoint(s) fire a veto |
| `all_decisions` | Every governance evaluation (verbose — for full audit streams) |
| `daily_summary` | Scheduled daily digest |

### Delivery Channels

| Channel | Mechanism |
|---------|-----------|
| `webhook` | HTTP POST to client-specified HTTPS URL |
| `email` | SMTP delivery (requires SMTP_HOST, SMTP_USER, SMTP_PASSWORD env vars) |

### Delivery Semantics

- **Best-effort**: delivery failures are logged but never block the governance response.
- **Asynchronous**: alerts fire in a daemon thread after `evaluate` returns — zero latency impact on the governance pipeline.
- **Webhook timeout**: 5 seconds (prevents slow client webhooks from blocking threads).
- **Record-everything**: every delivery attempt (success or failure) recorded in `alert_events`.
- **No automatic retry**: clients can inspect events and test re-delivery manually.

### Integration Point

Alerts are triggered from `governance.py` → `api_governance_evaluate()` after receipt generation, via `threading.Thread(target=trigger_alerts, ...)`. The governance response is never delayed by alert delivery.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/governance/alerts/config` | Get all alert configs |
| `PUT` | `/api/governance/alerts/config` | Create or update alert config |
| `DELETE` | `/api/governance/alerts/config/<id>` | Remove alert config |
| `GET` | `/api/governance/alerts/events` | Alert delivery history |
| `POST` | `/api/governance/alerts/test` | Send a test alert |

## Database Tables

```sql
alert_configs (
    id, alert_config_id, client_id, alert_type, channel,
    enabled, config, created_at, updated_at
    UNIQUE (client_id, alert_type, channel)
)

alert_events (
    id, event_id, alert_config_id, client_id, alert_type,
    channel, trigger_data, delivery_status,
    delivery_error, delivered_at, created_at
)
```

## Commercial Rationale

- **Retention**: clients who receive proactive alerts renew at higher rates.
- **Trust**: an alert at 2am saying "we blocked a high-risk decision" builds institutional confidence.
- **Enterprise requirement**: enterprise procurement teams require alerting as a baseline feature.
- **Differentiation**: positions OMNIX as active governance partner, not passive API.

## Files

- `omnix_dashboard/blueprints/governance_alerts.py` — Blueprint + trigger function
- `omnix_dashboard/blueprints/governance.py` — Alerts triggered post-evaluation
- `omnix_dashboard/blueprints/__init__.py` — Export added
- `omnix_dashboard/app.py` — Blueprint registered

## Email Configuration

Requires environment variables (optional — webhook works without these):
```
SMTP_HOST     — SMTP server hostname
SMTP_PORT     — SMTP port (default: 587)
SMTP_USER     — SMTP username
SMTP_PASSWORD — SMTP password
SMTP_FROM     — From address (defaults to SMTP_USER)
```

## Constraints

- Webhook URLs must start with `https://` — no plain HTTP.
- One config per `(client_id, alert_type, channel)` combination — upserted on PUT.
- Alert events are client-isolated — clients only see their own delivery history.
- `daily_summary` type stored but delivery requires an external scheduler (cron/Railway cron).
