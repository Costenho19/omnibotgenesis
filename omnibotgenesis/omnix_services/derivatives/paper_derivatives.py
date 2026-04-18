"""
Paper Derivatives Manager - OMNIX Premium
==========================================

Simulador de paper trading para derivados:
- Perpetuos BTC/ETH simulados
- Funding rates realistas
- Liquidaciones simuladas
- Track record para inversores
- Integración con MarginEngine

Diseñado para construir historial creíble.
"""

import logging
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class DerivativeOrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class DerivativeOrderSide(Enum):
    LONG = "long"
    SHORT = "short"


class DerivativeOrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    LIQUIDATED = "liquidated"


@dataclass
class DerivativeTrade:
    """Trade de derivados ejecutado"""
    trade_id: str
    symbol: str
    side: DerivativeOrderSide
    size: float
    entry_price: float
    leverage: float
    margin_used: float
    timestamp: datetime
    order_type: DerivativeOrderType
    status: DerivativeOrderStatus
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    funding_paid: float = 0.0
    close_timestamp: Optional[datetime] = None
    close_reason: Optional[str] = None


@dataclass
class DerivativePosition:
    """Posición abierta en derivados"""
    position_id: str
    symbol: str
    side: DerivativeOrderSide
    size: float
    entry_price: float
    leverage: float
    margin_used: float
    liquidation_price: float
    unrealized_pnl: float
    funding_accumulated: float
    open_timestamp: datetime
    last_update: datetime


class PaperDerivativesManager:
    """
    Gestor de Paper Trading para Derivados
    
    Características:
    - Balance virtual separado de spot
    - Simulación realista de perpetuos
    - Funding rates cada 8 horas
    - Liquidaciones automáticas
    - Historial completo para auditoría
    """
    
    DEFAULT_FUNDING_RATE = 0.0001
    FUNDING_INTERVAL_HOURS = 8
    
    TAKER_FEE = 0.0006
    MAKER_FEE = 0.0002
    
    SLIPPAGE_BPS = 5
    
    def __init__(self, 
                 initial_balance: float = 100_000.0,
                 max_leverage: float = 3.0):
        """
        Inicializar Paper Derivatives Manager
        
        Args:
            initial_balance: Balance inicial para derivados
            max_leverage: Apalancamiento máximo (máx 3.0)
        """
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.max_leverage = min(max_leverage, 3.0)
        
        self.positions: Dict[str, DerivativePosition] = {}
        self.trade_history: List[DerivativeTrade] = []
        self.funding_history: List[Dict] = []
        
        self._trade_counter = 0
        self._last_funding_time = datetime.now()
        
        self.stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "total_funding_paid": 0.0,
            "total_fees_paid": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "max_drawdown": 0.0,
            "peak_balance": initial_balance
        }
        
        logger.info(f"📊 PaperDerivativesManager inicializado")
        logger.info(f"   💵 Balance inicial: ${initial_balance:,.2f}")
        logger.info(f"   📈 Max leverage: {self.max_leverage}x")
    
    def _generate_trade_id(self) -> str:
        """Generar ID único para trade"""
        self._trade_counter += 1
        return f"DRV_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._trade_counter:04d}"
    
    def _calculate_liquidation_price(self, 
                                      entry_price: float, 
                                      side: DerivativeOrderSide,
                                      leverage: float) -> float:
        """
        Calcular precio de liquidación
        
        Args:
            entry_price: Precio de entrada
            side: LONG o SHORT
            leverage: Apalancamiento
            
        Returns:
            Precio de liquidación
        """
        maintenance_margin = 0.25
        liquidation_distance = entry_price * (1 - maintenance_margin) / leverage
        
        if side == DerivativeOrderSide.LONG:
            return entry_price - liquidation_distance
        else:
            return entry_price + liquidation_distance
    
    def _apply_slippage(self, price: float, side: DerivativeOrderSide) -> float:
        """Aplicar slippage realista"""
        slippage = price * (self.SLIPPAGE_BPS / 10000)
        if side == DerivativeOrderSide.LONG:
            return price + slippage
        else:
            return price - slippage
    
    def _calculate_fee(self, notional: float, is_taker: bool = True) -> float:
        """Calcular fee de trading"""
        fee_rate = self.TAKER_FEE if is_taker else self.MAKER_FEE
        return notional * fee_rate
    
    def open_position(self,
                      symbol: str,
                      side: DerivativeOrderSide,
                      size: float,
                      current_price: float,
                      leverage: float = 1.0,
                      order_type: DerivativeOrderType = DerivativeOrderType.MARKET) -> Optional[DerivativeTrade]:
        """
        Abrir posición de derivados
        
        Args:
            symbol: BTC, ETH, etc.
            side: LONG o SHORT
            size: Tamaño de la posición
            current_price: Precio actual
            leverage: Apalancamiento (máx 3x)
            order_type: Tipo de orden
            
        Returns:
            DerivativeTrade si se ejecutó
        """
        leverage = min(leverage, self.max_leverage)
        
        entry_price = self._apply_slippage(current_price, side)
        notional = size * entry_price
        margin_required = notional / leverage
        
        fee = self._calculate_fee(notional)
        total_required = margin_required + fee
        
        if total_required > self.current_balance:
            logger.warning(f"⚠️ Balance insuficiente: necesita ${total_required:,.2f}, disponible ${self.current_balance:,.2f}")
            return None
        
        total_exposure = sum(p.size * p.entry_price for p in self.positions.values())
        new_exposure = total_exposure + notional
        portfolio_leverage = new_exposure / self.current_balance if self.current_balance > 0 else 0
        
        if portfolio_leverage > self.max_leverage:
            logger.warning(f"⚠️ Leverage total {portfolio_leverage:.2f}x excedería máximo ({self.max_leverage}x)")
            return None
        
        self.current_balance -= (margin_required + fee)
        self.stats["total_fees_paid"] += fee
        
        liquidation_price = self._calculate_liquidation_price(entry_price, side, leverage)
        
        trade_id = self._generate_trade_id()
        position_id = f"POS_{trade_id}"
        
        trade = DerivativeTrade(
            trade_id=trade_id,
            symbol=symbol.upper(),
            side=side,
            size=size,
            entry_price=entry_price,
            leverage=leverage,
            margin_used=margin_required,
            timestamp=datetime.now(),
            order_type=order_type,
            status=DerivativeOrderStatus.FILLED
        )
        
        position = DerivativePosition(
            position_id=position_id,
            symbol=symbol.upper(),
            side=side,
            size=size,
            entry_price=entry_price,
            leverage=leverage,
            margin_used=margin_required,
            liquidation_price=liquidation_price,
            unrealized_pnl=0.0,
            funding_accumulated=0.0,
            open_timestamp=datetime.now(),
            last_update=datetime.now()
        )
        
        self.positions[position_id] = position
        self.trade_history.append(trade)
        self.stats["total_trades"] += 1
        
        logger.info(f"📈 Posición abierta: {side.value.upper()} {size} {symbol} @ ${entry_price:,.2f}")
        logger.info(f"   💰 Margen: ${margin_required:,.2f} | Leverage: {leverage}x")
        logger.info(f"   💀 Liquidación: ${liquidation_price:,.2f}")
        logger.info(f"   📋 Trade ID: {trade_id}")
        
        return trade
    
    def close_position(self,
                       position_id: str,
                       current_price: float,
                       reason: str = "manual") -> Optional[DerivativeTrade]:
        """
        Cerrar posición existente
        
        Args:
            position_id: ID de la posición
            current_price: Precio actual
            reason: Razón del cierre
            
        Returns:
            DerivativeTrade con resultado
        """
        if position_id not in self.positions:
            logger.warning(f"⚠️ Posición no encontrada: {position_id}")
            return None
        
        position = self.positions[position_id]
        
        if position.side == DerivativeOrderSide.LONG:
            exit_price = current_price * (1 - self.SLIPPAGE_BPS / 10000)
        else:
            exit_price = current_price * (1 + self.SLIPPAGE_BPS / 10000)
        
        if position.side == DerivativeOrderSide.LONG:
            pnl = (exit_price - position.entry_price) * position.size
        else:
            pnl = (position.entry_price - exit_price) * position.size
        
        pnl -= position.funding_accumulated
        
        notional = position.size * exit_price
        exit_fee = self._calculate_fee(notional)
        pnl -= exit_fee
        
        pnl_pct = pnl / position.margin_used if position.margin_used > 0 else 0
        
        self.current_balance += position.margin_used + pnl
        self.stats["total_fees_paid"] += exit_fee
        self.stats["total_pnl"] += pnl
        
        if pnl > 0:
            self.stats["winning_trades"] += 1
            if pnl > self.stats["largest_win"]:
                self.stats["largest_win"] = pnl
        else:
            self.stats["losing_trades"] += 1
            if pnl < self.stats["largest_loss"]:
                self.stats["largest_loss"] = pnl
        
        if self.current_balance > self.stats["peak_balance"]:
            self.stats["peak_balance"] = self.current_balance
        
        drawdown = (self.stats["peak_balance"] - self.current_balance) / self.stats["peak_balance"]
        if drawdown > self.stats["max_drawdown"]:
            self.stats["max_drawdown"] = drawdown
        
        trade = DerivativeTrade(
            trade_id=self._generate_trade_id(),
            symbol=position.symbol,
            side=position.side,
            size=position.size,
            entry_price=position.entry_price,
            leverage=position.leverage,
            margin_used=position.margin_used,
            timestamp=position.open_timestamp,
            order_type=DerivativeOrderType.MARKET,
            status=DerivativeOrderStatus.FILLED,
            exit_price=exit_price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            funding_paid=position.funding_accumulated,
            close_timestamp=datetime.now(),
            close_reason=reason
        )
        
        self.trade_history.append(trade)
        
        del self.positions[position_id]
        
        pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
        logger.info(f"📉 Posición cerrada: {position.symbol} {position.side.value}")
        logger.info(f"   💵 PnL: {pnl_str} ({pnl_pct:+.2%})")
        logger.info(f"   📋 Razón: {reason}")
        
        return trade
    
    def update_positions(self, prices: Dict[str, float]) -> List[Dict]:
        """
        Actualizar todas las posiciones con precios actuales
        
        Args:
            prices: Dict con symbol -> precio actual
            
        Returns:
            Lista de eventos (liquidaciones, etc.)
        """
        events = []
        positions_to_close = []
        
        for position_id, position in self.positions.items():
            current_price = prices.get(position.symbol)
            if not current_price:
                continue
            
            if position.side == DerivativeOrderSide.LONG:
                unrealized_pnl = (current_price - position.entry_price) * position.size
            else:
                unrealized_pnl = (position.entry_price - current_price) * position.size
            
            position.unrealized_pnl = unrealized_pnl
            position.last_update = datetime.now()
            
            if position.side == DerivativeOrderSide.LONG:
                is_liquidated = current_price <= position.liquidation_price
            else:
                is_liquidated = current_price >= position.liquidation_price
            
            if is_liquidated:
                positions_to_close.append((position_id, "liquidation"))
                events.append({
                    "type": "LIQUIDATION",
                    "position_id": position_id,
                    "symbol": position.symbol,
                    "side": position.side.value,
                    "price": current_price,
                    "liquidation_price": position.liquidation_price,
                    "loss": position.margin_used,
                    "timestamp": datetime.now()
                })
                logger.warning(f"💀 LIQUIDACIÓN: {position.symbol} {position.side.value} @ ${current_price:,.2f}")
        
        for position_id, reason in positions_to_close:
            self.close_position(position_id, prices.get(self.positions[position_id].symbol, 0), reason)
        
        return events
    
    def apply_funding(self, funding_rates: Dict[str, float]) -> float:
        """
        Aplicar funding rates a posiciones abiertas
        
        Args:
            funding_rates: Dict con symbol -> funding rate
            
        Returns:
            Total funding pagado/recibido
        """
        total_funding = 0.0
        
        for position_id, position in self.positions.items():
            rate = funding_rates.get(position.symbol, self.DEFAULT_FUNDING_RATE)
            
            notional = position.size * position.entry_price
            
            if position.side == DerivativeOrderSide.LONG:
                funding = notional * rate
            else:
                funding = -notional * rate
            
            position.funding_accumulated += funding
            total_funding += funding
            
            self.funding_history.append({
                "position_id": position_id,
                "symbol": position.symbol,
                "side": position.side.value,
                "funding_rate": rate,
                "funding_paid": funding,
                "timestamp": datetime.now()
            })
        
        if total_funding != 0:
            self.current_balance -= total_funding
            self.stats["total_funding_paid"] += total_funding
            
            if total_funding > 0:
                logger.info(f"💸 Funding pagado: ${total_funding:,.2f}")
            else:
                logger.info(f"💰 Funding recibido: ${abs(total_funding):,.2f}")
        
        self._last_funding_time = datetime.now()
        
        return total_funding
    
    def get_position(self, position_id: str) -> Optional[DerivativePosition]:
        """Obtener posición por ID"""
        return self.positions.get(position_id)
    
    def get_all_positions(self) -> List[DerivativePosition]:
        """Obtener todas las posiciones abiertas"""
        return list(self.positions.values())
    
    def get_position_by_symbol(self, symbol: str) -> Optional[DerivativePosition]:
        """Obtener posición por símbolo"""
        for pos in self.positions.values():
            if pos.symbol == symbol.upper():
                return pos
        return None
    
    def get_portfolio_stats(self) -> Dict:
        """
        Obtener estadísticas del portfolio de derivados
        
        Returns:
            Dict con métricas completas
        """
        total_unrealized = sum(p.unrealized_pnl for p in self.positions.values())
        total_margin = sum(p.margin_used for p in self.positions.values())
        total_notional = sum(p.size * p.entry_price for p in self.positions.values())
        
        portfolio_leverage = total_notional / self.current_balance if self.current_balance > 0 else 0
        
        win_rate = self.stats["winning_trades"] / self.stats["total_trades"] if self.stats["total_trades"] > 0 else 0
        
        return {
            "balance": self.current_balance,
            "initial_balance": self.initial_balance,
            "total_pnl": self.stats["total_pnl"],
            "total_pnl_pct": (self.current_balance - self.initial_balance) / self.initial_balance,
            "unrealized_pnl": total_unrealized,
            "open_positions": len(self.positions),
            "total_margin_used": total_margin,
            "total_notional": total_notional,
            "portfolio_leverage": portfolio_leverage,
            "max_leverage": self.max_leverage,
            "total_trades": self.stats["total_trades"],
            "winning_trades": self.stats["winning_trades"],
            "losing_trades": self.stats["losing_trades"],
            "win_rate": win_rate,
            "largest_win": self.stats["largest_win"],
            "largest_loss": self.stats["largest_loss"],
            "max_drawdown": self.stats["max_drawdown"],
            "total_fees": self.stats["total_fees_paid"],
            "total_funding": self.stats["total_funding_paid"],
            "peak_balance": self.stats["peak_balance"],
            "timestamp": datetime.now().isoformat()
        }
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """
        Obtener historial de trades
        
        Args:
            limit: Máximo número de trades
            
        Returns:
            Lista de trades como dicts
        """
        trades = self.trade_history[-limit:]
        
        return [
            {
                "trade_id": t.trade_id,
                "symbol": t.symbol,
                "side": t.side.value,
                "size": t.size,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "leverage": t.leverage,
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct,
                "status": t.status.value,
                "timestamp": t.timestamp.isoformat(),
                "close_timestamp": t.close_timestamp.isoformat() if t.close_timestamp else None,
                "close_reason": t.close_reason
            }
            for t in trades
        ]
    
    def export_for_investors(self) -> Dict:
        """
        Exportar datos para presentación a inversores
        
        Returns:
            Dict formateado para inversores
        """
        stats = self.get_portfolio_stats()
        
        return {
            "module": "OMNIX Derivatives Paper Trading",
            "period": {
                "start": self.trade_history[0].timestamp.isoformat() if self.trade_history else None,
                "end": datetime.now().isoformat()
            },
            "performance": {
                "initial_capital": f"${self.initial_balance:,.2f}",
                "current_value": f"${self.current_balance:,.2f}",
                "total_return": f"{stats['total_pnl_pct']:.2%}",
                "max_drawdown": f"{stats['max_drawdown']:.2%}"
            },
            "trading_stats": {
                "total_trades": stats["total_trades"],
                "win_rate": f"{stats['win_rate']:.1%}",
                "largest_win": f"${stats['largest_win']:,.2f}",
                "largest_loss": f"${abs(stats['largest_loss']):,.2f}"
            },
            "risk_management": {
                "max_leverage_used": f"{self.max_leverage}x",
                "portfolio_leverage": f"{stats['portfolio_leverage']:.2f}x",
                "open_positions": stats["open_positions"]
            },
            "costs": {
                "total_fees": f"${stats['total_fees']:,.2f}",
                "total_funding": f"${stats['total_funding']:,.2f}"
            },
            "disclaimer": "Paper trading results. Past performance does not guarantee future results.",
            "generated": datetime.now().isoformat()
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    manager = PaperDerivativesManager(
        initial_balance=100_000,
        max_leverage=3.0
    )
    
    print("\n=== Paper Derivatives Test ===\n")
    
    trade1 = manager.open_position(
        symbol="BTC",
        side=DerivativeOrderSide.LONG,
        size=0.5,
        current_price=95000,
        leverage=2.0
    )
    
    trade2 = manager.open_position(
        symbol="ETH",
        side=DerivativeOrderSide.SHORT,
        size=5.0,
        current_price=3500,
        leverage=2.0
    )
    
    manager.update_positions({"BTC": 96000, "ETH": 3400})
    
    manager.apply_funding({"BTC": 0.0001, "ETH": -0.00005})
    
    stats = manager.get_portfolio_stats()
    print(f"\n=== Portfolio Stats ===")
    print(f"Balance: ${stats['balance']:,.2f}")
    print(f"Unrealized PnL: ${stats['unrealized_pnl']:,.2f}")
    print(f"Portfolio Leverage: {stats['portfolio_leverage']:.2f}x")
    
    for pos in manager.get_all_positions():
        manager.close_position(pos.position_id, 96000 if pos.symbol == "BTC" else 3400)
    
    investor_report = manager.export_for_investors()
    print(f"\n=== Investor Report ===")
    print(json.dumps(investor_report, indent=2))
