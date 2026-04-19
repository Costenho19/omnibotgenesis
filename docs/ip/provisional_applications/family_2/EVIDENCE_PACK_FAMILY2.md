# EVIDENCE PACK — PATENT FAMILY 2
# NON-MARKOVIAN ADAPTIVE SIGNAL PROCESSING SYSTEM
# INTERNAL DOCUMENT — CONFIDENTIAL

**Document Reference:** OMNIX-PAT-2026-002-EVD
**Date:** [DATE OF FILING]
**Purpose:** To document the development timeline and evidentiary record supporting the priority date claim of provisional application OMNIX-PAT-2026-002.

> **Note:** This Evidence Pack is an internal document. It is not filed with the USPTO.

---

## SECTION 1 — GIT REPOSITORY EVIDENCE

### 1.1 Key Commit Timeline — Family 2 Subject Matter

| Date | Commit Description | Relevance to Family 2 |
|------|-------------------|----------------------|
| November 18, 2025 | First commit — signal processing modules included | Earliest date of signal processing codebase |
| November 22, 2025 | EMA and HMM signal modules integrated | Independent signal sources for DCI established |
| November 27, 2025 | PQC integration begun; Kyber/Dilithium modules introduced | Post-quantum layer active in codebase |
| December 2025 | Non-Markovian kernel formulation implemented | Core K(t−s) formula implemented in production code |
| December 30, 2025 | Signal normalization standardized | Normalized signal set (P, R, C, T, S, L) confirmed |
| January 15, 2026 | Official Day 1 — CAES active in production | Production deployment of CAES with real telemetry |
| February 17, 2026 | Patent draft v2.0 — Family 2 claims documented | Formal documentation of kernel and CAES claims |

> **Instructions for inventor:** Retrieve exact commit hashes from GitHub for each entry and record them here.

---

## SECTION 2 — ARCHITECTURE DECISION RECORDS

| ADR | Title | Relevance | Date |
|-----|-------|-----------|------|
| ADR-012 | Learning Baseline Freeze | Production deployment date — CAES and kernel operational | January 15, 2026 |
| ADR-064 | Assumption Validity Monitor | AVM tracks regime classification drift | April 9, 2026 |

**Note on kernel parameters:** The specific calibration of τ ≈ 12 hours, ε ≈ 0.35, and Ω ≈ π/6 is documented in the codebase and in the patent draft. These values are not arbitrary but were determined through empirical calibration against live market data during the Learning Baseline period (November 2025 – January 14, 2026), as documented in ADR-007.

---

## SECTION 3 — PRODUCTION DEPLOYMENT EVIDENCE

The CAES and Non-Markovian Memory Kernel have been in production operation since January 15, 2026, generating real position sizing recommendations evaluated against governance checkpoint criteria.

| Metric | Value |
|--------|-------|
| Production platform | Railway |
| Active since | January 15, 2026 |
| Integration | CAES output feeds DCI module at CP-6 of governance pipeline |

---

## SECTION 4 — PRIOR ART SEARCH NOTES

| Search Query | Result |
|---|---|
| "Non-Markovian memory kernel regime detection finance" | No prior art combining oscillatory exponential decay kernel with financial regime classification and confidence-adaptive position sizing found |
| "oscillatory exponential decay signal weighting time series" | Academic literature on non-Markovian processes found; no application to financial regime detection with CAES found |
| "confidence adaptive position sizing sigmoid function" | No prior art found for sigmoid-based aggression function applied to regime confidence score for position sizing |
| "regime multiplier lookup table position sizing" | No prior art found for the specific eleven-sub-state regime multiplier table described |

---

## SECTION 5 — FILING CHECKLIST

- [ ] Cover Sheet completed and signed
- [ ] Specification document complete
- [ ] All placeholders replaced
- [ ] Filing fee ($320 Micro Entity) prepared
- [ ] Git commit hashes retrieved and recorded
- [ ] Kernel implementation code exported and retained
- [ ] CAES implementation code exported and retained
- [ ] This Evidence Pack retained securely

---

*Document Reference: OMNIX-PAT-2026-002-EVD*
*Inventor: Harold Alberto Nunes Rodelo*
*Date: [DATE OF FILING]*
*© 2026 OMNIX Quantum Ltd. CONFIDENTIAL — NOT FOR FILING WITH USPTO.*
