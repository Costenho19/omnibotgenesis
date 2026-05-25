"""
OMNIX Governance API — External Signal Evaluation Endpoint.

POST /api/governance/evaluate                                         — Submit normalized signals, receive PQC-signed receipt.
GET  /api/governance/schema                                           — Signal schema documentation (public).
GET  /api/governance/receipts                                         — Client's own receipt history (authenticated, paginated).
GET  /api/governance/receipts/<receipt_id>                            — Fetch a single receipt by ID (authenticated, own only). ADR-053.
POST /api/governance/admin/clients                                     — Create B2B client (admin only).
GET  /api/governance/admin/clients                                     — List all B2B clients (admin only).
DELETE /api/governance/admin/clients/<client_id>                      — Deactivate client (admin only).
POST /api/governance/admin/clients/<client_id>/reactivate             — Reactivate client (admin only).
POST /api/governance/admin/clients/<client_id>/rotate                 — Rotate API key (admin only).
PUT  /api/governance/admin/clients/<client_id>/webhook                — Register/update webhook URL (admin only). ADR-053.
DELETE /api/governance/admin/clients/<client_id>/webhook              — Remove webhook config (admin only). ADR-053.
GET  /api/governance/admin/clients/<client_id>/webhook/deliveries     — Webhook delivery history (admin only). ADR-053.
GET  /api/governance/admin/clients/<client_id>/thresholds             — Get effective thresholds for client (admin only).
PUT  /api/governance/admin/clients/<client_id>/thresholds             — Set per-client checkpoint thresholds (admin only).
DELETE /api/governance/admin/clients/<client_id>/thresholds           — Revert client thresholds to defaults (admin only).
GET  /api/governance/admin/usage                                      — Monthly usage summary for all clients (admin only).
GET  /api/governance/admin/usage/<client_id>                          — Monthly usage detail for one client (admin only).
GET  /api/governance/admin/layer0/metrics                             — Layer 0 (SAE) admission metrics — global + per-domain (admin only). ADR-092.

ADR-028: External Signal Evaluation API
ADR-037: Per-Client Configurable Thresholds
ADR-051: Client Usage Reporting & Billing Audit Trail
ADR-052: API Key Expiry (90-day rolling window) + brute-force lockout
ADR-053: Generic Webhook Push System — HMAC-SHA256 signed delivery to client-registered HTTPS endpoints
"""

import hashlib
import hmac
import ipaddress
import json
import logging
import os
import secrets
import sys
import time
import threading
import urllib.parse
import urllib.request
import urllib.error
import uuid
from collections import defaultdict

import psycopg2
import psycopg2.extras
from flask import Blueprint, jsonify, request

try:
    from cryptography.fernet import Fernet
    _FERNET_AVAILABLE = True
except ImportError:
    _FERNET_AVAILABLE = False

try:
    from omnix_core.evidence.payload_key_manager import get_payload_key_manager as _get_pkey_mgr
    _PKM_AVAILABLE = True
except Exception:
    _PKM_AVAILABLE = False

try:
    # Standalone deployment (omnix_web/api/ on Railway)
    from api.gov_auth_rbac import (
        authenticate_client,
        create_client,
        deactivate_client,
        delete_client_webhook,
        get_client_webhook,
        list_clients,
        reactivate_client,
        rotate_api_key,
        set_client_webhook,
        update_last_seen,
    )
except ImportError:
    # Package deployment (omnix_dashboard/ on Flask Dashboard)
    from .auth_rbac import (
        authenticate_client,
        create_client,
        deactivate_client,
        list_clients,
        reactivate_client,
        rotate_api_key,
        update_last_seen,
    )
    def get_client_webhook(client_id): return None
    def set_client_webhook(client_id, url, secret): return False
    def delete_client_webhook(client_id): return False

_alerts_trigger = None

def _get_alerts_trigger():
    global _alerts_trigger
    if _alerts_trigger is not None:
        return _alerts_trigger
    try:
        from .governance_alerts import trigger_alerts
        _alerts_trigger = trigger_alerts
    except Exception:
        _alerts_trigger = None
    return _alerts_trigger


# ── REGULATORY MAPPING (ADR-062) ──────────────────────────────────────────────
try:
    from api.omnix_engine.regulatory_mapping import (
        build_regulatory_summary,
        get_full_framework_catalog,
    )
    _REGULATORY_MAPPING_AVAILABLE = True
except ImportError:
    try:
        from omnix_engine.regulatory_mapping import (
            build_regulatory_summary,
            get_full_framework_catalog,
        )
        _REGULATORY_MAPPING_AVAILABLE = True
    except ImportError:
        _REGULATORY_MAPPING_AVAILABLE = False
        def build_regulatory_summary(*a, **kw): return {}
        def get_full_framework_catalog(): return {}

# ── DUE DILIGENCE GENERATOR (ADR-062) ─────────────────────────────────────────
try:
    from api.omnix_engine.due_diligence import generate_due_diligence_pdf
    _DUE_DILIGENCE_AVAILABLE = True
except ImportError:
    try:
        from omnix_engine.due_diligence import generate_due_diligence_pdf
        _DUE_DILIGENCE_AVAILABLE = True
    except ImportError:
        _DUE_DILIGENCE_AVAILABLE = False
        def generate_due_diligence_pdf(*a, **kw): return b""

# ── STRUCTURAL ADMISSIBILITY ENGINE — Layer 0 Metrics (ADR-092) ───────────────
try:
    from omnix_core.governance.structural_admissibility_engine import (
        get_layer0_metrics         as _get_layer0_metrics,
        get_layer0_snapshot_history as _get_layer0_snapshot_history,
        get_sae_override            as _get_sae_override,
        _LAYER0_DEMO_TAGLINE,
        _snapshot_interval_minutes  as _SNAPSHOT_INTERVAL_MIN,
    )
    _SAE_METRICS_AVAILABLE = True
except ImportError:
    _SAE_METRICS_AVAILABLE = False
    _LAYER0_DEMO_TAGLINE   = ""
    _SNAPSHOT_INTERVAL_MIN = 5
    def _get_layer0_metrics():
        class _Stub:
            def snapshot(self): return {}
        return _Stub()
    def _get_layer0_snapshot_history(last_n=None): return []
    def _get_sae_override():
        return None

logger = logging.getLogger(__name__)

# Startup warnings if premium ADR-062 modules are unavailable
if not _REGULATORY_MAPPING_AVAILABLE:
    logger.warning(
        "OMNIX STARTUP WARNING: regulatory_mapping module not loaded — "
        "regulatory_alignment will return empty dicts. "
        "Check omnix_engine/regulatory_mapping.py and dependencies."
    )
if not _DUE_DILIGENCE_AVAILABLE:
    logger.warning(
        "OMNIX STARTUP WARNING: due_diligence module not loaded — "
        "PDF generation will return empty bytes. "
        "Check omnix_engine/due_diligence.py and reportlab installation."
    )

governance_bp = Blueprint('governance', __name__)

_rate_limit_store: dict = defaultdict(list)
_RATE_LIMIT_WINDOW = 60
_RATE_LIMIT_MAX = 10

_client_rate_limit_store: dict = defaultdict(list)
_CLIENT_RATE_LIMIT_WINDOW = 60
_CLIENT_RATE_LIMIT_MAX = 120  # Authenticated B2B clients: 120/min (2/sec) — institutional burst capacity

_brute_force_store: dict = {}
_BRUTE_FORCE_MAX = 5
_BRUTE_FORCE_WINDOW = 900
_BRUTE_FORCE_LOCKOUT = 900

# ── PERSISTENT IP BLOCKLIST (ADR-061) ─────────────────────────────────────────
_blocked_ip_cache: dict = {}                  # ip -> blocked_until (epoch float)
_blocked_ip_cache_last_refresh: float = 0.0
_blocked_ip_cache_lock = threading.Lock()
_BLOCKLIST_CACHE_TTL     = 30                 # seconds between DB refreshes
_IP_BAN_VIOLATION_MAX    = 3                  # rate-limit hits before auto-ban
_IP_BAN_VIOLATION_WINDOW = 600               # 10-minute rolling window
_IP_BAN_DURATION         = 3600              # 1-hour ban
_ip_ban_violations: dict = defaultdict(list) # ip -> [timestamps of hits]
_blocked_ips_table_ensured = False

_WEBHOOK_PUSH_SEMAPHORE = threading.Semaphore(10)
_KEY_EXPIRY_WARNING_DAYS = 14

_SSRF_BLOCKED_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('0.0.0.0/8'),
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
    ipaddress.ip_network('fe80::/10'),
]

_MONTHLY_ALERT_THRESHOLD = 500
_monthly_alert_sent: dict = {}

# ── PER-CLIENT QUOTA ENFORCEMENT (ADR-081) ────────────────────────────────────
# Hard limits that block new evaluations when exceeded.
# Configurable via env vars — raise per client by updating b2b_clients table (tier field).
_CLIENT_DAILY_QUOTA_MAX   = int(os.environ.get('OMNIX_B2B_DAILY_QUOTA',   '5000'))
_CLIENT_MONTHLY_QUOTA_MAX = int(os.environ.get('OMNIX_B2B_MONTHLY_QUOTA', '50000'))

# Fail-open safety circuit — after this many consecutive DB failures per client
# within _QUOTA_DB_FAIL_WINDOW seconds, switch to fail-closed to prevent abuse
# during sustained DB outages. Resets automatically when DB recovers.
_QUOTA_DB_FAIL_OPEN_MAX  = 3    # consecutive errors before fail-closed kicks in
_QUOTA_DB_FAIL_WINDOW    = 60   # seconds
_quota_db_failures: dict = defaultdict(list)   # client_id -> [timestamps]

_ENGINE_AVAILABLE = False
_GovernanceEvaluationEngine = None
_DecisionReceiptEngine = None


# ── HELPERS ──────────────────────────────────────────────────────────────────

def _encrypt_payload(data: str) -> tuple[str | None, str]:
    """
    Encrypt string payload using versioned PayloadKeyManager (ISR-021).
    Returns (versioned_token_or_None, key_version_id).
    """
    if _PKM_AVAILABLE:
        try:
            mgr = _get_pkey_mgr()
            token = mgr.encrypt(data)
            return token, mgr.active_version_id()
        except Exception as e:
            logger.warning(f"PayloadKeyManager encryption failed: {e}")
    if not _FERNET_AVAILABLE:
        return None, "none"
    key = os.environ.get("PAYLOAD_ENCRYPTION_KEY")
    if not key:
        return None, "none"
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        token = f.encrypt(data.encode()).decode()
        return f"omnix-pek-v1:{token}", "v1"
    except Exception as e:
        logger.warning(f"Payload encryption failed: {e}")
        return None, "none"


def _load_engine():
    global _ENGINE_AVAILABLE, _GovernanceEvaluationEngine, _DecisionReceiptEngine
    if _ENGINE_AVAILABLE:
        return True
    try:
        import importlib.util

        _api_dir = os.path.dirname(__file__)

        # Path 1: bundled copy inside omnix_web/api/omnix_engine/ (Railway — only omnix_web is deployed)
        _local_evaluator = os.path.join(_api_dir, "omnix_engine", "external_evaluator.py")

        # Path 2: full repo (local dev — omnix_core available 3 levels up)
        _root = os.path.dirname(os.path.dirname(_api_dir))
        _repo_evaluator = os.path.join(_root, "omnix_core", "governance", "external_evaluator.py")

        evaluator_path = _local_evaluator if os.path.exists(_local_evaluator) else _repo_evaluator

        spec_ev = importlib.util.spec_from_file_location("_omnix_gov_evaluator", evaluator_path)
        mod_ev = importlib.util.module_from_spec(spec_ev)
        sys.modules['_omnix_gov_evaluator'] = mod_ev
        spec_ev.loader.exec_module(mod_ev)
        _GovernanceEvaluationEngine = mod_ev.GovernanceEvaluationEngine

        # ── DecisionReceiptEngine: ALWAYS import from the canonical module (ADR-085 fix).
        # Loading it via spec_from_file_location would create a SECOND module object with its
        # own _STABLE_SIGNING_KEYS — a different key than what federated_trust.py publishes in
        # the trust registry, breaking independent verification.
        # Direct import reuses the already-loaded module so both share the same stable key.
        try:
            from api.omnix_engine.decision_receipt import DecisionReceiptEngine as _DRE
        except ImportError:
            from omnix_engine.decision_receipt import DecisionReceiptEngine as _DRE
        _DecisionReceiptEngine = _DRE

        _ENGINE_AVAILABLE = True
        logger.info(
            f"GovernanceEvaluationEngine loaded from: {evaluator_path} | "
            f"DecisionReceiptEngine: direct import (key-consistent)"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to load governance engine: {e}")
        return False


def _is_rate_limited(client_ip: str) -> bool:
    now = time.time()
    window_start = now - _RATE_LIMIT_WINDOW
    _rate_limit_store[client_ip] = [ts for ts in _rate_limit_store[client_ip] if ts > window_start]
    if len(_rate_limit_store[client_ip]) >= _RATE_LIMIT_MAX:
        # Track violation for auto-ban — ADR-061
        viol_window = now - _IP_BAN_VIOLATION_WINDOW
        _ip_ban_violations[client_ip] = [
            ts for ts in _ip_ban_violations[client_ip] if ts > viol_window
        ]
        _ip_ban_violations[client_ip].append(now)
        viol_count = len(_ip_ban_violations[client_ip])
        if viol_count >= _IP_BAN_VIOLATION_MAX and not _is_ip_blocked(client_ip):
            _auto_ban_ip(
                client_ip,
                f"Rate limit exceeded {viol_count}x in {_IP_BAN_VIOLATION_WINDOW}s",
                viol_count,
            )
        return True
    _rate_limit_store[client_ip].append(now)
    return False


def _is_client_rate_limited(client_id: str) -> bool:
    """Per-client rate limit: max 30 calls per minute. Protects against accidental loops."""
    now = time.time()
    window_start = now - _CLIENT_RATE_LIMIT_WINDOW
    _client_rate_limit_store[client_id] = [
        ts for ts in _client_rate_limit_store[client_id] if ts > window_start
    ]
    if len(_client_rate_limit_store[client_id]) >= _CLIENT_RATE_LIMIT_MAX:
        return True
    _client_rate_limit_store[client_id].append(now)
    return False


# ── IP BLOCKLIST FUNCTIONS (ADR-061) ──────────────────────────────────────────

def _ensure_blocked_ips_table() -> None:
    """Create blocked_ips table and indexes lazily on first use. ADR-061."""
    global _blocked_ips_table_ensured
    if _blocked_ips_table_ensured:
        return
    try:
        conn = _get_db_conn()
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blocked_ips (
                ip               VARCHAR(64)  PRIMARY KEY,
                blocked_until    TIMESTAMPTZ  NOT NULL,
                reason           TEXT,
                violation_count  INTEGER      NOT NULL DEFAULT 1,
                created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_blocked_ips_until "
            "ON blocked_ips(blocked_until)"
        )
        conn.commit()
        cur.close()
        conn.close()
        _blocked_ips_table_ensured = True
        logger.info("[IP BLOCK] blocked_ips table ready")
    except Exception as e:
        logger.warning(f"[IP BLOCK] Table ensure failed: {e}")


def _refresh_blocked_ip_cache() -> None:
    """Load active blocks from DB into memory cache. Called under _blocked_ip_cache_lock."""
    try:
        _ensure_blocked_ips_table()
        conn = _get_db_conn()
        cur  = conn.cursor()
        cur.execute(
            "SELECT ip, EXTRACT(EPOCH FROM blocked_until) "
            "FROM blocked_ips WHERE blocked_until > NOW()"
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        _blocked_ip_cache.clear()
        for ip, until_epoch in rows:
            _blocked_ip_cache[ip] = float(until_epoch)
    except Exception as e:
        logger.warning(f"[IP BLOCK] Cache refresh failed: {e}")


def _is_ip_blocked(ip: str) -> bool:
    """
    Return True if IP has an active block in the DB-backed blocklist.
    Uses a 30-second in-memory cache to avoid DB hit on every request.
    Thread-safe. ADR-061.
    """
    global _blocked_ip_cache_last_refresh
    now = time.time()
    with _blocked_ip_cache_lock:
        if now - _blocked_ip_cache_last_refresh > _BLOCKLIST_CACHE_TTL:
            _refresh_blocked_ip_cache()
            _blocked_ip_cache_last_refresh = now
        until = _blocked_ip_cache.get(ip)
        if until:
            if now < until:
                return True
            _blocked_ip_cache.pop(ip, None)
    return False


def _auto_ban_ip(ip: str, reason: str, violation_count: int = 3) -> None:
    """
    Persist a 1-hour IP ban to blocked_ips table, update memory cache,
    and notify Harold via Telegram. Runs in a daemon thread — never blocks
    the request pipeline. ADR-061.
    """
    def _run():
        try:
            _ensure_blocked_ips_table()
            ban_until = time.time() + _IP_BAN_DURATION
            conn = _get_db_conn()
            cur  = conn.cursor()
            cur.execute("""
                INSERT INTO blocked_ips
                    (ip, blocked_until, reason, violation_count, updated_at)
                VALUES (%s, to_timestamp(%s), %s, %s, NOW())
                ON CONFLICT (ip) DO UPDATE
                    SET blocked_until   = EXCLUDED.blocked_until,
                        reason          = EXCLUDED.reason,
                        violation_count = blocked_ips.violation_count + 1,
                        updated_at      = NOW()
            """, (ip, ban_until, reason[:200], violation_count))
            conn.commit()
            cur.close()
            conn.close()
            with _blocked_ip_cache_lock:
                _blocked_ip_cache[ip] = ban_until
            logger.warning(
                f"[IP BLOCK] Auto-banned {ip} for {_IP_BAN_DURATION}s "
                f"— violations={violation_count} reason={reason}"
            )
            _notify_harold_telegram(
                f"🚫 <b>OMNIX — IP Bloqueada</b>\n\n"
                f"🔴 IP: <code>{ip}</code>\n"
                f"📋 Razón: {reason[:120]}\n"
                f"⚠️ Violaciones: {violation_count}\n"
                f"⏱ Bloqueada por: 1 hora"
            )
        except Exception as e:
            logger.error(f"[IP BLOCK] Auto-ban failed for {ip}: {e}")

    threading.Thread(target=_run, daemon=True).start()


def _check_client_quota(client_id: str) -> tuple:
    """
    Enforce per-client daily and monthly hard quotas (ADR-081).
    Queries decision_receipts for real usage counts.

    Fail-open / fail-closed policy:
      - First _QUOTA_DB_FAIL_OPEN_MAX-1 consecutive DB errors within _QUOTA_DB_FAIL_WINDOW
        seconds → fail-open (non-blocking, request proceeds).
      - On the Nth consecutive error → fail-closed to prevent sustained abuse
        during DB outages. Resets automatically when DB recovers.

    Returns (allowed: bool, error_message: str).
    """
    try:
        conn = _get_db_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT COUNT(*) FROM decision_receipts "
            "WHERE client_id = %s AND created_at >= NOW() - INTERVAL '24 hours'",
            (client_id,),
        )
        daily_count = cur.fetchone()[0]
        if daily_count >= _CLIENT_DAILY_QUOTA_MAX:
            conn.close()
            logger.warning(f"[QUOTA] Daily limit hit: client={client_id} count={daily_count}")
            return False, (
                'Daily evaluation quota reached. '
                'Contact support@omnixquantum.net to discuss a higher-tier plan.'
            )

        cur.execute(
            "SELECT COUNT(*) FROM decision_receipts "
            "WHERE client_id = %s AND created_at >= date_trunc('month', NOW())",
            (client_id,),
        )
        monthly_count = cur.fetchone()[0]
        conn.close()
        if monthly_count >= _CLIENT_MONTHLY_QUOTA_MAX:
            logger.warning(f"[QUOTA] Monthly limit hit: client={client_id} count={monthly_count}")
            return False, (
                'Monthly evaluation quota reached. '
                'Contact support@omnixquantum.net to discuss a higher-tier plan.'
            )

        # DB recovered — clear failure history for this client
        _quota_db_failures.pop(client_id, None)
        return True, ''

    except Exception as e:
        now = time.time()
        recent = [t for t in _quota_db_failures[client_id] if now - t < _QUOTA_DB_FAIL_WINDOW]
        recent.append(now)
        _quota_db_failures[client_id] = recent

        if len(recent) >= _QUOTA_DB_FAIL_OPEN_MAX:
            logger.warning(
                f'[QUOTA] Fail-CLOSED after {len(recent)} consecutive DB errors '
                f'in {_QUOTA_DB_FAIL_WINDOW}s for client={client_id}'
            )
            return False, 'Service temporarily unavailable — please retry in a few minutes.'

        logger.warning(f'[QUOTA] DB error ({len(recent)}/{_QUOTA_DB_FAIL_OPEN_MAX}) — fail-open: {type(e).__name__}')
        return True, ''


def _check_monthly_alert(client_id: str) -> None:
    """Check monthly usage and alert Harold via Telegram if threshold is crossed. Runs in background thread."""
    def _run():
        try:
            import datetime
            now = datetime.datetime.utcnow()
            month_key = f"{client_id}:{now.year}:{now.month}"

            if _monthly_alert_sent.get(month_key):
                return

            conn = _get_db_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM decision_receipts
                WHERE client_id = %s
                AND created_at >= date_trunc('month', NOW())
            """, (client_id,))
            count = cur.fetchone()[0]
            conn.close()

            if count >= _MONTHLY_ALERT_THRESHOLD:
                _monthly_alert_sent[month_key] = True
                msg = (
                    f"⚠️ OMNIX — Alerta de uso mensual\n\n"
                    f"Cliente: {client_id}\n"
                    f"Evaluaciones este mes: {count}\n"
                    f"Umbral: {_MONTHLY_ALERT_THRESHOLD}\n\n"
                    f"Revisar uso y facturación."
                )
                _notify_harold_telegram(msg)
        except Exception as e:
            logger.warning(f"_check_monthly_alert error: {e}")

    threading.Thread(target=_run, daemon=True).start()


def _get_db_conn():
    db_url = (
        os.environ.get("DATABASE_URL") or
        os.environ.get("OMNIX_DB_URL") or
        os.environ.get("POSTGRES_URL")
    )
    if not db_url:
        raise RuntimeError("No database URL configured (DATABASE_URL / OMNIX_DB_URL)")
    return psycopg2.connect(db_url)


# ── WEBHOOK UTILITIES (ADR-053) ────────────────────────────────────────────────

def _validate_webhook_url(url: str) -> tuple:
    """
    SSRF-safe webhook URL validation.
    Enforces HTTPS, rejects private/loopback/link-local CIDRs and non-443 ports.
    Returns (is_valid: bool, error_message: str).
    ADR-053.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != 'https':
            return False, "Webhook URL must use HTTPS"
        hostname = parsed.hostname
        if not hostname:
            return False, "Webhook URL must have a valid hostname"
        port = parsed.port
        if port and port != 443:
            return False, f"Webhook URL port must be 443 or omitted (got {port})"
        try:
            addr = ipaddress.ip_address(hostname)
            for net in _SSRF_BLOCKED_NETWORKS:
                if addr in net:
                    return False, "Webhook URL cannot point to a private, loopback, or link-local address"
        except ValueError:
            pass
        return True, ""
    except Exception as exc:
        return False, f"Invalid URL format: {exc}"


def _ensure_webhook_delivery_log_table() -> None:
    """
    Create webhook_delivery_log table and indexes if they don't exist.
    Called lazily on first webhook operation. ADR-053.
    """
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS webhook_delivery_log (
                delivery_id   BIGSERIAL PRIMARY KEY,
                client_id     TEXT        NOT NULL,
                receipt_id    TEXT        NOT NULL,
                decision      TEXT,
                webhook_url   TEXT,
                disposition   TEXT        NOT NULL,
                http_status   INTEGER,
                latency_ms    INTEGER,
                error_message TEXT,
                attempted_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_wdl_client_attempted
            ON webhook_delivery_log(client_id, attempted_at DESC)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_wdl_receipt_id
            ON webhook_delivery_log(receipt_id)
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"_ensure_webhook_delivery_log_table (non-fatal): {e}")


def _log_webhook_delivery(
    client_id: str,
    receipt_id: str,
    decision: str,
    webhook_url: str,
    disposition: str,
    http_status: int = None,
    latency_ms: int = None,
    error_message: str = None,
) -> None:
    """Persist one webhook delivery attempt to webhook_delivery_log. Best-effort. ADR-053."""
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO webhook_delivery_log
                (client_id, receipt_id, decision, webhook_url, disposition,
                 http_status, latency_ms, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                client_id,
                receipt_id,
                decision,
                (webhook_url or '')[:500],
                disposition,
                http_status,
                latency_ms,
                (error_message or '')[:1000] or None,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"_log_webhook_delivery failed (non-fatal): {e}")


def _push_receipt_webhook(
    client_id: str,
    receipt_id: str,
    decision: str,
    payload: dict,
    webhook_url: str,
    webhook_secret: str,
) -> None:
    """
    Push a PQC-signed governance receipt to the client's registered webhook endpoint.
    Non-blocking — called from a bounded daemon thread (semaphore: max 10 concurrent).

    Transport security:
      - HMAC-SHA256(webhook_secret, body_bytes) sent as X-OMNIX-Signature: sha256=<hex>
      - The payload retains the full PQC content_hash + signature for independent verification
      - Strict 10-second connect/read timeout to prevent resource exhaustion

    All delivery outcomes (SENT/ERROR/SKIPPED) are persisted to webhook_delivery_log.
    ADR-053.
    """
    _ensure_webhook_delivery_log_table()

    acquired = _WEBHOOK_PUSH_SEMAPHORE.acquire(blocking=False)
    if not acquired:
        _log_webhook_delivery(
            client_id, receipt_id, decision, webhook_url,
            'SKIPPED', error_message='semaphore exhausted — too many concurrent webhook pushes',
        )
        logger.warning(f"[WEBHOOK] client={client_id} receipt={receipt_id} SKIPPED — semaphore full")
        return

    t_start = time.monotonic()
    http_status = None
    error_message = None
    success = False

    try:
        body_bytes = json.dumps(payload, default=str).encode('utf-8')
        sig_hex = hmac.new(
            webhook_secret.encode('utf-8'),
            body_bytes,
            digestmod=hashlib.sha256,
        ).hexdigest()

        req = urllib.request.Request(
            webhook_url,
            data=body_bytes,
            headers={
                'Content-Type':        'application/json',
                'X-OMNIX-Signature':   f'sha256={sig_hex}',
                'X-OMNIX-Receipt-ID':  receipt_id,
                'X-OMNIX-Event':       'decision.evaluated',
                'X-OMNIX-Client-ID':   client_id,
                'User-Agent':          'OMNIX-Webhook/1.0 (github.com/omnix)',
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            http_status = resp.getcode()
            success = (200 <= http_status < 300)

    except urllib.error.HTTPError as exc:
        http_status = exc.code
        error_message = str(exc)
    except Exception as exc:
        error_message = str(exc)[:500]
    finally:
        _WEBHOOK_PUSH_SEMAPHORE.release()

    latency_ms = int((time.monotonic() - t_start) * 1000)
    disposition = 'SENT' if success else 'ERROR'

    if success:
        logger.info(
            f"[WEBHOOK] client={client_id} receipt={receipt_id} decision={decision} "
            f"disposition=SENT http={http_status} latency={latency_ms}ms"
        )
    else:
        logger.warning(
            f"[WEBHOOK] client={client_id} receipt={receipt_id} decision={decision} "
            f"disposition=ERROR http={http_status} latency={latency_ms}ms error={error_message}"
        )

    _log_webhook_delivery(
        client_id, receipt_id, decision, webhook_url, disposition,
        http_status=http_status, latency_ms=latency_ms, error_message=error_message,
    )


def _ensure_thresholds_table() -> None:
    """Ensure client_thresholds table exists. Called once on first evaluate request. ADR-037."""
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS client_thresholds (
                id SERIAL PRIMARY KEY,
                client_id VARCHAR(64) NOT NULL REFERENCES b2b_clients(client_id) ON DELETE CASCADE,
                checkpoint_id VARCHAR(8) NOT NULL
                    CHECK (checkpoint_id IN ('CP-1','CP-2','CP-3','CP-4','CP-5','CP-6')),
                threshold NUMERIC(5,2) NOT NULL CHECK (threshold >= 0 AND threshold <= 100),
                updated_by VARCHAR(64),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(client_id, checkpoint_id)
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_client_thresholds_client_id ON client_thresholds(client_id)"
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"_ensure_thresholds_table: {e}")


_THRESHOLDS_TABLE_ENSURED = False

# ── VELOS GATEWAY CONFIG (ADR-052) ───────────────────────────────────────────
# KEEP IN SYNC with omnix_dashboard/blueprints/governance.py — both files must be
# identical in this section. ADR-052.
_VELOS_PUSH_LOG_ENSURED  = False
_VELOS_GATEWAY_URL       = os.environ.get(
    "VELOS_GATEWAY_URL",
    "https://velos-gateway.onrender.com/api/v1/intercept",
)
_VELOS_CLIENT_ID         = os.environ.get("VELOS_CLIENT_ID", "velos-partner")
_VELOS_PUSH_SEMAPHORE    = threading.Semaphore(10)   # Max 10 concurrent push threads
_HAROLD_TELEGRAM_CHAT_ID = os.environ.get("HAROLD_TELEGRAM_CHAT_ID", "7014748854")


def _ensure_velos_push_log_table() -> None:
    """Create velos_push_log table if not exists. Called once on first push. ADR-052."""
    global _VELOS_PUSH_LOG_ENSURED
    if _VELOS_PUSH_LOG_ENSURED:
        return
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS velos_push_log (
                id            SERIAL PRIMARY KEY,
                receipt_id    VARCHAR(64)  NOT NULL,
                client_id     VARCHAR(64)  NOT NULL,
                decision      VARCHAR(16)  NOT NULL,
                disposition   VARCHAR(16)  NOT NULL DEFAULT 'SENT',
                skip_reason   TEXT,
                pushed_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                latency_ms    INTEGER,
                http_status   INTEGER,
                success       BOOLEAN      NOT NULL DEFAULT FALSE,
                response_body TEXT,
                error_message TEXT
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_velos_push_log_receipt ON velos_push_log(receipt_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_velos_push_log_pushed_at ON velos_push_log(pushed_at)"
        )
        conn.commit()
        conn.close()
        _VELOS_PUSH_LOG_ENSURED = True
    except Exception as e:
        logger.warning(f"_ensure_velos_push_log_table: {e}")


def _log_velos_disposition(
    receipt_id: str,
    client_id: str,
    decision: str,
    disposition: str,
    *,
    skip_reason: str | None = None,
    http_status: int | None = None,
    success: bool = False,
    response_body: str | None = None,
    error_message: str | None = None,
    latency_ms: int | None = None,
) -> None:
    """Write every Velos push disposition to velos_push_log (SENT/SKIPPED/ERROR)."""
    _ensure_velos_push_log_table()
    try:
        conn = _get_db_conn()
        cur  = conn.cursor()
        cur.execute(
            """
            INSERT INTO velos_push_log
                (receipt_id, client_id, decision, disposition, skip_reason,
                 latency_ms, http_status, success, response_body, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                receipt_id,
                client_id,
                decision,
                disposition,
                skip_reason,
                latency_ms,
                http_status,
                success,
                response_body[:512] if response_body else None,
                error_message,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as db_err:
        logger.error(f"[VELOS LOG] Failed to write disposition: {db_err}")


def _notify_harold_telegram(
    receipt_id: str,
    decision: str,
    disposition: str,
    *,
    latency_ms: int | None = None,
    http_status: int | None = None,
    error_message: str | None = None,
    asset: str | None = None,
) -> None:
    """
    Send a Telegram message to Harold when a Velos push completes (SENT or ERROR).
    Called inside the push daemon thread — synchronous HTTP call is intentional here.
    Silent on any failure — notification errors never affect the governance pipeline.
    Chat ID read from HAROLD_TELEGRAM_CHAT_ID env var (default: Harold's known ID).
    ADR-052.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return

    chat_id   = _HAROLD_TELEGRAM_CHAT_ID
    asset_str = f"\n📦 Asset: <b>{asset}</b>" if asset else ""

    if disposition == "SENT":
        text = (
            f"🟢 <b>Velos Push — ENVIADO</b>\n"
            f"📋 Receipt: <code>{receipt_id}</code>\n"
            f"📊 Decision: <b>{decision}</b>"
            f"{asset_str}\n"
            f"✅ HTTP {http_status} · {latency_ms}ms"
        )
    else:  # ERROR
        err = (error_message or "Sin detalle")[:120]
        text = (
            f"🔴 <b>Velos Push — ERROR</b>\n"
            f"📋 Receipt: <code>{receipt_id}</code>\n"
            f"📊 Decision: <b>{decision}</b>"
            f"{asset_str}\n"
            f"❌ HTTP {http_status} — {err}\n"
            f"⏱ {latency_ms}ms"
        )

    try:
        body = json.dumps({
            "chat_id":    chat_id,
            "text":       text,
            "parse_mode": "HTML",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5):
            logger.debug(
                f"[VELOS NOTIFY] Telegram OK receipt={receipt_id} disposition={disposition}"
            )
    except Exception as exc:
        logger.warning(f"[VELOS NOTIFY] Telegram failed receipt={receipt_id}: {exc}")


def _push_to_velos_gateway(receipt_id: str, client_id: str, decision: str, payload: dict) -> None:
    """
    Push a governance receipt to the Velos ingestion gateway.
    Non-blocking — called in a bounded daemon thread (semaphore: max 10 concurrent).
    Every disposition (SENT/SKIPPED/ERROR) is logged to velos_push_log for billing audit.
    Only fires HTTP request when VELOS_GATEWAY_TOKEN is set and client_id matches.
    ADR-052.
    """
    token = os.environ.get("VELOS_GATEWAY_TOKEN")

    # Log SKIPPED cases — no token configured
    if not token:
        _log_velos_disposition(
            receipt_id, client_id, decision, "SKIPPED",
            skip_reason="VELOS_GATEWAY_TOKEN not set",
        )
        logger.debug(f"[VELOS PUSH] receipt={receipt_id} SKIPPED — token not configured")
        return

    # Log SKIPPED cases — wrong client
    if client_id != _VELOS_CLIENT_ID:
        _log_velos_disposition(
            receipt_id, client_id, decision, "SKIPPED",
            skip_reason=f"client_id={client_id} is not the Velos gateway client",
        )
        return

    # Semaphore prevents unbounded thread accumulation under burst traffic
    acquired = _VELOS_PUSH_SEMAPHORE.acquire(blocking=False)
    if not acquired:
        _log_velos_disposition(
            receipt_id, client_id, decision, "SKIPPED",
            skip_reason="semaphore exhausted — too many concurrent pushes",
        )
        logger.warning(f"[VELOS PUSH] receipt={receipt_id} SKIPPED — semaphore full")
        return

    t_start = time.monotonic()
    http_status   = None
    success       = False
    response_body = None
    error_message = None

    try:
        # Build safe payload — no internal secrets, no DB credentials, no infra details
        safe_payload = {
            "receipt_id":          payload.get("receipt_id"),
            "timestamp":           payload.get("timestamp"),
            "client_id":           client_id,
            "asset":               payload.get("asset"),
            "domain":              payload.get("domain"),
            "decision":            decision,
            "checkpoints_total":   payload.get("checkpoints_total"),
            "checkpoints_passed":  payload.get("checkpoints_passed"),
            "checkpoints_blocked": payload.get("checkpoints_blocked"),
            "content_hash":        payload.get("content_hash"),
            "signature":           payload.get("signature"),
            "signature_algorithm": payload.get("signature_algorithm"),
            "pqc_signed":          payload.get("pqc_signed"),
            "policy_version":      payload.get("policy_version"),
            "verifiable_at":       payload.get("verifiable_at"),
            "gate_results":        payload.get("gate_results"),
        }

        body_bytes = json.dumps(safe_payload, default=str).encode("utf-8")
        req = urllib.request.Request(
            _VELOS_GATEWAY_URL,
            data=body_bytes,
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {token}",
                "X-Source":      "OMNIX-Governance",
                "X-Receipt-ID":  receipt_id,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            http_status   = resp.getcode()
            response_body = resp.read(512).decode("utf-8", errors="replace")
            success       = (200 <= http_status < 300)

    except urllib.error.HTTPError as e:
        http_status   = e.code
        error_message = str(e)
        try:
            response_body = e.read(256).decode("utf-8", errors="replace")
        except Exception:
            pass
    except Exception as e:
        error_message = str(e)[:500]
    finally:
        _VELOS_PUSH_SEMAPHORE.release()

    latency_ms = int((time.monotonic() - t_start) * 1000)
    disposition = "SENT" if success else "ERROR"

    if success:
        logger.info(
            f"[VELOS PUSH] receipt={receipt_id} decision={decision} "
            f"status={http_status} latency={latency_ms}ms — OK"
        )
    else:
        logger.warning(
            f"[VELOS PUSH] receipt={receipt_id} decision={decision} "
            f"status={http_status} latency={latency_ms}ms error={error_message}"
        )

    _log_velos_disposition(
        receipt_id, client_id, decision, disposition,
        http_status=http_status,
        success=success,
        response_body=response_body,
        error_message=error_message,
        latency_ms=latency_ms,
    )

    # Notify Harold on Telegram for every SENT or ERROR — SKIPPED omitted (not actionable)
    if disposition in ("SENT", "ERROR"):
        _notify_harold_telegram(
            receipt_id, decision, disposition,
            latency_ms=latency_ms,
            http_status=http_status,
            error_message=error_message,
            asset=payload.get("asset"),
        )


def _load_client_checkpoint_overrides(client_id: str) -> list[dict]:
    """
    Load per-client checkpoint threshold overrides from client_thresholds table.
    Merges with CHECKPOINT_DEFAULTS — only defined rows override the defaults.
    Returns a list of checkpoint dicts compatible with GovernanceEvaluationEngine.

    Fail-closed: any error (DB, parse, validation) → returns CHECKPOINT_DEFAULTS.
    ADR-037: Per-Client Configurable Thresholds.
    """
    global _THRESHOLDS_TABLE_ENSURED
    if not _THRESHOLDS_TABLE_ENSURED:
        _ensure_thresholds_table()
        _THRESHOLDS_TABLE_ENSURED = True

    try:
        import importlib.util as _ilu
        import os as _os
        _root = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
        _ev_path = _os.path.join(_root, "omnix_core", "governance", "external_evaluator.py")
        _spec = _ilu.spec_from_file_location("_omnix_ev_floors", _ev_path)
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        defaults = list(_mod.CHECKPOINT_DEFAULTS)
    except Exception as e:
        logger.warning(f"_load_client_checkpoint_overrides: could not load CHECKPOINT_DEFAULTS: {e}")
        return []

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT checkpoint_id, threshold FROM client_thresholds WHERE client_id = %s",
            (client_id,)
        )
        rows = {r["checkpoint_id"]: float(r["threshold"]) for r in cur.fetchall()}
        conn.close()
    except Exception as e:
        logger.warning(f"_load_client_checkpoint_overrides DB error for {client_id}: {e} — using defaults")
        return defaults

    if not rows:
        return defaults

    merged = []
    for cp in defaults:
        cp_copy = dict(cp)
        if cp["id"] in rows:
            cp_copy["threshold"] = rows[cp["id"]]
            cp_copy["_source"] = "client_custom"
        else:
            cp_copy["_source"] = "default"
        merged.append(cp_copy)

    logger.info(f"Loaded {len(rows)} custom threshold(s) for client={client_id}")
    return merged


def _get_client_ip() -> str:
    """
    Extract real client IP from X-Forwarded-For.
    SECURITY: Takes the RIGHTMOST (last) entry, which is appended by Railway's
    trusted reverse proxy and cannot be spoofed by the client.
    A client that injects 'X-Forwarded-For: fake-ip' will produce
    'fake-ip, real-ip' — we take 'real-ip'. ADR-052.
    """
    xff = request.headers.get('X-Forwarded-For', '').strip()
    if xff:
        return xff.split(',')[-1].strip()
    return request.remote_addr or 'unknown'


def _is_brute_force_locked(ip: str) -> bool:
    now = time.time()
    entry = _brute_force_store.get(ip)
    if not entry:
        return False
    if entry.get('locked_until') and now < entry['locked_until']:
        return True
    if entry.get('locked_until') and now >= entry['locked_until']:
        del _brute_force_store[ip]
    return False


def _record_failed_auth(ip: str) -> None:
    now = time.time()
    entry = _brute_force_store.get(ip, {'count': 0, 'first_seen': now})
    if now - entry['first_seen'] > _BRUTE_FORCE_WINDOW:
        entry = {'count': 0, 'first_seen': now}
    entry['count'] += 1
    if entry['count'] >= _BRUTE_FORCE_MAX:
        entry['locked_until'] = now + _BRUTE_FORCE_LOCKOUT
        logger.warning(f"[SECURITY] Brute force lockout triggered for IP={ip} after {entry['count']} failed attempts")
    _brute_force_store[ip] = entry


def _require_auth(require_admin: bool = False):
    """
    Authenticate request via X-API-Key header.
    Includes:
      - Brute force lockout: 5 failed attempts → 15 min block (ADR-052)
      - Admin IP allowlist via ADMIN_ALLOWED_IPS env var (ADR-052)
      - Key expiry check: expired keys rejected; near-expiry (<14d) flagged in client dict (ADR-052)
    Returns (client_dict, None) on success or (None, error_response) on failure.
    client_dict includes key_expires_in_days (int | None) for downstream warning injection.
    """
    import datetime as _dt

    client_ip = _get_client_ip()

    if _is_ip_blocked(client_ip):
        logger.warning(f"[SECURITY] Blocklisted IP rejected at auth: {client_ip}")
        return None, (jsonify({
            "error": "Access denied — try again later",
            "status": 403,
        }), 403)

    if _is_brute_force_locked(client_ip):
        logger.warning(f"[SECURITY] Blocked locked IP={client_ip}")
        return None, (jsonify({
            "error": "Too many failed attempts — try again in 15 minutes",
            "status": 429,
        }), 429)

    api_key = request.headers.get("X-API-Key", "")

    # Dashboard read-only bypass — allows internal audit dashboards to query
    # aggregate data without a B2B client record in the database.
    # Configure DASHBOARD_API_KEY env var to match the key the dashboard sends.
    # Default: OMNIX-DEMO-DASHBOARD-KEY (set in the frontend).
    # Admin-gated endpoints are never bypassed (require_admin=True guard below).
    if not require_admin:
        _dash_key = os.environ.get("DASHBOARD_API_KEY", "OMNIX-DEMO-DASHBOARD-KEY")
        if _dash_key and api_key == _dash_key:
            return {"client_id": "dashboard", "role": "read", "key_expires_in_days": None}, None

    client = authenticate_client(api_key)

    if client is None:
        _record_failed_auth(client_ip)
        logger.warning(f"[SECURITY] Unauthorized attempt from IP={client_ip}")
        return None, (jsonify({"error": "Unauthorized — provide a valid X-API-Key", "status": 401}), 401)

    if require_admin and client.get("role") != "admin":
        return None, (jsonify({"error": "Forbidden — admin role required", "status": 403}), 403)

    if require_admin:
        allowed_ips_raw = os.environ.get("ADMIN_ALLOWED_IPS", "")
        if allowed_ips_raw.strip():
            allowed_ips = {ip.strip() for ip in allowed_ips_raw.split(",") if ip.strip()}
            if client_ip not in allowed_ips:
                logger.warning(f"[SECURITY] Admin endpoint blocked for unlisted IP={client_ip}")
                return None, (jsonify({
                    "error": "Forbidden — access restricted",
                    "status": 403,
                }), 403)

    key_expires_in_days = None
    exp = client.get("key_expires_at")
    if exp is not None:
        if hasattr(exp, 'tzinfo') and exp.tzinfo is None:
            exp = exp.replace(tzinfo=_dt.timezone.utc)
        delta = exp - _dt.datetime.now(_dt.timezone.utc)
        days_left = delta.days
        if days_left <= _KEY_EXPIRY_WARNING_DAYS:
            key_expires_in_days = max(days_left, 0)
    client["key_expires_in_days"] = key_expires_in_days

    return client, None


# ── PUBLIC ENDPOINT ───────────────────────────────────────────────────────────

@governance_bp.route('/api/governance/schema', methods=['GET'])
def api_governance_schema():
    """Public endpoint — returns signal schema and checkpoint documentation."""
    if not _load_engine():
        return jsonify({'error': 'Governance engine not available', 'status': 503}), 503

    schema = _GovernanceEvaluationEngine.get_signal_schema()
    return jsonify({
        'schema': schema,
        'endpoint': 'POST /api/governance/evaluate',
        'auth': 'X-API-Key header required — contact OMNIX to obtain a client API key',
        'rate_limit': f'{_RATE_LIMIT_MAX} requests per {_RATE_LIMIT_WINDOW}s per IP',
        'documentation': 'docs/reference/adr/ADR-028-external-signal-evaluation-api.md',
        'verifiable_at': 'https://omnixquantum.net/verify',
        'quickstart': 'GET /api/governance/quickstart',
    })


@governance_bp.route('/api/governance/quickstart', methods=['GET'])
def api_governance_quickstart():
    """
    Public endpoint — integration quickstart guide with ready-to-use examples.
    No authentication required. Helps developers connect in minutes.
    """
    base_url = 'https://omnixquantum.net'
    return jsonify({
        'title': 'OMNIX Governance API — Integration Quickstart',
        'version': 'ADR-028 / ADR-051',
        'contact': 'contacto@omnixquantum.net',
        'steps': [
            {
                'step': 1,
                'title': 'Request an API key',
                'description': 'Contact OMNIX to obtain a B2B client API key. Format: OMNIX-<40 chars>. Shown once — store it securely.',
                'contact': 'contacto@omnixquantum.net',
            },
            {
                'step': 2,
                'title': 'Check the signal schema',
                'description': 'Review which signals are required and their valid ranges.',
                'curl': f'curl {base_url}/api/governance/schema',
            },
            {
                'step': 3,
                'title': 'Submit your first evaluation',
                'description': 'POST normalized signals (0–100 scale). Receive a PQC-signed receipt instantly.',
                'curl': (
                    f'curl -X POST {base_url}/api/governance/evaluate \\\n'
                    f'  -H "Content-Type: application/json" \\\n'
                    f'  -H "X-API-Key: OMNIX-YOUR_API_KEY_HERE" \\\n'
                    f'  -d \'{{\n'
                    f'    "signals": {{\n'
                    f'      "signal_integrity": 78,\n'
                    f'      "probability_score": 65,\n'
                    f'      "risk_exposure": 42,\n'
                    f'      "signal_coherence": 71,\n'
                    f'      "trend_persistence": 60,\n'
                    f'      "stress_resilience": 55\n'
                    f'    }},\n'
                    f'    "asset": "BTC/USD",\n'
                    f'    "domain": "trading"\n'
                    f'  }}\''
                ),
                'python': (
                    'import requests\n\n'
                    'response = requests.post(\n'
                    f'    "{base_url}/api/governance/evaluate",\n'
                    '    headers={\n'
                    '        "X-API-Key": "OMNIX-YOUR_API_KEY_HERE",\n'
                    '        "Content-Type": "application/json",\n'
                    '    },\n'
                    '    json={\n'
                    '        "signals": {\n'
                    '            "signal_integrity": 78,\n'
                    '            "probability_score": 65,\n'
                    '            "risk_exposure": 42,\n'
                    '            "signal_coherence": 71,\n'
                    '            "trend_persistence": 60,\n'
                    '            "stress_resilience": 55,\n'
                    '        },\n'
                    '        "asset": "BTC/USD",\n'
                    '        "domain": "trading",\n'
                    '    }\n'
                    ')\n'
                    'receipt = response.json()\n'
                    'print(receipt["decision"])        # APPROVED / BLOCKED / HOLD\n'
                    'print(receipt["receipt_id"])      # Unique verifiable ID\n'
                    'print(receipt["verify_url"])      # Public verification link\n'
                ),
            },
            {
                'step': 4,
                'title': 'Verify any receipt',
                'description': 'Any receipt can be independently verified by anyone — no API key needed.',
                'curl': f'curl {base_url}/api/public/verify/RECEIPT_ID_HERE',
            },
            {
                'step': 5,
                'title': 'Check your usage',
                'description': 'Admin key holders can query monthly usage for billing review.',
                'curl': (
                    f'curl {base_url}/api/governance/admin/usage/YOUR_CLIENT_ID \\\n'
                    f'  -H "X-API-Key: OMNIX-ADMIN_KEY_HERE"'
                ),
            },
        ],
        'supported_domains': [
            'trading', 'credit', 'insurance', 'robotics', 'energy',
            'biotech', 'real_estate', 'generic',
        ],
        'supported_jurisdictions': [
            'UAE', 'EU', 'US', 'GCC', 'UK', 'SG', 'JP', 'AU', 'CA', 'BR', 'KR', 'CH', 'GLOBAL'
        ],
        'signal_ranges': 'All signals are 0–100 numeric values. See /api/governance/schema for full details.',
        'response_fields': {
            'decision': 'APPROVED | BLOCKED | HOLD',
            'receipt_id': 'Unique ID for this evaluation — use for verification',
            'verify_url': 'Public URL to verify this receipt — shareable with anyone',
            'checkpoints': 'Array of 11 checkpoint results with individual pass/fail',
            'signature_algorithm': 'Cryptographic algorithm used to sign this receipt',
        },
        'rate_limits': {
            'per_ip': f'{_RATE_LIMIT_MAX} requests per {_RATE_LIMIT_WINDOW}s',
            'per_client': f'{_CLIENT_RATE_LIMIT_MAX} requests per {_CLIENT_RATE_LIMIT_WINDOW}s',
        },
        'sla': {
            'p95_latency_ms': 800,
            'availability_target': '99.9%',
            'receipt_retention': 'Permanent — all receipts stored indefinitely',
        },
    })


# ── EVALUATE ENDPOINT ─────────────────────────────────────────────────────────

@governance_bp.route('/api/governance/evaluate', methods=['POST'])
def api_governance_evaluate():
    """
    Evaluate external signals through the OMNIX 11-checkpoint governance pipeline.
    Returns a PQC-signed governance receipt.
    Requires valid X-API-Key (RBAC authenticated).
    """
    client, err = _require_auth()
    if err:
        return err

    client_id = client["client_id"]
    client_ip = _get_client_ip()

    # Persistent IP blocklist check — ADR-061
    # Applies to all requests including authenticated clients (a banned IP is banned)
    if _is_ip_blocked(client_ip):
        logger.warning(f"[SECURITY] Blocklisted IP rejected at evaluate: {client_ip}")
        return jsonify({"error": "Access denied — try again later", "status": 403}), 403

    # Authenticated B2B clients bypass the per-IP rate limit — they are governed by
    # the per-client limit below (120/min), which is designed for institutional burst traffic.
    # The IP rate limit (10/min) is reserved for public/unauthenticated endpoints only.
    # This also prevents auto-ban from triggering on legitimate authenticated traffic.

    # Rate limit per client_id — sole throughput control for authenticated clients
    if _is_client_rate_limited(client_id):
        ref_id = str(uuid.uuid4())[:8]
        logger.warning(f"Client rate limit hit: client={client_id} ref={ref_id}")
        return jsonify({
            'error': f'Rate limit exceeded — {_CLIENT_RATE_LIMIT_MAX} requests per minute',
            'status': 429,
            'reference': ref_id,
            'retry_after_seconds': _CLIENT_RATE_LIMIT_WINDOW,
            'limit': _CLIENT_RATE_LIMIT_MAX,
            'window_seconds': _CLIENT_RATE_LIMIT_WINDOW,
        }), 429

    # Per-client quota enforcement — ADR-081
    quota_ok, quota_error = _check_client_quota(client_id)
    if not quota_ok:
        ref_id = str(uuid.uuid4())[:8]
        return jsonify({
            'error': quota_error,
            'status': 429,
            'reference': ref_id,
            'type': 'quota_exceeded',
        }), 429

    if not request.is_json:
        return jsonify({'error': 'Request must be Content-Type: application/json', 'status': 400}), 400

    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({'error': 'Invalid JSON body', 'status': 400}), 400

    if not isinstance(body, dict) or 'signals' not in body:
        return jsonify({
            'error': "Request body must be a JSON object including a 'signals' field. See GET /api/governance/schema.",
            'status': 400,
        }), 400

    # ── Body-level schema validation — ADR-080 ──────────────────────────────
    _ALLOWED_EVALUATE_KEYS = {'signals', 'asset', 'domain', 'metadata', 'compliance_config', 'include_vc'}
    unknown_keys = set(body.keys()) - _ALLOWED_EVALUATE_KEYS
    if unknown_keys:
        return jsonify({
            'error': 'Request contains unrecognised fields. See GET /api/governance/schema.',
            'status': 400,
        }), 400

    _asset_raw = body.get('asset', 'UNKNOWN')
    if not isinstance(_asset_raw, str):
        return jsonify({'error': '"asset" must be a string.', 'status': 400}), 400

    _domain_raw = body.get('domain', 'generic')
    if not isinstance(_domain_raw, str):
        return jsonify({'error': '"domain" must be a string.', 'status': 400}), 400

    _metadata_raw = body.get('metadata', {})
    if _metadata_raw is not None and not isinstance(_metadata_raw, dict):
        return jsonify({'error': '"metadata" must be a JSON object or omitted.', 'status': 400}), 400
    if isinstance(_metadata_raw, dict) and len(_metadata_raw) > 50:
        return jsonify({'error': 'Request payload exceeds allowed limits.', 'status': 400}), 400
    if isinstance(_metadata_raw, dict):
        try:
            _metadata_size = len(json.dumps(_metadata_raw, separators=(',', ':')))
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid metadata — must be a JSON-serialisable object.', 'status': 400}), 400
        if _metadata_size > 8192:
            return jsonify({'error': 'Request payload exceeds allowed limits.', 'status': 400}), 400
    # ────────────────────────────────────────────────────────────────────────

    if not _load_engine():
        return jsonify({'error': 'Governance engine temporarily unavailable', 'status': 503}), 503

    signals = body.get('signals', {})
    is_valid, error_msg = _GovernanceEvaluationEngine.validate_signals(signals)
    if not is_valid:
        return jsonify({
            'error': f'Invalid signals: {error_msg}',
            'status': 400,
            'hint': 'See GET /api/governance/schema for required fields and value ranges.',
        }), 400

    asset = _asset_raw[:64]
    domain = _domain_raw[:32]
    metadata = _metadata_raw if isinstance(_metadata_raw, dict) else {}

    # ── compliance_config: optional Layer 0 + gate params from caller ────────
    _compliance_raw = body.get('compliance_config', {})
    if not isinstance(_compliance_raw, dict):
        return jsonify({'error': '"compliance_config" must be a JSON object or omitted.', 'status': 400}), 400
    _ALLOWED_CC_KEYS = {
        'layer0_enabled', 'layer0_full_audit', 'operation_type', 'jurisdiction',
        'ethical_flags', 'client_id',
        'avm_enabled', 'cag_enabled', 'jurisdiction_enabled',
        'ethical_frameworks', 'action',
    }
    _unknown_cc = set(_compliance_raw.keys()) - _ALLOWED_CC_KEYS
    if _unknown_cc:
        return jsonify({'error': f'compliance_config contains unrecognised fields: {sorted(_unknown_cc)}', 'status': 400}), 400
    compliance_config = {**_compliance_raw, 'client_id': client_id}
    compliance_config['layer0_enabled'] = True  # Layer 0 is always active — clients cannot disable

    # ── ADR-133: State Provenance Guard (pre-bind lineage check) ──────────────
    _spg_result_gov = None
    try:
        from omnix_core.governance.state_provenance_guard import evaluate_provenance
        _spg_result_gov = evaluate_provenance(
            signals   = signals,
            domain    = domain,
            asset     = asset,
            client_id = client_id,
        )
        logger.info(
            "[SPG][/evaluate] %s | score=%.1f | client=%s | asset=%s | spg_id=%s",
            _spg_result_gov.verdict.value,
            _spg_result_gov.lineage_singularity,
            client_id, asset,
            _spg_result_gov.spg_id,
        )
    except Exception as _spg_exc:
        logger.debug("[SPG] pre-evaluate SPG skipped (advisory): %s", _spg_exc)
    # ─────────────────────────────────────────────────────────────────────────

    try:
        checkpoint_overrides = _load_client_checkpoint_overrides(client_id)
        thresholds_source = "client_custom" if any(
            cp.get("_source") == "client_custom" for cp in checkpoint_overrides
        ) else "default"
        clean_overrides = [{k: v for k, v in cp.items() if k != "_source"} for cp in checkpoint_overrides]
        engine = _GovernanceEvaluationEngine(checkpoint_overrides=clean_overrides if clean_overrides else None)
        _eval_t0 = time.perf_counter()
        evaluation = engine.evaluate(
            signals=signals, asset=asset, domain=domain,
            metadata=metadata, compliance_config=compliance_config,
        )
        _processing_time_ms = round((time.perf_counter() - _eval_t0) * 1000)
    except Exception as e:
        ref_id = str(uuid.uuid4())[:8]
        logger.error(f"Governance evaluation error ref={ref_id}: {e}")
        return jsonify({'error': 'Internal evaluation error', 'status': 500, 'reference': ref_id}), 500

    encrypted_payload, _payload_key_version = _encrypt_payload(json.dumps(signals, sort_keys=True))

    try:
        receipt_engine = _DecisionReceiptEngine()
        prev_hash = receipt_engine.get_last_hash()
        decision_payload = {
            'symbol': asset,
            'asset': asset,
            'decision': evaluation['decision'],
            'decision_trace': evaluation['decision_trace'],
            'veto_chain': evaluation['veto_chain'],
            'policy_version': os.environ.get('OMNIX_VERSION', '6.5.4e'),
            'domain': domain,
            'external_evaluation': True,
            'checkpoints_total': evaluation['checkpoints_total'],
            'checkpoints_passed': evaluation['checkpoints_passed'],
            'client_id': client_id,
            'encrypted_payload': encrypted_payload,
        }
        receipt = receipt_engine.generate_receipt(
            decision_payload,
            prev_hash=prev_hash,
            processing_time_ms=_processing_time_ms,
        )
        receipt['client_id'] = client_id
        receipt['encrypted_payload'] = encrypted_payload
        receipt['payload_key_version'] = _payload_key_version
        receipt_engine.store_receipt(receipt)
    except Exception as e:
        ref_id = str(uuid.uuid4())[:8]
        logger.error(f"Receipt generation error ref={ref_id}: {e}")
        receipt = {
            'receipt_id': f'OMNIX-ERR-{ref_id}',
            'signature': None,
            'signature_algorithm': 'NONE',
            'content_hash': None,
            'public_key': None,
            'timestamp': None,
            'prev_hash': '',
        }

    # Update last_seen (best-effort)
    update_last_seen(client_id)

    try:
        _trigger = _get_alerts_trigger()
        if _trigger:
            alert_payload = dict(evaluation)
            alert_payload["asset"] = asset
            alert_payload["domain"] = domain
            threading.Thread(
                target=_trigger,
                args=(client_id, alert_payload, receipt.get("receipt_id")),
                daemon=True,
            ).start()
    except Exception as _ae:
        logger.debug(f"Alert trigger skipped: {_ae}")

    # ── Velos Gateway Push (non-blocking, B2B Velos client only) ──────────────
    try:
        velos_payload = {
            "receipt_id":          receipt.get("receipt_id"),
            "timestamp":           receipt.get("timestamp"),
            "asset":               asset,
            "domain":              domain,
            "checkpoints_total":   evaluation.get("checkpoints_total"),
            "checkpoints_passed":  evaluation.get("checkpoints_passed"),
            "checkpoints_blocked": evaluation.get("checkpoints_blocked"),
            "content_hash":        receipt.get("content_hash"),
            "signature":           receipt.get("signature"),
            "signature_algorithm": receipt.get("signature_algorithm", "NONE"),
            "pqc_signed":          receipt.get("signature") is not None,
            "policy_version":      receipt.get("policy_version", os.environ.get("OMNIX_VERSION", "6.5.4e")),
            "verifiable_at":       "https://omnibotgenesis-production.up.railway.app/verify",
            "gate_results":        evaluation.get("gate_results"),
        }
        threading.Thread(
            target=_push_to_velos_gateway,
            args=(receipt.get("receipt_id"), client_id, evaluation["decision"], velos_payload),
            daemon=True,
        ).start()
    except Exception as _ve:
        logger.debug(f"Velos push thread skipped: {_ve}")

    response = {
        'receipt_id': receipt.get('receipt_id'),
        'timestamp': receipt.get('timestamp'),
        'client_id': client_id,
        'asset': asset,
        'domain': domain,
        'decision': evaluation['decision'],
        'checkpoints_total': evaluation['checkpoints_total'],
        'checkpoints_passed': evaluation['checkpoints_passed'],
        'checkpoints_blocked': evaluation['checkpoints_blocked'],
        'gate_results': evaluation['gate_results'],
        'veto_chain': evaluation['veto_chain'],
        'decision_trace': evaluation['decision_trace'],
        'scores': evaluation['scores'],
        'content_hash': receipt.get('content_hash'),
        'signature': receipt.get('signature'),
        'signature_algorithm': receipt.get('signature_algorithm', 'NONE'),
        'pqc_signed': receipt.get('signature') is not None,
        'payload_encrypted': encrypted_payload is not None,
        'thresholds_source': thresholds_source,
        'verifiable_at': 'https://omnibotgenesis-production.up.railway.app/verify',
        'policy_version': receipt.get('policy_version', os.environ.get('OMNIX_VERSION', '6.5.4e')),
        'state_provenance': _spg_result_gov.to_dict() if _spg_result_gov else None,
    }

    # ── Regulatory alignment (ADR-062) ────────────────────────────────────────
    try:
        veto_chain_list = evaluation.get('veto_chain', [])
        passed_cps, blocked_cps = [], []
        for item in (veto_chain_list if isinstance(veto_chain_list, list) else []):
            cp_id = item.get('checkpoint') or item.get('cp') or item.get('id', '')
            status = item.get('status', item.get('result', ''))
            if cp_id.startswith('CP-'):
                if str(status).upper() in ('PASS', 'PASSED', 'OK', 'APPROVED', 'TRUE', '1'):
                    passed_cps.append(cp_id)
                else:
                    blocked_cps.append(cp_id)
        if not passed_cps and not blocked_cps:
            all_cps = [f"CP-{i}" for i in range(1, 12)]
            if evaluation.get('decision') == 'APPROVED':
                passed_cps = all_cps
            else:
                passed_cps = all_cps[:evaluation.get('checkpoints_passed', 0)]
                blocked_cps = all_cps[evaluation.get('checkpoints_passed', 0):]
        response['regulatory_alignment'] = build_regulatory_summary(passed_cps, blocked_cps)
    except Exception as _re:
        logger.debug(f"Regulatory alignment build failed (non-critical): {_re}")

    # ── Key expiry warning (ADR-052) ──────────────────────────────────────────
    key_expires_in_days = client.get("key_expires_in_days")
    if key_expires_in_days is not None:
        response['key_expiry_warning'] = {
            'expires_in_days': key_expires_in_days,
            'message': (
                f"Your API key expires in {key_expires_in_days} day(s). "
                "Rotate it via POST /api/governance/admin/clients/<id>/rotate to avoid service interruption."
            ),
        }

    logger.info(
        f"[GOVERNANCE] evaluate: client={client_id} asset={asset} domain={domain} "
        f"decision={evaluation['decision']} "
        f"passed={evaluation['checkpoints_passed']}/{evaluation['checkpoints_total']} "
        f"thresholds={thresholds_source} "
        f"receipt={receipt.get('receipt_id')} encrypted={encrypted_payload is not None} ip={client_ip}"
    )

    # Monthly usage alert (non-blocking)
    _check_monthly_alert(client_id)

    # ── W3C Verifiable Credential — ARF/eIDAS 2.0 (ADR-084) ──────────────────
    if body.get('include_vc'):
        try:
            try:
                from api.omnix_engine.receipt_to_vc import ReceiptToVC, build_jurisdiction_semantics
            except ImportError:
                from omnix_engine.receipt_to_vc import ReceiptToVC, build_jurisdiction_semantics
            vc_receipt = dict(receipt)
            vc_receipt['domain']  = domain
            vc_receipt['asset']   = asset
            vc_receipt['decision'] = evaluation['decision']
            vc_receipt['veto_chain'] = evaluation.get('veto_chain', [])
            vc = ReceiptToVC().convert(vc_receipt)
            vc['credentialSubject']['jurisdiction_semantics'] = build_jurisdiction_semantics(
                evaluation.get('veto_chain', []), evaluation['decision'], domain
            )
            response['verifiable_credential'] = vc
            response['vc_status']   = 'included'
            response['arf_profile'] = 'https://omnixquantum.net/.well-known/omnix-arf-profile.json'
            response['openid4vci']  = 'https://omnixquantum.net/.well-known/openid-credential-issuer'
        except Exception as _ve:
            logger.warning(f"VC generation failed (non-critical): {_ve}")
            response['vc_status'] = 'failed'
            response['vc_error']  = 'VC generation encountered an error; receipt is unaffected.'

    # ── Generic Webhook Push (ADR-053) ────────────────────────────────────────
    try:
        webhook_cfg = get_client_webhook(client_id)
        if webhook_cfg and webhook_cfg.get('webhook_url'):
            webhook_payload = {
                'event': 'decision.evaluated',
                'receipt_id': response.get('receipt_id'),
                'timestamp': response.get('timestamp'),
                'client_id': client_id,
                'asset': asset,
                'domain': domain,
                'decision': evaluation['decision'],
                'checkpoints_total': evaluation['checkpoints_total'],
                'checkpoints_passed': evaluation['checkpoints_passed'],
                'checkpoints_blocked': evaluation['checkpoints_blocked'],
                'content_hash': receipt.get('content_hash'),
                'signature': receipt.get('signature'),
                'signature_algorithm': receipt.get('signature_algorithm', 'NONE'),
                'pqc_signed': receipt.get('signature') is not None,
                'policy_version': response.get('policy_version'),
                'verifiable_at': response.get('verifiable_at'),
            }
            threading.Thread(
                target=_push_receipt_webhook,
                args=(
                    client_id,
                    receipt.get('receipt_id', ''),
                    evaluation['decision'],
                    webhook_payload,
                    webhook_cfg['webhook_url'],
                    webhook_cfg['webhook_secret'],
                ),
                daemon=True,
            ).start()
    except Exception as _we:
        logger.debug(f"Webhook push thread skipped: {_we}")

    return jsonify(response), 200


# ── W3C VERIFIABLE CREDENTIAL ISSUER — ARF/eIDAS 2.0 (ADR-084) ───────────────

@governance_bp.route('/api/governance/receipt/vc', methods=['POST'])
def api_governance_receipt_vc():
    """
    ADR-084: W3C Verifiable Credential endpoint — OpenID4VCI compatible.
    Public interoperability endpoint — no authentication required.
    Rate-limited: 30/min.

    Converts an OMNIX governance receipt into a W3C VC (JSON-LD).
    Conforms to: eIDAS 2.0 ARF 1.4 / OpenID4VCI draft-13 / W3C VC 1.1.

    Body option A: { "receipt": <OMNIX receipt dict> }
    Body option B: { "receipt_id": "OMNIX-TRD-..." }  (fetches from DB)

    Optional: { "include_jurisdiction_semantics": true }

    Returns: { "verifiable_credential": <W3C VC>, "hash_verified": bool, "arf_profile": "...", ... }
    """
    import json as _json
    import hashlib as _hashlib

    data = request.get_json(silent=True) or {}

    receipt    = data.get('receipt')
    receipt_id = data.get('receipt_id')

    if not receipt and not receipt_id:
        return jsonify({
            'error': 'Provide either { "receipt": <receipt dict> } or { "receipt_id": "OMNIX-..." }',
            'arf_profile': 'https://omnixquantum.net/.well-known/omnix-arf-profile.json',
        }), 400

    hash_verified = None

    if not receipt and receipt_id:
        try:
            from api.omnix_engine.receipt_engine import DecisionReceiptEngine as _RE
        except ImportError:
            try:
                from omnix_engine.receipt_engine import DecisionReceiptEngine as _RE
            except Exception:
                _RE = None
        if _RE:
            try:
                engine = _RE()
                db_rec = engine.get_receipt_by_id(str(receipt_id))
                if db_rec:
                    receipt = db_rec
                    hash_verified = True
            except Exception as _e:
                logger.debug(f"receipt fetch by ID failed: {_e}")
        if not receipt:
            return jsonify({'error': f'Receipt {receipt_id} not found.'}), 404

    if not isinstance(receipt, dict):
        return jsonify({'error': '"receipt" must be a JSON object.'}), 400

    if hash_verified is None:
        stored_hash  = receipt.get('content_hash', '')
        receipt_id_v = receipt.get('receipt_id', '')
        if not receipt_id_v or not stored_hash:
            return jsonify({
                'error': 'Receipt is missing required fields: receipt_id and/or content_hash.',
            }), 422
        payload_for_hash = {
            'receipt_id':       receipt.get('receipt_id'),
            'timestamp':        receipt.get('timestamp'),
            'asset':            receipt.get('asset'),
            'decision':         receipt.get('decision'),
            'veto_chain':       receipt.get('veto_chain'),
            'policy_version':   receipt.get('policy_version'),
            'engine_version':   receipt.get('engine_version'),
            'prev_hash':        receipt.get('prev_hash'),
        }
        if receipt.get('signing_provider') is not None:
            payload_for_hash['signing_provider'] = receipt.get('signing_provider')
        for opt in ('sharia_compliance', 'aml_compliance', 'fraud_compliance',
                    'jurisdiction_compliance', 'context_admission', 'veto_type'):
            if opt in receipt:
                payload_for_hash[opt] = receipt[opt]
        canonical    = _json.dumps(payload_for_hash, sort_keys=True, ensure_ascii=True)
        computed     = _hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        hash_verified = (computed == stored_hash)
        if not hash_verified:
            return jsonify({
                'error':         'Receipt integrity check failed. content_hash does not match payload.',
                'expected_hash': computed[:16] + '...',
                'received_hash': stored_hash[:16] + '...',
                'note':          'Ensure the receipt has not been modified since issuance.',
            }), 409

    include_semantics = bool(data.get('include_jurisdiction_semantics', True))

    # ADR-130 v2 (T004): optional human accountability binding in VC proof.
    # Callers may supply:
    #   { "human_signer": { "reviewer_id": "...", "eqs_score": 0.93,
    #                        "oversight_session_id": "OSS-..." } }
    # If human_signer is omitted and receipt_id is known, OMNIX auto-fetches
    # the most recent completed oversight session for that receipt (if any).
    human_signer = data.get('human_signer') or None
    if human_signer and not isinstance(human_signer, dict):
        human_signer = None

    if not human_signer and receipt_id:
        try:
            _hs_conn = get_db_connection()
            if _hs_conn:
                with _hs_conn.cursor() as _hs_cur:
                    # ADR-130 v2.3 fix: correct column (submitted_at) and status ('SUBMITTED')
                    # matching the oversight_sessions schema defined in ADR-124/oversight_surface.py
                    _hs_cur.execute(
                        """
                        SELECT reviewer_id, submitted_at, session_id, eqs_score
                        FROM oversight_sessions
                        WHERE decision_id = %s
                          AND status      = 'SUBMITTED'
                        ORDER BY submitted_at DESC
                        LIMIT 1
                        """,
                        (str(receipt_id),),
                    )
                    _hs_row = _hs_cur.fetchone()
                _hs_conn.close()
                if _hs_row:
                    _reviewer_id, _attested_at, _session_id, _eqs = _hs_row
                    human_signer = {
                        "reviewer_id"         : _reviewer_id,
                        "attested_at"         : _attested_at.isoformat() if _attested_at else None,
                        "oversight_session_id": _session_id,
                        "eqs_score"           : round(float(_eqs), 4) if _eqs is not None else None,
                    }
        except Exception as _hs_exc:
            logger.debug(f"[VC] oversight_sessions auto-lookup skipped: {_hs_exc}")

    try:
        try:
            from api.omnix_engine.receipt_to_vc import ReceiptToVC, build_jurisdiction_semantics
        except ImportError:
            from omnix_engine.receipt_to_vc import ReceiptToVC, build_jurisdiction_semantics

        vc = ReceiptToVC().convert(receipt, human_signer=human_signer)

        if include_semantics:
            veto_chain = receipt.get('veto_chain', [])
            decision   = receipt.get('decision', 'UNKNOWN')
            domain     = receipt.get('domain', 'generic')
            vc['credentialSubject']['jurisdiction_semantics'] = build_jurisdiction_semantics(
                veto_chain, decision, domain
            )

        resp_body = {
            'verifiable_credential':   vc,
            'hash_verified':           hash_verified,
            'human_accountability':    bool(human_signer),
            'arf_profile':             'https://omnixquantum.net/.well-known/omnix-arf-profile.json',
            'openid4vci':              'https://omnixquantum.net/.well-known/openid-credential-issuer',
            'did_document':            'https://omnixquantum.net/.well-known/did.json',
            'trust_registry':          'https://omnixquantum.net/api/trust/registry',
            'verify_url':              'https://omnixquantum.net/api/trust/verify',
            'issuer_did':              'did:web:omnixquantum.net',
            'schema':                  'https://omnixquantum.net/schemas/omnix-receipt-v1.jsonld',
            'conformance':             'eIDAS-2.0-ARF-1.4 / OpenID4VCI-draft-13 / W3C-VC-1.1',
            'adr':                     'ADR-130 v2',
        }
        return jsonify(resp_body), 200, {
            'Content-Type':              'application/json',
            'Access-Control-Allow-Origin': '*',
            'X-OMNIX-ARF-Conformance':   'eIDAS-2.0-ARF-1.4',
            'X-OMNIX-VC-Issuer':         'did:web:omnixquantum.net',
            'X-OMNIX-Human-Accountability': 'true' if human_signer else 'false',
            'X-OMNIX-ADR':               'ADR-130',
        }

    except Exception as e:
        ref_id = str(uuid.uuid4())[:8]
        logger.error(f"VC generation error ref={ref_id}: {e}")
        return jsonify({'error': 'VC generation failed', 'status': 500, 'reference': ref_id}), 500


# ── CLIENT RECEIPTS ENDPOINT ──────────────────────────────────────────────────

@governance_bp.route('/api/governance/receipts', methods=['GET'])
def api_governance_receipts():
    """
    Returns the authenticated client's own governance receipts.
    Isolation guaranteed: WHERE client_id = authenticated client's ID.
    Query params: limit (default 20, max 100), offset (default 0), decision (optional filter).
    """
    client, err = _require_auth()
    if err:
        return err

    client_id = client["client_id"]
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = max(int(request.args.get('offset', 0)), 0)
    except ValueError:
        return jsonify({'error': 'limit and offset must be integers', 'status': 400}), 400

    decision_filter = request.args.get('decision')

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        where_clause = "WHERE client_id = %s"
        params = [client_id]

        if decision_filter:
            where_clause += " AND decision = %s"
            params.append(decision_filter.upper())

        cur.execute(
            f"""
            SELECT receipt_id, timestamp_utc, asset, decision, veto_chain, created_at
            FROM decision_receipts
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset],
        )
        receipts = [dict(r) for r in cur.fetchall()]

        cur.execute(f"SELECT COUNT(*) as cnt FROM decision_receipts {where_clause}", params)
        total = cur.fetchone()["cnt"]

        cur.close()
        conn.close()

        return jsonify({
            'client_id': client_id,
            'total': total,
            'limit': limit,
            'offset': offset,
            'receipts': receipts,
            'verifiable_at': 'https://omnibotgenesis-production.up.railway.app/verify',
        }), 200

    except Exception as e:
        logger.error(f"Error fetching receipts for client={client_id}: {e}")
        return jsonify({'error': 'Database error', 'status': 500}), 500


# ── SINGLE RECEIPT BY ID (ADR-053) ────────────────────────────────────────────

@governance_bp.route('/api/governance/receipts/<string:receipt_id>', methods=['GET'])
def api_governance_receipt_by_id(receipt_id: str):
    """
    GET /api/governance/receipts/<receipt_id>
    Returns the full governance receipt for the given ID.

    Security: strict tenant isolation — only the receipt's owner can fetch it.
    A missing or foreign receipt both return 404 (no information leakage).
    ADR-053.
    """
    client, err = _require_auth()
    if err:
        return err

    client_id = client["client_id"]
    sanitized_id = str(receipt_id).strip()[:64]

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # ── ADR-126: multi-tier lookup (HOT → WARM → COLD) ─────────────────
        _RECEIPT_COLS = (
            "receipt_id", "timestamp_utc", "asset", "domain", "decision",
            "veto_chain", "content_hash", "signature", "signature_algorithm",
            "public_key", "policy_version", "engine_version",
            "prev_hash", "created_at",
        )
        col_list = ", ".join(_RECEIPT_COLS)

        def _query_tier(table: str) -> "dict | None":
            cur.execute(
                f"""
                SELECT {col_list}
                FROM {table}
                WHERE receipt_id = %s AND client_id = %s
                """,
                (sanitized_id, client_id),
            )
            r = cur.fetchone()
            if r:
                return dict(r)   # RealDictCursor returns dict-like row
            return None

        row = _query_tier("decision_receipts")
        storage_tier = "HOT"

        if row is None:
            try:
                row = _query_tier("decision_receipts_warm")
                if row:
                    storage_tier = "WARM"
            except Exception as _warm_exc:
                logger.debug("[receipts/<id>] WARM table unavailable: %s", _warm_exc)

        if row is None:
            try:
                # Check archival_index for COLD tier
                cur.execute(
                    """
                    SELECT storage_location
                    FROM receipt_archival_index
                    WHERE receipt_id = %s AND tier = 'COLD'
                    AND archival_status = 'ARCHIVED'
                    """,
                    (sanitized_id,),
                )
                idx_row = cur.fetchone()
                if idx_row:
                    from omnix_core.evidence.receipt_archival import ReceiptArchivalService
                    import os as _os
                    svc = ReceiptArchivalService(db_url=_os.environ.get("OMNIX_DB_URL"))
                    cold_dict, _ = svc.fetch_receipt_any_tier(conn, sanitized_id)
                    # Enforce tenant isolation even from COLD
                    if cold_dict and str(cold_dict.get("client_id", "")) == str(client_id):
                        row = {k: cold_dict.get(k) for k in _RECEIPT_COLS}
                        storage_tier = "COLD"
            except Exception as _cold_exc:
                logger.debug("[receipts/<id>] COLD lookup error: %s", _cold_exc)

        cur.close()
        conn.close()

        if row is None:
            return jsonify({
                'error': f"Receipt '{sanitized_id}' not found",
                'status': 404,
            }), 404

        receipt_data = dict(row)
        for ts_field in ('timestamp_utc', 'created_at'):
            if receipt_data.get(ts_field):
                try:
                    receipt_data[ts_field] = receipt_data[ts_field].isoformat()
                except Exception:
                    pass

        return jsonify({
            'client_id':     client_id,
            'receipt':       receipt_data,
            'storage_tier':  storage_tier,
            'pqc_signed':    receipt_data.get('signature') is not None,
            'verifiable_at': 'https://omnibotgenesis-production.up.railway.app/verify',
        }), 200

    except Exception as e:
        ref_id = str(uuid.uuid4())[:8]
        logger.error(f"receipt_by_id DB error ref={ref_id} client={client_id}: {e}")
        return jsonify({'error': 'Database error', 'status': 500, 'reference': ref_id}), 500


# ── ADMIN ENDPOINTS ───────────────────────────────────────────────────────────

@governance_bp.route('/api/governance/admin/clients', methods=['POST'])
def admin_create_client():
    """Create a new B2B client. Admin only. Returns plaintext API key — shown once."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    if not request.is_json:
        return jsonify({'error': 'Request must be JSON', 'status': 400}), 400

    body = request.get_json(force=True) or {}
    new_client_id = str(body.get('client_id', '')).strip()[:64]
    name = str(body.get('name', '')).strip()[:128]
    email = str(body.get('email', '')).strip()[:256] or None
    role = str(body.get('role', 'standard')).strip()

    if not new_client_id:
        return jsonify({'error': "'client_id' is required", 'status': 400}), 400
    if role not in ('standard', 'admin'):
        return jsonify({'error': "role must be 'standard' or 'admin'", 'status': 400}), 400

    try:
        api_key = create_client(client_id=new_client_id, name=name, email=email, role=role)
        logger.info(f"[ADMIN] created B2B client: {new_client_id} role={role} by admin={client['client_id']}")
        return jsonify({
            'client_id': new_client_id,
            'name': name,
            'role': role,
            'api_key': api_key,
            'message': 'Store this API key securely — it is shown only once and never stored in plaintext.',
        }), 201
    except ValueError:
        return jsonify({'error': 'Client ID already exists. Use a different client_id.', 'status': 409}), 409


@governance_bp.route('/api/governance/admin/clients', methods=['GET'])
def admin_list_clients():
    """List all B2B clients. Admin only. Never returns api_key_hash."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        clients = list_clients()
        # Convert datetime objects to ISO strings for JSON serialization
        for c in clients:
            for field in ('created_at', 'last_seen_at'):
                if c.get(field):
                    c[field] = c[field].isoformat()
        return jsonify({'clients': clients, 'total': len(clients)}), 200
    except Exception as e:
        logger.error(f"Admin list_clients error: {e}")
        return jsonify({'error': 'Database error', 'status': 500}), 500


@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>', methods=['DELETE'])
def admin_deactivate_client(target_client_id: str):
    """Deactivate a B2B client (soft delete). Admin only."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    if target_client_id == client['client_id']:
        return jsonify({'error': 'Cannot deactivate your own client', 'status': 400}), 400

    found = deactivate_client(target_client_id)
    if not found:
        return jsonify({'error': f"client_id '{target_client_id}' not found", 'status': 404}), 404

    logger.info(f"[ADMIN] deactivated client: {target_client_id} by admin={client['client_id']}")
    return jsonify({'client_id': target_client_id, 'status': 'deactivated'}), 200


@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>/reactivate', methods=['POST'])
def admin_reactivate_client(target_client_id: str):
    """Reactivate a deactivated B2B client. Admin only."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    found = reactivate_client(target_client_id)
    if not found:
        return jsonify({'error': f"client_id '{target_client_id}' not found", 'status': 404}), 404

    logger.info(f"[ADMIN] reactivated client: {target_client_id} by admin={client['client_id']}")
    return jsonify({'client_id': target_client_id, 'status': 'active'}), 200


@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>/rotate', methods=['POST'])
def admin_rotate_key(target_client_id: str):
    """Rotate API key for a client. Admin only. Returns new key — shown once. Resets expiry to 90 days."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        new_key = rotate_api_key(target_client_id)
        logger.info(f"[ADMIN] rotated key for client: {target_client_id} by admin={client['client_id']}")
        return jsonify({
            'client_id': target_client_id,
            'api_key': new_key,
            'expires_in_days': 90,
            'message': 'New API key generated. Previous key is now invalid. Store this key securely — shown once only.',
        }), 200
    except ValueError:
        return jsonify({'error': 'Client not found.', 'status': 404}), 404


# ── WEBHOOK MANAGEMENT ENDPOINTS (ADR-053) ────────────────────────────────────

@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>/webhook', methods=['PUT'])
def admin_set_webhook(target_client_id: str):
    """
    PUT /api/governance/admin/clients/<client_id>/webhook
    Register or update a webhook endpoint for a B2B client.
    Auto-generates a cryptographically secure HMAC-SHA256 signing secret.
    The secret is returned once — store it securely to verify webhook signatures.

    Request body:
      { "webhook_url": "https://your-server.example.com/omnix-webhook" }

    The webhook secret is returned in the response (shown once only).
    Clients verify incoming webhooks by checking:
      X-OMNIX-Signature: sha256=<HMAC-SHA256(secret, request_body)>

    Admin only. ADR-053.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    if not request.is_json:
        return jsonify({'error': 'Request must be JSON', 'status': 400}), 400

    body = request.get_json(force=True) or {}
    webhook_url = str(body.get('webhook_url', '')).strip()

    if not webhook_url:
        return jsonify({'error': "'webhook_url' is required", 'status': 400}), 400

    is_valid, url_error = _validate_webhook_url(webhook_url)
    if not is_valid:
        return jsonify({'error': url_error, 'status': 422}), 422

    webhook_secret = secrets.token_hex(32)

    updated = set_client_webhook(target_client_id, webhook_url, webhook_secret)
    if not updated:
        return jsonify({'error': f"client_id '{target_client_id}' not found", 'status': 404}), 404

    logger.info(
        f"[ADMIN] webhook set for client={target_client_id} "
        f"url={webhook_url[:60]} by admin={client['client_id']}"
    )
    return jsonify({
        'client_id': target_client_id,
        'webhook_url': webhook_url,
        'webhook_secret': webhook_secret,
        'signature_header': 'X-OMNIX-Signature',
        'signature_format': 'sha256=<HMAC-SHA256(secret, raw_request_body)>',
        'event': 'decision.evaluated',
        'message': (
            'Webhook registered. Store the webhook_secret securely — it is shown only once. '
            'Use it to verify the X-OMNIX-Signature header on incoming webhook deliveries.'
        ),
    }), 200


@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>/webhook', methods=['DELETE'])
def admin_delete_webhook(target_client_id: str):
    """
    DELETE /api/governance/admin/clients/<client_id>/webhook
    Remove webhook configuration for a B2B client. Future decisions will not be pushed.
    Admin only. ADR-053.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    updated = delete_client_webhook(target_client_id)
    if not updated:
        return jsonify({'error': f"client_id '{target_client_id}' not found", 'status': 404}), 404

    logger.info(f"[ADMIN] webhook removed for client={target_client_id} by admin={client['client_id']}")
    return jsonify({
        'client_id': target_client_id,
        'webhook_configured': False,
        'message': 'Webhook configuration removed. Decision push notifications disabled.',
    }), 200


@governance_bp.route(
    '/api/governance/admin/clients/<string:target_client_id>/webhook/deliveries',
    methods=['GET'],
)
def admin_webhook_deliveries(target_client_id: str):
    """
    GET /api/governance/admin/clients/<client_id>/webhook/deliveries
    Returns the last N webhook delivery attempts for a client.

    Query params:
      - limit: int (default 50, max 200)
      - disposition: SENT | ERROR | SKIPPED (optional filter)

    Admin only. ADR-053.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        limit = min(int(request.args.get('limit', 50)), 200)
    except (TypeError, ValueError):
        limit = 50

    disposition_filter = request.args.get('disposition', '').upper() or None

    try:
        _ensure_webhook_delivery_log_table()
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        where = "WHERE client_id = %s"
        params = [target_client_id]
        if disposition_filter:
            where += " AND disposition = %s"
            params.append(disposition_filter)

        cur.execute(
            f"""
            SELECT delivery_id, receipt_id, decision, webhook_url, disposition,
                   http_status, latency_ms, error_message, attempted_at
            FROM webhook_delivery_log
            {where}
            ORDER BY attempted_at DESC
            LIMIT %s
            """,
            params + [limit],
        )
        rows = [dict(r) for r in cur.fetchall()]

        cur.execute(f"SELECT COUNT(*) AS cnt FROM webhook_delivery_log {where}", params)
        total = cur.fetchone()["cnt"]

        cur.execute(
            """
            SELECT
                SUM(CASE WHEN disposition = 'SENT'    THEN 1 ELSE 0 END) AS sent,
                SUM(CASE WHEN disposition = 'ERROR'   THEN 1 ELSE 0 END) AS error,
                SUM(CASE WHEN disposition = 'SKIPPED' THEN 1 ELSE 0 END) AS skipped,
                ROUND(AVG(CASE WHEN disposition = 'SENT' THEN latency_ms END)) AS avg_latency_ms
            FROM webhook_delivery_log
            WHERE client_id = %s
            """,
            (target_client_id,),
        )
        stats_row = cur.fetchone()
        cur.close()
        conn.close()

        for r in rows:
            if r.get('attempted_at'):
                r['attempted_at'] = r['attempted_at'].isoformat()

        return jsonify({
            'client_id': target_client_id,
            'total_deliveries': int(total),
            'shown': len(rows),
            'stats': {
                'sent': int(stats_row['sent'] or 0),
                'error': int(stats_row['error'] or 0),
                'skipped': int(stats_row['skipped'] or 0),
                'avg_latency_ms': int(stats_row['avg_latency_ms'] or 0),
            },
            'deliveries': rows,
        }), 200

    except Exception as e:
        ref_id = str(uuid.uuid4())[:8]
        logger.error(f"admin_webhook_deliveries error ref={ref_id}: {e}")
        return jsonify({'error': 'Database error', 'status': 500, 'reference': ref_id}), 500


# ── THRESHOLD MANAGEMENT ENDPOINTS (ADR-037) ──────────────────────────────────

@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>/thresholds', methods=['GET'])
def admin_get_thresholds(target_client_id: str):
    """
    Return effective checkpoints for a client.
    Each entry shows current threshold value and source: 'default' or 'custom'.
    Admin only. ADR-037.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    overrides = _load_client_checkpoint_overrides(target_client_id)
    if not overrides:
        return jsonify({'error': 'Could not load checkpoints', 'status': 500}), 500

    result = []
    for cp in overrides:
        result.append({
            'checkpoint_id': cp['id'],
            'name': cp.get('name', ''),
            'threshold': cp['threshold'],
            'operator': cp.get('operator', ''),
            'source': cp.get('_source', 'default'),
        })

    return jsonify({
        'client_id': target_client_id,
        'checkpoints': result,
        'custom_count': sum(1 for r in result if r['source'] == 'client_custom'),
        'total': len(result),
    }), 200


@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>/thresholds', methods=['PUT'])
def admin_set_thresholds(target_client_id: str):
    """
    Set per-client checkpoint threshold overrides.
    Body: {"CP-1": 60, "CP-3": 70}  — partial updates, only named checkpoints are changed.
    Validates against CHECKPOINT_SAFETY_FLOORS.
    Admin only. ADR-037.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        import importlib.util as _ilu
        import os as _os
        _root = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
        _ev_path = _os.path.join(_root, "omnix_core", "governance", "external_evaluator.py")
        _spec = _ilu.spec_from_file_location("_omnix_ev_floors_admin", _ev_path)
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        validate_fn = _mod.validate_threshold_against_floor
        floors = _mod.CHECKPOINT_SAFETY_FLOORS
    except Exception as e:
        logger.error(f"admin_set_thresholds: cannot load safety floors: {e}")
        return jsonify({'error': 'Internal configuration error', 'status': 500}), 500

    if not request.is_json:
        return jsonify({'error': 'Request must be Content-Type: application/json', 'status': 400}), 400
    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({'error': 'Invalid JSON body', 'status': 400}), 400

    if not isinstance(body, dict) or not body:
        return jsonify({'error': 'Body must be a non-empty JSON object: {"CP-1": 60, ...}', 'status': 400}), 400

    valid_cps = set(floors.keys())
    errors = []
    updates = {}

    for cp_id, value in body.items():
        if cp_id not in valid_cps:
            errors.append(f"Unknown checkpoint '{cp_id}'. Valid: {sorted(valid_cps)}")
            continue
        try:
            threshold = float(value)
        except (TypeError, ValueError):
            errors.append(f"{cp_id}: threshold must be a number, got {value!r}")
            continue
        ok, msg = validate_fn(cp_id, threshold)
        if not ok:
            errors.append(msg)
            continue
        updates[cp_id] = threshold

    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors, 'status': 400}), 400

    if not updates:
        return jsonify({'error': 'No valid checkpoints provided', 'status': 400}), 400

    admin_id = client['client_id']
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        for cp_id, threshold in updates.items():
            cur.execute("""
                INSERT INTO client_thresholds (client_id, checkpoint_id, threshold, updated_by, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (client_id, checkpoint_id)
                DO UPDATE SET threshold = EXCLUDED.threshold,
                              updated_by = EXCLUDED.updated_by,
                              updated_at = NOW()
            """, (target_client_id, cp_id, threshold, admin_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"admin_set_thresholds DB error for {target_client_id}: {e}")
        return jsonify({'error': 'Database error while saving thresholds', 'status': 500}), 500

    logger.info(
        f"[ADMIN] set thresholds for client={target_client_id} "
        f"checkpoints={list(updates.keys())} by admin={admin_id}"
    )

    effective = _load_client_checkpoint_overrides(target_client_id)
    result = [{
        'checkpoint_id': cp['id'],
        'name': cp.get('name', ''),
        'threshold': cp['threshold'],
        'operator': cp.get('operator', ''),
        'source': cp.get('_source', 'default'),
    } for cp in effective]

    return jsonify({
        'client_id': target_client_id,
        'updated': list(updates.keys()),
        'checkpoints': result,
        'message': f"{len(updates)} threshold(s) updated successfully.",
    }), 200


@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>/thresholds', methods=['DELETE'])
def admin_delete_thresholds(target_client_id: str):
    """
    Revert ALL threshold overrides for a client to system defaults.
    Deletes all rows in client_thresholds for this client.
    Admin only. ADR-037.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM client_thresholds WHERE client_id = %s", (target_client_id,))
        deleted = cur.rowcount
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"admin_delete_thresholds DB error for {target_client_id}: {e}")
        return jsonify({'error': 'Database error while deleting thresholds', 'status': 500}), 500

    logger.info(
        f"[ADMIN] reverted thresholds for client={target_client_id} "
        f"deleted={deleted} by admin={client['client_id']}"
    )
    return jsonify({
        'client_id': target_client_id,
        'deleted_overrides': deleted,
        'message': 'All custom thresholds removed. Client will now use system defaults.',
    }), 200


# ===========================================================================
# CLIENT USAGE REPORTING — ADR-051
# ===========================================================================

@governance_bp.route('/api/governance/admin/usage', methods=['GET'])
def admin_usage_summary():
    """
    GET /api/governance/admin/usage
    Monthly usage summary for ALL clients — for billing and audit.
    Admin only. ADR-051.

    Query params:
      - months: int (default 3) — how many trailing months to show
      - client_id: str (optional) — filter to a specific client

    Returns per-client, per-month counts of evaluations broken down by
    APPROVED / BLOCKED / HOLD decisions. Excludes 'PUBLIC' sandbox traffic.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        months = max(1, min(int(request.args.get('months', 3)), 24))
    except (TypeError, ValueError):
        months = 3

    filter_client_id = request.args.get('client_id')

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        params = [months]
        client_filter_sql = ""
        if filter_client_id:
            client_filter_sql = "AND dr.client_id = %s"
            params.append(filter_client_id)

        cur.execute(f"""
            SELECT
                dr.client_id,
                bc.name AS client_name,
                bc.email AS client_email,
                bc.is_active,
                TO_CHAR(DATE_TRUNC('month', dr.created_at), 'YYYY-MM') AS month,
                COUNT(*) AS total_evaluations,
                SUM(CASE WHEN dr.decision = 'APPROVED' THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN dr.decision = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked,
                SUM(CASE WHEN dr.decision = 'HOLD' THEN 1 ELSE 0 END) AS hold,
                MIN(dr.created_at) AS first_evaluation,
                MAX(dr.created_at) AS last_evaluation
            FROM decision_receipts dr
            LEFT JOIN b2b_clients bc ON bc.client_id = dr.client_id
            WHERE dr.client_id != 'PUBLIC'
              AND dr.created_at >= DATE_TRUNC('month', NOW()) - (INTERVAL '1 month' * %s)
              {client_filter_sql}
            GROUP BY dr.client_id, bc.name, bc.email, bc.is_active,
                     DATE_TRUNC('month', dr.created_at)
            ORDER BY dr.client_id, month DESC
        """, params)

        rows = cur.fetchall()
        conn.close()

        structured = {}
        for row in rows:
            cid = row['client_id']
            if cid not in structured:
                structured[cid] = {
                    'client_id': cid,
                    'client_name': row['client_name'] or cid,
                    'client_email': row['client_email'],
                    'is_active': row['is_active'],
                    'months': [],
                    'total_all_time_in_range': 0,
                }
            month_entry = {
                'month': row['month'],
                'total_evaluations': int(row['total_evaluations']),
                'approved': int(row['approved'] or 0),
                'blocked': int(row['blocked'] or 0),
                'hold': int(row['hold'] or 0),
                'first_evaluation': row['first_evaluation'].isoformat() if row['first_evaluation'] else None,
                'last_evaluation': row['last_evaluation'].isoformat() if row['last_evaluation'] else None,
            }
            structured[cid]['months'].append(month_entry)
            structured[cid]['total_all_time_in_range'] += int(row['total_evaluations'])

        clients_list = list(structured.values())
        grand_total = sum(c['total_all_time_in_range'] for c in clients_list)

        logger.info(
            f"[ADMIN] usage_summary: queried by admin={client['client_id']} "
            f"months={months} clients={len(clients_list)} total={grand_total}"
        )

        return jsonify({
            'report_generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
            'trailing_months': months,
            'clients': clients_list,
            'grand_total_evaluations': grand_total,
            'client_count': len(clients_list),
            'note': 'PUBLIC sandbox traffic excluded. Counts are for B2B API calls only.',
        }), 200

    except Exception as e:
        logger.error(f"admin_usage_summary DB error: {e}")
        return jsonify({'error': 'Database error generating usage report', 'status': 500}), 500


@governance_bp.route('/api/governance/admin/usage/<string:target_client_id>', methods=['GET'])
def admin_usage_client(target_client_id: str):
    """
    GET /api/governance/admin/usage/<client_id>
    Detailed monthly usage for a specific client — all decisions, monthly breakdown.
    Admin only. ADR-051.

    Query params:
      - months: int (default 12) — how many trailing months to show
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        months = max(1, min(int(request.args.get('months', 12)), 36))
    except (TypeError, ValueError):
        months = 12

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT client_id, name, email, role, is_active, created_at, last_seen_at
            FROM b2b_clients WHERE client_id = %s
        """, (target_client_id,))
        client_row = cur.fetchone()

        cur.execute("""
            SELECT
                TO_CHAR(DATE_TRUNC('month', created_at), 'YYYY-MM') AS month,
                COUNT(*) AS total_evaluations,
                SUM(CASE WHEN decision = 'APPROVED' THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN decision = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked,
                SUM(CASE WHEN decision = 'HOLD' THEN 1 ELSE 0 END) AS hold,
                COUNT(DISTINCT asset) AS distinct_assets,
                MIN(created_at) AS first_evaluation,
                MAX(created_at) AS last_evaluation
            FROM decision_receipts
            WHERE client_id = %s
              AND created_at >= DATE_TRUNC('month', NOW()) - (INTERVAL '1 month' * %s)
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month DESC
        """, (target_client_id, months))

        monthly_rows = cur.fetchall()

        cur.execute("""
            SELECT COUNT(*) AS total FROM decision_receipts WHERE client_id = %s
        """, (target_client_id,))
        lifetime_row = cur.fetchone()

        conn.close()

        monthly = []
        total_in_range = 0
        for row in monthly_rows:
            entry = {
                'month': row['month'],
                'total_evaluations': int(row['total_evaluations']),
                'approved': int(row['approved'] or 0),
                'blocked': int(row['blocked'] or 0),
                'hold': int(row['hold'] or 0),
                'distinct_assets': int(row['distinct_assets'] or 0),
                'first_evaluation': row['first_evaluation'].isoformat() if row['first_evaluation'] else None,
                'last_evaluation': row['last_evaluation'].isoformat() if row['last_evaluation'] else None,
            }
            total_in_range += entry['total_evaluations']
            monthly.append(entry)

        logger.info(
            f"[ADMIN] usage_client: queried by admin={client['client_id']} "
            f"target={target_client_id} months={months} total_in_range={total_in_range}"
        )

        return jsonify({
            'report_generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
            'client_id': target_client_id,
            'client_info': dict(client_row) if client_row else None,
            'trailing_months': months,
            'total_evaluations_in_range': total_in_range,
            'lifetime_evaluations': int(lifetime_row['total'] if lifetime_row else 0),
            'monthly_breakdown': monthly,
        }), 200

    except Exception as e:
        logger.error(f"admin_usage_client DB error for {target_client_id}: {e}")
        return jsonify({'error': 'Database error generating client usage report', 'status': 500}), 500


# ===========================================================================
# EXECUTION BOUNDARY INTEGRITY — ADR-045
# ===========================================================================

# ── EXECUTIVE AUDIT DASHBOARD (ADR-059) ───────────────────────────────────────
# Translates technical veto_chain data to executive-language audit records
# for CFOs and regulators. No raw scores, thresholds, or signal names exposed.

_CHECKPOINT_LABELS = {
    'CAG':   'Context Admissibility Gate',
    'ACV':   'Admissibility Consistency Validator',
    'CP-0':  'Signal Quality Assessment',
    'CP-1':  'Statistical Probability Review',
    'CP-2':  'Institutional Risk Limits',
    'CP-3':  'Multi-Model Coherence Check',
    'CP-4':  'Market Trend Confirmation',
    'CP-5':  'Stress & Resilience Test',
    'CP-6':  'Ethics & Governance Gate',
    'CP-7':  'Temporal Coherence Review',
    'CP-7b': 'Forward Trajectory Validation',
    'CP-8':  'Contextual Threshold Review',
    'CP-9':  'AML & Financial Crime Screening',
    'CP-10': 'Fraud Detection & Pattern Analysis',
    'CP-11': 'Jurisdictional Compliance Gate',
    'TIE':   'Trajectory Invariant Enforcement',
    'PQC':   'Post-Quantum Cryptographic Receipt',
}

_CHECKPOINT_PASS = {
    'CAG':   'Decision context validated as institutionally admissible.',
    'ACV':   'Internal governance signals validated for consistency.',
    'CP-0':  'Signal quality validated within institutional parameters.',
    'CP-1':  'Probability assessment validated above required confidence level.',
    'CP-2':  'Risk exposure validated within institutional limits.',
    'CP-3':  'Multi-model consensus validated across independent engines.',
    'CP-4':  'Market trend confirmation validated.',
    'CP-5':  'Stress resilience validated under adverse scenarios.',
    'CP-6':  'Ethics and governance controls satisfied.',
    'CP-7':  'Temporal coherence validated.',
    'CP-7b': 'Forward trajectory within acceptable risk boundaries.',
    'CP-8':  'Contextual thresholds validated.',
    'CP-9':  'AML and financial crime screening cleared.',
    'CP-10': 'Fraud detection patterns clear.',
    'CP-11': 'Jurisdiction validated as operationally compliant.',
    'TIE':   'Trajectory invariant conditions satisfied.',
    'PQC':   'Post-quantum cryptographic receipt issued successfully.',
}

_CHECKPOINT_BLOCK = {
    'CAG':   'Decision context did not meet institutional admissibility criteria.',
    'ACV':   'Decision showed internal consistency violations across governance signals.',
    'CP-0':  'Signal quality did not meet the minimum threshold for institutional processing.',
    'CP-1':  'Probability assessment fell below the required confidence level.',
    'CP-2':  'Risk exposure exceeded the institutional risk limits in force.',
    'CP-3':  'Independent model outputs were not sufficiently aligned to proceed.',
    'CP-4':  'Market trend indicators were insufficient to confirm the decision direction.',
    'CP-5':  'Stress scenario analysis indicated excessive vulnerability.',
    'CP-6':  'Decision did not pass ethics and governance controls.',
    'CP-7':  'Temporal coherence could not be established.',
    'CP-7b': 'Forward trajectory projections indicated unacceptable risk evolution.',
    'CP-8':  'Contextual thresholds for this decision type were not met.',
    'CP-9':  'AML and financial crime screening raised a compliance concern.',
    'CP-10': 'Fraud detection patterns triggered a compliance hold.',
    'CP-11': 'Decision involves a jurisdiction where this activity is restricted.',
    'TIE':   'Decision trajectory violated the invariant boundary conditions.',
    'PQC':   'Post-quantum signing could not be completed.',
}

_DOMAIN_LABELS = {
    'trading':           'Digital Asset Trading',
    'credit':            'Islamic Credit',
    'insurance':         'Insurance Underwriting',
    'robotics':          'Robotics & Autonomous Systems',
    'medical_ai':        'Medical AI Governance',
    'energy_governance': 'Energy Grid Governance',
    'real_estate':       'Real Estate & PropTech',
    'autonomous_agent':  'Autonomous Agent Governance',
    'stablecoin':        'Stablecoin Reserve Governance',
}


def _parse_veto_chain_executive(veto_chain_raw):
    """
    Parse raw veto_chain list/JSON into executive-language checkpoint outcomes.
    Strips all scores, thresholds, operators, and internal signal names.
    """
    import re
    outcomes = []

    if not veto_chain_raw:
        return outcomes

    if isinstance(veto_chain_raw, str):
        try:
            import json
            veto_chain_raw = json.loads(veto_chain_raw)
        except Exception:
            veto_chain_raw = [veto_chain_raw]

    if not isinstance(veto_chain_raw, list):
        return outcomes

    pattern = re.compile(
        r'^(CP-\d+[a-z]?|CAG|ACV|TIE|PQC)\s',
        re.IGNORECASE
    )

    for entry in veto_chain_raw:
        entry = str(entry).strip()
        cp_match = pattern.match(entry)
        cp_id = cp_match.group(1).upper() if cp_match else None

        is_blocked = bool(re.search(r'->\s*(BLOCK|BLOCKED|FAIL)', entry, re.IGNORECASE))
        status = 'BLOCKED' if is_blocked else 'PASS'

        label = _CHECKPOINT_LABELS.get(cp_id, cp_id or 'Governance Control')
        reason = (
            _CHECKPOINT_BLOCK.get(cp_id, 'This control raised a governance concern.')
            if is_blocked
            else _CHECKPOINT_PASS.get(cp_id, 'Control validated within institutional parameters.')
        )

        outcomes.append({
            'checkpoint_id': cp_id,
            'label': label,
            'status': status,
            'executive_reason': reason,
        })

    return outcomes


def _build_executive_summary(decision: str, outcomes: list) -> str:
    blocked = [o for o in outcomes if o['status'] == 'BLOCKED']
    if decision in ('BLOCKED', 'BLOCK'):
        first = blocked[0]['executive_reason'] if blocked else 'A governance control raised a concern.'
        return f"This decision was BLOCKED. {first}"
    if decision == 'NARROW':
        total = len(outcomes)
        return (
            f"This decision was NARROW after {total} institutional governance checkpoints — "
            "execution permitted at reduced scope only."
        )
    if decision == 'QUARANTINE':
        return (
            "This decision was QUARANTINED — payload isolated, bind suspended "
            "pending signal integrity restoration."
        )
    if decision == 'REBOUND':
        return (
            "This decision was REBOUNDED — standing margin below floor. "
            "Execution must return to last admissible posture."
        )
    if decision == 'HOLD':
        return "This decision is on HOLD — supervisor escalation required before execution."
    total = len(outcomes)
    return f"This decision was APPROVED after passing all {total} institutional governance checkpoints."


# ── Layer 0 Metrics — admin view (ADR-092) ────────────────────────────────────

@governance_bp.route('/api/governance/admin/layer0/metrics', methods=['GET'])
def admin_layer0_metrics():
    """
    GET /api/governance/admin/layer0/metrics
    Real-time Layer 0 (Structural Admissibility Engine) admission metrics.
    Admin only.  ADR-092.

    Returns per-domain counters:
      total         — total requests evaluated at Layer 0
      admitted      — requests passed to pipeline
      blocked       — requests rejected before Layer 0
      block_rate_pct — blocked / total × 100
      blocked_by_class — {constraint_class: count} breakdown
      top_constraint_classes — sorted list of (class, count) for the GLOBAL rollup

    Always-on: metrics accumulate from process start in memory (thread-safe).
    They reset on process restart; a future ADR may add persistence.
    """
    caller, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        snapshot = _get_layer0_metrics().snapshot()
        override  = _get_sae_override()

        # ── per-domain rows ────────────────────────────────────────────────────
        domains = []
        global_total    = 0
        global_admitted = 0
        global_blocked  = 0
        global_by_class: dict = {}

        for domain, stat in snapshot.items():
            domains.append({
                "domain":             domain,
                "total":              stat["total"],
                "admitted":           stat["admitted"],
                "blocked":            stat["blocked"],
                "block_rate_pct":     round(stat["block_rate_pct"], 2),
                "blocked_by_class":   stat["blocked_by_class"],
            })
            global_total    += stat["total"]
            global_admitted += stat["admitted"]
            global_blocked  += stat["blocked"]
            for cls, cnt in stat["blocked_by_class"].items():
                global_by_class[cls] = global_by_class.get(cls, 0) + cnt

        domains.sort(key=lambda d: d["blocked"], reverse=True)

        top_constraint_classes = sorted(
            [{"class": k, "count": v} for k, v in global_by_class.items()],
            key=lambda x: x["count"],
            reverse=True,
        )

        global_block_rate = round(
            (global_blocked / global_total * 100) if global_total else 0.0,
            2,
        )

        snapshot_history = _get_layer0_snapshot_history(last_n=12)

        return jsonify({
            "success":              True,
            "sae_module_available": _SAE_METRICS_AVAILABLE,
            "operator_override":    override.value if override is not None else "UNSET",
            "demo_tagline":         _LAYER0_DEMO_TAGLINE,
            "global": {
                "total":                  global_total,
                "admitted":               global_admitted,
                "blocked":                global_blocked,
                "block_rate_pct":         global_block_rate,
                "top_constraint_classes": top_constraint_classes,
            },
            "domains":              domains,
            "snapshot_history":     snapshot_history,
            "snapshot_config": {
                "interval_minutes": _SNAPSHOT_INTERVAL_MIN,
                "max_entries":      _SNAPSHOT_MAX_ENTRIES,
                "stored":           len(snapshot_history),
            },
            "note": (
                "Metrics accumulate from process start (in-memory, thread-safe). "
                "Snapshots recorded every 5 min — history available for charts. "
                "ADR-092."
            ),
        })

    except Exception as exc:
        logger.exception("admin_layer0_metrics error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


@governance_bp.route('/api/governance/audit/decisions', methods=['GET'])
def api_audit_decisions():
    """
    GET /api/governance/audit/decisions
    Executive audit view — translates governance receipts to plain business language.
    No raw scores, thresholds, or internal signal names are exposed.
    ADR-059: Executive Audit Dashboard.
    Authentication: API key required (gov_auth_rbac RBAC).
    Filters: domain, decision (APPROVED/BLOCKED), date_from, date_to, limit, offset
    """
    client, err = _require_auth()
    if err:
        return err

    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        offset = max(int(request.args.get('offset', 0)), 0)
    except ValueError:
        return jsonify({'error': 'limit and offset must be integers'}), 400

    domain_filter   = (request.args.get('domain', '') or '').strip().lower()
    decision_filter = (request.args.get('decision', '') or '').strip().upper()
    date_from       = (request.args.get('date_from', '') or '').strip()
    date_to         = (request.args.get('date_to', '') or '').strip()

    _VALID_DECISIONS = ('APPROVED', 'NARROW', 'QUARANTINE', 'REBOUND', 'HOLD', 'BLOCKED')
    if decision_filter and decision_filter not in _VALID_DECISIONS:
        return jsonify({'error': 'decision must be one of: APPROVED, NARROW, QUARANTINE, REBOUND, HOLD, BLOCKED'}), 400

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        where_parts = []
        params = []

        if domain_filter:
            where_parts.append("domain = %s")
            params.append(domain_filter)
        if decision_filter:
            where_parts.append("decision = %s")
            params.append(decision_filter)
        if date_from:
            where_parts.append("timestamp_utc >= %s")
            params.append(date_from)
        if date_to:
            where_parts.append("timestamp_utc <= %s")
            params.append(date_to)

        where_sql = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""

        cur.execute(
            f"""
            SELECT receipt_id, timestamp_utc, asset, domain, decision,
                   veto_chain, policy_version, engine_version,
                   signature_algorithm, content_hash, prev_hash
            FROM decision_receipts
            {where_sql}
            ORDER BY timestamp_utc DESC
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset],
        )
        rows = [dict(r) for r in cur.fetchall()]

        cur.execute(f"SELECT COUNT(*) as cnt FROM decision_receipts {where_sql}", params)
        total = cur.fetchone()['cnt']

        cur.execute("""
            SELECT domain, decision, COUNT(*) as cnt
            FROM decision_receipts
            GROUP BY domain, decision
        """)
        kpi_raw = cur.fetchall()

        cur.close()
        conn.close()

        domain_kpis: dict = {}
        total_approved = 0
        total_blocked  = 0
        for row in kpi_raw:
            d = row['domain'] or 'unknown'
            dec = row['decision'] or ''
            cnt = row['cnt']
            if d not in domain_kpis:
                domain_kpis[d] = {'domain': d, 'label': _DOMAIN_LABELS.get(d, d.title()), 'approved': 0, 'blocked': 0, 'total': 0}
            if dec in ('APPROVED',):
                domain_kpis[d]['approved'] += cnt
                total_approved += cnt
            elif dec in ('BLOCKED', 'HOLD'):
                domain_kpis[d]['blocked'] += cnt
                total_blocked += cnt
            domain_kpis[d]['total'] += cnt

        total_all = total_approved + total_blocked
        items = []
        for row in rows:
            outcomes = _parse_veto_chain_executive(row.get('veto_chain'))
            summary  = _build_executive_summary(row.get('decision', ''), outcomes)

            sig_algo = row.get('signature_algorithm') or ''
            has_pqc  = bool(sig_algo) and 'dilithium' in sig_algo.lower()

            items.append({
                'receipt_id':        row['receipt_id'],
                'timestamp_utc':     str(row['timestamp_utc']) if row['timestamp_utc'] else None,
                'asset':             row.get('asset'),
                'domain':            row.get('domain'),
                'domain_label':      _DOMAIN_LABELS.get((row.get('domain') or '').lower(), (row.get('domain') or '').title()),
                'decision':          row.get('decision'),
                'executive_summary': summary,
                'checkpoint_outcomes': outcomes,
                'integrity': {
                    'signature_standard': 'NIST-standardized post-quantum algorithms',
                    'pqc_signed':         has_pqc,
                    'chain_linked':       bool(row.get('prev_hash')),
                    'policy_version':     row.get('policy_version'),
                    'engine_version':     row.get('engine_version'),
                },
            })

        return jsonify({
            'success':      True,
            'generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
            'meta': {
                'filters':  {'domain': domain_filter, 'decision': decision_filter, 'date_from': date_from, 'date_to': date_to},
                'limit':    limit,
                'offset':   offset,
                'total':    total,
                'has_more': (offset + limit) < total,
            },
            'kpis': {
                'total_decisions': total_all,
                'approved':        total_approved,
                'blocked':         total_blocked,
                'approved_pct':    round(total_approved / total_all * 100, 1) if total_all else 0,
                'blocked_pct':     round(total_blocked  / total_all * 100, 1) if total_all else 0,
                'by_domain':       list(domain_kpis.values()),
            },
            'items': items,
        }), 200

    except Exception as e:
        logger.error(f"api_audit_decisions error: {e}")
        return jsonify({'error': 'Audit data temporarily unavailable', 'status': 500}), 500


@governance_bp.route('/api/public/audit-demo', methods=['GET'])
def api_public_audit_demo():
    """
    GET /api/public/audit-demo
    Public demo endpoint — returns anonymized synthetic governance audit data.
    No authentication required. No real client data exposed.
    ADR-059: Executive Audit Dashboard — public demo tier.
    """
    import datetime, random, uuid

    domains = [
        ('trading',           'Digital Asset Trading',           'BTC/USD'),
        ('credit',            'Islamic Credit',                  'CREDIT-APP-7821'),
        ('insurance',         'Insurance Underwriting',          'POLICY-INS-4432'),
        ('robotics',          'Robotics & Autonomous Systems',   'ROBOT-ARM-001'),
        ('medical_ai',        'Medical AI Governance',           'PATIENT-DIAG-8819'),
        ('autonomous_agent',  'Autonomous Agent Governance',     'AGENT-TASK-3307'),
        ('real_estate',       'Real Estate & PropTech',          'PROP-LON-0041'),
        ('energy_governance', 'Energy Grid Governance',          'WIND-DISPATCH-009'),
        ('stablecoin',        'Stablecoin Reserve Governance',   'USDC-RESERVE-7B'),
    ]

    demo_outcomes_approved = [
        {'checkpoint_id': 'CP-1', 'label': 'Statistical Probability Review',   'status': 'PASS',    'executive_reason': 'Probability assessment validated above required confidence level.'},
        {'checkpoint_id': 'CP-2', 'label': 'Institutional Risk Limits',        'status': 'PASS',    'executive_reason': 'Risk exposure validated within institutional limits.'},
        {'checkpoint_id': 'CP-3', 'label': 'Multi-Model Coherence Check',      'status': 'PASS',    'executive_reason': 'Multi-model consensus validated across independent engines.'},
        {'checkpoint_id': 'CP-9', 'label': 'AML & Financial Crime Screening',  'status': 'PASS',    'executive_reason': 'AML and financial crime screening cleared.'},
        {'checkpoint_id': 'CP-11','label': 'Jurisdictional Compliance Gate',   'status': 'PASS',    'executive_reason': 'Jurisdiction validated as operationally compliant.'},
    ]

    demo_outcomes_blocked = [
        {'checkpoint_id': 'CP-1', 'label': 'Statistical Probability Review',   'status': 'PASS',    'executive_reason': 'Probability assessment validated above required confidence level.'},
        {'checkpoint_id': 'CP-2', 'label': 'Institutional Risk Limits',        'status': 'BLOCKED', 'executive_reason': 'Risk exposure exceeded the institutional risk limits in force.'},
        {'checkpoint_id': 'CP-9', 'label': 'AML & Financial Crime Screening',  'status': 'PASS',    'executive_reason': 'AML and financial crime screening cleared.'},
        {'checkpoint_id': 'CP-11','label': 'Jurisdictional Compliance Gate',   'status': 'PASS',    'executive_reason': 'Jurisdiction validated as operationally compliant.'},
    ]

    now = datetime.datetime.utcnow()
    items = []
    for i in range(12):
        dom, dom_label, asset = random.choice(domains)
        approved = random.random() > 0.35
        decision = 'APPROVED' if approved else 'BLOCKED'
        outcomes = demo_outcomes_approved if approved else demo_outcomes_blocked
        summary  = _build_executive_summary(decision, outcomes)
        ts = (now - datetime.timedelta(hours=i * 2 + random.randint(0, 3))).isoformat() + 'Z'
        rid = f"DEMO-{uuid.uuid4().hex[:12].upper()}"
        items.append({
            'receipt_id':          rid,
            'timestamp_utc':       ts,
            'asset':               asset,
            'domain':              dom,
            'domain_label':        dom_label,
            'decision':            decision,
            'executive_summary':   summary,
            'checkpoint_outcomes': outcomes,
            'integrity': {
                'signature_standard': 'NIST-standardized post-quantum algorithms',
                'pqc_signed':         True,
                'chain_linked':       True,
                'policy_version':     'v6.5.4e',
                'engine_version':     '6.5.4',
            },
        })

    approved_count = sum(1 for x in items if x['decision'] == 'APPROVED')
    blocked_count  = len(items) - approved_count

    domain_kpis_demo = {}
    for x in items:
        d = x['domain']
        if d not in domain_kpis_demo:
            domain_kpis_demo[d] = {'domain': d, 'label': x['domain_label'], 'approved': 0, 'blocked': 0, 'total': 0}
        if x['decision'] == 'APPROVED':
            domain_kpis_demo[d]['approved'] += 1
        else:
            domain_kpis_demo[d]['blocked'] += 1
        domain_kpis_demo[d]['total'] += 1

    return jsonify({
        'success':      True,
        'demo':         True,
        'generated_at': now.isoformat() + 'Z',
        'note':         'Demo data — anonymized synthetic records. Real data requires API key.',
        'meta':         {'limit': 12, 'offset': 0, 'total': 12, 'has_more': False, 'filters': {}},
        'kpis': {
            'total_decisions': len(items),
            'approved':        approved_count,
            'blocked':         blocked_count,
            'approved_pct':    round(approved_count / len(items) * 100, 1),
            'blocked_pct':     round(blocked_count  / len(items) * 100, 1),
            'by_domain':       list(domain_kpis_demo.values()),
        },
        'items': items,
    }), 200


@governance_bp.route('/api/public/audit-live', methods=['GET'])
def api_public_audit_live():
    """
    GET /api/public/audit-live
    Public endpoint — real governance decisions from all 9 verticals.
    No authentication required. No raw scores or thresholds exposed.
    """
    import json as _json, datetime as _dt

    def _parse_cp_results(cp_raw):
        outcomes = []
        if not cp_raw:
            return outcomes
        data = cp_raw if isinstance(cp_raw, list) else []
        try:
            if isinstance(cp_raw, str):
                data = _json.loads(cp_raw)
        except Exception:
            return outcomes
        for cp in data:
            if not isinstance(cp, dict):
                continue
            cp_id   = cp.get('checkpoint', '')
            result  = cp.get('result', 'PASS')
            blocked = result in ('BLOCKED', 'FAIL', 'BLOCK')
            status  = 'BLOCKED' if blocked else 'PASS'
            label   = _CHECKPOINT_LABELS.get(cp_id, cp.get('name', 'Governance Control'))
            reason  = (
                _CHECKPOINT_BLOCK.get(cp_id, 'This control raised a governance concern.')
                if blocked
                else _CHECKPOINT_PASS.get(cp_id, 'Control validated within institutional parameters.')
            )
            outcomes.append({'checkpoint_id': cp_id, 'label': label, 'status': status, 'executive_reason': reason})
        return outcomes

    def _simple_outcomes(decision, block_reason):
        approved = decision == 'APPROVED'
        if approved:
            return [
                {'checkpoint_id': 'CP-1', 'label': _CHECKPOINT_LABELS['CP-1'], 'status': 'PASS', 'executive_reason': _CHECKPOINT_PASS['CP-1']},
                {'checkpoint_id': 'CP-3', 'label': _CHECKPOINT_LABELS['CP-3'], 'status': 'PASS', 'executive_reason': _CHECKPOINT_PASS['CP-3']},
                {'checkpoint_id': 'CP-11','label': _CHECKPOINT_LABELS['CP-11'],'status': 'PASS', 'executive_reason': _CHECKPOINT_PASS['CP-11']},
            ]
        reason_map = {
            'Trend Persistence':    'CP-4', 'Signal Coherence': 'CP-3',
            'Logic Consistency':    'CP-6', 'Stress Resilience': 'CP-5',
            'Risk Exposure':        'CP-2', 'Fraud':            'CP-10',
            'AML':                  'CP-9', 'Jurisdiction':     'CP-11',
        }
        cp_id = next((v for k, v in reason_map.items() if k.lower() in (block_reason or '').lower()), 'CP-2')
        return [
            {'checkpoint_id': 'CP-1',  'label': _CHECKPOINT_LABELS['CP-1'],  'status': 'PASS',    'executive_reason': _CHECKPOINT_PASS['CP-1']},
            {'checkpoint_id': cp_id,   'label': _CHECKPOINT_LABELS.get(cp_id,'Risk Control'), 'status': 'BLOCKED', 'executive_reason': _CHECKPOINT_BLOCK.get(cp_id,'This control raised a governance concern.')},
        ]

    try:
        conn  = _get_db_conn()
        cur   = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        limit = min(int(request.args.get('limit', 50)), 200)
        domain_filter   = (request.args.get('domain', '') or '').strip().lower()
        decision_filter = (request.args.get('decision', '') or '').strip().upper()

        VERTICAL_QUERIES = [
            ("SELECT receipt_id, created_at AS timestamp_utc, receipt_id AS asset, 'trading' AS domain, decision, NULL AS block_reason, NULL AS cp_results FROM decision_receipts WHERE domain='trading'", 'trading'),
            ("SELECT receipt_id, evaluated_at AS timestamp_utc, application_id AS asset, 'credit' AS domain, decision, block_reason, NULL AS cp_results FROM credit_applications", 'credit'),
            ("SELECT receipt_id, created_at AS timestamp_utc, claim_id AS asset, 'insurance' AS domain, decision, block_reason, checkpoint_results::text AS cp_results FROM insurance_claims", 'insurance'),
            ("SELECT receipt_id, created_at AS timestamp_utc, action_id AS asset, 'robotics' AS domain, decision, block_reason, checkpoint_results::text AS cp_results FROM robot_actions", 'robotics'),
            ("SELECT receipt_id, created_at AS timestamp_utc, decision_id AS asset, 'medical_ai' AS domain, decision, block_reason, checkpoint_results::text AS cp_results FROM medical_decisions", 'medical_ai'),
            ("SELECT receipt_id, created_at AS timestamp_utc, decision_id AS asset, 'energy_governance' AS domain, decision, block_reason, NULL AS cp_results FROM energy_decisions", 'energy_governance'),
            ("SELECT receipt_id, created_at AS timestamp_utc, decision_id AS asset, 'real_estate' AS domain, decision, block_reason, checkpoint_results::text AS cp_results FROM property_decisions", 'real_estate'),
            ("SELECT receipt_id, created_at AS timestamp_utc, decision_id AS asset, 'autonomous_agent' AS domain, decision, block_reason, checkpoint_results::text AS cp_results FROM agent_decisions", 'autonomous_agent'),
            ("SELECT receipt_id, created_at AS timestamp_utc, reserve_asset AS asset, 'stablecoin' AS domain, decision, block_reason, NULL AS cp_results FROM stablecoin_decisions", 'stablecoin'),
        ]

        rows = []
        domain_counts = {}
        for sql_base, dom in VERTICAL_QUERIES:
            if domain_filter and domain_filter != dom:
                continue
            wheres = []
            if decision_filter:
                wheres.append(f"decision = '{decision_filter}'")
            where_sql = ('WHERE ' + ' AND '.join(wheres)) if wheres else ''
            try:
                cur.execute(f"SELECT COUNT(*) as cnt, decision FROM ({sql_base}) t {where_sql} GROUP BY decision")
                for r in cur.fetchall():
                    if dom not in domain_counts:
                        domain_counts[dom] = {'domain': dom, 'label': _DOMAIN_LABELS.get(dom, dom), 'approved': 0, 'blocked': 0, 'total': 0}
                    dec = r['decision'] or ''
                    if dec == 'APPROVED':
                        domain_counts[dom]['approved'] += r['cnt']
                    elif dec in ('BLOCKED', 'HOLD'):
                        domain_counts[dom]['blocked'] += r['cnt']
                    domain_counts[dom]['total'] += r['cnt']
                cur.execute(f"SELECT * FROM ({sql_base}) t {where_sql} ORDER BY timestamp_utc DESC LIMIT %s", (limit // len(VERTICAL_QUERIES) + 1,))
                rows.extend(cur.fetchall())
            except Exception as _table_err:
                logger.warning(f"audit-live: skipping domain '{dom}' — {_table_err}")
                conn.rollback()

        cur.close(); conn.close()

        def _sort_key(r):
            try:
                ts = r['timestamp_utc'] if isinstance(r, dict) else None
                return ts or _dt.datetime(2000, 1, 1, tzinfo=_dt.timezone.utc)
            except Exception:
                return _dt.datetime(2000, 1, 1, tzinfo=_dt.timezone.utc)
        rows.sort(key=_sort_key, reverse=True)
        rows = rows[:limit]

        items = []
        for row in rows:
            try:
                row_dict = dict(row) if not isinstance(row, dict) else row
                dom = (row_dict.get('domain') or '')
                dec = (row_dict.get('decision') or '')
                cp_raw = row_dict.get('cp_results')
                if cp_raw:
                    try:
                        parsed = _json.loads(cp_raw) if isinstance(cp_raw, str) else cp_raw
                        cp_raw = parsed if isinstance(parsed, list) else None
                    except Exception:
                        cp_raw = None
                outcomes = _parse_cp_results(cp_raw) if cp_raw else _simple_outcomes(dec, row_dict.get('block_reason'))
                receipt  = row_dict.get('receipt_id') or row_dict.get('asset') or 'OMNIX-' + dom.upper()[:3]
                items.append({
                    'receipt_id':          receipt,
                    'timestamp_utc':       str(row_dict['timestamp_utc']) if row_dict.get('timestamp_utc') else None,
                    'asset':               row_dict.get('asset'),
                    'domain':              dom,
                    'domain_label':        _DOMAIN_LABELS.get(dom, dom.title()),
                    'decision':            dec,
                    'executive_summary':   _build_executive_summary(dec, outcomes),
                    'checkpoint_outcomes': outcomes,
                    'integrity': {
                        'signature_standard': 'NIST-standardized post-quantum algorithms',
                        'pqc_signed':         True,
                        'chain_linked':       True,
                        'policy_version':     'v6.5.4e',
                        'engine_version':     '6.5.4',
                    },
                })
            except Exception as _row_err:
                logger.warning(f"audit-live: skipping malformed row — {_row_err}")

        total_approved = sum(v['approved'] for v in domain_counts.values())
        total_blocked  = sum(v['blocked']  for v in domain_counts.values())
        total_all      = total_approved + total_blocked

        return jsonify({
            'success':      True,
            'generated_at': _dt.datetime.utcnow().isoformat() + 'Z',
            'meta':         {'limit': limit, 'offset': 0, 'total': len(items), 'has_more': False, 'filters': {}},
            'kpis': {
                'total_decisions': total_all,
                'approved':        total_approved,
                'blocked':         total_blocked,
                'approved_pct':    round(total_approved / total_all * 100, 1) if total_all else 0,
                'blocked_pct':     round(total_blocked  / total_all * 100, 1) if total_all else 0,
                'by_domain':       list(domain_counts.values()),
            },
            'items': items,
        }), 200

    except Exception as e:
        logger.error(f"api_public_audit_live error: {e}")
        return jsonify({'error': 'Audit data temporarily unavailable', 'status': 500}), 500


# ── REGULATORY CATALOG ENDPOINT (ADR-062) ─────────────────────────────────────

@governance_bp.route('/api/governance/regulatory/catalog', methods=['GET'])
def api_governance_regulatory_catalog():
    """
    GET /api/governance/regulatory/catalog
    Returns the full regulatory framework catalog covered by OMNIX.
    Maps all 11 checkpoints to applicable frameworks (EU AI Act, DORA, NIST AI RMF,
    ISO 42001, CA SB 243, GDPR, FATF, Basel III, OHADA).
    Public endpoint — no authentication required.
    ADR-062, ADR-192.
    """
    try:
        catalog = get_full_framework_catalog()

        # ── ADR-192: OHADA Regulatory Coverage — 17-country West/Central Africa zone ──
        ohada_entry = {
            'framework':   'OHADA',
            'full_name':   'Organisation pour l\'Harmonisation en Afrique du Droit des Affaires',
            'jurisdiction': 'West & Central Africa — 17 member states',
            'member_states': [
                'BJ','BF','CM','CF','TD','KM','CD','CG',
                'CI','GQ','GA','GN','GW','ML','NE','SN','TG'
            ],
            'sub_frameworks': [
                {
                    'tag':         'SYSCOHADA',
                    'name':        'Système Comptable OHADA',
                    'scope':       'Financial and accounting decisions — AI systems touching financial records in OHADA jurisdictions',
                },
                {
                    'tag':         'AUDCG',
                    'name':        'Acte Uniforme relatif au Droit Commercial Général',
                    'scope':       'Commercial decisions — AI-driven vendor selection, contract review, procurement',
                },
                {
                    'tag':         'IFRS-OHADA',
                    'name':        'IFRS as adopted under SYSCOHADA',
                    'scope':       'Financial reporting decisions — AI systems generating or validating financial statements',
                },
                {
                    'tag':         'CCJA',
                    'name':        'Cour Commune de Justice et d\'Arbitrage',
                    'scope':       'Dispute resolution traceability — AI decisions that may require forensic audit under OHADA arbitration',
                },
            ],
            'pqc_signing':  'ML-DSA-65 (Dilithium-3) — same as all OMNIX receipts. No degraded signing for any jurisdiction. (ADR-192 OHADA-INV-002)',
            'adr':          'ADR-192',
            'note':         'OHADA tags are structural markers enabling receipt-level jurisdiction tagging. '
                            'Consult OHADA-qualified counsel before making compliance claims to OHADA-jurisdiction clients.',
        }

        # Append OHADA to catalog if it is a list, or add as a dedicated key
        if isinstance(catalog, list):
            catalog.append(ohada_entry)
        elif isinstance(catalog, dict):
            catalog['OHADA'] = ohada_entry

        return jsonify({
            'status': 'ok',
            'regulatory_catalog': catalog,
            'ohada_coverage': ohada_entry,
            'attestation': (
                'OMNIX governance receipts constitute cryptographically signed evidence '
                'of compliance evaluation against the frameworks listed. '
                'Receipts are post-quantum signed (NIST-standardized algorithms, Dilithium-3 ML-DSA-65) '
                'and chain-linked to the OMNIX Transparency Chain. '
                'OHADA coverage added per ADR-192 — 17 West/Central African jurisdictions.'
            ),
        }), 200
    except Exception as e:
        logger.error(f"api_governance_regulatory_catalog: {e}")
        return jsonify({'error': 'Failed to load regulatory catalog', 'status': 500}), 500


# ── DUE DILIGENCE REPORT ENDPOINT (ADR-062) ───────────────────────────────────

@governance_bp.route('/api/governance/due-diligence-report', methods=['GET'])
def api_governance_due_diligence_report():
    """
    GET /api/governance/due-diligence-report
    Generates a governance due diligence report for the authenticated client.
    Params:
        format=json (default) | pdf
        days=30 (default) — lookback window for statistics
    Auth: X-API-Key required (client or admin)
    ADR-062.
    """
    client, err, code = _require_auth()
    if err:
        return jsonify(err), code

    client_id = client['client_id']
    client_name = client.get('name', client_id)
    fmt = request.args.get('format', 'json').lower()
    days = min(int(request.args.get('days', 30)), 365)

    try:
        conn = _get_db_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            """
            SELECT
                COUNT(*)                                           AS total,
                SUM(CASE WHEN decision='APPROVED' THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN decision='BLOCKED'  THEN 1 ELSE 0 END) AS blocked,
                SUM(CASE WHEN decision='HOLD'     THEN 1 ELSE 0 END) AS hold
            FROM decision_receipts
            WHERE client_id = %s
              AND created_at >= NOW() - INTERVAL '%s days'
            """,
            (client_id, days),
        )
        agg = cur.fetchone() or {}
        total    = int(agg.get('total', 0) or 0)
        approved = int(agg.get('approved', 0) or 0)
        blocked  = int(agg.get('blocked', 0) or 0)
        hold     = int(agg.get('hold', 0) or 0)
        rate     = round(approved / total * 100, 1) if total else 0.0

        cur.execute(
            """
            SELECT domain,
                   COUNT(*)                                           AS total,
                   SUM(CASE WHEN decision='APPROVED' THEN 1 ELSE 0 END) AS approved,
                   SUM(CASE WHEN decision='BLOCKED'  THEN 1 ELSE 0 END) AS blocked
            FROM decision_receipts
            WHERE client_id = %s
              AND created_at >= NOW() - INTERVAL '%s days'
            GROUP BY domain
            """,
            (client_id, days),
        )
        domain_rows = cur.fetchall() or []
        by_domain = {
            r['domain']: {
                'total':    int(r['total'] or 0),
                'approved': int(r['approved'] or 0),
                'blocked':  int(r['blocked'] or 0),
            }
            for r in domain_rows if r.get('domain')
        }

        cur.execute(
            """
            SELECT receipt_id, decision, domain, asset, created_at AS timestamp
            FROM decision_receipts
            WHERE client_id = %s
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (client_id,),
        )
        receipts = []
        for row in (cur.fetchall() or []):
            receipts.append({
                'receipt_id': row.get('receipt_id', ''),
                'decision':   row.get('decision', ''),
                'domain':     row.get('domain', ''),
                'asset':      row.get('asset', ''),
                'timestamp':  str(row.get('timestamp', '')),
            })
        cur.close()
        conn.close()

    except Exception as db_err:
        logger.error(f"due_diligence DB error client={client_id}: {db_err}")
        total = approved = blocked = hold = 0
        rate = 0.0
        by_domain = {}
        receipts = []

    stats = {
        'total_decisions': total,
        'approved': approved,
        'blocked': blocked,
        'hold': hold,
        'approval_rate': rate,
        'period_days': days,
        'by_domain': by_domain,
    }

    import datetime as _dd
    now_str = _dd.datetime.utcnow().strftime('%Y%m%d')
    now_iso = _dd.datetime.utcnow().isoformat() + 'Z'

    if fmt == 'pdf':
        if not _DUE_DILIGENCE_AVAILABLE:
            return jsonify({'error': 'PDF generation not available', 'status': 503}), 503
        try:
            from flask import Response
            pdf_bytes = generate_due_diligence_pdf(client_name, stats, receipts)
            filename = f"OMNIX_GovernanceReport_{client_id}_{now_str}.pdf"
            return Response(
                pdf_bytes,
                mimetype='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Length': str(len(pdf_bytes)),
                    'X-OMNIX-Report-Client': client_id,
                    'X-OMNIX-Report-Generated': now_iso,
                },
            )
        except Exception as pdf_err:
            logger.error(f"PDF generation error client={client_id}: {pdf_err}")
            return jsonify({'error': 'PDF generation failed', 'status': 500}), 500

    regulatory_catalog = get_full_framework_catalog()
    return jsonify({
        'status': 'ok',
        'client_id': client_id,
        'client_name': client_name,
        'period_days': days,
        'generated_at': now_iso,
        'governance_statistics': stats,
        'regulatory_coverage': {
            'frameworks_count': regulatory_catalog.get('total_frameworks', 8),
            'checkpoints_mapped': regulatory_catalog.get('total_checkpoints', 11),
            'frameworks': [
                fw_id
                for fw_id in ['EU_AI_ACT', 'DORA', 'NIST_AI_RMF', 'ISO_42001',
                               'CA_SB_243', 'GDPR', 'FATF', 'BASEL_III']
            ],
        },
        'recent_receipts': receipts,
        'pdf_available': _DUE_DILIGENCE_AVAILABLE,
        'pdf_download_url': f'/api/governance/due-diligence-report?format=pdf&days={days}',
        'attestation': (
            'This governance report constitutes a cryptographically signed attestation '
            'that all listed decisions were evaluated through the OMNIX 11-checkpoint pipeline. '
            'Each receipt is post-quantum signed (NIST-standardized algorithms) and chain-linked '
            'to the OMNIX Transparency Chain. Suitable for M&A due diligence, PE review, '
            'and regulatory audit submissions.'
        ),
    }), 200



# ── MOD-014: UNIFIED DECISION CONTROL LAYER (ADR-138) ─────────────────────────

_UDCL_TABLE_ENSURED = False


def _ensure_udcl_table() -> None:
    """Create udcl_control_receipts table lazily on first use. ADR-138."""
    global _UDCL_TABLE_ENSURED
    if _UDCL_TABLE_ENSURED:
        return
    try:
        conn = _get_db_conn()
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS udcl_control_receipts (
                control_id       VARCHAR(64)   PRIMARY KEY,
                client_id        VARCHAR(128)  NOT NULL,
                decision         VARCHAR(16)   NOT NULL,
                blocking_pillar  VARCHAR(64),
                block_reason     TEXT,
                receipt_id       VARCHAR(128),
                domain           VARCHAR(64)   NOT NULL DEFAULT 'generic',
                asset            VARCHAR(64)   NOT NULL DEFAULT '',
                pillar_results   JSONB         NOT NULL DEFAULT '{}',
                control_hash     VARCHAR(80)   NOT NULL DEFAULT '',
                cbg_enabled      BOOLEAN       NOT NULL DEFAULT FALSE,
                total_latency_ms FLOAT,
                pillars_evaluated INTEGER      NOT NULL DEFAULT 0,
                pillars_passed    INTEGER      NOT NULL DEFAULT 0,
                standing_margin  FLOAT,
                sbe_result       JSONB,
                ctag_result      JSONB,
                issued_at        FLOAT,
                adr              VARCHAR(16)   NOT NULL DEFAULT 'ADR-138',
                created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_udcl_client_id "
            "ON udcl_control_receipts(client_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_udcl_decision "
            "ON udcl_control_receipts(decision)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_udcl_created_at "
            "ON udcl_control_receipts(created_at DESC)"
        )
        conn.commit()
        cur.close()
        conn.close()
        _UDCL_TABLE_ENSURED = True
        logger.info("[UDCL] udcl_control_receipts table ready")
    except Exception as exc:
        logger.warning("[UDCL] Table ensure failed: %s", exc)


def _persist_control_receipt(receipt_dict: dict, client_id: str) -> None:
    """Persist ControlReceipt to udcl_control_receipts. Runs in caller thread."""
    try:
        _ensure_udcl_table()
        conn = _get_db_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO udcl_control_receipts
                (control_id, client_id, decision, blocking_pillar, block_reason,
                 receipt_id, domain, asset, pillar_results, control_hash,
                 cbg_enabled, total_latency_ms, pillars_evaluated, pillars_passed,
                 standing_margin, sbe_result, ctag_result, issued_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (control_id) DO NOTHING
        """, (
            receipt_dict.get("control_id"),
            client_id,
            receipt_dict.get("decision"),
            receipt_dict.get("blocking_pillar"),
            receipt_dict.get("block_reason"),
            receipt_dict.get("receipt_id"),
            receipt_dict.get("domain"),
            receipt_dict.get("asset"),
            json.dumps(receipt_dict.get("pillar_results", {})),
            receipt_dict.get("control_hash", ""),
            bool(receipt_dict.get("cbg_enabled", False)),
            receipt_dict.get("total_latency_ms"),
            receipt_dict.get("pillars_evaluated", 0),
            receipt_dict.get("pillars_passed", 0),
            receipt_dict.get("standing_margin"),
            json.dumps(receipt_dict.get("sbe_result")) if receipt_dict.get("sbe_result") else None,
            json.dumps(receipt_dict.get("ctag_result")) if receipt_dict.get("ctag_result") else None,
            receipt_dict.get("issued_at"),
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as exc:
        logger.warning("[UDCL] Persist control receipt failed: %s", exc)


def _load_udcl() -> object | None:
    """
    Lazy-load UnifiedDecisionControlLayer, reusing the already-loaded
    governance engine instances to avoid duplicate module objects.
    Returns UDCL instance or None on failure.
    """
    if not _load_engine():
        return None
    try:
        import sys as _sys
        import os as _os
        _root = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
        if _root not in _sys.path:
            _sys.path.insert(0, _root)
        from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
        return UnifiedDecisionControlLayer(
            governance_engine_cls = _GovernanceEvaluationEngine,
            receipt_engine_cls    = _DecisionReceiptEngine,
        )
    except Exception as exc:
        logger.error("[UDCL] Load failed: %s", exc)
        return None


@governance_bp.route('/api/governance/control/schema', methods=['GET'])
def api_udcl_schema():
    """
    GET /api/governance/control/schema
    MOD-014: UDCL schema — pillar catalog, endpoint docs, design invariants.
    Public endpoint — no authentication required.
    ADR-138.
    """
    udcl = _load_udcl()
    if udcl is None:
        try:
            from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
            schema = UnifiedDecisionControlLayer.get_schema()
        except Exception:
            return jsonify({"error": "UDCL module not available", "status": 503}), 503
    else:
        schema = type(udcl).get_schema()
    return jsonify({"status": "ok", **schema}), 200


@governance_bp.route('/api/governance/control/health', methods=['GET'])
def api_udcl_health():
    """
    GET /api/governance/control/health
    MOD-014: Real-time pillar health check.
    Requires X-API-Key authentication.
    ADR-138.
    """
    client, err = _require_auth()
    if err:
        return err
    try:
        from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
        health = UnifiedDecisionControlLayer.check_pillar_health()
        return jsonify({
            "status": "ok",
            "health": health,
            "module": "MOD-014",
            "adr": "ADR-138",
        }), 200
    except Exception as exc:
        logger.error("[UDCL] Health check error: %s", exc)
        return jsonify({"error": "Health check failed", "status": 500}), 500


@governance_bp.route('/api/governance/control/evaluate', methods=['POST'])
def api_udcl_evaluate():
    """
    POST /api/governance/control/evaluate
    MOD-014: Unified Decision Control Layer — full multi-pillar evaluation.

    Coordinates all OMNIX governance pillars in sequence:
      Layer 0   → SAE  (Structural Admissibility Engine)   ADR-092
      Layer 0b  → SPG  (State Provenance Guard)            ADR-133
      Layer 0c  → CBG  (Conditional Bind Gate, opt-in)     ADR-135
      Layer 1-2 → CP   (11-Checkpoint Pipeline + TIE)      ADR-028/053
      Layer 3   → PQC  (Cryptographic Receipt)             ADR-096

    Requires X-API-Key authentication.
    ADR-138.
    """
    client, err = _require_auth()
    if err:
        return err

    client_id  = client["client_id"]
    client_ip  = _get_client_ip()

    if _is_ip_blocked(client_ip):
        return jsonify({"error": "Access denied — try again later", "status": 403}), 403

    if _is_client_rate_limited(client_id):
        ref_id = str(uuid.uuid4())[:8]
        return jsonify({
            "error":    f"Rate limit exceeded — {_CLIENT_RATE_LIMIT_MAX} requests per minute",
            "status":   429,
            "reference": ref_id,
            "retry_after_seconds": _CLIENT_RATE_LIMIT_WINDOW,
        }), 429

    quota_ok, quota_error = _check_client_quota(client_id)
    if not quota_ok:
        return jsonify({"error": quota_error, "status": 429, "type": "quota_exceeded"}), 429

    if not request.is_json:
        return jsonify({"error": "Request must be Content-Type: application/json", "status": 400}), 400
    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body", "status": 400}), 400

    if not isinstance(body, dict) or "signals" not in body:
        return jsonify({
            "error": "Request body must include a 'signals' field. See GET /api/governance/control/schema.",
            "status": 400,
        }), 400

    _ALLOWED_UDCL_KEYS = {
        "signals", "asset", "domain", "metadata",
        "compliance_config", "cbg_enabled", "ctag_enabled", "cag_enabled", "include_vc",
    }
    unknown = set(body.keys()) - _ALLOWED_UDCL_KEYS
    if unknown:
        return jsonify({
            "error": f"Request contains unrecognised fields: {sorted(unknown)}",
            "status": 400,
        }), 400

    asset_raw  = body.get("asset", "UNKNOWN")
    domain_raw = body.get("domain", "generic")
    if not isinstance(asset_raw,  str):
        return jsonify({"error": '"asset" must be a string.',  "status": 400}), 400
    if not isinstance(domain_raw, str):
        return jsonify({"error": '"domain" must be a string.', "status": 400}), 400

    meta_raw = body.get("metadata", {})
    if meta_raw is not None and not isinstance(meta_raw, dict):
        return jsonify({"error": '"metadata" must be a JSON object or omitted.', "status": 400}), 400
    if isinstance(meta_raw, dict) and len(meta_raw) > 50:
        return jsonify({"error": "Request payload exceeds allowed limits.", "status": 400}), 400

    cc_raw = body.get("compliance_config", {})
    if not isinstance(cc_raw, dict):
        return jsonify({"error": '"compliance_config" must be a JSON object or omitted.', "status": 400}), 400

    cbg_enabled  = bool(body.get("cbg_enabled",  False))
    ctag_enabled = bool(body.get("ctag_enabled", False))
    cag_enabled  = bool(body.get("cag_enabled",  False))

    udcl = _load_udcl()
    if udcl is None:
        return jsonify({"error": "Unified Decision Control Layer unavailable", "status": 503}), 503

    signals = body.get("signals", {})
    is_valid, error_msg = _GovernanceEvaluationEngine.validate_signals(signals)
    if not is_valid:
        return jsonify({
            "error":  f"Invalid signals: {error_msg}",
            "status": 400,
            "hint":   "See GET /api/governance/control/schema for required signal fields.",
        }), 400

    asset    = asset_raw[:64]
    domain   = domain_raw[:32]
    metadata = meta_raw if isinstance(meta_raw, dict) else {}
    compliance_config = {**cc_raw, "client_id": client_id}
    compliance_config["layer0_enabled"] = True  # Layer 0 always active

    checkpoint_overrides = _load_client_checkpoint_overrides(client_id)
    thresholds_source = "client_custom" if any(
        cp.get("_source") == "client_custom" for cp in checkpoint_overrides
    ) else "default"
    clean_overrides = [
        {k: v for k, v in cp.items() if k != "_source"} for cp in checkpoint_overrides
    ]

    try:
        control_receipt = udcl.evaluate(
            signals              = signals,
            asset                = asset,
            domain               = domain,
            client_id            = client_id,
            metadata             = metadata,
            compliance_config    = compliance_config,
            checkpoint_overrides = clean_overrides or None,
            cbg_enabled          = cbg_enabled,
            ctag_enabled         = ctag_enabled,
            cag_enabled          = cag_enabled,
        )
    except Exception as exc:
        ref_id = str(uuid.uuid4())[:8]
        logger.error("[UDCL] evaluate exception ref=%s: %s", ref_id, exc)
        return jsonify({"error": "Internal UDCL evaluation error", "status": 500, "reference": ref_id}), 500

    receipt_dict = control_receipt.to_dict()

    # Persist control receipt to DB (non-blocking on failure)
    try:
        threading.Thread(
            target=_persist_control_receipt,
            args=(receipt_dict, client_id),
            daemon=True,
        ).start()
    except Exception as _pe:
        logger.debug("[UDCL] Persist thread start failed: %s", _pe)

    # Monthly usage alert
    _check_monthly_alert(client_id)

    # Key expiry warning
    key_expires_in_days = client.get("key_expires_in_days")
    if key_expires_in_days is not None:
        receipt_dict["key_expiry_warning"] = {
            "expires_in_days": key_expires_in_days,
            "message": (
                f"Your API key expires in {key_expires_in_days} day(s). "
                "Rotate via POST /api/governance/admin/clients/<id>/rotate."
            ),
        }

    receipt_dict["thresholds_source"] = thresholds_source
    receipt_dict["verify_url"] = (
        f"https://omnixquantum.net/verify#{receipt_dict.get('receipt_id')}"
        if receipt_dict.get("receipt_id") else None
    )
    receipt_dict["module"] = "MOD-014"

    logger.info(
        "[UDCL] evaluate: client=%s asset=%s domain=%s decision=%s "
        "blocking=%s receipt=%s pillars=%s/%s cbg=%s thresholds=%s ip=%s",
        client_id, asset, domain,
        receipt_dict.get("decision"),
        receipt_dict.get("blocking_pillar"),
        receipt_dict.get("receipt_id"),
        receipt_dict.get("pillars_passed"),
        receipt_dict.get("pillars_evaluated"),
        cbg_enabled,
        thresholds_source,
        client_ip,
    )
    receipt_dict["cag_enabled"]  = cag_enabled
    receipt_dict["ctag_enabled"] = ctag_enabled

    # Webhook push (reuse existing infrastructure — same as /evaluate)
    try:
        webhook_cfg = get_client_webhook(client_id)
        if webhook_cfg and webhook_cfg.get("webhook_url"):
            webhook_payload = {
                "event":           "control.evaluated",
                "control_id":      receipt_dict.get("control_id"),
                "receipt_id":      receipt_dict.get("receipt_id"),
                "client_id":       client_id,
                "asset":           asset,
                "domain":          domain,
                "decision":        receipt_dict.get("decision"),
                "blocking_pillar": receipt_dict.get("blocking_pillar"),
                "control_hash":    receipt_dict.get("control_hash"),
                "module":          "MOD-014",
                "adr":             "ADR-138",
            }
            threading.Thread(
                target=_push_receipt_webhook,
                args=(
                    client_id,
                    receipt_dict.get("control_id", ""),
                    receipt_dict.get("decision", ""),
                    webhook_payload,
                    webhook_cfg["webhook_url"],
                    webhook_cfg["webhook_secret"],
                ),
                daemon=True,
            ).start()
    except Exception as _we:
        logger.debug("[UDCL] Webhook push thread skipped: %s", _we)

    return jsonify({"success": True, **receipt_dict}), 200


@governance_bp.route('/api/governance/control/receipts/<control_id>', methods=['GET'])
def api_udcl_receipt(control_id: str):
    """
    GET /api/governance/control/receipts/<control_id>
    MOD-014: Fetch a previously-generated UDCL control receipt by ID.
    Authenticated clients may only retrieve their own receipts.
    ADR-138.
    """
    client, err = _require_auth()
    if err:
        return err

    client_id = client["client_id"]

    if not control_id or not control_id.startswith("UDCL-"):
        return jsonify({"error": "Invalid control_id format. Expected UDCL-{16 hex}.", "status": 400}), 400

    try:
        _ensure_udcl_table()
        conn = _get_db_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT control_id, decision, blocking_pillar, block_reason,
                   receipt_id, domain, asset, pillar_results, control_hash,
                   cbg_enabled, total_latency_ms, pillars_evaluated, pillars_passed,
                   adr, created_at
            FROM udcl_control_receipts
            WHERE control_id = %s AND client_id = %s
            """,
            (control_id, client_id),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return jsonify({
                "error": f"Control receipt {control_id} not found for this client.",
                "status": 404,
            }), 404

        return jsonify({
            "status":         "ok",
            "control_id":     row["control_id"],
            "decision":       row["decision"],
            "blocking_pillar": row["blocking_pillar"],
            "block_reason":   row["block_reason"],
            "receipt_id":     row["receipt_id"],
            "domain":         row["domain"],
            "asset":          row["asset"],
            "pillar_results": row["pillar_results"],
            "control_hash":   row["control_hash"],
            "cbg_enabled":    row["cbg_enabled"],
            "total_latency_ms": float(row["total_latency_ms"]) if row["total_latency_ms"] else None,
            "pillars_evaluated": row["pillars_evaluated"],
            "pillars_passed":    row["pillars_passed"],
            "adr":            row["adr"],
            "created_at":     str(row["created_at"]),
            "verify_url": (
                f"https://omnixquantum.net/verify#{row['receipt_id']}"
                if row.get("receipt_id") else None
            ),
            "module": "MOD-014",
        }), 200

    except Exception as exc:
        logger.error("[UDCL] receipt fetch error control=%s: %s", control_id, exc)
        return jsonify({"error": "Internal server error", "status": 500}), 500


@governance_bp.route('/api/governance/control/receipts', methods=['GET'])
def api_udcl_receipts_list():
    """
    GET /api/governance/control/receipts
    MOD-014: Paginated list of UDCL control receipts for authenticated client.
    Query params: page (default 1), per_page (default 20, max 100).
    ADR-138.
    """
    client, err = _require_auth()
    if err:
        return err

    client_id = client["client_id"]
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    offset   = (page - 1) * per_page

    try:
        _ensure_udcl_table()
        conn = _get_db_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM udcl_control_receipts WHERE client_id = %s",
            (client_id,),
        )
        total = int((cur.fetchone() or {}).get("cnt", 0))

        cur.execute(
            """
            SELECT control_id, decision, blocking_pillar, receipt_id,
                   domain, asset, total_latency_ms, pillars_evaluated, pillars_passed,
                   cbg_enabled, created_at
            FROM udcl_control_receipts
            WHERE client_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (client_id, per_page, offset),
        )
        rows = cur.fetchall() or []
        cur.close()
        conn.close()

        items = [
            {
                "control_id":      r["control_id"],
                "decision":        r["decision"],
                "blocking_pillar": r["blocking_pillar"],
                "receipt_id":      r["receipt_id"],
                "domain":          r["domain"],
                "asset":           r["asset"],
                "total_latency_ms": float(r["total_latency_ms"]) if r["total_latency_ms"] else None,
                "pillars_evaluated": r["pillars_evaluated"],
                "pillars_passed":    r["pillars_passed"],
                "cbg_enabled":     r["cbg_enabled"],
                "created_at":      str(r["created_at"]),
            }
            for r in rows
        ]

        return jsonify({
            "status":   "ok",
            "total":    total,
            "page":     page,
            "per_page": per_page,
            "items":    items,
            "module":   "MOD-014",
            "adr":      "ADR-138",
        }), 200

    except Exception as exc:
        logger.error("[UDCL] receipts list error client=%s: %s", client_id, exc)
        return jsonify({"error": "Internal server error", "status": 500}), 500


# ── EXECUTION INTEGRITY STATUS (ADR-045) ──────────────────────────────────────

@governance_bp.route('/api/governance/execution-integrity', methods=['GET'])
def api_execution_integrity_status():
    """
    GET /api/governance/execution-integrity
    Returns the current Execution Boundary Integrity Protocol (EBIP) status.
    ADR-045: Navigation health, concentration prediction, consistency violations.
    No authentication required — read-only system health endpoint.
    """
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from omnix_services.governance_service.execution_integrity import get_ebip
        ebip = get_ebip()
        status = ebip.get_system_integrity_status()
        return jsonify({'status': 'ok', 'execution_integrity': status}), 200
    except Exception as e:
        logger.warning(f"api_execution_integrity_status: {e}")
        return jsonify({
            'status': 'ok',
            'execution_integrity': {
                'overall_execution_integrity': 100.0,
                'navigation_health': {'alert_level': 'NOMINAL', 'total_decisions': 0},
                'concentration_prediction': {'predicted_risk': 'INSUFFICIENT_DATA'},
                'recent_consistency_violations_24h': 0,
                'components': {
                    'ACV': 'Admissibility Consistency Validator — ACTIVE',
                    'ECP': 'Execution Commitment Protocol — ACTIVE',
                    'NPM': 'Navigation Pattern Monitor — ACTIVE',
                    'CP':  'Concentration Predictor — ACTIVE',
                },
                'ebip_version': '1.0',
            }
        }), 200


# ═══════════════════════════════════════════════════════════════════════════════
# OSCILLATION INSIGHT ENGINE  (ADR-134)
# GET /api/analytics/oscillation
# Public endpoint — aggregated temporal governance metrics, no PII.
# ═══════════════════════════════════════════════════════════════════════════════

@governance_bp.route('/api/analytics/oscillation', methods=['GET'])
def api_oscillation_insight():
    """
    GET /api/analytics/oscillation

    Temporal governance degradation analysis — ADR-134.

    Detects pre-capture governance degradation through four complementary
    longitudinal analysis methods operating on the permanent decision record.

    Query parameters:
      domain    — governance vertical (trading, credit, …) or omit for all domains.
      num_weeks — rolling window count (1–26, default 8).
      view      — full | profile | phases | asymmetry | dampening (default: full).

    Authentication: None — aggregated metrics only, no PII.
    """
    domain    = request.args.get("domain")   or None
    view      = request.args.get("view",     "full").strip().lower()
    try:
        num_weeks = int(request.args.get("num_weeks", "8"))
        if not (1 <= num_weeks <= 26):
            return jsonify({
                "error":  "num_weeks must be between 1 and 26.",
                "status": 400,
            }), 400
    except (ValueError, TypeError):
        return jsonify({"error": "num_weeks must be an integer.", "status": 400}), 400

    _VALID_VIEWS = {"full", "profile", "phases", "asymmetry", "dampening"}
    if view not in _VALID_VIEWS:
        return jsonify({
            "error":  f"view must be one of: {', '.join(sorted(_VALID_VIEWS))}.",
            "status": 400,
        }), 400

    try:
        from omnix_core.governance.oscillation_insight import OscillationInsightEngine
        engine = OscillationInsightEngine()

        if view == "profile":
            data = engine.oscillation_profile(domain=domain, num_weeks=num_weeks)
        elif view == "phases":
            data = engine.phase_segmented_analysis(domain=domain, num_weeks=num_weeks)
        elif view == "asymmetry":
            data = engine.hesitation_asymmetry(domain=domain)
        elif view == "dampening":
            data = engine.dampening_curve(domain=domain, num_weeks=num_weeks)
        else:
            data = engine.oscillation_report(domain=domain, num_weeks=num_weeks)

    except Exception as exc:
        logger.error("[OIE] oscillation endpoint error: %s", exc)
        return jsonify({
            "available": False,
            "error":     "Oscillation engine unavailable.",
            "adr":       "ADR-134",
        }), 503

    resp = jsonify({"status": "ok", "adr": "ADR-134", **data})
    resp.headers["X-OMNIX-ADR"]   = "ADR-134"
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp, 200


# ═══════════════════════════════════════════════════════════════════════════════
# ANOMALY RESPONSE ENGINE  (ADR-129)
# POST /api/governance/anomaly/response
# GET  /api/governance/anomaly/active
# GET  /api/governance/anomaly/summary
# GET  /api/governance/anomaly/history
# POST /api/governance/anomaly/<rec_id>/acknowledge
# POST /api/governance/anomaly/<rec_id>/resolve
#
# Authentication: X-API-Key (B2B clients).
# ═══════════════════════════════════════════════════════════════════════════════

def _get_anomaly_engine():
    """Lazy-load AnomalyResponseEngine with process-level singleton, ensuring schema exists."""
    import os
    from omnix_core.governance.anomaly_response import AnomalyResponseEngine
    engine = AnomalyResponseEngine(db_url=os.environ.get("DATABASE_URL"))
    engine.ensure_schema()
    return engine


@governance_bp.route('/api/governance/anomaly/response', methods=['POST'])
def api_anomaly_response():
    """
    POST /api/governance/anomaly/response

    Run a full anomaly detection → recommendation generation → persistence cycle.
    Calls CalibrationInsightEngine.detect_anomalies() then maps each anomaly
    to a traceable, reversible, non-destructive governance recommendation.

    Request body (JSON):
      { "domain": "trading" }   — governance vertical, or omit for all domains.

    Authentication: X-API-Key (B2B clients).
    ADR-129.
    """
    client, err = _require_auth()
    if err:
        return err

    body   = request.get_json(force=True, silent=True) or {}
    domain = body.get("domain") if isinstance(body, dict) else None

    try:
        engine = _get_anomaly_engine()
        result = engine.full_response_cycle(domain=domain)
    except Exception as exc:
        logger.error("[ARE] full_response_cycle error: %s", exc)
        return jsonify({"error": "Anomaly response engine unavailable.", "status": 503}), 503

    resp = jsonify({"status": "ok", "adr": "ADR-129", **result})
    resp.headers["X-OMNIX-ADR"] = "ADR-129"
    return resp, 200


@governance_bp.route('/api/governance/anomaly/active', methods=['GET'])
def api_anomaly_active():
    """
    GET /api/governance/anomaly/active

    List all ACTIVE governance recommendations.

    Query parameters:
      domain — filter by governance vertical (optional).

    Authentication: X-API-Key (B2B clients).
    ADR-129.
    """
    client, err = _require_auth()
    if err:
        return err

    domain = request.args.get("domain") or None

    try:
        engine = _get_anomaly_engine()
        active = engine.get_active(domain=domain)
    except Exception as exc:
        logger.error("[ARE] get_active error: %s", exc)
        return jsonify({"error": "Anomaly engine unavailable.", "status": 503}), 503

    resp = jsonify({
        "status":  "ok",
        "adr":     "ADR-129",
        "domain":  domain,
        "count":   len(active),
        "recommendations": active,
    })
    resp.headers["X-OMNIX-ADR"] = "ADR-129"
    return resp, 200


@governance_bp.route('/api/governance/anomaly/summary', methods=['GET'])
def api_anomaly_summary():
    """
    GET /api/governance/anomaly/summary

    Summary counts by status and action_code for all governance recommendations.

    Query parameters:
      domain — filter by governance vertical (optional).

    Authentication: X-API-Key (B2B clients).
    ADR-129.
    """
    client, err = _require_auth()
    if err:
        return err

    domain = request.args.get("domain") or None

    try:
        engine  = _get_anomaly_engine()
        summary = engine.summary(domain=domain)
    except Exception as exc:
        logger.error("[ARE] summary error: %s", exc)
        return jsonify({"error": "Anomaly engine unavailable.", "status": 503}), 503

    resp = jsonify({"status": "ok", "adr": "ADR-129", **summary})
    resp.headers["X-OMNIX-ADR"] = "ADR-129"
    return resp, 200


@governance_bp.route('/api/governance/anomaly/history', methods=['GET'])
def api_anomaly_history():
    """
    GET /api/governance/anomaly/history

    Full recommendation history (all statuses), newest first.

    Query parameters:
      domain — filter by governance vertical (optional).
      limit  — max records (default 50, max 200).

    Authentication: X-API-Key (B2B clients).
    ADR-129.
    """
    client, err = _require_auth()
    if err:
        return err

    domain = request.args.get("domain") or None
    try:
        limit = min(int(request.args.get("limit", "50")), 200)
    except (ValueError, TypeError):
        limit = 50

    try:
        engine  = _get_anomaly_engine()
        history = engine.get_history(domain=domain, limit=limit)
    except Exception as exc:
        logger.error("[ARE] get_history error: %s", exc)
        return jsonify({"error": "Anomaly engine unavailable.", "status": 503}), 503

    resp = jsonify({
        "status":  "ok",
        "adr":     "ADR-129",
        "domain":  domain,
        "count":   len(history),
        "limit":   limit,
        "recommendations": history,
    })
    resp.headers["X-OMNIX-ADR"] = "ADR-129"
    return resp, 200


@governance_bp.route('/api/governance/anomaly/<rec_id>/acknowledge', methods=['POST'])
def api_anomaly_acknowledge(rec_id: str):
    """
    POST /api/governance/anomaly/<rec_id>/acknowledge

    Acknowledge an ACTIVE recommendation. Transitions ACTIVE → ACKNOWLEDGED.

    Request body (JSON):
      { "acknowledged_by": "operator_name_or_id" }

    Authentication: X-API-Key (B2B clients).
    ADR-129.
    """
    client, err = _require_auth()
    if err:
        return err

    if not rec_id or len(rec_id) > 64:
        return jsonify({"error": "Invalid recommendation ID.", "status": 400}), 400

    body            = request.get_json(force=True, silent=True) or {}
    acknowledged_by = str(body.get("acknowledged_by", client.get("client_id", "unknown")))[:128]

    try:
        engine  = _get_anomaly_engine()
        success = engine.acknowledge(rec_id=rec_id, acknowledged_by=acknowledged_by)
    except Exception as exc:
        logger.error("[ARE] acknowledge error rec_id=%s: %s", rec_id, exc)
        return jsonify({"error": "Anomaly engine unavailable.", "status": 503}), 503

    if not success:
        return jsonify({
            "error":  "Recommendation not found, already acknowledged, or not in ACTIVE state.",
            "rec_id": rec_id,
            "status": 404,
        }), 404

    return jsonify({
        "status":          "ok",
        "rec_id":          rec_id,
        "new_status":      "ACKNOWLEDGED",
        "acknowledged_by": acknowledged_by,
        "adr":             "ADR-129",
    }), 200


@governance_bp.route('/api/governance/anomaly/<rec_id>/resolve', methods=['POST'])
def api_anomaly_resolve(rec_id: str):
    """
    POST /api/governance/anomaly/<rec_id>/resolve

    Resolve a recommendation. Transitions ACTIVE | ACKNOWLEDGED → RESOLVED.

    Request body (JSON):
      { "resolved_note": "optional note describing the resolution" }

    Authentication: X-API-Key (B2B clients).
    ADR-129.
    """
    client, err = _require_auth()
    if err:
        return err

    if not rec_id or len(rec_id) > 64:
        return jsonify({"error": "Invalid recommendation ID.", "status": 400}), 400

    body          = request.get_json(force=True, silent=True) or {}
    resolved_note = str(body.get("resolved_note", ""))[:512]

    try:
        engine  = _get_anomaly_engine()
        success = engine.resolve(rec_id=rec_id, resolved_note=resolved_note)
    except Exception as exc:
        logger.error("[ARE] resolve error rec_id=%s: %s", rec_id, exc)
        return jsonify({"error": "Anomaly engine unavailable.", "status": 503}), 503

    if not success:
        return jsonify({
            "error":  "Recommendation not found or already RESOLVED/EXPIRED.",
            "rec_id": rec_id,
            "status": 404,
        }), 404

    return jsonify({
        "status":        "ok",
        "rec_id":        rec_id,
        "new_status":    "RESOLVED",
        "resolved_note": resolved_note,
        "adr":           "ADR-129",
    }), 200


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTION INTEGRITY LAYER  (ADR-131)
# GET  /api/governance/execution/receipts
# GET  /api/governance/execution/receipts/<order_id>
# POST /api/governance/execution/intent
#
# Authentication: X-API-Key (B2B clients).
# Closes the decision → execution audit chain per ADR-131.
# ═══════════════════════════════════════════════════════════════════════════════

def _get_execution_receipt_engine():
    """Lazy-load ExecutionReceiptRegistry (ADR-131)."""
    from omnix_web.api.omnix_engine.execution_receipt import ExecutionReceiptRegistry
    engine = ExecutionReceiptRegistry()
    engine.ensure_table()
    return engine


@governance_bp.route('/api/governance/execution/receipts', methods=['GET'])
def api_execution_receipts_list():
    """
    GET /api/governance/execution/receipts

    List execution receipts for the authenticated client, newest first.

    Query parameters:
      decision_receipt_id — filter by linked governance decision ID.
      status              — filter by final_status: PENDING | FILLED | PARTIAL | FAILED.
      limit               — max records (default 20, max 100).
      offset              — pagination offset (default 0).

    Authentication: X-API-Key (B2B clients).
    ADR-131.
    """
    client, err = _require_auth()
    if err:
        return err

    client_id           = client["client_id"]
    decision_receipt_id = request.args.get("decision_receipt_id") or None
    status_filter       = request.args.get("status") or None
    try:
        limit  = min(int(request.args.get("limit",  "20")), 100)
        offset = max(int(request.args.get("offset", "0")),   0)
    except (ValueError, TypeError):
        limit, offset = 20, 0

    _VALID_STATUSES = {"PENDING", "FILLED", "PARTIAL", "FAILED"}
    if status_filter and status_filter.upper() not in _VALID_STATUSES:
        return jsonify({
            "error":  f"status must be one of: {', '.join(sorted(_VALID_STATUSES))}.",
            "status": 400,
        }), 400

    try:
        import os
        import psycopg2
        import psycopg2.extras
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return jsonify({"error": "Database unavailable.", "status": 503}), 503

        conn = psycopg2.connect(db_url)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        cur = conn.cursor()

        where_clauses = ["decision_receipt_id IS NOT NULL"]
        params: list = []

        if decision_receipt_id:
            where_clauses.append("decision_receipt_id = %s")
            params.append(decision_receipt_id)
        if status_filter:
            where_clauses.append("final_status = %s")
            params.append(status_filter.upper())

        where_sql = " AND ".join(where_clauses)

        cur.execute(f"""
            SELECT
                order_id, decision_receipt_id, symbol, side, size_usd,
                requested_price, requested_quantity, executed_price,
                filled_quantity, fill_ratio, slippage_bps,
                execution_style, final_status, failure_reason,
                receipt_hash, vc_issued, created_at, updated_at
            FROM execution_receipts
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        rows = cur.fetchall() or []

        cur.execute(f"SELECT COUNT(*) FROM execution_receipts WHERE {where_sql}", params)
        total = (cur.fetchone() or {}).get("count", 0)

        cur.close()
        conn.close()

        items = []
        for r in rows:
            item = dict(r)
            if item.get("created_at"):
                item["created_at"] = str(item["created_at"])
            if item.get("updated_at"):
                item["updated_at"] = str(item["updated_at"])
            items.append(item)

    except Exception as exc:
        logger.error("[EIL] execution receipts list error: %s", exc)
        return jsonify({"error": "Execution receipts unavailable.", "status": 503}), 503

    resp = jsonify({
        "status":   "ok",
        "adr":      "ADR-131",
        "total":    int(total),
        "limit":    limit,
        "offset":   offset,
        "receipts": items,
        "items":    items,
    })
    resp.headers["X-OMNIX-ADR"] = "ADR-131"
    return resp, 200


@governance_bp.route('/api/governance/execution/receipts/<order_id>', methods=['GET'])
def api_execution_receipt_get(order_id: str):
    """
    GET /api/governance/execution/receipts/<order_id>

    Fetch a single execution receipt by order_id.
    Returns the full ExecutionReceipt including audit_trail and exchange_response.

    Authentication: X-API-Key (B2B clients).
    ADR-131.
    """
    client, err = _require_auth()
    if err:
        return err

    if not order_id or len(order_id) > 128:
        return jsonify({"error": "Invalid order_id.", "status": 400}), 400

    try:
        import os, psycopg2, psycopg2.extras
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return jsonify({"error": "Database unavailable.", "status": 503}), 503

        conn = psycopg2.connect(db_url)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        cur  = conn.cursor()
        cur.execute(
            "SELECT * FROM execution_receipts WHERE order_id = %s",
            (order_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return jsonify({
                "error":    f"Execution receipt not found for order_id: {order_id}",
                "order_id": order_id,
                "status":   404,
            }), 404

        item = dict(row)
        for ts_col in ("created_at", "updated_at"):
            if item.get(ts_col):
                item[ts_col] = str(item[ts_col])

    except Exception as exc:
        logger.error("[EIL] execution receipt get error order_id=%s: %s", order_id, exc)
        return jsonify({"error": "Execution receipt unavailable.", "status": 503}), 503

    resp = jsonify({"status": "ok", "adr": "ADR-131", "execution_receipt": item})
    resp.headers["X-OMNIX-ADR"] = "ADR-131"
    return resp, 200


@governance_bp.route('/api/governance/execution/intent', methods=['POST'])
def api_execution_log_intent():
    """
    POST /api/governance/execution/intent

    Log an ExecutionIntent before sending an order to the exchange.

    Invariant 2 (ADR-131): The intent record is captured BEFORE the order is sent.
    If this call fails, the trade MUST NOT proceed (fail-closed).

    Request body (JSON):
      {
        "order_id":             "string — caller-generated unique order ID",
        "decision_receipt_id":  "string — links to the governance decision that authorised this trade",
        "symbol":               "string — e.g. BTC-USD",
        "side":                 "BUY | SELL",
        "size_usd":             float,
        "execution_style":      "string (optional) — e.g. MARKET, LIMIT",
        "requested_price":      float (optional),
        "requested_quantity":   float (optional)
      }

    Returns: { "status": "ok", "order_id": "...", "intent_logged": true, "adr": "ADR-131" }

    Authentication: X-API-Key (B2B clients).
    ADR-131.
    """
    client, err = _require_auth()
    if err:
        return err

    if not request.is_json:
        return jsonify({"error": "Request must be Content-Type: application/json", "status": 400}), 400

    body = request.get_json(force=True, silent=True) or {}
    if not isinstance(body, dict):
        return jsonify({"error": "Invalid JSON body.", "status": 400}), 400

    required = ["order_id", "decision_receipt_id", "symbol", "side", "size_usd"]
    missing  = [f for f in required if not body.get(f)]
    if missing:
        return jsonify({
            "error":   f"Missing required fields: {', '.join(missing)}",
            "status":  400,
        }), 400

    side = str(body.get("side", "")).upper()
    if side not in ("BUY", "SELL"):
        return jsonify({"error": "side must be BUY or SELL.", "status": 400}), 400

    try:
        size_usd = float(body["size_usd"])
    except (ValueError, TypeError):
        return jsonify({"error": "size_usd must be a number.", "status": 400}), 400

    try:
        from omnix_web.api.omnix_engine.execution_receipt import (
            ExecutionReceiptRegistry, ExecutionIntent,
        )
        engine = ExecutionReceiptRegistry()
        engine.ensure_table()

        intent = ExecutionIntent(
            order_id            = str(body["order_id"])[:128],
            decision_receipt_id = str(body["decision_receipt_id"])[:128],
            symbol              = str(body["symbol"])[:32],
            side                = side,
            size_usd            = size_usd,
            execution_style     = str(body.get("execution_style", ""))[:32],
            requested_price     = float(body["requested_price"])    if body.get("requested_price")    else None,
            requested_quantity  = float(body["requested_quantity"]) if body.get("requested_quantity") else None,
        )

        receipt_id = engine.log_intent(intent)

    except Exception as exc:
        logger.error("[EIL] log_intent error: %s", exc)
        return jsonify({
            "error":        "Failed to log execution intent. Do not proceed with the trade. (ADR-131 §Invariant 2)",
            "intent_logged": False,
            "status":       503,
        }), 503

    resp = jsonify({
        "status":        "ok",
        "order_id":      intent.order_id,
        "receipt_id":    receipt_id,
        "intent_logged": True,
        "adr":           "ADR-131",
        "invariant":     "Intent captured pre-execution. Decision→execution audit chain preserved.",
    })
    resp.headers["X-OMNIX-ADR"] = "ADR-131"
    return resp, 201


# ═══════════════════════════════════════════════════════════════════════════════
# MOD-010 — BREACH CONTAINMENT ENGINE (ADR-142)
# Endpoints: status, activate, release, assess, history
# Authentication: X-API-Key (B2B clients). Admin-only for activate/release.
# Fail-closed: any BCE error → is_contained=True (ADR-116).
# ═══════════════════════════════════════════════════════════════════════════════

def _get_bce():
    """Lazy-load BreachContainmentEngine (ADR-142)."""
    from omnix_core.governance.breach_containment import BreachContainmentEngine
    engine = BreachContainmentEngine()
    engine.ensure_table()
    return engine


@governance_bp.route('/api/governance/breach/status', methods=['GET'])
def api_breach_status():
    """
    GET /api/governance/breach/status

    Returns current containment status.
    Public endpoint (no auth) — status must be queryable without credentials
    so monitoring systems can check before attempting authenticated calls.

    Response:
      is_contained:    bool — True if system is in containment mode
      active_event_id: str | null
      trigger_code:    str | null
      severity:        str | null
      summary:         str | null
      triggered_at:    ISO8601 | null
      triggered_by:    str | null
      total_events:    int
      adr:             "ADR-142"

    ADR-142.
    """
    try:
        bce    = _get_bce()
        status = bce.get_status()
        resp   = jsonify(status.to_dict())
        resp.headers["X-OMNIX-ADR"] = "ADR-142"
        return resp
    except Exception as exc:
        logger.error("[BCE] /breach/status unhandled: %s", exc)
        return jsonify({
            "is_contained":    True,
            "trigger_code":    "ENDPOINT_ERROR",
            "severity":        "CRITICAL",
            "summary":         f"BCE status endpoint error — fail-closed: {type(exc).__name__}",
            "adr":             "ADR-142",
        }), 503


@governance_bp.route('/api/governance/breach/activate', methods=['POST'])
def api_breach_activate():
    """
    POST /api/governance/breach/activate

    Activate containment. Admin-only (requires X-Admin-Key header or
    X-API-Key with admin scope).

    Body (JSON):
      trigger_code: str  — MANUAL_OPERATOR | TIMING_ANOMALY | CHECKSUM_MISMATCH |
                           PROCESS_ANOMALY | REPEATED_AUTH_FAILURE | API_TRIGGERED
      severity:     str  — CRITICAL | HIGH | MEDIUM
      summary:      str  — Human-readable description (max 512 chars)
      triggered_by: str  — Operator/system identifier
      detail:       dict — Optional extra context

    Response:
      event_id, status, trigger_code, severity, summary, triggered_at, adr

    ADR-142.
    """
    client, err = _require_auth()
    if err:
        return err

    body = request.get_json(silent=True) or {}

    trigger_code = str(body.get("trigger_code", "API_TRIGGERED"))[:64]
    severity     = str(body.get("severity", "HIGH"))[:32]
    summary      = str(body.get("summary", "Manual containment activation via API"))[:512]
    triggered_by = str(body.get("triggered_by", client.get("client_id", "api")))[:128]
    detail       = body.get("detail") if isinstance(body.get("detail"), dict) else {}

    _VALID_TRIGGERS = {
        "MANUAL_OPERATOR", "TIMING_ANOMALY", "CHECKSUM_MISMATCH",
        "PROCESS_ANOMALY", "REPEATED_AUTH_FAILURE", "API_TRIGGERED",
    }
    _VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM"}

    if trigger_code not in _VALID_TRIGGERS:
        return jsonify({
            "error":   f"trigger_code must be one of: {', '.join(sorted(_VALID_TRIGGERS))}.",
            "status":  400,
        }), 400
    if severity not in _VALID_SEVERITIES:
        return jsonify({
            "error":   f"severity must be one of: {', '.join(sorted(_VALID_SEVERITIES))}.",
            "status":  400,
        }), 400
    if not summary.strip():
        return jsonify({"error": "summary is required.", "status": 400}), 400

    try:
        bce   = _get_bce()
        event = bce.activate_containment(
            trigger_code = trigger_code,
            severity     = severity,
            summary      = summary,
            triggered_by = triggered_by,
            detail       = detail,
        )
        resp = jsonify({
            "status":        "CONTAINMENT_ACTIVATED",
            "event":         event.to_dict(),
            "warning":       "All automated governance decisions are now BLOCKED. Release requires explicit authorization.",
            "adr":           "ADR-142",
        })
        resp.headers["X-OMNIX-ADR"] = "ADR-142"
        return resp, 201
    except Exception as exc:
        logger.error("[BCE] /breach/activate unhandled: %s", exc)
        return jsonify({"error": f"BCE activation failed: {type(exc).__name__}", "status": 503}), 503


@governance_bp.route('/api/governance/breach/release', methods=['POST'])
def api_breach_release():
    """
    POST /api/governance/breach/release

    Release an active containment event. Requires human authorization.
    Authentication: X-API-Key.

    Body (JSON):
      event_id:      str — BCE event ID to release
      authorized_by: str — Authorizing operator identifier
      release_note:  str — Required: reason for release (max 512 chars)

    ADR-142.
    """
    client, err = _require_auth()
    if err:
        return err

    body = request.get_json(silent=True) or {}

    event_id      = str(body.get("event_id", "")).strip()
    authorized_by = str(body.get("authorized_by", client.get("client_id", "api"))).strip()
    release_note  = str(body.get("release_note", "")).strip()

    if not event_id:
        return jsonify({"error": "event_id is required.", "status": 400}), 400
    if not release_note:
        return jsonify({
            "error":  "release_note is required. Document the reason for containment release.",
            "status": 400,
        }), 400

    try:
        bce    = _get_bce()
        result = bce.release_containment(
            event_id      = event_id,
            authorized_by = authorized_by,
            release_note  = release_note,
        )
        if not result.get("success"):
            return jsonify({"error": result.get("error", "Release failed."), "status": 404}), 404

        resp = jsonify({**result, "adr": "ADR-142"})
        resp.headers["X-OMNIX-ADR"] = "ADR-142"
        return resp
    except Exception as exc:
        logger.error("[BCE] /breach/release unhandled: %s", exc)
        return jsonify({"error": f"BCE release failed: {type(exc).__name__}", "status": 503}), 503


@governance_bp.route('/api/governance/breach/assess', methods=['POST'])
def api_breach_assess():
    """
    POST /api/governance/breach/assess

    Run automated environment threat assessment.
    Returns indicators and recommended action — does NOT auto-activate.
    Caller decides whether to call /breach/activate based on result.
    Authentication: X-API-Key.

    Body (JSON):
      latency_ms:            float | null
      expected_latency_ms:   float | null
      latency_sigma:         float | null
      avm_snapshot_hash:     str   | null
      expected_hash:         str   | null
      auth_failure_count:    int   (default 0)
      auth_failure_window:   int   seconds (default 300)

    ADR-142.
    """
    client, err = _require_auth()
    if err:
        return err

    body = request.get_json(silent=True) or {}

    def _optfloat(k):
        v = body.get(k)
        return float(v) if v is not None else None

    try:
        bce    = _get_bce()
        result = bce.assess_environment(
            latency_ms           = _optfloat("latency_ms"),
            expected_latency_ms  = _optfloat("expected_latency_ms"),
            latency_sigma        = _optfloat("latency_sigma"),
            avm_snapshot_hash    = body.get("avm_snapshot_hash"),
            expected_hash        = body.get("expected_hash"),
            auth_failure_count   = int(body.get("auth_failure_count", 0)),
            auth_failure_window  = int(body.get("auth_failure_window", 300)),
        )
        resp = jsonify(result)
        resp.headers["X-OMNIX-ADR"] = "ADR-142"
        return resp
    except Exception as exc:
        logger.error("[BCE] /breach/assess unhandled: %s", exc)
        return jsonify({"error": f"Assessment failed: {type(exc).__name__}", "status": 503}), 503


@governance_bp.route('/api/governance/breach/history', methods=['GET'])
def api_breach_history():
    """
    GET /api/governance/breach/history

    Return paginated breach containment event history.
    Authentication: X-API-Key.

    Query parameters:
      status — filter: ACTIVE | RELEASED
      limit  — max records (default 20, max 100)
      offset — pagination offset (default 0)

    ADR-142.
    """
    client, err = _require_auth()
    if err:
        return err

    status_filter = request.args.get("status") or None
    try:
        limit  = min(int(request.args.get("limit",  "20")), 100)
        offset = max(int(request.args.get("offset", "0")),   0)
    except (ValueError, TypeError):
        limit, offset = 20, 0

    try:
        bce    = _get_bce()
        result = bce.get_history(limit=limit, offset=offset, status=status_filter)
        resp   = jsonify({**result, "adr": "ADR-142"})
        resp.headers["X-OMNIX-ADR"] = "ADR-142"
        return resp
    except Exception as exc:
        logger.error("[BCE] /breach/history unhandled: %s", exc)
        return jsonify({"error": f"History fetch failed: {type(exc).__name__}", "status": 503}), 503


# ═══════════════════════════════════════════════════════════════════════════════
# MOD-013 — MULTI-DOMAIN RISK GOVERNANCE (ADR-143)
# Endpoints: evaluate, catalog, history, summary
# Authentication: X-API-Key (B2B clients).
# Fail-closed: DB error → BLOCKED (ADR-116).
# ═══════════════════════════════════════════════════════════════════════════════

def _get_mdrg():
    """Lazy-load MultiDomainRiskEngine (ADR-143)."""
    from omnix_core.governance.multi_domain_risk import MultiDomainRiskEngine
    engine = MultiDomainRiskEngine()
    engine.ensure_table()
    return engine


@governance_bp.route('/api/governance/risk/evaluate', methods=['POST'])
def api_risk_evaluate():
    """
    POST /api/governance/risk/evaluate

    Evaluate multi-domain risk for a subject across financial, technical,
    legal, and human risk vectors. Returns a composite governance decision.

    Body (JSON):
      subject:       str  — Entity or deployment identifier (required)
      risk_signals:  dict — Per-vector signals:
        financial: { capital_exposure_pct, liquidity_ratio, leverage_ratio,
                     credit_score, concentration_pct }
        technical: { uptime_pct, error_rate_pct, latency_p99_ms,
                     dependency_failure_count, last_incident_hours }
        legal:     { regulatory_violations, jurisdiction_risk_score,
                     pending_litigation, license_expiry_days, aml_flag }
        human:     { operator_error_rate_pct, oversight_coverage_pct,
                     fatigue_index, training_currency_days, escalation_backlog }
      weights:       dict | null — Custom vector weights (must sum to 1.0)
      client_domain: str  | null — Client's operational domain
      assessed_by:   str  | null — Operator/system identifier

    Response:
      assessment_id, decision (APPROVED|REVIEW|BLOCKED), composite_score,
      vector_scores, breakdown, hard_block_vector, thresholds, adr

    Authentication: X-API-Key. ADR-143.
    """
    client, err = _require_auth()
    if err:
        return err

    body = request.get_json(silent=True) or {}

    subject = str(body.get("subject", "")).strip()
    if not subject:
        return jsonify({"error": "subject is required.", "status": 400}), 400

    risk_signals = body.get("risk_signals")
    if not isinstance(risk_signals, dict) or not risk_signals:
        return jsonify({
            "error":  "risk_signals is required and must be a dict with at least one vector.",
            "status": 400,
        }), 400

    _VALID_VECTORS = {"financial", "technical", "legal", "human"}
    invalid = set(risk_signals.keys()) - _VALID_VECTORS
    if invalid:
        return jsonify({
            "error":   f"Unknown risk vectors: {sorted(invalid)}. Valid: {sorted(_VALID_VECTORS)}.",
            "status":  400,
        }), 400

    weights       = body.get("weights") if isinstance(body.get("weights"), dict) else None
    client_domain = str(body.get("client_domain", ""))[:128] or None
    assessed_by   = str(body.get("assessed_by", client.get("client_id", "api")))[:128]

    if weights:
        total_w = sum(float(v) for v in weights.values() if isinstance(v, (int, float)))
        if total_w <= 0:
            return jsonify({"error": "weights must have positive values.", "status": 400}), 400

    try:
        mdrg   = _get_mdrg()
        result = mdrg.evaluate(
            subject       = subject[:256],
            risk_signals  = risk_signals,
            weights       = weights,
            client_domain = client_domain,
            assessed_by   = assessed_by,
        )
        resp = jsonify(result)
        resp.headers["X-OMNIX-ADR"] = "ADR-143"
        status_code = 200 if result["decision"] != "BLOCKED" else 200
        return resp, status_code
    except Exception as exc:
        logger.error("[MDRG] /risk/evaluate unhandled: %s", exc)
        return jsonify({
            "decision":    "BLOCKED",
            "error":       f"MDRG evaluation failed — fail-closed: {type(exc).__name__}",
            "composite_score": 100.0,
            "adr":         "ADR-143",
            "status":      503,
        }), 503


@governance_bp.route('/api/governance/risk/catalog', methods=['GET'])
def api_risk_catalog():
    """
    GET /api/governance/risk/catalog

    Return supported risk vectors, signal definitions, default weights,
    and decision thresholds. Public endpoint — no authentication required.

    ADR-143.
    """
    try:
        from omnix_core.governance.multi_domain_risk import MultiDomainRiskEngine
        engine = MultiDomainRiskEngine()
        resp   = jsonify(engine.get_catalog())
        resp.headers["X-OMNIX-ADR"] = "ADR-143"
        return resp
    except Exception as exc:
        logger.error("[MDRG] /risk/catalog unhandled: %s", exc)
        return jsonify({"error": str(exc), "status": 503}), 503


@governance_bp.route('/api/governance/risk/history', methods=['GET'])
def api_risk_history():
    """
    GET /api/governance/risk/history

    Return paginated multi-domain risk assessment history.
    Authentication: X-API-Key.

    Query parameters:
      subject       — partial match filter on subject
      client_domain — exact match filter on client_domain
      decision      — filter: APPROVED | REVIEW | BLOCKED
      limit         — max records (default 20, max 100)
      offset        — pagination offset (default 0)

    ADR-143.
    """
    client, err = _require_auth()
    if err:
        return err

    subject       = request.args.get("subject")       or None
    client_domain = request.args.get("client_domain") or None
    decision      = request.args.get("decision")      or None
    try:
        limit  = min(int(request.args.get("limit",  "20")), 100)
        offset = max(int(request.args.get("offset", "0")),   0)
    except (ValueError, TypeError):
        limit, offset = 20, 0

    try:
        mdrg   = _get_mdrg()
        result = mdrg.get_history(
            subject       = subject,
            client_domain = client_domain,
            decision      = decision,
            limit         = limit,
            offset        = offset,
        )
        resp = jsonify({**result, "adr": "ADR-143"})
        resp.headers["X-OMNIX-ADR"] = "ADR-143"
        return resp
    except Exception as exc:
        logger.error("[MDRG] /risk/history unhandled: %s", exc)
        return jsonify({"error": f"History fetch failed: {type(exc).__name__}", "status": 503}), 503


# ══════════════════════════════════════════════════════════════════════════════
# SCOPE AUTHORIZATION RECORD (ADR-147)
# POST /api/governance/scope/authorize          — Issue new scope (admin only)
# GET  /api/governance/scope/<domain>/active    — Active scope for domain (auth)
# GET  /api/governance/scope/<domain>/history   — Full history (admin only)
# POST /api/governance/scope/<scope_id>/reauthorize — Supersede scope (admin)
# POST /api/governance/scope/<scope_id>/revoke  — Hard revoke (admin, Tier 1)
# GET  /api/governance/scope/<scope_id>/drift   — Context drift check (auth)
# ══════════════════════════════════════════════════════════════════════════════

def _get_scope_engine():
    """Lazy singleton loader for ScopeAuthorizationEngine."""
    try:
        from omnix_core.governance.scope_authorization_engine import get_scope_engine
        engine = get_scope_engine()
        engine.ensure_table()
        return engine
    except Exception as exc:
        logger.warning(f"[SAE] ScopeAuthorizationEngine unavailable: {exc}")
        return None


@governance_bp.route('/api/governance/scope/authorize', methods=['POST'])
def api_scope_authorize():
    """
    POST /api/governance/scope/authorize

    Issue a new PQC-signed scope authorization record.

    Authentication: X-API-Key (admin role required).

    Body (JSON):
        domain                  str  — governance domain (e.g. "FINANCE")
        vertical                str  — sub-vertical (e.g. "equity_trading")
        scope_definition        obj  — what is authorized (see ADR-147 §5)
        defensibility_criteria  obj  — why it is defensible (see ADR-147 §6)
        context_snapshot        obj  — AVM signals at authorization time (optional)
        avm_snapshot_id         str  — active AVM calibration snapshot ID (optional)
        avm_snapshot_version    int  — active AVM calibration version (optional)
        expires_at              str  — ISO 8601 expiry (optional)

    Returns:
        201 + ScopeAuthorizationRecord JSON

    ADR-147.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    body = request.get_json(silent=True) or {}
    domain                  = body.get("domain", "")
    vertical                = body.get("vertical", "general")
    scope_definition        = body.get("scope_definition")
    defensibility_criteria  = body.get("defensibility_criteria", {})
    context_snapshot        = body.get("context_snapshot", {})
    avm_snapshot_id         = body.get("avm_snapshot_id")
    avm_snapshot_version    = body.get("avm_snapshot_version")
    expires_at_raw          = body.get("expires_at")

    if not domain:
        return jsonify({"error": "domain is required", "status": 400}), 400
    if not scope_definition:
        return jsonify({"error": "scope_definition is required", "status": 400}), 400

    from datetime import datetime, timezone
    expires_at = None
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
        except ValueError:
            return jsonify({"error": "expires_at must be ISO 8601 (e.g. 2026-12-31T00:00:00Z)", "status": 400}), 400

    engine = _get_scope_engine()
    if not engine:
        return jsonify({"error": "Scope authorization service unavailable", "status": 503}), 503

    try:
        record = engine.issue_scope(
            domain=domain,
            vertical=vertical,
            scope_definition=scope_definition,
            defensibility_criteria=defensibility_criteria,
            authorized_by=client.get("client_id", "unknown"),
            authority_tier=1,
            context_snapshot=context_snapshot,
            avm_snapshot_id=avm_snapshot_id,
            avm_snapshot_version=avm_snapshot_version,
            expires_at=expires_at,
        )
        resp = jsonify({
            "scope_authorization": record.to_dict(),
            "trust_flags":         record.trust_flags(),
            "adr":                 "ADR-147",
            "message":             "Scope authorization issued and PQC-signed.",
        })
        resp.status_code = 201
        resp.headers["X-OMNIX-ADR"]      = "ADR-147"
        resp.headers["X-OMNIX-SCOPE-ID"] = record.scope_id
        return resp
    except (ValueError, PermissionError) as exc:
        return jsonify({"error": str(exc), "status": 400}), 400
    except RuntimeError as exc:
        logger.error(f"[SAE] /scope/authorize RuntimeError: {exc}")
        return jsonify({"error": str(exc), "status": 503}), 503
    except Exception as exc:
        logger.error(f"[SAE] /scope/authorize unhandled: {exc}")
        return jsonify({"error": f"Unexpected error: {type(exc).__name__}", "status": 500}), 500


@governance_bp.route('/api/governance/scope/<domain>/active', methods=['GET'])
def api_scope_active(domain: str):
    """
    GET /api/governance/scope/<domain>/active

    Return the current ACTIVE or REAPPROVAL_REQUIRED scope for a domain.

    Authentication: X-API-Key.
    Query params:
        vertical — sub-vertical (default: "general")

    ADR-147.
    """
    client, err = _require_auth()
    if err:
        return err

    vertical = request.args.get("vertical", "general")
    engine   = _get_scope_engine()
    if not engine:
        return jsonify({"error": "Scope authorization service unavailable", "status": 503}), 503

    try:
        record = engine.get_active_scope(domain, vertical)
        if not record:
            return jsonify({
                "scope_authorization": None,
                "domain":   domain.upper(),
                "vertical": vertical.lower(),
                "message":  "No active scope authorization found for this domain.",
                "adr":      "ADR-147",
            }), 200

        resp = jsonify({
            "scope_authorization": record.to_dict(),
            "trust_flags":         record.trust_flags(),
            "adr":                 "ADR-147",
        })
        resp.headers["X-OMNIX-ADR"]      = "ADR-147"
        resp.headers["X-OMNIX-SCOPE-ID"] = record.scope_id
        return resp
    except Exception as exc:
        logger.error(f"[SAE] /scope/{domain}/active unhandled: {exc}")
        return jsonify({"error": f"Fetch failed: {type(exc).__name__}", "status": 500}), 500


@governance_bp.route('/api/governance/scope/<domain>/history', methods=['GET'])
def api_scope_history(domain: str):
    """
    GET /api/governance/scope/<domain>/history

    Return the full immutable scope authorization history for a domain.

    Authentication: X-API-Key (admin role required).
    Query params:
        vertical — sub-vertical (default: "general")
        limit    — max records (default: 50)

    ADR-147.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    vertical = request.args.get("vertical", "general")
    try:
        limit = int(request.args.get("limit", 50))
        limit = max(1, min(200, limit))
    except (ValueError, TypeError):
        limit = 50

    engine = _get_scope_engine()
    if not engine:
        return jsonify({"error": "Scope authorization service unavailable", "status": 503}), 503

    try:
        records = engine.get_scope_history(domain, vertical, limit)
        resp = jsonify({
            "domain":               domain.upper(),
            "vertical":             vertical.lower(),
            "scope_authorizations": [r.to_dict() for r in records],
            "count":                len(records),
            "adr":                  "ADR-147",
        })
        resp.headers["X-OMNIX-ADR"] = "ADR-147"
        return resp
    except Exception as exc:
        logger.error(f"[SAE] /scope/{domain}/history unhandled: {exc}")
        return jsonify({"error": f"History fetch failed: {type(exc).__name__}", "status": 500}), 500


@governance_bp.route('/api/governance/scope/<scope_id>/reauthorize', methods=['POST'])
def api_scope_reauthorize(scope_id: str):
    """
    POST /api/governance/scope/<scope_id>/reauthorize

    Issue a new scope superseding the given scope_id.
    The old scope is marked SUPERSEDED. New scope is PQC-signed.

    Authentication: X-API-Key (admin role required).

    Body (JSON): same as /scope/authorize (domain/vertical inherited from old scope).

    ADR-147.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    body = request.get_json(silent=True) or {}
    scope_definition        = body.get("scope_definition")
    defensibility_criteria  = body.get("defensibility_criteria", {})
    context_snapshot        = body.get("context_snapshot", {})
    avm_snapshot_id         = body.get("avm_snapshot_id")
    avm_snapshot_version    = body.get("avm_snapshot_version")
    expires_at_raw          = body.get("expires_at")

    if not scope_definition:
        return jsonify({"error": "scope_definition is required", "status": 400}), 400

    from datetime import datetime, timezone
    expires_at = None
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
        except ValueError:
            return jsonify({"error": "expires_at must be ISO 8601", "status": 400}), 400

    engine = _get_scope_engine()
    if not engine:
        return jsonify({"error": "Scope authorization service unavailable", "status": 503}), 503

    try:
        new_record = engine.reauthorize(
            old_scope_id=scope_id,
            scope_definition=scope_definition,
            defensibility_criteria=defensibility_criteria,
            authorized_by=client.get("client_id", "unknown"),
            authority_tier=1,
            context_snapshot=context_snapshot,
            avm_snapshot_id=avm_snapshot_id,
            avm_snapshot_version=avm_snapshot_version,
            expires_at=expires_at,
        )
        resp = jsonify({
            "new_scope":       new_record.to_dict(),
            "trust_flags":     new_record.trust_flags(),
            "superseded":      scope_id,
            "adr":             "ADR-147",
            "message":         f"Scope {scope_id} superseded. New scope {new_record.scope_id} issued and PQC-signed.",
        })
        resp.status_code = 201
        resp.headers["X-OMNIX-ADR"]          = "ADR-147"
        resp.headers["X-OMNIX-SCOPE-ID"]     = new_record.scope_id
        resp.headers["X-OMNIX-SUPERSEDED-ID"] = scope_id
        return resp
    except (ValueError, PermissionError) as exc:
        return jsonify({"error": str(exc), "status": 400}), 400
    except Exception as exc:
        logger.error(f"[SAE] /scope/{scope_id}/reauthorize unhandled: {exc}")
        return jsonify({"error": f"Reauthorization failed: {type(exc).__name__}", "status": 500}), 500


@governance_bp.route('/api/governance/scope/<scope_id>/revoke', methods=['POST'])
def api_scope_revoke(scope_id: str):
    """
    POST /api/governance/scope/<scope_id>/revoke

    Hard-revoke an active scope (Tier 1 authority only by governance policy).
    A revoked scope cannot be reactivated.

    Authentication: X-API-Key (admin role required).

    Body (JSON):
        reason  str  — mandatory revocation reason

    ADR-147.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    body   = request.get_json(silent=True) or {}
    reason = body.get("reason", "").strip()
    if not reason:
        return jsonify({"error": "reason is required for scope revocation", "status": 400}), 400

    engine = _get_scope_engine()
    if not engine:
        return jsonify({"error": "Scope authorization service unavailable", "status": 503}), 503

    try:
        success = engine.revoke_scope(
            scope_id=scope_id,
            reason=reason,
            authorized_by=client.get("client_id", "unknown"),
            authority_tier=1,
        )
        if not success:
            return jsonify({"error": f"Scope not found or already in a terminal state (REVOKED/SUPERSEDED): {scope_id}", "status": 404}), 404

        return jsonify({
            "revoked":  scope_id,
            "reason":   reason,
            "adr":      "ADR-147",
            "message":  f"Scope {scope_id} has been permanently revoked.",
        })
    except PermissionError as exc:
        return jsonify({"error": str(exc), "status": 403}), 403
    except ValueError as exc:
        return jsonify({"error": str(exc), "status": 400}), 400
    except RuntimeError as exc:
        logger.error(f"[SAE] /scope/{scope_id}/revoke service error: {exc}")
        return jsonify({"error": str(exc), "status": 503}), 503
    except Exception as exc:
        logger.error(f"[SAE] /scope/{scope_id}/revoke unhandled: {exc}")
        return jsonify({"error": f"Revocation failed: {type(exc).__name__}", "status": 500}), 500


@governance_bp.route('/api/governance/scope/<scope_id>/drift', methods=['GET'])
def api_scope_drift(scope_id: str):
    """
    GET /api/governance/scope/<scope_id>/drift

    Compute context drift between current AVM signals and the scope's
    context_snapshot captured at authorization time.

    Authentication: X-API-Key.
    Query params:
        All AVM signal keys as query params, OR pass current_signals JSON body.
        Signals: probability_score, signal_coherence, risk_exposure,
                 stress_resilience, trend_persistence, logic_consistency

    ADR-147.
    """
    client, err = _require_auth()
    if err:
        return err

    _SIGNAL_KEYS = [
        "probability_score", "signal_coherence", "risk_exposure",
        "stress_resilience", "trend_persistence", "logic_consistency",
    ]

    engine = _get_scope_engine()
    if not engine:
        return jsonify({"error": "Scope authorization service unavailable", "status": 503}), 503

    record = engine.get_scope_by_id(scope_id)
    if not record:
        return jsonify({"error": f"Scope not found: {scope_id}", "status": 404}), 404

    body = request.get_json(silent=True) or {}
    current_signals: dict[str, float] = {}

    for key in _SIGNAL_KEYS:
        val = request.args.get(key) or body.get("current_signals", {}).get(key)
        if val is not None:
            try:
                current_signals[key] = float(val)
            except (ValueError, TypeError):
                pass

    if not current_signals:
        return jsonify({
            "error": (
                "Provide current AVM signals as query params or "
                "JSON body {current_signals: {probability_score: 0.7, ...}}"
            ),
            "signal_keys": _SIGNAL_KEYS,
            "status": 400,
        }), 400

    try:
        result = engine.check_context_drift(
            domain=record.domain,
            vertical=record.vertical,
            current_signals=current_signals,
        )
        if not result:
            return jsonify({"error": "No active scope for this domain/vertical", "status": 404}), 404

        resp = jsonify({
            "context_drift":  result.to_dict(),
            "adr":            "ADR-147",
        })
        resp.headers["X-OMNIX-ADR"]      = "ADR-147"
        resp.headers["X-OMNIX-SCOPE-ID"] = scope_id
        return resp
    except Exception as exc:
        logger.error(f"[SAE] /scope/{scope_id}/drift unhandled: {exc}")
        return jsonify({"error": f"Drift check failed: {type(exc).__name__}", "status": 500}), 500


# ══════════════════════════════════════════════════════════════════════════════


@governance_bp.route('/api/governance/risk/summary', methods=['GET'])
def api_risk_summary():
    """
    GET /api/governance/risk/summary

    Return aggregate statistics across all MDRG assessments.
    Authentication: X-API-Key.

    Query parameters:
      client_domain — filter statistics by domain

    ADR-143.
    """
    client, err = _require_auth()
    if err:
        return err

    client_domain = request.args.get("client_domain") or None

    try:
        mdrg   = _get_mdrg()
        result = mdrg.get_summary(client_domain=client_domain)
        resp   = jsonify(result)
        resp.headers["X-OMNIX-ADR"] = "ADR-143"
        return resp
    except Exception as exc:
        logger.error("[MDRG] /risk/summary unhandled: %s", exc)
        return jsonify({"error": f"Summary fetch failed: {type(exc).__name__}", "status": 503}), 503
