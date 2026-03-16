# ADR-022: Post-Quantum Cryptography Implementation

**Status**: IMPLEMENTED  
**Date**: January 23, 2026  
**Updated**: February 28, 2026  
**Author**: Harold Nunes, OMNIX Quantum  
**Part of**: OMNIX Quantum Zenodo Deposit — DOI: 10.5281/zenodo.XXXXXXX

---

## Context

OMNIX Quantum implements post-quantum cryptography to protect governance decision audit trails against future quantum computer attacks. Decision receipts signed today must remain tamper-evident even after fault-tolerant quantum computers render classical public-key cryptography vulnerable — a property known as "harvest now, decrypt later" protection.

NIST standardized its first post-quantum algorithms in August 2024. OMNIX Quantum deployed these algorithms in production in November 2025 — not a roadmap item.

---

## Decision

**Post-quantum cryptography is fully operational** — implemented November 2025.

Two NIST-standardized algorithms are deployed:

| Component | Algorithm | NIST Standard | Purpose |
|-----------|-----------|---------------|---------|
| Digital Signatures | CRYSTALS-Dilithium-3 (ML-DSA-65) | FIPS 204 | Every governance decision is signed before storage |
| Key Encapsulation | CRYSTALS-Kyber-768 (ML-KEM-768) | FIPS 203 | Quantum-resistant key exchange for inter-service secrets |

---

## Critical Technical Distinction: KEM vs. Data Encryption

**Kyber-768 is a Key Encapsulation Mechanism (KEM) — not a data encryption algorithm.**

| Role | Correct Description | Incorrect Description |
|------|--------------------|-----------------------|
| Kyber-768 | Key encapsulation, shared secret generation, key exchange | Data encryption, payload encryption |
| Data protection | AES/Fernet symmetric encryption (bulk) | Kyber alone |

Correct architecture:
```
Kyber-768 KEM  →  establishes shared secret
                         ↓
AES/Fernet     →  encrypts actual data payload using derived key
```

Describing Kyber-768 as "data encryption" is a category error that undermines technical credibility in due diligence contexts.

---

## Key Size Reference

| Parameter | Value |
|-----------|-------|
| Kyber-768 public key | 1,184 bytes |
| Kyber-768 secret key | 2,400 bytes |
| Kyber-768 ciphertext | 1,088 bytes |
| Dilithium-3 public key | 1,952 bytes |
| Dilithium-3 secret key | 4,000 bytes |
| Dilithium-3 signature | 3,293 bytes |

---

## Security Level

Both algorithms provide NIST Level 3 security (~192-bit classical security equivalent), protecting against:
- Classical brute-force and cryptanalytic attacks
- Quantum attacks via Shor's algorithm (breaks RSA and elliptic curve)
- Quantum speedup via Grover's algorithm (symmetric key search)

The architecture is configurable to Dilithium-5 (ML-DSA-87, ~256-bit equivalent) for high-assurance or national-grade deployments via a single deployment environment variable — no code changes required.

---

## Implementation

**Module**: `omnix_core/security/pqc_security.py`  
**Library**: `pypqc >= 0.0.6.2`  
**Graceful degradation**: If `pypqc` is unavailable, all signing operations return `None`/`False` with a warning log — the system does not crash.

Every governance decision receipt includes:
- `signature`: Dilithium-3 signature over the canonical receipt hash
- `signature_algorithm`: `"Dilithium-3 (ML-DSA-65)"`
- `public_key`: The signing public key (enables independent verification)

---

## Consequences

**Positive**
- Every governance decision has cryptographic non-repudiation
- Audit trails remain tamper-evident against both classical and quantum attacks
- First-mover advantage: production PQC in governance infrastructure is rare as of 2026

**Negative**
- Larger key and signature sizes increase storage (manageable at production scale)
- Patent notices exist for Kyber cryptosystem (pypqc library displays this at startup)

---

## Related ADRs

- ADR-031: PQC Configurable Assurance Tiers (Level 3 / Level 5 via env var)
- ADR-042: Hybrid KEM (X25519 + Kyber-768 via HKDF)
- ADR-043: Crypto-Agility Layer (provider registry for algorithm swap)
- ADR-044: Quantum-Secure Decision Receipts (rolling Merkle chain + RFC 3161 timestamps)

---

## References

- [NIST Post-Quantum Cryptography Project](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [FIPS 203 — ML-KEM (Kyber)](https://csrc.nist.gov/pubs/fips/203/final)
- [FIPS 204 — ML-DSA (Dilithium)](https://csrc.nist.gov/pubs/fips/204/final)
- Mosca, M. (2018). Cybersecurity in an Era with Quantum Computers: Will We Be Ready? *IEEE Security & Privacy*, 16(5), 38–41.
