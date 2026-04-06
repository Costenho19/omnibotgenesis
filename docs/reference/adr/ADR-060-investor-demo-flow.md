# ADR-060: Guided Investor Demo Flow

**Status:** Accepted  
**Date:** 2026-04-06  
**Author:** Harold Nunes  

## Context

OMNIX has three distinct proof points (Bot, Command Center, Audit Dashboard) but no single narrative flow that connects them for an investor or prospective client in under 2 minutes. Each tool exists independently — a CFO or fund manager visiting the site must discover the connection themselves.

## Decision

Implement a **Guided Investor Demo** at `/demo` that walks any visitor through the complete OMNIX story in 4 sequential stages:

1. **Scenario Selection** — 4 real-world scenarios across all active verticals (Trading, Islamic Credit, Insurance, Robotics). Each pre-written, each designed to produce a clear governance outcome.
2. **11-Checkpoint Pipeline** — Animated checkpoint-by-checkpoint evaluation using a real API call to `/api/public/sandbox`. Checkpoints animate in sequence (320ms each). The pipeline result (APPROVED/BLOCKED) drives the visual state.
3. **Decision Receipt** — Shows the actual receipt_id, PQC SIGNED badge, CHAIN LINKED badge, governance rationale, and links to `/verify/{receipt_id}` and `/audit`.
4. **Full Picture** — Presents the 3 OMNIX proof points (Bot, Command Center, Audit Dashboard) as a unified architecture. Includes the fundraising call-to-action ($500K pre-seed, $3M valuation).

## Fallback

If `/api/public/sandbox` returns an error, the demo falls back to a deterministic local result based on scenario domain — the demo never breaks for a visitor.

## Navigation

- Route: `/demo`
- Entry point: InvestorCommandCenter → "2-Min Investor Demo" link (amber, top of quick links)
- No authentication required

## Consequences

- Any investor or client can experience the full OMNIX architecture without a sales call
- Scenario → Decision → Receipt → Audit is now a coherent 2-minute narrative
- Reduces dependence on live demos or prepared slides for first-contact meetings

## Files

```
omnix_web/src/pages/InvestorDemo.tsx   # 4-stage guided demo component
omnix_web/src/App.tsx                   # Route /demo added
omnix_web/src/pages/InvestorCommandCenter.tsx  # Quick link added
docs/reference/adr/ADR-060-investor-demo-flow.md
```
