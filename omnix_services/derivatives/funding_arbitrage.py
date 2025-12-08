"""
Funding Arbitrage Analyzer - OMNIX Premium
============================================

Analizador de oportunidades de arbitraje de funding rates:
- Monitoreo de funding rates en perpetuos
- Detección de oportunidades positivas
- Cálculo de retorno esperado
- Ejecución automática (opcional)

Estrategia: Long spot + Short perpetuo cuando funding > 0
Genera retorno por funding sin riesgo direccional.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class OpportunityStatus(Enum):
    DETECTED = "detected"
    EXECUTING = "executing"
    ACTIVE = "active"
    CLOSED = "closed"
    MISSED = "missed"


@dataclass
class FundingOpportunity:
    """Oportunidad de arbitraje de funding"""
    opportunity_id: str
    symbol: str
    funding_rate: float
    funding_rate_annualized: float
    spot_price: float
    perp_price: float
    basis: float
    expected_return_8h: float
    expected_return_annual: float
    entry_cost: float
    recommended_size: float
    risk_score: float
    detected_at: datetime
    status: OpportunityStatus
    expires_at: datetime


@dataclass
class FundingPosition:
    """Posición de arbitraje de funding activa"""
    position_id: str
    symbol: str
    spot_size: float
    spot_entry_price: float
    perp_size: float
    perp_entry_price: float
    total_funding_earned: float
    funding_payments: int
    pnl: float
    opened_at: datetime
    last_funding: datetime
    status: str


@dataclass
class FundingArbitrageConfig:
    """Configuración del arbitraje de funding"""
    enabled: bool = True
    min_funding_rate: float = 0.0001
    min_annualized_return: float = 0.05
    max_position_size_pct: float = 0.10
    auto_execute: bool = False
    max_concurrent_positions: int = 3
    min_liquidity_score: float = 50.0
    close_if_negative: bool = True
    funding_collection_periods: int = 3


class FundingArbitrageAnalyzer:
    """
    Analizador de Arbitraje de Funding OMNIX
    
    Funcionalidades:
    - Escanear funding rates en tiempo real
    - Identificar oportunidades rentables
    - Calcular retorno esperado neto de costos
    - Gestionar posiciones de arbitraje
    """
    
    TAKER_FEE = 0.0006
    MAKER_FEE = 0.0002
    SLIPPAGE_BPS = 5
    
    SUPPORTED_PAIRS = ["BTC", "ETH", "SOL", "XRP"]
    
    def __init__(self, 
                 futures_client: Optional[object] = None,
                 derivatives_manager: Optional[object] = None,
                 config: Optional[FundingArbitrageConfig] = None):
        """
        Inicializar Funding Arbitrage Analyzer
        
        Args:
            futures_client: KrakenFuturesClient para datos
            derivatives_manager: DerivativesManager para ejecución
            config: Configuración del arbitraje
        """
        self.futures_client = futures_client
        self.derivatives_manager = derivatives_manager
        self.config = config or FundingArbitrageConfig()
        
        self.active_positions: Dict[str, FundingPosition] = {}
        self.opportunities: Dict[str, FundingOpportunity] = {}
        self.position_history: List[FundingPosition] = []
        
        self._opportunity_counter = 0
        self._position_counter = 0
        
        self.stats = {
            "opportunities_detected": 0,
            "opportunities_executed": 0,
            "total_funding_earned": 0.0,
            "total_pnl": 0.0,
            "current_positions": 0,
            "avg_annualized_return": 0.0
        }
        
        logger.info(f"💰 FundingArbitrageAnalyzer inicializado")
        logger.info(f"   📊 Min funding rate: {self.config.min_funding_rate:.4%}")
        logger.info(f"   🎯 Min anual return: {self.config.min_annualized_return:.0%}")
        logger.info(f"   🤖 Auto-execute: {self.config.auto_execute}")
    
    def _generate_opportunity_id(self) -> str:
        """Generar ID único para oportunidad"""
        self._opportunity_counter += 1
        return f"FUND_OPP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._opportunity_counter:04d}"
    
    def _generate_position_id(self) -> str:
        """Generar ID único para posición"""
        self._position_counter += 1
        return f"FUND_POS_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._position_counter:04d}"
    
    def _calculate_entry_costs(self, notional: float) -> float:
        """
        Calcular costos de entrada (spot + perp)
        
        Args:
            notional: Valor notional de la posición
            
        Returns:
            Costo total de entrada
        """
        spot_fee = notional * self.TAKER_FEE
        perp_fee = notional * self.TAKER_FEE
        slippage = notional * (self.SLIPPAGE_BPS / 10000) * 2
        
        return spot_fee + perp_fee + slippage
    
    def _calculate_exit_costs(self, notional: float) -> float:
        """
        Calcular costos de salida (cerrar ambas posiciones)
        
        Args:
            notional: Valor notional de la posición
            
        Returns:
            Costo total de salida
        """
        return self._calculate_entry_costs(notional)
    
    def scan_opportunities(self) -> List[FundingOpportunity]:
        """
        Escanear mercado por oportunidades de funding arbitrage
        
        Returns:
            Lista de oportunidades detectadas
        """
        opportunities = []
        
        for symbol in self.SUPPORTED_PAIRS:
            opp = self._analyze_symbol(symbol)
            if opp:
                opportunities.append(opp)
                self.opportunities[opp.opportunity_id] = opp
                self.stats["opportunities_detected"] += 1
        
        opportunities.sort(key=lambda x: x.expected_return_annual, reverse=True)
        
        return opportunities
    
    def _analyze_symbol(self, symbol: str) -> Optional[FundingOpportunity]:
        """
        Analizar un símbolo específico
        
        Args:
            symbol: BTC, ETH, etc.
            
        Returns:
            FundingOpportunity si es rentable
        """
        if not self.futures_client:
            logger.warning(f"No futures client available for {symbol}")
            return None
        
        ticker = self.futures_client.get_ticker(symbol)
        if not ticker:
            return None
        
        funding_rate = ticker.funding_rate
        spot_price = ticker.index_price
        perp_price = ticker.mark_price
        
        if funding_rate < self.config.min_funding_rate:
            return None
        
        basis = (perp_price - spot_price) / spot_price
        
        funding_rate_annual = funding_rate * 3 * 365
        
        if funding_rate_annual < self.config.min_annualized_return:
            return None
        
        notional = 10000
        entry_costs = self._calculate_entry_costs(notional)
        exit_costs = self._calculate_exit_costs(notional)
        total_costs = entry_costs + exit_costs
        
        funding_per_8h = notional * funding_rate
        funding_per_8h_net = funding_per_8h - (total_costs / self.config.funding_collection_periods)
        
        expected_return_8h = funding_per_8h_net / notional
        expected_return_annual = expected_return_8h * 3 * 365
        
        if expected_return_annual < self.config.min_annualized_return:
            return None
        
        risk_score = self._calculate_risk_score(funding_rate, basis, symbol)
        
        return FundingOpportunity(
            opportunity_id=self._generate_opportunity_id(),
            symbol=symbol,
            funding_rate=funding_rate,
            funding_rate_annualized=funding_rate_annual,
            spot_price=spot_price,
            perp_price=perp_price,
            basis=basis,
            expected_return_8h=expected_return_8h,
            expected_return_annual=expected_return_annual,
            entry_cost=entry_costs / notional,
            recommended_size=0.0,
            risk_score=risk_score,
            detected_at=datetime.now(),
            status=OpportunityStatus.DETECTED,
            expires_at=datetime.now() + timedelta(hours=8)
        )
    
    def _calculate_risk_score(self, funding_rate: float, basis: float, 
                               symbol: str) -> float:
        """
        Calcular score de riesgo (0-100, menor = más seguro)
        
        Args:
            funding_rate: Tasa de funding
            basis: Diferencia spot-perp
            symbol: Símbolo
            
        Returns:
            Score de riesgo
        """
        risk = 0.0
        
        if abs(funding_rate) > 0.001:
            risk += 20
        
        if abs(basis) > 0.005:
            risk += 15
        
        symbol_risk = {
            "BTC": 0,
            "ETH": 5,
            "SOL": 15,
            "XRP": 20
        }
        risk += symbol_risk.get(symbol, 25)
        
        if funding_rate > 0.0003:
            risk += 10
        
        return min(100, risk)
    
    def execute_opportunity(self, 
                            opportunity_id: str,
                            position_size_usd: float) -> Optional[FundingPosition]:
        """
        Ejecutar oportunidad de arbitraje
        
        Args:
            opportunity_id: ID de la oportunidad
            position_size_usd: Tamaño en USD
            
        Returns:
            FundingPosition si se ejecutó
        """
        if opportunity_id not in self.opportunities:
            logger.warning(f"⚠️ Oportunidad no encontrada: {opportunity_id}")
            return None
        
        opp = self.opportunities[opportunity_id]
        
        if opp.status != OpportunityStatus.DETECTED:
            logger.warning(f"⚠️ Oportunidad ya procesada: {opp.status.value}")
            return None
        
        if datetime.now() > opp.expires_at:
            opp.status = OpportunityStatus.MISSED
            return None
        
        if len(self.active_positions) >= self.config.max_concurrent_positions:
            logger.warning("⚠️ Máximo de posiciones concurrentes alcanzado")
            return None
        
        spot_size = position_size_usd / opp.spot_price
        perp_size = position_size_usd / opp.perp_price
        
        opp.status = OpportunityStatus.EXECUTING
        
        position = FundingPosition(
            position_id=self._generate_position_id(),
            symbol=opp.symbol,
            spot_size=spot_size,
            spot_entry_price=opp.spot_price,
            perp_size=perp_size,
            perp_entry_price=opp.perp_price,
            total_funding_earned=0.0,
            funding_payments=0,
            pnl=0.0,
            opened_at=datetime.now(),
            last_funding=datetime.now(),
            status="active"
        )
        
        self.active_positions[position.position_id] = position
        opp.status = OpportunityStatus.ACTIVE
        self.stats["opportunities_executed"] += 1
        self.stats["current_positions"] = len(self.active_positions)
        
        logger.info(f"💰 Posición de funding abierta: {position.position_id}")
        logger.info(f"   📊 {opp.symbol}: ${position_size_usd:,.2f}")
        logger.info(f"   📈 Retorno esperado anual: {opp.expected_return_annual:.1%}")
        
        return position
    
    def collect_funding(self, position_id: str, current_funding_rate: float) -> Optional[Dict]:
        """
        Cobrar funding para una posición
        
        Args:
            position_id: ID de la posición
            current_funding_rate: Tasa de funding actual
            
        Returns:
            Dict con detalles del cobro
        """
        if position_id not in self.active_positions:
            return None
        
        pos = self.active_positions[position_id]
        
        notional = pos.perp_size * pos.perp_entry_price
        funding_amount = notional * current_funding_rate
        
        pos.total_funding_earned += funding_amount
        pos.funding_payments += 1
        pos.last_funding = datetime.now()
        pos.pnl = pos.total_funding_earned
        
        self.stats["total_funding_earned"] += funding_amount
        
        logger.info(f"💵 Funding cobrado: ${funding_amount:+,.2f} ({pos.symbol})")
        
        return {
            "position_id": position_id,
            "symbol": pos.symbol,
            "funding_rate": current_funding_rate,
            "funding_amount": funding_amount,
            "total_earned": pos.total_funding_earned,
            "payments": pos.funding_payments,
            "timestamp": datetime.now().isoformat()
        }
    
    def close_position(self, position_id: str, reason: str = "manual") -> Optional[Dict]:
        """
        Cerrar posición de arbitraje
        
        Args:
            position_id: ID de la posición
            reason: Razón del cierre
            
        Returns:
            Dict con resultado
        """
        if position_id not in self.active_positions:
            return None
        
        pos = self.active_positions[position_id]
        
        notional = pos.perp_size * pos.perp_entry_price
        exit_costs = self._calculate_exit_costs(notional)
        
        final_pnl = pos.total_funding_earned - exit_costs
        pos.pnl = final_pnl
        pos.status = "closed"
        
        self.position_history.append(pos)
        del self.active_positions[position_id]
        
        self.stats["current_positions"] = len(self.active_positions)
        self.stats["total_pnl"] += final_pnl
        
        logger.info(f"🔒 Posición de funding cerrada: {position_id}")
        logger.info(f"   💵 PnL final: ${final_pnl:+,.2f}")
        logger.info(f"   📊 Payments colectados: {pos.funding_payments}")
        
        return {
            "position_id": position_id,
            "symbol": pos.symbol,
            "total_funding": pos.total_funding_earned,
            "exit_costs": exit_costs,
            "final_pnl": final_pnl,
            "funding_payments": pos.funding_payments,
            "duration_hours": (datetime.now() - pos.opened_at).total_seconds() / 3600,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_active_positions(self) -> List[Dict]:
        """
        Obtener todas las posiciones activas
        
        Returns:
            Lista de posiciones
        """
        return [
            {
                "position_id": p.position_id,
                "symbol": p.symbol,
                "spot_size": p.spot_size,
                "perp_size": p.perp_size,
                "total_funding": p.total_funding_earned,
                "payments": p.funding_payments,
                "pnl": p.pnl,
                "opened_at": p.opened_at.isoformat(),
                "last_funding": p.last_funding.isoformat()
            }
            for p in self.active_positions.values()
        ]
    
    def get_current_opportunities(self) -> List[Dict]:
        """
        Obtener oportunidades actuales no expiradas
        
        Returns:
            Lista de oportunidades
        """
        now = datetime.now()
        return [
            {
                "opportunity_id": o.opportunity_id,
                "symbol": o.symbol,
                "funding_rate": o.funding_rate,
                "funding_rate_annual": o.funding_rate_annualized,
                "expected_return_annual": o.expected_return_annual,
                "basis": o.basis,
                "risk_score": o.risk_score,
                "status": o.status.value,
                "expires_in_hours": (o.expires_at - now).total_seconds() / 3600
            }
            for o in self.opportunities.values()
            if o.expires_at > now and o.status == OpportunityStatus.DETECTED
        ]
    
    def get_stats(self) -> Dict:
        """
        Obtener estadísticas del arbitraje
        
        Returns:
            Dict con estadísticas
        """
        if self.stats["opportunities_executed"] > 0:
            avg_return = self.stats["total_pnl"] / self.stats["opportunities_executed"]
        else:
            avg_return = 0
        
        return {
            "opportunities_detected": self.stats["opportunities_detected"],
            "opportunities_executed": self.stats["opportunities_executed"],
            "current_positions": self.stats["current_positions"],
            "total_funding_earned": self.stats["total_funding_earned"],
            "total_pnl": self.stats["total_pnl"],
            "avg_pnl_per_position": avg_return,
            "config": {
                "min_funding_rate": self.config.min_funding_rate,
                "min_annual_return": self.config.min_annualized_return,
                "auto_execute": self.config.auto_execute
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def export_for_investors(self) -> Dict:
        """
        Exportar resumen para inversores
        
        Returns:
            Dict formateado para presentación
        """
        stats = self.get_stats()
        
        return {
            "strategy": "Funding Rate Arbitrage",
            "description": "Market-neutral strategy that captures funding payments",
            "performance": {
                "total_pnl": f"${stats['total_pnl']:,.2f}",
                "total_funding_earned": f"${stats['total_funding_earned']:,.2f}",
                "positions_executed": stats["opportunities_executed"]
            },
            "risk_profile": {
                "market_exposure": "Neutral (hedged)",
                "main_risk": "Execution slippage, funding rate reversal",
                "max_drawdown_expected": "<5%"
            },
            "current_status": {
                "active_positions": stats["current_positions"],
                "opportunities_available": len(self.get_current_opportunities())
            },
            "disclaimer": "Past performance does not guarantee future results.",
            "generated": datetime.now().isoformat()
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    analyzer = FundingArbitrageAnalyzer()
    
    print("\n=== Funding Arbitrage Analyzer Test ===\n")
    
    opportunities = analyzer.scan_opportunities()
    
    for opp in opportunities:
        print(f"\n{opp.symbol} Opportunity:")
        print(f"  Funding Rate: {opp.funding_rate:.4%}")
        print(f"  Annual Return: {opp.expected_return_annual:.1%}")
        print(f"  Risk Score: {opp.risk_score:.0f}/100")
    
    if opportunities:
        position = analyzer.execute_opportunity(
            opportunities[0].opportunity_id,
            position_size_usd=10000
        )
        
        if position:
            print(f"\nPosition Opened: {position.position_id}")
            
            result = analyzer.collect_funding(position.position_id, 0.0001)
            print(f"Funding Collected: ${result['funding_amount']:,.2f}")
            
            close_result = analyzer.close_position(position.position_id)
            print(f"\nPosition Closed:")
            print(f"  Final PnL: ${close_result['final_pnl']:+,.2f}")
    
    stats = analyzer.get_stats()
    print(f"\nStats: {stats}")
    
    investor_report = analyzer.export_for_investors()
    print(f"\nInvestor Report:")
    import json
    print(json.dumps(investor_report, indent=2))
