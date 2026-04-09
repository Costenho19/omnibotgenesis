# ADR-071: PQC Receipt Builder — Eliminate score=100.0 defaults + evaluation_state in receipts

**Status:** Accepted  
**Date:** 2026-04-09  
**Author:** Harold Nunes  
**Scope:** `omnix_core/bot/auto_trading_bot.py` (receipt builder, lines ~790–860)

---

## Context

The PQC receipt builder in `auto_trading_bot.py` contained four critical fabrication bugs:

```python
'score': decision.get('sharia_score', 100.0),           # line 790
'score': decision.get('aml_score', 100.0),               # line 802
'integrity_score': decision.get('fraud_integrity_score', 100.0),  # line 813
'compliance_score': decision.get('jurisdiction_compliance_score', 100.0),  # line 825
```

When a gate is disabled, its score key is not written into the `decision` dict. The `.get(..., 100.0)` fallback therefore fabricated `100.0` (perfect compliance) into the **PQC-signed, immutable receipt** stored in the database.

This is the most severe category of epistemic violation:
- The receipt is cryptographically signed with Kyber-768 post-quantum encryption
- Once signed and stored, the score cannot be corrected
- Auditors, regulators, and investors see `sharia_score=100`, `aml_score=100`, `fraud_integrity=100` even when no gate ran

This was identified as the worst bug in the forensic audit.

---

## Decision

### 1. Replace all `default=100.0` with `None`-check pattern

For each gate score in the receipt builder:

```python
_sharia_score = decision.get('sharia_score')
_sharia_score_note = None
if _sharia_score is None:
    _sharia_score = 0.0
    _sharia_score_note = "SCORE_PROXY: sharia_score absent from decision; 0.0 means not evaluated."
receipt_input['sharia_compliance'] = {
    ...
    'score': _sharia_score,
    **({"score_note": _sharia_score_note} if _sharia_score_note else {}),
}
```

Applied to: `sharia_score`, `aml_score`, `fraud_integrity_score`, `jurisdiction_compliance_score`.

### 2. `evaluation_state` added to each gate's receipt block

```python
'evaluation_state': decision.get('sharia_evaluation_state', ''),
```

The `evaluation_state` is populated at the gate call site:
- `sharia_evaluation_state` from `getattr(_sharia_result, 'evaluation_state', '')`
- `aml_evaluation_state` from `getattr(_aml_result, 'evaluation_state', '')`
- `fraud_evaluation_state` from `getattr(_fraud_result, 'evaluation_state', '')`
- `jurisdiction_evaluation_state` from `getattr(_juris_result, 'evaluation_state', '')`

### 3. `SCORE_PROXY` note in receipt when score absent

When a gate's score is absent (gate disabled or not run), the receipt now contains:
```json
"score_note": "SCORE_PROXY: sharia_score absent from decision; 0.0 means not evaluated."
```

This makes the absence explicit in the immutable signed receipt.

---

## Consequences

- PQC receipts no longer contain fabricated compliance scores
- Receipts with disabled gates show `score=0.0` + `score_note="SCORE_PROXY:..."` + `evaluation_state="DISABLED"`
- Receipts with evaluated gates show the real score + `evaluation_state="EVALUATED"`
- All 5 new tests pass (TestPQCReceiptADR071)
- Backward-incompatible for receipt parsing: `score=0.0` + `score_note` is now the correct representation of "not evaluated"

---

## Regulatory Alignment

- **EU AI Act Art. 13 (Transparency)**: Decisions must explain their basis — fabricated scores violate this
- **FATF R.7 / R.16**: AML compliance cannot be asserted without evaluation
- **AAOIFI SS-59 (Gharar)**: Sharia compliance cannot be declared without Sharia evaluation
- **GDPR Art. 22**: Automated decisions must be explainable and accurate

---

## Tests Added

`tests/test_compliance_gates.py::TestPQCReceiptADR071` (5 tests):
- `test_sharia_score_missing_defaults_to_zero_not_100`
- `test_aml_score_missing_defaults_to_zero_not_100`
- `test_fraud_integrity_score_missing_defaults_to_zero_not_100`
- `test_jurisdiction_score_missing_defaults_to_zero_not_100`
- `test_receipt_builder_logic_no_hardcoded_100`
