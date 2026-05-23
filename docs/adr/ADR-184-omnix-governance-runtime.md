# ADR-184 — OMNIX Governance Runtime (OGR)

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-23  
**Supersedes:** —  
**Related:** ADR-156, ADR-157, ADR-158, ADR-159, ADR-173, ADR-174, ADR-181, ADR-182, ADR-183  
**RFC:** RFC-ATF-1 through RFC-ATF-6 (all six)

---

## Context

The Agent Trust Fabric (ATF) has grown to six layers across six RFCs, producing
a rich set of governance primitives: identity records, delegation receipts, temporal
admissibility records, runtime continuity records, cognitive governance engines,
and the new Behavioral Execution Verification (BEV) layer.

External AI agent developers face a significant integration burden: to be fully
ATF-BEV-Compliant they must integrate six distinct subsystems, understand 106
invariants, and produce three new artifact classes (BAR, CCS, CTCHC) per session.

**Problem:** The governance stack needs a single integration point that activates
all six layers simultaneously, without requiring integrators to know the internal
architecture.

**Competing approaches examined:**
- **CLARIXO Continuity Governance**: stateful agent continuity tracking with no
  cryptography and no formal invariants. Covers concepts similar to L3/L4 only.
- **MTCP (Ahmad A)**: behavioral measurement via empirical model evaluation.
  No cryptographic binding, no receipt architecture, no proactive veto integration.
- **VeriSigil**: governance specifications as contracts. No runtime attestation,
  no hash chain, no PQC.

None of the above produce:
  1. Receipt-bound behavioral attestation
  2. Post-quantum cryptographic sealing on every turn artifact
  3. Cross-turn coherence proof linked to a governing receipt
  4. Anticipatory veto integration (CCS → AGVP loop)

---

## Decision

Introduce the **OMNIX Governance Runtime (OGR)** — a premium integration layer
that exposes all six ATF layers through a clean session-oriented API.

### Architecture

```
External AI Agent
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                OMNIX Governance Runtime                  │
│                                                          │
│  POST /v1/govern/session/start                          │
│     ├─ Validates governing_receipt_id                   │
│     ├─ Activates ATF-L1 through ATF-L6                 │
│     └─ Initializes CTCHC genesis (BEV-INV-010)         │
│                                                          │
│  POST /v1/govern/session/{id}/turn                      │
│     ├─ BAR  ← PQC-signed behavioral attestation        │
│     ├─ CCS  ← constraint conformance signal            │
│     ├─ CTCHC link ← coherence hash chain extension     │
│     └─ OGR verdict (CONFORMANT / WARNING / HALT)       │
│                                                          │
│  POST /v1/govern/session/{id}/close                     │
│     ├─ CTCHC seal (BEV-INV-013/014)                    │
│     └─ Offline-verifiable proof package                 │
│                                                          │
│  GET  /v1/govern/session/{id}/proof                     │
│     └─ Complete Behavioral Attestation Chain            │
│                                                          │
│  GET  /v1/govern/session/{id}/status                    │
│  POST /v1/govern/verify                                 │
│  GET  /v1/govern/compliance/{id}                        │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│           ATF Core Modules (all existing)                │
│  L1: trust_lattice.py (AIR)                             │
│  L2: delegation_receipt.py (DR)                         │
│  L3: temporal_authority.py (TAR)                        │
│  L4: runtime_continuity.py (RCR)                        │
│  L5: cognitive governance engines                       │
│  L6: bev/ (BAR + CCS + CTCHC)  ← NEW                   │
└──────────────────────────────────────────────────────────┘
```

### Key invariants delegated to BEV (ADR-181/182/183)

| Invariant    | Enforced in           | Description                                          |
|-------------|----------------------|------------------------------------------------------|
| BEV-INV-001 | BAREngine             | Every turn → BAR before output delivered             |
| BEV-INV-002 | BAREngine             | BAR content_hash covers output+receipt+index         |
| BEV-INV-003 | BAREngine             | HALT BAR → immediate session halt (forensic state)  |
| BEV-INV-004 | BAREngine             | BAR PQC-verifiable offline                           |
| BEV-INV-005 | CCSEngine             | Every BAR → CCS in same atomic step                 |
| BEV-INV-006 | CCSEngine             | CCS score ∈ [0.0, 1.0]                              |
| BEV-INV-007 | CCSEngine             | CRITICAL verdict → AGVP watchdog                    |
| BEV-INV-008 | CCSEngine             | Cumulative drift > threshold → HALT                 |
| BEV-INV-009 | CCSEngine             | CCS history append-only, hash-linked                |
| BEV-INV-010 | CTCHCEngine           | Chain initialized before first BAR                  |
| BEV-INV-011 | CTCHCEngine           | Link = H(prev ‖ turn ‖ receipt)                     |
| BEV-INV-012 | CTCHCEngine           | Gaps in sequence → verify fails                     |
| BEV-INV-013 | CTCHCEngine           | Seal covers complete chain                          |
| BEV-INV-014 | CTCHCEngine           | Seal PQC-signed before OEP export                   |
| BEV-INV-015 | BAREngine             | Empty output_text → VIOLATION (no silent outputs)   |
| BEV-INV-016 | BAREngine             | BAR id MUST follow "BAR-{HEX16}" format             |
| BEV-INV-017 | CCSEngine             | Drift accumulator isolated per session_id           |
| BEV-INV-018 | CTCHCEngine           | Every link's receipt_id MUST match chain receipt    |

### OGR-level invariant (ADR-184)

| Invariant    | Enforced in           | Description                                          |
|-------------|----------------------|------------------------------------------------------|
| OGR-INV-001 | GovernanceRuntime     | Session MUST activate all 6 ATF layers simultaneously — partial activation is not ATF-BEV-Compliant |

### Database tables introduced

| Table                           | Purpose                                 |
|---------------------------------|-----------------------------------------|
| `atf_ogr_sessions`              | OGR session state                       |
| `atf_behavioral_anchor_records` | BAR per-turn attestations (ADR-181)     |
| `atf_constraint_conformance_signals` | CCS turn conformance (ADR-182)    |
| `atf_coherence_hash_chains`     | CTCHC chain headers (ADR-183)           |
| `atf_coherence_chain_links`     | CTCHC per-turn links (ADR-183)          |

All tables use `CREATE TABLE IF NOT EXISTS` — created automatically on first request.

---

## Consequences

### Positive
- External AI agents gain full ATF-BEV-Compliant governance in ≤ 5 API calls.
- Every session proof is offline-verifiable — auditors need no OMNIX access.
- The combination of receipt-binding + PQC + behavioral attestation + coherence
  chain is architecturally unique. No competitor produces all four simultaneously.
- Integration surface is clean and familiar (REST JSON, no OMNIX internals exposed).

### Negative / Mitigations
- Adds five new DB tables. Mitigated: auto-created, all indexed.
- CTCHC `_tip_cache` is in-process memory; multi-dyno deployments should ensure
  session affinity or use DB tip loading (implemented as fallback).
- `verify_artifact` for CCS requires DB access; true offline verification is only
  supported for BAR and CTCHC which embed all necessary fields in the artifact.

---

## Compliance tier: ATF-BEV-Compliant

Any session created via the OGR automatically qualifies for the ATF-BEV-Compliant
designation — the sixth and highest tier in the OMNIX governance hierarchy.

The designation requires:
1. All 18 BEV invariants (BEV-INV-001 through BEV-INV-018) satisfied
2. PQC sealing on all BAR artifacts and the CTCHC seal
3. Governing receipt bound to the session at genesis
4. Offline-verifiable proof package producible at close

---

*ADR-184 · OMNIX QUANTUM LTD · Harold Nunes · May 2026*
