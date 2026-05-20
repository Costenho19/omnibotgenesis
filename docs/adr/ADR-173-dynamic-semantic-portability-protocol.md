# ADR-173: Dynamic Semantic Portability Protocol (DSPP)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Supersedes:** None  
**Extends:** ADR-171 (SGIP) · ADR-172 (ATORS) · ADR-158 (DTR)  
**Related:** ADR-156 (DR) · ADR-161 (GPIL) · ADR-165 (OEP)  
**Implements:** `omnix_core/agents/atf/dynamic_semantic_portability.py`  
**Priority Record:** OMNIX-PAR-2026-DSPP-001 · May 20, 2026

---

## Context

### The Open Problem Antonio Socorro Identified

ADR-172 (ATORS) establishes Layer 2 (schema portability) and ADR-171 (SGIP) establishes Layer 4
(semantic alignment via SAC). Together they answer the question: *can a receipt be interpreted without
OMNIX at a point in time?* They do not answer the harder question Antonio Socorro articulated in his
cross-system technical review (May 2026):

> *"Where my current research direction starts to diverge slightly is around the idea of sealing
> semantic continuity entirely at receipt creation time. Because while a receipt may preserve
> cryptographic integrity, authority lineage, admissibility state, and contextual constraints,
> the receiving domain may still reinterpret operational meaning differently as: regulatory
> conditions evolve, sovereign policies change, runtime contexts shift, or governance semantics
> diverge over time."*

> *"So the problem that interests me most is whether semantic legitimacy itself can remain
> dynamically preservable across heterogeneous domains without requiring semantic dependency
> on the originating runtime, while also avoiding brittle pairwise semantic negotiation models."*

This is the **Dynamic Semantic Portability Problem (DSPP)** — and it is genuinely unsolved in the
governance infrastructure literature. No existing receipt-based system addresses it. OMNIX addresses
it here with a formal, implementable, offline-verifiable solution.

### Why Existing Layers Do Not Solve It

| Layer | What it solves | What it does NOT solve |
|---|---|---|
| L1 — Cryptographic | Receipt integrity offline | Meaning of receipt fields |
| L2 — ATORS | Field definitions at schema level | Operational meaning drift |
| L3 — GPIL | Policy parameter alignment at issuance | Post-issuance policy evolution |
| L4 — SGIP/SAC | Point-in-time bilateral semantic agreement | Unilateral semantic drift after agreement |

The gap: SAC is a bilateral agreement sealed at a point in time. If Domain B's regulatory context
changes six months after the SAC is signed — new regulations, new sovereign AI policies, new
jurisdictional requirements — the SAC says nothing about whether existing receipts issued under
the original semantic agreement remain portable.

The naive solution is to re-negotiate a new SAC — but this is exactly the "brittle pairwise
semantic negotiation" Antonio identified as inadequate for heterogeneous multi-domain environments
where any domain may interact with dozens of others.

### The DSPP Solution

**Observation:** Every ATF receipt already carries a PQC-signed timestamp. Every SPV (Semantic
Policy Vector, ADR-171) is already a point-in-time snapshot of a runtime's complete semantic
posture. The SPV hash uniquely identifies a specific semantic state.

**Insight:** If a receipt embeds the originating runtime's SPV hash at creation time — a
**Temporal Semantic Anchor (TSA)** — then any receiving domain can reconstruct the exact semantic
context in which the receipt was issued, without contacting the originating runtime, at any future
point in time.

**Mechanism:** When a runtime's semantic posture evolves (new regulations, updated definitions),
it publishes a **Semantic Drift Record (SDR)** — a PQC-signed, append-only artifact documenting
what changed, why, the direction of change, and the quantified drift delta per ATF Core Term.

**Assessment:** A **Retroactive Semantic Assessment (RSA)** can then be computed — entirely
offline, without bilateral negotiation — by comparing the TSA (what the receipt claimed) against
the receiving domain's current SPV, traversing the originating runtime's SDR chain to measure the
**Semantic Distance Unit (SDU)** per term.

**Verdict:** The RSA produces a deterministic, signed DSPP verdict:
`SEMANTICALLY_PORTABLE` · `DRIFT_ACKNOWLEDGED` · `DRIFT_CRITICAL` · `SEMANTICALLY_INCOMPATIBLE`

This is the first formally specified, post-quantum signed, quantified, offline-verifiable mechanism
for dynamic semantic portability of governance receipts across heterogeneous domains. No pairwise
negotiation is required. No originating runtime needs to be online. Drift is made explicit,
quantified, and auditable — not hidden.

---

## Decision

### Layer 5: Dynamic Semantic Portability

DSPP adds a fifth layer to the ATF interoperability stack established by ADR-172 §5:

```
Layer 1 — Cryptographic portability    [ADR-156 + ATORS §3]
  Any verifier with the public key can confirm receipt integrity.

Layer 2 — Schema portability           [ADR-172 / ATORS]
  Any verifier that has consumed ATORS knows what each field means.

Layer 3 — Policy alignment             [ADR-161 / GPIL]
  Two runtimes agree on numerical policy parameters.

Layer 4 — Semantic alignment           [ADR-171 / SGIP / SAC]
  Two runtimes declare and sign their operational definitions of the 8 ATF Core Terms.

Layer 5 — Dynamic semantic portability [ADR-173 / DSPP]  ← NEW
  A receipt remains semantically assessable across time and domain evolution,
  without requiring pairwise re-negotiation or originating runtime availability.
```

### Artifact 1: Temporal Semantic Anchor (TSA)

A TSA is a PQC-signed structure embedded in or attached to any ATF receipt at creation time.
It records the originating runtime's exact semantic posture (SPV hash + SPV version + generation
timestamp) at the moment the receipt was issued.

**Identifier format:** `OMNIX-TSA-{16HEX}`

**TSA fields:**

| Field | Type | Description |
|---|---|---|
| `tsa_id` | string | `OMNIX-TSA-{16HEX}` |
| `receipt_id` | string | The ATF receipt this TSA anchors (DR/TAR/RCR/SAC ID) |
| `receipt_type` | enum | `DR \| TAR \| DTR \| RCR \| SAC` |
| `runtime_id` | string | Originating runtime identifier |
| `spv_id` | string | SPV ID at time of receipt creation |
| `spv_hash` | string | SHA-256 of the originating SPV (the semantic anchor) |
| `spv_version` | string | Semantic version of the originating SPV (e.g. "1.3") |
| `spv_generated_at` | ISO UTC | When the originating SPV was generated |
| `anchored_at` | ISO UTC | When this TSA was created (≤ receipt timestamp) |
| `term_hashes` | dict | Per-term content_hash from originating SPV at anchor time |
| `content_hash` | string | SHA-256 of canonical TSA fields (excludes sig) |
| `pqc_signature` | string | ML-DSA-65 signature over content_hash |
| `pqc_algorithm` | string | `"ML-DSA-65"` |

**DSPP-INV-001:** A TSA must be created at or before receipt issuance time.
`anchored_at ≤ receipt.created_at`. A TSA cannot be added retroactively to an existing receipt
without producing a new receipt with a new content_hash.

**DSPP-INV-004:** The TSA content_hash covers `spv_hash + spv_version + spv_generated_at` of
the originating SPV, in addition to all other TSA fields. This makes the anchor cryptographically
bound to the specific semantic posture, not just the SPV identifier.

### Artifact 2: Semantic Drift Record (SDR)

An SDR is published by a runtime whenever it updates any STR entry (i.e. whenever its SPV changes).
It is append-only, PQC-signed, and references both the previous SPV and the new SPV.

**Identifier format:** `OMNIX-SDR-{runtime_id}-{16HEX}`

**SDR fields:**

| Field | Type | Description |
|---|---|---|
| `sdr_id` | string | `OMNIX-SDR-{runtime_id}-{16HEX}` |
| `runtime_id` | string | Runtime publishing the drift record |
| `previous_spv_id` | string | SPV being superseded |
| `previous_spv_hash` | string | Hash of the superseded SPV |
| `new_spv_id` | string | New SPV taking effect |
| `new_spv_hash` | string | Hash of the new SPV |
| `effective_from` | ISO UTC | When the new SPV takes effect |
| `drift_reason` | string | Human-readable reason (regulatory update, etc.) |
| `drift_category` | enum | `REGULATORY_UPDATE \| POLICY_EVOLUTION \| JURISDICTIONAL \| OPERATIONAL \| CORRECTION` |
| `term_drift_map` | dict | Per-term drift delta (SDU values, 0.0–1.0) |
| `drift_direction` | enum | `MORE_RESTRICTIVE \| LESS_RESTRICTIVE \| LATERAL` per term |
| `governance_impact` | enum | `PORTABLE \| ACKNOWLEDGED \| CRITICAL \| INCOMPATIBLE` |
| `regulatory_anchors` | list | Legal/regulatory references for the drift (e.g. "ADGM-AI-2026-Rev3") |
| `content_hash` | string | SHA-256 of canonical SDR fields |
| `pqc_signature` | string | ML-DSA-65 signature over content_hash |
| `pqc_algorithm` | string | `"ML-DSA-65"` |
| `created_at` | ISO UTC | Creation timestamp |

**DSPP-INV-002:** SDRs are append-only. Regulatory drift cannot be erased from the record.
A runtime that has published an SDR cannot retract it. An SDR can only be superseded by a new
SDR that explicitly references it.

**DSPP-INV-003 (inherits SGIP-INV-003):** When drift_direction is `LESS_RESTRICTIVE` and the
receiving domain's posture is `MORE_RESTRICTIVE`, the more restrictive interpretation governs.
Semantic drift toward permissiveness does not automatically grant permissive interpretation to
existing receipts.

### Artifact 3: Retroactive Semantic Assessment (RSA)

An RSA is a computed, PQC-signed report that answers the question: *given this receipt (anchored
at TSA) and this receiving domain's current semantic posture (its SPV), is the receipt still
semantically portable?*

The RSA is computed entirely offline. No bilateral negotiation. No originating runtime required.

**Identifier format:** `OMNIX-RSA-{16HEX}`

**RSA fields:**

| Field | Type | Description |
|---|---|---|
| `rsa_id` | string | `OMNIX-RSA-{16HEX}` |
| `tsa_id` | string | TSA being assessed |
| `receipt_id` | string | Receipt being assessed |
| `originating_runtime_id` | string | Runtime that issued the receipt |
| `receiving_runtime_id` | string | Domain performing the assessment |
| `originating_spv_hash` | string | SPV hash from the TSA (originating posture) |
| `receiving_spv_hash` | string | Current SPV hash of the receiving domain |
| `assessed_at` | ISO UTC | When the RSA was computed |
| `sdr_chain_traversed` | list | SDR IDs consulted during assessment |
| `term_assessment` | dict | Per-term: `{sdu, drift_direction, status, governing_interpretation}` |
| `aggregate_sdu` | float | Weighted mean SDU across all 8 core terms (0.0–1.0) |
| `dspp_verdict` | enum | `SEMANTICALLY_PORTABLE \| DRIFT_ACKNOWLEDGED \| DRIFT_CRITICAL \| SEMANTICALLY_INCOMPATIBLE` |
| `portability_confidence` | float | 1.0 − aggregate_sdu (0.0–1.0) |
| `governing_posture` | string | `MORE_RESTRICTIVE` (default) or declared override |
| `content_hash` | string | SHA-256 of canonical RSA fields |
| `pqc_signature` | string | ML-DSA-65 signature by the receiving runtime |
| `pqc_algorithm` | string | `"ML-DSA-65"` |

**DSPP-INV-005:** RSA verdicts are deterministic. Given identical TSA, receiving SPV, and SDR
chain, the RSA verdict is always identical. There is no negotiation state. No bilateral state
machine. The assessment is a pure function of public inputs.

**DSPP-INV-006:** A `SEMANTICALLY_INCOMPATIBLE` verdict propagates upward. If a delegation receipt
(DR) in a chain receives a SEMANTICALLY_INCOMPATIBLE verdict in a receiving domain, all receipts
that descend from that DR in the chain are also INCOMPATIBLE in that domain.

### Semantic Distance Unit (SDU) — Normative Specification

The SDU is a normalized measure of semantic divergence between two STR entries for the same term.
Range: `[0.0, 1.0]`. Zero means identical posture. One means completely incompatible postures.

**SDU computation algorithm:**

```python
def compute_sdu(term_a: SemanticTermEntry, term_b: SemanticTermEntry) -> float:
    """
    Computes the Semantic Distance Unit (SDU) between two STR entries
    for the same ATF Core Term.

    The SDU is a weighted combination of three sub-metrics:

    1. boundary_distance (weight 0.40):
       Fraction of boundary_conditions that differ between the two entries.
       Boundary conditions are the operationally critical constraints.

    2. scope_distance (weight 0.35):
       Jaccard distance of the operational_scope sets (domains + jurisdictions).
       1.0 − |A ∩ B| / |A ∪ B|

    3. regulatory_distance (weight 0.25):
       Fraction of regulatory_anchors that do not overlap between entries.
       Regulatory divergence is less operationally critical than boundary divergence.

    Hash-equivalence shortcut: if content_hash_a == content_hash_b, SDU = 0.0.
    """
```

**SDU verdict thresholds (DSPP-INV-007):**

| SDU range | DSPP verdict | Governance meaning |
|---|---|---|
| 0.00 – 0.09 | `SEMANTICALLY_PORTABLE` | No material drift — receipt is fully portable |
| 0.10 – 0.39 | `DRIFT_ACKNOWLEDGED` | Drift exists but resolvable under MORE_RESTRICTIVE |
| 0.40 – 0.69 | `DRIFT_CRITICAL` | Significant drift — receiving domain must explicitly acknowledge |
| 0.70 – 1.00 | `SEMANTICALLY_INCOMPATIBLE` | Receipt cannot be portably interpreted in this domain |

**DSPP-INV-007:** The SDU threshold boundaries (0.10, 0.40, 0.70) are structural constants, not
configurable parameters. They are part of the DSPP specification and cannot be overridden by
runtime configuration. Changing them requires a new ADR.

### No Pairwise Negotiation — Architectural Guarantee

The absence of pairwise negotiation is not a goal — it is a structural property of the design:

1. **TSA is unilateral.** The originating runtime creates the TSA. The receiving domain consumes it.
   No bilateral agreement required.

2. **SDR is unilateral.** Each runtime publishes its own drift records. No bilateral acknowledgment
   required to publish.

3. **RSA is computed locally.** The receiving domain runs the RSA algorithm locally using only:
   - The receipt + its TSA (public artifact)
   - The originating runtime's published SDR chain (public artifact)
   - Its own current SPV (local knowledge)
   No communication with the originating runtime occurs during RSA computation.

4. **Verdicts are deterministic.** The RSA is a pure function. Two different receiving domains
   computing an RSA for the same receipt against the same receiving SPV will always arrive at
   the same verdict. This is verifiable by any third party.

This architecture eliminates the central failure mode Antonio identified: systems that require
constant bilateral re-negotiation as contexts evolve become brittle when domains scale beyond
a handful of bilateral pairs. DSPP scales to arbitrarily many domains with O(1) computation
per receipt per receiving domain.

---

## Implementation

### Files Produced

| File | Description |
|---|---|
| `omnix_core/agents/atf/dynamic_semantic_portability.py` | DSPP engine — TSA · SDR · RSA · SDU |
| `tests/test_dspp.py` | Full test suite — DSPP-INV-001–007 · SDU algorithm · RSA determinism |

### Database Tables

| Table | Purpose |
|---|---|
| `atf_temporal_semantic_anchors` | TSA storage — one per receipt |
| `atf_semantic_drift_records` | SDR append-only log — one per SPV transition |
| `atf_retroactive_semantic_assessments` | RSA results — cached, indexed by tsa_id + receiving_runtime |

### Engine Public API

```python
from omnix_core.agents.atf.dynamic_semantic_portability import DSPPEngine

engine = DSPPEngine(runtime_id="RUNTIME-UAE-OMNIXQUANTUM-20260520")
engine.ensure_tables()

# Create a TSA when issuing a receipt
tsa = engine.create_tsa(
    receipt_id="ATFDR-7F3A9B2C1E4D8F6A",
    receipt_type="DR",
    spv=current_spv,
)

# Publish a Semantic Drift Record when semantic posture changes
sdr = engine.publish_sdr(
    previous_spv=old_spv,
    new_spv=new_spv,
    drift_reason="ADGM AI Governance Framework Rev 3 — updated AUTHORITY definition",
    drift_category="REGULATORY_UPDATE",
    regulatory_anchors=["ADGM-AI-GOVERNANCE-2026-REV3", "FIPS-204-Rev2"],
)

# Assess portability of a receipt in this domain (offline, no negotiation)
rsa = engine.assess_portability(
    tsa=tsa,
    receiving_spv=this_domain_current_spv,
    sdr_chain=originating_runtime_sdr_chain,
)

print(rsa.dspp_verdict)           # "SEMANTICALLY_PORTABLE"
print(rsa.aggregate_sdu)          # 0.03
print(rsa.portability_confidence) # 0.97
```

---

## Invariants — DSPP-INV-001 through DSPP-INV-007

| ID | Statement | Enforcement |
|---|---|---|
| DSPP-INV-001 | TSA creation time ≤ receipt creation time. TSA cannot be added retroactively. | `create_tsa()` rejects anchored_at > receipt.created_at |
| DSPP-INV-002 | SDRs are append-only. A published SDR cannot be retracted. | `publish_sdr()` raises SDRImmutabilityViolation on duplicate previous_spv_hash |
| DSPP-INV-003 | Drift toward permissiveness does not grant permissive interpretation to existing receipts. Unresolved drift defaults to more restrictive. | RSA governing_posture = MORE_RESTRICTIVE when drift_direction = LESS_RESTRICTIVE |
| DSPP-INV-004 | TSA content_hash covers spv_hash + spv_version + spv_generated_at of the originating SPV. | `_compute_tsa_hash()` always includes these three fields |
| DSPP-INV-005 | RSA verdict is deterministic. Identical inputs always produce identical output. | `assess_portability()` is a pure function — no random state, no external calls |
| DSPP-INV-006 | SEMANTICALLY_INCOMPATIBLE verdict propagates upward through delegation chain. | `assess_chain_portability()` halts at first INCOMPATIBLE and marks all descendants |
| DSPP-INV-007 | SDU thresholds (0.10, 0.40, 0.70) are structural constants — not configurable. | Defined as module-level constants, not environment variables |

Total invariant count after ADR-173: **58 invariants** (51 prior + 7 DSPP).

---

## Consequences

### Positive

- **Dynamic semantic portability achieved:** Governance receipts remain assessable across time and
  domain evolution without bilateral re-negotiation or originating runtime dependency.

- **Pairwise negotiation eliminated:** The RSA computation is local, deterministic, and requires
  only public artifacts. N domains can interact without N² bilateral SAC negotiations.

- **Drift is explicit and quantified:** The SDU metric turns a binary (compatible/incompatible)
  question into a continuous governance signal. Institutions can set their own internal SDU
  thresholds for operational decisions while the structural thresholds remain invariant.

- **First-mover position:** DSPP is the first formally specified, PQC-signed, quantified,
  offline-verifiable mechanism for dynamic semantic portability of governance receipts. No
  equivalent specification exists in the governance infrastructure literature as of May 2026.

- **RFC-ATF-4 foundation:** DSPP (together with ATORS/SGIP) provides the complete normative
  basis for RFC-ATF-4: the Dynamic Semantic Portability Protocol specification.

- **Antonio Socorro's research question answered:** The problem he identified is not only solvable —
  it is solved here with a formal specification, a reference implementation, and a test suite.

### Neutral

- DSPP is additive. Existing ATF receipts without TSAs can still be verified at Layers 1–4.
  TSA adoption is progressive — receipts issued after ADR-173 acceptance carry TSAs; older
  receipts operate at L4 maximum.

- SDR publication is voluntary at Layer 5 but required for `ATF-DSPP-Aligned` compliance
  designation.

### Negative

- SDU computation requires access to the originating runtime's published STR entries at the
  time of receipt creation. These must be publicly archived (via OEP or a public STR ledger)
  for full offline RSA computation.

- Term-level boundary condition comparison is fuzzy (text similarity) by default. Implementations
  that formalize boundary conditions in a decidable logic (e.g. first-order logic fragments) will
  achieve more precise SDU computation.

---

## Open Items

| ID | Description | Priority |
|---|---|---|
| DSPP-OI-001 | Public STR ledger endpoint: `GET /api/atf/str/{runtime_id}/{term_id}/history` — enables offline SDR chain reconstruction | HIGH |
| DSPP-OI-002 | OEP bundle extension: include TSA + SDR chain in OEP `META/manifest.json` for fully self-contained offline RSA computation | HIGH |
| DSPP-OI-003 | RFC-ATF-4 draft: DSPP as normative Layer 5 specification — SDU algorithm, TSA format, SDR format, RSA algorithm | MEDIUM |
| DSPP-OI-004 | Formal logic encoding of boundary conditions — replace text similarity with decidable predicate evaluation for SDU computation | LOW |
| DSPP-OI-005 | Cross-runtime SDR ledger federation — protocol for runtimes to publish and discover each other's SDR chains without central coordinator | LOW |

---

## References

- ADR-156 — Agent Trust Fabric (Delegation Receipt)
- ADR-157 — Temporal Authority Admissibility (TAR)
- ADR-158 — Cross-Domain Trust Portability (DTR)
- ADR-159 — Runtime Governance Continuity (RCR)
- ADR-161 — Governance Policy Interoperability Layer (GPIL)
- ADR-165 — OMNIX Evidence Package (OEP)
- ADR-171 — Semantic Governance Interoperability Protocol (SGIP)
- ADR-172 — ATF Open Receipt Schema (ATORS)
- RFC-ATF-1 — DOI: 10.5281/zenodo.20155016
- RFC-ATF-2 — DOI: 10.5281/zenodo.20241344
- RFC-ATF-3 — DOI: 10.5281/zenodo.20247342
- Antonio Socorro (cross-system technical review, May 2026) — problem statement
- `omnix_core/agents/atf/dynamic_semantic_portability.py` — reference implementation
- `tests/test_dspp.py` — conformance test suite
