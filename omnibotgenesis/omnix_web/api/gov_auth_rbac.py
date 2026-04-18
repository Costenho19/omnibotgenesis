"""
OMNIX B2B RBAC — Role-Based Access Control for Governance API.

Each B2B client has:
  - A unique client_id (e.g. "quant-fund-alpha-01")
  - A unique API key (stored as SHA-256 hash — plaintext never stored)
  - A role: 'standard' or 'admin'
  - is_active flag for instant revocation without code changes
  - key_expires_at: API key expires after 90 days (ADR-052)
  - webhook_url: optional HTTPS callback URL for decision push notifications (ADR-053)
  - webhook_secret: Fernet-encrypted HMAC secret for webhook verification (ADR-053)

Auth flow:
  X-API-Key header → SHA-256 hash → lookup in b2b_clients → return client row
  client_id comes from DB, NOT from X-Client-ID header → no spoofing possible

ADR-052: API Key Expiry (90-day rolling window)
ADR-053: Generic Webhook Push System
"""

import hashlib
import logging
import os
import secrets
import string

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


def _get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def hash_api_key(key: str) -> str:
    """Return SHA-256 hex digest of the API key."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def generate_api_key(prefix: str = "OMNIX") -> str:
    """Generate a cryptographically secure API key."""
    alphabet = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(40))
    return f"{prefix}-{random_part}"


def _ensure_key_expiry_column() -> None:
    """Add key_expires_at column to b2b_clients if it doesn't exist yet."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            ALTER TABLE b2b_clients
            ADD COLUMN IF NOT EXISTS key_expires_at TIMESTAMPTZ
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"RBAC _ensure_key_expiry_column (non-fatal): {e}")


_KEY_EXPIRY_DAYS = 90


def authenticate_client(api_key: str) -> dict | None:
    """
    Authenticate an API key against b2b_clients table.
    Returns the client row as dict if active and not expired, None otherwise.
    Falls back to B2B_API_KEY env var if b2b_clients table is empty (dev mode).
    """
    if not api_key:
        return None

    try:
        conn = _get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT COUNT(*) as cnt FROM b2b_clients")
        count = cur.fetchone()["cnt"]

        if count == 0:
            env_key = os.environ.get("B2B_API_KEY", "")
            if env_key and secrets.compare_digest(api_key, env_key):
                cur.close()
                conn.close()
                return {
                    "client_id": "legacy-env-client",
                    "name": "Legacy ENV Client",
                    "role": "admin",
                    "is_active": True,
                    "email": None,
                    "key_expires_at": None,
                }
            cur.close()
            conn.close()
            return None

        key_hash = hash_api_key(api_key)
        cur.execute(
            """
            SELECT client_id, name, email, role, is_active, created_at, last_seen_at, key_expires_at
            FROM b2b_clients
            WHERE api_key_hash = %s AND is_active = TRUE
            """,
            (key_hash,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row is None:
            return None

        client = dict(row)

        if client.get("key_expires_at") is not None:
            import datetime as _dt
            exp = client["key_expires_at"]
            if hasattr(exp, 'tzinfo') and exp.tzinfo is None:
                exp = exp.replace(tzinfo=_dt.timezone.utc)
            if exp < _dt.datetime.now(_dt.timezone.utc):
                logger.warning(f"RBAC: expired key used by client_id={client['client_id']}")
                return None

        return client

    except Exception as e:
        logger.error(f"RBAC authenticate_client error: {e}")
        return None


def update_last_seen(client_id: str) -> None:
    """Update last_seen_at for a client. Best-effort, never raises."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE b2b_clients SET last_seen_at = NOW() WHERE client_id = %s",
            (client_id,),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"RBAC update_last_seen error (non-fatal): {e}")


def create_client(
    client_id: str,
    name: str,
    email: str | None = None,
    role: str = "standard",
) -> str:
    """
    Create a new B2B client. Returns the plaintext API key — shown once only.
    Key expires in 90 days. Raises ValueError if client_id already exists.
    """
    _ensure_key_expiry_column()
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)

    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO b2b_clients (client_id, api_key_hash, name, email, role, is_active, key_expires_at)
            VALUES (%s, %s, %s, %s, %s, TRUE, NOW() + INTERVAL '90 days')
            """,
            (client_id, key_hash, name, email, role),
        )
        conn.commit()
        logger.info(f"RBAC: created client client_id={client_id} role={role} expires_in=90d")
        return api_key
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise ValueError(f"client_id '{client_id}' already exists")
    finally:
        cur.close()
        conn.close()


def deactivate_client(client_id: str) -> bool:
    """
    Soft-delete a client (sets is_active = FALSE).
    Returns True if the client was found and deactivated, False if not found.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE b2b_clients SET is_active = FALSE WHERE client_id = %s",
            (client_id,),
        )
        affected = cur.rowcount
        conn.commit()
        if affected > 0:
            logger.info(f"RBAC: deactivated client client_id={client_id}")
            return True
        return False
    finally:
        cur.close()
        conn.close()


def reactivate_client(client_id: str) -> bool:
    """Reactivate a previously deactivated client."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE b2b_clients SET is_active = TRUE WHERE client_id = %s",
            (client_id,),
        )
        affected = cur.rowcount
        conn.commit()
        return affected > 0
    finally:
        cur.close()
        conn.close()


def rotate_api_key(client_id: str) -> str:
    """
    Generate and store a new API key for an existing client.
    Resets key_expires_at to 90 days from now.
    Returns the new plaintext key — shown once only.
    Raises ValueError if client_id not found.
    """
    _ensure_key_expiry_column()
    new_key = generate_api_key()
    key_hash = hash_api_key(new_key)

    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE b2b_clients
            SET api_key_hash = %s, key_expires_at = NOW() + INTERVAL '90 days'
            WHERE client_id = %s
            """,
            (key_hash, client_id),
        )
        if cur.rowcount == 0:
            raise ValueError(f"client_id '{client_id}' not found")
        conn.commit()
        logger.info(f"RBAC: rotated API key for client_id={client_id} — new expiry in 90d")
        return new_key
    finally:
        cur.close()
        conn.close()


def list_clients() -> list[dict]:
    """
    List all clients (admin use — never returns api_key_hash or webhook_secret).
    Includes webhook_url (presence, not secret) and key_expires_at for admin visibility.
    Gracefully falls back to base columns if webhook/expiry columns don't exist yet.
    ADR-053.
    """
    conn = _get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        try:
            cur.execute(
                """
                SELECT client_id, name, email, role, is_active, created_at, last_seen_at,
                       key_expires_at,
                       webhook_url,
                       (webhook_secret IS NOT NULL) AS webhook_configured
                FROM b2b_clients
                ORDER BY created_at DESC
                """
            )
        except Exception:
            cur.execute(
                """
                SELECT client_id, name, email, role, is_active, created_at, last_seen_at
                FROM b2b_clients
                ORDER BY created_at DESC
                """
            )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        cur.close()
        conn.close()


# ── WEBHOOK MANAGEMENT (ADR-053) ──────────────────────────────────────────────

def _ensure_webhook_columns() -> None:
    """Add webhook_url and webhook_secret columns to b2b_clients if absent."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "ALTER TABLE b2b_clients ADD COLUMN IF NOT EXISTS webhook_url TEXT"
        )
        cur.execute(
            "ALTER TABLE b2b_clients ADD COLUMN IF NOT EXISTS webhook_secret TEXT"
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"RBAC _ensure_webhook_columns (non-fatal): {e}")


def _encrypt_webhook_secret(plaintext: str) -> str:
    """
    Encrypt webhook secret using Fernet (WEBHOOK_ENCRYPTION_KEY env var).
    Falls back to plaintext if cryptography package or key not available.
    """
    try:
        from cryptography.fernet import Fernet
        key = os.environ.get("WEBHOOK_ENCRYPTION_KEY", "").strip()
        if key:
            f = Fernet(key.encode())
            return f.encrypt(plaintext.encode()).decode()
    except Exception as e:
        logger.debug(f"RBAC webhook secret encryption skipped (non-fatal): {e}")
    return plaintext


def _decrypt_webhook_secret(ciphertext: str) -> str:
    """
    Decrypt Fernet-encrypted webhook secret.
    Falls back to returning as-is if key not available or decryption fails.
    """
    try:
        from cryptography.fernet import Fernet
        key = os.environ.get("WEBHOOK_ENCRYPTION_KEY", "").strip()
        if key:
            f = Fernet(key.encode())
            return f.decrypt(ciphertext.encode()).decode()
    except Exception as e:
        logger.debug(f"RBAC webhook secret decryption skipped (non-fatal): {e}")
    return ciphertext


def set_client_webhook(client_id: str, webhook_url: str, webhook_secret: str) -> bool:
    """
    Register or update a client's webhook URL and HMAC signing secret.
    Secret is Fernet-encrypted before storage — never stored in plaintext.
    Returns True if the client was found and updated.
    ADR-053.
    """
    _ensure_webhook_columns()
    encrypted_secret = _encrypt_webhook_secret(webhook_secret)
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE b2b_clients
            SET webhook_url = %s, webhook_secret = %s
            WHERE client_id = %s
            """,
            (webhook_url, encrypted_secret, client_id),
        )
        updated = cur.rowcount > 0
        conn.commit()
        if updated:
            logger.info(f"RBAC: webhook set for client_id={client_id} url={webhook_url[:60]}...")
        return updated
    finally:
        cur.close()
        conn.close()


def delete_client_webhook(client_id: str) -> bool:
    """
    Remove a client's webhook configuration.
    Returns True if the client was found and updated.
    ADR-053.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE b2b_clients SET webhook_url = NULL, webhook_secret = NULL WHERE client_id = %s",
            (client_id,),
        )
        updated = cur.rowcount > 0
        conn.commit()
        if updated:
            logger.info(f"RBAC: webhook removed for client_id={client_id}")
        return updated
    finally:
        cur.close()
        conn.close()


def get_client_webhook(client_id: str) -> dict | None:
    """
    Return the client's decrypted webhook config: {webhook_url, webhook_secret}.
    Returns None if the client has no webhook configured.
    ADR-053.
    """
    try:
        conn = _get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT webhook_url, webhook_secret
            FROM b2b_clients
            WHERE client_id = %s AND is_active = TRUE
            """,
            (client_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row or not row.get("webhook_url"):
            return None
        return {
            "webhook_url": row["webhook_url"],
            "webhook_secret": _decrypt_webhook_secret(row["webhook_secret"] or ""),
        }
    except Exception as e:
        logger.warning(f"RBAC get_client_webhook error (non-fatal): {e}")
        return None
