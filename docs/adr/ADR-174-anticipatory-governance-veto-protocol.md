# ADR-174: Anticipatory Governance Veto Protocol (AGVP)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Supersedes:** None  
**Extends:** ADR-076 (AVM Signal Schema) · ADR-120 (AVM Auto-Recalibration) · ADR-144 (AMG) · ADR-076 (AVM Alerts)  
**Related:** ADR-028 (Decision Receipts) · ADR-156 (DR) · ADR-161 (GPIL) · ADR-173 (DSPP)  
**Implements:** `omnix_core/governance/anticipatory_governance_veto.py`  
**Priority Record:** OMNIX-PAR-2026-AGVP-001 · May 20, 2026

---

## Context

### The Detection Latency Problem

The Assumption Validity Monitor (ADR-076 / ADR-120) evaluates governance signal drift
exclusively at **request time** — when a governance decision is solicited. This is a
deliberate reactive design. The pipeline does not issue a veto until a request arrives.

This creates a structural gap: **detection latency**. Between the moment adverse conditions
begin (a regulatory shock, a market collapse, a sudden jurisdiction change) and the moment
the next governance request arrives, OMNIX is operating in an unguarded window. If no
request arrives for hours, the veto never fires. The governance system knows nothing has
changed until someone asks.

The Terra/LUNA collapse (May 2022) illustrates the operational consequence: a governance
system that checks only at request boundaries would have processed requests during the
cascade's onset, issuing receipts under conditions that were already in violation of their
calibration envelope. The veto arrives too late to matter.

> *"la prueba Terra/LUNA es convincente — pero lo difícil es detectar el fallo de
> admisibilidad lo suficientemente pronto como para que la recepción del veto importe."*
>
> — Reza Zarei, Creator of 3S Silent Authority System (LinkedIn, May 2026)

### Why Existing Mechanisms Do Not Close This Gap

| Mechanism | What it does | What it does NOT do |
|---|---|---|
| AVM.evaluate() (ADR-076) | Checks drift at request time | Monitors between requests |
| auto_recalibrate_stale_domains() (ADR-120) | Periodic baseline refresh (72h) | Continuous drift detection |
| fire_avm_alert() (ADR-076) | Sends alerts when evaluate() detects anomalies | Monitors without requests |
| CAG (ADR-116) | Pre-session admission gate | Monitors between sessions |

The gap is architectural, not operational. OMNIX needs a mechanism that can issue a veto
**before any request arrives** — a veto that pre-empts, not merely blocks.

### The Insight: Authority Can Be Anticipatory

A governance system that only reacts is reactive by definition. OMNIX's architecture —
fail-closed, PQC-signed, receipt-based — is capable of something stronger: emitting a
cryptographically-attested veto that exists in the governance ledger **before any pending
decision**. When a request subsequently arrives, it does not cause the veto. It finds it.

This is the **Anticipatory Governance Veto Protocol (AGVP)**.

---

## Decision

### Two-Layer Veto Architecture

ADR-174 establishes that OMNIX operates a two-layer veto architecture:

```
Layer 1 — Reactive Veto (existing, ADR-076)
  Triggered by governance request → AVM.evaluate() → DRIFT_BLOCK
  Latency: detection occurs at request time only

Layer 2 — Anticipatory Veto (new, ADR-174 / AGVP)
  Triggered by AGVPWatchdog continuous monitoring → ProactiveVetoReceipt (PVR)
  Latency: detection within one watchdog interval (default 60s)
```

Both layers carry equivalent governance authority (AGV-INV-001). The anticipatory layer does
not replace the reactive layer — it precedes it.

### Artifact: Proactive Veto Receipt (PVR)

A PVR is a PQC-signed, database-persisted governance artifact emitted by the AGVP Watchdog
when it detects that a domain's live signals have drifted beyond the AVM threshold — without
any pending governance request having triggered the evaluation.

**Identifier format:** `OMNIX-PVR-{16HEX}`

**PVR fields:**

| Field | Type | Description |
|---|---|---|
| `pvr_id` | string | `OMNIX-PVR-{16HEX}` — globally unique |
| `tenant_id` | string | Tenant identifier (default: `"default"`) |
| `domain` | string | The governance domain that triggered the veto |
| `drift_score` | float | AVM drift score at time of watchdog assessment (0–100) |
| `drift_threshold` | float | The threshold that was exceeded |
| `drift_components` | dict | Per-signal drift breakdown (full forensic record) |
| `signals_at_assessment` | dict | Live signal values at time of watchdog poll |
| `signals_seen_at` | ISO UTC | When the watchdog last received fresh signals for this domain |
| `snapshot_id` | string | AVM calibration snapshot used for comparison |
| `assessment_timestamp` | ISO UTC | When the watchdog performed the evaluation |
| `veto_effective_from` | ISO UTC | Same as assessment_timestamp — the veto precedes all subsequent requests |
| `block_reason` | string | Human-readable veto reason with full context |
| `status` | enum | `ACTIVE \| REVOKED` |
| `revoked_at` | ISO UTC | Set only when status=REVOKED |
| `revoked_by` | string | Identity of admin who revoked (set only when REVOKED) |
| `revocation_reason` | string | Reason for revocation (set only when REVOKED) |
| `watchdog_interval_seconds` | int | Configured watchdog interval at time of emission |
| `content_hash` | string | SHA-256 of canonical PVR fields (excludes sig) |
| `pqc_signature` | string | ML-DSA-65 signature over content_hash (or `"TESTING"`) |
| `pqc_algorithm` | string | `"ML-DSA-65"` |
| `created_at` | ISO UTC | Creation timestamp |

**AGV-INV-004:** The PVR `content_hash` covers `domain + tenant_id + drift_score +
signals_at_assessment + assessment_timestamp` in canonical JSON form. This commits the watchdog
to the exact observable state at time of emission — the veto cannot be backdated or modified.

### AGVPWatchdog

The AGVP Watchdog is a daemon thread that continuously monitors all calibrated AVM domains.

**Operation cycle:**

```
Every AGVP_WATCHDOG_INTERVAL_SECONDS (default 60, minimum 30):
  For each domain with a calibrated AVM snapshot:
    1. Retrieve last-seen signals + seen_at from AGVP signal cache
    2. If signals are stale (> AGVP_MAX_SIGNAL_AGE_SECONDS), skip domain
    3. If an ACTIVE PVR already exists for this domain, skip (idempotent)
    4. Call AVM.evaluate(signals, domain)
    5. If result.is_valid=False AND result.pass_through=False:
       → Emit ProactiveVetoReceipt, persist to DB, fire Telegram alert
```

**Signal cache:** The signal cache (`_agvp_signal_cache`) is updated by the governance
pipeline at the beginning of every evaluation — **before** checking for active PVRs.
This decouples observability from the blocking decision: a domain can be blocked by an
active PVR while the watchdog still receives fresh signal telemetry. This breaks the
deadlock scenario where blocked requests prevent signal flow.

**Multi-process safety (ADR-174 §Multi-Dyno):** In multi-process deployments (Railway),
multiple watchdog instances may run concurrently. The AGVP uses a DB-level uniqueness
constraint (`UNIQUE active PVR per tenant+domain`) combined with idempotent `INSERT … ON
CONFLICT DO NOTHING` semantics. Only the first watchdog to detect the condition writes the
PVR. Alert deduplication via the existing `fire_avm_alert()` rate limiter prevents alert
storms. When Redis is available (`REDIS_URL`), an advisory lease reduces redundant polling.

### Revocation

PVR revocation is administrative. The watchdog cannot revoke its own receipts.

**AGV-INV-002:** A PVR transitions from `ACTIVE` to `REVOKED` exclusively via explicit
admin action: `AGVPEngine.revoke_pvr(pvr_id, revoked_by, reason)`. This requires the caller
to supply an authorization token (validated against `AGVP_ADMIN_TOKEN` or the existing AVM
admin allowlist). Revocation is logged immutably in the PVR record.

**Rationale:** Auto-revocation — triggering revocation when drift returns below threshold —
creates oscillation risk (chatter), removes administrative accountability from the recovery
decision, and makes the PVR forensically ambiguous. An admin revocation is an explicit human
attestation that the domain is safe to resume. That accountability is architecturally valuable.

**Recovery path:** When a domain recovers:
1. Admin calls `revoke_pvr()` with documented reason
2. Admin calls `save_calibration_snapshot()` to re-establish baseline (or auto-recalibration resumes)
3. Next governance request proceeds through reactive AVM normally
4. PVR record remains in DB as permanent forensic record of the event

**Note:** The watchdog emits an informational `RECOVERY_CANDIDATE` log entry when drift
returns below threshold for a domain with an active PVR. This surfaces the recovery signal
to the admin without auto-revoking.

### Integration with ADR-120 Auto-Recalibration

**AGV-INV-006:** `auto_recalibrate_stale_domains()` (ADR-120) skips domains that have an
active PVR. Auto-recalibration during an active veto would update the baseline to the drifted
conditions, masking the root cause. Recalibration of a vetoed domain requires explicit admin
action (revoke PVR first, then recalibrate, or call `revoke_and_recalibrate()` admin endpoint
with documented reason).

### Integration with AVM Evaluate Pipeline

The AGVP check is inserted as the **first gate** in the governance evaluation path, before
AVM drift computation:

```
governance request arrives
  │
  ├─ 1. AGVPEngine.update_domain_signals(domain, signals)  ← always runs, preserves observability
  │
  ├─ 2. AGVPEngine.get_active_pvr(domain)
  │       → ACTIVE PVR found → return ANTICIPATORY_VETO_ACTIVE (is_valid=False)
  │       → No active PVR → continue
  │
  └─ 3. AVM.evaluate(signals, domain)  ← existing reactive path
```

The signal update (step 1) always executes regardless of whether a PVR is active. This is
the architectural solution to the observability deadlock: even a fully blocked domain
continues to feed the watchdog with fresh signal telemetry.

---

## Invariants

### AGV-INV-001 — Anticipatory Authority Equivalence

An ACTIVE PVR blocks all governance requests for the affected domain with the same authority
as a reactive AVM drift block. The block is not weaker because it was issued proactively.
Governance receipts for blocked requests reference the PVR ID in their block_reason.

### AGV-INV-002 — Watchdog Cannot Self-Revoke

The AGVPWatchdog cannot revoke ProactiveVetoReceipts it has emitted. Revocation is
exclusively the domain of authorized admin action. The watchdog may log
`RECOVERY_CANDIDATE` events when drift subsides, but may not change PVR status.

### AGV-INV-003 — Minimum Watchdog Interval

The watchdog polling interval must be `≥ AGVP_MIN_INTERVAL_SECONDS` (30). An interval
of 0 or less is rejected at initialization with a `ValueError`. The intent is continuous
monitoring — not instantaneous polling that would saturate the AVM evaluation path.

### AGV-INV-004 — PVR Content Hash Commitment

The PVR `content_hash` is a SHA-256 digest of the canonical JSON encoding of:
`{pvr_id, tenant_id, domain, drift_score, drift_threshold, signals_at_assessment,
assessment_timestamp, veto_effective_from, snapshot_id}`. The signature covers this hash.
A PVR cannot be post-issuance modified without invalidating its signature.

### AGV-INV-005 — No Veto Without Baseline

The watchdog only emits a PVR when `AVM.evaluate()` returns `is_valid=False` AND
`pass_through=False`. Domains without a calibration snapshot (`pass_through=True`) cannot
receive proactive vetos — the watchdog has no authoritative baseline to compare against.
A domain that has never been calibrated is not under AGVP governance.

### AGV-INV-006 — Auto-Recalibration Freeze During Active PVR

The ADR-120 auto-recalibration cycle (`auto_recalibrate_stale_domains()`) must not
recalibrate domains with an active PVR. The AGVP module exposes `has_active_pvr(domain)`
for this check. Recalibrating to drifted conditions would destroy the governance baseline
and make the PVR's evidence forensically meaningless.

---

## Configuration Reference

| Environment Variable | Default | Description |
|---|---|---|
| `AGVP_ENABLED` | `true` | Master switch for the AGVP watchdog |
| `AGVP_WATCHDOG_INTERVAL_SECONDS` | `60` | Polling interval (minimum 30) |
| `AGVP_MAX_SIGNAL_AGE_SECONDS` | `300` | Max age for cached signals — stale signals are skipped |
| `AGVP_ADMIN_TOKEN` | _(none)_ | Token required for PVR revocation — if unset, revocation is locked |
| `AGVP_PQC_SIGN` | `true` | Enable ML-DSA-65 signing of PVRs (disable only in test) |

---

## Database Table

```sql
CREATE TABLE IF NOT EXISTS avm_anticipatory_veto_receipts (
    pvr_id               TEXT PRIMARY KEY,
    tenant_id            TEXT NOT NULL DEFAULT 'default',
    domain               TEXT NOT NULL,
    drift_score          REAL NOT NULL,
    drift_threshold      REAL NOT NULL,
    drift_components     JSONB,
    signals_at_assessment JSONB,
    signals_seen_at      TIMESTAMPTZ,
    snapshot_id          TEXT,
    assessment_timestamp TIMESTAMPTZ NOT NULL,
    veto_effective_from  TIMESTAMPTZ NOT NULL,
    block_reason         TEXT,
    status               TEXT NOT NULL DEFAULT 'ACTIVE',
    revoked_at           TIMESTAMPTZ,
    revoked_by           TEXT,
    revocation_reason    TEXT,
    watchdog_interval_seconds INTEGER,
    content_hash         TEXT,
    pqc_signature        TEXT,
    pqc_algorithm        TEXT DEFAULT 'ML-DSA-65',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- AGV-INV-001: Only one ACTIVE PVR per tenant+domain
CREATE UNIQUE INDEX IF NOT EXISTS uq_agvp_active_pvr_per_domain
    ON avm_anticipatory_veto_receipts (tenant_id, domain)
    WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_agvp_tenant_domain
    ON avm_anticipatory_veto_receipts (tenant_id, domain, status);

CREATE INDEX IF NOT EXISTS idx_agvp_created_at
    ON avm_anticipatory_veto_receipts (created_at DESC);
```

---

## Consequences

### Positive

- **Closes the detection latency gap**: governance systems no longer require a pending
  request to detect and record adverse conditions. The audit trail starts with the event,
  not the first request after it.
- **Anticipatory receipt**: a PVR exists in the governance ledger with a timestamp that
  predates any subsequent blocked request — this is forensically unambiguous evidence that
  the system detected the problem proactively.
- **No behavioral change for healthy domains**: if no domain exceeds its drift threshold,
  the watchdog runs silently and emits nothing.
- **Signal observability preserved during block**: the decoupled signal update path ensures
  the watchdog sees fresh telemetry even while a domain is fully blocked.
- **Admin accountability for recovery**: forced admin revocation creates an explicit human
  attestation that recovery is safe — stronger than automatic reset.

### Negative / Trade-offs

- **Additional background thread**: one daemon thread per process. In single-process
  deployments this is negligible. In multi-process deployments, DB uniqueness constraints
  handle coordination.
- **Signal cache dependency**: the watchdog's effectiveness depends on signals flowing
  through the governance pipeline. Domains that receive zero traffic have no cached signals
  and are not monitored by the watchdog. This is by design (AGV-INV-005): uncalibrated
  and unobserved domains are not under AGVP authority.
- **Admin revocation required for recovery**: this is a governance choice, not a limitation.
  It trades operational convenience for accountability. Systems requiring fully automated
  recovery should not deploy AGVP (or should configure it accordingly).

---

## Relationship to RFC-ATF-4

ADR-173 (DSPP), ADR-171 (SGIP), and ADR-174 (AGVP) together form the complete normative
foundation for RFC-ATF-4. AGVP addresses the temporal authority dimension of governance
receipts: a receipt issued under an ACTIVE PVR carries forensic evidence of the conditions
under which the block was issued, signed with PQC, persisted, and timestamped before the
request. This is the strongest form of governance attestation OMNIX produces.

---

*ADR-174 — Harold Nunes — OMNIX QUANTUM LTD — May 2026*  
*Priority Record: OMNIX-PAR-2026-AGVP-001*
