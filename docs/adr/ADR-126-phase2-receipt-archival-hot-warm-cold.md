# ADR-126 — Phase 2: Decision Receipt Archival (HOT / WARM / COLD)

**Status:** Accepted  
**Date:** 2026-04-25  
**Author:** Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD (UK)  
**Regulatory basis:** MiFID II Article 25 (5-year retention), GDPR Article 5(1)(e)

---

## Context

OMNIX Quantum's `decision_receipts` table (HOT tier) stores every governance
decision with PQC-signed receipts. Over time, the volume of receipts grows
unboundedly. Under MiFID II, receipts must be retained for ≥ 5 years.

Phase 2 implements a three-tier archival system — HOT, WARM, COLD — that
progressively moves aging receipts off the hot path while preserving full
auditability across all tiers.

---

## Decision

### Tier Structure

| Tier | Table / Location              | Retention        | Use Case              |
|------|-------------------------------|------------------|-----------------------|
| HOT  | `decision_receipts` (PG)      | 0–30 days        | Real-time ops, API    |
| WARM | `decision_receipts_warm` (PG) | 31–365 days      | Recent audits         |
| COLD | S3/R2 or `decision_receipts_cold` (PG fallback) | 1–5 years | Regulatory archives |

Retention windows configurable via env vars:
`HOT_RETENTION_DAYS=30`, `WARM_RETENTION_DAYS=365`, `COLD_RETENTION_DAYS=1825`

---

### 9-Step HOT → WARM Migration Protocol

1. **Pre-flight idempotency check** — if `receipt_archival_index` shows `ARCHIVED`, skip.
2. **PQC signature pre-verification** — `_verify_pqc_signature(receipt)` must return `True` or `None` (no provider). `False` → `ArchivalIntegrityError`.
3. **Mark COPYING** — write `PENDING → COPYING` in `receipt_archival_index`.
4. **INSERT INTO WARM** — copy all columns + `archived_at`, `source_tier = 'HOT'`.
5. **Verify content_hash in WARM** — `SELECT content_hash FROM decision_receipts_warm WHERE receipt_id = ?`. Hash mismatch → rollback + `ArchivalIntegrityError`.
6. **PQC re-verification on WARM row** — signature must still verify after copy.
7. **Mark VERIFIED** — update index to `VERIFIED`.
8. **DELETE from HOT** — only if WARM hash matches.
9. **Mark ARCHIVED** — final status, commit.

Same 9-step protocol applies for WARM → COLD, with the cold backend
(`S3ColdBackend` or `PostgreSQLColdBackend`) replacing the WARM INSERT.

---

### Immutability Guarantees

- S3/R2 object key is derived from `content_hash[:8]` — content-addressable.
- If `head_object` returns the same hash → idempotent skip (no re-upload).
- If `head_object` returns a **different** hash → `ArchivalIntegrityError` — a different receipt already occupies that key (impossible by design; indicates tampering).
- PostgreSQL COLD uses `ON CONFLICT (receipt_id) DO NOTHING` — same idempotency.

---

### Cold Storage Format

```json
{
  "receipt": {
    "receipt_id": "OMNIX-TRD-...",
    "timestamp_utc": "...",
    "..."
  },
  "metadata": {
    "tier": "cold",
    "version": "v1",
    "archived_at": "2026-04-25T23:00:00+00:00",
    "source_tier": "WARM",
    "immutable": true
  }
}
```

---

### Unified Retrieval (HOT → WARM → COLD)

All public receipt-fetching endpoints now call a multi-tier helper before
returning 404:

1. `proof_layer.py` / `institutional_verify` → `_fetch_receipt_all_tiers(receipt_id_clean)`
2. `gov_blueprint.py` / `GET /api/governance/receipts/<id>` → inline HOT → WARM → COLD

Both endpoints include `storage_tier: "HOT"|"WARM"|"COLD"` in their JSON
response so consumers know which tier served the request.

---

### Archival Index (`receipt_archival_index`)

```sql
CREATE TABLE IF NOT EXISTS receipt_archival_index (
    id              SERIAL PRIMARY KEY,
    receipt_id      VARCHAR(120) NOT NULL,
    tier            VARCHAR(10)  NOT NULL,   -- 'HOT', 'WARM', 'COLD'
    archival_status VARCHAR(20)  NOT NULL,   -- 'PENDING','COPYING','VERIFIED','ARCHIVED','ERROR'
    content_hash    VARCHAR(128),
    storage_location TEXT,
    archived_at     TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    error_message   TEXT
);
CREATE INDEX IF NOT EXISTS idx_archival_receipt_id ON receipt_archival_index(receipt_id);
CREATE INDEX IF NOT EXISTS idx_archival_status     ON receipt_archival_index(archival_status);
```

---

### COLD_STORAGE_REQUIRED Fail-Hard Mode

If `OMNIX_COLD_STORAGE_REQUIRED=true` (e.g., production Railway deployment)
and S3 credentials (`OMNIX_COLD_S3_BUCKET`, `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`) are not configured, `_get_cold_backend()` raises
`ColdStorageRequiredError` with an actionable message. The daemon thread logs
the error and skips that cycle.

---

### Daemon Thread (server.py)

`_receipt_archival_loop` starts after the retention loop (warmup 10 min,
cycle every 6 h). It calls `ReceiptArchivalService.run_archival_cycle()` and
logs the summary. Any `ColdStorageRequiredError` is captured in the summary
dict and logged at ERROR level.

---

## Implementation Files

| File | Change |
|------|--------|
| `omnix_core/evidence/receipt_archival.py` | NEW — full archival service (~600 lines) |
| `omnix_web/api/server.py` | ADD `_receipt_archival_loop` daemon |
| `omnix_web/api/proof_layer.py` | ADD `_fetch_receipt_all_tiers`, update `institutional_verify`, add `storage_tier` to response |
| `omnix_web/api/gov_blueprint.py` | UPDATE single-receipt endpoint to HOT→WARM→COLD lookup |
| `tests/test_phase2_receipt_archival.py` | NEW — 43 tests, 100% green |

---

## Test Coverage (43 tests)

| Suite | Tests | Focus |
|-------|-------|-------|
| TestArchivalServiceInit | 5 | Construction, env vars |
| TestColdBackendFactory | 5 | Backend selection, fail-hard |
| TestS3ColdBackend | 10 | put, get, verify_exists, immutability, envelope |
| TestHotToWarmMigration | 4 | 9-step protocol, integrity errors, idempotency |
| TestWarmToColdMigration | 3 | PG fallback, fail-hard propagation, idempotency |
| TestFetchReceiptAnyTier | 3 | HOT hit, WARM hit, not found |
| TestRunArchivalCycle | 4 | Skipped paths, success summary, error capture |
| TestHelpers | 9 | Serialization, constants, PQC skip |

---

## Consequences

**Positive:**
- Full MiFID II 5-year retention path implemented
- Zero data loss: HOT never deleted until WARM integrity verified
- Transparent to callers: `storage_tier` field tells which tier served the receipt
- Idempotent: safe to run archival job multiple times

**Accepted trade-offs:**
- WARM/COLD tables require schema migration on first deploy (handled by `ensure_schema`)
- COLD S3 lookup requires boto3 + valid credentials; PostgreSQL fallback is always available
