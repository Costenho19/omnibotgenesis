"""
OMNIX Security Package - Post-Quantum Cryptography V6.5.4

Available Modules:
- PostQuantumSecurity: Real PQC using pypqc (Kyber-768, Dilithium-3)
  Compliant with NIST FIPS 203 (ML-KEM) and FIPS 204 (ML-DSA)
"""

from .pqc_security import PostQuantumSecurity

__all__ = [
    'PostQuantumSecurity'
]
