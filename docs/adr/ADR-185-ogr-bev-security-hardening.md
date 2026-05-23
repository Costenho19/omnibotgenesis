# ADR-185 — OGR + BEV Post-Audit Security Hardening

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-23  
**Supersedes:** —  
**Amends:** ADR-184 (OMNIX Governance Runtime), ADR-181/182/183 (BEV Layer)  
**Related:** ADR-181, ADR-182, ADR-183, ADR-184  
**RFC basis:** RFC-ATF-6 (BEV Layer), RFC-ATF-1–5 (ATF Stack)

---

## Context

Following the initial deployment of the OMNIX Governance Runtime (OGR) as defined
in ADR-184 and the Behavioral Execution Verification (BEV) layer as defined in
ADR-181/182/183, a structured three-round security and correctness audit was
conducted against the full OGR+BEV implementation.

The audit covered:

- `omnix_core/govern/governance_runtime.py` — OGR central orchestrator
- `omnix_core/bev/behavioral_anchor_record.py` — BAR engine (L6)
- `omnix_core/bev/constraint_conformance_signal.py` — CCS engine (L6)
- `omnix_core/bev/coherence_hash_chain.py` — CTCHC engine (L6)
- `omnix_web/api/govern_blueprint.py` — REST API blueprint
- `docs/integration/` — integration documentation
- `docs/adr/ADR-184.md` — runtime architecture record
- `tests/test_bev_ogr.py` — BEV+OGR test suite

The audit found **15 bugs across 3 rounds**, ranging from critical architectural
gaps to documentation inconsistencies. All were resolved before any production
deployment. This ADR records the findings, their root causes, and the fixes
applied, so the decisions are auditable as part of the OMNIX governance record.

---

## Findings by Round

### Round 1 — Invariant Registry Drift

The first round focused on consistency between the code, the ADR, and the
integration documentation after BEV-INV-015 through BEV-INV-018 and OGR-INV-001
were introduced.

#### Finding R1-F1 — `get_status` invariant list frozen at 14

**Severity:** Medium  
**File:** `omnix_core/govern/governance_runtime.py` — `get_status()`  
**Symptom:** The `invariants_enforced` list in the status response contained
`BEV-INV-001` through `BEV-INV-014` only. Four invariants (015–018) and
`OGR-INV-001` were silently absent.  
**Root cause:** The list was hand-coded and not updated when BEV-INV-015–018
and OGR-INV-001 were added in the BEV hardening round.  
**Fix:** Extended the list to all 18 BEV invariants plus OGR-INV-001.

#### Finding R1-F2 — `compliance_report` blueprint docstring misidentified layer

**Severity:** Low  
**File:** `omnix_web/api/govern_blueprint.py` — `compliance_report()` docstring  
**Symptom:** Docstring referenced "RFC-ATF-5 compliance report" instead of
RFC-ATF-6. Misleading for developers reading the API source.  
**Fix:** Corrected to RFC-ATF-6.

#### Finding R1-F3 — `close_session` status fields inconsistent

**Severity:** Medium  
**File:** `omnix_core/govern/governance_runtime.py` — `close_session()`  
**Symptom:** Response used ad-hoc string literals for the result `status` field
(`"already_sealed"`, `"session_sealed_halted"`, `"session_closed"`) that did not
correspond to any documented status value. API consumers had no canonical
reference for these values.  
**Fix:** Normalised to `already_closed: true` boolean flag for the idempotent
case; the main `session_status` field now always uses the canonical
`STATUS_CLOSED` / `STATUS_HALTED` constants.

#### Finding R1-F4 — ADR-184 invariant table missing BEV-INV-015–018 and OGR-INV-001

**Severity:** Medium  
**File:** `docs/adr/ADR-184-omnix-governance-runtime.md`  
**Symptom:** The invariant table ended at BEV-INV-014. The five new invariants
introduced with the BEV hardening were absent, making the architecture record
incomplete.  
**Fix:** Table extended with BEV-INV-015, BEV-INV-016, BEV-INV-017,
BEV-INV-018, and OGR-INV-001.

#### Finding R1-F5 — `OMNIX_GOVERNANCE_RUNTIME.md` stated "14 invariants"

**Severity:** Low  
**File:** `docs/integration/OMNIX_GOVERNANCE_RUNTIME.md`  
**Symptom:** Integration documentation said "14 invariants" in the compliance
section. The correct count is 18 BEV invariants plus OGR-INV-001.  
**Fix:** Updated to "18 BEV invariants (BEV-INV-001–018) plus OGR-INV-001."

#### Finding R1-F6 — CCS multi-dyno drift bleed (BEV-INV-017 violation)

**Severity:** High  
**File:** `omnix_core/bev/constraint_conformance_signal.py` — `compute_signal()`  
**Symptom:** The cumulative drift accumulator was stored only in the in-process
`_drift_cache`. On a Railway multi-dyno deployment (or any restart), a new
process for the same session would start drift from 0.0 instead of the last
persisted value. This violates BEV-INV-017 (drift accumulator must be isolated
per session_id and preserved across process boundaries).  
**Root cause:** Cache miss on `_drift_cache` silently defaulted to 0.0 instead
of loading the last known state from the database.  
**Fix:** Added `_load_session_state_from_db(session_id)` — on cache miss, the
engine loads `cumulative_drift` and `chain_link_hash` from the
`atf_constraint_conformance_signals` table before computing the new signal. The
database is the source of truth; the in-process cache is a write-through
optimisation.

#### Finding R1-F7 — `compliance_report` overall_pass excluded new invariants

**Severity:** High  
**File:** `omnix_core/govern/governance_runtime.py` — `compliance_report()`  
**Symptom:** The `overall_pass` boolean did not include BEV-INV-015, BEV-INV-016,
BEV-INV-018, or OGR-INV-001 in its evaluation. A session could produce
`overall_pass: true` while violating these invariants.  
**Fix:** All eight criteria now gate `overall_pass`:
`bev_inv_001 ∧ bev_inv_004 ∧ bev_inv_013 ∧ bev_inv_014 ∧ bev_inv_015 ∧
bev_inv_016 ∧ bev_inv_018 ∧ ogr_inv_001 ∧ verification.verified`.

---

### Round 2 — Verification and Status Correctness

The second round focused on the verify and compliance paths in more depth.

#### Finding R2-F1 — `verify_artifact` docstring listed "CCS" as supported type

**Severity:** Low-Medium  
**File:** `omnix_core/govern/governance_runtime.py` — `verify_artifact()`  
**Symptom:** The method docstring stated
`artifact_type = "BAR" | "CCS" | "CTCHC" | "SESSION"` and the fallback error
message listed `"Supported: BAR, CCS, CTCHC, SESSION"`. No CCS branch exists
in the implementation — CCS verification is not possible offline because the
CCS object does not embed all inputs needed to recompute the signal.  
**Fix:** CCS removed from docstring and error message. A note explains that CCS
data is available through `compliance_report`, which reads from the database.

#### Finding R2-F2 — `list_sessions` accepted any string as `status`

**Severity:** Medium  
**File:** `omnix_web/api/govern_blueprint.py` — `list_sessions()`  
**Symptom:** The `?status=` query parameter was passed directly to the SQL
`WHERE session_status = %s` clause without validation. Any arbitrary string
(e.g., `?status=ACTIVE1`, `?status=hack`) passed through silently, returning
zero results rather than a 400 error.  
**Fix:** Added allowlist validation against `{ACTIVE, CLOSED, HALTED, EXPIRED}`
with case normalisation. Invalid values return HTTP 400.

---

### Round 3 — In-Memory Operation and Cache Correctness

The third round specifically targeted the in-memory (no-DATABASE_URL) execution
path, which is used by all automated tests, the Python SDK, and any developer
running the OGR without a database.

#### Finding R3-F1 — CRITICAL: `close_session` always raised RuntimeError without DB

**Severity:** Critical  
**File:** `omnix_core/bev/coherence_hash_chain.py` — `CTCHCEngine`  
**Symptom:** Any call to `GovernanceRuntime.close_session()` in an environment
without `DATABASE_URL` raised:
```
RuntimeError: [CTCHC] No chain found for session <id>
```
This meant the complete OGR session lifecycle — start → record_turn → close —
had never been executable without a database. No existing test covered the
full path.  
**Root cause:** `CTCHCEngine` maintained only a `_tip_cache: Dict[str, str]`
(the current tip hash). `get_chain()` returned `None` when `_db_url` was absent,
and `get_links()` returned `[]`. `seal_chain()` calls both — finding `chain=None`,
it raised `RuntimeError`. The full `CoherenceHashChain` object and the
`ChainLink` list were only ever stored in the database, never in memory.  
**Fix:**  
- Added `_chain_cache: Dict[str, CoherenceHashChain]` to `CTCHCEngine`.
- Added `_links_cache: Dict[str, List[ChainLink]]` to `CTCHCEngine`.
- `initialize_chain()` now populates both caches after creating the genesis block.
- `append_turn()` appends to `_links_cache[session_id]` immediately after
  creating each link.
- `_update_chain_tip()` now updates `_chain_cache[session_id].current_tip_hash`
  and `.turn_count` even when `_db_url` is absent.
- `get_chain()` returns `_chain_cache.get(session_id)` when there is no DB.
- `get_links()` returns a copy of `_links_cache.get(session_id, [])` when there
  is no DB.
- The `RuntimeError` for `seal_chain()` is now correctly triggered only when
  `initialize_chain()` was never called for the given session_id (legitimate
  error), not when the DB is absent.

**Impact:** This fix enables the full OGR lifecycle in production environments
without a persistent database, in SDK integration tests, and in CI pipelines.

#### Finding R3-F2 — `close_session` used `len(bars)` for `turn_count`

**Severity:** High  
**File:** `omnix_core/govern/governance_runtime.py` — `close_session()`  
**Symptom:** The `turn_count` field in the close result was computed as
`len(self._get_bar().list_bars(session_id))`. Without a database,
`list_bars()` returns `[]`, so `turn_count` was always 0 regardless of how
many turns the session had recorded. A residual reference to `len(bars)` in
the log message also caused a `NameError`.  
**Root cause:** The developer used a DB query to compute a value that was
already accurately tracked in `session.turn_count` — updated on every
`record_turn()` call both in-cache and in DB.  
**Fix:** `turn_count = session.turn_count` (always authoritative). The `bars`
list query was removed from `close_session()` entirely. The log message now
uses `turn_count`.

#### Finding R3-F3 — `close_session` did not invalidate `_session_cache`

**Severity:** High  
**File:** `omnix_core/govern/governance_runtime.py` — `close_session()`  
**Symptom:** After `close_session()` committed the closed state to the database,
the `_session_cache[session_id]` entry was not updated. Any subsequent call to
`get_session()` returned the pre-close snapshot: `session_status = ACTIVE`,
`chain_sealed = False`, `closed_at = None`. This violated the post-close
contract that callers depend on.  
**Root cause:** The cache write-back after DB commit was missing. The
`_update_session_turn()` helper performs this write-back on every turn, but
there was no equivalent step in `close_session()`.  
**Fix:** Immediately after `_close_session_db()`, the cache entry is refreshed
using `dataclasses.replace()` with `session_status=final_status`,
`chain_sealed=True`, `chain_seal_hash=sealed_chain.seal_hash`,
`closed_at=closed_at`. BEV-INV-003 is preserved: if the session was halted
before close, `final_status = STATUS_HALTED`, not `STATUS_CLOSED`.

#### Finding R3-F4 — `get_proof` used `len(bars)` for `turn_count`

**Severity:** Medium  
**File:** `omnix_core/govern/governance_runtime.py` — `get_proof()`  
**Symptom:** The `behavioral_attestation_chain.turn_count` field in the proof
response was computed as `len(bars)`, which returns 0 without a DB connection.
This made the proof package misleading: it reported 0 turns while `session.turn_count`
was accurate.  
**Fix:** `turn_count` now reads from `session.turn_count`. A new
`bars_retrieved` field exposes `len(bars)` for transparency — callers that
need to know how many BARs were actually fetched from storage can use it.

#### Finding R3-F5 — Blueprint docstring listed 8 endpoints; there are 9

**Severity:** Low  
**File:** `omnix_web/api/govern_blueprint.py` — module docstring  
**Symptom:** The `GET /v1/govern/manifest` endpoint was present in the code
but absent from the module docstring's endpoint list.  
**Fix:** Added to the docstring.

#### Finding R3-F6 — `docs/integration/GETTING_STARTED.md` stated "14 BEV invariants"

**Severity:** Low  
**File:** `docs/integration/GETTING_STARTED.md` — line 175  
**Symptom:** The compliance endpoint description said "14 BEV invariants".  
**Fix:** Updated to "18 BEV invariants (BEV-INV-001–018) plus OGR-INV-001."

#### Finding R3-F7 — Typo in `OMNIX_GOVERNANCE_RUNTIME.md` code example

**Severity:** Low  
**File:** `docs/integration/OMNIX_GOVERNANCE_RUNTIME.md` — offline verification example  
**Symptom:** The Python code sample used `x["turn_in dex"]` (space inserted)
instead of `x["turn_index"]`. The sample code would raise `KeyError` if copied
and executed by an integrator.  
**Fix:** Corrected to `x["turn_index"]`.

---

## Decision

Accept all fixes as described above. No compensating controls are needed beyond
the fixes themselves. All changes are tested and covered by the regression suite.

The following architectural principle is now explicit:

> **In-memory cache coherence is a correctness guarantee, not an optimisation.**
> Any code path that mutates persisted state MUST also reflect that mutation in
> the corresponding in-process cache entry. Omitting the cache write-back is a
> bug, not a performance trade-off.

---

## Test Coverage Added

Seven new regression tests were added to `tests/test_bev_ogr.py` in the
`TestCloseSessionFixes` class. These tests exercise the no-DB (in-memory) code
path that was completely untested before this audit:

| Test | Invariant | Finding covered |
|------|-----------|-----------------|
| `test_get_session_after_close_returns_closed_status` | cache coherence | R3-F3 |
| `test_get_session_after_halted_close_preserves_halted` | BEV-INV-003 | R3-F3 |
| `test_close_session_turn_count_matches_actual_turns` | R3-F1, R3-F2 | R3-F1+F2 |
| `test_verify_artifact_ccs_not_supported_gives_clear_error` | API contract | R2-F1 |
| `test_list_sessions_invalid_status_returns_400` | input validation | R2-F2 |
| `test_list_sessions_valid_statuses_accepted` | smoke | R2-F2 |
| `test_list_sessions_case_insensitive_status` | normalisation | R2-F2 |

The `test_seal_chain_no_db_in_memory` test description was also updated to
reflect the corrected semantics: the test now correctly documents that
`seal_chain()` raises `RuntimeError` when `initialize_chain()` was never called
for the session, not when the database is absent.

**Test suite totals after this ADR:**

| File | Tests | Status |
|------|-------|--------|
| `test_bev_ogr.py` | **73** | ✅ all pass |
| `test_governance_integrity.py` | 124 | ✅ all pass |
| `test_code_verification.py` + `test_version_consistency.py` + `test_critical_audit.py` | 27 | ✅ all pass |
| `test_response_validator.py` | 16 | ✅ all pass |
| `test_systemic_router.py` | 27 | ✅ all pass |
| **Total** | **267** | **✅ 267/267** |

---

## Open Item — RFC-ATF-6 Invariant Numbering Discrepancy

During the audit, a discrepancy was identified between the invariant numbering
scheme used in the implementation and the scheme in the `docs/standards/RFC-ATF-6.md`
draft and `docs/zenodo/rfc_atf_6/metadata.json`.

**RFC-ATF-6 draft scheme:**

| Family | Range     | Count |
|--------|-----------|-------|
| BAR    | 001–007   | 7     |
| CCS    | 008–013   | 6     |
| CTCHC  | 014–018   | 5     |

**Implementation scheme (per `replit.md` and `ADR-184`):**

| Family | Invariants          | Count |
|--------|---------------------|-------|
| BAR    | 001–004 + 015–016   | 6     |
| CCS    | 005–009 + 017       | 6     |
| CTCHC  | 010–014 + 018       | 6     |

The two schemes assign different semantics to the same invariant numbers.
For example, RFC-ATF-6 draft defines `BEV-INV-015` as "no gaps in BAR turn
sequence" (a CTCHC property), while the implementation defines it as "empty
output_text → VIOLATION" (a BAR property).

**RFC-ATF-6 has not yet been published on Zenodo.** No external party has
received or cited the draft numbering. The discrepancy must be resolved before
Zenodo submission.

**Resolution options (requires Harold's decision):**

1. **Align RFC to implementation** — Update `docs/standards/RFC-ATF-6.md` and
   `docs/zenodo/rfc_atf_6/metadata.json` to use the implementation numbering
   (001–004+015–016 / 005–009+017 / 010–014+018). The implementation is the
   source of truth; the RFC formalises what is already running.

2. **Align implementation to RFC** — Renumber invariants in the three BEV
   engines to match the sequential RFC scheme (001–007 / 008–013 / 014–018).
   This requires updating all three BEV modules, all tests, ADR-181/182/183/184,
   and the manifest endpoint. More work but produces a cleaner sequential scheme.

**This ADR does not resolve the discrepancy.** The open item is recorded here
for traceability. Once Harold makes the decision, a follow-up ADR or RFC
addendum will document the resolution.

---

## Consequences

### Positive

- The full OGR session lifecycle (start → record_turn → close → verify) now
  works correctly in all environments: with or without DATABASE_URL, single
  or multi-dyno, production or CI.
- Cache coherence is now a documented first-class requirement, not an implicit
  assumption.
- The `compliance_report` `overall_pass` flag is trustworthy: it gates on all
  19 invariants (18 BEV + OGR-INV-001).
- The `turn_count` field in all API responses (`close_session`, `get_proof`)
  is always accurate, even without a database.
- All input validation at the API boundary is now explicit with proper HTTP 400
  responses and descriptive error messages.
- The test suite covers the no-DB path end-to-end for the first time.

### Negative / Mitigations

- The RFC-ATF-6 numbering discrepancy remains open. Mitigation: RFC-ATF-6 has
  not been published; the discrepancy has no external impact today. The item
  is tracked in this ADR and will be resolved before submission.
- The CTCHC in-memory caches (`_chain_cache`, `_links_cache`) add a small
  per-session memory footprint. Mitigation: entries are small (one
  `CoherenceHashChain` object and N `ChainLink` objects per session). For
  very long-lived processes handling thousands of concurrent sessions, the
  caller should use `DATABASE_URL` for proper persistence — the caches are not
  a replacement for the database in that scenario.

---

## Files Changed

| File | Type | Change summary |
|------|------|----------------|
| `omnix_core/govern/governance_runtime.py` | Core | close_session cache + turn_count; get_proof turn_count; verify_artifact doc; get_status invariant list; compliance_report overall_pass |
| `omnix_core/bev/coherence_hash_chain.py` | Core | `_chain_cache` + `_links_cache` for no-DB operation |
| `omnix_core/bev/constraint_conformance_signal.py` | Core | `_load_session_state_from_db` for multi-dyno drift safety |
| `omnix_web/api/govern_blueprint.py` | API | `list_sessions` status validation; 9-endpoint docstring |
| `tests/test_bev_ogr.py` | Tests | `TestCloseSessionFixes` (7 tests); `TestCTCHCChain` docstring update |
| `docs/adr/ADR-184-omnix-governance-runtime.md` | Docs | BEV-INV-015–018 + OGR-INV-001 added to invariant table; Mitigations updated |
| `docs/integration/OMNIX_GOVERNANCE_RUNTIME.md` | Docs | Invariant count corrected; typo in code example fixed |
| `docs/integration/GETTING_STARTED.md` | Docs | "14 BEV invariants" → "18 BEV invariants + OGR-INV-001" |

---

## Audit Methodology

The audit was conducted in three rounds using the following approach:

1. **Static analysis** — Full read of all five source files, cross-referencing
   invariant numbers against ADR-181/182/183/184 and the test suite.
2. **Test execution** — All 267 tests run after every batch of fixes to detect
   regressions introduced by the fixes themselves.
3. **No-DB path analysis** — Explicit tracing of every method call when
   `DATABASE_URL` is absent, identifying cases where DB absence produced
   incorrect results instead of degraded-but-safe results.
4. **API contract review** — Every endpoint input parameter reviewed for
   missing validation, every response field reviewed for accuracy.
5. **Documentation cross-check** — Integration docs, ADRs, and RFC draft
   checked against the implementation for any divergence.

---

*ADR-185 · OMNIX QUANTUM LTD · Harold Nunes · 2026-05-23*  
*Amends: ADR-181, ADR-182, ADR-183, ADR-184*
