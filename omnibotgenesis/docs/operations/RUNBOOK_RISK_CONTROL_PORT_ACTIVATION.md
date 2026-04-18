# RUNBOOK: RiskControlPort Activation

## Overview

This runbook describes how to activate the RiskControlPort V7.0 interface for OMNIX.

**Port**: RiskControlPort  
**Adapter**: RiskControlAdapter  
**Feature Flag**: `USE_RISK_CONTROL_PORT`  
**Phase**: 5A (New Service Migration - Phase A)  
**Status**: Implemented, NOT ACTIVE

## Pre-Activation Checklist

- [ ] All unit tests passing in `tests/test_risk_control_port.py`
- [ ] Legacy services available and healthy:
  - [ ] AIRiskGuardian (omnix_services/risk/)
  - [ ] RiskEvaluator (omnix_core/risk/)
  - [ ] PositionSizer (omnix_services/position/)
  - [ ] DrawdownManager (omnix_core/risk/)
- [ ] Database available for risk metrics persistence
- [ ] Redis cache available for circuit breaker state

## Wrapped Legacy Services

The RiskControlAdapter wraps these legacy services:

| Service | Module | Purpose |
|---------|--------|---------|
| AIRiskGuardian | omnix_services/risk/ | AI-powered risk assessment |
| RiskEvaluator | omnix_core/risk/ | Traditional risk evaluation |
| PositionSizer | omnix_services/position/ | Position sizing algorithms |
| DrawdownManager | omnix_core/risk/ | Drawdown protection |

## Port Methods

| Method | Description | Fallback |
|--------|-------------|----------|
| `evaluate_trade_risk()` | Comprehensive risk assessment | HIGH risk w/ block recommendation |
| `get_current_risk_metrics()` | Portfolio risk snapshot | Default metrics |
| `get_position_size()` | Calculate safe position size | Minimum size (0.01) |
| `check_exposure_limits()` | Verify exposure within limits | Allowed with warning |
| `trigger_circuit_breaker()` | Emergency trading halt | Returns triggered state |
| `reset_circuit_breaker()` | Resume trading | Returns reset confirmation |
| `get_circuit_breaker_status()` | Current breaker state | Inactive status |
| `register_loss()` | Track losses | Stored loss record |
| `get_drawdown_status()` | Current drawdown level | Safe status |
| `health_check()` | Adapter health | Status dict |

## Activation Steps

### Step 1: Verify Tests
```bash
cd /home/runner/workspace
python -m pytest tests/test_risk_control_port.py -v
```

### Step 2: Enable Feature Flag (Railway)
```bash
# In Railway environment variables
USE_RISK_CONTROL_PORT=true
```

### Step 3: Monitor Logs
```bash
# Watch for initialization
grep "RiskControlAdapter" logs/omnix.log
```

### Step 4: Verify Health
```python
from src.omnix.bootstrap.container import get_container
container = get_container()
print(container.risk_control_adapter.health_check())
```

## Rollback Procedure

### Immediate Rollback
```bash
# Disable feature flag in Railway
USE_RISK_CONTROL_PORT=false
```

### Verify Rollback
- Check bot continues functioning with legacy risk paths
- Monitor for any error spikes in risk evaluation
- Verify trades are still being evaluated

## Expected Log Output

### Successful Activation
```
Container: Initializing RiskControlAdapter...
RiskControlAdapter: Initializing with lazy-loaded services
RiskControlAdapter: AIRiskGuardian initialized
RiskControlAdapter: RiskEvaluator initialized
Container: RiskControlAdapter initialized - healthy
```

### Degraded Mode
```
RiskControlAdapter: AIRiskGuardian unavailable, using fallback evaluator
RiskControlAdapter: Running in degraded mode - 3/4 services available
```

## Troubleshooting

### Service Initialization Failed
```python
# Check individual services
from omnix_services.risk.ai_risk_guardian import AIRiskGuardian
guardian = AIRiskGuardian()
print(guardian.health_check())
```

### Circuit Breaker Stuck
```python
# Manual reset
adapter = container.risk_control_adapter
result = adapter.reset_circuit_breaker("admin_override")
print(f"Reset: {result.success}")
```

### Drawdown Manager Issues
```python
# Check drawdown state
status = adapter.get_drawdown_status()
print(f"Level: {status.current_drawdown_pct}%")
print(f"Max: {status.max_allowed_pct}%")
```

## Critical Considerations

### Risk Evaluation Priority
This port controls trade approval. If degraded:
- Trades may be blocked conservatively
- Position sizes may be reduced
- Circuit breaker defaults to SAFE mode

### Fallback Behavior
When services unavailable:
1. `evaluate_trade_risk()` returns HIGH risk with BLOCK recommendation
2. `get_position_size()` returns minimum allowed size (0.01)
3. Circuit breaker defaults to ACTIVE (no trades)

### Performance
- Risk evaluation: < 100ms target
- Circuit breaker check: < 10ms
- Drawdown calculation: < 50ms

## Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| Evaluation latency | > 500ms | Check AI service |
| Block rate | > 50% | Review risk thresholds |
| Degraded mode | > 5 min | Investigate services |
| Circuit breaker trips | > 3/day | Review market conditions |
