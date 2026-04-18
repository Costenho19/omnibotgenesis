# CODE AUDIT: omnix_services/ (189 files)
## OMNIX — Phase 2B
**Date**: December 29, 2025  
**Auditor**: AI Assistant  
**Scope**: Service layer modules (189 Python files)

---

## Complete Subdirectory Inventory (22 directories + root)

| # | Subdirectory | Files | Category |
|---|--------------|-------|----------|
| 1 | ai_service/ | 35 | AI Services |
| 2 | trading_service/ | 19 | Trading Services |
| 3 | stock_trading/ | 19 | Stock Trading |
| 4 | market_data/ | 17 | Market Data |
| 5 | risk_management/ | 8 | Risk Management |
| 6 | portfolio_management/ | 8 | Portfolio Management |
| 7 | derivatives/ | 8 | Derivatives |
| 8 | database_service/ | 8 | Database Services |
| 9 | optimization/ | 7 | Optimization |
| 10 | analytics/ | 7 | Analytics |
| 11 | telegram_service/ | 6 | Telegram Service |
| 12 | monitoring/ | 6 | Monitoring |
| 13 | community_intelligence/ | 6 | Community Intelligence |
| 14 | execution_service/ | 5 | Execution Service |
| 15 | web_search_service/ | 4 | Web Search |
| 16 | notifications/ | 4 | Notifications |
| 17 | market_intelligence/ | 4 | Market Intelligence |
| 18 | concurrency/ | 4 | Concurrency |
| 19 | voice_service/ | 3 | Voice Service |
| 20 | user_settings/ | 3 | User Settings |
| 21 | coherence_service/ | 3 | Coherence Engine |
| 22 | adaptive_engine/ | 2 | Adaptive Engine |
| - | Root files | 3 | Module init, symbol classifier, news scraper |
| **TOTAL** | | **189** | |

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Files | 189 |
| Total Subdirectories | 22 |
| Critical Services | 4 (ai_service, trading_service, telegram_service, database_service) |
| Legacy Adapters | 2 (LegacyAIServiceAdapter, DatabaseManager adapter) |
| Architecture | Dependency Injection + Hexagonal ports |
| Multi-provider AI | 3 (Gemini, OpenAI, Anthropic) |

### Health Status: GOOD
- Modern DI architecture with legacy adapters for backward compatibility
- Multi-provider AI with automatic failover
- Fork-safe database gateway for multi-process support
- Versioned migration system for schema management

---

## Service Category Analysis

### CATEGORY 1: AI SERVICES (35 files) - CRITICAL

**Location**: `omnix_services/ai_service/`

**Key Components**:
| Component | File | Purpose |
|-----------|------|---------|
| ConversationalAIService | ai_service.py | Core AI orchestrator |
| AIModelsManager | ai_models.py | Multi-model management with retry |
| RoutingAIGateway | providers/routing_gateway.py | Load balancing + failover |
| ConversationalBrain | conversational_brain.py | Trade reasoning + evaluation |
| AIServiceContainer | container.py | DI container (dependency-injector) |
| ErrorClassifier | ai_error_handler.py | 8-category error classification |

**AI Providers Supported**:
| Provider | Model | File |
|----------|-------|------|
| Google Gemini | 2.0 Flash | providers/gemini_provider.py |
| OpenAI | GPT-4o | providers/openai_provider.py |
| Anthropic | Claude | providers/anthropic_provider.py |

**Architecture Patterns**:
- Dependency Injection via `dependency-injector` library
- Template Method in BaseAIProvider
- Failover with exponential backoff
- Protocol-based interfaces (AIGatewayProtocol)

**Legacy Adapter** (for backward compatibility):
```python
# omnix_services/ai_service/adapters/legacy_adapter.py
class LegacyAIServiceAdapter:
    """Wraps new DI-based RoutingAIGateway for legacy code"""
```
**STATUS**: Active - provides `get_ai_service()` for old code

**Type Safety Fix Applied** (Dec 28):
- `safe_float()` in conversational_brain.py (11 application sites)

---

### CATEGORY 2: TRADING SERVICES (19 files) - CRITICAL

**Location**: `omnix_services/trading_service/`

**Key Components**:
| Component | File | Scoring Weight |
|-----------|------|----------------|
| MonteCarloSimulator | monte_carlo.py | VETO (penalties only) |
| DualKalmanTrendFilter | kalman_filter.py | 15 pts |
| HMMRegimeDetector | hmm_regime.py | 25 pts |
| KellyCriterionOptimizer | kelly_criterion.py | 10 pts (modifier) |
| QuantumMomentumStrategy | quantum_momentum.py | VETO (penalties only) |
| BlackSwanDetector | advanced_features.py | VETO (penalties only) |

**Recent Fixes**:
- Dec 27: Added `filter_and_predict()` to DualKalmanTrendFilter
- Dec 27: Added `analyze()` method to BlackSwanDetector

**Legacy Pattern Identified**:
```python
# omnix_services/trading_service/paper_trading_manager.py line 552
def _save_paper_balance_legacy(self, balance_data: Dict) -> bool:
    """DEPRECATED: Fallback to memory when PostgreSQL fails"""
```
**ACTION**: Mark as DEPRECATED, ensure enterprise path is primary

---

### CATEGORY 3: TELEGRAM SERVICE (6 files) - HIGH

**Location**: `omnix_services/telegram_service/`

**Key Components**:
| Component | File | Purpose |
|-----------|------|---------|
| EnterpriseTelegramBot | enterprise_bot.py | Main bot class |
| CallbackHandler | callback_handler.py | Inline button handling |
| InlineKeyboardsManager | inline_keyboards.py | Menu generation |

**Commands Supported**: 50+ commands organized by category:
- Basic: `/start`, `/help`, `/precio`, `/status`
- Trading: `/balance`, `/analisis`, `/montecarlo`, `/blackswan`
- Paper Trading: `/paper_start`, `/paper_balance`, `/paper_buy`
- Auto-Trading: `/auto_start`, `/auto_stop`, `/auto_status`
- Stock Trading: `/analizar`, `/balance_bolsa`, `/comprar_bolsa`
- Community: `/feedback`, `/community_stats`, `/top_strategies`
- Risk Management: `/rms`, `/rms_limits`, `/emergency_halt`

**V7 Hexagonal Integration**:
```python
# enterprise_bot.py lines 255-274
if V7_CONTAINER_AVAILABLE:
    self.v7_ai_gateway = get_ai_gateway() if use_ai else None
    self.v7_voice_service = get_voice_service() if use_voice else None
```

**No Deprecated Handlers Found**

---

### CATEGORY 4: DATABASE SERVICES (8 files) - CRITICAL

**Location**: `omnix_services/database_service/`

**Key Components**:
| Component | File | Purpose |
|-----------|------|---------|
| DatabaseServiceEnterprise | database_service.py | Main PostgreSQL service |
| DatabaseGateway | database_gateway.py | Fork-safe connection pool |
| DatabaseManager | database_manager.py | Legacy adapter |
| PaperTradingRepository | paper_trading_repository.py | Real data queries |
| MigrationRunner | migrations/registry.py | Schema migrations |

**Database URL Resolution** (3-tier fallback):
1. `os.environ['DATABASE_URL']`
2. `env_manager.get('DATABASE_URL')`
3. `settings.database.url`

**Migration System**:
| Version | Purpose |
|---------|---------|
| V001 | Sync trade_reasonings.pair column |
| V002 | Fix profit vs profit_loss naming |
| V003 | Ensure symbol column exists |
| V004 | Enable Row-Level Security |

**Schema Fixes Applied**:
- Type fix: risk_guardian_events.user_id BIGINT → TEXT
- Foreign keys: ON DELETE CASCADE for 12+ tables
- Check constraints: trades.status, community_signals.signal_type

**Fork-Safe Pattern**:
```python
# database_gateway.py lines 62-78
@classmethod
def get_instance(cls) -> 'DatabaseGateway':
    """Fork-safe singleton - reinitializes after Gunicorn fork"""
```

---

### CATEGORY 5: STOCK TRADING (19 files)

**Location**: `omnix_services/stock_trading/`

**Purpose**: Alpaca integration for stock trading

**Status**: ACTIVE - Parallel to crypto trading

---

### CATEGORY 6: MARKET DATA (17 files)

**Location**: `omnix_services/market_data/`

**Submodules**:
- `intelligence/` - Arbitrage scanner, executor
- `feeds/` - Real-time data feeds

**Status**: ACTIVE

---

### CATEGORY 7: DERIVATIVES (8 files)

**Location**: `omnix_services/derivatives/`

**Purpose**: Futures, hedging, margin management

**Status**: ACTIVE

---

### CATEGORY 8: RISK MANAGEMENT (8 files)

**Location**: `omnix_services/risk_management/`

**Purpose**: Risk management services

**Status**: ACTIVE

---

### CATEGORY 9: PORTFOLIO MANAGEMENT (8 files)

**Location**: `omnix_services/portfolio_management/`

**Purpose**: Institutional portfolio optimizer

**Status**: ACTIVE

---

### CATEGORY 10: OTHER SERVICES (58 files)

| Service | Files | Purpose | Status |
|---------|-------|---------|--------|
| analytics/ | 7 | Analytics engine | ACTIVE |
| optimization/ | 7 | Performance optimizer | ACTIVE |
| community_intelligence/ | 6 | Community features | ACTIVE |
| monitoring/ | 6 | Health checks, latency | ACTIVE |
| execution_service/ | 5 | Execution protocol | ACTIVE |
| concurrency/ | 4 | Concurrency management | ACTIVE |
| market_intelligence/ | 4 | Fear/Greed, Finnhub | ACTIVE |
| notifications/ | 4 | Trade notifications | ACTIVE |
| web_search_service/ | 4 | Tavily integration | ACTIVE |
| coherence_service/ | 3 | Coherence Engine V5.4 | CRITICAL |
| user_settings/ | 3 | User preferences | ACTIVE |
| voice_service/ | 3 | TTS/STT (gTTS) | ACTIVE |
| adaptive_engine/ | 2 | Parameter calibration | ACTIVE |
| **Subtotal** | **58** | | |

**Plus Root Files (3)**: `__init__.py`, `symbol_classifier.py`, `news_scraper.py`

**Category Verification**:
- Categories 1-9: 35+19+6+8+19+17+8+8+8 = 128 files
- Category 10: 58 files
- Root files: 3 files
- **TOTAL: 189 files** (verified)

---

## Issues Summary

### Critical Issues: NONE

### Medium Priority Issues

| ID | Service | Issue | Recommendation |
|----|---------|-------|----------------|
| M1 | trading_service | `_save_paper_balance_legacy` deprecated | Remove after verification |
| M2 | ai_service | LegacyAIServiceAdapter still in use | Plan migration timeline |

### Low Priority / Technical Debt

| ID | Service | Issue | Recommendation |
|----|---------|-------|----------------|
| L1 | database_service | 1200+ lines in database_service.py | Split migrations to separate files |
| L2 | telegram_service | 127 LSP diagnostics | Address type hints |
| L3 | voice_service | 3 LSP diagnostics | Minor type fixes |

---

## Legacy Adapters (Backward Compatibility)

| Adapter | Location | Purpose | Migration Status |
|---------|----------|---------|------------------|
| LegacyAIServiceAdapter | ai_service/adapters/ | Wraps RoutingAIGateway | Active, plan deprecation |
| DatabaseManager | database_service/ | Wraps DatabaseServiceEnterprise | Active, needed for legacy |
| get_ai_service() | ai_service/__init__.py | Returns legacy adapter | Active, many consumers |

---

## Deletion Candidates: NONE

All 189 files are actively used. Legacy adapters are needed for backward compatibility.

---

## Security Findings

| Finding | Status | Details |
|---------|--------|---------|
| API Key Management | SECURE | Keys from environment, never logged |
| Error Messages | SAFE | User messages don't expose internals |
| Fork Safety | IMPLEMENTED | DatabaseGateway reinits after fork |
| Rate Limiting | ACTIVE | Per-provider rate limits |

---

## Next Steps

1. **Phase 2C**: Audit src/omnix/ (99 files - V7 hexagonal architecture)
2. **LSP Fixes**: Address 145 diagnostics in auto_trading_bot.py
3. **Migration Planning**: Timeline for legacy adapter deprecation

---

**Audit Completed**: December 29, 2025  
**Next Review**: After Phase 2C completion
