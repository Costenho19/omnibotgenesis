# Dataset Description: OMNIX Governance Receipts

**File**: `governance_receipts_dataset.csv`  
**Records**: 82,569  
**Period**: February 21, 2026 – March 20, 2026  
**Source**: OMNIX Decision Governance Infrastructure — live operational data

---

## Column Definitions

| Column | Type | Description |
|--------|------|-------------|
| `receipt_id` | string | Globally unique receipt identifier. Format: `OMNIX-{12 hex chars}`. Constructed as the first 12 characters of the SHA-256 hash of the receipt payload. |
| `timestamp_utc` | ISO 8601 | Timestamp of the governance decision with microsecond precision, in UTC. |
| `decision` | enum | Governance outcome: `HOLD` (decision deferred — signals do not meet full approval criteria), `BLOCK` (decision rejected — one or more checkpoints failed hard), `APPROVED` (all 8 checkpoints passed, decision approved for execution), `BLOCKED` (legacy label, equivalent to BLOCK). |
| `asset` | string | Financial instrument evaluated. Examples: `BTC/USD`, `XRP/USD`, `AVAX/USD`. |
| `policy_version` | string | Version of the governance policy active at decision time. `6.5.4e` = current production version. |
| `engine_version` | string | OMNIX engine version that produced the decision. |
| `signature_algorithm` | string | Post-quantum digital signature algorithm used to sign this receipt. `Dilithium-3 (ML-DSA-65)` = NIST ML-DSA-65 at ~192-bit classical security equivalent. |
| `content_hash` | SHA-256 hex | SHA-256 hash of the canonical receipt payload. This is the value that was signed by the Dilithium-3 key. Can be used to verify receipt integrity. |
| `prev_hash` | SHA-256 hex | SHA-256 hash of the previous receipt in the chain. Links receipts into an append-only cryptographic ledger. The first receipt in the chain has a synthetic genesis hash. |
| `created_at` | timestamp | Database insertion timestamp. |

---

## Decision Semantics

### HOLD (88.6% of decisions)
The governance pipeline evaluated the candidate decision and determined that current market conditions do not satisfy the full approval criteria. This is the expected behavior under uncertain or suboptimal signal conditions. A HOLD is not a failure — it is the system correctly abstaining from a decision it cannot confidently govern.

### BLOCK + BLOCKED (11.3% of decisions)
One or more checkpoints in the 8-checkpoint pipeline produced a hard failure. `BLOCK` is the current label; `BLOCKED` is a legacy equivalent retained for historical continuity. Common causes: Monte Carlo expected return below zero, coherence score below threshold, RMS drawdown limit exceeded, or Black Swan risk above ceiling.

### APPROVED (0.05% of decisions)
All 8 checkpoints passed simultaneously. The decision was authorized for execution. The rarity of this outcome reflects the system's high selectivity — requiring simultaneous satisfaction of all governance constraints.

---

## Hash Chain Verification

The `content_hash` and `prev_hash` columns form a cryptographic chain:

```
Receipt N:   prev_hash = content_hash of Receipt (N-1)
Receipt N:   content_hash = SHA256(receipt_id || timestamp || decision || asset || ... || prev_hash)
```

This construction means any modification to any historical receipt invalidates all subsequent `prev_hash` links, making tampering detectable by anyone holding the dataset.

To verify chain integrity, see the Python snippet in `README.md`.

---

## Notes on Completeness

- Receipts with `prev_hash = NULL` represent chain segments where the preceding receipt is not included in this export (e.g., beginning of a new chain segment after system restart)
- The dataset includes all governance decisions from the official Track Record period (January 15, 2026 – present) plus the tail of the Learning Baseline period
- No decisions have been filtered or excluded from this export
- Signature verification requires access to the Dilithium-3 public key, available via the public verification server at `https://omnixquantum.net/verify/{receipt_id}`
