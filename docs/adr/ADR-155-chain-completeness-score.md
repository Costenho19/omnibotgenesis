# ADR-155 — Chain Completeness Score (CCS)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Tags:** transparency, audit, completeness, differentiator

---

## Context

The transparency chain (ADR-044, ISR-022) currently provides a binary `valid: true/false` integrity verdict.  A chain is either fully intact or has detectable breaks.  This binary model has a structural limitation:

- An auditor or regulator asking "How complete is the audit trail?" receives only a boolean.
- A chain that had 1 minor break out of 1,000 entries is indistinguishable at the API level from a chain that is 90% broken.
- Pending WAL entries, time gaps between entries, and coverage depth are invisible in the current output.

No audit transparency framework in the market (including Hyperledger Fabric's audit tools, AWS CloudTrail Insights, or Palantir's governance chain) publishes a single completeness metric with breakdown components.  Regulators and CAIOs are increasingly asking for quantitative audit assurance, not just boolean pass/fail.

---

## Decision

Add `compute_chain_completeness_score()` to `transparency_chain.py` and embed its output in `get_chain_with_integrity()`:

### CCS Components (max 100 points)

| Component | Max Points | Logic |
|---|---|---|
| `chain_integrity_score` | 50 | 50 pts with no breaks; -8 per detected break (Merkle root mismatch OR prev_log_hash mismatch) |
| `temporal_consistency_score` | 30 | 30 pts; -10 per anomalous gap (gap > 24 h AND > 100× the minimum gap in the window) |
| `minimum_coverage_score` | 20 | 20 pts flat if chain has ≥1 entry; 0 for empty chain |
| `pending_penalty` | max -30 | -3 per WAL pending entry; capped at -30 |

### Verdict Thresholds

| CCS | Verdict | Meaning |
|---|---|---|
| ≥ 90 | COMPLETE | Audit trail is fully defensible |
| 70–89 | DEGRADED | Minor gaps; escalation recommended |
| 50–69 | PARTIAL | Significant gaps; audit integrity uncertain |
| < 50 | COMPROMISED | Audit trail cannot be trusted as complete |
| 0 (no data) | NO_DATA | Empty chain |

### API Change

`get_chain_with_integrity()` gains an optional `pending_table_count: int = 0` parameter.  The returned `integrity` dict now includes all CCS fields merged in:

```python
result = chain.get_chain_with_integrity(symbol="BTC", limit=50, pending_table_count=wal_pending)
print(result["integrity"]["ccs"])           # e.g. 93.0
print(result["integrity"]["ccs_verdict"])   # e.g. "COMPLETE"
```

This is a backward-compatible addition: existing callers reading only `valid`, `length`, and `breaks` continue to work.

---

## Consequences

### Positive

- **Quantitative audit assurance**: regulators, CAIOs, and external auditors receive a number they can compare across reporting periods — not just a boolean.
- **Differentiated severity**: a DEGRADED chain (minor gap) is distinguishable from a COMPROMISED chain (systematic tampering).
- **Detects previously invisible risks**: pending WAL entries and time anomalies were previously undetectable at the API level.
- **Backward compatible**: existing `get_chain_with_integrity()` callers need no changes.

### Negative / Trade-offs

- CCS is computed on the entries returned by `get_chain()` (up to `limit`).  A very large chain with tampering outside the query window may score COMPLETE for the queried window while having breaks elsewhere.
- `temporal_consistency_score` uses wall-clock timestamps stored in the DB.  Clock skew on the writing node could produce false anomalies.

---

## Implementation Notes

- File: `omnix_core/evidence/transparency_chain.py`
- Function: `compute_chain_completeness_score(entries, pending_table_count=0)`
- Modified: `get_chain_with_integrity()` — calls CCS and merges result into integrity dict
- Tests: `tests/test_differentiators.py` — `TestCCSNormal`, `TestCCSAdversarial`

### Institutional Explanation (non-technical)

> Instead of answering "Is the audit trail intact? Yes or No," OMNIX now answers "The audit trail is 94% complete, with a score breakdown: full chain integrity, no pending entries, and no anomalous time gaps."  A CAIO can present this number in a board audit meeting.  If tampering has occurred, the score drops visibly — the number doesn't lie.

---

## Invariant Impact

| Invariant | Impact |
|---|---|
| INV-006 (Transparency Chain Read-Path Verification) | Strengthened — CCS is additional verification layer |
| INV-001 (Fail-Closed) | Not affected |
| INV-002 (Receipt per Decision) | Not affected |

`get_chain_with_integrity()` is the recommended read path per ISR-022.  CCS is now part of its standard output.

---

*OMNIX-CCS-001 | ADR-155 | May 2026*
