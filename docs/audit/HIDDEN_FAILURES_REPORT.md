# HIDDEN_FAILURES_REPORT.md
## OMNIX QUANTUM — Hidden Failures & Silent Risk Audit
**Date:** 2026-05-27 | **Method:** Static analysis + runtime trace
**Last Updated:** 2026-05-27 — Correction pass

---

## CORRECTION LOG — 2026-05-27

| Finding | Status | Evidence |
|---|---|---|
| **HIDDEN-001** (BAR PQC signing) | ✅ **FIXED** | `sign_receipt` → `sign_message(payload_bytes, sk_bytes)` in `behavioral_anchor_record.py`. Runtime-verified: ML-DSA-65, sig=3309B, verify OK, tamper detected. Source: `BAREngine.create_bar` + `CTCHCEngine.seal_chain` both confirmed using `sign_message`. `sign_receipt` confirmed absent. |
| HIDDEN-002 through HIDDEN-011 | ⏳ OPEN | Not addressed in this pass. See individual findings below. |

---

## EXECUTIVE SUMMARY

This report documents **11 hidden failure modes** that do not surface as crashes, test failures, or logged errors. They fail silently, produce incorrect state, or quietly degrade governance guarantees.

---

## HIDDEN-001 — BAR PQC Signing Uses Wrong Method Name (Silent Non-Signing)
- **Severity:** CRITICAL → ✅ **FIXED 2026-05-27**
- **File:** `omnix_core/bev/behavioral_anchor_record.py`
- **Fix:** Replaced `.sign_receipt()` (non-existent) with `.sign_message(payload_bytes, sk_bytes)` + `base64.b64encode(sig_raw).decode()`. Same fix applied to `CTCHCEngine.seal_chain` in `coherence_hash_chain.py`.
- **Verification:** Runtime test confirmed — `PostQuantumSecurity.generate_keypair_signature()` → sign → verify → OK. Signature length: 3309 bytes (ML-DSA-65 nominal). Tampered payload: verify returns False. Env-var path (base64 Railway secret → decode → sign → verify): OK. `sign_receipt` confirmed absent from both source files.
- **BEV-INV-015 status:** ✅ Now satisfied — every future BAR persisted will carry a valid ML-DSA-65 PQC signature.

---

## HIDDEN-002 — In-Memory Rate Limiting Resets on Dyno Restart
- **Severity:** HIGH
- **File:** `omnix_web/api/sandbox.py`
- **Lines:** 21–29 (`_rate_limit_store`, `_rate_limit_hourly_store`, `_rate_limit_daily_store`)
- **Also:** `omnix_web/api/gov_blueprint.py:184` (`_brute_force_store`, `_blocked_ip_cache`)
- **Description:** All rate limiting and brute-force blocking state is stored in module-level Python dicts. On Railway, dynos restart periodically (deploys, crashes, memory pressure). After a restart, every attacker IP is unblocked and all rate limit counters reset to zero.
- **Why Hidden:** Works correctly within a single process lifetime. Tests pass. No error is logged.
- **Impact:** An attacker can exhaust daily limits, get blocked, then trigger a dyno restart (OOM attack or deploy) to reset all blocks. Effective rate limiting: zero cross-restart.
- **Note:** `server.py:74` acknowledges this: `[RateLimit] REDIS_URL not set — using in-memory storage`. If REDIS_URL is set, the rate limiting may be Redis-backed (need to verify which endpoints use it). But sandbox.py explicitly uses in-memory dicts.
- **Remediation:** Move sandbox and gov_blueprint rate limit state to Redis. Use `omnix_core/cache/redis_state.py` or a dedicated Redis key prefix.

---

## HIDDEN-003 — Stale Code in `omnix_core/build/lib/` May Shadow Production Code
- **Severity:** HIGH
- **File:** `omnix_core/build/lib/` (entire subtree)
- **Description:** A complete copy of omnix_core source (before the psycopg v3 migration and ADR-196–199) exists at `omnix_core/build/lib/`. If this path appears in `sys.path` before the live source, Python will import stale code. `omnix_core/build/lib/governance/avm_alerts.py`, `structural_admissibility_engine.py`, etc. all exist and contain pre-migration code.
- **Why Hidden:** Python silently imports from the first matching path. No import error. No warning.
- **Detection:** `python -c "import omnix_core.governance.avm_alerts; print(omnix_core.governance.avm_alerts.__file__)"` — if this returns a path containing `/build/lib/`, the stale version is active.
- **Impact:** All psycopg v3 migration work and ADR-196–199 hardening may be bypassed.
- **Remediation:** Delete `omnix_core/build/`. Add to `.gitignore`. Verify Python path.

---

## HIDDEN-004 — Cross-Dyno Brute-Force Block Bypass
- **Severity:** HIGH
- **File:** `omnix_web/api/gov_blueprint.py`
- **Lines:** 184, 190
- **Description:** `_brute_force_store: dict = {}` and `_blocked_ip_cache: dict = {}` — brute-force tracking for the governance API is in-memory per-process. On multi-dyno Railway deployments, an attacker can distribute attempts across dynos to evade per-dyno limits. With N dynos, each dyno sees 1/N of the attacks and never triggers the block threshold.
- **Why Hidden:** Single-dyno testing shows correct blocking behavior. Multi-dyno failure is invisible in development.
- **Impact:** Brute-force attacks against `/v1/govern/evaluate`, `/v1/govern/session/start`, etc. can bypass rate limiting.
- **Remediation:** Use Redis for brute-force state. Key: `brute_force:{ip}:{endpoint}`.

---

## HIDDEN-005 — ATF Connector Stub DR Admission Creates Legitimate-Looking TARs
- **Severity:** HIGH
- **File:** `omnix_core/agents/atf/atf_connector.py:223`
- **Description:** When no DR found, a synthetic `stub_dr` with `authority_budget_granted=0.0` and `delegator_id="UNKNOWN"` is created and passed to `engine.admit_execution()`. The TAR issued is PQC-signed and stored in `atf_temporal_records`. To a downstream consumer, this TAR looks legitimate — it has a real signature and a real timestamp.
- **Why Hidden:** The TAR is valid from a cryptographic standpoint. Only the `connector_note` metadata field reveals it was issued from a stub DR.
- **Impact:** Governance receipts with `delegator_id=UNKNOWN` could satisfy downstream ATF checks that don't verify the full delegation chain. An adversarial agent can register under any ID not in the lattice and receive a signed TAR.
- **Remediation:** Reject `admit_execution()` if DR is a stub. Return 403 from the ATF endpoint.

---

## HIDDEN-006 — Cold Block Sealer Skipped in TESTING Mode
- **Severity:** MEDIUM
- **File:** `omnix_core/evidence/cold_block_sealer.py`
- **Lines:** 142, 153, 317
- **Description:** `testing = os.environ.get("TESTING", "").lower() in ("1", "true")` — cold block sealing (COLD evidence lifecycle transition) is disabled in TESTING mode. If TESTING=true reaches production, COLD blocks are never sealed. Receipt archival depends on cold block sealing for long-term forensic integrity.
- **Why Hidden:** Testing infrastructure intentionally disables this. The gap is invisible until a forensic audit tries to retrieve COLD evidence.

---

## HIDDEN-007 — Receipt WAL Returns Empty List on Any Exception
- **Severity:** MEDIUM
- **File:** `omnix_core/evidence/receipt_wal.py`
- **Lines:** 168, 182
- **Description:** Both `get_pending()` and `get_all()` methods return `[]` on any exception. If the WAL encounters a DB error or schema mismatch, it silently reports zero pending receipts. Dependent systems (archival scheduler, replay) assume the WAL is empty.
- **Why Hidden:** No error is logged when these fallbacks trigger. Caller code sees `[]` and exits normally.
- **Impact:** Receipts waiting for archival may be permanently lost without any alert.
- **Remediation:** Log `CRITICAL` when WAL read fails. Add error metric. Return a sentinel `None` to force callers to handle the error state.

---

## HIDDEN-008 — `oversight_bp.py` Endpoints Fully Unauthenticated
- **Severity:** HIGH
- **File:** `omnix_web/api/oversight_bp.py`
- **Lines:** 63, 126, 164, 185, 211, 259, 333
- **Description:** All oversight session endpoints — including `create_oversight_session`, `submit_oversight_review`, and `expire_stale_sessions` — have no authentication decorator. Any anonymous HTTP client can create fake oversight sessions, submit fraudulent reviews, and expire real sessions.
- **Why Hidden:** The blueprint is registered in server.py and accessible. There is no 401 response.
- **Impact:** Complete human oversight simulation bypass. An attacker can pre-populate the oversight DB with fake APPROVED reviews.
- **Remediation:** Add `@require_api_key` decorator from `gov_blueprint.py` auth layer to all state-mutating routes.

---

## HIDDEN-009 — Operational Alerts Suppressed in TESTING Mode
- **Severity:** MEDIUM
- **File:** `omnix_core/ops/operational_alerts.py`
- **Line:** 96
- **Description:** `if os.getenv("TESTING", "").lower() == "true": return` — operational alerts are suppressed. Same risk as RUNTIME-001/002.

---

## HIDDEN-010 — Health Endpoint Reports WAL as Clear Without Verification
- **Severity:** MEDIUM
- **File:** `omnix_web/api/health_blueprint.py`
- **Lines:** 172–226
- **Description:** The health endpoint comments: `"WAL write-path verified via DB schema (in-memory WAL not loaded)"` — it cannot actually verify WAL state and reports it as clear. A health check that returns `healthy: true` while the WAL is backed up is a false negative.
- **Why Hidden:** Health checks return 200 OK regardless of WAL state.

---

## HIDDEN-011 — `_monthly_alert_sent` Dict Never Persisted
- **Severity:** LOW
- **File:** `omnix_web/api/gov_blueprint.py`
- **Line:** 216
- **Description:** `_monthly_alert_sent: dict = {}` — tracks which monthly alerts have been sent. Resets on dyno restart. Monthly cost/usage alerts can fire multiple times per month after each restart.
- **Impact:** LOW — alert spam, not a security issue.

---

*Report generated: 2026-05-27 | OMNIX QUANTUM Zero-Assumption Audit*
