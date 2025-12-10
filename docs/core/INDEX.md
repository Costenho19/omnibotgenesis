# OMNIX V6.5.4c INSTITUTIONAL+ Documentation Index

**Last Updated:** December 10, 2025  
**Authoritative Version:** `omnix_config/settings.py` → `VERSION_BANNER`

---

## Quick Navigation

| Document | Purpose | Primary Audience |
|----------|---------|------------------|
| [ARCHITECTURE_REFERENCE.md](ARCHITECTURE_REFERENCE.md) | Complete module catalog, protocol ports, dashboard APIs | Developers |
| [TRADING_OPERATIONS.md](TRADING_OPERATIONS.md) | Trading profiles, flow architecture, operational guides | Operators |
| [MODERNIZATION_ROADMAP.md](MODERNIZATION_ROADMAP.md) | V7.0 refactoring plans (DEFERRED until 500+ trades) | Developers |

## Investor Documentation

| Document | Purpose |
|----------|---------|
| [../audits/INTERNAL_AUDIT_TRANSPARENCY.md](../audits/INTERNAL_AUDIT_TRANSPARENCY.md) | Investor due diligence report |
| [../audits/DATABASE_AUDIT_REPORT.md](../audits/DATABASE_AUDIT_REPORT.md) | Database integrity audit status |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    OMNIX V6.5.4c INSTITUTIONAL+                 │
├─────────────────────────────────────────────────────────────────┤
│  INTERFACES                                                     │
│  ├── Telegram Bot (enterprise_bot.py)                          │
│  ├── Flask Dashboard (port 5000) - API + Terminal              │
│  └── Streamlit Dashboard (port 8080) - Investor Charts         │
├─────────────────────────────────────────────────────────────────┤
│  CORE ENGINES                                                   │
│  ├── AutoTradingBot V6.5.4 - Multi-crypto scanner              │
│  ├── CoherenceEngine V6.5 ULTRA - 6-tier veto system           │
│  ├── Non-Markovian Kernel V6.5 - Temporal memory               │
│  ├── Risk Guardian V5.4 - Drawdown + overtrading protection    │
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
| Track Record Trades | 27 | 500+ |
| Win Rate Target | 55%+ | Investor-grade |
| Active Profile | PRODUCTION_STABLE V6.5.4c | — |
| ARES Status | ACTIVE (V1: 70%, V2: 75% confidence) | Track record generation |
| Drawdown Limit | 15% | Allows recovery trading |
| Database FK Coverage | 90% (38/42 tables) | ✅ Complete |

---

## Document Governance

| Type | Location | Maintainer |
|------|----------|------------|
| Core Architecture | `docs/core/` | Development Team |
| Investor Audits | `docs/audits/` | Founders |
| Runtime Config | `omnix_core/config/` | Codebase (single source of truth) |
| API Reference | Flask `/api/` endpoints | Auto-generated from code |

**Note:** Trading parameters should reference `omnix_core/config/trading_profiles.py` directly, not documentation. Documentation reflects code, not the other way around.

---

## Related Files (Single Source of Truth)

| What | Where |
|------|-------|
| Trading Profiles | `omnix_core/config/trading_profiles.py` |
| System Version | `omnix_config/settings.py` → `VERSION_BANNER` |
| Hexagonal Ports | `omnix/ports/*.py` (12 protocol interfaces) |
| Dashboard APIs | `omnix_dashboard/app.py` |
| AI Service | `omnix_services/ai_service/` |
