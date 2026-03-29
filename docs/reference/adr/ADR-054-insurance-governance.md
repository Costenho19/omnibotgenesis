# ADR-054 — Insurance Governance Vertical

**Status**: IMPLEMENTED  
**Date**: 2026-03-29  
**Author**: Harold Nunes — OMNIX  
**Implements**: Domain-agnostic governance applied to global insurance claims

---

## Context

OMNIX is a domain-agnostic Decision Governance Infrastructure. ADR-028 established the trading vertical. ADR-052 established Islamic Credit. ADR-054 establishes a third vertical: Global Insurance Claim Governance — demonstrating that the same 11-checkpoint pipeline governs any high-stakes binary decision domain.

The insurance market ($7T+ global premiums) faces three governance failures:
1. Fraudulent claims approved without adequate signal validation
2. Legitimate claims blocked due to inconsistent evidence assessment
3. No cryptographically verifiable audit trail for claim decisions

---

## Decision

Deploy the Insurance Governance Vertical using the same OMNIX governance pipeline, with a domain-specific signal adapter that translates insurance claim parameters into the 6 normalized governance signals.

### Signal Mapping

| OMNIX Signal | Insurance Domain | Source Parameters |
|---|---|---|
| `probability_score` | Claim legitimacy probability | Claimant history, evidence completeness, fraud indicators |
| `risk_exposure` | Loss severity index | Claim/limit ratio, fraud baseline, incident recency |
| `signal_coherence` | Evidence consistency | Document alignment, history-fraud mismatch detection |
| `trend_persistence` | Underwriting condition stability | Loss ratio trend, regional benchmark, CAT events |
| `stress_resilience` | Reserve adequacy | Reserve score, claim size vs capacity |
| `logic_consistency` | Policy-claim alignment | Policy match, evidence-fraud cross-check |

### Supported Insurance Types
- Auto (25%), Property (30%), Health (20%), Liability (12%), Cyber (8%), Life (5%)

### Supported Regions
- NA, EU, APAC, MEA, LATAM

### Checkpoint Configuration

| Checkpoint | Status in Insurance Vertical |
|---|---|
| CP-0 SIV | ✅ Active — claim data completeness |
| CP-1 Probability | ✅ Active — claim legitimacy |
| CP-2 Risk | ✅ Active — loss severity |
| CP-3 Coherence | ✅ Active — evidence consistency |
| CP-4 Trend | ✅ Active — market conditions |
| CP-5 Stress | ✅ Active — reserve adequacy |
| CP-6 Sharia | ❌ Disabled — not applicable |
| CP-7 TCV | ✅ Active — policy alignment |
| CP-7b FTI | ✅ Active — forward risk trajectory |
| CP-8 ECW | ✅ Active — portfolio concentration |
| CP-9 AML | ✅ Active — financial crime screening |
| CP-10 Fraud | ✅ Active — behavioral fraud detection |
| CP-11 Jurisdiction | ✅ Active — regional compliance |
| TIE | ✅ Active — trajectory invariant enforcement |

### Simulation Engine

- **Cycle interval**: 240 seconds (4 minutes)
- **Batch size**: 4–10 claims per cycle
- **Markets simulated**: Global commercial insurance
- **Calibration**: Claim amounts, fraud rates, and approval rates calibrated to real-world insurance benchmarks

### Data Persistence

New PostgreSQL tables:
- `insurance_claims` — full claim record with all 6 governance signals + decision + receipt_id
- `insurance_cycle_metrics` — cycle-level aggregates (approval rate, loss avoided, fraud blocked)

### API Endpoints

```
GET  /api/insurance/metrics     — Summary KPIs
GET  /api/insurance/claims      — Recent claims with decisions
GET  /api/insurance/by-type     — Breakdown by insurance type
GET  /api/insurance/by-region   — Breakdown by region
GET  /api/insurance/timeline    — Approval/block trend over time
POST /api/insurance/evaluate    — Manual claim evaluation
GET  /api/insurance/health      — Engine health
```

### Dashboard

React dashboard at `/insurance` with:
- Real-time KPI cards (claims evaluated, approval rate, loss avoided, fraud blocks)
- Breakdown by insurance type with color-coded bars
- Breakdown by region with flag indicators
- 11-checkpoint pipeline visualization
- Recent claims table with decision badges and receipt IDs
- Signal breakdown for latest blocked claim

---

## Consequences

**Positive:**
- Proves domain-agnosticism: 3 completely different domains, 1 governance engine
- $7T+ addressable market — global commercial insurance
- Every blocked fraudulent claim is quantifiable loss avoided
- Same PQC-signed receipts — every decision independently verifiable

**Architectural:**
- Zero changes to governance engine core
- Signal adapter is the only domain-specific code
- Simulator provides realistic data for investor demonstrations

---

## Files

```
omnix_core/insurance/
  __init__.py
  insurance_signal_adapter.py   — 6-signal domain adapter
  insurance_simulator.py        — 24/7 simulation engine

omnix_dashboard/blueprints/
  insurance_governance.py       — Flask REST API blueprint

omnix_web/src/pages/
  InsuranceDashboard.tsx        — React dashboard (/insurance)
```
