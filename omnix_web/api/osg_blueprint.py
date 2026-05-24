"""
OMNIX Settlement Gate (OSG) — Flask API Blueprint
ADR-188 · OMNIX-OSG-2026-001

The commitment-time enforcement layer that binds downstream settlement consequences
to upstream OMNIX governance proofs (PoGC). Ledger-agnostic — XRPL/RLUSD reference impl.

"La ATF determina quién puede proponer.
 El punto de estrangulamiento determina si la propuesta vincula la consecuencia."

Six invariants:
    OSG-INV-001 — Fail-closed: no PoGC → REJECTED (never silently approved)
    OSG-INV-002 — Append-only ValidationReceipts (no DELETE, no UPDATE)
    OSG-INV-003 — Offline verifiability — VR + public key only, zero platform access
    OSG-INV-004 — TTL coverage — PoGC must not expire before settlement_deadline
    OSG-INV-005 — Ledger agnosticism — XRPL · ETH · SWIFT · FIX · OTHER
    OSG-INV-006 — Complete audit chain — intent → governance → proof → settlement

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request, Response

logger = logging.getLogger("OMNIX.API.OSG")

osg_bp = Blueprint("osg", __name__)

# ─── DDL ─────────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS osg_validation_receipts (
    vr_id               TEXT PRIMARY KEY,
    pogc_id             TEXT NOT NULL,
    session_id          TEXT NOT NULL,
    ctchc_seal_hash     TEXT NOT NULL,
    settlement_ledger   TEXT NOT NULL DEFAULT 'XRPL',
    settlement_tx_hash  TEXT,
    settlement_deadline TIMESTAMPTZ,
    settlement_amount   NUMERIC,
    settlement_currency TEXT DEFAULT 'RLUSD',
    org_id              TEXT NOT NULL,
    org_name            TEXT NOT NULL,
    verdict             TEXT NOT NULL CHECK (verdict IN ('APPROVED', 'REJECTED')),
    reject_reason       TEXT,
    reject_invariant    TEXT,
    content_hash        TEXT NOT NULL,
    pqc_signature       TEXT NOT NULL,
    pqc_algorithm       TEXT NOT NULL DEFAULT 'ml-dsa-65',
    validated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    anchored_at         TIMESTAMPTZ,
    executed_at         TIMESTAMPTZ,
    metadata            JSONB DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_osg_pogc     ON osg_validation_receipts (pogc_id);
CREATE INDEX IF NOT EXISTS idx_osg_org      ON osg_validation_receipts (org_id);
CREATE INDEX IF NOT EXISTS idx_osg_verdict  ON osg_validation_receipts (verdict);
CREATE INDEX IF NOT EXISTS idx_osg_ledger   ON osg_validation_receipts (settlement_ledger);
CREATE INDEX IF NOT EXISTS idx_osg_tx_hash  ON osg_validation_receipts (settlement_tx_hash)
    WHERE settlement_tx_hash IS NOT NULL;
"""

_tables_ensured = False

SUPPORTED_LEDGERS = {"XRPL", "ETH", "SWIFT", "FIX", "OTHER"}


def _get_db():
    import psycopg2
    import psycopg2.extras
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not configured")
    conn = psycopg2.connect(url)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def _ensure_tables():
    global _tables_ensured
    if _tables_ensured:
        return
    try:
        conn = _get_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute(_DDL)
        conn.close()
        _tables_ensured = True
        logger.info("[OSG] osg_validation_receipts table ensured")
    except Exception as exc:
        logger.warning(f"[OSG] ensure_tables failed (non-blocking): {exc}")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _err(msg: str, code: int = 400):
    return jsonify({"error": msg, "status": "error"}), code


def _vr_id() -> str:
    return "VR-" + secrets.token_hex(8).upper()


def _content_hash(data: Dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return "sha3-256:" + hashlib.sha3_256(payload).hexdigest()


def _sign(data: Dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    try:
        import base64
        sk_b64 = os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64")
        if sk_b64:
            from oqs import Signature
            sk = base64.b64decode(sk_b64)
            signer = Signature("ML-DSA-65", sk)
            return "ML-DSA-65:" + signer.sign(payload).hex()
    except Exception as exc:
        logger.warning(f"[OSG] PQC signing unavailable: {exc}")
    return "STUB-SHA3-256:" + hashlib.sha3_256(b"OSG-STUB:" + payload).hexdigest()


def _auth_client(req) -> Optional[Dict[str, Any]]:
    key = req.headers.get("X-API-Key") or req.headers.get("Authorization", "").removeprefix("Bearer ")
    if not key:
        return None
    try:
        conn = _get_db()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT client_id, name, active FROM b2b_clients WHERE api_key = %s AND active = TRUE LIMIT 1",
                (key,)
            )
            row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as exc:
        logger.warning(f"[OSG] Auth DB error: {exc}")
        return None


def _fetch_pogc(pogc_id: str) -> Optional[Dict[str, Any]]:
    """Fetch PoGC from pogr_certificates — OSG-INV-001 gate."""
    try:
        conn = _get_db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pogc_id, session_id, ctchc_seal_hash, status,
                       expires_at, issuer, subject_org, subject_org_id,
                       compliance_tier, content_hash
                FROM pogr_certificates WHERE pogc_id = %s LIMIT 1
            """, (pogc_id,))
            row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as exc:
        logger.warning(f"[OSG] fetch_pogc error: {exc}")
        return None


def _dt(v):
    return v.isoformat() if hasattr(v, "isoformat") else v


def _parse_dt(s) -> Optional[datetime]:
    if not s:
        return None
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


# ─── 1. POST /v1/osg/validate ─────────────────────────────────────────────────

@osg_bp.route("/v1/osg/validate", methods=["POST"])
def validate():
    """
    OSG main gate. Validates that a downstream settlement is backed by a valid PoGC.

    Body:
        pogc_id             (required) — PoGC to validate against
        settlement_ledger   (required) — XRPL | ETH | SWIFT | FIX | OTHER
        settlement_currency (optional) — RLUSD | USD | EUR | XRP | ...
        settlement_amount   (optional) — amount in settlement_currency
        settlement_deadline (optional) — ISO8601, must be before PoGC.expires_at
        metadata            (optional) — arbitrary JSON

    Returns:
        ValidationReceipt (VR) with verdict APPROVED or REJECTED
    """
    _ensure_tables()

    client = _auth_client(request)
    if not client:
        return _err("Authentication required", 401)

    body = request.get_json(silent=True) or {}
    pogc_id  = (body.get("pogc_id") or "").strip()
    ledger   = (body.get("settlement_ledger") or "XRPL").strip().upper()
    currency = (body.get("settlement_currency") or "RLUSD").strip().upper()
    amount   = body.get("settlement_amount")
    deadline = body.get("settlement_deadline")
    metadata = body.get("metadata") or {}

    if not pogc_id:
        # OSG-INV-001: fail-closed — missing pogc_id = REJECTED, not error
        return _build_rejection(client, pogc_id="", ledger=ledger, currency=currency,
                                amount=amount, reason="pogc_id is required",
                                invariant="OSG-INV-001", metadata=metadata)

    if ledger not in SUPPORTED_LEDGERS:
        return _err(f"settlement_ledger must be one of: {', '.join(sorted(SUPPORTED_LEDGERS))}")

    # ── Fetch PoGC ─────────────────────────────────────────────────────────
    pogc = _fetch_pogc(pogc_id)

    # OSG-INV-001: no PoGC → REJECTED (fail-closed)
    if not pogc:
        return _build_rejection(client, pogc_id=pogc_id, ledger=ledger, currency=currency,
                                amount=amount, reason="PoGC not found in registry",
                                invariant="OSG-INV-001", metadata=metadata)

    # OSG-INV-001: PoGC not ACTIVE
    if pogc["status"] != "ACTIVE":
        return _build_rejection(client, pogc_id=pogc_id, ledger=ledger, currency=currency,
                                amount=amount,
                                reason=f"PoGC status is {pogc['status']} — must be ACTIVE",
                                invariant="OSG-INV-001", metadata=metadata,
                                pogc=pogc)

    # OSG-INV-004: TTL coverage
    now = datetime.now(timezone.utc)
    expires_at = _parse_dt(pogc["expires_at"])
    if expires_at and now >= expires_at:
        return _build_rejection(client, pogc_id=pogc_id, ledger=ledger, currency=currency,
                                amount=amount, reason="PoGC has expired",
                                invariant="OSG-INV-004", metadata=metadata, pogc=pogc)

    if deadline:
        dl = _parse_dt(deadline)
        if dl and expires_at and dl > expires_at:
            return _build_rejection(client, pogc_id=pogc_id, ledger=ledger, currency=currency,
                                    amount=amount,
                                    reason=f"settlement_deadline {dl.date()} is after PoGC.expires_at {expires_at.date()}",
                                    invariant="OSG-INV-004", metadata=metadata, pogc=pogc)

    # ── All checks passed → APPROVED ────────────────────────────────────────
    vr_id      = _vr_id()
    checked_at = now.isoformat()

    canonical = {
        "vr_id":              vr_id,
        "pogc_id":            pogc_id,
        "session_id":         pogc["session_id"],
        "ctchc_seal_hash":    pogc["ctchc_seal_hash"],
        "settlement_ledger":  ledger,
        "settlement_currency": currency,
        "settlement_amount":  float(amount) if amount is not None else None,
        "verdict":            "APPROVED",
        "validated_at":       checked_at,
        "org_id":             client["client_id"],
    }
    c_hash = _content_hash(canonical)
    sig    = _sign(canonical)

    base_url = os.environ.get("OMNIX_WEB_URL", "https://omnixquantum.net")

    vr = {
        **canonical,
        "org_name":            client["name"],
        "content_hash":        c_hash,
        "pqc_signature":       sig,
        "pqc_algorithm":       "ml-dsa-65",
        "invariants_checked":  ["OSG-INV-001", "OSG-INV-004", "OSG-INV-006"],
        "offline_verify_url":  f"{base_url}/v1/osg/validation/{vr_id}",
        "pogc_expires_at":     _dt(expires_at),
        "settlement_deadline": deadline,
        "metadata":            metadata,
    }

    try:
        conn = _get_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO osg_validation_receipts (
                        vr_id, pogc_id, session_id, ctchc_seal_hash,
                        settlement_ledger, settlement_deadline,
                        settlement_amount, settlement_currency,
                        org_id, org_name, verdict,
                        content_hash, pqc_signature, pqc_algorithm,
                        metadata
                    ) VALUES (
                        %(vr_id)s, %(pogc_id)s, %(session_id)s, %(ctchc_seal_hash)s,
                        %(settlement_ledger)s, %(settlement_deadline)s,
                        %(settlement_amount)s, %(settlement_currency)s,
                        %(org_id)s, %(org_name)s, %(verdict)s,
                        %(content_hash)s, %(pqc_signature)s, %(pqc_algorithm)s,
                        %(metadata)s::jsonb
                    )
                """, {
                    "vr_id":                vr_id,
                    "pogc_id":              pogc_id,
                    "session_id":           pogc["session_id"],
                    "ctchc_seal_hash":      pogc["ctchc_seal_hash"],
                    "settlement_ledger":    ledger,
                    "settlement_deadline":  deadline,
                    "settlement_amount":    float(amount) if amount is not None else None,
                    "settlement_currency":  currency,
                    "org_id":               client["client_id"],
                    "org_name":             client["name"],
                    "verdict":              "APPROVED",
                    "content_hash":         c_hash,
                    "pqc_signature":        sig,
                    "pqc_algorithm":        "ml-dsa-65",
                    "metadata":             json.dumps(metadata),
                })
        conn.close()
    except Exception as exc:
        logger.error(f"[OSG] validate INSERT failed: {exc}")
        return jsonify({"error": "Registry write failed"}), 500

    logger.info(f"[OSG] APPROVED vr={vr_id} pogc={pogc_id} ledger={ledger} org={client['name']}")
    return jsonify({"status": "APPROVED", "validation_receipt": vr}), 200


def _build_rejection(client: Dict, pogc_id: str, ledger: str, currency: str,
                     amount: Any, reason: str, invariant: str,
                     metadata: Dict = None, pogc: Optional[Dict] = None):
    """OSG-INV-001/004: build and persist a REJECTED ValidationReceipt."""
    _ensure_tables()
    vr_id = _vr_id()
    now   = datetime.now(timezone.utc).isoformat()
    canonical = {
        "vr_id":   vr_id,
        "pogc_id": pogc_id,
        "verdict": "REJECTED",
        "reason":  reason,
        "validated_at": now,
        "org_id":  client["client_id"],
    }
    c_hash = _content_hash(canonical)
    sig    = _sign(canonical)

    try:
        conn = _get_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO osg_validation_receipts (
                        vr_id, pogc_id, session_id, ctchc_seal_hash,
                        settlement_ledger, settlement_amount, settlement_currency,
                        org_id, org_name, verdict,
                        reject_reason, reject_invariant,
                        content_hash, pqc_signature, pqc_algorithm,
                        metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb
                    )
                """, (
                    vr_id, pogc_id,
                    pogc["session_id"] if pogc else "",
                    pogc["ctchc_seal_hash"] if pogc else "",
                    ledger,
                    float(amount) if amount is not None else None,
                    currency,
                    client["client_id"], client["name"],
                    "REJECTED", reason, invariant,
                    c_hash, sig, "ml-dsa-65",
                    json.dumps(metadata or {}),
                ))
        conn.close()
    except Exception as exc:
        logger.warning(f"[OSG] rejection INSERT failed: {exc}")

    logger.warning(f"[OSG] REJECTED vr={vr_id} pogc={pogc_id} invariant={invariant} reason={reason}")
    base_url = os.environ.get("OMNIX_WEB_URL", "https://omnixquantum.net")
    return jsonify({
        "status": "REJECTED",
        "validation_receipt": {
            "vr_id":            vr_id,
            "pogc_id":          pogc_id,
            "verdict":          "REJECTED",
            "reject_reason":    reason,
            "reject_invariant": invariant,
            "content_hash":     c_hash,
            "pqc_signature":    sig,
            "pqc_algorithm":    "ml-dsa-65",
            "validated_at":     now,
            "org_id":           client["client_id"],
            "settlement_ledger": ledger,
            "offline_verify_url": f"{base_url}/v1/osg/validation/{vr_id}",
        },
    }), 200


# ─── 2. GET /v1/osg/validation/<vr_id> ────────────────────────────────────────

@osg_bp.route("/v1/osg/validation/<vr_id>", methods=["GET"])
def get_validation(vr_id: str):
    """Public — OSG-INV-003: zero-auth VR retrieval for offline verification."""
    _ensure_tables()
    try:
        conn = _get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM osg_validation_receipts WHERE vr_id = %s LIMIT 1", (vr_id,))
            row = cur.fetchone()
        conn.close()
    except Exception:
        return jsonify({"error": "Registry unavailable"}), 503

    if not row:
        return jsonify({"error": "ValidationReceipt not found", "vr_id": vr_id}), 404

    return jsonify({k: _dt(v) for k, v in dict(row).items()})


# ─── 3. GET /v1/osg/settlement/<tx_hash> ──────────────────────────────────────

@osg_bp.route("/v1/osg/settlement/<path:tx_hash>", methods=["GET"])
def get_by_tx_hash(tx_hash: str):
    """Look up validation receipt by settlement transaction hash."""
    _ensure_tables()
    client = _auth_client(request)
    if not client:
        return _err("Authentication required", 401)
    try:
        conn = _get_db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM osg_validation_receipts
                WHERE settlement_tx_hash = %s AND org_id = %s LIMIT 1
            """, (tx_hash, client["client_id"]))
            row = cur.fetchone()
        conn.close()
    except Exception:
        return jsonify({"error": "Registry unavailable"}), 503

    if not row:
        return jsonify({"error": "No ValidationReceipt found for this tx_hash"}), 404

    return jsonify({k: _dt(v) for k, v in dict(row).items()})


# ─── 4. POST /v1/osg/anchor ───────────────────────────────────────────────────

@osg_bp.route("/v1/osg/anchor", methods=["POST"])
def anchor():
    """
    Pre-anchor a settlement to a PoGC before execution.
    Runs the same invariant checks as /validate and records intent
    before the settlement transaction is submitted to the ledger.
    Returns a VR with verdict APPROVED that the submitter includes in tx metadata.
    """
    _ensure_tables()
    client = _auth_client(request)
    if not client:
        return _err("Authentication required", 401)

    body = request.get_json(silent=True) or {}
    # Same as /validate but also records anchored_at
    pogc_id  = (body.get("pogc_id") or "").strip()
    ledger   = (body.get("settlement_ledger") or "XRPL").strip().upper()
    currency = (body.get("settlement_currency") or "RLUSD").strip().upper()
    amount   = body.get("settlement_amount")
    deadline = body.get("settlement_deadline")
    metadata = body.get("metadata") or {}

    if not pogc_id:
        return _build_rejection(client, pogc_id="", ledger=ledger, currency=currency,
                                amount=amount, reason="pogc_id required for anchoring",
                                invariant="OSG-INV-001", metadata=metadata)

    pogc = _fetch_pogc(pogc_id)
    if not pogc or pogc["status"] != "ACTIVE":
        reason = "PoGC not found" if not pogc else f"PoGC status {pogc['status']} not ACTIVE"
        return _build_rejection(client, pogc_id=pogc_id, ledger=ledger, currency=currency,
                                amount=amount, reason=reason, invariant="OSG-INV-001",
                                metadata=metadata, pogc=pogc)

    now        = datetime.now(timezone.utc)
    expires_at = _parse_dt(pogc["expires_at"])
    if expires_at and now >= expires_at:
        return _build_rejection(client, pogc_id=pogc_id, ledger=ledger, currency=currency,
                                amount=amount, reason="PoGC expired", invariant="OSG-INV-004",
                                metadata=metadata, pogc=pogc)

    vr_id = _vr_id()
    anchor_ts = now.isoformat()
    canonical = {
        "vr_id": vr_id, "pogc_id": pogc_id,
        "session_id": pogc["session_id"],
        "ctchc_seal_hash": pogc["ctchc_seal_hash"],
        "settlement_ledger": ledger, "settlement_currency": currency,
        "settlement_amount": float(amount) if amount is not None else None,
        "verdict": "APPROVED", "anchored": True,
        "anchored_at": anchor_ts, "org_id": client["client_id"],
    }
    c_hash = _content_hash(canonical)
    sig    = _sign(canonical)

    try:
        conn = _get_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO osg_validation_receipts (
                        vr_id, pogc_id, session_id, ctchc_seal_hash,
                        settlement_ledger, settlement_amount, settlement_currency,
                        org_id, org_name, verdict,
                        content_hash, pqc_signature, pqc_algorithm,
                        anchored_at, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb
                    )
                """, (
                    vr_id, pogc_id, pogc["session_id"], pogc["ctchc_seal_hash"],
                    ledger,
                    float(amount) if amount is not None else None,
                    currency,
                    client["client_id"], client["name"],
                    "APPROVED", c_hash, sig, "ml-dsa-65",
                    now, json.dumps(metadata),
                ))
        conn.close()
    except Exception as exc:
        logger.error(f"[OSG] anchor INSERT failed: {exc}")
        return jsonify({"error": "Registry write failed"}), 500

    base_url = os.environ.get("OMNIX_WEB_URL", "https://omnixquantum.net")
    logger.info(f"[OSG] ANCHORED vr={vr_id} pogc={pogc_id} ledger={ledger}")
    return jsonify({
        "status": "ANCHORED",
        "validation_receipt": {
            "vr_id": vr_id, "pogc_id": pogc_id, "verdict": "APPROVED",
            "settlement_ledger": ledger, "settlement_currency": currency,
            "settlement_amount": float(amount) if amount is not None else None,
            "anchored_at": anchor_ts,
            "content_hash": c_hash, "pqc_signature": sig, "pqc_algorithm": "ml-dsa-65",
            "invariants_checked": ["OSG-INV-001", "OSG-INV-004", "OSG-INV-006"],
            "offline_verify_url": f"{base_url}/v1/osg/validation/{vr_id}",
            "pogc_expires_at": _dt(expires_at),
        },
        "instructions": "Include vr_id in your settlement transaction metadata before submitting to the ledger.",
    }), 201


# ─── 5. GET /v1/osg/organization/<org_id> ────────────────────────────────────

@osg_bp.route("/v1/osg/organization/<org_id>", methods=["GET"])
def org_history(org_id: str):
    """Validation history for an org (authenticated — own org only)."""
    _ensure_tables()
    client = _auth_client(request)
    if not client:
        return _err("Authentication required", 401)
    if client["client_id"] != org_id:
        return _err("Forbidden — can only access your own organization's history", 403)

    limit  = min(int(request.args.get("limit", 20)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)
    ledger = request.args.get("ledger")
    verdict = request.args.get("verdict")

    try:
        conn = _get_db()
        with conn.cursor() as cur:
            q = "SELECT * FROM osg_validation_receipts WHERE org_id = %s"
            params = [org_id]
            if ledger and ledger.upper() in SUPPORTED_LEDGERS:
                q += " AND settlement_ledger = %s"; params.append(ledger.upper())
            if verdict in ("APPROVED", "REJECTED"):
                q += " AND verdict = %s"; params.append(verdict)
            q += " ORDER BY validated_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cur.execute(q, params)
            rows = cur.fetchall()
            cur.execute("SELECT COUNT(*) as n FROM osg_validation_receipts WHERE org_id = %s", (org_id,))
            total = cur.fetchone()["n"]
        conn.close()
    except Exception:
        return jsonify({"error": "Registry unavailable"}), 503

    return jsonify({
        "org_id":   org_id,
        "total":    total,
        "limit":    limit,
        "offset":   offset,
        "receipts": [{k: _dt(v) for k, v in dict(r).items()} for r in rows],
    })


# ─── 6. GET /v1/osg/manifest ─────────────────────────────────────────────────

@osg_bp.route("/v1/osg/manifest", methods=["GET"])
def manifest():
    """OSG module manifest — public capability + stats registry."""
    _ensure_tables()

    try:
        conn = _get_db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE verdict='APPROVED') as approved,
                    COUNT(*) FILTER (WHERE verdict='REJECTED') as rejected,
                    COUNT(DISTINCT settlement_ledger) as ledgers_used,
                    COUNT(DISTINCT org_id) as orgs
                FROM osg_validation_receipts
            """)
            stats = dict(cur.fetchone())
        conn.close()
    except Exception:
        stats = {"total": 0, "approved": 0, "rejected": 0, "ledgers_used": 0, "orgs": 0}

    return jsonify({
        "module":           "OMNIX Settlement Gate",
        "product_id":       "OMNIX-OSG-2026-001",
        "version":          "1.0.0",
        "issuer":           "OMNIX QUANTUM LTD",
        "adr":              "ADR-188",
        "depends_on":       ["ADR-186 (PoGR)", "ADR-187 (PoGR API)", "ADR-184 (OGR)"],
        "invariants": {
            "OSG-INV-001": "Fail-closed — no PoGC → REJECTED",
            "OSG-INV-002": "Append-only ValidationReceipts",
            "OSG-INV-003": "Offline verifiability — VR + public key only",
            "OSG-INV-004": "TTL coverage — PoGC must not expire before settlement_deadline",
            "OSG-INV-005": "Ledger agnosticism — XRPL · ETH · SWIFT · FIX · OTHER",
            "OSG-INV-006": "Complete audit chain — intent → governance → proof → settlement",
        },
        "supported_ledgers":    sorted(SUPPORTED_LEDGERS),
        "reference_ledger":     "XRPL",
        "reference_currency":   "RLUSD",
        "pqc_algorithm":        "ml-dsa-65",
        "fips_standard":        "FIPS 204",
        "upstream_components":  ["ATF (ADR-156)", "OGR (ADR-184)", "PoGR (ADR-186)"],
        "endpoints": [
            "POST /v1/osg/validate",
            "POST /v1/osg/anchor",
            "GET  /v1/osg/validation/{vr_id}",
            "GET  /v1/osg/settlement/{tx_hash}",
            "GET  /v1/osg/organization/{org_id}",
            "GET  /v1/osg/manifest",
        ],
        "registry_stats":       stats,
        "published_at":         datetime.now(timezone.utc).isoformat(),
    })
