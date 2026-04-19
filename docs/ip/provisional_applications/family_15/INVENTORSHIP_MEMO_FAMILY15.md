# INVENTORSHIP MEMO — FAMILY 15
## OMNIX-PAT-2026-015

**Invention:** Structural Admissibility Engine (SAE) — Pre-Pipeline Schema Validation Layer
**Inventor:** Harold Alberto Nunes Rodelo — April 19, 2026

## INVENTIVE CONTRIBUTIONS

1. **Layer 0 Structural Admissibility Concept:** Design of the pre-pipeline boundary layer (Layer 0) that enforces decision admissibility at the schema-construction level rather than at runtime evaluation — making structurally invalid decision requests unrepresentable as valid system objects. The insight that admissibility is a property of state representation, not of runtime interception, constitutes the core inventive concept.

2. **Enumerated Constraint Encoding:** Design of the constraint encoding methodology that translates regulatory, jurisdictional, ethical, and operational rules into schema-level type constraints and constructor validators — so that a request combining a prohibited asset, an unauthorized operation type, or a disallowed jurisdictional combination cannot be instantiated as a valid EvaluationRequest object.

3. **Zero-Bypass Property:** Design of the zero-bypass architectural guarantee: because invalid requests cannot be constructed, no code path exists that could permit an inadmissible request to enter the governance pipeline. This is architecturally distinct from runtime interception, which requires every checkpoint to be active and correctly implemented to guarantee blocking.

4. **Four-Layer Governance Architecture:** Design of the four-layer composite governance architecture in which Layer 0 (Structural Admissibility Engine) precedes and gates Layer 1 (OMNIX Runtime Pipeline), Layer 2 (Trajectory Invariant Engine), and Layer 3 (Evidence and Receipt Layer) — creating a system in which each layer addresses a categorically different class of governance failure.

5. **Structured Rejection with Constraint Provenance:** Design of the structured rejection response format that, when a request fails schema construction, returns not merely an error code but a machine-readable constraint provenance record identifying the specific rule, the specific constraint violated, and the regulatory or policy source from which the constraint derives.

6. **Cross-Domain Constraint Composability:** Design of the composable constraint architecture that allows jurisdiction constraints, asset class constraints, operation type constraints, ethical compliance constraints (Sharia, ESG), and client-specific constraints to be combined into a single schema-level validator without requiring runtime branching logic.

## REDUCTION TO PRACTICE

- `omnix_web/api/omnix_engine/jurisdiction_gate.py` — existing runtime gate (ADR-049, March 2026) — prior art baseline from which SAE structurally advances
- `omnix_web/api/gov_blueprint.py` — evaluation pipeline entry point where Layer 0 integrates
- Architectural specification documented April 19, 2026 (this application)

**Git commit hashes:** [RETRIEVE BEFORE FILING]
