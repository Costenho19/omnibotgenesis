# Quantum Computing Roadmap
## Status: Research & Development Phase
### December 2025

---

## OVERVIEW

This document outlines the quantum computing initiatives within OMNIX. These features are in R&D phase and are **not included in production trading metrics**.

---

## 1. POST-QUANTUM CRYPTOGRAPHY (Implemented)

### Current Status: Production-Ready

OMNIX implements NIST-approved post-quantum cryptographic algorithms:

| Algorithm | Standard | Use Case | Status |
|-----------|----------|----------|--------|
| Kyber-768 | FIPS-203 | Key encapsulation | Implemented |
| Dilithium-3 | FIPS-204 | Digital signatures | Implemented |

**Note:** This is cryptographic security, not quantum computing for trading decisions.

---

## 2. QRNG (Quantum Random Number Generation)

### Current Status: Experimental

Integration with ANU Quantum Random Number Service for truly random seed generation.

**Use Case:** Enhanced randomness for Monte Carlo simulations.

**Status:** Proof of concept complete, pending validation of impact on trading outcomes.

---

## 3. QAOA (Quantum Approximate Optimization Algorithm)

### Current Status: Research Phase

Exploration of D-Wave quantum annealing for portfolio optimization.

**Potential Use Case:** Solve combinatorial optimization problems in asset allocation.

**Status:** Architecture designed, integration pending.

---

## 4. VALIDATION REQUIREMENTS

Before any quantum trading features move to production:

1. **A/B Testing**
   - Classical vs quantum approach comparison
   - Measurable performance improvement required

2. **Cost-Benefit Analysis**
   - Quantum compute costs vs performance gains
   - Latency impact assessment

3. **Regulatory Review**
   - Ensure compliance with financial regulations
   - Document quantum methodology for auditors

---

## TIMELINE

| Initiative | Phase | ETA |
|------------|-------|-----|
| PQC Cryptography | Production | Complete |
| QRNG Integration | Testing | Q1 2026 |
| QAOA Portfolio | Research | Q2 2026 |

---

## NOTES

For investor presentations, focus on:
- Production-proven strategies (QuantumMomentum, Monte Carlo, etc.)
- 6-tier Coherence Engine validation
- Risk Guardian protection
- Complete audit trail

Quantum initiatives should be mentioned as "roadmap" or "R&D" items only after demonstrating proven performance.

---

*Last Updated: December 2025*
*Document Location: docs/experimental/*
