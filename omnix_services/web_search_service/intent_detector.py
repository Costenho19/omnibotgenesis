"""
OMNIX INSTITUTIONAL+ - Search Intent Detector

Detects when a user message requires a web search based on
intent keywords, topic keywords, and question patterns.

Follows Single Responsibility Principle (SRP) - only handles intent detection.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger("OMNIX.IntentDetector")


SEARCH_INTENT_KEYWORDS = [
    "qué pasó", "what happened", "noticias", "news", "hoy", "today",
    "ayer", "yesterday", "esta semana", "this week", "últimas", "latest",
    "recientes", "recent", "última hora", "breaking",
    "anunció", "announced", "reportó", "reported", "dijo", "said",
    "según", "according to", "fuentes", "sources", "rumor", "rumores",
    "predicción", "prediction", "forecast", "pronóstico",
    "por qué subió", "why did it go up", "por qué bajó", "why did it drop",
    "qué está pasando", "what's happening", "busca", "search", "encuentra", "find",
    "pasó algo", "sucedió", "ocurrió",
    "2024", "2025", "diciembre", "december",
    "subió", "bajó", "cayó", "dropped", "rose", "fell", "crashed", "pumped",
    "rally", "dump", "pump", "crash",
    "halving", "etf", "aprobación", "approval",
    "elon musk", "trump", "biden", "powell", "gensler",
    "resumen", "summary", "reporte", "report", "análisis", "analysis",
    "cierre", "close", "apertura", "open", "sesión", "session",
    "comportamiento", "performance", "rendimiento", "returns",
    "lunes", "monday", "martes", "tuesday", "miércoles", "wednesday",
    "jueves", "thursday", "viernes", "friday", "sábado", "saturday", "domingo", "sunday",
    "semana pasada", "last week", "mes pasado", "last month",
    "esta mañana", "this morning", "anoche", "last night"
]

CRYPTO_FINANCE_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "crypto", "criptomoneda", "criptomonedas",
    "solana", "sol", "xrp", "ripple", "dogecoin", "doge", "cardano", "ada",
    "avalanche", "avax", "polkadot", "dot", "chainlink", "link", "polygon", "matic",
    "litecoin", "ltc", "cosmos", "atom", "altcoin", "altcoins", "memecoin",
    "binance", "coinbase", "kraken", "ftx", "gemini", "bybit", "okx", "kucoin",
    "bolsa", "bolsa de valores", "stock market", "wall street",
    "nasdaq", "nyse", "s&p", "s&p 500", "dow jones", "dow", "russell",
    "acciones", "stocks", "equities", "equity", "acción",
    "spy", "qqq", "dia", "iwm", "vti", "voo", "arkk",
    "índice", "index", "indices", "futures", "futuros",
    "tech", "tecnología", "tecnológicas", "financieras", "bancarias",
    "apple", "aapl", "microsoft", "msft", "google", "googl", "amazon", "amzn",
    "tesla", "tsla", "nvidia", "nvda", "meta", "netflix", "nflx",
    "fed", "federal reserve", "powell", "sec", "regulación", "regulation",
    "etf", "blackrock", "grayscale", "vanguard", "fidelity",
    "mercado", "market", "trading", "inversión", "investment",
    "inflación", "inflation", "tasas", "rates", "interest", "cpi", "ppi",
    "gdp", "pib", "unemployment", "desempleo", "jobs", "empleos", "nóminas", "payrolls",
    "bull", "bear", "bullish", "bearish", "alcista", "bajista",
    "volatilidad", "volatility", "vix", "fear", "greed", "miedo", "codicia"
]

QUESTION_MARKERS = [
    "?", "qué", "what", "cuál", "which", "cómo", "how", 
    "por qué", "why", "cuándo", "when", "dónde", "where"
]

EXPLICIT_SEARCH_COMMANDS = ["busca ", "buscar ", "encuentra ", "search ", "find "]


class IntentDetector:
    """
    Detects whether a message requires a web search.
    
    Single Responsibility: Only handles intent detection logic.
    Easily testable and replaceable.
    """
    
    def __init__(
        self,
        intent_keywords: List[str] = SEARCH_INTENT_KEYWORDS,
        topic_keywords: List[str] = CRYPTO_FINANCE_KEYWORDS,
        question_markers: List[str] = QUESTION_MARKERS,
        search_commands: List[str] = EXPLICIT_SEARCH_COMMANDS
    ):
        self.intent_keywords = intent_keywords
        self.topic_keywords = topic_keywords
        self.question_markers = question_markers
        self.search_commands = search_commands
    
    def detect(self, message: str) -> Dict[str, Any]:
        """
        Detect if a message requires a web search.
        
        Args:
            message: User message to analyze
            
        Returns:
            Dict with:
                - needs_search: bool
                - confidence: float (0.0-1.0)
                - suggested_query: str
                - reason: Optional[str]
                - intent_keywords: List[str]
                - topic_keywords: List[str]
        """
        message_lower = message.lower()
        
        matched_intent = self._match_keywords(message_lower, self.intent_keywords)
        matched_topics = self._match_keywords(message_lower, self.topic_keywords)
        
        is_question = self._is_question(message_lower)
        is_explicit_search = self._is_explicit_search(message_lower)
        
        intent_score = len(matched_intent)
        topic_score = len(matched_topics)
        total_score = intent_score * 2 + topic_score + (1 if is_question else 0)
        confidence = min(total_score / 10, 1.0)
        
        needs_search = (
            is_explicit_search or 
            (intent_score >= 1 and topic_score >= 1) or 
            (is_question and intent_score >= 1 and topic_score >= 1)
        )
        
        suggested_query = message
        if matched_topics and not matched_intent:
            suggested_query = f"{message} últimas noticias"
        
        reason = self._build_reason(needs_search, matched_intent, matched_topics)
        
        return {
            "needs_search": needs_search,
            "confidence": confidence,
            "suggested_query": suggested_query,
            "reason": reason,
            "intent_keywords": matched_intent,
            "topic_keywords": matched_topics
        }
    
    def _match_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Find all matching keywords in text"""
        return [kw for kw in keywords if kw in text]
    
    def _is_question(self, text: str) -> bool:
        """Check if text is a question"""
        return any(q in text for q in self.question_markers)
    
    def _is_explicit_search(self, text: str) -> bool:
        """Check if text contains explicit search commands"""
        return any(cmd in text for cmd in self.search_commands)
    
    def _build_reason(
        self, 
        needs_search: bool, 
        intent_keywords: List[str], 
        topic_keywords: List[str]
    ) -> str:
        """Build explanation for the detection result"""
        if not needs_search:
            return ""
        
        if intent_keywords:
            return f"Detected search intent: {', '.join(intent_keywords[:3])}"
        elif topic_keywords:
            return f"Topic requires current info: {', '.join(topic_keywords[:3])}"
        else:
            return "Question format detected"


_intent_detector: IntentDetector = None  # type: ignore[assignment]


def get_intent_detector() -> IntentDetector:
    """Get singleton IntentDetector instance"""
    global _intent_detector
    if _intent_detector is None:
        _intent_detector = IntentDetector()
    return _intent_detector
