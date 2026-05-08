# ADR-080 — API Request Body Schema Validation

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-11 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` |
| **Replaces** | — |

---

## Context

The governance API received JSON request bodies with no structured schema enforcement at the entry point. Malformed payloads (missing required fields, wrong types, out-of-range values) propagated into the governance pipeline and produced opaque internal errors (`KeyError`, `TypeError`, unhandled `None`) that were difficult to debug and exposed internal stack traces to clients.

Specific observed failures:

- `asset` field sent as `null` → `NoneType` crash in AML gate
- `jurisdiction` sent as integer → crash in jurisdiction gate
- `confidence` outside `[0.0, 1.0]` → unchecked float used in Kelly sizing

## Decision

Implement body-level schema validation at the API ingress layer in `gov_blueprint.py` before any governance module is invoked.

**Validation rules for `/api/governance/evaluate`:**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `asset` | string | Yes | Non-empty, max 64 chars |
| `domain` | string | Yes | Must be in `SUPPORTED_DOMAINS` |
| `jurisdiction` | string | Yes | Must be in `SUPPORTED_JURISDICTIONS` |
| `operation` | string | Yes | One of `SPOT`, `FUTURES`, `OPTIONS`, `SWAP` |
| `confidence` | float | No | `0.0 ≤ x ≤ 1.0` |
| `metadata` | object | No | Max depth 3, max 20 keys |

**Error response on validation failure:**

```json
{
  "status": "VALIDATION_ERROR",
  "errors": [
    {"field": "domain", "message": "Value 'UNKNOWN' is not a supported domain"},
    {"field": "confidence", "message": "Must be between 0.0 and 1.0, got 1.5"}
  ],
  "adr": "ADR-080"
}
```

HTTP 422 is returned for schema errors; HTTP 400 for malformed JSON.

## Consequences

**Positive:**
- No internal stack traces exposed to API clients.
- Governance modules receive guaranteed-valid inputs.
- Validation errors are auditable and trace back to the client API key.

**Negative:**
- Additional latency ~0.2ms per request.
- Strict schema means existing integrations must be updated if they send non-compliant payloads.

## Related

- ADR-081: Per-Client Quota Enforcement (applied after schema validation)
- ADR-123: External API Security Hardening
- ADR-132: SDK Public API (SDKs generate schema-valid payloads by design)
