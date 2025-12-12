"""
OMNIX V7.0 Kalman Filter Strategy
===================================
Re-export from legacy location for backward compatibility.

Original: omnix_services/trading_service/kalman_filter.py
Migration Status: RE-EXPORT (Phase 2 Wave 2)
"""

from omnix_services.trading_service.kalman_filter import (
    KalmanFilterPredictor,
    KalmanFilterPredictor as KalmanFilter,
)

__all__ = ["KalmanFilterPredictor", "KalmanFilter"]
