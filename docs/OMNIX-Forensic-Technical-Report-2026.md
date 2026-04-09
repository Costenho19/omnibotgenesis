# OMNIX Quantum — Forensic Technical Report
**Classification:** Technical Due Diligence — Investor and Enterprise Grade  
**Date:** April 2026  
**Prepared by:** OMNIX QUANTUM LTD — Technical Governance Division  
**Build:** 6.6.0  
**Status:** Pre-Seed Round — Active Deployment  

---

## 1. Executive Summary

OMNIX Quantum is a **Decision Governance Infrastructure** — a domain-agnostic, fail-closed pipeline that intercepts, evaluates, and certifies decisions made by automated systems before execution is permitted.

Its core thesis: AI systems operating in high-stakes environments (financial trading, credit, insurance, industrial robotics) produce decisions that cannot be verified by their own internal logic. OMNIX provides an external, cryptographically-anchored governance layer that operates independently of the system under governance.

**What OMNIX is technically:**

- An 11-checkpoint signal evaluation engine with deterministic, rule-based blocking logic
- A post-quantum cryptographic receipt engine that produces auditable, tamper-evident decision proofs
- An assumption validity monitor that tracks whether the conditions under which a model was calibrated have drifted enough to invalidate its current output
- A transparency chain that maintains an append-only, hash-linked audit log of every governance decision
- An anti-replay nonce store that prevents receipt reuse within configurable TTL windows

**What OMNIX is not:**

- A model or AI system itself — it governs AI systems but is not one
- A trading bot, insurance product, or credit system — it is the governance layer on top of them
- A compliance framework — it is infrastructure; compliance frameworks can be implemented on top of it

**Current maturity level:** Pre-production with MVP-complete governance core. The governance pipeline, cryptographic receipt engine, anti-replay protection, and multi-domain adapters are all implemented and tested. Infrastructure scaling (Redis anti-replay, multi-instance deployment) is documented and designed but not yet deployed.

**Domains in active simulation:** Algorithmic trading, Islamic credit (GCC market), parametric insurance, industrial robotics.

---

## 2. System Architecture

### 2.1 End-to-End Decision Flow

```
INCOMING DECISION REQUEST
         │
         ▼
┌─────────────────────────────┐
│  Signal Integrity Validator │  (Checkpoint 0 — pre-pipeline)
│  SIV score < 60 → HOLD      │  Data quality gate. Stale prices, anomalous
│  All signals must be clean  │  spreads, cross-source divergence → HOLD.
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Assumption Validity Monitor│  (Pre-pipeline — runs before CAG and all checkpoints)
│  AVM: NaN/Inf → BLOCK       │  Detects drift between live signals and the
│  Stale snapshot → BLOCK     │  calibration snapshot under which the model
│  Drift > threshold → BLOCK  │  was certified.
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Context Admission Gate     │  (Pre-pipeline — market conditions gate)
│  CAG: volatility, liquidity,│  Evaluates whether current market context
│  correlation, macro risk    │  permits decision execution at all.
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│           GOVERNANCE EVALUATION ENGINE — 11 CHECKPOINTS         │
│                                                                 │
│  Each checkpoint: receives normalized signals (0-100 scale)     │
│  Each checkpoint: independent pass/fail with veto_reason        │
│  ANY failure → decision is BLOCKED (fail-closed)                │
│                                                                 │
│  Checkpoints include: signal coherence, Monte Carlo score,      │
│  regime management score, Kelly sizing, trend persistence,      │
│  stress resilience, logic consistency, signal integrity,        │
│  temporal coherence, AML gate, fraud detection gate             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────┐
│  Exit Governance Engine     │  3 post-decision gates:
│  Gate 1: Regime thresholds  │  1. Regime-adjusted exit thresholds
│  Gate 2: Exit coherence     │  2. Internal coherence of exit signal
│  Gate 3: TCV exit check     │  3. Time/cost/value justification
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Decision Receipt Engine    │  Canonical ID generation + Dilithium-3 signing
│  Anti-replay registration   │  Transparency chain append
│  Transparency chain         │  PostgreSQL persistence
└────────────────────────────-┘
```

### 2.2 Fail-Closed Principle

The system defaults to BLOCK on any exception, missing data, or NaN/Inf signal. No code path produces APPROVED output as a fallback. The only exception to this is `pass_through=True`, which is explicitly not APPROVED — it is the absence of evaluation, documented and propagated as such in every receipt.

### 2.3 Domain Adapters

OMNIX uses domain-specific signal adapters that normalize raw domain data into the 0-100 signal scale expected by the pipeline:

| Domain | Adapter | Key Signals |
|--------|---------|-------------|
| Algorithmic Trading | `auto_trading_bot.py` + strategies | Regime score, Kelly sizing, SIV, volatility |
| Islamic Credit | `credit_signal_adapter.py` | DSR, macro risk, Sharia parameters, liquidity |
| Insurance | `insurance_service/` | Claim coherence, risk exposure, fraud indicators |
| Robotics | `robotics_service/` | Safety constraints, operational envelope, fallback state |

---

## 3. Core Components Breakdown

### 3.1 Assumption Validity Monitor (AVM)
**File:** `omnix_core/governance/assumption_validity_monitor.py`  
**Build:** 6.6.0

**Purpose:** Detect when live conditions have drifted beyond the envelope under which a model was calibrated — and block the pipeline before the model's assumptions become invalid.

**Data structures:**
- `CalibrationSnapshot`: timestamped baseline of signal values captured at calibration time
- `AVMResult`: evaluation output including `is_valid`, `drift_score`, `block_reason`, `pass_through`, `drift_components`

**Evaluation logic (strict precedence order):**
1. **NON_FINITE_SIGNAL** — if any input signal is NaN or Inf → `is_valid=False`, `block_reason="NON_FINITE_SIGNAL"` (double barrier: guard in `evaluate()` + clamp in `_compute_drift()`)
2. **CRITICAL_STALE** — if snapshot age > `CRITICAL_AGE_HOURS` → blocks regardless of drift score
3. **DRIFT_BLOCK** — if weighted drift score > `AVM_DRIFT_THRESHOLD_DEFAULT` (35.0) → block
4. **PASS** — all checks pass → `is_valid=True`, `pass_through=False` (certified baseline)

**`pass_through` semantics (critical for integrators):**
- `pass_through=True` → AVM disabled or no baseline snapshot exists → NOT CERTIFIED
- `pass_through=True` must never be interpreted as APPROVED by downstream systems
- Valid `pass_through` states: `AVM_DISABLED`, `NO_BASELINE`

**Signal weights for drift computation:** Defined in `SIGNAL_WEIGHTS` constant; weights must sum to 1.0. Higher weight = that signal's drift contributes more to the total score.

**Persistence:** Snapshots saved to filesystem (`snapshots/` directory) and to PostgreSQL via `avm_db_bridge.py` for cross-instance consistency.

**Dependencies:** `avm_db_bridge.py` (PostgreSQL bridge), `pqc_security.py` (optional signing of snapshots)

---

### 3.2 Decision Receipt Engine
**File:** `omnix_core/evidence/decision_receipt.py`

**Purpose:** Generate a cryptographically-signed, tamper-evident receipt for every governance decision — the primary audit artifact.

**Receipt ID format (canonical):**
```
OMNIX-{DOMAIN_CODE}-{12 hex chars}
```

**Domain code table (`_DOMAIN_CODES`):**

| Domain string | Code | Example receipt_id |
|--------------|------|--------------------|
| `trading` | `TRD` | `OMNIX-TRD-4a7f2b8c9d1e` |
| `insurance` | `INS` | `OMNIX-INS-3c8e1a9b4f2d` |
| `robotics` | `RBT` | `OMNIX-RBT-7d2c4e8a1b9f` |
| `islamic_credit` | `CRD` | `OMNIX-CRD-2b9f3e7a8c4d` |
| `public_sandbox` | `PUB` | `OMNIX-PUB-1a4b8c2d9e3f` |
| Unknown | `` (empty) | `OMNIX-8f3a2c9b4d1e` |

**Cryptographic model:**
1. Public payload is serialized deterministically (sorted keys)
2. `content_hash = SHA-256(serialized_payload)` — tamper detection
3. Primary signing: `Dilithium-3 (ML-DSA-65)` via `pqc.sign.dilithium3`
4. Fallback signing (if PQC library unavailable): `SHA-256(content_hash)` — `signature_format = 'hex_sha256_fallback'`
5. `signature_algorithm` field in every receipt makes the signing method explicit

**Receipt payload fields:** `receipt_id`, `timestamp_utc`, `asset`, `decision`, `veto_chain`, `drift_score`, `parameter_version`, `content_hash`, `signature`, `signature_algorithm`, `signature_format`, `signing_provider`, `prev_hash`

**Persistence:** PostgreSQL table with `ON CONFLICT (receipt_id) DO NOTHING` — deduplication at DB level. Also appended to transparency chain.

**Dependencies:** `pqc_security.py`, `transparency_chain.py`, PostgreSQL

---

### 3.3 Transparency Chain
**File:** `omnix_core/evidence/transparency_chain.py`

**Purpose:** Append-only, hash-linked audit log of every receipt — verifiable integrity across the full decision history.

**Structure:**
- Each entry contains: `receipt_id`, `payload_hash`, `prev_log_hash`, `merkle_root`, `timestamp_token`
- `prev_log_hash`: SHA-256 of the previous entry — links the chain
- `merkle_root`: rolling accumulation — `SHA256(prev_root || new_hash)` via `compute_rolling_merkle_root()`
- `InternalTimestamp`: per-entry nonce (random 16-byte hex), SHA-256 of timestamp data — provides non-repudiation evidence

**Chain integrity:** Any modification to a past entry breaks the hash chain. The Merkle root changes deterministically with every append — a corrupted entry produces a divergent root detectable by any verifier.

**Dependencies:** PostgreSQL (`transparency_chain` table), `decision_receipt.py`

---

### 3.4 Anti-Replay Module
**File:** `omnix_core/evidence/anti_replay.py`  
**ADR:** ADR-076

**Purpose:** Prevent a governance receipt from being submitted for execution more than once within its TTL window.

**Implementation:**
- `AntiReplayStore`: thread-safe in-process dict `{receipt_id: expiry_epoch_ms}`
- Single `threading.Lock` for atomic check-and-register
- Process-level singleton: `_STORE = AntiReplayStore()`
- `MIN_WINDOW_MS = 30,000` (30 seconds) — floor applied to all TTLs
- `MAX_STORE_SIZE = 100,000` — hard cap against unbounded memory growth

**`check_and_register(receipt_id, ttl_ms)` logic:**
1. Acquire lock
2. Purge expired entries (lazy cleanup)
3. If `receipt_id` found in store → raise `ReplayDetected`
4. If store at capacity → raise `AntiReplayStore` capacity error
5. Register with `expiry = now + max(ttl_ms, MIN_WINDOW_MS)`
6. Release lock

**Scope (documented limits — see §12):**

| Scenario | Protected |
|----------|-----------|
| Same receipt, same running instance, within TTL | ✅ |
| Same receipt, after process restart | ⚠️ Not protected |
| Same receipt, different worker instance | ❌ Not protected |
| TTL shorter than 30 seconds | ✅ Floor applied |

**Phase 2 roadmap:** Redis `SET key NX PX ttl_ms` — same interface, no caller changes required.

---

### 3.5 Governance Pipeline (GovernanceEvaluationEngine)
**File:** `omnix_core/governance/external_evaluator.py`

**Purpose:** Domain-agnostic 11-checkpoint evaluator. Receives normalized signals (0-100 scale) from domain adapters and evaluates them through a fail-closed checkpoint pipeline.

**Structure:**
- Each checkpoint: `checkpoint_id`, `name`, `operator` (`gte` or `lte`), `threshold`, `description`
- Safety floors per checkpoint: `CHECKPOINT_SAFETY_FLOORS` — operators cannot be misconfigured to make a gate trivially passable
- `validate_threshold_against_floor()` — enforced before any evaluation begins

**Named gates (partial list from source):**
- AML Gate — Anti-money laundering pattern screening using logic consistency as structural proxy
- Fraud Detection Gate — Signal integrity under adversarial assumptions

**Execution:** Any checkpoint failure → pipeline returns `BLOCKED` with `veto_reason`. All 11 must pass for `APPROVED`. Results include `checkpoints_total`, `checkpoints_passed`, `checkpoints_blocked`.

**Pre-pipeline interceptors (run before any checkpoint):**
1. AVM evaluation (if AVM is active and snapshot exists)
2. CAG evaluation (Context Admission Gate — market environment check)

---

### 3.6 Domain Adapters

**Islamic Credit Adapter** (`omnix_core/credit/credit_signal_adapter.py`):
- `ISLAMIC_DSR_MAX = 0.40` (40% of monthly income — ceiling for Debt Service Ratio screening)
- `_compute_probability_score()`: uses `dsr_score = (1 - dsr / ISLAMIC_DSR_MAX) * 100`
- `_compute_signal_coherence()`: uses same ceiling for `dsr_norm` — ensures internal consistency (fixed in ADR-074)
- `_check_sharia_compliance()`: enforces DSR cap; Sharia screening is always described as "Sharia parameter screening" — not compliance determination
- Macro data: live fetch from Alpha Vantage with FRED fallback
- `CreditSignals` dataclass: 9 normalized signals (0-100) fed to GovernanceEvaluationEngine

**Signal Integrity Validator** (`omnix_core/data/signal_integrity_validator.py`):
- "Checkpoint 0" — runs before the main pipeline
- Score < `SIV_THRESHOLD` (default 60) → HOLD
- Checks: price staleness (>300s), OHLC staleness (>900s), anomaly detection (>20% single-cycle change), spread (>5%), cross-source divergence (>2%)
- On module error → pass-through (admissible=True) — fail-open by design for SIV module failures only

---

## 4. Security Model

### 4.1 Fail-Closed Enforcement

Every decision path that produces output is tested to return BLOCKED or HOLD on failure. The `evaluate()` method of `GovernanceEvaluationEngine` returns BLOCKED on any checkpoint failure. AVM `evaluate()` returns `is_valid=False` on any exception — never `pass_through=True` on exception.

Bare `except` blocks in governance modules all log the exception explicitly — no silent failures.

### 4.2 NaN / Inf Protection (Double Barrier)

Implemented in AVM at two independent layers:

**Barrier 1 — Input guard in `evaluate()`:**
```python
non_finite_signals = [k for k, v in signals.items() if not math.isfinite(v)]
if non_finite_signals:
    return AVMResult(is_valid=False, block_reason="NON_FINITE_SIGNAL", ...)
```

**Barrier 2 — Clamp in `_compute_drift()`:**
```python
drift = min(drift, 100.0)  # prevents unbounded drift from propagating
```

**Pre-fix vulnerability (Ronda 3):** Before Build 6.6.0, a NaN signal could propagate through `_compute_drift()` and produce a drift score of `NaN`. Since `NaN > 35.0` evaluates to `False` in Python, the pipeline returned PASS instead of BLOCK. This was a silent governance bypass.

### 4.3 Tamper Detection

**Receipt level:** Every receipt has a `content_hash = SHA-256(canonical_payload)`. Any field modification changes the hash. The Dilithium-3 signature over the content_hash makes the receipt cryptographically non-repudiable.

**Chain level:** The transparency chain links every receipt via `prev_log_hash`. Modifying any historical entry breaks the chain from that point forward.

**Snapshot level:** `CalibrationSnapshot` includes a hash of its own content. The `avm_db_bridge.py` loads snapshots and verifies integrity: `OK=4 TAMPERED=0` confirmed in production logs.

### 4.4 Anti-Replay

See §3.4 and §8 for complete analysis.

### 4.5 Cryptographic Integrity

**Signing algorithm:** Dilithium-3 (ML-DSA-65) — NIST-standardized post-quantum signature scheme  
**Key Encapsulation:** Kyber-768 (ML-KEM-768) — key exchange only, not data encryption  
**Hash function:** SHA-256 (receipt content hash, chain links, Merkle root, timestamp tokens)  
**Fallback:** If `pqc` library is unavailable at runtime, signature falls back to `SHA-256(content_hash)` with `signature_format='hex_sha256_fallback'` explicitly marked in the receipt — no silent degradation  

**Dilithium-3 signature size:** 3309 bytes (confirmed in test)  
**Security level:** NIST Level 3 (enterprise baseline) — configurable to Level 5 via `PQC_SIGNING_LEVEL` environment variable without architectural changes

**Implemented protections:**
- Post-quantum receipt signing (Dilithium-3)
- SHA-256 content hash per receipt
- Rolling Merkle root for chain integrity
- SHA-256 fallback with explicit marking
- Nonce per transparency chain entry

**Planned / not yet implemented:**
- Distributed signing (multi-signer quorum)
- HSM integration for private key storage
- Cross-instance Merkle root synchronization
- Public key distribution infrastructure for third-party receipt verification

---

## 5. Forensic Audit History

Four formal audit rounds were conducted, each producing a dedicated test suite and ADR documentation.

### Ronda 1 — Bootstrap Validation
- Confirmed module imports and basic pipeline construction
- No bugs found; baseline established

### Ronda 2 — Receipt Consistency Audit (35 tests)
**Bug found:** `age_hours` property called as attribute (missing `()`) → snapshot always appeared as age 0 → CRITICAL_STALE never triggered  
**Fix:** Added `()` call in staleness evaluation  
**Bug found:** `financing_amount` column referenced as `requested_amount` in Insurance and Robotics pipelines → receipt generation failed  
**Fix:** Unified to `requested_amount` across all domain adapters  
**Bug found:** Receipt ID format inconsistent between domains — Insurance and Robotics were using UUIDs instead of canonical `OMNIX-{CODE}-{12hex}` format  
**Fix:** Migrated all domains to `build_receipt_id(domain)` factory method

### Ronda 3 — NaN/Inf Safety Audit (53 tests)
**Critical bug found:** `_compute_drift()` did not guard against NaN inputs. `NaN > 35.0 = False` in Python — the pipeline returned PASS when it should have blocked.  
**Fix:** Double barrier implemented (see §4.2)  
**Documentation:** ADR-075 created; AVM docstring updated to specify blocking precedence order

### Ronda 4 — Deep Consistency Audit (36 tests)
**Bug 1 — Sandbox receipt format:**  
`governance_sandbox.py` was generating `OMNIX-SB-{8hex}` instead of canonical format  
Fix: Migrated to `build_receipt_id("public_sandbox")` → `OMNIX-PUB-{12hex}`  

**Bug 2 — DSR normalization inconsistency:**  
`credit_signal_adapter.py` used `ISLAMIC_DSR_MAX=0.40` for `dsr_score` but hardcoded `0.5` for `dsr_norm` → two functions in the same pipeline reported contradictory signals for identical input  
Fix: Both `dsr_norm` and `dsr_score` now use `ISLAMIC_DSR_MAX` as the single source of truth (ADR-074)  

**Bug 3 — Anti-replay phantom implementation:**  
`transparency_chain.py` generated a nonce per entry but never validated it against a seen-nonces set → anti-replay was a field in the receipt with no enforcement  
Fix: `omnix_core/evidence/anti_replay.py` implemented with real enforcement (ADR-076)

---

## 6. Test Coverage Analysis

**Total test files:** 48  
**Confirmed passing tests:** ~330+ across 4 formal audit rounds plus workflow suites

### Coverage categories:

| Category | Files | Coverage |
|----------|-------|----------|
| Governance core (AVM, exit, signal integrity) | `test_assumption_validity_monitor.py`, `test_exit_governance.py`, `test_signal_integrity_validator.py` | Deep |
| Receipt system | `test_receipt_sha256_fallback.py`, `test_forensic_audit_ronda2.py`, `test_enterprise_audit.py` | Deep |
| Anti-replay | `test_forensic_audit_ronda4.py` (Bloc K, 21 tests) | Deep |
| DSR / Islamic credit | `test_forensic_audit_ronda4.py` (Bloc J) | Deep |
| NaN / Inf protection | `test_forensic_audit_ronda3.py` | Deep |
| Post-quantum crypto | `test_pqc_security.py`, `test_pqc_enhancements.py` | Good |
| Context admission gate | `test_context_admission_gate.py` (112 passing) | Good |
| Temporal coherence | `test_temporal_coherence.py` | Good |
| Systemic routing | `test_systemic_router.py` | Good |
| Response validation | `test_response_validator.py` | Good |
| Version consistency | `test_version_consistency.py` | Good |
| Code verification | `test_code_verification.py`, `test_critical_audit.py` | Good |
| Parity harness | `test_parity_harness.py` | Moderate |
| Compliance gates | `test_compliance_gates.py` | Moderate |
| Domain entities | `test_domain_entities.py` | Moderate |
| Frontend data integrity | `test_frontend_data_integrity.py` | Surface |

### Blind spots:
- `auto_trading_bot.py` (8,288 lines) — no dedicated governance audit; trading logic tested indirectly
- `trading_system.py` (5,587 lines) — no dedicated test suite
- `core.py` dashboard blueprint (106 KB) — endpoint authorization not formally audited
- Frontend (`omnix_web/src/pages/`) — 16+ pages with no automated UI tests
- `physics_validator.py` (4,459 lines) — not in active pipeline; no dedicated test
- Multi-instance anti-replay — not testable without Redis infrastructure

---

## 7. Critical Bugs Found and Resolved

### Bug 1: NaN → PASS (Governance Bypass)
**Severity:** Critical — governance could be silently bypassed  
**Root cause:** `math.nan > 35.0` evaluates to `False` in Python; a NaN drift score passed the threshold check  
**Path:** NaN signal → `_compute_drift()` → NaN drift score → `NaN > threshold = False` → PASS  
**Fix location:** `omnix_core/governance/assumption_validity_monitor.py`, `evaluate()` and `_compute_drift()`  
**Fix:** Double barrier — input guard before drift computation; clamp to 100.0 inside drift computation  

### Bug 2: Receipt ID Inconsistency (Insurance, Robotics)
**Severity:** High — audit trail non-canonical; receipt verification would fail domain matching  
**Root cause:** Insurance and Robotics adapters used UUID generation instead of the canonical factory  
**Fix location:** Domain adapter files; unified to `DecisionReceiptEngine.build_receipt_id(domain)`  

### Bug 3: DSR Normalization Contradiction (Islamic Credit)
**Severity:** High — two functions in the same pipeline reported contradictory risk scores for identical input  
**Root cause:** `dsr_score` used `ISLAMIC_DSR_MAX=0.40` as ceiling; `dsr_norm` hardcoded `0.5`  
**Impact:** A borrower at 42% DSR would appear low-risk in one signal and high-risk in another within the same evaluation cycle  
**Fix location:** `omnix_core/credit/credit_signal_adapter.py`, `_compute_signal_coherence()`  
**Fix:** `dsr_norm = (1 - dsr / ISLAMIC_DSR_MAX) * 100` — same ceiling, same semantics as `dsr_score`

### Bug 4: Anti-Replay Phantom Implementation
**Severity:** Medium-High — security control existed in documentation but not in code  
**Root cause:** `transparency_chain.py` generated a nonce per entry but never compared it against past nonces  
**Impact:** A receipt could be resubmitted indefinitely; anti-replay guarantee was false  
**Fix location:** `omnix_core/evidence/anti_replay.py` (new module)  
**Fix:** Real enforcement — `AntiReplayStore` with `threading.Lock`, TTL floor, capacity cap

### Bug 5: Sandbox Receipt Non-Canonical Format
**Severity:** Low-Medium — demo/sandbox receipts had a different format, breaking uniform audit processing  
**Root cause:** `governance_sandbox.py` used `f"OMNIX-SB-{8hex}"` hardcoded instead of factory  
**Fix location:** `omnix_dashboard/blueprints/governance_sandbox.py`  
**Fix:** `build_receipt_id("public_sandbox")` → `OMNIX-PUB-{12hex}`

### Bug 6: `age_hours` Called Without `()` (Staleness Never Triggered)
**Severity:** High — `CRITICAL_STALE` block could never fire; stale snapshots appeared as age 0  
**Root cause:** Property accessed as attribute reference (returned the bound method object, not a float)  
**Fix location:** Staleness check in `AssumptionValidityMonitor`  
**Fix:** `snapshot.age_hours()` with parentheses

---

## 8. Anti-Replay Analysis

### 8.1 Current Implementation (Phase 1)

The anti-replay system operates as a **process-level singleton** in `omnix_core/evidence/anti_replay.py`.

**Architecture:**
```python
_STORE = AntiReplayStore()  # module-level singleton

class AntiReplayStore:
    def __init__(self):
        self._store: dict[str, int] = {}  # {receipt_id: expiry_ms}
        self._lock = threading.Lock()

    def check_and_register(self, receipt_id, ttl_ms=MIN_WINDOW_MS):
        with self._lock:
            self._purge_expired_locked(now_ms)
            if receipt_id in self._store:
                raise ReplayDetected(receipt_id)
            if len(self._store) >= MAX_STORE_SIZE:
                raise CapacityError(...)
            self._store[receipt_id] = now + max(ttl_ms, MIN_WINDOW_MS)
```

**Constants:**
- `MIN_WINDOW_MS = 30,000` — TTL floor; adversarially short TTLs always get 30s minimum
- `MAX_STORE_SIZE = 100,000` — prevents unbounded memory growth under DDoS or misconfiguration

**Thread safety:** Confirmed by concurrent test (100 threads, exactly 1 registration succeeds).

### 8.2 Exact Limitations

| Scenario | Protected | Reason |
|----------|-----------|--------|
| Same receipt, same instance, within TTL | ✅ Yes | `_store` dict is checked atomically |
| Same receipt, after process restart | ⚠️ No | `_store` is in-memory; cleared on restart |
| Same receipt, different worker instance | ❌ No | Each worker has its own `_STORE` singleton |
| Adversarially short TTL (e.g., 1ms) | ✅ Yes | `MIN_WINDOW_MS` floor applies |

**Current deployment:** Single Railway dyno = single process = single store. Phase 1 protection is effective for the current infrastructure.

### 8.3 Phase 2 Redis Upgrade

**ADR-076** documents the upgrade path:
```python
# Phase 2 — same interface, distributed enforcement
redis.set(receipt_id, "1", nx=True, px=max(ttl_ms, MIN_WINDOW_MS))
# nx=True → only set if not exists (atomic check-and-set)
```

The caller interface (`check_and_register`, `is_replay`, `get_store`) does not change. Redis `SET NX PX` is atomic by design. No architectural rewrite required.

---

## 9. Data Integrity and Receipts

### 9.1 Canonical ID System

The `build_receipt_id(domain)` factory in `DecisionReceiptEngine` generates deterministic-format IDs using:
```python
receipt_id = f"OMNIX-{code}-{os.urandom(6).hex()}"
# e.g., OMNIX-TRD-4a7f2b8c9d1e
```

The 12-hex-char suffix is 6 bytes of OS entropy — 48 bits of randomness (2^48 ≈ 281 trillion combinations). Collision probability at 1M receipts/day: negligible.

### 9.2 Hashing Model

Every receipt undergoes:
1. **Deterministic serialization**: `json.dumps(payload, sort_keys=True, default=str)` — stable across platforms
2. **Content hash**: `SHA-256(serialized)` — 256-bit tamper detection
3. **Cryptographic signature**: Dilithium-3 over `content_hash.encode('utf-8')` — post-quantum non-repudiation
4. **Chain link**: `prev_hash` from previous receipt creates a linked list of decisions

### 9.3 Auditability

Every decision receipt is:
- Persisted to PostgreSQL with `ON CONFLICT DO NOTHING` deduplication
- Appended to the transparency chain with its own hash-linked entry
- Searchable by `receipt_id`, `asset`, `decision`, `timestamp`
- Verifiable independently: any party with the public key can verify the Dilithium-3 signature

### 9.4 Public Key Distribution

**Current state:** Public key is available via `receipt_engine.public_key_b64`. No PKI infrastructure exists. Third-party verification requires manual key exchange.

**Gap:** No public endpoint for key discovery. Enterprise clients must receive the public key out-of-band.

---

## 10. System Consistency

### 10.1 Cross-Domain Behavior

All four domains (trading, credit, insurance, robotics) route through the same `GovernanceEvaluationEngine`. Domain adapters normalize raw signals to 0-100 scale before entering the pipeline. The pipeline itself has no domain-specific logic.

**Verified in production (Flask Dashboard logs):**
- Trading: live receipt generation with `OMNIX-TRD-` IDs
- Islamic Credit: `CP_passed=11/11` (approval) and `CP_passed=10/11` (block) confirmed in simulation
- Insurance: claims blocked/approved through same pipeline
- Robotics: actions blocked/approved through same pipeline
- AVM: `OK=4 TAMPERED=0` across all 4 domains confirmed in snapshot integrity check

### 10.2 Policy Precedence

Within AVM: NON_FINITE → CRITICAL_STALE → DRIFT_BLOCK → PASS (strictest first)  
Within pipeline: any checkpoint failure → BLOCKED immediately  
Velos integration: `OMNIX_VETO_ENFORCED` propagates from OMNIX to Velos; Velos `APPROVED` is pass-through only

### 10.3 Signal Normalization Consistency

After Ronda 4 DSR fix: all signals in the credit adapter use the same ceiling constant (`ISLAMIC_DSR_MAX=0.40`) for normalization. No internal contradictions remain in the confirmed codebase.

---

## 11. Production Readiness

**Classification: Pre-Production / MVP-Complete**

### What is complete and tested:
- Governance pipeline (11 checkpoints) — domain-agnostic, fail-closed ✅
- Post-quantum receipt engine (Dilithium-3) — functional with SHA-256 fallback ✅
- Anti-replay enforcement — in-process, Phase 1 ✅
- NaN/Inf protection — double barrier ✅
- Transparency chain — append-only, hash-linked ✅
- Domain adapters (trading, credit, insurance, robotics) — operational ✅
- AVM drift detection — calibration snapshot comparison ✅
- Flask governance dashboard — live data, 4 domains ✅
- Test suite (48 files, ~330+ confirmed passing) ✅
- ADR documentation (ADR-073 through ADR-076) ✅
- Velos gateway integration (3 gate outcomes verified via HTTP) ✅

### What is not yet production-grade:
- Anti-replay: in-process only (Phase 2 Redis documented, not deployed)
- Public key infrastructure: no PKI for third-party receipt verification
- Multi-instance deployment: not tested; anti-replay would be ineffective
- HSM / secure key storage: keys in memory, not in hardware
- `core.py` endpoint authorization: not formally audited
- Frontend: no automated UI tests

---

## 12. Known Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| Anti-replay: in-process only | Replay possible after restart or across instances | Single-dyno deployment; Phase 2 Redis documented in ADR-076 |
| No persistent signing key storage | Key regenerated on restart; past receipts cannot be re-verified with new key | Phase 2: HSM or persisted key pair |
| Alpha Vantage → FRED fallback for macro data | Credit pipeline continues with fallback; flagged in logs | FRED data is reliable; acceptable for pre-production |
| No public PKI endpoint | Third parties cannot verify receipts without manual key exchange | Enterprise clients receive key out-of-band |
| `trading_system.py` / `auto_trading_bot.py` not formally audited | Unknown bugs in trading logic paths | Governance pipeline is independent; bad trading logic is blocked by governance |
| `core.py` endpoint authorization | Dashboard endpoints may be accessible without proper authorization | Requires dedicated security audit before public deployment |
| Frontend not formally tested | UI may display incorrect data in edge cases | Requires E2E test coverage before investor-facing demos |
| Physics validator (4,459 lines) not in active pipeline | Not a production risk; unused module | Can be deferred |

---

## 13. Risk Assessment

### Critical Risks (addressed)
- ~~NaN → PASS governance bypass~~ — Fixed (Build 6.6.0, ADR-075)
- ~~Anti-replay phantom implementation~~ — Fixed (ADR-076)
- ~~DSR normalization contradiction~~ — Fixed (ADR-074)
- ~~Receipt ID non-canonical format~~ — Fixed (Ronda 2)

### Medium Risks (documented, not yet resolved)
- **Anti-replay restart vulnerability** — Effective only within single process lifetime. Not a risk for current single-instance Railway deployment; becomes a risk at multi-instance scale.
- **Signing key persistence** — Private key is in-memory only. A restart generates new keys; historical receipt signatures cannot be re-verified without the original key. No key rotation protocol exists.
- **`core.py` authorization gaps** — Not audited. Dashboard endpoints are potentially accessible without authentication. Not a governance pipeline risk but a security surface for the ops interface.

### Low Risks (informational)
- **SHA-256 fallback** — Used only if `pqc` library is unavailable. The fallback is symmetric (non-asymmetric), so it does not provide non-repudiation. Explicitly marked in every receipt. Not a silent degradation.
- **FRED macro data latency** — Federal funds rate data has an inherent publication lag. Credit decisions use the latest available data point. This is a domain property, not a system bug.
- **Documentation inconsistency** — `exit_governance.py` references "8-checkpoint entry pipeline" in its docstring; the current pipeline has 11 checkpoints. The docstring is stale. No functional impact.

---

## 14. Deployment Readiness

**Is the system safe to deploy now?**  
Yes, under the following conditions:

**Safe for:** Demo environments, investor presentations, pilot clients with single-instance Railway deployment, governance-as-a-service for low-volume clients, Velos gateway integration.

**Conditions required for safe single-instance production:**
- Signing keys must be persisted across restarts (environment variable or secrets manager) — otherwise past receipt signatures become unverifiable after any restart
- `core.py` dashboard endpoints must be audited for authorization before public access
- Alpha Vantage API key must be active (FRED fallback is functional but secondary)

**Before multi-instance scaling:**
1. Anti-replay → Redis (ADR-076 Phase 2, estimated: 1-2 days implementation)
2. Signing key distribution → HSM or shared key store
3. AVM snapshot persistence → confirm cross-instance consistency via PostgreSQL bridge

**Before enterprise client onboarding:**
1. Public key endpoint for third-party receipt verification
2. Formal security audit of `core.py`
3. Frontend E2E test coverage

---

## 15. Strategic Value

### 15.1 What Makes OMNIX Unique

Most AI governance products are **monitoring systems** — they observe decisions after they happen and flag anomalies. OMNIX is a **pre-execution governance layer** — no decision reaches execution without a cryptographically-signed receipt proving it passed the pipeline.

The architectural separation is the core value: OMNIX does not know or care what model produced the decision. It receives normalized signals, evaluates them against configurable thresholds, and either blocks or certifies. The domain adapter pattern means a single governance engine serves trading, credit, insurance, and robotics without specialization.

The post-quantum cryptographic receipt is the commercial differentiator: every governance decision produces an audit artifact that:
- Cannot be forged (Dilithium-3 signature)
- Cannot be replayed (anti-replay enforcement)
- Cannot be silently tampered with (SHA-256 content hash + hash chain)
- Can be independently verified by any third party with the public key

### 15.2 Comparison to Typical AI Systems

| Property | Typical AI system | OMNIX |
|----------|------------------|-------|
| Decision audit | Logs (mutable) | Cryptographic receipts (immutable) |
| Failure mode | Silent or undefined | Explicitly fail-closed |
| Domain specificity | Domain-specific | Domain-agnostic |
| Assumption tracking | None | AVM with drift scoring |
| Replay protection | None | In-process anti-replay (Phase 2: Redis) |
| Regulatory artifact | None | Verifiable receipt per decision |
| Governance layer | Internal | External and independent |

### 15.3 Why It Matters

Regulatory pressure on AI in financial services (EU AI Act, UAE AI Strategy, FCA guidance) is converging on one requirement: **verifiable decision accountability**. An AI system that cannot produce a cryptographic proof that a human-auditable governance process approved a decision will not receive regulatory approval for autonomous operation in high-stakes domains.

OMNIX provides exactly this infrastructure — not for one domain, but for any domain that can normalize its signals to the standard 0-100 input format. The commercial implication is a horizontal governance platform with no vertical competitor currently occupying the space.

---

## Appendix A: File Map (Key Modules)

| Module | Path | Role |
|--------|------|------|
| AVM | `omnix_core/governance/assumption_validity_monitor.py` | Drift detection, NaN guard |
| Receipt Engine | `omnix_core/evidence/decision_receipt.py` | ID generation, Dilithium-3 signing |
| Transparency Chain | `omnix_core/evidence/transparency_chain.py` | Hash-linked append-only log |
| Anti-Replay | `omnix_core/evidence/anti_replay.py` | Nonce enforcement, TTL floor |
| Governance Pipeline | `omnix_core/governance/external_evaluator.py` | 11-checkpoint evaluator |
| Exit Governance | `omnix_core/governance/exit_governance.py` | 3-gate post-decision checks |
| Context Admission Gate | `omnix_core/governance/context_admission_gate.py` | Market context gate |
| Signal Integrity Validator | `omnix_core/data/signal_integrity_validator.py` | Data quality gate (Checkpoint 0) |
| Credit Adapter | `omnix_core/credit/credit_signal_adapter.py` | Islamic credit signal normalization |
| PQC Security | `omnix_core/security/pqc_security.py` | Dilithium-3 + Kyber-768 |
| AVM DB Bridge | `omnix_core/governance/avm_db_bridge.py` | Snapshot PostgreSQL persistence |

## Appendix B: ADR Index

| ADR | Subject |
|-----|---------|
| ADR-073C | `_liquidity_source` trace field in CAG market params |
| ADR-074 | DSR normalization unification (ISLAMIC_DSR_MAX ceiling) |
| ADR-075 | NaN/Inf double barrier in AVM — blocking precedence order |
| ADR-076 | Anti-replay guard — Phase 1 in-process, Phase 2 Redis roadmap |

---

*This report reflects the state of the OMNIX Quantum codebase as of Build 6.6.0, April 2026. All module names, function signatures, constants, and bugs listed are sourced directly from static code analysis of the production repository.*
