# OMNIX V6.5.4e - Mapa Completo de Funcionalidades

**Fecha**: 14 de Enero 2026  
**Propósito**: Documento de referencia para reescritura limpia V7.0  
**Estado**: CONSOLIDADO  
**Último Cambio**: ADR-007 Coherence Threshold Calibration

---

## Cambios Recientes (Dec 19, 2025)

### AI-First Multilingual Concurrency - IMPLEMENTADO
| Componente | Archivo | Función |
|------------|---------|---------|
| LanguageContextManager | `omnix_services/ai_service/prompt_templates.py` | Detección de idioma con lock + Redis |
| Fallback Messages | `ai_service.py`, `conversational_ai_adapter.py`, `ai_error_handler.py` | Placeholders EN universales |
| Redis Language Cache | `omnix:user_language:{chat_id}` | 24h TTL por usuario |

---

## 1. DOMINIO: Trading Signal Fabric

### 1.1 Estrategias de Señales (10 Core)

| Estrategia | Ubicación | Función | APIs Externas |
|------------|-----------|---------|---------------|
| QuantumMomentum | `omnix_services/trading_service/quantum_momentum.py` | 6-componentes: EMA/RSI/MACD/Volume/HP/ATR | Ninguna |
| Monte Carlo | `omnix_services/trading_service/monte_carlo.py` | 10,000 simulaciones con QRNG opcional | ANU QRNG API |
| Kelly Criterion | `omnix_services/trading_service/kelly_criterion.py` | Position sizing óptimo | Ninguna |
| Black Swan | `omnix_services/trading_service/black_swan.py` | Detección de riesgo extremo (VETO) | Ninguna |
| HMM Regime | `omnix_services/trading_service/hmm_regime.py` | TRENDING/RANGING/VOLATILE | Ninguna |
| Kalman Filter | `omnix_services/trading_service/kalman_filter.py` | Reducción de ruido en señales | Ninguna |
| Sentiment Analysis | `omnix_services/market_intelligence/` | Fear & Greed + noticias | Alternative.me, Finnhub |
| Non-Markovian Kernel | `omnix_core/strategies/non_markovian_kernel.py` | Memoria temporal con decay | Redis |
| Coherence Engine | `omnix_services/coherence_service/coherence_engine.py` | 6-tier veto system | Ninguna |
| Risk Guardian | `omnix_services/monitoring/risk_guardian.py` | Protección overtrading/drawdown | Ninguna |

### 1.2 Sistema de Coherencia (6 Tiers)

```
Tier 1: Contradiction check (5+ votos vs 3+)
Tier 2: Black Swan risk level
Tier 3: Coherence score threshold (55%+)
Tier 4: Confidence threshold (60%+)
Tier 5: Monte Carlo win rate (50%+)
Tier 6: Position limit check
```

### 1.3 Módulos de Soporte

| Módulo | Ubicación | Función |
|--------|-----------|---------|
| CAES V6.5.4 | `omnix_core/strategies/caes_module.py` | Position sizing dinámico (0.5x-3x) |
| Adaptive Engine | `omnix_services/adaptive_engine/adaptive_engine.py` | Auto-calibración por régimen |
| Optimization | `omnix_services/optimization/` | ML-based weight optimization |

---

## 2. DOMINIO: Market & Data Ingestion

### 2.1 APIs Externas Consumidas

| API | Servicio | Datos | Rate Limit |
|-----|----------|-------|------------|
| Kraken REST | market_data | OHLCV, ticker, orderbook | 15 req/min |
| Kraken WebSocket | market_data | Real-time prices, trades | Streaming |
| AlphaVantage | market_intelligence | RSI, MACD, technical indicators | 5 req/min |
| Finnhub | market_intelligence | News, sentiment, fundamentals | 60 req/min |
| Alternative.me | market_intelligence | Fear & Greed Index | 30 req/hour |
| Tavily | web_search_service | Real-time web search | Per API key |
| ANU QRNG | quantum/enhancements.py | Quantum random numbers | 1024/request |
| CoinGecko | market_data | Backup crypto prices | Standard |

### 2.2 Módulos de Datos

| Módulo | Ubicación | Función |
|--------|-----------|---------|
| MarketData | `omnix_services/market_data/` | Precios, orderbook, arbitrage scanner |
| MarketIntelligence | `omnix_services/market_intelligence/` | Fear/Greed, noticias, indicadores |
| WebSearchService | `omnix_services/web_search_service/` | Tavily integration |
| NewsScraper | `omnix_services/news_scraper.py` | Scraping de noticias |
| SymbolClassifier | `omnix_services/symbol_classifier.py` | Clasificación crypto/stock |

### 2.3 Sistema de Arbitraje (Premium)

| Componente | Ubicación |
|------------|-----------|
| Scanner | `omnix_services/market_data/intelligence/arbitrage_scanner.py` |
| Executor | `omnix_services/market_data/intelligence/arbitrage_executor.py` |
| Exchanges | 8: Kraken, Binance, Coinbase, Bybit, KuCoin, OKX, Gate.io, Bitfinex |

---

## 3. DOMINIO: Execution & Brokerage

### 3.1 Exchanges Soportados

| Exchange | Tipo | Estado | Cliente |
|----------|------|--------|---------|
| Kraken Spot | Crypto | CORE - Producción | `kraken_client.py` |
| Kraken Futures | Crypto Derivatives | STRATEGIC | `derivatives/` |
| Alpaca | Stocks (NYSE/NASDAQ) | SUPPORT | `stock_trading/` |

### 3.2 Módulos de Ejecución

| Módulo | Ubicación | Función |
|--------|-----------|---------|
| ExecutionService | `omnix_services/execution_service/` | Protocolo 4-capas institucional |
| TradingSystem | `omnix_core/trading_system.py` | Orquestador de ejecución |
| KrakenClient | `omnix_services/trading_service/kraken_client.py` | Cliente API Kraken |
| PaperTradingManager | `omnix_services/trading_service/paper_trading_manager.py` | Simulación paper trading |
| PositionManager | `omnix_services/trading_service/position_manager.py` | Gestión de posiciones |
| Derivatives | `omnix_services/derivatives/` | Futuros, margin, hedging |
| StockTrading | `omnix_services/stock_trading/` | Alpaca integration |

### 3.3 Protocolo de Ejecución 4 Capas

```
Capa 1: Análisis de liquidez
Capa 2: Correlación
Capa 3: Micro-volatilidad
Capa 4: Ejecución (TWAP/VWAP/ICEBERG)
```

---

## 4. DOMINIO: Risk & Protection

### 4.1 Capas de Protección

```
┌─────────────────────────────────────────────────────────────┐
│  Capa 1: Emergency SL (2% max loss per position)           │
│  Capa 2: Risk Guardian (daily loss limit 15%, overtrading) │
│  Capa 3: Circuit Breaker (halt on extreme events)          │
│  Capa 4: Cascade Protection (portfolio-level stops)        │
│  Capa 5: Dead Man Switch (inactivity protection)           │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Módulos de Riesgo

| Módulo | Ubicación | Función |
|--------|-----------|---------|
| RiskManagement | `omnix_services/risk_management/` | Circuit breaker, límites |
| Monitoring | `omnix_services/monitoring/` | Risk Guardian V5.4, metrics |
| MemoryRiskAdapter | `omnix_services/risk_management/memory_risk_adapter.py` | Kernel → risk adapter |
| RollbackProtocol | `omnix_core/risk/rollback_protocol.py` | ARP (Algorithmic Rollback) |

### 4.3 Circuit Breakers

| Trigger | Action |
|---------|--------|
| 5% daily loss | Reduce sizes 50% |
| 8% daily loss | Halt all trades |
| 3 consecutive losses | 30-min cooldown |
| Regime change | 15-min pause |

### 4.4 Stop Loss / Take Profit por Volatilidad

| Pair Type | SL | TP | R:R |
|-----------|----|----|-----|
| High Volatility (DOT, AVAX, SOL, LINK) | 2.5% | 4.5% | 1:1.8 |
| Normal Volatility (BTC, ETH, XRP, LTC) | 1.5% | 3.0% | 1:2.0 |

---

## 5. DOMINIO: AI & Communication

### 5.1 Proveedores AI

| Proveedor | Modelo | Rol | Rate Limit |
|-----------|--------|-----|------------|
| Google Gemini | 2.0 Flash | Primario | 60 RPM |
| OpenAI | GPT-4o | Backup | Per API key |
| Anthropic | Claude | Fallback | Per API key |
| OpenAI | Whisper | STT/TTS | Per API key |

### 5.2 Módulos de AI

| Módulo | Ubicación | Función |
|--------|-----------|---------|
| AIService | `omnix_services/ai_service/` | Orquestador con DI container (SOLID) |
| Providers | `omnix_services/ai_service/providers/` | Gemini, OpenAI, Anthropic |
| RoutingAIGateway | `omnix_services/ai_service/providers/routing_gateway.py` | Multi-provider routing |
| VideoAnalyzer | `omnix_services/ai_service/video/` | Análisis de video |
| VoiceService | `omnix_services/voice_service/` | STT (Whisper) + TTS |
| QuantumPhysicsValidator | `omnix_core/quantum/physics_validator.py` | Validación científica |

### 5.3 Web Search

| Componente | Ubicación |
|------------|-----------|
| IntentDetector | `omnix_services/web_search_service/intent_detector.py` |
| SearchManager | `omnix_services/web_search_service/search_manager.py` |
| TavilySearch | `omnix_services/web_search_service/tavily_search.py` |

---

## 6. DOMINIO: User Interfaces

### 6.1 Telegram Bot

| Archivo | Líneas | Función |
|---------|--------|---------|
| enterprise_bot.py | ~7,900 | Bot principal |
| inline_keyboards.py | - | Botones interactivos |
| callback_handler.py | - | Manejo de callbacks |
| portfolio_commands.py | - | Comandos de portfolio |

#### Comandos por Categoría (40+)

| Categoría | Comandos |
|-----------|----------|
| Market Data | `/precio`, `/market`, `/balance`, `/orderbook` |
| Paper Trading | `/paper_start`, `/paper_buy`, `/paper_sell`, `/paper_close` |
| Stock Trading | `/balance_bolsa`, `/analizar`, `/comprar_bolsa`, `/vender_bolsa` |
| Auto-Trading | `/auto_start`, `/auto_stop`, `/auto_status` |
| Analysis | `/montecarlo`, `/blackswan`, `/sentiment`, `/fibonacci` |
| Web Search | `/buscar` |
| Config | `/miconfig`, `/perfil`, `/limites`, `/proteccion` |
| Community | `/feedback`, `/community_stats`, `/top_strategies`, `/leaderboard` |
| Quantum | `/quantum_test`, `/quantum_stats`, `/optimize_portfolio` |

### 6.2 Flask Dashboard (Port 5000)

| Archivo | Función |
|---------|---------|
| app.py | Main Flask application |
| blueprints/core.py | Core routes |
| blueprints/market.py | Market data routes |
| blueprints/system.py | System health routes |
| blueprints/intelligence.py | AI/intelligence routes |
| api_client.py | OmnixAPIClient |

#### Dual Win Rate Framework (Jan 12, 2026)

El dashboard muestra dos métricas de win rate separadas:

| Métrica UI | Campo API | Descripción |
|------------|-----------|-------------|
| **Precisión** | `win_rate_directional` | % trades donde el precio se movió en la dirección predicha |
| **Rentable** | `win_rate_net` | % trades rentables después de fees de Kraken (~0.26%) |
| Fee Eroded | `fee_eroded_trades` | Trades que acertaron dirección pero perdieron a fees |

**Ubicación UI:**
- Terminal Header: Columnas "Precisión" y "Rentable" con tooltips en español
- Trade History Widget: Fila de estadísticas con ambos WR + contador fee-eroded
- Streamlit Overview: 5 columnas con tooltips explicativos

#### Endpoints Principales

| Endpoint | Función |
|----------|---------|
| `/api/metrics` | Trading performance data (incluye dual win rates) |
| `/api/sharpe` | Sharpe/Sortino/Calmar ratios |
| `/api/trades` | Recent trades |
| `/api/balance-history` | Balance history |
| `/api/report/pdf` | PDF report generation |
| `/api/health` | System health |
| `/api/db-diagnostics` | Database diagnostics |
| `/api/market/prices` | Real-time prices |
| `/api/calibration` | Calibration status |

### 6.3 Streamlit Dashboard (Port 8080)

| Widget | Data Source | Update |
|--------|-------------|--------|
| Balance Chart | `/api/balance-history` | 30s |
| Precisión | `/api/metrics` → `win_rate_directional` | 60s |
| Rentable | `/api/metrics` → `win_rate_net` | 60s |
| Fee Eroded Count | `/api/metrics` → `fee_eroded_trades` | 60s |
| Trade Table | `/api/trades` | 30s |
| P&L Chart | `/api/metrics` | 60s |
| Sharpe/Sortino | `/api/sharpe` | 60s |

---

## 7. DOMINIO: Persistence & Analytics

### 7.1 PostgreSQL (42 Tablas)

| Categoría | Tablas | FK Coverage |
|-----------|--------|-------------|
| Core User | 4 | 100% |
| Trading | 5 | 100% |
| Risk Management | 8 | 100% |
| Derivatives | 6 | 100% |
| Community | 5 | 100% |
| Snapshots/Analytics | 6 | 100% |
| System | 8 | N/A |

#### Tablas Clave

- `users` - Master user table
- `paper_trading_trades` - Paper trade records
- `paper_trading_balances` - User balances
- `risk_guardian_events` - Risk events log
- `decision_logs` - Institutional audit trail
- `community_feedback` - User feedback
- `strategy_votes` - Strategy voting
- `detected_patterns` - AI-detected patterns

### 7.2 Redis Cache

| Namespace | TTL | Purpose |
|-----------|-----|---------|
| `market:` | 60s | Price data |
| `user:` | 5min | User state |
| `conv:` | 1hr | Conversation history |
| `rate:` | 1min | Rate limiting |

### 7.3 Módulos de Persistencia

| Módulo | Ubicación |
|--------|-----------|
| DatabaseGateway | `omnix_services/database_service/database_gateway.py` |
| RedisCache | `omnix_core/cache/redis_cache.py` |
| Analytics | `omnix_services/analytics/` |

---

## 8. DOMINIO: Security & Quantum

### 8.1 Post-Quantum Cryptography

| Algorithm | Standard | Purpose | Status |
|-----------|----------|---------|--------|
| Kyber-768 | NIST FIPS-203 | Key encapsulation | Active |
| Dilithium-3 | NIST FIPS-204 | Digital signatures | Active |

### 8.2 Módulos de Seguridad

| Módulo | Ubicación |
|--------|-----------|
| PQCSecurity | `omnix_core/security/pqc_security.py` |
| QuantumEnhancements | `omnix_core/quantum/enhancements.py` |
| QRNG | `omnix_core/quantum/enhancements.py` (QuantumRandomNumberGenerator) |

### 8.3 QRNG (Quantum Random Number Generator)

- **Fuente**: ANU Quantum API
- **Método**: Fluctuaciones del vacío cuántico
- **Cache**: 1,024 números por batch, TTL 1 hora
- **Fallback**: numpy.random

---

## 9. DOMINIO: Portfolio Optimization

### 9.1 Modelos de Optimización

| Model | Description |
|-------|-------------|
| Markowitz Mean-Variance | Classic portfolio optimization |
| Black-Litterman | Incorporates user views |

### 9.2 CAES Position Sizing

| Factor | Effect |
|--------|--------|
| Base Size | Account Balance x Base % |
| Aggression Factor | Sigmoid of Kernel Confidence (0.5x - 3.0x) |
| Regime Multiplier | Market condition (0.5x - 1.3x) |
| ATR Validation | Hard caps on aggression |

### 9.3 Risk Profiles

| Profile | Max Per Trade | Daily Loss Limit |
|---------|---------------|------------------|
| Ultraconservador | 2% | 5% |
| Conservador | 5% | 10% |
| Moderado | 10% | 15% |
| Agresivo | 15% | 25% |
| Institucional | 8% | 12% |

---

## 10. DOMINIO: Community Intelligence

### 10.1 Módulos

| Módulo | Ubicación | Líneas |
|--------|-----------|--------|
| FeedbackManager | `omnix_services/community_intelligence/feedback_manager.py` | ~449 |
| CommunityAnalyzer | `omnix_services/community_intelligence/community_analyzer.py` | ~345 |
| RewardSystem | `omnix_services/community_intelligence/reward_system.py` | ~274 |
| CommunityDashboard | `omnix_services/community_intelligence/community_dashboard.py` | ~320 |
| SignalContribution | `omnix_services/community_intelligence/signal_contribution.py` | - |

### 10.2 Sistema de Recompensas

| Acción | Puntos |
|--------|--------|
| Feedback | +10 |
| Voto estrategia | +5 |
| Propuesta mejora | +25 |
| Feedback útil | +15 bonus |

### 10.3 Niveles

| Nivel | Puntos Mínimos |
|-------|----------------|
| Nuevo | 0 |
| Novato | 10 |
| Aprendiz | 50 |
| Intermedio | 100 |
| Avanzado | 300 |
| Experto | 500 |
| Maestro | 1000 |
| Leyenda | 2500 |

---

## 11. Trading Profiles System

### 11.1 Perfiles Disponibles

| Profile | Purpose | Aggressiveness |
|---------|---------|----------------|
| **PRODUCTION_STABLE** | Track record (ACTIVE) | Moderate |
| INSTITUTIONAL | Real money, max protection | Conservative |
| PAPER_AGGRESSIVE | Rapid testing | Aggressive |
| BALANCED | Middle ground | Moderate |
| PAPER_OPTIMIZED | Investor demos | Selective |
| WIN_RATE_OPTIMIZED | Maximum win rate | Very Selective |

### 11.2 PRODUCTION_STABLE V6.5.4d Parameters

| Parameter | Value |
|-----------|-------|
| min_trade_size | $100 |
| max_trade_size | $3,000 |
| base_trade_size | $500 |
| max_daily_trades | 10 |
| max_daily_loss_pct | 15% |
| coherence_threshold | 55% |
| min_signal_strength | 60% |
| emergency_sl_pct | 2.0% |
| score_moderate | 12 (=strong, MODERATE disabled) |

---

## 12. User Settings System

### 12.1 Módulos

| Módulo | Ubicación |
|--------|-----------|
| UserSettingsService | `omnix_services/user_settings/user_settings_service.py` |
| SettingsModels | `omnix_services/user_settings/settings_models.py` |

### 12.2 Configuraciones por Usuario

- Risk profile selection
- Trading limits
- Auto-protection settings
- Strategy enable/disable
- Allowed cryptocurrencies
- Auto-trading toggle

---

## 13. Notifications System

| Módulo | Ubicación | Función |
|--------|-----------|---------|
| Notifications | `omnix_services/notifications/` | Trade notifications, daily summary |
| TelegramUtils | `omnix_services/telegram_service/` | Send messages, alerts |

---

## 14. Estado de Migración Hexagonal

### 14.1 Ports Definidos

| Port | Status DI |
|------|-----------|
| TradingPort | ✅ Integrado |
| MarketDataPort | ✅ Integrado |
| AIInferencePort | ✅ Integrado |
| DatabasePort | ⬜ Diferido V7.0 |
| CachePort | ⬜ Diferido V7.0 |
| NotificationPort | ⬜ Diferido V7.0 |
| RestApiPort | ⬜ Diferido V7.0 |
| TelegramPort | ⬜ Diferido V7.0 |

### 14.2 Adapters Existentes

| Adapter | Implementa |
|---------|------------|
| KrakenAdapter | TradingPort, MarketDataPort |
| GeminiAdapter | AIInferencePort |
| TelegramAdapter | NotificationPort |

---

## 15. Deuda Técnica Conocida

| Issue | Priority |
|-------|----------|
| ~80 bare except clauses | MEDIUM |
| ~55 silenced exceptions | HIGH |
| main.py monolítico | HIGH |
| enterprise_bot.py (7,812 líneas) | MEDIUM |
| Test coverage <1% | CRITICAL (post-500 trades) |
| Cross-package coupling | HIGH |

---

## 16. APIs Externas (Resumen Completo)

| API | Uso Principal | Módulo |
|-----|---------------|--------|
| Kraken REST/WebSocket | Crypto trading | kraken_client |
| Alpaca | Stock trading | stock_trading |
| Google Gemini 2.0 Flash | AI primario | ai_service |
| OpenAI GPT-4o + Whisper | AI backup + Voice | ai_service, voice_service |
| Anthropic Claude | AI fallback | ai_service |
| AlphaVantage | Technical indicators | market_intelligence |
| Finnhub | News, sentiment | market_intelligence |
| Alternative.me | Fear & Greed | market_intelligence |
| Tavily | Web search | web_search_service |
| ANU QRNG | Quantum random | quantum/enhancements |
| CoinGecko | Backup prices | market_data |

---

## 17. Estructura de Archivos Clave

```
OMNIX/
├── src/omnix/           <- Hexagonal V7.0 (ports, domain, adapters)
│   ├── ports/
│   │   ├── driven/      <- Output ports
│   │   └── driver/      <- Input ports
│   ├── infrastructure/
│   │   └── adapters/    <- Implementations
│   └── bootstrap/       <- DI container
├── omnix_core/          <- Core runtime
│   ├── bot/             <- AutoTradingBot
│   ├── strategies/      <- CAES, Non-Markovian
│   ├── cache/           <- Redis cache
│   ├── config/          <- Trading profiles
│   ├── quantum/         <- QRNG, physics
│   ├── security/        <- PQC
│   └── trading_system.py
├── omnix_services/      <- Services layer (24 subpackages)
│   ├── ai_service/      <- SOLID AI with DI
│   ├── trading_service/ <- Strategies
│   ├── telegram_service/ <- Bot
│   ├── database_service/ <- PostgreSQL gateway
│   └── ...
├── omnix_dashboard/     <- Flask + Streamlit
├── omnix_api/           <- Stripe integration (B2C)
├── omnix_config/        <- Central settings
├── tests/               <- Test suite
├── tools/               <- Utilities
└── docs/                <- Documentation
```

---

## 10. INVENTARIO DE COMANDOS TELEGRAM (Dic 24, 2025)

### 10.1 Resumen de Superficie de Comandos

| Categoría | Cantidad | Estado |
|-----------|----------|--------|
| Comandos Registrados | 85 | ✅ |
| Handlers Únicos | 81 | ✅ |
| Alias (apuntan a otro handler) | 4 | ✅ |
| Comandos Comentados (TODO) | 2 | ❌ No expuestos |

### 10.2 Comandos READ-ONLY (Información)

| Comando | Handler | Backend | Protección |
|---------|---------|---------|------------|
| `/start` | `start_command` | Static + InlineKeyboards | N/A |
| `/version` | `version_command` | VERSION_BANNER | N/A |
| `/precio` | `precio_command` | Kraken API | N/A |
| `/market` | `market_command` | market_data | N/A |
| `/help`, `/ayuda` | `help_command` | Static | N/A |
| `/balance` | `balance_command` | Kraken/Paper | N/A |
| `/status` | `status_command` | System status | N/A |
| `/analisis` | `analisis_command` | TradingService | N/A |
| `/montecarlo`, `/quantum` | `montecarlo_command` | Monte Carlo 10K | N/A |
| `/quantum_test` | `quantum_test_command` | QRNG ANU | N/A |
| `/quantum_stats` | `quantum_stats_command` | QRNG stats | N/A |
| `/quantum_demo` | `quantum_demo_command` | physics_validator | N/A |
| `/blackswan` | `blackswan_command` | BlackSwanDetector | N/A |
| `/sentiment` | `sentiment_command` | Fear&Greed API | N/A |
| `/sharia` | `sharia_command` | Sharia validator | N/A |
| `/orderbook` | `orderbook_command` | Kraken orderbook | N/A |
| `/rms` | `rms_dashboard_command` | LimitsEngine | N/A |
| `/rms_limits` | `rms_limits_command` | LimitsEngine | N/A |
| `/arbitrage_scan` | `arbitrage_scan_command` | ArbitrageScanner | N/A |
| `/trading` | `trading_menu_command` | Static menu | N/A |
| `/arbitraje` | `arbitraje_command` | Alias arbitrage | N/A |

### 10.3 Comandos con SIDE EFFECTS (Trading)

| Comando | Handler | Backend | RMS Protected |
|---------|---------|---------|---------------|
| `/paper_buy` | `paper_buy_command` | PaperTradingManager | ✅ circuit_breaker + limits_engine |
| `/paper_sell` | `paper_sell_command` | PaperTradingManager | ✅ circuit_breaker + limits_engine |
| `/arbitrage_execute` | `arbitrage_execute_command` | ArbitrageExecutor | ✅ circuit_breaker + limits_engine (Dec 24) |
| `/comprar_bolsa` | `buy_stock_command` | StockHandler | ✅ Condicional |
| `/vender_bolsa` | `sell_stock_command` | StockHandler | ✅ Condicional |
| `/emergency_halt` | `rms_emergency_halt_command` | CircuitBreaker | ✅ Admin only |
| `/resume_trading` | `rms_resume_trading_command` | CircuitBreaker | ✅ Admin only |
| `/autotrading` | `autotrading_command` | UserSettingsService | ✅ Owner only |

### 10.4 Comandos CONDICIONALES (requieren módulo activo)

Estos comandos solo se registran si su módulo está disponible:

| Condición | Comandos |
|-----------|----------|
| `if self.stock_handler` | `/balance_bolsa`, `/mercado`, `/stock_status`, `/risk_dashboard`, `/comprar_bolsa`, `/vender_bolsa` |
| `if self.arbitrage_scanner` | `/arbitrage`, `/arbitrage_scan`, `/arbitrage_execute`, `/arbitrage_stats` |
| `if self.feedback_manager` | `/feedback`, `/community_stats`, `/top_strategies`, `/my_contributions`, `/vote_strategy`, `/leaderboard` |
| `if self.signal_contribution` | `/share_signal`, `/community_signals`, `/my_signals`, `/alpha_leaderboard`, `/execute_signal` |
| `if self.limits_engine` | `/rms`, `/rms_limits`, `/rms_set`, `/rms_history`, `/emergency_halt`, `/resume_trading` |
| `if self.user_settings_service` | `/miconfig`, `/perfil`, `/limites`, `/proteccion`, `/estrategias`, `/cryptos`, `/autotrading`, `/pausar`, `/reanudar`, `/onboarding` |

### 10.5 Lenguaje Institucional

**Archivos de Enforcement:**
- `omnix_services/ai_service/prompt_templates.py` → MASTER_SYSTEM_PROMPT
- `omnix_services/ai_service/ai_prompts.py` → Intent detector

**Blacklisted Phrases (21 EN/ES):**
- pérdida/loss, drawdown, failure, problema, error crítico
- warning sign, urgent, disclaimer, no garantiza
- podrías perder todo, rendimiento subóptimo

**Comandos Estáticos Revisados (Dic 24, 2025):**
- `/start` → Lenguaje institucional aplicado
- `/legal`, `/educacion` → Contenido legal obligatorio (sin modificar)

---

*Documento generado: 15 de Diciembre 2025*
*Última actualización: 24 de Diciembre 2025 - Sellado de comandos*
*Propósito: Base para reescritura limpia V7.0*
