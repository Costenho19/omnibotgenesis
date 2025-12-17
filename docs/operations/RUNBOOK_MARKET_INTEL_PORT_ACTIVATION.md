# RUNBOOK: MarketIntelPort Activation

## Overview

This runbook describes how to activate the MarketIntelPort V7.0 interface for OMNIX.

**Port**: MarketIntelPort  
**Adapter**: MarketIntelAdapter  
**Feature Flag**: `USE_MARKET_INTEL_PORT`  
**Phase**: 5 (New Service Migration)  
**Status**: Implemented, NOT ACTIVE

## Pre-Activation Checklist

- [ ] All unit tests passing in `tests/test_market_intel_port.py`
- [ ] Legacy services available and healthy:
  - [ ] FearGreedService (omnix_core/market_analysis/)
  - [ ] AlphaVantageService (omnix_services/indicators/)
  - [ ] FinnhubService (omnix_services/news/)
- [ ] Redis cache available for sentiment caching
- [ ] API keys configured:
  - [ ] `ALPHA_VANTAGE_API_KEY`
  - [ ] `FINNHUB_API_KEY`

## Wrapped Legacy Services

The MarketIntelAdapter wraps these legacy services:

| Service | Module | Purpose |
|---------|--------|---------|
| FearGreedService | omnix_core/market_analysis/ | Fear & Greed Index |
| AlphaVantageService | omnix_services/indicators/ | Technical indicators |
| FinnhubService | omnix_services/news/ | Market news and earnings |

## Port Methods

| Method | Description | Fallback |
|--------|-------------|----------|
| `get_sentiment_snapshot()` | Current F&G value | Neutral snapshot |
| `get_sentiment_history(days)` | Historical F&G | Empty list |
| `get_technical_indicator()` | Single indicator | Neutral indicator |
| `get_multiple_indicators()` | Batch indicators | Empty list |
| `get_company_news()` | Company-specific news | Empty list |
| `get_general_news()` | Market news | Empty list |
| `get_earnings_calendar()` | Upcoming earnings | Empty list |
| `refresh_macro_calendar()` | Economic events | Empty list |
| `get_aggregated_intel()` | Combined intelligence | Partial response |
| `is_provider_available()` | Provider health | True with warning |
| `health_check()` | Adapter health | Status dict |

## Activation Steps

### Step 1: Verify Tests
```bash
cd /home/runner/workspace
python -m pytest tests/test_market_intel_port.py -v
```

### Step 2: Enable Feature Flag (Railway)
```bash
# In Railway environment variables
USE_MARKET_INTEL_PORT=true
```

### Step 3: Monitor Logs
```bash
# Watch for initialization
grep "MarketIntelAdapter" logs/omnix.log
```

### Step 4: Verify Health
```python
from src.omnix.bootstrap.container import get_container
container = get_container()
print(container.market_intel_adapter.health_check())
```

## Rollback Procedure

### Immediate Rollback
```bash
# Disable feature flag in Railway
USE_MARKET_INTEL_PORT=false
```

### Verify Rollback
- Check bot continues functioning with legacy path
- Monitor for any error spikes

## Expected Log Output

### Successful Activation
```
Container: Initializing MarketIntelAdapter...
MarketIntelAdapter: Initializing with lazy-loaded services
Container: MarketIntelAdapter initialized - healthy
```

### Degraded Mode
```
MarketIntelAdapter: FearGreedService unavailable, using fallback
MarketIntelAdapter: Running in degraded mode - 2/3 providers available
```

## Troubleshooting

### Provider Unavailable
- Check API key validity
- Verify network connectivity
- Check rate limits

### Health Check Failing
```python
health = adapter.health_check()
print(f"Healthy: {health['healthy']}")
print(f"Providers: {health['providers']}")
```

### Fallback Mode
The adapter continues operation with available providers. Missing providers return neutral/empty data.

## Performance Considerations

- Sentiment caching: 5 minutes TTL
- News caching: 15 minutes TTL
- Indicator caching: 1 hour TTL

## Contact

For issues, check Railway logs and create a GitHub issue with:
1. Error message
2. Feature flag state
3. Provider health status
