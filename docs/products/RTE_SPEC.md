# OMNIX-RTE-001 — Runtime Treasury Execution Trace
## Product Specification

**Version:** 1.0.0  
**ADR:** ADR-201  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Date:** 2026-05-28  
**Status:** Available  

---

## What it is

The OMNIX Runtime Treasury Execution Trace (OMNIX-RTE-001) is the first complete, protocol-grade, offline-verifiable dual-path governance execution trace for an autonomous financial transaction.

It demonstrates — simultaneously, with cryptographic proof — two propositions:

1. **Under invalid or degraded authority:** a USD 50,000,000 cross-border treasury release cannot execute. The system halts. Evidence is sealed. Settlement is independently blocked at the OSG gate. No funds move.

2. **Under valid, recertified authority:** the same transaction executes completely. A Proof of Governance Certificate with MANDATE-BOUND certification is issued. The settlement gate opens. SWIFT MT202 and XRPL transaction references are embedded and verifiable.

Both propositions are proven in a single self-contained JSON package, verifiable offline with a single CLI command.

---

## Scenario

| Parameter | Value |
|---|---|
| Agent | OMNIX-AGENT-TREASURY-001 |
| Human authority | CFO-OPERATOR-HN-001 |
| Transaction | Cross-border liquidity release to EUR counterparty |
| Amount | USD 50,000,000 |
| Settlement rail | SWIFT MT202 / XRPL RLUSD |
| Domain | Institutional treasury |
| Mandate reference | TREASURY-MANDATE-2026-Q2 |
| Risk class | CRITICAL |
| Regulatory frameworks | EU AI Act Art. 9 · MiCA Title VI · DORA Art. 11 |

---

## Architecture

### Eight-step TA-14 chain (both paths)

```
1. SOURCE_STATE       Request + full treasury context + TCS (nanosecond regulatory timestamp)
2. AUTHORITY          DR issued + MIVP MBR activated before Turn 1
3. RUNTIME            CES computed + MIVP MAS per-turn + CCS conformance signal
4. COUNTERFACTUAL     CGE: 5 CFRs + CAT (decision space documented and sealed)
5. VERDICT            HALT (dangerous) or TAR ADMITTED (admissible)
6. GATE               OSG: ValidationReceipt REJECTED or APPROVED
7. EXECUTION          Refusal receipt or BAR + CTCHC + settlement reference
8. POST_EXECUTION     CTCHC sealed + TGB snapshot + replay proof
```

### Dangerous path

Conditions: authority budget depleted to 42% via drift across 6 prior sessions. CES=CRITICAL. MIVP detects proxy optimisation violation (speed-over-verification). OSG receives no PoGC — rejects independently, fail-closed.

Artefacts produced:
- DR with degraded budget (42/100)
- MBR issued, MAS=0.24 (HALT), 1 proxy_guard_violation
- RCR: CES=CRITICAL (formula: T×0.30 + B×0.30 + D×0.20 + I×0.20)
- 5 CFRs: 4 alternatives all blocked at different invariants, 1 requires human re-auth
- CAT: decision space sealed (5 CFRs, fragility scores ∈ [0,1])
- OSG ValidationReceipt: REJECTED (fail-closed, no PoGC)
- Refusal receipt (PQC-signed): 5 rejection reasons
- MBR Seal: UNCERTIFIED (1 violation)
- BAR: governance halt output attested
- CTCHC: sealed in HALTED state — forensic replay available
- TCS: regulatory context embedded post-halt

### Admissible path

Conditions: authority recertified (budget=88/100, TTL=4h fresh). CES=NOMINAL. MIVP MAS=0.94 (ALIGNED). Zero violations, zero warnings. Dual approval satisfied.

Artefacts produced:
- DR with healthy budget (88/100), dual approval reference embedded
- MBR issued, MAS=0.94 (ALIGNED), zero violations, zero warnings
- RCR: CES=NOMINAL (T≈99%, B=88%, D=97%, I=98.5%)
- 5 CFRs: all 5 alternatives would also admit, selected path has lowest fragility (0.09)
- CAT: decision space sealed
- TAR: ADMITTED (nanosecond-precision execution timestamp)
- Binding record + Commit record (scope locked before execution)
- PoGC: MANDATE-BOUND certification (MIVP-INV-008)
- MBR Seal: MANDATE-BOUND (zero violations, zero warnings)
- OSG ValidationReceipt: APPROVED
- BAR: execution output attested (PQC-signed)
- CTCHC: sealed (CLOSED state)
- Settlement reference: SWIFT MT202 + XRPL TxID embedded
- Outcome receipt (PQC-signed)
- TCS: regulatory context embedded post-execution
- Replay proof

---

## Artefacts

### Artefacts present in both paths

| Artefact | ID Prefix | Standard | Description |
|---|---|---|---|
| DelegationReceipt (DR) | ATFDR- | RFC-ATF-1 | PQC-signed authority grant |
| MandateBindingRecord (MBR) | MBR- | ADR-194 | Frozen mandate declaration (before Turn 1) |
| MandateAlignmentScore (MAS) | MAS- | ADR-194 | Per-turn mandate alignment |
| MBR Seal | MBRSEAL- | ADR-194 | Session-close mandate certification |
| ContinuityRecord (RCR) | ATFRCR- | RFC-ATF-2 | CES: T×0.30 + B×0.30 + D×0.20 + I×0.20 |
| CounterfactualForkRecord ×5 | CFR- | RFC-ATF-5 | What else could have happened |
| CounterfactualAttestationToken | CAT- | RFC-ATF-5 | CGE seal over all CFRs |
| TemporalContextSnapshot | ATFTCS- | RFC-ATF-5 | Nanosecond regulatory timestamp |
| OSG ValidationReceipt | VR- | ADR-188 | Settlement gate verdict |
| BehavioralAnchorRecord (BAR) | BAR- | RFC-ATF-6 | Actual agent output, PQC-attested |
| CTCHC (sealed) | CTCHC- | RFC-ATF-6 | Turn hash chain, sealed |
| Replay Proof | REPLAY- | ADR-201 | Offline replay continuity proof |

### Artefacts present in admissible path only

| Artefact | ID Prefix | Standard | Description |
|---|---|---|---|
| TemporalAdmissibilityRecord (TAR) | ATFTAR- | RFC-ATF-2 | Admission verdict (nanosecond) |
| Binding Record | BIND- | ADR-200 | Authority basis accepted |
| Commit Record | COMMIT- | ADR-200 | Scope locked before execution |
| Proof of Governance Certificate (PoGC) | POGC- | ADR-186/187 | MANDATE-BOUND certification |
| Settlement Reference | — | — | SWIFT MT202 + XRPL TxID |
| Outcome Receipt | OUTCOME- | ADR-201 | Execution outcome, PQC-signed |

### Artefacts present in dangerous path only

| Artefact | ID Prefix | Standard | Description |
|---|---|---|---|
| Refusal Receipt | REFUSAL- | ADR-201 | 5-reason PQC-signed refusal |

---

## Invariants demonstrated

28 invariants demonstrated across ATF, BEV, MIVP, CGE, TGB, PoGR, and RTE families:

- ATF-INV-001/002/005 — MAR, DR signing, receipt immutability
- BEV-INV-001/010/011/013/014 — BAR, CTCHC lifecycle
- MIVP-INV-001/003/007/008 — MBR, MAS, MBRSeal, MANDATE-BOUND
- CGE-INV-001/002/003/007 — CFR evaluation, CAT root hash, fragility bounds, PQC
- TGB-INV-001 — TCS nanosecond regulatory context
- PoGR-INV-001/002/003 — PoGC issuance, append-only, offline verifiable
- RTE-INV-001–008 — Package integrity, dual-path, HALT proof, MANDATE-BOUND, CFR count, TCS, offline verification, CLI exit code

---

## CLI Verifier

```bash
# Full verification (all checks, ~60 checks total)
python scripts/verify_treasury_execution_trace.py evidence_packages/OMNIX-RTE-001_*.json

# Targeted verification
python scripts/verify_treasury_execution_trace.py <package.json> --verify-authority
python scripts/verify_treasury_execution_trace.py <package.json> --verify-continuity
python scripts/verify_treasury_execution_trace.py <package.json> --verify-counterfactual
python scripts/verify_treasury_execution_trace.py <package.json> --verify-halt
python scripts/verify_treasury_execution_trace.py <package.json> --verify-settlement
python scripts/verify_treasury_execution_trace.py <package.json> --verify-replay

# Machine-readable output (for audit pipelines)
python scripts/verify_treasury_execution_trace.py <package.json> --json
```

Exit codes: 0 (all PASS) · 1 (FAIL) · 2 (invalid package)

**What it confirms:**
- All PQC signatures (ML-DSA-65) against the embedded public key
- All content hashes (SHA-256/SHA3-256) against reconstructed values
- CES formula consistency
- CGE CFR root hash and fragility bounds
- CTCHC link chain continuity
- OSG verdicts (REJECTED dangerous, APPROVED admissible)
- Mandate certification tiers
- Settlement reference presence
- HALT structural assertions

**What it does not confirm:**
- Governance policy values (FX rate bands, counterparty lists, mandate amounts)
- External market data referenced in source_state

---

## Generator

```bash
python scripts/generate_treasury_execution_trace.py
```

Produces: `evidence_packages/OMNIX-RTE-001_{timestamp}.json`

The generator bootstraps a fresh Dilithium-3 keypair for each run. Every signature in the package is produced with this ephemeral key. The public key is embedded in the package under `.pqc.public_key_b64`. No external OMNIX runtime is required to generate or verify the package.

---

## PQC Specification

| Parameter | Value |
|---|---|
| Algorithm | ML-DSA-65 (Dilithium-3) |
| Standard | NIST FIPS 204 |
| Security level | NIST Level 3 |
| Key generation | Fresh ephemeral keypair per package |
| Hash (DR/TAR) | SHA-256, compact JSON separators |
| Hash (all others) | SHA3-256, default JSON separators |
| Sig payload (all) | Compact JSON separators |
| BAR sig payload | Default JSON separators (matches BAREngine) |
| CTCHC seal sig | Default JSON separators (matches CTCHCEngine) |

---

## Files

| File | Description |
|---|---|
| `scripts/generate_treasury_execution_trace.py` | Package generator |
| `scripts/verify_treasury_execution_trace.py` | CLI verifier |
| `scripts/generate_rte_pdf.py` | Premium PDF generator |
| `evidence_packages/OMNIX-RTE-001_*.json` | Generated packages |
| `evidence_packages/OMNIX-RTE-001_*.pdf` | Generated PDFs |
| `docs/adr/ADR-201-*.md` | Architectural spec |
| `docs/products/RTE_SPEC.md` | This document |

---

## Relation to prior artefacts

| Artefact | Relation to OMNIX-RTE-001 |
|---|---|
| RCEP (ADR-200) | Predecessor. RTE-001 extends with MIVP, CGE, TGB, OSG, settlement |
| PoGR/PoGC (ADR-186/187) | PoGC issued in admissible path with MANDATE-BOUND certification |
| OSG (ADR-188) | OSG ValidationReceipt in both paths — REJECTED/APPROVED |
| MIVP (ADR-194) | MBR + MAS + MBRSeal in both paths |
| RFC-ATF-5 | CGE (CFR/CAT) + TGB (TCS) components |
| RFC-ATF-6 | BAR + CTCHC in both paths |

---

## Regulatory positioning

The OMNIX-RTE-001 provides direct evidence for:

- **EU AI Act Art. 9** (Risk Management Systems for high-risk AI): the dangerous path demonstrates that a CRITICAL-risk autonomous transaction cannot execute without complete, valid governance authority.
- **MiCA Title VI** (ARTs, EMTs): settlement is gated behind PoGC — no governance certificate, no settlement.
- **DORA Art. 11** (ICT Continuity): replay proof provides post-event continuity evidence.

The EU AI Act enforcement date is 1 August 2026.
