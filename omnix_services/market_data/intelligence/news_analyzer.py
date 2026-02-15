import logging

logger = logging.getLogger(__name__)

# Check if web analysis tools are available
try:
    import trafilatura
    import feedparser
    WEB_ANALYSIS_AVAILABLE = True
except ImportError:
    WEB_ANALYSIS_AVAILABLE = False

# Check if sentiment analysis is available
try:
    import textblob
    SENTIMENT_ANALYSIS_AVAILABLE = True
except ImportError:
    try:
        from textblob import TextBlob
        SENTIMENT_ANALYSIS_AVAILABLE = True
    except Exception:
        SENTIMENT_ANALYSIS_AVAILABLE = False


class FreeNewsAnalyzer:
    """Análisis gratuito de noticias crypto desde RSS feeds"""
    
    def __init__(self):
        self.news_sources = [
            'https://cointelegraph.com/rss',
            'https://feeds.coindesk.com/coindesk/news',
            'https://www.cryptocoinsnews.com/feed/',
            'https://bitcoinmagazine.com/feed'
        ]
        
    def get_crypto_news(self, limit=10):
        """Obtener noticias crypto gratuitas"""
        try:
            all_news = []
            for source in self.news_sources[:2]:
                try:
                    if WEB_ANALYSIS_AVAILABLE:
                        import feedparser
                        feed = feedparser.parse(source)
                        for entry in feed.entries[:limit//2]:
                            all_news.append({
                                'title': entry.title,
                                'summary': entry.get('summary', '')[:200],
                                'published': entry.get('published', ''),
                                'source': source.split('//')[1].split('/')[0]
                            })
                except Exception:
                    continue
            return all_news[:limit]
        except Exception:
            return []
    
    def analyze_sentiment(self, text):
        """Análisis sentiment gratuito"""
        try:
            if SENTIMENT_ANALYSIS_AVAILABLE:
                from textblob import TextBlob
                blob = TextBlob(text)
                sentiment = blob.sentiment.polarity
                
                if sentiment > 0.1:
                    return {'sentiment': 'POSITIVE', 'score': sentiment}
                elif sentiment < -0.1:
                    return {'sentiment': 'NEGATIVE', 'score': sentiment}
                else:
                    return {'sentiment': 'NEUTRAL', 'score': sentiment}
            else:
                positive_words = ['pump', 'moon', 'bullish', 'up', 'gain', 'rise', 'green']
                negative_words = ['dump', 'crash', 'bearish', 'down', 'loss', 'fall', 'red']
                
                text_lower = text.lower()
                positive_count = sum(1 for word in positive_words if word in text_lower)
                negative_count = sum(1 for word in negative_words if word in text_lower)
                
                if positive_count > negative_count:
                    return {'sentiment': 'POSITIVE', 'score': 0.5}
                elif negative_count > positive_count:
                    return {'sentiment': 'NEGATIVE', 'score': -0.5}
                else:
                    return {'sentiment': 'NEUTRAL', 'score': 0.0}
        except Exception:
            return {'sentiment': 'NEUTRAL', 'score': 0.0}
