"""
🏦 Alpaca Markets API Service
Stock trading execution and portfolio management
"""

import os
import logging
from typing import Dict, List, Optional
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
        
        self.connected = False
        if self.api_key and self.api_secret:
            self.connected = self._test_connection()
            if self.connected:
                mode = "PAPER" if paper_trading else "LIVE"
                logger.info(f"✅ Alpaca API conectada - Modo {mode}")
    
    def _test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = requests.get(
                f'{self.base_url}/v2/account',
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
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
            response = requests.get(
                f'{self.base_url}/v2/account',
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
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
            response = requests.get(
                f'{self.base_url}/v2/positions',
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
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
            response = requests.get(
                f'{self.data_url}/v2/stocks/{symbol}/trades/latest',
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
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
                order_data['qty'] = qty
            elif notional:
                order_data['notional'] = notional
            else:
                raise ValueError("Must specify qty or notional")
            
            if limit_price:
                order_data['limit_price'] = limit_price
            if stop_price:
                order_data['stop_price'] = stop_price
            
            response = requests.post(
                f'{self.base_url}/v2/orders',
                headers=self.headers,
                json=order_data,
                timeout=10
            )
            
            if response.status_code == 200:
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
            else:
                logger.error(f"❌ Order failed: {response.text}")
        except Exception as e:
            logger.error(f"Error creating order: {e}")
        
        return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order"""
        if not self.connected:
            return False
        
        try:
            response = requests.delete(
                f'{self.base_url}/v2/orders/{order_id}',
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
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
            response = requests.get(
                f'{self.base_url}/v2/orders',
                headers=self.headers,
                params={'status': status},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
        
        return []
    
    def close_position(self, symbol: str) -> bool:
        """Close entire position in a stock"""
        if not self.connected:
            return False
        
        try:
            response = requests.delete(
                f'{self.base_url}/v2/positions/{symbol}',
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error closing position {symbol}: {e}")
            return False
