# ADR-029: Governance Compliance Modules

**Status**: ACCEPTED  
**Date**: 2026-03-01  
**Author**: Harold Nunes, CEO — OMNIX Quantum  
**Internal Build Reference**: 6.5.4e  
**Supersedes**: None (additive to ADR-028)  
**Related**: ADR-028 (External Governance API), ADR-022 (Post-Quantum Cryptography), ADR-023 (Track Record), ADR-024 (Investor Challenge Response)

---

## Context

OMNIX has operated a live External Governance API (ADR-028) since February 27, 2026, generating PQC-signed governance receipts for B2B clients. This infrastructure produces a growing corpus of decision data. However, the system lacked structured modules to:

1. **Map and classify risk** systematically per client/use-case (NIST AI RMF: MAP)
2. **Measure signal drift** and performance over time (NIST AI RMF: MEASURE)
3. **Record human oversight** actions on AI-blocked decisions (EU AI Act Art. 14)
4. **Manage governance incidents** in a traceable lifecycle (EU AI Act Art. 9 + 62)
5. **Generate compliance reports** with full decision lineage (EU AI Act Art. 12)

**Trigger**: Eureka Dubai GCC 2026 semifinals (March 15, 2026) require demonstrable regulatory maturity. Institutional due diligence partners require evidence that OMNIX governance is not just a claim — it is a structured, auditable system.

**Constraint**: All new modules must be ADDITIVE. Zero changes to existing tables, endpoints, or the PQC-signed decision receipt hash chain.

---

## Decision

Implement 5 governance compliance modules as a new layer above the existing External Governance API. Each module is domain-agnostic and aligns with recognized international AI governance standards.

### Regulatory Alignment Matrix

| Module | NIST AI RMF Function | ISO/IEC 42001 Clause | EU AI Act Article |
|--------|---------------------|---------------------|-------------------|
| 1. Risk Mapping | MAP | §6.1 — Risk identification | Art. 9 — Risk management system |
| 2. Measurement & Monitoring | MEASURE | §9.1 — Monitoring and measurement | Art. 9 — Performance monitoring |
| 3. Human Oversight | MANAGE | §8.4 — Human oversight | Art. 14 — Human oversight measures |
| 4. Incident Management | MANAGE | §10.2 — Nonconformity and corrective action | Art. 62 — Serious incident reporting |
| 5. Governance Reporting | GOVERN | §10.3 — Continual improvement | Art. 12 — Record-keeping |

---

## Architecture

### New Files

| Layer | File | Blueprint | Endpoint Prefix |
|-------|------|-----------|-----------------|
| Core Engine | `omnix_core/governance/risk_mapping.py` | — | — |
| Core Engine | `omnix_core/governance/measurement_monitoring.py` | — | — |
| Core Engine | `omnix_core/governance/human_oversight.py` | — | — |
| Core Engine | `omnix_core/governance/incident_management.py` | — | — |
| Core Engine | `omnix_core/governance/reporting_engine.py` | — | — |
| Flask Blueprint | `omnix_dashboard/blueprints/governance_risk.py` | `governance_risk_bp` | `/api/governance/risk-map` |
| Flask Blueprint | `omnix_dashboard/blueprints/governance_metrics.py` | `governance_metrics_bp` | `/api/governance/metrics`, `/api/governance/drift` |
| Flask Blueprint | `omnix_dashboard/blueprints/governance_oversight.py` | `governance_oversight_bp` | `/api/governance/overrides` |
| Flask Blueprint | `omnix_dashboard/blueprints/governance_incidents.py` | `governance_incidents_bp` | `/api/governance/incidents` |
| Flask Blueprint | `omnix_dashboard/blueprints/governance_reports.py` | `governance_reports_bp` | `/api/governance/reports` |

### New Database Tables

```sql
-- Module 1: Risk Mapping
CREATE TABLE governance_risk_map (
    id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id         TEXT NOT NULL,
    use_case          TEXT NOT NULL,
    classification    TEXT CHECK (classification IN ('CRITICAL','HIGH','MEDIUM','LOW')) NOT NULL,
    impact_financial  INTEGER CHECK (impact_financial BETWEEN 0 AND 100) DEFAULT 50,
    impact_operational INTEGER CHECK (impact_operational BETWEEN 0 AND 100) DEFAULT 50,
    impact_regulatory  INTEGER CHECK (impact_regulatory BETWEEN 0 AND 100) DEFAULT 50,
    stakeholders      JSONB DEFAULT '[]',
    thresholds        JSONB DEFAULT '{}',
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (client_id, use_case)
);

-- Module 2: Measurement & Monitoring
CREATE TABLE governance_metrics (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id     TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    approval_rate NUMERIC(5,2),
    block_rate    NUMERIC(5,2),
    avg_score     NUMERIC(5,2),
    window_start  TIMESTAMPTZ,
    window_end    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE governance_drift_log (
    id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id      TEXT NOT NULL,
    signal_name    TEXT NOT NULL,
    baseline_stats JSONB DEFAULT '{}',
    current_stats  JSONB DEFAULT '{}',
    drift_score    NUMERIC(6,3),
    threshold      NUMERIC(6,3) DEFAULT 2.0,
    alert_level    TEXT CHECK (alert_level IN ('ALERT','WARNING','OK')) DEFAULT 'OK',
    detected_at    TIMESTAMPTZ DEFAULT NOW(),
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Module 3: Human Oversight
CREATE TABLE governance_overrides (
    id                  UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id           TEXT NOT NULL,
    receipt_id          TEXT NOT NULL,
    decision_before     TEXT NOT NULL,
    decision_after      TEXT NOT NULL,
    justification       TEXT NOT NULL,
    overridden_by       TEXT NOT NULL,
    role                TEXT,
    signature           TEXT,
    signature_algorithm TEXT,
    public_key          TEXT,
    content_hash        TEXT,
    prev_hash           TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Module 4: Incident Management
CREATE TABLE governance_incidents (
    id                 UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id          TEXT NOT NULL,
    incident_id        TEXT UNIQUE NOT NULL,
    severity           TEXT CHECK (severity IN ('CRITICAL','HIGH','MEDIUM','LOW','INFORMATIONAL')) NOT NULL,
    title              TEXT NOT NULL,
    description        TEXT,
    related_receipt_id TEXT,
    status             TEXT CHECK (status IN ('OPEN','UNDER_REVIEW','RESOLVED','CLOSED')) DEFAULT 'OPEN',
    reported_by        TEXT,
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    resolved_at        TIMESTAMPTZ
);

CREATE TABLE governance_incident_reviews (
    id                 UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    incident_id        TEXT NOT NULL,
    reviewer           TEXT,
    findings           TEXT,
    corrective_actions JSONB DEFAULT '[]',
    reviewed_at        TIMESTAMPTZ DEFAULT NOW(),
    created_at         TIMESTAMPTZ DEFAULT NOW()
);

-- Module 5: Governance Reporting
CREATE TABLE governance_reports (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id    TEXT NOT NULL,
    period_start TIMESTAMPTZ,
    period_end   TIMESTAMPTZ,
    report_type  TEXT DEFAULT 'COMPLIANCE',
    content_json JSONB DEFAULT '{}',
    content_hash TEXT,
    generated_by TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

### API Endpoints

| Module | Method | Endpoint | Auth | Description |
|--------|--------|----------|------|-------------|
| Risk Mapping | GET | `/api/governance/risk-map` | any | List client risk maps |
| Risk Mapping | GET | `/api/governance/risk-map/<use_case>` | any | Get specific risk map |
| Risk Mapping | POST | `/api/governance/risk-map` | admin | Create/update risk map |
| Risk Mapping | POST | `/api/governance/risk-map/classify` | any | Classify signals in real-time |
| Measurement | GET | `/api/governance/metrics` | any | Stored metrics (last N days) |
| Measurement | GET | `/api/governance/metrics/live` | any | Live stats from decision_receipts |
| Measurement | POST | `/api/governance/metrics` | admin | Record manual metrics snapshot |
| Measurement | POST | `/api/governance/drift/detect` | any | Run drift detection |
| Measurement | GET | `/api/governance/drift/logs` | any | Drift history (?alert_only=true) |
| Human Oversight | POST | `/api/governance/overrides` | admin | Create PQC-signed override |
| Human Oversight | GET | `/api/governance/overrides` | any | List overrides with pagination |
| Human Oversight | GET | `/api/governance/overrides/<id>` | any | Override detail + integrity check |
| Incident Mgmt | POST | `/api/governance/incidents` | any | Report new incident |
| Incident Mgmt | GET | `/api/governance/incidents` | any | List incidents (status/severity filter) |
| Incident Mgmt | GET | `/api/governance/incidents/<id>` | any | Incident detail + reviews |
| Incident Mgmt | POST | `/api/governance/incidents/<id>/review` | admin | Add review |
| Incident Mgmt | POST | `/api/governance/incidents/<id>/resolve` | admin | Resolve incident |
| Reporting | POST | `/api/governance/reports` | any | Generate compliance report |
| Reporting | GET | `/api/governance/reports` | any | List reports (metadata) |
| Reporting | GET | `/api/governance/reports/<id>` | any | Full report |
| Reporting | GET | `/api/governance/reports/<id>/export` | any | Export JSON or CSV |
| Reporting | GET | `/api/governance/reports/<id>/lineage/<receipt_id>` | any | Decision lineage trace |

Authentication via `X-API-Key` header — same RBAC pattern as ADR-028 (`b2b_clients` table).

---

## Human Oversight Override Semantics (Critical)

An override created via `POST /api/governance/overrides` **does NOT modify** the `decision_receipts` table. The PQC-signed hash chain is immutable by design.

An override is a **complementary audit record** that documents:
- Which human authorized a departure from the AI system's governance recommendation
- Their documented justification (minimum 50 characters)
- A PQC signature over the override content (Dilithium-3 / ML-DSA-65)
- A SHA-256 content hash for integrity verification

Semantically: *"A qualified human reviewed BLOCKED receipt OMNIX-XXXX and authorizes execution of the underlying action for the following documented reasons..."*

This design satisfies EU AI Act Article 14 requirements while preserving the immutability guarantees of the hash chain (ADR-022).

---

## Risk Classification Logic (Module 1)

Deterministic rule-based classification — no ML:

| Condition | Classification |
|-----------|---------------|
| `probability_score < 30` OR `risk_exposure > 80` | CRITICAL |
| `probability_score < 50` OR `risk_exposure > 65` | HIGH |
| `probability_score < 70` OR `risk_exposure > 45` OR `signal_coherence < 40` OR `stress_resilience < 30` | MEDIUM |
| All signals within safe ranges | LOW |

---

## Drift Detection Logic (Module 2)

Statistical drift detection using z-score method:

```
drift_score = |current_mean - baseline_mean| / baseline_std
```

| drift_score | alert_level |
|-------------|-------------|
| ≥ 2.0 | ALERT |
| ≥ 1.0 | WARNING |
| < 1.0 | OK |

Baseline is sourced from historical `governance_metrics` entries for the same `checkpoint_id`. Falls back to `mean=50.0, std=15.0` if no baseline exists.

---

## Consequences

### Positive
- **Regulatory maturity**: Structured mapping to NIST AI RMF, ISO/IEC 42001, EU AI Act — all three major AI governance frameworks
- **Investor-ready reporting**: One API call generates a full compliance report exportable as JSON or CSV
- **Immutable audit trail**: Human overrides are PQC-signed, timestamped, and stored independently of the decision chain
- **Full decision lineage**: End-to-end trace from input signal → 6 checkpoints → decision → human override → public verification URL
- **Domain-agnostic**: All modules work for any B2B use case (trading, HealthTech, supply chain, lending)
- **Additive architecture**: Zero risk to existing system — no existing tables or endpoints modified

### Constraints
- Overrides are complementary records, not mutations of the immutable chain
- Drift detection requires at least 2 current values; baseline requires prior `governance_metrics` entries
- Report content_json is stored in PostgreSQL JSONB — very large periods may produce large payloads (use export endpoint for CSV)
- Module 3 PQC signing degrades gracefully if the DecisionReceiptEngine is unavailable (stores "UNSIGNED" flag)

---

## External Communication

When describing these modules to external audiences:
- Use: "Structured governance compliance aligned with NIST AI RMF and ISO/IEC 42001"
- Use: "Human oversight audit trail with post-quantum cryptographic signatures" (institutional)
- Use: "NIST-standardized algorithms" (public/bot tier)
- NEVER: "FIPS 203", "FIPS 204", "NIST Level 3", "Kyber-768 for encryption" (see ADR-022 PQC Communication Tier Rules)

---

*ADR-029 approved. Implementation complete: March 1, 2026.*
