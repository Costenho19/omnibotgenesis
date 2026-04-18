# ADR-022: Post-Quantum Cryptography Implementation

**Status**: IMPLEMENTED — November 2025  
**Author**: Harold Nunes, OMNIX Quantum  
**Part of**: OMNIX Quantum Zenodo Deposit — DOI: 10.5281/zenodo.19056919  
**Related preprint**: SSRN Working Paper 6321298 (under peer review) — https://ssrn.com/abstract=6321298

---

## Context

OMNIX Quantum protects governance decision audit trails against future quantum computer attacks. Records signed today must remain tamper-evident even after fault-tolerant quantum computers render classical public-key cryptography obsolete — a threat known as "harvest now, decrypt later."

NIST standardized its first post-quantum algorithms in August 2024. OMNIX Quantum deployed these algorithms in production in November 2025.

---

## Decision

Post-quantum cryptography is **fully operational** — not a roadmap item.

Two NIST-standardized algorithms are deployed:

| Component | Algorithm | Purpose |
|-----------|-----------|---------|
| Digital Signatures | CRYSTALS-Dilithium-3 (ML-DSA-65) | Every governance decision is signed before storage |
| Key Encapsulation | CRYSTALS-Kyber-768 (ML-KEM-768) | Quantum-resistant key exchange |

**Important distinction**: Kyber-768 is a Key Encapsulation Mechanism (KEM), not a data encryption algorithm. It establishes a shared secret; actual data is protected by symmetric encryption derived from that secret.

---

## Security Level

Both algorithms are NIST-standardized and provide high security against classical and quantum attacks alike.

The architecture is configurable to Dilithium-5 (ML-DSA-87) for high-assurance deployments via a deployment parameter — no code changes required.

---

## What Each Receipt Contains

Every governance decision receipt includes:
- A Dilithium-3 digital signature over the decision payload
- The signing algorithm identifier
- The public verification key — enabling independent verification by any party

---

## Consequences

**Positive**
- Every decision has cryptographic non-repudiation
- Audit trails are tamper-evident against both classical and quantum attacks
- Operational since November 2025 — not a future commitment

**Negative**
- Larger signature sizes than classical algorithms (manageable at production scale)

---

## Related ADRs

- ADR-042: Hybrid KEM (classical + post-quantum key exchange)
- ADR-043: Crypto-Agility Layer
- ADR-044: Quantum-Secure Decision Receipts

---

## References

- [NIST Post-Quantum Cryptography Project](https://csrc.nist.gov/projects/post-quantum-cryptography)
- Mosca, M. (2018). Cybersecurity in an Era with Quantum Computers. *IEEE Security & Privacy*, 16(5), 38–41.
