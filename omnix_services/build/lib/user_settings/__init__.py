"""
OMNIX V6.4 INSTITUTIONAL+ - User Settings Service
Sistema Premium de Configuración Personalizada por Usuario

Este módulo permite a cada usuario configurar OMNIX según sus preferencias:
- Perfil de riesgo (conservador, moderado, agresivo, institucional)
- Límites de trading (mínimo, máximo, diario)
- Criptomonedas permitidas
- Estrategias activas
- Sistema de auto-protección
- Notificaciones personalizadas
"""

from .user_settings_service import UserSettingsService
from .settings_models import (
    UserSettings,
    RiskProfile,
    TradingLimits,
    NotificationPreferences,
    ProtectionSettings
)

__all__ = [
    'UserSettingsService',
    'UserSettings',
    'RiskProfile',
    'TradingLimits',
    'NotificationPreferences',
    'ProtectionSettings'
]
