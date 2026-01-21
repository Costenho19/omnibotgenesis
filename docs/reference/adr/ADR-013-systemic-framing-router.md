# ADR-013: Systemic Framing Router

**Status:** ADOPTED  
**Date:** January 19, 2026  
**Author:** Core Team + AI Architect  
**Supersedes:** Previous single SYSTEMIC_OVERRIDE approach  

---

## Context

OMNIX AI was using a single `SYSTEMIC_OVERRIDE_PROMPT` for ALL systemic risk questions. This caused a critical problem:

**Observed Problem (Jan 19, 2026):**
- User asked about **code defects** affecting multiple instances
- Bot opened with: "OMNIX no genera señales sincronizadas a todos los usuarios..."
- This opening is **irrelevant** to the question (code defects ≠ signal coordination)
- Bot also used numbered sections (*1. Análisis Inmediato*, *2. Datos Técnicos*) which ADR-009 prohibits

**Root Cause:**
The single override prompt relied on the AI model to self-select the correct opening based on "question type" guidance. Models ignore or misinterpret such guidance, leading to wrong framing.

**Impact:**
- Investor questions receive irrelevant disclaimers
- Responses sound like boilerplate, not thoughtful analysis
- Undermines credibility ("bot is copy-pasting the same intro")
- Violates ADR-009 Brevity First formatting rules

---

## Decision

Implement a **Systemic Framing Router** with deterministic classification:

### Architecture

```
User Question
     ↓
classify_systemic_question(message)
     ↓
Returns: TYPE_A / TYPE_B / TYPE_C / TYPE_D / None
     ↓
get_systemic_override_prompt(question_type)
     ↓
Injects type-specific override prompt
```

### Risk Type Classification

| Type | Category | Keywords | Mandatory Opening |
|------|----------|----------|-------------------|
| **A** | Coordination / Synchronization | "10,000 usuarios", "señal simultánea", "venta masiva", "coordinación", "todos reciben", "misma señal", "vendieran simultáneamente" | "OMNIX no genera señales sincronizadas a todos los usuarios..." |
| **B** | Software / Deployment | "defecto lógico", "bug", "código base", "versión del modelo", "despliegue", "patch", "actualización" | "OMNIX implementa múltiples capas de defensa contra fallos de software..." |
| **C** | Dependencies / Providers | "proveedores externos", "APIs", "datos inconsistentes", "fallo silencioso", "cloud", "exchange", "latencia" | "OMNIX valida cada fuente de datos de forma independiente..." |
| **D** | Governance / Compliance | "regulador", "compliance", "auditoría", "responsabilidad fiduciaria", "SEC", "legal", "MiFID" | "Desde una perspectiva de gobernanza y cumplimiento..." |

### Priority Order

When multiple types match, use this precedence:
1. **Type A** (Coordination) - Highest priority (most common investor concern)
2. **Type D** (Governance) - Regulatory questions are precise
3. **Type C** (Dependencies) - Provider/API questions
4. **Type B** (Software) - Lowest priority (most generic keywords)

### Type-Specific Overrides

Each type gets its own override prompt with:
- Mandatory opening phrase (cannot be changed by model)
- Required concepts for that risk type
- Forbidden patterns (from ADR-009)
- Example response

---

## Implementation

### 1. Keyword Lists

```python
SYSTEMIC_TYPE_A_KEYWORDS = [  # Coordination
    '10,000 usuarios', '10000 usuarios', '10k usuarios',
    'miles de usuarios', 'millones de usuarios',
    'venta simultánea', 'ventas simultáneas',
    'señal simultánea', 'señales simultáneas',
    'todos reciben', 'todos vendiendo', 'misma señal',
    'coordinación', 'efecto manada', 'herding',
]

SYSTEMIC_TYPE_B_KEYWORDS = [  # Software/Deployment
    'defecto lógico', 'bug', 'error en el código',
    'código base', 'code base', 'codebase',
    'versión del modelo', 'model version',
    'despliegue', 'deployment', 'deploy',
    'patch', 'actualización de software',
]

SYSTEMIC_TYPE_C_KEYWORDS = [  # Dependencies
    'proveedores externos', 'external providers',
    'api degradation', 'degradación de api',
    'datos inconsistentes', 'inconsistent data',
    'fallo silencioso', 'silent failure',
    'cloud', 'exchange', 'kraken', 'latencia',
]

SYSTEMIC_TYPE_D_KEYWORDS = [  # Governance
    'regulador', 'regulator', 'regulatory',
    'compliance', 'cumplimiento',
    'auditoría', 'audit',
    'responsabilidad fiduciaria', 'fiduciary',
    'sec', 'mifid', 'legal', 'jurisdicción',
]
```

### 2. Classifier Function

```python
def classify_systemic_question(message: str) -> Optional[str]:
    """
    Classify systemic question into type A/B/C/D.
    Returns None if not a systemic question.
    Priority: A > D > C > B
    """
    message_lower = message.lower()
    
    # Check Type A first (highest priority)
    for kw in SYSTEMIC_TYPE_A_KEYWORDS:
        if kw.lower() in message_lower:
            return 'TYPE_A'
    
    # Then Type D (governance)
    for kw in SYSTEMIC_TYPE_D_KEYWORDS:
        if kw.lower() in message_lower:
            return 'TYPE_D'
    
    # Then Type C (dependencies)
    for kw in SYSTEMIC_TYPE_C_KEYWORDS:
        if kw.lower() in message_lower:
            return 'TYPE_C'
    
    # Finally Type B (software)
    for kw in SYSTEMIC_TYPE_B_KEYWORDS:
        if kw.lower() in message_lower:
            return 'TYPE_B'
    
    return None
```

### 3. Override Selection

```python
def get_systemic_override_prompt(question_type: Optional[str]) -> str:
    """Get the appropriate override prompt for the question type."""
    if question_type == 'TYPE_A':
        return SYSTEMIC_OVERRIDE_COORDINATION
    elif question_type == 'TYPE_B':
        return SYSTEMIC_OVERRIDE_SOFTWARE
    elif question_type == 'TYPE_C':
        return SYSTEMIC_OVERRIDE_DEPENDENCIES
    elif question_type == 'TYPE_D':
        return SYSTEMIC_OVERRIDE_GOVERNANCE
    return ""  # No override for non-systemic questions
```

---

## Validation

### Test Cases

| Question | Expected Type | Expected Opening |
|----------|---------------|------------------|
| "Si 10,000 usuarios venden al mismo tiempo..." | TYPE_A | "OMNIX no genera señales sincronizadas..." |
| "¿Qué pasa si hay un defecto lógico en el código?" | TYPE_B | "Esta es una cuestión de riesgo de software..." |
| "¿Cómo manejan fallos silenciosos de APIs?" | TYPE_C | "Esta es una cuestión de resiliencia operativa..." |
| "¿Cómo se preparan para auditorías regulatorias?" | TYPE_D | "Desde una perspectiva de gobernanza..." |
| "¿Cuál es el win rate actual?" | None | (No override) |

### Regression Prevention

Test suite must verify:
1. Each keyword triggers correct type
2. Priority order is respected (A > D > C > B)
3. Correct opening phrase in each override
4. No numbered sections in any override
5. Monitoring clarification present when needed

---

## Consequences

### Positive

- Deterministic classification (no model guessing)
- Relevant openings for each risk category
- Scalable to new risk types
- Testable and auditable
- Compliant with ADR-009 (no numbered sections)

### Negative

- More code to maintain (4 overrides vs 1)
- Keywords may need periodic updates
- Overlapping questions may classify to "wrong" type

### Mitigation

- Priority order resolves overlaps consistently
- Test suite catches regressions
- Keywords reviewed quarterly with investor feedback

---

## References

- ADR-009: Brevity First Policy
- ADR-003: Official Positioning Strategy
- ADR-014: Provider Resilience Enhancement (TYPE_C improvements)
- docs/reference/omnix_official_language.md

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-21 | Added prompt leaking protection: BLACKLISTED_PATTERNS filter + reformatted prompts with "RESPONSE FOCUS" instead of "MANDATORY OPENING (use EXACTLY)" |
| 2026-01-21 | Keywords refined: TYPE_C now requires failure context (e.g., "fallo de kraken" not just "kraken") |
| 2026-01-19 | Initial adoption after investor testing revealed wrong framing |
