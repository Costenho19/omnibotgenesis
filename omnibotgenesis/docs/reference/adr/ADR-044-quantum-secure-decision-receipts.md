# ADR-044: Quantum-Secure Decision Receipts — Timestamping, Hash Chains & Transparency Log

**Status**: Accepted  
**Date**: March 2026  
**Author**: Harold Nunes, OMNIX Architecture  
**Category**: Evidence & Audit  
**Related**: ADR-022, ADR-031, ADR-042, ADR-043

---

## Context

OMNIX generates governance receipts for every decision (ADR-022). These receipts include a SHA-256 hash, a Dilithium-3 signature, and a `prev_hash` field linking to the previous receipt.

**Three gaps remain:**

1. **Timestamps are not independently verifiable.** The receipt timestamp is self-asserted by OMNIX — no external timestamping authority or internal tamper-evidence protects it.

2. **The hash chain exists but is per-asset, not globally ordered.** The `prev_hash` in `decision_receipts` chains receipts together, but there is no rolling accumulator (Merkle root) that allows verifying the entire chain's integrity with a single value.

3. **There is no public, append-only audit surface.** Regulators and investors cannot independently audit the chain without querying the internal DB.

---

## Decision

Implement three interconnected enhancements in `omnix_core/evidence/transparency_chain.py`:

### 1. Internal RFC 3161-Style Trusted Timestamping

Each receipt gets a **Timestamp Token (TST)** containing:
- SHA-256 hash of the payload
- Nanosecond-precision UTC timestamp
- Cryptographic nonce (prevents replay)
- OMNIX policy identifier
- SHA-256 hash of the TST itself (self-integrity)

This follows RFC 3161 structure without requiring an external TSA (Timestamp Authority). The TST is embedded in the transparency log entry and can be verified by anyone with the log entry.

```
Internal TSA model:
  payload_hash + nonce + ts_utc → TST → tst_hash
  tst_hash verifiable by anyone with the entry
```

> **Institutional framing**: "Internal timestamp with cryptographic nonce and self-integrity hash. No external TSA dependency — suitable for deployment environments with network restrictions."

### 2. Rolling Merkle-Root Transparency Log

A new append-only database table `governance_transparency_log` records every governance receipt with:

| Column | Description |
|--------|-------------|
| `log_id` | Unique entry ID |
| `receipt_id` | Links to `decision_receipts.receipt_id` |
| `symbol` | Asset (BTC, ETH, etc.) |
| `event_type` | decision / order / override |
| `payload_hash` | SHA-256 of the receipt content |
| `prev_log_hash` | Hash of previous entry (chain) |
| `merkle_root` | Rolling accumulator = SHA256(prev_root \|\| payload_hash) |
| `signing_provider` | Active crypto provider ID (ADR-043) |
| `signature_b64` | Dilithium signature over the entry |
| `ts_utc` | UTC timestamp |
| `chain_version` | Schema version (1 = ADR-044) |

**Rolling Merkle root formula:**
```
new_root = SHA256(prev_merkle_root || new_payload_hash)
first_entry: prev_root = "00...0" (64 zeros)
```

This allows auditors to compute the expected root at any point in the chain with only the ordered list of payload hashes — no additional data needed.

### 3. Public Transparency API

New endpoint (added to verification server):
```
GET /api/transparency/chain?symbol=BTC&limit=20
```

Returns ordered log entries with merkle roots, enabling independent chain verification. No internal data exposed — only cryptographic proofs.

---

## Backward Compatibility

Legacy receipts (pre-ADR-044) without transparency log entries:
- Still verify via `ReceiptVerifier.verify_receipt()` (unchanged)
- `prev_log_hash` is NULL for first entry — allowed in schema
- No retroactive re-signing required

---

## File Structure

```
omnix_core/evidence/transparency_chain.py   ← New (ADR-044)
governance_transparency_log                 ← New DB table
```

---

## Verification Protocol (Self-Verifiable Receipts)

Any auditor can verify a chain of N receipts with:
1. Compute `SHA256(payload)` for each receipt
2. Apply rolling Merkle formula in order
3. Compare final computed root with stored root in latest entry
4. Verify Dilithium signatures using stored `public_key` from receipt

No OMNIX infrastructure required after extraction.

---

## Consequences

### Positive
- Receipts are **self-verifiable** without calling OMNIX
- Merkle root allows auditing the entire chain with a single hash comparison
- Meets emerging regulatory expectations (EU AI Act Article 13 — traceability)
- Institutional statement: "Every OMNIX governance decision generates a self-verifiable receipt with a quantum-resistant signature and an independently verifiable hash chain"

### Negative / Risks
- Transparency log writes add ~5ms per receipt (async, non-blocking)
- `governance_transparency_log` table grows with every decision — archival strategy needed in future (not blocking)
- Rolling root is rolling, not full Merkle tree — sufficient for audit purposes, not formal Merkle proof path

---

## External Framing (Institutional Tier)

> "Every OMNIX governance decision produces a cryptographically signed, timestamped receipt with an independently verifiable hash chain. Receipts are self-verifiable — auditors can verify the entire governance history without accessing OMNIX systems. The chain uses a rolling Merkle accumulator, enabling single-hash integrity checks across thousands of decisions."

---

## Related ADRs
- ADR-022: Base PQC — original signing and receipt generation
- ADR-043: Crypto-Agility Layer — transparency log uses active provider for signing
- ADR-042: Hybrid Cryptography — optional hybrid transport for receipt packages
