# OMNIX V7.0 Phase 2: Domain & Application Migration

**Version:** 1.0  
**Date:** December 12, 2025  
**Status:** IN PROGRESS  
**Pattern:** Strangler Fig (Aggressive Timeline)

---

## Executive Summary

Full architecture migration from legacy structure to Clean/Hexagonal architecture. No milestone gates - executing immediately with production safety via re-exports and feature flags.

**Duration:** 3 waves over 72+ hours of work  
**Risk Level:** MEDIUM (mitigated via Strangler Fig pattern)  
**Railway Status:** Continues running throughout migration

---

## Wave 1: Protective Scaffolding (~18h)

### Objective
Establish domain foundation before moving any production code.

### Deliverables

| ID | Task | Location | Est. Hours |
|----|------|----------|------------|
| 1.1 | Domain entities (Trade, Position, Signal) | `src/omnix/domain/trading/entities.py` | 4 |
| 1.2 | Value objects (Money, Quantity, SymbolPair) | `src/omnix/domain/trading/value_objects.py` | 2 |
| 1.3 | Risk entities (RiskAlert, LimitState) | `src/omnix/domain/risk/entities.py` | 2 |
| 1.4 | New ports (RiskRepository, SignalRepository) | `src/omnix/application/ports/` | 3 |
| 1.5 | Entity unit tests | `tests/test_domain_entities.py` | 4 |
| 1.6 | Parity test harness | `tests/test_parity_harness.py` | 3 |

### Gate Criteria
- [ ] All entity unit tests pass
- [ ] `verify_code.py` passes
- [ ] Smoke tests (13/13) pass

---

## Wave 2: Core Logic Migration (~34h)

### Objective
Move trading and risk logic into domain/application layers with full backward compatibility.

### Strategy Migration Map

| Legacy Location | New Location | Re-export |
|-----------------|--------------|-----------|
| `omnix_core/strategies/ares_v1.py` | `src/omnix/domain/trading/strategies/ares_v1.py` | ✅ |
| `omnix_core/strategies/ares_v2.py` | `src/omnix/domain/trading/strategies/ares_v2.py` | ✅ |
| `omnix_core/strategies/non_markovian_kernel.py` | `src/omnix/domain/trading/strategies/non_markovian.py` | ✅ |
| `omnix_core/strategies/caes_module.py` | `src/omnix/domain/trading/strategies/caes.py` | ✅ |
| `omnix_services/trading_service/quantum_momentum.py` | `src/omnix/domain/trading/strategies/quantum_momentum.py` | ✅ |
| `omnix_services/trading_service/monte_carlo.py` | `src/omnix/domain/trading/strategies/monte_carlo.py` | ✅ |
| `omnix_services/trading_service/kelly_criterion.py` | `src/omnix/domain/trading/strategies/kelly.py` | ✅ |
| `omnix_services/trading_service/black_swan.py` | `src/omnix/domain/trading/strategies/black_swan.py` | ✅ |
| `omnix_services/trading_service/hmm_regime.py` | `src/omnix/domain/trading/strategies/hmm_regime.py` | ✅ |
| `omnix_services/trading_service/kalman_filter.py` | `src/omnix/domain/trading/strategies/kalman_filter.py` | ✅ |
| `omnix_services/monitoring/risk_guardian.py` | `src/omnix/domain/risk/risk_guardian.py` | ✅ |
| `omnix_core/risk/rollback_protocol.py` | `src/omnix/domain/risk/rollback_protocol.py` | ✅ |

### Use Cases

| Use Case | Location | Wraps |
|----------|----------|-------|
| `ExecuteTradeUseCase` | `src/omnix/application/trading/execute_trade.py` | TradingService |
| `ScanMarketUseCase` | `src/omnix/application/trading/scan_market.py` | Signal pipeline |
| `EvaluateRiskUseCase` | `src/omnix/application/risk/evaluate_risk.py` | RiskGuardian |
| `ManagePositionsUseCase` | `src/omnix/application/trading/manage_positions.py` | PositionManager |
| `GenerateCoherenceReportUseCase` | `src/omnix/application/trading/coherence_report.py` | CoherenceEngine |

### Gate Criteria
- [ ] Parity tests pass (legacy vs new output comparison)
- [ ] Use case tests pass with mocked ports
- [ ] All legacy imports still work via re-exports
- [ ] Smoke tests (13/13) pass

---

## Wave 3: Wiring & Deployment (~20h)

### Objective
Connect new architecture to existing entry points with feature flags.

### Deliverables

| ID | Task | Location |
|----|------|----------|
| 3.1 | Update Container with new ports | `src/omnix/bootstrap/container.py` |
| 3.2 | Create adapters for legacy services | `src/omnix/infrastructure/adapters/` |
| 3.3 | Add USE_APP_LAYER feature flag | `src/omnix/config/settings.py` |
| 3.4 | Update main.py with conditional wiring | `main.py` |
| 3.5 | Full integration test suite | `tests/test_integration_phase2.py` |
| 3.6 | Documentation updates | `docs/current/ARCHITECTURE.md` |

### Feature Flag Strategy

```python
# src/omnix/config/settings.py
use_app_layer: bool = Field(default=False, env="USE_APP_LAYER")

# main.py
if settings.use_app_layer:
    from src.omnix.application import bootstrap_application_layer
    bootstrap_application_layer(container)
else:
    # Legacy path - unchanged
    pass
```

### Gate Criteria
- [ ] All tests pass (unit + integration + smoke)
- [ ] Railway deploy succeeds with USE_APP_LAYER=false
- [ ] Canary test with USE_APP_LAYER=true on staging
- [ ] Documentation complete

---

## Rollback Strategy

### Git Tags
- `phase2-wave1-complete`
- `phase2-wave2-complete`
- `phase2-wave3-complete`

### Instant Rollback
1. Re-exports keep all legacy imports working
2. Feature flag USE_APP_LAYER defaults to false
3. Railway maintains previous build snapshot
4. Git revert to wave tag if needed

### Emergency Commands
```bash
# Revert to pre-Phase2
git checkout phase1-complete

# Disable new layer without deploy
export USE_APP_LAYER=false
```

---

## Directory Structure After Phase 2

```
src/omnix/
├── __init__.py
├── config/
│   ├── __init__.py
│   └── settings.py          # Centralized settings (Phase 1)
├── bootstrap/
│   ├── __init__.py
│   ├── container.py         # DI Container (Updated Wave 3)
│   └── runtime.py           # Bootstrap runtime
├── domain/                   # NEW - Wave 1
│   ├── __init__.py
│   ├── trading/
│   │   ├── __init__.py
│   │   ├── entities.py      # Trade, Position, Signal
│   │   ├── value_objects.py # Money, Quantity, SymbolPair
│   │   └── strategies/      # Wave 2 - migrated strategies
│   │       ├── __init__.py
│   │       ├── ares_v1.py
│   │       ├── ares_v2.py
│   │       ├── non_markovian.py
│   │       ├── quantum_momentum.py
│   │       ├── monte_carlo.py
│   │       ├── kelly.py
│   │       ├── black_swan.py
│   │       ├── hmm_regime.py
│   │       ├── kalman_filter.py
│   │       └── caes.py
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── entities.py      # RiskAlert, LimitState
│   │   ├── risk_guardian.py # Wave 2
│   │   └── rollback_protocol.py
│   └── support/
│       ├── __init__.py
│       └── market.py        # MarketSnapshot, StrategyVote
├── application/             # NEW - Wave 2
│   ├── __init__.py
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── trading_port.py  # Extended
│   │   ├── risk_repository_port.py
│   │   └── signal_repository_port.py
│   ├── trading/
│   │   ├── __init__.py
│   │   ├── execute_trade.py
│   │   ├── scan_market.py
│   │   ├── manage_positions.py
│   │   └── coherence_report.py
│   └── risk/
│       ├── __init__.py
│       └── evaluate_risk.py
└── infrastructure/          # NEW - Wave 3
    ├── __init__.py
    └── adapters/
        ├── __init__.py
        ├── trading_service_adapter.py
        ├── risk_guardian_adapter.py
        └── coherence_engine_adapter.py
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Import errors in production | Medium | High | Re-exports at every legacy location |
| Strategy output drift | Low | High | Parity tests comparing legacy vs new |
| Railway deploy failure | Low | High | Feature flag + instant rollback |
| Performance regression | Low | Medium | Benchmark before/after Wave 3 |

---

## Success Metrics

- [ ] All 35+ packages mapped to new structure
- [ ] Zero breaking changes to external API
- [ ] Railway deploys successfully after each wave
- [ ] Test coverage maintained at current level
- [ ] Documentation updated with new architecture
