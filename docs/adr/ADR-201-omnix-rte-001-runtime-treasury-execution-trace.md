# ADR-201 — OMNIX-RTE-001: Runtime Treasury Execution Trace

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-28  
**Supersedes:** —  
**Extends:** ADR-200 (RCEP) · ADR-184 (OGR) · ADR-186/187 (PoGR) · ADR-188 (OSG) · ADR-194 (MIVP) · RFC-ATF-5 (CGE/GUGT/TGB)  
**Artefact ID:** OMNIX-RTE-001  

---

## Context

The Route-Complete Evidence Package (RCEP, ADR-200) demonstrated two routes — refusal and admission — for a $2M trading desk reallocation. It proved that execution is structurally impossible under invalid authority and structurally admitted under complete authority. Three TA-14 Controlled PASS reviews validated the framework.

The strategic gap identified after those reviews: OMNIX has demonstrated architecture, enforcement, invariants, receipts, continuity, evidence, and offline verification. It has not yet demonstrated a **complete operational story from start to finish** under consequential, institutionally legible conditions.

Specifically absent from RCEP:

- **No mandate integrity tracking** — no MIVP across the execution turns
- **No counterfactual decision space** — only the selected path, not the alternatives
- **No settlement gate** — no OSG enforcement linking governance to financial settlement
- **No temporal context** — no TGB snapshot embedding regulatory context at nanosecond precision
- **No post-execution continuity proof** — the story ends at the outcome receipt
- **Scenario legibility** — $2M trading reallocation is technically valid but institutionally small

ADR-201 addresses all of these gaps with a single, complete, impeccable artefact.

---

## Decision

### Artefact: OMNIX-RTE-001

**Full name:** OMNIX Runtime Treasury Execution Trace  
**ID format:** `OMNIX-RTE-001-{HEX16}`  
**Scenario:** Autonomous cross-border liquidity release — USD 50,000,000 — SWIFT MT202 / XRPL  
**Generator:** `scripts/generate_treasury_execution_trace.py`  
**Verifier:** `scripts/verify_treasury_execution_trace.py`  
**Output:** `evidence_packages/OMNIX-RTE-001_*.json`

### Dual-path structure

The OMNIX-RTE-001 proves two simultaneous propositions:

| Path | Proposition |
|---|---|
| **DANGEROUS PATH** | Under authority drift, mandate misalignment, and continuity degradation, the system cannot execute and produces a provable, forensically sealed HALT |
| **ADMISSIBLE PATH** | Under valid, recertified authority and mandate alignment, the system executes exactly what was committed, produces a PoGC, and releases settlement |

The dangerous path must be more impressive than the admissible path. Any system can show an approval. No system shows a HALT with a verifiable reason chain, append-only evidence, and an OSG hard reject that prevented settlement.

### Nine-step trace structure (all paths) — v1.4.0

Each path follows the same 9-step TA-14 chain (Step 0 added in v1.4.0 — ADR-204 IPFL):

```
1. SOURCE_STATE      — request captured with full treasury context
2. AUTHORITY         — DR issued (degraded or valid) + MIVP MBR activated
3. RUNTIME           — CES computed + MIVP MAS per-turn + CCS signal
4. COUNTERFACTUAL    — CGE: 5 CFRs + CAT sealed (what could have happened)
5. VERDICT           — HALT (dangerous) or ADMITTED (admissible)
6. GATE              — OSG: ValidationReceipt REJECTED or APPROVED
7. EXECUTION         — refusal receipt (dangerous) or BAR+CTCHC+settlement (admissible)
8. POST_EXECUTION    — CTCHC sealed + TGB snapshot + replay proof
```

### New artefacts introduced (beyond RCEP)

| Artefact | Source | Present in dangerous | Present in admissible |
|---|---|---|---|
| MandateBindingRecord (MBR) | MIVP ADR-194 | ✓ | ✓ |
| MandateAlignmentScore (MAS) | MIVP ADR-194 | ✓ (low — triggers warning) | ✓ (high — BOUND) |
| MBRSeal | MIVP ADR-194 | ✓ (UNCERTIFIED) | ✓ (MANDATE-BOUND) |
| CounterfactualForkRecord (CFR) | CGE RFC-ATF-5 | ✓ ×5 | ✓ ×5 |
| CounterfactualAttestationToken (CAT) | CGE RFC-ATF-5 | ✓ | ✓ |
| TemporalContextSnapshot (TCS) | TGB RFC-ATF-5 | ✓ | ✓ |
| OSG ValidationReceipt | OSG ADR-188 | ✓ (REJECTED) | ✓ (APPROVED) |
| Settlement Reference | — | — | ✓ (SWIFT MT202 + XRPL TxID) |
| Post-execution replay proof | — | ✓ (forensic) | ✓ (operational) |

### CLI Verifier commands

```bash
# Full verification (all checks)
python scripts/verify_treasury_execution_trace.py <package.json>

# Targeted verification
python scripts/verify_treasury_execution_trace.py <package.json> --verify-authority
python scripts/verify_treasury_execution_trace.py <package.json> --verify-continuity
python scripts/verify_treasury_execution_trace.py <package.json> --verify-counterfactual
python scripts/verify_treasury_execution_trace.py <package.json> --verify-halt
python scripts/verify_treasury_execution_trace.py <package.json> --verify-settlement
python scripts/verify_treasury_execution_trace.py <package.json> --verify-replay
```

### Scenario parameters

| Parameter | Value |
|---|---|
| Agent ID | `OMNIX-AGENT-TREASURY-001` |
| Human authority | `CFO-OPERATOR-HN-001` |
| Action | Cross-border liquidity release — EUR counterparty settlement |
| Amount | USD 50,000,000 |
| Settlement rail | SWIFT MT202 / XRPL RLUSD |
| Domain | `institutional_treasury` |
| Mandate ref | `TREASURY-MANDATE-2026-Q2` |
| Risk class | CRITICAL |
| Regulatory frameworks | EU AI Act Art. 9 · MiCA · DORA |

### Invariants demonstrated

| Invariant | Source |
|---|---|
| ATF-INV-001 | MAR: authority never expands through delegation |
| ATF-INV-002 | Every DR PQC-signed by delegator |
| ATF-INV-005 | Receipts immutable once issued |
| BEV-INV-001 | BAR issued before output delivered |
| BEV-INV-010–014 | CTCHC: genesis → links → seal |
| MIVP-INV-001 | MBR issued before Turn 1 |
| MIVP-INV-003 | MAS computed per turn |
| MIVP-INV-007 | MBR Seal at session close |
| MIVP-INV-008 | MANDATE-BOUND tag on PoGC (admissible path) |
| CGE-INV-001 | CFRs computed at evaluation time |
| CGE-INV-002 | CAT root hash covers all CFRs |
| CGE-INV-003 | fragility_score ∈ [0.0, 1.0] |
| CGE-INV-007 | CAT PQC-signed before OEP export |
| TGB-INV-001 | TCS embedded in every ATF record |
| PoGR-INV-001 | PoGC issued only from SEALED session |
| PoGR-INV-002 | PoGC append-only |
| PoGR-INV-003 | PoGC verifiable offline (zero auth) |

### RTE-INV invariants (new — this ADR)

| ID | Statement |
|---|---|
| RTE-INV-001 | OMNIX-RTE-001 package MUST contain both dangerous and admissible paths |
| RTE-INV-002 | Dangerous path MUST terminate in HALT before Step 6 (OSG gate) |
| RTE-INV-003 | OSG MUST reject dangerous path independently of HALT (fail-closed) |
| RTE-INV-004 | Admissible path MUST produce PoGC with MANDATE-BOUND certification |
| RTE-INV-005 | Both paths MUST contain CGE CAT with ≥3 CFRs |
| RTE-INV-006 | Both paths MUST contain TCS with regulatory_context at issuance nanosecond |
| RTE-INV-007 | Package MUST be verifiable offline with zero OMNIX runtime access |
| RTE-INV-008 | CLI verifier MUST exit 0 on valid package, non-zero on any FAIL |

---

## Consequences

The OMNIX-RTE-001 transitions OMNIX from:
- *"OMNIX can do this"* → *"This occurred, here is the proof, here is what was prevented, here is what was admitted"*

Institutional-grade evidence: auditors, regulators, general counsel, and CFOs can read and understand the dangerous path without technical training. The admissible path shows the system in normal operation. Together they constitute what governance infrastructure must demonstrate to be taken seriously.

The CLI verifier transforms the document from a paper into a falsifiable artefact.

---

## §7 — Hardening Layer (v1.1.0) — ADR-202

After generating v1.0.0, a 15-attack adversarial simulation was conducted. 4 bypasses
were found and fully remediated in v1.1.0. The hardening is documented in ADR-202.

| Finding | Severity | Remediation | New checks |
|---|---|---|---|
| A09 — Cross-path DR injection | CRITICAL | `session_id` embedded in DR hash; MBR binds `dr_id`; verifier checks DR-SESS + MBR-DRID | +4 |
| A08 — CFR content mutation | HIGH | Each CFR gets `cfr_content_hash`; CAT root covers content hashes | +2 |
| A07 — No TTL enforcement | HIGH | Verifier emits TTL WARNING if DR elapsed (non-blocking) | +2 |
| source_state hash unverified | MEDIUM | Verifier checks `source_state_hash` per path | +2 |

**Check count:** 101 (v1.0.0) → **111 (v1.1.0)**  
**New invariants:** RTE-INV-009 (DR session binding) · RTE-INV-010 (MBR dr_id) · RTE-INV-011 (CFR content hash) · RTE-INV-012 (source_state hash)

---

---

## §8 — Multi-turn Execution Trace (v1.2.0) — 2026-05-30

The original generator (v1.1.0) produced a single-turn admissible path: one BAR, one CTCHC link, one MAS record. The trace proved governance admission but not **execution granularity** — the sequence of real-world actions performed under that governance.

v1.2.0 upgrades the admissible path to a **3-turn execution trace** matching the actual settlement pipeline:

| Turn | Label | Artifacts |
|---|---|---|
| **Turn 0** | SWIFT MT103 counterparty validation + sanctions screening | BAR-0 · CCS-0 (CONFORMANT/0.97) · CTCHC link-0 · MAS-1 (ALIGNED/0.96) |
| **Turn 1** | FIX 4.4 order routing — EUROBANK institutional gateway | BAR-1 · CCS-1 (CONFORMANT/0.95) · CTCHC link-1 · MAS-2 (ALIGNED/0.93) |
| **Turn 2** | XRPL RLUSD atomic settlement + ledger finality | BAR-2 · CCS-2 (CONFORMANT/0.94) · CTCHC link-2 · MAS-3 (ALIGNED/0.91) |

**CCS (Constraint Conformance Signal):** Each turn now includes a real PQC-signed CCS (BEV-INV-005) measuring per-turn constraint adherence. Cumulative drift across 3 turns: 0.06 — well below the 0.35 HALT threshold (BEV-INV-008).

**MBR Seal:** Covers 4 MAS records [pre-check (turn_index=0) + exec-0 + exec-1 + exec-2]. All 4 ALIGNED, 0 violations, 0 warnings → `MANDATE-BOUND` certification.

**PoGC:** References `ctchc_turn_count=3` and `bar_id` of the final execution turn (XRPL RLUSD settlement). The CTCHC seal covers the complete 3-turn hash chain.

**Package size:** 194.7 KB (v1.1.0) → **244.5 KB (v1.2.0)** — additional 49.8 KB from per-turn artifacts.

**Verifier:** `[CHC-ADM-CHAIN] CTCHC link chain continuity (3 links, BEV-INV-011)` — the existing 111-check verifier handles N-link chains generically. **111/111 PASS** unchanged.

**xrpl_tx_id:** In v1.2.0, the XRPL TxID in `settlement_reference` is anchored to the BAR output of Turn 2 (the execution turn that produced it), not a separately generated UUID. This eliminates a subtle gap where the settlement reference and execution trace could be from different executions.

**New invariant validated:**
- `BEV-INV-005` — every BAR has a corresponding CCS (now explicitly demonstrated across 3 turns)

---

## §9 — Interrupted Execution Path (v1.3.0) — 2026-05-30

v1.3.0 añade **Path C — Interrupted Execution**: el caso en que la autoridad es válida (DR fresco, CES NOMINAL), el TAR admite la solicitud, y la ejecución comienza correctamente — pero es interrumpida a mitad de cadena cuando el MIVP detecta colapso de alineamiento de mandato.

Este es el escenario más sofisticado de los tres: demuestra que OMNIX **no depende de un gate único de admisión**, sino que mantiene monitoreo continuo turno a turno durante la ejecución.

### Evolución turno a turno

| Turn | Label | CCS | MAS | Resultado |
|---|---|---|---|---|
| **Turn 0** | SWIFT MT103 contraparty + sanctions screening | CONFORMANT / 0.96 (drift=0.04) | ALIGNED / 0.94 | ✓ PASS |
| **Turn 1** | FIX 4.4 routing — gateway institucional | CONFORMANT / 0.91 (drift=0.09) | **WARNING / 0.61 < 0.65** | ⚠ WARNING |
| **Turn 2** | XRPL RLUSD atomic settlement | **CRITICAL / 0.58 (drift=0.42 > 0.35)** | **HALT / 0.28 < 0.30** | 🛑 HALT |

### Invariantes de terminación correcta

En Turn 2, el stack de gobernanza ejecuta la secuencia de terminación:
1. **MIVP HALT** — `alignment_score=0.28 < halt_threshold=0.30` → proxy-guard violation registrada
2. **BAR** — `bar_status=HALT_TRIGGERED` emitido (el output es registrado forense, no entregado)
3. **CTCHC sellado** — `terminal_state=HALTED` (3 links forenses completos, cadena íntegra)
4. **MBR Seal** — `certification_tier=UNCERTIFIED` (1 violation, MIVP-INV-009 three-tier)
5. **OSG REJECTED** — fail-closed independiente; settlement BLOCKED (RTE-INV-015)
6. **PoGC NO emitido** — cadena HALTED no califica como CLOSED (PoGR-INV-001 + RTE-INV-014)

### Nuevas invariantes (RTE-INV-013/014/015)

| Invariante | Enunciado |
|---|---|
| **RTE-INV-013** | En el path interrumpido, la CTCHC se sella en estado HALTED y todos los turn links quedan preservados forense-mente en la cadena. |
| **RTE-INV-014** | El PoGC NO se emite en el path interrumpido — la cadena sellada como HALTED no califica como CLOSED (PoGR-INV-001). |
| **RTE-INV-015** | El OSG rechaza independientemente (fail-closed) en el path interrumpido; el settlement USD 50,000,000 queda BLOCKED. |

### Impacto en el verifier

`verify_interrupted()` — 36 checks nuevos:

| Grupo | Checks |
|---|---|
| Estructural | INT-STRUCT (1) |
| CTCHC integridad | CHC-INT-GENESIS · CHC-INT-CHAIN · CHC-INT-SEAL · CHC-INT-SIG (4) + CHC-INT-HALTED (1) |
| BAR por turno (T0/T1/T2) | HASH+SIG+STATUS × 3 (9) |
| MAS T1 | HASH+SIG+WARNING (3) |
| MAS T2 | HASH+SIG+HALT+SCORE<0.30 (4) |
| CCS T2 | CRITICAL+AGVP (2) |
| MBR Seal | HASH+SIG+UNCERTIFIED (3) |
| OSG | HASH+SIG+REJECTED+FAILCLOSED (4) |
| PoGC + Settlement | INT-POGC-ABSENT + INT-SETTLE-BLOCKED (2) |
| Replay proof | HASH+SIG+STATUS+OFFLINE (4) |

**Total:** `EXPECTED_TOTAL_CHECKS = 148 (v1.3.0) + 39 (IPFL Step 0: 36 verify_intake + 3 PKG-INTAKE structural) = 187 (v1.4.0)`

### Package size

v1.3.0 (≈370 KB) → **v1.4.0 (≈494 KB)** — IPFL añade ~124 KB (3 GCFRs × 5 predicados + IDS seal por path).

---

## §10 — Intake and Predicate Formation Layer (v1.4.0) — 2026-05-30

v1.4.0 añade **Step 0 — GCFR (Governance Contract Formation Record)** como primer paso del trace, respondiendo a la observación de Dr. Masayuki Otani de que el artefacto público mostraba trace+verification pero no la capa de intake+predicate formation.

El **GCFR** sella cinco predicados pre-ejecución con ML-DSA-65:

| Predicado | ID | IPFL-INV |
|---|---|---|
| Intake Authority Declaration | IAD | INV-001 |
| Scope Authorization Record | SAR | INV-002 |
| Mandate Formation Record | MFR | INV-003/004 |
| Counterparty Predicate Set | CPS | INV-005 |
| Freshness Predicate Set | FPS | INV-006 |

**IDS Seal:** `SHA3-256(iad_hash ‖ "|" ‖ sar_hash ‖ "|" ‖ mfr_hash ‖ "|" ‖ cps_hash ‖ "|" ‖ fps_hash)` — PQC-signed. Alteración de cualquier predicado rompe el seal, detectable offline (IPFL-INV-007/008).

**Nuevos checks:** `verify_intake()` — 12 × 3 paths = **36 checks** + 3 PKG-INTAKE estructurales = **39 checks totales** (STRUCT + GCFR-COMP + GCFR-HASH + GCFR-SIG + 5 predicate hashes + XREF-MAND + XREF-PROXY + XREF-RAIL × 3 paths, más PKG-INTAKE-DNG/ADM/INT en verify_package_structure()).

**Nuevo comando IAEP:** `--verify-intake` (verificación) · `--intake-report` (IAEP-RPT-005 — Intake Formation Report).

Spec completa: **ADR-204** — `docs/adr/ADR-204-rte-001-intake-predicate-formation-layer.md`

---

## Related ADRs

- ADR-200 — Route-Complete Evidence Package (RCEP) — predecessor
- ADR-202 — OMNIX-RTE-001 Hardening Layer — adversarial remediation
- ADR-203 — Institutional Artifact Extraction Protocol (IAEP) — 5 premium reports
- ADR-204 — Intake and Predicate Formation Layer (IPFL) — Governance Contract Formation
- ADR-182 — Constraint Conformance Signal (CCS) — per-turn conformance measurement
- ADR-184 — OMNIX Governance Runtime (OGR) — session lifecycle
- ADR-186/187 — Proof of Governance Registry (PoGR/PoGC)
- ADR-188 — Operational Settlement Gate (OSG)
- ADR-194 — Mandate Integrity Verification Protocol (MIVP)
- RFC-ATF-5 — CGE (§5) · GUGT (§6) · TGB (§7)
- RFC-ATF-6 — BEV: BAR (ADR-181) · CCS (ADR-182) · CTCHC (ADR-183)
