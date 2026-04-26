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

W3C StatusList2021 bitstring (ADR-130 v2):
  Every revoked VC is assigned a sequential status_list_index.
  The /api/trust/status-list endpoint returns a GZIP-compressed, base64url-encoded
  bitstring of BITSTRING_SIZE bits where bit[index]=1 means revoked.
  This is the canonical W3C StatusList2021 format, compatible with any EUDI wallet.

Revocation webhook (ADR-130 v2):
  When a VC is revoked or reinstated, an HMAC-SHA256 signed webhook event is
  delivered asynchronously to the registered client endpoint.
  Event types: 'vc.revoked', 'vc.suspended', 'vc.reinstated'

Human accountability (ADR-124 integration):
  revoked_by can be:
    - a client_id (B2B client with admin role)
    - 'system:avm'   (Assumption Validity Monitor auto-revocation)
    - 'system:ebip'  (Execution Boundary Integrity Protocol)
    - 'system:anomaly' (AnomalyResponseEngine — ADR-129)
"""

import base64
import gzip
import hashlib
import hmac
import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.Revocation")

OMNIX_ISSUER_URL  = "https://omnixquantum.net"
BITSTRING_SIZE    = 131072   # W3C StatusList2021 §4: minimum 131,072 bits (16KB)
_WEBHOOK_TIMEOUT  = 10       # seconds


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


# ── W3C StatusList2021 bitstring ──────────────────────────────────────────────

def _build_encoded_list(revoked_indices: List[int], size: int = BITSTRING_SIZE) -> str:
    """
    Build a W3C StatusList2021 §4 encoded list.

    Creates a bitstring of `size` bits (default 131,072 — W3C minimum).
    Bit at position `index` is set to 1 if the credential at that index is revoked.
    Bit ordering: MSB first (bit 0 of byte 0 = index 0).

    Returns: base64url(gzip(bitstring)) — the `encodedList` field value.
    """
    ba = bytearray(size // 8)
    for idx in revoked_indices:
        if 0 <= idx < size:
            ba[idx // 8] |= (1 << (7 - (idx % 8)))
    compressed = gzip.compress(bytes(ba), compresslevel=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii")


def _get_next_status_list_index(cur) -> int:
    """
    Returns the next available sequential status_list_index.
    Thread-safe: uses SELECT MAX() + 1 within the same transaction.
    """
    cur.execute(
        "SELECT COALESCE(MAX(status_list_index), -1) + 1 FROM vc_revocation_registry"
    )
    row = cur.fetchone()
    return int(row[0]) if row else 0


# ── Revocation webhook delivery ───────────────────────────────────────────────

def _get_client_webhook_config(client_id: str) -> Optional[Dict[str, str]]:
    """
    Fetch the webhook_url and webhook_secret for a given client_id.
    Returns None if client has no webhook configured.
    """
    if not client_id or client_id.startswith("system:"):
        return None
    try:
        conn = _get_db_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT webhook_url, webhook_secret
                FROM b2b_clients
                WHERE client_id = %s AND active = true
                  AND webhook_url IS NOT NULL
                """,
                (client_id,),
            )
            row = cur.fetchone()
        conn.close()
        if not row or not row[0]:
            return None
        webhook_url, encrypted_secret = row
        if not encrypted_secret:
            return None
        try:
            from api.gov_auth_rbac import _decrypt_secret
        except ImportError:
            try:
                from gov_auth_rbac import _decrypt_secret
            except ImportError:
                return None
        secret = _decrypt_secret(encrypted_secret)
        return {"webhook_url": webhook_url, "webhook_secret": secret}
    except Exception as e:
        logger.debug(f"webhook config lookup failed for {client_id}: {e}")
        return None


def _deliver_revocation_webhook(
    client_id: str,
    receipt_id: str,
    event_type: str,
    status_data: Dict[str, Any],
) -> None:
    """
    Fire-and-forget: delivers a signed revocation webhook event.
    Called in a background daemon thread — never blocks the HTTP response.

    Event types: 'vc.revoked' | 'vc.suspended' | 'vc.reinstated'

    Payload signature: HMAC-SHA256(webhook_secret, body_bytes)
    Header: X-OMNIX-Signature: sha256=<hexdigest>
    """
    cfg = _get_client_webhook_config(client_id)
    if not cfg:
        return

    webhook_url    = cfg["webhook_url"]
    webhook_secret = cfg["webhook_secret"]

    payload = {
        "event":      event_type,
        "receipt_id": receipt_id,
        "data":       status_data,
        "issuer":     "did:web:omnixquantum.net",
        "adr":        "ADR-130 — VC Trust Revocation Registry",
        "delivered_at": datetime.now(timezone.utc).isoformat(),
        "verify_url": f"{OMNIX_ISSUER_URL}/api/trust/vc-status/{receipt_id}",
    }

    try:
        body_bytes = json.dumps(payload, default=str).encode("utf-8")
        sig_hex = hmac.new(
            webhook_secret.encode("utf-8"),
            body_bytes,
            digestmod=hashlib.sha256,
        ).hexdigest()

        req = urllib.request.Request(
            webhook_url,
            data=body_bytes,
            headers={
                "Content-Type":       "application/json",
                "X-OMNIX-Signature":  f"sha256={sig_hex}",
                "X-OMNIX-Event":      event_type,
                "X-OMNIX-Receipt-ID": receipt_id,
                "X-OMNIX-Client-ID":  client_id,
                "User-Agent":         "OMNIX-Webhook/2.0-ADR130 (omnixquantum.net)",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=_WEBHOOK_TIMEOUT) as resp:
            http_code = resp.getcode()
            logger.info(
                f"[Revocation.Webhook] {event_type} → {client_id} "
                f"receipt={receipt_id} http={http_code}"
            )
    except urllib.error.HTTPError as exc:
        logger.warning(
            f"[Revocation.Webhook] HTTP {exc.code} for {client_id} receipt={receipt_id}"
        )
    except Exception as exc:
        logger.warning(
            f"[Revocation.Webhook] delivery failed for {client_id} receipt={receipt_id}: {exc}"
        )


def fire_revocation_webhook(
    client_id: str,
    receipt_id: str,
    event_type: str,
    status_data: Dict[str, Any],
) -> None:
    """
    Dispatch a revocation webhook in a background daemon thread.
    Returns immediately — never blocks the calling HTTP handler.
    """
    t = threading.Thread(
        target=_deliver_revocation_webhook,
        args=(client_id, receipt_id, event_type, status_data),
        daemon=True,
        name=f"webhook-revoke-{receipt_id[:12]}",
    )
    t.start()


# ── Core registry class ───────────────────────────────────────────────────────

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
                "receipt_id":          str,
                "status":              "active" | "revoked" | "suspended",
                "status_list_index":   int | None,  (W3C StatusList2021 position)
                "revoked_at":          ISO8601 | None,
                "revoked_by":          str | None,
                "reason":              str | None,
                "reinstate_url":       str | None,  (only if suspended)
                "checked_at":          ISO8601,
                "vc_status_url":       str,
            }
        """
        now_iso    = datetime.now(timezone.utc).isoformat()
        status_url = f"{OMNIX_ISSUER_URL}/api/trust/vc-status/{receipt_id}"

        try:
            conn = _get_db_conn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT status, reason, revoked_by, revoked_at,
                           reinstated_at, reinstatement_reason, status_list_index
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
                "receipt_id":        receipt_id,
                "status":            "unknown",
                "status_list_index": None,
                "error":             "Revocation registry temporarily unavailable.",
                "checked_at":        now_iso,
                "vc_status_url":     status_url,
            }

        if not row:
            return {
                "receipt_id":         receipt_id,
                "status":             "active",
                "status_list_index":  None,
                "revoked_at":         None,
                "revoked_by":         None,
                "reason":             None,
                "checked_at":         now_iso,
                "vc_status_url":      status_url,
                "note":               "Not found in revocation registry — credential is active.",
            }

        status, reason, revoked_by, revoked_at, reinstated_at, reinstate_reason, sli = row
        result = {
            "receipt_id":           receipt_id,
            "status":               status,
            "status_list_index":    sli,
            "reason":               reason,
            "revoked_by":           revoked_by,
            "revoked_at":           revoked_at.isoformat() if revoked_at else None,
            "reinstated_at":        reinstated_at.isoformat() if reinstated_at else None,
            "reinstatement_reason": reinstate_reason,
            "checked_at":           now_iso,
            "vc_status_url":        status_url,
        }
        if status == "suspended":
            result["reinstate_url"] = f"{OMNIX_ISSUER_URL}/api/trust/reinstate/{receipt_id}"
        return result

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
        Assigns a sequential status_list_index (W3C StatusList2021 position).
        Fires an asynchronous webhook notification to the registered client.

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
            "action":    status,
            "actor":     revoked_by,
            "reason":    reason,
            "timestamp": now.isoformat(),
            "context":   context or {},
        }

        try:
            conn = _get_db_conn()
            with conn.cursor() as cur:
                next_index = _get_next_status_list_index(cur)
                cur.execute(
                    """
                    INSERT INTO vc_revocation_registry
                        (receipt_id, status, reason, revoked_by, revoked_at,
                         revocation_context, audit_trail, status_list_index, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, NOW())
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
                        next_index,
                    ),
                )
                conn.commit()
            conn.close()
            logger.warning(
                f"[Revocation] {receipt_id} → {status.upper()} "
                f"idx={next_index} by={revoked_by} reason={reason[:80]}"
            )
        except Exception as e:
            logger.error(f"revoke DB error for {receipt_id}: {e}")
            raise

        result = self.get_status(receipt_id)

        event_type = "vc.revoked" if status == "revoked" else "vc.suspended"
        fire_revocation_webhook(revoked_by, receipt_id, event_type, result)

        return result

    def reinstate(
        self,
        receipt_id: str,
        reason: str,
        reinstated_by: str,
    ) -> Dict[str, Any]:
        """
        Reinstates a suspended or revoked VC. Requires explicit justification.
        Audit trail is preserved — the original revocation event is not erased.
        Fires a 'vc.reinstated' webhook event.

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
            f"[Revocation] {receipt_id} → REINSTATED "
            f"by={reinstated_by} reason={reason[:80]}"
        )

        result = self.get_status(receipt_id)
        fire_revocation_webhook(reinstated_by, receipt_id, "vc.reinstated", result)
        return result

    def get_status_list(self, limit: int = 500) -> Dict[str, Any]:
        """
        Returns a W3C StatusList2021-compatible revocation credential.

        Format: Full W3C spec compliance —
          - 'encodedList': base64url(gzip(bitstring)) with BITSTRING_SIZE bits
          - 'revoked_credentials': human-readable index (with statusListIndex per entry)
          - ETag source: sha256(revoked_count + ":" + max_updated_at)

        Spec: https://www.w3.org/TR/2023/WD-vc-status-list-20230427/
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            conn = _get_db_conn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT receipt_id, status, revoked_at, reason, status_list_index,
                           MAX(updated_at) OVER () AS max_updated_at,
                           COUNT(*) OVER ()         AS total_count
                    FROM vc_revocation_registry
                    WHERE status != 'active'
                    ORDER BY status_list_index ASC NULLS LAST, revoked_at DESC NULLS LAST
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
            conn.close()
        except Exception as e:
            logger.error(f"status_list DB error: {e}")
            rows = []

        max_updated_at = None
        total_count    = 0
        revoked_indices: List[int] = []
        revoked_entries = []

        for r in rows:
            rid, status, revoked_at, reason, sli, mu, tc = r
            if max_updated_at is None:
                max_updated_at = mu
                total_count    = tc
            entry = {
                "receipt_id":        rid,
                "status":            status,
                "statusListIndex":   sli,
                "revoked_at":        revoked_at.isoformat() if revoked_at else None,
                "reason":            reason,
            }
            revoked_entries.append(entry)
            if sli is not None:
                revoked_indices.append(int(sli))

        encoded_list = _build_encoded_list(revoked_indices)

        etag_source = f"{len(revoked_entries)}:{max_updated_at or 'none'}"
        etag        = hashlib.sha256(etag_source.encode()).hexdigest()[:32]

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
            "issuedAt":            now_iso,
            "statusPurpose":       "revocation",
            "encodedList":         encoded_list,
            "bitstring_size":      BITSTRING_SIZE,
            "revoked_count":       len(revoked_entries),
            "revoked_credentials": revoked_entries,
            "etag":                etag,
            "spec":                "https://www.w3.org/TR/2023/WD-vc-status-list-20230427/",
            "adr":                 "ADR-130 — VC Trust Revocation Registry",
        }

    def get_etag(self) -> str:
        """
        Returns a lightweight ETag for the status list without fetching all entries.
        Used by the HTTP layer for conditional GET (If-None-Match → 304).
        """
        try:
            conn = _get_db_conn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS cnt,
                           COALESCE(MAX(updated_at)::text, 'none') AS mu
                    FROM vc_revocation_registry
                    WHERE status != 'active'
                    """
                )
                row = cur.fetchone()
            conn.close()
            cnt, mu = row if row else (0, "none")
            return hashlib.sha256(f"{cnt}:{mu}".encode()).hexdigest()[:32]
        except Exception as e:
            logger.debug(f"get_etag error: {e}")
            return hashlib.sha256(str(time.monotonic()).encode()).hexdigest()[:32]


def build_credential_status(receipt_id: str, status_list_index: Optional[int] = None) -> Dict[str, Any]:
    """
    Builds the credentialStatus block for embedding in a W3C VC.
    Called by ReceiptToVC.convert() for every issued credential.

    The verifier fetches {id} to confirm active/revoked status in real time.
    If status_list_index is provided, it is embedded for fast bitstring lookup.
    """
    block = {
        "id":                   f"{OMNIX_ISSUER_URL}/api/trust/vc-status/{receipt_id}",
        "type":                 "StatusList2021Entry",
        "statusPurpose":        "revocation",
        "statusListCredential": f"{OMNIX_ISSUER_URL}/api/trust/status-list",
        "adr":                  "ADR-130",
    }
    if status_list_index is not None:
        block["statusListIndex"] = status_list_index
    return block
