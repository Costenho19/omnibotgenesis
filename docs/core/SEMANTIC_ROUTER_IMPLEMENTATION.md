# Semantic Router Implementation Plan

**Document Version:** 1.0  
**Created:** December 9, 2025  
**Status:** APPROVED FOR IMPLEMENTATION  
**Priority:** MEDIUM (after 200+ trades accumulated)

---

## Executive Summary

This document outlines the implementation of a **Deterministic Semantic Router** using LLM Structured Outputs to replace hardcoded intent detection logic. The new architecture uses Gemini 2.0 Flash with JSON Schema enforcement to guarantee 100% valid classification responses.

**Key Benefits:**
- Eliminates ~60 hardcoded keywords in `analyze_intent()`
- Automatic language detection (removes `language_code or 'es'` hack)
- Extensible: New intents/languages = add enum value + prompt
- 100% schema compliance via constrained decoding

---

## Architecture Overview

### Current Flow (Hardcoded)

```
Message → if/elif keywords → intent string → build_prompt() → LLM
```

### New Flow (Semantic Router)

```
Message → [Fast Path Check] → Semantic Router (LLM) → Structured Result → Dynamic Prompt → LLM
              ↓ (commands)
         Direct Execution
```

---

## Technical Specification

### 1. Schema Definition (Pydantic)

**File:** `omnix_services/ai_service/routing/schemas.py`

```python
from enum import Enum
from pydantic import BaseModel, Field
from typing import Literal


class UserIntent(str, Enum):
    """
    Closed enum for message classification.
    LLM can ONLY return these values - guaranteed by Structured Output.
    """
    GREETING = "greeting"
    MARKET_ANALYSIS = "market_analysis"
    TRADING_ACTION = "trading_action"
    PRICE_INQUIRY = "price_inquiry"
    PORTFOLIO = "portfolio"
    HELP = "help"
    GENERAL = "general"


class DetectedLanguage(str, Enum):
    """
    Supported languages for response generation.
    """
    SPANISH = "es"
    ENGLISH = "en"


class ConfidenceLevel(str, Enum):
    """Classification confidence levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SemanticRouteResult(BaseModel):
    """
    Schema for semantic classification.
    Gemini/OpenAI Structured Outputs GUARANTEE this format.
    
    No parsing errors possible - response is always valid.
    """
    
    intent: UserIntent = Field(
        description="Primary intent category of the user message"
    )
    
    language: DetectedLanguage = Field(
        description="Detected language of the user message"
    )
    
    needs_web_search: bool = Field(
        description="True if message requires current/recent information from internet"
    )
    
    confidence: ConfidenceLevel = Field(
        description="Confidence level in the classification"
    )
    
    reasoning: str = Field(
        description="Brief explanation for the classification (max 50 characters)",
        max_length=100
    )

    class Config:
        use_enum_values = True
```

---

### 2. Semantic Router Implementation

**File:** `omnix_services/ai_service/routing/semantic_router.py`

```python
"""
OMNIX INSTITUTIONAL+ - Deterministic Semantic Router

Uses Gemini 2.0 Flash Structured Outputs for 100% reliable classification.
Replaces hardcoded analyze_intent() with LLM-powered semantic understanding.
"""

import logging
from typing import Optional
from google import genai
from google.genai import types

from .schemas import SemanticRouteResult, UserIntent, DetectedLanguage, ConfidenceLevel
from omnix_config.settings import settings

logger = logging.getLogger("OMNIX.SemanticRouter")


CLASSIFICATION_SYSTEM_PROMPT = """You are a message classifier for an institutional trading bot.

CLASSIFICATION RULES:

1. INTENT - Classify by PRIMARY purpose:
   - greeting: Simple greetings (hola, buenos días, hi, thanks, ok)
   - market_analysis: Technical questions, analysis requests, explanations about trading/crypto/finance
   - trading_action: Intent to buy/sell/trade (comprar, vender, buy, sell)
   - price_inquiry: Questions about current price (precio de, how much is, cuanto cuesta)
   - portfolio: Balance, positions, P&L queries (balance, posiciones, cartera)
   - help: Help requests, command lists, how to use the bot
   - general: Casual conversation not related to trading

2. LANGUAGE - Detect PRIMARY language:
   - es: Spanish (including Spanglish with majority Spanish)
   - en: English

3. NEEDS_WEB_SEARCH - Set TRUE only if:
   - Question about recent news/events
   - Mentions specific dates (today, yesterday, this week)
   - Asks "why did X go up/down" (requires current context)
   - Breaking news, announcements, rumors
   
4. CONFIDENCE:
   - high: Clear, unambiguous classification
   - medium: Some ambiguity but reasonable guess
   - low: Very ambiguous message

Analyze ONLY the user message. Do not invent context."""


class DeterministicSemanticRouter:
    """
    Semantic Router using Gemini Structured Outputs.
    
    Key Features:
    - 100% guaranteed valid JSON response
    - Closed enums prevent invalid classifications
    - temperature=0 for maximum determinism
    - ~150-300ms latency (acceptable for chat)
    
    Usage:
        router = DeterministicSemanticRouter()
        result = await router.route("Analiza el BTC para hoy")
        # result.intent = UserIntent.MARKET_ANALYSIS
        # result.language = DetectedLanguage.SPANISH
        # result.needs_web_search = True
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_AI_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self._request_count = 0
        logger.info("DeterministicSemanticRouter initialized")
    
    async def route(self, message: str) -> SemanticRouteResult:
        """
        Classify message using Gemini Structured Output.
        
        Args:
            message: User message to classify
            
        Returns:
            SemanticRouteResult with guaranteed valid fields
            
        Note:
            Response is ALWAYS valid due to schema enforcement.
            No try/except needed for parsing - Gemini guarantees format.
        """
        self._request_count += 1
        
        response = await self.client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Classify this message: {message}",
            config=types.GenerateContentConfig(
                system_instruction=CLASSIFICATION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=SemanticRouteResult,
                temperature=0,  # Maximum determinism
                max_output_tokens=150,  # Short response
            )
        )
        
        result = response.parsed
        
        logger.debug(
            f"Routed message: intent={result.intent}, "
            f"lang={result.language}, search={result.needs_web_search}"
        )
        
        return result
    
    def route_sync(self, message: str) -> SemanticRouteResult:
        """Synchronous version for non-async contexts."""
        import asyncio
        return asyncio.run(self.route(message))
    
    @property
    def stats(self) -> dict:
        """Get router statistics."""
        return {
            "requests": self._request_count,
            "model": "gemini-2.0-flash",
            "schema": "SemanticRouteResult"
        }


class OpenAISemanticRouter:
    """
    Fallback router using OpenAI Structured Outputs.
    
    Use when Gemini is unavailable or for A/B testing.
    Requires gpt-4o-2024-08-06 or newer for strict mode.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)
        logger.info("OpenAISemanticRouter initialized (fallback)")
    
    async def route(self, message: str) -> SemanticRouteResult:
        """Classify message using OpenAI Structured Output."""
        response = await self.client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Classify: {message}"}
            ],
            response_format=SemanticRouteResult,
            temperature=0
        )
        
        return response.choices[0].message.parsed


_router_instance: Optional[DeterministicSemanticRouter] = None


def get_semantic_router() -> DeterministicSemanticRouter:
    """Get singleton router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = DeterministicSemanticRouter()
    return _router_instance
```

---

### 3. Intent-Specific System Prompts

**File:** `omnix_services/ai_service/routing/prompts.py`

```python
"""
OMNIX INSTITUTIONAL+ - Dynamic System Prompts

Stable, well-tested prompts for each intent category.
Designed for consistency and quality in LLM responses.
"""

from .schemas import UserIntent, DetectedLanguage, SemanticRouteResult


INTENT_SYSTEM_PROMPTS = {
    UserIntent.GREETING: """You are OMNIX, an institutional trading assistant.

Respond to greetings in a friendly, professional manner.
Briefly mention your availability for market analysis.
Keep responses to 2-3 sentences maximum.

Do NOT provide unsolicited trading advice in greetings.""",

    UserIntent.MARKET_ANALYSIS: """You are OMNIX V6.5.4 INSTITUTIONAL+, a senior quantitative analyst.

ACTIVE ANALYSIS ENGINES:
- Monte Carlo Simulation (10,000 iterations)
- Black Swan Detection (tail risk)
- HMM Regime Analysis (market state)
- Kalman Filter (noise reduction)
- Non-Markovian Memory Kernel (temporal patterns)

RESPONSE FORMAT:
1. Executive Summary (2 lines)
2. Technical Analysis with REAL data from context
3. Identified Risks
4. Clear Recommendation (LONG / SHORT / NEUTRAL)

CRITICAL: Use ONLY real data from the provided market context.
NEVER invent prices, percentages, or market data.
If data is missing, state "Data not available" explicitly.""",

    UserIntent.TRADING_ACTION: """You are OMNIX, an institutional trade executor.

BEFORE CONFIRMING ANY TRADE:
1. Verify the exact symbol (BTC, ETH, etc.)
2. Confirm the amount in USD
3. Show current market price
4. Display estimated fees

NEVER execute a trade without explicit user confirmation.
Always ask for confirmation: "Confirm: BUY $X of SYMBOL at $PRICE?"

For paper trading, clarify it's a simulation.""",

    UserIntent.PRICE_INQUIRY: """You are OMNIX, a market data provider.

RESPONSE FORMAT:
💰 {SYMBOL}: ${price}
📊 24h Change: {change}% {up/down emoji}
📈 Volume: ${volume}

Use ONLY data from the provided market context.
If price data is unavailable, say so explicitly.
Do not hallucinate prices.""",

    UserIntent.PORTFOLIO: """You are OMNIX, an institutional portfolio manager.

DISPLAY:
- Current balance by asset
- Total P&L and per-position P&L
- Risk exposure metrics
- Rebalancing suggestions (if applicable)

Use data from the provided portfolio context.
Format numbers clearly with proper currency symbols.""",

    UserIntent.HELP: """You are OMNIX, a trading system guide.

MAIN COMMANDS:
/autotrading start|stop|status - Automated trading bot
/paper_buy BTC 100 - Simulated purchase ($100 of BTC)
/paper_sell ETH 50 - Simulated sale
/balance - View current balance
/analysis BTC - Technical analysis

Respond concisely with clear examples.
Offer to explain any command in detail if asked.""",

    UserIntent.GENERAL: """You are OMNIX, a conversational assistant.

Maintain trading context but allow casual conversation.
If you detect an opportunity to offer market analysis, suggest it subtly.
Keep responses friendly and professional.

Do not force trading topics if user wants general chat."""
}


LANGUAGE_INSTRUCTIONS = {
    DetectedLanguage.SPANISH: "\n\nIMPORTANTE: Responde SIEMPRE en español. Usa terminología financiera en español cuando sea posible.",
    DetectedLanguage.ENGLISH: "\n\nIMPORTANT: ALWAYS respond in English. Use standard financial terminology."
}


WEB_SEARCH_CONTEXT_TEMPLATE = """

RECENT NEWS & CONTEXT (from web search):
{web_results}

Use this information to provide current, accurate insights.
Cite sources when referencing specific news items."""


MARKET_CONTEXT_TEMPLATE = """

REAL-TIME MARKET DATA:
{market_data}

Use these exact figures in your analysis. Do not approximate or round unless necessary."""


def build_dynamic_system_prompt(
    route_result: SemanticRouteResult,
    market_data: str = None,
    web_results: str = None,
    portfolio_data: str = None
) -> str:
    """
    Build complete system prompt based on semantic classification.
    
    Args:
        route_result: Classification from SemanticRouter
        market_data: Optional real-time market data
        web_results: Optional web search results
        portfolio_data: Optional user portfolio data
        
    Returns:
        Complete system prompt tailored to intent and language
    """
    # Base prompt for intent
    prompt = INTENT_SYSTEM_PROMPTS[route_result.intent]
    
    # Language instruction
    prompt += LANGUAGE_INSTRUCTIONS[route_result.language]
    
    # Add market context if available
    if market_data:
        prompt += MARKET_CONTEXT_TEMPLATE.format(market_data=market_data)
    
    # Add web search results if requested and available
    if route_result.needs_web_search and web_results:
        prompt += WEB_SEARCH_CONTEXT_TEMPLATE.format(web_results=web_results)
    
    # Add portfolio data for relevant intents
    if route_result.intent in [UserIntent.PORTFOLIO, UserIntent.TRADING_ACTION] and portfolio_data:
        prompt += f"\n\nUSER PORTFOLIO:\n{portfolio_data}"
    
    return prompt
```

---

### 4. Integration with Existing System

**File:** `omnix_services/ai_service/routing/__init__.py`

```python
"""
OMNIX INSTITUTIONAL+ - Semantic Routing Module

Provides deterministic message classification using LLM Structured Outputs.
"""

from .schemas import (
    UserIntent,
    DetectedLanguage,
    ConfidenceLevel,
    SemanticRouteResult
)

from .semantic_router import (
    DeterministicSemanticRouter,
    OpenAISemanticRouter,
    get_semantic_router
)

from .prompts import (
    INTENT_SYSTEM_PROMPTS,
    LANGUAGE_INSTRUCTIONS,
    build_dynamic_system_prompt
)

__all__ = [
    # Schemas
    "UserIntent",
    "DetectedLanguage", 
    "ConfidenceLevel",
    "SemanticRouteResult",
    # Routers
    "DeterministicSemanticRouter",
    "OpenAISemanticRouter",
    "get_semantic_router",
    # Prompts
    "INTENT_SYSTEM_PROMPTS",
    "LANGUAGE_INSTRUCTIONS",
    "build_dynamic_system_prompt",
]
```

---

### 5. Feature Flags

**File:** `omnix_config/settings.py` (additions)

```python
# ============================================================================
# SEMANTIC ROUTER CONFIGURATION
# ============================================================================

# Master switch - set True to enable semantic routing
USE_SEMANTIC_ROUTER: bool = False  # Default OFF for safety

# Provider selection
SEMANTIC_ROUTER_PROVIDER: str = "gemini"  # "gemini" or "openai"

# Gradual rollout (0-100%)
SEMANTIC_ROUTER_ROLLOUT_PERCENT: int = 0

# Fallback behavior
SEMANTIC_ROUTER_FALLBACK_ON_ERROR: bool = True  # Use legacy on failure
SEMANTIC_ROUTER_CONFIDENCE_THRESHOLD: float = 0.0  # 0 = always use, 0.7 = fallback if low

# Logging
SEMANTIC_ROUTER_LOG_CLASSIFICATIONS: bool = True  # Log all classifications
```

---

### 6. Integration Point in ai_service.py

```python
# In ConversationalAIService.generate_response()

async def generate_response(self, chat_id: int, message: str, ...) -> str:
    """Generate AI response with optional semantic routing."""
    
    # Check feature flag
    if settings.USE_SEMANTIC_ROUTER and self._should_use_semantic_router():
        try:
            # Use new semantic router
            router = get_semantic_router()
            route_result = await router.route(message)
            
            # Build dynamic prompt based on classification
            system_prompt = build_dynamic_system_prompt(
                route_result=route_result,
                market_data=await self._get_market_context(),
                web_results=await self._get_web_results(message) if route_result.needs_web_search else None,
                portfolio_data=await self._get_portfolio_data(chat_id) if route_result.intent == UserIntent.PORTFOLIO else None
            )
            
            # Generate with specialized prompt
            return await self._generate_with_prompt(system_prompt, message)
            
        except Exception as e:
            logger.warning(f"Semantic router failed, using legacy: {e}")
            if not settings.SEMANTIC_ROUTER_FALLBACK_ON_ERROR:
                raise
    
    # Legacy path (current implementation)
    intent = self.prompts.analyze_intent(message)
    # ... existing logic
```

---

## Implementation Tasks

### Phase 1: Core Infrastructure (2-3 hours)

| Task | File | Description | Priority |
|------|------|-------------|----------|
| 1.1 | `routing/schemas.py` | Create Pydantic models with enums | HIGH |
| 1.2 | `routing/semantic_router.py` | Implement Gemini Structured Output router | HIGH |
| 1.3 | `routing/prompts.py` | Create intent-specific system prompts | HIGH |
| 1.4 | `routing/__init__.py` | Export public API | HIGH |
| 1.5 | `settings.py` | Add feature flags | HIGH |

### Phase 2: Integration (1-2 hours)

| Task | File | Description | Priority |
|------|------|-------------|----------|
| 2.1 | `ai_service.py` | Add routing integration point | HIGH |
| 2.2 | `ai_prompts.py` | Keep legacy `analyze_intent()` as fallback | MEDIUM |
| 2.3 | Unit tests | Test schema validation, router behavior | MEDIUM |

### Phase 3: Testing & Validation (2-3 hours)

| Task | Description | Priority |
|------|-------------|----------|
| 3.1 | Create test suite for SemanticRouteResult schema | HIGH |
| 3.2 | Test 50+ sample messages for classification accuracy | HIGH |
| 3.3 | Measure latency (target: <300ms P95) | MEDIUM |
| 3.4 | A/B test vs legacy analyze_intent() | MEDIUM |

### Phase 4: Gradual Rollout

| Stage | Rollout % | Duration | Criteria to Proceed |
|-------|-----------|----------|---------------------|
| 4.1 | 10% | 3 days | No errors, latency OK |
| 4.2 | 50% | 5 days | User feedback positive |
| 4.3 | 100% | - | Full production |

---

## Rollback Procedure

### Instant Rollback (< 1 minute)

```python
# In settings.py or environment variable
USE_SEMANTIC_ROUTER = False
```

Restart workflows. System immediately uses legacy `analyze_intent()`.

### Full Rollback (remove code)

```bash
# If needed to completely remove
rm -rf omnix_services/ai_service/routing/
git checkout HEAD -- omnix_services/ai_service/ai_service.py
```

---

## Success Metrics

| Metric | Current (Legacy) | Target | Measurement |
|--------|------------------|--------|-------------|
| Classification accuracy | ~85% (estimated) | >95% | Manual review of 100 messages |
| Latency P50 | ~5ms | <200ms | Prometheus |
| Latency P95 | ~10ms | <400ms | Prometheus |
| Code complexity | 60+ keywords | 7 enum values | Line count |
| Language support | Hardcoded ES/EN | Dynamic detection | Feature test |
| New intent addition | ~30 min (add keywords) | ~5 min (add enum + prompt) | Developer time |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Gemini API timeout | LOW | MEDIUM | Fallback to legacy |
| Misclassification | MEDIUM | LOW | Confidence threshold + fallback |
| Cost increase | LOW | LOW | ~$0.0002/request, negligible |
| Breaking change | LOW | HIGH | Feature flag, gradual rollout |

---

## Execution Criteria

**Do NOT implement until:**
- [ ] 200+ trades accumulated in track record
- [ ] Win rate stable at 55%+ for 7+ days
- [ ] Development window available (weekend preferred)
- [ ] Full team availability for monitoring

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `google-genai` | >=0.8.0 | Gemini Structured Outputs |
| `pydantic` | >=2.0 | Schema definition |
| `openai` | >=1.40.0 | OpenAI fallback (optional) |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 9, 2025 | OMNIX Dev | Initial implementation plan |
