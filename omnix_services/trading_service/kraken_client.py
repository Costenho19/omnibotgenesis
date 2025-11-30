"""
OMNIX V5.1 ENTERPRISE - Kraken API Client
Cliente profesional para integración con Kraken Exchange
Escalabilidad: 100K+ usuarios con rate limiting
"""

import hmac
import hashlib
import base64
import time
import urllib.parse
import requests
import threading
from typing import Dict, Any, Optional, List
from omnix_config.settings import settings
from omnix_core.utils.logger import get_logger
from omnix_core.cache.redis_cache import cache_result

logger = get_logger(__name__)


class KrakenAPIClient:
    """
    Enterprise-grade Kraken API client
    
    Features:
    - Automatic rate limiting
    - Connection pooling
    - Error handling and retries
    - Signature generation for authenticated requests
    - Thread-safe nonce generation (prevents "Invalid nonce" errors)
    """
    
    def __init__(self):
        self.api_url = "https://api.kraken.com"
        self.api_key = settings.trading.kraken_key
        self.api_secret = settings.trading.kraken_secret
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OMNIX-V5.1-Enterprise'
        })
        
        # Thread-safe nonce counter (prevents concurrent request collisions)
        self._nonce_lock = threading.Lock()
        self._nonce_counter = 0
        self._last_nonce_time = 0
        
        logger.info("🏦 Kraken API Client initialized")
    
    def _generate_signature(self, urlpath: str, data: Dict, nonce: str) -> str:
        """Generate API-Sign header for authenticated requests"""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(nonce) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        
        mac = hmac.new(
            base64.b64decode(self.api_secret),
            message,
            hashlib.sha512
        )
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()
    
    def _request(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        authenticated: bool = False,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Execute API request with retries and error handling
        
        Args:
            endpoint: API endpoint path
            data: Request payload
            authenticated: Whether to use authentication
            max_retries: Maximum retry attempts
            
        Returns:
            API response dictionary
        """
        url = f"{self.api_url}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                if authenticated:
                    if not self.api_key or not self.api_secret:
                        raise ValueError("Kraken API credentials not configured")
                    
                    # Thread-safe monotonic nonce generation
                    with self._nonce_lock:
                        current_time_ms = int(time.time() * 1000)
                        
                        # Ensure nonce is strictly increasing (never reuse)
                        # Use max to handle concurrent requests in same millisecond
                        nonce = max(current_time_ms, self._last_nonce_time + 1)
                        self._last_nonce_time = nonce
                    
                    data = data or {}
                    data['nonce'] = str(nonce)
                    
                    headers = {
                        'API-Key': self.api_key,
                        'API-Sign': self._generate_signature(endpoint, data, nonce)
                    }
                    
                    response = self.session.post(url, data=data, headers=headers, timeout=15)
                else:
                    response = self.session.get(url, params=data, timeout=15)
                
                response.raise_for_status()
                result = response.json()
                
                # Check for API errors
                if result.get('error'):
                    error_msg = ', '.join(result['error'])
                    logger.error(f"Kraken API error: {error_msg}")
                    raise Exception(f"Kraken API error: {error_msg}")
                
                return result.get('result', {})
                
            except Exception as e:
                logger.warning(f"Kraken request attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        return {}
    
    @cache_result(ttl=60, key_prefix="kraken_balance")
    def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            result = self._request('/0/private/Balance', authenticated=True)
            logger.info(f"✅ Balance retrieved: {len(result)} assets")
            return result
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {}
    
    @cache_result(ttl=10, key_prefix="kraken_price")
    def get_ticker(self, pair: str) -> Dict[str, Any]:
        """
        Get ticker information for trading pair
        
        Args:
            pair: Trading pair (e.g., 'XBTUSD' for BTC/USD)
        """
        try:
            result = self._request('/0/public/Ticker', data={'pair': pair})
            return result.get(pair, {}) if result else {}
        except Exception as e:
            logger.error(f"Failed to get ticker for {pair}: {e}")
            return {}
    
    @cache_result(ttl=300, key_prefix="kraken_ohlc")
    def get_ohlc(self, pair: str, interval: int = 60, since: Optional[int] = None) -> List[List]:
        """
        Get OHLC (candlestick) data for historical analysis
        
        Args:
            pair: Trading pair (e.g., 'XBTUSD', 'ETHUSD')
            interval: Time frame in minutes (1, 5, 15, 30, 60, 240, 1440, 10080, 21600)
            since: Return data since given timestamp
            
        Returns:
            List of OHLC data: [time, open, high, low, close, vwap, volume, count]
        """
        try:
            data = {'pair': pair, 'interval': interval}
            if since:
                data['since'] = since
            
            result = self._request('/0/public/OHLC', data=data)
            
            if result:
                for key in result:
                    if key != 'last' and isinstance(result[key], list):
                        ohlc_data = result[key]
                        logger.info(f"✅ OHLC data retrieved for {pair} (key={key}): {len(ohlc_data)} candles")
                        return ohlc_data
            
            logger.warning(f"⚠️ No OHLC data found for {pair}")
            return []
        except Exception as e:
            logger.error(f"Failed to get OHLC for {pair}: {e}")
            return []
    
    def get_order_book(self, pair: str, count: int = 10) -> Dict[str, Any]:
        """Get order book for analysis"""
        try:
            result = self._request('/0/public/Depth', data={'pair': pair, 'count': count})
            return result.get(pair, {}) if result else {}
        except Exception as e:
            logger.error(f"Failed to get order book for {pair}: {e}")
            return {}
    
    def place_order(
        self,
        pair: str,
        order_type: str,
        side: str,
        volume: float,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place trading order
        
        Args:
            pair: Trading pair
            order_type: 'market' or 'limit'
            side: 'buy' or 'sell'
            volume: Order volume
            price: Limit price (required for limit orders)
        """
        try:
            data = {
                'pair': pair,
                'type': side,
                'ordertype': order_type,
                'volume': str(volume)
            }
            
            if order_type == 'limit' and price:
                data['price'] = str(price)
            
            result = self._request('/0/private/AddOrder', data=data, authenticated=True)
            
            if result:
                logger.info(f"✅ Order placed: {side} {volume} {pair} at {price if price else 'market'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return {}
    
    def get_open_orders(self) -> Dict[str, Any]:
        """Get list of open orders"""
        try:
            return self._request('/0/private/OpenOrders', authenticated=True)
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return {}
    
    def cancel_order(self, txid: str) -> bool:
        """Cancel specific order"""
        try:
            result = self._request('/0/private/CancelOrder', data={'txid': txid}, authenticated=True)
            logger.info(f"✅ Order {txid} cancelled")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {txid}: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if Kraken API is accessible"""
        try:
            result = self._request('/0/public/Time')
            return 'unixtime' in result
        except Exception as e:
            logger.error(f"Kraken health check failed: {e}")
            return False
