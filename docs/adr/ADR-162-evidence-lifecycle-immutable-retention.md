# ADR-162: Evidence Lifecycle & Immutable Retention

**Status:** Accepted  
**Date:** May 14, 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** None  
**Extends:** ADR-028 (Decision Receipts) · ADR-159 (Runtime Governance Continuity) · ADR-160 (RPOL)  
**Related:** ADR-131 (Execution Integrity Layer) · ADR-138 (UDCL) · ADR-147 (Scope Authorization) ·
            ADR-156 (Agent Trust Fabric) · ADR-157 (Temporal Authority) · ADR-158 (Cross-Domain Trust) ·
            ADR-161 (GPIL)

---

## Context

OMNIX has crossed an architectural threshold. What began as an AI governance layer has matured
into a **runtime governance infrastructure** — one that continuously produces cryptographically
signed, legally relevant, auditable evidence at every decision point.

This creates a problem that every serious regulated infrastructure eventually faces:
**evidence lifecycle engineering**.

The system now produces data across fundamentally different value categories:

- **Legal evidence** — Dilithium-3-signed receipts that establish non-repudiable proof of
  governance decisions. These are irreplaceable.
- **Runtime telemetry** — High-frequency continuity samples (RCRs) that reflect momentary
  system health. Most are redundant over time; exceptions are not.
- **Continuity samples** — CES scores and status snapshots emitted at each sampling interval.
  NOMINAL and HEALTHY states form compressible timelines; HALT, CRITICAL, and FRAGMENTATION
  states are forensic artifacts.
- **Exception events** — Veto triggers, anomaly detections, escalation artifacts. Always
  permanent regardless of age.
- **Cross-runtime governance contracts** — CRGCs (ADR-161). Bilateral, PQC-signed agreements
  between sovereign runtimes. Immutable by design.
- **PQC chains** — The full Delegation Receipt chain (DR → TAR → RCR) underpinning each
  governance decision. Cannot be truncated without breaking ATF-INV-006 (Independent
  Verifiability).
- **Shadow nominal events** — Trading simulator events without veto or anomaly. High volume,
  low forensic value. Compressible.

Without a formal retention policy, these categories are treated identically — stored in the
same tables, with the same indexes, indefinitely. This creates three failure modes:

1. **Storage explosion** — `shadow_trade_events` averages 5.4 KB per row at ~20 MB/day growth.
   Full JSONB payloads stored for nominal events that carry no forensic value.
2. **Audit confusion** — No formal distinction between "this receipt is permanent evidence" and
   "this telemetry row can be aggregated". Compliance auditors cannot tier their verification.
3. **Verifiability risk** — Moving data to cheaper storage without preserving `content_hash`
   verifiability breaks ATF-INV-006 retroactively for all archived receipts.

---

## Decision

### 1. Evidence Classification

Every data artifact produced by OMNIX is assigned to exactly one evidence class.
The class determines its retention tier, compression policy, and archival requirements.

| Class | Code | Examples | Forensic Value |
|---|---|---|---|
| **Legal Evidence** | `LEGAL` | `decision_receipts`, `execution_receipts`, `udcl_control_receipts` | Irreplaceable — non-repudiable proof |
| **PQC Chain** | `PQC` | `atf_delegations`, `atf_temporal_records`, `atf_domain_bridges`, Dilithium-3 key receipts | Irreplaceable — verifiability chain |
| **Cross-Runtime Contract** | `CONTRACT` | `atf_runtime_continuity` CRGCs, `governance_scope_authorizations` | Immutable bilateral agreement |
| **Exception Event** | `EXCEPTION` | RCRs with `HALT`/`CRITICAL`/`FRAGMENTATION` status, `atf_continuity_escalations`, shadow events with veto/anomaly | Permanent forensic artifact |
| **Runtime Telemetry** | `TELEMETRY` | RCRs with `NOMINAL`/`MONITORING` status, `avm_calibration_snapshots` | Summarizable after retention window |
| **Continuity Sample** | `SAMPLE` | `atf_runtime_continuity` rows tagged `NOMINAL`/`HEALTHY` | Aggregatable into hourly snapshots |
| **Shadow Nominal Event** | `SHADOW_NOMINAL` | `shadow_trade_events` without veto, anomaly, or escalation | Compressible to hash + metadata |
| **Operational Data** | `OPS` | `b2b_clients`, `book_leads`, `paper_trading_balances` | Standard business retention |

### 2. Retention Tiers

OMNIX defines three storage tiers with explicit requirements:

#### HOT Tier
- **Duration:** 0–90 days from creation
- **Storage:** PostgreSQL (Railway managed)
- **Indexes:** Full — all query patterns supported
- **Access:** Real-time read/write
- **All evidence classes reside here during active window**

#### WARM Tier
- **Duration:** 90–365 days from creation
- **Storage:** PostgreSQL with partial compression
- **Indexes:** Reduced — audit and hash-lookup only
- **Access:** Read-only after promotion from HOT
- **Eligible classes:** `TELEMETRY`, `SAMPLE`, `SHADOW_NOMINAL`, `OPS`
- **Ineligible classes (remain HOT indefinitely):** `LEGAL`, `PQC`, `CONTRACT`, `EXCEPTION`
- **Existing artifact:** `decision_receipts_warm` table formalizes this pattern

#### COLD Tier
- **Duration:** 365 days+ (or permanent for immutable classes)
- **Storage:** Object storage (Parquet + SHA-256 block hash) — immutable archive
- **Indexes:** None — hash-addressed lookup only
- **Access:** Archival verification only
- **Invariant:** COLD storage MUST preserve `content_hash` and `pqc_signatures` to satisfy
  ATF-INV-006 (Independent Verifiability). A COLD artifact must be fully verifiable offline
  without any platform dependency.

### 3. Retention Policy Table

| Evidence Class | HOT | WARM | COLD | Deletion |
|---|---|---|---|---|
| `LEGAL` | Permanent | Never | Optional immutable archive | Never |
| `PQC` | Permanent | Never | Optional immutable archive | Never |
| `CONTRACT` | Permanent | Never | Optional immutable archive | Never |
| `EXCEPTION` | Permanent | Never | Optional immutable archive | Never |
| `TELEMETRY` | 90 days | 90–365 days | Aggregated snapshot | After COLD aggregation |
| `SAMPLE` (NOMINAL/HEALTHY) | 30 days | Aggregated hourly | Compressed timeline | After aggregation |
| `SHADOW_NOMINAL` | 30 days | Hash + metadata only | Compressed | After COLD compression |
| `OPS` | Active lifetime | 90–365 days | Optional | Per business policy |

### 4. Shadow Event Reduction Policy

`shadow_trade_events` is the highest-volume table in the system. The current schema stores
full JSONB payloads for every event regardless of outcome.

**New policy:** The payload stored depends on event classification at write time.

| Event Type | Stored Fields |
|---|---|
| Veto triggered | Full payload (EXCEPTION class — permanent) |
| Anomaly detected | Full payload (EXCEPTION class — permanent) |
| Escalation raised | Full payload (EXCEPTION class — permanent) |
| Critical risk tier | Full payload (EXCEPTION class — permanent) |
| Nominal / healthy | `event_id`, `timestamp_ns`, `event_type`, `agent_id`, `content_hash`, `risk_score` only |

This classification happens at write time, not retroactively. Estimated reduction:
**~80% volume decrease** for deployments where nominal events dominate.

### 5. RCR Summarization Policy

Runtime Continuity Records (`atf_runtime_continuity`) are emitted continuously by the
sampling engine (ADR-160). NOMINAL and HEALTHY records carry low individual forensic value
but high aggregate value.

**Summarization rule:**

- `HALT`, `CRITICAL`, `FRAGMENTATION`, `ESCALATION` RCRs → EXCEPTION class → permanent
- `WARNING` RCRs → EXCEPTION class → permanent (threshold crossing is forensically relevant)
- `MONITORING` RCRs → TELEMETRY class → summarizable after 90 days
- `NOMINAL` / `HEALTHY` RCRs → SAMPLE class → aggregatable into hourly snapshots after 30 days

**Hourly aggregate schema (SAMPLE compression):**

```
rcr_hourly_aggregate(
    hour_bucket        TIMESTAMPTZ,
    chain_root_id      TEXT,
    domain             TEXT,
    sample_count       INTEGER,
    avg_ces_score      FLOAT,
    min_ces_score      FLOAT,
    status_distribution JSONB,   -- {"NOMINAL": 847, "MONITORING": 12}
    first_rcr_id       TEXT,
    last_rcr_id        TEXT,
    content_hash       TEXT       -- hash of aggregate, not individual RCRs
)
```

Individual NOMINAL RCRs can be dropped after aggregation. The aggregate is not a substitute
for the original records for forensic purposes — it is a telemetry summary only.

### 6. Immutable Archive Invariant

**ELR-INV-001 — Verifiability Preservation:**
Any artifact moved to COLD tier MUST retain its `content_hash` and `pqc_signatures`
(where applicable) in a form that allows offline verification per ATF-INV-006.
Compression and format changes are permitted; hash mutation is not.

**ELR-INV-002 — Exception Permanence:**
No artifact classified as `EXCEPTION`, `LEGAL`, `PQC`, or `CONTRACT` may be deleted,
truncated, or compressed in a way that reduces its forensic completeness, regardless of age.

**ELR-INV-003 — Classification Immutability:**
Once an artifact is classified at write time, its evidence class cannot be downgraded.
A `SHADOW_NOMINAL` event that triggered a veto is reclassified to `EXCEPTION` at veto time
and treated as EXCEPTION from that point forward.

**ELR-INV-004 — HOT Retention Guarantee:**
All evidence classes remain in HOT tier for a minimum of 30 days regardless of volume
pressure. No automated process may promote to WARM before this minimum.

### 7. Database Maintenance Policy

Independent of the lifecycle tiers, the following maintenance operations are formally adopted:

1. **Dead index removal** — Indexes with 0 scans over 30 days are candidates for removal.
   Duplicate indexes (same columns, same table) are removed unconditionally.
2. **VACUUM schedule** — VACUUM ANALYZE runs weekly on all tables; immediately after any
   bulk operation producing > 10,000 dead tuples.
3. **Autovacuum tuning** — Tables with high row turnover (`paper_trading_balances`,
   `avm_calibration_snapshots`) use `autovacuum_vacuum_scale_factor = 0.01` and
   `autovacuum_analyze_scale_factor = 0.005`.

---

## Consequences

### Positive

- **Storage controlled:** `shadow_trade_events` growth reduced ~80% by payload reduction at
  write time. Predictable growth trajectory for HOT tier.
- **Audit clarity:** Compliance auditors can identify permanent evidence vs. summarizable
  telemetry without inspecting individual rows.
- **ATF-INV-006 preserved:** Immutable archive invariant (ELR-INV-001) ensures all archived
  receipts remain independently verifiable offline indefinitely.
- **Operational maturity:** OMNIX adopts the same lifecycle model used by Splunk, Datadog,
  and SIEM platforms — appropriate for a runtime governance infrastructure at this scale.

### Neutral

- **Summarization is lossy by design:** NOMINAL RCR aggregates cannot reconstruct individual
  samples. This is intentional and acceptable — individual NOMINAL samples carry no forensic
  value that the aggregate does not capture.
- **Write-time classification adds overhead:** Shadow event classification requires a
  conditional check at write time. Cost is O(1) per event, negligible at current volumes.

### Negative

- **Migration complexity:** Existing `shadow_trade_events` rows were stored without
  classification. Retroactive classification requires a one-time scan. Existing NOMINAL
  rows cannot be retroactively compressed without auditor sign-off.
- **COLD tier not yet implemented:** Object storage pipeline (Parquet + immutable archive)
  requires a separate implementation ADR. This ADR defines the policy; the pipeline ADR
  defines the mechanism.

---

## Implementation Notes

- `decision_receipts_warm` already exists and formalizes the HOT→WARM promotion pattern.
  This ADR retroactively ratifies that table as the canonical WARM tier artifact for
  `LEGAL` class (it stores warm copies, the HOT originals remain permanent).
- Shadow event classification must be implemented at the `shadow_trade_events` write path,
  not as a background job.
- The `rcr_hourly_aggregate` table is a new artifact — requires schema migration.
- Phase 1 database maintenance (dead index removal, VACUUM, autovacuum tuning) can be
  executed immediately without schema changes. It is not blocked by this ADR's
  implementation status.

---

## References

- ADR-028 — Decision Receipts (original governance receipt format)
- ADR-131 — Execution Integrity Layer
- ADR-138 — Unified Decision Control Layer
- ADR-147 — Governance Scope Authorization
- ADR-156 — Agent Trust Fabric
- ADR-157 — Temporal Authority Admissibility
- ADR-158 — Cross-Domain Trust Portability
- ADR-159 — Runtime Governance Continuity (RGC)
- ADR-160 — RCR Performance & Observability Layer (RPOL)
- ADR-161 — Governance Policy Interoperability Layer (GPIL)
- RFC-ATF-1 §7.6 — Independent Verifiability (ATF-INV-006)
- RFC-ATF-2 §5 — RGC Invariants (RGC-INV-001–008)
