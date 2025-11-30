"""
📊 Stock Technical Analyzer
RSI, MACD, EMA strategies adapted for stock market
"""

import logging
import numpy as np
import os
from typing import Dict, List, Optional, Tuple
import requests

logger = logging.getLogger(__name__)


class StockAnalyzer:
    """
    Technical analysis for stocks using same strategies as crypto
    Adapted for lower volatility and market hours
    """
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
    
    def fetch_historical_data(self, symbol: str, interval: str = '5min', outputsize: str = 'compact') -> Optional[List[Dict]]:
        """
        Fetch historical OHLCV data from Alpha Vantage
        interval: '1min', '5min', '15min', '30min', '60min', 'daily'
        """
        try:
            if interval == 'daily':
                function = 'TIME_SERIES_DAILY'
                key = 'Time Series (Daily)'
            else:
                function = 'TIME_SERIES_INTRADAY'
                key = f'Time Series ({interval})'
            
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': self.alpha_vantage_key,
                'outputsize': outputsize
            }
            
            if interval != 'daily':
                params['interval'] = interval
            
            response = requests.get(
                'https://www.alphavantage.co/query',
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if key not in data:
                    logger.error(f"API response missing data: {data}")
                    return None
                
                time_series = data[key]
                candles = []
                
                for timestamp, values in sorted(time_series.items()):
                    candles.append({
                        'timestamp': timestamp,
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': int(values['5. volume'])
                    })
                
                return candles
        
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict]:
        """Calculate MACD indicator"""
        if len(prices) < slow + signal:
            return None
        
        prices_array = np.array(prices)
        
        # Calculate EMAs
        ema_fast = self._calculate_ema(prices_array, fast)
        ema_slow = self._calculate_ema(prices_array, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': round(macd_line[-1], 4),
            'signal': round(signal_line[-1], 4),
            'histogram': round(histogram[-1], 4)
        }
    
    def calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate single EMA value"""
        if len(prices) < period:
            return None
        
        ema_values = self._calculate_ema(np.array(prices), period)
        return round(ema_values[-1], 4)
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Internal EMA calculation"""
        multiplier = 2 / (period + 1)
        ema = np.zeros(len(prices))
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = (prices[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        return ema
    
    def analyze_stock(self, symbol: str) -> Optional[Dict]:
        """
        Complete technical analysis for a stock
        Returns signals and indicators
        """
        # Fetch intraday data (5min candles)
        candles = self.fetch_historical_data(symbol, interval='5min', outputsize='full')
        
        if not candles or len(candles) < 100:
            logger.warning(f"Insufficient data for {symbol}")
            return None
        
        closes = [c['close'] for c in candles]
        
        # Calculate indicators
        rsi = self.calculate_rsi(closes, period=14)
        macd = self.calculate_macd(closes, fast=12, slow=26, signal=9)
        ema_9 = self.calculate_ema(closes, 9)
        ema_21 = self.calculate_ema(closes, 21)
        ema_50 = self.calculate_ema(closes, 50)
        
        current_price = closes[-1]
        
        # Generate signals (same logic as crypto but adapted)
        signals = {
            'symbol': symbol,
            'current_price': current_price,
            'rsi': rsi,
            'macd': macd,
            'ema_9': ema_9,
            'ema_21': ema_21,
            'ema_50': ema_50,
            'signal': self._generate_signal(rsi, macd, ema_9, ema_21, ema_50, current_price),
            'confidence': self._calculate_confidence(rsi, macd, ema_9, ema_21)
        }
        
        return signals
    
    def _generate_signal(self, rsi, macd, ema_9, ema_21, ema_50, price) -> str:
        """Generate BUY/SELL/HOLD signal"""
        buy_votes = 0
        sell_votes = 0
        
        # RSI signal
        if rsi and rsi < 35:
            buy_votes += 1
        elif rsi and rsi > 65:
            sell_votes += 1
        
        # MACD signal
        if macd and macd['macd'] > macd['signal'] and macd['histogram'] > 0:
            buy_votes += 1
        elif macd and macd['macd'] < macd['signal'] and macd['histogram'] < 0:
            sell_votes += 1
        
        # EMA crossover
        if ema_9 and ema_21:
            if ema_9 > ema_21:
                buy_votes += 1
            elif ema_9 < ema_21:
                sell_votes += 1
        
        # Long-term trend (EMA 50)
        if ema_50 and price > ema_50:
            buy_votes += 0.5
        elif ema_50 and price < ema_50:
            sell_votes += 0.5
        
        if buy_votes > sell_votes and buy_votes >= 2:
            return 'BUY'
        elif sell_votes > buy_votes and sell_votes >= 2:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _calculate_confidence(self, rsi, macd, ema_9, ema_21) -> float:
        """Calculate signal confidence (0-100%)"""
        confidence = 0
        total_checks = 0
        
        # RSI confidence
        if rsi:
            total_checks += 1
            if rsi < 30 or rsi > 70:
                confidence += 30
            elif rsi < 40 or rsi > 60:
                confidence += 15
        
        # MACD confidence
        if macd:
            total_checks += 1
            if abs(macd['histogram']) > 0.5:
                confidence += 30
            elif abs(macd['histogram']) > 0.2:
                confidence += 15
        
        # EMA confidence
        if ema_9 and ema_21:
            total_checks += 1
            diff_pct = abs(ema_9 - ema_21) / ema_21 * 100
            if diff_pct > 2:
                confidence += 40
            elif diff_pct > 0.5:
                confidence += 20
        
        if total_checks == 0:
            return 0
        
        return min(100, confidence)


import os
