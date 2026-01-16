# ADR-009: Brevity First Policy

**Status:** ADOPTED  
**Date:** January 15, 2026  
**Author:** Core Team + AI Architect  
**Supersedes:** None  

---

## Context

OMNIX AI responses were identified as problematic for investor communication:

**Observed Problem (Jan 14, 2026):**
- User asked: "¿Las cuentas de fondeo se operan igual que el capital real?"
- Expected answer: "Sí. A nivel operativo, el motor aplica los mismos vetos y protección."
- Actual response: 600+ words with jargon, marketing narrative, and philosophical framing

**Impact:**
- Confuses users with unnecessary complexity
- Makes investors suspicious ("¿Qué está ocultando?")
- Undermines credibility by mixing marketing with technical content
- Creates perception of "storytelling" instead of "substance"

---

## Decision

Implement **BREVITY FIRST** policy across all AI responses:

### Core Rule

> **Answer the question directly in 1-2 sentences FIRST.**  
> Details, context, and elaboration are optional and come AFTER.

### Word Limits by Question Type

| Question Type | Max Words | Example |
|--------------|-----------|---------|
| **Explanation/Lists** | **UNLIMITED** | "Explícame cómo funciona", "dime 10 cosas" → Full response |
| Simple yes/no | 80 | "¿Funciona 24/7?" → "Sí, opera 24/7." + brief context |
| Operational | 120 | "¿Cómo calcula el riesgo?" → Answer + friendly context |
| Technical | 180 | Architecture questions with conversational depth |
| Performance/Metrics | 200 | Full metrics with honest framing |
| Due Diligence | 350 | Comprehensive investor response |

> **UPDATE (Jan 16, 2026):** Limits raised to allow conversational, friendly responses while maintaining brevity. Original 30-50 word limits were too restrictive for pleasant interaction.

### Adaptive Behavior: User-Driven Detail Level

When the user explicitly requests an explanation, the system removes word limits:

**Explanation Triggers (Spanish):**
- "explícame", "cuéntame más", "dame detalles", "en detalle"
- "quiero saber más", "más información", "cuéntame todo"

**Explanation Triggers (English):**
- "tell me more", "explain in detail", "give me details"
- "elaborate", "walk me through", "break it down"

**Behavior:**
- User asks simple question → Conversational response (80-120 words)
- User says "explícame más" or requests lists → Full response without limit
- This ensures brevity by default but allows depth when requested
- Responses should be friendly and pleasant, not cold or robotic

### Prohibited Patterns

**NEVER use:**
- "Caballero [Name]" or similar flowery salutations
- "Espero que esta respuesta sea de su agrado"
- Multiple numbered sections for simple questions
- Marketing language mixed with technical answers
- Philosophical framing ("para comprender la filosofía de OMNIX...")
- Unnecessary repetition of question back to user

**ALWAYS:**
- Start with direct answer
- Use simple, everyday language
- One idea per sentence
- Technical terms only when necessary (with brief explanation)

---

## Implementation

### 1. MASTER_SYSTEM_PROMPT Update

Add BREVITY FIRST section:

```
## BREVITY FIRST POLICY [CRITICAL - ADR-009]

**RULE:** Answer the question directly in 1-2 sentences FIRST. Then add friendly context.

WORD LIMITS (Updated Jan 16, 2026 - Conversational Focus):
- Simple questions (yes/no): 80 words max
- Operational questions: 120 words max
- Technical questions: 180 words max
- Performance/metrics: 200 words max
- Explanation/list requests: UNLIMITED

TONE: Be conversational and friendly. Not cold or robotic.

PROHIBITED:
- "Caballero", "Estimado", flowery salutations
- "Espero que esta respuesta sea de su agrado"
- Numbered sections for simple questions
- Marketing mixed with technical content

EXAMPLE - CORRECT:
Q: "¿Las cuentas de fondeo se operan igual?"
A: "Sí, exactamente igual. El motor aplica los mismos vetos, gates y protección 
    de capital en ambos casos. La única diferencia es que el dinero no es real 
    todavía, lo que nos permite validar sin riesgo. ¿Tienes alguna otra pregunta?"

EXAMPLE - WRONG:
Q: "¿Las cuentas de fondeo se operan igual?"
A: "Caballero Harold, buenos días. Su pregunta sobre si las cuentas 
    de fondeo se operan igual que con capital real es crucial para 
    comprender la filosofía de OMNIX..." [600+ words]
```

### 2. Question Type Detection

Add to intent analysis:

```python
def get_response_word_limit(question: str) -> Optional[int]:
    """Determine max words based on question complexity.
    Returns None for unlimited (explanation/list requests).
    Updated Jan 16: Conversational limits."""
    question_lower = question.lower()
    
    # PRIORITY 1: Explicit explanation/list requests → NO LIMIT
    explanation_indicators = ['explícame', 'cuéntame más', 'dame detalles',
                              'enumera', 'cuales son', 'dime todas',
                              'tell me more', 'explain in detail', 'list all']
    if any(ind in question_lower for ind in explanation_indicators):
        return None  # Unlimited
    
    # Numbered list requests (e.g., "dime 10 cosas")
    if re.search(r'(dime|dame|give me|tell me)\s+\d+\s+', question_lower):
        return None  # Unlimited
    
    # Simple yes/no questions
    if any(q in question_lower for q in ['funciona', 'opera', 'tiene', 'puede']):
        if len(question.split()) < 10:
            return 80  # Updated from 30
    
    # Performance/metrics
    if any(q in question_lower for q in ['win rate', 'rendimiento', 'balance']):
        return 200  # Updated from 150
    
    # Default operational
    return 120  # Updated from 50
```

### 3. Response Post-Processing

Add brevity check before sending:

```python
def enforce_brevity(response: str, max_words: int) -> str:
    """Ensure response doesn't exceed word limit."""
    words = response.split()
    if len(words) <= max_words:
        return response
    
    # Truncate to max_words and add continuation offer
    truncated = ' '.join(words[:max_words])
    return f"{truncated}... ¿Necesitas más detalles?"
```

---

## Consequences

### Positive

- Clearer, more professional communication
- Faster responses for users
- More credible for investors ("answers the question")
- Reduced AI token usage (cost savings)
- Eliminates "bot habla como filósofo" perception

### Negative

- Some technical depth may be lost in initial response
- Users may need to ask follow-up questions

### Mitigation

- Offer "¿Necesitas más detalles?" for truncated responses
- Complex technical questions still get 100-150 words
- Due diligence context triggers expanded responses

---

## Validation

**Test Case 1:**
- Input: "¿Las cuentas de fondeo se operan igual que el capital real?"
- Expected: ~30 words, direct answer first
- Pass if: No "Caballero", no philosophical framing, answers question in first sentence

**Test Case 2:**
- Input: "¿Cuál es el win rate actual?"
- Expected: ~50 words with metrics + honest context
- Pass if: Shows real number, adds context, no marketing language

---

## References

- ADR-002: Honest Framing over Censorship
- ADR-003: Official Positioning Strategy
- docs/reference/omnix_official_language.md

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | **Conversational Tone Update:** Raised all word limits (30→80, 50→120, 100→180, 150→200, 300→350) to allow friendly, amene responses while maintaining brevity. Added list/enumeration detection. |
| 2026-01-15 | Added adaptive behavior: explanation requests get unlimited words |
| 2026-01-15 | Initial adoption after investor communication issue identified |
