# ADR-042: Hybrid Key Encapsulation Mechanism (Classical + Post-Quantum)

**Status**: ACCEPTED — Implemented March 2026  
**Author**: Harold Nunes, OMNIX Quantum  
**Part of**: OMNIX Quantum Zenodo Deposit — DOI: 10.5281/zenodo.XXXXXXX  
**Related**: ADR-022 (base PQC), ADR-043 (crypto-agility), ADR-044 (receipts)

---

## Context

OMNIX Quantum already uses Kyber-768 for key encapsulation (ADR-022). This provides quantum resistance but relies on a single algorithm family. The cryptographic community and NIST both recommend a **hybrid approach** during the quantum transition period: combine a classical and a post-quantum algorithm so that security requires breaking **both simultaneously** — an astronomically unlikely event.

---

## Decision

Implement a `HybridKEM` combining X25519 (classical) and Kyber-768 (post-quantum), deriving a unified shared secret via HKDF-SHA256.

### Algorithm Components

| Component | Algorithm | Role |
|-----------|-----------|------|
| Classical | X25519 (ECDH) | Ephemeral classical key exchange |
| Post-Quantum | Kyber-768 (ML-KEM-768) | Post-quantum key encapsulation |
| Key Derivation | HKDF-SHA256 | Derives single 32-byte shared secret |

### Combined Secret Formula

```
shared_secret = HKDF-SHA256(
    IKM   = kyber_shared_secret || x25519_shared_secret,
    info  = b"OMNIX-ADR042-HybridKEM-v1",
    length = 32 bytes
)
```

The domain separation label (`OMNIX-ADR042-HybridKEM-v1`) cryptographically binds the derived key to this specific application context, preventing cross-protocol attacks.

### Step-by-Step Encapsulation

```
Input:  Recipient public keys (pk_kyber, pk_x25519)
Output: Ciphertext bundle (ct_kyber, eph_x25519_pub), shared_secret

1.  (ct_kyber, secret_kyber)    ← Kyber768.encapsulate(pk_kyber)
2.  (eph_priv, eph_pub)         ← X25519.generate_keypair()
3.  secret_x25519               ← X25519.exchange(eph_priv, pk_x25519)
4.  composite                   ← secret_kyber || secret_x25519
5.  shared_secret               ← HKDF-SHA256(ikm=composite, info=label, len=32)
6.  Return (ct_kyber, eph_pub), shared_secret
```

### Graceful Degradation Policy

| Condition | Mode | Security |
|-----------|------|----------|
| Both libraries available | `hybrid` | Classical + PQC — strongest |
| Only Kyber available | `kyber768_only` | PQC only — quantum-resistant |
| Only X25519 available | `x25519_only` | Classical only — warning logged |
| Neither available | `none` | Operation blocked — critical log |

The system never silently falls back to a weaker mode without logging the downgrade. The degradation chain is: `hybrid → kyber768_only → x25519_only`.

---

## Key Sizes (Kyber-768)

| Parameter | Size |
|-----------|------|
| Public key | 1,184 bytes |
| Secret key | 2,400 bytes |
| Ciphertext | 1,088 bytes |
| Shared secret output | 32 bytes (after HKDF) |

---

## Usage Scope

The Hybrid KEM is used for:
- Session key establishment for sensitive inter-service communication
- Receipt packaging when encrypted transport is required
- B2B External Governance API: client payload encryption at rest

It is **additive** to the existing Dilithium-3 signing layer — it does not replace decision signing.

---

## Security Property

Breaking the combined shared secret requires **simultaneously** breaking both:
- X25519: requires solving the elliptic curve discrete logarithm problem (classically hard)
- Kyber-768: requires solving the Module Learning With Errors (MLWE) problem (quantum-hard)

No known attack breaks both simultaneously. This is the hybrid security guarantee.

---

## Implementation

**Module**: `omnix_core/security/hybrid_crypto.py`  
**Dependencies**: `pypqc >= 0.0.6.2`, `cryptography >= 41.0`

---

## Consequences

**Positive**
- Security requires breaking two independent hard problems simultaneously
- Legitimate claim: "Hybrid classical + post-quantum KEM following NIST transition recommendations"
- Fail-safe: graceful degradation never crashes the governance pipeline

**Negative**
- ~2ms additional overhead per key exchange (acceptable)
- HKDF label is fixed — changing it invalidates previously derived secrets (migration needed if updated)

---

## Related ADRs

- ADR-022: Base PQC — Kyber-768 KEM + Dilithium-3 signing
- ADR-043: Crypto-Agility Layer — provider abstraction for signing algorithms
- ADR-044: Quantum-Secure Decision Receipts — uses this KEM for receipt transport
