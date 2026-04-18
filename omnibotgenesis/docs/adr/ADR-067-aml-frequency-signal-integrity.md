# ADR-067: AML Frequency Signal Integrity — AML_FREQUENCY_PROXY_MODE

**Status:** Accepted  
**Date:** 2026-04-09  
**Author:** Harold Nunes (OMNIX QUANTUM LTD)  
**Companion ADRs:** ADR-066 (Epistemic Transparency), ADR-068 (OFAC Lifecycle)

---

## Context

The AML gate evaluates structuring risk — the practice of splitting large transactions to avoid reporting thresholds. A core input is `trade_frequency_24h`: how many trades the account executed in the last 24 hours.

**The bug:** In the production bot (`auto_trading_bot.py`), the AML call was hardcoded:

```python
aml_result = aml_gate.evaluate(symbol, action, volume_usd=volume_usd, trade_frequency_24h=0)
```

`trade_frequency_24h=0` is never the real value. The AML gate's structuring detection was effectively disabled — any structuring pattern would evaluate as if the account had made zero trades.

This is a variant of the same "manufactured confidence" problem as ADR-066: we claimed to be running AML evaluation but the evaluation lacked one of its primary inputs.

---

## Decision

**The bot must attempt to compute real trade frequency before calling AML. If real data is unavailable, it must explicitly document the gap.**

### Implementation

A helper method `_get_trade_frequency_24h()` is added to `AutoTradingBot`:

```python
def _get_trade_frequency_24h(self) -> int:
    try:
        stats = self.db.get_today_trade_stats()
        return stats.get("count", 0)
    except Exception:
        pass
    try:
        stats = self.db.get_paper_trades_stats()
        return stats.get("today_count", 0)
    except Exception:
        pass
    return 0
```

When the real count is unavailable (returns 0 via fallback), the bot adds `AML_FREQUENCY_PROXY_MODE` to the `decision_trace` and emits a WARNING log:

```
WARNING: [AML] trade_frequency_24h unavailable — using proxy=0. AML structuring detection may be incomplete.
```

The AML call becomes:

```python
freq = self._get_trade_frequency_24h()
aml_result = aml_gate.evaluate(symbol, action, volume_usd=volume_usd, trade_frequency_24h=freq)
if freq == 0:
    decision_trace.append("AML_FREQUENCY_PROXY_MODE: real count unavailable, structuring detection uses proxy=0")
```

---

## Consequences

### Positive

1. **Structuring detection is real** — When the DB has trade history, AML evaluates with actual frequency. High-frequency low-volume patterns are now correctly detected.
2. **Honest when unavailable** — `AML_FREQUENCY_PROXY_MODE` in the decision trace makes the limitation visible in the PQC receipt. Auditors see exactly what inputs were available.
3. **No regression on existing behavior** — When frequency data is unavailable (which was always the case before this ADR), behavior is identical to before, but now documented.

### Negative / Mitigations

- **DB latency** — `_get_trade_frequency_24h()` adds one DB call per decision cycle. The try/except pattern ensures this never blocks the pipeline even if the DB is unavailable.
- **Proxy mode is not a permanent solution** — Production deployments should ensure `get_today_trade_stats()` returns real data. This ADR documents the fallback, not the endgame.

---

## Implementation

### Files Modified

- `omnix_core/bot/auto_trading_bot.py` — `_get_trade_frequency_24h()` helper + AML call updated + proxy mode trace.

### Tests Added

- `tests/test_compliance_gates.py::TestAMLFrequencyTransparency` — 3 tests verifying frequency=0 passes, frequency > threshold reduces score, combined violations trigger veto risk.
