# SECURITY_AND_HARDENING_REPORT.md
## OMNIX QUANTUM — Security & Hardening Audit
**Date:** 2026-05-27 | **Method:** Static analysis, auth tracing, CORS audit

---

## EXECUTIVE SUMMARY

**5 CRITICAL security findings.** The most severe: 189 API routes lack authentication enforcement at the decorator level, including state-mutating endpoints. CORS wildcard (`*`) is set on 14+ governance endpoints. In-memory rate limiting resets on dyno restart. BAR PQC signing silently fails, producing unsigned turn attestations.

---

## SEC-001 — 189 API Routes Without Authentication Decorator [CRITICAL]
- **Severity:** CRITICAL
- **Files:** `omnix_web/api/agent_blueprint.py` (36 routes), `omnix_web/api/oversight_bp.py` (7 routes), `omnix_web/api/proof_layer.py` (3 routes), `omnix_web/api/health_blueprint.py` (3 routes), `omnix_web/api/sandbox.py` (2 routes), others
- **Description:** AST scan of all API blueprints found 189 route handlers with no authentication decorator (`@require_api_key`, `@login_required`, etc.). This includes **all** agent_blueprint routes: `register_agent`, `create_delegation`, `temporal_admit`, `continuity_start`, `continuity_sample` — state-mutating endpoints that insert records into ATF tables.
- **Clarification Required:** Some blueprints may rely on `before_request` middleware registered at the blueprint level rather than per-route decorators. `gov_blueprint.py` has a `before_request` auth check. `agent_blueprint.py` has no `before_request` registration visible from grep analysis.
- **Exploitability:** HIGH — if `agent_blueprint` has no `before_request` middleware, any unauthenticated HTTP client can register agents, create delegations, and start continuity sessions.
- **Institutional Impact:** CRITICAL — regulatory auditors will flag unprotected agent registration endpoints.
- **Verification Required:** Confirm whether `agent_blueprint.py` registers a `before_request` middleware auth hook. If not, this is a confirmed unauthenticated write endpoint.
- **Remediation:** Add explicit `@require_api_key` or `@require_auth` to all state-mutating routes. For public read routes (verify, badge), ensure they are read-only and rate-limited.

---

## SEC-002 — CORS Wildcard on Governance Endpoints [HIGH]
- **Severity:** HIGH
- **Files:** `omnix_web/api/proof_layer.py:1157,1524,1537`, `omnix_web/api/gov_blueprint.py:1944`, `omnix_web/api/server.py:1819,1840,1874,1900,1926,2013,2040,2074,2104,2186,2215`
- **Description:** `Access-Control-Allow-Origin: *` is manually set in response headers on 14+ endpoints, including governance receipt endpoints, institutional verification, and evaluate endpoints. While the top-level Flask CORS config in `server.py:56` uses a restricted origin list, these manual overrides bypass it.
- **Exploitability:** MEDIUM — CORS wildcard allows any browser origin to read governance receipt responses, including B2B client data, institutional verification results, and governance scores.
- **Impact:** Cross-site request forgery attacks from malicious sites can read governance responses on behalf of authenticated users. Cookie-based auth would be compromised.
- **Remediation:** Remove manual `Access-Control-Allow-Origin: *` headers from individual routes. Rely solely on Flask-CORS middleware with origin allowlist. For public endpoints (badge, public verify), CORS wildcard is acceptable.

---

## SEC-003 — In-Memory Rate Limiting Resets on Dyno Restart [HIGH]
- **Severity:** HIGH
- **File:** `omnix_web/api/sandbox.py:21-29`
- **Description:** `_rate_limit_store`, `_rate_limit_hourly_store`, `_rate_limit_daily_store` are module-level Python dicts. On Railway, each new dyno or deploy resets all rate limit counters. An attacker who saturates daily limits simply waits for a deploy or triggers an OOM to reset the counter.
- **Also:** `omnix_web/api/gov_blueprint.py:184,190` — `_brute_force_store` and `_blocked_ip_cache` same issue.
- **Exploitability:** HIGH — deliberate DoS → deploy cycle → repeat attack.
- **Remediation:** Use Redis for all rate limiting state. `server.py:74` already acknowledges this: use `REDIS_URL` for rate limit backend.

---

## SEC-004 — Oversight Endpoints Fully Unauthenticated (State-Mutating) [CRITICAL]
- **Severity:** CRITICAL
- **File:** `omnix_web/api/oversight_bp.py`
- **Lines:** 63 (`create_oversight_session`), 185 (`open_oversight_session`), 211 (`submit_oversight_review`), 333 (`expire_stale_sessions`)
- **Description:** The human oversight blueprint allows unauthenticated POST requests to create oversight sessions, open them, submit reviews, and expire existing sessions. These are write operations on the `oversight_sessions` table.
- **Exploitability:** HIGH — any unauthenticated attacker can: (1) create fake oversight approvals, (2) expire real oversight sessions before humans review them.
- **Attack Scenario:** Before a scheduled governance review, attacker POSTs to `expire_stale_sessions` → real sessions expire → review never happens. Alternatively, attacker creates fake "APPROVED" oversight sessions.
- **Remediation:** Require `X-API-Key` with admin role on all write endpoints in oversight_bp.

---

## SEC-005 — BAR PQC Signing Silently Fails — All Turn Attestations Unsigned [CRITICAL]
- **Severity:** CRITICAL
- **File:** `omnix_core/bev/behavioral_anchor_record.py:266`
- **Description:** The PQC signing method call is `pqc.sign_receipt(...)` but `PostQuantumSecurity` has no `sign_receipt` attribute. Every BAR record ever stored has `pqc_signature = null`. An adversary presenting BAR records to a verifier gets rejection. A regulator inspecting the attestation chain finds unsigned artifacts throughout.
- **Exploitability:** MEDIUM — cannot be exploited to forge BAR records. Impact is forensic integrity loss, not code execution.
- **Institutional Impact:** CRITICAL — "PQC-signed turn attestation" is a core product claim. Every BAR is unsigned.
- **Remediation:** Fix method call. Verify against `PostQuantumSecurity` class API.

---

## SEC-006 — AVM_AUTO_APPROVE Requires No Rotation After Use [MEDIUM]
- **Severity:** MEDIUM
- **File:** `omnix_core/governance/auto_modification_guard.py:89-93`
- **Description:** `AVM_AUTO_APPROVE=true` bypasses the AMG approval gate. There is no automatic expiry, rotation requirement, or audit trail requirement for this flag. Once set, it persists indefinitely until manually removed.
- **Remediation:** Add a `AVM_AUTO_APPROVE_EXPIRES_AT` env var. If the current timestamp exceeds it, treat as false regardless. Log every decision made while flag is active.

---

## SEC-007 — FORENSIC_EXPORT_ALLOW_CALLER_KEYS Documented but No Enforcement Guard [MEDIUM]
- **Severity:** MEDIUM
- **File:** `replit.md` + `omnix_web/api/`
- **Description:** `FORENSIC_EXPORT_ALLOW_CALLER_KEYS=true` is documented as "NEVER in production" (ADR-166 FEA-INV-005). There is no code enforcement — no startup assertion that verifies this is false in `ENVIRONMENT=production`. An operator error or a Railway deploy with this flag set would expose caller-controlled forensic exports.
- **Remediation:** Add `assert os.environ.get("FORENSIC_EXPORT_ALLOW_CALLER_KEYS", "false").lower() != "true" or os.environ.get("ENVIRONMENT") != "production"` in server.py startup.

---

## SEC-008 — Verification Server Silent Exception Swallowing [MEDIUM]
- **Severity:** MEDIUM
- **File:** `omnix_core/evidence/verification_server.py`
- **Lines:** 555, 606, 615, 674, 748, 756, 808
- **Description:** Multiple `except Exception: pass` blocks in the verification server. If receipt verification fails due to an exception (not a cryptographic failure), the server may return an incorrect result or silently drop the verification.
- **Remediation:** Replace bare `pass` with `return {"verified": False, "error": str(exc)}`. Never swallow verification exceptions.

---

## SEC-009 — Jurisdiction Gate Pass-Through on Exception [LOW]
- **Severity:** LOW
- **File:** `omnix_web/api/omnix_engine/jurisdiction_gate.py:239`
- **Description:** `reason=f"CP-11 Jurisdiction exception → pass-through: {exc}"` — jurisdiction gate exceptions result in pass-through (allow). Fail-open on exception for a compliance gate.
- **Impact:** If jurisdiction evaluation code throws any exception, the request proceeds without jurisdiction validation.
- **Remediation:** Fail-closed on jurisdiction gate exceptions (deny, log, and alert).

---

## SEC-010 — PQC Key Absence Falls Back to "UNSIGNED" Without Alerting [MEDIUM]
- **Severity:** MEDIUM
- **File:** `omnix_core/governance/anticipatory_governance_veto.py:113`
- **Description:** `return "UNSIGNED", "ML-DSA-65"` — if `OMNIX_SIGNING_SECRET_KEY_B64` is not set, AGVP PVRs are marked UNSIGNED and execution continues. No alert, no HALT.
- **Impact:** In a deployment where the PQC key env var is accidentally unset, all PVRs are unsigned and the system continues operating without notification.
- **Remediation:** Emit AVM CRITICAL alert on PQC key absence. Consider fail-closed for governance receipts (block issuance until key is available).

---

## SECURITY POSITIVE FINDINGS ✅

The following security controls are correctly implemented:
- PQC signing key management via Railway env vars ✅
- Anti-replay mode `strict` enforced in production via `OMNIX_ANTI_REPLAY_MODE` ✅
- B2B API key hash stored (never plaintext) in `b2b_clients` ✅
- Admin IP filtering via `ADMIN_ALLOWED_IPS` ✅
- `AVM_FAIL_CLOSED` available for DB failure scenarios ✅
- Flask-CORS with origin allowlist at top level ✅
- Dilithium-3 (ML-DSA-65) key-based signing when keys present ✅
- MIVP ProxyGuard keyword detection per turn ✅

---

*Report generated: 2026-05-27 | OMNIX QUANTUM Zero-Assumption Audit*
