# OMNIX V7.0 - Plan de Reescritura Limpia

**Fecha**: 15 de Diciembre 2025  
**Estado**: PROPUESTO  
**Enfoque**: Reescritura desde cero (NO wrapping de legacy)

---

## Resumen Ejecutivo

Este plan establece 6 fases para reescribir OMNIX completamente usando arquitectura hexagonal moderna, manteniendo el sistema legacy corriendo 24/7 en Railway durante la migración.

**Esfuerzo estimado**: 49-68 días de desarrollo (~10-14 semanas)

---

## Mapa de Dependencias

```
┌─────────────────────────────────────────────────────────────────┐
│  FASE 6: Interfaces & Orchestration                             │
│  (AutoTradingBot, EnterpriseBot, Dashboards, APIs)              │
│      ↑ depende de todas las capas anteriores                    │
├─────────────────────────────────────────────────────────────────┤
│  FASE 5: Execution & Brokerage                                  │
│  (Order routing, paper/live brokers, derivatives)               │
│      ↑ depende de señales + risk                                │
├─────────────────────────────────────────────────────────────────┤
│  FASE 4: Trading Signal Fabric                                  │
│  (10 strategies, coherence engine, CAES/ARES)                   │
│      ↑ depende de data + risk                                   │
├─────────────────────────────────────────────────────────────────┤
│  FASE 3: Risk & Analytics                                       │
│  (Risk Guardian, circuit breakers, monitoring)                  │
│      ↑ depende de data/persistence                              │
├─────────────────────────────────────────────────────────────────┤
│  FASE 2: Data & Persistence                                     │
│  (Market ingestion, repositories, Redis/Postgres)               │
│      ↑ depende de platform foundations                          │
├─────────────────────────────────────────────────────────────────┤
│  FASE 1: Platform Foundations                                   │
│  (Config, DI container, logging, shared DTOs)                   │
│      ↑ sin dependencias                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Evaluación de Complejidad por Dominio

| Dominio | Complejidad | Razón |
|---------|-------------|-------|
| Platform Foundations | MEDIA | Pydantic config + observability + port wiring |
| Data & Persistence | ALTA | Kraken REST/WS, AlphaVantage, Finnhub, Tavily, Redis/Postgres |
| Risk & Analytics | MEDIA-ALTA | Multi-layer protections, circuit breakers, monitoring |
| Trading Signal Fabric | ALTA | 10 core strategies, 6-tier coherence, QRNG |
| Execution & Brokerage | MUY ALTA | 4-layer protocol, multi-exchange, derivatives, paper/live parity |
| Interfaces & Orchestration | MUY ALTA | 40+ Telegram commands, dual dashboards, AI integrations |

---

## FASE 1: Platform Foundations

**Duración**: 5-7 días  
**Complejidad**: MEDIA  
**Riesgo**: BAJO

### Entregables

| Componente | Descripción | Ubicación Nueva |
|------------|-------------|-----------------|
| Config Service | Pydantic settings centralizado | `src/omnix/config/settings.py` |
| DI Container | Dependency injection | `src/omnix/bootstrap/container.py` |
| Event Bus | Logging y eventos estructurados | `src/omnix/infrastructure/events/` |
| Shared DTOs | Value objects, entities base | `src/omnix/domain/shared/` |
| Re-exports | Compatibilidad legacy | `omnix_core/__init__.py` |

### Tareas

1. Crear estructura de carpetas `src/omnix/` completa
2. Implementar Pydantic BaseSettings para todas las env vars
3. Crear DI Container con injection automático
4. Definir interfaces base (Entity, ValueObject, Result)
5. Establecer logging estructurado (JSON format)
6. Crear re-exports para imports legacy

### Validación

- Unit tests del container
- Smoke test de bootstrap
- Verificar que legacy sigue funcionando

### Rollback

- Toggle entre legacy y nuevo bootstrap path
- Feature flag: `USE_NEW_BOOTSTRAP=false`

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Env mismatch Railway | Blue/green deploy |
| Circular imports | Import linter en CI |

---

## FASE 2: Data & Persistence

**Duración**: 7-10 días  
**Complejidad**: ALTA  
**Riesgo**: MEDIO

### Entregables

| Componente | APIs Externas | Ubicación Nueva |
|------------|---------------|-----------------|
| MarketDataPort | Kraken REST/WS, CoinGecko | `src/omnix/ports/driven/market_data.py` |
| KrakenAdapter | Kraken API | `src/omnix/infrastructure/adapters/kraken/` |
| DatabasePort | PostgreSQL | `src/omnix/ports/driven/database.py` |
| DatabaseAdapter | psycopg3 | `src/omnix/infrastructure/adapters/postgres/` |
| CachePort | Redis | `src/omnix/ports/driven/cache.py` |
| CacheAdapter | Redis | `src/omnix/infrastructure/adapters/redis/` |
| ExternalDataPort | AlphaVantage, Finnhub, Tavily | `src/omnix/ports/driven/external_data.py` |

### Tareas

1. Definir protocol interfaces para cada port
2. Implementar KrakenAdapter (REST + WebSocket)
3. Implementar PostgresAdapter con connection pooling
4. Implementar RedisAdapter con TTL management
5. Crear ExternalDataAdapter para APIs de mercado
6. Ejecutar shadow pipeline (persistir en schemas paralelos)
7. Reconciliar datos legacy vs nuevo

### Validación

- Shadow pipelines comparando output
- Fixtures grabados para replay
- Reconciliación de datos

### Rollback

- Feature flag para flipear a legacy clients
- `USE_NEW_DATA_LAYER=false`

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| API throttling | Circuit breakers + recorded fixtures |
| Data inconsistency | Schema paralelo + reconciliación |

---

## FASE 3: Risk & Analytics

**Duración**: 5-7 días  
**Complejidad**: MEDIA-ALTA  
**Riesgo**: MEDIO

### Entregables

| Componente | Descripción | Ubicación Nueva |
|------------|-------------|-----------------|
| RiskService | Risk Guardian V5.4 reescrito | `src/omnix/domain/risk/` |
| CircuitBreaker | 5 capas de protección | `src/omnix/domain/risk/circuit_breaker.py` |
| MonitoringService | Métricas y observabilidad | `src/omnix/application/monitoring/` |
| AdaptiveEngine | Auto-calibración | `src/omnix/domain/risk/adaptive/` |
| OptimizationService | ML weights | `src/omnix/domain/optimization/` |

### Tareas

1. Modelar entidades de dominio (RiskEvent, CircuitState, etc.)
2. Implementar RiskGuardian como domain service
3. Implementar CircuitBreaker con 5 capas
4. Implementar MonitoringService sobre nuevos repositories
5. Crear AdaptiveEngine con calibración por régimen
6. Validar con historical replay

### Validación

- Historical replay de trades pasados
- Chaos scripts para circuit breakers
- Comparación de métricas legacy vs nuevo

### Rollback

- Routing a legacy risk services
- `USE_NEW_RISK_LAYER=false`

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Reglas de riesgo incorrectas | Historical replay |
| Circuit breaker triggers falsos | Chaos testing |

---

## FASE 4: Trading Signal Fabric

**Duración**: 10-14 días  
**Complejidad**: ALTA  
**Riesgo**: ALTO

### Entregables

| Componente | Descripción | Ubicación Nueva |
|------------|-------------|-----------------|
| QuantumMomentumStrategy | 6-componentes | `src/omnix/domain/strategies/quantum_momentum.py` |
| MonteCarloStrategy | 10k simulations + QRNG | `src/omnix/domain/strategies/monte_carlo.py` |
| KellyStrategy | Position sizing | `src/omnix/domain/strategies/kelly.py` |
| BlackSwanStrategy | Veto power | `src/omnix/domain/strategies/black_swan.py` |
| HMMRegimeStrategy | Market state detection | `src/omnix/domain/strategies/hmm_regime.py` |
| KalmanStrategy | Signal filtering | `src/omnix/domain/strategies/kalman.py` |
| CoherenceEngine | 6-tier veto system | `src/omnix/domain/coherence/engine.py` |
| CAESModule | Dynamic position sizing | `src/omnix/domain/sizing/caes.py` |
| ARESStrategies | V1 (Swing) + V2 (Scalping) | `src/omnix/domain/strategies/ares/` |
| NonMarkovianKernel | Temporal memory | `src/omnix/domain/strategies/non_markovian.py` |

### Tareas

1. Definir Strategy protocol interface
2. Implementar cada estrategia como domain service
3. Implementar CoherenceEngine con 6 tiers
4. Implementar CAES position sizing
5. Implementar ARES V1 y V2
6. Implementar Non-Markovian Kernel
7. Ejecutar shadow signal generation
8. Comparar señales legacy vs nuevo (divergencia <1%)

### Validación

- Shadow signal generation
- Comparación con señales históricas
- Divergencia máxima <1%

### Rollback

- Switch signal provider binding
- `USE_NEW_SIGNALS=false`

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Señales diferentes | Shadow comparison |
| Performance degradation | Profiling continuo |

---

## FASE 5: Execution & Brokerage

**Duración**: 12-16 días  
**Complejidad**: MUY ALTA  
**Riesgo**: MUY ALTO

### Entregables

| Componente | Descripción | Ubicación Nueva |
|------------|-------------|-----------------|
| ExecutionProtocol | 4 capas institucionales | `src/omnix/domain/execution/protocol.py` |
| OrderRouter | Multi-exchange routing | `src/omnix/domain/execution/router.py` |
| PaperTradingService | Simulación completa | `src/omnix/application/paper_trading/` |
| LiveTradingService | Ejecución real | `src/omnix/application/live_trading/` |
| KrakenBroker | Spot trading | `src/omnix/infrastructure/brokers/kraken/` |
| AlpacaBroker | Stock trading | `src/omnix/infrastructure/brokers/alpaca/` |
| DerivativesBroker | Futures/margin | `src/omnix/infrastructure/brokers/derivatives/` |
| PositionManager | Gestión de posiciones | `src/omnix/domain/execution/positions.py` |

### Tareas

1. Definir TradingPort y BrokerPort protocols
2. Implementar ExecutionProtocol con 4 capas
3. Implementar OrderRouter con multi-exchange support
4. Implementar PaperTradingService con ledger completo
5. Implementar LiveTradingService
6. Implementar KrakenBroker adapter
7. Implementar AlpacaBroker adapter
8. Implementar DerivativesBroker
9. Validar con sandbox exchanges
10. Paper trading ledger diff

### Validación

- Sandbox exchange testing
- Paper trading ledger comparison
- Staged rollout: paper → fractional live

### Rollback

- Broker adapter toggle
- `USE_NEW_EXECUTION=false`

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Órdenes incorrectas | Sandbox testing extensivo |
| Pérdida de dinero | Paper first, luego fractional |
| Race conditions | Locks + idempotency keys |

---

## FASE 6: Interfaces & Orchestration

**Duración**: 10-14 días  
**Complejidad**: MUY ALTA  
**Riesgo**: ALTO

### Entregables

| Componente | Descripción | Ubicación Nueva |
|------------|-------------|-----------------|
| AutoTradingBotService | Bot principal reescrito | `src/omnix/application/trading/auto_trading_bot.py` |
| TelegramAdapter | Bot Telegram | `src/omnix/interfaces/telegram/` |
| CommandHandlers | 40+ handlers modulares | `src/omnix/interfaces/telegram/handlers/` |
| FlaskAPIAdapter | REST API | `src/omnix/interfaces/rest/` |
| StreamlitAdapter | Dashboard interactivo | `src/omnix/interfaces/streamlit/` |
| AIOrchestrator | Multi-provider AI | `src/omnix/application/ai/` |
| NotificationService | Alertas y resúmenes | `src/omnix/application/notifications/` |
| VoiceService | STT/TTS | `src/omnix/application/voice/` |

### Tareas

1. Crear TelegramPort driver interface
2. Dividir EnterpriseBot en command handlers modulares
3. Implementar AutoTradingBotService sobre nuevas capas
4. Implementar FlaskAPIAdapter
5. Implementar StreamlitAdapter
6. Implementar AIOrchestrator con providers
7. Implementar NotificationService
8. Migrar comandos gradualmente con command multiplexer
9. End-to-end rehearsal
10. Investor dashboard parity check

### Validación

- End-to-end rehearsal
- Command multiplexer (legacy + nuevo en paralelo)
- Dashboard parity check

### Rollback

- Command routing a legacy services
- `USE_NEW_INTERFACES=false`

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Comandos rotos | Command multiplexer gradual |
| UX diferente | A/B testing con usuarios beta |

---

## Safeguards Cross-Fase

| Medida | Propósito |
|--------|-----------|
| Telemetry paralela | Comparar legacy vs nuevo |
| Nightly regression suites | Detectar regresiones |
| Feature flags por fase | Rollback instantáneo |
| Blue/green Railway deploy | Zero downtime |
| Documentación actualizada | Onboarding futuro |

---

## Timeline Resumido

| Fase | Duración | Acumulado |
|------|----------|-----------|
| 1. Platform Foundations | 5-7 días | Semana 1 |
| 2. Data & Persistence | 7-10 días | Semanas 2-3 |
| 3. Risk & Analytics | 5-7 días | Semana 4 |
| 4. Trading Signal Fabric | 10-14 días | Semanas 5-6 |
| 5. Execution & Brokerage | 12-16 días | Semanas 7-9 |
| 6. Interfaces & Orchestration | 10-14 días | Semanas 10-12 |
| **TOTAL** | **49-68 días** | **10-14 semanas** |

---

## Próximos Pasos

1. **Aprobar Fase 1**: Definir scope exacto y crear environment shadow en Railway
2. **Contract-first schemas**: Definir DTOs para market data, trades, risk events
3. **Comparison harness**: Crear herramienta automatizada para comparar señales/trades/métricas

---

*Plan creado: 15 de Diciembre 2025*  
*Basado en análisis de COMPLETE_FUNCTIONALITY_MAP.md*
