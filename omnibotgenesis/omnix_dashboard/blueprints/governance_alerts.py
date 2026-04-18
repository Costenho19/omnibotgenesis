"""
OMNIX Governance Alerts — Real-Time Notification System for B2B Clients.

Delivers real-time alerts when governance events occur: blocked decisions,
high-risk scores, checkpoint vetoes, and daily summaries.

GET  /api/governance/alerts/config              — Get client's alert configuration
PUT  /api/governance/alerts/config              — Create or update alert configuration
DELETE /api/governance/alerts/config/<alert_id> — Remove an alert configuration
GET  /api/governance/alerts/events              — List alert event history
POST /api/governance/alerts/test                — Send a test alert to verify delivery

Internal (called by governance.py evaluate endpoint):
  trigger_alerts(client_id, evaluation_result, receipt_id)

Supported channels:
  - webhook: HTTP POST to a client-specified URL (universal B2B)
  - email:   SMTP delivery (requires SMTP_HOST, SMTP_USER, SMTP_PASSWORD env vars)

Alert types:
  - decision_blocked:   Triggered when any decision is blocked (HOLD/REJECT)
  - high_risk_score:    Triggered when decision_score exceeds threshold (default: 80)
  - checkpoint_veto:    Triggered when a specific checkpoint fires a veto
  - all_decisions:      Triggered on every evaluation (verbose — use for auditing)
  - daily_summary:      Scheduled daily digest (requires external scheduler or cron)

Delivery semantics:
  - Best-effort: delivery failures are logged but never raise to the client.
  - Each attempt is recorded in alert_events with delivery_status.
  - Webhook timeout: 5 seconds (fire-and-forget for production evaluations).
  - Retry: not automatic (clients can inspect events and re-trigger manually).

ADR-039: Alerts and Notification System
"""

import json
import logging
import os
import smtplib
import threading
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import psycopg2
import psycopg2.extras
from flask import Blueprint, jsonify, request

from .auth_rbac import authenticate_client, update_last_seen

logger = logging.getLogger(__name__)

governance_alerts_bp = Blueprint("governance_alerts", __name__)

ALERT_TYPES = {
    "decision_blocked": "Triggered when a decision is blocked (HOLD or REJECT outcome)",
    "high_risk_score": "Triggered when the decision risk score exceeds the configured threshold",
    "checkpoint_veto": "Triggered when a specific checkpoint fires a veto",
    "all_decisions": "Triggered on every governance evaluation (verbose)",
    "daily_summary": "Daily digest of governance activity",
}

ALERT_CHANNELS = {
    "webhook": "HTTP POST to a client-specified URL",
    "email": "Email delivery to a configured address",
}

_WEBHOOK_TIMEOUT_SECONDS = 5
_TABLES_ENSURED = False


# ── DB HELPERS ────────────────────────────────────────────────────────────────

def _get_db_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def _ensure_tables() -> None:
    global _TABLES_ENSURED
    if _TABLES_ENSURED:
        return
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alert_configs (
                id SERIAL PRIMARY KEY,
                alert_config_id VARCHAR(64) UNIQUE NOT NULL,
                client_id VARCHAR(64) NOT NULL REFERENCES b2b_clients(client_id) ON DELETE CASCADE,
                alert_type VARCHAR(32) NOT NULL
                    CHECK (alert_type IN ('decision_blocked','high_risk_score','checkpoint_veto','all_decisions','daily_summary')),
                channel VARCHAR(16) NOT NULL
                    CHECK (channel IN ('webhook', 'email')),
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                config JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (client_id, alert_type, channel)
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_alert_configs_client "
            "ON alert_configs(client_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_alert_configs_enabled "
            "ON alert_configs(client_id, enabled)"
        )
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alert_events (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(64) UNIQUE NOT NULL,
                alert_config_id VARCHAR(64) REFERENCES alert_configs(alert_config_id) ON DELETE SET NULL,
                client_id VARCHAR(64) NOT NULL,
                alert_type VARCHAR(32) NOT NULL,
                channel VARCHAR(16) NOT NULL,
                trigger_data JSONB,
                delivery_status VARCHAR(16) NOT NULL DEFAULT 'pending'
                    CHECK (delivery_status IN ('pending','delivered','failed','skipped')),
                delivery_error TEXT,
                delivered_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_alert_events_client "
            "ON alert_events(client_id, created_at DESC)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_alert_events_status "
            "ON alert_events(client_id, delivery_status)"
        )
        conn.commit()
        conn.close()
        _TABLES_ENSURED = True
        logger.info("Alert tables ensured")
    except Exception as e:
        logger.warning(f"_ensure_tables alerts: {e}")


# ── AUTH ──────────────────────────────────────────────────────────────────────

def _require_auth():
    api_key = request.headers.get("X-API-Key", "")
    client = authenticate_client(api_key)
    if client is None:
        return None, (jsonify({"error": "Unauthorized — provide a valid X-API-Key", "status": 401}), 401)
    return client, None


# ── DELIVERY ENGINES ──────────────────────────────────────────────────────────

def _deliver_webhook(url: str, payload: dict, event_id: str, config_id: str | None) -> tuple[bool, str]:
    """POST payload to webhook URL. Returns (success, error_message)."""
    try:
        import urllib.request
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "OMNIX-Alerts/1.0",
                "X-OMNIX-Event-ID": event_id,
                "X-OMNIX-Alert-Config": config_id or "",
            },
            method="POST",
        )
        import urllib.error
        try:
            with urllib.request.urlopen(req, timeout=_WEBHOOK_TIMEOUT_SECONDS) as resp:
                status = resp.status
                if 200 <= status < 300:
                    return True, ""
                return False, f"HTTP {status}"
        except urllib.error.HTTPError as e:
            return False, f"HTTP {e.code}"
        except Exception as e:
            return False, str(e)
    except Exception as e:
        return False, str(e)


def _deliver_email(to_address: str, subject: str, html_body: str, text_body: str) -> tuple[bool, str]:
    """Send email via SMTP. Returns (success, error_message)."""
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user)

    if not smtp_host or not smtp_user:
        return False, "SMTP not configured (set SMTP_HOST, SMTP_USER, SMTP_PASSWORD)"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"OMNIX Alerts <{smtp_from}>"
        msg["To"] = to_address
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, [to_address], msg.as_string())
        return True, ""
    except Exception as e:
        return False, str(e)


def _record_event(
    conn,
    event_id: str,
    config_id: str | None,
    client_id: str,
    alert_type: str,
    channel: str,
    trigger_data: dict,
    status: str,
    error: str = "",
) -> None:
    """Record alert delivery attempt in alert_events table."""
    try:
        cur = conn.cursor()
        delivered_at = "NOW()" if status == "delivered" else "NULL"
        cur.execute(
            f"""
            INSERT INTO alert_events
              (event_id, alert_config_id, client_id, alert_type, channel,
               trigger_data, delivery_status, delivery_error, delivered_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, {delivered_at})
            """,
            (
                event_id,
                config_id,
                client_id,
                alert_type,
                channel,
                json.dumps(trigger_data),
                status,
                error[:512] if error else None,
            ),
        )
    except Exception as e:
        logger.warning(f"_record_event failed: {e}")


# ── INTERNAL TRIGGER (called from governance.py) ──────────────────────────────

def trigger_alerts(client_id: str, evaluation: dict, receipt_id: str | None = None) -> None:
    """
    Evaluate which alert configs match this governance result and deliver them.
    Called asynchronously from governance.py after each evaluation.
    Never raises — all errors are logged and recorded.
    """
    try:
        _ensure_tables()
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT alert_config_id, alert_type, channel, config
            FROM alert_configs
            WHERE client_id = %s AND enabled = TRUE
            """,
            (client_id,),
        )
        configs = cur.fetchall()
        conn.close()

        if not configs:
            return

        decision = evaluation.get("decision", "UNKNOWN")
        decision_score = evaluation.get("decision_score") or evaluation.get("score")
        veto_chain = evaluation.get("veto_chain", [])
        blocked_checkpoints = [v for v in veto_chain if v.get("result") == "VETO"]

        for cfg in configs:
            alert_type = cfg["alert_type"]
            channel = cfg["channel"]
            config = cfg["config"] or {}
            config_id = cfg["alert_config_id"]

            should_fire = False

            if alert_type == "all_decisions":
                should_fire = True
            elif alert_type == "decision_blocked" and decision in ("HOLD", "REJECT", "VETO"):
                should_fire = True
            elif alert_type == "high_risk_score":
                threshold = float(config.get("threshold", 80))
                if decision_score is not None and float(decision_score) >= threshold:
                    should_fire = True
            elif alert_type == "checkpoint_veto" and blocked_checkpoints:
                watched = config.get("checkpoint_ids", [])
                if not watched:
                    should_fire = True
                else:
                    fired_ids = [v.get("checkpoint_id") for v in blocked_checkpoints]
                    should_fire = any(cp in fired_ids for cp in watched)

            if not should_fire:
                continue

            event_id = f"AEV-{uuid.uuid4().hex[:12].upper()}"
            trigger_data = {
                "event_id": event_id,
                "client_id": client_id,
                "alert_type": alert_type,
                "decision": decision,
                "decision_score": decision_score,
                "checkpoints_passed": evaluation.get("checkpoints_passed"),
                "checkpoints_total": evaluation.get("checkpoints_total"),
                "checkpoints_blocked": len(blocked_checkpoints),
                "blocked_checkpoints": [v.get("checkpoint_id") for v in blocked_checkpoints],
                "receipt_id": receipt_id,
                "asset": evaluation.get("asset", "UNKNOWN"),
                "domain": evaluation.get("domain", "unknown"),
                "omnix_source": "OMNIX Decision Governance Infrastructure",
            }

            _fire_alert(
                event_id=event_id,
                config_id=config_id,
                client_id=client_id,
                alert_type=alert_type,
                channel=channel,
                config=config,
                trigger_data=trigger_data,
            )

    except Exception as e:
        logger.error(f"trigger_alerts error for client={client_id}: {e}")


def _fire_alert(
    event_id: str,
    config_id: str,
    client_id: str,
    alert_type: str,
    channel: str,
    config: dict,
    trigger_data: dict,
) -> None:
    """Deliver a single alert. Records result in alert_events."""
    success = False
    error_msg = ""

    try:
        if channel == "webhook":
            url = config.get("url", "")
            if not url:
                success, error_msg = False, "Webhook URL not configured"
            else:
                success, error_msg = _deliver_webhook(url, trigger_data, event_id, config_id)

        elif channel == "email":
            to_address = config.get("email", "")
            if not to_address:
                success, error_msg = False, "Email address not configured"
            else:
                alert_labels = {
                    "decision_blocked": "Decision Blocked",
                    "high_risk_score": "High Risk Score Detected",
                    "checkpoint_veto": "Checkpoint Veto Fired",
                    "all_decisions": "Governance Decision",
                    "daily_summary": "Daily Summary",
                }
                subject = f"OMNIX Alert — {alert_labels.get(alert_type, alert_type)} [{trigger_data.get('asset', '')}]"
                decision = trigger_data.get("decision", "UNKNOWN")
                score = trigger_data.get("decision_score")
                blocked = trigger_data.get("checkpoints_blocked", 0)
                receipt_id = trigger_data.get("receipt_id", "N/A")
                html_body = f"""
                <html><body style="font-family:Arial,sans-serif;color:#1a1a2e;padding:24px;">
                <div style="border-left:4px solid #003f8a;padding-left:16px;margin-bottom:24px;">
                  <h2 style="margin:0;color:#003f8a;">OMNIX Governance Alert</h2>
                  <p style="color:#666;margin:4px 0 0;">{alert_labels.get(alert_type, alert_type)}</p>
                </div>
                <table style="border-collapse:collapse;width:100%;max-width:500px;">
                  <tr><td style="padding:8px;background:#f5f7fa;font-weight:bold;">Decision</td>
                      <td style="padding:8px;">{decision}</td></tr>
                  <tr><td style="padding:8px;background:#f5f7fa;font-weight:bold;">Risk Score</td>
                      <td style="padding:8px;">{f"{score:.1f}" if score is not None else "N/A"}</td></tr>
                  <tr><td style="padding:8px;background:#f5f7fa;font-weight:bold;">Checkpoints Blocked</td>
                      <td style="padding:8px;">{blocked}</td></tr>
                  <tr><td style="padding:8px;background:#f5f7fa;font-weight:bold;">Asset</td>
                      <td style="padding:8px;">{trigger_data.get("asset","N/A")}</td></tr>
                  <tr><td style="padding:8px;background:#f5f7fa;font-weight:bold;">Receipt ID</td>
                      <td style="padding:8px;font-family:monospace;">{receipt_id}</td></tr>
                </table>
                <p style="margin-top:24px;color:#999;font-size:12px;">
                  OMNIX Decision Governance Infrastructure — Event {event_id}<br>
                  This is an automated alert. Do not reply to this message.
                </p>
                </body></html>
                """
                text_body = (
                    f"OMNIX Alert — {alert_labels.get(alert_type, alert_type)}\n\n"
                    f"Decision: {decision}\n"
                    f"Risk Score: {score}\n"
                    f"Checkpoints Blocked: {blocked}\n"
                    f"Asset: {trigger_data.get('asset','N/A')}\n"
                    f"Receipt ID: {receipt_id}\n\n"
                    f"Event ID: {event_id}\n"
                    "OMNIX Decision Governance Infrastructure"
                )
                success, error_msg = _deliver_email(to_address, subject, html_body, text_body)
        else:
            success, error_msg = False, f"Unsupported channel: {channel}"

    except Exception as e:
        success, error_msg = False, str(e)

    status = "delivered" if success else "failed"
    if error_msg:
        logger.warning(f"Alert {event_id} {channel} {status}: {error_msg}")
    else:
        logger.info(f"Alert {event_id} {channel} delivered")

    try:
        conn = _get_db_conn()
        _record_event(conn, event_id, config_id, client_id, alert_type, channel, trigger_data, status, error_msg)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"_fire_alert record error: {e}")


# ── CONFIG ENDPOINTS ──────────────────────────────────────────────────────────

@governance_alerts_bp.route("/api/governance/alerts/config", methods=["GET"])
def get_alert_configs():
    """Get all alert configurations for the authenticated client."""
    client, err = _require_auth()
    if err:
        return err

    _ensure_tables()
    client_id = client["client_id"]

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT alert_config_id, alert_type, channel, enabled, config,
                   created_at, updated_at
            FROM alert_configs
            WHERE client_id = %s
            ORDER BY created_at DESC
            """,
            (client_id,),
        )
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        ref = str(uuid.uuid4())[:8]
        logger.error(f"get_alert_configs error ref={ref}: {e}")
        return jsonify({"error": "Failed to retrieve alert configs", "reference": ref, "status": 500}), 500

    configs = []
    for row in rows:
        configs.append({
            "alert_config_id": row["alert_config_id"],
            "alert_type": row["alert_type"],
            "alert_type_description": ALERT_TYPES.get(row["alert_type"], ""),
            "channel": row["channel"],
            "channel_description": ALERT_CHANNELS.get(row["channel"], ""),
            "enabled": row["enabled"],
            "config": row["config"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        })

    update_last_seen(client_id)
    return jsonify({
        "configs": configs,
        "total": len(configs),
        "available_alert_types": ALERT_TYPES,
        "available_channels": ALERT_CHANNELS,
    })


@governance_alerts_bp.route("/api/governance/alerts/config", methods=["PUT"])
def upsert_alert_config():
    """
    Create or update an alert configuration.

    Body:
      alert_type  (required): decision_blocked | high_risk_score | checkpoint_veto |
                               all_decisions | daily_summary
      channel     (required): webhook | email
      enabled     (optional, default true): boolean
      config      (required): channel-specific settings
        For webhook: { "url": "https://..." }
        For email:   { "email": "ops@company.com" }
        For high_risk_score: { "threshold": 80.0, ... }
        For checkpoint_veto: { "checkpoint_ids": ["CP-1","CP-2"], ... }
    """
    client, err = _require_auth()
    if err:
        return err

    _ensure_tables()
    client_id = client["client_id"]

    if not request.is_json:
        return jsonify({"error": "Request must be Content-Type: application/json", "status": 400}), 400

    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON body", "status": 400}), 400

    alert_type = str(body.get("alert_type", "")).strip()
    channel = str(body.get("channel", "")).strip()
    enabled = bool(body.get("enabled", True))
    config = body.get("config", {})

    if alert_type not in ALERT_TYPES:
        return jsonify({
            "error": f"Invalid alert_type. Must be one of: {', '.join(ALERT_TYPES.keys())}",
            "status": 400,
        }), 400

    if channel not in ALERT_CHANNELS:
        return jsonify({
            "error": f"Invalid channel. Must be one of: {', '.join(ALERT_CHANNELS.keys())}",
            "status": 400,
        }), 400

    if not isinstance(config, dict):
        return jsonify({"error": "'config' must be a JSON object", "status": 400}), 400

    if channel == "webhook" and not config.get("url", "").startswith("https://"):
        return jsonify({
            "error": "Webhook config must include 'url' starting with 'https://'",
            "status": 400,
        }), 400

    if channel == "email" and "@" not in config.get("email", ""):
        return jsonify({
            "error": "Email config must include a valid 'email' address",
            "status": 400,
        }), 400

    if alert_type == "high_risk_score":
        threshold = config.get("threshold", 80)
        try:
            threshold = float(threshold)
            if not (0 <= threshold <= 100):
                raise ValueError
            config["threshold"] = threshold
        except (ValueError, TypeError):
            return jsonify({"error": "high_risk_score config requires 'threshold' (0–100)", "status": 400}), 400

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            INSERT INTO alert_configs
              (alert_config_id, client_id, alert_type, channel, enabled, config)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (client_id, alert_type, channel)
            DO UPDATE SET
              enabled = EXCLUDED.enabled,
              config = EXCLUDED.config,
              updated_at = NOW()
            RETURNING alert_config_id, alert_type, channel, enabled, config, created_at, updated_at
            """,
            (
                f"AC-{uuid.uuid4().hex[:12].upper()}",
                client_id,
                alert_type,
                channel,
                enabled,
                json.dumps(config),
            ),
        )
        row = dict(cur.fetchone())
        conn.commit()
        conn.close()
    except Exception as e:
        ref = str(uuid.uuid4())[:8]
        logger.error(f"upsert_alert_config error ref={ref}: {e}")
        return jsonify({"error": "Failed to save alert config", "reference": ref, "status": 500}), 500

    update_last_seen(client_id)
    return jsonify({
        "alert_config_id": row["alert_config_id"],
        "alert_type": row["alert_type"],
        "channel": row["channel"],
        "enabled": row["enabled"],
        "config": row["config"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        "status": "saved",
    }), 200


@governance_alerts_bp.route("/api/governance/alerts/config/<alert_config_id>", methods=["DELETE"])
def delete_alert_config(alert_config_id: str):
    """Remove an alert configuration."""
    client, err = _require_auth()
    if err:
        return err

    _ensure_tables()
    client_id = client["client_id"]

    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM alert_configs WHERE alert_config_id = %s AND client_id = %s",
            (alert_config_id, client_id),
        )
        deleted = cur.rowcount
        conn.commit()
        conn.close()
    except Exception as e:
        ref = str(uuid.uuid4())[:8]
        logger.error(f"delete_alert_config error ref={ref}: {e}")
        return jsonify({"error": "Failed to delete config", "reference": ref, "status": 500}), 500

    if deleted == 0:
        return jsonify({"error": "Alert config not found", "status": 404}), 404

    update_last_seen(client_id)
    return jsonify({
        "message": f"Alert config {alert_config_id} removed",
        "status": "deleted",
    })


# ── EVENTS ENDPOINT ───────────────────────────────────────────────────────────

@governance_alerts_bp.route("/api/governance/alerts/events", methods=["GET"])
def get_alert_events():
    """List alert delivery history for the authenticated client."""
    client, err = _require_auth()
    if err:
        return err

    _ensure_tables()
    client_id = client["client_id"]

    limit = min(int(request.args.get("limit", 50)), 200)
    status_filter = request.args.get("status")
    alert_type_filter = request.args.get("alert_type")

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT event_id, alert_config_id, alert_type, channel,
                   trigger_data, delivery_status, delivery_error,
                   delivered_at, created_at
            FROM alert_events
            WHERE client_id = %s
        """
        params = [client_id]
        if status_filter and status_filter in ("pending", "delivered", "failed", "skipped"):
            query += " AND delivery_status = %s"
            params.append(status_filter)
        if alert_type_filter and alert_type_filter in ALERT_TYPES:
            query += " AND alert_type = %s"
            params.append(alert_type_filter)
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        rows = cur.fetchall()

        cur.execute(
            "SELECT delivery_status, COUNT(*) as cnt FROM alert_events WHERE client_id = %s GROUP BY delivery_status",
            (client_id,),
        )
        stats = {r["delivery_status"]: r["cnt"] for r in cur.fetchall()}
        conn.close()
    except Exception as e:
        ref = str(uuid.uuid4())[:8]
        logger.error(f"get_alert_events error ref={ref}: {e}")
        return jsonify({"error": "Failed to retrieve alert events", "reference": ref, "status": 500}), 500

    events = []
    for row in rows:
        events.append({
            "event_id": row["event_id"],
            "alert_config_id": row["alert_config_id"],
            "alert_type": row["alert_type"],
            "channel": row["channel"],
            "delivery_status": row["delivery_status"],
            "delivery_error": row["delivery_error"],
            "trigger_data": row["trigger_data"],
            "delivered_at": row["delivered_at"].isoformat() if row["delivered_at"] else None,
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        })

    update_last_seen(client_id)
    return jsonify({
        "events": events,
        "total": len(events),
        "delivery_stats": {
            "delivered": stats.get("delivered", 0),
            "failed": stats.get("failed", 0),
            "pending": stats.get("pending", 0),
            "skipped": stats.get("skipped", 0),
        },
    })


# ── TEST ENDPOINT ─────────────────────────────────────────────────────────────

@governance_alerts_bp.route("/api/governance/alerts/test", methods=["POST"])
def test_alert():
    """
    Send a test alert to verify delivery configuration.

    Body:
      alert_config_id (required): ID from GET /api/governance/alerts/config
    """
    client, err = _require_auth()
    if err:
        return err

    _ensure_tables()
    client_id = client["client_id"]

    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON body", "status": 400}), 400

    alert_config_id = str(body.get("alert_config_id", "")).strip()
    if not alert_config_id:
        return jsonify({"error": "'alert_config_id' is required", "status": 400}), 400

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM alert_configs WHERE alert_config_id = %s AND client_id = %s",
            (alert_config_id, client_id),
        )
        cfg = cur.fetchone()
        conn.close()
    except Exception as e:
        ref = str(uuid.uuid4())[:8]
        logger.error(f"test_alert lookup error ref={ref}: {e}")
        return jsonify({"error": "Config lookup failed", "reference": ref, "status": 500}), 500

    if not cfg:
        return jsonify({"error": "Alert config not found", "status": 404}), 404

    event_id = f"AEV-TEST-{uuid.uuid4().hex[:8].upper()}"
    trigger_data = {
        "event_id": event_id,
        "client_id": client_id,
        "alert_type": cfg["alert_type"],
        "is_test": True,
        "decision": "HOLD",
        "decision_score": 82.5,
        "checkpoints_passed": 5,
        "checkpoints_total": 11,
        "checkpoints_blocked": 3,
        "blocked_checkpoints": ["CP-3", "CP-4", "CP-5"],
        "receipt_id": "OMNIX-TEST-00000000",
        "asset": "TEST_ASSET",
        "domain": "test",
        "omnix_source": "OMNIX Decision Governance Infrastructure — Test Alert",
    }

    _fire_alert(
        event_id=event_id,
        config_id=cfg["alert_config_id"],
        client_id=client_id,
        alert_type=cfg["alert_type"],
        channel=cfg["channel"],
        config=cfg["config"] or {},
        trigger_data=trigger_data,
    )

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT delivery_status, delivery_error FROM alert_events WHERE event_id = %s",
            (event_id,),
        )
        result = cur.fetchone()
        conn.close()
    except Exception:
        result = None

    status = result["delivery_status"] if result else "unknown"
    error = result["delivery_error"] if result else None

    update_last_seen(client_id)
    return jsonify({
        "event_id": event_id,
        "alert_config_id": alert_config_id,
        "alert_type": cfg["alert_type"],
        "channel": cfg["channel"],
        "delivery_status": status,
        "delivery_error": error,
        "is_test": True,
        "message": "Test alert fired. Check delivery_status for result.",
    }), 200 if status == "delivered" else 207
