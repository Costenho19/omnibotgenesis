# ADR-092: Structural Admissibility Engine — Layer 0

**Status:** Accepted  
**Date:** 2026-04-20  
**Author:** Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD  
**Patent Reference:** OMNIX-PAT-2026-015  
**Related:** ADR-049 (Jurisdiction Gate CP-11), ADR-046 (Sharia Gate CP-6), ADR-053 (TIE), ADR-064 (AVM)

---

## Context

The OMNIX governance pipeline (Layers 1–3) operates as a runtime interception model: decisions are formulated and submitted to the pipeline, which evaluates and blocks inadmissible ones. This model has a fundamental architectural limitation: **the inadmissible decision exists as a system object before it is blocked.**

This means:
- If any checkpoint fails silently, the inadmissible decision proceeds
- Computational resources are allocated to represent and process requests that are definitionally inadmissible
- The governance guarantee depends on every checkpoint being operational

**The root cause:** There is no architectural layer that prevents inadmissible requests from being *constructed* in the first place.

---

## Decision

Introduce **Layer 0 — Structural Admissibility Engine (SAE)** to the OMNIX governance architecture.

Layer 0 is **constitutive**, not evaluative. It does not intercept existing objects — it determines what objects are allowed to *exist*. An `EvaluationRequest` object (the only valid input to Layer 1) can be constructed **exclusively** through the `StructuralAdmissibilityValidator.validate_and_construct()` method. Any attempt to construct one directly raises an unswallowable exception.

### Complete four-layer governance architecture:

```
Layer 0 — Structural Admissibility Engine (SAE)     ← THIS ADR
           ↓ (only EvaluationRequest objects pass)
Layer 1 — OMNIX Runtime Pipeline (CP-0 … CP-11 + TIE)
           ↓
Layer 2 — Trajectory Invariant Engine (TIE)
           ↓
Layer 3 — PQC Evidence & Receipt Layer
```

---

## Implementation

### Component A — Structural Constraint Schema (SCS)

Declarative constraint registry organized in 6 classes, evaluated in priority order:

| Priority | Class | Source |
|---|---|---|
| 1 | `SANCTIONS` | OFAC SDN, EU Consolidated, UN SC lists (from jurisdiction_gate.py ADR-068) |
| 2 | `JURISDICTION_ASSET` | Per-jurisdiction asset prohibitions (from jurisdiction_gate.JURISDICTION_RULES) |
| 3 | `JURISDICTION_OPERATION` | Per-jurisdiction operation restrictions (LEVERAGED, DERIVATIVES, SHORT) |
| 4 | `ETHICAL_SHARIA` | AAOIFI standards — active when ethical_flags=["SHARIA"] |
| 5 | `ETHICAL_ESG` | UN PRI / SFDR — active when ethical_flags=["ESG"] |
| 6 | `CLIENT_SPECIFIC` | Per-client overrides (further restrict only, never expand) |

### Component B — Structural Admissibility Validator (SAV)

```python
result = sav.validate_and_construct(proposed, mode=EvaluationMode.FAST_FAIL)
# Returns EvaluationRequest (admissible) or StructuredRejectionRecord (inadmissible)
```

Two evaluation modes:
- **FAST_FAIL** (default): halts at first violation — minimal latency
- **FULL_AUDIT**: collects all violations — maximum provenance for audit

### Component C — Zero-Bypass Boundary Enforcement (ZBE)

```python
class EvaluationRequest:
    _SAV_TOKEN = object()  # private sentinel, never exposed

    def __init__(self, _token, proposed, validated_at):
        if _token is not EvaluationRequest._SAV_TOKEN:
            raise StructuralAdmissibilityViolation(...)
        # ... immutable after construction
```

The sentinel object `_SAV_TOKEN` is only accessible within the module. External code cannot obtain it. Therefore external code **cannot construct** a valid `EvaluationRequest`. The construction attempt raises a non-swallowable exception.

After construction, `EvaluationRequest` is **immutable** — `__setattr__` raises `AttributeError`.

### Component D — Structured Rejection with Constraint Provenance (SRCP)

```json
{
  "admissibility": "INADMISSIBLE",
  "rejected_at": "LAYER_0_STRUCTURAL_ADMISSIBILITY",
  "audit_id": "A3F2B9C1D0E4",
  "layer_0_processing_ms": 0.8,
  "pipeline_entry": false,
  "violations": [{
    "constraint_id": "JA-UAE-XMR-001",
    "constraint_class": "JURISDICTION_ASSET",
    "description": "Asset XMR is prohibited in UAE jurisdiction",
    "regulatory_source": "UAE VARA Virtual Assets Regulations 2023",
    "input_fields": ["subject", "jurisdiction"],
    "input_values": {"subject": "XMR", "jurisdiction": "UAE"},
    "resolution": "XMR is not permitted in UAE. Select a compliant asset."
  }]
}
```

### Component E — Composable Cross-Domain Constraint Architecture (CCCA)

The `ConstraintRegistry` allows registering new constraint evaluators **without modifying SAV logic**. New domains, regulatory frameworks, or client-specific constraints are added via:

```python
sae.register_constraint(ConstraintClass.CLIENT_SPECIFIC, my_evaluator_fn)
sae.register_client_constraint("CLIENT_42", custom_restriction_fn)
```

---

## Domain-Agnostic Coverage

The SAE architecture is invariant across all OMNIX verticals. The `subject`, `operation`, `jurisdiction`, and `domain` fields are generic:

| Domain | subject | operation | jurisdiction |
|---|---|---|---|
| Financial Trading | asset symbol (BTC, XMR) | SPOT, LEVERAGED, DERIVATIVES | UAE, EU, US, UK... |
| Insurance | underwriting line | ISSUE, RENEW, EXCLUDE | US, UK, EU... |
| Medical AI | diagnostic category | DIAGNOSE, RECOMMEND, PRESCRIBE | FDA, CE, MHRA... |
| Real Estate | property type | BUY, MORTGAGE, SHORT_LET | UK, UAE, US... |
| Energy | energy source | TRADE, CONTRACT, STAKE | EU, AU, UK... |
| Autonomous Agent | action type | EXECUTE, OVERRIDE, ESCALATE | authorization scope |

---

## Integration with Layer 1

`external_evaluator.py` calls `sae.validate()` as the first step before any governance signal evaluation. Only `EvaluationRequest` objects produced by Layer 0 proceed to Layer 1.

```python
# external_evaluator.py — Layer 0 gate
sae = get_sae()
proposed = ProposedRequest(subject=asset, operation=op, jurisdiction=jur, ...)
layer0_result = sae.validate(proposed)
if isinstance(layer0_result, StructuredRejectionRecord):
    return layer0_result.to_dict()  # Never enters Layer 1
# else: layer0_result is EvaluationRequest — proceed to Layer 1
```

### Relationship with CP-11 (Jurisdiction Gate)

The SAE (Layer 0) and CP-11 (Layer 1, Jurisdiction Gate, ADR-049) are **complementary**:
- **SAE**: structural guarantee at *request construction time* — prohibits construction of inadmissible objects
- **CP-11**: runtime verification at *evaluation time* — validates conditions that may change after construction (e.g., updated sanctions lists)

CP-11 remains valuable for dynamic conditions. The SAE removes the static, known-at-construction-time violations from the runtime pipeline.

---

## Performance

Layer 0 processing time: **0.4–2.1ms per request** (in-memory constraint evaluation, FAST_FAIL mode).

Constraint tables are loaded from jurisdiction_gate and sharia_gate at first use and cached in-memory. Refresh of dynamic constraints (future: sanctions list updates) will be asynchronous per patent §VIII.

---

## Consequences

### Positive
- Inadmissible requests are **unrepresentable** — they cannot exist as system objects
- No Layer 1 component failure can allow an inadmissible request to proceed through Layer 0
- Full constraint provenance in every rejection — regulatory audit ready
- CCCA enables adding new regulatory frameworks without modifying SAV logic
- Performance overhead: < 2ms per request

### Negative
- Every request submitted to the governance pipeline must now construct a `ProposedRequest` before calling `sae.validate()`
- Integration requires all callers of Layer 1 to go through Layer 0 first
- The immutability of `EvaluationRequest` means post-construction enrichment requires wrapping patterns

### Constraints accepted
- `EvaluationRequest._SAV_TOKEN` is a module-level Python object — a determined attacker with code execution in the same process can access it via `EvaluationRequest._SAV_TOKEN`. The zero-bypass guarantee is architectural (no legitimate code path bypasses the SAV), not a security boundary against malicious in-process code.
- Dynamic sanctions list refresh is not yet implemented (in-memory tables loaded at startup) — subject to ADR-068 stale warning policy.

---

## Files

- `omnix_core/governance/structural_admissibility_engine.py` — SAE implementation
- `tests/test_structural_admissibility_engine.py` — Test suite
- `docs/ip/provisional_applications/family_15/SPECIFICATION_FAMILY15.md` — Patent specification
- `docs/ip/provisional_applications/pdf_exports/PRIORITY_1_URGENT/P1_004_F15_StructuralAdmissibilityEngine.pdf` — Patent PDF
