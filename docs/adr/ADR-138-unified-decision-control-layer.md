# ADR-138 — Unified Decision Control Layer (UDCL)

**Status:** ACCEPTED (v1.0)
**Date:** 2026-05-06
**Author:** OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo
**Module:** MOD-014
**Scope:** `omnix_core/governance/unified_control_layer.py` · `omnix_web/api/gov_blueprint.py`

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| v1.0 | 2026-05-06 | Initial implementation — UnifiedDecisionControlLayer, 5 pillars, ControlReceipt, DB persistence, 5 API endpoints |

---

## 1. Context and Problem Statement

OMNIX exposes a rich governance pipeline via `POST /api/governance/evaluate` (ADR-028).
That endpoint is a **black box**: callers submit signals, receive a decision. The internal
multi-layer architecture — SAE, SPG, CBG, 11-Checkpoint Pipeline, TIE, PQC Receipt — is not
individually visible to B2B consumers.

This creates two institutional gaps:

**Gap 1: Pillar opacity**
Enterprise clients cannot see *which governance layer* produced a block. A B2B compliance
officer reviewing a BLOCKED decision needs to know whether it was rejected at structural
admissibility (Layer 0), provenance ambiguity (Layer 0b/c), or a specific checkpoint
(Layer 1). Without pillar-level visibility, the audit chain is incomplete.

**Gap 2: Coordinated failure mode**
The existing `/evaluate` endpoint runs layers internally but does not provide a formal
coordination contract. A client integrating multiple layers independently risks partial
coverage: they may call SPG separately, evaluate independently, and not connect the
outcomes under a single verifiable seal.

**MOD-014** closes both gaps.

---

## 2. Decision

Implement a **Unified Decision Control Layer (UDCL)** as a formal B2B orchestration
surface that:

1. **Coordinates** all OMNIX governance pillars in defined, immutable sequence.
2. **Returns** per-pillar results with layer IDs, pass/fail, latency, and detail.
3. **Seals** the entire multi-pillar outcome with a tamper-evident `control_hash`.
4. **Persists** every evaluation to `udcl_control_receipts` for audit retrieval.
5. **Exposes** five API endpoints for evaluation, schema, health, and receipt lookup.

---

## 3. Architecture

### 3.1 Pipeline Sequence

```
POST /api/governance/control/evaluate
    │
    ├── [Layer 0]   SAE — Structural Admissibility Engine        (ADR-092)
    │     └── Rejects malformed signal envelopes and inadmissible domains
    │
    ├── [Layer 0b]  SPG — State Provenance Guard                 (ADR-133)
    │     └── ADVISORY: warns on AMBIGUOUS lineage, does not block alone
    │
    ├── [Layer 0c]  CBG — Conditional Bind Gate [opt-in]         (ADR-135)
    │     └── Blocks if SPG AMBIGUOUS exceeds severity threshold
    │     └── Requires cbg_enabled=true in request body
    │
    ├── [Layer 1-2] CP  — 11-Checkpoint Pipeline + TIE           (ADR-028/053)
    │     └── Full CP-0..CP-11 evaluation + Trajectory Invariant Engine
    │     └── PQC receipt generated even for BLOCKED decisions
    │
    └── [Layer 3]   PQC — Cryptographic Receipt                  (ADR-096)
          └── Dilithium-3 signed, chain-linked to prior receipt
          └── receipt_id embedded in ControlReceipt
```

### 3.2 Fail-Closed Policy

| Pillar | Type | Failure behavior |
|---|---|---|
| SAE | Mandatory | BLOCKED — structural rejection is always final |
| SPG | Advisory | Warning only — CONTRADICTED does not block alone |
| CBG | Opt-in mandatory | BLOCKED — bind explicitly denied |
| CP (11-checkpoint + TIE) | Mandatory | BLOCKED — any checkpoint failure |
| PQC Receipt | Mandatory | BLOCKED — receipt generation required for all outcomes |

**Exception handling**: Any unhandled exception in a mandatory pillar → BLOCKED with
`blocking_pillar="system_error"`. Advisory pillar exceptions → pass-through, detail
notes the unavailability.

### 3.3 ControlReceipt

Every evaluation returns a `ControlReceipt`:

```json
{
  "control_id":       "UDCL-A3F2B1C9D0E4F5A6",
  "decision":         "APPROVED",
  "blocking_pillar":  null,
  "block_reason":     null,
  "pillar_results": {
    "sae": {
      "pillar": "sae", "layer": "Layer 0", "passed": true,
      "advisory": false, "latency_ms": 1.2,
      "detail": {"admission_status": "admitted", "adr": "ADR-092"}
    },
    "spg": {
      "pillar": "spg", "layer": "Layer 0b", "passed": true,
      "advisory": true, "latency_ms": 3.4,
      "detail": {"verdict": "SINGULAR", "lineage_singularity": 82.5,
                 "contradiction_count": 0, "spg_id": "SPG-A3F2B1C9", "adr": "ADR-133"}
    },
    "checkpoint_pipeline": {
      "pillar": "checkpoint_pipeline", "layer": "Layer 1-2", "passed": true,
      "advisory": false, "latency_ms": 45.1,
      "detail": {"decision": "APPROVED", "score": 78, "checkpoints_total": 11,
                 "checkpoints_passed": 11, "adr": "ADR-028"}
    },
    "pqc_receipt": {
      "pillar": "pqc_receipt", "layer": "Layer 3", "passed": true,
      "advisory": false, "latency_ms": 12.3,
      "detail": {"receipt_id": "OMNIX-TRD-A3F2B1C9D0E4",
                 "algorithm": "Dilithium-3", "pqc_signed": true,
                 "verify_url": "https://omnixquantum.net/verify#OMNIX-TRD-...",
                 "chain_linked": true, "adr": "ADR-096"}
    }
  },
  "receipt_id":        "OMNIX-TRD-A3F2B1C9D0E4",
  "domain":            "trading",
  "asset":             "BTC/USD",
  "total_latency_ms":  62.0,
  "pillar_latency_ms": {"sae": 1.2, "spg": 3.4, "checkpoint_pipeline": 45.1, "pqc_receipt": 12.3},
  "control_hash":      "sha256:a3f2b1c9d0e4f5a6...",
  "pillars_evaluated": 4,
  "pillars_passed":    4,
  "cbg_enabled":       false,
  "module":            "MOD-014",
  "adr":               "ADR-138",
  "version":           "1.0"
}
```

### 3.4 ControlHash

The `control_hash` seals the multi-pillar outcome against post-hoc modification:

```python
SHA-256({
    "control_id": "UDCL-...",
    "decision":   "APPROVED",
    "pillars":    sorted(["sae:PASS", "spg:PASS", "checkpoint_pipeline:PASS", "pqc_receipt:PASS"])
})
```

The hash covers only the `control_id`, final `decision`, and each pillar's outcome
(`PASS`/`BLOCK`). It does not cover individual pillar details — those may include
non-deterministic fields (timestamps, scores that vary by microsecond). The hash
guarantees that the overall outcome and pillar-level verdict cannot be silently changed.

---

## 4. API Endpoints

All authenticated endpoints require `X-API-Key` header (same B2B RBAC as ADR-028).

| Method | Path | Auth | Description |
|---|---|---|---|
| GET  | `/api/governance/control/schema`               | Public | UDCL schema, pillar catalog, design invariants |
| GET  | `/api/governance/control/health`               | Client | Real-time pillar availability status |
| POST | `/api/governance/control/evaluate`             | Client | Full multi-pillar evaluation |
| GET  | `/api/governance/control/receipts/<control_id>`| Client | Fetch single control receipt by ID |
| GET  | `/api/governance/control/receipts`             | Client | Paginated list of client's control receipts |

### POST /api/governance/control/evaluate — Request

```json
{
  "signals": {
    "signal_integrity": 78,
    "probability_score": 65,
    "risk_exposure": 42,
    "signal_coherence": 71,
    "trend_persistence": 60,
    "stress_resilience": 55
  },
  "asset":             "BTC/USD",
  "domain":            "trading",
  "metadata":          {},
  "compliance_config": {"jurisdiction": "UAE"},
  "cbg_enabled":       false
}
```

### POST /api/governance/control/evaluate — Response (BLOCKED example)

```json
{
  "success":          true,
  "control_id":       "UDCL-C9A3F2B1D0E4F5A6",
  "decision":         "BLOCKED",
  "blocking_pillar":  "checkpoint_pipeline",
  "block_reason":     "CP-3: Monte Carlo VETO — win probability below threshold",
  "pillar_results":   { ... },
  "receipt_id":       "OMNIX-TRD-C9A3F2B1...",
  "control_hash":     "sha256:c9a3f2b1d0e4f5a6...",
  "total_latency_ms": 58.3,
  "module":           "MOD-014",
  "adr":              "ADR-138"
}
```

---

## 5. Database Schema

### udcl_control_receipts

```sql
CREATE TABLE IF NOT EXISTS udcl_control_receipts (
    control_id        VARCHAR(64)   PRIMARY KEY,
    client_id         VARCHAR(128)  NOT NULL,
    decision          VARCHAR(16)   NOT NULL,
    blocking_pillar   VARCHAR(64),
    block_reason      TEXT,
    receipt_id        VARCHAR(128),
    domain            VARCHAR(64)   NOT NULL DEFAULT 'generic',
    asset             VARCHAR(64)   NOT NULL DEFAULT '',
    pillar_results    JSONB         NOT NULL DEFAULT '{}',
    control_hash      VARCHAR(80)   NOT NULL DEFAULT '',
    cbg_enabled       BOOLEAN       NOT NULL DEFAULT FALSE,
    total_latency_ms  FLOAT,
    pillars_evaluated INTEGER       NOT NULL DEFAULT 0,
    pillars_passed    INTEGER       NOT NULL DEFAULT 0,
    adr               VARCHAR(16)   NOT NULL DEFAULT 'ADR-138',
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
```

**Indexes:**
- `idx_udcl_client_id` — fetch client's receipt history
- `idx_udcl_decision` — aggregate queries by decision outcome
- `idx_udcl_created_at DESC` — time-ordered audit queries

**Design decisions:**
- `control_id` is opaque token (UDCL-{16 hex}) — not a serial integer
- `pillar_results` stored as JSONB verbatim — full detail preserved
- `ON CONFLICT (control_id) DO NOTHING` — idempotent insert
- Table created lazily on first use — zero startup migration required

---

## 6. Design Invariants

| # | Invariant |
|---|---|
| 1 | All pillar results are returned even on block — full transparency for institutional audit |
| 2 | `blocking_pillar` names the first pillar that produced a non-advisory failure |
| 3 | `control_hash` seals the entire multi-pillar outcome — tamper-evident |
| 4 | SPG (Layer 0b) is advisory — AMBIGUOUS warns but never blocks alone |
| 5 | CBG (Layer 0c) is opt-in — disabled by default, enable via `cbg_enabled=true` |
| 6 | PQC receipt is generated for ALL decisions including BLOCKED |
| 7 | Mandatory pillar engine exception → BLOCKED with `blocking_pillar="system_error"` |
| 8 | Advisory pillar engine exception → pass-through, detail notes unavailability |
| 9 | `udcl_control_receipts` table is created lazily — no startup migration required |
| 10 | Webhook push uses existing ADR-053 infrastructure — `event: "control.evaluated"` |

---

## 7. Relationship to Other ADRs

### ADR-028 — External Signal Evaluation API (upstream dependency)
UDCL reuses the `GovernanceEvaluationEngine` loaded by ADR-028. The UDCL is a
coordinating layer over the existing pipeline, not a replacement.

### ADR-092 — Structural Admissibility Engine (Layer 0)
SAE is the first pillar in the UDCL sequence. UDCL calls `get_layer0_metrics().snapshot()`
to check `admission_status`. If unavailable, UDCL passes through (SAE fail-safe).

### ADR-133 — State Provenance Guard (Layer 0b)
SPG is the second pillar. UDCL calls `evaluate_provenance()` and exposes the result
as an advisory pillar. The `spg_id` from SPG is passed to CBG if enabled.

### ADR-135 — Conditional Bind Gate (Layer 0c)
CBG is opt-in. When `cbg_enabled=true`, UDCL calls `ConditionalBindGate().evaluate()`
with the SPG result. A `GATE_CREATED` verdict → BLOCKED.

### ADR-037 — Per-Client Configurable Thresholds
UDCL loads per-client checkpoint overrides via `_load_client_checkpoint_overrides()`
and passes them to the checkpoint pipeline, preserving full per-client customization.

### ADR-053 — Generic Webhook Push
On every UDCL evaluation, a webhook push with `event: "control.evaluated"` is
dispatched in a daemon thread to the client's registered endpoint.

### ADR-052 — API Key Security
UDCL endpoints enforce the same `_require_auth()` checks: brute-force lockout,
IP blocklist, key expiry, admin IP allowlist.

### ADR-081 — Per-Client Quota Enforcement
UDCL evaluations are counted toward client daily/monthly quotas via
`_check_client_quota()` — same infrastructure as `/api/governance/evaluate`.

### ADR-131 — Execution Integrity Layer
Future integration: UDCL can accept an `execution_intent` field to link
governance decisions directly to `ExecutionReceipt` records.

---

## 8. Investor Narrative

> "OMNIX does not just evaluate decisions — it coordinates governance.
> The Unified Decision Control Layer is the single API surface that runs
> every governance pillar in sequence, fails closed if any non-advisory
> layer rejects, and returns a tamper-evident ControlReceipt that shows
> exactly which pillar produced which outcome. Institutional B2B clients
> get full audit transparency: Layer 0 structural integrity, Layer 0b
> provenance traceability, Layer 0c conditional bind accountability,
> and 11-checkpoint governance — all under one cryptographically sealed call."

---

## 9. Consequences

### Positive
- **Pillar visibility**: B2B clients see per-pillar results, latency, and the exact blocking layer.
- **Single verifiable seal**: `control_hash` + `receipt_id` close the audit chain under one call.
- **CBG integration**: Opt-in human attestation workflow is now available via the standard API.
- **Webhook parity**: UDCL evaluations emit `control.evaluated` events using ADR-053 infrastructure.
- **Additive**: Zero modifications to existing `/api/governance/evaluate` endpoint.
- **Backward compatible**: Existing clients continue to function without change.

### Negative / Trade-offs
- **Higher per-call latency**: 5 pillars run sequentially. Measured overhead vs `/evaluate`: ~5–15ms
  (SAE + SPG imports; CBG disabled by default). Acceptable for institutional B2B use cases.
- **Additional DB table**: `udcl_control_receipts` adds one table. Created lazily — no migration.
- **CBG requires SPG**: The CBG pillar depends on SPG result. If SPG is unavailable, CBG
  fails safe (bind allowed per ADR-135 §2.1 Constraint 1).

---

## 10. Files

| File | Role |
|---|---|
| `omnix_core/governance/unified_control_layer.py` | Core module — UnifiedDecisionControlLayer, PillarResult, ControlReceipt |
| `omnix_web/api/gov_blueprint.py` | 5 API endpoints + DB persistence helpers |
| `udcl_control_receipts` (DB table) | Persistent control receipt audit trail |
| `docs/adr/ADR-138-unified-decision-control-layer.md` | This document |

---

## 11. Compliance References

| Standard | Requirement | ADR-138 Response |
|---|---|---|
| EU AI Act Art. 9(5) | Risk management system must cover all lifecycle phases | UDCL covers signal→decision→receipt in one verifiable call |
| EU AI Act Art. 14(4)(c) | Human oversight must have visibility into AI system operation | `pillar_results` exposes every layer — full operational visibility |
| DORA Art. 6 | ICT risk management across all layers | Per-pillar health check via `/control/health` |
| ISO 42001 §6.1.2 | AI risk assessment must be documented and traceable | `control_hash` + `pillar_results` provides traceable evidence |
| MiFID II Art. 25 | Transaction reporting with complete decision trail | `control_id` → `receipt_id` creates continuous audit chain |
| NIST AI RMF — GOVERN 1.2 | Roles and responsibilities for AI risk documented | `blocking_pillar` field names responsible governance layer |
