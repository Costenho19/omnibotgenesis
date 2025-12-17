# RUNBOOK: DerivativesPort Activation

## Overview

This runbook describes how to activate the DerivativesPort V7.0 interface for OMNIX.

**Port**: DerivativesPort  
**Adapter**: DerivativesAdapter  
**Feature Flag**: `USE_DERIVATIVES_PORT`  
**Phase**: 5B (New Service Migration - Phase B)  
**Status**: Implemented, NOT ACTIVE

## Pre-Activation Checklist

- [ ] All unit tests passing in `tests/test_derivatives_port.py`
- [ ] Legacy services available and healthy:
  - [ ] DerivativesManager (omnix_services/derivatives/)
  - [ ] FuturesClient (omnix_core/exchanges/)
  - [ ] HedgingService (omnix_services/hedging/)
  - [ ] MarginEngine (omnix_services/derivatives/)
- [ ] Exchange API credentials configured:
  - [ ] Kraken Futures API key
  - [ ] Kraken Futures API secret
- [ ] Database available for position persistence

## Wrapped Legacy Services

The DerivativesAdapter wraps these legacy services:

| Service | Module | Purpose |
|---------|--------|---------|
| DerivativesManager | omnix_services/derivatives/ | Derivatives orchestration |
| FuturesClient | omnix_core/exchanges/ | Futures order execution |
| HedgingService | omnix_services/hedging/ | Hedge position management |
| MarginEngine | omnix_services/derivatives/ | Margin calculations |

## Port Methods

| Method | Description | Fallback |
|--------|-------------|----------|
| `get_futures_positions()` | List open futures | Empty list |
| `open_futures_position()` | Open new position | Error result |
| `close_futures_position()` | Close position | Error result |
| `modify_futures_position()` | Adjust position | Error result |
| `get_available_contracts()` | List tradeable contracts | Empty list |
| `get_contract_details()` | Contract specifications | None |
| `calculate_margin_requirement()` | Required margin | Error requirement |
| `get_funding_rate()` | Current funding rate | Zero rate |
| `get_hedge_positions()` | List hedge positions | Empty list |
| `create_hedge()` | Create hedge position | Error result |
| `close_hedge()` | Close hedge position | Error result |
| `rebalance_hedge()` | Adjust hedge ratio | Error result |
| `health_check()` | Adapter health | Status dict |

## Activation Steps

### Step 1: Verify Tests
```bash
cd /home/runner/workspace
python -m pytest tests/test_derivatives_port.py -v
```

### Step 2: Verify Exchange Connectivity
```python
from omnix_core.exchanges.kraken_futures import KrakenFuturesClient
client = KrakenFuturesClient()
print(client.get_account_info())
```

### Step 3: Enable Feature Flag (Railway)
```bash
# In Railway environment variables
USE_DERIVATIVES_PORT=true
```

### Step 4: Monitor Logs
```bash
# Watch for initialization
grep "DerivativesAdapter" logs/omnix.log
```

### Step 5: Verify Health
```python
from src.omnix.bootstrap.container import get_container
container = get_container()
print(container.derivatives_adapter.health_check())
```

## Rollback Procedure

### Immediate Rollback
```bash
# Disable feature flag in Railway
USE_DERIVATIVES_PORT=false
```

### Emergency Position Closure
If positions are stuck:
```python
# Direct exchange API call
from omnix_core.exchanges.kraken_futures import KrakenFuturesClient
client = KrakenFuturesClient()
client.close_all_positions()
```

### Verify Rollback
- Check derivatives functionality via legacy path
- Monitor for any position sync issues
- Verify margin calculations

## Expected Log Output

### Successful Activation
```
Container: Initializing DerivativesAdapter...
DerivativesAdapter: Initializing with lazy-loaded services
DerivativesAdapter: DerivativesManager initialized
DerivativesAdapter: FuturesClient connected to Kraken
Container: DerivativesAdapter initialized - healthy
```

### Degraded Mode
```
DerivativesAdapter: MarginEngine unavailable, using fallback calculations
DerivativesAdapter: Running in degraded mode - 3/4 services available
```

## Troubleshooting

### Exchange Connection Failed
```python
# Verify API credentials
import os
print("KRAKEN_FUTURES_KEY:", bool(os.getenv("KRAKEN_FUTURES_KEY")))
print("KRAKEN_FUTURES_SECRET:", bool(os.getenv("KRAKEN_FUTURES_SECRET")))
```

### Position Sync Issues
```python
# Manual position refresh
adapter = container.derivatives_adapter
positions = adapter.get_futures_positions()
print(f"Found {len(positions)} positions")
```

### Margin Calculation Errors
```python
# Test margin calculation
requirement = adapter.calculate_margin_requirement(
    symbol="BTC-PERP",
    size=1.0,
    leverage=10
)
print(f"Margin required: ${requirement.margin_usd}")
```

## Critical Considerations

### Position Management
This port controls real derivatives positions. If degraded:
- New positions are blocked
- Existing positions remain open
- Hedge adjustments are disabled

### Fallback Behavior
When services unavailable:
1. `open_futures_position()` returns error (no new trades)
2. `get_futures_positions()` may return stale data
3. Margin calculations use conservative estimates

### Margin Safety
- Always use conservative leverage (max 5x for crypto)
- Monitor maintenance margin levels
- Auto-deleverage if margin < 50%

## Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| Position sync lag | > 30s | Check exchange API |
| Margin utilization | > 80% | Reduce positions |
| Funding rate | > 0.1%/8h | Consider closing |
| Failed orders | > 3 consecutive | Check exchange status |

## Contract Types Supported

| Type | Symbol Pattern | Example |
|------|---------------|---------|
| Perpetual | `{ASSET}-PERP` | BTC-PERP |
| Quarterly | `{ASSET}-{QUARTER}` | ETH-0324 |
| Option Call | `{ASSET}-CALL-{STRIKE}` | BTC-CALL-50000 |
| Option Put | `{ASSET}-PUT-{STRIKE}` | ETH-PUT-3000 |
