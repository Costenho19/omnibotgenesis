"""
OMNIX B2B RBAC — Role-Based Access Control for Governance API.

Each B2B client has:
  - A unique client_id (e.g. "quant-fund-alpha-01")
  - A unique API key (stored as SHA-256 hash — plaintext never stored)
  - A role: 'standard' or 'admin'
  - is_active flag for instant revocation without code changes

Auth flow:
  X-API-Key header → SHA-256 hash → lookup in b2b_clients → return client row
  client_id comes from DB, NOT from X-Client-ID header → no spoofing possible
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


def authenticate_client(api_key: str) -> dict | None:
    """
    Authenticate an API key against b2b_clients table.
    Returns the client row as dict if active, None otherwise.
    Falls back to B2B_API_KEY env var if b2b_clients table is empty (dev mode).
    """
    if not api_key:
        return None

    try:
        conn = _get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Check if any clients exist — if none, fall back to env var
        cur.execute("SELECT COUNT(*) as cnt FROM b2b_clients")
        count = cur.fetchone()["cnt"]

        if count == 0:
            # Dev fallback: if b2b_clients is empty, use B2B_API_KEY env var
            env_key = os.environ.get("B2B_API_KEY", "")
            if env_key and api_key == env_key:
                cur.close()
                conn.close()
                return {
                    "client_id": "legacy-env-client",
                    "name": "Legacy ENV Client",
                    "role": "admin",
                    "is_active": True,
                    "email": None,
                }
            cur.close()
            conn.close()
            return None

        key_hash = hash_api_key(api_key)
        cur.execute(
            """
            SELECT client_id, name, email, role, is_active, created_at, last_seen_at
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
        return dict(row)

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
    Raises ValueError if client_id already exists.
    """
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)

    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO b2b_clients (client_id, api_key_hash, name, email, role, is_active)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            """,
            (client_id, key_hash, name, email, role),
        )
        conn.commit()
        logger.info(f"RBAC: created client client_id={client_id} role={role}")
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
    Returns the new plaintext key — shown once only.
    Raises ValueError if client_id not found.
    """
    new_key = generate_api_key()
    key_hash = hash_api_key(new_key)

    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE b2b_clients SET api_key_hash = %s WHERE client_id = %s",
            (key_hash, client_id),
        )
        if cur.rowcount == 0:
            raise ValueError(f"client_id '{client_id}' not found")
        conn.commit()
        logger.info(f"RBAC: rotated API key for client_id={client_id}")
        return new_key
    finally:
        cur.close()
        conn.close()


def list_clients() -> list[dict]:
    """List all clients (admin use — never returns api_key_hash)."""
    conn = _get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
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
