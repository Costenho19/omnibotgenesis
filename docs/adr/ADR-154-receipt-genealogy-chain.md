# ADR-154 — Receipt Genealogy Chain

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Tags:** receipts, audit, lineage, differentiator

---

## Context

Every governance receipt (ADR-028, ADR-078) is currently a standalone artifact.  It proves a single decision was made, with a valid signature, at a specific time — but it does not record what decisions came before it for the same asset.

This creates an auditability gap: a regulator reviewing an APPROVED receipt cannot determine whether it was the first decision for that asset in the session, or whether it followed 10 previous BLOCKs that were each submitted with incrementally modified signals until one finally passed.  The latter pattern is a material governance concern — it is the human equivalent of "shopping" for an approval.

### Industry Context

No governance receipt system in production (including AWS governance controls, Azure Policy receipts, or Palantir Foundry decision logs) links sequential decisions for the same asset into a verifiable chain.  Each receipt is treated as independent.  OMNIX receipts are nodes in a linked list.

---

## Decision

Add a Receipt Genealogy Chain to `DecisionReceiptEngine.generate_receipt()`:

1. **Module-level genealogy buffer** (`_genealogy_buffer`): a `dict[str, deque]` mapping `"{domain}:{asset}"` keys to ordered deques of receipt IDs (max 50 per key, protected by `_genealogy_lock`).

2. **`_build_genealogy()` function**: called inside `generate_receipt()`, before the `content_hash` is computed.  Returns:
   - `parent_receipt_id` — ID of the immediately preceding receipt for this key (None if first)
   - `chain_root_id` — ID of the first receipt in this session's chain for this key
   - `generation_depth` — 1-indexed position in the chain
   - `chain_key` — `"{domain}:{asset}"`
   - `is_chain_root` — True when this is the first receipt

3. **`public_payload['genealogy']`**: embedded BEFORE `content_hash` computation.  This is the critical design decision: because genealogy is part of the hashed content, any tampering with `parent_receipt_id` (e.g., removing the evidence that a BLOCK preceded an APPROVE) changes the `content_hash` and breaks signature verification.

### Tamper-Evidence Proof

```
payload = { ..., genealogy: { parent_receipt_id: "OMNI-abc", ... } }
content_hash = SHA256(json.dumps(payload, sort_keys=True))
signature = Dilithium3.sign(content_hash)
```

If an attacker changes `parent_receipt_id` to `None` to hide the preceding BLOCK:

```
tampered_payload = { ..., genealogy: { parent_receipt_id: None, ... } }
tampered_hash ≠ content_hash  →  signature verification fails
```

### Scope

- In-memory only (per-process).  Genealogy resets on process restart.
- Max 50 receipts tracked per domain:asset key (ring buffer).
- Backward compatible: existing receipts without a `genealogy` field still verify correctly (hash was computed without it).

---

## Consequences

### Positive

- **Decision lineage is now verifiable**: auditors can trace the complete sequence of approvals, blocks, and holds for any asset within a session — without database access.
- **Tamper-evident**: genealogy is cryptographically bound to the receipt signature.  Removing or altering parent linkage breaks the PQC signature.
- **Zero impact on existing receipts**: legacy receipts (no `genealogy` key) still verify via their stored `content_hash`.
- **Thread-safe**: `_genealogy_lock` protects all buffer operations.

### Negative / Trade-offs

- In-memory only: genealogy does not persist across restarts.  Cross-restart continuity requires a DB-backed genealogy store (planned RC-2).
- `generation_depth` is session-scoped, not global.  A process restart resets depth to 1.

---

## Implementation Notes

- File: `omnix_core/evidence/decision_receipt.py`
- Buffer: `_genealogy_buffer`, `_genealogy_lock`, `_GENEALOGY_MAX_CHAIN = 50`
- Function: `_build_genealogy(domain, asset, receipt_id)`
- Insertion point: `generate_receipt()` — after `avm_result` block, before `content_hash`
- Tests: `tests/test_differentiators.py` — `TestGenealogy`

### Institutional Explanation (non-technical)

> Every approval receipt now records who its predecessor was.  If a decision was BLOCKED three times before finally being APPROVED, the APPROVED receipt contains a cryptographic reference to the preceding BLOCKED receipt.  Tampering with that history — trying to make an approval look like the first and only decision — breaks the cryptographic signature.  It is like a paper trail where each page references the previous one, and altering any page invalidates the entire document's notary stamp.

---

## Invariant Impact

| Invariant | Impact |
|---|---|
| INV-002 (Receipt per Decision) | Not affected — genealogy is additive |
| INV-003 (Hash Version in Receipt) | Not affected |
| INV-008 (PQC Signing) | Strengthened — genealogy data is signed |

**Schema change**: `public_payload` gains a `genealogy` object.  This is a new field addition (backward compatible — no existing field is removed or renamed).  A Migration Plan is not required per the Evolution Protocol (only column additions to `decision_receipts` DB table require one; this is a JSON payload field).

---

*OMNIX-GEN-001 | ADR-154 | May 2026*
