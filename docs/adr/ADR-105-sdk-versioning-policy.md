# ADR-105 — SDK Versioning and Backward Compatibility Policy

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-21 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `sdk/python/` · `sdk/node/` |
| **Extends** | ADR-132 (SDK Public API) |
| **Replaces** | — |

---

## Context

The Python and Node.js SDKs (ADR-132) were shipped without a formal versioning policy. As the governance API evolved (ADR-080, ADR-081, ADR-096, ADR-097), SDK clients needed clarity on:

- When a new SDK version is required vs. optional
- Which API changes are breaking vs. backward-compatible
- How long deprecated SDK versions will continue to work against the production API

Without a versioning policy, enterprise clients could not confidently pin an SDK version in their production CI/CD pipelines.

## Decision

Adopt **Semantic Versioning (SemVer 2.0)** for both SDKs with an explicit compatibility matrix.

### Version format: `MAJOR.MINOR.PATCH`

| Change type | Version bump | Example |
|---|---|---|
| Breaking API change | MAJOR | New required field, removed endpoint |
| New non-breaking feature | MINOR | New optional parameter, new endpoint |
| Bug fix, documentation | PATCH | Fix wrong default, typo in error message |

### Compatibility guarantee

| API Version | SDK versions supported |
|---|---|
| v1 (current) | SDK ≥ 1.0.0 |
| v2 (future) | SDK ≥ 2.0.0, v1 SDKs deprecated for 12 months |

### Deprecation policy

1. Deprecated features are announced in `CHANGELOG.md` with the target removal version.
2. A deprecation warning is emitted at SDK construction time when a deprecated feature is used.
3. Minimum 6 months between deprecation announcement and removal.
4. Enterprise plan clients receive direct notification 90 days before breaking changes.

### SDK compatibility header

Every API request from the SDK includes:

```
X-OMNIX-SDK-Version: python/1.2.0
X-OMNIX-SDK-Client: omnix-python-sdk
```

This allows OMNIX to notify clients using deprecated SDK versions before their integration breaks.

## Consequences

**Positive:**
- Enterprise clients can pin SDK versions with confidence.
- OMNIX has a structured process for evolving the API without breaking clients.

**Negative:**
- MAJOR version bumps require coordinated releases across Python and Node.js SDKs simultaneously.

## Related

- ADR-132: SDK Public API
- ADR-028: External Signal Evaluation API
- ADR-062: Premium Features / Client Portal
