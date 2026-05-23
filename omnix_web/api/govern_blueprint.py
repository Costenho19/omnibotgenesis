"""
OMNIX Governance Runtime — Flask API Blueprint
ADR-184 · RFC-ATF-1 through RFC-ATF-6

The single integration endpoint for the full 6-layer Agent Trust Fabric.
One session. All invariants. ATF-BEV-Compliant by default.

Endpoints:
    POST /v1/govern/session/start           — Initialize a governed session
    POST /v1/govern/session/<id>/turn       — Record one agent turn (BAR+CCS+CTCHC)
    GET  /v1/govern/session/<id>/proof      — Behavioral Attestation Chain
    POST /v1/govern/session/<id>/close      — Seal CTCHC + close session
    GET  /v1/govern/session/<id>/status     — Full governance status
    GET  /v1/govern/sessions                — List sessions for an agent
    POST /v1/govern/verify                  — Offline artifact verification
    GET  /v1/govern/compliance/<id>         — ATF-BEV-Compliant report

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

from flask import Blueprint, jsonify, request

logger = logging.getLogger("OMNIX.API.OGR")

ogr_bp = Blueprint("ogr", __name__)

_runtime = None


def _get_runtime():
    global _runtime
    if _runtime is None:
        from omnix_core.govern.governance_runtime import GovernanceRuntime
        _runtime = GovernanceRuntime()
        try:
            _runtime.ensure_tables()
        except Exception as exc:
            logger.warning(f"[OGR.API] ensure_tables failed (non-blocking): {exc}")
    return _runtime


def _err(msg: str, code: int = 400):
    return jsonify({"error": msg, "status": "error"}), code


# ─────────────────────────────────────────────────────────────────
#  1. START SESSION
# ─────────────────────────────────────────────────────────────────

@ogr_bp.route("/v1/govern/session/start", methods=["POST"])
def start_session():
    """
    Initialize a fully governed session.

    Activates all 6 ATF layers simultaneously and creates the CTCHC genesis
    block. Every subsequent turn will be bound to the governing_receipt_id
    provided here.

    Body:
        agent_id               (required)
        governing_receipt_id   (required) — must reference a valid decision receipt
        domain                 (optional, default "general")
        vertical               (optional, default "general")
        policy_name            (optional, default "default")
        constraint_set         (optional, dict) — policy constraints for the session
        metadata               (optional, dict)

    Constraint set fields (all optional):
        max_output_length     (int) — max chars per turn output
        max_turns             (int) — session turn limit
        halt_on_keywords      (list[str]) — keywords that halt the session
        warn_on_keywords      (list[str]) — keywords that trigger WARNING
        forbidden_topics      (list[str]) — topics that violate conformance
        required_keywords     (list[str]) — at least one must appear each turn
    """
    data = request.get_json(silent=True) or {}

    agent_id = (data.get("agent_id") or "").strip()
    governing_receipt_id = (data.get("governing_receipt_id") or "").strip()

    if not agent_id:
        return _err("agent_id is required")
    if not governing_receipt_id:
        return _err("governing_receipt_id is required")

    try:
        runtime = _get_runtime()
        session = runtime.start_session(
            agent_id=agent_id,
            governing_receipt_id=governing_receipt_id,
            domain=data.get("domain", "general"),
            vertical=data.get("vertical", "general"),
            policy_name=data.get("policy_name", "default"),
            constraint_set=data.get("constraint_set") or {},
            metadata=data.get("metadata") or {},
        )
        return jsonify({
            "status": "session_started",
            "session_id": session.session_id,
            "governing_receipt_id": session.governing_receipt_id,
            "chain_genesis_hash": session.chain_genesis_hash,
            "chain_id": session.chain_id,
            "compliance_tier": session.compliance_tier,
            "atf_layers_active": session.atf_layers_active,
            "session": session.governance_summary(),
            "ogr_version": "1.0.0",
        }), 201
    except ValueError as exc:
        return _err(str(exc))
    except Exception as exc:
        logger.error(f"[OGR.API] start_session error: {exc}")
        return _err(f"Failed to start session: {exc}", 500)


# ─────────────────────────────────────────────────────────────────
#  2. RECORD TURN
# ─────────────────────────────────────────────────────────────────

@ogr_bp.route("/v1/govern/session/<session_id>/turn", methods=["POST"])
def record_turn(session_id: str):
    """
    Record one agent output turn through all active ATF layers.

    Atomically produces:
      • BAR — PQC-signed behavioral anchor record (ADR-181)
      • CCS — constraint conformance signal (ADR-182)
      • CTCHC link — coherence hash chain extension (ADR-183)

    Returns the OGR verdict immediately. If should_halt=true, the agent
    MUST stop and must not deliver the output.

    Body:
        output_text    (required) — the agent's output for this turn
        metadata       (optional, dict)
    """
    data = request.get_json(silent=True) or {}
    output_text = data.get("output_text")

    if output_text is None:
        return _err("output_text is required")
    if not isinstance(output_text, str):
        return _err("output_text must be a string")

    try:
        runtime = _get_runtime()
        result = runtime.record_turn(
            session_id=session_id,
            output_text=output_text,
            turn_metadata=data.get("metadata") or {},
        )
        response = result.to_dict()
        response["status"] = "turn_recorded"

        http_code = 200
        if result.should_halt:
            response["status"] = "turn_halted"
            http_code = 200

        return jsonify(response), http_code
    except ValueError as exc:
        return _err(str(exc))
    except Exception as exc:
        logger.error(f"[OGR.API] record_turn error: {exc}")
        return _err(f"Failed to record turn: {exc}", 500)


# ─────────────────────────────────────────────────────────────────
#  3. GET PROOF
# ─────────────────────────────────────────────────────────────────

@ogr_bp.route("/v1/govern/session/<session_id>/proof", methods=["GET"])
def get_proof(session_id: str):
    """
    Retrieve the complete Behavioral Attestation Chain for a session.

    The proof contains:
      • All BAR records (per-turn behavioral attestations)
      • CCS trend (session conformance history)
      • CTCHC chain with seal
      • Offline verification result

    This proof is sufficient for regulatory submission and third-party
    governance audit without requiring further OMNIX access.
    """
    try:
        runtime = _get_runtime()
        proof = runtime.get_proof(session_id)
        return jsonify({
            "status": "proof_retrieved",
            **proof,
        })
    except ValueError as exc:
        return _err(str(exc), 404)
    except Exception as exc:
        logger.error(f"[OGR.API] get_proof error: {exc}")
        return _err(f"Failed to retrieve proof: {exc}", 500)


# ─────────────────────────────────────────────────────────────────
#  4. CLOSE SESSION
# ─────────────────────────────────────────────────────────────────

@ogr_bp.route("/v1/govern/session/<session_id>/close", methods=["POST"])
def close_session(session_id: str):
    """
    Seal the CTCHC and close the governed session.

    After closing:
      • The coherence hash chain is PQC-sealed (BEV-INV-013/014)
      • The session is immutable
      • The proof is offline-verifiable

    Body:
        package_oep    (optional, bool, default false) — include OEP export note
    """
    data = request.get_json(silent=True) or {}
    package_oep = bool(data.get("package_oep", False))

    try:
        runtime = _get_runtime()
        result = runtime.close_session(session_id, package_oep=package_oep)
        result["status"] = "session_closed"
        return jsonify(result)
    except ValueError as exc:
        return _err(str(exc))
    except Exception as exc:
        logger.error(f"[OGR.API] close_session error: {exc}")
        return _err(f"Failed to close session: {exc}", 500)


# ─────────────────────────────────────────────────────────────────
#  5. GET STATUS
# ─────────────────────────────────────────────────────────────────

@ogr_bp.route("/v1/govern/session/<session_id>/status", methods=["GET"])
def get_status(session_id: str):
    """
    Full governance status dashboard for a session.

    Returns live CCS trend, chain state, compliance tier, and active layers.
    """
    try:
        runtime = _get_runtime()
        status = runtime.get_status(session_id)
        return jsonify({
            "status": "ok",
            **status,
        })
    except ValueError as exc:
        return _err(str(exc), 404)
    except Exception as exc:
        logger.error(f"[OGR.API] get_status error: {exc}")
        return _err(f"Failed to get status: {exc}", 500)


# ─────────────────────────────────────────────────────────────────
#  6. LIST SESSIONS
# ─────────────────────────────────────────────────────────────────

@ogr_bp.route("/v1/govern/sessions", methods=["GET"])
def list_sessions():
    """
    List governed sessions.

    Query params:
        agent_id  (optional) — filter by agent
        status    (optional) — ACTIVE | CLOSED | HALTED | EXPIRED
        limit     (optional, default 50)
    """
    agent_id = request.args.get("agent_id")
    status = request.args.get("status")
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
    except (TypeError, ValueError):
        limit = 50

    try:
        runtime = _get_runtime()
        sessions = runtime.list_sessions(agent_id=agent_id, status=status, limit=limit)
        return jsonify({
            "status": "ok",
            "sessions": [s.governance_summary() for s in sessions],
            "total": len(sessions),
            "filter_agent_id": agent_id,
            "filter_status": status,
        })
    except Exception as exc:
        logger.error(f"[OGR.API] list_sessions error: {exc}")
        return _err(f"Failed to list sessions: {exc}", 500)


# ─────────────────────────────────────────────────────────────────
#  7. VERIFY ARTIFACT
# ─────────────────────────────────────────────────────────────────

@ogr_bp.route("/v1/govern/verify", methods=["POST"])
def verify_artifact():
    """
    Offline verification of any OGR artifact.

    Accepts BAR, CTCHC chain, or full SESSION — verifies all embedded
    cryptographic proofs without requiring further database access when
    artifact_data is provided directly.

    Body:
        artifact_type   (required) — "BAR" | "CTCHC" | "SESSION"
        artifact_id     (required) — the artifact's primary key
        artifact_data   (optional) — embedded artifact for fully offline use
    """
    data = request.get_json(silent=True) or {}
    artifact_type = (data.get("artifact_type") or "").strip()
    artifact_id = (data.get("artifact_id") or "").strip()

    if not artifact_type:
        return _err("artifact_type is required (BAR | CTCHC | SESSION)")
    if not artifact_id:
        return _err("artifact_id is required")

    try:
        runtime = _get_runtime()
        result = runtime.verify_artifact(
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            artifact_data=data.get("artifact_data"),
        )
        return jsonify({
            "status": "verified" if result.get("verified") else "invalid",
            **result,
        })
    except Exception as exc:
        logger.error(f"[OGR.API] verify_artifact error: {exc}")
        return _err(f"Verification failed: {exc}", 500)


# ─────────────────────────────────────────────────────────────────
#  8. COMPLIANCE REPORT
# ─────────────────────────────────────────────────────────────────

@ogr_bp.route("/v1/govern/compliance/<session_id>", methods=["GET"])
def compliance_report(session_id: str):
    """
    Generate an ATF-BEV-Compliant governance compliance report.

    This report documents:
      • All 6 ATF layers attested
      • Behavioral attestation statistics (BAR)
      • Conformance trend (CCS)
      • Chain integrity proof (CTCHC)
      • Per-invariant pass/fail for BEV-INV-001 through BEV-INV-014

    Suitable for regulatory submission, partner due diligence,
    and third-party governance audit.
    """
    try:
        runtime = _get_runtime()
        report = runtime.compliance_report(session_id)
        return jsonify({
            "status": "report_generated",
            **report,
        })
    except ValueError as exc:
        return _err(str(exc), 404)
    except Exception as exc:
        logger.error(f"[OGR.API] compliance_report error: {exc}")
        return _err(f"Failed to generate report: {exc}", 500)


# ─────────────────────────────────────────────────────────────────
#  9. OGR CAPABILITY MANIFEST
# ─────────────────────────────────────────────────────────────────

@ogr_bp.route("/v1/govern/manifest", methods=["GET"])
def manifest():
    """
    OGR capability manifest — what this integration provides and how.

    Machine-readable description of all active ATF layers, invariants,
    PQC algorithm, and compliance tiers. Use this to auto-configure
    integrations that need to know what governance is in effect.
    """
    return jsonify({
        "product": "OMNIX Governance Runtime",
        "version": "1.0.0",
        "issuer": "OMNIX QUANTUM LTD",
        "compliance_tier": "ATF-BEV-Compliant",
        "atf_layers": {
            "L1": {
                "name": "Identity",
                "artifact": "AIR",
                "rfc": "RFC-ATF-1",
                "pqc_signed": True,
            },
            "L2": {
                "name": "Delegation",
                "artifact": "DR",
                "rfc": "RFC-ATF-1",
                "pqc_signed": True,
            },
            "L3": {
                "name": "Temporal Authority",
                "artifact": "TAR",
                "rfc": "RFC-ATF-2",
                "pqc_signed": True,
            },
            "L4": {
                "name": "Runtime Continuity",
                "artifact": "RCR",
                "rfc": "RFC-ATF-2",
                "pqc_signed": True,
            },
            "L5": {
                "name": "Cognitive Governance",
                "artifacts": ["CGE", "GUGT", "TGB"],
                "rfc": "RFC-ATF-5",
                "pqc_signed": True,
            },
            "L6": {
                "name": "Behavioral Execution Verification",
                "artifacts": ["BAR", "CCS", "CTCHC"],
                "rfc": "RFC-ATF-6",
                "pqc_signed": True,
                "invariants": [
                    "BEV-INV-001", "BEV-INV-002", "BEV-INV-003", "BEV-INV-004",
                    "BEV-INV-005", "BEV-INV-006", "BEV-INV-007", "BEV-INV-008",
                    "BEV-INV-009", "BEV-INV-010", "BEV-INV-011", "BEV-INV-012",
                    "BEV-INV-013", "BEV-INV-014", "BEV-INV-015", "BEV-INV-016",
                    "BEV-INV-017", "BEV-INV-018",
                ],
            },
        },
        "ogr_invariants": {
            "OGR-INV-001": (
                "A governed session MUST activate all 6 ATF layers simultaneously "
                "— partial activation is not permitted."
            ),
        },
        "pqc": {
            "algorithm": "ML-DSA-65",
            "standard": "FIPS 204",
            "common_name": "Dilithium-3",
            "offline_verifiable": True,
        },
        "differentiators": [
            "Receipt-bound behavioral attestation — every turn artifact is "
            "cryptographically bound to the receipt that authorized the action",
            "Post-quantum cryptographic sealing on every artifact (ML-DSA-65)",
            "Six-layer simultaneous activation — no competitor activates all six",
            "Anticipatory governance — CCS feeds AGVP for proactive veto issuance",
            "Offline-verifiable session proof — no OMNIX access needed post-close",
            "Chain coherence proof — tamper-evident turn sequence linked to receipt",
        ],
        "total_invariants": 106,
        "bev_invariants": 18,
        "ogr_invariants_count": 1,
        "endpoints": [
            "POST /v1/govern/session/start",
            "POST /v1/govern/session/{id}/turn",
            "GET  /v1/govern/session/{id}/proof",
            "POST /v1/govern/session/{id}/close",
            "GET  /v1/govern/session/{id}/status",
            "GET  /v1/govern/sessions",
            "POST /v1/govern/verify",
            "GET  /v1/govern/compliance/{id}",
            "GET  /v1/govern/manifest",
        ],
    })
