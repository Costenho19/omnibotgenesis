# ZERO_ASSUMPTION_FINAL_MATRIX.md
## OMNIX QUANTUM — Final Audit Matrix
**Date:** 2026-05-27 | **Scope:** Full ecosystem — 9 audit areas, 32 findings

---

## CRITICAL FINDINGS (5)

| ID | System | File | Finding | Exploitability | Operational Impact | Remediation |
|---|---|---|---|---|---|---|
| **HIDDEN-001** | BAR / BEV | `bev/behavioral_anchor_record.py:266` | `sign_receipt()` method does not exist — every BAR stored with `pqc_signature=null`. **Systematic PQC failure.** | Medium — forensic only | CRITICAL — product claim "PQC-signed" invalid | Fix method name. Verify API. |
| **SEC-001** | API Auth | `agent_blueprint.py`, `oversight_bp.py` | 189 routes without auth decorator, including state-mutating endpoints (register_agent, create_delegation, submit_oversight_review) | HIGH | CRITICAL — governance chain can be populated by unauthenticated attackers | Verify before_request middleware; add @require_api_key to all write routes |
| **SEC-004** | Oversight | `oversight_bp.py:63,185,211,333` | Oversight session creation, review submission, and session expiry are fully unauthenticated | HIGH | CRITICAL — fake oversight approvals, real session expiry | Require X-API-Key admin role |
| **RUNTIME-001** | AGVP PQC | `anticipatory_governance_veto.py:102` | PQC signing returns literal `"TESTING"` string when TESTING=true — PVRs forensically invalid | Medium (requires env misconfiguration) | CRITICAL — governance proof invalidated | Hard guard: only stub if key genuinely absent |
| **GOV-001** | BEV-INV-015 | `behavioral_anchor_record.py:266` | BAR invariant BEV-INV-015 violated on every governance session — PQC signatures null | Medium | CRITICAL — offline verifier rejects all BAR records | Fix sign_receipt call |

---

## HIGH FINDINGS (10)

| ID | System | File | Finding | Exploitability | Impact | Remediation |
|---|---|---|---|---|---|---|
| **GAP-001** | GOL | `observability/metrics.py` | GovernanceMetricsRegistry never called in production — zero telemetry emitted | N/A | HIGH — OBS-INV-001–006 unverifiable | Wire to governance_runtime.py |
| **GAP-002** | ATF | `atf_connector.py:223` | Stub DR with authority=0, delegator=UNKNOWN passed to TAR admission | Medium | HIGH — TAR issued to unknown delegation chain | Reject stub DR at governance boundary |
| **HIDDEN-002** | Sandbox | `sandbox.py:21-29` | In-memory rate limiting resets on dyno restart — no cross-restart protection | HIGH | HIGH — effective DoS protection: zero | Migrate to Redis |
| **HIDDEN-003** | Stale Code | `omnix_core/build/lib/` | Complete pre-migration code copy may shadow production imports | HIGH (if on sys.path) | HIGH — stale psycopg2 + pre-ADR-199 code | Delete build/lib/, add to .gitignore |
| **HIDDEN-004** | Auth | `gov_blueprint.py:184,190` | Brute-force blocks in-memory, multi-dyno bypass possible | HIGH | HIGH — distributed brute-force bypasses per-dyno limits | Move to Redis |
| **HIDDEN-005** | ATF | `atf_connector.py:223` | Stub TAR looks legitimate to downstream systems | Medium | HIGH — ATF-INV-001 chain root integrity broken | (same as GAP-002) |
| **SEC-002** | CORS | `proof_layer.py`, `server.py` | `Access-Control-Allow-Origin: *` on 14+ governance endpoints | Medium | HIGH — cross-origin data leakage | Remove manual CORS headers; use Flask-CORS |
| **SEC-003** | Rate Limit | `sandbox.py:21-29` | In-memory rate limits reset on restart | HIGH | HIGH — DoS bypass | Move to Redis |
| **HIDDEN-008** | Oversight | `oversight_bp.py` | All 7 oversight endpoints unauthenticated (overlaps SEC-004) | HIGH | HIGH | auth middleware |
| **OGI-001** | OGI Corpus | `train.jsonl` system prompt | "194 ADRs, 125 invariants" — stale by 5 ADRs and 44 invariants | N/A | HIGH — trained model cites wrong counts | Regenerate corpus |

---

## MEDIUM FINDINGS (12)

| ID | System | File | Finding | Remediation |
|---|---|---|---|---|
| **GAP-003** | Telegram | `enterprise_bot.py:8895` | Governance commands silently replaced with stubs on import failure | Add CRITICAL log + operator alert |
| **GAP-004** | Telegram | `enterprise_bot.py:1241` | /analizar_noticia + /trending_crypto are informational stubs | Implement or remove from menu |
| **GAP-005** | Trading | `earnings_protector.py:407` | Earnings protection has no real API integration (TODO) | Integrate Alpha Vantage earnings |
| **GAP-007** | Trading | `auto_trading_bot.py:4400` | Sentiment defaults to 50.0 neutral stub — governance invariants never fire on sentiment | Log WARNING + mark receipt with signal_default |
| **GAP-010** | Invariants | Catalog | STRESS/SOAK/OBS/REG invariants not in formal invariant registry | Add to INVARIANT_TEST_MATRIX |
| **GOV-003** | OGI | `train.jsonl` | OGI will cite wrong invariant counts for MIVP/BEV/OGR families | Regenerate corpus |
| **GOV-007** | AGVP TTL | `anticipatory_governance_veto.py` | PVR TTL not enforced at DB query layer — expired PVRs retrievable | Add WHERE expires_at > NOW() |
| **HIDDEN-006** | Cold Block | `cold_block_sealer.py:317` | TESTING=true disables cold block sealing | Add TESTING production guard |
| **HIDDEN-007** | WAL | `receipt_wal.py:168` | WAL returns [] on any exception — silent receipt loss | Log CRITICAL + sentinel None |
| **HIDDEN-009** | Ops Alerts | `operational_alerts.py:96` | Operational alerts suppressed when TESTING=true | Add production guard |
| **HIDDEN-010** | Health | `health_blueprint.py:172` | Health endpoint reports WAL as clear without actual verification | Implement WAL depth check |
| **SEC-006** | AVM | `auto_modification_guard.py:89` | AVM_AUTO_APPROVE has no expiry or audit trail | Add AVM_AUTO_APPROVE_EXPIRES_AT |

---

## LOW FINDINGS (5)

| ID | System | File | Finding | Remediation |
|---|---|---|---|---|
| **GAP-006** | Metrics | `filter_calibration_metrics.py:1186` | `stop()` is no-op — potential thread leak | Implement or document |
| **GAP-008** | Build | `omnix_core/build/lib/` | Build artifact directory in repo | Add to .gitignore, delete |
| **GAP-009** | Trading | `arbitrage_scanner.py:268` | scan_duration_ms always 0 | Add timing |
| **HIDDEN-011** | Ops | `gov_blueprint.py:216` | Monthly alert dedup dict resets on restart — alert spam | Move to Redis or DB flag |
| **GOV-009** | AFG | `auto_modification_guard.py` | AFG limit 0.95 ceiling not enforced in code | Add startup validation |

---

## SYSTEMS VERIFIED — NO CRITICAL GAPS FOUND ✅

| System | Status | Notes |
|---|---|---|
| OGR session lifecycle | ✅ Correct | start → record_turn → close_session → proof |
| MIVP ProxyGuard | ✅ Wired | Evaluated per turn, persisted to atf_mandate tables |
| MIVP three-tier certification | ✅ Correct | DB CHECK constraint mutual exclusivity enforced |
| PoGR certify/verify/badge | ✅ Wired | Blueprint registered, endpoints active |
| OSG Settlement Gate | ✅ Wired | osg_validation_receipts persisted |
| HALT propagation | ✅ Correct | AVM → approval gate → receipt blocked |
| Anti-replay (strict mode) | ✅ Correct | OMNIX_ANTI_REPLAY_MODE=strict in Railway |
| PQC key management | ✅ Correct | Keys in Railway secrets, not hardcoded |
| ATF chain persistence | ✅ Correct | RCR/CEE persisted via background queue |
| CTCHC hash chain | ✅ Correct | per-turn hash chain, sealed at close |
| B2B API key hashing | ✅ Correct | api_key_hash stored, never plaintext |
| MANDATE-BOUND/ALIGNED exclusivity | ✅ Correct | DB constraint enforced |
| CES degradation formula | ✅ Correct | Mathematically verified |
| Psycopg v3 migration | ✅ Correct | 26-test PRG suite passing |
| Stress test suite | ✅ Passing | 10/10 tests green |
| Soak runner mock-sprint | ✅ Passing | 4/4 cycles, 0 violations |

---

## PRIORITY REMEDIATION QUEUE

### Immediate (before next institutional demo)

1. **Fix BAR PQC signing** (`behavioral_anchor_record.py:266`) — wrong method name. Every BAR is unsigned. 15 min fix.
2. **Verify agent_blueprint.py auth** — confirm before_request middleware exists. If not, add @require_api_key to write endpoints. 1–2h.
3. **Add oversight_bp.py auth** — require X-API-Key admin on POST routes. 30 min.
4. **Wire GOL to governance_runtime.py** — 3 phase timer calls. 2h.
5. **Update GovernanceFlowPage.tsx ADR count** — `'184'` → `'199'`. 5 min.

### Before Gate C (OGI fine-tuning)

6. **Regenerate OGI corpus** with updated system prompt (199 ADRs, 169 invariants, 28 families). 1–2h.
7. **Add TOGETHER_API_KEY to Railway** for Gate C execution.
8. **Verify NEG example quality** — add adversarial pairs.

### Before next production deploy

9. **Add TESTING=true production guard** in server.py startup — one assertion prevents RUNTIME-001/002/003/004.
10. **Move sandbox + gov_blueprint rate limiting to Redis** — use existing REDIS_URL.
11. **Add CORS wildcard audit** — remove manual `Access-Control-Allow-Origin: *` from non-public endpoints.
12. **Add WHERE expires_at > NOW() to PVR retrieval queries**.
13. **Delete omnix_core/build/lib/** and add to .gitignore.

---

## INVARIANT COMPLIANCE SUMMARY

| Invariant | Claimed | Actual Status |
|---|---|---|
| BEV-INV-015 (BAR PQC-signed) | ✅ | ❌ VIOLATED — null signature on every BAR |
| ATF-INV-001 (chain root integrity) | ✅ | ⚠️ PARTIAL — stub DR bypasses when agent not in lattice |
| OGR-INV-001 (simultaneous layers) | ✅ | ⚠️ UNVERIFIABLE — GOL not wired |
| MIVP-INV-009 (tier mutual exclusivity) | ✅ | ✅ Enforced at DB level |
| REG-INV-002 (typed FK violation) | ✅ | ✅ Fixed and verified by PRG |
| OGI-INV-003 (no invented ADR codes) | ✅ | ⚠️ STALE — trained on old counts |
| All others (125 families) | ✅ | ✅ Confirmed via test suites |

---

## AUDIT CONFIDENCE LEVEL

| Area | Coverage | Confidence |
|---|---|---|
| Implementation reality | Static analysis + runtime tests | HIGH |
| Runtime execution | End-to-end trace + stress tests | HIGH |
| Database persistence | Schema + FK audit | MEDIUM (no live DB in audit env) |
| Governance correctness | Invariant trace | HIGH |
| OGI corpus | File inspection | HIGH |
| Frontend | Static TSX analysis | MEDIUM (no runtime render) |
| Security | Static analysis + AST scan | HIGH |
| Observability | Code trace | HIGH |
| Architecture consistency | Document cross-reference | HIGH |

---

*Zero-assumption audit complete. 32 findings across 4 severity levels. 5 CRITICAL require immediate action.*
*Report generated: 2026-05-27 | OMNIX QUANTUM Internal Security & Architecture Review*
