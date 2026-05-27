"""
OMNIX Receipt Archival Service — Phase 2 (ADR-126)

HOT/WARM/COLD tiered archival for decision_receipts with cryptographic
integrity preservation across physical storage boundaries.

Tiers
─────
  HOT  (0–30d):   decision_receipts          (live PostgreSQL — unchanged)
  WARM (30d–12m): decision_receipts_warm      (PostgreSQL archive table)
  COLD (12m–5y):  S3/R2 object storage        (external, immutable)
                  └── fallback: decision_receipts_cold (dev/staging only)

Migration protocol — 9 steps, verified at each boundary
─────────────────────────────────────────────────────────
  1.  Check archival_index — skip if already ARCHIVED (idempotent)
  2.  Mark status=COPYING  in receipt_archival_index
  3.  Copy receipt to target tier
  4.  Re-fetch from target — verify content_hash matches source
  5.  Verify PQC signature against content_hash (if present)
  6.  Mark status=VERIFIED in archival_index
  7.  Update tier + storage_location in archival_index
  8.  Delete from source tier
  9.  Mark status=ARCHIVED

Immutability guarantees
───────────────────────
  - WARM: INSERT-only (ON CONFLICT DO NOTHING, no UPDATE ever)
  - COLD: no-overwrite enforced (head_object before put_object)
  - COLD: object key derived from content_hash prefix — not mutable
  - COLD: boto3 put carries object-level Metadata for independent audit

COLD_STORAGE_REQUIRED
─────────────────────
  OMNIX_COLD_STORAGE_REQUIRED=true  → fail hard if no S3/R2 credentials
  OMNIX_COLD_STORAGE_REQUIRED=false → PostgreSQL fallback (dev/staging only)

ADR-126  /  MiFID II Article 25 — 5-year retention
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.ReceiptArchival")

# ── Table names ────────────────────────────────────────────────────────────────
HOT_TABLE   = "decision_receipts"
WARM_TABLE  = "decision_receipts_warm"
COLD_TABLE  = "decision_receipts_cold"   # PostgreSQL fallback only
INDEX_TABLE = "receipt_archival_index"

# ── Retention thresholds ───────────────────────────────────────────────────────
HOT_RETENTION_DAYS  = 30       # days before moving HOT → WARM
WARM_RETENTION_DAYS = 365      # days before moving WARM → COLD
COLD_RETENTION_DAYS = 5 * 365  # MiFID II: 5-year minimum

# ── Columns preserved across all tiers ────────────────────────────────────────
_HOT_COLUMNS: Tuple[str, ...] = (
    "receipt_id",
    "timestamp_utc",
    "asset",
    "decision",
    "veto_chain",
    "policy_version",
    "engine_version",
    "prev_hash",
    "content_hash",
    "signature",
    "signature_algorithm",
    "public_key",
    "client_id",
    "encrypted_payload",
    "retention_until",
    "domain",
    "created_at",
    "processing_time_ms",
)

# ── Archival status lifecycle ──────────────────────────────────────────────────
STATUS_PENDING  = "PENDING"
STATUS_COPYING  = "COPYING"
STATUS_VERIFIED = "VERIFIED"
STATUS_ARCHIVED = "ARCHIVED"
STATUS_ERROR    = "ERROR"

TIER_HOT  = "HOT"
TIER_WARM = "WARM"
TIER_COLD = "COLD"


# ── Exceptions ─────────────────────────────────────────────────────────────────

class ArchivalIntegrityError(RuntimeError):
    """Raised when post-copy hash or signature verification fails."""


class ColdStorageRequiredError(RuntimeError):
    """
    Raised at archival-daemon startup when OMNIX_COLD_STORAGE_REQUIRED=true
    but no S3/R2 credentials are configured.

    This is intentional: production systems must not silently fall back to
    PostgreSQL cold storage and believe they are institutionally compliant.
    """


# ── Internal helpers ───────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize_receipt(row: Dict) -> Dict:
    """
    Normalize a receipt row (from psycopg2 or dict) to a JSON-serializable dict.
    Datetime objects → ISO strings.  JSONB that arrived as dict stays as dict.
    """
    out: Dict = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif isinstance(v, (dict, list)):
            out[k] = v
        elif v is None:
            out[k] = None
        else:
            out[k] = v
    return out


def _extract_col(row: Dict, col: str) -> Any:
    """
    Extract a column value from a receipt dict, coercing JSONB to JSON string.
    veto_chain is stored as JSONB in PostgreSQL — we INSERT as JSON string.
    """
    v = row.get(col)
    if col == "veto_chain" and isinstance(v, (dict, list)):
        return json.dumps(v)
    return v


def _verify_pqc_signature(receipt: Dict) -> Optional[bool]:
    """
    Verify the PQC signature in a receipt dict.

    Returns:
      True  — signature verified
      False — signature present but invalid
      None  — no signature or provider unavailable
    """
    sig_b64 = receipt.get("signature")
    pub_b64 = receipt.get("public_key")
    content_hash = receipt.get("content_hash")

    if not sig_b64 or not pub_b64 or not content_hash:
        return None

    import base64
    try:
        from omnix_core.security.crypto_providers import get_provider, get_active_provider
        provider_id = receipt.get("signature_algorithm", "dilithium3")
        provider = None
        try:
            provider = get_provider(provider_id)
        except Exception:
            provider = get_active_provider()

        if provider:
            sig  = base64.b64decode(sig_b64)
            pub  = provider.deserialize_public_key(pub_b64)
            msg  = content_hash.encode("utf-8")
            return provider.verify(sig, msg, pub)
    except Exception as exc:
        logger.warning("[Archival] PQC verify error (non-fatal): %s", exc)

    return None


def _get_db_connection(db_url: str):
    try:
        import psycopg
        # FIX-3: connect_timeout=10 prevents the archival daemon from blocking
        # indefinitely on a slow or unreachable PostgreSQL host.
        return psycopg.connect(db_url, connect_timeout=10)
    except Exception as exc:
        logger.error("[Archival] DB connection failed: %s", exc)
        return None


# ── Cold storage backends ──────────────────────────────────────────────────────

class S3ColdBackend:
    """
    Cloudflare R2 / AWS S3 cold storage backend.

    Object key format:
        receipts/{year}/{month}/{hash8}/{receipt_id}.json

    Key is derived from content_hash prefix — same hash always maps to the
    same key, making accidental overwrites structurally impossible.

    Stored object format:
        {
          "receipt": { ...full receipt fields... },
          "metadata": {
            "archived_at":      "<ISO-8601>",
            "tier":             "cold",
            "hash":             "<content_hash>",
            "signature":        "<sig_b64 | null>",
            "version":          "v1",
            "immutable":        true,
            "archival_service": "OMNIX-ReceiptArchival-ADR126"
          }
        }
    """

    def __init__(
        self,
        bucket: str,
        endpoint_url: Optional[str],
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region: str = "auto",
    ):
        import boto3
        self.bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region,
        )

    def _make_key(self, receipt_id: str, content_hash: str, ts_utc: Any) -> str:
        try:
            if hasattr(ts_utc, "year"):
                year = ts_utc.year
                month = f"{ts_utc.month:02d}"
            else:
                dt = datetime.fromisoformat(str(ts_utc).replace("Z", "+00:00"))
                year, month = dt.year, f"{dt.month:02d}"
        except Exception:
            now = datetime.now(timezone.utc)
            year, month = now.year, f"{now.month:02d}"
        hash_prefix = (content_hash or "00000000")[:8]
        return f"receipts/{year}/{month}/{hash_prefix}/{receipt_id}.json"

    def put(self, receipt_dict: Dict, archived_at: str) -> str:
        """
        Store receipt in cold storage. No-overwrite enforced via head_object check.
        Returns the object key on success.
        Raises ArchivalIntegrityError if object exists with conflicting hash.
        """
        from botocore.exceptions import ClientError

        receipt_id   = receipt_dict.get("receipt_id", "UNKNOWN")
        content_hash = receipt_dict.get("content_hash", "")
        ts_utc       = receipt_dict.get("timestamp_utc") or receipt_dict.get("created_at")
        key          = self._make_key(receipt_id, content_hash, ts_utc)

        # No-overwrite check
        try:
            existing = self._client.head_object(Bucket=self.bucket, Key=key)
            stored_hash = existing.get("Metadata", {}).get("content_hash", "")
            if stored_hash and stored_hash != content_hash:
                raise ArchivalIntegrityError(
                    f"Cold object exists with conflicting hash "
                    f"key={key} stored={stored_hash} expected={content_hash}"
                )
            logger.info(
                "[COLD] Idempotent: receipt already in cold storage key=%s", key
            )
            return key
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "404":
                raise

        body = json.dumps(
            {
                "receipt": _serialize_receipt(receipt_dict),
                "metadata": {
                    "archived_at":      archived_at,
                    "tier":             "cold",
                    "hash":             content_hash,
                    "signature":        receipt_dict.get("signature"),
                    "version":          "v1",
                    "immutable":        True,
                    "archival_service": "OMNIX-ReceiptArchival-ADR126",
                },
            },
            sort_keys=True,
            ensure_ascii=True,
        ).encode("utf-8")

        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
            Metadata={
                "receipt_id":   receipt_id,
                "content_hash": content_hash,
                "archived_at":  archived_at,
                "tier":         "cold",
            },
        )
        logger.info("[COLD] Stored in object storage key=%s", key)
        return key

    def get(self, storage_location: str) -> Optional[Dict]:
        """Fetch and parse a receipt from cold storage by object key."""
        from botocore.exceptions import ClientError
        try:
            resp = self._client.get_object(Bucket=self.bucket, Key=storage_location)
            body = json.loads(resp["Body"].read().decode("utf-8"))
            return body.get("receipt")
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise

    def verify_exists(self, storage_location: str, expected_hash: str) -> bool:
        """Re-verify object exists in destination and content_hash matches."""
        from botocore.exceptions import ClientError
        try:
            resp = self._client.head_object(Bucket=self.bucket, Key=storage_location)
            stored_hash = resp.get("Metadata", {}).get("content_hash", "")
            return stored_hash == expected_hash
        except ClientError:
            return False


class PostgreSQLColdBackend:
    """
    PostgreSQL fallback for COLD tier — development and staging only.

    OMNIX_COLD_STORAGE_REQUIRED=true prevents this backend from being used
    in production.  If active, a prominent WARNING is logged for every
    receipt archived.
    """

    def put(self, receipt_dict: Dict, archived_at: str, conn) -> str:
        receipt_id = receipt_dict.get("receipt_id", "UNKNOWN")
        logger.warning(
            "[COLD-FALLBACK] receipt_id=%s stored in PostgreSQL cold table "
            "(NOT institutional-grade). "
            "Set OMNIX_COLD_S3_BUCKET + credentials for production archival.",
            receipt_id,
        )
        col_list     = ", ".join(list(_HOT_COLUMNS) + ["archived_at", "source_tier"])
        placeholders = ", ".join(["%s"] * (len(_HOT_COLUMNS) + 2))
        values       = [_extract_col(receipt_dict, c) for c in _HOT_COLUMNS]
        values      += [archived_at, TIER_WARM]

        cur = conn.cursor()
        cur.execute(
            f"""
            INSERT INTO {COLD_TABLE} ({col_list})
            VALUES ({placeholders})
            ON CONFLICT (receipt_id) DO NOTHING
            """,
            values,
        )
        cur.close()
        return f"pg::{COLD_TABLE}::{receipt_id}"

    def get(self, storage_location: str, conn) -> Optional[Dict]:
        receipt_id = storage_location.split("::")[-1]
        col_list   = ", ".join(_HOT_COLUMNS)
        cur        = conn.cursor()
        cur.execute(
            f"SELECT {col_list} FROM {COLD_TABLE} WHERE receipt_id = %s",
            (receipt_id,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return None
        return dict(zip(_HOT_COLUMNS, row))

    def verify_exists(
        self, storage_location: str, expected_hash: str, conn
    ) -> bool:
        receipt_id = storage_location.split("::")[-1]
        cur = conn.cursor()
        cur.execute(
            f"SELECT content_hash FROM {COLD_TABLE} WHERE receipt_id = %s",
            (receipt_id,),
        )
        row = cur.fetchone()
        cur.close()
        return row is not None and row[0] == expected_hash


# ── Archival service ───────────────────────────────────────────────────────────

class ReceiptArchivalService:
    """
    Orchestrates HOT → WARM → COLD archival with full cryptographic verification.

    Usage
    ─────
        svc = ReceiptArchivalService(db_url=os.environ["OMNIX_DB_URL"])
        svc.ensure_schema()
        svc.run_archival_cycle()  # called by daemon every N hours
    """

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        self._cold_backend: Optional[Any] = None
        self._cold_required: bool = (
            os.environ.get("OMNIX_COLD_STORAGE_REQUIRED", "false").lower() == "true"
        )
        self._warn_production_cold_flag()

    def _warn_production_cold_flag(self) -> None:
        """
        I-2 guard: emit CRITICAL log if running in production with cold storage
        flag disabled. This prevents silent non-compliance with MiFID II retention.
        Production is detected via RAILWAY_ENVIRONMENT, OMNIX_APP_ENV, or APP_ENV.
        """
        env = (
            os.environ.get("RAILWAY_ENVIRONMENT", "")
            or os.environ.get("OMNIX_APP_ENV", "")
            or os.environ.get("APP_ENV", "")
        ).lower()
        if env == "production" and not self._cold_required:
            logger.critical(
                "[Archival] PRODUCTION ENVIRONMENT DETECTED but "
                "OMNIX_COLD_STORAGE_REQUIRED=false. Receipts older than 12 months "
                "will be archived to PostgreSQL fallback instead of S3/R2. "
                "This may violate MiFID II Article 25 (5-year external retention). "
                "Set OMNIX_COLD_STORAGE_REQUIRED=true and configure S3/R2 credentials "
                "before the next archival cycle."
            )

    # ── Cold backend factory ───────────────────────────────────────────────────

    def _get_cold_backend(self) -> Any:
        """
        Return the appropriate cold backend, initializing lazily.

        Raises ColdStorageRequiredError if OMNIX_COLD_STORAGE_REQUIRED=true
        and no S3/R2 credentials are configured.
        """
        if self._cold_backend is not None:
            return self._cold_backend

        bucket       = os.environ.get("OMNIX_COLD_S3_BUCKET", "")
        endpoint_url = os.environ.get("OMNIX_COLD_S3_ENDPOINT_URL") or None
        access_key   = os.environ.get("AWS_ACCESS_KEY_ID", "")
        secret_key   = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        region       = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "auto"))

        if bucket and access_key and secret_key:
            logger.info(
                "[Archival] Cold backend: S3/R2 bucket=%s endpoint=%s",
                bucket, endpoint_url or "AWS default",
            )
            self._cold_backend = S3ColdBackend(
                bucket=bucket,
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region=region,
            )
            return self._cold_backend

        if self._cold_required:
            raise ColdStorageRequiredError(
                "OMNIX_COLD_STORAGE_REQUIRED=true but S3/R2 credentials are not "
                "configured. Set OMNIX_COLD_S3_BUCKET, AWS_ACCESS_KEY_ID, "
                "AWS_SECRET_ACCESS_KEY (and optionally OMNIX_COLD_S3_ENDPOINT_URL "
                "for Cloudflare R2). "
                "Refusing to fallback to PostgreSQL in production. "
                "Set OMNIX_COLD_STORAGE_REQUIRED=false for dev/staging fallback."
            )

        logger.warning(
            "[Archival] Cold backend: PostgreSQL fallback "
            "(dev/staging). Set OMNIX_COLD_S3_BUCKET for institutional cold storage."
        )
        self._cold_backend = PostgreSQLColdBackend()
        return self._cold_backend

    # ── Schema management ──────────────────────────────────────────────────────

    def ensure_schema(self, conn=None) -> bool:
        """
        Create WARM table, COLD fallback table, and archival_index.
        Safe to call multiple times (CREATE TABLE IF NOT EXISTS).
        Returns True on success, False on error.
        """
        own_conn = conn is None
        if own_conn:
            conn = _get_db_connection(self.db_url)
            if not conn:
                logger.error("[Archival] Cannot create schema — no DB connection")
                return False
        try:
            cur = conn.cursor()

            # WARM table — same as HOT + archival columns
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {WARM_TABLE} (
                    receipt_id          VARCHAR(64)  PRIMARY KEY,
                    timestamp_utc       TIMESTAMPTZ,
                    asset               VARCHAR(100),
                    decision            VARCHAR(20),
                    veto_chain          JSONB,
                    policy_version      VARCHAR(20),
                    engine_version      VARCHAR(20),
                    prev_hash           VARCHAR(64),
                    content_hash        VARCHAR(64),
                    signature           TEXT,
                    signature_algorithm VARCHAR(50),
                    public_key          TEXT,
                    client_id           VARCHAR(100),
                    encrypted_payload   TEXT,
                    retention_until     DATE,
                    domain              VARCHAR(50),
                    created_at          TIMESTAMPTZ,
                    processing_time_ms  INTEGER,
                    archived_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                    source_tier         VARCHAR(4)   NOT NULL DEFAULT 'HOT'
                )
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_warm_created_at
                ON {WARM_TABLE}(created_at)
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_warm_domain
                ON {WARM_TABLE}(domain)
            """)

            # COLD fallback table (PostgreSQL backend only)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {COLD_TABLE} (
                    receipt_id          VARCHAR(64)  PRIMARY KEY,
                    timestamp_utc       TIMESTAMPTZ,
                    asset               VARCHAR(100),
                    decision            VARCHAR(20),
                    veto_chain          JSONB,
                    policy_version      VARCHAR(20),
                    engine_version      VARCHAR(20),
                    prev_hash           VARCHAR(64),
                    content_hash        VARCHAR(64),
                    signature           TEXT,
                    signature_algorithm VARCHAR(50),
                    public_key          TEXT,
                    client_id           VARCHAR(100),
                    encrypted_payload   TEXT,
                    retention_until     DATE,
                    domain              VARCHAR(50),
                    created_at          TIMESTAMPTZ,
                    processing_time_ms  INTEGER,
                    archived_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                    source_tier         VARCHAR(4)   NOT NULL DEFAULT 'WARM'
                )
            """)

            # Archival metadata index — the PostgreSQL source of truth for all tiers
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {INDEX_TABLE} (
                    receipt_id          VARCHAR(64)  PRIMARY KEY,
                    tier                VARCHAR(4)   NOT NULL DEFAULT 'HOT',
                    storage_location    TEXT         NOT NULL,
                    content_hash        VARCHAR(64)  NOT NULL,
                    signature_prefix    VARCHAR(40),
                    original_ts_utc     TIMESTAMPTZ,
                    client_id           VARCHAR(100),
                    domain              VARCHAR(50),
                    archived_at         TIMESTAMPTZ  DEFAULT NOW(),
                    archival_status     VARCHAR(10)  NOT NULL DEFAULT 'PENDING',
                    archival_version    VARCHAR(4)   NOT NULL DEFAULT 'v1',
                    retry_count         INTEGER      NOT NULL DEFAULT 0,
                    last_error          TEXT
                )
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_archival_index_tier
                ON {INDEX_TABLE}(tier)
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_archival_index_status
                ON {INDEX_TABLE}(archival_status)
            """)

            conn.commit()
            cur.close()
            logger.info(
                "[Archival] Schema OK — %s, %s, %s, %s",
                WARM_TABLE, COLD_TABLE, INDEX_TABLE, HOT_TABLE,
            )
            return True
        except Exception as exc:
            logger.error("[Archival] Schema creation error: %s: %s", type(exc).__name__, exc)
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            if own_conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # ── Index helpers ──────────────────────────────────────────────────────────

    def _update_index(
        self,
        cur,
        receipt_id: str,
        tier: str,
        status: str,
        location: str,
        content_hash: str,
        signature: Optional[str] = None,
        original_ts: Any = None,
        client_id: Optional[str] = None,
        domain: Optional[str] = None,
        error: Optional[str] = None,
        increment_retry: bool = False,
    ) -> None:
        sig_prefix = (signature or "")[:40] if signature else None
        if increment_retry:
            cur.execute(
                f"""
                INSERT INTO {INDEX_TABLE}
                    (receipt_id, tier, storage_location, content_hash,
                     signature_prefix, original_ts_utc, client_id, domain,
                     archival_status, last_error, retry_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                ON CONFLICT (receipt_id) DO UPDATE SET
                    tier             = EXCLUDED.tier,
                    storage_location = EXCLUDED.storage_location,
                    archival_status  = EXCLUDED.archival_status,
                    last_error       = EXCLUDED.last_error,
                    retry_count      = {INDEX_TABLE}.retry_count + 1,
                    archived_at      = NOW()
                """,
                (receipt_id, tier, location, content_hash, sig_prefix,
                 original_ts, client_id, domain, status, error),
            )
        else:
            cur.execute(
                f"""
                INSERT INTO {INDEX_TABLE}
                    (receipt_id, tier, storage_location, content_hash,
                     signature_prefix, original_ts_utc, client_id, domain,
                     archival_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (receipt_id) DO UPDATE SET
                    tier             = EXCLUDED.tier,
                    storage_location = EXCLUDED.storage_location,
                    archival_status  = EXCLUDED.archival_status,
                    last_error       = %s,
                    archived_at      = NOW()
                """,
                (receipt_id, tier, location, content_hash, sig_prefix,
                 original_ts, client_id, domain, status, error),
            )

    # ── HOT → WARM migration ───────────────────────────────────────────────────

    def _migrate_one_hot_to_warm(self, conn, row: Dict) -> None:
        """
        Migrate one receipt from HOT to WARM.

        Protocol:
          1. Skip if already ARCHIVED in index
          2. Mark COPYING
          3. INSERT into WARM (ON CONFLICT DO NOTHING — idempotent)
          4. Re-fetch from WARM — verify content_hash
          5. Verify PQC signature
          6. Mark VERIFIED
          7. DELETE from HOT
          8. Mark ARCHIVED
        """
        receipt_id   = row["receipt_id"]
        content_hash = row.get("content_hash", "")
        signature    = row.get("signature")
        location     = f"pg::{WARM_TABLE}::{receipt_id}"

        cur = conn.cursor()

        # Step 1 — idempotency check
        cur.execute(
            f"SELECT archival_status FROM {INDEX_TABLE} WHERE receipt_id = %s",
            (receipt_id,),
        )
        existing = cur.fetchone()
        if existing and existing[0] == STATUS_ARCHIVED:
            cur.close()
            logger.debug("[HOT→WARM] Skip already-archived receipt_id=%s", receipt_id)
            return

        try:
            # Step 2 — mark COPYING
            self._update_index(
                cur, receipt_id, TIER_WARM, STATUS_COPYING, location,
                content_hash, signature,
                original_ts=row.get("timestamp_utc"),
                client_id=row.get("client_id"),
                domain=row.get("domain"),
            )
            conn.commit()

            # Step 3 — INSERT into WARM (idempotent)
            col_list     = ", ".join(list(_HOT_COLUMNS) + ["archived_at", "source_tier"])
            placeholders = ", ".join(["%s"] * (len(_HOT_COLUMNS) + 2))
            values       = [_extract_col(row, c) for c in _HOT_COLUMNS]
            values      += [_now_iso(), TIER_HOT]
            cur.execute(
                f"""
                INSERT INTO {WARM_TABLE} ({col_list})
                VALUES ({placeholders})
                ON CONFLICT (receipt_id) DO NOTHING
                """,
                values,
            )
            conn.commit()

            # Step 4 — re-fetch from WARM and verify hash
            cur.execute(
                f"SELECT content_hash FROM {WARM_TABLE} WHERE receipt_id = %s",
                (receipt_id,),
            )
            warm_row = cur.fetchone()
            if not warm_row:
                raise ArchivalIntegrityError(
                    f"Receipt not found in WARM after INSERT receipt_id={receipt_id}"
                )
            if warm_row[0] != content_hash:
                raise ArchivalIntegrityError(
                    f"Hash mismatch after WARM copy receipt_id={receipt_id} "
                    f"source={content_hash} dest={warm_row[0]}"
                )

            # Step 5 — verify PQC signature (non-fatal if provider unavailable)
            sig_valid = _verify_pqc_signature(row)
            if sig_valid is False:
                raise ArchivalIntegrityError(
                    f"PQC signature invalid for receipt_id={receipt_id} — "
                    "refusing to archive a tampered receipt"
                )

            # Step 6 — mark VERIFIED
            self._update_index(
                cur, receipt_id, TIER_WARM, STATUS_VERIFIED, location,
                content_hash, signature,
            )
            conn.commit()

            # Step 7 — delete from HOT
            cur.execute(
                f"DELETE FROM {HOT_TABLE} WHERE receipt_id = %s",
                (receipt_id,),
            )

            # Step 8 — mark ARCHIVED
            self._update_index(
                cur, receipt_id, TIER_WARM, STATUS_ARCHIVED, location,
                content_hash, signature,
            )
            conn.commit()

            logger.info(
                "[HOT→WARM] ✅ Archived receipt_id=%s hash=%s",
                receipt_id, content_hash[:16],
            )

        except ArchivalIntegrityError:
            conn.rollback()
            self._update_index(
                cur, receipt_id, TIER_WARM, STATUS_ERROR, location,
                content_hash, signature, error="ArchivalIntegrityError",
                increment_retry=True,
            )
            conn.commit()
            raise
        except Exception as exc:
            conn.rollback()
            self._update_index(
                cur, receipt_id, TIER_WARM, STATUS_ERROR, location,
                content_hash, signature, error=str(exc)[:200],
                increment_retry=True,
            )
            conn.commit()
            logger.error("[HOT→WARM] Error receipt_id=%s: %s", receipt_id, exc)
        finally:
            cur.close()

    def archive_hot_to_warm(self, conn) -> Tuple[int, int]:
        """
        Move all HOT receipts older than HOT_RETENTION_DAYS to WARM.
        Returns (archived_count, error_count).
        """
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT {', '.join(_HOT_COLUMNS)}
            FROM {HOT_TABLE}
            WHERE created_at < NOW() - INTERVAL '{HOT_RETENTION_DAYS} days'
            ORDER BY created_at ASC
            LIMIT 500
            """,
        )
        rows = cur.fetchall()
        cur.close()

        archived, errors = 0, 0
        for row_tuple in rows:
            row = dict(zip(_HOT_COLUMNS, row_tuple))
            try:
                self._migrate_one_hot_to_warm(conn, row)
                archived += 1
            except ArchivalIntegrityError as exc:
                logger.error("[HOT→WARM] Integrity failure: %s", exc)
                errors += 1
            except Exception as exc:
                logger.error("[HOT→WARM] Unexpected error: %s", exc)
                errors += 1

        if archived or errors:
            logger.info(
                "[HOT→WARM] Cycle complete — archived=%d errors=%d",
                archived, errors,
            )
        return archived, errors

    # ── WARM → COLD migration ──────────────────────────────────────────────────

    def _migrate_one_warm_to_cold(self, conn, row: Dict) -> None:
        """
        Migrate one receipt from WARM to COLD (S3/R2 or PostgreSQL fallback).

        Protocol:
          1. Skip if already ARCHIVED in index at COLD tier
          2. Mark COPYING
          3. Write to cold backend (no-overwrite enforced)
          4. Re-verify hash from destination
          5. Verify PQC signature
          6. Mark VERIFIED
          7. DELETE from WARM
          8. Update index to COLD/ARCHIVED
        """
        receipt_id   = row["receipt_id"]
        content_hash = row.get("content_hash", "")
        signature    = row.get("signature")
        archived_at  = _now_iso()
        cold_backend = self._get_cold_backend()

        cur = conn.cursor()

        # Step 1 — idempotency check
        cur.execute(
            f"SELECT tier, archival_status FROM {INDEX_TABLE} WHERE receipt_id = %s",
            (receipt_id,),
        )
        existing = cur.fetchone()
        if existing and existing[0] == TIER_COLD and existing[1] == STATUS_ARCHIVED:
            cur.close()
            logger.debug("[WARM→COLD] Skip already-cold receipt_id=%s", receipt_id)
            return

        location = f"pg::{COLD_TABLE}::{receipt_id}"   # default; overwritten for S3

        try:
            # Step 2 — mark COPYING
            self._update_index(
                cur, receipt_id, TIER_COLD, STATUS_COPYING, location,
                content_hash, signature,
                original_ts=row.get("timestamp_utc"),
                client_id=row.get("client_id"),
                domain=row.get("domain"),
            )
            conn.commit()

            # Step 3 — write to cold backend
            if isinstance(cold_backend, S3ColdBackend):
                location = cold_backend.put(_serialize_receipt(row), archived_at)
                conn_for_backend = None
            else:
                cold_backend.put(row, archived_at, conn)
                conn.commit()
                conn_for_backend = conn

            # Step 4 — re-verify hash from destination
            if isinstance(cold_backend, S3ColdBackend):
                ok = cold_backend.verify_exists(location, content_hash)
            else:
                ok = cold_backend.verify_exists(location, content_hash, conn)

            if not ok:
                raise ArchivalIntegrityError(
                    f"Destination verification failed for receipt_id={receipt_id} "
                    f"location={location}"
                )

            # Step 5 — verify PQC signature
            sig_valid = _verify_pqc_signature(row)
            if sig_valid is False:
                raise ArchivalIntegrityError(
                    f"PQC signature invalid for receipt_id={receipt_id} — "
                    "refusing to archive a tampered receipt"
                )

            # Step 6 — mark VERIFIED
            self._update_index(
                cur, receipt_id, TIER_COLD, STATUS_VERIFIED, location,
                content_hash, signature,
            )
            conn.commit()

            # Step 7 — delete from WARM
            cur.execute(
                f"DELETE FROM {WARM_TABLE} WHERE receipt_id = %s",
                (receipt_id,),
            )

            # Step 8 — mark ARCHIVED at COLD
            self._update_index(
                cur, receipt_id, TIER_COLD, STATUS_ARCHIVED, location,
                content_hash, signature,
            )
            conn.commit()

            logger.info(
                "[WARM→COLD] ✅ Archived receipt_id=%s location=%s hash=%s",
                receipt_id, location, content_hash[:16],
            )

        except ArchivalIntegrityError:
            conn.rollback()
            self._update_index(
                cur, receipt_id, TIER_COLD, STATUS_ERROR, location,
                content_hash, signature, error="ArchivalIntegrityError",
                increment_retry=True,
            )
            conn.commit()
            raise
        except Exception as exc:
            conn.rollback()
            self._update_index(
                cur, receipt_id, TIER_COLD, STATUS_ERROR, location,
                content_hash, signature, error=str(exc)[:200],
                increment_retry=True,
            )
            conn.commit()
            logger.error("[WARM→COLD] Error receipt_id=%s: %s", receipt_id, exc)
        finally:
            cur.close()

    def archive_warm_to_cold(self, conn) -> Tuple[int, int]:
        """
        Move all WARM receipts older than WARM_RETENTION_DAYS to COLD.
        Returns (archived_count, error_count).
        """
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT {', '.join(_HOT_COLUMNS)}
            FROM {WARM_TABLE}
            WHERE archived_at < NOW() - INTERVAL '{WARM_RETENTION_DAYS} days'
            ORDER BY archived_at ASC
            LIMIT 200
            """,
        )
        rows = cur.fetchall()
        cur.close()

        archived, errors = 0, 0
        for row_tuple in rows:
            row = dict(zip(_HOT_COLUMNS, row_tuple))
            try:
                self._migrate_one_warm_to_cold(conn, row)
                archived += 1
            except ColdStorageRequiredError:
                raise   # propagate — daemon must not continue silently
            except ArchivalIntegrityError as exc:
                logger.error("[WARM→COLD] Integrity failure: %s", exc)
                errors += 1
            except Exception as exc:
                logger.error("[WARM→COLD] Unexpected error: %s", exc)
                errors += 1

        if archived or errors:
            logger.info(
                "[WARM→COLD] Cycle complete — archived=%d errors=%d",
                archived, errors,
            )
        return archived, errors

    # ── Unified retrieval ──────────────────────────────────────────────────────

    def fetch_receipt_any_tier(
        self,
        conn,
        receipt_id: str,
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Search HOT → WARM → COLD for a receipt_id.

        Returns (receipt_dict, tier) or (None, None) if not found.

        1. Fast path: check HOT table directly.
        2. Check archival_index for tier + storage_location.
        3. Fetch from WARM or COLD accordingly.
        """
        col_list = ", ".join(_HOT_COLUMNS)
        rid = receipt_id.strip().upper()

        cur = conn.cursor()

        # 1. HOT — fast path (most recent receipts)
        cur.execute(
            f"SELECT {col_list} FROM {HOT_TABLE} WHERE receipt_id = %s",
            (rid,),
        )
        row = cur.fetchone()
        if row:
            cur.close()
            return dict(zip(_HOT_COLUMNS, row)), TIER_HOT

        # 2. Lookup archival_index
        cur.execute(
            f"""
            SELECT tier, storage_location, content_hash
            FROM {INDEX_TABLE}
            WHERE receipt_id = %s
            """,
            (rid,),
        )
        idx = cur.fetchone()
        cur.close()

        if not idx:
            return None, None

        tier, location, _ = idx

        if tier == TIER_WARM:
            cur2 = conn.cursor()
            cur2.execute(
                f"SELECT {col_list} FROM {WARM_TABLE} WHERE receipt_id = %s",
                (rid,),
            )
            row = cur2.fetchone()
            cur2.close()
            if row:
                return dict(zip(_HOT_COLUMNS, row)), TIER_WARM
            return None, None

        if tier == TIER_COLD:
            cold_backend = self._get_cold_backend()
            if isinstance(cold_backend, S3ColdBackend):
                receipt = cold_backend.get(location)
                return receipt, TIER_COLD
            else:
                receipt = cold_backend.get(location, conn)
                return receipt, TIER_COLD

        return None, None

    # ── Full archival cycle ────────────────────────────────────────────────────

    def run_archival_cycle(self) -> Dict[str, Any]:
        """
        Execute a full archival cycle (HOT→WARM and WARM→COLD).
        Called by the daemon thread.  Safe to call concurrently.
        Returns a summary dict for logging.
        """
        if not self.db_url:
            logger.warning("[Archival] No DB URL — cycle skipped")
            return {"skipped": True, "reason": "no_db_url"}

        conn = _get_db_connection(self.db_url)
        if not conn:
            return {"skipped": True, "reason": "db_connection_failed"}

        summary: Dict[str, Any] = {}
        try:
            self.ensure_schema(conn)

            hw_archived, hw_errors = self.archive_hot_to_warm(conn)
            summary["hot_to_warm"] = {"archived": hw_archived, "errors": hw_errors}

            wc_archived, wc_errors = self.archive_warm_to_cold(conn)
            summary["warm_to_cold"] = {"archived": wc_archived, "errors": wc_errors}

            summary["cycle_ts"] = _now_iso()
            summary["cold_backend"] = (
                "s3" if isinstance(self._cold_backend, S3ColdBackend)
                else "postgres_fallback"
                if isinstance(self._cold_backend, PostgreSQLColdBackend)
                else "uninitialized"
            )
        except ColdStorageRequiredError as exc:
            logger.error(
                "[Archival] ❌ COLD_STORAGE_REQUIRED=true but credentials missing: %s", exc
            )
            summary["error"] = "ColdStorageRequiredError"
            summary["message"] = str(exc)
        except Exception as exc:
            logger.error("[Archival] Cycle error: %s: %s", type(exc).__name__, exc)
            summary["error"] = type(exc).__name__
        finally:
            try:
                conn.close()
            except Exception:
                pass

        return summary
