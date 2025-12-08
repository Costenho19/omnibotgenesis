"""
OMNIX INSTITUTIONAL+ - Web Search Service

Provides real-time web search capabilities using Tavily API.
Integrates with AI services to enhance responses with current information.

Features:
- Tavily Search API integration
- Redis caching for cost optimization
- Rate limiting to prevent abuse
- Automatic fallback when API unavailable
"""

from .tavily_search import TavilySearchClient, get_tavily_client
from .search_manager import WebSearchManager, get_search_manager

__all__ = [
    'TavilySearchClient',
    'get_tavily_client', 
    'WebSearchManager',
    'get_search_manager'
]
