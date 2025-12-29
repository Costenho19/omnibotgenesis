# OMNIX V7.0 - Matriz de Trazabilidad Funcionalidad → Migración

**Fecha**: 15 de Diciembre 2025  
**Propósito**: Garantizar 100% cobertura de funcionalidades durante reescritura  
**Estado**: DOCUMENTO DE REFERENCIA

---

## Leyenda

| Símbolo | Significado |
|---------|-------------|
| **CORE** | Crítico para funcionamiento - Sin esto el sistema no opera |
| **SUPPORT** | Importante pero no bloqueante |
| **STRATEGIC** | Valor futuro, puede diferirse |
| ✅ | Cubierto en plan de migración |
| ⚠️ | Requiere atención especial |
| ❌ | No cubierto - acción requerida |

---

## DOMINIO 1: Trading Signal Fabric

### Fase de Migración: **FASE 4** (Semanas 5-6)

| # | Componente | Ubicación Legacy | Ubicación V7.0 | Dependencias | Validación | Prioridad |
|---|------------|------------------|----------------|--------------|------------|-----------|
| 1.1 | QuantumMomentum | `omnix_services/trading_service/quantum_momentum.py` | `src/omnix/domain/strategies/quantum_momentum.py` | MarketData (F2) | Shadow signals <1% divergencia | ✅ CORE |
| 1.2 | Monte Carlo | `omnix_services/trading_service/monte_carlo.py` | `src/omnix/domain/strategies/monte_carlo.py` | QRNG (F1), MarketData (F2) | Comparación distribuciones | ✅ CORE |
| 1.3 | Kelly Criterion | `omnix_services/trading_service/kelly_criterion.py` | `src/omnix/domain/strategies/kelly.py` | RiskService (F3) | Unit tests matemáticos | ✅ CORE |
| 1.4 | Black Swan | `omnix_services/trading_service/black_swan.py` | `src/omnix/domain/strategies/black_swan.py` | MarketData (F2) | Chaos testing, replay histórico | ✅ CORE |
| 1.5 | HMM Regime | `omnix_services/trading_service/hmm_regime.py` | `src/omnix/domain/strategies/hmm_regime.py` | MarketData (F2) | Comparación estados detectados | ✅ CORE |
| 1.6 | Kalman Filter | `omnix_services/trading_service/kalman_filter.py` | `src/omnix/domain/strategies/kalman.py` | MarketData (F2) | Unit tests señales filtradas | ✅ CORE |
| 1.7 | Sentiment Analysis | `omnix_services/market_intelligence/` | `src/omnix/domain/strategies/sentiment.py` | ExternalData (F2) | API mocking + replay | ✅ CORE |
| 1.8 | Non-Markovian Kernel | `omnix_core/strategies/non_markovian_kernel.py` | `src/omnix/domain/strategies/non_markovian.py` | CacheAdapter (F2) | Memory decay validation | ✅ CORE |
| 1.9 | CoherenceEngine | `omnix_services/coherence_service/coherence_engine.py` | `src/omnix/domain/coherence/engine.py` | Todas las estrategias | 6-tier veto testing | ✅ CORE |
| 1.10 | Risk Guardian | `omnix_services/monitoring/risk_guardian.py` | `src/omnix/domain/risk/guardian.py` | RiskService (F3) | Historical replay | ✅ CORE |
| 1.11 | CAES Module | `omnix_core/strategies/caes_module.py` | `src/omnix/domain/sizing/caes.py` | CoherenceEngine | Position sizing tests | ✅ CORE |
| 1.12 | ~~ARES V1 (Swing)~~ | ~~`omnix_core/strategies/ares_v1.py`~~ | ~~`src/omnix/domain/strategies/ares/v1.py`~~ | - | **REMOVED Dec 24, 2025** | ❌ REMOVED |
| 1.13 | ~~ARES V2 (Scalping)~~ | ~~`omnix_core/strategies/ares_v2.py`~~ | ~~`src/omnix/domain/strategies/ares/v2.py`~~ | - | **REMOVED Dec 24, 2025** | ❌ REMOVED |
| 1.14 | Adaptive Engine | `omnix_services/adaptive_engine/adaptive_engine.py` | `src/omnix/domain/adaptive/engine.py` | HMM Regime | Regime switch tests | ✅ SUPPORT |
| 1.15 | Optimization ML | `omnix_services/optimization/` | `src/omnix/domain/optimization/` | Analytics (F3) | Backtest comparison | ✅ SUPPORT |

**Cobertura Dominio 1**: 13/13 componentes ✅ (ARES V1/V2 removed Dec 24, 2025)

---

## DOMINIO 2: Market & Data Ingestion

### Fase de Migración: **FASE 2** (Semanas 2-3)

| # | Componente | Ubicación Legacy | Ubicación V7.0 | APIs Externas | Validación | Prioridad |
|---|------------|------------------|----------------|---------------|------------|-----------|
| 2.1 | MarketDataPort | `omnix_services/market_data/` | `src/omnix/ports/driven/market_data.py` | - | Interface contract tests | ✅ CORE |
| 2.2 | KrakenAdapter REST | `omnix_services/trading_service/kraken_client.py` | `src/omnix/infrastructure/adapters/kraken/rest.py` | Kraken REST | API response mocking | ✅ CORE |
| 2.3 | KrakenAdapter WS | `omnix_services/trading_service/kraken_client.py` | `src/omnix/infrastructure/adapters/kraken/websocket.py` | Kraken WS | Streaming tests | ✅ CORE |
| 2.4 | AlphaVantageAdapter | `omnix_services/market_intelligence/` | `src/omnix/infrastructure/adapters/alphavantage/` | AlphaVantage | Rate limit testing | ✅ SUPPORT |
| 2.5 | FinnhubAdapter | `omnix_services/market_intelligence/` | `src/omnix/infrastructure/adapters/finnhub/` | Finnhub | News parsing tests | ✅ SUPPORT |
| 2.6 | AlternativeMeAdapter | `omnix_services/market_intelligence/` | `src/omnix/infrastructure/adapters/alternative_me/` | Alternative.me | Fear/Greed validation | ✅ SUPPORT |
| 2.7 | TavilyAdapter | `omnix_services/web_search_service/tavily_search.py` | `src/omnix/infrastructure/adapters/tavily/` | Tavily | Search result tests | ✅ SUPPORT |
| 2.8 | CoinGeckoAdapter | `omnix_services/market_data/` | `src/omnix/infrastructure/adapters/coingecko/` | CoinGecko | Fallback price tests | ✅ SUPPORT |
| 2.9 | MarketIntelligence | `omnix_services/market_intelligence/` | `src/omnix/application/market_intelligence/` | Multiple | Aggregation tests | ✅ CORE |
| 2.10 | WebSearchService | `omnix_services/web_search_service/` | `src/omnix/application/web_search/` | Tavily | Intent detection tests | ✅ SUPPORT |
| 2.11 | IntentDetector | `omnix_services/web_search_service/intent_detector.py` | `src/omnix/application/web_search/intent.py` | - | NLP classification tests | ✅ SUPPORT |
| 2.12 | SearchManager | `omnix_services/web_search_service/search_manager.py` | `src/omnix/application/web_search/manager.py` | - | Orchestration tests | ✅ SUPPORT |
| 2.13 | NewsScraper | `omnix_services/news_scraper.py` | `src/omnix/infrastructure/adapters/news/` | - | Parsing tests | ⚠️ STRATEGIC |
| 2.14 | SymbolClassifier | `omnix_services/symbol_classifier.py` | `src/omnix/domain/shared/symbol_classifier.py` | - | Classification tests | ✅ SUPPORT |
| 2.15 | ArbitrageScanner | `omnix_services/market_data/intelligence/arbitrage_scanner.py` | `src/omnix/application/arbitrage/scanner.py` | 8 exchanges | Multi-exchange mocking | ⚠️ STRATEGIC |
| 2.16 | ArbitrageExecutor | `omnix_services/market_data/intelligence/arbitrage_executor.py` | `src/omnix/application/arbitrage/executor.py` | 8 exchanges | Paper trading tests | ⚠️ STRATEGIC |

**Cobertura Dominio 2**: 16/16 componentes ✅

---

## DOMINIO 3: Execution & Brokerage

### Fase de Migración: **FASE 5** (Semanas 7-9)

| # | Componente | Ubicación Legacy | Ubicación V7.0 | Dependencias | Validación | Prioridad |
|---|------------|------------------|----------------|--------------|------------|-----------|
| 3.1 | TradingPort | `src/omnix/ports/driven/trading_port.py` | `src/omnix/ports/driven/trading.py` | - | Contract tests | ✅ CORE |
| 3.2 | ExecutionProtocol | `omnix_services/execution_service/execution_protocol.py` | `src/omnix/domain/execution/protocol.py` | RiskService (F3) | 4-layer testing | ✅ CORE |
| 3.3 | TradingSystem | `omnix_core/trading_system.py` | `src/omnix/application/trading/system.py` | ExecutionProtocol | End-to-end tests | ✅ CORE |
| 3.4 | KrakenBroker | `omnix_services/trading_service/kraken_client.py` | `src/omnix/infrastructure/brokers/kraken/` | KrakenAdapter (F2) | Sandbox testing | ✅ CORE |
| 3.5 | PaperTradingManager | `omnix_services/trading_service/paper_trading_manager.py` | `src/omnix/application/paper_trading/manager.py` | Database (F2) | Ledger reconciliation | ✅ CORE |
| 3.6 | PositionManager | `omnix_services/trading_service/position_manager.py` | `src/omnix/domain/execution/positions.py` | Database (F2) | Position tracking tests | ✅ CORE |
| 3.7 | AlpacaBroker | `omnix_services/stock_trading/` | `src/omnix/infrastructure/brokers/alpaca/` | Alpaca API | Sandbox testing | ✅ SUPPORT |
| 3.8 | StockTradingService | `omnix_services/stock_trading/` | `src/omnix/application/stock_trading/` | AlpacaBroker | Paper trading tests | ✅ SUPPORT |
| 3.9 | DerivativesBroker | `omnix_services/derivatives/` | `src/omnix/infrastructure/brokers/derivatives/` | Kraken Futures | Sandbox testing | ⚠️ STRATEGIC |
| 3.10 | DerivativesService | `omnix_services/derivatives/` | `src/omnix/application/derivatives/` | DerivativesBroker | Paper testing | ⚠️ STRATEGIC |
| 3.11 | OrderRouter | - (nuevo) | `src/omnix/domain/execution/router.py` | All brokers | Multi-broker tests | ✅ CORE |
| 3.12 | TWAP Execution | `omnix_services/execution_service/` | `src/omnix/domain/execution/algorithms/twap.py` | - | Algorithm tests | ✅ CORE |
| 3.13 | VWAP Execution | `omnix_services/execution_service/` | `src/omnix/domain/execution/algorithms/vwap.py` | - | Algorithm tests | ✅ CORE |
| 3.14 | ICEBERG Execution | `omnix_services/execution_service/` | `src/omnix/domain/execution/algorithms/iceberg.py` | - | Algorithm tests | ✅ SUPPORT |

**Cobertura Dominio 3**: 14/14 componentes ✅

---

## DOMINIO 4: Risk & Protection

### Fase de Migración: **FASE 3** (Semana 4)

| # | Componente | Ubicación Legacy | Ubicación V7.0 | Dependencias | Validación | Prioridad |
|---|------------|------------------|----------------|--------------|------------|-----------|
| 4.1 | RiskManagement | `omnix_services/risk_management/` | `src/omnix/domain/risk/` | Database (F2) | Historical replay | ✅ CORE |
| 4.2 | CircuitBreaker | `omnix_services/risk_management/circuit_breaker.py` | `src/omnix/domain/risk/circuit_breaker.py` | Monitoring | Chaos testing | ✅ CORE |
| 4.3 | RiskGuardian V5.4 | `omnix_services/monitoring/risk_guardian.py` | `src/omnix/domain/risk/guardian.py` | Database (F2) | Overtrading tests | ✅ CORE |
| 4.4 | MemoryRiskAdapter | `omnix_services/risk_management/memory_risk_adapter.py` | `src/omnix/infrastructure/adapters/risk/memory.py` | NonMarkovian (F4) | Integration tests | ✅ SUPPORT |
| 4.5 | RollbackProtocol (ARP) | `omnix_core/risk/rollback_protocol.py` | `src/omnix/domain/risk/rollback.py` | Config (F1) | Threshold tests | ✅ CORE |
| 4.6 | Monitoring | `omnix_services/monitoring/` | `src/omnix/application/monitoring/` | Database (F2) | Metrics validation | ✅ CORE |
| 4.7 | PerformanceTracker | `omnix_services/monitoring/` | `src/omnix/application/monitoring/performance.py` | Database (F2) | Metrics accuracy | ✅ SUPPORT |
| 4.8 | DeadManSwitch | `omnix_services/monitoring/` | `src/omnix/domain/risk/dead_man_switch.py` | - | Timeout tests | ✅ SUPPORT |
| 4.9 | CascadeProtection | `omnix_services/risk_management/` | `src/omnix/domain/risk/cascade.py` | PositionManager (F5) | Portfolio tests | ✅ CORE |
| 4.10 | EmergencyStop | `omnix_core/bot/auto_trading_bot.py` | `src/omnix/domain/risk/emergency_stop.py` | - | 2% SL tests | ✅ CORE |

**Cobertura Dominio 4**: 10/10 componentes ✅

---

## DOMINIO 5: AI & Communication

### Fase de Migración: **FASE 6** (Semanas 10-12)

| # | Componente | Ubicación Legacy | Ubicación V7.0 | APIs Externas | Validación | Prioridad |
|---|------------|------------------|----------------|---------------|------------|-----------|
| 5.1 | AIInferencePort | `src/omnix/ports/driven/ai_inference_port.py` | `src/omnix/ports/driven/ai_inference.py` | - | Contract tests | ✅ CORE |
| 5.2 | ConversationalAIService | `omnix_services/ai_service/ai_service.py` | `src/omnix/application/ai/conversational.py` | All AI providers | Response quality | ✅ CORE |
| 5.3 | RoutingAIGateway | `omnix_services/ai_service/providers/routing_gateway.py` | `src/omnix/application/ai/routing.py` | - | Fallback tests | ✅ CORE |
| 5.4 | GeminiAdapter | `omnix_services/ai_service/providers/gemini_provider.py` | `src/omnix/infrastructure/adapters/ai/gemini.py` | Gemini 2.0 Flash | API mocking | ✅ CORE |
| 5.5 | OpenAIAdapter | `omnix_services/ai_service/providers/openai_provider.py` | `src/omnix/infrastructure/adapters/ai/openai.py` | GPT-4o | API mocking | ✅ SUPPORT |
| 5.6 | AnthropicAdapter | `omnix_services/ai_service/providers/anthropic_provider.py` | `src/omnix/infrastructure/adapters/ai/anthropic.py` | Claude | API mocking | ✅ SUPPORT |
| 5.7 | DI Container AI | `omnix_services/ai_service/container.py` | `src/omnix/bootstrap/ai_container.py` | - | DI tests | ✅ CORE |
| 5.8 | VideoAnalyzer | `omnix_services/ai_service/video/analyzer.py` | `src/omnix/application/ai/video/` | OpenAI Whisper | Video processing tests | ⚠️ STRATEGIC |
| 5.9 | VoiceService | `omnix_services/voice_service/` | `src/omnix/application/voice/` | OpenAI Whisper | STT/TTS tests | ✅ SUPPORT |
| 5.10 | QuantumPhysicsValidator | `omnix_core/quantum/physics_validator.py` | `src/omnix/domain/validation/physics.py` | - | Scientific accuracy | ⚠️ STRATEGIC |
| 5.11 | PromptBuilder | `omnix_services/ai_service/providers/omnix_prompt_builder.py` | `src/omnix/application/ai/prompts/` | - | Prompt tests | ✅ SUPPORT |
| 5.12 | StyleRenderer | `omnix_services/ai_service/providers/omnix_style_renderer.py` | `src/omnix/application/ai/rendering/` | - | Style tests | ✅ SUPPORT |

**Cobertura Dominio 5**: 12/12 componentes ✅

---

## DOMINIO 6: User Interfaces

### Fase de Migración: **FASE 6** (Semanas 10-12)

| # | Componente | Ubicación Legacy | Ubicación V7.0 | Dependencias | Validación | Prioridad |
|---|------------|------------------|----------------|--------------|------------|-----------|
| 6.1 | TelegramPort | `src/omnix/ports/driver/telegram_port.py` | `src/omnix/ports/driver/telegram.py` | - | Contract tests | ✅ CORE |
| 6.2 | EnterpriseBot | `omnix_services/telegram_service/enterprise_bot.py` | `src/omnix/interfaces/telegram/bot.py` | All services | E2E tests | ✅ CORE |
| 6.3 | InlineKeyboards | `omnix_services/telegram_service/inline_keyboards.py` | `src/omnix/interfaces/telegram/keyboards.py` | - | UI tests | ✅ SUPPORT |
| 6.4 | CallbackHandler | `omnix_services/telegram_service/callback_handler.py` | `src/omnix/interfaces/telegram/callbacks.py` | - | Callback tests | ✅ SUPPORT |
| 6.5 | PortfolioCommands | `omnix_services/telegram_service/portfolio_commands.py` | `src/omnix/interfaces/telegram/handlers/portfolio.py` | - | Command tests | ✅ SUPPORT |
| 6.6 | MarketCommands | - (en enterprise_bot) | `src/omnix/interfaces/telegram/handlers/market.py` | MarketData (F2) | Command tests | ✅ CORE |
| 6.7 | TradingCommands | - (en enterprise_bot) | `src/omnix/interfaces/telegram/handlers/trading.py` | Trading (F5) | Command tests | ✅ CORE |
| 6.8 | AnalysisCommands | - (en enterprise_bot) | `src/omnix/interfaces/telegram/handlers/analysis.py` | Strategies (F4) | Command tests | ✅ SUPPORT |
| 6.9 | ConfigCommands | - (en enterprise_bot) | `src/omnix/interfaces/telegram/handlers/config.py` | UserSettings (F2) | Command tests | ✅ SUPPORT |
| 6.10 | CommunityCommands | - (en enterprise_bot) | `src/omnix/interfaces/telegram/handlers/community.py` | Community (F2) | Command tests | ⚠️ STRATEGIC |
| 6.11 | QuantumCommands | - (en enterprise_bot) | `src/omnix/interfaces/telegram/handlers/quantum.py` | Quantum (F1) | Command tests | ⚠️ STRATEGIC |
| 6.12 | FlaskApp | `omnix_dashboard/app.py` | `src/omnix/interfaces/rest/app.py` | All services | API tests | ✅ CORE |
| 6.13 | CoreBlueprint | `omnix_dashboard/blueprints/core.py` | `src/omnix/interfaces/rest/routes/core.py` | Database (F2) | Route tests | ✅ CORE |
| 6.14 | MarketBlueprint | `omnix_dashboard/blueprints/market.py` | `src/omnix/interfaces/rest/routes/market.py` | MarketData (F2) | Route tests | ✅ SUPPORT |
| 6.15 | SystemBlueprint | `omnix_dashboard/blueprints/system.py` | `src/omnix/interfaces/rest/routes/system.py` | Monitoring (F3) | Route tests | ✅ SUPPORT |
| 6.16 | IntelligenceBlueprint | `omnix_dashboard/blueprints/intelligence.py` | `src/omnix/interfaces/rest/routes/intelligence.py` | AI (F6) | Route tests | ✅ SUPPORT |
| 6.17 | StreamlitApp | `omnix_dashboard/streamlit_app.py` | `src/omnix/interfaces/streamlit/app.py` | Flask API | Visual tests | ✅ CORE |
| 6.18 | OmnixAPIClient | `omnix_dashboard/api_client.py` | `src/omnix/interfaces/streamlit/client.py` | Flask API | Client tests | ✅ SUPPORT |
| 6.19 | Notifications | `omnix_services/notifications/` | `src/omnix/application/notifications/` | TelegramPort | Notification tests | ✅ SUPPORT |
| 6.20 | DailySummary | `omnix_services/notifications/` | `src/omnix/application/notifications/daily.py` | Analytics (F3) | Summary tests | ✅ SUPPORT |

**Cobertura Dominio 6**: 20/20 componentes ✅

---

## DOMINIO 7: Persistence & Analytics

### Fase de Migración: **FASE 2** (Semanas 2-3)

| # | Componente | Ubicación Legacy | Ubicación V7.0 | Dependencias | Validación | Prioridad |
|---|------------|------------------|----------------|--------------|------------|-----------|
| 7.1 | DatabasePort | `src/omnix/ports/driven/database_port.py` | `src/omnix/ports/driven/database.py` | - | Contract tests | ✅ CORE |
| 7.2 | DatabaseGateway | `omnix_services/database_service/database_gateway.py` | `src/omnix/infrastructure/adapters/postgres/gateway.py` | PostgreSQL | Pool tests | ✅ CORE |
| 7.3 | CachePort | `src/omnix/ports/driven/cache_port.py` | `src/omnix/ports/driven/cache.py` | - | Contract tests | ✅ CORE |
| 7.4 | RedisCache | `omnix_core/cache/redis_cache.py` | `src/omnix/infrastructure/adapters/redis/cache.py` | Redis | TTL tests | ✅ CORE |
| 7.5 | Analytics | `omnix_services/analytics/` | `src/omnix/application/analytics/` | Database | Metrics accuracy | ✅ CORE |
| 7.6 | InstitutionalMetrics | `omnix_services/analytics/institutional_metrics.py` | `src/omnix/application/analytics/institutional.py` | Database | Sharpe/Sortino tests | ✅ CORE |
| 7.7 | InstitutionalReport | `omnix_services/analytics/institutional_report.py` | `src/omnix/application/analytics/report.py` | Analytics | PDF generation | ✅ SUPPORT |
| 7.8 | VolumeProfile | `omnix_services/analytics/volume_profile.py` | `src/omnix/application/analytics/volume.py` | MarketData (F2) | Profile tests | ✅ SUPPORT |
| 7.9 | FibonacciAnalyzer | `omnix_services/analytics/fibonacci_analyzer.py` | `src/omnix/application/analytics/fibonacci.py` | MarketData (F2) | Level tests | ✅ SUPPORT |
| 7.10 | UserRepository | `omnix_services/database_service/` | `src/omnix/infrastructure/repositories/user.py` | Database | CRUD tests | ✅ CORE |
| 7.11 | TradeRepository | `omnix_services/database_service/` | `src/omnix/infrastructure/repositories/trade.py` | Database | CRUD tests | ✅ CORE |
| 7.12 | BalanceRepository | `omnix_services/database_service/` | `src/omnix/infrastructure/repositories/balance.py` | Database | CRUD tests | ✅ CORE |
| 7.13 | RiskEventRepository | `omnix_services/database_service/` | `src/omnix/infrastructure/repositories/risk_event.py` | Database | CRUD tests | ✅ CORE |
| 7.14 | DecisionLogRepository | `omnix_services/database_service/` | `src/omnix/infrastructure/repositories/decision_log.py` | Database | Audit tests | ✅ CORE |

**Cobertura Dominio 7**: 14/14 componentes ✅

---

## DOMINIO 8: Security & Quantum

### Fase de Migración: **FASE 1** (Semana 1)

| # | Componente | Ubicación Legacy | Ubicación V7.0 | Dependencias | Validación | Prioridad |
|---|------------|------------------|----------------|--------------|------------|-----------|
| 8.1 | PQCSecurity | `omnix_core/security/pqc_security.py` | `src/omnix/infrastructure/security/pqc.py` | - | Crypto tests | ✅ CORE |
| 8.2 | Kyber768 | `omnix_core/security/pqc_security.py` | `src/omnix/infrastructure/security/kyber.py` | - | Key encapsulation tests | ✅ CORE |
| 8.3 | Dilithium3 | `omnix_core/security/pqc_security.py` | `src/omnix/infrastructure/security/dilithium.py` | - | Signature tests | ✅ CORE |
| 8.4 | QuantumEnhancements | `omnix_core/quantum/enhancements.py` | `src/omnix/infrastructure/quantum/` | - | QRNG tests | ✅ SUPPORT |
| 8.5 | QRNG | `omnix_core/quantum/enhancements.py` | `src/omnix/infrastructure/quantum/qrng.py` | ANU API | Randomness tests | ✅ SUPPORT |
| 8.6 | QAOA | `omnix_core/quantum/enhancements.py` | `src/omnix/infrastructure/quantum/qaoa.py` | - | Optimization tests | ⚠️ STRATEGIC |

**Cobertura Dominio 8**: 6/6 componentes ✅

---

## DOMINIO 9: Portfolio Optimization

### Fase de Migración: **FASE 3** (Semana 4)

| # | Componente | Ubicación Legacy | Ubicación V7.0 | Dependencias | Validación | Prioridad |
|---|------------|------------------|----------------|--------------|------------|-----------|
| 9.1 | PortfolioManagement | `omnix_services/portfolio_management/` | `src/omnix/domain/portfolio/` | RiskService (F3) | Optimization tests | ✅ SUPPORT |
| 9.2 | MarkowitzOptimizer | `omnix_services/portfolio_management/` | `src/omnix/domain/portfolio/markowitz.py` | Analytics | Mean-variance tests | ✅ SUPPORT |
| 9.3 | BlackLittermanOptimizer | `omnix_services/portfolio_management/` | `src/omnix/domain/portfolio/black_litterman.py` | Analytics | View integration tests | ✅ SUPPORT |
| 9.4 | CAESPositionSizing | `omnix_core/strategies/caes_module.py` | `src/omnix/domain/sizing/caes.py` | Strategies (F4) | Sizing tests | ✅ CORE |

**Cobertura Dominio 9**: 4/4 componentes ✅

---

## DOMINIO 10: Community Intelligence

### Fase de Migración: **FASE 2** (Semanas 2-3)

| # | Componente | Ubicación Legacy | Ubicación V7.0 | Dependencias | Validación | Prioridad |
|---|------------|------------------|----------------|--------------|------------|-----------|
| 10.1 | FeedbackManager | `omnix_services/community_intelligence/feedback_manager.py` | `src/omnix/application/community/feedback.py` | Database (F2) | CRUD tests | ⚠️ STRATEGIC |
| 10.2 | CommunityAnalyzer | `omnix_services/community_intelligence/community_analyzer.py` | `src/omnix/application/community/analyzer.py` | AI (F6) | Analysis tests | ⚠️ STRATEGIC |
| 10.3 | RewardSystem | `omnix_services/community_intelligence/reward_system.py` | `src/omnix/application/community/rewards.py` | Database (F2) | Points tests | ⚠️ STRATEGIC |
| 10.4 | CommunityDashboard | `omnix_services/community_intelligence/community_dashboard.py` | `src/omnix/application/community/dashboard.py` | Database (F2) | Stats tests | ⚠️ STRATEGIC |
| 10.5 | SignalContribution | `omnix_services/community_intelligence/signal_contribution.py` | `src/omnix/application/community/signals.py` | Database (F2) | Contribution tests | ⚠️ STRATEGIC |

**Cobertura Dominio 10**: 5/5 componentes ✅

---

## DOMINIO 11: Trading Profiles & User Settings

### Fase de Migración: **FASE 1** (Semana 1)

| # | Componente | Ubicación Legacy | Ubicación V7.0 | Dependencias | Validación | Prioridad |
|---|------------|------------------|----------------|--------------|------------|-----------|
| 11.1 | TradingProfiles | `omnix_core/config/trading_profiles.py` | `src/omnix/config/profiles.py` | - | Profile tests | ✅ CORE |
| 11.2 | PRODUCTION_STABLE | `omnix_core/config/trading_profiles.py` | `src/omnix/config/profiles/production_stable.py` | - | Parameter tests | ✅ CORE |
| 11.3 | INSTITUTIONAL | `omnix_core/config/trading_profiles.py` | `src/omnix/config/profiles/institutional.py` | - | Parameter tests | ✅ SUPPORT |
| 11.4 | PAPER_AGGRESSIVE | `omnix_core/config/trading_profiles.py` | `src/omnix/config/profiles/paper_aggressive.py` | - | Parameter tests | ✅ SUPPORT |
| 11.5 | PAPER_OPTIMIZED | `omnix_core/config/trading_profiles.py` | `src/omnix/config/profiles/paper_optimized.py` | - | Parameter tests | ✅ SUPPORT |
| 11.6 | UserSettingsService | `omnix_services/user_settings/user_settings_service.py` | `src/omnix/application/user_settings/service.py` | Database (F2) | Settings tests | ✅ CORE |
| 11.7 | SettingsModels | `omnix_services/user_settings/settings_models.py` | `src/omnix/domain/user/settings.py` | - | Model tests | ✅ CORE |

**Cobertura Dominio 11**: 7/7 componentes ✅

---

## RESUMEN DE COBERTURA

| Dominio | Componentes | Cubiertos | Cobertura |
|---------|-------------|-----------|-----------|
| 1. Trading Signal Fabric | 15 | 15 | ✅ 100% |
| 2. Market & Data Ingestion | 16 | 16 | ✅ 100% |
| 3. Execution & Brokerage | 14 | 14 | ✅ 100% |
| 4. Risk & Protection | 10 | 10 | ✅ 100% |
| 5. AI & Communication | 12 | 12 | ✅ 100% |
| 6. User Interfaces | 20 | 20 | ✅ 100% |
| 7. Persistence & Analytics | 14 | 14 | ✅ 100% |
| 8. Security & Quantum | 6 | 6 | ✅ 100% |
| 9. Portfolio Optimization | 4 | 4 | ✅ 100% |
| 10. Community Intelligence | 5 | 5 | ✅ 100% |
| 11. Trading Profiles | 7 | 7 | ✅ 100% |
| **TOTAL** | **123** | **123** | **✅ 100%** |

---

## COMPONENTES POR FASE

| Fase | Dominios | Componentes | Duración |
|------|----------|-------------|----------|
| **F1** | 8, 11 | 13 (Security, Profiles, Config) | 5-7 días |
| **F2** | 2, 7, 10 | 35 (Data, Persistence, Community) | 7-10 días |
| **F3** | 4, 9 | 14 (Risk, Portfolio) | 5-7 días |
| **F4** | 1 | 15 (Strategies, Coherence) | 10-14 días |
| **F5** | 3 | 14 (Execution, Brokers) | 12-16 días |
| **F6** | 5, 6 | 32 (AI, Interfaces) | 10-14 días |
| **TOTAL** | 11 | 123 | 49-68 días |

---

## FUNCIONALIDADES HUÉRFANAS O SIN COBERTURA

### Revisión de cobertura: ❌ NINGUNA

Todos los 123 componentes identificados tienen:
- ✅ Fase de migración asignada
- ✅ Ubicación V7.0 propuesta
- ✅ Dependencias documentadas
- ✅ Método de validación definido

### Componentes Marcados como STRATEGIC (pueden diferirse)

| Componente | Dominio | Razón |
|------------|---------|-------|
| NewsScraper | 2 | Funcionalidad de scraping no crítica |
| ArbitrageScanner | 2 | Feature avanzado, no en MVP |
| ArbitrageExecutor | 2 | Feature avanzado, no en MVP |
| VideoAnalyzer | 5 | Feature experimental |
| QuantumPhysicsValidator | 5 | Feature nicho |
| QAOA | 8 | Research phase |
| Toda Community Intelligence | 10 | B2C feature futuro |

---

## DEPENDENCIAS CRÍTICAS CROSS-FASE

```
F1 → F2: Config/DI necesarios para todos los adapters
F2 → F3: Database/Cache necesarios para Risk
F2 → F4: MarketData necesario para Strategies
F3 → F4: RiskService necesario para CAES sizing
F3 → F5: Risk checks antes de execution
F4 → F5: Signals necesarios para trading
F2,F3,F4,F5 → F6: Todas las capas necesarias para interfaces
```

---

*Matriz creada: 15 de Diciembre 2025*  
*Última actualización: 15 de Diciembre 2025*  
*Total componentes: 123*  
*Cobertura: 100%*
