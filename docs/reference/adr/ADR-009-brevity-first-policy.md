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
| **INVESTOR DUE DILIGENCE** | **UNLIMITED** | Family office, AUM, seed, pre-money, multiple questions → FULL response |
| **Explanation/Lists** | **UNLIMITED** | "Explícame cómo funciona", "dime 10 cosas" → Full response |
| **Long Questions (100+ words)** | **UNLIMITED** | Detailed question deserves detailed answer |
| Simple yes/no | 80 | "¿Funciona 24/7?" → "Sí, opera 24/7." + brief context |
| Operational | 120 | "¿Cómo calcula el riesgo?" → Answer + friendly context |
| Technical | 180 | Architecture questions with conversational depth |
| Performance/Metrics | 200 | Full metrics with honest framing |

> **UPDATE (Jan 16, 2026 - Conversational Tone):** Limits raised for friendly interaction.  
> **UPDATE (Jan 16, 2026 - Investor Questions):** Investor due diligence questions now get UNLIMITED responses. Investors deserve complete answers with data, calculations, and justification.

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

### Investor Due Diligence Detection (CRITICAL)

When ANY of these signals are detected, the response has NO WORD LIMIT:

**Investor Signals:**
- "family office", "AUM", "seed", "pre-money", "post-money"
- "equity", "valuation", "term sheet", "institutional"
- "due diligence", "diligence examen", "evaluating", "evaluando"
- "mandatory questions", "preguntas obligatorias"
- "clientes institucionales", "cliente institucional"

**Compliance Signals:**
- "sharia", "compliance", "regulatory", "SEC", "legal", "jurisdiction"

**Systemic Risk / Sophisticated Investor Signals (Jan 19, 2026):**
- "riesgo sistémico", "systemic risk", "amplificador de riesgo", "risk amplifier"
- "externalidades adversas", "adverse externalities"
- "fail-closed", "fail closed", "modo fail"
- "estrés sistémico", "systemic stress"
- "efectos de segunda ronda", "second-order effects"
- "retroalimentación negativa", "negative feedback"
- "preservación de capital", "capital preservation"

**Structure Signals:**
- Multiple numbered questions (1. 2. 3. etc. - 3 or more)
- Long questions (100+ words)

**Response Requirements for Investor Questions:**
1. Acknowledge the seriousness of their inquiry
2. Address EACH numbered point with specific data
3. Include calculations, SQL queries, or projections when requested
4. Provide honest assessments with confidence levels
5. Do NOT truncate or summarize - investors want COMPLETE answers

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

### Post-Processing Anti-Servile Filter (Jan 19, 2026)

A safety-net filter in `conversational_ai_adapter.py` removes servile/prohibited phrases AFTER AI generation. This catches phrases even when the AI ignores prompt instructions.

**Location:** `omnix_services/ai_service/conversational_ai_adapter.py` → `BLACKLISTED_PHRASES` + `post_process_response()`

**Filtered Patterns (Spanish):**
- "Agradezco la perspicacia de tu pregunta..."
- "me comprometo a ofrecer una respuesta exhaustiva..."
- "mi objetivo es proporcionar claridad..."
- "Entiendo la importancia de este tema..."
- Numbered section headers: "*1. Análisis Inmediato*", "**2. Datos Técnicos**", "3. Conclusión:"

**Filtered Patterns (English):**
- "I appreciate the insight of your question..."
- "I appreciate your question..."
- "I understand the importance..."

**Behavior:**
- Complete servile sentences are removed, preserving valuable content
- Numbered headers are stripped, keeping the content that follows
- Mid-sentence appendages like ", y me comprometo a ofrecer..." are cleaned
- Response is capitalized properly after removal

---

## Implementation

### 1. MASTER_SYSTEM_PROMPT Update

Add BREVITY FIRST section:

```
## BREVITY FIRST POLICY [CRITICAL - ADR-009]

**RULE:** Match response length to question complexity. Direct answer first.

INVESTOR DUE DILIGENCE → UNLIMITED (CRITICAL):
When detecting: family office, AUM, seed round, pre-money, due diligence,
multiple numbered questions (3+), or 100+ word questions:
→ Provide COMPLETE response with data, calculations, justification

WORD LIMITS (Normal Conversations):
- Simple questions (yes/no): 80 words max
- Operational questions: 120 words max
- Technical questions: 180 words max
- Performance/metrics: 200 words max
- Explanation/list requests: UNLIMITED

TONE: Conversational and friendly. Not cold or robotic.

PROHIBITED:
- "Caballero", "Estimado", flowery salutations
- Philosophical framing for simple questions

EXAMPLE - SIMPLE QUESTION:
Q: "¿Las cuentas de fondeo se operan igual?"
A: "Sí, exactamente igual. El motor aplica los mismos vetos y protección 
    de capital. La única diferencia es que el dinero no es real todavía."

EXAMPLE - INVESTOR DUE DILIGENCE:
Q: [Family office, 5 technical questions about metrics, sizing, scalability...]
A: [COMPLETE response addressing each point with data, tables, calculations]
```

### 2. Question Type Detection

Add to intent analysis:

```python
def get_response_word_limit(question: str) -> Optional[int]:
    """Determine max words based on question complexity.
    Updated Jan 16: Investor questions get FULL responses."""
    question_lower = question.lower()
    word_count = len(question.split())
    
    # PRIORITY 0: INVESTOR DUE DILIGENCE → UNLIMITED
    investor_indicators = ['family office', 'aum', 'seed round', 'pre-money',
                           'due diligence', 'preguntas obligatorias', 'valuation']
    if any(ind in question_lower for ind in investor_indicators):
        return None  # UNLIMITED - investor deserves full answer
    
    # PRIORITY 0b: Multiple numbered questions (3+) → UNLIMITED
    if re.search(r'(\d+[\.\)]\s*.*?){3,}', question, re.DOTALL):
        return None  # UNLIMITED - structured multi-part question
    
    # PRIORITY 0c: Long questions (100+ words) → UNLIMITED
    if word_count >= 100:
        return None  # UNLIMITED - detailed question, detailed answer
    
    # PRIORITY 1: Explicit explanation/list requests → UNLIMITED
    explanation_indicators = ['explícame', 'enumera', 'cuales son', 'dime todas']
    if any(ind in question_lower for ind in explanation_indicators):
        return None  # Unlimited
    
    # Simple yes/no: 80 words, Metrics: 200 words, Default: 120 words
    if word_count < 10:
        return 80
    if any(q in question_lower for q in ['win rate', 'rendimiento']):
        return 200
    return 120
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
| 2026-01-19 | **Sophisticated Investor Detection:** Added systemic risk indicators (riesgo sistémico, amplificador de riesgo, externalidades adversas, fail-closed, estrés sistémico, efectos de segunda ronda, retroalimentación negativa, preservación de capital). Added "clientes institucionales" to investor signals. |
| 2026-01-19 | **Anti-Servile Filter Enhancement:** Added patterns for "Agradezco la perspicacia", "me comprometo a ofrecer", numbered section headers (*1. Análisis Inmediato*, etc.). Filter now removes complete servile sentences while preserving valuable content. |
| 2026-01-16 | **Investor Due Diligence Fix:** Added UNLIMITED response for investor questions (family office, AUM, seed, pre-money, multiple numbered questions, 100+ word questions). Investors deserve complete answers. |
| 2026-01-16 | **Conversational Tone Update:** Raised all word limits (30→80, 50→120, 100→180, 150→200, 300→350) to allow friendly, amene responses while maintaining brevity. Added list/enumeration detection. |
| 2026-01-15 | Added adaptive behavior: explanation requests get unlimited words |
| 2026-01-15 | Initial adoption after investor communication issue identified |
