# ADR-180: Temporal Governance Bridge (TGB)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Supersedes:** None  
**Extends:** ADR-157 (TAR · Temporal Authority) · ADR-173 (DSPP) · ADR-159 (RGC) · ADR-165 (OEP)  
**Related:** ADR-162 (Evidence Lifecycle) · ADR-164 (Forensic Archive) · RFC-ATF-5  
**Implements:** `omnix_core/governance/temporal_bridge.py`  
**Priority Record:** OMNIX-PAR-2026-TGB-001 · May 2026

---

## Context

### The Two-Speed Problem in AI Governance

AI governance operates simultaneously at two radically different temporal scales:

**Micro-scale (nanoseconds to seconds):** Runtime governance enforcement. A Delegation Receipt is issued with `created_at` precision of nanoseconds. A Runtime Continuity Record evaluates CES in sub-millisecond cycles. A HALT decision is enforced before the next instruction executes. The ATF stack operates at this scale with full cryptographic precision.

**Macro-scale (months to years):** Regulatory review and legal proceedings. A regulator reviewing an EU AI Act compliance claim examines records from 12–36 months prior. A court admitting AI governance evidence may be reviewing decisions made under a regulatory framework that has since been superseded. A forensic auditor reconstructing an incident timeline works across years of accumulated records.

No bridge currently exists between these two scales. The ATF stack produces nanosecond-precision records. Regulatory frameworks operate on calendar-year review cycles. The gap between them is structural — and it creates a reproducible failure mode: governance records that are cryptographically intact but semantically uninterpretable when reviewed years later under changed regulatory contexts.

### The Semantic Drift Problem at Scale

ADR-173 (DSPP) introduced Dynamic Semantic Portability for cross-domain semantic drift within a single operational timeframe. The TGB addresses a structurally different problem: **temporal semantic drift** — the change in meaning of governance fields as regulatory frameworks evolve over time.

Concrete examples:
- A "HIGH RISK" classification under EU AI Act Annex III 2024 may map to a different risk tier under a 2027 amendment
- A `ces_score` of 72.0 that was MONITORING-tier under ATF Spec v1.4 may be re-evaluated against ATF Spec v2.0 thresholds in a future audit
- A jurisdiction-specific governance parameter valid under GCC/DIFC Regulation 2024 may require reinterpretation under a 2026 revision

DSPP provides semantic drift assessment at a point in time. TGB provides the **longitudinal projection layer** — a formal mechanism for mapping historical governance records to current interpretive frameworks without modifying the underlying evidence.

### The Quantum Gravity Analogy

In physics, Quantum Gravity seeks to unify quantum mechanics (governing the infinitesimally small, at Planck-scale precision) with General Relativity (governing the cosmologically large, at astronomical scales). The two theories are individually correct at their respective scales but structurally incompatible at the boundary.

The TGB is the governance equivalent: a formal bridge between the nanosecond-precision micro-governance layer (RCR, TAR, DR) and the multi-year macro-governance layer (regulatory frameworks, audit cycles, legal proceedings). Both layers are individually correct. The TGB makes them coherent at the boundary.

---

## Decision

### Establish the Temporal Governance Bridge (TGB)

ADR-180 establishes the **Temporal Governance Bridge (TGB)** as a protocol layer that projects ATF governance evidence across temporal boundaries. The TGB introduces two new record types:

1. **Temporal Context Snapshot (TCS)** — embedded at receipt issuance, captures the exact regulatory framework context active at the moment of governance
2. **Regulatory Alignment Receipt (RAR)** — issued at review time, projects historical records to current frameworks without modifying original evidence

The TGB is **non-destructive by design**: RARs are projection artifacts. They exist alongside original records, never replacing or modifying them. TGB-INV-002 makes this a hard invariant.

### Temporal Context Snapshot (TCS)

A TCS is embedded within every ATF record at issuance (DR, TAR, RCR). It captures the complete regulatory context at the nanosecond of record creation:

```
{
  "tcs_id": "TCS-{16HEX}",
  "parent_record_id": "{DR|TAR|RCR id}",
  "issued_at_ns": "{nanosecond epoch}",
  "regulatory_context": {
    "eu_ai_act_version": "2024/1689-v1.0",
    "nist_ai_rmf_version": "1.0",
    "gcc_difc_version": "2024-r1",
    "iso_42001_version": "2023",
    "atf_spec_version": "1.4",
    "omnix_engine_version": "{semver}",
    "jurisdiction_active": ["EU", "GCC_DIFC", "GLOBAL"],
    "risk_classification_scheme": "EU_AI_ACT_ANNEX_III_2024"
  },
  "threshold_context": {
    "nominal_threshold": 80.0,
    "monitoring_lower": 50.0,
    "warning_lower": 30.0,
    "halt_threshold": 30.0,
    "fragmentation_limit": 0.90,
    "max_delegation_depth": 5
  },
  "tcs_hash": "sha256(canonical_tcs_json)",
  "tcs_seal": "{Dilithium-3 signature}"
}
```

The `tcs_hash` is included in the parent record's `posture_state_hash` computation, binding the regulatory context to the cryptographic identity of the governance decision. This ensures that a future reviewer can verify not only what the decision was, but under exactly what regulatory and threshold context it was made.

### Regulatory Alignment Receipt (RAR)

A RAR is issued by the TGB when a reviewing party needs to interpret a historical record under a current regulatory framework. The RAR is a projection — it maps fields and classifications from the historical context to the current context, documenting every mapping explicitly:

```
{
  "rar_id": "RAR-{16HEX}",
  "source_record_id": "{original DR|TAR|RCR id}",
  "source_tcs_id": "TCS-{16HEX}",
  "review_timestamp": "{ISO8601}",
  "reviewer_context": {
    "eu_ai_act_version": "2027/amended-v2.1",
    "atf_spec_version": "2.0",
    "jurisdiction_active": ["EU", "UK", "GCC_DIFC"]
  },
  "field_projections": [
    {
      "field": "continuity_status",
      "source_value": "MONITORING",
      "source_scheme": "ATF-1.4-THRESHOLD",
      "target_value": "ELEVATED_OVERSIGHT",
      "target_scheme": "EU_AI_ACT_ART9_2027",
      "projection_rule": "MONITORING → ELEVATED_OVERSIGHT (CES 50.0–79.9 maps to Art.9(3) enhanced monitoring)",
      "projection_confidence": "HIGH",
      "requires_human_review": false
    }
  ],
  "semantic_shift_detected": true,
  "semantic_shift_fields": ["continuity_status", "risk_classification"],
  "original_record_integrity": "VERIFIED",
  "original_record_hash": "sha256:{original_record_canonical}",
  "projection_methodology": "TGB-RAR-V1.0",
  "rar_seal": "{Dilithium-3 signature}",
  "atf_spec_version_source": "1.4",
  "atf_spec_version_target": "2.0"
}
```

The `original_record_integrity: VERIFIED` field confirms that the source record's Dilithium-3 seal was verified before projection — ensuring the RAR is built on authentic evidence.

### Temporal Migration Record (TMR)

When a governance record transitions between evidence lifecycle states (HOT → WARM → COLD, per ADR-162), the TGB issues a **Temporal Migration Record (TMR)** capturing the state of the regulatory context at each transition point:

```
{
  "tmr_id": "TMR-{16HEX}",
  "source_record_id": "{receipt id}",
  "migration_event": "HOT_TO_WARM | WARM_TO_COLD",
  "migration_timestamp": "{ISO8601}",
  "regulatory_context_at_migration": "{TCS-like snapshot}",
  "retention_basis": "EU_AI_ACT_ART72_7YR | GCC_DIFC_ART14_5YR | CUSTOMER_CONTRACT",
  "next_review_due": "{ISO8601}",
  "tmr_seal": "{Dilithium-3 signature}"
}
```

TMRs provide a longitudinal audit trail of how governance evidence moved through its lifecycle under which regulatory context — critical for demonstrating compliance with multi-jurisdiction retention obligations.

### Offline Projection Computation

RARs MUST be independently computable by any party possessing:
1. The original record + its embedded TCS
2. The published TGB projection rulebook (versioned, published at `omnix_core/governance/tgb_rulebook.json`)
3. The OMNIX public key

The projection rulebook is a versioned, PQC-signed JSON document containing all field mapping rules for every supported framework transition. It is published via OMNIX API and embedded in OEP packages — ensuring a reviewer in 2030 can reconstruct projections using only offline artifacts.

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS atf_temporal_context_snapshots (
    id                      SERIAL PRIMARY KEY,
    tcs_id                  TEXT NOT NULL UNIQUE,
    parent_record_id        TEXT NOT NULL,
    parent_record_type      TEXT NOT NULL,
    issued_at_ns            BIGINT NOT NULL,
    regulatory_context      JSONB NOT NULL,
    threshold_context       JSONB NOT NULL,
    tcs_hash                TEXT NOT NULL,
    tcs_seal                TEXT NOT NULL,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS atf_regulatory_alignment_receipts (
    id                      SERIAL PRIMARY KEY,
    rar_id                  TEXT NOT NULL UNIQUE,
    source_record_id        TEXT NOT NULL,
    source_tcs_id           TEXT NOT NULL,
    review_timestamp        TIMESTAMP WITH TIME ZONE NOT NULL,
    reviewer_context        JSONB NOT NULL,
    field_projections       JSONB NOT NULL,
    semantic_shift_detected BOOLEAN NOT NULL DEFAULT FALSE,
    semantic_shift_fields   TEXT[],
    original_record_integrity TEXT NOT NULL,
    original_record_hash    TEXT NOT NULL,
    projection_methodology  TEXT NOT NULL DEFAULT 'TGB-RAR-V1.0',
    rar_seal                TEXT NOT NULL,
    atf_spec_version_source TEXT NOT NULL,
    atf_spec_version_target TEXT NOT NULL,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS atf_temporal_migration_records (
    id                      SERIAL PRIMARY KEY,
    tmr_id                  TEXT NOT NULL UNIQUE,
    source_record_id        TEXT NOT NULL,
    migration_event         TEXT NOT NULL,
    migration_timestamp     TIMESTAMP WITH TIME ZONE NOT NULL,
    regulatory_context_at_migration JSONB NOT NULL,
    retention_basis         TEXT NOT NULL,
    next_review_due         TIMESTAMP WITH TIME ZONE,
    tmr_seal                TEXT NOT NULL,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tcs_parent ON atf_temporal_context_snapshots(parent_record_id);
CREATE INDEX IF NOT EXISTS idx_rar_source ON atf_regulatory_alignment_receipts(source_record_id);
CREATE INDEX IF NOT EXISTS idx_tmr_source ON atf_temporal_migration_records(source_record_id);
CREATE INDEX IF NOT EXISTS idx_tmr_event ON atf_temporal_migration_records(migration_event);
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TGB_ENABLED` | `true` | Enable TCS embedding in all new records |
| `TGB_AUTO_RAR` | `false` | Auto-generate RAR on record retrieval if framework version mismatch detected |
| `TGB_RULEBOOK_VERSION` | `1.0` | Active projection rulebook version |
| `TGB_INCLUDE_IN_OEP` | `true` | Include TCS + RARs in OEP evidence packages |
| `TGB_RETENTION_DEFAULT` | `EU_AI_ACT_ART72_7YR` | Default retention basis for TMR generation |

---

## Invariants

### TGB-INV-001 — Mandatory TCS Embedding
**Every ATF record (DR, TAR, RCR) issued with `TGB_ENABLED=true` MUST carry an embedded TCS that captures the complete regulatory and threshold context at the nanosecond of issuance. Records without TCS are TGB-incomplete.**

Rationale: A record without temporal context is interpretable only in the present. A record with TCS is interpretable at any future point — the essential property for multi-year regulatory review.

### TGB-INV-002 — RAR Non-Destruction
**A RAR MUST NOT modify any field of the original source record. RARs are projection artifacts. The source record MUST remain byte-identical before and after RAR generation. Any system where RAR generation modifies source records has a critical integrity defect.**

Rationale: Projecting historical evidence to current frameworks must not alter the historical evidence itself. These are categorically separate operations.

### TGB-INV-003 — Offline RAR Computability
**Every RAR produced by TGB MUST be independently computable by any party possessing the source record, the source TCS, and the published TGB projection rulebook — without accessing any OMNIX infrastructure.**

Rationale: A projection that requires platform access to verify is not a verifiable projection — it is a platform-trust assertion. Offline computability is the minimum bar for regulatory credibility.

### TGB-INV-004 — Projection Monotonicity
**A governance record that is valid under framework version N MUST remain valid under framework version N+k (k≥0) unless an explicit invalidity declaration (EID) is issued and recorded in `atf_regulatory_alignment_receipts` with `original_record_integrity: INVALIDATED`.**

Rationale: Regulatory framework evolution MUST NOT retroactively invalidate governance evidence without an explicit, auditable declaration. Silent invalidation is a governance failure mode that creates legal exposure.

### TGB-INV-005 — TMR PQC Sealing
**Every Temporal Migration Record and every RAR MUST be sealed with Dilithium-3 (ML-DSA-65, FIPS 204). Unsealed temporal bridge artifacts MUST NOT be accepted as valid governance evidence.**

Rationale: Temporal bridge records are governance evidence. They carry the same evidentiary weight as primary records and require the same cryptographic protection.

---

## Consequences

### Positive

- **Multi-year regulatory compliance:** Governance records remain interpretable and compliant through regulatory framework evolution without re-issuance or modification.
- **Legal admissibility:** RARs provide the contextual mapping that courts and arbitrators need to admit AI governance evidence produced under superseded frameworks.
- **Retention obligation satisfaction:** TMRs document retention decisions under specific regulatory clauses — satisfying EU AI Act Art. 72, GCC/DIFC Art. 14, and ISO/IEC 42001 §9.1 simultaneously.
- **OEP enrichment:** TCS + RARs embedded in OEP packages make forensic evidence packages self-contained across time — not just across organizations (ADR-165).
- **Competitive differentiation:** No peer governance system provides a formal temporal projection layer. This directly addresses the "governance evidence aging" problem that enterprise legal teams face in long-cycle regulated industries (financial services, healthcare, government AI).

### Constraints

- TCS embedding adds approximately 400 bytes per record. In high-throughput environments, `TGB_ENABLED=false` may be configured for non-consequential evaluations.
- The TGB rulebook must be maintained as frameworks evolve. A dedicated governance process for rulebook updates is required (quarterly minimum).
- RAR generation for large historical record sets should be batched — on-demand RAR at query time is appropriate for individual record lookups only.

---

## Regulatory Alignment

| Framework | Obligation | TGB Satisfaction |
|---|---|---|
| EU AI Act Art. 72 | 7-year record retention for high-risk AI | TMR tracks lifecycle transitions under Art. 72 retention basis |
| EU AI Act Art. 11 | Technical documentation remains current | RAR provides framework-current projection of historical documentation |
| NIST AI RMF MAP 5.2 | Impact documentation across AI lifecycle | TCS captures regulatory context at decision time across full lifecycle |
| GCC/DIFC Art. 14 | Audit trail maintenance across framework revisions | RAR + TMR provide continuous audit trail through framework revisions |
| ISO/IEC 42001 §9.3 | Management review with historical trend analysis | TCS enables cross-framework trend analysis across governance history |

---

## Priority Record

**OMNIX-PAR-2026-TGB-001**  
Filed: May 2026  
Author: Harold Alberto Nunes Rodelo  
Organization: OMNIX QUANTUM LTD  
Jurisdiction: England & Wales (registered) · UAE (operational)  
Scope: Temporal Governance Bridge — TCS/RAR/TMR architecture, TGB-INV-001–005  
Classification: Architecture Decision Record — Accepted
