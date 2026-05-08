# ADR-110 — Governance System Health Endpoint

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-24 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` · `omnix_web/api/server.py` |
| **Replaces** | — |

---

## Context

Railway deployment health checks used a simple HTTP 200 ping against `/`. This did not verify whether the governance engine was actually operational — the web server could be up while the database connection was broken, Redis was unreachable, PQC keys were missing, or AVM baselines had not loaded.

This caused Railway to report the service as healthy during incidents where governance decisions would fail or degrade. Operators had no single endpoint to check the full system health before routing traffic.

## Decision

Implement a structured health endpoint at `GET /api/health` that checks all critical dependencies.

### Health check components

| Component | Check | Failure impact |
|---|---|---|
| Database | `SELECT 1` | CRITICAL — governance fails |
| Redis | `PING` | DEGRADED — anti-replay disabled |
| PQC signing keys | key loaded and valid | CRITICAL — receipts unsigned |
| AVM baselines | ≥1 domain loaded | DEGRADED — uncalibrated defaults |
| UDCL pillars | all 8 importable | CRITICAL — pipeline incomplete |

### Response format

```json
{
  "status": "HEALTHY" | "DEGRADED" | "UNHEALTHY",
  "components": {
    "database": { "status": "UP", "latency_ms": 4 },
    "redis": { "status": "UP", "latency_ms": 1 },
    "pqc_keys": { "status": "UP", "key_id": "8b1b2b64873056a0" },
    "avm_baselines": { "status": "UP", "domains_loaded": 11 },
    "udcl_pillars": { "status": "UP", "pillars_healthy": 8 }
  },
  "version": "6.0.0",
  "uptime_seconds": 3847
}
```

### HTTP status mapping

- `HEALTHY` → HTTP 200
- `DEGRADED` → HTTP 200 (with warning — Railway keeps routing)
- `UNHEALTHY` → HTTP 503 (Railway stops routing, triggers restart)

### Railway health check configuration

```toml
[deploy]
healthcheckPath = "/api/health"
healthcheckTimeout = 10
```

## Consequences

**Positive:**
- Railway accurately detects governance engine failures and triggers restart/failover.
- Operators can diagnose which specific component is causing a degraded state.

**Negative:**
- Health check adds a DB + Redis round-trip on every Railway health poll (~every 30s).

## Related

- ADR-076: Anti-Replay Guard (Redis dependency)
- ADR-078: Signing Key Persistence (PQC key dependency)
- ADR-074: AVM Database Persistence Bridge
