# ADR-149 — Governance Replay Fidelity Classification

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** —  
**Related:** ADR-145 (Governance Replay Engine)  
**Module:** `omnix_core/simulation/governance_replay.py`

---

## Context

ADR-145 established the Governance Replay Engine. The GOVERNANCE FAILURE MODE REPORT (HGA-2026-Q3-001, Section 6) documented a tension between commercial claims and technical reality:

| Dimension | Actual Fidelity |
|---|---|
| Signal Fidelity | HIGH — derived from real market data |
| Verdict Fidelity | NON-COMPUTATIONAL — derived from `expected_verdict` constants |
| Checkpoint Fidelity | LOW — gate logic not invoked; checkpoints are descriptive strings |
| Format Fidelity | HIGH — identical receipt structure to production |
| Hash/Sign Fidelity | HIGH — same SHA-256 + Dilithium-3 as production |

External auditors and institutional clients require a clear, machine-readable declaration of which fidelity class each receipt belongs to. A receipt that says "OMNIX BLOCKED FTX" but does not declare the fidelity of that claim is legally and institutionally ambiguous.

---

## Decision

Define a formal `ReplayFidelityClass` enum and embed a `fidelity_classification` field in every `SignedReplayReceipt`. Implement `verify_replay_chain()` as a public, standalone verification function.

### Fidelity Classes

| Class | Value | Meaning |
|---|---|---|
| `FORENSIC_SIMULATION` | `"FORENSIC_SIMULATION"` | Verdict derived from historically-documented expected outcome. Signals are real; gate logic is not invoked. Correct claim: "OMNIX framework applied to real signal conditions." |
| `COMPUTATIONAL_REPLAY` | `"COMPUTATIONAL_REPLAY"` | Verdict computed by live gate logic against historical signals. Full computational fidelity. (Future — not yet implemented.) |
| `PARTIAL_COMPUTATIONAL` | `"PARTIAL_COMPUTATIONAL"` | Some checkpoints computed live; others use forensic expected verdicts. (Future — partial implementation.) |

All current OMNIX replay receipts (ADR-145) are `FORENSIC_SIMULATION`.

### Claim Governance

**Forbidden claim:**
> "The same governance engine running in production today — applied retroactively."

**Correct claim:**
> "The OMNIX governance framework — applied retroactively to the exact signal conditions that existed when each crisis unfolded. Verdict fidelity: FORENSIC_SIMULATION — derived from OMNIX forensic documents aligned with public market records."

### verify_replay_chain()

A standalone function that takes a list of `SignedReplayReceipt` objects and:
1. Re-computes the canonical hash for each receipt.
2. Verifies it matches `receipt.canonical_hash`.
3. Returns a verification report with per-receipt status.

This enables independent external verification of a complete replay session without OMNIX infrastructure.

---

## Fidelity Attestation in Receipt

Every `SignedReplayReceipt.to_dict()` now includes:

```json
{
  "fidelity_classification": "FORENSIC_SIMULATION",
  "fidelity_note": "Verdict derived from historically-verified expected outcome (OMNIX forensic documents). Signal data sourced from public market records. Canonical hash seals the full payload.",
  "admissible_claim": "OMNIX governance framework applied to real signal conditions of [scenario] — producing this verifiable receipt."
}
```

---

## Consequences

### Positive
- **Legal defensibility**: explicit fidelity class prevents misrepresentation claims.
- **Regulator-ready**: auditors can inspect `fidelity_classification` without reading source code.
- **Future-proof**: when computational replay is implemented, receipts upgrade to `COMPUTATIONAL_REPLAY` with no UI/API changes.
- **verify_replay_chain()**: enables offline verification by any third party.

### Negative
- **Receipt format change**: adds 3 new fields to `to_dict()`. Backward-compatible.

---

## Migration

Existing ADR-145 replay receipts (before this ADR) are implicitly `FORENSIC_SIMULATION`. The `/crisis-replay` UI displays fidelity class next to each receipt. The public verifier (`omnix_verify.py`) reports fidelity class in its output.

---

*OMNIX QUANTUM — Decision Governance Infrastructure*  
*ADR-149 · Replay Fidelity Classification · omnixquantum.net*
