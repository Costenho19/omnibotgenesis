"""
OMNIX V6.4 INSTITUTIONAL+ - User Settings Service
Servicio Premium de Configuración Personalizada

Maneja:
- Persistencia de configuraciones en PostgreSQL
- Validación de trades según límites del usuario
- Sistema de auto-protección
- Procesamiento de comandos en lenguaje natural
"""

import logging
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple, List

from .settings_models import (
    UserSettings, 
    RiskProfile, 
    TradingLimits, 
    ProtectionSettings,
    NotificationPreferences
)

logger = logging.getLogger(__name__)

PSYCOPG_AVAILABLE = False
try:
    import psycopg
    PSYCOPG_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ psycopg no disponible para UserSettingsService")


class UserSettingsService:
    """
    Servicio de configuración personalizada por usuario
    
    Características:
    - Almacenamiento en PostgreSQL
    - Cache en memoria para rendimiento
    - Valores por defecto inteligentes
    - Validación de trades
    - Sistema de auto-protección
    """
    
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        self.connected = False
        self._settings_cache: Dict[str, UserSettings] = {}
        self._daily_stats_cache: Dict[str, Dict] = {}
        
        if self.db_url and PSYCOPG_AVAILABLE:
            self._init_table()
    
    def _get_connection(self):
        """Obtener conexión a PostgreSQL"""
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return None
        try:
            return psycopg.connect(self.db_url)
        except Exception as e:
            logger.error(f"Error conectando a DB: {e}")
            return None
    
    def _init_table(self):
        """Inicializar tabla user_settings"""
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    risk_profile TEXT DEFAULT 'moderate',
                    trading_limits JSONB DEFAULT '{}',
                    protection_settings JSONB DEFAULT '{}',
                    notification_preferences JSONB DEFAULT '{}',
                    allowed_cryptos JSONB DEFAULT '[]',
                    allowed_stocks JSONB DEFAULT '[]',
                    active_strategies JSONB DEFAULT '[]',
                    trading_enabled BOOLEAN DEFAULT true,
                    auto_trading BOOLEAN DEFAULT false,
                    paper_trading_mode BOOLEAN DEFAULT true,
                    is_paused BOOLEAN DEFAULT false,
                    pause_reason TEXT,
                    pause_until TIMESTAMP WITH TIME ZONE,
                    onboarding_completed BOOLEAN DEFAULT false,
                    terms_accepted BOOLEAN DEFAULT false,
                    risk_disclosure_accepted BOOLEAN DEFAULT false,
                    daily_pnl_usd NUMERIC(18,8) DEFAULT 0,
                    daily_trades_count INTEGER DEFAULT 0,
                    daily_traded_usd NUMERIC(18,8) DEFAULT 0,
                    daily_stats_date DATE DEFAULT CURRENT_DATE,
                    weekly_pnl_usd NUMERIC(18,8) DEFAULT 0,
                    risk_level TEXT DEFAULT 'MODERATE',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                ALTER TABLE user_settings
                ADD COLUMN IF NOT EXISTS risk_level TEXT DEFAULT 'MODERATE'
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_settings_profile ON user_settings(risk_profile)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_settings_paused ON user_settings(is_paused) WHERE is_paused = true')
            
            conn.commit()
            self.connected = True
            logger.info("✅ Tabla user_settings inicializada")
            
        except Exception as e:
            logger.error(f"Error inicializando tabla user_settings: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_user_settings(self, user_id: str, username: Optional[str] = None) -> UserSettings:
        """Obtener configuración del usuario (crea una nueva si no existe)"""
        if user_id in self._settings_cache:
            cached = self._settings_cache[user_id]
            if cached.updated_at:
                now = datetime.now(timezone.utc)
                updated = cached.updated_at.replace(tzinfo=timezone.utc) if cached.updated_at.tzinfo is None else cached.updated_at
                if (now - updated).seconds < 300:
                    return cached
        
        conn = self._get_connection()
        if not conn:
            settings = UserSettings(user_id=user_id, username=username)
            self._settings_cache[user_id] = settings
            return settings
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, username, risk_profile, trading_limits, protection_settings,
                       notification_preferences, allowed_cryptos, allowed_stocks, active_strategies,
                       trading_enabled, auto_trading, paper_trading_mode, is_paused, pause_reason,
                       pause_until, onboarding_completed, terms_accepted, risk_disclosure_accepted,
                       daily_pnl_usd, daily_trades_count, daily_traded_usd, daily_stats_date,
                       created_at, updated_at
                FROM user_settings
                WHERE user_id = %s
            ''', (str(user_id),))
            
            row = cursor.fetchone()
            
            if row:
                data = {
                    'user_id': row[0],
                    'username': row[1],
                    'risk_profile': row[2],
                    'trading_limits': row[3] if isinstance(row[3], dict) else json.loads(row[3] or '{}'),
                    'protection_settings': row[4] if isinstance(row[4], dict) else json.loads(row[4] or '{}'),
                    'notification_preferences': row[5] if isinstance(row[5], dict) else json.loads(row[5] or '{}'),
                    'allowed_cryptos': row[6] if isinstance(row[6], list) else json.loads(row[6] or '[]'),
                    'allowed_stocks': row[7] if isinstance(row[7], list) else json.loads(row[7] or '[]'),
                    'active_strategies': row[8] if isinstance(row[8], list) else json.loads(row[8] or '[]'),
                    'trading_enabled': row[9],
                    'auto_trading': row[10],
                    'paper_trading_mode': row[11],
                    'is_paused': row[12],
                    'pause_reason': row[13],
                    'pause_until': row[14].isoformat() if row[14] else None,
                    'onboarding_completed': row[15],
                    'terms_accepted': row[16],
                    'risk_disclosure_accepted': row[17]
                }
                
                settings = UserSettings.from_dict(data)
                settings.created_at = row[22]
                settings.updated_at = row[23]
                
                self._daily_stats_cache[user_id] = {
                    'pnl_usd': float(row[18] or 0),
                    'trades_count': row[19] or 0,
                    'traded_usd': float(row[20] or 0),
                    'date': row[21]
                }
            else:
                settings = self._create_default_settings(user_id, username)
            
            self._settings_cache[user_id] = settings
            cursor.close()
            conn.close()
            return settings
            
        except Exception as e:
            logger.error(f"Error obteniendo settings: {e}")
            settings = UserSettings(user_id=user_id, username=username)
            self._settings_cache[user_id] = settings
            return settings
    
    def _create_default_settings(self, user_id: str, username: Optional[str] = None) -> UserSettings:
        """Crear configuración por defecto para nuevo usuario"""
        settings = UserSettings(
            user_id=user_id,
            username=username,
            risk_profile=RiskProfile.MODERATE,
            paper_trading_mode=True,
            onboarding_completed=False
        )
        
        self.save_user_settings(settings)
        return settings
    
    def save_user_settings(self, settings: UserSettings) -> bool:
        """Guardar configuración del usuario"""
        conn = self._get_connection()
        if not conn:
            self._settings_cache[settings.user_id] = settings
            return False
        
        try:
            cursor = conn.cursor()
            
            data = settings.to_dict()
            
            cursor.execute('''
                INSERT INTO user_settings (
                    user_id, username, risk_profile, trading_limits, protection_settings,
                    notification_preferences, allowed_cryptos, allowed_stocks, active_strategies,
                    trading_enabled, auto_trading, paper_trading_mode, is_paused, pause_reason,
                    pause_until, onboarding_completed, terms_accepted, risk_disclosure_accepted,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    risk_profile = EXCLUDED.risk_profile,
                    trading_limits = EXCLUDED.trading_limits,
                    protection_settings = EXCLUDED.protection_settings,
                    notification_preferences = EXCLUDED.notification_preferences,
                    allowed_cryptos = EXCLUDED.allowed_cryptos,
                    allowed_stocks = EXCLUDED.allowed_stocks,
                    active_strategies = EXCLUDED.active_strategies,
                    trading_enabled = EXCLUDED.trading_enabled,
                    auto_trading = EXCLUDED.auto_trading,
                    paper_trading_mode = EXCLUDED.paper_trading_mode,
                    is_paused = EXCLUDED.is_paused,
                    pause_reason = EXCLUDED.pause_reason,
                    pause_until = EXCLUDED.pause_until,
                    onboarding_completed = EXCLUDED.onboarding_completed,
                    terms_accepted = EXCLUDED.terms_accepted,
                    risk_disclosure_accepted = EXCLUDED.risk_disclosure_accepted,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                data['user_id'],
                data['username'],
                data['risk_profile'],
                json.dumps(data['trading_limits']),
                json.dumps(data['protection_settings']),
                json.dumps(data['notification_preferences']),
                json.dumps(data['allowed_cryptos']),
                json.dumps(data['allowed_stocks']),
                json.dumps(data['active_strategies']),
                data['trading_enabled'],
                data['auto_trading'],
                data['paper_trading_mode'],
                data['is_paused'],
                data['pause_reason'],
                datetime.fromisoformat(data['pause_until']) if data['pause_until'] else None,
                data['onboarding_completed'],
                data['terms_accepted'],
                data['risk_disclosure_accepted']
            ))
            
            conn.commit()
            settings.updated_at = datetime.now()
            self._settings_cache[settings.user_id] = settings
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Settings guardados para usuario {settings.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando settings: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def update_risk_profile(self, user_id: str, profile: RiskProfile, accept_disclaimer: bool = False) -> Tuple[bool, str]:
        """Actualizar perfil de riesgo del usuario"""
        settings = self.get_user_settings(user_id)
        
        high_risk_profiles = [RiskProfile.AGGRESSIVE, RiskProfile.CUSTOM]
        if profile in high_risk_profiles and not accept_disclaimer:
            return False, """⚠️ **ADVERTENCIA DE RIESGO ALTO**

Has seleccionado un perfil de riesgo ALTO. Esto implica:
• Mayor exposición a pérdidas potenciales
• Mayor volatilidad en tu portfolio
• Mayor apalancamiento disponible

Para confirmar, envía el comando nuevamente con la palabra ACEPTO:
`/perfil agresivo ACEPTO`

Recuerda: Invierte solo lo que puedas permitirte perder."""
        
        settings.risk_profile = profile
        
        defaults = RiskProfile.get_defaults(profile)
        settings.trading_limits.max_trade_pct = defaults['max_trade_pct']
        settings.trading_limits.leverage_max = defaults['leverage_max']
        settings.protection_settings.daily_loss_limit_pct = defaults['daily_loss_limit_pct']
        settings.protection_settings.stop_loss_default_pct = defaults['stop_loss_pct']
        settings.protection_settings.take_profit_default_pct = defaults['take_profit_pct']
        settings.trading_limits.max_open_positions = defaults['max_open_positions']
        
        if profile in high_risk_profiles:
            settings.risk_disclosure_accepted = True
        
        self.save_user_settings(settings)
        
        return True, f"""✅ **Perfil actualizado: {defaults['description']}**

Nuevos parámetros aplicados:
• Máx. por trade: {defaults['max_trade_pct']}%
• Stop Loss: {defaults['stop_loss_pct']}%
• Take Profit: {defaults['take_profit_pct']}%
• Límite pérdida diaria: {defaults['daily_loss_limit_pct']}%
• Posiciones máx: {defaults['max_open_positions']}

Tu configuración está lista. Usa /miconfig para ver todos los detalles."""
    
    def update_trading_limits(
        self, 
        user_id: str, 
        min_trade: Optional[float] = None,
        max_trade: Optional[float] = None,
        daily_limit: Optional[float] = None,
        max_positions: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Actualizar límites de trading"""
        settings = self.get_user_settings(user_id)
        
        changes = []
        
        if min_trade is not None:
            if min_trade < 1:
                return False, "El mínimo por trade debe ser al menos $1"
            settings.trading_limits.min_trade_usd = min_trade
            changes.append(f"• Mínimo: ${min_trade:.0f}")
        
        if max_trade is not None:
            if max_trade < settings.trading_limits.min_trade_usd:
                return False, "El máximo debe ser mayor al mínimo"
            if max_trade > 100000:
                return False, "El máximo por trade no puede superar $100,000"
            settings.trading_limits.max_trade_usd = max_trade
            changes.append(f"• Máximo: ${max_trade:.0f}")
        
        if daily_limit is not None:
            if daily_limit < settings.trading_limits.max_trade_usd:
                return False, "El límite diario debe ser mayor al máximo por trade"
            settings.trading_limits.daily_trade_limit_usd = daily_limit
            changes.append(f"• Límite diario: ${daily_limit:.0f}")
        
        if max_positions is not None:
            if max_positions < 1 or max_positions > 50:
                return False, "Las posiciones máximas deben estar entre 1 y 50"
            settings.trading_limits.max_open_positions = max_positions
            changes.append(f"• Posiciones máx: {max_positions}")
        
        self.save_user_settings(settings)
        
        return True, f"""✅ **Límites actualizados**

Cambios aplicados:
{chr(10).join(changes)}

Usa /miconfig para ver tu configuración completa."""
    
    def update_protection_settings(
        self,
        user_id: str,
        daily_loss_limit: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        auto_pause: Optional[bool] = None
    ) -> Tuple[bool, str]:
        """Actualizar configuración de protección"""
        settings = self.get_user_settings(user_id)
        
        changes = []
        
        if daily_loss_limit is not None:
            if daily_loss_limit < 1 or daily_loss_limit > 50:
                return False, "El límite de pérdida diaria debe estar entre 1% y 50%"
            settings.protection_settings.daily_loss_limit_pct = daily_loss_limit
            changes.append(f"• Límite pérdida diaria: {daily_loss_limit}%")
        
        if stop_loss is not None:
            if stop_loss < 0.5 or stop_loss > 20:
                return False, "El stop loss debe estar entre 0.5% y 20%"
            settings.protection_settings.stop_loss_default_pct = stop_loss
            changes.append(f"• Stop Loss: {stop_loss}%")
        
        if take_profit is not None:
            if take_profit < 1 or take_profit > 100:
                return False, "El take profit debe estar entre 1% y 100%"
            settings.protection_settings.take_profit_default_pct = take_profit
            changes.append(f"• Take Profit: {take_profit}%")
        
        if auto_pause is not None:
            settings.protection_settings.auto_pause_enabled = auto_pause
            changes.append(f"• Auto-pausa: {'✅ Activada' if auto_pause else '❌ Desactivada'}")
        
        self.save_user_settings(settings)
        
        return True, f"""🛡️ **Protección actualizada**

{chr(10).join(changes)}

Tu sistema de protección está configurado."""
    
    def toggle_auto_trading(self, user_id: str, enable: bool) -> Tuple[bool, str]:
        """Activar/desactivar trading automático"""
        settings = self.get_user_settings(user_id)
        
        if enable and not settings.risk_disclosure_accepted:
            return False, """🤖 **Confirmación requerida**

Para activar el trading automático, confirma que entiendes el sistema:

OMNIX ejecuta operaciones con gestión de riesgo institucional, límites de posición controlados y Asset Quarantine activo.

Envía: `/autotrading activar ACEPTO`"""
        
        settings.auto_trading = enable
        if enable:
            settings.risk_disclosure_accepted = True
        
        self.save_user_settings(settings)
        
        if enable:
            return True, """🤖 **Trading Automático ACTIVADO**

OMNIX ahora puede ejecutar trades automáticamente basándose en:
• Tus estrategias activas
• Tus límites configurados
• Tu perfil de riesgo

El sistema respetará todos tus parámetros de protección.

Usa /pausar para detener temporalmente en cualquier momento."""
        else:
            return True, """👤 **Trading Automático DESACTIVADO**

OMNIX ahora solo ejecutará trades cuando tú lo solicites explícitamente.

Puedes reactivarlo cuando quieras con /autotrading activar"""
    
    def pause_trading(self, user_id: str, reason: str, minutes: int = 60) -> Tuple[bool, str]:
        """Pausar trading (manual o automático por protección)"""
        settings = self.get_user_settings(user_id)
        
        settings.is_paused = True
        settings.pause_reason = reason
        settings.pause_until = datetime.now() + timedelta(minutes=minutes)
        
        self.save_user_settings(settings)
        
        return True, f"""⏸️ **Trading PAUSADO**

Razón: {reason}
Duración: {minutes} minutos
Reanuda: {settings.pause_until.strftime('%H:%M')}

Durante la pausa:
• No se ejecutarán nuevos trades
• Las posiciones abiertas se mantienen
• Puedes reanudar manualmente con /reanudar"""
    
    def resume_trading(self, user_id: str) -> Tuple[bool, str]:
        """Reanudar trading"""
        settings = self.get_user_settings(user_id)
        
        settings.is_paused = False
        settings.pause_reason = None
        settings.pause_until = None
        
        self.save_user_settings(settings)
        
        return True, """▶️ **Trading REANUDADO**

OMNIX está listo para operar según tu configuración.
"""
    
    def check_daily_protection(self, user_id: str, new_pnl: float) -> Tuple[bool, Optional[str]]:
        """Verificar si se debe activar la protección diaria"""
        settings = self.get_user_settings(user_id)
        
        if not settings.protection_settings.auto_pause_enabled:
            return True, None
        
        daily_stats = self._daily_stats_cache.get(user_id, {'pnl_usd': 0, 'traded_usd': 0})
        current_daily_pnl = daily_stats.get('pnl_usd', 0) + new_pnl
        
        starting_balance = settings.trading_limits.daily_trade_limit_usd * 10
        loss_pct = abs(min(current_daily_pnl, 0)) / starting_balance * 100
        
        if loss_pct >= settings.protection_settings.daily_loss_limit_pct:
            self.pause_trading(
                user_id,
                f"Límite de pérdida diaria alcanzado ({loss_pct:.1f}%)",
                settings.protection_settings.cool_down_minutes
            )
            
            return False, f"""🛡️ **PROTECCIÓN ACTIVADA**

Has alcanzado tu límite de pérdida diaria ({loss_pct:.1f}%).

El trading se ha pausado automáticamente por {settings.protection_settings.cool_down_minutes} minutos para proteger tu capital.

Esto es una medida de seguridad que tú configuraste. Usa /proteccion para ajustar estos límites."""
        
        return True, None
    
    def record_trade(self, user_id: str, amount_usd: float, pnl_usd: float):
        """Registrar un trade en las estadísticas diarias"""
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_settings
                SET 
                    daily_trades_count = CASE 
                        WHEN daily_stats_date = CURRENT_DATE THEN daily_trades_count + 1
                        ELSE 1
                    END,
                    daily_traded_usd = CASE 
                        WHEN daily_stats_date = CURRENT_DATE THEN daily_traded_usd + %s
                        ELSE %s
                    END,
                    daily_pnl_usd = CASE 
                        WHEN daily_stats_date = CURRENT_DATE THEN daily_pnl_usd + %s
                        ELSE %s
                    END,
                    daily_stats_date = CURRENT_DATE,
                    weekly_pnl_usd = weekly_pnl_usd + %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            ''', (amount_usd, amount_usd, pnl_usd, pnl_usd, pnl_usd, str(user_id)))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if user_id in self._daily_stats_cache:
                self._daily_stats_cache[user_id]['pnl_usd'] = \
                    self._daily_stats_cache[user_id].get('pnl_usd', 0) + pnl_usd
                self._daily_stats_cache[user_id]['traded_usd'] = \
                    self._daily_stats_cache[user_id].get('traded_usd', 0) + amount_usd
                self._daily_stats_cache[user_id]['trades_count'] = \
                    self._daily_stats_cache[user_id].get('trades_count', 0) + 1
                    
        except Exception as e:
            logger.error(f"Error registrando trade en stats: {e}")
            conn.rollback()
            conn.close()
    
    def process_natural_language_command(self, user_id: str, message: str) -> Optional[Tuple[str, Dict]]:
        """
        Procesar comando en lenguaje natural
        
        Ejemplos:
        - "quiero ser más agresivo"
        - "baja mi riesgo"
        - "máximo 500 por trade"
        - "pausa el trading"
        - "activa el auto trading"
        """
        message_lower = message.lower().strip()
        
        risk_increase_keywords = ['agresivo', 'más riesgo', 'aumenta', 'sube el riesgo', 'quiero ganar más']
        risk_decrease_keywords = ['conservador', 'menos riesgo', 'baja', 'reduce el riesgo', 'más seguro', 'proteger']
        
        for keyword in risk_increase_keywords:
            if keyword in message_lower:
                return ('update_risk', {
                    'action': 'increase',
                    'suggested_profile': RiskProfile.AGGRESSIVE,
                    'message': message
                })
        
        for keyword in risk_decrease_keywords:
            if keyword in message_lower:
                return ('update_risk', {
                    'action': 'decrease', 
                    'suggested_profile': RiskProfile.CONSERVATIVE,
                    'message': message
                })
        
        import re
        max_patterns = [
            r'máximo[:\s]*\$?(\d+)',
            r'max[:\s]*\$?(\d+)',
            r'no más de[:\s]*\$?(\d+)',
            r'hasta[:\s]*\$?(\d+)\s*(?:por trade|usd|dólares)?'
        ]
        
        for pattern in max_patterns:
            match = re.search(pattern, message_lower)
            if match:
                amount = float(match.group(1))
                return ('update_limit', {
                    'type': 'max_trade',
                    'value': amount,
                    'message': message
                })
        
        min_patterns = [
            r'mínimo[:\s]*\$?(\d+)',
            r'min[:\s]*\$?(\d+)',
            r'al menos[:\s]*\$?(\d+)'
        ]
        
        for pattern in min_patterns:
            match = re.search(pattern, message_lower)
            if match:
                amount = float(match.group(1))
                return ('update_limit', {
                    'type': 'min_trade',
                    'value': amount,
                    'message': message
                })
        
        pause_keywords = ['pausa', 'para', 'detén', 'stop', 'pausar']
        if any(k in message_lower for k in pause_keywords):
            return ('pause', {'message': message})
        
        resume_keywords = ['reanuda', 'continúa', 'sigue', 'resume', 'reanudar']
        if any(k in message_lower for k in resume_keywords):
            return ('resume', {'message': message})
        
        auto_on = ['activa auto', 'enciende auto', 'trading automático on', 'automático activo']
        if any(k in message_lower for k in auto_on):
            return ('auto_trading', {'enable': True, 'message': message})
        
        auto_off = ['desactiva auto', 'apaga auto', 'trading automático off', 'automático desactivo']
        if any(k in message_lower for k in auto_off):
            return ('auto_trading', {'enable': False, 'message': message})
        
        return None
    
    def get_available_strategies(self) -> List[Dict]:
        """Obtener lista de estrategias disponibles"""
        return [
            {'id': 'EMA_REGIME', 'name': 'EMA Regime Signal', 'description': 'Señal principal basada en EMA (40 pts)', 'risk': 'medium'},
            {'id': 'HMM_REGIME', 'name': 'HMM Regime Detection', 'description': 'Detección de regímenes de mercado (25 pts)', 'risk': 'low'},
            {'id': 'KALMAN_FILTER', 'name': 'Kalman Filter', 'description': 'Filtrado adaptativo de señales (15 pts)', 'risk': 'low'},
            {'id': 'MEMORY_KERNEL', 'name': 'Non-Markovian Memory', 'description': 'Memoria temporal avanzada (15 pts)', 'risk': 'medium'},
            {'id': 'KELLY_CRITERION', 'name': 'Kelly Criterion', 'description': 'Optimización de tamaño de posición (10 pts)', 'risk': 'low'},
            {'id': 'MONTE_CARLO', 'name': 'Monte Carlo', 'description': 'Simulaciones probabilísticas (veto)', 'risk': 'medium'},
            {'id': 'BLACK_SWAN', 'name': 'Black Swan Detection', 'description': 'Detección de eventos extremos (veto)', 'risk': 'low'},
            {'id': 'COHERENCE_ENGINE', 'name': 'Coherence Engine', 'description': 'Validación de coherencia (veto)', 'risk': 'low'},
        ]
    
    def update_active_strategies(self, user_id: str, strategies: List[str]) -> Tuple[bool, str]:
        """Actualizar estrategias activas"""
        settings = self.get_user_settings(user_id)
        
        available = [s['id'] for s in self.get_available_strategies()]
        invalid = [s for s in strategies if s not in available]
        
        if invalid:
            return False, f"Estrategias no válidas: {', '.join(invalid)}"
        
        settings.active_strategies = strategies
        self.save_user_settings(settings)
        
        strategy_names = [s['name'] for s in self.get_available_strategies() if s['id'] in strategies]
        
        return True, f"""📈 **Estrategias Actualizadas**

Activas ({len(strategies)}):
{chr(10).join(['• ' + name for name in strategy_names])}

Estas estrategias serán utilizadas para generar señales de trading."""


_settings_service_instance: Optional[UserSettingsService] = None

def get_settings_service() -> UserSettingsService:
    """Obtener instancia singleton del servicio"""
    global _settings_service_instance
    if _settings_service_instance is None:
        _settings_service_instance = UserSettingsService()
    return _settings_service_instance
