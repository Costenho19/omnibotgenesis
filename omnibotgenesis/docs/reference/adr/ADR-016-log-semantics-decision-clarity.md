# ADR-016: Log Semantics & Decision Clarity

**Status**: Accepted  
**Date**: 2026-01-21  
**Deciders**: OMNIX Core Team  
**Categories**: Logging, UX, Debugging

## Context

During log analysis, three sources of confusion were identified in the trading decision logs:

1. **Kelly Criterion logging on HOLD**: Kelly was logging "Confidence: HIGH" even when the final action was HOLD, creating misleading impressions about trade readiness.

2. **Dual confidence metrics**: Two different "confidence" values appeared in logs without clear distinction:
   - `Conf=0.5%` (decision score confidence)
   - `Confianza: 47.1%` (coherence score)

3. **Adaptive Gate text contradiction**: Log message "INACTIVE" followed by "PASSED" created cognitive dissonance, even though the logic was correct.

These issues affected:
- Debug efficiency for developers
- Log interpretation by auditors
- Future self-readability

## Decision

### P1: Kelly Skip on HOLD (Functional)

Kelly Criterion calculation continues (for sizing data), but logging is conditional:

```python
# Before (confusing)
💎 Kelly Criterion: 2.00% of capital ($20000.00) - Confidence: HIGH
📊 [DECISION_TELEMETRY] ... Action=HOLD ...

# After (clear)
💎 KELLY_SKIPPED: action=HOLD (size would be 2.00%)  # DEBUG level only
📊 [DECISION_TELEMETRY] ... Action=HOLD ...
```

- `log=False` parameter added to `calculate_optimal_position()`
- Kelly logged only when `action in (BUY, SELL)`
- HOLD cases logged at DEBUG level for traceability

### P2: Confidence Naming (Cosmetic)

Renamed in DECISION_TELEMETRY log:

| Before | After | Meaning |
|--------|-------|---------|
| `Conf=0.5%` | `DecisionConf=0.5%` | Score-derived confidence |
| `Coh=47.1%` | `CoherenceScore=47.1%` | Strategy alignment score |

### P3: Adaptive Gate Text (UX)

Changed wording for cognitive clarity:

```
# Before
📊 [ADAPTIVE_GATE] INACTIVE: EMA=12pts < 20 → using default threshold=10%
✅ [COHERENCE_GATE] PASSED: Score 47.1% >= 30%

# After
📊 [ADAPTIVE_GATE] BYPASSED: EMA=12pts < 20 → using base COHERENCE_GATE (threshold=30%)
✅ [COHERENCE_GATE] PASSED: Score 47.1% >= 30%
```

- "INACTIVE" → "BYPASSED" communicates intentional skip
- Clarifies that COHERENCE_GATE is the fallback

## Consequences

### Positive
- Logs no longer mislead about Kelly "confidence" on HOLD
- Two confidence metrics are now distinguishable
- Adaptive Gate behavior is self-documenting
- Reduces debugging time and cognitive load

### Negative
- Slight log format change may affect any log parsers (unlikely external dependency)
- Need to update any documentation referencing old log formats

### Neutral
- No behavioral changes to trading logic
- All changes are log-only (except Kelly log=False parameter)

## Files Changed

- `omnix_services/trading_service/kelly_criterion.py` - Added `log` parameter
- `omnix_core/bot/auto_trading_bot.py` - Conditional Kelly logging, renamed confidence labels
- `omnix_services/coherence_service/coherence_engine.py` - "INACTIVE" → "BYPASSED"

## References

- Railway logs analysis (Jan 21, 2026)
- ADR-007: Coherence Threshold Calibration
