# ADR-153 — Numeric Uniformity Anomaly (NUA) Detection

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Tags:** security, llm-boundary, fabrication-detection, differentiator

---

## Context

The LLM Isolation Boundary (ADR-148) enforces a whitelist of 22 approved numeric signal keys.  It checks key names and data types — but it cannot distinguish between numeric values derived from real market data and numeric values invented by an LLM.

An LLM can fabricate governance signals that look structurally valid (correct keys, float values, within 0–100 range) but exhibit statistically suspicious patterns that real market data does not:

1. **Coefficient of variation < 0.15** — all signals suspiciously similar in magnitude.  Real market signals measuring different phenomena (volatility, liquidity, sentiment) are naturally noisy and diverse.
2. **Round-number ratio > 60%** — most values fall on ×0.05 multiples (e.g., 0.75, 0.50, 0.25).  LLMs tend to round to "clean" numbers; financial data does not.
3. **Value range < 5.0 across ≥3 signals** — unnaturally narrow spread across conceptually unrelated signals.

No other governance platform performs post-boundary statistical analysis on the numeric values themselves.  Traditional boundary checks only validate structure.

---

## Decision

Add Numeric Uniformity Anomaly detection to `LLMIsolationBoundary`:

1. **`NumericUniformityReport` dataclass**: captures `report_id`, `coefficient_of_variation`, `round_number_ratio`, `value_range`, `uniformity_score` (0–100), `nua_verdict` (NATURAL / SUSPICIOUS / FABRICATION_LIKELY), and `suspicious_signals` list.

2. **`_analyze_numeric_uniformity()` function**: standalone function called from `form_packet()`.  Computes three independent components:
   - CV component: `max(0, (0.5 - cv) / 0.5) × 40` — max 40 pts
   - Round-number component: `round_ratio × 30` — max 30 pts
   - Range component: `max(0, (10 - range) / 10) × 30` (only if ≥3 signals) — max 30 pts

3. **Verdict thresholds**:
   - `< 30` → NATURAL
   - `30–70` → SUSPICIOUS
   - `≥ 70` → FABRICATION_LIKELY

4. **`nua_report` field in `GovernanceSignalPacket`**: embedded in every packet.  Serialized in `to_dict()`.

### What NUA Does NOT Do

- NUA never blocks a packet.  It is flag-only.  The governance pipeline continues regardless of verdict.
- NUA does not penalize legitimate low-variation signals (e.g., stable fixed-income metrics).  FABRICATION_LIKELY requires all three components to be elevated simultaneously — a single low CV is insufficient.
- NUA does not strip signals or modify them.

---

## Consequences

### Positive

- **Verifiable evidence**: every GovernanceSignalPacket carries a structured NUA report with the exact metrics used for the verdict.
- **Multi-indicator design**: FABRICATION_LIKELY requires CV + round-number + range anomalies together.  Single-indicator triggering is deliberately avoided to prevent false positives on stable signals.
- **Auditor transparency**: `suspicious_signals` list identifies which specific signals triggered the anomaly.
- **Zero false positives on normal inputs**: diverse market signals naturally produce CV > 0.5, varied rounding, and wide range.

### Negative / Trade-offs

- NUA cannot detect fabrication where LLM values happen to be diverse (LLM with good noise injection).  It catches the most common fabrication pattern, not all possible patterns.
- Requires ≥ 2 signals to run; single-signal packets return NATURAL unconditionally.

---

## Implementation Notes

- File: `omnix_core/governance/llm_isolation_boundary.py`
- Dataclass: `NumericUniformityReport`
- Function: `_analyze_numeric_uniformity(signals, packet_id)`
- Field: `GovernanceSignalPacket.nua_report`
- Tests: `tests/test_differentiators.py` — `TestNUANormal`, `TestNUAAdversarial`

### Institutional Explanation (non-technical)

> If a bank analyst gives you six independent risk metrics and every single one is exactly 0.75, you instinctively question the data.  NUA automates that intuition.  It analyzes whether the numbers coming from the AI model look like real market data or like numbers invented by a computer trying to look plausible.  It does not block — it flags and records the suspicion in the audit trail.

---

## Invariant Impact

| Invariant | Impact |
|---|---|
| INV-005 (LLM content never enters governance directly) | Not affected — NUA runs after the boundary, on already-approved signals |
| INV-001 (Fail-Closed) | Not affected — NUA never blocks |
| INV-002 (Receipt per Decision) | Not affected |

---

*OMNIX-NUA-001 | ADR-153 | May 2026*
