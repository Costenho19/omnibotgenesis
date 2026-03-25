# ADR-049: Jurisdiction Compliance Gate (CP-11)

**Status:** ACCEPTED  
**Date:** March 25, 2026  
**Author:** Harold Nunes  
**Module:** `omnix_core/governance/jurisdiction_gate.py`

---

## Context

OMNIX operates globally and targets institutional clients in multiple jurisdictions with distinct regulatory frameworks. Each jurisdiction has different rules about which assets can be traded, what operation types are permitted, and which entities are sanctioned. Manual per-client configuration is error-prone and doesn't generate audit evidence.

CP-11 provides a configurable, PQC-audited jurisdictional compliance layer that automatically validates each decision against the active jurisdiction's rules, generating a cryptographic record of compliance.

---

## Decision

Implement CP-11 — the **Jurisdiction Compliance Gate** — as the final compliance checkpoint in the extended pipeline, positioned AFTER CP-10 (Fraud Gate).

### Design Principles

1. **Fail-safe by default** — disabled for all existing clients; exceptions → pass-through
2. **Activatable via env var** — `JURISDICTION_GATE_ENABLED=true` + `JURISDICTION=UAE`
3. **Jurisdiction-specific rule tables** — built-in defaults for UAE, EU, US, GCC, GLOBAL
4. **OFAC sanctions screening** — always applied when gate is enabled
5. **Zero impact on existing pipeline** — default OFF

---

## Implementation

### Module: `omnix_core/governance/jurisdiction_gate.py`

Three validation checks in sequence:

| Check | Rule | Behavior |
|-------|------|----------|
| **1. Sanctions screening** | Asset in OFAC/UN sanctions list | Hard VETO — `SANCTIONED_ASSET` |
| **2. Prohibited asset** | Asset in jurisdiction prohibited list | Hard VETO — `PROHIBITED_IN_{JURISDICTION}` |
| **3. Operation type** | Leverage/derivatives not permitted | Hard VETO — `LEVERAGE/DERIVATIVES_PROHIBITED` |

### Pipeline Position

```
CP-8 (ECW) → CP-9 (AML) → CP-10 (Fraud) → CP-11 (Jurisdiction Gate) ← NEW
```

### Jurisdiction Rule Table

| Jurisdiction | Spot | Leveraged | Derivatives | Prohibited Assets |
|-------------|------|-----------|-------------|-------------------|
| **UAE** | ✅ | ❌ | ❌ | XMR, ZEC, DASH, GRIN, BEAM, FIRO |
| **EU** | ✅ | ✅ | ✅ | XMR, GRIN, BEAM |
| **US** | ✅ | ❌ | ❌ | XMR, ZEC, DASH, GRIN, BEAM, FIRO, PIVX |
| **GCC** | ✅ | ❌ | ❌ | XMR, ZEC, DASH, GRIN, BEAM |
| **GLOBAL** | ✅ | ✅ | ✅ | (none) |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JURISDICTION_GATE_ENABLED` | `false` | Master enable switch |
| `JURISDICTION` | `GLOBAL` | Active jurisdiction: UAE, EU, US, GCC, GLOBAL |
| `JURISDICTION_OP_TYPE` | `spot` | Operation type: spot, leveraged, derivatives |
| `JURISDICTION_BLOCK_SANCTIONED` | `true` | Enable OFAC sanctions screening |

### Logging Format

```
🌐 [CP-11] JURISDICTION_VETO: {violation} | asset={symbol} | jurisdiction={j}
🌐 [CP-11] JURISDICTION_PASS: NONE | asset={symbol} | jurisdiction=UAE | score=100/100
```

### Receipt Block

```json
{
  "jurisdiction_compliance": {
    "check": "enabled",
    "result": "passed|failed|skipped",
    "jurisdiction": "UAE",
    "compliance_score": 100.0,
    "violation": "",
    "asset": "BTC/USD"
  }
}
```

---

## UAE Activation Example

To activate CP-11 for a UAE-based institutional client:

```bash
JURISDICTION_GATE_ENABLED=true
JURISDICTION=UAE
JURISDICTION_OP_TYPE=spot
```

Result: XMR, ZEC, DASH, GRIN, BEAM, FIRO will be blocked. Leveraged and derivative operations will be blocked. BTC, ETH, SOL (and other non-prohibited assets) pass without friction.

---

## Consequences

### Positive
- OMNIX can credibly claim jurisdiction-aware governance infrastructure — no competitor has this
- UAE + GCC configuration directly supports the Eureka Dubai pitch narrative
- Jurisdictional compliance receipts can be presented to regulators without additional documentation
- Extensible: new jurisdictions can be added by updating the `JURISDICTION_RULES` dict

### Negative / Trade-offs
- Real regulatory APIs (VARA live registry, FinCEN active sanctions) not integrated — internal rules only
- Rule tables require periodic review as regulations evolve
- Single jurisdiction per deployment — multi-jurisdiction routing deferred to v2

---

## Investor Narrative

> "An OMNIX client in the UAE activates one environment variable, and every automated decision is immediately screened against VARA's asset framework — with a cryptographic receipt showing the jurisdiction check passed. This is the first time governance infrastructure has embedded regulatory jurisdiction into the decision record itself."

---

## Related ADRs

- ADR-022: Post-Quantum Cryptography
- ADR-046: Sharia Gate (CP-6)
- ADR-047: AML Gate (CP-9)
- ADR-048: Fraud Gate (CP-10)
