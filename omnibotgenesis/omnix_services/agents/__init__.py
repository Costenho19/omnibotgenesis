"""
OMNIX Multi-Agent System
ADR-041: Multi-Agent Decision Governance

Agents propose. OMNIX governs.

Usage:
    from omnix_services.agents import AgentOrchestrator
    import asyncio

    orchestrator = AgentOrchestrator()
    result = asyncio.run(orchestrator.run(symbol="BTC", timeframe="1h"))
    print(result.consensus_signal, result.consensus_score)
"""
from omnix_services.agents.orchestrator import AgentOrchestrator
from omnix_services.agents.models import (
    AgentResult, OrchestratorResult, SignalType, RiskLevel, AgentStatus
)
from omnix_services.agents.signal_agent    import SignalAgent
from omnix_services.agents.sentiment_agent import SentimentAgent
from omnix_services.agents.risk_agent      import RiskAgent
from omnix_services.agents.repository      import AgentRepository

__all__ = [
    "AgentOrchestrator",
    "AgentResult",
    "OrchestratorResult",
    "SignalType",
    "RiskLevel",
    "AgentStatus",
    "SignalAgent",
    "SentimentAgent",
    "RiskAgent",
    "AgentRepository",
]
