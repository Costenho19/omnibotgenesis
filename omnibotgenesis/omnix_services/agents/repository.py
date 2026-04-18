"""
OMNIX Multi-Agent System — Agent Repository
ADR-041: Multi-Agent Decision Governance

Persists OrchestratorResult runs to the agent_orchestrator_runs table
for audit trails, traceability, and future calibration analysis.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from omnix_services.agents.models import OrchestratorResult

logger = logging.getLogger(__name__)


class AgentRepository:
    """
    Persists agent orchestrator runs to PostgreSQL.
    Fails silently — persistence issues must NOT block the governance pipeline.
    """

    TABLE = "agent_orchestrator_runs"

    def save(self, result: OrchestratorResult, decision_id: Optional[str] = None) -> Optional[int]:
        """
        Persist an OrchestratorResult. Returns the new row ID or None on failure.
        """
        try:
            from omnix_services.database_service.gateway import DatabaseGateway
            gw = DatabaseGateway()
            with gw.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        INSERT INTO {self.TABLE} (
                            symbol, timeframe,
                            consensus_signal, consensus_score, consensus_confidence,
                            component_results, degraded_flags, latency_ms,
                            requires_stronger_core_signal, decision_id,
                            created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        result.symbol,
                        result.timeframe,
                        result.consensus_signal.value,
                        result.consensus_score,
                        result.consensus_confidence,
                        json.dumps({k: v.to_dict() for k, v in result.component_results.items()}),
                        json.dumps(result.degraded_flags),
                        result.latency_ms,
                        result.requires_stronger_core_signal,
                        decision_id,
                        datetime.now(timezone.utc),
                    ))
                    row = cur.fetchone()
                    conn.commit()
                    return row[0] if row else None
        except Exception as e:
            logger.warning(f"[AgentRepository] Failed to persist run: {e}")
            return None

    def get_recent(self, symbol: str, limit: int = 10) -> list:
        """Retrieve recent orchestrator runs for a symbol."""
        try:
            from omnix_services.database_service.gateway import DatabaseGateway
            gw = DatabaseGateway()
            with gw.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        SELECT id, symbol, consensus_signal, consensus_score,
                               consensus_confidence, latency_ms, created_at
                        FROM {self.TABLE}
                        WHERE symbol = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (symbol, limit))
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description]
                    return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            logger.warning(f"[AgentRepository] Failed to fetch recent runs: {e}")
            return []
