# Security Analysis of the Agent Trust Fabric Protocol
## Nine Attack Classes and Their Mitigations

**Document ID:** OMNIX-SA-ATF-2026-001
**Date:** May 2026
**Author:** Harold Nunes — OMNIX QUANTUM LTD
**Covers:** RFC-ATF-1 (v1.0.0) + RFC-ATF-2 (v1.0.0)
**Status:** Internal · Pre-publication draft

---

## Abstract

This document provides a structured security analysis of the Agent Trust
Fabric (ATF) protocol across its full four-layer stack: Identity (L1),
Delegation (L2), Temporal Authority (L3), and Runtime Continuity (L4).

Nine attack classes are identified, classified using an ATF-specific
taxonomy derived from STRIDE, and analyzed against protocol invariants,
implementation controls, and residual risk. For each attack class, the
document specifies: the attack vector, the invariant or mechanism that
mitigates it, the residual risk after mitigation, and the detection
signature available to an independent verifier.

All mitigations described are implemented in the reference implementation
(`omnix_core/agents/atf/`) and verified by the test suite (82 tests
for the runtime layer alone).

---

## 1. Threat Classification Framework

ATF artifacts are subject to two categories of adversary:

**Protocol-level adversary:** An entity that attempts to forge, replay,
or manipulate ATF artifacts (DRs, TARs, RCRs, CEEs, RCs) to gain or
exercise authority not legitimately granted.

**Runtime adversary:** An entity that attempts to manipulate the runtime
inputs to the Continuity Eligibility Score (CES) or the Authority
Fragmentation Guard (AFG) to prevent legitimate termination or to trigger
false HALTs.

Threat classes are labeled TM-001 through TM-009, matching the ATF Threat
Model taxonomy (`docs/atf/ATF-THREAT-MODEL.md`).

---

## 2. Attack Analysis

---

### TM-001: Receipt Replay Attack

**Layer:** L2 (Delegation) / L3 (Temporal)

**Description:**
An adversary captures a valid Delegation Receipt (DR) or Temporal
Admissibility Record (TAR) from a previous execution and attempts to
reuse it to authorize a new execution after the original has expired or
been revoked.

**Attack mechanism:**
1. Adversary intercepts DR with `status = ACTIVE` during a valid execution.
2. After DR expiry or revocation, adversary presents the captured DR
   to the verification endpoint.
3. If the verifier relies only on the embedded `status` field (which was
   `ACTIVE` at capture time), the replay succeeds.

**Mitigations:**

*ATF-INV-005 (Receipt Immutability):* DRs are immutable once issued.
The `status` field reflects state at issuance, not current state.
Verifiers that perform online verification query the live lattice state.

*TAR temporal binding:* Every TAR carries `execution_ns` — the nanosecond
of admission. A replayed TAR's execution_ns will be in the past relative
to the new execution's admission time. The TAR engine rejects TARs where
`execution_ns` is older than the configurable replay window.

*Anti-replay registry:* The platform maintains a Redis-backed anti-replay
registry keyed by `(delegation_id, execution_ns)`. Replayed combinations
are rejected (configurable via `OMNIX_ANTI_REPLAY_MODE=strict`).

**Residual risk:** LOW. Offline verifiers cannot check current DR status
without platform access. ATF-INV-006 (independent verifiability) is
preserved by design — offline verification confirms cryptographic
integrity, not current liveness. Liveness requires online verification.

**Detection signature:** Replayed TARs produce `execution_ns` in the
past relative to the current admission window. Verifier output will show
`temporal_valid: false` with `execution_ns` older than expected.

---

### TM-002: Delegation Receipt Forgery

**Layer:** L2 (Delegation)

**Description:**
An adversary attempts to forge a DR without possessing the delegating
principal's Dilithium-3 private key, in order to grant unauthorized
authority to an agent they control.

**Attack mechanism:**
1. Adversary constructs a DR with elevated `authority_budget_granted`.
2. Adversary computes a content_hash from the forged fields.
3. Adversary submits the forged DR for verification.

**Mitigations:**

*ATF-INV-002 (Receipt Signing):* Every DR MUST be signed by the delegating
principal's Dilithium-3 private key. The signature covers the content_hash,
which is the SHA-256 digest of all DR fields except the signature fields.

*ML-DSA-65 post-quantum security:* Dilithium-3 provides 128-bit
post-quantum security under the Module Learning With Errors (MLWE) hardness
assumption. Forgery requires solving MLWE — computationally infeasible for
both classical and quantum adversaries.

*Content hash construction:* The content_hash is computed from a
canonicalized, sorted-key JSON serialization of all payload fields.
Any field modification invalidates the hash, which invalidates the signature.

**Residual risk:** NEGLIGIBLE. Forgery would require either breaking
ML-DSA-65 or stealing the delegating principal's private key. Key
compromise is addressed in TM-006.

**Detection signature:** Forged DRs produce `hash_valid: false` or
`pqc_signature_valid: false` in any compliant verifier.

---

### TM-003: Authority Expansion (MAR Violation)

**Layer:** L2 (Delegation)

**Description:**
An adversary attempts to issue a DR granting more authority than the
delegating principal possesses, violating the Monotonic Authority
Reduction invariant and escalating privileges beyond what was granted.

**Attack mechanism:**
1. Agent A holds DR with `authority_budget_granted = 60`.
2. Agent A issues a sub-delegation with `authority_budget_granted = 80`.
3. If the sub-delegation is accepted, Agent B has more authority than A.

**Mitigations:**

*ATF-INV-001 (MAR):* Every DR MUST have `authority_budget_granted ≤
authority_budget_delegator`. The lattice engine enforces this check at
DR creation time. Violations raise `MARViolationError`.

*Verification check:* Every verifier recomputes MAR from DR fields.
`mar_invariant_valid` is false if the invariant is violated.

*Budget ceiling:* ATF-INV-004 enforces that no DR may grant a budget
exceeding 100.0 — the maximum Tier-1 authority.

**Residual risk:** LOW. MAR is enforced at issuance and at verification.
An adversary who successfully forges a DR signature (TM-002) could also
violate MAR in the forged DR. Residual risk is bounded by TM-002 residual.

**Detection signature:** `mar_invariant_valid: false` in verifier output.
`authority_budget_granted > authority_budget_delegator` is detectable
by any party with access to both values.

---

### TM-004: Clock Drift Attack

**Layer:** L3 (Temporal) / L4 (Runtime Continuity)

**Description:**
An adversary who controls the system clock attempts to manipulate
`execution_ns` to extend the temporal validity window of a TAR or
to artificially inflate the T-component of the CES.

**Attack mechanism (TAR):**
1. Adversary advances system clock to make a TAR appear more recent.
2. A freshness check against `execution_ns` passes incorrectly.

**Attack mechanism (CES):**
1. Adversary sets `time_remaining_ns` artificially high.
2. T-component = `time_remaining_ns / total_dr_lifetime_ns × 100` is
   inflated, preventing CES from dropping to WARNING or CRITICAL.

**Mitigations:**

*Monotonic clock requirement (RGC-INV-006):* The continuity chain enforces
that each RCR's `execution_ns` is strictly greater than its predecessor's.
Clock rollback is detected and rejected.

*Engine-computed time values:* The CES engine computes `time_remaining_ns`
from `time.time_ns()` (system monotonic clock) against `dr_expires_at_ns`.
Agent-reported time values are never used.

*TAR execution_ns range:* TAR issuance validates that `execution_ns` is
within ±30 seconds of the server time at issuance.

**Residual risk:** MEDIUM. An adversary with OS-level clock control could
manipulate both the TAR nanosecond and the CES T-component. Deployments in
adversarial environments SHOULD use a hardware time source or external NTP
authority with clock validation.

**Detection signature:** Clock drift produces execution_ns values that
are inconsistent with the timestamps of other system events. An independent
verifier comparing multiple RCRs in a chain can detect non-monotonic
execution_ns sequences.

---

### TM-005: Delegation Chain Poisoning

**Layer:** L2 (Delegation) / L3 (Temporal)

**Description:**
An adversary inserts a malicious DR into the middle of a delegation chain
to redirect authority, change the scope, or introduce a fake chain root.

**Attack mechanism:**
1. Adversary intercepts the chain between Agent A (delegator) and Agent B
   (delegate).
2. Adversary issues a forged DR appearing to come from Agent A, delegating
   to an adversary-controlled Agent C instead of Agent B.
3. Agent C now operates with Agent A's authority scope.

**Mitigations:**

*ATF-INV-003 (Chain Root Traceability):* Every DR in a chain carries
`chain_root_id` — the DRID of the first DR issued by the Tier-1 human
principal. A poisoned DR would require forging a DR that correctly
references the legitimate `chain_root_id` AND is validly signed by the
claimed intermediate delegator. This requires TM-002 (DR Forgery).

*Parent linkage:* Each DR carries `parent_delegation_id` linking it to
its immediate parent. Chain traversal from leaf to root detects breaks
in the signed lineage.

*Chain Completeness Score (CCS):* The ATF CCS metric flags chains where
intermediate DRs are missing or unverifiable.

**Residual risk:** LOW. Chain poisoning requires DR forgery (TM-002).
Residual risk is bounded by TM-002 residual.

---

### TM-006: Delegator Key Compromise

**Layer:** L1 (Identity) / L2 (Delegation)

**Description:**
An adversary obtains a delegating principal's Dilithium-3 private key
and uses it to issue fraudulent DRs with full cryptographic validity.

**Mitigations:**

*Key-per-agent isolation:* Each agent holds its own Dilithium-3 key pair.
Compromise of one agent's key does not compromise the chain root or other
agents.

*Scope constraints in DR:* Even with a compromised key, issued DRs are
constrained by the MAR invariant — the compromised agent cannot grant
more authority than it holds.

*Receipt immutability:* Receipts issued by the compromised key before
compromise are not retroactively invalidated — their historical validity
is preserved. Post-compromise DRs can be identified by timeline analysis.

*Revocation:* The affected agent's AID can be removed from the lattice
and existing DRs flagged as `REVOKED`. Downstream RCRs will show
`integrity_score` decremented by the `active_anomalies` mechanism.

**Residual risk:** HIGH until revocation is executed. Revocation latency
is the primary residual risk window. Deployments SHOULD configure
automated anomaly detection that triggers revocation on abnormal
DR issuance patterns.

---

### TM-007: DAG Cycle Injection

**Layer:** L2 (Delegation) / L4 (Runtime Continuity)

**Description:**
An adversary attempts to introduce a cycle into the Trust Lattice (DAG)
or the Continuity Chain, enabling circular authority references or
infinite chain traversal.

**Attack mechanism (Lattice):**
1. Adversary issues DR from Agent B back to Agent A when A→B already exists.
2. Chain traversal enters an infinite loop or produces false chain roots.

**Attack mechanism (Continuity Chain):**
1. Adversary attempts to insert an RCR with `predecessor_rcr_id` pointing
   to a later RCR, creating a backward reference.

**Mitigations:**

*TLA+ proven acyclicity:* The Trust Lattice acyclicity property is proven
in the TLA+ formal specification (`docs/formal/ATF-TLA-SPEC.tla`). The
lattice engine enforces directed-only edges at DR issuance.

*RGC-INV-006 (Chain Acyclicity):* Each RCR's `execution_ns` MUST be
strictly greater than its predecessor's. Backward references produce
`execution_ns` violations detected at insertion time.

**Residual risk:** NEGLIGIBLE. Acyclicity is enforced at write time and
verified at read time. Cycles in the lattice cannot be introduced without
forge capability (TM-002).

---

### TM-008: Authority Fragmentation Attack

**Layer:** L4 (Runtime Continuity)

**Description:**
An adversary (or a misconfigured orchestration system) spawns many
concurrent sub-agents from a single DR, each with individually valid
sub-delegations, but collectively exhausting the authority budget in ways
that individual-level MAR checks cannot detect.

**Attack mechanism:**
1. Agent A holds DR with `authority_budget_granted = 90`.
2. Agent A spawns 15 concurrent sub-agents, each receiving a grant of 60.
3. Each individual grant satisfies MAR (60 ≤ 90). Aggregate: 900.
4. The chain root budget is effectively multiplied by sub-agent count.

**Mitigations:**

*RGC-INV-004 (Authority Fragmentation Guard):*
`aggregate_consumed = Σ budget_at_admission for all ACTIVE sessions on chain_root_id`
If `aggregate_consumed + new_grant > chain_root_budget × AFG_LIMIT`,
the new sub-delegation is rejected with `AuthorityFragmentationViolation`.

*Default AFG_LIMIT = 0.90:* 10% of the chain root budget is permanently
reserved as a continuity buffer — it cannot be delegated.

*Fragmentation score in RCR:* Every RCR reports `fragmentation_score`
(aggregate consumption percentage). Operators can monitor this in real time.

**Residual risk:** LOW. AFG_LIMIT is configurable. If set above 0.95,
the residual fragmentation window increases. Values above 1.0 are rejected.
Multi-instance deployments without distributed AFG state may miss
cross-instance fragmentation (addressed in RFC-ATF-2 §19, Extension Points).

---

### TM-009: CES Manipulation (Phantom NOMINAL)

**Layer:** L4 (Runtime Continuity)

**Description:**
An adversary with partial write access to CES inputs attempts to keep
CES artificially high to prevent legitimate escalation and HALT transitions.

**Attack mechanism:**
1. Adversary controls the `active_anomalies` input to the CES engine.
2. By suppressing anomaly reporting, the I-component stays at 100.
3. Even with degraded temporal and budget components, CES stays above
   CRITICAL threshold.

**Mitigations:**

*Source isolation:* CES components are sourced independently:
- T-component: computed by the engine from `time.time_ns()` — not agent-reported.
- B-component: computed by the engine from session budget state — not agent-reported.
- D-component: sourced from the Scope Authorization Engine (ADR-147) — independent service.
- I-component: sourced from the governance monitoring layer — independent service.

*RGC-INV-002 (Real-Time CES Computation):* CES MUST be computed from
real-time values. Cached inputs raise `InvalidCESInputError`.

*RGC-INV-007 (Input Freshness):* Staleness thresholds: 5 seconds for
CRITICAL sessions, 30 seconds for NOMINAL. Stale inputs raise errors.

**Residual risk:** MEDIUM. If the adversary has OS-level or network-level
access to the Scope Authorization Engine or the anomaly monitoring service,
D and I components can be manipulated. Deployments SHOULD run these services
as isolated, independently authenticated microservices.

**Detection signature:** An external verifier can recompute CES from
the stored component values in the RCR and compare against the stored
`ces_score`. Discrepancy indicates component manipulation at issuance time.

---

## 3. Summary Table

| ID | Attack Class | Layer | Primary Mitigation | Residual Risk |
|---|---|---|---|---|
| TM-001 | Receipt Replay | L2/L3 | Anti-replay registry + TAR temporal binding | LOW |
| TM-002 | DR Forgery | L2 | ML-DSA-65 (FIPS 204) signature | NEGLIGIBLE |
| TM-003 | Authority Expansion | L2 | MAR invariant (ATF-INV-001) | LOW |
| TM-004 | Clock Drift | L3/L4 | Monotonic clock + engine-computed values | MEDIUM |
| TM-005 | Chain Poisoning | L2/L3 | Chain root traceability + CCS | LOW |
| TM-006 | Key Compromise | L1/L2 | Per-agent key isolation + revocation | HIGH (pre-revocation) |
| TM-007 | DAG Cycle Injection | L2/L4 | TLA+-proven acyclicity + RGC-INV-006 | NEGLIGIBLE |
| TM-008 | Authority Fragmentation | L4 | AFG (RGC-INV-004) | LOW |
| TM-009 | CES Manipulation | L4 | Source isolation + freshness enforcement | MEDIUM |

---

## 4. Independent Verifiability of Security Properties

A critical design property of ATF is that all cryptographic security
properties are independently verifiable without platform access (ATF-INV-006).

For each attack class, an independent verifier (regulator, auditor,
counterparty) can detect a successful attack as follows:

| Attack | Independent Detection Method |
|---|---|
| TM-001 Replay | Compare `execution_ns` against known execution timeline |
| TM-002 Forgery | Recompute content_hash; verify pqc_signature against embedded public key |
| TM-003 Expansion | Verify `authority_budget_granted ≤ authority_budget_delegator` in DR |
| TM-004 Clock Drift | Check execution_ns monotonicity across RCR chain |
| TM-005 Poisoning | Traverse chain from leaf to root; verify each signature |
| TM-006 Key Compromise | DRs issued post-compromise retain valid signatures; detected by timeline |
| TM-007 Cycle | Verify DAG acyclicity by chain traversal |
| TM-008 Fragmentation | Sum `budget_at_admission` across chain; compare to `fragmentation_score` |
| TM-009 CES Manip. | Recompute CES from stored components; compare to stored `ces_score` |

The ATF Public Verifier CLI (`omnix_web/public/omnix_atf_verify.py`) and
the ATF Multi-Protocol Verifier (`/atf-verify`) implement checks for
TM-001, TM-002, TM-003, TM-007, and TM-009 without platform access.

---

## 5. Formal Verification Status

| Property | Formal Method | Status |
|---|---|---|
| MAR (TM-003) | TLA+ (ATF-TLA-SPEC.tla) | Proven |
| Acyclicity (TM-007) | TLA+ (ATF-TLA-SPEC.tla) | Proven |
| Immutability (TM-002) | TLA+ (ATF-TLA-SPEC.tla) | Proven |
| Chain Root Consistency (TM-005) | TLA+ (ATF-TLA-SPEC.tla) | Proven |
| MAR Chain (TM-003) | TLA+ (ATF-TLA-SPEC.tla) | Proven |
| AFG (TM-008) | Unit tests (82/82 passing) | Tested |
| Replay protection (TM-001) | Unit tests + Redis integration | Tested |

---

## References

- RFC-ATF-1 — `docs/standards/RFC-ATF-1.md` · DOI: 10.5281/zenodo.20155016
- RFC-ATF-2 — `docs/standards/RFC-ATF-2.md`
- ATF Threat Model — `docs/atf/ATF-THREAT-MODEL.md`
- TLA+ Specification — `docs/formal/ATF-TLA-SPEC.tla`
- Reference Implementation — `omnix_core/agents/atf/`
- Test Suite — `tests/test_runtime_governance_continuity.py` (82 tests)
