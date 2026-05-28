# QUICKSTART.md — First-Time Reviewer

This is the fastest path from download to verified result.

---

## Step 1 — Confirm Python version

```
python --version
```

Any version >= 3.9 works. No pip install. No virtual environment. No dependencies.

---

## Step 2 — Run full verification

```
python verify.py
```

This runs 101 checks across both execution paths (dangerous and admissible).
It takes approximately 3-5 seconds.

You should see:

```
  TOTAL CHECKS : 101
  PASSED        : 101
  FAILED        : 0
  VERDICT: ALL VERIFICATIONS PASS — package integrity confirmed
```

If you see this, the package has not been altered, all PQC signatures are
cryptographically valid, and the structural invariants hold.

---

## Step 3 — Verify the HALT (dangerous path)

```
python verify.py --verify-halt
```

This proves that the autonomous agent was stopped before any execution occurred.

Key checks:
- `execution_occurred = False`
- `settlement_released = False`
- OSG verdict = `REJECTED`
- Refusal type = `HARD_REFUSAL`
- CTCHC sealed in HALTED state (BEV-INV-013)

---

## Step 4 — Verify the settlement (admissible path)

```
python verify.py --verify-settlement
```

This proves that the same agent, under recertified authority, executed the
transfer and that the execution is forensically sealed.

Key checks:
- TAR status = `ADMITTED`
- PoGC `POGC-F1DC0218E5204875` = `MANDATE-BOUND`
- Settlement amount = USD 50,000,000
- OSG verdict = `APPROVED`

---

## Step 5 — Inspect the raw evidence

The complete evidence package is in `evidence/OMNIX-RTE-001_*.json`.
It is a self-contained JSON file with all artifacts for both paths.

```python
import json
pkg = json.load(open("evidence/OMNIX-RTE-001_20260528_071811.json"))

# Dangerous path summary
print(json.dumps(pkg["paths"]["path_dangerous"]["summary"], indent=2))

# Admissible path summary
print(json.dumps(pkg["paths"]["path_admissible"]["summary"], indent=2))

# Public key used to verify all 101 signatures
print(pkg["pqc"]["algorithm"])
print(pkg["pqc"]["public_key_b64"][:80], "...")
```

---

## Step 6 — Read the institutional document

Open `evidence/OMNIX-RTE-001_*.pdf` for a 15-page forensic narrative
covering all artifacts, both paths, and the verification report.

---

## What this package demonstrates

| Property | Status |
|---|---|
| Autonomous agent halted before execution | Proven cryptographically |
| Halt is offline-verifiable without OMNIX | Confirmed (101/101 PASS) |
| Admissible execution forensically sealed | Proven cryptographically |
| PoGC issued for admissible settlement | POGC-F1DC0218E5204875 |
| PQC algorithm | ML-DSA-65 (Dilithium-3, FIPS 204) |
| External dependencies required | None |
| Network access required | None |
| OMNIX platform access required | None |

---

## Questions or challenges

If you find a check that fails, or a signature that does not verify,
that is a finding worth reporting. The package is designed to be challenged.

Contact: OMNIX QUANTUM LTD — Harold Nunes
Standard: RFC-ATF-1 through RFC-ATF-6 · ADR-201
