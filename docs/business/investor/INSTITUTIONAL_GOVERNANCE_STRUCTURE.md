# OMNIX — Institutional Governance Structure

**Classification**: Governance Framework  
**Date**: March 6, 2026  
**Status**: ACTIVE  
**ADR Compliance**: ADR-027 (Category Creation), ADR-036 (Exit Governance)  
**Identity**: OMNIX is building the category of Decision Governance Infrastructure — a governance control architecture for automated decision systems.

---

## Canonical Statement

> OMNIX operates under a structured human governance layer with defined executive authority, parameter control, and override mechanisms, designed to scale into multi-party oversight as the platform institutionalizes.

---

## Layer 1 — Human Governance Authority

The Founder Governance Authority holds executive responsibility over all system parameters, deployment decisions, and override mechanisms.

### Current Authority: Harold Nunes, Founder & Product Architect

| Role | Scope | Description |
|------|-------|-------------|
| **Architecture Owner** | System design and evolution | Approves all architectural changes, checkpoint calibration, and engine modifications |
| **Risk Parameter Authority** | Threshold governance | Controls DCI thresholds, ECW configuration, coherence gates, and veto sensitivity |
| **Deployment Approval Authority** | Production releases | Authorizes all deployments to production (Railway). No automated deployment without approval |
| **Override Authority** | Emergency governance | Can override any automated decision in production. Zero overrides exercised to date — the architecture governs itself |

### Governance Principles

- **Separation of concerns**: Human authority governs parameters. The architecture governs execution.
- **No manual trading**: The Founder does not place trades. The system does — only when the architecture permits.
- **Audit-first culture**: Every parameter change is documented via ADR (Architectural Decision Record) before implementation — 171 ADRs active.
- **Fail-closed default**: When in doubt, the system blocks. Human authority reinforces this principle, never overrides it.

---

## Layer 2 — Control Architecture (Automated Execution Discipline)

The governance engine operates autonomously within the parameters set by Layer 1. No single signal can bypass the checkpoint sequence.

### Governance Components

| Component | Function | Governance Role |
|-----------|----------|-----------------|
| **Coherence Engine V5.4** | Structural signal analysis | Blocks execution when internal signals contradict |
| **Decision Contradiction Index (DCI)** | Contradiction quantification | Measures internal disagreement — preservation mode when ≥ 70 |
| **Risk Guardian** | Real-time risk assessment | Monte Carlo validation, Black Swan detection, Kelly Criterion sizing |
| **Decision Trace** | Full audit trail | Every decision logged with complete reasoning chain — 100% telemetry |
| **Circuit Breaker** | Emergency protection | Automatic halt on drawdown limits, connectivity loss, or anomalous behavior |
| **Edge Confirmation Window (ECW)** | Persistence validation | Requires edge to persist across consecutive cycles before execution |

### Architecture Characteristics

- **8-checkpoint sequential entry evaluation** — no checkpoint can be bypassed
- **3-gate exit governance pipeline (EGL)** — automated exit discipline
- **Fail-closed behavior** — if any evaluation fails or times out, execution is blocked
- **Full auditability** — every governance evaluation produces a complete decision trace
- **Domain-agnostic core** — governance logic separable from vertical-specific signals via Domain Adapter pattern (ADR-026)

---

## Layer 3 — Future Institutional Expansion

The architecture is designed to integrate additional governance participants as the platform scales. These roles do not exist today — but the system is built to support them without architectural changes.

### Planned Governance Roles

| Role | Function | Integration Point |
|------|----------|-------------------|
| **Risk Oversight Committee** | Multi-party parameter review | Approves threshold changes via formal governance process |
| **External Auditor** | Independent validation | Read-only access to Decision Trace and audit logs |
| **Compliance Officer** | Regulatory alignment | Automated governance reports for MiCA, ADGM, and other frameworks |
| **Institutional Partner** | Client-specific governance | Custom risk parameters per deployment via white-label configuration |

### Why This Matters Now

The system already produces the data, audit trails, and decision documentation that institutional oversight requires. When these roles are activated, the infrastructure does not need to change — only the access controls and approval workflows expand.

This is the difference between a product that *could* be governed and a product that *is* governed.

---

## Governance vs. Traditional Risk Management

| Dimension | Traditional Risk | OMNIX Governance |
|-----------|-----------------|------------------|
| **Who controls parameters** | Traders or risk managers | Founder Governance Authority with ADR documentation |
| **When does blocking occur** | After threshold violation | Before execution — structural contradiction detection |
| **Audit trail** | Periodic reports | Real-time, every decision, 100% coverage |
| **Override mechanism** | Manual desk override | Formal authority with zero overrides exercised |
| **Scalability** | Add more risk managers | Add governance roles without architecture changes |

---

## Evidence of Governance in Practice

| Evidence | Detail |
|----------|--------|
| Parameter changes documented | 171 ADRs recording every architectural decision |
| Zero manual overrides | All 670,000+ evaluation cycles handled by architecture |
| Fail-closed demonstrated | System blocking execution for 33+ consecutive days under structural contradiction |
| Full audit trail | Decision Trace with complete reasoning chain for every evaluation cycle |
| Production continuity | 24/7 operation since November 2025 without human intervention |

---

## Document Governance

| Attribute | Value |
|-----------|-------|
| Owner | Harold Nunes, Founder Governance Authority |
| Review Cycle | Quarterly or upon governance structure change |
| Distribution | Investors, Due Diligence, Compliance, Board (future) |
| Related Documents | ADR-027 (Category), ADR-025 (Positioning), Governance Behavior Snapshot, Business Model Canvas |

---

*OMNIX — Institutionalizing discipline in automated systems.*
