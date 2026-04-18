# ADR-059: Executive Audit Dashboard

**Status:** Accepted  
**Date:** 2026-04-06  
**Author:** Harold Nunes  
**Deciders:** Harold Nunes (Founder), Architect review

---

## Context

OMNIX issues a post-quantum cryptographic receipt for every governance decision across all 4 active verticals (Trading, Islamic Credit, Insurance, Robotics). These receipts contain the full `veto_chain` — a technical trace of every checkpoint that ran, including internal signal names, raw scores, and threshold values.

This technical format is meaningful for engineers and auditors but **illegible for CFOs, board members, and regulators** who need to understand governance outcomes without interpreting quantitative internals. A CFO should not need to know that `risk_exposure=78 >= 65 -> BLOCK` means the trade was blocked due to excessive institutional risk exposure.

Additionally, exposing raw scores and thresholds publicly constitutes **intellectual property risk** — the threshold calibration is a core proprietary asset of the OMNIX governance engine.

---

## Decision

Implement an **Executive Audit Dashboard** (`/audit`) that:

1. **Translates** the raw `veto_chain` to plain business-language checkpoint outcomes using a server-side sanitization layer — no scores, thresholds, or internal signal names are exposed.
2. **Exposes a protected API endpoint** (`GET /api/governance/audit/decisions`) authenticated via existing RBAC/API key infrastructure (ADR-055), returning sanitized decision records.
3. **Exposes a public demo endpoint** (`GET /api/public/audit-demo`) that returns anonymized synthetic data for prospective clients — no real data, no authentication required.
4. **Presents** a dedicated React page with KPI bar, domain breakdown, decision table, and detail panel showing checkpoint outcomes in executive language plus cryptographic integrity badges.

---

## Architecture

### Backend — `omnix_web/api/gov_blueprint.py`

#### Translation Layer

A server-side `_parse_veto_chain_executive()` function parses each veto_chain entry using regex to extract:
- `checkpoint_id` (e.g., `CP-2`)
- `status` (PASS or BLOCKED)

It then maps each checkpoint to:
- `label`: Human-readable name (e.g., `Institutional Risk Limits`)
- `executive_reason`: Business-language explanation (e.g., `Risk exposure exceeded the institutional risk limits in force.`)

**What is NEVER exposed to the API consumer:**
- Raw scores (`risk_exposure=78`)
- Threshold values (`>= 65`)
- Operator symbols (`>=`, `<=`)
- Internal signal names (`risk_exposure`, `probability_score`, `signal_coherence`)
- Algorithm names beyond the NIST standard label

#### Protected Endpoint

```
GET /api/governance/audit/decisions
Authorization: X-API-Key <key>
Filters: domain, decision, date_from, date_to, limit, offset
```

Returns:
```json
{
  "success": true,
  "kpis": { "total_decisions": ..., "approved_pct": ..., "by_domain": [...] },
  "items": [{
    "receipt_id": "OMNIX-A3F829C14E72",
    "decision": "APPROVED",
    "executive_summary": "This decision was APPROVED after passing all 11 institutional governance checkpoints.",
    "checkpoint_outcomes": [
      { "checkpoint_id": "CP-2", "label": "Institutional Risk Limits", "status": "PASS", "executive_reason": "Risk exposure validated within institutional limits." }
    ],
    "integrity": { "signature_standard": "NIST-standardized post-quantum algorithms", "pqc_signed": true, "chain_linked": true }
  }]
}
```

#### Public Demo Endpoint

```
GET /api/public/audit-demo
(No authentication)
```

Returns 12 anonymized synthetic records across all 4 domains. Clearly marked with `"demo": true` and `"note": "Demo data — anonymized synthetic records."`.

### Frontend — `omnix_web/src/pages/AuditDashboard.tsx`

- Route: `/audit`
- Navigation entry: InvestorCommandCenter → "Executive Audit" link
- Components: KPI bar, domain breakdown grid, decision table (filterable by domain and decision), sticky detail panel with checkpoint outcomes and integrity section
- Default mode: Public demo data (no API key needed)
- Demo badge visible when using public endpoint
- Dark theme consistent with InvestorCommandCenter (`#050D18` background, OMNIX gold `#C9A227` accent)

---

## Consequences

### Positive

- **Investor/client facing:** A CFO or regulatory officer can now audit OMNIX decisions without technical interpretation
- **IP protected:** No proprietary thresholds, scores, or internal signal names are exposed in the API response
- **Demo-ready:** Any visitor to the site can see the audit dashboard without an API key — accelerates sales conversations
- **Integrity visible:** Each decision shows a PQC signed badge and chain-linked status, making cryptographic governance tangible to non-technical stakeholders
- **Builds on existing infrastructure:** Reuses `decision_receipts` table (already populated), RBAC/API key system (ADR-055), and the InvestorCommandCenter design system

### Negative / Trade-offs

- The executive language translation is necessarily approximate — a regulatory audit requiring full technical detail still needs direct DB access or the raw `/api/governance/receipts` endpoint (authenticated)
- Demo endpoint uses synthetic data — real data requires API key provisioning (acceptable friction)

---

## Related ADRs

- ADR-044: Quantum-Secure Decision Receipts (data source)
- ADR-055: API Key RBAC (authentication layer reused)
- ADR-057: Critical Override Layer (override events visible in audit)
- ADR-058: Bot Governance Integration (bot `/recibo` command complements this dashboard)
- ADR-026: Multi-Vertical Governance Architecture (4 domains shown in audit)
