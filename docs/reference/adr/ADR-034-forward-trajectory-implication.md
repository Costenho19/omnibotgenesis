# ADR-034: Forward Trajectory Implicator (FTI) — Checkpoint 7b

**Status**: ACCEPTED  
**Date**: March 2026  
**Author**: Harold Nunes  
**Category**: Architecture — Temporal Governance  
**Follows**: ADR-033 (SIV — CP-0), ADR-032 (TCV — CP-7)

---

## Context

TCV (ADR-032) evaluates whether a proposed decision is consistent with the recent
PAST trajectory of the system. It asks: "Given what the system has been doing,
is this action coherent?"

**The gap**: TCV is purely backward-looking. It cannot evaluate whether the
proposed action makes sense for the near FUTURE.

A concrete failure mode: The system has been consistently HOLDING (TCV passes).
BUY signal appears. TCV says "OK, we were holding — a BUY doesn't contradict that."
But the HMM detects 70% probability of transition to BEARISH regime in 3 cycles.
Buying now implies holding through a likely adverse regime transition.

TCV cannot detect this because it only evaluates historical trajectory.

**FTI closes this gap**: It evaluates the forward implication of the proposed decision
over a configurable N-cycle horizon.

---

## Distinction from TCV

| Dimension | TCV (ADR-032) | FTI (ADR-034) |
|-----------|---------------|---------------|
| **Temporal Direction** | Backward-looking | Forward-looking |
| **Question asked** | "Is this coherent with the past?" | "What does this imply for the future?" |
| **Data sources** | Historical DB events | HMM transition matrix + EMA slope |
| **Threshold** | 20 (conservative) | 25 (very conservative) |
| **Position in pipeline** | Checkpoint 7 | Checkpoint 7b (after TCV) |
| **Veto when** | Past trajectory contradicts action | Future trajectory severely penalizes action |

---

## Decision

Add Forward Trajectory Implicator as **Checkpoint 7b** — immediately after TCV
and before the ECW Gate.

---

## Algorithm — Implied Score (0-100)

```
Implied Score = RegimeTransitionRisk(40%) + ImpliedDecisionConsistency(35%) + SignalMomentumSustainability(25%)
```

### Dimension 1: Regime Transition Risk (40%)

Uses the HMM transition matrix to estimate the probability of transitioning to
an ADVERSE regime within the next `FTI_HORIZON` cycles.

Adverse regimes:
- For BUY: BEARISH, DOWNTREND, VOLATILE, STRONG_SELL
- For SELL: BULLISH, UPTREND, VOLATILE, STRONG_BUY
- For HOLD: none (always neutral score)

When HMM matrix is available:
```
adverse_prob = sum(P(current_regime → adverse_regime)) for each adverse_regime
multi_cycle_risk = 1 - (1 - adverse_prob)^horizon
score = (1 - multi_cycle_risk) × 100
```

When HMM matrix is unavailable: uses regime persistence priors (TRENDING=0.82,
VOLATILE=0.45, etc.) to estimate probability of remaining in current regime.

### Dimension 2: Implied Decision Consistency (35%)

Given the recent regime history, evaluates how consistent the proposed action
is with the regimes the system has been experiencing.

Considers:
- Persistence ratio: how often the current regime appeared in recent history
- Compatibility ratio: how often compatible regimes appeared in recent history

Compatible regimes per action:
- BUY: BULLISH, UPTREND, TRENDING, NEUTRAL
- SELL: BEARISH, DOWNTREND, VOLATILE
- HOLD: NEUTRAL, RANGING, VOLATILE

### Dimension 3: Signal Momentum Sustainability (25%)

Computes the linear slope of recent EMA scores and evaluates whether the
momentum is sustainable for the proposed action direction.

- Positive slope + BUY → high score (momentum supports the direction)
- Negative slope + BUY → lower score (momentum against the direction)
- Positive slope + SELL → lower score
- Flat score + HOLD → high score (stable, HOLD is coherent)

---

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `FTI_THRESHOLD` | 25 | Minimum implied score to pass |
| `FTI_HORIZON` | 5 | N-cycle look-ahead |

**Conservative threshold (25/100)**: FTI only vetoes when the forward implication
is strongly negative across multiple dimensions simultaneously. A single adverse
dimension at medium strength does not trigger a veto.

---

## Fail-Safe Design

On any FTI module error → `passed=True`, `pass_through=True`.

If HMM matrix is absent: Dimension 1 uses persistence priors (never crashes).
If EMA scores absent: Dimension 3 returns neutral score 50.
If regime history absent: Dimension 2 returns neutral score 50.

FTI gracefully degrades to less precise evaluation without blocking the pipeline.

---

## Observability

| Field | Description |
|-------|-------------|
| `fti_score` | Composite implied score [0-100] |
| `fti_passed` | Whether FTI threshold was met |
| `fti_regime_transition_risk` | Raw regime transition probability [0-1] |
| `fti_pass_through` | True if FTI returned passed due to error |

Log format:
```
🔮 [FTI] BTC/USD | action=BUY | regime=TRENDING | score=72.3 → PASS
🔮 [FTI_VETO] BTC/USD | action=BUY | implied=18.4 < 25.0 | transition_risk=61.2% → HOLD
```

---

## Test Coverage

45 tests in `tests/test_forward_trajectory.py`:

| Test Class | Tests | Coverage Area |
|------------|-------|---------------|
| `TestFTIResult` | 4 | Dataclass structure |
| `TestFTIFailSafe` | 5 | Fail-safe behavior |
| `TestFTIRegimeTransitionRisk` | 8 | HMM matrix + persistence fallback |
| `TestFTIImpliedConsistency` | 8 | Regime history analysis |
| `TestFTISignalMomentum` | 6 | EMA slope computation |
| `TestFTIThreshold` | 5 | Veto threshold logic |
| `TestFTIHorizonConfig` | 4 | N-cycle horizon configuration |
| `TestFTILinearSlope` | 5 | Slope utility function |

---

## Consequences

### Positive
- **Closes backward-only gap**: OMNIX now evaluates both past and future coherence.
- **Conservative**: threshold 25/100 means FTI is a rarely-triggering safety net,
  not a frequent veto source.
- **Graceful degradation**: works without HMM matrix (uses priors).
- **Investor narrative**: "We validate not just what the system has done, but what
  the proposed action implies it will need to do next."

### Constraints
- **No DB queries**: FTI works entirely from in-memory context passed by the bot.
  This is intentional — FTI is a real-time forward model, not a historical query.
- **Probabilistic**: regime transition risk is an estimate, not a guarantee.
  The threshold is set conservatively to account for uncertainty.

---

## Relationship to Prior ADRs

| ADR | Relationship |
|-----|-------------|
| ADR-019 | ECW Gate — FTI precedes ECW in pipeline |
| ADR-032 | TCV — backward complement; FTI is forward complement |
| ADR-033 | SIV — data quality gate at CP-0; FTI is trajectory gate at CP-7b |
| ADR-014 | HMM Regime Detection — provides transition matrix for Dimension 1 |
