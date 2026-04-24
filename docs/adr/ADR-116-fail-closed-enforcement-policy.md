# ADR-116: Fail-Closed Enforcement Policy — Governance Gate Internal Error Handling

**Status:** ACCEPTED  
**Date:** 2026-04-24  
**Author:** Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD  
**Build:** 6.5.7 | Post-Forensic Audit II  
**Supersedes:** None (new policy)  
**Related:** ADR-092 (SAE Layer 0), ADR-072 (CAG), ADR-047 (AML Gate), ADR-048 (Fraud Gate), ADR-096 (PQC Receipt), ADR-073 (Forensic Audit I)

---

## Context

A second forensic audit (24 April 2026) identified 16 architectural defects across the OMNIX governance pipeline. Eight were classified as critical — all sharing a common root cause: **governance gates failing open on internal errors instead of closed**.

The defects produced three categories of failure:

### Category 1 — Gates disabled by default

The Layer 0 SAE (`SAE_ENABLED`) and the Context Admission Gate (`CAG_ENABLED`) both defaulted to `"false"`. This meant:
- A production deployment without explicit env var configuration silently operated without Layer 0 structural admissibility checks
- The CAG, which blocks sessions with insufficient liquidity, excessive volatility, or excessive macro risk, was never active unless manually enabled

### Category 2 — Gates failing open on internal errors

When AML Gate (CP-9), Fraud Gate (CP-10), or the SAE itself raised an internal exception, the system issued a `logger.warning` and continued to Layer 1 as if the gate had passed. This violates the foundational OMNIX guarantee:

> *"OMNIX is a fail-closed governance engine. A gate that cannot evaluate must not pass."*

For the SAE specifically, this also violated the **Zero-Bypass guarantee** of ADR-092 Component C (ZBE): an SAE internal error allowed a request to reach Layer 1 without structural admissibility validation.

### Category 3 — Silent institutional-grade degradation

Two additional patterns silently degraded OMNIX's institutional guarantees without any caller notification:

1. **PQC signing failure → SHA-256 fallback**: When Dilithium-3 signing failed, the receipt was silently issued with `SHA-256-FALLBACK` as the `signature_algorithm`. A client that purchased institutional-grade PQC governance received a SHA-256 hash receipt without knowing their security guarantee had degraded.

2. **Dashboard metrics → hardcoded fake data**: When the PostgreSQL connection failed at the `/api/metrics` endpoint, the API responded with `success: True` and hardcoded numbers (766,741 evaluation cycles, 82,518 PQC-signed receipts, 9,317 blocked decisions). An investor or counterparty viewing the dashboard during a DB outage would see fabricated operational data.

---

## Decision

### Policy 1 — All governance gates are ON by default

`SAE_ENABLED` and `CAG_ENABLED` env vars default to `"true"`. Only an explicit `"false"` disables them.

```python
# BEFORE (fail-open default):
os.environ.get("SAE_ENABLED", "false").lower() == "true"
os.environ.get("CAG_ENABLED", "false").lower() == "true"

# AFTER (fail-closed default):
os.environ.get("SAE_ENABLED", "true").lower() != "false"
os.environ.get("CAG_ENABLED", "true").lower() != "false"
```

Applied in both `omnix_web/api/omnix_engine/external_evaluator.py` and `omnix_core/governance/external_evaluator.py`.

### Policy 2 — SAE internal errors → BLOCKED (fail-closed)

An `Exception` raised inside the SAE `validate()` call does not produce a pass-through. It produces a `BLOCKED` response with `layer: LAYER_0_STRUCTURAL_ADMISSIBILITY` and `result: SAE_INTERNAL_ERROR`. The veto chain documents the error. Layer 1 is never reached.

```python
except Exception as _sae_err:
    logger.error(
        f"[Layer 0] SAE INTERNAL ERROR — failing closed: {_sae_err} | "
        f"asset={asset} domain={domain}"
    )
    return {
        "decision": "BLOCKED",
        "layer": "LAYER_0_STRUCTURAL_ADMISSIBILITY",
        "veto_chain": [{
            "checkpoint_id": "LAYER_0",
            "result": "SAE_INTERNAL_ERROR",
            "description": f"SAE internal error — fail-closed: {_sae_err}",
        }],
        ...
    }
```

### Policy 3 — SAEOverride.FORCE_OFF permanently removed

`SAEOverride.FORCE_OFF` has been removed from the `SAEOverride` enum in `structural_admissibility_engine.py`. It was an undocumented emergency bypass that contradicted the Zero-Bypass guarantee of ADR-092 Component C.

The enum now contains only:
- `SAEOverride.UNSET` — honour `compliance_config.layer0_enabled` / `SAE_ENABLED` env var
- `SAEOverride.FORCE_ON` — Layer 0 active regardless of caller flags

There is no operator mechanism to disable Layer 0 at runtime. To disable Layer 0 for a specific deployment, `SAE_ENABLED=false` must be set as an explicit environment variable, which produces an observable configuration log at startup.

### Policy 4 — AML and Fraud Gate internal errors → BLOCKED (fail-closed)

An `Exception` in CP-9 (AML Gate) or CP-10 (Fraud Gate) no longer issues a pass-through warning. Both gates now:
- Log at `ERROR` level (not `WARNING`)
- Set `decision = "BLOCKED"`, `overall_blocked = True`
- Append an `AML_INTERNAL_ERROR` / `FRAUD_INTERNAL_ERROR` veto chain entry
- Prevent the receipt from being issued as APPROVED

Applied in both `omnix_web/api/omnix_engine/external_evaluator.py` and `omnix_core/governance/external_evaluator.py`.

### Policy 5 — PQC signing failure → RuntimeError (no SHA-256 fallback)

`_sign_canonical_hash()` in `proof_layer.py` now raises `RuntimeError` when Dilithium-3 signing fails. No SHA-256 fallback is produced.

```python
except Exception as _pqc_err:
    logger.error(
        f"[ADR-096] PQC signing FAILED — receipt cannot be issued: {_pqc_err}"
    )
    raise RuntimeError(
        f"PQC signing unavailable — institutional receipt cannot be issued: {_pqc_err}"
    ) from _pqc_err
```

**Rationale:** A receipt issued with SHA-256 instead of Dilithium-3 silently violates the institutional guarantee clients purchased. A `RuntimeError` surfaces as an HTTP 500 at the `/evaluate` endpoint — explicit, auditable, and consistent with the principle that a governance system must not silently degrade its own guarantees.

If the PQC signing infrastructure is unavailable, the system must surface this as a service error, not silently produce a weaker receipt.

### Policy 6 — Dashboard metrics failure → HTTP 503 (no hardcoded fallback)

The `/api/metrics` endpoint no longer returns hardcoded operational numbers on database failure. It returns:

```json
{
  "success": false,
  "live": false,
  "error": "Metrics unavailable — database unreachable",
  "last_updated": "<ISO8601>"
}
```

with HTTP status `503`. This is consistent with standard API design: a service that cannot read real data must not claim it has real data.

---

## Fail-Closed Gate Registry

The following table documents the current fail-closed policy for each governance gate:

| Gate | Checkpoint | Internal Error → | ADR |
|---|---|---|---|
| SAE Layer 0 | LAYER_0 | `BLOCKED` + `SAE_INTERNAL_ERROR` veto | ADR-092 + this |
| CAG Context Admission Gate | CAG | `pass-through` (by design — ADR-050) | ADR-050 |
| AML Gate | CP-9 | `BLOCKED` + `AML_INTERNAL_ERROR` veto | ADR-047 + this |
| Fraud Gate | CP-10 | `BLOCKED` + `FRAUD_INTERNAL_ERROR` veto | ADR-048 + this |
| Jurisdiction Gate | CP-11 | `pass-through` with trace entry | ADR-049 |
| Sharia Gate | CP-6 | `BLOCKED` on gate evaluation | ADR-046 |
| TIE | — | `trajectory_score=0.0` pass-through (ADR-066) | ADR-066 |
| PQC Signing | — | `RuntimeError` → HTTP 500 | ADR-096 + this |

**Note on CAG:** CAG exceptions are handled as pass-through with a trace entry (existing behavior from ADR-050). CAG is a session-level pre-admission gate — its role is to block sessions with clearly inadmissible market conditions. An internal exception in CAG does not have the same semantic risk as an exception in a compliance gate (AML/Fraud/SAE). This asymmetry is intentional and documented.

---

## CAG Parameters Now Forwarded from /evaluate Request Body

As a consequence of CAG being enabled by default, the `/evaluate` public endpoint (`proof_layer.py`) now reads and forwards the following CAG context parameters from the request body to the `compliance_config`:

```json
{
  "action": "TRADE",
  "asset": "BTC",
  "amount": 1000,
  "cag_liquidity_score": 80.0,
  "cag_global_volatility": 10.0,
  "cag_cross_pair_correlation": 20.0,
  "cag_macro_risk": 15.0
}
```

When these parameters are absent, the CAG operates in proxy mode (`CAG_LIQUIDITY_PROXY_MODE` as per ADR-072) with conservative defaults (`liq=0.0`). This may block sessions that have healthy real-world liquidity. Callers providing real market data will produce more accurate governance outcomes.

---

## Consequences

### Positive
- Layer 0 structural admissibility is now active in all deployments by default — no configuration required to achieve the Zero-Bypass guarantee
- AML and Fraud Gate failures can no longer silently allow a transaction through compliance checks
- PQC receipt degradation is now explicit — clients know when their institutional guarantee is unavailable
- Dashboard consumers cannot mistake fabricated metrics for real operational data
- The fail-closed gate policy is now documented, testable, and auditable across all governance layers

### Negative / Trade-offs
- Deployments that previously relied on `SAE_ENABLED` and `CAG_ENABLED` being `false` by default now require explicit `SAE_ENABLED=false` or `CAG_ENABLED=false` env vars to restore previous behavior
- PQC signing infrastructure unavailability will surface as HTTP 500 at `/evaluate` — clients need to handle this error class (previously they received a receipt with degraded security)
- Any deployment without Dilithium-3 signing keys configured (`OMNIX_SIGNING_SECRET_KEY_B64` absent) will now fail to issue receipts. Configure persistent keys per ADR-078.

---

## Files Changed

| File | Change |
|---|---|
| `omnix_web/api/omnix_engine/external_evaluator.py` | SAE default ON, CAG default ON, SAE/AML/Fraud fail-closed |
| `omnix_core/governance/external_evaluator.py` | Same changes in the core version |
| `omnix_core/governance/structural_admissibility_engine.py` | `SAEOverride.FORCE_OFF` removed |
| `omnix_web/api/proof_layer.py` | PQC signing raises, CAG params forwarded from body |
| `omnix_web/api/server.py` | `/api/metrics` returns 503 on DB failure |
| `tests/test_structural_admissibility_engine.py` | `FORCE_OFF` tests removed |
| `tests/test_sae_e2e.py` | CAG params added to `test_btc_global_approved` |

---

## Tests

All 93 governance tests pass after these changes.  
`TESTING=true python -m pytest tests/test_structural_admissibility_engine.py tests/test_sae_e2e.py -v` → **93/93 PASSED**
