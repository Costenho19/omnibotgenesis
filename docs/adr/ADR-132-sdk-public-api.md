# ADR-132 — SDK Public API Surface

**Status:** ACCEPTED  
**Date:** 2026-04-27  
**Author:** OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo  
**Context:** Phase D — B2B SDK Release · Decision Governance Infrastructure  

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| v1 | 2026-04-27 | Initial Python SDK v2.0.0 and Node.js SDK v2.0.0 — full API surface covering evaluate, execute, verify, VC, revocation, utility |

---

## 1. Context and Problem Statement

OMNIX has built a production-grade Decision Governance Infrastructure spanning:
- ADR-084: W3C Verifiable Credentials
- ADR-130: VC Trust Revocation Registry (StatusList2021, ETag, webhooks, human accountability)
- ADR-131: Execution Integrity Layer (decision→execution audit chain)

For B2B adoption, clients need a **zero-dependency SDK** that makes all of this
accessible in a single, well-documented client library — without requiring clients
to understand the underlying architecture.

The API surface spans multiple endpoint families (governance, trust, execution, utility),
each with authentication, retry, and error-handling requirements. A raw HTTP client
leaves too much room for integration errors that could break the audit chain.

This ADR defines the public SDK API surface, its design principles, and the reasoning
behind every method signature choice.

---

## 2. Decision

Ship two official SDK implementations:
- **Python SDK** (`omnix_sdk/python/omnix_sdk.py`) — Python 3.8+, zero dependencies
- **Node.js SDK** (`omnix_sdk/node/index.js`) — Node.js 14+, zero dependencies

Both expose an **identical surface** with language-idiomatic naming:

| Category | Python | Node.js | Endpoint |
|---|---|---|---|
| Governance | `evaluate()` | `evaluate()` | `POST /api/governance/evaluate` |
| Execution | `execute()` | `execute()` | `POST /api/execution/receipts` |
| Execution | `get_execution_receipt()` | `getExecutionReceipt()` | `GET /api/execution/receipts/<id>` |
| Receipts | `get_receipt()` | `getReceipt()` | `GET /api/governance/receipts/<id>` |
| Receipts | `list_receipts()` | `listReceipts()` | `GET /api/governance/receipts` |
| Verification | `verify()` | `verify()` | `POST /api/trust/verify` |
| VC | `get_vc()` | `getVc()` | `POST /api/governance/receipt/vc` |
| VC Status | `get_vc_status()` | `getVcStatus()` | `GET /api/trust/vc-status/<id>` |
| Status List | `get_status_list()` | `getStatusList()` | `GET /api/trust/status-list` |
| Revocation | `revoke()` | `revoke()` | `POST /api/trust/revoke/<id>` |
| Revocation | `reinstate()` | `reinstate()` | `POST /api/trust/reinstate/<id>` |
| Health | `health()` | `health()` | `GET /api/health` |
| Schema | `get_schema()` | `getSchema()` | `GET /api/governance/schema` |
| Regulatory | `get_regulatory_frameworks()` | `getRegulatoryFrameworks()` | `GET /api/governance/regulatory/catalog` |
| Reports | `get_due_diligence_report()` | `getDueDiligenceReport()` | `GET /api/governance/due-diligence-report` |

---

## 3. Design Principles

### 3.1 Zero External Dependencies

Both SDKs use only stdlib HTTP (`urllib.request` / `https`) to avoid dependency
hell in client environments. This is a hard requirement for B2B institutional
clients with strict package governance policies (Basel IV, DORA Article 6).

### 3.2 Full Error Hierarchy

Raw `Exception` or single-error libraries force clients to parse error messages.
OMNIX SDK exposes a typed exception hierarchy:

```
OmnixError (base)
  ├── OmnixAuthError        401/403 — invalid key, insufficient permissions
  ├── OmnixNotFoundError    404 — resource not found or not owned
  ├── OmnixValidationError  422 — missing/invalid fields
  ├── OmnixRateLimitError   429 — rate limit, retryAfter attribute
  ├── OmnixTimeoutError     408 — request timeout
  ├── OmnixServerError      5xx — unexpected server error
  └── OmnixAPIError         catch-all for other 4xx
```

This lets clients write single-purpose exception handlers per failure mode rather
than parsing status codes or error message strings.

### 3.3 Automatic Retry with Exponential Backoff

Transient failures (`429 Rate Limit`, `503 Service Unavailable`) are automatically
retried with exponential backoff before raising to the caller. Default: 3 retries,
1-second base backoff. Configurable via `max_retries` and `retry_backoff`.

The client respects the `Retry-After` header from 429 responses — it won't retry
faster than the server asks it to.

### 3.4 Environment Variable Support

`OMNIX_API_KEY` and `OMNIX_BASE_URL` are auto-detected from the environment if not
passed to the constructor. This enables twelve-factor app patterns and avoids
API key literals in source code.

### 3.5 SDK-Level Validation

Client-side validation (missing signal fields, invalid enum values, insufficient
reason lengths) is performed before making network requests. This catches the most
common integration errors at compile/run time with clear error messages, rather
than at HTTP round-trip time.

### 3.6 Backward-Compatible Contract

The SDK wraps HTTP response dicts directly. No custom response types are used.
Clients always receive plain dicts — this avoids SDK version lock-in for
deserialization and simplifies logging and serialization.

---

## 4. Execution Endpoint (ADR-131 Public Surface)

The `execute()` method required a **new API endpoint** not previously exposed:

```
POST /api/execution/receipts
GET  /api/execution/receipts/<receipt_id>
```

These endpoints wrap the `ExecutionReceiptRegistry` from ADR-131. The flow for
the POST endpoint:

1. Validate authentication (X-API-Key)
2. Validate required fields and status-conditional fields
3. Construct an `ExecutionIntent` and call `registry.log_intent()`
4. Call `registry.log_result()` with the execution outcome
5. Return the sealed `ExecutionReceipt.to_dict()` response with HTTP 201

This means clients call `execute()` **after** the trade has occurred, reporting
the result. This is different from the internal `ExecutionGuard` context manager
which wraps the trade in real time — but for B2B clients integrating from outside,
the post-hoc reporting model is the correct pattern.

The decision→execution audit chain integrity is preserved: the
`decision_receipt_id` field binds the execution receipt to its governance
decision, and `receipt_hash` provides tamper-evident sealing.

---

## 5. API Key Format

API keys follow the format `OMNIX-<40 alphanumeric characters>`.

The SDK validates this format at construction time and raises `OmnixValidationError`
immediately if the format is wrong — no network request is made.

Admin-only methods (`revoke()`, `reinstate()`) require an API key with `role = 'admin'`
in the B2B client registry. The server enforces this; the SDK passes the key
transparently.

---

## 6. Signal Reference

The 8 required governance signals are validated client-side before the network request:

| Signal | Meaning | Strategic use |
|---|---|---|
| `signal_integrity` | Input data quality | Catch dirty/incomplete data before governance |
| `probability_score` | Decision confidence | Model confidence in the outcome |
| `risk_exposure` | Risk level (lower = safer) | Risk gate — high exposure triggers BLOCKED |
| `signal_coherence` | Internal consistency | Detect conflicting signal combinations |
| `trend_persistence` | Trend alignment | Validate against prevailing market/context trend |
| `stress_resilience` | Adverse condition tolerance | Stress test — how does decision hold under shock? |
| `logic_consistency` | Logical coherence | Epistemic validity of the decision scenario |
| `temporal_coherence` | Time-context validity | Is the context window still valid? |

---

## 7. Context Manager (Python only)

The Python `OmnixClient` supports the context manager protocol for resource cleanup
patterns:

```python
with OmnixClient(api_key="OMNIX-...") as client:
    result = client.evaluate(signals)
```

The `__exit__` method is a no-op (no connections to close — each request opens
and closes its own connection). The context manager is provided for idiomatic
Python usage and future-proofing.

---

## 8. Versioning

| Artifact | Version | Location |
|---|---|---|
| Python SDK | 2.0.0 | `omnix_sdk/python/omnix_sdk.py` (`__version__`) |
| Node.js SDK | 2.0.0 | `omnix_sdk/node/index.js` (`SDK_VERSION`) |
| API surface | ADR-132 | This document |

Future breaking changes to the API surface require a new major version and
a corresponding ADR-132 revision.

---

## 9. Consequences

### Positive

- B2B clients can integrate OMNIX with ~10 lines of code per use case
- Typed exception hierarchy enables clean error handling per failure mode
- Auto-retry + backoff reduces client-side operational complexity
- Zero dependencies removes a major adoption barrier for enterprise clients
- `execute()` completes the public surface for the full audit chain
- Execution endpoint (ADR-131) is now accessible via the public API

### Negative / Trade-offs

- Maintained in two languages — Python and Node.js must be kept in sync
- Raw dict responses (no typed models) — clients lose IDE autocomplete for fields
- Zero-dependency HTTP means no HTTP/2 or connection pooling — adequate for
  governance workloads but not for high-frequency use cases (>100 req/s)

---

## 10. Security Considerations

- API keys are **never logged** in the SDK or the server
- Keys are transmitted via `X-API-Key` header (HTTPS enforced in production)
- SDK-level validation prevents malformed requests that could probe server behavior
- `User-Agent` headers (`omnix-python-sdk/2.0.0`, `omnix-node-sdk/2.0.0`) enable
  server-side SDK version tracking for deprecation management

---

## 11. Related ADRs

| ADR | Relation |
|---|---|
| ADR-084 | W3C VC endpoint (get_vc) |
| ADR-124 | Oversight surface (human accountability auto-lookup) |
| ADR-130 | VC Trust Revocation (revoke, reinstate, get_vc_status, get_status_list, verify) |
| ADR-131 | Execution Integrity Layer (execute, get_execution_receipt) |

---

## 12. Implementation Files

```
NEW:
  omnix_sdk/python/omnix_sdk.py        Python SDK v2.0.0 — full client implementation
  omnix_sdk/python/README.md           Python SDK documentation
  omnix_sdk/node/index.js              Node.js SDK v2.0.0 — full client implementation
  omnix_sdk/node/README.md             Node.js SDK documentation
  docs/adr/ADR-132-sdk-public-api.md  This document

MODIFIED:
  omnix_web/api/server.py
      + POST /api/execution/receipts       Create execution receipt (ADR-131 public surface)
      + GET  /api/execution/receipts/<id>  Retrieve execution receipt
```
