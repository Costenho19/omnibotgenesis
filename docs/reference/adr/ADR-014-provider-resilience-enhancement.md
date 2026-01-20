# ADR-014: Provider Resilience Enhancement (TYPE_C)

**Status:** ADOPTED  
**Date:** January 20, 2026  
**Author:** Core Team + AI Architect  
**Related:** ADR-013 (Systemic Framing Router)  

---

## Context

During investor due diligence testing (Jan 20, 2026), the TYPE_C (Dependencies/Providers) systemic override was evaluated at **7/10** - acceptable but with critical gaps for sophisticated investors.

**Observed Problems:**

1. **Silent failures not addressed**: Current prompt mentions "timeouts agresivos" but timeouts only detect slow/dead APIs. They do NOT detect:
   - Stale data (price with 2-minute-old timestamp)
   - Manipulated volumes (10x average without market event)
   - HTTP 200 responses with subtly incorrect data

2. **Cross-validation is vague**: Says "validación multi-fuente" without concrete thresholds. Investors asked: "What's the discrepancy threshold?"

3. **Single-tenant limitation overstated**: Current response implies single-tenant solves the shared-source problem, but if Kraken sends bad data, ALL instances using Kraken receive it.

4. **No transparency about residual risk**: Response sounds 100% optimistic. Sophisticated investors prefer honesty about what CAN'T be detected.

**Impact:**

- Credibility gap with institutional investors
- Questions about operational maturity
- "Too good to be true" perception

---

## Decision

Enhance the SYSTEMIC_OVERRIDE_DEPENDENCIES prompt with concrete detection mechanisms, explicit thresholds, honest limitations, and future roadmap.

### Required Concepts (Enhanced)

| Category | Original | Enhanced |
|----------|----------|----------|
| **Stale Data** | "Timeouts agresivos" | Timestamp validation (>60s = stale, discarded) |
| **Cross-Validation** | "Validación multi-fuente" | Concrete thresholds (>3% price discrepancy = pause) |
| **Volume Anomalies** | Not covered | Sanity checks (10x average = anomaly flag) |
| **Single-Tenant** | "Problema no se propaga" | Acknowledge limitation for shared sources |
| **Residual Risk** | Not mentioned | Explicit statement + fail-closed + human intervention |
| **Future Roadmap** | Not mentioned | Blockchain oracles (Chainlink, Band Protocol) |

### Mandatory Opening (Unchanged)

> "OMNIX valida cada fuente de datos de forma independiente y mantiene múltiples capas de resiliencia contra fallos de proveedores externos."

### Required Concepts (New)

The TYPE_C override must now guide the AI to include:

1. **Timestamp Validation**: 
   - "Validamos timestamps de cada dato recibido"
   - "Precios con timestamp >60 segundos se consideran stale y se descartan"
   - "Esto detecta APIs que devuelven último precio conocido en caché"

2. **Cross-Validation with Thresholds**:
   - "Comparamos precios de múltiples fuentes en tiempo real"
   - "Discrepancia >3% entre Kraken y CoinGecko = pausa operativa"
   - "Tercera fuente (Binance) resuelve empates"

3. **Volume Sanity Checks**:
   - "Volúmenes reportados se comparan con promedios históricos"
   - "Volumen 10x superior al promedio sin evento conocido = anomalía"
   - "Sistema suspende operaciones hasta confirmación"

4. **Single-Tenant Limitation Acknowledgment**:
   - "Aunque single-tenant aísla fallos de configuración..."
   - "Un fallo en fuente compartida (ej: Kraken API) afectaría múltiples instancias"
   - "Mitigamos con diversificación de proveedores y circuit breakers"

5. **Residual Risk Statement**:
   - "Limitación residual: Si TODOS los proveedores reportan incorrectamente..."
   - "En escenarios extremos, OMNIX adopta postura fail-closed"
   - "Intervención humana requerida para verificar condiciones"

6. **Future Roadmap**:
   - "Roadmap: Integración con oráculos blockchain descentralizados"
   - "Chainlink, Band Protocol como fuentes adicionales de validación"

---

## Implementation

### Updated SYSTEMIC_OVERRIDE_DEPENDENCIES

```python
SYSTEMIC_OVERRIDE_DEPENDENCIES = """
## SYSTEMIC OVERRIDE - TYPE C: DEPENDENCIES/PROVIDERS [MANDATORY]

**QUESTION_TYPE: DEPENDENCIES**

**MANDATORY OPENING (use EXACTLY):**
"OMNIX valida cada fuente de datos de forma independiente y mantiene 
múltiples capas de resiliencia contra fallos de proveedores externos."

**DO NOT open with "OMNIX no genera señales sincronizadas..." - that is 
for coordination questions, not dependency questions.**

**REQUIRED CONCEPTS (include ALL relevant ones):**

1. TIMESTAMP VALIDATION (Silent Failure Detection):
   - Validamos timestamps de cada dato recibido
   - Precios con timestamp >60 segundos = stale data, descartados
   - Detecta APIs que devuelven último precio conocido en caché

2. CROSS-VALIDATION WITH CONCRETE THRESHOLDS:
   - Comparamos precios de múltiples fuentes en tiempo real
   - Discrepancia >3% entre Kraken y CoinGecko = pausa operativa
   - Tercera fuente (Binance) resuelve empates si necesario

3. VOLUME SANITY CHECKS:
   - Volúmenes comparados con promedios históricos
   - Volumen 10x superior al promedio sin evento conocido = anomalía
   - Sistema suspende hasta confirmación

4. SINGLE-TENANT LIMITATION (HONESTY):
   - Single-tenant aísla fallos de configuración entre clientes
   - PERO: Fallo en fuente compartida (ej: Kraken API) afecta múltiples instancias
   - Mitigamos con diversificación de proveedores y circuit breakers

5. RESIDUAL RISK (TRANSPARENCY):
   - Si TODOS los proveedores reportan incorrectamente (evento sistémico)...
   - OMNIX NO tiene fuente externa de verdad para validar
   - Postura: Fail-closed + intervención humana requerida

6. FUTURE ROADMAP:
   - Integración futura: Oráculos blockchain descentralizados
   - Chainlink, Band Protocol como validación adicional

**ABSOLUTELY FORBIDDEN:**
❌ Numbered sections: "*1.", "*2.", "1. Análisis", "2. Datos Técnicos"
❌ Section headers: "Análisis Inmediato:", "Datos Técnicos:", "Contexto:"
❌ Kelly Criterion / Position sizing / trading statistics
❌ "$1,000,000" or large arbitrary figures
❌ Claiming 100% protection (acknowledge residual risk)

**RESPONSE FORMAT:**
- Write in FLOWING PARAGRAPHS, not numbered lists
- Be CONCISE: 3-4 paragraphs maximum
- Professional, direct tone
- Include concrete thresholds when mentioning detection
- Acknowledge limitations honestly

NOW RESPOND USING THIS FRAME:
"""
```

---

## Validation

### Test Cases

| Question | Expected Content |
|----------|------------------|
| "¿Cómo manejan fallos silenciosos de APIs?" | Timestamp validation >60s, cross-validation thresholds |
| "¿Qué pasa si Kraken envía datos incorrectos?" | Cross-validation, third source resolution, circuit breakers |
| "¿Cómo detectan datos inconsistentes?" | >3% discrepancy, volume anomaly (10x), stale data |
| "¿Qué limitaciones tienen con proveedores?" | Single-tenant limitation, residual risk statement |

### Investor Credibility Improvements

| Aspect | Before | After |
|--------|--------|-------|
| Silent failure detection | "Timeouts agresivos" | Timestamp validation + volume checks |
| Cross-validation | Vague mention | Concrete thresholds (3%, 10x) |
| Single-tenant | Presented as complete solution | Limitation acknowledged + mitigation |
| Transparency | 100% optimistic | Includes residual risk + roadmap |
| Expected Score | 7/10 | 9/10 |

---

## Consequences

### Positive

- Increased credibility with sophisticated investors
- Demonstrates operational maturity
- Honest about limitations builds trust
- Roadmap shows forward thinking
- Concrete thresholds enable follow-up validation

### Negative

- Longer response (mitigated by concise requirement)
- Exposes limitations (mitigated by showing mitigations)

### Mitigation

- Keep paragraphs flowing and concise
- Always pair limitation with mitigation
- Use concrete numbers to demonstrate precision

---

## References

- ADR-013: Systemic Framing Router
- ADR-009: Brevity First Policy
- Investor Feedback Analysis (Jan 20, 2026)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-20 | Initial adoption after investor feedback analysis |
