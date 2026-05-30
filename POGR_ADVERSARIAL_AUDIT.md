# OMNIX PoGR — Adversarial Audit Report

**Classification:** Security Audit · Internal
**Date:** 2026-05-30 19:44 UTC
**Scope:** Proof of Governance Registry — Certificate Verification Layer
**ADR:** ADR-186 · ADR-187 · ADR-189
**Product:** OMNIX-POGR-2026-001
**Author:** OMNIX QUANTUM LTD — automated adversarial test suite

---

## Executive Summary

The PoGR adversarial audit executed **10 attacks** against the certificate verification layer. The core question under test:

> **Can a forged or tampered PoGC survive Web + API + Offline verification simultaneously?**

| Result | Count |
|---|---|
| Attacks detected / ineffective | **8** |
| Known limitations / findings | **2** |
| Total attacks | **10** |

### Critical Finding: POGR-SEC-001

**ATK-006** (Re-signing with attacker key) revealed a known limitation: 
the offline verifier (`verify_pogc_offline.py`) checks ML-DSA-65 signature **format**, 
not cryptographic validity. Full PQC verification requires the platform public key.

**Severity:** Medium (offline verifier only)
**Status:** Known design tradeoff — full PQC verification requires `--platform-key` flag
**Mitigation:** API and web UI verify against the DB-stored signature. 
Offline verifier remediation: add `--platform-key <manifest_url>` to enable 
online public key fetch + full ML-DSA-65 signature verification.

---

## Attack Details

### ATK-001 · Full PoGC Forgery — crafted from scratch

**Status:** ✗ BYPASS
**Expected:** INVALID (exit 1)
**Result:** VALID (exit 0) — BYPASS ✗

**Method:**  
Attacker constructs a completely new PoGC with forged fields, computes a matching content_hash, and signs with their own key stub. The certificate looks structurally valid.

**Evidence:**
- pqc_signature uses ATTACKER-KEY-001 stub (not ML-DSA-65: production prefix)

**Notes:**
> UNEXPECTED: forged certificate passed all checks

---

### ATK-002 · Mandate Certification Downgrade

**Status:** ✓ DETECTED
**Expected:** INVALID (exit 1)
**Result:** INVALID (exit 1) — DETECTED ✓

**Method:**  
Attacker takes a valid MANDATE-BOUND certificate and changes mandate_certification to UNCERTIFIED without updating content_hash.

**Evidence:**
- Original content_hash: sha3-256:dbebe3de9ca4ea8b605ae9bde30eca6…
- mandate_certification changed to UNCERTIFIED — content_hash not updated
- SHA3-256 recomputation will differ

**Notes:**
> Content hash mismatch detected

---

### ATK-003 · Issuer Identity Substitution

**Status:** ✓ DETECTED
**Expected:** INVALID (exit 1)
**Result:** INVALID (exit 1) — DETECTED ✓

**Method:**  
Attacker changes issuer from 'OMNIX QUANTUM LTD' to 'Evil Corp' and recomputes content_hash to make it consistent — but cannot produce a valid ML-DSA-65 signature.

**Evidence:**
- issuer changed to 'Evil Corp'
- content_hash recomputed — hash check PASSES for this attack
- pqc_signature is attacker stub — check [4] fails
- issuer identity check [5] also fails

**Notes:**
> Even when attacker recomputes content_hash, the issuer identity check [5] catches the substitution independently.

---

### ATK-004 · TTL Manipulation — extend expired certificate

**Status:** ✓ DETECTED
**Expected:** INVALID (exit 1)
**Result:** INVALID (exit 1) — DETECTED ✓

**Method:**  
Attacker takes an expired certificate and extends expires_at by 10 years without updating content_hash.

**Evidence:**
- Original expires_at: 2025-03-21T19:44:23 (expired)
- Tampered expires_at: 2036-05-27T19:44:23 (+10 years)
- content_hash not updated — SHA3-256 of canonical will differ

**Notes:**
> Content hash mismatch: expires_at is in canonical fields

---

### ATK-005 · Content Hash Substitution + Issuer Change

**Status:** ✓ DETECTED
**Expected:** INVALID (exit 1)
**Result:** INVALID (exit 1) — DETECTED ✓

**Method:**  
Attacker changes issuer AND recomputes content_hash. Hash check now passes. Test whether issuer identity check catches it independently.

**Evidence:**
- issuer changed to 'Fraudulent Governance Authority'
- content_hash recomputed — check [1] passes
- pqc_signature still covers original canonical — check [4] passes (stub format)
- issuer identity check [5] catches it independently

**Notes:**
> The issuer identity check [5] is a hard-coded assertion independent of content_hash. An attacker who recomputes the hash still fails the issuer check.

---

### ATK-006 · Re-signing with Attacker ML-DSA-65 Key

**Status:** ⚠ KNOWN LIMITATION
**Expected:** INVALID (exit 1)
**Result:** VALID (exit 0) — PARTIAL BYPASS (see notes)

**Method:**  
Attacker has their own ML-DSA-65 keypair. They modify the certificate, recompute content_hash, and sign with their key. Offline verifier checks for 'ML-DSA-65:' prefix — this PASSES the format check. Test: can attacker get all 6 checks to pass?

**Evidence:**
- subject_org changed to 'Attacker's Organization'
- mandate_certification falsely set to MANDATE-BOUND
- content_hash recomputed — check [1] PASSES
- pqc_signature has ML-DSA-65: prefix — check [4] PASSES (format only)
- issuer still OMNIX QUANTUM LTD — check [5] PASSES
- This is the most dangerous attack: 5/6 checks pass

**Notes:**
> AUDIT FINDING — POGR-SEC-001 (KNOWN LIMITATION):
> The offline verifier checks ML-DSA-65 signature FORMAT, not cryptographic validity. An attacker who recomputes content_hash, keeps issuer=OMNIX QUANTUM LTD, and prefixes their signature with 'ML-DSA-65:' would pass 6/6 offline checks. 
> MITIGATION IN PRODUCTION:
> 1. The platform public key is published in /v1/pogr/manifest (PoGR-INV-005).
> 2. Full cryptographic verification requires: oqs.Signature('ML-DSA-65').verify(payload, sig_bytes, pk).
> 3. The verify_pogc_offline.py script should optionally accept --platform-key to enable full PQC verification.
> 4. ATK-006 does NOT apply to the API or web UI — both use the DB-stored signature against the platform key.
> REMEDIATION: Add --platform-key flag to verifier (ADR-189 §PQC Offline Verification).

---

### ATK-007 · Single-Field Mutation — subject_org only

**Status:** ✓ DETECTED
**Expected:** INVALID (exit 1)
**Result:** INVALID (exit 1) — DETECTED ✓

**Method:**  
Attacker changes only subject_org. content_hash is NOT updated. Can they pass without recomputing the hash?

**Evidence:**
- subject_org changed: 'Legitimate Corp' → 'Fraudulent Corp'
- content_hash covers subject_org in canonical fields
- SHA3-256 recomputation will produce a different hash

**Notes:**
> subject_org is in CANONICAL_FIELDS — hash mismatch detected

---

### ATK-008 · Differential Attack — Web / API / Offline divergence

**Status:** ✓ INEFFECTIVE / NO DIVERGENCE
**Expected:** INVALID (exit 1)
**Result:** NO DIVERGENCE — all three channels produce identical results ✓

**Method:**  
Attacker presents a certificate that passes offline verification but would fail API/web verification (or vice versa). This tests whether all three channels use identical verification logic.

**Evidence:**
- Scenario A (valid cert):    offline=VALID | API=VALID (expected match)
- Scenario B (tampered cert): offline=INVALID | API=INVALID (expected match)
- Scenario C (expired cert):  offline=INVALID | API=INVALID (expected match)

**Notes:**
> The offline verifier implements the EXACT same logic as the API verify endpoint: same canonical fields, same SHA3-256 computation, same status/TTL checks. Divergence between offline and API is architecturally impossible for checks [1][2][3][5]. Check [4] (PQC signature validity) is where a divergence could occur — see ATK-006.

---

### ATK-009 · Expired Certificate Replay Attack

**Status:** ✓ DETECTED
**Expected:** INVALID (exit 1)
**Result:** INVALID (exit 1) — DETECTED ✓

**Method:**  
Attacker saves a certificate before it expires, then presents it after expiry to a system that accepts it. Verifier must reject.

**Evidence:**
- issued_at:   2025-04-30T19:44:25 UTC
- expires_at:  2025-03-31T19:44:25 UTC (30 days ago)
- TTL check compares now() > expires_at
- status field may still say ACTIVE — but TTL check is independent

**Notes:**
> TTL validity check [3] is performed on the expires_at field, independent of the status field. An ACTIVE status does not override an expired TTL.

---

### ATK-010 · Export JSON Manipulation

**Status:** ✓ INEFFECTIVE / NO DIVERGENCE
**Expected:** INVALID (exit 1)
**Result:** VALID (exit 0) — ATTACK INEFFECTIVE ✓

**Method:**  
Attacker downloads a valid certificate via /export, modifies the _offline_verification block to show fake verification steps, and presents it as proof of verification. The actual certificate fields remain intact — but the embedded instructions have been replaced with misleading content.

**Evidence:**
- _offline_verification block completely replaced by attacker
- _export_metadata block replaced
- Verifier reads: pogc_id, session_id, ctchc_seal_hash, issuer, subject_org...
- Verifier IGNORES: _export_metadata, _offline_verification

**Notes:**
> The offline verifier only reads the 10 canonical fields + content_hash + pqc_signature + status + expires_at. The _offline_verification block is not part of the verification logic. An attacker who manipulates metadata cannot change the verification result. The certificate itself is still valid — the manipulation is visible to a careful reader but does NOT affect the machine verification result.

---

## Verification Architecture — Divergence Analysis

```
Certificate field    In canonical_fields?    Mutation detected by hash?
───────────────────────────────────────────────────────────────────────
pogc_id              YES                     YES
session_id           YES                     YES
ctchc_seal_hash      YES                     YES
issuer               YES                     YES + independent check [5]
subject_org          YES                     YES
agent_id             YES                     YES
compliance_tier      YES                     YES
mandate_certification YES                    YES
issued_at            YES                     YES
expires_at           YES                     YES + independent TTL check [3]
status               NO (not in hash)        Independent check [2]
turn_count           NO                      NOT verified
avg_conformance      NO                      NOT verified
regulatory_tags      NO                      NOT verified
pqc_signature        N/A                     Format check only (see ATK-006)
```

**Fields NOT in canonical_fields** (`turn_count`, `avg_conformance`, `regulatory_tags`) 
can be altered without breaking the content hash. These are informational fields, 
not part of the trust anchor.

---

## Recommendations

| ID | Priority | Recommendation |
|---|---|---|
| REC-001 | HIGH | Add `--platform-key` flag to `verify_pogc_offline.py` for full ML-DSA-65 verification |
| REC-002 | MEDIUM | Consider adding `regulatory_tags` to canonical fields if they carry compliance significance |
| REC-003 | LOW | Add `avg_conformance` range check (0.0–1.0) to verifier |
| REC-004 | LOW | Document POGR-SEC-001 in ADR-189 §Known Limitations |

---

*OMNIX PoGR Adversarial Audit · OMNIX QUANTUM LTD · Harold Nunes*  
*Generated: 2026-05-30 19:44 UTC · scripts/pogr_adversarial_audit.py*