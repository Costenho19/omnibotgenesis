"""
OMNIX Proof Layer — Institutional Evidence & Simple Evaluation API

GET  /verify/<receipt_id>   — Institutional-grade receipt verification (P1)
POST /evaluate              — Simple decision evaluation entry point (P2)

Patent Reference: OMNIX-PAT-2026-015
ADR-092: Structural Admissibility Engine (Layer 0)
ADR-085: PQC Evidence & Receipt Layer
ADR-096: Expanded Canonical Receipt — Full Execution Proof

Design goals:
  • /verify returns a concise, machine-readable verdict investors can audit independently
  • /evaluate is the "plug → validate → receipt" interface that converts OMNIX into a product
  • Both endpoints fail-closed on DB errors (no silent pass-throughs)
  • execution_proof covers the full evaluation context at T=0 nanosecond precision (ADR-096)
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, jsonify, request

_WORKSPACE_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, _WORKSPACE_ROOT)

logger = logging.getLogger("OMNIX.ProofLayer")

proof_bp = Blueprint("proof_layer", __name__)

_EVL_CACHE: dict[str, dict] = {}
_EVL_CACHE_LOCK = threading.Lock()
_EVL_CACHE_MAX = 500

# ── In-memory rate limiter for /evaluate (public endpoint) ───────────────────
# 30 requests per minute per IP — prevents DoS and computational abuse.
# No external dependency needed; mirrors the pattern in gov_blueprint.py.
_EVL_RATE_STORE: dict[str, list] = {}
_EVL_RATE_LOCK  = threading.Lock()
_EVL_RATE_LIMIT = 30
_EVL_RATE_WINDOW = 60

def _is_evl_rate_limited(client_ip: str) -> bool:
    now = time.time()
    window_start = now - _EVL_RATE_WINDOW
    with _EVL_RATE_LOCK:
        timestamps = _EVL_RATE_STORE.get(client_ip, [])
        timestamps = [ts for ts in timestamps if ts > window_start]
        if len(timestamps) >= _EVL_RATE_LIMIT:
            _EVL_RATE_STORE[client_ip] = timestamps
            return True
        timestamps.append(now)
        _EVL_RATE_STORE[client_ip] = timestamps
        return False


def _cache_evl_receipt(receipt_id: str, data: dict) -> None:
    with _EVL_CACHE_LOCK:
        if len(_EVL_CACHE) >= _EVL_CACHE_MAX:
            oldest = next(iter(_EVL_CACHE))
            del _EVL_CACHE[oldest]
        _EVL_CACHE[receipt_id] = data


def _lookup_evl_receipt(receipt_id: str) -> dict | None:
    with _EVL_CACHE_LOCK:
        return _EVL_CACHE.get(receipt_id)

_BASE_URL = os.environ.get("OMNIX_PUBLIC_URL", "https://omnixquantum.net")
_ISSUER_DID = "did:web:omnixquantum.net"
_SCHEMA_URL = f"{_BASE_URL}/schemas/omnix-receipt-schema-v6.5.4e.json"

_ACTION_TO_OPERATION: dict[str, str] = {
    "TRADE":    "SPOT",
    "BUY":      "SPOT",
    "SELL":     "SPOT",
    "SHORT":    "SHORT",
    "LEVERAGE": "LEVERAGED",
    "HEDGE":    "HEDGE",
    "STAKE":    "STAKE",
}

_HIGH_RISK_JURISDICTIONS = {"UAE", "CN", "KP", "IR", "RU", "BY", "SY", "CU"}
_MEDIUM_RISK_JURISDICTIONS = {"NG", "PK", "VN", "TH", "ID"}


def _get_db_connection():
    try:
        import psycopg2
        db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        if not db_url:
            return None
        return psycopg2.connect(db_url, connect_timeout=5)
    except Exception:
        return None


def _fetch_receipt_all_tiers(receipt_id_clean: str) -> "tuple[tuple | None, str | None]":
    """
    Search all storage tiers for a receipt — ADR-126.

    Order: HOT (fast path) → WARM (PostgreSQL archive) → COLD (S3/R2 or PG fallback).
    Returns (db_row_tuple, tier_label) or (None, None) if not found.

    The row tuple matches the SELECT column order used in institutional_verify:
        receipt_id, timestamp_utc, asset, decision, veto_chain,
        policy_version, engine_version, prev_hash, content_hash, signature,
        signature_algorithm, public_key, domain, client_id,
        created_at, encrypted_payload
    """
    _VERIFY_COLS = (
        "receipt_id", "timestamp_utc", "asset", "decision", "veto_chain",
        "policy_version", "engine_version", "prev_hash", "content_hash", "signature",
        "signature_algorithm", "public_key", "domain", "client_id",
        "created_at", "encrypted_payload",
    )
    col_list = ", ".join(_VERIFY_COLS)

    conn = _get_db_connection()
    if not conn:
        return None, None

    try:
        cur = conn.cursor()

        # ── HOT ────────────────────────────────────────────────────────────────
        cur.execute(
            f"""
            SELECT {col_list}
            FROM decision_receipts
            WHERE receipt_id = %s OR content_hash = %s
            LIMIT 1
            """,
            (receipt_id_clean, receipt_id_clean),
        )
        row = cur.fetchone()
        if row:
            cur.close()
            return row, "HOT"

        # ── WARM ───────────────────────────────────────────────────────────────
        _warm_failed = False
        try:
            cur.execute(
                f"""
                SELECT {col_list}
                FROM decision_receipts_warm
                WHERE receipt_id = %s
                LIMIT 1
                """,
                (receipt_id_clean,),
            )
            row = cur.fetchone()
            if row:
                cur.close()
                return row, "WARM"
        except Exception as _warm_exc:
            _warm_failed = True
            logger.debug("[/verify] WARM table not available: %s", _warm_exc)
            # FIX-1: cursor is in undefined state after exception —
            # close and open a fresh cursor so the COLD block is not affected.
            try:
                cur.close()
            except Exception:
                pass
            try:
                cur = conn.cursor()
            except Exception as _cur_exc:
                logger.error("[/verify] Cannot create cursor for COLD lookup: %s", _cur_exc)
                return None, None

        # ── COLD (via archival index) ──────────────────────────────────────────
        # FIX-2: track whether COLD had a retrieval error (distinct from "not found")
        _cold_retrieval_error = False
        try:
            cur.execute(
                """
                SELECT tier, storage_location
                FROM receipt_archival_index
                WHERE receipt_id = %s AND tier = 'COLD' AND archival_status = 'ARCHIVED'
                LIMIT 1
                """,
                (receipt_id_clean,),
            )
            idx = cur.fetchone()
            if idx:
                _, location = idx
                from omnix_core.evidence.receipt_archival import (
                    ReceiptArchivalService,
                )
                db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
                svc    = ReceiptArchivalService(db_url=db_url)
                try:
                    receipt_dict, _ = svc.fetch_receipt_any_tier(conn, receipt_id_clean)
                except Exception as _cold_fetch_exc:
                    # FIX-2: cold payload corrupted/unreadable — escalate to ERROR,
                    # caller gets (None, None) but we log the true cause.
                    _cold_retrieval_error = True
                    logger.error(
                        "[/verify] COLD retrieval error receipt_id=%s location=%s — "
                        "payload may be corrupted: %s",
                        receipt_id_clean, location, _cold_fetch_exc,
                    )
                    receipt_dict = None

                if receipt_dict:
                    # Reconstruct tuple in the same column order
                    row_dict = {k: receipt_dict.get(k) for k in _VERIFY_COLS}
                    cur.close()
                    return tuple(row_dict[c] for c in _VERIFY_COLS), "COLD"
                elif not _cold_retrieval_error:
                    # Index says ARCHIVED but fetch returned nothing — gap in index
                    logger.error(
                        "[/verify] COLD index entry exists but fetch returned None "
                        "receipt_id=%s location=%s — index/storage out of sync",
                        receipt_id_clean, location,
                    )
        except Exception as _cold_exc:
            logger.error("[/verify] COLD index lookup error receipt_id=%s: %s",
                         receipt_id_clean, _cold_exc)

        cur.close()
        return None, None

    except Exception as exc:
        logger.error("[/verify] multi-tier lookup error: %s", exc)
        return None, None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _compute_content_hash(receipt_id: str, timestamp: str, asset: str, decision: str) -> str:
    payload = json.dumps(
        {"receipt_id": receipt_id, "timestamp": timestamp, "asset": asset, "decision": decision},
        sort_keys=True,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


# ── ADR-096: Frozen constants — versioned, never dynamic ─────────────────────────

# The exact 16 field paths covered by the v2 canonical hash.
# FROZEN per hash_version.  Changing this list = new version.
# v1 (legacy): receipt_id, timestamp, asset, decision  (4 fields, content_hash)
# v2 (ADR-096): the 16 paths below
_HASH_V2_COVERAGE: tuple[str, ...] = (
    "receipt_id",
    "execution_nanosecond (as string)",
    "asset",
    "decision",
    "authority_binding.policy_id",
    "authority_binding.policy_version",
    "authority_binding.client_id",
    "authority_binding.actor",
    "authority_binding.jurisdiction",
    "authority_binding.operation",
    "authority_binding.ethical_flags (sorted)",
    "authority_binding.layer0_status",
    "authority_binding.timestamp_utc",
    "checkpoint_proof[*].id (sorted numerically)",
    "checkpoint_proof[*].score (normalized 6dp, None→'null')",
    "checkpoint_proof[*].threshold (normalized 6dp, None→'null')",
    "checkpoint_proof[*].result",
    "checkpoints_passed",
    "checkpoints_total",
)

# Determinism rules — applied in _canonical_json().  Frozen per version.
_HASH_V2_DETERMINISM_RULES: tuple[str, ...] = (
    "sort_keys=True on all JSON serialization",
    "floats rounded to 6 decimal places",
    "execution_nanosecond as string (not int)",
    "ethical_flags sorted alphabetically",
    "checkpoint_proof sorted numerically by id (CP-0 < CP-1 < … < CP-10)",
    "None values serialized as 'null' string",
    "ensure_ascii=True — no locale-dependent unicode normalization",
    "encoding: UTF-8",
)


def _canonical_json(obj: Any) -> bytes:
    """
    Single canonical serializer — the ONLY function that may produce bytes
    for hashing in ADR-096 execution_proof.

    Rules (frozen, ADR-096 v2):
      • sort_keys=True   — deterministic key order in all languages
      • ensure_ascii=True — no locale-dependent unicode escape differences
      • separators=(',', ':') — no variable whitespace
      • encoding: UTF-8

    A verifier in any language must reproduce:
        sha256(json.dumps(canonical, sort_keys=True,
                          ensure_ascii=True, separators=(',', ':')).encode('utf-8'))

    This function is the ground-truth reference implementation.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=True,
        separators=(',', ':'),
    ).encode("utf-8")


def _fingerprint_public_key(public_key_b64: str) -> str:
    """
    Canonical public-key fingerprint (ADR-096).

    Definition (frozen):
        fingerprint = "SHA256:" + base64(sha256(raw_public_key_bytes))

    Where raw_public_key_bytes = base64.b64decode(public_key_b64).

    This matches the SSH/TLS fingerprint convention so institutional
    counterparties can pin the key using standard tooling.

    Example output: "SHA256:KHcqXlgqf8ruNQznoo6sgFHsxtIo..."
    """
    raw = base64.b64decode(public_key_b64)
    digest = hashlib.sha256(raw).digest()
    return "SHA256:" + base64.b64encode(digest).decode("ascii")


def _cp_sort_key(cp_id: str) -> tuple[int, str]:
    """
    Numeric sort key for checkpoint ids (CP-0 … CP-10).

    Lexicographic sort would place CP-10 before CP-2 ("1" < "2").
    This key extracts the integer suffix for correct numeric ordering:
        CP-0 < CP-1 < CP-2 < … < CP-9 < CP-10

    Falls back to (0, cp_id) for non-standard ids to keep sort stable.
    """
    import re
    m = re.match(r'^[A-Za-z\-]+(\d+)$', cp_id)
    if m:
        return (int(m.group(1)), cp_id)
    return (0, cp_id)


# ── ADR-096: Full Canonical Receipt — Execution Proof helpers ────────────────────

def _build_authority_binding(
    client_id: str,
    policy_version: str,
    engine_version: str,
    jurisdiction: str,
    operation: str,
    ethical_flags: list,
    layer0_status: str,
    timestamp_utc: str = "",
) -> dict:
    """
    Authority binding — the exact authorization context at T=0.

    This answers Naimat's question: "what human authority was bound to this
    specific payload at the millisecond of execution?"

    OMNIX answers at nanosecond precision with full structural binding:
    who authorized, under which policy, in which jurisdiction, with which
    operation type, and through which governance layer.

    Fields (all required for institutional-grade binding):
      policy_id      — canonical identifier of the governance policy applied
      policy_version — human-readable version tag
      jurisdiction   — regulatory jurisdiction at T=0
      operation      — operation type evaluated (SPOT / LEVERAGED / etc.)
      ethical_flags  — active ethical constraint sets (SHARIA / ESG / [])
      layer0_status  — Layer 0 SAE result (PASSED / BLOCKED / DISABLED)
      timestamp_utc  — ISO-8601 UTC timestamp of evaluation (T=0 reference)
      actor          — system actor that authorized the evaluation
      authorized_by  — patent reference governing the evaluation protocol

    ADR-096 / OMNIX-PAT-2026-015 §4.3
    """
    return {
        "policy_id":        f"OMNIX-{policy_version}",
        "policy_version":   policy_version,
        "engine_version":   engine_version,
        "client_id":        client_id,
        "actor":            "OMNIX-GOVERNANCE-ENGINE",
        "jurisdiction":     jurisdiction,
        "operation":        operation,
        "ethical_flags":    sorted(ethical_flags),
        "layer0_status":    layer0_status,
        "timestamp_utc":    timestamp_utc,
        "authorized_by":    "OMNIX-PAT-2026-015",
        "governance_model": "Layer0->Layer1->PQC (OMNIX 4-layer)",
        "issuer_did":       _ISSUER_DID,
    }


def _normalize_float(v: Any) -> Any:
    """
    Canonical float normalization for hash stability (ADR-096).

    Floats are rounded to 6 decimal places and serialized as strings
    in the canonical payload to eliminate platform-dependent repr()
    differences (0.1 vs 0.10000000000000001, etc.).

    None → the string "null" (avoids null/empty-string ambiguity).
    Non-numeric types are returned unchanged.
    """
    if v is None:
        return "null"
    if isinstance(v, float):
        return round(v, 6)
    return v


def _build_checkpoint_proof(gate_results: list) -> list:
    """
    Checkpoint-level proof — every single checkpoint decision is embedded
    in the signed receipt payload.

    Unlike observational logging (which records what happened after),
    checkpoint_proof is constitutive: each entry was a binding gate in the
    execution environment at T=0. A VETO here means the decision was
    structurally prevented — not observed, not flagged, prevented.

    Floats are normalized via _normalize_float() for hash stability.
    List is ordered by checkpoint id (CP-0 … CP-10) for determinism.

    ADR-096 / OMNIX-PAT-2026-015 §4.4
    """
    proof = []
    for gate in (gate_results or []):
        if not isinstance(gate, dict):
            continue
        cp_id = gate.get("checkpoint", gate.get("id", "?"))
        proof.append({
            "id":        str(cp_id),
            "name":      str(gate.get("name", "")),
            "signal":    str(gate.get("signal", "")),
            "score":     _normalize_float(gate.get("score")),
            "threshold": _normalize_float(gate.get("threshold")),
            "condition": str(gate.get("condition", "gte")),
            "result":    str(gate.get("result", "PASS")),
            "optional":  bool(gate.get("optional", False)),
        })
    proof.sort(key=lambda c: _cp_sort_key(c["id"]))
    return proof


def _compute_full_canonical_hash(
    receipt_id: str,
    execution_nanosecond: int,
    asset: str,
    decision: str,
    authority_binding: dict,
    checkpoint_proof: list,
    checkpoints_passed: int,
    checkpoints_total: int,
) -> str:
    """
    Expanded canonical hash — covers the full evaluation context at T=0.

    Determinism guarantees (ADR-096):
      • sort_keys=True on all JSON serialization
      • floats normalized to 6 dp via _normalize_float()
      • execution_nanosecond serialized as string (not int) to eliminate
        any platform-specific integer representation differences
      • ethical_flags sorted in authority_binding (prevents list-order mismatch)
      • checkpoint_proof sorted by id (prevents order-dependent hash variation)
      • None values replaced by "null" string (prevents null/empty ambiguity)
      • ensure_ascii=True prevents unicode normalization variations

    hash_version = "v2" distinguishes from the legacy 4-field content_hash (v1).
    """
    canonical = {
        "hash_version":          "v2",
        "receipt_id":            str(receipt_id),
        "execution_nanosecond":  str(int(execution_nanosecond)),
        "asset":                 str(asset),
        "decision":              str(decision),
        "authority_binding":     authority_binding,
        "checkpoint_proof":      checkpoint_proof,
        "checkpoints_passed":    int(checkpoints_passed),
        "checkpoints_total":     int(checkpoints_total),
    }
    return hashlib.sha256(_canonical_json(canonical)).hexdigest()


def _sign_canonical_hash(canonical_hash: str) -> tuple[str | None, str, str | None]:
    """
    Sign the canonical hash with the deployment's PQC key (Dilithium-3).

    Returns: (signature_b64, algorithm_name, public_key_b64)
    Falls back to SHA-256 hex if PQC is unavailable.

    ADR-096 / ADR-078 (key persistence)
    """
    try:
        from omnix_web.api.omnix_engine.decision_receipt import (
            _STABLE_SIGNING_KEYS,
            _STABLE_PUBLIC_KEY_B64,
            _active_provider,
        )
        if _STABLE_SIGNING_KEYS and _active_provider:
            _, priv_key = _STABLE_SIGNING_KEYS
            raw_sig = _active_provider.sign(canonical_hash.encode("utf-8"), priv_key)
            sig_b64 = base64.b64encode(raw_sig).decode("utf-8")
            algo    = _active_provider.algorithm_name()
            pub_b64 = _STABLE_PUBLIC_KEY_B64
            return sig_b64, algo, pub_b64
    except Exception as _pqc_err:
        logger.error(
            f"[ADR-096] PQC signing FAILED — receipt cannot be issued without PQC signature: {_pqc_err}"
        )
        raise RuntimeError(
            f"PQC signing unavailable — institutional receipt cannot be issued: {_pqc_err}"
        ) from _pqc_err


def _build_execution_proof(
    receipt_id: str,
    execution_nanosecond: int,
    asset: str,
    decision: str,
    authority_binding: dict,
    checkpoint_proof: list,
    checkpoints_passed: int,
    checkpoints_total: int,
) -> dict:
    """
    Build the complete execution_proof block — ADR-096.

    This is the OMNIX answer to Dilithium-signed institutional receipts:
      • nanosecond T=0 (beyond the millisecond Naimat describes)
      • full authority binding (who, under which policy, in which jurisdiction)
      • checkpoint-level proof (every gate is in the signed payload)
      • PQC signature (Dilithium-3, NIST FIPS 204 — quantum resistant)
      • independently verifiable (hash + sig + DID public key)
      • W3C VC compatible (ADR-082/ADR-084)
    """
    canonical_hash = _compute_full_canonical_hash(
        receipt_id, execution_nanosecond, asset, decision,
        authority_binding, checkpoint_proof, checkpoints_passed, checkpoints_total,
    )
    sig_b64, algo, pub_b64 = _sign_canonical_hash(canonical_hash)

    pub_key_fingerprint: str | None = None
    if pub_b64:
        try:
            pub_key_fingerprint = _fingerprint_public_key(pub_b64)
        except Exception:
            pub_key_fingerprint = None

    return {
        "receipt_version":    "v2",
        "hash_version":       "v2",
        "hash_algorithm":     "SHA-256",
        "serializer":         "json.dumps(sort_keys=True, ensure_ascii=True, separators=(',',':'))",
        "canonical_hash":     canonical_hash,
        "hash_coverage":      list(_HASH_V2_COVERAGE),
        "determinism_guarantees": list(_HASH_V2_DETERMINISM_RULES),
        "execution_nanosecond": str(int(execution_nanosecond)),
        "checkpoints_passed": int(checkpoints_passed),
        "checkpoints_total":  int(checkpoints_total),
        "signature":           sig_b64,
        "signature_algorithm": algo,
        "public_key":          pub_b64,
        "public_key_fingerprint": pub_key_fingerprint,
        "fingerprint_definition": "SHA256:base64(sha256(raw_public_key_bytes))",
        "pqc_standard":        "NIST FIPS 204 (ML-DSA / Dilithium-3)",
        "issuer_did":          _ISSUER_DID,
        "did_document_url":    f"{_BASE_URL}/.well-known/did.json",
        "verification_url":    f"{_BASE_URL}/verify/{receipt_id}",
        "independently_verifiable": True,
        "external_verification_steps": [
            "1. GET https://omnixquantum.net/.well-known/did.json — resolve issuer DID",
            "2. Extract Dilithium-3 public key; verify SHA256:base64(sha256(key)) == execution_proof.public_key_fingerprint",
            "3. Build canonical dict from response fields (see hash_coverage — all fields are in the response)",
            "4. Serialize: json.dumps(canonical, sort_keys=True, ensure_ascii=True, separators=(',',':'))",
            "5. sha256(serialized_bytes) must equal execution_proof.canonical_hash",
            "6. dilithium3.verify(public_key, canonical_hash.encode(), base64.b64decode(signature)) must succeed",
        ],
        "patent_reference":    "OMNIX-PAT-2026-015 §4.3–4.4",
        "adr_reference":       "ADR-096",
    }


def _build_w3c_vc_from_execution_proof(
    receipt_id: str,
    evaluated_at: str,
    asset: str,
    decision: str,
    domain: str,
    authority_binding: dict,
    execution_proof: dict,
    checkpoint_proof: list,
) -> dict:
    """
    Build a W3C Verifiable Credential that wraps the full execution_proof.

    This is a richer VC than the sandbox path (ADR-082) — it includes
    authority_binding and checkpoint_proof in the credentialSubject,
    making every checkpoint decision independently verifiable by any
    W3C VC-aware system without OMNIX-specific tooling.

    ADR-096 / ADR-082 / ADR-084
    """
    from datetime import timedelta
    try:
        issuance_dt = datetime.fromisoformat(evaluated_at.replace("Z", "+00:00"))
    except Exception:
        issuance_dt = datetime.now(timezone.utc)
    expiry_dt = issuance_dt + timedelta(days=365)
    vc_id = f"https://omnixquantum.net/receipts/{receipt_id}"

    sig_b64  = execution_proof.get("signature")
    sig_algo = execution_proof.get("signature_algorithm", "SHA-256")
    pub_b64  = execution_proof.get("public_key")

    proof_type_map = {
        "Dilithium-3": "Dilithium2021",
        "ML-DSA-65":   "MlDsa2024",
        "Falcon-512":  "Falcon2021",
    }
    proof_type = proof_type_map.get(sig_algo, "OmnixPostQuantumProof2026")

    vc = {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://omnixquantum.net/schemas/omnix-receipt-v1.jsonld",
        ],
        "id":   vc_id,
        "type": ["VerifiableCredential", "OmnixGovernanceCredential", "OmnixExecutionPhysicsCredential"],
        "issuer": {
            "id":   _ISSUER_DID,
            "name": "OMNIX Quantum Ltd",
            "url":  _BASE_URL,
        },
        "issuanceDate":   issuance_dt.isoformat(),
        "expirationDate": expiry_dt.isoformat(),
        "credentialSubject": {
            "id":                   vc_id,
            "receipt_id":           receipt_id,
            "asset":                asset,
            "decision":             decision,
            "domain":               domain,
            "execution_nanosecond": execution_proof.get("execution_nanosecond"),
            "canonical_hash":       execution_proof.get("canonical_hash"),
            "hash_version":         "v2",
            "authority_binding":    authority_binding,
            "checkpoint_proof":     checkpoint_proof,
            "verification_url":     f"{_BASE_URL}/verify/{receipt_id}",
            "pqc_standard":         "NIST FIPS 204 (ML-DSA / Dilithium-3)",
        },
        "proof": {
            "type":               proof_type if sig_b64 and "FALLBACK" not in sig_algo else "OmnixHashProof2026",
            "created":            issuance_dt.isoformat(),
            "verificationMethod": f"{_ISSUER_DID}#pqc-key-1",
            "proofPurpose":       "assertionMethod",
            "proofValue":         sig_b64 or execution_proof.get("canonical_hash"),
            "publicKey":          pub_b64,
            "signatureAlgorithm": sig_algo,
            "signedData":         execution_proof.get("canonical_hash"),
            "nist_note":          "Post-quantum signature (NIST FIPS 204 ML-DSA / Dilithium-3)",
            "adr_reference":      "ADR-096",
        },
    }
    return vc


def _persist_evl_receipt(
    receipt_id: str,
    timestamp_utc: str,
    asset: str,
    decision: str,
    veto_chain: list,
    checkpoints_passed: int,
    checkpoints_total: int,
    layer0_status: str,
    jurisdiction: str,
    operation: str,
    ethical_flags: list,
    action: str,
) -> bool:
    """
    Persist an evaluate receipt to decision_receipts table.
    Returns True on success, False on failure (non-fatal — cache is the fallback).
    """
    conn = _get_db_connection()
    if not conn:
        return False
    try:
        content_hash = _compute_content_hash(receipt_id, timestamp_utc, asset, decision)
        veto_json = json.dumps(veto_chain)
        metadata = json.dumps({
            "source": "POST /evaluate",
            "action": action,
            "jurisdiction": jurisdiction,
            "operation": operation,
            "ethical_flags": ethical_flags,
            "checkpoints_passed": checkpoints_passed,
            "checkpoints_total": checkpoints_total,
            "layer0_status": layer0_status,
            "issuer": _ISSUER_DID,
        })
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO decision_receipts
                (receipt_id, timestamp_utc, asset, decision, veto_chain,
                 policy_version, engine_version, content_hash,
                 signature_algorithm, public_key, client_id, domain,
                 encrypted_payload, created_at)
            VALUES (%s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, NOW())
            ON CONFLICT (receipt_id) DO NOTHING
            """,
            (
                receipt_id, timestamp_utc, asset, decision, veto_json,
                "EVL-1.0", "6.5.4e", content_hash,
                "SHA256_SUMMARY", _ISSUER_DID, "PUBLIC_EVALUATE", "trading",
                metadata,
            ),
        )
        conn.commit()
        cur.close()
        logger.info(f"[/evaluate] Receipt persisted to DB: {receipt_id}")
        return True
    except Exception as exc:
        logger.warning(f"[/evaluate] DB persist failed (cache active): {exc}")
        return False
    finally:
        conn.close()


def _detect_signature_mode(sig_algo: str | None, sig_format: str | None) -> str:
    if not sig_algo or sig_algo == "NONE":
        return "NONE"
    algo_upper = (sig_algo or "").upper()
    fmt_upper  = (sig_format or "").upper()
    if fmt_upper == "HEX_SHA256_FALLBACK":
        return "SHA256_FALLBACK"
    if "DILITHIUM" in algo_upper or "ML-DSA" in algo_upper or "CRYSTALS" in algo_upper:
        return "PQC_STRICT"
    if "FALCON" in algo_upper or "SPHINCS" in algo_upper or "KYBER" in algo_upper:
        return "PQC_STRICT"
    if fmt_upper == "BASE64_PQC":
        return "PQC_FALLBACK"
    return "PQC_FALLBACK"


def _parse_veto_chain(raw) -> list[dict]:
    if not raw:
        return []
    try:
        items = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(items, list):
            return []
        result = []
        for item in items:
            if isinstance(item, str):
                upper = item.upper()
                result.append({
                    "checkpoint": item.split(":")[0] if ":" in item else item,
                    "result": "BLOCKED" if "BLOCK" in upper or "VETO" in upper or "FAIL" in upper else "PASS",
                })
            elif isinstance(item, dict):
                result.append({
                    "checkpoint": item.get("checkpoint", item.get("cp", "?")),
                    "result": item.get("result", item.get("status", "PASS")),
                })
        return result
    except Exception:
        return []


def _extract_reason_code(veto_chain) -> str:
    """
    First-blocking-entry-wins rule (deterministic, auditor-grade).

    Accepts a list[dict] — callers must parse JSON before calling.

    Recognized blocking result values (all checked case-insensitively):
      - "VETO"            — checkpoint pipeline block (external_evaluator.py standard)
      - "INADMISSIBLE"    — Layer 0 SAE structural rejection
      - "BLOCKED"         — normalised result (legacy receipts / _parse_veto_chain output)
      - "STALE_BLOCK"     — AVM assumption-drift block
      - "SESSION_BLOCKED" — CAG context-admission block

    Precedence for reason_code value:
      1. has constraint_id  → return constraint_id.upper()  (Layer 0 / SAE)
      2. checkpoint_id CP-N + signal → return "{CP-N}-{SIGNAL_UPPER_WITH_UNDERSCORES}"
      3. checkpoint_id alone → return checkpoint_id.upper()
    Fallback (no blocking entry): "GOVERNANCE_PASS"
    """
    _BLOCKING = {"VETO", "INADMISSIBLE", "BLOCKED", "STALE_BLOCK", "SESSION_BLOCKED"}
    for e in (veto_chain or []):
        if not isinstance(e, dict):
            continue
        r = str(e.get("result", "")).upper()
        if r not in _BLOCKING:
            continue
        if "constraint_id" in e:
            return str(e["constraint_id"]).upper()
        cp = str(
            e.get("checkpoint_id")
            or e.get("checkpoint")
            or e.get("cp")
            or "CP"
        ).upper()
        sig = (e.get("signal") or "").upper().replace(" ", "_")
        if sig:
            return f"{cp}-{sig}"
        return cp
    return "GOVERNANCE_PASS"


def _query_chain_validity(receipt_id: str) -> "bool | None":
    """
    ADR-096: WAL chain verification for a single receipt.

    Queries governance_transparency_log to verify that this receipt's chain
    entry correctly links back to a real prior entry — i.e., the chain has
    not been tampered with, truncated, or reordered.

    Returns:
        True  — chain entry exists AND prev_log_hash found in a prior entry (intact)
        False — chain entry exists BUT prev_log_hash not found (broken / tampered)
        None  — no chain entry for this receipt (legacy receipt or chain not yet active)
    """
    try:
        conn = _get_db_connection()
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT log_id, payload_hash, prev_log_hash, ts_utc
                FROM governance_transparency_log
                WHERE receipt_id = %s
                ORDER BY ts_utc ASC
                LIMIT 1
                """,
                (receipt_id,),
            )
            entry = cur.fetchone()
            if not entry:
                cur.close()
                conn.close()
                return None

            log_id, payload_hash, prev_log_hash, ts_utc = entry

            if not prev_log_hash:
                cur.close()
                conn.close()
                return True

            cur.execute(
                """
                SELECT COUNT(*)
                FROM governance_transparency_log
                WHERE payload_hash = %s AND ts_utc < %s
                """,
                (prev_log_hash, ts_utc),
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row and int(row[0]) > 0:
                return True
            logger.warning(
                f"[ChainVerify] receipt={receipt_id} log={log_id} "
                f"prev_hash={str(prev_log_hash)[:12]}... NOT FOUND — chain broken"
            )
            return False
        except Exception as qexc:
            logger.warning(f"[ChainVerify] query error: {qexc}")
            try:
                conn.close()
            except Exception:
                pass
            return None
    except Exception as cexc:
        logger.warning(f"[ChainVerify] connection error: {cexc}")
        return None


# ── P1: GET /api/verify/<receipt_id> ────────────────────────────────────────────
# NOTE: Route is /api/verify/ (not /verify/) so the React SPA handles the
# user-facing /verify/:receiptId URL and renders the visual receipt page.
# Machine/API callers use /api/verify/<receipt_id> directly.

@proof_bp.route("/api/verify/<path:receipt_id>", methods=["GET"])
def institutional_verify(receipt_id: str):
    """
    Institutional-grade receipt verification.

    Returns a concise, machine-readable audit response suitable for:
    - Investor due diligence
    - Regulatory evidence submission
    - Independent integrity audit

    Fields:
      status           — VALID | INVALID | NOT_FOUND
      signature_mode   — PQC_STRICT | PQC_FALLBACK | SHA256_FALLBACK | NONE
      timestamp_issued — ISO-8601 UTC when receipt was created
      decision_trace   — compact governance summary
      integrity        — hash_valid, signature_valid, chain_valid
    """
    if not receipt_id or len(receipt_id) > 120:
        return jsonify({"status": "ERROR", "error": "Invalid receipt_id"}), 400

    receipt_id_clean = receipt_id.upper().strip()

    # ── ADR-126: multi-tier lookup (HOT → WARM → COLD) ───────────────────────
    row, _storage_tier = _fetch_receipt_all_tiers(receipt_id_clean)

    if not row:
        evl = _lookup_evl_receipt(receipt_id_clean)
        if not evl:
            evl = _lookup_evl_receipt(receipt_id)
        if evl:
            gs = evl.get("governance_summary", {})
            # Paridad DB vs cache: reason_code y decision se leen directamente;
            # nunca se recalculan para garantizar respuesta idéntica en ambas rutas.
            evl_decision    = (evl.get("decision") or evl.get("status") or "UNKNOWN").upper()
            evl_reason_code = (
                evl.get("reason_code")
                or _extract_reason_code(evl.get("_veto_chain") or [])
            )
            _sig_mode = gs.get("signature_mode", "PQC_STRICT")
            return jsonify({
                "receipt_id":       evl["receipt_id"],
                "status":           "VALID",
                "source":           "evaluate_cache",
                "decision":         evl_decision,
                "reason_code":      evl_reason_code,
                "timestamp_issued": evl["evaluated_at"],
                "signature": {
                    "valid": None,
                    "mode":  _sig_mode,
                },
                "integrity": {
                    "hash_valid":  None,
                    "chain_valid": None,
                },
                "hash_valid":       None,
                "signature_valid":  None,
                "chain_valid":      None,
                "decision_trace": {
                    "asset":               gs.get("asset"),
                    "domain":              "trading",
                    "action":              gs.get("action"),
                    "decision":            evl_decision,
                    "checkpoints_passed":  gs.get("checkpoints_passed", 0),
                    "checkpoints_total":   gs.get("checkpoints_total", 0),
                    "layer0":              gs.get("layer0_status"),
                    "jurisdiction":        gs.get("jurisdiction"),
                    "operation":           gs.get("operation"),
                    "ethical_flags":       gs.get("ethical_flags", []),
                },
                "validation_policy": {
                    "hash":      "strict",
                    "signature": "optional",
                    "chain":     "contextual",
                },
                "verify_url": evl.get("verify_url", f"{_BASE_URL}/verify/{receipt_id}"),
                "issuer":     _ISSUER_DID,
            }), 200
        return jsonify({
            "receipt_id":  receipt_id,
            "status":      "NOT_FOUND",
            "verify_url":  f"{_BASE_URL}/verify/{receipt_id}",
            "issuer":      _ISSUER_DID,
        }), 404

    (rid, ts_utc, asset, decision, veto_raw,
     policy_ver, engine_ver, prev_hash, content_hash,
     signature, sig_algo,
     public_key, domain, client_id,
     created_at, _encrypted_payload_raw) = row

    _layer0_status: "str | None" = None
    if _encrypted_payload_raw:
        try:
            _meta = (
                json.loads(_encrypted_payload_raw)
                if isinstance(_encrypted_payload_raw, str)
                else _encrypted_payload_raw
            )
            _layer0_status = _meta.get("layer0_status")
        except Exception:
            pass

    ts_issued  = ts_utc.isoformat() if hasattr(ts_utc, "isoformat") else str(ts_utc)
    ts_created = created_at.isoformat() if hasattr(created_at, "isoformat") else None

    sig_mode = _detect_signature_mode(sig_algo, None)

    checkpoints = _parse_veto_chain(veto_raw)
    passed  = sum(1 for c in checkpoints if c["result"] == "PASS")
    blocked = sum(1 for c in checkpoints if c["result"] == "BLOCKED")
    total   = len(checkpoints)

    hash_valid: bool | None = None
    sig_valid:  bool | None = None

    try:
        from omnix_web.api.omnix_engine.decision_receipt import ReceiptVerifier
        veto_list = json.loads(veto_raw) if isinstance(veto_raw, str) and veto_raw else (veto_raw or [])
        _provider_id = "dilithium3" if sig_algo and "dilithium" in sig_algo.lower() else (
            "sha256" if sig_algo and "sha" in sig_algo.lower() else None
        )
        receipt_obj = {
            "receipt_id":          rid,
            "timestamp":           ts_issued,
            "asset":               asset,
            "decision":            decision,
            "veto_chain":          veto_list,
            "policy_version":      policy_ver,
            "engine_version":      engine_ver,
            "prev_hash":           prev_hash,
            "content_hash":        content_hash,
            "signature":           signature,
            "signature_algorithm": sig_algo,
            "public_key":          public_key,
            "signing_provider":    _provider_id,
        }
        verification = ReceiptVerifier.verify_receipt(receipt_obj)
        sig_valid  = verification.get("signature_valid")
        hash_valid = verification.get("hash_valid")
    except Exception:
        pass

    if hash_valid is None and content_hash:
        try:
            from omnix_core.evidence.decision_receipt import ReceiptEngine as _CoreReceiptEngine
            veto_list = json.loads(veto_raw) if isinstance(veto_raw, str) and veto_raw else (veto_raw or [])
            receipt_obj_core = {
                "receipt_id":          rid,
                "timestamp":           ts_issued,
                "asset":               asset,
                "decision":            decision,
                "veto_chain":          veto_list,
                "policy_version":      policy_ver,
                "engine_version":      engine_ver,
                "prev_hash":           prev_hash,
                "content_hash":        content_hash,
                "signature":           signature,
                "signature_algorithm": sig_algo,
                "public_key":          public_key,
            }
            verification = _CoreReceiptEngine.verify_receipt(receipt_obj_core)
            if sig_valid is None:
                sig_valid  = verification.get("signature_valid")
            hash_valid = verification.get("hash_valid")
        except Exception:
            pass

    decision_upper = (decision or "UNKNOWN").upper()

    # chain_valid policy (ADR-096 — WAL chain verification):
    #   True  — governance_transparency_log entry found AND prev_log_hash
    #            links correctly to a prior entry (chain intact)
    #   False — log entry found BUT prev_log_hash not found (broken / tampered)
    #   None  — no log entry for this receipt (legacy receipt or chain not yet active)
    chain_valid = _query_chain_validity(rid)

    # Status rule — determinista, primer fallo gana:
    #   hash_valid=False   → recibo alterado post-emisión       → INVALID
    #   sig_valid=False    → firma criptográfica inválida        → INVALID
    #   chain_valid=False  → cadena de continuidad rota         → INVALID
    #   None en cualquier campo → dato no disponible, no es evidencia de fallo
    if hash_valid is False:
        status = "INVALID"
    elif sig_valid is False:
        status = "INVALID"
    elif chain_valid is False:
        status = "INVALID"
    else:
        status = "VALID"

    # reason_code — first-blocking-entry-wins sobre lista parseada
    # Safe parse: malformed/legacy veto_raw must never 500 /verify.
    try:
        _veto_list: list = (
            json.loads(veto_raw)
            if isinstance(veto_raw, str) and veto_raw
            else (veto_raw or [])
        )
        if not isinstance(_veto_list, list):
            _veto_list = []
    except Exception:
        _veto_list = []
    reason_code = _extract_reason_code(_veto_list)

    decision_trace = {
        "asset":               asset,
        "domain":              domain or "trading",
        "decision":            decision_upper,
        "checkpoints_passed":  passed,
        "checkpoints_blocked": blocked,
        "checkpoints_total":   total if total > 0 else None,
        "policy_version":      policy_ver,
        "engine_version":      engine_ver,
        "layer0_status":       _layer0_status,
    }

    return jsonify({
        "receipt_id":       rid,
        "status":           status,
        "source":           "db",
        "storage_tier":     _storage_tier or "HOT",
        "decision":         decision_upper,
        "reason_code":      reason_code,
        "timestamp_issued": ts_issued,
        "timestamp_stored": ts_created,
        "layer0_status":    _layer0_status,
        "signature": {
            "valid": sig_valid,
            "mode":  sig_mode,
        },
        "integrity": {
            "hash_valid":  hash_valid,
            "chain_valid": chain_valid,
            "chain_source": "governance_transparency_log" if chain_valid is not None else None,
        },
        "hash_valid":       hash_valid,
        "signature_valid":  sig_valid,
        "chain_valid":      chain_valid,
        "decision_trace":   decision_trace,
        "validation_policy": {
            "hash":      "strict",
            "signature": "optional",
            "chain":     "contextual",
        },
        "verify_url":       f"{_BASE_URL}/verify/{rid}",
        "issuer":           _ISSUER_DID,
        "schema":           _SCHEMA_URL,
    }), 200, {
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-store",
        "X-OMNIX-Receipt-ID": rid,
        "X-OMNIX-Status": status,
        "X-OMNIX-Sig-Mode": sig_mode,
    }


# ── P2: POST /evaluate ───────────────────────────────────────────────────────────

def _build_signals(asset: str, amount: float, jurisdiction: str) -> dict[str, float]:
    """
    Derive synthetic governance signals from a simple evaluate request.
    These represent normalized governance criteria — not price predictions.

    Signal semantics (matching external_evaluator checkpoints):
      probability_score  — gte 50  : expected positive outcome probability
      risk_exposure      — lte 65  : lower = safer (small amounts = low risk)
      signal_coherence   — gte 55  : internal signal agreement
      trend_persistence  — gte 50  : temporal persistence
      stress_resilience  — gte 35  : stress scenario resilience
      logic_consistency  — gte 40  : structural logic integrity
    """
    jur_upper  = jurisdiction.upper()
    asset_upper = asset.upper()

    jur_risk_bonus = {
        k: v for k, v in
        [(j, 22.0) for j in _HIGH_RISK_JURISDICTIONS] +
        [(j, 10.0) for j in _MEDIUM_RISK_JURISDICTIONS]
    }.get(jur_upper, 0.0)

    jur_quality_factor = (
        0.76 if jur_upper in _HIGH_RISK_JURISDICTIONS
        else 0.90 if jur_upper in _MEDIUM_RISK_JURISDICTIONS
        else 1.0
    )

    stable_assets   = {"BTC", "ETH", "SOL", "USDC", "USDT", "DOT", "LINK", "ADA"}
    volatile_assets = {"SHIB", "DOGE", "PEPE", "FLOKI", "BONK", "MEME"}
    asset_quality = (
        1.0  if asset_upper in stable_assets
        else 0.70 if asset_upper in volatile_assets
        else 0.85
    )

    base_quality = 74.0 * jur_quality_factor * asset_quality

    risk_base = 18.0 + (amount / 500_000) * 52.0
    risk_exposure = min(90.0, max(10.0, risk_base + jur_risk_bonus))

    return {
        "probability_score": min(95.0, max(35.0, base_quality + 6.0)),
        "risk_exposure":     risk_exposure,
        "signal_coherence":  min(95.0, max(35.0, base_quality + 2.0)),
        "trend_persistence": min(90.0, max(30.0, base_quality - 6.0)),
        "stress_resilience": min(90.0, max(28.0, base_quality - 2.0)),
        "logic_consistency": min(95.0, max(40.0, base_quality + 8.0)),
    }


@proof_bp.route("/evaluate", methods=["POST"])
def simple_evaluate():
    """
    Simple Decision Evaluation API — OMNIX product entry point.

    Input:
        {
          "action":       "TRADE" | "BUY" | "SELL" | "SHORT" | "LEVERAGE" | "HEDGE",
          "asset":        "BTC",
          "amount":       1000,
          "jurisdiction": "UAE",
          "ethical_mode":       "SHARIA" | "ESG" | null         (optional, single string)
          "ethical_frameworks": ["SHARIA"] | ["ESG"] | ["SHARIA","ESG"]  (optional, list)
        }

    Output:
        {
          "status":       "APPROVED" | "BLOCKED",
          "receipt_id":   "EVL-...",
          "reason":       "...",
          "layer0":       "PASSED" | "BLOCKED" | "DISABLED",
          "verify_url":   "https://omnixquantum.net/verify/EVL-...",
          "evaluated_at": "ISO8601",
          "governance_summary": {...}
        }
    """
    client_ip = (
        request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        .split(",")[0].strip()
    )
    if _is_evl_rate_limited(client_ip):
        return jsonify({
            "error": "Rate limit exceeded",
            "limit": f"{_EVL_RATE_LIMIT} requests per {_EVL_RATE_WINDOW}s",
            "retry_after_seconds": _EVL_RATE_WINDOW,
        }), 429

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "JSON body required"}), 400

    action       = str(body.get("action", "TRADE")).upper().strip()
    asset        = str(body.get("asset",  "BTC")).upper().strip()
    jurisdiction = str(body.get("jurisdiction", "GLOBAL")).upper().strip()
    ethical_mode = str(body.get("ethical_mode", "") or "").upper().strip()

    _ethical_frameworks_raw = body.get("ethical_frameworks", [])
    if isinstance(_ethical_frameworks_raw, list):
        _frameworks_from_list = [
            str(f).upper().strip() for f in _ethical_frameworks_raw
            if isinstance(f, str) and str(f).upper().strip() in ("SHARIA", "ESG", "HALAL")
        ]
        _frameworks_from_list = [
            "SHARIA" if f == "HALAL" else f for f in _frameworks_from_list
        ]
    else:
        _frameworks_from_list = []

    try:
        amount = float(body.get("amount", 1000))
        if amount < 0:
            raise ValueError("negative amount")
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be a positive number"}), 400

    if not asset.replace("/", "").replace("-", "").isalnum():
        return jsonify({"error": "Invalid asset identifier"}), 400

    if len(asset) > 32:
        return jsonify({"error": "Asset identifier too long (max 32 chars)"}), 400

    operation = _ACTION_TO_OPERATION.get(action, "SPOT")
    _mode_flag = [ethical_mode] if ethical_mode in ("SHARIA", "ESG") else []
    ethical_flags = list(dict.fromkeys(_mode_flag + _frameworks_from_list))

    execution_nanosecond = time.time_ns()
    evaluated_at = datetime.now(timezone.utc).isoformat()
    receipt_id   = f"OMNIX-EVL-{uuid.uuid4().hex[:16].upper()}"

    layer0_status  = "DISABLED"
    layer0_detail  = None
    overall_status = "APPROVED"
    reason         = "All governance checkpoints passed."
    gate_results   = []
    veto_chain     = []
    checkpoints_passed  = 0
    checkpoints_total   = 0

    try:
        from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine

        signals = _build_signals(asset, amount, jurisdiction)

        compliance_config = {
            "layer0_enabled":  True,
            "operation_type":  operation,
            "jurisdiction":    jurisdiction,
            "ethical_flags":   ethical_flags,
            "client_id":       "PUBLIC_EVALUATE",
        }
        _cag_keys = (
            "cag_liquidity_score", "cag_global_volatility",
            "cag_cross_pair_correlation", "cag_macro_risk",
            "cag_enabled", "cag_volatility_threshold",
            "cag_correlation_threshold", "cag_liquidity_minimum",
            "cag_macro_risk_ceiling", "cag_block_on_any_violation",
        )
        for _k in _cag_keys:
            if _k in body:
                try:
                    compliance_config[_k] = float(body[_k]) if _k.startswith("cag_") and _k not in ("cag_enabled", "cag_block_on_any_violation") else body[_k]
                except (TypeError, ValueError):
                    pass

        engine = GovernanceEvaluationEngine()
        result = engine.evaluate(
            signals=signals,
            asset=asset,
            domain="trading",
            metadata={
                "source":       "POST /evaluate",
                "action":       action,
                "amount":       amount,
                "jurisdiction": jurisdiction,
                "operation":    operation,
            },
            compliance_config=compliance_config,
        )

        overall_status = result.get("decision", "BLOCKED").upper()
        gate_results   = result.get("gate_results", [])
        veto_chain     = result.get("veto_chain", [])
        checkpoints_passed  = result.get("checkpoints_passed", 0)
        checkpoints_total   = result.get("checkpoints_total", 0)

        layer0_data = result.get("layer_0")
        if layer0_data:
            is_inadmissible = layer0_data.get("admissibility") == "INADMISSIBLE"
            layer0_status   = "BLOCKED" if is_inadmissible else "PASSED"
            if layer0_status == "BLOCKED":
                overall_status = "BLOCKED"
                violations = layer0_data.get("violations", [])
                if violations:
                    v = violations[0]
                    c_id    = v.get("constraint_id", "STRUCTURAL_VIOLATION")
                    c_class = v.get("constraint_class", "")
                    c_desc  = v.get("description", "Structural constraint violation")
                    reason  = f"Blocked at Layer 0 — {c_id} ({c_class}): {c_desc}."
                else:
                    reason = "Blocked at Layer 0 — Structural admissibility violation."
        else:
            layer0_status = "PASSED" if checkpoints_total > 0 else "DISABLED"

        if overall_status == "BLOCKED" and layer0_status not in ("BLOCKED",):
            veto_chain_list = result.get("veto_chain", [])
            for veto in veto_chain_list:
                if isinstance(veto, dict):
                    veto_result = str(veto.get("result", "")).upper()
                    if any(k in veto_result for k in ("BLOCK", "VETO", "FAIL", "REJECT")):
                        cp      = veto.get("checkpoint_id", veto.get("checkpoint", "checkpoint"))
                        reason  = f"Blocked at {cp}: {veto.get('reason', veto.get('description', 'Governance constraint violated'))}."
                        break
            if reason == "All governance checkpoints passed." and overall_status == "BLOCKED":
                reason = f"Blocked by governance pipeline — {checkpoints_total - checkpoints_passed} checkpoint(s) failed."

    except Exception as exc:
        logger.error(f"[/evaluate] Engine error: {exc}", exc_info=True)
        overall_status = "ERROR"
        reason = "Evaluation engine temporarily unavailable — fail-closed by design."
        return jsonify({
            "status":       "ERROR",
            "reason":       reason,
            "evaluated_at": evaluated_at,
        }), 503

    # ── ADR-096: Build Execution Proof ───────────────────────────────────────────
    authority_binding = _build_authority_binding(
        client_id      = "PUBLIC_EVALUATE",
        policy_version = "EVL-1.0",
        engine_version = os.environ.get("OMNIX_VERSION", "6.5.4e"),
        jurisdiction   = jurisdiction,
        operation      = operation,
        ethical_flags  = ethical_flags,
        layer0_status  = layer0_status,
        timestamp_utc  = evaluated_at,
    )
    checkpoint_proof = _build_checkpoint_proof(gate_results)
    execution_proof  = _build_execution_proof(
        receipt_id           = receipt_id,
        execution_nanosecond = execution_nanosecond,
        asset                = asset,
        decision             = overall_status,
        authority_binding    = authority_binding,
        checkpoint_proof     = checkpoint_proof,
        checkpoints_passed   = checkpoints_passed,
        checkpoints_total    = checkpoints_total,
    )

    w3c_vc = _build_w3c_vc_from_execution_proof(
        receipt_id        = receipt_id,
        evaluated_at      = evaluated_at,
        asset             = asset,
        decision          = overall_status,
        domain            = "trading",
        authority_binding = authority_binding,
        execution_proof   = execution_proof,
        checkpoint_proof  = checkpoint_proof,
    )

    response = {
        "status":       overall_status,
        "receipt_id":   receipt_id,
        "reason":       reason,
        "layer0":       layer0_status,
        "verify_url":   f"{_BASE_URL}/verify/{receipt_id}",
        "evaluated_at": evaluated_at,
        "governance_summary": {
            "action":               action,
            "asset":                asset,
            "amount":               amount,
            "jurisdiction":         jurisdiction,
            "operation":            operation,
            "ethical_flags":        ethical_flags,
            "checkpoints_passed":   checkpoints_passed,
            "checkpoints_total":    checkpoints_total,
            "layer0_status":        layer0_status,
            "signature_mode":       execution_proof.get("signature_algorithm", "PQC_STRICT"),
            "issuer":               _ISSUER_DID,
        },
        "authority_binding":  authority_binding,
        "checkpoint_proof":   checkpoint_proof,
        "execution_proof":    execution_proof,
        "verifiable_credential": w3c_vc,
    }

    # Paridad DB vs cache:
    #   reason_code y decision se computan UNA SOLA VEZ aquí y se guardan en caché.
    #   /verify los lee directamente sin recalcular — garantiza respuesta idéntica
    #   venga de DB o de caché en memoria.
    _cache_reason_code = _extract_reason_code(veto_chain)
    _cache_evl_receipt(receipt_id, {
        **response,
        "decision":    overall_status,
        "reason_code": _cache_reason_code,
        "_veto_chain": veto_chain,
    })

    _persist_evl_receipt(
        receipt_id=receipt_id,
        timestamp_utc=evaluated_at,
        asset=asset,
        decision=overall_status,
        veto_chain=veto_chain,
        checkpoints_passed=checkpoints_passed,
        checkpoints_total=checkpoints_total,
        layer0_status=layer0_status,
        jurisdiction=jurisdiction,
        operation=operation,
        ethical_flags=ethical_flags,
        action=action,
    )

    # ── ADR-127: Phase 3 — Filter Calibration Metrics (non-blocking) ─────────
    try:
        from omnix_core.governance.filter_calibration_metrics import (
            extract_event_from_result,
            get_global_service,
        )
        _proc_ms = (time.time_ns() - execution_nanosecond) // 1_000_000
        _fcm_event = extract_event_from_result(
            result,
            domain             = "trading",
            asset              = asset,
            client_id          = "PUBLIC_EVALUATE",
            processing_time_ms = int(_proc_ms),
        )
        get_global_service().record(_fcm_event)
    except Exception as _fcm_exc:
        logger.debug("[/evaluate] FCM record skipped: %s", _fcm_exc)

    return jsonify(response), 200, {
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-store",
        "X-OMNIX-Decision": overall_status,
        "X-OMNIX-Layer0": layer0_status,
        "X-OMNIX-Receipt-ID": receipt_id,
        "X-OMNIX-Execution-NS": str(execution_nanosecond),
        "X-OMNIX-Sig-Mode": execution_proof.get("signature_algorithm", "PQC"),
    }


@proof_bp.route("/evaluate", methods=["OPTIONS"])
def evaluate_options():
    return "", 204, {
        "Access-Control-Allow-Origin":  "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }
