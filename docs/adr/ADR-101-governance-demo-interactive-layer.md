# ADR-101 — Governance Demo Interactive Layer

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-19 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/src/pages/` · `omnix_web/api/sandbox.py` |
| **Replaces** | — |

---

## Context

OMNIX governance demos at `/governance-demo-{domain}` served static scenario cards with pre-computed outcomes. Investor feedback consistently requested the ability to modify scenario parameters and see governance decisions update in real time — demonstrating that the engine is live, not pre-computed.

Static demos limited investor engagement and reduced perceived credibility during Series-A fundraising conversations.

## Decision

Upgrade all 10 governance demo pages to fully interactive mode:

### Interactive parameter controls

Each demo page exposes sliders/inputs for the key domain signals. When parameters change, the frontend sends a live request to the sandbox evaluation endpoint.

### Sandbox endpoint (`/api/sandbox/evaluate`)

```
POST /api/sandbox/evaluate
{
  "domain": "trading",
  "scenario": { <signal values from sliders> },
  "preset": "STRESS_TEST" | "NORMAL" | "EDGE_CASE"
}
```

Response is identical in structure to the production governance response, enabling side-by-side comparison during investor demos.

### Demo presets

Each domain ships with 3 presets:
- **NORMAL** — typical operating conditions → likely APPROVED
- **STRESS_TEST** — extreme signal values → likely BLOCKED
- **EDGE_CASE** — boundary conditions → HOLD with human review recommended

### Rate limiting

Sandbox endpoint limited to 30 requests/minute per IP (unauthenticated) to prevent abuse. No API key required.

## Consequences

**Positive:**
- Investors can prove to themselves that governance decisions change in real time.
- Presets allow a demo flow that consistently tells a compelling governance story.
- Interactive layer reuses the production governance engine — no mock logic.

**Negative:**
- Live sandbox calls consume governance engine capacity; heavy demo traffic may affect production latency if not isolated.

## Related

- ADR-040: Public Governance Sandbox
- ADR-056: Investor Command Center
- ADR-060: Investor Demo Flow
