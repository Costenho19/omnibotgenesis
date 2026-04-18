# ADR-052: Islamic Credit Governance Vertical

**Date**: March 27, 2026  
**Status**: ACCEPTED  
**Author**: Harold Nunes, Solo Founder & CEO  
**Category**: Domain Expansion — Multi-Vertical Governance  
**Tags**: `credit`, `islamic-finance`, `multi-vertical`, `sharia`, `domain-adapter`

---

## Context

OMNIX Decision Governance Infrastructure was designed from inception as domain-agnostic (ADR-026: Multi-Vertical Governance Architecture). The trading vertical validated the 8-checkpoint pipeline in a high-frequency, high-stakes environment. ADR-052 activates the first non-trading vertical: **Islamic Credit Governance**.

Islamic finance is the highest-priority target because:

1. **UAE regulatory mandate**: Central Bank of UAE requires audit trails for automated credit decisions
2. **Sharia compliance gate already built**: CP-6 Sharia Gate (ADR-046) is fully implemented and production-ready
3. **Largest addressable market in GCC**: $3.8T Islamic finance industry, growing at 7.5% CAGR
4. **No comparable governance solution exists**: Banks use rule-based systems without cryptographic audit trails
5. **Clearest ROI story**: A blocked high-risk application at AED 5M with 35% PD = AED 1.75M protected per decision

---

## Decision

Implement the Islamic Credit Governance Vertical as a second production engine running 24/7 alongside the trading engine, using the **same governance pipeline** with a domain adapter for credit signals.

### Architecture

```
UAE/GCC Credit Applications
        │
        ▼
CreditMacroDataProvider          ← Real macroeconomic data (Alpha Vantage, FRED)
        │                           Fed Funds Rate, credit spreads, VIX proxy
        ▼
CreditSignalAdapter              ← Domain adapter (new — ADR-052)
        │                           Maps 12 credit params → 8 OMNIX signals
        │
        ├── probability_score   = Creditworthiness (credit score + DSR + collateral)
        ├── risk_exposure       = Default risk index (PD × LGD proxy)
        ├── signal_coherence    = Indicator agreement (all signals aligned?)
        ├── trend_persistence   = Macro credit conditions stability
        ├── stress_resilience   = Income shock test (-20% income scenario)
        ├── logic_consistency   = Application internal consistency check
        ├── signal_integrity    = Data completeness score
        └── temporal_coherence = Macro data recency
        │
        ▼
GovernanceEvaluationEngine       ← UNCHANGED — same 8-checkpoint pipeline
        │
        ├── CP-0: Signal Integrity Validation
        ├── CP-1: Probability Check (creditworthiness ≥ 50)
        ├── CP-2: Risk Limits (default risk ≤ 65)
        ├── CP-3: Signal Coherence (indicator agreement ≥ 55)
        ├── CP-4: Trend Persistence (macro stability ≥ 50)
        ├── CP-5: Stress Resilience (income shock ≥ 35)
        ├── CP-6: Sharia Compliance Gate ← Islamic finance specific
        └── CP-7: Temporal Coherence (data freshness ≥ 45)
        │
        ▼
PQC-Signed Decision Receipt      ← UNCHANGED — Dilithium-3 signature
        │
        ▼
PostgreSQL (credit_applications) ← New domain tables
```

### Key Design Choices

**1. Signal mapping is the only new code**  
The governance pipeline receives the same 8 normalized signals regardless of domain. The adapter is the only domain-specific component. This is the domain adapter pattern from ADR-026.

**2. CP-6 Sharia Gate repurposed for credit context**  
In the trading vertical, CP-6 screens asset symbols and financing structures. In the credit vertical, it screens:
- Sector halal compliance
- Riba (interest) prohibition — asset-backed structures only
- Gharar (uncertainty) limit ≤ 65
- DSR ≤ 40% (Islamic standard, stricter than conventional 50-60%)
- Asset backing ratio ≥ 50% for Murabaha/Ijara structures

**3. Macro conditions are real**  
Unlike trading where market data is live from Kraken, credit macro conditions are sourced from Alpha Vantage (already integrated — Federal Funds Rate, economic indicators) with FRED as fallback. These are real, current rates that influence all credit governance decisions.

**4. Simulation is calibrated, not random**  
Applications are generated using:
- UAE market statistics (SME 60%, Individual 30%, Corporate 10%)
- Realistic credit score distributions (mean ~650, σ 75)
- Actual UAE Islamic finance instruments (Murabaha 60%, Ijara 20%, Musharaka 15%)
- Amount ranges calibrated to UAE/GCC market data
- Macro stress influences applicant quality distribution

**5. PQC receipts are identical to trading receipts**  
A credit governance receipt has the same cryptographic properties as a trading decision receipt — Dilithium-3 signature, SHA-256 hash chain, Merkle root anchor. Verifiable at omnixquantum.net/verify.

---

## Islamic Finance Signal Mapping (Detail)

### Credit Parameters → OMNIX Signals

| OMNIX Signal | Credit Metric | Formula |
|---|---|---|
| `probability_score` | Creditworthiness | `(CS_norm×0.4 + DSR_norm×0.25 + Coll_norm×0.20 + Macro_adj×0.15)` |
| `risk_exposure` | Default risk | `min(95, PD×LGD×300)` |
| `signal_coherence` | Indicator agreement | `100 - std_dev(CS, DSR, Collateral, Macro)×0.8` |
| `trend_persistence` | Macro stability | `(Volatility_score×0.5 + VIX_score×0.3 + Spread_stability×0.2)` |
| `stress_resilience` | Income shock | `(residual_at_-20%_income / threshold) × 70 + 30` |
| `logic_consistency` | App consistency | `100 - penalty_sum(contradictions)` |
| `signal_integrity` | Data quality | `100 - missing_field_penalties` |
| `temporal_coherence` | Data freshness | `freshness×0.3×100 + stability×0.7` |

### Sharia CP-6 Evaluation Matrix

| Parameter | Islamic Standard | Block if |
|---|---|---|
| Sector | Halal sectors only | Haram sector detected |
| Structure | Asset-backed only | Riba (interest) present |
| Gharar | Uncertainty ≤ 65 | Gharar score > 65 |
| DSR | ≤ 40% monthly income | DSR > 40% |
| Asset backing | ≥ 50% for Murabaha/Ijara | Ratio < 50% |

---

## Credit Application Schema

New table: `credit_applications`  
New table: `credit_cycle_metrics`

Key fields beyond standard governance:
- `financing_type`: Murabaha | Ijara | Musharaka | Diminishing_Musharaka  
- `gharar_score`: Uncertainty score 0-100  
- `sharia_compliant`: Boolean + violation reason  
- `pd_estimate`: Probability of Default (0-1)  
- `lgd_estimate`: Loss Given Default (0-1)  
- `outcome`: Future field for REPAID/DEFAULTED — enables calibration loop

---

## Simulation Engine

**Cycle**: Every 300 seconds (5 minutes)  
**Batch**: 3-8 applications per cycle  
**24/7**: Runs as daemon thread alongside Flask Dashboard

**Calibration to UAE market**:
- SME applications: AED 100K – 5M
- Individual financing: AED 50K – 500K (home/vehicle/education)
- Corporate: AED 1M – 50M
- Sectors: technology, real estate, healthcare, retail, F&B, manufacturing, logistics
- Financing types: Murabaha (60%), Ijara (20%), Musharaka (15%), Diminishing (5%)

---

## New API Endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/credit/metrics` | KPIs: approvals, blocks, amounts, Sharia rate |
| GET | `/api/credit/applications` | Recent applications with decisions |
| GET | `/api/credit/sectors` | Sector breakdown |
| GET | `/api/credit/timeline` | Hourly/daily timeline |
| POST | `/api/credit/evaluate` | Manual evaluation |
| GET | `/api/credit/macro` | Current macro conditions |
| GET | `/api/credit/health` | Engine status |

---

## New Web Routes

| Route | Page |
|---|---|
| `/credit` | CreditLiveDashboard — live metrics, pipeline visual, application feed |

---

## Transition to Production (Real Applications)

The simulation → production transition is a data source swap:

```python
# SIMULATION (today):
app = generate_credit_application(macro_stress=macro.market_stress_index)

# PRODUCTION (bank integration):
app = CreditApplication.from_bank_api(bank_payload)  # Same schema, real data
```

The governance engine, receipts, checkpoints, and database schema are unchanged.

---

## Business Model (B2B)

**Pricing model**: Per-evaluation + SaaS tier  
- Tier 1: AED 15/evaluation (spot)
- Tier 2: AED 8/evaluation (10K+ monthly)
- Tier 3: Custom (enterprise, includes SLA + dedicated receipt API)

**Target customers**:
- UAE Islamic banks (ADIB, DIB, FAB Islamic, Mashreq Islamic)
- GCC digital lending platforms
- Saudi Vision 2030 fintech cohorts
- ADGM-regulated credit providers

**Regulatory hook**: UAE Central Bank Circular #2/2023 requires automated credit decisions to maintain an audit trail. OMNIX provides this natively with cryptographic proof.

---

## Consequences

**Positive**:
- Second vertical running with same infrastructure investment — validates multi-vertical model
- Sharia gate demonstrates domain specialization capability
- UAE/GCC regulatory tailwind creates urgency for target customers
- Every receipt generated is verifiable proof of governance without disclosing credit data

**Risks**:
- Simulation data doesn't include real borrower behavior diversity
- Calibration improves once real application data flows through
- CP-6 Sharia evaluation is heuristic-based — production would require certified Sharia scholar review layer

**Mitigations**:
- Simulation clearly labeled (simulation_run=TRUE in database)
- Sharia layer designed as advisory gate that can be upgraded to scholar-validated ruleset
- All transparency notes visible on dashboard

---

## Related ADRs

- ADR-026: Multi-Vertical Governance Architecture
- ADR-028: External Signal Evaluation API
- ADR-037: Per-Client Configurable Thresholds
- ADR-046: Sharia Governance Gate (CP-6)
- ADR-047: AML Governance Gate
- ADR-048: Fraud Detection Gate
- ADR-049: Jurisdiction Compliance Gate

---

*Next verticals: Insurance Underwriting (ADR-053), Supply Chain (ADR-054)*
