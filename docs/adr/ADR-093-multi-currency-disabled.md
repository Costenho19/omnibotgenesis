# ADR-093: Multi-Currency System Temporarily Disabled

**Status:** Accepted  
**Date:** 2026-04-20  
**Author:** Harold Alberto Nunes Rodelo — OMNIX Quantum Ltd  

---

## Context

During initialization of `TradingSystem` (omnix_core/trading_system.py), the call to
`self._init_multi_currency_system()` caused a crash at startup. The crash was reproducible
and blocking system initialization entirely.

The multi-currency system is responsible for managing portfolio positions across multiple
fiat and crypto pairs simultaneously. It is not required for single-pair governance evaluation,
which is the primary production use case at this stage.

## Decision

Disable `_init_multi_currency_system()` at construction time by commenting out the call
on line 199 of `trading_system.py`. The system initializes with single-currency mode
(BTC/USDT primary pair). A warning log is emitted at startup:

```
⚠️ Multi-currency system temporalmente desactivado (debugging)
```

## Consequences

**Positive:**
- System starts reliably without crash
- All governance checkpoints (CP-0 through CP-10 + Layer 0 SAE) remain fully operational
- Single-pair trading and evaluation unaffected

**Negative:**
- Portfolio diversification across multiple pairs not available
- Multi-currency risk aggregation disabled
- Cross-pair correlation signals not computed

## Reactivation Criteria

Reactivate once the root cause of the initialization crash is diagnosed and fixed.
The crash is believed to originate in a circular dependency between the multi-currency
portfolio state and the regime signal adapter during cold-start.

**Tracking:** Reactivation blocked on root-cause diagnosis of init crash.  
**Estimated effort:** 2–4h investigation + regression test.

---

*This ADR documents a deliberate, temporary architectural decision per OMNIX governance standards.*
