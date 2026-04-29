# OMNIX Governance Flow — Transition Map
## Model-Certifiable → Human-Authorized
### Prepared for: Eduardo Monteiro

---

## Context

This document maps the concrete governance flow for a single decision segment in the Digital Asset Trading domain. It traces the exact point where the system transitions from **model-certifiable execution** to **human-authorized execution under partial representation**, and shows what each governance receipt captures in both conditions.

Live system metrics at time of mapping:
- Evaluation cycles: 660,581
- PQC-signed receipts: 161,258
- Decisions blocked: 11,302
- Capital preserved: 98.62%
- System uptime: Day 105

---

## Decision Under Review

```
Domain:      Digital Asset Trading
Asset:       BTC/USD
Operation:   ENTRY
Amount:      $50,000
Jurisdiction: UK (FCA-regulated)
```

---

## The 11 Checkpoints — Sequential, Fail-Closed

Every governance decision passes through the following gates in order. A block at any checkpoint stops execution immediately and issues a signed rejection receipt. No gate is skipped.

```
[01] CAG   — Context Admission Gate
[02] AV    — Authority Verification
[03] SC    — Scope Conformance
[04] RG    — Regime Gate (macro condition check)
[05] TIE   — Trajectory Invariant Enforcement
[06] RCG   — Risk Concentration Gate
[07] CB    — Circuit Breaker
[08] RL    — Risk Limits
[09] AVM   — Adaptive Validation Model (drift check)
[10] PQC   — Post-Quantum Cryptographic Signing
[11] BIND  — Execution Commit
```

---

## Zone A — Model-Certifiable Execution

**Condition:** All parameters fall within the domain baseline established at AVM calibration.

In this zone, the system operates with full representability. Each checkpoint evaluates against known, measured parameters. The AVM at checkpoint [09] compares current domain state against the calibrated snapshot. If drift index is below threshold, the action is certified and proceeds to cryptographic signing at [10].

**Example — IN-SCOPE execution (APPROVED):**

```json
{
  "receipt_id": "OMNIX-TRD-A1B2C3D4E5F6",
  "domain": "trading",
  "asset": "BTC/USD",
  "operation": "ENTRY",
  "amount": 50000,
  "decision": "APPROVED",
  "checkpoints_passed": 11,
  "avm_drift_index": 12.4,
  "avm_threshold": 35.0,
  "state_certification": "FULL — within calibrated parameter space",
  "human_signer": null,
  "pqc_signature": "CRYSTALS-Dilithium3 / NIST FIPS 204",
  "timestamp": "2026-04-29T15:42:00Z",
  "grounding_status": "CERTIFIED"
}
```

**What the receipt captures:** Full state certification. Drift is measured and within bounds. No human authority required. The system certifies that the state at bind matches the state the model represents.

---

## Zone B — The Transition Point

**Condition:** AVM drift index exceeds threshold before execution commits.

This is the STALE_BLOCK trigger. The domain state has shifted beyond what the calibrated snapshot can certify. The system does not proceed with model-authority. It does not assume the drift is safe. Execution stops at checkpoint [09].

**Example — STALE_BLOCK (drift exceeded):**

```json
{
  "receipt_id": "OMNIX-TRD-B7C8D9E0F1G2",
  "domain": "trading",
  "asset": "BTC/USD",
  "operation": "ENTRY",
  "amount": 50000,
  "decision": "STALE_BLOCK",
  "checkpoints_passed": 8,
  "blocked_at": "AVM [09]",
  "avm_drift_index": 43.2,
  "avm_threshold": 35.0,
  "snapshot_age": "14.2h",
  "state_certification": "FAILED — domain state outside certifiable parameter space",
  "human_signer": null,
  "escalation_required": true,
  "pqc_signature": "CRYSTALS-Dilithium3 / NIST FIPS 204",
  "timestamp": "2026-04-29T15:42:00Z",
  "grounding_status": "UNREPRESENTABLE — bind suspended"
}
```

**What the receipt captures:** The exact drift index, the threshold that was exceeded, the snapshot age, and the explicit declaration that the domain state is outside the certifiable parameter space. Execution is suspended. The receipt is signed and logged before any human involvement.

---

## Zone C — Human-Authorized Execution Under Partial Representation

**Condition:** Drift is detected, escalation is triggered, an authorized human reviews and overrides.

This is where your question sits precisely.

When human authority is invoked, the system does not recertify the state. It cannot — the model's certifiable space has already been exceeded. What the human authorizes is **action under acknowledged partial representation**. The receipt records this explicitly.

**Example — HUMAN_OVERRIDE (authorized under partial representation):**

```json
{
  "receipt_id": "OMNIX-TRD-C3D4E5F6G7H8",
  "domain": "trading",
  "asset": "BTC/USD",
  "operation": "ENTRY",
  "amount": 50000,
  "decision": "APPROVED",
  "checkpoints_passed": 11,
  "avm_drift_index": 43.2,
  "avm_threshold": 35.0,
  "state_certification": "PARTIAL — domain state outside certifiable space",
  "human_signer": {
    "authorized_by": "oversight_session_id:OS-2026-0429-001",
    "authority_level": "SENIOR_GOVERNANCE_OFFICER",
    "authorization_basis": "HUMAN_OVERRIDE_UNDER_PARTIAL_REPRESENTATION",
    "acknowledged_partial_state": true
  },
  "partial_representation_acknowledged": true,
  "consequence_threshold_check": "WITHIN_ACCEPTABLE_BOUNDARY",
  "pqc_signature": "CRYSTALS-Dilithium3 / NIST FIPS 204",
  "timestamp": "2026-04-29T15:47:00Z",
  "grounding_status": "PARTIAL — human accountability assigned, model certification not issued"
}
```

**What the receipt captures:**
- The state was NOT certified by the model
- A human explicitly acknowledged partial representation before authorizing
- The human's identity and authority level are bound to the receipt
- The consequence threshold check confirms the domain-specific risk boundary was evaluated
- `grounding_status: PARTIAL` is explicitly recorded — this is not hidden or normalized

---

## The Gap Your Question Identifies

Human authorization does not restore grounding. It assigns accountability for proceeding without it.

The receipt captures this distinction explicitly. The difference between Zone A and Zone C is not just a field value — it changes the entire accountability structure of the execution:

| Condition | State Certified | Human Required | Grounding Status |
|-----------|----------------|----------------|-----------------|
| Zone A — In-scope | YES | NO | CERTIFIED |
| Zone B — STALE_BLOCK | NO | BLOCKED | UNREPRESENTABLE |
| Zone C — Human Override | NO | YES | PARTIAL |

For domains where PARTIAL grounding is not acceptable, the system can be configured to refuse execution even with human authorization — making Zone B a hard stop with no Zone C pathway.

---

## What This Shows

The system does not silently pass execution through partial states. It records the partial state explicitly, assigns human accountability for the decision to proceed under that condition, and produces a signed receipt that distinguishes between certified and acknowledged-partial execution.

Whether that is sufficient grounding depends on the consequence boundary of the domain. The system makes that determination configurable — not assumed.

---

*OMNIX QUANTUM LTD — omnixquantum.net*
*April 2026*
