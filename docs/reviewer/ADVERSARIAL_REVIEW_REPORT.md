# ADVERSARIAL REVIEW REPORT
## OMNIX-RTE-001 — Hostile Reviewer Simulation

**Role:** Hostile cryptography reviewer + institutional auditor + regulator + protocol engineer  
**Package:** `OMNIX-RTE-001-REVIEWER_20260528_081409.zip`  
**Evidence:** `OMNIX-RTE-001_20260528_071811.json`  
**Verifier:** `verify.py` (standalone, stdlib + optional `pip install pqc`)  
**Date:** 2026-05-28  
**Optimization target:** Finding what a hostile reviewer attacks first. NOT optimizing for PASS.

---

## Executive Summary

**15 adversarial attacks executed. 11 DETECTED. 4 BYPASS. 2 CRITICAL.**

The verifier correctly enforces cryptographic integrity for all hash-covered, PQC-signed artifacts. However, two structural gaps allow adversarial mutation without detection:

| Severity | Finding | Attack |
|---|---|---|
| **CRITICAL** | Cross-path DR injection — dangerous authority passes as admissible | A09 |
| **HIGH** | CFR content mutation undetected — counterfactual narrative is mutable | A08 |
| **HIGH** | No TTL enforcement — expired authority is indistinguishable from valid | A07 |
| **MEDIUM** | Package metadata not hash-covered — scenario amount, chain map narrative | A01, A03 |
| **INFORMATIONAL** | No external root of trust for embedded PQC public key | A10-variant |

---

## Attack Results — Full Matrix

| # | Attack | Result | Severity |
|---|---|---|---|
| A01 | Mutate `scenario.amount_usd` to 99,999,999 | **BYPASS** | MEDIUM |
| A02 | Mutate DR `budget_granted` (hash-covered) | DETECTED | — |
| A03 | Mutate `rte_chain_map` narrative | **BYPASS** | MEDIUM |
| A04 | Remove all CTCHC chain links | DETECTED | — |
| A05 | Swap MBR seal tier UNCERTIFIED→MANDATE-BOUND | DETECTED | — |
| A06 | Set DR `expires_at` to 2019 (hash-covered) | DETECTED | — |
| A07 | TTL enforcement — no semantic expiry check | **BYPASS** | HIGH |
| A08 | Mutate CFR content, preserve cfr_ids | **BYPASS** | HIGH |
| A09 | Cross-path DR injection (dangerous→admissible) | **BYPASS** | CRITICAL |
| A10 | Replace embedded public key with random bytes | DETECTED | — |
| A11 | Delete `replay_proof` from dangerous path | DETECTED | — |
| A12 | Timestamp normalization `+00:00`→`Z` | DETECTED | — |
| A13 | CLI unknown flag `--verify-foo` | DETECTED (exit=2) | — |
| A14 | Missing evidence file | DETECTED (exit=2) | — |
| A15 | Forge MBR: recompute hash + preserve original sig | DETECTED | — |

---

## Finding F-ADV-001 — CRITICAL: Cross-Path DR Injection (A09)

**Attack:** Replace the admissible path Delegation Receipt with the dangerous path DR. Run full verification.

**Result:** `101 / 101 PASS` — complete bypass.

**Root cause:** The verifier checks DR `content_hash` integrity in isolation:

```python
expected = _hash_compact(dr, exclude=["content_hash", "pqc_signature", "pqc_algorithm"])
actual   = dr.get("content_hash", "")
hash_ok  = expected == actual
```

It verifies that the DR is internally consistent and PQC-signed. It does NOT verify that:
- `DR.session_id` matches the path's `session_id` in `1_source_state`
- `DR.dr_id` is referenced by any other artifact in the same path
- The DR's authority budget is the one used in the MBR or MAS computations

**Impact:** An adversary can inject a DR representing degraded authority (CRITICAL CES band, low budget) into the admissible path position. The verifier shows 101/101 PASS. A reviewer relying solely on the verifier cannot detect this.

**Note:** The dangerous and admissible paths in this package use different `session_id` values (`SESSION-7E0549F26BA04DF4` vs `SESSION-B3AB40581EBF487D`). The verifier never cross-checks them.

**Remediation:** Add cross-artifact session binding: verify that `DR.session_id` equals the path's `1_source_state.session_id`. Add `dr_id` to the MBR canonical fields so the MBR binds to a specific DR.

---

## Finding F-ADV-002 — HIGH: CFR Content Unverified (A08)

**Attack:** Mutate all CFR `description`, `outcome_summary`, and `fragility_score` fields (within [0.0, 1.0] range) in the admissible path. Preserve all `cfr_id` values.

**Result:** `17 / 17 PASS` (verify-counterfactual) — complete bypass.

**Root cause:** The Counterfactual Attestation Token (CAT) binds only to the list of CFR IDs:

```python
expected_root = _sha3(json.dumps([c["cfr_id"] for c in cfrs], sort_keys=True))
```

Individual CFR content (description, fragility score, outcome summary, selected path narrative) is not included in any hash. The CAT's `cfr_root_hash` is a commitment to existence, not to content.

**Impact:** An adversary can rewrite the counterfactual narrative — what alternatives were considered, what fragility was assessed, what the governance engine rejected — without detection. For a $50M settlement, the counterfactual record is the primary audit artifact establishing that alternatives were evaluated.

**Remediation:** Include `SHA3-256(canonical_CFR_content)` per CFR in the CAT root hash. Or add individual `cfr_content_hash` fields with verification.

---

## Finding F-ADV-003 — HIGH: No TTL Enforcement (A07)

**Attack:** No field mutation needed. Observe that the verifier has zero time-aware checks.

**Evidence:** The `expires_at` field on the DR is covered by the content hash (mutating it is detected — A06). However, the verifier never reads the system clock and never compares any `issued_at`, `expires_at`, or `valid_until` field against the current time.

**Impact:** A package generated with authority that expired in 2024 presents identically to a package with current authority. A reviewer verifying the package in 2030 cannot determine whether the DR was within its validity window at execution time.

**Institutional relevance:** Regulatory frameworks (EU AI Act Article 17, DORA Article 16) require that governance records establish temporal validity, not merely temporal presence.

**Remediation:** The verifier should warn (not fail) when any `issued_at` field is outside a configurable window, or document explicitly that temporal validity is out of scope and must be confirmed by the reviewer against the package `generated_at` timestamp.

---

## Finding F-ADV-004 — MEDIUM: Package Metadata Not Hash-Covered (A01, A03)

**Attack A01:** Change `scenario.amount_usd` from 50,000,000 to 99,999,999.  
**Attack A03:** Replace `rte_chain_map` narrative with attacker text.

**Result:** Both: `101 / 101 PASS`.

**Root cause:** The `scenario` section and `rte_chain_map` are top-level package fields not included in any artifact's canonical hash. They are human-readable descriptions, not cryptographic commitments.

**Impact — A01:** A reviewer reading the package sees $50M in the scenario and $50M confirmed by SETTLE-AMOUNT. But between those two layers, the scenario amount is mutable. A sophisticated attacker could create a package where the scenario describes a different amount than the one actually settled.

**Impact — A03:** The `rte_chain_map` summarizes the 8-step governance chain in prose. An attacker can replace all chain descriptions with misleading text. The verifier confirms the chain; the chain descriptions are decorative.

**Remediation:** Include `scenario` hash in the source state artifact. Sign `rte_chain_map` or remove it from the trusted surface.

---

## Finding F-ADV-005 — INFORMATIONAL: No External Root of Trust for Embedded PQC Key

**Attack A10:** Replace `pqc.public_key_b64` with random bytes → 26 FAILED (detected).  
**Undetectable variant:** Generate new Dilithium-3 keypair, re-sign ALL artifacts with the new private key, replace `pqc.public_key_b64` with the new public key → **101/101 PASS**.

**Root cause:** The embedded public key is self-referential. The verifier uses the key from the package to verify signatures in the same package. There is no:
- Certificate Authority
- Key pinning against an external registry
- Cross-reference to the OMNIX public key published at a canonical URL
- Timestamp-of-issue in the key record

**Impact:** An adversary who can regenerate all 101 artifacts (requires the Dilithium-3 private key equivalent — significant capability) produces a package that verifies completely with a different identity. The reviewer cannot distinguish a legitimate OMNIX-signed package from an attacker-signed one without an external trust anchor.

**Note:** This is an architectural property, not a bug. The PoGR (Proof of Governance Registry) is the designed external anchor (ADR-186). The limitation is that the verifier does not validate the key against the PoGR.

**Remediation:** Embed the OMNIX root public key fingerprint in the verifier. Or validate the embedded key against a canonical OMNIX PoGR endpoint (with offline fallback hash).

---

## What the Verifier Gets Right

The following attack surfaces are closed:

- **Hash integrity:** Any mutation to a hash-covered field is detected (A02, A05, A06, A12, A15)
- **Chain continuity:** Removing or reordering CTCHC links is detected (A04)
- **Semantic verdict enforcement:** OSG verdict, MBR seal tier, and path outcome checks are cross-validated (A05, full path swap → 38 FAILED)
- **PQC sig binding:** Altered hash + preserved sig is detected (A15) — the two-layer hash+sig architecture works
- **CLI hardening:** Unknown flags handled gracefully (A13, exit=2)
- **Missing artifact handling:** Deleted `replay_proof` fails gracefully, not crash (A11)
- **Missing file handling:** Non-existent package exits 2 with informative message (A14)
- **Timestamp canonicalization:** Format differences (`+00:00` vs `Z`) are detected (A12)

---

## Priority Remediation Order

1. **[CRITICAL] F-ADV-001** — Cross-path DR session binding (one line: compare `DR.session_id` to path session)
2. **[HIGH] F-ADV-002** — CFR content hashing (per-CFR content commitment in CAT root)
3. **[HIGH] F-ADV-003** — TTL documentation (explicit scope note or clock-aware warning)
4. **[MEDIUM] F-ADV-004** — Scenario hash (include scenario in source_state_hash)
5. **[INFORMATIONAL] F-ADV-005** — External key root (PoGR key fingerprint validation)

---

*Generated by adversarial simulation — OMNIX QUANTUM LTD · 2026-05-28*
