"""
OMNIX V6.0 ULTRA - Risk Management System (RMS)
===============================================
Módulo institucional de gestión de riesgos.

Componentes:
- LimitsEngine: Validación pre-trade de límites
- PositionMonitor: Monitoreo de posiciones en tiempo real
- CircuitBreaker: Bloqueos automáticos de trading
- AlertDispatcher: Sistema de alertas y notificaciones
- RiskDashboard: Dashboard para inversores

Creado: Nov 27, 2025
"""

from omnix_services.risk_management.risk_models import (
    RiskLimitType,
    RiskSeverity,
    RiskAction,
    RiskLimit,
    RiskBreach,
    RiskMetrics,
    RiskConfig
)
from omnix_services.risk_management.limits_engine import LimitsEngine
from omnix_services.risk_management.position_monitor import PositionMonitor
from omnix_services.risk_management.circuit_breaker import CircuitBreaker
from omnix_services.risk_management.alert_dispatcher import AlertDispatcher
from omnix_services.risk_management.risk_dashboard import RiskDashboard

__all__ = [
    'RiskLimitType',
    'RiskSeverity',
    'RiskAction',
    'RiskLimit',
    'RiskBreach',
    'RiskMetrics',
    'RiskConfig',
    'LimitsEngine',
    'PositionMonitor',
    'CircuitBreaker',
    'AlertDispatcher',
    'RiskDashboard'
]

__version__ = '1.0.0'
