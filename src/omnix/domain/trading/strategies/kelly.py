"""
OMNIX V7.0 Kelly Criterion Strategy
=====================================
Re-export from legacy location for backward compatibility.

Original: omnix_services/trading_service/kelly_criterion.py
Migration Status: RE-EXPORT (Phase 2 Wave 2)
"""

from omnix_services.trading_service.kelly_criterion import (
    KellyCriterionOptimizer,
    KellyCriterionOptimizer as KellyCriterion,
)

__all__ = ["KellyCriterionOptimizer", "KellyCriterion"]
