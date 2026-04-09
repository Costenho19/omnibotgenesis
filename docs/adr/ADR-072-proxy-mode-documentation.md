# ADR-072: Proxy Mode Documentation — AML Volume, Fraud Sentiment, CAG Liquidity

**Status:** Accepted  
**Date:** 2026-04-09  
**Author:** Harold Nunes  
**Scope:** `omnix_core/bot/auto_trading_bot.py`, `omnix_core/governance/external_evaluator.py`

---

## Context

Following the pattern established by ADR-067 (AML frequency proxy) and ADR-065 (CAG epistemic warning), three additional silent proxy defaults were identified where real data is unavailable but the system uses optimistic/zero values without documenting this in the decision trace:

1. **AML `volume_usd=0`** when `estimated_value_usd` absent from decision dict. The large-volume AML check (FATF Recommendation 7) silently never fires.

2. **Fraud Gate `sentiment_score=50.0`** (neutral stub) when `v52_analysis` absent. The signal divergence check uses a neutral sentinel that never triggers divergence violations.

3. **CAG `liquidity_score=100.0`** in `external_evaluator.py` when `cag_liquidity_score` not provided by API caller. Perfect liquidity was assumed silently.

All three are silent optimistic proxies that could allow trades through checks that would have blocked them with real data.

---

## Decision

### 1. AML Volume Proxy Mode (bot)

```python
_aml_volume = decision.get('estimated_value_usd')
_aml_volume_proxy = _aml_volume is None
if _aml_volume is None:
    _aml_volume = 0.0

_aml_result = _aml_gate.evaluate(..., volume_usd=_aml_volume, ...)
if _aml_volume_proxy:
    decision['decision_trace'].append(
        "AML_VOLUME_PROXY_MODE: estimated_value_usd absent from decision; "
        "volume_usd=0.0 (undercount). Large-volume AML thresholds (FATF R.7) "
        "may not fire. Source: proxy_zero"
    )
```

### 2. Fraud Gate Sentiment Proxy Mode (bot)

```python
_sent_score = 50.0
_sent_source = "PROXY"
if 'v52_analysis' in decision:
    _sent_score = decision['v52_analysis'].get('sentiment_score', 50.0)
    _sent_source = "V52"
if _sent_source == "PROXY":
    decision['decision_trace'].append(
        "FRAUD_SENTIMENT_PROXY_MODE: v52_analysis absent; "
        "sentiment_score=50.0 (neutral stub). Fraud Gate DCI check still active."
    )
```

### 3. CAG Liquidity Proxy Mode (external_evaluator)

Changed from silent `100.0` default to explicit `0.0` with trace:

```python
_cag_liq_raw = cfg.get("cag_liquidity_score")
_cag_liq_proxy = _cag_liq_raw is None
_cag_liq = float(_cag_liq_raw) if _cag_liq_raw is not None else 0.0

if _cag_liq_proxy:
    decision_trace.append(
        "CAG_LIQUIDITY_PROXY_MODE: cag_liquidity_score not provided by caller; "
        "liquidity_score=0.0 used (conservative). Real web/order-book liquidity "
        "data unavailable. Liquidity gate checks may block even healthy sessions."
    )
```

Note: Changed from optimistic `100.0` to conservative `0.0`. This may cause more CAG blocks when liquidity data is absent — which is the correct behavior (fail-safe rather than fail-open).

### 4. ADR-065 epistemic warning updated

The existing CAG_WARNING for all-defaults now reflects the new proxy default values:
```
"vol=0.0, corr=0.0, liq=0.0, macro=0.0" (was "liq=100.0")
```

---

## Consequences

- Decision traces now contain explicit proxy mode markers for all three checks
- Audit dashboards can detect and flag decisions where volume/sentiment/liquidity detection was degraded
- CAG liquidity change from 100.0→0.0 is conservative (fail-safe): more sessions may be blocked when liquidity data absent, but no false positives of perfect liquidity
- All 4 new proxy mode tests pass (TestProxyModesADR072 partial)

---

## Proxy Mode Registry

| Proxy Mode | Trigger | Value Used | Check Degraded |
|---|---|---|---|
| `AML_FREQUENCY_PROXY_MODE` | No DB trade count (ADR-067) | `freq=0` | Structuring detection |
| `AML_VOLUME_PROXY_MODE` | `estimated_value_usd` absent | `volume=0.0` | Large-volume detection |
| `FRAUD_SENTIMENT_PROXY_MODE` | `v52_analysis` absent | `sentiment=50.0` | Divergence detection |
| `FRAUD_REVERSAL_PROXY_MODE` | No action history (ADR-069) | `reversals=0` | Reversal detection |
| `CAG_LIQUIDITY_PROXY_MODE` | `cag_liquidity_score` absent | `liq=0.0` | Liquidity gate |

---

## Regulatory Alignment

- **FATF R.7**: Large-value transaction monitoring — must be operational or explicitly documented as degraded
- **EU AI Act Art. 13**: Transparency — proxy modes must be documented in audit trail
- **MiFID II Rec. 11**: Algorithmic decision systems must document detection limitations

---

## Tests Added

`tests/test_compliance_gates.py::TestProxyModesADR072` (7 tests):
- `test_aml_volume_proxy_note_in_decision_dict`
- `test_fraud_sentiment_proxy_note_when_v52_absent`
- `test_fraud_reversal_proxy_note_when_no_history`
- `test_cag_liquidity_proxy_uses_zero_not_100`
- `test_get_recent_reversals_returns_proxy_when_no_cache`
- `test_get_recent_reversals_returns_cache_when_history_present`
- `test_track_recent_action_maintains_rolling_history`
