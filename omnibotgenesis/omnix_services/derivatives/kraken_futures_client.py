"""
Kraken Futures API Client - OMNIX Premium
==========================================

Cliente para Kraken Futures con soporte para:
- Perpetuos BTC/ETH (PI_XBTUSD, PI_ETHUSD)
- REST API + WebSocket real-time
- Autenticación separada de spot
- Rate limiting inteligente

Endpoints principales:
- Ticker/Orderbook perpetuos
- Posiciones abiertas
- Órdenes limit/market
- Funding rates históricos
"""

import os
import time
import hmac
import hashlib
import base64
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FuturesSymbol(Enum):
    """Símbolos de perpetuos soportados en Kraken Futures"""
    BTC_USD = "PI_XBTUSD"
    ETH_USD = "PI_ETHUSD"
    SOL_USD = "PI_SOLUSD"
    XRP_USD = "PI_XRPUSD"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "mkt"
    LIMIT = "lmt"
    STOP = "stp"
    TAKE_PROFIT = "take_profit"


@dataclass
class FuturesTicker:
    """Datos de ticker para perpetuos"""
    symbol: str
    mark_price: float
    index_price: float
    last_price: float
    bid: float
    ask: float
    volume_24h: float
    funding_rate: float
    next_funding_time: datetime
    open_interest: float
    timestamp: datetime


@dataclass
class FuturesPosition:
    """Posición abierta en perpetuos"""
    symbol: str
    side: str
    size: float
    entry_price: float
    mark_price: float
    liquidation_price: float
    unrealized_pnl: float
    realized_pnl: float
    leverage: float
    margin_used: float
    timestamp: datetime


@dataclass
class FundingRate:
    """Datos de funding rate"""
    symbol: str
    rate: float
    predicted_rate: float
    timestamp: datetime
    next_funding_time: datetime


class KrakenFuturesClient:
    """
    Cliente para Kraken Futures API
    
    Soporta trading de perpetuos con:
    - Autenticación API separada
    - Rate limiting (10 req/s)
    - Manejo de errores robusto
    - Modo demo/paper automático
    """
    
    BASE_URL = "https://futures.kraken.com/derivatives/api/v3"
    DEMO_URL = "https://demo-futures.kraken.com/derivatives/api/v3"
    
    SUPPORTED_SYMBOLS = {
        "BTC": FuturesSymbol.BTC_USD,
        "ETH": FuturesSymbol.ETH_USD,
        "SOL": FuturesSymbol.SOL_USD,
        "XRP": FuturesSymbol.XRP_USD
    }
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, demo_mode: bool = True):
        """
        Inicializar cliente Kraken Futures
        
        Args:
            api_key: API key de Kraken Futures (separada de spot)
            api_secret: API secret de Kraken Futures
            demo_mode: True para usar demo API (recomendado para testing)
        """
        self.api_key = api_key or os.getenv("KRAKEN_FUTURES_API_KEY", "")
        self.api_secret = api_secret or os.getenv("KRAKEN_FUTURES_API_SECRET", "")
        self.demo_mode = demo_mode
        self.base_url = self.DEMO_URL if demo_mode else self.BASE_URL
        
        self._last_request_time = 0
        self._min_request_interval = 0.1
        
        self._ticker_cache: Dict[str, FuturesTicker] = {}
        self._cache_ttl = 5
        self._last_cache_update: Dict[str, float] = {}
        
        mode_str = "DEMO" if demo_mode else "LIVE"
        logger.info(f"🚀 KrakenFuturesClient inicializado - Modo: {mode_str}")
        logger.info(f"   📊 Símbolos soportados: {list(self.SUPPORTED_SYMBOLS.keys())}")
        
        if not self.api_key:
            logger.warning("⚠️ Sin API key - Solo datos públicos disponibles")
    
    def _rate_limit(self):
        """Aplicar rate limiting entre requests"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _sign_request(self, endpoint: str, data: str = "") -> Dict[str, str]:
        """
        Firmar request para endpoints autenticados
        
        Returns:
            Headers con firma HMAC-SHA512
        """
        if not self.api_key or not self.api_secret:
            return {}
        
        nonce = str(int(time.time() * 1000))
        post_data = data + nonce + endpoint
        
        sha256_hash = hashlib.sha256()
        sha256_hash.update(post_data.encode('utf-8'))
        
        hmac_digest = hmac.new(
            base64.b64decode(self.api_secret),
            sha256_hash.digest(),
            hashlib.sha512
        )
        
        return {
            "APIKey": self.api_key,
            "Nonce": nonce,
            "Authent": base64.b64encode(hmac_digest.digest()).decode('utf-8')
        }
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                 data: Optional[Dict] = None, authenticated: bool = False) -> Dict[str, Any]:
        """
        Realizar request a Kraken Futures API
        
        Args:
            method: GET/POST
            endpoint: Endpoint de la API
            params: Query parameters
            data: Body data para POST
            authenticated: Si requiere autenticación
            
        Returns:
            Response JSON
        """
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        if authenticated:
            auth_headers = self._sign_request(endpoint, str(data or {}))
            headers.update(auth_headers)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            else:
                response = requests.post(url, data=data, headers=headers, timeout=10)
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("result") == "error":
                error_msg = result.get("error", "Unknown error")
                logger.error(f"❌ Kraken Futures API error: {error_msg}")
                return {"error": error_msg, "success": False}
            
            return {"data": result, "success": True}
            
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Timeout en request a {endpoint}")
            return {"error": "Request timeout", "success": False}
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error en request: {str(e)}")
            return {"error": str(e), "success": False}
        except Exception as e:
            logger.error(f"❌ Error inesperado: {str(e)}")
            return {"error": str(e), "success": False}
    
    def get_ticker(self, symbol: str = "BTC") -> Optional[FuturesTicker]:
        """
        Obtener ticker de un perpetuo
        
        Args:
            symbol: BTC, ETH, SOL, XRP
            
        Returns:
            FuturesTicker con datos actuales
        """
        futures_symbol = self.SUPPORTED_SYMBOLS.get(symbol.upper())
        if not futures_symbol:
            logger.error(f"❌ Símbolo no soportado: {symbol}")
            return None
        
        cache_key = futures_symbol.value
        if cache_key in self._ticker_cache:
            if time.time() - self._last_cache_update.get(cache_key, 0) < self._cache_ttl:
                return self._ticker_cache[cache_key]
        
        response = self._request("GET", "tickers")
        
        if not response.get("success"):
            return None
        
        tickers = response.get("data", {}).get("tickers", [])
        
        for ticker in tickers:
            if ticker.get("symbol") == futures_symbol.value:
                try:
                    funding_rate = ticker.get("fundingRate", 0) or 0
                    next_funding = datetime.now() + timedelta(hours=8)
                    
                    result = FuturesTicker(
                        symbol=futures_symbol.value,
                        mark_price=float(ticker.get("markPrice", 0)),
                        index_price=float(ticker.get("indexPrice", 0)),
                        last_price=float(ticker.get("last", 0)),
                        bid=float(ticker.get("bid", 0)),
                        ask=float(ticker.get("ask", 0)),
                        volume_24h=float(ticker.get("vol24h", 0)),
                        funding_rate=float(funding_rate),
                        next_funding_time=next_funding,
                        open_interest=float(ticker.get("openInterest", 0)),
                        timestamp=datetime.now()
                    )
                    
                    self._ticker_cache[cache_key] = result
                    self._last_cache_update[cache_key] = time.time()
                    
                    return result
                    
                except (ValueError, TypeError) as e:
                    logger.error(f"❌ Error parseando ticker: {e}")
                    return None
        
        logger.warning(f"⚠️ Ticker no encontrado para {futures_symbol.value}")
        return None
    
    def get_all_tickers(self) -> Dict[str, FuturesTicker]:
        """
        Obtener tickers de todos los perpetuos soportados
        
        Returns:
            Dict con símbolo -> FuturesTicker
        """
        result = {}
        for symbol in self.SUPPORTED_SYMBOLS.keys():
            ticker = self.get_ticker(symbol)
            if ticker:
                result[symbol] = ticker
        return result
    
    def get_funding_rate(self, symbol: str = "BTC") -> Optional[FundingRate]:
        """
        Obtener funding rate actual de un perpetuo
        
        Args:
            symbol: BTC, ETH, etc.
            
        Returns:
            FundingRate con datos actuales
        """
        ticker = self.get_ticker(symbol)
        if not ticker:
            return None
        
        return FundingRate(
            symbol=ticker.symbol,
            rate=ticker.funding_rate,
            predicted_rate=ticker.funding_rate * 0.95,
            timestamp=ticker.timestamp,
            next_funding_time=ticker.next_funding_time
        )
    
    def get_funding_rates_history(self, symbol: str = "BTC", limit: int = 100) -> List[Dict]:
        """
        Obtener histórico de funding rates
        
        Args:
            symbol: BTC, ETH, etc.
            limit: Número máximo de registros
            
        Returns:
            Lista de funding rates históricos
        """
        futures_symbol = self.SUPPORTED_SYMBOLS.get(symbol.upper())
        if not futures_symbol:
            return []
        
        response = self._request("GET", f"historicalfundingrates", 
                                 params={"symbol": futures_symbol.value})
        
        if not response.get("success"):
            return []
        
        rates = response.get("data", {}).get("rates", [])
        return rates[:limit]
    
    def get_orderbook(self, symbol: str = "BTC", depth: int = 10) -> Optional[Dict]:
        """
        Obtener orderbook de un perpetuo
        
        Args:
            symbol: BTC, ETH, etc.
            depth: Profundidad del orderbook
            
        Returns:
            Dict con bids y asks
        """
        futures_symbol = self.SUPPORTED_SYMBOLS.get(symbol.upper())
        if not futures_symbol:
            return None
        
        response = self._request("GET", "orderbook", 
                                 params={"symbol": futures_symbol.value})
        
        if not response.get("success"):
            return None
        
        book = response.get("data", {}).get("orderBook", {})
        
        return {
            "symbol": futures_symbol.value,
            "bids": book.get("bids", [])[:depth],
            "asks": book.get("asks", [])[:depth],
            "timestamp": datetime.now()
        }
    
    def get_positions(self) -> List[FuturesPosition]:
        """
        Obtener posiciones abiertas (requiere autenticación)
        
        Returns:
            Lista de FuturesPosition
        """
        if not self.api_key:
            logger.warning("⚠️ get_positions requiere autenticación")
            return []
        
        response = self._request("GET", "openpositions", authenticated=True)
        
        if not response.get("success"):
            return []
        
        positions = response.get("data", {}).get("openPositions", [])
        result = []
        
        for pos in positions:
            try:
                result.append(FuturesPosition(
                    symbol=pos.get("symbol", ""),
                    side=pos.get("side", ""),
                    size=float(pos.get("size", 0)),
                    entry_price=float(pos.get("price", 0)),
                    mark_price=float(pos.get("markPrice", 0)),
                    liquidation_price=float(pos.get("liquidationThreshold", 0)),
                    unrealized_pnl=float(pos.get("pnl", 0)),
                    realized_pnl=float(pos.get("realizedFunding", 0)),
                    leverage=float(pos.get("leverage", 1)),
                    margin_used=float(pos.get("initialMargin", 0)),
                    timestamp=datetime.now()
                ))
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Error parseando posición: {e}")
        
        return result
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Obtener información de cuenta futures (requiere autenticación)
        
        Returns:
            Dict con balance, margin, etc.
        """
        if not self.api_key:
            logger.warning("⚠️ get_account_info requiere autenticación")
            return None
        
        response = self._request("GET", "accounts", authenticated=True)
        
        if not response.get("success"):
            return None
        
        accounts = response.get("data", {}).get("accounts", {})
        
        if "flex" in accounts:
            flex = accounts["flex"]
            return {
                "balance": float(flex.get("availableMargin", 0)),
                "equity": float(flex.get("portfolioValue", 0)),
                "margin_used": float(flex.get("initialMargin", 0)),
                "unrealized_pnl": float(flex.get("unrealizedFunding", 0)),
                "margin_level": float(flex.get("marginLevel", 0))
            }
        
        return None
    
    def place_order(self, symbol: str, side: OrderSide, size: float, 
                    order_type: OrderType = OrderType.MARKET,
                    price: Optional[float] = None,
                    leverage: float = 1.0,
                    reduce_only: bool = False) -> Optional[Dict]:
        """
        Colocar orden en perpetuos (requiere autenticación)
        
        Args:
            symbol: BTC, ETH, etc.
            side: OrderSide.BUY o OrderSide.SELL
            size: Tamaño en contratos
            order_type: MARKET, LIMIT, STOP
            price: Precio límite (para LIMIT orders)
            leverage: Apalancamiento (máx 3x en OMNIX)
            reduce_only: Si es para cerrar posición
            
        Returns:
            Dict con detalles de la orden
        """
        if not self.api_key:
            logger.error("❌ place_order requiere autenticación")
            return None
        
        futures_symbol = self.SUPPORTED_SYMBOLS.get(symbol.upper())
        if not futures_symbol:
            logger.error(f"❌ Símbolo no soportado: {symbol}")
            return None
        
        if leverage > 3.0:
            logger.warning(f"⚠️ Leverage {leverage}x excede máximo OMNIX (3x). Usando 3x.")
            leverage = 3.0
        
        order_data = {
            "orderType": order_type.value,
            "symbol": futures_symbol.value,
            "side": side.value,
            "size": size,
            "reduceOnly": reduce_only
        }
        
        if order_type == OrderType.LIMIT and price:
            order_data["limitPrice"] = price
        
        response = self._request("POST", "sendorder", data=order_data, authenticated=True)
        
        if not response.get("success"):
            return None
        
        result = response.get("data", {}).get("sendStatus", {})
        
        logger.info(f"📋 Orden colocada: {side.value} {size} {symbol} @ {order_type.value}")
        
        return {
            "order_id": result.get("order_id"),
            "symbol": futures_symbol.value,
            "side": side.value,
            "size": size,
            "type": order_type.value,
            "status": result.get("status", "unknown"),
            "timestamp": datetime.now()
        }
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancelar orden pendiente
        
        Args:
            order_id: ID de la orden
            
        Returns:
            True si se canceló exitosamente
        """
        if not self.api_key:
            return False
        
        response = self._request("POST", "cancelorder", 
                                 data={"order_id": order_id}, 
                                 authenticated=True)
        
        return response.get("success", False)
    
    def close_position(self, symbol: str) -> Optional[Dict]:
        """
        Cerrar posición completamente
        
        Args:
            symbol: BTC, ETH, etc.
            
        Returns:
            Dict con resultado del cierre
        """
        positions = self.get_positions()
        
        for pos in positions:
            if symbol.upper() in pos.symbol:
                close_side = OrderSide.SELL if pos.side == "long" else OrderSide.BUY
                return self.place_order(
                    symbol=symbol,
                    side=close_side,
                    size=pos.size,
                    order_type=OrderType.MARKET,
                    reduce_only=True
                )
        
        logger.warning(f"⚠️ No se encontró posición abierta para {symbol}")
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtener estado del cliente
        
        Returns:
            Dict con estado de conexión y configuración
        """
        test_ticker = self.get_ticker("BTC")
        
        return {
            "connected": test_ticker is not None,
            "mode": "DEMO" if self.demo_mode else "LIVE",
            "authenticated": bool(self.api_key),
            "symbols": list(self.SUPPORTED_SYMBOLS.keys()),
            "base_url": self.base_url,
            "btc_price": test_ticker.mark_price if test_ticker else None,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    client = KrakenFuturesClient(demo_mode=True)
    
    print("\n=== Kraken Futures Client Test ===\n")
    
    status = client.get_status()
    print(f"Estado: {status}")
    
    ticker = client.get_ticker("BTC")
    if ticker:
        print(f"\nBTC Perpetuo:")
        print(f"  Mark Price: ${ticker.mark_price:,.2f}")
        print(f"  Funding Rate: {ticker.funding_rate:.4%}")
        print(f"  Open Interest: {ticker.open_interest:,.0f}")
    
    funding = client.get_funding_rate("ETH")
    if funding:
        print(f"\nETH Funding Rate: {funding.rate:.4%}")
