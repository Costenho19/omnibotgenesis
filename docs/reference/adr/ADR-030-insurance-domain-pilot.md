# ADR-030: Insurance Domain Pilot — Multi-Domain Extensibility Validated

**Status**: ACCEPTED  
**Date**: March 1, 2026  
**Author**: Harold Nunes  
**Category**: Architecture / Strategic Validation  
**Depends on**:
- ADR-026 (Multi-Vertical Governance Architecture — Domain Adapter Pattern)
- ADR-027 (Decision Governance Infrastructure — Category Creation)
- ADR-028 (External Governance API — POST /api/governance/evaluate)
- ADR-029 (Governance Compliance Modules — NIST AI RMF + ISO 42001 + EU AI Act)

---

## Context

ADR-026 (Feb 15, 2026) proposed the Domain Adapter Pattern — a technical architecture that decouples domain-specific signal generation from the domain-agnostic 6-checkpoint governance engine. It documented trading as the validated vertical (670,000+ cycles) and positioned credit, supply chain, and insurance as future verticals.

Concurrently, an interactive insurance demo was built in the frontend (`omnix_web/src/pages/InsuranceGovernanceDemo.tsx`) demonstrating how OMNIX's 6 checkpoints apply to insurance underwriting decisions (BIND / REFER / DECLINE). This demo operated on simulated frontend-only logic.

This ADR documents the conversion of that frontend demonstration into **real, PQC-signed governance receipts** via the External Governance API (ADR-028). The insurance domain is now the **third validated domain** — alongside trading (production, 699,000+ cycles) and the HealthTech conceptual framework — with immutable on-chain evidence.

**Strategic positioning**: This is not a "pilot" in the product sense — no insurance company has been onboarded. It is a **demonstration of extensibility**: the same fail-closed engine that governs trading decisions can govern insurance underwriting decisions, generating a verifiable PQC-signed audit trail, without any changes to the core engine. This evidence directly supports the multi-vertical TAM claim in the Eureka Dubai GCC 2026 pitch.

---

## Decision

Execute 3 real API calls to `POST /api/governance/evaluate` with `domain: "insurance"` using the Domain Adapter signal mapping. The results are immutable in the PQC receipt chain and publicly verifiable.

**New B2B Client Created**: `insurance-pilot-01` (role: standard, active since March 1, 2026)

---

## Signal Mapping (Insurance Domain Adapter)

| OMNIX Signal | Threshold | Insurance Interpretation |
|---|---|---|
| `probability_score` | ≥ 50 | Probability the policy/claim does NOT result in a loss event |
| `risk_exposure` | ≤ 65 | Coverage concentration + geographic zone + claims history (inverted) |
| `signal_coherence` | ≥ 55 | Agreement between age, claims history, and geographic risk signals |
| `trend_persistence` | ≥ 50 | Sustained clean claims history — no worsening trend |
| `stress_resilience` | ≥ 35 | Resilience under hard market conditions / catastrophic events |
| `logic_consistency` | ≥ 40 | Internal consistency across risk signals |

Full adapter specification: `docs/reference/domain-adapters/insurance-domain-adapter.md`

---

## Real Results — PQC-Signed Receipts

All 3 receipts were generated on **March 1, 2026** and are publicly verifiable at `https://omnibotgenesis-production.up.railway.app/verify`.

### Scenario A — Viable Auto Policy (APPROVED)

**Profile**: 35-year-old driver, 0 prior claims, low-risk geographic zone, stable market

| Signal | Score | Threshold | Result |
|---|---|---|---|
| probability_score | 78 | ≥ 50 | PASS |
| risk_exposure | 42 | ≤ 65 | PASS |
| signal_coherence | 76 | ≥ 55 | PASS |
| trend_persistence | 71 | ≥ 50 | PASS |
| stress_resilience | 63 | ≥ 35 | PASS |
| logic_consistency | 74 | ≥ 40 | PASS |

**Decision**: APPROVED (6/6 checkpoints passed)  
**Receipt ID**: `OMNIX-AB1D878EC56A`  
**Asset**: AUTO-POL-2847  
**Timestamp**: 2026-03-01T05:36:21Z  
**Signature**: Dilithium-3 (ML-DSA-65, NIST-standardized)  
**Insurance Interpretation**: BIND — all governance gates cleared, policy may be issued automatically

---

### Scenario B — High-Risk Auto Policy (BLOCKED)

**Profile**: 28-year-old driver, 4 prior claims, high-risk zone (flood-prone), hard market

| Signal | Score | Threshold | Result |
|---|---|---|---|
| probability_score | 22 | ≥ 50 | VETO |
| risk_exposure | 85 | ≤ 65 | VETO |
| signal_coherence | 28 | ≥ 55 | VETO |
| trend_persistence | 8 | ≥ 50 | VETO |
| stress_resilience | 19 | ≥ 35 | VETO |
| logic_consistency | 31 | ≥ 40 | VETO |

**Decision**: BLOCKED (6/6 checkpoints vetoed)  
**Receipt ID**: `OMNIX-B5782882E993`  
**Asset**: AUTO-POL-9999  
**Timestamp**: 2026-03-01T05:36:39Z  
**Veto Chain**: CP-1 · CP-2 · CP-3 · CP-4 · CP-5 · CP-6  
**Signature**: Dilithium-3 (ML-DSA-65, NIST-standardized)  
**Insurance Interpretation**: DECLINE — unanimous veto across all 6 governance checkpoints

---

### Scenario C — Borderline Life Policy (BLOCKED — Partial Veto)

**Profile**: 62-year-old, 2 prior claims, moderate-risk zone, hardening market

| Signal | Score | Threshold | Result |
|---|---|---|---|
| probability_score | 52 | ≥ 50 | PASS |
| risk_exposure | 61 | ≤ 65 | PASS |
| signal_coherence | 54 | ≥ 55 | VETO |
| trend_persistence | 38 | ≥ 50 | VETO |
| stress_resilience | 42 | ≥ 35 | PASS |
| logic_consistency | 49 | ≥ 40 | PASS |

**Decision**: BLOCKED (2/6 checkpoints vetoed — fail-closed)  
**Receipt ID**: `OMNIX-C23154E3D1B0`  
**Asset**: LIFE-POL-4521  
**Timestamp**: 2026-03-01T05:36:42Z  
**Veto Chain**: CP-3:Signal Coherence · CP-4:Trend Persistence  
**Signature**: Dilithium-3 (ML-DSA-65, NIST-standardized)  
**Insurance Interpretation**: REFER — borderline profile blocked by declining claims trend and insufficient signal coherence. Requires human underwriter review.

**Notable**: The borderline scenario demonstrates the fail-closed architecture elegantly. Probability and risk scores are borderline acceptable, but the coherence gate (54 vs. 55 threshold) and trend gate (38 vs. 50 threshold) independently veto. One checkpoint is enough to block. This mirrors how ECW behaves in trading: patience over marginal edge.

---

## Regulatory Alignment

| Regulation | Article | How OMNIX Addresses It |
|---|---|---|
| **GDPR** | Art. 22 | Automated decision-making on individuals — explainable checkpoint trace provided, human override available (Module 3, ADR-029) |
| **EU AI Act** | Art. 9 | Risk management system — governance_risk_map entry (classification: CRITICAL) documents risk posture |
| **EU AI Act** | Art. 14 | Human oversight — every BLOCKED receipt can receive a PQC-signed override record (complementary, does not alter chain) |
| **Solvency II** | Pillar II | Internal governance requirements — immutable PQC receipt chain provides audit-grade decision lineage |
| **IDD** | Art. 20 | Product oversight — every underwriting decision is traced through structured risk assessment |

---

## Market Context

| Metric | Value |
|---|---|
| Global insurance market size | ~$6.3T premium volume (2024) |
| Claims processing automation TAM | ~$3.8B (2025, growing ~14% CAGR) |
| Underwriting automation TAM | ~$2.1B |
| OMNIX addressable segment | Governance layer for automated decisions — not replacement of actuarial models |

Insurance is listed as Phase 5 (Year 3+) in ADR-026's implementation roadmap — this pilot does not accelerate that timeline. It validates the extensibility claim with real evidence.

---

## Strategic Consequences

### What This Proves

1. **Domain-agnostic is real, not theoretical**: The same API endpoint, the same 6 checkpoints, the same PQC signing — zero engine changes required to govern insurance decisions
2. **Signal mapping is the adapter**: Domain expertise translates raw data to 6 signals. The governance engine is indifferent to the domain
3. **Fail-closed works across domains**: Scenario C demonstrates that the fail-closed architecture correctly catches borderline cases with the same precision as it does in trading
4. **Audit trail is immediate**: 3 receipts, publicly verifiable, generated in under 1 minute

### What This Does NOT Prove

- That an insurance company would pay for this today
- That actuarial models have been validated in production
- That OMNIX can replace underwriting software

### Pitch Positioning

Do NOT say: *"We have an insurance pilot"*  
DO say: *"The same engine that has governed 699,000+ trading decisions can govern insurance underwriting decisions — here are 3 PQC-signed receipts from today proving it. The governance infrastructure scales across domains."*

This is the narrative of extensibility, not the narrative of a vertical product.

---

## Evidence Summary

| Receipt ID | Domain | Asset | Decision | Checkpoints |
|---|---|---|---|---|
| `OMNIX-AB1D878EC56A` | insurance | AUTO-POL-2847 | APPROVED | 6/6 passed |
| `OMNIX-B5782882E993` | insurance | AUTO-POL-9999 | BLOCKED | 6/6 vetoed |
| `OMNIX-C23154E3D1B0` | insurance | LIFE-POL-4521 | BLOCKED | 4 pass, 2 veto |

All verifiable at: `https://omnibotgenesis-production.up.railway.app/verify`  
All signed with Dilithium-3 (ML-DSA-65, NIST-standardized post-quantum algorithm)  
All stored in immutable PQC hash chain — cannot be altered retroactively

---

## References

- [ADR-026](ADR-026-multi-vertical-governance-architecture.md) — Domain Adapter Pattern
- [ADR-027](ADR-027-category-creation-decision-governance-infrastructure.md) — DGI Category Creation
- [ADR-028](ADR-028-external-signal-evaluation-api.md) — External Governance API
- [ADR-029](ADR-029-governance-compliance-modules.md) — Governance Compliance Modules
- `docs/reference/domain-adapters/insurance-domain-adapter.md` — Signal mapping specification
- `omnix_web/src/pages/InsuranceGovernanceDemo.tsx` — Interactive frontend demonstration

---

*Decision accepted: March 1, 2026*  
*Third domain validated. Trading (699K+ cycles) + Insurance (3 real receipts) + HealthTech (conceptual framework). All via same governance engine, zero core changes.*
