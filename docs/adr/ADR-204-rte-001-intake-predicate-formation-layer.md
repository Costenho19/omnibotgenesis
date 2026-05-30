# ADR-204 — RTE-001 Intake and Predicate Formation Layer (IPFL)

**Status:** Accepted  
**Date:** 2026-05-30  
**Authors:** Harold Nunes, OMNIX QUANTUM LTD  
**Supersedes:** —  
**Related:** ADR-201 (RTE-001), ADR-202 (Hardening), ADR-203 (IAEP), RFC-ATF-1 through RFC-ATF-6  
**Package version:** RTE-001 v1.4.0  
**Invariants:** IPFL-INV-001 through IPFL-INV-008

---

## 1. Context

Dr. Masayuki Otani observed during external review of the OMNIX-RTE-001 public artefact that the
package demonstrates trace execution and cryptographic verification but does not make explicit the
**intake and predicate formation layer** — the layer responsible for forming the Governance Contract
*before* any execution trace begins.

The OMNIX runtime already performs this function internally: `GovernanceRuntime.start_session`
initialises a `DelegationReceipt` (ADR-156), `ScopeAuthorizationRecord` (ADR-147), and
`MandateBindingRecord` (ADR-194) before admitting Turn 0. However, the RTE-001 artefact did not
make this pre-execution layer explicit, observable, or independently verifiable offline.

This ADR formalises the **Intake and Predicate Formation Layer (IPFL)** as a first-class component
of the RTE-001 package, introducing the **Governance Contract Formation Record (GCFR)** as Step 0
of the 9-step execution trace.

---

## 2. Decision

### 2.1 IPFL Architecture

The IPFL consists of five intake predicates, each a standalone PQC-signed artefact, assembled into
a single sealed GCFR before `1_source_state` capture. The GCFR constitutes the **Governance
Contract** — the complete pre-execution declaration of who can act, what they may do, under what
mandate, with whom, and within what time bounds.

```
GOVERNANCE CONTRACT (GCFR)
  ├── [IAD] Intake Authority Declaration        — IPFL §2.1
  ├── [SAR] Scope Authorization Record          — IPFL §2.2
  ├── [MFR] Mandate Formation Record            — IPFL §2.3
  ├── [CPS] Counterparty Predicate Set          — IPFL §2.4
  └── [FPS] Freshness Predicate Set             — IPFL §2.5
       └── IDS Seal (intake_seal)               — IPFL §2.6
           seal_hash = SHA3-256(iad||sar||mfr||cps||fps)
           pqc_signature: ML-DSA-65 over {ids_id, seal_hash, formed_at}
```

### 2.2 Intake Authority Declaration (IAD) — IPFL §2.1

Declares the agent, human authority root, authority type (DEGRADED / RECERTIFIED / VALID), 
authority budget as a percentage of the delegator's ceiling, depth limit, and operational
constraints. The IAD is PQC-signed and hash-committed before any execution artefact is produced.

**Relationship to existing artefacts:** The IAD surfaces the authority state that the DR (ADR-156)
encodes at a later step, but captures it at the moment of intake — before the DR is formally issued.
The XREF-RAIL verifier check ensures consistency between both.

### 2.3 Scope Authorization Record (SAR) — IPFL §2.2

Delimits what the agent is permitted to do (`permitted_actions`) and explicitly excluded from doing
(`excluded_actions`), along with the approved settlement rails and maximum transaction amount.

**Relationship to existing artefacts:** The SAR complements the `ScopeAuthorizationRecord` issued
by `ScopeAuthorizationEngine` (ADR-147). IPFL-INV-002 enforces that the SAR's `approved_rails`
must match the DR's `task_scope.approved_rails`, making the intake predicate and the formal
delegation scope coherent.

### 2.4 Mandate Formation Record (MFR) — IPFL §2.3

Canonical pre-execution declaration of the mandate: objective (hashed), prohibited proxy metrics
as plain-language strings, and the MIVP scoring thresholds (halt/warning). The MFR is formed and
sealed *before* the MBR is issued at step `2_authority`.

**Relationship to existing artefacts:** The MFR and MBR (ADR-194) are companion artefacts.
IPFL-INV-003 requires `mfr.mandate_objective_hash == mbr.mandate_objective_hash`. IPFL-INV-004
requires that every proxy guard description in the MBR is declared as a prohibition in the MFR —
no proxy guard may be introduced after the Governance Contract is sealed.

### 2.5 Counterparty Predicate Set (CPS) — IPFL §2.4

Pre-verified counterparty declaration: whitelist, BIC registry, sanctions checks (OFAC, EU
Consolidated List, UN Sanctions), FX rate band, maximum single transaction amount, and dual
approval authorities. All sanctions checks must record CLEAR before the GCFR is sealed.

### 2.6 Freshness Predicate Set (FPS) — IPFL §2.5

Declares the validity windows and temporal freshness bounds active at contract formation: DR TTL
budget (`max_ttl_seconds`), TAR validity window, regulatory epoch assignment
(`EU-AI-ACT-PRE-ENFORCEMENT-2026`), mandate reference expiry date, and staleness threshold.

### 2.7 Governance Contract Formation Record (GCFR) — IPFL §2.6

Assembles the five predicates into a sealed record. The canonical seal formula is:

```
seal_hash = SHA3-256(iad_content_hash ‖ "|" ‖ sar_content_hash ‖ "|" ‖
                     mfr_content_hash ‖ "|" ‖ cps_predicate_hash ‖ "|" ‖
                     fps_freshness_hash)
```

The GCFR's `intake_seal` carries an **Intake Declaration Seal (IDS)** — a PQC signature over
`{ids_id, seal_hash, formed_at}` with ML-DSA-65 (FIPS 204). Alteration of any predicate after
sealing produces a different seal_hash, detectable offline with zero OMNIX runtime.

---

## 3. Invariants

### IPFL-INV-001 — IAD Pre-Execution Sealing
The Intake Authority Declaration must be formed and PQC-sealed before `1_source_state` capture
(Step 0 of the 9-step RTE-001 trace). An execution trace without a sealed IAD is not admissible.

**Verification:** `INT-{P}-STRUCT` + `INT-{P}-IAD-HASH` checks in `verify_intake()`.

### IPFL-INV-002 — SAR/DR Rail Coherence
`SAR.approved_rails` (sorted) must equal `DR.task_scope.approved_rails` (sorted). The intake
scope predicate and the formal delegation receipt must authorise the same settlement rails.

**Verification:** `INT-{P}-XREF-RAIL` check in `verify_intake()`.

### IPFL-INV-003 — Mandate Objective Consistency
`MFR.mandate_objective_hash` must equal `MBR.mandate_objective_hash`. The mandate objective is
frozen at Governance Contract formation and may not change between IPFL intake and MBR issuance.

**Verification:** `INT-{P}-XREF-MAND` check in `verify_intake()`.

### IPFL-INV-004 — Proxy Guard Pre-Declaration
Every proxy guard declared in `MBR.proxy_guards` must have its description listed in
`MFR.mandate_prohibitions`. No proxy guard may be introduced at runtime execution that was not
declared in the Governance Contract. Formally: `MBR.proxy_guards.descriptions ⊆ MFR.mandate_prohibitions`.

**Verification:** `INT-{P}-XREF-PROXY` check in `verify_intake()`.

### IPFL-INV-005 — Sanctions Clear Before Execution
`CPS.sanctions_all_clear` must be `True` at GCFR formation. All three sanctions checks (OFAC SDN,
EU Consolidated List, UN Sanctions) must record CLEAR. A Governance Contract with a non-CLEAR
sanctions record is not valid.

**Verification:** `INT-{P}-CPS-HASH` recomputation confirms the CPS payload including
`sanctions_all_clear=True`.

### IPFL-INV-006 — Positive TTL Budget
`FPS.max_ttl_seconds` must be strictly greater than zero. The DR TTL budget is declared at
contract formation and applied consistently to the DR issued at step `2_authority`.

**Verification:** `INT-{P}-FPS-HASH` recomputation confirms `max_ttl_seconds > 0` in FPS payload.

### IPFL-INV-007 — GCFR Seal Completeness
The GCFR `intake_seal.seal_hash` must cover all five component hashes in canonical order
(IAD ‖ SAR ‖ MFR ‖ CPS ‖ FPS). Altering any predicate after sealing produces a different
`seal_hash`, making the manipulation detectable offline without the OMNIX runtime.

**Verification:** `INT-{P}-GCFR-HASH` (seal recomputation) + `INT-{P}-GCFR-SIG` (PQC signature).

### IPFL-INV-008 — Step Ordering: GCFR Before Source State
The GCFR is unconditionally Step 0 of the RTE-001 9-step trace. In the package JSON, the key
`"0_intake"` must appear in `steps` before `"1_source_state"` in all three paths (dangerous,
admissible, interrupted).

**Verification:** `PKG-INTAKE-{DNG/ADM/INT}` structural checks in `verify_package_structure()`.

---

## 4. Canonicalization Profile

All GCFR component hashes use JSON canonicalization with `sort_keys=True` (same as the RTE-001
default profile documented in ADR-200 §4), excluding the hash field itself and PQC signature
fields before hashing.

| Artefact | Hash algorithm | Serialization | Excluded fields |
|---|---|---|---|
| IAD | SHA3-256 | `sort_keys=True` | `iad_content_hash`, `pqc_signature`, `pqc_algorithm` |
| SAR | SHA3-256 | `sort_keys=True` | `sar_content_hash`, `pqc_signature`, `pqc_algorithm` |
| MFR | SHA3-256 | `sort_keys=True` | `mfr_content_hash`, `pqc_signature`, `pqc_algorithm` |
| CPS | SHA3-256 | `sort_keys=True` | `cps_predicate_hash`, `pqc_signature`, `pqc_algorithm` |
| FPS | SHA3-256 | `sort_keys=True` | `fps_freshness_hash`, `pqc_signature`, `pqc_algorithm` |
| GCFR seal | SHA3-256 | `"|".join(component_hashes)` | — |
| IDS signature | ML-DSA-65 compact | `{ids_id, seal_hash, formed_at}` | — |

---

## 5. Three-Path GCFR Parameterisation

| Parameter | Path DANGEROUS | Path ADMISSIBLE | Path INTERRUPTED |
|---|---|---|---|
| IAD `authority_type` | `DELEGATED_DEGRADED` | `DELEGATED_RECERTIFIED` | `DELEGATED_VALID` |
| IAD `authority_budget_pct` | 42.0% | 88.0% | 88.0% |
| FPS `max_ttl_seconds` | 79,200 (22h) | 14,400 (4h) | 14,400 (4h) |
| FPS `tar_validity_window_hours` | 22 | 4 | 4 |
| Narrative | Authority already degraded at contract formation — drift cause is visible pre-execution | Recertified authority — full compliance expected | Valid authority — mid-chain halt is not caused by authority failure |

---

## 6. Verifier Extension — verify_intake()

`verify_intake()` adds **36 new checks** to the RTE-001 offline verifier (`12 checks × 3 paths = 36`),
plus **3 PKG-INTAKE structural checks** in `verify_package_structure()`.
`EXPECTED_TOTAL_CHECKS` advances from **148 → 187** (148 + 36 + 3).

```
Checks per path (×3 paths = 36 total):
  INT-{P}-STRUCT     GCFR required keys present in 0_intake step
  INT-{P}-GCFR-COMP  component_hashes has exactly 5 entries
  INT-{P}-GCFR-HASH  seal_hash recomputed from 5 component hashes
  INT-{P}-GCFR-SIG   IDS PQC signature valid (ML-DSA-65)
  INT-{P}-IAD-HASH   IAD iad_content_hash recomputed
  INT-{P}-SAR-HASH   SAR sar_content_hash recomputed
  INT-{P}-MFR-HASH   MFR mfr_content_hash recomputed
  INT-{P}-CPS-HASH   CPS cps_predicate_hash recomputed
  INT-{P}-FPS-HASH   FPS fps_freshness_hash recomputed
  INT-{P}-XREF-MAND  MFR.mandate_objective_hash == MBR.mandate_objective_hash
  INT-{P}-XREF-PROXY MBR.proxy_guards.descriptions ⊆ MFR.mandate_prohibitions
  INT-{P}-XREF-RAIL  SAR.approved_rails == DR.task_scope.approved_rails
```

CLI command: `python scripts/verify_treasury_execution_trace.py <pkg.json> --verify-intake`

---

## 7. IAEP Extension — IAEP-RPT-005

`--intake-report` adds the **Intake Formation Report (IFR)** as IAEP-RPT-005 (ADR-203 §2.5
extension). The IFR presents the GCFR for all three paths with per-predicate human-readable
summary — IAD authority level, SAR scope and rails, MFR mandate objective hash and prohibitions
count, CPS sanctions verdict, FPS freshness window and regulatory epoch.

This report is the direct, machine-extractable answer to Dr. Otani's observation.

CLI command: `python scripts/verify_treasury_execution_trace.py <pkg.json> --intake-report`

---

## 8. Package Version — RTE-001 v1.4.0

| Field | v1.3.0 | v1.4.0 |
|---|---|---|
| `package_version` | `"1.3.0"` | `"1.4.0"` |
| Steps per path | 8 | 9 (step 0 added) |
| `rte_chain_map` entries | 8 | 9 (`"0_INTAKE"` first) |
| `EXPECTED_TOTAL_CHECKS` | 148 | 187 (36 verify_intake + 3 PKG-INTAKE structural) |
| IPFL invariants | — | IPFL-INV-001–008 |
| `--verify-intake` | — | ✓ |
| `--intake-report` | — | ✓ (IAEP-RPT-005) |

**COMPAT-INV-001 (ADR-203 §3) preserved:** v1.4.0 adds 39 new checks (36 verify_intake + 3 PKG-INTAKE structural) on the new `0_intake` step.
No existing check from v1.0.0–v1.3.0 is modified or removed.

---

## 9. Consequences

**Positive:**
- The RTE-001 public artefact now explicitly demonstrates the full governance lifecycle:
  Contract Formation → Source State → Authority → Runtime → Verdict → Execution → Post-Execution.
- Dr. Otani's gap observation is addressed with machine-verifiable evidence.
- All three paths demonstrate the same Governance Contract structure under different authority
  conditions, making the IPFL universally applicable regardless of execution outcome.
- The GCFR is verifiable offline using only the embedded public key — zero OMNIX runtime required.
- IPFL-INV-004 (proxy guard pre-declaration) closes a theoretical attack vector where a runtime
  could introduce proxy guards post-contract to manipulate MAS scoring.

**Negative / Trade-offs:**
- Package size increases (GCFR adds ~20 KB of structured JSON per path).
- `EXPECTED_TOTAL_CHECKS` increases by 39 (36 + 3 structural); any CI pipeline pinned to 148 must update to 187.
- The `PKG-CHAIN` verifier check now requires 9 steps (was 8); v1.3.0 packages fail this check
  when verified with the v1.4.0 verifier (expected — use `--check-version` to confirm compat level).

---

## 10. References

| Document | Relevance |
|---|---|
| ADR-201 | RTE-001 core specification |
| ADR-202 | Production Hardening Layer |
| ADR-203 | Institutional Artifact Extraction Protocol (IAEP) |
| ADR-156 | Delegation Receipt (DR) — authority artefact |
| ADR-147 | Scope Authorization Engine (SAE) — scope artefact |
| ADR-194 | MIVP — Mandate Binding Record (MBR) |
| ADR-157 | Temporal Admissibility Record (TAR) |
| RFC-ATF-1 | ATF-INV-001: Monotonic Authority Reduction |
| RFC-ATF-6 | BEV-INV-001–018: Behavioral Execution Verification |

---

*ADR-204 · OMNIX QUANTUM LTD · 2026-05-30*
