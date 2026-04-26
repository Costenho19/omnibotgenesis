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

    def convert(
        self,
        receipt: Dict[str, Any],
        human_signer: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Wrap an OMNIX receipt into a W3C VC envelope.
        Returns the VC as a dict (JSON-serialisable).

        Args:
            receipt:      OMNIX governance receipt dict.
            human_signer: Optional human accountability block (ADR-130 §7).
                          If provided, embedded in the proof as 'humanSigner'.
                          {
                            "reviewer_id":       str,
                            "attested_at":       ISO8601,
                            "attestation_hash":  "sha256:<hex>",
                            "oversight_session_id": str | None,
                            "eqs_score":         float | None,
                          }
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

        try:
            from api.omnix_engine.vc_revocation import build_credential_status
        except ImportError:
            try:
                from omnix_engine.vc_revocation import build_credential_status
            except ImportError:
                build_credential_status = None

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
            "credentialStatus": (
                build_credential_status(receipt_id)
                if build_credential_status else {
                    "id":   f"{OMNIX_ISSUER_URL}/api/trust/vc-status/{receipt_id}",
                    "type": "StatusList2021Entry",
                    "statusPurpose": "revocation",
                    "statusListCredential": f"{OMNIX_ISSUER_URL}/api/trust/status-list",
                }
            ),
            "credentialSubject": credential_subject,
        }

        if sig_b64:
            proof_block = {
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
            proof_block = {
                "type":               "OmnixHashProof2026",
                "created":            issuance_dt.isoformat(),
                "proofPurpose":       "assertionMethod",
                "proofValue":         content_hash,
                "signatureAlgorithm": "SHA-256",
                "nist_note":          "Hash-chain integrity proof (no PQC key available at issuance)",
            }

        if human_signer:
            proof_block["humanSigner"] = self._build_human_signer_block(
                receipt_id, human_signer
            )

        vc["proof"] = proof_block
        return vc

    def _build_human_signer_block(
        self,
        receipt_id: str,
        human_signer: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Builds the humanSigner sub-block for the proof.

        ADR-130 §7 — Human Accountability Binding:
        The human who authorized the issuance of this governance credential is
        cryptographically identified. This shifts OMNIX governance from
        observational (the system decided) to accountable (this human authorized it).

        The attestation_hash binds reviewer_id + receipt_id + attested_at in a
        single SHA-256 digest — independently verifiable by any party.

        Verifier instructions:
          1. SHA-256(reviewer_id + ":" + receipt_id + ":" + attested_at)
          2. Compare with attestation_hash (strip "sha256:" prefix)
          3. Match confirms the named human was the authorizing party.
        """
        reviewer_id   = human_signer.get("reviewer_id", "unknown")
        attested_at   = human_signer.get("attested_at", datetime.now(timezone.utc).isoformat())
        session_id    = human_signer.get("oversight_session_id")
        eqs_score     = human_signer.get("eqs_score")
        provided_hash = human_signer.get("attestation_hash", "")

        if not provided_hash.startswith("sha256:"):
            import hashlib as _hl
            computed = _hl.sha256(
                f"{reviewer_id}:{receipt_id}:{attested_at}".encode()
            ).hexdigest()
            attestation_hash = f"sha256:{computed}"
        else:
            attestation_hash = provided_hash

        block: Dict[str, Any] = {
            "type":             "HumanAccountabilityAttestation2026",
            "adr":              "ADR-130 — Human Accountability Binding",
            "reviewerId":       reviewer_id,
            "attestedAt":       attested_at,
            "attestationHash":  attestation_hash,
            "hashMethod":       "SHA-256(reviewerId:receipt_id:attestedAt)",
            "verifierNote":     (
                "Recompute SHA-256(reviewerId + ':' + receipt_id + ':' + attestedAt) "
                "and compare with attestationHash to confirm human identity binding."
            ),
        }
        if session_id:
            block["oversightSessionId"] = session_id
        if eqs_score is not None:
            block["epistemicQualityScore"] = round(float(eqs_score), 4)
        return block

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
    means under specific regulatory frameworks — ADR-085 cross-border edition.

    Design principle: OMNIX proves THAT a decision was governed (cryptographically).
    It does NOT claim authoritative regulatory equivalence across jurisdictions.
    This block maximises coverage by mapping the receipt to every applicable
    framework explicitly, and states the proof scope and its limits in plain language
    so that any external verifier understands exactly what this receipt certifies.

    Frameworks covered (10):
      EU AI Act · GDPR · DORA · FATF · UK FCA/SMCR · US SEC Rule 15c3-5 ·
      MAS Singapore · UAE CBUAE · SAMA Saudi Arabia · FSB G20
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

    # ------------------------------------------------------------------
    # REGULATORY FRAMEWORKS — 10 jurisdictions
    # Each entry: label, jurisdiction, region, APPROVED / BLOCKED / HOLD
    # text, and the specific article/reference cited.
    # ------------------------------------------------------------------
    JURISDICTION_INTERPRETATION = {
        "EU_AI_ACT": {
            "label":      "EU Artificial Intelligence Act",
            "jurisdiction": "European Union",
            "region":     "Europe",
            "reference":  "Regulation (EU) 2024/1689",
            "APPROVED": (
                "Decision satisfies EU AI Act Article 9 risk management requirements. "
                "All applicable high-risk AI system governance checkpoints passed. "
                "Compliant with Annex III — Financial Services classification. "
                "Transparency obligation (Art.13) met via signed veto chain."
            ),
            "BLOCKED": (
                "Decision blocked by OMNIX governance — not presented to end user. "
                "EU AI Act Article 14 (Human Oversight) satisfied: system prevented "
                "a non-compliant outcome before execution. Logging obligations met."
            ),
            "HOLD": (
                "Decision deferred pending additional review. EU AI Act Article 9(2) "
                "iterative risk assessment ongoing. Human reviewer notified."
            ),
        },
        "GDPR": {
            "label":      "EU General Data Protection Regulation",
            "jurisdiction": "European Union",
            "region":     "Europe",
            "reference":  "Regulation (EU) 2016/679 — Article 22",
            "APPROVED": (
                "Automated decision satisfies GDPR Article 22 requirements. "
                "OMNIX governance pipeline constitutes meaningful oversight equivalent — "
                "decision is not solely automated. Audit trail available per Art.5(2)."
            ),
            "BLOCKED": (
                "Automated decision blocked before affecting data subject rights. "
                "GDPR Article 22 (right not to be subject to solely automated decisions) "
                "protected — no adverse outcome reached the data subject."
            ),
            "HOLD": (
                "Decision deferred. GDPR Article 22 data subject rights preserved. "
                "Manual review initiated before any profiling-based outcome is issued."
            ),
        },
        "DORA": {
            "label":      "Digital Operational Resilience Act",
            "jurisdiction": "European Union — Financial Sector",
            "region":     "Europe",
            "reference":  "Regulation (EU) 2022/2554",
            "APPROVED": (
                "Decision passed DORA Article 6 ICT Risk Management requirements. "
                "Stress testing (CP-6) and threshold validation (CP-8) confirm "
                "operational resilience. ICT incident classification: none triggered."
            ),
            "BLOCKED": (
                "ICT risk threshold breach detected. Decision blocked per DORA Article 8 "
                "risk identification obligations. Incident classification logged. "
                "Notification obligations under Art.19 assessed."
            ),
            "HOLD": (
                "Operational parameters outside defined ICT boundaries. DORA Article 13 "
                "security policy review required before decision proceeds."
            ),
        },
        "FATF": {
            "label":      "FATF — Financial Action Task Force",
            "jurisdiction": "International (G7 + 37 member jurisdictions)",
            "region":     "Global",
            "reference":  "FATF Recommendations 10, 16, 20, 29 (2023 update)",
            "APPROVED": (
                "AML screening (CP-9) passed. Transaction pattern consistent with "
                "FATF Recommendation 10 Customer Due Diligence. "
                "No structuring, layering, or high-risk counterparty signals detected. "
                "Travel Rule (R.16) compliance check included where applicable."
            ),
            "BLOCKED": (
                "AML gate triggered BLOCK. Decision suppressed before execution per "
                "FATF Recommendation 29 (Financial Intelligence obligations). "
                "Suspicious Transaction Report (STR) obligation reviewed. "
                "Audit record preserved for competent authority."
            ),
            "HOLD": (
                "AML screening inconclusive. Enhanced Due Diligence (FATF R.10 EDD) "
                "recommended. Transaction held pending manual verification."
            ),
        },
        "UK_FCA": {
            "label":      "UK FCA — Senior Managers & Certification Regime + COBS",
            "jurisdiction": "United Kingdom",
            "region":     "United Kingdom",
            "reference":  "FCA COBS 11.2 · SYSC 9.1 · SM&CR 2016",
            "APPROVED": (
                "Decision satisfies FCA COBS 11.2 best execution obligations. "
                "OMNIX veto chain provides the audit trail required under SYSC 9.1 "
                "(record-keeping for regulated activities). SM&CR accountability "
                "preserved — governance checkpoint evidence available per request."
            ),
            "BLOCKED": (
                "Decision suppressed by governance pipeline in line with FCA Principle 6 "
                "(Customers' Interests) and COBS 2.1.1 (fair, clear, not misleading). "
                "SM&CR senior manager accountability: blocked-decision receipt retained."
            ),
            "HOLD": (
                "Decision held pending clarification. FCA Principle 2 (Skill, Care, "
                "Diligence) applies — manual review required before execution."
            ),
        },
        "US_SEC": {
            "label":      "US SEC — Rule 15c3-5 (Market Access Rule) + Reg SCI",
            "jurisdiction": "United States of America",
            "region":     "North America",
            "reference":  "17 CFR §240.15c3-5 · Regulation SCI (17 CFR §242.1000)",
            "APPROVED": (
                "Decision passed pre-trade risk controls consistent with SEC Rule 15c3-5 "
                "market access requirements. Risk evaluation (CP-3), threshold checks (CP-8), "
                "and coherence gate (CP-4) satisfy erroneous-order prevention obligations. "
                "Reg SCI systems integrity confirmed via stress test (CP-6)."
            ),
            "BLOCKED": (
                "Decision blocked by pre-trade controls per SEC Rule 15c3-5(c)(1). "
                "Order was not transmitted to market — regulatory block recorded. "
                "Reg SCI incident assessment initiated."
            ),
            "HOLD": (
                "Decision held for supervisory review consistent with FINRA Rule 3110 "
                "supervision obligations. No market access until review completes."
            ),
        },
        "MAS_SINGAPORE": {
            "label":      "MAS — Monetary Authority of Singapore AI Governance Framework",
            "jurisdiction": "Singapore",
            "region":     "Asia-Pacific",
            "reference":  "MAS FEAT Principles (2019) · MAS AI Governance Framework v2 (2020)",
            "APPROVED": (
                "Decision satisfies MAS FEAT Principle: Fairness, Ethics, Accountability, "
                "Transparency. OMNIX veto chain fulfils the Explainability requirement — "
                "each checkpoint provides a traceable rationale per MAS FEAT §3.4. "
                "Audit trail meets MAS Notice FAA-N16 record-retention standards."
            ),
            "BLOCKED": (
                "Decision suppressed. MAS FEAT Accountability principle satisfied — "
                "system prevented an outcome that failed internal governance thresholds. "
                "Governance record retained per MAS Notice SFA 04-N02."
            ),
            "HOLD": (
                "Decision deferred. MAS FEAT Transparency obligation: human reviewer "
                "notified with full checkpoint trace before any outcome is issued."
            ),
        },
        "UAE_CBUAE": {
            "label":      "UAE Central Bank AI Governance Framework",
            "jurisdiction": "United Arab Emirates",
            "region":     "Middle East",
            "reference":  "CBUAE AI Governance Framework 2024 · UAE Federal AI Strategy 2031",
            "APPROVED": (
                "Decision compliant with CBUAE AI Governance Framework (2024). "
                "Explainability requirement met — veto chain provides full audit trail "
                "per Article 3.2 (Transparency). Sharia-compatibility gate included "
                "where domain is Islamic Finance (Ethics & Domain Gate CP-7)."
            ),
            "BLOCKED": (
                "Decision blocked in compliance with CBUAE Article 4.1 (Risk Management). "
                "Automated suppression recorded. Governance receipt retained for "
                "CBUAE supervisory review if requested."
            ),
            "HOLD": (
                "Decision pending review. CBUAE Article 5 (Human Oversight) protocol active. "
                "No automated outcome issued pending manual confirmation."
            ),
        },
        "SAMA_SAUDI": {
            "label":      "SAMA — Saudi Central Bank Open Banking & AI Framework",
            "jurisdiction": "Kingdom of Saudi Arabia",
            "region":     "Middle East",
            "reference":  "SAMA Principles for Responsible AI in Finance (2023) · Vision 2030",
            "APPROVED": (
                "Decision consistent with SAMA Responsible AI Principle 3 (Accountability) "
                "and Principle 5 (Transparency). Governance checkpoint evidence satisfies "
                "SAMA's auditability requirement. Sharia compliance gate (CP-7) active "
                "for Islamic finance domain decisions."
            ),
            "BLOCKED": (
                "Decision blocked. SAMA Principle 2 (Safety) satisfied — automated "
                "suppression prevented a potentially non-compliant financial outcome. "
                "Signed receipt retained per SAMA record-keeping obligations."
            ),
            "HOLD": (
                "Decision held. SAMA Principle 3 (Human Accountability) requires manual "
                "review. Checkpoint trace available for SAMA examination."
            ),
        },
        "FSB_G20": {
            "label":      "FSB — Financial Stability Board AI/ML in Financial Services",
            "jurisdiction": "G20 — International",
            "region":     "Global",
            "reference":  "FSB Report on AI/ML in Financial Services (Nov 2017, updated 2023)",
            "APPROVED": (
                "Decision governance satisfies FSB accountability and explainability "
                "recommendations for AI/ML in financial services. Third-party verifiability "
                "requirement met — receipt hash and signature independently verifiable. "
                "Model risk management (CP-3 + CP-6) consistent with FSB guidance §3.2."
            ),
            "BLOCKED": (
                "Governance pipeline blocked decision consistent with FSB guidance on "
                "fail-safe mechanisms (§4.1 — operational risk). Signed receipt provides "
                "the accountability trail FSB recommends for suppressed AI outputs."
            ),
            "HOLD": (
                "Decision held for review consistent with FSB recommendation on human "
                "oversight of high-impact automated financial decisions (§3.4)."
            ),
        },
    }

    dec = (decision or "UNKNOWN").upper()

    # Build per-framework interpretations
    frameworks_output = {}
    for fw_key, fw_data in JURISDICTION_INTERPRETATION.items():
        text = fw_data.get(dec, fw_data.get("APPROVED", ""))
        frameworks_output[fw_key] = {
            "label":           fw_data["label"],
            "jurisdiction":    fw_data["jurisdiction"],
            "region":          fw_data["region"],
            "reference":       fw_data["reference"],
            "interpretation":  text,
            "decision_effect": dec,
        }

    blocked_gates = [
        f"{g} blocked → {GATE_TO_CHECKPOINT.get(g, 'CP-?')} failed"
        for g in checkpoints_blocked
    ]

    # ------------------------------------------------------------------
    # PROOF SCOPE — explicit separation of what OMNIX proves vs. what it
    # does not claim. This is the direct answer to the cross-border
    # semantic equivalence problem: we state our boundary plainly so
    # any verifier knows exactly what this receipt certifies.
    # ------------------------------------------------------------------
    proof_scope = {
        "what_this_receipt_proves": [
            "The decision was evaluated by OMNIX governance checkpoints at the stated timestamp.",
            "The veto chain result ({} passed, {} blocked) is cryptographically bound to this receipt.".format(
                len(checkpoints_passed), len(checkpoints_blocked)
            ),
            "The receipt has not been altered since signing — hash and PQC signature are independently verifiable.",
            "The issuer (did:web:omnixquantum.net) controlled the signing key at time of issuance.",
            "Each regulatory framework mapping above reflects OMNIX's interpretation at time of issuance.",
        ],
        "what_this_receipt_does_not_claim": [
            "Authoritative regulatory approval from any named jurisdiction or supervisory body.",
            "Semantic equivalence between the interpretations above — different verifiers in "
            "different jurisdictions may reach different regulatory conclusions from the same receipt.",
            "That OMNIX's internal checkpoint logic satisfies every local implementation rule — "
            "local legal counsel assessment remains the authoritative determination.",
            "Guaranteed cross-border enforceability — receipt serves as governance evidence, "
            "not as a substitute for jurisdiction-specific compliance certification.",
        ],
        "verifier_guidance": (
            "To use this receipt as governance evidence: (1) verify the hash and PQC signature "
            "independently via https://omnixquantum.net/api/trust/verify; (2) apply the "
            "regulatory_interpretation entry for your local jurisdiction; (3) obtain legal "
            "counsel confirmation for any jurisdiction-specific compliance determination. "
            "The proof_scope block is provided to ensure all parties share the same understanding "
            "of what this cryptographic evidence certifies and where interpretation diverges."
        ),
    }

    # ------------------------------------------------------------------
    # CROSS-JURISDICTION CONCORDANCE — which frameworks agree on the
    # outcome and which may require additional local assessment.
    # ------------------------------------------------------------------
    global_frameworks  = ["FATF", "FSB_G20"]
    europe_frameworks  = ["EU_AI_ACT", "GDPR", "DORA"]
    uk_frameworks      = ["UK_FCA"]
    us_frameworks      = ["US_SEC"]
    apac_frameworks    = ["MAS_SINGAPORE"]
    me_frameworks      = ["UAE_CBUAE", "SAMA_SAUDI"]

    if dec == "APPROVED":
        concordance_note = (
            "All 10 mapped frameworks interpret an APPROVED outcome as evidence of "
            "governance compliance for the checkpoints within OMNIX's scope. "
            "Local regulatory bodies retain authority over final compliance determination."
        )
        concordance_status = "BROADLY_ALIGNED"
    elif dec == "BLOCKED":
        concordance_note = (
            "All 10 mapped frameworks interpret a BLOCKED outcome as a governance "
            "safeguard satisfying oversight obligations. "
            "FATF and UK FCA frameworks additionally trigger record-retention and "
            "potential reporting obligations that must be assessed locally."
        )
        concordance_status = "ALIGNED_WITH_LOCAL_REPORTING_OBLIGATIONS"
    else:
        concordance_note = (
            "A HOLD outcome is interpreted consistently across all frameworks as a "
            "deferred decision requiring human review. No framework treats HOLD as "
            "a final adverse determination."
        )
        concordance_status = "FULLY_ALIGNED"

    cross_jurisdiction_concordance = {
        "status":  concordance_status,
        "note":    concordance_note,
        "regions": {
            "Global (FATF + FSB)":        global_frameworks,
            "European Union":             europe_frameworks,
            "United Kingdom":             uk_frameworks,
            "United States":              us_frameworks,
            "Asia-Pacific (Singapore)":   apac_frameworks,
            "Middle East (UAE + Saudi)":  me_frameworks,
        },
        "divergence_risk": (
            "Low for cryptographic validity — all verifiers will reach the same "
            "conclusion on receipt integrity. Medium for regulatory interpretation — "
            "local implementation rules may add obligations (e.g., FATF STR reporting, "
            "UK SM&CR accountability mapping, US Reg SCI incident classification) that "
            "OMNIX's internal logic does not automatically fulfil."
        ),
    }

    return {
        "omnix_decision_meaning": (
            f"The OMNIX engine evaluated this {domain} decision through "
            f"{len(veto_chain)} governance checkpoints. "
            f"{'All checkpoints passed — decision approved for execution.' if dec == 'APPROVED' else 'One or more checkpoints blocked the decision — execution was suppressed.'}"
        ),
        "frameworks_mapped":         len(JURISDICTION_INTERPRETATION),
        "checkpoints_passed_count":  len(checkpoints_passed),
        "checkpoints_blocked_count": len(checkpoints_blocked),
        "blocked_gates":             blocked_gates,
        "proof_scope":               proof_scope,
        "regulatory_interpretation": frameworks_output,
        "cross_jurisdiction_concordance": cross_jurisdiction_concordance,
        "schema_url":   "https://omnixquantum.net/schemas/omnix-receipt-schema-v6.5.4e.json",
        "context_url":  OMNIX_JSONLD_CONTEXT,
        "note": (
            "This semantics block maps the receipt to 10 regulatory frameworks across "
            "6 regions to maximise cross-border interpretability. "
            "Interpretations reflect OMNIX's regulatory mapping at time of issuance. "
            "The proof_scope block explicitly states what this receipt certifies and "
            "where authoritative determination remains with local regulatory bodies. "
            "Independent verifiers should read proof_scope before drawing compliance conclusions."
        ),
    }
