"""
OMNIX Fear & Greed Index Service
Uses Alternative.me API - 100% free, no API key required
Helps OMNIX understand market sentiment for better trade timing
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class FearGreedService:
    """
    Fear & Greed Index Service for market sentiment analysis.
    
    Classifications:
    - 0-24: Extreme Fear (potential buying opportunity)
    - 25-49: Fear
    - 50: Neutral
    - 51-75: Greed
    - 76-100: Extreme Greed (potential selling/waiting)
    """
    
    API_URL = "https://api.alternative.me/fng/"
    
    def __init__(self):
        self._cache = {}
        self._cache_time = None
        self._cache_duration = timedelta(minutes=30)
    
    def get_current_index(self) -> Optional[Dict]:
        """
        Get the current Fear & Greed Index value.
        
        Returns:
            Dict with value, classification, and trading recommendation
        """
        try:
            if self._is_cache_valid():
                return self._cache.get('current')
            
            response = requests.get(
                f"{self.API_URL}?limit=1",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                fng_data = data['data'][0]
                value = int(fng_data['value'])
                classification = fng_data['value_classification']
                
                result = {
                    'value': value,
                    'classification': classification,
                    'timestamp': datetime.fromtimestamp(int(fng_data['timestamp'])),
                    'recommendation': self._get_trading_recommendation(value),
                    'color': self._get_color(value),
                    'description': self._get_description(value)
                }
                
                self._cache['current'] = result
                self._cache_time = datetime.now()
                
                logger.info(f"Fear & Greed Index: {value} ({classification}) - {result['recommendation']}")
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed Index: {e}")
            return self._cache.get('current')
    
    def get_historical(self, days: int = 30) -> Optional[List[Dict]]:
        """
        Get historical Fear & Greed Index data.
        
        Args:
            days: Number of days of history to fetch
            
        Returns:
            List of daily Fear & Greed values
        """
        try:
            response = requests.get(
                f"{self.API_URL}?limit={days}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('data'):
                history = []
                for item in data['data']:
                    history.append({
                        'value': int(item['value']),
                        'classification': item['value_classification'],
                        'date': datetime.fromtimestamp(int(item['timestamp']))
                    })
                return history
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed history: {e}")
            return None
    
    def get_trend(self, days: int = 7) -> Optional[Dict]:
        """
        Analyze the trend of Fear & Greed over recent days.
        
        Returns:
            Dict with trend analysis (improving, worsening, stable)
        """
        history = self.get_historical(days)
        
        if not history or len(history) < 2:
            return None
        
        current = history[0]['value']
        oldest = history[-1]['value']
        avg = sum(h['value'] for h in history) / len(history)
        
        change = current - oldest
        
        if change > 10:
            trend = 'improving_to_greed'
            trend_description = 'Market sentiment improving (moving toward greed)'
        elif change < -10:
            trend = 'declining_to_fear'
            trend_description = 'Market sentiment declining (moving toward fear)'
        else:
            trend = 'stable'
            trend_description = 'Market sentiment relatively stable'
        
        return {
            'current': current,
            'average': round(avg, 1),
            'change': change,
            'trend': trend,
            'trend_description': trend_description,
            'days_analyzed': len(history)
        }
    
    def should_trade(self, signal_strength: str = 'MODERATE') -> Dict:
        """
        Determine if market sentiment supports trading.
        
        Args:
            signal_strength: VERY_STRONG, STRONG, or MODERATE
            
        Returns:
            Dict with trading recommendation based on sentiment
        """
        current = self.get_current_index()
        
        if not current:
            return {
                'should_trade': True,
                'reason': 'Fear & Greed data unavailable - using default behavior',
                'confidence_modifier': 1.0
            }
        
        value = current['value']
        
        if value <= 20:
            return {
                'should_trade': True,
                'reason': f"Extreme Fear ({value}) - Potential buying opportunity",
                'confidence_modifier': 1.2,
                'bias': 'BUY'
            }
        
        elif value <= 35:
            return {
                'should_trade': True,
                'reason': f"Fear ({value}) - Good conditions for careful buying",
                'confidence_modifier': 1.1,
                'bias': 'BUY'
            }
        
        elif value <= 65:
            return {
                'should_trade': True,
                'reason': f"Neutral/Moderate ({value}) - Normal trading conditions",
                'confidence_modifier': 1.0,
                'bias': 'NEUTRAL'
            }
        
        elif value <= 80:
            if signal_strength == 'VERY_STRONG':
                return {
                    'should_trade': True,
                    'reason': f"Greed ({value}) - Proceed with strong signals only",
                    'confidence_modifier': 0.9,
                    'bias': 'SELL'
                }
            else:
                return {
                    'should_trade': False,
                    'reason': f"Greed ({value}) - Consider waiting for better entry",
                    'confidence_modifier': 0.8,
                    'bias': 'SELL'
                }
        
        else:
            return {
                'should_trade': False,
                'reason': f"Extreme Greed ({value}) - High risk of reversal, avoid new positions",
                'confidence_modifier': 0.5,
                'bias': 'SELL'
            }
    
    def _get_trading_recommendation(self, value: int) -> str:
        """Get trading recommendation based on Fear & Greed value."""
        if value <= 20:
            return "STRONG_BUY_OPPORTUNITY"
        elif value <= 35:
            return "BUY_OPPORTUNITY"
        elif value <= 50:
            return "NEUTRAL_SLIGHT_BUY"
        elif value <= 65:
            return "NEUTRAL"
        elif value <= 80:
            return "CAUTION"
        else:
            return "EXTREME_CAUTION"
    
    def _get_color(self, value: int) -> str:
        """Get color code for UI display."""
        if value <= 25:
            return "#ff3366"
        elif value <= 45:
            return "#ff9933"
        elif value <= 55:
            return "#ffff00"
        elif value <= 75:
            return "#99ff33"
        else:
            return "#00ff88"
    
    def _get_description(self, value: int) -> str:
        """Get human-readable description."""
        if value <= 20:
            return "El mercado está en PÁNICO EXTREMO. Históricamente buen momento para comprar."
        elif value <= 35:
            return "El mercado tiene MIEDO. Posible oportunidad de compra."
        elif value <= 50:
            return "Sentimiento NEUTRAL con ligera tendencia al miedo."
        elif value <= 65:
            return "Sentimiento NEUTRAL con ligera tendencia a la codicia."
        elif value <= 80:
            return "El mercado tiene CODICIA. Precaución recomendada."
        else:
            return "CODICIA EXTREMA. Alto riesgo de corrección. Evitar nuevas posiciones."
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self._cache_time or not self._cache:
            return False
        return datetime.now() - self._cache_time < self._cache_duration


fear_greed_service = FearGreedService()
