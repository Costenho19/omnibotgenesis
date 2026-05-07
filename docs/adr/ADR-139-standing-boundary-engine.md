# ADR-139 — Standing Boundary Engine (SBE)

**Status:** ACCEPTED (v1.0)
**Date:** 2026-05-07
**Author:** OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo
**Module:** MOD-015
**Scope:** `omnix_core/governance/standing_boundary_engine.py` · `omnix_core/governance/unified_control_layer.py`

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| v1.0 | 2026-05-07 | Initial implementation — StandingBoundaryEngine, StandingVector, SBEResult, 6 extended decision classes, NARROW scope reduction, QUARANTINE token, REBOUND posture |

---

## 1. Context and Problem Statement

OMNIX governance decisions prior to ADR-139 produced three possible outcomes:
`APPROVED`, `BLOCKED`, or `HOLD`. This binary-plus-hold vocabulary is
insufficient for institutional orchestration contexts where:

**Gap 1: No partial admission**
An evaluation may be *nearly* admissible — signal integrity is high, authority
is valid, but exposure headroom is marginal. The correct response is not full
approval or full block, but **scope reduction**: permit a smaller consequence
that falls within the boundary. Without NARROW, callers must choose between
over-approving or over-blocking.

**Gap 2: No payload isolation**
When signal integrity is compromised but other governance dimensions are sound,
the correct response is to **isolate the problematic payload** rather than
refuse the entire evaluation. Without QUARANTINE, legitimate institutional
operations are unnecessarily blocked.

**Gap 3: No posture restoration**
In persistent orchestration (robotics, autonomous agents, energy infrastructure),
a BLOCKED decision with no recovery path leaves the system in an undefined
posture. The correct response is **REBOUND** — return to the last admissible
state and document the rebound target for audit.

**Gap 4: No numeric margin**
Institutional consumers need to know not just *whether* a decision was
approved, but *by how much*. A standing margin of +0.02 signals operational
fragility even on an APPROVED decision. No numeric margin was previously
available.

---

## 2. Decision

Implement a **Standing Boundary Engine (SBE)** as Layer 4 in the UDCL pipeline
(after PQC Receipt, Layer 3) that:

1. **Computes** an 8-dimension Standing Vector from data already collected by
   the UDCL pipeline — no re-evaluation of signals.
2. **Derives** a numeric Standing Margin: `margin = weighted_score − 0.65`.
3. **Maps** the margin to one of six extended decision classes.
4. **Returns** `standing_margin`, `standing_vector`, and `sbe_result` in
   every `ControlReceipt`.
5. **Never overrides** a prior BLOCKED or HOLD — SBE only refines APPROVED.

---

## 3. Architecture

### 3.1 Layer Position

```
POST /api/governance/control/evaluate
    │
    ├── [Layer 0]   SAE  — Structural Admissibility Engine       (ADR-092)
    ├── [Layer 0b]  SPG  — State Provenance Guard                (ADR-133)
    ├── [Layer 0c]  CBG  — Conditional Bind Gate [opt-in]        (ADR-135)
    ├── [Layer 1-2] CP   — 11-Checkpoint Pipeline + TIE          (ADR-028/053)
    ├── [Layer 3]   PQC  — Cryptographic Receipt                 (ADR-096)
    └── [Layer 4]   SBE  — Standing Boundary Engine              ← ADR-139
          └── standing_margin + extended decision class added to ControlReceipt
```

### 3.2 Standing Vector Dimensions

| # | Dimension | Weight | Min Threshold | Source |
|---|---|---|---|---|
| 1 | `authority_score` | 0.18 | 0.50 | SAE admission status |
| 2 | `policy_compliance` | 0.18 | 0.60 | Checkpoint pass rate |
| 3 | `signal_integrity` | 0.16 | 0.40 | SPG lineage_singularity |
| 4 | `capacity_margin` | 0.14 | 0.20 | Score-derived exposure headroom |
| 5 | `coherence_score` | 0.12 | 0.30 | Veto chain length |
| 6 | `trajectory_stability` | 0.10 | 0.20 | TIE stability score |
| 7 | `execution_readiness` | 0.07 | 0.30 | CBG pass + zero blocked checkpoints |
| 8 | `debt_load_inverted` | 0.05 | 0.10 | 1 − (blocked_cps / total_cps) |

Weights sum to 1.0. `standing_margin = weighted_score − 0.65`.

### 3.3 Decision Band Mapping

| Margin Range | Decision | Behavior |
|---|---|---|
| > +0.20 | `APPROVED` | Full execution authorized — clear headroom |
| +0.05 to +0.20 | `APPROVED` | Full execution authorized — narrow headroom flagged |
| +0.01 to +0.05 | `NARROW` | Scope reduced before bind |
| −0.05 to +0.01 | `QUARANTINE` | Payload isolated, bind suspended |
| −0.15 to −0.05 | `REBOUND` | Return to last admissible posture |
| < −0.15 | `BLOCKED` | Hard refusal |

**Override conditions (independent of margin):**
- `signal_integrity < 0.40` → `QUARANTINE` regardless of margin
- `trajectory_stability < 0.10` → `REBOUND` regardless of margin

### 3.4 NARROW Scope Reduction

Scope reduction factor: `1 − (margin / 0.05) × 0.5`

| Margin | Reduction |
|---|---|
| 0.01 | 90% |
| 0.025 | 75% |
| 0.04 | 60% |

Original scope values are multiplied by `(1 − reduction_factor)`.
The `narrowed_scope` dict is returned in `SBEResult` and embedded in `ControlReceipt`.

### 3.5 QUARANTINE Token

A deterministic token `QT-{16 hex}` is generated via SHA-256 of
`{sbe_id}:{asset}:{domain}:{timestamp}`. This token is returned to the caller
for payload tracking and later release review.

### 3.6 REBOUND Target

If a prior admissible `control_id` is known (passed via `rebound_target_id`),
it is embedded in `SBEResult.rebound_target_id` and included in the
`ControlReceipt` for downstream recovery orchestration.

---

## 4. ControlReceipt Extensions

```json
{
  "decision":        "NARROW",
  "standing_margin": 0.0312,
  "sbe_result": {
    "sbe_id":            "SBE-A1B2C3",
    "decision":          "NARROW",
    "standing_margin":   0.0312,
    "standing_vector": {
      "authority_score":      1.0,
      "policy_compliance":    0.91,
      "signal_integrity":     0.87,
      "capacity_margin":      0.72,
      "coherence_score":      0.85,
      "trajectory_stability": 0.68,
      "execution_readiness":  1.0,
      "debt_load_inverted":   1.0
    },
    "failed_dimensions": [],
    "narrowed_scope": {
      "quantity":       30000,
      "original_scope": {"quantity": 100000},
      "scope_reduction": "70%"
    },
    "quarantine_token":  null,
    "rebound_target_id": null,
    "resolution_note": "Standing margin +0.0312 — marginal. Scope reduced. Execution permitted at reduced scope only."
  }
}
```

---

## 5. Fail-Closed Policy

| Condition | Behavior |
|---|---|
| SBE raises unhandled exception | `BLOCKED`, `standing_margin = null`, `error` logged |
| Prior decision is `BLOCKED` or `HOLD` | SBE honors prior decision — no override |
| `signal_integrity < 0.40` | `QUARANTINE` — integrity override regardless of margin |
| `trajectory_stability < 0.10` | `REBOUND` — trajectory override regardless of margin |

---

## 6. Extended Decision Class Vocabulary

```
APPROVED   — positive margin; full execution authorized
NARROW     — marginal positive; scope reduced before bind
QUARANTINE — signal integrity failure or near-zero margin; payload isolated
REBOUND    — margin negative or trajectory degraded; return to last admissible
HOLD       — margin indeterminate; supervisor escalation required
BLOCKED    — margin below absolute floor; hard refusal
```

These six classes supersede the prior three-class vocabulary
(`APPROVED | HOLD | BLOCKED`) for all UDCL evaluations from ADR-139 onward.
Backward compatibility is maintained: `APPROVED` and `BLOCKED` retain their
prior semantics; `HOLD` is unchanged.

---

## 7. Regulatory Alignment

| Standard | Clause | How SBE Addresses It |
|---|---|---|
| EU AI Act Art. 9 | Risk management, quantified risk levels | `standing_margin` provides numeric risk quantification per evaluation |
| NIST AI RMF GOVERN 1.1 | Documented governance mechanisms | 8-dimension vector + 6 decision classes formally documented |
| MiFID II | Pre-trade risk controls | NARROW enforces position-level scope reduction at governance layer |
| ISO 42001 | AI risk assessment | Standing vector provides dimension-level risk transparency |

---

## 8. ADR Dependencies

| ADR | Module | Relation |
|---|---|---|
| ADR-028 | 11-Checkpoint Pipeline | Checkpoint pass rate → `policy_compliance` dimension |
| ADR-053 | TIE | TIE stability score → `trajectory_stability` dimension |
| ADR-092 | SAE | Admission status → `authority_score` dimension |
| ADR-133 | SPG | Lineage singularity → `signal_integrity` dimension |
| ADR-135 | CBG | Bind result → `execution_readiness` dimension |
| ADR-138 | UDCL | SBE integrated as Layer 4 — ControlReceipt extended |
| ADR-140 | CTAG | Uses `standing_margin` from SBE as commit-time baseline |
