# ADR-109 — Multi-Region Deployment Policy

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-23 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | Railway deployment configuration · `docs/operations/DEPLOYMENT.md` |
| **Replaces** | — |

---

## Context

OMNIX operates enterprise clients across UAE (GCC), EU (MiCA/GDPR), and US (SEC/CFTC) jurisdictions. A single-region Railway deployment in `us-west` introduced:

1. **Data residency concerns** — EU clients under GDPR cannot have governance receipts (which may contain personal/financial data) stored exclusively in US infrastructure.
2. **Latency** — UAE clients experienced 180–250ms API round-trip latency from a US-west deployment.
3. **Regulatory risk** — some jurisdictions require financial infrastructure to be hosted within national or regional boundaries.

## Decision

Adopt a multi-region deployment strategy on Railway:

### Region assignments

| Client Jurisdiction | Primary Region | Receipt Storage |
|---|---|---|
| UAE / GCC | `ap-southeast-1` (Singapore) | Regional PostgreSQL |
| EU (GDPR) | `eu-west-1` (Frankfurt) | Regional PostgreSQL + GDPR DPA |
| US | `us-west-1` | US PostgreSQL |
| Global / Sandbox | `us-west-1` | Shared PostgreSQL |

### Architecture invariants

1. **No cross-region receipt replication** — EU receipts never transit US infrastructure.
2. **Shared governance engine code** — the same Docker image deploys to all regions; no region-specific code branches.
3. **Regional Redis instances** — anti-replay cache (ADR-076, ADR-077) is per-region to avoid cross-region clock skew issues.
4. **PQC key management** — signing keys are region-specific secrets, never transmitted cross-region.

### Jurisdiction routing

The API gateway routes requests to the nearest compliant region based on the `jurisdiction` field in the governance request, not client IP (which may be a VPN/proxy).

## Consequences

**Positive:**
- EU clients achieve GDPR data residency compliance.
- UAE clients experience <50ms API latency.
- Single codebase deployed uniformly across regions.

**Negative:**
- Multi-region deployment increases infrastructure cost by ~2.5x.
- Cross-region consistency for global analytics (Investor Command Center) requires a read-replica aggregation layer.

## Related

- ADR-049: Jurisdiction Compliance Gate
- ADR-085: Cross-Border Semantic Governance
- ADR-078: Signing Key Persistence
