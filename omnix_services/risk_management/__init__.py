"""
OMNIX V6.2 ULTRA - Risk Management System (RMS)
================================================
Módulo institucional de gestión de riesgos con
integración de memoria Non-Markoviana.

Componentes:
- LimitsEngine: Validación pre-trade de límites (memory-enhanced)
- PositionMonitor: Monitoreo de posiciones en tiempo real (memory-enhanced)
- CircuitBreaker: Bloqueos automáticos de trading (memory-enhanced)
- AlertDispatcher: Sistema de alertas y notificaciones (predictive)
- RiskDashboard: Dashboard para inversores
- MemoryRiskAdapter: Puente entre Non-Markovian Kernel y RMS (NEW V6.2)

Creado: Nov 27, 2025
Actualizado: Nov 29, 2025 - Memory-Enhanced Risk Management V6.2
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
from omnix_services.risk_management.memory_risk_adapter import (
    MemoryRiskAdapter,
    MemoryRiskMetrics,
    MemoryRiskLevel
)

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
    'RiskDashboard',
    'MemoryRiskAdapter',
    'MemoryRiskMetrics',
    'MemoryRiskLevel'
]

__version__ = '6.2.0'
