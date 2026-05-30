# ADR-189 — PoGR Public Certificate Verifier

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-24  
**Updated:** 2026-05-30 — §Offline Verification Protocol added  
**Supersedes:** —  
**Related:** ADR-186 (PoGR spec) · ADR-187 (PoGR API) · ADR-188 (OSG)  
**Product ID:** OMNIX-POGR-2026-001

---

## Context

ADR-186 established the Proof of Governance Registry and its zero-trust verification invariant (PoGR-INV-003): any certificate must be verifiable by anyone, with no OMNIX account, no API key, and no access to the issuer's internal systems.

ADR-187 implemented the backend API (`/v1/pogr/verify/{pogc_id}`). The ProofOfGovernancePage (`/proof-of-governance`) provides a registry browser with embedded verification capability.

**The missing layer:** a standalone, shareable, publicly accessible verification page designed for external audiences — regulators, auditors, customers, legal counsel — who receive a PoGC link from an enterprise and need to verify it with zero OMNIX context.

The URL `omnixquantum.net/pogr/verify/POGC-xxx` must be the terminal trust artifact: self-explanatory, premium, and complete in one page.

### The Distribution Problem

When an enterprise includes a PoGC in a regulatory submission, a customer contract, or an audit package, they include a URL. That URL is the first (and often only) touchpoint between OMNIX and the external party doing the verification.

The existing `/proof-of-governance` page is designed for OMNIX users navigating the platform. It has three tabs, loads a registry, and assumes the visitor already knows what PoGR is. A regulator or auditor clicking a link from a third party has none of that context.

---

## Decision

Introduce a dedicated **PoGR Public Verifier** page at:

```
/pogr/verify               — search input (no ID)
/pogr/verify/:pogcId       — direct verification (with ID)
```

### Design Principles

1. **Zero-context entry** — The page must be fully comprehensible to someone who has never heard of OMNIX. It explains what it is showing, why it matters, and what the result means.

2. **Single-purpose** — No navigation, no tabs, no registry browser. One job: show whether this certificate is valid.

3. **Premium trust signal** — The visual design must communicate institutional-grade credibility. A regulator who lands on this page must feel confidence, not confusion.

4. **Cryptographic transparency** — Show the content hash, the CTCHC seal hash, the PQC algorithm, and the signature presence. A technically sophisticated auditor must be able to cross-reference with the offline verification protocol (§Offline Verification Protocol below).

5. **Shareable** — Every certificate has a stable, permanent URL. Copy-link functionality is first-class.

6. **Offline-verifiable** — Any certificate can be downloaded as a self-contained JSON and verified with zero network access using `scripts/verify_pogc_offline.py`. The page surfaces this capability prominently.

### URL Update

`POST /v1/pogr/certify` previously returned `public_page` pointing to `/proof-of-governance?id={pogc_id}`. Updated to `/pogr/verify/{pogc_id}` — the canonical public verification URL.

### Components

```
PoGRVerifyPage
├── HexLogo
├── LoadingState
├── SearchState             — shown when no ID in URL
├── NotFoundState           — 404 from API
├── ValidCertDisplay        — main certificate view
│   ├── Verdict banner      — ✅/❌ + ConformanceRing
│   ├── Certificate identity grid
│   ├── Mandate tier banner (MANDATE-BOUND / MANDATE-ALIGNED · ADR-194)
│   ├── Verification checks (PoGR-INV-003 notes)
│   ├── Cryptographic proof (content_hash + ctchc_seal_hash + signature presence)
│   ├── Share / copy-link
│   └── OfflineVerification — download JSON + Python snippet + 4-step guide
└── CopyButton
```

### Invariants Exercised

- **PoGR-INV-003** — verification requires zero auth; enforced by calling public API endpoint
- **PoGR-INV-002** — revoked certificates shown as REVOKED (not hidden)
- **PoGR-INV-004** — expired certificates shown as EXPIRED (not valid)

---

## Offline Verification Protocol

**Principle:** A PoGC must produce the same verification result whether checked via the web UI, the API, or a locally-executed Python script with no network access.

### Certificate Export Endpoint

```
GET /v1/pogr/certificate/<pogc_id>/export
Auth: None (PoGR-INV-003)
Response: application/json (Content-Disposition: attachment)
```

Returns the full certificate augmented with:
- `_export_metadata` — registry reference, product ID, ADR refs
- `_offline_verification` — canonical fields schema, hash algorithm, verification steps, Python snippet, verifier command

### Offline Verifier Script

`scripts/verify_pogc_offline.py` — standalone Python 3.8+, no external dependencies.

```
Usage:
  python verify_pogc_offline.py POGC-A3F2B1C4D5E6F7A8
  python verify_pogc_offline.py --file POGC-A3F2B1C4D5E6F7A8.json
  python verify_pogc_offline.py POGC-... --download-only
  python verify_pogc_offline.py POGC-... --json   # machine-readable output

Exit codes: 0 = VALID · 1 = INVALID/WARNING · 2 = usage error
```

### Verification Checks (6 total)

| Check | Method | Invariant |
|---|---|---|
| Content hash integrity | SHA3-256 recomputed over canonical fields, compared to `content_hash` | ADR-186 §4 |
| Certificate status | `status == 'ACTIVE'` | PoGR-INV-002 |
| TTL validity | `now < expires_at` (UTC) | PoGR-INV-004 |
| PQC signature presence | `pqc_signature.startswith('ML-DSA-65:')` | ADR-186 §3 |
| Issuer identity | `issuer == 'OMNIX QUANTUM LTD'` | PoGR-INV-001 |
| Mandate certification | MANDATE-BOUND / MANDATE-ALIGNED / UNCERTIFIED (informational) | ADR-194 MIVP |

### Canonical Fields Schema

The `content_hash` covers exactly these 10 fields, serialized as
`json.dumps(canonical, sort_keys=True, separators=(',',':'))`:

```python
CANONICAL_FIELDS = [
    "pogc_id", "session_id", "ctchc_seal_hash",
    "issuer", "subject_org", "agent_id",
    "compliance_tier", "mandate_certification",
    "issued_at", "expires_at",
]
```

### Minimum Python Snippet

Any party can verify integrity in 6 lines, with zero dependencies:

```python
import hashlib, json

FIELDS = ['pogc_id','session_id','ctchc_seal_hash','issuer','subject_org',
          'agent_id','compliance_tier','mandate_certification','issued_at','expires_at']

cert      = json.load(open('POGC-xxx.json'))
canonical = {k: cert[k] for k in FIELDS if k in cert}
payload   = json.dumps(canonical, sort_keys=True, separators=(',',':')).encode()
computed  = 'sha3-256:' + hashlib.sha3_256(payload).hexdigest()

assert computed == cert['content_hash'], 'Hash mismatch — certificate tampered!'
print('✓', computed)
```

### Trust Chain

```
omnixquantum.net/pogr/verify/POGC-xxx    — web verification (zero-context, no auth)
              ↕  same result
/v1/pogr/verify/<pogc_id>                 — API verification (PoGR-INV-003)
              ↕  same result
python verify_pogc_offline.py --file x.json  — fully offline (no network)
```

All three paths produce the same determination: VALID or INVALID.

---

## Routing

| Path | Component | Auth |
|---|---|---|
| `/pogr/verify` | `PoGRVerifyPage` | None |
| `/pogr/verify/:pogcId` | `PoGRVerifyPage` | None |
| `/proof-of-governance` | `ProofOfGovernancePage` | None (registry browser) |
| `GET /v1/pogr/certificate/<id>/export` | `pogr_blueprint.export_certificate` | None |

Both pages remain active. ProofOfGovernancePage is the registry browser (OMNIX users, enterprise context). PoGRVerifyPage is the public verifier (external parties, single-certificate context).

---

## Bug Fixes Applied (2026-05-30)

| ID | Description | Fix |
|---|---|---|
| POGR-BUG-001 | `PoGRVerifyPage` share URL and navigate used `/verify/` instead of `/pogr/verify/` | Fixed in `ValidCertDisplay` and `handleSearch` |
| POGR-BUG-002 | `_auth_api_key` queried `b2b_clients.active` — column is `is_active` | Fixed in `pogr_blueprint.py` |

---

## Consequences

### Positive
- The canonical share URL (`/pogr/verify/{id}`) is now a premium, standalone trust artifact
- Regulators and auditors can verify without any OMNIX navigation context
- `public_page` in the certify response now points to the correct URL
- **Any certificate is now fully offline-verifiable** — download JSON, run script, same result
- The offline verifier has zero external dependencies — any Python 3.8+ installation works
- The ProofOfGovernancePage is unmodified — backward compatible

### Constraints
- Two pages now serve verification; they must remain consistent with the same underlying API
- The `/pogr/verify/:pogcId` route requires React Router's catch-all to pass through to Flask, which already serves `dist/index.html` for all non-API routes

---

*ADR-189 · OMNIX QUANTUM LTD · Harold Nunes · May 2026*  
*PoGR Public Certificate Verifier · OMNIX-POGR-2026-001*  
*Updated 2026-05-30: Offline Verification Protocol · export endpoint · verifier script · bug fixes POGR-BUG-001/002*
