"""
OMNIX INSTITUTIONAL+ - Web Search Manager

Orchestrates web searches with intelligent caching, rate limiting,
and automatic intent detection for AI-assisted searches.

Refactored to follow SOLID principles - IntentDetector extracted.
"""

import json
import hashlib
import logging
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime, timedelta

logger = logging.getLogger("OMNIX.WebSearchManager")

REDIS_AVAILABLE = False
get_redis_client: Optional[Callable[[], Any]] = None

try:
    from omnix_core.cache.redis_cache import get_redis_client  # type: ignore[import-not-found]
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Redis cache not available for web search")

from .tavily_search import TavilySearchClient, get_tavily_client
from .intent_detector import IntentDetector, get_intent_detector


class WebSearchManager:
    """
    Intelligent Web Search Manager
    
    Features:
    - Automatic search intent detection (via IntentDetector)
    - Redis caching with configurable TTL
    - Rate limiting to control costs
    - Fallback handling when API unavailable
    
    SOLID: Uses IntentDetector for search intent detection (SRP).
    """
    
    CACHE_TTL = 900
    RATE_LIMIT_SEARCHES = 30
    RATE_LIMIT_WINDOW = 60
    
    def __init__(self, intent_detector: IntentDetector = None):  # type: ignore[assignment]
        """Initialize the search manager"""
        self.tavily = get_tavily_client()
        self.intent_detector = intent_detector or get_intent_detector()
        self.redis = None
        self._init_redis()
        
        self.search_timestamps: List[datetime] = []
        self.total_searches = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        logger.info("✅ WebSearchManager initialized")
    
    def _init_redis(self):
        """Initialize Redis connection for caching"""
        if REDIS_AVAILABLE and get_redis_client is not None:
            try:
                self.redis = get_redis_client()
                if self.redis:
                    logger.info("✅ Redis cache enabled for web search")
            except Exception as e:
                logger.warning(f"⚠️ Redis init failed: {e}")
                self.redis = None
    
    def _get_cache_key(self, query: str, search_type: str = "search") -> str:
        """Generate cache key for a query"""
        normalized = query.lower().strip()
        query_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
        return f"websearch:{search_type}:{query_hash}"
    
    def _check_cache(self, cache_key: str) -> Optional[Dict]:
        """Check if result exists in cache"""
        if not self.redis:
            return None
        
        try:
            cached = self.redis.get(cache_key)
            if cached:
                self.cache_hits += 1
                logger.debug(f"✅ Cache hit: {cache_key}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"⚠️ Cache read error: {e}")
        
        return None
    
    def _set_cache(self, cache_key: str, data: Dict):
        """Store result in cache"""
        if not self.redis:
            return
        
        try:
            self.redis.setex(cache_key, self.CACHE_TTL, json.dumps(data))
            logger.debug(f"✅ Cached: {cache_key} (TTL: {self.CACHE_TTL}s)")
        except Exception as e:
            logger.warning(f"⚠️ Cache write error: {e}")
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.RATE_LIMIT_WINDOW)
        
        self.search_timestamps = [ts for ts in self.search_timestamps if ts > cutoff]
        
        if len(self.search_timestamps) >= self.RATE_LIMIT_SEARCHES:
            logger.warning(f"⚠️ Rate limit reached: {len(self.search_timestamps)}/{self.RATE_LIMIT_SEARCHES} searches in {self.RATE_LIMIT_WINDOW}s")
            return False
        
        return True
    
    def detect_search_intent(self, message: str) -> Dict[str, Any]:
        """
        Detect if a message requires a web search.
        
        Delegates to IntentDetector following Single Responsibility Principle.
        
        Returns:
            Dict with 'needs_search', 'confidence', 'suggested_query', 'reason'
        """
        return self.intent_detector.detect(message)
    
    def search(
        self, 
        query: str, 
        max_results: int = 5,
        use_cache: bool = True,
        force_search: bool = False
    ) -> Dict[str, Any]:
        """
        Perform a web search with caching and rate limiting
        
        Args:
            query: Search query
            max_results: Maximum results to return
            use_cache: Whether to use Redis cache
            force_search: Skip intent detection and search anyway
            
        Returns:
            Dict with search results or error
        """
        cache_key: Optional[str] = None
        
        if not force_search:
            intent = self.detect_search_intent(query)
            if not intent["needs_search"]:
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "No search intent detected",
                    "results": [],
                    "answer": None
                }
        
        if use_cache:
            cache_key = self._get_cache_key(query)
            cached = self._check_cache(cache_key)
            if cached:
                cached["from_cache"] = True
                return cached
            self.cache_misses += 1
        
        if not self._check_rate_limit():
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "results": [],
                "answer": None
            }
        
        if not self.tavily.available:
            return {
                "success": False,
                "error": "Web search not available",
                "tavily_status": self.tavily.get_status(),
                "results": [],
                "answer": None
            }
        
        self.search_timestamps.append(datetime.now())
        self.total_searches += 1
        
        result = self.tavily.search(query, max_results=max_results)
        
        if result["success"] and use_cache and cache_key:
            self._set_cache(cache_key, result)
        
        result["from_cache"] = False
        return result
    
    def get_context_for_ai(
        self, 
        query: str, 
        max_tokens: int = 2000,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Get search context formatted for AI/RAG applications
        
        This is the primary method for AI to use when it needs
        current information to answer a question.
        
        Args:
            query: The question or topic to search
            max_tokens: Approximate max tokens for context
            use_cache: Whether to use cache
            
        Returns:
            Context string ready to inject into AI prompt, or None
        """
        cache_key: Optional[str] = None
        
        if use_cache:
            cache_key = self._get_cache_key(query, "context")
            cached = self._check_cache(cache_key)
            if cached and "context" in cached:
                return cached["context"]
        
        if not self._check_rate_limit():
            logger.warning("⚠️ Rate limit - cannot get context")
            return None
        
        if not self.tavily.available:
            return None
        
        self.search_timestamps.append(datetime.now())
        self.total_searches += 1
        
        context = self.tavily.get_search_context(query, max_tokens=max_tokens)
        
        if context and use_cache and cache_key:
            self._set_cache(cache_key, {"context": context})
        
        return context
    
    def get_quick_answer(self, question: str, use_cache: bool = True) -> Optional[str]:
        """
        Get a quick, direct answer to a factual question
        
        Best for simple questions like "What is Bitcoin's price today?"
        
        Args:
            question: The question to answer
            use_cache: Whether to use cache
            
        Returns:
            Direct answer string, or None
        """
        cache_key: Optional[str] = None
        
        if use_cache:
            cache_key = self._get_cache_key(question, "qna")
            cached = self._check_cache(cache_key)
            if cached and "answer" in cached:
                return cached["answer"]
        
        if not self._check_rate_limit():
            return None
        
        if not self.tavily.available:
            return None
        
        self.search_timestamps.append(datetime.now())
        self.total_searches += 1
        
        answer = self.tavily.qna_search(question)
        
        if answer and use_cache and cache_key:
            self._set_cache(cache_key, {"answer": answer})
        
        return answer
    
    def is_available(self) -> bool:
        """Check if web search is available"""
        return self.tavily.available
    
    def get_status(self) -> Dict[str, Any]:
        """Get manager status for diagnostics"""
        return {
            "available": self.tavily.available,
            "tavily_status": self.tavily.get_status(),
            "redis_enabled": self.redis is not None,
            "cache_ttl_seconds": self.CACHE_TTL,
            "rate_limit": f"{self.RATE_LIMIT_SEARCHES}/{self.RATE_LIMIT_WINDOW}s",
            "stats": {
                "total_searches": self.total_searches,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate": f"{(self.cache_hits / max(self.cache_hits + self.cache_misses, 1)) * 100:.1f}%",
                "recent_searches": len(self.search_timestamps)
            }
        }


_search_manager: Optional[WebSearchManager] = None

def get_search_manager() -> WebSearchManager:
    """Get singleton WebSearchManager instance"""
    global _search_manager
    if _search_manager is None:
        _search_manager = WebSearchManager()
    return _search_manager
