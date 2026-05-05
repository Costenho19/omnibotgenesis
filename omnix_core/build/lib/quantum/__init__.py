"""
OMNIX V6.0 ULTRA - Quantum Enhancements Package
Exports QRNG, QAOA, D-Wave, Physics Validator, Testing Framework, and Confidence System

QUANTUM REAL:
- ANU QRNG: True quantum randomness from Australian National University
- D-Wave Leap: Real quantum annealing for portfolio optimization
"""

from omnix_core.quantum.enhancements import (
    global_qrng,
    global_qaoa,
    get_quantum_random,
    optimize_portfolio_quantum,
    get_quantum_stats,
    QuantumRandomNumberGenerator,
    QuantumPortfolioOptimizer
)

from omnix_core.quantum.physics_validator import (
    quantum_physics_validator,
    response_confidence,
    generate_quantum_response,
    get_quantum_physics_context,
    add_quantum_footer,
    QuantumPhysicsValidator,
    ResponseConfidence
)

from omnix_core.quantum.testing_framework import (
    global_testing_framework,
    QuantumTestingFramework,
    TestCase,
    TestResult
)

from omnix_core.quantum.dwave_qaoa import (
    DWavePortfolioOptimizer,
    QuantumOptimizationResult,
    DWAVE_AVAILABLE
)

__all__ = [
    'global_qrng',
    'global_qaoa',
    'get_quantum_random',
    'optimize_portfolio_quantum',
    'get_quantum_stats',
    'QuantumRandomNumberGenerator',
    'QuantumPortfolioOptimizer',
    'quantum_physics_validator',
    'response_confidence',
    'generate_quantum_response',
    'get_quantum_physics_context',
    'add_quantum_footer',
    'QuantumPhysicsValidator',
    'ResponseConfidence',
    'global_testing_framework',
    'QuantumTestingFramework',
    'TestCase',
    'TestResult',
    'DWavePortfolioOptimizer',
    'QuantumOptimizationResult',
    'DWAVE_AVAILABLE'
]
