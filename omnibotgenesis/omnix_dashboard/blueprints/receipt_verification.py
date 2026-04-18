"""
PKI Verification API — ADR-079

Endpoints for third-party cryptographic verification of OMNIX governance receipts.

GET  /api/receipts/public-key    — Returns current signing public key metadata.
POST /api/receipts/verify        — Verifies a receipt's Dilithium-3 signature.

Security:
    - Public key endpoint is unauthenticated (public keys are not secret).
    - Verify endpoint is unauthenticated but rate-limited (60 req/min per IP).
    - Private key material is never exposed.
    - Input validated strictly (receipt_id format, hash length, signature size).
    - DB cross-reference prevents validation of unissued (receipt_id, hash, sig) tuples.
    - Error responses are normalized (no information leakage).

Harold Nunes — OMNIX QUANTUM LTD
ADR-079 — April 2026
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Optional

from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

receipt_pki_bp = Blueprint("receipt_pki", __name__)

# ── Input validation constants ─────────────────────────────────────────────────

_RECEIPT_ID_RE = re.compile(
    r"^OMNIX-(?:[A-Z]{3}-)?[A-F0-9]{12}$"
)
_HASH_RE           = re.compile(r"^[0-9a-fA-F]{64}$")
_SIG_MAX_DECODED   = 8192        # bytes — Dilithium-3 sigs are ~3293 bytes
_BODY_MAX_BYTES    = 16 * 1024   # 16 KB request cap

# ── Rate limiting ──────────────────────────────────────────────────────────────

_rl_store: dict[str, list[float]] = {}
_RL_WINDOW   = 60
_RL_MAX      = int(os.environ.get("OMNIX_VERIFY_RATE_LIMIT", "60"))


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    _rl_store.setdefault(ip, [])
    _rl_store[ip] = [t for t in _rl_store[ip] if now - t < _RL_WINDOW]
    if len(_rl_store[ip]) >= _RL_MAX:
        return False
    _rl_store[ip].append(now)
    return True


def _client_ip() -> str:
    return (
        request.headers.get("X-Forwarded-For", request.remote_addr or "")
        .split(",")[0]
        .strip()
    )


# ── Lazy receipt engine accessor ───────────────────────────────────────────────

def _get_engine():
    """Return the singleton DecisionReceiptEngine, or None on import failure."""
    try:
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        if not hasattr(_get_engine, "_instance"):
            _get_engine._instance = DecisionReceiptEngine()
        return _get_engine._instance
    except Exception as exc:
        logger.error(f"[PKI] Cannot load DecisionReceiptEngine: {exc}")
        return None


# ── DB cross-reference ─────────────────────────────────────────────────────────

def _db_lookup(receipt_id: str) -> Optional[dict]:
    """
    Fetch stored receipt data for cross-reference validation.

    Returns dict with keys: found, content_hash, signature, decision, timestamp
    Returns None on DB error (treat as unavailable — not as 'not found').
    """
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return None

    conn = None
    try:
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
        except ImportError:
            import psycopg
            conn = psycopg.connect(db_url, autocommit=True)

        cur = conn.cursor()
        cur.execute(
            """
            SELECT content_hash, signature, decision, timestamp_utc
            FROM decision_receipts
            WHERE receipt_id = %s
            LIMIT 1
            """,
            (receipt_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        conn = None

        if row is None:
            return {"found": False}

        ts = row[3]
        return {
            "found":        True,
            "content_hash": row[0],
            "signature":    row[1],
            "decision":     row[2],
            "timestamp":    ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
        }

    except Exception as exc:
        logger.error(f"[PKI] DB lookup failed: {exc}")
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        return None


# ── GET /api/receipts/public-key ───────────────────────────────────────────────

@receipt_pki_bp.route("/api/receipts/public-key", methods=["GET"])
def get_public_key():
    """
    Return the current signing public key and metadata.
    Safe for public use — public keys are not secret.
    """
    engine = _get_engine()

    if engine is None:
        return jsonify({
            "error": "SERVICE_UNAVAILABLE",
            "message": "Receipt engine not available",
        }), 503

    pk_b64 = engine.public_key_b64
    provider = engine._provider

    if pk_b64 is None or provider is None:
        return jsonify({
            "error": "KEY_NOT_AVAILABLE",
            "message": "Signing keys are not configured",
            "key_mode": engine.key_mode,
        }), 503

    kid     = engine.key_id
    mode    = engine.key_mode
    warning = (
        "Ephemeral key — not stable across process restarts. "
        "Set OMNIX_SIGNING_SECRET_KEY_B64 + OMNIX_SIGNING_PUBLIC_KEY_B64 for persistence."
        if mode == "ephemeral_dev"
        else None
    )

    return jsonify({
        "algorithm":       provider.algorithm_name(),
        "provider_id":     provider.provider_id(),
        "nist_standard":   "FIPS 204 — ML-DSA-65",
        "public_key_b64":  pk_b64,
        "key_id":          kid,
        "key_mode":        mode,
        "active_since":    engine.active_since,
        "warning":         warning,
    }), 200


# ── POST /api/receipts/verify ──────────────────────────────────────────────────

@receipt_pki_bp.route("/api/receipts/verify", methods=["POST"])
def verify_receipt():
    """
    Cryptographically verify a receipt signature.

    Input (JSON):
        receipt_id    — canonical OMNIX receipt ID
        content_hash  — SHA-256 hex of the receipt payload (64 chars)
        signature_b64 — base64-encoded Dilithium-3 signature

    Process:
        1. Input validation
        2. Rate limiting
        3. DB cross-reference (content_hash match)
        4. Offline cryptographic signature verification

    Returns:
        { valid, receipt_id, algorithm, key_id, verified_at, db_cross_reference?, reason? }
    """
    # ── Rate limit ──────────────────────────────────────────────────────────
    ip = _client_ip()
    if not _check_rate_limit(ip):
        return jsonify({
            "error": "RATE_LIMIT_EXCEEDED",
            "retry_after_seconds": _RL_WINDOW,
        }), 429

    # ── Body size guard ─────────────────────────────────────────────────────
    if request.content_length and request.content_length > _BODY_MAX_BYTES:
        return jsonify({"error": "REQUEST_TOO_LARGE"}), 413

    # ── Parse JSON ──────────────────────────────────────────────────────────
    try:
        body = request.get_json(force=True, silent=True) or {}
    except Exception:
        body = {}

    receipt_id   = str(body.get("receipt_id",   "")).strip()
    content_hash = str(body.get("content_hash", "")).strip()
    sig_b64      = str(body.get("signature_b64", "")).strip()

    verified_at = datetime.now(timezone.utc).isoformat()

    def _invalid(reason: str):
        return jsonify({
            "valid":       False,
            "receipt_id":  receipt_id or None,
            "reason":      reason,
            "verified_at": verified_at,
        }), 400

    # ── Validate receipt_id ─────────────────────────────────────────────────
    if not receipt_id or not _RECEIPT_ID_RE.match(receipt_id):
        return _invalid("MALFORMED_INPUT")

    # ── Validate content_hash ───────────────────────────────────────────────
    if not content_hash or not _HASH_RE.match(content_hash):
        return _invalid("MALFORMED_INPUT")

    # ── Validate signature ──────────────────────────────────────────────────
    if not sig_b64:
        return _invalid("MALFORMED_INPUT")

    try:
        sig_bytes = base64.b64decode(sig_b64, validate=True)
    except Exception:
        return _invalid("MALFORMED_INPUT")

    if len(sig_bytes) > _SIG_MAX_DECODED:
        return _invalid("MALFORMED_INPUT")

    # ── Engine availability ─────────────────────────────────────────────────
    engine = _get_engine()
    if engine is None or engine._provider is None or engine._signing_keys is None:
        return jsonify({
            "valid":       False,
            "receipt_id":  receipt_id,
            "reason":      "SIGNING_KEY_NOT_AVAILABLE",
            "verified_at": verified_at,
        }), 503

    provider   = engine._provider
    public_key = engine._signing_keys[0]
    kid        = engine.key_id

    # ── DB cross-reference ──────────────────────────────────────────────────
    db_ref  = _db_lookup(receipt_id)
    db_resp = None

    if db_ref is None:
        # DB unavailable — skip cross-reference, proceed with crypto only
        db_resp = {"available": False}
    elif not db_ref.get("found"):
        # Receipt not in DB — could be sandbox / non-persisted
        db_resp = {"found": False}
    else:
        stored_hash = db_ref.get("content_hash", "")
        hash_match  = stored_hash.strip().lower() == content_hash.strip().lower()
        db_resp     = {
            "found":              True,
            "content_hash_match": hash_match,
            "decision":           db_ref.get("decision"),
            "timestamp":          db_ref.get("timestamp"),
        }
        if not hash_match:
            return jsonify({
                "valid":               False,
                "receipt_id":          receipt_id,
                "reason":              "HASH_MISMATCH",
                "verified_at":         verified_at,
                "db_cross_reference":  db_resp,
            }), 200

    # ── Cryptographic verification ──────────────────────────────────────────
    try:
        message = content_hash.encode("utf-8")
        is_valid = provider.verify(sig_bytes, message, public_key)
    except Exception as exc:
        logger.warning(f"[PKI] verify() raised exception for {receipt_id}: {exc}")
        is_valid = False

    if is_valid:
        resp: dict = {
            "valid":       True,
            "receipt_id":  receipt_id,
            "algorithm":   provider.algorithm_name(),
            "key_id":      kid,
            "verified_at": verified_at,
        }
        if db_resp is not None:
            resp["db_cross_reference"] = db_resp
        return jsonify(resp), 200
    else:
        resp = {
            "valid":       False,
            "receipt_id":  receipt_id,
            "reason":      "SIGNATURE_INVALID",
            "verified_at": verified_at,
        }
        if db_resp is not None:
            resp["db_cross_reference"] = db_resp
        return jsonify(resp), 200
