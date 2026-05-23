# ADR-182: Constraint Conformance Signal (CCS)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Supersedes:** None  
**Extends:** ADR-174 (AGVP) · ADR-173 (DSPP) · ADR-181 (BAR)  
**Related:** ADR-181 (BAR) · ADR-183 (CTCHC) · RFC-ATF-6  
**Priority Record:** OMNIX-PAR-2026-CCS-001 · May 2026

---

## Context

### The Conformance Observability Problem

The Anticipatory Governance Veto Protocol (ADR-174, RFC-ATF-4) is designed to issue Proactive Veto Receipts (PVRs) before governance violations occur. The AGVP watchdog monitors observable signals and issues a PVR when any signal crosses a degradation threshold.

As of RFC-ATF-5, the AGVP input space covers:

- **CES score trajectory** — structural governance signal
- **Fragmentation score trend** — authority distribution signal
- **Semantic drift index** — DSPP cross-domain semantic signal

Missing: **a signal measuring whether the agent's actual behavioral outputs conform to the constraint boundaries in its governing receipt**.

This is Gap_COP (Conformance Observability Problem): behavioral drift toward constraint violation has no observable signal feeding the AGVP. Without such a signal, the AGVP cannot issue anticipatory vetoes for behavioral degradation trajectories.

### Why Existing ML Monitoring Solutions Are Insufficient

Existing ML monitoring platforms (Arize, WhyLabs, Evidently AI) monitor AI outputs against **separately configured policies**. Three critical problems:

1. **The monitoring policy is separate from the authorization.** In OMNIX, the constraint vector is embedded in the governing receipt — PQC-signed and immutable. Existing ML monitors reference a separate configuration. There is no cryptographic binding between the monitoring policy and the authorization.

2. **Monitoring output is telemetry, not governance evidence.** An Arize dashboard produces operational alerts. An OMNIX governance artifact produces a PQC-signed record admissible in regulatory proceedings.

3. **No AGVP integration.** Existing ML monitoring platforms generate alerts to human operators. They do not trigger governance-native anticipatory veto receipt issuance.

The CCS resolves all three problems by providing a governance-native conformance signal: computed from the governing receipt's constraint vector, embedded in the PQC-sealed BAR, and integrated with the AGVP watchdog.

---

## Decision

### Establish the Constraint Conformance Signal (CCS)

ADR-182 establishes the **Constraint Conformance Signal (CCS)** as the behavioral conformance measurement artifact of the BEV layer (RFC-ATF-6). The CCS is a multi-component numerical score in [0.0, 100.0] computed per execution turn, measuring how closely the turn's behavioral output conforms to the constraint vector of its governing receipt.

### Four CCS Components

| Component | Max | Deduction | Measures |
|---|---|---|---|
| Output Boundary Score (OBS) | 40 | -10 per boundary violation | Output within declared domain and not in prohibited classes |
| Constraint Satisfaction Score (CSS) | 30 | -8 per constraint failure | Explicit constraints in CV satisfied |
| Semantic Drift Score (SDS) | 20 | Proportional to cosine distance from authorized profile | Semantic proximity to authorized behavior |
| Authority Alignment Score (AAS) | 10 | -10 if scope exceeded | Agent acted within declared authority_scope |

**CCS Score = OBS + CSS + SDS + AAS ∈ [0.0, 100.0]**

All components are non-negative (BEV-INV-011). A component can reach 0 but never go negative — preventing a high-violation component from being masked by negative offsets in another component.

### CCS Verdicts

| Score | Verdict | Response |
|---|---|---|
| ≥ 90.0 | CONFORMANT | Normal operation |
| 70.0 – 89.9 | DRIFTING | AGVP PVR issuance triggered |
| 50.0 – 69.9 | BREACH | Escalation required |
| < 50.0 | VIOLATION | HALT propagation initiated |
| -1.0 | NO_DATA | CCS_ENABLED=false or REDACTED mode |

### AGVP Integration

When a BAR is persisted with `ccs_verdict ∈ {DRIFTING, BREACH, VIOLATION}`, the BEV runtime MUST submit a PVR issuance request to the AGVP watchdog within `BEV_AGVP_TRIGGER_TIMEOUT_MS` (default: 500ms).

PVR payload fields:
```json
{
  "trigger_source":          "CCS_BEV",
  "trigger_session_id":      "<session_id>",
  "trigger_bar_id":          "<bar_id>",
  "trigger_ccs_score":       74.5,
  "trigger_ccs_verdict":     "DRIFTING",
  "trigger_turn_index":      8,
  "governing_receipt_id":    "<receipt_id>",
  "veto_type":               "BEHAVIORAL_CONFORMANCE_DEGRADATION",
  "anticipatory_risk_level": "MONITORING"
}
```

For VIOLATION: `anticipatory_risk_level = "HALT"` and HALT propagation is initiated per RFC-ATF-2 §7.3.

### CCS Embedding in BAR

The CCS is **not stored in a separate table at the turn level**. It is embedded in the BAR before the BAR is sealed. This design ensures:

1. **Tamper-evidence:** modifying `ccs_score` after BAR sealing invalidates `pqc_signature` (BEV-INV-013)
2. **Co-location:** a BAR is a complete behavioral evidence artifact — output hash, conformance measurement, chain link — in one document
3. **Offline verifiability:** any verifier with the BAR JSON can verify the CCS score without OMNIX infrastructure

The separate `atf_constraint_conformance_signals` table (§ Database Schema below) is a **projection** of BAR data for efficient history queries.

---

## Architecture

### CCS Computation Order

```
1. CV extracted from session context (constant per session)
2. OBS: apply prohibited_classes and output_domain checks → violations count
3. CSS: evaluate domain_specific_constraints → failures count
4. SDS: compute cosine distance from authorized profile (if model configured)
5. AAS: check capability invocations against authority_scope
6. ccs_score = OBS + CSS + SDS + AAS
7. ccs_verdict = derive_verdict(ccs_score)
8. Embed in BAR before content_hash_bar computation
```

Steps 1-7 MUST complete before BAR `content_hash_bar` is computed (BEV-INV-013).

### Threshold Configuration

```
CCS_CONFORMANT_THRESHOLD  default: 90.0  production floor: 85.0
CCS_DRIFTING_THRESHOLD    default: 70.0  production floor: 60.0
CCS_BREACH_THRESHOLD      default: 50.0  production floor: 40.0
BEV_AGVP_TRIGGER_TIMEOUT  default: 500ms never exceed: 5000ms
BEV_HALT_TIMEOUT_MS       default: 100ms never exceed: 2000ms
```

**Security note:** CCS thresholds are behavioral security parameters. Lowering thresholds below production floors reduces governance coverage and MUST be documented with a security exception.

---

## Database Schema

### atf_constraint_conformance_signals (projection table)

```sql
CREATE TABLE IF NOT EXISTS atf_constraint_conformance_signals (
    ccs_id                        VARCHAR(64)      PRIMARY KEY,
    bar_id                        VARCHAR(64)      NOT NULL
                                      REFERENCES atf_behavioral_anchor_records(bar_id)
                                      ON DELETE RESTRICT,
    session_id                    VARCHAR(64)      NOT NULL,
    governing_receipt_id          VARCHAR(128)     NOT NULL,
    turn_index                    INTEGER          NOT NULL,
    ccs_score                     DOUBLE PRECISION NOT NULL,
    ccs_verdict                   VARCHAR(16)      NOT NULL,
    output_boundary_score         DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    constraint_satisfaction_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    semantic_drift_score          DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    authority_alignment_score     DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    boundary_violation_count      INTEGER          NOT NULL DEFAULT 0,
    constraint_failure_count      INTEGER          NOT NULL DEFAULT 0,
    drift_magnitude               DOUBLE PRECISION,
    agvp_pvr_triggered            BOOLEAN          NOT NULL DEFAULT FALSE,
    agvp_pvr_id                   VARCHAR(64),
    halt_triggered                BOOLEAN          NOT NULL DEFAULT FALSE,
    computed_at_ns                BIGINT           NOT NULL DEFAULT 0,
    created_at                    TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);
```

**Indexes:**
- `idx_ccs_session_id` — session CCS history
- `idx_ccs_verdict` — filter by verdict
- `idx_ccs_governing_receipt_id` — receipt-level CCS history
- `idx_ccs_ccs_score` — range queries for audit
- `idx_ccs_bar_id` — join to BAR

---

## Invariant Impact

| Invariant | Statement |
|---|---|
| BEV-INV-008 | Mandatory CCS per BAR (when CCS_ENABLED) |
| BEV-INV-009 | ccs_score ∈ [0.0, 100.0] |
| BEV-INV-010 | DRIFTING triggers AGVP PVR within BEV_AGVP_TRIGGER_TIMEOUT_MS |
| BEV-INV-011 | All four CCS components non-negative |
| BEV-INV-012 | VIOLATION triggers HALT propagation within BEV_HALT_TIMEOUT_MS |
| BEV-INV-013 | CCS fields covered by content_hash_bar (tamper-evident) |

---

## Formal Verification

Z3 SMT proof BEV-FVS-003 verifies CCS score bounds:

```python
from z3 import Real, Or, Solver, And, unsat
obs, css, sds, aas = [Real(x) for x in ["obs","css","sds","aas"]]
s = Solver()
s.add(obs >= 0, obs <= 40)
s.add(css >= 0, css <= 30)
s.add(sds >= 0, sds <= 20)
s.add(And(Or(aas == 0, aas == 10)))
ccs = obs + css + sds + aas
s.add(Or(ccs < 0, ccs > 100))
assert s.check() == unsat  # no violation of [0.0, 100.0] possible
```

Z3 SMT proof BEV-FVS-004 verifies component non-negativity:
```python
from z3 import Real, Not, Solver, If, unsat
base, ded = Real("base"), Real("ded")
s = Solver()
s.add(base == 40, ded >= 0)
result = If(base - ded >= 0, base - ded, 0)
s.add(Not(result >= 0))
assert s.check() == unsat  # max(0, base-ded) >= 0 always
```

---

## Consequences

### Positive

- **Completes the AGVP input space:** behavioral conformance degradation now feeds the AGVP watchdog, enabling anticipatory behavioral vetoes
- **Governance-native:** measurement references the PQC-signed governing receipt's CV — the policy and the measurement are cryptographically coupled
- **Tamper-evident:** CCS is embedded in the PQC-sealed BAR; post-hoc CCS score modification is detectable
- **Formally verified:** bounds [0.0, 100.0] and component non-negativity proven with Z3 (BEV-FVS-003, BEV-FVS-004)
- **Regulatory alignment:** provides NIST AI RMF MEASURE 2.6 ongoing monitoring evidence in governance-native form

### Negative / Trade-offs

- **OBS and CSS require implementation-specific detectors:** the definitions of "boundary violation" and "constraint failure" depend on domain-specific logic that must be implemented per deployment.
- **SDS requires embedding model:** cosine distance computation requires a configured embedding model. When absent, SDS defaults to 20.0 (no deduction) — meaning the SDS component does not contribute to detection.
- **Per-turn computation cost:** CCS adds ~1-5ms per turn depending on complexity of CV and availability of embedding model.

### Not Permitted

- `CCS_CONFORMANT_THRESHOLD` below 80.0 in production (security exception required below 85.0)
- Modifying `ccs_score` or `ccs_components` after `content_hash_bar` computation
- Setting `AVM_AUTO_APPROVE=true` to bypass CCS-triggered AGVP escalation

---

## Files

| File | Purpose |
|---|---|
| `omnix_core/bev/constraint_conformance_signal.py` | CCS computation engine |
| `omnix_core/bev/agvp_ccs_integration.py` | CCS→AGVP trigger bridge |
| `tests/test_constraint_conformance_signal.py` | Full test suite |
| `docs/adr/ADR-182-constraint-conformance-signal.md` | This document |
| `docs/standards/RFC-ATF-6.md` | Normative specification |

---

*OMNIX-CCS-001 | ADR-182 | May 2026*
