"""
OMNIX V7.0 Kraken Infrastructure Adapter

Implements TradingPort and MarketDataPort protocols by wrapping
the legacy KrakenAPIClient. Provides retry logic, telemetry,
health checks, and structured error handling.

Phase 3: Interfaces Migration
"""

import asyncio
import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class KrakenAdapter:
    """
    Infrastructure adapter for Kraken exchange.
    
    Implements:
    - TradingPort: execute_order, get_ticker, get_balance, get_open_positions, cancel_order, is_connected
    - MarketDataPort: get_ohlcv, get_orderbook, get_recent_trades, get_fear_greed_index
    
    Wraps legacy KrakenAPIClient with:
    - Async interface (asyncio.to_thread for sync operations)
    - Retry policies with exponential backoff
    - Telemetry and structured logging
    - Health check endpoint
    - Graceful fallback on connection issues
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        max_retries: int = 3,
        timeout: float = 15.0
    ):
        """
        Initialize Kraken adapter.
        
        Args:
            api_key: Kraken API key (uses settings if None)
            api_secret: Kraken API secret (uses settings if None)
            max_retries: Maximum retry attempts for failed requests
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self._api_secret = api_secret
        self._max_retries = max_retries
        self._timeout = timeout
        self._client: Optional[Any] = None
        self._connected = False
        self._last_health_check: Optional[datetime] = None
        self._request_count = 0
        self._error_count = 0
        
    def _get_client(self):
        """Lazy initialization of legacy Kraken client."""
        if self._client is None:
            try:
                from omnix_services.trading_service.kraken_client import KrakenAPIClient
                self._client = KrakenAPIClient()
                self._connected = True
                logger.info("KrakenAdapter: Legacy client initialized")
            except Exception as e:
                logger.error(f"KrakenAdapter: Failed to initialize legacy client: {e}")
                self._connected = False
                raise
        return self._client
    
    def _with_retry(self, operation: Callable[[], T], operation_name: str) -> T:
        """
        Execute SYNC operation with exponential backoff retry.
        
        Args:
            operation: Callable to execute
            operation_name: Name for logging
            
        Returns:
            Operation result
            
        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(1, self._max_retries + 1):
            try:
                return operation()
            except Exception as e:
                last_exception = e
                self._error_count += 1
                
                if attempt < self._max_retries:
                    backoff = min(2 ** attempt * 0.5, 10.0)
                    logger.warning(
                        f"KrakenAdapter.{operation_name} attempt {attempt}/{self._max_retries} "
                        f"failed: {e}. Retrying in {backoff:.1f}s"
                    )
                    time.sleep(backoff)
                else:
                    logger.error(
                        f"KrakenAdapter.{operation_name} failed after {self._max_retries} attempts: {e}"
                    )
        
        raise last_exception  # type: ignore
    
    async def _async_with_retry(self, operation: Callable[[], T], operation_name: str) -> T:
        """
        Execute ASYNC operation with exponential backoff retry using asyncio.sleep.
        
        Args:
            operation: Sync callable to execute in thread
            operation_name: Name for logging
            
        Returns:
            Operation result
            
        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(1, self._max_retries + 1):
            try:
                return await asyncio.to_thread(operation)
            except Exception as e:
                last_exception = e
                self._error_count += 1
                
                if attempt < self._max_retries:
                    backoff = min(2 ** attempt * 0.5, 10.0)
                    logger.warning(
                        f"KrakenAdapter.{operation_name} attempt {attempt}/{self._max_retries} "
                        f"failed: {e}. Retrying in {backoff:.1f}s"
                    )
                    await asyncio.sleep(backoff)
                else:
                    logger.error(
                        f"KrakenAdapter.{operation_name} failed after {self._max_retries} attempts: {e}"
                    )
        
        raise last_exception  # type: ignore
    
    def execute_order(
        self,
        symbol: str,
        side: str,
        amount: Decimal,
        order_type: str = 'market'
    ) -> Dict[str, Any]:
        """
        Execute a trade order (TradingPort).
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            side: 'buy' or 'sell'
            amount: Order quantity
            order_type: 'market' or 'limit'
            
        Returns:
            Order result dictionary
        """
        self._request_count += 1
        
        def _execute():
            client = self._get_client()
            kraken_pair = self._to_kraken_pair(symbol)
            kraken_side = side.lower()
            
            result = client.add_order(
                pair=kraken_pair,
                type=kraken_side,
                ordertype=order_type,
                volume=str(amount)
            )
            
            return {
                "order_id": result.get("txid", ["unknown"])[0] if result.get("txid") else "unknown",
                "status": "executed",
                "filled_amount": amount,
                "price": Decimal(str(result.get("price", 0))),
                "timestamp": datetime.utcnow(),
                "raw": result
            }
        
        return self._with_retry(_execute, "execute_order")
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price for symbol (TradingPort).
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            
        Returns:
            Ticker data dictionary
        """
        self._request_count += 1
        
        def _get():
            client = self._get_client()
            kraken_pair = self._to_kraken_pair(symbol)
            
            result = client.get_ticker(kraken_pair)
            
            if result:
                ticker_key = list(result.keys())[0] if result else None
                ticker_data = result.get(ticker_key, {}) if ticker_key else {}
                
                return {
                    "bid": Decimal(str(ticker_data.get("b", [0])[0])) if ticker_data.get("b") else Decimal(0),
                    "ask": Decimal(str(ticker_data.get("a", [0])[0])) if ticker_data.get("a") else Decimal(0),
                    "last": Decimal(str(ticker_data.get("c", [0])[0])) if ticker_data.get("c") else Decimal(0),
                    "volume": Decimal(str(ticker_data.get("v", [0, 0])[1])) if ticker_data.get("v") else Decimal(0),
                    "timestamp": datetime.utcnow()
                }
            return {
                "bid": Decimal(0),
                "ask": Decimal(0),
                "last": Decimal(0),
                "volume": Decimal(0),
                "timestamp": datetime.utcnow()
            }
        
        return self._with_retry(_get, "get_ticker")
    
    def get_balance(self) -> Dict[str, Decimal]:
        """
        Get account balances (TradingPort).
        
        Returns:
            Dictionary mapping currency to balance
        """
        self._request_count += 1
        
        def _get():
            client = self._get_client()
            result = client.get_balance()
            
            return {
                currency: Decimal(str(amount))
                for currency, amount in result.items()
            }
        
        return self._with_retry(_get, "get_balance")
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions (TradingPort).
        
        Returns:
            List of position dictionaries
        """
        self._request_count += 1
        
        def _get():
            client = self._get_client()
            result = client.get_open_positions()
            
            positions = []
            for pos_id, pos_data in result.items():
                positions.append({
                    "id": pos_id,
                    "symbol": pos_data.get("pair", ""),
                    "side": pos_data.get("type", ""),
                    "amount": Decimal(str(pos_data.get("vol", 0))),
                    "entry_price": Decimal(str(pos_data.get("cost", 0))),
                    "unrealized_pnl": Decimal(str(pos_data.get("net", 0)))
                })
            return positions
        
        try:
            return self._with_retry(_get, "get_open_positions")
        except Exception:
            return []
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order (TradingPort).
        
        Args:
            order_id: The order ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        self._request_count += 1
        
        def _cancel():
            client = self._get_client()
            result = client.cancel_order(order_id)
            return bool(result.get("count", 0) > 0)
        
        try:
            return self._with_retry(_cancel, "cancel_order")
        except Exception:
            return False
    
    def is_connected(self) -> bool:
        """
        Check if exchange connection is active (TradingPort).
        
        Returns:
            True if connected and authenticated
        """
        try:
            client = self._get_client()
            client.get_server_time()
            self._connected = True
            self._last_health_check = datetime.utcnow()
            return True
        except Exception:
            self._connected = False
            return False
    
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get OHLCV candles (MarketDataPort).
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            timeframe: Candle interval ('1m', '5m', '1h', '1d')
            limit: Number of candles
            
        Returns:
            List of OHLCV dictionaries
        """
        self._request_count += 1
        
        try:
            result = await self._async_with_retry(
                lambda: self._get_client().get_ohlc(
                    self._to_kraken_pair(symbol),
                    interval=self._timeframe_to_minutes(timeframe)
                ),
                "get_ohlcv"
            )
            
            candles = []
            if result:
                data_key = [k for k in result.keys() if k != 'last'][0] if len(result) > 1 else list(result.keys())[0]
                raw_candles = result.get(data_key, [])[:limit]
                
                for candle in raw_candles:
                    if len(candle) >= 6:
                        candles.append({
                            "timestamp": datetime.fromtimestamp(candle[0]),
                            "open": float(candle[1]),
                            "high": float(candle[2]),
                            "low": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": float(candle[6]) if len(candle) > 6 else 0.0
                        })
            return candles
        except Exception as e:
            logger.error(f"KrakenAdapter.get_ohlcv exhausted retries: {e}")
            return []
    
    async def get_orderbook(
        self,
        symbol: str,
        depth: int = 20
    ) -> Dict[str, Any]:
        """
        Get order book (MarketDataPort).
        
        Args:
            symbol: Trading pair
            depth: Number of levels each side
            
        Returns:
            Order book dictionary
        """
        self._request_count += 1
        
        try:
            result = await self._async_with_retry(
                lambda: self._get_client().get_orderbook(self._to_kraken_pair(symbol), count=depth),
                "get_orderbook"
            )
            
            if result:
                data_key = list(result.keys())[0]
                book = result.get(data_key, {})
                return {
                    "bids": [[float(p), float(a)] for p, a, _ in book.get("bids", [])[:depth]],
                    "asks": [[float(p), float(a)] for p, a, _ in book.get("asks", [])[:depth]],
                    "timestamp": datetime.utcnow()
                }
            return {"bids": [], "asks": [], "timestamp": datetime.utcnow()}
        except Exception as e:
            logger.error(f"KrakenAdapter.get_orderbook exhausted retries: {e}")
            return {"bids": [], "asks": [], "timestamp": datetime.utcnow()}
    
    async def get_recent_trades(
        self,
        symbol: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent trades (MarketDataPort).
        
        Args:
            symbol: Trading pair
            limit: Number of trades
            
        Returns:
            List of trade dictionaries
        """
        self._request_count += 1
        
        try:
            result = await self._async_with_retry(
                lambda: self._get_client().get_recent_trades(self._to_kraken_pair(symbol)),
                "get_recent_trades"
            )
            
            trades = []
            if result:
                data_key = [k for k in result.keys() if k != 'last'][0] if len(result) > 1 else list(result.keys())[0]
                raw_trades = result.get(data_key, [])[:limit]
                
                for trade in raw_trades:
                    if len(trade) >= 4:
                        trades.append({
                            "price": float(trade[0]),
                            "amount": float(trade[1]),
                            "timestamp": datetime.fromtimestamp(trade[2]),
                            "side": "buy" if trade[3] == "b" else "sell"
                        })
            return trades
        except Exception as e:
            logger.error(f"KrakenAdapter.get_recent_trades exhausted retries: {e}")
            return []
    
    async def get_fear_greed_index(self) -> Dict[str, Any]:
        """
        Get Fear & Greed Index (MarketDataPort).
        
        Note: Kraken doesn't provide this directly, delegates to market intelligence service.
        
        Returns:
            Fear & Greed data dictionary
        """
        try:
            def _fetch():
                from omnix_services.market_intelligence.fear_greed_service import FearGreedService
                service = FearGreedService()
                return service.get_current_index()
            
            result = await asyncio.to_thread(_fetch)
            
            if result:
                return {
                    "value": result.get("value", 50),
                    "classification": result.get("classification", "Neutral"),
                    "timestamp": datetime.utcnow()
                }
            return {
                "value": 50,
                "classification": "Neutral",
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.warning(f"KrakenAdapter.get_fear_greed_index fallback: {e}")
            return {
                "value": 50,
                "classification": "Neutral",
                "timestamp": datetime.utcnow()
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Health check for monitoring.
        
        Returns:
            Health status dictionary
        """
        connected = self.is_connected()
        return {
            "adapter": "KrakenAdapter",
            "connected": connected,
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1)
        }
    
    def _to_kraken_pair(self, symbol: str) -> str:
        """Convert standard symbol to Kraken format."""
        return symbol.replace("/", "")
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes."""
        mappings = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "4h": 240, "1d": 1440, "1w": 10080
        }
        return mappings.get(timeframe, 60)
