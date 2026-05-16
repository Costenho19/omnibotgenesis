# ADR-168: Dual-Path Module Synchronization Policy

**Status:** ACCEPTED  
**Date:** 2026-05-16  
**Authors:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** —  
**Related:** ADR-028 (Decision Receipt), ADR-131 (Execution Integrity Layer), ADR-156–159 (ATF Stack)

---

## Context

The OMNIX platform maintains two distinct module loading paths for core governance logic:

**Path A — Canonical source:**  
`omnix_core/` — The authoritative implementation, subject to full ADR governance, test coverage, and version control.

**Path B — Bundled copy:**  
`omnix_web/api/omnix_engine/` — A set of standalone copies of select `omnix_core` modules, introduced to support Railway deployment scenarios where `omnix_core` may not be importable as a package (e.g., PYTHONPATH issues in certain dyno configurations).

### Affected modules (as of ADR-168)

| Bundled file | Canonical source |
|---|---|
| `omnix_web/api/omnix_engine/decision_receipt.py` | `omnix_core/evidence/decision_receipt.py` |
| `omnix_web/api/omnix_engine/execution_receipt.py` | `omnix_core/evidence/execution_receipt.py` |
| `omnix_web/api/omnix_engine/external_evaluator.py` | `omnix_core/governance/external_evaluator.py` |
| `omnix_web/api/omnix_engine/federated_trust.py` | `omnix_core/governance/federated_trust.py` |
| `omnix_web/api/omnix_engine/jurisdiction_gate.py` | `omnix_core/governance/jurisdiction_gate.py` |
| `omnix_web/api/omnix_engine/receipt_to_vc.py` | `omnix_core/evidence/receipt_to_vc.py` |
| `omnix_web/api/omnix_engine/regulatory_mapping.py` | `omnix_core/governance/regulatory_mapping.py` |
| `omnix_web/api/omnix_engine/vc_revocation.py` | `omnix_core/evidence/vc_revocation.py` |
| `omnix_web/api/omnix_engine/due_diligence.py` | `omnix_core/governance/due_diligence.py` |

### Risk

**Version drift** is the primary risk. If `omnix_core` modules are updated (new receipt fields, invariant changes, schema migrations) and the bundled copies in `omnix_engine/` are not updated simultaneously, the platform may produce divergent results between:

- The governance pipeline executed via canonical imports
- The same pipeline executed via bundled copies on Railway

This divergence is **silent** — no exception is raised, no hash mismatch triggers, no monitoring alert fires. The resulting governance receipts may differ in structure or semantics while passing all local tests.

This is classified as a **high-severity architectural risk** because:
1. Governance receipts are PQC-signed and forensically immutable — a divergent receipt cannot be corrected retroactively
2. The divergence is undetectable without explicit cross-path parity testing
3. Receipt format changes in `omnix_core` (e.g., new ATF fields post-ADR-159) have already occurred without corresponding updates to bundled copies

---

## Decision

### Policy: Controlled Dual-Path with Mandatory Parity

The dual-path architecture is **accepted as a deployment necessity** for the current Railway configuration, subject to the following mandatory controls:

#### 1. Synchronization obligation

Every change to a canonical module listed in the table above MUST be applied to its corresponding bundled copy in the same commit. The commit message MUST reference both paths:

```
fix(receipt): add atf_context.tar_id field to content_hash computation

Modified: omnix_core/evidence/decision_receipt.py
Synced:   omnix_web/api/omnix_engine/decision_receipt.py
ADR-168 sync required — dual-path module
```

#### 2. Parity test requirement

The test suite MUST include at least one test that imports both the canonical and bundled versions and asserts functional equivalence for the receipt format fields. This test is the canary for drift detection.

Canonical test: `tests/test_adr168_module_parity.py`

#### 3. Synchronization audit in CI

The Code Verification workflow MUST include a step that checks file modification timestamps (or content hash) across both paths. Any discrepancy fails the build.

#### 4. Deprecation path

The bundled copies in `omnix_web/api/omnix_engine/` are designated **temporary infrastructure**. The target state is a single import path via `omnix_core` as a properly installed package on Railway. This is the preferred resolution and will be tracked as a deployment task. When achieved, `omnix_engine/` is to be deleted and this ADR updated to SUPERSEDED.

#### 5. `omnix_core/build/` artifact

The directory `omnix_core/build/` is a pip build artifact that must not be tracked in version control. It was identified during the ADR-168 architect review (May 2026). It is excluded from git tracking via `.gitignore` (entry added in this ADR's corresponding commit). Any future `python -m build` or `pip install -e .` command will regenerate it locally without affecting the repo.

---

## Invariant

**SYNC-INV-001:** At any point in the main branch, the functional behavior of each module in `omnix_web/api/omnix_engine/` MUST be identical to its canonical counterpart in `omnix_core/`. Drift between the two paths is a governance integrity violation.

---

## Consequences

**Positive:**
- Risk is formally acknowledged and tracked
- Developers have a clear obligation when modifying canonical modules
- Parity test provides automated drift detection
- Deprecation path is defined

**Negative:**
- Short-term: every change to covered modules requires double edit
- The parity test adds marginal CI time

**Mitigation:**  
The synchronization overhead is acceptable given the forensic immutability requirements of the governance pipeline. A single divergent receipt in production is a worse outcome than double-editing 9 files.

---

## References

- `omnix_web/api/omnix_engine/` — bundled copies  
- `omnix_core/evidence/` + `omnix_core/governance/` — canonical sources  
- ADR-028 — Decision Receipt format  
- ADR-131 — Execution Integrity Layer  
- ADR-167 — Forensic Hardening (verifier determinism, FVP-INV-007)  
- Architect Review — May 2026 (OMNIX Institutional Sprint)

---

*OMNIX QUANTUM LTD · Harold Nunes · 2026-05-16*
