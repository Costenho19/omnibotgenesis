# ADR-097 — Canonical Hash v2 Persistence

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-17 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_core/evidence/decision_receipt.py` · `omnix_web/api/omnix_engine/receipt_to_vc.py` |
| **Extends** | ADR-096 (Expanded Canonical Receipt) |
| **Replaces** | — |

---

## Context

ADR-096 introduced a canonical hash v2 (`execution_proof.canonical_hash`) that included the execution context — executor ID, execution timestamp, and outcome — in the hash input, binding the governance decision to its actual execution for full auditability.

However, the v2 hash was computed on-the-fly and returned in the API response and cache, but **not persisted** as a dedicated database column. This created a gap:

- Receipts retrieved from the database could not be re-verified using the v2 hash without re-executing the execution proof computation.
- Cross-receipt deduplication and integrity scanning could not use the canonical hash as a lookup key.
- Auditors querying the database directly had no stable hash to reference in their audit reports.

## Decision

Persist `execution_proof.canonical_hash` as a dedicated column `canonical_hash_v2` in the `decision_receipts` table.

```sql
ALTER TABLE decision_receipts
    ADD COLUMN IF NOT EXISTS canonical_hash_v2 TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_dr_canonical_hash_v2
    ON decision_receipts (canonical_hash_v2)
    WHERE canonical_hash_v2 IS NOT NULL;
```

### Backfill policy

Existing rows where `execution_proof` is present are backfilled at first startup via a one-time migration script. Rows without an `execution_proof` block retain `canonical_hash_v2 = NULL`.

### Verification endpoint update

`GET /verify/<receipt_id>` now returns both hash versions:

```json
{
  "canonical_hash_v1": "sha256:abc...",
  "canonical_hash_v2": "sha256:def...",
  "hash_algorithm": "SHA-256",
  "execution_bound": true
}
```

## Consequences

**Positive:**
- Auditors can use `canonical_hash_v2` as a stable, database-queryable identifier.
- Deduplication checks are O(1) via the unique index.
- Re-verification does not require re-computing the execution proof.

**Negative:**
- Backfill migration adds ~2–5 minutes to first deploy on large datasets.
- `canonical_hash_v2` is NULL for receipts created before ADR-096.

## Related

- ADR-096: Expanded Canonical Receipt
- ADR-078: Signing Key Persistence
- ADR-131: Execution Integrity Layer
