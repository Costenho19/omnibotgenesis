# ADR-141 — Module API Wiring: Oscillation Engine, Anomaly Response, Execution Integrity, Context Admission Gate

**Status:** Active  
**Date:** 2026-05-07  
**Author:** Harold Alberto Nunes Rodelo, OMNIX QUANTUM LTD  
**Builds on:** ADR-050 (CAG), ADR-129 (ARE), ADR-131 (EIL), ADR-134 (OIE), ADR-138 (UDCL)

---

## 1. Context

Four production-grade governance modules existed as fully implemented Python files
but were not connected to the public API or the Unified Decision Control Layer (UDCL)
pipeline. This created a gap between the theoretical governance architecture and what
was actually accessible to B2B clients and institutional evaluators.

Modules affected:

| Module | ADR | File |
|---|---|---|
| OscillationInsightEngine | ADR-134 | `omnix_core/governance/oscillation_insight.py` |
| AnomalyResponseEngine | ADR-129 | `omnix_core/governance/anomaly_response.py` |
| Execution Integrity Layer | ADR-131 | `omnix_web/api/omnix_engine/execution_receipt.py` |
| Context Admission Gate | ADR-050 | `omnix_core/governance/context_admission_gate.py` |

---

## 2. Decisions

### 2.1 OscillationInsightEngine (ADR-134) → Public API

**Endpoint:** `GET /api/analytics/oscillation`  
**Authentication:** None — aggregated metrics only, no PII.  
**Headers:** `X-OMNIX-ADR: ADR-134`, `Cache-Control: no-cache`

| Parameter | Type | Default | Values |
|---|---|---|---|
| `domain` | string | all | trading, credit, insurance, … |
| `num_weeks` | int | 8 | 1–26 |
| `view` | string | full | full \| profile \| phases \| asymmetry \| dampening |

**Views:**
- `full` — `oscillation_report()`: all four methods + executive summary (risk level: LOW/MEDIUM/HIGH/CRITICAL)
- `profile` — `oscillation_profile()`: HOLD rate pattern (CYCLING/DRIFTING/SETTLING/STABLE)
- `phases` — `phase_segmented_analysis()`: regime-change boundary detection
- `asymmetry` — `hesitation_asymmetry()`: processing latency by decision type
- `dampening` — `dampening_curve()`: oscillation amplitude trend (DAMPENING/AMPLIFYING/STABLE)

**Fail-safe:** Returns `{"available": false}` on DB unavailability.  
**Design rationale:** Read-only analytics — no governance pipeline impact.

---

### 2.2 AnomalyResponseEngine (ADR-129) → Six Authenticated Endpoints

**Authentication:** X-API-Key (B2B clients).  
**Header:** `X-OMNIX-ADR: ADR-129`

| Method | Path | Description |
|---|---|---|
| POST | `/api/governance/anomaly/response` | Full cycle: detect anomalies → generate recommendations → persist |
| GET  | `/api/governance/anomaly/active` | List ACTIVE recommendations (filterable by domain) |
| GET  | `/api/governance/anomaly/summary` | Count by status and action_code |
| GET  | `/api/governance/anomaly/history` | Full history all statuses (limit/offset) |
| POST | `/api/governance/anomaly/<rec_id>/acknowledge` | ACTIVE → ACKNOWLEDGED |
| POST | `/api/governance/anomaly/<rec_id>/resolve` | ACTIVE\|ACKNOWLEDGED → RESOLVED |

**Lifecycle:** `ACTIVE → ACKNOWLEDGED → RESOLVED | EXPIRED`  
**Design principle:** Every output is a recommendation, never a forced action. No governance layer is bypassed automatically.

---

### 2.3 Execution Integrity Layer (ADR-131) → Three Authenticated Endpoints

**Authentication:** X-API-Key (B2B clients).  
**Header:** `X-OMNIX-ADR: ADR-131`

| Method | Path | Description |
|---|---|---|
| POST | `/api/governance/execution/intent` | Log ExecutionIntent PRE-order (Invariant 2) |
| GET  | `/api/governance/execution/receipts` | List execution receipts (filterable by decision_receipt_id, status) |
| GET  | `/api/governance/execution/receipts/<order_id>` | Fetch single receipt with full audit_trail |

**Three invariants (ADR-131, non-negotiable):**
1. **No silent execution** — every execution path produces a verifiable ExecutionReceipt.
2. **Pre-intent captured** — intent logged to DB BEFORE order sent. If this fails, trade MUST NOT proceed.
3. **Decision binding** — every ExecutionReceipt carries `decision_receipt_id` linking to the authorising governance decision.

**Audit chain:** `decision_receipt → execution_intent → execution_receipt`

---

### 2.4 Context Admission Gate (ADR-050) → UDCL Layer 0d

The CAG is now wired into the UDCL pipeline as **Layer 0d**, positioned after CBG
(Layer 0c) and before the 11-checkpoint pipeline (Layer 1-2).

**UDCL execution order (updated):**
```
SAE (Layer 0) → SPG (Layer 0b) → [CBG (Layer 0c)] → [CAG (Layer 0d)] → CP (Layer 1-2) → PQC (Layer 3) → SBE (Layer 4) → [CTAG (Layer 5)]
```

**Activation:** `cag_enabled=true` in `POST /api/governance/control/evaluate` request body.

**Market condition parameters** (via `metadata` dict):

| Key | Type | Description |
|---|---|---|
| `metadata.cag_volatility` | float 0–100 | Composite volatility index |
| `metadata.cag_correlation` | float 0–100 | Cross-pair correlation |
| `metadata.cag_liquidity` | float 0–100 | Liquidity score (higher = more liquid) |
| `metadata.cag_macro_risk` | float 0–100 | Composite macro risk |

**Fail-closed:** Any exception during CAG evaluation → BLOCKED (ADR-116).  
**Disabled path:** When `cag_enabled=false`, Layer 0d is skipped entirely (zero pipeline impact).

---

## 3. UDCL Schema Version Bump

`UnifiedDecisionControlLayer.VERSION`: `"1.0.0"` → `"1.2.0"`

Changes:
- PILLAR_CATALOG: CAG entry added (`"context_admission_gate"`, Layer 0d)
- `evaluate()`: `cag_enabled`, `ctag_enabled` parameters added
- `get_schema()`: `cag_enabled` documented in `request_body`
- `get_schema()`: CAG design invariant added
- `check_pillar_health()`: CAG health check added

---

## 4. Compliance Alignment

| Endpoint / Module | Regulatory Basis |
|---|---|
| OIE (ADR-134) | NIST AI RMF: temporal model governance monitoring |
| ARE (ADR-129) | EU AI Act Art. 9: risk management response procedures |
| EIL (ADR-131) | MiFID II, SEC Rule 17a-4, CFTC audit trail requirements |
| CAG (ADR-050) | MiFID II: circuit breaker obligations; NIST AI RMF: context-aware governance |

---

## 5. Fail-Safe Guarantees

| Module | On Error |
|---|---|
| OIE | `{"available": false}` — zero governance impact |
| ARE | `{"available": false}` — recommendations not persisted, response returned |
| EIL (intent log) | 503 returned — caller MUST NOT proceed with trade (ADR-131 §Invariant 2) |
| EIL (receipt list) | 503 returned — read-only failure |
| CAG in UDCL | `BLOCKED` — fail-closed per ADR-116 |

---

## 6. Changelog

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-05-07 | Initial wiring of all 4 modules: OIE, ARE, EIL, CAG into UDCL |
