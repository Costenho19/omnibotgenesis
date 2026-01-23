# ADR-022: Post-Quantum Cryptography Implementation

**Status**: IMPLEMENTED  
**Date**: 2026-01-23  
**Authors**: Harold Nunes, OMNIX Team

## Context

OMNIX markets itself as an institutional-grade trading system with post-quantum cryptography protection. Investor presentations reference "PQC security" as a differentiator. There was confusion about whether PQC was actually implemented or merely a roadmap item.

## Decision

**PQC IS FULLY IMPLEMENTED** - Not a roadmap item.

The implementation was completed in November 2025 using the NIST 2024 standardized algorithms:

| Component | Algorithm | NIST Standard | Purpose |
|-----------|-----------|---------------|---------|
| Key Encapsulation | Kyber-768 (ML-KEM-768) | FIPS 203 | Secure key exchange resistant to quantum attacks |
| Digital Signatures | Dilithium-3 (ML-DSA-65) | FIPS 204 | Trading order authentication |

## Implementation Details

### Module Location
`omnix_core/security/pqc_security.py`

### Key Capabilities

1. **Key Pair Generation**
   - Kyber-768: Public key (1184 bytes), Secret key (2400 bytes)
   - Dilithium-3: Public key (1952 bytes), Secret key (4000 bytes)

2. **Key Encapsulation (Kyber-768)**
   - `encapsulate_secret()`: Creates shared secret with ciphertext
   - `decapsulate_secret()`: Recovers shared secret from ciphertext

3. **Digital Signatures (Dilithium-3)**
   - `sign_message()`: Signs arbitrary messages
   - `verify_signature()`: Verifies signatures
   - `sign_trading_order()`: Signs trading order payloads
   - `verify_trading_order()`: Verifies trading order authenticity

4. **API Key Protection**
   - `secure_api_key()`: Encrypts API keys for secure transmission

### Trading Order Integration

As of ADR-022, all real trading orders are signed with Dilithium-3 before execution:

```python
# In trading_system.py execute_real_trade()
order_data_for_signature = {
    'symbol': current_pair,
    'type': side.lower(),
    'amount': crypto_amount,
    'amount_usd': amount_usd,
    'price': current_price,
    'timestamp': datetime.now().isoformat(),
    'user_id': str(user_id)
}
pqc_signature = self.sign_trading_order_pqc(order_data_for_signature)
```

Trade results now include:
- `pqc_signed`: Boolean indicating if order was cryptographically signed
- `pqc_algorithm`: "Dilithium-3 (ML-DSA-65)" when signed

### Security Level

Both algorithms provide NIST Level 3 security (~192-bit classical security equivalent), protecting against:
- Classical brute-force attacks
- Future quantum computer attacks (Shor's algorithm, Grover's algorithm)

### Dependencies

```
pypqc>=0.0.6.2
```

The module includes graceful degradation if pypqc is not available:
- `PQC_AVAILABLE` flag indicates library availability
- All methods return `None` or `False` when PQC unavailable
- Warning logged at startup

## AI Prompt Updates

The system state manifest (`omnix_config/system_state_manifest.json`) now includes:

```json
"post_quantum_cryptography": {
    "status": "IMPLEMENTED",
    "CRITICAL_FACT": "PQC YA ESTÁ IMPLEMENTADO - NO está en roadmap",
    "NEVER_SAY": [
        "PQC está en roadmap",
        "PQC planificado para Q3 2026",
        "Seguridad cuántica no implementada"
    ]
}
```

This prevents the AI from incorrectly stating PQC is a future feature.

## Investor Messaging

When asked about PQC, the AI should respond with:

> "OMNIX implementa criptografía post-cuántica usando los estándares NIST 2024 (Kyber-768 para encriptación, Dilithium-3 para firmas digitales). Esto protege las comunicaciones y órdenes de trading contra futuros ataques de computadoras cuánticas. El módulo está operativo desde noviembre 2025."

## Patent Notice

The Kyber cryptosystem may be protected under patents (FR2956541A1/US9094189B2/EP2537284B1, US9246675/EP2837128B1). The pypqc library displays this warning. For production use, consider legal review.

## Alternatives Considered

1. **Wait for NIST final standards (2026)**: Rejected - Standards were finalized in August 2024
2. **Use liboqs instead of pypqc**: Could be explored for performance
3. **Hybrid classical+PQC**: Not implemented but could be added

## Consequences

### Positive
- Legitimate claim to "post-quantum security" in investor presentations
- Protection against future quantum threats
- Audit trail for signed trading orders
- Differentiator from competitors

### Negative
- Larger key and signature sizes (increased storage/bandwidth)
- Potential patent encumbrances
- Library dependency on pypqc

## Related ADRs

- ADR-015: Dashboard Security Enhancement
- ADR-019: Edge Confirmation Window
- ADR-020: Institutional Response Quality Standards

## References

- [NIST Post-Quantum Cryptography](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [FIPS 203 (ML-KEM)](https://csrc.nist.gov/pubs/fips/203/final)
- [FIPS 204 (ML-DSA)](https://csrc.nist.gov/pubs/fips/204/final)
- [pypqc Documentation](https://pypi.org/project/pypqc/)
