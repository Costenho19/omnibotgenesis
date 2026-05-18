# ADR-161: Governance Policy Interoperability Layer (GPIL)

**Status:** Accepted
**Date:** May 14, 2026
**Author:** Harold Nunes — OMNIX QUANTUM LTD
**Supersedes:** None
**Extends:** ADR-159 (Runtime Governance Continuity) · RFC-ATF-2
**Related:** ADR-156 (Agent Trust Fabric), ADR-157 (Temporal Authority Admissibility),
             ADR-158 (Cross-Domain Trust Portability), ADR-160 (RPOL)

---

## Context

RFC-ATF-2 defines the Runtime Governance Continuity protocol and establishes eight
formal invariants (RGC-INV-001–008) that every ATF-RGC-Compliant implementation
MUST satisfy. Those invariants are non-negotiable structural properties — they
cannot be relaxed by any sovereign runtime.

RFC-ATF-2 touches implicitly but does not formalize a structural distinction
that becomes critical in multi-runtime deployments:

> Two sovereign runtimes could validate the same ML-DSA-65 signed ATF receipt
> successfully and still reach different governance conclusions.

This identifies a **Policy Divergence Surface** — the space where two fully
compliant runtimes make different governance decisions using identical
cryptographic artifacts. This surface is not a defect; it is an intended
property of the sovereign runtime model. But it requires formal specification
to be operable.

### The Core Distinction

**Cryptographic Interoperability:**
Any party with the issuer's Dilithium-3 public key can verify the ML-DSA-65
signature on any RCR, CEE, or RC. This is unconditional and binary — the
receipt either passes signature verification or it does not. This is fully
defined by RFC-ATF-2 §5.4 and ATF-INV-006.

**Governance Interoperability:**
The governance conclusion derived from a verified receipt depends on parameters
that RFC-ATF-2 leaves to each runtime's policy. Two runtimes that both achieve
ATF-RGC compliance may disagree on whether a specific RCR indicates acceptable
continuity.

The divergence sources are not bugs — they are **policy parameters**: configurable
within protocol-defined bounds, sovereign to each runtime, and not resolvable
by cryptographic verification alone.

### Why This Requires Formal Specification

Without a formal Policy Parameter Registry:
1. Cross-runtime governance decisions are opaque — a third party cannot
   determine whether two runtimes agree on governance interpretation
2. Compliance audits cannot distinguish "different policy" from "non-compliant"
3. Multi-cloud and multi-party ATF deployments cannot establish governance
   contracts between runtimes
4. The distinction between a protocol violation and a policy choice is
   undefined

---

## Decision

### 1. The Interoperability Taxonomy

ADR-161 formally establishes three distinct interoperability layers for
ATF implementations:

```
Layer 1 — Cryptographic Interoperability (CI)
  Scope: Signature verification of ATF artifacts (RCR, CEE, RC, DR, TAR)
  Requirement: Unconditional. Any verifier with the Dilithium-3 public key
               can verify any artifact. Defined by RFC-ATF-1 §7.6 + RFC-ATF-2 §14.
  Variability: None. Binary pass/fail.

Layer 2 — Protocol Interoperability (PI)
  Scope: Conformance to RFC-ATF-2 structural invariants (RGC-INV-001–008)
  Requirement: All ATF-RGC-Compliant implementations MUST satisfy all 8
               invariants without exception.
  Variability: None. All invariants are hard constraints.

Layer 3 — Governance Policy Interoperability (GPI)
  Scope: Agreement between runtimes on governance policy parameters
  Requirement: Optional. Two runtimes MAY diverge on policy parameters
               within their allowed ranges without violating compliance.
  Variability: Full — within bounds defined in §2 (Policy Parameter Registry).
```

**The Policy Divergence Surface is entirely within Layer 3.**
Layers 1 and 2 are fully deterministic across all compliant runtimes.

### 2. Governance Policy Parameter Registry

The following parameters are formally recognized as **governance policy
parameters** — configurable by each sovereign runtime within the stated
bounds. Parameters outside these bounds constitute non-compliance.

#### 2.1 Authority Fragmentation Guard Limit

| Parameter | Symbol | Default | Min | Max | Protocol bound |
|---|---|---|---|---|---|
| AFG Fragmentation Limit | `AFG_FRAGMENTATION_LIMIT` | 0.90 | 0.01 | 0.95 | Hard max 0.95 |

**Divergence scenario:** Runtime A sets `AFG_FRAGMENTATION_LIMIT=0.80`.
Runtime B sets `AFG_FRAGMENTATION_LIMIT=0.95`. An aggregate reaching 0.85
of the chain root budget would be **blocked by A but permitted by B**. Both
are compliant; the receipts they issue are cryptographically valid; but their
governance conclusion differs.

**Cross-runtime contract:** When two runtimes need governance alignment on
AFG, they MUST negotiate and declare a shared `AFG_FRAGMENTATION_LIMIT`
value via a governance contract (see §4, Cross-Runtime Governance Contracts).

#### 2.2 Reauthorization Challenge TTL

| Parameter | Symbol | Default | Min | Max | Protocol bound |
|---|---|---|---|---|---|
| RC TTL | `RGC_RC_TTL_SECONDS` | 300 | 30 | 3600 | Hard max 3600s |

**Divergence scenario:** Runtime A issues an RC with TTL=300s. A verifying
runtime B with TTL_policy=600s would not have auto-HALTed at second 301 had
it been the issuer. The HALT decision is bound to the **issuing runtime's
policy**, not the verifier's.

#### 2.3 Context Drift Definition

| Parameter | Type | Default | Allowed range | Protocol bound |
|---|---|---|---|---|
| Context drift measurement methodology | Implementation-defined | Euclidean distance over task-scope vector | Any monotonic [0%, 100%] function | Function MUST be monotonic |

This is the **widest divergence surface** in the protocol. RFC-ATF-2 defines
`context_drift_pct` as an input to the CES formula but deliberately does not
define how it is measured. Two runtimes measuring the same execution may
report different `context_drift_pct` values for identical operational events.

**Implications:**
- A CES of 72.0 on Runtime A may correspond to a CES of 83.5 on Runtime B
  for the same execution — because D-component inputs differ.
- Both CES values are cryptographically valid.
- Neither runtime is non-compliant.
- The governance conclusion (NOMINAL vs MONITORING) is legitimately different.

#### 2.4 Anomaly Definition and Counting

| Parameter | Type | Default | Protocol bound |
|---|---|---|---|
| Anomaly detection criteria | Implementation-defined | N governance events matching anomaly patterns | Integer count ≥ 0; contributes I = max(0, 100 − (active_anomalies × 10)) |

Similar to context drift: the protocol defines the I-component formula but
not what constitutes an anomaly. Runtime A may count 2 anomalies for a set
of events that Runtime B counts as 3 or 0.

#### 2.5 Sampling Strategy Parameters

| Parameter | Default | Allowed range |
|---|---|---|
| SHORT/NOMINAL interval | 0s | 0–60s |
| MEDIUM/NOMINAL interval | 300s | 60–3600s |
| LONG/NOMINAL interval | 3600s | 300–86400s |
| STREAMING/NOMINAL interval | 30s | 5–300s |
| Critical multiplier | 6× | 2×–20× |

**Divergence scenario:** Two runtimes monitor the same STREAMING execution.
Runtime A samples every 30s (NOMINAL), Runtime B samples every 10s. Runtime B
will detect a CES degradation event ~20 seconds earlier than Runtime A.
The Continuity Chain artifacts are identical in structure but differ in
temporal density.

#### 2.6 Governance Risk Tier Assignment (ADR-160)

| Parameter | Type | Protocol bound |
|---|---|---|
| Tier assignment logic | Implementation-defined | Must map to LOW / STANDARD / HIGH / CRITICAL |
| LOW tier: skip PQC + DB | Policy choice | Permitted per ADR-160 §4 |
| HIGH/CRITICAL tier: sync persistence | Policy choice | HALT path MUST use sync (RGC-INV-003) |

**Divergence scenario:** Runtime A classifies a given operation as STANDARD
(async persistence). Runtime B classifies the same operation as HIGH (sync).
Both are valid; Runtime B provides stronger persistence guarantees for that
operation at the cost of higher latency.

### 3. Invariant Parameters (Non-Negotiable)

The following are NOT policy parameters — they are protocol invariants that
all ATF-RGC-Compliant implementations MUST use exactly as specified:

| Parameter | Fixed value | Invariant |
|---|---|---|
| CES formula | T×0.30 + B×0.30 + D×0.20 + I×0.20 | RGC-INV-002 |
| NOMINAL threshold | CES ≥ 75.0 | RFC-ATF-2 §6.3 |
| MONITORING threshold | 50.0 ≤ CES < 75.0 | RFC-ATF-2 §6.3 |
| WARNING threshold | 25.0 ≤ CES < 50.0 | RFC-ATF-2 §6.3 |
| CRITICAL threshold | 10.0 ≤ CES < 25.0 | RFC-ATF-2 §6.3 |
| HALT threshold | CES < 10.0 | RFC-ATF-2 §6.3 |
| RC issuance range | CRITICAL (10 ≤ CES < 25) | RFC-ATF-2 §10 |
| B-component formula | budget_remaining / budget_admission × 100 | RFC-ATF-2 §6.2 |
| I-component formula | max(0, 100 − active_anomalies × 10) | RFC-ATF-2 §6.2 |
| T-component: expired DR | 0.0 | RGC-INV-007 |
| AFG hard max | 0.95 | RFC-ATF-2 §8.2 |
| content_hash algorithm | SHA-256 over canonical JSON (sort_keys=True) | RFC-ATF-2 §5.3 |
| PQC algorithm | ML-DSA-65 (FIPS 204) | RFC-ATF-2 §5.4 |
| HALT → sibling revocation | Unconditional | RGC-INV-003 |
| RC expiry → auto-HALT | Unconditional | RGC-INV-008 |

**These values cannot be changed by any runtime for any reason.** A runtime
that uses a different CES formula, different threshold values, or a different
hash algorithm is NOT ATF-RGC-Compliant regardless of any other properties.

### 4. Cross-Runtime Governance Contracts

When two or more ATF-RGC-Compliant runtimes need to reach **governance-aligned**
decisions (not just cryptographically valid ones), they MUST establish a
**Cross-Runtime Governance Contract (CRGC)** that declares:

```json
{
  "crgc_id": "CRGC-{16HEX}",
  "parties": ["runtime-A-identity", "runtime-B-identity"],
  "effective_from": "ISO-8601",
  "expires_at": "ISO-8601",
  "invariant_version": "RFC-ATF-2-v1.0.0",
  "policy_parameters": {
    "afg_fragmentation_limit": 0.85,
    "rc_ttl_seconds": 300,
    "context_drift_methodology_ref": "task-scope-euclidean-v1",
    "anomaly_criteria_ref": "OMNIX-ANOMALY-SPEC-v1",
    "sampling_profile": "STREAMING",
    "governance_risk_tier_policy": "HIGH"
  },
  "content_hash": "...",
  "pqc_signatures": ["<party-A-dilithium3-signature>", "<party-B-dilithium3-signature>"]
}
```

A CRGC is itself a PQC-signed artifact — it is a governance contract, not
merely a configuration agreement. Both parties sign it with their respective
Dilithium-3 keys. `pqc_signatures` is an ordered array aligned to `parties`.

**A CRGC does not modify protocol invariants.** It only aligns the policy
parameters from §2 between the parties. Invariants from §3 remain
unconditionally fixed.

### 5. Compliance Designations

ADR-161 introduces a new compliance designation layer on top of RFC-ATF-2:

```
ATF-RGC-Compliant (existing, RFC-ATF-2)
  All 8 invariants satisfied. Policy parameters within bounds.
  Two ATF-RGC-Compliant runtimes have Layer 1 + Layer 2 interoperability.

ATF-GPI-Aligned (new, ADR-161)
  ATF-RGC-Compliant AND parties have established a valid CRGC.
  Two ATF-GPI-Aligned runtimes have Layer 1 + Layer 2 + Layer 3
  interoperability — full governance agreement, not just cryptographic.
```

The distinction matters for:
- **Multi-cloud deployments:** Runtimes across cloud providers need Layer 3
  alignment to make consistent enforcement decisions.
- **Regulatory audits:** Auditors cannot assume two compliant runtimes
  made the same governance decision — they must check CRGC existence.
- **Cross-organizational delegation chains:** A DR issued by Organization A
  and used by Organization B's runtime may be evaluated differently unless
  a CRGC exists.

### 6. The Formal Resolution

The policy divergence problem translates formally to:

> "Cryptographic interoperability is a property of Layer 1.
>  Governance interoperability is a property of Layer 3.
>  RFC-ATF-2 fully specifies Layer 1 and Layer 2.
>  ADR-161 specifies the boundary, the parameter space,
>  and the coordination mechanism for Layer 3."

The receipt remaining cryptographically valid across divergent runtimes is
**not a weakness** of the protocol. It is a deliberate property:
- It enables sovereign runtimes to set policy appropriate to their
  risk context.
- It separates the tamper-evidence concern (Layer 1) from the
  policy-enforcement concern (Layer 3).
- It allows governance policy to evolve without breaking existing
  cryptographic audit trails.

---

## Consequences

### Positive

- **Formal clarity:** The distinction between invariants and policy is now
  explicit and machine-verifiable.
- **Cross-runtime contracts:** CRGC provides a standards-track mechanism
  for multi-party governance alignment without requiring platform lock-in.
- **Audit correctness:** Compliance auditors now have a clear framework:
  verify invariants → verify policy bounds → verify CRGC (if alignment required).
- **Academic contribution:** ADR-161 formalizes the "cryptographic vs governance
  interoperability" distinction raised in the research commentary, anchoring
  it as a first-class ATF concept.

### Neutral

- Existing ATF-RGC-Compliant implementations are unchanged — ADR-161 is
  additive. No existing invariant is modified.
- CRGC is optional — single-runtime deployments do not need it.

### Negative

- Cross-runtime governance alignment now requires explicit CRGC negotiation
  (previously this was informal or assumed).

---

## Implementation Notes

- **CRGC schema** is defined in §4 of this ADR. Wire format: JSON + ML-DSA-65 signature.
- **Policy Parameter Registry values** can be read from environment variables
  (same convention as existing ATF parameters — see `replit.md`).
- **No code changes required** for existing ATF-RGC implementations to become
  GPIL-aware — ADR-161 is a protocol-layer specification.
- **Reference document:** RFC-ATF-2 §21 "Interoperability Boundaries" (added
  concurrently) is the normative specification. This ADR is the rationale document.

---

## References

- RFC-ATF-2 §21 "Interoperability Boundaries" (added concurrently with this ADR)
- RFC-ATF-2 §6 (CES), §8 (AFG), §10 (RC TTL), §12 (Invariants)
- ADR-159 — Runtime Governance Continuity (RGC)
- ADR-160 — RCR Performance Optimization Layer (Governance Risk Tier)
- ADR-171 — Semantic Governance Interoperability Protocol (SGIP) — Layer 4 extension
