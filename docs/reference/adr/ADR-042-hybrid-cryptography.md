# ADR-042: Hybrid Cryptography — Classical + Post-Quantum KEM

**Status**: Accepted  
**Date**: March 2026  
**Author**: Harold Nunes, OMNIX Architecture  
**Category**: Security Architecture  
**Related**: ADR-022 (base PQC), ADR-043 (crypto-agility), ADR-044 (receipts)

---

## Context

OMNIX already uses Kyber-768 for key encapsulation (ADR-022). This provides quantum resistance but relies entirely on a single algorithm family (CRYSTALS-Kyber/ML-KEM).

**The problem**: If a cryptographic weakness is discovered in Kyber-768 before quantum computers arrive, there is no fallback layer. Similarly, if classical channels must be protected during a key exchange, Kyber alone is not always sufficient for hybrid deployment scenarios.

NIST and the cryptographic community recommend a **hybrid approach** during the quantum transition period: use classical and post-quantum algorithms simultaneously so that security depends on **both** being broken simultaneously — which is astronomically unlikely.

---

## Decision

Implement a `HybridKEM` class in `omnix_core/security/hybrid_crypto.py` that combines:

| Component | Algorithm | Library | Role |
|-----------|-----------|---------|------|
| Classical | X25519 (ECDH) | `cryptography` stdlib | Ephemeral key exchange |
| Post-Quantum | Kyber-768 (ML-KEM-768) | `pypqc` | KEM for quantum resistance |
| Combiner | HKDF-SHA256 | `cryptography` stdlib | Derives single shared secret |

**Combined secret formula:**
```
combined_secret = HKDF(
    IKM  = kyber_secret || x25519_secret,
    info = b"OMNIX-ADR042-HybridKEM-v1",
    len  = 32 bytes
)
```

### Graceful Degradation (fail-safe)

| Situation | Mode | Behavior |
|-----------|------|----------|
| Both available | `hybrid` | Full hybrid — strongest |
| Only Kyber available | `kyber768_only` | PQC only — still quantum-resistant |
| Only X25519 available | `x25519_only` | Classical only — logs warning |
| Neither available | `None` | Logs critical — operation blocked |

### Usage

The `HybridKEM` is **additive** — it does not replace existing `sign_trading_order()` or Dilithium signing. It is used for:
- Session key establishment for sensitive inter-service communication
- Receipt packaging when encrypted transport is needed
- Future: hybrid TLS session establishment

---

## File Structure

```
omnix_core/security/hybrid_crypto.py   ← New (ADR-042)
```

---

## Consequences

### Positive
- Security requires **simultaneously breaking** both Kyber-768 AND X25519 → extremely unlikely
- Legitimate claim: "Hybrid classical + post-quantum key exchange (NIST-recommended approach)"
- Useful for institutional clients requiring hybrid TLS compliance
- Fail-safe: degrades gracefully, never crashes the pipeline

### Negative / Risks
- Additional computational overhead per key exchange (~2ms typical)
- Two libraries must be available (pypqc + cryptography)
- HKDF context label is fixed — changing it invalidates previously derived secrets

---

## External Framing (Institutional Tier)

> "OMNIX implements hybrid key exchange combining classical X25519 and post-quantum Kyber-768, deriving a combined shared secret via HKDF. Security requires breaking both algorithms simultaneously — the approach recommended by NIST for the quantum transition period. Operational since March 2026."

---

## Alternatives Considered

1. **Kyber-768 alone** — Current state. Rejected because no fallback if Kyber weakness found.
2. **P-256 instead of X25519** — Both valid; X25519 chosen for performance and simpler key serialization.
3. **Wait for NIST hybrid standard** — NIST recommendation already clear; implementation follows guidance.

---

## Related ADRs
- ADR-022: Base PQC implementation (Kyber-768 KEM + Dilithium-3 signing)
- ADR-043: Crypto-Agility Layer (provider abstraction for signing)
- ADR-044: Quantum-Secure Decision Receipts (uses hybrid for receipt transport)
