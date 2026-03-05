# ADR-036: Exit Governance Layer (EGL)

**Status**: ACCEPTED  
**Date**: March 2026  
**Author**: Harold Nunes  
**Category**: Architecture — Exit Governance  
**Follows**: ADR-035 (RCK), ADR-032 (TCV), ADR-022 (PQC)

---

## Context

OMNIX has an 8-checkpoint entry governance pipeline (CP-0 SIV through CP-8 ECW).
Every trading entry passes through rigorous statistical, temporal, and data quality
validation before execution.

**The gap**: Exit decisions — approximately 40% of all capital events — had no
governance pipeline. The existing `_check_open_positions_tp_sl` function made exit
decisions via simple price comparisons:

```python
if pnl_pct >= tp_pct:
    should_close = True   # ← no governance, no receipt, no regime awareness
```

**Why this matters**:
1. **No regime awareness**: TP/SL percentages are fixed regardless of whether the
   market is TRENDING (where you should let winners run) or VOLATILE (where you
   should exit more aggressively).
2. **No coherence check**: A position might show TP hit during a brief spike,
   while all signals say the direction is still valid.
3. **No audit trail**: Entries generate PQC-signed receipts. Exits generated nothing.
   This creates asymmetric traceability — entries are fully auditable, exits are not.

---

## Entry Governance vs. Exit Governance — Feature Parity

| Feature | Entry (before ADR-036) | Exit (before ADR-036) | Exit (ADR-036) |
|---------|------------------------|----------------------|-----------------|
| Regime awareness | ✅ HMM-conditioned | ❌ Fixed % | ✅ Regime-adjusted TP/SL |
| Signal coherence | ✅ TCV + Coherence Engine | ❌ None | ✅ Exit Coherence Gate |
| Trajectory check | ✅ TCV + FTI | ❌ None | ✅ TCV Exit Check (optional) |
| PQC-signed receipt | ✅ Every decision | ❌ None | ✅ Every exit evaluation |
| Audit trail | ✅ decision_receipts | ❌ None | ✅ exit_governance_receipts |
| Fail-safe | ✅ pass-through | N/A | ✅ pass-through to naive exit |

---

## Decision

Add Exit Governance Engine as a **3-gate exit pipeline** applied in
`_check_open_positions_tp_sl()` for non-emergency exits.

**Emergency SL bypass**: Loss > `EMERGENCY_SL_PCT` (2%) → immediate exit, no EGL.
Capital protection has absolute priority and cannot be delayed by governance evaluation.

---

## 3-Gate Pipeline

### Gate 1: Regime-Adjusted Threshold Gate

TP/SL distances from entry are scaled by market regime:

| Regime | TP Multiplier | SL Multiplier | Rationale |
|--------|--------------|--------------|-----------|
| TRENDING | 1.3× | 0.8× | Let winners run; tighter stop |
| UPTREND | 1.3× | 0.8× | Same as TRENDING |
| BULLISH | 1.2× | 0.85× | Moderate extension |
| RANGING | 0.8× | 1.2× | Take profit faster; more SL noise tolerance |
| NEUTRAL | 1.0× | 1.0× | No adjustment |
| VOLATILE | 0.7× | 0.7× | Both directions, tighter exits |
| DOWNTREND | 0.8× | 0.85× | Shorter hold in downtrend |
| BEARISH | 0.6× | 0.6× | Most conservative |

**Note**: Multipliers apply to the DISTANCE from entry, not the absolute price.
This preserves the direction of TP/SL while scaling how far they sit from entry.

**SL override priority**: If a regime-adjusted SL is hit → exits unconditionally.
If only TP is hit → goes to Gate 2.

### Gate 2: Exit Coherence Gate

Evaluates whether the EMA signal direction supports exiting the position.

Logic for BUY positions:
- EMA says SELL/BEARISH + TP hit → **exit confirmed** (signals agree)
- EMA says BUY/BULLISH + position is in loss (≥0.5%) → **exit denied** (holding is coherent)
- EMA says BUY/BULLISH + position is in profit → **exit allowed** (TP = natural conclusion)
- No EMA context → **exit allowed** (neutral)

For SELL positions: mirror logic applied.

### Gate 3: TCV Exit Check (advisory)

Reuses `TemporalCoherenceValidator` in exit mode: evaluates whether the REVERSE
action of the position direction is temporally admissible.

- BUY position exit = proposing SELL → TCV evaluates "is SELL admissible now?"
- If TCV says admissible → exit timing is coherent with recent trajectory
- TCV errors → neutral (exit proceeds)

Gate 3 is only evaluated when the naive exit condition (`naive_tp or naive_sl`) is True.

### Aggregation Logic

1. Emergency SL → exit unconditionally (bypasses EGL)
2. Gate 1 SL hit → exit unconditionally (capital protection)
3. Gate 1 TP hit + Gate 2 coherent → exit with confidence
4. Gate 1 TP hit + Gate 2 denies → **HOLD** (coherence overrides TP signal)
5. Gate 1 not met + naive exit True → **HOLD** (regime says not yet)

---

## PQC-Signed Exit Receipts

Every exit evaluation generates an exit receipt stored in `exit_governance_receipts`:

```sql
CREATE TABLE IF NOT EXISTS exit_governance_receipts (
    id SERIAL PRIMARY KEY,
    receipt_id VARCHAR(36) UNIQUE NOT NULL,
    position_id VARCHAR(100),
    symbol VARCHAR(20),
    exit_reason VARCHAR(200),
    regime VARCHAR(50),
    should_exit BOOLEAN,
    gate1_threshold_verdict BOOLEAN,
    gate2_coherence_verdict BOOLEAN,
    gate3_tcv_verdict BOOLEAN,
    regime_adjusted_tp DECIMAL(20,8),
    regime_adjusted_sl DECIMAL(20,8),
    confidence DECIMAL(8,4),
    pqc_signature TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Signature**: Dilithium-3 when PQC is available; SHA-256 hash when not.
**Note**: EGL uses ephemeral keypairs (per instance). For cross-session verification,
receipts include the SHA-256 hash of the payload as the canonical identifier.

---

## Fail-Safe Design

On any EGL module error:
- `passed = naive_exit` (original price-comparison result)
- `pass_through = True`
- Pipeline continues with existing naive TP/SL behavior unchanged

This means EGL NEVER degrades exit performance below the existing baseline.
The worst case is that EGL fails silently and the system exits as it always did.

---

## Test Coverage

44 tests in `tests/test_exit_governance.py`:

| Test Class | Tests | Coverage Area |
|------------|-------|---------------|
| `TestExitGovernanceResult` | 5 | Dataclass structure |
| `TestRegimeAdjustedThresholds` | 10 | All regime multipliers |
| `TestExitCoherenceGate` | 8 | EMA signal coherence logic |
| `TestTCVExitCheck` | 5 | Gate 3 TCV integration |
| `TestExitReceipt` | 6 | PQC signing and uniqueness |
| `TestFailSafe` | 5 | Pass-through on error |
| `TestIntegration` | 5 | End-to-end scenarios |

---

## Consequences

### Positive
- **Governance parity**: Entry and exit decisions now both have structured pipeline
  + PQC-signed receipts.
- **Regime-appropriate exits**: TP/SL are no longer static; they adapt to the market
  context that was already being used for entry decisions.
- **Coherence**: Prevents premature exits when signals still support the position.
- **Full audit trail**: Every exit evaluation, including holds, is signed and stored.
- **No regression**: Emergency SL bypass and fail-safe design guarantee existing
  capital protection behavior is preserved.

### Constraints
- **EGL regime is currently NEUTRAL**: In the first implementation, `_egl_regime`
  is passed as "NEUTRAL" because the HMM regime is not directly accessible from
  `_check_open_positions_tp_sl()`. A follow-up improvement would pass the current
  regime from `_analyze_market()` results. With NEUTRAL regime, multipliers = 1.0×
  (no change from baseline), which is a safe starting behavior.
- **EGL adds latency**: Each exit evaluation adds gate processing time. This is
  negligible for the current 90-second check interval.

---

## Relationship to Prior ADRs

| ADR | Relationship |
|-----|-------------|
| ADR-019 | ECW Gate (entries) — EGL is the exit analog of ECW |
| ADR-022 | PQC — Dilithium-3 signatures on exit receipts |
| ADR-032 | TCV — Gate 3 reuses TCV in exit mode |
| ADR-033 | SIV — entry CP-0; EGL is exit governance layer |
