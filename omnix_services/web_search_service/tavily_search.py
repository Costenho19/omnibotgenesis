"""
OMNIX INSTITUTIONAL+ - Tavily Search Client

Direct integration with Tavily Search API for real-time web searches.
Optimized for AI/RAG applications with context-aware responses.
"""

import os
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger("OMNIX.WebSearch")

TAVILY_AVAILABLE = False
try:
    from tavily import TavilyClient, MissingAPIKeyError, InvalidAPIKeyError, UsageLimitExceededError
    TAVILY_AVAILABLE = True
    logger.info("✅ Tavily SDK loaded successfully")
except ImportError:
    logger.warning("⚠️ Tavily SDK not installed - web search disabled")
    TavilyClient = None
    MissingAPIKeyError = Exception
    InvalidAPIKeyError = Exception
    UsageLimitExceededError = Exception


class TavilySearchClient:
    """
    Tavily Search API Client
    
    Provides web search capabilities optimized for AI applications.
    Features RAG context mode and Q&A direct answers.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Tavily client with API key"""
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.client = None
        self.available = False
        self.last_error = None
        self.search_count = 0
        self.last_search_time = None
        
        self._initialize()
    
    def _initialize(self):
        """Initialize the Tavily client"""
        if not TAVILY_AVAILABLE:
            self.last_error = "Tavily SDK not installed"
            logger.warning("⚠️ Tavily SDK not available")
            return
        
        if not self.api_key:
            self.last_error = "TAVILY_API_KEY not configured"
            logger.warning("⚠️ TAVILY_API_KEY not set - web search disabled")
            return
        
        try:
            self.client = TavilyClient(api_key=self.api_key)
            self.available = True
            logger.info("✅ Tavily Search Client initialized successfully")
        except MissingAPIKeyError:
            self.last_error = "Missing API key"
            logger.error("❌ Tavily: Missing API key")
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"❌ Tavily initialization error: {e}")
    
    def search(
        self, 
        query: str, 
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform a web search
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-10)
            search_depth: "basic" or "advanced" (advanced costs more)
            include_domains: Only search these domains
            exclude_domains: Exclude these domains
            
        Returns:
            Dict with 'success', 'results', 'answer', 'error' keys
        """
        if not self.available:
            return {
                "success": False,
                "error": self.last_error or "Tavily not available",
                "results": [],
                "answer": None
            }
        
        try:
            self.last_search_time = datetime.now()
            self.search_count += 1
            
            kwargs = {
                "query": query,
                "max_results": min(max_results, 10),
                "search_depth": search_depth
            }
            
            if include_domains:
                kwargs["include_domains"] = include_domains
            if exclude_domains:
                kwargs["exclude_domains"] = exclude_domains
            
            response = self.client.search(**kwargs)
            
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0)
                })
            
            logger.info(f"✅ Tavily search: '{query[:50]}...' → {len(results)} results")
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "answer": response.get("answer"),
                "response_time": response.get("response_time", 0),
                "error": None
            }
            
        except InvalidAPIKeyError:
            self.last_error = "Invalid API key"
            logger.error("❌ Tavily: Invalid API key")
            return {"success": False, "error": "Invalid API key", "results": [], "answer": None}
            
        except UsageLimitExceededError:
            self.last_error = "Usage limit exceeded"
            logger.warning("⚠️ Tavily: Usage limit exceeded")
            return {"success": False, "error": "Usage limit exceeded", "results": [], "answer": None}
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"❌ Tavily search error: {e}")
            return {"success": False, "error": str(e), "results": [], "answer": None}
    
    def get_search_context(self, query: str, max_tokens: int = 4000) -> Optional[str]:
        """
        Get search results formatted as context for RAG/AI applications
        
        This is optimized for injecting into AI prompts.
        
        Args:
            query: Search query
            max_tokens: Approximate max tokens for context
            
        Returns:
            Context string or None if failed
        """
        if not self.available:
            return None
        
        try:
            context = self.client.get_search_context(
                query=query,
                max_tokens=max_tokens
            )
            logger.info(f"✅ Tavily context: '{query[:50]}...' → {len(context)} chars")
            return context
        except Exception as e:
            logger.error(f"❌ Tavily context error: {e}")
            return None
    
    def qna_search(self, query: str) -> Optional[str]:
        """
        Get a direct answer to a question
        
        Best for factual questions that need a concise answer.
        
        Args:
            query: Question to answer
            
        Returns:
            Answer string or None if failed
        """
        if not self.available:
            return None
        
        try:
            answer = self.client.qna_search(query=query)
            logger.info(f"✅ Tavily Q&A: '{query[:50]}...' → answer received")
            return answer
        except Exception as e:
            logger.error(f"❌ Tavily Q&A error: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status for diagnostics"""
        return {
            "available": self.available,
            "tavily_sdk_installed": TAVILY_AVAILABLE,
            "api_key_configured": bool(self.api_key),
            "search_count": self.search_count,
            "last_search": self.last_search_time.isoformat() if self.last_search_time else None,
            "last_error": self.last_error
        }


_tavily_client: Optional[TavilySearchClient] = None

def get_tavily_client() -> TavilySearchClient:
    """Get singleton Tavily client instance"""
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilySearchClient()
    return _tavily_client
