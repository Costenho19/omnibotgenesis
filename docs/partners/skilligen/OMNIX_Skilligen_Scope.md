# OMNIX × Skilligen HDI — Integration Scope
## Technical Collaboration Document

**Status:** Draft — Pending formal proposal
**Date:** 14 April 2026
**Prepared by:** Harold Alberto Nunes Rodelo — OMNIX Quantum Ltd

---

## 1. Context

OMNIX Quantum Ltd and Skilligen HDI are exploring a technical partnership to embed decision governance infrastructure into HDI (Human Decision Infrastructure) workflows. This document outlines the initial scope of exploration.

---

## 2. What OMNIX Brings

| Capability | Description |
|-----------|-------------|
| 11-Checkpoint Governance Pipeline | Real-time deterministic evaluation: signal integrity, risk, coherence, ethics, AML, fraud, jurisdiction |
| Post-Quantum Receipts | CRYSTALS-Dilithium3 signed audit trails — W3C Verifiable Credential format |
| Domain Adapters | Trading, credit, insurance, robotics, medical, energy, real estate, agents |
| B2B API | REST API with per-client quota enforcement, RBAC, webhook push |
| Regulatory Alignment | EU AI Act checkpoint coverage (points 1–4, 6–8), EUDI-compatible receipt format |
| Audit Layer | Immutable hash-chained decision log, public verification endpoint |

---

## 3. Proposed Integration Points

### 3.1 HDI Decision Governance Layer
Embed OMNIX governance evaluation within Skilligen's human decision workflows. Each decision recommendation from the HDI platform passes through the OMNIX 11-checkpoint pipeline before execution. Output: signed governance receipt.

### 3.2 Compliance Evidence for Enterprise Clients
Skilligen's enterprise clients receive W3C Verifiable Credentials per decision — usable for regulatory audits, EU AI Act compliance documentation, and internal governance reporting.

### 3.3 Custom Domain Adapter
If Skilligen HDI operates a proprietary domain, OMNIX can develop a dedicated domain adapter (e.g., `hdi_decisions` table, custom checkpoint weights) under a separate technical agreement.

---

## 4. Technical Requirements (Preliminary)

- OMNIX B2B API key provisioned for Skilligen HDI
- Signal schema mapping: Skilligen HDI signals → OMNIX input format
- Webhook endpoint on Skilligen side for receipt push
- Sandbox evaluation access during pilot phase

---

## 5. Next Steps

| Step | Owner | Target |
|------|-------|--------|
| Technical demo — 11-checkpoint pipeline | Harold (OMNIX) | TBD |
| Signal schema review | Both | TBD |
| Pilot domain definition | Dr. Amanulla Khan | TBD |
| Formal integration proposal | Harold (OMNIX) | TBD |
| Pilot SLA & commercial terms | Both | TBD |

---

## 6. Contact

**OMNIX Quantum Ltd**
Harold Alberto Nunes Rodelo
contacto@omnixquantum.net

**Skilligen HDI**
Dr. Amanulla Khan
aman@skilligen.com
