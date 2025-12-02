# OMNIX V6.5 Dashboard Analysis - Complete Technical Report

> **Last Updated:** December 2024  
> **Status:** Pre-Production Review  
> **Purpose:** Technical audit for institutional investors

---

## 1. File Structure

```
omnix_dashboard/
├── app.py                      # Backend Flask (1639 lines, 25+ endpoints)
├── __init__.py
├── templates/
│   ├── terminal.html           # Dashboard Terminal (982 lines)
│   └── dashboard.html          # Dashboard Classic (1150 lines)
└── static/
    ├── css/                    # (empty - CSS inline)
    └── js/                     # (empty - JS inline)
```

---

## 2. Dashboard Overview

### 2.1 Terminal Dashboard (Bloomberg-style)

| Aspect | Detail |
|--------|--------|
| **File** | `omnix_dashboard/templates/terminal.html` |
| **URL Route** | `/terminal` (and `/` redirects here) |
| **Backend** | `app.py` lines 355-359 |
| **Purpose** | Real-time trading operations terminal |
| **Audience** | Traders, Operations Center (NOC) |
| **Size** | 982 lines (inline HTML+CSS+JS) |

**Features:**
- Header with core metrics (PnL, Win Rate, Trades, Drawdown, Sharpe, Sortino)
- 24h crypto ticker (real-time)
- OHLC candlestick chart 1H (Plotly)
- Active signals panel by strategy
- Volume bars by trading pair
- News feed (internal + Finnhub)
- Fear & Greed indicator
- Equity curve
- Status bar with protections
- Auto-refresh every 10 seconds

**APIs Consumed:**
- `/api/metrics`
- `/api/market/crypto`
- `/api/market/ohlc/<symbol>`
- `/api/signals/active`
- `/api/market/volume`
- `/api/news`
- `/api/market/finnhub-news`
- `/api/market/fear-greed`
- `/api/equity-curve`

---

### 2.2 Classic Dashboard (Executive)

| Aspect | Detail |
|--------|--------|
| **File** | `omnix_dashboard/templates/dashboard.html` |
| **URL Route** | `/classic` |
| **Backend** | `app.py` lines 362-366 |
| **Purpose** | Executive performance report |
| **Audience** | Investors, Risk Committee |
| **Size** | 1150 lines (inline HTML+CSS+JS) |

**Features:**
- Institutional metrics (card format)
- Unified table: open positions + closed trades
- Equity curve with filled area
- Market mix pie chart (Crypto vs Stocks)
- Crypto ticker
- News feed
- "System Status" panel with drawdown tier and ramp-up
- Live clock with timezone
- Auto-refresh every 10 seconds

**APIs Consumed:**
- `/api/metrics`
- `/api/trades`
- `/api/positions`
- `/api/equity-curve`
- `/api/market/crypto`
- `/api/news`
- `/api/system/status`

---

## 3. Execution Architecture

### 3.1 Railway (Production 24/7)

```
railway.json → startCommand: "python -u main.py"

main.py
├── Initialize services (DB, AI, Trading)
├── Start Telegram Bot (polling)
├── Start Dashboard in SECONDARY THREAD
│     └── Flask on port 5000
└── Monitoring loop every 5 sec
      └── If dashboard dies → exit(1) → Railway restarts
```

**Code (main.py lines 689-700):**
```python
def start_dashboard():
    from omnix_dashboard.app import app
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

dashboard_thread = threading.Thread(target=start_dashboard)
dashboard_thread.start()
```

### 3.2 Replit (Development)

```
Workflow "Dashboard Preview"
└── Runs ONLY dashboard Flask
    └── cd omnix_dashboard && python -c "from app import app; app.run(...)"
    └── Port 5000 → webview
```

**Key Difference:** Replit does NOT run Telegram bot (avoids token conflict)

---

## 4. Database Connection

**Both environments use the SAME PostgreSQL database (Railway):**

```python
# app.py lines 23-34
def get_database_url():
    return os.environ.get('DATABASE_URL') or 
           os.environ.get('POSTGRES_URL') or 
           os.environ.get('DATABASE_PUBLIC_URL')
```

---

## 5. Issues Detected

### 5.1 CRITICAL - Security

| # | Issue | Location | Impact | Status |
|---|-------|----------|--------|--------|
| 1 | **Hardcoded SECRET_KEY** | `app.py` line 25-30 | **MANDATORY** in Railway (crashes if missing), dev fallback for Replit | ✅ Fixed (Dec 2024) |
| 2 | **Unrestricted global CORS** | `app.py` line 33-43 | CORS restricted to Railway/Replit domains via `DASHBOARD_ALLOWED_ORIGINS` | ✅ Fixed (Dec 2024) |
| 3 | **No API authentication** | Sensitive endpoints | `@require_api_key` decorator protects: metrics, trades, positions, portfolio, equity-curve, signals | ✅ Fixed (Dec 2024) |

**Security Configuration for Railway (MANDATORY):**
```bash
# REQUIRED - Dashboard will crash without this in Railway:
SESSION_SECRET=<your-secret>

# STRONGLY RECOMMENDED - Protects sensitive endpoints:
DASHBOARD_API_KEY=<generate-with: python -c "import secrets; print(secrets.token_urlsafe(32))">

# OPTIONAL - Defaults to Railway/Replit domains if not set:
DASHBOARD_ALLOWED_ORIGINS=https://your-domain.com,https://another-domain.com
```

**Protected Endpoints (require DASHBOARD_API_KEY when configured):**
- `/api/metrics` - Performance metrics
- `/api/trades` - Trade history
- `/api/positions` - Open positions
- `/api/portfolio` - Portfolio state
- `/api/equity-curve` - Equity curve data
- `/api/signals/active` - Active trading signals

**Public Endpoints (no authentication required):**
- `/api/market/*` - Public market data (Kraken prices, volume, OHLC)
- `/api/news` - Internal news
- `/api/health` - Health check
- `/api/system/status` - System status

### 5.2 CRITICAL - Architecture

| # | Issue | Location | Impact | Status |
|---|-------|----------|--------|--------|
| 4 | **Flask dev server in production** | `main.py` line 693 | Werkzeug doesn't scale, no TLS, single-thread | ❌ Open |
| 5 | **No connection pooling** | `app.py` line 50 | New connection per request = inefficient | ❌ Open |
| 6 | **Blocking requests without timeout** | `app.py` multiple | Kraken/Finnhub calls can block everything | ❌ Open |
| 7 | **Dashboard thread without lifecycle** | `main.py` line 699 | If main thread blocks, monitoring collapses | ❌ Open |

### 5.3 SEVERE - Data

| # | Issue | Location | Impact | Status |
|---|-------|----------|--------|--------|
| 8 | **DB failures return empty `[]`** | `app.py` multiple | User sees "no data" instead of "error" | ❌ Open |
| 9 | **Status panel is FAKE** | `terminal.html` line 675-680 | Shows static "DATABASE CONNECTED" | ❌ Open |
| 10 | **No paper/real distinction** | Both dashboards | Doesn't indicate virtual vs real money | ❌ Open |
| 11 | **Prices without fallback** | `/api/positions` | If Kraken fails, entire table empty | ❌ Open |

### 5.4 SEVERE - Frontend

| # | Issue | Location | Impact | Status |
|---|-------|----------|--------|--------|
| 12 | **Full Plotly re-render** | Both dashboards | Recreates charts every 10s (expensive) | ❌ Open |
| 13 | **No retry/backoff** | JavaScript fetch | Silent network errors | ❌ Open |
| 14 | **Promise.all without granularity** | `refreshAll()` | One error affects all widgets | ❌ Open |
| 15 | **Duplicated JS logic** | terminal.html + dashboard.html | Same code in both files | ❌ Open |

### 5.5 MODERATE - Functionality

| # | Issue | Location | Impact | Status |
|---|-------|----------|--------|--------|
| 16 | **Risk Guardian invisible** | Both dashboards | Protection status not shown | ❌ Open |
| 17 | **Adaptive Engine absent** | Both dashboards | Calibrations not exposed | ❌ Open |
| 18 | **Benchmarks not shown** | Both dashboards | No market comparison | ❌ Open |
| 19 | **Timezone misaligned** | Classic dashboard | System settings ignored | ❌ Open |
| 20 | **No audited snapshots** | Both dashboards | Data not reconciled | ❌ Open |

---

## 6. Unused Endpoints

APIs that exist in `app.py` but NO dashboard consumes:

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `/api/portfolio` | Complete portfolio state | High |
| `/api/health` | System health status | High |
| `/api/market/stocks` | Stock data | Medium |
| `/api/market/technical-indicators/<symbol>` | Technical indicators | Medium |
| `/api/intelligence/summary` | Intelligence summary | High |
| `/api/intelligence/fear-greed` | Fear-greed duplicate | Low |
| `/api/intelligence/finnhub/news` | News duplicate | Low |
| `/api/intelligence/finnhub/sentiment/<symbol>` | Sentiment by symbol | Medium |
| `/api/intelligence/alpha-vantage/technical/<symbol>` | Alpha Vantage indicators | Medium |

---

## 7. Missing Investor-Critical Data

| Data | Importance | Exists in Backend | Dashboard Status |
|------|------------|-------------------|------------------|
| Risk Guardian / Circuit Breaker status | 🔴 Critical | ✅ Yes | Not displayed |
| Exposure limits per asset | 🔴 Critical | ✅ Yes | Not displayed |
| Benchmark comparison | 🔴 Critical | ❌ No | Not available |
| Adaptive calibration audit trail | 🟠 High | ✅ Partial | Not displayed |
| Data/Kraken latency | 🟠 High | ❌ No | Not available |
| Incident logs | 🟠 High | ✅ Yes | Not exposed |
| Paper vs live confirmation | 🟠 High | ✅ Yes | Not shown |
| Data integrity alerts | 🟡 Medium | ❌ No | Not available |

---

## 8. Code Duplication Between Dashboards

| Component | Terminal | Classic | Duplicated Code |
|-----------|----------|---------|-----------------|
| Fetch metrics | ✅ | ✅ | ~30 lines JS |
| Equity curve | ✅ | ✅ | ~40 lines JS |
| Crypto ticker | ✅ | ✅ | ~25 lines JS |
| News feed | ✅ | ✅ | ~20 lines JS |
| CSS variables | ✅ | ✅ | ~50 lines CSS |

**Total duplicated estimated:** ~165 lines

---

## 9. Current Level vs Institutional Standard

| Dashboard | Current Level | Institutional Standard | Gap |
|-----------|---------------|------------------------|-----|
| Terminal | ~60% | Bloomberg Terminal | 40% |
| Classic | ~65% | TradingView Pro | 35% |

**Gap Reasons:**
- No audited data guarantees
- No authentication
- No connection pooling
- No risk telemetry
- No graceful degradation
- Dev server in production

---

## 10. Improvement Roadmap

### Phase 1: Security (Critical) ⏱️ 2-3 hours

| Task | File | Line | Action |
|------|------|------|--------|
| Move SECRET_KEY to env | `app.py` | 18 | `os.environ.get('SESSION_SECRET')` |
| Restrict CORS | `app.py` | 17 | Add allowed origins list |
| Add API auth | `app.py` | - | Token validation middleware |

### Phase 2: Architecture (Critical) ⏱️ 4-6 hours

| Task | File | Action |
|------|------|--------|
| Replace Flask dev server | `main.py` | Use Gunicorn with workers |
| Implement connection pooling | `app.py` | psycopg_pool or SQLAlchemy |
| Add request timeouts | `app.py` | `requests.get(..., timeout=10)` |
| Add circuit breakers | `app.py` | pybreaker or custom |

### Phase 3: Data (Severe) ⏱️ 3-4 hours

| Task | File | Action |
|------|------|--------|
| Explicit error responses | `app.py` | Return `{error: "...", code: 500}` |
| Real status panel | `terminal.html` | Call `/api/health` |
| Paper/real indicator | Both dashboards | Add banner/badge |
| Price fallbacks | `app.py` | CoinGecko as backup |

### Phase 4: Frontend (Moderate) ⏱️ 4-5 hours

| Task | File | Action |
|------|------|--------|
| Consolidate JS | `static/js/common.js` | Extract shared functions |
| Delta chart updates | Both dashboards | Use Plotly.react() |
| Retry with backoff | JS | exponential-backoff library |
| Per-endpoint error handling | JS | Individual try-catch |

### Phase 5: Investor Features (Moderate) ⏱️ 3-4 hours

| Task | File | Action |
|------|------|--------|
| Risk Guardian panel | Both dashboards | New widget |
| Adaptive calibrations | Both dashboards | New widget |
| Consume unused endpoints | Both dashboards | Wire up APIs |
| Benchmark comparisons | `app.py` + dashboards | New endpoint + widget |

---

## 11. Priority Matrix

```
                    IMPACT
                    High            Low
            ┌───────────────┬───────────────┐
    High    │ Phase 1 & 2   │ Phase 4       │
URGENCY     │ Security +    │ Frontend      │
            │ Architecture  │ Improvements  │
            ├───────────────┼───────────────┤
    Low     │ Phase 3       │ Phase 5       │
            │ Data Issues   │ Investor      │
            │               │ Features      │
            └───────────────┴───────────────┘
```

---

## 12. Estimated Total Effort

| Phase | Hours | Priority | Dependencies |
|-------|-------|----------|--------------|
| Phase 1: Security | 2-3 | P0 | None |
| Phase 2: Architecture | 4-6 | P0 | Phase 1 |
| Phase 3: Data | 3-4 | P1 | Phase 2 |
| Phase 4: Frontend | 4-5 | P2 | Phase 3 |
| Phase 5: Investor | 3-4 | P2 | Phase 3 |
| **TOTAL** | **16-22** | - | - |

---

## 13. Quick Reference: File Locations

| Component | Path | Lines |
|-----------|------|-------|
| Flask Backend | `omnix_dashboard/app.py` | 1639 |
| Terminal HTML | `omnix_dashboard/templates/terminal.html` | 982 |
| Classic HTML | `omnix_dashboard/templates/dashboard.html` | 1150 |
| Main Entry | `main.py` | 723 |
| Railway Config | `railway.json` | 12 |
| Replit Config | `.replit` | ~80 |

---

## 14. API Endpoint Reference

### Core Views (5)
| Endpoint | Method | Returns |
|----------|--------|---------|
| `/` | GET | Redirect to /terminal |
| `/terminal` | GET | Terminal dashboard HTML |
| `/classic` | GET | Classic dashboard HTML |
| `/api/health` | GET | System health JSON |
| `/api/debug` | GET | Debug info JSON |

### Trading Data (6)
| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/metrics` | GET | Performance metrics |
| `/api/trades` | GET | Trade history |
| `/api/equity-curve` | GET | Equity curve data |
| `/api/portfolio` | GET | Portfolio state |
| `/api/positions` | GET | Open positions |
| `/api/signals/active` | GET | Active signals |

### Market Data (5)
| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/market/crypto` | GET | Crypto prices |
| `/api/market/stocks` | GET | Stock prices |
| `/api/market/ohlc/<symbol>` | GET | OHLC candles |
| `/api/market/volume` | GET | Volume data |
| `/api/news` | GET | Internal news |

### Market Intelligence (8)
| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/market/fear-greed` | GET | Fear & Greed index |
| `/api/market/finnhub-news` | GET | Finnhub news |
| `/api/market/technical-indicators/<symbol>` | GET | Technical indicators |
| `/api/intelligence/fear-greed` | GET | Fear & Greed (duplicate) |
| `/api/intelligence/finnhub/news` | GET | Finnhub news (duplicate) |
| `/api/intelligence/finnhub/sentiment/<symbol>` | GET | Sentiment analysis |
| `/api/intelligence/alpha-vantage/technical/<symbol>` | GET | Alpha Vantage indicators |
| `/api/intelligence/summary` | GET | Intelligence summary |

### System (1)
| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/system/status` | GET | System status |

---

*Document generated from OMNIX V6.5 Dashboard Audit - December 2024*
