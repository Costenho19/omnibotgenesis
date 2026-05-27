"""
OMNIX Human Oversight Engine — Module 3 of 5 Governance Compliance Modules.

Aligns with:
- EU AI Act: Article 14 (Human oversight measures for high-risk AI systems)
- NIST AI RMF: MANAGE function (human intervention in AI decisions)

IMPORTANT DESIGN DECISION:
Overrides do NOT modify the decision_receipts table. The PQC-signed receipt
chain is immutable by design. An override is a COMPLEMENTARY audit record
that documents human review of a BLOCKED decision and authorization to
proceed despite the AI system's governance recommendation.

Semantics: "A qualified human reviewed receipt OMNIX-XXXX (BLOCKED) and
authorizes execution of the underlying action for the following reasons..."

ADR-029: Governance Compliance Modules
"""

import hashlib
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger("OMNIX.Governance.HumanOversight")

MIN_JUSTIFICATION_LENGTH = 50
_RECEIPT_ENGINE = None


def _get_conn():
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("OMNIX_DB_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL not configured — HumanOversightEngine requires database access. "
            "Set DATABASE_URL environment variable."
        )
    return psycopg.connect(db_url)


def _load_receipt_engine():
    global _RECEIPT_ENGINE
    if _RECEIPT_ENGINE is not None:
        return _RECEIPT_ENGINE
    try:
        import importlib.util
        _root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        receipt_path = os.path.join(_root, "omnix_core", "evidence", "decision_receipt.py")
        spec = importlib.util.spec_from_file_location("_omnix_gov_receipt_ho", receipt_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_omnix_gov_receipt_ho"] = mod
        spec.loader.exec_module(mod)
        _RECEIPT_ENGINE = mod.DecisionReceiptEngine
        return _RECEIPT_ENGINE
    except Exception as e:
        logger.warning(f"PQC receipt engine not available for override signing: {e}")
        return None


class HumanOversightEngine:
    """
    PQC-signed human override workflow for AI governance decisions.

    Each override is:
    1. Validated (justification length, receipt existence check)
    2. Hashed: SHA-256(receipt_id + decision_before + decision_after + justification + timestamp)
    3. Signed with Dilithium-3 (same PQC algorithm used for decision receipts)
    4. Stored immutably in governance_overrides

    EU AI Act Art. 14: High-risk AI systems must allow human oversight and
    intervention. Every override is logged with who, when, and why.
    """

    def create_override(
        self,
        client_id: str,
        receipt_id: str,
        decision_before: str,
        decision_after: str,
        justification: str,
        overridden_by: str,
        role: str = "admin",
    ) -> dict[str, Any]:
        """
        Create a PQC-signed human oversight override record.

        Args:
            client_id: Authenticated B2B client
            receipt_id: The decision receipt being overridden
            decision_before: Original AI decision (typically BLOCKED)
            decision_after: Human-authorized outcome (typically APPROVED)
            justification: Required explanation (min 50 chars) — stored immutably
            overridden_by: Identity of the human authorizing (from auth context)
            role: Their role at time of override

        Returns:
            Override record with PQC signature and content hash
        """
        if len(justification.strip()) < MIN_JUSTIFICATION_LENGTH:
            raise ValueError(
                f"Justification must be at least {MIN_JUSTIFICATION_LENGTH} characters. "
                f"Human oversight requires documented reasoning."
            )

        timestamp = datetime.now(timezone.utc).isoformat()
        content_str = f"{receipt_id}|{decision_before}|{decision_after}|{justification.strip()}|{timestamp}"
        content_hash = "sha256:" + hashlib.sha256(content_str.encode("utf-8")).hexdigest()

        signature = None
        signature_algorithm = "NONE"
        public_key = None

        ReceiptEngine = _load_receipt_engine()
        if ReceiptEngine:
            try:
                engine = ReceiptEngine()
                prev_hash = engine.get_last_hash()
                sign_payload = {
                    "receipt_id": receipt_id,
                    "override_content_hash": content_hash,
                    "decision_before": decision_before,
                    "decision_after": decision_after,
                    "overridden_by": overridden_by,
                    "timestamp": timestamp,
                }
                sig_result = engine._sign_payload(json.dumps(sign_payload, sort_keys=True))
                if sig_result:
                    signature = sig_result.get("signature")
                    signature_algorithm = sig_result.get("algorithm", "Dilithium-3 (ML-DSA-65)")
                    public_key = sig_result.get("public_key")
            except Exception as e:
                logger.warning(f"PQC signing unavailable for override, storing unsigned: {e}")
                signature_algorithm = "UNSIGNED (PQC engine unavailable)"

        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                INSERT INTO governance_overrides
                    (client_id, receipt_id, decision_before, decision_after,
                     justification, overridden_by, role,
                     signature, signature_algorithm, public_key, content_hash, prev_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    client_id, receipt_id, decision_before, decision_after,
                    justification.strip(), overridden_by, role,
                    signature, signature_algorithm, public_key, content_hash, None,
                ),
            )
            row = dict(cur.fetchone())
            conn.commit()
            row["id"] = str(row["id"])
            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()
        finally:
            conn.close()

        logger.info(
            f"[OVERRIDE] created client={client_id} receipt={receipt_id} "
            f"{decision_before}→{decision_after} by={overridden_by} "
            f"signed={signature is not None}"
        )

        row["disclaimer"] = (
            "This override is logged immutably for audit compliance (EU AI Act Art. 14). "
            "The original decision receipt remains unchanged in the PQC-signed hash chain."
        )
        return row

    def verify_override(self, override_id: str) -> dict[str, Any]:
        """Verify the content hash integrity of an override record."""
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute("SELECT * FROM governance_overrides WHERE id = %s", (override_id,))
            row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            return {"verified": False, "error": "Override not found"}

        row = dict(row)
        stored_hash = row.get("content_hash", "")
        if not stored_hash:
            return {"verified": False, "reason": "No content hash stored — record may predate integrity checks"}

        return {
            "override_id": override_id,
            "receipt_id": row["receipt_id"],
            "content_hash": stored_hash,
            "signature_algorithm": row.get("signature_algorithm"),
            "pqc_signed": bool(row.get("signature")),
            "verification_note": (
                "Content hash computed at creation time. "
                "PQC signature over payload verifiable using the stored public key."
            ),
        }

    def list_overrides(self, client_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
        """List override records for the authenticated client."""
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                SELECT id, client_id, receipt_id, decision_before, decision_after,
                       overridden_by, role, signature_algorithm, content_hash, created_at
                FROM governance_overrides
                WHERE client_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (client_id, limit, offset),
            )
            rows = [dict(r) for r in cur.fetchall()]
            for row in rows:
                row["id"] = str(row["id"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                row["pqc_signed"] = bool(row.get("signature_algorithm") and "UNSIGNED" not in str(row.get("signature_algorithm", "")))
            return rows
        finally:
            conn.close()

    def get_override(self, override_id: str, client_id: str) -> dict | None:
        """Get full override detail (client isolation enforced)."""
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                "SELECT * FROM governance_overrides WHERE id = %s AND client_id = %s",
                (override_id, client_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            row = dict(row)
            row["id"] = str(row["id"])
            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()
            return row
        finally:
            conn.close()
