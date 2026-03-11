# ADR-037: Per-Client Configurable Thresholds

**Status**: ACCEPTED  
**Date**: March 11, 2026  
**Author**: Harold Nunes, OMNIX  
**Category**: Architecture / B2B / Enterprise  
**Depends on**: ADR-028 (External Signal Evaluation API), ADR-026 (Multi-Vertical Governance Architecture)  
**Implements**: Deferred item from ADR-028 Constraints section

---

## Context

ADR-028 (February 27, 2026) deliberately deferred per-client threshold customization:

> "Thresholds are currently fixed (`CHECKPOINT_DEFAULTS`). Post-investment, per-client thresholds are a premium feature."

The rationale was sound at the time: launching with fixed thresholds reduces implementation risk while proving the core product works. However, the enterprise sales pipeline surfaced a concrete blocker — institutional B2B clients (quantitative funds, credit decisioning platforms) operate under their own internal risk mandates and need thresholds calibrated to their domain. A fund managing $200M+ cannot use the same CP-2 risk exposure threshold as a startup's supply chain optimizer.

Per-client thresholds are now implemented as a paid tier unlock — **not** a free feature. The admin-only control plane ensures governance integrity cannot be loosened without explicit operator authorization.

---

## Decision

Store per-client checkpoint threshold overrides in a dedicated `client_thresholds` PostgreSQL table. At evaluation time, the system loads the client's custom thresholds and merges them with `CHECKPOINT_DEFAULTS`. Missing rows fall through to defaults. Any error in loading (DB timeout, constraint violation, parse error) falls back to `CHECKPOINT_DEFAULTS` — fail-closed behavior is preserved.

Only the numeric **threshold value** is client-configurable. The checkpoint signal binding, operator (`gte`/`lte`), and description are immutable at the system level and cannot be overridden.

---

## Architecture

```
POST /api/governance/evaluate
        │
        ▼
_require_auth() → client_id (from DB, never from request header)
        │
        ▼
_load_client_checkpoint_overrides(client_id)
  ├── Query: SELECT checkpoint_id, threshold FROM client_thresholds WHERE client_id = ?
  ├── Merge with CHECKPOINT_DEFAULTS (DB rows override, missing rows use defaults)
  ├── Validate each custom value against CHECKPOINT_SAFETY_FLOORS
  └── ANY error → return CHECKPOINT_DEFAULTS (fail-closed)
        │
        ▼
GovernanceEvaluationEngine(checkpoint_overrides=resolved_checkpoints)
        │
        ▼
Response includes: thresholds_source: "default" | "client_custom"
```

### Admin Control Plane

Threshold management is admin-only:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/governance/admin/clients/<id>/thresholds` | GET | View effective thresholds with source annotation |
| `/api/governance/admin/clients/<id>/thresholds` | PUT | Upsert one or more checkpoint overrides |
| `/api/governance/admin/clients/<id>/thresholds` | DELETE | Revert all overrides to system defaults |

---

## Schema

```sql
CREATE TABLE IF NOT EXISTS client_thresholds (
    id           SERIAL PRIMARY KEY,
    client_id    VARCHAR(64) NOT NULL REFERENCES b2b_clients(client_id) ON DELETE CASCADE,
    checkpoint_id VARCHAR(8) NOT NULL CHECK (checkpoint_id IN ('CP-1','CP-2','CP-3','CP-4','CP-5','CP-6')),
    threshold    NUMERIC(5,2) NOT NULL CHECK (threshold >= 0 AND threshold <= 100),
    updated_by   VARCHAR(64),
    updated_at   TIMESTAMPTZ DEFAULT NOW(),
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, checkpoint_id)
);
CREATE INDEX IF NOT EXISTS idx_client_thresholds_client_id ON client_thresholds(client_id);
```

**Design rationale — row-per-checkpoint (not JSON blob)**:
- Each row has a `UNIQUE(client_id, checkpoint_id)` constraint — no duplicates possible
- CHECK constraint enforces 0–100 range at the DB layer
- ON DELETE CASCADE: deactivating a client automatically cleans up their thresholds
- Individual rows are auditable (when changed, by whom) without parsing JSON
- UPSERT pattern (`INSERT ... ON CONFLICT DO UPDATE`) is clean and atomic

---

## Safety Floors

Hard-coded in `omnix_core/governance/external_evaluator.py` as `CHECKPOINT_SAFETY_FLOORS`. No client may set a threshold outside these bounds. The admin `PUT` endpoint validates against these floors before writing to the database.

| Checkpoint | Default Threshold | Min Client | Max Client | Rationale |
|-----------|-------------------|-----------|-----------|-----------|
| CP-1 Probability Check | 50 | **30** | 90 | ≥30 ensures minimum probabilistic confidence |
| CP-2 Risk Limits | 65 | **40** | 85 | ≥40 min strictness; operator cannot loosen below 40 |
| CP-3 Signal Coherence | 55 | **30** | 90 | ≥30 prevents incoherent signals from passing |
| CP-4 Trend Persistence | 50 | **25** | 90 | ≥25 maintains trend validity check |
| CP-5 Stress Resilience | 35 | **20** | 80 | ≥20 baseline stress test remains active |
| CP-6 Logic Consistency | 40 | **20** | 80 | ≥20 internal contradiction check cannot be disabled |

---

## Fail-Closed Behavior

The implementation is **fail-closed at every layer**:

1. `_load_client_checkpoint_overrides()` catches all exceptions — DB timeouts, parse errors, import failures — and returns `CHECKPOINT_DEFAULTS`
2. `_ensure_thresholds_table()` is called lazily on the first request, ensuring the table exists even on fresh deployments
3. `GovernanceEvaluationEngine` already accepts `checkpoint_overrides=None`, in which case it uses its internal defaults
4. If `checkpoint_overrides` is an empty list (should never happen), the engine also falls back

---

## Response Metadata

Every `/api/governance/evaluate` response now includes:

```json
"thresholds_source": "default"     ← no custom thresholds defined for this client
"thresholds_source": "client_custom"  ← at least one checkpoint uses a custom value
```

This enables clients to audit which threshold regime was active for each governance receipt.

---

## Consequences

### Positive
- **Enterprise unlock**: institutional clients can calibrate thresholds to their internal risk mandates
- **Revenue lever**: threshold customization is a paid premium tier, supporting the $2K–$5K/month pricing with enterprise upsell
- **Audit trail**: per-row `updated_by` + `updated_at` provides full change history
- **Zero client autonomy**: clients cannot change their own thresholds — only admins (OMNIX operators) can, preventing gaming
- **Backwards compatible**: all existing clients without rows in `client_thresholds` continue with `CHECKPOINT_DEFAULTS` — zero behavior change

### Constraints
- No self-service threshold UI for clients (future sprint — web dashboard for admin threshold management)
- Admin-only access enforced at the API layer (`role='admin'` check via RBAC)
- Threshold changes take effect on the **next** evaluate call — no invalidation of previous receipts
- Safety floors are hard-coded in source; changing them requires a code deployment

---

## Files

| File | Change |
|------|--------|
| `omnix_core/governance/external_evaluator.py` | Added `CHECKPOINT_SAFETY_FLOORS` dict + `validate_threshold_against_floor()` |
| `omnix_dashboard/blueprints/governance.py` | Added `_load_client_checkpoint_overrides()`, `_ensure_thresholds_table()`, 3 admin endpoints, `thresholds_source` in response |
| `docs/reference/adr/ADR-028-external-signal-evaluation-api.md` | Constraints section updated — deferred item now IMPLEMENTED |
| `omnix_services/database_service/database_service.py` | `client_thresholds` table creation added to enterprise init |
