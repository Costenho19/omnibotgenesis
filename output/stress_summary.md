# OMNIX Security Stress Audit — Summary Report

**Generated**: 2026-02-20T04:10:13.309834+00:00
**Target**: http://localhost:5000
**Config**: 2000 requests, 50 concurrency, 8.55s

## Verdict: PASS

| Metric | Value |
|--------|-------|
| Endpoints Tested | 20 |
| Total Requests | 2000 |
| Overall Error Rate | 5.0% |
| Throughput | 233.9 req/s |
| Security Headers Compliant | Yes |
| Information Leaks | 0 |

## Security Header Compliance

**Forbidden headers detected:**
- Server: Werkzeug/3.1.3 Python/3.11.14 (version fingerprinting)

## Latency Percentiles (ms)

| Endpoint | Reqs | p50 | p95 | p99 | Err% |
|----------|------|-----|-----|-----|------|
| /api/core/balance | 100 | 55.98 | 632.17 | 727.85 | 0.0% |
| /api/core/decisions | 100 | 53.14 | 628.2 | 706.28 | 0.0% |
| /api/core/drawdown_chart | 100 | 43.48 | 102.67 | 1293.08 | 0.0% |
| /api/core/equity_curve | 100 | 47.6 | 625.16 | 742.6 | 0.0% |
| /api/core/performance | 100 | 57.25 | 636.46 | 716.9 | 0.0% |
| /api/core/pnl_breakdown | 100 | 44.84 | 100.68 | 808.54 | 0.0% |
| /api/core/portfolio | 100 | 48.57 | 642.05 | 780.0 | 0.0% |
| /api/core/trades | 100 | 55.26 | 631.11 | 720.41 | 0.0% |
| /api/core/win_rate_dual | 100 | 47.28 | 632.12 | 736.84 | 0.0% |
| /api/health | 100 | 5.66 | 36.66 | 69.97 | 0.0% |
| /api/intelligence/correlation_heatmap | 100 | 43.13 | 109.7 | 743.19 | 0.0% |
| /api/intelligence/dci | 100 | 40.52 | 100.56 | 738.92 | 0.0% |
| /api/intelligence/learning | 100 | 41.57 | 84.29 | 755.57 | 0.0% |
| /api/intelligence/regime | 100 | 43.23 | 645.36 | 787.18 | 0.0% |
| /api/intelligence/shadow | 100 | 43.61 | 98.34 | 1349.33 | 0.0% |
| /api/market/btc | 100 | 44.61 | 128.74 | 1281.68 | 0.0% |
| /api/market/sentiment | 100 | 42.27 | 115.99 | 761.58 | 0.0% |
| /api/market/time_heatmap | 100 | 43.13 | 632.84 | 778.71 | 0.0% |
| /api/system/quarantine | 100 | 9.75 | 53.67 | 119.2 | 100.0% |
| /api/system/version | 100 | 41.33 | 114.11 | 734.69 | 0.0% |

## Information Leakage Scan

No information leakage detected across all tested endpoints.

## Endpoints Status

| Endpoint | HTTP Status | Category |
|----------|-------------|----------|
| /api/core/balance | 200 (OK) | core |
| /api/core/decisions | 200 (OK) | core |
| /api/core/drawdown_chart | 200 (OK) | core |
| /api/core/equity_curve | 200 (OK) | core |
| /api/core/performance | 200 (OK) | core |
| /api/core/pnl_breakdown | 200 (OK) | core |
| /api/core/portfolio | 200 (OK) | core |
| /api/core/trades | 200 (OK) | core |
| /api/core/win_rate_dual | 200 (OK) | core |
| /api/health | 200 (OK) | system |
| /api/intelligence/correlation_heatmap | 200 (OK) | intelligence |
| /api/intelligence/dci | 200 (OK) | intelligence |
| /api/intelligence/learning | 200 (OK) | intelligence |
| /api/intelligence/regime | 200 (OK) | intelligence |
| /api/intelligence/shadow | 200 (OK) | intelligence |
| /api/market/btc | 200 (OK) | market |
| /api/market/sentiment | 200 (OK) | market |
| /api/market/time_heatmap | 200 (OK) | market |
| /api/system/quarantine | 503 (Service Unavailable (expected)) | system |
| /api/system/version | 200 (OK) | system |

---
*OMNIX Decision Governance — Automated Security Audit Tool v1.0*