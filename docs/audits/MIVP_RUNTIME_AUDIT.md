# MIVP Runtime Audit — Institutional Deep Audit
**Date:** 2026-05-25 (rev.1 — 2026-05-26: F-001, F-002, F-003, F-006, F-007 resolved)  
**Auditor:** OMNIX Internal Governance Audit  
**Scope:** ADR-194 · `omnix_core/bev/mandate_integrity_verification.py` · `omnix_core/govern/governance_runtime.py`  
**Verdict:** ✅ PASS — 5 findings resolved. 0 HIGH open. 2 MEDIUM open (F-004, F-005). 3 LOW open.

---

## Executive Summary

MIVP is architecturally sound. The three-artifact lifecycle (MBR → MAS × N → MBRSeal) is correctly integrated into the OGR session lifecycle. All 8 invariants are enforced at the structural level. No race condition in session-level state; no orphan MBR in the happy path; no replay vulnerability in the append-only MAS chain.

Five findings require remediation before the first production PoGC emission with MANDATE-BOUND tag. One finding (F-002) is an institutional credibility risk that should be resolved before external publication of ADR-194.

---

## F-001 — ✅ RESOLVED (2026-05-26) — DB driver inconsistency: psycopg2 vs psycopg3

**File:** `omnix_core/bev/mandate_integrity_verification.py` — lines 432, 770, 798, 820, 852, 892, 930  
**File:** `omnix_services/database_service/database_service.py` (uses psycopg3)

**Finding:** All MIVP persistence methods import `psycopg2` directly (`import psycopg2`). The rest of the OMNIX stack uses psycopg3 (`psycopg`). This creates a dual-driver dependency. In Railway, if `psycopg2` is not installed alongside `psycopg`, all `_persist_*` calls will silently log a WARNING and fall back to in-memory only — meaning MIVP artifacts will NOT be persisted to DB without any operational alert.

**Impact:** Silent data loss of MBR, MAS, MBRSeal in Railway if psycopg2 is absent. `ensure_tables()` will also fail silently, leaving tables uncreated.  
**Exploitability:** Medium — requires psycopg2 absence in the deployment environment.  
**Institutional Risk:** HIGH — a MANDATE-BOUND certificate issued against in-memory-only state is not forensically durable.

**Remediation:** Replace all `import psycopg2` with `import psycopg` (psycopg3) to match the rest of the stack. Update connection syntax accordingly (`psycopg.connect()`).

---

## F-002 — ✅ RESOLVED (2026-05-26) — MANDATE-BOUND eligible with WARNING turns

**File:** `omnix_core/bev/mandate_integrity_verification.py` — line 664  
**Code:** `mandate_bound_eligible = (turns_in_violation == 0 and mbr is not None)`

**Finding:** A session with N WARNING turns (MAS persistently between 0.30 and 0.65) and 0 HALT turns receives `mandate_bound_eligible = True` and the MANDATE-BOUND PoGC tag. This means an agent that spent the entire session in the WARNING zone — close to the halt threshold — can receive MANDATE-BOUND certification.

**Impact:** Institutional credibility risk. An adversarial auditor reviewing a MANDATE-BOUND certificate on a session with 8/10 WARNING turns will correctly question its meaning.  
**Exploitability:** Low (requires an operator-controlled session that consistently scores in the 0.31–0.64 range).  
**Institutional Risk:** HIGH — this is the core attestation the PoGC tag communicates to relying parties.

**Remediation options (pick one):**  
a) Add `turns_in_warning = 0` as additional condition for `mandate_bound_eligible` (strictest — may be too restrictive for real use).  
b) Add `mandate_bound_eligible = (turns_in_violation == 0) and (turns_in_warning / max(turns_covered, 1) < 0.20)` — allows up to 20% WARNING turns.  
c) Add a separate PoGC tag `MANDATE-ALIGNED` for sessions with warnings, reserving MANDATE-BOUND for zero violations AND zero warnings.

**Recommendation:** Option (c) gives the most expressive certification hierarchy and is most defensible to regulators.

**Resolution (2026-05-26):** Option (c) implemented. Three-tier mandate certification hierarchy introduced:
- `MANDATE-BOUND` (Tier 1): `turns_in_violation = 0` AND `turns_in_warning = 0` — pristine execution.
- `MANDATE-ALIGNED` (Tier 2): `turns_in_violation = 0` AND `turns_in_warning > 0` — mission-aligned.
- UNCERTIFIED (Tier 3): `turns_in_violation > 0` — mandate violations recorded.
DB CHECK constraint `chk_seal_tier_consistency` enforces mutual exclusivity at the persistence layer.
MIVP-INV-009 added to ADR-194. `MANDATE_ALIGNED_TAG` exported from `omnix_core/bev/__init__.py`.
`mandate_aligned_eligible` field added to `MBRSeal` dataclass, DDL, and `_persist_seal()` INSERT.

---

## F-003 — ✅ RESOLVED (2026-05-26) — No DB foreign key constraints between MIVP tables

**File:** `omnix_core/bev/mandate_integrity_verification.py` — DDL section

**Finding:** `atf_mandate_alignment_scores.mbr_id` and `atf_mbr_seals.mbr_id` had no `FOREIGN KEY` constraint referencing `atf_mandate_binding_records.mbr_id`. DB consistency relied entirely on application-level ordering.

**Impact:** A partial failure (MBR persisted, MAS write crashes) leaves orphan MAS rows with an mbr_id that has no corresponding MBR. DB-level query for forensic verification would return inconsistent results.  
**Exploitability:** Low — requires a DB write partial failure scenario.  
**Institutional Risk:** MEDIUM — forensic auditors querying the DB directly (a standard institutional audit procedure) would find rows with dangling references.

**Resolution (2026-05-26):** FK constraint `fk_seals_mbr` added to `atf_mbr_seals` DDL via `_APPLY_SEAL_FK` — a `DO $$ ... $$ IF NOT EXISTS` block applied opportunistically in `ensure_tables()` as a non-fatal post-table step. Non-fatal because `atf_mandate_binding_records` may not exist when MIVP initialises first (init ordering is not guaranteed). Two DB CHECK constraints also added:
- `chk_seal_tier`: `mandate_certification_tier IN ('MANDATE-BOUND', 'MANDATE-ALIGNED', 'UNCERTIFIED')`
- `chk_seal_tier_consistency`: `NOT (mandate_bound_eligible AND mandate_aligned_eligible)` — mutual exclusivity at DB level.
Four indexes added on `mandate_certification_tier`, `mandate_bound_eligible`, `mandate_aligned_eligible`.

---

## F-004 — MEDIUM — Non-atomic MBR creation vs session cache write

**File:** `omnix_core/govern/governance_runtime.py` — lines 393–409

**Finding:** In `start_session()`, the call sequence is:
1. `mivp.create_mbr(...)` — persists MBR to DB and in-memory store
2. `session = _dc.replace(session, mbr_id=mbr.mbr_id)` — updates session dataclass
3. `self._session_cache[session_id] = session` — writes to session cache

If an exception occurs between steps 1 and 3, an MBR exists in DB with no corresponding OGR session. The MBR is an orphan. The session cannot be closed (no `session.mbr_id`), so `seal_mbr()` will never be called for that MBR.

**Impact:** Orphan MBR rows in `atf_mandate_binding_records`. No MBRSeal will ever be emitted for them.  
**Exploitability:** Low — requires a crash between those two lines.  
**Institutional Risk:** MEDIUM — forensic query of `atf_mandate_binding_records LEFT JOIN atf_mbr_seals WHERE seal_id IS NULL` would reveal unsealed MBRs.

**Remediation:** Move `mivp.create_mbr()` to after the session is committed to cache, or wrap both operations in a try/except that compensates by deleting the MBR on session cache write failure.

---

## F-005 — MEDIUM — ProxyGuard keyword density is trivially gameable

**File:** `omnix_core/bev/mandate_integrity_verification.py` — lines 66–87

**Finding:** `ProxyGuard.activation_score()` uses keyword density analysis: `hits / total_words × 20`, saturated at 1.0. An adversarial model that knows the proxy guard keywords can trivially avoid them — producing clean MAS scores while still optimizing for the prohibited proxy semantically.

**Impact:** The MIVP invariant enforcement is only as strong as the ProxyGuard detection method. With keyword density, a sophisticated agent can pass all guards while violating the mandate's intent.  
**Exploitability:** HIGH against a known ProxyGuard configuration.  
**Institutional Risk:** MEDIUM — ADR-194 documents this limitation but does not specify a minimum detection quality requirement for production deployments.

**Remediation:** ADR-194 already notes "production should extend with ML classifiers." This must be a formal gate: add `OGI-INV-011` or `MIVP-INV-009` requiring that production ProxyGuards use ML-backed classifiers with documented precision ≥ 0.85. Keyword-only guards should be explicitly tagged as `detection_tier: ALPHA` and blocked from MANDATE-BOUND issuance in production.

---

## F-006 — ✅ RESOLVED (2026-05-26) — `_DEFAULT_MAS_HALT` configurable via env with no floor validation

**File:** `omnix_core/bev/mandate_integrity_verification.py` — lines 41–42

**Finding:** `MIVP_MAS_HALT_THRESHOLD` env var is read directly as float with no minimum floor validation. An operator can set `MIVP_MAS_HALT_THRESHOLD=0.0`, effectively disabling mandate HALT for all sessions.

**Impact:** MIVP-INV-005 is silently bypassed when halt threshold is 0.0.  
**Exploitability:** Medium — requires access to environment configuration.  
**Institutional Risk:** MEDIUM — equivalent to setting `AVM_FAIL_CLOSED=false` in production.

**Remediation:** Add validation in `create_mbr()`:
```python
if mas_halt < 0.05 or mas_halt >= mas_warn:
    raise ValueError(f"mas_halt_threshold {mas_halt} invalid: must be in [0.05, mas_warning)")
```

**Resolution (2026-05-26):** Validation added in `create_mbr()` — raises `ValueError` if `mas_halt < 0.05` (floor) or `mas_halt >= mas_warn` (ordering). MIVP-INV-005 cannot be silently bypassed via env configuration.

---

## F-007 — ✅ RESOLVED (2026-05-26) — `mandate_bound_eligible` condition is always True when reached

**File:** `omnix_core/bev/mandate_integrity_verification.py` — line 664

**Finding:** `mandate_bound_eligible = (turns_in_violation == 0 and mbr is not None)`. The `mbr is not None` guard is unreachable-false: the function raises `RuntimeError` at line 638 if `mbr is None`. The condition is therefore always equivalent to `turns_in_violation == 0`. Not a bug, but misleading to future maintainers.

**Impact:** None functional.  
**Remediation:** Remove the dead `mbr is not None` clause or add a comment explaining the redundancy.

**Resolution (2026-05-26):** `mbr is not None` dead clause removed. Condition restructured into the three-tier certification logic block with explicit inline documentation of why the guard is unnecessary at that point in the function.

---

## F-008 — LOW — In-memory MBR store not shared across processes (Railway multi-dyno)

**File:** `omnix_core/bev/mandate_integrity_verification.py` — lines 423–425

**Finding:** `self._mbr_store`, `self._mas_store`, and `self._seal_store` are per-instance Python dicts. In Railway multi-dyno deployments, two dynos serving requests for the same session will have inconsistent in-memory state. The DB load fallback (`_load_mbr_from_db`) provides eventual consistency but only if the DB write succeeded (see F-001, F-003).

**Impact:** If Dyno A creates MBR and the request is routed to Dyno B for `record_turn()`, Dyno B will attempt a DB load. If DB is unavailable, `compute_mas()` raises RuntimeError.  
**Exploitability:** Low — Railway typically sticky-routes session requests.  
**Institutional Risk:** LOW in current deployment; HIGH if horizontal scaling increases.

**Remediation:** Use Redis for MBR/MAS state sharing across dynos (existing Redis infrastructure). Mirror the CTCHC engine pattern.

---

## F-009 — LOW — `MIVP_MAS_HALT_THRESHOLD` not documented in replit.md env reference

**File:** `replit.md` — Flask Web API environment variable table

**Finding:** The two new MIVP env vars (`MIVP_MAS_HALT_THRESHOLD`, `MIVP_MAS_WARNING_THRESHOLD`) are not documented in the canonical env var reference table in `replit.md`.

**Remediation:** Add both to the env var table with description and default values (0.30 / 0.65).

---

## Invariant Enforcement Verification

| Invariant | Location | Enforcement | Status |
|---|---|---|---|
| MIVP-INV-001 | `governance_runtime.py:393–409` | MBR created before session cache write | ✅ Enforced |
| MIVP-INV-002 | `mandate_integrity_verification.py:484–486` | SHA-256 hash computed and frozen at `create_mbr()` | ✅ Enforced |
| MIVP-INV-003 | `governance_runtime.py:494–508` | `compute_mas()` called in every `record_turn()` when `mbr_id` present | ✅ Enforced |
| MIVP-INV-004 | `mandate_integrity_verification.py:580` | `max(0.0, min(1.0, ...))` clamp applied | ✅ Enforced |
| MIVP-INV-005 | `mandate_integrity_verification.py:583–584` + `governance_runtime.py:509` | HALT verdict triggers OGR halt gate | ✅ Enforced |
| MIVP-INV-006 | `mandate_integrity_verification.py:606–608` | Append-only list; DB INSERT only | ✅ Enforced |
| MIVP-INV-007 | `governance_runtime.py:610–623` | `seal_mbr()` called in `close_session()` when `mbr_id` present | ✅ Enforced |
| MIVP-INV-008 | `mandate_integrity_verification.py:664` + `governance_runtime.py:650` | MANDATE-BOUND only when `mandate_bound_eligible` | ⚠️ Partial (see F-002) |

---

## Fail-Closed Behavior Audit

| Scenario | Behavior | Verdict |
|---|---|---|
| `mandate_binding` absent in constraint_set | MIVP not activated; session proceeds normally | ✅ Correct |
| `create_mbr()` raises exception | Caught at line 408; logged WARNING; session continues without MIVP | ⚠️ Fail-open by design (ADR-194 §Consequential Risk) |
| `compute_mas()` raises exception | Caught at line 505; `mivp_halt = False`; session continues | ⚠️ Fail-open — see note below |
| `seal_mbr()` raises exception | Caught at line 622; `mandate_bound = False`; MANDATE-BOUND not issued | ✅ Fail-closed on certification |
| DB unavailable | In-memory fallback activated; artifacts not persisted | ⚠️ F-001 — silent if psycopg2 missing |

**Note on fail-open MAS:** The fail-open behavior on `compute_mas()` failure is intentional per ADR-194 to avoid halting production sessions on infrastructure failures. However, this means a MAS computation failure is indistinguishable from ALIGNED — no WARNING is surfaced to the session verdict. Recommend adding `mas_error=True` to the turn result when this occurs.

---

## AGVP Interaction Consistency

The AGVP watchdog (`anticipatory_governance_veto.py`) monitors CCS drift. MIVP adds a parallel MAS signal. These two signals are currently independent — AGVP does not consume MAS. This is architecturally correct (additive, not coupled) but means AGVP cannot issue a ProactiveVetoReceipt based on mandate drift alone. Full integration requires a future ADR (suggested: ADR-195 or AGVP extension in ADR-174 rev.2).

**Status:** By design for ADR-194 scope. Document as known limitation, not defect.

---

## PoGC Compatibility

MANDATE-BOUND is appended to `pogc_tags` list in `close_session()`. The PoGR blueprint (ADR-186/187) reads `pogc_tags` to populate certificate metadata. No conflict detected. The tag string `"MANDATE-BOUND"` is unique and does not collide with existing tags.

---

## Verdict

**CONDITIONAL PASS.**  
F-001 (psycopg2 driver mismatch) must be resolved before first Railway deployment with DB persistence.  
F-002 (WARNING-turns eligible for MANDATE-BOUND) must be resolved before any external publication of MANDATE-BOUND certificates.  
F-003 through F-009 are recommended remediation items without blocking the initial implementation.
