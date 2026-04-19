# INVENTORSHIP MEMO — FAMILY 11
## OMNIX-PAT-2026-011

**Invention:** Crypto-Agility Provider Architecture + Hybrid KEM
**Inventor:** Harold Alberto Nunes Rodelo — April 19, 2026

## INVENTIVE CONTRIBUTIONS

1. **Crypto-Agility Provider Interface:** Design of the uniform CryptoProvider abstract interface that decouples governance pipeline components from specific signing algorithms — enabling configuration-driven algorithm substitution without code changes.

2. **Algorithm-Bound Receipt Signing:** Design of the security mechanism that embeds the provider_id within the signed payload before signing — preventing algorithm substitution attacks where a valid PQC signature is replaced with a forged classical signature.

3. **Provider Registry with Backward Verification:** Design of the registry architecture that retains all historical providers, enabling correct verification of receipts signed under any previously active algorithm.

4. **Hybrid KEM HKDF Combination:** Design of the HKDF(kyber_secret || ecdh_secret) combination scheme that provides mutual security guarantees from two independent cryptographic assumptions.

5. **Four-Tier Fail-Safe Degradation:** Design of the HYBRID → KYBER_ONLY → ECDH_ONLY → NONE degradation hierarchy with mode binding in key bundle metadata.

6. **Protocol Label Binding in HKDF:** Use of the "OMNIX-ADR042-HybridKEM-v1" info label to prevent cross-protocol attacks on the derived combined secret.

## REDUCTION TO PRACTICE
- `omnix_core/security/crypto_providers.py` (ADR-043) — operational March 2026
- `omnix_core/security/hybrid_crypto.py` (ADR-042) — operational March 2026
Git hashes: [RETRIEVE BEFORE FILING]
