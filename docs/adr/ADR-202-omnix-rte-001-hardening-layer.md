# ADR-202 — OMNIX-RTE-001 Hardening Layer

**Status:** ACCEPTED  
**Date:** 2026-05-28  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Package version affected:** OMNIX-RTE-001 v1.0.0 → v1.1.0  
**Triggered by:** Adversarial review simulation (15 attacks, 4 bypasses found in v1.0.0)  
**Closes:** F-ADV-001 (CRITICAL) · F-ADV-002 (HIGH) · F-ADV-007 (HIGH) · source_state (MEDIUM)  

---

## Context

After generating OMNIX-RTE-001 v1.0.0 (ADR-201), a full adversarial review was conducted
against the package using a 15-attack simulation targeting the verifier logic, hash coverage,
and cross-artifact binding.

The simulation found 4 bypasses:

| ID | Severity | Finding |
|---|---|---|
| A09 | CRITICAL | Cross-path DR injection — dangerous authority passes as admissible (101/101 PASS) |
| A08 | HIGH | CFR content mutation — description and fragility_score mutable without CAT invalidation |
| A07 | HIGH | No TTL enforcement — expired authority indistinguishable from valid |
| source_state | MEDIUM | source_state_hash present but never verified by verifier |

This ADR documents the remediation decisions and the resulting check count increase from
101 to 111 checks in the full verification suite.

---

## Decision

### Fix A09 — Cross-Path DR Session Binding (CRITICAL)

**Root cause:** The verifier checks DR `content_hash` in isolation (self-consistency).
It does not verify that the DR belongs to the current path's session. An adversary can
replace the admissible path DR with the dangerous path DR — both DRs are internally valid
but represent different authority levels.

**Fix (generator + verifier):**

1. **Generator** (`_enrich_dr_with_session()`): After `DelegationReceiptEngine.create_delegation()`,
   inject `session_id` into the DR dict and recompute `content_hash` (SHA-256 compact) and
   re-sign (`pqc_signature`) using the session's keypair. This embeds `session_id` in the
   hash-covered payload.

2. **Generator** (`_build_mbr()`): Add `dr_id` parameter — embed the DR's `delegation_id`
   in the MBR canonical fields (hash-covered). The MBR is now cryptographically bound to a
   specific DR.

3. **Verifier** (`verify_authority()`): Add two new checks per path:
   - `DR-{PATH}-SESS`: `DR.session_id == source_state.session_id`
   - `MBR-{PATH}-DRID`: `MBR.dr_id == DR.delegation_id`

**Result:** A DR transplanted from another path has a different `session_id` in its
`content_hash`. The DR hash check fails. The session binding check fails. The MBR.dr_id
check fails. Three independent detection layers.

**New checks:** +4 (DR-DAN-SESS, MBR-DAN-DRID, DR-ADM-SESS, MBR-ADM-DRID)

### Fix A08 — CFR Content Hash Coverage (HIGH)

**Root cause:** The CAT `cfr_root_hash` was computed as
`SHA3-256([cfr_id, cfr_id, ...])` — only covering CFR IDs, not CFR content. An adversary
could mutate `fork_description`, `counterfactual_outcome`, and `fragility_score` (within
range [0.0, 1.0]) without invalidating the CFR root hash or the CAT signature.

**Fix (generator + verifier):**

1. **Generator** (`_build_cfr()`): Each CFR now includes
   `cfr_content_hash = SHA3-256(all_cfr_fields_except_cfr_content_hash)`.

2. **Generator** (`_build_cat()`): New `cfr_root_hash` formula:
   ```
   cfr_entries = [{"cfr_id": c.cfr_id, "cfr_content_hash": c.cfr_content_hash}
                   for c in sorted(cfrs, by=cfr_index)]
   cfr_root_hash = SHA3-256(json.dumps(cfr_entries, sort_keys=True))
   ```
   Mutating any CFR field changes `cfr_content_hash`, which changes `cfr_root_hash`,
   which invalidates `cat_content_hash` and the CAT PQC signature.

3. **Verifier** (`_check_cat()`): Two changes:
   - Update `cfr_root_hash` verification to use the new formula (existing check updated).
   - Add `CAT-{PATH}-CFRHASH`: verify every CFR's `cfr_content_hash` independently.

**New checks:** +2 (CAT-DAN-CFRHASH, CAT-ADM-CFRHASH) + existing CAT-ROOT check updated

### Fix A07 — TTL Temporal Warning (HIGH)

**Root cause:** The verifier checked DR `expires_at` only for hash coverage (field is
hash-covered by the DR content_hash). It never compared `expires_at` to the current
timestamp. An expired DR is cryptographically valid — the signature does not expire.

**Decision:** This is a WARNING not a FAIL. A package submitted to a reviewer 30 days after
generation will have expired DRs. The PQC signatures are still valid. The reviewer must
be informed that the authority window has elapsed, but the cryptographic evidence is intact.

**Fix (verifier only):**

Add `DR-{PATH}-TTL` per path:
- If `now() ≤ DR.expires_at`: PASS with label "DR TTL valid"
- If `now() > DR.expires_at`: WARN (non-blocking) with elapsed timestamps

`VerificationReport.warn()` method added — creates a WARN status entry (counted in total
checks, counted in `self.warned`, does not increment `self.failed`, does not affect PASS
verdict).

**New checks:** +2 (DR-DAN-TTL, DR-ADM-TTL) — WARNING type when expired, PASS when valid

### source_state Hash Verification (MEDIUM)

**Root cause:** The generator computed `source_state_hash` and embedded it in the
source_state dict. The verifier never verified this hash. A mutated source_state
(e.g., changing `risk_class`, `amount_usd`, `approved_counterparties`) would not be
detected by the verifier.

**Fix (verifier only):**

Add `_check_source_state()` function:
```python
base     = {k: v for k, v in ss.items() if k != "source_state_hash"}
expected = SHA3-256(json.dumps(base, sort_keys=True))
```
Called from `verify_authority()` per path.

**New checks:** +2 (SRC-DAN-HASH, SRC-ADM-HASH)

---

## Check Count

| Version | Total checks | PASS | Notes |
|---|---|---|---|
| v1.0.0 | 101 | 101/101 | 4 bypasses found |
| v1.1.0 | 111 | 111/111 | All bypasses closed |

**New checks breakdown:**
- A09 session binding: +4 (DR-SESS × 2, MBR-DRID × 2)
- A08 CFR content: +2 (CAT-CFRHASH × 2)
- A07 TTL: +2 (DR-TTL × 2)
- source_state: +2 (SRC-HASH × 2)
- **Total new: +10**

---

## Invariants Added / Updated

**CGE-INV-002 (updated):** CAT `cfr_root_hash` now covers `(cfr_id, cfr_content_hash)` pairs
sorted by `cfr_index`, not bare `cfr_ids`.

**RTE-INV-009 (new):** Each DR in an RTE-001 package is bound to exactly one session via
`session_id` embedded in `content_hash`. Cross-path DR substitution is detectable by the
offline verifier.

**RTE-INV-010 (new):** Each MBR contains `dr_id = DR.delegation_id`. A mandate record
cannot be separated from its delegation receipt without invalidating `mbr_content_hash`.

**RTE-INV-011 (new):** Each CFR record contains `cfr_content_hash` covering all CFR fields.
The CAT root hash covers all `cfr_content_hash` values. CFR narrative mutation is detectable.

**RTE-INV-012 (new):** The verifier checks `source_state_hash` against SHA3-256 of all
source_state fields (excluding the hash itself). Source state mutation is detectable offline.

---

## Files Changed

| File | Change type |
|---|---|
| `scripts/generate_treasury_execution_trace.py` | Modified — `_sign_raw()`, `_enrich_dr_with_session()`, `_build_cfr()`, `_build_cat()`, `_build_mbr()`, both path generators |
| `scripts/verify_treasury_execution_trace.py` | Modified — `EXPECTED_TOTAL_CHECKS`, `VerificationReport.warn()`, `_check_cat()`, `_check_source_state()`, `verify_authority()` |
| `evidence_packages/OMNIX-RTE-001_20260528_084559.json` | Regenerated — v1.1.0 package |
| `docs/reviewer/REMEDIATION_CLOSURE_REPORT.md` | New — adversarial review closure document |

---

## Consequences

- All 4 bypass findings from the adversarial simulation are closed.
- Package version bumped to `"1.1.0"` in the package metadata.
- `EXPECTED_TOTAL_CHECKS = 111` — used by consistency audits and CI pipelines.
- Warning infrastructure (`VerificationReport.warn()`) is extensible for future non-blocking
  advisory checks without modifying the PASS/FAIL verdict logic.
- Backwards compatibility: v1.0.0 packages will fail the new DR-SESS, MBR-DRID, CAT-CFRHASH,
  and SRC-HASH checks. This is intentional — v1.0.0 packages had structural gaps.

---

## References

- ADR-201: OMNIX-RTE-001 Runtime Treasury Execution Trace (base spec)
- ADR-200: Route Complete Evidence Package (RCEP canonicalization profiles)
- RFC-ATF-1: Agent Trust Fabric — ATF-INV-001–006
- RFC-ATF-5: Cognitive Governance Layer — CGE-INV-001–007
- `docs/reviewer/ADVERSARIAL_REVIEW_REPORT.md` — 15-attack simulation results
- `docs/reviewer/VERIFIER_BYPASS_ANALYSIS.md` — bypass root cause analysis
