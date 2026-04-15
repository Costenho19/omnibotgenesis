# ADR-113: Medical AI Governance Vertical (ADR-MED-001)

**Status:** ACCEPTED  
**Date:** 15 April 2026  
**Internal Code:** ADR-MED-001  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Scope:** `omnix_core/medical/` · `omnix_dashboard/blueprints/medical_governance.py` · `omnix_web/src/pages/MedicalDashboard.tsx` · `omnix_web/src/pages/MedicalGovernanceDemo.tsx`  
**Engine Integration:** `ADR-115` — connected to `GovernanceEvaluationEngine` on 15 April 2026

---

## Context

Clinical AI systems — diagnostic inference engines, surgical decision support, drug dosage
calculators, triage algorithms — are making decisions that directly affect patient safety.
Without an independent governance layer, these systems can approve contraindicated treatments,
override consent requirements, or operate outside jurisdictional regulatory frameworks without
any auditable trail.

OMNIX extends its 11-checkpoint pipeline to the Medical AI domain, providing pre-execution
governance for every clinical decision before it is committed to a care workflow. The vertical
is built for FDA-SaMD-level audit precision and EU MDR compliance.

---

## Decision

Build a full-stack medical AI governance vertical applying the OMNIX 11-checkpoint pipeline
adapted to clinical decision parameters, with domain-mandatory hard blocks for ethics and
informed consent that bypass the engine entirely (no score override possible).

**Engine connection** (ADR-115): As of 15 April 2026, medical decisions route through
`GovernanceEvaluationEngine.evaluate(domain="medical_ai")` — the same engine instance
used by Trading, Credit, Insurance, and Robotics. Hard blocks (ethics flag, consent
not verified) are checked pre-engine and return BLOCKED without scoring.

---

## Signal Adapter

**File:** `omnix_core/medical/medical_signal_adapter.py`

Maps 8 clinical parameters to 6 OMNIX governance signals:

| Clinical Parameter | OMNIX Signal | Interpretation |
|-------------------|-------------|----------------|
| `diagnostic_confidence` + `sensor_confidence` | `probability_score` | Clinical probability of correct outcome |
| `patient_risk_score` + `contraindication_score` | `risk_exposure` | Patient harm risk |
| `evidence_completeness` + `care_plan_alignment` | `signal_coherence` | Evidence-protocol coherence |
| `recovery_trend` + `comorbidity_index` | `trend_persistence` | Patient trajectory stability |
| `prior_adverse_events` (inverted) + `comorbidity_index` | `stress_resilience` | Resilience under adverse conditions |
| `ethics_flag` (inverted) + `consent_verified` + `off_label_use` (inverted) | `logic_consistency` | Regulatory and ethical alignment |

### Hard blocks (pre-engine, not scored)

| Condition | Block reason |
|-----------|-------------|
| `ethics_flag = True` | `CP-7: Ethics flag raised — clinical review required` |
| `consent_verified = False` | `CP-7: Informed consent not verified — BLOCK` |

Hard blocks return BLOCKED at `decision_score = composite × 0.15` — penalised to signal
that the block was regulatory, not marginal signal failure.

---

## Simulator

**File:** `omnix_core/medical/medical_simulator.py`

24/7 simulator for live data generation:

| Parameter | Value |
|-----------|-------|
| Cycle interval | 240 seconds |
| Decisions per cycle | 3–8 |
| Decision types | `diagnosis_inference` (30%) · `treatment_recommendation` (25%) · `drug_dosage` (20%) · `surgical_planning` (15%) · `triage_priority` (10%) |
| Device types | `diagnostic_ai` · `surgical_robot` · `monitoring_system` · `drug_dispensing` · `triage_engine` |
| Patient profiles | `low_risk` · `chronic` · `elderly` · `pediatric` · `critical` |
| Jurisdictions | EU, UK, US, GCC, APAC |
| Tables | `medical_decisions` + `medical_cycle_metrics` |
| Engine | `GovernanceEvaluationEngine(domain="medical_ai")` — live since ADR-115 |

---

## Flask Blueprint

**File:** `omnix_dashboard/blueprints/medical_governance.py`

Endpoints at `/api/medical/*`:

| Endpoint | Purpose |
|----------|---------|
| `/api/medical/metrics` | Aggregate KPIs |
| `/api/medical/decisions` | Decision list |
| `/api/medical/by-type` | Breakdown by decision type |
| `/api/medical/by-device` | Breakdown by device type |
| `/api/medical/by-jurisdiction` | Breakdown by jurisdiction |
| `/api/medical/timeline` | 24h timeline |
| `/api/medical/live-feed` | Last 30 decisions |
| `/api/medical/evaluate` | Single decision evaluation |
| `/api/medical/health` | Health check |

---

## Frontend

### `/governance-demo-medical` → `MedicalGovernanceDemo.tsx`
Interactive 11-checkpoint demo:
- Decision type, device type, patient profile, jurisdiction selectors
- Sliders: diagnostic confidence, patient risk, evidence completeness, care plan alignment, recovery trend
- Hard block toggles: ethics flag, consent verified, off-label use
- Animated pipeline evaluation with per-checkpoint clinical reasoning
- Badge: **ADR-113**

### `/medical` → `MedicalDashboard.tsx`
Live operations dashboard:
- 7 KPI cards: total decisions, approved, blocked, approval rate, avg diagnostic confidence, avg patient risk, ethics blocks
- Average signal health strip (6 signals)
- Breakdown tables: by decision type, by device type, by jurisdiction
- Live decision feed (30 decisions, 10s refresh)
- 3 feature callout cards: PQC receipts, ethics hard blocks, FDA-SaMD audit trail

---

## Infrastructure integration

| File | Change |
|------|--------|
| `omnix_dashboard/blueprints/__init__.py` | `medical_bp` imported and exported |
| `omnix_dashboard/app.py` | Blueprint registered, tables initialized eagerly, simulator started |
| `omnix_web/src/App.tsx` | Routes `/governance-demo-medical` + `/medical` |
| `omnix_web/src/pages/ClientDashboard.tsx` | `medical_ai: '🏥' / #f472b6` |
| `omnix_web/src/pages/AuditDashboard.tsx` | `medical_ai: '🏥' / #f472b6` |
| `omnix_core/evidence/decision_receipt.py` | `"medical_ai": "MED"` in `_DOMAIN_CODES` |

---

## Regulatory frameworks covered

| Framework | Alignment |
|-----------|-----------|
| EU MDR (Medical Device Regulation) | CP-7 (ethics) + CP-11 (jurisdiction/CE marking) |
| FDA 21 CFR Part 11 (SaMD) | Audit trail + PQC-signed receipt per decision |
| ISO 13485 Medical Device QMS | 11-checkpoint governance as quality control gate |
| GDPR Article 22 (automated decisions) | Hard block on consent_verified = False |
| EU AI Act — High-Risk AI Systems | Full 11-checkpoint pipeline, ethics gate |

---

## References

- ADR-026: Multi-vertical domain adapter architecture (foundational)
- ADR-044: Quantum-Secure Decision Receipts
- ADR-115: Engine Unification — all 8 verticals on `GovernanceEvaluationEngine`
- `replit.md` — Medical vertical entry (ADR-MED-001)
