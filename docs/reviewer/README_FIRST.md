# OMNIX-RTE-001 — Reviewer Package

**Runtime Treasury Execution Trace**
Autonomous governance evidence for a $50,000,000 cross-border liquidity release.
SWIFT MT202 / XRPL RLUSD — Dilithium-3 (ML-DSA-65, FIPS 204)

---

## What this package contains

A cryptographically verifiable dual-path execution trace showing:

- **PATH DANGEROUS** — An autonomous treasury agent with degraded authority
  attempted a $50M transfer. Governance halted it. The halt is proven
  cryptographically. No execution occurred.

- **PATH ADMISSIBLE** — The same agent, recertified, executed the same transfer
  under valid authority. Settlement was released. The execution is proven
  cryptographically.

Both paths share the same governance stack, the same PQC keypair, and the same
verification procedure. The verifier requires no OMNIX platform access.

---

## Verification time: under 2 minutes

**Requirements:** Python 3.9+

```
pip install pqc        # Dilithium-3 PQC verification (one-time, ~5 seconds)
python verify.py
```

Expected output with `pqc` installed (111 checks, 0 failures):

```
  TOTAL CHECKS : 111
  PASSED        : 111
  FAILED        : 0
  VERDICT: ALL VERIFICATIONS PASS — package integrity confirmed
```

Without `pip install pqc`: the 26 PQC signature checks are SKIPPED (not FAILED).
All 75 structural and hash integrity checks run and pass regardless.

See `VERIFY.md` for targeted verification commands and expected outputs.

---

## The anchor artifact

**Proof of Governance Certificate**

```
ID:         POGC-F1DC0218E5204875
Tier:       MANDATE-BOUND
PQC:        ML-DSA-65 (Dilithium-3, FIPS 204)
Settlement: USD 50,000,000
SWIFT ref:  MT202-2CAA8C200950
XRPL tx:    XRPL-8F7967D6A3A04ECC8C27CD0C
```

This certificate is embedded in the package and PQC-signed with the ephemeral
keypair whose public key is also embedded. It can be verified without any
external reference, network access, or OMNIX infrastructure.

---

## Package contents

```
OMNIX-RTE-001-REVIEWER/
├── README_FIRST.md       — this file
├── VERIFY.md             — verification commands and expected outputs
├── QUICKSTART.md         — step-by-step for first-time reviewers
├── verify.py             — standalone verifier (Python 3.9+, pip install pqc)
└── evidence/
    ├── OMNIX-RTE-001_*.json   — complete evidence package (194 KB)
    └── OMNIX-RTE-001_*.pdf    — institutional document (15 pages)
```

---

## Standard

RFC-ATF-1 through RFC-ATF-6 · ADR-201
OMNIX QUANTUM LTD — Harold Nunes
