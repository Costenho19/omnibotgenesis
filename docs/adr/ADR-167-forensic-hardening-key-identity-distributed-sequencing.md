# ADR-167 — Forensic Layer Hardening: Key Identity Registry, Distributed Block Sequencing & Verifier Determinism

**Status:** ACCEPTED  
**Date:** 2026-05-15  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Scope:** Forensic verification layer — `omnix_core/evidence/`, `omnix_web/api/forensic_blueprint.py`, `omnix_web/src/pages/ArchiveVerifierPage.tsx`, `docs/zenodo/submission_package/omnix_atf_verify.py`  
**Supersedes / Extends:** ADR-163 (pipeline), ADR-164 (portal), ADR-165 (OEP format), ADR-166 (export auth)

---

## 1. Context

Third adversarial audit of the OMNIX forensic governance stack produced 11 findings across three severity tiers. This ADR documents the architectural decisions made to address all 11 findings, with particular emphasis on the four systemic hardening dimensions:

1. **Key identity ambiguity** — the `/verify` oracle could be used to validate fabricated evidence against a non-platform key, producing a server-signed `PASS` verdict indistinguishable from a legitimate one.
2. **Block ID collision in distributed deployments** — in-process sequence counters cannot guarantee uniqueness across Railway dynos.
3. **Verifier library non-determinism** — a multi-library fallback chain in the standalone verifier violated EAP-INV-005 (platform independence) and introduced wire-format inconsistency risk.
4. **Non-distributed rate limiting** — per-process Flask-Limiter counters rendered rate caps proportional to dyno count.

Additional findings addressed: UI export authentication (P0-001), bash arithmetic in `verify_all.sh` (P1-001), nanosecond timestamp sort overflow in UI (P2-001), custody log truncation without notice (P2-003).

---

## 2. Decisions

### 2.1 Key Identity Fingerprinting in `/verify` Response (P0-002)

**Decision:** The `/api/forensic/verify` endpoint now computes and returns a `key_identity` object in every response.

**Fields:**
```json
{
  "key_identity": {
    "provided_fingerprint": "sha256:abcdef...",
    "platform_fingerprint": "sha256:123456...",
    "matches_platform": true,
    "warning": null
  }
}
```

**Semantics:**
- `provided_fingerprint` — SHA-256 of the public key bytes sent by the caller (base64-decoded).
- `platform_fingerprint` — SHA-256 of `OMNIX_SIGNING_PUBLIC_KEY_B64` env var bytes. `null` if the platform key is not configured server-side.
- `matches_platform` — `true` iff both fingerprints are present and identical. `null` if either is missing.
- `warning` — populated (non-null) when `matches_platform === false` or when the platform key is not server-side-configured.

**Warning text when `matches_platform === false`:**
> "PROVIDED KEY DOES NOT MATCH OMNIX PLATFORM KEY — this block was not signed by OMNIX QUANTUM LTD. A PASS verdict here is NOT a platform endorsement."

**Rationale:** The `/verify` endpoint intentionally accepts arbitrary public keys to allow offline verification of any ML-DSA-65–signed data. This is by design — EAP-INV-005 requires that verification work without platform access. However, without key identity disclosure, an adversary can submit a block signed with their own key, receive a `PASS` verdict from the OMNIX server, and present that verdict as platform endorsement. The `key_identity` field makes the distinction explicit and machine-readable. Any UI or API consumer can check `matches_platform` and render the appropriate trust level.

**Browser UI behavior:** When `key_identity.warning` is present, the verification notes section of `ArchiveVerifierPage.tsx` displays it prominently. When `matches_platform === true`, a positive confirmation is also shown.

**Server logging:** Every request where `matches_platform === false` produces a `WARNING` log entry with the provided fingerprint, platform fingerprint, and client IP. This enables forensic audit of potential abuse attempts.

**Invariant established (FVP-INV-007):**
> Every `/verify` response MUST include a `key_identity` object. If the platform key is configured, `platform_fingerprint` MUST be populated. Suppressing `key_identity` is not permitted.

---

### 2.2 Distributed Block ID Sequencing via Redis INCR (P0-003)

**Decision:** `_next_block_id()` in `omnix_core/evidence/cold_block_sealer.py` now uses Redis `INCR` as the primary sequence source.

**Key schema:** `omnix:block_seq:{YYYYMMDD}` (e.g. `omnix:block_seq:20260515`)  
**TTL:** 30 days (set with `EXPIRE ... NX` on first increment — does not reset existing TTL)  
**Atomicity:** Redis `INCR` is atomic by definition. No locking, no transactions needed.

**Fallback:** If `REDIS_URL` is not set or Redis is unreachable at call time, the function falls back to an in-process counter **with a `WARNING` log entry**. This fallback is explicitly documented as unsafe for multi-process deployments. The fallback does NOT trigger in test environments (`TESTING=true`) to avoid spurious warnings.

**Implementation notes:**
- Redis client is lazy-initialized on first call, cached at module level.
- `socket_timeout=2.0s` prevents sealing from hanging if Redis is slow.
- If Redis `INCR` raises after initialization, the error is logged at `ERROR` level and the process falls back to the in-process counter for that sealing cycle only.

**Production requirement:** `REDIS_URL` MUST be set in Railway. Railway already provides Redis as a managed service (already required for anti-replay and Flask-Limiter in ADR-123).

**Invariant established (EAP-INV-007):**
> Block IDs MUST be globally unique across the platform lifetime. In production (REDIS_URL present), uniqueness is guaranteed by atomic Redis INCR. In test/dev (no REDIS_URL), uniqueness is best-effort within a single process.

---

### 2.3 Distributed Rate Limiting via Redis Storage (P1-002)

**Decision:** Flask-Limiter `storage_uri` is now set to `REDIS_URL` when present, falling back to `"memory://"` only in local dev environments.

**Rationale:** With N Railway dynos, in-memory storage produces N independent rate counters. The effective rate limit becomes `N × configured_limit`. Since Railway auto-scales on load, a volumetric attack that triggers auto-scaling would simultaneously raise the effective rate limit — a perverse incentive. Redis INCR-based counters are shared across all dynos, making the configured rate limit a true per-IP ceiling regardless of scale.

**Production requirement:** `REDIS_URL` MUST be set (already required — same Redis instance as anti-replay and block sequencing).

**Startup behavior:** If `REDIS_URL` is not set at import time, a `WARNING` log entry is emitted. The server starts normally (development mode) but rate limits are in-process only.

---

### 2.4 Single-Library Verifier Determinism (P1-005)

**Decision:** `_verify_pqc_signature()` in `docs/zenodo/submission_package/omnix_atf_verify.py` now uses **only `pypqc` (`pqc.sign.dilithium3`)** for ML-DSA-65 verification. The `dilithium` package fallback and `omnix_core.security.crypto_providers` fallback are permanently removed.

**Removed fallbacks:**
1. `import dilithium` — third-party package with potentially different wire format from `pypqc`.
2. `from omnix_core.security.crypto_providers import get_active_provider` — imports from the OMNIX platform codebase, violating EAP-INV-005 (standalone independence).

**New behavior when `pypqc` is not installed:**
```
(False, "UNAVAILABLE", "pypqc not installed. Install with: pip install pypqc\npypqc is the only supported library for ML-DSA-65 verification in this tool.")
```

**Rationale:**
- Wire-format portability: ML-DSA-65 is standardized in FIPS 204, but library implementations may differ in byte packing, encoding, or API contracts. A verifier that silently switches libraries can produce verdicts that are not reproducible across installations.
- Platform independence (EAP-INV-005): The `omnix_core` fallback made the "standalone" verifier depend on the OMNIX codebase. This is contradictory by definition. An auditor without OMNIX access would get a different result than one with it.
- Determinism guarantee: With a single library, the verdict for any given `(block, key, signature)` triple is deterministic across all environments that have `pypqc` installed.

**Migration note:** Any existing OEPs verified with the `dilithium` fallback that produced `PASS` should be re-verified with `pypqc`. If a signature produced by the OMNIX platform (which uses `pypqc` for signing) fails with `pypqc` for verification, that is a genuine verification failure — not a library compatibility issue.

---

### 2.5 Export UI Authentication (P0-001)

**Decision:** The `generateOEP()` function in `ArchiveVerifierPage.tsx` sends the `X-API-Key` header from the `exportApiKey` state variable.

**UI design:**
- "Set Operator Key" button toggles an inline key input panel (password type).
- A `401` response from the server automatically reveals the key input panel and sets an error message explaining that admin credentials are required.
- A successful export shows a success banner with: package ID, block count, key source, and filename.
- All HTTP error codes (401, 403, 503, 400, other) produce distinct, actionable error messages.

**Rationale:** The export endpoint was authenticated in ADR-166 but the UI was not updated. This left the primary user-facing export path silently broken in production. The key input panel follows the design system (Gold `#C9A227` / Navy `#0A1628`) and is non-disruptive — it appears only when needed (on demand or after a 401).

---

### 2.6 Bash Arithmetic Safety in `verify_all.sh` (P1-001)

**Decision:** All `((VAR++))` constructs in the generated `VERIFY/verify_all.sh` script are replaced with `VAR=$((VAR+1))`.

**Root cause:** In bash with `set -e` (enabled at the top of `verify_all.sh`), an arithmetic expression `((N))` that evaluates to **0** returns exit code 1. `FAIL=0; ((FAIL++))` evaluates to 0 (FAIL was 0, post-increment returns old value 0) → exit code 1 → `set -e` terminates the script. The first missing block encountered causes the script to die instead of counting the failure.

**Fix:** `FAIL=$((FAIL+1))` is a variable assignment — it always returns exit code 0 regardless of the computed value.

The `if [[ ! -f "$BLOCK" ]]; then` guard was also added to make the intent clearer and avoid arithmetic evaluation in a conditional context.

---

### 2.7 Nanosecond Timestamp Sort Safety (P2-001)

**Decision:** All sorting of `BlockData` objects in `ArchiveVerifierPage.tsx` now uses `BigInt()` comparison via the `safeBlockCmp` comparator.

**Root cause:** `creation_timestamp_ns` values are Unix nanosecond timestamps (~1.78 × 10¹⁸ for 2026 dates). `Number.MAX_SAFE_INTEGER` is ~9.0 × 10¹⁵. Subtraction of two values above this range produces imprecise results due to IEEE 754 double precision loss. The sort `(a, b) => a.timestamp - b.timestamp` was not guaranteed to produce correct chronological order.

**Fix:** `safeBlockCmp` uses `BigInt(a._rawCreationTimestampNs ?? '0')` vs `BigInt(b._rawCreationTimestampNs ?? '0')` and returns `-1/0/1` by comparison, not subtraction. `_rawCreationTimestampNs` is the string representation parsed before any number coercion.

Applies to: `chartData` useMemo sort, chain graph display sort.

---

### 2.8 Custody Log Truncation Notice (P2-003)

**Decision:** The HTML report generated inside OEP packages now displays an explicit amber warning row when the custody log was truncated to the first 200 entries.

**Warning text:**
> "⚠ Report shows first 200 of N custody entries. Full custody log available in CUSTODY/custody_log.json within this package."

**Rationale:** A forensic report that silently omits evidence is indefensible. The full log is preserved in the package's `CUSTODY/custody_log.json` — the report truncation is a display-only constraint. The notice ensures that a reader of the HTML report knows to consult the JSON for the complete record.

---

## 3. Invariants Summary

| ID | Statement | Enforcer |
|---|---|---|
| FVP-INV-007 | Every `/verify` response includes `key_identity` with `platform_fingerprint` when the platform key is configured | `forensic_blueprint.py` |
| EAP-INV-007 | Block IDs are globally unique across all processes; guaranteed by Redis INCR in production | `cold_block_sealer.py` |
| EAP-INV-005 (strengthened) | The standalone verifier (`omnix_atf_verify.py`) has zero dependency on the OMNIX platform codebase | `omnix_atf_verify.py` |

---

## 4. Production Deployment Requirements

The following Railway environment variables are now required for full production compliance:

| Variable | Reason | Consequence if missing |
|---|---|---|
| `REDIS_URL` | Distributed rate limiting (P1-002) + Block ID sequencing (P0-003) | Rate limits per-dyno; block ID collisions possible in multi-dyno |
| `OMNIX_SIGNING_PUBLIC_KEY_B64` | Key identity fingerprinting (P0-002) | `platform_fingerprint: null` — cannot confirm key authenticity |

Both variables were already required for prior ADRs (anti-replay, PQC signing). This ADR adds two additional uses to an already-required infrastructure dependency.

---

## 5. Security Considerations

### 5.1 Key Fingerprint Disclosure

The `platform_fingerprint` field in `/verify` responses discloses the SHA-256 of the platform public key. This is intentional — the public key is already distributed in every OEP and is by definition public. SHA-256 of a public key is not a secret; it is a verification handle. There is no security benefit to hiding it.

### 5.2 Redis as Single Point of Failure for Block Sequencing

If Redis becomes unavailable at seal time, the sealer falls back to in-process counters with a log WARNING. This means a transient Redis outage during a multi-dyno sealing event could theoretically produce a block ID collision. Mitigation: the `FAIL_CLOSED` pattern (if strict uniqueness is required, fail the seal rather than use the fallback) is available as a future enhancement. Current decision is availability-over-strictness for sealing, given that block ID collisions are detectable post-facto via chain integrity verification.

### 5.3 Rate Limit Storage Key Prefix

Flask-Limiter stores rate limit counters in Redis under its own key namespace (default: `LIMITS:`). No conflict with the block sequence keys (`omnix:block_seq:*`) or anti-replay keys. If Redis is shared between services, key namespace isolation is maintained.

---

## 6. Audit Trail

| Finding | Severity | Fix | Files Changed |
|---|---|---|---|
| P0-001: UI export broken — no X-API-Key header | P0 | API key input + error handling in export UI | `ArchiveVerifierPage.tsx` |
| P0-002: Verify oracle accepts any key (trust inversion) | P0 | `key_identity` object in `/verify` response | `forensic_blueprint.py`, `ArchiveVerifierPage.tsx` |
| P0-003: Block ID collision in multi-process | P0 | Redis INCR atomic sequence | `cold_block_sealer.py` |
| P1-001: `((FAIL++))` with `set -e` kills verify script | P1 | `FAIL=$((FAIL+1))` arithmetic assignment | `oep_generator.py` |
| P1-002: Rate limiting not distributed | P1 | Redis storage for Flask-Limiter | `server.py` |
| P1-005: Multi-library verifier fallback | P1 | Single library (pypqc only), platform-independent | `omnix_atf_verify.py` |
| P2-001: chartData sort unsafe BigInt | P2 | `safeBlockCmp` with BigInt comparison | `ArchiveVerifierPage.tsx` |
| P2-003: Custody log truncation silent | P2 | Truncation notice in HTML report | `oep_generator.py` |

*P1-003 (public key registry) and P1-004 (key rotation protocol) are addressed by this ADR architecturally but require a separate operational runbook. Tracked as OMNIX-SEC-2026-001.*

---

## 7. References

- ADR-163 — Immutable Evidence Archive Pipeline
- ADR-164 — Forensic Archive Verification Portal
- ADR-165 — OMNIX Evidence Package (OEP) Format
- ADR-166 — Forensic Export Authentication (RBAC)
- RFC-ATF-1 — Agent Trust Fabric Formal Specification
- RFC-ATF-2 — Runtime Governance Continuity (published)
- EAP-INV-001–007 — Evidence Archive Pipeline Invariants
- FVP-INV-001–007 — Forensic Verification Portal Invariants
- FIPS 204 — Module-Lattice-Based Digital Signature Standard (ML-DSA-65)
