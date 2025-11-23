"""
OMNIX Optimization Services
Optimización, aprendizaje automático y pesos adaptativos
"""

from .adaptive_weights import AdaptiveWeightSystem, AdaptiveWeights, create_adaptive_system, interpret_regime
from .auto_learner import AutoLearningSystem
from .auto_optimizer import GeneticOptimizer, ABTestingEngine, AutoAdjustmentEngine
from .ml_module import AdvancedMLModule
from .math_helpers import MathematicalOptimizer, generate_unique_nonce

__all__ = [
    'AdaptiveWeightSystem',
    'AdaptiveWeights',
    'create_adaptive_system',
    'interpret_regime',
    'AutoLearningSystem',
    'GeneticOptimizer',
    'ABTestingEngine',
    'AutoAdjustmentEngine',
    'AdvancedMLModule',
    'MathematicalOptimizer',
    'generate_unique_nonce'
]
