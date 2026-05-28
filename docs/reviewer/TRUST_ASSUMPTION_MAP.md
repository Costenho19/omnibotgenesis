# TRUST ASSUMPTION MAP
## OMNIX-RTE-001 — What the Verifier Trusts and What It Does Not

**Role:** Protocol engineer + skeptical enterprise buyer  
**Package:** OMNIX-RTE-001 · Reviewer package `081409`  
**Date:** 2026-05-28

This document maps every trust assumption present in the OMNIX-RTE-001 verifier. Each assumption is a potential attack surface for a hostile reviewer.

---

## Trust Layer Architecture

```
LAYER 5: External root of trust
  └─ Assumed: embedded public key is authentic OMNIX key
  └─ Verified: NO — no external anchor, no PoGR key validation

LAYER 4: Cross-artifact session binding
  └─ Assumed: all artifacts in a path belong to the same governance session
  └─ Verified: PARTIALLY — OSG + MBR + outcome are path-labeled; DR is NOT

LAYER 3: Temporal validity
  └─ Assumed: artifacts were generated and used within their validity windows
  └─ Verified: NO — no TTL check, no expiry enforcement, no clock comparison

LAYER 2: Artifact content integrity
  └─ Assumed: hash-covered fields have not been altered
  └─ Verified: YES — SHA-256 / SHA3-256 per artifact type

LAYER 1: PQC signature integrity
  └─ Assumed: Dilithium-3 provides 128-bit quantum-resistant security
  └─ Verified: YES (with pip install pqc) — ML-DSA-65, FIPS 204
```

---

## Complete Trust Assumption Inventory

### TA-001: Embedded Public Key Is Authentic
**Status: UNVERIFIED — highest risk assumption**

The verifier loads the public key from `pqc.public_key_b64` in the package itself. It verifies all signatures against this key. There is no external validation that this key belongs to OMNIX QUANTUM LTD.

**Attack:** Generate a new Dilithium-3 keypair, re-sign all artifacts, replace embedded key → 101/101 PASS with attacker identity.

**Mitigation:** Published OMNIX root key fingerprint (future PoGR integration, ADR-186). Until then: reviewers must obtain the OMNIX public key via an out-of-band channel.

---

### TA-002: Hash-Covered Fields Are Semantically Complete
**Status: PARTIALLY VERIFIED**

The verifier's canonicalization excludes signature fields and hash fields themselves (correct). It includes all other fields in the canonical payload. However:

- `scenario` section: NOT covered by any artifact hash
- `rte_chain_map`: NOT covered by any artifact hash
- `invariants_demonstrated`: NOT covered
- `verification_instructions`: NOT covered
- `paths[*].label`, `paths[*].rte_verdict`: NOT covered
- CFR content (description, outcome_summary, fragility_score): NOT individually hashed

**A reviewer reading uncovered fields cannot treat them as verified.**

---

### TA-003: Both Paths Belong to the Same Governance Session
**Status: NOT VERIFIED**

The package contains two governance sessions (`path_dangerous` and `path_admissible`) with different session IDs:

```
path_dangerous session_id:  SESSION-7E0549F26BA04DF4
path_admissible session_id: SESSION-B3AB40581EBF487D
```

The verifier never checks that artifacts within a path share a consistent session ID, nor does it check that the two paths are related (e.g., that the admissible path is a re-certification of the dangerous path agent).

**Attack (A09):** Replace admissible DR with dangerous DR → 101/101 PASS.

---

### TA-004: DR Belongs to the Path It Authenticates
**Status: NOT VERIFIED**

The verifier checks that a DR is internally consistent (content_hash, PQC sig). It does NOT check:
- `DR.session_id` = `path.1_source_state.session_id`
- `DR.dr_id` is referenced by `MBR.dr_id` or any other artifact in the path
- The DR's agent matches the path's agent

**Attack (A09):** A DR from any governance session, with any authority level, passes if internally consistent.

---

### TA-005: MBR Binds to a Specific DR
**Status: NOT VERIFIED**

The MBR (Mandate Binding Record) should bind the mandate to a specific delegation receipt. The verifier checks MBR integrity and PQC signature, but does not verify that `MBR.dr_id` (if present) matches the DR in the same path.

**Impact:** An MBR with a valid mandate can be combined with a DR representing a different authority context.

---

### TA-006: Temporal Validity of Authority
**Status: NOT VERIFIED**

The verifier performs no clock-aware checks. Fields present in artifacts:
- `DR.expires_at` — present, hash-covered, but never compared to now
- `MBR.issued_at` — present, hash-covered, never compared to now
- `TAR.admission_status` — checked semantically (ADMITTED/REJECTED), not temporally

**Impact:** A package with authority that expired two years ago verifies identically to a package with current authority. For a $50M settlement, this matters.

---

### TA-007: CFR Content Reflects the Governance Engine's Actual Analysis
**Status: NOT VERIFIED**

The CAT (Counterfactual Attestation Token) commits to the list of CFR IDs via `cfr_root_hash`. Individual CFR content (description, outcome_summary, fragility_score, selected_path narrative) is not committed.

**Attack (A08):** Rewrite all CFR descriptions and fragility scores → 17/17 PASS (verify-counterfactual).

**Impact:** The counterfactual record — the primary audit artifact establishing that the governance engine evaluated alternatives — is mutable. An attacker can change what alternatives were supposedly considered.

---

### TA-008: The CTCHC Covers the Actual Agent Outputs
**Status: PARTIALLY VERIFIED**

The CTCHC (Cross-Turn Coherence Hash Chain) verifies:
- Link chain continuity (prev_link_hash progression)
- Genesis hash reference
- Seal hash covers the complete link list

It does NOT verify that `turn_hash` values within each link correspond to actual model outputs. `turn_hash` is present in the links but its source data (the actual agent output that was hashed) is not included in the package.

**Impact:** The chain integrity is verified, but the chain's content anchoring to actual agent behavior requires trust that `turn_hash` was honestly computed.

---

### TA-009: Settlement Amount Is Consistent Across All Artifacts
**Status: PARTIALLY VERIFIED**

`SETTLE-AMOUNT` check verifies that `settlement_reference.amount_usd == 50,000,000`. However:
- `scenario.amount_usd` is NOT hash-covered (A01 bypass)
- The settlement amount in `outcome_receipt.settlement_reference.amount_usd` IS verified
- No check that `DR.budget_granted` (authority budget) is semantically related to the settlement amount

**A hostile reviewer notes:** The authority budget (42% or 88% of mandate) is not directly tied to the dollar amount of the settlement in the verifier logic.

---

### TA-010: The Verifier Covers All Meaningful Artifacts
**Status: PARTIALLY VERIFIED**

Artifacts verified: DR, MBR, MAS, RCR, MBR Seal, CAT, OSG VR, BAR, CTCHC, PoGC, TCS, Refusal receipt, Outcome receipt, Replay proof.

Artifacts present in the package but NOT individually verified:
- `1_source_state` fields (including `source_state_hash` — not checked)
- `5_verdict` (TAR in dangerous path — structure not fully verified, only `admission_status`)
- `3_runtime.continuity_record.binding_record` and `commit_record` (admissible path) — present but not individually hash-checked
- CCS (Constraint Conformance Signal) — referenced in docs, not individually verified
- Individual CFR records (only CAT is verified)

---

### TA-011: Package Version and Schema Are Authentic
**Status: NOT VERIFIED**

`package_version`, `omnix_version`, `adr_reference` are top-level metadata fields. The verifier does not check these against any canonical schema version. An attacker can claim any version.

---

## Trust Surface Summary

| Trust Assumption | Verified | Attack Surface |
|---|---|---|
| TA-001: Embedded PQC key is authentic | ✗ NO | Complete re-sign with attacker key |
| TA-002: Hash coverage is semantically complete | Partial | scenario, rte_chain_map, CFR content |
| TA-003: Both paths belong to same session | ✗ NO | Cross-session path injection |
| TA-004: DR belongs to its path | ✗ NO | Cross-path DR injection (A09 BYPASS) |
| TA-005: MBR binds to its DR | ✗ NO | Cross-artifact authority mismatch |
| TA-006: Authority is temporally valid | ✗ NO | Expired authority replay |
| TA-007: CFR content reflects actual analysis | ✗ NO | CFR narrative rewrite (A08 BYPASS) |
| TA-008: CTCHC covers actual agent outputs | Partial | turn_hash source not verifiable |
| TA-009: Settlement amount is consistent | Partial | scenario amount mutable |
| TA-010: All meaningful artifacts are verified | Partial | source_state, TAR, CCS not verified |
| TA-011: Package version is authentic | ✗ NO | Version spoofing |

---

## Minimum Viable Trust Extension

For institutional use, three additions would close the critical gaps:

1. **Cross-artifact session binding** — `verify DR.session_id == path.session_id` (one line)
2. **CFR content commitment** — include SHA3-256(CFR canonical fields) in CAT root hash
3. **External key anchor** — publish OMNIX root key fingerprint; verifier validates embedded key against it

These three changes would raise the trust posture from "cryptographic integrity of isolated artifacts" to "cryptographic integrity of a coherent governance session."

---

*Trust Assumption Map — OMNIX-RTE-001 · OMNIX QUANTUM LTD · 2026-05-28*
