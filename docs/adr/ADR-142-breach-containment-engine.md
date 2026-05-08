# ADR-142 — Breach Containment Engine (MOD-010)

| Field       | Value                                     |
|-------------|-------------------------------------------|
| **Status**  | Accepted                                  |
| **Date**    | 2026-05-08                                |
| **Author**  | OMNIX Architecture Council                |
| **Module**  | MOD-010 / BCE                             |
| **Layer**   | Infrastructure — Pre-Pipeline             |

---

## Context

OMNIX operates governance pipelines for high-stakes domains (trading, defense, medical AI, autonomous agents). All existing protection layers (AVM, CAG, SPG, CBG) assume a **trusted execution environment**. None of them address the scenario where the infrastructure itself is compromised.

Threat vectors that require infrastructure-level response:
- Cyberattack or intrusion into the OMNIX execution host
- Tampered AVM snapshots (checksum mismatch)
- Timing attacks signaling external instrumentation
- Credential stuffing / brute-force auth bypass attempts
- Operator-detected anomalies requiring immediate halting

Without a Breach Containment Engine, OMNIX has no way to suspend all automated decisions when the environment can no longer be trusted.

---

## Decision

Implement the **Breach Containment Engine (BCE)** as an infrastructure-layer module at `omnix_core/governance/breach_containment.py`.

### Core Behavior

- **CONTAINMENT_ACTIVE**: all governance decisions return `BLOCKED` immediately, regardless of pipeline logic.
- **CONTAINMENT_INACTIVE**: normal pipeline operation. No overhead.
- **Activation**: manual (API/operator) or automated (threat indicators).
- **Release**: requires explicit human authorization (`authorized_by` + `release_note`).

### Fail-Closed (ADR-116)

If the BCE itself fails (DB unreachable, module error):
- `get_status()` returns `is_contained=True`
- Endpoint `/api/governance/breach/status` returns HTTP 503 with `is_contained: true`
- This prevents a compromised BCE from silently clearing containment.

### Threat Indicators (Automated Detection)

| Indicator | Trigger | Severity |
|-----------|---------|----------|
| Timing anomaly | Evaluation latency > 3σ from baseline | HIGH |
| Checksum mismatch | AVM snapshot hash ≠ expected | CRITICAL |
| Auth failure surge | ≥ 10 failures in configurable window | HIGH |
| Manual operator | Direct API call | Operator-specified |
| Process anomaly | External monitoring signal | Operator-specified |

### Containment Lifecycle

```
INACTIVE ──[breach detected]──► ACTIVE ──[authorized release]──► RELEASED
                                   │
                         All decisions: BLOCKED
```

### API Endpoints (5)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET  | `/api/governance/breach/status`   | None | Current containment status (fail-closed) |
| POST | `/api/governance/breach/activate` | API Key | Activate containment |
| POST | `/api/governance/breach/release`  | API Key | Release with authorization |
| POST | `/api/governance/breach/assess`   | API Key | Automated threat assessment |
| GET  | `/api/governance/breach/history`  | API Key | Paginated event history |

### Database

Table: `breach_containment_events`

```sql
CREATE TABLE breach_containment_events (
    id           SERIAL PRIMARY KEY,
    event_id     TEXT        NOT NULL UNIQUE,   -- BCE-{hex12}
    status       TEXT        NOT NULL,           -- ACTIVE | RELEASED
    trigger_code TEXT        NOT NULL,
    severity     TEXT        NOT NULL,           -- CRITICAL | HIGH | MEDIUM
    summary      TEXT        NOT NULL,
    detail       JSONB,
    triggered_by TEXT,
    released_by  TEXT,
    release_note TEXT,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    released_at  TIMESTAMPTZ,
    is_active    BOOLEAN     NOT NULL DEFAULT TRUE
);
```

### SDK Support

Added to Python SDK (`OmnixClient`):
- `breach_status()` — public, no auth
- `breach_activate(trigger_code, severity, summary, triggered_by, detail)`
- `breach_release(event_id, authorized_by, release_note)`
- `breach_assess(latency_ms, expected_latency_ms, latency_sigma, avm_snapshot_hash, …)`
- `breach_history(status, limit, offset)`

Added to Node.js SDK (`OmnixClient`): matching TypeScript methods.

### Frontend

Dashboard page: `/breach` — `omnix_web/src/pages/BreachDashboard.tsx`
- Live status banner (red/green)
- Event history table
- 8-second auto-refresh

---

## Consequences

**Positive:**
- Closes the infrastructure security gap not addressed by AVM/CAG/SPG/CBG.
- Fail-closed by default — false positive containment is always preferable to false negative.
- Human-in-the-loop for release: no automated recovery without authorization.
- All events are auditable and persisted.

**Negative / Trade-offs:**
- False positive containment halts all governance decisions — operators must be trained.
- Manual threat indicators require operator judgment for activation.
- No automated release: if BCE is incorrectly activated, human action is required.

---

## Regulatory Alignment

| Framework | Provision | BCE Mapping |
|-----------|-----------|-------------|
| NIST AI RMF | GV-1.1, MS-2.5 | AI risk policies + incident response |
| EU AI Act | Art. 9 | Risk management — operational monitoring |
| ISO/IEC 42001 | §8.4 | AI management — incident and breach response |
| NIS2 Directive | Art. 21 | Incident handling for critical infrastructure |

---

## Related ADRs

- ADR-116: Fail-Closed Policy (inherited)
- ADR-050: Context Admission Gate (peer: session-level gating)
- ADR-129: Anomaly Response Layer (peer: statistical anomaly detection)
- ADR-138: UDCL v1.x (coordinator that checks BCE status pre-evaluation)
- ADR-141: Module API Wiring (predecessor to this ADR)
- ADR-143: Multi-Domain Risk Governance (co-delivered with this ADR)
