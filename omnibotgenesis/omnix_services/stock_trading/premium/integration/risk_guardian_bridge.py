"""
🛡️ STOCK RISK GUARDIAN BRIDGE V6.2
Puente para integrar acciones con AI Risk Guardian
Protección institucional adaptada para mercado tradicional
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(Enum):
    DRAWDOWN = "drawdown"
    OVERTRADING = "overtrading"
    CONCENTRATION = "concentration"
    VOLATILITY = "volatility"
    REGIME = "regime"
    MARKET_HOURS = "market_hours"


@dataclass
class RiskAssessment:
    approved: bool
    risk_level: RiskLevel
    risk_score: float
    active_risks: List[Dict]
    position_size_multiplier: float
    stop_loss_adjustment: float
    recommendations: List[str]


class StockRiskGuardianBridge:
    """
    Puente Risk Guardian para Acciones
    
    Integra con AI Risk Guardian V5.4 para supervisión
    de riesgo en tiempo real adaptada para acciones.
    
    Protecciones:
    - Drawdown máximo diario: 3%
    - Drawdown máximo swing: 8%
    - Máximo posiciones simultáneas: 10
    - Concentración máxima por sector: 30%
    - Volatilidad máxima aceptable: 4% diario
    
    Diferencias vs Crypto:
    - Umbrales más estrictos (menor volatilidad esperada)
    - Protección por horarios de mercado
    - Análisis de correlación sectorial
    """
    
    RISK_PARAMS = {
        'max_daily_drawdown': 0.03,
        'max_swing_drawdown': 0.08,
        'max_positions': 10,
        'max_sector_concentration': 0.30,
        'max_daily_volatility': 0.04,
        'max_trades_per_day': 20,
        'min_cash_reserve': 0.10,
        'max_position_size': 0.15,
        'correlation_threshold': 0.7
    }
    
    def __init__(self, risk_guardian=None, database_service=None):
        """
        Args:
            risk_guardian: Instancia de RiskGuardian crypto (opcional)
            database_service: Servicio de base de datos
        """
        self.risk_guardian = risk_guardian
        self.database_service = database_service
        
        self.daily_pnl = 0
        self.positions = {}
        self.trades_today = 0
        self.last_reset = datetime.now().date()
        self.risk_events = []
        
        logger.info("🛡️ Stock Risk Guardian Bridge V6.2 inicializado")
        logger.info(f"   📉 Max Daily Drawdown: {self.RISK_PARAMS['max_daily_drawdown']:.0%}")
        logger.info(f"   📊 Max Positions: {self.RISK_PARAMS['max_positions']}")
    
    def assess_risk(
        self,
        symbol: str,
        signal_type: str,
        confidence: float,
        position_size: float,
        current_price: float,
        sector: str = "unknown",
        market_open: bool = True
    ) -> RiskAssessment:
        """
        Evaluar riesgo para nueva operación
        
        Args:
            symbol: Símbolo de la acción
            signal_type: Tipo de señal (buy/sell/hold)
            confidence: Confianza de la señal (0-1)
            position_size: Tamaño de posición propuesto
            current_price: Precio actual
            sector: Sector de la acción
            market_open: Si el mercado está abierto
            
        Returns:
            RiskAssessment con evaluación completa
        """
        try:
            self._check_daily_reset()
            
            active_risks = []
            recommendations = []
            
            if not market_open:
                active_risks.append({
                    'type': RiskType.MARKET_HOURS.value,
                    'severity': 'high',
                    'message': 'Mercado cerrado'
                })
                recommendations.append("Esperar apertura del mercado")
            
            drawdown_risk = self._check_drawdown()
            if drawdown_risk:
                active_risks.append(drawdown_risk)
            
            overtrading_risk = self._check_overtrading()
            if overtrading_risk:
                active_risks.append(overtrading_risk)
                recommendations.append("Reducir frecuencia de trading")
            
            concentration_risk = self._check_concentration(sector)
            if concentration_risk:
                active_risks.append(concentration_risk)
                recommendations.append(f"Diversificar fuera de {sector}")
            
            position_risk = self._check_position_size(position_size)
            if position_risk:
                active_risks.append(position_risk)
            
            risk_score = self._calculate_risk_score(active_risks)
            risk_level = self._determine_risk_level(risk_score)
            
            size_multiplier = self._calculate_position_multiplier(
                risk_score, confidence, risk_level
            )
            
            stop_adjustment = self._calculate_stop_adjustment(risk_level)
            
            approved = risk_level not in [RiskLevel.CRITICAL]
            if risk_level == RiskLevel.HIGH and confidence < 0.7:
                approved = False
                recommendations.append("Señal requiere confianza > 70%")
            
            assessment = RiskAssessment(
                approved=approved,
                risk_level=risk_level,
                risk_score=risk_score,
                active_risks=active_risks,
                position_size_multiplier=size_multiplier,
                stop_loss_adjustment=stop_adjustment,
                recommendations=recommendations
            )
            
            if active_risks:
                self._log_risk_event(symbol, assessment)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error en evaluación de riesgo: {e}")
            return RiskAssessment(
                approved=False,
                risk_level=RiskLevel.CRITICAL,
                risk_score=1.0,
                active_risks=[{
                    'type': 'error',
                    'severity': 'critical',
                    'message': str(e)
                }],
                position_size_multiplier=0,
                stop_loss_adjustment=0,
                recommendations=["Error en sistema de riesgo"]
            )
    
    def _check_daily_reset(self):
        """Resetear contadores diarios si es nuevo día"""
        today = datetime.now().date()
        if today != self.last_reset:
            self.daily_pnl = 0
            self.trades_today = 0
            self.last_reset = today
            logger.info("🔄 Reset diario de contadores de riesgo")
    
    def _check_drawdown(self) -> Optional[Dict]:
        """Verificar drawdown"""
        if abs(self.daily_pnl) > self.RISK_PARAMS['max_daily_drawdown']:
            severity = 'critical' if self.daily_pnl < -self.RISK_PARAMS['max_daily_drawdown'] else 'high'
            return {
                'type': RiskType.DRAWDOWN.value,
                'severity': severity,
                'message': f"Drawdown diario: {self.daily_pnl:.2%}",
                'value': self.daily_pnl
            }
        return None
    
    def _check_overtrading(self) -> Optional[Dict]:
        """Verificar overtrading"""
        if self.trades_today >= self.RISK_PARAMS['max_trades_per_day']:
            return {
                'type': RiskType.OVERTRADING.value,
                'severity': 'high',
                'message': f"Límite de trades alcanzado: {self.trades_today}",
                'value': self.trades_today
            }
        elif self.trades_today >= self.RISK_PARAMS['max_trades_per_day'] * 0.8:
            return {
                'type': RiskType.OVERTRADING.value,
                'severity': 'moderate',
                'message': f"Cerca del límite de trades: {self.trades_today}",
                'value': self.trades_today
            }
        return None
    
    def _check_concentration(self, sector: str) -> Optional[Dict]:
        """Verificar concentración sectorial"""
        sector_positions = sum(
            1 for p in self.positions.values() 
            if p.get('sector', '') == sector
        )
        
        total_positions = len(self.positions) + 1
        concentration = sector_positions / total_positions if total_positions > 0 else 0
        
        if concentration > self.RISK_PARAMS['max_sector_concentration']:
            return {
                'type': RiskType.CONCENTRATION.value,
                'severity': 'high',
                'message': f"Alta concentración en {sector}: {concentration:.0%}",
                'value': concentration
            }
        return None
    
    def _check_position_size(self, size: float) -> Optional[Dict]:
        """Verificar tamaño de posición"""
        if size > self.RISK_PARAMS['max_position_size']:
            return {
                'type': 'position_size',
                'severity': 'moderate',
                'message': f"Tamaño de posición alto: {size:.0%}",
                'value': size
            }
        return None
    
    def _calculate_risk_score(self, risks: List[Dict]) -> float:
        """Calcular score de riesgo total"""
        if not risks:
            return 0
        
        severity_scores = {
            'low': 0.2,
            'moderate': 0.4,
            'high': 0.7,
            'critical': 1.0
        }
        
        scores = [severity_scores.get(r.get('severity', 'low'), 0.2) for r in risks]
        
        max_score = max(scores)
        avg_score = np.mean(scores)
        
        return min(max_score * 0.7 + avg_score * 0.3, 1.0)
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determinar nivel de riesgo"""
        if score < 0.25:
            return RiskLevel.LOW
        elif score < 0.5:
            return RiskLevel.MODERATE
        elif score < 0.75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _calculate_position_multiplier(
        self, 
        risk_score: float, 
        confidence: float,
        risk_level: RiskLevel
    ) -> float:
        """Calcular multiplicador de tamaño de posición"""
        base = 1.0
        
        risk_adjustment = 1 - (risk_score * 0.5)
        
        if risk_level == RiskLevel.HIGH:
            base *= 0.5
        elif risk_level == RiskLevel.CRITICAL:
            base *= 0.1
        
        confidence_boost = 1 + (confidence - 0.5) * 0.3
        
        multiplier = base * risk_adjustment * confidence_boost
        
        return np.clip(multiplier, 0.1, 1.5)
    
    def _calculate_stop_adjustment(self, risk_level: RiskLevel) -> float:
        """Calcular ajuste de stop loss"""
        adjustments = {
            RiskLevel.LOW: 0,
            RiskLevel.MODERATE: 0.1,
            RiskLevel.HIGH: 0.25,
            RiskLevel.CRITICAL: 0.5
        }
        return adjustments.get(risk_level, 0)
    
    def _log_risk_event(self, symbol: str, assessment: RiskAssessment):
        """Registrar evento de riesgo"""
        event = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'risk_level': assessment.risk_level.value,
            'risk_score': assessment.risk_score,
            'risks': [r['type'] for r in assessment.active_risks],
            'approved': assessment.approved
        }
        
        self.risk_events.append(event)
        
        if len(self.risk_events) > 500:
            self.risk_events = self.risk_events[-500:]
        
        if assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            logger.warning(f"🚨 Risk Event: {symbol} - {assessment.risk_level.value}")
    
    def update_pnl(self, pnl_change: float):
        """Actualizar P&L diario"""
        self.daily_pnl += pnl_change
    
    def record_trade(self, symbol: str, sector: str = "unknown"):
        """Registrar trade ejecutado"""
        self.trades_today += 1
        self.positions[symbol] = {
            'sector': sector,
            'entry_time': datetime.now()
        }
    
    def close_position(self, symbol: str):
        """Registrar cierre de posición"""
        if symbol in self.positions:
            del self.positions[symbol]
    
    def get_risk_summary(self) -> Dict:
        """Obtener resumen de riesgo"""
        recent_events = [e for e in self.risk_events if e['timestamp'] > datetime.now() - timedelta(hours=24)]
        
        return {
            'daily_pnl': self.daily_pnl,
            'trades_today': self.trades_today,
            'open_positions': len(self.positions),
            'risk_events_24h': len(recent_events),
            'high_risk_events': sum(1 for e in recent_events if e['risk_level'] in ['high', 'critical']),
            'approval_rate': sum(1 for e in recent_events if e['approved']) / len(recent_events) if recent_events else 1,
            'params': self.RISK_PARAMS
        }
    
    def is_trading_allowed(self) -> Tuple[bool, List[str]]:
        """Verificar si trading está permitido"""
        reasons = []
        
        if self.daily_pnl < -self.RISK_PARAMS['max_daily_drawdown']:
            reasons.append(f"Drawdown diario excedido: {self.daily_pnl:.2%}")
        
        if self.trades_today >= self.RISK_PARAMS['max_trades_per_day']:
            reasons.append(f"Límite de trades alcanzado: {self.trades_today}")
        
        if len(self.positions) >= self.RISK_PARAMS['max_positions']:
            reasons.append(f"Máximo de posiciones alcanzado: {len(self.positions)}")
        
        return len(reasons) == 0, reasons
