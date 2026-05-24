# ADR-186 — Proof of Governance Public Registry (PoGR)

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-23  
**Supersedes:** —  
**Related:** ADR-176 (Governance API Product) · ADR-184 (OGR) · ADR-185 (OGR Hardening) · ADR-163 (EAP) · ADR-165 (OEP)  
**RFC:** RFC-ATF-1 through RFC-ATF-6  
**Product ID:** OMNIX-POGR-2026-001

---

## Context

### The Verification Gap

OMNIX QUANTUM has built the world's only complete, formally specified, post-quantum decision governance infrastructure for AI agents. The OGR (ADR-184) produces cryptographically sealed session proofs — Behavioral Anchor Records (BAR), Constraint Conformance Signals (CCS), and Cross-Turn Coherence Hash Chains (CTCHC) — all signed with ML-DSA-65 (FIPS 204).

The technical infrastructure is complete. The missing layer is **public trust anchoring**.

Today, an enterprise using OMNIX can prove to its own auditors that its AI agents were governed correctly. What it cannot do is prove this to the external world — regulators, customers, partners, and courts — without granting those parties direct access to its internal systems.

The analogy to Bitcoin is precise:

- Bitcoin did not invent ledgers. Banks had ledgers. What Bitcoin invented was a **public ledger** that anyone can verify without trusting the bank.
- OMNIX did not invent governance logs. Enterprises have logs. What OMNIX has invented is **cryptographically sealed governance receipts**. What it now needs is a **public registry** that anyone can verify without trusting the enterprise.

### The Regulatory Forcing Function

The EU AI Act enters enforcement on **2 August 2026** — 68 days from the date of this ADR. Article 9 mandates risk management systems for high-risk AI. Article 13 mandates transparency. Article 17 mandates quality management documentation.

None of these articles specify *how* that documentation must be produced or verified. OMNIX can define that specification by being first — making the Proof of Governance Registry (PoGR) the de facto standard before any competing definition solidifies.

### Competitive Landscape at ADR-186 Date

| System | What they produce | PoGR equivalent |
|---|---|---|
| CLARIXO | Internal continuity logs | ❌ No public registry |
| VeriSigil | Governance contract specs | ❌ No public registry |
| MTCP | Empirical behavioral scores | ❌ No public registry |
| Enterprise logging (Splunk etc.) | Raw logs | ❌ No cryptographic sealing |
| **OMNIX PoGR** | PQC-sealed, publicly verifiable governance certificates | ✅ **First in market** |

---

## Decision

Introduce the **Proof of Governance Public Registry (PoGR)** — a globally accessible, append-only registry of governance certificates backed by OMNIX OGR session proofs.

### Core Concept

A **PoG Certificate** is a publicly registered artifact that:

1. References a sealed OGR session (`session_id` + `ctchc_seal_hash`)
2. Carries the ML-DSA-65 signature of the OMNIX platform signing key
3. Declares the compliance tier (`ATF-BEV-Compliant`)
4. Is publicly verifiable by anyone using the OMNIX public key — no API key required, no platform account required
5. Has a defined TTL and renewable lifecycle
6. Cannot be deleted — only expired or revoked by the original issuer

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                   OMNIX OGR (existing — ADR-184)                    │
│  session/start → turn(s) → close → proof → compliance report        │
│  CTCHC sealed · BAR × N · CCS × N · ML-DSA-65 signed               │
└──────────────────────────┬──────────────────────────────────────────┘
                           │  POST /v1/pogr/certify
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Proof of Governance Registry (PoGR)                │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  PoG Certificate (PoGC)                                     │   │
│  │  ─────────────────────                                      │   │
│  │  pogc_id:          POGC-{HEX16}                             │   │
│  │  session_id:       OGR-{HEX20}                              │   │
│  │  ctchc_seal_hash:  sha3-256:{...}                           │   │
│  │  issuer:           OMNIX QUANTUM LTD                        │   │
│  │  subject_org:      {enterprise name}                        │   │
│  │  agent_id:         {governed agent identifier}              │   │
│  │  compliance_tier:  ATF-BEV-Compliant                        │   │
│  │  turn_count:       {N}                                      │   │
│  │  avg_conformance:  {0.0–1.0}                                │   │
│  │  issued_at:        {ISO-8601}                               │   │
│  │  expires_at:       {ISO-8601}                               │   │
│  │  regulatory_tags:  [EU-AI-ACT, NIST-AI-RMF, UAE-CRAE]      │   │
│  │  content_hash:     sha3-256:{canonical JSON hash}           │   │
│  │  pqc_signature:    ML-DSA-65:{...}                          │   │
│  │  pqc_algorithm:    ml-dsa-65                                │   │
│  │  status:           ACTIVE | EXPIRED | REVOKED               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│            Append-only ledger (PoGR-INV-002)                       │
│                           │                                         │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   Public lookup     DNS anchor      DOI anchor
   GET /v1/pogr/     TXT record      Zenodo snapshot
   verify/{pogc_id}  (PoGR-INV-005)  (quarterly)
   (zero auth)
```

### API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/v1/pogr/certify` | API Key | Issue a PoG Certificate from a sealed OGR session |
| GET | `/v1/pogr/verify/{pogc_id}` | **None** | Public verification of any certificate |
| GET | `/v1/pogr/certificate/{pogc_id}` | **None** | Full certificate JSON with proof |
| GET | `/v1/pogr/organization/{org_id}` | **None** | All certificates for an organization |
| GET | `/v1/pogr/manifest` | **None** | Registry manifest + platform public key |
| POST | `/v1/pogr/revoke/{pogc_id}` | API Key + PQC proof | Revoke a certificate (issuer only) |
| GET | `/v1/pogr/badge/{pogc_id}.svg` | **None** | Embeddable compliance badge |

### The PoG Badge

Every certificate comes with an embeddable SVG badge:

```
┌──────────────────────────────────┐
│  ⬡ PROOF OF GOVERNANCE           │
│  ATF-BEV-Compliant               │
│  OMNIX QUANTUM · EU AI Act Ready │
│  POGC-A3F2B1C4D5E6F7A8          │
│  Verify: omnixquantum.net/pogr/  │
└──────────────────────────────────┘
```

Enterprises embed this badge on their product pages, in regulatory submissions, and in partner due diligence packets.

### Offline Verification Protocol

A verifier with zero OMNIX access can verify a PoG Certificate using:

```python
import hashlib, json

def verify_pogc(certificate: dict, platform_public_key: bytes) -> bool:
    # Step 1: Recompute content hash
    canonical_fields = {
        "pogc_id": certificate["pogc_id"],
        "session_id": certificate["session_id"],
        "ctchc_seal_hash": certificate["ctchc_seal_hash"],
        "issuer": certificate["issuer"],
        "subject_org": certificate["subject_org"],
        "agent_id": certificate["agent_id"],
        "compliance_tier": certificate["compliance_tier"],
        "issued_at": certificate["issued_at"],
        "expires_at": certificate["expires_at"],
    }
    expected_hash = hashlib.sha3_256(
        json.dumps(canonical_fields, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert expected_hash == certificate["content_hash"], "Content hash mismatch"

    # Step 2: Verify ML-DSA-65 signature
    # (using oqs or dilithium library)
    from oqs import Signature
    verifier = Signature("ML-DSA-65")
    payload = json.dumps(canonical_fields, sort_keys=True, separators=(",", ":")).encode()
    sig = bytes.fromhex(certificate["pqc_signature"].replace("ML-DSA-65:", ""))
    assert verifier.verify(payload, sig, platform_public_key), "PQC signature invalid"

    # Step 3: Check status and expiry
    from datetime import datetime, timezone
    assert certificate["status"] == "ACTIVE", f"Certificate is {certificate['status']}"
    expires = datetime.fromisoformat(certificate["expires_at"])
    assert expires > datetime.now(timezone.utc), "Certificate expired"

    return True
```

The platform public key is obtainable from three independent channels (PoGR-INV-005):
- `GET /api/forensic/platform-key` — live HTTP
- DNS TXT: `_omnix-key.omnixquantum.net`
- Zenodo DOI: permanent archive snapshot

---

## Invariants — PoGR-INV-001–006

### PoGR-INV-001 — Session Proof Backing
Every PoG Certificate MUST reference a sealed, PQC-signed OGR session. A certificate cannot be issued for an unsealed or halted session. Backing proof: `ctchc_seal_hash` must match the sealed session's `chain_seal.seal_hash` on record.

### PoGR-INV-002 — Append-Only Ledger
The PoG Registry is append-only. No certificate entry may be deleted. Entries may transition from `ACTIVE` to `EXPIRED` (by TTL) or `REVOKED` (by issuer with PQC proof), but the entry and its transition history remain permanently in the ledger.

### PoGR-INV-003 — Zero-Trust Verification
The verification of any PoG Certificate (`GET /v1/pogr/verify/{pogc_id}`) requires no API key, no OMNIX account, and no access to the certificate issuer's systems. The certificate is self-contained: content hash, PQC signature, and all canonical fields are embedded.

### PoGR-INV-004 — Explicit TTL and Renewable Lifecycle
Every PoG Certificate MUST carry an `expires_at` field set to no more than 12 months from `issued_at`. Renewal requires a new sealed OGR session — TTL cannot be extended by administrative override without a new proof.

### PoGR-INV-005 — Three-Channel Trust Anchor
The OMNIX platform public key used to verify PoG Certificate signatures MUST be consistently published across three independent channels: HTTP endpoint, DNS TXT record, and Zenodo DOI snapshot. Discrepancy across channels MUST trigger an alert.

### PoGR-INV-006 — Issuer-Only Revocation with PQC Proof
A PoG Certificate may be revoked only by the original issuing organization, and only by presenting a revocation request signed with the same PQC key used at issuance. Administrative revocation without cryptographic proof is not permitted.

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS pogr_certificates (
    pogc_id             TEXT PRIMARY KEY,              -- POGC-{HEX16}
    session_id          TEXT NOT NULL,                 -- OGR-{HEX20}
    ctchc_seal_hash     TEXT NOT NULL,
    issuer              TEXT NOT NULL DEFAULT 'OMNIX QUANTUM LTD',
    subject_org         TEXT NOT NULL,
    subject_org_id      TEXT NOT NULL,                 -- B2B client ID
    agent_id            TEXT NOT NULL,
    compliance_tier     TEXT NOT NULL DEFAULT 'ATF-BEV-Compliant',
    turn_count          INTEGER NOT NULL,
    avg_conformance     REAL NOT NULL,
    issued_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ NOT NULL,
    regulatory_tags     TEXT[] NOT NULL DEFAULT '{}',
    content_hash        TEXT NOT NULL,
    pqc_signature       TEXT NOT NULL,
    pqc_algorithm       TEXT NOT NULL DEFAULT 'ml-dsa-65',
    status              TEXT NOT NULL DEFAULT 'ACTIVE'
                            CHECK (status IN ('ACTIVE', 'EXPIRED', 'REVOKED')),
    revoked_at          TIMESTAMPTZ,
    revocation_reason   TEXT,
    revocation_proof    TEXT,                          -- PQC-signed revocation payload
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pogr_org      ON pogr_certificates (subject_org_id);
CREATE INDEX IF NOT EXISTS idx_pogr_status   ON pogr_certificates (status);
CREATE INDEX IF NOT EXISTS idx_pogr_session  ON pogr_certificates (session_id);
CREATE INDEX IF NOT EXISTS idx_pogr_expires  ON pogr_certificates (expires_at);
```

---

## Product Tiers

### Starter — Free
- 10 PoG Certificates per month
- Public registry listing
- Embeddable badge
- EU AI Act regulatory tag
- Verification API access (unlimited, public)

### Professional — $499/month
- 500 PoG Certificates per month
- Priority registry listing
- Custom regulatory tags (NIST, UAE-CRAE, MiFID-II, SOC2)
- Certificate renewal automation
- Compliance report PDF export
- SLA: 99.9% uptime on verification endpoint

### Enterprise — Custom pricing
- Unlimited certificates
- Private sub-registry (branded domain)
- On-premises deployment option
- Regulatory submission package (formatted for EU AI Act Article 9/13/17)
- Dedicated integration support
- Quarterly Zenodo DOI snapshot of org's certificate ledger
- White-label badge
- Legal team access for due diligence

---

## Regulatory Alignment

| Regulation | Requirement | PoGR Coverage |
|---|---|---|
| EU AI Act Art. 9 | Risk management system for high-risk AI | PoGC documents governance decisions per-session |
| EU AI Act Art. 13 | Transparency and provision of information | Public registry + embeddable badge |
| EU AI Act Art. 17 | Quality management system | Append-only audit trail with PQC integrity |
| NIST AI RMF | Govern · Map · Measure · Manage | CCS conformance score covers Measure; CTCHC covers Manage |
| UAE CRAE | Accountability for AI decisions | Issuer-only revocation with PQC proof |
| MiFID-II | Explainability of algorithmic decisions | BAR per-turn attestation linked to certificate |

---

## Consequences

### Positive
- First publicly verifiable, PQC-anchored governance certificate registry in the world
- Converts the OGR (currently a B2B API) into a public trust infrastructure analogous to a certificate authority for AI governance
- Creates a recurring revenue stream independent of per-API-call pricing
- Positions OMNIX as the definer of the PoG standard before the EU AI Act enforcement window
- Network effect: every enterprise that embeds a PoG badge increases the registry's authority

### Constraints
- PoGR-INV-002 (append-only) means no certificate can be deleted — operational teams must be trained accordingly
- The three-channel trust anchor (PoGR-INV-005) requires DNS management and quarterly Zenodo snapshots as operational overhead
- Certificate renewal requires a new OGR session — organizations must plan agent re-governance cycles

### Implementation Sequence
1. Database schema (this ADR) — deploy via Railway DDL auto-create
2. `/v1/pogr/certify` and `/v1/pogr/verify` endpoints — ADR-187
3. Badge SVG generator — ADR-187
4. Public landing page `/proof-of-governance` — React SPA page
5. DNS TXT record for trust anchor channel 2
6. Quarterly Zenodo snapshot process

---

*ADR-186 · OMNIX QUANTUM LTD · Harold Nunes · May 2026*  
*Proof of Governance Public Registry · OMNIX-POGR-2026-001*
