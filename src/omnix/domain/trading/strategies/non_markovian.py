"""
OMNIX V7.0 Non-Markovian Kernel Strategy
==========================================
Re-export from legacy location for backward compatibility.

Original: omnix_core/strategies/non_markovian_kernel.py
Migration Status: RE-EXPORT (Phase 2 Wave 2)
"""

from omnix_core.strategies.non_markovian_kernel import (
    NonMarkovianMemoryKernel,
    NonMarkovianMemoryKernel as NonMarkovianKernel,
)

__all__ = ["NonMarkovianMemoryKernel", "NonMarkovianKernel"]
