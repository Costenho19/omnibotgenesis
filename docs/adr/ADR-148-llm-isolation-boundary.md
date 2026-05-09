# ADR-148 — LLM Isolation Boundary

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** —  
**Related:** ADR-028, ADR-040, ISR-017, ISR-012  
**Module:** `omnix_core/governance/llm_isolation_boundary.py`

---

## Context

OMNIX operates two distinct computational flows that must never directly exchange data without explicit sanitization and normalization:

1. **Conversational AI Flow** — `omnix_services/ai_service/` — intent analysis, natural language generation, Telegram bot responses, web search. Optimistic, user-facing, trust-flexible.

2. **Governance Pipeline** — `omnix_core/governance/` — 11-checkpoint fail-closed evaluation engine, AVM, PQC-signed receipts. Zero-tolerance, institutional-grade, trust-anchored.

ISR-017 identified a prompt injection vector where `user_message` content entered AI prompts without sanitization. That was remediated at the *content level* by `input_sanitizer.py`.

However, a deeper architectural gap remained: **no structural enforcement** prevented raw LLM output dictionaries — potentially containing model names, conversation fragments, or injected keys — from reaching the governance signal normalization layer.

The risk is not just content-level injection. It is architectural contamination: LLM-generated keys with non-numeric values or forbidden names could inadvertently pass governance checkpoint logic as signals, producing false evaluations.

---

## Decision

Implement a **LLM Isolation Boundary** as a structural enforcement module (`llm_isolation_boundary.py`) that:

1. Defines a strict **approved signal key whitelist** (`_APPROVED_SIGNAL_KEYS`) — 22 numeric governance signals.
2. Defines an explicit **forbidden key list** (`_FORBIDDEN_SIGNAL_KEYS`) — 13 LLM artifact keys.
3. Requires all data crossing from the AI layer to the governance layer to be wrapped in a `GovernanceSignalPacket`.
4. `LLMIsolationBoundary.form_packet()` is the **only authorized crossing function** — strips forbidden/unknown/non-numeric keys, logs every crossing.
5. Every boundary crossing is logged in-process with full provenance: source, destination, asset, domain, stripped keys, sanitization flags from ISR-017, packet hash.
6. `BoundaryViolationError` is raised in strict mode when forbidden LLM keys are detected.
7. A module-level singleton `get_isolation_boundary()` is the standard access pattern.

---

## Signal Whitelist

The following numeric signals are approved for governance evaluation:

| Signal Key | Description |
|---|---|
| `probability` | Primary signal probability (normalized 0–1) |
| `risk_score` | Composite risk score |
| `coherence_score` | Cross-signal coherence (ADR-007) |
| `volatility` | Asset/market volatility |
| `volume_ratio` | Volume anomaly ratio |
| `correlation` | Cross-asset correlation |
| `liquidity_score` | Liquidity Coverage Ratio (LCR) |
| `macro_risk_index` | Macro environment risk |
| `concentration_pct` | Portfolio concentration % |
| `collateral_coverage` | Collateral coverage ratio |
| `counterparty_risk` | Counterparty exposure risk |
| `aml_risk_score` | AML risk indicator |
| `fraud_risk_score` | Fraud probability |
| `jurisdiction_risk` | Regulatory/jurisdiction risk |
| `sentiment_score` | Market sentiment |
| `drawdown_pct` | Maximum drawdown % |
| `sharpe_ratio` | Risk-adjusted return |
| `var_95` | Value at Risk (95%) |
| `cvar_95` | Conditional VaR (95%) |
| `beta` | Market beta |
| `leverage_ratio` | Leverage ratio |
| `duration` | Portfolio duration |

---

## Forbidden Keys

The following keys are explicitly forbidden from governance signals (LLM artifacts):

`user_message`, `prompt`, `system_prompt`, `llm_response`, `model_name`, `model_id`, `conversation_id`, `session_id`, `raw_text`, `instruction`, `context_window`, `temperature`, `top_p`, `completion`, `chat_history`

---

## Consequences

### Positive
- **Structural enforcement**: even if sanitizer (ISR-017) fails, boundary strips LLM artifacts before governance.
- **Auditability**: every crossing is logged with packet hash — regulators can verify what signals entered governance.
- **Defense in depth**: two independent layers (content sanitizer + signal boundary) before governance evaluation.
- **Strict mode**: optional fail-closed mode for high-security deployments.

### Negative
- **New dependency**: callers from the AI layer must use `form_packet()` — existing direct signal passing must be refactored.
- **Approved whitelist management**: adding new governance signals requires updating `_APPROVED_SIGNAL_KEYS`.

---

## Boundary Crossing Protocol

```
[AI Service / Telegram Bot]
         │
         │ raw_dict (may contain LLM artifacts)
         ▼
[input_sanitizer.py / ISR-017]   ← content-level sanitization
         │
         │ (sanitized_text, flags)
         ▼
[LLMIsolationBoundary.form_packet()]  ← structural enforcement
         │
         │ GovernanceSignalPacket (approved numeric signals only)
         ▼
[GovernanceEvaluationEngine.evaluate()]  ← 11-checkpoint pipeline
         │
         │ evaluation result
         ▼
[DecisionReceiptEngine.generate_receipt()]  ← PQC-signed receipt
```

---

## Implementation Notes

- `GovernanceSignalPacket.packet_hash()` produces a SHA-256 of the packet content (excluding `packet_id`) — suitable for audit trail integrity.
- `get_boundary_stats()` returns crossing statistics suitable for Grafana/observability dashboards.
- `get_boundary_log(limit)` returns recent crossing records — usable by the operations dashboard.
- In-process ring buffer holds up to 1,000 crossing records. For persistent storage, wire `_log_crossing` to DB (future ADR).

---

*OMNIX QUANTUM — Decision Governance Infrastructure*  
*ADR-148 · LLM Isolation Boundary · omnixquantum.net*
