# ADR-046: Sharia Governance Gate (CP-6)

**Status:** ACCEPTED 
**Date:** March 25, 2026 
**Author:** Harold Nunes 
**Module:** `omnix_core/governance/sharia_gate.py`

---

## Context

OMNIX is presented at and targets institutional capital in the Gulf Cooperation Council (UAE, Saudi Arabia, Qatar). A significant portion of institutional capital in this region operates under Islamic finance principles (Sharia law), which prohibits:

- **Riba** (interest / usury)
- **Gharar** (excessive uncertainty)
- **Haram assets** (alcohol, tobacco, pork, weapons, gambling, conventional banking)
- **Excessive debt** (ratio > 33% of total assets)

No existing automated governance infrastructure provides real-time Sharia compliance validation with cryptographic audit receipts. This is a structural market gap.

---

## Decision

Implement CP-6 — the previously unassigned checkpoint slot — as the **Sharia Governance Gate**, positioned between CP-5 (Adaptive Coherence) and CP-7 (TCV) in the 8-checkpoint decision pipeline.

### Design Principles

1. **Fail-safe by default** — disabled for all existing clients; exceptions → pass-through
2. **Configurable per client** — `sharia_enabled` flag in `b2b_clients` table
3. **Fail-closed when enabled** — haram asset or gharar violation → immediate BLOCKED with PQC receipt
4. **Zero impact on existing pipeline** — existing behavior preserved 100%

---

## Implementation

### Module: `omnix_core/governance/sharia_gate.py`

Four validation checks in sequence:

| Check | Rule | Behavior |
|-------|------|----------|
| **1. Haram screening** | Asset in haram list | Hard VETO — `HARAM_ASSET` |
| **2. Halal whitelist** | Asset not in known halal list | Score deduction (-30 pts) |
| **3. Gharar limit** | Uncertainty score > threshold (default 70) | Hard VETO — `GHARAR_EXCESIVO` |
| **4. Debt ratio** | Issuer debt > 33% of assets | Score deduction (-30 pts) |

### Pipeline Position

```
CP-1 (Monte Carlo) → CP-2 (RMS) → CP-3 (Early Return)
→ CP-4 (Coherence) → CP-5 (Adaptive Coherence)
→ CP-6 (Sharia Gate) ← NEW
→ CP-7 (TCV) → CP-7b (FTI) → CP-8 (ECW)
```

### Database Schema

```sql
ALTER TABLE b2b_clients
 ADD COLUMN sharia_enabled BOOLEAN DEFAULT FALSE,
 ADD COLUMN gharar_threshold FLOAT DEFAULT 70.0,
 ADD COLUMN debt_ratio_max FLOAT DEFAULT 0.33;
```

### Halal Asset List (initial)

BTC, ETH, SOL, ADA, DOT, AVAX, LINK, MATIC, XLM, ALGO, ATOM, NEAR, and their USD/USDT trading pairs.

### Haram Asset List (initial)

WBTC (wrapped, interest-generating product in some protocols).

---

## Consequences

### Positive
- Positions OMNIX as the only governance infrastructure with real-time Sharia compliance
- Each Sharia-vetoed decision generates a PQC-signed receipt — independently verifiable
- Enables targeting Islamic finance funds in UAE, Saudi Arabia, Qatar
- CP-6 slot finally assigned — pipeline numbering is now complete (CP-1 through CP-8)
- Zero risk to existing clients — completely opt-in

### Negative / Trade-offs
- Halal whitelist requires maintenance as new assets emerge
- Debt ratio check not applicable to spot crypto (always 0) — relevant for future equity instruments
- Riba check placeholder for now (DeFi lending not yet in scope)

---

## Investor Narrative

> "OMNIX is the only governance infrastructure in the market that validates decisions against Islamic finance principles in real time, with a cryptographically signed receipt that any Sharia board can independently verify — without asking OMNIX for records."

---

## Test Results

| Test | Input | Expected | Result |
|------|-------|----------|--------|
| Disabled (default) | BTC/USD, gharar=20 | Pass-through | PASS |
| Enabled, halal asset | BTC/USD, gharar=20 | Admissible, score=100 | PASS |
| Enabled, haram asset | WBTC, gharar=20 | VETO HARAM_ASSET | PASS |
| High gharar | BTC/USD, gharar=85 > 70 | VETO GHARAR_EXCESIVO | PASS |
| Exception | None as symbol | Pass-through (fail-safe) | PASS |

All 5 tests passed — March 25, 2026.

---

## Related ADRs

- ADR-022: Post-Quantum Cryptography (Dilithium-3 signatures on receipts)
- ADR-024: Investor Challenge Response Framework
- ADR-032: Temporal Coherence Validation (CP-7)
- ADR-036: Exit Governance Layer
