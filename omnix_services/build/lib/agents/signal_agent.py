"""
OMNIX Multi-Agent System — Signal Agent
ADR-041: Multi-Agent Decision Governance

Generates a technical BUY/HOLD/SELL signal using:
  - Kraken OHLC data (price momentum, EMA cross)
  - Alpha Vantage RSI + MACD (external confirmation)

Weight in orchestrator: 0.45 (dominant — technical data is most direct)
"""
import logging
import asyncio
from typing import Dict, Any, List

from omnix_services.agents.base_agent import BaseAgent
from omnix_services.agents.models import AgentResult, SignalType, AgentStatus

logger = logging.getLogger(__name__)


class SignalAgent(BaseAgent):
    """
    Technical signal agent.
    BUY  → price momentum positive + RSI not overbought + MACD bullish
    SELL → price momentum negative + RSI not oversold  + MACD bearish
    HOLD → mixed or insufficient data
    """

    name = "SignalAgent"
    timeout = 12.0

    async def _fetch_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()

        kraken_task = loop.run_in_executor(None, self._fetch_kraken, symbol)
        av_task     = loop.run_in_executor(None, self._fetch_alpha_vantage, symbol)

        kraken_data, av_data = await asyncio.gather(kraken_task, av_task, return_exceptions=True)

        return {
            "kraken": kraken_data if not isinstance(kraken_data, Exception) else None,
            "alpha_vantage": av_data if not isinstance(av_data, Exception) else None,
            "kraken_error": str(kraken_data) if isinstance(kraken_data, Exception) else None,
            "av_error":     str(av_data)     if isinstance(av_data, Exception) else None,
        }

    def _fetch_kraken(self, symbol: str):
        try:
            from omnix_services.market_data.kraken_data import get_ohlc_daily
            ohlc = get_ohlc_daily(symbol, days=10)
            return ohlc
        except Exception as e:
            logger.warning(f"[SignalAgent] Kraken fetch failed: {e}")
            raise

    def _fetch_alpha_vantage(self, symbol: str):
        try:
            from omnix_services.market_intelligence.alpha_vantage_service import AlphaVantageService
            svc = AlphaVantageService()
            if not svc.is_available():
                return None
            rsi  = svc.get_rsi(symbol)
            macd = svc.get_macd(symbol) if hasattr(svc, "get_macd") else None
            return {"rsi": rsi, "macd": macd}
        except Exception as e:
            logger.warning(f"[SignalAgent] Alpha Vantage fetch failed: {e}")
            raise

    async def _compute_signal(self, symbol: str, timeframe: str, raw_data: Dict[str, Any]) -> AgentResult:
        kraken = raw_data.get("kraken")
        av     = raw_data.get("alpha_vantage")

        signals = []
        confidence_factors = []
        metadata = {"symbol": symbol, "sources": []}

        if kraken and isinstance(kraken, list) and len(kraken) >= 3:
            momentum = self._compute_momentum(kraken)
            signals.append(momentum["signal"])
            confidence_factors.append(momentum["strength"])
            metadata["sources"].append("kraken_ohlc")
            metadata["price_momentum"] = momentum

        if av and isinstance(av, dict):
            rsi_data = av.get("rsi")
            if rsi_data and isinstance(rsi_data, dict):
                rsi_signal = self._interpret_rsi(rsi_data)
                signals.append(rsi_signal["signal"])
                confidence_factors.append(rsi_signal["strength"])
                metadata["sources"].append("alpha_vantage_rsi")
                metadata["rsi"] = rsi_signal

        if not signals:
            return self._make_result(
                SignalType.HOLD, 0.0,
                "No data available from Kraken or Alpha Vantage",
                metadata, AgentStatus.DEGRADED
            )

        buy_count  = signals.count(SignalType.BUY)
        sell_count = signals.count(SignalType.SELL)
        avg_conf   = (sum(confidence_factors) / len(confidence_factors)) * 100 if confidence_factors else 0

        if buy_count > sell_count:
            signal = SignalType.BUY
            reasoning = f"Technical: {buy_count}/{len(signals)} indicators bullish. Avg strength: {avg_conf:.0f}%"
        elif sell_count > buy_count:
            signal = SignalType.SELL
            reasoning = f"Technical: {sell_count}/{len(signals)} indicators bearish. Avg strength: {avg_conf:.0f}%"
        else:
            signal = SignalType.HOLD
            avg_conf *= 0.5
            reasoning = f"Technical: Mixed signals ({buy_count} bullish, {sell_count} bearish). Holding."

        status = AgentStatus.OK if len(metadata["sources"]) >= 2 else AgentStatus.DEGRADED
        return self._make_result(signal, avg_conf, reasoning, metadata, status)

    def _compute_momentum(self, ohlc: List) -> Dict[str, Any]:
        try:
            closes = []
            for candle in ohlc[-10:]:
                if isinstance(candle, (list, tuple)) and len(candle) >= 5:
                    closes.append(float(candle[4]))
                elif isinstance(candle, dict):
                    closes.append(float(candle.get("close", candle.get("c", 0))))

            if len(closes) < 3:
                return {"signal": SignalType.HOLD, "strength": 0.0}

            recent   = sum(closes[-3:]) / 3
            previous = sum(closes[-6:-3]) / 3 if len(closes) >= 6 else closes[0]
            change_pct = (recent - previous) / previous * 100 if previous else 0

            if change_pct > 1.0:
                return {"signal": SignalType.BUY,  "strength": min(1.0, change_pct / 5.0), "change_pct": change_pct}
            elif change_pct < -1.0:
                return {"signal": SignalType.SELL, "strength": min(1.0, abs(change_pct) / 5.0), "change_pct": change_pct}
            else:
                return {"signal": SignalType.HOLD, "strength": 0.3, "change_pct": change_pct}
        except Exception as e:
            logger.warning(f"[SignalAgent] Momentum compute error: {e}")
            return {"signal": SignalType.HOLD, "strength": 0.0}

    def _interpret_rsi(self, rsi_data: Dict) -> Dict[str, Any]:
        try:
            rsi_val = None
            if isinstance(rsi_data, dict):
                rsi_val = rsi_data.get("value") or rsi_data.get("rsi") or rsi_data.get("RSI")
            if rsi_val is None:
                return {"signal": SignalType.HOLD, "strength": 0.0}
            rsi = float(rsi_val)
            if rsi < 35:
                return {"signal": SignalType.BUY,  "strength": (35 - rsi) / 35, "rsi": rsi}
            elif rsi > 65:
                return {"signal": SignalType.SELL, "strength": (rsi - 65) / 35, "rsi": rsi}
            else:
                return {"signal": SignalType.HOLD, "strength": 0.3, "rsi": rsi}
        except Exception as e:
            logger.warning(f"[SignalAgent] RSI interpret error: {e}")
            return {"signal": SignalType.HOLD, "strength": 0.0}
