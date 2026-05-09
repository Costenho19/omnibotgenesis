# REMEDIATION ARCHITECTURE — ISR-001 · ISR-008 · ISR-013 · ISR-017 · ISR-021
**Audit Ref:** ISR-2026-Q2-001  
**Date:** 9 May 2026  
**Classification:** INTERNAL — Pre-Deployment Architecture

---

## OVERVIEW

This document covers the architecture, migration strategy, operational impact, replay compatibility, and institutional tradeoffs for the five highest-priority remediations from the Institutional Survivability Report before any regulated multi-tenant deployment.

Each ISR section follows the same structure:
1. Root cause (one sentence)
2. Architecture decision
3. Migration strategy (zero-downtime where possible)
4. Operational impact
5. Replay compatibility
6. Institutional tradeoffs

---

## ISR-001 — AVM Tenant-Isolated Calibration

### Root Cause
`AssumptionValidityMonitor` is a process-level singleton keyed by `domain`. All tenants sharing a domain share the same calibration baseline, drift history, and recalibration triggers.

### Architecture Decision

**Phase 1 (implemented now):** Introduce `tenant_id` as a first-class key in all AVM persistence and runtime paths. The `_avm_instance` singleton is replaced by a `dict[tenant_id, AssumptionValidityMonitor]` registry, each instance isolated.

**Schema change:**  
`avm_calibration_snapshots`: PRIMARY KEY changes from `(domain)` to `(tenant_id, domain)`.  
`avm_baseline_change_log`: `tenant_id` column added.

**File path change:**  
`avm_snapshots/{domain}_calibration.json` → `avm_snapshots/{tenant_id}/{domain}_calibration.json`

**Backward compatibility:**  
- Existing rows with no `tenant_id` are migrated to `tenant_id = 'default'`.
- `get_avm_instance()` gains a `tenant_id` parameter (default: `'default'`).
- All existing single-tenant deployments continue working without code changes (they use `default`).

### Migration Strategy (Zero-Downtime)

```
Step 1: Apply DDL_ALTER_TENANT_ID (ADD COLUMN IF NOT EXISTS tenant_id DEFAULT 'default')
Step 2: Backfill: UPDATE avm_calibration_snapshots SET tenant_id = 'default' WHERE tenant_id IS NULL
Step 3: CREATE UNIQUE INDEX ON (tenant_id, domain)
Step 4: DROP PRIMARY KEY on domain alone, promote composite PK
Step 5: Rename existing avm_snapshots/*.json to avm_snapshots/default/*.json
Step 6: Deploy new code (reads tenant_id from request context)
```

Railway DDL is applied idempotently via `ADD COLUMN IF NOT EXISTS` — no downtime.

### Operational Impact
- `gov_blueprint.py` must pass `client_id` as `tenant_id` to every AVM call.
- Admin recalibration scripts must specify `--tenant-id`.
- Dashboard AVM status endpoint must filter by `tenant_id`.

### Replay Compatibility
Existing receipts carry no `avm_snapshot_id` reference. The change is additive — no existing receipts are invalidated. The `calibrated_by_tenant` field added to new receipts is purely informational.

### Institutional Tradeoffs
- **Pro:** Contractually guarantees tenant isolation of calibration baselines. Required for any SLA with regulated bank clients.
- **Con:** Each tenant domain now requires its own genesis calibration. Onboarding cost increases. Mitigation: a "shared template" genesis can be cloned per-tenant on first use.

---

## ISR-008 — Semantic Governance Version Registry

### Root Cause
`engine_version` is a free string from an env var. No mechanism links it to a specific checkpoint logic fingerprint, making historical receipts semantically opaque after code changes.

### Architecture Decision

New module: `omnix_core/governance/semantic_version_registry.py`

Contains:
- `SEMANTIC_REGISTRY`: dict mapping `engine_version → SemanticEntry`
- `SemanticEntry`: checkpoint definitions, threshold semantics, ADR citations, policy hash, logic fingerprint
- `compute_logic_fingerprint()`: SHA-256 of sorted checkpoint source files
- `get_current_entry()`: returns the registry entry for the running version
- `get_historical_entry(version)`: for receipt reconstruction
- `assert_version_consistency()`: raises if running code hash ≠ registry entry hash (for CI)

Each governance receipt gains `governance_schema_version` and `checkpoint_logic_fingerprint` fields (additive — old receipts without these fields are flagged as `pre-registry`).

### Migration Strategy
1. Create `semantic_version_registry.py` with current version entry.
2. Add `governance_schema_version` and `checkpoint_logic_fingerprint` to new receipts in `decision_receipt.py`.
3. Add `test_engine_version_matches_registry` to CI — fails if logic changes without registry update.
4. Historical receipts without fingerprint are tagged `legacy_unregistered` — verifiable by hash, not semantically reconstructable beyond stored veto_chain.

### Replay Compatibility
Old receipts: verifiable by hash and PQC signature. Semantic reconstruction relies on `veto_chain` field (always present since ADR-028) and `engine_version` string for approximate ADR mapping.  
New receipts: fully semantically reconstructable from registry.

### Institutional Tradeoffs
- **Pro:** Regulators can reconstruct what CP-3 meant on any date for any receipt going forward.
- **Pro:** CI guard prevents silent semantic drift.
- **Con:** Registry must be maintained by engineering. Every non-trivial checkpoint change requires a registry entry update. Mitigation: CI test makes this mandatory, not optional.

---

## ISR-013 — Durable Transparency Chain Persistence

### Root Cause
`_store_entry()` catches all exceptions and returns `False`, allowing execution to continue with a silent gap in the audit chain.

### Architecture Decision

**Three-layer durability:**

1. **Primary path:** PostgreSQL `transparency_log` (existing). Retry 3× with 100ms/300ms/900ms backoff.
2. **Fallback path:** If all DB retries fail, write to `transparency_chain_pending` table (append-only, simpler schema). A background reconciliation job (`reconcile_pending_chain_entries`) drains this table into `transparency_log` on next success.
3. **Degraded governance signal:** If both paths fail, raise `TransparencyChainDegraded` flag in process state. All subsequent governance evaluations include `audit_chain_degraded: true` in their receipt. Operators receive Telegram alert.

No execution is blocked (fail-open for business continuity), but the gap is now **explicit and auditable**, not silent.

### Migration Strategy
1. Add `transparency_chain_pending` table (DDL idempotent).
2. Replace `_store_entry` with `_store_entry_with_durability`.
3. Add `reconcile_pending_chain_entries()` called on app startup and every 5 minutes via background thread.

### Operational Impact
- New table `transparency_chain_pending`. Low write volume in normal operation (only filled during DB stress).
- Telegram alert on degraded state requires `TELEGRAM_ADMIN_USER_ID` (already configured).
- Startup reconciliation adds ~50ms to cold start.

### Replay Compatibility
Fully compatible. Pending entries are reconciled into the main chain with original timestamps. The Merkle root is preserved from the time of the original write attempt.

### Institutional Tradeoffs
- **Pro:** No more silent audit gaps. Regulators can see exactly when and why a chain entry was delayed.
- **Pro:** Pending table provides a secondary evidence trail even during DB outages.
- **Con:** Reconciliation adds complexity. Mitigation: reconciliation is idempotent (duplicate entries are detected by `log_id` uniqueness).

---

## ISR-017 — LLM Prompt Injection Containment

### Root Cause
`user_message` from the Telegram bot is inserted directly into LLM prompts as an f-string with no sanitization. The same adapter then queries PostgreSQL and Kraken in real-time based on intent detected in the raw user text.

### Architecture Decision

**New module:** `omnix_services/ai_service/input_sanitizer.py`

Three-layer defense:

1. **Structural sanitization:** Strip prompt-injection markers (`[INST]`, `<|system|>`, `\n\nSystem:`, `Ignore previous instructions`, etc.) before any prompt construction.
2. **Length enforcement:** `MAX_USER_MESSAGE_CHARS = 2000`. Messages exceeding this are truncated with a user-facing notice.
3. **Query isolation:** DB queries in `_fetch_trade_performance`, `_fetch_veto_data`, `_fetch_investor_data` are bounded by the authenticated `user_id` from the Telegram auth context — never by text extracted from `user_message`. The user cannot cause a query for a different `user_id` through message content.

**Not changed:** The LLM still receives user message content — the goal is containment, not censorship. Governance decisions remain fully deterministic and are never influenced by LLM output.

### Migration Strategy
1. Create `input_sanitizer.py` with `sanitize_user_message()` and `enforce_query_isolation()`.
2. Inject `sanitize_user_message(user_message)` at the entry point of `generate_response()` and `generate_response_async()`.
3. Audit and isolate all DB query methods to use `user_id` from auth context.

### Operational Impact
- Users sending messages >2000 chars receive a truncation notice. Very rare in practice for a trading bot.
- Sanitization adds <1ms per message (regex-based).
- Prompt injection attempts are logged at `WARNING` level for security audit.

### Replay Compatibility
N/A — this change affects the conversational layer only. Governance receipts are unaffected.

### Institutional Tradeoffs
- **Pro:** Closes confirmed injection vector. Required for any enterprise client whose employees use the Telegram bot.
- **Pro:** Explicit logging of injection attempts provides a security audit trail.
- **Con:** Aggressive sanitization may occasionally reject legitimate complex queries. Mitigation: the BLACKLISTED_PHRASES list is tunable and can be expanded/contracted based on observed false positives.

---

## ISR-021 — Payload Encryption Key Survivability

### Root Cause
`PAYLOAD_ENCRYPTION_KEY` is a single Fernet key with no versioning, rotation policy, or recovery mechanism. If lost, encrypted signal payloads in all historical `decision_receipts` are permanently irrecoverable.

### Architecture Decision

**New module:** `omnix_core/evidence/payload_key_manager.py`

Key versioning strategy:
- Keys are named `PAYLOAD_ENCRYPTION_KEY_v{N}` (e.g., `v1`, `v2`).
- `PAYLOAD_ENCRYPTION_KEY_CURRENT` env var points to the active version identifier (e.g., `"v2"`).
- Every encrypted payload is prefixed with `omnix-pek-v{N}:` to identify the key version used.
- Decryption tries the version identified in the prefix, then falls back through all known versions.
- `PAYLOAD_ENCRYPTION_KEY` (legacy) maps to version `v1` for backward compatibility.

**Escrow policy (operational, not code):**
- `PAYLOAD_ENCRYPTION_KEY_v{N}` is stored in Railway + an out-of-band encrypted backup (e.g., 1Password vault with access granted to CAIO and CTO).
- Key rotation is documented in `docs/operations/KEY_ROTATION.md`.
- Every receipt includes `payload_key_version` field so auditors know which key to retrieve for decryption.

### Migration Strategy
1. Add `payload_key_version: "v1"` to all new receipts immediately.
2. Existing receipts without `payload_key_version` are assumed `v1` during decryption.
3. New `PayloadKeyManager` class wraps all encrypt/decrypt calls with version awareness.
4. `gov_blueprint._encrypt_payload()` and `server.py` decrypt path both use `PayloadKeyManager`.

### Operational Impact
- All new receipts have `payload_key_version` field (additive — backward compatible).
- Key rotation requires: set new env var + update `PAYLOAD_ENCRYPTION_KEY_CURRENT` + leave old key available for decryption.
- No re-encryption of historical data required (version prefix handles multi-key decryption).

### Replay Compatibility
- New receipts: `payload_key_version` field enables deterministic key selection for decryption.
- Old receipts: assumed `v1` — decryption works if `PAYLOAD_ENCRYPTION_KEY` (mapped to v1) is available.
- If v1 key is lost: payload is irrecoverable (unchanged from current state), but at least it is now explicit which key was needed.

### Institutional Tradeoffs
- **Pro:** Survives key rotation without breaking historical decryption.
- **Pro:** Auditor can determine exactly which key to request from escrow for any receipt.
- **Pro:** Supports MiFID II explainability requirement — signal payload can be recovered years later if escrow process is followed.
- **Con:** Adds operational burden of maintaining multiple key versions in Railway. Mitigation: `PayloadKeyManager` provides a `list_active_key_versions()` helper for operational visibility.

---

## IMPLEMENTATION ORDER

```
1. ISR-013 — Lowest risk, highest audit impact. No schema dependency.
2. ISR-017 — Low risk, immediate security gain.
3. ISR-021 — Additive to receipt schema. No breaking changes.
4. ISR-008 — Additive to receipt schema. CI guard added.
5. ISR-001 — Highest complexity. Requires schema migration + tenant context threading.
```

All changes are designed to be:
- **Backward compatible**: existing receipts remain verifiable.
- **Additive**: new fields do not break existing parsers.
- **Idempotent**: DDL migrations use `ADD COLUMN IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`.
- **Observable**: every change adds structured logging, not silent behavior.
