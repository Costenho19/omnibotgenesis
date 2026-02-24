# OMNIX — Real Data Policy

**Status**: Active | **Effective**: February 2026 | **Scope**: All user-facing surfaces

## Core Principle

> "Todo real, nada inventado" — Every metric shown to investors, users, or judges
> must originate from a verified data source. No estimates, no synthetic data,
> no silent fallbacks to zero.

## Data Sources (Authorized)

| Source | Type | Examples |
|--------|------|----------|
| PostgreSQL (Railway) | Primary persistence | Trades, P&L, balance history, analysis |
| Live APIs | Real-time feeds | Kraken, Alpaca, CoinGecko, Finnhub |
| Process metrics | Runtime telemetry | Latency, uptime, veto counts |

## Prohibited Patterns

### Python Backend

| Pattern | Risk | Required Fix |
|---------|------|-------------|
| `confidence = 0.85` (hardcoded) | Fabricated metric | Query from DB or return `insufficient_data` |
| `return value or 0.0` on financial metrics | Hides missing data | Return `None` or `{"status": "insufficient_data"}` |
| `fallback_price = 50000` | Stale/invented price | Raise exception or return error status |
| Mock data in production paths | Fake investor data | Use `@real_data_required` decorator |

**Decorator**: `omnix_core/data_integrity.py` provides `@real_data_required` which
enforces that decorated functions return data from verified sources only.

### JavaScript Frontend

| Pattern | Risk | Required Fix |
|---------|------|-------------|
| `metrics.win_rate \|\| 0` | Shows "0%" instead of "N/A" | `OmnixUtils.safeMetric(metrics.win_rate)` |
| `value ?? 0` | Same as above | `OmnixUtils.safeMetric(value)` |
| `parseFloat(x) \|\| 0` | Converts NaN to 0 | `OmnixUtils.renderMetricValue(...)` |
| `Number(x) \|\| 0` | Same as above | `OmnixUtils.renderMetricValue(...)` |
| `value.toFixed(2)` without null check | Runtime crash on null | `OmnixUtils.renderMetricValue(sm(value), v => v.toFixed(2))` |

### When `|| 0` IS Acceptable

Operational counters that genuinely default to zero:
- `trades_today || 0` (no trades = 0, not missing data)
- `open_positions || 0` (no positions = 0)
- `veto_count || 0` (no vetoes = 0)
- Chart data arrays for rendering (Plotly handles 0 correctly)

## Frontend Helpers (utils.js)

### `OmnixUtils.safeMetric(value, fallback?)`
Returns the value if valid, or `fallback` (default: `null`) if:
- `null`, `undefined`, empty string
- `NaN`, `Infinity`, `-Infinity`
- Object with `{status: "insufficient_data"}`

### `OmnixUtils.renderMetricValue(value, formatter?, naText?)`
Returns formatted string if value is valid, or `naText` (default: `"N/A"`) if invalid.
The formatter callback is only called when value is valid — prevents `.toFixed()` crashes.

### `OmnixUtils.isDataAvailable(value)`
Boolean check. Returns `false` for null, undefined, or `{status: "insufficient_data"}`.

## Usage Pattern

```javascript
const sm = OmnixUtils.safeMetric;
const rv = OmnixUtils.renderMetricValue;

// Investor-critical metric
const pnl = sm(metrics.total_pnl);
element.textContent = rv(pnl, v => OmnixUtils.formatCurrency(v, { showSign: true }));
// Result: "$-15,198.73" if real data, "N/A" if missing

// Operational counter (|| 0 is OK here)
element.textContent = `${metrics.trades_today || 0} trades`;
```

## Chart Safety

- Plotly equity curves filter null data points before rendering
- Pie charts use `(val || 0)` in reduce — safe because 0 is valid chart input
- All chart functions check for empty/insufficient data before calling Plotly

## Sort Safety

- Strategy sorting uses `-Infinity` fallback for null P&L values
- Ensures null-P&L strategies appear last, not randomly positioned

## Anti-Regression Tests

| Test File | Scope | Tests |
|-----------|-------|-------|
| `tests/test_no_hardcoded_metrics.py` | Python backend | Scans for hardcoded confidence scores, synthetic data patterns |
| `tests/test_frontend_data_integrity.py` | JS frontend | Verifies safeMetric usage, no `\|\| 0` on critical metrics, chart/sort safety |

## Investor-Critical Metrics (Protected)

These metrics MUST use `safeMetric`/`renderMetricValue` — never `|| 0`:

- Total P&L
- Win Rate (directional, net, legacy)
- Sharpe Ratio
- Max Drawdown
- Profit Factor
- Sortino Ratio
- Expectancy
- Avg Win / Avg Loss
- Best Trade / Worst Trade
- Signal Quality, Regime Accuracy (Adaptive Engine)
- Est. Profit / Est. Loss (Learning Insights)

## Compliance Verification

Run the full audit suite:
```bash
TESTING=true TELEGRAM_BOT_TOKEN=test-token python -m pytest tests/test_frontend_data_integrity.py tests/test_no_hardcoded_metrics.py -v
```

All tests must pass before any deployment.
