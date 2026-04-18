"""
OMNIX Multi-Agent System — Base Agent
ADR-041: Multi-Agent Decision Governance

Abstract base class for all OMNIX governance agents.
Each concrete agent must implement: _fetch_data() and _compute_signal().
"""
import logging
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from omnix_services.agents.models import AgentResult, SignalType, AgentStatus

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 10


class BaseAgent(ABC):
    """
    Abstract base for all OMNIX agents.

    Lifecycle per run():
      1. _fetch_data()   — retrieve raw data from APIs (can raise)
      2. _compute_signal() — derive signal + confidence from raw data
      3. Wrap result in AgentResult with graceful fallback on any exception
    """

    name: str = "BaseAgent"
    timeout: float = DEFAULT_TIMEOUT_SECONDS

    async def run(self, symbol: str, timeframe: str = "1h") -> AgentResult:
        """
        Execute the agent. Always returns an AgentResult — never raises.
        On failure returns HOLD with confidence=0 and status=FAILED.
        """
        try:
            result = await asyncio.wait_for(
                self._execute(symbol, timeframe),
                timeout=self.timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(f"[{self.name}] Timeout after {self.timeout}s for {symbol}")
            return self._fallback(symbol, reason=f"Timeout after {self.timeout}s")
        except Exception as exc:
            logger.error(f"[{self.name}] Unexpected error for {symbol}: {exc}", exc_info=True)
            return self._fallback(symbol, reason=str(exc))

    async def _execute(self, symbol: str, timeframe: str) -> AgentResult:
        raw_data = await self._fetch_data(symbol, timeframe)
        return await self._compute_signal(symbol, timeframe, raw_data)

    @abstractmethod
    async def _fetch_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Fetch raw data from external APIs. May raise on failure."""

    @abstractmethod
    async def _compute_signal(self, symbol: str, timeframe: str, raw_data: Dict[str, Any]) -> AgentResult:
        """Derive BUY/HOLD/SELL signal + confidence from raw data."""

    def get_health(self) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "status": "healthy",
            "timeout_s": self.timeout,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _fallback(self, symbol: str, reason: str = "Unknown error") -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            signal=SignalType.HOLD,
            confidence=0.0,
            reasoning=f"[FALLBACK] {reason}",
            status=AgentStatus.FAILED,
            metadata={"symbol": symbol, "fallback_reason": reason},
        )

    def _make_result(
        self,
        signal: SignalType,
        confidence: float,
        reasoning: str,
        metadata: Optional[Dict[str, Any]] = None,
        status: AgentStatus = AgentStatus.OK,
    ) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            signal=signal,
            confidence=max(0.0, min(100.0, confidence)),
            reasoning=reasoning,
            status=status,
            metadata=metadata or {},
        )
