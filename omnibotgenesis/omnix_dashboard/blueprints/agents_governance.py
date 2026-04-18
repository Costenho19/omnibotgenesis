"""
OMNIX Autonomous Agent Governance API Blueprint
ADR-AGT-001: Autonomous Agent Governance Vertical

REST endpoints for the Autonomous Agent Governance vertical.

Routes:
  GET  /api/agents/metrics        — Summary KPIs
  GET  /api/agents/decisions      — Recent agent decisions with outcomes
  GET  /api/agents/by-type        — Breakdown by decision type
  GET  /api/agents/by-agent       — Breakdown by agent type
  GET  /api/agents/by-environment — Breakdown by environment
  GET  /api/agents/timeline       — Decision trend over time
  GET  /api/agents/live-feed      — Last 10 decisions for live feed
  POST /api/agents/evaluate       — Manual decision evaluation
  GET  /api/agents/health         — Engine health check
"""

from __future__ import annotations

import logging
import os
import uuid

from flask import Blueprint, jsonify, request, g

logger = logging.getLogger("OMNIX.Agents.API")

agents_bp = Blueprint("agents", __name__, url_prefix="/api/agents")


def _get_db():
    import psycopg2
    if "db" not in g:
        g.db = psycopg2.connect(os.environ["DATABASE_URL"])
    return g.db


def _query(sql: str, params=None) -> list[dict]:
    conn = _get_db()
    from psycopg2.extras import RealDictCursor
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def _queryOne(sql: str, params=None) -> dict | None:
    rows = _query(sql, params)
    return rows[0] if rows else None


@agents_bp.route("/metrics")
@agents_bp.route("/metrics.json")
def get_metrics():
    try:
        totals = _queryOne("""
            SELECT
                COUNT(*) AS total_decisions,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                COUNT(*) FILTER (WHERE decision='HOLD') AS held,
                COALESCE(AVG(task_complexity), 0) AS avg_task_complexity,
                COALESCE(AVG(scope_blast_radius), 0) AS avg_scope_risk,
                COALESCE(AVG(decision_score), 0) AS avg_decision_score,
                COALESCE(AVG(trajectory_score), 0) AS avg_trajectory_score,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') AS decisions_24h,
                COUNT(DISTINCT agent_id) AS active_agents,
                COUNT(*) FILTER (WHERE decision='BLOCKED' AND (safety_critical_flag=TRUE OR (human_approval_required=TRUE AND human_approved=FALSE))) AS safety_blocks
            FROM agent_decisions
        """)

        cycles = _queryOne("SELECT COUNT(*) AS total_cycles FROM agent_cycle_metrics")

        if not totals:
            return jsonify({"success": False, "error": "No data yet"}), 404

        total = int(totals.get("total_decisions", 0)) or 1
        approved = int(totals.get("approved", 0))
        blocked = int(totals.get("blocked", 0))

        return jsonify({
            "success": True,
            "metrics": {
                "total_decisions": total,
                "decisions_approved": approved,
                "decisions_blocked": blocked,
                "decisions_held": int(totals.get("held", 0)),
                "approval_rate": round(approved / total, 4),
                "block_rate": round(blocked / total, 4),
                "avg_task_complexity": round(float(totals.get("avg_task_complexity", 0)), 2),
                "avg_scope_risk": round(float(totals.get("avg_scope_risk", 0)), 2),
                "avg_decision_score": round(float(totals.get("avg_decision_score", 0)), 2),
                "avg_trajectory_score": round(float(totals.get("avg_trajectory_score", 0)), 2),
                "decisions_last_24h": int(totals.get("decisions_24h", 0)),
                "active_agents": int(totals.get("active_agents", 0)),
                "safety_blocks": int(totals.get("safety_blocks", 0)),
                "simulation_cycles": int((cycles or {}).get("total_cycles", 0)),
            }
        })
    except Exception as e:
        logger.error(f"get_metrics error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/decisions")
def get_decisions():
    try:
        limit = min(int(request.args.get("limit", 30)), 100)
        rows = _query("""
            SELECT decision_id, agent_id, agent_type, decision_type,
                   environment, reversibility, data_sensitivity,
                   task_complexity, resource_utilization, context_completeness,
                   goal_alignment, dependency_score, scope_blast_radius,
                   fallback_coverage, permission_scope,
                   safety_critical_flag, human_approval_required, human_approved,
                   cross_boundary, retry_count,
                   decision, decision_score, block_reason, receipt_id,
                   probability_score, risk_exposure, signal_coherence,
                   trend_persistence, stress_resilience, logic_consistency,
                   trajectory_score, created_at
            FROM agent_decisions
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return jsonify({"success": True, "decisions": rows})
    except Exception as e:
        logger.error(f"get_decisions error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/live-feed")
def get_live_feed():
    try:
        rows = _query("""
            SELECT decision_id, agent_type, decision_type, environment,
                   reversibility, data_sensitivity, task_complexity,
                   scope_blast_radius, decision, decision_score,
                   block_reason, receipt_id, trajectory_score, created_at
            FROM agent_decisions
            ORDER BY created_at DESC
            LIMIT 10
        """)
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return jsonify({"success": True, "decisions": rows})
    except Exception as e:
        logger.error(f"get_live_feed error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/by-type")
def get_by_type():
    try:
        rows = _query("""
            SELECT
                decision_type,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                ROUND(AVG(task_complexity)::numeric, 2) AS avg_complexity,
                ROUND(AVG(scope_blast_radius)::numeric, 2) AS avg_scope_risk,
                ROUND(COUNT(*) FILTER (WHERE decision='APPROVED')::numeric / NULLIF(COUNT(*),0), 4) AS approval_rate
            FROM agent_decisions
            GROUP BY decision_type
            ORDER BY total DESC
        """)
        return jsonify({"success": True, "by_type": rows})
    except Exception as e:
        logger.error(f"get_by_type error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/by-agent")
def get_by_agent():
    try:
        rows = _query("""
            SELECT
                agent_type,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                ROUND(AVG(task_complexity)::numeric, 2) AS avg_complexity,
                ROUND(AVG(decision_score)::numeric, 2) AS avg_decision_score,
                COUNT(DISTINCT agent_id) AS agent_count,
                ROUND(COUNT(*) FILTER (WHERE decision='APPROVED')::numeric / NULLIF(COUNT(*),0), 4) AS approval_rate
            FROM agent_decisions
            GROUP BY agent_type
            ORDER BY total DESC
        """)
        return jsonify({"success": True, "by_agent": rows})
    except Exception as e:
        logger.error(f"get_by_agent error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/by-environment")
def get_by_environment():
    try:
        rows = _query("""
            SELECT
                environment,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                ROUND(AVG(scope_blast_radius)::numeric, 2) AS avg_scope_risk,
                ROUND(AVG(decision_score)::numeric, 2) AS avg_score,
                ROUND(COUNT(*) FILTER (WHERE decision='APPROVED')::numeric / NULLIF(COUNT(*),0), 4) AS approval_rate
            FROM agent_decisions
            GROUP BY environment
            ORDER BY CASE environment WHEN 'production' THEN 1 WHEN 'staging' THEN 2 WHEN 'development' THEN 3 ELSE 4 END
        """)
        return jsonify({"success": True, "by_environment": rows})
    except Exception as e:
        logger.error(f"get_by_environment error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/timeline")
def get_timeline():
    try:
        rows = _query("""
            SELECT
                DATE_TRUNC('hour', created_at) AS hour,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                ROUND(AVG(decision_score)::numeric, 2) AS avg_score
            FROM agent_decisions
            WHERE created_at > NOW() - INTERVAL '48 hours'
            GROUP BY DATE_TRUNC('hour', created_at)
            ORDER BY hour ASC
        """)
        for r in rows:
            if r.get("hour"):
                r["hour"] = r["hour"].isoformat()
        return jsonify({"success": True, "timeline": rows})
    except Exception as e:
        logger.error(f"get_timeline error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/evaluate", methods=["POST"])
def manual_evaluate():
    try:
        from omnix_core.agents.agents_signal_adapter import (
            AgentDecisionInput, AgentSignalAdapter
        )
        data = request.get_json(force=True)
        decision_input = AgentDecisionInput(
            agent_type=data.get("agent_type", "Enterprise_Agent"),
            decision_type=data.get("decision_type", "task_delegation"),
            environment=data.get("environment", "production"),
            reversibility=data.get("reversibility", "partially_reversible"),
            task_complexity=float(data.get("task_complexity", 45)),
            resource_utilization=float(data.get("resource_utilization", 50)),
            context_completeness=float(data.get("context_completeness", 80)),
            goal_alignment=float(data.get("goal_alignment", 80)),
            dependency_score=float(data.get("dependency_score", 40)),
            scope_blast_radius=float(data.get("scope_blast_radius", 35)),
            fallback_coverage=float(data.get("fallback_coverage", 70)),
            permission_scope=float(data.get("permission_scope", 45)),
            safety_critical_flag=bool(data.get("safety_critical_flag", False)),
            human_approval_required=bool(data.get("human_approval_required", False)),
            human_approved=bool(data.get("human_approved", False)),
            cross_boundary=bool(data.get("cross_boundary", False)),
            data_sensitivity=data.get("data_sensitivity", "low"),
            retry_count=int(data.get("retry_count", 0)),
        )
        adapter = AgentSignalAdapter()
        signals = adapter.adapt(decision_input)
        return jsonify({"success": True, "signals": signals.to_omnix_dict(),
                        "recommendation": signals.recommendation})
    except Exception as e:
        logger.error(f"manual_evaluate error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/health")
def health():
    try:
        count = _queryOne("SELECT COUNT(*) AS cnt FROM agent_decisions")
        return jsonify({
            "success": True,
            "status": "operational",
            "total_decisions": int((count or {}).get("cnt", 0)),
            "domain": "autonomous_agents",
            "receipt_prefix": "OMNIX-AGT"
        })
    except Exception as e:
        return jsonify({"success": False, "status": "degraded", "error": str(e)}), 500
