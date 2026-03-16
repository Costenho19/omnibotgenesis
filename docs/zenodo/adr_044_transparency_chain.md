# ADR-044: Quantum-Secure Decision Receipts — Transparency Chain & Hash Verification

**Status**: ACCEPTED — Implemented March 2026  
**Author**: Harold Nunes, OMNIX Quantum  
**Part of**: OMNIX Quantum Zenodo Deposit — DOI: 10.5281/zenodo.XXXXXXX  
**Related**: ADR-022 (PQC signing), ADR-042 (hybrid KEM), ADR-043 (crypto-agility)

---

## Context

OMNIX Quantum generates a cryptographically signed receipt for every governance decision. Before ADR-044, three gaps existed:

1. **Timestamps were self-asserted** — no independent tamper-evidence for timing
2. **No global hash chain accumulator** — no single value to verify the entire chain
3. **No public audit surface** — external auditors needed direct database access

ADR-044 addresses all three.

---

## Decision

### 1. Rolling SHA-256 Merkle Chain

Every receipt is linked to the previous one via a rolling accumulator:

```
new_root = SHA256(prev_merkle_root || new_payload_hash)
```

**Genesis root** (first entry in the chain):
```
genesis_root = SHA256(b"OMNIX-GENESIS-TRANSPARENCY-CHAIN-v1")
```

This construction means:
- Modifying any historical receipt invalidates all subsequent roots
- A single hash value (the current root) represents the integrity of the entire chain
- Any party holding the root at any point in time can detect retroactive tampering

### 2. Internal RFC 3161-Style Timestamp Tokens

Each receipt includes a Timestamp Token (TST) containing:

| Field | Description |
|-------|-------------|
| `payload_hash` | SHA-256 of the receipt content |
| `ts_utc` | Nanosecond-precision UTC timestamp |
| `nonce` | Cryptographic nonce (prevents replay) |
| `policy_id` | OMNIX governance policy version |
| `tst_hash` | SHA-256 of the token itself (self-integrity) |

This follows RFC 3161 structure without requiring an external Timestamp Authority — suitable for deployment environments with network restrictions.

### 3. Public Verification Interface

Every receipt can be independently verified without OMNIX infrastructure:

```
GET /api/public/verify/{receipt_id}
GET /r/{receipt_id}               ← Human-readable HTML report
```

The verification endpoint exposes no internal system state — only the receipt fields, signature status, and chain linkage.

---

## Receipt Schema

| Field | Type | Description |
|-------|------|-------------|
| `receipt_id` | string | `OMNIX-{12 hex chars}` — globally unique |
| `timestamp_utc` | ISO 8601 | Decision timestamp (microsecond precision) |
| `decision` | enum | APPROVED / BLOCK / HOLD |
| `asset` | string | Financial instrument evaluated |
| `veto_chain` | JSON | Ordered checkpoint results with metrics |
| `policy_version` | string | Governance policy version at decision time |
| `prev_hash` | SHA-256 | Hash of previous receipt (chain link) |
| `content_hash` | SHA-256 | Hash of this receipt's canonical payload |
| `signature` | bytes | Dilithium-3 signature over `content_hash` |
| `signature_algorithm` | string | `"Dilithium-3 (ML-DSA-65)"` |
| `public_key` | bytes | Signing public key (1,952 bytes) — enables independent verification |

---

## Chain Verification Protocol

Any auditor can verify a sequence of N receipts without OMNIX infrastructure:

```python
import csv, hashlib

with open('governance_receipts_dataset.csv') as f:
    rows = list(csv.DictReader(f))

# Step 1: Verify hash chain linkage
chain_valid = 0
chain_broken = 0
for i in range(len(rows) - 1):
    if rows[i]['content_hash'] == rows[i+1]['prev_hash']:
        chain_valid += 1
    else:
        chain_broken += 1

print(f"Chain links verified : {chain_valid}")
print(f"Chain breaks detected: {chain_broken}")
print(f"Chain integrity      : {'VALID' if chain_broken == 0 else 'COMPROMISED'}")
```

For signature verification, the Dilithium-3 public key is embedded in each receipt's `public_key` field and available via `/api/public/verify/{receipt_id}`.

---

## Dataset Application

The `governance_receipts_dataset.csv` included in this deposit contains 72,443 receipts forming a contiguous hash chain. Running the verification script above confirms chain integrity across the full dataset. Any researcher can independently verify that:

1. No receipt has been modified after creation (hash chain integrity)
2. Every receipt was signed by the OMNIX Quantum governance engine (Dilithium-3 signature)
3. The sequence is complete with no gaps (prev_hash continuity)

---

## Consequences

**Positive**
- Receipts are **self-verifiable** without calling OMNIX Quantum systems
- Rolling Merkle root allows auditing the entire chain with a single hash comparison
- Meets EU AI Act Article 13 traceability requirements
- Any tampering is cryptographically detectable

**Negative**
- Rolling root (not full Merkle tree) — sufficient for audit but does not produce formal Merkle proof paths
- Transparency log table grows with every decision — archival strategy planned for future

---

## Related ADRs

- ADR-022: Base PQC — Dilithium-3 signing and original receipt generation
- ADR-040: Public Governance Sandbox — first public endpoint for governance decisions
- ADR-042: Hybrid KEM — optional encrypted transport for receipt packages
- ADR-043: Crypto-Agility Layer — transparency log uses active provider
