# ADR-178: Counterfactual Governance Engine (CGE)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Supersedes:** None  
**Extends:** ADR-156 (ATF Identity & Delegation) · ADR-174 (AGVP) · ADR-177 (FVS)  
**Related:** ADR-159 (RGC) · ADR-173 (DSPP) · RFC-ATF-5  
**Implements:** `omnix_core/governance/counterfactual_engine.py`  
**Priority Record:** OMNIX-PAR-2026-CGE-001 · May 2026

---

## Context

### The Governance Evidence Gap

Every governance system records what happened. No governance system — in academic literature, regulatory frameworks, or commercial infrastructure — formally records what else could have happened at the same moment under different authority parameters.

This gap is consequential. When a regulator, auditor, or enterprise risk officer reviews a governance decision, the question is not only "was this decision correct?" but "what alternatives existed, and why were they not taken?" A governance record that answers only the first question provides accountability. A governance record that answers both provides **justiciable auditability** — the capacity to reconstruct the full decision space, not just the selected path.

### The Multiverse Problem in Governance

At the moment of any ATF governance evaluation, the following parameters are operationally live:

- `authority_budget_granted` — the delegation ceiling
- `ces_score` — the Continuity Evaluation Score (T×0.30 + B×0.30 + D×0.20 + I×0.20)
- Invariant thresholds: NOMINAL (≥80.0), MONITORING (50.0–79.9), WARNING (30.0–49.9), HALT (<30.0)
- `delegation_depth` — chain length constraint
- `fragmentation_score` — AFG constraint (≤0.90 default)

Each of these parameters could have been set differently — by the delegating principal, by a prior calibration event, or by jurisdiction-specific override. The decision that was recorded is one path through a continuous parameter space. The governance record contains no information about the shape of that space.

### Regulatory Demand for Decision Space Evidence

Emerging AI governance frameworks are beginning to require decision space documentation:

- **EU AI Act Art. 9** — Risk management systems must document "the possible alternatives considered"
- **US NIST AI RMF MAP 1.6** — Contextualizing risks requires understanding of "what might have happened"
- **GCC/DIFC AI Regulation** — Consequential AI decisions must be reviewable in context

No existing ATF record type satisfies this requirement. The CGE closes this gap.

### Competitive Differentiation

No peer governance infrastructure system — including VeriSigil VGS (Zenodo 10.5281/zenodo.20264923), IBM OpenScale, or Microsoft Azure Responsible AI Dashboard — provides cryptographically attested, append-only counterfactual governance paths. This is a structurally novel capability with no existing implementation in the AI governance space.

---

## Decision

### Establish the Counterfactual Governance Engine (CGE)

ADR-178 establishes the **Counterfactual Governance Engine (CGE)** as a first-class protocol component of the ATF governance stack. The CGE operates as a read-only parallel computation layer: at the moment of any governance evaluation, it computes M alternative governance paths using parametric variations of the primary evaluation inputs, seals each path as a cryptographically signed **Counterfactual Fork Record (CFR)**, and assembles the full set into a **Counterfactual Attestation Token (CAT)**.

The CGE is **additive and non-invasive**: primary governance decisions are computed first, sealed, and recorded before any counterfactual computation begins. The CGE cannot modify the primary decision. CGE-INV-002 makes this a hard invariant.

### Record Architecture

#### Counterfactual Fork Record (CFR)

A CFR represents a single alternative governance path. It contains:

```
{
  "cfr_id": "CFR-{16HEX}",
  "primary_receipt_id": "ATFRCR-{...} | ATFTAR-{...}",
  "evaluation_id": "CGE-EVAL-{16HEX}",
  "variation_vector": {
    "authority_budget_delta_pct": -0.20,
    "ces_threshold_nominal_override": 85.0,
    "delegation_depth_limit_override": 2,
    "fragmentation_limit_override": 0.80
  },
  "counterfactual_outcome": "NOMINAL | MONITORING | WARNING | HALT | REJECT",
  "counterfactual_ces_score": 74.5,
  "outcome_diverges_from_primary": true,
  "divergence_invariant_triggered": "RGC-INV-004",
  "posture_state_hash_cf": "sha256:{hex}",
  "issued_at": "{ISO8601 nanoseconds}",
  "cfr_seal": "{Dilithium-3 signature over canonical JSON}",
  "verifiable_fields": [
    "cfr_id", "primary_receipt_id", "variation_vector",
    "counterfactual_outcome", "counterfactual_ces_score",
    "outcome_diverges_from_primary", "issued_at"
  ]
}
```

The `posture_state_hash_cf` is computed identically to the primary posture_state_hash — SHA-256 over canonical JSON of the variation-adjusted committed fields — ensuring counterfactual paths are independently verifiable using the same offline verification procedure as primary records.

#### Counterfactual Attestation Token (CAT)

A CAT is the complete set of CFRs for a single evaluation, assembled as a cryptographically bound artifact:

```
{
  "cat_id": "CAT-{16HEX}",
  "primary_receipt_id": "{receipt that triggered this CAT}",
  "evaluation_timestamp": "{ISO8601 nanoseconds}",
  "cfr_count": 3,
  "cfr_ids": ["CFR-{A}", "CFR-{B}", "CFR-{C}"],
  "cfr_content_hashes": ["sha256:{A}", "sha256:{B}", "sha256:{C}"],
  "cat_root_hash": "sha256(sorted(cfr_content_hashes))",
  "divergence_count": 2,
  "decision_space_summary": {
    "primary_outcome": "NOMINAL",
    "alternative_outcomes": {"NOMINAL": 1, "MONITORING": 2},
    "parameter_sensitivity": "HIGH_CES | LOW_BUDGET"
  },
  "cat_seal": "{Dilithium-3 signature over canonical JSON}",
  "atf_spec_version": "1.4"
}
```

The `cat_root_hash` commits to all CFR content hashes. Any modification to any CFR in the set invalidates the CAT seal — enforcing CGE-INV-004.

### Variation Vector Design

The CGE generates M=3 counterfactual paths by default (configurable via `CGE_FORK_COUNT` env var, range 1–7). Variation vectors are generated deterministically from the evaluation seed using a CSPRNG seeded with `sha256(evaluation_id + primary_receipt_id)`, ensuring reproducibility without storing random state.

Variation bounds are governed by `CGE_MAX_VARIATION_PCT` (default: 0.40, range: 0.05–0.40). No variation may exceed ±40% of any primary parameter value (CGE-INV-005).

### Offline Verifiability

A party possessing only the CAT and the OMNIX public key (available via DNS TXT, HTTPS, and Zenodo DOI) can:

1. Extract the `cfr_content_hashes` and recompute `cat_root_hash`
2. Verify `cat_seal` against the root hash
3. For each CFR: recompute `posture_state_hash_cf` from `variation_vector` + primary record fields
4. Verify `cfr_seal` against canonical CFR JSON

No platform access required. No trust in OMNIX infrastructure required. This satisfies CGE-INV-007.

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS atf_counterfactual_forks (
    id                          SERIAL PRIMARY KEY,
    cfr_id                      TEXT NOT NULL UNIQUE,
    cat_id                      TEXT NOT NULL,
    primary_receipt_id          TEXT NOT NULL,
    evaluation_id               TEXT NOT NULL,
    variation_vector            JSONB NOT NULL,
    counterfactual_outcome      TEXT NOT NULL,
    counterfactual_ces_score    NUMERIC(6,3),
    outcome_diverges_from_primary BOOLEAN NOT NULL,
    divergence_invariant_triggered TEXT,
    posture_state_hash_cf       TEXT NOT NULL,
    cfr_seal                    TEXT NOT NULL,
    issued_at                   TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS atf_counterfactual_tokens (
    id                          SERIAL PRIMARY KEY,
    cat_id                      TEXT NOT NULL UNIQUE,
    primary_receipt_id          TEXT NOT NULL,
    evaluation_timestamp        TIMESTAMP WITH TIME ZONE NOT NULL,
    cfr_count                   INTEGER NOT NULL,
    cfr_ids                     TEXT[] NOT NULL,
    cfr_content_hashes          TEXT[] NOT NULL,
    cat_root_hash               TEXT NOT NULL,
    divergence_count            INTEGER NOT NULL DEFAULT 0,
    decision_space_summary      JSONB NOT NULL,
    cat_seal                    TEXT NOT NULL,
    atf_spec_version            TEXT NOT NULL DEFAULT '1.4',
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cfr_primary_receipt ON atf_counterfactual_forks(primary_receipt_id);
CREATE INDEX IF NOT EXISTS idx_cfr_cat ON atf_counterfactual_forks(cat_id);
CREATE INDEX IF NOT EXISTS idx_cat_primary_receipt ON atf_counterfactual_tokens(primary_receipt_id);
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CGE_ENABLED` | `true` | Enable/disable counterfactual computation |
| `CGE_FORK_COUNT` | `3` | Number of counterfactual paths per evaluation (1–7) |
| `CGE_MAX_VARIATION_PCT` | `0.40` | Maximum parameter variation magnitude |
| `CGE_ASYNC_MODE` | `true` | Compute CFRs asynchronously after primary receipt |
| `CGE_INCLUDE_IN_OEP` | `true` | Include CAT in OMNIX Evidence Package exports |

---

## Invariants

### CGE-INV-001 — Mandatory Fork Production
**Every governance evaluation with `CGE_ENABLED=true` MUST produce a CAT containing at least one CFR before the evaluation is considered complete.**

Rationale: A CAT with zero CFRs provides no decision-space information. The invariant guarantees the minimum useful output.

### CGE-INV-002 — Primary Decision Isolation
**The primary governance decision (DR, TAR, RCR outcome) MUST be identical whether or not CGE is enabled. Counterfactual computation is strictly read-only with respect to the primary governance pipeline.**

Rationale: CGE must not introduce governance side effects. Any platform where enabling CGE changes the primary outcome has a structural defect.

### CGE-INV-003 — CFR PQC Sealing
**Every CFR MUST be sealed with a Dilithium-3 (ML-DSA-65, FIPS 204) signature over its canonical JSON representation using the same signing key as the primary receipt.**

Rationale: CFRs are governance evidence. They carry the same evidentiary weight as primary records and require the same cryptographic protection.

### CGE-INV-004 — CAT Root Hash Integrity
**The `cat_root_hash` of a CAT MUST equal `sha256(sorted(cfr_content_hashes))`. Any modification to any CFR in the set MUST invalidate the CAT seal.**

Rationale: The CAT is only meaningful as a bound set. Individual CFR tampering must be detectable from the CAT alone.

### CGE-INV-005 — Variation Bound
**No parameter in a variation vector may deviate by more than `CGE_MAX_VARIATION_PCT` (default 0.40 = 40%) from the corresponding primary parameter value. Variations outside this bound MUST be rejected and logged.**

Rationale: Extreme variations produce governance paths that are counterfactually meaningless (no principal would have configured parameters that far from the actual configuration). The bound ensures counterfactuals are legally credible.

### CGE-INV-006 — Append-Only Storage
**CFRs and CATs MUST be stored in append-only tables. No UPDATE or DELETE operation is permitted on `atf_counterfactual_forks` or `atf_counterfactual_tokens` after initial insert.**

Rationale: Modifying counterfactual records after the fact would allow retroactive fabrication of favorable alternative paths — the precise attack this system is designed to prevent.

### CGE-INV-007 — Offline Verifiability
**The complete set of counterfactual paths in a CAT MUST be independently verifiable by any party possessing the CAT, the primary receipt, and the OMNIX public key — without any access to OMNIX infrastructure.**

Rationale: Decision-space evidence is only useful if it is trustworthy to parties who do not trust the platform. Offline verifiability is the minimum bar.

---

## Consequences

### Positive

- **Justiciable auditability:** Regulators can reconstruct the full decision space, not just the selected path. Satisfies EU AI Act Art. 9, US NIST AI RMF MAP 1.6.
- **Novel capability:** No peer governance infrastructure system provides cryptographically attested counterfactual governance paths. Structural first-mover position.
- **Sensitivity analysis:** The `decision_space_summary.parameter_sensitivity` field identifies which parameters most influence governance outcomes — invaluable for risk officers.
- **OEP integration:** CATs included in OMNIX Evidence Package exports make counterfactual evidence portable across organizational boundaries.

### Constraints

- `CGE_ASYNC_MODE=true` is required in production to prevent CGE computation from adding latency to the primary governance pipeline.
- `CGE_FORK_COUNT` above 5 is inadvisable in high-throughput environments without dedicated compute allocation.
- CFR storage grows at M × primary receipt storage rate. Retention policy must be configured at the OEP level.

---

## Regulatory Alignment

| Framework | Requirement | CGE Satisfaction |
|---|---|---|
| EU AI Act Art. 9 | Document alternatives considered | CAT documents M alternative governance paths with parameter justification |
| US NIST AI RMF MAP 1.6 | Contextualize risks with alternative scenarios | CFR divergence analysis provides scenario context |
| GCC/DIFC AI Regulation | Consequential decisions reviewable in context | CAT provides full decision-space context per evaluation |
| ISO/IEC 42001 §6.1.2 | Risk treatment alternatives documentation | CAT constitutes formal alternatives documentation |

---

## Priority Record

**OMNIX-PAR-2026-CGE-001**  
Filed: May 2026  
Author: Harold Alberto Nunes Rodelo  
Organization: OMNIX QUANTUM LTD  
Jurisdiction: England & Wales (registered) · UAE (operational)  
Scope: Counterfactual Governance Engine — CFR/CAT record architecture, CGE-INV-001–007  
Classification: Architecture Decision Record — Accepted
