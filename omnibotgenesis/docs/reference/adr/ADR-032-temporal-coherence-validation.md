# ADR-032: Temporal Coherence Validation (TCV) — Checkpoint 7

**Status**: ACCEPTED  
**Date**: March 2026  
**Author**: Harold Nunes  
**Category**: Architecture — Decision Governance  
**Review**: Post-architect deep review applied (5 critical fixes)

---

## Context

OMNIX's 6-checkpoint pipeline (Monte Carlo VETO → RMS VETO → Coherence Gate →
ECW Gate → Scoring → Decision) evaluates each proposed decision in isolation as
a probabilistic question: *"Is this decision justified given current market
conditions?"*

This is necessary but not sufficient.

A February 2026 conversation with JJ Jimenez (Quantum Temporal Dynamics
researcher) surfaced a structural gap: OMNIX does not evaluate whether a
sequence of individually-justified decisions produces a coherent system
trajectory. In physics and control theory, a system can make locally valid
transitions that collectively produce an inadmissible global trajectory.

**The distinction:**
- Probabilistic governance: "Is this BUY signal statistically justified?" → 6 checkpoints
- Temporal admissibility: "Is this BUY signal coherent with what this system has
  been doing in the last N cycles?" → gap identified, addressed by TCV

### Example of the gap

Imagine the governance pipeline approves: HOLD → HOLD → HOLD → HOLD → HOLD → BUY.
Each HOLD was individually justified. The BUY is statistically valid by Monte Carlo.
But there was **no regime change** between cycle 5 and cycle 6. The BUY appears
incoherent as a trajectory event — the system "jumped" without a causal transition.

TCV catches this: it evaluates the trajectory of the last N cycles and asks
whether the proposed action is admissible given that trajectory.

---

## Distinction from Related Temporal Frameworks

A February 2026 conversation with JJ Jimenez (QuantumThreat Labs, originator of
Quantum Temporal Dynamics™) surfaced the structural gap described above. For
due-diligence clarity, the distinction between his work and OMNIX's TCV is
documented here explicitly:

| Aspect | JJ Jimenez / QuantumThreat Labs | OMNIX TCV (this ADR) |
|--------|--------------------------------|----------------------|
| **Full name** | Temporal **Continuity** Validation | Temporal **Coherence** Validation |
| **Domain** | Post-quantum cryptographic security | Decision governance for automated systems |
| **Core question** | Does the cryptographic system maintain continuity under adversarial / quantum attack? | Does the sequence of governance decisions form a coherent directional trajectory? |
| **Implementation** | Validation infrastructure for secure communications and PQC migration | Checkpoint 7 in the OMNIX trading governance pipeline (49 unit tests) |
| **IP ownership** | Quantum Temporal Dynamics™ doctrine (JJ Jimenez / QuantumThreat Labs) | OMNIX implementation (Harold Nunes / OMNIX) |

**What the two share:** The underlying philosophical principle that evaluating a
system at a single instant is insufficient — the trajectory over time carries
information that point-in-time analysis discards. Both frameworks treat temporal
structure as a first-class variable rather than an afterthought.

**What differs:** The problem domain, the threat model, the implementation, and
the intended use case are completely different. OMNIX's TCV is not derived from
QTD doctrine; it applies a related intuition — trajectory coherence — to the
distinct problem of decision governance in automated trading.

The conversation with JJ Jimenez identified the gap in OMNIX's architecture.
The implementation (including the 5 production-grade corrections documented
below) is OMNIX's own work.

---

## Decision

Add Temporal Coherence Validation as **Checkpoint 7** in the OMNIX governance pipeline.

Position in pipeline:
```
[1] Monte Carlo VETO
[2] RMS VETO
[3] VETO Early Return
[4] Coherence Gate (6-tier)
[5] ← TCV — Checkpoint 7 (ADR-032)
[6] Edge Confirmation Window (ECW) Gate (ADR-019)
[7] Scoring
[8] Final Decision
```

### Algorithm: Trajectory Coherence Score (0-100)

TCV evaluates three trajectory dimensions:

| Dimension | Weight | Metric | What it detects |
|-----------|--------|--------|-----------------|
| **Direction Coherence** | 40% | Sign-change rate of consecutive EMA-score deltas | Rapid signal reversals (up-down-up-down = incoherent) |
| **Regime-Action Alignment** | 35% | Proposed action vs dominant HMM regime in recent history | BUY in a sustained BEARISH regime = incoherent |
| **Signal Stability** | 25% | Direction flip rate across normalized signal labels | BULLISH→BEARISH alternation = unstable trajectory |

**Scoring**:
- Direction Coherence: `(1 − sign_change_rate) × 100`. A monotonic trend (all-up or all-down) scores 100. A perfectly alternating signal scores 0.
- Regime Alignment: `70 + dominant_pct × 30` if action matches regime; `(1 − dominant_pct) × 40` if not. Requires dominant regime ≥ 40% plurality.
- Signal Stability: `(1 − flip_rate) × 100` across normalized direction labels.

**Default veto threshold**: 20/100 — very conservative (only blocks severe incoherence).

**Configurable** via environment variable `TCV_THRESHOLD` (default: 20).

---

## Critical Corrections Applied (Post-Architect Review)

An internal architect review identified 5 production-grade issues in the initial
implementation. All 5 were corrected before release:

### 1. Integration: Evaluating the Intended Action (not the default HOLD)

**Problem**: At the TCV insertion point in the pipeline, `decision["action"]` is
always "HOLD" — the BUY/SELL assignment happens in the scoring phase (~700 lines
later). The initial implementation evaluated HOLD, making the checkpoint
functionally inactive for most calls.

**Fix**: Derive `proposed_action` from `ema_signal.direction` at the call site,
using the same normalization table already present in the codebase
(BULLISH→BUY, BEARISH→SELL, NEUTRAL→HOLD). The EMA signal is available in scope
at the TCV insertion point (post-coherence-gate, pre-ECW).

### 2. Database Driver Compatibility (psycopg v3 primary, psycopg2 fallback)

**Problem**: The initial implementation imported `psycopg2` only. Railway uses
`psycopg[binary,pool]==3.3.1` (v3). This silently caused all DB fetches to fail,
triggering the pass-through (admissible=True) every time — effectively disabling
Checkpoint 7 in production.

**Fix**: Primary fetch uses `psycopg v3` (with `row_factory=dict_row`). If that
fails, falls back to `psycopg2`. Failure is logged at DEBUG level for observability.

### 3. Unbiased Trajectory Data (Dual Data Sources)

**Problem**: `shadow_trade_events` captures only VETOED/BLOCKED signals — a
biased subset of the decision stream. Using it alone makes the trajectory look
"more blocked than it actually is", potentially overstating incoherence risk.

**Fix**: TCV queries DUAL sources and merges them:
- `shadow_trade_events` — vetoed/blocked signals (half of window)
- `paper_trading_trades` — executed/approved signals (half of window)

Combined, they represent the full decision trajectory. `TCVResult.data_sources`
records which sources contributed to each evaluation.

### 4. Correct Direction Coherence Metric (Monotonicity, not Variance)

**Problem**: The original metric used standard deviation of EMA scores to measure
"consistency". This is a LEVEL measure, not a DIRECTION measure. A strong trend
from 20 → 80 is flagged as "inconsistent" due to high score variance, which is
wrong — it's a perfectly coherent directional move.

**Fix**: Replace with delta sign-change rate:
```
deltas = [score[i] - score[i+1] for each consecutive pair]
signs = sign of each delta
sign_change_rate = count(sign flips) / (len(signs) - 1)
score = (1 - sign_change_rate) × 100
```
This correctly rewards monotonic trends and penalizes reversals.

### 5. Signal Taxonomy Normalization

**Problem**: `shadow_trade_events` stores signals as BULLISH/BEARISH.
`paper_trading_trades` stores as LONG/SHORT/UPTREND/DOWNTREND. Mixing without
normalization causes false "high velocity" readings.

**Fix**: All signals pass through `_normalize_direction()` before scoring.
The normalization table covers all known OMNIX signal formats:
`BULLISH | LONG | BUY | STRONG_BUY | UPTREND → BUY`
`BEARISH | SHORT | SELL | STRONG_SELL | DOWNTREND → SELL`
`NEUTRAL | NONE | RANGING | VOLATILE → HOLD`

---

## Observability

Every `TCVResult` includes:

| Field | Purpose |
|-------|---------|
| `trajectory_score` | Composite score [0-100] |
| `dimension_scores` | Breakdown: direction_coherence, regime_alignment, signal_stability |
| `events_analyzed` | Number of events used |
| `data_sources` | ["shadow", "trade"] — which sources contributed |
| `pass_through` | True when TCV returned admissible without actual evaluation |
| `threshold_used` | Configured threshold at evaluation time |
| `timestamp` | ISO-8601 UTC timestamp |

TCV also populates `decision["temporal_coherence_score"]`,
`decision["temporal_coherence_admissible"]`, and `decision["temporal_coherence_pass_through"]`
in the governance decision payload. These fields are captured in the
`decision_trace` and included in PQC-signed governance receipts (ADR-028/031).

---

## Consequences

### Positive

- **Closes the trajectory gap**: OMNIX now validates individual decisions AND
  their sequence coherence.
- **Relevant for non-trading verticals**: In robotics and healthcare, trajectory
  admissibility is critical (irreversible physical actions cannot be evaluated
  only at the moment of execution).
- **Proven extensibility**: A 7th checkpoint added without modifying the
  governance core, validating the hexagonal architecture design.
- **Investor response**: Directly answers JJ Jimenez (QTD) with a concrete,
  tested implementation.

### Constraints

- **Conservative by design**: Threshold 20/100 means TCV only blocks severe
  trajectory incoherence. It is additive to, not a replacement for, statistical vetos.
- **Data dependency**: Requires ≥ 3 events in trajectory window (72h lookback,
  configurable). With fewer events → pass-through (admissible=True).
- **Not a regime detector**: TCV uses HMM regime as an input signal. The HMM
  checkpoint remains in the Coherence Gate (Checkpoint 4).

---

## Test Coverage

49 tests in `tests/test_temporal_coherence.py` covering:

| Test Class | Tests | Coverage Area |
|------------|-------|---------------|
| `TestNormalizeDirection` | 7 | Signal taxonomy normalization |
| `TestTCVResult` | 4 | Dataclass structure and serialization |
| `TestTCVFailSafe` | 5 | Fail-safe behavior |
| `TestTCVCoherentTrajectory` | 4 | Coherent → admissible=True |
| `TestTCVIncoherentTrajectory` | 4 | Incoherent → dimension analysis |
| `TestTCVDirectionCoherence` | 4 | Monotonicity metric correctness |
| `TestTCVRegimeAlignment` | 6 | Regime-action alignment logic |
| `TestTCVSignalStability` | 5 | Signal flip rate scoring |
| `TestTCVScoreRange` | 2 | Bounds validation [0, 100] |
| `TestTCVResultFields` | 5 | Observability field completeness |
| `TestTCVMergeAndNormalize` | 3 | Dual-source merge correctness |

All 49 pass. Runtime: ~11 seconds.

---

## Implementation Files

```
omnix_core/temporal/__init__.py
omnix_core/temporal/coherence_validator.py
omnix_core/bot/auto_trading_bot.py  (integration, Checkpoint 7)
tests/test_temporal_coherence.py
omnix_config/system_state_manifest.json
```

---

## Relationship to Prior ADRs

| ADR | Relationship |
|-----|-------------|
| ADR-013 | Non-Markovian Memory Kernel — philosophical foundation for TCV |
| ADR-017 | 6-tier Coherence Engine — TCV is additive, not a replacement |
| ADR-019 | Edge Confirmation Window — TCV operates immediately before ECW |
| ADR-028 | External Governance API — `temporal_coherence_score` in governance receipts |
| ADR-031 | PQC Configurable Assurance — TCV outputs are Dilithium-3 signed |

---

## Future Domain Calibration

For non-trading verticals, TCV thresholds and windows should be calibrated
per domain. These are configuration changes only — no architectural changes required:

| Domain | Threshold | Window | Rationale |
|--------|-----------|--------|-----------|
| Trading | 20 | 15 cycles | Lenient — markets are noisy |
| Robotics | 60 | 5 actions | Strict — irreversible physical consequences |
| Healthcare | 45 | 10 decisions | Moderate — regulatory auditability required |
