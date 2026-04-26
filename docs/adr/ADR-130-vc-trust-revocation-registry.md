# ADR-130 — VC Trust Revocation Registry

**Status:** ACCEPTED  
**Date:** 2026-04-26  
**Author:** OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo  
**Context:** Fase C — eIDAS 2.0 / W3C VC / ARF Institutional Readiness  

---

## 1. Context and Problem Statement

OMNIX Governance Credentials (W3C VCs, ADR-084) are issued at the moment of each
governance decision. Once issued, a VC remains valid indefinitely — unless explicitly
revoked. This creates a trust gap identified during Fase C institutional audit and
highlighted by external security experts (Dr. Todd M. Price, 2026-04-26):

> *"The core question you're asking is right: Does the process deserve trust?  
> The next layer is: who can revoke that trust — and what happens when they do?  
> That's where governance shifts from observational… to enforceable."*

Without a revocation mechanism, OMNIX governance is observational but not enforceable.
A VC issued for a decision that is later found fraudulent, assumption-invalidated, or
overridden by regulation continues to exist as apparently valid evidence. External
verifiers — wallets, regulators, audit firms — have no way to discover the invalidation.

This ADR implements the revocation layer that closes this gap.

---

## 2. Decision

Implement a **VC Trust Revocation Registry** with the following properties:

1. **W3C StatusList2021 compatible**: Every issued VC includes a `credentialStatus`
   block pointing to a live revocation check endpoint.
2. **Innocent-until-revoked**: Not found in the registry = `status: active`. This
   avoids requiring a write to the registry at VC issuance time.
3. **Append-only audit trail**: Every state transition (revoke, suspend, reinstate)
   is recorded in a JSONB `audit_trail` column. Nothing is ever deleted.
4. **Multi-actor revocation**: Human admins, AVM, EBIP, and AnomalyResponseEngine
   can all trigger revocations with actor identity preserved.
5. **Reinstatement with accountability**: A revoked VC can be reinstated with a
   minimum 20-character justification. Original revocation event is never erased.

---

## 3. Architecture

### 3.1 Database Table

```sql
CREATE TABLE IF NOT EXISTS vc_revocation_registry (
    receipt_id           VARCHAR(128) PRIMARY KEY,
    status               VARCHAR(20)  NOT NULL DEFAULT 'active',
    reason               TEXT,
    revoked_by           VARCHAR(128),
    revoked_at           TIMESTAMPTZ,
    reinstated_at        TIMESTAMPTZ,
    reinstatement_reason TEXT,
    revocation_context   JSONB        NOT NULL DEFAULT '{}',
    audit_trail          JSONB        NOT NULL DEFAULT '[]',
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

**Status values:**
| Status | Meaning |
|---|---|
| `active` | Credential is valid (default — not in registry) |
| `revoked` | Permanently invalidated. Tamper-detection + reason mandatory. |
| `suspended` | Temporarily invalidated. Can be reinstated. |

### 3.2 Core Module

`omnix_web/api/omnix_engine/vc_revocation.py`

```
VCRevocationRegistry
├── get_status(receipt_id)     → dict  (public — no auth)
├── revoke(receipt_id, ...)    → dict  (admin auth required)
├── reinstate(receipt_id, ...) → dict  (admin auth required)
└── get_status_list()          → dict  (W3C StatusList2021 format)

build_credential_status(receipt_id) → dict
    Called by ReceiptToVC.convert() — embeds credentialStatus in every VC.
```

### 3.3 API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/trust/vc-status/{receipt_id}` | Public | Real-time status check |
| `POST` | `/api/trust/revoke/{receipt_id}` | Admin | Revoke or suspend |
| `POST` | `/api/trust/reinstate/{receipt_id}` | Admin | Reinstate with audit trail |
| `GET` | `/api/trust/status-list` | Public | W3C StatusList2021 index |

### 3.4 VC Structure Change (ADR-084 Extension)

Every VC issued by `ReceiptToVC.convert()` now includes:

```json
{
  "@context": ["https://www.w3.org/2018/credentials/v1", "..."],
  "id": "https://omnixquantum.net/receipts/{receipt_id}",
  "type": ["VerifiableCredential", "OmnixGovernanceCredential"],
  "credentialStatus": {
    "id": "https://omnixquantum.net/api/trust/vc-status/{receipt_id}",
    "type": "StatusList2021Entry",
    "statusPurpose": "revocation",
    "statusListCredential": "https://omnixquantum.net/api/trust/status-list",
    "adr": "ADR-130"
  },
  "credentialSubject": { "..." },
  "proof": { "..." }
}
```

### 3.5 Revocation Actors

```
revoked_by value          Trigger source
─────────────────────────────────────────────────────────────────
{client_id}               B2B admin client via POST /api/trust/revoke
system:avm                AssumptionValidityMonitor — drift > threshold
system:ebip               ExecutionBoundaryIntegrityProtocol — violation
system:anomaly            AnomalyResponseEngine (ADR-129) — critical anomaly
```

---

## 4. Revocation Triggers

### 4.1 Manual Revocation (Human Admin)
```
POST /api/trust/revoke/{receipt_id}
X-API-Key: {admin_key}
{ "reason": "Fraudulent counterparty detected post-issuance",
  "status": "revoked",
  "context": { "regulatory_basis": "FATF R.20", "case_ref": "CASE-2026-001" } }
```

### 4.2 System Revocation (AVM)
The AssumptionValidityMonitor (ADR-064/ADR-075) detects when the conditions
under which a decision was made are no longer valid (drift > threshold). Future
integration: AVM DRIFT_BLOCK events trigger automatic suspension of outstanding
VCs for the affected domain when drift > 80%.

```python
registry = VCRevocationRegistry()
registry.revoke(
    receipt_id=receipt_id,
    reason=f"AVM drift exceeded safety threshold: {drift:.1f}% (max 80%)",
    revoked_by="system:avm",
    status="suspended",
    context={"drift": drift, "domain": domain, "threshold": 80.0},
)
```

### 4.3 EBIP Integration (Future)
ExecutionBoundaryIntegrityProtocol (EBIP) violations with severity ≥ CRITICAL
can trigger automatic suspension of the associated VC, pending investigation.

---

## 5. Verifier Protocol

A third-party verifier receiving an OMNIX VC MUST:

1. Verify the `proof.proofValue` (Dilithium-3 signature) against the public key
   at `/api/trust/registry`.
2. Verify the `content_hash` integrity (SHA-256 recomputation).
3. **Check `/api/trust/vc-status/{receipt_id}` for revocation status.**
   Step 3 is mandatory. A cryptographically valid but revoked VC is not valid
   governance evidence.

Cache policy for step 3: `Cache-Control: no-cache` — always check live.

---

## 6. W3C StatusList2021 Compliance

The `GET /api/trust/status-list` endpoint returns a W3C-compatible revocation index.

Current format: enumerated list (suitable for current receipt volume ≤ 327K).  
Migration path: When revocation volume exceeds 131,072 entries, migrate to the
compressed bitstring format specified in StatusList2021 §4.

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://w3id.org/vc/status-list/2021/v1"
  ],
  "type": ["VerifiableCredential", "StatusList2021Credential"],
  "statusPurpose": "revocation",
  "revoked_credentials": [ { "receipt_id": "...", "status": "revoked", ... } ]
}
```

---

## 7. Human Accountability (Dr. Price Principle)

ADR-124 (Oversight Surface Engine) already implements deliberation windows,
framing governance, and override friction for human reviewers. ADR-130 extends
accountability to the post-issuance layer:

- The `revoked_by` field is cryptographically anchored in the audit trail.
- Every revocation requires explicit justification (min 10 chars).
- Every reinstatement requires explicit justification (min 20 chars).
- The `audit_trail` JSONB column is append-only — actors cannot retroactively
  change their stated reasons.

This closes the loop Dr. Price identified: OMNIX governance is no longer merely
observational. Trust can be granted and revoked with full accountability.

---

## 8. Security Considerations

- **Revocation endpoint rate limit**: Inherits server default (200/min). Revocation
  writes additionally gated by admin RBAC.
- **No full hash exposure**: `revocation_context` may contain partial hashes
  (prefix[:16] only) to avoid replay attacks.
- **Innocent-until-revoked**: If the registry DB is unavailable, `get_status()`
  returns `status: unknown` (not `active`) and logs an error. Verifiers should
  treat `unknown` as inconclusive.
- **No cascade deletion**: Reinstatement sets `status = 'active'` but preserves
  the full `audit_trail`. Nothing is ever deleted from this table.

---

## 9. Consequences

### Positive
- OMNIX governance shifts from observational to enforceable.
- Full W3C StatusList2021 compliance closes the eIDAS 2.0 / ARF 1.4 gap.
- Any EUDI wallet can verify OMNIX VC status in real time.
- Trust can be revoked with full human accountability preserved.
- AVM, EBIP, and AnomalyResponseEngine can trigger automatic revocations.

### Negative / Trade-offs
- Verifiers must perform an additional HTTP call to check revocation status.
  Mitigated: `status-list` endpoint provides cacheable bulk index (TTL: 5min).
- Admin RBAC required for revocation — no anonymous revocation possible.
  This is intentional: the trust anchor must itself be accountable.

---

## 10. Related ADRs

| ADR | Title | Relationship |
|---|---|---|
| ADR-084 | W3C Verifiable Credentials | Extended — adds `credentialStatus` to every VC |
| ADR-085 | Federated Trust Layer | Extended — adds 4 new endpoints to trust surface |
| ADR-096 | Canonical Receipt | Foundation — receipt_id is the revocation key |
| ADR-124 | Oversight Surface Engine | Human accountability complement |
| ADR-126 | Receipt Archival HOT/WARM/COLD | Revocation check applies across all storage tiers |
| ADR-129 | Anomaly Response Layer | System actor for automated revocation triggers |

---

## 11. Implementation Files

```
NEW:
  omnix_web/api/omnix_engine/vc_revocation.py
      VCRevocationRegistry, build_credential_status, _require_admin_auth

MODIFIED:
  omnix_web/api/server.py
      + vc_revocation_registry table in _ensure_vertical_tables()
      + GET  /api/trust/vc-status/<receipt_id>
      + POST /api/trust/revoke/<receipt_id>
      + POST /api/trust/reinstate/<receipt_id>
      + GET  /api/trust/status-list
      Updated /api/trust/health endpoints dict

  omnix_web/api/omnix_engine/receipt_to_vc.py
      + credentialStatus block in VC output (ReceiptToVC.convert)

  omnix_web/public/.well-known/omnix-arf-profile.json
      + revocation section with W3C StatusList2021 references
```
