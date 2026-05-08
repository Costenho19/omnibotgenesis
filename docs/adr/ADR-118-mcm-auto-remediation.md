# ADR-118 — Meta-Coherence Monitor Auto-Remediation

| Field | Value |
|---|---|
| **Status** | Accepted — Extended May 2026 (ADR-144 anti-loop guard) |
| **Date** | 2026-04-25 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_core/governance/meta_coherence_monitor.py` · `omnix_core/governance/unified_control_layer.py` |
| **Extends** | ADR-117 (Meta-Coherence Monitor) · ADR-144 (Auto-Modification Guard) |
| **Replaces** | — |

---

## Context

The Meta-Coherence Monitor (ADR-117) detected governance degradation patterns — drift, deferral cascades, approval-rate anomalies — and surfaced them as `MCM_ALERT` events at three severity levels: INFO, WARNING, CRITICAL.

However, detection without action left operators as the single point of failure for remediation. During a CRITICAL alert triggered outside business hours, no automated corrective action occurred. The governance engine continued operating in a degraded state for 4+ hours until a human operator responded.

ADR-117 §9 explicitly planned auto-remediation as the next step.

## Decision

Implement automated remediation triggered by MCM `alert_level = CRITICAL`.

### Remediation actions by alert type

| MCM Alert Pattern | Auto-Remediation Action |
|---|---|
| `DEFERRAL_CASCADE` — excessive HOLD rate | Force AVM recalibration (ADR-120) with reason `MCM_DEFERRAL_CASCADE` |
| `APPROVAL_RATE_DRIFT` — approval rate outside ±20% of 30-day baseline | Tighten AVM veto thresholds by 10% for affected domain |
| `COHERENCE_FLOOR_BREACH` — coherence consistently near minimum threshold | Trigger AI model health check; switch to fallback model if primary is degrading |
| `SIGNAL_STALENESS` — price/signal data older than configured threshold | Activate DATA_SOURCE_FALLBACK and alert operator |
| `UNKNOWN_DEGRADATION` | Escalate to human operator only — no auto-remediation |

### Remediation constraints

1. **Maximum one auto-remediation per domain per 6-hour window** — prevents remediation loops.
2. **All auto-remediation actions are logged** to `mcm_remediation_log` with the triggering alert ID, action taken, and outcome.
3. **Human notification always sent** — even when auto-remediation fires, the Telegram admin bot sends a notification to the OMNIX operator.
4. **Remediation is reversible** — every auto-remediation stores the pre-remediation state so a human operator can rollback within 24 hours.

### Escalation path

```
MCM CRITICAL detected
    → auto-remediation eligible? YES
        → remediation fired
        → notify operator (Telegram)
        → log to mcm_remediation_log
    → auto-remediation eligible? NO (cooldown / UNKNOWN pattern)
        → escalate to operator (Telegram + dashboard alert)
        → governance continues in DEGRADED mode
```

### Schema

```sql
CREATE TABLE IF NOT EXISTS mcm_remediation_log (
    id                  SERIAL PRIMARY KEY,
    mcm_alert_id        TEXT NOT NULL,
    domain              TEXT NOT NULL,
    alert_pattern       TEXT NOT NULL,
    action_taken        TEXT NOT NULL,
    pre_remediation_state JSONB,
    outcome             TEXT,   -- SUCCESS, FAILED, ROLLED_BACK
    triggered_at        TIMESTAMPTZ DEFAULT now(),
    resolved_at         TIMESTAMPTZ
);
```

## Design invariant

Auto-remediation **never modifies** the governance decision outcome retroactively. It adjusts thresholds and triggers recalibration for *future* decisions only. Past receipts are immutable.

## Consequences

**Positive:**
- CRITICAL governance degradation is addressed within seconds, not hours.
- Remediation log provides a full audit trail satisfying regulatory change-management requirements.
- Operator is always notified — auto-remediation augments but does not replace human oversight.

**Negative:**
- Automated threshold tightening during a volatile market period could increase false-positive BLOCKED decisions.
- Remediation cooldown (6h) means a persistent degradation pattern may re-trigger after the window expires.

## ADR-144 Extension — Anti-Loop Guard (May 2026)

ADR-144 added a mandatory anti-loop guard to `auto_remediate()` that runs **before** any action is determined or executed.

### What it does

When `auto_remediate()` is invoked, the guard queries `mcm_remediation_log` for the target domain. If it finds ≥2 entries in the last `AVM_ANTI_LOOP_WINDOW_HOURS` (default 24h) with `action_taken IN ('TIGHTEN_CHECKPOINT_THRESHOLDS', 'FORCE_AVM_RECALIBRATION')`, the current remediation is **blocked** and escalated to human review.

### Why it matters

Without this guard, the following loop was possible:
```
MCM detects BLOCK_RATE_COLLAPSE (from previous tightening)
    → auto-tighten 10%
    → MCM detects BLOCK_RATE_COLLAPSE again (over-blocking)
    → auto-tighten 10% again
    → ...
```
The 6-hour rate limit constrained frequency but did not prevent the loop from completing across two windows. The anti-loop guard detects the pattern structurally.

### TIGHTEN now routes through AMG

The `TIGHTEN_CHECKPOINT_THRESHOLDS` action no longer calls `save_calibration_snapshot()` directly. It calls `deploy_optimized_thresholds()` with `source="MCM_AUTO_TIGHTEN"`, which runs all six Auto-Modification Guard safeguards before writing any change.

If AMG blocks or holds the tightening (cumulative cap exceeded, approval gate triggered), `outcome` is recorded as `HELD_OR_BLOCKED_BY_AMG` in `mcm_remediation_log`. The domain is not tightened until human approval is received.

### Loop detection record

When a loop is detected, a `LOOP_DETECTED` entry is written to `mcm_remediation_log` with `loop_detected=TRUE` and `outcome=LOOP_BLOCKED`. Telegram admin notification is sent with explicit loop context including `loop_alert_id`.

---

## Related

- ADR-117: Meta-Coherence Monitor
- ADR-120: AVM Engine Auto-Recalibration
- ADR-116: Fail-Closed Enforcement Policy
- ADR-124: Oversight Surface Engine
- ADR-144: Auto-Modification Guard (anti-loop guard, approval gate, cumulative drift cap)
