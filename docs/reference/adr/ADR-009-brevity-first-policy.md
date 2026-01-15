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
| Simple yes/no | 30 | "¿Funciona 24/7?" → "Sí, opera 24/7 en Railway." |
| Operational | 50 | "¿Cómo calcula el riesgo?" → Brief answer + 1 key point |
| Technical | 100 | Architecture questions with specific details |
| Performance/Metrics | 150 | Full metrics with honest framing |
| Due Diligence | 300 | Comprehensive investor response |

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

**RULE:** Answer the question directly in 1-2 sentences FIRST.

WORD LIMITS:
- Simple questions (yes/no): 30 words max
- Operational questions: 50 words max
- Technical questions: 100 words max
- Performance/metrics: 150 words max

PROHIBITED:
- "Caballero", "Estimado", flowery salutations
- "Espero que esta respuesta sea de su agrado"
- Numbered sections for simple questions
- Marketing mixed with technical content

EXAMPLE - CORRECT:
Q: "¿Las cuentas de fondeo se operan igual?"
A: "Sí. El motor aplica los mismos vetos, gates y protección de capital. 
    La única diferencia es que el dinero no es real todavía."

EXAMPLE - WRONG:
Q: "¿Las cuentas de fondeo se operan igual?"
A: "Caballero Harold, buenos días. Su pregunta sobre si las cuentas 
    de fondeo se operan igual que con capital real es crucial para 
    comprender la filosofía de OMNIX..." [600+ words]
```

### 2. Question Type Detection

Add to intent analysis:

```python
def get_response_word_limit(question: str) -> int:
    """Determine max words based on question complexity."""
    question_lower = question.lower()
    
    # Simple yes/no questions
    if any(q in question_lower for q in ['funciona', 'opera', 'tiene', 'puede', 'es posible']):
        if len(question.split()) < 10:
            return 30
    
    # Performance/metrics
    if any(q in question_lower for q in ['win rate', 'rendimiento', 'balance', 'p&l', 'métricas']):
        return 150
    
    # Technical/architecture
    if any(q in question_lower for q in ['cómo funciona', 'arquitectura', 'algoritmo', 'explica']):
        return 100
    
    # Default operational
    return 50
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
| 2026-01-15 | Initial adoption after investor communication issue identified |
