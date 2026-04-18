# ADR-023: Investor Positioning Refinement

**Status**: ADOPTED  
**Date**: January 23, 2026  
**Author**: OMNIX Team  
**Category**: Business / Investor Relations

---

## Context

Following external feedback on investor documentation, several language refinements were identified to reduce regulatory risk and improve institutional credibility. The core content and technical claims remain unchanged—only the framing was adjusted.

## Decision

Adopt the following positioning refinements across all investor-facing documentation:

### 1. Remove "INSTITUTIONAL+" from Public Headers

| Before | After |
|--------|-------|
| V6.5.4e INSTITUTIONAL+ | V6.5.4e Advanced Tier |

**Rationale**: "Institutional" implies regulatory status that may not apply. "Advanced Tier" conveys sophistication without compliance risk.

### 2. Soften PQC Claims

| Before | After |
|--------|-------|
| "First retail platform with post-quantum cryptography" | "One of the first advanced trading platforms experimenting with NIST-aligned post-quantum cryptography standards" |

**Rationale**: "Experimenting with" provides legal protection while maintaining the technical truth that PQC is implemented and operational.

### 3. Avoid Direct Firm Comparisons

| Before | After |
|--------|-------|
| "Citadel/Jump Trading-level execution" | "Execution protocols inspired by institutional liquidity management techniques (TWAP/VWAP/ICEBERG)" |

**Rationale**: Never compare directly with regulated top-tier firms. "Inspired by" acknowledges influence without implying equivalence.

### 4. Reinforce Core Messaging

Three themes to repeat consistently:

| Theme | Key Phrase |
|-------|------------|
| **Capital Preservation** | "Risk-first", "Fail-closed", "Capital protection over returns" |
| **Auditability** | "Every decision is logged, traceable, and reviewable" |
| **Strategic Discipline** | "We intentionally delayed live capital deployment to validate risk behavior" |

### 5. Remove/Freeze Topics

| Topic | Status | Reason |
|-------|--------|--------|
| Tokenization | FROZEN | Not implemented, distracts from infrastructure focus |
| "Democratizing finance" | REMOVED | Regulatory risk, retail mass-market connotation |
| Yield promises | REMOVED | Compliance risk |
| Guaranteed returns | REMOVED | Compliance risk |

### 6. Document Classification

All investor documents should include:

```
**Classification**: Investor Confidential
```

This signals controlled distribution without legal implications.

### 7. Track Record Period Disclosure (Added Jan 24, 2026)

**Mandatory disclosure when reporting any trading metrics.**

| Period | Dates | Trades | P&L | Purpose |
|--------|-------|--------|-----|---------|
| **Learning Baseline** | Nov 2025 - 14 Ene 2026 | 119 | -$15,198.73 | Calibration phase |
| **Track Record Oficial** | 15 Ene 2026 - present | ~0 | $0 | Validation with recalibrated parameters |

**Disclosure Rule**: Whenever AI reports P&L, win rate, trade counts, or symbol performance, it MUST include:

> **Nota de Período**: Estos datos corresponden al Learning Baseline (Nov-Dic 2025), fase de calibración. Desde el 15 de enero 2026, el sistema opera con parámetros recalibrados en el Track Record Oficial.

**Triggers requiring disclosure**:
- P&L amounts (e.g., -$15,198, -$3,847)
- Win rate percentages (e.g., 20.2%, 0%)
- Trade counts (e.g., 119 trades, 16 losses)
- Symbol performance analysis (e.g., "ADA/USD losses")

**Exceptions** (no disclosure needed):
- Greetings, commands, technical questions without metrics
- Architecture explanations

**Rationale**: Prevents investor confusion between calibration data and official track record. The Learning Baseline was intentionally aggressive to stress-test risk systems; the Official Track Record applies recalibrated, conservative parameters.

---

## Documents Updated

| Document | Changes |
|----------|---------|
| `docs/business/investor/PRODUCT_OVERVIEW.md` | Header, PQC language, classification |
| `docs/business/investor/RISK_GUARDIAN_PRODUCT.md` | Header, Auditability section, PQC language |
| `docs/business/investor/TRACK_RECORD_CASE_STUDY.md` | Header, Strategic Discipline section |
| `docs/business/investor/PITCH_DECK_OUTLINE.md` | NEW - 12-slide structure for investor presentations |

---

## New Positioning

### Primary Identity

> **OMNIX = AI Capital & Risk Orchestration Engine**

Not: "trading bot", "algo system", "DeFi platform"

### Value Proposition

> "Preserve capital before optimizing returns"

### Credibility Statement

> "We delayed live capital deployment to validate risk behavior. This is discipline, not hesitation."

---

## Consequences

### Positive

- Reduced regulatory exposure in investor communications
- Clearer institutional positioning
- Stronger credibility through discipline narrative
- Auditability positioned as competitive moat

### Negative

- Slightly softer technical claims (necessary for compliance)
- "Experimenting with" may understate PQC maturity (acceptable trade-off)

### Neutral

- Core technical architecture unchanged
- All capabilities remain as documented
- Only framing adjusted

---

## Implementation Checklist

- [x] Update PRODUCT_OVERVIEW.md headers and PQC language
- [x] Update RISK_GUARDIAN_PRODUCT.md with Auditability section
- [x] Update TRACK_RECORD_CASE_STUDY.md with Strategic Discipline section
- [x] Create PITCH_DECK_OUTLINE.md with 12-slide structure
- [x] Add "Investor Confidential" classification to all investor docs
- [x] Update docs/README.md with links to investor documentation
- [x] Create this ADR for traceability
- [x] Add Track Record Period Disclosure rules to system_state_manifest.json (Jan 24, 2026)
- [x] Update prompt_templates.py with mandatory disclosure rule (Jan 24, 2026)

---

## References

- `docs/business/investor/PRODUCT_OVERVIEW.md`
- `docs/business/investor/RISK_GUARDIAN_PRODUCT.md`
- `docs/business/investor/TRACK_RECORD_CASE_STUDY.md`
- `docs/business/investor/PITCH_DECK_OUTLINE.md`
- External feedback: Investor documentation review (Jan 23, 2026)
