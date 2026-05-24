# ADR-188 — OMNIX Settlement Gate (OSG)

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-24  
**Supersedes:** —  
**Implements:** ADR-186 (PoGR) · ADR-187 (PoGR API)  
**Related:** ADR-184 (OGR) · ADR-183 (CTCHC) · ADR-156 (ATF DR)  
**Blueprint:** `omnix_web/api/osg_blueprint.py`  
**Product ID:** OMNIX-OSG-2026-001

---

## Context

### The Settlement Gap

ADR-186 introduced the Proof of Governance Public Registry (PoGR) — the world's first publicly verifiable, post-quantum-anchored registry of AI governance certificates. A PoGC proves that a governance session was correctly executed.

What it does not do is enforce that a downstream *consequence* — a financial settlement, a contract execution, a liquidity commitment — is bound to that proof before it happens.

This is the gap Brent Heckerman (CEO, Eterna.AI) identified in a direct message to Harold Nunes on 2026-05-24:

> "El invariante A_child ≤ A_parent es la mitad aguas arriba del problema. Hemos estado construyendo la mitad downstream: un punto de estrangulamiento de tiempo de compromiso fallo-cerrado que produce certificados criptográficos en la unión entre intención y liquidación."
> — Brent Heckerman, CEO Eterna.AI, LinkedIn, 24 May 2026

OMNIX already has everything upstream:
- **ATF (ADR-156):** who can propose — cryptographic delegation A_child ≤ A_parent
- **OGR (ADR-184):** what the agent did — every turn sealed with BAR + CCS + CTCHC
- **PoGR (ADR-186):** public proof that the session was governed correctly

What OMNIX lacked was the **commitment-time enforcement gate** — the moment where the downstream consequence (settlement, execution, payment) is blocked unless a valid PoGC exists.

This ADR introduces that gate as a first-class OMNIX component, designed to be ledger-agnostic (XRPL, Ethereum, SWIFT, FIX) but with XRPL/RLUSD as the reference implementation.

### Why OMNIX Builds This Instead of Composing with a Third Party

Allowing a third party to own the settlement enforcement layer while OMNIX owns only the governance layer creates a structural dependency that severs the end-to-end audit chain. The forensic value of OMNIX — a single immutable trail from human intent to consequence — is preserved only if the enforcement gate is part of the same signature chain.

---

## Decision

Introduce the **OMNIX Settlement Gate (OSG)** — a commitment-time enforcement layer that validates the existence of a valid PoGC before approving a downstream settlement.

### Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                OMNIX ATF Stack (upstream — ADR-156–186)            │
│  Human Intent → ATF Delegation → OGR Session → CTCHC Seal → PoGC  │
└─────────────────────────────┬──────────────────────────────────────┘
                              │  pogc_id included in settlement payload
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│              OMNIX Settlement Gate (OSG) — ADR-188                 │
│                                                                    │
│  POST /v1/osg/validate                                             │
│  ├── Assert PoGC exists in PoGR (ADR-186)                         │
│  ├── Assert PoGC.status == ACTIVE                                  │
│  ├── Assert PoGC.expires_at > settlement_deadline (OSG-INV-004)   │
│  ├── Assert settlement_amount ≤ PoGC.authorized_amount (if set)   │
│  ├── Compute ValidationReceipt (VR) with PQC signature            │
│  └── INSERT INTO osg_validation_receipts (append-only)            │
│                                                                    │
│  Result: APPROVED (VR-ID) | REJECTED (reason + invariant ref)     │
└─────────────────────────────┬──────────────────────────────────────┘
                              │  VR-ID forwarded with transaction
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│              Settlement Layer (XRPL / Ethereum / SWIFT)            │
│  Transaction payload includes: pogc_id + vr_id + osg_signature    │
│  On-chain / counterparty can verify offline using OSG public key   │
└────────────────────────────────────────────────────────────────────┘
```

### OSG Invariants

| ID | Name | Statement |
|---|---|---|
| OSG-INV-001 | Fail-Closed | Absence of a valid PoGC = REJECTED. No silent approval. |
| OSG-INV-002 | Immutable VR | Every validation produces an append-only ValidationReceipt — no DELETE, no UPDATE |
| OSG-INV-003 | Offline Verifiability | VR verifiable using only VR JSON + OMNIX public key — zero platform access |
| OSG-INV-004 | TTL Coverage | PoGC must not expire before the settlement_deadline in the request |
| OSG-INV-005 | Ledger Agnosticism | OSG logic is independent of the settlement ledger (XRPL, ETH, SWIFT) |
| OSG-INV-006 | Complete Audit Chain | VR carries pogc_id + session_id + ctchc_seal_hash — single chain from intent to settlement |

### Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/osg/validate` | API Key | Main gate: validate settlement against PoGC |
| `GET` | `/v1/osg/validation/{vr_id}` | None | Retrieve ValidationReceipt (public) |
| `GET` | `/v1/osg/settlement/{tx_hash}` | API Key | Lookup by settlement tx hash |
| `POST` | `/v1/osg/anchor` | API Key | Pre-anchor a settlement to a PoGC before execution |
| `GET` | `/v1/osg/organization/{org_id}` | API Key | Validation history for org |
| `GET` | `/v1/osg/manifest` | None | Module manifest + public key |

### DB Table: `osg_validation_receipts`

```sql
CREATE TABLE IF NOT EXISTS osg_validation_receipts (
    vr_id               TEXT PRIMARY KEY,          -- VR-{HEX16}
    pogc_id             TEXT NOT NULL,             -- POGC-{HEX16}
    session_id          TEXT NOT NULL,             -- OGR session
    ctchc_seal_hash     TEXT NOT NULL,             -- from PoGC
    settlement_ledger   TEXT NOT NULL,             -- XRPL | ETH | SWIFT | FIX | OTHER
    settlement_tx_hash  TEXT,                      -- ledger tx hash (post-execution)
    settlement_deadline TIMESTAMPTZ,               -- must be before PoGC.expires_at
    settlement_amount   NUMERIC,                   -- for amount-bound validations
    settlement_currency TEXT,                      -- RLUSD | USD | EUR | XRP
    org_id              TEXT NOT NULL,
    org_name            TEXT NOT NULL,
    verdict             TEXT NOT NULL CHECK (verdict IN ('APPROVED', 'REJECTED')),
    reject_reason       TEXT,
    reject_invariant    TEXT,
    content_hash        TEXT NOT NULL,
    pqc_signature       TEXT NOT NULL,
    pqc_algorithm       TEXT NOT NULL DEFAULT 'ml-dsa-65',
    validated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    anchored_at         TIMESTAMPTZ,               -- if pre-anchored via /anchor
    executed_at         TIMESTAMPTZ,               -- when settlement confirmed
    metadata            JSONB DEFAULT '{}'
);
```

### ValidationReceipt (VR) Structure

```json
{
  "vr_id":              "VR-A3F2B1C4D5E6F7A8",
  "pogc_id":            "POGC-...",
  "session_id":         "OGR-...",
  "ctchc_seal_hash":    "sha3-256:...",
  "settlement_ledger":  "XRPL",
  "settlement_currency": "RLUSD",
  "settlement_amount":  125000.00,
  "verdict":            "APPROVED",
  "invariants_checked": ["OSG-INV-001", "OSG-INV-004", "OSG-INV-006"],
  "content_hash":       "sha3-256:...",
  "pqc_signature":      "ml-dsa-65:...",
  "validated_at":       "2026-05-24T...",
  "offline_verify_url": "/v1/osg/validation/VR-..."
}
```

---

## Consequences

### Positive
- OMNIX owns the complete chain: **intent → governance → proof → settlement enforcement**
- Every settlement carries a forensic trail from human origin to on-chain consequence
- Regulators can verify the entire chain offline — from governance decision to payment
- Ledger-agnostic: works with XRPL, Ethereum, SWIFT, FIX
- Competitive moat: Eterna.AI owns settlement enforcement for XRPL only; OMNIX owns it for any ledger

### Negative
- Settlement enforcement is only as strong as the PoGC TTL — short-TTL certificates reduce the usable enforcement window
- On-chain enforcement requires the counterparty / ledger to check the VR — external adoption dependency

---

## OSG vs Eterna.AI Comparison

| Dimension | Eterna.AI | OMNIX OSG |
|---|---|---|
| Upstream governance | ❌ Starts at commitment | ✅ ATF → OGR → PoGC → OSG |
| Ledger | XRPL only | XRPL · ETH · SWIFT · FIX · Any |
| Settlement token | RLUSD | Any (currency-agnostic) |
| Offline verifiability | Unknown | ✅ OSG-INV-003 — zero platform access |
| PQC signing | Unknown | ✅ ML-DSA-65 FIPS 204 |
| Public registry | Unknown | ✅ PoGR + VR public |
| Audit chain | Settlement → cert | Intent → governance → proof → settlement |
| Standards published | None | RFC-ATF-1/2/3 (6 DOIs) |

---

*ADR-188 · OMNIX QUANTUM LTD · Harold Nunes · May 2026*
