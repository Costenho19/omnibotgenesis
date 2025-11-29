"""
OMNIX V6.2 ULTRA - Position Monitor (Memory-Enhanced)
======================================================
Monitoreo en tiempo real de posiciones y exposición con
ajuste de riesgo basado en memoria Non-Markoviana.

Funciones principales:
- Tracking de posiciones abiertas
- Cálculo de exposición total
- Snapshots diarios de métricas
- Detección de concentración excesiva
- NUEVO V6.2: Factor de riesgo por divergencia de memoria

Creado: Nov 27, 2025
Actualizado: Nov 29, 2025 - Memory-Enhanced Risk Management
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, date
from dataclasses import dataclass

from omnix_services.risk_management.risk_models import (
    RiskMetrics, RiskConfig, RiskLimitType
)

logger = logging.getLogger(__name__)


@dataclass
class PositionInfo:
    """Información de una posición"""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    value_usd: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    weight_pct: float
    opened_at: Optional[datetime] = None


class PositionMonitor:
    """
    Monitor de posiciones en tiempo real.
    
    Rastrea todas las posiciones abiertas y calcula métricas de riesgo.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, database_service=None, trading_service=None, config: RiskConfig = None,
                 memory_adapter=None):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.db = database_service
        self.trading_service = trading_service
        self.config = config or RiskConfig.from_env()
        
        self._positions_cache: Dict[str, List[PositionInfo]] = {}
        self._metrics_cache: Dict[str, RiskMetrics] = {}
        self._last_snapshot: Dict[str, date] = {}
        
        self._memory_adapter = memory_adapter
        self._enable_memory_adjustment = True
        self._memory_risk_factor = 1.0
        
        self._initialized = True
        logger.info("📊 PositionMonitor V6.2 inicializado - Tracking en tiempo real activo")
        logger.info(f"   🧠 Memory-Enhanced: {'Activo' if memory_adapter else 'No disponible'}")
    
    def set_trading_service(self, trading_service):
        """Configurar trading_service después de la inicialización"""
        self.trading_service = trading_service
        if trading_service:
            logger.info("📊 PositionMonitor: TradingService configurado correctamente")
    
    def get_current_positions(self, user_id: str) -> List[PositionInfo]:
        """Obtener todas las posiciones abiertas del usuario"""
        positions = []
        
        try:
            if self.db:
                db_positions = self.db.get_open_positions(user_id)
                if db_positions:
                    total_value = sum(p.get('value_usd', 0) for p in db_positions)
                    
                    for pos in db_positions:
                        entry_price = pos.get('entry_price', 0)
                        current_price = pos.get('current_price', entry_price)
                        quantity = pos.get('quantity', 0)
                        value_usd = pos.get('value_usd', quantity * current_price)
                        
                        unrealized_pnl = (current_price - entry_price) * quantity
                        if pos.get('side', 'buy') == 'sell':
                            unrealized_pnl = -unrealized_pnl
                        
                        unrealized_pnl_pct = (unrealized_pnl / (entry_price * quantity)) * 100 if entry_price * quantity > 0 else 0
                        weight_pct = (value_usd / total_value) * 100 if total_value > 0 else 0
                        
                        positions.append(PositionInfo(
                            symbol=pos.get('symbol', 'UNKNOWN'),
                            side=pos.get('side', 'buy'),
                            quantity=quantity,
                            entry_price=entry_price,
                            current_price=current_price,
                            value_usd=value_usd,
                            unrealized_pnl=unrealized_pnl,
                            unrealized_pnl_pct=unrealized_pnl_pct,
                            weight_pct=weight_pct,
                            opened_at=pos.get('opened_at')
                        ))
            
            self._positions_cache[user_id] = positions
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo posiciones: {e}")
        
        return positions
    
    def get_exposure_summary(self, user_id: str) -> Dict[str, Any]:
        """Obtener resumen de exposición del portafolio"""
        positions = self.get_current_positions(user_id)
        
        total_exposure = sum(p.value_usd for p in positions)
        total_unrealized_pnl = sum(p.unrealized_pnl for p in positions)
        
        exposure_by_asset = {}
        for pos in positions:
            if pos.symbol not in exposure_by_asset:
                exposure_by_asset[pos.symbol] = 0
            exposure_by_asset[pos.symbol] += pos.value_usd
        
        max_concentration = 0
        max_concentration_asset = ''
        if total_exposure > 0:
            for symbol, value in exposure_by_asset.items():
                concentration = (value / total_exposure) * 100
                if concentration > max_concentration:
                    max_concentration = concentration
                    max_concentration_asset = symbol
        
        balance = self.config.initial_capital
        if self.db:
            try:
                balance_data = self.db.get_paper_trading_balance(user_id)
                if balance_data:
                    balance = balance_data.get('balance', self.config.initial_capital)
            except:
                pass
        
        return {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'total_balance': balance,
            'total_exposure': total_exposure,
            'exposure_pct': (total_exposure / balance) * 100 if balance > 0 else 0,
            'available_balance': balance - total_exposure,
            'open_positions': len(positions),
            'total_unrealized_pnl': total_unrealized_pnl,
            'unrealized_pnl_pct': (total_unrealized_pnl / balance) * 100 if balance > 0 else 0,
            'exposure_by_asset': exposure_by_asset,
            'max_concentration_pct': max_concentration,
            'max_concentration_asset': max_concentration_asset,
            'positions': [
                {
                    'symbol': p.symbol,
                    'side': p.side,
                    'quantity': p.quantity,
                    'value_usd': p.value_usd,
                    'weight_pct': p.weight_pct,
                    'unrealized_pnl': p.unrealized_pnl,
                    'unrealized_pnl_pct': p.unrealized_pnl_pct
                }
                for p in positions
            ]
        }
    
    def get_risk_metrics(self, user_id: str) -> RiskMetrics:
        """Calcular métricas de riesgo actuales"""
        exposure = self.get_exposure_summary(user_id)
        
        metrics = RiskMetrics(
            user_id=user_id,
            snapshot_date=datetime.now(),
            total_balance_usd=exposure['total_balance'],
            total_exposure_usd=exposure['total_exposure'],
            available_balance_usd=exposure['available_balance'],
            open_positions=exposure['open_positions'],
            max_single_position_pct=exposure['max_concentration_pct'],
            positions_breakdown=exposure['exposure_by_asset']
        )
        
        if self.db:
            try:
                daily_stats = self.db.get_daily_trading_stats(user_id)
                if daily_stats:
                    metrics.daily_pnl_usd = daily_stats.get('daily_pnl', 0)
                    metrics.daily_trades_count = daily_stats.get('trades_count', 0)
                    if metrics.total_balance_usd > 0:
                        metrics.daily_pnl_pct = (metrics.daily_pnl_usd / metrics.total_balance_usd) * 100
            except:
                pass
        
        if self.config.initial_capital > 0:
            metrics.current_drawdown_pct = max(0, 
                ((self.config.initial_capital - metrics.total_balance_usd) / self.config.initial_capital) * 100
            )
            metrics.max_drawdown_pct = metrics.current_drawdown_pct
            metrics.max_drawdown_usd = self.config.initial_capital - metrics.total_balance_usd
        
        metrics.risk_score = self._calculate_risk_score(metrics)
        
        self._metrics_cache[user_id] = metrics
        
        return metrics
    
    def _calculate_risk_score(self, metrics: RiskMetrics) -> int:
        """Calcular score de riesgo 1-100"""
        score = 0
        
        if metrics.current_drawdown_pct > 0:
            score += min(30, int(metrics.current_drawdown_pct * 3))
        
        if metrics.max_single_position_pct > 0:
            score += min(20, int(metrics.max_single_position_pct * 0.8))
        
        if metrics.daily_pnl_pct < 0:
            score += min(20, int(abs(metrics.daily_pnl_pct) * 10))
        
        if metrics.total_balance_usd > 0:
            exposure_ratio = metrics.total_exposure_usd / metrics.total_balance_usd
            score += min(15, int(exposure_ratio * 15))
        
        if metrics.open_positions > 5:
            score += min(15, (metrics.open_positions - 5) * 3)
        
        return min(100, max(0, score))
    
    def save_daily_snapshot(self, user_id: str) -> bool:
        """Guardar snapshot diario de métricas"""
        today = date.today()
        
        if self._last_snapshot.get(user_id) == today:
            logger.info(f"📸 Snapshot ya guardado hoy para {user_id}")
            return True
        
        try:
            metrics = self.get_risk_metrics(user_id)
            
            if self.db:
                success = self.db.save_risk_metrics_snapshot(
                    user_id=user_id,
                    snapshot_date=today,
                    metrics=metrics.to_dict()
                )
                
                if success:
                    self._last_snapshot[user_id] = today
                    logger.info(f"📸 Snapshot diario guardado para {user_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error guardando snapshot: {e}")
            return False
    
    def get_historical_metrics(self, user_id: str, days: int = 30) -> List[Dict]:
        """Obtener historial de métricas"""
        if self.db:
            try:
                return self.db.get_risk_metrics_history(user_id, days)
            except Exception as e:
                logger.error(f"❌ Error obteniendo historial: {e}")
        return []
    
    def check_concentration_alerts(self, user_id: str) -> List[str]:
        """Verificar alertas de concentración"""
        alerts = []
        exposure = self.get_exposure_summary(user_id)
        
        max_allowed = self.config.default_max_concentration_pct
        
        for symbol, value in exposure['exposure_by_asset'].items():
            if exposure['total_exposure'] > 0:
                concentration = (value / exposure['total_exposure']) * 100
                if concentration > max_allowed:
                    alerts.append(
                        f"⚠️ {symbol}: {concentration:.1f}% del portafolio (límite: {max_allowed}%)"
                    )
                elif concentration > max_allowed * 0.8:
                    alerts.append(
                        f"⚡ {symbol}: {concentration:.1f}% del portafolio (acercándose al límite)"
                    )
        
        return alerts
    
    def get_position_by_symbol(self, user_id: str, symbol: str) -> Optional[PositionInfo]:
        """Obtener posición específica por símbolo"""
        positions = self.get_current_positions(user_id)
        for pos in positions:
            if pos.symbol == symbol:
                return pos
        return None
    
    def clear_cache(self, user_id: Optional[str] = None):
        """Limpiar cache"""
        if user_id:
            self._positions_cache.pop(user_id, None)
            self._metrics_cache.pop(user_id, None)
        else:
            self._positions_cache.clear()
            self._metrics_cache.clear()
    
    def set_memory_adapter(self, memory_adapter) -> None:
        """Configurar adaptador de memoria después de inicialización"""
        self._memory_adapter = memory_adapter
        if memory_adapter:
            logger.info("🧠 PositionMonitor: MemoryRiskAdapter conectado")
    
    def enable_memory_adjustment(self, enabled: bool = True) -> None:
        """Habilitar/deshabilitar ajuste por memoria"""
        self._enable_memory_adjustment = enabled
        logger.info(f"🧠 Memory adjustment: {'Activo' if enabled else 'Desactivado'}")
    
    def get_memory_risk_factor(self) -> float:
        """
        Obtener factor de riesgo basado en memoria Non-Markoviana.
        
        Este factor ajusta el riesgo de posiciones basándose en:
        1. Divergencia de memoria (tensión precio/memoria histórica)
        2. Coherencia de régimen (estabilidad del mercado)
        3. Riesgo de transición (cambio de régimen inminente)
        
        Returns:
            Factor multiplicador [0.3, 2.0] para el risk score
        """
        if not self._enable_memory_adjustment or not self._memory_adapter:
            return 1.0
        
        try:
            factor = self._memory_adapter.get_position_risk_factor()
            self._memory_risk_factor = factor
            return factor
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo factor de memoria: {e}")
            return 1.0
    
    def get_memory_enhanced_risk_metrics(self, user_id: str, 
                                          current_price: float) -> RiskMetrics:
        """
        Obtener métricas de riesgo mejoradas con análisis de memoria.
        
        Extiende get_risk_metrics añadiendo:
        1. Ajuste de risk_score por coherencia temporal
        2. Volatility_index mejorado con predicción de cambio
        3. Alertas predictivas en metadata
        
        Args:
            user_id: ID del usuario
            current_price: Precio actual del activo principal
            
        Returns:
            RiskMetrics con análisis de memoria integrado
        """
        metrics = self.get_risk_metrics(user_id)
        
        if not self._memory_adapter or not self._enable_memory_adjustment:
            return metrics
        
        try:
            memory_metrics = self._memory_adapter.compute_memory_risk(current_price)
            
            memory_adjustment = int(memory_metrics.overall_memory_risk * 0.25)
            metrics.risk_score = min(100, metrics.risk_score + memory_adjustment)
            
            if memory_metrics.predicted_volatility_change > 0:
                metrics.volatility_index = min(100, 
                    metrics.volatility_index + memory_metrics.predicted_volatility_change)
            
        except Exception as e:
            logger.warning(f"⚠️ Error en métricas mejoradas: {e}")
        
        return metrics
    
    def check_memory_concentration_alerts(self, user_id: str, 
                                           current_price: float) -> List[str]:
        """
        Verificar alertas de concentración mejoradas con memoria.
        
        Combina alertas tradicionales con alertas predictivas del kernel.
        
        Args:
            user_id: ID del usuario
            current_price: Precio actual
            
        Returns:
            Lista combinada de alertas
        """
        alerts = self.check_concentration_alerts(user_id)
        
        if not self._memory_adapter or not self._enable_memory_adjustment:
            return alerts
        
        try:
            predictive_alerts = self._memory_adapter.get_predictive_alerts()
            for alert in predictive_alerts:
                if alert['severity'] in ['critical', 'warning']:
                    alerts.append(f"🧠 {alert['message']}")
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo alertas predictivas: {e}")
        
        return alerts
    
    def get_position_sizing_recommendation(self, user_id: str, 
                                            base_size_usd: float,
                                            current_price: float) -> Dict[str, Any]:
        """
        Obtener recomendación de tamaño de posición ajustado por memoria.
        
        Args:
            user_id: ID del usuario
            base_size_usd: Tamaño base de la posición en USD
            current_price: Precio actual del activo
            
        Returns:
            Diccionario con tamaño recomendado y justificación
        """
        result = {
            'base_size_usd': base_size_usd,
            'recommended_size_usd': base_size_usd,
            'adjustment_factor': 1.0,
            'memory_risk_level': 'stable',
            'reasoning': []
        }
        
        exposure = self.get_exposure_summary(user_id)
        
        if exposure['exposure_pct'] > 70:
            result['adjustment_factor'] *= 0.7
            result['reasoning'].append(
                f"Exposición alta ({exposure['exposure_pct']:.1f}%) - reducción 30%"
            )
        
        if exposure['max_concentration_pct'] > 20:
            result['adjustment_factor'] *= 0.8
            result['reasoning'].append(
                f"Concentración alta ({exposure['max_concentration_pct']:.1f}%) - reducción 20%"
            )
        
        if self._memory_adapter and self._enable_memory_adjustment:
            try:
                memory_factor = self._memory_adapter.get_position_risk_factor()
                if memory_factor < 1.0:
                    result['adjustment_factor'] *= memory_factor
                    
                    memory_metrics = self._memory_adapter.compute_memory_risk(current_price)
                    result['memory_risk_level'] = memory_metrics.risk_level.value
                    result['reasoning'].append(
                        f"Riesgo de memoria ({result['memory_risk_level']}) - factor {memory_factor:.1f}x"
                    )
            except Exception as e:
                logger.warning(f"⚠️ Error en recomendación de memoria: {e}")
        
        result['recommended_size_usd'] = base_size_usd * result['adjustment_factor']
        
        return result
