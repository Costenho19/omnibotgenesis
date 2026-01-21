# ADR-019: EDGE_CONFIRMATION_WINDOW (ECW)

**Date:** January 21, 2026  
**Status:** Accepted  
**Category:** Risk Management / Capital Patience / Institutional Trading

## Context

OMNIX operates in "capital preservation mode" with strict veto gates (MC, RMS, Coherence). While this correctly blocks trades without statistical edge, it creates a challenge:

> "The system is in perpetual HOLD - there's no exit path once market conditions improve."

Current behavior:
- MC_WR < 50% or MC_ER < 0 → HOLD
- When conditions improve for ONE cycle → immediate trade allowed

This single-cycle decision is suboptimal because:
1. **False positives**: Market noise can briefly show edge that disappears next cycle
2. **No confirmation**: One positive reading doesn't establish trend
3. **Investor perception**: "Reactive" rather than "patient" trading

## Decision

Implement **EDGE_CONFIRMATION_WINDOW (ECW)** - a gate that requires edge persistence before allowing trades.

### Key Properties

| Property | Value |
|----------|-------|
| **Mode** | ENFORCEMENT |
| **Affects Trading** | YES - blocks trades until edge confirmed |
| **Storage** | Redis counter per symbol with TTL |
| **Purpose** | Transform "capital preservation" into "capital patience" |

## Thresholds (v1.0)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **MC Win Rate Min** | 52% | 2% above break-even for statistical significance |
| **MC Expected Return Min** | > 0% | Any positive edge |
| **Consecutive Cycles Required** | 3 | Confirm persistence, not noise |
| **Black Swan Max** | MEDIUM | No trades during severe tail risk |

## Algorithm

```python
def evaluate_ecw(symbol, monte_carlo, black_swan):
    # 1. Check conditions
    wr_ok = mc_win_rate >= 52%
    er_ok = mc_expected_return > 0%
    bs_ok = black_swan_level in ['NONE', 'LOW', 'MEDIUM']
    all_conditions_met = wr_ok and er_ok and bs_ok
    
    # 2. Update counter in Redis
    if all_conditions_met:
        ecw_counter = redis.incr(f"ecw:{symbol}")
        redis.expire(f"ecw:{symbol}", 3600)  # 1 hour TTL
    else:
        redis.delete(f"ecw:{symbol}")  # Reset on failure
        ecw_counter = 0
    
    # 3. Decision
    ecw_passed = ecw_counter >= 3
    return ecw_passed, ecw_counter
```

## Behavior

### Counter Increments When:
- MC_WR >= 52%
- MC_ER > 0%  
- Black Swan <= MEDIUM

### Counter Resets When:
- Any condition fails
- TTL expires (1 hour of inactivity)

### Trade Allowed When:
- Counter >= 3 consecutive cycles

## Integration Point

ECW gate is evaluated AFTER Coherence Gate and BEFORE final scoring:

```
MC VETO → RMS VETO → COHERENCE GATE → [ECW GATE] → Scoring → Decision
```

If ECW not passed but trade signal exists:
- `should_trade = False`
- `action = HOLD`
- `veto_chain.append('ECW_WAITING')`
- Trade logged to Shadow Portfolio for counterfactual analysis

## Logging Format

```
⏳ [ECW_GATE] BTC/USD | ECW: 2/3 cycles (WR=53.2%✓, ER=0.15%✓, BS=LOW✓) → Waiting for edge confirmation
✅ [ECW_GATE] BTC/USD | ECW: 3/3 cycles (WR=54.1%✓, ER=0.22%✓, BS=LOW✓) → Trade window OPEN
```

## Investor Explanation

> "OMNIX does not trade on the first positive cycle. We wait for confirmation of statistical edge over 3 consecutive analysis cycles. This approach trades frequency for reliability - we prefer fewer, higher-conviction trades over reacting to market noise."

This narrative transforms "capital preservation" into **"capital patience"** - a more institutional framing.

## Consequences

### Positive
- Reduced false positive trades from noise
- Persistent edge confirmation improves win rate
- Institutional narrative: "patient capital"
- Auditable: counter visible in decision payload

### Negative  
- Delayed entry when edge first appears
- May miss quick opportunities
- Adds complexity to decision flow

### Mitigations
- Shadow Portfolio tracks missed opportunities for calibration
- Counter TTL prevents stale state
- Redis fallback to memory if unavailable

## Files Modified

- `omnix_core/bot/auto_trading_bot.py` - ECW gate implementation
- `omnix_config/system_state_manifest.json` - ECW configuration
- `docs/REAL_SYSTEM_STATUS.md` - ECW documentation
- `replit.md` - System overview update

## Future Work

1. **Calibration (Day 15-30)**: Analyze Shadow Portfolio to determine if 3 cycles is optimal
2. **Per-Symbol Thresholds**: Different assets may need different confirmation windows
3. **Regime-Adaptive ECW**: Reduce required cycles in trending markets

## Related ADRs

- ADR-007: Coherence Threshold Calibration
- ADR-018: Decision Contradiction Index (DCI)
- ADR-008: Shadow Portfolio Opportunity Tracker
