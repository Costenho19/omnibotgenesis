"""
OMNIX VC Trust Revocation Registry — ADR-130
W3C StatusList2021 compatible revocation for OMNIX Governance Credentials.

Architecture Decision: ADR-130
Spec references:
  - W3C Status List 2021: https://www.w3.org/TR/2023/WD-vc-status-list-20230427/
  - W3C Verifiable Credentials 1.1: https://www.w3.org/TR/vc-data-model/
  - eIDAS 2.0 / EUDI ARF 1.4 — revocation requirements
  - Dr. Todd M. Price observation (2026-04-26): "Who can revoke that trust —
    and what happens when they do?" — the shift from observational to enforceable.

Status lifecycle:
  active     → initial state for all issued VCs (default — innocent until revoked)
  revoked    → credential is invalidated. Tamper-detection + reason mandatory.
  suspended  → temporary, pending investigation. May be reinstated.

Revocation is append-only. The audit_trail JSONB column carries every state
transition with timestamp, actor, and reason. Nothing is ever deleted.

Human accountability (ADR-124 integration):
  revoked_by can be:
    - a client_id (B2B client with admin role)
    - 'system:avm'   (Assumption Validity Monitor auto-revocation)
    - 'system:ebip'  (Execution Boundary Integrity Protocol)
    - 'system:anomaly' (AnomalyResponseEngine — ADR-129)
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("OMNIX.Revocation")

OMNIX_ISSUER_URL = "https://omnixquantum.net"


def _get_db_conn():
    """Obtain a raw psycopg2 connection — consistent with server.py pattern."""
    import psycopg2
    db_url = (
        os.environ.get("DATABASE_URL") or
        os.environ.get("OMNIX_DB_URL") or
        os.environ.get("POSTGRES_URL")
    )
    if not db_url:
        raise RuntimeError("No database URL configured (OMNIX_DB_URL)")
    return psycopg2.connect(db_url)


def _require_admin_auth(request) -> Tuple[Optional[str], Optional[Any]]:
    """
    Validates admin-level auth for revocation operations.
    Checks X-API-Key against b2b_clients with role='admin'.
    Returns (client_id, None) on success or (None, flask_response) on failure.
    """
    from flask import jsonify

    api_key = (
        request.headers.get("X-API-Key") or
        request.headers.get("x-api-key")
    )
    if not api_key:
        return None, (jsonify({
            "error": "Missing X-API-Key header.",
            "hint":  "Revocation requires admin-level authentication.",
        }), 401)

    import hashlib
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    try:
        conn = _get_db_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT client_id, role FROM b2b_clients WHERE key_hash = %s AND active = true",
                (key_hash,),
            )
            row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error(f"Admin auth DB error: {e}")
        return None, (jsonify({"error": "Authentication service unavailable."}), 503)

    if not row:
        return None, (jsonify({"error": "Invalid or inactive API key."}), 401)

    client_id, role = row
    if role != "admin":
        return None, (jsonify({
            "error": "Insufficient privileges. Revocation requires admin role.",
            "your_role": role,
        }), 403)

    return client_id, None


class VCRevocationRegistry:
    """
    Core revocation logic — stateless, DB-backed.

    Usage:
        registry = VCRevocationRegistry()
        status   = registry.get_status("OMNIX-TRD-aabb1122ccdd3344")
        event    = registry.revoke("OMNIX-TRD-...", reason="fraud_detected",
                                   revoked_by="system:avm")
    """

    def get_status(self, receipt_id: str) -> Dict[str, Any]:
        """
        Returns the current revocation status of a VC.
        Innocent-until-revoked: if the receipt_id is not in the registry,
        status = 'active'. This avoids requiring a registry write at VC issuance.

        Returns:
            {
                "receipt_id":    str,
                "status":        "active" | "revoked" | "suspended",
                "revoked_at":    ISO8601 | None,
                "revoked_by":    str | None,
                "reason":        str | None,
                "reinstate_url": str | None,  (only if suspended)
                "checked_at":    ISO8601,
                "vc_status_url": str,
            }
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        status_url = f"{OMNIX_ISSUER_URL}/api/trust/vc-status/{receipt_id}"

        try:
            conn = _get_db_conn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT status, reason, revoked_by, revoked_at,
                           reinstated_at, reinstatement_reason
                    FROM vc_revocation_registry
                    WHERE receipt_id = %s
                    """,
                    (receipt_id,),
                )
                row = cur.fetchone()
            conn.close()
        except Exception as e:
            logger.error(f"get_status DB error for {receipt_id}: {e}")
            return {
                "receipt_id":    receipt_id,
                "status":        "unknown",
                "error":         "Revocation registry temporarily unavailable.",
                "checked_at":    now_iso,
                "vc_status_url": status_url,
            }

        if not row:
            return {
                "receipt_id":    receipt_id,
                "status":        "active",
                "revoked_at":    None,
                "revoked_by":    None,
                "reason":        None,
                "checked_at":    now_iso,
                "vc_status_url": status_url,
                "note":          "Not found in revocation registry — credential is active.",
            }

        status, reason, revoked_by, revoked_at, reinstated_at, reinstate_reason = row
        return {
            "receipt_id":         receipt_id,
            "status":             status,
            "reason":             reason,
            "revoked_by":         revoked_by,
            "revoked_at":         revoked_at.isoformat() if revoked_at else None,
            "reinstated_at":      reinstated_at.isoformat() if reinstated_at else None,
            "reinstatement_reason": reinstate_reason,
            "checked_at":         now_iso,
            "vc_status_url":      status_url,
        }

    def revoke(
        self,
        receipt_id: str,
        reason: str,
        revoked_by: str,
        status: str = "revoked",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Revokes or suspends a VC. Creates or updates the registry entry.

        Args:
            receipt_id: The OMNIX receipt_id of the VC to revoke.
            reason:     Human-readable reason (mandatory, min 10 chars).
            revoked_by: client_id or 'system:avm' / 'system:ebip' / 'system:anomaly'.
            status:     'revoked' (permanent) or 'suspended' (temporary). Default: 'revoked'.
            context:    Optional JSONB payload — market conditions, regulatory basis, etc.

        Returns: updated status dict.
        """
        if status not in ("revoked", "suspended"):
            raise ValueError("status must be 'revoked' or 'suspended'")
        if not reason or len(reason.strip()) < 10:
            raise ValueError("reason must be at least 10 characters.")

        now = datetime.now(timezone.utc)
        audit_entry = {
            "action":     status,
            "actor":      revoked_by,
            "reason":     reason,
            "timestamp":  now.isoformat(),
            "context":    context or {},
        }

        try:
            conn = _get_db_conn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO vc_revocation_registry
                        (receipt_id, status, reason, revoked_by, revoked_at,
                         revocation_context, audit_trail, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, NOW())
                    ON CONFLICT (receipt_id) DO UPDATE SET
                        status             = EXCLUDED.status,
                        reason             = EXCLUDED.reason,
                        revoked_by         = EXCLUDED.revoked_by,
                        revoked_at         = EXCLUDED.revoked_at,
                        revocation_context = EXCLUDED.revocation_context,
                        audit_trail        = vc_revocation_registry.audit_trail ||
                                             EXCLUDED.audit_trail::jsonb,
                        updated_at         = NOW()
                    """,
                    (
                        receipt_id,
                        status,
                        reason,
                        revoked_by,
                        now,
                        json.dumps(context or {}),
                        json.dumps([audit_entry]),
                    ),
                )
                conn.commit()
            conn.close()
            logger.warning(
                f"[Revocation] {receipt_id} → {status.upper()} | by={revoked_by} | reason={reason[:80]}"
            )
        except Exception as e:
            logger.error(f"revoke DB error for {receipt_id}: {e}")
            raise

        return self.get_status(receipt_id)

    def reinstate(
        self,
        receipt_id: str,
        reason: str,
        reinstated_by: str,
    ) -> Dict[str, Any]:
        """
        Reinstates a suspended or revoked VC. Requires explicit justification.
        Audit trail is preserved — the original revocation event is not erased.

        Args:
            receipt_id:    The VC to reinstate.
            reason:        Justification for reinstatement (min 20 chars).
            reinstated_by: client_id or system actor.
        """
        if not reason or len(reason.strip()) < 20:
            raise ValueError("Reinstatement reason must be at least 20 characters.")

        now = datetime.now(timezone.utc)
        audit_entry = {
            "action":    "reinstated",
            "actor":     reinstated_by,
            "reason":    reason,
            "timestamp": now.isoformat(),
        }

        try:
            conn = _get_db_conn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE vc_revocation_registry SET
                        status               = 'active',
                        reinstated_at        = %s,
                        reinstatement_reason = %s,
                        audit_trail          = audit_trail || %s::jsonb,
                        updated_at           = NOW()
                    WHERE receipt_id = %s
                    RETURNING receipt_id
                    """,
                    (now, reason, json.dumps([audit_entry]), receipt_id),
                )
                row = cur.fetchone()
                conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"reinstate DB error for {receipt_id}: {e}")
            raise

        if not row:
            raise ValueError(f"Receipt {receipt_id} not found in revocation registry.")

        logger.warning(
            f"[Revocation] {receipt_id} → REINSTATED | by={reinstated_by} | reason={reason[:80]}"
        )
        return self.get_status(receipt_id)

    def get_status_list(self, limit: int = 500) -> Dict[str, Any]:
        """
        Returns a W3C StatusList2021-compatible revocation index.
        Lists all non-active VCs with their status.

        For large deployments, StatusList2021 specifies a compressed bitstring.
        OMNIX uses an enumerated list format (suitable for current receipt volume)
        with a migration path to full bitstring compression noted.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            conn = _get_db_conn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT receipt_id, status, revoked_at, reason
                    FROM vc_revocation_registry
                    WHERE status != 'active'
                    ORDER BY revoked_at DESC NULLS LAST
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
            conn.close()
        except Exception as e:
            logger.error(f"status_list DB error: {e}")
            rows = []

        revoked_entries = [
            {
                "receipt_id": r[0],
                "status":     r[1],
                "revoked_at": r[2].isoformat() if r[2] else None,
                "reason":     r[3],
            }
            for r in rows
        ]

        return {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://w3id.org/vc/status-list/2021/v1",
            ],
            "id":   f"{OMNIX_ISSUER_URL}/api/trust/status-list",
            "type": ["VerifiableCredential", "StatusList2021Credential"],
            "issuer": {
                "id":   "did:web:omnixquantum.net",
                "name": "OMNIX Quantum Ltd",
            },
            "issuedAt":           now_iso,
            "statusPurpose":      "revocation",
            "format_note":        (
                "Enumerated list format (current). Migration path to "
                "StatusList2021 compressed bitstring available when "
                "revocation volume exceeds 131,072 entries."
            ),
            "revoked_count":      len(revoked_entries),
            "revoked_credentials": revoked_entries,
            "spec":               "https://www.w3.org/TR/2023/WD-vc-status-list-20230427/",
            "adr":                "ADR-130 — VC Trust Revocation Registry",
        }


def build_credential_status(receipt_id: str) -> Dict[str, Any]:
    """
    Builds the credentialStatus block for embedding in a W3C VC.
    Called by ReceiptToVC.convert() for every issued credential.

    The verifier fetches {id} to confirm active/revoked status in real time.
    """
    return {
        "id":                    f"{OMNIX_ISSUER_URL}/api/trust/vc-status/{receipt_id}",
        "type":                  "StatusList2021Entry",
        "statusPurpose":         "revocation",
        "statusListCredential":  f"{OMNIX_ISSUER_URL}/api/trust/status-list",
        "adr":                   "ADR-130",
    }
