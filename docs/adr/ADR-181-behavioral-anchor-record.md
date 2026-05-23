# ADR-181: Behavioral Anchor Record (BAR)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Supersedes:** None  
**Amended by:** ADR-185 (invariant renumbering — see §Invariant Impact)  
**Extends:** ADR-131 (Execution Integrity Layer) · ADR-156 (ATF Identity & Delegation) · ADR-174 (AGVP)  
**Related:** ADR-182 (CCS) · ADR-183 (CTCHC) · RFC-ATF-6  
**Priority Record:** OMNIX-PAR-2026-BAR-001 · May 2026

---

## Context

### The Behavioral Attestation Gap

ADR-131 (Execution Integrity Layer) closed the decision→execution audit chain: every governance decision now produces an ExecutionReceipt that records whether an order was placed, filled, or failed. The chain from authorization to execution action is cryptographically verifiable.

But a structural gap remains: the ExecutionReceipt records **that an action occurred**, not **what the agent produced behaviorally during the session that led to the action**. A regulator examining the governance chain can verify:

- **Authorization:** the agent was authorized by a specific receipt
- **Execution:** a specific order was placed and filled
- **Decision space:** alternative paths were documented (ADR-178, CGE)

What they cannot verify: **what the agent actually said, did, or produced** during the interaction that generated the decision — the behavioral content of the execution.

This gap is consequential:

- **EU AI Act Art. 12** requires logging of AI system outputs
- **NIST AI RMF MEASURE 2.6** requires ongoing monitoring of AI system outputs
- **Enterprise legal counsel** require behavioral output evidence in liability proceedings

No ATF artifact prior to this ADR closes this gap.

### Why Not Extend ExecutionReceipt?

The ExecutionReceipt (ADR-131) operates at the exchange order level: it records a specific order sent to a specific exchange. The BAR operates at the behavioral output level: it records what the agent produced during an interaction turn. These are different abstraction layers.

A trading agent may produce 15 turns of analysis, commentary, and intermediate reasoning before emitting the order that produces an ExecutionReceipt. The BAR records each of those 15 turns. The ExecutionReceipt records the resulting order.

They are complementary, not overlapping.

---

## Decision

### Establish the Behavioral Anchor Record (BAR)

ADR-181 establishes the **Behavioral Anchor Record (BAR)** as the primary per-turn behavioral attestation artifact of the BEV layer (RFC-ATF-6). The BAR is a PQC-signed record produced at each execution turn, containing the output hash of the agent's behavioral output, bound to the governing receipt that authorized the session.

### Three Non-Negotiable Invariants

**Invariant 1: No silent turns (BEV-INV-001)**  
Every execution turn under a BEV-enabled session MUST produce a persisted BAR before the next turn begins. There is no execution path that completes a turn without a BAR.

**Invariant 2: Governing receipt binding (BEV-INV-002)**  
Every BAR carries a `governing_receipt_id` referencing the specific ATF record that authorized the session. A BAR without a valid governing receipt reference is structurally invalid.

**Invariant 3: PQC sealing before persistence (BEV-INV-004)**  
Every BAR is sealed with ML-DSA-65 over its `content_hash` before being written to the database. Unsealed BARs are not permitted in `atf_behavioral_anchor_records`.

### Record Architecture

```
BAR (Behavioral Anchor Record)
  bar_id                  — BAR-{16HEX}
  session_id              — BEV-SESSION-{16HEX}
  governing_receipt_id    — links to DR / TAR / RCR
  agent_id                — must match governing receipt agent_id
  turn_index              — 0-based, strictly monotonic per session
  output_hash             — "sha256:" + SHA-256(canonical output)
  output_hash_mode        — FULL | HASHED | REDACTED
  output_payload          — actual output (FULL mode only)
  constraint_vector       — snapshot of CV from governing receipt
  conformance_score       — embedded CCS conformance score [0.0, 1.0]
  ccs_verdict             — CONFORMANT | WARNING | CRITICAL | HALT | NO_DATA
  ccs_components          — {obs, css, sds, aas} breakdown
  chain_link              — CTCHC chain link for this turn
  genesis_hash            — present only in turn_index=0 BAR
  session_start_ns        — present only in turn_index=0 BAR
  bar_timestamp_ns        — nanosecond precision (time.time_ns())
  issued_at               — ISO 8601 UTC with nanosecond precision
  content_hash        — SHA-256 of canonical BAR JSON
  pqc_signature           — ML-DSA-65 sig over content_hash
  pqc_algorithm           — "ML-DSA-65"
  atf_spec_version        — "1.6"
```

### Output Hash Privacy Modes

Three modes balance forensic completeness with GDPR requirements:

| Mode | Storage | Use Case |
|---|---|---|
| FULL | output_payload + hash | Development, non-sensitive, forensic-critical |
| HASHED | hash only | Production (recommended), sensitive outputs |
| REDACTED | placeholder hash | GDPR-erased, non-deterministic outputs |

HASHED mode is the recommended production default. It provides output attestation without storing the payload content. Verification requires the original output to recompute the hash — which the verifying party must independently possess.

---

## Architecture

### Lifecycle

```
PENDING → ACTIVE (BAR persisted successfully)
ACTIVE  → SEALED (CTCHC session sealed at session close)
ACTIVE  → FLAGGED (integrity verification failure)
FLAGGED → [terminal, no recovery]
```

### Production Ordering (per turn)

```
1. Agent produces behavioral output BO
2. output_hash = SHA3-256(output_text.encode("utf-8")) [privacy mode applied]
3. CCS computed from BO and CV (if CCS_ENABLED)
4. chain_link computed from prior link and turn_hash(n)
5. BAR assembled with all fields
6. content_hash = SHA3-256(output_hash || governing_receipt_id || str(turn_index))
7. pqc_signature = ML-DSA-65.sign(content_hash.encode())
8. INSERT INTO atf_behavioral_anchor_records
```

Steps 3-4 MUST complete before step 5. Step 8 MUST complete before next turn.

### Offline Verification (5 steps)

1. Recompute `content_hash` = SHA3-256(output_hash || receipt_id || turn_index) → compare
2. Verify `pqc_signature` using platform public key
3. Verify `output_hash` = SHA3-256(output_text.encode()) [FULL mode]
4. Verify `chain_link` continuity from prior BAR or genesis hash
5. Verify `turn_index` is previous + 1

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS atf_behavioral_anchor_records (
    bar_id                    VARCHAR(64)      PRIMARY KEY,
    session_id                VARCHAR(64)      NOT NULL,
    governing_receipt_id      VARCHAR(128)     NOT NULL,
    agent_id                  VARCHAR(128)     NOT NULL,
    turn_index                INTEGER          NOT NULL,
    output_hash               VARCHAR(80)      NOT NULL,
    output_hash_mode          VARCHAR(16)      NOT NULL DEFAULT 'HASHED',
    output_payload            TEXT,
    constraint_vector         JSONB            NOT NULL DEFAULT '{}',
    ccs_score                 DOUBLE PRECISION NOT NULL DEFAULT -1.0,
    ccs_verdict               VARCHAR(16)      NOT NULL DEFAULT 'NO_DATA',
    ccs_components            JSONB            NOT NULL DEFAULT '{}',
    chain_link                VARCHAR(64)      NOT NULL,
    genesis_hash              VARCHAR(64),
    session_start_ns          BIGINT,
    bar_timestamp_ns          BIGINT           NOT NULL DEFAULT 0,
    issued_at                 TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    content_hash          VARCHAR(64)      NOT NULL DEFAULT '',
    pqc_signature             TEXT             NOT NULL DEFAULT '',
    pqc_algorithm             VARCHAR(32)      NOT NULL DEFAULT 'ML-DSA-65',
    atf_spec_version          VARCHAR(8)       NOT NULL DEFAULT '1.6',
    session_status            VARCHAR(32)      NOT NULL DEFAULT 'ACTIVE',
    created_at                TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);
```

**Indexes:**
- `idx_bar_session_id` — session lookup
- `idx_bar_governing_receipt_id` — receipt→BAR joins
- `idx_bar_session_id_turn_index` — ordered retrieval per session
- `idx_bar_ccs_verdict` — verdict-based audit queries
- `idx_bar_created_at DESC` — time-ordered access

**Design decisions:**
- `output_payload` is nullable — NULL when mode = HASHED or REDACTED
- `genesis_hash` and `session_start_ns` are NULL for turns > 0
- No UPDATE or DELETE triggers (BEV-INV-004 enforcement)

---

## Consequences

### Positive

- **Closes the behavioral attestation gap:** every authorized turn now has a verifiable, PQC-signed record of the agent's behavioral output — or its hash.
- **Governing receipt binding:** the BAR's `governing_receipt_id` closes the authorization→output chain. A regulator can trace from authorization to behavioral content.
- **Tamper-evident output attestation:** modifying `output_hash` after BAR sealing invalidates `pqc_signature`. Post-hoc output substitution is detectable.
- **Privacy-preserving:** HASHED mode provides attestation without storing sensitive content.
- **CTCHC-ready:** `chain_link` embedded in BAR enables session coherence verification without separate infrastructure.
- **OEP-portable:** BAR records can be included in OEP forensic packages (ADR-165) for portable behavioral evidence.

### Negative / Trade-offs

- **One synchronous DB write per turn:** BAR persistence is synchronous with turn completion. In high-frequency agent sessions, this adds ~0.5-1ms per turn on Railway PostgreSQL.
- **output_payload storage in FULL mode:** storing full outputs may violate GDPR right-to-erasure for PII-containing outputs. HASHED mode is the recommended production default.
- **Key stability dependency:** BAR verification requires the signing key to be stable (FMR-001). Key rotation invalidates existing BAR signatures unless re-signed.

---

## Invariant Impact

| Invariant | Impact |
|---|---|
| BEV-INV-001 | Mandatory BAR before output is delivered |
| BEV-INV-002 | content_hash = SHA3-256(output_hash ‖ receipt_id ‖ turn_index) |
| BEV-INV-003 | HALTED BAR → immediate session halt |
| BEV-INV-004 | PQC sealing + offline verifiability + append-only storage |
| BEV-INV-015 | Empty output_text → VIOLATION |
| BEV-INV-016 | BAR id MUST follow BAR-{HEX16} format |

---

## Files

| File | Purpose |
|---|---|
| `omnix_core/bev/behavioral_anchor_record.py` | Core module — BAR models, registry, guard |
| `tests/test_behavioral_anchor_record.py` | Full test suite |
| `docs/adr/ADR-181-behavioral-anchor-record.md` | This document |
| `docs/standards/RFC-ATF-6.md` | Normative specification |

---

## Compliance References

| Standard | Requirement | BAR Response |
|---|---|---|
| EU AI Act Art. 12 | Logging of AI system outputs | BAR per turn with PQC-signed output hash |
| EU AI Act Art. 72 | 7-year retention (high-risk AI) | BAR records subject to retention policy |
| NIST AI RMF MEASURE 2.6 | Ongoing monitoring of AI outputs | BAR provides per-turn output record |
| NIST GOVERN 1.7 | AI system behavior documentation | BAR is the behavioral documentation artifact |
| ISO 42001 §8.4 | AI system operation controls | BAR is the operational output control artifact |
| MiFID II Art. 17 | Pre- and post-output records | BAR complements ADR-131 ExecutionReceipt |

---

*OMNIX-BAR-001 | ADR-181 | May 2026*
