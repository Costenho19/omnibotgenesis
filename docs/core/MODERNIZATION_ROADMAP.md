# OMNIX V7.0 Modernization Roadmap

**Version:** 1.0  
**Last Updated:** December 10, 2025  
**Status:** DEFERRED (pending 500+ trades track record)

---

## Executive Summary

This document consolidates all planned refactoring and modernization work for OMNIX V7.0. All work is deferred until the track record milestone is achieved to avoid disrupting trade generation.

**Execution Criteria:**
- [ ] 500+ trades accumulated
- [ ] Win rate stable at 55%+ for 14+ days
- [ ] Full team availability for monitoring

---

## Table of Contents

1. [Architecture Refactoring](#1-architecture-refactoring)
2. [AI Service DI Completion](#2-ai-service-di-completion)
3. [Semantic Router Implementation](#3-semantic-router-implementation)
4. [Rollback Procedures](#4-rollback-procedures)

---

## 1. Architecture Refactoring

### 1.1 Hexagonal Architecture Completion

**Current State:** Phase 1 Complete - 12 protocol interfaces defined  
**Target State:** Full port/adapter separation with dependency injection

| Phase | Scope | Status | Effort |
|-------|-------|--------|--------|
| 1 | Define protocols in `omnix/ports/` | ✅ Complete | 4h |
| 2 | Implement adapters | ⬜ Pending | 8h |
| 3 | Wire DI container | ⬜ Pending | 4h |
| 4 | Migrate consumers | ⬜ Pending | 12h |

### 1.2 Pending Adapter Implementations

| Port | Adapter Needed | Priority |
|------|----------------|----------|
| TradingBotPort | AutoTradingBotAdapter | HIGH |
| UserCommandPort | TelegramCommandAdapter | HIGH |
| WebhookPort | AlertWebhookAdapter | MEDIUM |
| SchedulerPort | APSchedulerAdapter | MEDIUM |
| HealthCheckPort | PrometheusAdapter | LOW |
| ConfigPort | ProfileConfigAdapter | LOW |

### 1.3 Code Quality Targets

| Metric | Current | Target |
|--------|---------|--------|
| ConversationalAIService lines | 371 | <200 |
| Unit test coverage (core) | ~30% | >80% |
| Circular imports | ~5 | 0 |
| Type hint coverage | ~60% | >90% |

---

## 2. AI Service DI Completion

### 2.1 Phase 2: Complete DI Container

**Risk Level:** MEDIUM  
**Estimated Time:** 2-3 hours

| Protocol | Status | Implementation Needed |
|----------|--------|----------------------|
| `AIGatewayProtocol` | ✅ DONE | GeminiProvider, OpenAIProvider, AnthropicProvider |
| `ContextProviderProtocol` | ❌ MISSING | RedisContextProvider |
| `PromptBuilderProtocol` | ❌ MISSING | OmnixPromptBuilder |
| `StyleRendererProtocol` | ❌ MISSING | OmnixStyleRenderer |

**Tasks:**

2.1 Create `RedisContextProvider`:
```
File: omnix_services/ai_service/providers/redis_context_provider.py
Methods: get_conversation_history(), add_message(), get_full_context()
```

2.2 Create `OmnixPromptBuilder`:
```
File: omnix_services/ai_service/providers/omnix_prompt_builder.py
Methods: analyze_intent(), build_system_prompt(), build_user_prompt()
```

2.3 Create `OmnixStyleRenderer`:
```
File: omnix_services/ai_service/providers/omnix_style_renderer.py
Methods: render_response(), format_error()
```

2.4 Update `container.py` with new providers

2.5 Add feature flags (default OFF):
```python
USE_DI_CONTEXT_PROVIDER = False
USE_DI_PROMPT_BUILDER = False
USE_DI_STYLE_RENDERER = False
```

### 2.2 Phase 3: Refactor ConversationalAIService

**Risk Level:** HIGH  
**Estimated Time:** 4-6 hours  
**Dependency:** Phase 2 completed and stable for 7+ days

**Current State:**
```
ConversationalAIService (371 lines)
├── __init__: Initializes 5+ managers directly
├── generate_response: Main entry (complex)
└── Various helper methods
```

**Target State:**
```
ConversationalAIService (150-200 lines)
├── __init__: Receives injected dependencies
├── generate_response: Orchestration only
└── Delegates to: ContextProvider, PromptBuilder, AIGateway, StyleRenderer
```

**Tasks:**

3.1 Create legacy backup: `omnix_services/ai_service/legacy/conversational_ai_service_v1.py`

3.2 Modify constructor to accept injected dependencies

3.3 Refactor `generate_response()` to use injected providers

3.4 Create backward compatibility adapter

3.5 Add master feature flag: `AI_SERVICE_V2_ENABLED = False`

---

## 3. Semantic Router Implementation

### 3.1 Overview

Replace hardcoded intent detection (~60 keywords) with LLM Structured Outputs using Gemini 2.0 Flash.

**Benefits:**
- Eliminates keyword maintenance
- Automatic language detection
- Extensible: New intent = add enum + prompt
- 100% schema compliance

### 3.2 Architecture

**Current Flow:**
```
Message → if/elif keywords → intent string → build_prompt() → LLM
```

**New Flow:**
```
Message → [Fast Path] → Semantic Router (LLM) → Structured Result → Dynamic Prompt → LLM
              ↓
        Direct Execution (commands)
```

### 3.3 Schema Definition

```python
class UserIntent(str, Enum):
    GREETING = "greeting"
    MARKET_ANALYSIS = "market_analysis"
    TRADING_ACTION = "trading_action"
    PRICE_INQUIRY = "price_inquiry"
    PORTFOLIO = "portfolio"
    HELP = "help"
    GENERAL = "general"

class SemanticRouteResult(BaseModel):
    intent: UserIntent
    language: DetectedLanguage  # es, en
    needs_web_search: bool
    confidence: ConfidenceLevel  # high, medium, low
    reasoning: str  # max 100 chars
```

### 3.4 Implementation Files

| File | Purpose |
|------|---------|
| `routing/schemas.py` | Pydantic models with enums |
| `routing/semantic_router.py` | Gemini/OpenAI router |
| `routing/prompts.py` | Intent-specific system prompts |
| `routing/__init__.py` | Public API exports |

### 3.5 Feature Flags

```python
USE_SEMANTIC_ROUTER = False  # Master switch
SEMANTIC_ROUTER_PROVIDER = "gemini"  # or "openai"
SEMANTIC_ROUTER_ROLLOUT_PERCENT = 0  # Gradual rollout
SEMANTIC_ROUTER_FALLBACK_ON_ERROR = True  # Use legacy on failure
```

### 3.6 Rollout Plan

| Stage | Rollout % | Duration | Criteria |
|-------|-----------|----------|----------|
| 1 | 10% | 3 days | No errors, latency OK |
| 2 | 50% | 5 days | User feedback positive |
| 3 | 100% | - | Full production |

---

## 4. Rollback Procedures

### 4.1 AI Service DI Rollback (Phase 2)

**Risk:** LOW - New files only

```bash
git checkout HEAD -- omnix_services/ai_service/container.py
rm -rf omnix_services/ai_service/providers/redis_context_provider.py
rm -rf omnix_services/ai_service/providers/omnix_prompt_builder.py
rm -rf omnix_services/ai_service/providers/omnix_style_renderer.py
```

### 4.2 AI Service V2 Rollback (Phase 3)

**Risk:** MEDIUM - Modified core file

1. Set `AI_SERVICE_V2_ENABLED = False`
2. Restart workflows
3. If needed, restore from legacy backup:
```bash
cp omnix_services/ai_service/legacy/conversational_ai_service_v1.py \
   omnix_services/ai_service/ai_service.py
```

### 4.3 Semantic Router Rollback

**Instant (< 1 minute):**
```python
USE_SEMANTIC_ROUTER = False
```

**Full removal:**
```bash
rm -rf omnix_services/ai_service/routing/
git checkout HEAD -- omnix_services/ai_service/ai_service.py
```

---

## Timeline

| Milestone | Trigger | Work Items |
|-----------|---------|------------|
| Track record: 200 trades | Begin Phase 2 DI | 2.1-2.5 |
| Track record: 400 trades | Begin Phase 3 Refactor | 3.1-3.5 |
| Track record: 500 trades | Begin Semantic Router | Full implementation |
| Win rate 55%+ for 14 days | Production activation | Gradual rollout |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| container.py providers | 3 | 6 |
| ConversationalAIService lines | 371 | <200 |
| Unit test coverage (ai_service/) | ~30% | >80% |
| Response latency P95 | baseline | ±10% |
| Classification accuracy | ~85% | >95% |
| Intent keywords | 60+ | 7 enum values |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 10, 2025 | Consolidated from 3 roadmap documents |
