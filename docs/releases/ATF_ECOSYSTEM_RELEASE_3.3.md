# ATF Ecosystem Release 3.3
## OMNIX QUANTUM LTD — Agent Trust Fabric Protocol Stack

**Release Identifier:** OMNIX-ATF-RELEASE-3.3-2026-05  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Contact:** omnixquantum.net

---

## Release Summary

ATF Ecosystem Release 3.3 completes the formal specification of the OMNIX Agent Trust Fabric protocol stack. This release adds RFC-ATF-3 (Forensic Verification Protocol), formalizes the Governance Execution Context Router (GECR, ADR-170), closes six structural gaps in the invariant coverage matrix, and delivers cross-language conformance infrastructure for SDK implementers.

The ATF stack now covers the full lifecycle of an agent governance event:

```
Human authority → Delegation → Temporal admissibility → Runtime continuity
→ Commit-time re-evaluation → Evidence archival → Offline forensic verification
```

Every transition in this chain is governed by a formally specified invariant, implemented in a named module, tested by an identified test, and independently verifiable offline using only the platform's public key.

---

## Published RFC Artifacts

| RFC | Title | Zenodo DOI | Figshare DOI | SSRN ID | Status |
|---|---|---|---|---|---|
| RFC-ATF-1 | Agent Trust Fabric — Delegation Protocol with Post-Quantum Signatures (ML-DSA-65 / NIST FIPS 204) | [10.5281/zenodo.20155016](https://doi.org/10.5281/zenodo.20155016) | [10.6084/m9.figshare.32308077](https://doi.org/10.6084/m9.figshare.32308077) | 6757339 | ✅ Published |
| RFC-ATF-2 | Agent Trust Fabric — Runtime Governance Continuity | [10.5281/zenodo.20241344](https://doi.org/10.5281/zenodo.20241344) | [10.6084/m9.figshare.32308095](https://doi.org/10.6084/m9.figshare.32308095) | 6763978 | ✅ Published |
| RFC-ATF-3 | Agent Trust Fabric — Governance Policy Interoperability, Evidence Lifecycle & Forensic Verification Protocol | [10.5281/zenodo.20247342](https://doi.org/10.5281/zenodo.20247342) | [10.6084/m9.figshare.32308119](https://doi.org/10.6084/m9.figshare.32308119) | — | ✅ Published |

**Supporting publications:**

| Document | Repository | DOI / ID |
|---|---|---|
| OMNIX Technical Whitepaper v1.5 | SSRN | 6507559 |
| OMNIX Technical Whitepaper v1.5 | Zenodo | 10.5281/zenodo.19375792 |
| Production Dataset — 82,569 governance decisions | Zenodo | 10.5281/zenodo.19056919 |
| OMNIX Production Study | SSRN | 6321298 |

All Zenodo and Figshare DOIs are permanent. Zenodo is indexed by OpenAIRE and DataCite. Figshare is indexed by Thomson Reuters Data Citation Index.

---

## Invariant System — Release 3.3 State

**Total invariants: 47 across 9 families**

| Family | Count | RFC / ADR | Domain |
|---|---|---|---|
| ATF + TAR | 7 | RFC-ATF-1 · ADR-156/157 | Delegation integrity · temporal admissibility |
| RGC | 8 | RFC-ATF-2 · ADR-159/160 | Runtime continuity · CES scoring |
| GPIL | 3 | RFC-ATF-3 Part I · ADR-161 | Cross-runtime policy interoperability |
| ELR | 4 | RFC-ATF-3 Part II · ADR-162 | Evidence lifecycle · reclassification prevention |
| EAP | 7 | RFC-ATF-3 Part III · ADR-163/167 | Evidence archive pipeline · cold block integrity |
| OEP | 6 | RFC-ATF-3 Part IV · ADR-165 | Offline evidence package · self-contained verification |
| FEA | 5 | RFC-ATF-3 Part V · ADR-166 | Forensic export access control |
| FVP | 1 | RFC-ATF-3 Part VI · ADR-164/167 | Verification portal · key identity disclosure |
| GECR | 6 | ADR-170 | Governance execution context routing |

**Coverage (as of this release):**

```
Direct test coverage:   41 / 47  =  87.2%
Structural enforcement:  6 / 47  =  12.8%
Zero coverage:           0 / 47  =   0.0%
```

Authoritative traceability: `docs/compliance/INVARIANT_TEST_MATRIX.md` (OMNIX-COMPLIANCE-INV-MATRIX-2026-05, rev.3)

---

## Release 3.3 Changelog

### NEW: RFC-ATF-3 — Forensic Verification Protocol

RFC-ATF-3 specifies four protocol areas not covered by RFC-ATF-1 or RFC-ATF-2:

**Part I — Governance Policy Interoperability Layer (GPIL, ADR-161)**  
Formal specification for cross-runtime governance compatibility. Two sovereign OMNIX runtimes sharing the same cryptographic interoperability layer (ML-DSA-65 verification) may hold different policy parameters within protocol-defined bounds. The GPIL resolves this by defining three interoperability layers — Cryptographic (unconditional), Protocol (invariant-bound), and Governance Policy (sovereign but bounded). Cross-Runtime Governance Contracts (CRGC) are bilaterally signed by both runtimes before any cross-runtime agent operation is admitted.

**Part II — Evidence Lifecycle Registry (ELR, ADR-162)**  
Formal specification that evidence class is immutable protocol state from creation. A reclassification attack — changing an artifact's class during archive tier transitions (HOT→WARM→COLD) — is structurally detectable via the `classification_hash` binding (evidence_class + payload + timestamp + evidentiary_meaning), which is computed at creation and preserved through all transitions.

**Part III — Evidence Archive Pipeline (EAP) Extensions (ADR-163/167)**  
Formalizes HOT→WARM→COLD tier transitions as irreversible. Block IDs are globally unique via Redis INCR in production (ADR-167 §2.2). Manifest completeness: every tier transition creates a manifest entry before the transition executes, or rolls back.

**Part IV — OMNIX Evidence Package (OEP) Protocol (ADR-165)**  
Self-contained ZIP package enabling complete offline forensic verification. An OEP contains: MANIFEST.json (block metadata), BLOCKS/ (COLD block files), KEYS/public_key.b64 (platform verification key embedded), SIGNATURE/package_signature.json (ML-DSA-65 signature over canonical manifest hash), and a VERIFIER/ directory with the standalone Python CLI. No network access, no platform access, no OMNIX runtime required to verify.

**Part V — Forensic Export Access Control (FEA, ADR-166)**  
API-key gated export endpoint (`/api/forensic/export`). Platform private key never leaves the server boundary; all OEP packages are signed server-side before delivery. `FORENSIC_EXPORT_ALLOW_CALLER_KEYS=true` is explicitly prohibited in production environments (FEA-INV-005).

**Part VI — Forensic Verification Portal (FVP, ADR-164/167)**  
Dual-plane verification: Plane 1 (browser-side, canonical hash + Merkle root recomputation) and Plane 2 (server-side, ML-DSA-65 PQC signature verification). When planes disagree, server verdict is binding. Every `/verify` response includes a `key_identity` object carrying the platform fingerprint — enabling a verifier to confirm they are checking against the correct platform key without trusting the response itself (key must be obtained independently from DNS TXT or Zenodo registry).

### NEW: ADR-170 — Governance Execution Context Router (GECR)

The GECR is the formal specification of Mode C governance — *control and proof as a single atomic operation*. Prior governance architectures operated in either Mode A (real-time control without independently verifiable proof) or Mode B (cryptographic proof at admission without continuous control through execution). OMNIX operates in Mode C:

> A governance receipt is not a record of a decision that already occurred. It is the authorization that makes the next action admissible. The control and the proof are the same event.

The GECR comprises six components integrated with the Unified Decision Control Layer (UDCL):

| Component | Module | ADR | Invariant |
|---|---|---|---|
| Context Pre-Admission Router (CPR) | `context_admission_gate.py` | ADR-050 | GECR-INV-002 |
| Commit-Time Re-Evaluation Gate (CREG) | `commit_time_gate.py` | ADR-140 | GECR-INV-002 |
| Continuity-Aware Admission Controller (CAAC) | `runtime_continuity.py` | ADR-159 | GECR-INV-001 |
| Cross-Agent Budget Enforcer (CABE) | `runtime_continuity.py` (AFG) | ADR-159 | GECR-INV-003 |
| Workflow Interruption Signal (WIS) | `runtime_continuity.py` (HALT) | ADR-159 | GECR-INV-004 |
| Cross-Runtime Policy Router (CRPR) | ADR-161 CRGC | ADR-161 | GECR-INV-005 |

**Key invariant — GECR-INV-001 (Control-Receipt Atomicity):**  
No controlled action proceeds without a receipt being issued first. This is not a policy choice; it is a structural property of the UDCL pipeline. Layer 3 PQC receipt issuance is non-optional. There is no code path in the GECR through which a commit can be authorized without a signed ControlReceipt.

### CLOSED: TAR-INV-006 — Compiled Staleness Bound (ADR-157 rev.2)

`RCR_CES_STALENESS_BOUND_SECONDS = 300` is now a compiled constant in `runtime_continuity.py`, not an environment variable. The constant cannot be overridden at runtime. Verified by env-monkeypatch tests in `test_tar_inv006_staleness_bound.py` (23 passing tests, including immutability verification). Simultaneously closes RGC-INV-007 (CES inputs must meet freshness requirements).

### CLOSED: RGC-INV-007 — CES Input Freshness

CES inputs older than 300 seconds are structurally rejected. `rcr_performance.py` EventDrivenSampler `notify()` pattern ensures sampling is event-driven, not purely periodic. Status promoted from Structural to Direct (test coverage).

### Cross-Language Conformance Infrastructure

`sdk/conformance_vectors.json` — 12 machine-generated conformance vectors (7 Key Fingerprint + 5 Canonical JSON) produced from the Python reference implementation. Any SDK (Python, Node.js, Go, Rust, Java) must pass against this vector file.

- `tests/test_conformance_vectors.py` — 37 Python conformance tests
- `sdk/node/conformance_check.ts` — 17 Node.js conformance checks (Key Fingerprint + Canonical JSON)
- All 54 cross-language checks pass as of this release

---

## Architecture Decision Records — Release 3.3

| ADR | Title | Status | Extends |
|---|---|---|---|
| ADR-161 | Governance Policy Interoperability Layer (GPIL) | Accepted | ADR-156/157/159 |
| ADR-162 | Evidence Lifecycle Registry (ELR) | Accepted | ADR-163 |
| ADR-163 | Evidence Archive Pipeline (EAP) | Accepted | ADR-028 |
| ADR-164 | Forensic Verification Portal (FVP) | Accepted | ADR-163/165 |
| ADR-165 | OMNIX Evidence Package (OEP) | Accepted | ADR-163/164 |
| ADR-166 | Forensic Export Access (FEA) | Accepted | ADR-165 |
| ADR-167 | Platform Key Registry | Accepted | ADR-165/166 |
| ADR-168 | CES Staleness Bound Compiled Constant | Accepted | ADR-157/159 |
| ADR-169 | SDK Conformance Vector Infrastructure | Accepted | ADR-156/164 |
| ADR-170 | Governance Execution Context Router (GECR) | Accepted | ADR-050/138/140/157/159/161 |

**Total ADRs: 170**  
Complete index: `docs/ARCHITECTURE_INDEX.md`

---

## Test Coverage — Release 3.3

| Suite | Tests | Status | Coverage Area |
|---|---|---|---|
| `test_atf_receipts.py` | 47 | ✅ All pass | DR/TAR/DTR/AIR field integrity, MAR, chain root, immutability |
| `test_agent_trust_fabric.py` | 31 | ✅ All pass | ATF stack integration, DAG structure, chain verification |
| `test_runtime_governance_continuity.py` | 38 | ✅ All pass | RCR, CES formula, HALT propagation, AFG, RC TTL |
| `test_governance_integrity.py` | 29 | ✅ All pass | GECR components, CTAG drift, AVM thresholds |
| `test_cold_block_archive.py` | 109 | ✅ All pass | EAP tier transitions, COLD block integrity, chain linkage |
| `test_oep_forensic_audit.py` | 41 | ✅ All pass | OEP structure, FEA access control, offline verification |
| `test_eap_extended_audit.py` | 58 | ✅ 54 pass / 4 skip | FVP key identity, FEA auth, cross-language conformance |
| `test_gpil_audit.py` | 24 | ✅ All pass | GPIL protocol bounds, CRGC signing, policy parameters |
| `test_conformance_vectors.py` | 37 | ✅ All pass | SDK canonical JSON + key fingerprint vectors (Python) |
| `test_tar_inv006_staleness_bound.py` | 23 | ✅ All pass | TAR compiled constant, env-monkeypatch immutability |
| Additional suites | 58+ | ✅ All pass | Code verification, response validator, systemic router |
| **TOTAL** | **495+** | ✅ | Full institutional coverage |

---

## Open Items — Known Gaps

The following structural gaps are documented, acknowledged, and scheduled for closure. They do not affect the validity of the invariant claims — the invariants are enforced structurally — but they represent points where explicit rejection tests would strengthen the audit posture.

| Priority | Invariant | Gap Description | Target File | Sprint |
|---|---|---|---|---|
| 1 | ATF-INV-002 | Cycle injection test: circular DR chain must be rejected | `test_agent_trust_fabric.py` | Next |
| 2 | ELR-INV-003 | Reclassification rejection: attempt to change `evidence_class` on transition, assert error | `test_eap_audit.py` | Next |
| 3 | ELR-INV-004 | Compression rejection: attempt to strip LEGAL-class artifact fields, assert rejection | `test_eap_audit.py` | Next |
| 4 | EAP-INV-007 | Production Redis probe: `OMNIX_ARCHIVE_REDIS_REQUIRED=true` + absent REDIS_URL = hard fail | `test_cold_block_archive.py` | Next |
| 5 | FEA-INV-001 | Default-false test: absent `FORENSIC_EXPORT_ALLOW_CALLER_KEYS` behaves as false | `test_oep_forensic_audit.py` | Next |
| 6 | ELR-INV-003 (impl) | Implement `omnix_core/governance/gpil.py` runtime module — CRGC issuance, signing, storage | `gpil.py` | Future |

---

## Artifacts

| Artifact | Description | Location |
|---|---|---|
| `omnix_atf_verify.py` v1.1.0 | Standalone offline CLI verifier — zero external dependencies except `pypqc` | `sdk/omnix_atf_verify.py` |
| `sdk/conformance_vectors.json` | 12 canonical conformance vectors (Key Fingerprint + Canonical JSON) | `sdk/conformance_vectors.json` |
| `sdk/python/` | Python SDK — ATF receipt construction, OEP generation, verification | `sdk/python/` |
| `sdk/node/` | Node.js SDK — Canonical JSON, key fingerprint, conformance check | `sdk/node/` |
| Python SDK packages | `pypqc>=0.0.7.1`, `oqspy` | PyPI |

**CLI verifier usage:**

```bash
pip install pypqc
python omnix_atf_verify.py \
  --package path/to/OMNIX-OEP-{package_id}.zip \
  --public-key path/to/platform_public_key.b64
```

Expected output: `VERIFIED`, `SIGNATURE_INVALID`, `CHAIN_BROKEN`, `MANIFEST_INCOMPLETE`, or `INCOMPLETE` (PQC check deferred to server).

---

## Platform Key Registry

The OMNIX platform signing key is published through three independent channels. Verifiers should confirm key fingerprint through at least two channels before trusting any verification result.

| Channel | Location | Format |
|---|---|---|
| HTTP API | `GET /api/forensic/platform-key` | JSON — fingerprint, algorithm, key_size_bytes |
| DNS TXT | `_omnix-platform-key.omnixquantum.net` | `v=OMNIX1;fp=SHA256:{fingerprint};alg=ML-DSA-65` |
| Zenodo Registry | DOI: 10.5281/zenodo.19056919 | Embedded in production dataset metadata |

Algorithm: ML-DSA-65 (Dilithium-3) · NIST FIPS 204 · NIST Level 3  
Key size: 1952 bytes (public) / 4032 bytes (secret)  
Fingerprint algorithm: SHA-256 over raw public key bytes → hex → lowercase

---

## Regulatory Alignment

| Regulation | Alignment | ATF Component |
|---|---|---|
| EU AI Act Art. 14 | Human oversight — signed delegation chain with budget ceiling | DR chain (ATF-INV-001/003) |
| EU AI Act Art. 17 | Quality management — continuous session legitimacy | RCR/CES (RGC-INV-001–008) |
| EU AI Act Art. 11 | Technical documentation — offline-verifiable evidence | OEP (OEP-INV-001–006) |
| NIST AI RMF Govern | Accountable AI — PQC-signed audit chain | Full ATF stack |
| NIST AI RMF Map | Risk contextualization — CES degradation monitoring | CES/RCR (RFC-ATF-2) |
| eIDAS 2.0 / ARF | Verifiable credentials — ML-DSA-65 signed receipts | TAR + DR (RFC-ATF-1) |
| Basel III / BCBS 239 | Data lineage — immutable evidence archive | EAP/COLD (RFC-ATF-3) |
| GDPR Art. 22 | Explainable automated decisions — human delegation root | AIR + DR chain |
| DORA Art. 15 | ICT incident evidence — COLD block chain with HALT sealing | EAP + WIS (GECR-INV-004) |

---

## Priority Record

This document establishes the intellectual priority of the ATF protocol stack and its formal invariant system as of May 2026. The stack was designed, implemented, tested in production, and published by Harold Nunes, OMNIX QUANTUM LTD, Abu Dhabi UAE / London UK.

The formal invariant system (47 invariants, 9 families) is the subject of RFC-ATF-1, RFC-ATF-2, and RFC-ATF-3. All three are deposited on Zenodo (permanent DOI) and Figshare (permanent DOI), providing independent timestamped priority records.

**GOVERNANCE_BASELINE-2026-Q2-001** — Frozen architecture state as of May 2026:
- 47 formal invariants
- 171 ADRs
- 495+ passing tests
- 3 published RFCs (6 permanent DOIs)
- Production since November 2025

**Institutional Baseline Snapshot — May 18, 2026:**  
`docs/releases/ATF_ECOSYSTEM_BASELINE_2026-05.md` (OMNIX-ATF-BASELINE-2026-05) — frozen point-in-time snapshot for institutional review, regulatory reference, and academic citation.

**End-to-End Verification Walkthrough:**  
`docs/walkthroughs/OFFLINE_GOVERNANCE_VERIFICATION_WALKTHROUGH.md` (OMNIX-WALK-001) — 7-act forensic walkthrough from human delegation through offline verification. Based entirely on production module source code.

---

*This release document is canonical. It is referenced by `docs/ARCHITECTURE_INDEX.md`, `docs/whitepaper/OMNIX_TECHNICAL_WHITEPAPER.md`, and `docs/compliance/INVARIANT_TEST_MATRIX.md`.*  
*OMNIX QUANTUM LTD · May 2026 · OMNIX-ATF-RELEASE-3.3-2026-05*
