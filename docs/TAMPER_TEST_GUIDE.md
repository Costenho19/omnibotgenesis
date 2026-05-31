# OMNIX QUANTUM — Independent Tamper Test Guide

**Version:** 1.0.0 · **Package:** OMNIX-RTE-001 v1.4.0  
**Audience:** Independent technical reviewers — no OMNIX account, no API key required  
**Time required:** ~10 minutes  
**Purpose:** Verify that the OMNIX evidence package detects any modification to its cryptographic integrity chain

---

## What This Demonstrates

The OMNIX Governance Package contains a cryptographic chain sealed with **ML-DSA-65 (Dilithium-3, FIPS 204)** — the NIST post-quantum cryptography standard. This guide lets you independently verify:

1. A clean package passes all 187 integrity checks (`exit code 0`)
2. Any single-byte mutation to a predicate hash is detected immediately (`exit code 1`)
3. Any mutation to the PQC signature is detected immediately (`exit code 1`)
4. Verification works **offline** — zero OMNIX infrastructure required

---

## Step 1: Requirements

Install the post-quantum cryptography library:

```bash
pip install oqs-python
```

Expected output:
```
Successfully installed oqs-python-X.X.X
```

> **Note:** This is the only dependency beyond Python 3.9+. No OMNIX account, no API key, no network access after install.

---

## Step 2: Download the Evidence Package

You should have received a `.zip` containing:
- `OMNIX-RTE-001_<timestamp>.json` — the evidence package
- `verify_treasury_execution_trace.py` — the standalone verifier
- `INDEPENDENT_VERIFIER_GUIDE.md` — one-page quick reference

Place all three in the same directory. Navigate to that directory:

```bash
cd /path/to/reviewer-package/
```

---

## Step 3: Verify the Clean Package (Baseline)

Run the full verification suite including IPFL intake checks:

```bash
python verify_treasury_execution_trace.py OMNIX-RTE-001_<timestamp>.json --verify-intake
```

**Expected output (last lines):**

```
  PASSED        : 187
  FAILED        : 0
  SKIPPED       : 0
  VERDICT: ALL VERIFICATIONS PASS — package integrity confirmed

Exit code: 0
```

**What this confirms:**
- All 187 cryptographic checks pass
- The Governance Contract (GCFR) was formed before Turn 0 and is intact
- The 5 predicates (IAD · SAR · MFR · CPS · FPS) match their SHA3-256 hashes
- The ML-DSA-65 signature over the intake seal is valid
- The MANDATE-BOUND certification is consistent across the session

To capture the exit code explicitly:

```bash
python verify_treasury_execution_trace.py OMNIX-RTE-001_<timestamp>.json --verify-intake
echo "Exit code: $?"
```

---

## Step 4: Perform the Tamper

The following one-liner mutates the first predicate hash in the `path_admissible` intake step. This simulates what an attacker would do to try to alter the governance record.

### Tamper A — Mutate a predicate component hash

```bash
python3 - << 'EOF'
import json, copy, sys

PKG = "OMNIX-RTE-001_<timestamp>.json"  # replace with your filename

with open(PKG) as f:
    pkg = json.load(f)

tampered = copy.deepcopy(pkg)
ch = tampered["paths"]["path_admissible"]["steps"]["0_intake"]["component_hashes"]
original = ch[0]
ch[0] = "deadbeef" + original[8:]  # mutate first 8 hex chars

with open("TAMPERED_component_hash.json", "w") as f:
    json.dump(tampered, f)

print(f"Original hash[0] : {original[:32]}...")
print(f"Mutated  hash[0] : {ch[0][:32]}...")
print("Tampered package saved: TAMPERED_component_hash.json")
EOF
```

### Tamper B — Mutate the GCFR seal hash

```bash
python3 - << 'EOF'
import json, copy

PKG = "OMNIX-RTE-001_<timestamp>.json"  # replace with your filename

with open(PKG) as f:
    pkg = json.load(f)

tampered = copy.deepcopy(pkg)
seal = tampered["paths"]["path_admissible"]["steps"]["0_intake"]["intake_seal"]
original = seal["seal_hash"]
seal["seal_hash"] = "aabbccdd" + original[8:]

with open("TAMPERED_seal_hash.json", "w") as f:
    json.dump(tampered, f)

print(f"Original seal_hash : {original[:32]}...")
print(f"Mutated  seal_hash : {seal['seal_hash'][:32]}...")
print("Tampered package saved: TAMPERED_seal_hash.json")
EOF
```

### Tamper C — Mutate the ML-DSA-65 PQC signature

```bash
python3 - << 'EOF'
import json, copy

PKG = "OMNIX-RTE-001_<timestamp>.json"  # replace with your filename

with open(PKG) as f:
    pkg = json.load(f)

tampered = copy.deepcopy(pkg)
seal = tampered["paths"]["path_admissible"]["steps"]["0_intake"]["intake_seal"]
original_sig = seal["pqc_signature"]
seal["pqc_signature"] = "ZZZZZZZZ" + original_sig[8:]

with open("TAMPERED_pqc_sig.json", "w") as f:
    json.dump(tampered, f)

print(f"Original sig (first 32): {original_sig[:32]}...")
print(f"Mutated  sig (first 32): {seal['pqc_signature'][:32]}...")
print("Tampered package saved: TAMPERED_pqc_sig.json")
EOF
```

---

## Step 5: Verify the Tampered Packages

Run the verifier against each tampered package:

### Tamper A result

```bash
python verify_treasury_execution_trace.py TAMPERED_component_hash.json --verify-intake
echo "Exit code: $?"
```

**Expected output:**

```
  ✗ [INT-ADM-GCFR-HASH] [ADMISSIBLE] GCFR seal_hash = SHA3-256(iad_hash|sar_hash|mfr_hash|cps_hash|fps_hash) (IPFL-INV-007)

  PASSED        : 186
  FAILED        : 1
  SKIPPED       : 0
  VERDICT: 1 VERIFICATION(S) FAILED — package integrity compromised

Exit code: 1
```

### Tamper B result

```bash
python verify_treasury_execution_trace.py TAMPERED_seal_hash.json --verify-intake
echo "Exit code: $?"
```

**Expected output:**

```
  ✗ [INT-ADM-GCFR-HASH] [ADMISSIBLE] GCFR seal_hash = SHA3-256(iad_hash|sar_hash|mfr_hash|cps_hash|fps_hash) (IPFL-INV-007)
  ✗ [INT-ADM-GCFR-SIG]  [ADMISSIBLE] GCFR intake_seal PQC signature (ML-DSA-65) — contract sealed before Turn 0

  PASSED        : 185
  FAILED        : 2
  SKIPPED       : 0
  VERDICT: 2 VERIFICATION(S) FAILED — package integrity compromised

Exit code: 1
```

### Tamper C result

```bash
python verify_treasury_execution_trace.py TAMPERED_pqc_sig.json --verify-intake
echo "Exit code: $?"
```

**Expected output:**

```
  ✗ [INT-ADM-GCFR-SIG] [ADMISSIBLE] GCFR intake_seal PQC signature (ML-DSA-65) — contract sealed before Turn 0

  PASSED        : 186
  FAILED        : 1
  SKIPPED       : 0
  VERDICT: 1 VERIFICATION(S) FAILED — package integrity compromised

Exit code: 1
```

---

## What the Results Mean

| Tamper | Check Failed | Invariant | Why it matters |
|--------|-------------|-----------|----------------|
| Component hash | `INT-ADM-GCFR-HASH` | IPFL-INV-007 | The GCFR seal covers all 5 predicate hashes. Any change to a predicate breaks the seal. |
| Seal hash | `INT-ADM-GCFR-HASH` + `INT-ADM-GCFR-SIG` | IPFL-INV-007 | Changing the seal hash invalidates both the hash check and the ML-DSA-65 signature. |
| PQC signature | `INT-ADM-GCFR-SIG` | ML-DSA-65 | Without the private key (Dilithium-3), it is computationally impossible to forge a valid signature. |

**Key property:** The verifier uses only the **public key embedded in the package** — it does not contact OMNIX servers. The verification is fully self-contained and reproducible by any third party.

---

## Security Guarantees

- **No private key = no forgery.** The ML-DSA-65 signature cannot be reproduced without OMNIX's private key. An attacker who modifies any field and tries to re-sign will fail — the key is never distributed.
- **Hash chain is total.** The GCFR seal covers all 5 predicates. The CTCHC covers all turns. Modifying any node in the chain breaks the hash at that node and all subsequent checks.
- **Offline by design.** The verifier is a standalone Python script with zero network calls. It can be audited line by line.
- **Post-quantum resistant.** ML-DSA-65 is NIST FIPS 204 — designed to resist attacks from quantum computers.

---

## Regulatory Context

This package provides cryptographic evidence compliant with:

| Regulation | Requirement | How OMNIX satisfies it |
|------------|-------------|----------------------|
| EU AI Act Art. 9/11 | Risk management + technical documentation | GCFR + 187-check audit trail |
| MiCA Title VI | Governance for crypto-asset services | MANDATE-BOUND certification per session |
| DORA Art. 11 | ICT continuity + auditability | Append-only hash chain, offline verifiable |
| NIST AU-2 | Audit events defined | Full per-turn attestation via BAR/CCS/CTCHC |

---

## Questions or Findings

If you discover a case where a tampered package passes verification, or any other anomaly, please document:
1. The exact mutation applied (which field, what value)
2. The verifier output (full stdout)
3. The exit code (`echo $?`)

This is exactly the kind of adversarial finding that strengthens the protocol.

---

*OMNIX QUANTUM LTD · omnixquantum.net · RFC-ATF-1 through RFC-ATF-6 published with DOI on Zenodo and Figshare*
