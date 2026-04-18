"""
🏦 Alpaca Markets API Service
Stock trading execution and portfolio management
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class AlpacaService:
    """
    Enterprise-grade Alpaca Markets integration
    Supports both paper and live trading
    """
    
    def __init__(self, paper_trading: bool = True):
        self.paper_trading = paper_trading
        self.api_key = os.getenv('ALPACA_API_KEY', '')
        self.api_secret = os.getenv('ALPACA_API_SECRET', '')
        
        if paper_trading:
            self.base_url = 'https://paper-api.alpaca.markets'
            self.data_url = 'https://data.alpaca.markets'
        else:
            self.base_url = 'https://api.alpaca.markets'
            self.data_url = 'https://data.alpaca.markets'
        
        self.headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        self.connected = False
        if self.api_key and self.api_secret:
            self.connected = self._test_connection()
            if self.connected:
                mode = "PAPER" if paper_trading else "LIVE"
                logger.info(f"✅ Alpaca API conectada - Modo {mode}")
    
    def _request(
        self,
        method: str,
        url: str,
        max_retries: int = 3,
        timeout: int = 15,
        **kwargs
    ) -> Optional[requests.Response]:
        """Execute request with retries and exponential backoff"""
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, timeout=timeout, **kwargs)
                if response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                return response
            except requests.exceptions.Timeout:
                logger.warning(f"Alpaca timeout (attempt {attempt + 1}/{max_retries})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Alpaca connection error (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.error(f"Alpaca request error: {e}")
                break
            
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
        
        return None
    
    def _test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = self._request('GET', f'{self.base_url}/v2/account')
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Error connecting to Alpaca: {e}")
            return False
    
    def fetch_balance(self) -> Optional[Dict]:
        """
        Get account balance and buying power
        Returns: {
            'cash': float,
            'buying_power': float,
            'portfolio_value': float,
            'equity': float
        }
        """
        if not self.connected:
            return None
        
        try:
            response = self._request('GET', f'{self.base_url}/v2/account')
            
            if response and response.status_code == 200:
                data = response.json()
                return {
                    'cash': float(data.get('cash', 0)),
                    'buying_power': float(data.get('buying_power', 0)),
                    'portfolio_value': float(data.get('portfolio_value', 0)),
                    'equity': float(data.get('equity', 0))
                }
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
        
        return None
    
    def fetch_positions(self) -> List[Dict]:
        """
        Get current stock positions
        Returns list of positions with ticker, qty, market_value, etc.
        """
        if not self.connected:
            return []
        
        try:
            response = self._request('GET', f'{self.base_url}/v2/positions')
            
            if response and response.status_code == 200:
                positions = response.json()
                return [
                    {
                        'symbol': p['symbol'],
                        'qty': float(p['qty']),
                        'avg_entry_price': float(p['avg_entry_price']),
                        'current_price': float(p['current_price']),
                        'market_value': float(p['market_value']),
                        'unrealized_pl': float(p['unrealized_pl']),
                        'unrealized_plpc': float(p['unrealized_plpc'])
                    }
                    for p in positions
                ]
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
        
        return []
    
    def fetch_ticker_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a stock ticker"""
        if not self.connected:
            return None
        
        try:
            response = self._request('GET', f'{self.data_url}/v2/stocks/{symbol}/trades/latest')
            
            if response and response.status_code == 200:
                data = response.json()
                return float(data['trade']['p'])
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
        
        return None
    
    def create_order(
        self,
        symbol: str,
        qty: Optional[float] = None,
        notional: Optional[float] = None,
        side: str = 'buy',
        order_type: str = 'market',
        time_in_force: str = 'day',
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Create stock order
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            qty: Number of shares (or use notional for dollar amount)
            notional: Dollar amount to invest (fractional shares)
            side: 'buy' or 'sell'
            order_type: 'market', 'limit', 'stop', 'stop_limit'
            time_in_force: 'day', 'gtc', 'ioc', 'fok'
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders
        """
        if not self.connected:
            logger.error("Cannot create order - not connected to Alpaca")
            return None
        
        try:
            order_data = {
                'symbol': symbol.upper(),
                'side': side,
                'type': order_type,
                'time_in_force': time_in_force
            }
            
            if qty:
                order_data['qty'] = str(qty)
            elif notional:
                order_data['notional'] = str(notional)
            else:
                raise ValueError("Must specify qty or notional")
            
            if limit_price:
                order_data['limit_price'] = str(limit_price)
            if stop_price:
                order_data['stop_price'] = str(stop_price)
            
            response = self._request('POST', f'{self.base_url}/v2/orders', json=order_data)
            
            if response and response.status_code == 200:
                order = response.json()
                logger.info(f"✅ Order created: {side.upper()} {qty or notional} {symbol}")
                return {
                    'id': order['id'],
                    'symbol': order['symbol'],
                    'qty': order.get('qty'),
                    'notional': order.get('notional'),
                    'side': order['side'],
                    'type': order['type'],
                    'status': order['status'],
                    'filled_avg_price': order.get('filled_avg_price')
                }
            elif response:
                logger.error(f"❌ Order failed (status {response.status_code}): {response.text}")
            else:
                logger.error(f"❌ Order failed: API request returned None after retries")
        except Exception as e:
            logger.error(f"Error creating order: {e}")
        
        return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order"""
        if not self.connected:
            return False
        
        try:
            response = self._request('DELETE', f'{self.base_url}/v2/orders/{order_id}')
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return False
    
    def get_orders(self, status: str = 'open') -> List[Dict]:
        """
        Get orders
        status: 'open', 'closed', 'all'
        """
        if not self.connected:
            return []
        
        try:
            response = self._request('GET', f'{self.base_url}/v2/orders', params={'status': status})
            
            if response and response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
        
        return []
    
    def close_position(self, symbol: str) -> bool:
        """Close entire position in a stock"""
        if not self.connected:
            return False
        
        try:
            response = self._request('DELETE', f'{self.base_url}/v2/positions/{symbol}')
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Error closing position {symbol}: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if Alpaca API is accessible"""
        try:
            response = self._request('GET', f'{self.base_url}/v2/clock')
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Alpaca health check failed: {e}")
            return False
