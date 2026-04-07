"""
OMNIX Regulatory Mapping Engine
Maps each of the 11 governance checkpoints to specific regulatory frameworks.
Frameworks: CA SB 243, EU AI Act, DORA, NIST AI RMF, ISO 42001, GDPR, Basel III.

Returns structured regulatory_alignment metadata for each decision receipt.
"""

CHECKPOINT_REGULATORY_MAP = {
    "CP-1": {
        "name": "Signal Integrity Validator",
        "frameworks": {
            "NIST_AI_RMF": {
                "ref": "GOVERN 1.1 / MEASURE 2.5",
                "description": "Input data integrity validation — ensures decision inputs meet quality thresholds before processing.",
            },
            "EU_AI_ACT": {
                "ref": "Article 10 — Data Governance",
                "description": "High-risk AI systems must use data that is relevant, representative, and free of errors.",
            },
            "ISO_42001": {
                "ref": "Clause 8.4 — AI System Input",
                "description": "Input validation controls for AI system integrity.",
            },
            "CA_SB_243": {
                "ref": "Section 3(b) — Input Transparency",
                "description": "AI system must document and validate the nature of inputs used in consequential decisions.",
            },
        },
    },
    "CP-2": {
        "name": "Probability Assessment",
        "frameworks": {
            "NIST_AI_RMF": {
                "ref": "MEASURE 1.1 / MEASURE 2.1",
                "description": "Quantitative risk and uncertainty measurement prior to decision execution.",
            },
            "DORA": {
                "ref": "Article 6 — ICT Risk Management Framework",
                "description": "Probabilistic risk assessment required for automated systems in financial entities.",
            },
            "BASEL_III": {
                "ref": "Pillar 2 — Internal Capital Adequacy",
                "description": "Probability-weighted assessment of decision outcomes affecting capital exposure.",
            },
            "EU_AI_ACT": {
                "ref": "Article 9 — Risk Management System",
                "description": "Ongoing risk assessment throughout the lifecycle of high-risk AI systems.",
            },
        },
    },
    "CP-3": {
        "name": "Risk Evaluation",
        "frameworks": {
            "DORA": {
                "ref": "Article 8 — Identification of ICT Risk",
                "description": "Risk exposure evaluation and classification for financial-sector automated decisions.",
            },
            "NIST_AI_RMF": {
                "ref": "MAP 1.1 / MEASURE 2.2",
                "description": "Systematic risk identification and impact assessment.",
            },
            "BASEL_III": {
                "ref": "Pillar 1 — Operational Risk",
                "description": "Risk exposure must not exceed defined thresholds per operational risk framework.",
            },
            "EU_AI_ACT": {
                "ref": "Article 9(2) — Iterative Risk Assessment",
                "description": "Risk levels must be evaluated and updated based on operational context.",
            },
        },
    },
    "CP-4": {
        "name": "Coherence Engine",
        "frameworks": {
            "NIST_AI_RMF": {
                "ref": "MEASURE 2.6 — Bias & Coherence",
                "description": "Detects internal signal contradictions that could lead to inconsistent or biased decisions.",
            },
            "ISO_42001": {
                "ref": "Clause 9.1 — Performance Evaluation",
                "description": "AI system outputs must be evaluated for consistency and coherence.",
            },
            "EU_AI_ACT": {
                "ref": "Article 15 — Robustness and Accuracy",
                "description": "High-risk AI must maintain consistent accuracy across variable inputs.",
            },
        },
    },
    "CP-5": {
        "name": "Trend Validator",
        "frameworks": {
            "NIST_AI_RMF": {
                "ref": "MEASURE 2.7 — Environmental Context",
                "description": "Validates that decisions are consistent with prevailing market regime.",
            },
            "DORA": {
                "ref": "Article 9 — Scenario Analysis",
                "description": "Automated systems must account for current operational environment before execution.",
            },
            "BASEL_III": {
                "ref": "Pillar 2 — Stress Testing",
                "description": "Decision validity must be assessed against current market trends.",
            },
        },
    },
    "CP-6": {
        "name": "Stress Testing",
        "frameworks": {
            "DORA": {
                "ref": "Article 26 — Advanced TLPT Testing",
                "description": "Critical systems must demonstrate resilience under adverse conditions.",
            },
            "NIST_AI_RMF": {
                "ref": "MEASURE 2.5 — Adversarial Testing",
                "description": "System decisions must survive stress scenarios before approval.",
            },
            "BASEL_III": {
                "ref": "Pillar 2 — Stress Testing Requirements",
                "description": "Capital and risk decisions must be validated under stress scenarios.",
            },
            "EU_AI_ACT": {
                "ref": "Article 9(6) — Stress and Anomaly Testing",
                "description": "High-risk AI systems must be tested under foreseeable stress conditions.",
            },
        },
    },
    "CP-7": {
        "name": "Ethics & Domain Gate",
        "frameworks": {
            "EU_AI_ACT": {
                "ref": "Article 5 — Prohibited Practices / Article 14 — Human Oversight",
                "description": "Enforces ethical constraints and prohibits manipulation, discrimination, and unsafe automation.",
            },
            "NIST_AI_RMF": {
                "ref": "GOVERN 4.1 — Organizational Values",
                "description": "AI decisions must comply with organizational ethics policies.",
            },
            "ISO_42001": {
                "ref": "Clause 4.2 — Interested Parties / Clause 6.1 — Ethics Risk",
                "description": "Ethical considerations must be embedded in the AI governance system.",
            },
            "CA_SB_243": {
                "ref": "Section 4 — Algorithmic Accountability",
                "description": "Automated systems must not produce outputs that violate ethical standards or legal rights.",
            },
        },
    },
    "CP-8": {
        "name": "Threshold & Context Validator",
        "frameworks": {
            "NIST_AI_RMF": {
                "ref": "MAP 3.5 — Deployment Context",
                "description": "Decision parameters must be within defined operational boundaries for the deployment context.",
            },
            "DORA": {
                "ref": "Article 13 — Information Security Policies",
                "description": "Operational parameters and system configurations must remain within approved boundaries.",
            },
            "ISO_42001": {
                "ref": "Clause 8.5 — Operational Controls",
                "description": "AI system must operate within defined operational parameters.",
            },
        },
    },
    "CP-9": {
        "name": "AML Screening",
        "frameworks": {
            "FATF": {
                "ref": "Recommendation 10 — Customer Due Diligence",
                "description": "Automated screening for money laundering patterns, structuring, and high-risk counterparties.",
            },
            "EU_AI_ACT": {
                "ref": "Article 26 — Obligations for Deployers (Financial Sector)",
                "description": "AI systems used in financial services must include AML compliance checks.",
            },
            "DORA": {
                "ref": "Article 45 — Oversight of Critical ICT Providers",
                "description": "Automated transaction systems must include financial crime detection.",
            },
            "CA_SB_243": {
                "ref": "Section 5 — Financial Risk Disclosure",
                "description": "AI systems operating in financial contexts must screen for illegal transaction patterns.",
            },
        },
    },
    "CP-10": {
        "name": "Fraud Detection",
        "frameworks": {
            "NIST_AI_RMF": {
                "ref": "MEASURE 2.8 — Anomaly Detection",
                "description": "Automated fraud pattern detection before decision execution.",
            },
            "EU_AI_ACT": {
                "ref": "Article 9(2)(b) — Known Risks Mitigation",
                "description": "Reasonably foreseeable misuse patterns (including fraud) must be identified and mitigated.",
            },
            "DORA": {
                "ref": "Article 17 — ICT-Related Incident Management",
                "description": "Detection of fraud signals constitutes an ICT-related incident requiring automated response.",
            },
            "CA_SB_243": {
                "ref": "Section 6 — Automated Decision Audit Trail",
                "description": "Fraud detection events must be captured in the decision audit trail.",
            },
        },
    },
    "CP-11": {
        "name": "Jurisdiction Compliance",
        "frameworks": {
            "EU_AI_ACT": {
                "ref": "Article 4 — Scope / Article 85 — Delegated Acts",
                "description": "Ensures AI system decisions comply with the regulatory framework of the applicable jurisdiction.",
            },
            "GDPR": {
                "ref": "Article 22 — Automated Decision-Making",
                "description": "Automated decisions with legal or significant effect require human oversight mechanisms.",
            },
            "DORA": {
                "ref": "Article 3 — Scope / Chapter V — Third-Country Provisions",
                "description": "Digital operational resilience requirements vary by jurisdiction — CP-11 enforces applicable rules.",
            },
            "CA_SB_243": {
                "ref": "Section 2 — Applicability",
                "description": "Determines whether California AI transparency requirements apply based on decision context.",
            },
            "ISO_42001": {
                "ref": "Clause 4.1 — Context of the Organization",
                "description": "Organizational context includes legal and regulatory requirements per jurisdiction.",
            },
        },
    },
}

FRAMEWORK_METADATA = {
    "EU_AI_ACT": {
        "full_name": "EU Artificial Intelligence Act",
        "status": "In force — August 2024",
        "applies_to": "High-risk AI systems in EU markets",
        "risk_classification": "High-Risk (Annex III — Financial Services)",
    },
    "NIST_AI_RMF": {
        "full_name": "NIST AI Risk Management Framework 1.0",
        "status": "Published January 2023",
        "applies_to": "AI systems in US and internationally aligned organizations",
        "risk_classification": "Organizational + Technical Risk Controls",
    },
    "DORA": {
        "full_name": "Digital Operational Resilience Act (EU) 2022/2554",
        "status": "Applicable from January 2025",
        "applies_to": "Financial entities operating in the EU",
        "risk_classification": "ICT Risk in Financial Sector",
    },
    "ISO_42001": {
        "full_name": "ISO/IEC 42001:2023 — AI Management Systems",
        "status": "Published December 2023",
        "applies_to": "Organizations developing or deploying AI systems",
        "risk_classification": "Management System Standard",
    },
    "CA_SB_243": {
        "full_name": "California SB 243 — Automated Decision Systems Accountability Act",
        "status": "Under review / Proposed legislation",
        "applies_to": "AI systems making consequential decisions affecting California residents",
        "risk_classification": "State-level AI Accountability",
    },
    "GDPR": {
        "full_name": "General Data Protection Regulation (EU) 2016/679",
        "status": "In force — May 2018",
        "applies_to": "Processing personal data of EU residents",
        "risk_classification": "Data Protection / Privacy",
    },
    "FATF": {
        "full_name": "Financial Action Task Force Recommendations",
        "status": "Ongoing — updated periodically",
        "applies_to": "Financial institutions globally",
        "risk_classification": "Anti-Money Laundering / Counter-Terrorism Financing",
    },
    "BASEL_III": {
        "full_name": "Basel III — International Regulatory Framework for Banks",
        "status": "Implementation ongoing (Basel III.1 from 2025)",
        "applies_to": "Banks and financial institutions",
        "risk_classification": "Capital Adequacy / Operational Risk",
    },
}


def get_checkpoint_regulatory_alignment(checkpoint_id: str) -> dict:
    """Return regulatory frameworks mapped to a specific checkpoint."""
    return CHECKPOINT_REGULATORY_MAP.get(checkpoint_id, {})


def build_regulatory_summary(checkpoints_passed: list, checkpoints_blocked: list) -> dict:
    """
    Build a regulatory alignment summary for a decision receipt.
    Returns frameworks covered, checkpoint-to-regulation mapping, and overall status.
    """
    all_frameworks = set()
    checkpoint_map = []

    for cp_id in (checkpoints_passed + checkpoints_blocked):
        cp_data = CHECKPOINT_REGULATORY_MAP.get(cp_id)
        if not cp_data:
            continue
        frameworks = list(cp_data["frameworks"].keys())
        all_frameworks.update(frameworks)
        checkpoint_map.append({
            "checkpoint": cp_id,
            "name": cp_data["name"],
            "status": "PASSED" if cp_id in checkpoints_passed else "BLOCKED",
            "frameworks_enforced": frameworks,
        })

    frameworks_detail = []
    for fw_key in sorted(all_frameworks):
        fw_meta = FRAMEWORK_METADATA.get(fw_key, {})
        frameworks_detail.append({
            "id": fw_key,
            "full_name": fw_meta.get("full_name", fw_key),
            "status": fw_meta.get("status", ""),
            "applies_to": fw_meta.get("applies_to", ""),
        })

    return {
        "frameworks_covered": len(all_frameworks),
        "frameworks": frameworks_detail,
        "checkpoint_mapping": checkpoint_map,
        "attestation_note": (
            "This governance receipt constitutes a cryptographically signed attestation "
            "that the decision was evaluated against the regulatory frameworks listed above. "
            "Receipt is post-quantum signed (NIST-standardized algorithms) and chain-linked "
            "to the OMNIX Transparency Chain."
        ),
    }


def get_full_framework_catalog() -> dict:
    """Return the complete regulatory framework catalog for documentation endpoints."""
    return {
        "frameworks": FRAMEWORK_METADATA,
        "checkpoint_coverage": {
            cp_id: {
                "name": data["name"],
                "frameworks": list(data["frameworks"].keys()),
            }
            for cp_id, data in CHECKPOINT_REGULATORY_MAP.items()
        },
        "total_checkpoints": len(CHECKPOINT_REGULATORY_MAP),
        "total_frameworks": len(FRAMEWORK_METADATA),
    }
