# ADR-020: Institutional Response Quality Standards

**Date:** January 21, 2026  
**Status:** Accepted  
**Category:** AI Governance / Investor Communications / Quality Assurance

## Context

During Day 7 of the 30-day track record, an investor-style question revealed several quality issues in AI responses:

1. **Inflated unauditable figures**: Bot claimed "$82,940,000 en capital protegido" and "$240,000 en últimas 48 horas" - impossible to verify on Day 7
2. **Unrealistic thresholds**: Bot stated "WR > 60%, ER > 1%" for execution - contradicts ADR-018's realistic thresholds
3. **Arbitrary language**: "Módulos ignorados conscientemente" sounds like manual override, not governance
4. **Missing unlock criteria**: No mention of ECW (ADR-019) conditions for exiting HOLD
5. **Vague loss calculation**: "Es difícil cuantificar" when ADR-018 provides explicit formula

These issues could undermine investor confidence and suggest lack of rigor.

## Decision

Implement a multi-layer response quality system:

### Layer 1: Post-Processing Filter (Safety Net)

Added to `conversational_ai_adapter.py`:

**Blacklist Patterns (removed from responses):**
- Large capital protection claims ($82M+, $240K in 48h)
- "Es difícil cuantificar" phrases
- Unrealistic threshold claims (WR > 60%, ER > 1%)

**Language Replacements:**
| Original | Replacement |
|----------|-------------|
| "Módulos ignorados conscientemente" | "Señales ponderadas adaptativamente según marco de gestión de riesgo" |
| "Es difícil cuantificar con precisión" | "Bajo supuestos conservadores (Position_Size × max(VaR95, Avg_Loss)), el rango estimado es" |
| "win rate debe superar el 60%" | "win rate debe superar el 52%" |

### Layer 2: Prompt Template Rules (Prevention)

Added RULE 15 to `prompt_templates.py`:

**Realistic Thresholds (ADR-018):**
| Metric | Minimum | NEVER SAY |
|--------|---------|-----------|
| MC Win Rate | > 50% (target ≥52%) | "WR > 60%" |
| MC Expected Return | > 0% | "ER > 1%" or "ER > 5%" |
| Coherence | > 50% | "Perfect coherence" |
| DCI | < 70 | "High DCI to trade" (inverted logic) |
| Black Swan | LOW/NONE | Omit this gate |

**ECW Unlock Criteria (ADR-019):**
1. MC Win Rate ≥ 52% (2% above break-even)
2. MC Expected Return > 0% (any positive edge)
3. Black Swan ≤ MEDIUM
4. **3 consecutive cycles** meeting all conditions

**Loss Avoidance Formula:**
```
Est. Loss Avoided = Position_Size × max(VaR95, Historical_Avg_Loss)
```

Example response: "Bajo supuestos conservadores, el rango de pérdida evitada se estima entre $92 y $516 basado en VaR95 y datos históricos del asset."

### Layer 3: Prohibited Patterns

**NEVER include in responses:**
- ❌ "Es difícil cuantificar la pérdida evitada"
- ❌ Unaudited large figures ($82M protected, $240K in 48 hours)
- ❌ "Módulos ignorados conscientemente"
- ❌ Unrealistic thresholds (WR 60%, ER 1-5%)
- ❌ "Years of data" when we have days

## Implementation

### Files Changed

1. **`omnix_services/ai_service/conversational_ai_adapter.py`**
   - Added blacklist patterns for inflated capital figures
   - Added `LANGUAGE_REPLACEMENTS` dictionary
   - Updated `post_process_response()` to apply language transforms

2. **`omnix_services/ai_service/prompt_templates.py`**
   - Added RULE 15: Realistic Thresholds & Unlock Criteria
   - Documents ADR-018 thresholds and ADR-019 ECW criteria
   - Provides loss avoidance formula with example

### Testing

Post-processing filter can be tested with:
```python
from omnix_services.ai_service.conversational_ai_adapter import post_process_response

# Test inflated figure removal
response = "El sistema ha protegido $82,940,000.00 en capital."
cleaned = post_process_response(response)
assert "$82,940,000" not in cleaned

# Test language replacement
response = "Los módulos fueron ignorados conscientemente."
cleaned = post_process_response(response)
assert "ponderadas adaptativamente" in cleaned
```

## Consequences

### Positive
- Investor responses are now consistent with documented architecture (ADR-018, ADR-019)
- No unverifiable claims that could backfire during due diligence
- Clear unlock criteria explain HOLD → execution transition
- Loss avoidance uses auditable formula, not vague language

### Negative
- Slightly reduced flexibility in AI responses
- Post-processing adds minimal latency (~1ms)

### Neutral
- Requires ongoing maintenance if new problematic patterns emerge

## References

- ADR-018: Decision Contradiction Index (DCI)
- ADR-019: Edge Confirmation Window (ECW)
- ADR-009: Brevity First Policy
- ADR-013: Systemic Framing Router
