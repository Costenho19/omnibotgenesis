"""
OMNIX — Health & Operational Readiness Blueprint  (ADR-150)

Endpoints:
  GET  /api/health             — full subsystem health report (JSON)
  GET  /api/health/live        — liveness probe (200 / 503) for Railway / load balancers
  GET  /api/health/ready       — readiness probe (200 / 503) — DB + governance must be UP
  POST /api/health/reconcile-wal — trigger WAL reconciliation (admin only)

Response contract:
  /api/health returns:
    {
      "status":              "UP" | "DEGRADED" | "DOWN",
      "timestamp_utc":       ISO-8601,
      "version":             "6.6.0",
      "governance_baseline": "OMNIX-BASELINE-2026-Q2-001",
      "uptime_seconds":      float,
      "wal_pending":         int,
      "adr_count":           int,
      "pqc_mode":            str,
      "subsystems": [
        { "name": str, "status": str, "latency_ms": float, "detail": str, "critical": bool }
      ]
    }

ADR-150: /api/health/live always returns 200 unless the process itself
is unhealthy (i.e. Python runtime is broken). /api/health/ready returns
503 only when critical subsystems (DB, governance engine) are DOWN.
"""

import logging
import os
from functools import wraps

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__)


# ── Minimal auth for reconcile-wal (admin IP or X-Admin-Token) ───────────────

def _admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        allowed_ips_raw = os.getenv("ADMIN_ALLOWED_IPS", "127.0.0.1")
        allowed_ips = [ip.strip() for ip in allowed_ips_raw.split(",") if ip.strip()]
        remote = request.remote_addr or ""
        admin_token = os.getenv("ADMIN_TOKEN", "")
        provided_token = request.headers.get("X-Admin-Token", "")
        if remote in allowed_ips:
            return f(*args, **kwargs)
        if admin_token and provided_token and provided_token == admin_token:
            return f(*args, **kwargs)
        return jsonify({"error": "Unauthorized"}), 403
    return decorated


# ── /api/health ───────────────────────────────────────────────────────────────

@health_bp.route("/api/health", methods=["GET"])
def health_full():
    """
    Full operational health report.

    Runs deep probes of all subsystems and returns a structured JSON report.
    Also dispatches Telegram alerts for any DOWN / DEGRADED subsystem
    (with 5-minute cooldown to prevent alert flooding).

    Query params:
      ?alerts=false  — suppress Telegram alerts for this request
    """
    try:
        from omnix_core.ops.health_check import run_health_check
        from omnix_core.ops.operational_alerts import evaluate_health_and_alert

        report = run_health_check()

        send_alerts = request.args.get("alerts", "true").lower() != "false"
        if send_alerts and os.getenv("TESTING", "").lower() != "true":
            try:
                evaluate_health_and_alert(report)
            except Exception as ae:
                logger.warning(f"[health_bp] Alert dispatch failed (non-blocking): {ae}")

        status_code = 200 if report.status in ("UP", "DEGRADED") else 503
        return jsonify(report.to_dict()), status_code

    except Exception as e:
        logger.error(f"[health_bp] Health check crashed: {e}")
        return jsonify({
            "status": "DOWN",
            "error":  str(e),
            "detail": "Health check module failed to execute",
        }), 503


# ── /api/health/live ─────────────────────────────────────────────────────────

@health_bp.route("/api/health/live", methods=["GET"])
def health_live():
    """
    Liveness probe — always 200 if the process is alive.
    Used by Railway / Kubernetes / uptime monitors.
    """
    from datetime import datetime, timezone
    return jsonify({
        "alive": True,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }), 200


# ── /api/health/ready ─────────────────────────────────────────────────────────

@health_bp.route("/api/health/ready", methods=["GET"])
def health_ready():
    """
    Readiness probe — 200 only when DB and governance engine are UP.
    Returns 503 when the instance should not receive traffic.
    """
    try:
        from omnix_core.ops.health_check import (
            _probe_database, _probe_governance_engine
        )
        import os
        db_probe  = _probe_database(os.getenv("DATABASE_URL"))
        gov_probe = _probe_governance_engine()

        ready = db_probe.status == "UP" and gov_probe.status == "UP"
        body = {
            "ready":    ready,
            "database": db_probe.status,
            "governance_engine": gov_probe.status,
        }
        return jsonify(body), 200 if ready else 503

    except Exception as e:
        return jsonify({"ready": False, "error": str(e)}), 503


# ── /api/health/reconcile-wal ────────────────────────────────────────────────

@health_bp.route("/api/health/reconcile-wal", methods=["POST"])
@_admin_required
def reconcile_wal():
    """
    Trigger WAL reconciliation — replay all pending receipts into the DB.

    ISR-012: Call this endpoint after a DB outage is resolved to flush
    receipts that were durably written to WAL but not yet committed to DB.

    Requires: request from ADMIN_ALLOWED_IPS or valid X-Admin-Token header.
    """
    try:
        from omnix_core.evidence.receipt_wal import get_receipt_wal
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        import os

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return jsonify({"error": "DATABASE_URL not configured"}), 503

        engine = DecisionReceiptEngine(db_url=db_url)
        wal = get_receipt_wal()

        pending_before = wal.wal_size()
        reconciled = wal.reconcile_wal(lambda r: engine.store_receipt(r))

        return jsonify({
            "reconciled":     reconciled,
            "pending_before": pending_before,
            "pending_after":  wal.wal_size(),
        }), 200

    except Exception as e:
        logger.error(f"[health_bp] WAL reconciliation failed: {e}")
        return jsonify({"error": str(e)}), 500
