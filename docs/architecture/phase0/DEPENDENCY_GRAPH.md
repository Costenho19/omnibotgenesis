# OMNIX V6.5.4d Dependency Graph

**Generated:** December 11, 2025  
**Phase:** 0.1 Foundation  
**Status:** Complete

---

## 1. Package Overview

| Package | Files | Primary Purpose |
|---------|-------|-----------------|
| `omnix/` | 10 | Hexagonal ports (Protocol interfaces) |
| `omnix_api/` | 6 | Stripe/B2C integration (future) |
| `omnix_config/` | 5 | Environment management |
| `omnix_core/` | 45 | Bot, cache, strategies, sessions |
| `omnix_dashboard/` | 25 | Flask + Streamlit dashboards |
| `omnix_reports/` | 8 | PDF pitch deck generation |
| `omnix_risk/` | 5 | Portfolio summary, cascade protection |
| `omnix_services/` | 85 | 24 service subpackages |
| `omnix_strategies/` | 4 | Legacy regime switcher |
| `omnix_testing/` | 15 | Backtesting framework |

---

## 2. Internal Dependency Matrix

```
                    IMPORTS FROM →
                    omnix  omnix_config  omnix_core  omnix_services  omnix_dashboard
IMPORTED BY ↓       
─────────────────────────────────────────────────────────────────────────────────────
omnix_core            -         3           10            -              -
omnix_services        -        14           19           16              -
omnix_dashboard       -         2            -            -             17
omnix_testing         -         -            -            -              -
omnix_risk            -         -            -            -              -
```

### Key Observations:

1. **omnix_services** is the most coupled package:
   - Imports 19× from `omnix_core`
   - Imports 14× from `omnix_config`
   - Has 16 internal cross-imports

2. **omnix_dashboard** is self-contained:
   - 17 internal imports
   - Only 2 imports from `omnix_config`
   - No coupling to `omnix_services` (good isolation)

3. **omnix/** (ports) has no inbound dependencies:
   - Ports are defined but not implemented
   - Target for Strangler Fig migration

---

## 3. Dependency Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         OMNIX ARCHITECTURE                           │
└─────────────────────────────────────────────────────────────────────┘

                          ┌──────────────────┐
                          │   omnix_config   │
                          │  (Settings Hub)  │
                          └────────┬─────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
            ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   omnix_core    │◄───│  omnix_services │    │ omnix_dashboard │
│  (Bot, Cache,   │    │   (24 services) │    │  (Flask, API)   │
│   Strategies)   │    │                 │    │                 │
└────────┬────────┘    └────────┬────────┘    └─────────────────┘
         │                      │
         │                      │ uses logger, cache
         │◄─────────────────────┘
         │
         ▼
┌─────────────────┐
│   omnix/ports   │ ◄── UNUSED (Strangler target)
│   (Protocols)   │
└─────────────────┘

Legend:
  ───▶ depends on
  ◄─── is imported by
```

---

## 4. Most Imported Modules

### From omnix_core:
| Module | Import Count | Used By |
|--------|--------------|---------|
| `omnix_core.utils.logger` | 13 | omnix_services, omnix_core |
| `omnix_core.cache.redis_cache` | 6 | omnix_services, omnix_core |

### From omnix_config:
| Module | Import Count | Used By |
|--------|--------------|---------|
| `omnix_config.settings` | 9 | omnix_services, omnix_core |
| `omnix_config.VERSION_BANNER` | 8 | omnix_services, omnix_dashboard |

### From omnix_services:
| Module | Import Count | Used By |
|--------|--------------|---------|
| `omnix_services.risk_management.*` | 11 | omnix_services internal |
| `omnix_services.ai_service.*` | 3 | omnix_services internal |

---

## 5. Circular Import Risks

### Identified Patterns:

1. **omnix_core ↔ omnix_services**:
   - `omnix_services` imports `logger` and `cache` from `omnix_core`
   - Potential for circular if `omnix_core` imports services

2. **omnix_services internal**:
   - 16 internal cross-imports
   - Risk of service-to-service circular deps

### Recommended Resolution (Phase 2):
- Move `logger` and `cache` to `src/omnix/infrastructure/`
- Services should import via dependency injection

---

## 6. External Dependencies (Top 20)

| Package | Version | Purpose |
|---------|---------|---------|
| `python-telegram-bot` | 21.13 | Telegram bot interface |
| `flask` | 3.0.3 | Dashboard web server |
| `sqlalchemy` | 2.0.31 | Database ORM |
| `pandas` | 2.2.3 | Data analysis |
| `numpy` | 1.26.4 | Numerical computing |
| `google-generativeai` | 0.8.3 | Gemini AI |
| `openai` | 1.46.0 | GPT-4 integration |
| `anthropic` | 0.75.0 | Claude integration |
| `krakenex` | 2.2.2 | Kraken exchange API |
| `alpaca-trade-api` | 3.2.0 | Stock trading |
| `redis` | 5.0.7 | Caching layer |
| `psycopg2-binary` | 2.9.10 | PostgreSQL driver |
| `pydantic` | 2.11.7 | Data validation |
| `streamlit` | 1.44.1 | Interactive dashboard |
| `scipy` | 1.15.3 | Scientific computing |
| `ta` | 0.11.0 | Technical analysis |
| `hmmlearn` | 0.3.3 | Hidden Markov Models |
| `dwave-ocean-sdk` | 9.0.0 | Quantum computing |
| `reportlab` | 4.4.1 | PDF generation |
| `tavily-python` | 0.5.0 | Web search |

---

## 7. Migration Priority

Based on coupling analysis, recommended migration order:

| Priority | Package | Reason |
|----------|---------|--------|
| 1 | `omnix_config` | Central settings, few deps |
| 2 | `omnix_core/cache` | Widely imported, low complexity |
| 3 | `omnix_core/utils` | Logger used everywhere |
| 4 | `omnix/ports` | Already defined, needs adapters |
| 5 | `omnix_services/database_service` | Core infrastructure |
| 6 | `omnix_services/ai_service` | Already SOLID (reference model) |
| 7 | `omnix_core/bot` | Core domain logic |
| 8 | `omnix_services/*` | Remaining services |
| 9 | `omnix_dashboard` | Self-contained, last |

---

*Document generated as part of Phase 0 Foundation*
