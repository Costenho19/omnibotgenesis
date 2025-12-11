# OMNIX V6.5.4d INSTITUTIONAL+ Documentation Index

**Last Updated:** December 11, 2025  
**Authoritative Version:** `omnix_config/settings.py` → `VERSION_BANNER`

---

## Quick Navigation

| Document | Purpose | Primary Audience |
|----------|---------|------------------|
| [ARCHITECTURE_REFERENCE.md](ARCHITECTURE_REFERENCE.md) | Complete module catalog, protocol ports, dashboard APIs | Developers |
| [TRADING_OPERATIONS.md](TRADING_OPERATIONS.md) | Trading profiles, flow architecture, operational guides | Operators |
| [MODERNIZATION_ROADMAP.md](MODERNIZATION_ROADMAP.md) | V7.0 refactoring plans (DEFERRED until 500+ trades) | Developers |
| [B2C_IMPLEMENTATION_PLAN.md](B2C_IMPLEMENTATION_PLAN.md) | SaaS monetization roadmap ($19-$49 plans) | Product/Business |

## Architecture Documentation

| Document | Purpose |
|----------|---------|
| [../architecture/ARCHITECTURE_AUDIT_2025.md](../architecture/ARCHITECTURE_AUDIT_2025.md) | Code audit, problems identified, target structure |
| [../architecture/MIGRATION_ROADMAP.md](../architecture/MIGRATION_ROADMAP.md) | Strangler Fig migration plan (5 phases) |
| [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) | Known technical debt and deferred items |

## Investor Documentation

| Document | Purpose |
|----------|---------|
| [../audits/INTERNAL_AUDIT_TRANSPARENCY.md](../audits/INTERNAL_AUDIT_TRANSPARENCY.md) | Investor due diligence report |
| [../audits/DATABASE_AUDIT_REPORT.md](../audits/DATABASE_AUDIT_REPORT.md) | Database integrity audit status |
| [../audits/AUDIT_REPORT_20251208.md](../audits/AUDIT_REPORT_20251208.md) | Code-to-documentation verification |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    OMNIX V6.5.4d INSTITUTIONAL+                  │
├─────────────────────────────────────────────────────────────────┤
│  INTERFACES                                                     │
│  ├── Telegram Bot (enterprise_bot.py)                          │
│  ├── Flask Dashboard (port 5000) - API + Terminal              │
│  └── Streamlit Dashboard (port 8080) - Investor Charts         │
├─────────────────────────────────────────────────────────────────┤
│  CORE ENGINES                                                   │
│  ├── AutoTradingBot V6.5.4d - Multi-crypto scanner + Emergency SL│
│  ├── CoherenceEngine V6.5 ULTRA - 6-tier veto system           │
│  ├── Non-Markovian Kernel V6.5 - Temporal memory               │
│  ├── Risk Guardian V5.4 - Drawdown + overtrading protection    │
│  ├── Macro Trend Veto - Kalman/HMM bearish blocking (V6.5.4d)  │
│  └── ARES V1/V2 (Swing/Scalping) - ACTIVE in PRODUCTION_STABLE │
├─────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                     │
│  ├── PostgreSQL (Railway) - 42 tables, 90% FK coverage         │
│  ├── Redis (Railway) - Caching + state management              │
│  └── DatabaseGateway - Unified connection pool                 │
├─────────────────────────────────────────────────────────────────┤
│  EXTERNAL APIs                                                  │
│  ├── Kraken - Crypto data + execution                          │
│  ├── Alpaca - Stock data                                       │
│  ├── Gemini 2.0 Flash - Primary AI                             │
│  └── Tavily - Web search                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Current System State (December 2025)

| Metric | Status | Target |
|--------|--------|--------|
| Version | V6.5.4d | — |
| Track Record Trades | ~30 | 500+ |
| Win Rate Target | 55%+ | Investor-grade |
| Active Profile | PRODUCTION_STABLE V6.5.4d | — |
| ARES Status | ACTIVE (V1: 70%, V2: 75% confidence) | Track record generation |
| Drawdown Limit | 15% | Allows recovery trading |
| Database Tables | 42 | ✅ Complete |
| Database FK Coverage | 90% (38/42 tables) | ✅ Complete |

### V6.5.4d Key Changes

| Change | Description |
|--------|-------------|
| Emergency Stop Loss | 2% max absolute loss per position (class-level constant) |
| Entry Thresholds | score_moderate=12 (same as strong), only STRONG/VERY_STRONG trades |
| ADA/USD Excluded | Permanently blocked (0% win rate) |
| Macro Trend Veto | Kalman BEARISH -15pts, HMM trending_bear -10pts |

---

## Document Governance

| Type | Location | Maintainer |
|------|----------|------------|
| Core Architecture | `docs/core/` | Development Team |
| Investor Audits | `docs/audits/` | Founders |
| Runtime Config | `omnix_core/config/` | Codebase (single source of truth) |
| API Reference | Flask `/api/` endpoints | Auto-generated from code |
| Technical Debt | `docs/core/TECHNICAL_DEBT.md` | Development Team |

**Note:** Trading parameters should reference `omnix_core/config/trading_profiles.py` directly, not documentation. Documentation reflects code, not the other way around.

---

## Related Files (Single Source of Truth)

| What | Where |
|------|-------|
| Trading Profiles | `omnix_core/config/trading_profiles.py` |
| System Version | `omnix_config/settings.py` → `VERSION_BANNER` |
| Hexagonal Ports | `omnix/ports/*.py` (8 protocol interfaces) |
| Dashboard APIs | `omnix_dashboard/app.py` |
| AI Service | `omnix_services/ai_service/` |
| Emergency SL Constant | `omnix_core/bot/auto_trading_bot.py` → `EMERGENCY_SL_PCT` |
