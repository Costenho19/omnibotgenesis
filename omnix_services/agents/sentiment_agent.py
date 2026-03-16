"""
OMNIX Multi-Agent System — Sentiment Agent
ADR-041: Multi-Agent Decision Governance

Generates a sentiment-based BUY/HOLD/SELL signal using:
  - Finnhub news sentiment
  - Tavily real-time web search
  - Fear & Greed Index (Alternative.me)

Weight in orchestrator: 0.25 (contextual confirmation layer)
"""
import logging
import asyncio
from typing import Dict, Any

from omnix_services.agents.base_agent import BaseAgent
from omnix_services.agents.models import AgentResult, SignalType, AgentStatus

logger = logging.getLogger(__name__)


class SentimentAgent(BaseAgent):
    """
    Sentiment signal agent.
    Aggregates Fear/Greed + news sentiment + web search context.
    BUY  → low fear + positive news sentiment
    SELL → extreme greed + negative news sentiment
    HOLD → neutral or conflicting sentiment signals
    """

    name = "SentimentAgent"
    timeout = 15.0

    async def _fetch_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()

        fg_task      = loop.run_in_executor(None, self._fetch_fear_greed)
        finnhub_task = loop.run_in_executor(None, self._fetch_finnhub, symbol)
        tavily_task  = loop.run_in_executor(None, self._fetch_tavily, symbol)

        fg, finnhub, tavily = await asyncio.gather(
            fg_task, finnhub_task, tavily_task,
            return_exceptions=True
        )

        return {
            "fear_greed": fg      if not isinstance(fg, Exception)      else None,
            "finnhub":    finnhub if not isinstance(finnhub, Exception)  else None,
            "tavily":     tavily  if not isinstance(tavily, Exception)   else None,
            "fg_error":      str(fg)      if isinstance(fg, Exception)      else None,
            "finnhub_error": str(finnhub) if isinstance(finnhub, Exception) else None,
            "tavily_error":  str(tavily)  if isinstance(tavily, Exception)  else None,
        }

    def _fetch_fear_greed(self):
        try:
            from omnix_services.market_intelligence.fear_greed_service import FearGreedService
            svc = FearGreedService()
            return svc.get_index()
        except Exception as e:
            logger.warning(f"[SentimentAgent] Fear&Greed fetch failed: {e}")
            raise

    def _fetch_finnhub(self, symbol: str):
        try:
            from omnix_services.market_intelligence.finnhub_service import FinnhubService
            svc = FinnhubService()
            if not svc.is_available():
                return None
            news = svc.get_company_news(symbol, days=3)
            return news
        except Exception as e:
            logger.warning(f"[SentimentAgent] Finnhub fetch failed: {e}")
            raise

    def _fetch_tavily(self, symbol: str):
        try:
            from omnix_services.web_search_service.tavily_search import TavilySearchClient
            client = TavilySearchClient()
            query = f"{symbol} cryptocurrency market sentiment today"
            result = client.search(query, max_results=3)
            return result
        except Exception as e:
            logger.warning(f"[SentimentAgent] Tavily fetch failed: {e}")
            raise

    async def _compute_signal(self, symbol: str, timeframe: str, raw_data: Dict[str, Any]) -> AgentResult:
        signals = []
        confidence_factors = []
        metadata = {"symbol": symbol, "sources": []}

        fg = raw_data.get("fear_greed")
        if fg:
            fg_signal = self._interpret_fear_greed(fg)
            signals.append(fg_signal["signal"])
            confidence_factors.append(fg_signal["strength"])
            metadata["sources"].append("fear_greed")
            metadata["fear_greed"] = fg_signal

        finnhub = raw_data.get("finnhub")
        if finnhub and isinstance(finnhub, list) and len(finnhub) > 0:
            news_signal = self._interpret_news(finnhub)
            signals.append(news_signal["signal"])
            confidence_factors.append(news_signal["strength"])
            metadata["sources"].append("finnhub_news")
            metadata["news_sentiment"] = news_signal

        tavily = raw_data.get("tavily")
        if tavily:
            web_signal = self._interpret_web_search(tavily)
            if web_signal["signal"] != SignalType.UNKNOWN:
                signals.append(web_signal["signal"])
                confidence_factors.append(web_signal["strength"])
                metadata["sources"].append("tavily_search")
                metadata["web_context"] = web_signal

        if not signals:
            return self._make_result(
                SignalType.HOLD, 0.0,
                "No sentiment data available from any source",
                metadata, AgentStatus.DEGRADED
            )

        buy_count  = signals.count(SignalType.BUY)
        sell_count = signals.count(SignalType.SELL)
        avg_conf   = (sum(confidence_factors) / len(confidence_factors)) * 100 if confidence_factors else 0

        if buy_count > sell_count:
            signal    = SignalType.BUY
            reasoning = f"Sentiment: {buy_count}/{len(signals)} sources positive. Confidence: {avg_conf:.0f}%"
        elif sell_count > buy_count:
            signal    = SignalType.SELL
            reasoning = f"Sentiment: {sell_count}/{len(signals)} sources negative. Confidence: {avg_conf:.0f}%"
        else:
            signal    = SignalType.HOLD
            avg_conf *= 0.5
            reasoning = f"Sentiment: Mixed ({buy_count} positive, {sell_count} negative). Holding."

        status = AgentStatus.OK if len(metadata["sources"]) >= 2 else AgentStatus.DEGRADED
        return self._make_result(signal, avg_conf, reasoning, metadata, status)

    def _interpret_fear_greed(self, fg_data: Any) -> Dict:
        try:
            value = None
            if isinstance(fg_data, dict):
                value = fg_data.get("value") or fg_data.get("index")
                if value is None and "data" in fg_data:
                    data = fg_data["data"]
                    if isinstance(data, list) and data:
                        value = data[0].get("value")
            if value is None:
                return {"signal": SignalType.HOLD, "strength": 0.0}
            idx = int(value)
            metadata = {"fg_index": idx}
            if idx < 25:
                return {"signal": SignalType.BUY,  "strength": (25 - idx) / 25, **metadata}
            elif idx > 75:
                return {"signal": SignalType.SELL, "strength": (idx - 75) / 25, **metadata}
            elif idx < 40:
                return {"signal": SignalType.BUY,  "strength": (40 - idx) / 40 * 0.5, **metadata}
            elif idx > 60:
                return {"signal": SignalType.SELL, "strength": (idx - 60) / 40 * 0.5, **metadata}
            else:
                return {"signal": SignalType.HOLD, "strength": 0.3, **metadata}
        except Exception as e:
            logger.warning(f"[SentimentAgent] FG interpret error: {e}")
            return {"signal": SignalType.HOLD, "strength": 0.0}

    def _interpret_news(self, news: list) -> Dict:
        try:
            positive_keywords = ["surge", "rally", "gain", "bullish", "rise", "up", "high", "breakout", "adoption"]
            negative_keywords = ["crash", "drop", "fall", "bearish", "down", "low", "ban", "hack", "fraud", "collapse"]
            pos_score = 0
            neg_score = 0
            for article in news[:10]:
                headline = (article.get("headline", "") + " " + article.get("summary", "")).lower()
                pos_score += sum(1 for kw in positive_keywords if kw in headline)
                neg_score += sum(1 for kw in negative_keywords if kw in headline)
            total = pos_score + neg_score
            if total == 0:
                return {"signal": SignalType.HOLD, "strength": 0.2, "pos": 0, "neg": 0}
            if pos_score > neg_score:
                return {"signal": SignalType.BUY,  "strength": pos_score / (total * 2), "pos": pos_score, "neg": neg_score}
            elif neg_score > pos_score:
                return {"signal": SignalType.SELL, "strength": neg_score / (total * 2), "pos": pos_score, "neg": neg_score}
            else:
                return {"signal": SignalType.HOLD, "strength": 0.2, "pos": pos_score, "neg": neg_score}
        except Exception as e:
            logger.warning(f"[SentimentAgent] News interpret error: {e}")
            return {"signal": SignalType.HOLD, "strength": 0.0}

    def _interpret_web_search(self, tavily_result: Any) -> Dict:
        try:
            if not tavily_result:
                return {"signal": SignalType.UNKNOWN, "strength": 0.0}
            content = ""
            if isinstance(tavily_result, dict):
                content = tavily_result.get("answer", "") or " ".join(
                    r.get("content", "") for r in tavily_result.get("results", [])
                )
            elif isinstance(tavily_result, str):
                content = tavily_result
            content = content.lower()
            bull_terms = ["bullish", "upward", "positive", "growth", "buy"]
            bear_terms = ["bearish", "downward", "negative", "decline", "sell", "crash"]
            bull_hits = sum(1 for t in bull_terms if t in content)
            bear_hits = sum(1 for t in bear_terms if t in content)
            if bull_hits > bear_hits:
                return {"signal": SignalType.BUY,  "strength": 0.4, "bull_hits": bull_hits, "bear_hits": bear_hits}
            elif bear_hits > bull_hits:
                return {"signal": SignalType.SELL, "strength": 0.4, "bull_hits": bull_hits, "bear_hits": bear_hits}
            return {"signal": SignalType.HOLD, "strength": 0.2}
        except Exception as e:
            logger.warning(f"[SentimentAgent] Web interpret error: {e}")
            return {"signal": SignalType.UNKNOWN, "strength": 0.0}
