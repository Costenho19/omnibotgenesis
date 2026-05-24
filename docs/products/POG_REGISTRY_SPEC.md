# Proof of Governance Registry (PoGR) — Product Specification

**Product ID:** OMNIX-POGR-2026-001  
**Version:** 1.0.0  
**Author:** Harold Nunes · OMNIX QUANTUM LTD  
**Date:** May 2026  
**ADR:** [ADR-186](../adr/ADR-186-proof-of-governance-registry.md)  
**Status:** DEFINED — Implementation pending ADR-187

---

## What is the Proof of Governance Registry?

The Proof of Governance Registry (PoGR) is the world's first publicly verifiable, post-quantum-anchored registry of AI governance certificates.

It does for AI governance decisions what a certificate authority does for web security — except it requires no central trust anchor, because every certificate carries its own cryptographic proof.

**One sentence:** An enterprise connects its AI agents to OMNIX, governs every decision through the OGR, and receives a publicly verifiable PoG Certificate that any regulator, customer, or court can verify in seconds — without any access to the enterprise's internal systems.

---

## The Problem It Solves

Every enterprise deploying AI agents today faces the same question from regulators, auditors, and customers:

> *"How do you know your AI made that decision responsibly? Can you prove it?"*

Current answers:
- **"We have logs."** — Logs are internal. Anyone can modify them. Nobody can verify them independently.
- **"We have an AI governance policy."** — A document is not a proof. It describes intent, not execution.
- **"We use [major cloud AI service]."** — Their compliance certifications cover the infrastructure, not the decisions.

The PoGR answers this question with cryptographic finality:

> *"Here is a Proof of Governance Certificate. It references a sealed, tamper-evident session proof signed with post-quantum cryptography. Verify it yourself — right now — with no OMNIX access, no account, no API key."*

---

## How It Works — Four Steps

```
STEP 1 — Govern your agent sessions via OMNIX OGR
──────────────────────────────────────────────────
Your AI agent's outputs pass through the Governance Runtime.
Every turn produces a Behavioral Anchor Record (BAR) signed with ML-DSA-65.
A Cross-Turn Coherence Hash Chain links all turns cryptographically.
The session is sealed with a PQC signature when complete.

STEP 2 — Request a PoG Certificate
────────────────────────────────────
POST /v1/pogr/certify
  { "session_id": "OGR-9B8A7C6D...",
    "subject_org": "Acme Financial AI",
    "regulatory_tags": ["EU-AI-ACT", "MIFID-II"] }

OMNIX verifies the session is sealed, computes the certificate,
signs it with the platform ML-DSA-65 key, and publishes it
to the public registry.

STEP 3 — Receive your PoG Certificate
───────────────────────────────────────
{
  "pogc_id": "POGC-A3F2B1C4D5E6F7A8",
  "compliance_tier": "ATF-BEV-Compliant",
  "avg_conformance": 0.9750,
  "turn_count": 47,
  "regulatory_tags": ["EU-AI-ACT", "MIFID-II"],
  "expires_at": "2027-05-23T00:00:00Z",
  "pqc_signature": "ML-DSA-65:...",
  "verify_url": "https://omnixquantum.net/v1/pogr/verify/POGC-A3F2B1C4D5E6F7A8"
}

STEP 4 — Publish your governance proof
────────────────────────────────────────
Embed the PoG badge on your product page.
Include the POGC-ID in regulatory submissions.
Send verify_url to auditors — they click it, they see the proof.
No OMNIX account required for verification. Zero.
```

---

## The PoG Badge

Every PoG Certificate comes with an embeddable SVG badge enterprises can place on product pages, pitch decks, regulatory submissions, and partner onboarding materials.

```
┌──────────────────────────────────────┐
│  ⬡  PROOF OF GOVERNANCE              │
│     ATF-BEV-Compliant                │
│     OMNIX QUANTUM                    │
│     EU AI Act Ready · May 2026       │
│     POGC-A3F2B1C4D5E6F7A8           │
│     omnixquantum.net/pogr/           │
└──────────────────────────────────────┘
```

The badge links to the public verification URL. Anyone who clicks it sees the full certificate, the compliance tier, the conformance score, and can verify the PQC signature in their browser.

---

## What Makes This Genuinely Different

Nothing like this exists today. This is not a claim — it is a structural observation:

### 1. Post-Quantum Cryptography on Every Certificate
Every PoG Certificate is signed with ML-DSA-65 (Dilithium-3, FIPS 204) — the NIST-standardized post-quantum algorithm. No competitor, incumbent governance tool, or AI compliance framework uses post-quantum cryptography on governance artifacts. When quantum computers break RSA and ECDSA (timeline: 5–15 years), PoG Certificates remain valid. Competitor certificates do not.

### 2. Offline-Verifiable Without OMNIX
The certificate is self-contained. A regulator with no OMNIX account, no API key, and no internet connection to OMNIX can verify the certificate using the published platform public key and a 30-line Python script. This is the core architectural difference from every other "AI governance" tool on the market — they require you to access their platform to verify anything.

### 3. Backed by a Sealed Behavioral Hash Chain
A PoG Certificate is not a badge that says "this organization has a governance policy." It references a sealed Cross-Turn Coherence Hash Chain (CTCHC) that cryptographically links every output of the governed AI session. Any modification to any past turn breaks the chain. The certificate cannot be issued for a session that was not sealed.

### 4. Six Formal Invariants (PoGR-INV-001–006)
The registry operates under six formal invariants that cannot be disabled:
- **PoGR-INV-001** — Every certificate is backed by a sealed OGR session
- **PoGR-INV-002** — The registry is append-only — no certificate can be deleted
- **PoGR-INV-003** — Verification requires zero OMNIX access
- **PoGR-INV-004** — Certificates have explicit TTL; renewal requires new proof
- **PoGR-INV-005** — Platform public key published via three independent channels
- **PoGR-INV-006** — Revocation requires PQC proof from original issuer

### 5. First Mover on the EU AI Act Enforcement Window
The EU AI Act enters enforcement on **2 August 2026**. No standardized proof format for Articles 9, 13, and 17 has been defined by any standards body. The PoGR defines that format first, backed by three published RFCs with permanent DOIs (Zenodo + Figshare) that serve as prior art anchors.

---

## Comparison Table

| | PoGR | SOC 2 | ISO 27001 | AI vendor compliance | Internal logs |
|---|:---:|:---:|:---:|:---:|:---:|
| Per-decision proof | ✅ | ❌ | ❌ | ❌ | ❌ |
| PQC-signed | ✅ | ❌ | ❌ | ❌ | ❌ |
| Offline verifiable | ✅ | ❌ | ❌ | ❌ | ❌ |
| Append-only ledger | ✅ | ❌ | ❌ | ❌ | ❌ |
| Public verification URL | ✅ | ❌ | ❌ | ❌ | ❌ |
| Embeddable badge | ✅ | ✅ | ✅ | partial | ❌ |
| EU AI Act Art. 9/13/17 | ✅ | ❌ | partial | ❌ | ❌ |
| Formal invariants | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## Target Customers

### Primary — EU AI Act Compliance Window (now → Aug 2, 2026)
Any enterprise deploying AI agents in the EU that needs to demonstrate compliance with Article 9 (risk management), Article 13 (transparency), and Article 17 (quality management) for high-risk AI systems.

**Verticals:**
- Financial services (MiFID-II + EU AI Act dual compliance)
- Healthcare AI (GDPR + EU AI Act)
- Legal tech (evidence admissibility)
- Government / public sector (ATO mandates)
- Insurance underwriting (UAE CRAE / DFSA)

### Secondary — Trust Signal for B2B Sales
Any AI startup that sells to enterprise customers and needs a third-party governance proof to answer security questionnaires, procurement requirements, and partner due diligence.

**The ask from their buyers:** "Show me that your AI is governed." The PoGR is the answer.

### Tertiary — Regulatory Arbitrage
Organizations operating across jurisdictions (EU + UAE + UK + US) that need a single governance proof format accepted in multiple regulatory regimes simultaneously.

---

## Product Tiers

### Starter — Free
For teams exploring governance compliance.
- 10 PoG Certificates per month
- Public registry listing
- Embeddable badge (standard)
- EU AI Act regulatory tag
- Public verification API (unlimited reads)
- 12-month certificate TTL

### Professional — $499/month
For teams actively deploying governed AI.
- 500 PoG Certificates per month
- Custom regulatory tags (NIST-AI-RMF, UAE-CRAE, MiFID-II, SOC-2-AI)
- Certificate renewal automation
- Compliance report PDF (formatted for regulatory submission)
- Priority registry listing
- SLA: 99.9% uptime on public verification endpoint
- Email support

### Enterprise — Custom pricing
For regulated industries requiring institutional-grade governance proof.
- Unlimited certificates
- Private sub-registry (branded domain: `governance.yourcompany.com/pogr/`)
- Regulatory submission package (EU AI Act Articles 9/13/17 pre-formatted)
- Quarterly Zenodo DOI snapshot of organization's full certificate ledger
- White-label badge
- On-premises deployment option
- Dedicated integration engineer
- Legal team access for due diligence packages
- Custom invariant set (additional constraints beyond PoGR-INV-001–006)

---

## Integration with Existing OMNIX Products

```
OMNIX Governance API (ADR-176)
    └── OMNIX Governance Runtime / OGR (ADR-184)
            └── Proof of Governance Registry / PoGR (ADR-186)
                    └── Public Verification Portal (/proof-of-governance)
```

The PoGR is not a separate product — it is the **public trust layer** on top of the OGR. Every existing OGR customer can activate PoGR with a single API call after closing a session.

---

## Go-To-Market — EU AI Act Window

**Target date:** First PoG Certificate issued before **1 July 2026** — 32 days before enforcement.

**Sequence:**
1. ADR-187 — API implementation (`/v1/pogr/certify`, `/v1/pogr/verify`, badge generator)
2. React page `/proof-of-governance` — public landing page with live registry browser
3. DNS TXT record — `_omnix-pogr.omnixquantum.net` trust anchor
4. GitHub Pages PoGR section — `/pogr/` on the ATF protocol standard site
5. LinkedIn announcement — position as "the SSL certificate for AI governance"
6. Outreach to Andrea de Jounge / Raheem Larry Babatunde / Marcus O'Dell group as first external validators
7. First paying customer before Aug 2, 2026

---

*OMNIX-POGR-2026-001 · OMNIX QUANTUM LTD · Harold Nunes · May 2026*  
*ADR-186 · RFC-ATF-1 through RFC-ATF-6*
