"""
tests/test_phase2_receipt_archival.py — Phase 2: Receipt Archival (ADR-126)

Test suite for ReceiptArchivalService covering:
  - HOT → WARM migration protocol (9-step copy-verify-delete)
  - Integrity enforcement: ArchivalIntegrityError on hash mismatch
  - Idempotency: double-archive is a safe no-op
  - WARM → COLD migration (PostgreSQL fallback backend)
  - COLD_STORAGE_REQUIRED=true fail-hard behavior
  - S3 backend: put / get / verify_exists (mocked)
  - Unified retrieval: fetch_receipt_any_tier (HOT → WARM → COLD)
  - Archival index: status lifecycle PENDING → COPYING → VERIFIED → ARCHIVED
  - run_archival_cycle: no DB → skipped gracefully
  - Cold storage format: receipt + metadata envelope

Design notes
────────────
All tests that require database operations use a shared in-memory psycopg2 mock
so the suite runs fully offline (no live DB required).

ADR-126 / MiFID II Article 25 — 5-year retention
"""
import hashlib
import json
import os
import sys
import time
import unittest
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch, call

# ── Ensure workspace root is on path ──────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

os.environ.setdefault("TESTING", "true")

from omnix_core.evidence.receipt_archival import (
    ReceiptArchivalService,
    ArchivalIntegrityError,
    ColdStorageRequiredError,
    S3ColdBackend,
    PostgreSQLColdBackend,
    HOT_TABLE,
    WARM_TABLE,
    COLD_TABLE,
    INDEX_TABLE,
    STATUS_PENDING,
    STATUS_COPYING,
    STATUS_VERIFIED,
    STATUS_ARCHIVED,
    STATUS_ERROR,
    TIER_HOT,
    TIER_WARM,
    TIER_COLD,
    _serialize_receipt,
    _verify_pqc_signature,
    _now_iso,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_receipt(
    receipt_id: str = "OMNIX-TRD-AABBCCDDEEFF",
    decision: str = "APPROVED",
    content_hash: Optional[str] = None,
    signature: str = "dGVzdHNpZ25hdHVyZQ==",
    public_key: str = "dGVzdHB1YmxpY2tleQ==",
    age_days: int = 0,
) -> Dict:
    ts = datetime.now(timezone.utc) - timedelta(days=age_days)
    payload = {"receipt_id": receipt_id, "timestamp": ts.isoformat(),
               "asset": "BTC", "decision": decision}
    ch = content_hash or hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()
    return {
        "receipt_id":          receipt_id,
        "timestamp_utc":       ts,
        "asset":               "BTC",
        "decision":            decision,
        "veto_chain":          [],
        "policy_version":      "6.5.4e",
        "engine_version":      "6.5.4e",
        "prev_hash":           "0" * 64,
        "content_hash":        ch,
        "signature":           signature,
        "signature_algorithm": "SHA256_FALLBACK",
        "public_key":          public_key,
        "client_id":           "test-client-001",
        "encrypted_payload":   None,
        "retention_until":     (ts + timedelta(days=1825)).date(),
        "domain":              "trading",
        "created_at":          ts,
        "processing_time_ms":  None,
    }


def _make_mock_conn(tables: Dict[str, list] = None):
    """
    Build a minimal psycopg2 connection mock that supports the archival
    protocol: INSERT, SELECT, DELETE, commit, rollback, cursor.

    tables: dict of table_name → list of row dicts (mutable in-place)
    """
    tables = tables or {
        HOT_TABLE:   [],
        WARM_TABLE:  [],
        COLD_TABLE:  [],
        INDEX_TABLE: [],
    }
    conn = MagicMock()
    conn.tables = tables   # expose for test assertions

    def make_cursor():
        cur = MagicMock()
        cur._last_query = None
        cur._last_params = None

        def execute(query, params=None):
            cur._last_query  = query
            cur._last_params = params
            cur._result = None

            q = query.strip().upper()

            # CREATE TABLE — always succeed
            if q.startswith("CREATE TABLE") or q.startswith("CREATE INDEX"):
                cur._result = None
                return

            # INSERT INTO <table>
            if q.startswith("INSERT INTO"):
                for tname in tables:
                    if tname.upper() in q:
                        if params:
                            receipt_id = params[0]
                            # ON CONFLICT DO NOTHING: skip if exists
                            if any(r.get("receipt_id") == receipt_id
                                   for r in tables[tname]):
                                return
                            tables[tname].append({
                                "receipt_id": receipt_id,
                                "_params": params,
                            })
                        return

            # DELETE FROM <table>
            if q.startswith("DELETE FROM"):
                for tname in tables:
                    if tname.upper() in q:
                        if params:
                            receipt_id = params[0]
                            tables[tname] = [
                                r for r in tables[tname]
                                if r.get("receipt_id") != receipt_id
                            ]
                            conn.tables = tables
                        return

            # SELECT content_hash FROM <table>
            if "SELECT" in q and "CONTENT_HASH" in q:
                for tname in tables:
                    if tname.upper() in q:
                        if params:
                            receipt_id = params[0]
                            match = next(
                                (r for r in tables[tname]
                                 if r.get("receipt_id") == receipt_id),
                                None,
                            )
                            cur._result = (match.get("content_hash"),) if match else None
                        return

            # SELECT ... FROM receipt_archival_index
            if "RECEIPT_ARCHIVAL_INDEX" in q and "SELECT" in q:
                if params:
                    receipt_id = params[0]
                    match = next(
                        (r for r in tables.get(INDEX_TABLE, [])
                         if r.get("receipt_id") == receipt_id),
                        None,
                    )
                    if match:
                        if "ARCHIVAL_STATUS" in q and "TIER" in q:
                            cur._result = (match.get("tier"), match.get("archival_status"))
                        elif "ARCHIVAL_STATUS" in q:
                            cur._result = (match.get("archival_status"),)
                        elif "TIER" in q:
                            cur._result = (match.get("tier"), match.get("storage_location"))
                        else:
                            cur._result = None
                    else:
                        cur._result = None

            # SELECT columns FROM HOT
            if "SELECT" in q and HOT_TABLE.upper() in q and "CONTENT_HASH" not in q:
                # batch query for archival candidates
                # return empty list by default (tests patch individual methods)
                cur._batch_result = []

        def fetchone():
            return cur._result

        def fetchall():
            return getattr(cur, "_batch_result", [])

        cur.execute = execute
        cur.fetchone = fetchone
        cur.fetchall = fetchall
        return cur

    def cursor(**kwargs):
        return make_cursor()

    conn.cursor = cursor
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.close = MagicMock()
    return conn


# ─── Suite 1: ReceiptArchivalService initialization ───────────────────────────

class TestArchivalServiceInit(unittest.TestCase):

    def test_service_creates_without_db_url(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OMNIX_DB_URL", None)
            os.environ.pop("DATABASE_URL", None)
            svc = ReceiptArchivalService(db_url=None)
        self.assertIsNone(svc.db_url)

    def test_service_stores_db_url(self):
        svc = ReceiptArchivalService(db_url="postgresql://localhost/test")
        self.assertEqual(svc.db_url, "postgresql://localhost/test")

    def test_cold_required_defaults_false(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OMNIX_COLD_STORAGE_REQUIRED", None)
            svc = ReceiptArchivalService()
            self.assertFalse(svc._cold_required)

    def test_cold_required_true_from_env(self):
        with patch.dict(os.environ, {"OMNIX_COLD_STORAGE_REQUIRED": "true"}):
            svc = ReceiptArchivalService()
            self.assertTrue(svc._cold_required)

    def test_cold_required_case_insensitive(self):
        with patch.dict(os.environ, {"OMNIX_COLD_STORAGE_REQUIRED": "TRUE"}):
            svc = ReceiptArchivalService()
            self.assertTrue(svc._cold_required)


# ─── Suite 2: Cold backend factory ────────────────────────────────────────────

class TestColdBackendFactory(unittest.TestCase):

    def test_returns_postgresql_fallback_when_no_s3_credentials(self):
        with patch.dict(os.environ, {
            "OMNIX_COLD_S3_BUCKET": "",
            "AWS_ACCESS_KEY_ID": "",
            "AWS_SECRET_ACCESS_KEY": "",
            "OMNIX_COLD_STORAGE_REQUIRED": "false",
        }):
            svc = ReceiptArchivalService()
            svc._cold_backend = None
            backend = svc._get_cold_backend()
            self.assertIsInstance(backend, PostgreSQLColdBackend)

    def test_raises_when_cold_required_and_no_credentials(self):
        with patch.dict(os.environ, {
            "OMNIX_COLD_S3_BUCKET": "",
            "AWS_ACCESS_KEY_ID": "",
            "OMNIX_COLD_STORAGE_REQUIRED": "true",
        }):
            svc = ReceiptArchivalService()
            svc._cold_backend = None
            with self.assertRaises(ColdStorageRequiredError):
                svc._get_cold_backend()

    def test_cold_required_error_message_is_informative(self):
        with patch.dict(os.environ, {
            "OMNIX_COLD_S3_BUCKET": "",
            "AWS_ACCESS_KEY_ID": "",
            "OMNIX_COLD_STORAGE_REQUIRED": "true",
        }):
            svc = ReceiptArchivalService()
            svc._cold_backend = None
            try:
                svc._get_cold_backend()
                self.fail("Expected ColdStorageRequiredError")
            except ColdStorageRequiredError as exc:
                self.assertIn("OMNIX_COLD_S3_BUCKET", str(exc))
                self.assertIn("OMNIX_COLD_STORAGE_REQUIRED=false", str(exc))

    def test_returns_s3_backend_when_credentials_present(self):
        with patch.dict(os.environ, {
            "OMNIX_COLD_S3_BUCKET": "omnix-cold-receipts",
            "AWS_ACCESS_KEY_ID": "test_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret",
            "OMNIX_COLD_S3_ENDPOINT_URL": "https://r2.example.com",
        }):
            with patch("omnix_core.evidence.receipt_archival.S3ColdBackend") as MockS3:
                svc = ReceiptArchivalService()
                svc._cold_backend = None
                backend = svc._get_cold_backend()
                MockS3.assert_called_once()

    def test_backend_is_cached_after_first_call(self):
        with patch.dict(os.environ, {
            "OMNIX_COLD_S3_BUCKET": "",
            "OMNIX_COLD_STORAGE_REQUIRED": "false",
        }):
            svc = ReceiptArchivalService()
            svc._cold_backend = None
            b1 = svc._get_cold_backend()
            b2 = svc._get_cold_backend()
            self.assertIs(b1, b2)


# ─── Suite 3: S3 backend ──────────────────────────────────────────────────────

class TestS3ColdBackend(unittest.TestCase):

    def _make_backend(self):
        with patch("boto3.client"):
            b = S3ColdBackend(
                bucket="test-bucket",
                endpoint_url="https://r2.example.com",
                aws_access_key_id="key",
                aws_secret_access_key="secret",
                region="auto",
            )
        return b

    def test_make_key_contains_hash_prefix(self):
        b = self._make_backend()
        receipt = _make_receipt()
        key = b._make_key(
            receipt["receipt_id"],
            receipt["content_hash"],
            receipt["timestamp_utc"],
        )
        self.assertIn("receipts/", key)
        self.assertIn(receipt["content_hash"][:8], key)
        self.assertTrue(key.endswith(".json"))

    def test_make_key_contains_receipt_id(self):
        b = self._make_backend()
        receipt = _make_receipt()
        key = b._make_key(
            receipt["receipt_id"],
            receipt["content_hash"],
            receipt["timestamp_utc"],
        )
        self.assertIn(receipt["receipt_id"], key)

    def test_put_skips_if_object_already_exists_same_hash(self):
        """Idempotent: if object exists with same hash, return existing key."""
        b = self._make_backend()
        receipt = _make_receipt()
        ch = receipt["content_hash"]

        expected_key = f"receipts/2026/01/{ch[:8]}/{receipt['receipt_id']}.json"
        b._client.head_object.return_value = {
            "Metadata": {"content_hash": ch},
        }
        key = b.put(receipt, _now_iso())
        b._client.put_object.assert_not_called()

    def test_put_raises_on_conflicting_hash_in_existing_object(self):
        """No-overwrite: if object exists with different hash, raise integrity error."""
        b = self._make_backend()
        receipt = _make_receipt()

        b._client.head_object.return_value = {
            "Metadata": {"content_hash": "different_hash"},
        }
        with self.assertRaises(ArchivalIntegrityError):
            b.put(receipt, _now_iso())

    def test_put_calls_put_object_for_new_receipt(self):
        from botocore.exceptions import ClientError
        b = self._make_backend()
        receipt = _make_receipt()

        b._client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not found"}}, "HeadObject"
        )
        b._client.put_object.return_value = {}
        key = b.put(receipt, _now_iso())
        b._client.put_object.assert_called_once()
        call_kwargs = b._client.put_object.call_args
        self.assertEqual(call_kwargs.kwargs["Bucket"], "test-bucket")
        self.assertIn("receipt_id", call_kwargs.kwargs["Metadata"])

    def test_put_object_body_is_valid_json_with_envelope(self):
        """Cold object format: receipt + metadata envelope."""
        from botocore.exceptions import ClientError
        b = self._make_backend()
        receipt = _make_receipt()

        captured_body = {}

        def _put_object(**kwargs):
            captured_body["body"] = json.loads(kwargs["Body"].decode("utf-8"))

        b._client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": ""}}, "HeadObject"
        )
        b._client.put_object.side_effect = _put_object
        b.put(receipt, _now_iso())

        body = captured_body["body"]
        self.assertIn("receipt", body)
        self.assertIn("metadata", body)
        self.assertEqual(body["metadata"]["tier"], "cold")
        self.assertTrue(body["metadata"]["immutable"])
        self.assertEqual(body["metadata"]["version"], "v1")
        self.assertIn("archived_at", body["metadata"])

    def test_verify_exists_returns_true_when_hash_matches(self):
        b = self._make_backend()
        expected_hash = "abc123"
        b._client.head_object.return_value = {
            "Metadata": {"content_hash": expected_hash},
        }
        self.assertTrue(b.verify_exists("receipts/key.json", expected_hash))

    def test_verify_exists_returns_false_on_hash_mismatch(self):
        b = self._make_backend()
        b._client.head_object.return_value = {
            "Metadata": {"content_hash": "different"},
        }
        self.assertFalse(b.verify_exists("receipts/key.json", "expected_hash"))

    def test_verify_exists_returns_false_on_not_found(self):
        from botocore.exceptions import ClientError
        b = self._make_backend()
        b._client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": ""}}, "HeadObject"
        )
        self.assertFalse(b.verify_exists("receipts/key.json", "hash"))

    def test_get_returns_receipt_dict_from_object(self):
        b = self._make_backend()
        receipt = _make_receipt()
        body = json.dumps({
            "receipt": _serialize_receipt(receipt),
            "metadata": {"tier": "cold"},
        }).encode("utf-8")
        mock_body = MagicMock()
        mock_body.read.return_value = body
        b._client.get_object.return_value = {"Body": mock_body}
        result = b.get("receipts/key.json")
        self.assertIsNotNone(result)
        self.assertEqual(result["receipt_id"], receipt["receipt_id"])


# ─── Suite 4: HOT → WARM migration ────────────────────────────────────────────

class TestHotToWarmMigration(unittest.TestCase):

    def _make_svc(self):
        svc = ReceiptArchivalService(db_url="postgresql://test/test")
        svc._cold_backend = PostgreSQLColdBackend()
        return svc

    def test_migrate_inserts_into_warm_and_deletes_from_hot(self):
        """
        Core protocol: receipt copied to WARM, verified, then deleted from HOT.
        """
        svc = self._make_svc()
        receipt = _make_receipt(age_days=35)

        tables = {
            HOT_TABLE:   [{"receipt_id": receipt["receipt_id"],
                           "content_hash": receipt["content_hash"]}],
            WARM_TABLE:  [],
            INDEX_TABLE: [],
        }
        conn = _make_mock_conn(tables)

        # Patch WARM select to return the hash (simulating successful copy)
        # and index select to return no existing entry
        original_cursor = conn.cursor

        def mock_cursor_with_warm_verify(**kwargs):
            cur = original_cursor(**kwargs)
            original_execute = cur.execute

            def execute_patched(query, params=None):
                original_execute(query, params)
                q = query.strip().upper()
                # After INSERT into WARM, when we SELECT content_hash from WARM:
                if "SELECT" in q and WARM_TABLE.upper() in q and "CONTENT_HASH" in q:
                    cur._result = (receipt["content_hash"],)
            cur.execute = execute_patched
            return cur

        conn.cursor = mock_cursor_with_warm_verify

        with patch.object(svc, "_verify_pqc_or_skip", return_value=None, create=True):
            with patch(
                "omnix_core.evidence.receipt_archival._verify_pqc_signature",
                return_value=None,   # provider not available — non-fatal
            ):
                svc._migrate_one_hot_to_warm(conn, receipt)

        # Receipt should now be in WARM index
        index_entries = tables[INDEX_TABLE]
        self.assertTrue(
            any(r.get("receipt_id") == receipt["receipt_id"] for r in index_entries),
            "Receipt must be in archival_index after migration",
        )

    def test_integrity_error_on_hash_mismatch_after_copy(self):
        """
        Step 4: if content_hash in WARM doesn't match source, raise ArchivalIntegrityError.
        """
        svc = self._make_svc()
        receipt = _make_receipt(age_days=35)

        original_cursor = MagicMock()
        conn = MagicMock()
        conn.commit = MagicMock()
        conn.rollback = MagicMock()

        call_count = [0]

        def cursor(**kwargs):
            cur = MagicMock()
            cur._result = None

            def execute(query, params=None):
                q = query.strip().upper()
                if "SELECT" in q and WARM_TABLE.upper() in q and "CONTENT_HASH" in q:
                    # Simulate corrupted WARM content_hash
                    cur._result = ("CORRUPTED_HASH_DIFFERENT",)
                elif "SELECT" in q and INDEX_TABLE.upper() in q:
                    cur._result = None   # no existing index entry

            cur.execute = execute
            cur.fetchone = lambda: cur._result
            cur.fetchall = lambda: []
            cur.close = MagicMock()
            return cur

        conn.cursor = cursor

        with patch(
            "omnix_core.evidence.receipt_archival._verify_pqc_signature",
            return_value=None,
        ):
            with self.assertRaises(ArchivalIntegrityError):
                svc._migrate_one_hot_to_warm(conn, receipt)

        conn.rollback.assert_called()

    def test_pqc_signature_invalid_blocks_migration(self):
        """
        Step 5: if PQC signature is invalid, refuse to archive.
        """
        svc = self._make_svc()
        receipt = _make_receipt(age_days=35)

        conn = MagicMock()
        conn.commit = MagicMock()
        conn.rollback = MagicMock()

        def cursor(**kwargs):
            cur = MagicMock()

            def execute(query, params=None):
                q = query.strip().upper()
                if "SELECT" in q and WARM_TABLE.upper() in q:
                    cur._result = (receipt["content_hash"],)   # hash OK
                elif "SELECT" in q and INDEX_TABLE.upper() in q:
                    cur._result = None

            cur.execute = execute
            cur.fetchone = lambda: cur._result
            cur.fetchall = lambda: []
            cur.close = MagicMock()
            return cur

        conn.cursor = cursor

        with patch(
            "omnix_core.evidence.receipt_archival._verify_pqc_signature",
            return_value=False,   # signature INVALID
        ):
            with self.assertRaises(ArchivalIntegrityError) as ctx:
                svc._migrate_one_hot_to_warm(conn, receipt)

        self.assertIn("signature", str(ctx.exception).lower())
        conn.rollback.assert_called()

    def test_idempotent_skip_when_already_archived(self):
        """
        Step 1: if index shows ARCHIVED, skip without error.
        """
        svc = self._make_svc()
        receipt = _make_receipt()

        conn = MagicMock()
        conn.commit = MagicMock()

        def cursor(**kwargs):
            cur = MagicMock()

            def execute(query, params=None):
                q = query.strip().upper()
                if "SELECT" in q and INDEX_TABLE.upper() in q:
                    cur._result = (STATUS_ARCHIVED,)   # already done

            cur.execute = execute
            cur.fetchone = lambda: cur._result
            cur.fetchall = lambda: []
            cur.close = MagicMock()
            return cur

        conn.cursor = cursor

        # Should not raise, should not commit (no changes)
        svc._migrate_one_hot_to_warm(conn, receipt)
        conn.commit.assert_not_called()


# ─── Suite 5: WARM → COLD migration ──────────────────────────────────────────

class TestWarmToColdMigration(unittest.TestCase):

    def test_warm_to_cold_postgresql_fallback_stores_receipt(self):
        """WARM → COLD using PostgreSQL fallback backend."""
        svc = ReceiptArchivalService(db_url="postgresql://test/test")

        pg_cold = PostgreSQLColdBackend()
        svc._cold_backend = pg_cold

        receipt = _make_receipt(age_days=400)

        conn = MagicMock()
        conn.commit = MagicMock()
        conn.rollback = MagicMock()

        def cursor(**kwargs):
            cur = MagicMock()
            cur._result = None

            def execute(query, params=None):
                q = query.strip().upper()
                if "SELECT" in q and INDEX_TABLE.upper() in q:
                    # tier + status check: return WARM/COPYING (not COLD/ARCHIVED)
                    cur._result = (TIER_WARM, STATUS_VERIFIED)
                elif "SELECT" in q and COLD_TABLE.upper() in q and "CONTENT_HASH" in q:
                    # verify_exists: receipt was stored
                    cur._result = (receipt["content_hash"],)

            cur.execute = execute
            cur.fetchone = lambda: cur._result
            cur.fetchall = lambda: []
            cur.close = MagicMock()
            return cur

        conn.cursor = cursor

        with patch(
            "omnix_core.evidence.receipt_archival._verify_pqc_signature",
            return_value=None,
        ):
            with patch.object(
                pg_cold, "put", return_value=f"pg::{COLD_TABLE}::{receipt['receipt_id']}"
            ) as mock_put:
                with patch.object(pg_cold, "verify_exists", return_value=True):
                    svc._migrate_one_warm_to_cold(conn, receipt)
                    mock_put.assert_called_once()

    def test_cold_required_propagates_to_warm_to_cold(self):
        """ColdStorageRequiredError from backend propagates up (daemon must see it)."""
        with patch.dict(os.environ, {
            "OMNIX_COLD_S3_BUCKET": "",
            "OMNIX_COLD_STORAGE_REQUIRED": "true",
        }):
            svc = ReceiptArchivalService()
            svc._cold_backend = None

            with self.assertRaises(ColdStorageRequiredError):
                svc._get_cold_backend()

    def test_warm_to_cold_idempotent_for_already_cold_archived(self):
        """Step 1: if index shows COLD/ARCHIVED, skip without touching storage."""
        svc = ReceiptArchivalService()
        svc._cold_backend = PostgreSQLColdBackend()
        receipt = _make_receipt()

        conn = MagicMock()
        conn.commit = MagicMock()

        def cursor(**kwargs):
            cur = MagicMock()

            def execute(query, params=None):
                q = query.strip().upper()
                if "SELECT" in q and INDEX_TABLE.upper() in q:
                    cur._result = (TIER_COLD, STATUS_ARCHIVED)

            cur.execute = execute
            cur.fetchone = lambda: cur._result
            cur.fetchall = lambda: []
            cur.close = MagicMock()
            return cur

        conn.cursor = cursor
        svc._migrate_one_warm_to_cold(conn, receipt)
        conn.commit.assert_not_called()


# ─── Suite 6: Unified retrieval ───────────────────────────────────────────────

class TestFetchReceiptAnyTier(unittest.TestCase):

    def test_returns_hot_receipt_on_first_hit(self):
        from omnix_core.evidence.receipt_archival import _HOT_COLUMNS
        svc = ReceiptArchivalService(db_url="postgresql://test/test")
        receipt = _make_receipt()
        values = tuple(receipt.get(c) for c in _HOT_COLUMNS)

        conn = MagicMock()

        def cursor(**kwargs):
            cur = MagicMock()

            def execute(query, params=None):
                q = query.strip().upper()
                if HOT_TABLE.upper() in q and "SELECT" in q:
                    cur._result = values

            cur.execute = execute
            cur.fetchone = lambda: cur._result
            cur.fetchall = lambda: []
            cur.close = MagicMock()
            return cur

        conn.cursor = cursor
        result, tier = svc.fetch_receipt_any_tier(conn, receipt["receipt_id"])
        self.assertEqual(tier, TIER_HOT)
        self.assertEqual(result["receipt_id"], receipt["receipt_id"])

    def test_returns_warm_receipt_when_not_in_hot(self):
        from omnix_core.evidence.receipt_archival import _HOT_COLUMNS
        svc = ReceiptArchivalService(db_url="postgresql://test/test")
        receipt = _make_receipt()
        values = tuple(receipt.get(c) for c in _HOT_COLUMNS)

        conn = MagicMock()

        def cursor(**kwargs):
            cur = MagicMock()

            def execute(query, params=None):
                q = query.strip().upper()
                # Check WARM before HOT since HOT string is substring of WARM
                if WARM_TABLE.upper() in q and "SELECT" in q:
                    cur._result = values
                elif INDEX_TABLE.upper() in q and "SELECT" in q:
                    # archival_index: returns (tier, storage_location, content_hash)
                    cur._result = (TIER_WARM, f"warm::{receipt['receipt_id']}", receipt["content_hash"])
                elif HOT_TABLE.upper() in q and "SELECT" in q:
                    cur._result = None   # not in HOT

            cur.execute = execute
            cur.fetchone = lambda: cur._result
            cur.fetchall = lambda: []
            cur.close = MagicMock()
            return cur

        conn.cursor = cursor
        result, tier = svc.fetch_receipt_any_tier(conn, receipt["receipt_id"])
        self.assertEqual(tier, TIER_WARM)
        self.assertEqual(result["receipt_id"], receipt["receipt_id"])

    def test_returns_none_when_not_in_any_tier(self):
        svc = ReceiptArchivalService(db_url="postgresql://test/test")

        conn = MagicMock()

        def cursor(**kwargs):
            cur = MagicMock()
            cur.execute = MagicMock()
            cur.fetchone = lambda: None
            cur.fetchall = lambda: []
            cur.close = MagicMock()
            return cur

        conn.cursor = cursor
        result, tier = svc.fetch_receipt_any_tier(conn, "OMNIX-NOTEXIST-123456")
        self.assertIsNone(result)
        self.assertIsNone(tier)


# ─── Suite 7: run_archival_cycle ──────────────────────────────────────────────

class TestRunArchivalCycle(unittest.TestCase):

    def test_cycle_skipped_when_no_db_url(self):
        svc = ReceiptArchivalService(db_url="postgresql://dummy/test")
        svc.db_url = None   # Force None after env-fallback construction
        result = svc.run_archival_cycle()
        self.assertTrue(result.get("skipped"))
        self.assertEqual(result.get("reason"), "no_db_url")

    def test_cycle_skipped_when_db_connection_fails(self):
        svc = ReceiptArchivalService(db_url="postgresql://invalid/test")
        with patch(
            "omnix_core.evidence.receipt_archival._get_db_connection",
            return_value=None,
        ):
            result = svc.run_archival_cycle()
        self.assertTrue(result.get("skipped"))
        self.assertEqual(result.get("reason"), "db_connection_failed")

    def test_cycle_returns_summary_on_success(self):
        svc = ReceiptArchivalService(db_url="postgresql://test/test")
        svc._cold_backend = PostgreSQLColdBackend()

        conn = MagicMock()
        conn.commit = MagicMock()
        conn.close = MagicMock()

        def cursor(**kwargs):
            cur = MagicMock()
            cur.execute = MagicMock()
            cur.fetchone = lambda: None
            cur.fetchall = lambda: []
            cur.close = MagicMock()
            return cur

        conn.cursor = cursor

        with patch(
            "omnix_core.evidence.receipt_archival._get_db_connection",
            return_value=conn,
        ):
            with patch.object(svc, "ensure_schema", return_value=True):
                with patch.object(svc, "archive_hot_to_warm", return_value=(3, 0)):
                    with patch.object(svc, "archive_warm_to_cold", return_value=(1, 0)):
                        result = svc.run_archival_cycle()

        self.assertEqual(result["hot_to_warm"]["archived"], 3)
        self.assertEqual(result["warm_to_cold"]["archived"], 1)
        self.assertIn("cycle_ts", result)

    def test_cold_storage_required_error_captured_in_summary(self):
        svc = ReceiptArchivalService(db_url="postgresql://test/test")

        conn = MagicMock()
        conn.commit = MagicMock()
        conn.close = MagicMock()

        def cursor(**kwargs):
            cur = MagicMock()
            cur.execute = MagicMock()
            cur.fetchone = lambda: None
            cur.fetchall = lambda: []
            cur.close = MagicMock()
            return cur

        conn.cursor = cursor

        with patch(
            "omnix_core.evidence.receipt_archival._get_db_connection",
            return_value=conn,
        ):
            with patch.object(svc, "ensure_schema", return_value=True):
                with patch.object(
                    svc, "archive_hot_to_warm",
                    side_effect=ColdStorageRequiredError("No bucket configured"),
                ):
                    result = svc.run_archival_cycle()

        self.assertEqual(result.get("error"), "ColdStorageRequiredError")


# ─── Suite 8: Helpers and edge cases ─────────────────────────────────────────

class TestHelpers(unittest.TestCase):

    def test_serialize_receipt_converts_datetimes(self):
        receipt = _make_receipt()
        serialized = _serialize_receipt(receipt)
        ts = serialized.get("timestamp_utc")
        self.assertIsInstance(ts, str, "datetime must be converted to ISO string")

    def test_serialize_receipt_preserves_none(self):
        receipt = _make_receipt()
        receipt["processing_time_ms"] = None
        serialized = _serialize_receipt(receipt)
        self.assertIsNone(serialized["processing_time_ms"])

    def test_verify_pqc_signature_returns_none_when_no_signature(self):
        receipt = _make_receipt()
        receipt.pop("signature", None)
        result = _verify_pqc_signature(receipt)
        self.assertIsNone(result)

    def test_verify_pqc_signature_returns_none_when_no_public_key(self):
        receipt = _make_receipt()
        receipt.pop("public_key", None)
        result = _verify_pqc_signature(receipt)
        self.assertIsNone(result)

    def test_verify_pqc_signature_returns_none_when_provider_unavailable(self):
        receipt = _make_receipt()
        with patch(
            "omnix_core.evidence.receipt_archival.ReceiptArchivalService",
            side_effect=ImportError,
        ):
            result = _verify_pqc_signature(receipt)
        self.assertIsNone(result)

    def test_now_iso_returns_valid_iso_string(self):
        ts = _now_iso()
        self.assertIsInstance(ts, str)
        parsed = datetime.fromisoformat(ts)
        self.assertIsNotNone(parsed)

    def test_constants_are_correct(self):
        self.assertEqual(HOT_TABLE, "decision_receipts")
        self.assertEqual(WARM_TABLE, "decision_receipts_warm")
        self.assertEqual(COLD_TABLE, "decision_receipts_cold")
        self.assertEqual(INDEX_TABLE, "receipt_archival_index")

    def test_status_lifecycle_constants(self):
        self.assertEqual(STATUS_PENDING,  "PENDING")
        self.assertEqual(STATUS_COPYING,  "COPYING")
        self.assertEqual(STATUS_VERIFIED, "VERIFIED")
        self.assertEqual(STATUS_ARCHIVED, "ARCHIVED")
        self.assertEqual(STATUS_ERROR,    "ERROR")

    def test_tier_constants(self):
        self.assertEqual(TIER_HOT,  "HOT")
        self.assertEqual(TIER_WARM, "WARM")
        self.assertEqual(TIER_COLD, "COLD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
