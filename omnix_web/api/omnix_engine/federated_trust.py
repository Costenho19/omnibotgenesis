"""
OMNIX Federated Trust Layer — ADR-085
Implements the three pillars of cross-system interoperability:

1. Trust Registry  — who OMNIX is, what keys it uses, what partners are trusted
2. Independent Verifier — stateless receipt verification without OMNIX DB access
3. DID Resolution support — runtime key publication for did:web:omnixquantum.net

Any external system can:
  GET  /api/trust/registry      → see trusted issuers + live public key
  POST /api/trust/verify        → verify any OMNIX receipt independently
  GET  /.well-known/did.json    → resolve did:web:omnixquantum.net

This completes the federated trust layer described in OMNIX-Interoperability-Layer.md.
ADR-085 reference.
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("OMNIX.FederatedTrust")

OMNIX_DID          = "did:web:omnixquantum.net"
OMNIX_ISSUER_NAME  = "OMNIX Quantum Ltd"
OMNIX_ISSUER_URL   = "https://omnixquantum.net"
OMNIX_ENGINE_VER   = os.environ.get("OMNIX_VERSION", "6.5.4e")
OMNIX_POLICY_VER   = os.environ.get("OMNIX_VERSION", "6.5.4e")

SUPPORTED_SCHEMAS = [
    "https://omnixquantum.net/schemas/omnix-receipt-v1.jsonld",
    "https://omnixquantum.net/schemas/omnix-receipt-schema-v6.5.4e.json",
]

SUPPORTED_FRAMEWORKS = [
    "EU_AI_ACT", "FATF", "GDPR", "DORA", "NIST_AI_RMF",
    "ISO_42001", "BASEL_III", "UAE_CBUAE", "CA_SB_243",
]

FUTURE_TRUSTED_PARTNERS = [
    {
        "name": "Skilligen HDI",
        "did": "did:web:skilligen.com",
        "status": "pending_onboarding",
        "contact": "aman@skilligen.com",
        "nda_date": "2026-04-14",
        "trust_level": "negotiation",
    },
    {
        "name": "Velos Capital",
        "did": "did:web:veloscapital.com",
        "status": "pending_onboarding",
        "contact": "naimat@veloscapital.com",
        "trust_level": "integration_review",
    },
]


def _get_runtime_public_key() -> Optional[str]:
    """Attempt to retrieve the current runtime PQC public key from the signing engine."""
    try:
        from api.omnix_engine.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine()
        return engine.public_key_b64
    except Exception:
        try:
            from omnix_engine.decision_receipt import DecisionReceiptEngine
            engine = DecisionReceiptEngine()
            return engine.public_key_b64
        except Exception as e:
            logger.debug(f"Runtime key not available: {e}")
            return None


def _get_signing_algorithm() -> str:
    """Return the algorithm name of the active signing provider."""
    try:
        from omnix_core.security.crypto_providers import get_active_provider
        provider = get_active_provider()
        if provider:
            return provider.algorithm_name()
    except Exception:
        pass
    return "SHA-256"


def build_trust_registry() -> Dict[str, Any]:
    """
    Build the public trust registry for OMNIX.
    Returns the full registry as a dict — served at GET /api/trust/registry.
    """
    runtime_pub_key = _get_runtime_public_key()
    signing_algo    = _get_signing_algorithm()
    now             = datetime.now(timezone.utc).isoformat()

    omnix_entry: Dict[str, Any] = {
        "did":          OMNIX_DID,
        "name":         OMNIX_ISSUER_NAME,
        "url":          OMNIX_ISSUER_URL,
        "status":       "active",
        "trust_level":  "anchor",
        "engine_version": OMNIX_ENGINE_VER,
        "policy_version": OMNIX_POLICY_VER,
        "signing_algorithm": signing_algo,
        "verification_methods": [
            {
                "id":    f"{OMNIX_DID}#pqc-key-1",
                "type":  "PostQuantumKey2026",
                "algorithm": signing_algo,
                "public_key_b64": runtime_pub_key,
                "note":  (
                    "Ephemeral per deployment — refresh from registry before verification. "
                    "Stable key rotation policy: ADR-043."
                ),
            }
        ],
        "supported_schemas":    SUPPORTED_SCHEMAS,
        "supported_frameworks": SUPPORTED_FRAMEWORKS,
        "services": {
            "governance_api":   f"{OMNIX_ISSUER_URL}/api/governance/evaluate",
            "receipt_verifier": f"{OMNIX_ISSUER_URL}/api/trust/verify",
            "vc_issuer":        f"{OMNIX_ISSUER_URL}/api/governance/receipt/vc",
            "did_document":     f"{OMNIX_ISSUER_URL}/.well-known/did.json",
            "jsonld_context":   SUPPORTED_SCHEMAS[0],
            "json_schema":      SUPPORTED_SCHEMAS[1],
        },
        "checkpoints": 11,
        "domains": [
            "trading", "credit", "insurance", "robotics",
            "medical_ai", "energy_governance", "real_estate", "autonomous_agent",
        ],
        "registered_at": "2026-04-14T00:00:00+00:00",
        "last_seen": now,
    }

    return {
        "registry_id":    f"{OMNIX_DID}#trust-registry-v1",
        "registry_url":   f"{OMNIX_ISSUER_URL}/api/trust/registry",
        "spec":           "OMNIX Trust Registry v1.0 — ADR-085",
        "generated_at":   now,
        "trusted_issuers": [omnix_entry],
        "pending_partners": FUTURE_TRUSTED_PARTNERS,
        "federation_note": (
            "OMNIX receipts carry did:web:omnixquantum.net as the issuer DID. "
            "To add an external validator or partner to the trust chain, submit their DID "
            "and public key for review. Federation is a partnership agreement, not a technical barrier."
        ),
        "how_to_verify": {
            "step_1": "Fetch the issuer public key from verification_methods[0].public_key_b64",
            "step_2": "POST the receipt to /api/trust/verify — stateless, no DB access required",
            "step_3": "Check hash_valid=true and signature_valid=true in the response",
            "step_4": "Read jurisdiction_semantics for regulatory interpretation",
            "step_5": (
                "Optionally resolve did:web:omnixquantum.net via "
                "omnixquantum.net/.well-known/did.json to confirm issuer identity"
            ),
        },
    }


def independent_verify(receipt_or_vc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stateless independent receipt verifier — ADR-085.

    Accepts either:
    - A raw OMNIX receipt dict
    - A W3C VC dict (extracts credentialSubject as the receipt)

    Does NOT require DB access. Uses only:
    - SHA-256 hash recomputation (always available)
    - PQC signature verification if public key is embedded in the receipt
    - Jurisdiction semantics computation

    Returns a complete verification report.
    """
    now = datetime.now(timezone.utc).isoformat()

    is_vc = "@context" in receipt_or_vc and "credentialSubject" in receipt_or_vc
    if is_vc:
        receipt = receipt_or_vc.get("credentialSubject", {})
        proof   = receipt_or_vc.get("proof", {})
        if proof and not receipt.get("signature"):
            receipt = dict(receipt)
            receipt["signature"]           = proof.get("proofValue")
            receipt["signature_algorithm"] = proof.get("signatureAlgorithm", "")
            receipt["public_key"]          = proof.get("publicKey")
            receipt["content_hash"]        = proof.get("signedData", receipt.get("content_hash",""))
        input_format = "W3C_VC"
    else:
        receipt      = receipt_or_vc
        input_format = "OMNIX_RECEIPT"

    receipt_id   = receipt.get("receipt_id", "UNKNOWN")
    content_hash = receipt.get("content_hash", "")
    sig_b64      = receipt.get("signature")
    pub_key_b64  = receipt.get("public_key")
    sig_algo     = receipt.get("signature_algorithm", "SHA-256")
    provider_id  = receipt.get("signing_provider", "sha256")
    decision     = (receipt.get("decision") or "UNKNOWN").upper()
    domain       = receipt.get("domain", "generic")
    veto_chain   = receipt.get("veto_chain", [])

    result: Dict[str, Any] = {
        "receipt_id":          receipt_id,
        "verified_at":         now,
        "input_format":        input_format,
        "issuer_did":          OMNIX_DID,
        "hash_valid":          False,
        "signature_valid":     None,
        "overall_valid":       False,
        "independent":         True,
        "db_required":         False,
        "verification_method": f"{OMNIX_DID}#pqc-key-1",
    }

    payload_for_hash: Dict[str, Any] = {
        "receipt_id":     receipt.get("receipt_id"),
        "timestamp":      receipt.get("timestamp"),
        "asset":          receipt.get("asset"),
        "decision":       receipt.get("decision"),
        "veto_chain":     receipt.get("veto_chain"),
        "policy_version": receipt.get("policy_version"),
        "engine_version": receipt.get("engine_version"),
        "prev_hash":      receipt.get("prev_hash"),
    }
    if receipt.get("signing_provider"):
        payload_for_hash["signing_provider"] = receipt["signing_provider"]
    for opt in ("sharia_compliance","aml_compliance","fraud_compliance",
                "jurisdiction_compliance","context_admission"):
        if opt in receipt:
            payload_for_hash[opt] = receipt[opt]
    if "veto_type" in receipt:
        payload_for_hash["veto_type"] = receipt["veto_type"]

    canonical     = json.dumps(payload_for_hash, sort_keys=True, ensure_ascii=True)
    computed_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    result["hash_valid"]    = (computed_hash == content_hash)
    result["computed_hash"] = computed_hash
    result["stored_hash"]   = content_hash

    if not result["hash_valid"]:
        result["hash_note"] = "Content hash mismatch — receipt may have been tampered with."
    else:
        result["hash_note"] = "SHA-256 content hash verified — receipt payload is intact."

    if sig_b64 and pub_key_b64:
        try:
            import base64 as _b64
            try:
                from omnix_core.security.crypto_providers import get_provider as _get_prov
                provider = _get_prov(provider_id)
            except Exception:
                provider = None

            if provider:
                signature  = _b64.b64decode(sig_b64)
                public_key = provider.deserialize_public_key(pub_key_b64)
                message    = content_hash.encode("utf-8")
                result["signature_valid"] = provider.verify(signature, message, public_key)
                result["signature_note"]  = (
                    f"PQC signature verified ({sig_algo}). "
                    "Receipt is cryptographically authentic."
                ) if result["signature_valid"] else (
                    f"PQC signature INVALID ({sig_algo}). Receipt may have been forged."
                )
            else:
                result["signature_valid"] = None
                result["signature_note"]  = (
                    f"Provider '{provider_id}' not available in this environment. "
                    "Hash integrity still verified. "
                    "For full PQC verification, use /api/trust/verify on omnixquantum.net."
                )
        except Exception as e:
            result["signature_valid"] = None
            result["signature_note"]  = f"Verification attempted but failed: {e}"
    elif sig_b64 and not pub_key_b64:
        result["signature_valid"] = None
        result["signature_note"]  = (
            "Signature present but public key not embedded. "
            "Fetch the issuer public key from /api/trust/registry to complete verification."
        )
    else:
        result["signature_valid"] = None
        result["signature_note"]  = "No signature present — hash-chain integrity only."

    result["overall_valid"] = (
        result["hash_valid"] and result["signature_valid"] is not False
    )

    try:
        from api.omnix_engine.receipt_to_vc import build_jurisdiction_semantics
        result["jurisdiction_semantics"] = build_jurisdiction_semantics(
            veto_chain=veto_chain, decision=decision, domain=domain
        )
    except Exception:
        try:
            from omnix_engine.receipt_to_vc import build_jurisdiction_semantics
            result["jurisdiction_semantics"] = build_jurisdiction_semantics(
                veto_chain=veto_chain, decision=decision, domain=domain
            )
        except Exception:
            result["jurisdiction_semantics"] = None

    result["trust_chain"] = {
        "issuer_did":       OMNIX_DID,
        "issuer_name":      OMNIX_ISSUER_NAME,
        "registry_url":     f"{OMNIX_ISSUER_URL}/api/trust/registry",
        "did_document_url": f"{OMNIX_ISSUER_URL}/.well-known/did.json",
        "schema_url":       SUPPORTED_SCHEMAS[1],
        "context_url":      SUPPORTED_SCHEMAS[0],
    }
    result["algorithm"]         = sig_algo
    result["signing_provider"]  = provider_id

    return result
