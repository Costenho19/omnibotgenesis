# ADR-140 — Commit-Time Admissibility Gate (CTAG)

**Status:** ACCEPTED (v1.0)
**Date:** 2026-05-07
**Author:** OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo
**Module:** MOD-016
**Scope:** `omnix_core/governance/commit_time_gate.py` · `omnix_core/governance/unified_control_layer.py`

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| v1.0 | 2026-05-07 | Initial implementation — CommitTimeAdmissibilityGate, CTAGResult, drift verdicts VALID/DRIFTED/REVOKED/INDETERMINATE |

---

## 1. Context and Problem Statement

OMNIX issues PQC-signed receipts at decision time (Layer 3, ADR-096). These
receipts are cryptographically valid — their signatures cannot be forged or
tampered with after issuance.

However, in persistent orchestration contexts (autonomous agents, robotics,
energy infrastructure, multi-step financial workflows), a meaningful time gap
may exist between *decision time* and *execution time*. During that gap,
operational conditions may drift:

- Market liquidity may collapse.
- A counterparty's authority may be revoked.
- Signal integrity may degrade.
- Trajectory may destabilize.

**The PQC receipt remains valid. The operational assumptions do not.**

This creates an execution-boundary gap: a governance artifact that is
cryptographically authentic may authorize a consequence whose preconditions
no longer hold.

> *"Does OMNIX treat admissibility as a continuously re-evaluated execution
> condition, or primarily as a point-in-time verification state attached to
> the artifact itself?"*
> — Akhilesh Warik, 2026-05-07

**ADR-140 closes this gap.** OMNIX treats admissibility as **both**:

(a) A **point-in-time cryptographic receipt** (Layer 3, PQC — immutable, verifiable)
(b) A **continuously re-evaluable execution condition** (Layer 5, CTAG — evaluated at commit)

---

## 2. Decision

Implement a **Commit-Time Admissibility Gate (CTAG)** as Layer 5 in the UDCL
pipeline (after SBE, Layer 4) that:

1. **Accepts** the current `standing_margin` (from SBE, Layer 4) and the
   original `ControlReceipt` dict (from the original approval).
2. **Computes** `drift_delta = current_margin − original_margin`.
3. **Returns** one of four verdicts with `commit_authorized` flag.
4. **Revokes** authorization if `drift_delta < −0.15` (hard threshold).
5. **Flags** drift if `−0.15 ≤ drift_delta < −0.05` (caution threshold).
6. Is **opt-in** — callers must pass `ctag_enabled=True` to the UDCL.

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
    ├── [Layer 4]   SBE  — Standing Boundary Engine              (ADR-139)
    └── [Layer 5]   CTAG — Commit-Time Admissibility Gate [opt-in] ← ADR-140
          └── drift_delta computed; commit_authorized flag returned
```

### 3.2 Drift Verdict Mapping

| drift_delta | Verdict | commit_authorized |
|---|---|---|
| ≥ −0.05 | `VALID` | `true` |
| −0.15 to −0.05 | `DRIFTED` | `true` (with caveat) |
| < −0.15 | `REVOKED` | `false` |
| Baseline unavailable | `INDETERMINATE` | `true` (advisory) |

`drift_delta = current_standing_margin − original_standing_margin`

Negative delta = conditions degraded since approval.
Positive delta = conditions improved since approval.

### 3.3 Thresholds

```
REVOCATION_DRIFT_THRESHOLD = 0.15   # 15-point drop → revocation
CAUTION_DRIFT_THRESHOLD    = 0.05   # 5-point drop  → caution / DRIFTED
```

These thresholds are domain-independent. Future ADRs may introduce
domain-specific threshold overrides.

---

## 4. CTAGResult

```json
{
  "ctag_id":             "CTAG-A1B2C3",
  "verdict":             "DRIFTED",
  "commit_authorized":   true,
  "original_margin":     0.18,
  "current_margin":      0.10,
  "drift_delta":         -0.08,
  "original_decision":   "APPROVED",
  "original_control_id": "UDCL-9F2E1A4B",
  "elapsed_seconds":     312.4,
  "resolution_note":     "Admissibility DRIFTED. Drift delta -0.0800 exceeds caution threshold -0.05 but within revocation tolerance. Commit authorized with monitoring caveat.",
  "latency_ms":          0.41,
  "adr":                 "ADR-140"
}
```

---

## 5. Fail-Closed Policy

| Condition | Behavior |
|---|---|
| CTAG raises unhandled exception | `REVOKED`, `commit_authorized=false` — fail-closed |
| `original_control` not provided | `INDETERMINATE`, `commit_authorized=true` — advisory pass |
| `drift_delta < −REVOCATION_DRIFT_THRESHOLD` | `REVOKED` — commit refused |

---

## 6. OMNIX Admissibility Model (ADR-140 Formal Statement)

> **OMNIX treats admissibility as a two-layer property:**
>
> **Layer A — Point-in-Time Receipt (PQC, ADR-096)**
> A Dilithium-3 signed receipt is issued at decision time. This receipt is
> cryptographically immutable: its authenticity can be verified at any future
> point via the public key and the `/verify` endpoint. The receipt represents
> the OMNIX governance position *at the moment of evaluation*.
>
> **Layer B — Continuous Execution Condition (SBE + CTAG, ADR-139/140)**
> Admissibility is also a runtime property: the Standing Boundary Engine
> continuously derives a numeric standing margin from live pillar data. The
> Commit-Time Admissibility Gate compares the current margin to the original
> baseline at the moment an irreversible consequence is about to be committed.
> If conditions have drifted beyond threshold, the original authorization is
> revoked — even though the PQC receipt remains cryptographically valid.
>
> **This dual-layer model resolves the execution-boundary distinction:**
> receipts are immutable artifacts of governance history; commit-time
> re-evaluation is the live enforcement gate that prevents stale approvals
> from authorizing consequences in changed conditions.

---

## 7. Integration with UDCL (ADR-138)

When `ctag_enabled=True`:
- CTAG runs after SBE (Layer 4).
- `original_control` must be passed in `metadata["ctag_original_control"]`.
- If CTAG returns `REVOKED`, the final decision is overridden to `BLOCKED`
  with `blocking_pillar="ctag"`.
- `ctag_result` is embedded in `ControlReceipt`.

When `ctag_enabled=False` (default):
- CTAG is not run. `ctag_result` is `null` in `ControlReceipt`.
- Point-in-time receipt remains the sole governance artifact.

---

## 8. Regulatory Alignment

| Standard | Clause | How CTAG Addresses It |
|---|---|---|
| EU AI Act Art. 9 | Continuous risk management | Formal commit-time re-evaluation gate for all irreversible consequences |
| NIST AI RMF MANAGE 2.2 | Runtime monitoring of AI decisions | CTAG provides structured drift measurement at execution boundary |
| MiFID II | Pre-trade risk controls | Commit authorization revocable if market conditions drift |
| ISO 42001 §6.1 | AI risk treatment across lifecycle | Admissibility evaluated at both decision-time and execution-time |

---

## 9. ADR Dependencies

| ADR | Module | Relation |
|---|---|---|
| ADR-096 | PQC Receipt | Point-in-time receipt baseline — CTAG does not replace, complements it |
| ADR-138 | UDCL | CTAG integrated as Layer 5 — ControlReceipt extended with ctag_result |
| ADR-139 | SBE | CTAG consumes `standing_margin` produced by SBE (Layer 4) |
