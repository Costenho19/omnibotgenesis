# OMNIX INSTITUTIONAL+ - Module Catalog

> **Version Control**: Current system version is defined in `omnix_config/settings.py`. 
> See VERSION_BANNER for the authoritative version string.

**Document Version:** 1.1  
**Created:** December 6, 2025  
**Last Updated:** December 8, 2025  
**Status:** ✅ COMPLETE - Exhaustive Module Inventory (AI Service DI Added)

---

## Executive Summary

| Metric | Count |
|--------|-------|
| **Total Python Files** | 160+ |
| **Total Lines of Code** | ~95,000 |
| **Core Modules (omnix_core)** | 20 (in 9 subpackages + root) |
| **Service Subpackages (omnix_services)** | 22 |
| **Dashboard Files (omnix_dashboard)** | 40+ |
| **Database Tables** | 42 |
| **API Endpoints** | 26+ |

---

## 1. omnix_core/ - Core Trading Engine

**Purpose:** Central trading logic, strategies, security, caching, and user sessions.  
**Total Lines:** 20,131

### 1.1 Package Structure

```
omnix_core/
├── trading_system.py         # 5,576 lines - Core engine
├── bot/
│   ├── auto_trading_bot.py   # 3,932 lines - 24/7 trading automation
│   └── paper_trading.py      # ~400 lines - Paper trading manager
├── strategies/
│   ├── ares_v1.py            # 679 lines - Swing Trading Protocol
│   ├── ares_v2.py            # 587 lines - Scalping M1 Protocol
│   ├── caes_module.py        # ~300 lines - Confidence-Adaptive Entry System
│   └── non_markovian_kernel.py # 630 lines - Temporal Memory Kernel
├── security/
│   └── pqc_security.py       # 468 lines - Real Post-Quantum (Kyber-768, Dilithium-3)
├── risk/
│   └── rollback_protocol.py  # Algorithmic Rollback Protocol V6.5.4
├── quantum/
│   ├── physics_validator.py  # 4,459 lines - 24 verified physics formulas
│   ├── testing_framework.py  # 852 lines - AI response validation
│   ├── enhancements.py       # 587 lines - QRNG + Portfolio Optimizer
│   └── dwave_qaoa.py         # 350 lines - D-Wave Quantum Annealing
├── cache/
│   ├── redis_cache.py        # ~300 lines - Redis caching layer
│   └── redis_state.py        # ~234 lines - State management
├── sessions/
│   └── user_session_manager.py  # 561 lines - Multi-user session management
├── context/
│   └── real_data_provider.py    # 313 lines - Real data provider
├── config/
│   └── trading_profiles.py      # Trading profile configurations
└── utils/
    ├── logger.py             # ~200 lines - Colored formatter
    └── rate_limiter.py       # ~160 lines - Rate limiting
```

### 1.2 Key Modules

#### 1.2.1 trading_system.py (5,576 lines)

**Purpose:** Core trading engine orchestrating all strategies and Kraken integration.

**Key Classes:**
- `TradingSystem` - Main orchestrator
- Multi-currency trading with auto-switch
- ARES V1/V2 strategy integration
- Post-quantum security integration

**Dependencies:** ccxt, numpy, scipy, requests

---

#### 1.2.2 auto_trading_bot.py (3,932 lines)

**Purpose:** 24/7 automated trading with 10 institutional strategies.

**INSTITUTIONAL+ Features:**
- Multi-crypto scanning (11 pairs)
- Tiered signal strength (WEAK → MODERATE → STRONG → ULTRA)
- Ramp-up system for gradual position increases
- HMM quality filter
- Drawdown protection

**10 Trading Strategies:**
1. Monte Carlo Simulation (10,000 paths)
2. Black Swan Detection (Kurtosis/Skewness)
3. Sentiment Analysis
4. Kelly Criterion Position Sizing
5. HMM Regime Detection (4 states)
6. Kalman Filter (adaptive signal filtering)
7. Quantum Momentum (6-component proprietary)
8. ARES V1 - Swing Trading (55-65% win rate)
9. ARES V2 - Scalping M1 (60-70% win rate)
10. Non-Markovian Kernel - Temporal memory K(t-s)

**Key Methods:**
- `run_trading_cycle()` - Main trading loop
- `analyze_pair()` - Multi-strategy analysis
- `execute_signal()` - Trade execution with veto system
- `scan_all_pairs()` - 11-pair crypto scanner

**V6.5.4 Contradiction Monitor (Lines ~2054-2070):**

Passive logging system to detect decision contradictions for future optimization.

| Field | Source | Description |
|-------|--------|-------------|
| `coherence_rec` | `coherence_report.decision_recommendation` | HOLD/BUY/SELL from Coherence Engine |
| `final_action` | `decision['action']` | Final trade decision |
| `coherence_pct` | `coherence_report.coherence_score` | Coherence percentage (0-100%) |
| `signal_strength` | `decision['signal_strength']` | WEAK/MODERATE/STRONG/VERY_STRONG/ULTRA |
| `amount` | `decision['amount_usd']` | Trade size in USD |
| `symbol` | `getattr(self, 'current_symbol', 'UNKNOWN')` | Trading pair (safe access) |

**Trigger Condition:**
```python
# Guard: solo ejecutar si coherence_report existe y tiene atributos requeridos
if coherence_report and hasattr(coherence_report, 'decision_recommendation'):
    if coherence_rec == 'HOLD' and final_action in ['BUY', 'SELL'] and decision.get('should_trade'):
        logger.warning(f"⚡ CONTRADICTION MONITOR V6.5.4: ...")
```

**Log Format:**
```
⚡ CONTRADICTION MONITOR V6.5.4: Coherence=HOLD (53.4%) vs Final=BUY | Signal=VERY_STRONG | Amount=$1500.00 | Symbol=BTC/USD
```

**Purpose:** Phase 1 monitoring only - does NOT modify trading behavior. Data collected for future Phase 2 automated mitigation decisions.

---

#### 1.2.3 ARES Protocols (ares_v1.py, ares_v2.py)

| Strategy | Lines | Win Rate | Timeframe | Stop Loss |
|----------|-------|----------|-----------|-----------|
| **ARES V1** | 679 | 55%-65% | Swing | -0.95% |
| **ARES V2** | 587 | 60%-70% | M1 Scalping | -0.28% |

**ARES V1 Architecture (3 Layers):**
1. **ANF (Adaptive Noise Filter):** Filters 90% of low-value trades
2. **ISA (Institutional Signal Analysis):** 6 professional signals
3. **SXE (Smart Execution Engine):** Hedge fund-style execution

**ARES V2 Additions:**
- Micro-timeframe optimization (M1)
- Tighter risk controls
- Faster entry/exit logic

---

#### 1.2.4 Non-Markovian Kernel (630 lines)

**Purpose:** Memory-based temporal analysis that remembers past market patterns.

**Kernel Equation:**
```
K(t-s) = exp(-|t-s|/τ) × [1 + ε × cos(Ω(t-s))]
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| τ (tau) | 12 hours | Memory decay constant |
| ε (epsilon) | 0.35 | Oscillation amplitude |
| Ω (omega) | 0.523 rad | Oscillation frequency |
| Window | 168 periods | 1 week of hourly data |

**Key Methods:**
- `compute_kernel()` - Calculate memory weight
- `get_historical_similarity()` - Pattern matching
- `regime_transition_detection()` - Regime change alerts

---

#### 1.2.5 CAES Module (Confidence-Adaptive Entry System)

**Purpose:** Dynamic position sizing based on Non-Markovian Kernel confidence.

**Sigmoid Aggression Function:**
```
multiplier = 0.5 + 2.5 × sigmoid(confidence_score - 0.5)
```

**Limits:** 0.5x to 3.0x position multiplier with safety caps.

**Sub-Regime Detection:**
- FLOOR_RESCUE
- RECOVERY
- NEUTRAL
- MOMENTUM

---

#### 1.2.6 Post-Quantum Security

| Module | Lines | Algorithm | Standard |
|--------|-------|-----------|----------|
| `pqc_security.py` | 468 | Kyber-768 + Dilithium-3 | NIST FIPS 203/204 |
| `pqc_encryption.py` | 199 | Simulated fallback | - |

**Library:** pypqc (when available)

---

## 2. omnix_services/ - Service Layer

**Total Subpackages:** 22  
**Root-Level Modules:** 2  
**Total Lines:** 62,613

### 2.1 Complete Subpackage Inventory

| Subpackage | Files | Key Lines | Primary Purpose |
|------------|-------|-----------|-----------------|
| **database_service/** | 4 | 4,860 | PostgreSQL operations |
| **telegram_service/** | 5 | 7,654 | Telegram bot interface |
| **trading_service/** | 15 | ~4,500 | Trade execution, analysis |
| **ai_service/** | 21 | ~5,500 | Multi-AI integration (SOLID + DI refactored Dec 8, 2025) |
| **monitoring/** | 5 | ~3,600 | Metrics, Risk Guardian |
| **risk_management/** | 8 | ~3,200 | Limits, alerts, circuit breaker |
| **derivatives/** | 7 | ~4,100 | Futures, margin, hedging |
| **coherence_service/** | 2 | 637 | 6-tier veto system |
| **portfolio_management/** | 6 | ~2,500 | Markowitz, Black-Litterman |
| **stock_trading/** | 15 | ~3,000 | Alpaca integration |
| **adaptive_engine/** | 2 | 936 | Auto-calibration |
| **on_chain_service/** | 5 | ~1,500 | Blockchain analytics |
| **community_intelligence/** | 5 | ~1,200 | Crowdsourced signals |
| **notifications/** | 4 | ~800 | Trade alerts, summaries |
| **market_data/** | 12 | ~2,500 | Real-time data, arbitrage |
| **market_intelligence/** | 4 | ~800 | Fear/Greed, Finnhub |
| **optimization/** | 7 | ~2,000 | Auto-optimizer, ML |
| **analytics/** | 3 | ~600 | Fibonacci, volume profile |
| **alerts/** | 2 | ~300 | Smart alert engine |
| **voice_service/** | 3 | ~500 | TTS, Whisper |
| **user_settings/** | 3 | 693 | User preferences |
| **concurrency/** | 4 | ~600 | Cache, resource management |
| **web_search_service/** | 2 | ~400 | Tavily web search + intent detection |

### 2.3 AI Service Architecture (SOLID + Dependency Injection)

**Refactored:** December 8, 2025  
**Pattern:** Hexagonal Architecture with Ports & Adapters

The AI Service module has been fully refactored following SOLID principles with dependency injection:

```
omnix_services/ai_service/
├── interfaces/               # Protocol definitions (PEP 544)
│   ├── __init__.py
│   ├── ai_gateway.py         # AIGatewayProtocol, TextGenerationRequest/Response
│   ├── prompt_builder.py     # PromptBuilderProtocol
│   ├── style_renderer.py     # StyleRendererProtocol
│   └── context_provider.py   # ContextProviderProtocol
├── providers/                # Concrete AI implementations
│   ├── __init__.py
│   ├── gemini_provider.py    # GeminiAIGateway (Primary)
│   ├── openai_provider.py    # OpenAIGateway (Fallback)
│   ├── anthropic_provider.py # AnthropicGateway (Fallback)
│   └── routing_gateway.py    # RoutingAIGateway (load balancing + failover)
├── adapters/                 # Legacy compatibility
│   └── legacy_adapter.py     # LegacyAIServiceAdapter
├── testing/                  # Mock implementations for unit tests
│   └── fakes.py              # FakeAIGateway, InMemoryContextProvider
├── container.py              # AIServiceContainer (dependency-injector library)
├── ai_service.py             # ConversationalAIService (DI-enabled)
├── ai_models.py              # AIModelsManager
├── ai_styles.py              # VisualStylesManager
├── ai_prompts.py             # PromptsContextManager
├── video/                    # Video Learning Module (2,120 lines)
│   ├── analyzer.py           # VideoAnalyzerUltra (1,346 lines)
│   ├── learning_analyzer.py  # VideoLearningAnalyzer (344 lines)
│   └── integration.py        # VideoLearningIntegration (416 lines)
└── __init__.py               # Public API exports
```

### 2.3.1 Video Learning Module (Added Dec 9, 2025)

**Purpose:** Advanced video analysis for trading education and parameter auto-tuning.

| Component | Lines | Purpose |
|-----------|-------|---------|
| `VideoAnalyzerUltra` | 1,346 | Multi-modal video analysis (visual + audio) |
| `VideoLearningAnalyzer` | 344 | Technical parameter extraction from transcripts |
| `VideoLearningIntegration` | 416 | Bridges video insights to AutoLearningSystem |

**Capabilities:**
- GPT-4 Vision API for chart pattern detection
- Gemini 2.0 Flash Multimodal for frame analysis
- OpenAI Whisper for audio transcription
- Automatic RSI/EMA/MACD parameter extraction
- Safe parameter change proposals with validation

**Key Classes:**
```python
from omnix_services.ai_service.video import (
    VideoAnalyzerUltra,      # Visual + audio analysis
    VideoLearningAnalyzer,   # Parameter extraction
    VideoLearningIntegration # AutoLearning bridge
)
```

**Key Interfaces (Protocols):**

| Interface | Purpose | Methods |
|-----------|---------|---------|
| `AIGatewayProtocol` | Text generation contract | `generate_text()`, `generate_stream()`, `health_check()` |
| `PromptBuilderProtocol` | System prompt construction | `build_system_prompt()`, `build_context_prompt()` |
| `StyleRendererProtocol` | Visual formatting | `render_response()`, `format_error()` |
| `ContextProviderProtocol` | Trading context | `get_market_context()`, `get_trading_context()` |

**Provider Implementations:**

| Provider | Model | Priority | Features |
|----------|-------|----------|----------|
| `GeminiAIGateway` | Gemini 2.0 Flash | Primary | Streaming, async |
| `OpenAIGateway` | GPT-4o | Fallback 1 | Streaming, async |
| `AnthropicGateway` | Claude 3.5 | Fallback 2 | Streaming, async |
| `RoutingAIGateway` | All | Orchestrator | Load balancing, automatic failover |

**Usage Examples:**

```python
# New DI-based API (Recommended)
from omnix_services.ai_service import get_ai_gateway, TextGenerationRequest
gateway = get_ai_gateway()
response = await gateway.generate_text(TextGenerationRequest(prompt="Analyze BTC"))

# Legacy API (Backward Compatible)
from omnix_services.ai_service import get_ai_service
service = get_ai_service()
response = await service.generate_response(chat_id, message)

# Testing with Fakes
from omnix_services.ai_service.testing import FakeAIGateway
fake_gateway = FakeAIGateway(responses={"default": "Mocked response"})
```

**SOLID Compliance:**
- **S (Single Responsibility)**: Each provider handles exactly one AI model
- **O (Open/Closed)**: New providers added without modifying existing code
- **L (Liskov Substitution)**: Any provider interchangeable via Protocol
- **I (Interface Segregation)**: Small, focused interfaces
- **D (Dependency Inversion)**: High-level modules depend on abstractions

### 2.3.2 Quantum Physics Validator Integration

**Location:** `omnix_core/quantum/physics_validator.py` (4,460 lines)  
**Integration:** `ai_prompts.py` imports with graceful fallback

The AI Service integrates with the Quantum Physics Validator to ensure scientifically accurate responses about quantum optics and QRNG physics. The integration uses optional import pattern:

```python
# ai_prompts.py - Graceful fallback pattern
try:
    from omnix_core.quantum.physics_validator import get_quantum_physics_context
    QUANTUM_PHYSICS_VALIDATOR_AVAILABLE = True
except ImportError:
    QUANTUM_PHYSICS_VALIDATOR_AVAILABLE = False
```

**Status:** ✅ VERIFIED (Dec 9, 2025) - Integration works with graceful degradation when validator unavailable.

### 2.3.3 Known Technical Debt (AI Service)

**Import-Time Side Effects (Low Priority):**

The following modules emit logs/prints at import time. These do not affect functionality but should be cleaned up in future refactoring:

| File | Line | Side Effect | Impact |
|------|------|-------------|--------|
| `ai_service.py` | 10 | `print("✅ ai_service.py CARGADO...")` | Debug noise in logs |
| `ai_prompts.py` | 14 | `print("✅ ai_prompts.py CARGADO...")` | Debug noise in logs |
| `ai_prompts.py` | 27, 38 | `logger.info()` on import | Expected behavior (startup confirmation) |

**Recommendation:** Future cleanup should convert prints to DEBUG-level logging with feature flag control. Not blocking for production.

### 2.2 Critical Modules (>1,000 lines)

| Module | Lines | Purpose |
|--------|-------|---------|
| `telegram_service/enterprise_bot.py` | 7,654 | Complete Telegram interface |
| `database_service/database_service.py` | 4,860 | Enterprise DB operations |
| `monitoring/advanced_intelligence.py` | 1,330 | Advanced analytics |
| `trading_service/advanced_features.py` | 1,216 | Trading enhancements |
| `ai_service/video/analyzer.py` | 1,346 | Video learning (VideoAnalyzerUltra) |
| `monitoring/analytics_engine.py` | 1,092 | Performance analytics |
| `trading_service/paper_trading_manager.py` | 1,023 | Paper trading simulation |

### 2.3 Database Service Architecture

```
database_service/
├── database_gateway.py    # Fork-safe singleton (Phase 2)
├── database_manager.py    # Legacy adapter pattern
├── database_service.py    # Enterprise service (4,860 lines)
└── optimize_indexes.sql   # Index optimization
```

**Key Architecture:**
- `DatabaseGateway`: Fork-safe for Gunicorn workers
- Feature flag: `USE_UNIFIED_GATEWAY` (default: false)
- **Contract:** All queries use tuple-based rows `row[n]`, NOT dict access

---

### 2.4 Trading Service Components

```
trading_service/
├── trading_service.py        # Main trading operations
├── kraken_client.py          # Kraken API client
├── position_manager.py       # Position tracking (DynamicPositionManager)
├── paper_trading_manager.py  # Paper trading simulation (1,023 lines)
├── monte_carlo.py            # Monte Carlo simulations
├── advanced_features.py      # Enhanced trading (1,216 lines)
└── analyzers/
    ├── technical_analyzer.py # Technical indicators
    └── sentiment_analyzer.py # Sentiment analysis
```

---

### 2.5 Risk Management System (RMS)

```
risk_management/
├── limits_engine.py      # 533 lines - Pre-trade validation
├── position_monitor.py   # Real-time position monitoring
├── circuit_breaker.py    # Emergency trading halt
├── alert_dispatcher.py   # 607 lines - Multi-channel alerts
├── risk_dashboard.py     # Risk visualization
├── risk_models.py        # Data models
├── risk_config.py        # Configuration
└── memory_risk_adapter.py # Non-Markovian integration
```

**LimitsEngine Features:**
- Singleton pattern
- Per-operation, daily, drawdown limits
- Memory-enhanced adjustment (via Non-Markovian Kernel)
- Warning/critical thresholds

---

### 2.6 Coherence Engine (6-Tier Veto System)

**Purpose:** Validates strategy agreement before trade execution.

**Thresholds:**
- Quality threshold: 30%
- Win rate threshold: 45%
- Target win rate: >55%

**Veto Tiers:**
1. Signal strength validation
2. Strategy consensus check
3. Risk limit verification
4. Regime alignment
5. Memory coherence score
6. Final execution approval

---

### 2.7 Adaptive Parameter Engine

**Purpose:** Auto-calibration of ARES strategies based on market regime.

**Regime Types:**
- TRENDING_UP
- TRENDING_DOWN
- RANGING
- HIGH_VOLATILITY
- LOW_VOLATILITY

**Key Methods:**
- `detect_regime()` - Market regime classification
- `calibrate_parameters()` - Dynamic parameter adjustment
- `get_optimal_settings()` - Regime-specific configurations

---

### 2.8 Web Search Service Premium+ V6.5.4

**Purpose:** Real-time internet search for AI responses with intelligent intent detection.

**Architecture:**
```
web_search_service/
├── tavily_search.py    # ~200 lines - Tavily API client
└── search_manager.py   # ~400 lines - Intent detection + caching
```

**Key Classes:**
- `TavilySearchClient` - Tavily API integration (search, Q&A, context)
- `WebSearchManager` - Caching, rate limiting, intent detection

**Premium+ V6.5.4 Features:**

| Feature | Description |
|---------|-------------|
| **Dual-Trigger Detection** | Requires BOTH intent + topic keywords to trigger search |
| **Redis Caching** | 15-minute TTL, reduces API calls |
| **Rate Limiting** | 30 searches/minute safeguard |
| **Visual Indicator** | "🔍 Información verificada" banner in AI responses |

**Intent Keywords (37 triggers):**
- Time-sensitive: "hoy", "ayer", "noticias", "qué pasó", "últimas"
- Summary: "resumen", "reporte", "análisis", "cierre", "apertura"
- Performance: "rendimiento", "comportamiento", "returns"
- Days of week: "lunes" through "domingo" (Spanish + English)
- Temporal: "semana pasada", "mes pasado", "esta mañana", "anoche"

**Topic Keywords (70+ triggers):**
- **Crypto**: bitcoin, ethereum, solana, xrp, dogecoin, altcoins, memecoin
- **Exchanges**: binance, coinbase, kraken, bybit, okx, kucoin
- **Stock Market**: bolsa, wall street, stock market, acciones, equities
- **US Indices**: nasdaq, nyse, s&p 500, dow jones, russell
- **ETFs**: spy, qqq, dia, iwm, vti, voo, arkk
- **Companies**: apple, microsoft, google, amazon, tesla, nvidia, meta
- **Macro**: fed, cpi, ppi, gdp, unemployment, payrolls
- **Conditions**: bull, bear, volatility, vix, fear, greed

**Integration Points:**
1. `ai_service.py` → Calls `get_search_manager().get_context_for_ai()`
2. `enterprise_bot.py` → Displays "🔍 Información verificada" banner
3. `redis_cache.py` → Caches search results

**Example Queries that Trigger Search:**
- "dame un resumen de la bolsa del viernes" ✅
- "qué pasó con bitcoin hoy" ✅
- "noticias de nvidia esta semana" ✅
- "cómo cerró el s&p 500 ayer" ✅

---

## 3. omnix_dashboard/ - Web Interface

**Framework:** Flask 3.x with Blueprints  
**Production:** Gunicorn + gevent  
**Total Lines:** 9,037

### 3.1 Architecture

```
omnix_dashboard/
├── app.py                 # Application factory (92 lines)
├── gunicorn.conf.py       # Production config
├── blueprints/
│   ├── views.py           # HTML routes (/, /terminal, /classic)
│   ├── core.py            # /api/metrics, /api/trades (~470 lines)
│   ├── market.py          # /api/ticker, /api/fear-greed (390 lines)
│   ├── intelligence.py    # /api/adaptive, /api/riskguardian (304 lines)
│   ├── system.py          # /api/debug, /api/db-diagnostics (491 lines)
│   └── snapshots.py       # /api/snapshots (630 lines)
├── utils/
│   ├── database.py        # Connection pooling (317 lines)
│   ├── queries.py         # SQL queries (297 lines)
│   ├── decorators.py      # @require_api_key (46 lines)
│   └── external_apis.py   # HTTP helpers (69 lines)
├── static/
│   ├── css/               # 19 CSS files
│   └── js/
│       ├── core/          # api.js, clock.js, utils.js
│       ├── components/    # 12 UI components
│       └── pages/         # dashboard.js, terminal.js
└── templates/
    ├── base.html
    ├── dashboard.html     # Classic dashboard (359 lines)
    └── terminal.html      # Bloomberg-style terminal (198 lines)
```

### 3.2 API Endpoints (26+)

| Blueprint | Endpoint | Purpose |
|-----------|----------|---------|
| core | `/api/metrics` | Trading performance |
| core | `/api/trades` | Recent trades |
| core | `/api/trades/history` | Detailed P&L history |
| core | `/api/positions` | Open positions |
| core | `/api/health` | System health |
| core | `/api/equity-curve` | Balance over time |
| market | `/api/ticker` | Real-time prices |
| market | `/api/fear-greed` | Market sentiment |
| market | `/api/news` | Market news |
| intelligence | `/api/adaptive` | Adaptive engine status |
| intelligence | `/api/riskguardian` | Risk guardian status |
| intelligence | `/api/signals` | Active signals |
| system | `/api/debug` | Debug info |
| system | `/api/db-diagnostics` | Pool health |
| snapshots | `/api/snapshots` | Portfolio snapshots |

---

## 4. omnix_risk/ - Risk Extensions

```
omnix_risk/
├── usd_risk_calculator.py   # USD-denominated risk
├── cascade_protection.py    # Cascade failure protection
├── reactivation_engine.py   # Auto-reactivation
├── portfolio_summary.py     # Portfolio overview
├── audit_logger.py          # Institutional audit trail
└── dead_man_switch.py       # Health monitoring
```

---

## 5. omnix_config/ - Configuration

```
omnix_config/
├── env_manager.py           # 580 lines - Environment variables
├── settings.py              # 140 lines - Centralized settings
└── grafana/                 # Grafana dashboard config
```

**Environment Precedence:** Replit Secrets > .env.local > defaults

---

## 6. omnix_testing/ - Backtesting & Validation

```
omnix_testing/
├── backtesting/
│   ├── engine.py            # BacktestingEngine
│   ├── data_downloader.py   # KrakenDataDownloader
│   └── metrics.py           # MetricsCalculator
├── validation/
│   ├── professional_validator.py  # Walk-forward + Monte Carlo
│   └── stress_suite.py            # Institutional stress tests
└── reporting/
    ├── chart_generator.py   # Equity curves, drawdowns
    └── pdf_generator.py     # Investor reports
```

---

## 7. External API Integrations

### 7.1 Trading Exchanges

| Service | Module | Purpose |
|---------|--------|---------|
| **Kraken** | `trading_service/kraken_client.py` | Crypto trading + data |
| **Alpaca** | `stock_trading/alpaca_service.py` | Stock trading + data |

### 7.2 AI Providers

| Service | Module | Purpose |
|---------|--------|---------|
| **Gemini 2.0 Flash** | `ai_service/brain.py` | Primary AI model |
| **OpenAI GPT-4o** | `ai_service/openai_client.py` | AI fallback |
| **Claude (Anthropic)** | `ai_service/claude_client.py` | AI fallback |
| **Whisper** | `voice_service/` | Voice transcription |

### 7.3 Market Data

| Service | Module | Purpose |
|---------|--------|---------|
| **CoinGecko** | `market_data/coingecko.py` | Backup crypto prices |
| **Alternative.me** | `market_intelligence/fear_greed.py` | Fear & Greed Index |
| **Finnhub** | `market_intelligence/finnhub.py` | News, sentiment |
| **Alpha Vantage** | `market_intelligence/alpha_vantage.py` | Technical indicators |

### 7.4 Blockchain Analytics

| Service | Module | Purpose |
|---------|--------|---------|
| **Glassnode** | `on_chain_service/` | On-chain metrics |
| **Whale Alert** | `on_chain_service/whale_tracker.py` | Whale movements |
| **Exchange Flows** | `on_chain_service/exchange_flow.py` | Exchange in/outflows |

### 7.5 Quantum Computing

| Service | Module | Purpose |
|---------|--------|---------|
| **ANU QRNG** | `quantum/enhancements.py` | Quantum random numbers |
| **D-Wave Leap** | `quantum/dwave_qaoa.py` | Quantum annealing |

---

## 8. Database Schema Summary

**Total Tables:** 42  
**Foreign Keys:** 38 (90% coverage)

### 8.1 Core Tables

| Table | Purpose |
|-------|---------|
| `users` | User accounts |
| `paper_trading_trades` | Trade history |
| `paper_trading_balances` | Balance tracking |
| `paper_trading_positions` | Open positions |
| `balance_history` | Balance changes |
| `conversations` | AI chat history |
| `pending_evaluations` | Scheduled evaluations |
| `ai_auto_learning_entries` | Learning data |

### 8.2 Advanced Tables

| Table | Purpose |
|-------|---------|
| `derivatives_positions` | Futures positions |
| `margin_accounts` | Margin balances |
| `risk_events` | Risk incidents |
| `adaptive_engine_state` | Calibration data |
| `community_signals` | Crowdsourced signals |
| `on_chain_metrics` | Blockchain data |

---

## 9. Additional Packages

### 9.1 omnix/ - Hexagonal Architecture (V7.0 Foundation)

```
omnix/
├── ports/
│   ├── driven/              # Output ports (infrastructure)
│   │   ├── ai_inference_port.py
│   │   ├── cache_port.py
│   │   ├── database_port.py
│   │   ├── market_data_port.py
│   │   ├── notification_port.py
│   │   └── trading_port.py
│   ├── driver/              # Input ports (application)
│   │   ├── rest_api_port.py
│   │   └── telegram_port.py
│   └── verify_ports.py      # Port verification utility
```

**Status:** Phase 1 COMPLETED (Dec 9, 2025) - 12 Protocol interfaces defined.

### 9.2 omnix_risk/ - Risk Management Utilities

```
omnix_risk/
├── audit_logger.py          # Institutional audit logging
├── cascade_protection.py    # Cascade failure protection
├── dead_man_switch.py       # Dead man switch protocol
├── portfolio_summary.py     # Portfolio analytics
├── reactivation_engine.py   # System reactivation logic
└── usd_risk_calculator.py   # USD risk calculations
```

### 9.3 omnix_strategies/ - Strategy Modules

```
omnix_strategies/
└── regime_switcher.py       # Market regime strategy switching
```

### 9.4 omnix_api/ - API Layer

```
omnix_api/
├── payments/
│   └── stripe_integration.py  # Stripe payment processing
└── routes/                    # API route definitions
```

---

## 10. Trading Profiles (V6.5.4c)

| Profile | Use Case | ARES Status | Drawdown Limit |
|---------|----------|-------------|----------------|
| **PRODUCTION_STABLE** | Track record building | V1+V2 ACTIVE (experimental) | 15% |
| **INSTITUTIONAL** | Conservative, real money | DISABLED | 10% |
| **PAPER_AGGRESSIVE** | Aggressive testing | ENABLED | 15% |
| **BALANCED** | Mixed mode | DISABLED | 10% |

**V6.5.4c Changes:**
- ARES V1 (Swing): 70% min confidence, active
- ARES V2 (Scalping): 75% min confidence, active
- Max 3 trades/day (shared between V1/V2)
- Lateral markets allowed (require_trend=False)

---

## 11. INSTITUTIONAL+ Specific Features

### 10.1 BUY Bias Escalonado (Paper Mode)

| Market Sentiment | Base Boost | Accelerator Boost |
|------------------|------------|-------------------|
| FLOOR_RESCUE | +30% | +20% |
| RECOVERY | +20% | +15% |
| NEUTRAL | +10% | +10% |
| MOMENTUM | +5% | +5% |

### 10.2 Track Record Accelerator

- 1.3x multiplier for first 50 trades in paper mode
- Normalizes to 1.0x after 50 trades
- Accelerates track record building for investor presentations

### 10.3 Fear & Greed Contrarian Strategy

- Applies in both paper and real modes
- Contrarian boost on extreme fear
- Position adjustment based on sentiment extremes

---

## Document Changelog

| Date | Version | Changes |
|------|---------|---------|
| Dec 6, 2025 | 1.0 | Initial complete module catalog for INSTITUTIONAL+ |
| Dec 8, 2025 | 1.1 | Added AI Service DI architecture |
| Dec 10, 2025 | 1.2 | **V6.5.4c Sync**: Removed pqc_encryption.py (never existed), added omnix/, omnix_risk/, omnix_strategies/, omnix_api/, updated trading profiles with ARES activation and 15% drawdown |
