# ADR-114: Real Estate Governance Vertical (ADR-RES-001)

**Status:** ACCEPTED  
**Date:** 15 April 2026  
**Internal Code:** ADR-RES-001  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Scope:** `omnix_core/real_estate/` · `omnix_dashboard/blueprints/real_estate_governance.py` · `omnix_web/src/pages/RealEstateDashboard.tsx` · `omnix_web/src/pages/RealEstateGovernanceDemo.tsx`  
**Visibility:** Internal — not publicly announced. Release when the right client arrives.  
**Engine Integration:** `ADR-115` — connected to `GovernanceEvaluationEngine` on 15 April 2026

---

## Context

Real estate transactions — property valuations, mortgage approvals, tenant screenings,
AML-sensitive property purchases — involve high capital exposure, complex regulatory
stacks (RERA, FATF, Sharia financing frameworks), and irreversible legal commitments.
A mortgage approved with falsified comparable data or an AML-flagged buyer represents
systemic risk to the institution.

OMNIX extends its 11-checkpoint pipeline to the Real Estate domain, providing pre-execution
governance for every property decision before it is committed to a legal workflow. The
vertical is built for UAE RERA, UK FCA, and FATF AML compliance.

---

## Decision

Build a full-stack real estate governance vertical applying the OMNIX 11-checkpoint pipeline
adapted to property decision parameters, with domain-mandatory hard blocks for AML flags,
RERA non-compliance, Sharia screening failures, and LTV limit breaches — all bypassing
the engine entirely (no score override possible for regulatory blocks).

**Engine connection** (ADR-115): As of 15 April 2026, real estate decisions route through
`GovernanceEvaluationEngine.evaluate(domain="real_estate")` for non-blocked transactions.
Hard blocks (AML, RERA, Sharia, LTV) are checked pre-engine and return BLOCKED at
`decision_score = composite × 0.15`.

**Visibility strategy:** Vertical is live and operational. Not announced publicly.
Internal testing, validation, and partner demo capability. Release trigger: first institutional
real estate client or Velos/GCC property market entry.

---

## Signal Adapter

**File:** `omnix_core/real_estate/real_estate_signal_adapter.py`

Maps property parameters to 6 OMNIX governance signals:

| Property Parameter | OMNIX Signal | Interpretation |
|-------------------|-------------|----------------|
| `comparable_quality` + `model_accuracy` + `data_freshness` | `probability_score` | AVM valuation confidence |
| `ltv_ratio` + `price_deviation` + `aml_risk_score` | `risk_exposure` | Transaction risk |
| `comparable_alignment` + `market_depth` | `signal_coherence` | Multi-source data alignment |
| `market_trend_score` + `demand_index` + `inventory_pressure` | `trend_persistence` | Market trajectory stability |
| `liquidity_score` + `rate_sensitivity` + `vacancy_risk` | `stress_resilience` | Asset stress resilience |
| `aml_flag` (inverted) + `rera_compliant` + `beneficial_owner_verified` | `logic_consistency` | Regulatory compliance alignment |

### Hard blocks (pre-engine, not scored)

| Condition | Block reason |
|-----------|-------------|
| `aml_flag = True` | `CP-7: AML alert triggered — transaction BLOCKED pending investigation` |
| `rera_compliant = False` | `CP-7: RERA non-compliance detected — regulatory BLOCK` |
| Islamic financing + `sharia_screening_passed = False` | `CP-7: Sharia parameter screening failed — Islamic financing BLOCK` |
| `ltv_ratio > limit` (by financing mode) | `CP-3: LTV exceeds maximum — HARD BLOCK` |

**LTV limits by financing mode:** Conventional 90% · Murabaha 85% · Ijarah 85% · Musharaka 80%

---

## Simulator

**File:** `omnix_core/real_estate/real_estate_simulator.py`

24/7 simulator for live data generation:

| Parameter | Value |
|-----------|-------|
| Cycle interval | 300 seconds |
| Decisions per cycle | 3–8 |
| Decision types | `property_valuation` (30%) · `mortgage_approval` (28%) · `tenant_screening` (20%) · `AML_property` (12%) · `rental_yield` (10%) |
| Property types | `Residential` · `Commercial` · `Industrial` · `Mixed_Use` · `Land` |
| Market segments | `prime` · `standard` · `affordable` · `luxury` · `off_plan` |
| Jurisdictions | UAE · UK · GCC · EU · International |
| Financing modes | `Conventional` · `Murabaha` · `Ijarah` · `Musharaka` |
| Tables | `property_decisions` + `property_cycle_metrics` |
| Engine | `GovernanceEvaluationEngine(domain="real_estate")` — live since ADR-115 |

---

## Flask Blueprint

**File:** `omnix_dashboard/blueprints/real_estate_governance.py`

Endpoints at `/api/real-estate/*`:

| Endpoint | Purpose |
|----------|---------|
| `/api/real-estate/metrics` | Aggregate KPIs |
| `/api/real-estate/decisions` | Decision list |
| `/api/real-estate/by-type` | Breakdown by decision type |
| `/api/real-estate/by-jurisdiction` | Breakdown by jurisdiction |
| `/api/real-estate/by-property-type` | Breakdown by property type |
| `/api/real-estate/timeline` | 24h timeline |
| `/api/real-estate/live-feed` | Last 30 decisions |
| `/api/real-estate/evaluate` | Single decision evaluation |
| `/api/real-estate/health` | Health check |

---

## Frontend

### `/governance-demo-real-estate` → `RealEstateGovernanceDemo.tsx`
Interactive 11-checkpoint demo:
- Decision type, property type, market segment, jurisdiction, financing mode selectors
- Sliders: AVM confidence, LTV ratio, AML risk, market trend, liquidity score
- Hard block toggles: AML flag, RERA compliant, Sharia screening, beneficial owner verified
- Animated pipeline with per-checkpoint property-specific reasoning
- Badge: **ADR-114**

### `/real-estate` → `RealEstateDashboard.tsx`
Live operations dashboard:
- 8 KPI cards: total decisions, approved, blocked, approval rate, avg AVM confidence, avg LTV, AML blocks, RERA blocks
- Average signal health strip (6 signals)
- Breakdown tables: by decision type, by jurisdiction, by property type
- Live decision feed (30 decisions, 10s refresh)

---

## Infrastructure integration

| File | Change |
|------|--------|
| `omnix_dashboard/blueprints/__init__.py` | `real_estate_bp` imported and exported |
| `omnix_dashboard/app.py` | Blueprint registered, tables initialized eagerly, simulator started |
| `omnix_web/src/App.tsx` | Routes `/real-estate` + `/governance-demo-real-estate` |
| `omnix_web/src/pages/ClientDashboard.tsx` | `real_estate: '🏢' / #38bdf8` |
| `omnix_web/src/pages/AuditDashboard.tsx` | `real_estate: '🏢' / #38bdf8` |
| `omnix_core/evidence/decision_receipt.py` | `"real_estate": "REP"` in `_DOMAIN_CODES` |
| `omnix_config/system_state_manifest.json` | NOT in public metrics — internal vertical only |

---

## Regulatory frameworks covered

| Framework | Alignment |
|-----------|-----------|
| FATF Recommendations (AML/CFT) | CP-7 AML hard block + `aml_risk_score` signal |
| UAE RERA (Real Estate Regulatory Agency) | Hard block on `rera_compliant = False` |
| AAOIFI / Islamic Finance Standards | Sharia gate + Islamic financing mode parameters |
| UK FCA Mortgage Conduct of Business | LTV hard blocks + beneficial owner verification |
| GDPR / UAE PDPL | PQC-signed audit receipt per decision |

---

## References

- ADR-026: Multi-vertical domain adapter architecture (foundational)
- ADR-044: Quantum-Secure Decision Receipts
- ADR-047: AML Gate (CP-9)
- ADR-115: Engine Unification — all 8 verticals on `GovernanceEvaluationEngine`
- `replit.md` — Real Estate vertical entry (ADR-RES-001)
