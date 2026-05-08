# ADR-108 — Institutional Language Enforcement in AI Responses

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-23 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_services/ai_service/ai_prompts.py` · `omnix_services/telegram_service/enterprise_bot.py` |
| **Replaces** | — |

---

## Context

AI-generated governance explanations and Telegram bot responses used inconsistent terminology that undermined institutional credibility. Specific problems observed in investor demos:

- "The trade looks risky" → should be "The evaluated operation presents elevated systemic exposure"
- "Blocked because the market is volatile" → should be "Decision outcome: BLOCKED. Primary veto trigger: volatility threshold breach (AVM-74)"
- Casual tone in AI reasoning traces visible to auditors
- Inconsistent use of governance terminology across domains (e.g., "rejected" vs "BLOCKED" vs "denied")

## Decision

Implement a language enforcement layer applied to all AI-generated output before delivery.

### Canonical terminology

| Informal | Canonical |
|---|---|
| Blocked / rejected / denied | `BLOCKED` (all-caps in outcomes) |
| Approved / passed / accepted | `APPROVED` |
| On hold / pending | `HOLD` |
| Risky / dangerous | "presents elevated [signal] exposure" |
| Bad signal | "signal integrity below governance threshold" |
| The AI thinks | "The governance engine evaluated" |

### Enforcement mechanism

A `InstitutionalLanguageFilter` post-processor applies regex-based term substitutions and tone scoring:

```python
class InstitutionalLanguageFilter:
    def apply(self, text: str, context: str = "general") -> str:
        text = self._normalize_outcome_terms(text)
        text = self._elevate_tone(text)
        text = self._enforce_governance_citations(text)
        return text
```

### Governance citation requirement

Any AI explanation referencing a governance decision must include the relevant ADR citation:

> "Signal integrity validation (ADR-033) flagged divergence between primary and secondary price sources, triggering a HOLD decision."

## Consequences

**Positive:**
- Investor demos and audit reviews present a consistent, institutional-grade voice.
- Regulatory examiners see governance terminology aligned with the ADR framework.

**Negative:**
- Over-aggressive term replacement can produce awkward constructions; threshold tuning required.

## Related

- ADR-020: Institutional Response Quality
- ADR-017: Final Decision Reason Summary
- ADR-009: Brevity-First Policy
