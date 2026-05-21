# ADR-176: OMNIX Governance API — Commercial Product Definition

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Supersedes:** None  
**Extends:** ADR-172 (ATORS) · ADR-171 (SGIP) · ADR-165 (OEP) · ADR-156–159 (ATF stack)  
**Related:** ADR-161 (GPIL) · ADR-170 (GECR) · ADR-173 (DSPP) · ADR-174 (AGVP) · ADR-175 (SSD)

---

## Context

### The Commercial Gap

OMNIX QUANTUM has built a complete, formally specified, post-quantum decision governance infrastructure:

- **67 invariants** across 13 protocol families (ATF, RGC, GPIL, ELR, EAP, OEP, FEA, FVP, GECR, SGIP, DSPP, AGVP, SSD)
- **3 published RFCs** with permanent DOIs (Zenodo + Figshare)
- **175 ADRs** — full architecture decision record
- **245+ tests** — institutional test suite
- **ATF Open Receipt Schema (ATORS)** — runtime-independent, machine-readable, verifiable offline
- **ML-DSA-65 / Dilithium-3 (FIPS 204)** — post-quantum cryptographic signing on every receipt
- **SGIP** — cross-runtime semantic interoperability protocol

This infrastructure exists as production code but has not been packaged as a commercial API product with clear tiers, legal positioning, and onboarding documentation.

### The Market Gap

The regulatory environment for AI governance is accelerating:

- EU AI Act (2024) — Article 9 mandates risk management systems for high-risk AI
- ADGM AI Governance Framework — sovereign admissibility requirements
- MiFID-II (financial AI systems) — explainability and audit trail obligations
- US Executive Order 14110 on Safe AI — accountability documentation requirements

Most organizations deploying AI agents face the same problem: **they cannot prove their AI decisions were governed correctly.** They have logs. They do not have governance receipts.

The gap between "we have logs" and "we have cryptographically signed, invariant-verified, independently auditable governance receipts" is exactly what OMNIX fills. No competitor currently provides PQC-signed governance receipts with formal invariant coverage at this level.

### Legal Positioning

OMNIX Governance API is positioned as:

**RegTech infrastructure software (SaaS)** — NOT:
- Financial advisory service
- Investment management
- Asset management
- Trading signal provider
- Any regulated financial service under FCA, ADGM, DFSA, SEC, or equivalent

This positioning requires:
1. All marketing copy must describe OMNIX as "decision governance infrastructure"
2. No performance claims (no "improves returns", "reduces losses")
3. No trading recommendations in any product tier
4. Clear disclaimers on all product pages
5. Terms of Service explicitly excluding financial advice

---

## Decision

### Product: OMNIX Governance API

**Definition:** A commercially packaged API providing decision governance infrastructure — specifically, the issuance, cryptographic signing, and verification of governance receipts for decisions made by AI systems, human operators, or hybrid pipelines.

**Core deliverable per API call:** A signed governance receipt of one of the following types:
- **DR** (Delegation Receipt) — ATF-INV-001–006
- **TAR** (Temporal Authority Record) — TAR-INV-001
- **RCR** (Runtime Continuity Record) — RGC-INV-001–008
- **SAC** (Semantic Alignment Certificate) — SGIP-INV-001–004
- **PVR** (Proactive Veto Receipt) — AGV-INV-001–006
- **SSR** (Structural Shift Report) — SSD-INV-001–003

Each receipt:
1. Is signed with ML-DSA-65 (Dilithium-3, FIPS 204) at issuance
2. Carries `content_hash` (SHA-256 canonical JSON)
3. Is verifiable offline using `sdk/python/omnix_atf_verify.py` with zero OMNIX runtime dependency
4. Complies with ATORS (ADR-172) — machine-readable, language-agnostic schema
5. Satisfies the invariants of its type

---

## Pricing Tiers

### Tier 0 — VERIFIER (Free / Open)
**Target:** Researchers, auditors, regulators, external validators  
**Access:**
- `sdk/python/omnix_atf_verify.py` — standalone offline verifier
- `sdk/atf_open_receipt_schema.json` — ATORS open schema
- Public ATF documentation and RFC downloads
- Receipt verification via `/atf-verify` UI
**Limitation:** Verify only — no receipt issuance

### Tier 1 — BUILDER ($500/month)
**Target:** Startups, fintech builders, AI developers  
**Access:**
- Up to 1,000 signed governance receipts/month
- DR + TAR receipt types
- API key via B2B provisioning
- Basic audit dashboard access
- ATORS-compliant receipt schema
- Email support (48h SLA)

### Tier 2 — PROFESSIONAL ($2,000/month)
**Target:** Asset managers, trading firms, regulated fintechs  
**Access:**
- Up to 10,000 signed governance receipts/month
- Full ATF stack: DR + TAR + RCR + SAC receipts
- SGIP cross-runtime interoperability (ADR-171)
- Forensic export packages (OEP — ADR-165)
- AGVP proactive veto receipts (ADR-174)
- SSD structural shift reports (ADR-175)
- Audit dashboard + offline verifier support
- Priority support (24h SLA)

### Tier 3 — ENTERPRISE (Custom — from $10,000/month)
**Target:** Banks, sovereign funds, regulatory bodies, institutional AI deployers  
**Access:**
- Unlimited receipt issuance
- Dedicated deployment option (on-premise or private cloud)
- Full ATF + SGIP + DSPP stack
- Custom CRGC (Cross-Runtime Governance Contract) negotiation
- SLA: 99.9% uptime, 4h response
- Compliance documentation package (for regulators)
- Regulatory alignment review (EU AI Act, ADGM, MiFID-II)
- Dedicated governance engineer during onboarding

---

## What OMNIX Governance API Is NOT

This product does NOT:
1. Provide financial advice, investment recommendations, or trading signals
2. Manage, hold, or direct client funds
3. Predict market outcomes
4. Guarantee any operational result
5. Replace legal counsel or compliance officers

This product DOES:
1. Provide cryptographic proof that a governance process was followed
2. Generate auditable receipts that satisfy formal invariant specifications
3. Enable third-party verification of governance decisions without OMNIX runtime access
4. Support regulatory documentation requirements for AI governance (EU AI Act, ADGM AI Framework, etc.)

---

## Technical Integration Points

### REST API
```
POST /api/governance/receipt          # Issue a signed governance receipt
GET  /api/governance/receipt/{id}     # Retrieve a receipt by ID
POST /api/governance/verify           # Verify a receipt (L1–L5)
POST /api/governance/export           # Generate OEP forensic export package
GET  /api/governance/schema           # Retrieve current ATORS schema version
GET  /api/governance/invariants       # List active invariants
```

### Authentication
- API key via `X-OMNIX-API-KEY` header
- Rate limits per tier
- Key provisioning via `provision_b2b_client.py`

### SDKs
- Python SDK: `sdk/python/`
- Node.js SDK: `sdk/nodejs/`
- Standalone verifier: `sdk/python/omnix_atf_verify.py` (zero dependencies)

---

## ADR Invariants Exposed to API Consumers

| Receipt Type | Invariants | ADR |
|---|---|---|
| DR | ATF-INV-001–006 | ADR-156 / RFC-ATF-1 |
| TAR | TAR-INV-001 | ADR-157 / RFC-ATF-2 |
| RCR | RGC-INV-001–008 | ADR-159 / RFC-ATF-2 |
| SAC | SGIP-INV-001–004 | ADR-171 / RFC-ATF-3 |
| PVR | AGV-INV-001–006 | ADR-174 |
| SSR | SSD-INV-001–003 | ADR-175 |

---

## Consequences

### Positive
- Converts existing institutional infrastructure into a direct revenue stream
- Legal positioning as RegTech SaaS requires no financial license in UK or UAE
- Free tier (VERIFIER) creates adoption pipeline for paid tiers
- PQC-first (FIPS 204) is a 3–5 year technical moat — no equivalent currently exists in the market
- ATORS open schema enables ecosystem growth (third parties can build on OMNIX receipts)
- SGIP cross-runtime interoperability (ADR-171) enables partnerships (e.g., VeriSigil AI)

### Constraints
- All product copy must maintain strict financial advice exclusion
- Terms of Service must be reviewed by UK-qualified legal counsel before launch
- Revenue recognition: SaaS subscription model, not transaction-based
- Onboarding documentation required before Tier 2+ launch

### Identifiers
- Product ID: `OMNIX-PRODUCT-GOV-API-001`
- ADR: `ADR-176`
- Product page route: `/governance-api`
