# VERIFIER BYPASS ANALYSIS
## OMNIX-RTE-001 — Adversarial Verifier Semantics

**Role:** Protocol engineer + hostile cryptography reviewer  
**Date:** 2026-05-28  
**Methodology:** Static analysis of `verify.py` + dynamic execution of bypass attempts

---

## Verifier Architecture Overview

```
verify.py
├── _load_pqc()             — loads Dilithium-3 from pqc PyPI or omnix_core
├── _verify_sig()           — compact sep JSON payload signature
├── _verify_sig_bytes()     — raw bytes signature (DR/TAR profile)
├── _verify_sig_default()   — default sep JSON signature (BAR/CTCHC profile)
├── _add_sig()              — SKIP sentinel vs FAIL routing
├── _hash_compact()         — SHA-256 compact (DR/TAR)
├── _hash_default()         — SHA3-256 default (all others)
└── verifier functions:
    _check_dr / _check_tar / _check_rcr / _check_mbr / _check_mas
    _check_mbr_seal / _check_cat / _check_osg_vr / _check_bar
    _check_ctchc / _check_pogc / _check_tcs / _check_refusal
    _check_outcome / _check_replay
```

---

## Bypass Category 1 — Hash-Uncovered Fields

### B1-01: Package Metadata

Fields confirmed NOT in any artifact hash:
```python
pkg["scenario"]["amount_usd"]      # A01: BYPASS confirmed
pkg["rte_chain_map"][*]            # A03: BYPASS confirmed
pkg["_attacker_note"]              # Injected root field: BYPASS
pkg["regulatory_clearance"]        # Injected root field: BYPASS
pkg["package_version"]             # Metadata mutation: BYPASS
pkg["omnix_version"]               # Metadata mutation: BYPASS
pkg["invariants_demonstrated"]     # Invariant list: BYPASS
pkg["verification_instructions"]   # Instructions: BYPASS
pkg["paths"][*]["label"]           # Path label: BYPASS
pkg["paths"][*]["rte_verdict"]     # Path verdict string: BYPASS
pkg["paths"][*]["summary"]         # Summary section: BYPASS
```

**Demonstrated:** Adding `{"_attacker_note": "...", "regulatory_clearance": {...}}` at package root → `101/101 PASS`.

### B1-02: CFR Content Fields

```python
cfr["description"]       # A08: BYPASS confirmed
cfr["outcome_summary"]   # A08: BYPASS confirmed
cfr["fragility_score"]   # A08: BYPASS (in [0,1]) confirmed
cfr["counterfactual_action"]  # Not individually hash-checked
cfr["reasoning"]              # Not individually hash-checked
```

The CAT verifier:
```python
expected_root = _sha3(json.dumps([c["cfr_id"] for c in cfrs], sort_keys=True))
```
Only the `cfr_id` list is committed. CFR content is decorative from the verifier's perspective.

### B1-03: Source State Fields

```python
step1["source_state_hash"]  # Field is present, but not verified by verifier
step1["treasury_context"]   # Not hash-covered
step1["policy_constraints"] # Not hash-covered
step1["request_id"]         # Not hash-covered
```

The verifier has no `_check_source_state()` function. Step 1 is entirely unverified.

### B1-04: Step 5 — TAR Dangerous Path

The dangerous path `5_verdict` TAR is not individually verified:
```python
step5["admission_status"]  # Read by verifier → HALT check uses OSG verdict, not TAR
step5["content_hash"]      # Present but NOT verified
step5["pqc_signature"]     # Present but NOT verified
```

The verifier checks `OSG verdict=REJECTED` for the dangerous path. The TAR `content_hash` and signature are never checked.

---

## Bypass Category 2 — Session Binding Gaps

### B2-01: Cross-Path DR Injection (CRITICAL — A09 BYPASS)

**Bypass confirmed:** `101 / 101 PASS`

Root cause in `_check_dr()`:
```python
def _check_dr(report, dr, pqc, pk_bytes, path):
    expected = _hash_compact(dr, exclude=["content_hash","pqc_signature","pqc_algorithm"])
    actual   = dr.get("content_hash", "")
    hash_ok  = expected == actual
    report.add(...)  # PASS if internally consistent
    
    raw_ch = actual.encode("utf-8")
    ok, detail = _verify_sig_bytes(pqc, pk_bytes, raw_ch, dr.get("pqc_signature"))
    _add_sig(...)  # PASS if PQC sig verifies
```

**Missing check (required to close bypass):**
```python
# NOT PRESENT in verifier:
path_session = pkg["paths"][path_key]["steps"]["1_source_state"]["session_id"]
assert dr.get("session_id") == path_session, "DR session binding violation"
```

### B2-02: MBR Does Not Reference DR

The MBR canonical payload:
```python
sig_payload = {"mbr_id": mbr.get("mbr_id"), 
               "mbr_content_hash": actual, 
               "issued_at": mbr.get("issued_at")}
```

The MBR hash:
```python
_hash_default(mbr, exclude=["mbr_content_hash","pqc_signature","pqc_algorithm"])
```

`DR.dr_id` is NOT in the MBR canonical fields or sig payload. An MBR can be swapped between DRs of the same path without detection if the MBR's mandate_amount happens to match.

---

## Bypass Category 3 — Semantic Scope Limits (By Design)

The verifier explicitly documents these out-of-scope items. A hostile reviewer treats them as attack surfaces despite the documentation:

### B3-01: FX Bands and Counterparty Lists
```
"Does NOT verify governance policy values (FX bands, counterparty lists, mandate amounts)"
```
`policy_constraints` in source_state is not verified. An attacker can insert any constraints.

### B3-02: CES Component Weights
The verifier checks `CES formula consistent (expected≈42.05, got=42.05)` using:
```python
expected_ces = round(t*0.30 + b*0.30 + d*0.20 + i*0.20, 2)
```
But it reads the weights (0.30, 0.30, 0.20, 0.20) as constants, not from the package. If a package was generated with different weights, the CES check would fail. However: the weights themselves are not in the RCR hash. An adversary who knows the CES formula can construct any CES value with compliant component scores.

### B3-03: External Market Data
Source state `treasury_context` fields (FX rates, counterparty details, instrument) are not hash-covered and not verified.

---

## Bypass Category 4 — Separator Sensitivity

### B4-01: Compact vs Default Separators

The verifier uses two separator profiles:
- **Compact** `(",",":")`: DR, TAR, MBR (sig payload), MBR Seal (sig payload), CAT (sig payload), TCS (sig payload), OSG VR (sig payload), Refusal (sig payload), Outcome (sig payload), Replay (sig payload), PoGC (sig payload)
- **Default** `(", ", ": ")`: BAR, CTCHC

A single separator error in the generator would cause ALL signature checks for that artifact type to fail. The verifier's separator assignment is hardcoded and must match the generator exactly.

**Attack surface:** A package generated with wrong separators shows mass signature failures. This is detected, but the diagnostic message says only "signature mismatch" without indicating the root cause. A reviewer sees 26 FAILED with no clue that it's a separator mismatch vs key mismatch vs content tampering.

### B4-02: sort_keys=True Is Non-Negotiable

All hash and sig functions use `sort_keys=True`. Key ordering attacks are therefore not effective:

```python
# This is detected (A12 confirmed: +00:00 → Z causes hash mismatch)
pkg["issued_at"] = "2026-05-28T07:18:12Z"  # format change → FAIL

# This is NOT detected (field addition to uncovered section):
pkg["scenario"]["_extra"] = "injected"  # no hash → PASS
```

---

## Bypass Category 5 — PQC Verification Mode Interaction

### B5-01: SKIP vs FAIL Disambiguation (Designed Behavior)

Without `pip install pqc`, all 26 PQC sig checks are SKIPPED:
```
TOTAL CHECKS : 101
PASSED        : 75
FAILED        : 0
SKIPPED       : 26
VERDICT: STRUCTURAL + HASH CHECKS PASS
```

**A hostile reviewer's attack:** Present this output to a non-technical audience and claim "ALL VERIFICATIONS PASS." The output says STRUCTURAL + HASH CHECKS PASS, not "ALL VERIFICATIONS PASS." The distinction requires reading carefully.

**Verifier mitigation:** The verdict string is different. Exit code is still 0 (by design — SKIP is not FAIL). A reviewer processing exit codes only would see 0 = success for both states.

**Recommendation:** When skipped > 0, exit code should be 3 (partial verification) to distinguish from complete verification.

### B5-02: Exception Handling in PQC Verifier

```python
def verify_signature(self, sig_bytes, msg_bytes, pk):
    try:
        _dil3.verify(sig_bytes, msg_bytes, pk)
        return True
    except Exception:
        return False
```

Any exception (malformed sig, wrong key, corrupted bytes) returns `False`, which maps to FAIL. This is correct behavior, but the diagnostic message "signature mismatch" does not distinguish between "invalid signature" and "malformed input." Both fail, but the root cause is different for forensic purposes.

---

## Bypass Category 6 — Verifier Completeness Gaps

### B6-01: Missing Artifact Verifiers

Artifacts in the package without individual verifier functions:

| Artifact | Location | Verified |
|---|---|---|
| `source_state_hash` | step 1 | ✗ |
| `TAR` (dangerous path) | step 5 | ✗ (content_hash not checked) |
| `binding_record` | admissible step 5 | ✗ |
| `commit_record` | admissible step 5 | ✗ |
| CCS (Constraint Conformance Signal) | step 3 | ✗ |
| Individual CFR records | step 4 | ✗ (only CAT verified) |

### B6-02: MAR Check Is Directionally Incomplete

The verifier checks MAR (Monotonic Authority Reduction):
```python
report.add(..., budget_granted <= budget_delegator, ...)
```

This checks that the DR's budget is ≤ the delegator's budget. It does NOT check:
- Whether `budget_delegator` is itself legitimate (no grandparent DR check)
- Whether `budget_granted` is semantically appropriate for the action (no mandate cross-check)
- Whether the same DR is reused across multiple sessions (no uniqueness check)

---

## Bypasses Confirmed vs Expected — Full Matrix

| Bypass | Confirmed | Expected By Design |
|---|---|---|
| scenario.amount_usd mutable | ✓ | Scope limit (documented) |
| rte_chain_map mutable | ✓ | Scope limit (documented) |
| CFR content mutable | ✓ | **GAP** — should be hash-covered |
| Cross-path DR injection | ✓ | **GAP** — session binding missing |
| No TTL enforcement | ✓ | **GAP** — needs documentation or fix |
| source_state not verified | ✓ | **GAP** — source_state_hash unused |
| TAR (dangerous) not verified | ✓ | **GAP** — partial coverage |
| No external key anchor | ✓ | Architectural (PoGR pending, ADR-186) |
| SKIP=0 exit code ambiguity | ✓ | Design choice — debatable |

---

## Verifier Hardening Checklist

**Must fix (protocol correctness):**
- [ ] `_check_dr()`: add `DR.session_id == path.session_id` assertion
- [ ] `_check_cat()`: include per-CFR content hash in `cfr_root_hash` computation
- [ ] `_check_source_state()`: add verifier function for `source_state_hash`

**Should fix (institutional credibility):**
- [ ] TTL warning: compare `issued_at` + max_validity_window to `generated_at`
- [ ] TAR verification: add `_check_tar_dangerous()` for step 5
- [ ] SKIP exit code: use exit=3 when any checks are SKIPPED

**Should document (scope clarity):**
- [ ] Explicitly state that `scenario`, `rte_chain_map`, and `paths[*].summary` are informational only
- [ ] State that CFR content integrity is not verified (hash covers IDs only)
- [ ] State that the embedded public key requires external validation for production use

---

*Verifier Bypass Analysis — OMNIX-RTE-001 · OMNIX QUANTUM LTD · 2026-05-28*
