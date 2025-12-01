"""
OMNIX Finnhub Service
Real-time news, earnings calendar, and sentiment analysis
Requires FINNHUB_API_KEY environment variable
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class FinnhubService:
    """
    Finnhub integration for:
    - Real-time company news
    - Earnings calendar (to avoid volatility)
    - News sentiment analysis
    - Market status
    """
    
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self):
        self.api_key = os.environ.get('FINNHUB_API_KEY')
        self._news_cache = {}
        self._cache_time = {}
        self._cache_duration = timedelta(minutes=5)
        
        if not self.api_key:
            logger.warning("FINNHUB_API_KEY not configured - Finnhub features disabled")
    
    def is_available(self) -> bool:
        """Check if Finnhub API is configured."""
        return self.api_key is not None
    
    def get_company_news(self, symbol: str, days: int = 7) -> Optional[List[Dict]]:
        """
        Get recent news for a specific company/crypto.
        
        Args:
            symbol: Stock ticker (AAPL, TSLA) or crypto (BTC)
            days: Number of days to look back
            
        Returns:
            List of news articles with headlines, summaries, sentiment
        """
        if not self.api_key:
            return None
        
        cache_key = f"news_{symbol}_{days}"
        if self._is_cache_valid(cache_key):
            return self._news_cache.get(cache_key)
        
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            response = requests.get(
                f"{self.BASE_URL}/company-news",
                params={
                    'symbol': symbol,
                    'from': from_date,
                    'to': today,
                    'token': self.api_key
                },
                timeout=10
            )
            response.raise_for_status()
            news = response.json()
            
            articles = []
            for article in news[:20]:
                articles.append({
                    'headline': article.get('headline', ''),
                    'summary': article.get('summary', '')[:200] + '...' if article.get('summary') else '',
                    'source': article.get('source', ''),
                    'url': article.get('url', ''),
                    'datetime': datetime.fromtimestamp(article.get('datetime', 0)),
                    'category': article.get('category', 'general'),
                    'related': article.get('related', symbol)
                })
            
            self._news_cache[cache_key] = articles
            self._cache_time[cache_key] = datetime.now()
            
            logger.info(f"Fetched {len(articles)} news articles for {symbol}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return self._news_cache.get(cache_key)
    
    def get_general_news(self, category: str = 'general') -> Optional[List[Dict]]:
        """
        Get general market news.
        
        Args:
            category: 'general', 'forex', 'crypto', 'merger'
        """
        if not self.api_key:
            return None
        
        cache_key = f"general_{category}"
        if self._is_cache_valid(cache_key):
            return self._news_cache.get(cache_key)
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/news",
                params={
                    'category': category,
                    'token': self.api_key
                },
                timeout=10
            )
            response.raise_for_status()
            news = response.json()
            
            articles = []
            for article in news[:15]:
                articles.append({
                    'headline': article.get('headline', ''),
                    'summary': article.get('summary', '')[:200] + '...' if article.get('summary') else '',
                    'source': article.get('source', ''),
                    'url': article.get('url', ''),
                    'datetime': datetime.fromtimestamp(article.get('datetime', 0)),
                    'category': category
                })
            
            self._news_cache[cache_key] = articles
            self._cache_time[cache_key] = datetime.now()
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching general news: {e}")
            return self._news_cache.get(cache_key)
    
    def get_news_sentiment(self, symbol: str) -> Optional[Dict]:
        """
        Get aggregated news sentiment for a symbol.
        
        Returns:
            Dict with sentiment score, buzz metrics, and sector comparison
        """
        if not self.api_key:
            return None
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/news-sentiment",
                params={
                    'symbol': symbol,
                    'token': self.api_key
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            buzz = data.get('buzz', {})
            sentiment = data.get('sentiment', {})
            
            result = {
                'symbol': symbol,
                'company_score': data.get('companyNewsScore', 0),
                'sector_avg_score': data.get('sectorAverageBullishPercent', 0),
                'articles_this_week': buzz.get('articlesInLastWeek', 0),
                'weekly_average': buzz.get('weeklyAverage', 0),
                'buzz_level': 'HIGH' if buzz.get('buzz', 0) > 1 else 'NORMAL',
                'bullish_percent': sentiment.get('bullishPercent', 0),
                'bearish_percent': sentiment.get('bearishPercent', 0),
                'recommendation': self._get_sentiment_recommendation(data)
            }
            
            logger.info(f"Sentiment for {symbol}: {result['recommendation']}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching sentiment for {symbol}: {e}")
            return None
    
    def get_earnings_calendar(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Get upcoming earnings announcements.
        Use this to avoid trading before high-volatility events.
        
        Returns:
            List of upcoming earnings with dates and symbols
        """
        if not self.api_key:
            return None
        
        try:
            if not from_date:
                from_date = datetime.now().strftime("%Y-%m-%d")
            if not to_date:
                to_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            
            response = requests.get(
                f"{self.BASE_URL}/calendar/earnings",
                params={
                    'from': from_date,
                    'to': to_date,
                    'token': self.api_key
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            earnings = []
            for item in data.get('earningsCalendar', [])[:50]:
                earnings.append({
                    'symbol': item.get('symbol', ''),
                    'date': item.get('date', ''),
                    'hour': item.get('hour', 'unknown'),
                    'eps_estimate': item.get('epsEstimate'),
                    'eps_actual': item.get('epsActual'),
                    'revenue_estimate': item.get('revenueEstimate'),
                    'year': item.get('year'),
                    'quarter': item.get('quarter')
                })
            
            logger.info(f"Found {len(earnings)} upcoming earnings events")
            return earnings
            
        except Exception as e:
            logger.error(f"Error fetching earnings calendar: {e}")
            return None
    
    def should_avoid_symbol(self, symbol: str) -> Dict:
        """
        Check if a symbol should be avoided due to upcoming earnings.
        
        Args:
            symbol: Stock ticker to check
            
        Returns:
            Dict with recommendation to trade or avoid
        """
        if not self.api_key:
            return {'should_avoid': False, 'reason': 'Finnhub not configured'}
        
        try:
            today = datetime.now()
            week_ahead = today + timedelta(days=3)
            
            earnings = self.get_earnings_calendar(
                from_date=today.strftime("%Y-%m-%d"),
                to_date=week_ahead.strftime("%Y-%m-%d")
            )
            
            if earnings:
                for event in earnings:
                    if event['symbol'].upper() == symbol.upper():
                        return {
                            'should_avoid': True,
                            'reason': f"Earnings report on {event['date']} - High volatility expected",
                            'event_date': event['date'],
                            'event_hour': event['hour']
                        }
            
            return {
                'should_avoid': False,
                'reason': 'No upcoming earnings events'
            }
            
        except Exception as e:
            logger.error(f"Error checking earnings for {symbol}: {e}")
            return {'should_avoid': False, 'reason': 'Error checking earnings'}
    
    def get_market_status(self) -> Optional[Dict]:
        """
        Get current market status (open/closed).
        """
        if not self.api_key:
            return None
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/stock/market-status",
                params={
                    'exchange': 'US',
                    'token': self.api_key
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                'exchange': data.get('exchange', 'US'),
                'is_open': data.get('isOpen', False),
                'session': data.get('session', 'unknown'),
                'timezone': data.get('timezone', 'America/New_York')
            }
            
        except Exception as e:
            logger.error(f"Error fetching market status: {e}")
            return None
    
    def _get_sentiment_recommendation(self, data: Dict) -> str:
        """Get trading recommendation based on sentiment data."""
        score = data.get('companyNewsScore', 0.5)
        
        if score >= 0.7:
            return "VERY_BULLISH"
        elif score >= 0.55:
            return "BULLISH"
        elif score >= 0.45:
            return "NEUTRAL"
        elif score >= 0.3:
            return "BEARISH"
        else:
            return "VERY_BEARISH"
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache_time:
            return False
        return datetime.now() - self._cache_time[key] < self._cache_duration


finnhub_service = FinnhubService()
