# ADR-002: Honest Framing Over Censorship

**Status:** Accepted  
**Date:** January 10, 2026  
**Decision Makers:** Harold Nunes, OMNIX Development Team

## Context

On January 10, 2026, a review was conducted of the `PublicResponseFilter` system that was designed to hide negative metrics (Win Rate < 40%, negative P&L, paper trading mentions) from potential investors.

The system used:
- Blacklist patterns to remove lines with negative metrics
- Word replacements ("pérdida" → "capital protegido")
- Response length limits (150 words max)

## Problem

**Ethical Issue:** Hiding losses from potential investors may constitute fraud by omission.

When an investor asks "how is the system performing?" and we respond with sanitized metrics that hide a 20% win rate and -$15K P&L, we are potentially:
1. Violating securities disclosure norms
2. Creating legal liability for fraud
3. Destroying trust if investors later discover hidden data
4. Contradicting our own ADR-001 "Brutal Honesty" principle

## Decision

**We will NOT hide negative metrics. We will use "Honest Framing" instead.**

### Honest Framing Principles:
1. **Show ALL real data** when users ask about performance
2. **Add truthful positive context** (but never misleading euphemisms)
3. **Only show detailed metrics when specifically requested**
4. **Never use euphemisms that deceive** ("capital deployment" to hide losses)

### Implementation:

| Real Metric | Honest Framing (CORRECT) | Censorship (DEPRECATED) |
|-------------|--------------------------|-------------------------|
| Win Rate: 20.17% | "20.17% (objetivo: 40%+)" | ~~Hidden~~ |
| P&L: -$15,198 | "-$15,198 (98.5% capital preserved)" | ~~Hidden~~ |
| 12 days no trades | "Protection mode activated" | ~~"Active validation"~~ |
| 695 vetos | "695 high-risk ops blocked" | ~~Hidden~~ |

## Technical Changes

1. `PublicResponseFilter` → `HonestFramingFormatter`
2. Removed `PUBLIC_BLACKLIST_PATTERNS` (no censorship)
3. Removed `PUBLIC_SAFE_REPLACEMENTS` (no deceptive replacements)
4. Added `should_show_metrics()` - only show when asked
5. Updated `MASTER_SYSTEM_PROMPT` with Honest Framing policy

## Consequences

### Positive:
- Full legal compliance with disclosure norms
- Aligned with ADR-001 "Brutal Honesty"
- Builds genuine investor trust
- No risk of fraud accusations

### Negative:
- Investors see current performance (20% WR, -$15K)
- May delay investment until metrics improve

### Mitigation:
- The TRUE positive story IS the protection system (98.5% capital preserved)
- We don't need to hide data - we need to improve performance
- Honest framing shows the system WORKS (protects capital)

## References

- ADR-001: Brutal Honesty Monitoring
- DATA_INTEGRITY_AUDIT_JAN2026.md
- HonestFramingFormatter in `honesty_guard.py`
