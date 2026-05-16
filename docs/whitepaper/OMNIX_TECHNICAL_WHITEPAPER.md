# OMNIX QUANTUM — Technical Whitepaper

**Runtime Legitimacy Infrastructure for Autonomous Decision Systems**

**Version:** 1.1 · **Date:** May 2026
**Author:** Harold Nunes — OMNIX QUANTUM LTD
**Jurisdiction:** United Arab Emirates / United Kingdom
**Contact:** omnixquantum.net

---

## Abstract

OMNIX QUANTUM is a decision governance infrastructure for autonomous agents and AI systems. It establishes a verifiable, auditable chain of authority from a human operator to every autonomous decision, using post-quantum cryptography (ML-DSA-65, FIPS 204), formal protocol invariants, and an immutable evidence archive pipeline.

The core claim: any governance decision made by any OMNIX-governed agent can be independently verified — offline, without platform access, by any third party with the platform's public key — at any point in the future, even after the original system has been decommissioned.

This whitepaper describes the technical architecture, the formal invariant system, the cryptographic proof layer, and the deployment model.

---

## Table of Contents

1. [The Runtime Legitimacy Problem](#1-the-runtime-legitimacy-problem)
2. [Architecture Overview](#2-architecture-overview)
3. [Agent Trust Fabric (ATF)](#3-agent-trust-fabric-atf)
4. [Continuity Eligibility Score (CES)](#4-continuity-eligibility-score-ces)
5. [Governance Policy Interoperability Layer (GPIL)](#5-governance-policy-interoperability-layer-gpil)
6. [Post-Quantum Cryptography](#6-post-quantum-cryptography)
7. [Immutable Evidence Archive Pipeline](#7-immutable-evidence-archive-pipeline)
8. [OMNIX Evidence Package (OEP)](#8-omnix-evidence-package-oep)
9. [Formal Invariant System (40 Invariants)](#9-formal-invariant-system-40-invariants)
10. [Verification Architecture](#10-verification-architecture)
11. [Regulatory Alignment](#11-regulatory-alignment)
12. [Deployment Model](#12-deployment-model)
13. [Verification Claims](#13-verification-claims)
14. [Glossary](#14-glossary)

---

## 1. The Runtime Legitimacy Problem

Modern AI and autonomous agent systems generate decisions at machine speed. These decisions may have regulatory, financial, or safety consequences. The current state of the art fails in three critical ways:

**Problem A — Opaque delegation.** When an autonomous agent makes a decision, there is typically no signed, auditable record linking that agent's authority to a human principal. Who authorized this agent? What scope were they given? When did that authorization expire?

**Problem B — No runtime continuity guarantee.** Autonomous sessions degrade over time — temporal windows close, authority budgets are consumed, context drifts. There is no formal mechanism to detect when a runtime session has become illegitimate before the next decision executes.

**Problem C — Evidence evaporation.** Decision evidence typically exists only in live databases. After system migration, decommissioning, or a security incident, the ability to independently verify past decisions is permanently lost. There is no cryptographic chain of custody.

OMNIX solves all three: explicit signed delegation (ATF), session legitimacy scoring (CES), and immutable evidence archive (EAP). Every component is formally specified, invariant-governed, and post-quantum hardened.

**Verifiable test coverage:** 334+ passing tests across the institutional audit suites (GPIL, OEP, EAP, AI Fallback) confirm every stated claim as of May 2026 — see Section 13.

---

## 2. Architecture Overview

OMNIX organizes governance into six layers, each extending the one below without replacing it:

```
L5 ─ Immutable Evidence          COLD Archive · OEP Bundles · Forensic Verification
L4 ─ Execution Gate              Governance Receipt · AVM Approval · ATF Compliance check
L3 ─ Runtime Continuity          RCR · CES Scoring · Halt Protocol
L2 ─ Temporal Admissibility      TAR · Session Bounds · TTL Enforcement
L1 ─ Delegation                  DR · Scope Assignment · MAR Enforcement
L0 ─ Human Authority Root        Agent Identity Receipt (AIR) · Root Issuance
```

**Authority propagates downward.** A human operator at L0 issues an identity to an agent. That agent receives a delegation (L1) with a bounded authority budget. The delegation is time-bounded (L2). During execution, the session is continuously scored (L3). Each decision passes an approval gate (L4). Every artifact is archived immutably (L5).

**Evidence flows upward.** Every artifact at every layer carries an ML-DSA-65 signature over a deterministic canonical hash. A third party can reconstruct and verify the complete chain from L5 backwards to L0 without any platform access.

### Component Map

| Layer | Component | ADR | RFC |
|---|---|---|---|
| L0 | Agent Identity Receipt (AIR) | ADR-156 | RFC-ATF-1 §2 |
| L1 | Delegation Receipt (DR) | ADR-156 | RFC-ATF-1 §3 |
| L2 | Temporal Admissibility Record (TAR) | ADR-157 | RFC-ATF-1 §4 |
| L3 | Runtime Continuity Record (RCR) | ADR-159 | RFC-ATF-2 §6 |
| L3 | RCR Performance Optimization (RPOL) | ADR-160 | RFC-ATF-2 §7 |
| L3 | Cross-Domain Trust Bridge | ADR-158 | RFC-ATF-1 §5 |
| L4 | Governance Receipt (RC) | ADR-028 | — |
| L4 | Adaptive Veto Machine (AVM) | ADR-074 | — |
| L4 | Execution Integrity Layer | ADR-131 | — |
| L5 | Evidence Archive Pipeline | ADR-163 | — |
| L5 | OMNIX Evidence Package (OEP) | ADR-165 | — |
| All | Forensic Verification Portal | ADR-164 | — |
| All | Platform Key Registry | ADR-167 | — |

---

## 3. Agent Trust Fabric (ATF)

The Agent Trust Fabric is the formal delegation and identity layer. It was first specified in RFC-ATF-1 (published May 2026) and extended with the runtime continuity protocol in RFC-ATF-2.

### 3.1 Agent Identity Receipt (AIR)

Every agent operating under OMNIX governance must have an Agent Identity Receipt — a PQC-signed document that establishes:

- `agent_id`: canonical identifier (format: `AGT-{jurisdiction}-{date}-{hex}`)
- `tier`: authority tier (TIER-1 Human, TIER-2 Autonomous, TIER-3 Subordinate)
- `issued_by`: the principal that issued this identity
- `pqc_public_key`: the agent's ML-DSA-65 public key
- `content_hash`: SHA-256 of the canonical JSON representation
- `pqc_signature`: ML-DSA-65 signature by the issuer

### 3.2 Delegation Receipt (DR)

When authority is delegated from one principal to another, a Delegation Receipt is produced. The DR is the primary mechanism for satisfying the EU AI Act Article 14 requirement for human oversight — every delegation in the chain is signed and auditable.

**Monotonic Authority Reduction (ATF-INV-001):** The authority budget granted in a DR can never exceed the authority budget of the delegator. Authority only ever decreases through the chain.

```
human_principal   →  authority_budget = 1.0  (root)
  agent_tier2     →  authority_budget = 0.75 (granted ≤ 1.0)
    agent_tier3   →  authority_budget = 0.45 (granted ≤ 0.75)
```

### 3.3 Temporal Admissibility Record (TAR)

Every decision session is bounded by a Temporal Admissibility Record. The TAR enforces:

- `valid_from` / `valid_until`: hard temporal bounds — no decision executes outside this window
- `ttl_seconds`: must not exceed `RC_TTL_CRITICAL_DEFAULT` (3600s by protocol)
- Time-bounded session prevents decision replay across different market or operational states

### 3.4 Cross-Domain Trust Portability (ADR-158)

Delegation receipts may cross jurisdictional or organizational boundaries via signed Cross-Domain Trust Bridge records. These establish that an agent identity from Runtime A is recognized by Runtime B, with explicit scope limitations. The bridge itself is PQC-signed and carries the policy alignment record.

---

## 4. Continuity Eligibility Score (CES)

The Continuity Eligibility Score is a continuous session legitimacy metric, formally defined in RFC-ATF-2 §6. It is computed at every governance decision point and recorded in the Runtime Continuity Record (RCR).

### 4.1 Formula

```
CES = Temporal × 0.30 + Budget × 0.30 + Context × 0.20 + Integrity × 0.20
```

All four components are in [0, 100]. CES is therefore in [0, 100].

**Weights are protocol invariants** — no runtime configuration may change them.

### 4.2 Component Definitions

| Component | Measures | Degrades When |
|---|---|---|
| **Temporal** | Fraction of TAR window remaining | Time passes; window closes |
| **Budget** | Fraction of authority budget remaining | Decisions consume budget |
| **Context** | Alignment with original decision context | Market/state drift accumulates |
| **Integrity** | Receipt hash coverage, signature validity | Hash mismatches, PQC failures |

### 4.3 Operational Stages

| Stage | CES Threshold | Operational Effect |
|---|---|---|
| NOMINAL | ≥ 75.0 | Standard operation |
| MONITORING | ≥ 50.0 | Elevated logging, threshold alerts |
| WARNING | ≥ 25.0 | Reduced-confidence decisions, AVM alerts |
| CRITICAL | ≥ 10.0 | Single-decision authorization only |
| HALT | < 10.0 | **RGC-INV-003**: All decisions blocked. Emergency seal. |

### 4.4 HALT Protocol (RGC-INV-003)

When CES reaches 0 (HALT), the Runtime Governance Continuity engine:
1. Blocks all new decision execution immediately
2. Triggers emergency sealing of all pending evidence to COLD tier (EAP integration)
3. Emits a Continuity Escalation event
4. Requires explicit operator reauthorization to resume

This is not a soft warning — it is a protocol halt. The integration between the HALT trigger and the Evidence Archive Pipeline ensures that evidence cannot be tampered with post-incident, because the emergency seal happens before any operator can access the system.

---

## 5. Governance Policy Interoperability Layer (GPIL)

The GPIL (ADR-161, RFC-ATF-2 §21) is the formal specification for cross-runtime governance compatibility. It resolves the following observation:

> Two sovereign runtimes could validate the same ML-DSA-65 signed ATF receipt successfully and still reach different governance conclusions.

This is not a defect. It is an intended property of the sovereign runtime model.

### 5.1 Three Interoperability Layers

**Layer 1 — Cryptographic Interoperability (CI)**
Binary: a receipt either passes ML-DSA-65 signature verification or it does not. This is unconditional. Any party with the platform public key can verify any receipt. Defined by RFC-ATF-2 §5.4 and ATF-INV-006.

**Layer 2 — Protocol Interoperability (PI)**
All ATF-RGC-Compliant runtimes share the same CES formula, threshold definitions, and invariant table. A runtime that changes the CES formula is not ATF-RGC-Compliant.

**Layer 3 — Governance Policy Interoperability (GPI)**
Sovereign runtimes may configure policy parameters within protocol-defined bounds. Two runtimes that are both PI-compliant may reach different governance verdicts for the same receipt.

### 5.2 Policy Parameter Registry

ADR-161 §21.3 defines exactly **6 Policy Divergence Surface parameters** — the complete set of dimensions along which two PI-compliant runtimes may legitimately reach different governance verdicts. Every `CRGCPolicyParameters` instance carries all 6 fields; values outside protocol bounds are rejected at construction time (GPIL-INV-001).

| Parameter | Type | Min | Max | Default | Effect |
|---|---|---|---|---|---|
| `afg_fragmentation_limit` | float | 0.01 | 0.95 | 0.90 | Authority fragmentation ceiling (ATF-INV-005) |
| `rc_ttl_seconds` | int | 30 | 3600 | 300 | Session temporal bound (RGC-INV-001) |
| `sampling_profile` | enum | — | — | `MEDIUM` | CES sampling cadence: SHORT / MEDIUM / LONG / STREAMING |
| `governance_risk_tier_policy` | enum | — | — | `STANDARD` | Risk tier governing approval thresholds: LOW / STANDARD / HIGH / CRITICAL |
| `context_drift_methodology_ref` | string URI | — | — | protocol default | Reference to the context drift detection specification in use |
| `anomaly_criteria_ref` | string | — | — | protocol default | Reference to the anomaly detection criteria specification |

The first two parameters are numeric with validated bounds. The remaining four are categorical or reference types. All 6 are included in the CRGC hash computation for bilateral agreement integrity.

### 5.3 Cross-Runtime Governance Contracts (CRGC)

Two runtimes that need to make consistent multi-party decisions can establish a CRGC — a PQC-signed agreement on their shared Layer 3 policy parameters. The CRGC is bilaterally signed and time-bounded. It enables deterministic cross-runtime verdicts without requiring runtimes to abandon their sovereign policy configurations.

---

## 6. Post-Quantum Cryptography

OMNIX uses ML-DSA-65 (Module-Lattice-Based Digital Signature Algorithm, FIPS 204) throughout the governance stack. This algorithm was standardized by NIST in August 2024.

### 6.1 Why Post-Quantum Now

Governance evidence is intended to remain verifiable for decades — during legal proceedings, regulatory inquiries, and historical audits. A classical ECDSA or RSA signature produced today may become forgeable within the 10–15 year horizon of quantum computing progress ("harvest now, decrypt later" threat model).

ML-DSA-65 (Dilithium-3) provides:
- Security level equivalent to AES-192 against quantum adversaries
- NIST FIPS 204 standardization (August 2024)
- 3293-byte signature size (compact for a post-quantum scheme)
- Deterministic signing (no randomness vulnerabilities)

### 6.2 Key Architecture

Every signing operation in OMNIX uses:
- **Algorithm:** ML-DSA-65 (FIPS 204) — also known as Dilithium-3
- **Message:** The `canonical_hash` of the artifact (SHA-256 with `sha256:` prefix)
- **Key type:** ML-DSA-65 keypair — 1312-byte public key, 2528-byte secret key

The platform signing key is:
- Generated once per deployment and stored in `OMNIX_SIGNING_SECRET_KEY_B64` (Railway secret)
- The corresponding public key (`OMNIX_SIGNING_PUBLIC_KEY_B64`) is published at:
  - `/api/forensic/platform-key` (HTTP)
  - `_omnix-key.omnixquantum.net` (DNS TXT)
  - Zenodo DOI: https://doi.org/10.5281/zenodo.20155016 (permanent academic archive)

### 6.3 Key Fingerprint

The platform key is identified by its SHA-256 fingerprint over the raw public key bytes:

```
fingerprint = "sha256:" + sha256(base64_decode(OMNIX_SIGNING_PUBLIC_KEY_B64)).hexdigest()
```

This fingerprint is embedded in every OEP bundle (in `KEYS/public_key.b64`) and in every receipt that OMNIX issues. External verifiers can check the fingerprint against the DNS TXT record or Zenodo publication without making any API call.

### 6.4 Key Rotation

Key rotation follows a formal lifecycle (documented in `docs/security/KEY_ROTATION_RUNBOOK.md`):

```
ACTIVE → ROTATION SCHEDULED → DUAL ACTIVE (30-day overlap) → RETIRED / REVOKED
```

The overlap period ensures all in-flight verification operations against the old key continue to work. Emergency revocation (e.g., key compromise) bypasses the overlap and produces a REVOKED status with a public notification event.

---

## 7. Immutable Evidence Archive Pipeline

The Evidence Archive Pipeline (ADR-163) moves governance artifacts through a three-tier lifecycle, ensuring offline reconstructability at every stage.

### 7.0 Evidence Lifecycle & Retention (ADR-160, ADR-162)

The Evidence Lifecycle & Retention specification (ADR-162) defines the formal retention policy governing all governance artifacts. It works in conjunction with the RCR Performance Optimization layer (ADR-160), which provides write-queue batching and event-driven sampling to reduce database pressure without compromising the integrity of the evidence record.

ADR-160 introduces the `RCRWriteQueue`, `EventDrivenSampler`, and `RCRScheduler` — components that ensure CES snapshots are written efficiently under high decision throughput, while the `GovernanceRiskTier` system ensures that high-risk decisions always produce a full synchronous evidence write regardless of batching configuration.

ADR-162 establishes four Evidence Lifecycle & Retention invariants (ELR-INV-001–004): retention schedules may not be shortened post-issuance; immutable classes bypass all compression; WARM-tier compression preserves the original `content_hash`; and the COLD-tier seal is irreversible.

### 7.1 Evidence Classes

| Class | Retention | Notes |
|---|---|---|
| LEGAL | Indefinite HOT | Never moves to WARM |
| PQC | Indefinite HOT | Never moves to WARM |
| CONTRACT | Indefinite HOT | Never moves to WARM |
| EXCEPTION | Indefinite HOT | Never moves to WARM |
| TELEMETRY | HOT 90d → WARM 365d → COLD | Compressed in WARM |
| SAMPLE | HOT 90d → WARM 365d → COLD | Compressed in WARM |
| SHADOW_NOMINAL | Reduced at HOT | Payload-stripped for nominal events |
| OPS | HOT 90d → WARM 365d → COLD | Standard pipeline |

### 7.2 Pipeline Stages

**Stage 1 — HOT (0–90 days)**
Direct storage in PostgreSQL. No transformation. Full payload available for real-time verification. Indefinite retention for immutable classes.

**Stage 2 — WARM (90–365 days)**
Compression of TELEMETRY, SAMPLE, and OPS artifacts into hourly aggregates. The original `content_hash` is recorded in the `warm_archive_manifest` before payload stripping, preserving the ability to verify the hash chain even after payload loss.

**Stage 3 — COLD (365+ days)**
Final sealing into object storage (S3/Parquet). Each batch of artifacts is sealed into an immutable COLD block:

```json
{
  "block_id": "OMNIX-BLOCK-20260514-000001",
  "creation_timestamp_ns": 1715692800000000000,
  "artifact_count": 1247,
  "evidence_classes": ["LEGAL", "PQC", "CONTRACT"],
  "canonical_hash": "sha256:a3f7c2b9...",
  "predecessor_block_hash": "0000...0000",
  "integrity_manifest": {
    "artifact_hashes": ["sha256:...", "..."],
    "merkle_root": "sha256:b8e2d4f6...",
    "hash_algorithm": "sha256-v1"
  },
  "pqc_signature": "ML-DSA-65 signature (3293 bytes, base64)",
  "pqc_algorithm": "ML-DSA-65 (FIPS 204)",
  "omnix_version": "1.0.0"
}
```

### 7.3 Block Hash Chain

Each block's `canonical_hash` covers:
- `block_id`, `creation_timestamp_ns`, `artifact_count`, `evidence_classes`
- `hash_algorithm`, `merkle_root`, `omnix_version`, `predecessor_block_hash`

The `predecessor_block_hash` field creates a tamper-evident hash chain. Any modification to any block in the chain breaks all subsequent blocks' predecessor links — detectable by any verifier.

The genesis block uses `predecessor_block_hash = "0" × 64`.

### 7.4 Pipeline Triggers

| Trigger | Frequency | Condition |
|---|---|---|
| Scheduled HOT→WARM | Daily | Age ≥ 90 days |
| Scheduled WARM→COLD | Weekly | Age ≥ 365 days |
| Emergency HALT | Immediate | RGC-INV-003 triggered |
| Admin | On-demand | Explicit operator command |

The emergency HALT trigger is the most critical: when a governance session reaches CES=0 and the HALT protocol fires, all evidence associated with that session is sealed immediately, before any operator intervention. This prevents post-incident evidence tampering.

### 7.5 Custody Log

Every artifact sealed into a COLD block generates a `CustodyLogEntry` that records:
- `artifact_id`, `block_id`, `sealed_at`
- `tier_transition` (HOT→COLD, WARM→COLD)
- `content_hash` (final hash at time of sealing)
- `block_canonical_hash` (the block that contains this artifact)

The custody log provides an auditable trail from any artifact back to its COLD block and from any COLD block to all its artifacts.

---

## 8. OMNIX Evidence Package (OEP)

An OMNIX Evidence Package (.oep) is a self-contained ZIP archive that allows a third party to independently verify a complete governance evidence chain without any OMNIX platform access.

### 8.1 Package Structure

```
OMNIX-EVIDENCE-{date}-{id}.oep  (ZIP)
├── BLOCKS/
│   ├── OMNIX-BLOCK-20260514-000001.json
│   ├── OMNIX-BLOCK-20260514-000002.json
│   ├── ...
│   └── chain_index.json
├── KEYS/
│   └── public_key.b64              ← Platform public key (ML-DSA-65)
├── VERIFY/
│   ├── omnix_atf_verify.py         ← Standalone verifier script
│   └── verify_all.sh               ← Shell verification script
├── CUSTODY/
│   └── custody_log.jsonl           ← Artifact custody records
├── REPORT/
│   └── forensic_report.json        ← Chain completeness score, verdict
├── META/
│   └── manifest.json               ← sha256 for every file (OEP-INV-002)
└── SIGNATURE/
    └── package_signature.json      ← ML-DSA-65 over canonical_manifest_hash
```

### 8.2 Two-Phase Signature Protocol

The package signature resolves a chicken-and-egg problem: the signature file itself cannot be hashed before it is created.

**Phase 1:** Collect all content files. Compute sha256 for each.
**Phase 2:** Build `content_manifest` from all file hashes — excluding the signature file.
**Phase 3:** `canonical_manifest_hash = sha256(json.dumps(content_manifest, sort_keys=True, compact))`
**Phase 4:** Sign `canonical_manifest_hash` with ML-DSA-65. Write `package_signature.json`.
**Phase 5:** Write final ZIP with all content + manifest + signature.

**Auditor verification:**
```python
manifest = json.loads(zip.read("META/manifest.json"))
# Strip signature entry from manifest before rehashing
manifest_for_hash = {k: v for k, v in manifest.items()
                     if k not in ("package_signature_hash",)}
canonical_json = json.dumps(manifest_for_hash, sort_keys=True, separators=(",", ":"))
computed_hash = "sha256:" + sha256(canonical_json.encode()).hexdigest()
# Compare against package_signature.json.canonical_manifest_hash
# Then verify ML-DSA-65 signature of canonical_manifest_hash
```

### 8.3 Trust Level Classification

When verifying an OEP, the trust level depends on the signing key:

| Trust Level | Condition | Meaning |
|---|---|---|
| **OMNIX_PLATFORM** | `sha256(KEYS/public_key.b64)` matches platform key registry | Signed by OMNIX QUANTUM LTD |
| **EXTERNAL** | Fingerprint does not match platform registry | Signed by third-party key |

EXTERNAL is not a failure — it means the evidence was signed by a key other than the official platform key. The cryptographic integrity of the chain may still be PASS under EXTERNAL; the trust level merely indicates the institutional provenance of the signing authority.

---

## 9. Formal Invariant System (40 Invariants)

OMNIX governs its behaviour through 40 formally specified invariants across 8 categories. These invariants are not configuration parameters — they are structural properties that every OMNIX-compliant implementation must satisfy. Breaking any invariant constitutes a protocol violation, not a policy choice.

### ATF Invariants — RFC-ATF-1 (6 invariants)

| ID | Statement |
|---|---|
| ATF-INV-001 | Authority budget granted ≤ authority budget of delegator (Monotonic Authority Reduction) |
| ATF-INV-002 | Every delegation receipt carries a PQC signature by the delegator |
| ATF-INV-003 | Delegation scope is a strict subset of delegator scope |
| ATF-INV-004 | Delegation depth is finite and bounded by the ATF stack configuration |
| ATF-INV-005 | Temporal bounds of a delegation cannot exceed the delegator's temporal bounds |
| ATF-INV-006 | All ATF artifacts are independently verifiable offline without platform access |

### RGC Invariants — RFC-ATF-2 (8 invariants)

| ID | Statement |
|---|---|
| RGC-INV-001 | CES is computed as T×0.3 + B×0.3 + C×0.2 + I×0.2, bounded [0, 100] |
| RGC-INV-002 | CES thresholds: NOMINAL≥75, MONITORING≥50, WARNING≥25, CRITICAL≥10, HALT=0 |
| RGC-INV-003 | When CES reaches HALT: all decision execution blocked; emergency archive seal triggered |
| RGC-INV-004 | Every governance decision produces a receipt; no decision executes without a receipt path |
| RGC-INV-005 | Runtime continuity records are PQC-signed at creation; signatures are immutable |
| RGC-INV-006 | AFG fragmentation limit: default 0.90, configurable [0.50, 0.95], never >1.0 |
| RGC-INV-007 | CES components are independently auditable from the RCR payload |
| RGC-INV-008 | HALT escalation events are written to the continuity escalations table and archived |

### EAP Invariants — Evidence Archive Pipeline (7 invariants)

| ID | Statement |
|---|---|
| EAP-INV-001 | Every archived artifact retains its original `content_hash` through all tier transitions |
| EAP-INV-002 | Every COLD block carries an ML-DSA-65 signature over its `canonical_hash` |
| EAP-INV-003 | Each block's `predecessor_block_hash` must equal the `canonical_hash` of the immediately preceding block |
| EAP-INV-004 | Immutable evidence classes (LEGAL, PQC, CONTRACT, EXCEPTION) never transition to WARM |
| EAP-INV-005 | The complete evidence chain is reconstructable and verifiable offline without platform access |
| EAP-INV-006 | Every sealed artifact generates a custody log entry before the sealing operation completes |
| EAP-INV-007 | Blocks are append-only; no block may be modified after sealing |

### FVP Invariants — RFC-ATF-3 (1 invariant)

| ID | Statement |
|---|---|
| FVP-INV-007 | The platform public key fingerprint is publicly accessible without authentication |

**FVP architectural separation principles** (FVP-INV-001–006 — not counted in formal total): Plane 1 emits only PASS/INTEGRITY_VIOLATION; Plane 2 is the authoritative PQC path; hash verification is deterministic; SIGNATURE_INVALID is Plane 2 exclusive; same cryptographic library used for signing and verification; Plane 2 verdict is always authoritative.

### GPIL Invariants — Governance Policy Interoperability Layer (3 invariants)

| ID | Statement |
|---|---|
| GPIL-INV-001 | All CRGC policy parameters must remain within validated bounds; out-of-range values are rejected before enforcement, never silently clamped |
| GPIL-INV-002 | Every policy-affecting governance event produces a CRGC receipt before the policy change takes effect |
| GPIL-INV-003 | The GPIL taxonomy must cover all governance event types defined in the ATF and RGC protocol stacks |

### ELR Invariants — Evidence Lifecycle & Retention (4 invariants)

| ID | Statement |
|---|---|
| ELR-INV-001 | Retention schedules may not be shortened post-issuance |
| ELR-INV-002 | Immutable evidence classes (LEGAL, PQC, CONTRACT, EXCEPTION) bypass all compression |
| ELR-INV-003 | WARM-tier compression preserves the original `content_hash` |
| ELR-INV-004 | The COLD-tier seal is irreversible |

### OEP Invariants — Evidence Package (6 invariants)

| ID | Statement |
|---|---|
| OEP-INV-001 | Every OEP bundle includes the standalone verifier script (omnix_atf_verify.py) |
| OEP-INV-002 | Every content file in the bundle has a sha256 hash in META/manifest.json |
| OEP-INV-003 | Package signature is required; OEP generation fails if signing key is absent |
| OEP-INV-004 | Chain completeness is verified before OEP generation; incomplete chains are rejected |
| OEP-INV-005 | The platform public key is embedded in KEYS/ of every OEP bundle |
| OEP-INV-006 | Package schema version is locked to `oep-1.0` |

### FEA Invariants — Forensic Export Authorization (5 invariants)

| ID | Statement |
|---|---|
| FEA-INV-001 | The platform key fingerprint endpoint returns deterministic results for the same key |
| FEA-INV-002 | When the platform key is not configured, the endpoint returns `configured: false`, never an error |
| FEA-INV-003 | The OEP export endpoint requires RBAC role = admin; non-admin requests are rejected |
| FEA-INV-004 | If no valid signing key is available, the export endpoint returns 503 (fail-closed) |
| FEA-INV-005 | Caller-provided signing keys are rejected unless `FORENSIC_EXPORT_ALLOW_CALLER_KEYS=true` (development only) |

---

## 10. Verification Architecture

OMNIX implements a three-plane verification architecture for forensic operations.

### Plane 1 — Browser (Preliminary)

Performed client-side in the OMNIX Forensic Verification Portal (`/archive-verify`). No server required after block data is loaded.

- Recomputes SHA-256 of each artifact hash
- Verifies Merkle root determinism
- Checks predecessor hash linkage
- **Cannot** verify ML-DSA-65 signatures (no PQC library in browser)
- Emits: `PASS` or `INTEGRITY_VIOLATION` only

### Plane 2 — Server (Authoritative)

Performed by the Flask API at `/api/forensic/verify`. Uses the same `pypqc` library that signed the blocks.

- All Plane 1 checks
- ML-DSA-65 signature verification (authoritative)
- PQC algorithm validation
- **Binding verdict** — overrides Plane 1 (FVP-INV-006)
- Emits: `PASS`, `INTEGRITY_VIOLATION`, `CHAIN_BREAK`, `SIGNATURE_INVALID`, `INCOMPLETE`

### Plane 3 — Offline (Independent, Platform-Free)

Performed by the standalone `omnix_atf_verify.py` script embedded in every OEP bundle.

- All Plane 2 checks
- No network connectivity required
- No OMNIX platform access required
- Satisfies ATF-INV-006 and EAP-INV-005
- Chain Completeness Score (CCS) computed: 0–100
- Verdicts: `COMPLETE`, `DEGRADED`, `PARTIAL`, `COMPROMISED`

### Verification Claims Matrix

| Property | Plane 1 | Plane 2 | Plane 3 |
|---|---|---|---|
| Hash integrity | ✓ | ✓ | ✓ |
| Merkle root | ✓ | ✓ | ✓ |
| Predecessor chain | ✓ | ✓ | ✓ |
| PQC signature | ✗ | ✓ | ✓ |
| Platform key match | ✗ | ✓ | ✓ |
| Binding verdict | ✗ | ✓ | ✓ |
| Platform-free | ✓ | ✗ | ✓ |

---

## 11. Regulatory Alignment

### EU AI Act (2024/1689)

| Requirement | OMNIX Mechanism |
|---|---|
| Art. 9 — Risk management systems | AVM + CES continuous scoring |
| Art. 14 — Human oversight | DR chain → every decision traceable to human principal |
| Art. 17 — Quality management | 38-invariant governance layer |
| Art. 19 — Automatically generated logs | Governance receipts + custody log |
| Art. 20 — Record-keeping | EAP immutable archive (365+ day COLD retention) |

### NIST AI Risk Management Framework (AI RMF 1.0)

| Function | OMNIX Mechanism |
|---|---|
| GOVERN — Policies | GPIL Policy Parameter Registry (ADR-161) |
| MAP — Risk identification | ATF delegation chain, CRGC cross-runtime mapping |
| MEASURE — Risk analysis | CES continuous scoring, AVM drift detection |
| MANAGE — Risk response | HALT protocol (RGC-INV-003), emergency archive seal |

### UAE Financial Services Regulatory Considerations

OMNIX is designed for UAE-based financial services operations under ADGM and DFSA framework considerations:
- Decision receipts provide the audit trail required under DFSA MKT and CIR rules
- PQC hardening addresses DFSA guidance on technology risk management
- Immutable evidence archive supports regulatory data retention requirements
- GPIL enables multi-jurisdiction operations without compromising sovereign runtime integrity

### eIDAS 2.0 / EU Digital Identity Architecture

The ATF delegation chain (DR hierarchy with PQC signatures) is architecturally compatible with eIDAS 2.0 trust anchors. The OMNIX platform key published at Zenodo and via DNS TXT constitutes a publicly verifiable trust anchor in the eIDAS sense.

---

## 12. Deployment Model

### Production Stack

| Component | Technology | Platform |
|---|---|---|
| Frontend SPA | React 18, Vite 7, TypeScript | Railway |
| API | Python 3.11, Flask | Railway |
| Database | PostgreSQL | Railway Managed |
| Cache / Anti-Replay | Redis | Railway Managed |
| PQC Library | pypqc (ML-DSA-65, Kyber-768) | Railway |
| Signing Keys | Railway Secrets | Never in code |

### Environment Variables (Critical)

| Variable | Purpose | Security Note |
|---|---|---|
| `OMNIX_SIGNING_SECRET_KEY_B64` | ML-DSA-65 private key | Never log; never expose |
| `OMNIX_SIGNING_PUBLIC_KEY_B64` | ML-DSA-65 public key | Public by design |
| `OMNIX_ANTI_REPLAY_MODE` | `strict` in production | `best_effort` allows replay |
| `AVM_FAIL_CLOSED` | `true` halts on DB failure | Never `false` in production |
| `FORENSIC_EXPORT_ALLOW_CALLER_KEYS` | Caller key bypass | NEVER `true` in production |

### Anti-Replay Architecture (ADR-131)

OMNIX implements a Redis-backed anti-replay layer for all decision receipts. Each receipt carries a unique `nonce`; the Redis store tracks seen nonces with a TTL matching the receipt's temporal validity. Replay attempts are detected and rejected.

In `OMNIX_ANTI_REPLAY_MODE=strict`, Redis unavailability causes the decision gate to fail-closed. In `best_effort`, the gate degrades gracefully — acceptable in development, unacceptable in production.

---

## 13. Verification Claims

### Institutional Audit Test Suite Coverage

Every structural claim in this whitepaper is backed by a passing test assertion. Third parties can reproduce these results:

```bash
# Full institutional audit suite (334 tests)
TESTING=true TELEGRAM_BOT_TOKEN=test-token python -m pytest \
  tests/test_gpil_audit.py \
  tests/test_oep_forensic_audit.py \
  tests/test_eap_extended_audit.py \
  tests/test_ai_fallback_observability.py \
  -v
# Expected: 329 passed, 5 skipped
```

| Test Suite | Tests | Coverage |
|---|---|---|
| `test_gpil_audit.py` | 187 pass, 1 skip | GPIL taxonomy · CRGC · 14 invariants · CES formula · Policy Bounds · ADR-161 |
| `test_oep_forensic_audit.py` | 74 pass | OEP bundle · two-phase signature · FEA-INV-001–005 · FVP-INV-006/007 · ADR-164–167 |
| `test_eap_extended_audit.py` | 45 pass, 4 skip | GPIL Policy Divergence Surface (6 params) · FVP two-plane separation · OEP offline self-containment · EAP chain integrity · ADR-161/163/165 |
| `test_ai_fallback_observability.py` | 15 pass | AI fallback chain log format (VII1–VII10) · Claude model name regression (VIII1–VIII5) · T000 spec |

**Key verifiable claims by test:**

| Claim | Test |
|---|---|
| CES formula = T×0.30+B×0.30+D×0.20+I×0.20 | `test_gpil_audit.py::TestInvariantTable::test_RGC_INV_001` |
| AFG max = 0.95 — hard limit | `test_gpil_audit.py::TestPolicyParameterBounds` |
| HALT propagates to all sibling sessions | `test_runtime_governance_continuity.py::TestHALTProtocol` |
| Policy Divergence Surface has exactly 6 parameters | `test_eap_extended_audit.py::TestGPILPolicyParameterRegistry::test_I10` |
| SIGNATURE_INVALID only from server (Plane 2) | `test_eap_extended_audit.py::TestFVPINV006ServerVerdictBinding::test_III4` |
| FORENSIC_EXPORT_ALLOW_CALLER_KEYS default = false | `test_eap_extended_audit.py::TestFEAINV003RBACExportGate::test_IV3` |
| OEP schema_version = "oep-1.0" | `test_eap_extended_audit.py::TestOEPInvariantsExtended::test_V1` |
| Chain predecessor hash linkage (EAP-INV-003) | `test_eap_extended_audit.py::TestEAPPipelineInvariantsExtended::test_VI3` |
| Genesis block predecessor = 64 zeros | `test_eap_extended_audit.py::TestEAPPipelineInvariantsExtended::test_VI8` |
| CRGC hash is deterministic (no timestamp drift) | `test_gpil_audit.py::TestCRGCFormat::test_crgc_hash_stability` |
| 14 invariants in total (ATF×6 + RGC×8) | `test_gpil_audit.py::TestDocumentationCoherence::test_invariant_count_is_14` |
| PQC algorithm constant = ML-DSA-65 / FIPS 204 | `test_eap_extended_audit.py::TestEAPPipelineInvariantsExtended::test_VI2` |

### The following claims are independently verifiable by third parties:

**Claim 1: Every governance decision is receipt-backed.**
Verify: query the `decision_receipts` table for any decision output. Every row has `content_hash` (SHA-256) and `pqc_signature` (ML-DSA-65).
ADR reference: ADR-028, RGC-INV-004.

**Claim 2: The delegation chain from any agent to a human principal is auditable.**
Verify: traverse the `atf_delegations` table from any `agent_id` upward, verifying each DR signature.
ADR reference: ADR-156, ATF-INV-001–005.

**Claim 3: The platform public key can be verified without HTTP access.**
Verify: `dig TXT _omnix-key.omnixquantum.net` returns the SHA-256 fingerprint matching `/api/forensic/platform-key`.
ADR reference: ADR-167, FVP-INV-007.

**Claim 4: Any COLD archive block can be verified offline.**
Verify: obtain any `.oep` bundle. Run `python VERIFY/omnix_atf_verify.py --archive-block BLOCKS/*.json`. No network, no account required.
ADR reference: ADR-163, EAP-INV-005, OEP-INV-001.

**Claim 5: Tampering with any block in the archive chain is detectable.**
Verify: modify any field in any `BLOCKS/*.json`. Rerun the verifier. The canonical_hash mismatch will produce `INTEGRITY_VIOLATION`. Any downstream block will produce `CHAIN_BREAK`.
ADR reference: ADR-163, EAP-INV-003.

**Claim 6: No autonomous decision can be made outside a temporal session bound.**
Verify: inspect any `atf_temporal_records` row. The `valid_until` timestamp is embedded in the TAR receipt and PQC-signed. Post-expiry decision attempts produce a TAR rejection event.
ADR reference: ADR-157, ATF-INV-005.

**Claim 7: Runtime degradation is auditable — no session legitimacy is assumed.**
Verify: inspect any `atf_runtime_continuity` row. The `ces_score` field shows the exact CES at decision time, with all four component values. The formula is deterministic and independently reproducible.
ADR reference: ADR-159, RGC-INV-001.

---

## 14. Glossary

| Term | Definition |
|---|---|
| **AFG** | Authority Fragmentation Guard — rejects delegation chains where budget fragmentation exceeds AFG_FRAGMENTATION_LIMIT |
| **AIR** | Agent Identity Receipt — the root identity artifact for an agent |
| **ATF** | Agent Trust Fabric — the complete delegation and identity layer (ADR-156–160) |
| **ATF-RGC-Compliant** | An implementation that satisfies all 14 protocol invariants (ATF-INV-001–006, RGC-INV-001–008) |
| **ATF-GPI-Aligned** | ATF-RGC-Compliant + GPIL CRGC negotiation capability (ADR-161) |
| **AVM** | Adaptive Veto Machine — drift-based approval gate (ADR-074/120) |
| **CCS** | Chain Completeness Score — OEP-level integrity metric (0–100) |
| **CES** | Continuity Eligibility Score — session legitimacy metric (RFC-ATF-2 §6) |
| **COLD** | Archive tier 3 — immutable sealed blocks in object storage (ADR-163) |
| **CRGC** | Cross-Runtime Governance Contract — bilateral PQC-signed policy alignment record |
| **DR** | Delegation Receipt — signed delegation artifact from one principal to another |
| **EAP** | Evidence Archive Pipeline — HOT→WARM→COLD lifecycle (ADR-163) |
| **FEA** | Forensic Export Authorization — RBAC + key resolution layer (ADR-166) |
| **FVP** | Forensic Verification Portal — three-plane verification architecture (ADR-164) |
| **GPIL** | Governance Policy Interoperability Layer — cross-runtime policy alignment (ADR-161) |
| **HOT** | Archive tier 1 — live PostgreSQL (ADR-163) |
| **MAR** | Monotonic Authority Reduction — ATF-INV-001 |
| **ML-DSA-65** | Module-Lattice-Based Digital Signature Algorithm, security level 3 (FIPS 204) — also known as Dilithium-3 |
| **OEP** | OMNIX Evidence Package — self-contained ZIP for offline verification (ADR-165) |
| **PQC** | Post-Quantum Cryptography |
| **RC** | Governance Receipt (Runtime Continuity receipt) |
| **RCR** | Runtime Continuity Record — CES snapshot at decision time |
| **RFC-ATF-1** | Published specification of the Agent Trust Fabric (L1–L4 delegation protocol) |
| **RFC-ATF-2** | Published specification of the Runtime Governance Continuity protocol |
| **RGC** | Runtime Governance Continuity — the session lifecycle protocol (ADR-159, RFC-ATF-2) |
| **TAR** | Temporal Admissibility Record — session temporal bound artifact |
| **WARM** | Archive tier 2 — compressed aggregate storage (ADR-163) |

---

*OMNIX QUANTUM LTD · Registered in England & Wales · Operational Headquarters: UAE*
*This document describes the technical architecture of the OMNIX governance platform.*
*All invariant numbers, ADR references, and cryptographic parameters are canonical.*
*Version 1.2 · May 2026 — Updated: invariant count corrected to 40 (GPIL-INV-001–003, ELR-INV-001–004 added), test count updated to 319, EAP Extended Audit suite (58 tests)*
