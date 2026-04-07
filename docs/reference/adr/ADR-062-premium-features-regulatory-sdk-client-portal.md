# ADR-062: Premium Features — Regulatory Mapping, Due Diligence Package, SDKs, Client Portal

**Date:** 2026-04-07
**Status:** Accepted
**Author:** Harold Nunes — OMNIX Quantum

---

## Context

OMNIX needed four competitive differentiators to pull ahead of adjacent players (SASI, AEGIS, Fallon/HUMYN):
1. Regulatory mapping — explicitly link governance checkpoints to specific regulations
2. Due diligence package — auto-generate a premium PDF for M&A/PE use
3. Integration SDKs — reduce client onboarding from weeks to 10 lines of code
4. Client portal — real-time governance dashboard accessible with API key

---

## Decisions

### 1. Regulatory Mapping Engine (`omnix_engine/regulatory_mapping.py`)

Maps all 11 checkpoints to 8 regulatory frameworks:
- **EU AI Act** — Articles 5, 9, 10, 14, 15, 26
- **DORA** (EU 2022/2554) — Articles 6, 8, 9, 13, 17, 26, 45
- **NIST AI RMF 1.0** — GOVERN, MAP, MEASURE function categories
- **ISO 42001:2023** — Clauses 4, 6, 8, 9
- **CA SB 243** — Sections 2–6
- **GDPR** — Article 22 (Automated Decision-Making)
- **FATF** — Recommendation 10 (Customer Due Diligence)
- **Basel III** — Pillars 1, 2 (Operational Risk)

Every evaluation response now includes `regulatory_alignment` with:
- `frameworks_covered` (int)
- `frameworks` (list with full_name, status, applies_to)
- `checkpoint_mapping` (per-CP list with status and frameworks_enforced)
- `attestation_note` (ready-to-paste text for compliance docs)

**Public endpoint:** `GET /api/governance/regulatory/catalog` — no auth required.

### 2. Due Diligence PDF Generator (`omnix_engine/due_diligence.py`)

**Endpoint:** `GET /api/governance/due-diligence-report?format=pdf&days=30`
**Auth:** X-API-Key (client or admin)

Generates a premium PDF using reportlab with:
- OMNIX branded header/footer (logo, dark theme)
- KPI bar: Total decisions, Approved, Blocked, Approval Rate
- Domain breakdown with progress bars
- 11-checkpoint regulatory coverage table (CP → frameworks)
- Regulatory framework catalog cards
- Recent governance receipts table
- Cryptographic attestation statement

Also available as `format=json` for programmatic consumption.

### 3. Python SDK (`omnix_sdk/python/omnix_sdk.py`)

Drop-in Python client. No external dependencies (uses stdlib only).
Methods: `evaluate()`, `get_receipt()`, `list_receipts()`, `get_regulatory_catalog()`, `get_due_diligence_report()`.
Error classes: `OmnixAuthError`, `OmnixRateLimitError`, `OmnixAPIError`.

### 4. Node.js SDK (`omnix_sdk/node/index.js`)

Drop-in Node.js client. No external dependencies (uses `https`/`http` stdlib).
Methods: `evaluate()`, `getReceipt()`, `listReceipts()`, `getRegulatoryFrameworks()`, `getDueDiligenceReport()`.
Same error classes pattern as Python SDK.

### 5. Client Portal (`/client` — `ClientDashboard.tsx`)

Authentication: API key input (OMNIX- format). Stored only in component state, never persisted.
Sections:
- KPI bar: Total/Approved/Blocked/Frameworks
- Time period selector: 7d / 30d / 90d
- Domain breakdown bar chart
- Regulatory coverage badges (all 8 frameworks)
- Recent receipts table with decision badges
- Cryptographic attestation block
- Integrated SDK quick-start (Python + Node with key pre-filled)
- Due diligence PDF download button

---

## Files Affected

```
omnix_web/api/omnix_engine/regulatory_mapping.py   # NEW — 8 frameworks, 11 CPs
omnix_web/api/omnix_engine/due_diligence.py        # NEW — PDF generator
omnix_web/api/gov_blueprint.py                      # MODIFIED — 3 additions:
                                                    #   - regulatory_alignment in evaluate response
                                                    #   - GET /api/governance/regulatory/catalog
                                                    #   - GET /api/governance/due-diligence-report
omnix_web/src/pages/ClientDashboard.tsx             # NEW — /client portal
omnix_web/src/App.tsx                               # MODIFIED — Route /client added
omnix_web/src/pages/InvestorCommandCenter.tsx       # MODIFIED — "Client Portal" link added
omnix_sdk/python/omnix_sdk.py                       # NEW — Python SDK
omnix_sdk/python/README.md                          # NEW
omnix_sdk/node/index.js                             # NEW — Node.js SDK
omnix_sdk/node/README.md                            # NEW
docs/reference/adr/ADR-062-*.md                    # THIS FILE
```

---

## Competitive Impact

| Feature | SASI | AEGIS | Fallon | OMNIX |
|---------|------|-------|--------|-------|
| Regulatory mapping (explicit articles) | ✗ | ✗ | ✗ | ✓ |
| Auto due diligence PDF | ✗ | ✗ | ✗ | ✓ |
| Client-facing governance portal | ✗ | ✗ | unknown | ✓ |
| Python + Node.js SDK | ✗ | unknown | unknown | ✓ |
| PQC-signed receipts | ✗ | ✗ | ✗ | ✓ |

---

## No Breaking Changes

- `regulatory_alignment` added as new field to evaluate response — additive only.
- All new endpoints require auth (except `/regulatory/catalog` which is public).
- Existing endpoints, DB schema, and receipt format unchanged.
