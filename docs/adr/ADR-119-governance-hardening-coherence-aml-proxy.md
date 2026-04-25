# ADR-119 — Governance Hardening: Dynamic Coherence Threshold & AML Proxy Mode Transparency

**Status:** Accepted — Implemented 25 Apr 2026  
**Author:** Harold Alberto Nunes Rodelo  
**Scope:** Trading governance pipeline — coherence gate, AML gate  
**Triggered by:** Full audit log review — decision OMNIX-TRD-DC8160C9AE88

---

## 1. Context

A full review of a live trading decision log revealed three issues with the governance pipeline operating at the edge of acceptable tolerance:

### Finding 1 — Coherence threshold too permissive when Black Swan = HIGH
The `veto_critical` threshold was fixed at 30% regardless of market conditions. In the audited decision, coherence was 40.1% (POOR) and Black Swan was HIGH. The system passed coherence validation despite operating in elevated crash-risk conditions. Accepting POOR coherence under HIGH crash probability weakens the pre-execution admissibility gate at exactly the moment it matters most.

### Finding 2 — AML PROXY_MODE not explicitly flagged
When `OMNIX_DB_URL` is unavailable, the AML gate cannot query real trade frequency. It falls back to `frequency=0` (conservative baseline) without:
- Explicit `proxy_mode` flag on the result object
- A log warning readable by operators
- Clear traceability in the audit receipt

The MCM already detects this via the `GATE_AMPLIFICATION:AML_FREQUENCY_PROXY_MODE` transition signature (ADR-117), but the gate itself was silent.

### Finding 3 — Adaptive gate bypass (documentation)
When EMA period count < 20, the adaptive gate is bypassed and falls back to a weaker baseline. This is intentional behavior (insufficient history), but the fallback baseline strength is not explicitly logged or documented in the decision trace.

---

## 2. Decision

### Fix 1: Dynamic coherence threshold escalation — BS=HIGH

When Black Swan level = HIGH, coherence thresholds are escalated before the veto comparison:

| Condition | `veto_critical` | `veto_normal` |
|---|---|---|
| Normal | 30% (profile) | 45% (profile) |
| BS = HIGH | max(profile, **50%**) | max(profile, **65%**) |

This ensures that under elevated crash probability, only decisions with strong signal agreement proceed. A HOLD is always safe to emit under these conditions.

**Implementation:** `omnix_core/bot/auto_trading_bot.py` — after threshold computation, before coherence comparison.

**Decision trace entry:** `BS_HIGH_COHERENCE_ESCALATION: critical=50% normal=65%`

**Log level:** WARNING — visible in operator logs.

### Fix 2: AML proxy_mode explicit flag

`AMLVetoResult` dataclass gains `proxy_mode: bool = False`.

When `freq_source == "unavailable"`:
- `result.proxy_mode = True`
- Logger emits WARNING with clear message and remediation hint

This makes the degraded state explicit and traceable in the decision receipt veto_chain analysis.

**Implementation:** `omnix_core/governance/aml_gate.py`

### Fix 3: Adaptive gate — documentation only (this ADR)

The adaptive gate bypass when EMA < 20 periods is intentional. It uses a static baseline rather than an adaptive one. No code change in this ADR. A future ADR (ADR-120) will define the fallback strength criteria.

---

## 3. Consequences

### Positive
- Decisions under BS=HIGH conditions now require coherence ≥ 50% (vs 30% before). This reduces the risk of executing under POOR coherence during elevated crash probability.
- AML proxy mode is now explicit, logged, and traceable. Operators can detect it without inspecting the MCM report.
- Both changes are logged to `decision_trace` — fully auditable in the PQC receipt.

### Trade-offs
- BS=HIGH + coherence between 30%–50% will now HOLD instead of proceeding. This is by design — under crash conditions, the cost of a false positive (unnecessary HOLD) is lower than a false negative (executing under degraded coherence).
- AML proxy_mode warning will appear in logs when `OMNIX_DB_URL` is not set. This is intentional noise — it signals a configuration issue.

---

## 4. Threshold Rationale

| Threshold | Value | Rationale |
|---|---|---|
| `veto_critical` BS=HIGH | 50% | Below 50% = less than half signals agree. Under crash conditions, this is insufficient. |
| `veto_normal` BS=HIGH | 65% | Strong majority required for non-HOLD execution when crash risk is elevated. |
| AML proxy baseline | freq=0 | Conservative: assumes no structuring. Better than blocking all trades; worse than real data. |

---

## 5. Related ADRs

| ADR | Relation |
|---|---|
| ADR-051 | ACTIVE mode coherence thresholds — this ADR overrides upward when BS=HIGH |
| ADR-069 | Fraud gate proxy mode — same pattern applied to AML gate |
| ADR-116 | Fail-closed enforcement — proxy_mode is explicit degradation, not silent bypass |
| ADR-117 | MCM v1.1 — GATE_AMPLIFICATION:AML_FREQUENCY_PROXY_MODE already detected |
| ADR-119 | This document |

---

## 6. Audit Log Reference

Decision: `OMNIX-TRD-DC8160C9AE88`  
Pre-fix behavior: coherence 40.1% (POOR) passed veto_critical=30% under BS=HIGH  
Post-fix behavior: coherence 40.1% < escalated veto_critical=50% → HOLD (correct)

*"The system no longer accepts POOR coherence under elevated crash probability. The gate is stricter precisely when the cost of error is highest."*
