# REPLAY ATTACK ANALYSIS
## OMNIX-RTE-001 — Replay, Reuse, and Temporal Integrity

**Role:** Hostile cryptography reviewer  
**Package:** OMNIX-RTE-001 · Reviewer package `081409`  
**Date:** 2026-05-28

This document analyzes every form of replay attack possible against the OMNIX-RTE-001 evidence package.

---

## Replay Taxonomy

```
TYPE 1 — Intra-package replay:    reuse an artifact from one path in another path
TYPE 2 — Cross-package replay:    present a legitimate past package as a new one
TYPE 3 — Stale authority replay:  reuse expired delegation in a new context
TYPE 4 — Cross-keypair replay:    present package signed under a different key
TYPE 5 — Partial replay:          inject one authentic artifact into a tampered package
TYPE 6 — Counterfactual replay:   present the dangerous path as the admissible path
```

---

## Type 1 — Intra-Package Replay

### 1a. Cross-Path DR Injection (CONFIRMED BYPASS — A09)

**Executed:** Replace admissible path DR with dangerous path DR.  
**Result:** `101 / 101 PASS`

**Why it works:**
The DR's `content_hash` and PQC signature are self-consistent regardless of which path they appear in. The verifier has no binding check between:
- `DR.session_id` and `path.1_source_state.session_id`
- `DR.dr_id` and `MBR.dr_id` (if field exists)

The dangerous path DR represents authority at CES=42.05 (CRITICAL band). When injected into the admissible path, the package presents:
- A CRITICAL-band authority as ADMITTED
- A MANDATE-BOUND PoGC (from the legitimate admissible path)
- A $50M settlement as APPROVED

The settlement appears valid. The authority was not.

### 1b. Cross-Path MBR Seal Injection

**Tested:** Not independently executed, but follows the same logic.  
**Hypothesis:** An UNCERTIFIED MBR seal injected into admissible path step 6 would be caught because `_check_mbr_seal()` checks `certification_tier == "MANDATE-BOUND"` for ADMISSIBLE path (A05 DETECTED). However, combined with DR injection above, an attacker could present a full admissible path composed of dangerous artifacts where the seal tier check passes independently.

### 1c. CTCHC Genesis Manipulation

**What CTCHC verifies:**
- `first_link.prev_link_hash == genesis_hash` (BEV-INV-010)
- Link chain continuity (BEV-INV-011)
- Seal hash covers complete chain (BEV-INV-013)

**What it does NOT verify:**
- Whether `genesis_hash` was generated from the correct session state
- Whether `chain_id` is unique across executions
- Whether `session_id` in the CTCHC seal matches the path's session

**Replay scenario:** Take a CTCHC from a legitimate past session. Inject into a new package. If `chain_id` and `session_id` are not cross-checked against the path's session, this passes.

---

## Type 2 — Cross-Package Replay (Stale Package Presentation)

**Scenario:** The same OMNIX-RTE-001 package, generated on 2026-05-28, is presented to a reviewer in 2028 as evidence of current governance capability.

**Verifier response:** `101 / 101 PASS`

**Why:** The verifier performs zero time-aware checks. All `issued_at` fields are verified as part of hash integrity but never compared to the current timestamp. A package generated two years ago is cryptographically indistinguishable from one generated today.

**What a hostile regulator asks:**
> "This package was generated in May 2026. The EU AI Act enforcement date was August 2026. Does this package demonstrate that your governance system was operational at the time of the regulated action, or merely that it was operational at some prior demonstration date?"

**Verifier answer:** Silence. The package has no "freshness" guarantee beyond `generated_at` being a field in the JSON that the verifier reads but does not validate against the current clock.

**Mitigation:** The package is time-anchored by the `PoGC.issued_at` and `generated_at` fields. A reviewer must manually compare these against the claimed transaction date. The verifier should document this explicitly as an out-of-scope check or add a `--after-date` flag.

---

## Type 3 — Stale Authority Replay

**Scenario:** A Delegation Receipt with `expires_at: 2026-01-01` is used in a package presented in 2026-12-01.

**Executed (A06):** Mutating `expires_at` to 2019 was detected — because `expires_at` is a hash-covered field and changing it breaks the hash.

**The subtle replay attack:** Use a legitimately generated package where the DR was within its validity window at generation time. Present the package after the DR has expired. The hash and signature still verify. The DR's authority has expired in real-world terms. The verifier returns PASS.

**Verifier response:** `101 / 101 PASS` — because the hash of `expires_at=2026-05-28T11:18:02` is correct for the value that was there at generation time.

**Impact:** A reviewer cannot determine from the verifier output alone whether the authority was valid at the time of use. The temporal gap between DR issuance and package verification is invisible to the verifier.

---

## Type 4 — Cross-Keypair Replay (Complete Package Re-Sign)

**Executed (A10, partial):** Replace `pqc.public_key_b64` with random bytes → 26 FAILED.

**The undetectable variant:**
1. Obtain or synthesize all package artifacts (requires knowing the canonical format)
2. Generate a new Dilithium-3 keypair (attacker-controlled)
3. Sign all 26 PQC-covered artifacts with the attacker's private key
4. Embed the attacker's public key as `pqc.public_key_b64`
5. Run verifier → `101 / 101 PASS`

**Required capability:** Knowledge of the RTE-001 canonicalization profile (published in ADR-200 §4 and in the verifier's docstring — it is public). Ability to generate Dilithium-3 signatures (requires `pip install pqc` or equivalent). Knowledge of what values to put in each field to pass semantic checks (OSG verdict, MBR tier, execution flags — all documented).

**This is not a theoretical attack for a sophisticated adversary.** The canonicalization profile is public. The verifier is open source. The semantic check values are enumerated in the verifier source.

**The only protection against this attack is external key anchoring** — a mechanism outside the package that confirms the embedded public key is authentic OMNIX identity.

---

## Type 5 — Partial Replay (Authentic Artifact Injection)

**Scenario:** An attacker takes one legitimate PQC-signed artifact from a real OMNIX governance session and injects it into a fabricated package.

**Example:** Take a real PoGC (`POGC-F1DC0218E5204875`) from a legitimate $1M settlement. Inject it into a package claiming $50M.

**Verifier response:**
- `POGC-HASH`: PASS (PoGC is internally consistent)
- `POGC-SIG`: PASS (legitimate OMNIX signature)
- `POGC-BOUND`: PASS (mandate_certification=MANDATE-BOUND)
- `SETTLE-AMOUNT`: DEPENDS on whether `settlement_reference.amount_usd` is also forged

**Why this is partially effective:** The PoGC signature is over `{pogc_id, content_hash, issued_at}`. The verifier does not check that `PoGC.amount_usd` matches `settlement_reference.amount_usd`. A real PoGC from a $1M settlement + a forged settlement_reference claiming $50M might pass all checks if `settlement_reference` is not individually PQC-signed with a field binding the PoGC.

**Verification:** `settlement_reference` has no individual hash check in the verifier. `SETTLE-AMOUNT` reads directly from `settlement_reference.amount_usd`. This amount is NOT covered by the PoGC's `content_hash` (which only hashes PoGC fields). The outcome receipt IS hash-checked and references the settlement, but the amount in the settlement_reference is only checked by value equality, not by cross-artifact binding.

---

## Type 6 — Counterfactual Replay

**Scenario:** Present the dangerous path's execution trace (HALT) as evidence that the governance system once correctly halted. Simultaneously present the admissible path's PoGC as evidence of settled execution. Claim both happened for the same transaction.

**This is the intended package structure** — both paths share the same scenario. The attack vector is using this legitimately constructed evidence in an adversarial context: claiming the dangerous path demonstrates ongoing governance capability while the admissible path is a different real-world transaction.

**Verifier limitation:** The verifier cannot determine whether the two paths represent a test scenario or two distinct real-world events.

---

## Replay Protection Summary

| Replay Type | Verifier Protection | Gap |
|---|---|---|
| Intra-path field mutation | ✓ Hash + PQC signature | — |
| Cross-path DR injection | ✗ Not checked | **CRITICAL** |
| Stale package presentation | ✗ No clock | **HIGH** |
| Stale authority (past expiry) | ✗ No TTL enforcement | **HIGH** |
| Complete re-sign with attacker key | ✗ No external anchor | **HIGH** |
| Partial authentic artifact injection | Partial | PoGC amount not cross-bound |
| CTCHC genesis reuse | ✗ No uniqueness check | **MEDIUM** |
| rte_chain_map narrative rewrite | ✗ Not hash-covered | MEDIUM |
| CFR content mutation | ✗ Only cfr_ids hashed | HIGH |

---

## Recommendations for Institutional Reviewers

Before relying on this package for a governance decision, an institutional reviewer should:

1. **Confirm the embedded public key** via an out-of-band OMNIX channel
2. **Check `generated_at`** against the claimed transaction date manually
3. **Check `DR.expires_at`** manually and confirm it was in the future at `generated_at`
4. **Verify session consistency** manually: confirm both paths' session IDs are intentionally different (test scenario) or investigate the discrepancy
5. **Read CFR content** directly from the JSON — the verifier does not protect it
6. **Confirm the settlement reference amount** appears in the PQC-signed outcome receipt (it does, via `OUT-HASH` / `OUT-SIG`)

---

*Replay Attack Analysis — OMNIX-RTE-001 · OMNIX QUANTUM LTD · 2026-05-28*
