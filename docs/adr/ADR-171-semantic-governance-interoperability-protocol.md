# ADR-171: Semantic Governance Interoperability Protocol (SGIP)
## Layer 4 — Semantic Interoperability for Cross-Runtime ATF Deployments

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Supersedes:** None  
**Extends:** ADR-161 (Governance Policy Interoperability Layer) · RFC-ATF-3  
**Related:** ADR-156 (Agent Trust Fabric) · ADR-157 (Temporal Authority Admissibility) · ADR-159 (Runtime Governance Continuity) · ADR-170 (GECR)

---

## Context

### The Unresolved Layer of Cross-Runtime Governance

ADR-161 established three interoperability layers for ATF-compliant runtimes:

- **Layer 1 — Cryptographic Interoperability (CI):** Binary, unconditional. ML-DSA-65 signature verification is identical across all verifiers.
- **Layer 2 — Protocol Interoperability (PI):** Structural. All ATF-RGC-Compliant runtimes share the CES formula, threshold definitions, and invariant table.
- **Layer 3 — Governance Policy Interoperability (GPI):** Parametric. Two PI-compliant runtimes may configure policy parameters (AFG limit, RC TTL, sampling profile, risk tier, drift methodology, anomaly criteria) within protocol-defined bounds.

The Cross-Runtime Governance Contract (CRGC, ADR-161 §4) enables two runtimes to negotiate and bilaterally sign a set of aligned Layer 3 parameters. This provides deterministic cross-runtime governance verdicts for the six Policy Divergence Surface dimensions.

**What the GPIL does not address — and what this ADR formalizes:**

Two runtimes may satisfy all three layers simultaneously — identical cryptographic verification, identical CES formula and thresholds, bilaterally signed CRGC with aligned numerical parameters — and still derive **structurally different governance conclusions** for the same operation, because they hold different operational definitions of the core concepts the protocol is built upon.

The six Policy Divergence Surface parameters in ADR-161 govern *how* the protocol operates numerically. What they do not govern is *what the protocol means* when it uses the terms: authority, admissibility, trust, sovereignty, risk, escalation, revocation, and legitimacy.

### The Semantic Divergence Problem

Consider two ATF-RGC-Compliant runtimes — Runtime A (deployed by a European financial institution under MiFID-II) and Runtime B (deployed by a UAE sovereign fund under ADGM financial regulations):

Both runtimes:
- Share the same ML-DSA-65 public key infrastructure
- Use the identical CES formula with the same threshold values
- Have a valid, bilaterally signed CRGC with aligned AFG limit, RC TTL, and sampling profile

Yet they may reach different governance verdicts for the same Delegation Receipt because:

| Concept | Runtime A (MiFID-II) | Runtime B (ADGM) |
|---|---|---|
| **Authority** | Budget granted by a licensed natural person under ESMA registration | Budget granted by a legal entity under DFSA authorization |
| **Revocation** | Triggered by FCA instruction, MiFID-II §25 compliance event, or AML alert | Triggered by DFSA notification or ADGM Market Rules §8.3 compliance event |
| **Legitimacy** | Decision is legitimate if it has EU AI Act Art.14 oversight chain | Decision is legitimate if it satisfies ADGM AI Governance Framework §4 |
| **Escalation** | CES < 25 AND market volatility > 2σ of 30-day baseline | CES < 25 AND exposure > regulatory position limit |
| **Sovereignty** | Runtime cannot be governed by a principal outside EU jurisdiction | Runtime is sovereign within ADGM Financial Centre jurisdiction |

A CRGC with aligned numerical parameters does not — and cannot — resolve these differences. They are not parameter choices. They are semantic postures: the operational meaning the runtime assigns to its governance concepts in the context of its regulatory and organizational environment.

**This is not a defect.** Sovereign semantic autonomy is a feature, not a problem. The problem is that currently there is no mechanism to:
1. **Declare** these semantic postures formally and immutably
2. **Expose** the divergence surface between two specific runtimes
3. **Bind** both parties cryptographically to their declared definitions
4. **Audit** whether a cross-runtime governance decision was taken with full semantic transparency

Without this mechanism, semantic divergence is invisible in the audit trail. A forensic examiner looking at a CRGC sees aligned parameters but cannot determine whether the parties held compatible definitions of the concepts those parameters govern.

### Why This Matters at Institutional Scale

**For regulators:** Two compliant runtimes may interpret "revocation" differently. Without formal semantic declarations, an auditor cannot determine whether a revocation event was treated consistently across systems.

**For legal proceedings:** A cross-runtime governance decision may be challenged on the grounds that "legitimacy" was interpreted differently by the two runtimes involved. Without a bilaterally signed semantic declaration, neither party has a verifiable record of what they each understood legitimacy to mean at the time of the decision.

**For multi-jurisdiction deployments:** A DR issued under EU AI Act authority and evaluated by an ADGM-regulated runtime may produce different admission verdicts — not because of cryptographic failure, not because of parameter mismatch, but because "admissibility" carries different regulatory meaning in each context. This needs to be declared, not discovered.

**For institutional buyers:** A procurement committee evaluating two ATF deployments may find that both are "RFC-ATF-2 compliant" with valid CRGCs — yet the governance decisions they produce are semantically incompatible. The SGIP provides the mechanism to detect and declare this in advance of any cross-runtime operation.

---

## Decision

### 1. Architecture: Layer 4 — Semantic Interoperability (SI)

ADR-171 establishes a fourth interoperability layer in the ATF taxonomy:

```
Layer 1 — Cryptographic Interoperability (CI)          [ADR-156/RFC-ATF-1]
  Unconditional. ML-DSA-65 signature verification.
  Variability: None.

Layer 2 — Protocol Interoperability (PI)               [ADR-159/RFC-ATF-2]
  CES formula, invariant table, threshold definitions.
  Variability: None.

Layer 3 — Governance Policy Interoperability (GPI)     [ADR-161/RFC-ATF-3]
  Six parametric divergence surface dimensions.
  Variability: Bounded by protocol-defined min/max.

Layer 4 — Semantic Interoperability (SI)               [ADR-171 — this document]
  Operational definitions of ATF core concepts.
  Variability: Sovereign, declared, bilaterally witnessed.
```

Layer 4 does not constrain sovereign semantic choices. It makes them visible, immutable, and cryptographically committed.

**The key property of Layer 4:** A runtime that has published a Semantic Term Registry entry for a term can never silently change its definition. Any modification produces a new hash, which invalidates any Semantic Alignment Certificate that referenced the previous definition. The semantic audit trail is as tamper-evident as the governance receipt chain.

### 2. Semantic Term Registry (STR)

The Semantic Term Registry is a per-runtime, append-only, PQC-signed store of formal definitions for governance concepts. Each entry defines exactly one term within the runtime's operational context.

#### 2.1 STR Entry Schema

```json
{
  "str_entry_id": "STR-{runtime_id}-{term_id}-{16HEX}",
  "runtime_id": "RUNTIME-{jurisdiction}-{organization}-{date}",
  "term_id": "AUTHORITY | ADMISSIBILITY | TRUST | SOVEREIGNTY | RISK | ESCALATION | REVOCATION | LEGITIMACY",
  "term_version": "1.0",
  "definition": {
    "formal_statement": "string — authoritative operational definition",
    "boundary_conditions": ["condition_1", "condition_2"],
    "regulatory_anchors": ["EU-AI-ACT-ART-14", "FIPS-204"],
    "out_of_scope": ["explicit_exclusion_1"],
    "examples": [
      {
        "case": "descriptive case",
        "verdict": "IN_SCOPE | OUT_OF_SCOPE",
        "rationale": "string"
      }
    ]
  },
  "operational_scope": {
    "domains": ["TRADING", "MEDICAL_AI"],
    "jurisdictions": ["EU", "UAE"],
    "agent_tiers": ["TIER-2", "TIER-3"]
  },
  "effective_from": "ISO-8601",
  "supersedes": "STR-{previous_entry_id} | null",
  "content_hash": "SHA-256 over canonical JSON of all fields above",
  "pqc_signature": "ML-DSA-65 signature over content_hash",
  "pqc_algorithm": "ML-DSA-65"
}
```

**Immutability property (SGIP-INV-001):** An STR entry, once published and signed, is immutable. A runtime may publish a new version of a term (incrementing `term_version` and setting `supersedes`), but the hash of the original entry is permanently part of any SAC that referenced it. Any Semantic Alignment Certificate issued against version 1.0 remains verifiable against 1.0 indefinitely, even after 2.0 is published.

#### 2.2 ATF Core Term Set

The following eight terms constitute the **ATF Core Term Set** — the minimum set that any runtime seeking Layer 4 interoperability MUST define in its STR before a Semantic Alignment Certificate can be issued (SGIP-INV-002):

| Term ID | Governance Concept | Why It Matters for Cross-Runtime Governance |
|---|---|---|
| `AUTHORITY` | What constitutes delegated authority in this runtime's context | A DR may carry identical numerical budget on two runtimes that define authority differently under their respective regulatory frameworks |
| `ADMISSIBILITY` | The necessary and sufficient conditions for an action to be admitted | TAR admission criteria may differ beyond the temporal window — regulatory pre-clearance, position limits, etc. |
| `TRUST` | The trust model between agents and principals in this runtime | Determines how chain_root_id is interpreted and what "human oversight" means in practice |
| `SOVEREIGNTY` | The boundaries of this runtime's governance sovereignty | Determines what cross-runtime operations require explicit authorization vs. are rejected outright |
| `RISK` | The operational definition of risk in this runtime's governance context | AVM scoring, AFG calibration, and CES context-component measurement all depend on the underlying risk model |
| `ESCALATION` | The conditions that constitute an escalation event requiring elevated governance | RC issuance logic and HALT propagation semantics depend on what the runtime considers an escalation-worthy condition |
| `REVOCATION` | The events that invalidate an active delegation or admission | Determines when DR status transitions from ACTIVE to REVOKED — differences here can produce divergent TAR verdicts |
| `LEGITIMACY` | What makes a governance decision legitimate in this runtime's context | The ultimate criterion against which HALT, APPROVED, and QUARANTINE verdicts are evaluated operationally |

These eight terms are the exact concepts that Layer 1–3 interoperability assumes are shared but never declares. SGIP makes this assumption explicit and testable.

### 3. Semantic Policy Vector (SPV)

A Semantic Policy Vector is a signed, point-in-time snapshot of a runtime's STR entries for all eight ATF Core Term Set terms. It is the "semantic fingerprint" of a runtime at a specific moment.

#### 3.1 SPV Schema

```json
{
  "spv_id": "OMNIX-SPV-{runtime_id}-{ISO-date}-{16HEX}",
  "runtime_id": "RUNTIME-{jurisdiction}-{organization}-{date}",
  "generated_at": "ISO-8601",
  "atf_core_term_set": {
    "AUTHORITY":     { "str_entry_id": "STR-...", "content_hash": "sha256:..." },
    "ADMISSIBILITY": { "str_entry_id": "STR-...", "content_hash": "sha256:..." },
    "TRUST":         { "str_entry_id": "STR-...", "content_hash": "sha256:..." },
    "SOVEREIGNTY":   { "str_entry_id": "STR-...", "content_hash": "sha256:..." },
    "RISK":          { "str_entry_id": "STR-...", "content_hash": "sha256:..." },
    "ESCALATION":    { "str_entry_id": "STR-...", "content_hash": "sha256:..." },
    "REVOCATION":    { "str_entry_id": "STR-...", "content_hash": "sha256:..." },
    "LEGITIMACY":    { "str_entry_id": "STR-...", "content_hash": "sha256:..." }
  },
  "extended_terms": {},
  "spv_hash": "SHA-256 over canonical JSON of atf_core_term_set entries",
  "pqc_signature": "ML-DSA-65 signature over spv_hash",
  "pqc_algorithm": "ML-DSA-65"
}
```

The `spv_hash` is a single value that represents the complete semantic posture of the runtime. Two runtimes with identical `spv_hash` values are semantically equivalent. Two runtimes with different `spv_hash` values have at least one divergent term — the Semantic Alignment Certificate will identify exactly which ones.

### 4. Semantic Alignment Certificate (SAC)

The Semantic Alignment Certificate is the Layer 4 extension of the Cross-Runtime Governance Contract. It incorporates the SPVs of both parties and produces an explicit, bilaterally signed map of semantic alignment, acknowledged divergence, and unresolved gaps.

A SAC is OPTIONAL for Layer 3 (CRGC) interactions but REQUIRED for any cross-runtime governance operation that claims Layer 4 interoperability (ATF-SGIP-Aligned designation, see §6).

#### 4.1 SAC Schema

```json
{
  "sac_id": "OMNIX-SAC-{16HEX}",
  "crgc_id": "CRGC-{16HEX}",
  "parties": {
    "runtime_a": {
      "runtime_id": "RUNTIME-EU-ARDENT-20260501",
      "spv_id": "OMNIX-SPV-...",
      "spv_hash": "sha256:a3f8c2..."
    },
    "runtime_b": {
      "runtime_id": "RUNTIME-UAE-SOVEREIGN-20260501",
      "spv_id": "OMNIX-SPV-...",
      "spv_hash": "sha256:b7d4e1..."
    }
  },
  "effective_from": "ISO-8601",
  "expires_at": "ISO-8601",
  "semantic_alignment_map": {
    "AUTHORITY": {
      "status": "ALIGNED | ACKNOWLEDGED_DIVERGENCE | UNRESOLVED",
      "runtime_a_hash": "sha256:...",
      "runtime_b_hash": "sha256:...",
      "divergence_resolution": "MORE_RESTRICTIVE | RUNTIME_A | RUNTIME_B | BILATERAL_OVERRIDE | null",
      "divergence_note": "string — human-readable description of the difference"
    },
    "ADMISSIBILITY":  { "status": "...", "..." : "..." },
    "TRUST":          { "status": "...", "..." : "..." },
    "SOVEREIGNTY":    { "status": "...", "..." : "..." },
    "RISK":           { "status": "...", "..." : "..." },
    "ESCALATION":     { "status": "...", "..." : "..." },
    "REVOCATION":     { "status": "...", "..." : "..." },
    "LEGITIMACY":     { "status": "...", "..." : "..." }
  },
  "unresolved_terms": ["LEGITIMACY"],
  "governing_posture": "MORE_RESTRICTIVE",
  "sac_content_hash": "SHA-256 over canonical JSON of parties + semantic_alignment_map",
  "pqc_signatures": [
    "ML-DSA-65 signature by runtime_a over sac_content_hash",
    "ML-DSA-65 signature by runtime_b over sac_content_hash"
  ],
  "pqc_algorithm": "ML-DSA-65"
}
```

#### 4.2 Alignment Status Definitions

| Status | Meaning | Effect on Cross-Runtime Governance |
|---|---|---|
| `ALIGNED` | Both runtimes reference the same STR entry hash for this term | No divergence — cross-runtime governance decisions on operations touching this concept are semantically equivalent |
| `ACKNOWLEDGED_DIVERGENCE` | Both runtimes have defined the term, but with different hashes. Both have reviewed and signed the divergence | The SAC's `divergence_resolution` field specifies which interpretation governs when the two conflict in a cross-runtime operation |
| `UNRESOLVED` | One or both runtimes have not defined the term in their STR, or have refused to sign the other's definition | Per SGIP-INV-003: unresolved terms default to the more restrictive interpretation available. If neither runtime has a definition, the cross-runtime operation on that concept is BLOCKED. |

#### 4.3 Divergence Resolution Policies

When `ACKNOWLEDGED_DIVERGENCE` exists for a term, the SAC declares one of four resolution policies:

| Policy | Meaning |
|---|---|
| `MORE_RESTRICTIVE` | The interpretation producing the more conservative governance outcome governs. Safe default. |
| `RUNTIME_A` | Runtime A's definition governs for this concept in cross-runtime operations |
| `RUNTIME_B` | Runtime B's definition governs for this concept in cross-runtime operations |
| `BILATERAL_OVERRIDE` | Both parties have agreed to a third definition (referenced by `override_str_entry_id`) that governs this concept — neither party's original definition is used |

**The `BILATERAL_OVERRIDE` mechanism** enables regulatory-neutral cross-jurisdiction governance: when EU and UAE frameworks define "revocation" differently, the parties can agree to a neutral definition that satisfies both regulatory regimes and sign it as a shared STR entry.

### 5. SGIP Formal Invariants

The following four invariants are formally defined by this ADR. They are PROPOSED for activation in the next OMNIX governance baseline revision.

#### SGIP-INV-001 — Semantic Term Immutability

An STR entry, once published with a valid ML-DSA-65 signature, has an immutable `content_hash`. A runtime MAY publish a new version of a term (new `str_entry_id`, incremented `term_version`, populated `supersedes` field), but the original entry's hash is permanently preserved and remains independently verifiable. Any SAC that referenced the original hash remains verifiable against the original definition indefinitely.

**Formal statement:** `∀ entry ∈ STR: hash(entry) is permanent from moment of first valid pqc_signature`

**Implementation:** Append-only STR storage. No UPDATE path on `str_entry_id`. Any modification attempt MUST be rejected with `STR_IMMUTABILITY_VIOLATION`.

#### SGIP-INV-002 — SAC Requires Complete Core Term Coverage

A Semantic Alignment Certificate MUST NOT be issued unless both parties have valid, signed STR entries for all eight ATF Core Term Set terms. An SAC referencing an incomplete SPV (any of the eight terms absent) is invalid and MUST be rejected at construction time.

**Formal statement:** `∀ SAC: |{t ∈ CoreTermSet : runtime_a.spv[t] ≠ null AND runtime_b.spv[t] ≠ null}| = 8`

**Implementation:** SAC construction validates both SPVs for completeness before computing `sac_content_hash`. Incomplete SPV → `SAC_INCOMPLETE_SPV` error, not a partial SAC.

#### SGIP-INV-003 — Unresolved Divergence Defaults to More Restrictive

For any cross-runtime governance operation touching a concept with `UNRESOLVED` status in the governing SAC, the system MUST apply the more restrictive interpretation of any available definition. If neither runtime has defined the term, the operation on that concept is BLOCKED unconditionally.

**Formal statement:** `∀ op touching term t: status(t) = UNRESOLVED → outcome = max_restrictive(available_definitions(t)) | BLOCKED`

**Implementation:** Cross-runtime admission gate checks SAC semantic_alignment_map before evaluating any operation. UNRESOLVED term → restrictive path, not pass-through.

#### SGIP-INV-004 — SAC Content Hash Covers Both SPVs

The `sac_content_hash` computation MUST include the complete `spv_hash` of both parties. Modification of either SPV after SAC issuance (e.g., a runtime publishing a new STR entry that supersedes a term referenced in the SAC) MUST not silently invalidate the SAC — the SAC continues to govern under the SPV hashes at the time of issuance. A verifier computing `sac_content_hash` from the original party SPVs MUST produce the identical hash.

**Formal statement:** `sac_content_hash = SHA256(canonical_JSON(parties, semantic_alignment_map)) where parties.runtime_x.spv_hash = spv_hash_at_issuance`

**Implementation:** SAC construction embeds `spv_hash` values at construction time. SPV updates do not mutate existing SACs. Verifier recomputes `sac_content_hash` from embedded values.

### 6. Compliance Designation: ATF-SGIP-Aligned

ADR-171 introduces a new compliance designation above ATF-GPI-Aligned (ADR-161):

```
ATF-RGC-Compliant (RFC-ATF-2)
  All 8 RGC invariants satisfied.
  Layers 1 + 2 interoperability.

ATF-GPI-Aligned (ADR-161)
  ATF-RGC-Compliant + valid CRGC.
  Layers 1 + 2 + 3 interoperability.

ATF-SGIP-Aligned (ADR-171 — this document)
  ATF-GPI-Aligned + valid SAC covering all 8 ATF Core Terms.
  Layers 1 + 2 + 3 + 4 interoperability.
  Full semantic transparency: every cross-runtime governance decision
  is traceable to declared, bilaterally signed concept definitions.
```

**ATF-SGIP-Aligned is the highest designation in the ATF compliance stack.** It is the only designation that provides a complete audit trail from cryptographic verification through protocol compliance through policy alignment through semantic declaration.

A governance decision made between two ATF-SGIP-Aligned runtimes can be examined forensically at every layer:
- Layer 1: Was the receipt signature valid? (ML-DSA-65 verification)
- Layer 2: Was the CES formula applied correctly? (Invariant audit)
- Layer 3: Were the policy parameters within agreed bounds? (CRGC audit)
- Layer 4: Did both parties share the same operational definition of the concept at issue? (SAC audit)

### 7. SGIP Pipeline Integration

The SGIP integrates with the existing ATF stack at two points:

#### 7.1 CRGC Extension (Layer 3 → Layer 4)

The existing CRGC schema (ADR-161 §4) is extended with an optional `sac_id` field:

```json
{
  "crgc_id": "CRGC-{16HEX}",
  "parties": [...],
  "policy_parameters": {...},
  "sac_id": "OMNIX-SAC-{16HEX} | null",
  "sgip_designation": "ATF-SGIP-Aligned | ATF-GPI-Aligned",
  "content_hash": "...",
  "pqc_signatures": [...]
}
```

When `sac_id` is present and valid, the CRGC carries Layer 4 alignment. The `sgip_designation` field makes the compliance level explicit and machine-verifiable.

#### 7.2 Cross-Runtime Admission Gate (GECR Layer — ADR-170)

The GECR Cross-Runtime Policy Router (CRPR, ADR-170 §1) is extended to check SAC semantic alignment before admitting cross-runtime operations:

```
Cross-runtime operation requested
        │
        ▼
[CRPR] Check: valid CRGC exists? — NO → BLOCK (existing ADR-170 behaviour)
        │ YES
        ▼
[CRPR-SGIP] Check: CRGC has valid SAC?
        │ NO → Admit at ATF-GPI-Aligned level (existing behaviour)
        │ YES
        ▼
[CRPR-SGIP] Check: operation touches term with UNRESOLVED status?
        │ YES → Apply SGIP-INV-003 (more restrictive | BLOCK)
        │ NO
        ▼
[CRPR-SGIP] Check: operation touches term with ACKNOWLEDGED_DIVERGENCE?
        │ YES → Apply declared divergence_resolution policy
        │ NO (all terms ALIGNED)
        ▼
Admit at ATF-SGIP-Aligned level
```

This integration is additive. Existing CRGC-only cross-runtime operations continue to be admitted at ATF-GPI-Aligned level with no behaviour change.

### 8. SAC as a Forensic Artifact

A Semantic Alignment Certificate is a first-class forensic artifact under the EAP/OEP pipeline (ADR-163/165). It is:

- **COLD-block eligible:** SACs are sealed into the evidence archive at the same tier as DRs and TARs
- **OEP-includable:** A forensic examiner requesting an OEP for a cross-runtime governance decision can request that the governing SAC be bundled in the package
- **Independently verifiable:** The SAC's `sac_content_hash` and `pqc_signatures` are verifiable offline with the standard CLI verifier (`omnix_atf_verify.py`) — no platform access required
- **Immutable by construction:** SGIP-INV-004 ensures that post-issuance SPV changes do not silently retroactively modify the SAC

**What a forensic examiner can determine from a SAC:** For any cross-runtime governance decision, the examiner can identify: (a) what each runtime understood each of the eight core governance concepts to mean at the time of the decision; (b) which concepts were aligned, which were acknowledged divergence, and which were unresolved; (c) which divergence resolution policy was applied; and (d) whether the decision's outcome would have been different had both runtimes used the more restrictive interpretation.

This makes the SGIP the only mechanism in the ATF stack that enables **semantic counterfactual auditing** — the ability to determine, after the fact, whether a different semantic posture would have produced a different governance decision.

---

## The Five-Layer Governance Assurance Stack

ADR-171 completes the OMNIX governance assurance architecture. The full stack for a cross-runtime governance operation is now:

```
Governance Question                    Layer    Mechanism           ADR
────────────────────────────────────────────────────────────────────────
Was the receipt tampered with?         L1       ML-DSA-65 sig       ADR-156/RFC-ATF-1
Was the CES formula applied right?     L2       Invariant audit     ADR-159/RFC-ATF-2
Were policy parameters within bounds?  L3       CRGC audit          ADR-161/RFC-ATF-3
Did both runtimes agree on meaning?    L4       SAC audit           ADR-171 (this)
Was the execution context controlled?  L5 (*)   GECR receipt chain  ADR-170
────────────────────────────────────────────────────────────────────────
(*) L5 = GECR orchestration layer; orthogonal to the interoperability stack
```

No other governance infrastructure in the industry addresses all four interoperability layers simultaneously in a production system. Layers 1 and 2 exist in various forms across PQC-capable systems. Layer 3 is novel to OMNIX (ADR-161). **Layer 4 is unique.** No other system provides a formally specified, cryptographically committed, independently verifiable mechanism for declaring operational semantic definitions and exposing their divergence surface across sovereign governance runtimes.

---

## Consequences

### Positive

- **Complete audit trail:** A forensic examiner can now trace any cross-runtime governance decision from cryptographic proof through protocol compliance through policy alignment through semantic declaration — four independent verification layers, all offline-verifiable.
- **Regulatory defensibility:** Regulators examining cross-jurisdiction governance decisions can verify not just that the protocol was followed but that both parties shared (or explicitly acknowledged diverging) definitions of the concepts the protocol governs.
- **Semantic counterfactual auditing:** Novel capability — enables examiners to determine post-hoc whether different semantic postures would have changed the governance outcome.
- **Priority record:** The Semantic Term Registry + Semantic Policy Vector + Semantic Alignment Certificate architecture is an original contribution. Deposited as part of the OMNIX ATF stack, May 2026.

### Neutral

- Existing ATF-RGC-Compliant and ATF-GPI-Aligned deployments are unchanged. SGIP is additive. No existing invariant is modified.
- SAC is optional for single-runtime deployments and for cross-runtime deployments that do not require Layer 4 designation.

### Negative

- Cross-runtime deployments seeking ATF-SGIP-Aligned designation must invest in authoring STR entries for all eight Core Terms. This is a deliberate governance investment — the cost is proportional to the complexity of the semantic environment being declared.

---

## Implementation Notes

- **STR storage:** Append-only table `atf_semantic_term_registry` — no UPDATE on existing rows. Schema: `(str_entry_id, runtime_id, term_id, term_version, definition_json, content_hash, pqc_signature, effective_from, supersedes_id, created_at)`
- **SPV generation:** On-demand computation from current STR state. Cached by `spv_hash` for use in SAC construction.
- **SAC storage:** Table `atf_semantic_alignment_certificates` — linked to `atf_delegations` table via `crgc_id`. Schema follows §4.1.
- **CRGC extension:** `sac_id` column added to existing `atf_delegations` table — nullable for backward compatibility.
- **Verifier extension:** `omnix_atf_verify.py` v1.2.0 will include SAC verification as an optional `--sac` flag.
- **OEP extension:** `oep_generator.py` to accept `include_sac=True` parameter for bundling SAC in forensic packages.
- **Python module:** `omnix_core/agents/atf/semantic_governance.py` — STR, SPV, SAC classes as PQC-signed dataclasses following the existing ATF pattern.

---

## Priority Record

The Semantic Governance Interoperability Protocol — comprising the Semantic Term Registry (STR), Semantic Policy Vector (SPV), Semantic Alignment Certificate (SAC), ATF Core Term Set, and ATF-SGIP-Aligned compliance designation — is an original protocol contribution by Harold Nunes, OMNIX QUANTUM LTD, Abu Dhabi UAE / London UK, May 2026.

This ADR constitutes the first formal specification of Layer 4 semantic interoperability for post-quantum governance infrastructure. The architecture is deposited as part of the OMNIX ATF ecosystem (Release 3.3) and subject to RFC publication as RFC-ATF-4.

**GOVERNANCE_BASELINE-2026-Q2-001 addendum:** 4 proposed invariants (SGIP-INV-001–004). Pending formal activation in next baseline revision.

---

## References

- ADR-161 — Governance Policy Interoperability Layer (GPIL)
- ADR-159 — Runtime Governance Continuity (RGC)
- ADR-170 — Governance Execution Context Router (GECR)
- ADR-163 — Evidence Archive Pipeline (EAP)
- ADR-165 — OMNIX Evidence Package (OEP)
- RFC-ATF-1 — DOI: 10.5281/zenodo.20155016
- RFC-ATF-2 — DOI: 10.5281/zenodo.20241344
- RFC-ATF-3 — DOI: 10.5281/zenodo.20247342
