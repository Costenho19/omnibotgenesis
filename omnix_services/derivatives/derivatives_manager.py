"""
Derivatives Manager - OMNIX Premium Orchestrator
=================================================

Orquestador principal para el módulo de derivados:
- Coordina KrakenFuturesClient, MarginEngine, PaperDerivatives
- Integración con RMS (Risk Management System)
- Routing automático paper/live
- Métricas para inversores

Este es el punto de entrada principal para derivados.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .kraken_futures_client import KrakenFuturesClient, FuturesTicker, OrderSide, OrderType
from .margin_engine import MarginEngine, MarginStatus, MarginLevel
from .paper_derivatives import PaperDerivativesManager, DerivativeOrderSide, DerivativeOrderType

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    PAPER = "paper"
    LIVE = "live"


@dataclass
class DerivativesConfig:
    """Configuración del módulo de derivados"""
    trading_mode: TradingMode = TradingMode.PAPER
    initial_capital: float = 100_000.0
    max_leverage: float = 3.0
    risk_tolerance: str = "conservative"
    auto_hedge: bool = False
    funding_arbitrage: bool = False
    
    max_position_size_pct: float = 0.20
    max_single_loss_pct: float = 0.02
    daily_loss_limit_pct: float = 0.05
    
    enable_stop_loss: bool = True
    default_stop_loss_pct: float = 0.05
    enable_take_profit: bool = True
    default_take_profit_pct: float = 0.10


class DerivativesManager:
    """
    Gestor Principal de Derivados OMNIX
    
    Características:
    - Modo paper/live configurable
    - Integración con MarginEngine para control de riesgo
    - Conexión a RMS para alertas y circuit breakers
    - API unificada para Telegram y otros módulos
    """
    
    def __init__(self, config: Optional[DerivativesConfig] = None):
        """
        Inicializar Derivatives Manager
        
        Args:
            config: Configuración del módulo (usa defaults si None)
        """
        self.config = config or DerivativesConfig()
        
        self.mode = self.config.trading_mode
        
        demo_mode = self.mode == TradingMode.PAPER
        self.futures_client = KrakenFuturesClient(demo_mode=demo_mode)
        
        self.margin_engine = MarginEngine(
            initial_capital=self.config.initial_capital,
            max_leverage=self.config.max_leverage,
            risk_tolerance=self.config.risk_tolerance
        )
        
        self.paper_manager = PaperDerivativesManager(
            initial_balance=self.config.initial_capital,
            max_leverage=self.config.max_leverage
        )
        
        self._rms = None
        self._alert_dispatcher = None
        
        self._daily_pnl = 0.0
        self._daily_trades = 0
        self._last_reset = datetime.now().date()
        
        self._is_halted = False
        self._halt_reason = None
        
        logger.info(f"🚀 DerivativesManager inicializado")
        logger.info(f"   📊 Modo: {self.mode.value.upper()}")
        logger.info(f"   💰 Capital: ${self.config.initial_capital:,.2f}")
        logger.info(f"   📈 Max Leverage: {self.config.max_leverage}x")
    
    def connect_rms(self, limits_engine: Any = None, circuit_breaker: Any = None, 
                    alert_dispatcher: Any = None) -> None:
        """
        Conectar con el Risk Management System
        
        Args:
            limits_engine: LimitsEngine del RMS
            circuit_breaker: CircuitBreaker del RMS
            alert_dispatcher: AlertDispatcher del RMS
        """
        self._rms = {
            "limits_engine": limits_engine,
            "circuit_breaker": circuit_breaker
        }
        self._alert_dispatcher = alert_dispatcher
        
        logger.info("🛡️ DerivativesManager conectado a RMS")
    
    def _check_daily_reset(self):
        """Resetear contadores diarios si es nuevo día"""
        today = datetime.now().date()
        if today != self._last_reset:
            self._daily_pnl = 0.0
            self._daily_trades = 0
            self._last_reset = today
            logger.info("🔄 Contadores diarios reseteados")
    
    def _pre_trade_validation(self, symbol: str, size: float, 
                               leverage: float, side: str) -> Tuple[bool, str]:
        """
        Validación pre-trade con todas las reglas
        
        Args:
            symbol: Símbolo
            size: Tamaño
            leverage: Apalancamiento
            side: long/short
            
        Returns:
            (puede_operar, razón)
        """
        self._check_daily_reset()
        
        if self._is_halted:
            return False, f"Trading detenido: {self._halt_reason}"
        
        if leverage > self.config.max_leverage:
            return False, f"Leverage {leverage}x excede máximo ({self.config.max_leverage}x)"
        
        ticker = self.futures_client.get_ticker(symbol)
        if not ticker:
            return False, f"No se pudo obtener precio para {symbol}"
        
        notional = size * ticker.mark_price
        capital = self.paper_manager.current_balance if self.mode == TradingMode.PAPER else self.config.initial_capital
        position_pct = notional / capital
        
        if position_pct > self.config.max_position_size_pct:
            return False, f"Tamaño {position_pct:.1%} excede máximo ({self.config.max_position_size_pct:.1%})"
        
        daily_loss_pct = abs(self._daily_pnl) / capital if self._daily_pnl < 0 else 0
        if daily_loss_pct >= self.config.daily_loss_limit_pct:
            return False, f"Límite de pérdida diaria alcanzado ({daily_loss_pct:.1%})"
        
        margin_status = self.margin_engine.get_margin_status()
        if not margin_status.can_trade:
            return False, f"Trading bloqueado por margen: {margin_status.margin_level.value} - {margin_status.warnings[0] if margin_status.warnings else 'Margen insuficiente'}"
        
        if self._rms and self._rms.get("limits_engine"):
            pass
        
        return True, "OK"
    
    def open_position(self, 
                      symbol: str,
                      side: str,
                      size: float,
                      leverage: float = 1.0,
                      stop_loss_pct: Optional[float] = None,
                      take_profit_pct: Optional[float] = None) -> Dict[str, Any]:
        """
        Abrir posición de derivados
        
        Args:
            symbol: BTC, ETH, etc.
            side: "long" o "short"
            size: Tamaño de la posición
            leverage: Apalancamiento (máx 3x)
            stop_loss_pct: Stop loss en % (opcional)
            take_profit_pct: Take profit en % (opcional)
            
        Returns:
            Dict con resultado de la operación
        """
        can_trade, reason = self._pre_trade_validation(symbol, size, leverage, side)
        if not can_trade:
            logger.warning(f"⚠️ Trade rechazado: {reason}")
            return {
                "success": False,
                "error": reason,
                "symbol": symbol,
                "side": side,
                "size": size
            }
        
        ticker = self.futures_client.get_ticker(symbol)
        if not ticker:
            return {"success": False, "error": "No se pudo obtener precio"}
        
        current_price = ticker.mark_price
        
        order_side = DerivativeOrderSide.LONG if side.lower() == "long" else DerivativeOrderSide.SHORT
        
        if self.mode == TradingMode.PAPER:
            trade = self.paper_manager.open_position(
                symbol=symbol,
                side=order_side,
                size=size,
                current_price=current_price,
                leverage=leverage
            )
            
            if trade:
                self.margin_engine.add_position(symbol, size if side == "long" else -size, 
                                                 current_price, leverage)
                self._daily_trades += 1
                
                return {
                    "success": True,
                    "mode": "PAPER",
                    "trade_id": trade.trade_id,
                    "symbol": symbol,
                    "side": side,
                    "size": size,
                    "entry_price": trade.entry_price,
                    "leverage": leverage,
                    "margin_used": trade.margin_used,
                    "timestamp": trade.timestamp.isoformat()
                }
            else:
                return {"success": False, "error": "No se pudo abrir posición paper"}
        
        else:
            order_side_api = OrderSide.BUY if side.lower() == "long" else OrderSide.SELL
            
            result = self.futures_client.place_order(
                symbol=symbol,
                side=order_side_api,
                size=size,
                order_type=OrderType.MARKET,
                leverage=leverage
            )
            
            if result:
                self.margin_engine.add_position(symbol, size if side == "long" else -size,
                                                 current_price, leverage)
                self._daily_trades += 1
                
                return {
                    "success": True,
                    "mode": "LIVE",
                    "order_id": result.get("order_id"),
                    "symbol": symbol,
                    "side": side,
                    "size": size,
                    "price": current_price,
                    "leverage": leverage,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Error ejecutando orden en exchange"}
    
    def close_position(self, symbol: str, reason: str = "manual") -> Dict[str, Any]:
        """
        Cerrar posición existente
        
        Args:
            symbol: Símbolo de la posición
            reason: Razón del cierre
            
        Returns:
            Dict con resultado
        """
        ticker = self.futures_client.get_ticker(symbol)
        if not ticker:
            return {"success": False, "error": "No se pudo obtener precio"}
        
        current_price = ticker.mark_price
        
        if self.mode == TradingMode.PAPER:
            position = self.paper_manager.get_position_by_symbol(symbol)
            if not position:
                return {"success": False, "error": f"No hay posición abierta para {symbol}"}
            
            trade = self.paper_manager.close_position(position.position_id, current_price, reason)
            
            if trade:
                self._daily_pnl += trade.pnl or 0
                
                if self._alert_dispatcher and trade.pnl:
                    if trade.pnl > 0:
                        pass
                
                return {
                    "success": True,
                    "mode": "PAPER",
                    "trade_id": trade.trade_id,
                    "symbol": symbol,
                    "exit_price": trade.exit_price,
                    "pnl": trade.pnl,
                    "pnl_pct": trade.pnl_pct,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Error cerrando posición"}
        
        else:
            result = self.futures_client.close_position(symbol)
            if result:
                return {
                    "success": True,
                    "mode": "LIVE",
                    "symbol": symbol,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Error cerrando posición en exchange"}
    
    def get_positions(self) -> List[Dict]:
        """
        Obtener todas las posiciones abiertas
        
        Returns:
            Lista de posiciones
        """
        if self.mode == TradingMode.PAPER:
            positions = self.paper_manager.get_all_positions()
            return [
                {
                    "position_id": p.position_id,
                    "symbol": p.symbol,
                    "side": p.side.value,
                    "size": p.size,
                    "entry_price": p.entry_price,
                    "leverage": p.leverage,
                    "unrealized_pnl": p.unrealized_pnl,
                    "liquidation_price": p.liquidation_price,
                    "margin_used": p.margin_used,
                    "open_time": p.open_timestamp.isoformat()
                }
                for p in positions
            ]
        else:
            return [
                {
                    "symbol": p.symbol,
                    "side": p.side,
                    "size": p.size,
                    "entry_price": p.entry_price,
                    "mark_price": p.mark_price,
                    "unrealized_pnl": p.unrealized_pnl,
                    "leverage": p.leverage,
                    "liquidation_price": p.liquidation_price
                }
                for p in self.futures_client.get_positions()
            ]
    
    def update_prices(self) -> Dict[str, float]:
        """
        Actualizar precios y posiciones
        
        Returns:
            Dict con precios actuales
        """
        tickers = self.futures_client.get_all_tickers()
        
        prices = {symbol: ticker.mark_price for symbol, ticker in tickers.items()}
        
        if self.mode == TradingMode.PAPER:
            events = self.paper_manager.update_positions(prices)
            
            for event in events:
                if event["type"] == "LIQUIDATION":
                    self._handle_liquidation(event)
        
        return prices
    
    def _handle_liquidation(self, event: Dict):
        """Manejar evento de liquidación"""
        logger.error(f"💀 LIQUIDACIÓN: {event['symbol']} - Pérdida: ${event['loss']:,.2f}")
        
        if self._alert_dispatcher:
            pass
        
        self._daily_pnl -= event["loss"]
    
    def apply_funding_rates(self) -> Dict[str, Any]:
        """
        Aplicar funding rates a posiciones
        
        Returns:
            Dict con funding aplicado
        """
        funding_rates = {}
        for symbol in ["BTC", "ETH", "SOL", "XRP"]:
            funding = self.futures_client.get_funding_rate(symbol)
            if funding:
                funding_rates[symbol] = funding.rate
        
        if self.mode == TradingMode.PAPER:
            total = self.paper_manager.apply_funding(funding_rates)
            return {
                "success": True,
                "total_funding": total,
                "rates": funding_rates,
                "timestamp": datetime.now().isoformat()
            }
        
        return {"success": True, "rates": funding_rates}
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """
        Obtener datos de mercado para un símbolo
        
        Args:
            symbol: BTC, ETH, etc.
            
        Returns:
            Dict con datos de mercado
        """
        ticker = self.futures_client.get_ticker(symbol)
        if not ticker:
            return None
        
        return {
            "symbol": symbol,
            "mark_price": ticker.mark_price,
            "index_price": ticker.index_price,
            "bid": ticker.bid,
            "ask": ticker.ask,
            "spread": ticker.ask - ticker.bid,
            "spread_pct": (ticker.ask - ticker.bid) / ticker.mark_price,
            "funding_rate": ticker.funding_rate,
            "funding_rate_annualized": ticker.funding_rate * 3 * 365,
            "volume_24h": ticker.volume_24h,
            "open_interest": ticker.open_interest,
            "timestamp": ticker.timestamp.isoformat()
        }
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen del portfolio de derivados
        
        Returns:
            Dict con resumen completo
        """
        if self.mode == TradingMode.PAPER:
            stats = self.paper_manager.get_portfolio_stats()
        else:
            account = self.futures_client.get_account_info()
            stats = account if account else {}
        
        margin_status = self.margin_engine.get_margin_status()
        
        return {
            "mode": self.mode.value.upper(),
            "portfolio": stats,
            "margin": {
                "equity": margin_status.total_equity,
                "available": margin_status.available_margin,
                "used": margin_status.used_margin,
                "ratio": margin_status.margin_ratio,
                "level": margin_status.margin_level.value,
                "leverage": margin_status.effective_leverage,
                "can_trade": margin_status.can_trade,
                "warnings": margin_status.warnings
            },
            "daily": {
                "pnl": self._daily_pnl,
                "trades": self._daily_trades
            },
            "is_halted": self._is_halted,
            "halt_reason": self._halt_reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def halt_trading(self, reason: str = "Manual halt"):
        """Detener trading de derivados"""
        self._is_halted = True
        self._halt_reason = reason
        logger.warning(f"🛑 Trading de derivados DETENIDO: {reason}")
    
    def resume_trading(self):
        """Reanudar trading de derivados"""
        self._is_halted = False
        self._halt_reason = None
        logger.info("✅ Trading de derivados REANUDADO")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtener estado del módulo
        
        Returns:
            Dict con estado completo
        """
        client_status = self.futures_client.get_status()
        
        return {
            "module": "OMNIX Derivatives Manager",
            "version": "1.0.0",
            "mode": self.mode.value.upper(),
            "is_halted": self._is_halted,
            "halt_reason": self._halt_reason,
            "config": {
                "max_leverage": self.config.max_leverage,
                "max_position_pct": self.config.max_position_size_pct,
                "daily_loss_limit": self.config.daily_loss_limit_pct,
                "risk_tolerance": self.config.risk_tolerance
            },
            "futures_client": client_status,
            "rms_connected": self._rms is not None,
            "timestamp": datetime.now().isoformat()
        }
    
    def export_investor_report(self) -> Dict:
        """
        Exportar reporte para inversores
        
        Returns:
            Dict formateado para presentación
        """
        if self.mode == TradingMode.PAPER:
            return self.paper_manager.export_for_investors()
        else:
            summary = self.get_portfolio_summary()
            return {
                "module": "OMNIX Derivatives Live Trading",
                "performance": summary["portfolio"],
                "risk": summary["margin"],
                "disclaimer": "Live trading results. Past performance does not guarantee future results.",
                "generated": datetime.now().isoformat()
            }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    config = DerivativesConfig(
        trading_mode=TradingMode.PAPER,
        initial_capital=100_000,
        max_leverage=3.0,
        risk_tolerance="conservative"
    )
    
    manager = DerivativesManager(config)
    
    print("\n=== Derivatives Manager Test ===\n")
    
    status = manager.get_status()
    print(f"Estado: {status['mode']}")
    
    result = manager.open_position(
        symbol="BTC",
        side="long",
        size=0.5,
        leverage=2.0
    )
    print(f"\nOpen Position: {result}")
    
    positions = manager.get_positions()
    print(f"\nPositions: {len(positions)}")
    
    prices = manager.update_prices()
    print(f"\nPrices updated: {list(prices.keys())}")
    
    summary = manager.get_portfolio_summary()
    print(f"\nPortfolio Summary:")
    print(f"  Mode: {summary['mode']}")
    print(f"  Margin Level: {summary['margin']['level']}")
    print(f"  Can Trade: {summary['margin']['can_trade']}")
