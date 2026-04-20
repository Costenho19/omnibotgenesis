# ADR-094: Enterprise Analytics Engine Temporarily Disabled

**Status:** Accepted  
**Date:** 2026-04-20  
**Author:** Harold Alberto Nunes Rodelo — OMNIX Quantum Ltd  

---

## Context

The Enterprise Analytics Engine (`initialize_enterprise_features()`) was designed to
provide advanced portfolio analytics, client reporting, and executive dashboards for
B2B deployments. It was implemented but is currently disabled at system startup
(omnix_core/trading_system.py, line 5341).

The feature was disabled during a system stability refactor to ensure clean separation
between the core governance pipeline (which must be always-on) and auxiliary analytics
features (which are additive).

## Decision

Comment out the `initialize_enterprise_features(global_ai_system, global_trading_system)`
call during the Flask app initialization sequence. The governance pipeline, receipt system,
Layer 0 SAE, and all 11 checkpoints continue to operate normally.

```python
# COMENTADO TEMPORALMENTE - Se activará después del bot
# enterprise_system = initialize_enterprise_features(global_ai_system, global_trading_system)
```

## Consequences

**Positive:**
- Flask app initializes faster and more reliably
- No risk of enterprise module errors affecting core governance functionality
- Core product (decision governance + receipts) fully unaffected

**Negative:**
- Advanced B2B analytics dashboards not active
- Enterprise client reporting not available until reactivation
- Executive summary generation disabled

## Reactivation Criteria

Reactivate after:
1. B2B client onboarding begins (Skilligen HDI pilot or Velos Capital integration)
2. Enterprise module tested independently with `TESTING=true` flag
3. ADR-086 B2B API endpoint verified stable under load

**Tracking:** Schedule for reactivation during B2B pilot phase.  
**Estimated effort:** 4–8h integration + load test.

---

*This ADR documents a deliberate, temporary architectural decision per OMNIX governance standards.*
