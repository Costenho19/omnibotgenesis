# ADR-112: Energy Governance Vertical (ADR-ENG-001)

**Status:** ACCEPTED  
**Date:** 11 April 2026  
**Internal Code:** ADR-ENG-001  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Scope:** `omnix_core/energy/` · `omnix_dashboard/blueprints/energy_governance.py` · `omnix_web/src/pages/EnergyDashboard.tsx`  
**Visibility:** Internal — not publicly announced. Release when the right client arrives.

---

## Context

Energy trading and dispatch decisions — MW commitment, curtailment orders, PPA contracts,
capacity trades, carbon credits — are high-stakes, time-critical, and irreversible once
committed to the grid. A 500 MW dispatch committed in a constrained grid zone can trigger
cascade failures if the decision logic is wrong.

OMNIX extends its 11-checkpoint pipeline to the energy trading domain, providing
pre-execution governance for every dispatch, curtailment, PPA, capacity, and carbon
decision. The vertical is built for SCADA-operator-level precision.

---

## Decision

Build a full-stack energy governance vertical with SCADA-aesthetic visual identity,
applying the OMNIX 11-checkpoint pipeline adapted to energy market decision parameters.

---

## Visual Identity — SCADA Control Room

| Property | Value |
|----------|-------|
| Background | `#030810` (darker than all other dashboards) |
| Primary accent | `#00B4D8` (electric blue / cyan) |
| Approved | `#0AFF9D` (voltage green) |
| Unique panels | Grid Frequency Gauge (Hz, animated) · Fuel Mix stacked bar · CO₂ Avoided counter · Settlement Risk · Capacity Margin indicator |
| Table style | Power grid operator interface |

---

## Signal Adapter

**File:** `omnix_core/energy/energy_signal_adapter.py`

| Energy Parameter | OMNIX Signal | Source |
|----------------|-------------|--------|
| LMP forecast confidence + freq health | `probability_score` | Grid stability |
| MW concentration + vol risk + capacity margin | `risk_exposure` | Portfolio exposure |
| Day-ahead/RT spread + futures convergence + cross-border | `signal_coherence` | Price coherence |
| Load accuracy + demand stability + seasonality | `trend_persistence` | Demand trajectory |
| Renewable buffer + interconnect headroom + storage | `stress_resilience` | Grid resilience |
| Regulatory compliance + carbon intensity | `logic_consistency` | Compliance gate |

### Hard blocks (pipeline stops regardless of scores)
- `freq_deviation > 0.5 Hz` → BLOCK (grid stability breach)
- `capacity_margin < 5%` → BLOCK (reserve margin breach)
- `counterparty_default` → BLOCK (credit risk)
- `carbon_cap_breach` → BLOCK (regulatory)
- `regulatory_violation` → BLOCK
- `sanctions` → BLOCK (OFAC/FATF)

---

## Simulator

**File:** `omnix_core/energy/energy_simulator.py`

24/7 simulator for live data generation:

| Parameter | Value |
|-----------|-------|
| Cycle interval | 180 seconds |
| Decisions per cycle | 4–10 |
| Decision types | dispatch_order (35%) · curtailment_order (20%) · ppa_contract (15%) · capacity_trade (15%) · carbon_credit (10%) · balancing_action (5%) |
| Energy sources | Natural_Gas · Wind_Onshore · Wind_Offshore · Solar_Utility · Nuclear · Hydro · Battery_Storage · LNG · Coal |
| Grid regions | PJM · UK · EU_ENTSO_E · ERCOT · GCC · AEMO |
| Tables | `energy_decisions` + `energy_cycle_metrics` |

---

## Flask Blueprint

**File:** `omnix_dashboard/blueprints/energy_governance.py`

Endpoints at `/api/energy/*`:

| Endpoint | Purpose |
|----------|---------|
| `/api/energy/metrics` | Aggregate KPIs (MW governed, CO₂ avoided, grid stability) |
| `/api/energy/decisions` | Decision list |
| `/api/energy/by-type` | Breakdown by decision type |
| `/api/energy/by-source` | Breakdown by energy source |
| `/api/energy/by-region` | Breakdown by grid region |
| `/api/energy/timeline` | 24h timeline |
| `/api/energy/live-feed` | Last N decisions with telemetry (Hz, capacity %, MW) |
| `/api/energy/evaluate` | Single decision evaluation |
| `/api/energy/health` | Health check |

---

## Frontend

### `/energy` → `EnergyDashboard.tsx`
SCADA-aesthetic live operations dashboard:
- KPIs: MW Governed, Approved MW, CO₂ Avoided, Decisions/24h, Grid Stability, Capacity Margin, Hard Blocks, Settlement Risk
- Grid Frequency Monitor (Hz, animated gauge)
- Fuel Mix (donut + bar chart)
- Signal Health strip (6 signals)
- Tables: Decision Types, Grid Regions, Energy Source breakdown
- Live feed with telemetry (Hz, capacity %, MW per decision)
- Badge: **ADR-112**

---

## Metrics — First Test Cycle (11-Apr-2026)

| Metric | Value |
|--------|-------|
| Decisions | 7 |
| APPROVED | 4 |
| BLOCKED | 2 |
| HELD | 1 |
| MW governed | 4,174 |
| CO₂e avoided | 5,718 kt |
| API /api/energy/health | `status: operational` · `receipt_prefix: OMNIX-EGV` |

---

## Infrastructure integration

| File | Change |
|------|--------|
| `omnix_dashboard/blueprints/__init__.py` | `energy_bp` imported and exported |
| `omnix_dashboard/app.py` | Blueprint registered, tables initialized, simulator started |
| `omnix_web/src/App.tsx` | Route `/energy` |
| `omnix_web/vite.config.ts` | Proxy `/api/energy` configured |
| `omnix_web/src/pages/ClientDashboard.tsx` | `energy_governance: '⚡' / #00B4D8` |
| `omnix_web/src/pages/AuditDashboard.tsx` | `energy_governance: '⚡' / #00B4D8` |
| `omnix_core/evidence/decision_receipt.py` | `"energy_governance": "EGV"` in `_DOMAIN_CODES` |

---

## ADR number gap — ADR-086 through ADR-111

ADR-112 is the formal designation for this vertical. The range ADR-086 to ADR-111
represents internal micro-ADRs and code-level architecture decisions made during
the April 2026 build sprint. These are tracked in code comments and replit.md
rather than individual ADR files.

`ADR_COUNT = 112` in `live_metrics.py` reflects this as the current ceiling ADR number.

---

## Business context

Potential pilot via Naimat Khan (Velos Capital — contacts with utilities/energy trading
operators). Vertical to be released publicly when the right energy client is secured.

---

## References

- ADR-ENG-001 entry in `replit.md`
- ADR-091: Autonomous Agents Vertical (same build sprint)
- ADR-085: Cross-Border Semantic Governance (receipts cover energy frameworks)
- `omnix_web/src/pages/EnergyDashboard.tsx` — SCADA frontend
