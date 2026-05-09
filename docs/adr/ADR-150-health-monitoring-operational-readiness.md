# ADR-150 — Health Monitoring & Operational Readiness

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** None  
**Related:** ADR-012 (DB resilience), ISR-012 (WAL), OMNIX-BASELINE-2026-Q2-001

---

## Context

OMNIX QUANTUM has reached architectural maturity (149 ADRs, 10 governance invariants, ISR remediations complete). The primary risk is no longer functional correctness — it is **operational resilience**: what happens at 3am when the DB goes down, when WAL accumulates, or when PQC keys are absent.

No structured health monitoring infrastructure existed. Monitoring was ad-hoc and relied on Railway's default crash detection. There were no liveness/readiness probes, no structured Telegram operational alerts, and no WAL reconciliation endpoint.

---

## Decision

Implement a dedicated Operational Readiness Layer (`omnix_core/ops/`) with three components:

### 1. Health Check Engine (`omnix_core/ops/health_check.py`)

Deep probes of 6 subsystems:

| Subsystem | Critical | What is checked |
|---|---|---|
| `database` | ✅ | psycopg2 connect + `SELECT COUNT(*) FROM decision_receipts` |
| `redis` | ❌ | ping + SET/GET round-trip with random probe value |
| `pqc_dilithium3` | ❌ | sign + verify cycle with test payload |
| `receipt_wal` | ❌ | pending WAL entries count |
| `avm` | ❌ | `get_avm_instance("health-probe").get_current_weights()` |
| `governance_engine` | ✅ | ExternalEvaluator + DecisionReceiptEngine importable |

**Overall status** = worst-case of all **critical** subsystems.

Each probe returns `{name, status, latency_ms, detail, critical}`.

### 2. Operational Alert Dispatcher (`omnix_core/ops/operational_alerts.py`)

- `alert_critical()`, `alert_warning()`, `alert_info()`, `alert_recovery()`
- Sends HTML-formatted Telegram messages to `TELEGRAM_ADMIN_USER_ID`
- 5-minute cooldown per (subsystem, level) pair to prevent alert flooding
- Non-blocking — failure to send never propagates to callers
- `evaluate_health_and_alert(report)` — called from `/api/health`
- `alert_startup()` — called on server initialization

### 3. Health Blueprint (`omnix_web/api/health_blueprint.py`)

| Endpoint | Purpose | Auth |
|---|---|---|
| `GET /api/health` | Full subsystem report + optional alert dispatch | None (public) |
| `GET /api/health/live` | Liveness probe — always 200 if process alive | None |
| `GET /api/health/ready` | Readiness probe — 503 if DB or engine DOWN | None |
| `POST /api/health/reconcile-wal` | Flush WAL receipts to DB after recovery | ADMIN_ALLOWED_IPS or X-Admin-Token |

---

## Response Contract

`GET /api/health` returns:

```json
{
  "status": "UP",
  "timestamp_utc": "2026-05-09T12:00:00+00:00",
  "version": "6.6.0",
  "governance_baseline": "OMNIX-BASELINE-2026-Q2-001",
  "uptime_seconds": 3600.0,
  "wal_pending": 0,
  "adr_count": 150,
  "pqc_mode": "dilithium3-persistent",
  "subsystems": [
    { "name": "database", "status": "UP", "latency_ms": 12.4, "detail": "decision_receipts accessible — 4,821 rows", "critical": true },
    { "name": "redis", "status": "UP", "latency_ms": 2.1, "detail": "SET/GET round-trip verified", "critical": false },
    ...
  ]
}
```

---

## Consequences

**Positive:**
- Railway health checks can use `/api/health/live` (liveness) and `/api/health/ready` (readiness) instead of the generic ping.
- Operational failures trigger immediate Telegram alerts — no more silent 3am outages.
- WAL reconciliation is a documented, authorized, single-command recovery procedure.
- External uptime monitors (UptimeRobot, Better Stack) can hit `/api/health/live` with no auth.

**Negative:**
- Each `/api/health` call runs 6 DB/Redis probes — not suitable for high-frequency polling (use `/api/health/live` for that).
- Alert cooldown means a persistent outage only sends one alert per 5 minutes — intentional.

---

## Implementation Notes

- `omnix_core/ops/` is a new module directory. It does **not** touch any `core-frozen` module.
- Health checks are additive — they observe subsystems but never modify them.
- The reconcile-wal endpoint requires `ADMIN_ALLOWED_IPS` or `ADMIN_TOKEN` env var — never exposed publicly.
- `?alerts=false` query parameter suppresses alert dispatch for monitoring-only calls (e.g. uptime monitors that ping every 30 seconds).
