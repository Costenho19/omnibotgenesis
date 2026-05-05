"""
OMNIX Alpha Vantage Service
External technical indicators for confirmation
Requires ALPHA_VANTAGE_API_KEY environment variable
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class AlphaVantageService:
    """
    Alpha Vantage integration for external technical indicators.
    Provides second-opinion confirmation for OMNIX internal calculations.
    
    Free tier: 25 calls/day, 5 calls/minute
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self):
        self.api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        self._cache = {}
        self._cache_time = {}
        self._cache_duration = timedelta(minutes=15)
        
        if not self.api_key:
            logger.warning("ALPHA_VANTAGE_API_KEY not configured - Alpha Vantage features disabled")
    
    def is_available(self) -> bool:
        """Check if Alpha Vantage API is configured."""
        return self.api_key is not None
    
    def get_rsi(self, symbol: str, interval: str = 'daily', time_period: int = 14) -> Optional[Dict]:
        """
        Get Relative Strength Index (RSI) for a symbol.
        
        Args:
            symbol: Stock ticker (AAPL) or crypto (BTC)
            interval: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
            time_period: Number of data points for RSI calculation
            
        Returns:
            Dict with current RSI value and interpretation
        """
        if not self.api_key:
            return None
        
        cache_key = f"rsi_{symbol}_{interval}"
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        
        try:
            response = requests.get(
                self.BASE_URL,
                params={
                    'function': 'RSI',
                    'symbol': symbol,
                    'interval': interval,
                    'time_period': time_period,
                    'series_type': 'close',
                    'apikey': self.api_key
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            if 'Technical Analysis: RSI' in data:
                rsi_data = data['Technical Analysis: RSI']
                latest_date = list(rsi_data.keys())[0]
                rsi_value = float(rsi_data[latest_date]['RSI'])
                
                result = {
                    'symbol': symbol,
                    'indicator': 'RSI',
                    'value': round(rsi_value, 2),
                    'date': latest_date,
                    'interpretation': self._interpret_rsi(rsi_value),
                    'signal': self._get_rsi_signal(rsi_value)
                }
                
                self._cache[cache_key] = result
                self._cache_time[cache_key] = datetime.now()
                
                logger.info(f"RSI for {symbol}: {rsi_value:.2f} - {result['signal']}")
                return result
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                return self._cache.get(cache_key)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching RSI for {symbol}: {e}")
            return self._cache.get(cache_key)
    
    def get_macd(self, symbol: str, interval: str = 'daily') -> Optional[Dict]:
        """
        Get MACD (Moving Average Convergence Divergence) for a symbol.
        
        Returns:
            Dict with MACD, signal line, histogram, and interpretation
        """
        if not self.api_key:
            return None
        
        cache_key = f"macd_{symbol}_{interval}"
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        
        try:
            response = requests.get(
                self.BASE_URL,
                params={
                    'function': 'MACD',
                    'symbol': symbol,
                    'interval': interval,
                    'series_type': 'close',
                    'apikey': self.api_key
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            if 'Technical Analysis: MACD' in data:
                macd_data = data['Technical Analysis: MACD']
                latest_date = list(macd_data.keys())[0]
                latest = macd_data[latest_date]
                
                macd_value = float(latest['MACD'])
                signal_value = float(latest['MACD_Signal'])
                histogram = float(latest['MACD_Hist'])
                
                result = {
                    'symbol': symbol,
                    'indicator': 'MACD',
                    'macd': round(macd_value, 4),
                    'signal': round(signal_value, 4),
                    'histogram': round(histogram, 4),
                    'date': latest_date,
                    'interpretation': self._interpret_macd(macd_value, signal_value, histogram),
                    'trade_signal': self._get_macd_signal(macd_value, signal_value, histogram)
                }
                
                self._cache[cache_key] = result
                self._cache_time[cache_key] = datetime.now()
                
                logger.info(f"MACD for {symbol}: {result['trade_signal']}")
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching MACD for {symbol}: {e}")
            return self._cache.get(cache_key)
    
    def get_bollinger_bands(self, symbol: str, interval: str = 'daily', time_period: int = 20) -> Optional[Dict]:
        """
        Get Bollinger Bands for a symbol.
        
        Returns:
            Dict with upper, middle, lower bands and position interpretation
        """
        if not self.api_key:
            return None
        
        cache_key = f"bbands_{symbol}_{interval}"
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        
        try:
            response = requests.get(
                self.BASE_URL,
                params={
                    'function': 'BBANDS',
                    'symbol': symbol,
                    'interval': interval,
                    'time_period': time_period,
                    'series_type': 'close',
                    'nbdevup': 2,
                    'nbdevdn': 2,
                    'apikey': self.api_key
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            if 'Technical Analysis: BBANDS' in data:
                bbands_data = data['Technical Analysis: BBANDS']
                latest_date = list(bbands_data.keys())[0]
                latest = bbands_data[latest_date]
                
                upper = float(latest['Real Upper Band'])
                middle = float(latest['Real Middle Band'])
                lower = float(latest['Real Lower Band'])
                
                result = {
                    'symbol': symbol,
                    'indicator': 'BBANDS',
                    'upper': round(upper, 2),
                    'middle': round(middle, 2),
                    'lower': round(lower, 2),
                    'bandwidth': round((upper - lower) / middle * 100, 2),
                    'date': latest_date,
                    'interpretation': f"Band width: {((upper - lower) / middle * 100):.1f}%"
                }
                
                self._cache[cache_key] = result
                self._cache_time[cache_key] = datetime.now()
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Bollinger Bands for {symbol}: {e}")
            return self._cache.get(cache_key)
    
    def get_sma(self, symbol: str, interval: str = 'daily', time_period: int = 50) -> Optional[Dict]:
        """
        Get Simple Moving Average for a symbol.
        """
        if not self.api_key:
            return None
        
        cache_key = f"sma_{symbol}_{interval}_{time_period}"
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        
        try:
            response = requests.get(
                self.BASE_URL,
                params={
                    'function': 'SMA',
                    'symbol': symbol,
                    'interval': interval,
                    'time_period': time_period,
                    'series_type': 'close',
                    'apikey': self.api_key
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            if 'Technical Analysis: SMA' in data:
                sma_data = data['Technical Analysis: SMA']
                latest_date = list(sma_data.keys())[0]
                sma_value = float(sma_data[latest_date]['SMA'])
                
                result = {
                    'symbol': symbol,
                    'indicator': f'SMA{time_period}',
                    'value': round(sma_value, 2),
                    'date': latest_date
                }
                
                self._cache[cache_key] = result
                self._cache_time[cache_key] = datetime.now()
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching SMA for {symbol}: {e}")
            return self._cache.get(cache_key)
    
    def get_technical_summary(self, symbol: str) -> Dict:
        """
        Get a summary of multiple technical indicators for a symbol.
        Combines RSI, MACD, and provides overall recommendation.
        
        Returns:
            Dict with all indicators and combined signal
        """
        rsi = self.get_rsi(symbol)
        macd = self.get_macd(symbol)
        
        signals = []
        details = []
        
        if rsi:
            signals.append(rsi['signal'])
            details.append(f"RSI: {rsi['value']} ({rsi['interpretation']})")
        
        if macd:
            signals.append(macd['trade_signal'])
            details.append(f"MACD: {macd['interpretation']}")
        
        bullish_count = sum(1 for s in signals if s in ['BUY', 'STRONG_BUY'])
        bearish_count = sum(1 for s in signals if s in ['SELL', 'STRONG_SELL'])
        
        if bullish_count > bearish_count:
            overall = 'BULLISH'
        elif bearish_count > bullish_count:
            overall = 'BEARISH'
        else:
            overall = 'NEUTRAL'
        
        return {
            'symbol': symbol,
            'rsi': rsi,
            'macd': macd,
            'signals': signals,
            'details': details,
            'overall_signal': overall,
            'confidence': abs(bullish_count - bearish_count) / max(len(signals), 1),
            'timestamp': datetime.now().isoformat()
        }
    
    def _interpret_rsi(self, value: float) -> str:
        """Interpret RSI value."""
        if value >= 70:
            return "Sobrecomprado - Posible corrección"
        elif value >= 60:
            return "Zona alta - Momentum alcista"
        elif value >= 40:
            return "Zona neutral"
        elif value >= 30:
            return "Zona baja - Momentum bajista"
        else:
            return "Sobrevendido - Posible rebote"
    
    def _get_rsi_signal(self, value: float) -> str:
        """Get trading signal from RSI."""
        if value >= 80:
            return "STRONG_SELL"
        elif value >= 70:
            return "SELL"
        elif value >= 55:
            return "HOLD"
        elif value >= 45:
            return "NEUTRAL"
        elif value >= 30:
            return "BUY"
        else:
            return "STRONG_BUY"
    
    def _interpret_macd(self, macd: float, signal: float, histogram: float) -> str:
        """Interpret MACD values."""
        if macd > signal and histogram > 0:
            return "Tendencia alcista confirmada"
        elif macd > signal and histogram < 0:
            return "Posible cambio a alcista"
        elif macd < signal and histogram < 0:
            return "Tendencia bajista confirmada"
        else:
            return "Posible cambio a bajista"
    
    def _get_macd_signal(self, macd: float, signal: float, histogram: float) -> str:
        """Get trading signal from MACD."""
        if macd > signal:
            if histogram > 0 and histogram > abs(macd - signal):
                return "STRONG_BUY"
            return "BUY"
        elif macd < signal:
            if histogram < 0 and abs(histogram) > abs(macd - signal):
                return "STRONG_SELL"
            return "SELL"
        return "NEUTRAL"
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache_time:
            return False
        return datetime.now() - self._cache_time[key] < self._cache_duration
    
    def get_daily_prices(self, symbol: str, days: int = 30) -> List[Dict]:
        """
        Get daily closing prices for a symbol (stocks like SPY).
        Uses TIME_SERIES_DAILY endpoint.
        
        Args:
            symbol: Stock ticker (SPY, AAPL, etc.)
            days: Number of days of historical data (default 30, max 100)
            
        Returns:
            List of {date: str, price: float} sorted by date ascending
        """
        if not self.api_key:
            logger.warning("ALPHA_VANTAGE_API_KEY not configured")
            return []
        
        cache_key = f"daily_{symbol}_{days}"
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key, [])
        
        try:
            response = requests.get(
                self.BASE_URL,
                params={
                    'function': 'TIME_SERIES_DAILY',
                    'symbol': symbol,
                    'outputsize': 'compact',
                    'apikey': self.api_key
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit: {data.get('Note', '')[:100]}")
                return self._cache.get(cache_key, [])
            
            if 'Time Series (Daily)' not in data:
                logger.warning(f"No daily data for {symbol}")
                return []
            
            time_series = data['Time Series (Daily)']
            cutoff_date = datetime.now() - timedelta(days=days)
            
            result = []
            for date_str, values in sorted(time_series.items()):
                date = datetime.strptime(date_str, '%Y-%m-%d')
                if date >= cutoff_date:
                    result.append({
                        'date': date_str,
                        'price': round(float(values['4. close']), 2)
                    })
            
            self._cache[cache_key] = result
            self._cache_time[cache_key] = datetime.now()
            
            logger.info(f"Fetched {len(result)} daily prices for {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching daily prices for {symbol}: {e}")
            return self._cache.get(cache_key, [])


alpha_vantage_service = AlphaVantageService()
