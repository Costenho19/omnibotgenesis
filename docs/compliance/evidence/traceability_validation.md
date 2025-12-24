# OMNIX Traceability Validation Report

**Generated**: 2025-12-24 06:29:20  
**Git Commit**: 060c17c2  
**Branch**: main  
**Total Components**: 123

---

## Executive Summary

| Status | Count | Description |
|--------|-------|-------------|
| ✅ FULL | 1 | Both Legacy and V7 paths exist |
| 🟡 LEGACY_ONLY | 115 | Legacy exists, V7 not yet created |
| 🔵 V7_ONLY | 0 | V7 exists (new component or migrated) |
| ⚪ PLANNED | 7 | New in V7, marked as planned |
| ❌ MISSING | 0 | Neither path exists |

### Validation Score

- **Legacy Coverage**: 116/123 (94%)
- **V7 Coverage**: 1/123 (0%)

---

## Domain Breakdown

| Domain | Total | Legacy Exists | V7 Exists |
|--------|-------|---------------|-----------|
| 1. Trading Signal Fabric | 15 | 15 | 0 |
| 10. Community Intelligence | 5 | 5 | 0 |
| 11. Trading Profiles & User Settings | 7 | 7 | 0 |
| 2. Market & Data Ingestion | 16 | 16 | 0 |
| 3. Execution & Brokerage | 14 | 13 | 0 |
| 4. Risk & Protection | 10 | 10 | 1 |
| 5. AI & Communication | 12 | 12 | 0 |
| 6. User Interfaces | 20 | 14 | 0 |
| 7. Persistence & Analytics | 14 | 14 | 0 |
| 8. Security & Quantum | 6 | 6 | 0 |
| 9. Portfolio Optimization | 4 | 4 | 0 |

---

## Component Details by Status

### 🟡 LEGACY_ONLY (115 components)

| ID | Name | Legacy Path | V7 Path | Priority |
|-----|------|-------------|---------|----------|
| 1.1 | QuantumMomentum | `omnix_services/trading_service/quantum_momentum.py` | `src/omnix/domain/strategies/quantum_momentum.py` | CORE |
| 1.2 | Monte Carlo | `omnix_services/trading_service/monte_carlo.py` | `src/omnix/domain/strategies/monte_carlo.py` | CORE |
| 1.3 | Kelly Criterion | `omnix_services/trading_service/kelly_criterion.py` | `src/omnix/domain/strategies/kelly.py` | CORE |
| 1.4 | Black Swan | `omnix_services/trading_service/black_swan.py` | `src/omnix/domain/strategies/black_swan.py` | CORE |
| 1.5 | HMM Regime | `omnix_services/trading_service/hmm_regime.py` | `src/omnix/domain/strategies/hmm_regime.py` | CORE |
| 1.6 | Kalman Filter | `omnix_services/trading_service/kalman_filter.py` | `src/omnix/domain/strategies/kalman.py` | CORE |
| 1.7 | Sentiment Analysis | `omnix_services/market_intelligence/` | `src/omnix/domain/strategies/sentiment.py` | CORE |
| 1.8 | Non-Markovian Kernel | `omnix_core/strategies/non_markovian_kernel.py` | `src/omnix/domain/strategies/non_markovian.py` | CORE |
| 1.9 | CoherenceEngine | `omnix_services/coherence_service/coherence_engine.py` | `src/omnix/domain/coherence/engine.py` | CORE |
| 1.10 | Risk Guardian | `omnix_services/monitoring/risk_guardian.py` | `src/omnix/domain/risk/guardian.py` | CORE |
| 1.11 | CAES Module | `omnix_core/strategies/caes_module.py` | `src/omnix/domain/sizing/caes.py` | CORE |
| 1.12 | ARES V1 (Swing) | `omnix_core/strategies/ares_v1.py` | `src/omnix/domain/strategies/ares/v1.py` | CORE |
| 1.13 | ARES V2 (Scalping) | `omnix_core/strategies/ares_v2.py` | `src/omnix/domain/strategies/ares/v2.py` | CORE |
| 1.14 | Adaptive Engine | `omnix_services/adaptive_engine/adaptive_engine.py` | `src/omnix/domain/adaptive/engine.py` | SUPPORT |
| 1.15 | Optimization ML | `omnix_services/optimization/` | `src/omnix/domain/optimization/` | SUPPORT |
| 2.1 | MarketDataPort | `omnix_services/market_data/` | `src/omnix/ports/driven/market_data.py` | CORE |
| 2.2 | KrakenAdapter REST | `omnix_services/trading_service/kraken_client.py` | `src/omnix/infrastructure/adapters/kraken/rest.py` | CORE |
| 2.3 | KrakenAdapter WS | `omnix_services/trading_service/kraken_client.py` | `src/omnix/infrastructure/adapters/kraken/websocket.py` | CORE |
| 2.4 | AlphaVantageAdapter | `omnix_services/market_intelligence/` | `src/omnix/infrastructure/adapters/alphavantage/` | SUPPORT |
| 2.5 | FinnhubAdapter | `omnix_services/market_intelligence/` | `src/omnix/infrastructure/adapters/finnhub/` | SUPPORT |
| 2.6 | AlternativeMeAdapter | `omnix_services/market_intelligence/` | `src/omnix/infrastructure/adapters/alternative_me/` | SUPPORT |
| 2.7 | TavilyAdapter | `omnix_services/web_search_service/tavily_search.py` | `src/omnix/infrastructure/adapters/tavily/` | SUPPORT |
| 2.8 | CoinGeckoAdapter | `omnix_services/market_data/` | `src/omnix/infrastructure/adapters/coingecko/` | SUPPORT |
| 2.9 | MarketIntelligence | `omnix_services/market_intelligence/` | `src/omnix/application/market_intelligence/` | CORE |
| 2.10 | WebSearchService | `omnix_services/web_search_service/` | `src/omnix/application/web_search/` | SUPPORT |
| 2.11 | IntentDetector | `omnix_services/web_search_service/intent_detector.py` | `src/omnix/application/web_search/intent.py` | SUPPORT |
| 2.12 | SearchManager | `omnix_services/web_search_service/search_manager.py` | `src/omnix/application/web_search/manager.py` | SUPPORT |
| 2.13 | NewsScraper | `omnix_services/news_scraper.py` | `src/omnix/infrastructure/adapters/news/` | STRATEGIC |
| 2.14 | SymbolClassifier | `omnix_services/symbol_classifier.py` | `src/omnix/domain/shared/symbol_classifier.py` | SUPPORT |
| 2.15 | ArbitrageScanner | `omnix_services/market_data/intelligence/arbitrage_scanner.py` | `src/omnix/application/arbitrage/scanner.py` | STRATEGIC |
| 2.16 | ArbitrageExecutor | `omnix_services/market_data/intelligence/arbitrage_executor.py` | `src/omnix/application/arbitrage/executor.py` | STRATEGIC |
| 3.1 | TradingPort | `src/omnix/ports/driven/trading_port.py` | `src/omnix/ports/driven/trading.py` | CORE |
| 3.2 | ExecutionProtocol | `omnix_services/execution_service/execution_protocol.py` | `src/omnix/domain/execution/protocol.py` | CORE |
| 3.3 | TradingSystem | `omnix_core/trading_system.py` | `src/omnix/application/trading/system.py` | CORE |
| 3.4 | KrakenBroker | `omnix_services/trading_service/kraken_client.py` | `src/omnix/infrastructure/brokers/kraken/` | CORE |
| 3.5 | PaperTradingManager | `omnix_services/trading_service/paper_trading_manager.py` | `src/omnix/application/paper_trading/manager.py` | CORE |
| 3.6 | PositionManager | `omnix_services/trading_service/position_manager.py` | `src/omnix/domain/execution/positions.py` | CORE |
| 3.7 | AlpacaBroker | `omnix_services/stock_trading/` | `src/omnix/infrastructure/brokers/alpaca/` | SUPPORT |
| 3.8 | StockTradingService | `omnix_services/stock_trading/` | `src/omnix/application/stock_trading/` | SUPPORT |
| 3.9 | DerivativesBroker | `omnix_services/derivatives/` | `src/omnix/infrastructure/brokers/derivatives/` | STRATEGIC |
| 3.10 | DerivativesService | `omnix_services/derivatives/` | `src/omnix/application/derivatives/` | STRATEGIC |
| 3.12 | TWAP Execution | `omnix_services/execution_service/` | `src/omnix/domain/execution/algorithms/twap.py` | CORE |
| 3.13 | VWAP Execution | `omnix_services/execution_service/` | `src/omnix/domain/execution/algorithms/vwap.py` | CORE |
| 3.14 | ICEBERG Execution | `omnix_services/execution_service/` | `src/omnix/domain/execution/algorithms/iceberg.py` | SUPPORT |
| 4.2 | CircuitBreaker | `omnix_services/risk_management/circuit_breaker.py` | `src/omnix/domain/risk/circuit_breaker.py` | CORE |
| 4.3 | RiskGuardian V5.4 | `omnix_services/monitoring/risk_guardian.py` | `src/omnix/domain/risk/guardian.py` | CORE |
| 4.4 | MemoryRiskAdapter | `omnix_services/risk_management/memory_risk_adapter.py` | `src/omnix/infrastructure/adapters/risk/memory.py` | SUPPORT |
| 4.5 | RollbackProtocol (ARP) | `omnix_core/risk/rollback_protocol.py` | `src/omnix/domain/risk/rollback.py` | CORE |
| 4.6 | Monitoring | `omnix_services/monitoring/` | `src/omnix/application/monitoring/` | CORE |
| 4.7 | PerformanceTracker | `omnix_services/monitoring/` | `src/omnix/application/monitoring/performance.py` | SUPPORT |
| 4.8 | DeadManSwitch | `omnix_services/monitoring/` | `src/omnix/domain/risk/dead_man_switch.py` | SUPPORT |
| 4.9 | CascadeProtection | `omnix_services/risk_management/` | `src/omnix/domain/risk/cascade.py` | CORE |
| 4.10 | EmergencyStop | `omnix_core/bot/auto_trading_bot.py` | `src/omnix/domain/risk/emergency_stop.py` | CORE |
| 5.1 | AIInferencePort | `src/omnix/ports/driven/ai_inference_port.py` | `src/omnix/ports/driven/ai_inference.py` | CORE |
| 5.2 | ConversationalAIService | `omnix_services/ai_service/ai_service.py` | `src/omnix/application/ai/conversational.py` | CORE |
| 5.3 | RoutingAIGateway | `omnix_services/ai_service/providers/routing_gateway.py` | `src/omnix/application/ai/routing.py` | CORE |
| 5.4 | GeminiAdapter | `omnix_services/ai_service/providers/gemini_provider.py` | `src/omnix/infrastructure/adapters/ai/gemini.py` | CORE |
| 5.5 | OpenAIAdapter | `omnix_services/ai_service/providers/openai_provider.py` | `src/omnix/infrastructure/adapters/ai/openai.py` | SUPPORT |
| 5.6 | AnthropicAdapter | `omnix_services/ai_service/providers/anthropic_provider.py` | `src/omnix/infrastructure/adapters/ai/anthropic.py` | SUPPORT |
| 5.7 | DI Container AI | `omnix_services/ai_service/container.py` | `src/omnix/bootstrap/ai_container.py` | CORE |
| 5.8 | VideoAnalyzer | `omnix_services/ai_service/video/analyzer.py` | `src/omnix/application/ai/video/` | STRATEGIC |
| 5.9 | VoiceService | `omnix_services/voice_service/` | `src/omnix/application/voice/` | SUPPORT |
| 5.10 | QuantumPhysicsValidator | `omnix_core/quantum/physics_validator.py` | `src/omnix/domain/validation/physics.py` | STRATEGIC |
| 5.11 | PromptBuilder | `omnix_services/ai_service/providers/omnix_prompt_builder.py` | `src/omnix/application/ai/prompts/` | SUPPORT |
| 5.12 | StyleRenderer | `omnix_services/ai_service/providers/omnix_style_renderer.py` | `src/omnix/application/ai/rendering/` | SUPPORT |
| 6.1 | TelegramPort | `src/omnix/ports/driver/telegram_port.py` | `src/omnix/ports/driver/telegram.py` | CORE |
| 6.2 | EnterpriseBot | `omnix_services/telegram_service/enterprise_bot.py` | `src/omnix/interfaces/telegram/bot.py` | CORE |
| 6.3 | InlineKeyboards | `omnix_services/telegram_service/inline_keyboards.py` | `src/omnix/interfaces/telegram/keyboards.py` | SUPPORT |
| 6.4 | CallbackHandler | `omnix_services/telegram_service/callback_handler.py` | `src/omnix/interfaces/telegram/callbacks.py` | SUPPORT |
| 6.5 | PortfolioCommands | `omnix_services/telegram_service/portfolio_commands.py` | `src/omnix/interfaces/telegram/handlers/portfolio.py` | SUPPORT |
| 6.12 | FlaskApp | `omnix_dashboard/app.py` | `src/omnix/interfaces/rest/app.py` | CORE |
| 6.13 | CoreBlueprint | `omnix_dashboard/blueprints/core.py` | `src/omnix/interfaces/rest/routes/core.py` | CORE |
| 6.14 | MarketBlueprint | `omnix_dashboard/blueprints/market.py` | `src/omnix/interfaces/rest/routes/market.py` | SUPPORT |
| 6.15 | SystemBlueprint | `omnix_dashboard/blueprints/system.py` | `src/omnix/interfaces/rest/routes/system.py` | SUPPORT |
| 6.16 | IntelligenceBlueprint | `omnix_dashboard/blueprints/intelligence.py` | `src/omnix/interfaces/rest/routes/intelligence.py` | SUPPORT |
| 6.17 | StreamlitApp | `omnix_dashboard/streamlit_app.py` | `src/omnix/interfaces/streamlit/app.py` | CORE |
| 6.18 | OmnixAPIClient | `omnix_dashboard/api_client.py` | `src/omnix/interfaces/streamlit/client.py` | SUPPORT |
| 6.19 | Notifications | `omnix_services/notifications/` | `src/omnix/application/notifications/` | SUPPORT |
| 6.20 | DailySummary | `omnix_services/notifications/` | `src/omnix/application/notifications/daily.py` | SUPPORT |
| 7.1 | DatabasePort | `src/omnix/ports/driven/database_port.py` | `src/omnix/ports/driven/database.py` | CORE |
| 7.2 | DatabaseGateway | `omnix_services/database_service/database_gateway.py` | `src/omnix/infrastructure/adapters/postgres/gateway.py` | CORE |
| 7.3 | CachePort | `src/omnix/ports/driven/cache_port.py` | `src/omnix/ports/driven/cache.py` | CORE |
| 7.4 | RedisCache | `omnix_core/cache/redis_cache.py` | `src/omnix/infrastructure/adapters/redis/cache.py` | CORE |
| 7.5 | Analytics | `omnix_services/analytics/` | `src/omnix/application/analytics/` | CORE |
| 7.6 | InstitutionalMetrics | `omnix_services/analytics/institutional_metrics.py` | `src/omnix/application/analytics/institutional.py` | CORE |
| 7.7 | InstitutionalReport | `omnix_services/analytics/institutional_report.py` | `src/omnix/application/analytics/report.py` | SUPPORT |
| 7.8 | VolumeProfile | `omnix_services/analytics/volume_profile.py` | `src/omnix/application/analytics/volume.py` | SUPPORT |
| 7.9 | FibonacciAnalyzer | `omnix_services/analytics/fibonacci_analyzer.py` | `src/omnix/application/analytics/fibonacci.py` | SUPPORT |
| 7.10 | UserRepository | `omnix_services/database_service/` | `src/omnix/infrastructure/repositories/user.py` | CORE |
| 7.11 | TradeRepository | `omnix_services/database_service/` | `src/omnix/infrastructure/repositories/trade.py` | CORE |
| 7.12 | BalanceRepository | `omnix_services/database_service/` | `src/omnix/infrastructure/repositories/balance.py` | CORE |
| 7.13 | RiskEventRepository | `omnix_services/database_service/` | `src/omnix/infrastructure/repositories/risk_event.py` | CORE |
| 7.14 | DecisionLogRepository | `omnix_services/database_service/` | `src/omnix/infrastructure/repositories/decision_log.py` | CORE |
| 8.1 | PQCSecurity | `omnix_core/security/pqc_security.py` | `src/omnix/infrastructure/security/pqc.py` | CORE |
| 8.2 | Kyber768 | `omnix_core/security/pqc_security.py` | `src/omnix/infrastructure/security/kyber.py` | CORE |
| 8.3 | Dilithium3 | `omnix_core/security/pqc_security.py` | `src/omnix/infrastructure/security/dilithium.py` | CORE |
| 8.4 | QuantumEnhancements | `omnix_core/quantum/enhancements.py` | `src/omnix/infrastructure/quantum/` | SUPPORT |
| 8.5 | QRNG | `omnix_core/quantum/enhancements.py` | `src/omnix/infrastructure/quantum/qrng.py` | SUPPORT |
| 8.6 | QAOA | `omnix_core/quantum/enhancements.py` | `src/omnix/infrastructure/quantum/qaoa.py` | STRATEGIC |
| 9.1 | PortfolioManagement | `omnix_services/portfolio_management/` | `src/omnix/domain/portfolio/` | SUPPORT |
| 9.2 | MarkowitzOptimizer | `omnix_services/portfolio_management/` | `src/omnix/domain/portfolio/markowitz.py` | SUPPORT |
| 9.3 | BlackLittermanOptimizer | `omnix_services/portfolio_management/` | `src/omnix/domain/portfolio/black_litterman.py` | SUPPORT |
| 9.4 | CAESPositionSizing | `omnix_core/strategies/caes_module.py` | `src/omnix/domain/sizing/caes.py` | CORE |
| 10.1 | FeedbackManager | `omnix_services/community_intelligence/feedback_manager.py` | `src/omnix/application/community/feedback.py` | STRATEGIC |
| 10.2 | CommunityAnalyzer | `omnix_services/community_intelligence/community_analyzer.py` | `src/omnix/application/community/analyzer.py` | STRATEGIC |
| 10.3 | RewardSystem | `omnix_services/community_intelligence/reward_system.py` | `src/omnix/application/community/rewards.py` | STRATEGIC |
| 10.4 | CommunityDashboard | `omnix_services/community_intelligence/community_dashboard.py` | `src/omnix/application/community/dashboard.py` | STRATEGIC |
| 10.5 | SignalContribution | `omnix_services/community_intelligence/signal_contribution.py` | `src/omnix/application/community/signals.py` | STRATEGIC |
| 11.1 | TradingProfiles | `omnix_core/config/trading_profiles.py` | `src/omnix/config/profiles.py` | CORE |
| 11.2 | PRODUCTION_STABLE | `omnix_core/config/trading_profiles.py` | `src/omnix/config/profiles/production_stable.py` | CORE |
| 11.3 | INSTITUTIONAL | `omnix_core/config/trading_profiles.py` | `src/omnix/config/profiles/institutional.py` | SUPPORT |
| 11.4 | PAPER_AGGRESSIVE | `omnix_core/config/trading_profiles.py` | `src/omnix/config/profiles/paper_aggressive.py` | SUPPORT |
| 11.5 | PAPER_OPTIMIZED | `omnix_core/config/trading_profiles.py` | `src/omnix/config/profiles/paper_optimized.py` | SUPPORT |
| 11.6 | UserSettingsService | `omnix_services/user_settings/user_settings_service.py` | `src/omnix/application/user_settings/service.py` | CORE |
| 11.7 | SettingsModels | `omnix_services/user_settings/settings_models.py` | `src/omnix/domain/user/settings.py` | CORE |

### ⚪ PLANNED (7 components)

| ID | Name | Legacy Path | V7 Path | Priority |
|-----|------|-------------|---------|----------|
| 3.11 | OrderRouter | - | `src/omnix/domain/execution/router.py` | CORE |
| 6.6 | MarketCommands | - | `src/omnix/interfaces/telegram/handlers/market.py` | CORE |
| 6.7 | TradingCommands | - | `src/omnix/interfaces/telegram/handlers/trading.py` | CORE |
| 6.8 | AnalysisCommands | - | `src/omnix/interfaces/telegram/handlers/analysis.py` | SUPPORT |
| 6.9 | ConfigCommands | - | `src/omnix/interfaces/telegram/handlers/config.py` | SUPPORT |
| 6.10 | CommunityCommands | - | `src/omnix/interfaces/telegram/handlers/community.py` | STRATEGIC |
| 6.11 | QuantumCommands | - | `src/omnix/interfaces/telegram/handlers/quantum.py` | STRATEGIC |

### ✅ FULL (1 components)

| ID | Name | Legacy Path | V7 Path | Priority |
|-----|------|-------------|---------|----------|
| 4.1 | RiskManagement | `omnix_services/risk_management/` | `src/omnix/domain/risk/` | CORE |


---

## Reproducibility

This report was generated by running:

```bash
python scripts/traceability/validate_traceability.py
```

### Validation Commands Used

For each component, the script checks:

1. **File existence**: `test -f <path>` or `test -d <path>`
2. **Directory contents**: `ls <path>/*.py 2>/dev/null | wc -l`

---

*Generated by OMNIX Traceability Validator*  
*2025-12-24 06:29:20*
