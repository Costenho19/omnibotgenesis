# ADR-079: PKI Verification Endpoint

**Status:** ACCEPTED  
**Date:** 2026-04-09  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Scope:** `omnix_dashboard/blueprints/receipt_verification.py`

---

## Context

OMNIX governance receipts are signed with Dilithium-3. Without a public verification
endpoint, third parties (Velos gateway, enterprise clients, auditors) cannot verify
a receipt's authenticity without manual key distribution and custom verification code.

This ADR establishes two public endpoints that enable self-service receipt verification.

---

## Decision

### Endpoints

#### `GET /api/receipts/public-key`

Returns the current signing public key and metadata. **Public — no authentication required.**

Response:
```json
{
  "algorithm": "Dilithium-3 (ML-DSA-65)",
  "provider_id": "dilithium3",
  "public_key_b64": "<base64-encoded public key>",
  "key_id": "<SHA-256 fingerprint, first 16 hex chars>",
  "key_mode": "persisted | ephemeral_dev",
  "nist_standard": "FIPS 204 — ML-DSA-65",
  "active_since": "<ISO timestamp>",
  "warning": null | "Ephemeral key — not stable across restarts"
}
```

#### `POST /api/receipts/verify`

Verifies a receipt's Dilithium-3 signature.

Input:
```json
{
  "receipt_id": "OMNIX-TRD-4A7F2B8C9D1E",
  "content_hash": "<SHA-256 hex of receipt payload>",
  "signature_b64": "<base64-encoded Dilithium-3 signature>"
}
```

Response (valid):
```json
{
  "valid": true,
  "receipt_id": "OMNIX-TRD-4A7F2B8C9D1E",
  "algorithm": "Dilithium-3 (ML-DSA-65)",
  "key_id": "<fingerprint>",
  "verified_at": "<ISO timestamp>",
  "db_cross_reference": {
    "found": true,
    "content_hash_match": true,
    "decision": "APPROVED",
    "timestamp": "<ISO>"
  }
}
```

Response (invalid):
```json
{
  "valid": false,
  "receipt_id": "OMNIX-TRD-4A7F2B8C9D1E",
  "reason": "SIGNATURE_INVALID | HASH_MISMATCH | RECEIPT_NOT_FOUND | MALFORMED_INPUT",
  "verified_at": "<ISO timestamp>"
}
```

### Input Validation

| Field | Constraint | Rejection reason |
|-------|-----------|-----------------|
| `receipt_id` | Must match `^OMNIX-[A-Z]{3}-[A-F0-9]{12}$` or `^OMNIX-[A-F0-9]{12}$` | `MALFORMED_INPUT` |
| `content_hash` | Must be 64 hex chars (SHA-256) | `MALFORMED_INPUT` |
| `signature_b64` | Max 8192 bytes decoded | `MALFORMED_INPUT` |

### DB Cross-Reference

The verify endpoint attempts to look up `receipt_id` in the PostgreSQL `decision_receipts` table.
If found: compares stored `content_hash` against submitted hash.
If not found: `db_cross_reference.found = false` — cryptographic verification still proceeds.

This prevents validating arbitrary detached (receipt_id, hash, signature) tuples that
were never issued by this OMNIX instance.

### Rate Limiting

Simple per-IP rate limit: 60 requests/minute via `OMNIX_VERIFY_RATE_LIMIT` env var (default: 60).
Exceeded: HTTP 429, body `{"error": "RATE_LIMIT_EXCEEDED"}`.

### Security Constraints

- Public key endpoint is public (no auth) — public keys are not secret.
- Verify endpoint is public — it only consumes the public key; no private key is exposed.
- Error responses are normalized — no information leakage (all invalid cases return same error structure).
- Request body capped at 16 KB to prevent large-payload abuse.

---

## Consequences

### Positive
- Any third party with a receipt can verify it independently
- Velos gateway can verify OMNIX receipts without custom integration
- Auditors get cryptographic proof of governance decisions
- Key rotation is detectable via `key_id` field

### Negative / Risks
- Public endpoint is a potential DDoS surface — mitigated by rate limiting
- If signing keys rotate (restart in ephemeral mode), past receipts cannot be verified
  against the new public key — mitigated by ADR-078 key persistence

---

## References

- ADR-078: Signing Key Persistence
- ADR-076/077: Anti-Replay Guard
- `omnix_dashboard/blueprints/receipt_verification.py`
- `omnix_core/evidence/decision_receipt.py`
