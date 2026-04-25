# ADR-120 — AVMEngine: Structured Access Layer & Auto-Recalibración de Dominios

**Status:** Accepted — Implemented 25 Apr 2026  
**Author:** Harold Alberto Nunes Rodelo  
**Scope:** Assumption Validity Monitor — external API, auto-recalibration daemon  
**Triggered by:** OMNIX Hardcore Audit Suite v2.0 — findings A-03, C-01

---

## 1. Context

The `AssumptionValidityMonitor` (AVM) was a singleton with direct internal access patterns. Two audit findings required architectural changes:

### Finding A-03 — No structured external API for AVM
Audit scripts and governance endpoints accessed AVM internals directly. There was no `AVMEngine` façade class to expose `get_stale_domains()`, `auto_recalibrate_stale_domains()`, or `get_avm_status()` through a stable interface. This made the AVM unauditable from external tooling without coupling to internal implementation.

### Finding C-01 — No automatic recalibration of stale assumptions
Domains with calibration age > 72 hours were never automatically recalibrated. Drift could accumulate silently with no daemon observing or acting on it. AVM health was purely reactive (recalibrated only when a trade was evaluated for that domain).

---

## 2. Decision

### 2.1 AVMEngine — Structured Façade (`omnix_core/governance/avm_engine.py`)

A new `AVMEngine` class wraps the `AssumptionValidityMonitor` singleton and exposes:

| Method | Description |
|---|---|
| `get_stale_domains(interval_h=72)` | Returns domains with calibration age ≥ interval from 3 sources: memory store, disk calibration files, PostgreSQL `avm_snapshots` table |
| `auto_recalibrate_stale_domains()` | Triggers recalibration for each stale domain using live cached signals |
| `get_avm_status()` | Returns a complete snapshot of all domain health for audit dashboards |

**Key design choices:**
- `get_stale_domains()` checks 3 sources to detect domains tracked only in DB (e.g., after server restart, before any live evaluation). In production, 8–10 domains are typically detected stale from DB after 72h+ without recalibration.
- `auto_recalibrate_stale_domains()` skips domains without cached live signals (`_last_seen_signals`) — never recalibrates blindly from stale data.
- Drift guard: if drift > `_drift_threshold_override` (default 80%), recalibration is skipped with a WARNING (may indicate market crisis requiring human review).

### 2.2 AVM Auto-Recalibración Daemon (`omnix_web/api/server.py`)

A background daemon thread `AVM-AutoRecalib` runs:
- **Warmup:** 30 minutes after startup (server needs live signal data first)
- **Cycle:** Every 24 hours
- **Logic:** Calls `AVMEngine().auto_recalibrate_stale_domains()` — domains stale ≥ 72h are recalibrated if live signals are available

### 2.3 AssumptionValidityMonitor enhancements

- `evaluate()` now caches live signals in `_last_seen_signals[domain]` with a thread lock
- `auto_recalibrate_stale_domains(interval_h=72, max_drift=0.80)` added as first-class method
- Threading imports added for daemon-safe signal cache

---

## 3. Fail-Safe Dataclass Defaults (ADR-116 supplement)

As part of the audit repair, all governance gate result dataclasses now have explicit fail-safe defaults:

| Class | Field | Before | After |
|---|---|---|---|
| `AMLVetoResult` | `admissible` | required positional arg | `bool = False` |
| `FraudVetoResult` | `admissible` | required positional arg | `bool = False` |
| `CAGResult` | `admitted` | required positional arg | `bool = False` |

**Rationale:** If a result object is instantiated without the admission field (e.g., in test scaffolds or proxy mode), the default is `False` (not admitted). This is the fail-safe direction: the system blocks rather than permits. Consistent with ADR-116 Zero-Bypass Enforcement Policy.

---

## 4. TESTING Flag — Production Safety Guard

The `TESTING=true` environment variable bypasses `TELEGRAM_BOT_TOKEN` format validation in `env_manager.py`. This is used exclusively in CI/CD and development.

**Guard added:** `env_manager.py` now checks `ENVIRONMENT=production` or `RAILWAY_ENVIRONMENT_NAME=production` before applying the TESTING bypass. If running in production, `TESTING=true` is ignored and the full validation runs — preventing accidental bypass if the env var is ever set in a Railway deployment.

```python
is_production = (
    os.environ.get('ENVIRONMENT', '').lower() == 'production' or
    os.environ.get('RAILWAY_ENVIRONMENT_NAME', '').lower() == 'production'
)
is_test_env = (
    not is_production and (
        os.environ.get('PYTEST_CURRENT_TEST') is not None or
        os.environ.get('TESTING', '').lower() in ('true', '1', 'yes')
    )
)
```

---

## 5. except:pass → logger (A-05 Audit Finding)

12 silent `except: pass` blocks across governance and monitoring modules were replaced with explicit `logger.debug` or `logger.warning` calls. Files affected:

- `omnix_core/governance/avm_engine.py` (2 blocks — disk glob failures)
- `omnix_core/governance/assumption_validity_monitor.py` (1 block — disk glob)
- `omnix_core/governance/meta_coherence_monitor.py` (2 blocks — datetime/json parse)
- `omnix_core/governance/trajectory_invariant_engine.py` (1 block — rollback failure)
- `omnix_services/governance_service/execution_integrity.py` (4 blocks — violation logging, decision recording, DB query)
- `omnix_services/risk_management/position_monitor.py` (2 blocks — balance/stats queries)
- `omnix_services/monitoring/risk_guardian.py` (1 block — timestamp parse with fallback)

**Log level policy:**
- `logger.debug`: Non-critical fallback paths where a safe default is applied (glob, date parse)
- `logger.warning`: Governance-critical paths where silence obscures operational issues (violation logging, DB queries)

---

## 6. Theoretical Foundation — Dual-Layer Governance Drift

*The following conceptual framework was articulated by Dr. Amanulla Khan (Honorary Doctorate) in correspondence with OMNIX QUANTUM LTD, 25 Apr 2026. It provides the institutional governance theory that informs the AVM design decisions documented above.*

---

### The dual-layer drift problem

In environments with multiple simultaneous governance layers — such as commercial compliance operating alongside a Sharia evaluative layer in UAE financial institutions — a stabilizing effect emerges when the secondary layer maintains genuine **reference independence** from the primary operational environment. The secondary layer generates evaluative friction: it slows normalization capture because decisions are being assessed through more than one legitimacy frame at the same time.

The opposite risk, however, is equally real and harder to detect:

> *"If both layers gradually adapt to the same operational incentives or continuity pressures, the organization can begin experiencing synchronized drift across multiple governance frames while still interpreting itself as highly governed because of the visible presence of dual oversight structures."*
>
> — Dr. Amanulla Khan

This is the **synchronized capture failure mode**: an organization can accumulate cross-layer drift while maintaining the outward appearance of comprehensive governance. The multiplicity of layers increases *perceived* legitimacy without preserving *independent evaluative integrity*.

The critical diagnostic signal for this failure mode is the **disappearance of tension** across layers. When all governance layers agree without friction, it is not necessarily because the environment is clean — it may be because all layers have already absorbed the same bias.

---

### Mapping to OMNIX AVM architecture

| Institutional concept | OMNIX implementation |
|---|---|
| Secondary governance layer | `AssumptionValidityMonitor` — evaluates whether the statistical assumptions underlying trade decisions still hold |
| Reference independence | AVM snapshot: calibrated at a fixed point in time, not updated on every decision cycle. The baseline is anchored to *past* market conditions, not the current operational frame |
| Synchronized drift detection | `drift_threshold` comparison: AVM detects when live signals have moved away from the historical baseline, even when all other governance layers pass normally |
| Tension preservation | The `max_drift_for_auto` guard (80%): when drift is extreme, auto-recalibration is blocked. The AVM refuses to "harmonize" with the current operational environment under crisis conditions — it preserves the tension rather than resolving it |
| Normalization capture resistance | Auto-recalibration requires explicit human review when drift > 80%. The system does not silently absorb extreme drift by updating its own reference frame |
| Signal schema validation | If `live_signals` has no overlapping keys with `baseline_signals`, recalibration is blocked with `SIGNAL_SCHEMA_MISMATCH`. The AVM will not anchor to a structurally different signal environment without audit trail |

### Key design principle

The AVM is not designed to always agree with the current market state. It is designed to **preserve disagreement** when the current state has drifted significantly from the calibrated baseline — because that disagreement is itself the governance signal.

Auto-recalibration is permitted only within the 0–80% drift band, where normal market evolution is the most likely explanation. Beyond that threshold, the AVM remains out of step with the current environment intentionally — because agreement at extreme drift levels would indicate the secondary layer has been captured by the same operational frame it was designed to constrain.

This is the structural implementation of what Dr. Khan describes as the condition that makes parallel governance systems genuinely stabilizing rather than merely visible:

> *"Parallel governance systems seem stabilizing only as long as they preserve enough separation to generate unresolved tension when drift begins emerging in the primary execution environment."*

---

## 7. Consequences

- AVM recalibration is now automatic and observable via logs
- External audit tooling can call `AVMEngine` without AVM internal knowledge
- All governance gate results are fail-safe by default (no implicit admission)
- TESTING bypass cannot activate in Railway production deployments
- 0 silent exception swallows remain in core governance path
- AVM is architecturally designed to preserve governance tension, not resolve it — consistent with dual-layer governance theory
