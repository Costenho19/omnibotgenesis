# AI Response Speed Optimization - January 30, 2026

## Problem Statement

The bot was experiencing timeout errors when users sent messages, particularly for market analysis requests. The OpenAI API was timing out after 15 seconds, causing "Procesando tu mensaje..." to hang without response.

**Symptom observed in logs:**
```
2026-01-30 06:11:55 [WARNING] omnix_services.ai_service.ai_error_handler - ❌ OPENAI Timeout después de 15.0s | Intento 1/3
```

## Solution Implemented

### 1. Increased AI Timeouts (15s → 30s)

**File:** `omnix_services/ai_service/ai_models.py`

| Provider | Before | After |
|----------|--------|-------|
| OpenAI | 15s | 30s |
| Gemini | 20s | 30s |
| Anthropic | 15s | 30s |

**Rationale:** Complex market analysis prompts require more processing time, especially when the AI is generating detailed responses with multiple data points.

### 2. Smart Model Selection (GPT-4o-mini Fast Path)

**File:** `omnix_services/ai_service/ai_models.py`

Added intelligent routing based on query complexity:

| Query Type | Model | Timeout | Response Length Min |
|------------|-------|---------|---------------------|
| Simple (greetings, short non-trading) | GPT-4o-mini | 15s | 10 chars |
| Complex (market analysis, trading) | GPT-4o | 30s | 50 chars |

**Simple Query Detection (`_is_simple_query()`):**
- Greetings: hola, hello, hi, buenos días, etc.
- Short messages (<20 chars) without trading keywords
- Simple responses: sí, no, ok, gracias, etc.

**Trading Keywords (force GPT-4o):**
- btc, eth, xrp, precio, price
- mercado, market, trade, trading
- buy, sell, comprar, vender
- análisis, analysis, reporte, report

### 3. Relaxed Validation for Simple Responses

**File:** `omnix_services/ai_service/ai_models.py`

| Constant | Value | Purpose |
|----------|-------|---------|
| `MIN_RESPONSE_LENGTH` | 50 | Complex responses |
| `MIN_RESPONSE_LENGTH_SIMPLE` | 10 | Simple greetings |

**Integration Point:**
- `_validate_response(response, is_simple=True/False)` now accepts context
- Prevents false rejections of valid short greetings

## Code Changes Summary

```python
# Before
TIMEOUT_OPENAI = 15.0
TIMEOUT_GEMINI = 20.0
TIMEOUT_ANTHROPIC = 15.0

# After
TIMEOUT_OPENAI = 30.0
TIMEOUT_GEMINI = 30.0
TIMEOUT_ANTHROPIC = 30.0
```

**New Methods Added:**
- `_generate_openai_fast_async()` - GPT-4o-mini with 15s timeout
- `_is_simple_query()` - Detects simple queries
- `generate_smart_async()` - Public method for smart selection

**Modified Methods:**
- `generate()` - Now uses smart selection for GPT models
- `_validate_response()` - Accepts `is_simple` parameter

## Expected Behavior

| User Message | Model Used | Expected Response Time |
|--------------|------------|------------------------|
| "Hola" | GPT-4o-mini | 2-3 seconds |
| "Buenos días" | GPT-4o-mini | 2-3 seconds |
| "Cómo ves el BTC?" | GPT-4o | 5-15 seconds |
| "Dame un análisis del mercado" | GPT-4o | 10-25 seconds |

## Logging

**Fast Path:**
```
⚡ Using GPT-4o-mini for simple query
⚡ GPT-4o-mini generated X characters (fast mode)
```

**Standard Path:**
```
✅ GPT-4o generated X characters
```

## Rollback Procedure

If issues occur, revert to previous behavior by:

1. Change timeouts back to 15s/20s/15s
2. Remove `_is_simple_query()` logic from `generate()` method
3. Remove `is_simple` parameter from `_validate_response()`

## Related Files

- `omnix_services/ai_service/ai_models.py` - Main changes
- `replit.md` - Updated with Jan 30 changes

## Session Metrics

- **Files Modified:** 2
- **New Methods:** 3
- **Architect Review:** Completed (validation issue fixed)
