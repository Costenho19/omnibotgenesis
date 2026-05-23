# ADR-183: Cross-Turn Coherence Hash Chain (CTCHC)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Supersedes:** None  
**Amended by:** ADR-185 (invariant renumbering — see §Invariant Impact)  
**Extends:** ADR-181 (BAR) · ADR-155 (Chain Completeness Score) · ADR-165 (OEP)  
**Related:** ADR-181 (BAR) · ADR-182 (CCS) · RFC-ATF-6  
**Priority Record:** OMNIX-PAR-2026-CTCHC-001 · May 2026

---

## Context

### The Multi-Turn Coherence Problem

The BAR (ADR-181) provides per-turn behavioral attestation. Each turn produces a PQC-signed record of the agent's output for that turn, bound to the governing receipt. A set of valid BARs is a strong attestation artifact — but it is not a **session integrity proof**.

A set of N valid BARs does not prove:

1. **Completeness:** all N turns are present (an adversary could suppress a turn where a violation occurred)
2. **Ordering:** the turns are presented in the original execution order (turn reordering changes causality and behavioral trajectory)
3. **Session binding:** the BARs belong to this specific session under this specific governing receipt (cross-session BAR substitution is possible without a binding mechanism)

This is Gap_MCP (Multi-Turn Coherence Problem). A governance stack with valid BARs but without a session coherence mechanism provides per-turn attestation but not session-level behavioral integrity.

### Why Not Use the ADR-155 Chain Completeness Score?

ADR-155 (Chain Completeness Score) measures audit trail completeness: the percentage of decisions that have corresponding execution receipts, with temporal consistency and break detection. It operates on the audit trail as a whole — across many sessions, many agents, many decisions.

The CTCHC operates on a single BEV Session: it proves that a specific sequence of turns, all governed by a specific receipt, occurred in order and without modification. These are structurally different problems with structurally different constructions.

The CCS (ADR-155) and the CTCHC are complementary:
- CCS: audit trail completeness across the fleet
- CTCHC: session behavioral coherence for a single session

### Why Not Use a Standard Audit Log Hash Chain?

Existing audit log hash chains (CloudTrail, Splunk, OpenTelemetry) provide integrity for system event sequences. They differ from the CTCHC in one critical structural way:

**Existing chains are not bound to a specific governance receipt.** The genesis hash of an existing audit log chain is seeded by the logging system's configuration — not by the authorization that governs the session. This means:

- BARs from session S1 (governed by receipt R1) could be presented as if from session S2 (governed by receipt R2) — the chain prefix would differ, but only if R2 differs from R1.
- If R1 ≈ R2 (same receipt type, different instance), the cross-session substitution is not detectable from the chain alone.

The CTCHC's genesis hash is seeded by `governing_receipt_id + session_id + session_start_ns`. This makes the chain **inseparable from the specific authorization that governs it** — a structural property no existing audit log chain provides.

---

## Decision

### Establish the Cross-Turn Coherence Hash Chain (CTCHC)

ADR-183 establishes the **Cross-Turn Coherence Hash Chain (CTCHC)** as the session integrity artifact of the BEV layer (RFC-ATF-6). The CTCHC is a cryptographic hash chain linking each BAR's output hash to the previous turn's chain link, seeded by the governing receipt identifier and session identifier. The final chain hash provides offline-verifiable proof of session coherence.

### Core Design: Receipt-Seeded Genesis Hash

```
genesis_hash = SHA3-256(
    session_id.encode("utf-8") +
    b"||" +
    governing_receipt_id.encode("utf-8") +
    b"||" +
    b"OMNIX-CTCHC-GENESIS"
)
```

This binding is the CTCHC's novel contribution: the genesis hash is derived from the governing receipt and session identity. No chain from a different governing receipt or different session can produce the same genesis hash. Cross-session BAR substitution produces a genesis hash mismatch detectable by any verifier.

### Chain Link Construction

For turn n >= 0:
```
link_payload(n) = json.dumps({
    "prev": prev_hash,
    "turn": output_hash(n),
    "receipt": governing_receipt_id
}, sort_keys=True).encode()

chain_link(0) = SHA3-256(link_payload where prev=genesis_hash)
chain_link(n) = SHA3-256(link_payload where prev=chain_link(n-1))  [n > 0]
```

Each chain link is a 64-character lowercase hexadecimal SHA-256 digest. The chain is embedded in the corresponding BAR before the BAR is sealed — making the chain link tamper-evident.

### Session Sealing (Session Integrity Proof)

At session close:
```
final_chain_hash = chain_link(N-1)

seal_hash = SHA3-256(seal_payload(genesis_hash + all_link_hashes + current_tip_hash))

ctchc_seal = base64(ML-DSA-65.sign(seal_hash))
```

The sealed CTCHC record is the **Session Integrity Proof (SIP)**: any party with the CTCHC record, the BAR sequence, and the platform public key can verify session coherence without OMNIX infrastructure access.

---

## What the CTCHC Detects

| Attack | Detection Method |
|---|---|
| Turn omission | Missing BAR at turn k → chain_link(k+1) diverges from expected value |
| Turn reordering | Swapping T_i and T_{i+1} → chain_link(i+1) depends on chain_link(i), swap produces wrong value |
| Cross-session BAR substitution | BARs from different session → genesis_hash mismatch at CTCHC verification Step 4 |
| Output hash substitution | output_hash modified in BAR → chain_link computed from modified hash diverges from expected |
| Genesis hash tampering | genesis_hash included in seal_payload → modification invalidates ctchc_seal (seal_hash) |

---

## Architecture

### Chain State Per Session

```
Session S begins:
  genesis_hash = f(governing_receipt_id, session_id, session_start_ns)
  chain_state = genesis_hash

Turn 0:
  chain_link(0) = SHA3-256(link_payload(prev=genesis_hash, turn=output_hash_0, receipt=receipt_id))
  → embedded in BAR_0 before BAR_0 is sealed

Turn n:
  chain_link(n) = SHA3-256(link_payload(prev=link(n-1), turn=output_hash_n, receipt=receipt_id))
  → embedded in BAR_n before BAR_n is sealed

Session close:
  final_chain_hash = chain_link(N-1)
  CTCHC record assembled and sealed with ML-DSA-65
  All BARs in session transition to SEALED
```

### Offline Verification (6 steps)

1. **CTCHC record integrity:** verify `ctchc_seal` (ML-DSA-65) over `seal_hash`
2. **BAR completeness:** verify `len(all_bar_ids) = turn_count`, all turn_index values present (0…N-1)
3. **Individual BAR verification:** verify each BAR per ADR-181 §Offline Verification
4. **Genesis hash verification:** recompute genesis hash from BAR_0 fields, compare to CTCHC
5. **Chain reconstruction:** recompute chain_link(0)…chain_link(N-1) from BAR output hashes, compare to embedded chain_links
6. **Final chain hash verification:** compare reconstructed chain_link(N-1) to CTCHC.final_chain_hash

All 6 steps MUST pass for the session to be COHERENT.

### Partial Chain Recovery

When infrastructure failure mid-session prevents BAR persistence:

- If failure is at turn k+1 and turns 0…k are complete: CTCHC_PARTIAL can be sealed over chain_link(k)
- CTCHC_PARTIAL covers turns 0…k only; the failure is documented
- CTCHC_PARTIAL MUST NOT be presented as a full Session Integrity Proof
- Non-contiguous failures (missing turns from session interior): CHAIN_BROKEN, no recovery possible

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS atf_coherence_hash_chains (
    ctchc_id              VARCHAR(64)  PRIMARY KEY,
    session_id            VARCHAR(64)  NOT NULL UNIQUE,
    governing_receipt_id  VARCHAR(128) NOT NULL,
    genesis_hash          VARCHAR(64)  NOT NULL,
    final_chain_hash      VARCHAR(64)  NOT NULL,
    turn_count            INTEGER      NOT NULL,
    all_bar_ids           JSONB        NOT NULL DEFAULT '[]',
    session_start_ns      BIGINT       NOT NULL DEFAULT 0,
    session_close_ns      BIGINT       NOT NULL DEFAULT 0,
    session_status        VARCHAR(32)  NOT NULL DEFAULT 'BEV-COMPLETE',
    failure_turn_index    INTEGER,
    failure_reason        TEXT         NOT NULL DEFAULT '',
    seal_hash    VARCHAR(64)  NOT NULL DEFAULT '',
    ctchc_seal            TEXT         NOT NULL DEFAULT '',
    pqc_algorithm         VARCHAR(32)  NOT NULL DEFAULT 'ML-DSA-65',
    atf_spec_version      VARCHAR(8)   NOT NULL DEFAULT '1.6',
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

**Indexes:**
- `idx_ctchc_session_id` — primary lookup (UNIQUE)
- `idx_ctchc_governing_receipt_id` — receipt-level CTCHC queries
- `idx_ctchc_session_status` — filter complete/incomplete/broken
- `idx_ctchc_created_at DESC` — chronological access

**Design decisions:**
- `session_id` is UNIQUE — one CTCHC per BEV Session
- `all_bar_ids` is JSONB array of bar_ids in turn_index order — enables completeness verification without loading all BARs
- `session_status`: BEV-COMPLETE | BEV-INCOMPLETE | CTCHC_SEAL_FAILED | CHAIN_BROKEN | CTCHC_PARTIAL
- No UPDATE or DELETE (BEV-INV-014 enforcement)

---

## Invariant Impact

| Invariant | Statement |
|---|---|
| BEV-INV-010 | Chain initialized before first BAR (genesis seeded by session_id + receipt_id) |
| BEV-INV-011 | link = SHA3-256(json(prev, turn=output_hash, receipt)) — construction |
| BEV-INV-012 | Gaps in turn sequence (0…N-1) → verify fails |
| BEV-INV-013 | seal_hash covers complete chain (genesis to tip) |
| BEV-INV-014 | Seal ML-DSA-65 signed before OEP export |
| BEV-INV-018 | Every link's governing_receipt_id MUST match chain receipt |

---

## Formal Verification

Z3 SMT proof BEV-FVS-005 covers chain monotonicity (structural):

```python
# chain_link(n) = SHA3-256(json.dumps({prev, turn, receipt}, sort_keys=True))
# For n != m: 'prev' differs (chain evolves) => JSON payload differs
# => chain_link(n) != chain_link(m)
# Conditional on SHA3-256 collision resistance (FIPS 202)
# P(collision per session) < 2^{-115} for sessions < 100_000 turns
```

---

## Consequences

### Positive

- **Closes Gap_MCP (Multi-Turn Coherence Problem):** provides the first published session-level behavioral integrity proof for multi-turn AI agent sessions
- **Receipt-seeded:** genesis hash design makes cross-session BAR substitution detectable without any database queries — only the CTCHC record and BAR sequence are needed
- **Turn omission detection:** any missing BAR causes chain divergence at the next turn, detectable by any verifier
- **Offline verifiable:** the 6-step verification protocol requires no OMNIX infrastructure — only the CTCHC record, BARs, and platform public key
- **OEP-portable:** CTCHC records can be included in OEP forensic packages (ADR-165), providing portable session integrity proof
- **Deterministic construction:** given the same inputs, any implementation produces identical chain links — enabling independent verification by any party

### Negative / Trade-offs

- **Sequential chain construction:** chain_link(n) requires chain_link(n-1). In concurrent agent deployments, chain link computation must be serialized even if turn outputs are computed in parallel.
- **Session turn limit:** CTCHC imposes a soft limit of 100,000 turns per session (R-CTCHC-05). Sessions exceeding this limit must be split into sub-sessions with separate governing receipts. In practice, sessions exceeding 1,000 turns are unusual.
- **Key rotation impact:** CTCHC records sealed with a rotated key require the new key to be the verification target. FMR-001 key stability applies.

### Not Permitted

- CTCHC_PARTIAL record presented as a Session Integrity Proof
- UPDATE or DELETE on `atf_coherence_hash_chains`
- Genesis hash computed without `governing_receipt_id` (breaks receipt binding)
- Sessions with more than 100,000 turns under a single CTCHC

---

## Comparison with ADR-155

| Dimension | ADR-155 (Chain Completeness Score) | ADR-183 (CTCHC) |
|---|---|---|
| Scope | Audit trail across all sessions | Single BEV Session |
| Purpose | Audit completeness measurement | Behavioral session integrity proof |
| Seeding | Audit trail configuration | Governing receipt + session identity |
| Output | Score (0–100%) | Hash chain + PQC seal |
| Detects | Missing execution receipts | Turn omission, reordering, substitution |
| Offline verification | No | Yes (BEV-INV-013) |

---

## Files

| File | Purpose |
|---|---|
| `omnix_core/bev/coherence_hash_chain.py` | CTCHC construction, sealing, verification |
| `tests/test_coherence_hash_chain.py` | Full test suite |
| `docs/adr/ADR-183-cross-turn-coherence-hash-chain.md` | This document |
| `docs/standards/RFC-ATF-6.md` | Normative specification |

---

*OMNIX-CTCHC-001 | ADR-183 | May 2026*
