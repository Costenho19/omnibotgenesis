# OMNIX V6.5.4d Documentation Hub

**Version:** V6.5.4d INSTITUTIONAL+ PREMIUM  
**Last Updated:** December 12, 2025  
**Status:** Production on Railway | Track Record Generation Active

---

## Quick Navigation by Role

### For Developers
| Document | Description |
|----------|-------------|
| [Current Architecture](current/ARCHITECTURE.md) | System modules, ports, services (V6.5.4d) |
| [Technical Debt](current/TECHNICAL_DEBT.md) | Known issues, deferred refactoring |
| [Migration Plan](transformation/MIGRATION_PLAN.md) | V7.0 hexagonal architecture roadmap |
| [ADRs](transformation/adr/) | Architecture Decision Records |

### For Operators
| Document | Description |
|----------|-------------|
| [Trading Operations](current/TRADING_OPERATIONS.md) | Profiles, risk management, troubleshooting |
| [Railway Deployment](operations/deployment/RAILWAY_DEPLOYMENT.md) | Production deployment guide |
| [Dashboard Setup](operations/deployment/RAILWAY_DASHBOARD_SETUP.md) | Flask + Streamlit configuration |

### For Investors
| Document | Description |
|----------|-------------|
| [One Pager](business/investor/one_pager.md) | Executive summary |
| [Financial Projections](business/investor/financial_projections.md) | Revenue forecasts |
| [Pitch Deck](business/investor/pitch_deck.html) | Full presentation |

### For Business/Product
| Document | Description |
|----------|-------------|
| [B2C SaaS Plan](business/B2C_SAAS_PLAN.md) | "Asesor Personal IA" monetization roadmap |

---

## Documentation Structure

```
docs/
├── README.md                         <- You are here (global index)
│
├── current/                          <- V6.5.4d System State
│   ├── ARCHITECTURE.md               <- Modules, ports, services, DB schema
│   ├── TRADING_OPERATIONS.md         <- Profiles, ARES, risk management
│   └── TECHNICAL_DEBT.md             <- Known issues, deferred work
│
├── transformation/                   <- V7.0 Migration Plan
│   ├── ARCHITECTURE_AUDIT.md         <- Diagnostic, problems identified
│   ├── MIGRATION_PLAN.md             <- Strangler Fig phases, timeline
│   └── adr/                          <- Architecture Decision Records
│       └── ADR-001-hexagonal.md      <- Hexagonal migration strategy
│
├── business/                         <- Business & Product
│   ├── B2C_SAAS_PLAN.md              <- SaaS monetization ($19-$49 plans)
│   └── investor/                     <- Pitch decks, projections
│
├── operations/                       <- Operational Guides
│   ├── deployment/                   <- Railway guides
│   └── experimental/                 <- ARES development, quantum roadmap
│
├── compliance/                       <- Audits & Verification
│   └── audits/                       <- Code audits, DB audits
│
└── history/                          <- Archived Documentation
    └── archive/                      <- Historical decisions
```

---

## Current System Overview (V6.5.4d)

```
┌─────────────────────────────────────────────────────────────────┐
│                    OMNIX V6.5.4d INSTITUTIONAL+                  │
├─────────────────────────────────────────────────────────────────┤
│  INTERFACES                                                      │
│  ├── Telegram Bot (enterprise_bot.py) - Primary user interface  │
│  ├── Flask Dashboard (port 5000) - API + Web terminal           │
│  └── Streamlit Dashboard (port 8080) - Investor visualization   │
├─────────────────────────────────────────────────────────────────┤
│  CORE ENGINES                                                    │
│  ├── AutoTradingBot V6.5.4d - Multi-crypto scanner + 2% SL      │
│  ├── CoherenceEngine V6.5 ULTRA - 6-tier veto system            │
│  ├── Non-Markovian Kernel V6.5 - Temporal memory                │
│  ├── Risk Guardian V5.4 - Drawdown + overtrading protection     │
│  └── ARES V1/V2 (Swing/Scalping) - Track record generation      │
├─────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                      │
│  ├── PostgreSQL (Railway) - 42 tables, 90% FK coverage          │
│  ├── Redis (Railway) - Caching + state management               │
│  └── DatabaseGateway - Unified connection pool                  │
├─────────────────────────────────────────────────────────────────┤
│  EXTERNAL APIs                                                   │
│  ├── Kraken - Crypto data + execution                           │
│  ├── Alpaca - Stock data                                        │
│  ├── Gemini 2.0 Flash - Primary AI                              │
│  └── Tavily - Web search                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## V6.5.4d Key Changes (December 2025)

| Change | Implementation | Impact |
|--------|---------------|--------|
| Emergency Stop Loss | `EMERGENCY_SL_PCT = 0.02` | Max 2% loss per position |
| Entry Thresholds | `score_moderate = 12` | Only STRONG/VERY_STRONG trades |
| ADA/USD Excluded | `CalibrationTier.EXCLUDED` | Blocked (0% win rate) |
| Macro Trend Veto | Kalman -15pts, HMM -10pts | Blocks bearish trend trades |

---

## Track Record Progress

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Trades | ~30 | 500+ | 8-9 weeks |
| Win Rate | TBD | 55%+ | Ongoing |
| ARES Strategies | Active | Track record | Separate metrics |

**Goal:** Generate verifiable paper trading track record for $1M seed funding at $11.5M pre-money valuation.

---

## Migration Status (V7.0)

| Phase | Name | Status |
|-------|------|--------|
| 0 | Foundation | ✅ Complete (Dec 11, 2025) |
| 1 | Bootstrap & Config | ⬜ Ready to start |
| 2 | Domain & Application | 🔒 Blocked (500 trades) |
| 3 | Interfaces | 🔒 Blocked (500 trades) |
| 4 | Cleanup | 🔒 Blocked (500 trades + 14 days) |

See [MIGRATION_PLAN.md](transformation/MIGRATION_PLAN.md) for details.

---

## Document Governance

| Type | Owner | Update Frequency |
|------|-------|------------------|
| Current Architecture | Development Team | Per release |
| Trading Operations | Operations Team | Per parameter change |
| Migration Plan | Architecture Team | Per phase completion |
| Investor Docs | Founders | Per milestone |
| Compliance/Audits | Founders | Per audit cycle |

**Single Source of Truth:**
- Trading parameters: `omnix_core/config/trading_profiles.py`
- System version: `omnix_config/settings.py` → `VERSION_BANNER`
- Project overview: `/replit.md`

---

*OMNIX V6.5.4d INSTITUTIONAL+ PREMIUM*  
*Target: $1M seed @ $11.5M pre-money valuation*
