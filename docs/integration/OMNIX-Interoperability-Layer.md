# OMNIX Interoperability Layer — ADR-084
**Version:** 1.0 — 14 April 2026  
**Prepared by:** Harold Nunes — OMNIX QUANTUM LTD  
**Status:** Production

---

## Overview

OMNIX decisions are fully auditable within the OMNIX system. This document describes the **Interoperability Layer** — the set of standards and endpoints that allow external systems, regulators, and partners to independently interpret and validate OMNIX receipts **without requiring OMNIX's internal logic**.

The layer consists of:

| Component | Description |
|---|---|
| **JSON-LD Context** | Semantic definitions for every receipt field |
| **JSON Schema** | Machine-readable schema for structural validation |
| **W3C VC Endpoint** | Converts any OMNIX receipt into a W3C Verifiable Credential |
| **Jurisdiction Semantics** | Explains each checkpoint result under 5 regulatory frameworks |

---

## 1. JSON-LD Context

**URL:** `https://omnixquantum.net/schemas/omnix-receipt-v1.jsonld`  
**MIME type:** `application/ld+json`  
**Cache:** 24 hours (`Cache-Control: public, max-age=86400`)

The context file maps every OMNIX receipt field to a semantic URI, enabling:
- Linked Data integration
- RDF triple stores (Stardog, Apache Jena, GraphDB)
- Semantic web reasoning
- DID-linked verifiable data registries

### Key Mappings

| OMNIX Field | Semantic URI |
|---|---|
| `receipt_id` | `https://omnixquantum.net/schemas/v1#receiptId` |
| `decision` | `https://omnixquantum.net/schemas/v1#decision` |
| `veto_chain` | `https://omnixquantum.net/schemas/v1#vetoChain` |
| `aml_compliance` | `https://omnixquantum.net/schemas/v1#amlCompliance` / `https://www.fatf-gafi.org/ontology#Recommendation` |
| `jurisdiction_compliance` | `https://omnixquantum.net/schemas/v1#jurisdictionCompliance` / EU AI Act ontology |

---

## 2. JSON Schema

**URL:** `https://omnixquantum.net/schemas/omnix-receipt-schema-v6.5.4e.json`  
**MIME type:** `application/schema+json`  
**Spec:** JSON Schema 2020-12

External systems can validate any OMNIX receipt against this schema independently:

```bash
# Example using ajv-cli
npx ajv validate \
  -s https://omnixquantum.net/schemas/omnix-receipt-schema-v6.5.4e.json \
  -d your-receipt.json
```

### Required Fields

- `receipt_id` — `OMNIX-{12-char hex}` pattern
- `timestamp` — ISO 8601 UTC
- `asset` — evaluated entity
- `decision` — `APPROVED | BLOCKED | HOLD | UNKNOWN`
- `veto_chain` — array of checkpoint result strings
- `policy_version`, `engine_version`
- `content_hash` — SHA-256 hex (64 chars)

---

## 3. W3C Verifiable Credential Endpoint

### Request

```
POST https://omnixquantum.net/api/governance/receipt/vc
Content-Type: application/json

{
  "receipt": { ...full OMNIX receipt JSON... }
}
```

### Validation steps performed before VC issuance

1. Receipt has required fields (`receipt_id`, `content_hash`)
2. `content_hash` matches the canonical payload — tampering detected and rejected (HTTP 409)
3. Receipt domain is recognised

### Response

```json
{
  "verifiable_credential": { ...W3C VC JSON-LD... },
  "hash_verified": true,
  "schema_url": "https://omnixquantum.net/schemas/omnix-receipt-schema-v6.5.4e.json",
  "context_url": "https://omnixquantum.net/schemas/omnix-receipt-v1.jsonld",
  "w3c_spec": "https://www.w3.org/TR/vc-data-model/"
}
```

### VC Structure

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://omnixquantum.net/schemas/omnix-receipt-v1.jsonld"
  ],
  "type": ["VerifiableCredential", "OmnixGovernanceCredential"],
  "issuer": {
    "id": "did:web:omnixquantum.net",
    "name": "OMNIX Quantum Ltd"
  },
  "issuanceDate": "2026-04-14T10:00:00+00:00",
  "expirationDate": "2027-04-14T10:00:00+00:00",
  "credentialSubject": {
    "receipt_id": "OMNIX-A3F7C1D92B0E",
    "decision": "BLOCKED",
    "domain": "trading",
    "jurisdiction_semantics": { ... }
  },
  "proof": {
    "type": "Dilithium2021",
    "verificationMethod": "did:web:omnixquantum.net#pqc-key-1",
    "proofValue": "BASE64_DILITHIUM3_SIG",
    "signatureAlgorithm": "Dilithium-3"
  }
}
```

### Proof Types by Algorithm

| PQC Algorithm | VC Proof Type |
|---|---|
| Dilithium-3 (ML-DSA-65) | `Dilithium2021` |
| ML-DSA-65 | `MlDsa2024` |
| Falcon-512 | `Falcon2021` |
| Ed25519 | `Ed25519Signature2020` |
| SHA-256 fallback | `OmnixHashProof2026` |

---

## 4. Jurisdiction Semantics on `/verify`

The public verification endpoint now returns a `jurisdiction_semantics` block:

```
GET https://omnixquantum.net/api/public/verify/OMNIX-A3F7C1D92B0E
```

```json
{
  "found": true,
  "decision": "BLOCKED",
  "jurisdiction_semantics": {
    "omnix_decision_meaning": "The OMNIX engine evaluated this trading decision through 11 governance checkpoints. One or more checkpoints blocked the decision — execution was suppressed.",
    "checkpoints_passed_count": 9,
    "checkpoints_blocked_count": 2,
    "blocked_gates": [
      "Stress Testing blocked → CP-6 failed",
      "AML Screening blocked → CP-9 failed"
    ],
    "regulatory_interpretation": {
      "EU_AI_ACT": {
        "label": "EU Artificial Intelligence Act",
        "jurisdiction": "European Union",
        "interpretation": "Decision blocked by OMNIX governance — not presented to end user. EU AI Act Article 14 (Human Oversight) satisfied...",
        "decision_effect": "BLOCKED"
      },
      "FATF": {
        "label": "FATF — Financial Action Task Force",
        "jurisdiction": "International (G7 + 37 members)",
        "interpretation": "AML gate triggered BLOCK. Decision suppressed before execution in compliance with FATF Recommendation 29..."
      },
      "GDPR": { ... },
      "DORA": { ... },
      "UAE_CBUAE": { ... }
    },
    "schema_url": "https://omnixquantum.net/schemas/omnix-receipt-schema-v6.5.4e.json",
    "context_url": "https://omnixquantum.net/schemas/omnix-receipt-v1.jsonld",
    "note": "This semantics block is provided to enable external systems to interpret OMNIX receipts without requiring knowledge of OMNIX internal logic."
  }
}
```

---

## 5. Regulatory Frameworks Covered

| Framework | Jurisdiction | OMNIX Checkpoints |
|---|---|---|
| EU AI Act | European Union | CP-1, CP-2, CP-3, CP-6, CP-7, CP-9, CP-11 |
| FATF Recommendations | International | CP-9 (AML), CP-10 (Fraud) |
| GDPR Article 22 | European Union | CP-7, CP-11 |
| DORA | EU Financial Sector | CP-2, CP-3, CP-5, CP-6, CP-8, CP-10 |
| NIST AI RMF | USA / International | All 11 checkpoints |
| ISO 42001 | International | CP-1, CP-4, CP-7, CP-8, CP-11 |
| Basel III | Banking / International | CP-2, CP-3, CP-5, CP-6 |
| UAE CBUAE AI Framework | UAE | CP-7, CP-9, CP-11 |

---

## 6. Interface Boundaries (for External Integrators)

Per OMNIX's Mutual NDA with partners (ADR-084, interface-level interaction principle):

- External systems receive **inputs, outputs, and schema definitions** only
- OMNIX internal logic, model weights, and checkpoint algorithms are **not exposed**
- The JSON-LD context and JSON Schema constitute the complete public interface contract
- No knowledge of OMNIX internals is required to validate or interpret a receipt

---

## 7. Federated Trust Layer — ADR-085

The federated trust layer makes OMNIX receipts independently verifiable by any external system, without requiring access to OMNIX's internal DB or knowledge of OMNIX internals.

### 7.1 DID Document — `did:web:omnixquantum.net`

The OMNIX DID is now resolvable:

```
GET https://omnixquantum.net/.well-known/did.json
Accept: application/did+json
```

Returns the full DID Document with:
- Live PQC public key (runtime ephemeral, always current)
- Verification methods: `#pqc-key-1`, `#governance-key-1`
- Service endpoints: governance API, receipt verifier, VC issuer, trust registry, schema repository

### 7.2 Trust Registry

```
GET https://omnixquantum.net/api/trust/registry
```

Returns:
- OMNIX as a trusted issuer with live public key and supported schemas
- Pending partners (Skilligen HDI, Velos Capital) with their DIDs and trust levels
- Step-by-step guide for external systems to verify OMNIX receipts
- All supported regulatory frameworks

### 7.3 Independent Stateless Verifier

```
POST https://omnixquantum.net/api/trust/verify
Content-Type: application/json

{ "receipt": { ...OMNIX receipt... } }
// OR
{ "verifiable_credential": { ...W3C VC... } }
```

**No DB access required. No OMNIX account required.**

Verifies:
1. SHA-256 content hash — receipt payload is intact
2. PQC signature — cryptographic authenticity (if public key embedded)
3. Jurisdiction semantics — what the decision means per regulatory framework
4. Trust chain — confirms issuer DID and links to registry

Response includes:
- `hash_valid`, `signature_valid`, `overall_valid`
- `jurisdiction_semantics` (EU AI Act, FATF, GDPR, DORA, UAE CBUAE)
- `trust_chain` with all resolution URLs

### 7.4 Regulatory Frameworks Catalog

```
GET https://omnixquantum.net/api/trust/frameworks
```

Returns full mapping of 11 checkpoints × 8+ regulatory frameworks with descriptions, article references, and applicability scope.

### 7.5 Trust Layer Health

```
GET https://omnixquantum.net/api/trust/health
```

Live status of all 6 interoperability components: DID document, JSON-LD context, JSON Schema, signing key, VC converter, independent verifier.

---

## 8. Complete API Surface — Interoperability Layer

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/.well-known/did.json` | DID Document — resolves `did:web:omnixquantum.net` |
| `GET` | `/api/trust/registry` | Trust Registry — issuers, keys, schemas, partners |
| `POST` | `/api/trust/verify` | Independent Verifier — no DB, no OMNIX account needed |
| `GET` | `/api/trust/frameworks` | Regulatory Framework Catalog |
| `GET` | `/api/trust/health` | Interoperability layer health check |
| `POST` | `/api/governance/receipt/vc` | Convert receipt → W3C VC |
| `GET` | `/api/public/verify/<id>` | Verify by receipt ID (includes jurisdiction semantics) |
| `GET` | `/schemas/omnix-receipt-v1.jsonld` | JSON-LD Context |
| `GET` | `/schemas/omnix-receipt-schema-v6.5.4e.json` | JSON Schema |

---

## 9. Partner Onboarding — How to Add a Trusted Counterparty

To add Skilligen HDI, Velos Capital, or any other partner to the OMNIX trust chain:

1. Partner publishes their own `/.well-known/did.json` at their domain
2. Partner shares their DID (e.g. `did:web:skilligen.com`) with OMNIX
3. OMNIX adds their DID to the trust registry under `trusted_issuers`
4. Both systems can now independently verify each other's evidence without a shared DB
5. Joint decisions carry both DIDs in the `proof` block

---

*OMNIX QUANTUM LTD — 71-75 Shelton Street, Covent Garden, London WC2H 9JQ*  
*omnixquantum.net · harold@omnixquantum.net*
