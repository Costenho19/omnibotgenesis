# RUNBOOK: PortfolioPort Activation

## Overview

This runbook describes how to activate the PortfolioPort V7.0 interface for OMNIX.

**Port**: PortfolioPort  
**Adapter**: PortfolioAdapter  
**Feature Flag**: `USE_PORTFOLIO_PORT`  
**Phase**: 5C (New Service Migration - Phase C)  
**Status**: Implemented, NOT ACTIVE

## Pre-Activation Checklist

- [ ] All unit tests passing in `tests/test_portfolio_port.py`
- [ ] Legacy services available and healthy:
  - [ ] PortfolioEngine (omnix_services/portfolio/)
  - [ ] PortfolioOptimizer (omnix_services/portfolio/)
  - [ ] ExposureManager (omnix_core/risk/)
  - [ ] RiskModelEngine (omnix_services/risk/)
- [ ] Database available for portfolio persistence
- [ ] Current portfolio data exists

## Wrapped Legacy Services

The PortfolioAdapter wraps these legacy services:

| Service | Module | Purpose |
|---------|--------|---------|
| PortfolioEngine | omnix_services/portfolio/ | Core portfolio management |
| PortfolioOptimizer | omnix_services/portfolio/ | Allocation optimization |
| ExposureManager | omnix_core/risk/ | Exposure tracking |
| RiskModelEngine | omnix_services/risk/ | Risk-adjusted allocation |

## Port Methods

| Method | Description | Fallback |
|--------|-------------|----------|
| `get_portfolio_view()` | Current portfolio snapshot | Empty portfolio |
| `get_portfolio_history()` | Historical values | Empty list |
| `get_allocation()` | Current weights | Empty allocation |
| `get_target_allocation()` | Target weights | Empty allocation |
| `set_target_allocation()` | Update targets | Error result |
| `get_drift_report()` | Target vs actual | Zero drift |
| `generate_rebalance_plan()` | Rebalancing orders | Empty plan |
| `execute_rebalance()` | Execute rebalancing | Error result |
| `get_sector_exposure()` | Sector breakdown | Empty exposures |
| `get_correlation_matrix()` | Asset correlations | Identity matrix |
| `get_value_at_risk()` | VaR calculation | Zero VaR |
| `health_check()` | Adapter health | Status dict |

## Activation Steps

### Step 1: Verify Tests
```bash
cd /home/runner/workspace
python -m pytest tests/test_portfolio_port.py -v
```

### Step 2: Verify Portfolio Data
```python
from omnix_services.portfolio.portfolio_engine import PortfolioEngine
engine = PortfolioEngine()
portfolio = engine.get_current_portfolio()
print(f"Total value: ${portfolio.total_value_usd}")
```

### Step 3: Enable Feature Flag (Railway)
```bash
# In Railway environment variables
USE_PORTFOLIO_PORT=true
```

### Step 4: Monitor Logs
```bash
# Watch for initialization
grep "PortfolioAdapter" logs/omnix.log
```

### Step 5: Verify Health
```python
from src.omnix.bootstrap.container import get_container
container = get_container()
print(container.portfolio_adapter.health_check())
```

## Rollback Procedure

### Immediate Rollback
```bash
# Disable feature flag in Railway
USE_PORTFOLIO_PORT=false
```

### Cancel Pending Rebalances
```python
# Cancel any in-progress rebalancing
adapter = container.portfolio_adapter
# Rebalancing is atomic - either completes or not started
```

### Verify Rollback
- Check portfolio views via legacy path
- Monitor for any allocation sync issues
- Verify rebalancing still works

## Expected Log Output

### Successful Activation
```
Container: Initializing PortfolioAdapter...
PortfolioAdapter: Initializing with lazy-loaded services
PortfolioAdapter: PortfolioEngine initialized
PortfolioAdapter: RiskModelEngine initialized
Container: PortfolioAdapter initialized - healthy
```

### Degraded Mode
```
PortfolioAdapter: PortfolioOptimizer unavailable, using basic allocation
PortfolioAdapter: Running in degraded mode - 3/4 services available
```

## Troubleshooting

### Portfolio View Empty
```python
# Check database connection
from omnix_core.database.portfolio_repo import PortfolioRepository
repo = PortfolioRepository()
positions = repo.get_all_positions()
print(f"Found {len(positions)} positions in DB")
```

### Drift Calculation Wrong
```python
# Manual drift check
adapter = container.portfolio_adapter
current = adapter.get_allocation()
target = adapter.get_target_allocation()
for asset, weight in current.weights.items():
    target_weight = target.weights.get(asset, 0)
    print(f"{asset}: {weight:.2%} vs target {target_weight:.2%}")
```

### Rebalancing Failed
```python
# Check rebalance plan without executing
plan = adapter.generate_rebalance_plan()
print(f"Orders to execute: {len(plan.orders)}")
print(f"Total buy: ${plan.total_buy_usd}")
print(f"Total sell: ${plan.total_sell_usd}")
```

## Critical Considerations

### Portfolio Management
This port controls portfolio allocation. If degraded:
- Rebalancing is disabled
- Portfolio view may be stale
- Optimization unavailable

### Fallback Behavior
When services unavailable:
1. `get_portfolio_view()` returns cached or empty portfolio
2. `execute_rebalance()` returns error (no trades)
3. Optimization returns equal-weight allocation

### Rebalancing Safety
- Always generate plan before executing
- Verify order count and sizes
- Check slippage estimates

## Asset Classes Supported

| Class | Examples | Source |
|-------|----------|--------|
| CRYPTO | BTC, ETH, SOL | Kraken |
| STOCKS | AAPL, MSFT, NVDA | Alpaca |
| FOREX | EUR/USD, GBP/USD | (future) |
| COMMODITIES | GOLD, SILVER | (future) |

## Rebalancing Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| THRESHOLD | Rebalance when drift > X% | Default (5%) |
| CALENDAR | Rebalance on schedule | Weekly/monthly |
| TACTICAL | Market-driven rebalance | Active management |
| RISK_PARITY | Equal risk contribution | Low volatility |
| MOMENTUM | Trend-following allocation | Bull markets |

## Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| Portfolio drift | > 10% | Trigger rebalance |
| Rebalance cost | > 0.5% AUM | Review frequency |
| Sector concentration | > 40% | Diversify |
| Correlation spike | > 0.8 avg | Review diversification |

## VaR Calculation

The adapter calculates Value at Risk:
- Method: Historical simulation (default)
- Confidence: 95% (configurable)
- Horizon: 1 day (configurable)
- Lookback: 252 trading days
