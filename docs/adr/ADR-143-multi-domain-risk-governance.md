# ADR-143 — Multi-Domain Risk Governance Engine (MOD-013)

| Field       | Value                                     |
|-------------|-------------------------------------------|
| **Status**  | Accepted                                  |
| **Date**    | 2026-05-08                                |
| **Author**  | OMNIX Architecture Council                |
| **Module**  | MOD-013 / MDRG                            |
| **Layer**   | Governance — Cross-Domain Evaluation      |

---

## Context

All existing OMNIX governance engines are domain-specific (trading, Islamic credit, insurance, defense, etc.). Enterprise clients outside financial services — logistics, healthcare, manufacturing, public sector — need governance capabilities but do not fit any existing vertical.

Additionally, no current engine unifies **financial, technical, legal, and human** risk into a single governance score. Each of these dimensions is currently evaluated in isolation (AVM for financial thresholds, SAE for structural admissibility, jurisdiction gate for legal).

This creates two gaps:
1. Non-financial clients cannot use OMNIX without mapping their domain to a financial vertical.
2. There is no cross-vector risk governance score usable for enterprise-level reporting and control.

---

## Decision

Implement the **Multi-Domain Risk Governance Engine (MDRG)** at `omnix_core/governance/multi_domain_risk.py`.

### Four Risk Vectors

| Vector | Focus | Key Signals |
|--------|-------|-------------|
| **Financial** | Capital exposure, leverage, liquidity, credit | `capital_exposure_pct`, `leverage_ratio`, `liquidity_ratio`, `credit_score`, `concentration_pct` |
| **Technical** | System reliability, latency, dependencies | `uptime_pct`, `error_rate_pct`, `latency_p99_ms`, `dependency_failure_count`, `last_incident_hours` |
| **Legal** | Regulatory compliance, jurisdiction, litigation | `regulatory_violations`, `jurisdiction_risk_score`, `pending_litigation`, `license_expiry_days`, `aml_flag` |
| **Human** | Operator risk, oversight, fatigue, training | `operator_error_rate_pct`, `oversight_coverage_pct`, `fatigue_index`, `training_currency_days`, `escalation_backlog` |

### Scoring Architecture

Each vector produces a normalized risk score 0–100 (0 = no risk, 100 = maximum risk).

**Composite score** = weighted average:
- Default weights: financial=0.35, technical=0.25, legal=0.25, human=0.15
- Custom weights accepted per evaluation (normalized to sum to 1.0)

**Decision thresholds:**

| Score Range | Decision | Meaning |
|-------------|----------|---------|
| ≥ 80        | BLOCKED  | Risk exceeds governance threshold |
| 60 – 79     | REVIEW   | Elevated risk — human review required |
| < 60        | APPROVED | Within acceptable governance bounds |

**Hard block:** Any single vector ≥ 95 → BLOCKED regardless of composite score.

### Design Principles

1. **Rule-based scoring**: No ML model dependency. Full auditability of every signal → score mapping.
2. **Fail-closed (ADR-116)**: DB error during evaluation → `decision: BLOCKED`.
3. **PQC-signable**: Output schema is compatible with ADR-078 Dilithium-3 signing pipeline.
4. **Stateless scoring**: Each evaluation is independent. No prior state dependency.
5. **Client-supplied signals**: Clients provide domain-specific values; MDRG normalizes them.

### API Endpoints (4)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/governance/risk/evaluate` | API Key | Evaluate multi-domain risk |
| GET  | `/api/governance/risk/catalog`  | None   | Signal catalog + thresholds (public) |
| GET  | `/api/governance/risk/history`  | API Key | Paginated assessment history |
| GET  | `/api/governance/risk/summary`  | API Key | Aggregate statistics |

### Database

Table: `multi_domain_risk_assessments`

```sql
CREATE TABLE multi_domain_risk_assessments (
    id                SERIAL PRIMARY KEY,
    assessment_id     TEXT         NOT NULL UNIQUE,   -- MDRG-{hex12}
    subject           TEXT         NOT NULL,
    client_domain     TEXT,
    decision          TEXT         NOT NULL,           -- APPROVED | REVIEW | BLOCKED
    composite_score   NUMERIC(6,2) NOT NULL,
    financial_score   NUMERIC(6,2),
    technical_score   NUMERIC(6,2),
    legal_score       NUMERIC(6,2),
    human_score       NUMERIC(6,2),
    hard_block_vector TEXT,
    weights_used      JSONB,
    signals           JSONB,
    breakdown         JSONB,
    assessed_by       TEXT,
    assessed_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

### SDK Support

Added to Python SDK (`OmnixClient`):
- `risk_evaluate(subject, risk_signals, weights, client_domain, assessed_by)`
- `risk_catalog()` — public, no auth
- `risk_history(subject, client_domain, decision, limit, offset)`
- `risk_summary(client_domain)`

Added to Node.js SDK (`OmnixClient`): matching TypeScript methods.

### Frontend

Dashboard page: `/risk` — `omnix_web/src/pages/RiskDashboard.tsx`
- Aggregate KPIs (total, approved, review, blocked)
- Average vector score bars
- Filterable assessment table with per-vector breakdown
- 15-second auto-refresh

---

## Usage Example

```python
from omnix import OmnixClient

client = OmnixClient(api_key="OMNIX-...")
result = client.risk_evaluate(
    subject="ACME_LOGISTICS_DEPLOYMENT_42",
    risk_signals={
        "financial": {
            "capital_exposure_pct": 35,
            "liquidity_ratio":      2.5,
            "leverage_ratio":       3.0,
        },
        "technical": {
            "uptime_pct":      99.5,
            "error_rate_pct":  0.2,
            "latency_p99_ms":  180,
        },
        "legal": {
            "regulatory_violations":   0,
            "jurisdiction_risk_score": 5,
            "aml_flag":                0,
        },
        "human": {
            "oversight_coverage_pct": 92,
            "fatigue_index":          15,
            "operator_error_rate_pct": 0.8,
        },
    },
    client_domain="logistics",
)

print(result["decision"])        # APPROVED
print(result["composite_score"]) # 24.7
print(result["assessment_id"])   # MDRG-A3F8...
```

---

## Consequences

**Positive:**
- OMNIX can now serve non-financial clients (logistics, manufacturing, healthcare, public sector).
- Unified cross-vector risk score enables enterprise-level governance dashboards.
- Rule-based scoring is fully auditable — no black-box ML.
- Extensible: new vectors can be added without breaking existing clients (all vectors are opt-in).

**Negative / Trade-offs:**
- Signal normalization heuristics (e.g., `uptime_pct` → risk score) will need calibration per client.
- Default weights are generic — enterprise clients should supply custom weights via the `weights` parameter.
- Does not integrate with AVM per-domain calibration (intentional: MDRG is cross-domain by design).

---

## Regulatory Alignment

| Framework | Provision | MDRG Mapping |
|-----------|-----------|--------------|
| NIST AI RMF | MP-2.3, MS-2.5 | Risk categorization + monitoring |
| EU AI Act | Art. 9 | Risk management for high-risk AI |
| ISO 31000 | §6 | Risk management — general principles |
| ISO/IEC 42001 | §8.4 | AI management — risk treatment |

---

## Related ADRs

- ADR-116: Fail-Closed Policy (inherited)
- ADR-138: UDCL v1.x (MDRG output can be fed as a pillar via `metadata`)
- ADR-141: Module API Wiring (predecessor to this ADR)
- ADR-142: Breach Containment Engine (co-delivered with this ADR)
- ADR-134: Oscillation Insight Engine (peer: time-series governance analytics)
