# VERIFY.md — OMNIX-RTE-001 Verification Commands

All commands run from the package root directory.
Requirements: Python 3.9+ — no external dependencies.

---

## Full verification (101 checks)

```
python verify.py
```

Expected output:

```
  TOTAL CHECKS : 101
  PASSED        : 101
  FAILED        : 0
  SKIPPED       : 0
  VERDICT: ALL VERIFICATIONS PASS — package integrity confirmed
```

---

## Targeted verification modes

### 1. Verify authority chain (DR + MBR) — both paths

```
python verify.py --verify-authority
```

Checks: Delegation Receipt integrity + PQC signature, Mandate Binding Record
signature, MAR constraint (budget_granted <= budget_delegator), MIVP thresholds.

Expected: `15 / 15 PASS`

---

### 2. Verify runtime continuity (RCR + CES + MAS) — both paths

```
python verify.py --verify-continuity
```

Checks: CES formula consistency (T*0.30 + B*0.30 + D*0.20 + I*0.20),
CES band classification, MAS score + PQC signature, proxy-guard violation flag.

Expected: `17 / 17 PASS`

---

### 3. Verify counterfactual engine (CGE CFRs + CAT) — both paths

```
python verify.py --verify-counterfactual
```

Checks: 5 Counterfactual Fork Records per path, CAT cfr_root_hash covers all
CFR IDs, CAT PQC signature, fragility scores present.

Expected: `17 / 17 PASS`

---

### 4. Verify dangerous path HALT enforcement

```
python verify.py --verify-halt
```

Checks: Refusal receipt type=HARD_REFUSAL, settlement_status=BLOCKED,
OSG verdict=REJECTED, execution_occurred=False, settlement_released=False,
BAR/CTCHC forensic seals, MBR seal tier=UNCERTIFIED.

Expected: `25 / 25 PASS`

Key invariants verified:
- RTE-INV-002: No execution without admissibility
- BEV-INV-013: CTCHC chain sealed in HALTED state
- OSG-INV-001: OSG fail-closed under invalid authority

---

### 5. Verify admissible path settlement

```
python verify.py --verify-settlement
```

Checks: TAR admission_status=ADMITTED, PoGC PQC signature,
PoGC mandate_certification=MANDATE-BOUND, MBR seal tier=MANDATE-BOUND,
OSG verdict=APPROVED, outcome receipt, settlement amount=50000000,
BAR/CTCHC forensic seals.

Expected: `33 / 33 PASS`

Key invariants verified:
- PoGR-INV-003: PoGC offline-verifiable
- MIVP-INV-008: MANDATE-BOUND certification requires zero violations
- ATF-INV-001: MAR (Monotonic Authority Reduction) enforced

---

### 6. Verify post-execution replay proofs — both paths

```
python verify.py --verify-replay
```

Checks: Temporal Context Snapshots (pre + post), Replay Proof hashes and
PQC signatures, terminal_status values (HALTED / CLOSED), offline_verifiable=True.

Expected: `19 / 19 PASS`

---

## Machine-readable output (JSON)

```
python verify.py --json
```

Returns a structured JSON report with status per check, suitable for
audit pipeline integration or automated compliance reporting.

---

## What the verifier does NOT check

The verifier is scoped to cryptographic and structural integrity only:

- It does NOT validate governance policy values (FX bands, counterparty lists)
- It does NOT access the OMNIX platform, network, or any external service
- It does NOT require the OMNIX private key — only the embedded public key

If all 101 checks pass, the package has not been altered since generation,
all PQC signatures are valid, and the structural invariants are satisfied.

---

## Proof of Governance Certificate

The admissible path produced a PoGC that can be independently verified:

```
POGC-F1DC0218E5204875
Tier:       MANDATE-BOUND
Standard:   RFC-ATF-1 through RFC-ATF-6 / ADR-201
Settlement: USD 50,000,000
SWIFT:      MT202-2CAA8C200950
XRPL:       XRPL-8F7967D6A3A04ECC8C27CD0C
```

To inspect the PoGC directly:

```python
import json
pkg = json.load(open("evidence/OMNIX-RTE-001_*.json"))
pogc = pkg["paths"]["path_admissible"]["steps"]["6_gate"]["proof_of_governance_certificate"]
print(json.dumps(pogc, indent=2))
```
