# ADR-157: Temporal Authority Admissibility

**Status:** Accepted  
**Date:** May 12, 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** None  
**Related:** ADR-131 (Execution Integrity Layer), ADR-156 (Agent Trust Fabric)

---

## Context

ADR-156 established that every AI agent delegation event produces a
cryptographically signed Delegation Receipt (DR). A DR proves that an agent
*was* delegated authority. But it does not, by itself, prove that the authority
*was still valid at the exact moment the agent acted*.

A Delegation Receipt can be:
- **Expired** — its `expires_at` has passed
- **Revoked** — a Tier-1 principal explicitly revoked it
- **Superseded** — the agent's authority was modified between issuance and use

Without temporal binding, a sophisticated adversary could:
1. Obtain a legitimate DR before expiry
2. Present it as proof of authorization after expiry
3. Challenge the governance record in a regulatory proceeding

This gap also affects regulatory compliance. EU AI Act Article 13 requires
operators to demonstrate that autonomous systems operated within their
authorized scope at the time of each decision — not merely that they had
authorization at some prior point.

ADR-157 closes this gap by defining the **Temporal Admissibility Record (TAR)**
— a PQC-signed proof that a specific DR was ACTIVE at the exact nanosecond an
execution event was admitted.

---

## Decision

### Temporal Admissibility Record (TAR)

Every time an agent requests admission to execute an action, the
`TemporalAuthorityEngine` issues a **TAR** that is:

1. Issued **synchronously** at the moment of admission request — before the
   execution occurs and before it is logged.

2. Timestamped to **nanosecond precision** using `time.time_ns()`, which
   captures the Unix monotonic nanosecond at the exact moment of the call.

3. PQC-signed (Dilithium-3) over a content hash that includes the nanosecond
   timestamp — making the timestamp cryptographically bound and tamper-evident.

4. Associated with the Delegation Receipt ID, the agent AID, and an optional
   reference to the ExecutionReceipt (ADR-131) that records the action itself.

### TAR Identifier

Format: `ATFTAR-{16HEX}`  
Example: `ATFTAR-C4D8E2F1A3B5C7D9`

### TAR Fields

| Field | Type | Description |
|---|---|---|
| `tar_id` | string | `ATFTAR-{16HEX}` |
| `delegation_id` | string | `ATFDR-{16HEX}` of the authorizing DR |
| `agent_id` | string | `AID-{DOMAIN}-{16HEX}` of the acting agent |
| `execution_ref` | string? | Optional ExecutionReceipt ID (ADR-131) |
| `execution_ns` | int | Nanosecond Unix timestamp of admission |
| `execution_ts` | string | ISO UTC timestamp of admission |
| `dr_status_at_admission` | string | Status of the DR at admission time |
| `dr_expires_at` | string? | DR expiry from the original receipt |
| `authority_budget` | float | Authority budget of the DR |
| `domain` | string | Governance domain |
| `task_action` | string | Action being admitted |
| `admission_status` | string | `ADMITTED` or `REJECTED` |
| `rejection_reason` | string? | Reason for rejection (if any) |
| `content_hash` | string | SHA-256 of all fields except sig fields |
| `pqc_signature` | string? | Dilithium-3 sig over content_hash |
| `pqc_algorithm` | string? | `"dilithium3"` |
| `chain_root_id` | string | chain_root_id of the source DR |
| `issued_at` | string | ISO UTC timestamp of TAR issuance |
| `metadata` | object | Extension dict |

### Admission Logic

```
TAR.admission_status = ADMITTED  if:
    DR.status == ACTIVE
    AND time.time_ns() <= DR.expires_at_ns (if expires_at set)
    AND DR has not been revoked

TAR.admission_status = REJECTED  if any condition above fails
```

Rejected TARs are still issued and persisted — they serve as an audit record
of unauthorized execution attempts.

### Integration with Execution Integrity Layer (ADR-131)

When an agent execution is admitted via TAR, the `execution_ref` field of the
TAR SHOULD be populated with the `ExecutionReceipt.execution_id` from ADR-131.
This creates a bidirectional link:

```
ExecutionReceipt (ADR-131)
    ↕  execution_ref / tar_id cross-reference
TemporalAdmissibilityRecord (ADR-157)
    ↕  delegation_id
DelegationReceipt (ADR-156)
    ↕  chain_root_id
Human Tier-1 Origin
```

This chain answers the complete governance question:

> "Who authorized this agent, under what scope, was the authorization
> valid at the exact nanosecond of execution, and what did the agent do?"

---

## Invariants

| ID | Invariant | Enforcement |
|---|---|---|
| TAR-INV-001 | TAR is issued BEFORE execution is logged | `admit_execution()` must be called synchronously |
| TAR-INV-002 | execution_ns is bound by PQC signature | content_hash includes execution_ns |
| TAR-INV-003 | Expired DRs produce REJECTED TARs | nanosecond comparison against DR expiry |
| TAR-INV-004 | TARs are immutable once issued | content_hash + no UPDATE path in DDL |
| TAR-INV-005 | TAR traces to DR and execution event | delegation_id + execution_ref fields |

---

## Database

Table: `atf_temporal_records` — auto-created idempotently on first request.

Indices:
- `(delegation_id)` — all TARs for a DR
- `(agent_id, admission_status)` — admission history per agent
- `(execution_ns)` — temporal range queries
- `(chain_root_id)` — chain-level audit

---

## API

New endpoints added to `agent_blueprint.py`:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/atf/temporal/admit` | Issue a TAR for an execution event |
| `GET` | `/api/atf/temporal/<tar_id>` | Get a TAR by ID |
| `POST` | `/api/atf/temporal/verify` | Verify a TAR |
| `GET` | `/api/atf/temporal/report/<agent_id>` | Temporal admissibility report |

---

## Consequences

**Positive:**
- Every agent execution has a nanosecond-precise authorization proof
- Regulators can verify temporal validity without platform access
- Connects ATF to the existing Execution Integrity Layer (ADR-131)
- Enables "time-window" governance — authority valid only during defined intervals
- Provides audit evidence for post-hoc investigation of specific actions

**Negative:**
- Small performance overhead at admission (typically < 1ms)
- Requires TAR storage (estimated 512 bytes per record)

**Mitigations:**
- TAR issuance is non-blocking (async persist)
- Storage auto-pruned by retention policy (configurable, default 90 days)

---

## Compliance

| Regulation | Requirement | TAR Coverage |
|---|---|---|
| EU AI Act Art. 13 | Demonstrate authorized scope at time of decision | TAR + DR + ExecutionReceipt chain |
| DORA Art. 9 | ICT risk management — operational control evidence | TAR rejection audit log |
| MiCA Recital 65 | Algorithmic trading controls | TAR admission chain for trading agents |
| SOC 2 CC6 | Logical access controls | TAR + agent_id → human root traceability |
| ISO 27001 A.9.4 | Information system access control | TAR temporal boundary enforcement |
