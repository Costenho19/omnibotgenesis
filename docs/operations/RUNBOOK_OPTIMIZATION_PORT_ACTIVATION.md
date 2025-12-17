# RUNBOOK: OptimizationPort Activation

## Overview

This runbook describes how to activate the OptimizationPort V7.0 interface for OMNIX.

**Port**: OptimizationPort  
**Adapter**: OptimizationAdapter  
**Feature Flag**: `USE_OPTIMIZATION_PORT`  
**Phase**: 5C (New Service Migration - Phase C)  
**Status**: Implemented, NOT ACTIVE

## Pre-Activation Checklist

- [ ] All unit tests passing in `tests/test_optimization_port.py`
- [ ] Legacy services available and healthy:
  - [ ] AutoOptimizer (omnix_services/auto_optimizer/)
  - [ ] AdaptiveWeights (omnix_core/adaptive/)
  - [ ] PerformanceOptimizer (omnix_services/optimization/)
  - [ ] MLModule (omnix_services/ml/)
- [ ] Sufficient historical data for optimization (min 30 days)
- [ ] Database available for optimization results

## Wrapped Legacy Services

The OptimizationAdapter wraps these legacy services:

| Service | Module | Purpose |
|---------|--------|---------|
| AutoOptimizer | omnix_services/auto_optimizer/ | Automated parameter tuning |
| AdaptiveWeights | omnix_core/adaptive/ | Dynamic weight adjustment |
| PerformanceOptimizer | omnix_services/optimization/ | Performance forecasting |
| MLModule | omnix_services/ml/ | ML-based predictions |

## Port Methods

| Method | Description | Fallback |
|--------|-------------|----------|
| `run_optimization()` | Execute optimization run | Empty result |
| `get_optimization_status()` | Current optimization state | Idle status |
| `cancel_optimization()` | Stop running optimization | Success |
| `get_optimization_results()` | Historical results | Empty list |
| `get_current_weights()` | Active weight set | Default weights |
| `update_weights()` | Apply new weights | Error result |
| `get_weight_history()` | Historical weights | Empty list |
| `get_performance_forecast()` | Future performance estimate | Neutral forecast |
| `get_parameter_recommendations()` | Suggested parameters | Empty dict |
| `health_check()` | Adapter health | Status dict |

## Activation Steps

### Step 1: Verify Tests
```bash
cd /home/runner/workspace
python -m pytest tests/test_optimization_port.py -v
```

### Step 2: Verify Historical Data
```python
from omnix_services.optimization.performance_optimizer import PerformanceOptimizer
optimizer = PerformanceOptimizer()
data_days = optimizer.get_available_data_days()
print(f"Historical data: {data_days} days")
```

### Step 3: Enable Feature Flag (Railway)
```bash
# In Railway environment variables
USE_OPTIMIZATION_PORT=true
```

### Step 4: Monitor Logs
```bash
# Watch for initialization
grep "OptimizationAdapter" logs/omnix.log
```

### Step 5: Verify Health
```python
from src.omnix.bootstrap.container import get_container
container = get_container()
print(container.optimization_adapter.health_check())
```

## Rollback Procedure

### Immediate Rollback
```bash
# Disable feature flag in Railway
USE_OPTIMIZATION_PORT=false
```

### Cancel Active Optimization
```python
adapter = container.optimization_adapter
result = adapter.cancel_optimization()
print(f"Cancelled: {result.success}")
```

### Verify Rollback
- Check optimization via legacy path
- Monitor for any weight sync issues
- Verify auto-optimizer still runs

## Expected Log Output

### Successful Activation
```
Container: Initializing OptimizationAdapter...
OptimizationAdapter: Initializing with lazy-loaded services
OptimizationAdapter: AutoOptimizer initialized
OptimizationAdapter: AdaptiveWeights loaded (default set)
Container: OptimizationAdapter initialized - healthy
```

### Degraded Mode
```
OptimizationAdapter: MLModule unavailable, using rule-based optimization
OptimizationAdapter: Running in degraded mode - 3/4 services available
```

## Troubleshooting

### Optimization Not Starting
```python
# Check current status
adapter = container.optimization_adapter
status = adapter.get_optimization_status()
print(f"Status: {status.status}")
print(f"Last run: {status.last_run_at}")
```

### Weight Update Failed
```python
# Verify weights format
from src.omnix.ports.driven.optimization_port import WeightUpdate
update = WeightUpdate(
    category=WeightCategory.SIGNAL_STRENGTH,
    weights={"rsi": 0.3, "macd": 0.4, "volume": 0.3}
)
result = adapter.update_weights(update)
print(f"Success: {result.success}")
```

### Performance Forecast Stale
```python
# Force recalculation
forecast = adapter.get_performance_forecast(horizon_days=30)
print(f"Expected return: {forecast.expected_return_pct}%")
print(f"Favorable: {forecast.is_favorable}")
```

## Critical Considerations

### Optimization Safety
This port controls trading parameters. If degraded:
- Optimization runs are blocked
- Existing weights remain active
- No automatic adjustments

### Fallback Behavior
When services unavailable:
1. `run_optimization()` returns empty result
2. `get_current_weights()` returns default conservative weights
3. `update_weights()` returns error (no changes)

### Weight Categories

| Category | Description | Components |
|----------|-------------|------------|
| SIGNAL_STRENGTH | Indicator weights | RSI, MACD, BB, etc. |
| RISK_FACTOR | Risk adjustments | Volatility, drawdown |
| POSITION_SIZE | Sizing factors | Kelly, fixed, dynamic |
| MARKET_REGIME | Regime detection | Trend, range, volatile |
| TIMING | Entry/exit timing | Speed, confirmation |

## Optimization Objectives

| Objective | Description | Use Case |
|-----------|-------------|----------|
| SHARPE_RATIO | Risk-adjusted return | Default objective |
| MAX_RETURN | Maximum total return | Bull markets |
| MIN_DRAWDOWN | Minimize losses | Bear markets |
| WIN_RATE | Maximize win percentage | High-frequency |
| PROFIT_FACTOR | Profit/loss ratio | Conservative |

## Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| Optimization runtime | > 10 min | Reduce search space |
| Weight changes/day | > 5 | Review stability |
| Forecast accuracy | < 50% | Increase lookback |
| Performance vs forecast | > 20% drift | Recalibrate model |

## AdaptiveWeights System

The adapter manages the AdaptiveWeights system:

```python
# Weight structure
weights = {
    "signal_strength": {
        "rsi": 0.25,
        "macd": 0.30,
        "bollinger": 0.20,
        "volume": 0.25
    },
    "risk_factor": {
        "volatility": 0.40,
        "drawdown": 0.35,
        "correlation": 0.25
    },
    "position_size": {
        "kelly_fraction": 0.25,
        "max_position": 0.10,
        "scaling_factor": 1.0
    }
}
```

## NullAdaptiveWeights Fallback

When AdaptiveWeights service unavailable, the adapter uses NullAdaptiveWeights:
- Returns default weights for all categories
- Health check reports degraded status
- No weight updates applied
- Optimization uses cached weights

```python
# NullAdaptiveWeights behavior
null_weights = NullAdaptiveWeights()
null_weights.get_weights()  # Returns default weights
null_weights.update_weights(new_weights)  # No-op, returns False
```

## Performance Optimization Schedule

| Period | Action | Objective |
|--------|--------|-----------|
| Daily | Quick weight adjustment | SHARPE_RATIO |
| Weekly | Full optimization run | SHARPE_RATIO |
| Monthly | Deep parameter search | MAX_RETURN |
| Quarterly | Strategy review | PROFIT_FACTOR |
