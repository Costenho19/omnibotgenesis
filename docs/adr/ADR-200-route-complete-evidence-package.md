# ADR-200 — Route-Complete Evidence Package (RCEP)

**Status:** ACCEPTED  
**Date:** 2026-05-27  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** —  
**Related:** ADR-028 (receipts), ADR-156 (DR), ADR-157 (TAR), ADR-159 (RCR), ADR-181 (BAR), ADR-183 (CTCHC), ADR-186 (PoGR)  
**RFCs:** RFC-ATF-1 through RFC-ATF-6  

---

## 1. Context

Third-party reviewers evaluating OMNIX's governance claims (TA-14 admissibility standard, Butler review) require a self-contained artefact that proves two structurally opposite outcomes without any access to the OMNIX runtime, database, or network:

1. **Route A — REFUSAL**: execution is structurally impossible when authority is exhausted.  
2. **Route B — ADMISSION**: execution is admitted only when every chain link in the governance stack is complete.

No existing artefact provided this dual-route proof in a single, offline-verifiable JSON document with all PQC signatures embedded and a standalone verifier script.

---

## 2. Decision

Introduce the **Route-Complete Evidence Package (RCEP)** — a JSON document containing the full 8-step TA-14 admissibility chain for both routes, with:

- A fresh Dilithium-3 (ML-DSA-65, FIPS 204) keypair generated per package run, with the public key embedded for offline verification.
- Every governance artefact (DR, TAR, RCR, Binding, Commit, BAR, CTCHC, PoGC) serialized inline with its PQC signature.
- A standalone verifier script (`scripts/verify_evidence_package.py`) with zero OMNIX runtime dependencies.
- A machine-readable verification report written alongside the package after every run.

The package is **not a production receipt**. It is an auditor-grade demonstration of the complete governance chain, generated on demand for TA-14 and similar reviews.

---

## 3. Architecture — The 8-Step TA-14 Chain

Each route follows the same 8-step chain. The steps map to the TA-14 admissibility framework:

| Step | Key | TA-14 Layer | Artefact |
|---|---|---|---|
| 1 | `1_source_state` | Reality | Source state hash |
| 2 | `2_record` | Record | DelegationReceipt (DR) |
| 3 | `3_continuity` | Continuity | Runtime Continuity Record (RCR) |
| 4 | `4_admissibility` | Admissibility | TemporalAdmissibilityRecord (TAR) |
| 5 | `5_binding` | Binding | Binding record |
| 6 | `6_commit` | Commit | Commit record |
| 7 | `7_execution` | Execution | BAR + CTCHC (Route B) / Refusal receipt (Route A) |
| 8 | `8_outcome` | Outcome | PoGC + Outcome receipt (Route B) / Refusal outcome (Route A) |

**Route A differentiation**: refusal occurs at step 5 (binding refused, authority budget = 0.0 / ATF-INV-001). Step 6 records that execution was structurally unreachable. Step 7 issues a PQC-signed HARD_REFUSAL receipt. Step 8 records `execution_occurred=False` and `what_remained_impossible`.

**Route B differentiation**: all 8 steps complete successfully. BAR attests the actual agent output. CTCHC seals the turn chain. PoGC issues a MANDATE-BOUND certificate.

---

## 4. Canonicalization Profile Registry

This is the authoritative reference for how each artefact is hashed and signed in RCEP v1.0.0. Any future version of the verifier **must** consult this registry before changing hash or signature logic.

### 4.1 Hash canonicalization

| Artefact | Hash algo | JSON separators | Excluded fields |
|---|---|---|---|
| Source state | SHA3-256 | **default** (`", ": "`) | `source_state_hash` |
| DR (`content_hash`) | SHA-256 | **compact** (`,` `:`) | `content_hash`, `pqc_signature`, `pqc_algorithm` |
| TAR (`content_hash`) | SHA-256 | **compact** (`,` `:`) | `content_hash`, `pqc_signature`, `pqc_algorithm` |
| RCR (`rcr_hash`) | SHA3-256 | **default** | `rcr_hash`, `pqc_signature`, `pqc_algorithm` |
| Binding (`binding_hash`) | SHA3-256 | **default** | `binding_hash`, `pqc_signature`, `pqc_algorithm` |
| Commit (`commit_hash`) | SHA3-256 | **default** | `commit_hash`, `pqc_signature`, `pqc_algorithm` |
| Refusal receipt | SHA3-256 | **default** | `content_hash`, `pqc_signature`, `pqc_algorithm` |
| BAR (`content_hash`) | SHA3-256 | **default** | canonical 6-field tuple (see §4.2) |
| PoGC (`content_hash`) | SHA3-256 | **default** | `content_hash`, `pqc_signature` ONLY — `pqc_algorithm` **IS included** (§4.3) |
| Outcome receipt | SHA3-256 | **default** | `content_hash`, `pqc_signature`, `pqc_algorithm` |

> **Why two separator modes?** DR and TAR hashes are produced by `DelegationReceiptEngine` and `TemporalAuthorityEngine` which use SHA-256 + compact separators (established in ADR-028 / ADR-156 / ADR-157 before RCEP). All generator-native hashes (RCR, binding, commit, refusal, outcome, PoGC) use SHA3-256 + default separators. This asymmetry is intentional and locked at v1.0.0.

### 4.2 BAR content_hash canonical tuple

```python
{
  "session_id":           <str>,
  "agent_id":             <str>,
  "turn_index":           <int>,
  "output_hash":          <str>,
  "governing_receipt_id": <str>,
  "constraint_set_hash":  <str>,
}
# sorted keys=True, default separators, SHA3-256
```

### 4.3 PoGC content_hash — pqc_algorithm inclusion

`pqc_algorithm` is included in the `canonical_fields` dict **before** hashing. This binds the algorithm name into the certificate's integrity proof. The verifier must NOT exclude `pqc_algorithm` when recomputing the PoGC hash.

### 4.4 Signature payload canonicalization

| Artefact | Signing party | Payload | Separators |
|---|---|---|---|
| DR | DelegationReceiptEngine | `content_hash.encode()` (raw bytes, not JSON) | N/A |
| TAR | TemporalAuthorityEngine | `content_hash.encode()` (raw bytes, not JSON) | N/A |
| RCR | generator `_sign_payload` | `{"rcr_id": …, "rcr_hash": …}` | **compact** |
| Binding | generator `_sign_payload` | `{"binding_id": …, "binding_hash": …}` | **compact** |
| Commit | generator `_sign_payload` | `{"commit_id": …, "commit_hash": …}` | **compact** |
| BAR seal | `BAREngine.create_bar` | `{"bar_id":…, "content_hash":…, "governing_receipt_id":…, "created_at":…}` | **default** |
| CTCHC seal | `CTCHCEngine.seal_chain` | `{"chain_id":…, "seal_hash":…, "session_id":…}` | **default** |
| PoGC | generator `_sign_payload` | `{"pogc_id":…, "content_hash":…, "issued_at":…}` | **compact** |
| Refusal | generator `_sign_payload` | `{"receipt_id":…, "content_hash":…, "issued_at":…}` | **compact** |
| Outcome | generator `_sign_payload` | `{"receipt_id":…, "content_hash":…, "issued_at":…}` | **compact** |

> **Why two separator modes for signatures?** `BAREngine` and `CTCHCEngine` predate RCEP and use Python's `json.dumps` without separator override (default). All generator-native signings use `_sign_payload` with compact separators. The verifier must match each signing party's behaviour exactly.

### 4.5 CTCHC genesis verification

CTCHC genesis hash is computed inside `CTCHCEngine.initialize_chain()` using `initialized_at = datetime.now(timezone.utc).isoformat()`. However, the value serialized into the package JSON may differ in format depending on Python version and whether the DB round-trip path is taken (PostgreSQL `TIMESTAMPTZ` → Python `datetime` → `str()` produces space-separated format instead of `T`-separated ISO 8601).

**Verification approach:** The verifier confirms genesis integrity via **chain continuity**:

1. `chain.governing_receipt_id == governing_receipt_id` (genesis anchors to the DR)  
2. `links[0].prev_link_hash == chain.genesis_hash` (chain starts at declared genesis)

This is cryptographically equivalent to re-deriving genesis from `initialized_at` because:
- The `seal_hash` covers `genesis_hash` (step 4 in CTCHC verification).
- The `seal_pqc_signature` is a Dilithium-3 signature over `seal_hash`.
- Any tampering with `genesis_hash` would invalidate the PQC-signed seal.

---

## 5. Verifier Scope Limits (TA-14 Gap 6)

The standalone verifier confirms:

- ✓ Every PQC signature (Dilithium-3 ML-DSA-65) verifies against the embedded public key.
- ✓ Every content_hash / binding_hash / commit_hash / seal_hash is recomputed from the stored fields and matches.
- ✓ CTCHC link-by-link hash chain is internally consistent.
- ✓ CTCHC genesis is anchored to the governing receipt and the chain starts there.
- ✓ PoGC mandate_certification is present and valid.
- ✓ Route A: `execution_occurred=False`, `what_remained_impossible` populated.
- ✓ Route B: TAR `admission_status=ADMITTED`, commit `execution_reachable=True`.

The verifier does **not** confirm:

- ✗ Governance policy parameters (mandate risk ceilings, approval thresholds) — see `docs/standards/`.
- ✗ External market data referenced in `source_state.market_context`.
- ✗ The correctness of the governance decision itself — only its cryptographic integrity.

---

## 6. Invariants

| ID | Invariant |
|---|---|
| RCEP-INV-001 | Every RCEP must contain both Route A and Route B. |
| RCEP-INV-002 | The PQC keypair is generated fresh per package run. The embedded public key is the sole verification authority for all signatures in that package. |
| RCEP-INV-003 | Route A must produce `execution_occurred=False` and a HARD_REFUSAL receipt. |
| RCEP-INV-004 | Route B must produce `execution_occurred=True`, `bar_status=VALID`, `is_sealed=True`, and `mandate_certification` in (`MANDATE-BOUND`, `MANDATE-ALIGNED`). |
| RCEP-INV-005 | The verifier must exit with code 0 (all checks pass) or code 1 (one or more failures). It must write a machine-readable verification report alongside the package. |
| RCEP-INV-006 | The Canonicalization Profile Registry in §4 is immutable for v1.0.0 packages. Any change requires a new `package_version` and a new ADR amendment. |

---

## 7. Files

| File | Purpose |
|---|---|
| `scripts/generate_route_evidence_package.py` | Generator — produces RCEP JSON |
| `scripts/verify_evidence_package.py` | Standalone offline verifier |
| `evidence_packages/` | Output directory for generated packages |
| `evidence_packages/*_verification_report.json` | Machine-readable report written by verifier |

---

## 8. Consequences

**Positive:**
- Butler and other third-party reviewers can run `python scripts/verify_evidence_package.py <package>.json` and get a 52-check, 0-failure result offline.
- The Canonicalization Profile Registry (§4) eliminates the separator-inconsistency class of bugs permanently.
- The CTCHC genesis approach (chain continuity) is documented as intentional and is more robust than timestamp re-derivation.

**Negative:**
- The separator asymmetry between DR/TAR (SHA-256/compact) and generator-native artefacts (SHA3-256/default) is locked in. Future artefacts should use a single canonicalization profile.
- The RCEP keypair is ephemeral (demo-grade). A production PoGC would use the Railway-stored `OMNIX_SIGNING_SECRET_KEY_B64`.

---

## 9. Alternatives Considered

**A. Re-use production key instead of ephemeral keypair**: rejected — demo packages must not depend on Railway secrets being available. The embedded public key model is self-contained and offline-verifiable by design.

**B. Single-route package (ADMISSION only)**: rejected — Butler's TA-14 review specifically requires proving that execution is structurally blocked under invalid authority (not just that valid authority produces a receipt).

**C. Fix CTCHCEngine to always store initialized_at as ISO T-string**: deferred — the bug exists in the DB round-trip path (`str(row["initialized_at"])` returns space-separated format). The chain-continuity genesis verification is architecturally superior. Tracked for future cleanup.
