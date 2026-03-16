# ADR-044: Quantum-Secure Decision Receipts — Transparency Chain

**Status**: ACCEPTED — March 2026  
**Author**: Harold Nunes, OMNIX Quantum  
**Part of**: OMNIX Quantum Zenodo Deposit — DOI: 10.5281/zenodo.XXXXXXX  
**Related**: ADR-022 (PQC signing), ADR-042 (hybrid KEM)

---

## Context

OMNIX Quantum generates a cryptographically signed receipt for every governance decision. Three gaps were identified and addressed by this ADR:

1. Timestamps were self-asserted with no independent tamper-evidence
2. No global chain accumulator existed to verify the entire history with a single value
3. No public audit surface existed for external verification without internal system access

---

## Decision

Three interconnected enhancements were implemented:

### 1. Internal Trusted Timestamping

Each receipt includes a timestamp token containing a cryptographic nonce and a self-integrity hash, following the RFC 3161 structure without requiring an external Timestamp Authority. This makes timestamps independently verifiable from the receipt data alone.

### 2. Rolling Hash Chain Accumulator

Every receipt is linked to the previous one via a rolling SHA-256 accumulator. Modifying any historical receipt invalidates all subsequent entries. A single hash value represents the integrity of the entire chain — any auditor can verify it without accessing OMNIX systems.

### 3. Public Verification Interface

Every receipt can be independently verified at:

**`https://omnixquantum.net/r/{receipt_id}`**

No credentials required. No internal data exposed.

---

## Receipt Fields (Public)

Each receipt in the dataset contains:

| Field | Description |
|-------|-------------|
| `receipt_id` | Globally unique identifier (`OMNIX-{12 hex chars}`) |
| `timestamp_utc` | Decision timestamp |
| `decision` | APPROVED / BLOCK / HOLD |
| `asset` | Financial instrument evaluated |
| `content_hash` | SHA-256 of this receipt |
| `prev_hash` | Links to previous receipt (chain) |
| `signature_algorithm` | `"Dilithium-3 (ML-DSA-65)"` |

---

## Chain Integrity

The dataset included in this deposit (72,443 receipts) forms a contiguous hash chain. Any researcher can verify that:

1. No receipt was modified after creation (hash chain continuity)
2. Every receipt carries a Dilithium-3 signature
3. The sequence is complete with no gaps

---

## Consequences

**Positive**
- Receipts are self-verifiable without calling OMNIX systems
- A single hash value audits the entire governance history
- Meets EU AI Act Article 13 traceability requirements

**Negative**
- Transparency log grows with every decision (archival strategy planned)

---

## Related ADRs

- ADR-022: Base PQC — Dilithium-3 signing and receipt generation
- ADR-042: Hybrid KEM — encrypted transport for receipt packages
- ADR-043: Crypto-Agility Layer
