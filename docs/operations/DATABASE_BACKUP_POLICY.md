# OMNIX Decision Governance — Database Backup Policy

**Classification**: Internal — Operations  
**Version**: 1.0  
**Effective Date**: February 26, 2026  
**Owner**: Harold Nunes — Solo Founder & CEO  
**Last Verified**: February 26, 2026  

---

## 1. Database Infrastructure

| Component | Provider | Location | Plan |
|-----------|----------|----------|------|
| PostgreSQL (primary) | Railway | Production — `omnibotgenesis` service | Starter |
| Redis (cache) | Railway | Production — shared with bot | Starter |
| Database URL | `${{Postgres.DATABASE_URL}}` | Railway internal | N/A |

---

## 2. Critical Tables

These tables contain irreplaceable production data and must be protected:

| Table | Description | Criticality |
|-------|-------------|-------------|
| `decision_receipts` | PQC-signed governance receipts | **CRITICAL** — Audit evidence |
| `shadow_trade_events` | 670K+ evaluation cycle records | **CRITICAL** — Learning engine data |
| `trades` | Historical trade executions | **CRITICAL** — Track record |
| `balance_history` | Capital snapshots over time | **HIGH** |
| `conversation_memory` | Bot conversation context | **MEDIUM** |
| `risk_metrics_snapshots` | Risk state history | **MEDIUM** |
| `adaptive_engine_data` | Calibration parameters | **MEDIUM** |

---

## 3. Automatic Backup Coverage (Railway)

Railway PostgreSQL performs automatic backups on all plans:

| Parameter | Value |
|-----------|-------|
| Frequency | Daily (automatic) |
| Retention — Starter Plan | 7 days rolling |
| Retention — Pro Plan | 30 days rolling |
| Backup type | Full database snapshot |
| Geographic redundancy | Railway cloud infrastructure |
| Access | Railway Dashboard → Database → Backups |

> **Note**: Upgrade to Railway Pro before investor due diligence or immediately after first B2B client — 30-day retention is required for audit trails.

---

## 4. Manual Backup Procedure (On-Demand)

Run before any major deployment, schema migration, or investor demo.

### 4.1 Command

```bash
pg_dump $DATABASE_URL \
  --format=custom \
  --compress=9 \
  --file="omnix_backup_$(date +%Y%m%d_%H%M%S).dump"
```

### 4.2 Backup Critical Tables Only

```bash
pg_dump $DATABASE_URL \
  --format=custom \
  --table=decision_receipts \
  --table=shadow_trade_events \
  --table=trades \
  --table=balance_history \
  --compress=9 \
  --file="omnix_critical_$(date +%Y%m%d_%H%M%S).dump"
```

### 4.3 Verify Backup

```bash
pg_restore --list omnix_backup_YYYYMMDD_HHMMSS.dump | head -20
```

---

## 5. Restore Procedure

### 5.1 Restore from Railway Automatic Backup

1. Go to Railway Dashboard → Project → `omnibotgenesis`
2. Click on the PostgreSQL database service
3. Navigate to **Backups** tab
4. Select the desired backup date
5. Click **Restore** — Railway handles the full restoration
6. Verify by running: `SELECT COUNT(*) FROM decision_receipts;`
7. Restart the bot service after restore completes

### 5.2 Restore from Manual Dump

```bash
pg_restore \
  --dbname=$DATABASE_URL \
  --clean \
  --if-exists \
  --verbose \
  omnix_backup_YYYYMMDD_HHMMSS.dump
```

### 5.3 Verify Restore

```sql
SELECT COUNT(*) FROM decision_receipts;
SELECT COUNT(*) FROM shadow_trade_events;
SELECT MAX(created_at) FROM trades;
```

Expected: `decision_receipts` ≥ 20,000 rows, `shadow_trade_events` ≥ 670,000 rows.

---

## 6. Recovery Time Objectives

| Scenario | RTO | RPO | Method |
|----------|-----|-----|--------|
| Accidental table drop | < 30 min | 24 hours | Railway automatic restore |
| Corrupted data | < 30 min | 24 hours | Railway automatic restore |
| Full database loss | < 60 min | 24 hours | Railway automatic restore |
| Schema migration rollback | < 15 min | 0 (pre-migration dump) | Manual dump restore |

---

## 7. Backup Verification Schedule

| Frequency | Action | Responsible |
|-----------|--------|-------------|
| Monthly | Verify Railway shows backups in the last 7 days | Harold Nunes |
| Before each deployment | Run manual backup of critical tables | Harold Nunes |
| Before investor demos | Full manual backup + row count verification | Harold Nunes |
| After Railway plan upgrade | Confirm retention extended to 30 days | Harold Nunes |

---

## 8. Disaster Recovery Contact

| Role | Contact |
|------|---------|
| Infrastructure | Railway Support — railway.app/support |
| Database | Railway Dashboard → Help |
| Application Owner | Harold Nunes |

---

## 9. Verification Log

| Date | Verified By | Railway Backup Status | Row Counts | Notes |
|------|-------------|----------------------|------------|-------|
| Feb 26, 2026 | Harold Nunes | ✅ Railway auto-backup active | decision_receipts: 20,610 / shadow_events: 681,728 | Initial policy creation |

---

## 10. References

- Database schema: `omnix_services/database_service/`
- Railway deployment: `docs/compliance/audits/CTO_SRE_SECURITY_AUDIT_JAN21_2026.md`
- Security audit: `docs/compliance/audits/OMNIX_Security_Audit_v1.0_INTERNAL.md`
