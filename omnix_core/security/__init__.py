"""
OMNIX Security Package - Post-Quantum Cryptography

Available Modules:
- PostQuantumSecurity: Real PQC using pypqc (Kyber-768, Dilithium-3)
- pqc_encryption: Simulated fallback for environments without pypqc
"""

from .pqc_security import PostQuantumSecurity

__all__ = [
    'PostQuantumSecurity'
]
