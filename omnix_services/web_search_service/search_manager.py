"""
Web Search Manager V6.5.4 INSTITUTIONAL+

Orchestrates web searches with intelligent caching, rate limiting,
and automatic intent detection for AI-assisted searches.
"""

import os
import json
import hashlib
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger("OMNIX.WebSearchManager")

try:
    from omnix_core.cache.redis_cache import get_redis_client
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️ Redis cache not available for web search")

from .tavily_search import TavilySearchClient, get_tavily_client


SEARCH_INTENT_KEYWORDS = [
    # Time-sensitive triggers (HIGH PRIORITY - require current info)
    "qué pasó", "what happened", "noticias", "news", "hoy", "today",
    "ayer", "yesterday", "esta semana", "this week", "últimas", "latest",
    "recientes", "recent", "última hora", "breaking",
    "anunció", "announced", "reportó", "reported", "dijo", "said",
    "según", "according to", "fuentes", "sources", "rumor", "rumores",
    "predicción", "prediction", "forecast", "pronóstico",
    "por qué subió", "why did it go up", "por qué bajó", "why did it drop",
    "qué está pasando", "what's happening", "busca", "search", "encuentra", "find",
    # V6.5.4 Premium - Event-specific triggers (not generic conversation)
    "pasó algo", "sucedió", "ocurrió",
    "2024", "2025", "diciembre", "december",
    "subió", "bajó", "cayó", "dropped", "rose", "fell", "crashed", "pumped",
    "rally", "dump", "pump", "crash",
    "halving", "etf", "aprobación", "approval",
    "elon musk", "trump", "biden", "powell", "gensler"
]

CRYPTO_FINANCE_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "crypto", "criptomoneda",
    "solana", "sol", "xrp", "ripple", "dogecoin", "doge", "cardano", "ada",
    "fed", "federal reserve", "powell", "sec", "regulación", "regulation",
    "etf", "blackrock", "grayscale", "binance", "coinbase", "kraken",
    "mercado", "market", "trading", "inversión", "investment",
    "inflación", "inflation", "tasas", "rates", "interest",
    "acciones", "stocks", "nasdaq", "s&p", "dow jones"
]


class WebSearchManager:
    """
    Intelligent Web Search Manager
    
    Features:
    - Automatic search intent detection
    - Redis caching with configurable TTL
    - Rate limiting to control costs
    - Fallback handling when API unavailable
    """
    
    CACHE_TTL = 900
    RATE_LIMIT_SEARCHES = 30
    RATE_LIMIT_WINDOW = 60
    
    def __init__(self):
        """Initialize the search manager"""
        self.tavily = get_tavily_client()
        self.redis = None
        self._init_redis()
        
        self.search_timestamps: List[datetime] = []
        self.total_searches = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        logger.info("✅ WebSearchManager initialized")
    
    def _init_redis(self):
        """Initialize Redis connection for caching"""
        if REDIS_AVAILABLE:
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
        Detect if a message requires a web search
        
        Returns:
            Dict with 'needs_search', 'confidence', 'suggested_query', 'reason'
        """
        message_lower = message.lower()
        
        intent_score = 0
        matched_intent_keywords = []
        for keyword in SEARCH_INTENT_KEYWORDS:
            if keyword in message_lower:
                intent_score += 1
                matched_intent_keywords.append(keyword)
        
        topic_score = 0
        matched_topic_keywords = []
        for keyword in CRYPTO_FINANCE_KEYWORDS:
            if keyword in message_lower:
                topic_score += 1
                matched_topic_keywords.append(keyword)
        
        is_question = any(q in message_lower for q in ["?", "qué", "what", "cuál", "which", "cómo", "how", "por qué", "why", "cuándo", "when", "dónde", "where"])
        
        # V6.5.4 Premium: Balanced scoring to avoid over-triggering
        total_score = intent_score * 2 + topic_score + (1 if is_question else 0)
        confidence = min(total_score / 10, 1.0)
        
        # V6.5.4: Require BOTH intent keyword AND topic keyword to trigger
        # This prevents generic questions from triggering search
        # Only exception: explicit search commands ("busca", "search", "encuentra")
        explicit_search = any(cmd in message_lower for cmd in ["busca ", "buscar ", "encuentra ", "search ", "find "])
        needs_search = explicit_search or (intent_score >= 1 and topic_score >= 1) or (is_question and intent_score >= 1 and topic_score >= 1)
        
        suggested_query = message
        if matched_topic_keywords and not matched_intent_keywords:
            suggested_query = f"{message} últimas noticias"
        
        reason = None
        if needs_search:
            if matched_intent_keywords:
                reason = f"Detected search intent: {', '.join(matched_intent_keywords[:3])}"
            elif matched_topic_keywords:
                reason = f"Topic requires current info: {', '.join(matched_topic_keywords[:3])}"
            else:
                reason = "Question format detected"
        
        return {
            "needs_search": needs_search,
            "confidence": confidence,
            "suggested_query": suggested_query,
            "reason": reason,
            "intent_keywords": matched_intent_keywords,
            "topic_keywords": matched_topic_keywords
        }
    
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
        
        if result["success"] and use_cache:
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
        
        if context and use_cache:
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
        
        if answer and use_cache:
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
