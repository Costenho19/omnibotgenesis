# ADR-025: Decision Governance Platform Repositioning

**Note (Feb 17, 2026):** Extended by ADR-027, which upgrades "AI Decision Governance Platform" to "Decision Governance Infrastructure for Automated Systems" with category-creation framing.

**Status**: ADOPTED 
**Date**: February 15, 2026 
**Author**: Harold Nunes, OMNIX Team 
**Category**: Business / Strategic Positioning

---

## Context

OMNIX has successfully completed its 30-day paper trading track record (Jan 15 - Feb 13, 2026) and advanced to **Semifinalist** status in . The core technology — a 6-checkpoint veto architecture, Monte Carlo simulation, Non-Markovian Memory, Shadow Portfolio learning engine — has been validated in real market conditions with 670,000+ decision cycles analyzed.

Upon review, the technology OMNIX has built is **not limited to trading**. The core engine solves a universal problem: **governing high-stakes decisions under uncertainty**. Crypto trading is simply the first domain where this was validated.

Investors and competition judges (, Hub71) evaluate **total addressable market** and **scalability potential**. Positioning OMNIX solely as "crypto trading risk infrastructure" limits perceived market size and creates direct competition with thousands of trading bots. Positioning as a **decision governance platform** opens multiple verticals worth billions collectively.

## Decision

Reposition OMNIX from:

| Before | After |
|--------|-------|
| "AI Capital & Risk Orchestration Engine" | **"Decision Governance Infrastructure for Automated Systems"** |
| Crypto trading risk infrastructure | Decision governance infrastructure for any high-stakes domain |
| Single vertical (digital asset trading) | Multi-vertical platform with crypto as first validated use case |

### New Core Identity

> **OMNIX is a governance control architecture for automated decision systems. It is building the category of Decision Governance Infrastructure. The first validated vertical is digital asset trading.**

### New Tagline

> "Governing Decisions Under Uncertainty"

### The "Airport Security" Metaphor — Now Universal

The existing "airport security for your capital" metaphor naturally extends:

| Vertical | What OMNIX Governs |
|----------|-------------------|
| **Digital Asset Trading** (Validated) | Trade execution decisions — block high-risk trades before capital deployment |
| **Supply Chain** | Procurement decisions — block high-risk purchase orders before commitment |
| **Lending / Credit** | Loan approval decisions — block high-risk credit extensions |
| **Insurance** | Underwriting decisions — block high-risk policy issuances |
| **Energy Trading** | Energy procurement decisions — block high-risk energy contracts |
| **RegTech / Compliance** | Operational decisions — block regulatory-violating actions |

In every case, the same 6-checkpoint architecture applies:
1. Probability Check ("Is this likely to succeed?")
2. Risk Limit ("Would this exceed safe limits?")
3. Signal Agreement ("Do multiple models agree?")
4. Trend Confirmation ("Is this sustained or noise?")
5. Stress Test ("What if conditions deteriorate?")
6. Logic Check ("Are signals contradicting each other?")

## Constraints (MANDATORY)

### Numbers — UNCHANGED

All existing metrics remain exactly as documented:

| Metric | Value | Status |
|--------|-------|--------|
| Raising | $500,000 USD | Unchanged |
| Equity | 16.7% | Unchanged |
| Pre-Money Valuation | $2.5M-$3M | Unchanged |
| Capital Preserved | 98.5% | Unchanged |
| Max Drawdown | 1.5% | Unchanged |
| Trades Blocked | 47 | Unchanged |
| Block Success Rate | 91% | Unchanged |
| Decision Cycles | 670,000+ | Unchanged |
| P&L (Learning Baseline) | -$15,198.73 | Unchanged |
| B2B Prop Firm Pricing | $15K-35K/month | Unchanged |
| B2C Pro | $149/month | Unchanged |
| B2C Advanced | $499/month | Unchanged |

### Crypto Trading — FIRST VERTICAL, NOT REMOVED

- Digital asset trading remains the **first validated vertical**
- All crypto-specific evidence, metrics, and case studies remain
- Dubai/ADGM focus remains the go-to-market strategy
- Prop firms (200+ in ADGM/DIFC) remain primary B2B target
- The expansion to other verticals is **roadmap**, not current revenue

### ADR-023 Rules — STILL BINDING

- No yield promises
- No direct firm comparisons
- No "democratizing finance"
- Mandatory Track Record Period Disclosure
- "Experimenting with" language for PQC claims
- "Investor Confidential" classification on investor docs

## Narrative Framework

### Pitch Structure (Updated)

1. **Problem**: Universal — "95% of high-stakes decision systems lack proper governance"
2. **Solution**: "6-checkpoint AI governance engine that blocks bad decisions before they happen"
3. **First Vertical (Proof)**: Digital asset trading — 98.5% capital preserved, 670,000+ cycles
4. **Multi-Vertical Vision**: Supply chain, lending, insurance, energy, RegTech
5. **Business Model**: B2B risk infrastructure licensing (unchanged pricing)
6. **Market**: Expanded TAM — not just crypto, but all regulated decision-making
7. **The Ask**: $500K, 16.7%, $2.5M-$3M (unchanged)

### Key Phrases to Use

| Theme | Phrases |
|-------|---------|
| Core Identity | "Decision Governance Platform", "AI governance infrastructure" |
| Value Prop | "Prevents costly mistakes before they happen", "Governs decisions under uncertainty" |
| First Vertical | "Validated in digital asset trading", "First vertical: crypto (proven)" |
| Expansion | "Vertical-agnostic architecture", "Same 6-checkpoint engine, different domains" |
| Moat | "670,000+ governed decisions", "Learning from what it blocks" |

### Key Phrases to AVOID

| Avoid | Why |
|-------|-----|
| "Just a trading bot" | Undermines platform positioning |
| "We plan to expand" (vague) | Must be specific about verticals |
| "Any industry" (too broad) | Focus on 5-6 named verticals |
| "Pivot" or "pivoting" | This is expansion, not pivot — crypto is still core |

## Documents to Update

| Document | Changes Required |
|----------|-----------------|
| `docs/business/OMNIX_EUREKA_PITCH_FINAL.md` | Tagline, problem/solution broadened, add Multi-Vertical Vision slide |
| `docs/business/OMNIX_EUREKA_PITCH_FINAL_ES.md` | Same changes in Spanish |
| `docs/business/OMNIX_BUSINESS_MODEL_CANVAS.md` | Value prop, TAM expansion, vertical segments |
| `docs/business/investor/PRODUCT_OVERVIEW.md` | Core identity, add "First Vertical" + "Next Verticals" |
| `docs/business/investor/PITCH_DECK_OUTLINE.md` | Update slide structure for platform framing |
| `omnix_web/src/pages/CommercialLanding.tsx` | Hero messaging, add verticals section |
| `omnix_web/src/pages/InstitutionalPage.tsx` | Update institutional positioning |
| `omnix_config/system_state_manifest.json` | Core identity fields |
| `replit.md` | Overview section |
| `docs/README.md` | Positioning line |

## Implementation Checklist

- [ ] Create this ADR (ADR-025)
- [ ] Update Pitch Deck EN with multi-vertical framing
- [ ] Update Pitch Deck ES with same changes
- [ ] Update Business Model Canvas
- [ ] Update PRODUCT_OVERVIEW.md
- [ ] Update PITCH_DECK_OUTLINE.md
- [ ] Update CommercialLanding.tsx
- [ ] Update InstitutionalPage.tsx
- [ ] Update system_state_manifest.json identity
- [ ] Update replit.md overview
- [ ] Update docs/README.md positioning
- [ ] Verify all numbers unchanged across all documents

## Consequences

### Positive

- **Dramatically expanded TAM** — from crypto risk infra (~$18.8B) to decision governance across multiple industries
- **Stronger positioning** — judges see scalable platform, not niche bot
- **Investor appeal** — multi-vertical potential justifies valuation and shows growth trajectory
- **Competitive differentiation** — exits "trading bot" category entirely
- **Natural metaphor extension** — "airport security" works for any domain
- **Same technology** — no engineering changes required, only narrative

### Negative

- **Broader claims require careful framing** — must emphasize crypto is validated, others are roadmap
- **May need vertical-specific expertise** for future expansion (addressed post-funding with hires)
- **Risk of appearing unfocused** — mitigated by keeping crypto as clear first vertical with evidence

### Neutral

- All existing technical architecture unchanged
- All existing metrics unchanged
- All ADR-023 rules still apply
- Dubai/ADGM go-to-market strategy unchanged

---

## References

- ADR-023: Investor Positioning Refinement
- ADR-024: Investor Challenge Response Framework
- `docs/business/OMNIX_EUREKA_PITCH_FINAL.md`
- `docs/business/OMNIX_BUSINESS_MODEL_CANVAS.md`
- `docs/business/investor/PRODUCT_OVERVIEW.md`

---

*Decision adopted: February 15, 2026*
*This is an expansion of positioning, not a pivot. Crypto trading remains the first validated vertical.*
