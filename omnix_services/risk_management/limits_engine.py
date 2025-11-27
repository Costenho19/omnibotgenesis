"""
OMNIX V6.0 ULTRA - Limits Engine
================================
Motor de validación pre-trade de límites de riesgo.

Funciones principales:
- Validar órdenes antes de ejecución
- Verificar límites por operación, diarios, drawdown
- Calcular uso de límites en tiempo real

Creado: Nov 27, 2025
"""

import logging
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from omnix_services.risk_management.risk_models import (
    RiskLimitType, RiskSeverity, RiskAction, ThresholdUnit,
    RiskLimit, RiskBreach, RiskMetrics, RiskConfig, DEFAULT_LIMITS
)

logger = logging.getLogger(__name__)


@dataclass
class OrderValidationResult:
    """Resultado de validación de una orden"""
    is_valid: bool = True
    rejection_reason: Optional[str] = None
    breaches: List[RiskBreach] = None
    warnings: List[str] = None
    risk_score: int = 0
    
    def __post_init__(self):
        if self.breaches is None:
            self.breaches = []
        if self.warnings is None:
            self.warnings = []


class LimitsEngine:
    """
    Motor de límites de riesgo institucional.
    
    Valida todas las órdenes contra límites configurados antes de ejecución.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, database_service=None, config: RiskConfig = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.db = database_service
        self.config = config or RiskConfig.from_env()
        self._user_limits_cache: Dict[str, List[RiskLimit]] = {}
        self._daily_stats_cache: Dict[str, Dict] = {}
        self._cache_ttl = 60
        self._last_cache_update: Dict[str, datetime] = {}
        
        self._initialized = True
        logger.info("🛡️ LimitsEngine inicializado - Validación pre-trade activa")
        logger.info(f"   📊 Capital inicial: ${self.config.initial_capital:,.2f}")
        logger.info(f"   ⚠️  Warning threshold: {self.config.warning_threshold_pct}%")
        logger.info(f"   🚨 Critical threshold: {self.config.critical_threshold_pct}%")
    
    def validate_order(
        self,
        user_id: str,
        symbol: str,
        side: str,
        amount_usd: float,
        current_metrics: Optional[RiskMetrics] = None
    ) -> OrderValidationResult:
        """
        Validar una orden contra todos los límites configurados.
        
        Args:
            user_id: ID del usuario
            symbol: Par de trading (ej: BTC/USD)
            side: 'buy' o 'sell'
            amount_usd: Monto de la orden en USD
            current_metrics: Métricas actuales (opcional)
            
        Returns:
            OrderValidationResult con is_valid=True/False y detalles
        """
        result = OrderValidationResult()
        
        try:
            limits = self._get_user_limits(user_id)
            if not limits:
                limits = DEFAULT_LIMITS
            
            if current_metrics is None:
                current_metrics = self._get_current_metrics(user_id)
            
            for limit in limits:
                if not limit.is_active:
                    continue
                    
                breach = self._check_limit(
                    limit=limit,
                    order_amount=amount_usd,
                    symbol=symbol,
                    side=side,
                    metrics=current_metrics
                )
                
                if breach:
                    if breach.severity == RiskSeverity.HALT:
                        result.is_valid = False
                        result.rejection_reason = breach.description
                        result.breaches.append(breach)
                        logger.warning(f"🚫 Orden RECHAZADA: {breach.description}")
                    elif breach.severity == RiskSeverity.CRITICAL:
                        result.warnings.append(f"⚠️ CRÍTICO: {breach.description}")
                        result.breaches.append(breach)
                    elif breach.severity == RiskSeverity.WARNING:
                        result.warnings.append(f"⚠️ {breach.description}")
                        result.breaches.append(breach)
            
            result.risk_score = self._calculate_risk_score(current_metrics, result.breaches)
            
            if result.is_valid:
                logger.info(f"✅ Orden validada: {symbol} {side} ${amount_usd:,.2f} (Risk Score: {result.risk_score})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error validando orden: {e}")
            result.warnings.append(f"Error en validación: {str(e)}")
            return result
    
    def _check_limit(
        self,
        limit: RiskLimit,
        order_amount: float,
        symbol: str,
        side: str,
        metrics: RiskMetrics
    ) -> Optional[RiskBreach]:
        """Verificar un límite específico"""
        
        current_value = 0.0
        threshold = limit.threshold_value
        description = ""
        
        if limit.limit_type == RiskLimitType.PER_TRADE:
            if limit.threshold_unit == ThresholdUnit.PERCENT:
                threshold_usd = metrics.total_balance_usd * (threshold / 100)
                current_value = order_amount
                percentage_used = (order_amount / threshold_usd) * 100 if threshold_usd > 0 else 0
                description = f"Orden ${order_amount:,.2f} excede {threshold}% del capital (${threshold_usd:,.2f})"
            else:
                current_value = order_amount
                percentage_used = (order_amount / threshold) * 100 if threshold > 0 else 0
                description = f"Orden ${order_amount:,.2f} excede límite ${threshold:,.2f}"
                
        elif limit.limit_type == RiskLimitType.DAILY_LOSS:
            if limit.threshold_unit == ThresholdUnit.PERCENT:
                threshold_usd = metrics.total_balance_usd * (threshold / 100)
                current_value = abs(min(0, metrics.daily_pnl_usd))
                percentage_used = (current_value / threshold_usd) * 100 if threshold_usd > 0 else 0
                description = f"Pérdida diaria ${current_value:,.2f} ({metrics.daily_pnl_pct:.2f}%) vs límite {threshold}%"
            else:
                current_value = abs(min(0, metrics.daily_pnl_usd))
                percentage_used = (current_value / threshold) * 100 if threshold > 0 else 0
                description = f"Pérdida diaria ${current_value:,.2f} vs límite ${threshold:,.2f}"
                
        elif limit.limit_type == RiskLimitType.MAX_DRAWDOWN:
            if limit.threshold_unit == ThresholdUnit.PERCENT:
                current_value = metrics.current_drawdown_pct
                percentage_used = (current_value / threshold) * 100 if threshold > 0 else 0
                description = f"Drawdown actual {current_value:.2f}% vs límite {threshold}%"
            else:
                current_value = metrics.max_drawdown_usd
                percentage_used = (current_value / threshold) * 100 if threshold > 0 else 0
                description = f"Drawdown ${current_value:,.2f} vs límite ${threshold:,.2f}"
                
        elif limit.limit_type == RiskLimitType.PORTFOLIO_CONCENTRATION:
            position_value = metrics.positions_breakdown.get(symbol, 0) + order_amount
            current_value = (position_value / metrics.total_balance_usd) * 100 if metrics.total_balance_usd > 0 else 0
            percentage_used = (current_value / threshold) * 100 if threshold > 0 else 0
            description = f"Concentración en {symbol}: {current_value:.1f}% vs límite {threshold}%"
            
        elif limit.limit_type == RiskLimitType.DAILY_TRADES:
            current_value = metrics.daily_trades_count + 1
            percentage_used = (current_value / threshold) * 100 if threshold > 0 else 0
            description = f"Trades hoy: {int(current_value)} vs límite {int(threshold)}"
            
        elif limit.limit_type == RiskLimitType.OPEN_POSITIONS:
            current_value = metrics.open_positions + 1 if side == 'buy' else metrics.open_positions
            percentage_used = (current_value / threshold) * 100 if threshold > 0 else 0
            description = f"Posiciones abiertas: {int(current_value)} vs límite {int(threshold)}"
        
        else:
            return None
        
        severity = self._determine_severity(percentage_used)
        
        if severity != RiskSeverity.INFO:
            return RiskBreach(
                user_id=metrics.user_id,
                limit_type=limit.limit_type,
                severity=severity,
                current_value=current_value,
                threshold_value=threshold,
                percentage_used=percentage_used,
                action_taken=RiskAction.ORDER_REJECTED if severity == RiskSeverity.HALT else RiskAction.ALERT_SENT,
                description=description,
                created_at=datetime.now()
            )
        
        return None
    
    def _determine_severity(self, percentage_used: float) -> RiskSeverity:
        """Determinar severidad basada en porcentaje de uso"""
        if percentage_used >= 100:
            return RiskSeverity.HALT
        elif percentage_used >= self.config.critical_threshold_pct:
            return RiskSeverity.CRITICAL
        elif percentage_used >= self.config.warning_threshold_pct:
            return RiskSeverity.WARNING
        return RiskSeverity.INFO
    
    def _calculate_risk_score(self, metrics: RiskMetrics, breaches: List[RiskBreach]) -> int:
        """Calcular score de riesgo 1-100"""
        score = 0
        
        if metrics.current_drawdown_pct > 0:
            score += min(30, int(metrics.current_drawdown_pct * 3))
        
        if metrics.max_single_position_pct > 0:
            score += min(20, int(metrics.max_single_position_pct * 0.8))
        
        if metrics.daily_pnl_pct < 0:
            score += min(20, int(abs(metrics.daily_pnl_pct) * 10))
        
        score += min(15, len(breaches) * 5)
        
        if metrics.open_positions > 5:
            score += min(15, (metrics.open_positions - 5) * 3)
        
        return min(100, max(0, score))
    
    def _get_user_limits(self, user_id: str) -> List[RiskLimit]:
        """Obtener límites configurados del usuario"""
        cache_key = user_id
        now = datetime.now()
        
        if cache_key in self._user_limits_cache:
            last_update = self._last_cache_update.get(cache_key)
            if last_update and (now - last_update).seconds < self._cache_ttl:
                return self._user_limits_cache[cache_key]
        
        limits = []
        if self.db:
            try:
                db_limits = self.db.get_risk_limits(user_id)
                if db_limits:
                    for row in db_limits:
                        limits.append(RiskLimit(
                            id=row.get('id'),
                            user_id=row.get('user_id'),
                            limit_type=RiskLimitType(row.get('limit_type')),
                            threshold_value=row.get('threshold_value'),
                            threshold_unit=ThresholdUnit(row.get('threshold_unit')),
                            warning_threshold_pct=row.get('warning_threshold_pct', 80.0),
                            is_active=row.get('is_active', True),
                            cooldown_minutes=row.get('cooldown_minutes', 60)
                        ))
            except Exception as e:
                logger.warning(f"⚠️ Error obteniendo límites de BD: {e}")
        
        if not limits:
            limits = DEFAULT_LIMITS.copy()
        
        self._user_limits_cache[cache_key] = limits
        self._last_cache_update[cache_key] = now
        
        return limits
    
    def _get_current_metrics(self, user_id: str) -> RiskMetrics:
        """Obtener métricas actuales del usuario"""
        metrics = RiskMetrics(user_id=user_id)
        
        if self.db:
            try:
                balance_data = self.db.get_paper_trading_balance(user_id)
                if balance_data:
                    metrics.total_balance_usd = balance_data.get('balance', self.config.initial_capital)
                    metrics.available_balance_usd = balance_data.get('available', metrics.total_balance_usd)
                else:
                    metrics.total_balance_usd = self.config.initial_capital
                    metrics.available_balance_usd = self.config.initial_capital
                
                daily_stats = self.db.get_daily_trading_stats(user_id)
                if daily_stats:
                    metrics.daily_pnl_usd = daily_stats.get('daily_pnl', 0)
                    metrics.daily_pnl_pct = (metrics.daily_pnl_usd / metrics.total_balance_usd) * 100 if metrics.total_balance_usd > 0 else 0
                    metrics.daily_trades_count = daily_stats.get('trades_count', 0)
                
                positions = self.db.get_open_positions(user_id)
                if positions:
                    metrics.open_positions = len(positions)
                    total_position_value = 0
                    max_position = 0
                    for pos in positions:
                        value = pos.get('value_usd', 0)
                        symbol = pos.get('symbol', 'UNKNOWN')
                        metrics.positions_breakdown[symbol] = value
                        total_position_value += value
                        if value > max_position:
                            max_position = value
                    
                    metrics.total_exposure_usd = total_position_value
                    metrics.max_single_position_pct = (max_position / metrics.total_balance_usd) * 100 if metrics.total_balance_usd > 0 else 0
                
            except Exception as e:
                logger.warning(f"⚠️ Error obteniendo métricas: {e}")
        else:
            metrics.total_balance_usd = self.config.initial_capital
            metrics.available_balance_usd = self.config.initial_capital
        
        metrics.current_drawdown_pct = ((self.config.initial_capital - metrics.total_balance_usd) / self.config.initial_capital) * 100 if self.config.initial_capital > 0 else 0
        if metrics.current_drawdown_pct < 0:
            metrics.current_drawdown_pct = 0
        
        return metrics
    
    def get_limits_status(self, user_id: str) -> Dict[str, Any]:
        """Obtener estado actual de todos los límites"""
        limits = self._get_user_limits(user_id)
        metrics = self._get_current_metrics(user_id)
        
        status = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'risk_score': self._calculate_risk_score(metrics, []),
            'metrics': metrics.to_dict(),
            'limits': []
        }
        
        for limit in limits:
            breach = self._check_limit(limit, 0, '', '', metrics)
            limit_status = {
                'type': limit.limit_type.value,
                'threshold': limit.threshold_value,
                'unit': limit.threshold_unit.value,
                'is_active': limit.is_active,
                'current_usage': 0,
                'percentage_used': 0,
                'status': 'OK'
            }
            
            if breach:
                limit_status['current_usage'] = breach.current_value
                limit_status['percentage_used'] = breach.percentage_used
                limit_status['status'] = breach.severity.value.upper()
            
            status['limits'].append(limit_status)
        
        return status
    
    def set_limit(
        self,
        user_id: str,
        limit_type: RiskLimitType,
        threshold_value: float,
        threshold_unit: ThresholdUnit = ThresholdUnit.PERCENT
    ) -> bool:
        """Configurar un límite para un usuario"""
        try:
            if self.db:
                success = self.db.set_risk_limit(
                    user_id=user_id,
                    limit_type=limit_type.value,
                    threshold_value=threshold_value,
                    threshold_unit=threshold_unit.value
                )
                if success:
                    if user_id in self._user_limits_cache:
                        del self._user_limits_cache[user_id]
                    logger.info(f"✅ Límite {limit_type.value} configurado: {threshold_value} {threshold_unit.value}")
                return success
            return False
        except Exception as e:
            logger.error(f"❌ Error configurando límite: {e}")
            return False
    
    def clear_cache(self, user_id: Optional[str] = None):
        """Limpiar cache de límites"""
        if user_id:
            self._user_limits_cache.pop(user_id, None)
            self._last_cache_update.pop(user_id, None)
        else:
            self._user_limits_cache.clear()
            self._last_cache_update.clear()
