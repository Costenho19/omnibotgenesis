# ADR-203 — RTE-001 Institutional Artifact Extraction Protocol (IAEP)

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-30  
**Supersedes:** —  
**Related:** ADR-201 (RTE-001 spec) · ADR-194 (MIVP) · ADR-183 (CTCHC) · ADR-186 (PoGR)  
**RFC:** RFC-ATF-1 through RFC-ATF-6

---

## Context

### The Four Properties That Make RTE-001 Institutional

OMNIX-RTE-001 v1.3.0 produces a triple-path execution package (148/148 verifier checks) that demonstrates governance-grade treasury execution. An external technical review of v1.2.0 identified four properties that collectively elevate the package from a demonstration to an institutional artifact:

1. **Treasury-grade multi-step execution** — The 3-turn SWIFT MT103 → FIX 4.4 → XRPL RLUSD sequence maps each execution step to a real institutional protocol standard. Each turn has its own PQC-signed BAR. An auditor can verify forensically what the agent did in each step, not only whether the final result was approved.

2. **Continuous mandate verification** — The MBR (Mandate Binding Record) is frozen cryptographically before Turn 0 (MIVP-INV-001). Each subsequent turn produces a MAS (Mandate Alignment Score). In Path C, the system executes Turn 0 (ALIGNED, MAS=0.94), warns at Turn 1 (WARNING, MAS=0.61), and halts at Turn 2 (HALT, MAS=0.28 < 0.30 threshold). The mandate cannot be renegotiated mid-execution.

3. **Forensic chain-of-custody** — The CTCHC (Cross-Turn Coherence Hash Chain) links each turn cryptographically: `link_hash = SHA3-256(prev_link_hash ‖ turn_hash ‖ governing_receipt_id)`. Modifying any BAR breaks all subsequent links and the seal. Verifiable offline, no runtime access required.

4. **Backward-compatible protocol evolution** — From v1.0.0 (single-path, ~74 checks) to v1.3.0 (triple-path, 148 checks), no existing check was ever modified. New paths add new checks; existing paths are never touched.

### The Gap

These four properties exist inside the full RTE-001 package but are not extractable as standalone institutional artifacts. A banking regulator, a MiFID-II auditor, or a court cannot efficiently locate and present a single property without navigating the full package.

### Decision

Introduce the **Institutional Artifact Extraction Protocol (IAEP)** — four premium reporting commands added to the RTE-001 verifier that extract each of the four properties as standalone, formatted, shareable artifacts.

---

## Decision

### Architecture

The IAEP commands are integrated into `scripts/verify_treasury_execution_trace.py` as post-verification reporting commands. They:

- Read directly from the loaded RTE-001 JSON package
- Produce formatted terminal output suitable for pipe, redirect, or copy-paste into regulatory submissions
- Do **not** add to the verification check count (`EXPECTED_TOTAL_CHECKS = 148` is unchanged)
- Run **after** the verification summary when combined with verify flags
- Run **standalone** (only structural checks, no verification suite) when no verify flags are present

```
scripts/verify_treasury_execution_trace.py <package.json>
  ├── [verification mode — default or targeted]
  │     --verify-authority / --verify-continuity / ... / --verify-interrupted
  │     → produces: check results + PASS/FAIL summary (148 checks FULL mode)
  │
  └── [IAEP reporting mode — explicit opt-in, ADR-203]
        --treasury-protocol  → TPER (IAEP-RPT-001)
        --mandate-timeline   → MIT  (IAEP-RPT-002)
        --chain-custody      → CoCC (IAEP-RPT-003)
        --check-version      → VCA  (IAEP-RPT-004)
```

---

## The Four IAEP Artifacts

### §2.1 — Treasury Protocol Execution Report (TPER) · `--treasury-protocol`

**Artifact ID:** IAEP-RPT-001  
**Command:** `python verify.py <package.json> --treasury-protocol`

Presents the 3-turn SWIFT→FIX→XRPL execution sequence with per-turn BAR attestation, MAS mandate verdict, and institutional protocol metadata from both the admissible path (all VALID → settlement RELEASED) and the interrupted path (HALT at Turn 2).

**Turn mapping:**

| Turn | Protocol | Standard | Role |
|---|---|---|---|
| Turn 0 | SWIFT MT103 | ISO 15022 / SWIFT FIN | Counterparty validation + sanctions screening |
| Turn 1 | FIX 4.4 | FIX Protocol Ltd. | Order routing — institutional gateway |
| Turn 2 | XRPL RLUSD | XRPL Foundation / Ripple | Atomic settlement + finality confirmation |

**Per-turn data shown:** BAR ID · BAR content_hash · MAS score + verdict · proxy guard violations · output preview · PQC algorithm · CTCHC link anchor.

**Primary audience:** SWIFT compliance teams · MiFID-II auditors · banking regulators · institutional counterparties.

**Differentiator:** No other AI governance system produces a per-turn, protocol-mapped, PQC-signed execution report aligned to real institutional standards.

---

### §2.2 — Mandate Integrity Timeline (MIT) · `--mandate-timeline`

**Artifact ID:** IAEP-RPT-002  
**Command:** `python verify.py <package.json> --mandate-timeline`

Renders the complete mandate lifecycle for all three paths:

```
MBR ISSUED (pre-Turn-0, frozen — MIVP-INV-001)
     │
     ├── Turn 0 (SWIFT): MAS=0.94  ALIGNED  ████████████████████░░░░░░░░░░
     ├── Turn 1 (FIX):   MAS=0.61  WARNING  ████████████░░░░░░░░░░░░░░░░░░
     └── Turn 2 (XRPL):  MAS=0.28  HALT     █████░░░░░░░░░░░░░░░░░░░░░░░░░
                               ↑HALT(0.30)        ↑WARN(0.65)
     │
MBR SEAL → certification tier: MANDATE-BOUND / MANDATE-ALIGNED / UNCERTIFIED
```

**Per-path data shown:** MBR ID + issued_at + thresholds + hash + PQC · per-turn MAS score + visual bar + verdict + violations/warnings · MBR Seal certification tier + total violations/warnings + hash + PQC.

**Primary audience:** Risk committees · compliance officers · internal audit · EU AI Act Art. 9 submissions.

**Differentiator:** The world's first per-turn, threshold-aware mandate alignment timeline for AI agent governance, backed by PQC-signed artifacts at every step.

---

### §2.3 — Chain-of-Custody Certificate (CoCC) · `--chain-custody`

**Artifact ID:** IAEP-RPT-003  
**Command:** `python verify.py <package.json> --chain-custody`

Extracts the CTCHC from both the admissible path (terminal: CLOSED) and the interrupted path (terminal: HALTED) and formats each as a standalone forensic chain-of-custody document.

**Hash chain formula:**

```
link_hash[i] = SHA3-256(link_hash[i-1] ‖ turn_hash[i] ‖ governing_receipt_id)
link_hash[0] = SHA3-256(GENESIS ‖ turn_hash[0] ‖ governing_receipt_id)
```

**Per-link data shown:** Link ID · prev_link_hash (or GENESIS) · turn_hash · governing_receipt_id · chain_link_hash · created_at · feed arrow to next link.

**Chain seal shown:** seal_hash · PQC signature presence · terminal_state (CLOSED or HALTED).

**Offline verification protocol included:**
1. Recompute SHA3-256(prev_link ‖ turn_hash ‖ governing_receipt_id) for each link
2. Confirm chain_link_hash matches
3. Confirm current_tip_hash = last link's chain_link_hash
4. Verify seal PQC sig: ML-DSA-65.verify(seal_hash, sig, public_key)
5. Confirm terminal_state matches expected

**Primary audience:** Courts · forensic auditors · regulators requiring chain-of-custody documentation · due diligence reviews.

**Differentiator:** The world's first PQC-signed, per-turn chain-of-custody certificate for AI governance decisions. BEV-INV-010–014 (RFC-ATF-6, ADR-183).

---

### §2.4 — Version Compatibility Attestation (VCA) · `--check-version`

**Artifact ID:** IAEP-RPT-004  
**Command:** `python verify.py <package.json> --check-version`

Formal machine-readable declaration of: package spec version detected from paths present, expected check count for that version, and the backward-compatibility guarantee that governs all RTE-001 evolution.

**Compatibility matrix shown:**

| Spec | Paths | Checks | New checks added |
|---|---|---|---|
| v1.0.0 | A+B | ~74 | Baseline |
| v1.1.0 | A+B | ~74 | MBR/MAS/CTCHC added to existing paths |
| v1.2.0 | A+B | 111 | +37 checks on existing paths (explicit MAS/CTCHC) |
| v1.3.0 | A+B+C | 148 | +37 checks for Path C (interrupted execution) |

**Primary audience:** Technical reviewers · CI/CD pipelines · audit teams verifying protocol version · enterprise integration teams.

---

## §3 — Invariants

### COMPAT-INV-001 — Backward-Compatibility Guarantee

Each RTE-001 version upgrade adds verification checks to new paths or new artifact types. Existing checks on existing paths are NEVER modified or removed. A package that passed N checks under verifier version V will still pass those same N checks under any later version V+k.

Formal statement: `∀ pkg ∈ RTE-001-v1.k, ∀ check c ∈ checks(v1.k): c ∈ checks(v1.k+1) ∧ verdict(c, pkg, v1.k) = verdict(c, pkg, v1.k+1)`

### IAEP-INV-001 — No Check Count Inflation

IAEP reporting commands (`--treasury-protocol`, `--mandate-timeline`, `--chain-custody`, `--check-version`) do not add to `EXPECTED_TOTAL_CHECKS`. The verifier check count is owned exclusively by the verification suites. Reporting is orthogonal to verification.

### IAEP-INV-002 — Package-Only Extraction

All four IAEP reports are generated exclusively from data already present in the RTE-001 package JSON. No external API calls, no database queries, no runtime access. Every IAEP report is as offline-verifiable as the package itself.

### IAEP-INV-003 — Ordered Execution

When combined with verification flags, IAEP reports run AFTER the verification summary. The user sees the cryptographic verdict before the institutional artifact. This ordering is fixed and cannot be overridden.

---

## §4 — Usage Examples

```bash
# Full verification (148/148 PASS) + all 4 institutional reports
python scripts/verify_treasury_execution_trace.py evidence_packages/OMNIX-RTE-001_*.json \
  --treasury-protocol --mandate-timeline --chain-custody --check-version

# Institutional reports only (no verification suite — structural checks still run)
python scripts/verify_treasury_execution_trace.py evidence_packages/OMNIX-RTE-001_*.json \
  --treasury-protocol

# For regulators: mandate timeline + chain custody only
python scripts/verify_treasury_execution_trace.py evidence_packages/OMNIX-RTE-001_*.json \
  --mandate-timeline --chain-custody

# For technical reviewers: version attestation
python scripts/verify_treasury_execution_trace.py evidence_packages/OMNIX-RTE-001_*.json \
  --check-version

# Combine with machine-readable output
python scripts/verify_treasury_execution_trace.py evidence_packages/OMNIX-RTE-001_*.json \
  --verify-settlement --check-version --json
```

---

## §5 — Implementation

**File modified:** `scripts/verify_treasury_execution_trace.py`  
**Functions added:**
- `report_treasury_protocol(pkg: Dict) → None` — IAEP-RPT-001
- `report_mandate_timeline(pkg: Dict) → None` — IAEP-RPT-002
- `report_chain_custody(pkg: Dict) → None` — IAEP-RPT-003
- `report_version_compatibility(pkg: Dict, pkg_path: str) → None` — IAEP-RPT-004
- `_TURN_PROTOCOLS: Dict[int, tuple]` — shared turn metadata constant
- `_TURN_LABELS: Dict[int, str]` — shared turn label constant

**`EXPECTED_TOTAL_CHECKS`:** Unchanged at 148. IAEP-INV-001.

**Argparse flags added:**
- `--treasury-protocol` → calls `report_treasury_protocol(pkg)`
- `--mandate-timeline` → calls `report_mandate_timeline(pkg)`
- `--chain-custody` → calls `report_chain_custody(pkg)`
- `--check-version` → calls `report_version_compatibility(pkg, pkg_path)`

**`any_reports` variable:** Added to `main()` to detect IAEP flags and exclude them from `run_all` verification trigger. When only IAEP flags are set, `run_all = False` (structural checks only, no 148-check suite).

---

## §6 — Consequences

### Positive
- Four peer-reviewed properties of RTE-001 are now formally extractable as standalone institutional artifacts
- Each artifact is shareable with its target audience without exposing the full package
- The verifier is now a multi-tool: cryptographic verifier + institutional artifact extractor
- COMPAT-INV-001 formally documents the backward-compatibility guarantee that has held across all versions
- `EXPECTED_TOTAL_CHECKS = 148` remains unchanged — no CI/CD breakage

### Constraints
- IAEP reports are terminal output only — no PDF or JSON serialization in this version (planned for ADR-203)
- `--mandate-timeline` for Path A (dangerous) shows MBR and MBR Seal but no execution turns, since the path halts before reaching the runtime
- `--treasury-protocol` covers admissible and interrupted paths only — dangerous path has no execution turns to report

---

*ADR-203 · OMNIX QUANTUM LTD · Harold Nunes · May 2026*  
*Institutional Artifact Extraction Protocol · IAEP-RPT-001–004*
