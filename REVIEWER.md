# START HERE — Technical Reviewer Path

> **OMNIX QUANTUM Decision Governance Infrastructure**  
> ATF v3.3.0 · RFC-ATF-1/2/3 Published · 171 ADRs · 47 Invariants · 245+ Tests  
> Canonical repository: [Costenho19/omnibotgenesis](https://github.com/Costenho19/omnibotgenesis)

If you are evaluating OMNIX / ATF for the first time, follow this path in order.  
Each step has a defined scope, expected time, and what it establishes.

---

## Step 1 — Institutional Brief
**File:** [`docs/business/EXECUTIVE_FACT_SHEET.md`](docs/business/EXECUTIVE_FACT_SHEET.md)  
**Time:** ~5 minutes  
**What this proves:** System scope, active domains, production metrics, and governance stack at a glance.  
**Why this matters:** Establishes the factual baseline before any technical depth.

---

## Step 2 — Governance Flow Walkthrough
**Live:** [`/try`](https://omnixquantum.net/try) — Public Governance Sandbox (no auth required)  
**Live:** [`/demo`](https://omnixquantum.net/demo) — Investor Governance Demo  
**Time:** ~10 minutes  
**What this proves:** The pipeline runs live. Real decisions, real Dilithium-3 receipts, real audit trail.  
**Why this matters:** Distinguishes a working system from a prototype. Every decision produces a verifiable, cryptographically-signed receipt.

---

## Step 3 — Independent Verification
**Live:** [`/verify-independently`](https://omnixquantum.net/verify-independently) — Offline verification guide  
**Live:** [`/forensic-operations`](https://omnixquantum.net/forensic-operations) — Five forensic operation demos (A–E)  
**Live:** [`/atf-verify`](https://omnixquantum.net/atf-verify) — ATF trust chain verifier  
**Time:** ~10 minutes  
**What this proves:** Receipts are verifiable without OMNIX infrastructure. Dilithium-3 signatures hold independently.  
**Why this matters:** Auditability is the core claim. This is where it is tested.

---

## Step 4 — RFC Stack
**Files:**
- [`docs/standards/RFC-ATF-1.md`](docs/standards/RFC-ATF-1.md) — Agent Trust Fabric: Identity, Delegation, Trust Establishment
- [`docs/standards/RFC-ATF-2.md`](docs/standards/RFC-ATF-2.md) — Runtime Governance Continuity: Temporal Authority, Runtime Continuity
- [`docs/standards/RFC-ATF-3.md`](docs/standards/RFC-ATF-3.md) — Extended Audit Protocol: Forensic, Execution, Scope Governance

**Published DOIs:**

| RFC | Zenodo | Figshare |
|-----|--------|----------|
| RFC-ATF-1 | [10.5281/zenodo.20155016](https://doi.org/10.5281/zenodo.20155016) | [10.6084/m9.figshare.32308077](https://doi.org/10.6084/m9.figshare.32308077) |
| RFC-ATF-2 | [10.5281/zenodo.20241344](https://doi.org/10.5281/zenodo.20241344) | [10.6084/m9.figshare.32308095](https://doi.org/10.6084/m9.figshare.32308095) |
| RFC-ATF-3 | [10.5281/zenodo.20247342](https://doi.org/10.5281/zenodo.20247342) | [10.6084/m9.figshare.32308119](https://doi.org/10.6084/m9.figshare.32308119) |

**Time:** ~30 minutes per RFC (skim: ~10 minutes each)  
**What this proves:** Governance behavior is formally specified before implementation. The RFCs define invariants that the system must uphold — not the other way around.  
**Why this matters:** Published DOIs establish external timestamping and priority. The spec exists independently of this repository.

---

## Step 5 — Conformance Suite
**File:** [`docs/compliance/INVARIANT_TEST_MATRIX.md`](docs/compliance/INVARIANT_TEST_MATRIX.md)  
**Tests:** [`tests/`](tests/) — 245+ tests across 12 suites  
**Audit:** [`docs/audits/ATF_EAP_OEP_INSTITUTIONAL_AUDIT_2026-05.md`](docs/audits/ATF_EAP_OEP_INSTITUTIONAL_AUDIT_2026-05.md)

**Run locally:**
```bash
TESTING=true TELEGRAM_BOT_TOKEN=test-token \
  python -m pytest tests/ -v --tb=short
```

**Time:** ~20 minutes (read matrix) / ~3 minutes (run tests)  
**What this proves:** 47 invariants × implementation × test coverage mapped explicitly. 34/40 core invariants have direct test coverage. 6/40 are structural (enforced by architecture, not test).  
**Why this matters:** Invariant traceability is the difference between "we claim this" and "we can show this".

---

## Step 6 — Release Governance and Audit Trail
**Release notes:** [`docs/submissions/GITHUB_RELEASE_v1.1.0.md`](docs/submissions/GITHUB_RELEASE_v1.1.0.md)  
**Changelog:** [`CHANGELOG.md`](CHANGELOG.md)  
**Audit log:** [`docs/audits/`](docs/audits/) — 13 audit documents  
**Architecture decisions:** [`docs/adr/`](docs/adr/) — 171 ADRs  
**Ecosystem baseline:** [`docs/ECOSYSTEM_BASELINE_MAY2026.md`](docs/ECOSYSTEM_BASELINE_MAY2026.md)

**Time:** ~15 minutes  
**What this proves:** Every architectural decision is recorded, dated, and traceable. Release governance follows a defined process. The audit trail is complete and publicly inspectable.  
**Why this matters:** Institutional infrastructure requires documented decision history, not just working code.

---

## Quick Reference

| Claim | Evidence location |
|-------|-------------------|
| Post-quantum signatures (Dilithium-3 / ML-DSA-65, FIPS 204) | `omnix_core/security/` · ADR-078 · `/verify-independently` |
| 47 formal invariants across 9 families | `docs/compliance/INVARIANT_TEST_MATRIX.md` · RFC-ATF-1/2/3 |
| 11-checkpoint governance pipeline | `docs/current/WEB_INFRASTRUCTURE.md` · ADRs 028–053 |
| 10 active governance domains | `docs/current/DOMAIN_REGISTRY.md` · AVM snapshots |
| 670,000+ governance decisions (trading validation) | `docs/business/investor/INVESTOR_FAQ.md` · ADR-036 |
| External DOI publication | Zenodo / Figshare — 6 DOIs above |
| Audit independence | `docs/audits/ATF_EAP_OEP_INSTITUTIONAL_AUDIT_2026-05.md` |

---

## What OMNIX Is Not

- Not a trading signal provider
- Not a compliance checkbox product
- Not a prototype awaiting production hardening

OMNIX is a **decision governance infrastructure layer** — auditable, cryptographically-bound, formally-specified — designed to sit between AI/autonomous agents and consequential actions.

---

*Canonical baseline: [`docs/ECOSYSTEM_BASELINE_MAY2026.md`](docs/ECOSYSTEM_BASELINE_MAY2026.md)*  
*Questions: harold@omnixquantum.com*
