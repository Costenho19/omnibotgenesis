# ADR-022: Post-Quantum Cryptography Implementation

**Status**: IMPLEMENTED  
**Date**: 2026-01-23  
**Updated**: 2026-02-28 (added communication rules + KEM clarification)  
**Authors**: Harold Nunes, OMNIX Team

## Context

OMNIX markets itself as an institutional-grade trading system with post-quantum cryptography protection. Investor presentations reference "PQC security" as a differentiator. There was confusion about whether PQC was actually implemented or merely a roadmap item.

A secondary issue was identified (Feb 2026): the AI bot was using internal technical labels (FIPS numbers, "NIST Level 3") in external conversations, and incorrectly describing Kyber-768 as "data encryption" rather than a key encapsulation mechanism. These have been corrected via manifest and documentation updates.

## Decision

**PQC IS FULLY IMPLEMENTED** - Not a roadmap item.

The implementation was completed in November 2025 using the NIST 2024 standardized algorithms:

| Component | Algorithm | NIST Standard | Purpose |
|-----------|-----------|---------------|---------|
| Key Encapsulation | Kyber-768 (ML-KEM-768) | FIPS 203 | Secure key exchange — establishes shared secrets resistant to quantum attacks |
| Digital Signatures | Dilithium-3 (ML-DSA-65) | FIPS 204 | Decision signing and trading order authentication |

> **Note**: FIPS numbers (FIPS 203, FIPS 204) are referenced here for internal/technical accuracy. They must NOT appear in external communications or bot responses. See Communication Rules below.

---

## Critical Technical Distinction: KEM vs. Data Encryption

**Kyber-768 is a Key Encapsulation Mechanism (KEM) — not a data encryption algorithm.**

| Term | Correct | Incorrect |
|------|---------|-----------|
| Kyber-768 role | "key encapsulation", "shared secret generation", "key exchange" | "data encryption", "secure data encryption", "payload encryption" |
| Data payload protection | AES/Fernet symmetric encryption | (PQC alone does not encrypt data) |

This distinction matters for institutional credibility: describing Kyber-768 as a "data encryption" system is a category error that signals shallow cryptographic understanding to technical due diligence reviewers.

**Correct architecture:**
```
PQC-KEM (Kyber-768) → establishes shared secret
                              ↓
Symmetric cipher (AES/Fernet) → encrypts actual data payload
```

---

## Communication Rules by Audience

The following rules govern how PQC must be described depending on who is receiving the information:

| Audience | Allowed | Prohibited |
|----------|---------|-----------|
| **External / Public** (bot responses, Telegram, website) | "NIST-standardized algorithms", "post-quantum cryptography", "quantum-resistant audit trail" | FIPS 203, FIPS 204, "NIST Level 3", algorithm names (Kyber-768, Dilithium-3) |
| **Institutional** (investors, partners, pitch docs) | Algorithm names (Dilithium-3, Kyber-768), "NIST-standardized", "operational since Nov 2025" | FIPS numbers, "NIST Level 3 security equivalent" (without qualifier) |
| **Internal** (ADRs, audits, technical data room) | Full technical detail including FIPS 203/204, NIST Level 3, key sizes | N/A — full accuracy required |

### Approved phrasing by tier

**External (bot/Telegram):**
> "OMNIX signs every governance decision with NIST-standardized post-quantum cryptographic algorithms. Every decision generates an immutable, tamper-proof cryptographic receipt."

**Institutional (investor conversations):**
> "OMNIX implements post-quantum cryptography using NIST-standardized algorithms — Kyber-768 for key exchange and Dilithium-3 for digital signatures. Operational since November 2025, not a roadmap item."

**Internal (data room, technical due diligence):**
> "CRYSTALS-Dilithium-3 (ML-DSA-65, FIPS 204) for decision signing. CRYSTALS-Kyber-768 (ML-KEM-768, FIPS 203) for key encapsulation. Both at NIST Level 3 (~192-bit classical security equivalent)."

---

## Implementation Details

### Module Location
`omnix_core/security/pqc_security.py`

### Key Capabilities

1. **Key Pair Generation**
   - Kyber-768: Public key (1184 bytes), Secret key (2400 bytes)
   - Dilithium-3: Public key (1952 bytes), Secret key (4000 bytes)

2. **Key Encapsulation (Kyber-768)**
   - `encapsulate_secret()`: Creates shared secret with ciphertext (key exchange, not data encryption)
   - `decapsulate_secret()`: Recovers shared secret from ciphertext

3. **Digital Signatures (Dilithium-3)**
   - `sign_message()`: Signs arbitrary messages
   - `verify_signature()`: Verifies signatures
   - `sign_trading_order()`: Signs trading order payloads
   - `verify_trading_order()`: Verifies trading order authenticity

4. **API Key Protection**
   - `secure_api_key()`: Uses Kyber-768 KEM + XOR encryption for API key transmission

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

> **Internal use only**: "NIST Level 3" is an internal engineering benchmark. It must not appear in external or investor-facing communications without the qualifier "internal benchmark."

### Dependencies

```
pypqc>=0.0.6.2
```

The module includes graceful degradation if pypqc is not available:
- `PQC_AVAILABLE` flag indicates library availability
- All methods return `None` or `False` when PQC unavailable
- Warning logged at startup

---

## AI Prompt Configuration

The system state manifest (`omnix_config/system_state_manifest.json`) controls how the bot discusses PQC. The manifest now includes:

- `communication_tier_rule`: explicit tiering rules for external / institutional / internal language
- `NEVER_SAY`: expanded list including FIPS 203, FIPS 204, "NIST Level 3 security equivalent", and "Kyber-768 for data encryption"
- `data_encryption_note`: clarifies that Kyber-768 is KEM, not data encryption
- `investor_explanation`: uses institutional-tier language (algorithm names, no FIPS)

---

## Investor Messaging

When asked about PQC, the AI should respond at the institutional tier:

> "OMNIX implementa criptografía post-cuántica usando algoritmos estandarizados por NIST (Kyber-768 para intercambio de claves, Dilithium-3 para firmas digitales). Esto protege el audit trail de gobernanza y las órdenes de trading contra futuros ataques de computadoras cuánticas. El módulo está operativo desde noviembre 2025, no es roadmap."

For English institutional context:

> "OMNIX implements post-quantum cryptography using NIST-standardized algorithms — Kyber-768 for key exchange and Dilithium-3 for digital signatures. Every governance decision is cryptographically signed, producing a tamper-proof audit trail. Operational since November 2025."

---

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
- Clear communication tiers prevent institutional credibility damage

### Negative
- Larger key and signature sizes (increased storage/bandwidth)
- Potential patent encumbrances
- Library dependency on pypqc

## Assurance Tier Configurability (added March 2026)

ADR-031 extends this implementation to support configurable signing levels via the `PQC_SIGNING_LEVEL` environment variable:

- **Level 3** (default, `PQC_SIGNING_LEVEL=3`): ML-DSA-65 (Dilithium-3) — enterprise baseline, current production configuration
- **Level 5** (`PQC_SIGNING_LEVEL=5`): ML-DSA-87 (Dilithium-5) — high-assurance / national-grade deployments

No architectural rewrite is required to change tiers. The selection happens at deployment startup via `omnix_core/security/pqc_config.py`. See ADR-031 for full threat model by tier and approved institutional framing.

**Approved institutional statement** (verified technically accurate as of March 2026):
> "Dilithium-3 (ML-DSA-65) is the enterprise production baseline. For high-assurance or national-grade deployments, the architecture is configurable to Dilithium-5 (ML-DSA-87) via a single deployment-environment parameter — no architectural rewrite required."

## Related ADRs

- ADR-015: Dashboard Security Enhancement
- ADR-019: Edge Confirmation Window
- ADR-020: Institutional Response Quality Standards
- ADR-031: PQC Configurable Assurance Tiers (configurable Level 3 / Level 5 via env var)

## References (Internal Use)

- [NIST Post-Quantum Cryptography](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [FIPS 203 (ML-KEM)](https://csrc.nist.gov/pubs/fips/203/final)
- [FIPS 204 (ML-DSA)](https://csrc.nist.gov/pubs/fips/204/final)
- [pypqc Documentation](https://pypi.org/project/pypqc/)
