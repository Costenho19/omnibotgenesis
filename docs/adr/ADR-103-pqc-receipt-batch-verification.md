# ADR-103 — PQC Receipt Batch Verification

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-20 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` · `omnix_core/security/pqc_security.py` |
| **Replaces** | — |

---

## Context

The receipt verification endpoint (`GET /verify/<receipt_id>`) verified one receipt per request. Enterprise clients conducting quarterly audits needed to verify thousands of receipts. Sequential single-receipt verification at 200ms per call would take 33+ minutes for 10,000 receipts — unacceptable for automated compliance pipelines.

## Decision

Add a batch verification endpoint that accepts up to 500 receipt IDs per request and returns verification results for all of them.

### Endpoint

```
POST /api/verify/batch
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "receipt_ids": ["rcpt_abc123", "rcpt_def456", ...],  // max 500
  "include_payload": false   // if true, returns full receipt JSON (larger response)
}
```

### Response

```json
{
  "total": 3,
  "verified": 2,
  "failed": 1,
  "results": [
    {
      "receipt_id": "rcpt_abc123",
      "status": "VERIFIED",
      "signature_algorithm": "Dilithium-3",
      "domain": "trading",
      "decision": "APPROVED"
    },
    {
      "receipt_id": "rcpt_def456",
      "status": "SIGNATURE_INVALID",
      "error": "Signature verification failed"
    }
  ],
  "batch_id": "batch_xyz789",
  "verified_at": "2026-04-20T14:23:11Z"
}
```

### Performance

Batch verification uses parallel PQC signature checks across a thread pool (8 workers by default). 500 receipts verified in ~4 seconds vs. 100 seconds sequentially.

## Consequences

**Positive:**
- Compliance pipelines can verify entire audit windows in seconds.
- Batch results include a `batch_id` for audit trail purposes.

**Negative:**
- Max 500 receipts per batch requires pagination for larger datasets.
- Parallel PQC verification increases CPU spike load during batch processing.

## Related

- ADR-044: Quantum-Secure Decision Receipts
- ADR-078: Signing Key Persistence
- ADR-079: PKI Verification Endpoint
