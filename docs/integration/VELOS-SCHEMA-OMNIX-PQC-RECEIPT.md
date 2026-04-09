# OMNIX Post-Quantum Mandate Receipt — Schema Specification
**For:** Naimat Khan / Velos  
**Prepared by:** Harold Nunes — OMNIX QUANTUM LTD  
**Date:** 2026-04-09  
**Version:** 1.0.0 (schema v6.5.4e)  
**ADR refs:** ADR-022 (PQC), ADR-031 (assurance tiers), ADR-043 (crypto-agility), ADR-044 (transparency chain)

---

## 1. Overview

Every decision emitted by OMNIX produces a **Post-Quantum Decision Receipt** — a self-contained, cryptographically signed JSON object that encodes the complete governance trail of a single enforcement decision, including all veto gates, compliance blocks, and assumption validity state.

The receipt is the atomic unit of the OMNIX evidence layer. It is:

- **Signed** using NIST FIPS 204 — Dilithium-3 (ML-DSA-65) at enterprise baseline, or Dilithium-5 (ML-DSA-87) at high-assurance tier
- **Chained** — each receipt includes the SHA-256 hash of its predecessor, forming a tamper-evident audit trail
- **Time-bounded** — carries explicit `ttl_epoch_ms` for T=0 gateway enforcement
- **Domain-agnostic** — identical schema for trading, Islamic credit, insurance, and robotics domains

---

## 2. Full JSON Schema

### 2.1 Complete Field Reference

```json
{
  "receipt_id":          "OMNIX-A3F7C1D92B0E",
  "timestamp":           "2026-04-09T14:23:01.847291+00:00",
  "issued_at_ms":        1744208581847,
  "ttl_epoch_ms":        1744208611847,
  "ttl_ms":              30000,

  "asset":               "BTC/USDT",
  "decision":            "BLOCK",

  "veto_chain":          [
    "AML: PASS — volume_score=12.4 frequency_score=0.3",
    "FRAUD: PASS — sentiment_score=0.12 reversal_risk=0.04",
    "SHARIA: BLOCK — gharar_score=0.81 exceeds threshold 0.35",
    "CAG: SKIPPED (upstream veto)"
  ],

  "policy_version":      "6.5.4e",
  "engine_version":      "6.5.4e",
  "prev_hash":           "a9f3c1d4e8b2...",

  "signing_provider":    "dilithium3",
  "content_hash":        "3f8e7a2c...",

  "signature":           "BASE64==...",
  "signature_algorithm": "Dilithium-3 (ML-DSA-65)",
  "signature_format":    "base64_pqc",
  "public_key":          "BASE64==...",

  "sharia_compliance":   { ... },
  "aml_compliance":      { ... },
  "fraud_compliance":    { ... },
  "jurisdiction_compliance": { ... },
  "context_admission":   { ... },
  "veto_type":           "SHARIA_BLOCK",
  "avm_result":          { ... }
}
```

---

### 2.2 Field-by-Field Specification

#### Identity Fields (always present)

| Field | Type | Description |
|---|---|---|
| `receipt_id` | `string` | Globally unique receipt identifier. Format: `OMNIX-{12 hex chars uppercase}`. Example: `OMNIX-A3F7C1D92B0E` |
| `timestamp` | `string` | ISO-8601 UTC timestamp of receipt generation. Example: `2026-04-09T14:23:01.847291+00:00` |

#### Timing Fields — **T=0 Gateway Critical** (always present from schema v6.5.4e)

| Field | Type | Description |
|---|---|---|
| `issued_at_ms` | `integer` | Unix epoch milliseconds when the receipt was generated. Derived from `timestamp`. This is the canonical "T=0 reference point". |
| `ttl_epoch_ms` | `integer` | Unix epoch milliseconds when the receipt expires. `ttl_epoch_ms = issued_at_ms + ttl_ms`. **Velos must reject receipts where `now_ms > ttl_epoch_ms`.** |
| `ttl_ms` | `integer` | Time-to-live in milliseconds. Default: `30000` (30 seconds). Configurable via `OMNIX_RECEIPT_TTL_MS` environment variable on the OMNIX side. |

**Velos ingestion rule for T=0:**
```python
now_ms = int(time.time() * 1000)
if now_ms > receipt["ttl_epoch_ms"]:
    return {"status": "REJECTED", "reason": "RECEIPT_EXPIRED"}
```

#### Decision Fields (always present)

| Field | Type | Description |
|---|---|---|
| `asset` | `string` | Asset symbol. Examples: `BTC/USDT`, `ETH/USD`, `UNKNOWN` |
| `decision` | `string` | Final governance decision, uppercased. Values: `BLOCK`, `ALLOW`, `PASS`, `UNKNOWN` |
| `veto_chain` | `array[string]` | Ordered list of gate verdicts. Each entry: `"GATE_NAME: RESULT — detail"`. Maximum 80 characters per entry. Empty array if no trace. |

#### Versioning Fields (always present)

| Field | Type | Description |
|---|---|---|
| `policy_version` | `string` | Policy version that evaluated this decision. Usually matches `engine_version`. |
| `engine_version` | `string` | OMNIX engine version. Current: `6.5.4e` |
| `prev_hash` | `string` | SHA-256 `content_hash` of the immediately preceding receipt in the chain. Empty string `""` for the first receipt. This forms the tamper-evident chain. |

#### Cryptographic Fields (always present)

| Field | Type | Description |
|---|---|---|
| `signing_provider` | `string` | Identifier of the active signing algorithm. Values: `dilithium3`, `dilithium5`, `ed25519`, `sha256`. **Bound into the signed payload to prevent algorithm confusion / downgrade attacks.** |
| `content_hash` | `string` | SHA-256 hex digest of the canonical JSON of all fields above (plus any present governance blocks), serialized with `sort_keys=True`. **This is what gets signed.** |
| `signature` | `string\|null` | Detached digital signature over `content_hash.encode('utf-8')`. Encoding depends on `signature_format` — see below. |
| `signature_algorithm` | `string` | Human-readable algorithm name. Examples: `"Dilithium-3 (ML-DSA-65)"`, `"SHA-256"`, `"NONE"` |
| `signature_format` | `string` | **Critical for Velos ingestion.** Disambiguates the encoding of the `signature` field. |
| `public_key` | `string\|null` | Base64-encoded public key corresponding to the signing key pair for this receipt. Required for asymmetric signature verification. `null` in SHA-256 fallback mode. |

#### `signature_format` Values

| Value | Meaning | How to verify |
|---|---|---|
| `base64_pqc` | `signature` is Base64-encoded raw PQC signature bytes | Decode Base64 → verify with Dilithium/ML-DSA using `public_key` |
| `hex_sha256_fallback` | `signature` is a hex string of `SHA-256(content_hash)`. Symmetric. No asymmetric signing. | `sha256(content_hash.encode()).hexdigest() == signature`. `public_key` will be `null`. |
| `NONE` | Signing failed. Receipt has no integrity guarantee. | **Reject this receipt.** |

---

### 2.3 Conditional Governance Blocks

These blocks appear **only when the corresponding gate was evaluated** for the decision. Each block is a dict with gate-specific internals (structure varies by domain and gate version).

| Field | Present when |
|---|---|
| `sharia_compliance` | Islamic finance gate was evaluated |
| `aml_compliance` | AML gate was evaluated |
| `fraud_compliance` | Fraud gate was evaluated |
| `jurisdiction_compliance` | Jurisdiction gate was evaluated |
| `context_admission` | CAG (Context Admission Gate) was evaluated |
| `veto_type` | `context_admission` is present and contains a `veto_type` string |
| `avm_result` | AVM (Assumption Validity Monitor) was evaluated |

#### `avm_result` Sub-Schema

```json
{
  "is_valid":          true,
  "snapshot_id":       "snap-abc123",
  "parameter_version": "v3.1",
  "drift_score":       0.12,
  "age_hours":         2.4,
  "pass_through":      false,
  "block_reason":      "DRIFT_EXCEEDED"
}
```

`block_reason` only present if AVM blocked the decision.

---

## 3. What Gets Hashed (content_hash contract)

The `content_hash` is computed as:

```python
canonical = json.dumps(payload_fields, sort_keys=True, ensure_ascii=True)
content_hash = sha256(canonical.encode('utf-8')).hexdigest()
```

**Fields included in the hash (in alphabetical order after sort_keys):**

Mandatory:
- `asset`
- `decision`
- `engine_version`
- `issued_at_ms` ← new (v6.5.4e)
- `policy_version`
- `prev_hash`
- `receipt_id`
- `signing_provider`
- `timestamp`
- `ttl_epoch_ms` ← new (v6.5.4e)
- `ttl_ms` ← new (v6.5.4e)
- `veto_chain`

Conditional (if present):
- `aml_compliance`
- `avm_result`
- `context_admission`
- `fraud_compliance`
- `jurisdiction_compliance`
- `sharia_compliance`
- `veto_type`

**Fields NOT included in the hash (detached signature pattern):**
- `content_hash` itself
- `signature`
- `signature_algorithm`
- `signature_format`
- `public_key`

---

## 4. Verification Algorithm for Velos

```python
import json, hashlib, base64, time

def verify_omnix_receipt(receipt: dict) -> dict:
    result = {"receipt_id": receipt.get("receipt_id"), "valid": False, "reason": None}

    # Step 1 — TTL check
    ttl_epoch_ms = receipt.get("ttl_epoch_ms")
    if ttl_epoch_ms is not None:
        now_ms = int(time.time() * 1000)
        if now_ms > ttl_epoch_ms:
            result["reason"] = "RECEIPT_EXPIRED"
            return result

    # Step 2 — Reconstruct payload for hashing
    MANDATORY = [
        "receipt_id", "timestamp", "issued_at_ms", "ttl_epoch_ms", "ttl_ms",
        "asset", "decision", "veto_chain",
        "policy_version", "engine_version", "prev_hash", "signing_provider"
    ]
    CONDITIONAL = [
        "sharia_compliance", "aml_compliance", "fraud_compliance",
        "jurisdiction_compliance", "context_admission", "veto_type", "avm_result"
    ]

    payload = {k: receipt[k] for k in MANDATORY if k in receipt}
    if payload.get("signing_provider") is None:
        payload.pop("signing_provider", None)
    for k in CONDITIONAL:
        if k in receipt:
            payload[k] = receipt[k]

    # Step 3 — Verify content_hash
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    computed_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if computed_hash != receipt.get("content_hash"):
        result["reason"] = "HASH_MISMATCH"
        return result

    # Step 4 — Verify signature based on signature_format
    sig_format = receipt.get("signature_format", "UNKNOWN")
    signature  = receipt.get("signature")
    public_key = receipt.get("public_key")
    message    = receipt["content_hash"].encode("utf-8")

    if sig_format == "base64_pqc":
        provider = receipt.get("signing_provider", "dilithium3")
        # Use pqc library matching the provider
        if provider == "dilithium3":
            from pqc.sign import dilithium3
            try:
                dilithium3.verify(base64.b64decode(signature), message, base64.b64decode(public_key))
                result["valid"] = True
            except Exception:
                result["reason"] = "SIGNATURE_INVALID"
        elif provider == "dilithium5":
            from pqc.sign import dilithium5
            try:
                dilithium5.verify(base64.b64decode(signature), message, base64.b64decode(public_key))
                result["valid"] = True
            except Exception:
                result["reason"] = "SIGNATURE_INVALID"

    elif sig_format == "hex_sha256_fallback":
        expected = hashlib.sha256(receipt["content_hash"].encode("utf-8")).hexdigest()
        result["valid"] = (expected == signature)
        if not result["valid"]:
            result["reason"] = "FALLBACK_HASH_MISMATCH"

    else:
        result["reason"] = f"UNKNOWN_SIGNATURE_FORMAT:{sig_format}"

    return result
```

---

## 5. Cryptographic Assurance Tiers

| Tier | Provider ID | Algorithm | NIST Standard | Security Level | Key Size (PK) | Sig Size |
|---|---|---|---|---|---|---|
| Enterprise Baseline (default) | `dilithium3` | Dilithium-3 (ML-DSA-65) | FIPS 204 | ~192-bit classical equivalent | 1952 bytes | ~3309 bytes |
| High-Assurance | `dilithium5` | Dilithium-5 (ML-DSA-87) | FIPS 204 | ~256-bit classical equivalent | 2592 bytes | ~4627 bytes |
| Dev/Test Fallback | `ed25519` | Ed25519 (classical) | — | 128-bit classical | 32 bytes | 64 bytes |
| No PQC available | `sha256` | SHA-256 HMAC (symmetric) | — | Non-asymmetric | N/A | 64 hex chars |

**Tier is set on the OMNIX side via `PQC_SIGNING_LEVEL` env var (3 or 5). Velos must dispatch verification based on `signing_provider` field in the receipt.**

---

## 6. Receipt Chaining (Audit Trail)

Each receipt carries `prev_hash` = `content_hash` of the immediately preceding receipt. This forms a singly-linked chain:

```
Receipt[n].prev_hash == Receipt[n-1].content_hash
```

A chain break means either:
- A receipt was injected out of order
- A receipt was tampered with
- The chain was restarted (first receipt has `prev_hash = ""`)

---

## 7. Integration Checklist for Velos T=0 Gateway

- [ ] Extract `ttl_epoch_ms` — reject if `now_ms > ttl_epoch_ms`
- [ ] Extract `signature_format` — dispatch verification accordingly (do NOT assume base64)
- [ ] Extract `signing_provider` — determines which PQC algorithm to use for verification
- [ ] Install `pypqc` on Velos side: `pip install pypqc`
- [ ] Verify `content_hash` by recomputing from the payload (exclude `signature`, `public_key`, `signature_format`, `signature_algorithm`, `content_hash` itself)
- [ ] Check `decision` field value — `BLOCK` means OMNIX has vetoed the action
- [ ] Read `veto_chain` array for the specific gate(s) that blocked
- [ ] Treat `signature_format = "NONE"` as invalid receipt — reject

---

## 8. Example: Full BLOCK Receipt (Trading Domain)

```json
{
  "receipt_id":          "OMNIX-A3F7C1D92B0E",
  "timestamp":           "2026-04-09T14:23:01.847291+00:00",
  "issued_at_ms":        1744208581847,
  "ttl_epoch_ms":        1744208611847,
  "ttl_ms":              30000,
  "asset":               "BTC/USDT",
  "decision":            "BLOCK",
  "veto_chain": [
    "AML: PASS — volume_score=12.4 frequency_score=0.3",
    "FRAUD: PASS — sentiment_score=0.12 reversal_risk=0.04",
    "SHARIA: BLOCK — gharar_score=0.81 exceeds threshold 0.35",
    "CAG: SKIPPED (upstream veto)"
  ],
  "policy_version":      "6.5.4e",
  "engine_version":      "6.5.4e",
  "prev_hash":           "a9f3c1d4e8b2fc71...",
  "signing_provider":    "dilithium3",
  "sharia_compliance": {
    "admitted":          false,
    "evaluation_state":  "EVALUATED",
    "violation":         "GHARAR_EXCESSIVE",
    "gharar_score":      0.81,
    "debt_ratio":        0.0
  },
  "content_hash":        "3f8e7a2c91bd...",
  "signature":           "BASE64_DILITHIUM3_SIGNATURE==",
  "signature_algorithm": "Dilithium-3 (ML-DSA-65)",
  "signature_format":    "base64_pqc",
  "public_key":          "BASE64_PUBLIC_KEY=="
}
```

---

## 9. Schema Versioning

| Schema Version | Released | Changes |
|---|---|---|
| 6.5.4e (this) | 2026-04-09 | Added `issued_at_ms`, `ttl_epoch_ms`, `ttl_ms`, `signature_format`. Verifier now checks TTL expiry and exposes `is_expired`, `age_ms`. |
| Pre-6.5.4e | — | `timestamp` only. No TTL fields. `signature_format` absent — assume `base64_pqc` if `public_key` present, else `hex_sha256_fallback`. |

**Backward compatibility:** Receipts generated before this version will not have `ttl_epoch_ms`. Velos should treat absent `ttl_epoch_ms` as non-expiring (legacy receipts). Use `signature_format` absence as indicator of legacy receipt — fall back to provider heuristic.

---

*Document prepared by Harold Nunes. OMNIX QUANTUM LTD — Eureka GCC Dubai 2026 Semifinalist.*
