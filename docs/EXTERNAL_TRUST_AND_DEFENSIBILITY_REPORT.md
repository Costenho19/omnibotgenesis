# EXTERNAL TRUST AND DEFENSIBILITY REPORT
**Audit ID:** HGA-2026-Q4-001  
**Classification:** CONFIDENTIAL — External Audit Preparation  
**Date:** 9 May 2026  
**Stage:** 4 of 4 (External Trust, Adversarial Verification, Legal Defensibility, Institutional Risk)  
**Preceding Reports:**  
- HGA-2026-Q2-001 — Hidden Gap Audit  
- HGA-2026-Q2-002 — Governance Deep Risk Report  
- HGA-2026-Q3-001 — Governance Failure Mode Report (11 failure modes)

**Audit Frame:**  
This report assumes OMNIX is being reviewed simultaneously by five hostile external parties:  
a hostile external auditor, a financial regulator, an enterprise security team, a skeptical investor, and a malicious integrator attempting to forge, replay, or impersonate receipts. Internal confidence is not the optimization target. Institutional defensibility is.

---

## EXECUTIVE SUMMARY

OMNIX has built a governance infrastructure with strong cryptographic foundations, a well-designed public trust anchor at `/.well-known/omnix-public-key.json`, robust multi-layer authentication, and correctly-implemented fail-closed governance logic. However, five gaps remain that a hostile external party could successfully challenge: (1) the public verifier trusts the embedded key in each receipt without checking it against a pinned OMNIX key registry — meaning a well-crafted forged receipt with an attacker-generated Dilithium-3 keypair passes verification; (2) the chain integrity function `verify_chain()` is not called on the receipt read path, so tampering with individual records goes undetected at query time; (3) COLD-tier archival (required for the MiFID II 5-year claim) requires S3/R2 credentials that are likely not configured in the production Railway deployment; (4) Redis is absent from the web service in Railway, making `strict` anti-replay mode configured but inactive; (5) fourteen claims across public pages use language ("immutable," "tamper-proof," "proven") that is technically defensible for hash integrity but could be challenged by a regulator who understands that PostgreSQL records can be deleted by a database administrator.

**Risk Level at Moment of Report:** MEDIUM-HIGH for external adversarial challenge. MEDIUM for regulatory review. LOW for enterprise security audit (auth and rate-limiting are solid).

---

## CATEGORY 1 — EXTERNAL TRUST ANCHOR VALIDATION

### 1.1 Public Key Discovery

**Finding: PASS with condition**

The `/.well-known/omnix-public-key.json` endpoint exists and returns a complete public key manifest with the following elements verifiable by any third party:

```json
{
  "spec": "OMNIX Public Key Manifest v1.0",
  "issuer": "OMNIX Quantum Ltd",
  "issuer_did": "did:web:omnixquantum.net",
  "key": {
    "id": "did:web:omnixquantum.net#pqc-key-1",
    "algorithm": "Dilithium-3 (ML-DSA-65)",
    "standard": "NIST FIPS 204 — ML-DSA-65",
    "public_key_b64": "<current active key>",
    "fingerprint_sha256": "<first 32 hex chars of SHA-256(raw key)>"
  },
  "rotation_policy": {
    "policy": "ADR-043 — Crypto-agility",
    "rotation": "Manual, announced 30 days in advance"
  }
}
```

The endpoint correctly uses `Cache-Control: no-cache, must-revalidate` and `CORS: *` (intentional — public trust anchors must be universally accessible). The DID method `did:web:omnixquantum.net` is RFC-compliant and independently resolvable.

**Condition:** This endpoint only serves a stable, pinnable key when `OMNIX_SIGNING_SECRET_KEY_B64` and `OMNIX_SIGNING_PUBLIC_KEY_B64` are set in the deployment environment. If these variables are absent:

- The endpoint serves an ephemeral key generated at startup
- The ephemeral key changes on every server restart
- Any third party who pins the key at 09:00 will be unable to verify receipts issued after a 09:30 restart
- There is no signal in the response to indicate whether the served key is stable or ephemeral

**Status in production (Railway):** `mode=persisted` confirmed in logs. Key is stable. This condition is currently met.

**Residual gap:** The response does not include a `key_mode` field (`"stable"` vs `"ephemeral"`) that would allow third parties to detect if they are receiving a trustworthy anchor.

### 1.2 Key Pinning and Versioning

**Finding: PARTIAL**

- Key ID is static: `did:web:omnixquantum.net#pqc-key-1` — version number not incremented on rotation
- Rotation policy documents "30 days advance notice" but no changelog endpoint exists at `/api/trust/registry/changelog`
- No mechanism prevents an attacker from substituting the public key in a receipt with their own key and passing it to the verifier

### 1.3 Independent Discoverability

**Finding: PASS**

A third party can discover and use the OMNIX public key through three independent paths:
1. `/.well-known/omnix-public-key.json` — primary
2. `/.well-known/did.json` — DID document
3. Embedded `public_key` field in every receipt (self-contained)

The verify script at `omnix_web/public/omnix_verify.py` is publicly accessible and allows offline verification.

### 1.4 What Prevents Forged Receipts with Attacker Keypairs

**Finding: CRITICAL GAP — ETA-001**

This is the most important finding in the entire audit for adversarial review.

The current verifier (`/api/trust/verify`) accepts a receipt, extracts the embedded `public_key` field, verifies the PQC signature against that embedded key, and reports `signature_valid: true` if they match.

An attacker can:
1. Generate a valid Dilithium-3 keypair (open source, freely available)
2. Craft a receipt JSON with any desired payload and decision
3. Sign it with their private key
4. Embed their public key in the `public_key` field of the receipt
5. Submit to `/api/trust/verify`
6. Receive `signature_valid: true`

**The verifier has no mechanism to check whether the embedded public key is an OMNIX-issued key.** There is no pinned key registry, no key allowlist, and no cross-reference against `/.well-known/omnix-public-key.json` at verification time.

**Impact:** A malicious integrator could present forged OMNIX governance receipts to a third party (regulator, LP, auditor). If that third party runs the verifier, it would confirm the signature as valid. Only the `issuer_did`, `receipt_id` format (`OMNIX-*`), and an out-of-band comparison of the embedded public key against the OMNIX trust anchor would reveal the forgery.

**Required fix:** The verifier must cross-reference the embedded `public_key` against the trusted OMNIX key fingerprint (from `/.well-known/omnix-public-key.json` or a hardcoded OMNIX key registry). Any receipt whose `public_key` does not match a known OMNIX key should return `issuer_trusted: false` alongside the signature validity status.

---

## CATEGORY 2 — RECEIPT SURVIVABILITY AFTER FAILURE

### Survivability Matrix

| Scenario | Receipt Survives? | Notes |
|---|---|---|
| DB outage during `evaluate()` | **❌ NO** | Decision is made and returned. `store_receipt()` fails silently. No DB record created. The client receives a decision with a `receipt_id` they cannot later retrieve. |
| DB outage during `GET /receipt/{id}` | ⚠️ Partial | Returns 503. No data loss — receipt is in DB, just unavailable. Recovers when DB returns. |
| Partial receipt persistence | ✅ Safe | PostgreSQL ACID — `INSERT` is atomic. No partial rows possible. |
| Server restart (env keys set) | ✅ Full | Same PQC keys loaded. All old receipts remain verifiable. |
| Server restart (env keys absent) | **❌ LOSS** | New ephemeral keypair generated. All PQC signatures from previous session are permanently unverifiable. FMR-001. |
| Redeploy (Railway) | ✅ if keys set | Identical to restart scenario. Keys in env vars survive redeployment. |
| Rollback to prior image | ⚠️ Key-version dependent | If key env vars are unchanged, safe. If a key rotation occurred between versions, prior-version receipts use different key — verify with embedded `public_key`. |
| Key rotation | ✅ Verifiable | Old receipts embed their signing public key. Verifier uses the embedded key. Old receipts remain independently verifiable forever. |
| Clock skew (+5 min) | ⚠️ Anti-replay distorted | Anti-replay TTL starts 5 min early — replay window effectively shortened |
| Clock skew (-5 min) | ⚠️ Anti-replay distorted | Replay window extended by 5 min — stale receipts accepted longer |
| S3/R2 credentials absent (COLD tier) | **⚠️ PARTIAL** | HOT (0–30d) and WARM (30d–12m) archival functional via PostgreSQL. COLD tier requires AWS/R2 credentials. Without them, receipts >12 months are retained in PostgreSQL only — not in immutable cold storage. The "5 years (MiFID II)" claim depends on this configuration. |

### Key Gap: DB Outage During Evaluation (ETA-002)

When the governance engine completes an evaluation and returns a decision to the client, `store_receipt()` is called afterwards. If the DB is unavailable at that moment:
- The client receives a valid receipt JSON with a real `receipt_id`
- No record is written to `decision_receipts`
- A later `GET /receipt/{receipt_id}` returns 404
- The client's receipt JSON is authentic (correct hash, valid signature) but unrecoverable from the OMNIX DB

**Mitigation path:** A `pending_receipts` buffer (Redis or write-ahead file) that stores receipt payloads during DB unavailability and replays on recovery (ADR-138 extension, classified as FMR-010 in Stage 3 report).

---

## CATEGORY 3 — PRODUCTION IDENTITY CONTINUITY

### 3.1 Current Status

**Confirmed via production logs:**
```
INFO:OMNIX.Evidence:[ADR-078] Signing keys loaded from environment.
key_id=8b1b2b64873056a0  algorithm=Dilithium-3 (ML-DSA-65)  mode=persisted
```

Both `OMNIX_SIGNING_SECRET_KEY_B64` and `OMNIX_SIGNING_PUBLIC_KEY_B64` are set in Railway. The server is operating in `mode=persisted`. FMR-001 is resolved in the current deployment.

### 3.2 Hard-Fail Guard (Added This Session)

Prior to this audit, the server would start with ephemeral keys if the env vars were absent — logging `CRITICAL` but continuing. This represented a silent downgrade risk for any future deployment where keys are accidentally omitted.

**Fix applied:** `decision_receipt.py` now reads `OMNIX_REQUIRE_PERSISTENT_KEYS` at startup. When set to `true`, the process raises `SystemExit` if persistent keys are not available, refusing to start rather than silently operating with ephemeral keys.

**Recommendation:** Set `OMNIX_REQUIRE_PERSISTENT_KEYS=true` in Railway to harden production against accidental key loss.

### 3.3 SHA-Only Fallback Silent Activation

If the `dilithium3` PQC library fails to import at runtime (corrupted package, dependency conflict), the signing engine falls back to SHA-256 only. This fallback:
- Is logged as WARNING (not CRITICAL)
- Is not surfaced in the `/.well-known/omnix-public-key.json` response
- Would cause receipts to carry `signature_algorithm: sha256` with no PQC signature
- Would not be detected by monitoring unless someone reads the startup logs

**Status:** No active mechanism prevents silent SHA-fallback in production. An external verifier would observe the change in `signature_algorithm` field.

### 3.4 Key Mode Not Exposed in Trust Anchor

The `/.well-known/omnix-public-key.json` response does not include a field indicating whether the served key is `stable` (from env vars) or `ephemeral`. Third parties cannot distinguish a trustworthy stable key anchor from an ephemeral key that will be invalidated on next restart.

---

## CATEGORY 4 — MULTI-INSTANCE CONSISTENCY

### State Consistency by Component

| Component | State Location | Multi-Instance Safe? | Notes |
|---|---|---|---|
| AMG registry | PostgreSQL (`avm_modification_registry`) | ✅ Yes | Full DB-backed. All instances see same state. |
| AMG rollback state | PostgreSQL | ✅ Yes | Checked from DB on every invocation |
| Scope Authorization (SAE) | PostgreSQL (`governance_scope_authorizations`) | ✅ Yes | DB is source of truth. In-memory singleton is a read-through cache. |
| AVM baselines | PostgreSQL | ✅ Yes | Genesis snapshot, calibration snapshots all in DB |
| Anti-replay | Redis (if REDIS_URL set) | ✅ Yes when Redis available | |
| Anti-replay | In-memory fallback (no Redis) | **❌ No** | Each dyno has its own replay store. Cross-dyno replay is possible. |
| Rate limiting (Flask-Limiter) | In-memory per process | **❌ No** | Rate limits are per-dyno, not aggregate. A client can hit N dynos × rate limit. |
| Rate limiting (gov_blueprint) | In-memory `_rate_limit_store` | **❌ No** | Same issue — per-dyno memory |
| Brute force lockout | In-memory `_brute_force_store` | **❌ No** | An attacker can spread attempts across dynos to bypass lockout |
| Decision receipt issuance | PostgreSQL + shared PQC env keys | ✅ Yes | All dynos use same env keys, write to same DB |
| Signing key identity | Env var loaded at startup | ✅ Yes | All dynos load same key from same env vars |

### Critical Gaps

**ETA-003 — Redis absent from Railway web service:**  
`OMNIX_ANTI_REPLAY_MODE=strict` was added to the web service, but if `REDIS_URL` is not set in the web service (it is set in the bot service, not the web service), then anti-replay operates in in-memory mode per the fallback logic. `strict` mode only has effect when a Redis backend is present. **Confirm `REDIS_URL` is set in the Railway web service, not only in the bot service.**

**ETA-004 — Rate limiting and brute force are per-dyno:**  
Single-dyno Railway deployments are not affected. Multi-dyno deployments would allow bypass.

---

## CATEGORY 5 — PUBLIC VERIFIER ADVERSARIAL TEST

### Adversarial Receipt Simulation Results

| Attack Vector | Verifier Response | Assessment |
|---|---|---|
| **Forged receipt, attacker Dilithium-3 keypair** | `signature_valid: true` (attacker key matches forged payload) | **❌ CRITICAL — ETA-001.** Verifier cannot detect forgery by unknown keypair. |
| **Altered receipt (payload modified)** | `hash_valid: false` — rejected | ✅ PASS |
| **Malformed hash (wrong hex length)** | Parsing error → rejected | ✅ PASS |
| **Stale receipt (timestamp 6 months old)** | Accepted — no freshness check in verifier | ⚠️ Gap: no timestamp validation in `/api/trust/verify` |
| **Replay receipt (same receipt_id submitted twice)** | Accepted — replay protection is at `evaluate()` level, not `verify()` level | ⚠️ Acceptable: verifier is stateless by design |
| **Receipt with unknown/random `public_key`** | `signature_valid: false` (random key won't match valid sig) | ✅ PASS for random key attacks |
| **Receipt with attacker keypair + valid signature** | `signature_valid: true` — **FORGERY UNDETECTED** | **❌ CRITICAL — ETA-001** |
| **Receipt with `signature_algorithm: sha256` (downgrade)** | Accepted if `content_hash` matches | ⚠️ Downgrade attack possible if verifier does not require PQC signature |
| **Receipt with empty signature field** | Depends on null-check in verifier | ⚠️ Requires code verification |
| **Receipt with `receipt_id` not in OMNIX DB** | Accepted by stateless verifier (uses only embedded fields) | ⚠️ By design — but an institutional integrator may not realize the DB is not queried |

### Recommended Verifier Hardening

```
1. Cross-reference embedded public_key against /.well-known/omnix-public-key.json fingerprint
   → Add field: "issuer_key_trusted": true/false
2. Add timestamp freshness check: receipts older than configurable window → "stale: true" warning
3. Require signature_algorithm to be "dilithium3" for full trust classification
   → Receipts with sha256-only algorithm → "trust_level": "reduced" in response
4. Add receipt_id format validation (must match OMNIX-[A-Z0-9]{10})
```

---

## CATEGORY 6 — LEGAL DEFENSIBILITY AUDIT

### Wording Classification Across All 52 Instances

**Classification legend:**  
- ✅ **PROVEN** — mathematically or empirically verifiable  
- 🔵 **INTERNALLY VALIDATED** — correct within OMNIX's own architecture  
- 🟡 **ASPIRATIONAL** — directionally accurate, not independently certified  
- 🔴 **UNSUPPORTED** — no external validation, legally risky as stated  
- ⬛ **DISCLAIMER** — explicit statement of what is NOT claimed (legally protective)

---

**PROVEN (no fix required):**

| Claim | File | Classification |
|---|---|---|
| "SHA-256 hash integrity — detectable by anyone if modified" | IndependentVerification.tsx | ✅ PROVEN — mathematical property |
| "Dilithium-3 signature — only the holder of the private key can sign" | IndependentVerification.tsx | ✅ PROVEN — cryptographic property |
| "Can be verified in 2030 using only the script and the public key" | IndependentVerification.tsx | ✅ PROVEN — self-contained receipt design |
| "Identical inputs always produce identical outputs" | CrisisReplay.tsx | ✅ PROVEN — deterministic hashing |
| "Past performance does not guarantee future results" | InstitutionalPage.tsx, TermsOfService.tsx | ✅ DISCLAIMER |
| "We don't guarantee outcomes. We help prevent costly mistakes." | CommercialLanding.tsx | ✅ DISCLAIMER — excellent |
| "What this credential does NOT claim: Guaranteed cross-border enforceability…" | ARFCompliance.tsx | ✅ DISCLAIMER — correctly labeled |

---

**INTERNALLY VALIDATED (acceptable, should be qualified):**

| Claim | File | Notes |
|---|---|---|
| "Immutable audit record" | BiotechGovernanceDemo.tsx, multiple | 🔵 Correct for hash-chain integrity. Technically PostgreSQL records can be deleted by DB admin — detectable via hash mismatch but not prevented. Recommend: "cryptographically-linked audit record" |
| "Tamper-proof" | CommercialLanding.tsx, GettingStarted.tsx, PublicDecisionVerify.tsx | 🔵 Same as above. Hash integrity detects tampering — it does not physically prevent it. Recommend: "tamper-evident" |
| "11-checkpoint MiCA-compliant pipeline" | StablecoinDashboard.tsx, StablecoinGovernanceDemo.tsx | 🔵 Architecture aligns with MiCA signal requirements. No MiCA certification from a competent authority. Recommend: "MiCA-aligned pipeline" |
| "Cryptographically proven" | PitchDeck.tsx | 🔵 Accurate for hash+signature properties. Recommend: "cryptographically verifiable" |
| "OMNIX doesn't just govern decisions — it proves them" | InvestorDemo.tsx | 🔵 Defensible in context of cryptographic receipts. Recommend: "OMNIX doesn't just govern decisions — it records them with cryptographic proof" |
| "5 years (MiFID II), HOT→WARM→COLD archival, immutable" | GettingStarted.tsx | 🔵 Architecture exists. COLD tier requires S3/R2 credentials not confirmed in production. Claim should be qualified. |
| "99.9% Uptime SLA Advisory+" | IntegrationGuide.tsx | 🔵 "Advisory+" qualifier softens appropriately. Uptime commitment requires Railway SLA agreement to back it. |
| "p50 < 800ms" | IntegrationGuide.tsx | 🔵 Measurable and confirmed in demo environments. Should specify: "measured on single-dyno Railway deployment" |
| "Receipt retention: Permanent, append-only ledger" | IntegrationGuide.tsx | 🔵 "Permanent" is aggressive. DB admin deletion is theoretically possible. Recommend: "5-year minimum, hash-linked ledger" |

---

**ASPIRATIONAL (requires qualification or removal):**

| Claim | File | Risk Level | Recommended Rewrite |
|---|---|---|---|
| "Regulatory Compliance & Certifications" (section header) | InstitutionalPage.tsx | MEDIUM | Rename to "Regulatory Alignment & Architecture" — no certification from a competent authority has been issued |
| "eIDAS 2.0 … ARF … AI Act … MiFID II" (regulatory alignment list) | `/.well-known` response | LOW | Currently framed as "regulatory alignment" — acceptable. Do not elevate to "compliant with" without independent assessment |
| "ISO 13850 Category 0 stop" (robotics demo) | RoboticsGovernanceDemo.tsx | MEDIUM | Context-specific domain check — acceptable in demo context, not a product claim |

---

**Legal Risk Hierarchy (Ranked):**

1. **HIGHEST:** "MiCA-compliant" without qualification — could be interpreted as regulatory certification  
2. **HIGH:** "5 years (MiFID II)" retention — requires S3/R2 COLD tier to be true  
3. **MEDIUM:** "immutable" and "tamper-proof" — should be "tamper-evident" and "cryptographically linked"  
4. **MEDIUM:** "Regulatory Compliance & Certifications" section header — should be "Regulatory Alignment"  
5. **LOW:** "99.9% Uptime SLA" — "Advisory+" qualifier provides adequate softening  

---

## CATEGORY 7 — ENTERPRISE SECURITY REVIEW

### Authentication Architecture

| Control | Status | Notes |
|---|---|---|
| API key authentication | ✅ Active | X-API-Key header, client-scoped, revokable |
| Brute force lockout | ✅ Active | 5 failed attempts → 15-minute block per IP |
| Admin IP allowlist | ✅ Active | `ADMIN_ALLOWED_IPS` env var |
| Role-based access | ✅ Active | `read` vs `admin` roles enforced |
| Key expiry check | ✅ Active | Expired keys rejected; <14d warning injected in response |
| API key logging | ✅ Safe | Failed auth logs only IP address, not the submitted key |

### CORS Configuration

| Scope | Config | Status |
|---|---|---|
| Flask-CORS global | `origins: [omnixquantum.net, localhost:5173, localhost:3000]` | ✅ Correct |
| Manual CORS `*` overrides | ~15 endpoints | ⚠️ Intentional for public trust/schema endpoints |

**CORS wildcard endpoints (all public-by-design, no auth required):**
- `/.well-known/omnix-public-key.json` — public key anchor
- `/.well-known/did.json` — DID document
- `/.well-known/openid-credential-issuer` — OpenID4VCI metadata
- `/schemas/omnix-receipt-schema-*.json` — JSON-LD schema
- `/api/trust/registry` — public trust registry
- `/api/trust/verify` — public stateless verifier
- `/api/governance/schema` — public signal schema
- Health check endpoints

**Assessment:** The wildcard overrides are appropriate for public read-only endpoints. No authenticated endpoints use wildcard CORS. The Flask-CORS global config correctly restricts all other routes.

### Rate Limiting

| Layer | Mechanism | Per-instance? |
|---|---|---|
| Flask-Limiter | Global default + per-endpoint decorators | Yes — not aggregated across dynos |
| gov_blueprint IP rate limit | In-memory store | Yes — per-dyno |
| gov_blueprint per-client limit | 30 req/min per client | Yes — per-dyno |
| `/api/trust/verify` | 60 per minute (Flask-Limiter) | Yes |
| `/api/governance/report` | 3 per minute, 10 per hour | Yes |

**Request size:** 1MB max content length enforced at Flask level.

### Hardcoded Credential (OMNIX-DEMO-DASHBOARD-KEY)

| Aspect | Detail |
|---|---|
| Location | Hardcoded in 4 frontend TSX files, default value in gov_blueprint.py |
| Visibility | Present in compiled React bundle — any user can inspect browser source |
| Access granted | Read-only aggregate dashboard endpoints (Anomaly, Breach, Risk, Execution) |
| Admin bypass | No — `require_admin=True` endpoints are never bypassed by this key |
| Mitigation | Set `DASHBOARD_API_KEY` env var in Railway to override default |
| Residual risk | Any external user who finds the key can query aggregate governance metrics |

**Assessment:** Intentional design for public-facing audit dashboards. The exposed data is aggregate read-only governance statistics. No individual decision data, client identity, or signing keys are accessible. Risk is LOW but should be documented in the enterprise deployment guide.

### Attack Paths (Realistic)

1. **Forged receipt submission to regulator** — MEDIUM probability, HIGH impact. Attacker generates their own Dilithium-3 keypair and presents a forged OMNIX receipt. Verifier accepts it. Mitigated only by out-of-band key comparison against `/.well-known`. → ETA-001.

2. **Dashboard data harvesting via hardcoded key** — LOW impact (aggregate data only). Any competitor or curious party can query anomaly, breach, risk, and execution aggregate counts using the publicly visible demo key.

3. **Rate limit bypass via multiple dynos** — LOW probability (Railway single-dyno is typical). Only relevant at scale. In-memory rate limiting doesn't aggregate.

4. **Clock skew anti-replay bypass** — LOW probability (requires NTP attack or compromised host). Extends or shrinks replay window.

---

## CATEGORY 8 — CHAIN OF CUSTODY AUDIT

### Lifecycle Map

| Stage | Actor | Mechanism | Verifiable? |
|---|---|---|---|
| **Creation** | `DecisionReceiptEngine.generate_receipt()` | PQC signature over canonical JSON payload | ✅ Yes — signature embedded in receipt |
| **Pre-storage hash** | `content_hash = SHA-256(canonical_payload)` | Computed at creation, before DB write | ✅ Yes |
| **Chain linking** | `prev_hash = last_hash_from_DB` | Linked to previous receipt's `content_hash` | ✅ Yes — chain traversable |
| **Storage** | `store_receipt()` → PostgreSQL | ACID INSERT | ✅ Yes |
| **Retrieval** | `GET /receipt/{id}` → DB lookup | No chain verification on read | ⚠️ See below |
| **Verification** | `POST /api/trust/verify` | Hash + PQC sig check against embedded key | ⚠️ No OMNIX key cross-reference |
| **Chain audit** | `verify_chain(receipts: list)` | Traverses prev_hash chain across N receipts | ✅ Function exists |

### Chain Integrity Gap (ETA-005)

`verify_chain()` exists in `decision_receipt.py` and correctly traverses the `prev_hash → content_hash` linkage. However, it is **not called on the standard receipt read path** (`GET /receipt/{id}`).

A DB administrator who modifies a receipt's fields would:
1. Break the `content_hash` (SHA-256 mismatch detectable by anyone)
2. Break the PQC signature (cryptographic mismatch detectable by anyone)
3. Break the `prev_hash` chain for all subsequent receipts (detectable by `verify_chain()`)

**But:** None of these are automatically verified when a receipt is retrieved via the API. The system reports the receipt contents without flagging tamper evidence. A verifier would need to explicitly call `verify_chain()` across a range of receipts to detect the break.

### What An External Auditor Cannot Detect (ETA-006)

- **Record deletion:** If a DB admin deletes a receipt record, the chain breaks at the deletion point. A subsequent `verify_chain()` call would show the break. But there is no automated chain integrity monitor that would alert on this in real time.
- **Orphaned receipts:** A decision that fails `store_receipt()` leaves the client with a valid receipt JSON that cannot be retrieved from the OMNIX DB (404). No audit trail exists for this event.

---

## CATEGORY 9 — PRODUCTION KILL-SWITCH AND EMERGENCY MODE

### Fail-Closed Verification by Component

| Failure Scenario | Behavior | Assessment |
|---|---|---|
| DB unavailable during `evaluate()` | Returns OMNIX-ERR receipt, BLOCKS decision | ✅ Fail-closed |
| DB unavailable, `AVM_FAIL_CLOSED=true` | Halts process entirely | ✅ Fail-closed (optional hardening) |
| Redis unavailable (anti-replay) | Falls to in-memory best_effort | ⚠️ Fail-open for anti-replay |
| AVM snapshot unavailable | Retries then applies fail-closed policy | ✅ Fail-closed |
| AI model unavailable | Fallback chain (OpenAI → Gemini → Anthropic) | ✅ Degraded, not failed |
| All AI models unavailable | Blocks evaluation with error | ✅ Fail-closed |
| Signer unavailable (PQC library) | Falls to SHA-256 only | ⚠️ Fail-open for PQC guarantee |
| Verifier unavailable | Returns 503 | ✅ Safe |
| `OMNIX_REQUIRE_PERSISTENT_KEYS=true`, keys absent | `SystemExit` — refuses to start | ✅ Fail-closed (new guard, this session) |

### Emergency Freeze (ETA-007)

There is no documented emergency freeze procedure for the web API. The Telegram bot has admin commands (`/pause`, `/resume` for trading), but there is no equivalent for:

- Suspending all governance evaluations immediately
- Putting the system in a read-only mode
- Revoking all active API keys simultaneously

**Available workarounds:**
- Remove `DATABASE_URL` env var in Railway → all DB-dependent endpoints fail with 503
- Set `AVM_FAIL_CLOSED=true` → AVM failures block evaluations
- Revoke individual API keys via `POST /api/client/rotate-key`

**Gap:** No single emergency lever to freeze all governance output without taking down the entire service.

### Redis Anti-Replay Status

`OMNIX_ANTI_REPLAY_MODE=strict` has been added to the web service in Railway. However, strict mode only activates when a Redis backend is reachable. If `REDIS_URL` is not set in the web service (confirmed: Redis is set in the bot service but web service status is unconfirmed), strict mode is configured but inactive — anti-replay operates in in-memory best_effort per dyno.

**Action required:** Confirm `REDIS_URL` is set in the Railway web service variable group, not only the bot service.

---

## CATEGORY 10 — EXTERNAL READINESS ASSESSMENT

### Institution-by-Institution Readiness

| Reviewer | Readiness | Key Concerns |
|---|---|---|
| **Hostile external auditor** | MEDIUM | ETA-001 (forged receipt), ETA-005 (no chain check on read), ETA-002 (DB outage leaves no receipt) |
| **Financial regulator** | MEDIUM-HIGH | "5 years MiFID II" requires COLD tier config; "MiCA-compliant" needs qualification |
| **Enterprise security team** | HIGH | Auth, rate limiting, CORS are solid; brute force lockout and IP allowlist active |
| **Skeptical investor** | HIGH | Live infrastructure confirmed, PQC confirmed, fail-closed confirmed; governance replay verifiable |
| **Malicious integrator** | MEDIUM | ETA-001 is the primary attack vector; can forge receipts that pass public verification |

---

## RANKED ACTION PLAN

### Priority 1 — Critical (Blocks External Institutional Trust)

| ID | Action | File | Impact |
|---|---|---|---|
| **ETA-001** | Add OMNIX trusted key registry check to verifier. Cross-reference embedded `public_key` fingerprint against `/.well-known/omnix-public-key.json`. Return `issuer_key_trusted: true/false` in verify response. | `omnix_core/evidence/verification_server.py` | Closes forged receipt attack |
| **ETA-003** | Confirm `REDIS_URL` is set in Railway **web service** (not just bot service). Without it, `strict` anti-replay mode is configured but inactive. | Railway environment variables | Closes cross-dyno replay risk |

### Priority 2 — High (Regulatory and Legal Defensibility)

| ID | Action | File | Impact |
|---|---|---|---|
| **ETA-002** | Add `pending_receipts` buffer (Redis or write-ahead log) for `store_receipt()` failures. Prevents orphaned decisions. | `omnix_web/api/gov_blueprint.py` | Closes MiFID II evidence continuity gap |
| **ETA-005** | Call `verify_chain()` on every receipt retrieval (or on a recent window). Return `chain_intact: true/false` in `GET /receipt/{id}` response. | `omnix_web/api/gov_blueprint.py` | Closes tampering detection gap on read |
| **ETA-006** | Set `OMNIX_REQUIRE_PERSISTENT_KEYS=true` in Railway. Prevents silent ephemeral key startup. | Railway environment variables | Hardens FMR-001 guard (code already deployed this session) |
| **ETA-007** | Implement emergency freeze endpoint (`POST /api/admin/emergency-freeze`) that sets a global flag blocking all `evaluate()` calls. | `omnix_web/api/gov_blueprint.py` | Closes kill-switch gap |

### Priority 3 — Medium (Legal Wording, Marketing Risk)

| ID | Action | File | Impact |
|---|---|---|---|
| **ETA-008** | Replace "MiCA-compliant" with "MiCA-aligned" across UI pages | `StablecoinDashboard.tsx`, `StablecoinGovernanceDemo.tsx` | Removes unsubstantiated certification claim |
| **ETA-009** | Replace "immutable" with "cryptographically-linked" where it refers to DB records | Multiple pages | More defensible against regulatory challenge |
| **ETA-010** | Replace "tamper-proof" with "tamper-evident" | Multiple pages | Technically accurate — hash integrity detects but does not physically prevent tampering |
| **ETA-011** | Replace "Receipt retention: Permanent" with "5-year minimum, hash-linked" | `IntegrationGuide.tsx` | Removes "permanent" (dependent on DB survival) |
| **ETA-012** | Rename "Regulatory Compliance & Certifications" section to "Regulatory Alignment Architecture" | `InstitutionalPage.tsx` | Removes implication of issued certification |
| **ETA-013** | Qualify "5 years (MiFID II)" with note: "HOT+WARM tiers via PostgreSQL; COLD tier requires S3/R2 configuration" | `GettingStarted.tsx` | Accurate disclosure of archival tier requirements |

### Priority 4 — Low (Operational Hygiene)

| ID | Action | File | Impact |
|---|---|---|---|
| **ETA-014** | Add `key_mode` field to `/.well-known/omnix-public-key.json` response: `"stable"` or `"ephemeral"` | `omnix_web/api/server.py` | Third parties can detect unstable key anchor |
| **ETA-015** | Add `key_version` increment to `did:web:omnixquantum.net#pqc-key-1` on key rotation | `omnix_web/api/server.py` | Enables third parties to detect key rotation |
| **ETA-016** | Set `DASHBOARD_API_KEY` env var in Railway to a non-guessable key. Document in enterprise deployment guide. | Railway + docs | Removes hardcoded credential from production |
| **ETA-017** | Add timestamp freshness check to `/api/trust/verify`: receipts older than configurable threshold get `stale: true` warning | `omnix_web/api/server.py` | Adversarial stale receipt detection |

---

## EVIDENCE CHAIN GAPS SUMMARY

| Gap | Severity | Status |
|---|---|---|
| Forged receipt with attacker keypair passes verifier (ETA-001) | CRITICAL | Open |
| DB outage during evaluate() leaves orphaned decision (ETA-002) | HIGH | Open |
| Anti-replay strict mode inactive without Redis in web service (ETA-003) | HIGH | Open — confirm REDIS_URL |
| Chain integrity not verified on receipt read path (ETA-005) | HIGH | Open |
| No emergency freeze for web API (ETA-007) | MEDIUM | Open |
| COLD tier archival requires S3/R2 not confirmed in production (ETA-013) | MEDIUM | Open |
| Key mode (stable/ephemeral) not signaled in trust anchor (ETA-014) | LOW | Open |
| `OMNIX_REQUIRE_PERSISTENT_KEYS=true` guard available but not set in Railway (ETA-006) | LOW | Actionable — one env var |

---

## WHAT IS ALREADY EXTERNALLY DEFENSIBLE

The following properties can be demonstrated to a hostile external party with no additional work:

1. **PQC signatures are genuine** — `mode=persisted` confirmed. Every receipt produced since key deployment is signed with a stable Dilithium-3 key. The public key is independently accessible at `/.well-known/omnix-public-key.json`.

2. **Hash integrity is mathematically provable** — SHA-256 of the canonical payload is embedded in every receipt. Any field modification produces a detectable mismatch. This is independently verifiable without OMNIX servers.

3. **Fail-closed governance is operational** — `external_evaluator.py` contains 12 fail-closed references. Governance decisions default to BLOCK under uncertainty. AVM FAIL_CLOSED option is available.

4. **Authentication is enterprise-grade** — Brute force lockout, role-based access, admin IP allowlist, key expiry enforcement, and per-client rate limiting are all active.

5. **Crisis replay receipts are independently verifiable** — The 12 receipts on `/crisis-replay` carry real SHA-256 hashes generated by the GovernanceReplayEngine. Any party can verify the hash integrity offline using `omnix_verify.py`.

6. **CORS is correctly configured** — Global Flask-CORS restricts authenticated endpoints to `omnixquantum.net`. Wildcard CORS is intentional and correct for public trust infrastructure endpoints only.

7. **Chain linking is implemented** — Every receipt carries a `prev_hash` pointing to the prior receipt's `content_hash`. `verify_chain()` can traverse any sequence of receipts and detect breaks.

---

*Report generated by internal audit stage 4 — HGA-2026-Q4-001. Next review recommended prior to first institutional B2B client onboarding or regulatory submission.*
