# OMNIX V6.5 INSTITUTIONAL+ Documentation Index

**Version:** V6.5 INSTITUTIONAL+  
**Last Updated:** December 2024

---

## Quick Navigation

| Document | Location | Description |
|----------|----------|-------------|
| **Project Overview** | `/replit.md` | Main project documentation |
| **Project Structure** | `docs/core/PROJECT_STRUCTURE.md` | Architecture and modules |
| **Database Schema** | `docs/core/DATABASE.md` | 44 tables documented |
| **Environment Config** | `docs/core/MIGRATION_GUIDE.md` | 30+ environment variables |
| **Dashboard Technical Reference** | `docs/core/DASHBOARD_TECHNICAL_REFERENCE.md` | Complete API, security, and architecture reference |
| **Railway Deployment** | `docs/deployment/RAILWAY_DEPLOYMENT.md` | Production deployment |
| **Dashboard Setup** | `docs/deployment/RAILWAY_DASHBOARD_SETUP.md` | Dashboard configuration |
| **Testing Suite** | `omnix_testing/README.md` | Backtesting and validation |

---

## Documentation Structure

```
docs/
├── README.md                          # This index file
│
├── core/                              # Core architecture docs
│   ├── PROJECT_STRUCTURE.md           # System architecture (V6.5)
│   ├── DATABASE.md                    # Database schema (44 tables)
│   ├── MIGRATION_GUIDE.md             # Environment configuration
│   └── DASHBOARD_TECHNICAL_REFERENCE.md  # Dashboard API & security (19 protected endpoints)
│
├── deployment/                        # Deployment guides
│   ├── RAILWAY_DEPLOYMENT.md          # Railway production setup
│   └── RAILWAY_DASHBOARD_SETUP.md     # Dashboard configuration
│
├── testing/                           # Testing documentation
│   └── (see omnix_testing/README.md)
│
└── archive/                           # Historical documentation
    ├── historical/                    # Past version docs
    └── ivan/                          # Ivan documentation
```

---

## V6.5 Key Features

### Core Engines
- **AutoTradingBot V6.4 PREMIUM** - Multi-crypto scanning, tiered signals
- **Non-Markovian Memory Kernel V6.5** - Regime transitions, cyclical patterns
- **Coherence Engine V5.4 ULTRA** - 6-Tier Veto System
- **AI Risk Guardian V5.4** - Overtrading and drawdown protection

### New in V6.5
- **Adaptive Parameter Engine V6.5 ULTRA** - Auto-calibration per regime
- **On-Chain Data Intelligence V6.5** - Whale tracking, exchange flows
- **44 Database Tables** - Complete persistent storage
- **25+ Dashboard API Endpoints** - Real-time data access

### Portfolio Management (6 Modules)
1. Risk Parity
2. Black-Litterman
3. Kelly Criterion
4. HRP (Hierarchical Risk Parity)
5. Mean-Variance
6. CVaR Optimization

### Protection Modules (9 Active)
1. Monte Carlo
2. Kalman Filter
3. HMM (Hidden Markov Model)
4. ARES-STOCK
5. Non-Markovian Memory
6. Coherence Engine
7. Risk Guardian
8. Gap Protection
9. Earnings Protector

---

## Getting Started

### For Developers
1. Read `replit.md` - Project overview
2. Read `docs/core/PROJECT_STRUCTURE.md` - Architecture
3. Review `docs/core/DATABASE.md` - Database schema
4. Check `docs/core/MIGRATION_GUIDE.md` - Environment setup

### For Deployment
1. Read `docs/deployment/RAILWAY_DEPLOYMENT.md` - Main deployment
2. Read `docs/deployment/RAILWAY_DASHBOARD_SETUP.md` - Dashboard

### For Testing
1. Read `omnix_testing/README.md` - Testing suite
2. Run `python omnix_testing/run_premium_validation.py` - Validation

---

## External Dependencies

### APIs & Services
| Service | Purpose | Required |
|---------|---------|----------|
| Kraken | Crypto trading | Yes |
| Alpaca | Stock trading | Optional |
| Google Gemini | Primary AI | Yes |
| OpenAI | AI backup | Optional |
| Anthropic | AI fallback | Optional |
| Finnhub | News/sentiment | Yes |
| Alpha Vantage | Technical indicators | Yes |
| Telegram | Bot interface | Yes |

### Databases
| Service | Purpose |
|---------|---------|
| PostgreSQL (Railway) | Main persistence |
| Redis (Railway) | Cache & state |

---

## Version History

| Version | Date | Key Features |
|---------|------|--------------|
| V6.5 | Dec 2024 | Adaptive Parameter Engine, On-Chain Intelligence |
| V6.4 | Nov 2024 | Portfolio INSTITUTIONAL+, Market Intelligence |
| V6.3 | Nov 2024 | Stock Trading ULTRA, Real Data Integration |
| V6.2 | Oct 2024 | RMS Memory-Enhanced, Derivatives |
| V6.1 | Oct 2024 | Non-Markovian Kernel, Coherence Engine |
| V6.0 | Sep 2024 | Multi-Exchange Arbitrage, Institutional Compliance |

---

## Support

- **Technical Issues:** Review documentation first
- **Architecture Questions:** See `PROJECT_STRUCTURE.md`
- **Database:** See `DATABASE.md`
- **Deployment:** See deployment guides

---

**OMNIX V6.5 INSTITUTIONAL+**  
**Target: $400K seed funding @ $2.5M valuation**
