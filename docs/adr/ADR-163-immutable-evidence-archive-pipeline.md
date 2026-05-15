# ADR-163: Immutable Evidence Archive Pipeline

**Status:** Accepted  
**Date:** May 14, 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** None  
**Extends:** ADR-162 (Evidence Lifecycle & Immutable Retention)  
**Related:** ADR-028 (Decision Receipts) · ADR-131 (Execution Integrity) · ADR-156–161 (ATF Stack) ·
            RFC-ATF-1 §7.6 (ATF-INV-006) · RFC-ATF-2 §5 (RGC-INV-001–008)

---

## Context

ADR-162 established the Evidence Lifecycle & Immutable Retention policy: eight evidence classes,
three storage tiers (HOT/WARM/COLD), and four invariants (ELR-INV-001–004). It defined the
*what* — which artifacts belong to which tier and how long they are retained.

This ADR defines the *how*: the concrete pipeline that moves artifacts from HOT to WARM to COLD
while preserving, at every stage:

1. **Cryptographic verifiability** — `content_hash` must remain recomputable offline
2. **PQC signature integrity** — ML-DSA-65 signatures must remain verifiable without OMNIX runtime
3. **Chain linkability** — predecessor relationships in the DR → TAR → RCR chain must be restorable
4. **Evidence class integrity** — classification cannot degrade across tier transitions

Traditional archive systems optimize for cost and retrieval. OMNIX requires **evidentiary integrity
as a first-class constraint** — identical to how forensic evidence chains work in regulated
environments. An archive that cannot prove non-tampering is not an archive; it is a liability.

The distinction formalized here is:

> *Storage efficiency is a secondary concern. Offline reconstructability is a hard requirement.*

---

## Decision

### 1. Archive Pipeline Stages

The pipeline defines three sequential stages. Each stage has explicit admission criteria,
transformation rules, and integrity verification requirements.

#### Stage 1 — HOT (Active PostgreSQL)

**Duration:** 0–90 days (ELR classes LEGAL/PQC/CONTRACT/EXCEPTION: indefinite)  
**Storage:** Railway PostgreSQL  
**Indexes:** Full — all query patterns  
**Write path:** Direct from governance engine, RPOL write queue (ADR-160)  
**Integrity guarantee:** PostgreSQL ACID + WAL  

No transformation occurs in Stage 1. All artifacts are stored in their canonical form as emitted
by the governance engine.

#### Stage 2 — WARM (Compressed Aggregates)

**Duration:** 90–365 days from creation  
**Eligible classes:** `TELEMETRY`, `SAMPLE`, `SHADOW_NOMINAL`, `OPS`  
**Ineligible:** `LEGAL`, `PQC`, `CONTRACT`, `EXCEPTION` — these never leave HOT (or go directly
to COLD immutable archive)  

**Transformation rules:**
- TELEMETRY/SAMPLE → compressed into `rcr_hourly_aggregate` (defined in ADR-162 §5)
- SHADOW_NOMINAL → stripped to `{event_id, timestamp_ns, event_type, agent_id, content_hash,
  risk_score}` — full JSONB payload dropped
- Before any compression, the original `content_hash` is written to a **WARM manifest entry**
  alongside the compressed artifact's hash — enabling audit of the compression event itself

**WARM manifest entry schema:**
```sql
CREATE TABLE IF NOT EXISTS warm_archive_manifest (
    manifest_id         TEXT PRIMARY KEY,
    original_artifact_id TEXT NOT NULL,
    evidence_class      TEXT NOT NULL,
    original_hash       TEXT NOT NULL,       -- content_hash before compression
    compressed_hash     TEXT NOT NULL,       -- hash of compressed artifact
    compression_method  TEXT NOT NULL,       -- 'aggregate_hourly' | 'strip_nominal' | 'none'
    promoted_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    promoted_by         TEXT NOT NULL DEFAULT 'lifecycle_pipeline',
    integrity_verified  BOOLEAN NOT NULL DEFAULT FALSE
);
```

#### Stage 3 — COLD (Immutable Archive)

**Duration:** Permanent for immutable classes; 365+ days for compressible classes  
**Storage:** Object storage (S3-compatible) — append-only, versioning disabled, object lock enabled  
**Format:** Parquet segments with SHA-256 block manifests  

**COLD archive block structure:**
```json
{
  "block_id":               "OMNIX-BLOCK-{YYYYMMDD}-{sequence:06d}",
  "creation_timestamp_ns":  1747267200000000000,
  "artifact_count":         847,
  "evidence_classes":       ["LEGAL", "PQC", "CONTRACT", "EXCEPTION"],
  "canonical_hash":         "sha256:{hex}",
  "predecessor_block_hash": "sha256:{hex}",
  "integrity_manifest": {
    "artifact_hashes":      ["sha256:{hex}", "..."],
    "merkle_root":          "sha256:{hex}",
    "hash_algorithm":       "sha256-v1"
  },
  "pqc_signature":          "{ML-DSA-65 signature over canonical_hash}",
  "pqc_algorithm":          "ML-DSA-65 (FIPS 204)",
  "omnix_version":          "1.0.0"
}
```

**Block chaining invariant:** Each block's `predecessor_block_hash` references the previous block's
`canonical_hash`. The genesis block uses `"0000...0000"` (64 zeros). This creates an append-only
hash chain across all COLD archive blocks — tampering with any block breaks the chain.

### 2. Pipeline Invariants

**EAP-INV-001 — Verification Preservation:**  
Any artifact transitioned to WARM or COLD MUST have its original `content_hash` recorded in the
transition manifest before transformation. The hash must be recomputable from the original artifact
fields as defined in the issuing ADR.

**EAP-INV-002 — PQC Signature Preservation:**  
Any artifact bearing an ML-DSA-65 signature (pqc_signatures array) must have that signature array
preserved in COLD storage in its original form. Compression may reduce other fields; the signature
array is untouchable.

**EAP-INV-003 — Block Chain Integrity:**  
The `predecessor_block_hash` chain across all COLD blocks must be unbroken. Any gap in the chain
(missing predecessor) constitutes an integrity violation. The pipeline validator checks this before
any new block is sealed.

**EAP-INV-004 — Immutable Class Permanence:**  
Evidence class `LEGAL`, `PQC`, `CONTRACT`, and `EXCEPTION` artifacts must be sealed in COLD storage
in their complete canonical form — no field stripping, no payload reduction. The full artifact as
emitted by the governance engine must be preserved.

**EAP-INV-005 — Offline Reconstructability:**  
An auditor must be able, using only:
- a COLD archive block file
- the issuer's public Dilithium-3 key
- the `omnix_atf_verify.py` CLI (ADR-156)

to verify: block integrity, PQC signatures, predecessor chain, and artifact content hashes.
No OMNIX runtime, no database access, no API calls are permitted in this verification path.

**EAP-INV-006 — Manifest Completeness:**  
Every HOT→WARM and WARM→COLD transition must create a manifest entry. Transitions without a
manifest entry are invalid and must be rolled back.

### 3. Offline Verifier Extension

The existing `omnix_atf_verify.py` verifier (ADR-156) must be extended with a `--archive-block`
mode:

```bash
python omnix_atf_verify.py \
  --archive-block OMNIX-BLOCK-20260514-000001.parquet \
  --public-key omnix_public_key.pem \
  --verify-chain \
  --predecessor-block OMNIX-BLOCK-20260514-000000.parquet
```

**Verification steps (all offline):**
1. Load block manifest
2. Recompute `canonical_hash` from `integrity_manifest.merkle_root`
3. Verify ML-DSA-65 signature over `canonical_hash`
4. Verify `predecessor_block_hash` matches predecessor block's `canonical_hash`
5. For each artifact: recompute `content_hash` from artifact fields, verify against manifest
6. Emit verification report: PASS / INTEGRITY_VIOLATION / CHAIN_BREAK / SIGNATURE_INVALID

### 4. Pipeline Trigger Model

The archive pipeline runs as a scheduled background process, not in the request path:

| Trigger | Action |
|---|---|
| Daily at 02:00 UTC | HOT→WARM promotion for eligible artifacts > 90 days old |
| Weekly Sunday 03:00 UTC | WARM→COLD block sealing for artifacts > 365 days |
| On demand (admin) | Force-seal current WARM batch to COLD (emergency archival) |
| On governance halt | Immediate COLD seal of all EXCEPTION-class artifacts from the halted chain |

**"On governance halt" trigger** is the most critical: when RGC-INV-003 fires a HALT, all artifacts
from the halted chain root are immediately promoted to COLD tier — regardless of age — to prevent
any post-halt modification of the evidence trail.

### 5. Evidence Custody Log

Every pipeline transition creates an entry in a non-deletable custody log:

```sql
CREATE TABLE IF NOT EXISTS evidence_custody_log (
    custody_id          TEXT PRIMARY KEY,
    artifact_id         TEXT NOT NULL,
    evidence_class      TEXT NOT NULL,
    transition          TEXT NOT NULL,   -- 'HOT->WARM' | 'WARM->COLD' | 'EMERGENCY_COLD'
    from_hash           TEXT NOT NULL,
    to_hash             TEXT NOT NULL,
    block_id            TEXT,            -- populated for COLD transitions
    triggered_by        TEXT NOT NULL,   -- 'scheduler' | 'halt_event' | 'admin'
    transition_ns       BIGINT NOT NULL,
    integrity_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at         TIMESTAMPTZ,
    notes               TEXT
);
```

This table is itself classified as `LEGAL` evidence — it can never be deleted or modified.

### 6. Integration with Existing Stack

| Component | Integration Point |
|---|---|
| `RuntimeContinuityEngine` (ADR-159) | HALT trigger fires `EMERGENCY_COLD` pipeline event |
| `RCRWriteQueue` (ADR-160) | Provides batch artifacts to HOT stage |
| `omnix_atf_verify.py` (ADR-156) | Extended with `--archive-block` verification mode |
| `decision_receipts_warm` | Formalized as the HOT→WARM stage artifact for `LEGAL` class |
| ADR-162 retention policy | ADR-163 is the mechanical implementation of ADR-162 policy |

---

## Consequences

### Positive

- **ATF-INV-006 guaranteed across all lifecycle stages.** No archived artifact can become
  unverifiable — the pipeline enforces offline reconstructability at every transition.
- **Forensic-grade custody chain.** The `evidence_custody_log` + COLD block chain together
  form a complete chain of custody for every governance artifact OMNIX produces.
- **HALT-triggered emergency archival** ensures no evidence can be modified after a governance
  halt — the integrity window is closed at the moment of the halt event.
- **Infrastructure parity.** OMNIX now matches the evidence lifecycle model of regulated
  forensic systems (SIEM, LEGALTECH, regulated financial audit).

### Neutral

- **COLD tier requires object storage.** S3-compatible storage (AWS S3, Cloudflare R2, Backblaze B2)
  is required for Stage 3. Cost is negligible at current volumes (~$0.023/GB/month for R2).
- **Block sealing is asynchronous.** COLD blocks are sealed weekly unless an emergency trigger fires.
  There is a window where evidence is in WARM but not yet in COLD — this is acceptable because
  WARM artifacts still have their original `content_hash` in the manifest.

### Negative

- **Implementation complexity.** The pipeline requires three new subsystems: WARM manifest,
  COLD block sealer, and verifier extension. This ADR authorizes the design; implementation
  requires a dedicated development cycle.
- **Parquet dependency.** COLD storage requires a Parquet serialization library (`pyarrow`).
  This is the only new production dependency introduced by this ADR.

---

## Implementation Notes

- The `evidence_custody_log` table must be created before any pipeline code runs — it is
  a prerequisite, not an output.
- The Parquet block sealer must run in a separate process from the governance engine to avoid
  blocking request handling.
- COLD block files must be named deterministically: `OMNIX-BLOCK-{YYYYMMDD}-{seq:06d}.parquet`
  to enable chain reconstruction from filenames alone.
- The public verifier script (`omnix_atf_verify.py`) must ship alongside every COLD archive
  block delivery — an auditor must never need to download additional tools.

---

## References

- ADR-028 — Decision Receipts
- ADR-131 — Execution Integrity Layer
- ADR-156 — Agent Trust Fabric (public verifier CLI)
- ADR-159 — Runtime Governance Continuity (HALT trigger)
- ADR-160 — RCR Performance & Observability Layer (RCRWriteQueue)
- ADR-162 — Evidence Lifecycle & Immutable Retention (policy this ADR implements)
- RFC-ATF-1 §7.6 — ATF-INV-006 (Independent Verifiability)
- RFC-ATF-2 §5 — RGC-INV-003 (HALT Propagation — emergency archive trigger)
