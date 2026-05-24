# ADR-189 — PoGR Public Certificate Verifier

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-24  
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

4. **Cryptographic transparency** — Show the content hash, the CTCHC seal hash, the PQC algorithm, and the signature presence. A technically sophisticated auditor must be able to cross-reference with the offline verification protocol (ADR-186 §Offline Verification).

5. **Shareable** — Every certificate has a stable, permanent URL. Copy-link functionality is first-class.

### URL Update

`POST /v1/pogr/certify` previously returned `public_page` pointing to `/proof-of-governance?id={pogc_id}`. Updated to `/pogr/verify/{pogc_id}` — the canonical public verification URL.

### Components

```
PoGRVerifyPage
├── HexLogo
├── LoadingState
├── SearchState          — shown when no ID in URL
├── NotFoundState        — 404 from API
├── ValidCertDisplay     — main certificate view
│   ├── Verdict banner   — ✅/❌ + conformance ring
│   ├── Certificate identity grid
│   ├── Verification checks (PoGR-INV-003 notes)
│   ├── Cryptographic proof (hashes + signature)
│   └── Share / copy-link
└── CopyButton
```

### Invariants Exercised

- **PoGR-INV-003** — verification requires zero auth; enforced by calling public API endpoint
- **PoGR-INV-002** — revoked certificates shown as REVOKED (not hidden)
- **PoGR-INV-004** — expired certificates shown as EXPIRED (not valid)

---

## Routing

| Path | Component | Auth |
|---|---|---|
| `/pogr/verify` | `PoGRVerifyPage` | None |
| `/pogr/verify/:pogcId` | `PoGRVerifyPage` | None |
| `/proof-of-governance` | `ProofOfGovernancePage` | None (registry browser) |

Both pages remain active. ProofOfGovernancePage is the registry browser (OMNIX users, enterprise context). PoGRVerifyPage is the public verifier (external parties, single-certificate context).

---

## Consequences

### Positive
- The canonical share URL (`/pogr/verify/{id}`) is now a premium, standalone trust artifact
- Regulators and auditors can verify without any OMNIX navigation context
- `public_page` in the certify response now points to the correct URL
- The ProofOfGovernancePage is unmodified — backward compatible

### Constraints
- Two pages now serve verification; they must remain consistent with the same underlying API
- The `/pogr/verify/:pogcId` route requires React Router's catch-all to pass through to Flask, which already serves `dist/index.html` for all non-API routes

---

*ADR-189 · OMNIX QUANTUM LTD · Harold Nunes · May 2026*  
*PoGR Public Certificate Verifier · OMNIX-POGR-2026-001*
