# PROVISIONAL PATENT APPLICATION
## OMNIX-PAT-2026-015

**Title:** STRUCTURAL ADMISSIBILITY ENGINE FOR AUTOMATED DECISION GOVERNANCE SYSTEMS WITH PRE-PIPELINE SCHEMA VALIDATION, ENUMERATED CONSTRAINT ENCODING, AND ZERO-BYPASS BOUNDARY ENFORCEMENT

**Inventor:** Harold Alberto Nunes Rodelo
**Applicant:** OMNIX QUANTUM LTD
**Filing Basis:** 35 U.S.C. § 111(b)
**Entity Status:** Micro Entity
**Date Prepared:** April 19, 2026
**Date of Filing:** April 19, 2026
**Related Applications:** OMNIX-PAT-2026-001 (Governance Control Architecture), OMNIX-PAT-2026-011 (Jurisdiction Compliance Gate), OMNIX-PAT-2026-014 (Bidirectional Temporal Admissibility System)

---

## FIELD OF THE INVENTION

The present invention relates to automated decision governance systems, and more particularly to a pre-pipeline structural admissibility layer that enforces decision admissibility at the point of input construction rather than at runtime evaluation — making structurally inadmissible decision requests unrepresentable as valid system objects. The Structural Admissibility Engine (SAE) constitutes a new architectural stratum — Layer 0 — that precedes and gates all downstream governance processing, providing a zero-bypass guarantee that no inadmissible request can enter the evaluation pipeline regardless of the operational state of any downstream component.

---

## BACKGROUND

### I. THE FUNDAMENTAL INADEQUACY OF RUNTIME INTERCEPTION IN GOVERNANCE PIPELINES

Contemporary automated decision governance systems — including multi-checkpoint sequential pipelines, rule-based policy engines, and AI-driven compliance systems — share a common structural assumption: that governance is enforced by intercepting and blocking invalid decisions after those decisions have been formulated and submitted for evaluation. This runtime interception model has a fundamental and irremediable architectural deficiency: the invalid decision exists as a system object before it is blocked.

The consequences of this architecture extend beyond the theoretical:

**1.1 Bypass Through Component Failure.** In a runtime interception model, every blocking component must be operational and correctly implemented for the governance guarantee to hold. If a governance checkpoint fails silently, is disabled for maintenance, encounters an unhandled exception, or is bypassed by a misconfigured pipeline, the invalid decision that it was designed to block may proceed to execution. The governance guarantee is only as strong as the weakest component in the chain.

**1.2 Latent Invalid State Generation.** Because the invalid decision is formulated as a system object before any checkpoint evaluates it, the system must allocate computational resources to represent, transmit, and process a request that is definitionally inadmissible. This generates latent invalid state throughout the system — in memory, in logs, in audit trails — even when the request is ultimately blocked.

**1.3 Governance Dependency on Execution Order.** Runtime interception pipelines depend on correct execution ordering to guarantee governance. A checkpoint that evaluates jurisdictional compliance must execute before a checkpoint that generates an execution commitment. Any inversion of execution order — whether through code defect, configuration error, or concurrent execution — may permit an inadmissible decision to receive an execution commitment before the blocking checkpoint evaluates it.

**1.4 Absence of a Constitutive Boundary.** In existing systems, the boundary between admissible and inadmissible requests is not constitutive — it does not determine what can exist in the system. It is merely evaluative — it determines what happens to things that already exist. There is no architectural mechanism that prevents the construction and submission of a request for an operation that is categorically prohibited by jurisdiction, asset class, operation type, regulatory classification, or ethical constraint.

**1.5 No Constraint Provenance in Rejection.** When a runtime interception system blocks a request, the rejection is typically expressed as an error code or a binary BLOCKED decision. The system does not identify the specific structural constraint that the request violated, the regulatory or policy source from which that constraint derives, or the combination of input fields that jointly produced the inadmissibility. This impedes regulatory audit, client communication, and system debugging.

### II. PRIOR ART AND ITS LIMITATIONS

**2.1 Runtime Checkpoint Pipelines.** The prior art in automated decision governance consists primarily of sequential checkpoint pipelines in which each checkpoint evaluates the decision against a specific criterion and produces a pass or block determination. These systems, including the OMNIX governance pipeline described in related application OMNIX-PAT-2026-001, operate entirely within the runtime interception model. They are powerful and comprehensive, but they do not prevent invalid requests from being formulated.

**2.2 Schema Validation in API Systems.** Web API systems commonly employ input schema validation using frameworks such as JSON Schema, OpenAPI, or programming language validation libraries. These systems validate that input data conforms to a structural specification — for example, that a field named "asset" contains a string, or that a numeric field falls within a specified range. However, these systems do not encode regulatory, jurisdictional, or ethical constraints at the schema level. They validate data structure, not decision admissibility.

**2.3 Type Systems in Programming Languages.** Programming language type systems, particularly in statically typed functional languages, have been used to enforce invariants at the type level — a practice described in the programming language theory literature as "making illegal states unrepresentable." This principle has been applied to data modeling in software applications but has not been systematically applied as an architectural layer for automated decision governance systems with regulatory, jurisdictional, and ethical constraint encoding.

**2.4 Access Control and Authorization Systems.** Authorization frameworks (OAuth, RBAC, ABAC) control whether an entity is permitted to submit a request. They operate at the identity and permission level, not at the decision content level. An authorized user may still submit a decision request that is structurally inadmissible — for example, requesting an operation on a prohibited asset in a restricted jurisdiction. Authorization systems do not evaluate decision content admissibility.

No prior art combines: (a) schema-level structural validation; (b) regulatory, jurisdictional, and ethical constraint encoding; (c) zero-bypass architectural guarantee; (d) structured rejection with constraint provenance; and (e) composable cross-domain constraint architecture — as a unified pre-pipeline governance layer for automated decision systems.

---

## SUMMARY OF THE INVENTION

The present invention provides a Structural Admissibility Engine (SAE) comprising:

**Component A — Structural Constraint Schema (SCS):** A declarative, machine-readable specification of all constraints that determine whether a proposed decision request is structurally admissible. Constraints are organized into six classes evaluated in priority order: (i) Sanctions Constraints, encoding assets and entities appearing on OFAC, EU, or UN sanctions lists, which are unconditionally prohibited in all jurisdictions and for all clients; (ii) Jurisdiction-Asset Constraints, encoding which asset classes are permissible within each regulatory jurisdiction; (iii) Jurisdiction-Operation Constraints, encoding which operation types are permissible within each regulatory jurisdiction; (iv) Ethical Sharia Constraints, encoding asset and operation restrictions derived from AAOIFI Sharia compliance standards; (v) Ethical ESG Constraints, encoding asset restrictions derived from ESG screening criteria per UN PRI and SFDR; and (vi) Client-Specific Constraints, encoding per-client overrides and restrictions negotiated at client onboarding.

**Component B — Structural Admissibility Validator (SAV):** A pre-construction validator that evaluates a proposed decision request against the Structural Constraint Schema before constructing the EvaluationRequest object that would represent that request in the governance pipeline. If the proposed request violates any constraint in any constraint class, the SAV does not construct the EvaluationRequest object. The invalid request is rejected at the boundary — it never becomes a valid system object.

**Component C — Zero-Bypass Boundary Enforcement (ZBE):** An architectural guarantee that the SAV is the sole path through which a proposed decision request may be converted into an EvaluationRequest object. There is no code path, configuration, or operational state that permits the construction of an EvaluationRequest object without passing through the SAV. The zero-bypass property is enforced by making EvaluationRequest construction private to the SAV — external code may submit proposed requests to the SAV but may not directly construct EvaluationRequest objects.

**Component D — Structured Rejection with Constraint Provenance (SRCP):** A rejection response format that, when the SAV determines that a proposed request is structurally inadmissible, returns a machine-readable record identifying: the specific constraint violated; the constraint class to which it belongs; the regulatory or policy source from which the constraint derives; the specific input fields that jointly produced the violation; and a human-readable explanation suitable for client communication.

**Component E — Composable Cross-Domain Constraint Architecture (CCCA):** A constraint composition mechanism that allows constraints from multiple domains and sources to be combined into a single SAV evaluation without runtime branching logic. A proposed request is evaluated against all applicable constraints simultaneously, and the SAV produces a unified admissibility determination with provenance for all violated constraints.

---

## DETAILED DESCRIPTION OF THE INVENTION

### I. LAYER 0: THE STRUCTURAL ADMISSIBILITY ENGINE IN THE FOUR-LAYER GOVERNANCE ARCHITECTURE

The present invention introduces Layer 0 to the governance architecture described in related application OMNIX-PAT-2026-001. The complete four-layer architecture is:

**Layer 0 — Structural Admissibility Engine (present invention):** Determines whether a proposed decision request is structurally representable as a valid system object. Only structurally admissible requests proceed. Structurally inadmissible requests are rejected before any downstream processing occurs.

**Layer 1 — OMNIX Runtime Pipeline:** A sequential, multi-checkpoint pipeline (CP-0 through CP-11, TIE) that evaluates the decision against runtime conditions including signal quality, probabilistic confidence, risk exposure, temporal coherence, and jurisdictional compliance. Described in OMNIX-PAT-2026-001.

**Layer 2 — Trajectory Invariant Engine:** A trajectory-aware evaluation module that assesses the proposed decision against the historical and projected behavioral trajectory of the system. Described in OMNIX-PAT-2026-014.

**Layer 3 — Evidence and Receipt Layer:** A post-evaluation layer that generates a cryptographically sealed, PQC-signed decision receipt constituting an immutable audit record. Described in OMNIX-PAT-2026-001.

The key architectural property of Layer 0 is that it is constitutive, not evaluative. Layers 1, 2, and 3 evaluate requests that exist. Layer 0 determines what can exist.

### II. THE STRUCTURAL CONSTRAINT SCHEMA (SCS)

The Structural Constraint Schema is a declarative specification of admissibility constraints organized in a hierarchical structure:

#### 2.1 Jurisdiction-Asset Constraints

For each regulatory jurisdiction J and each asset class A, the SCS specifies:

```
JA_CONSTRAINT(J, A) ∈ {PERMITTED, PROHIBITED, CONDITIONAL}
```

Where CONDITIONAL indicates that the combination is permitted only when additional conditions C are satisfied (for example, the client holds a specific regulatory license or the position size is below a specified threshold).

Jurisdictions include but are not limited to: UAE (VARA framework), EU (MiCA regulation), US (FinCEN/SEC/CFTC framework), UK (FCA framework), GCC (unified VARA-aligned framework), SG (MAS framework), and GLOBAL (no jurisdiction-specific restrictions beyond sanctions).

Asset class restrictions are encoded at multiple levels of specificity:
- Category level: e.g., PRIVACY_COIN category is PROHIBITED in US jurisdiction
- Individual asset level: e.g., XMR (Monero) is PROHIBITED in UAE, EU, US, UK, GCC, SG jurisdictions
- Sanctioned asset list: assets appearing on OFAC, EU, or UN sanctions lists are PROHIBITED in all jurisdictions

#### 2.2 Jurisdiction-Operation Constraints

For each regulatory jurisdiction J and each operation type O, the SCS specifies:

```
JO_CONSTRAINT(J, O) ∈ {PERMITTED, PROHIBITED, CONDITIONAL}
```

Operation types include: SPOT (spot purchase or sale), LEVERAGED (leveraged position), DERIVATIVES (derivative contract), SHORT (short sale), STAKING (asset staking), LENDING (asset lending).

For example:
- JO_CONSTRAINT(UAE, LEVERAGED) = PROHIBITED
- JO_CONSTRAINT(EU, DERIVATIVES) = PERMITTED
- JO_CONSTRAINT(US, DERIVATIVES) = CONDITIONAL (requires CFTC authorization)
- JO_CONSTRAINT(UK, LEVERAGED) = PROHIBITED (retail clients)

#### 2.3 Ethical Compliance Constraints

Ethical compliance constraints encode restrictions derived from recognized ethical frameworks:

**Sharia Compliance Constraints:** For each asset class A and operation type O, a Sharia compliance determination S(A, O) ∈ {HALAL, HARAM, MASHBOOH} is encoded. Assets classified as HARAM or operations classified as HARAM are PROHIBITED for clients with Sharia compliance requirements. Described in detail in related application OMNIX-PAT-2026-003.

**ESG Constraints:** For clients with ESG restrictions, asset classes that fail specified ESG screening criteria are PROHIBITED. ESG screening criteria are configurable per client.

**Sanctions Constraints:** Assets appearing on active OFAC, EU, or UN sanctions lists are PROHIBITED for all clients regardless of other constraints.

#### 2.4 Client-Specific Constraints

Client-specific constraints are negotiated at client onboarding and stored in a per-client constraint record:

```
CLIENT_CONSTRAINT(client_id, field, value) → {PERMITTED, PROHIBITED}
```

Client-specific constraints may further restrict but may not expand the structural admissibility determined by jurisdiction, asset class, operation, and ethical constraints. A client may prohibit additional assets or operations beyond the default constraint set, but may not permit assets or operations that are prohibited by default.

### III. THE STRUCTURAL ADMISSIBILITY VALIDATOR (SAV)

The SAV is the evaluation engine of the Structural Admissibility Engine. It operates as follows:

#### 3.1 Pre-Construction Evaluation

When external code submits a proposed decision request P to the SAV, the SAV performs the following evaluation before constructing any EvaluationRequest object:

```
ADMISSIBILITY(P) = ⋂ { C_i(P) : C_i ∈ SCS applicable to P }
```

Where C_i(P) is the admissibility determination of constraint C_i applied to proposed request P. If any applicable constraint determines P to be PROHIBITED, ADMISSIBILITY(P) = INADMISSIBLE.

If ADMISSIBILITY(P) = INADMISSIBLE, the SAV does not construct an EvaluationRequest object. It returns a Structured Rejection Record (described in Section V) and halts.

If ADMISSIBILITY(P) = ADMISSIBLE, the SAV constructs and returns an EvaluationRequest object. This object is the only valid input to Layer 1 of the governance pipeline.

#### 3.2 Constraint Evaluation Order

Constraints are evaluated in the following priority order, with evaluation halting at the first INADMISSIBLE determination (fast-fail mode, default) or continuing to collect all violations (full-audit mode, configurable):

1. **Sanctions** (highest priority — unconditional PROHIBITED in all jurisdictions; OFAC SDN, EU Consolidated List, UN Security Council)
2. **Jurisdiction-Asset** (per-jurisdiction asset class prohibitions)
3. **Jurisdiction-Operation** (per-jurisdiction operation type restrictions: LEVERAGED, DERIVATIVES, SHORT)
4. **Ethical Sharia** (AAOIFI-derived HALAL/HARAM determinations — active only when `ethical_flags` includes `"SHARIA"`)
5. **Ethical ESG** (UN PRI / SFDR screening — active only when `ethical_flags` includes `"ESG"`)
6. **Client-Specific** (per-client onboarding constraints — further restrict only, never expand)

In full-audit mode, all violated constraints are collected and reported in the Structured Rejection Record.

#### 3.3 Composite Condition Evaluation

For CONDITIONAL constraints, the SAV evaluates the associated conditions against the proposed request metadata:

```
CONDITIONAL_ADMISSIBILITY(J, A, O, metadata) = 
  JA_CONSTRAINT(J, A) = CONDITIONAL 
  AND JO_CONSTRAINT(J, O) = CONDITIONAL
  AND ∀ condition c ∈ CONDITIONS(J, A, O): c(metadata) = TRUE
```

If any condition is not satisfied, the CONDITIONAL determination resolves to PROHIBITED.

### IV. ZERO-BYPASS BOUNDARY ENFORCEMENT (ZBE)

The zero-bypass property is the defining architectural characteristic that distinguishes the SAE from prior art runtime interception systems.

#### 4.1 Structural Enforcement

In the implementation of the present invention, the EvaluationRequest type is defined with a private constructor enforced by a module-level sentinel token (`_SAV_TOKEN`). The only public interface for constructing an EvaluationRequest object is the `StructuralAdmissibilityEngine.validate()` method, which performs the full constraint evaluation described in Section III before constructing the object. The EvaluationRequest object is immutable after construction — any attempt to modify its attributes after initialization raises an immediate exception.

```python
class EvaluationRequest:
    """
    Structural admissibility-enforced evaluation request.
    Only constructible via StructuralAdmissibilityEngine.validate().
    Direct instantiation raises StructuralAdmissibilityViolation.
    Immutable after construction — __setattr__ raises AttributeError.
    """
    _SAV_TOKEN = object()  # Private module-level sentinel

    def __init__(self, _token, proposed: "ProposedRequest", validated_at: str):
        if _token is not EvaluationRequest._SAV_TOKEN:
            raise StructuralAdmissibilityViolation(
                "EvaluationRequest must be constructed via "
                "StructuralAdmissibilityEngine.validate(). "
                "Direct instantiation is prohibited."
            )
        object.__setattr__(self, "subject",      proposed.subject)
        object.__setattr__(self, "operation",    proposed.operation)
        object.__setattr__(self, "jurisdiction", proposed.jurisdiction)
        object.__setattr__(self, "domain",       proposed.domain)
        object.__setattr__(self, "client_id",    proposed.client_id)
        object.__setattr__(self, "ethical_flags",proposed.ethical_flags)
        object.__setattr__(self, "metadata",     proposed.metadata)
        object.__setattr__(self, "validated_at", validated_at)
        object.__setattr__(self, "evaluation_id", _new_evaluation_id())

    def __setattr__(self, name, value):
        raise AttributeError(
            "EvaluationRequest is immutable after construction."
        )

class StructuralAdmissibilityEngine:
    def validate(
        self,
        proposed: "ProposedRequest | dict",
        mode: EvaluationMode = EvaluationMode.FAST_FAIL,
    ) -> "EvaluationRequest | StructuredRejectionRecord":
        if isinstance(proposed, dict):
            proposed = ProposedRequest(**proposed)
        violations = self._evaluate_all_constraints(proposed, mode)
        if violations:
            return StructuredRejectionRecord(proposed=proposed, violations=violations)
        return EvaluationRequest(
            _token=EvaluationRequest._SAV_TOKEN,
            proposed=proposed,
            validated_at=_utcnow_iso(),
        )
```

#### 4.2 Architectural Guarantee

The zero-bypass property guarantees that:

(a) No EvaluationRequest object can exist that has not passed through the full SAV constraint evaluation.
(b) No code path, configuration flag, or operational condition can produce an EvaluationRequest object that bypasses the SAV.
(c) Any attempt to directly construct an EvaluationRequest object without the SAV raises an immediate, unhandled exception that halts the construction attempt.

This is categorically different from a runtime interception model, where a failed, disabled, or bypassed checkpoint can silently allow an inadmissible request to proceed. In the SAE model, silence is impossible: an inadmissible request either raises an exception or is never constructed.

### V. STRUCTURED REJECTION WITH CONSTRAINT PROVENANCE (SRCP)

When the SAV determines that a proposed request is structurally inadmissible, it returns a Structured Rejection Record with the following fields:

```json
{
  "admissibility": "INADMISSIBLE",
  "rejected_at": "LAYER_0_STRUCTURAL_ADMISSIBILITY",
  "audit_id": "A3F2B9C1D0E4",
  "violations": [
    {
      "constraint_class": "JURISDICTION_ASSET",
      "constraint_id": "JA-UAE-XMR-001",
      "description": "Asset XMR (Monero) is prohibited in UAE jurisdiction under VARA regulations",
      "regulatory_source": "UAE VARA Virtual Assets and Related Activities Regulations 2023, Schedule 1",
      "input_fields": ["subject", "jurisdiction"],
      "input_values": {"subject": "XMR", "jurisdiction": "UAE"},
      "resolution": "Select a VARA-compliant asset for UAE jurisdiction. Permitted categories: BTC, ETH, ADA, DOT (spot only)."
    }
  ],
  "pipeline_entry": false,
  "layer_0_processing_ms": 0.8
}
```

The machine-readable format of the SRCP serves three purposes:

**Regulatory Audit:** The constraint provenance record constitutes a complete, machine-readable audit trail of why the decision was rejected at the structural level, which regulatory source mandated the constraint, and which input fields jointly produced the violation.

**Client Communication:** The resolution field provides actionable guidance to the client system or operator on how to reformulate the request in a structurally admissible form.

**System Debugging:** The constraint_id and input_fields fields enable precise identification of constraint configuration errors during system development and maintenance.

### VI. COMPOSABLE CROSS-DOMAIN CONSTRAINT ARCHITECTURE (CCCA)

The CCCA enables constraints from multiple domains to be evaluated simultaneously without runtime branching logic:

#### 6.1 Constraint Registry

All constraints are registered in a unified Constraint Registry at system initialization. The registry is organized by constraint class and indexed by the fields each constraint evaluates:

```
REGISTRY = {
  "JURISDICTION_ASSET": {JA_constraints...},
  "JURISDICTION_OPERATION": {JO_constraints...},
  "ETHICAL_SHARIA": {ES_constraints...},
  "ETHICAL_ESG": {EE_constraints...},
  "SANCTIONS": {SN_constraints...},
  "CLIENT_SPECIFIC": {CS_constraints...}
}
```

#### 6.2 Constraint Composition

For a proposed request P, the SAV retrieves all applicable constraints from the registry based on the fields present in P (asset, operation, jurisdiction, client_id, ethical_flags), and evaluates them as a conjunction:

```
ADMISSIBILITY(P) = ADMISSIBLE iff 
  ∀ C ∈ APPLICABLE_CONSTRAINTS(P): C(P) ≠ PROHIBITED
```

New constraint classes (for example, carbon footprint constraints, age restriction constraints, or novel regulatory framework constraints) can be added to the registry without modifying the SAV evaluation logic. The CCCA is therefore extensible by constraint addition, not by code modification.

### VII. INTERACTION WITH LAYER 1: THE OMNIX RUNTIME PIPELINE

The SAE operates as the exclusive gateway to Layer 1. The Layer 1 pipeline (CP-0 through CP-11, TIE) accepts only EvaluationRequest objects as input. Because EvaluationRequest objects can only be constructed by the SAV, and the SAV only constructs objects for structurally admissible requests, the Layer 1 pipeline is constitutively protected from inadmissible inputs.

This has an important architectural consequence for Layer 1: the runtime checkpoint CP-11 (Jurisdiction Compliance Gate, OMNIX-PAT-2026-011) — which currently performs jurisdictional validation at runtime — becomes partially redundant for the constraint classes covered by the SAE. The Layer 1 CP-11 checkpoint continues to provide value as a runtime verification of jurisdiction-specific conditions that may change between the time of request construction and the time of execution (for example, a jurisdiction's sanction list update that occurred after request construction). The SAE and CP-11 are complementary rather than duplicative: the SAE provides structural guarantee at construction time, and CP-11 provides runtime verification at execution time.

### VIII. MULTI-DOMAIN APPLICABILITY

The SAE is domain-agnostic. The constraint classes described in this specification are illustrated using financial trading (asset, operation, jurisdiction) as the primary domain, but the SAE architecture applies without modification to all domains supported by the OMNIX governance platform:

**Financial Trading:** Asset + Operation + Jurisdiction constraints as described.

**Insurance Underwriting:** Underwriting line + Coverage type + Regulatory jurisdiction + Ethical constraints (e.g., FHEO anti-discrimination constraints in US housing insurance).

**Medical AI:** Diagnostic category + Treatment recommendation type + Regulatory approval status (FDA, CE Mark, MHRA) + Clinical indication constraints.

**Real Estate:** Property type + Transaction type + Jurisdiction + Anti-money-laundering structural constraints.

**Energy:** Energy source type + Contract type + Grid operator jurisdiction + Carbon accounting constraints.

**Autonomous Agents:** Agent action type + Operating domain + Authorization scope + Safety envelope constraints.

In each domain, the SCS encodes the domain-specific constraints, and the SAV enforces them at request construction time. The Layer 0 architecture is invariant across domains.

### IX. PERFORMANCE CHARACTERISTICS

The SAE is designed for minimal latency impact on the overall governance pipeline:

**Constraint evaluation** operates on in-memory constraint tables populated at system initialization. No database query is required for standard constraint evaluation. Constraint evaluation time is O(k) where k is the number of applicable constraints for the given request fields.

**Constraint table refresh** for dynamic constraints (sanctions lists, client-specific overrides) is performed asynchronously on a configurable refresh interval, with in-memory tables updated atomically to avoid request-time latency.

**Fast-fail mode** (default): evaluation halts at the first PROHIBITED determination, minimizing processing time for inadmissible requests.

**Full-audit mode** (configurable): evaluation collects all violations before returning, maximizing constraint provenance completeness at the cost of additional processing time.

Observed Layer 0 processing time: 0.4–2.1 milliseconds per request (in-memory constraint evaluation, fast-fail mode).

---

## CLAIMS

1. A computer-implemented Structural Admissibility Engine for automated decision governance systems, comprising:
   a. a Structural Constraint Schema encoding admissibility constraints organized into at least two constraint classes including jurisdiction-asset constraints and jurisdiction-operation constraints;
   b. a Structural Admissibility Validator configured to evaluate a proposed decision request against the Structural Constraint Schema before constructing a valid EvaluationRequest object representing the proposed decision request;
   c. wherein the Structural Admissibility Validator constructs the EvaluationRequest object only if the proposed decision request satisfies all applicable constraints in the Structural Constraint Schema; and
   d. wherein the Structural Admissibility Validator does not construct the EvaluationRequest object if the proposed decision request violates any applicable constraint in the Structural Constraint Schema.

2. The Structural Admissibility Engine of claim 1, wherein the EvaluationRequest object type comprises a private constructor accessible exclusively through the Structural Admissibility Validator, enforcing a zero-bypass property whereby no code path external to the Structural Admissibility Validator can construct a valid EvaluationRequest object.

3. The Structural Admissibility Engine of claim 1, wherein the Structural Constraint Schema further comprises ethical compliance constraints derived from at least one of: Sharia compliance criteria, environmental, social, and governance (ESG) screening criteria, and international sanctions lists.

4. The Structural Admissibility Engine of claim 1, wherein the Structural Constraint Schema further comprises client-specific constraints encoding per-client admissibility restrictions, and wherein client-specific constraints may further restrict but may not expand the admissibility determined by jurisdiction-asset constraints and jurisdiction-operation constraints.

5. The Structural Admissibility Engine of claim 1, wherein when the Structural Admissibility Validator determines that a proposed decision request is inadmissible, the Validator returns a Structured Rejection Record comprising: a constraint identifier identifying the violated constraint; a constraint class identifier; a regulatory source citation identifying the regulatory or policy source from which the constraint derives; an identification of the specific input fields jointly responsible for the violation; and a resolution guidance field.

6. The Structural Admissibility Engine of claim 1, wherein the Structural Admissibility Validator supports a composable cross-domain constraint architecture in which constraints from multiple constraint classes are evaluated simultaneously through a unified Constraint Registry, and wherein new constraint classes are added to the registry without modification to the Structural Admissibility Validator evaluation logic.

7. The Structural Admissibility Engine of claim 1, wherein the Structural Admissibility Engine constitutes Layer 0 of a four-layer governance architecture, and wherein Layer 0 gates a Layer 1 runtime checkpoint pipeline that accepts only EvaluationRequest objects as input, ensuring that the Layer 1 pipeline cannot receive structurally inadmissible inputs regardless of the operational state of any Layer 1 checkpoint.

8. The Structural Admissibility Engine of claim 1, wherein constraint evaluation operates on in-memory constraint tables populated at system initialization, and wherein constraint table refresh for dynamic constraint classes is performed asynchronously on a configurable refresh interval with atomic in-memory table updates.

9. The Structural Admissibility Engine of claim 7, wherein the four-layer governance architecture further comprises Layer 2, a trajectory invariant enforcement layer evaluating the proposed decision against the historical and projected behavioral trajectory of the governance system; and Layer 3, a post-evaluation evidence and cryptographic receipt layer generating a post-quantum cryptographically sealed audit record.

10. A method for enforcing structural admissibility in automated decision governance systems comprising:
    a. receiving a proposed decision request comprising at least an asset identifier, an operation type, and a jurisdictional context;
    b. evaluating the proposed decision request against a Structural Constraint Schema encoding at least jurisdiction-asset constraints and jurisdiction-operation constraints, the evaluation occurring prior to constructing any system object representing the proposed decision request;
    c. if the proposed decision request satisfies all applicable constraints, constructing an EvaluationRequest object via a Structural Admissibility Validator and forwarding the EvaluationRequest object to a downstream governance pipeline;
    d. if the proposed decision request violates any applicable constraint, returning a Structured Rejection Record identifying the violated constraints with constraint provenance and not constructing any EvaluationRequest object; and
    e. enforcing a zero-bypass property by restricting EvaluationRequest object construction to the Structural Admissibility Validator.

---

## ABSTRACT

A Structural Admissibility Engine (SAE) for automated decision governance systems enforces decision admissibility at the point of input construction rather than at runtime evaluation, making structurally inadmissible decision requests unrepresentable as valid system objects. The SAE comprises a Structural Constraint Schema encoding regulatory, jurisdictional, and ethical constraints; a Structural Admissibility Validator that evaluates proposed decision requests against the schema before constructing any EvaluationRequest object; and a Zero-Bypass Boundary Enforcement mechanism that restricts EvaluationRequest construction exclusively to the Structural Admissibility Validator. Inadmissible requests are rejected at the structural boundary with a Structured Rejection Record providing machine-readable constraint provenance identifying the specific violated constraint, its regulatory source, and the responsible input fields. The SAE constitutes Layer 0 of a four-layer governance architecture that gates a downstream runtime checkpoint pipeline (Layer 1), trajectory invariant enforcement layer (Layer 2), and cryptographic receipt layer (Layer 3). The zero-bypass property guarantees that no inadmissible request can enter the governance pipeline regardless of the operational state of any downstream component — a categorical improvement over runtime interception architectures where governance guarantees are contingent on every intercepting component being operational and correctly implemented.

---

*Application prepared: April 19, 2026*
*Inventor: Harold Alberto Nunes Rodelo*
*Company: OMNIX Quantum Ltd, United Kingdom*
*© 2026 OMNIX Quantum Ltd. All rights reserved. CONFIDENTIAL — DO NOT DISTRIBUTE*
