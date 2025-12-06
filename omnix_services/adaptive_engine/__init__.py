"""
OMNIX ULTRA - Adaptive Parameter Engine
Sistema de Auto-Calibración Inteligente para ARES Strategies

El motor de parámetros adaptativos modula dinámicamente los parámetros
de las estrategias ARES basándose en señales del Non-Markovian Memory Kernel.

Componentes:
- AdaptiveParameterEngine: Orquestador principal
- RegimeSignalProcessor: Procesa señales del Memory Kernel
- ParameterCalibrator: Calcula ajustes de parámetros
- CooldownManager: Gestiona cooldowns entre calibraciones
- TelemetryEmitter: Logging y métricas

Autor: OMNIX Team
"""

from .adaptive_engine import (
    AdaptiveParameterEngine,
    AdaptiveParameterProfile,
    CalibrationEvent,
    RegimeType,
    get_adaptive_engine
)

__all__ = [
    'AdaptiveParameterEngine',
    'AdaptiveParameterProfile', 
    'CalibrationEvent',
    'RegimeType',
    'get_adaptive_engine'
]

__version__ = "6.5.0"
