"""
OMNIX V6.2 ULTRA - Alert Dispatcher (Memory-Enhanced)
======================================================
Sistema de alertas y notificaciones de riesgo con
alertas predictivas basadas en memoria Non-Markoviana.

Funciones principales:
- Enviar alertas por Telegram
- Logging de eventos de riesgo
- Resúmenes diarios
- Escalamiento de alertas
- NUEVO V6.2: Alertas predictivas de transición de régimen

Creado: Nov 27, 2025
Actualizado: Nov 29, 2025 - Memory-Enhanced Risk Management
"""

import logging
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from omnix_services.risk_management.risk_models import (
    RiskSeverity, RiskBreach, RiskMetrics, RiskConfig
)

logger = logging.getLogger(__name__)


class AlertChannel(Enum):
    """Canales de notificación"""
    TELEGRAM = 'telegram'
    LOG = 'log'
    EMAIL = 'email'
    WEBHOOK = 'webhook'


@dataclass
class AlertMessage:
    """Mensaje de alerta"""
    severity: RiskSeverity
    title: str
    message: str
    user_id: str
    channel: AlertChannel
    metadata: Optional[Dict] = None
    sent_at: Optional[datetime] = None
    delivered: bool = False


class AlertDispatcher:
    """
    Dispatcher de alertas de riesgo.
    
    Envía notificaciones multicanal sobre eventos de riesgo.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, telegram_bot=None, database_service=None, config: RiskConfig = None,
                 memory_adapter=None):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.telegram_bot = telegram_bot
        self.db = database_service
        self.config = config or RiskConfig.from_env()
        
        self._alert_history: Dict[str, List[AlertMessage]] = {}
        self._cooldowns: Dict[str, datetime] = {}
        self._alert_count_today: Dict[str, int] = {}
        
        self._max_alerts_per_day = 50
        self._cooldown_seconds = 30
        
        self._telegram_chat_ids: List[str] = []
        
        self._memory_adapter = memory_adapter
        self._enable_predictive_alerts = True
        self._last_predictive_check: Optional[datetime] = None
        self._predictive_alert_cooldown = 300
        
        self._initialized = True
        logger.info("📢 AlertDispatcher V6.2 inicializado - Notificaciones activas")
        logger.info(f"   📱 Telegram: {'Activo' if telegram_bot else 'No disponible'}")
        logger.info(f"   ⏱️ Cooldown: {self._cooldown_seconds}s entre alertas")
        logger.info(f"   🧠 Alertas predictivas: {'Activo' if memory_adapter else 'No disponible'}")
    
    def set_telegram_bot(self, telegram_bot) -> None:
        """
        Configurar bot de Telegram después de inicialización.
        
        Args:
            telegram_bot: Instancia del bot de Telegram (Application.bot)
        """
        self.telegram_bot = telegram_bot
        logger.info(f"📱 AlertDispatcher: Telegram bot {'conectado' if telegram_bot else 'desconectado'}")
    
    def add_alert_chat_id(self, chat_id: str) -> None:
        """Agregar chat ID para recibir alertas"""
        if chat_id not in self._telegram_chat_ids:
            self._telegram_chat_ids.append(chat_id)
            logger.info(f"📱 Chat ID {chat_id} agregado para alertas RMS")
    
    async def send_alert(
        self,
        user_id: str,
        severity: RiskSeverity,
        title: str,
        message: str,
        channels: List[AlertChannel] = None
    ) -> bool:
        """Enviar alerta por múltiples canales"""
        
        if channels is None:
            channels = [AlertChannel.LOG]
            if self.config.enable_telegram_alerts and self.telegram_bot:
                channels.append(AlertChannel.TELEGRAM)
        
        if not self._can_send_alert(user_id):
            logger.debug(f"⏸️ Alerta suprimida por cooldown para {user_id}")
            return False
        
        emoji_map = {
            RiskSeverity.INFO: 'ℹ️',
            RiskSeverity.WARNING: '⚠️',
            RiskSeverity.CRITICAL: '🚨',
            RiskSeverity.HALT: '🛑'
        }
        emoji = emoji_map.get(severity, '📢')
        
        formatted_message = self._format_alert(emoji, title, message, severity)
        
        success = False
        for channel in channels:
            try:
                if channel == AlertChannel.LOG:
                    self._send_log_alert(severity, title, message)
                    success = True
                    
                elif channel == AlertChannel.TELEGRAM:
                    if await self._send_telegram_alert(user_id, formatted_message):
                        success = True
                        
            except Exception as e:
                logger.error(f"❌ Error enviando alerta por {channel.value}: {e}")
        
        if success:
            self._record_alert(user_id, AlertMessage(
                severity=severity,
                title=title,
                message=message,
                user_id=user_id,
                channel=channels[0],
                sent_at=datetime.now(),
                delivered=True
            ))
        
        return success
    
    def send_alert_sync(
        self,
        user_id: str,
        severity: RiskSeverity,
        title: str,
        message: str
    ) -> bool:
        """Versión síncrona de send_alert (solo logging)"""
        
        if not self._can_send_alert(user_id):
            return False
        
        self._send_log_alert(severity, title, message)
        
        self._record_alert(user_id, AlertMessage(
            severity=severity,
            title=title,
            message=message,
            user_id=user_id,
            channel=AlertChannel.LOG,
            sent_at=datetime.now(),
            delivered=True
        ))
        
        return True
    
    def send_breach_alert(self, breach: RiskBreach) -> bool:
        """Enviar alerta desde una violación de límite"""
        
        severity_titles = {
            RiskSeverity.WARNING: 'Límite al 80%',
            RiskSeverity.CRITICAL: 'Límite CRÍTICO (95%)',
            RiskSeverity.HALT: 'TRADING DETENIDO'
        }
        
        title = severity_titles.get(breach.severity, 'Alerta de Riesgo')
        
        return self.send_alert_sync(
            user_id=breach.user_id,
            severity=breach.severity,
            title=title,
            message=breach.description
        )
    
    def send_halt_notification(
        self,
        user_id: str,
        reason: str,
        resume_at: Optional[datetime] = None
    ) -> bool:
        """Notificar que el trading fue detenido"""
        
        message = f"Trading detenido: {reason}"
        if resume_at:
            message += f"\n⏰ Reanudar: {resume_at.strftime('%H:%M:%S')}"
        
        return self.send_alert_sync(
            user_id=user_id,
            severity=RiskSeverity.HALT,
            title='🛑 TRADING HALTED',
            message=message
        )
    
    def send_resume_notification(self, user_id: str) -> bool:
        """Notificar que el trading fue reanudado"""
        
        return self.send_alert_sync(
            user_id=user_id,
            severity=RiskSeverity.INFO,
            title='✅ Trading Reanudado',
            message='El sistema de trading ha sido reactivado.'
        )
    
    def send_daily_summary(self, user_id: str, metrics: RiskMetrics) -> bool:
        """Enviar resumen diario de riesgos"""
        
        summary = self._format_daily_summary(metrics)
        
        return self.send_alert_sync(
            user_id=user_id,
            severity=RiskSeverity.INFO,
            title='📊 Resumen Diario de Riesgos',
            message=summary
        )
    
    def _format_alert(
        self,
        emoji: str,
        title: str,
        message: str,
        severity: RiskSeverity
    ) -> str:
        """Formatear mensaje de alerta"""
        
        severity_bar = {
            RiskSeverity.INFO: '▪️▪️▪️▪️▪️',
            RiskSeverity.WARNING: '🟡🟡🟡▪️▪️',
            RiskSeverity.CRITICAL: '🟠🟠🟠🟠▪️',
            RiskSeverity.HALT: '🔴🔴🔴🔴🔴'
        }
        
        return f"""
{emoji} **{title}**
{severity_bar.get(severity, '')}

{message}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    def _format_daily_summary(self, metrics: RiskMetrics) -> str:
        """Formatear resumen diario"""
        
        risk_emoji = '🟢' if metrics.risk_score < 30 else ('🟡' if metrics.risk_score < 60 else '🔴')
        pnl_emoji = '📈' if metrics.daily_pnl_usd >= 0 else '📉'
        
        return f"""
{risk_emoji} **Risk Score: {metrics.risk_score}/100**

💰 Balance: ${metrics.total_balance_usd:,.2f}
{pnl_emoji} P&L Hoy: ${metrics.daily_pnl_usd:,.2f} ({metrics.daily_pnl_pct:+.2f}%)

📊 Posiciones abiertas: {metrics.open_positions}
📉 Drawdown actual: {metrics.current_drawdown_pct:.2f}%
🔢 Trades hoy: {metrics.daily_trades_count}

🎯 Max concentración: {metrics.max_single_position_pct:.1f}%
"""
    
    def _send_log_alert(self, severity: RiskSeverity, title: str, message: str):
        """Enviar alerta a logs"""
        
        log_message = f"[RISK ALERT] {title}: {message}"
        
        if severity == RiskSeverity.HALT:
            logger.critical(log_message)
        elif severity == RiskSeverity.CRITICAL:
            logger.error(log_message)
        elif severity == RiskSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    async def _send_telegram_alert(self, user_id: str, message: str) -> bool:
        """Enviar alerta por Telegram"""
        
        if not self.telegram_bot:
            return False
        
        try:
            chat_id = int(user_id)
            await self.telegram_bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            logger.error(f"❌ Error enviando Telegram: {e}")
            return False
    
    def _can_send_alert(self, user_id: str) -> bool:
        """Verificar si podemos enviar alerta (cooldown + límite diario)"""
        
        now = datetime.now()
        
        last_alert = self._cooldowns.get(user_id)
        if last_alert:
            if (now - last_alert).seconds < self._cooldown_seconds:
                return False
        
        today_key = f"{user_id}_{now.date()}"
        count = self._alert_count_today.get(today_key, 0)
        if count >= self._max_alerts_per_day:
            return False
        
        self._cooldowns[user_id] = now
        self._alert_count_today[today_key] = count + 1
        
        return True
    
    def _record_alert(self, user_id: str, alert: AlertMessage):
        """Registrar alerta en historial"""
        
        if user_id not in self._alert_history:
            self._alert_history[user_id] = []
        
        self._alert_history[user_id].append(alert)
        
        if len(self._alert_history[user_id]) > 100:
            self._alert_history[user_id] = self._alert_history[user_id][-100:]
        
        if self.db:
            try:
                self.db.save_risk_alert(user_id, {
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'message': alert.message,
                    'channel': alert.channel.value,
                    'sent_at': alert.sent_at.isoformat() if alert.sent_at else None
                })
            except Exception as e:
                logger.warning(f"⚠️ Error guardando alerta en BD: {e}")
    
    def get_alert_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Obtener historial de alertas"""
        
        history = self._alert_history.get(user_id, [])
        return [
            {
                'severity': a.severity.value,
                'title': a.title,
                'message': a.message,
                'sent_at': a.sent_at.isoformat() if a.sent_at else None
            }
            for a in history[-limit:]
        ]
    
    def get_alert_stats(self, user_id: str) -> Dict[str, Any]:
        """Obtener estadísticas de alertas"""
        
        history = self._alert_history.get(user_id, [])
        today = datetime.now().date()
        
        today_alerts = [a for a in history if a.sent_at and a.sent_at.date() == today]
        
        by_severity = {}
        for a in today_alerts:
            sev = a.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        return {
            'total_today': len(today_alerts),
            'total_all_time': len(history),
            'by_severity': by_severity,
            'last_alert': history[-1].sent_at.isoformat() if history else None,
            'predictive_alerts_enabled': self._enable_predictive_alerts
        }
    
    def set_memory_adapter(self, memory_adapter) -> None:
        """Configurar adaptador de memoria después de inicialización"""
        self._memory_adapter = memory_adapter
        if memory_adapter:
            logger.info("🧠 AlertDispatcher: MemoryRiskAdapter conectado")
    
    def enable_predictive_alerts(self, enabled: bool = True) -> None:
        """Habilitar/deshabilitar alertas predictivas"""
        self._enable_predictive_alerts = enabled
        logger.info(f"🧠 Alertas predictivas: {'Activo' if enabled else 'Desactivado'}")
    
    def check_and_send_predictive_alerts(self, user_id: str, 
                                          current_price: float) -> List[Dict]:
        """
        Verificar y enviar alertas predictivas basadas en memoria.
        
        Esta función evalúa las métricas del kernel Non-Markoviano y
        envía alertas anticipatorias sobre cambios de régimen.
        
        Args:
            user_id: ID del usuario
            current_price: Precio actual del activo
            
        Returns:
            Lista de alertas enviadas
        """
        if not self._enable_predictive_alerts or not self._memory_adapter:
            return []
        
        now = datetime.now()
        if (self._last_predictive_check and 
            (now - self._last_predictive_check).seconds < self._predictive_alert_cooldown):
            return []
        
        self._last_predictive_check = now
        
        sent_alerts = []
        
        try:
            predictive_alerts = self._memory_adapter.get_predictive_alerts()
            
            for alert in predictive_alerts:
                severity_map = {
                    'critical': RiskSeverity.CRITICAL,
                    'warning': RiskSeverity.WARNING,
                    'info': RiskSeverity.INFO
                }
                severity = severity_map.get(alert.get('severity', 'info'), RiskSeverity.INFO)
                
                alert_type = alert.get('type', 'MEMORY_ALERT')
                title = self._get_predictive_alert_title(alert_type)
                message = alert.get('message', 'Alerta de memoria detectada')
                
                if alert.get('recommended_action'):
                    message += f"\n\n📋 Recomendación: {alert['recommended_action']}"
                
                success = self.send_alert_sync(
                    user_id=user_id,
                    severity=severity,
                    title=title,
                    message=message
                )
                
                if success:
                    sent_alerts.append({
                        'type': alert_type,
                        'severity': alert.get('severity'),
                        'sent_at': now.isoformat()
                    })
        
        except Exception as e:
            logger.error(f"❌ Error enviando alertas predictivas: {e}")
        
        return sent_alerts
    
    def _get_predictive_alert_title(self, alert_type: str) -> str:
        """Obtener título formateado para alerta predictiva"""
        titles = {
            'REGIME_TRANSITION': '🔮 Transición de Régimen Detectada',
            'COHERENCE_LOSS': '🧠 Pérdida de Coherencia Temporal',
            'VOLATILITY_INCREASE': '📊 Aumento de Volatilidad Esperado',
            'VOLATILITY_DECREASE': '📉 Disminución de Volatilidad Esperada',
            'MEMORY_ALERT': '🧠 Alerta de Memoria Non-Markoviana'
        }
        return titles.get(alert_type, f'🔮 {alert_type}')
    
    async def send_predictive_alert_async(
        self,
        user_id: str,
        alert_type: str,
        message: str,
        recommended_action: str = '',
        severity: str = 'warning'
    ) -> bool:
        """
        Enviar alerta predictiva asíncrona con formato especial.
        
        Args:
            user_id: ID del usuario
            alert_type: Tipo de alerta (REGIME_TRANSITION, COHERENCE_LOSS, etc.)
            message: Mensaje de la alerta
            recommended_action: Acción recomendada (opcional)
            severity: Severidad ('info', 'warning', 'critical')
            
        Returns:
            True si se envió correctamente
        """
        severity_map = {
            'critical': RiskSeverity.CRITICAL,
            'warning': RiskSeverity.WARNING,
            'info': RiskSeverity.INFO
        }
        risk_severity = severity_map.get(severity, RiskSeverity.INFO)
        
        title = self._get_predictive_alert_title(alert_type)
        
        full_message = f"🔮 **ALERTA PREDICTIVA**\n\n{message}"
        if recommended_action:
            full_message += f"\n\n📋 **Acción Recomendada:**\n{recommended_action}"
        
        return await self.send_alert(
            user_id=user_id,
            severity=risk_severity,
            title=title,
            message=full_message
        )
    
    def send_regime_transition_alert(self, user_id: str, 
                                      transition_risk: float,
                                      coherence_level: float) -> bool:
        """
        Enviar alerta específica de transición de régimen.
        
        Args:
            user_id: ID del usuario
            transition_risk: Riesgo de transición (0-100)
            coherence_level: Nivel de coherencia (0-100)
            
        Returns:
            True si se envió correctamente
        """
        severity = RiskSeverity.CRITICAL if transition_risk > 80 else RiskSeverity.WARNING
        
        message = f"""
🔮 **Transición de Régimen Detectada**

📊 Riesgo de transición: {transition_risk:.1f}%
🧠 Coherencia temporal: {coherence_level:.1f}%

El kernel Non-Markoviano ha detectado patrones que indican
un posible cambio de régimen de mercado inminente.

📋 **Recomendaciones:**
• Reducir tamaño de posiciones nuevas
• Ajustar stops más conservadores
• Monitorear volatilidad de cerca
"""
        
        return self.send_alert_sync(
            user_id=user_id,
            severity=severity,
            title='🔮 Transición de Régimen',
            message=message
        )
    
    def send_memory_coherence_alert(self, user_id: str,
                                     coherence_risk: float,
                                     regime_stability: float) -> bool:
        """
        Enviar alerta de pérdida de coherencia temporal.
        
        Args:
            user_id: ID del usuario
            coherence_risk: Riesgo por pérdida de coherencia (0-100)
            regime_stability: Estabilidad del régimen (0-100)
            
        Returns:
            True si se envió correctamente
        """
        severity = RiskSeverity.CRITICAL if coherence_risk > 80 else RiskSeverity.WARNING
        
        message = f"""
🧠 **Pérdida de Coherencia Temporal**

⚠️ Riesgo por incoherencia: {coherence_risk:.1f}%
📊 Estabilidad del régimen: {regime_stability:.1f}%

La memoria temporal del mercado muestra signos de
decoherencia, lo que reduce la predictibilidad.

📋 **Recomendaciones:**
• Operar con cautela adicional
• Preferir posiciones más pequeñas
• Esperar estabilización antes de nuevas entradas
"""
        
        return self.send_alert_sync(
            user_id=user_id,
            severity=severity,
            title='🧠 Coherencia Temporal Baja',
            message=message
        )
