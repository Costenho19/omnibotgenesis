# OMNIX Dashboard V6.5 - Flask Blueprints Architecture

## Overview

The OMNIX Dashboard has been refactored from a monolithic 1728-line `app.py` into a modular Flask Blueprints architecture. This improves maintainability, testability, and scalability.

## Architecture Summary

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Main app.py | 1728 lines | 90 lines | 95% reduction |
| Total code | 1728 lines | 1961 lines | +13% (better organized) |
| Files | 1 | 12 | Modular structure |
| Blueprints | 0 | 5 | Logical separation |

## Directory Structure

```
omnix_dashboard/
├── app.py                  # Application factory (90 lines)
├── run.py                  # WSGI entry point
├── ARCHITECTURE.md         # This file
├── blueprints/
│   ├── __init__.py        # Blueprint exports
│   ├── views.py           # HTML page routes (3 routes)
│   ├── core.py            # Core API endpoints (6 routes)
│   ├── market.py          # Market data endpoints (7 routes)
│   ├── intelligence.py    # External intelligence APIs (4 routes)
│   └── system.py          # System status/debug (5 routes)
├── utils/
│   ├── __init__.py        # Utils exports
│   ├── database.py        # PostgreSQL connection pool
│   ├── decorators.py      # API key authentication
│   ├── external_apis.py   # HTTP client with retry
│   └── queries.py         # SQL query functions
├── templates/
│   ├── base.html          # Jinja2 base template
│   ├── terminal.html      # Trading terminal view
│   └── dashboard.html     # Classic dashboard view
└── static/
    ├── css/               # Modular CSS (18 files)
    └── js/                # Modular JavaScript (11 files)
```

## Blueprints

### 1. Views Blueprint (`views_bp`)
**Purpose**: HTML page rendering
- `/` - Redirect to terminal
- `/terminal` - Trading terminal view
- `/classic` - Classic dashboard view

### 2. Core Blueprint (`core_bp`)
**Purpose**: Trading metrics and performance data
- `/api/metrics` - Performance metrics with strategy breakdown
- `/api/trades` - Recent trades list
- `/api/equity-curve` - Equity curve data points
- `/api/portfolio` - Portfolio allocation
- `/api/positions` - Open positions with live prices
- `/api/health` - Health check with pool stats

### 3. Market Blueprint (`market_bp`)
**Purpose**: Real-time market data
- `/api/market/crypto` - Live crypto prices (Kraken)
- `/api/market/stocks` - Stock prices (Alpaca)
- `/api/market/ohlc/<symbol>` - Candlestick data
- `/api/market/volume` - 24H volume data
- `/api/market/fear-greed` - Fear & Greed Index
- `/api/market/finnhub-news` - Market news
- `/api/news` - CoinGecko news (fallback)

### 4. Intelligence Blueprint (`intelligence_bp`)
**Purpose**: External API integrations
- `/api/intelligence/fear-greed` - Alternative.me Fear & Greed
- `/api/intelligence/finnhub/news` - Finnhub market news
- `/api/intelligence/finnhub/sentiment/<symbol>` - Symbol sentiment
- `/api/intelligence/alpha-vantage/technical/<symbol>` - Technical indicators

### 5. System Blueprint (`system_bp`)
**Purpose**: System status and debugging
- `/api/system/status` - Full system status
- `/api/signals/active` - Active trading signals
- `/api/debug` - Debug information (no secrets)

## Utils Package

### database.py
- `init_database()` - Initialize connection pool
- `get_db_connection()` - Context manager for connections
- `get_pool_stats()` - Pool health metrics
- Connection pooling: min=2, max=10 connections

### decorators.py
- `@require_api_key` - API authentication decorator
- Supports both query param and header authentication

### external_apis.py
- `http_get_with_timeout()` - HTTP client with retry logic
- 10-second timeout, 3 retries with exponential backoff

### queries.py
- `get_paper_trades(limit)` - Fetch trades from PostgreSQL
- `calculate_metrics(trades)` - Compute Sharpe, Sortino, etc.
- `get_strategy_breakdown(trades)` - Strategy performance
- `get_asset_breakdown(trades)` - Asset class breakdown

## Application Factory Pattern

```python
# app.py
def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(market_bp, url_prefix='')
    app.register_blueprint(intelligence_bp, url_prefix='')
    app.register_blueprint(system_bp)
    
    return app
```

## Import Pattern

All imports use absolute paths for package independence:

```python
# Correct (absolute)
from omnix_dashboard.utils.database import get_db_connection
from omnix_dashboard.utils.decorators import require_api_key

# Avoid (relative)
from ..utils.database import get_db_connection
```

## Running the Application

### Development
```bash
python omnix_dashboard/run.py
```

### Production (Railway)
```bash
gunicorn --bind=0.0.0.0:5000 --workers=4 omnix_dashboard.run:app
```

## API Response Format

All endpoints return JSON with consistent structure:

```json
{
  "success": true,
  "data": {...},
  "source": "PostgreSQL",
  "timestamp": "2025-12-02T09:00:00.000000"
}
```

## Database Connection

PostgreSQL via psycopg3 with connection pooling:
- Pool size: 2-10 connections
- Auto-reconnection on failure
- Health monitoring via `/api/health`

## Security

- API key authentication on sensitive endpoints
- No secrets exposed in debug endpoints
- Session-based CSRF protection

---

*Architecture refactored December 2024 | OMNIX V6.5 INSTITUTIONAL+*
