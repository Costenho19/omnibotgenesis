"""
OMNIX Multi-Agent System — Risk Agent
ADR-041: Multi-Agent Decision Governance

Evaluates current portfolio risk and translates it into a governance signal:
  - Current drawdown vs max allowed
  - Portfolio exposure level
  - Market regime (from DB / bot state)
  - Black Swan severity (from existing risk systems)

Weight in orchestrator: 0.30 (risk modulates signal conviction)

Signal logic:
  BUY  → Low risk environment, room to enter
  HOLD → Moderate risk, caution warranted
  SELL → High/Extreme risk, reduce exposure
"""
import logging
import asyncio
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from omnix_services.agents.base_agent import BaseAgent
from omnix_services.agents.models import AgentResult, SignalType, RiskLevel, AgentStatus

logger = logging.getLogger(__name__)

MAX_DRAWDOWN_ALLOWED = float(os.environ.get("MAX_DRAWDOWN_PCT", "5.0"))
HIGH_EXPOSURE_PCT    = float(os.environ.get("HIGH_EXPOSURE_PCT", "70.0"))


class RiskAgent(BaseAgent):
    """
    Portfolio risk agent.
    Reads existing OMNIX state from DB to assess current risk environment.
    Never connects to external APIs — uses internal data only.
    """

    name = "RiskAgent"
    timeout = 8.0

    async def _fetch_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()

        db_task    = loop.run_in_executor(None, self._fetch_db_state, symbol)
        redis_task = loop.run_in_executor(None, self._fetch_redis_state, symbol)

        db_data, redis_data = await asyncio.gather(db_task, redis_task, return_exceptions=True)

        return {
            "db":    db_data    if not isinstance(db_data, Exception)    else None,
            "redis": redis_data if not isinstance(redis_data, Exception) else None,
            "db_error":    str(db_data)    if isinstance(db_data, Exception)    else None,
            "redis_error": str(redis_data) if isinstance(redis_data, Exception) else None,
        }

    def _fetch_db_state(self, symbol: str) -> Optional[Dict]:
        try:
            from omnix_services.database_service.gateway import DatabaseGateway
            gw = DatabaseGateway()
            with gw.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            current_balance,
                            initial_balance,
                            total_profit_loss,
                            max_drawdown_pct,
                            open_positions_count,
                            last_regime,
                            last_updated
                        FROM bot_state
                        ORDER BY last_updated DESC
                        LIMIT 1
                    """)
                    row = cur.fetchone()
                    if not row:
                        return None
                    cols = [d[0] for d in cur.description]
                    return dict(zip(cols, row))
        except Exception as e:
            logger.warning(f"[RiskAgent] DB fetch failed: {e}")
            raise

    def _fetch_redis_state(self, symbol: str) -> Optional[Dict]:
        try:
            import redis
            redis_url = os.environ.get("REDIS_URL")
            if not redis_url:
                return None
            r = redis.from_url(redis_url, decode_responses=True, socket_timeout=3)
            keys_to_check = [
                "omnix:risk:black_swan_severity",
                "omnix:risk:current_drawdown",
                "omnix:regime:current",
            ]
            data = {}
            for key in keys_to_check:
                val = r.get(key)
                if val:
                    data[key.split(":")[-1]] = val
            return data if data else None
        except Exception as e:
            logger.warning(f"[RiskAgent] Redis fetch failed: {e}")
            raise

    async def _compute_signal(self, symbol: str, timeframe: str, raw_data: Dict[str, Any]) -> AgentResult:
        db    = raw_data.get("db")
        redis = raw_data.get("redis")

        risk_factors = []
        metadata = {"symbol": symbol, "sources": [], "risk_factors": []}

        if db and isinstance(db, dict):
            db_risk = self._assess_db_risk(db)
            risk_factors.append(db_risk)
            metadata["sources"].append("bot_state_db")
            metadata["db_risk"] = db_risk

        if redis and isinstance(redis, dict):
            redis_risk = self._assess_redis_risk(redis)
            risk_factors.append(redis_risk)
            metadata["sources"].append("redis_state")
            metadata["redis_risk"] = redis_risk

        if not risk_factors:
            return self._make_result(
                SignalType.HOLD, 30.0,
                "No portfolio state available — defaulting to cautious HOLD",
                metadata, AgentStatus.DEGRADED
            )

        avg_risk_score = sum(r["score"] for r in risk_factors) / len(risk_factors)
        risk_level = self._score_to_level(avg_risk_score)
        metadata["avg_risk_score"] = round(avg_risk_score, 2)
        metadata["risk_level"] = risk_level.value

        if risk_level == RiskLevel.LOW:
            signal    = SignalType.BUY
            confidence = 60.0 + (1 - avg_risk_score) * 30
            reasoning  = f"Risk environment LOW ({avg_risk_score:.2f}). Governance permits entry consideration."
        elif risk_level == RiskLevel.MODERATE:
            signal    = SignalType.HOLD
            confidence = 50.0
            reasoning  = f"Risk environment MODERATE ({avg_risk_score:.2f}). Caution warranted."
        elif risk_level == RiskLevel.HIGH:
            signal    = SignalType.SELL
            confidence = 60.0 + avg_risk_score * 20
            reasoning  = f"Risk environment HIGH ({avg_risk_score:.2f}). Reduce exposure."
        else:
            signal    = SignalType.SELL
            confidence = 85.0
            reasoning  = f"Risk environment EXTREME ({avg_risk_score:.2f}). Exit / avoid entry."

        return self._make_result(signal, confidence, reasoning, metadata, AgentStatus.OK)

    def _assess_db_risk(self, db: Dict) -> Dict:
        score = 0.0
        factors = []
        try:
            current  = float(db.get("current_balance", 0) or 0)
            initial  = float(db.get("initial_balance", 0) or 0)
            if initial > 0 and current < initial:
                drawdown_pct = (initial - current) / initial * 100
                dd_score = min(1.0, drawdown_pct / MAX_DRAWDOWN_ALLOWED)
                score += dd_score * 0.5
                factors.append(f"drawdown={drawdown_pct:.1f}%")

            open_pos = int(db.get("open_positions_count", 0) or 0)
            if open_pos > 3:
                pos_score = min(1.0, open_pos / 6)
                score += pos_score * 0.3
                factors.append(f"open_positions={open_pos}")

            regime = str(db.get("last_regime", "") or "")
            if "VOLATILE" in regime.upper():
                score += 0.2
                factors.append(f"regime={regime}")
            elif "TRENDING" in regime.upper():
                score -= 0.1

        except Exception as e:
            logger.warning(f"[RiskAgent] DB risk assess error: {e}")
        return {"score": max(0.0, min(1.0, score)), "factors": factors}

    def _assess_redis_risk(self, redis: Dict) -> Dict:
        score = 0.0
        factors = []
        try:
            severity = str(redis.get("black_swan_severity", "") or "").upper()
            severity_map = {"LOW": 0.1, "MEDIUM": 0.4, "HIGH": 0.7, "EXTREME": 1.0}
            if severity in severity_map:
                score += severity_map[severity] * 0.6
                factors.append(f"black_swan={severity}")

            drawdown = redis.get("current_drawdown")
            if drawdown:
                dd = float(drawdown)
                score += min(1.0, dd / MAX_DRAWDOWN_ALLOWED) * 0.4
                factors.append(f"drawdown={dd:.2f}%")
        except Exception as e:
            logger.warning(f"[RiskAgent] Redis risk assess error: {e}")
        return {"score": max(0.0, min(1.0, score)), "factors": factors}

    def _score_to_level(self, score: float) -> RiskLevel:
        if score < 0.25:
            return RiskLevel.LOW
        elif score < 0.50:
            return RiskLevel.MODERATE
        elif score < 0.75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME
