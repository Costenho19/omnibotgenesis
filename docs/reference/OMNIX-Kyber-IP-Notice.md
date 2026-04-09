# OMNIX — Cryptographic IP Notice
## Kyber-768 / ML-KEM and Dilithium-3 / ML-DSA

**Document type:** Internal legal & compliance reference  
**Audience:** Engineering, legal, enterprise prospects  
**Maintained by:** Harold Nunes, OMNIX QUANTUM LTD (UK)  
**Last updated:** April 2026

---

## 1. What OMNIX uses and why

| Algorithm | Standard name | Role in OMNIX | Used for |
|-----------|--------------|---------------|----------|
| Kyber-768 | ML-KEM (FIPS 203) | Key Encapsulation Mechanism | Ephemeral session key exchange only |
| Dilithium-3 | ML-DSA (FIPS 204) | Digital signature | Signing every governance receipt |
| AES-256-GCM / Fernet | Classical | Symmetric encryption | Encrypting data at rest and in transit |

**Critical distinction:** Kyber-768 is a KEM — it is used exclusively for *key exchange*, never for encrypting governance data. All data encryption uses AES-256. Dilithium-3 signs every decision receipt.

---

## 2. Patent status — Kyber / ML-KEM

### Background
During the NIST Post-Quantum Cryptography standardization process (2016–2024), Kyber was selected as the basis for the ML-KEM standard (FIPS 203, published August 2024). Patent concerns were raised around contributions by certain submitters.

### Current status (as of April 2026)
- **NIST FIPS 203 (ML-KEM)** has been published as a final standard.
- NIST's process included IP disclosure requirements. All identified patent holders either granted royalty-free licenses or disclaimed relevant patents for use under FIPS 203.
- **Practical conclusion:** Commercial use of ML-KEM as specified in FIPS 203 carries no actionable patent risk for compliant implementations.

### OMNIX implementation
- OMNIX uses the `pypqc` library, which implements Kyber-768/ML-KEM.
- The library generates a `UserWarning` referencing historical patent concerns — this warning reflects the library's conservative stance from before FIPS 203 finalization, not a current legal risk.
- OMNIX suppresses this warning in test output (via pytest config) because it is legally resolved and creates noise in CI/CD pipelines.

### Risk assessment
| Risk | Level | Rationale |
|------|-------|-----------|
| Patent infringement (Kyber KEM) | ⬛ Negligible | NIST FIPS 203 IP disclosures resolved |
| Export control (ML-KEM) | 🟡 Low | NIST-standardized; no known restrictions for financial/governance use |
| Commercial use risk | ⬛ Negligible | ML-KEM is a public NIST standard |

---

## 3. Dilithium-3 / ML-DSA — Receipt Signing

Dilithium-3 is standardized as ML-DSA (FIPS 204, published August 2024). OMNIX uses it to sign every governance receipt.

- **No patent concerns identified** for Dilithium / ML-DSA.
- All OMNIX governance receipts carry a Dilithium-3 signature, verifiable independently.

---

## 4. External communication rules

Per OMNIX PQC Communication Tier Rules (replit.md):

| Audience | Approved language |
|----------|------------------|
| Public / bot / web | "post-quantum cryptography", "NIST-standardized algorithms" |
| Institutional / investors | "Dilithium-3", "Kyber-768", "NIST-standardized" |
| Internal / ADRs / code | All technical names permitted |

**Never use:** "FIPS 203", "FIPS 204" in external communications.

---

## 5. Fallback readiness

If, for any reason, a client requires an alternative to Kyber-768:

| Alternative | Status | Notes |
|-------------|--------|-------|
| ML-KEM (direct FIPS 203 library) | Ready | Drop-in replacement, same security level |
| X25519 (classical ECDH) | Active fallback | Already in use as part of hybrid KEM |
| Hybrid X25519 + ML-KEM | Architecture default | OMNIX uses hybrid KEM via HKDF |

OMNIX already operates a **hybrid KEM** (X25519 + Kyber-768 via HKDF), meaning even if Kyber were removed entirely, X25519 would continue providing classical security. The architecture is crypto-agile by design (ADR reference: replit.md §Security/PQC Rules).

---

## 6. Summary

> Kyber-768 is used only for key exchange (never data encryption). Its patent situation was resolved with the publication of NIST FIPS 203 in August 2024. Dilithium-3 (ML-DSA / FIPS 204) signs every governance receipt. OMNIX is crypto-agile and can swap any algorithm without system redesign.
