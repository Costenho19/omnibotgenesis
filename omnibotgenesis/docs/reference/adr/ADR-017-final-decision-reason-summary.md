# ADR-017: FINAL_DECISION_REASON Summary Block

**Date:** January 21, 2026  
**Status:** Accepted  
**Category:** Observability / Investor Transparency

## Context

When reviewing Railway logs or responding to investor due diligence, the decision-making rationale was scattered across multiple log lines:
- DECISION_TELEMETRY showed metrics but not explicit causation
- VETO_CHAIN showed what blocked but not the full context
- GUARDS_PASSED showed what worked but not why the final action was chosen

Investors and operators needed a single, consolidated summary that explains **why** each decision was made.

## Decision

Add a structured `FINAL_DECISION_REASON` block after each trading cycle that consolidates:

1. **Local signals** - EMA direction, Non-Markovian memory triggers
2. **Global edge** - Monte Carlo expected return and win rate assessment
3. **Regime status** - HMM regime (BULLISH/BEARISH/RANGING) and volatility level
4. **Risk level** - Black Swan detector status
5. **Coherence gate** - Pre-score vs threshold with PASSED/BLOCKED status
6. **Final determination** - Action with explicit reason (blocked, insufficient quality, all gates passed)

## Log Format

```
📋 FINAL_DECISION_REASON:
   - EMA signal: NONE
   - Global edge: insufficient (MC_ER=0.0001, WR=48.5%)
   - Regime: RANGING | Volatility: HIGH
   - Black Swan: elevated_kurtosis
   - Coherence: BLOCKED (25% vs 30% threshold)
   → Action: HOLD (BLOCKED by COHERENCE_GATE_LOW)
```

## Data Structure

```python
decision['final_decision_reason'] = {
    'action': 'HOLD',
    'final_reason': 'BLOCKED by COHERENCE_GATE_LOW',
    'components': [
        'EMA signal: NONE',
        'Global edge: insufficient (MC_ER=0.0001, WR=48.5%)',
        'Regime: RANGING | Volatility: HIGH',
        'Black Swan: elevated_kurtosis',
        'Coherence: BLOCKED (25% vs 30% threshold)'
    ],
    'capital_preservation': True
}
```

## Benefits

1. **Investor Transparency** - Clear audit trail for each decision
2. **Debugging** - Single place to understand decision causation
3. **Due Diligence** - Structured data for investor Q&A responses
4. **Capital Preservation Narrative** - Explicit flag when HOLD protects capital

## Files Changed

- `omnix_core/bot/auto_trading_bot.py` - Added FINAL_DECISION_REASON generation in telemetry section

## Consequences

- Slightly larger log output per cycle (~5 lines)
- `final_decision_reason` dict available in decision payload for downstream use
- No impact on trading logic (observability only)
