# ADR-066: Epistemic Transparency Layer Extension — score=0 on Failsafe/Disabled

**Status:** Accepted  
**Date:** 2026-04-09  
**Author:** Harold Nunes (OMNIX QUANTUM LTD)  
**Companion ADRs:** ADR-067 (AML Frequency), ADR-068 (OFAC Lifecycle)

---

## Context

Post-ADR-065 audit revealed that six components returned `score=100` on disabled or error (failsafe) paths:

| Component | Field | Old value | Problem |
|-----------|-------|-----------|---------|
| TIE (_pass_through) | `trajectory_score` | 100.0 | Disabled TIE reported perfect trajectory health |
| SIV (failsafe) | `score` | 100.0 | Exception during validation returned perfect integrity |
| FTI (failsafe) | `implied_score` | 100.0 | Module error returned perfect trajectory implication |
| AML (disabled) | `aml_score` | 100.0 | Gate not evaluated returned perfect AML compliance |
| Sharia (disabled) | `sharia_score` | 100.0 | Gate not evaluated returned perfect Sharia compliance |
| Jurisdiction (disabled) | `compliance_score` | 100.0 | Gate not evaluated returned perfect jurisdictional compliance |

This is "manufactured trust" — confidence scores fabricated without underlying evidence. For a Decision Governance Infrastructure whose value proposition is the integrity of the audit trail, this constitutes a fundamental epistemic failure.

### The Principle

> **score=100 is an assertion**. It claims: "This component evaluated the input and found it excellent." When the component did not evaluate anything, that assertion is false. Silence (absence of evaluation) is not perfect quality.

---

## Decision

**All failsafe and disabled paths must emit score=0, not score=100.**

Additional required fields:

- **TIE**: `pass_through_reason` field on `TIEResult` distinguishes `TIE_DISABLED`, `TIE_BLOCKED_BYPASS`, and `TIE_FAILSAFE` paths.
- **SIV**: `reason` field on `SIVResult` populated only on failsafe paths, format: `SIV_FAILSAFE: score=0 reflects module error, not data quality — {exc}`.
- **FTI**: `reason` field on `FTIResult` populated only on failsafe paths, format: `FTI_FAILSAFE: score=0 reflects module error, not trajectory health — {exc}`.
- **AML, Sharia, Jurisdiction**: `evaluation_state` field added to results — `"DISABLED"`, `"FAILSAFE"`, or `"EVALUATED"`. Allows dashboards to distinguish `score=0-real` from `score=0-not-evaluated`.

---

## Consequences

### Positive

1. **PQC receipt integrity** — Receipts no longer contain scores that claim evaluation-level confidence without evidence.
2. **Dashboard auditability** — `evaluation_state` field enables operations to identify which gates were actually active vs. bypassed.
3. **Regulatory defensibility** — In a regulatory review, score=0 with `evaluation_state=DISABLED` is honest. score=100 with disabled gate is not.
4. **Investor trust** — Pre-seed narrative ("we are the governance infrastructure") requires that the infrastructure not lie about its own state.

### Negative / Mitigations

- **Pipeline behavior unchanged**: All failsafe/disabled paths continue to emit `pass_through=True` / `admissible=True`. score=0 does not block the pipeline.
- **Downstream reads `admissible`, not `score`**: No checkpoint veto logic relies on these scores for pass/fail decisions. Confirmed by ADR-065 architecture review.
- **Old tests updated**: 2 tests (`test_pass_through_has_max_score`, `test_pass_through_score_is_100`) were asserting the old incorrect behavior. Renamed and corrected to `test_pass_through_has_zero_score_adr066` and `test_pass_through_score_is_zero_adr066`.

---

## Implementation

### Files Modified

- `omnix_core/governance/trajectory_invariant_engine.py` — TIE `_pass_through()`: `trajectory_score=0.0`; `TIEResult` dataclass: add `pass_through_reason` field; `result_to_dict()`: include `pass_through_reason`.
- `omnix_core/data/signal_integrity_validator.py` — SIV failsafe block: `score=0.0`; `SIVResult` dataclass: add `reason` field; `to_dict()`: include `reason` if present.
- `omnix_core/temporal/forward_trajectory.py` — FTI failsafe block: `implied_score=0.0`; `FTIResult` dataclass: add `reason` field; `to_dict()`: include `reason` if present.
- `omnix_core/governance/aml_gate.py` — disabled path: `aml_score=0.0`, `evaluation_state="DISABLED"`; evaluated path: `evaluation_state="EVALUATED"`.
- `omnix_core/governance/sharia_gate.py` — same pattern as AML.
- `omnix_core/governance/jurisdiction_gate.py` — same pattern as AML.

### Tests Added

- `tests/test_compliance_gates.py` — `TestTIEEpistemicTransparency` (5 tests), `TestAMLGateEpistemicTransparency` (5), `TestShariaGateEpistemicTransparency` (4), `TestJurisdictionGateEpistemicTransparency` (8 incl. ADR-068)
- `tests/test_signal_integrity_validator.py` — `TestSIVEpistemicTransparency` (5 tests)
- `tests/test_forward_trajectory.py` — `TestFTIEpistemicTransparency` (5 tests)

**Test result:** 161/161 (full compliance + SIV + FTI suite), 35/35 new ADR-066/067/068 tests.

---

## Alternatives Considered

**Keep score=100 but add `evaluated=False` flag** — Rejected. The score field is the primary signal consumers read. A secondary boolean requires every consumer to check two fields. score=0 is self-explanatory and aligns with the principle of least surprise.

**Emit `score=null`** — Rejected. The existing `JurisdictionVetoResult` etc. use typed floats. Null introduces optional type complexity throughout the pipeline. score=0 with `evaluation_state` field is sufficient and simpler.
