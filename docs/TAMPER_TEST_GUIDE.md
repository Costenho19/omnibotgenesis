# OMNIX QUANTUM — Independent Tamper-Test Guide

**For:** External auditors, regulators, and technical reviewers  
**Subject:** OMNIX-RTE-001 v1.4.0 Evidence Package — cryptographic integrity verification  
**No OMNIX account required. No API key required. Zero trust assumptions.**

---

## The scenario this covers

| Field | Value |
|---|---|
| **Scenario** | QuantumBank AI Trading Desk — USD 50,000,000 cross-border transfer |
| **Route** | SWIFT MT202 / XRPL RLUSD |
| **Session** | `SESSION-B9199C8CC9394304` |
| **GCFR** | `GCFR-96D8BA6CA0FF4295` — Governance Contract sealed ML-DSA-65 before Turn 0 |
| **Verdict** | `HALT PROVEN` |
| **Mandate certification** | `MANDATE-BOUND` |
| **Admission result** | `FULL ADMISSION` |
| **PQC certificate** | `POGC-GENESIS-E071CC96` |
| **Checks** | 187 (148 base + 36 IPFL intake + 3 PKG-INTAKE) |
| **Regulatory coverage** | EU AI Act Art. 9/11 · MiCA Title VI · DORA Art. 11 · NIST AU-2 |

---

## What this proves

This guide lets any technically capable reviewer independently verify that:

1. An OMNIX governance evidence package is cryptographically intact (exit code 0)
2. Any modification to the package — even a single byte — is immediately detected (exit code 1)
3. The detection uses **ML-DSA-65 (Dilithium-3, FIPS 204)** post-quantum signatures, not HMAC or SHA alone
4. The HALT PROVEN verdict and MANDATE-BOUND certification cannot be silently changed

The package used in this guide covers a real governance scenario:  
**Session `SESSION-B9199C8CC9394304` · GCFR `GCFR-96D8BA6CA0FF4295` · 187 checks · exit 0 (clean) / exit 1 (tampered)**  
Package ID: `OMNIX-RTE-001-2824C7A71045465E`

---

## Step 1 — Requirements

You need Python 3.8+ and one library:

```bash
pip install oqs-python
```

`oqs-python` provides the ML-DSA-65 (Dilithium-3) post-quantum signature primitives used to verify all cryptographic seals in the package. No other OMNIX software is needed.

**Verify the install:**

```bash
python3 -c "import oqs; print('oqs-python OK, version:', oqs.__version__)"
```

Expected output:
```
oqs-python OK, version: 0.10.0
```

---

## Step 2 — Get the package

Clone or download the OMNIX QUANTUM repository. The evidence package is at:

```
evidence_packages/OMNIX-RTE-001_20260531_051950.json
```

The verifier script is at:

```
scripts/verify_treasury_execution_trace.py
```

Both files are self-contained. The verifier reads the embedded public key (`pqc.public_key_b64`) directly from the JSON — no external key material required.

---

## Step 3 — Verify clean (expected: exit code 0)

Run the verifier against the unmodified package:

```bash
python3 scripts/verify_treasury_execution_trace.py \
    evidence_packages/OMNIX-RTE-001_20260531_051950.json
```

**Expected output (last section):**

```
═════════════════════════════════════════════════════════════════
  OMNIX-RTE-001 VERIFICATION REPORT
  Package:  OMNIX-RTE-001-2824C7A71045465E
  Mode:     FULL
  Time:     2026-05-31T...
─────────────────────────────────────────────────────────────────
  TOTAL CHECKS : 187
  PASSED        : 185
  FAILED        : 0
  SKIPPED       : 0
  WARNINGS      : 2 (non-blocking — see DR-TTL checks)
─────────────────────────────────────────────────────────────────
  VERDICT: ALL VERIFICATIONS PASS — 2 non-blocking warning(s)
═════════════════════════════════════════════════════════════════
```

**What this means:** 187 integrity checks across three execution paths (DANGEROUS · ADMISSIBLE · INTERRUPTED) all pass. The 2 warnings are non-blocking DR timestamp TTL notices — they do not affect the cryptographic integrity result.

**Confirm exit code:**

```bash
echo "Exit code: $?"
```

Expected: `Exit code: 0`

---

## Step 4 — Tamper the package

Use any of these three Python one-liners to introduce a controlled mutation. Each targets a different layer of the governance proof chain.

### Variant A — Mutate the GCFR seal hash

This modifies the Governance Contract Formation Record seal — the foundational pre-execution contract.

```bash
python3 - <<'EOF'
import json

with open("evidence_packages/OMNIX-RTE-001_20260531_051950.json") as f:
    d = json.load(f)

original = d["paths"]["path_admissible"]["steps"]["0_intake"]["intake_seal"]["seal_hash"]
d["paths"]["path_admissible"]["steps"]["0_intake"]["intake_seal"]["seal_hash"] = "TAMPERED_" + original[9:]

with open("/tmp/omnix_tampered.json", "w") as f:
    json.dump(d, f)

print("Tampered package written to /tmp/omnix_tampered.json")
print(f"Original seal_hash prefix:  {original[:32]}...")
print(f"Tampered seal_hash prefix:  TAMPERED_{original[9:32]}...")
EOF
```

### Variant B — Mutate the PQC signature

This replaces the ML-DSA-65 post-quantum signature of the GCFR intake seal.

```bash
python3 - <<'EOF'
import json

with open("evidence_packages/OMNIX-RTE-001_20260531_051950.json") as f:
    d = json.load(f)

original = d["paths"]["path_admissible"]["steps"]["0_intake"]["intake_seal"]["pqc_signature"]
d["paths"]["path_admissible"]["steps"]["0_intake"]["intake_seal"]["pqc_signature"] = \
    "TAMPERED_SIGNATURE_" + original[19:]

with open("/tmp/omnix_tampered.json", "w") as f:
    json.dump(d, f)

print("Tampered package written to /tmp/omnix_tampered.json")
EOF
```

### Variant C — Mutate a downstream hash (delegation receipt)

This modifies the content hash of the Delegation Receipt — a step that occurs after the intake gate.

```bash
python3 - <<'EOF'
import json

with open("evidence_packages/OMNIX-RTE-001_20260531_051950.json") as f:
    d = json.load(f)

d["paths"]["path_admissible"]["steps"]["2_authority"]["delegation_receipt"]["content_hash"] = \
    "000000deadbeef0000000000000000000000000000000000"

with open("/tmp/omnix_tampered.json", "w") as f:
    json.dump(d, f)

print("Tampered package written to /tmp/omnix_tampered.json")
EOF
```

---

## Step 5 — Verify tampered (expected: exit code 1)

Run the same verifier against the tampered file:

```bash
python3 scripts/verify_treasury_execution_trace.py /tmp/omnix_tampered.json
```

**Expected output for Variant A (seal_hash mutation):**

```
  ✗ [INT-ADM-GCFR-HASH] [ADMISSIBLE] GCFR seal_hash = SHA3-256(iad|sar|mfr|cps|fps) (IPFL-INV-007)
  ✗ [INT-ADM-GCFR-SIG]  [ADMISSIBLE] GCFR intake_seal PQC signature (ML-DSA-65)

─────────────────────────────────────────────────────────────────
  TOTAL CHECKS : 187
  PASSED        : 183
  FAILED        : 2
─────────────────────────────────────────────────────────────────
  VERDICT: 2 VERIFICATION(S) FAILED — package integrity compromised
```

**Expected output for Variant B (PQC signature mutation):**

```
  ✗ [INT-ADM-GCFR-SIG]  [ADMISSIBLE] GCFR intake_seal PQC signature (ML-DSA-65)

─────────────────────────────────────────────────────────────────
  TOTAL CHECKS : 187
  PASSED        : 184
  FAILED        : 1
─────────────────────────────────────────────────────────────────
  VERDICT: 1 VERIFICATION(S) FAILED — package integrity compromised
```

**Expected output for Variant C (delegation receipt hash):**

```
  ✗ [DR-ADM-HASH] [ADMISSIBLE] DR content_hash integrity
  ✗ [DR-ADM-SIG]  [ADMISSIBLE] DR PQC signature (ML-DSA-65)

─────────────────────────────────────────────────────────────────
  TOTAL CHECKS : 187
  PASSED        : 182
  FAILED        : 3
─────────────────────────────────────────────────────────────────
  VERDICT: 3 VERIFICATION(S) FAILED — package integrity compromised
```

**Confirm exit code:**

```bash
echo "Exit code: $?"
```

Expected: `Exit code: 1`

---

## What each check code means

| Check code | Layer | What it verifies |
|---|---|---|
| `INT-ADM-GCFR-HASH` | IPFL · ADR-204 | GCFR seal_hash = SHA3-256 of 5 predicate hashes |
| `INT-ADM-GCFR-SIG` | IPFL · ADR-204 | ML-DSA-65 signature of GCFR intake seal |
| `INT-ADM-IAD-HASH` | IPFL · IPFL-INV-001 | Intake Authority Declaration hash |
| `INT-ADM-SAR-HASH` | IPFL · IPFL-INV-002 | Scope Authorization Record hash |
| `INT-ADM-MFR-HASH` | IPFL · IPFL-INV-003 | Mandate Formation Record hash |
| `DR-ADM-HASH` | ATF · RFC-ATF-1 | Delegation Receipt content hash |
| `DR-ADM-SIG` | ATF · RFC-ATF-1 | Delegation Receipt ML-DSA-65 signature |

All 187 checks, their invariant references (RFC-ATF-1 through RFC-ATF-6, ADR-201 through ADR-204), and the three execution paths (DANGEROUS · ADMISSIBLE · INTERRUPTED) are documented in:

- `docs/adr/ADR-201-rte-001-evidence-package.md`
- `docs/adr/ADR-204-intake-predicate-formation-layer.md`
- `docs/standards/RFC-ATF-1.md` through `RFC-ATF-6.md`

---

## Machine-readable output

For automated CI or regulatory reporting pipelines, use `--json`:

```bash
python3 scripts/verify_treasury_execution_trace.py \
    evidence_packages/OMNIX-RTE-001_20260531_051950.json \
    --json
```

Returns a JSON object with `verdict`, `total_checks`, `passed`, `failed`, and per-check results. Exit code is always 0 (clean) or 1 (tampered/failed).

---

## Why ML-DSA-65

ML-DSA-65 (formerly Dilithium-3) is FIPS 204 standardized by NIST in August 2024. It provides:

- **Post-quantum security**: resistant to Shor's algorithm and Grover's attacks
- **Deterministic signing**: same key + payload always produces the same signature
- **Offline verification**: the public key is embedded in the package — no network call, no OMNIX server, no trust anchor beyond the key itself

The public key embedded in `pqc.public_key_b64` is the same key OMNIX QUANTUM uses to sign all governance receipts in production. Independent reviewers can pin this key and verify all future packages without any OMNIX involvement.

---

*OMNIX QUANTUM LTD · RFC-ATF-1 through RFC-ATF-6 · ADR-186/187/200/201/204*  
*Proof of Governance Registry: https://omnixquantum.net/pogr/verify/POGC-GENESIS-E071CC96*
