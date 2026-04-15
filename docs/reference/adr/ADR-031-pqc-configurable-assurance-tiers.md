# ADR-031: PQC Configurable Assurance Tiers

**Status**: ACCEPTED 
**Date**: March 3, 2026 
**Author**: Harold Nunes 
**Category**: Security Architecture / Cryptographic Posture 
**Depends on**:
- ADR-022 (Post-Quantum Cryptography Implementation — base implementation)
- ADR-028 (External Governance API — receipt signing)

---

## Context

During due diligence, a technical evaluator (Leighton) asked a legitimate architecture question:

> "You use language like 'sovereign' and 'high-assurance.' Your current signing is ML-DSA-65 (NIST Level 3). Level 3 ≠ Level 5. How do you justify the alignment between your positioning and your cryptographic level selection?"

This is a well-formed question. NIST defines five security levels for post-quantum standards:

| Level | Classical Security Equivalent | Representative Use Case |
|-------|------------------------------|------------------------|
| 1 | ~128-bit (AES-128) | Consumer / lightweight IoT |
| 2 | ~128-bit (SHA-256 collision) | General enterprise |
| **3** | **~192-bit (AES-192)** | **Capital-sensitive enterprise, governance infrastructure** |
| 4 | ~192-bit (SHA-384 collision) | High-value enterprise |
| **5** | **~256-bit (AES-256)** | **National-grade, state-secrecy, maximum assurance** |

OMNIX selected Level 3 (ML-DSA-65 / Dilithium-3) as the production baseline because:

1. **Threat model alignment**: OMNIX governs autonomous trading decisions in institutional, non-state environments. AES-192 equivalent security is the appropriate floor for capital-sensitive but non-classified operations.
2. **Performance tradeoff**: Level 5 signatures are ~40% larger and ~30% slower. For high-frequency governance evaluation (700,000+ cycles), the overhead is material.
3. **NIST guidance**: NIST explicitly designed Level 3 for enterprise-grade assurance — it is not a "minimum viable" security level; it is the primary target for institutional deployments.

However, the question surfaced a valid capability gap: **the signing level was previously hardcoded**, making it impossible to truthfully say the architecture supports higher-assurance configurations without code changes.

---

## Decision

Refactor the PQC signing layer so that the assurance tier is **deployment-context configurable** via the `PQC_SIGNING_LEVEL` environment variable, without any architectural rewrite.

### Implementation

`omnix_core/security/pqc_config.py` — new configuration module that:
- Reads `PQC_SIGNING_LEVEL` (default: `"3"`, valid values: `"3"` or `"5"`)
- Selects the appropriate Dilithium module at startup
- Fails closed: invalid values fall back to Level 3 with a logged warning
- Exposes tier metadata consumed by `PostQuantumSecurity` and all callers

`omnix_core/security/pqc_security.py` — refactored to use `pqc_config` for all signing operations. No caller API changes.

### Supported Tiers

| PQC_SIGNING_LEVEL | Algorithm | NIST Variant | Security | Use Case |
|-------------------|-----------|--------------|----------|----------|
| `3` (default) | Dilithium-3 | ML-DSA-65 | ~192-bit classical equivalent | Enterprise baseline — capital governance, institutional deployments |
| `5` | Dilithium-5 | ML-DSA-87 | ~256-bit classical equivalent | High-assurance — regulated environments, national-grade, maximum assurance |

---

## What Can Now Be Said (Communication Rules)

### Institutional Tier (investors, technical evaluators, partners)

**Approved framing:**
> "OMNIX uses Dilithium-3 (ML-DSA-65) as the enterprise production baseline — NIST Level 3, appropriate for capital-sensitive institutional environments. For high-assurance or national-grade deployments, the architecture is configurable to Dilithium-5 (ML-DSA-87, Level 5) via a single deployment-environment parameter. No architectural rewrite required. The signing module is parameterizable by design."

**Approved framing on threat model:**
> "Cryptographic level selection is threat-model driven, not a ceiling. Level 3 provides strong post-quantum security equivalent to AES-192 class assurance, which is appropriate for the environments OMNIX targets today. 'Sovereign' in OMNIX refers to structural decision authority and deterministic enforceability at the execution boundary — cryptographic level scales with deployment context."

### What Is Prohibited (NEVER SAY)

| Prohibited Statement | Why |
|----------------------|-----|
| "We support dynamic runtime swap between Level 3 and Level 5" | Level is set at deployment startup, not changed mid-operation |
| "Level 5 is already active in production" | Production uses Level 3 (ML-DSA-65) |
| "Configurable in real-time" | Configuration is a deployment-time variable, not a runtime toggle |
| "Level 3 is just our minimum" | Level 3 is the designed enterprise baseline, not a floor |

---

## Threat Model by Tier

### Level 3 — Enterprise Baseline (current production)

**Appropriate for:**
- Institutional trading governance
- B2B decision infrastructure (financial services, supply chain, lending)
- Regulatory compliance contexts (ADGM, SEC-adjacent)
- Environments where decision integrity and audit trail immutability are the primary security concerns

**Security posture:**
- ~192-bit classical security equivalent
- Resists both classical and quantum attacks (Shor's algorithm, Grover's algorithm)
- Signature size ~3,309 bytes — viable at 700,000+ daily governance evaluations

### Level 5 — High-Assurance Configuration

**Appropriate for:**
- National government deployments
- Military / intelligence-adjacent environments
- Contexts requiring state-secrecy-grade cryptographic assurance
- Maximum regulatory assurance requirements

**Security posture:**
- ~256-bit classical security equivalent
- ~40% larger signature overhead (~4,627 bytes)
- Activated via `PQC_SIGNING_LEVEL=5` in deployment environment

---

## Consequences

### Positive
- Harold can truthfully state "the architecture supports ML-DSA-87 (Level 5) via deployment configuration" — now technically accurate
- No regression: existing receipts, behavior, and callers unchanged
- Fail-closed design: invalid config defaults to Level 3, never degrades silently to no-signing
- `get_security_info()` now returns full tier documentation for technical due diligence
- Demonstrates architectural maturity: security posture designed for multiple deployment contexts

### Negative
- None. Dilithium-5 library (`pqc.sign.dilithium5`) is already present in the pypqc package
- The refactor is additive — no breaking changes

---

## Related ADRs

- **ADR-022** — Base PQC implementation (Dilithium-3, Kyber-768, communication tier rules)
- **ADR-028** — External Governance API (PQC-signed receipts)
- **ADR-029** — Governance Compliance Modules (human oversight overrides signed with Dilithium-3)

---

## References (Internal)

- NIST FIPS 204 — ML-DSA (Dilithium) standard, all levels
- `omnix_core/security/pqc_config.py` — tier configuration module
- `omnix_core/security/pqc_security.py` — refactored signing module
