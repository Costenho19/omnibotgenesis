# ADR-159: Runtime Governance Continuity (RGC)

**Status:** Accepted  
**Date:** May 13, 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** None  
**Related:** ADR-131 (Execution Integrity Layer), ADR-156 (Agent Trust Fabric),
              ADR-157 (Temporal Authority Admissibility), ADR-158 (Cross-Domain Trust),
              ADR-147 (Scope Authorization Record)

---

## Context

ADR-157 introduced the **Temporal Admissibility Record (TAR)** — a nanosecond-precise
cryptographic proof that a Delegation Receipt was valid at the exact moment an execution
was admitted. This closes the point-of-admission governance gap.

However, an admission proof is a snapshot. It answers:

> "Was this agent authorized when it started?"

It does not answer:

> "Is this agent still authorized, and is its authorization still healthy, right now — at
> minute 47 of this 90-minute workflow?"

Enterprise AI systems increasingly operate as **long-running, multi-step executions**
where governance conditions can change mid-flight:

- A Delegation Receipt may expire before the execution completes
- The authority budget may be consumed across parallel sub-tasks below safe thresholds
- Operational context may drift beyond the scope for which authority was originally granted
- Multiple concurrent sub-agents spawned from the same DR may collectively exceed the
  budget that any individual sub-agent would have been denied

No existing framework — including ATF-1 as specified — addresses **runtime authority
health**. Governance frameworks treat delegation as a binary event (granted/not granted)
and leave the ongoing validity of that grant as an assumption rather than a continuously
verifiable state.

### The Runtime Continuity Problem

Identified formally by Akhilesh Warik (Runtime AI Governance Research, May 2026) as
the architectural separation between:

- **Boundary attestation** — proving authority existed at the admission boundary
- **Continuous governability supervision** — monitoring authority health throughout execution

ADR-159 closes this gap by introducing the **Runtime Governance Continuity** layer:
a continuous, cryptographically anchored authority health monitoring system that operates
throughout the lifecycle of a long-running agent execution.

---

## Decision

### 1. Runtime Continuity Record (RCR)

Every long-running execution produces **Runtime Continuity Records** — PQC-signed
authority health snapshots emitted at governed intervals throughout the execution lifecycle.

```
ATFRCR-{16HEX}     e.g. ATFRCR-3F7A2B1C4D5E6F7A
```

An RCR is:
1. Anchored to the admission **TAR** (`tar_id` — required, not nullable)
2. Timestamped to **nanosecond precision** at the moment of sampling
3. Carries a computed **Continuity Eligibility Score (CES)** — see §2
4. Carries a **continuity_status** (NOMINAL / MONITORING / WARNING / CRITICAL / HALT)
5. PQC-signed (Dilithium-3) over its content hash
6. **Immutable** once issued (no UPDATE path)

RCRs form a **continuity chain**: each RCR references its predecessor via
`predecessor_rcr_id`, creating a cryptographic timeline of authority health from
admission to completion.

---

### 2. Continuity Eligibility Score (CES)

The CES is a composite metric (0.0 – 100.0) that quantifies the runtime health of an
agent's authorization at a specific nanosecond.

```
CES = (T × 0.30) + (B × 0.30) + (D × 0.20) + (I × 0.20)
```

**Component definitions:**

| Component | Symbol | Weight | Definition |
|-----------|--------|--------|------------|
| Temporal Health | T | 0.30 | `time_remaining_ns / total_dr_lifetime_ns × 100`. Measures how much of the DR's authorized lifetime remains. |
| Budget Health | B | 0.30 | `budget_remaining / budget_at_admission × 100`. Measures how much authority budget is unconsumed. |
| Context Fidelity | D | 0.20 | `100 - context_drift_pct`. Derived from Scope Authorization Engine (ADR-147) context drift. |
| Integrity Score | I | 0.20 | `100 - (active_anomalies × 10)`. Decremented by 10 per active governance anomaly on the chain. |

**CES thresholds:**

| CES Range | Status | Required Action |
|-----------|--------|-----------------|
| 75 – 100 | `NOMINAL` | Continue. Sample at standard interval. |
| 50 – 75 | `MONITORING` | Continue. Increase sampling frequency. Flag outputs in receipt. |
| 25 – 50 | `WARNING` | Continue with restrictions. Issue Tier-1 alert. Outputs flagged `GOVERNANCE_DEGRADED`. |
| 10 – 25 | `CRITICAL` | Suspend new sub-task spawning. Issue Reauthorization Challenge (RC). Await Tier-1 response. |
| 0 – 10 | `HALT` | Execution terminated. Final RCR issued with `HALT`. All in-flight sub-tasks receive revocation signal. |

**RGC-INV-007:** CES MUST be computed from real-time values — cached or stale inputs are
rejected by the engine with an `InvalidCESInputError`.

---

### 3. Authority Fragmentation Guard (AFG)

When a single Delegation Receipt is used to spawn multiple **concurrent sub-agents**,
each sub-delegation individually respects MAR. However, the **aggregate** of sub-delegations
may collectively exhaust the budget in ways that no individual delegation would have been
denied.

This is the **Authority Fragmentation Attack** vector — distributing a large grant across
many small delegations to bypass individual-level budget checks.

The AFG closes this by tracking the **aggregate authority consumption** across all
concurrent sub-agents sharing a `chain_root_id`:

```
aggregate_consumed = Σ authority_budget_granted for all ACTIVE DRs in chain

RGC-INV-004: aggregate_consumed ≤ chain_root_budget × AFG_FRAGMENTATION_LIMIT
```

Default `AFG_FRAGMENTATION_LIMIT` = 0.90 (90% — 10% reserved as continuity buffer).

When aggregate consumption exceeds the limit, new sub-delegations are rejected with
`AuthorityFragmentationViolation`. Existing delegations continue unless CES falls below
CRITICAL.

---

### 4. Escalation Protocol

When CES crosses a threshold boundary, the `EscalationProtocol` issues a formal
**Continuity Escalation Event (CEE)**:

```
ATFCEE-{16HEX}
```

A CEE is PQC-signed and carries:
- The triggering RCR ID
- The threshold crossed (status transition)
- The recommended action (ALERT / SUSPEND / REAUTHORIZE / HALT)
- The Tier-1 agent or human designated to receive the escalation
- A TTL for response (default: 300 seconds for CRITICAL, 0 for HALT)

**Reauthorization Challenge (RC):**

When CES drops to CRITICAL, the EscalationProtocol issues a **Reauthorization Challenge**:

```
ATFRC-{16HEX}
```

The RC is a cryptographically signed request to the Tier-1 authority for explicit
reauthorization of the execution. The Tier-1 authority responds by issuing a new
short-lifetime DR (valid for the RC TTL only), which resets the T-component of the CES.

If no reauthorization arrives within TTL, the engine automatically transitions to HALT.

**RC Protocol:**

```
1. Engine detects CES < 25
2. Engine issues ATFRC-{16HEX} (PQC-signed)
3. RC is delivered to designated Tier-1 escalation endpoint
4. Tier-1 issues new DR (linked to RC via metadata.rc_id)
5. Engine validates new DR, resets T-component
6. New RCR issued with refreshed CES
   — OR —
4. TTL expires without response
5. Engine issues HALT RCR
6. In-flight sub-tasks receive revocation signal
```

---

### 5. Sampling Strategy

| Execution Profile | Default Interval | MONITORING Override | CRITICAL Override |
|---|---|---|---|
| SHORT (< 60s) | No sampling | 15s | 5s |
| MEDIUM (60s – 600s) | 60s | 30s | 10s |
| LONG (> 600s) | 120s | 60s | 20s |
| STREAMING (unbounded) | 30s | 15s | 5s |

Intervals are configurable via `RGC_SAMPLE_INTERVAL_SECONDS` environment variable.

---

### 6. RCR — Full Field Specification

| Field | Type | Description |
|---|---|---|
| `rcr_id` | string | `ATFRCR-{16HEX}` |
| `tar_id` | string | Source TAR (admission anchor) — NOT NULL |
| `delegation_id` | string | Source DR being monitored |
| `agent_id` | string | `AID-{DOMAIN}-{16HEX}` of the executing agent |
| `chain_root_id` | string | Human Tier-1 chain origin |
| `execution_ns` | int | Nanosecond Unix timestamp of this sample |
| `execution_ts` | string | ISO UTC of this sample |
| `ces_score` | float | Continuity Eligibility Score (0.0–100.0) |
| `ces_temporal` | float | T-component (0.0–100.0) |
| `ces_budget` | float | B-component (0.0–100.0) |
| `ces_context` | float | D-component (0.0–100.0) |
| `ces_integrity` | float | I-component (0.0–100.0) |
| `continuity_status` | string | NOMINAL / MONITORING / WARNING / CRITICAL / HALT |
| `predecessor_rcr_id` | string? | Previous RCR in the continuity chain |
| `budget_at_admission` | float | Budget at TAR issuance |
| `budget_remaining` | float | Current remaining budget |
| `context_drift_pct` | float | Context drift % from scope engine |
| `active_anomalies` | int | Count of active governance anomalies |
| `dr_expires_at` | string? | DR expiry from source DR |
| `time_remaining_ns` | int | Nanoseconds until DR expiry |
| `fragmentation_score` | float | Aggregate budget consumption % across chain |
| `escalation_event_id` | string? | CEE issued at this sample, if any |
| `reauth_challenge_id` | string? | RC issued at this sample, if any |
| `sample_reason` | string | SCHEDULED / THRESHOLD_BREACH / FRAGMENTATION / EXTERNAL |
| `content_hash` | string | SHA-256 of all fields except sig fields |
| `pqc_signature` | string? | Dilithium-3 signature |
| `pqc_algorithm` | string? | `"dilithium3"` |
| `issued_at` | string | ISO UTC of RCR issuance |
| `metadata` | object | Extension dict |

---

## Invariants

| ID | Invariant | Enforcement |
|---|---|---|
| RGC-INV-001 | Every RCR is anchored to a valid TAR | `tar_id` NOT NULL, validated against `atf_temporal_records` |
| RGC-INV-002 | CES is computed from real-time values only | `InvalidCESInputError` if stale inputs |
| RGC-INV-003 | HALT status terminates execution | Engine issues revocation signal to all active sub-tasks in chain |
| RGC-INV-004 | Aggregate budget never exceeds AFG limit | `AuthorityFragmentationViolation` on breach |
| RGC-INV-005 | All RCRs are PQC-signed and immutable | Content hash + no UPDATE path |
| RGC-INV-006 | Continuity chain is acyclic and complete | `predecessor_rcr_id` links form a monotonically increasing ns timeline |
| RGC-INV-007 | CES inputs must be fresh | Staleness threshold: 5 seconds for CRITICAL, 30 seconds for NOMINAL |
| RGC-INV-008 | Reauthorization Challenge TTL is enforced | Automatic HALT on TTL expiry without response |

---

## Database

### Table: `atf_runtime_continuity`

```sql
CREATE TABLE IF NOT EXISTS atf_runtime_continuity (
    rcr_id                  VARCHAR(64)   PRIMARY KEY,
    tar_id                  VARCHAR(64)   NOT NULL,
    delegation_id           VARCHAR(64)   NOT NULL,
    agent_id                VARCHAR(64)   NOT NULL,
    chain_root_id           VARCHAR(64)   NOT NULL,
    execution_ns            BIGINT        NOT NULL,
    execution_ts            TIMESTAMPTZ   NOT NULL,
    ces_score               FLOAT         NOT NULL,
    ces_temporal            FLOAT         NOT NULL,
    ces_budget              FLOAT         NOT NULL,
    ces_context             FLOAT         NOT NULL,
    ces_integrity           FLOAT         NOT NULL,
    continuity_status       VARCHAR(16)   NOT NULL,
    predecessor_rcr_id      VARCHAR(64)   DEFAULT NULL,
    budget_at_admission     FLOAT         NOT NULL,
    budget_remaining        FLOAT         NOT NULL,
    context_drift_pct       FLOAT         NOT NULL DEFAULT 0.0,
    active_anomalies        INT           NOT NULL DEFAULT 0,
    dr_expires_at           TIMESTAMPTZ   DEFAULT NULL,
    time_remaining_ns       BIGINT        DEFAULT NULL,
    fragmentation_score     FLOAT         NOT NULL DEFAULT 0.0,
    escalation_event_id     VARCHAR(64)   DEFAULT NULL,
    reauth_challenge_id     VARCHAR(64)   DEFAULT NULL,
    sample_reason           VARCHAR(32)   NOT NULL DEFAULT 'SCHEDULED',
    content_hash            VARCHAR(64)   NOT NULL,
    pqc_signature           TEXT          DEFAULT NULL,
    pqc_algorithm           VARCHAR(32)   DEFAULT NULL,
    issued_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    metadata                JSONB         NOT NULL DEFAULT '{}'
);
```

Indices:
- `(tar_id)` — all RCRs for an execution session
- `(delegation_id, continuity_status)` — health monitoring per DR
- `(chain_root_id, execution_ns)` — chain-level timeline queries
- `(continuity_status, issued_at)` — dashboard queries for degraded executions
- `(agent_id, execution_ns)` — agent audit trail

### Table: `atf_continuity_escalations`

```sql
CREATE TABLE IF NOT EXISTS atf_continuity_escalations (
    cee_id                  VARCHAR(64)   PRIMARY KEY,
    rcr_id                  VARCHAR(64)   NOT NULL,
    tar_id                  VARCHAR(64)   NOT NULL,
    delegation_id           VARCHAR(64)   NOT NULL,
    agent_id                VARCHAR(64)   NOT NULL,
    chain_root_id           VARCHAR(64)   NOT NULL,
    threshold_crossed       VARCHAR(16)   NOT NULL,
    recommended_action      VARCHAR(32)   NOT NULL,
    ces_at_escalation       FLOAT         NOT NULL,
    escalation_ns           BIGINT        NOT NULL,
    response_ttl_seconds    INT           NOT NULL DEFAULT 300,
    response_received_at    TIMESTAMPTZ   DEFAULT NULL,
    response_dr_id          VARCHAR(64)   DEFAULT NULL,
    resolved                BOOLEAN       NOT NULL DEFAULT FALSE,
    resolution_status       VARCHAR(32)   DEFAULT NULL,
    content_hash            VARCHAR(64)   NOT NULL,
    pqc_signature           TEXT          DEFAULT NULL,
    pqc_algorithm           VARCHAR(32)   DEFAULT NULL,
    issued_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    metadata                JSONB         NOT NULL DEFAULT '{}'
);
```

---

## API

New endpoints added to `agent_blueprint.py`:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/atf/continuity/start` | Start a runtime continuity session (anchored to TAR) |
| `POST` | `/api/atf/continuity/sample` | Emit a manual RCR sample |
| `GET` | `/api/atf/continuity/<rcr_id>` | Get a specific RCR |
| `GET` | `/api/atf/continuity/session/<tar_id>` | Full continuity chain for an execution |
| `GET` | `/api/atf/continuity/health/<delegation_id>` | Current CES for an active DR |
| `POST` | `/api/atf/continuity/reauthorize` | Submit reauthorization response to a RC |
| `GET` | `/api/atf/escalations/<chain_root_id>` | All escalation events for a chain |

---

## Consequences

**Positive:**
- Closes the governance survivability gap: authority health is now continuously monitored,
  not assumed
- Provides regulators with a cryptographic timeline of authority health for any execution
- Enables automated response to authority degradation without human latency
- Authority Fragmentation Guard closes a non-obvious attack vector in multi-agent systems
- Reauthorization Challenge provides a formal, verifiable escalation protocol
- All artifacts independently verifiable offline (RGC-INV-005)

**Negative:**
- Runtime overhead of CES computation at each sample (typically < 2ms)
- Additional DB writes per long-running execution
- Requires context drift signal from Scope Authorization Engine (ADR-147)

**Mitigations:**
- CES computation is CPU-only, no external calls
- DB writes are async (non-blocking on execution path)
- Context drift defaults to 0.0 if ADR-147 is unavailable (degrades gracefully)

---

## Patent Landscape

ADR-159 introduces the following novel technical claims suitable for IP protection:

1. **Continuity Eligibility Score (CES):** A composite, weighted, real-time metric
   for AI agent authority health, computed from temporal, budget, context, and integrity
   components. No prior art exists for a continuously-computed authority health score
   during AI agent execution.

2. **Runtime Continuity Record (RCR):** A PQC-signed, TAR-anchored, immutable artifact
   that creates a cryptographic timeline of authority health throughout a long-running
   execution. Distinguishable from audit logs in that it is: (a) pre-committed before
   sampling, (b) cryptographically bound to the source admission proof (TAR), and
   (c) part of an acyclic chain verifiable without platform access.

3. **Authority Fragmentation Guard (AFG):** A protocol that enforces aggregate budget
   constraints across concurrent sub-agents sharing a delegation chain root, preventing
   authority fragmentation attacks that individual-level MAR cannot detect.

4. **Reauthorization Challenge Protocol:** A formal, cryptographically signed mid-execution
   authority renewal protocol where a challenged execution can receive a fresh short-lifetime
   DR from a Tier-1 authority to reset its temporal CES component, with automatic HALT
   on TTL expiry. No prior art exists for a mid-execution authority renewal protocol
   with cryptographic binding to the admission event.

5. **TAR-Anchored Continuity Chain:** A linked sequence of RCRs anchored to an
   admission TAR, forming a monotonically advancing cryptographic timeline that connects
   point-of-admission to point-of-completion (or termination), verifiable by any party
   with the platform public key.

---

## Compliance

| Regulation | Gap Closed by ADR-159 |
|---|---|
| EU AI Act Art. 13 | Continuous evidence of authorized scope throughout execution, not only at admission |
| EU AI Act Art. 9 | Risk management extends to runtime authority degradation, not only design-time assessment |
| DORA Art. 9 | ICT operational control evidence for the full duration of autonomous actions |
| MiCA Recital 65 | Algorithmic trading: CES provides continuous position authority validation |
| SOC 2 CC6 | Logical access controls enforced and evidenced throughout execution lifetime |
| ISO 27001 A.9.4 | Information access control: runtime enforcement, not just admission-time |
| NIST AI RMF Govern 1.4 | Continuous monitoring of AI system behavior within authorized parameters |

---

## Related Future Extensions

- **RCR → VC Export:** Export RCR chains as W3C Verifiable Presentations for cross-org
  governance verification
- **Predictive CES:** ML model trained on historical CES trajectories to predict CRITICAL
  events 60–120 seconds before threshold crossing
- **Multi-Instance Synchronization:** Sync fragmentation guard across horizontally scaled
  OMNIX instances via Redis CES state broadcast
