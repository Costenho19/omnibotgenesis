# CCI × ATF Integration Mapping
**Cryptographic Certificates of Intent — OMNIX Agent Trust Fabric**  
**Prepared by:** Harold Nunes — OMNIX QUANTUM LTD  
**Counterpart:** Brent Heckerman — Cryptographic Certificates of Intent  
**Classification:** Confidential — Integration Working Session  
**Date:** May 2026  
**Reference:** CISA/NSA/Five Eyes — "Careful Adoption of Agentic AI Services" (1 May 2026)

---

## 1. Purpose

This document maps the Cryptographic Certificates of Intent (CCI) stack against the OMNIX Agent Trust Fabric (ATF) protocol stack to identify the exact integration points that produce a complete, end-to-end governance chain satisfying the joint CISA/NSA/Five Eyes guidance.

Neither stack alone satisfies the full guidance. Together they do.

---

## 2. What Each Stack Covers

### CCI Stack (Brent)

| Component | Function | Timing |
|---|---|---|
| Certificate of Intent (CoI) | Agent declares what it is about to do | Pre-execution |
| Short-lived JWT (5-min TTL) | Time-bounded commitment window | Pre-execution |
| Fail-closed gate | Execution blocked until CoI issued | Pre-execution |
| On-chain anchor | Immutable record of declared intent | Pre-execution |
| Human-in-the-loop pattern | Multi-level authority for high-impact actions | Pre-execution |

**CCI coverage:** The commitment layer — what was declared, by whom, and when.

---

### ATF Stack (OMNIX)

| Component | RFC | Function | Timing |
|---|---|---|---|
| Agent Identity Record (AIR) | RFC-ATF-1 | Cryptographic identity — who the agent is, anchored to a human principal | Pre-admission |
| Delegation Receipt (DR) | RFC-ATF-1 | What the agent was authorized to do, signed ML-DSA-65 | Pre-admission |
| Temporal Authority Record (TAR) | RFC-ATF-1 | Time-bounded authority scope | Pre-admission |
| Runtime Continuity Record (RCR) | RFC-ATF-2 | Continuous authority health throughout execution | During execution |
| Authority Fragmentation Guard (AFG) | RFC-ATF-2 | Prevents authority budget fragmentation across sub-agents | During execution |
| Reauthorization Challenge (RC) | RFC-ATF-2 | Formal halt-or-reauthorize at CRITICAL threshold | During execution |
| Governance Policy Interoperability Layer (GPIL) | RFC-ATF-3 | Cross-domain governance contract — the formal integration mechanism | Cross-domain |
| Evidence Lifecycle Pipeline (ELP) | RFC-ATF-3 | HOT/WARM/COLD evidence classification and retention | Post-execution |
| OMNIX Evidence Package (OEP) | RFC-ATF-3 | Self-contained forensic deliverable, sealed and verifiable offline | Post-execution |
| Proactive Veto Receipt (PVR) | RFC-ATF-4 | Signed veto emitted **before any request arrives** | Pre-execution |
| Structural Shift Detector (SSD) | RFC-ATF-4 | Detects when recalibration is safe vs. unsafe | Continuous |
| Dynamic Semantic Portability Protocol (DSPP) | RFC-ATF-4 | Retroactive semantic assessment — receipt meaning is portable across domains and time | Post-execution |
| Proof of Governance Certificate (PoGC) | ADR-186 | Final trust artifact — PQC-signed, offline verifiable, append-only | Post-session |

**ATF coverage:** The authority layer — who was authorized, what was the scope, did it remain valid, and is the evidence portable across domains and time.

---

## 3. The Gap CISA/NSA/Five Eyes Identified

The joint guidance (1 May 2026) identifies six requirements for agentic AI adoption:

| Requirement | CCI | ATF | Together |
|---|---|---|---|
| Cryptographically verified agent identity anchored per-agent | — | RFC-ATF-1 AIR | ✓ |
| Short-lived credentials | JWT 5-min CoI | TAR (time-bounded) | ✓ |
| Pre-execution application — throttle point at commitment time | CoI + fail-closed gate | PVR (RFC-ATF-4) | ✓ |
| Continuous runtime authentication | — | RFC-ATF-2 RCR | ✓ |
| Human-in-the-loop for high-impact actions | Multi-level authority pattern | AMG Approval Gate + RC | ✓ |
| Accountability — offline-verifiable audit trail | On-chain anchor | PoGC + OEP (RFC-ATF-3) | ✓ |

**Neither stack alone covers all six. Both stacks together cover all six with no gaps.**

---

## 4. Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRE-EXECUTION LAYER                          │
│                                                                 │
│  ATF: AIR + DR + TAR                                           │
│  (who is this agent, what can it do, for how long)             │
│         │                                                       │
│         ▼                                                       │
│  CCI: Certificate of Intent issued                             │
│  (agent declares: "I am about to do X")                        │
│  JWT 5-min TTL · Fail-closed gate · On-chain anchor            │
│         │                                                       │
│  ATF: PVR (RFC-ATF-4)                                          │
│  (OMNIX emits proactive veto receipt — signed before request)  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    EXECUTION LAYER                               │
│                                                                 │
│  ATF: RCR chain (RFC-ATF-2)                                    │
│  (continuous authority health — CES score at every interval)   │
│         │                                                       │
│  ATF: AFG — no sub-agent exceeds delegated budget              │
│         │                                                       │
│  ATF: RC — HALT or reauthorize at CRITICAL threshold           │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    POST-EXECUTION LAYER                          │
│                                                                 │
│  ATF: Evidence classified HOT → WARM → COLD (RFC-ATF-3 ELP)   │
│         │                                                       │
│  CCI on-chain anchor + ATF OEP = complete forensic package     │
│  (sealed, self-contained, verifiable without platform access)  │
│         │                                                       │
│  ATF: DSPP RSA — receipt semantics portable across domains     │
│  (regulator in any jurisdiction can verify without bilateral    │
│   negotiation with OMNIX or CCI)                               │
│         │                                                       │
│  ATF: PoGC issued                                              │
│  (Proof of Governance Certificate — ML-DSA-65 signed,         │
│   public verifier: omnixquantum.net/pogr/verify/{id})         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. The Formal Integration Point — GPIL (RFC-ATF-3)

The Governance Policy Interoperability Layer is the mechanism that makes CCI × ATF a formally defined integration rather than an informal partnership.

GPIL defines three levels of interoperability:

| Level | What it covers | CCI × ATF application |
|---|---|---|
| L1 — Cryptographic | Both systems use the same signing primitives | CCI anchors intent hash in ATF delegation chain using ML-DSA-65 |
| L2 — Protocol | Both systems speak the same receipt format | CCI CoI ID included as `external_commitment_ref` in ATF DR |
| L3 — Governance Policy | Both systems agree on what the receipt means across domains | CRGC defines how CCI intent maps to ATF authority scope |

The formal artifact that governs this is the **Cross-Runtime Governance Contract (CRGC)** — a signed bilateral agreement between the CCI runtime and the ATF runtime that defines which CCI intent classes map to which ATF authority scopes.

**This is what the "mapping session" produces:** a CRGC that can be referenced in any integrated deployment.

---

## 6. The PVR Intersection (RFC-ATF-4 — Note for Session)

The Proactive Veto Receipt (PVR) is the ATF artifact that operates in the same temporal space as the CCI Certificate of Intent.

| | CCI Certificate of Intent | ATF Proactive Veto Receipt (PVR) |
|---|---|---|
| **Timing** | Before agent acts | Before request arrives |
| **Issuer** | Agent (self-declaring) | OMNIX governance engine |
| **Content** | "I intend to do X" | "If X is requested, the veto condition is Y" |
| **TTL** | 5 minutes | Configurable (default: 30 min) |
| **Anchor** | On-chain | PostgreSQL + PQC signature |
| **Purpose** | Commitment | Pre-emptive governance boundary |

These are complementary, not overlapping. The CoI says what the agent will do. The PVR says what OMNIX has pre-authorized (or pre-vetoed). When both exist for the same action, the regulator has the complete picture at the moment of commitment — not reconstructed after the fact.

---

## 7. Integration API Reference

### ATF Endpoints (OMNIX)

```
POST /v1/atf/delegate
  → Returns: Delegation Receipt (DR) with DR-ID for CoI reference

GET  /v1/atf/verify/{dr_id}
  → Offline-verifiable delegation chain

POST /v1/atf/rcr
  → Emit Runtime Continuity Record during execution

GET  /v1/atf/rcr/{session_id}/chain
  → Full continuity chain for a session

POST /v1/pogr/certify
  → Issue Proof of Governance Certificate at session close
  → Returns: { pogc_id, public_page: "/pogr/verify/{id}", verify_url }

GET  /v1/pogr/verify/{pogc_id}
  → Zero-auth public verification (PoGR-INV-003)
  → Public page: https://omnixquantum.net/pogr/verify/{pogc_id}

POST /v1/atf/export
  → Generate OMNIX Evidence Package (OEP) — sealed forensic deliverable
```

### Integration Flow (CCI → ATF)

```
Step 1: CCI registers agent with ATF
  POST /v1/atf/delegate
  Body: { agent_id, principal_id, authority_scope, max_budget }
  → Receives: { dr_id, tar_id, air_id }

Step 2: CCI issues CoI, includes ATF reference
  CoI.authority_anchor = { dr_id, tar_id, omnix_verify_url }
  → CoI is now anchored to the ATF delegation chain

Step 3: During execution, CCI notifies ATF at key events
  POST /v1/atf/rcr
  Body: { session_id, dr_id, ces_contribution: { ... } }

Step 4: Session closes — both artifacts sealed
  ATF: POST /v1/pogr/certify → PoGC issued
  CCI: On-chain anchor finalized
  Combined: OEP includes both CCI CoI hash + ATF PoGC as trust anchors

Step 5: Regulator verifies
  https://omnixquantum.net/pogr/verify/{pogc_id}
  → Full chain: intent declared (CCI) → authority verified (ATF) → evidence sealed
```

---

## 8. Evidence Package Composition

When both stacks are integrated, the forensic deliverable (OEP) contains:

```json
{
  "oep_id": "OEP-{hex}",
  "sealed_at": "ISO-8601",
  "trust_anchors": {
    "cci": {
      "certificate_of_intent_id": "CoI-{id}",
      "intent_hash": "SHA3-256:{hex}",
      "onchain_anchor": "{chain}:{tx_hash}",
      "commitment_window_ms": 300000
    },
    "atf": {
      "pogc_id": "POGC-{hex}",
      "delegation_receipt_id": "DR-{id}",
      "air_id": "AIR-{id}",
      "continuity_chain_complete": true,
      "ces_score_terminal": 0.94,
      "pqc_algorithm": "ML-DSA-65 (FIPS 204)",
      "verify_url": "https://omnixquantum.net/pogr/verify/{pogc_id}"
    }
  },
  "regulatory_coverage": ["EU-AI-ACT", "CISA-AGENTIC-AI-2026", "NSA-FIVE-EYES"],
  "offline_verifiable": true
}
```

---

## 9. What the Session Needs to Produce

At the end of the mapping session, the output should be:

1. **A Cross-Runtime Governance Contract (CRGC)** — the signed bilateral document (per RFC-ATF-3 §GPIL) that defines the formal integration terms between CCI and ATF.

2. **An integration schema** — the agreed JSON structure for how CCI CoI references are embedded in ATF DRs and vice versa.

3. **A joint regulatory reference** — a one-page document for regulators that explains the chain: CoI (intent) → ATF DR (authority) → PVR (pre-vetted) → RCR (runtime) → PoGC (evidence) — all as a single governance chain.

4. **A test trace** — one live governance session running both stacks end-to-end, producing a PoGC that includes the CCI anchor.

---

## 10. Regulatory Alignment Summary

This integration directly maps to the CISA/NSA/Five Eyes guidance (1 May 2026, "Careful Adoption of Agentic AI Services"):

| Guidance Requirement | Covered By |
|---|---|
| Verify agent identity cryptographically | ATF AIR + DR (RFC-ATF-1) |
| Use short-lived credentials | CCI JWT 5-min + ATF TAR |
| Apply pre-execution controls | CCI fail-closed gate + ATF PVR (RFC-ATF-4) |
| Authenticate continuously at runtime | ATF RCR chain (RFC-ATF-2) |
| Enforce human-in-the-loop | CCI multi-level authority + ATF AMG gate |
| Maintain offline-verifiable accountability | CCI on-chain + ATF PoGC + OEP (RFC-ATF-3) |

**Six requirements. Six covered. Zero gaps.**

---

*CCI × ATF Integration Mapping — OMNIX QUANTUM LTD × CCI*  
*Prepared for technical working session — Harold Nunes / Brent Heckerman*  
*May 2026*
