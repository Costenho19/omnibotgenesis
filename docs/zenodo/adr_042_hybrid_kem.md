# ADR-042: Hybrid Key Encapsulation Mechanism (Classical + Post-Quantum)

**Status**: ACCEPTED — March 2026  
**Author**: Harold Nunes, OMNIX Quantum  
**Part of**: OMNIX Quantum Zenodo Deposit — DOI: 10.5281/zenodo.XXXXXXX  
**Related**: ADR-022 (base PQC), ADR-044 (receipts)

---

## Context

Relying on a single cryptographic algorithm — even a quantum-resistant one — creates a single point of failure. If a weakness is discovered in that algorithm before quantum computers arrive, there is no fallback layer.

NIST and the broader cryptographic community recommend a **hybrid approach** during the quantum transition period: combine a classical and a post-quantum algorithm so that security depends on **both** being broken simultaneously.

---

## Decision

OMNIX Quantum implements a hybrid key encapsulation mechanism combining:

| Component | Algorithm | Role |
|-----------|-----------|------|
| Classical | X25519 (ECDH) | Ephemeral classical key exchange |
| Post-Quantum | Kyber-768 (ML-KEM-768) | Post-quantum key encapsulation |
| Key Derivation | HKDF-SHA256 | Derives a single unified shared secret |

The combined shared secret is derived from both classical and post-quantum components together. Breaking the combined secret requires defeating **both algorithms simultaneously** — an astronomically unlikely event given the independence of their underlying hard problems.

---

## Graceful Degradation

The system degrades safely when components are unavailable, always logging the downgrade. It never silently falls to a weaker mode.

---

## Security Property

- Breaking X25519 requires solving the elliptic curve discrete logarithm problem
- Breaking Kyber-768 requires solving the Module Learning With Errors (MLWE) problem
- No known attack breaks both simultaneously

This is the hybrid security guarantee recommended by NIST for the post-quantum transition period.

---

## Consequences

**Positive**
- Security requires simultaneously breaking two independent hard problems
- Follows NIST transition recommendations
- Fail-safe by design — never crashes the governance pipeline

**Negative**
- Small additional computational overhead per key exchange

---

## Related ADRs

- ADR-022: Base PQC — Kyber-768 KEM + Dilithium-3 signing
- ADR-043: Crypto-Agility Layer
- ADR-044: Quantum-Secure Decision Receipts
