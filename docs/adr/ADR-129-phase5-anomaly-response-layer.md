# ADR-129 — Phase 5: Anomaly Response Layer

**Status:** ACCEPTED  
**Date:** 2026-04-25  
**Author:** OMNIX Engineering  
**Scope:** `omnix_core/governance/anomaly_response.py`, `tests/test_phase5_anomaly_response.py`

---

## Context

Phase 4 (ADR-128) built `CalibrationInsightEngine` — a detection layer that identifies 6 types of governance anomalies (BLOCK_RATE_DROP, DCI_SURGE, HOLD_SPIKE, COHERENCE_DRIFT, BS_HIGH_SURGE, ESCALATION_SURGE) with severity classification.

Detection alone is passive. Phase 5 converts detected anomalies into **structured, traceable governance recommendations** — the first layer of controlled autonomous response.

### Problem
- A CRITICAL anomaly surfaced at 3am produces no action if there is no recommendation system.
- Without a lifecycle model, operators have no way to acknowledge, act on, or close anomaly signals.
- Without persistence, anomaly history is invisible to auditors and investors.
- Any automated response that bypasses governance layers would itself violate the governance architecture OMNIX is built to enforce.

### Requirements
1. **Recommendation-first**: Every response is advisory. No decision is overridden, no gate is modified, no model is changed automatically.
2. **Reversible**: Recommendations can be closed (ACKNOWLEDGED → RESOLVED) at any time with no side effects.
3. **Traceable**: All recommendations and lifecycle transitions are persisted to `anomaly_recommendations` with full operator audit trail.
4. **Non-destructive**: The response engine has zero write path to governance tables, AVM models, or decision receipts.
5. **Cycle**: `detect_anomalies()` → `generate_recommendations()` → `log_recommendations()` → lifecycle management.
6. **Testable without DB**: 100% mockable via dependency injection.

---

## Decision

Introduce `AnomalyResponseEngine` in `omnix_core/governance/anomaly_response.py`.

### Anomaly → Action Mapping

| Anomaly Type | Action Code | Description |
|---|---|---|
| `BLOCK_RATE_DROP` | `SUSPEND_RECALIBRATION` | Pause automated coherence gate threshold recalibration until root cause identified and block rate recovers |
| `DCI_SURGE` | `REDUCE_POSITION_SIZING` | Recommend reducing max position sizing by 25% for new decisions until DCI returns to TENSIONED/ALIGNED band |
| `HOLD_SPIKE` | `FLAG_OPERATIONAL_ALERT` | Alert operations team: manual review queue saturating; assess temporary widening of auto-approve thresholds for low-risk decisions |
| `COHERENCE_DRIFT` | `TRIGGER_AVM_REVIEW` | Trigger AVM review for affected domain: verify upstream data freshness, model weight staleness, and signal range bounds |
| `BS_HIGH_SURGE` | `MONITOR_BS_LEVELS` | Escalate Black Swan monitoring to 15-min intervals; alert risk committee if BS_HIGH rate exceeds 20% in next 1h window |
| `ESCALATION_SURGE` | `ESCALATION_REVIEW` | Review ADR-119 escalation configuration; document findings before any threshold change is approved |

All action codes are:
- **Reversible**: closing the recommendation has zero side effects
- **Non-destructive**: no core system state is changed by the recommendation itself
- **Advisory**: a human operator must take the actual action

### Recommendation Lifecycle

```
generate_recommendations()  →  ACTIVE
         │
         ├── acknowledge(rec_id, operator)  →  ACKNOWLEDGED
         │         │
         │         └── resolve(rec_id, note)  →  RESOLVED
         │
         ├── resolve(rec_id, note)  →  RESOLVED
         │
         └── expire_stale()  →  EXPIRED  (if expires_at passed or age > hours)
```

### Urgency Levels (from severity)

| Severity | Urgency | Target Response Time |
|---|---|---|
| CRITICAL | IMMEDIATE | 15 minutes |
| HIGH | URGENT | 1 hour |
| MEDIUM | ELEVATED | 4 hours |
| LOW | MONITORING | 24 hours |

### full_response_cycle() API

Single-call entry point that chains:
1. `CalibrationInsightEngine.detect_anomalies(domain)` — anomaly detection
2. `generate_recommendations(anomaly_result)` — pure mapping, no DB
3. `log_recommendations(recs)` — persists to `anomaly_recommendations`
4. `get_active(domain)` — returns current active count

Returns:
```python
{
    "domain":           str | None,
    "available":        bool,
    "anomalies":        { detect_anomalies() output },
    "recommendations":  [ { AnomalyRecommendation.to_dict() } ],
    "new_logged":       int,
    "active_count":     int,
    "overall_severity": str,
    "generated_at":     str,
}
```

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS anomaly_recommendations (
    id                   VARCHAR(36)   PRIMARY KEY,        -- UUID v4
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    anomaly_type         VARCHAR(50)   NOT NULL,
    severity             VARCHAR(20)   NOT NULL,
    urgency              VARCHAR(20)   NOT NULL DEFAULT 'ELEVATED',
    domain               VARCHAR(50),
    action_code          VARCHAR(50)   NOT NULL,
    action_description   TEXT          NOT NULL,
    rationale            TEXT          NOT NULL,
    is_reversible        BOOLEAN       NOT NULL DEFAULT TRUE,
    status               VARCHAR(20)   NOT NULL DEFAULT 'ACTIVE',
    anomaly_detected_at  TIMESTAMPTZ,
    expires_at           TIMESTAMPTZ,
    acknowledged_at      TIMESTAMPTZ,
    acknowledged_by      VARCHAR(100),
    resolved_at          TIMESTAMPTZ,
    resolved_note        TEXT,
    auto_generated       BOOLEAN       NOT NULL DEFAULT TRUE
);
```

Indexes:
- `(domain, status, created_at DESC)` — active recommendations by domain
- `(status, created_at DESC)` — status-based queries
- `(anomaly_type, created_at DESC)` — pattern queries
- `(expires_at) WHERE status = 'ACTIVE'` — expiry scan

---

## Module Structure

```
omnix_core/governance/anomaly_response.py
│
├── _ActionSpec                       — internal action specification dataclass
├── _ANOMALY_ACTION_MAP               — dict[anomaly_type → _ActionSpec]
├── _SEVERITY_TO_URGENCY              — dict[severity → urgency]
│
├── AnomalyRecommendation             — output dataclass with full audit fields
│
├── AnomalyResponseEngine             — main class
│   ├── ensure_schema()               — create table + indexes
│   ├── generate_recommendations()    — pure: anomaly_result → List[Recommendation]
│   ├── log_recommendations()         — persist to DB (ON CONFLICT DO NOTHING)
│   ├── acknowledge()                 — ACTIVE → ACKNOWLEDGED
│   ├── resolve()                     — ACTIVE|ACKNOWLEDGED → RESOLVED
│   ├── expire_stale()                — mark expired ACTIVE recommendations
│   ├── get_active()                  — list ACTIVE recs for a domain
│   ├── get_history()                 — full audit trail (all statuses)
│   ├── summary()                     — counts by status + action_code
│   └── full_response_cycle()         — detect + generate + log + return
│
└── get_response_engine()             — convenience factory
```

---

## Consequences

### Positive
- OMNIX transitions from passive detection to **controlled response governance** — a qualitative capability jump for institutional clients.
- `full_response_cycle()` is a single call that delivers the complete anomaly → recommendation pipeline.
- Lifecycle model (ACTIVE → ACKNOWLEDGED → RESOLVED) gives operations teams a structured workflow with full traceability.
- `anomaly_recommendations` table provides an auditable history of every governance anomaly and how it was handled — critical for due diligence, regulatory review, and investor audits.
- The engine is fully mockable and has zero real-DB tests — safe to integrate without DB changes.

### Negative / Accepted Trade-offs
- Recommendations are advisory only. There is no mechanism to enforce that operators act on a CRITICAL recommendation within the urgency window. A monitoring layer (Phase 6+) would close this gap.
- `expire_stale()` must be called externally (by a daemon or cron). The engine does not self-schedule expiry.
- `SUSPEND_RECALIBRATION` and `REDUCE_POSITION_SIZING` are worded as recommendations. The actual suspension or sizing change must be implemented at the application layer separately — Phase 5 only names and logs the recommendation.

### Neutral
- The `anomaly_recommendations` table is append-only in normal usage (ON CONFLICT DO NOTHING). History is never deleted. This is intentional for audit integrity.

---

## References

- ADR-018: Decision Contradiction Index (DCI) — ALIGNED/TENSIONED/CONTRADICTORY bands
- ADR-119: Governance Hardening — BS_HIGH coherence escalation (ADR-119 escalation events)
- ADR-120: AVM Auto-Recalibration (TRIGGER_AVM_REVIEW recommendation target)
- ADR-125: Phase 1 Critical Core Tests
- ADR-126: Phase 2 Receipt Archival HOT/WARM/COLD
- ADR-127: Phase 3 Filter Calibration Metrics (event collection layer)
- ADR-128: Phase 4 Calibration Insight Engine (anomaly detection layer, input to Phase 5)
