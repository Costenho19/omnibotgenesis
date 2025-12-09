# AI Service Refactoring Roadmap

**Document Version:** 1.0  
**Created:** December 9, 2025  
**Status:** DEFERRED (pending track record completion)  
**Author:** OMNIX Development Team

---

## Executive Summary

This document outlines the planned refactoring of the AI Service module to complete SOLID principles implementation and fully utilize the Dependency Injection container. The work is split into two phases with clear risk assessments and rollback procedures.

**Current State:** DI container partially implemented (3 AI providers registered)  
**Target State:** Full DI with all protocols implemented and registered

**CRITICAL:** Do not execute until 500+ trades accumulated with stable win rate.

---

## Phase 2: Complete DI Container

**Risk Level:** MEDIUM  
**Estimated Time:** 2-3 hours  
**Dependencies:** None (new code, no modifications to existing)

### Objective

Create concrete implementations of all defined protocols and register them in the DI container.

### Current Gap Analysis

| Protocol | Lines | Status | Implementation Needed |
|----------|-------|--------|----------------------|
| `AIGatewayProtocol` | 50 | ✅ DONE | GeminiProvider, OpenAIProvider, AnthropicProvider |
| `ContextProviderProtocol` | 88 | ❌ MISSING | RedisContextProvider |
| `PromptBuilderProtocol` | 81 | ❌ MISSING | OmnixPromptBuilder |
| `StyleRendererProtocol` | ~60 | ❌ MISSING | OmnixStyleRenderer |

### Tasks

#### 2.1 Create RedisContextProvider

**File:** `omnix_services/ai_service/providers/redis_context_provider.py`

**Purpose:** Implement ContextProviderProtocol using existing Redis/PostgreSQL infrastructure.

```python
class RedisContextProvider:
    """
    Concrete implementation of ContextProviderProtocol.
    Uses Redis for fast access, PostgreSQL for persistence.
    """
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[ConversationMessage]:
        # Delegate to omnix_core.cache.redis_state.get_conversation_history
        pass
    
    def add_message(self, user_id: str, message: ConversationMessage) -> None:
        # Store in Redis with TTL, persist to PostgreSQL
        pass
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        # Delegate to existing user_preferences store
        pass
    
    def get_market_context(self) -> Dict[str, Any]:
        # Aggregate from RealContextProvider
        pass
    
    def get_full_context(self, user_id: str) -> ConversationContext:
        # Combine all context sources
        pass
```

**Integration Points:**
- `omnix_core.cache.redis_state.get_conversation_history()`
- `omnix_core.cache.redis_state.get_user_preferences()`
- `omnix_core.cache.redis_state.get_market_context()`
- `omnix_core.context.get_real_context_provider()`

---

#### 2.2 Create OmnixPromptBuilder

**File:** `omnix_services/ai_service/providers/omnix_prompt_builder.py`

**Purpose:** Implement PromptBuilderProtocol extracting logic from ai_prompts.py.

```python
class OmnixPromptBuilder:
    """
    Concrete implementation of PromptBuilderProtocol.
    Handles intent detection and prompt construction.
    """
    
    def __init__(self, prompts_manager: PromptsContextManager):
        self.prompts_manager = prompts_manager
    
    def analyze_intent(self, message: str) -> UserIntent:
        # Extract from current _detect_intent logic
        pass
    
    def build_system_prompt(self, context: PromptContext) -> str:
        # Delegate to prompts_manager.get_system_prompt()
        pass
    
    def build_user_prompt(self, context: PromptContext) -> str:
        # Format user message with context
        pass
    
    def get_intent_specific_instructions(self, intent: UserIntent) -> str:
        # Return specialized instructions per intent
        pass
```

**Integration Points:**
- `omnix_services.ai_service.ai_prompts.PromptsContextManager`
- Quantum Physics Validator integration (optional import pattern)

---

#### 2.3 Create OmnixStyleRenderer

**File:** `omnix_services/ai_service/providers/omnix_style_renderer.py`

**Purpose:** Implement StyleRendererProtocol extracting logic from ai_styles.py.

```python
class OmnixStyleRenderer:
    """
    Concrete implementation of StyleRendererProtocol.
    Handles response formatting and visual styling.
    """
    
    def __init__(self, styles_manager: VisualStylesManager):
        self.styles_manager = styles_manager
    
    def render_response(self, content: str, style: str = "default") -> str:
        # Apply visual formatting
        pass
    
    def format_error(self, error: Exception, user_friendly: bool = True) -> str:
        # Format errors for user display
        pass
```

**Integration Points:**
- `omnix_services.ai_service.ai_styles.VisualStylesManager`

---

#### 2.4 Update container.py

**Required Imports (add at top of container.py):**

```python
from .providers.redis_context_provider import RedisContextProvider
from .providers.omnix_prompt_builder import OmnixPromptBuilder
from .providers.omnix_style_renderer import OmnixStyleRenderer
from .ai_prompts import PromptsContextManager
from .ai_styles import VisualStylesManager
```

**Additions to AIServiceContainer:**

```python
class AIServiceContainer(containers.DeclarativeContainer):
    # ... existing providers ...
    
    # NEW: Context Provider
    context_provider = providers.Singleton(
        RedisContextProvider,
    )
    
    # NEW: Prompt Builder (requires PromptsContextManager)
    prompts_manager = providers.Singleton(PromptsContextManager)
    
    prompt_builder = providers.Singleton(
        OmnixPromptBuilder,
        prompts_manager=prompts_manager,
    )
    
    # NEW: Style Renderer (requires VisualStylesManager)
    styles_manager = providers.Singleton(VisualStylesManager)
    
    style_renderer = providers.Singleton(
        OmnixStyleRenderer,
        styles_manager=styles_manager,
    )
```

---

#### 2.5 Feature Flag Implementation

**File:** `omnix_config/settings.py`

```python
# AI Service DI Feature Flags
USE_DI_CONTEXT_PROVIDER: bool = False  # Default OFF
USE_DI_PROMPT_BUILDER: bool = False    # Default OFF
USE_DI_STYLE_RENDERER: bool = False    # Default OFF
```

**Usage Pattern:**
```python
if settings.USE_DI_CONTEXT_PROVIDER:
    context_provider = container.context_provider()
else:
    context_provider = LegacyContextAdapter()  # Existing behavior
```

---

### Phase 2 Verification Checklist

- [ ] All new files pass linting (ruff)
- [ ] All new classes have docstrings
- [ ] Unit tests created for each provider
- [ ] Feature flags default to OFF
- [ ] Container initializes without errors
- [ ] Legacy behavior unchanged when flags OFF
- [ ] Integration tests pass with flags ON (sandbox only)

---

## Phase 3: Refactor ConversationalAIService

**Risk Level:** HIGH  
**Estimated Time:** 4-6 hours  
**Dependencies:** Phase 2 completed and tested

### Objective

Reduce ConversationalAIService responsibilities by delegating to injected providers.

### Current State

```
ConversationalAIService (371 lines)
├── __init__: Initializes 5+ managers directly
├── ai_gateway property: Lazy-loads gateway
├── generate_response: Main entry point (complex)
├── _process_message: Intent detection + routing
├── _build_prompt: Prompt construction
├── _format_response: Style application
└── Various helper methods
```

### Target State

```
ConversationalAIService (150-200 lines)
├── __init__: Receives injected dependencies
├── generate_response: Orchestration only
└── Delegates to:
    ├── ContextProvider.get_full_context()
    ├── PromptBuilder.build_system_prompt()
    ├── AIGateway.generate_text()
    └── StyleRenderer.render_response()
```

### Tasks

#### 3.1 Create Legacy Backup

**File:** `omnix_services/ai_service/legacy/conversational_ai_service_v1.py`

```python
"""
OMNIX - Legacy ConversationalAIService Backup
Created: [DATE]
Purpose: Rollback target if Phase 3 causes issues

This is an exact copy of ai_service.py before Phase 3 refactoring.
"""
# Copy of original ConversationalAIService
```

---

#### 3.2 Modify ConversationalAIService Constructor

**Before:**
```python
def __init__(
    self,
    models_manager: Optional[AIModelsManager] = None,
    styles_manager: Optional[VisualStylesManager] = None,
    prompts_manager: Optional[PromptsContextManager] = None,
    ai_gateway: Optional["RoutingAIGateway"] = None,
):
    self.models = models_manager or AIModelsManager()
    self.styles = styles_manager or VisualStylesManager()
    self.prompts = prompts_manager or PromptsContextManager()
    # ... direct initialization
```

**After:**
```python
def __init__(
    self,
    context_provider: Optional[ContextProviderProtocol] = None,
    prompt_builder: Optional[PromptBuilderProtocol] = None,
    style_renderer: Optional[StyleRendererProtocol] = None,
    ai_gateway: Optional[AIGatewayProtocol] = None,
):
    # Use injected or fallback to container
    self._context_provider = context_provider
    self._prompt_builder = prompt_builder
    self._style_renderer = style_renderer
    self._ai_gateway = ai_gateway
    
    # Lazy initialization for backward compatibility
    # ...
```

---

#### 3.3 Refactor generate_response Method

**Current Flow:**
1. Get user preferences (direct Redis call)
2. Get conversation history (direct Redis call)
3. Detect intent (inline logic)
4. Build prompt (inline logic)
5. Call AI model (via gateway)
6. Format response (inline logic)
7. Store in history (direct Redis call)

**Target Flow:**
1. `context = self.context_provider.get_full_context(user_id)`
2. `prompt = self.prompt_builder.build_system_prompt(context)`
3. `response = await self.ai_gateway.generate_text(request)`
4. `formatted = self.style_renderer.render_response(response)`
5. `self.context_provider.add_message(user_id, response_message)`

---

#### 3.4 Backward Compatibility Layer

**File:** `omnix_services/ai_service/adapters/legacy_adapter.py`

```python
class LegacyAIServiceAdapter:
    """
    Adapter that provides old API using new DI-based internals.
    Ensures existing code continues to work during transition.
    """
    
    def __init__(self, service: ConversationalAIService):
        self._service = service
    
    # Mirror all old method signatures
    async def generate_response(self, chat_id: int, message: str, ...) -> str:
        return await self._service.generate_response(chat_id, message, ...)
```

---

#### 3.5 Feature Flag for V2

**File:** `omnix_config/settings.py`

```python
# Phase 3 Master Switch
AI_SERVICE_V2_ENABLED: bool = False  # Default OFF
```

**Factory Location:** `omnix_services/ai_service/__init__.py`

The `get_ai_service()` factory MUST remain in `__init__.py` to ensure centralized activation across all services. Do not create alternative factories in other modules.

**Usage in factory function:**
```python
def get_ai_service() -> ConversationalAIService:
    if settings.AI_SERVICE_V2_ENABLED:
        container = get_container()
        return ConversationalAIService(
            context_provider=container.context_provider(),
            prompt_builder=container.prompt_builder(),
            style_renderer=container.style_renderer(),
            ai_gateway=container.ai_gateway(),
        )
    else:
        # Legacy initialization
        return ConversationalAIService()
```

---

### Phase 3 Verification Checklist

- [ ] Legacy backup created and committed
- [ ] All existing tests pass with V2 OFF
- [ ] All existing tests pass with V2 ON
- [ ] No breaking changes to public API
- [ ] generate_response() signature unchanged
- [ ] Rate limiting still works
- [ ] Web search integration still works
- [ ] Real Context Provider still works
- [ ] Quantum Physics Validator still works
- [ ] Performance benchmarks comparable

---

## Rollback Procedures

### Phase 2 Rollback

**Risk:** LOW - New files only

1. Delete new provider files
2. Revert container.py changes
3. Remove feature flags from settings.py
4. Restart workflows

**Commands:**
```bash
git checkout HEAD -- omnix_services/ai_service/container.py
rm -rf omnix_services/ai_service/providers/redis_context_provider.py
rm -rf omnix_services/ai_service/providers/omnix_prompt_builder.py
rm -rf omnix_services/ai_service/providers/omnix_style_renderer.py
```

### Phase 3 Rollback

**Risk:** MEDIUM - Modified core file

1. Set `AI_SERVICE_V2_ENABLED = False` in settings
2. Restart workflows
3. Verify bot functioning
4. If needed, restore from legacy backup:

```bash
cp omnix_services/ai_service/legacy/conversational_ai_service_v1.py \
   omnix_services/ai_service/ai_service.py
```

---

## Execution Criteria

### When to Execute Phase 2

- [ ] Track record has 200+ trades (provides buffer for testing)
- [ ] Win rate stable at 55%+ for 7+ days
- [ ] Weekend or low-volume trading period
- [ ] Full team availability for monitoring

### When to Execute Phase 3

- [ ] Phase 2 completed and stable for 7+ days
- [ ] All Phase 2 feature flags tested ON in sandbox
- [ ] Track record has 400+ trades
- [ ] Win rate stable at 55%+ for 14+ days

### When to Activate in Production

- [ ] 500+ trades accumulated
- [ ] All investor metrics validated
- [ ] PDF report generation tested
- [ ] Dashboard metrics confirmed accurate
- [ ] Gradual rollout: 10% → 50% → 100% of requests

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| container.py providers | 3 | 6 | Code count |
| ConversationalAIService lines | 371 | <200 | wc -l |
| Unit test coverage (ai_service/) | ~30% | >80% | pytest-cov |
| Response latency P95 | baseline | ±10% | Prometheus |
| Error rate | baseline | ±5% | Prometheus |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 9, 2025 | OMNIX Dev | Initial roadmap created |
