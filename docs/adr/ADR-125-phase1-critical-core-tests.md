# ADR-125 — Phase 1: Minimal Critical Core Tests

**Status:** ACCEPTED — Implemented 25 Apr 2026  
**Author:** Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD  
**Scope:** `tests/test_phase1_critical_core.py`  
**Plan Reference:** Institutional Readiness Plan — Fase 1 (Surgical Test Coverage)  
**Previous coverage:** < 1% on legacy core (ADR-001 CRITICAL risk)

---

## 1. Context

Following the completion of ADR-116 (Fail-Closed Enforcement), ADR-122 (Execution Boundary Hardening), ADR-123 (API Security), and ADR-124 (Oversight Surface Engine), the OMNIX test suite covered governance policy, security hardening, and the OSE layer well — but had a critical gap: the three foundational modules that every production deployment depends on were not covered by surgical behavioral tests:

| Module | Gap |
|---|---|
| `GovernanceEvaluationEngine` (`external_evaluator.py`) | No test for happy path / fail path on 11-checkpoint pipeline |
| `DecisionReceiptEngine` (`decision_receipt.py`) | No test for receipt generation, hash integrity, or cross-restart key stability |
| `ExecutionProtocol` boundary (`execution_protocol.py`) | No test for `should_execute` semantics or fallback behavior |

**Without these tests:** Any code change in these modules could break production governance silently. Deploy confidence was zero for the core pipeline.

**Phase 1 objective:** Confianza de despliegue, not 100% coverage. The right tests, not all tests.

---

## 2. Decision

Implement `tests/test_phase1_critical_core.py` — 72 tests across 5 test suites covering the three foundational modules.

### 2.1 Suite 1 — GovernanceEvaluationEngine (27 tests)

**Covers:**
- Happy path: all signals pass all 11 checkpoints → `APPROVED`
- `gate_results`, `veto_chain`, `scores`, `checkpoints_passed` integrity
- Failure paths: `probability_score` below CP-1, `risk_exposure` above CP-2 (lte gate)
- **No-execution under contradiction:** `logic_consistency < 40` → CP-6 veto → `BLOCKED`
- Edge case: `logic_consistency=0` → `BLOCKED`
- Optional signal defaults: `signal_integrity` and `temporal_coherence` apply conservative defaults when absent; documented in `decision_trace` (ADR-065 epistemic transparency)
- Signal validation: missing required, out-of-range, negative, non-numeric, non-dict
- Safety floors: threshold below min, above max, unknown checkpoint (ADR-037)
- Metadata and domain preservation in result

**Key behavioral contract tested:**
```python
# CP-6: logic_consistency >= 40 required
signals["logic_consistency"] = 10.0  # → BLOCKED (CP-6 veto)
signals["logic_consistency"] = 0.0   # → BLOCKED (extreme contradiction)
```

### 2.2 Suite 2 — Fail-Closed Behavior (3 tests)

**Covers:**
- SAE internal error → `BLOCKED` with `SAE_INTERNAL_ERROR` veto (ADR-116 Policy 2)
- AML Gate internal error → `BLOCKED` with `AML_INTERNAL_ERROR` veto (ADR-116 Policy 4)
- Custom checkpoint override respected (ADR-037): strict threshold blocks signals that pass defaults

**Key behavioral contract tested:**
```python
# ADR-116: Any gate that cannot evaluate must block, not pass
with patch("omnix_core.governance.external_evaluator.get_sae",
           side_effect=Exception("SAE_MOCK_CRASH")):
    result = engine.evaluate(passing_signals)
    assert result["decision"] == "BLOCKED"
    assert result["layer"] == "LAYER_0_STRUCTURAL_ADMISSIBILITY"
```

### 2.3 Suite 3 — DecisionReceiptEngine (20 tests)

**Covers:**
- Required fields: `receipt_id`, `timestamp`, `asset`, `decision`, `content_hash`, `signature`, `signature_algorithm`, `policy_version`, `engine_version`, `prev_hash`
- Receipt ID format: `OMNIX-{CODE}-{hex12}` for known domains, `OMNIX-{hex12}` for unknown (ADR-074)
- Domain code mapping: all 10 known verticals (`trading→TRD`, `insurance→INS`, etc.)
- Content hash: non-empty 64-char hex, deterministic over same payload, changes on any field modification
- SHA-256 fallback: `signature_format="hex_sha256_fallback"`, matches `SHA-256(content_hash)`
- PQC signing path: provider called with content_hash, output base64-encoded
- `store_receipt` without DB URL → `False` (graceful, no exception)
- `get_last_hash` without DB URL → `""` (graceful)
- Stable process key (ADR-085): two engines in same process share `key_id`
- `key_id` format: 16 hex characters (SHA-256 fingerprint prefix)

**Design note on `hash_valid` (ADR-095 §4):**  
The `ReceiptVerifier.verify_receipt()` reconstructs a v1 field subset for hash verification. `DecisionReceiptEngine.generate_receipt()` hashes the full payload including `domain` and `signing_key_id`, which are not in the v1 reconstruction. This is a documented gap (ADR-095). Full hash verification uses the v2 canonical hash in `execution_proof.canonical_hash` (ADR-096). The tests reflect actual verifier behavior, not an idealized expectation.

### 2.4 Suite 4 — ReceiptVerifier (7 tests)

**Covers:**
- Verifier returns complete structure: all required fields present, `computed_hash` is 64-char hex
- `receipt_id` preserved in verification result
- `verification_timestamp` is an ISO string
- **Tampering detection:** modifying `decision` → `hash_valid=False`
- **Tampering detection:** modifying `asset` → `hash_valid=False`
- **Tampering detection:** replacing `content_hash` with fake → `hash_valid=False`
- Unknown signing provider → no exception (graceful `signature_valid=None`)

### 2.5 Suite 5 — ExecutionDecision Boundary (15 tests)

**Covers:**
- Nominal conditions → `should_execute=True`
- `to_dict()` includes `should_execute`
- **`data_integrity_block=True` → `should_execute=False`** (both data sources unavailable)
- **`market_condition=CRISIS` → `should_execute=False`**
- **`contagion_risk >= 80` → `should_execute=False`** (exact threshold)
- **`contagion_risk = 100` → `should_execute=False`** (maximum)
- **`slippage > 50bps` → `should_execute=False`** (unacceptable)
- **`timing.execute_now=False` → `should_execute=False`**
- `ADVERSE` market alone does not block (only `CRISIS` blocks)
- `contagion_risk < 80` → does not block alone
- Multiple block conditions → still blocked
- `to_dict()` includes `block_reason` when blocked
- `_get_fallback_decision()` → `ExecutionStyle.LIMIT`, confidence ≤ 0.3 (ADR-122 §3.3)
- `risk_adjusted_size` halved in EXTREME/HIGH volatility (factor=0.5)
- `risk_adjusted_size` equals `size_usd` in NORMAL regime with no other risk factors

---

## 3. Architectural Notes

### 3.1 SAE Isolation in Tests

The SAE (Layer 0) is enabled by default after ADR-116. Tests in `TestGovernanceEvaluationEngine` set `SAE_ENABLED=false` to isolate the Layer 1 checkpoint pipeline. `TestGovernanceFailClosed` sets `SAE_ENABLED=true` and patches `get_sae()` to test fail-closed behavior.

### 3.2 PQC Isolation in Receipt Tests

Receipt tests use `DecisionReceiptEngine.__new__()` with `_provider=None` to force SHA-256 fallback mode. This makes receipt tests deterministic without requiring Dilithium-3 key generation.

### 3.3 ExecutionDecision Dataclass Testing

`ExecutionDecision` is tested directly as a dataclass — no sub-engines instantiated for boundary tests. This isolates the semantic boundary logic (`should_execute`, `risk_adjusted_size`) from network/market data dependencies.

---

## 4. Test Results

```
72 tests collected
72 passed in 11.48s
0 failed
0 errors
```

| Suite | Tests | Focus |
|---|---|---|
| `TestGovernanceEvaluationEngine` | 27 | Pipeline happy/fail paths, defaults, validation, safety floors |
| `TestGovernanceFailClosed` | 3 | SAE/AML fail-closed (ADR-116) |
| `TestDecisionReceiptEngine` | 20 | Generation, hash, signature, persistence, key stability |
| `TestReceiptVerifier` | 7 | Hash integrity, tampering detection, graceful degradation |
| `TestExecutionDecisionBoundary` | 15 | should_execute semantics, fallback, risk sizing |
| **Total** | **72** | **72/72 PASSED** |

---

## 5. What This Enables

With these 72 tests green, the following guarantees are machine-verifiable:

| Guarantee | Test |
|---|---|
| Engine never APPROVES a contradictory signal set | `test_contradiction_blocks_execution` |
| Engine never APPROVES a zero logic_consistency signal | `test_zero_logic_consistency_blocked` |
| SAE internal error never passes through to Layer 1 | `test_sae_internal_error_fails_closed` |
| AML internal error never produces an APPROVED decision | `test_aml_internal_error_fails_closed` |
| Receipt hash changes on any field modification | `test_content_hash_changes_on_tamper` |
| Two engine instances share the same key in the same process | `test_two_engines_share_stable_key_in_same_process` |
| Execution never proceeds with both data sources unavailable | `test_data_integrity_block_prevents_execution` |
| Execution never proceeds in CRISIS market conditions | `test_crisis_market_prevents_execution` |
| Fallback decision is always LIMIT style | `test_fallback_decision_uses_limit_style` |

---

## 6. Phase Completion Status

| Fase | Status | ADR |
|---|---|---|
| **Fase 1 — Tests mínimos críticos** | ✅ COMPLETE | This ADR |
| Fase 2 — Archival `decision_receipts` (MiFID II 5yr) | ⏳ PENDING | ADR-126 planned |
| Fase 3 — Metrics (`filter_calibration_metrics`) | ⏳ PENDING | ADR-127 planned |
| Fase 4 — Shadow Portfolio batch outcomes | ⏳ PENDING | ADR-128 planned |

---

## 7. Consequences

**Positive:**
- Any regression in `GovernanceEvaluationEngine`, `DecisionReceiptEngine`, or `ExecutionProtocol` will be caught before deploy
- The fail-closed guarantee (ADR-116) is now machine-tested for SAE and AML Gate
- Receipt hash integrity is now verifiable through the test suite
- The execution boundary semantics are pinned — accidental changes to `should_execute` logic surface immediately
- 72 new behavioral tests added with zero regressions (existing 84+ tests unaffected)

**Limitations / Phase 2 targets:**
- `ReceiptVerifier.hash_valid` v1 gap (ADR-095 §4) documented but not resolved — deferred to Fase 2 archival work which will also address canonical hash storage
- `decision_receipt.store_receipt()` not tested with real DB — covered implicitly by production monitoring
- `execution_protocol.get_execution_decision()` end-to-end (with live market data) out of scope for Fase 1

---

## 8. References

- ADR-028: External Signal Evaluation API
- ADR-037: Per-Client Configurable Thresholds (safety floors)
- ADR-044: Quantum-Secure Decision Receipts
- ADR-065: Epistemic Transparency Score (signal defaults in trace)
- ADR-074: Receipt ID Format — OMNIX-{DOMAIN}-{hex12}
- ADR-078: Signing Key Persistence (stable_process mode)
- ADR-085: PQC Evidence Layer (module-level stable keys)
- ADR-092: Structural Admissibility Engine (Layer 0)
- ADR-095: Receipt Retention Policy (v1 hash gap documentation)
- ADR-096: Expanded Canonical Receipt (v2 hash)
- ADR-116: Fail-Closed Enforcement Policy
- ADR-122: Audit Suite v4 — Execution Boundary (ADR-122 §3.3)
