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
- `scripts/casi_trade_demo.py` - Demo script for investor presentations

## ECW_PROGRESS & ECW_RESET_REASON (Enhancement Jan 21, 2026)

### ECW_PROGRESS Structure

Added to `decision['v52_analysis']`:

```json
{
  "ecw_progress": {
    "current": 2,
    "required": 3,
    "previous": 1
  }
}
```

### ECW_RESET_REASON Enum

When ECW counter resets (was > 0, now = 0), reason is logged:

| Reason | Trigger |
|--------|---------|
| `BLACK_SWAN_HIGH` | Black Swan level = HIGH |
| `BLACK_SWAN_ELEVATED` | Black Swan not in allowed list |
| `MC_EDGE_DEGRADED` | MC Win Rate < 52% |
| `MC_ER_NEGATIVE` | MC Expected Return <= 0% |
| `SIGNAL_FLIP` | Signal changed from BUY to SELL/HOLD |
| `CONDITIONS_FAILED` | Generic fallback |

### Log Format

```
⏳ [ECW_GATE] BTC/USD | 2/3 cycles → Waiting for edge confirmation
🔄 [ECW_RESET] BTC/USD | 2/3 → 0/3 | Reason: BLACK_SWAN_HIGH
✅ [ECW_GATE] BTC/USD | 3/3 cycles → Trade window OPEN
```

### SQL Query for Auditing

```sql
SELECT 
    timestamp,
    symbol,
    (v52_analysis->'ecw_progress'->>'current')::int as ecw_current,
    v52_analysis->>'ecw_reset_reason' as reset_reason
FROM paper_trading_decisions
WHERE v52_analysis->>'ecw_reset_reason' IS NOT NULL
ORDER BY timestamp DESC;
```

## Casi-Trade Demo Script

Located at `scripts/casi_trade_demo.py`:

```bash
python scripts/casi_trade_demo.py          # ASCII timeline output
python scripts/casi_trade_demo.py --json   # JSON for video tools
python scripts/casi_trade_demo.py -o demo.json  # Save to file
```

### Sample Output

```
    TIME       SIGNAL    ECW      CONDITIONS            RESULT
    ────       ──────    ───      ──────────            ──────
    14:00       BUY      █░░ 1/3   WR✓ ER✓ BS:LOW✓       ⏳ Waiting...
      │
      ▼
    14:05       BUY      ██░ 2/3   WR✓ ER✓ BS:LOW✓       ⏳ Waiting...
      │
      ▼
    14:10       BUY      ✖ RESET   WR✓ ER✓ BS:HIGH✗     🔄 BLACK_SWAN_HIGH
      │
      ▼
    14:15      HOLD      ░░░ 0/3   WR✗ ER✗ BS:HIGH✗     📉 -2.7% avoided
```

## Future Work

1. **Calibration (Day 15-30)**: Analyze Shadow Portfolio to determine if 3 cycles is optimal
2. **Per-Symbol Thresholds**: Different assets may need different confirmation windows
3. **Regime-Adaptive ECW**: Reduce required cycles in trending markets

---

## Revision v1.1 - January 29, 2026

### Motivation

Alta tasa de HOLD por MC_WR ≈ 49–50% con ER ≈ 0% en mercados volátiles, sin degradación de otros módulos (Non-Markovian Kernel 67%, CAES 1.27x, EMA SHORT 38-43%). Después de 14 días de Track Record (Jan 15-28, 2026), el sistema ejecutó 0 trades.

### Hypothesis

Reducir WR mínimo de 52% a 50% permitirá evaluar si el bloqueo es estadístico (umbral muy alto) o de mercado (sin edge real), sin comprometer capital debido a los guardrails restantes (ER>0%, 3 ciclos, Black Swan, $20K cap).

### Decision

Reduce `mc_wr_min` threshold from 52% to 50% as controlled experiment.

### Success Criteria

- ↑ Número de trades válidos (objetivo: 5-10 trades antes de Day 30)
- Drawdown ≤ baseline (máx 3%)
- ER agregado ≥ 0%

### Rollback Criteria

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Drawdown excesivo | DD > 3% | Rollback inmediato |
| ER agregado negativo | ER < 0% tras 5+ trades | Rollback |
| Black Swan elevado | Aumento de vetos HIGH/EXTREME | Evaluar rollback |

### Observation Metrics (Non-Decisional)

Para monitoreo interno, no afectan decisiones de trading:

| Metric | Query | Purpose |
|--------|-------|---------|
| % trades desbloqueados por cambio WR | Trades con MC_WR 50-52% | Medir impacto del cambio |
| Delta trades/day | Trades v1.1 vs v1.0 period | Comparar actividad |
| Delta ER agregado | ER post-cambio vs baseline | Validar hipótesis |

**SQL para auditoría:**
```sql
SELECT 
    COUNT(*) as total_trades,
    AVG(mc_wr) as avg_mc_wr,
    SUM(CASE WHEN mc_wr >= 50 AND mc_wr < 52 THEN 1 ELSE 0 END) as trades_in_50_52_range
FROM paper_trading_decisions
WHERE created_at >= '2026-01-29'
AND ecw_config_version = '1.1';
```

### Changes

| Parameter | v1.0 | v1.1 | Rationale |
|-----------|------|------|-----------|
| **MC Win Rate Min** | 52% | **50%** | Allow trades at break-even edge |
| **MC Expected Return Min** | > 0% | > 0% | Unchanged - still require positive edge |
| **Consecutive Cycles** | 3 | 3 | Unchanged - still require confirmation |
| **Black Swan Max** | MEDIUM | MEDIUM | Unchanged - no trades in tail risk |

### ENV Configuration

All ECW thresholds are now ENV-configurable for rollback without redeploy:

| Variable | Default | Description |
|----------|---------|-------------|
| `ECW_MC_WR_MIN` | 50 | MC Win Rate minimum % |
| `ECW_MC_ER_MIN` | 0 | MC Expected Return minimum % |
| `ECW_CYCLES_REQUIRED` | 3 | Consecutive cycles required |

### Rollback Procedure

To revert to v1.0 thresholds:
1. Railway: Set `ECW_MC_WR_MIN=52` in Variables
2. Restart service
3. No code change or redeploy required

### Track Record Integrity

- **Pre-v1.1 data (Jan 15-28)**: Immutable, logged under config epoch v1.0
- **Post-v1.1 data (Jan 29+)**: New trades logged with `ecw_config_version: 1.1`
- **No retroactive impact**: Historical decisions remain unchanged

### Guardrails Maintained

- Kelly max 2% / $20K cap (ADR-004)
- Only BTC/USD and XRP/USD allowed
- Black Swan ≤ MEDIUM required
- ER > 0% required (positive edge mandatory)
- 3 consecutive cycles confirmation

### Success Criteria (Day 30 Review)

- At least 5-10 trades executed
- Win rate ≥ 45%
- No drawdown > 3%
- If criteria not met: Evaluate further calibration

---

## Related ADRs

- ADR-007: Coherence Threshold Calibration
- ADR-018: Decision Contradiction Index (DCI)
- ADR-008: Shadow Portfolio Opportunity Tracker
