# ADR-095: Receipt Retention Policy — Demo vs Production

**Status:** Accepted  
**Date:** 2026-04-20  
**Author:** Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD  
**Related:** ADR-085 (PQC Evidence Layer), ADR-092 (SAE Layer 0), OMNIX-PAT-2026-015

---

## Context

OMNIX generates signed decision receipts via `/evaluate`. Institutional investors,
fund managers, and regulatory reviewers will ask:

- How long do receipts live?
- Are demo receipts distinguishable from production receipts?
- What happens if the DB goes down — are receipts recoverable?
- Is there any TTL or expiry mechanism?

This ADR defines policy answers to those questions.

---

## Decision

### 1. Retention Duration

| Mode        | Retention                    | Storage             |
|-------------|------------------------------|---------------------|
| Demo        | **Indefinite** (no TTL)      | DB + in-memory cache |
| Production  | **Indefinite** (no TTL)      | DB + PQC ledger      |

Receipts are never automatically deleted. This is a deliberate decision:
governance decisions must remain auditable at any future point in time for
regulatory evidence submission and dispute resolution.

If GDPR/CCPA right-to-deletion is required in a future version, receipts will
be pseudonymised (decision + hash retained, PII removed) rather than hard-deleted.

### 2. Demo vs Production Distinction

Demo receipts issued via the public `/evaluate` endpoint are stored with:

```json
"client_id": "PUBLIC_EVALUATE",
"policy_version": "EVL-1.0",
"domain": "trading"
```

Production receipts (B2B integrations) will carry:

```json
"client_id": "<institutional_client_id>",
"policy_version": "PROD-<version>",
"domain": "<client_domain>"
```

This distinction is queryable: `SELECT * FROM decision_receipts WHERE client_id = 'PUBLIC_EVALUATE'`
returns only demo receipts.

**Important:** Demo receipts are structurally identical to production receipts.
The same Layer 0 → Layer 1 → PQC pipeline runs in both modes. The `client_id`
field is the only differentiator — it does not affect governance logic.

### 3. DB Failure Fallback

If the DB is unavailable at receipt creation time:

1. The receipt is stored in the in-memory LRU cache (max 500 entries, FIFO eviction)
2. The API returns 200 with the receipt — **the evaluation is not blocked by DB failure**
3. The in-memory cache does NOT survive server restart
4. Lost receipts (DB down + server restart) are non-recoverable in the current version

**ADR-096 (planned):** Implement a write-ahead log (WAL) that queues DB writes
and retries them on reconnect. This will close the DB-down + restart gap.

### 4. Content Hash Coverage

Each receipt is hashed over the following canonical payload (deterministic, sort_keys=True):

```json
{
  "asset":      "<ASSET>",
  "decision":   "<APPROVED|BLOCKED>",
  "receipt_id": "OMNIX-EVL-<HEX16>",
  "timestamp":  "<ISO8601_UTC>"
}
```

This hash is stored in `decision_receipts.content_hash` and re-derived on every
`/verify` call. A mismatch means the record was tampered with after issuance.

**Limitation:** The hash does not cover `amount`, `jurisdiction`, or `operation`.
These are stored in `encrypted_payload` (metadata JSON) but not hashed. This is
a known gap — the hash covers the governance decision itself, not the full
evaluation context. A broader canonical payload is planned for OMNIX-PAT-2026-015
production deployment.

### 5. AVM Baseline Versioning

Every call to `save_calibration_snapshot()` now appends an immutable entry to
`avm_snapshots/{domain}_history.jsonl`. This file is append-only — entries are
never deleted. Fields per entry:

```json
{
  "snapshot_id": "AVM-XXXXXXXXXX",
  "parameter_version": "1.xxxxxxxxxx",
  "domain": "<domain>",
  "calibrated_at": "<ISO8601>",
  "description": "<human-readable reason>",
  "tags": [],
  "baseline_signals": { ... }
}
```

If the active snapshot is overwritten (intentional recalibration), all previous
baselines remain in the history log. This satisfies the "leave trace if it changes"
requirement for regulatory due diligence.

---

## Consequences

**Positive:**
- Clear answer to "how long do receipts last?" — indefinitely
- Demo vs production distinguishable by `client_id` and `policy_version`
- Hash coverage is documented and its limitations are explicit
- AVM recalibrations fully traceable via append-only history

**Negative / Future Work:**
- DB-down + restart gap remains open until ADR-096 (WAL) is implemented
- Hash covers only 4 fields — broader coverage deferred to production deployment
- No automated GDPR pseudonymisation (deferred to B2B pilot phase)

---

## References

- `omnix_web/api/proof_layer.py` — `_persist_evl_receipt()`, `_compute_content_hash()`
- `omnix_core/governance/assumption_validity_monitor.py` — `save_calibration_snapshot()`
- `avm_snapshots/{domain}_history.jsonl` — AVM version history files
- ADR-085: PQC Evidence & Receipt Layer
- ADR-092: Structural Admissibility Engine (Layer 0)
