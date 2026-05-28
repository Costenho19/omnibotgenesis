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

### Eight-step trace structure (both paths)

Each path follows the same 8-step TA-14 chain:

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

## Related ADRs

- ADR-200 — Route-Complete Evidence Package (RCEP) — predecessor
- ADR-184 — OMNIX Governance Runtime (OGR) — session lifecycle
- ADR-186/187 — Proof of Governance Registry (PoGR/PoGC)
- ADR-188 — Operational Settlement Gate (OSG)
- ADR-194 — Mandate Integrity Verification Protocol (MIVP)
- RFC-ATF-5 — CGE (§5) · GUGT (§6) · TGB (§7)
