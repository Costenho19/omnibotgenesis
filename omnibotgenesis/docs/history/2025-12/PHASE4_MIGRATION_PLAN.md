# OMNIX Phase 4: Service Migration to Hexagonal Architecture

**Version:** 1.2  
**Created:** December 13, 2025  
**Last Updated:** December 15, 2025  
**Status:** STAGE 4D IN PROGRESS - TelegramAdapter Complete  
**Estimated Duration:** 2-3 weeks (iterative)

---

## Executive Summary

This document details the migration of `omnix_services/` (24 subdomains, 200+ imports) to the hexagonal architecture in `src/omnix/`. The migration uses the **Strangler Fig Pattern** with dual-stack coexistence, feature flags, and constant architect reviews.

### Key Principles

1. **Zero Downtime:** System remains fully operational throughout migration
2. **Incremental Rollout:** One service family at a time
3. **Instant Rollback:** Feature flags allow immediate reversion
4. **Contract Tests:** Every adapter must pass interface contracts
5. **Architect Reviews:** Every stage requires architect approval

---

## 1. Current State Analysis

### 1.1 omnix_services/ Inventory (24 Subdomains)

| # | Subdomain | Files | Purpose | External APIs | Import Count | Priority |
|---|-----------|-------|---------|---------------|--------------|----------|
| 1 | `telegram_service/` | 5 | Bot interface, commands | Telegram Bot API | HIGH | Stage 4E |
| 2 | `ai_service/` | 20+ | Multi-provider AI (Gemini, OpenAI, Claude) | Gemini, OpenAI, Anthropic | HIGH | Stage 4B |
| 3 | `database_service/` | 6 | PostgreSQL gateway, migrations | PostgreSQL | HIGH | Stage 4C |
| 4 | `trading_service/` | 15+ | Strategies, paper trading, Kraken | Kraken REST/WS | CRITICAL | Stage 4D |
| 5 | `execution_service/` | 5 | 4-layer execution protocol | None (uses kraken) | CRITICAL | Stage 4D |
| 6 | `monitoring/` | 5 | Risk Guardian, metrics | None | MEDIUM | Stage 4A |
| 7 | `risk_management/` | 8 | Circuit breaker, limits | None | CRITICAL | Stage 4D |
| 8 | `market_data/` | 12 | Prices, orderbook, arbitrage | Kraken | HIGH | Stage 4C |
| 9 | `market_intelligence/` | 4 | Fear/Greed, Finnhub, Alpha Vantage | AlphaVantage, Finnhub, Alternative.me | MEDIUM | Stage 4C |
| 10 | `coherence_service/` | 3 | 6-tier veto system | None | HIGH | Stage 4D |
| 11 | `adaptive_engine/` | 2 | Auto-calibration by regime | None | MEDIUM | Stage 4D |
| 12 | `portfolio_management/` | 7 | Institutional optimization | None | MEDIUM | Stage 4D |
| 13 | `notifications/` | 3 | Trade alerts, daily summary | Telegram | LOW | Stage 4A |
| 14 | `analytics/` | 7 | Fibonacci, patterns, metrics | None | LOW | Stage 4A |
| 15 | `stock_trading/` | 8 | Alpaca integration | Alpaca API | MEDIUM | Stage 4D |
| 16 | `derivatives/` | 8 | Kraken Futures, hedging | Kraken Futures API | LOW | Stage 4D |
| 17 | `web_search_service/` | 4 | Tavily search integration | Tavily | MEDIUM | Stage 4B |
| 18 | `voice_service/` | 3 | STT/TTS (Whisper) | OpenAI Whisper | LOW | Stage 4B |
| 19 | `user_settings/` | 3 | Per-user configuration | None | LOW | Stage 4E |
| 20 | `community_intelligence/` | 5 | Social signals (B2C) | None | LOW | Stage 4E |
| 21 | `concurrency/` | 4 | Thread management, cache | Redis | LOW | Stage 4A |
| 22 | `optimization/` | 6 | ML weights, auto-learner | None | LOW | Stage 4D |

### 1.2 src/omnix/ Current State (Hexagonal Target)

```
src/omnix/
├── ports/                    # Protocol interfaces (COMPLETE)
│   ├── driven/               # Output ports (6 defined)
│   │   ├── trading_port.py   # ✅ KrakenAdapter implements
│   │   ├── database_port.py  # ⬜ Pending adapter
│   │   ├── cache_port.py     # ⬜ Pending adapter
│   │   ├── ai_inference_port.py  # ✅ GeminiAdapter implements
│   │   ├── market_data_port.py   # ✅ KrakenAdapter implements
│   │   └── notification_port.py  # ⬜ Pending adapter
│   └── driver/               # Input ports (2 defined)
│       ├── rest_api_port.py  # ⬜ Pending adapter
│       └── telegram_port.py  # ✅ Implemented
│
├── infrastructure/adapters/   # Adapter implementations
│   ├── kraken_adapter.py     # ✅ TradingPort, MarketDataPort
│   ├── gemini_adapter.py     # ✅ AIInferencePort
│   ├── telegram_adapter.py   # ✅ COMPLETE (38 tests)
│   └── ... (3 more needed)
│
├── domain/                   # Business logic (PARTIAL)
│   ├── trading/              # Entities, value objects
│   └── risk/                 # Risk entities
│
├── application/              # Use cases (PARTIAL)
│   ├── trading/              # Execute trade, scan market
│   └── risk/                 # Evaluate risk
│
└── bootstrap/                # DI Container, entry points
    ├── container.py          # ✅ 3 adapters registered
    └── main_entry.py         # ✅ Async bot startup
```

### 1.3 Dependency Graph (Simplified)

```
                    ┌─────────────────────────────────────────┐
                    │           INTERFACES LAYER              │
                    │  telegram_service ←→ omnix_dashboard    │
                    └─────────────────┬───────────────────────┘
                                      │
                    ┌─────────────────▼───────────────────────┐
                    │         APPLICATION LAYER               │
                    │  ai_service, coherence_service          │
                    │  adaptive_engine, notifications         │
                    └─────────────────┬───────────────────────┘
                                      │
    ┌─────────────────────────────────▼─────────────────────────────────┐
    │                      DOMAIN SERVICES LAYER                         │
    │  trading_service, execution_service, risk_management              │
    │  portfolio_management, stock_trading, derivatives                 │
    └─────────────────────────────────┬─────────────────────────────────┘
                                      │
    ┌─────────────────────────────────▼─────────────────────────────────┐
    │                    INFRASTRUCTURE LAYER                            │
    │  database_service, market_data, market_intelligence               │
    │  web_search_service, voice_service, concurrency                   │
    └───────────────────────────────────────────────────────────────────┘
```

---

## 2. Migration Stages

### Stage 1: Inventory & Baseline (Day 1)

**Objective:** Complete audit with verified dependency counts and API documentation.

| Task | Description | Verification |
|------|-------------|--------------|
| 1.1 | Run import scanner on all 24 subdomains | `grep` results documented |
| 1.2 | Document external API usage per service | API table with rate limits |
| 1.3 | Identify circular dependencies | Dependency graph validated |
| 1.4 | Create baseline test suite (smoke tests) | Tests pass on legacy code |

**Architect Review Checkpoint:** Verify inventory accuracy before proceeding.

---

### Stage 2: Ports Alignment (Day 2-3)

**Objective:** Map each service to its hexagonal port(s).

| Service | Target Port(s) | Port Type | Adapter Strategy |
|---------|---------------|-----------|------------------|
| `telegram_service/` | TelegramPort | Driver | ✅ COMPLETE - TelegramBotAdapter |
| `ai_service/` | AIInferencePort | Driven | Already has providers |
| `database_service/` | DatabasePort | Driven | Wrap database_gateway.py |
| `trading_service/` | TradingPort | Driven | Wrap kraken_client.py |
| `market_data/` | MarketDataPort | Driven | Wrap kraken_data.py |
| `notifications/` | NotificationPort | Driven | Wrap telegram_utils.py |
| `web_search_service/` | AIInferencePort (ext) | Driven | New WebSearchPort |
| `risk_management/` | (Internal domain) | N/A | Domain service |

**New Ports Required:**
- `WebSearchPort` - For Tavily integration
- `VoicePort` - For Whisper STT/TTS
- `ExchangePort` - For multi-exchange (Kraken, Alpaca)

**Architect Review Checkpoint:** Approve port mapping before adapter design.

---

### Stage 3: Adapter Design (Day 4-5)

**Objective:** Design adapters with anti-corruption layer and contract tests.

#### 3.1 Adapter Template

```python
# src/omnix/infrastructure/adapters/database_adapter.py
from src.omnix.ports.driven.database_port import DatabasePort
from omnix_services.database_service import database_gateway  # Legacy

class DatabaseAdapter(DatabasePort):
    """Anti-corruption layer wrapping legacy DatabaseGateway."""
    
    def __init__(self):
        self._legacy = database_gateway
    
    async def execute_query(self, query: str, params: dict) -> list:
        # Translate to legacy interface
        return self._legacy.execute(query, params)
    
    async def save_trade(self, trade: Trade) -> str:
        # Convert domain entity to legacy format
        legacy_dict = self._to_legacy_format(trade)
        return self._legacy.insert_trade(legacy_dict)
```

#### 3.2 Contract Tests

```python
# tests/contracts/test_database_port_contract.py
import pytest
from src.omnix.ports.driven.database_port import DatabasePort

class TestDatabasePortContract:
    """All DatabasePort implementations must pass these tests."""
    
    @pytest.fixture
    def adapter(self) -> DatabasePort:
        from src.omnix.infrastructure.adapters import DatabaseAdapter
        return DatabaseAdapter()
    
    async def test_execute_query_returns_list(self, adapter):
        result = await adapter.execute_query("SELECT 1", {})
        assert isinstance(result, list)
    
    async def test_save_trade_returns_id(self, adapter):
        trade = create_test_trade()
        trade_id = await adapter.save_trade(trade)
        assert trade_id is not None
```

**Architect Review Checkpoint:** Approve adapter designs before implementation.

---

### Stage 4: Iterative Service Extraction

#### Stage 4A: Low-Coupling Services (Day 6-7)

| Service | Migration Steps | Feature Flag |
|---------|-----------------|--------------|
| `notifications/` | 1. Create NotificationAdapter<br>2. Register in container<br>3. Update callers to use port | `USE_NOTIFICATION_PORT` |
| `monitoring/` | 1. Create MetricsAdapter<br>2. Keep Risk Guardian in domain | `USE_METRICS_PORT` |
| `analytics/` | 1. Move to domain/analytics<br>2. No port needed (pure logic) | N/A |
| `concurrency/` | 1. Evaluate: merge with CachePort or keep | `USE_CONCURRENCY_PORT` |

**Dual-Write Pattern:**
```python
# During migration, both paths active
if os.getenv("USE_NOTIFICATION_PORT", "false") == "true":
    await container.get(NotificationPort).send_message(msg)
else:
    from omnix_services.notifications import telegram_utils
    telegram_utils.send_message(msg)
```

**Architect Review Checkpoint:** Verify low-coupling migrations before proceeding.

---

#### Stage 4B: AI Services (Day 8-9)

| Service | Migration Steps | SDK Reference |
|---------|-----------------|---------------|
| `ai_service/` | Already SOLID-compliant with DI<br>1. Ensure providers implement AIInferencePort<br>2. Register in main container | [Gemini SDK](https://ai.google.dev/gemini-api/docs)<br>[OpenAI SDK](https://platform.openai.com/docs) |
| `web_search_service/` | 1. Create WebSearchPort<br>2. Create TavilyAdapter<br>3. Inject into ai_service | [Tavily Docs](https://docs.tavily.com) |
| `voice_service/` | 1. Create VoicePort<br>2. Create WhisperAdapter | [Whisper API](https://platform.openai.com/docs/guides/speech-to-text) |

**Provider Fallback Chain:**
```python
# Existing pattern in ai_service - KEEP
providers = [GeminiProvider, OpenAIProvider, AnthropicProvider]
for provider in providers:
    try:
        return await provider.generate(prompt)
    except ProviderError:
        continue
raise AllProvidersFailedError()
```

**Architect Review Checkpoint:** Verify AI provider integration.

---

#### Stage 4C: Data Services (Day 10-11)

| Service | Migration Steps | API Reference |
|---------|-----------------|---------------|
| `database_service/` | 1. DatabaseAdapter wraps gateway<br>2. Register in container<br>3. Use in repositories | psycopg3 docs |
| `market_data/` | 1. MarketDataAdapter (extends KrakenAdapter)<br>2. Add orderbook, arbitrage methods | [Kraken REST](https://docs.kraken.com/rest/) |
| `market_intelligence/` | 1. Create MarketIntelligencePort<br>2. Aggregate: AlphaVantage, Finnhub, Fear/Greed | [Finnhub](https://finnhub.io/docs/api), [AlphaVantage](https://www.alphavantage.co/documentation/) |

**Architect Review Checkpoint:** Verify data layer adapters.

---

#### Stage 4D: Critical Trading Services (Day 12-14)

**CAUTION:** These services are production-critical. Dual-write is MANDATORY.

| Service | Migration Steps | Rollback Plan |
|---------|-----------------|---------------|
| `trading_service/` | 1. TradingAdapter already exists<br>2. Migrate strategies to domain<br>3. Dual-write all orders | Feature flag instant rollback |
| `execution_service/` | 1. Wrap in ExecutionAdapter<br>2. Keep 4-layer protocol intact | Log both paths, compare |
| `risk_management/` | 1. Move to domain/risk<br>2. Keep circuit breaker as-is | Never disable risk checks |
| `coherence_service/` | 1. Move to domain/trading<br>2. Pure logic, no adapter needed | N/A |
| `portfolio_management/` | 1. Move to domain/portfolio | N/A |

**Dual-Write for Orders:**
```python
async def execute_order(order: Order):
    # ALWAYS log both paths during migration
    legacy_result = await legacy_execute(order)
    
    if os.getenv("USE_TRADING_PORT", "false") == "true":
        port_result = await container.get(TradingPort).execute_order(order)
        # Compare results, alert if mismatch
        if legacy_result != port_result:
            alert_mismatch(legacy_result, port_result)
        return port_result
    
    return legacy_result
```

**Architect Review Checkpoint:** CRITICAL - Full review before any trading changes.

---

#### Stage 4E: User Interfaces (Day 15-16)

| Service | Migration Steps | Notes |
|---------|-----------------|-------|
| `telegram_service/` | 1. Create TelegramAdapter (driver port)<br>2. enterprise_bot.py delegates to use cases<br>3. Keep async polling as-is | [python-telegram-bot v20+](https://docs.python-telegram-bot.org/) |
| `user_settings/` | 1. Move to domain/user | Simple migration |
| `community_intelligence/` | 1. Evaluate B2C roadmap<br>2. Keep or deprecate | Business decision |

**Architect Review Checkpoint:** Verify interface layer integration.

---

### Stage 5: Validation (Day 17-18)

| Test Type | Tool | Scope |
|-----------|------|-------|
| Contract Tests | pytest | All adapters implement ports |
| Integration Tests | pytest + testcontainers | DB, Redis, APIs |
| Load Tests | locust | 100 concurrent users |
| Canary Deploy | Railway | 10% traffic to new stack |
| Security Review | Architect | API keys, secrets handling |

**Canary Deployment:**
```yaml
# Railway environment
CANARY_PERCENTAGE: "10"
USE_APP_LAYER: "true"  # Enable hexagonal for canary
```

**Architect Review Checkpoint:** Full system validation before decommission.

---

### Stage 6: Decommission (Day 19-20)

**Only after 100% traffic on new stack for 48 hours:**

| Step | Action | Verification |
|------|--------|--------------|
| 6.1 | Remove feature flags | All `USE_*_PORT` flags |
| 6.2 | Delete legacy wrapper calls | No dual-write code |
| 6.3 | Archive omnix_services/ | Move to docs/history/legacy/ |
| 6.4 | Update all imports | `src.omnix` only |
| 6.5 | Update documentation | ARCHITECTURE.md, replit.md |

**Architect Review Checkpoint:** Final approval for legacy removal.

---

## 3. Feature Flags Reference

| Flag | Default | Purpose |
|------|---------|---------|
| `USE_APP_LAYER` | `false` | Master switch for hexagonal |
| `USE_TRADING_PORT` | `false` | TradingPort for orders |
| `USE_DATABASE_PORT` | `false` | DatabasePort for queries |
| `USE_NOTIFICATION_PORT` | `false` | NotificationPort for alerts |
| `USE_AI_PORT` | `false` | AIInferencePort for LLM |
| `USE_MARKET_DATA_PORT` | `false` | MarketDataPort for prices |
| `CANARY_PERCENTAGE` | `0` | % of traffic to new stack |

---

## 4. Rollback Procedures

### Instant Rollback (< 1 minute)
```bash
# Railway: Set feature flag
railway variables set USE_APP_LAYER=false
railway redeploy
```

### Full Rollback (if adapters corrupted)
1. Revert to last known good commit
2. Redeploy from main branch
3. Restore database from backup if needed

---

## 5. Documentation Updates Required

| Document | Updates Needed |
|----------|----------------|
| `docs/current/ARCHITECTURE.md` | Add Phase 4 adapter mapping |
| `docs/current/TECHNICAL_DEBT.md` | Track dual-stack state |
| `replit.md` | Update service locations |
| `docs/transformation/adr/` | ADR for each major decision |

---

## 6. Success Criteria

| Metric | Target |
|--------|--------|
| All contract tests pass | 100% |
| Integration tests pass | 100% |
| Zero production incidents | 0 |
| Load test: 100 users | < 500ms p99 |
| Feature parity verified | 100% |
| Documentation updated | 100% |

---

## 7. Timeline Summary

| Week | Stages | Deliverables |
|------|--------|--------------|
| Week 1 | 1, 2, 3 | Inventory, port mapping, adapter designs |
| Week 2 | 4A, 4B, 4C | Low-coupling, AI, data services migrated |
| Week 3 | 4D, 4E, 5, 6 | Critical trading, interfaces, validation, decommission |

---

## 8. Reference Documentation

### Official SDK Documentation

| Service | Official Docs | Version |
|---------|---------------|---------|
| python-telegram-bot | https://docs.python-telegram-bot.org/ | v20+ (async native) |
| Google Gemini | https://ai.google.dev/gemini-api/docs | 2.0 Flash |
| OpenAI | https://platform.openai.com/docs | GPT-4o |
| Anthropic Claude | https://docs.anthropic.com/ | Claude 3 |
| Kraken REST | https://docs.kraken.com/rest/ | v0 |
| Kraken WebSocket | https://docs.kraken.com/websockets/ | v2 |
| Alpaca | https://alpaca.markets/docs/api-documentation/ | v2 |
| Tavily | https://docs.tavily.com/ | v1 |
| psycopg3 | https://www.psycopg.org/psycopg3/docs/ | v3 |
| Redis | https://redis.io/docs/ | v7 |

### Internal Documentation

| Document | Purpose |
|----------|---------|
| `docs/current/ARCHITECTURE.md` | Module catalog, domain map |
| `docs/current/TECHNICAL_DEBT.md` | Known issues registry |
| `docs/current/FOLDER_AUDIT_PHASE6.md` | Phase 6 cleanup record |
| `src/omnix/ports/` | Port protocol definitions |

---

## 9. Trading Reconciliation & Shadow Testing (CRITICAL)

### 9.1 Idempotent Order Envelope

Every order must have a unique idempotent key to prevent duplicate executions:

```python
@dataclass
class OrderEnvelope:
    idempotency_key: str  # UUID v4
    order: Order
    timestamp: datetime
    source: str  # "legacy" or "hexagonal"
    
    @classmethod
    def create(cls, order: Order, source: str) -> "OrderEnvelope":
        return cls(
            idempotency_key=str(uuid.uuid4()),
            order=order,
            timestamp=datetime.utcnow(),
            source=source
        )
```

### 9.2 Shadow Traffic Pattern

During Stage 4D, ALL orders execute through both paths but only legacy commits:

```python
async def execute_order_with_shadow(order: Order) -> OrderResult:
    envelope = OrderEnvelope.create(order, "dual")
    
    # LEGACY: Actually executes
    legacy_result = await legacy_execute(envelope)
    
    # HEXAGONAL: Shadow mode (DRY RUN)
    try:
        hex_result = await hexagonal_execute(envelope, dry_run=True)
        
        # Compare results
        await reconciliation_service.compare(
            envelope.idempotency_key,
            legacy_result,
            hex_result
        )
    except Exception as e:
        logger.error(f"Shadow execution failed: {e}")
        # Never affects legacy path
    
    return legacy_result  # Always return legacy during shadow
```

### 9.3 Reconciliation Dashboard

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Result Mismatch Rate | < 0.1% | Telegram + PagerDuty |
| Shadow Execution Failures | < 1% | Telegram |
| Latency Difference (hex - legacy) | < 100ms p99 | Dashboard |
| Order ID Parity | 100% | CRITICAL - halt migration |

### 9.4 Parity Verification Checklist

Before switching traffic to hexagonal:

- [ ] 1000+ shadow orders with 0 mismatches
- [ ] p99 latency within 10% of legacy
- [ ] All order states match (filled, partial, cancelled)
- [ ] Balance calculations identical
- [ ] Risk checks produce same decisions
- [ ] Architect sign-off on reconciliation report

---

## 10. Complete Feature Flag Matrix

### 10.1 Master Flags

| Flag | Default | Scope | Rollback Time |
|------|---------|-------|---------------|
| `USE_APP_LAYER` | `false` | Global hexagonal switch | < 1 min |
| `CANARY_PERCENTAGE` | `0` | % traffic to hexagonal | < 1 min |
| `SHADOW_MODE_ENABLED` | `true` | Enable shadow execution | < 1 min |

### 10.2 Adapter-Level Flags

| Flag | Default | Service | Stage |
|------|---------|---------|-------|
| `USE_NOTIFICATION_PORT` | `false` | notifications/ | 4A |
| `USE_MONITORING_PORT` | `false` | monitoring/ | 4A |
| `USE_ANALYTICS_PORT` | `false` | analytics/ | 4A |
| `USE_CONCURRENCY_PORT` | `false` | concurrency/ | 4A |
| `USE_AI_PORT` | `false` | ai_service/ | 4B |
| `USE_WEBSEARCH_PORT` | `false` | web_search_service/ | 4B |
| `USE_VOICE_PORT` | `false` | voice_service/ | 4B |
| `USE_DATABASE_PORT` | `false` | database_service/ | 4C |
| `USE_MARKET_DATA_PORT` | `false` | market_data/ | 4C |
| `USE_MARKET_INTEL_PORT` | `false` | market_intelligence/ | 4C |
| `USE_TRADING_PORT` | `false` | trading_service/ | 4D |
| `USE_EXECUTION_PORT` | `false` | execution_service/ | 4D |
| `USE_RISK_PORT` | `false` | risk_management/ | 4D |
| `USE_COHERENCE_PORT` | `false` | coherence_service/ | 4D |
| `USE_PORTFOLIO_PORT` | `false` | portfolio_management/ | 4D |
| `USE_STOCK_PORT` | `false` | stock_trading/ | 4D |
| `USE_DERIVATIVES_PORT` | `false` | derivatives/ | 4D |
| `USE_TELEGRAM_PORT` | `false` | telegram_service/ | 4E |
| `USE_USER_SETTINGS_PORT` | `false` | user_settings/ | 4E |

### 10.3 Rollback Scripts

```bash
# Instant rollback - all services
railway variables set USE_APP_LAYER=false
railway redeploy

# Rollback single service (example: trading)
railway variables set USE_TRADING_PORT=false
railway redeploy

# Emergency halt - disable all new code
railway variables set USE_APP_LAYER=false SHADOW_MODE_ENABLED=false CANARY_PERCENTAGE=0
railway redeploy
```

---

## 11. Observability & Incident Response

### 11.1 Required Metrics

| Category | Metric | Source | Dashboard |
|----------|--------|--------|-----------|
| **Latency** | Order execution p50/p95/p99 | Both paths | Grafana |
| **Errors** | Exception rate by adapter | Logs | Grafana |
| **Parity** | Legacy vs Hex result match % | Reconciliation | Custom |
| **Traffic** | Requests per adapter | Metrics | Grafana |
| **Health** | Adapter health check status | /health | Railway |

### 11.2 Alert Thresholds

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Mismatch Detected | Any order result differs | CRITICAL | Halt migration, investigate |
| Hex Latency Spike | p99 > legacy + 200ms | HIGH | Review adapter, consider rollback |
| Shadow Failure Rate | > 5% | HIGH | Check logs, fix or rollback |
| Adapter Health Down | Health check fails 3x | CRITICAL | Auto-rollback via flag |
| Error Rate Spike | > 1% errors | MEDIUM | Alert on-call |

### 11.3 Live Health Checks

```python
# Add to each adapter
class TradingAdapter(TradingPort):
    async def health_check(self) -> HealthStatus:
        try:
            # Test connection to Kraken
            await self.get_balance("USD")
            return HealthStatus(healthy=True, latency_ms=elapsed)
        except Exception as e:
            return HealthStatus(healthy=False, error=str(e))
```

### 11.4 Incident Response Runbook

**Scenario: Order Mismatch Detected**

1. **Immediate (< 1 min):**
   - Check if real money affected (paper trading = lower urgency)
   - If real money: Set `USE_TRADING_PORT=false`, redeploy

2. **Investigation (< 15 min):**
   - Pull reconciliation logs for idempotency_key
   - Compare legacy vs hex order details
   - Identify divergence point

3. **Resolution:**
   - Fix adapter logic
   - Add regression test
   - Resume shadow testing
   - Require 500+ orders without mismatch before re-enabling

**Scenario: Hexagonal Path Down**

1. **Automatic:** Feature flag defaults to legacy
2. **Manual:** Verify legacy path healthy
3. **Post-incident:** Root cause analysis, improve resilience

### 11.5 On-Call Checklist

- [ ] Railway dashboard access
- [ ] Telegram alert channel
- [ ] Rollback scripts documented
- [ ] Database backup verified
- [ ] Contact list for escalation

---

## 12. Architect Review Gates

| Gate | Stage | Required Approvals | Criteria |
|------|-------|-------------------|----------|
| G1 | After Stage 1 | Inventory accuracy | All services catalogued |
| G2 | After Stage 2 | Port mapping complete | Every service has target port |
| G3 | After Stage 3 | Adapter designs approved | Contract tests defined |
| G4A | After Stage 4A | Low-coupling verified | Tests pass, no incidents |
| G4B | After Stage 4B | AI services verified | Provider fallback works |
| G4C | After Stage 4C | Data services verified | Query parity confirmed |
| G4D | After Stage 4D | CRITICAL GATE | 1000+ shadow orders, 0 mismatches |
| G4E | After Stage 4E | Interface layer verified | Telegram commands work |
| G5 | After Stage 5 | Full validation | All tests pass, canary stable |
| G6 | Before decommission | Legacy removal approved | 48h stable on hex only |

---

*Document Author: OMNIX Migration Team*  
*Last Updated: December 13, 2025*  
*Architect Review: v1 - Added reconciliation, flags, observability*  
*Status: READY FOR EXECUTION*
