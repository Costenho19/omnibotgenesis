# OMNIX Decision Governance Infrastructure
## Governance Architecture Reference

**Version:** 6.6.0 
**Author:** Harold Nunes, OMNIX QUANTUM LTD 
**Last updated:** 2026-04-09 (post Forensic Audit Ronda 3) 
**Raises:** $500K pre-seed @ $3M valuation | 

---

## 1. Overview

OMNIX is a domain-agnostic Decision Governance Infrastructure. It wraps any
high-stakes automated decision (trading, Islamic credit, insurance, robotics) in an
11-checkpoint pipeline and issues a post-quantum cryptographically signed receipt
for every outcome.

The system is designed around one principle: **when in doubt, block**.

---

## 2. Pipeline Architecture

```
Input Signals
 │
 ▼
┌─────────────────────────────────────────────────────┐
│ AVM — Assumption Validity Monitor (ADR-064/075) │
│ ┌──────────────────────────────────────────────┐ │
│ │ Guard 1: NON_FINITE_SIGNAL (NaN/Inf → BLOCK) │ │
│ │ Guard 2: CRITICAL_STALE (age → BLOCK) │ │
│ │ Guard 3: DRIFT_BLOCK (drift → BLOCK) │ │
│ └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
 │ is_valid=True + pass_through=False (certified)
 ▼
┌─────────────────────────────────────────────────────┐
│ CAG — Context Admission Gate (ADR-050) │
└─────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────┐
│ 11 Checkpoints (CP-1 to CP-11) │
│ Each checkpoint: signal evaluation + threshold gate │
└─────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────┐
│ TIE — Transaction Integrity Engine (ADR-053) │
│ Generates post-quantum signed receipt │
└─────────────────────────────────────────────────────┘
 │
 ▼
Decision: APPROVED / BLOCKED / HOLD
+ Receipt: OMNIX-{DOMAIN}-{12hex} (canónico)
+ PQC signature (Dilithium)
```

---

## 3. AVM — Assumption Validity Monitor

### 3.1 Blocking policy (precedence, strictest wins)

| Priority | Check | Condition | Outcome |
|----------|-------|-----------|---------|
| 1 | NON_FINITE_SIGNAL | Any signal is NaN or Inf | `is_valid=False`, `block_reason=NON_FINITE_SIGNAL` |
| 2 | CRITICAL_STALE | `age_hours > critical_age_hours` (default: 720h) | `is_valid=False`, `drift_score=100.0` |
| 3 | DRIFT_BLOCK | `weighted_drift > effective_threshold` | `is_valid=False`, `block_reason` includes snapshot_id |
| 4 | PASS | All checks clear | `is_valid=True`, `pass_through=False` |

### 3.2 pass_through semantics

`pass_through=True` = AVM had **no baseline**. This is **NOT** certification.

| `is_valid` | `pass_through` | Correct interpretation |
|------------|----------------|------------------------|
| `True` | `False` | **CERTIFIED** — drift verified, assumptions valid |
| `False` | `False` | **BLOCKED** — explicit reason in `block_reason` |
| `True` | `True` | **NON_CERTIFIED** — no snapshot, no comparison possible |

**Rule for downstream integrators:** Never treat `pass_through=True` as approval.
In production domains (trading, credit, insurance, robotics), `pass_through=True`
must be treated as a governance gap requiring recalibration.

### 3.3 Non-finite signal policy (ADR-075)

**Why this matters:** Python evaluates `NaN > threshold` as `False`. Without a
guard, NaN signals silently produce `is_valid=True`.

**Fix:** Two-layer defense:
1. `evaluate()` rejects any non-finite signal before calling `_compute_drift()`
2. `_compute_drift()` clamps non-finite values to `100.0` (maximum drift)

Any non-finite signal → `NON_FINITE_BLOCK`, `is_valid=False`, `pass_through=False`.

### 3.4 Drift score calculation

```
drift_score = Σ (weight_i × |current_i - baseline_i|) / Σ weight_i

Signal weights (must sum to 1.0):
 probability_score: 0.25
 signal_coherence: 0.25
 risk_exposure: 0.20 (amplified ×1.4 when increasing)
 stress_resilience: 0.15
 trend_persistence: 0.10
 logic_consistency: 0.05

effective_threshold = drift_threshold × (1 - 0.3 × age_overage_ratio)
```

---

## 4. PostgreSQL Persistence (ADR-074)

### 4.1 Tables

| Table | Purpose |
|-------|---------|
| `avm_calibration_snapshots` | One row per domain. SHA-256 hash, versioning, is_active |
| `avm_baseline_change_log` | Immutable audit log. Every SEED/RECALIBRATE/RESTORE logged |

### 4.2 Integrity chain

```
baseline_signals (dict)
 → json.dumps(sort_keys=True, separators=(',',':'))
 → SHA-256
 → baseline_hash (stored in DB)

On load:
 recompute hash → compare with stored
 match → integrity_status = OK
 miss → integrity_status = TAMPERED → snapshot rejected
 empty → integrity_status = LEGACY_NO_HASH → warning
```

### 4.3 Versioning

- `SEED` action: keeps `version` unchanged (no increment)
- `RECALIBRATE` action: increments `version` by 1, requires non-empty `reason`
- `is_active=TRUE` always (single active snapshot per domain via PRIMARY KEY)

### 4.4 Fail-closed modes

| `AVM_FAIL_CLOSED` | DB offline | TAMPERED snapshot |
|-------------------|------------|-------------------|
| `false` (default) | DEGRADED warning, use JSON fallback | Rejected, logged |
| `true` | `RuntimeError` — halt | `RuntimeError` — halt |

---

## 5. Receipt ID Canonical Format

All 8 domains produce receipts via `DecisionReceiptEngine.build_receipt_id(domain)`:

| Domain | Code | Format |
|--------|------|--------|
| `trading` | TRD | `OMNIX-TRD-{12hex}` |
| `islamic_credit` | CRD | `OMNIX-CRD-{12hex}` |
| `insurance` | INS | `OMNIX-INS-{12hex}` |
| `robotics` | RBT | `OMNIX-RBT-{12hex}` |
| `medical_ai` | MED | `OMNIX-MED-{12hex}` |
| `autonomous_agent` | AGT | `OMNIX-AGT-{12hex}` |
| `public_sandbox` | PUB | `OMNIX-PUB-{12hex}` |
| unknown | — | `OMNIX-{12hex}` |

The 12-hex suffix is UUID4 (cryptographically random). No collisions observed in
500 concurrent generation tests.

**Rule:** All simulators MUST call `DecisionReceiptEngine.build_receipt_id(domain)`.
Never hardcode `f"OMNIX-{CODE}-{uuid.uuid4()...}"` directly. Enforced by tests
`test_B7` and `test_B8` in `test_forensic_audit_ronda3.py`.

---

## 6. Governance Domains

| Domain | Simulator | Cycle | Batch | DB Table |
|--------|-----------|-------|-------|----------|
| Trading | `omnix_core/trading/` | 300s | varies | `shadow_trade_events` |
| Islamic Credit | `omnix_core/credit/credit_simulator.py` | 300s | 4-10 | `credit_applications` |
| Insurance | `omnix_core/insurance/insurance_simulator.py` | 300s | 4-10 | `insurance_claims` |
| Robotics | `omnix_core/robotics/robotics_simulator.py` | 300s | 6-15 | `robot_actions` |
| Medical AI | `omnix_core/medical/medical_simulator.py` (roadmap) | 300s | 4-10 | `medical_decisions` |
| Autonomous Agent | `omnix_core/agents/agent_simulator.py` (roadmap) | 300s | 4-10 | `agent_actions` |

**Sharia language rule:** Always "Sharia parameter screening" — never "Sharia compliance".

---

## 7. Forensic Audit Summary

| Audit | Tests | Critical bugs | Status |
|-------|-------|---------------|--------|
| Ronda 1 (pre-session) | 59 | age_hours() without (), wrong column names | Fixed |
| Ronda 2 (2026-04-09) | 36 | _BRIDGE_ONLY_FIELDS, receipt_id unification | Fixed |
| Ronda 3 (2026-04-09) | 53 | NaN → PASS bypass (CRITICAL), pass_through semantics | Fixed |
| **Total** | **148** | **0 open critical** | **DEPLOYABLE** |

### Ronda 3 — hallazgos por bloque

| Ref | Hallazgo | Severidad | Estado |
|-----|----------|-----------|--------|
| H1-H4 | NaN/Inf en señal → PASS silencioso (drift=NaN > threshold = False) | **CRÍTICA** | ✅ Corregido en evaluate() + _compute_drift() |
| H8 | AVM internal exception propagates to caller (caller must treat as BLOCK) | Alta | ✅ Documentado en ADR-075 §4.4 |
| F1 | CRITICAL_STALE tiene precedencia absoluta sobre drift=0 | Alta | ✅ Confirmado correcto |
| F3 | pass_through=True no significa CERTIFIED | Alta | ✅ Documentado, contrato establecido |
| D2 | Contadores restored/tampered precisos en restore_to_json | Media | ✅ Confirmado correcto |
| D3 | Restore idempotente (3 veces = mismo JSON) | Media | ✅ Confirmado correcto |
| A1 | 500 receipt_ids paralelos: 0 colisiones | Baja | ✅ UUID4 es threadsafe |
| C4 | NaN en 1 de 6 señales bloquea (no bypass por otras 5 buenas) | **CRÍTICA** | ✅ Corregido |
| E5 | Modificar baseline_signals con hash original → TAMPERED detectado | Alta | ✅ SHA-256 cadena íntegra |

### Riesgo residual

| Riesgo | Bloquea deploy | Mitigación |
|--------|----------------|------------|
| pass_through=True interpretado como CERTIFIED por código externo | No (si este repo es la fuente única) | Documentado + tests E/F |
| Race condition en restore_to_json + evaluate concurrente | No (improbable en producción single-instance) | Test A3 pasa; atomicidad en roadmap |
| Señales fuera de rango [0, 100] no bloqueadas | No (clamped a 100.0 = max drift → BLOCK) | Test C3 documenta comportamiento |

---

## 8. Deploy Checklist

- [x] 148/148 tests pasando
- [x] NaN/Inf bypass corregido (ADR-075)
- [x] receipt_id canónico en 6 dominios (ADR-074)
- [x] Versioning + SHA-256 integrity en PostgreSQL (ADR-074)
- [x] Fail-closed configurable `AVM_FAIL_CLOSED` (ADR-074)
- [x] Dashboard mostrando `drift_status: STABLE`, `integrity: OK`
- [x] `last_decision` con datos reales desde credit_applications
- [x] Documentación ADR-075 creada
- [ ] `bash push.sh` → Railway (pendiente autorización Harold)

---

## 8b. Anti-Replay Guard — Scope and Limits (ADR-076)

> **Anti-replay enforcement is currently scoped to a single running instance
> and in-memory nonce store. Protection is effective for same-instance replay
> attempts within the configured TTL window, but does not yet survive process
> restarts or multi-instance routing.**

| Scenario | Protected |
|----------|-----------|
| Same receipt twice — same running instance | ✅ `ReplayDetected` raised |
| Same receipt after process restart (within TTL) | ⚠️ Not protected — store cleared |
| Same receipt to a different worker | ❌ Not protected — each worker has own store |
| TTL shorter than 30s minimum floor | ✅ Effective window always ≥ 30s |

**Phase 2 trigger:** Railway scaling to > 1 dyno → swap store to Redis `SET NX PX`. Interface unchanged.

Contract language for external integrators (Velos):
> OMNIX anti-replay (Phase 1) prevents same-instance receipt reuse within a minimum 30-second window, effective for the current single-dyno deployment. Phase 2 extends this to persistent multi-instance coverage via Redis.

---

## 9. Cryptographic Notes

- **Kyber-768:** KEM (Key Encapsulation Mechanism), NOT encryption. Ver `docs/reference/OMNIX-Kyber-IP-Notice.md`
- **Dilithium:** Firma post-cuántica de los governance receipts
- **SHA-256:** Integridad de calibration snapshots en PostgreSQL
- **UUID4:** Generación de receipt_id (aleatorio, threadsafe, 0 colisiones en 500 paralelos)

---

## 10. Cross-Border Governance — ADR-085 (2026-04-14)

### 10.1 The cross-border semantic problem

W3C VCs + JSON-LD + schema mappings ensure verifiable structure, not semantic equivalence
across jurisdictions. Independent verifiers can validate the same receipt and still arrive
at different regulatory conclusions. This is accurate and expected — no governance system
can guarantee cross-border regulatory equivalence.

OMNIX's response: maximum coverage with transparent scope boundaries.

### 10.2 Three-layer solution

**Layer 1 — Regulatory mapping (10 frameworks, 6 regions)**

Every receipt maps the outcome to all applicable frameworks simultaneously. A verifier in
any target jurisdiction finds their framework inside the receipt without needing OMNIX knowledge.

Frameworks: EU AI Act · GDPR · DORA · FATF · UK FCA/SM&CR · US SEC Rule 15c3-5 ·
MAS Singapore · UAE CBUAE · SAMA Saudi Arabia · FSB G20.

**Layer 2 — Proof scope**

Every receipt contains a `proof_scope` block with explicit lists of:
- `what_this_receipt_proves` — 5 cryptographic facts, all independently verifiable
- `what_this_receipt_does_not_claim` — 4 explicit non-claims, including no cross-border semantic equivalence
- `verifier_guidance` — step-by-step instructions for using the receipt as governance evidence

**Layer 3 — Cross-jurisdiction concordance**

A `cross_jurisdiction_concordance` block shows which frameworks agree on the outcome
and where additional local obligations (FATF STR, UK SM&CR mapping, US Reg SCI) may arise.

### 10.3 Trust score fix (Bug resolved in ADR-085)

`jurisdiction_semantics` now computed BEFORE `trust_score` — the +0.10 bonus is applied
correctly. Maximum reachable trust score is now 1.0 (was capped at 0.90).

### 10.4 Key consistency fix (Bug resolved in ADR-085)

`gov_blueprint._load_engine()` now imports `DecisionReceiptEngine` directly (not via
`spec_from_file_location`). Trust registry and governance API share the same keypair.
Independent verification against published public key now succeeds for all receipts.

### 10.5 Reference documents

- `docs/adr/ADR-085-cross-border-semantic-governance.md` — Technical decision record
- `docs/compliance/CROSS_JURISDICTION_GOVERNANCE.md` — Institutional reference document

---

## 11. Cryptographic Standards Alignment

| Algorithm | NIST Standard | Status | Active Since |
|-----------|---------------|--------|--------------|
| CRYSTALS-Dilithium-3 (ML-DSA-65) | FIPS 204 | Operational — production baseline | Nov 2025 |
| CRYSTALS-Dilithium-5 (ML-DSA-87) | FIPS 204 | Available — high-assurance configuration | Mar 2026 |
| CRYSTALS-Kyber-768 (ML-KEM-768) | FIPS 203 | Operational — key encapsulation | Nov 2025 |

---

*OMNIX QUANTUM LTD — Decision Governance Infrastructure* 
*Harold Nunes | Founder | OMNIX QUANTUM LTD, UK* 
*71-75 Shelton Street, Covent Garden, London, WC2H 9JQ* 
*
