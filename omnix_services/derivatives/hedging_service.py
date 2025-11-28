"""
Hedging Service - OMNIX Premium
================================

Servicio de hedging automático para proteger posiciones spot:
- Delta hedging con perpetuos
- Protección de portfolio spot
- Rebalanceo automático
- Cobertura parcial/total

Diseñado para protección institucional de capital.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class HedgeType(Enum):
    FULL = "full"
    PARTIAL = "partial"
    DYNAMIC = "dynamic"


class HedgeStatus(Enum):
    ACTIVE = "active"
    PENDING = "pending"
    CLOSED = "closed"
    ERROR = "error"


@dataclass
class HedgePosition:
    """Posición de cobertura"""
    hedge_id: str
    spot_symbol: str
    spot_size: float
    spot_value: float
    hedge_symbol: str
    hedge_size: float
    hedge_side: str
    hedge_entry_price: float
    hedge_type: HedgeType
    coverage_ratio: float
    delta: float
    created_at: datetime
    last_rebalance: datetime
    status: HedgeStatus
    pnl: float = 0.0


@dataclass
class HedgeConfig:
    """Configuración de hedging"""
    enabled: bool = True
    default_coverage: float = 0.80
    min_coverage: float = 0.50
    max_coverage: float = 1.00
    rebalance_threshold: float = 0.10
    max_hedge_leverage: float = 2.0
    auto_rebalance: bool = True
    rebalance_interval_hours: int = 4


class HedgingService:
    """
    Servicio de Hedging Automático OMNIX
    
    Funcionalidades:
    - Calcular hedge óptimo para posiciones spot
    - Ejecutar hedges en perpetuos
    - Rebalancear hedges periódicamente
    - Monitorear efectividad del hedge
    """
    
    SPOT_TO_PERP_MAPPING = {
        "BTC": "PI_XBTUSD",
        "ETH": "PI_ETHUSD",
        "SOL": "PI_SOLUSD",
        "XRP": "PI_XRPUSD"
    }
    
    def __init__(self, 
                 derivatives_manager: Optional[object] = None,
                 config: Optional[HedgeConfig] = None):
        """
        Inicializar Hedging Service
        
        Args:
            derivatives_manager: DerivativesManager para ejecutar hedges
            config: Configuración de hedging
        """
        self.derivatives_manager = derivatives_manager
        self.config = config or HedgeConfig()
        
        self.active_hedges: Dict[str, HedgePosition] = {}
        self.hedge_history: List[HedgePosition] = []
        
        self._hedge_counter = 0
        
        self.stats = {
            "total_hedges": 0,
            "active_hedges": 0,
            "total_protected_value": 0.0,
            "hedge_pnl": 0.0,
            "rebalances": 0
        }
        
        logger.info(f"🛡️ HedgingService inicializado")
        logger.info(f"   📊 Cobertura default: {self.config.default_coverage:.0%}")
        logger.info(f"   🔄 Auto-rebalance: {self.config.auto_rebalance}")
    
    def _generate_hedge_id(self) -> str:
        """Generar ID único para hedge"""
        self._hedge_counter += 1
        return f"HEDGE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._hedge_counter:04d}"
    
    def calculate_optimal_hedge(self,
                                 spot_symbol: str,
                                 spot_size: float,
                                 spot_price: float,
                                 coverage_ratio: float = None) -> Dict:
        """
        Calcular hedge óptimo para una posición spot
        
        Args:
            spot_symbol: Símbolo spot (BTC, ETH, etc.)
            spot_size: Tamaño de la posición spot
            spot_price: Precio actual spot
            coverage_ratio: Ratio de cobertura (default: config)
            
        Returns:
            Dict con parámetros del hedge óptimo
        """
        if spot_symbol not in self.SPOT_TO_PERP_MAPPING:
            return {"error": f"No hay perpetuo disponible para {spot_symbol}"}
        
        coverage = coverage_ratio or self.config.default_coverage
        coverage = max(self.config.min_coverage, min(coverage, self.config.max_coverage))
        
        spot_value = spot_size * spot_price
        
        hedge_size = spot_size * coverage
        hedge_value = hedge_size * spot_price
        
        hedge_symbol = self.SPOT_TO_PERP_MAPPING[spot_symbol]
        
        leverage = min(2.0, self.config.max_hedge_leverage)
        margin_required = hedge_value / leverage
        
        return {
            "spot_symbol": spot_symbol,
            "spot_size": spot_size,
            "spot_value": spot_value,
            "spot_price": spot_price,
            "hedge_symbol": hedge_symbol,
            "hedge_size": hedge_size,
            "hedge_side": "short",
            "hedge_value": hedge_value,
            "coverage_ratio": coverage,
            "leverage": leverage,
            "margin_required": margin_required,
            "estimated_cost": hedge_value * 0.001
        }
    
    def create_hedge(self,
                     spot_symbol: str,
                     spot_size: float,
                     spot_price: float,
                     coverage_ratio: float = None,
                     hedge_type: HedgeType = HedgeType.PARTIAL) -> Optional[HedgePosition]:
        """
        Crear hedge para posición spot
        
        Args:
            spot_symbol: Símbolo spot
            spot_size: Tamaño spot
            spot_price: Precio spot
            coverage_ratio: Ratio de cobertura
            hedge_type: Tipo de hedge
            
        Returns:
            HedgePosition si se creó exitosamente
        """
        optimal = self.calculate_optimal_hedge(spot_symbol, spot_size, spot_price, coverage_ratio)
        
        if "error" in optimal:
            logger.error(f"❌ Error calculando hedge: {optimal['error']}")
            return None
        
        if self.derivatives_manager:
            result = self.derivatives_manager.open_position(
                symbol=spot_symbol,
                side="short",
                size=optimal["hedge_size"],
                leverage=optimal["leverage"]
            )
            
            if not result.get("success"):
                logger.error(f"❌ Error ejecutando hedge: {result.get('error')}")
                return None
            
            entry_price = result.get("entry_price", spot_price)
        else:
            entry_price = spot_price
            logger.warning("⚠️ DerivativesManager no conectado - hedge simulado")
        
        hedge = HedgePosition(
            hedge_id=self._generate_hedge_id(),
            spot_symbol=spot_symbol,
            spot_size=spot_size,
            spot_value=optimal["spot_value"],
            hedge_symbol=optimal["hedge_symbol"],
            hedge_size=optimal["hedge_size"],
            hedge_side="short",
            hedge_entry_price=entry_price,
            hedge_type=hedge_type,
            coverage_ratio=optimal["coverage_ratio"],
            delta=0.0,
            created_at=datetime.now(),
            last_rebalance=datetime.now(),
            status=HedgeStatus.ACTIVE
        )
        
        self.active_hedges[hedge.hedge_id] = hedge
        self.stats["total_hedges"] += 1
        self.stats["active_hedges"] = len(self.active_hedges)
        self.stats["total_protected_value"] += optimal["spot_value"]
        
        logger.info(f"🛡️ Hedge creado: {hedge.hedge_id}")
        logger.info(f"   📊 {spot_symbol}: {spot_size} spot → {optimal['hedge_size']:.4f} short perp")
        logger.info(f"   💰 Valor protegido: ${optimal['spot_value']:,.2f} ({optimal['coverage_ratio']:.0%})")
        
        return hedge
    
    def update_hedge(self, hedge_id: str, current_spot_price: float, 
                     current_perp_price: float) -> Optional[Dict]:
        """
        Actualizar hedge con precios actuales
        
        Args:
            hedge_id: ID del hedge
            current_spot_price: Precio spot actual
            current_perp_price: Precio perpetuo actual
            
        Returns:
            Dict con estado actualizado
        """
        if hedge_id not in self.active_hedges:
            return None
        
        hedge = self.active_hedges[hedge_id]
        
        spot_pnl = (current_spot_price - (hedge.spot_value / hedge.spot_size)) * hedge.spot_size
        
        hedge_pnl = (hedge.hedge_entry_price - current_perp_price) * hedge.hedge_size
        
        net_pnl = spot_pnl + hedge_pnl
        hedge.pnl = hedge_pnl
        
        hedge.delta = spot_pnl + hedge_pnl
        
        current_spot_value = hedge.spot_size * current_spot_price
        current_hedge_value = hedge.hedge_size * current_perp_price
        actual_coverage = current_hedge_value / current_spot_value if current_spot_value > 0 else 0
        
        coverage_drift = abs(actual_coverage - hedge.coverage_ratio)
        needs_rebalance = coverage_drift > self.config.rebalance_threshold
        
        return {
            "hedge_id": hedge_id,
            "spot_pnl": spot_pnl,
            "hedge_pnl": hedge_pnl,
            "net_pnl": net_pnl,
            "delta": hedge.delta,
            "target_coverage": hedge.coverage_ratio,
            "actual_coverage": actual_coverage,
            "coverage_drift": coverage_drift,
            "needs_rebalance": needs_rebalance,
            "hedge_effectiveness": 1 - abs(net_pnl / spot_pnl) if spot_pnl != 0 else 1.0
        }
    
    def rebalance_hedge(self, hedge_id: str, current_spot_price: float,
                        current_perp_price: float) -> Optional[Dict]:
        """
        Rebalancear hedge para mantener cobertura objetivo
        
        Args:
            hedge_id: ID del hedge
            current_spot_price: Precio spot actual
            current_perp_price: Precio perpetuo actual
            
        Returns:
            Dict con resultado del rebalance
        """
        if hedge_id not in self.active_hedges:
            return None
        
        hedge = self.active_hedges[hedge_id]
        
        current_spot_value = hedge.spot_size * current_spot_price
        target_hedge_value = current_spot_value * hedge.coverage_ratio
        target_hedge_size = target_hedge_value / current_perp_price
        
        size_diff = target_hedge_size - hedge.hedge_size
        
        if abs(size_diff) < 0.001:
            return {"rebalanced": False, "reason": "Diferencia insignificante"}
        
        if self.derivatives_manager:
            if size_diff > 0:
                result = self.derivatives_manager.open_position(
                    symbol=hedge.spot_symbol,
                    side="short",
                    size=abs(size_diff),
                    leverage=2.0
                )
            else:
                pass
        
        hedge.hedge_size = target_hedge_size
        hedge.last_rebalance = datetime.now()
        self.stats["rebalances"] += 1
        
        logger.info(f"🔄 Hedge rebalanceado: {hedge_id}")
        logger.info(f"   📊 Nuevo tamaño: {target_hedge_size:.4f}")
        
        return {
            "rebalanced": True,
            "hedge_id": hedge_id,
            "old_size": hedge.hedge_size - size_diff,
            "new_size": target_hedge_size,
            "size_change": size_diff,
            "timestamp": datetime.now().isoformat()
        }
    
    def close_hedge(self, hedge_id: str, current_perp_price: float, 
                    reason: str = "manual") -> Optional[Dict]:
        """
        Cerrar hedge
        
        Args:
            hedge_id: ID del hedge
            current_perp_price: Precio perpetuo actual
            reason: Razón del cierre
            
        Returns:
            Dict con resultado
        """
        if hedge_id not in self.active_hedges:
            return None
        
        hedge = self.active_hedges[hedge_id]
        
        if self.derivatives_manager:
            result = self.derivatives_manager.close_position(
                symbol=hedge.spot_symbol,
                reason=f"Hedge closed: {reason}"
            )
        
        hedge_pnl = (hedge.hedge_entry_price - current_perp_price) * hedge.hedge_size
        
        hedge.status = HedgeStatus.CLOSED
        hedge.pnl = hedge_pnl
        
        self.hedge_history.append(hedge)
        del self.active_hedges[hedge_id]
        
        self.stats["active_hedges"] = len(self.active_hedges)
        self.stats["hedge_pnl"] += hedge_pnl
        self.stats["total_protected_value"] -= hedge.spot_value
        
        logger.info(f"🔓 Hedge cerrado: {hedge_id}")
        logger.info(f"   💵 PnL del hedge: ${hedge_pnl:+,.2f}")
        
        return {
            "hedge_id": hedge_id,
            "pnl": hedge_pnl,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_hedge(self, hedge_id: str) -> Optional[HedgePosition]:
        """Obtener hedge por ID"""
        return self.active_hedges.get(hedge_id)
    
    def get_all_hedges(self) -> List[Dict]:
        """
        Obtener todos los hedges activos
        
        Returns:
            Lista de hedges como dicts
        """
        return [
            {
                "hedge_id": h.hedge_id,
                "spot_symbol": h.spot_symbol,
                "spot_size": h.spot_size,
                "spot_value": h.spot_value,
                "hedge_size": h.hedge_size,
                "hedge_side": h.hedge_side,
                "coverage_ratio": h.coverage_ratio,
                "delta": h.delta,
                "pnl": h.pnl,
                "status": h.status.value,
                "created_at": h.created_at.isoformat(),
                "last_rebalance": h.last_rebalance.isoformat()
            }
            for h in self.active_hedges.values()
        ]
    
    def get_hedge_for_symbol(self, symbol: str) -> Optional[HedgePosition]:
        """Obtener hedge activo para un símbolo"""
        for hedge in self.active_hedges.values():
            if hedge.spot_symbol == symbol.upper():
                return hedge
        return None
    
    def calculate_portfolio_hedge(self, 
                                   spot_positions: List[Dict],
                                   target_coverage: float = None) -> Dict:
        """
        Calcular hedge óptimo para portfolio completo
        
        Args:
            spot_positions: Lista de posiciones spot [{symbol, size, price}, ...]
            target_coverage: Cobertura objetivo
            
        Returns:
            Dict con recomendación de hedges
        """
        coverage = target_coverage or self.config.default_coverage
        
        total_spot_value = sum(p["size"] * p["price"] for p in spot_positions)
        
        hedges_needed = []
        for pos in spot_positions:
            if pos["symbol"] in self.SPOT_TO_PERP_MAPPING:
                optimal = self.calculate_optimal_hedge(
                    pos["symbol"], pos["size"], pos["price"], coverage
                )
                hedges_needed.append(optimal)
        
        total_margin = sum(h.get("margin_required", 0) for h in hedges_needed)
        total_hedge_value = sum(h.get("hedge_value", 0) for h in hedges_needed)
        
        return {
            "total_spot_value": total_spot_value,
            "total_hedge_value": total_hedge_value,
            "total_margin_required": total_margin,
            "target_coverage": coverage,
            "effective_coverage": total_hedge_value / total_spot_value if total_spot_value > 0 else 0,
            "hedges": hedges_needed,
            "estimated_cost": total_hedge_value * 0.001
        }
    
    def get_stats(self) -> Dict:
        """
        Obtener estadísticas del servicio
        
        Returns:
            Dict con estadísticas
        """
        return {
            "total_hedges": self.stats["total_hedges"],
            "active_hedges": self.stats["active_hedges"],
            "total_protected_value": self.stats["total_protected_value"],
            "hedge_pnl": self.stats["hedge_pnl"],
            "rebalances": self.stats["rebalances"],
            "config": {
                "enabled": self.config.enabled,
                "default_coverage": self.config.default_coverage,
                "auto_rebalance": self.config.auto_rebalance
            },
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    service = HedgingService()
    
    print("\n=== Hedging Service Test ===\n")
    
    optimal = service.calculate_optimal_hedge("BTC", 2.0, 95000, 0.80)
    print(f"Optimal Hedge:")
    print(f"  Spot Value: ${optimal['spot_value']:,.2f}")
    print(f"  Hedge Size: {optimal['hedge_size']:.4f}")
    print(f"  Margin Required: ${optimal['margin_required']:,.2f}")
    
    hedge = service.create_hedge("BTC", 2.0, 95000, 0.80)
    if hedge:
        print(f"\nHedge Created: {hedge.hedge_id}")
        print(f"  Coverage: {hedge.coverage_ratio:.0%}")
    
    update = service.update_hedge(hedge.hedge_id, 94000, 93800)
    if update:
        print(f"\nHedge Update:")
        print(f"  Spot PnL: ${update['spot_pnl']:+,.2f}")
        print(f"  Hedge PnL: ${update['hedge_pnl']:+,.2f}")
        print(f"  Net PnL: ${update['net_pnl']:+,.2f}")
        print(f"  Effectiveness: {update['hedge_effectiveness']:.1%}")
    
    stats = service.get_stats()
    print(f"\nStats: {stats}")
