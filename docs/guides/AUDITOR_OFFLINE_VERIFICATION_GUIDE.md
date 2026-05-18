# How an External Auditor Verifies ATF Evidence Offline
## OMNIX QUANTUM LTD — Institutional Verification Guide

**Document ID:** OMNIX-GUIDE-AUDITOR-OFV-2026-05  
**Version:** 1.0  
**Date:** May 2026  
**Audience:** External auditors · Regulators · Institutional buyers · Legal counsel  
**Classification:** Public — no confidential information required  

---

## What This Document Is

This guide explains, step by step, how any external party can verify the integrity and authenticity of governance evidence produced by OMNIX — **without accessing the OMNIX platform, its database, its logs, or any internal system**.

The verification is cryptographic and deterministic. Given the same inputs, two independent verifiers will always reach the same conclusion. The platform cannot influence the result after evidence has been sealed.

**What you need:**
1. An OMNIX Evidence Package (OEP) — a `.zip` file delivered to you by the governed organization
2. The OMNIX platform public key — obtained independently (see §3)
3. Python 3.9+ with the `pypqc` library
4. Approximately 10 minutes

**What you do not need:**
- Network access during verification
- An account on the OMNIX platform
- Access to the organization's systems
- Trust in the organization providing the package

---

## Part 1 — What You Are Verifying

### 1.1 The Governance Chain

When OMNIX governs an autonomous agent decision, it produces a layered chain of signed receipts. Each receipt answers a specific legal and technical question:

| Receipt Type | Question Answered | Signed By |
|---|---|---|
| **Agent Identity Receipt (AIR)** | Who is this agent, and who created it? | Human operator (platform key) |
| **Delegation Receipt (DR)** | What authority did a human explicitly grant to this agent? | Delegating principal (platform key) |
| **Temporal Admissibility Record (TAR)** | Was the delegation valid at the **exact nanosecond** this decision began? | Platform (ML-DSA-65) |
| **Runtime Continuity Record (RCR)** | Did the agent's authorization remain valid **throughout** execution? | Platform (ML-DSA-65) |
| **Governance Receipt (ControlReceipt)** | Did the 11-checkpoint governance pipeline approve this decision? | Platform (ML-DSA-65) |
| **COLD Block** | Is all of the above archived immutably, in cryptographic sequence? | Platform (ML-DSA-65) |

Every single item in this chain is:
- **Signed** with ML-DSA-65 (CRYSTALS-Dilithium-3, NIST FIPS 204, Level 3)
- **Hash-chained** — each block's signature covers the hash of the previous block
- **Self-contained** — the verification key is embedded in the package you received

The OMNIX Evidence Package you have received contains all of this in a single ZIP file. Your job is to verify that the chain is intact and that the signatures are valid.

### 1.2 The Critical Legal Property

The fundamental legal property that distinguishes OMNIX receipts from conventional audit logs:

> An OMNIX governance receipt is not a record of a decision that was made. It is the authorization that made the decision possible. The sequence is: **receipt issued → action permitted**, not **action taken → receipt written**.

This means that if a valid receipt exists for a decision, that decision was governed before it executed. It is not possible to retrofit a receipt onto an ungoverned action without invalidating the cryptographic chain.

This property is formally specified as **GECR-INV-001 (Control-Receipt Atomicity)** in ADR-170.

---

## Part 2 — Package Contents

An OMNIX Evidence Package (OEP) is a ZIP file with the following structure:

```
OMNIX-OEP-{package_id}.zip
├── MANIFEST.json                          # Package metadata, block index, chain root
├── BLOCKS/
│   ├── block_0001.json                    # COLD block — GENESIS or first sealed block
│   ├── block_0002.json                    # COLD block — subsequent sealed block
│   └── ...                               # Additional blocks in sequence
├── KEYS/
│   └── public_key.b64                    # Platform ML-DSA-65 public key (base64)
├── SIGNATURE/
│   └── package_signature.json            # ML-DSA-65 signature over canonical MANIFEST hash
├── VERIFIER/
│   └── omnix_atf_verify.py               # Standalone Python verifier (zero external deps except pypqc)
└── README.txt                            # Human-readable verification instructions
```

### 2.1 MANIFEST.json — What to Inspect

```json
{
  "manifest_version": "oep-1.0",
  "package_id": "OEP-2026-05-09-A4F8C2D1",
  "issued_at": "2026-05-09T14:32:17.841Z",
  "issued_by": "OMNIX QUANTUM LTD",
  "chain_root_id": "ATFDR-D81296910B4F",
  "block_count": 4,
  "chain_index": [
    {
      "block_seq": 1,
      "block_id": "COLD-BLK-00001",
      "block_hash": "a7f3c2e1d8b94f...",
      "sealed_at": "2026-05-09T14:30:00.000Z"
    },
    {
      "block_seq": 2,
      "block_id": "COLD-BLK-00002",
      "block_hash": "b8d4e5f2c1a03e...",
      "predecessor_hash": "a7f3c2e1d8b94f...",
      "sealed_at": "2026-05-09T14:31:22.441Z"
    }
  ],
  "pqc_algorithm": "ML-DSA-65",
  "canonical_hash_algorithm": "sha256-v1"
}
```

**What to check:**
- `manifest_version` must be exactly `"oep-1.0"` — any other value indicates a non-compliant package
- `chain_index` — every block must have `predecessor_hash` equal to the `block_hash` of the prior block (except GENESIS)
- `block_count` must match the actual number of files in `BLOCKS/`
- `pqc_algorithm` must be `"ML-DSA-65"` — this is the only algorithm accepted in production

### 2.2 COLD Block Structure — What to Inspect

Each file in `BLOCKS/` is a sealed COLD block:

```json
{
  "block_id": "COLD-BLK-00002",
  "block_seq": 2,
  "sealed_at": "2026-05-09T14:31:22.441Z",
  "predecessor_block_hash": "a7f3c2e1d8b94f...",
  "block_content_hash": "c9e5f8a2d1b7c4...",
  "pqc_signature": "base64-encoded-ML-DSA-65-signature...",
  "pqc_algorithm": "ML-DSA-65",
  "evidence_class": "GOVERNANCE_RECEIPT",
  "receipts": [
    {
      "receipt_type": "DELEGATION_RECEIPT",
      "receipt_id": "ATFDR-08FB348A2D4F4E22",
      "content_hash": "e3b0c44298fc1c...",
      "pqc_signature": "base64...",
      "delegation_id": "ATFDR-08FB348A2D4F4E22",
      "delegator_id": "OPERATOR-99",
      "delegate_id": "AID-TRADING-4FC32A00",
      "authority_budget_delegator": 100.0,
      "authority_budget_granted": 85.5,
      "chain_root_id": "ATFDR-D81296910B4F",
      "expires_at": "2026-05-09T18:00:00Z",
      "status": "ACTIVE"
    },
    {
      "receipt_type": "TEMPORAL_ADMISSIBILITY_RECORD",
      "receipt_id": "ATFTAR-1BFCB97D4A21",
      "delegation_id": "ATFDR-08FB348A2D4F4E22",
      "execution_ns": 1715261537841000000,
      "execution_ts": "2026-05-09T14:32:17.841Z",
      "dr_status_at_admission": "ACTIVE",
      "admission_status": "ADMITTED",
      "authority_budget": 85.5,
      "domain": "TRADING",
      "task_action": "EXECUTE_SWAP",
      "content_hash": "f4a1c5b8e2d9f7...",
      "pqc_signature": "base64..."
    }
  ]
}
```

**Key fields to inspect as an auditor:**
- `predecessor_block_hash` — must match `block_content_hash` of prior block (chain integrity)
- `evidence_class` — must not have changed from original classification (ELR-INV-001)
- `pqc_signature` — ML-DSA-65 signature over the block's canonical JSON hash
- `admission_status` in each TAR — must be `"ADMITTED"` for governed decisions
- `authority_budget_granted ≤ authority_budget_delegator` — MAR invariant (ATF-INV-001)
- `expires_at` in DR — the TAR's `execution_ns` must fall within this window

---

## Part 3 — Obtaining the Platform Public Key Independently

The package includes the platform public key at `KEYS/public_key.b64`. However, an auditor should always verify this key against an independent source before trusting any verification result. The OMNIX platform publishes its public key through three independent channels:

### Channel 1 — HTTP API (machine-readable)

```bash
curl https://omnixquantum.net/api/forensic/platform-key
```

Response:
```json
{
  "status": "configured",
  "fingerprint": "SHA256:a3f8c2d1e9b4...",
  "fingerprint_short": "a3f8c2d1",
  "algorithm": "ML-DSA-65",
  "key_size_bytes": 1952,
  "configured": true
}
```

### Channel 2 — DNS TXT Record

```bash
dig TXT _omnix-platform-key.omnixquantum.net
```

Expected format: `"v=OMNIX1;fp=SHA256:{fingerprint};alg=ML-DSA-65"`

The DNS TXT record survives platform outages and cannot be modified by the platform without TTL propagation delay — it is an independent authority.

### Channel 3 — Zenodo Production Dataset

The platform public key fingerprint is embedded in the metadata of the production dataset deposited at Zenodo DOI `10.5281/zenodo.19056919`. Zenodo provides a permanent, independently timestamped reference that predates any subsequent platform configuration change.

**Cross-reference procedure:**  
Compute the SHA-256 fingerprint of `KEYS/public_key.b64` (after base64 decoding to raw bytes) and compare against all three channel outputs. All three must match. If any channel returns a different fingerprint, treat the package as unverified and request clarification from the issuing organization.

```python
import base64, hashlib

with open("KEYS/public_key.b64", "r") as f:
    raw_key = base64.b64decode(f.read().strip())
fingerprint = "SHA256:" + hashlib.sha256(raw_key).hexdigest()
print(fingerprint)
# Compare this value against all three channels
```

---

## Part 4 — Running the Verifier

### 4.1 Prerequisites

```bash
pip install pypqc>=0.0.7.1
# No other external dependencies required
```

`pypqc` is the Python binding to the reference implementation of CRYSTALS-Dilithium (NIST FIPS 204). It is available on PyPI and does not require OMNIX to be installed.

### 4.2 Basic Verification

```bash
python VERIFIER/omnix_atf_verify.py \
  --package OMNIX-OEP-{package_id}.zip \
  --public-key KEYS/public_key.b64
```

The verifier performs, in sequence:

1. **Manifest completeness** — All files referenced in `chain_index` are present in `BLOCKS/`. All required directories exist (KEYS, SIGNATURE, VERIFIER).
2. **Schema validation** — `manifest_version == "oep-1.0"`. Unknown versions are rejected.
3. **Chain integrity** — For each block (seq > 1): `block.predecessor_block_hash == hash(prev_block_content)`. Any broken link halts verification.
4. **Canonical hash recomputation** — For each block: recompute `block_content_hash` from the block's fields using the `sha256-v1` canonical JSON algorithm and compare against the recorded value.
5. **PQC signature verification** — For each block and for the package manifest: verify the ML-DSA-65 signature against the embedded public key. Requires `pypqc`.
6. **Package signature** — Verify `SIGNATURE/package_signature.json` signature against `MANIFEST.json` canonical hash.

### 4.3 Interpreting the Output

```
OMNIX ATF Verifier v1.1.0
Package: OMNIX-OEP-2026-05-09-A4F8C2D1.zip
Public Key Fingerprint: SHA256:a3f8c2d1e9b4...

[1/6] Manifest completeness............... PASS
[2/6] Schema validation................... PASS (manifest_version: oep-1.0)
[3/6] Chain integrity..................... PASS (4 blocks, chain intact)
[4/6] Canonical hash recomputation........ PASS (4/4 blocks match)
[5/6] PQC signature verification.......... PASS (4/4 blocks, algorithm: ML-DSA-65)
[6/6] Package signature................... PASS

RESULT: VERIFIED

Evidence Chain:
  GENESIS block:    COLD-BLK-00001 (2026-05-09T14:30:00Z)
  Latest block:     COLD-BLK-00004 (2026-05-09T14:35:44Z)
  Receipts archived: 7 (DR: 1, TAR: 1, RCR: 4, ControlReceipt: 1)
  Chain root ID:    ATFDR-D81296910B4F
```

**Possible outcomes:**

| Result | Meaning | Auditor Action |
|---|---|---|
| `VERIFIED` | All checks pass. Chain is intact, all signatures valid. | Accept evidence. |
| `SIGNATURE_INVALID` | ML-DSA-65 signature check failed on ≥1 block or package. | **Reject evidence.** The package has been tampered with or signed with a different key. Report to counterparty. |
| `CHAIN_BROKEN` | `predecessor_block_hash` mismatch between consecutive blocks. | **Reject evidence.** Blocks have been removed, inserted, or reordered. |
| `MANIFEST_INCOMPLETE` | Files listed in `chain_index` are missing from `BLOCKS/`. | **Reject evidence.** Package is incomplete — request a re-export. |
| `INCOMPLETE` | Structural checks pass but PQC library unavailable (pypqc not installed). | Install pypqc and re-run. Do not accept as VERIFIED without PQC check. |

### 4.4 Advanced: Verifying a Specific Receipt

To confirm that a specific decision is governed within the package:

```bash
python VERIFIER/omnix_atf_verify.py \
  --package OMNIX-OEP-{package_id}.zip \
  --public-key KEYS/public_key.b64 \
  --receipt-id ATFTAR-1BFCB97D4A21 \
  --verbose
```

The verifier will locate the TAR within its COLD block, verify the block's integrity, and output the full receipt fields:

```
Receipt: ATFTAR-1BFCB97D4A21
  Type:               TEMPORAL_ADMISSIBILITY_RECORD
  Block:              COLD-BLK-00002
  Agent:              AID-TRADING-4FC32A00
  Delegated by:       OPERATOR-99 (DR: ATFDR-08FB348A2D4F4E22)
  Execution time:     2026-05-09T14:32:17.841Z (UTC)
  Execution ns:       1715261537841000000
  DR status at t=0:   ACTIVE
  Admission status:   ADMITTED
  Authority budget:   85.5 / 100.0
  Domain:             TRADING
  Action:             EXECUTE_SWAP
  Chain root:         ATFDR-D81296910B4F
  Block signature:    VALID (ML-DSA-65)
  Content hash:       MATCH (sha256-v1)
```

---

## Part 5 — Reading the Receipt Chain as a Legal Narrative

For legal purposes, the receipt chain tells the following story:

### Human-to-Agent Authorization (DR)

> On [created_at], [delegator_id] explicitly authorized [delegate_id] to act within the scope [task_scope] with an authority budget of [authority_budget_granted], which was ≤ [authority_budget_delegator] held by the delegator at that time. This authorization expires at [expires_at] and cannot be extended without issuing a new signed receipt.

**Legal relevance:** This establishes that the agent was not self-authorized. Authority flowed from a human principal through a signed, immutable record. Under EU AI Act Article 14 (human oversight), this receipt constitutes the documented human control mechanism.

### Point-of-Admission Governance (TAR)

> At the exact nanosecond [execution_ns] (wall clock: [execution_ts]), the governance system evaluated whether the Delegation Receipt [delegation_id] was still valid. The DR status was [dr_status_at_admission]. The admission verdict was [admission_status].

**Legal relevance:** The TAR proves that the decision did not proceed during an expired or revoked authorization window. Unlike a database timestamp, the `execution_ns` field is captured *before* any pipeline evaluation — it is the admission timestamp, not the completion timestamp. It cannot be retrofitted.

### Continuous Session Legitimacy (RCR)

Each RCR in the chain represents a governance health snapshot during the execution session:

> At [timestamp], the Continuity Eligibility Score was [ces_score]/100 (Temporal: [ces_temporal], Budget: [ces_budget], Context: [ces_context], Integrity: [ces_integrity]). Session status: [continuity_status]. Budget remaining: [budget_remaining] / 100.

**Legal relevance:** The RCR chain proves that the agent's authorization was continuously monitored, not just checked at the start. If the session degraded (CES dropped), this is visible in the chain. If the session was halted (CES < 10), the HALT event is recorded with a signed RCR and the subsequent emergency COLD seal timestamp.

### Decision Governance (ControlReceipt)

> The governance pipeline evaluated [decision] through 11 sequential checkpoints. The verdict was [verdict] (APPROVED / QUARANTINE / BLOCKED). A signed ControlReceipt was issued at [timestamp] before the action was permitted to proceed.

**Legal relevance:** The ControlReceipt is the authorization, not the audit log. Under GECR-INV-001, this receipt was issued before the action executed. No receipt means the action was not governed.

---

## Part 6 — Common Auditor Questions

**Q: Can the organization alter the evidence after the fact?**  
A: No. Once a COLD block is sealed, its `block_content_hash` is computed and embedded in the `predecessor_block_hash` field of the next block. Any modification to a sealed block changes its hash, which invalidates every subsequent block's predecessor reference. The verifier detects this as `CHAIN_BROKEN`. Additionally, the ML-DSA-65 signature over the block's canonical hash would fail (`SIGNATURE_INVALID`). Both failures are detectable offline.

**Q: Can the platform re-sign a modified block with the same key?**  
A: Only if they hold the private key. The public key in the package must match the independently published key (see §3). If the platform replaced a tampered block and re-signed it, the fingerprint of the key used for re-signing would differ from the one published in DNS TXT and Zenodo — which you cross-check before verification. If the keys match but the content was altered, the original `content_hash` embedded in prior blocks will not match the recomputed hash of the altered block.

**Q: Can OMNIX selectively exclude unfavorable decisions from the package?**  
A: A package can be scoped to a specific chain root (`chain_root_id`) or time window. Within the scope, omitting blocks is detectable — the predecessor hash of block N+1 references block N, so a gap in the sequence produces `CHAIN_BROKEN`. However, an organization could in principle request a package that excludes certain sessions entirely by specifying a narrower scope. An auditor should always verify that the scope of the OEP matches the scope of the audit request.

**Q: What is the post-quantum security level?**  
A: ML-DSA-65 (CRYSTALS-Dilithium-3) is NIST FIPS 204, Security Level 3. It is designed to resist attacks by quantum computers running Grover's or Shor's algorithms. The key size is 1952 bytes (public) / 4032 bytes (secret). The signature size is 3293 bytes. NIST Level 3 provides security equivalent to AES-192 against classical and quantum adversaries.

**Q: What if I cannot install pypqc?**  
A: The verifier will still perform all structural checks (manifest, chain, canonical hashes) and report `INCOMPLETE` rather than `VERIFIED`. Structural checks alone confirm chain integrity. PQC verification confirms the signatures were produced by the holder of the private key. For regulatory-grade verification, both are required. A JavaScript reference implementation is also available at `sdk/node/conformance_check.ts` for environments where Python is not available.

**Q: Can I verify this without the verifier script?**  
A: Yes. The verification algorithm is fully specified in RFC-ATF-3 §8 (DOI: 10.5281/zenodo.20247342). You can implement your own verifier in any language that supports SHA-256 and ML-DSA-65. The canonical JSON serialization algorithm (`sha256-v1`) is specified in `sdk/conformance_vectors.json`, with 12 test vectors for cross-language conformance.

**Q: What does it mean if admission_status is REJECTED in a TAR?**  
A: It means the governance system evaluated the delegation at that nanosecond and determined it was not valid (expired, revoked, or outside scope). The action that triggered this evaluation should not have proceeded. If you find a ControlReceipt with `verdict: APPROVED` paired with a TAR showing `admission_status: REJECTED` in the same block, this indicates a potential integrity violation — contact OMNIX and the competent authority.

---

## Part 7 — Regulatory Verification Checklist

For regulatory examinations, the following checklist operationalizes the verification:

```
□ 1. OEP package received and hash noted (sha256sum OMNIX-OEP-*.zip)
□ 2. Platform public key fingerprint obtained from ≥2 independent channels
□ 3. Fingerprint in KEYS/public_key.b64 matches independent channels
□ 4. omnix_atf_verify.py executed — result: VERIFIED
□ 5. Chain root ID confirmed against engagement scope
□ 6. Block count and date range match audit period
□ 7. All DRs: authority_budget_granted ≤ authority_budget_delegator (ATF-INV-001)
□ 8. All TARs: execution_ns within DR valid_from / expires_at window
□ 9. All TARs: admission_status == "ADMITTED" for approved decisions
□ 10. All RCRs: continuity_status progression is monotonic or justified
□ 11. No HALT events without subsequent operator reauthorization record
□ 12. If cross-domain receipts (DTR) present: translated_budget ≤ source_authority_budget
□ 13. Evidence class unchanged through all tier transitions (ELR-INV-001)
□ 14. Package signature valid (SIGNATURE/package_signature.json)
```

All 14 checks can be completed offline with the provided package and verifier.

---

## Appendix A — ML-DSA-65 Algorithm Reference

| Property | Value |
|---|---|
| Standard | NIST FIPS 204 (ML-DSA) |
| Variant | ML-DSA-65 (Dilithium-3) |
| Security Level | NIST Level 3 (quantum-resistant) |
| Classical security | ≥ 128-bit |
| Quantum security | ≥ 128-bit (resists Grover / Shor) |
| Public key size | 1952 bytes |
| Private key size | 4032 bytes |
| Signature size | 3293 bytes |
| Hash over | Canonical SHA-256 of receipt fields (sorted JSON, no whitespace) |
| Reference impl | liboqs / pypqc / pqcrypto |

---

## Appendix B — Canonical JSON Specification (sha256-v1)

The canonical JSON algorithm used for all content hashes is `sha256-v1`:

1. Take the Python `dict` representation of the receipt (all fields)
2. Recursively sort all dictionary keys alphabetically
3. Serialize with `separators=(',', ':')` — no whitespace
4. Encode as UTF-8
5. Compute SHA-256
6. Encode as lowercase hex

This algorithm is language-agnostic. Cross-language conformance vectors are in `sdk/conformance_vectors.json`. Any verifier implementation must produce identical results for the 5 canonical JSON test vectors before it can be considered RFC-ATF-3 compliant.

---

*This document is part of the OMNIX QUANTUM institutional documentation suite.*  
*Cross-referenced by: `docs/releases/ATF_ECOSYSTEM_RELEASE_3.3.md` · `docs/whitepaper/OMNIX_TECHNICAL_WHITEPAPER.md` · RFC-ATF-3 (DOI: 10.5281/zenodo.20247342)*  
*OMNIX QUANTUM LTD · May 2026 · OMNIX-GUIDE-AUDITOR-OFV-2026-05*
