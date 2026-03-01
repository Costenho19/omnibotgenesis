# OMNIX Domain Adapter — Insurance Claim & Underwriting Governance

**Status**: VALIDATED-PILOT  
**Date**: March 1, 2026  
**Author**: Harold Nunes  
**Depends on**: ADR-026 (Domain Adapter Pattern), ADR-027 (Decision Governance Infrastructure), ADR-028 (External Governance API), ADR-029 (Governance Compliance Modules)  
**Related**: `omnix_web/src/pages/InsuranceGovernanceDemo.tsx` (interactive frontend demo)

---

## Overview

This adapter documents how OMNIX's 6-checkpoint governance engine applies to insurance decisions — specifically policy underwriting and claim authorization. The same fail-closed architecture that has governed 699,000+ trading evaluation cycles can govern whether an insurance policy should be bound, referred for manual review, or declined.

The OMNIX engine does not replace actuarial models. It governs the **decision output** of those models — applying a structured, auditable, PQC-signed checkpoint layer before any automated binding or payout occurs. This is the same role it plays in trading: not predicting markets, but governing whether to act on predictions.

**Real Pilot**: As of March 1, 2026, this adapter has been validated with real API calls generating PQC-signed governance receipts. See ADR-030 for receipt IDs and outcomes.

---

## Signal Mapping

The 6 normalized signals (0–100 scale) map to insurance-specific data as follows:

| Signal | Threshold | Insurance Interpretation | Derivation |
|--------|-----------|--------------------------|------------|
| `probability_score` | ≥ 50 | Probability that the policy/claim does **not** result in a loss event (1 − adjustedClaimProb × 100) | Base risk by policy type + claims history penalty + coverage ratio adjustment |
| `risk_exposure` | ≤ 65 | Concentration of risk across coverage amount, geographic zone, and claims history (lower = safer) | coverageExposure + geoExposure + claimsExposure, normalized 0–100 (inverted) |
| `signal_coherence` | ≥ 55 | Agreement between independent risk signals: age factor, claims trend, and geographic zone (higher = more consistent picture) | ageSignal×0.25 + claimsSignal×0.50 + geoSignal×0.25 |
| `trend_persistence` | ≥ 50 | Sustained positive history — no worsening claims trend over time | claimsTrend score × (ageFactor×0.6 + geoFactor×0.4) |
| `stress_resilience` | ≥ 35 | Ability to withstand adverse market conditions (hard market, catastrophic events) | marketStress×0.60 + claimsStress×0.40 |
| `logic_consistency` | ≥ 40 | Internal consistency — signals do not contradict each other | 100 − normalized variance across all signals |

### Checkpoint Interpretation for Insurance

| Checkpoint | Generic Function | Insurance Meaning |
|-----------|-----------------|------------------|
| CP-1 (Probability) | Is this likely to succeed? | Is the applicant/claim statistically low-risk? |
| CP-2 (Risk Limits) | Would this exceed safe exposure? | Does coverage exceed concentration limits? |
| CP-3 (Signal Agreement) | Do multiple models agree? | Do age, history, and geography tell a consistent story? |
| CP-4 (Trend Confirmation) | Is this sustained, not noise? | Is the positive history a real trend or a recent anomaly? |
| CP-5 (Stress Test) | What if conditions deteriorate? | Would this hold up in a hard market or catastrophic event? |
| CP-6 (Logic Check) | Are signals contradicting each other? | Are there internal contradictions in the risk profile? |

---

## Decision Outputs

| OMNIX Decision | Insurance Meaning | Action |
|----------------|------------------|--------|
| `APPROVED` | All 6 checkpoints passed | BIND — issue the policy or authorize payout |
| `HOLD` | Partial pass — borderline profile | REFER — mandatory human underwriter review |
| `BLOCKED` | One or more checkpoints vetoed | DECLINE — reject or flag for investigation |

All decisions are returned with a **PQC-signed governance receipt** (Dilithium-3 / ML-DSA-65, NIST-standardized) providing an immutable, verifiable audit trail.

---

## Use Cases

| Insurance Line | Primary Checkpoints | Typical Block Triggers |
|---------------|--------------------|-----------------------|
| **Auto Insurance** | CP-1, CP-3, CP-4 | Frequent claims history, young driver + high-risk zone |
| **Life Insurance** | CP-1, CP-2, CP-5 | High coverage + advanced age + adverse health signals |
| **Health Insurance** | CP-1, CP-5 | Pre-existing conditions, sector stress (pandemic scenarios) |
| **Property Insurance** | CP-2, CP-5 | High-risk geographic zone, catastrophic event exposure |
| **Cyber Insurance** | CP-3, CP-6 | Inconsistent security posture signals, contradiction in coverage history |
| **Commercial Liability** | CP-2, CP-3, CP-6 | Sector concentration, inconsistent financial signals |

---

## Example Payloads

### Scenario A — Viable Auto Policy (Expected: APPROVED / HOLD)
Profile: 35-year-old driver, 0 claims, low-risk zone, stable market.

```json
{
  "signals": {
    "probability_score": 78,
    "risk_exposure": 42,
    "signal_coherence": 76,
    "trend_persistence": 71,
    "stress_resilience": 63,
    "logic_consistency": 74
  },
  "asset": "AUTO-POL-2847",
  "domain": "insurance",
  "metadata": {
    "policy_type": "auto",
    "applicant_age": 35,
    "claims_history": 0,
    "geographic_zone": "low_risk",
    "market_condition": "stable"
  }
}
```

### Scenario B — High-Risk Auto Policy (Expected: BLOCKED)
Profile: 28-year-old driver, 4 prior claims, high-risk zone (flood-prone), hard market.

```json
{
  "signals": {
    "probability_score": 22,
    "risk_exposure": 85,
    "signal_coherence": 28,
    "trend_persistence": 8,
    "stress_resilience": 19,
    "logic_consistency": 31
  },
  "asset": "AUTO-POL-9999",
  "domain": "insurance",
  "metadata": {
    "policy_type": "auto",
    "applicant_age": 28,
    "claims_history": 4,
    "geographic_zone": "high_risk",
    "market_condition": "hard"
  }
}
```

### Scenario C — Borderline Life Policy (Expected: HOLD / BLOCKED)
Profile: 62-year-old, 2 prior claims, moderate-risk zone, hardening market.

```json
{
  "signals": {
    "probability_score": 52,
    "risk_exposure": 61,
    "signal_coherence": 54,
    "trend_persistence": 38,
    "stress_resilience": 42,
    "logic_consistency": 49
  },
  "asset": "LIFE-POL-4521",
  "domain": "insurance",
  "metadata": {
    "policy_type": "life",
    "applicant_age": 62,
    "claims_history": 2,
    "geographic_zone": "moderate",
    "market_condition": "hardening"
  }
}
```

---

## Regulatory Alignment

| Regulation | Article | Relevance to OMNIX Insurance Governance |
|-----------|---------|----------------------------------------|
| **GDPR** | Art. 22 | Right not to be subject to automated decisions — OMNIX provides explainable checkpoint trace + human override capability (Module 3, ADR-029) |
| **EU AI Act** | Art. 9 | Risk management system — OMNIX Risk Map (Module 1) documents classification as CRITICAL for automated underwriting |
| **EU AI Act** | Art. 14 | Human oversight — every BLOCKED or HOLD decision is overridable via PQC-signed override record (Module 3, ADR-029) |
| **Solvency II** | Pillar II (Art. 41-49) | Internal governance and risk management — PQC-signed receipts provide immutable audit chain for regulatory reporting |
| **IDD** (Insurance Distribution Directive) | Art. 20 | Product oversight — governance receipts document that each underwriting decision passed structured risk assessment |

---

## Integration Notes

### API Endpoint

```
POST /api/governance/evaluate
Host: [your-omnix-instance]
X-API-Key: OMNIX-INS-{your_key}
X-Client-ID: insurance-pilot-01
Content-Type: application/json
```

### Human Oversight Override

When a BLOCKED decision requires manual override (EU AI Act Art. 14 compliance):

```
POST /api/governance/overrides
X-API-Key: {admin_key}
```

Override is a PQC-signed complementary audit record. The original BLOCKED receipt remains immutable in the hash chain. See Module 3 documentation (ADR-029).

### Public Receipt Verification

Any governance receipt can be publicly verified at:
```
GET /api/verify/{receipt_id}
```

Zero internal data is exposed. Verification confirms signature validity and decision hash integrity.

---

## References

- [ADR-026](../adr/ADR-026-multi-vertical-governance-architecture.md) — Domain Adapter Pattern architecture
- [ADR-027](../adr/ADR-027-category-creation-decision-governance-infrastructure.md) — Decision Governance Infrastructure category
- [ADR-028](../adr/ADR-028-external-signal-evaluation-api.md) — External Governance API specification
- [ADR-029](../adr/ADR-029-governance-compliance-modules.md) — Governance Compliance Modules (Risk Map, Oversight, Reporting)
- [ADR-030](../adr/ADR-030-insurance-domain-pilot.md) — Insurance Domain Pilot results with real receipt IDs
- `omnix_web/src/pages/InsuranceGovernanceDemo.tsx` — Interactive frontend demonstration (BIND/REFER/DECLINE simulation)

---

*Document created: March 1, 2026*  
*This adapter is validated with real PQC-signed receipts. See ADR-030 for evidence.*
