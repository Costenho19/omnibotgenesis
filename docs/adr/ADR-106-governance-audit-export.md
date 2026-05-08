# ADR-106 — Governance Audit Export

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-22 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` · `omnix_core/evidence/receipt_archival.py` |
| **Replaces** | — |

---

## Context

Regulatory auditors and enterprise clients conducting due diligence needed the ability to export governance receipts in machine-readable formats for offline verification and compliance reporting. The existing interfaces (web dashboard, single-receipt API) were designed for interactive use, not bulk data export.

Specific requests from prospective institutional clients:
- Export all receipts for a specific domain over a date range as CSV for Excel analysis
- Export receipts as JSONL (newline-delimited JSON) for ingestion into audit tools
- Export a W3C VC bundle (JSON-LD) covering all receipts in an audit window

## Decision

Add an audit export endpoint with format options and streaming response support.

### Endpoint

```
GET /api/governance/export/receipts
Authorization: Bearer <api_key>   (ADMIN or READ role required)

Query parameters:
  domain       = trading | credit | ... | all
  from         = ISO 8601 date (e.g. 2026-03-01)
  to           = ISO 8601 date (e.g. 2026-03-31)
  format       = csv | jsonl | vc_bundle (default: jsonl)
  signed_only  = true | false (default: true — ADR-063 filter applied)
  max_rows     = 1–10000 (default: 1000)
```

### Streaming response

Large exports are streamed using `flask.stream_with_context` to avoid memory accumulation. Response headers:

```
Content-Type: application/x-ndjson   (for jsonl)
Content-Disposition: attachment; filename="omnix_audit_2026-03_trading.jsonl"
X-OMNIX-Export-Count: 1247
X-OMNIX-Export-ADR: ADR-106
```

### VC bundle format

The `vc_bundle` format produces a single JSON-LD document containing all receipts as verifiable credentials, signed with the OMNIX Dilithium-3 key. The bundle itself carries a bundle-level signature.

## Consequences

**Positive:**
- Auditors can extract full governance histories for offline analysis.
- VC bundle format enables cross-jurisdictional regulatory submission.

**Negative:**
- Large exports (10,000 rows) generate significant DB load. Rate limiting (1 export per client per 5 minutes) mitigates this.

## Related

- ADR-063: Receipt Public Ledger Filter
- ADR-095: Receipt Retention Policy
- ADR-126: Phase 2 Receipt Archival (HOT/WARM/COLD)
