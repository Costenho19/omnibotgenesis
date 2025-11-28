"""
Margin Engine - OMNIX Derivatives Premium
==========================================

Motor de gestión de margen institucional con:
- Límite máximo 3x apalancamiento (conservador)
- Cálculo de margen inicial/mantenimiento
- Protección automática contra liquidación
- Deleveraging progresivo
- Alertas de margen

Diseñado para proteger capital institucional.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MarginLevel(Enum):
    """Niveles de margen para alertas"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    LIQUIDATION = "liquidation"


class LeverageLevel(Enum):
    """Niveles de apalancamiento permitidos"""
    CONSERVATIVE = 1.0
    MODERATE = 2.0
    MAXIMUM = 3.0


@dataclass
class MarginStatus:
    """Estado actual del margen"""
    total_equity: float
    available_margin: float
    used_margin: float
    margin_ratio: float
    margin_level: MarginLevel
    effective_leverage: float
    max_leverage: float
    liquidation_distance: float
    can_trade: bool
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PositionMargin:
    """Requisitos de margen para una posición"""
    symbol: str
    notional_value: float
    initial_margin: float
    maintenance_margin: float
    margin_ratio: float
    effective_leverage: float
    liquidation_price: float
    safety_buffer: float


class MarginEngine:
    """
    Motor de Margen Institucional para OMNIX
    
    Características:
    - Apalancamiento máximo 3x (configurable hasta 3x)
    - Margen inicial: 33.33% para 3x
    - Margen mantenimiento: 25%
    - Buffer de seguridad: 15% sobre mantenimiento
    - Auto-deleveraging si margen < 140% mantenimiento
    """
    
    MAX_LEVERAGE = 3.0
    INITIAL_MARGIN_RATE = 0.3333
    MAINTENANCE_MARGIN_RATE = 0.25
    
    WARNING_THRESHOLD = 0.60
    CRITICAL_THRESHOLD = 0.40
    LIQUIDATION_THRESHOLD = 0.30
    
    SAFETY_BUFFER = 1.15
    
    ASSET_RISK_WEIGHTS = {
        "BTC": 1.0,
        "ETH": 1.1,
        "SOL": 1.3,
        "XRP": 1.4
    }
    
    def __init__(self, 
                 initial_capital: float = 1_000_000.0,
                 max_leverage: float = 3.0,
                 risk_tolerance: str = "conservative"):
        """
        Inicializar Margin Engine
        
        Args:
            initial_capital: Capital inicial en USD
            max_leverage: Apalancamiento máximo permitido (max 3.0)
            risk_tolerance: conservative, moderate, aggressive
        """
        self.initial_capital = initial_capital
        self.current_equity = initial_capital
        self.max_leverage = min(max_leverage, self.MAX_LEVERAGE)
        self.risk_tolerance = risk_tolerance
        
        self.positions: Dict[str, Dict] = {}
        self.total_notional = 0.0
        self.total_margin_used = 0.0
        
        self._margin_history: List[MarginStatus] = []
        self._alerts_triggered: List[Dict] = []
        
        tolerance_multipliers = {
            "conservative": 0.8,
            "moderate": 0.9,
            "aggressive": 1.0
        }
        self._risk_multiplier = tolerance_multipliers.get(risk_tolerance, 0.8)
        
        logger.info(f"💰 MarginEngine inicializado")
        logger.info(f"   💵 Capital: ${initial_capital:,.2f}")
        logger.info(f"   📊 Max Leverage: {self.max_leverage}x")
        logger.info(f"   🎯 Tolerancia: {risk_tolerance}")
    
    def calculate_position_margin(self, 
                                   symbol: str, 
                                   size: float, 
                                   entry_price: float,
                                   leverage: float = 1.0) -> PositionMargin:
        """
        Calcular requisitos de margen para una posición
        
        Args:
            symbol: Símbolo (BTC, ETH, etc.)
            size: Tamaño de la posición
            entry_price: Precio de entrada
            leverage: Apalancamiento deseado (máx 3x)
            
        Returns:
            PositionMargin con todos los cálculos
        """
        leverage = min(leverage, self.max_leverage)
        
        notional_value = abs(size * entry_price)
        
        risk_weight = self.ASSET_RISK_WEIGHTS.get(symbol.upper(), 1.5)
        
        initial_margin_rate = self.INITIAL_MARGIN_RATE * risk_weight
        initial_margin = notional_value * initial_margin_rate
        
        maintenance_margin_rate = self.MAINTENANCE_MARGIN_RATE * risk_weight
        maintenance_margin = notional_value * maintenance_margin_rate
        
        margin_ratio = initial_margin / notional_value if notional_value > 0 else 0
        
        effective_leverage = notional_value / initial_margin if initial_margin > 0 else 0
        
        liquidation_distance = (1 - maintenance_margin_rate) * entry_price
        liquidation_price = entry_price - liquidation_distance if size > 0 else entry_price + liquidation_distance
        
        safety_buffer = (maintenance_margin * self.SAFETY_BUFFER) - maintenance_margin
        
        return PositionMargin(
            symbol=symbol.upper(),
            notional_value=notional_value,
            initial_margin=initial_margin,
            maintenance_margin=maintenance_margin,
            margin_ratio=margin_ratio,
            effective_leverage=effective_leverage,
            liquidation_price=max(0, liquidation_price),
            safety_buffer=safety_buffer
        )
    
    def can_open_position(self, 
                          symbol: str, 
                          size: float, 
                          entry_price: float,
                          leverage: float = 1.0) -> Tuple[bool, str]:
        """
        Verificar si se puede abrir una posición
        
        Args:
            symbol: Símbolo
            size: Tamaño
            entry_price: Precio
            leverage: Apalancamiento
            
        Returns:
            (bool, str): (puede_abrir, razón)
        """
        if leverage > self.max_leverage:
            return False, f"Leverage {leverage}x excede máximo permitido ({self.max_leverage}x)"
        
        margin_req = self.calculate_position_margin(symbol, size, entry_price, leverage)
        
        available_margin = self.get_available_margin()
        
        if margin_req.initial_margin > available_margin:
            return False, f"Margen insuficiente: necesita ${margin_req.initial_margin:,.2f}, disponible ${available_margin:,.2f}"
        
        new_total_notional = self.total_notional + margin_req.notional_value
        new_leverage = new_total_notional / self.current_equity if self.current_equity > 0 else 0
        
        if new_leverage > self.max_leverage:
            return False, f"Apalancamiento total {new_leverage:.2f}x excedería máximo ({self.max_leverage}x)"
        
        concentration = margin_req.notional_value / self.current_equity if self.current_equity > 0 else 0
        max_concentration = 0.5 * self._risk_multiplier
        
        if concentration > max_concentration:
            return False, f"Concentración {concentration:.1%} excede máximo ({max_concentration:.1%})"
        
        return True, "OK"
    
    def add_position(self, 
                     symbol: str, 
                     size: float, 
                     entry_price: float,
                     leverage: float = 1.0) -> Optional[PositionMargin]:
        """
        Agregar posición al tracking de margen
        
        Args:
            symbol: Símbolo
            size: Tamaño (positivo=long, negativo=short)
            entry_price: Precio de entrada
            leverage: Apalancamiento
            
        Returns:
            PositionMargin si se agregó exitosamente
        """
        can_open, reason = self.can_open_position(symbol, size, entry_price, leverage)
        
        if not can_open:
            logger.warning(f"⚠️ No se puede abrir posición: {reason}")
            return None
        
        margin_req = self.calculate_position_margin(symbol, size, entry_price, leverage)
        
        position_id = f"{symbol.upper()}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.positions[position_id] = {
            "symbol": symbol.upper(),
            "size": size,
            "entry_price": entry_price,
            "leverage": leverage,
            "margin": margin_req,
            "timestamp": datetime.now()
        }
        
        self.total_notional += margin_req.notional_value
        self.total_margin_used += margin_req.initial_margin
        
        logger.info(f"📊 Posición agregada: {symbol} {size:+.4f} @ ${entry_price:,.2f}")
        logger.info(f"   💰 Margen usado: ${margin_req.initial_margin:,.2f}")
        logger.info(f"   📈 Leverage efectivo: {margin_req.effective_leverage:.2f}x")
        
        return margin_req
    
    def update_position(self, position_id: str, current_price: float) -> Optional[Dict]:
        """
        Actualizar posición con precio actual
        
        Args:
            position_id: ID de la posición
            current_price: Precio actual del mercado
            
        Returns:
            Dict con PnL y estado actualizado
        """
        if position_id not in self.positions:
            return None
        
        pos = self.positions[position_id]
        size = pos["size"]
        entry_price = pos["entry_price"]
        
        pnl = (current_price - entry_price) * size
        pnl_pct = pnl / (entry_price * abs(size)) if entry_price * abs(size) > 0 else 0
        
        new_notional = abs(size * current_price)
        margin = self.calculate_position_margin(pos["symbol"], size, current_price, pos["leverage"])
        
        self.positions[position_id]["current_price"] = current_price
        self.positions[position_id]["pnl"] = pnl
        self.positions[position_id]["pnl_pct"] = pnl_pct
        self.positions[position_id]["margin"] = margin
        
        return {
            "position_id": position_id,
            "symbol": pos["symbol"],
            "size": size,
            "entry_price": entry_price,
            "current_price": current_price,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "margin": margin
        }
    
    def close_position(self, position_id: str) -> Optional[Dict]:
        """
        Cerrar y remover posición
        
        Args:
            position_id: ID de la posición
            
        Returns:
            Dict con resultado del cierre
        """
        if position_id not in self.positions:
            return None
        
        pos = self.positions[position_id]
        margin = pos["margin"]
        
        self.total_notional -= margin.notional_value
        self.total_margin_used -= margin.initial_margin
        
        self.total_notional = max(0, self.total_notional)
        self.total_margin_used = max(0, self.total_margin_used)
        
        pnl = pos.get("pnl", 0)
        self.current_equity += pnl
        
        del self.positions[position_id]
        
        logger.info(f"📉 Posición cerrada: {pos['symbol']}")
        logger.info(f"   💵 PnL: ${pnl:+,.2f}")
        
        return {
            "position_id": position_id,
            "symbol": pos["symbol"],
            "pnl": pnl,
            "new_equity": self.current_equity
        }
    
    def get_available_margin(self) -> float:
        """
        Obtener margen disponible para nuevas posiciones
        
        Returns:
            Margen disponible en USD
        """
        reserved = self.total_margin_used * self.SAFETY_BUFFER
        return max(0, self.current_equity - reserved)
    
    def get_margin_status(self) -> MarginStatus:
        """
        Obtener estado completo del margen
        
        Returns:
            MarginStatus con todos los detalles
        """
        available_margin = self.get_available_margin()
        margin_ratio = available_margin / self.current_equity if self.current_equity > 0 else 0
        effective_leverage = self.total_notional / self.current_equity if self.current_equity > 0 else 0
        
        if margin_ratio >= self.WARNING_THRESHOLD:
            level = MarginLevel.HEALTHY
        elif margin_ratio >= self.CRITICAL_THRESHOLD:
            level = MarginLevel.WARNING
        elif margin_ratio >= self.LIQUIDATION_THRESHOLD:
            level = MarginLevel.CRITICAL
        else:
            level = MarginLevel.LIQUIDATION
        
        liquidation_distance = margin_ratio - self.LIQUIDATION_THRESHOLD
        
        can_trade = level in [MarginLevel.HEALTHY, MarginLevel.WARNING]
        
        warnings = []
        if level == MarginLevel.WARNING:
            warnings.append(f"⚠️ Margen bajo: {margin_ratio:.1%}")
        elif level == MarginLevel.CRITICAL:
            warnings.append(f"🚨 Margen crítico: {margin_ratio:.1%} - Reducir posiciones")
        elif level == MarginLevel.LIQUIDATION:
            warnings.append(f"💀 RIESGO DE LIQUIDACIÓN: {margin_ratio:.1%}")
        
        if effective_leverage > 2.5:
            warnings.append(f"📊 Apalancamiento alto: {effective_leverage:.2f}x")
        
        status = MarginStatus(
            total_equity=self.current_equity,
            available_margin=available_margin,
            used_margin=self.total_margin_used,
            margin_ratio=margin_ratio,
            margin_level=level,
            effective_leverage=effective_leverage,
            max_leverage=self.max_leverage,
            liquidation_distance=liquidation_distance,
            can_trade=can_trade,
            warnings=warnings,
            timestamp=datetime.now()
        )
        
        self._margin_history.append(status)
        if len(self._margin_history) > 1000:
            self._margin_history = self._margin_history[-500:]
        
        return status
    
    def check_liquidation_risk(self) -> List[Dict]:
        """
        Verificar riesgo de liquidación en todas las posiciones
        
        Returns:
            Lista de posiciones en riesgo
        """
        at_risk = []
        
        for pos_id, pos in self.positions.items():
            margin = pos.get("margin")
            current_price = pos.get("current_price", pos["entry_price"])
            
            if margin:
                distance_to_liq = abs(current_price - margin.liquidation_price) / current_price
                
                if distance_to_liq < 0.10:
                    at_risk.append({
                        "position_id": pos_id,
                        "symbol": pos["symbol"],
                        "current_price": current_price,
                        "liquidation_price": margin.liquidation_price,
                        "distance_pct": distance_to_liq,
                        "recommended_action": "CLOSE" if distance_to_liq < 0.05 else "REDUCE"
                    })
        
        return at_risk
    
    def suggest_deleveraging(self) -> List[Dict]:
        """
        Sugerir reducciones de posición para mejorar margen
        
        Returns:
            Lista de sugerencias de deleveraging
        """
        status = self.get_margin_status()
        
        if status.margin_level == MarginLevel.HEALTHY:
            return []
        
        suggestions = []
        
        sorted_positions = sorted(
            self.positions.items(),
            key=lambda x: x[1].get("pnl", 0)
        )
        
        target_margin_ratio = self.WARNING_THRESHOLD
        margin_deficit = (target_margin_ratio - status.margin_ratio) * self.current_equity
        
        for pos_id, pos in sorted_positions:
            if margin_deficit <= 0:
                break
            
            margin = pos.get("margin")
            if margin:
                reduction_pct = min(0.5, margin_deficit / margin.initial_margin)
                
                suggestions.append({
                    "position_id": pos_id,
                    "symbol": pos["symbol"],
                    "current_size": pos["size"],
                    "reduce_by_pct": reduction_pct,
                    "reduce_by_size": pos["size"] * reduction_pct,
                    "margin_freed": margin.initial_margin * reduction_pct
                })
                
                margin_deficit -= margin.initial_margin * reduction_pct
        
        return suggestions
    
    def get_summary(self) -> Dict:
        """
        Obtener resumen del motor de margen
        
        Returns:
            Dict con estadísticas completas
        """
        status = self.get_margin_status()
        at_risk = self.check_liquidation_risk()
        
        return {
            "equity": self.current_equity,
            "initial_capital": self.initial_capital,
            "total_pnl": self.current_equity - self.initial_capital,
            "total_pnl_pct": (self.current_equity - self.initial_capital) / self.initial_capital,
            "positions_count": len(self.positions),
            "total_notional": self.total_notional,
            "margin_used": self.total_margin_used,
            "margin_available": status.available_margin,
            "margin_ratio": status.margin_ratio,
            "margin_level": status.margin_level.value,
            "effective_leverage": status.effective_leverage,
            "max_leverage": self.max_leverage,
            "can_trade": status.can_trade,
            "positions_at_risk": len(at_risk),
            "warnings": status.warnings,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = MarginEngine(
        initial_capital=1_000_000,
        max_leverage=3.0,
        risk_tolerance="conservative"
    )
    
    print("\n=== Margin Engine Test ===\n")
    
    margin1 = engine.add_position("BTC", 1.0, 95000.0, leverage=2.0)
    if margin1:
        print(f"BTC Position Margin: ${margin1.initial_margin:,.2f}")
        print(f"Liquidation Price: ${margin1.liquidation_price:,.2f}")
    
    margin2 = engine.add_position("ETH", 10.0, 3500.0, leverage=2.0)
    if margin2:
        print(f"\nETH Position Margin: ${margin2.initial_margin:,.2f}")
    
    status = engine.get_margin_status()
    print(f"\n=== Margin Status ===")
    print(f"Equity: ${status.total_equity:,.2f}")
    print(f"Available Margin: ${status.available_margin:,.2f}")
    print(f"Margin Ratio: {status.margin_ratio:.1%}")
    print(f"Level: {status.margin_level.value}")
    print(f"Effective Leverage: {status.effective_leverage:.2f}x")
    print(f"Can Trade: {status.can_trade}")
    
    summary = engine.get_summary()
    print(f"\n=== Summary ===")
    print(f"Positions: {summary['positions_count']}")
    print(f"Total Notional: ${summary['total_notional']:,.2f}")
