# OMNIX / ATF Ecosystem Baseline — May 2026

**Status:** CANONICAL FREEZE  
**Date:** 2026-05-19  
**Supersedes:** All prior public counts, version references, and historical snapshots

> This document is the single source of truth for the state of the OMNIX QUANTUM ecosystem as of May 2026.  
> Any document that conflicts with the values below should be treated as historical unless explicitly annotated otherwise.

---

## Canonical Repository

| Field | Value |
|-------|-------|
| Repository | `Costenho19/omnibotgenesis` |
| Current release | `v1.1.0` |
| Release date | May 2026 |
| Release notes | `docs/submissions/GITHUB_RELEASE_v1.1.0.md` |
| Changelog | `CHANGELOG.md` |

---

## RFC Stack

| RFC | Title | Status | Zenodo DOI | Figshare DOI |
|-----|-------|--------|------------|--------------|
| RFC-ATF-1 | Agent Trust Fabric: Core Protocol | **Published** | [10.5281/zenodo.20155016](https://doi.org/10.5281/zenodo.20155016) | [10.6084/m9.figshare.32308077](https://doi.org/10.6084/m9.figshare.32308077) |
| RFC-ATF-2 | Runtime Governance Continuity | **Published** | [10.5281/zenodo.20241344](https://doi.org/10.5281/zenodo.20241344) | [10.6084/m9.figshare.32308095](https://doi.org/10.6084/m9.figshare.32308095) |
| RFC-ATF-3 | Extended Audit Protocol | **Published** | [10.5281/zenodo.20247342](https://doi.org/10.5281/zenodo.20247342) | [10.6084/m9.figshare.32308119](https://doi.org/10.6084/m9.figshare.32308119) |

All three RFCs published under OMNIX QUANTUM Open Standard format. Not IETF. Not arXiv preprints. Timestamped, citable, DOI-registered.

---

## Active Invariants

| Metric | Value |
|--------|-------|
| Total invariants | **47** |
| Invariant families | **9** |
| Direct test coverage | 34/40 core invariants (85%) |
| Structural enforcement | 6/40 (enforced by architecture) |
| Untested | 0 |

**Family breakdown:**

| Family | Invariants | Source |
|--------|-----------|--------|
| ATF Core (AIR + DR + DTR) | 6 | RFC-ATF-1 §5 |
| TAR (Temporal Authority) | 1 | RFC-ATF-1 §6 |
| RGC (Runtime Governance Continuity) | 8 | RFC-ATF-2 |
| GPIL (Governance Pipeline Integrity) | 3 | RFC-ATF-3 / ADR-161 |
| ELR (Execution Ledger) | 4 | RFC-ATF-3 / ADR-131 |
| EAP (Extended Audit Protocol) | 7 | RFC-ATF-3 / ADR-162 |
| OEP (Operational Evidence Protocol) | 6 | RFC-ATF-3 / ADR-164 |
| FEA (Forensic Evidence Architecture) | 5 | RFC-ATF-3 / ADR-166 |
| GECR (Governance Evidence Chain of Responsibility) | 6 | ADR-170 |
| FVP (Forensic Verification Protocol) | 1 | RFC-ATF-3 / ADR-163 |

Note: CDTP (4 proposed) and SGIP (4 proposed) are roadmap items — not counted in the 47 active invariants.

---

## Architecture Decision Records

| Metric | Value |
|--------|-------|
| Total ADRs | **171** |
| ADR range | ADR-001 through ADR-171 |
| Location | `docs/adr/` |
| Status | Immutable historical record |

ADRs are append-only. Each records the state, context, and rationale at decision time. Do not expect ADR counts in older documents (ADR-036 era) to match the current total — they are correct for their filing date.

---

## Test Status

| Metric | Value |
|--------|-------|
| Total tests | **245+** |
| Test suites | 12 |
| Last full run | 2026-05-19 |
| Result | **245 passed / 5 skipped / 0 failed** |
| Skipped | Infrastructure-dependent (Redis anti-replay, live DB) — expected in isolated test mode |

**Test suites:**
- `test_code_verification.py` — import integrity, syntax
- `test_version_consistency.py` — no hardcoded stale versions
- `test_critical_audit.py` — governance logic invariants
- `test_governance_integrity.py` — pipeline integrity
- `test_response_validator.py` — decision payload schema
- `test_systemic_router.py` — domain routing
- `test_eap_extended_audit.py` — EAP / OEP / GPIL invariants (58 pass / 4 skip)
- Additional suites in `tests/`

---

## Governance Pipeline

| Metric | Value |
|--------|-------|
| Checkpoints | **11** (CP-0 through CP-10) |
| Additional control layers | CAG (Context Admission Gate) + TIE (Temporal Integrity Engine) |
| Total control layers | **13** |
| Domains | **10** |
| PQC algorithm | Dilithium-3 (ML-DSA-65, FIPS 204) |
| Anti-replay | Redis-backed, configurable strict / best_effort |

**Active governance domains:**
`trading` · `autonomous_agent` · `energy_governance` · `insurance` · `crisis` · `islamic_credit` · `stablecoin` · `medical_ai` · `defense_governance` · `real_estate` · `robotics`

Note: The trading vertical uses an 8-checkpoint entry pipeline (CP-0 through CP-7) + 3-gate EGL exit, validated across 670,000+ decisions (Feb–Mar 2026). The general governance pipeline has 11 checkpoints + CAG + TIE.

---

## ATF Version

| Field | Value |
|-------|-------|
| ATF version | **v3.3.0** |
| Stack layers | L1 Identity (AIR) → L2 Delegation (DR) → L3 Temporal (TAR) → L4 Runtime Continuity (RCR) |
| Specification | RFC-ATF-1 + RFC-ATF-2 + RFC-ATF-3 |

---

## Production Infrastructure

| Component | Platform | Status |
|-----------|----------|--------|
| Web API + React SPA | Railway (gunicorn) | Live |
| Telegram Bot | Railway (24/7) | Live |
| PostgreSQL | Railway managed | Live |
| Redis (anti-replay) | Railway managed | Live |
| Domain | omnixquantum.net | Active |

---

## Conformance Status

| Layer | Status |
|-------|--------|
| Invariant traceability matrix | Complete — `docs/compliance/INVARIANT_TEST_MATRIX.md` |
| Institutional audit | Complete — `docs/audits/ATF_EAP_OEP_INSTITUTIONAL_AUDIT_2026-05.md` |
| Documentation sweep | Complete — `docs/audits/GLOBAL_SWEEP_REPORT_2026-05-19.md` |
| Release governance | Complete — `CHANGELOG.md` + `docs/submissions/GITHUB_RELEASE_v1.1.0.md` |

---

## Known Historical Exceptions

Some documents in this repository contain values that differ from the canonical figures above. These are **not errors** — they are accurate records of the system's state at their respective filing dates.

The full inventory of historical exceptions with individual justifications is documented in:  
[`docs/audits/GLOBAL_SWEEP_REPORT_2026-05-19.md`](audits/GLOBAL_SWEEP_REPORT_2026-05-19.md) — Section "Residual Known Exceptions" (R-01 through R-22)

**Summary of common patterns:**
- `8-checkpoint` in trading/investor docs → accurate for the trading vertical validated in Feb–Mar 2026
- `36 ADRs → 57 ADRs` in EXECUTIVE_FACT_SHEET evolution table → historical growth milestones, not current count
- `DOI: pending` in Zenodo submission guides → step-by-step process instructions, not open claims
- ADRs ADR-036 through ADR-053 with 8-checkpoint references → correct at decision date

---

## Freeze Scope

This baseline covers:

- All documentation in `docs/`
- All source files in `omnix_core/`, `omnix_services/`, `omnix_dashboard/`
- All React pages in `omnix_web/src/`
- All SDK files in `sdk/`
- All published RFC files in `docs/standards/`
- All test suites in `tests/`

**Out of scope:** `.local/tasks/` (internal sprint planning), `attached_assets/` (historical submission records), provisional patent applications in `docs/ip/` (legally bound to filing date).

---

**This baseline supersedes prior public counts and historical snapshots.**

*Compiled: 2026-05-19 · OMNIX QUANTUM LTD (UK) · omnixquantum.com*
