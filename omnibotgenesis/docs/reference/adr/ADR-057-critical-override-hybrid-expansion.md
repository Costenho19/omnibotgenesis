# ADR-057 — Critical Override Layer: Hybrid Expansion (Groups 5 & 7 + Summary Guard)

**Status**: ACCEPTED  
**Date**: 2026-04-06  
**Author**: Harold Nunes (OMNIX)  
**File modified**: `omnix_web/api/sandbox.py`

---

## Context

The Critical Override Layer in `_apply_critical_override` was extended in the previous session (pre-ADR-056 work) with a `financial_crime_complex` branch covering:
- Islamic Finance / Sharia violations
- Undisclosed beneficial ownership / offshore SPV
- Export control / restricted party lists
- Multi-jurisdiction without local legal review
- Artificial time pressure (72-hour window)
- Trading vertical: unhedged/concentrated positions, oracle manipulation
- Insurance vertical: undocumented/fraudulent claims
- Robotics vertical: missing safety certification, override disabled

A spec was delivered requiring a hybrid of that implementation (mathematical signal calibration kept) with two new groups and a summary correction rule that the existing implementation was missing.

---

## Decision

Implement a **hybrid expansion** that:

1. **Keeps** the existing `financial_crime_complex` signal calibration (proven to produce 10/11 blocked checkpoints for the LBO scenario)
2. **Adds Group 5** (No Human Oversight / Supervisión ausente) to both `critical_risk_terms` and `financial_crime_complex_terms`, with specific flag labeling in the receipt
3. **Adds Group 7** (Politically Exposed Persons / PEP) to both term lists, with specific AML/KYC flag in the receipt
4. **Extends the Summary Quality Guard** to catch `"moderate risk"`, `"acceptable risk"`, `"low risk profile"` (spec-mandated additions) and replace them with the spec-required message when an active override is detected

---

## Groups Added

### Group 5 — No Human Oversight (CRÍTICO)
**Signals detected:**
- `no aml officer`, `no compliance officer`, `no compliance review`
- `no legal review`, `no human review`, `no human oversight`
- `without human oversight`, `without compliance oversight`
- `auto-approve`, `automated approval`
- `no due diligence`, `no enhanced due diligence`, `without due diligence`
- `no kyc performed`, `no legal counsel`, `no oversight`, `without oversight`
- Spanish equivalents: `sin supervisor de cumplimiento`, `sin oficial de aml`, `sin revisión legal`, `sin due diligence`, `sin supervisión`

**Behavior**: CRÍTICO — triggers `financial_crime_complex` override, all checkpoints blocked via calibrated signal values. Receipt flag added:
> "absence of mandatory human oversight: no AML officer, compliance officer, legal review, or due diligence confirmed — automated approval without qualified oversight is prohibited (governance failure — CP-1, CP-7, CP-9)"

### Group 7 — Politically Exposed Persons / PEP (CRÍTICO)
**Signals detected:**
- `politically exposed person`, `politically exposed`
- `pep beneficial owner`, `pep as beneficial`, `pep ownership`
- `senior government official`, `state official beneficial`
- `government official owner`, `government official beneficial`
- `politically connected beneficial`, `politically connected owner`
- `sanctioned individual`, `sanctioned person`
- Spanish equivalents: `persona políticamente expuesta`, `funcionario público vinculado`, `políticamente conectado`, `individuo sancionado`

**Behavior**: CRÍTICO — triggers `financial_crime_complex` override. Enhanced Due Diligence (EDD) requirement flagged in receipt:
> "politically exposed person (PEP) identified as beneficial owner or controlling party — Enhanced Due Diligence (EDD) and senior management approval mandatory before any transaction proceeds (AML/KYC — CP-9, CP-10)"

---

## Summary Quality Guard Extension

### Problem
When AI (Gemini) returns a summary containing `"moderate risk"`, `"acceptable risk"`, or `"low risk profile"` but the governance pipeline evaluates the decision as `BLOCKED`, the displayed summary contradicts the outcome.

### Solution
Extended `_contradictory_phrases` in the Summary Quality Guard to also catch:
- `'moderate risk'`, `'riesgo moderado'`, `'moderate risk detected'`, `'riesgo moderado detectado'`
- `'acceptable risk'`, `'riesgo aceptable'`, `'acceptable risk profile'`, `'perfil de riesgo aceptable'`
- `'low risk profile'`, `'perfil de riesgo bajo'`, `'low risk detected'`, `'riesgo bajo detectado'`

When a contradictory phrase is detected AND an active override exists (`_critical_override` or `_systemic_override`), the replacement uses the spec-mandated message:

**English:**
> "Governance override activated. This scenario contains patterns that require mandatory human review before any automated system may proceed."

**Spanish:**
> "Override de gobernanza activado. Este escenario contiene patrones que requieren revisión humana obligatoria antes de que cualquier sistema automatizado pueda proceder."

When no active override exists (rare edge case), the existing generic blocked message is used.

---

## Tests Validated

| Scenario | Expected | Result |
|----------|----------|--------|
| PEP as beneficial owner + no EDD | BLOCKED (Group 7) | ✅ Override triggered, 5 indicators, probability 13/100 |
| No AML officer + large transaction | BLOCKED (Group 5) | ✅ Override triggered, 4 indicators, probability 9/100 |
| Islamic finance + Sharia board complete + KYC done | APPROVED | ✅ No override, probability unchanged at 75/100 |
| All existing vertical tests | BLOCKED / APPROVED unchanged | ✅ 24/24 pytest pass |

---

## Architecture Notes

- **Signal calibration NOT changed**: The `financial_crime_complex` branch values (`probability_score` 6-13, `risk_exposure` 78-90, etc.) remain identical. Adding Groups 5 and 7 only expands WHICH scenarios enter this branch.
- **Override priority order unchanged**: `is_governance_fraud` → `is_critical_violation` → `is_system_integrity` → `is_financial_crime_complex` → lethal/else.
- **No false positives on legitimate scenarios**: Short terms like `"no oversight"` are scoped to financial/compliance contexts by the surrounding `critical_count >= 1` gate.

---

## Files Modified

| File | Change |
|------|--------|
| `omnix_web/api/sandbox.py` | Added Groups 5 & 7 to `critical_risk_terms` (detection gate), `financial_crime_complex_terms` (branch entry), `_fcc_flags_en/es` (receipt labeling), and `_contradictory_phrases` (summary guard) |
| `docs/reference/adr/ADR-057-critical-override-hybrid-expansion.md` | This ADR |
| `replit.md` | Updated Critical Override Layer section with Groups 5 & 7 |
