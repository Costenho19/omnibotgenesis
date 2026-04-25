"""
OMNIX Dashboard - Intelligence Blueprint
Market Intelligence API routes (/api/intelligence/*, /api/news)
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify

from omnix_dashboard.utils.external_apis import http_get_with_timeout
from omnix_dashboard.utils.decorators import require_api_key

logger = logging.getLogger(__name__)

intelligence_bp = Blueprint('intelligence', __name__)

_fear_greed_service = None
_finnhub_service = None
_alpha_vantage_service = None


def _get_fear_greed_service():
    """Lazy-load fear_greed_service to avoid import-time side effects."""
    global _fear_greed_service
    if _fear_greed_service is None:
        try:
            from omnix_services.market_intelligence import fear_greed_service
            _fear_greed_service = fear_greed_service
        except ImportError as e:
            logger.warning(f"Could not import fear_greed_service: {e}")
            _fear_greed_service = False
    return _fear_greed_service if _fear_greed_service else None


def _get_finnhub_service():
    """Lazy-load finnhub_service to avoid import-time side effects."""
    global _finnhub_service
    if _finnhub_service is None:
        try:
            from omnix_services.market_intelligence import finnhub_service
            _finnhub_service = finnhub_service
        except ImportError as e:
            logger.warning(f"Could not import finnhub_service: {e}")
            _finnhub_service = False
    return _finnhub_service if _finnhub_service else None


def _get_alpha_vantage_service():
    """Lazy-load alpha_vantage_service to avoid import-time side effects."""
    global _alpha_vantage_service
    if _alpha_vantage_service is None:
        try:
            from omnix_services.market_intelligence import alpha_vantage_service
            _alpha_vantage_service = alpha_vantage_service
        except ImportError as e:
            logger.warning(f"Could not import alpha_vantage_service: {e}")
            _alpha_vantage_service = False
    return _alpha_vantage_service if _alpha_vantage_service else None


@intelligence_bp.route('/api/news')
def api_news():
    """API endpoint for financial news via centralized Finnhub service"""
    try:
        finnhub_service = _get_finnhub_service()
        
        if finnhub_service and finnhub_service.is_available():
            raw_news = finnhub_service.get_general_news('crypto')
            
            if raw_news and len(raw_news) > 0:
                news = []
                for item in raw_news[:10]:
                    dt = item.get('datetime')
                    if isinstance(dt, datetime):
                        published = dt.isoformat()
                    elif isinstance(dt, (int, float)):
                        published = datetime.fromtimestamp(dt).isoformat()
                    else:
                        published = ''
                    
                    news.append({
                        'title': item.get('headline', ''),
                        'description': item.get('summary', '')[:150] + '...' if item.get('summary') else '',
                        'url': item.get('url', ''),
                        'source': item.get('source', 'Finnhub'),
                        'published': published,
                        'category': 'crypto'
                    })
                
                return jsonify({
                    'success': True,
                    'news': news,
                    'source': 'Finnhub News',
                    'timestamp': datetime.now().isoformat()
                })
    except Exception as e:
        logger.warning(f"Finnhub service error in /api/news: {e}")
    
    news = [
        {
            'title': 'Bitcoin mantiene soporte en niveles clave',
            'description': 'Los analistas observan consolidacion mientras el mercado espera el proximo movimiento...',
            'source': 'OMNIX Analysis',
            'category': 'crypto',
            'published': datetime.now().isoformat()
        },
        {
            'title': 'ETH 2.0 muestra adopcion institucional creciente',
            'description': 'Grandes fondos continuan acumulando Ethereum en anticipacion a actualizaciones...',
            'source': 'OMNIX Analysis',
            'category': 'crypto',
            'published': datetime.now().isoformat()
        },
        {
            'title': 'Mercados tradicionales impactan correlacion crypto',
            'description': 'La correlacion entre S&P500 y Bitcoin alcanza nuevos niveles esta semana...',
            'source': 'OMNIX Analysis',
            'category': 'markets',
            'published': datetime.now().isoformat()
        }
    ]
    
    return jsonify({
        'success': True,
        'news': news,
        'source': 'OMNIX Fallback',
        'timestamp': datetime.now().isoformat()
    })


@intelligence_bp.route('/api/intelligence/fear-greed')
@require_api_key
def api_fear_greed():
    """API endpoint for Fear & Greed Index via market intelligence service"""
    try:
        fear_greed_service = _get_fear_greed_service()
        
        if not fear_greed_service:
            return jsonify({
                'success': False,
                'error': 'Fear & Greed service not available'
            })
        
        current = fear_greed_service.get_current_index()
        trend = fear_greed_service.get_trend(7)
        
        if current:
            return jsonify({
                'success': True,
                'current': {
                    'value': current['value'],
                    'classification': current['classification'],
                    'recommendation': current['recommendation'],
                    'color': current['color'],
                    'description': current['description']
                },
                'trend': trend,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'success': False,
            'error': 'Unable to fetch Fear & Greed data'
        })
        
    except Exception as e:
        logger.error(f"Error in fear-greed endpoint: {e}")
        return jsonify({
            'success': False,
            'error': "Internal server error"
        })


@intelligence_bp.route('/api/intelligence/finnhub/news')
@require_api_key
def api_finnhub_news():
    """API endpoint for Finnhub financial news via market intelligence service"""
    try:
        finnhub_service = _get_finnhub_service()
        
        if not finnhub_service:
            return jsonify({
                'success': False,
                'error': 'Finnhub service not available'
            })
        
        if not finnhub_service.is_available():
            return jsonify({
                'success': False,
                'error': 'FINNHUB_API_KEY not configured'
            })
        
        news = finnhub_service.get_general_news('general')
        
        return jsonify({
            'success': True,
            'news': news[:10] if news else [],
            'source': 'Finnhub',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in finnhub news endpoint: {e}")
        return jsonify({
            'success': False,
            'error': "Internal server error"
        })


@intelligence_bp.route('/api/intelligence/finnhub/sentiment/<symbol>')
@require_api_key
def api_finnhub_sentiment(symbol):
    """API endpoint for Finnhub news sentiment"""
    try:
        finnhub_service = _get_finnhub_service()
        
        if not finnhub_service:
            return jsonify({
                'success': False,
                'error': 'Finnhub service not available'
            })
        
        if not finnhub_service.is_available():
            return jsonify({
                'success': False,
                'error': 'FINNHUB_API_KEY not configured'
            })
        
        sentiment = finnhub_service.get_news_sentiment(symbol)
        
        return jsonify({
            'success': True,
            'sentiment': sentiment,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in sentiment endpoint: {e}")
        return jsonify({
            'success': False,
            'error': "Internal server error"
        })


@intelligence_bp.route('/api/intelligence/alpha-vantage/technical/<symbol>')
@require_api_key
def api_alpha_vantage_technical(symbol):
    """API endpoint for Alpha Vantage technical indicators via market intelligence service"""
    try:
        alpha_vantage_service = _get_alpha_vantage_service()
        
        if not alpha_vantage_service:
            return jsonify({
                'success': False,
                'error': 'Alpha Vantage service not available'
            })
        
        if not alpha_vantage_service.is_available():
            return jsonify({
                'success': False,
                'error': 'ALPHA_VANTAGE_API_KEY not configured'
            })
        
        summary = alpha_vantage_service.get_technical_summary(symbol)
        
        return jsonify({
            'success': True,
            'technical': summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in alpha vantage endpoint: {e}")
        return jsonify({
            'success': False,
            'error': "Internal server error"
        })


@intelligence_bp.route('/api/intelligence/summary')
@require_api_key
def api_intelligence_summary():
    """Combined market intelligence summary"""
    try:
        fear_greed_service = _get_fear_greed_service()
        finnhub_service = _get_finnhub_service()
        alpha_vantage_service = _get_alpha_vantage_service()
        
        fear_greed = None
        if fear_greed_service:
            fear_greed = fear_greed_service.get_current_index()
        
        finnhub_available = finnhub_service.is_available() if finnhub_service else False
        alpha_available = alpha_vantage_service.is_available() if alpha_vantage_service else False
        
        return jsonify({
            'success': True,
            'fear_greed': {
                'value': fear_greed['value'] if fear_greed else None,
                'classification': fear_greed['classification'] if fear_greed else None,
                'recommendation': fear_greed['recommendation'] if fear_greed else None
            } if fear_greed else None,
            'services': {
                'fear_greed': fear_greed_service is not None,
                'finnhub': finnhub_available,
                'alpha_vantage': alpha_available
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in intelligence summary: {e}")
        return jsonify({
            'success': False,
            'error': "Internal server error"
        })
