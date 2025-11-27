"""
OMNIX V6.0 ULTRA - Risk Management Models
==========================================
DTOs, Enums y configuraciones para el sistema RMS.

Creado: Nov 27, 2025
"""

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class RiskLimitType(Enum):
    """Tipos de límites de riesgo soportados"""
    PER_TRADE = 'per_trade'
    DAILY_LOSS = 'daily_loss'
    MAX_DRAWDOWN = 'max_drawdown'
    PORTFOLIO_CONCENTRATION = 'portfolio_concentration'
    VOLATILITY = 'volatility'
    DAILY_TRADES = 'daily_trades'
    OPEN_POSITIONS = 'open_positions'


class RiskSeverity(Enum):
    """Niveles de severidad de alertas"""
    INFO = 'info'
    WARNING = 'warning'
    CRITICAL = 'critical'
    HALT = 'halt'


class RiskAction(Enum):
    """Acciones tomadas por el sistema de riesgo"""
    NONE = 'none'
    ALERT_SENT = 'alert_sent'
    ORDER_REJECTED = 'order_rejected'
    POSITION_REDUCED = 'position_reduced'
    TRADING_HALTED = 'trading_halted'
    MANUAL_OVERRIDE = 'manual_override'


class ThresholdUnit(Enum):
    """Unidades para umbrales de límites"""
    USD = 'USD'
    PERCENT = 'PERCENT'
    RATIO = 'RATIO'
    COUNT = 'COUNT'


@dataclass
class RiskLimit:
    """Configuración de un límite de riesgo"""
    id: Optional[int] = None
    user_id: str = 'default'
    limit_type: RiskLimitType = RiskLimitType.PER_TRADE
    threshold_value: float = 0.0
    threshold_unit: ThresholdUnit = ThresholdUnit.USD
    warning_threshold_pct: float = 80.0
    is_active: bool = True
    cooldown_minutes: int = 60
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'limit_type': self.limit_type.value,
            'threshold_value': self.threshold_value,
            'threshold_unit': self.threshold_unit.value,
            'warning_threshold_pct': self.warning_threshold_pct,
            'is_active': self.is_active,
            'cooldown_minutes': self.cooldown_minutes
        }


@dataclass
class RiskBreach:
    """Registro de una violación de límite"""
    id: Optional[int] = None
    user_id: str = 'default'
    limit_id: Optional[int] = None
    limit_type: RiskLimitType = RiskLimitType.PER_TRADE
    severity: RiskSeverity = RiskSeverity.WARNING
    current_value: float = 0.0
    threshold_value: float = 0.0
    percentage_used: float = 0.0
    action_taken: RiskAction = RiskAction.NONE
    description: str = ''
    metadata: Optional[Dict] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'limit_id': self.limit_id,
            'limit_type': self.limit_type.value,
            'severity': self.severity.value,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'percentage_used': self.percentage_used,
            'action_taken': self.action_taken.value,
            'description': self.description,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class RiskMetrics:
    """Métricas de riesgo en un momento dado"""
    user_id: str = 'default'
    snapshot_date: Optional[datetime] = None
    total_balance_usd: float = 0.0
    total_exposure_usd: float = 0.0
    available_balance_usd: float = 0.0
    daily_pnl_usd: float = 0.0
    daily_pnl_pct: float = 0.0
    max_drawdown_usd: float = 0.0
    max_drawdown_pct: float = 0.0
    current_drawdown_pct: float = 0.0
    max_single_position_pct: float = 0.0
    open_positions: int = 0
    daily_trades_count: int = 0
    volatility_index: float = 0.0
    risk_score: int = 0
    positions_breakdown: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'total_balance_usd': self.total_balance_usd,
            'total_exposure_usd': self.total_exposure_usd,
            'available_balance_usd': self.available_balance_usd,
            'daily_pnl_usd': self.daily_pnl_usd,
            'daily_pnl_pct': self.daily_pnl_pct,
            'max_drawdown_usd': self.max_drawdown_usd,
            'max_drawdown_pct': self.max_drawdown_pct,
            'current_drawdown_pct': self.current_drawdown_pct,
            'max_single_position_pct': self.max_single_position_pct,
            'open_positions': self.open_positions,
            'daily_trades_count': self.daily_trades_count,
            'volatility_index': self.volatility_index,
            'risk_score': self.risk_score,
            'positions_breakdown': self.positions_breakdown
        }


@dataclass
class RiskConfig:
    """Configuración global del sistema RMS"""
    initial_capital: float = 1_000_000.0
    
    default_per_trade_limit_usd: float = 50_000.0
    default_per_trade_limit_pct: float = 5.0
    
    default_daily_loss_limit_usd: float = 20_000.0
    default_daily_loss_limit_pct: float = 2.0
    
    default_max_drawdown_usd: float = 100_000.0
    default_max_drawdown_pct: float = 10.0
    
    default_max_concentration_pct: float = 25.0
    
    default_max_daily_trades: int = 50
    default_max_open_positions: int = 10
    
    high_volatility_threshold: float = 30.0
    high_volatility_position_reduction: float = 0.5
    
    warning_threshold_pct: float = 80.0
    critical_threshold_pct: float = 95.0
    
    halt_cooldown_minutes: int = 60
    
    enable_telegram_alerts: bool = True
    enable_auto_halt: bool = True
    enable_position_reduction: bool = False
    
    @classmethod
    def from_env(cls) -> 'RiskConfig':
        """Crear configuración desde variables de entorno"""
        import os
        config = cls()
        
        if os.getenv('RMS_INITIAL_CAPITAL'):
            config.initial_capital = float(os.getenv('RMS_INITIAL_CAPITAL'))
        if os.getenv('RMS_PER_TRADE_LIMIT_PCT'):
            config.default_per_trade_limit_pct = float(os.getenv('RMS_PER_TRADE_LIMIT_PCT'))
        if os.getenv('RMS_DAILY_LOSS_LIMIT_PCT'):
            config.default_daily_loss_limit_pct = float(os.getenv('RMS_DAILY_LOSS_LIMIT_PCT'))
        if os.getenv('RMS_MAX_DRAWDOWN_PCT'):
            config.default_max_drawdown_pct = float(os.getenv('RMS_MAX_DRAWDOWN_PCT'))
        if os.getenv('RMS_MAX_CONCENTRATION_PCT'):
            config.default_max_concentration_pct = float(os.getenv('RMS_MAX_CONCENTRATION_PCT'))
        if os.getenv('RMS_ENABLE_AUTO_HALT'):
            config.enable_auto_halt = os.getenv('RMS_ENABLE_AUTO_HALT', 'true').lower() == 'true'
            
        return config


DEFAULT_LIMITS = [
    RiskLimit(
        limit_type=RiskLimitType.PER_TRADE,
        threshold_value=5.0,
        threshold_unit=ThresholdUnit.PERCENT,
        warning_threshold_pct=80.0
    ),
    RiskLimit(
        limit_type=RiskLimitType.DAILY_LOSS,
        threshold_value=2.0,
        threshold_unit=ThresholdUnit.PERCENT,
        warning_threshold_pct=80.0
    ),
    RiskLimit(
        limit_type=RiskLimitType.MAX_DRAWDOWN,
        threshold_value=10.0,
        threshold_unit=ThresholdUnit.PERCENT,
        warning_threshold_pct=80.0
    ),
    RiskLimit(
        limit_type=RiskLimitType.PORTFOLIO_CONCENTRATION,
        threshold_value=25.0,
        threshold_unit=ThresholdUnit.PERCENT,
        warning_threshold_pct=80.0
    ),
    RiskLimit(
        limit_type=RiskLimitType.DAILY_TRADES,
        threshold_value=50,
        threshold_unit=ThresholdUnit.COUNT,
        warning_threshold_pct=80.0
    ),
    RiskLimit(
        limit_type=RiskLimitType.OPEN_POSITIONS,
        threshold_value=10,
        threshold_unit=ThresholdUnit.COUNT,
        warning_threshold_pct=80.0
    )
]
