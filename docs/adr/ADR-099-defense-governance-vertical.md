# ADR-099 — Autonomous Defense Governance Vertical

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-18 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` · `omnix_services/defense_service/` |
| **Replaces** | — |

---

## Context

Autonomous defense systems — unmanned vehicles, cyber-defense agents, AI-assisted targeting — operate in high-stakes environments where every decision must be auditable, compliant with rules of engagement (ROE), and subject to mandatory human oversight for lethal or near-lethal actions.

No existing OMNIX vertical addressed:
- **Rules of engagement compliance** — is the proposed action within pre-authorized ROE parameters?
- **Proportionality assessment** — is the force level proportional to the assessed threat?
- **Human oversight threshold** — does this decision require human approval before execution?
- **Dual-use ethics gate** — is the technology or action restricted under international law or export controls?

## Decision

Add `AUTONOMOUS_DEFENSE` as the 10th and final supported governance domain.

### Signal schema (`_SIGNAL_SCHEMA_SET["autonomous_defense"]`)

| Signal | Type | Range | Description |
|---|---|---|---|
| `threat_confidence` | float | `0.0–1.0` | AI threat assessment confidence |
| `proportionality_score` | float | `0.0–1.0` | Assessed force proportionality |
| `roe_compliance_score` | float | `0.0–1.0` | Rules of engagement compliance |
| `civilian_proximity` | float | `0.0–1.0` | Proximity score to civilian assets |
| `dual_use_risk` | float | `0.0–1.0` | Dual-use / export control risk |
| `human_oversight_required` | bool | — | Mandatory human approval flag |

### Human oversight rule (non-negotiable)

Any action where `human_oversight_required=True` is BLOCKED at the governance layer until a human supervisor provides explicit approval via the oversight API. This is architecturally enforced — it cannot be disabled via configuration.

### AVM baseline

- BLOCK if `roe_compliance_score < 0.80`
- BLOCK if `civilian_proximity > 0.40`
- BLOCK if `proportionality_score < 0.60`
- HOLD (mandatory human review) if `human_oversight_required=True`

## Design invariant

The defense vertical enforces the strictest governance policy of all 10 domains. No configuration, API key privilege, or admin override can bypass the `human_oversight_required` gate.

## Consequences

**Positive:**
- OMNIX achieves full 10-domain coverage, completing the governance platform vision.
- Defense vertical establishes OMNIX as applicable to the most sensitive AI governance use cases.

**Negative:**
- Defense domain requires the most careful AVM calibration; miscalibrated thresholds have the highest consequence of any domain.
- Regulatory landscape for autonomous defense AI is rapidly evolving; jurisdiction rules will require frequent updates.

## Related

- ADR-091: Autonomous Agents Governance (related domain)
- ADR-049: Jurisdiction Compliance Gate
- ADR-115: Engine Unification All Verticals
- ADR-124: Oversight Surface Engine
