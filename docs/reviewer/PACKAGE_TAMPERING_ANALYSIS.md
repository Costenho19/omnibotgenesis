# PACKAGE TAMPERING ANALYSIS
## OMNIX-RTE-001 — What an Attacker Can and Cannot Mutate

**Role:** Institutional auditor + regulator  
**Package:** OMNIX-RTE-001 · Reviewer package `081409`  
**Date:** 2026-05-28

This document classifies every section of the evidence package by tamperability — what an attacker can change without detection, and what they cannot.

---

## Tamperability Classification

```
CLASS A — IMMUTABLE:   Change detected by hash check + PQC signature
CLASS B — HASH-ONLY:   Change detected by hash check; PQC skip hides it if pqc not installed
CLASS C — MUTABLE:     Change NOT detected by verifier (structural or semantic gap)
CLASS D — OBSERVABLE:  Change visible in output but verifier does not fail on it
```

---

## Top-Level Package Fields

| Field | Class | Attack | Verifier Response |
|---|---|---|---|
| `package_id` | C | Mutate to any string | PASS (not hash-covered) |
| `package_type` | D | Mutate to non-OMNIX-RTE-001 | Fails `PKG-TYPE` structural check |
| `package_version` | C | Mutate to "0.0.1" | PASS |
| `omnix_version` | C | Mutate | PASS |
| `adr_reference` | C | Mutate | PASS |
| `generated_at` | C | Mutate to any timestamp | PASS |
| `generated_by` | C | Mutate to attacker identity | PASS |
| `pqc.public_key_b64` | A* | Mutate to random bytes → 26 FAIL; re-sign all → 101 PASS | Detected for wrong key; undetected for attacker key |
| `pqc.algorithm` | C | Mutate to "RSA-2048" | PASS (decorative) |
| `invariants_demonstrated` | C | Mutate / add / remove invariants | PASS |
| `verification_instructions` | C | Replace with attacker instructions | PASS |
| `rte_chain_map.[*]` | C | Rewrite all chain descriptions | PASS (**A03 confirmed**) |
| `scenario.amount_usd` | C | 50,000,000 → 99,999,999 | PASS (**A01 confirmed**) |
| `scenario.description` | C | Rewrite narrative | PASS |
| `scenario.regulatory_context` | C | Replace jurisdictions | PASS |
| Root-level injected fields | C | Add `_attacker_note`, `regulatory_clearance` | PASS (confirmed) |

*`pqc.public_key_b64`: CLASS A for random mutation; CLASS C for complete re-sign.

---

## Path Labels and Summaries

| Field | Class | Notes |
|---|---|---|
| `paths.path_dangerous.path` | D | "DANGEROUS" → semantic checks use path label |
| `paths.path_dangerous.label` | C | Prose label — mutable |
| `paths.path_dangerous.rte_verdict` | C | Verdict string — mutable |
| `paths.path_dangerous.summary.*` | C | All summary fields mutable |
| `paths.path_admissible.path` | D | "ADMISSIBLE" → semantic checks use this |
| `paths.path_admissible.label` | C | Mutable |
| `paths.path_admissible.summary.*` | C | All mutable including `mandate_certification` in summary |

**Note:** Swapping `paths.path_dangerous` ↔ `paths.path_admissible` content entirely → **38 FAILED** — the OSG verdict semantic checks catch this (A-probe confirmed).

---

## Step 1 — Source State

| Field | Class | Notes |
|---|---|---|
| `session_id` | C | Not hash-verified; not cross-checked with DR |
| `request_id` | C | Mutable |
| `actor` | C | Mutable — no binding to DR agent_id |
| `treasury_context.*` | C | FX rates, counterparty, all mutable |
| `policy_constraints.*` | C | Governance policy — mutable |
| `source_state_hash` | C | Present but never verified |
| `temporal_context_snapshot` | A | Verified via `_check_tcs()` |

---

## Step 2 — Authority (DR + MBR)

| Field | Class | Notes |
|---|---|---|
| `DR.budget_granted` | A | Hash + PQC (A02 DETECTED) |
| `DR.ces_band_at_grant` | A | Hash-covered |
| `DR.expires_at` | A | Hash-covered (A06 DETECTED) |
| `DR.content_hash` | A | PQC-signed; changing it invalidates sig |
| `DR.pqc_signature` | A | Dilithium-3 sig — quantum-resistant |
| `DR.session_id` | A* | Hash-covered; BUT verifier doesn't check it against path | 
| `MBR.mandate_amount` | A | Hash-covered (A15 test: recompute hash → sig fails) |
| `MBR.mandate_ref` | A | Hash-covered |
| `MBR.issued_at` | A | Hash-covered (A12 normalization: +00:00→Z DETECTED) |
| `MBR.mbr_content_hash` | A | PQC-signed |
| Entire DR (cross-path) | C | Dangerous DR → admissible position: PASS (**A09 BYPASS**) |

*DR.session_id: immutable in isolation; exploitable via cross-path injection.

---

## Step 3 — Runtime (RCR + MAS)

| Field | Class | Notes |
|---|---|---|
| `RCR.ces_score` | A | Hash-covered + formula verified by verifier |
| `RCR.ces_components.*` | A | Hash-covered; CES formula recomputed by verifier |
| `RCR.ces_band` | A | Hash-covered |
| `RCR.rcr_hash` | A | PQC-signed |
| `MAS.mas_score` | A | Hash-covered |
| `MAS.proxy_guard_violated` | A | Hash-covered |
| `MAS.pqc_signature` | A | Dilithium-3 |

**Note:** The CES formula weights (0.30, 0.30, 0.20, 0.20) are hardcoded in the verifier, not read from the package. An attacker cannot change the weights.

---

## Step 4 — Counterfactual (CFR + CAT)

| Field | Class | Notes |
|---|---|---|
| `CFR[*].cfr_id` | A | CAT root_hash covers cfr_id list |
| `CFR[*].description` | **C** | Not individually hashed (**A08 BYPASS**) |
| `CFR[*].outcome_summary` | **C** | Not individually hashed (**A08 BYPASS**) |
| `CFR[*].fragility_score` | C* | In [0,1] → range check passes; value mutable |
| `CFR[*].selected_path` | D | Verifier checks exactly one selected=True |
| `CFR[*].counterfactual_action` | **C** | Not individually hashed |
| `CAT.cfr_root_hash` | A | Verified against SHA3(cfr_id_list) |
| `CAT.cfr_count` | D | Checked: count ≥ 3 |
| `CAT.cat_content_hash` | A | Hash + PQC |
| `CAT.pqc_signature` | A | Dilithium-3 |

*fragility_score: value is mutable within [0.0, 1.0]; out-of-range is detected.

**CRITICAL SURFACE:** CFR description, outcome_summary, and narrative fields (everything except cfr_id) are completely mutable without detection.

---

## Step 5 — Verdict

| Field | Class | Notes |
|---|---|---|
| Dangerous path TAR.admission_status | D* | Only checked via OSG verdict indirectly |
| Dangerous path TAR.content_hash | **C** | Present but not verified |
| Dangerous path TAR.pqc_signature | **C** | Present but not verified |
| Admissible path TAR.admission_status | A | Verified: must = ADMITTED |
| Admissible path TAR.content_hash | A | Hash + PQC |
| Admissible path binding_record | **C** | Present but not individually verified |
| Admissible path commit_record | **C** | Present but not individually verified |

---

## Step 6 — Gate (OSG + PoGC + MBR Seal)

| Field | Class | Notes |
|---|---|---|
| `OSG_VR.verdict` | A | Hash + semantic check (REJECTED/APPROVED) |
| `OSG_VR.fail_closed` | A | Hash-covered; checked = True |
| `OSG_VR.vr_content_hash` | A | PQC-signed |
| `PoGC.mandate_certification` | A | Hash-covered; checked = MANDATE-BOUND |
| `PoGC.amount_usd` | A | Hash-covered (PoGC hash includes all non-sig fields) |
| `PoGC.content_hash` | A | PQC-signed |
| `MBR_Seal.certification_tier` | A | Hash-covered; semantic check (A05 DETECTED) |
| `MBR_Seal.seal_content_hash` | A | PQC-signed |

**Step 6 is the most strongly protected section.** All settlement-critical fields are hash-covered and PQC-signed.

---

## Step 7 — Execution (BAR + CTCHC + Settlement)

| Field | Class | Notes |
|---|---|---|
| `BAR.session_id` | A | In 6-field canonical hash |
| `BAR.output_hash` | A | In 6-field canonical hash |
| `BAR.governing_receipt_id` | A | In 6-field canonical hash |
| `BAR.pqc_signature` | A | 4-field default-sep sig |
| `CTCHC.links[*].turn_hash` | A | In link hash chain computation |
| `CTCHC.links[*].chain_link_hash` | A | Chain continuity checked |
| `CTCHC.sealed.seal_hash` | A | Covers full chain (BEV-INV-013) |
| `CTCHC.sealed.seal_pqc_signature` | A | Dilithium-3 |
| `settlement_reference.amount_usd` | D | Checked by value: = 50,000,000; not PQC-signed independently |
| `settlement_reference.swift_ref` | D | Checked by presence; not PQC-signed |
| `settlement_reference.xrpl_tx_id` | D | Checked by presence; not PQC-signed |
| `outcome_receipt.*` | A | Hash + PQC; includes settlement_reference |

**Note on settlement_reference:** The settlement_reference fields are checked for presence and value (SETTLE-AMOUNT = 50,000,000, SETTLE-SWIFT presence, SETTLE-XRPL presence). They are included in the `outcome_receipt` canonical hash, which IS PQC-signed. An attacker cannot change settlement_reference without breaking the outcome_receipt hash.

---

## Step 8 — Post-Execution (TCS + Replay)

| Field | Class | Notes |
|---|---|---|
| `TCS.regulatory_context` | A | Hash-covered; presence checked |
| `TCS.tcs_hash` | A | PQC-signed |
| `replay_proof.terminal_status` | A | Hash-covered; checked: HALTED/CLOSED |
| `replay_proof.offline_verifiable` | A | Hash-covered; checked = True |
| `replay_proof.proof_content_hash` | A | PQC-signed |

---

## Tampering Resistance Summary by Section

| Section | Overall Resistance | Critical Gaps |
|---|---|---|
| Package metadata | **LOW** | All top-level fields mutable |
| Source state (step 1) | **LOW** | No hash verification |
| Authority (step 2) | HIGH | Cross-path injection bypass |
| Runtime (step 3) | HIGH | None identified |
| Counterfactual (step 4) | **MEDIUM** | CFR content mutable |
| Verdict (step 5) | MEDIUM | Dangerous TAR unverified |
| Gate (step 6) | **HIGH** | Strongest section |
| Execution (step 7) | HIGH | settlement_reference class D (presence only) |
| Post-execution (step 8) | HIGH | None identified |

---

## Most Valuable Artifacts for an Attacker

A sophisticated adversary would prioritize:

1. **`scenario.amount_usd`** — mutable without detection; creates false impression of verified amount
2. **CFR descriptions** — mutable; rewrites the counterfactual governance narrative
3. **`rte_chain_map`** — mutable; rewrites the chain execution narrative
4. **Path-level DR injection** — genuine authority bypass (A09)
5. **`paths[*].summary`** — mutable; summary is the first thing a reviewer reads

**An attacker presenting this package to a non-technical audience would focus on the mutable fields** because they are the human-readable parts that create the governance narrative.

---

## Defense-in-Depth Assessment

The package has strong cryptographic integrity at the artifact level (Layer 2) but weak cross-artifact binding (Layer 4). The gap between individual artifact integrity and session-level coherence is where the critical bypass (A09) lives.

The analogy: each document in a contract is individually notarized. But the notary doesn't verify that all documents belong to the same contract — allowing an attacker to swap one notarized document for another from a different context.

---

*Package Tampering Analysis — OMNIX-RTE-001 · OMNIX QUANTUM LTD · 2026-05-28*
