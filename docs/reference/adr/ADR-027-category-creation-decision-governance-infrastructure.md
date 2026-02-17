# ADR-027: Category Creation — Decision Governance Infrastructure

**Status**: ADOPTED  
**Date**: February 17, 2026  
**Author**: Harold Nunes, OMNIX Team  
**Category**: Business / Strategic Positioning  
**Supersedes**: ADR-025 (extends, does not replace)

---

## Context

ADR-025 repositioned OMNIX from "AI Capital & Risk Orchestration Engine" to "AI Decision Governance Platform." This was correct directionally but insufficient strategically.

OMNIX should not compete in the existing "Fintech AI" category. OMNIX should **create** the category of **Decision Governance Infrastructure**.

### Why Create a Category vs. Compete in One

| Competing in "Fintech AI" | Creating "Decision Governance Infrastructure" |
|---------------------------|-----------------------------------------------|
| 500+ startups in the category | No direct competitors — OMNIX defines the rules |
| Compared against trading bots, robo-advisors | Compared against nothing (new category) |
| Conversation: "How much return?" | Conversation: "How much risk without governance?" |
| Differential dilutes as "features" | Architecture IS the product |
| Single-vertical TAM ($18.8B) | Multi-vertical TAM ($37.3B+) |
| Investors see tool | Investors see platform/infrastructure |
| Fintech multiples | Infrastructure multiples (significantly higher) |

### Historical Parallel

Just as payment infrastructure became necessary before e-commerce could scale, governance infrastructure will become necessary before automated decision systems can scale.

This is the correct analogy. **Never say**: "We are the Stripe of governance." That sounds pitchy. Instead, state the structural parallel without naming companies.

## Decision

Reposition OMNIX from:

| Before (ADR-025) | After (ADR-027) |
|-------------------|-----------------|
| "AI Decision Governance Platform" | **"Decision Governance Infrastructure for Automated Systems"** |
| Competing in Fintech AI | **Creating the category of Decision Governance Infrastructure** |
| "OMNIX is a platform" | **"OMNIX is building a new category"** |
| Investor question: "How much alpha?" | **Investor question: "How much risk exists without governance?"** |

### New Canonical Definition

> OMNIX is a governance control architecture for automated decision systems. It is building the category of Decision Governance Infrastructure. The first validated vertical is digital asset trading.

### New Platform Identity

> Decision Governance Infrastructure for Automated Systems

### New Tagline

> "Governing Decisions Under Uncertainty" *(unchanged from ADR-025)*

### Investor One-Liner

> OMNIX builds the governance layer for automated decision systems. First validated in digital asset trading.

### Investor Question Reframe

| Old Frame | New Frame |
|-----------|-----------|
| "How much alpha does OMNIX generate?" | "How much capital risk exists in automated systems without governance control?" |
| "What's your return?" | "What happens to capital when governance is absent?" |
| "Compare to buy & hold" | "Compare governed vs ungoverned decision systems" |

## Mandatory Language Rules

### ALWAYS Use

- "Decision Governance Infrastructure" (the category name)
- "governance control architecture for automated decision systems" (canonical definition)
- "building the category" or "building a new category" (not "leading" or "dominating")
- "first validated vertical is digital asset trading" (grounded in evidence)
- "the governance layer for automated decision systems" (structural description)

### NEVER Use

- "OMNIX is the global leader in Decision Governance Infrastructure" (sounds vacuous)
- "We are the Stripe/Plaid/Palantir of governance" (pitchy)
- "AI-powered trading governance system" (old framing, limits scope)
- "We created a new category" (past tense implies it already exists — use "building")
- "Fintech AI platform" (puts us in wrong competitive set)
- Any language implying the category is already recognized by the market

### Category-Creation Discipline

| Do | Don't |
|----|-------|
| "OMNIX is building a new category: Decision Governance Infrastructure" | "OMNIX is the leader in Decision Governance Infrastructure" |
| "A control layer for automated decision systems" | "The world's first governance platform" |
| "We're defining what governance means for automated systems" | "Everyone recognizes our category" |

## Constraints (ALL PRESERVED)

### Numbers — UNCHANGED (from ADR-025)

All existing metrics remain exactly as documented:

| Metric | Value | Status |
|--------|-------|--------|
| Raising | $500,000 USD | Unchanged |
| Equity | 16.7% | Unchanged |
| Pre-Money Valuation | $2.5M-$3M | Unchanged |
| Capital Preserved | 98.5% | Unchanged |
| Max Drawdown | 1.5% | Unchanged |
| Decision Cycles | 192,000+ | Unchanged |
| P&L (Learning Baseline) | -$15,198.73 | Unchanged |

### Rules Still Binding

- ADR-023: No yield promises, no direct comparisons, mandatory Track Record Period Disclosure
- ADR-024: Investor Challenge Response Framework (number first, framework second, positioning third)
- ADR-025: Crypto = first validated vertical, not removed; expansion = roadmap, not current
- ADR-026: Multi-Vertical Governance Architecture (Domain Adapter pattern)

### Honesty — UNCHANGED

- "First validated vertical" discipline preserved
- No claims of operation in non-trading verticals
- Credit/Insurance demos are INTERACTIVE DEMONSTRATIONS, not operational governance
- "Building" language, never "proclaimed supremacy"

## What Changes

### 1. Homepage Headline

| Before | After |
|--------|-------|
| "AI Decision Governance Platform" | **"Decision Governance Infrastructure for Automated Systems"** |

### 2. Pitch Narrative (Eureka Slide 1)

| Before | After |
|--------|-------|
| "AI Decision Governance Platform" | **"Decision Governance Infrastructure"** |
| "AI-powered decision governance" | **"OMNIX builds the governance layer for automated decision systems. First validated in digital asset trading."** |

### 3. Bot Identity (MASTER_SYSTEM_PROMPT)

| Before | After |
|--------|-------|
| "governance control architecture for automated decision systems" | Add: **"It is building the category of Decision Governance Infrastructure."** |

### 4. Investor Framing

| Before | After |
|--------|-------|
| "How much alpha?" | **"How much capital risk exists in automated systems without governance control?"** |

## What Does NOT Change

- Honesty discipline and Track Record Period Disclosure
- "First validated vertical" — always present
- Claims discipline — no overpromising non-validated verticals
- All ADR-023/024 rules still binding
- All numbers and metrics
- Technical architecture (zero engineering changes)
- Dubai/ADGM go-to-market strategy

## Documents to Update

| Document | Change |
|----------|--------|
| `replit.md` | Overview identity line |
| `docs/README.md` | Positioning line |
| `docs/reference/omnix_official_language.md` | Full refresh: definition, approved phrases, category language |
| `docs/reference/adr/ADR-003-official-positioning.md` | Update definition to DGI |
| `docs/reference/adr/ADR-025-decision-governance-platform.md` | Note extension by ADR-027 |
| `docs/business/OMNIX_EUREKA_PITCH_FINAL.md` | Slide 1 title, solution framing |
| `docs/business/OMNIX_EUREKA_PITCH_FINAL_ES.md` | Same in Spanish |
| `docs/business/OMNIX_BUSINESS_MODEL_CANVAS.md` | Headline |
| `docs/business/investor/PRODUCT_OVERVIEW.md` | Title, core identity |
| `docs/business/investor/PITCH_DECK_OUTLINE.md` | Slide 1, solution |
| `docs/business/investor/one_pager.md` | Opening definition |
| `docs/business/investor/INVESTOR_FAQ.md` | Add governance framing Q/A |
| `docs/business/investor/NARRATIVE_CONSISTENCY.md` | Update matrix |
| `docs/business/EXECUTIVE_FACT_SHEET.md` | Add identity line |
| `omnix_services/ai_service/prompt_templates.py` | Canonical definition |
| `omnix_services/ai_service/ai_prompts.py` | Bot identity |
| `omnix_config/system_state_manifest.json` | platform_identity |
| `omnix_web/src/pages/CommercialLanding.tsx` | Already updated |
| `omnix_web/src/pages/InstitutionalPage.tsx` | Already updated |

## Consequences

### Positive

- **Category ownership** — OMNIX defines the competitive landscape, not reacts to it
- **Higher valuation multiples** — Infrastructure companies trade at higher multiples than fintech tools
- **Expanded investor narrative** — "How much risk without governance?" is a stronger conversation
- **Natural multi-vertical framing** — Category is inherently domain-agnostic
- **Defensible positioning** — First to define = first mover advantage in narrative

### Negative

- **Requires market education** — Category doesn't exist yet, investors may not understand immediately
- **Risk of appearing unfocused** — Mitigated by "first validated vertical" discipline
- **"Building" language may seem premature** — Mitigated by 192,000+ governed decisions as evidence

### Neutral

- All technical architecture unchanged
- All metrics unchanged
- All ADR-023/024/025/026 rules still apply

## The Real Question

> Are you evaluated by monthly return performance, or by institutional architecture?
>
> One is fintech. The other is critical infrastructure.
>
> The valuation multiples are completely different.

---

## References

- ADR-023: Investor Positioning Refinement
- ADR-024: Investor Challenge Response Framework
- ADR-025: Decision Governance Platform (extended by this ADR)
- ADR-026: Multi-Vertical Governance Architecture

---

*Decision adopted: February 17, 2026*
*This is a category-creation decision. OMNIX is building Decision Governance Infrastructure, not competing in Fintech AI.*
