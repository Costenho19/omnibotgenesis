# RUNBOOK: ExecutionPort Activation

## Overview

This runbook describes how to activate the ExecutionPort V7.0 interface for OMNIX.

**Port**: ExecutionPort  
**Adapter**: ExecutionAdapter  
**Feature Flag**: `USE_EXECUTION_PORT`  
**Phase**: 5 (New Service Migration)  
**Status**: Implemented, NOT ACTIVE

## Pre-Activation Checklist

- [ ] All unit tests passing in `tests/test_execution_port.py`
- [ ] Legacy services available and healthy:
  - [ ] ExecutionProtocol (omnix_services/execution_service/)
  - [ ] LiquidityAnalyzer (omnix_services/execution_service/)
  - [ ] CrossAssetCorrelationEngine (omnix_services/execution_service/)
  - [ ] MicroVolatilityEngine (omnix_services/execution_service/)
- [ ] Kraken API connectivity verified
- [ ] Paper trading mode confirmed active

## Wrapped Legacy Services

The ExecutionAdapter wraps these legacy services:

| Service | Module | Purpose |
|---------|--------|---------|
| ExecutionProtocol | omnix_services/execution_service/ | Order routing |
| LiquidityAnalyzer | omnix_services/execution_service/ | Depth analysis |
| CrossAssetCorrelationEngine | omnix_services/execution_service/ | Cross-asset correlation |
| MicroVolatilityEngine | omnix_services/execution_service/ | Short-term volatility |

## Port Methods

| Method | Description | Fallback |
|--------|-------------|----------|
| `evaluate_liquidity()` | Analyze order book depth | Conservative estimate |
| `assess_correlation()` | Cross-asset correlation | Empty matrix |
| `compute_micro_volatility()` | Short-term volatility | Normal regime |
| `predict_slippage()` | Slippage estimation | Conservative estimate |
| `get_optimal_timing()` | Best execution window | Current time |
| `route_execution()` | Execute order | Failed result |
| `get_market_condition()` | Current market state | Neutral condition |
| `get_execution_summary()` | Combined metrics | Basic summary |
| `is_execution_safe()` | Safety check | (True, "Assumed safe") |
| `health_check()` | Adapter health | Status dict |

## Activation Steps

### Step 1: Verify Tests
```bash
cd /home/runner/workspace
python -m pytest tests/test_execution_port.py -v
```

### Step 2: Enable Feature Flag (Railway)
```bash
# In Railway environment variables
USE_EXECUTION_PORT=true
```

### Step 3: Monitor Logs
```bash
# Watch for initialization
grep "ExecutionAdapter" logs/omnix.log
```

### Step 4: Verify Health
```python
from src.omnix.bootstrap.container import get_container
container = get_container()
print(container.execution_adapter.health_check())
```

## Rollback Procedure

### Immediate Rollback
```bash
# Disable feature flag in Railway
USE_EXECUTION_PORT=false
```

### Verify Rollback
- Check trading continues with legacy execution path
- Monitor for any execution failures

## Expected Log Output

### Successful Activation
```
Container: Initializing ExecutionAdapter...
ExecutionAdapter: Initializing with lazy-loaded services
Container: ExecutionAdapter initialized - healthy
```

### Degraded Mode
```
ExecutionAdapter: LiquidityAnalyzer unavailable, using conservative estimates
ExecutionAdapter: Running in degraded mode - 3/4 components available
```

## Critical Safety Checks

### Pre-Execution Validation
```python
is_safe, reason = adapter.is_execution_safe("BTC/USD", 10000.0)
if not is_safe:
    logger.warning(f"Execution blocked: {reason}")
```

### Slippage Guard
```python
prediction = adapter.predict_slippage("BTC/USD", 10000.0, "buy")
if not prediction.is_acceptable:
    logger.warning(f"Slippage too high: {prediction.expected_slippage_bps} bps")
```

## Troubleshooting

### Liquidity Analysis Failing
- Verify Kraken API connectivity
- Check order book data availability
- Review rate limits

### Correlation Engine Errors
- Check historical data availability
- Verify sufficient data points (24h minimum)

### Slippage Overestimation
- Review volatility regime detection
- Check spread calculations
- Verify depth data freshness

## Performance Considerations

- Liquidity analysis: Real-time (no cache)
- Correlation matrix: 5 minute cache
- Volatility metrics: 1 minute cache
- Slippage predictions: Real-time (no cache)

## Paper Trading Mode

**CRITICAL**: ExecutionPort should only be activated in paper trading mode initially.

```python
# Verify paper mode
from omnix_config.settings import get_settings
settings = get_settings()
assert settings.paper_trading is True
```

## Contact

For issues, check Railway logs and create a GitHub issue with:
1. Error message
2. Feature flag state
3. Component health status
4. Last successful execution
