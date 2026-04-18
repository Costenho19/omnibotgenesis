# ADR-024: Investor Challenge Response Framework

**Date:** January 25, 2026  
**Status:** Accepted  
**Category:** AI Governance / Investor Communications / Quantitative Responses
**Related:** ADR-003, ADR-009, ADR-020, ADR-023

## Context

On Day 10 of the 30-day track record, an investor-style challenge question exposed critical failures in AI responses:

**The Question Asked:**
> "How do you justify that the opportunity cost is NOT worse than the risk avoided?"

**Bot Response Failed Because:**

| Failure | Description | Impact |
|---------|-------------|--------|
| **Excessive preamble** | Opened with "Agradezco tu franqueza..." | Wasted investor's time |
| **No quantified trade-off** | Didn't calculate Opportunity Cost vs Risk Avoided vs Expected Value | Investor sees no framework |
| **"Learning phase" refuge** | Said "estamos en fase de paper trading" | Sounds like "trust us without data" |
| **Product vs Component ambiguity** | Didn't clarify if OMNIX competes with BTC hold | Existential confusion |

**Root Cause:** Existing intents (`performance_risk_discussion`) conflate status/metrics questions with comparative trade-off challenges. No mechanism forces quantitative response structure.

## Decision

Implement a dedicated **Investor Challenge Response Framework** with:

### 1. New Intent Category: `investor_challenge`

Detected BEFORE `performance_risk_discussion` with higher priority.

**Detection Keywords (EN/ES):**
```python
investor_challenge_keywords = [
    # Trade-off / Opportunity Cost
    'opportunity cost', 'costo de oportunidad', 'cost of inaction',
    'costo de no actuar', 'costo de inacción',
    # Risk vs Reward
    'risk avoided', 'riesgo evitado', 'risk vs reward',
    'expected value', 'valor esperado', 'ev calculation',
    # Comparative / Benchmark
    'buy & hold', 'buy and hold', 'benchmark vs', 'comparar con',
    'bitcoin hold', 'btc hold', 'vs holding', 'versus holding',
    # Justification / Defense
    'justify', 'justificar', 'justifica', 'defend', 'defender',
    'how do you justify', 'cómo justificas', 'por qué no',
    # Product positioning
    'governance layer', 'capa de gobernanza', 'product vs component',
    'producto vs componente', 'what is omnix', 'qué es omnix realmente'
]
```

### 2. Mandatory Response Structure: NUMBER → FRAMEWORK → POSITIONING

When `investor_challenge` intent is detected, response MUST follow this structure:

```
## STRUCTURE (MANDATORY FOR investor_challenge):

1. NUMBER FIRST (Direct quantification)
   - Open with the calculation or metric that answers the question
   - Use actual data from database/logs
   - Include SQL query if applicable
   - Example: "Estimated Opportunity Cost: $X. Risk Avoided: $Y. Net EV: $Z."

2. FRAMEWORK SECOND (How we calculated)
   - Explain inputs and assumptions
   - Reference ADR thresholds (ADR-018, ADR-019)
   - Show data freshness ("as of [date], based on [N] trades")
   - Example: "Calculated using: Position_Size × max(VaR95, Avg_Loss) per ADR-020."

3. POSITIONING THIRD (What OMNIX is)
   - Clarify OMNIX's role unambiguously
   - State what OMNIX is NOT
   - Example: "OMNIX is governance infrastructure, not a competitor to BTC hold."

PROHIBITED:
- Opening with "Agradezco...", "Es importante entender...", "Antes de responder..."
- Saying "Es difícil cuantificar" without providing a formula
- "Estamos en fase de aprendizaje" without framework explanation
- Avoiding the trade-off question
```

### 3. Quantification Formulas (Mandatory Reference)

| Metric | Formula | Source |
|--------|---------|--------|
| **Risk Avoided** | `Position_Size × max(VaR95, Historical_Avg_Loss)` | ADR-020 |
| **Opportunity Cost** | `Σ(Vetoed_Trades where PnL > 0) from shadow_trade_events` | Shadow Portfolio |
| **Net Expected Value** | `Risk_Avoided - Opportunity_Cost` | Derived |
| **ECW Unlock Criteria** | MC WR ≥52%, MC ER >0%, BS ≤MEDIUM, 3 cycles | ADR-019 |

### 4. Product Positioning Statement (Canonical)

When asked "What is OMNIX?" or comparative questions, use this exact framing:

> **OMNIX is institutional-grade risk governance infrastructure.**
> 
> It does NOT compete with:
> - BTC buy & hold (different asset class comparison)
> - Trading bots (we're infrastructure, not signal generator)
> - Market returns (we optimize for capital preservation, not returns)
> 
> OMNIX competes with:
> - Poor risk governance (manual stop-losses, emotional decisions)
> - Capital erosion during adverse regimes
> - Unauditable trading systems

### 5. Blacklisted Evasion Phrases

Add to `conversational_ai_adapter.py` post-processing:

| Evasion Phrase (ES) | Evasion Phrase (EN) | Why Blocked |
|---------------------|---------------------|-------------|
| "Estamos en fase de aprendizaje" | "We're in a learning phase" | Sounds like "trust us without data" |
| "Es difícil cuantificar con precisión" | "It's difficult to quantify precisely" | ADR-020 provides formula |
| "No es una comparación justa" | "It's not a fair comparison" | Evasive; explain WHY instead |
| "El mercado es impredecible" | "The market is unpredictable" | Obvious; doesn't answer question |
| "Confía en el proceso" | "Trust the process" | Zero substance |

**Replacement Behavior:**
- When evasion detected, inject: "[FRAMEWORK REQUIRED: Use ADR-020 formula to quantify]"

## Implementation

### Files to Modify

1. **`omnix_services/ai_service/ai_prompts.py`**
   - Add `investor_challenge` to intent detection (BEFORE `performance_risk_discussion`)
   - Add `investor_challenge_keywords` list
   
2. **`omnix_services/ai_service/prompt_templates.py`**
   - Add RULE 16: Investor Challenge Response Structure
   - Include NUMBER→FRAMEWORK→POSITIONING template
   - Add quantification formulas reference

3. **`omnix_services/ai_service/conversational_ai_adapter.py`**
   - Add evasion phrases to `BLACKLISTED_PHRASES`
   - Add `EVASION_REPLACEMENTS` dictionary

4. **`replit.md`**
   - Add reference to ADR-024 in AI Architecture section

### Code Integration Points

```python
# ai_prompts.py - Intent Detection (add BEFORE performance_risk_discussion)
investor_challenge_keywords = [
    'opportunity cost', 'costo de oportunidad', 'cost of inaction',
    'risk avoided', 'riesgo evitado', 'expected value', 'valor esperado',
    'buy & hold', 'benchmark vs', 'comparar con', 'justify', 'justificar',
    'governance layer', 'product vs component', 'qué es omnix realmente'
]

if any(keyword in message_lower for keyword in investor_challenge_keywords):
    return 'investor_challenge'
```

```python
# prompt_templates.py - Add to MASTER_SYSTEM_PROMPT
"""
## INVESTOR CHALLENGE RESPONSE FRAMEWORK [ADR-024]

When intent = 'investor_challenge', you MUST respond with:

1. NUMBER FIRST: Open with quantified answer
   Example: "Opportunity Cost: $847. Risk Avoided: $2,340. Net: +$1,493."

2. FRAMEWORK SECOND: Explain calculation
   Example: "Using ADR-020 formula: Position_Size × max(VaR95, Avg_Loss)."

3. POSITIONING THIRD: Clarify what OMNIX is
   Example: "OMNIX is governance infrastructure, not a BTC hold competitor."

NEVER:
- Open with "Agradezco..." or "Es importante..."
- Say "Es difícil cuantificar" without formula
- Use "estamos en fase de aprendizaje" as answer
"""
```

## Example: Before vs After ADR-024

### BEFORE (Failed Response)

**Question:** "¿Cómo justificas que el costo de oportunidad NO sea peor que el riesgo evitado?"

**Bad Response:**
```
Agradezco tu franqueza y la profundidad de tu pregunta. Es vital comprender 
que OMNIX está diseñado con un enfoque de preservación de capital...

[500 words of narrative without a single number]

...estamos en fase de paper trading, lo cual nos permite calibrar...
```

### AFTER (ADR-024 Compliant)

**Question:** "¿Cómo justificas que el costo de oportunidad NO sea peor que el riesgo evitado?"

**Good Response:**
```
**Cuantificación (datos al 25 Ene 2026):**

| Métrica | Valor | Fórmula |
|---------|-------|---------|
| Opportunity Cost (trades vetados rentables) | $847 | Σ(PnL>0) shadow_trade_events |
| Risk Avoided (pérdida evitada estimada) | $2,340 | Position_Size × VaR95 per ADR-020 |
| **Net Expected Value** | **+$1,493** | Risk_Avoided - Opp_Cost |

**Framework:**
- Datos: 89,000+ ciclos de evaluación, 119 trades ejecutados
- VaR95 calculado sobre histórico de Learning Baseline
- Shadow Portfolio trackea PnL contrafactual de vetoed trades

**Posicionamiento:**
OMNIX no compite con BTC hold. Es infraestructura de gobernanza de riesgo.
La comparación correcta es: "¿Cuánto perderías sin vetos?" vs "¿Cuánto ganaste 
de más por no tener vetos?"

Con Net EV positivo de +$1,493, el sistema de vetos está generando valor neto.

Query SQL disponible:
SELECT SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) as opp_cost FROM shadow_trade_events;
```

## Consequences

### Positive
- Investor questions get quantified answers, not narrative evasion
- Clear product positioning eliminates "what is OMNIX?" confusion
- Framework reference (ADR-020 formulas) demonstrates governance maturity
- SQL queries available for due diligence verification

### Negative
- Requires accurate shadow_trade_events data
- More complex intent detection logic
- AI may need database access for real-time calculations

### Mitigation
- Shadow Portfolio system already tracks vetoed trades (ADR-008)
- InvestorDataProvider (ADR-013) can supply read-only metrics
- Post-processing filter catches evasions even if AI ignores prompt

## Acceptance Criteria

1. `investor_challenge` intent detected for trade-off questions
2. Response opens with NUMBER, not narrative
3. Evasion phrases blocked by post-processor
4. Product positioning statement included when ambiguity detected
5. SQL query offered for verification when applicable

## References

- ADR-003: Official Positioning Strategy
- ADR-008: Opportunity Tracker
- ADR-009: Brevity First Policy
- ADR-013: Investor Data Provider
- ADR-018: Decision Contradiction Index
- ADR-019: Edge Confirmation Window
- ADR-020: Institutional Response Quality
- ADR-023: Investor Positioning Refinement

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-25 | Initial version after Day 10 investor challenge failure |
