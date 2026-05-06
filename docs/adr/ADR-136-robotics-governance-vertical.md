# ADR-136: Industrial Robotics Governance Vertical

**Status:** Accepted  
**Date:** 2026-05-06  
**Author:** Harold Nunes, OMNIX QUANTUM  
**Resolves:** Extension of OMNIX governance to the Industrial Robotics and Autonomous Systems domain

---

## Context

Industrial robots, autonomous mobile robots (AMRs), cobots, drones, and autonomous vehicles make real-time decisions that directly impact human safety, property, and liability. The absence of a cryptographically auditable governance layer creates unacceptable risk in regulated sectors (automotive manufacturing, pharmaceutical handling, healthcare logistics).

Standards bodies — ISO 10218 (robot safety), IEC 61508 (functional safety SIL), ISO/TS 15066 (human-robot collaboration), and RIA R15.06 — mandate documented risk assessment and safety verification. OMNIX extends this mandate with cryptographic proof of every governance decision.

## Decision

OMNIX establishes a dedicated **Industrial Robotics Governance Vertical** (`domain: robotics`) with the following characteristics:

### 11-Checkpoint Fail-Closed Pipeline (ISO 10218 / IEC 61508 aligned)

| CP | Gate | Threshold | Standard |
|----|------|-----------|----------|
| CP-1 | Sensor Fusion Integrity | ≥50 | ISO 10218-1 §5.4 |
| CP-2 | Collision Risk Assessment | ≥42 | ISO 10218-2 §5.5 |
| CP-3 | Human Proximity Gate | ≥48 | ISO/TS 15066 |
| CP-4 | Operational Context Validation | ≥45 | RIA R15.06 |
| CP-5 | Battery & Power Integrity | ≥40 | IEC 61508 SIL-2 |
| CP-6 | Payload & Force Limits | ≥44 | ISO 10218-1 §5.6 |
| CP-7 | Environmental Mapping Coherence | ≥46 | IEC 62061 |
| CP-8 | Emergency Stop Readiness | ≥42 | ISO 13850 |
| CP-9 | Cross-Sensor Contradiction Gate | ≥40 | IEC 61508 SIL |
| CP-10 | AML / Liability Attribution | ≥50 | GDPR + EU AI Act |
| CP-11 | Edge Confirmation & Boundary Gate | ≥48 | ISO/TS 15066 |

### Hard Block Conditions (pre-evaluation, fail-closed)

1. **Collision risk > 85%** — Action prohibited immediately (imminent collision)
2. **Sensor confidence < 20%** — Blind robot cannot act safely
3. **Human proximity < 50 cm + speed > 1.5 m/s** — Physical harm threshold (ISO/TS 15066 Table 1)

### Receipt Format

Every approved robotic action generates a PQC-signed receipt:
```
OMNIX-ROB-{12 uppercase hex chars}
Algorithm: Dilithium-3 (NIST FIPS 204 / ML-DSA-65)
```

### Supported Robot Types

- Industrial Arm (6-DOF) — automotive, welding, assembly
- Autonomous Mobile Robot (AMR) — logistics, warehouse
- Collaborative Robot (Cobot) — human-robot handoff zones
- Inspection Drone — pharmaceutical, infrastructure
- Autonomous Ground Vehicle (AGV) — manufacturing floor

### Jurisdictions

EU Machinery Regulation 2023/1230, FDA 21 CFR Part 820 (medical devices), OSHA 29 CFR 1910.217

## Consequences

- Robotics domain joins the 10-vertical OMNIX governance fleet
- All robotic action receipts are independently verifiable via `/verify/{receipt_id}`
- ISO/TS 15066 hard block logic prevents any human-harm-risk action from proceeding
- Interactive demo available at `/governance-demo-robotics`
- Domain key: `robotics` — receipt prefix: `OMNIX-ROB`

## References

- ADR-115: Engine Unification — All Verticals
- ADR-131: Execution Integrity Layer
- ISO 10218-1:2011, ISO 10218-2:2011
- ISO/TS 15066:2016 — Robots and robotic devices: Collaborative robots
- IEC 61508:2010 — Functional Safety (SIL)
- RIA R15.06 — American National Standard for Industrial Robots
