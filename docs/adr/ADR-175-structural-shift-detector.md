# ADR-175: Structural Shift Detector (SSD)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Supersedes:** None  
**Extends:** ADR-174 (AGVP) · ADR-120 (AVM Auto-Recalibration) · ADR-076 (AVM Signal Schema)  
**Related:** ADR-064 (AVM Core) · ADR-173 (DSPP) · ADR-174 (AGVP)  
**Implements:** `omnix_core/governance/assumption_validity_monitor.py` (SSD methods)  
**Priority Record:** OMNIX-PAR-2026-SSD-001 · May 20, 2026

---

## Context

### The Recalibration Topology Problem

The AVM (ADR-064/120) detects THAT a domain has drifted beyond its calibration envelope.
The AGVP (ADR-174) anticipates veto conditions before any governance request arrives.

Neither mechanism answers the question that determines whether recalibration is safe:

> *"Is the drift a sustained excursion from a stable calibration frame, or has the domain's
> signal topology itself changed — making the current frame potentially obsolete?"*

This distinction has direct operational consequences:

| Condition | Recalibration Policy | Rationale |
|---|---|---|
| **Sustained Drift** | Auto-recalibration safe | Same signals drive the score; thresholds remain conceptually valid; the domain has moved outside its calibrated range but the range is still meaningful |
| **Structural Shift** | Human review required | The composition of what is drifting has changed; the calibration frame may be entirely obsolete; auto-recalibration would embed unvalidated assumptions |

### The Observational Gap

This gap was identified through a LinkedIn technical exchange (May 2026) with Reza Zarei
(Creator of 3S Silent Authority System):

> *"¿Cómo detectas que un desplazamiento es estructural frente a un patrón de deriva
> sostenida antes de que se active la revisión?"*
>
> — Reza Zarei, 3S Silent Authority System (LinkedIn, May 2026)

The answer requires monitoring not just the magnitude of drift scores but the composition
of which signals dominate the drift across consecutive evaluation cycles.

### Why Existing Mechanisms Are Insufficient

| Mechanism | What it detects | What it misses |
|---|---|---|
| AVM.evaluate() drift_score | Magnitude of deviation from baseline | Which signals are driving the drift and whether this has changed |
| GTPD (ADR-064) | Adversarial threshold probing | Legitimate structural topology changes |
| AGV-INV-006 (ADR-174) | Active PVR blocks auto-recalibration | STRUCTURAL_SHIFT without active PVR |
| `_gtpd_drift_history` ring buffer | Score magnitudes over time | Component composition changes over time |

---

## Decision

### Component Rank Stability Index (CRSI)

ADR-175 establishes a new continuous monitoring capability within the AVM:
the **Structural Shift Detector (SSD)**, which computes the **Component Rank Stability
Index (CRSI)** after every `evaluate()` call.

**Algorithm — Position-Weighted Jaccard Overlap:**

```
For each evaluate() call for domain D:

1. Rank current drift_components descending by drift value → current_top_K
   (K = SSD_TOP_K_COMPONENTS = 3 by default)

2. For each history entry h in _component_history[D]:
   a. Rank h.components descending → hist_top_K
   b. position_weights = {rank_i: K - i for i in range(K)}
      (rank-1 = K, rank-2 = K-1, ..., rank-K = 1)
   c. overlap_h = Σ position_weights[i]
                  for each rank-i component in current_top_K
                  that also appears anywhere in hist_top_K
   d. CRSI_h = overlap_h / Σ(position_weights.values())

3. CRSI = mean(CRSI_h) over all history entries

4. Classification:
   CRSI >= 0.70 → STABLE
   0.50 <= CRSI < 0.70 → DRIFT_WITH_INSTABILITY
   CRSI < 0.50 (and >= SSD_MIN_CYCLES history) → STRUCTURAL_SHIFT
   < SSD_MIN_CYCLES history entries → INSUFFICIENT_DATA
```

**Why position-weighted Jaccard:**
- Rank-1 component carries maximum weight — the dominant driver of instability matters most
- Pure set overlap (unweighted Jaccard) would treat all components equally, missing the
  critical distinction between the #1 driver changing vs the #3 driver changing
- Position weights produce a continuous stability metric, not a binary classification

### StructuralShiftReport

Every `AVMResult` now carries a `structural_shift_report` field containing a
`StructuralShiftReport` with:

| Field | Description |
|---|---|
| `ssd_id` | Unique identifier (format: `SSD-{10HEX}`) |
| `domain` | Domain evaluated |
| `shift_class` | `INSUFFICIENT_DATA` \| `STABLE` \| `DRIFT_WITH_INSTABILITY` \| `STRUCTURAL_SHIFT` |
| `crsi` | Component Rank Stability Index (0–1, 4 decimal places) |
| `cycles_analyzed` | Number of history entries used in computation |
| `dominant_components_current` | Top-K components by drift this cycle |
| `dominant_components_baseline` | Consensus top-K across history (≥50% frequency) |
| `emerged_components` | In current top-K but not in baseline — new drift drivers |
| `receded_components` | In baseline top-K but not current — quieted drift drivers |
| `detected_at` | ISO 8601 UTC timestamp |

### Integration Points

**1. `AVMResult` (every evaluate() call)**
`structural_shift_report` is always populated when drift_components are non-empty
and AVM is enabled. Both DRIFT_BLOCK and PASS results carry the report.

**2. `ProactiveVetoReceipt` (AGVP Watchdog cycles)**
The `structural_shift_class` field carries the SSD verdict into every PVR emitted.
This makes the structural shift classification part of the PQC-signed forensic receipt.

**3. `auto_recalibrate_stale_domains()` (SSD-INV-001)**
Before executing any auto-recalibration, the AVM checks for STRUCTURAL_SHIFT.
If detected, recalibration is blocked and the domain is flagged for human review.
This guard is independent of and additive to AGV-INV-006.

---

## Invariants

### SSD-INV-001: Structural Shift Blocks Auto-Recalibration

`auto_recalibrate_stale_domains()` MUST skip any domain for which
`_detect_structural_shift()` returns `shift_class == "STRUCTURAL_SHIFT"`.

Rationale: A structural shift means the current calibration frame may be entirely
obsolete. Anchoring a new baseline to current signals when the topology has changed
embeds unvalidated assumptions into the governance baseline.

This invariant is independent of and additive to AGV-INV-006 (which blocks
recalibration when an active PVR exists). A domain can have STRUCTURAL_SHIFT
without an active PVR (if drift has recovered but topology has shifted), and
in that case AGV-INV-006 would not block — SSD-INV-001 does.

**Verification:** `tests/test_ssd.py::TestSSDInvariant001`

### SSD-INV-002: Component History Ring Buffer Is Append-Only

The `_component_history` ring buffer MUST be append-only within its size window.
No history entry may be modified or deleted selectively — only evicted by the
ring buffer size limit (FIFO). This preserves the chronological integrity of
the component topology record.

**Verification:** `tests/test_ssd.py::TestSSDInvariant002`

### SSD-INV-003: STRUCTURAL_SHIFT Requires Minimum History

`_detect_structural_shift()` MUST return `shift_class == "INSUFFICIENT_DATA"`
when the domain has fewer than `SSD_MIN_CYCLES` (default: 5) history entries.
A single-cycle or low-history STRUCTURAL_SHIFT verdict is statistically unreliable
and would trigger false recalibration blocks on cold start.

**Verification:** `tests/test_ssd.py::TestSSDInvariant003`

---

## Configuration

| Parameter | Default | Description |
|---|---|---|
| `SSD_TOP_K_COMPONENTS` | `3` | Number of top drift components compared per cycle |
| `SSD_MIN_CYCLES` | `5` | Minimum history entries before STRUCTURAL_SHIFT verdict |
| `SSD_STRUCTURAL_THRESHOLD` | `0.50` | CRSI below this → STRUCTURAL_SHIFT |
| `SSD_INSTABILITY_THRESHOLD` | `0.70` | CRSI below this → DRIFT_WITH_INSTABILITY |
| `_SSD_HISTORY_SIZE` | `20` | Maximum component snapshots retained per domain |

---

## Consequences

### Positive

- **Precise recalibration policy:** Auto-recalibration only proceeds when the signal
  topology is stable. Structural changes require human attestation before any baseline
  update — preventing incoherent calibration frames.

- **Forensic topology record:** `StructuralShiftReport` provides an evidence trail of
  when and how the domain's drift composition changed. `emerged_components` and
  `receded_components` identify the specific signals that drove the topology change.

- **PQC-attested structural evidence:** `structural_shift_class` is embedded in every
  PVR — the topology classification is part of the PQC-signed, DB-persisted artifact.

- **Richer AVMResult:** Every governance receipt now carries a structural shift report,
  enabling auditors to distinguish between drift excursions and topology changes in
  the historical evidence record.

### Constraints

- CRSI requires `SSD_MIN_CYCLES` (5) evaluation cycles before producing a
  STRUCTURAL_SHIFT verdict. This is intentional (SSD-INV-003) and means the
  first 5 cycles for a domain produce INSUFFICIENT_DATA — not a false STABLE.

- The ring buffer is in-memory and process-local. In multi-dyno deployments,
  each process maintains independent component history. This is acceptable because
  structural shift detection is a per-process heuristic that informs the
  recalibration guard — the actual recalibration block is enforced by SSD-INV-001
  which runs on the process that would execute the recalibration.

---

## Relationship to ADR-174 (AGVP)

ADR-175 is an orthogonal extension to ADR-174:

| Layer | What it detects | When it acts |
|---|---|---|
| AGVP (ADR-174) | Drift magnitude exceeds threshold proactively | Before any request — PVR blocks all requests |
| SSD (ADR-175) | Drift topology has structurally changed | During auto-recalibration — blocks baseline update |

Both layers add independent guards. A domain can have:
- Active PVR (AGV-INV-006 blocks recalibration) + STRUCTURAL_SHIFT (SSD-INV-001 also blocks)
- Active PVR + STABLE (only AGV-INV-006 blocks)
- No active PVR + STRUCTURAL_SHIFT (only SSD-INV-001 blocks)
- No active PVR + STABLE (neither blocks — normal operation)

---

## RFC Foundation

ADR-175 contributes to the RFC-ATF-4 foundation alongside:

| ADR | Component |
|---|---|
| ADR-171 | Semantic Governance Interoperability Protocol (SGIP) |
| ADR-172 | ATF Open Receipt Schema (ATORS) |
| ADR-173 | Dynamic Semantic Portability Protocol (DSPP) |
| ADR-174 | Anticipatory Governance Veto Protocol (AGVP) |
| **ADR-175** | **Structural Shift Detector (SSD)** |

---

*Harold Nunes — OMNIX QUANTUM LTD — May 2026*  
*Priority Record: OMNIX-PAR-2026-SSD-001*
