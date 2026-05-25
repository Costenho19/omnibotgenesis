# ADR-191 — OMNIX Executive View

**Status:** Accepted
**Author:** Harold Nunes
**Date:** 2026-05-25
**Related:** ADR-184 (OGR), ADR-186 (PoGR), ADR-190 (SAL)

---

## Context

All existing OMNIX interfaces speak the language of engineers and protocol designers:
receipts, hash chains, invariants, BEV layers, ATF stacks. This is by design for the
technical integration audience.

However, the **economic buyer** for OMNIX is the C-suite — CEOs, CFOs, CROs, and
Chief Compliance Officers. These decision-makers need a different interface: one that
translates cryptographic governance into business language they can act on in 30 seconds.

**Gap identified:** OMNIX has no interface designed for the institutional buyer who must
approve the budget to integrate the protocol. This mirrors the UHG-Tech "L'OMBRE" gap
identified in competitive analysis (2026-05-25).

---

## Decision

Introduce **OMNIX Executive View** at route `/executive`.

### Design Principles

1. **Zero jargon** — No mention of hash chains, Dilithium, invariants, or ATF layers
   on the primary view. These exist one click deeper for the CISO/CTO.
2. **Decision in 30 seconds** — The executive must understand governance health, active
   risk, and what requires their attention without scrolling.
3. **Premium aesthetics** — Dark background, gold typography, institutional feel.
   The page must feel like Bloomberg Terminal meets governance infrastructure.
4. **One action per section** — Each metric panel has a single clear next action.
5. **Trust narrative** — Every metric is framed as a business outcome, not a
   technical measurement.

### Information Architecture

```
┌─────────────────────────────────────────────────────┐
│  OMNIX EXECUTIVE VIEW        Governance Health: 98% │
│  Your AI. Governed.                          [Live] │
├─────────────────────────────────────────────────────┤
│  [Decisions Today]  [Active Agents]  [Risk Level]  │
│  [Vetoed Actions]   [Compliance Score] [Alerts]    │
├─────────────────────────────────────────────────────┤
│  WHAT HAPPENED TODAY (plain English narrative)      │
├─────────────────────────────────────────────────────┤
│  ACTION REQUIRED (if any)                          │
├─────────────────────────────────────────────────────┤
│  PROOF OF GOVERNANCE    [Download Certificate]     │
└─────────────────────────────────────────────────────┘
```

### Route

`/executive` — lazy-loaded, added to App.tsx.
Accessible from CommercialLanding nav ("Executive View") and from the main CTA section.

---

## Invariants

- **EV-INV-001:** The Executive View MUST NOT display raw cryptographic data (hashes,
  signatures, hex strings) in the primary viewport. Technical details live behind
  "View Details" links.
- **EV-INV-002:** All metrics displayed MUST have a plain-English label and a
  business-outcome description.
- **EV-INV-003:** The page MUST be accessible without authentication (public demo mode).

---

## Consequences

**Positive:**
- Bridges the gap between technical protocol and economic buyer
- Directly addresses the competitive gap vs UHG-Tech L'OMBRE
- Provides a shareable link Harold can send to enterprise prospects before any sales call

**Negative:**
- Demo metrics are illustrative; real metrics require API key integration
