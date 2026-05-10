# ADR-152 — Governance Threshold Probe Detection (GTPD)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Tags:** security, avm, adversarial-detection, differentiator

---

## Context

The Adaptive Veto Machine (AVM) evaluates each governance request by comparing a drift score against a per-domain approval threshold.  This threshold is not published, but it can be empirically reverse-engineered: an adversary submits many governance requests with slightly different signals and observes which ones pass vs. block.  After enough attempts, the adversary knows the exact drift boundary and can craft inputs that always barely pass — defeating the governance gate without ever triggering a block.

This is a structural side-channel attack on governance integrity.  No other governance platform detects it because no other platform records evaluation patterns across requests for the same domain.

### Why Now

The Hidden Gap Audit (HGA-2026-Q2-001) and the Governance Failure Mode Report (HGA-2026-Q3-001) both identified the AVM approval threshold as an attackable parameter.  GTPD is the direct remediation for failure mode FMR-007 ("Threshold Reverse-Engineering via Repeated Probing").

---

## Decision

Add Governance Threshold Probe Detection to `AssumptionValidityMonitor`:

1. **Per-domain drift history ring buffer** (`_gtpd_drift_history`): stores the last 50 drift scores per domain in a thread-safe module-level dict.  Every call to `evaluate()` appends to this buffer.

2. **`ThresholdProbeReport` dataclass**: captures `probe_id`, `clustering_coefficient`, `evaluations_near_threshold`, `probe_score` (0–100), and `probe_verdict` (INSUFFICIENT_DATA / CLEAN / SUSPECTED / CONFIRMED).

3. **`_detect_threshold_probe()` method**: runs after every valid evaluation.  Defines "near threshold" as within ±30% of the current threshold value.  Computes clustering coefficient = near_count / total_count.  Verdicts:
   - **INSUFFICIENT_DATA**: fewer than 3 evaluations in history
   - **CLEAN**: < 20% near-threshold
   - **SUSPECTED**: ≥ 3 evals, 20–60% near-threshold
   - **CONFIRMED**: ≥ 5 evals, > 60% near-threshold

4. **`probe_report` field in `AVMResult`**: embedded in every successful evaluation.  Serialized via `to_dict()`.

### What GTPD Does NOT Do

- GTPD never changes `AVMResult.is_valid`.  It is a detection-only layer.
- GTPD does not block requests.  Blocking is the operator's responsibility upon a CONFIRMED verdict.
- GTPD does not persist across process restarts (in-memory only).  A restart resets the window.

---

## Consequences

### Positive

- **Verifiable evidence**: `probe_report` is embedded in every AVMResult and flows through to governance receipts — it is part of the audit record.
- **Adversarial detection**: CONFIRMED verdict requires ≥ 5 evaluations clustering > 60% near the threshold — statistically improbable by chance for any legitimate workload.
- **No false positives on normal use**: diverse real-world drift scores spread across 0–100; natural workloads will never cluster near any specific threshold.
- **Thread-safe**: `_GTPD_HISTORY_LOCK` protects the shared buffer.

### Negative / Trade-offs

- In-memory only: a probe attack across process restarts evades detection in the current window.
- Requires ≥ 3 evaluations before any verdict.  First-call evaluations always return INSUFFICIENT_DATA.

---

## Implementation Notes

- File: `omnix_core/governance/assumption_validity_monitor.py`
- Dataclass: `ThresholdProbeReport`
- Buffer: `_gtpd_drift_history`, `_GTPD_HISTORY_LOCK`, `_GTPD_HISTORY_SIZE = 50`
- Methods: `_update_drift_history()`, `_detect_threshold_probe()`
- Tests: `tests/test_differentiators.py` — `TestGTPDNormal`, `TestGTPDAdversarial`

### Institutional Explanation (non-technical)

> Imagine someone testing a security door repeatedly, each time with slightly different force, trying to find the exact threshold that opens it.  GTPD detects when someone is doing exactly that to OMNIX's governance gate — and records the pattern as verifiable evidence in every subsequent governance receipt.

---

## Invariant Impact

No invariants are modified.  GTPD is additive.

| Invariant | Impact |
|---|---|
| INV-001 (Fail-Closed) | Not affected — GTPD never blocks |
| INV-002 (Receipt per Decision) | Not affected |
| INV-004 (AVM Tenant Isolation) | GTPD buffer is per-domain, consistent with tenant isolation model |

---

*OMNIX-GTPD-001 | ADR-152 | May 2026*
