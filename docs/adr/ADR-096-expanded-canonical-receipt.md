# ADR-096: Expanded Canonical Receipt — Full Execution Proof (ADR-095 Gap Resolution)

**Status:** ACCEPTED  
**Date:** April 2026  
**Author:** Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD, United Kingdom  
**Scope:** `omnix_web/api/proof_layer.py` — `_build_execution_proof()`, `_build_authority_binding()`, `_build_checkpoint_proof()`, `_compute_full_canonical_hash()`  
**Resolves:** ADR-095 §4 known gap — "hash covers only 4 fields"  
**Patent Reference:** OMNIX-PAT-2026-015 §4.3–4.4

---

## Context

ADR-095 documented a known limitation in the OMNIX receipt hash:

> *"Limitation: The hash does not cover `amount`, `jurisdiction`, or `operation`. These are stored in `encrypted_payload` (metadata JSON) but not hashed. This is a known gap — the hash covers the governance decision itself, not the full evaluation context."*

The 4-field hash (`receipt_id`, `timestamp`, `asset`, `decision`) covers the governance outcome but not the execution context. An auditor or regulator cannot verify from the hash alone:

- **Which jurisdiction** governed the decision
- **Which operation type** was evaluated (SPOT vs LEVERAGED)
- **Which ethical constraints** were active (SHARIA, ESG)
- **What each checkpoint scored** — the granular gate-level proof
- **Which client and policy** authorized the evaluation
- **The exact nanosecond** at which execution occurred

This gap becomes critical when institutional counterparties demand what Naimat's framework calls "execution physics" — immutable, mathematically verifiable proof of exactly what authority was bound to a specific payload at the moment of execution.

OMNIX already had PQC signing (Dilithium-3), W3C VC format, and DID-based issuer identity (ADR-082, ADR-084, ADR-078). This ADR closes the content coverage gap.

---

## Decision

Every `/evaluate` response now includes an `execution_proof` block containing:

### 1. `authority_binding` — Who authorized, under which conditions

```json
{
  "client_id":        "PUBLIC_EVALUATE",
  "policy_version":   "EVL-1.0",
  "engine_version":   "6.5.4e",
  "jurisdiction":     "UAE",
  "operation":        "SPOT",
  "ethical_flags":    ["SHARIA"],
  "layer0_status":    "PASSED",
  "authorized_by":    "OMNIX-PAT-2026-015",
  "governance_model": "Layer0→Layer1→PQC (OMNIX 4-layer)",
  "issuer_did":       "did:web:omnixquantum.net"
}
```

### 2. `checkpoint_proof` — Every gate decision in the signed payload

```json
[
  {
    "id":        "CP-0",
    "name":      "Signal Integrity Validation",
    "signal":    "signal_integrity",
    "score":     75.0,
    "threshold": 60.0,
    "condition": "gte",
    "result":    "PASS",
    "optional":  true
  },
  ...
  {
    "id":        "CP-4",
    "name":      "Trend Persistence",
    "signal":    "trend_persistence",
    "score":     46.8,
    "threshold": 50.0,
    "condition": "gte",
    "result":    "VETO",
    "optional":  false
  }
]
```

### 3. `execution_proof` — Canonical hash v2 + PQC signature

```json
{
  "hash_version":       "v2",
  "hash_algorithm":     "SHA-256",
  "canonical_hash":     "<sha256_hex>",
  "hash_coverage": [
    "receipt_id",
    "execution_nanosecond",
    "asset",
    "decision",
    "authority_binding.client_id",
    "authority_binding.policy_version",
    "authority_binding.jurisdiction",
    "authority_binding.operation",
    "authority_binding.ethical_flags",
    "authority_binding.layer0_status",
    "checkpoint_proof[*].id",
    "checkpoint_proof[*].score",
    "checkpoint_proof[*].threshold",
    "checkpoint_proof[*].result",
    "checkpoints_passed",
    "checkpoints_total"
  ],
  "execution_nanosecond": 1745612345678901234,
  "signature":           "<dilithium3_base64>",
  "signature_algorithm": "Dilithium-3",
  "public_key":          "<dilithium3_public_key_base64>",
  "pqc_standard":        "NIST FIPS 204 (ML-DSA / Dilithium-3)",
  "issuer_did":          "did:web:omnixquantum.net",
  "verification_url":    "https://omnixquantum.net/verify/<receipt_id>",
  "independently_verifiable": true,
  "patent_reference":    "OMNIX-PAT-2026-015 §4.3–4.4",
  "adr_reference":       "ADR-096"
}
```

### 4. `verifiable_credential` — W3C VC wrapping the execution_proof

The W3C VC (ADR-082/ADR-084) is extended to include `authority_binding` and `checkpoint_proof` in the `credentialSubject`. Type extended to `OmnixExecutionPhysicsCredential`.

---

## Hash Version Strategy

| Version | Coverage | Fields | Used by |
|---------|----------|--------|---------|
| v1 | Legacy — 4 fields | receipt_id, timestamp, asset, decision | `content_hash` in DB (ADR-095) |
| v2 | Full execution context | 16 field paths including all checkpoints | `execution_proof.canonical_hash` (this ADR) |

**Backward compatibility:** `content_hash` (v1) in the `decision_receipts` DB table is unchanged. The `/verify` endpoint continues to validate v1 hashes for all existing receipts. New receipts carry BOTH v1 (DB column) and v2 (`execution_proof.canonical_hash`).

---

## Why This Exceeds the State of the Market

The institutional benchmark (per Naimat's framework and SEC/FCA guidance on AI agent governance) requires:

| Requirement | Market Standard | OMNIX ADR-096 |
|-------------|-----------------|---------------|
| Immutability | SHA-256 hash | SHA-256 (v2) + Dilithium-3 PQC signature |
| Temporal precision | Millisecond | **Nanosecond** (`execution_nanosecond`) |
| Authority binding | Operator ID | Full binding: client_id + policy_version + jurisdiction + operation + ethical_flags + layer0_status |
| Checkpoint evidence | Aggregate pass/fail | **Per-checkpoint proof**: id, name, signal, score, threshold, condition, result |
| Standard interoperability | Proprietary | **W3C Verifiable Credential** (JSON-LD) |
| Issuer identity | Vendor-asserted | **DID** (`did:web:omnixquantum.net`) — resolvable independently |
| Quantum resistance | None / RSA | **Dilithium-3** (NIST FIPS 204) |
| Regulatory coverage | Single jurisdiction | **10-framework semantics** (ADR-085): EU AI Act, GDPR, DORA, FATF, UK FCA, US SEC, MAS, UAE CBUAE, SAMA, FSB G20 |
| Pre-execution vs post-execution | Post-execution logging | **Pre-execution enforcement** — Layer 0 blocks inadmissible requests before they exist |

---

## Key Architectural Distinction

Naimat's framework (Velos Systems) targets **post-execution audit proof** — cryptographic receipts for what an agent *did* at 3:00 AM, usable in regulatory or legal proceedings.

OMNIX ADR-096 operates at a different layer: the receipt proves not only *what happened* but *what was structurally prevented from happening*. The execution_proof is issued at T=0 — the exact nanosecond of the governance gate evaluation — before any action reaches the execution environment.

> *"Without that separation [between probabilistic generation and deterministic admissibility enforcement], governance remains consultative. With it, governance becomes structural."*  
> — John M. Willis (LinkedIn, April 2026)

ADR-096 makes the structural enforcement cryptographically provable.

---

## HTTP Response Headers Added

| Header | Value | Purpose |
|--------|-------|---------|
| `X-OMNIX-Receipt-ID` | `<receipt_id>` | Machine-parseable receipt reference |
| `X-OMNIX-Execution-NS` | `<nanosecond>` | T=0 execution timestamp |
| `X-OMNIX-Sig-Mode` | `Dilithium-3` / `SHA-256-FALLBACK` | Signature mode for quick audit |

---

## Audit Pass — April 2026 (v2 Hardening)

Following initial implementation, an institutional-grade audit identified 5 risks. All were resolved in the same session:

### Fix 1 — Hash Determinism (`_normalize_float`, `_build_checkpoint_proof`)

Introduced `_normalize_float()`:
- `None → "null"` string (prevents null/empty-string ambiguity in canonical JSON)
- `float → round(v, 6)` (prevents platform-dependent repr differences: `0.1` vs `0.10000000000000001`)
- `int` and other types pass through unchanged

`_build_checkpoint_proof()` now sorts entries by `id` (CP-0 … CP-10) to prevent list-order-dependent hash variation.

### Fix 2 — Receipt Versioning

`execution_proof.receipt_version: "v2"` added explicitly. Verifiers and future migration scripts can now distinguish v1 (4-field `content_hash`) from v2 (`execution_proof.canonical_hash`) receipts without ambiguity.

### Fix 3 — Authority Binding Completeness

`authority_binding` now includes all required institutional fields:
- `policy_id` — canonical identifier (`OMNIX-EVL-1.0`)
- `actor` — system actor string (`OMNIX-GOVERNANCE-ENGINE`)
- `timestamp_utc` — ISO-8601 UTC timestamp of evaluation (T=0 reference, from `evaluated_at`)
- `ethical_flags` — sorted alphabetically for hash stability

### Fix 4 — Nanosecond Serialization

`execution_nanosecond` is serialized as `str(int(v))` in both the canonical hash payload and the `execution_proof` response block. This eliminates float conversion risk at JSON serialization, DB persistence, and API transport layers. The value is an integer in `time.time_ns()` and treated as string in the hash — deterministic on all platforms.

### Fix 5 — External Verifiability Confirmed

External verifier test confirmed: a third party can reconstruct `canonical_hash` using only the fields present in the API response (no OMNIX system access required):

```python
import json, hashlib

canonical = {
    "hash_version":         "v2",
    "receipt_id":           str(response["receipt_id"]),
    "execution_nanosecond": str(int(response["execution_proof"]["execution_nanosecond"])),
    "asset":                str(response["governance_summary"]["asset"]),
    "decision":             str(response["status"]),
    "authority_binding":    response["authority_binding"],
    "checkpoint_proof":     response["checkpoint_proof"],
    "checkpoints_passed":   int(response["execution_proof"]["checkpoints_passed"]),
    "checkpoints_total":    int(response["execution_proof"]["checkpoints_total"]),
}
# Exact serializer — must match execution_proof.serializer field
serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode("utf-8")
recomputed  = hashlib.sha256(serialized).hexdigest()
assert recomputed == response["execution_proof"]["canonical_hash"]  # PASSES
```

The `public_key_fingerprint` (`SHA256:<b64>`) enables verifiers to confirm the Dilithium-3 key against the DID document before verifying the signature.

### Hardening Pass — Last 5% (same session)

Four additional structural improvements applied after the initial 5 audit fixes:

**Fix 6 — Single canonical serializer (`_canonical_json`)**  
A dedicated `_canonical_json(obj) -> bytes` function is the ONLY code path that produces bytes for hashing. It enforces `sort_keys=True, ensure_ascii=True, separators=(',', ':')` — no whitespace, deterministic in all languages. The exact serializer string is exposed in `execution_proof.serializer` so any verifier can match it exactly.

**Fix 7 — Frozen coverage list (`_HASH_V2_COVERAGE`, `_HASH_V2_DETERMINISM_RULES`)**  
The 19-path coverage list and 8 determinism rules are now module-level `tuple` constants — never dynamically generated. Changing them requires a new `hash_version`. Both are referenced from the constant in `_build_execution_proof()`, eliminating any risk of inconsistency between the actual hash and what the `hash_coverage` field claims.

**Fix 8 — Numeric checkpoint sort (`_cp_sort_key`)**  
A dedicated `_cp_sort_key(id)` function extracts the numeric suffix from checkpoint ids (CP-0…CP-10) for correct numeric ordering. Lexicographic sort would place CP-10 before CP-2 (`"1" < "2"`). The new sort guarantees: `CP-0 < CP-1 < … < CP-9 < CP-10` on every runtime, every platform.

**Fix 9 — Fingerprint definition frozen (`_fingerprint_public_key`)**  
A formal `_fingerprint_public_key(public_key_b64) -> str` function with frozen definition:

```
fingerprint = "SHA256:" + base64(sha256(base64_decode(public_key_b64)))
```

Matches SSH/TLS convention. The definition is also exposed in `execution_proof.fingerprint_definition` so institutional counterparties can pin the key using standard tooling without reading source code.

---

## Consequences

**Positive:**
- Hash coverage gap (ADR-095 §4) is fully resolved
- Checkpoint-level evidence is now cryptographically bound to every receipt
- Authority binding provides the exact context regulators and litigators require
- Nanosecond precision exceeds any known institutional receipt standard
- W3C VC extends to `OmnixExecutionPhysicsCredential` type — distinct from generic governance VCs
- Backward compatible — existing receipts and `/verify` are unaffected
- External hash reconstruction confirmed — no OMNIX system access required for verification
- `public_key_fingerprint` enables key-pinning by institutional counterparties

**Negative / Future Work:**
- v2 hash is not yet stored in a dedicated DB column — `execution_proof` is returned in response and cache but not persisted separately (ADR-097 planned: persist `execution_proof.canonical_hash` as `canonical_hash_v2`)
- Chain verification (WAL-based, ADR-096 planned revision) still pending

---

## References

- ADR-095: Receipt Retention Policy (documented the v1 hash gap this ADR resolves)
- ADR-085: PQC Evidence & Receipt Layer (Dilithium-3 signing infrastructure)
- ADR-082: W3C Verifiable Credentials — Public Governance Sandbox
- ADR-084: W3C VC Endpoint + Interoperability Layer
- ADR-078: Signing Key Persistence (stable Dilithium-3 keypair)
- OMNIX-PAT-2026-015: Structural Admissibility Engine (§4.3 authority binding, §4.4 checkpoint provenance)
- NIST FIPS 204: Module-Lattice-Based Digital Signature Standard (ML-DSA / Dilithium-3)
