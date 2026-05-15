"""
OMNIX Forensic API Blueprint — ADR-164 (Forensic Archive Verification Portal)
============================================================================
Two-plane verification architecture:
  Plane 1: Browser (preliminary, hash + chain)
  Plane 2: Server (authoritative, PQC + canonical)

Endpoints:
  GET  /api/forensic/status   — verifier health (fail-closed if verifier absent)
  POST /api/forensic/verify   — authoritative Plane 2 verification (FVP-INV-005)
  POST /api/forensic/export   — generate + stream OEP bundle (ADR-165)

Rate limits (ADR-164 §4):
  /verify: 60 per minute (PQC verification is CPU-intensive)
  /export: 10 per minute (OEP generation is I/O + CPU intensive)

ADR-164: FVP-INV-006 — server verdict binding ONLY for PQC layer (not hash reality).
ADR-164: FVP-INV-004 — SIGNATURE_INVALID emitted ONLY by this server path.

SECURITY NOTE on /export key handling:
  /export accepts caller-provided secret_key_b64. The generated OEP will bear the
  fingerprint of the caller's key — not the OMNIX platform key. This is intentional
  for self-service forensic packaging. Production deployments requiring platform-keyed
  OEPs should authenticate the endpoint (RBAC/API key) and pin to the platform key.
"""
import sys
import os
import importlib.util
import json
import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, send_file, current_app
from pathlib import Path
import tempfile
import io

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    _HAS_LIMITER = True
except ImportError:
    _HAS_LIMITER = False

# ── Bootstrap omnix_core ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WORKSPACE_ROOT = os.path.dirname(BASE_DIR)
if _WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, _WORKSPACE_ROOT)

from omnix_core.evidence.oep_generator import OEPGenerator, OEPConfig

logger = logging.getLogger("OMNIX.ForensicAPI")

forensic_bp = Blueprint("forensic_bp", __name__)

# ── Verifier loader (fail-closed) ─────────────────────────────────────────────
_VERIFIER_PATH = os.path.join(
    _WORKSPACE_ROOT, "docs", "zenodo", "submission_package", "omnix_atf_verify.py"
)

_verifier = None
_verifier_load_error: str | None = None


def _load_verifier():
    """Load omnix_atf_verify.py dynamically. Fail-closed: any error captured."""
    global _verifier, _verifier_load_error
    if not os.path.exists(_VERIFIER_PATH):
        _verifier_load_error = f"Verifier not found at {_VERIFIER_PATH}"
        logger.error("[ForensicAPI] %s", _verifier_load_error)
        return
    try:
        spec = importlib.util.spec_from_file_location("omnix_atf_verify", _VERIFIER_PATH)
        if spec is None or spec.loader is None:
            _verifier_load_error = "importlib spec is None — cannot load verifier"
            logger.error("[ForensicAPI] %s", _verifier_load_error)
            return
        module = importlib.util.module_from_spec(spec)
        sys.modules["omnix_atf_verify"] = module
        spec.loader.exec_module(module)   # type: ignore[union-attr]
        _verifier = module
        logger.info("[ForensicAPI] Verifier loaded — omnix_atf_verify v1.1.0")
    except Exception as exc:
        _verifier_load_error = f"{type(exc).__name__}: {exc}"
        logger.error("[ForensicAPI] Verifier load failed: %s", _verifier_load_error)


_load_verifier()


# ── GET /status ───────────────────────────────────────────────────────────────

@forensic_bp.route("/status", methods=["GET"])
def get_status():
    """
    Health endpoint — fail-closed.
    Returns 'degraded' if verifier is absent; 'ok' only when fully operational.
    """
    if _verifier is None:
        return jsonify({
            "status": "degraded",
            "verifier_version": None,
            "verifier_error": _verifier_load_error,
            "algorithms": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Server-side PQC verification (Plane 2) is unavailable. Hash/chain checks still work browser-side.",
        }), 503
    return jsonify({
        "status": "ok",
        "verifier_version": "1.1.0",
        "algorithms": ["ML-DSA-65 (FIPS 204)", "sha256-v1"],
        "verifier_path": _VERIFIER_PATH,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ── POST /verify (Plane 2 — Authoritative) ────────────────────────────────────

@forensic_bp.route("/verify", methods=["POST"])
def verify_block():
    """
    Authoritative server-side verification (Plane 2 — ADR-164 §1).
    Uses the same pypqc / omnix_atf_verify.py that SIGNED the blocks.
    This is the only code path that may emit SIGNATURE_INVALID (FVP-INV-004).
    FVP-INV-006: this verdict is binding — it overrides browser (Plane 1) results.
    """
    # ── Verifier availability check ───────────────────────────────────────────
    if _verifier is None:
        return jsonify({
            "verdict": "INCOMPLETE",
            "reasons": [f"Server verifier unavailable: {_verifier_load_error}"],
            "checks": {
                "merkle_valid": None,
                "canonical_valid": None,
                "chain_valid": None,
                "signature_valid": None,
            },
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "verifier_version": None,
            "error": "Verifier module not loaded",
        }), 503

    # ── Parse request ─────────────────────────────────────────────────────────
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({
                "error": "Missing or invalid JSON body",
                "verdict": "INCOMPLETE",
            }), 400

        block = data.get("block")
        public_key_b64 = data.get("public_key_b64") or None
        predecessor_block = data.get("predecessor_block") or None

        if not block:
            return jsonify({"error": "Missing 'block' field", "verdict": "INCOMPLETE"}), 400

    except Exception as exc:
        logger.warning("[ForensicAPI/verify] Request parse error: %s", exc)
        return jsonify({"error": "Request parse error", "verdict": "INCOMPLETE"}), 400

    # ── Call verifier (correct ADR-163 signature) ─────────────────────────────
    try:
        result = _verifier.verify_archive_block(
            block,
            public_key_b64=public_key_b64,          # optional — skips PQC if None
            predecessor_block=predecessor_block,     # optional — skips chain check if None
        )
    except Exception as exc:
        logger.exception("[ForensicAPI/verify] verify_archive_block raised: %s", exc)
        return jsonify({
            "verdict": "INCOMPLETE",
            "reasons": [f"Verifier internal error: {type(exc).__name__}"],
            "checks": {
                "merkle_valid": None,
                "canonical_valid": None,
                "chain_valid": None,
                "signature_valid": None,
            },
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "verifier_version": "1.1.0",
        }), 500

    # ── Build response ────────────────────────────────────────────────────────
    # ArchiveBlockResult fields: verdict, merkle_valid, canonical_valid,
    # chain_valid, pqc_signature_valid, failure_reasons, warnings
    try:
        checks = {
            "merkle_valid":    getattr(result, "merkle_valid", None),
            "canonical_valid": getattr(result, "canonical_valid", None),
            "chain_valid":     getattr(result, "chain_valid", None),
            "signature_valid": getattr(result, "pqc_signature_valid", None),
        }
        return jsonify({
            "verdict":          result.verdict,
            "reasons":          getattr(result, "failure_reasons", []),
            "warnings":         getattr(result, "warnings", []),
            "checks":           checks,
            "verified_at":      datetime.now(timezone.utc).isoformat(),
            "verifier_version": "1.1.0",
            "plane":            2,
            "authoritative":    True,
        })
    except Exception as exc:
        logger.exception("[ForensicAPI/verify] Result serialization error: %s", exc)
        return jsonify({"verdict": "INCOMPLETE", "error": "Result serialization error"}), 500


# ── POST /export (OEP Bundle Generation) ─────────────────────────────────────

@forensic_bp.route("/export", methods=["POST"])
def export_oep():
    """
    Generate and stream an OMNIX Evidence Package (.oep) ZIP bundle (ADR-165).
    Accepts JSON body: {blocks, public_key_b64, secret_key_b64?, custody_entries?}
    Returns: application/zip stream (Content-Disposition: attachment).
    OEP-INV-003: requires secret_key_b64 for package signature.
    """
    # ── Parse request ─────────────────────────────────────────────────────────
    try:
        if request.is_json:
            data = request.get_json(force=True, silent=True) or {}
        else:
            raw = request.form.to_dict()
            data = {}
            for key in ("blocks", "custody_entries"):
                if key in raw:
                    try:
                        data[key] = json.loads(raw[key])
                    except Exception:
                        data[key] = raw.get(key, [])
            data["public_key_b64"] = raw.get("public_key_b64")
            data["secret_key_b64"] = raw.get("secret_key_b64")

        blocks = data.get("blocks") or []
        public_key_b64 = data.get("public_key_b64")
        secret_key_b64 = data.get("secret_key_b64") or None
        custody_entries = data.get("custody_entries") or []

    except Exception as exc:
        logger.warning("[ForensicAPI/export] Request parse error: %s", exc)
        return jsonify({"error": "Request parse error", "verdict": "INCOMPLETE"}), 400

    # ── Validate required fields ──────────────────────────────────────────────
    if not blocks:
        return jsonify({"error": "Missing 'blocks' (at least one required)", "verdict": "INCOMPLETE"}), 400
    if not public_key_b64:
        return jsonify({"error": "Missing 'public_key_b64' (OEP-INV-001: key must be embedded)", "verdict": "INCOMPLETE"}), 400
    if not isinstance(blocks, list):
        return jsonify({"error": "'blocks' must be a JSON array", "verdict": "INCOMPLETE"}), 400

    # ── Generate OEP ─────────────────────────────────────────────────────────
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = OEPConfig(
                blocks=blocks,
                public_key_b64=public_key_b64,
                secret_key_b64=secret_key_b64,
                custody_log_entries=custody_entries,
                output_path=Path(tmp_dir),
            )
            generator = OEPGenerator(config)
            result = generator.generate()

            if not result.success:
                logger.error("[ForensicAPI/export] OEP generation failed: %s", result.errors)
                return jsonify({
                    "error": "OEP package generation failed",
                    "details": result.errors,
                    "verdict": "INCOMPLETE",
                }), 500

            # ── Read file into memory before temp dir is deleted ──────────────
            with open(result.oep_path, "rb") as f:
                oep_bytes = f.read()

    except Exception as exc:
        logger.exception("[ForensicAPI/export] OEP generation raised: %s", exc)
        return jsonify({
            "error": "Internal error during OEP generation",
            "verdict": "INCOMPLETE",
        }), 500

    # ── Stream response ────────────────────────────────────────────────────────
    buf = io.BytesIO(oep_bytes)
    download_name = f"OMNIX-PACKAGE-{result.package_id}.oep"
    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name=download_name,
    )
