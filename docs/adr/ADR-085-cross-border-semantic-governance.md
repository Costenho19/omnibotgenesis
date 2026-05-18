# ADR-085: Cross-Border Semantic Governance Framework

**Status:** ACCEPTED  
**Date:** 2026-04-14  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Scope:** `omnix_web/api/omnix_engine/receipt_to_vc.py` · `omnix_web/api/omnix_engine/federated_trust.py` · `omnix_core/evidence/decision_receipt.py`

---

## Context

### The Cross-Jurisdiction Semantic Governance Problem

OMNIX receipts are cryptographically sound. The hash is independently verifiable. The
Dilithium-3 signature is independently verifiable. The W3C VC envelope is structurally
valid and resolves at `did:web:omnixquantum.net`.

However, a technically correct observation was raised:

> "W3C VCs + JSON-LD + schema mappings ensure verifiable structure, not semantic
> equivalence across jurisdictions. Returning `jurisdiction_semantics` is an internal
> projection of regulatory meaning. Independent verifiers can validate the same receipt
> and still arrive at different regulatory conclusions."

This is architecturally accurate. The `jurisdiction_semantics` block, in its original
form (5 frameworks, no proof scope, no concordance), provided OMNIX's interpretation
of regulatory meaning. It did not:

1. Explicitly state the boundary of what the receipt cryptographically proves.
2. Explicitly state what remains jurisdiction-dependent.
3. Provide coverage across enough frameworks for cross-border deployments (UAE, UK, US, Singapore, Saudi Arabia).
4. Give verifiers a concordance map to understand where frameworks agree and where additional local assessment is needed.

The result: technically correct receipts that could still be misread by external parties
as broader compliance claims than what the cryptographic evidence supports.

---

## Decision

### Three-layer solution

**Layer 1 — Expanded regulatory mapping (10 frameworks, 6 regions)**

Map every receipt to all major applicable frameworks simultaneously. A verifier in any
target market finds their jurisdiction's interpretation without needing to contact OMNIX.

| Framework | Jurisdiction | Region |
|-----------|-------------|--------|
| EU Artificial Intelligence Act (Reg. 2024/1689) | European Union | Europe |
| EU GDPR (Reg. 2016/679, Art. 22) | European Union | Europe |
| DORA (Reg. 2022/2554) | EU Financial Sector | Europe |
| FATF Recommendations 10/16/20/29 (2023) | G7 + 37 members | Global |
| UK FCA — COBS 11.2 + SM&CR + SYSC 9.1 | United Kingdom | UK |
| US SEC Rule 15c3-5 + Reg SCI | United States | North America |
| MAS FEAT Principles v2 (2020) | Singapore | Asia-Pacific |
| UAE CBUAE AI Governance Framework (2024) | United Arab Emirates | Middle East |
| SAMA Responsible AI Principles (2023) | Kingdom of Saudi Arabia | Middle East |
| FSB G20 AI/ML in Financial Services (2023) | G20 International | Global |

Each entry includes: `label`, `jurisdiction`, `region`, `reference` (specific regulation/article), and the interpretation text for APPROVED / BLOCKED / HOLD outcome.

**Layer 2 — Proof scope (what the receipt certifies vs. what it does not)**

Every `jurisdiction_semantics` block now contains a `proof_scope` section with three
explicit fields:

```json
{
  "proof_scope": {
    "what_this_receipt_proves": [
      "The decision was evaluated by OMNIX governance checkpoints at the stated timestamp.",
      "The veto chain result (N passed, M blocked) is cryptographically bound to this receipt.",
      "The receipt has not been altered since signing — hash and PQC signature are independently verifiable.",
      "The issuer (did:web:omnixquantum.net) controlled the signing key at time of issuance.",
      "Each regulatory framework mapping reflects OMNIX's interpretation at time of issuance."
    ],
    "what_this_receipt_does_not_claim": [
      "Authoritative regulatory approval from any named jurisdiction or supervisory body.",
      "Semantic equivalence between interpretations — different verifiers may reach different regulatory conclusions.",
      "That OMNIX's internal checkpoint logic satisfies every local implementation rule.",
      "Guaranteed cross-border enforceability — this is governance evidence, not a compliance certificate."
    ],
    "verifier_guidance": "..."
  }
}
```

This directly answers the objection: OMNIX does not claim semantic equivalence. It
states explicitly, inside the receipt itself, that authoritative determination remains
with local regulators. Any verifier who misreads the receipt as a compliance certificate
has been explicitly warned inside the artifact they are reading.

**Layer 3 — Cross-jurisdiction concordance**

A `cross_jurisdiction_concordance` block indicates which frameworks agree on the
outcome and where additional local obligations may arise:

```json
{
  "cross_jurisdiction_concordance": {
    "status": "BROADLY_ALIGNED | ALIGNED_WITH_LOCAL_REPORTING_OBLIGATIONS | FULLY_ALIGNED",
    "note": "...",
    "regions": { ... },
    "divergence_risk": "Low for cryptographic validity. Medium for regulatory interpretation — local implementation rules may add obligations (FATF STR, UK SM&CR, US Reg SCI)."
  }
}
```

This is a first in governance receipt design: the receipt maps not just what OMNIX
thinks the outcome means, but where verifiers from different jurisdictions are likely
to agree and where they will need to do additional local work.

---

## Trust Score fix (Bug 1)

The `trust_score` calculation in `federated_trust.py` previously included
`jurisdiction_semantics` as a +0.10 bonus, but `jurisdiction_semantics` was computed
AFTER the `trust_score` block — meaning the bonus was never applied.

Fixed: `jurisdiction_semantics` is now computed before `trust_score`. A receipt with
valid jurisdiction semantics now correctly scores up to 1.0 rather than capping at 0.90.

---

## Key consistency fix (Bug 2 — direct import)

`gov_blueprint._load_engine()` previously loaded `DecisionReceiptEngine` via
`importlib.util.spec_from_file_location()`. This created a second module object with
its own `_STABLE_SIGNING_KEYS` — a different keypair from the one registered in the
trust registry. Independent verification against the published public key would always
fail for receipts signed via `gov_blueprint`.

Fixed: `_load_engine()` now imports `DecisionReceiptEngine` directly from the canonical
module. Both the trust registry and the governance API share the same instance, and
therefore the same public key.

---

## Stable signing keys (ADR-085 companion to ADR-078)

Both `omnix_web/api/omnix_engine/decision_receipt.py` (the web service version) and
`omnix_core/evidence/decision_receipt.py` (the bot service version) now generate a
single keypair at module import time (`_STABLE_SIGNING_KEYS`). All `DecisionReceiptEngine`
instances within the same process share this keypair. The EPHEMERAL warning is eliminated
for all normal deployments.

To persist the same keypair across process restarts (production requirement):

```
OMNIX_SIGNING_SECRET_KEY_B64=<base64 Dilithium-3 secret key>
OMNIX_SIGNING_PUBLIC_KEY_B64=<base64 Dilithium-3 public key>
```

Set both in Railway environment variables (see ADR-078 for key capture procedure).

---

## Verification server PORT fix (bot service)

`omnix_core/evidence/verification_server.py` previously started on hardcoded port 8000.
Railway's health check targets `$PORT` (dynamically assigned). The bot service
(`omnibotgenesis`) was crashing because Railway could not reach its health check endpoint.

Fixed: `start_verification_server_task()` in `main_entry.py` now reads `$PORT` from
the environment (fallback: 8000 for local dev). The verification server also exposes
`GET /health` in addition to `GET /` for explicit Railway health check compatibility.

---

## What this framework establishes

### What OMNIX receipts now prove (cryptographic layer)

| Claim | Mechanism |
|-------|-----------|
| Decision was evaluated at the stated timestamp | Timestamp embedded in signed payload |
| Veto chain result is authentic | SHA-256 content hash, Dilithium-3 signature |
| Receipt was not modified after signing | Any modification invalidates the signature |
| Issuer controlled the signing key at issuance | `did:web:omnixquantum.net` DID document |
| Governance checkpoints were applied in sequence | Veto chain array in receipt payload |

### What the regulatory mapping layer adds

| Claim | Mechanism |
|-------|-----------|
| Receipt maps to 10 regulatory frameworks | `regulatory_interpretation` block |
| Frameworks are region-indexed | `region` field per framework |
| Outcome interpretation is explicit per framework | `interpretation` text per APPROVED/BLOCKED/HOLD |
| Specific article/regulation cited | `reference` field per framework |

### What the receipt explicitly does NOT claim

| Non-claim | Where stated |
|-----------|-------------|
| Authoritative regulatory approval | `proof_scope.what_this_receipt_does_not_claim` |
| Semantic equivalence across jurisdictions | `proof_scope.what_this_receipt_does_not_claim` |
| Compliance certificate substitute | `proof_scope.what_this_receipt_does_not_claim` |
| Full local implementation rule coverage | `proof_scope.what_this_receipt_does_not_claim` |

---

## Consequences

### Positive

- Any external verifier in 10 jurisdictions finds their local framework's interpretation
  directly in the receipt — no OMNIX knowledge required.
- The `proof_scope` block preempts misinterpretation by stating boundaries explicitly
  inside the artifact.
- The `cross_jurisdiction_concordance` block makes divergence risk visible and
  quantified — no verifier is surprised by additional local obligations.
- Trust score now correctly reaches 1.0 for receipts with valid jurisdiction semantics.
- Key consistency between trust registry and governance API — independent verification
  succeeds for all production receipts.
- Bot service health check passes on Railway — `omnibotgenesis` service remains running.

### Negative / Acceptable risks

- Larger receipt payload (~4-6 KB additional in `jurisdiction_semantics`). Acceptable
  given B2B institutional use case where completeness matters more than payload size.
- The framework maps OMNIX's regulatory interpretation, not any regulator's official
  position. This is explicitly stated in `proof_scope` and in the block `note` field.
- Divergence risk rated "Medium for regulatory interpretation" is honest and accurate —
  this is the correct state of the art for any cross-border governance receipt today.

---

## References

- ADR-044: Self-Verifiable Receipts (Merkle chain, transparency log)
- ADR-078: Signing Key Persistence (Dilithium-3 key management)
- ADR-079: PKI Verification Endpoint (public key + verify endpoints)
- ADR-084: Receipt → W3C VC Converter
- `omnix_web/api/omnix_engine/receipt_to_vc.py` — `build_jurisdiction_semantics()`
- `omnix_web/api/omnix_engine/federated_trust.py` — `independent_verify()`, trust registry
- `omnix_web/api/gov_blueprint.py` — `_load_engine()` (direct import fix)
- `omnix_core/evidence/decision_receipt.py` — `_STABLE_SIGNING_KEYS`, `_init_keys()`
- `omnix_core/evidence/verification_server.py` — `create_verification_app()`, `/health` route
- `src/omnix/bootstrap/main_entry.py` — `start_verification_server_task()` (PORT fix)
- `docs/compliance/CROSS_JURISDICTION_GOVERNANCE.md` — institutional reference document
