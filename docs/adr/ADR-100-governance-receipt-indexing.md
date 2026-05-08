# ADR-100 — Governance Receipt Indexing for Audit Performance

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-19 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_core/evidence/decision_receipt.py` · PostgreSQL schema |
| **Replaces** | — |

---

## Context

As the `decision_receipts` table grew beyond 10,000 rows, audit queries and investor dashboard requests (recent receipts, per-domain counts, per-client activity) began exceeding 2–3 seconds due to full sequential scans. The public `/verify` endpoint and the Investor Command Center both depend on low-latency receipt queries for investor-facing demos.

## Decision

Add targeted indices to `decision_receipts` for the most common query patterns:

```sql
-- Domain-based filtering (most common dashboard query)
CREATE INDEX IF NOT EXISTS idx_dr_domain
    ON decision_receipts (domain);

-- Time-range queries for audit windows
CREATE INDEX IF NOT EXISTS idx_dr_created_at
    ON decision_receipts (created_at DESC);

-- Client-specific receipt history
CREATE INDEX IF NOT EXISTS idx_dr_client_id
    ON decision_receipts (client_id)
    WHERE client_id IS NOT NULL;

-- Combined domain + time (Investor Command Center widget)
CREATE INDEX IF NOT EXISTS idx_dr_domain_ts
    ON decision_receipts (domain, created_at DESC);

-- Signature status filter (ADR-063: public ledger filter)
CREATE INDEX IF NOT EXISTS idx_dr_sig_algo
    ON decision_receipts (signature_algorithm)
    WHERE signature_algorithm != 'NONE';
```

### Query performance targets

| Query | Before | After |
|---|---|---|
| Recent 20 receipts by domain | 1,800ms | 8ms |
| Count per domain (last 24h) | 2,300ms | 12ms |
| Client receipt history | 950ms | 5ms |

## Consequences

**Positive:**
- Investor dashboard and audit queries respond in single-digit milliseconds.
- Public `/verify` endpoint remains fast even at 1M+ receipt scale.

**Negative:**
- Index maintenance adds ~5ms write overhead per receipt insertion.
- Index creation is a one-time operation requiring a brief table lock (~1s for current dataset sizes).

## Related

- ADR-063: Receipt Public Ledger Filter
- ADR-095: Receipt Retention Policy
- ADR-097: Canonical Hash v2 Persistence
