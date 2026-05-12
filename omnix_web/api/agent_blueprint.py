"""
OMNIX Agent Trust Fabric — Flask API Blueprint
ADR-156: REST endpoints for agent identity, delegation, and verification.
ADR-157: Temporal Authority Admissibility endpoints.
ADR-158: Cross-Domain Trust Portability endpoints.

Endpoints (ADR-156 — Core ATF):
    POST  /api/atf/agents/register          — Register a new agent
    GET   /api/atf/agents                   — List agents (by domain)
    GET   /api/atf/agents/<agent_id>        — Get agent identity
    POST  /api/atf/delegate                 — Create delegation receipt
    GET   /api/atf/delegations/<agent_id>   — Get delegations for agent
    POST  /api/atf/verify                   — Verify a delegation chain
    GET   /api/atf/verify/<agent_id>        — Verify chain for agent
    GET   /api/atf/lattice                  — Full lattice state snapshot
    GET   /api/atf/ccs/<agent_id>           — ATF Chain Completeness Score
    POST  /api/atf/demo/simulate            — Demo: simulate multi-agent chain

Endpoints (ADR-157 — Temporal Authority):
    POST  /api/atf/temporal/admit           — Issue TAR for an execution event
    GET   /api/atf/temporal/<tar_id>        — Get a TAR by ID
    POST  /api/atf/temporal/verify          — Verify a TAR
    GET   /api/atf/temporal/report/<agent_id> — Temporal admissibility report

Endpoints (ADR-158 — Cross-Domain Trust Portability):
    POST  /api/atf/translate                — Issue a Domain Translation Receipt
    GET   /api/atf/translate/<dtr_id>       — Get a DTR by ID
    POST  /api/atf/translate/verify         — Verify a DTR
    GET   /api/atf/translate/policy         — Get discount for a domain pair

ADR-156/157/158 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

from flask import Blueprint, jsonify, request

logger = logging.getLogger("OMNIX.API.ATF")

atf_bp = Blueprint("atf", __name__)

_lattice = None

def _get_lattice():
    global _lattice
    if _lattice is None:
        from omnix_core.agents.atf.trust_lattice import TrustLattice
        _lattice = TrustLattice()
        try:
            _lattice.ensure_tables()
        except Exception as exc:
            logger.warning(f"[ATF.API] ensure_tables failed (non-blocking): {exc}")
    return _lattice


def _err(msg: str, code: int = 400):
    return jsonify({"error": msg, "status": "error"}), code


@atf_bp.route("/api/atf/agents/register", methods=["POST"])
def register_agent():
    """
    Register a new AI agent in the trust lattice.

    Body:
        display_name     (required)
        domain           (required)
        vertical         (optional, default "general")
        authority_budget (optional, default 50.0)
        registered_by    (optional, default "api")
        capabilities     (optional, list of strings)
        metadata         (optional, dict)
    """
    data = request.get_json(silent=True) or {}
    display_name = data.get("display_name", "").strip()
    domain = data.get("domain", "").strip()

    if not display_name:
        return _err("display_name is required")
    if not domain:
        return _err("domain is required")

    try:
        budget = float(data.get("authority_budget", 50.0))
    except (TypeError, ValueError):
        return _err("authority_budget must be a number between 0 and 100")

    try:
        lattice = _get_lattice()
        identity = lattice.register_agent(
            display_name=display_name,
            domain=domain,
            vertical=data.get("vertical", "general"),
            authority_budget=budget,
            registered_by=data.get("registered_by", "api"),
            registration_tier=int(data.get("registration_tier", 2)),
            capabilities=data.get("capabilities") or [],
            metadata=data.get("metadata") or {},
        )
        return jsonify({
            "status": "registered",
            "agent": identity.trust_summary(),
            "agent_id": identity.agent_id,
            "public_key_b64": identity.public_key_b64,
            "registered_at": identity.registered_at,
        }), 201
    except ValueError as exc:
        return _err(str(exc))
    except Exception as exc:
        logger.error(f"[ATF.API] register_agent error: {exc}")
        return _err(f"Registration failed: {exc}", 500)


@atf_bp.route("/api/atf/agents", methods=["GET"])
def list_agents():
    """List registered agents. Filter by domain via ?domain=FINANCE"""
    domain = request.args.get("domain")
    status = request.args.get("status", "ACTIVE")
    try:
        lattice = _get_lattice()
        agents = lattice._identity_engine.list_agents(domain=domain, status=status)
        return jsonify({
            "agents": [a.trust_summary() for a in agents],
            "total": len(agents),
            "filter_domain": domain,
            "filter_status": status,
        })
    except Exception as exc:
        logger.error(f"[ATF.API] list_agents error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/agents/<agent_id>", methods=["GET"])
def get_agent(agent_id: str):
    """Get agent identity by agent_id."""
    try:
        lattice = _get_lattice()
        identity = lattice._identity_engine.get_agent(agent_id)
        if identity is None:
            return _err(f"Agent not found: {agent_id}", 404)

        verification = lattice._identity_engine.verify_identity(identity)
        return jsonify({
            "agent": identity.trust_summary(),
            "capabilities": identity.capabilities,
            "vertical": identity.vertical,
            "registered_by": identity.registered_by,
            "registration_tier": identity.registration_tier,
            "registration_hash": identity.registration_hash,
            "pqc_algorithm": identity.pqc_algorithm,
            "verification": verification,
        })
    except Exception as exc:
        logger.error(f"[ATF.API] get_agent error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/delegate", methods=["POST"])
def create_delegation():
    """
    Create a PQC-signed delegation receipt.

    Body:
        delegator_id               (required)
        delegate_id                (required)
        task_scope                 (required, dict)
        authority_budget_delegator (required)
        authority_budget_granted   (required)
        parent_delegation_id       (optional)
        chain_root_id              (optional)
        delegation_depth           (optional, default 0)
        expires_at                 (optional, ISO UTC)
        metadata                   (optional)
    """
    data = request.get_json(silent=True) or {}

    required = ["delegator_id", "delegate_id", "task_scope",
                "authority_budget_delegator", "authority_budget_granted"]
    for f in required:
        if not data.get(f) and data.get(f) != 0:
            return _err(f"{f} is required")

    try:
        from omnix_core.agents.atf.delegation_receipt import AuthorityExpansionViolation
        lattice = _get_lattice()
        receipt = lattice.delegate(
            delegator_id=data["delegator_id"],
            delegate_id=data["delegate_id"],
            task_scope=data["task_scope"],
            authority_budget_delegator=float(data["authority_budget_delegator"]),
            authority_budget_granted=float(data["authority_budget_granted"]),
            parent_delegation_id=data.get("parent_delegation_id"),
            chain_root_id=data.get("chain_root_id"),
            delegation_depth=int(data.get("delegation_depth", 0)),
            expires_at=data.get("expires_at"),
            metadata=data.get("metadata") or {},
        )
        return jsonify({
            "status": "delegated",
            "delegation_receipt": receipt.trust_summary(),
            "delegation_id": receipt.delegation_id,
            "content_hash": receipt.content_hash,
            "pqc_signed": receipt.pqc_signature is not None,
            "pqc_algorithm": receipt.pqc_algorithm,
            "created_at": receipt.created_at,
        }), 201
    except AuthorityExpansionViolation as exc:
        return _err(f"ATF-INV-001: {exc}", 422)
    except (ValueError, TypeError) as exc:
        return _err(str(exc))
    except Exception as exc:
        logger.error(f"[ATF.API] create_delegation error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/delegations/<agent_id>", methods=["GET"])
def get_delegations(agent_id: str):
    """Get all delegation receipts for a given agent (as delegate)."""
    status = request.args.get("status", "ACTIVE")
    try:
        lattice = _get_lattice()
        delegations = lattice._delegation_engine.list_delegations(
            delegate_id=agent_id, status=status
        )
        return jsonify({
            "agent_id": agent_id,
            "delegations": [d.trust_summary() for d in delegations],
            "total": len(delegations),
        })
    except Exception as exc:
        logger.error(f"[ATF.API] get_delegations error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/verify/<agent_id>", methods=["GET"])
def verify_agent_chain(agent_id: str):
    """
    Verify the full delegation chain for an agent.
    Returns the complete VerificationResult including chain path.
    """
    try:
        lattice = _get_lattice()
        result = lattice.verify_chain(agent_id=agent_id)
        return jsonify({
            "verification": result.summary(),
            "chain": [n.to_dict() for n in result.chain],
            "failure_reason": result.failure_reason,
        })
    except Exception as exc:
        logger.error(f"[ATF.API] verify_agent_chain error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/verify", methods=["POST"])
def verify_receipt():
    """
    Verify a specific delegation receipt by ID, or by embedding the receipt dict.

    Body:
        delegation_id (optional) — look up by ID
        receipt       (optional) — provide the full receipt dict directly
    """
    data = request.get_json(silent=True) or {}

    try:
        from omnix_core.agents.atf.delegation_receipt import DelegationReceipt
        lattice = _get_lattice()

        if data.get("delegation_id"):
            dr = lattice._delegation_engine.get_delegation(data["delegation_id"])
            if dr is None:
                return _err(f"Delegation receipt not found: {data['delegation_id']}", 404)
        elif data.get("receipt"):
            r = data["receipt"]
            dr = DelegationReceipt(
                delegation_id=r.get("delegation_id", ""),
                delegator_id=r.get("delegator_id", ""),
                delegate_id=r.get("delegate_id", ""),
                task_scope=r.get("task_scope", {}),
                authority_budget_delegator=float(r.get("authority_budget_delegator", 0)),
                authority_budget_granted=float(r.get("authority_budget_granted", 0)),
                parent_delegation_id=r.get("parent_delegation_id"),
                chain_root_id=r.get("chain_root_id", ""),
                delegation_depth=int(r.get("delegation_depth", 0)),
                delegator_public_key=r.get("delegator_public_key", ""),
                content_hash=r.get("content_hash", ""),
                pqc_signature=r.get("pqc_signature"),
                pqc_algorithm=r.get("pqc_algorithm"),
                expires_at=r.get("expires_at"),
                status=r.get("status", "ACTIVE"),
                created_at=r.get("created_at", ""),
                metadata=r.get("metadata", {}),
            )
        else:
            return _err("Provide delegation_id or receipt dict")

        vr = lattice._delegation_engine.verify_receipt(dr)
        return jsonify({
            "verification": vr,
            "status": "verified" if vr["fully_verified"] else "invalid",
        })
    except Exception as exc:
        logger.error(f"[ATF.API] verify_receipt error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/lattice", methods=["GET"])
def get_lattice_state():
    """Get current trust lattice state: all agents and active delegations."""
    try:
        lattice = _get_lattice()
        state = lattice.get_lattice_state()
        return jsonify(state)
    except Exception as exc:
        logger.error(f"[ATF.API] get_lattice_state error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/ccs/<agent_id>", methods=["GET"])
def get_chain_completeness_score(agent_id: str):
    """
    ATF Chain Completeness Score for an agent's delegation chain.
    Analogous to CCS (ADR-155) but for the agent trust layer.
    """
    try:
        lattice = _get_lattice()
        ccs = lattice.chain_completeness_score(agent_id=agent_id)
        return jsonify(ccs)
    except Exception as exc:
        logger.error(f"[ATF.API] ccs error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/temporal/admit", methods=["POST"])
def temporal_admit():
    """
    ADR-157: Issue a Temporal Admissibility Record (TAR) for an execution event.

    The TAR proves that a Delegation Receipt was ACTIVE at the exact nanosecond
    of execution. TAR is issued synchronously at admission time (TAR-INV-001).

    Body:
        delegation_id     (required) — ATFDR-... to admit
        agent_id          (required) — AID of the acting agent
        task_action       (required) — action being performed
        execution_ref     (optional) — ExecutionReceipt ID (ADR-131)
        metadata          (optional)
    """
    data = request.get_json(silent=True) or {}

    delegation_id = (data.get("delegation_id") or "").strip()
    agent_id      = (data.get("agent_id") or "").strip()
    task_action   = (data.get("task_action") or "").strip()

    if not delegation_id:
        return _err("delegation_id is required")
    if not agent_id:
        return _err("agent_id is required")
    if not task_action:
        return _err("task_action is required")

    try:
        from omnix_core.agents.atf.temporal_authority import TemporalAuthorityEngine
        from omnix_core.agents.atf.delegation_receipt import DelegationReceipt

        engine = TemporalAuthorityEngine()
        engine.ensure_tables()

        lattice = _get_lattice()
        dr = lattice._delegation_engine.get_delegation(delegation_id)
        if dr is None:
            return _err(f"Delegation receipt not found: {delegation_id}", 404)

        tar = engine.admit_execution(
            delegation_receipt=dr,
            agent_id=agent_id,
            task_action=task_action,
            execution_ref=data.get("execution_ref"),
            metadata=data.get("metadata") or {},
        )

        code = 201 if tar.is_admitted() else 200
        return jsonify({
            "tar": tar.summary(),
            "tar_id": tar.tar_id,
            "admission_status": tar.admission_status,
            "execution_ns": tar.execution_ns,
            "execution_ts": tar.execution_ts,
            "pqc_signed": tar.pqc_signature is not None,
            "rejection_reason": tar.rejection_reason,
            "status": "admitted" if tar.is_admitted() else "rejected",
        }), code
    except Exception as exc:
        logger.error(f"[ATF.API] temporal_admit error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/temporal/<tar_id>", methods=["GET"])
def get_tar(tar_id: str):
    """ADR-157: Get a Temporal Admissibility Record by ID."""
    try:
        from omnix_core.agents.atf.temporal_authority import TemporalAuthorityEngine
        engine = TemporalAuthorityEngine()
        tar = engine.get_tar(tar_id)
        if tar is None:
            return _err(f"TAR not found: {tar_id}", 404)
        return jsonify({
            "tar": tar.to_dict(),
            "admitted": tar.is_admitted(),
        })
    except Exception as exc:
        logger.error(f"[ATF.API] get_tar error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/temporal/verify", methods=["POST"])
def verify_tar():
    """
    ADR-157: Verify a Temporal Admissibility Record.

    Body:
        tar_id  (optional) — look up by ID
        tar     (optional) — embed the full TAR dict
    """
    data = request.get_json(silent=True) or {}
    try:
        from omnix_core.agents.atf.temporal_authority import (
            TemporalAuthorityEngine, TemporalAdmissibilityRecord
        )
        engine = TemporalAuthorityEngine()

        if data.get("tar_id"):
            tar = engine.get_tar(data["tar_id"])
            if tar is None:
                return _err(f"TAR not found: {data['tar_id']}", 404)
        elif data.get("tar"):
            t = data["tar"]
            tar = TemporalAdmissibilityRecord(
                tar_id=t.get("tar_id", ""),
                delegation_id=t.get("delegation_id", ""),
                agent_id=t.get("agent_id", ""),
                execution_ref=t.get("execution_ref"),
                execution_ns=int(t.get("execution_ns", 0)),
                execution_ts=t.get("execution_ts", ""),
                dr_status_at_admission=t.get("dr_status_at_admission", ""),
                dr_expires_at=t.get("dr_expires_at"),
                authority_budget=float(t.get("authority_budget", 0)),
                domain=t.get("domain", ""),
                task_action=t.get("task_action", ""),
                admission_status=t.get("admission_status", ""),
                rejection_reason=t.get("rejection_reason"),
                content_hash=t.get("content_hash", ""),
                pqc_signature=t.get("pqc_signature"),
                pqc_algorithm=t.get("pqc_algorithm"),
                chain_root_id=t.get("chain_root_id", ""),
                issued_at=t.get("issued_at", ""),
                metadata=t.get("metadata", {}),
            )
        else:
            return _err("Provide tar_id or tar dict")

        result = engine.verify_tar(tar)
        return jsonify({
            "verification": result,
            "status": "verified" if result["fully_verified"] else "invalid",
        })
    except Exception as exc:
        logger.error(f"[ATF.API] verify_tar error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/temporal/report/<agent_id>", methods=["GET"])
def temporal_report(agent_id: str):
    """ADR-157: Temporal admissibility summary report for an agent."""
    try:
        from omnix_core.agents.atf.temporal_authority import TemporalAuthorityEngine
        engine = TemporalAuthorityEngine()
        report = engine.temporal_admissibility_report(agent_id)
        return jsonify(report)
    except Exception as exc:
        logger.error(f"[ATF.API] temporal_report error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/translate", methods=["POST"])
def create_domain_translation():
    """
    ADR-158: Issue a Domain Translation Receipt (DTR) for cross-domain authority.

    Body:
        source_delegation_id  (required) — ATFDR-... in source domain
        source_agent_id       (required) — AID in source domain
        target_agent_id       (required) — AID in target domain
        target_domain         (required) — target governance domain
        target_task_scope     (required) — authorized scope in target domain
        issued_by             (optional) — issuer identifier
        expires_at            (optional) — ISO UTC expiry
        metadata              (optional)
    """
    data = request.get_json(silent=True) or {}

    for f in ["source_delegation_id", "source_agent_id", "target_agent_id",
              "target_domain", "target_task_scope"]:
        if not data.get(f):
            return _err(f"{f} is required")

    try:
        from omnix_core.agents.atf.domain_bridge import CrossDomainBridge, CrossDomainAuthorityError

        bridge = CrossDomainBridge()
        bridge.ensure_tables()

        lattice = _get_lattice()
        dr = lattice._delegation_engine.get_delegation(data["source_delegation_id"])
        if dr is None:
            return _err(f"Source delegation not found: {data['source_delegation_id']}", 404)

        dtr = bridge.translate(
            source_delegation=dr,
            source_agent_id=data["source_agent_id"],
            target_agent_id=data["target_agent_id"],
            target_domain=data["target_domain"],
            target_task_scope=data["target_task_scope"],
            issued_by=data.get("issued_by", "api"),
            expires_at=data.get("expires_at"),
            metadata=data.get("metadata") or {},
        )

        return jsonify({
            "status": "translated",
            "dtr": dtr.trust_summary(),
            "dtr_id": dtr.dtr_id,
            "source_domain": dtr.source_domain,
            "target_domain": dtr.target_domain,
            "source_budget": dtr.source_authority_budget,
            "translated_budget": dtr.translated_budget,
            "translation_discount": f"{dtr.translation_discount*100:.0f}%",
            "translation_policy": dtr.translation_policy,
            "pqc_signed": dtr.pqc_signature is not None,
            "issued_at": dtr.issued_at,
        }), 201
    except CrossDomainAuthorityError as exc:
        return _err(f"CDTP-INV-001: {exc}", 422)
    except Exception as exc:
        logger.error(f"[ATF.API] create_domain_translation error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/translate/<dtr_id>", methods=["GET"])
def get_dtr(dtr_id: str):
    """ADR-158: Get a Domain Translation Receipt by ID."""
    try:
        from omnix_core.agents.atf.domain_bridge import CrossDomainBridge
        bridge = CrossDomainBridge()
        dtr = bridge.get_dtr(dtr_id)
        if dtr is None:
            return _err(f"DTR not found: {dtr_id}", 404)
        return jsonify({
            "dtr": dtr.to_dict(),
            "trust_summary": dtr.trust_summary(),
        })
    except Exception as exc:
        logger.error(f"[ATF.API] get_dtr error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/translate/verify", methods=["POST"])
def verify_dtr():
    """
    ADR-158: Verify a Domain Translation Receipt.

    Body:
        dtr_id  (optional) — look up by ID
        dtr     (optional) — embed the full DTR dict
    """
    data = request.get_json(silent=True) or {}
    try:
        from omnix_core.agents.atf.domain_bridge import CrossDomainBridge, DomainTranslationReceipt
        bridge = CrossDomainBridge()

        if data.get("dtr_id"):
            dtr = bridge.get_dtr(data["dtr_id"])
            if dtr is None:
                return _err(f"DTR not found: {data['dtr_id']}", 404)
        elif data.get("dtr"):
            d = data["dtr"]
            dtr = DomainTranslationReceipt(
                dtr_id=d.get("dtr_id", ""),
                source_delegation_id=d.get("source_delegation_id", ""),
                source_domain=d.get("source_domain", ""),
                target_domain=d.get("target_domain", ""),
                source_agent_id=d.get("source_agent_id", ""),
                target_agent_id=d.get("target_agent_id", ""),
                source_authority_budget=float(d.get("source_authority_budget", 0)),
                translated_budget=float(d.get("translated_budget", 0)),
                translation_discount=float(d.get("translation_discount", 0.20)),
                translation_policy=d.get("translation_policy", ""),
                task_scope=d.get("task_scope", {}),
                chain_root_id=d.get("chain_root_id", ""),
                content_hash=d.get("content_hash", ""),
                pqc_signature=d.get("pqc_signature"),
                pqc_algorithm=d.get("pqc_algorithm"),
                status=d.get("status", "ACTIVE"),
                expires_at=d.get("expires_at"),
                issued_at=d.get("issued_at", ""),
                issued_by=d.get("issued_by", ""),
                metadata=d.get("metadata", {}),
            )
        else:
            return _err("Provide dtr_id or dtr dict")

        result = bridge.verify_dtr(dtr)
        return jsonify({
            "verification": result,
            "status": "verified" if result["fully_verified"] else "invalid",
        })
    except Exception as exc:
        logger.error(f"[ATF.API] verify_dtr error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/translate/policy", methods=["GET"])
def get_translation_policy():
    """
    ADR-158: Get translation discount policy for a domain pair.

    Query params:
        source  (required) — source domain (e.g. FINANCE)
        target  (required) — target domain (e.g. HEALTHCARE)
    """
    source = (request.args.get("source") or "").strip().upper()
    target = (request.args.get("target") or "").strip().upper()

    if not source or not target:
        return _err("source and target domain parameters are required")

    try:
        from omnix_core.agents.atf.domain_bridge import CrossDomainBridge
        bridge = CrossDomainBridge()
        discount, policy_id = bridge.get_policy(source, target)
        return jsonify({
            "source_domain": source,
            "target_domain": target,
            "translation_discount": discount,
            "translation_discount_pct": f"{discount*100:.0f}%",
            "translation_policy": policy_id,
            "max_translated_from_100": round(100.0 * (1.0 - discount), 2),
            "note": "Authority is always reduced by at least this % at domain crossing",
        })
    except Exception as exc:
        logger.error(f"[ATF.API] get_translation_policy error: {exc}")
        return _err(str(exc), 500)


@atf_bp.route("/api/atf/demo/simulate", methods=["POST"])
def simulate_chain():
    """
    Demo: simulate a realistic multi-agent delegation chain.
    Creates: Human → Orchestrator → Analysis Agent → Data Agent
    Returns the full lattice state and chain verification result.

    Accepts optional body:
        domain (default "FINANCE")
        depth  (1, 2, or 3 levels, default 3)
    """
    data = request.get_json(silent=True) or {}
    domain = data.get("domain", "FINANCE").upper()
    depth = min(int(data.get("depth", 3)), 3)

    try:
        from omnix_core.agents.atf.trust_lattice import TrustLattice
        sim_lattice = TrustLattice()

        agents_created = []
        delegations_created = []

        orchestrator = sim_lattice.register_agent(
            display_name="Orchestrator Agent",
            domain=domain,
            vertical="orchestration",
            authority_budget=80.0,
            registered_by="HUMAN-TIER1-DEMO",
            registration_tier=1,
            capabilities=["orchestrate", "delegate", "monitor"],
        )
        agents_created.append(orchestrator.trust_summary())

        root_dr = sim_lattice.delegate(
            delegator_id="HUMAN-TIER1-DEMO",
            delegate_id=orchestrator.agent_id,
            task_scope={
                "action": "orchestrate_governance_pipeline",
                "domain": domain,
                "constraints": ["no_external_calls", "audit_all_decisions"],
            },
            authority_budget_delegator=100.0,
            authority_budget_granted=80.0,
            delegation_depth=1,
        )
        delegations_created.append(root_dr.trust_summary())

        chain_root_id = root_dr.delegation_id
        leaf_agent = orchestrator
        parent_dr = root_dr

        if depth >= 2:
            analysis_agent = sim_lattice.register_agent(
                display_name="Analysis Agent",
                domain=domain,
                vertical="analysis",
                authority_budget=55.0,
                registered_by=orchestrator.agent_id,
                registration_tier=2,
                capabilities=["read_signals", "compute_risk", "produce_report"],
            )
            agents_created.append(analysis_agent.trust_summary())

            analysis_dr = sim_lattice.delegate(
                delegator_id=orchestrator.agent_id,
                delegate_id=analysis_agent.agent_id,
                task_scope={
                    "action": "analyze_market_signals",
                    "domain": domain,
                    "constraints": ["read_only", "no_trading"],
                },
                authority_budget_delegator=80.0,
                authority_budget_granted=55.0,
                parent_delegation_id=root_dr.delegation_id,
                chain_root_id=chain_root_id,
                delegation_depth=2,
            )
            delegations_created.append(analysis_dr.trust_summary())
            leaf_agent = analysis_agent
            parent_dr = analysis_dr

        if depth >= 3:
            data_agent = sim_lattice.register_agent(
                display_name="Data Retrieval Agent",
                domain=domain,
                vertical="data",
                authority_budget=25.0,
                registered_by=leaf_agent.agent_id,
                registration_tier=2,
                capabilities=["fetch_price_data", "fetch_risk_metrics"],
            )
            agents_created.append(data_agent.trust_summary())

            data_dr = sim_lattice.delegate(
                delegator_id=leaf_agent.agent_id,
                delegate_id=data_agent.agent_id,
                task_scope={
                    "action": "fetch_market_data",
                    "domain": domain,
                    "constraints": ["read_only", "approved_sources_only"],
                },
                authority_budget_delegator=55.0,
                authority_budget_granted=25.0,
                parent_delegation_id=parent_dr.delegation_id,
                chain_root_id=chain_root_id,
                delegation_depth=3,
            )
            delegations_created.append(data_dr.trust_summary())
            leaf_agent = data_agent

        verification = sim_lattice.verify_chain(agent_id=leaf_agent.agent_id)
        ccs = sim_lattice.chain_completeness_score(agent_id=leaf_agent.agent_id)

        return jsonify({
            "simulation": {
                "domain": domain,
                "depth_simulated": depth,
                "agents_created": agents_created,
                "delegations_created": delegations_created,
            },
            "verification": verification.summary(),
            "chain": [n.to_dict() for n in verification.chain],
            "ccs": ccs,
            "leaf_agent_id": leaf_agent.agent_id,
            "chain_root_id": chain_root_id,
            "simulated_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as exc:
        logger.error(f"[ATF.API] simulate_chain error: {exc}")
        return _err(str(exc), 500)
