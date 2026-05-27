# RUNTIME_REALITY_AUDIT.md
## OMNIX QUANTUM — Runtime Execution Reality Audit
**Date:** 2026-05-27 | **Method:** Static trace + dynamic test verification
**Last Updated:** 2026-05-27 — Correction pass

---

## CORRECTION LOG — 2026-05-27

| Finding | Status | Evidence |
|---|---|---|
| BAR/CTCHC PQC signing (related: HIDDEN-001/GOV-001) | ✅ **FIXED** | `BAREngine.create_bar` + `CTCHCEngine.seal_chain` now use `sign_message`. Runtime-verified: 3309B ML-DSA-65 sig, tamper detection OK. |
| RUNTIME-001 (AGVP TESTING stub) | ⏳ OPEN | No change in this pass. Requires adding key-presence guard in `anticipatory_governance_veto.py:99–108`. |
| RUNTIME-002 through RUNTIME-004 | ⏳ OPEN | Not addressed in this pass. |

---

## EXECUTIVE SUMMARY

Runtime trace of end-to-end governance flows reveals that the **protocol specification is largely sound** but has **4 runtime execution gaps** that prevent full enforcement in production. The most critical: AGVP PQC signature is a literal `"TESTING"` string when `TESTING=true` is active, and GOL metrics are never emitted.

---

## RUNTIME-001 — AGVP PQC Signature Returns Literal "TESTING" String
- **Severity:** CRITICAL
- **File:** `omnix_core/governance/anticipatory_governance_veto.py`
- **Lines:** 99–108
- **Description:** `_pqc_sign()` returns `("TESTING", "ML-DSA-65")` when `os.environ.get("TESTING") == "true"`. In production, `TESTING` must never be true. However, if a Railway deployment has `TESTING=true` set accidentally (or an operator runs a health check with this flag), all PVRs (Proactive Veto Receipts) will carry a `pqc_signature = "TESTING"` — not a real Dilithium-3 signature. Forensic verification of these PVRs will fail silently.
- **Exploitability:** MEDIUM — requires TESTING=true in production environment, which is documented as forbidden but has no enforcement guard.
- **Runtime Impact:** All PVRs issued become forensically invalid — offline verifiers will reject them but the platform continues operating normally.
- **Remediation:** Add a hard guard: if `TESTING=true` and `OMNIX_SIGNING_SECRET_KEY_B64` is set, sign anyway. Only use the stub if the key is genuinely absent. Log `CRITICAL` when stub is used.

---

## RUNTIME-002 — AVM Alert Suppression in TESTING Mode
- **Severity:** HIGH
- **File:** `omnix_core/governance/avm_alerts.py`
- **Line:** 118
- **Description:** `if os.environ.get("TESTING", "").lower() == "true": return` — all AVM alerts are suppressed when TESTING=true. This is correct for unit tests. However, the same risk as RUNTIME-001 applies: if `TESTING=true` reaches production, the AVM alert subsystem is completely silent. No HALT, CRITICAL, or WARNING alerts are dispatched.
- **Runtime Impact:** Governance violation notifications (Telegram, webhook) are never sent. Operators are blind.
- **Remediation:** Same mitigation as RUNTIME-001: add startup assertion `assert os.environ.get("TESTING") != "true", "TESTING=true in production"` in server.py.

---

## RUNTIME-003 — Transparency Chain TESTING Bypass Skips Operator Notification
- **Severity:** MEDIUM
- **File:** `omnix_core/evidence/transparency_chain.py`
- **Line:** 527
- **Description:** `if not admin_id or not token or os.environ.get("TESTING"): return` — Telegram notification for transparency events is skipped when TESTING=true. This affects the immutable transparency log notification path.
- **Runtime Impact:** Transparency chain entries are still written to DB (if available), but operator notifications are silently suppressed.
- **Remediation:** Factor out the Telegram notification from the chain persistence. TESTING=true should suppress notifications, not persistence.

---

## RUNTIME-004 — Snapshot Scheduler Skipped in TESTING Mode (SAE Layer 0)
- **Severity:** LOW (correct behavior for tests, low risk in production)
- **File:** `omnix_core/governance/structural_admissibility_engine.py`
- **Lines:** 268–278
- **Description:** `_start_snapshot_scheduler()` returns immediately when `TESTING=true`. The Layer 0 SAE snapshot scheduler is never started. This is correct for tests. If TESTING=true reaches production, no SAE snapshots are taken.
- **Runtime Impact:** Layer 0 activation state is not periodically snapshotted. Loss of SAE audit trail.
- **Remediation:** Same startup assertion as RUNTIME-001.

---

## RUNTIME-005 — Receipt Archival Exception Swallowing
- **Severity:** MEDIUM
- **File:** `omnix_core/evidence/receipt_archival.py`
- **Lines:** 609, 616, 1122
- **Description:** Multiple `except Exception: pass` blocks in the archival path. If a receipt fails to archive (network error, schema mismatch), the exception is swallowed and execution continues. No error counter is incremented, no alert is triggered.
- **Runtime Impact:** Receipt persistence failures are silent. The governance receipt may appear issued but is not archived.
- **Remediation:** Replace bare `pass` with `logger.error(...)` + `error_counter.increment("receipt_archival_failure")`. Consider fail-closed for forensic receipts (per FEA-INV-001).

---

## RUNTIME-006 — Exception Swallowing in BEV/Governance Layers
- **Severity:** HIGH
- **File:** `omnix_core/govern/governance_runtime.py`, `omnix_core/bev/*.py`
- **Description:** Multiple `except Exception: pass` blocks in governance_runtime.py (BEV PQC signing). The BAR PQC signing failure is logged as WARNING but does not fail the record_turn call. This means turns can be recorded without PQC attestation — the behavioral chain exists but individual BAR records are unsigned.
- **Evidence:** Log output shows `[BAR] PQC signing failed (non-blocking): 'PostQuantumSecurity' object has no attribute 'sign_receipt'` during stress test runs.
- **Runtime Impact:** BAR records have `pqc_signature = null` in production when Dilithium key unavailable. Offline verification of BAR records fails.
- **Root Cause:** `PostQuantumSecurity` object does not expose `sign_receipt()` method — the BAR layer calls the wrong method name.
- **Remediation:** Fix the method call. `PostQuantumSecurity` likely exposes `sign_data()` or `sign()`. Verify the correct API and wire it. Make PQC signing fail-closed for production BAR records.

---

## RUNTIME-007 — GOL Phase Metrics Never Emitted
- **Severity:** HIGH
- **File:** `omnix_core/observability/metrics.py` (complete module)
- **Description:** The entire GOL module (ADR-198, OBS-INV-001–006) was built but never integrated into the production execution path. `governance_runtime.py` does not import `GovernanceMetricsRegistry`. `record_turn()` and `close_session()` do not use `GovernancePhaseTimer`. `ErrorCounter` is never incremented.
- **Runtime Impact:** Zero telemetry emitted in production. The GOL module is build-complete but runtime-dead.
- **Remediation:** See GAP-001. Immediate: add 3 phase timer calls to `governance_runtime.py`.

---

## RUNTIME-008 — ATF Continuity _insert_rcr / _insert_cee Called from Background Queue
- **Severity:** LOW (implementation correct, risk is queue saturation)
- **File:** `omnix_core/agents/atf/rcr_performance.py`
- **Lines:** 277–329
- **Description:** `_insert_rcr()` and `_insert_cee()` are properly implemented with full SQL INSERTs. However, they run on a background worker thread queue. If the queue fills (e.g., during stress), tasks are dropped silently. The queue size is not monitored.
- **Runtime Impact:** RCR/CEE records may not be persisted during high-throughput events.
- **Remediation:** Add queue depth metric to GOL (when wired). Alert when queue > 80% capacity.

---

## RUNTIME FLOWS VERIFIED ✅

The following flows were traced and confirmed functional:
- `POST /v1/govern/session/start` → OGR session created, chain_genesis_hash computed ✅
- `POST /v1/govern/session/{id}/turn` → BAR created (PQC signing non-blocking) ✅
- `POST /v1/govern/session/{id}/close` → CTCHC sealed (requires DB) ✅
- `POST /v1/pogr/certify` → PoGC issued, persisted to pogr_certificates ✅
- `GET /v1/pogr/verify/{id}` → public verification endpoint active ✅
- `POST /v1/osg/validate` → OSG validation receipt persisted ✅
- AVM approval gate blocks on high drift ✅
- HALT propagation through ATF stack ✅
- MIVP ProxyGuard evaluation on each turn ✅

---

*Report generated: 2026-05-27 | OMNIX QUANTUM Zero-Assumption Audit*
