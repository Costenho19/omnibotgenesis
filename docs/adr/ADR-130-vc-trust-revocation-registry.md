# ADR-130 — VC Trust Revocation Registry

**Status:** ACCEPTED (v2 — "full Europa" premium upgrade)  
**Date:** 2026-04-26  
**Author:** OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo  
**Context:** Fase C — eIDAS 2.0 / W3C VC / ARF Institutional Readiness  

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| v1 | 2026-04-26 | Initial revocation registry — 4 endpoints, credentialStatus block, ADR doc |
| v2 | 2026-04-26 | Full Europa upgrade: W3C compressed bitstring, ETag cache strategy, revocation webhooks, human accountability binding in VC proof |

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

This ADR implements the revocation layer that closes this gap, and its v2 upgrade
brings it to full W3C StatusList2021 spec compliance with enterprise-grade caching,
real-time webhook delivery, and cryptographic human accountability binding.

---

## 2. Decision

Implement a **VC Trust Revocation Registry** with the following properties:

1. **W3C StatusList2021 compressed bitstring**: Every issued VC includes a `credentialStatus`
   block pointing to a live revocation check endpoint. The status-list endpoint returns
   a gzip-compressed, base64url-encoded bitstring of minimum 131,072 bits (16 KB uncompressed),
   MSB-first bit ordering, fully compliant with StatusList2021 §4.
2. **Innocent-until-revoked**: Not found in the registry = `status: active`. This
   avoids requiring a write to the registry at VC issuance time.
3. **Append-only audit trail**: Every state transition (revoke, suspend, reinstate)
   is recorded in a JSONB `audit_trail` column. Nothing is ever deleted.
4. **Multi-actor revocation**: Human admins, AVM, EBIP, and AnomalyResponseEngine
   can all trigger revocations with actor identity preserved.
5. **Reinstatement with accountability**: A revoked VC can be reinstated with a
   minimum 20-character justification. Original revocation event is never erased.
6. **ETag / conditional GET cache strategy**: `GET /api/trust/status-list` supports
   `If-None-Match` → `304 Not Modified`. ETag is computed as SHA-256 of registry
   state (count + latest timestamp). `Cache-Control: public, max-age=300` (5-minute TTL).
7. **Revocation webhooks**: B2B clients receive real-time `vc.revoked`, `vc.suspended`,
   and `vc.reinstated` events via HMAC-SHA256-signed HTTP callbacks configured in
   `b2b_clients.webhook_url` / `b2b_clients.webhook_secret`.
8. **Human accountability binding in VC proof**: When a human reviewer approves a
   governance decision, the VC `proof` block includes a `humanSigner` sub-object with
   reviewer identity, attestation timestamp, SHA-256 attestation hash, oversight session
   ID, and EQS score. This closes the human-in-the-loop audit trail at the cryptographic layer.

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

-- v2 migration (applied at startup via ALTER TABLE IF NOT EXISTS):
ALTER TABLE vc_revocation_registry ADD COLUMN IF NOT EXISTS status_list_index INTEGER;
```

**Status values:**
| Status | Meaning |
|---|---|
| `active` | Credential is valid (default — not in registry) |
| `revoked` | Permanently invalidated. Tamper-detection + reason mandatory. |
| `suspended` | Temporarily invalidated. Can be reinstated. |

**`status_list_index`**: Sequential integer assigned at first revocation.
Maps the receipt to a bit position in the W3C StatusList2021 compressed bitstring.

### 3.2 Core Module

`omnix_web/api/omnix_engine/vc_revocation.py`

```
VCRevocationRegistry
├── get_status(receipt_id)              → dict  (public — no auth)
├── revoke(receipt_id, ...)             → dict  (admin auth required)
│     └── fires fire_revocation_webhook() in daemon thread
├── reinstate(receipt_id, ...)          → dict  (admin auth required)
│     └── fires fire_revocation_webhook() in daemon thread
├── get_status_list()                   → dict  (W3C StatusList2021 + encodedList)
├── get_etag()                          → str   (SHA-256 of registry state)
└── _build_encoded_list()               → str   (gzip+base64url 131072-bit bitstring)

_get_next_status_list_index(cur)        → int   (sequential assignment)
build_credential_status(receipt_id)     → dict  (embedded in every VC)
fire_revocation_webhook(event, data)    → None  (daemon thread, HMAC-SHA256 signed)
_require_admin_auth(request)            → (client_id, error_response)
```

### 3.3 API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/trust/vc-status/{receipt_id}` | Public | Real-time status check (no-cache) |
| `POST` | `/api/trust/revoke/{receipt_id}` | Admin | Revoke or suspend |
| `POST` | `/api/trust/reinstate/{receipt_id}` | Admin | Reinstate with audit trail |
| `GET` | `/api/trust/status-list` | Public | W3C StatusList2021 bitstring (ETag/304) |

### 3.4 VC Structure (ADR-084 Extension)

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
    "statusListIndex": 42,
    "adr": "ADR-130"
  },
  "credentialSubject": { "..." },
  "proof": {
    "type": "Dilithium3Signature2024",
    "proofValue": "...",
    "verificationMethod": "did:web:omnixquantum.net#key-1",
    "humanSigner": {
      "reviewerId": "reviewer-uuid",
      "attestedAt": "2026-04-26T12:00:00Z",
      "attestationHash": "sha256:<hex>",
      "oversightSessionId": "OSS-...",
      "eqsScore": 0.94
    }
  }
}
```

**`statusListIndex`**: present only when the VC has been assigned an index (first revocation
sets the index; build_credential_status() embeds it if known at issuance time).

**`humanSigner`**: present only when `human_signer` dict is passed to `ReceiptToVC.convert()`.
Attestation hash = `sha256(reviewerId + ":" + receipt_id + ":" + attestedAt)`.
Verifiers can recompute the hash to confirm reviewer identity.

### 3.5 Revocation Actors

```
revoked_by value          Trigger source
─────────────────────────────────────────────────────────────────
{client_id}               B2B admin client via POST /api/trust/revoke
system:avm                AssumptionValidityMonitor — drift > threshold
system:ebip               ExecutionBoundaryIntegrityProtocol — violation
system:anomaly            AnomalyResponseEngine (ADR-129) — critical anomaly
```

System actors (`system:*`) do not trigger webhook delivery — no client is associated.

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
under which a decision was made are no longer valid (drift > threshold).

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

## 5. W3C StatusList2021 Bitstring (v2)

### 5.1 Encoding

The `GET /api/trust/status-list` endpoint returns a `StatusList2021Credential` with
a compressed bitstring in the `encodedList` field:

- **Size**: 131,072 bits minimum (16 KB uncompressed). W3C StatusList2021 §6.1 minimum.
- **Bit ordering**: MSB-first (bit 0 of byte 0 = credential at index 0).
- **Compression**: gzip (level 9) → base64url (no padding).
- **Set bits**: A `1` at position `status_list_index` means that credential is revoked/suspended.

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://w3id.org/vc/status-list/2021/v1"
  ],
  "type": ["VerifiableCredential", "StatusList2021Credential"],
  "id": "https://omnixquantum.net/api/trust/status-list",
  "issuer": "did:web:omnixquantum.net",
  "issuanceDate": "2026-04-26T12:00:00Z",
  "credentialSubject": {
    "id": "https://omnixquantum.net/api/trust/status-list#list",
    "type": "StatusList2021",
    "statusPurpose": "revocation",
    "encodedList": "<base64url(gzip(bitstring))>"
  },
  "statusPurpose": "revocation",
  "total_credentials": 131072,
  "revoked_count": 3,
  "adr": "ADR-130 v2"
}
```

### 5.2 Index Assignment

Each new revocation is assigned the next sequential `status_list_index`:
```sql
SELECT COALESCE(MAX(status_list_index), -1) + 1 FROM vc_revocation_registry
```
This index is stored in the `status_list_index` column and embedded in
`credentialStatus.statusListIndex` of the VC at issuance time (when known).

---

## 6. ETag / Cache Strategy (v2)

### 6.1 ETag Computation

```python
def get_etag(self) -> str:
    # ETag = SHA-256 of "count:max_updated_at"
    # Changes whenever any credential is revoked, suspended, or reinstated.
    payload = f"{count}:{max_updated_at}"
    return hashlib.sha256(payload.encode()).hexdigest()[:32]
```

### 6.2 Conditional GET Protocol

```
Client → GET /api/trust/status-list
Server ← 200 OK  ETag: "abc123..."  Cache-Control: public, max-age=300
         [encodedList bitstring body]

--- 5 minutes later ---

Client → GET /api/trust/status-list  If-None-Match: "abc123..."
Server ← 304 Not Modified  ETag: "abc123..."   (no body — save bandwidth)

--- after a revocation ---

Client → GET /api/trust/status-list  If-None-Match: "abc123..."
Server ← 200 OK  ETag: "def456..."  [new bitstring body]
```

### 6.3 HTTP Headers

| Header | Value |
|---|---|
| `Cache-Control` | `public, max-age=300` |
| `ETag` | `"<sha256[:32]>"` |
| `X-StatusList-Encoding` | `StatusList2021/gzip+base64url` |

The `/api/trust/vc-status/{receipt_id}` endpoint remains `no-cache, no-store`
(per W3C StatusList2021 §7.1 — real-time status checks must not be cached).

---

## 7. Revocation Webhooks (v2)

### 7.1 Configuration

B2B clients configure webhooks in `b2b_clients`:

```sql
webhook_url     TEXT   -- HTTPS endpoint to receive events
webhook_secret  TEXT   -- Encrypted symmetric secret (AES-256, ADR-053 pattern)
```

Webhook secrets are encrypted at rest using `_decrypt_secret()` from `gov_auth_rbac`.

### 7.2 Event Schema

All events are signed with HMAC-SHA256 and delivered with a 10-second timeout and
2 retries (0-second delay). Delivery is asynchronous (daemon thread) — revocation
API response is not blocked.

```json
{
  "event":       "vc.revoked",
  "receipt_id":  "OMNIX-TRD-20260426-001",
  "status":      "revoked",
  "reason":      "Fraudulent counterparty detected post-issuance",
  "revoked_by":  "client-abc123",
  "revoked_at":  "2026-04-26T12:00:00Z",
  "vc_status_url": "https://omnixquantum.net/api/trust/vc-status/OMNIX-TRD-20260426-001",
  "adr":         "ADR-130",
  "omnix_version": "6.5.4e"
}
```

**Events:**
| Event | Trigger |
|---|---|
| `vc.revoked` | `revoke()` with `status="revoked"` |
| `vc.suspended` | `revoke()` with `status="suspended"` |
| `vc.reinstated` | `reinstate()` |

### 7.3 Signature

```
X-OMNIX-Signature: sha256=<hmac_sha256_hex(secret, body_bytes)>
X-OMNIX-Event: vc.revoked
X-OMNIX-Delivery: <uuid>
```

Receivers MUST verify the signature before processing the event.

---

## 8. Human Accountability Binding (v2)

### 8.1 humanSigner Block in VC Proof

When a governance decision is reviewed and approved by a human, the caller of
`POST /api/governance/receipt/vc` may supply a `human_signer` dict:

```json
{
  "receipt": { "..." },
  "human_signer": {
    "reviewer_id":          "reviewer-uuid",
    "eqs_score":            0.94,
    "oversight_session_id": "OSS-2026-04-26-001"
  }
}
```

`ReceiptToVC.convert(receipt, human_signer=...)` embeds the following in `proof`:

```json
"humanSigner": {
  "reviewerId":           "reviewer-uuid",
  "attestedAt":           "2026-04-26T12:00:00Z",
  "attestationHash":      "sha256:a1b2c3...",
  "oversightSessionId":   "OSS-2026-04-26-001",
  "eqsScore":             0.94
}
```

### 8.2 Attestation Hash

```python
payload = f"{reviewer_id}:{receipt_id}:{attested_at}"
attestation_hash = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()
```

Any verifier can recompute the hash from the three public fields to confirm
the reviewer identity has not been tampered with post-issuance.

### 8.3 Response Indicators

`POST /api/governance/receipt/vc` response:

```json
{
  "verifiable_credential": { "..." },
  "human_accountability":  true,
  "adr":                   "ADR-130 v2",
  "..."
}
```

HTTP header: `X-OMNIX-Human-Accountability: true | false`

---

## 9. Verifier Protocol

A third-party verifier receiving an OMNIX VC MUST:

1. Verify the `proof.proofValue` (Dilithium-3 signature) against the public key
   at `/api/trust/registry`.
2. Verify the `content_hash` integrity (SHA-256 recomputation).
3. **Check `/api/trust/vc-status/{receipt_id}` for revocation status.**
   Step 3 is mandatory. A cryptographically valid but revoked VC is not valid
   governance evidence. This endpoint is `no-cache` — always check live.
4. *(Optional)* For efficient bulk checks, fetch `GET /api/trust/status-list`,
   cache it for up to 300 seconds (respect `ETag` for conditional GET), and check
   the bit at `credentialStatus.statusListIndex`.
5. *(Optional)* If `proof.humanSigner` is present, recompute `attestationHash`
   from `reviewerId + ":" + receipt_id + ":" + attestedAt` and compare to verify
   the human reviewer binding has not been tampered with.

---

## 10. Security Considerations

- **Revocation endpoint rate limit**: Inherits server default (200/min). Revocation
  writes additionally gated by admin RBAC.
- **No full hash exposure**: `revocation_context` may contain partial hashes
  (prefix[:16] only) to avoid replay attacks.
- **Innocent-until-revoked**: If the registry DB is unavailable, `get_status()`
  returns `status: unknown` (not `active`) and logs an error. Verifiers should
  treat `unknown` as inconclusive.
- **No cascade deletion**: Reinstatement sets `status = 'active'` but preserves
  the full `audit_trail`. Nothing is ever deleted from this table.
- **Webhook HMAC-SHA256**: Webhook payloads are signed. Receivers who skip signature
  verification are vulnerable to spoofed revocation events.
- **ETag timing**: ETag changes on any revocation/reinstatement, ensuring verifiers
  never serve a stale bitstring after a state change.

---

## 11. Consequences

### Positive
- OMNIX governance shifts from observational to enforceable.
- Full W3C StatusList2021 compliance (compressed bitstring, 131072-bit minimum).
- Any EUDI wallet can verify OMNIX VC status in real time or via cached bitstring.
- Trust can be revoked with full human accountability preserved.
- AVM, EBIP, and AnomalyResponseEngine can trigger automatic revocations.
- B2B clients receive instant webhook notifications on every state change.
- Human reviewers are cryptographically bound to the VC they approved — non-repudiable.
- ETag/304 support reduces bandwidth for verifiers polling the status list.

### Negative / Trade-offs
- Verifiers must perform an additional HTTP call to check revocation status.
  Mitigated: `status-list` endpoint provides cacheable bulk index (TTL: 5min, ETag).
- Admin RBAC required for revocation — no anonymous revocation possible.
  This is intentional: the trust anchor must itself be accountable.
- `humanSigner` is optional — VCs issued without a human reviewer do not have
  this block. Absence is not an error; it means the decision was fully automated.

---

## 12. Related ADRs

| ADR | Title | Relationship |
|---|---|---|
| ADR-084 | W3C Verifiable Credentials | Extended — adds `credentialStatus` + `humanSigner` to every VC |
| ADR-085 | Federated Trust Layer | Extended — adds 4 new endpoints to trust surface |
| ADR-096 | Canonical Receipt | Foundation — receipt_id is the revocation key |
| ADR-124 | Oversight Surface Engine | Human accountability complement — EQS score source |
| ADR-126 | Receipt Archival HOT/WARM/COLD | Revocation check applies across all storage tiers |
| ADR-129 | Anomaly Response Layer | System actor for automated revocation triggers |
| ADR-053 | Credential Encryption | Pattern reused for webhook secret encryption |

---

## 13. Implementation Files

```
MODIFIED (v2):
  omnix_web/api/omnix_engine/vc_revocation.py
      + _build_encoded_list()              W3C compressed bitstring (gzip+base64url, 131072 bits)
      + _get_next_status_list_index()      sequential index assignment
      + get_status_list()                  returns encodedList + per-entry statusListIndex
      + get_etag()                         SHA-256 of registry state for ETag
      + fire_revocation_webhook()          HMAC-SHA256 signed, daemon thread
      + _deliver_revocation_webhook()      HTTP delivery with 2 retries
      + _get_client_webhook_config()       fetches webhook_url/secret from b2b_clients
      revoke()                             triggers webhook + assigns status_list_index
      reinstate()                          triggers vc.reinstated webhook

  omnix_web/api/omnix_engine/receipt_to_vc.py
      + _build_human_signer_block()        humanSigner sub-object in proof
      convert()                            accepts optional human_signer= kwarg

  omnix_web/api/server.py
      _ensure_vertical_tables()            + ALTER TABLE … ADD COLUMN IF NOT EXISTS status_list_index
      trust_status_list()                  + ETag, If-None-Match→304, X-StatusList-Encoding header

  omnix_web/api/gov_blueprint.py
      api_governance_receipt_vc()          + human_signer extraction + pass-through to ReceiptToVC

NEW (v1, unchanged in v2):
  omnix_web/api/omnix_engine/vc_revocation.py
      VCRevocationRegistry, build_credential_status, _require_admin_auth

  omnix_web/api/server.py
      GET  /api/trust/vc-status/<receipt_id>
      POST /api/trust/revoke/<receipt_id>
      POST /api/trust/reinstate/<receipt_id>
      GET  /api/trust/status-list
      Updated /api/trust/health endpoints dict

  omnix_web/api/omnix_engine/receipt_to_vc.py
      credentialStatus block in VC output (ReceiptToVC.convert)

  omnix_web/public/.well-known/omnix-arf-profile.json
      revocation section with W3C StatusList2021 references
```
