# ADR-028: External Signal Evaluation API

**Status**: ACCEPTED  
**Date**: February 27, 2026  
**Author**: Harold Nunes, OMNIX  
**Category**: Architecture / Product / B2B  
**Depends on**: ADR-026 (Multi-Vertical Governance Architecture), ADR-027 (Decision Governance Infrastructure)

---

## Context

ADR-026 established the Domain Adapter pattern — the architectural insight that OMNIX's 6-checkpoint governance engine is domain-agnostic. Any system can supply normalized signals and receive a governance decision. ADR-027 declared OMNIX's market positioning as "Decision Governance Infrastructure for Automated Systems."

Both decisions were architectural and strategic. This ADR delivers the first external-facing implementation: a REST API endpoint that allows any external automated system — a quantitative fund's algo, a credit decisioning engine, an insurance underwriting platform — to submit normalized signals, receive an evaluation through OMNIX's fail-closed 6-checkpoint pipeline, and obtain a PQC-signed governance receipt as cryptographic proof of the decision.

This endpoint is the core B2B product. It is what clients pay $2K–$5K/month to access.

---

## Decision

Implement `POST /api/governance/evaluate` as a production endpoint in the Flask Dashboard service. The endpoint:

1. Accepts 6 normalized signals (0–100 scale) plus optional metadata
2. Runs them through the fail-closed `GovernanceEvaluationEngine` (6 checkpoints)
3. Generates a Dilithium-3–signed governance receipt via the existing `DecisionReceiptEngine`
4. Stores the receipt in PostgreSQL (hash-chained to all previous receipts)
5. Returns the full receipt with gate results, veto chain, and public verification URL

---

## Architecture

```
External Client (B2B)
        │
        ▼  POST /api/governance/evaluate
        │  Headers: X-API-Key: <client_key>
        │
        ▼
Flask Dashboard (Port 5000)
        │
        ├── Rate limit: 10 req/min per IP
        ├── Input validation: 6 signals, values 0-100
        │
        ▼
GovernanceEvaluationEngine          ← omnix_core/governance/external_evaluator.py
  ├── CP-1: Probability Check       (probability_score ≥ 50)
  ├── CP-2: Risk Limits             (risk_exposure ≤ 65)
  ├── CP-3: Signal Coherence        (signal_coherence ≥ 55)
  ├── CP-4: Trend Persistence       (trend_persistence ≥ 50)
  ├── CP-5: Stress Resilience       (stress_resilience ≥ 35)
  └── CP-6: Logic Consistency       (logic_consistency ≥ 40)
        │
        │  Fail-closed: any gate failure → BLOCKED
        │
        ▼
DecisionReceiptEngine               ← omnix_core/evidence/decision_receipt.py (existing)
  ├── SHA-256 hash chain
  ├── Dilithium-3 signature
  └── Store in PostgreSQL (decision_receipts table)
        │
        ▼
Response to client
```

---

## Signal Schema

All signals are numeric values in the range **[0, 100]**. The meaning of each signal is domain-agnostic — the client's domain adapter translates raw data to these normalized values.

| Signal | Range | Pass Condition | Domain Trading Example | Domain Credit Example |
|--------|-------|---------------|----------------------|----------------------|
| `probability_score` | 0–100 | ≥ 50 | MC win probability | Credit repayment probability |
| `risk_exposure` | 0–100 | ≤ 65 | Portfolio VaR% | Debt-to-income ratio |
| `signal_coherence` | 0–100 | ≥ 55 | EMA/HMM agreement | Score model consensus |
| `trend_persistence` | 0–100 | ≥ 50 | Regime stability | Payment history consistency |
| `stress_resilience` | 0–100 | ≥ 35 | Black swan resilience | Adverse scenario survival |
| `logic_consistency` | 0–100 | ≥ 40 | DCI (inverted) | Internal scorecard consistency |

**Fail-closed**: if any signal fails its checkpoint, the decision is `BLOCKED`. No override path exists.

---

## Request Format

```http
POST /api/governance/evaluate
Content-Type: application/json
X-API-Key: <your_api_key>

{
  "asset": "BTC/USD",
  "domain": "trading",
  "signals": {
    "probability_score": 72,
    "risk_exposure": 35,
    "signal_coherence": 68,
    "trend_persistence": 81,
    "stress_resilience": 45,
    "logic_consistency": 78
  },
  "metadata": {
    "source": "client_algo_v1",
    "requested_action": "BUY",
    "portfolio_id": "FUND-A"
  }
}
```

---

## Response Format

```json
{
  "receipt_id": "OMNIX-A3F7B2C91D4E",
  "timestamp": "2026-02-27T14:30:00.000Z",
  "asset": "BTC/USD",
  "domain": "trading",
  "decision": "APPROVED",
  "checkpoints_total": 6,
  "checkpoints_passed": 6,
  "checkpoints_blocked": 0,
  "gate_results": [
    {
      "checkpoint": "CP-1",
      "name": "Probability Check",
      "signal": "probability_score",
      "score": 72.0,
      "threshold": 50,
      "condition": "72.0 ≥ 50",
      "result": "PASS",
      "description": "Expected positive outcome probability must meet minimum threshold."
    }
  ],
  "veto_chain": [],
  "decision_trace": [
    "CP-1 Probability Check: 72.0 ≥ 50 → PASS",
    "CP-2 Risk Limits: 35.0 ≤ 65 → PASS"
  ],
  "content_hash": "sha256:a3f7b2c91d4e...",
  "signature": "Dilithium3_base64_encoded_signature...",
  "signature_algorithm": "Dilithium-3 (ML-DSA-65)",
  "verifiable_at": "https://omnibotgenesis-production.up.railway.app/verify",
  "policy_version": "6.5.4e"
}
```

---

## Additional Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/governance/evaluate` | POST | Required | Submit signals, receive receipt |
| `/api/governance/schema` | GET | None | Signal schema and checkpoint documentation |

---

## Authentication & Multi-Tenant

**API Key**: The endpoint uses a dedicated `B2B_API_KEY` environment variable. Required header:
```
X-API-Key: <your_b2b_api_key>
```
In Railway production, `B2B_API_KEY` must be configured. In development (unset), the endpoint is open.

**Client Identification**: Each request may include an optional `X-Client-ID` header (max 64 chars):
```
X-Client-ID: quant-fund-alpha-01
```
This value is stored in `decision_receipts.client_id` and `shadow_trade_events.client_id`, enabling per-client data segmentation and audit queries. Defaults to `"anonymous"` if omitted.

---

## Rate Limiting

- 10 requests per minute per IP (more restrictive than general endpoints — evaluation is computationally meaningful)
- Returns HTTP 429 with reference ID on limit exceeded

---

## Demo — curl Examples

### APPROVED Decision
```bash
curl -s -X POST https://omnix-dashboard.up.railway.app/api/governance/evaluate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_b2b_api_key" \
  -H "X-Client-ID: quant-fund-alpha-01" \
  -d '{
    "asset": "BTC/USD",
    "domain": "trading",
    "signals": {
      "probability_score": 72,
      "risk_exposure": 35,
      "signal_coherence": 68,
      "trend_persistence": 81,
      "stress_resilience": 45,
      "logic_consistency": 78
    }
  }' | python3 -m json.tool
```

### BLOCKED Decision (risk_exposure too high)
```bash
curl -s -X POST https://omnix-dashboard.up.railway.app/api/governance/evaluate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_b2b_api_key" \
  -H "X-Client-ID: credit-desk-01" \
  -d '{
    "asset": "LOAN-2847",
    "domain": "credit",
    "signals": {
      "probability_score": 65,
      "risk_exposure": 78,
      "signal_coherence": 60,
      "trend_persistence": 55,
      "stress_resilience": 40,
      "logic_consistency": 50
    }
  }' | python3 -m json.tool
```

### Schema (no auth required)
```bash
curl -s https://omnix-dashboard.up.railway.app/api/governance/schema | python3 -m json.tool
```

---

## Data Governance

### Payload Encryption at Rest

Client signal payloads are encrypted before storage using **Fernet** (AES-128-CBC + HMAC-SHA256).

- **Config**: Set `PAYLOAD_ENCRYPTION_KEY` in Railway Variables (generate with `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
- **Storage**: `decision_receipts.encrypted_payload` (TEXT, nullable)
- **Dev mode**: If key not set, column is NULL — signals are not stored in plaintext
- **Response field**: `payload_encrypted: true/false`

> **Due diligence statement**: "Client signal data is encrypted at rest at the application layer using AES-128-CBC with HMAC-SHA256 integrity verification. Encryption keys are managed exclusively via environment secrets."

### Data Retention

Each receipt receives `retention_until = created_at + 365 days` (12-month default, configurable per contract).

See full policy: `docs/operations/DATA_RETENTION_POLICY.md`

### Database Schema — New Columns

```sql
ALTER TABLE decision_receipts ADD COLUMN client_id VARCHAR(64);
ALTER TABLE decision_receipts ADD COLUMN encrypted_payload TEXT;
ALTER TABLE decision_receipts ADD COLUMN retention_until DATE;
ALTER TABLE shadow_trade_events ADD COLUMN client_id VARCHAR(64);
```

---

## Consequences

### Positive
- OMNIX becomes an **external governance service** — not just self-contained infrastructure
- B2B product is demonstrable with a single curl command
- Every evaluation generates a PQC-signed receipt stored in the hash chain — audit trail grows with client usage
- Domain-agnostic: same endpoint works for trading, credit, insurance, supply chain
- Verifiable at public URL — clients can show auditors cryptographic proof of governance
- **Multi-tenant from day one**: `client_id` enables per-client data segmentation
- **Encryption at rest**: Fernet-encrypted payloads — defensible in due diligence
- **Retention policy**: 12-month default, configurable per contract

### Constraints
- ~~Thresholds are currently fixed (`CHECKPOINT_DEFAULTS`). Post-investment, per-client thresholds are a premium feature.~~ **→ IMPLEMENTED in ADR-037 (March 11, 2026)**: Per-client configurable thresholds are now live. See [ADR-037](ADR-037-per-client-configurable-thresholds.md) for schema, safety floors, and admin API.
- The endpoint does not fetch market data — signal generation is the client's responsibility.
- `B2B_API_KEY` must be configured in Railway for production security.
- Fernet key rotation requires re-encryption of stored payloads — operational procedure to be defined pre-scale.

---

## Implementation Files

| File | Purpose |
|------|---------|
| `omnix_core/governance/external_evaluator.py` | GovernanceEvaluationEngine — 6-checkpoint logic |
| `omnix_core/governance/__init__.py` | Module init |
| `omnix_dashboard/blueprints/governance.py` | Flask blueprint — POST/GET endpoints, B2B auth, multi-tenant, Fernet encryption |
| `omnix_dashboard/blueprints/__init__.py` | Export governance_bp |
| `omnix_dashboard/app.py` | Blueprint registration |
| `omnix_core/evidence/decision_receipt.py` | store_receipt() — persists client_id, encrypted_payload, retention_until |
| `docs/operations/DATA_RETENTION_POLICY.md` | Full data retention and client rights policy |

---

*OMNIX Decision Governance Infrastructure — ADR-028 (Updated Feb 27, 2026)*  
*Internal Build Reference: 6.5.4e*
