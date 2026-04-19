# INVENTORSHIP MEMO — FAMILY 4
## OMNIX-PAT-2026-004

**Invention:** Calibration Drift Detection and Execution Blocking System (Assumption Validity Monitor / AVM)
**Inventor:** Harold Alberto Nunes Rodelo
**Date:** April 19, 2026

---

## INVENTIVE CONTRIBUTION

Harold Alberto Nunes Rodelo is the sole inventor of the systems and methods described in this application. His inventive contributions include:

1. **Identification of the Knightian Uncertainty Gap:** Recognition that automated governance systems certify decisions based on calibrated parameters but have no mechanism for detecting when those calibration assumptions are no longer valid — producing structurally valid but substantively unreliable certifications.

2. **Three-Priority Blocking Policy:** Design and implementation of the fail-closed blocking policy that evaluates non-finite signal detection, critical staleness, and weighted drift in strict priority order — ensuring that the most severe failure modes are detected first.

3. **NaN Fail-Closed Architecture (ADR-075):** Identification of the silent pass-through vulnerability in Python governance systems where NaN > threshold evaluates to False, and design of the explicit non-finite detection mechanism that treats NaN/Inf inputs as blocking conditions.

4. **Weighted Multi-Signal Drift Scoring:** Design of the weighted drift computation architecture with configurable per-signal weights reflecting governance importance hierarchy.

5. **Pass-Through vs. Certified Distinction:** Design of the epistemic transparency principle distinguishing pass-through (no baseline — not certified) from certified (baseline validated) states, preventing false certification by absence.

6. **Snapshot Parameter Versioning:** Design of the certification provenance system embedding snapshot identifiers in governance receipts for retrospective traceability and invalidation.

7. **Adversarial Test Cases:** Design and validation of adversarial scenarios including Terra/LUNA collapse pattern, gradual drift manipulation, boundary manipulation, and NaN injection — each based on real-world governance failure modes.

---

## CONCEPTION DATE

The AVM concept was conceived in the context of OMNIX governance architecture development. The Terra/LUNA adversarial scenario — which directly motivated the critical age blocking mechanism — was documented in internal architecture decision records (ADR-064, ADR-075) during the period January–April 2026.

---

## REDUCTION TO PRACTICE

The AVM was reduced to practice as implemented code in `omnix_core/governance/assumption_validity_monitor.py`, with a comprehensive adversarial test suite in `tests/test_assumption_validity_monitor.py`. The implementation is operational and integrated into the OMNIX governance pipeline as of April 2026.
