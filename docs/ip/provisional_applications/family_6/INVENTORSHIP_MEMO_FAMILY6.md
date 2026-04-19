# INVENTORSHIP MEMO — FAMILY 6
## OMNIX-PAT-2026-006

**Invention:** Session-Level Context Admission Gate (CAG)
**Inventor:** Harold Alberto Nunes Rodelo
**Date:** April 19, 2026

---

## INVENTIVE CONTRIBUTION

Harold Alberto Nunes Rodelo is the sole inventor of the systems and methods described in this application. His inventive contributions include:

1. **Identification of the Macro Admissibility Gap:** Recognition that per-decision governance systems contain a structural gap — they evaluate whether a specific decision is admissible without first evaluating whether the global environment makes any decision admissible at all.

2. **Session-Level vs. Decision-Level Architecture:** Design of the session-level pre-admission gate as a distinct architectural layer upstream of all per-decision checkpoints — ensuring that macro-inadmissible environments block entire sessions, not individual decisions.

3. **Four-Dimensional Global Condition Evaluation:** Design of the four-dimension evaluation framework (global volatility, cross-pair correlation, liquidity score, macro risk) as independent, configurable admission conditions covering both "must be below" and "must be above" threshold types.

4. **Epistemic Transparency Enforcement (ADR-070):** Identification of the false confidence fabrication problem — systems that assign high scores when disabled, treating non-evaluation as evidence of favorable conditions — and design of the explicit state matrix distinguishing EVALUATED, DISABLED, and FAILSAFE states with zero scores for non-evaluated states.

5. **Regulatory Alignment Architecture:** Design of the CAG as a direct implementation of session-level circuit breaker obligations under MiFID II, context-aware governance under NIST AI RMF, and risk management under EU AI Act Article 9.

6. **Fail-Safe-to-Admit Policy:** Design of the asymmetric fail policy: CAG module failure → admit with zero score (FAILSAFE), contrasting with AVM module failure → block (fail-closed). This reflects the different architectural roles of the two modules.

---

## CONCEPTION DATE

The CAG concept was conceived during OMNIX governance architecture development, documented in ADR-050 (March 2026) and refined in ADR-070 (April 9, 2026) following identification of the false confidence score issue.

---

## REDUCTION TO PRACTICE

The CAG was reduced to practice as implemented code in `omnix_core/governance/context_admission_gate.py`, with a comprehensive test suite in `tests/test_context_admission_gate.py`. The implementation is operational and integrated into the OMNIX governance pipeline as of April 2026.
