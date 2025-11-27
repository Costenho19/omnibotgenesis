"""
OMNIX V6.0 ULTRA - Risk Dashboard
==================================
Dashboard de riesgo para inversores.

Funciones principales:
- Generar resúmenes de riesgo
- Crear reportes para inversores
- Visualización de métricas
- Historial de eventos

Creado: Nov 27, 2025
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from omnix_services.risk_management.risk_models import (
    RiskMetrics, RiskConfig, RiskLimitType
)

logger = logging.getLogger(__name__)


class RiskDashboard:
    """
    Dashboard de riesgo para presentaciones a inversores.
    
    Genera resúmenes, métricas y reportes profesionales.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        database_service=None,
        limits_engine=None,
        position_monitor=None,
        circuit_breaker=None,
        config: RiskConfig = None
    ):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.db = database_service
        self.limits_engine = limits_engine
        self.position_monitor = position_monitor
        self.circuit_breaker = circuit_breaker
        self.config = config or RiskConfig.from_env()
        
        self._initialized = True
        logger.info("📊 RiskDashboard inicializado - Dashboard para inversores activo")
    
    def get_risk_summary(self, user_id: str) -> Dict[str, Any]:
        """Obtener resumen completo de riesgo"""
        
        metrics = None
        if self.position_monitor:
            metrics = self.position_monitor.get_risk_metrics(user_id)
        else:
            metrics = RiskMetrics(
                user_id=user_id,
                total_balance_usd=self.config.initial_capital,
                available_balance_usd=self.config.initial_capital
            )
        
        limits_status = None
        if self.limits_engine:
            limits_status = self.limits_engine.get_limits_status(user_id)
        
        halt_status = None
        if self.circuit_breaker:
            halt_status = self.circuit_breaker.get_halt_status(user_id).to_dict()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'overall_status': self._get_overall_status(metrics, halt_status),
            'risk_score': metrics.risk_score if metrics else 0,
            'trading_enabled': not (halt_status and halt_status.get('is_halted', False)),
            'metrics': metrics.to_dict() if metrics else {},
            'limits': limits_status.get('limits', []) if limits_status else [],
            'halt_status': halt_status,
            'recommendations': self._generate_recommendations(metrics, limits_status)
        }
    
    def get_telegram_summary(self, user_id: str) -> str:
        """Generar resumen formateado para Telegram"""
        
        summary = self.get_risk_summary(user_id)
        metrics = summary.get('metrics', {})
        
        status_emoji = {
            'HEALTHY': '🟢',
            'WARNING': '🟡',
            'CRITICAL': '🟠',
            'HALTED': '🔴'
        }
        
        status = summary.get('overall_status', 'UNKNOWN')
        emoji = status_emoji.get(status, '⚪')
        
        risk_bar = self._generate_risk_bar(summary.get('risk_score', 0))
        
        text = f"""
📊 **OMNIX RMS Dashboard**
━━━━━━━━━━━━━━━━━━━━

{emoji} Estado: **{status}**
🎯 Risk Score: {summary.get('risk_score', 0)}/100
{risk_bar}

💰 **Balance**
   Total: ${metrics.get('total_balance_usd', 0):,.2f}
   Disponible: ${metrics.get('available_balance_usd', 0):,.2f}
   Exposición: ${metrics.get('total_exposure_usd', 0):,.2f}

📈 **Rendimiento Hoy**
   P&L: ${metrics.get('daily_pnl_usd', 0):+,.2f}
   Cambio: {metrics.get('daily_pnl_pct', 0):+.2f}%

📉 **Riesgo**
   Drawdown: {metrics.get('current_drawdown_pct', 0):.2f}%
   Max Concentración: {metrics.get('max_single_position_pct', 0):.1f}%

📊 **Actividad**
   Posiciones: {metrics.get('open_positions', 0)}
   Trades hoy: {metrics.get('daily_trades_count', 0)}

🔒 Trading: {'✅ Activo' if summary.get('trading_enabled') else '❌ Detenido'}
━━━━━━━━━━━━━━━━━━━━
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return text
    
    def get_limits_summary(self, user_id: str) -> str:
        """Generar resumen de límites para Telegram"""
        
        if not self.limits_engine:
            return "❌ LimitsEngine no disponible"
        
        status = self.limits_engine.get_limits_status(user_id)
        
        text = """
🛡️ **Límites de Riesgo**
━━━━━━━━━━━━━━━━━━━━
"""
        
        for limit in status.get('limits', []):
            status_emoji = {
                'OK': '🟢',
                'WARNING': '🟡',
                'CRITICAL': '🟠',
                'HALT': '🔴'
            }
            
            emoji = status_emoji.get(limit.get('status', 'OK'), '⚪')
            pct = limit.get('percentage_used', 0)
            bar = self._generate_progress_bar(pct)
            
            limit_names = {
                'per_trade': 'Por Operación',
                'daily_loss': 'Pérdida Diaria',
                'max_drawdown': 'Max Drawdown',
                'portfolio_concentration': 'Concentración',
                'daily_trades': 'Trades/Día',
                'open_positions': 'Posiciones'
            }
            
            name = limit_names.get(limit.get('type', ''), limit.get('type', ''))
            value = limit.get('threshold', 0)
            unit = limit.get('unit', '')
            
            unit_symbol = '%' if unit == 'PERCENT' else ('$' if unit == 'USD' else '')
            
            text += f"\n{emoji} **{name}**\n"
            text += f"   Límite: {unit_symbol}{value:,.0f}\n"
            text += f"   Uso: {pct:.0f}% {bar}\n"
        
        text += f"\n━━━━━━━━━━━━━━━━━━━━"
        
        return text
    
    def get_investor_report(self, user_id: str, period_days: int = 30) -> Dict[str, Any]:
        """Generar reporte completo para inversores"""
        
        summary = self.get_risk_summary(user_id)
        
        historical = []
        if self.db:
            try:
                historical = self.db.get_risk_metrics_history(user_id, period_days)
            except:
                pass
        
        breach_history = []
        if self.db:
            try:
                breach_history = self.db.get_risk_breaches(user_id, period_days)
            except:
                pass
        
        stats = self._calculate_period_stats(historical)
        
        return {
            'report_date': datetime.now().isoformat(),
            'period_days': period_days,
            'user_id': user_id,
            'executive_summary': {
                'current_status': summary.get('overall_status'),
                'risk_score': summary.get('risk_score'),
                'capital_preservation': stats.get('capital_preservation_pct', 100),
                'max_drawdown_period': stats.get('max_drawdown', 0),
                'avg_risk_score': stats.get('avg_risk_score', 0),
                'total_breaches': len(breach_history),
                'critical_breaches': len([b for b in breach_history if b.get('severity') in ['critical', 'halt']])
            },
            'current_metrics': summary.get('metrics'),
            'limits_status': summary.get('limits'),
            'historical_metrics': historical,
            'breach_history': breach_history,
            'risk_controls': {
                'limits_configured': len(summary.get('limits', [])),
                'auto_halt_enabled': self.config.enable_auto_halt,
                'telegram_alerts_enabled': self.config.enable_telegram_alerts,
                'warning_threshold': self.config.warning_threshold_pct,
                'critical_threshold': self.config.critical_threshold_pct
            },
            'recommendations': summary.get('recommendations', [])
        }
    
    def _get_overall_status(self, metrics: RiskMetrics, halt_status: Optional[Dict]) -> str:
        """Determinar estado general del sistema"""
        
        if halt_status and halt_status.get('is_halted'):
            return 'HALTED'
        
        if metrics:
            if metrics.risk_score >= 80:
                return 'CRITICAL'
            elif metrics.risk_score >= 50:
                return 'WARNING'
        
        return 'HEALTHY'
    
    def _generate_recommendations(
        self,
        metrics: Optional[RiskMetrics],
        limits_status: Optional[Dict]
    ) -> List[str]:
        """Generar recomendaciones basadas en el estado actual"""
        
        recommendations = []
        
        if not metrics:
            return recommendations
        
        if metrics.max_single_position_pct > 20:
            recommendations.append(
                f"⚠️ Considerar reducir concentración en posición principal ({metrics.max_single_position_pct:.1f}%)"
            )
        
        if metrics.current_drawdown_pct > 5:
            recommendations.append(
                f"📉 Drawdown elevado ({metrics.current_drawdown_pct:.1f}%), considerar reducir exposición"
            )
        
        if metrics.daily_pnl_pct < -1:
            recommendations.append(
                "🔴 Pérdida diaria significativa, evaluar pausar operaciones"
            )
        
        if metrics.open_positions > 8:
            recommendations.append(
                f"📊 Muchas posiciones abiertas ({metrics.open_positions}), considerar consolidar"
            )
        
        if metrics.risk_score > 70:
            recommendations.append(
                f"🎯 Risk Score alto ({metrics.risk_score}), reducir actividad de trading"
            )
        
        if not recommendations:
            recommendations.append("✅ Sistema operando dentro de parámetros normales")
        
        return recommendations
    
    def _generate_risk_bar(self, score: int) -> str:
        """Generar barra visual de riesgo"""
        
        filled = score // 10
        empty = 10 - filled
        
        if score < 30:
            char = '🟢'
        elif score < 60:
            char = '🟡'
        elif score < 80:
            char = '🟠'
        else:
            char = '🔴'
        
        return char * filled + '⚪' * empty
    
    def _generate_progress_bar(self, percentage: float) -> str:
        """Generar barra de progreso"""
        
        filled = int(percentage / 10)
        empty = 10 - filled
        
        return '█' * filled + '░' * empty
    
    def _calculate_period_stats(self, historical: List[Dict]) -> Dict[str, Any]:
        """Calcular estadísticas del período"""
        
        if not historical:
            return {
                'capital_preservation_pct': 100,
                'max_drawdown': 0,
                'avg_risk_score': 0
            }
        
        initial_balance = historical[0].get('total_balance_usd', self.config.initial_capital)
        final_balance = historical[-1].get('total_balance_usd', initial_balance)
        
        capital_preservation = (final_balance / initial_balance) * 100 if initial_balance > 0 else 100
        
        max_drawdown = max(
            (h.get('current_drawdown_pct', 0) for h in historical),
            default=0
        )
        
        risk_scores = [h.get('risk_score', 0) for h in historical]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        return {
            'capital_preservation_pct': capital_preservation,
            'max_drawdown': max_drawdown,
            'avg_risk_score': avg_risk_score
        }
    
    def get_halt_history(self, user_id: str) -> str:
        """Obtener historial de halts formateado"""
        
        if not self.circuit_breaker:
            return "❌ CircuitBreaker no disponible"
        
        history = self.circuit_breaker.get_halt_history(user_id)
        
        if not history:
            return "✅ Sin historial de bloqueos"
        
        text = """
🛑 **Historial de Bloqueos**
━━━━━━━━━━━━━━━━━━━━
"""
        
        for halt in history[-5:]:
            halted_at = halt.get('halted_at', 'N/A')
            reason = halt.get('reason', 'Unknown')
            message = halt.get('message', '')
            
            text += f"\n📅 {halted_at[:19] if halted_at else 'N/A'}\n"
            text += f"   Razón: {reason}\n"
            if message:
                text += f"   {message[:50]}...\n" if len(message) > 50 else f"   {message}\n"
        
        return text
