# OMNIX — Cross-Border Governance Receipt Framework
## Institutional Reference Document

**Classification:** Institutional — Investor, Partner & Regulator Distribution  
**Version:** 1.0.0  
**Date:** 2026-04-14  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**ADR:** ADR-085  

---

## Executive Summary

OMNIX governance receipts provide cryptographic proof that a high-stakes automated
decision was evaluated through a structured, fail-closed 11-checkpoint pipeline before
execution. Every receipt is signed with CRYSTALS-Dilithium (NIST ML-DSA-65), carries a
W3C Verifiable Credential envelope, and resolves at a public DID document
(`did:web:omnixquantum.net`).

This document addresses a question raised by institutional reviewers:

> "W3C VCs ensure verifiable structure — not semantic equivalence across jurisdictions.
> Independent verifiers can validate the same receipt and arrive at different regulatory
> conclusions."

This is correct. OMNIX does not claim to solve cross-border regulatory equivalence.
No system can guarantee that a regulator in Singapore will interpret a governance receipt
the same way as a regulator in Dubai or London.

What OMNIX does instead is more rigorous: it **maps every receipt explicitly to 10
regulatory frameworks across 6 regions**, **states the exact boundary of what the
cryptographic evidence proves**, and **gives every verifier a concordance map** showing
where frameworks agree and where additional local assessment is needed.

A receipt that lies about its scope is dangerous. A receipt that defines its scope
precisely — and is honest about what it does not claim — is institutional-grade evidence.

---

## 1. The Three-Layer Governance Evidence Model

### 1.1 Layer 1 — Cryptographic Proof (what no jurisdiction can dispute)

Every OMNIX receipt provides these facts with cryptographic certainty:

| Fact | Mechanism | Independent Verifiable |
|------|-----------|----------------------|
| Decision was evaluated at stated timestamp | UTC timestamp embedded in signed payload | ✅ Yes |
| Veto chain result (N checkpoints passed/blocked) is authentic | SHA-256 content hash bound to Dilithium-3 signature | ✅ Yes |
| Receipt was not modified after signing | Signature invalidated by any byte change | ✅ Yes |
| Issuer controlled the signing key at time of issuance | `did:web:omnixquantum.net` — public DID document | ✅ Yes |
| Checkpoints were applied in the stated sequence | Veto chain array in signed payload | ✅ Yes |
| Receipt ID is unique and non-colliding | UUID4-derived 12-hex suffix | ✅ Yes |

**Verification endpoints (public, no authentication):**
- `GET https://omnixquantum.net/api/trust/verify` — hash + signature verification
- `GET https://omnixquantum.net/api/trust/registry` — current public key + algorithm
- `GET https://omnixquantum.net/.well-known/did.json` — W3C DID Document

### 1.2 Layer 2 — Regulatory Mapping (10 frameworks, 6 regions)

Every receipt maps the governance outcome to 10 regulatory frameworks simultaneously.
A verifier in any target jurisdiction finds their applicable framework inside the receipt
without requiring knowledge of OMNIX internal logic.

| # | Framework | Jurisdiction | Region | Key Reference |
|---|-----------|-------------|--------|--------------|
| 1 | EU Artificial Intelligence Act | European Union | Europe | Regulation (EU) 2024/1689 — Art. 9, 13, 14 |
| 2 | EU GDPR | European Union | Europe | Regulation (EU) 2016/679 — Art. 22 |
| 3 | DORA | EU Financial Sector | Europe | Regulation (EU) 2022/2554 — Art. 6, 8, 13 |
| 4 | FATF Recommendations | G7 + 37 members | Global | R.10, R.16, R.20, R.29 (2023 update) |
| 5 | UK FCA / SM&CR / COBS | United Kingdom | UK | FCA COBS 11.2 · SYSC 9.1 · SM&CR 2016 |
| 6 | US SEC Rule 15c3-5 + Reg SCI | United States | North America | 17 CFR §240.15c3-5 · 17 CFR §242.1000 |
| 7 | MAS FEAT Principles | Singapore | Asia-Pacific | MAS AI Governance Framework v2 (2020) |
| 8 | UAE CBUAE AI Framework | United Arab Emirates | Middle East | CBUAE AI Governance Framework (2024) |
| 9 | SAMA Responsible AI | Kingdom of Saudi Arabia | Middle East | SAMA Principles for Responsible AI (2023) |
| 10 | FSB G20 AI/ML Guidance | G20 International | Global | FSB Report AI/ML Financial Services (2023) |

### 1.3 Layer 3 — Proof Scope (explicit boundary declaration)

Every receipt contains a `proof_scope` block that states, in plain language, exactly
what the cryptographic evidence certifies and what it does not:

**What this receipt proves:**
- The decision was evaluated by OMNIX governance checkpoints at the stated timestamp.
- The veto chain result is cryptographically bound to this receipt.
- The receipt has not been altered since signing.
- The issuer controlled the signing key at time of issuance.
- Each regulatory framework mapping reflects OMNIX's interpretation at time of issuance.

**What this receipt does NOT claim:**
- Authoritative regulatory approval from any named jurisdiction or supervisory body.
- Semantic equivalence between framework interpretations.
- That OMNIX's checkpoint logic satisfies every local implementation rule.
- Guaranteed cross-border enforceability.

This is deliberate transparency, not a limitation. A receipt that overstates its scope
creates legal risk for all parties. A receipt with defined boundaries is institutional-grade evidence.

---

## 2. Framework-by-Framework Coverage

### 2.1 European Union — EU AI Act (Regulation 2024/1689)

**Why it applies:** OMNIX operates as a High-Risk AI System under Annex III —
Financial Services. All 11 governance checkpoints satisfy Art. 9 risk management
requirements. The signed veto chain satisfies Art. 13 (transparency) and Art. 12
(record-keeping for technical documentation).

| Decision Outcome | EU AI Act Interpretation |
|-----------------|--------------------------|
| **APPROVED** | Satisfies Art. 9 risk management. All applicable high-risk AI governance checkpoints passed. Compliant with Annex III. Art. 13 transparency obligation met via signed veto chain. |
| **BLOCKED** | Art. 14 (Human Oversight) satisfied — governance pipeline prevented a non-compliant outcome before execution. Logging obligations met. |
| **HOLD** | Art. 9(2) iterative risk assessment ongoing. Human reviewer notified. Decision not executed. |

**Local assessment note:** OMNIX provides the technical documentation and audit trail required
under Art. 11 and Art. 12. Conformity assessment (Art. 43) remains the deploying entity's
obligation for notified body certification.

---

### 2.2 European Union — GDPR (Regulation 2016/679, Article 22)

**Why it applies:** Automated decision-making systems are regulated under Art. 22 when
decisions produce legal or similarly significant effects on individuals.

| Decision Outcome | GDPR Interpretation |
|-----------------|---------------------|
| **APPROVED** | Satisfies GDPR Art. 22 requirements. OMNIX governance pipeline constitutes meaningful oversight — decision is not solely automated. Audit trail available per Art. 5(2) (accountability principle). |
| **BLOCKED** | Art. 22 right protected — no adverse outcome reached the data subject. Governance record demonstrates the system prevented the automated decision from executing. |
| **HOLD** | Data subject rights preserved. Manual review initiated before any profiling-based outcome. |

**Local assessment note:** Data subjects' rights under Art. 22(3) (human intervention,
expression of point of view, contest the decision) remain the deploying entity's obligation
to implement alongside the OMNIX governance layer.

---

### 2.3 European Union — DORA (Regulation 2022/2554)

**Why it applies:** Digitally operated decision systems in EU financial services are
subject to DORA ICT risk management requirements (Art. 6) and incident classification.

| Decision Outcome | DORA Interpretation |
|-----------------|---------------------|
| **APPROVED** | Passed DORA Art. 6 ICT Risk Management requirements. Stress testing (CP-6) and threshold validation (CP-8) confirm operational resilience. ICT incident classification: none triggered. |
| **BLOCKED** | ICT risk threshold breach detected. Decision blocked per Art. 8 risk identification obligations. Incident classification logged. Art. 19 notification obligations assessed. |
| **HOLD** | Operational parameters outside ICT boundaries. Art. 13 security policy review required before proceeding. |

---

### 2.4 FATF — Financial Action Task Force (Recommendations 10, 16, 20, 29)

**Why it applies:** AML screening (CP-9) is a mandatory checkpoint in the OMNIX pipeline.
FATF recommendations apply to all financial institutions in 40+ member jurisdictions.

| Decision Outcome | FATF Interpretation |
|-----------------|---------------------|
| **APPROVED** | AML screening (CP-9) passed. Transaction pattern consistent with FATF R.10 Customer Due Diligence. No structuring, layering, or high-risk counterparty signals detected. Travel Rule (R.16) compliance check included where applicable. |
| **BLOCKED** | AML gate triggered BLOCK. Decision suppressed per FATF R.29 (Financial Intelligence obligations). Suspicious Transaction Report (STR) obligation reviewed. Audit record preserved for competent authority. |
| **HOLD** | AML screening inconclusive. Enhanced Due Diligence (FATF R.10 EDD) recommended. Transaction held pending manual verification. |

**Local assessment note:** STR filing obligations remain with the reporting entity under
local AML legislation (e.g., POCA 2002 in UK, AMLD6 in EU). OMNIX provides the audit
trail; the filing decision is a human compliance officer determination.

---

### 2.5 United Kingdom — FCA / SM&CR / COBS

**Why it applies:** FCA-regulated firms using automated decision systems must satisfy
COBS 11.2 (best execution), SYSC 9.1 (record-keeping), and SM&CR accountability
requirements. The UK AI Strategy and FCA's AI Discussion Paper (DP5/22) signal increasing
scrutiny of AI governance in financial services.

| Decision Outcome | UK FCA Interpretation |
|-----------------|----------------------|
| **APPROVED** | Satisfies FCA COBS 11.2 best execution obligations. OMNIX veto chain provides the audit trail required under SYSC 9.1. SM&CR accountability preserved — checkpoint evidence available per request. FCA Principle 6 (Customers' Interests) evidenced. |
| **BLOCKED** | Decision suppressed per FCA Principle 6 and COBS 2.1.1 (fair, clear, not misleading). SM&CR senior manager accountability: blocked-decision receipt retained for firm records. |
| **HOLD** | FCA Principle 2 (Skill, Care, Diligence) applies — manual review required. Decision not executed until confirmed. |

**Local assessment note:** SM&CR individual accountability mapping (which Senior Manager
is accountable for AI governance decisions) is a firm-level obligation OMNIX does not
determine. OMNIX provides the evidence; the accountability mapping is the firm's responsibility.

---

### 2.6 United States — SEC Rule 15c3-5 + Regulation SCI

**Why it applies:** Broker-dealers using automated order systems must comply with SEC
Rule 15c3-5 (Market Access Rule) pre-trade risk controls. Reg SCI applies to systems
critical to market infrastructure integrity.

| Decision Outcome | US SEC Interpretation |
|-----------------|----------------------|
| **APPROVED** | Passed pre-trade risk controls consistent with SEC Rule 15c3-5(c)(1). Risk evaluation (CP-3), threshold checks (CP-8), and coherence gate (CP-4) satisfy erroneous-order prevention obligations. Reg SCI systems integrity confirmed via stress test (CP-6). |
| **BLOCKED** | Order blocked by pre-trade controls per Rule 15c3-5(c)(1). Order was not transmitted to market — regulatory block recorded. Reg SCI incident assessment initiated. |
| **HOLD** | Held for supervisory review per FINRA Rule 3110 supervision obligations. No market access until review completes. |

**Local assessment note:** Reg SCI incident reporting obligations (if triggered) remain with
the SCI entity. OMNIX provides the governance record; SEC notification is a firm obligation.

---

### 2.7 Singapore — MAS FEAT Principles

**Why it applies:** MAS expects financial institutions using AI/ML in decision-making to
satisfy FEAT principles: Fairness, Ethics, Accountability, Transparency. The OMNIX veto
chain satisfies the explainability requirement per FEAT §3.4.

| Decision Outcome | MAS Interpretation |
|-----------------|-------------------|
| **APPROVED** | Satisfies MAS FEAT Principle — Fairness, Ethics, Accountability, Transparency. OMNIX veto chain fulfils Explainability requirement per FEAT §3.4. Audit trail meets MAS Notice FAA-N16 record-retention standards. |
| **BLOCKED** | MAS FEAT Accountability principle satisfied — system prevented an outcome that failed internal governance thresholds. Governance record retained per MAS Notice SFA 04-N02. |
| **HOLD** | MAS FEAT Transparency: human reviewer notified with full checkpoint trace before any outcome is issued. |

---

### 2.8 United Arab Emirates — CBUAE AI Governance Framework

**Why it applies:** The UAE is a primary target market for OMNIX. The CBUAE AI
Governance Framework (2024) sets explainability, transparency, and risk management
requirements for AI in financial services. The UAE AI Strategy 2031 mandates governance
for AI operating in regulated sectors. Where domain is Islamic Finance, Sharia parameter
screening (CP-7 Ethics & Domain Gate) applies.

| Decision Outcome | UAE CBUAE Interpretation |
|-----------------|--------------------------|
| **APPROVED** | Compliant with CBUAE AI Governance Framework (2024). Explainability requirement met — veto chain provides full audit trail per Art. 3.2 (Transparency). Sharia parameter screening included where domain is Islamic Finance. |
| **BLOCKED** | Blocked in compliance with CBUAE Art. 4.1 (Risk Management). Automated suppression recorded. Governance receipt retained for CBUAE supervisory review. |
| **HOLD** | CBUAE Art. 5 (Human Oversight) protocol active. No automated outcome issued pending manual confirmation. |

**Language note:** OMNIX uses the term "Sharia parameter screening" (not "Sharia compliance").
Compliance determination remains with the relevant Islamic finance scholar or Sharia board.

---

### 2.9 Kingdom of Saudi Arabia — SAMA Responsible AI Framework

**Why it applies:** SAMA's Principles for Responsible AI in Finance (2023) align with
Vision 2030's mandate for responsible technology in the financial sector. Principle 3
(Accountability) and Principle 5 (Transparency) are directly satisfied by OMNIX receipts.

| Decision Outcome | SAMA Interpretation |
|-----------------|---------------------|
| **APPROVED** | Consistent with SAMA Responsible AI Principle 3 (Accountability) and Principle 5 (Transparency). Governance checkpoint evidence satisfies SAMA's auditability requirement. Sharia compliance gate (CP-7) active for Islamic finance domain decisions. |
| **BLOCKED** | SAMA Principle 2 (Safety) satisfied — automated suppression prevented a potentially non-compliant financial outcome. Signed receipt retained per SAMA record-keeping obligations. |
| **HOLD** | SAMA Principle 3 (Human Accountability) — manual review required. Checkpoint trace available for SAMA examination. |

---

### 2.10 G20 / FSB — Financial Stability Board AI/ML Guidance

**Why it applies:** The FSB's 2017 report (updated 2023) on AI and Machine Learning in
Financial Services sets expectations for accountability, explainability, and operational
risk management for AI systems in G20 member jurisdictions.

| Decision Outcome | FSB Interpretation |
|-----------------|-------------------|
| **APPROVED** | Satisfies FSB accountability and explainability recommendations. Third-party verifiability requirement met — receipt hash and signature independently verifiable. Model risk management (CP-3 + CP-6) consistent with FSB guidance §3.2. |
| **BLOCKED** | Consistent with FSB guidance on fail-safe mechanisms (§4.1 — operational risk). Signed receipt provides the accountability trail FSB recommends for suppressed AI outputs. |
| **HOLD** | Consistent with FSB recommendation on human oversight of high-impact automated financial decisions (§3.4). |

---

## 3. Cross-Jurisdiction Concordance Model

### 3.1 How frameworks align on an APPROVED outcome

All 10 mapped frameworks interpret an APPROVED governance receipt as evidence that:
- The AI decision system applied a structured risk management process.
- The decision passed all applicable governance checkpoints before execution.
- An audit trail exists linking the decision to the governance state that produced it.

**Where frameworks diverge on APPROVED:**
- EU AI Act requires conformity assessment certification separately (Art. 43).
- UK SM&CR requires a named Senior Manager accountable for the AI system.
- US Reg SCI may require additional systems integrity reporting.
- FATF may require Travel Rule compliance documentation separately (R.16).

These are additive obligations on the deploying entity — they do not challenge the
validity of the governance receipt. They require the deploying entity to satisfy
additional local obligations alongside using OMNIX.

### 3.2 How frameworks align on a BLOCKED outcome

All 10 frameworks interpret a BLOCKED governance receipt as a governance safeguard:
- The AI system prevented an outcome that failed governance thresholds.
- No adverse automated decision reached execution or the end party.
- An audit trail of the block reason is available for regulatory review.

**Where frameworks diverge on BLOCKED:**
- FATF may trigger STR reporting obligations (if AML gate blocked the decision).
- UK FCA SYSC 9.1 requires the blocked-decision record to be retained for regulatory review.
- US SEC Rule 15c3-5 may classify a blocked order as a Reg SCI incident requiring reporting.

These are reporting obligations — not challenges to the receipt's validity. A BLOCKED
receipt is always positive evidence of governance function, regardless of jurisdiction.

### 3.3 Divergence risk summary

| Dimension | Divergence Risk | Notes |
|-----------|-----------------|-------|
| Cryptographic validity | **None** | All verifiers reach identical conclusions on hash + signature |
| Receipt authenticity | **None** | DID document and public key endpoint are independently verifiable |
| Regulatory interpretation | **Low–Medium** | All frameworks agree on the governance function; differ on additional local obligations |
| Compliance certification | **Not applicable** | OMNIX provides governance evidence; compliance certification is the deploying entity's obligation |

---

## 4. What OMNIX Cannot and Does Not Claim

This section is provided explicitly to prevent misinterpretation of OMNIX receipts
in regulatory, legal, or commercial contexts.

| Non-claim | Explanation |
|-----------|-------------|
| **Authoritative regulatory approval** | No private governance system can grant regulatory approval. That authority rests with the relevant supervisory body (FCA, SEC, CBUAE, MAS, etc.). |
| **Cross-border semantic equivalence** | The same receipt may be interpreted differently by regulators in different jurisdictions. OMNIX maps its interpretation; authoritative determination is local. |
| **Compliance certificate** | A governance receipt is evidence of process, not a compliance certificate. Compliance certifications are issued by accredited conformity assessment bodies or regulators. |
| **Full local implementation coverage** | OMNIX's 11 checkpoints are designed to satisfy the governance requirements common across frameworks. Local implementation rules (e.g., specific reporting formats, filing deadlines, prescribed human review procedures) may impose additional obligations. |
| **Legal advice** | This document and OMNIX receipts do not constitute legal advice. Deploying entities should obtain legal counsel for jurisdiction-specific compliance determinations. |

---

## 5. Independent Verification Protocol

Any party holding an OMNIX governance receipt can independently verify it without
contacting OMNIX. The following sequence requires no OMNIX involvement:

### Step 1 — Verify the receipt hash

```bash
# Canonicalise the receipt payload (sort keys, no whitespace)
echo -n '{...canonical receipt payload...}' | sha256sum
# Compare with receipt.content_hash
```

### Step 2 — Obtain the public key

```bash
curl https://omnixquantum.net/api/trust/registry
# Returns: public_key_b64, algorithm (ML-DSA-65), key_id
```

### Step 3 — Verify the signature

```python
import base64
from pqc.sign import dilithium3  # or equivalent ML-DSA-65 library

pub_key = base64.b64decode(receipt["public_key_b64"])
signature = base64.b64decode(receipt["signature_b64"])
payload = receipt["content_hash"].encode()

valid = dilithium3.verify(signature, payload, pub_key)
# True = receipt is authentic and unmodified
```

### Step 4 — Resolve the DID

```bash
curl https://omnixquantum.net/.well-known/did.json
# Returns: W3C DID Document with verification method and public key
```

### Step 5 — Apply your jurisdiction's framework

Using the `regulatory_interpretation` block in the receipt, locate the entry for your
jurisdiction and apply the interpretation to your local compliance assessment.

---

## 6. Architecture Integration Points

| Component | Purpose |
|-----------|---------|
| `omnix_web/api/omnix_engine/receipt_to_vc.py` | `build_jurisdiction_semantics()` — 10-framework mapping, proof_scope, concordance |
| `omnix_web/api/omnix_engine/federated_trust.py` | Trust registry, independent verify endpoint, trust score |
| `omnix_web/api/gov_blueprint.py` | B2B governance API — `_load_engine()` direct import (key-consistent) |
| `omnix_core/evidence/decision_receipt.py` | Module-level stable keys — shared keypair across all instances |
| `omnix_core/evidence/verification_server.py` | Public verification web server — `GET /health`, `GET /`, `GET /api/verify/{id}` |
| `src/omnix/bootstrap/main_entry.py` | Bot service entrypoint — `$PORT`-aware verification server startup |
| `omnix_web/public/.well-known/did.json` | W3C DID Document — `did:web:omnixquantum.net` |

---

## 7. Approved Institutional Statement (ADR-085)

The following statement is approved for use in investor materials, partner briefings,
and regulatory submissions:

> "OMNIX governance receipts provide cryptographic proof — via NIST-standardised
> CRYSTALS-Dilithium (ML-DSA-65) — that a high-stakes automated decision was evaluated
> through a structured, fail-closed 11-checkpoint pipeline before execution. Each receipt
> maps the governance outcome to 10 regulatory frameworks across 6 regions (EU AI Act,
> GDPR, DORA, FATF, UK FCA/SM&CR, US SEC Rule 15c3-5, MAS FEAT, UAE CBUAE, SAMA, FSB
> G20), with explicit citations to the applicable article or recommendation in each
> framework.
>
> OMNIX receipts state explicitly what they prove (cryptographic integrity, governance
> process, veto chain authenticity) and what they do not claim (authoritative regulatory
> approval, cross-border semantic equivalence, compliance certification). This design
> principle — maximum coverage with transparent boundaries — makes OMNIX receipts
> institutional-grade governance evidence: honest about scope, thorough in coverage,
> independently verifiable without OMNIX infrastructure."

---

## 8. Regulatory Contact Points by Jurisdiction

| Jurisdiction | Primary Regulator | AI/Governance Framework |
|-------------|------------------|------------------------|
| European Union | ESMA / National Competent Authorities | EU AI Act — EUCA (European AI Office) |
| United Kingdom | FCA | FCA AI Discussion Paper DP5/22 |
| United States | SEC / FINRA | SEC Rule 15c3-5, Reg SCI |
| UAE | CBUAE | CBUAE AI Governance Framework 2024 |
| Saudi Arabia | SAMA | SAMA Responsible AI Principles 2023 |
| Singapore | MAS | MAS FEAT Principles v2 2020 |
| Global (AML) | FATF Secretariat | FATF Recommendations 2023 |
| Global (FSB) | FSB Secretariat | FSB AI/ML Report 2023 |

---

*OMNIX QUANTUM LTD — Decision Governance Infrastructure*  
*71-75 Shelton Street, Covent Garden, London, WC2H 9JQ*  
*Harold Nunes | Founder | omnixquantum.net*  
*Classification: Institutional — Investor, Partner & Regulator Distribution*
