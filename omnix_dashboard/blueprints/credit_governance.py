"""
OMNIX Credit Governance API Blueprint
ADR-052: Islamic Credit Governance Vertical

REST endpoints for the Islamic Credit Governance vertical.
Provides metrics, application history, and manual evaluation for the dashboard.

Routes:
  GET  /api/credit/metrics          — Summary metrics + KPIs
  GET  /api/credit/applications     — Recent applications with decisions
  GET  /api/credit/sectors          — Breakdown by sector
  GET  /api/credit/timeline         — Approval/block counts over time
  POST /api/credit/evaluate         — Manual application evaluation
  GET  /api/credit/macro            — Current macro conditions
  GET  /api/credit/health           — Engine health check
"""

from __future__ import annotations

import logging
import os
import time
from functools import wraps

from flask import Blueprint, jsonify, request, g

logger = logging.getLogger("OMNIX.Credit.API")

credit_bp = Blueprint("credit", __name__, url_prefix="/api/credit")


def _get_db():
    """Get database connection from Flask app context."""
    import psycopg2
    import psycopg2.extras
    if "db" not in g:
        g.db = psycopg2.connect(os.environ["DATABASE_URL"])
    return g.db


def _query(sql: str, params=None) -> list[dict]:
    """Execute a SELECT query and return list of dicts."""
    conn = _get_db()
    with conn.cursor(cursor_factory=__import__("psycopg2.extras", fromlist=["RealDictCursor"]).RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def _queryOne(sql: str, params=None) -> dict | None:
    rows = _query(sql, params)
    return rows[0] if rows else None


# ──────────────────────────────────────────────────────────────────────────────
# Metrics Endpoint
# ──────────────────────────────────────────────────────────────────────────────

@credit_bp.route("/metrics")
def get_metrics():
    """
    Returns comprehensive KPI metrics for the Credit Governance vertical.
    Used by the dashboard and investor presentations.
    """
    try:
        # Total counts
        totals = _queryOne("""
            SELECT
                COUNT(*) as total_applications,
                COUNT(*) FILTER (WHERE decision = 'APPROVED') as total_approved,
                COUNT(*) FILTER (WHERE decision = 'BLOCKED') as total_blocked,
                COUNT(*) FILTER (WHERE decision = 'HOLD') as total_hold,
                ROUND(AVG(CASE WHEN decision = 'APPROVED' THEN 1.0 ELSE 0.0 END) * 100, 2)
                    as approval_rate,
                ROUND(SUM(requested_amount), 2) as total_amount_evaluated,
                ROUND(SUM(CASE WHEN decision = 'APPROVED' THEN requested_amount ELSE 0 END), 2)
                    as total_amount_approved,
                ROUND(SUM(CASE WHEN decision = 'BLOCKED' THEN requested_amount ELSE 0 END), 2)
                    as total_amount_blocked,
                ROUND(AVG(signal_probability_score), 2) as avg_probability_score,
                ROUND(AVG(signal_risk_exposure), 2) as avg_risk_exposure,
                COUNT(*) FILTER (WHERE sharia_compliant = FALSE) as sharia_violations,
                ROUND(AVG(CASE WHEN sharia_compliant = TRUE THEN 1.0 ELSE 0.0 END) * 100, 2)
                    as sharia_compliance_rate,
                MIN(submitted_at) as first_evaluation,
                MAX(submitted_at) as last_evaluation
            FROM credit_applications
        """)

        # Capital protected (blocked × estimated default rate)
        capital = _queryOne("""
            SELECT
                ROUND(SUM(requested_amount * (signal_risk_exposure / 200.0)), 2)
                    as capital_protected_estimate
            FROM credit_applications
            WHERE decision = 'BLOCKED'
        """)

        # Top blocked reasons
        block_reasons = _query("""
            SELECT
                COALESCE(blocked_at_checkpoint, 'CP-?') as checkpoint,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / NULLIF(
                    (SELECT COUNT(*) FROM credit_applications WHERE decision = 'BLOCKED'), 0
                ), 1) as pct
            FROM credit_applications
            WHERE decision = 'BLOCKED'
            GROUP BY blocked_at_checkpoint
            ORDER BY count DESC
            LIMIT 5
        """)

        # Last 24h activity
        activity_24h = _queryOne("""
            SELECT
                COUNT(*) as applications_24h,
                COUNT(*) FILTER (WHERE decision = 'APPROVED') as approved_24h,
                COUNT(*) FILTER (WHERE decision = 'BLOCKED') as blocked_24h
            FROM credit_applications
            WHERE submitted_at >= NOW() - INTERVAL '24 hours'
        """)

        # Latest macro snapshot
        macro_row = _queryOne("""
            SELECT macro_credit_index, macro_stress_level, fed_funds_rate, macro_volatility
            FROM credit_applications
            WHERE macro_credit_index IS NOT NULL
            ORDER BY submitted_at DESC
            LIMIT 1
        """)

        # Cycle count
        cycle_row = _queryOne("SELECT COUNT(*) as cycles FROM credit_cycle_metrics")

        t = totals or {}
        c = capital or {}
        a = activity_24h or {}

        return jsonify({
            "status": "ok",
            "vertical": "islamic_credit",
            "engine_version": "1.0.0",
            "metrics": {
                "total_applications": int(t.get("total_applications") or 0),
                "total_approved": int(t.get("total_approved") or 0),
                "total_blocked": int(t.get("total_blocked") or 0),
                "total_hold": int(t.get("total_hold") or 0),
                "approval_rate": float(t.get("approval_rate") or 0),
                "total_amount_evaluated_aed": float(t.get("total_amount_evaluated") or 0),
                "total_amount_approved_aed": float(t.get("total_amount_approved") or 0),
                "total_amount_blocked_aed": float(t.get("total_amount_blocked") or 0),
                "capital_protected_estimate_aed": float(c.get("capital_protected_estimate") or 0),
                "avg_probability_score": float(t.get("avg_probability_score") or 0),
                "avg_risk_exposure": float(t.get("avg_risk_exposure") or 0),
                "sharia_compliance_rate": float(t.get("sharia_compliance_rate") or 100),
                "sharia_violations": int(t.get("sharia_violations") or 0),
                "simulation_cycles": int(cycle_row.get("cycles") or 0) if cycle_row else 0,
                "first_evaluation": str(t.get("first_evaluation") or ""),
                "last_evaluation": str(t.get("last_evaluation") or ""),
            },
            "activity_24h": {
                "applications": int(a.get("applications_24h") or 0),
                "approved": int(a.get("approved_24h") or 0),
                "blocked": int(a.get("blocked_24h") or 0),
            },
            "top_block_reasons": block_reasons,
            "macro": {
                "credit_index": float((macro_row or {}).get("macro_credit_index") or 58),
                "stress_level": str((macro_row or {}).get("macro_stress_level") or "MODERATE"),
                "fed_funds_rate": float((macro_row or {}).get("fed_funds_rate") or 5.33),
                "volatility": float((macro_row or {}).get("macro_volatility") or 38),
            },
        })

    except Exception as e:
        logger.error(f"[CreditAPI] metrics error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────────
# Applications Feed
# ──────────────────────────────────────────────────────────────────────────────

@credit_bp.route("/applications")
def get_applications():
    """Recent credit applications with governance decisions."""
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
        decision_filter = request.args.get("decision", None)
        sector_filter = request.args.get("sector", None)

        where_clauses = []
        params = []

        if decision_filter:
            where_clauses.append("decision = %s")
            params.append(decision_filter.upper())
        if sector_filter:
            where_clauses.append("sector = %s")
            params.append(sector_filter)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        params.append(limit)

        rows = _query(f"""
            SELECT
                application_id, submitted_at, applicant_type, sector,
                requested_amount, currency, tenor_months, financing_type, purpose,
                credit_score, debt_service_ratio, asset_backing_ratio,
                sharia_compliant, gharar_score,
                signal_probability_score, signal_risk_exposure,
                decision, receipt_id, blocked_at_checkpoint, block_reason,
                checkpoints_passed, checkpoints_total,
                macro_stress_level, fed_funds_rate
            FROM credit_applications
            {where_sql}
            ORDER BY submitted_at DESC
            LIMIT %s
        """, params if params else [limit])

        # Format for frontend
        formatted = []
        for r in rows:
            formatted.append({
                **r,
                "submitted_at": str(r.get("submitted_at", "")),
                "requested_amount": float(r.get("requested_amount") or 0),
                "credit_score": float(r.get("credit_score") or 0),
                "debt_service_ratio": float(r.get("debt_service_ratio") or 0),
                "asset_backing_ratio": float(r.get("asset_backing_ratio") or 0),
                "gharar_score": float(r.get("gharar_score") or 0),
                "signal_probability_score": float(r.get("signal_probability_score") or 0),
                "signal_risk_exposure": float(r.get("signal_risk_exposure") or 0),
            })

        return jsonify({"status": "ok", "applications": formatted, "count": len(formatted)})

    except Exception as e:
        logger.error(f"[CreditAPI] applications error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────────
# Sector Breakdown
# ──────────────────────────────────────────────────────────────────────────────

@credit_bp.route("/sectors")
def get_sectors():
    """Governance decisions broken down by sector."""
    try:
        rows = _query("""
            SELECT
                sector,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE decision = 'APPROVED') as approved,
                COUNT(*) FILTER (WHERE decision = 'BLOCKED') as blocked,
                ROUND(AVG(CASE WHEN decision = 'APPROVED' THEN 1.0 ELSE 0.0 END) * 100, 1)
                    as approval_rate,
                ROUND(SUM(requested_amount), 0) as total_amount_aed,
                ROUND(AVG(signal_probability_score), 1) as avg_probability
            FROM credit_applications
            GROUP BY sector
            ORDER BY total DESC
        """)
        typed = [
            {
                "sector": r["sector"],
                "total": int(r["total"]),
                "approved": int(r["approved"]),
                "blocked": int(r["blocked"]),
                "approval_rate": float(r["approval_rate"] or 0),
                "total_amount_aed": float(r["total_amount_aed"] or 0),
                "avg_probability": float(r["avg_probability"] or 0),
            }
            for r in rows
        ]
        return jsonify({"status": "ok", "sectors": typed})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────────
# Timeline
# ──────────────────────────────────────────────────────────────────────────────

@credit_bp.route("/timeline")
def get_timeline():
    """Hourly/daily timeline of governance decisions."""
    try:
        interval = request.args.get("interval", "hour")
        trunc = "hour" if interval == "hour" else "day"

        rows = _query(f"""
            SELECT
                DATE_TRUNC('{trunc}', submitted_at) as period,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE decision = 'APPROVED') as approved,
                COUNT(*) FILTER (WHERE decision = 'BLOCKED') as blocked,
                ROUND(SUM(requested_amount), 0) as total_amount_aed,
                ROUND(AVG(signal_probability_score), 1) as avg_probability
            FROM credit_applications
            WHERE submitted_at >= NOW() - INTERVAL '7 days'
            GROUP BY period
            ORDER BY period DESC
            LIMIT 168
        """)

        formatted = [
            {**r, "period": str(r.get("period", ""))}
            for r in rows
        ]

        return jsonify({"status": "ok", "timeline": formatted})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────────
# Manual Evaluation
# ──────────────────────────────────────────────────────────────────────────────

@credit_bp.route("/evaluate", methods=["POST"])
def manual_evaluate():
    """
    Manually evaluate a credit application through the governance pipeline.
    Useful for demo and testing purposes.
    """
    try:
        data = request.get_json(force=True) or {}

        from omnix_core.credit.credit_signal_adapter import CreditApplication
        from omnix_core.credit.credit_macro_data import CreditMacroDataProvider
        from omnix_core.credit.credit_simulator import evaluate_credit_application
        import asyncio

        app = CreditApplication(
            application_id=f"MANUAL-{int(time.time())}",
            applicant_type=data.get("applicant_type", "SME"),
            sector=data.get("sector", "technology"),
            requested_amount=float(data.get("requested_amount", 500_000)),
            tenor_months=int(data.get("tenor_months", 36)),
            financing_type=data.get("financing_type", "Murabaha"),
            purpose=data.get("purpose", "Working capital"),
            credit_score=float(data.get("credit_score", 680)),
            debt_service_ratio=float(data.get("debt_service_ratio", 0.35)),
            asset_backing_ratio=float(data.get("asset_backing_ratio", 1.20)),
            collateral_type=data.get("collateral_type", "property"),
            annual_revenue=float(data.get("annual_revenue", 2_000_000)),
            existing_obligations=float(data.get("existing_obligations", 0)),
            gharar_score=float(data.get("gharar_score", 25.0)),
        )

        macro_provider = CreditMacroDataProvider()
        macro = macro_provider.get_snapshot()

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(evaluate_credit_application(app, macro))
        loop.close()

        if not result:
            return jsonify({"status": "error", "message": "Evaluation failed"}), 500

        signals = result["signals"]

        return jsonify({
            "status": "ok",
            "application_id": app.application_id,
            "decision": result["final_decision"],
            "checkpoints_passed": result.get("checkpoints_passed", 0),
            "checkpoints_total": result.get("checkpoints_total", 8),
            "receipt_id": result.get("receipt_id"),
            "block_reason": result.get("block_reason"),
            "blocked_at": result.get("blocked_at"),
            "sharia_compliant": signals.sharia_compliant,
            "sharia_violation": signals.sharia_violation,
            "signals": signals.to_dict(),
            "gate_results": result.get("gate_results", []),
            "macro": {
                "credit_index": macro.credit_conditions_index,
                "stress_level": macro.stress_level,
                "fed_funds_rate": macro.fed_funds_rate,
            },
        })

    except Exception as e:
        logger.error(f"[CreditAPI] evaluate error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────────
# Macro Conditions
# ──────────────────────────────────────────────────────────────────────────────

@credit_bp.route("/macro")
def get_macro():
    """Current macroeconomic conditions used by the credit engine."""
    try:
        from omnix_core.credit.credit_macro_data import CreditMacroDataProvider
        provider = CreditMacroDataProvider()
        snap = provider.get_snapshot()

        return jsonify({
            "status": "ok",
            "macro": {
                "credit_conditions_index": snap.credit_conditions_index,
                "market_stress_index": snap.market_stress_index,
                "liquidity_score": snap.liquidity_score,
                "macro_volatility": snap.macro_volatility,
                "fed_funds_rate": snap.fed_funds_rate,
                "us_10yr_yield": snap.us_10yr_yield,
                "credit_spread_bps": snap.credit_spread_bps,
                "vix_proxy": snap.vix_proxy,
                "stress_level": snap.stress_level,
                "source": snap.source,
                "age_seconds": snap.age_seconds,
            },
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────────────────────────────────────

@credit_bp.route("/health")
def health():
    """Engine health check."""
    try:
        row = _queryOne("""
            SELECT
                COUNT(*) as total,
                MAX(submitted_at) as last_evaluation,
                EXTRACT(EPOCH FROM (NOW() - MAX(submitted_at))) as seconds_since_last
            FROM credit_applications
        """)

        total = int(row.get("total") or 0) if row else 0
        last_eval = str(row.get("last_evaluation") or "") if row else ""
        secs = float(row.get("seconds_since_last") or 9999) if row else 9999

        CYCLE_TIMEOUT = 900  # 15 min = 3 cycles missed
        engine_status = "RUNNING" if secs < CYCLE_TIMEOUT else "STALE"

        return jsonify({
            "status": "ok",
            "engine": engine_status,
            "total_evaluations": total,
            "last_evaluation": last_eval,
            "seconds_since_last_evaluation": round(secs, 0),
            "cycle_interval_seconds": 300,
            "vertical": "islamic_credit_v1",
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
