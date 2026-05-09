# OMNIX QUANTUM — Health Monitoring & Operational Runbook

**Document:** OMNIX-OPS-001  
**ADR:** ADR-150  
**Date:** May 2026  
**Audience:** Harold Nunes · Future DevOps · On-call engineer

---

## 1. Health Endpoints

| Endpoint | Purpose | When to use |
|---|---|---|
| `GET /api/health` | Full subsystem report | Dashboard, scheduled check, investigation |
| `GET /api/health/live` | Liveness — is the process alive? | Railway health check, UptimeRobot, Pingdom |
| `GET /api/health/ready` | Readiness — can it serve traffic? | Railway readiness probe, load balancer |
| `POST /api/health/reconcile-wal` | Flush WAL after DB recovery | After any DB outage |

### Interpreting `/api/health`

| `status` | Meaning | Action |
|---|---|---|
| `UP` | All critical subsystems healthy | None |
| `DEGRADED` | Non-critical subsystem(s) impaired (Redis, WAL, AVM) | Monitor; investigate if persists >15 min |
| `DOWN` | Critical subsystem(s) down (DB or governance engine) | Immediate action — see Section 3 |

Add `?alerts=false` to suppress Telegram alerts (e.g. for uptime monitors polling every 30s):

```
GET /api/health?alerts=false
```

---

## 2. Subsystem Reference

### database (CRITICAL)
**Probe:** psycopg2 connect + `SELECT COUNT(*) FROM decision_receipts LIMIT 1`  
**DOWN means:** No governance receipts can be stored. WAL accumulates.  
**Root causes:** DATABASE_URL missing, Railway DB paused, connection pool exhausted.

### redis (non-critical)
**Probe:** SET/GET round-trip with random probe value  
**DEGRADED means:** Anti-replay may allow duplicate receipt IDs across dynos.  
**Root causes:** REDIS_URL missing, Railway Redis paused, network partition.

### pqc_dilithium3 (non-critical)
**Probe:** sign + verify cycle with `b"omnix-health-probe"`  
**DEGRADED means:** Receipts are SHA-256 only — not Dilithium-3 signed.  
**Root causes:** `pypqc` not installed, `OMNIX_SIGNING_SECRET_KEY_B64` missing.

### receipt_wal (non-critical)
**Probe:** `wal.wal_size()` — pending entries  
**DEGRADED means:** 1-9 receipts in WAL not yet committed to DB.  
**DOWN means:** ≥10 receipts in WAL — DB likely not receiving writes.  
**Recovery:** `POST /api/health/reconcile-wal` after DB is restored.

### avm (non-critical)
**Probe:** `get_avm_instance("health-probe").get_current_weights()`  
**DEGRADED means:** AVM calibration may be stale or module not loaded.

### governance_engine (CRITICAL)
**Probe:** import `ExternalEvaluator` + `DecisionReceiptEngine`  
**DOWN means:** Governance evaluations cannot complete.  
**Root causes:** Python import error, corrupted module, missing dependency.

---

## 3. Incident Runbooks

### INC-001: `database` DOWN

1. Check Railway dashboard → database service status
2. Check `DATABASE_URL` env var is correctly set in Railway
3. Run `GET /api/health/ready` — will return 503
4. When DB is restored:
   - Run `POST /api/health/reconcile-wal` to flush WAL
   - Verify `wal_pending: 0` in next `GET /api/health`

### INC-002: `receipt_wal` has pending entries after DB recovery

```bash
curl -X POST https://omnixquantum.net/api/health/reconcile-wal \
  -H "X-Admin-Token: <ADMIN_TOKEN>"
```

Response: `{"reconciled": N, "pending_before": N, "pending_after": 0}`

### INC-003: `pqc_dilithium3` DEGRADED in production

**Immediate:** Receipts are still valid (SHA-256 hash) — governance is not broken.  
**Action:** Add `OMNIX_SIGNING_SECRET_KEY_B64` and `OMNIX_SIGNING_PUBLIC_KEY_B64` to Railway environment variables.  
**Reference:** FMR-001 in `docs/GOVERNANCE_FAILURE_MODE_REPORT.md`

### INC-004: `redis` DEGRADED in production

**Immediate:** Anti-replay is in `best_effort` mode — replay attacks possible across dynos.  
**Action:** Restore Redis. Verify `REDIS_URL` in Railway. Set `OMNIX_ANTI_REPLAY_MODE=strict`.  
**Reference:** FMR-004 in `docs/GOVERNANCE_FAILURE_MODE_REPORT.md`

---

## 4. Railway Configuration (Required)

Add these health check paths in Railway service settings:

| Check type | Path | Expected |
|---|---|---|
| Liveness | `/api/health/live` | HTTP 200 |
| Readiness | `/api/health/ready` | HTTP 200 |

### Recommended uptime monitor (UptimeRobot / Better Stack)

```
URL:      https://omnixquantum.net/api/health/live
Interval: 60 seconds
Alert:    immediately on first failure
```

For deep health checks (not every 60s — has DB cost):

```
URL:      https://omnixquantum.net/api/health?alerts=false
Interval: 300 seconds (5 min)
```

---

## 5. Telegram Alert Reference

All alerts come from the OMNIX bot to the admin user (`TELEGRAM_ADMIN_USER_ID`).

| Badge | Level | Trigger |
|---|---|---|
| 🔴 CRITICAL | Immediate action | DB DOWN, WAL ≥10 pending, governance engine DOWN |
| 🟡 WARNING | Investigate | Redis DEGRADED, WAL 1-9 pending, PQC fallback |
| 🟢 INFO | Informational | Server startup, scheduled events |
| ✅ RECOVERY | Resolved | Subsystem returned to UP from DOWN/DEGRADED |

**Cooldown:** 5 minutes between identical alerts (same subsystem + level).  
**Override:** `force=True` in `alert_critical()` bypasses cooldown (used at startup).

---

## 6. Manual Health Check (CLI)

```bash
# Quick liveness
curl https://omnixquantum.net/api/health/live

# Full report (no alerts)
curl "https://omnixquantum.net/api/health?alerts=false" | python -m json.tool

# Readiness (exit code 0 = ready, 1 = not ready)
curl -f https://omnixquantum.net/api/health/ready && echo "READY" || echo "NOT READY"
```

---

*OMNIX QUANTUM — Operational Runbook OMNIX-OPS-001 · ADR-150 · May 2026*
