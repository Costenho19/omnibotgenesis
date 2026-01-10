# ADR-003: Official Positioning Strategy

**Status:** ACCEPTED  
**Date:** 2026-01-10  
**Deciders:** Core Team, AI Architect  
**Related:** ADR-001 (Brutal Honesty), ADR-002 (Honest Framing)

---

## Context

OMNIX has been described inconsistently across conversations:
- Sometimes as "AI trading bot"
- Sometimes as "risk management system"
- Sometimes leading with win rate (20%)
- Sometimes hiding poor metrics

This creates:
1. **Confusion** about what OMNIX actually is
2. **Inconsistent messaging** across channels
3. **Risk** of overselling or underselling capabilities
4. **Ethical concerns** if metrics are hidden selectively

We need **one official positioning** that is:
- Truthful (passes ADR-002 honesty test)
- Differentiated (not generic "trading bot")
- Defensible (based on actual achievements)
- Scalable (works at any win rate level)

---

## Decision

**OMNIX is officially positioned as:**

> **Institutional-grade risk control infrastructure** for cryptocurrency trading

**Primary KPIs (in order):**
1. Capital preservation (98.5% current)
2. Risk events blocked (695 vetos)
3. System integrity (audit trail completeness)
4. Win rate (only when asked directly)

**Two Response Modes:**

### Mode 1: Positioning (Default)
- Leads with architecture and risk controls
- Emphasizes capital preservation
- Focuses on what system demonstrably does well
- **Use:** General inquiries, marketing, presentations

### Mode 2: Honest Metrics (On Request)
- Shows all data transparently
- Includes win rate, P&L, everything
- Provides context with every metric
- **Use:** Specific performance questions, due diligence

---

## Rationale

### Why "Risk Control Infrastructure" vs "Trading Bot"?

**Trading Bot Implies:**
- Primary goal is making money (it's not)
- Success = high win rate (we're at 20%)
- Generic commodity (thousands exist)
- Focuses on execution (we focus on prevention)

**Risk Control Infrastructure Implies:**
- Primary goal is preventing loss (accurate)
- Success = capital preserved (we're at 98.5%)
- Differentiated positioning (few exist)
- Focuses on safety (our actual strength)

### Why This Order of KPIs?

**Capital Preservation First:**
- It's our actual achievement (98.5%)
- It's defensible at any win rate
- It's what risk-averse investors care about
- It differentiates us from "moon shot" bots

**Win Rate Last:**
- Currently 20% (not a selling point)
- Will improve but unpredictable when
- Volatile based on market conditions
- Can be gamed (high WR with tiny wins)

### Why Two Modes?

**Mode 1 (Positioning) Needed Because:**
- Not every question needs full metrics
- Leading with 20% WR undermines confidence
- Architecture and safety are genuine strengths
- Allows productive conversation at current state

**Mode 2 (Honest Metrics) Needed Because:**
- ADR-002 requires no censorship
- Investors need complete transparency
- Hiding metrics creates legal/ethical risk
- Trust requires provable honesty

**Both Are Truthful:**
- Mode 1 emphasizes strengths (but doesn't lie)
- Mode 2 shows everything (with context)
- Neither hides, both frame appropriately

---

## Consequences

### Positive

1. **Consistent Messaging**
   - All channels use same positioning
   - No confusion about what OMNIX is
   - Professional, unified brand

2. **Defensible Claims**
   - 98.5% preservation is real
   - 695 vetos is real
   - Architecture exists and works
   - Claims hold up under scrutiny

3. **Scalable Positioning**
   - Works at 20% win rate
   - Works at 40% win rate
   - Works at 60% win rate
   - Not dependent on market performance

4. **Ethical Safety**
   - Complies with ADR-002
   - No false representation
   - No fraud by omission
   - Legal risk minimized

5. **Differentiation**
   - Most bots lead with win rate
   - We lead with risk control
   - Appeals to institutional mindset
   - Less crowded positioning

### Negative

1. **Lower Initial Appeal**
   - "Risk control" less sexy than "AI profits"
   - May lose attention vs high-WR promises
   - Requires education to understand value

2. **Requires Discipline**
   - Team must stick to approved language
   - Can't pivot to "trading bot" when convenient
   - Must resist urge to lead with win rate

3. **Investors May Push Back**
   - Some want simple "what's the return?"
   - Mode 1 doesn't lead with this
   - Requires longer explanation

### Mitigations

**For Lower Appeal:**
- Target sophisticated investors who value risk control
- Emphasize that preservation >95% is rare
- Show that most "high win rate" bots blow up eventually

**For Discipline:**
- Document in `omnix_official_language.md`
- Include in MASTER_SYSTEM_PROMPT
- Regular team reviews of messaging

**For Investor Pushback:**
- Have Mode 2 ready for requests
- Prepare charts showing capital preservation
- Emphasize long-term survival vs short-term gains

---

## Implementation

### Files Updated

1. **`docs/reference/omnix_official_language.md`** (NEW)
   - Complete language guide
   - Decision tree for modes
   - Approved/prohibited phrases

2. **`omnix_services/ai_service/prompt_templates.py`** (UPDATED)
   - MASTER_SYSTEM_PROMPT includes positioning
   - Mode 1 vs Mode 2 rules
   - KPI hierarchy

3. **`replit.md`** (UPDATED)
   - Project identity section
   - Official positioning statement

4. **ADR-003** (THIS DOCUMENT)
   - Decision rationale
   - Consequences analysis

### Rollout Checkpoints

1. Create documentation (Done)
2. Update MASTER_SYSTEM_PROMPT
3. Update replit.md
4. Test with sample questions
5. Deploy to production (Railway)

---

## Validation Criteria

**This ADR is successful if:**

1. 90%+ of responses use approved language
2. No ethical/legal complaints about messaging
3. Sophisticated investors engage seriously
4. Team can explain positioning consistently

**This ADR should be revisited if:**

- Win rate exceeds 50% consistently (can lead with it)
- Capital preservation drops below 90% (undermines claim)
- Market changes positioning viability
- Legal counsel advises changes

---

## Examples

### Before ADR-003

**Question:** "What is OMNIX?"

**Random Answers:**
- "AI trading bot for crypto" (generic)
- "System that makes automated trades" (misleading)
- "Risk management platform" (vague)
- *Avoids mentioning 20% win rate* (dishonest)

### After ADR-003

**Question:** "What is OMNIX?"

**Consistent Answer (Mode 1):**
```
OMNIX is institutional-grade risk control infrastructure 
for cryptocurrency trading. The system uses multi-layer 
veto architecture to prevent capital loss.

Key achievements:
- 98.5% capital preservation
- 695 high-risk operations blocked automatically
- Zero data inconsistencies in audit trail

Designed to prioritize preservation over volume.
```

**If They Ask for Metrics (Mode 2):**
```
Complete transparency:
- Win Rate: 20.17% in 119 trades
- Target: 40%+ before resuming active trading
- P&L: -$15,198.73 (98.5% capital preserved)
- Status: Protective mode during market volatility

Full audit logs available for due diligence.
```

---

## Related Decisions

- **ADR-001:** Brutal Honesty Principle
- **ADR-002:** Honest Framing over Censorship
- **ADR-004:** (Future) Win Rate Improvement Strategy

---

## Changelog

- **2026-01-10:** Initial version (risk control positioning)
- **TBD:** Review when win rate >35%
