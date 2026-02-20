# Phase 1 Gradual Activation — Feb 13, 2026

## Context

The 30-day official track record period (Jan 15 - Feb 13, 2026) has been completed. During this period:
- **0 trades executed** — capital preservation demonstrated
- **192,000+ decision cycles** analyzed by the Shadow Portfolio engine
- **47 trades blocked** — 91% would have resulted in losses
- **98.5% capital preserved** while BTC dropped 7.37%

The system proved it can protect capital. Now it needs to demonstrate it can selectively trade when conditions are favorable.

---

## Phase 1 Changes

### What Changed

| Parameter | Previous Value | New Value | Where to Change |
|-----------|---------------|-----------|-----------------|
| `TRACK_RECORD_MODE` | `true` | `false` | Railway ENV Variables |
| `ECW_CYCLES_REQUIRED` | `3` | `2` | Railway ENV Variables |

### What TRACK_RECORD_MODE Did (Now Removed)
- Capped maximum score to 6/12 (50%) — even perfect signals couldn't exceed this
- Reduced position sizing by 0.35x factor
- Enabled WEAK_TREND scoring
- Applied reduced execution thresholds (VS=6, S=5, M=3 instead of normal)

**Effect of removing it**: Scores can now reach their natural values (up to 12/12). If all 5 signals agree, the trade can pass. If signals are bad, the score stays low and doesn't pass. The system's natural intelligence decides, not an artificial cap.

### What ECW_CYCLES_REQUIRED Change Does
- Previously needed 3 consecutive cycles with edge confirmed (MC WR >= 50%, MC ER > 0%, Black Swan <= MEDIUM)
- Now needs 2 consecutive cycles
- Still resets to 0 if any condition fails (SIGNAL_FLIP, BLACK_SWAN_HIGH, MC_EDGE_DEGRADED)

**Effect**: Faster confirmation of edge, but still requires persistence. One good cycle is not enough — needs 2 in a row.

---

## What Was NOT Changed (Safety Preserved)

| Safety Layer | Rule | Status |
|-------------|------|--------|
| **Monte Carlo VETO** | Expected Return < 0% → BLOCKED | ACTIVE — never touched |
| **Monte Carlo VETO** | VaR95 worse than -3% → BLOCKED | ACTIVE — never touched |
| **Monte Carlo Size Reduction** | Win Rate < 50% → position reduced to 50% | ACTIVE — never touched |
| **RMS VETO** | Pre-trade validation, circuit breaker | ACTIVE — never touched |
| **Black Swan Detector** | Tail event monitoring | ACTIVE — never touched |
| **Coherence Gate Critical** | < 30% coherence → CRITICAL BLOCK | ACTIVE — never touched |
| **Coherence Gate Normal** | < 45% coherence → NORMAL BLOCK | ACTIVE — never touched |
| **DCI** | >= 70 → mandatory HOLD | ACTIVE — never touched |
| **Asset Quarantine** | ADA, SOL, ETH, LINK quarantined | ACTIVE — never touched |

---

## Rollback Instructions (Railway)

If the system starts losing money or behaving unexpectedly:

### Immediate Rollback (< 1 minute)
1. Go to Railway → Project → Variables
2. Set `TRACK_RECORD_MODE=true`
3. Set `ECW_CYCLES_REQUIRED=3`
4. Railway auto-restarts — system returns to 30-day track record mode

### Partial Rollback Options
- Only restore score cap: Set `TRACK_RECORD_MODE=true` (keeps ECW at 2)
- Only restore ECW strictness: Set `ECW_CYCLES_REQUIRED=3` (keeps score cap removed)

---

## Phase Plan (Gradual)

| Phase | Changes | Timeline | Trigger for Next Phase |
|-------|---------|----------|----------------------|
| **Phase 1 (Now)** | Remove score cap + ECW 3→2 | Feb 13, 2026 | Observe 1-2 weeks for first trades |
| **Phase 2** | ECW_MC_WR_MIN 50→48 | ~Feb 27 | If Phase 1 produces 0 trades after 2 weeks |
| **Phase 3** | Coherence thresholds review | ~Mar 2026 | Only if Phase 2 insufficient |
| **Phase 4** | Normal operations | TBD | When system demonstrates consistent selective trading |

### Decision Criteria for Phase 2
- If after 2 weeks the system still executes 0 trades → lower MC WR threshold from 50% to 48%
- If the system executes 3-5 trades with positive outcomes → stay in Phase 1
- If the system executes trades with losses → evaluate and potentially rollback

---

## Business Documents Updated (Same Session)

| Document | Changes |
|----------|---------|
| Pitch Deck EN/ES | Prop firms pricing $15K-$50K → $15K-$35K, team section updated, Hub71 marked as "Applied - pending" |
| Business Model Canvas EN/ES | Created new, all numbers aligned with pitch deck |
| system_state_manifest.json | track_record_day=30, status=COMPLETED, Phase 1 documented |

---

## Summary

Phase 1 is conservative. We removed artificial constraints while preserving ALL safety mechanisms. The system should now be able to trade when genuine statistical edge exists, while still blocking everything during dangerous conditions. If anything goes wrong, rollback takes less than 1 minute via Railway ENV variables.

**The goal is NOT aggressive trading. The goal is selective, disciplined trading — exactly what OMNIX promises to investors.**

---

*Document created: Feb 13, 2026*
*Author: Development session*
*Status: Active — Phase 1 in effect*
