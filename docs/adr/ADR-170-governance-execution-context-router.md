# ADR-170: Governance Execution Context Router (GECR)

**Status:** Accepted  
**Date:** May 17, 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** None  
**Extends:** ADR-050 (CAG) · ADR-138 (UDCL) · ADR-140 (CTAG) · ADR-157 (TAR) · ADR-159 (RGC) · ADR-161 (GPIL/CRGC)  
**Related:** ADR-156 (ATF) · ADR-158 (Cross-Domain Trust) · ADR-160 (RPOL) · RFC-ATF-1 · RFC-ATF-2

---

## Context

A structural question emerges when comparing OMNIX's governance architecture to
runtime-only orchestration systems: does OMNIX govern the **ongoing execution
context** of an agent workflow, or only the **admission boundary**?

The answer requires a precise architectural description that has been implicit
in OMNIX since ADR-050 (March 2026) but was never formalized as a discrete
tier: the **Governance Execution Context Router** (GECR).

### The Orchestration Gap — Formally Stated

ADR-157 introduced the Temporal Admissibility Record (TAR): a nanosecond-
precise, Dilithium-3 signed proof that a Delegation Receipt was valid at the
exact moment of admission. TAR is point-of-admission governance.

ADR-159 introduced Runtime Continuity Records (RCR) and the Continuity
Eligibility Score (CES): a continuous authority health signal that monitors
whether the conditions justifying admission remain valid throughout execution.

ADR-140 introduced the Commit-Time Admissibility Gate (CTAG): a re-evaluation
gate that compares operational conditions at commit time against the baseline
captured at approval time and blocks irreversible commits when drift exceeds
revocation threshold.

ADR-050 introduced the Context Admission Gate (CAG): a session-level pre-
admission gate that routes global operational context before any individual
signal enters the governance pipeline.

ADR-161 introduced Cross-Runtime Governance Contracts (CRGC): bilaterally
PQC-signed contracts that align governance policies between sovereign OMNIX
runtimes before cross-runtime agent operations are authorized.

Each of these components addresses a distinct orchestration concern. What was
missing was a **formal specification of the tier they comprise together** —
and a statement of the invariant that distinguishes this tier from both
"proof-only" and "control-only" governance architectures.

### The Architectural Distinction

Runtime governance systems typically operate in one of two modes:

**Mode A — Control without proof:**  
The system makes real-time orchestration decisions (permit/deny/interrupt
workflow) based on runtime state. The decision is enforced. No independently
verifiable record of the decision exists. Auditability depends on internal
logs owned by the same platform that made the decision.

**Mode B — Proof without continuous control:**  
The system produces a cryptographically signed receipt at the point of
admission. The receipt is independently verifiable. But the receipt is a
snapshot: it answers "was this agent authorized when it started?" and does
not monitor whether authorization remained valid through execution, whether
context drifted, whether sibling agents collectively exhausted the authority
budget, or whether the conditions justifying approval still held at commit time.

OMNIX operates in **Mode C**, which neither Mode A nor Mode B describes:

**Mode C — Control and proof as a single atomic operation:**  
Every orchestration decision — context admission, continuity assessment,
commit-time re-evaluation, cross-runtime authorization, workflow interruption —
produces a Dilithium-3 signed governance receipt before the controlled action
proceeds. The control and the proof are not sequential; they are the same
event. A controlled action without a receipt cannot occur.

The GECR is the formal specification of Mode C.

---

## Decision

### 1. Definition

The **Governance Execution Context Router (GECR)** is the orchestration tier
of the OMNIX platform. It sits above the point-of-admission layer (TAR/AVM)
and below the application layer. Its function is to route, evaluate, and
control the execution context of agent workflows throughout their lifecycle —
not only at the admission boundary.

The GECR comprises six components:

| Component | Module | ADR | Function |
|---|---|---|---|
| Context Pre-Admission Router (CPR) | `context_admission_gate.py` | ADR-050 | Evaluates global operational context before any signal enters the pipeline. Session-level. Fail-closed. |
| Commit-Time Re-Evaluation Gate (CREG) | `commit_time_gate.py` | ADR-140 | Re-evaluates admissibility at the exact nanosecond of irreversible commitment. Computes drift_delta; blocks on REVOKED verdict. |
| Continuity-Aware Admission Controller (CAAC) | `runtime_continuity.py` | ADR-159 | Monitors authority health throughout execution via RCR/CES. HALT at CES < 10. Issues Reauthorization Challenges at CRITICAL. |
| Cross-Agent Budget Enforcer (CABE) | `runtime_continuity.py` AFG | ADR-159 | Enforces aggregate Monotonic Authority Reduction at chain_root_id level. Prevents fragmentation attack across concurrent sub-agents. |
| Workflow Interruption Signal (WIS) | `runtime_continuity.py` HALT | ADR-159 | Propagates HALT atomically to all sibling sessions sharing the same chain_root_id. Cannot be selectively applied to a subset of siblings. |
| Cross-Runtime Policy Router (CRPR) | `docs/adr/ADR-161` CRGC | ADR-161 | Authorizes cross-runtime agent operations only when a bilaterally PQC-signed CRGC exists between the involved runtimes. |

### 2. Receipts as Control Primitives

In the GECR, a governance receipt is not a record of a decision that already
occurred. It is the authorization that makes the next action admissible. The
sequence is:

```
Context evaluated → Receipt issued → Action permitted
```

Not:

```
Action taken → Receipt issued (as record)
```

This ordering is non-negotiable. Every GECR component enforces it. The
implication is that the audit trail produced by the GECR is not a log of
what the system did. It is the authorization chain that made each action
possible. Removing any receipt from the chain invalidates every subsequent
action.

### 3. GECR Pipeline Integration

The GECR components integrate with the Unified Decision Control Layer (UDCL,
ADR-138) at defined injection points:

```
EVALUATION REQUEST
        │
        ▼
[CPR] Layer 0d — Context Pre-Admission Router
        │   Global context evaluated (volatility, liquidity, macro_risk, custom)
        │   CAGResult → embedded in ControlReceipt
        │   BLOCK on inadmissible context → no further evaluation
        ▼
[UDCL] Layers 0–4 — Structural + Pipeline + PQC Receipt + SBE
        │   TAR issued via ATFConnector (ADR-156/157)
        │   PQC receipt generated at Layer 3
        │   Standing margin computed at Layer 4
        ▼
[CREG] Layer 5 — Commit-Time Re-Evaluation Gate (opt-in)
        │   drift_delta = current_margin − original_margin
        │   REVOKED if drift_delta < −0.15 → commit refused
        │   DRIFTED if drift_delta < −0.05 → commit with caveat receipt
        ▼
APPROVED / NARROW / QUARANTINE / REBOUND / HOLD / BLOCKED
        │
        ▼  (for long-running executions)
[CAAC + CABE] RCR/CES continuous monitoring
        │   CES = T×0.30 + B×0.30 + D×0.20 + I×0.20
        │   Snapshots at governed intervals + event-driven on threshold crossing
        │   MONITORING (CES 50–75) → increased sampling
        │   WARNING (CES 25–50)    → restrict sub-task spawning
        │   CRITICAL (CES 10–25)   → issue Reauthorization Challenge
        │   HALT (CES < 10)        → terminate + [WIS] propagate to siblings
        ▼
[CRPR] Cross-runtime (when applicable)
        │   Requires bilaterally PQC-signed CRGC between runtimes
        │   Policy Divergence Surface explicitly declared
        │   ATF-GPI-Aligned status required before cross-runtime admission
        ▼
EXECUTION COMPLETE — full receipt chain, every step independently verifiable
```

### 4. Formal Invariants

#### GECR-INV-001 — Control-Receipt Atomicity

Every GECR orchestration decision is atomic with its governance receipt. No
controlled action proceeds without a receipt being issued first. The receipt
is not a post-hoc record; it is the authorization that makes the action
admissible.

**Implementation:** Layer 3 PQC receipt (ADR-096) is mandatory in the UDCL
pipeline; CTAG verdict is embedded in the ControlReceipt before commit is
permitted; RCR is issued before CES-driven action (HALT, RC).

#### GECR-INV-002 — Bounded Context Drift

The operational context admitted at Layer 0d (CPR) must remain within
evaluated bounds through Layer 5 (CREG). Bounded drift (drift_delta between
−0.05 and −0.15) triggers a DRIFTED receipt, which permits commit but records
the degradation. Unbounded drift (drift_delta < −0.15) triggers REVOKED,
which refuses commit regardless of the original approval.

**Implementation:** CTAG `drift_delta` computation in `commit_time_gate.py`.
Thresholds: `REVOCATION_DRIFT_THRESHOLD = 0.15`, `CAUTION_DRIFT_THRESHOLD = 0.05`.

#### GECR-INV-003 — Cross-Agent Authority Ceiling

The aggregate authority score across all concurrent sub-agents sharing the
same `chain_root_id` must never exceed the Authority Fragmentation Guard (AFG)
limit. The default AFG limit is 0.90 (90% of total budget). The hard protocol
cap is 0.95; values above 0.95 are rejected at the ATF admission layer.

**Implementation:** AFG enforcement in `runtime_continuity.py`. Per-agent MAR
(ADR-156) prevents individual over-delegation; AFG prevents the fragmentation
attack where individually compliant sub-agents collectively exhaust the budget.

#### GECR-INV-004 — Atomic HALT Propagation

A HALT signal triggered by any component of the GECR propagates atomically to
all sibling sessions sharing the same `chain_root_id`. Partial HALT — applying
to a subset of siblings — is not a valid GECR state. Every sibling either
continues under NOMINAL/MONITORING/WARNING/CRITICAL status, or all are HALTED.

**Implementation:** HALT propagation in `runtime_continuity.py`. The
`chain_root_id` is the propagation key. All in-flight sub-tasks are revoked
as part of the HALT operation.

#### GECR-INV-005 — Cross-Runtime Authorization Gate

Cross-runtime agent operations are only authorized when a bilaterally
Dilithium-3 signed Cross-Runtime Governance Contract (CRGC) exists between the
involved runtimes prior to the first cross-runtime admission. The CRGC must
declare the Policy Divergence Surface explicitly: which governance parameters
each runtime governs independently, and which parameters are jointly constrained.
Any parameter not declared in the CRGC divergence surface defaults to the more
restrictive runtime's value.

**Implementation:** CRGC issuance and validation in ADR-161. ATF-GPI-Aligned
status required on cross-runtime receipts.

#### GECR-INV-006 — Reauthorization Challenge TTL Enforcement

Mid-execution Reauthorization Challenges (RC) issued at CRITICAL CES auto-HALT
on TTL expiry without human response. The TTL is bounded and non-extensible.
No mechanism in the GECR permits TTL extension; a new RC with a fresh TTL
requires a new CES evaluation cycle, not an extension of the expired one.

**Implementation:** RC TTL enforcement in `runtime_continuity.py` (RGC-INV-008,
previously specified). GECR-INV-006 restates this as a GECR-tier invariant to
make the TTL non-extension property explicit at the orchestration level.

---

## Consequences

### OMNIX GECR vs. Runtime-Only Governance

The GECR specification clarifies the architectural distinction between OMNIX
and systems that provide runtime control without proof:

| Property | Runtime-Only | OMNIX GECR |
|---|---|---|
| Real-time context evaluation | ✅ | ✅ CAG (Layer 0d) |
| Commit-time drift detection | ❌ | ✅ CTAG (Layer 5) |
| Continuous authority health | ❌ | ✅ RCR/CES (ADR-159) |
| Cross-agent budget enforcement | ❌ | ✅ AFG (GECR-INV-003) |
| Atomic HALT propagation | ✅ (internal log) | ✅ PQC-signed RCR |
| Cross-runtime policy alignment | ❌ | ✅ CRGC (ADR-161) |
| Every orchestration decision independently verifiable | ❌ | ✅ GECR-INV-001 |
| Auditability without platform access | ❌ | ✅ OEP offline bundle (ADR-165) |

The critical differentiator is GECR-INV-001: **control-receipt atomicity**.
A runtime governance system can enforce HALT internally and record it in a
proprietary log. Only protocol-grade governance infrastructure produces a
Dilithium-3 signed receipt for every enforcement event that any party with
the public key can verify independently — without contacting OMNIX.

### GECR vs. "Proof-Only" Governance

Systems that produce cryptographic receipts at the admission boundary but do
not monitor execution context are also distinguishable from the GECR tier:

| Property | Proof-Only | OMNIX GECR |
|---|---|---|
| Point-of-admission proof | ✅ | ✅ TAR (ADR-157) |
| Ongoing context monitoring | ❌ | ✅ RCR/CES |
| Context drift detection | ❌ | ✅ CTAG |
| Workflow interruption | ❌ | ✅ HALT + WIS |
| Mid-execution reauthorization | ❌ | ✅ RC |
| Cross-agent state enforcement | ❌ | ✅ AFG |

A point-of-admission receipt proves the agent was authorized when it started.
It does not prove the agent remained authorized, that its execution context
did not drift beyond the scope for which authority was granted, or that sibling
agents did not collectively exhaust the authority budget.

### Invariant Count Update

ADR-170 introduces 6 new formal invariants (GECR-INV-001–006), raising the
OMNIX formal invariant total to **47** (was 41).

| Family | ADR | Count |
|---|---|---|
| ATF-INV-001–006 | RFC-ATF-1 | 6 |
| TAR-INV-006 | ADR-157 rev.2 | 1 |
| RGC-INV-001–008 | RFC-ATF-2 | 8 |
| GPIL-INV-001–003 | ADR-161 | 3 |
| ELR-INV-001–004 | ADR-162 | 4 |
| EAP-INV-001–007 | ADR-163 | 7 |
| OEP-INV-001–006 | ADR-165 | 6 |
| FEA-INV-001–005 | ADR-166 | 5 |
| FVP-INV-007 | RFC-ATF-3 | 1 |
| **GECR-INV-001–006** | **ADR-170** | **6** |
| **TOTAL** | | **47** |

---

## Formal Statement

> A governance system that enforces runtime behavior controls MUST produce
> independently verifiable proof of each enforcement event. A governance system
> that produces cryptographic receipts at the admission boundary MUST also
> monitor whether the conditions justifying that admission remain valid
> throughout execution.
>
> GECR-INV-001 is the invariant that unifies both requirements: every
> orchestration decision and every enforcement event produces a Dilithium-3
> signed governance receipt before the controlled action proceeds. Control and
> proof are not separable layers. They are a single atomic operation.

---

## ADR References

- ADR-050 — Context Admission Gate (CAG)
- ADR-092 — Structural Admissibility Engine (SAE)
- ADR-096 — PQC Cryptographic Receipt
- ADR-133 — State Provenance Guard (SPG)
- ADR-135 — Conditional Bind Gate (CBG)
- ADR-138 — Unified Decision Control Layer (UDCL)
- ADR-139 — Standing Boundary Engine (SBE)
- ADR-140 — Commit-Time Admissibility Gate (CTAG)
- ADR-156 — Agent Trust Fabric (ATF)
- ADR-157 rev.2 — Temporal Authority Admissibility (TAR + TAR-INV-006)
- ADR-158 — Cross-Domain Trust Portability
- ADR-159 — Runtime Governance Continuity (RGC)
- ADR-160 — RCR Performance Optimization Layer (RPOL)
- ADR-161 — Governance Policy Interoperability Layer (GPIL/CRGC)
- RFC-ATF-1 (DOI: 10.5281/zenodo.20155016) — Agent Trust Fabric
- RFC-ATF-2 (DOI: 10.5281/zenodo.20241344) — Runtime Governance Continuity
- RFC-ATF-3 (DOI: 10.5281/zenodo.20247342) — Forensic Verification Protocol

---

*ADR-170 — Harold Nunes — OMNIX QUANTUM LTD — May 17, 2026*  
*Registered in England & Wales · Operational Headquarters: UAE*
