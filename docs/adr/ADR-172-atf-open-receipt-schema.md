# ADR-172: ATF Open Receipt Schema (ATORS)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Supersedes:** None  
**Extends:** ADR-171 (SGIP) · ADR-156 (DR) · ADR-157 (TAR) · ADR-158 (DTR) · ADR-159 (RCR)  
**Related:** ADR-161 (GPIL) · ADR-165 (OEP) · ADR-167 (Platform Key Fingerprint)  
**Implements:** `sdk/atf_open_receipt_schema.json` · `sdk/python/omnix_atf_verify.py`

---

## Context

### The Semantic Portability Problem

ADR-171 (SGIP) establishes four layers of ATF interoperability and identifies the critical gap between them: a receipt can be **cryptographically portable** (Layer 1 — the ML-DSA-65 signature is verifiable anywhere) while remaining **semantically opaque** to any system that does not run the OMNIX runtime.

This gap was articulated precisely by Antonio Socorro (cross-system technical review, May 2026):

> *"If the receipt only conserves its complete meaning within OMNIX, interoperability depends on the ecosystem. The hardest architectural problem is making that legitimacy portable without requiring all sovereign domains or external systems to run OMNIX themselves."*

> *"Can ATF receipts become portable governance artifacts, with OMNIX as one implementation, rather than the required runtime for interpretation?"*

And by Raheem Larry Babatunde (VeriSigil AI, May 2026), whose joint offline continuity artifact proposal frames the same problem from the cross-system verification direction:

> *"Can a joint offline continuity artifact exist such that ATF and VGS verifiers both independently accept the admissibility chain without requiring runtime-origin dependency during replay?"*

Both questions converge on the same structural gap: **the absence of an open, machine-readable, runtime-independent specification of what ATF receipt fields mean and how to verify them.**

### What Already Exists

**Cryptographic portability is solved.** ATF Delegation Receipts already embed the delegator's ML-DSA-65 public key. The `content_hash` algorithm (SHA-256 of canonical JSON) and the signature computation (`sign(content_hash.encode("utf-8"), secret_key)`) are fully specified by ADR-156 and validated by `sdk/conformance_vectors.json`. Any system with access to the public key can independently verify a DR's integrity without OMNIX.

**The gap is semantic, not cryptographic.** A verifier receiving an ATF receipt can confirm it was not tampered with — but cannot determine:
- What `task_scope` authorizes or prohibits operationally
- What `delegation_depth: 3` implies for authority trust
- Whether `admission_status: ADMITTED` satisfies their governance framework's admissibility definition
- How `ces_score: 72.4` translates to a governance action in their domain

The OMNIX codebase encodes these semantics implicitly in Python logic. The SGIP (ADR-171) formalizes the inter-runtime semantic alignment mechanism but does not define the base schema that any system needs to parse and interpret ATF receipts.

---

## Decision

### 1. ATF Open Receipt Schema (ATORS)

ADR-172 establishes the **ATF Open Receipt Schema (ATORS)** — a versioned, machine-readable, runtime-independent JSON Schema that:

1. **Defines the structural contract** for all ATF receipt types (DR, TAR, DTR, RCR, SAC, STR, SPV)
2. **Specifies the canonical JSON algorithm** for content hash computation (with enough precision for any language implementation)
3. **Documents invariants** per receipt type, referenced to the ADR that formally specifies them
4. **Enables semantic portability** — any system that consumes ATORS can parse, validate, and semantically interpret ATF receipts without OMNIX

**Location:** `sdk/atf_open_receipt_schema.json`  
**Schema version:** 1.0.0  
**JSON Schema dialect:** Draft-07

### 2. ATF Standalone Verifier (omnix_atf_verify.py)

A zero-dependency Python CLI that implements ATORS verification offline:

**Location:** `sdk/python/omnix_atf_verify.py`  
**Version:** 1.2.0

Verification layers implemented:
- **L1 — Structural check:** required fields present for each receipt type
- **L2 — Hash verification:** recomputes `content_hash` using the canonical algorithm and compares to stored value
- **L3 — Invariant check:** validates invariants (ATF-INV-001, TAR-INV-003, CDTP-INV-001, RGC-INV-004, SGIP-INV-002, etc.)
- **L4 — PQC signature:** optional ML-DSA-65 / Dilithium-3 verification (requires `oqs-python` or `pypqc`)
- **L5 — SAC alignment:** for SAC receipts, reports semantic alignment status per term

**Verification levels:**

| Level | Meaning |
|---|---|
| `FULL` | Hash valid + PQC sig valid + invariants pass |
| `HASH_ONLY` | Hash valid, PQC library not available or no public key provided |
| `FAILED` | Hash invalid — tampering detected |

**Critical design rule (Architect review, May 2026):** `fully_verified: true` is NEVER set unless PQC signature verification was actually performed and succeeded. `HASH_ONLY` verification detects field tampering but does not authenticate the issuer. The output makes this distinction explicit.

### 3. Canonical JSON Algorithm — Normative Specification

The following is the normative specification for `content_hash` computation in all ATF receipts:

```python
import hashlib
import json

def compute_content_hash(receipt: dict, exclude_fields: set) -> str:
    clean = {k: v for k, v in receipt.items() if k not in exclude_fields}
    canonical = json.dumps(
        clean,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False   # Unicode preserved as-is, not \uXXXX escaped
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()

EXCLUDE_FIELDS = {
    "content_hash", "pqc_signature", "pqc_algorithm",
    "pqc_signature_a", "pqc_signature_b", "sac_content_hash", "spv_hash"
}
```

**For SAC:** the hash input is `{parties: {...}, semantic_alignment_map: {...}}` (not the full SAC dict).  
**For SPV:** the hash input is `atf_core_term_set` only.  
**PQC signatures:** computed over `content_hash.encode("utf-8")` — the hex string, not the raw SHA-256 bytes.

This algorithm is validated by `sdk/conformance_vectors.json` (FVP-INV-007, ATF-INV-006).

### 4. Receipt Types and Identifier Prefixes

| Receipt Type | ID Prefix | ADR | Hash Field | Public Key Embedded |
|---|---|---|---|---|
| DR — Delegation Receipt | `ATFDR-{16HEX}` | ADR-156 | `content_hash` | Yes (`delegator_public_key`) |
| TAR — Temporal Admissibility Record | `ATFTAR-{16HEX}` | ADR-157 | `content_hash` | No |
| DTR — Domain Translation Receipt | `ATFDTR-{16HEX}` | ADR-158 | `content_hash` | No |
| RCR — Runtime Continuity Record | `ATFRCR-{16HEX}` | ADR-159 | `content_hash` | No |
| SAC — Semantic Alignment Certificate | `OMNIX-SAC-{16HEX}` | ADR-171 | `sac_content_hash` | No |
| STR — Semantic Term Registry Entry | `STR-{runtime}-{term}-{16HEX}` | ADR-171 | `content_hash` | No |
| SPV — Semantic Policy Vector | `OMNIX-SPV-{runtime}-{date}-{16HEX}` | ADR-171 | `spv_hash` | No |

**Portable key note:** Only DR embeds the issuer public key. For TAR, DTR, RCR verification, the verifier must supply `--public-key` or access the platform's published public key.

### 5. ATORS as a Semantic Bridge for Cross-System Interoperability

ATORS directly answers Antonio Socorro's framing: it is the semantic layer that makes ATF receipts interpretable without OMNIX. When combined with SGIP (ADR-171):

```
Layer 1 — Cryptographic portability   [ADR-156 + ATORS §3 canonical algorithm]
  Any verifier with the public key can confirm receipt integrity.

Layer 2 — Schema portability           [ATORS — this ADR]
  Any verifier that has consumed ATORS knows what each field means,
  what invariants apply, and how to interpret the governance verdict.

Layer 3 — Policy alignment             [ADR-161 GPIL / CRGC]
  Two runtimes agree on numerical policy parameters.

Layer 4 — Semantic alignment           [ADR-171 SGIP / SAC]
  Two runtimes declare and bilaterally sign their operational definitions
  of the 8 ATF Core Terms.
```

ATORS is Layer 2 — the schema portability layer. Without it, Layers 3 and 4 are underspecified for external systems.

### 6. Raheem Larry Babatunde's Joint Artifact Question

Raheem's "joint offline continuity artifact" (CDPR-ATF-VGS-001 in his formulation) maps to the following ATORS implementation:

An ATF Delegation Receipt (DR) already satisfies 7 of his 8 proposed boundary receipt fields:

| Raheem's field | ATF equivalent | ATORS location |
|---|---|---|
| `source_runtime` | `delegator_id` / `chain_root_id` | DR schema |
| `destination_runtime` | `delegate_id` + DTR `target_domain` | DR + DTR schema |
| `delegated_scope` | `task_scope` | DR schema |
| `removed_scope` | Computed: `originating_scope - task_scope` | Derivable from DR chain |
| `continuity_hash` | `content_hash` + `parent_delegation_id` chain | DR schema |
| `jurisdiction_hash` | DTR `target_domain` + SAC `runtime_b.spv_hash` | DTR + SAC schema |
| `revocation_state` | DR `status` (ACTIVE/REVOKED) | DR schema |
| `temporal_proof` | TAR `pqc_signature` over `execution_ns` | TAR schema |

The "joint artifact" is a DR + TAR + SAC bundle, exported as an OEP (ADR-165). ATORS provides the schema that both the ATF verifier and a VGS verifier can independently consume.

---

## Implementation

### Files Produced

| File | Description |
|---|---|
| `sdk/atf_open_receipt_schema.json` | Open JSON Schema v1.0.0 — all ATF receipt types |
| `sdk/python/omnix_atf_verify.py` | Standalone verifier CLI v1.2.0 |
| `omnix_core/agents/atf/semantic_governance.py` | SGIP engine (STR + SPV + SAC) — ADR-171 implementation |

### Verifier Usage

```bash
# Verify a Delegation Receipt (hash + invariants, no PQC)
python sdk/python/omnix_atf_verify.py --receipt dr.json

# Verify with PQC signature (requires oqs-python or pypqc)
python sdk/python/omnix_atf_verify.py --receipt dr.json --public-key pub.b64

# Verify a TAR (type required — no prefix autodetect for all types)
python sdk/python/omnix_atf_verify.py --receipt tar.json --type TAR --public-key pub.b64

# Verify a SAC — reports semantic alignment layer
python sdk/python/omnix_atf_verify.py --receipt sac.json --type SAC

# CI/CD mode — exit code 1 if not fully_verified
python sdk/python/omnix_atf_verify.py --receipt dr.json --public-key pub.b64 --exit-code
```

### SGIP Engine Usage

```python
from omnix_core.agents.atf.semantic_governance import SemanticGovernanceEngine

engine = SemanticGovernanceEngine(runtime_id="RUNTIME-UAE-OMNIXQUANTUM-20260520")
engine.ensure_tables()

# Publish a term definition
authority_entry = engine.publish_term(
    term_id="AUTHORITY",
    definition={
        "formal_statement": (
            "Authority is the cryptographically attested right to direct "
            "agent execution within a defined task_scope, issued by a human "
            "Tier-1 operator and propagated via Delegation Receipts with "
            "monotonically reducing budget (ATF-INV-001)."
        ),
        "regulatory_anchors": ["ADGM-AI-GOVERNANCE-FRAMEWORK-S4", "FIPS-204"],
        "boundary_conditions": [
            "Budget granted must never exceed delegator budget",
            "Authority expires with the DR's expires_at field",
        ],
        "out_of_scope": ["Implicit authority from role membership alone"],
    },
    operational_scope={
        "domains": ["TRADING", "DEFENSE", "MEDICAL_AI"],
        "jurisdictions": ["UAE", "UK"],
    }
)

# Generate SPV (after publishing all 8 core terms)
spv = engine.generate_spv()
print(spv.coverage_report())  # {"complete": True, "coverage_pct": 100.0, ...}
```

---

## Consequences

### Positive

- **Semantic portability achieved:** Any system that consumes ATORS can parse, validate, and semantically interpret ATF receipts without the OMNIX runtime. OMNIX is one implementation of the ATF schema, not the required interpreter.
- **Cross-system verification enabled:** The standalone verifier provides the concrete artifact Raheem's cross-system replay scenario requires — offline receipt verification without platform dependency.
- **Priority record:** ATORS v1.0.0 is the first open schema specification for post-quantum governance receipts with multi-layer invariant traceability. Deposited May 2026.
- **Institutional procurement:** An evaluating institution can independently validate any ATF receipt bundle using only `omnix_atf_verify.py` and the published public key — zero platform access required during due diligence.
- **RFC-ATF-4 foundation:** ATORS provides the normative base schema for the planned RFC-ATF-4 publication (Semantic Governance Interoperability Protocol).

### Neutral

- ATORS is additive — existing ATF receipts are already ATORS-compliant (the schema documents their existing structure).
- `omnix_atf_verify.py` has zero OMNIX imports and can be distributed independently.

### Negative

- PQC signature verification in the standalone verifier requires `oqs-python` or `pypqc`. Hash-only verification is always available but cannot authenticate the issuer.
- TAR, DTR, and RCR do not embed the issuer public key — external verifiers must supply it separately. This is a known limitation documented clearly in the verifier output.

---

## Open Items

| ID | Description | Priority |
|---|---|---|
| ATORS-OI-001 | Align RCR signing in `runtime_continuity.py` to use canonical JSON with `ensure_ascii=False` and correct provider interface (identified by architect review) | HIGH |
| ATORS-OI-002 | Publish OMNIX signing public key at well-known URL for external verifiers | MEDIUM |
| ATORS-OI-003 | OEP bundle extension: include ATORS schema reference in OEP `META/manifest.json` | MEDIUM |
| ATORS-OI-004 | RFC-ATF-4 draft: ATORS + SGIP as normative Layer 2 + Layer 4 specification | LOW |

---

## References

- ADR-156 — Agent Trust Fabric (Delegation Receipt)
- ADR-157 — Temporal Authority Admissibility (TAR)
- ADR-158 — Cross-Domain Trust Portability (DTR)
- ADR-159 — Runtime Governance Continuity (RCR)
- ADR-161 — Governance Policy Interoperability Layer (GPIL / CRGC)
- ADR-165 — OMNIX Evidence Package (OEP)
- ADR-167 — Platform Key Fingerprint (FVP-INV-007)
- ADR-171 — Semantic Governance Interoperability Protocol (SGIP)
- `sdk/conformance_vectors.json` — Cross-language hash parity vectors (FVP-INV-007)
- RFC-ATF-1 — DOI: 10.5281/zenodo.20155016
- RFC-ATF-2 — DOI: 10.5281/zenodo.20241344
- RFC-ATF-3 — DOI: 10.5281/zenodo.20247342
