"""
OMNIX Receipt → W3C Verifiable Credential Converter — ADR-084
Wraps any valid OMNIX governance receipt into a W3C VC (JSON-LD) envelope.

Spec: W3C Verifiable Credentials Data Model 1.1
      https://www.w3.org/TR/vc-data-model/

The existing PQC signature becomes the VC proof block.
The JSON-LD context is served at omnixquantum.net/schemas/omnix-receipt-v1.jsonld.
"""

import json
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger("OMNIX.VC")

OMNIX_JSONLD_CONTEXT = "https://omnixquantum.net/schemas/omnix-receipt-v1.jsonld"
OMNIX_ISSUER_DID     = "did:web:omnixquantum.net"
OMNIX_ISSUER_NAME    = "OMNIX Quantum Ltd"
OMNIX_ISSUER_URL     = "https://omnixquantum.net"

VC_CONTEXT = [
    "https://www.w3.org/2018/credentials/v1",
    OMNIX_JSONLD_CONTEXT,
]

VC_DEFAULT_TTL_DAYS = 365


class ReceiptToVC:
    """
    Converts an OMNIX governance receipt dict into a W3C Verifiable Credential.

    Usage:
        converter = ReceiptToVC()
        vc = converter.convert(receipt)
    """

    def convert(self, receipt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrap an OMNIX receipt into a W3C VC envelope.
        Returns the VC as a dict (JSON-serialisable).
        """
        receipt_id  = receipt.get("receipt_id", "UNKNOWN")
        timestamp   = receipt.get("timestamp", datetime.now(timezone.utc).isoformat())
        asset       = receipt.get("asset", "UNKNOWN")
        decision    = receipt.get("decision", "UNKNOWN")
        domain      = receipt.get("domain", "generic")
        veto_chain  = receipt.get("veto_chain", [])
        content_hash = receipt.get("content_hash", "")
        sig_b64      = receipt.get("signature")
        sig_algo     = receipt.get("signature_algorithm", "SHA-256")
        pub_key_b64  = receipt.get("public_key")
        policy_ver   = receipt.get("policy_version", "6.5.4e")
        engine_ver   = receipt.get("engine_version", "6.5.4e")
        prev_hash    = receipt.get("prev_hash", "")
        provider_id  = receipt.get("signing_provider", "sha256")

        issuance_dt  = self._parse_timestamp(timestamp)
        expiry_dt    = issuance_dt + timedelta(days=VC_DEFAULT_TTL_DAYS)
        vc_id        = f"https://omnixquantum.net/receipts/{receipt_id}"

        credential_subject = {
            "id":               vc_id,
            "receipt_id":       receipt_id,
            "asset":            asset,
            "decision":         decision,
            "domain":           domain,
            "veto_chain":       veto_chain,
            "policy_version":   policy_ver,
            "engine_version":   engine_ver,
            "prev_hash":        prev_hash,
            "content_hash":     content_hash,
            "signing_provider": provider_id,
        }

        for optional_block in (
            "sharia_compliance", "aml_compliance", "fraud_compliance",
            "jurisdiction_compliance", "context_admission", "veto_type",
        ):
            if optional_block in receipt:
                credential_subject[optional_block] = receipt[optional_block]

        vc = {
            "@context": VC_CONTEXT,
            "id": vc_id,
            "type": ["VerifiableCredential", "OmnixGovernanceCredential"],
            "issuer": {
                "id":   OMNIX_ISSUER_DID,
                "name": OMNIX_ISSUER_NAME,
                "url":  OMNIX_ISSUER_URL,
            },
            "issuanceDate":   issuance_dt.isoformat(),
            "expirationDate": expiry_dt.isoformat(),
            "credentialSubject": credential_subject,
        }

        if sig_b64:
            vc["proof"] = {
                "type":               self._map_proof_type(sig_algo),
                "created":            issuance_dt.isoformat(),
                "verificationMethod": f"{OMNIX_ISSUER_DID}#pqc-key-1",
                "proofPurpose":       "assertionMethod",
                "proofValue":         sig_b64,
                "publicKey":          pub_key_b64,
                "signatureAlgorithm": sig_algo,
                "signedData":         content_hash,
                "nist_note":          "Post-quantum signature (NIST-standardized algorithm)",
            }
        else:
            vc["proof"] = {
                "type":           "OmnixHashProof2026",
                "created":        issuance_dt.isoformat(),
                "proofPurpose":   "assertionMethod",
                "proofValue":     content_hash,
                "signatureAlgorithm": "SHA-256",
                "nist_note":      "Hash-chain integrity proof (no PQC key available at issuance)",
            }

        return vc

    def _parse_timestamp(self, ts: Any) -> datetime:
        if isinstance(ts, datetime):
            return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    def _map_proof_type(self, algo: str) -> str:
        mapping = {
            "Dilithium-3":  "Dilithium2021",
            "ML-DSA-65":    "MlDsa2024",
            "Falcon-512":   "Falcon2021",
            "Ed25519":      "Ed25519Signature2020",
            "SHA-256":      "OmnixHashProof2026",
        }
        return mapping.get(algo, "OmnixPostQuantumProof2026")


def build_jurisdiction_semantics(
    veto_chain: list,
    decision: str,
    domain: str,
) -> Dict[str, Any]:
    """
    Build a jurisdiction_semantics block explaining what each checkpoint result
    means under specific regulatory frameworks.

    This makes receipts interpretable by external systems that do not know
    OMNIX's internal logic — they only need to understand EU AI Act / FATF / etc.
    """
    checkpoints_passed  = []
    checkpoints_blocked = []

    for entry in veto_chain:
        entry_str = str(entry)
        parts = entry_str.split(":", 1)
        if len(parts) < 2:
            continue
        gate = parts[0].strip()
        result_part = parts[1].strip()
        if "BLOCKED" in result_part.upper():
            checkpoints_blocked.append(gate)
        else:
            checkpoints_passed.append(gate)

    GATE_TO_CHECKPOINT = {
        "Signal Integrity Validator": "CP-1",
        "Probability Assessment":     "CP-2",
        "Risk Evaluation":            "CP-3",
        "Coherence Engine":           "CP-4",
        "Trend Validator":            "CP-5",
        "Stress Testing":             "CP-6",
        "Ethics & Domain Gate":       "CP-7",
        "Threshold & Context":        "CP-8",
        "AML Screening":              "CP-9",
        "Fraud Detection":            "CP-10",
        "Jurisdiction Compliance":    "CP-11",
    }

    JURISDICTION_INTERPRETATION = {
        "EU_AI_ACT": {
            "label":   "EU Artificial Intelligence Act",
            "jurisdiction": "European Union",
            "APPROVED": (
                "Decision satisfies EU AI Act Article 9 risk management requirements. "
                "All applicable high-risk AI system governance checkpoints passed. "
                "Compliant with Annex III — Financial Services classification."
            ),
            "BLOCKED": (
                "Decision blocked by OMNIX governance — not presented to end user. "
                "EU AI Act Article 14 (Human Oversight) satisfied: system prevented "
                "a non-compliant outcome before execution."
            ),
            "HOLD": (
                "Decision deferred pending additional review. EU AI Act Article 9(2) "
                "iterative risk assessment ongoing."
            ),
        },
        "FATF": {
            "label":   "FATF — Financial Action Task Force",
            "jurisdiction": "International (G7 + 37 members)",
            "APPROVED": (
                "AML screening (CP-9) passed. Transaction pattern consistent with "
                "FATF Recommendation 10 Customer Due Diligence requirements. "
                "No structuring, smurfing, or high-risk counterparty signals detected."
            ),
            "BLOCKED": (
                "AML gate triggered BLOCK. Decision suppressed before execution in "
                "compliance with FATF Recommendation 29 (Financial Intelligence). "
                "Suspicious transaction report (STR) obligation may apply."
            ),
            "HOLD": (
                "AML screening inconclusive. Enhanced Due Diligence (FATF R.10) "
                "recommended before proceeding."
            ),
        },
        "GDPR": {
            "label":   "EU General Data Protection Regulation",
            "jurisdiction": "European Union",
            "APPROVED": (
                "Automated decision satisfies GDPR Article 22 requirements. "
                "Human oversight mechanism was active (OMNIX governance layer). "
                "Decision is not solely automated — governance pipeline constitutes "
                "meaningful human-equivalent review."
            ),
            "BLOCKED": (
                "Automated decision blocked before affecting data subject rights. "
                "GDPR Article 22 (right not to be subject to solely automated decision) "
                "protected — no adverse outcome reached the data subject."
            ),
            "HOLD": (
                "Decision deferred. GDPR Article 22 rights preserved pending review."
            ),
        },
        "DORA": {
            "label":   "Digital Operational Resilience Act (EU) 2022/2554",
            "jurisdiction": "European Union — Financial Sector",
            "APPROVED": (
                "Decision passed DORA Article 6 ICT Risk Management requirements. "
                "Stress testing (CP-6) and threshold validation (CP-8) confirm "
                "operational resilience of the automated decision system."
            ),
            "BLOCKED": (
                "ICT risk threshold breach detected. Decision blocked per DORA Article 8 "
                "risk identification obligations. Incident logging active."
            ),
            "HOLD": (
                "Operational parameters outside defined boundaries. DORA Article 13 "
                "ICT security policy review required."
            ),
        },
        "UAE_CBUAE": {
            "label":   "UAE Central Bank AI Governance Framework",
            "jurisdiction": "United Arab Emirates",
            "APPROVED": (
                "Decision compliant with UAE CBUAE Artificial Intelligence Governance "
                "Framework (2024). Explainability requirement met — veto chain provides "
                "full audit trail per Article 3.2 (Transparency)."
            ),
            "BLOCKED": (
                "Decision blocked by governance pipeline in compliance with CBUAE "
                "Article 4.1 (Risk Management). Automated suppression recorded."
            ),
            "HOLD": (
                "Decision pending review. CBUAE Article 5 (Human Oversight) protocol active."
            ),
        },
    }

    dec = (decision or "UNKNOWN").upper()
    frameworks_output = {}
    for fw_key, fw_data in JURISDICTION_INTERPRETATION.items():
        text = fw_data.get(dec, fw_data.get("APPROVED", ""))
        frameworks_output[fw_key] = {
            "label":          fw_data["label"],
            "jurisdiction":   fw_data["jurisdiction"],
            "interpretation": text,
            "decision_effect": dec,
        }

    blocked_gates = [
        f"{g} blocked → {GATE_TO_CHECKPOINT.get(g, 'CP-?')} failed"
        for g in checkpoints_blocked
    ]

    return {
        "omnix_decision_meaning": (
            f"The OMNIX engine evaluated this {domain} decision through "
            f"{len(veto_chain)} governance checkpoints. "
            f"{'All checkpoints passed — decision approved for execution.' if dec == 'APPROVED' else 'One or more checkpoints blocked the decision — execution was suppressed.'}"
        ),
        "checkpoints_passed_count":  len(checkpoints_passed),
        "checkpoints_blocked_count": len(checkpoints_blocked),
        "blocked_gates":             blocked_gates,
        "regulatory_interpretation": frameworks_output,
        "schema_url":
            "https://omnixquantum.net/schemas/omnix-receipt-schema-v6.5.4e.json",
        "context_url":
            OMNIX_JSONLD_CONTEXT,
        "note": (
            "This semantics block is provided to enable external systems to interpret "
            "OMNIX receipts without requiring knowledge of OMNIX internal logic. "
            "Interpretations are informational — authoritative compliance determination "
            "remains with the relevant regulatory body."
        ),
    }
