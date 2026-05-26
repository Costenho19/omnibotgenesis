#!/usr/bin/env python3
"""
OMNIX OGI — Canonical Ontology Generator
ADR-193 OGI-INV-007 Gate 4 — Hallucination Detection Foundation

Auto-generates `ontology.json` from the live OMNIX corpus:
  - All ADR identifiers (extracted from filenames)
  - All RFC section identifiers
  - All invariant codes (regex-extracted from ADR/RFC content)
  - All canonical artifact IDs and their prefixes
  - All canonical term definitions (OMNIX vocabulary)
  - All PoGC tag names
  - All verdict tokens

The ontology is the ground truth for Gate 4 (hallucination rate ≤ 3%).
An OGI model output is a hallucination if it references an identifier
that does NOT appear in this file.

Usage:
  python generate_ontology.py [--output OUTPUT_PATH] [--verbose]

Outputs:
  scripts/fine_tuning/output/ontology.json

ADR-193 OGI-INV-007: hallucination_rate ≤ 3% — auto-checked against canonical ontology.
F-C-006 resolution: this script generates the ontology that Gate 4 requires.

Author: OMNIX QUANTUM LTD · Harold Nunes
Version: 2.0.0 — Gate B premium build
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("ogi.ontology")

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
OUTPUT_DIR  = SCRIPTS_DIR / "output"

# ── Section 1 — Hardcoded canonical terms (OMNIX vocabulary) ─────────────────
# These are the 60+ OMNIX-proprietary terms that cannot be derived from
# filename scanning alone. Updated when new RFCs or ADRs introduce terms.

CANONICAL_TERMS: dict[str, dict[str, Any]] = {

    # ── Core Artifacts ────────────────────────────────────────────────────────
    "DR": {
        "full_name": "Delegation Receipt",
        "description": "Cryptographic proof of authority transfer between agents",
        "adr": "RFC-ATF-1",
        "id_prefix": "DR-",
    },
    "TAR": {
        "full_name": "Temporal Admissibility Record",
        "description": "Proves a DR was valid at nanosecond of execution",
        "adr": "ADR-157",
        "id_prefix": "TAR-",
    },
    "RCR": {
        "full_name": "Runtime Continuity Record",
        "description": "Continuous health snapshot during long-running tasks",
        "adr": "RFC-ATF-2",
        "id_prefix": "RCR-",
    },
    "AIR": {
        "full_name": "Agent Identity Record",
        "description": "Immutable binding of agent to human principal",
        "adr": "RFC-ATF-1",
        "id_prefix": "AIR-",
    },
    "DTR": {
        "full_name": "Domain Translation Receipt",
        "description": "Enables cross-domain authority transfer",
        "adr": "ADR-158",
        "id_prefix": "DTR-",
    },
    "BAR": {
        "full_name": "Behavioral Anchor Record",
        "description": "Per-turn PQC-signed attestation of agent output",
        "adr": "ADR-181",
        "id_prefix": "BAR-",
    },
    "CCS": {
        "full_name": "Constraint Conformance Signal",
        "description": "Real-time conformance score [0.0, 1.0] per turn",
        "adr": "ADR-182",
        "id_prefix": "CCS-",
    },
    "CTCHC": {
        "full_name": "Cross-Turn Coherence Hash Chain",
        "description": "Cryptographic linkage of all session turns",
        "adr": "ADR-183",
        "id_prefix": "CTCHC-",
    },
    "PoGC": {
        "full_name": "Proof of Governance Certificate",
        "description": "PQC-signed artifact proving governance was active",
        "adr": "ADR-186",
        "id_prefix": "POGC-",
    },
    "OEP": {
        "full_name": "OMNIX Evidence Package",
        "description": "Self-contained forensic ZIP for offline audit",
        "adr": "ADR-165",
        "id_prefix": "OEP-",
    },
    "PVR": {
        "full_name": "Proactive Veto Receipt",
        "description": "Anticipatory veto before request arrives",
        "adr": "ADR-174",
        "id_prefix": "PVR-",
    },

    # ── MIVP Artifacts (ADR-194) ──────────────────────────────────────────────
    "MBR": {
        "full_name": "Mandate Binding Record",
        "description": "PQC-signed artifact encoding the declared mandate, proxy guards, and objective constraints. Issued BEFORE the first agent turn (MIVP-INV-001).",
        "adr": "ADR-194",
        "id_prefix": "MBR-",
    },
    "MAS": {
        "full_name": "Mandate Alignment Score",
        "description": "Continuous [0.0, 1.0] per-turn signal measuring alignment with declared mandate vs. proxy drift (MIVP-INV-003/004)",
        "adr": "ADR-194",
        "id_prefix": "MAS-",
    },
    "MBRSeal": {
        "full_name": "MBR Seal",
        "description": "Final attestation of mandate alignment issued at session close. Triggers three-tier mandate certification (MIVP-INV-007/008/009).",
        "adr": "ADR-194",
        "id_prefix": "MBRS-",
    },
    "ProxyGuard": {
        "full_name": "Proxy Guard",
        "description": "Per-turn detector for proxy-optimization signals in agent outputs. Baseline: keyword-density scoring over forbidden proxy terms.",
        "adr": "ADR-194",
    },

    # ── Engines ───────────────────────────────────────────────────────────────
    "AVM": {
        "full_name": "Adaptive Veto Machine",
        "description": "Dynamic threshold calibration engine",
        "adr": "ADR-074",
    },
    "AGVP": {
        "full_name": "Anticipatory Governance Veto Protocol",
        "description": "Watchdog for proactive vetoes",
        "adr": "ADR-174",
    },
    "DSPP": {
        "full_name": "Dynamic Semantic Portability Protocol",
        "description": "Semantic drift management across time",
        "adr": "ADR-173",
    },
    "CES": {
        "full_name": "Continuity Eligibility Score",
        "description": "Composite health score [0–100] for runtime continuity",
        "adr": "RFC-ATF-2",
    },
    "AFG": {
        "full_name": "Authority Fragmentation Guard",
        "description": "Prevents aggregate sibling authority budget exceeding limit (default 0.90)",
        "adr": "RFC-ATF-2",
    },
    "CGE": {
        "full_name": "Counterfactual Governance Engine",
        "description": "Documents decision space with PQC-signed counterfactual alternatives",
        "adr": "ADR-178",
    },
    "GUGT": {
        "full_name": "Grand Unified Governance Theory",
        "description": "Multi-jurisdiction universal certification framework",
        "adr": "ADR-179",
    },
    "TGB": {
        "full_name": "Temporal Governance Bridge",
        "description": "Longitudinal evidence interpretability across time",
        "adr": "ADR-180",
    },
    "SAE": {
        "full_name": "Signal Admission Engine",
        "description": "Layer 0 pre-filter before governance evaluation pipeline",
        "adr": "ADR-050",
    },
    "MAR": {
        "full_name": "Monotonic Authority Reduction",
        "description": "Granted budget MUST be ≤ delegator budget (ATF-INV-001)",
        "adr": "RFC-ATF-1",
    },

    # ── Protocol Stacks ───────────────────────────────────────────────────────
    "ATF": {
        "full_name": "Agent Trust Fabric",
        "description": "6-layer governance protocol (RFC-ATF-1 through RFC-ATF-6)",
        "adr": "RFC-ATF-1",
    },
    "BEV": {
        "full_name": "Behavioral Execution Verification",
        "description": "Turn-level behavioral attestation layer (RFC-ATF-6, ADR-181/182/183)",
        "adr": "RFC-ATF-6",
    },
    "MIVP": {
        "full_name": "Mandate Integrity Verification Protocol",
        "description": "Optional governance layer for cryptographic mandate binding and per-turn alignment verification. Closes the proxy-optimization governance gap.",
        "adr": "ADR-194",
    },
    "OGR": {
        "full_name": "OMNIX Governance Runtime",
        "description": "Unified integration API for all 6 ATF layers",
        "adr": "ADR-184",
    },
    "OGI": {
        "full_name": "OMNIX Governance Intelligence",
        "description": "Domain-expert AI model fine-tuned on OMNIX corpus",
        "adr": "ADR-193",
    },
    "SAL": {
        "full_name": "Sovereign AI Layer",
        "description": "Provider-independent AI with Groq/Llama-3/Mistral fallback chain",
        "adr": "ADR-190",
    },
    "PoGR": {
        "full_name": "Proof of Governance Registry",
        "description": "Append-only public certificate store",
        "adr": "ADR-186",
    },
    "GPIL": {
        "full_name": "Governance Policy Interoperability Layer",
        "description": "Cross-domain policy contracts and interoperability",
        "adr": "RFC-ATF-3",
    },
    "UDCL": {
        "full_name": "Unified Decision Control Layer",
        "description": "Multi-layer verdict synthesis",
        "adr": "ADR-138",
    },
    "SGIP": {
        "full_name": "Semantic Governance Interoperability Protocol",
        "description": "Cross-runtime semantic alignment certification",
        "adr": "ADR-171",
    },
    "OSG": {
        "full_name": "OMNIX Settlement Gate",
        "description": "Post-execution settlement decision validation",
        "adr": "ADR-188",
    },

    # ── Cryptography ──────────────────────────────────────────────────────────
    "ML-DSA-65": {
        "full_name": "Module Lattice Digital Signature Algorithm (65-bit security)",
        "description": "NIST FIPS 204 post-quantum signature algorithm (Dilithium-3 lattice-based)",
        "adr": "RFC-ATF-1",
    },
    "Dilithium-3": {
        "full_name": "Dilithium-3",
        "description": "CRYSTALS-Dilithium lattice-based signature scheme (same as ML-DSA-65, FIPS 204)",
        "adr": "RFC-ATF-1",
    },
    "PQC": {
        "full_name": "Post-Quantum Cryptography",
        "description": "Cryptography resistant to quantum computer attacks",
        "adr": "RFC-ATF-1",
    },

    # ── DSPP Artifacts (ADR-173) ──────────────────────────────────────────────
    "TSA": {
        "full_name": "Temporal Semantic Anchor",
        "description": "Snapshot of semantic context at governance receipt issuance. Immutable.",
        "adr": "ADR-173",
    },
    "SDR": {
        "full_name": "Semantic Drift Record",
        "description": "Append-only log of detected semantic changes over time",
        "adr": "ADR-173",
    },
    "RSA": {
        "full_name": "Retroactive Semantic Assessment",
        "description": "Offline O(1) re-evaluation of historical receipts against current semantics",
        "adr": "ADR-173",
    },
}

# ── Section 2 — Canonical Verdict Tokens ─────────────────────────────────────

CANONICAL_VERDICTS: dict[str, str] = {
    "CONFORMANT":         "All constraints satisfied, agent may proceed",
    "WARNING":            "Drift approaching threshold, proceed with caution",
    "CRITICAL":           "High drift, governance intervention required",
    "HALT":               "Authority revoked, agent must stop immediately",
    "APPROVED":           "Governance gate passed",
    "BLOCKED":            "Governance gate failed — action not permitted",
    "NARROW":             "Scope narrowing applied — restricted approval",
    "HOLD":               "Session paused pending principal review",
    "REBOUND":            "Session recovered from degraded state",
    "QUARANTINE":         "Session isolated pending forensic investigation",
    "ALIGNED":            "Mandate alignment confirmed (MIVP MAS verdict)",
    "VIOLATED":           "Mandate violation detected (MIVP MAS verdict)",
    "MANDATE-BOUND":      "Tier 1 mandate certification: zero violations AND zero warnings (MIVP-INV-008)",
    "MANDATE-ALIGNED":    "Tier 2 mandate certification: zero violations, warnings allowed (MIVP-INV-009)",
    "UNCERTIFIED":        "MIVP violations recorded — mandate certification withheld",
    "ATF-BEV-COMPLIANT":  "All 6 ATF layers active, BEV layer complete (OGR-INV-001)",
    "MANDATE-BOUND":      "Tier 1 PoGC tag — pristine mandate fidelity",
    "MANDATE-ALIGNED":    "Tier 2 PoGC tag — mission-aligned despite transient warnings",
    "SESSION_HALTED":     "HTTP 422 error code returned when a halted session receives a new turn request",
    "GOVERNING_RECEIPT_EXPIRED": "HTTP 422 error code — TAR cannot be issued for expired DR",
    "INSUFFICIENT_AUTHORITY_BUDGET": "HTTP 422 error code — agent budget exhausted",
}

# ── Section 3 — Canonical Session States ──────────────────────────────────────

CANONICAL_STATES: dict[str, str] = {
    "ACTIVE":    "OGR session is open and receiving turns",
    "HALTED":    "OGR session was halted by a governance verdict",
    "SEALED":    "OGR session completed and sealed — eligible for PoGC",
    "HOT":       "Evidence lifecycle: active, full-resolution, low-latency (ELR-INV-001)",
    "WARM":      "Evidence lifecycle: compressed, medium-latency (ELR-INV-001)",
    "COLD":      "Evidence lifecycle: archived, high-latency (ELR-INV-001)",
}

# ── Section 4 — Canonical API Endpoints ───────────────────────────────────────

CANONICAL_ENDPOINTS: dict[str, str] = {
    "POST /v1/govern/session":           "Start OGR session (ADR-184)",
    "POST /v1/govern/session/{id}/turn": "Record agent turn (ADR-184)",
    "POST /v1/govern/session/{id}/close":"Seal OGR session (ADR-184)",
    "GET /v1/govern/session/{id}/proof": "Retrieve behavioral attestation chain (ADR-184)",
    "POST /v1/pogr/certify":             "Issue Proof of Governance Certificate (ADR-186/187)",
    "GET /v1/pogr/verify/{pogc_id}":     "Verify PoGC (ADR-187)",
    "GET /v1/pogr/registry":             "Browse PoG Registry (ADR-186)",
    "POST /v1/sandbox/simulate":         "Governance simulation sandbox",
}

# ── Section 5 — Regex patterns for invariant code extraction ──────────────────

INVARIANT_PATTERN = re.compile(
    r"\b(ATF|RGC|GPIL|ELR|EAP|OEP|FEA|FVP|GECR|SGIP|DSPP|AGV|SSD|FVS|CGE|GUGT|TGB|BEV|OGR|PoGR|OSG|MIVP|OGI|TAR|CDTP|PoGR|CRGC|AGVP)-INV-\d{3}\b"
)

ADR_PATTERN    = re.compile(r"\bADR-\d{1,3}\b")
RFC_PATTERN    = re.compile(r"\bRFC-ATF-\d\b")

# ── Section 6 — Live extraction from corpus ────────────────────────────────────

def extract_from_corpus() -> dict[str, Any]:
    """
    Scan all allowlisted ADR and RFC files, extract:
    - All ADR identifiers that actually exist as files
    - All RFC identifiers
    - All invariant codes found in the corpus
    - All artifact ID prefixes found (MBR-, BAR-, etc.)
    """
    allowlist_path = SCRIPTS_DIR / "corpus_allowlist.yaml"
    if not allowlist_path.exists():
        log.warning("corpus_allowlist.yaml not found — falling back to ADR directory scan")
        adr_dir = REPO_ROOT / "docs" / "adr"
        source_files = list(adr_dir.glob("ADR-*.md"))
    else:
        import yaml
        with open(allowlist_path) as f:
            al = yaml.safe_load(f)
        adr_dir = REPO_ROOT / al["allowed_sources"]["adr_directory"]
        adr_pattern = al["allowed_sources"]["adr_pattern"]
        adr_exclude = set(al["allowed_sources"].get("adr_exclude", []))
        source_files = [p for p in sorted(adr_dir.glob(adr_pattern))
                        if p.name not in adr_exclude]
        for rp in al["allowed_sources"].get("rfc_files", []):
            p = REPO_ROOT / rp
            if p.exists():
                source_files.append(p)

    found_adrs: set[str]       = set()
    found_rfcs: set[str]       = set()
    found_invariants: set[str] = set()
    found_artifact_ids: set[str] = set()

    # Artifact ID prefix pattern: MBR-HEX16, POGC-HEX16, etc.
    artifact_prefix_pat = re.compile(
        r"\b(MBR|MAS|MBRS|BAR|CCS|CTCHC|POGC|PVR|OEP|DR|TAR|RCR|AIR|DTR|TSA|SDR|RSA|OGR-SES)-[A-Z0-9]{4,16}\b"
    )

    for p in source_files:
        # ADR IDs from filenames
        m = re.match(r"(ADR-\d+)", p.name)
        if m:
            found_adrs.add(m.group(1))

        # RFC IDs from filenames
        m = re.match(r"(RFC-ATF-\d)", p.name)
        if m:
            found_rfcs.add(m.group(1))

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # Invariant codes
        for inv_code in INVARIANT_PATTERN.findall(content):
            # findall returns group(1) — the family prefix
            pass
        for m in INVARIANT_PATTERN.finditer(content):
            found_invariants.add(m.group(0))

        # ADR and RFC references in content
        for adr in ADR_PATTERN.findall(content):
            found_adrs.add(adr)
        for rfc in RFC_PATTERN.findall(content):
            found_rfcs.add(rfc)

        # Artifact ID examples
        for m in artifact_prefix_pat.finditer(content):
            found_artifact_ids.add(m.group(0))

    log.info(f"Corpus scan: {len(source_files)} files | {len(found_adrs)} ADRs | "
             f"{len(found_rfcs)} RFCs | {len(found_invariants)} invariant codes | "
             f"{len(found_artifact_ids)} artifact ID examples")

    return {
        "adr_identifiers":     sorted(found_adrs),
        "rfc_identifiers":     sorted(found_rfcs),
        "invariant_codes":     sorted(found_invariants),
        "artifact_id_examples": sorted(found_artifact_ids),
    }


# ── Section 7 — Build full ontology ───────────────────────────────────────────

def build_ontology(verbose: bool = False) -> dict[str, Any]:
    """
    Combine hardcoded canonical terms with live corpus extraction.
    Returns the full ontology as a dict.
    """
    log.info("Building OMNIX canonical ontology (ADR-193 OGI-INV-007 Gate 4)…")

    corpus_data = extract_from_corpus()

    # Invariant families — enumerate valid family prefixes for hallucination checking
    invariant_families: dict[str, dict[str, str]] = {
        "ATF":   {"adr": "RFC-ATF-1", "count": 6,  "range": "ATF-INV-001–006"},
        "TAR":   {"adr": "ADR-157",   "count": 1,  "range": "TAR-INV-006"},
        "RGC":   {"adr": "RFC-ATF-2", "count": 8,  "range": "RGC-INV-001–008"},
        "GPIL":  {"adr": "RFC-ATF-3", "count": 3,  "range": "GPIL-INV-001–003"},
        "ELR":   {"adr": "ADR-162",   "count": 4,  "range": "ELR-INV-001–004"},
        "EAP":   {"adr": "ADR-163",   "count": 7,  "range": "EAP-INV-001–007"},
        "OEP":   {"adr": "ADR-165",   "count": 6,  "range": "OEP-INV-001–006"},
        "FEA":   {"adr": "ADR-166",   "count": 5,  "range": "FEA-INV-001–005"},
        "FVP":   {"adr": "ADR-177",   "count": 1,  "range": "FVP-INV-007"},
        "GECR":  {"adr": "ADR-178",   "count": 6,  "range": "GECR-INV-001–006"},
        "SGIP":  {"adr": "ADR-171",   "count": 4,  "range": "SGIP-INV-001–004"},
        "DSPP":  {"adr": "ADR-173",   "count": 7,  "range": "DSPP-INV-001–007"},
        "AGV":   {"adr": "ADR-174",   "count": 6,  "range": "AGV-INV-001–006"},
        "SSD":   {"adr": "ADR-175",   "count": 3,  "range": "SSD-INV-001–003"},
        "FVS":   {"adr": "ADR-177",   "count": 3,  "range": "FVS-INV-001–003"},
        "CGE":   {"adr": "ADR-178",   "count": 7,  "range": "CGE-INV-001–007"},
        "GUGT":  {"adr": "ADR-179",   "count": 6,  "range": "GUGT-INV-001–006"},
        "TGB":   {"adr": "ADR-180",   "count": 5,  "range": "TGB-INV-001–005"},
        "BEV":   {"adr": "RFC-ATF-6", "count": 18, "range": "BEV-INV-001–018"},
        "OGR":   {"adr": "ADR-184",   "count": 1,  "range": "OGR-INV-001"},
        "PoGR":  {"adr": "ADR-186",   "count": 6,  "range": "PoGR-INV-001–006"},
        "OSG":   {"adr": "ADR-188",   "count": 6,  "range": "OSG-INV-001–006"},
        "MIVP":  {"adr": "ADR-194",   "count": 9,  "range": "MIVP-INV-001–009"},
        "OGI":   {"adr": "ADR-193",   "count": 10, "range": "OGI-INV-001–010"},
    }

    # Compute all valid invariant codes from family registry
    valid_invariant_codes: list[str] = []
    for family, meta in invariant_families.items():
        # Parse range to generate exact codes
        range_str = meta["range"]
        # Handle "FAMILY-INV-001–006" style ranges
        m = re.search(r"(\d+)–(\d+)$", range_str)
        if m:
            start, end = int(m.group(1)), int(m.group(2))
            for n in range(start, end + 1):
                valid_invariant_codes.append(f"{family}-INV-{n:03d}")
        else:
            # Single invariant like "FVP-INV-007"
            single_match = re.search(r"INV-(\d+)$", range_str)
            if single_match:
                valid_invariant_codes.append(f"{family}-INV-{single_match.group(1).zfill(3)}")

    # Merge corpus-discovered invariants (may have some we haven't hardcoded)
    all_invariant_codes = sorted(set(valid_invariant_codes) | set(corpus_data["invariant_codes"]))

    ontology = {
        "_meta": {
            "version": "2.0.0",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "purpose": "OGI Gate 4 hallucination detection — ADR-193 OGI-INV-007",
            "resolution": "F-C-006 — canonical ontology for hallucination evaluation",
            "total_terms": len(CANONICAL_TERMS),
            "total_invariant_codes": len(all_invariant_codes),
            "total_adr_identifiers": len(corpus_data["adr_identifiers"]),
            "total_verdict_tokens": len(CANONICAL_VERDICTS),
            "description": (
                "An OGI model output is a hallucination (Gate 4) if it references an ADR number, "
                "invariant code, RFC identifier, or canonical artifact name that does NOT appear "
                "in this file. Types 1 and 2 hallucinations (invented IDs) are auto-detectable "
                "from this ontology. Type 3 (citation mismatch) requires human spot-check."
            ),
        },

        "hallucination_detection_guide": {
            "type_1_invented_adr": {
                "description": "Model cites an ADR that does not exist (e.g., 'ADR-201')",
                "detection": "Check adr_identifiers list — any cited ADR not present is Type 1 hallucination",
                "auto_checkable": True,
            },
            "type_2_invented_invariant": {
                "description": "Model cites an invariant code not in the ontology (e.g., 'MIVP-INV-011')",
                "detection": "Check valid_invariant_codes list — any cited code not present is Type 2 hallucination",
                "auto_checkable": True,
            },
            "type_3_citation_mismatch": {
                "description": "Model cites a real ADR for a claim it does not make",
                "detection": "Requires human spot-check of random 10% of test responses",
                "auto_checkable": False,
                "spot_check_target": "10% of test responses, flag if >5% contain citation mismatches",
            },
        },

        "canonical_terms": CANONICAL_TERMS,
        "canonical_verdicts": CANONICAL_VERDICTS,
        "canonical_session_states": CANONICAL_STATES,
        "canonical_api_endpoints": CANONICAL_ENDPOINTS,

        "invariant_families": invariant_families,
        "valid_invariant_codes": all_invariant_codes,
        "corpus_discovered_invariants": sorted(corpus_data["invariant_codes"]),

        "adr_identifiers": corpus_data["adr_identifiers"],
        "rfc_identifiers": corpus_data["rfc_identifiers"],
        "artifact_id_examples": corpus_data["artifact_id_examples"],

        "pogc_tags": {
            "MANDATE-BOUND": {
                "tier": 1,
                "condition": "turns_in_violation = 0 AND turns_in_warning = 0",
                "semantics": "Pristine mandate fidelity throughout session",
                "invariant": "MIVP-INV-008",
                "adr": "ADR-194",
            },
            "MANDATE-ALIGNED": {
                "tier": 2,
                "condition": "turns_in_violation = 0 AND turns_in_warning > 0",
                "semantics": "Mission-aligned despite transient warning-level drift",
                "invariant": "MIVP-INV-009",
                "adr": "ADR-194",
                "mutual_exclusivity": "Cannot appear on same PoGC as MANDATE-BOUND",
            },
            "ATF-BEV-COMPLIANT": {
                "tier": None,
                "condition": "All 6 ATF layers active (OGR-INV-001)",
                "semantics": "Full ATF + BEV compliance",
                "invariant": "OGR-INV-001",
                "adr": "ADR-184",
            },
        },

        "mandate_certification_tiers": {
            "1": {
                "tag": "MANDATE-BOUND",
                "description": "Pristine: zero violations AND zero warnings",
                "invariant": "MIVP-INV-008",
            },
            "2": {
                "tag": "MANDATE-ALIGNED",
                "description": "Aligned: zero violations, warnings allowed",
                "invariant": "MIVP-INV-009",
            },
            "3": {
                "tag": "UNCERTIFIED",
                "description": "Violations recorded — no mandate PoGC tag issued",
                "invariant": "MIVP-INV-005",
            },
        },

        "non_existent_terms": {
            "description": "Terms that OGI MUST NOT invent. If a model defines these, it is hallucinating.",
            "examples": [
                "OQEP", "ATF-INV-099", "BEV-INV-099", "MIVP-INV-011",
                "OGI-INV-011", "ADR-201", "RFC-ATF-7", "RFC-ATF-8",
                "MANDATE-CERTIFIED", "MANDATE-VERIFIED", "MANDATE-CONFIRMED",
            ],
        },
    }

    if verbose:
        log.info(f"Ontology built: {len(CANONICAL_TERMS)} canonical terms")
        log.info(f"  Invariant families: {len(invariant_families)}")
        log.info(f"  Valid invariant codes: {len(all_invariant_codes)}")
        log.info(f"  ADR identifiers: {len(corpus_data['adr_identifiers'])}")
        log.info(f"  RFC identifiers: {len(corpus_data['rfc_identifiers'])}")
        log.info(f"  Verdict tokens: {len(CANONICAL_VERDICTS)}")
        log.info(f"  PoGC tags: {len(ontology['pogc_tags'])}")

    return ontology


# ── Section 8 — CLI ────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "OMNIX OGI Canonical Ontology Generator — ADR-193 OGI-INV-007 Gate 4\n"
            "Generates ontology.json for hallucination detection during model evaluation."
        )
    )
    parser.add_argument(
        "--output", type=str,
        default=str(OUTPUT_DIR / "ontology.json"),
        help="Output path for ontology.json (default: scripts/fine_tuning/output/ontology.json)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Build ontology but do not write to disk — print summary only",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    ontology = build_ontology(verbose=args.verbose)

    if args.dry_run:
        log.info("DRY RUN — ontology built but not written")
        log.info(f"  Terms: {len(ontology['canonical_terms'])}")
        log.info(f"  Invariant codes: {len(ontology['valid_invariant_codes'])}")
        log.info(f"  ADR IDs: {len(ontology['adr_identifiers'])}")
        print(json.dumps(ontology["_meta"], indent=2))
        return

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ontology, f, indent=2, ensure_ascii=False)

    log.info("═" * 60)
    log.info(f"Ontology written → {output_path}")
    log.info(f"  Canonical terms: {len(ontology['canonical_terms'])}")
    log.info(f"  Valid invariant codes: {len(ontology['valid_invariant_codes'])}")
    log.info(f"  ADR identifiers: {len(ontology['adr_identifiers'])}")
    log.info(f"  PoGC tags: {len(ontology['pogc_tags'])}")
    log.info("Gate 4 (hallucination_rate ≤ 3%) can now execute.")
    log.info("═" * 60)


if __name__ == "__main__":
    main()
