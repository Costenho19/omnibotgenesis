# OMNIX Decision Governance Infrastructure — Zenodo Deposit

**Title**: OMNIX: Post-Quantum Decision Governance Infrastructure for Automated Financial Systems  
**Author**: Harold Nunes — OMNIX Quantum, Abu Dhabi, UAE  
**Date**: March 2026  
**SSRN Working Paper**: 6321298 (under review)

---

## Contents of This Deposit

| File | Description |
|------|-------------|
| `omnix_technical_paper.pdf` | Full technical paper (12 sections, 6,678 words) |
| `governance_receipts_dataset.csv` | Real governance receipt dataset — 72,443 decisions with cryptographic hash chain |
| `dataset_description.md` | Column-by-column description of the dataset |
| `core_algorithms.py` | Reference implementation of key OMNIX algorithms |
| `adr_022_post_quantum_cryptography.md` | ADR-022: PQC implementation details |
| `adr_042_hybrid_kem.md` | ADR-042: Hybrid Key Encapsulation Mechanism |
| `adr_044_transparency_chain.md` | ADR-044: Quantum-Secure Transparency Chain |
| `README.md` | This file |

---

## Dataset Summary

The `governance_receipts_dataset.csv` file contains **72,443 real governance decisions** produced by the OMNIX 8-checkpoint pipeline between February 21, 2026 and March 16, 2026.

### Decision Distribution

| Decision | Count | Percentage |
|----------|-------|-----------|
| HOLD | 69,421 | 95.8% |
| BLOCK | 2,987 | 4.1% |
| APPROVED | 14 | 0.02% |
| BLOCKED | 21 | 0.03% |

### Key Properties

- **Every receipt is hash-chained**: each `content_hash` links to the previous receipt's `prev_hash`, forming an append-only cryptographic ledger
- **All decisions signed with Dilithium-3 (ML-DSA-65)**: NIST-standardized post-quantum digital signature
- **Zero data fabrication**: these are live governance decisions from the operational OMNIX system

### How to Verify Hash Chain Integrity

```python
import csv
import hashlib

with open('governance_receipts_dataset.csv') as f:
    rows = list(csv.DictReader(f))

# Verify chain linkage: each row's content_hash should appear 
# as prev_hash in the next row
chain_valid = 0
chain_broken = 0
for i in range(len(rows) - 1):
    if rows[i]['content_hash'] == rows[i+1]['prev_hash']:
        chain_valid += 1
    else:
        chain_broken += 1

print(f"Chain links verified: {chain_valid}")
print(f"Chain breaks: {chain_broken}")
```

---

## Public Receipt Verification

Any receipt in this dataset can be independently verified at:

**https://omnixquantum.net/r/{receipt_id}**

Example:
- `https://omnixquantum.net/r/OMNIX-EBC5A5719789`

The verification page shows the complete checkpoint pipeline result, cryptographic integrity status, and Dilithium-3 signature information — without requiring any credentials or system access.

---

## Reproducibility

The paper describes the full governance pipeline architecture. The `core_algorithms.py` file contains reference implementations of:

- The rolling SHA-256 Merkle chain construction
- The Monte Carlo VETO Engine decision logic
- The hybrid KEM (X25519 + Kyber-768 via HKDF) key derivation
- The Decision Contradiction Index (DCI) computation

These implementations are provided for academic reproducibility and do not constitute the full production system.

---

## License

**Creative Commons Attribution 4.0 International (CC BY 4.0)**

You are free to share, adapt, and build upon this work for any purpose, provided appropriate credit is given to the author.

---

## Citation

```bibtex
@misc{nunes2026omnix,
  author    = {Nunes, Harold},
  title     = {{OMNIX}: Post-Quantum Decision Governance Infrastructure 
               for Automated Financial Systems},
  year      = {2026},
  month     = {March},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.XXXXXXX},
  url       = {https://doi.org/10.5281/zenodo.XXXXXXX}
}
```

---

## Contact

Harold Nunes — Founder & CEO, OMNIX Quantum  
Abu Dhabi, UAE  
For correspondence regarding this deposit: [contact via SSRN Working Paper 6321298]
