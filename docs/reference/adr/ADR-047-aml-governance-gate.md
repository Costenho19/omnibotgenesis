# ADR-047: AML Governance Gate (CP-9)

**Status:** IMPLEMENTED  
**Date:** March 25, 2026  
**Implemented:** March 29, 2026  
**Author:** Harold Nunes  
**Module:** `omnix_core/governance/aml_gate.py`

---

## Context

Following the successful implementation of the Sharia Gate (ADR-046 / CP-6), OMNIX expands its compliance governance pipeline with Anti-Money Laundering (AML) validation. AML compliance is mandatory under:

- **FATF Recommendation 15** — Virtual Assets and Virtual Asset Service Providers
- **FinCEN Virtual Currency Guidance (2019)** — US framework for VA transactions
- **UAE Central Bank AML/CFT Framework** — mandatory for all digital asset operations in the Emirates

No existing automated governance infrastructure screens trading decisions for AML patterns with cryptographic audit receipts. This is a structural compliance gap for institutional clients in regulated jurisdictions.

---

## Decision

Implement CP-9 — the **AML Governance Gate** — positioned AFTER CP-8 (ECW) in the decision pipeline.

### Design Principles

1. **Fail-safe by default** — disabled for all existing clients; exceptions → pass-through
2. **Activatable via env var** — `AML_GATE_ENABLED=true`
3. **Fail-closed when enabled** — high-risk asset or pattern → immediate BLOCKED with log
4. **Zero impact on existing pipeline** — default OFF preserves Railway operation

---

## Implementation

### Module: `omnix_core/governance/aml_gate.py`

Four validation checks in sequence:

| Check | Rule | Behavior |
|-------|------|----------|
| **1. Privacy coin screening** | Asset in HIGH_RISK_AML_ASSETS | Hard VETO — `HIGH_RISK_AML_ASSET` |
| **2. Mixer token screening** | Asset in AML_MIXER_TOKENS | Hard VETO — `HIGH_RISK_AML_ASSET` |
| **3. Anomalous volume** | Volume USD > threshold (default $500K) | Score deduction (-40 pts) |
| **4. Structuring pattern** | Frequency > threshold (default 10/24h) | Score deduction (-30 pts) |

### Pipeline Position

```
CP-1 → CP-2 → CP-3 → CP-4 → CP-5 → CP-6 (Sharia) → CP-7 → CP-7b → CP-8 (ECW)
→ CP-9 (AML Gate) ← NEW
→ CP-10 (Fraud Gate) → CP-11 (Jurisdiction Gate)
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AML_GATE_ENABLED` | `false` | Master enable switch |
| `AML_VOLUME_THRESHOLD_USD` | `500000` | Max trade volume in USD |
| `AML_FREQUENCY_THRESHOLD` | `10` | Max trades per 24h |
| `AML_BLOCK_PRIVACY_COINS` | `true` | Block XMR, ZEC, DASH, etc. |
| `AML_BLOCK_MIXER_TOKENS` | `true` | Block TORN, RAIL, AZTEC, etc. |

### High-Risk AML Asset List (initial)

Privacy coins: XMR, ZEC, DASH, GRIN, BEAM, FIRO, PIVX and their trading pairs.  
Mixer tokens: TORN (Tornado Cash), RAIL (Railgun), AZTEC.

### Logging Format

```
🏦 [CP-9] AML_VETO: {violation} | asset={symbol} | aml_score={score}
🏦 [CP-9] AML_PASS: NONE | asset={symbol} | score=100/100
```

### Receipt Block

```json
{
  "aml_compliance": {
    "check": "enabled",
    "result": "passed|failed|skipped",
    "score": 100.0,
    "violation": "",
    "asset": "BTC/USD"
  }
}
```

---

## Consequences

### Positive
- OMNIX becomes the only governance infrastructure screening AML patterns with PQC-signed receipts
- Enables institutional clients in UAE, US, EU to demonstrate FATF compliance per automated decision
- CP-9 slot formally assigned — extends pipeline to 11 checkpoints
- Zero risk to existing clients — completely opt-in

### Negative / Trade-offs
- Volume and frequency checks use simplified heuristics (no on-chain analytics integration yet)
- Chainalysis/Elliptic integration deferred to v2 — out of scope per task specification
- Privacy coin list requires maintenance as new assets emerge

---

## Investor Narrative

> "OMNIX doesn't just screen assets — it screens every decision. When CP-9 activates, every AML violation generates a cryptographically signed record that any compliance officer can independently verify, without asking OMNIX for data."

---

## Related ADRs

- ADR-022: Post-Quantum Cryptography (Dilithium-3 signatures on receipts)
- ADR-046: Sharia Governance Gate (CP-6) — same pattern
- ADR-048: Fraud Detection Gate (CP-10)
- ADR-049: Jurisdiction Compliance Gate (CP-11)
