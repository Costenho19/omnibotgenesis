"""
OMNIX V6.4 INSTITUTIONAL+ - Settings Models
Modelos de datos para configuración personalizada de usuarios
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from enum import Enum


class RiskProfile(Enum):
    """Perfiles de riesgo institucionales"""
    ULTRA_CONSERVATIVE = "ultra_conservative"  # 1-2% max por trade
    CONSERVATIVE = "conservative"              # 2-5% max por trade
    MODERATE = "moderate"                      # 5-10% max por trade
    AGGRESSIVE = "aggressive"                  # 10-15% max por trade
    INSTITUTIONAL = "institutional"            # 5-8% optimizado institucional
    CUSTOM = "custom"                          # Configuración personalizada

    @classmethod
    def get_defaults(cls, profile: 'RiskProfile') -> Dict[str, Any]:
        """Obtener valores por defecto para cada perfil"""
        defaults = {
            cls.ULTRA_CONSERVATIVE: {
                'max_trade_pct': 2.0,
                'daily_loss_limit_pct': 5.0,
                'max_open_positions': 3,
                'stop_loss_pct': 2.0,
                'take_profit_pct': 4.0,
                'leverage_max': 1.0,
                'description': '🛡️ Ultra Conservador - Máxima protección del capital'
            },
            cls.CONSERVATIVE: {
                'max_trade_pct': 5.0,
                'daily_loss_limit_pct': 10.0,
                'max_open_positions': 5,
                'stop_loss_pct': 3.0,
                'take_profit_pct': 6.0,
                'leverage_max': 2.0,
                'description': '🔒 Conservador - Crecimiento estable con protección'
            },
            cls.MODERATE: {
                'max_trade_pct': 10.0,
                'daily_loss_limit_pct': 15.0,
                'max_open_positions': 8,
                'stop_loss_pct': 5.0,
                'take_profit_pct': 10.0,
                'leverage_max': 3.0,
                'description': '⚖️ Moderado - Balance entre crecimiento y riesgo'
            },
            cls.AGGRESSIVE: {
                'max_trade_pct': 15.0,
                'daily_loss_limit_pct': 25.0,
                'max_open_positions': 12,
                'stop_loss_pct': 8.0,
                'take_profit_pct': 16.0,
                'leverage_max': 5.0,
                'description': '🔥 Agresivo - Máximo crecimiento, mayor volatilidad'
            },
            cls.INSTITUTIONAL: {
                'max_trade_pct': 8.0,
                'daily_loss_limit_pct': 12.0,
                'max_open_positions': 10,
                'stop_loss_pct': 4.0,
                'take_profit_pct': 8.0,
                'leverage_max': 3.0,
                'description': '🏦 Institucional - Parámetros Goldman-Sachs level'
            },
            cls.CUSTOM: {
                'max_trade_pct': 5.0,
                'daily_loss_limit_pct': 10.0,
                'max_open_positions': 5,
                'stop_loss_pct': 3.0,
                'take_profit_pct': 6.0,
                'leverage_max': 2.0,
                'description': '⚙️ Personalizado - Tus propios parámetros'
            }
        }
        return defaults.get(profile, defaults[cls.MODERATE])


@dataclass
class TradingLimits:
    """Límites de trading personalizados"""
    min_trade_usd: float = 10.0              # Mínimo por trade
    max_trade_usd: float = 1000.0            # Máximo por trade
    daily_trade_limit_usd: float = 5000.0    # Límite diario de trading
    max_trade_pct: float = 5.0               # Porcentaje máximo del portfolio
    max_open_positions: int = 5              # Máximo de posiciones abiertas
    leverage_max: float = 2.0                # Apalancamiento máximo
    
    def to_dict(self) -> Dict:
        return {
            'min_trade_usd': self.min_trade_usd,
            'max_trade_usd': self.max_trade_usd,
            'daily_trade_limit_usd': self.daily_trade_limit_usd,
            'max_trade_pct': self.max_trade_pct,
            'max_open_positions': self.max_open_positions,
            'leverage_max': self.leverage_max
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TradingLimits':
        return cls(
            min_trade_usd=data.get('min_trade_usd', 10.0),
            max_trade_usd=data.get('max_trade_usd', 1000.0),
            daily_trade_limit_usd=data.get('daily_trade_limit_usd', 5000.0),
            max_trade_pct=data.get('max_trade_pct', 5.0),
            max_open_positions=data.get('max_open_positions', 5),
            leverage_max=data.get('leverage_max', 2.0)
        )


@dataclass
class ProtectionSettings:
    """Configuración del sistema de auto-protección"""
    daily_loss_limit_pct: float = 10.0       # Pausa automática si pierde X% del día
    weekly_loss_limit_pct: float = 20.0      # Pausa automática semanal
    stop_loss_default_pct: float = 3.0       # Stop loss por defecto
    take_profit_default_pct: float = 6.0     # Take profit por defecto
    trailing_stop_enabled: bool = True        # Trailing stop habilitado
    trailing_stop_pct: float = 2.0           # Porcentaje del trailing stop
    auto_pause_enabled: bool = True          # Pausar automáticamente al alcanzar límite
    cool_down_minutes: int = 60              # Minutos de pausa tras alcanzar límite
    
    def to_dict(self) -> Dict:
        return {
            'daily_loss_limit_pct': self.daily_loss_limit_pct,
            'weekly_loss_limit_pct': self.weekly_loss_limit_pct,
            'stop_loss_default_pct': self.stop_loss_default_pct,
            'take_profit_default_pct': self.take_profit_default_pct,
            'trailing_stop_enabled': self.trailing_stop_enabled,
            'trailing_stop_pct': self.trailing_stop_pct,
            'auto_pause_enabled': self.auto_pause_enabled,
            'cool_down_minutes': self.cool_down_minutes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProtectionSettings':
        return cls(
            daily_loss_limit_pct=data.get('daily_loss_limit_pct', 10.0),
            weekly_loss_limit_pct=data.get('weekly_loss_limit_pct', 20.0),
            stop_loss_default_pct=data.get('stop_loss_default_pct', 3.0),
            take_profit_default_pct=data.get('take_profit_default_pct', 6.0),
            trailing_stop_enabled=data.get('trailing_stop_enabled', True),
            trailing_stop_pct=data.get('trailing_stop_pct', 2.0),
            auto_pause_enabled=data.get('auto_pause_enabled', True),
            cool_down_minutes=data.get('cool_down_minutes', 60)
        )


@dataclass
class NotificationPreferences:
    """Preferencias de notificaciones del usuario"""
    trade_alerts: bool = True                # Alertas de cada trade
    daily_summary: bool = True               # Resumen diario
    weekly_report: bool = True               # Reporte semanal
    price_alerts: bool = True                # Alertas de precio
    stop_loss_alerts: bool = True            # Alertas de stop loss
    take_profit_alerts: bool = True          # Alertas de take profit
    protection_alerts: bool = True           # Alertas de protección
    market_news: bool = False                # Noticias del mercado
    quiet_hours_start: Optional[int] = None  # Hora inicio sin notificaciones (0-23)
    quiet_hours_end: Optional[int] = None    # Hora fin sin notificaciones (0-23)
    language: str = 'es'                     # Idioma preferido
    
    def to_dict(self) -> Dict:
        return {
            'trade_alerts': self.trade_alerts,
            'daily_summary': self.daily_summary,
            'weekly_report': self.weekly_report,
            'price_alerts': self.price_alerts,
            'stop_loss_alerts': self.stop_loss_alerts,
            'take_profit_alerts': self.take_profit_alerts,
            'protection_alerts': self.protection_alerts,
            'market_news': self.market_news,
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end,
            'language': self.language
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NotificationPreferences':
        return cls(
            trade_alerts=data.get('trade_alerts', True),
            daily_summary=data.get('daily_summary', True),
            weekly_report=data.get('weekly_report', True),
            price_alerts=data.get('price_alerts', True),
            stop_loss_alerts=data.get('stop_loss_alerts', True),
            take_profit_alerts=data.get('take_profit_alerts', True),
            protection_alerts=data.get('protection_alerts', True),
            market_news=data.get('market_news', False),
            quiet_hours_start=data.get('quiet_hours_start'),
            quiet_hours_end=data.get('quiet_hours_end'),
            language=data.get('language', 'es')
        )


@dataclass
class UserSettings:
    """Configuración completa del usuario"""
    user_id: str
    username: Optional[str] = None
    
    risk_profile: RiskProfile = RiskProfile.MODERATE
    trading_limits: TradingLimits = field(default_factory=TradingLimits)
    protection_settings: ProtectionSettings = field(default_factory=ProtectionSettings)
    notification_preferences: NotificationPreferences = field(default_factory=NotificationPreferences)
    
    allowed_cryptos: List[str] = field(default_factory=lambda: [
        'BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD', 'ADA/USD', 'DOGE/USD', 'DOT/USD'
    ])
    allowed_stocks: List[str] = field(default_factory=lambda: [
        'AAPL', 'TSLA', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META'
    ])
    
    active_strategies: List[str] = field(default_factory=lambda: [
        'ARES_V1', 'ARES_V2', 'MONTE_CARLO', 'HMM_REGIME'
    ])
    
    trading_enabled: bool = True             # Trading habilitado
    auto_trading: bool = False               # Trading automático
    paper_trading_mode: bool = True          # Modo paper trading
    is_paused: bool = False                  # Trading pausado (protección)
    pause_reason: Optional[str] = None       # Razón de la pausa
    pause_until: Optional[datetime] = None   # Hasta cuándo está pausado
    
    onboarding_completed: bool = False       # Onboarding completado
    terms_accepted: bool = False             # Términos aceptados
    risk_disclosure_accepted: bool = False   # Disclosure de riesgo aceptado
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def get_daily_stats_today(self) -> Dict:
        """Placeholder para stats del día"""
        return {
            'trades_count': 0,
            'total_traded_usd': 0,
            'pnl_usd': 0,
            'pnl_pct': 0
        }
    
    def can_trade(self) -> tuple[bool, str]:
        """Verificar si el usuario puede operar"""
        if not self.trading_enabled:
            return False, "Trading deshabilitado en tu configuración"
        
        if self.is_paused:
            now_utc = datetime.now(timezone.utc)
            pause_until_aware = self.pause_until.replace(tzinfo=timezone.utc) if self.pause_until and self.pause_until.tzinfo is None else self.pause_until
            if pause_until_aware and now_utc < pause_until_aware:
                minutes_left = int((pause_until_aware - now_utc).total_seconds() / 60)
                return False, f"Trading pausado por protección. Reanuda en {minutes_left} minutos. Razón: {self.pause_reason}"
            else:
                return True, "OK"
        
        return True, "OK"
    
    def validate_trade(self, amount_usd: float, symbol: str) -> tuple[bool, str]:
        """Validar si un trade cumple con la configuración del usuario"""
        can, reason = self.can_trade()
        if not can:
            return False, reason
        
        if amount_usd < self.trading_limits.min_trade_usd:
            return False, f"Monto mínimo: ${self.trading_limits.min_trade_usd:.2f}"
        
        if amount_usd > self.trading_limits.max_trade_usd:
            return False, f"Monto máximo: ${self.trading_limits.max_trade_usd:.2f}"
        
        is_crypto = '/' in symbol
        if is_crypto and symbol not in self.allowed_cryptos:
            return False, f"Crypto {symbol} no está en tu lista permitida"
        
        if not is_crypto and symbol not in self.allowed_stocks:
            return False, f"Acción {symbol} no está en tu lista permitida"
        
        return True, "OK"
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario para guardar en DB"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'risk_profile': self.risk_profile.value,
            'trading_limits': self.trading_limits.to_dict(),
            'protection_settings': self.protection_settings.to_dict(),
            'notification_preferences': self.notification_preferences.to_dict(),
            'allowed_cryptos': self.allowed_cryptos,
            'allowed_stocks': self.allowed_stocks,
            'active_strategies': self.active_strategies,
            'trading_enabled': self.trading_enabled,
            'auto_trading': self.auto_trading,
            'paper_trading_mode': self.paper_trading_mode,
            'is_paused': self.is_paused,
            'pause_reason': self.pause_reason,
            'pause_until': self.pause_until.isoformat() if self.pause_until else None,
            'onboarding_completed': self.onboarding_completed,
            'terms_accepted': self.terms_accepted,
            'risk_disclosure_accepted': self.risk_disclosure_accepted
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserSettings':
        """Crear desde diccionario de la DB"""
        risk_profile_str = data.get('risk_profile', 'moderate')
        try:
            risk_profile = RiskProfile(risk_profile_str)
        except ValueError:
            risk_profile = RiskProfile.MODERATE
        
        pause_until = None
        if data.get('pause_until'):
            try:
                pause_until = datetime.fromisoformat(data['pause_until'])
            except:
                pass
        
        return cls(
            user_id=data.get('user_id', ''),
            username=data.get('username'),
            risk_profile=risk_profile,
            trading_limits=TradingLimits.from_dict(data.get('trading_limits', {})),
            protection_settings=ProtectionSettings.from_dict(data.get('protection_settings', {})),
            notification_preferences=NotificationPreferences.from_dict(data.get('notification_preferences', {})),
            allowed_cryptos=data.get('allowed_cryptos', [
                'BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD', 'ADA/USD', 'DOGE/USD', 'DOT/USD'
            ]),
            allowed_stocks=data.get('allowed_stocks', [
                'AAPL', 'TSLA', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META'
            ]),
            active_strategies=data.get('active_strategies', [
                'ARES_V1', 'ARES_V2', 'MONTE_CARLO', 'HMM_REGIME'
            ]),
            trading_enabled=data.get('trading_enabled', True),
            auto_trading=data.get('auto_trading', False),
            paper_trading_mode=data.get('paper_trading_mode', True),
            is_paused=data.get('is_paused', False),
            pause_reason=data.get('pause_reason'),
            pause_until=pause_until,
            onboarding_completed=data.get('onboarding_completed', False),
            terms_accepted=data.get('terms_accepted', False),
            risk_disclosure_accepted=data.get('risk_disclosure_accepted', False)
        )
    
    def get_profile_summary(self) -> str:
        """Generar resumen visual del perfil"""
        profile_info = RiskProfile.get_defaults(self.risk_profile)
        
        emoji_map = {
            RiskProfile.ULTRA_CONSERVATIVE: "🛡️",
            RiskProfile.CONSERVATIVE: "🔒",
            RiskProfile.MODERATE: "⚖️",
            RiskProfile.AGGRESSIVE: "🔥",
            RiskProfile.INSTITUTIONAL: "🏦",
            RiskProfile.CUSTOM: "⚙️"
        }
        
        emoji = emoji_map.get(self.risk_profile, "📊")
        
        status = "🟢 ACTIVO" if self.trading_enabled and not self.is_paused else "🔴 PAUSADO"
        mode = "📝 Paper Trading" if self.paper_trading_mode else "💵 Trading Real"
        auto = "🤖 Automático" if self.auto_trading else "👤 Manual"
        
        summary = f"""
{emoji} **TU PERFIL OMNIX**

**Estado:** {status}
**Modo:** {mode} | {auto}

**Perfil de Riesgo:** {profile_info['description']}

**📊 Límites Configurados:**
• Mín. por trade: ${self.trading_limits.min_trade_usd:.0f}
• Máx. por trade: ${self.trading_limits.max_trade_usd:.0f}
• Límite diario: ${self.trading_limits.daily_trade_limit_usd:.0f}
• Posiciones máx: {self.trading_limits.max_open_positions}
• Apalancamiento: x{self.trading_limits.leverage_max:.1f}

**🛡️ Protección:**
• Stop Loss: {self.protection_settings.stop_loss_default_pct}%
• Take Profit: {self.protection_settings.take_profit_default_pct}%
• Límite pérdida diaria: {self.protection_settings.daily_loss_limit_pct}%
• Auto-pausa: {'✅' if self.protection_settings.auto_pause_enabled else '❌'}

**📈 Estrategias Activas:** {len(self.active_strategies)}
{', '.join(self.active_strategies[:4])}{'...' if len(self.active_strategies) > 4 else ''}

**🪙 Cryptos:** {len(self.allowed_cryptos)} permitidas
**📊 Stocks:** {len(self.allowed_stocks)} permitidas
"""
        return summary.strip()
