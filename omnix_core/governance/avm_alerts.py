"""
AVM Real Alerts — ADR-076 extension

Sends real-time notifications when the AVM detects critical schema or drift anomalies.
Alerts go to Telegram. On Telegram failure, logs at CRITICAL so the alert is
never silently lost regardless of channel availability.

Rate limiting: max 5 alerts per (event_type, domain) per 60 seconds to prevent
spam loops. Suppressed alerts are logged at WARNING level.

Environment variables required:
    TELEGRAM_BOT_TOKEN    — bot token (already present in OMNIX)
    OMNIX_ADMIN_CHAT_ID   — numeric chat ID of the admin who receives alerts

Optional:
    AVM_ALERT_MAX_PER_MINUTE  — override rate limit (default: 5)
    AVM_ALERT_WINDOW_SECONDS  — override window (default: 60)
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger("OMNIX.AVM.Alerts")

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

_ALERT_ICONS = {
    "SCHEMA_ANOMALY_NONE":    "🚨",
    "SCHEMA_ANOMALY_PARTIAL": "⚠️",
    "DRIFT_ANOMALY":          "💥",
    "SCHEMA_MISMATCH_DB":     "🛑",
}

# ── Rate limiter ────────────────────────────────────────────────────────────────
# Tracks timestamps of recent firings per (event_type, domain) key.
# Thread-safe via a dedicated lock.
_rate_lock = threading.Lock()
_rate_history: dict[str, list[float]] = defaultdict(list)


def _is_rate_limited(event_type: str, domain: str) -> bool:
    """
    Returns True if this (event_type, domain) pair has already fired
    AVM_ALERT_MAX_PER_MINUTE times within the last AVM_ALERT_WINDOW_SECONDS.
    Prunes stale timestamps on every call.
    """
    max_per_window = int(os.environ.get("AVM_ALERT_MAX_PER_MINUTE", "5"))
    window_seconds = float(os.environ.get("AVM_ALERT_WINDOW_SECONDS", "60"))
    key  = f"{event_type}:{domain}"
    now  = time.monotonic()

    with _rate_lock:
        history = _rate_history[key]
        cutoff  = now - window_seconds
        pruned  = [t for t in history if t > cutoff]
        _rate_history[key] = pruned

        if len(pruned) >= max_per_window:
            return True

        _rate_history[key].append(now)
        return False


# ── Transport ───────────────────────────────────────────────────────────────────

def _send_telegram(token: str, chat_id: str, text: str) -> None:
    url = _TELEGRAM_API.format(token=token)
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        resp.read()


# ── Public API ──────────────────────────────────────────────────────────────────

def fire_avm_alert(
    event_type: str,
    domain: str,
    detail: str,
    snapshot_id: str = "UNKNOWN",
) -> None:
    """
    Send a real Telegram alert for a critical AVM anomaly.

    Guarantees:
    - Never blocks the governance pipeline (runs in a daemon thread).
    - Never silently swallows failures: if Telegram delivery fails,
      the full alert text is emitted at CRITICAL log level.
    - Rate-limited: at most AVM_ALERT_MAX_PER_MINUTE (default 5) alerts
      per (event_type, domain) per AVM_ALERT_WINDOW_SECONDS (default 60s).
      Suppressed alerts are logged at WARNING.

    Args:
        event_type:  SCHEMA_ANOMALY_NONE | SCHEMA_ANOMALY_PARTIAL |
                     DRIFT_ANOMALY | SCHEMA_MISMATCH_DB
        domain:      AVM domain name (e.g. 'real_estate')
        detail:      Human-readable description of the anomaly
        snapshot_id: Snapshot identifier for traceability
    """
    if os.environ.get("TESTING", "").lower() == "true":
        logger.debug(
            f"[AVM.Alerts] TESTING mode — alert suppressed: {event_type} domain={domain}"
        )
        return

    # ── Rate limit check ────────────────────────────────────────────────────────
    if _is_rate_limited(event_type, domain):
        logger.warning(
            f"[AVM.Alerts] RATE_LIMITED — event={event_type} domain={domain} | "
            f"Max {os.environ.get('AVM_ALERT_MAX_PER_MINUTE', 5)} alerts/"
            f"{os.environ.get('AVM_ALERT_WINDOW_SECONDS', 60)}s reached. "
            "Alert suppressed to prevent spam."
        )
        return

    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("OMNIX_ADMIN_CHAT_ID", "")

    icon = _ALERT_ICONS.get(event_type, "⚠️")
    now  = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    text = (
        f"{icon} <b>OMNIX AVM ALERT</b>\n"
        f"Event: <code>{event_type}</code>\n"
        f"Domain: <code>{domain}</code>\n"
        f"Snapshot: <code>{snapshot_id}</code>\n"
        f"Time: {now}\n\n"
        f"{detail}"
    )

    if not token or not chat_id:
        # Channel not configured — log CRITICAL so no alert is ever silently lost
        logger.critical(
            f"[AVM.Alerts] ALERT_NOT_SENT — TELEGRAM_BOT_TOKEN or OMNIX_ADMIN_CHAT_ID "
            f"not set. Configure OMNIX_ADMIN_CHAT_ID to enable Telegram alerts.\n"
            f"ALERT CONTENT: event={event_type} domain={domain} snapshot={snapshot_id}\n"
            f"{detail}"
        )
        return

    def _send() -> None:
        try:
            _send_telegram(token, chat_id, text)
            logger.info(
                f"[AVM.Alerts] Alert sent — event={event_type} domain={domain}"
            )
        except Exception as exc:
            # Telegram delivery failed — escalate to CRITICAL so the alert
            # always surfaces in logs even when the channel is down
            logger.critical(
                f"[AVM.Alerts] TELEGRAM_DELIVERY_FAILED: {exc} | "
                f"event={event_type} domain={domain} snapshot={snapshot_id}\n"
                f"ALERT CONTENT (use this for manual follow-up):\n{detail}"
            )

    t = threading.Thread(target=_send, daemon=True, name=f"avm-alert-{domain}")
    t.start()
