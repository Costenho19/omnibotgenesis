# ADR-043: Crypto-Agility Layer

**Status**: Accepted  
**Date**: March 2026  
**Author**: Harold Nunes, OMNIX Architecture  
**Category**: Security Architecture  
**Related**: ADR-022, ADR-031, ADR-042, ADR-044

---

## Context

OMNIX's signing algorithm (Dilithium-3) is hardcoded in two places:
- `decision_receipt.py`: `from pqc.sign import dilithium3`
- `verification_server.py`: `from pqc.sign import dilithium3`

**The problem**: Changing the signing algorithm requires modifying source code and redeploying. Regulators (ADGM, SEC) increasingly ask: *"What is your plan if NIST recommends a different algorithm tomorrow?"*

Crypto-agility is the architectural property that allows **swapping cryptographic algorithms without code changes** — only an environment variable change and restart.

---

## Decision

Introduce a `CryptoProvider` abstract interface and a provider registry in `omnix_core/security/crypto_providers.py`.

### CryptoProvider Interface

```python
class CryptoProvider(ABC):
    def provider_id(self) -> str           # Stable ID (bound into signed payloads)
    def algorithm_name(self) -> str        # Human-readable name
    def generate_keypair() -> (bytes, bytes)
    def sign(message, secret_key) -> bytes
    def verify(signature, message, public_key) -> bool
    def serialize_public_key(pk) -> str
    def deserialize_public_key(data) -> bytes
```

### Provider Registry

| Provider ID | Algorithm | Use Case |
|-------------|-----------|----------|
| `dilithium3` | Dilithium-3 (ML-DSA-65) | Enterprise baseline (default) |
| `dilithium5` | Dilithium-5 (ML-DSA-87) | High-assurance / national-grade |
| `ed25519`    | Ed25519 (classical) | Dev/test only — NOT quantum-resistant |

### Activation

```bash
# Current (default): Dilithium-3
ACTIVE_SIGNING_PROVIDER=dilithium3

# Upgrade to Dilithium-5 (high-assurance):
ACTIVE_SIGNING_PROVIDER=dilithium5

# No code changes needed. Restart Railway service.
```

### Backward Compatibility

Old receipts (signed with dilithium3) include `"signature_algorithm": "Dilithium-3 (ML-DSA-65)"` in their payload. The verifier dispatches to the correct provider based on this field — no re-signing needed.

### Security: Algorithm Confusion Prevention

The `provider_id` is embedded into the canonical signed payload. A verifier that receives a dilithium5-signed receipt with a dilithium3 `provider_id` will reject it — preventing algorithm substitution attacks.

---

## File Structure

```
omnix_core/security/crypto_providers.py   ← New (ADR-043)
```

Existing files updated:
- `decision_receipt.py` → uses `get_active_provider()` instead of hardcoded dilithium3

---

## Consequences

### Positive
- Algorithm swap in seconds: change env var → restart → done
- Regulators can verify via `GET /api/security/agility` endpoint
- Institutional statement: "Cryptographic algorithm is deployment-configurable — no code changes required to upgrade or respond to a cryptographic advisory"
- Future-proof: add Falcon, SPHINCS+ to registry without touching existing code

### Negative / Risks
- Old receipts and new receipts coexist — verification must dispatch correctly
- `ed25519` provider must never be used in production (guarded by documentation)

---

## External Framing (Institutional Tier)

> "OMNIX implements cryptographic agility — the ability to swap signing algorithms via environment variable without modifying or redeploying application code. This means OMNIX can respond to any NIST cryptographic advisory within hours, not weeks."

---

## Alternatives Considered

1. **Manual code changes per algorithm swap** — Current state. Rejected: slow, risky, deployment dependency.
2. **Plugin system with dynamic loading** — Rejected: over-engineered, security risk from dynamic loading.
3. **Hard-code two algorithms and toggle** — Rejected: doesn't scale, requires rewrite for each new algo.

---

## Related ADRs
- ADR-022: Base PQC (Kyber-768 KEM + Dilithium signing — original hardcoded implementation)
- ADR-031: PQC Configurable Assurance Tiers (PQC_SIGNING_LEVEL — precursor to full agility)
- ADR-042: Hybrid Cryptography
- ADR-044: Quantum-Secure Decision Receipts (uses active provider for transparency log signing)
