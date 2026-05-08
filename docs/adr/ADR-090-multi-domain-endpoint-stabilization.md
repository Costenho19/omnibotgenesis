# ADR-090 — Multi-Domain Endpoint Stabilization

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-16 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` · `omnix_core/governance/` |
| **Replaces** | — |

---

## Context

The governance engine supported 10 live domains but the API surface was not uniformly stable across them. Domains added in later build sprints (Autonomous Agents, Energy, Real Estate, Stablecoin Reserve, Defense — ADR-091, ADR-112, ADR-114) inherited the core pipeline but had inconsistent:

1. **Signal schema coverage** — some domains lacked a full `_SIGNAL_SCHEMA_SET` entry, causing AVM to fall back to trading-domain defaults.
2. **Jurisdiction gate rules** — three domains had no jurisdiction-specific rules, passing all evaluations regardless of jurisdiction.
3. **Simulator alignment** — simulator-generated decisions for newer domains used slightly different payload shapes than the API response schema.

## Decision

A stabilization sweep across all 10 domains to enforce uniform contracts:

### 1. Signal schema enforcement

Every domain must have a complete entry in `_SIGNAL_SCHEMA_SET` in `assumption_validity_monitor.py`. Missing schemas cause a startup assertion error rather than silent fallback.

### 2. Jurisdiction gate completeness check

`jurisdiction_gate.py` validates that every supported domain has at least one jurisdiction rule. Domains with no rules are logged as `UNCONFIGURED_JURISDICTION` and return `HOLD` (not `APPROVED`) until rules are added.

### 3. Simulator payload alignment

All domain simulators updated to produce payloads structurally identical to what the `/api/governance/evaluate` endpoint produces, ensuring that dashboard visualizations fed by simulators match the production schema exactly.

### Coverage verification

```python
# ADR-090 startup assertion
for domain in SUPPORTED_DOMAINS:
    assert domain in _SIGNAL_SCHEMA_SET, f"Missing schema for domain {domain}"
    assert jurisdiction_gate.has_rules(domain), f"No jurisdiction rules for {domain}"
```

## Consequences

**Positive:**
- All 10 domains behave uniformly under the same API contract.
- Startup assertions catch schema gaps before any request is processed.
- Dashboard metrics are consistent with production governance decisions.

**Negative:**
- Startup assertion may block deployment if a new domain is added without its schema.

## Related

- ADR-085: Cross-Border Semantic Governance
- ADR-091: Autonomous Agents Governance Vertical
- ADR-115: Engine Unification All Verticals
