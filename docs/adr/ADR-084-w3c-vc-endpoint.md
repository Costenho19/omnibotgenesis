# ADR-084: W3C Verifiable Credential Endpoint + Interoperability Layer

**Status:** ACCEPTED  
**Date:** April 2026  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Scope:** `omnix_web/api/omnix_engine/receipt_to_vc.py` · `omnix_web/api/gov_blueprint.py` · `omnix_web/api/server.py` · `omnix_web/public/schemas/`

**Full institutional reference:** `docs/integration/OMNIX-Interoperability-Layer.md`

---

## Context

ADR-082 added W3C VC wrapping to the public sandbox response. ADR-084 extends this to
the B2B governance API and adds three public interoperability endpoints:

1. A dedicated `POST /api/governance/receipt/vc` endpoint for receipt → VC conversion
2. A public JSON-LD context file served at `/schemas/omnix-receipt-v1.jsonld`
3. A public JSON Schema file served at `/schemas/omnix-receipt-schema-v6.5.4e.json`

---

## Endpoints

### 1. `POST /api/governance/receipt/vc`

Converts any OMNIX receipt JSON into a W3C Verifiable Credential.

| Property | Value |
|----------|-------|
| Auth | None — public interoperability endpoint |
| Rate limit | 30 requests/minute |
| Input | `{ "receipt": { ...OMNIX receipt object... } }` |
| Output | W3C VC JSON-LD object |
| Validation | receipt_id + content_hash required; expiry checked |

**Error cases:**
- Missing/invalid `receipt` field → 400
- Missing `receipt_id` or `content_hash` → 400

### 2. `GET /schemas/omnix-receipt-v1.jsonld`

Serves the public OMNIX JSON-LD context file.

| Property | Value |
|----------|-------|
| MIME | `application/ld+json` |
| Cache | `public, max-age=86400` (24h) |
| CORS | `Access-Control-Allow-Origin: *` |
| Header | `X-OMNIX-Schema-Version: 1.0` |

Used by external verifiers to resolve `@context` references in OMNIX VCs.

### 3. `GET /schemas/omnix-receipt-schema-v6.5.4e.json`

Serves the public JSON Schema for OMNIX receipt validation.

| Property | Value |
|----------|-------|
| MIME | `application/schema+json` |
| Cache | `public, max-age=86400` (24h) |
| CORS | `Access-Control-Allow-Origin: *` |
| Header | `X-OMNIX-Schema-Version: 6.5.4e` |

Allows external systems to validate OMNIX receipt structure without contacting OMNIX.

---

## Core converter module

**File:** `omnix_web/api/omnix_engine/receipt_to_vc.py`

| Function | Purpose |
|----------|---------|
| `build_w3c_vc(receipt)` | Convert OMNIX receipt dict → W3C VC JSON-LD |
| `build_jurisdiction_semantics(decision, asset, domain)` | Build 10-framework regulatory mapping (ADR-085) |
| `independent_verify(receipt)` | Verify receipt hash + signature against trust registry |

---

## DID document

OMNIX publishes its DID at `did:web:omnixquantum.net`. External verifiers can resolve:

```
https://omnixquantum.net/.well-known/did.json
```

The DID document contains the Dilithium-3 public key used to verify all OMNIX receipt
signatures.

---

## Velos integration

The Velos Capital partner integration uses ADR-084 endpoints directly:

```
Naimat's system
    → POST /api/governance/evaluate  (X-API-Key header)
    → OMNIX runs 11-checkpoint pipeline
    → Response includes VC under `verifiable_credential` key
    → Naimat pushes receipt to velos-gateway (60s Auth_Hash window)
    → External verifier calls POST /api/governance/receipt/vc for VC conversion
```

Full schema: `docs/integration/VELOS-SCHEMA-OMNIX-PQC-RECEIPT.md`

---

## References

- ADR-082: W3C VC for public sandbox (same VC structure, different entry point)
- ADR-083: Enterprise Bot Security (bot-side complement)
- ADR-085: Cross-Border Semantic Governance (jurisdiction_semantics expansion)
- `docs/integration/OMNIX-Interoperability-Layer.md` — full institutional reference
- `docs/integration/VELOS-SCHEMA-OMNIX-PQC-RECEIPT.md` — Velos schema spec
