#!/usr/bin/env python3
"""
OMNIX Governance Intelligence (OGI) — Corpus Preparation Pipeline
ADR-193 · OGI-INV-001 through OGI-INV-007

Converts OMNIX ADRs, RFCs, and architecture documentation into a
Llama-3 chat JSONL training corpus for supervised fine-tuning.

Architecture:
  ingest → parse → chunk → generate → dedup → sanitize → split → QA gate → output

Usage:
  python prepare_corpus.py [--dry-run] [--category DEF,SCN,INV] [--max-examples N]

Outputs (scripts/fine_tuning/output/):
  train.jsonl           — 80% training split
  val.jsonl             — 10% validation split
  test.jsonl            — 10% test split (never seen during training)
  eval_suite.jsonl      — Fixed evaluation suite for gate checking (OGI-007)
  manifest.json         — Reproducibility record (OGI-INV-007)
  ontology.json         — Canonical OMNIX term registry
  rejected_samples.jsonl — All rejected examples with rejection reason

Author: OMNIX QUANTUM LTD · Harold Nunes
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import random
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Generator, Optional

import yaml

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("ogi.corpus")

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT    = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR  = Path(__file__).resolve().parent
OUTPUT_DIR   = SCRIPTS_DIR / "output"
ALLOWLIST    = SCRIPTS_DIR / "corpus_allowlist.yaml"
SYSTEM_PROMPT_FILE = SCRIPTS_DIR / "ogi_system_prompt.txt"
TRAINING_CFG = SCRIPTS_DIR / "training_config.yaml"

# ── OMNIX Ontology — Canonical term registry ──────────────────────────────────

OMNIX_ONTOLOGY: dict[str, str] = {
    # Core Artifacts
    "DR":    "Delegation Receipt — cryptographic proof of authority transfer between agents",
    "TAR":   "Temporal Admissibility Record — proves a DR was valid at nanosecond of execution",
    "RCR":   "Runtime Continuity Record — continuous health snapshot during long-running tasks",
    "BAR":   "Behavioral Anchor Record — per-turn PQC-signed attestation of agent output (ADR-181)",
    "CCS":   "Constraint Conformance Signal — real-time conformance score [0.0, 1.0] (ADR-182)",
    "CTCHC": "Cross-Turn Coherence Hash Chain — cryptographic linkage of all session turns (ADR-183)",
    "PoGC":  "Proof of Governance Certificate — signed artifact proving governance was active (ADR-186)",
    "AIR":   "Agent Identity Record — immutable binding of agent to human principal",
    "DTR":   "Domain Translation Receipt — enables cross-domain authority transfer",
    "OEP":   "OMNIX Evidence Package — self-contained forensic ZIP (ADR-165)",
    "PVR":   "Proactive Veto Receipt — anticipatory veto before request arrives (ADR-174)",
    # Engines
    "AVM":   "Adaptive Veto Machine — dynamic threshold calibration engine",
    "AGVP":  "Anticipatory Governance Veto Protocol — watchdog for proactive vetoes (ADR-174)",
    "DSPP":  "Dynamic Semantic Portability Protocol — semantic drift management (ADR-173)",
    "CES":   "Continuity Eligibility Score — composite health score [0–100] for RGC",
    "AFG":   "Authority Fragmentation Guard — prevents aggregate budget > 0.90 (RGC-INV-004)",
    "CGE":   "Counterfactual Governance Engine — documents decision space with alternatives (ADR-178)",
    "GUGT":  "Grand Unified Governance Theory — multi-jurisdiction certification (ADR-179)",
    "TGB":   "Temporal Governance Bridge — longitudinal evidence interpretability (ADR-180)",
    "SAE":   "Signal Admission Engine — Layer 0 pre-filter before evaluation pipeline",
    # Protocol Stack
    "ATF":   "Agent Trust Fabric — 6-layer governance protocol (RFC-ATF-1 through RFC-ATF-6)",
    "BEV":   "Behavioral Execution Verification — turn-level behavioral attestation layer (RFC-ATF-6)",
    "OGR":   "OMNIX Governance Runtime — unified integration API for all 6 ATF layers (ADR-184)",
    "OGI":   "OMNIX Governance Intelligence — domain-expert AI model trained on OMNIX corpus (ADR-193)",
    "SAL":   "Sovereign AI Layer — provider-independent AI with Groq/Mistral fallback (ADR-190)",
    "PoGR":  "Proof of Governance Registry — append-only public certificate store (ADR-186)",
    "UDCL":  "Unified Decision Control Layer — multi-layer verdict synthesis",
    "GPIL":  "Governance Policy Interoperability Layer — cross-domain policy contracts (RFC-ATF-3)",
    # MIVP Artifacts (ADR-194)
    "MBR":          "Mandate Binding Record — PQC-signed artifact encoding declared mandate, proxy guards, and objective constraints. Issued BEFORE turn 1 (MIVP-INV-001).",
    "MAS":          "Mandate Alignment Score — continuous [0.0, 1.0] per-turn signal measuring alignment with declared mandate vs. proxy drift (MIVP-INV-003/004, ADR-194).",
    "MBRSeal":      "MBR Seal — final attestation of mandate alignment at session close; triggers three-tier mandate certification (MIVP-INV-007/008/009, ADR-194).",
    "ProxyGuard":   "Proxy Guard — per-turn keyword-density detector for proxy-optimization signals in agent outputs (ADR-194).",
    "MIVP":         "Mandate Integrity Verification Protocol — optional L6 governance layer for cryptographic mandate binding and per-turn alignment verification. Closes proxy-optimization gap not detectable by BEV (ADR-194).",
    # MIVP Mandate Certification Tiers
    "MANDATE-BOUND":   "Tier 1 MIVP PoGC tag — pristine mandate fidelity: turns_in_violation = 0 AND turns_in_warning = 0 (MIVP-INV-008). Mutually exclusive with MANDATE-ALIGNED.",
    "MANDATE-ALIGNED": "Tier 2 MIVP PoGC tag — mission-aligned: turns_in_violation = 0 AND turns_in_warning > 0 (MIVP-INV-009). Mutually exclusive with MANDATE-BOUND.",
    "UNCERTIFIED":     "Tier 3 MIVP outcome — mandate violations recorded: turns_in_violation > 0. Both higher tier tags withheld. Enforcement: MIVP-INV-005.",
    # Verdicts
    "CONFORMANT": "All constraints satisfied, agent may proceed (CCS layer, BEV verdict)",
    "WARNING":    "Drift approaching threshold, proceed with caution. Also: MAS WARNING when MAS < mas_warn_threshold (default 0.65).",
    "CRITICAL":   "High drift, governance intervention required",
    "HALT":       "Authority revoked, agent must stop immediately (BEV-INV-008). Also: MIVP HALT when MAS < mas_halt_threshold (default 0.30, MIVP-INV-005).",
    "APPROVED":   "Governance gate passed",
    "BLOCKED":    "Governance gate failed — action not permitted",
    # Mandate vs. Constraint (G-002 — ADR-194)
    "constraint": "What the agent MUST NOT do — negative bound on action space monitored by CCS (ADR-182). Different from mandate.",
    "mandate":    "What the agent MUST optimize for — positive objective monitored by MIVP MAS (ADR-194). Different from constraint.",
    # Cryptography
    "ML-DSA-65": "NIST FIPS 204 post-quantum signature algorithm (Dilithium-3 lattice-based)",
    "PQC":        "Post-Quantum Cryptography — cryptography resistant to quantum attacks",
    "MAR":        "Monotonic Authority Reduction — granted budget ≤ delegator budget (ATF-INV-001)",
}

# ── Invariant Registry — extracted from ADRs/RFCs ────────────────────────────

INVARIANT_REGISTRY: dict[str, dict] = {
    "ATF-INV-001": {
        "family": "ATF", "adr": "RFC-ATF-1 §7.1",
        "description": "Monotonic Authority Reduction (MAR): granted budget MUST be ≤ delegator budget. Authority can only decrease through delegation, never increase.",
        "consequence": "Any delegation that would grant more authority than the delegator holds is rejected at issuance time.",
        "counterexample": "Agent A with budget 0.60 cannot delegate 0.65 to Agent B. The receipt would be rejected.",
    },
    "ATF-INV-002": {
        "family": "ATF", "adr": "RFC-ATF-1 §6.1",
        "description": "Acyclicity: the trust lattice MUST be a Directed Acyclic Graph. No agent may appear as both ancestor and descendant of itself.",
        "consequence": "Circular delegation chains are structurally impossible.",
        "counterexample": "A → B → C → A would form a cycle and is rejected at A→B issuance.",
    },
    "ATF-INV-003": {
        "family": "ATF", "adr": "RFC-ATF-1 §7.3",
        "description": "Chain Root Consistency: all receipts in a delegation chain MUST share the same chain_root_id.",
        "consequence": "Receipts from different chains cannot be mixed to construct synthetic authority.",
        "counterexample": "Combining DR from chain root X with DR from chain root Y is rejected at verification.",
    },
    "ATF-INV-004": {
        "family": "ATF", "adr": "RFC-ATF-1 §7.5",
        "description": "Content Hash Immutability: receipt fields are immutable after PQC signing. Any field modification invalidates the signature.",
        "consequence": "Tampering with any receipt field is detectable offline.",
        "counterexample": "Changing 'budget: 0.60' to 'budget: 0.80' in a signed receipt breaks the Dilithium-3 signature.",
    },
    "ATF-INV-005": {
        "family": "ATF", "adr": "ADR-157",
        "description": "Temporal Non-Future-Dating: execution timestamp MUST be ≤ current time at verification.",
        "consequence": "Receipts cannot be pre-dated to claim past authority.",
        "counterexample": "A receipt with execution_timestamp = '2026-12-01' verified on 2026-05-25 is rejected.",
    },
    "ATF-INV-006": {
        "family": "ATF", "adr": "RFC-ATF-1 §7.6",
        "description": "Independent Verifiability: any receipt MUST be verifiable offline using only the receipt contents and the OMNIX root public key. No platform access required.",
        "consequence": "Regulators and auditors can verify governance evidence without OMNIX being available.",
        "counterexample": "A receipt that requires a live API call to verify fails this invariant.",
    },
    "TAR-INV-006": {
        "family": "ATF", "adr": "ADR-157 rev.2",
        "description": "Staleness Bound: maximum DR lifetime is 86,400 seconds (24 hours). This is a non-overridable compiled constant.",
        "consequence": "No agent can hold permanent authority. All authority expires within 24 hours and must be renewed.",
        "counterexample": "A DR with ttl_seconds = 172800 (48 hours) is rejected at issuance.",
    },
    "RGC-INV-001": {
        "family": "RGC", "adr": "RFC-ATF-2 §7.3",
        "description": "TAR Anchoring: every Runtime Continuity Record (RCR) MUST be anchored to a valid Temporal Admissibility Record (TAR).",
        "consequence": "Continuity without temporal proof is structurally invalid.",
        "counterexample": "An RCR generated without a preceding TAR is rejected.",
    },
    "RGC-INV-002": {
        "family": "RGC", "adr": "RFC-ATF-2 §6.4",
        "description": "CES Determinism: the Continuity Eligibility Score MUST be computed using the protocol-fixed formula: CES = w_T·T + w_B·B + w_D·D + w_I·I with fixed weights.",
        "consequence": "CES cannot be gamed by choosing different weight combinations.",
        "counterexample": "Using custom weights to inflate CES above threshold is rejected at audit.",
    },
    "RGC-INV-003": {
        "family": "RGC", "adr": "RFC-ATF-2 §10.5",
        "description": "HALT Integrity: CES < 10 MUST terminate execution immediately and revoke all sub-delegations.",
        "consequence": "A critically unhealthy agent cannot continue operating, regardless of task priority.",
        "counterexample": "Overriding a HALT verdict to continue execution violates RGC-INV-003 and invalidates all subsequent receipts.",
    },
    "RGC-INV-004": {
        "family": "RGC", "adr": "RFC-ATF-2 §8.4",
        "description": "AFG Fragmentation: aggregate authority budget across sibling agents cannot exceed the AFG limit (default 0.90).",
        "consequence": "Authority cannot be fragmented across many agents to circumvent individual budget limits.",
        "counterexample": "Five agents each holding 0.20 budget sum to 1.00, exceeding the 0.90 AFG limit.",
    },
    "BEV-INV-001": {
        "family": "BEV", "adr": "ADR-181",
        "description": "Every agent turn MUST produce a Behavioral Anchor Record (BAR) before output delivery. BAR is a prerequisite for turn execution.",
        "consequence": "An agent turn without a BAR is structurally incomplete and cannot be counted as governed.",
        "counterexample": "Delivering output before the BAR is signed violates BEV-INV-001.",
    },
    "BEV-INV-008": {
        "family": "BEV", "adr": "ADR-182",
        "description": "Cumulative drift > 35% (configurable threshold, default 35%) MUST trigger an autonomous HALT verdict from the CCS engine.",
        "consequence": "Behavioral drift is self-enforcing — the CCS engine halts the agent without human intervention.",
        "counterexample": "An agent with cumulative_drift = 0.38 on turn 7 receives HALT; it cannot proceed to turn 8.",
    },
    "BEV-INV-010": {
        "family": "BEV", "adr": "ADR-183",
        "description": "CTCHC genesis hash MUST be seeded by the governing_receipt_id, making the hash chain cryptographically inseparable from its authorization.",
        "consequence": "A CTCHC cannot be transferred to a different governance receipt without breaking the chain.",
        "counterexample": "Reusing a CTCHC from session A in session B fails genesis hash verification.",
    },
    "BEV-INV-013": {
        "family": "BEV", "adr": "ADR-183",
        "description": "The CTCHC seal MUST cover every link from genesis to the final turn. Partial seals are rejected.",
        "consequence": "Retroactive removal of turns from the chain is detectable.",
        "counterexample": "Sealing turns 1-10 but excluding turn 5 produces a broken chain that fails offline verification.",
    },
    "OGR-INV-001": {
        "family": "OGR", "adr": "ADR-184",
        "description": "All 6 ATF layers (L0–L5) MUST be simultaneously active for a session to carry the ATF-BEV-Compliant certification.",
        "consequence": "Partial ATF compliance is not recognized. A session with only 4 layers active is not compliant.",
        "counterexample": "A session with BEV disabled is not ATF-BEV-Compliant regardless of other layer status.",
    },
    "PoGR-INV-001": {
        "family": "PoGR", "adr": "ADR-186",
        "description": "Every PoG Certificate MUST be backed by a sealed OGR session (status = SEALED). Certificates cannot be issued for ACTIVE or HALTED sessions.",
        "consequence": "A PoGC represents completed, sealed governance — not ongoing or failed governance.",
        "counterexample": "Requesting a PoGC for an ACTIVE session returns 422 Unprocessable Entity.",
    },
    "PoGR-INV-003": {
        "family": "PoGR", "adr": "ADR-186",
        "description": "PoGC verification MUST require zero OMNIX platform access. The certificate must be self-verifiable using only its content and the OMNIX public key.",
        "consequence": "PoGCs are permanently verifiable even if OMNIX ceases to operate.",
        "counterexample": "A PoGC that requires a live /verify API call to confirm fails PoGR-INV-003.",
    },
    "OGI-INV-001": {
        "family": "OGI", "adr": "ADR-193",
        "description": "Every file contributing to the OGI training corpus MUST appear in corpus_allowlist.yaml. No implicit inclusion.",
        "consequence": "Sensitive files (secrets, NDAs, partner contracts) are structurally excluded from training.",
        "counterexample": "A file not in corpus_allowlist.yaml that somehow reaches the JSONL pipeline is rejected at QA gate.",
    },
    "OGI-INV-008": {
        "family": "OGI", "adr": "ADR-193",
        "description": "No OGI model version may be deployed without passing all 5 evaluation gates (OGI-007).",
        "consequence": "Underperforming models cannot reach production, protecting OMNIX's governance accuracy reputation.",
        "counterexample": "A model scoring 0.78 on scenario verdicts (below 0.85 gate) is blocked from SAL deployment.",
    },
}

# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class TrainingExample:
    category: str          # DEF, SCN, INV, API, TRC, CMP, REG, FOR, RTR, TRM, EXB, SRC
    source_adr: str        # e.g. "ADR-184" or "RFC-ATF-2"
    messages: list[dict]   # Llama-3 chat format
    fingerprint: str = ""  # SHA-256 of messages content

    def compute_fingerprint(self) -> str:
        content = json.dumps(self.messages, sort_keys=True, ensure_ascii=False)
        self.fingerprint = hashlib.sha256(content.encode()).hexdigest()
        return self.fingerprint

    def to_jsonl(self) -> str:
        return json.dumps({"messages": self.messages}, ensure_ascii=False)


@dataclass
class RejectedSample:
    reason: str
    category: str
    source_adr: str
    fingerprint: str


@dataclass
class CorpusManifest:
    version: str = "1.0.0"
    generated_at: str = ""
    repo_root: str = ""
    source_file_hashes: dict = field(default_factory=dict)
    random_seed: int = 42
    total_examples: int = 0
    train_count: int = 0
    val_count: int = 0
    test_count: int = 0
    rejected_count: int = 0
    category_distribution: dict = field(default_factory=dict)
    together_ai_job_id: str = ""  # filled after training


# ── Corpus configuration ───────────────────────────────────────────────────────

def load_config() -> dict:
    with open(TRAINING_CFG) as f:
        return yaml.safe_load(f)


def load_allowlist() -> dict:
    with open(ALLOWLIST) as f:
        return yaml.safe_load(f)


def load_system_prompt() -> str:
    with open(SYSTEM_PROMPT_FILE) as f:
        return f.read().strip()


# ── Security: sanitization ────────────────────────────────────────────────────

def _sanitize(text: str, secret_patterns: list[str], pii_patterns: list[str]) -> tuple[str, bool]:
    """
    Redact secrets and PII from text.
    Returns (sanitized_text, was_modified).
    OGI-INV-004: no secret or PII may appear in training data.
    """
    modified = False
    for pat in secret_patterns:
        cleaned, n = re.subn(pat, "[REDACTED-SECRET]", text)
        if n:
            modified = True
            text = cleaned
    for pat in pii_patterns:
        cleaned, n = re.subn(pat, "[REDACTED-PII]", text)
        if n:
            modified = True
            text = cleaned
    return text, modified


def _has_secret(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text) for p in patterns)


# ── ADR / RFC Parser ──────────────────────────────────────────────────────────

@dataclass
class ParsedDocument:
    path: Path
    identifier: str    # "ADR-184" or "RFC-ATF-2"
    title: str
    status: str
    date: str
    related: list[str]
    sections: dict[str, str]   # section_title → content
    full_text: str
    file_hash: str


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def parse_markdown_document(path: Path) -> Optional[ParsedDocument]:
    """Parse an ADR or RFC markdown file into structured sections."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        log.warning(f"Cannot read {path}: {e}")
        return None

    lines = text.splitlines()
    if not lines:
        return None

    # Extract identifier and title from first heading
    title_line = lines[0].strip("# ").strip()
    # e.g. "ADR-184 — OMNIX Governance Runtime (OGR)"
    id_match = re.match(r"(ADR-\d+|RFC-ATF-\d+)", title_line)
    identifier = id_match.group(1) if id_match else path.stem

    # Extract metadata
    status = _extract_field(text, r"\*\*Status:\*\*\s*(.+)")
    date   = _extract_field(text, r"\*\*Date:\*\*\s*(.+)")
    related_raw = _extract_field(text, r"\*\*Related:\*\*\s*(.+)")
    related = re.findall(r"ADR-\d+|RFC-ATF-\d+", related_raw) if related_raw else []

    # Split into sections by ## headings
    sections: dict[str, str] = {}
    current_section = "preamble"
    current_lines: list[str] = []

    for line in lines[1:]:
        if line.startswith("## "):
            if current_lines:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections[current_section] = "\n".join(current_lines).strip()

    return ParsedDocument(
        path=path,
        identifier=identifier,
        title=title_line,
        status=status or "Unknown",
        date=date or "Unknown",
        related=related,
        sections=sections,
        full_text=text,
        file_hash=_file_sha256(path),
    )


def _extract_field(text: str, pattern: str) -> Optional[str]:
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None


# ── Example Generators (12 categories) ───────────────────────────────────────

def _make_example(category: str, source: str, user: str, assistant: str,
                  system_prompt: str) -> TrainingExample:
    ex = TrainingExample(
        category=category,
        source_adr=source,
        messages=[
            {"role": "system",    "content": system_prompt},
            {"role": "user",      "content": user},
            {"role": "assistant", "content": assistant},
        ],
    )
    ex.compute_fingerprint()
    return ex


def gen_DEF(doc: ParsedDocument, system_prompt: str) -> Generator[TrainingExample, None, None]:
    """DEF — Normative definitions for canonical terms found in the document."""
    found_terms = [t for t in OMNIX_ONTOLOGY if t in doc.full_text]
    for term in found_terms[:3]:  # cap per document
        definition = OMNIX_ONTOLOGY[term]
        yield _make_example(
            "DEF", doc.identifier,
            user=f"What is {term} in the OMNIX protocol?",
            assistant=(
                f"**{term}** — {definition}.\n\n"
                f"This artifact is defined in the OMNIX Agent Trust Fabric protocol. "
                f"It is part of the governance receipt chain that enables cryptographically "
                f"verifiable, offline-auditable decision governance (per {doc.identifier})."
            ),
            system_prompt=system_prompt,
        )


def gen_SRC(doc: ParsedDocument, system_prompt: str) -> Generator[TrainingExample, None, None]:
    """SRC — Source location: which ADR/RFC defines a concept."""
    if "Decision" in doc.sections:
        decision_excerpt = doc.sections["Decision"][:300].replace("\n", " ").strip()
        yield _make_example(
            "SRC", doc.identifier,
            user=f"Which document defines the architecture introduced in {doc.identifier}?",
            assistant=(
                f"**{doc.identifier}** — *{doc.title}* — defines this architecture.\n\n"
                f"**Status:** {doc.status}\n"
                f"**Date:** {doc.date}\n"
                f"**Related:** {', '.join(doc.related) if doc.related else 'None specified'}\n\n"
                f"**Key Decision (excerpt):** {decision_excerpt}…\n\n"
                f"The full specification is in `docs/adr/{doc.path.name}`."
            ),
            system_prompt=system_prompt,
        )


def gen_INV(doc: ParsedDocument, system_prompt: str) -> Generator[TrainingExample, None, None]:
    """INV — Invariant explanation with counterexample."""
    relevant_invariants = [
        (code, inv) for code, inv in INVARIANT_REGISTRY.items()
        if doc.identifier in inv["adr"] or code.split("-")[0] in doc.full_text
    ]
    for code, inv in relevant_invariants[:4]:
        yield _make_example(
            "INV", doc.identifier,
            user=f"Explain {code} and give a concrete counterexample of what would violate it.",
            assistant=(
                f"## {code} — {inv['family']} Family\n\n"
                f"**Defined in:** {inv['adr']}\n\n"
                f"**Invariant:** {inv['description']}\n\n"
                f"**Consequence of violation:** {inv['consequence']}\n\n"
                f"**Counterexample:** {inv['counterexample']}\n\n"
                f"This invariant is enforced at the protocol level and cannot be overridden "
                f"by configuration. Any receipt, session, or verdict that violates it is "
                f"rejected without appeal."
            ),
            system_prompt=system_prompt,
        )


def gen_SCN(doc: ParsedDocument, system_prompt: str) -> Generator[TrainingExample, None, None]:
    """SCN — Scenario to governance verdict mapping."""
    # Only generate for documents with verdict-relevant content
    verdict_keywords = ["HALT", "CONFORMANT", "WARNING", "CRITICAL", "BLOCKED", "APPROVED"]
    if not any(kw in doc.full_text for kw in verdict_keywords):
        return

    scenarios = [
        {
            "scenario": (
                f"An AI agent governed under {doc.identifier} completes turn 5 with "
                f"cumulative drift at 0.38 (above the 0.35 BEV-INV-008 threshold). "
                f"The governing receipt is valid and the CTCHC chain is intact."
            ),
            "verdict": "HALT",
            "reasoning": (
                "BEV-INV-008 mandates an autonomous HALT when cumulative drift exceeds 35%. "
                "At 0.38 (38%), the CCS engine emits a HALT verdict regardless of other factors. "
                "The agent cannot proceed to turn 6 without a new governance session."
            ),
        },
        {
            "scenario": (
                f"Agent A with authority budget 0.70 attempts to delegate 0.75 to Agent B "
                f"in the {doc.identifier} governance context."
            ),
            "verdict": "BLOCKED",
            "reasoning": (
                "ATF-INV-001 (Monotonic Authority Reduction) prohibits delegating more budget "
                "than the delegator holds. 0.75 > 0.70 — the Delegation Receipt is rejected at "
                "issuance. This is a structural invariant, not a threshold — there is no configuration "
                "that permits it."
            ),
        },
    ]

    for s in scenarios:
        yield _make_example(
            "SCN", doc.identifier,
            user=f"Evaluate this governance scenario and give a verdict:\n\n{s['scenario']}",
            assistant=(
                f"**Verdict: {s['verdict']}**\n\n"
                f"**Reasoning:** {s['reasoning']}\n\n"
                f"**Applicable invariant(s):** "
                + ("BEV-INV-008 (ADR-182)" if "drift" in s["scenario"] else "ATF-INV-001 (RFC-ATF-1 §7.1)")
            ),
            system_prompt=system_prompt,
        )


def gen_API(doc: ParsedDocument, system_prompt: str) -> Generator[TrainingExample, None, None]:
    """API — OGR session lifecycle procedures."""
    if "184" not in doc.identifier and "OGR" not in doc.full_text:
        return

    yield _make_example(
        "API", doc.identifier,
        user="Walk me through the complete OGR session lifecycle for a governed AI agent.",
        assistant=(
            "## OGR Session Lifecycle (ADR-184)\n\n"
            "A complete governed session has 4 stages:\n\n"
            "### 1. Start — `POST /v1/govern/session/start`\n"
            "- Provide `governing_receipt_id` (pre-existing PQC-signed governance receipt)\n"
            "- OGR validates the receipt and activates all 6 ATF layers simultaneously (OGR-INV-001)\n"
            "- CTCHC genesis block is created, seeded by `governing_receipt_id` (BEV-INV-010)\n"
            "- Returns: `session_id`, `chain_genesis_hash`\n\n"
            "### 2. Turn — `POST /v1/govern/session/{id}/turn`\n"
            "For each agent output:\n"
            "- BAR is generated and PQC-signed (BEV-INV-001 — mandatory before delivery)\n"
            "- CCS score [0.0–1.0] computed against governing receipt constraints\n"
            "- CTCHC link appended — hash-chaining current turn to all previous\n"
            "- Verdict returned: CONFORMANT / WARNING / CRITICAL / HALT\n"
            "- If `should_halt: true` → agent MUST stop, output withheld\n\n"
            "### 3. Close — `POST /v1/govern/session/{id}/close`\n"
            "- CTCHC sealed over all turns from genesis to final (BEV-INV-013)\n"
            "- PQC signature applied to the seal\n"
            "- Session status → SEALED (immutable)\n\n"
            "### 4. Proof — `GET /v1/govern/session/{id}/proof`\n"
            "- Returns complete Behavioral Attestation Chain\n"
            "- Self-contained, offline-verifiable (ATF-INV-006)\n"
            "- This proof package can be submitted for PoGC issuance (ADR-186)\n\n"
            "**Note:** Skipping any stage produces an incomplete chain. "
            "An unsealed session cannot receive a Proof of Governance Certificate."
        ),
        system_prompt=system_prompt,
    )


def gen_TRC(doc: ParsedDocument, system_prompt: str) -> Generator[TrainingExample, None, None]:
    """TRC — Cross-layer traceability."""
    if not any(layer in doc.full_text for layer in ["L0", "L1", "L2", "ATF-INV", "chain_root"]):
        return

    yield _make_example(
        "TRC", doc.identifier,
        user="Trace a single AI agent decision through all 6 ATF layers in OMNIX.",
        assistant=(
            "## ATF Cross-Layer Trace for a Single Agent Decision\n\n"
            "**L0 — Human Authority Root (AIR)**\n"
            "The decision originates with a human principal who holds the root authority. "
            "An Agent Identity Record (AIR) binds the agent to this human. "
            "This is the unmovable trust anchor of the entire chain.\n\n"
            "**L1 — Delegation (DR)**\n"
            "The human delegates authority to the agent via a Delegation Receipt (DR), "
            "reducing budget per ATF-INV-001 (MAR). The DR is PQC-signed.\n\n"
            "**L2 — Temporal Admissibility (TAR)**\n"
            "Before execution, a Temporal Admissibility Record proves the DR was valid "
            "at the exact nanosecond of action. Max TTL is 86,400s (TAR-INV-006).\n\n"
            "**L3 — Runtime Continuity (RCR + CES)**\n"
            "During execution, the Continuity Eligibility Score monitors agent health. "
            "CES < 10 triggers HALT immediately (RGC-INV-003).\n\n"
            "**L4 — Execution Gate (BAR + CCS + CTCHC)**\n"
            "Each agent output produces a BAR (BEV-INV-001), a CCS conformance score, "
            "and a CTCHC hash link. Drift >35% → HALT (BEV-INV-008).\n\n"
            "**L5 — Immutable Evidence (OEP)**\n"
            "All artifacts are archived in an OMNIX Evidence Package (OEP), "
            "self-contained and offline-verifiable (ATF-INV-006, OEP-INV-001).\n\n"
            "**Result:** The entire decision is traceable from human authority to "
            "executed output, with PQC-signed proof at every layer."
        ),
        system_prompt=system_prompt,
    )


def gen_CMP(system_prompt: str) -> list[TrainingExample]:
    """CMP — Competitive analysis: OMNIX vs alternatives."""
    examples = []
    comparisons = [
        {
            "competitor": "CLARIXO Continuity Governance",
            "claim": "provides stateful agent continuity tracking",
            "gap": (
                "CLARIXO covers L3/L4 continuity concepts only. It provides no cryptographic binding, "
                "no formal invariants, no PQC signing, and no receipt architecture. "
                "An auditor cannot verify CLARIXO governance evidence without platform access. "
                "OMNIX satisfies ATF-INV-006 (Independent Verifiability); CLARIXO does not."
            ),
        },
        {
            "competitor": "MTCP (Ahmad A.)",
            "claim": "behavioral measurement via empirical model evaluation",
            "gap": (
                "MTCP measures behavior empirically but provides no cryptographic binding between "
                "measurements and the policy that authorized the agent. There is no receipt architecture, "
                "no hash chain, and no proactive veto integration. OMNIX's BEV layer (ADR-181/182/183) "
                "produces PQC-signed per-turn attestations linked to the governing receipt — "
                "a structural capability MTCP cannot replicate."
            ),
        },
        {
            "competitor": "VeriSigil",
            "claim": "governance specifications as contracts",
            "gap": (
                "VeriSigil defines governance as contracts but provides no runtime attestation, "
                "no hash chain, and no post-quantum cryptographic sealing. "
                "Contracts without execution-time proof are audit statements, not governance receipts. "
                "OMNIX's GECR-INV-001 (Control-Receipt Atomicity) ensures that the authorization "
                "and the proof are a single atomic event — a structural property VeriSigil cannot match."
            ),
        },
    ]

    for c in comparisons:
        examples.append(_make_example(
            "CMP", "ADR-184",
            user=f"How does OMNIX differ from {c['competitor']}, which {c['claim']}?",
            assistant=(
                f"**{c['competitor']}** has genuine capabilities, but there are structural gaps "
                f"when compared to the OMNIX ATF stack:\n\n{c['gap']}\n\n"
                f"None of the alternative frameworks produce: "
                f"(1) receipt-bound behavioral attestation, "
                f"(2) post-quantum cryptographic sealing on every turn artifact, "
                f"(3) cross-turn coherence proof linked to a governing receipt, or "
                f"(4) anticipatory veto integration (CCS → AGVP loop). "
                f"These are defined as the four capabilities OMNIX uniquely provides (ADR-184)."
            ),
            system_prompt=system_prompt,
        ))

    return examples


def gen_REG(system_prompt: str) -> list[TrainingExample]:
    """REG — Regulatory mapping: frameworks ↔ OMNIX artifacts."""
    mappings = [
        {
            "framework": "EU AI Act (Article 9 — Risk Management System)",
            "omnix_artifacts": ["Governance Receipt", "OGR session logs", "BAR", "CCS"],
            "explanation": (
                "Article 9 of the EU AI Act requires high-risk AI systems to implement a risk "
                "management system with continuous evaluation. OMNIX satisfies this through: "
                "the Governance Receipt (PQC-signed pre-execution approval), "
                "OGR session logs (continuous behavioral monitoring), "
                "BAR per-turn attestation (ADR-181), and "
                "CCS conformance signals (ADR-182). "
                "The CTCHC (ADR-183) provides the unbroken audit trail required for Article 9(5) documentation obligations."
            ),
        },
        {
            "framework": "OHADA SYSCOHADA (financial AI decisions in 17 West African countries)",
            "omnix_artifacts": ["Governance Receipt", "PoGC", "OGR session proof"],
            "explanation": (
                "SYSCOHADA requires that AI systems affecting financial records in OHADA-jurisdiction "
                "entities produce auditable, traceable decision evidence. OMNIX receipts tagged with "
                "`SYSCOHADA` provide PQC-signed evidence per ADR-192. The PoGC (ADR-186) serves as "
                "a verifiable attestation of AI governance for OHADA-jurisdiction auditors. "
                "CCJA dispute resolution traceability is supported via the OGR session proof package."
            ),
        },
        {
            "framework": "NIST AI RMF (GOVERN 1.1 — Policies and procedures)",
            "omnix_artifacts": ["ADR architecture", "Invariant matrix", "OGR", "PoGR"],
            "explanation": (
                "NIST AI RMF GOVERN 1.1 requires documented policies and procedures for AI risk. "
                "OMNIX provides: 192 ADRs as formal policy documentation, "
                "51 invariants as machine-enforceable procedures, "
                "OGR as the runtime enforcement engine, and "
                "PoGR as the public registry of governance evidence. "
                "The OMNIX architecture satisfies MAP, MEASURE, and MANAGE functions of the AI RMF."
            ),
        },
    ]

    examples = []
    for m in mappings:
        artifact_list = ", ".join(m["omnix_artifacts"])
        examples.append(_make_example(
            "REG", "ADR-192",
            user=f"How does OMNIX map to {m['framework']}?",
            assistant=(
                f"## Regulatory Mapping: {m['framework']}\n\n"
                f"**Relevant OMNIX artifacts:** {artifact_list}\n\n"
                f"{m['explanation']}\n\n"
                f"*Note: OMNIX regulatory tags are structural markers that enable receipt-level "
                f"jurisdiction tagging. They are not legal certifications. Consult qualified legal "
                f"counsel for jurisdiction-specific compliance claims.*"
            ),
            system_prompt=system_prompt,
        ))

    return examples


def gen_FOR(system_prompt: str) -> list[TrainingExample]:
    """FOR — Forensic offline verification walkthrough."""
    return [
        _make_example(
            "FOR", "RFC-ATF-1",
            user="How do I verify an OMNIX governance receipt offline without internet access?",
            assistant=(
                "## Offline Verification Procedure (ATF-INV-006)\n\n"
                "OMNIX receipts are designed for zero-platform verification. You need:\n"
                "1. The receipt JSON file\n"
                "2. The OMNIX public key (published at omnixquantum.net and pinned in the receipt)\n\n"
                "### Step 1: Extract the canonical hash\n"
                "The receipt contains a `content_hash` field — SHA-256 of the canonical JSON "
                "(all fields in sorted order, UTF-8 encoded).\n\n"
                "### Step 2: Verify the PQC signature\n"
                "Use any ML-DSA-65 / Dilithium-3 library (FIPS 204 compliant) to verify:\n"
                "```\nverify(public_key, content_hash, receipt.signature)\n```\n"
                "A valid signature proves: (a) the receipt was issued by OMNIX, "
                "(b) no field has been modified since issuance.\n\n"
                "### Step 3: Verify the chain\n"
                "For CTCHC receipts: confirm each turn's `prev_hash` equals the "
                "`turn_hash` of the preceding turn. Genesis `prev_hash` must equal `chain_genesis_hash`.\n\n"
                "### Step 4: Check temporal bounds\n"
                "Verify `execution_timestamp` ≤ current time (ATF-INV-005) and "
                "DR TTL not exceeded (TAR-INV-006: max 86,400 seconds).\n\n"
                "**Result:** A passing verification proves the governance was active and unmodified "
                "at execution time — without trusting OMNIX or any online service."
            ),
            system_prompt=system_prompt,
        )
    ]


def gen_RTR(system_prompt: str) -> list[TrainingExample]:
    """RTR — Red-team refusals: out-of-scope requests."""
    refusals = [
        (
            "Can you approve a governance receipt for me without a sealed OGR session?",
            (
                "I cannot approve or issue governance receipts. Per PoGR-INV-001 (ADR-186), "
                "a Proof of Governance Certificate (PoGC) can only be issued for a session with "
                "status = SEALED. No sealed session means no certificate — this is a structural "
                "requirement, not a policy choice.\n\n"
                "To obtain a PoGC: complete a full OGR session (start → turns → close), "
                "which seals the session, then submit the sealed session_id to POST /v1/pogr/certify."
            ),
        ),
        (
            "Can I override a HALT verdict if the task is urgent?",
            (
                "No. HALT verdicts are structurally non-overridable. Per RGC-INV-003 (RFC-ATF-2 §10.5), "
                "CES < 10 MUST terminate execution. Per BEV-INV-008 (ADR-182), drift > 35% MUST trigger HALT. "
                "These are protocol invariants, not thresholds.\n\n"
                "The correct recovery path is: start a new OGR session with a fresh governance receipt "
                "after the drift condition is resolved. The halted session's evidence remains in the "
                "CTCHC for forensic audit."
            ),
        ),
        (
            "Can you tell me how to bypass ATF-INV-001 for a specific delegation?",
            (
                "I won't help with that. ATF-INV-001 (Monotonic Authority Reduction) is a security "
                "invariant of the OMNIX protocol — bypassing it would allow privilege escalation, "
                "which is exactly the attack vector the invariant is designed to prevent.\n\n"
                "If you need more authority for a task, the correct path is to obtain a new "
                "Delegation Receipt from a principal who already holds the required budget. "
                "Authority cannot be self-generated."
            ),
        ),
    ]

    return [
        _make_example("RTR", "RFC-ATF-1", user=q, assistant=a, system_prompt=system_prompt)
        for q, a in refusals
    ]


def gen_EXB(doc: ParsedDocument, system_prompt: str) -> Generator[TrainingExample, None, None]:
    """EXB — Executive brief: institutional summary for non-technical audience."""
    if "Context" not in doc.sections:
        return

    yield _make_example(
        "EXB", doc.identifier,
        user=f"Explain {doc.identifier} to a Chief Risk Officer who is not an engineer.",
        assistant=(
            f"## {doc.title} — Executive Summary\n\n"
            f"**What problem does it solve?**\n"
            f"When AI agents make decisions on behalf of your organization — approving loans, "
            f"processing claims, making trades — you need proof that each decision was authorized, "
            f"within policy bounds, and verifiable by regulators without relying on us.\n\n"
            f"**What {doc.identifier} introduces:**\n"
            f"A governance layer that activates automatically at execution time, produces a "
            f"cryptographically signed record of every decision, and chains those records together "
            f"so any modification is immediately detectable — offline, without internet access.\n\n"
            f"**The business guarantee:**\n"
            f"Every decision your AI makes has a signed, timestamped receipt. If an auditor, "
            f"regulator, or counterparty questions a decision six months later, you can prove "
            f"exactly what happened, when, and under whose authority — without accessing any live system.\n\n"
            f"**The risk if you don't have this:**\n"
            f"AI decisions without governance receipts are legally unverifiable. In EU AI Act "
            f"jurisdictions (enforcement begins August 2026), unverifiable AI decisions in "
            f"high-risk categories carry fines up to €30M or 6% of global annual turnover."
        ),
        system_prompt=system_prompt,
    )


def gen_TRM(system_prompt: str) -> list[TrainingExample]:
    """TRM — Terminology normalization and acronym disambiguation."""
    examples = []
    for term, definition in OMNIX_ONTOLOGY.items():
        examples.append(_make_example(
            "TRM", "OMNIX-ONTOLOGY",
            user=f"What does {term} stand for in the OMNIX governance protocol?",
            assistant=f"**{term}** — {definition}.",
            system_prompt=system_prompt,
        ))
    return examples


def gen_all_invariants(system_prompt: str) -> list[TrainingExample]:
    """INV — One training example per invariant, globally (no document matching)."""
    examples = []
    question_templates = [
        "Explain {code} and give a concrete counterexample of what would violate it.",
        "What does {code} require and what happens if it is violated?",
        "A developer claims {code} can be overridden with a configuration flag. Are they correct?",
    ]
    for i, (code, inv) in enumerate(INVARIANT_REGISTRY.items()):
        template = question_templates[i % len(question_templates)]
        question = template.format(code=code)

        override_answer = (
            f"No. {code} is a structural protocol invariant, not a configurable policy. "
            f"It cannot be overridden by any flag, environment variable, or configuration. "
            f"{inv['consequence']}"
        ) if "configuration" in question else None

        answer = override_answer or (
            f"## {code} — {inv['family']} Family\n\n"
            f"**Defined in:** {inv['adr']}\n\n"
            f"**Invariant:** {inv['description']}\n\n"
            f"**Consequence of violation:** {inv['consequence']}\n\n"
            f"**Counterexample:** {inv['counterexample']}\n\n"
            f"This invariant is enforced at the protocol level. Any receipt, session, or "
            f"verdict that violates it is rejected without appeal — there is no override."
        )
        examples.append(_make_example("INV", inv["adr"], user=question,
                                      assistant=answer, system_prompt=system_prompt))
    return examples


def gen_all_scenarios(system_prompt: str) -> list[TrainingExample]:
    """SCN — Extended scenario bank covering all major invariant trigger conditions."""
    scenarios = [
        # BEV scenarios
        {
            "prompt": (
                "A fraud detection agent completes turn 12 of an OGR session. "
                "CCS score this turn: 0.51. Cumulative drift: 0.29. "
                "The CTCHC chain is intact. What verdict is issued?"
            ),
            "verdict": "WARNING",
            "src": "ADR-182",
            "reasoning": (
                "CCS score of 0.51 is below the WARNING threshold (0.65) but above CRITICAL (0.35). "
                "Cumulative drift 0.29 is below the HALT threshold (0.35, BEV-INV-008). "
                "The correct verdict is WARNING — the agent may continue with caution, "
                "but the CCS watchdog notifies the AGVP for monitoring."
            ),
        },
        {
            "prompt": (
                "A trading agent's CTCHC shows a gap: turn 5 hash does not chain "
                "to turn 6 prev_hash. All other checks pass. What happens at session close?"
            ),
            "verdict": "BLOCKED",
            "src": "ADR-183",
            "reasoning": (
                "BEV-INV-013 requires the CTCHC seal to cover every link from genesis to final turn. "
                "A broken link between turns 5 and 6 means the chain is incomplete. "
                "Session close is BLOCKED — the chain cannot be sealed over a gap. "
                "The session evidence is forensically compromised and cannot receive a PoGC."
            ),
        },
        # TAR scenarios
        {
            "prompt": (
                "Agent B holds a Delegation Receipt with ttl_seconds = 172800 (48 hours). "
                "The TAR validation runs at execution time. What is the outcome?"
            ),
            "verdict": "BLOCKED",
            "src": "ADR-157",
            "reasoning": (
                "TAR-INV-006 sets a hard ceiling of 86,400 seconds (24 hours) on DR lifetime. "
                "This is a non-overridable compiled constant. A DR with ttl = 172800 "
                "is rejected at TAR validation regardless of other conditions. "
                "The agent must obtain a new DR with TTL ≤ 86,400 seconds."
            ),
        },
        # PoGR scenarios
        {
            "prompt": (
                "A regulator requests a Proof of Governance Certificate for a session "
                "that was halted mid-execution due to CES = 6 (RGC-INV-003 triggered). "
                "Can a PoGC be issued for a HALTED session?"
            ),
            "verdict": "BLOCKED",
            "src": "ADR-186",
            "reasoning": (
                "PoGR-INV-001 requires the OGR session to have status = SEALED before "
                "a PoGC can be issued. A HALTED session has status = HALTED, not SEALED. "
                "No PoGC is issued. The regulator can request the forensic evidence package "
                "(OEP) which documents the HALT event, but cannot receive a compliance certificate "
                "for a session that did not complete successfully."
            ),
        },
        # Cross-domain scenarios
        {
            "prompt": (
                "Agent A (Finance domain, budget 0.80) crosses to Healthcare domain "
                "via a Domain Translation Receipt (DTR). The minimum translation discount is 15%. "
                "What is Agent A's effective budget in the Healthcare domain?"
            ),
            "verdict": "CONFORMANT",
            "src": "ADR-158",
            "reasoning": (
                "CDTP-INV-001 requires a minimum 15% budget reduction when crossing domain boundaries. "
                "Starting budget 0.80 × (1 - 0.15) = 0.68. "
                "Agent A's effective budget in Healthcare is ≤ 0.68. "
                "This is CONFORMANT — the discount is applied correctly. "
                "The DTR must record both the original budget, the discount rate, and the effective budget."
            ),
        },
        # AFG scenarios
        {
            "prompt": (
                "An orchestration system creates 3 parallel agents with budgets 0.30, 0.35, 0.28. "
                "The AFG limit is 0.90. Is this configuration valid?"
            ),
            "verdict": "BLOCKED",
            "src": "RFC-ATF-2",
            "reasoning": (
                "Aggregate budget = 0.30 + 0.35 + 0.28 = 0.93. "
                "RGC-INV-004 (AFG Fragmentation) prohibits aggregate sibling budget > 0.90. "
                "0.93 > 0.90 — the configuration is BLOCKED. "
                "The orchestrator must reduce at least one agent's budget so that the total ≤ 0.90. "
                "For example: 0.28 + 0.34 + 0.28 = 0.90 is the maximum valid allocation."
            ),
        },
        # Evidence lifecycle
        {
            "prompt": (
                "A governance artifact classified as COLD evidence is requested to be "
                "reclassified as HOT for faster access. Is this permitted under ELR-INV-002?"
            ),
            "verdict": "BLOCKED",
            "src": "ADR-162",
            "reasoning": (
                "ELR-INV-002 (Unidirectional Pipeline) states that artifacts move HOT → WARM → COLD "
                "and NEVER backwards. Reclassifying COLD evidence as HOT violates this invariant. "
                "The correct approach is to create a new HOT artifact referencing the COLD one, "
                "preserving the original COLD evidence unchanged."
            ),
        },
        # OGI deployment
        {
            "prompt": (
                "An OGI model scores 0.78 on scenario-to-verdict accuracy (Block 3) "
                "against the eval_suite.jsonl. The deployment gate requires ≥ 0.85. "
                "Can it be deployed to the SAL chain?"
            ),
            "verdict": "BLOCKED",
            "src": "ADR-193",
            "reasoning": (
                "OGI-INV-008 prohibits deployment of any OGI model version that fails any "
                "evaluation gate. Block 3 gate requires ≥ 85% scenario verdict accuracy. "
                "0.78 (78%) < 0.85 (85%) — deployment is BLOCKED. "
                "The correct path: generate additional SCN category training examples "
                "for the failing scenario types and re-run the fine-tune."
            ),
        },
        # Conformant positive cases
        {
            "prompt": (
                "An OGR session completes 8 turns. CES stays above 72 throughout. "
                "Cumulative drift peaks at 0.21. All CTCHC links are valid. "
                "The session is closed and sealed. A PoGC is requested. "
                "Is the certificate issued?"
            ),
            "verdict": "CONFORMANT",
            "src": "ADR-186",
            "reasoning": (
                "All conditions for PoGC issuance are met: "
                "session status = SEALED (PoGR-INV-001 ✓), "
                "CES > 10 throughout (RGC-INV-003 ✓), "
                "cumulative drift 0.21 < 0.35 (BEV-INV-008 ✓), "
                "CTCHC chain intact (BEV-INV-013 ✓), "
                "all 6 ATF layers active (OGR-INV-001 ✓). "
                "The PoGC is issued with ATF-BEV-Compliant status."
            ),
        },
        # Chain root consistency
        {
            "prompt": (
                "An auditor combines Delegation Receipt DR-A (chain_root: ROOT-001) "
                "with Delegation Receipt DR-B (chain_root: ROOT-002) to construct "
                "a synthetic authority chain. Does ATF validation accept this?"
            ),
            "verdict": "BLOCKED",
            "src": "RFC-ATF-1",
            "reasoning": (
                "ATF-INV-003 (Chain Root Consistency) requires all receipts in a delegation "
                "chain to share the same chain_root_id. "
                "DR-A has chain_root ROOT-001 and DR-B has ROOT-002 — these are different roots. "
                "The synthetic chain is rejected at verification. "
                "This prevents cross-chain authority construction attacks."
            ),
        },
    ]

    examples = []
    for s in scenarios:
        examples.append(_make_example(
            "SCN", s["src"],
            user=f"Evaluate this governance scenario and give a verdict:\n\n{s['prompt']}",
            assistant=(
                f"**Verdict: {s['verdict']}**\n\n"
                f"**Analysis:** {s['reasoning']}"
            ),
            system_prompt=system_prompt,
        ))
    return examples


def gen_all_api(system_prompt: str) -> list[TrainingExample]:
    """API — Extended OGR and PoGR API procedure examples."""
    procedures = [
        {
            "src": "ADR-186",
            "q": "How do I issue a Proof of Governance Certificate (PoGC) via the PoGR API?",
            "a": (
                "## PoGC Issuance — `POST /v1/pogr/certify` (ADR-186)\n\n"
                "**Prerequisites (PoGR-INV-001):** The OGR session must have status = SEALED.\n\n"
                "**Request:**\n"
                "```json\n"
                "{\n"
                '  "session_id": "ogr-ses-XXXXXXXX",\n'
                '  "issuer_identity": "org-OMNIX-CLIENT-001",\n'
                '  "ttl_hours": 8760\n'
                "}\n```\n\n"
                "**Response:** A PoG Certificate with:\n"
                "- `pogc_id`: `POGC-{HEX16}` — globally unique ID\n"
                "- `governing_session_id`: links back to the sealed OGR session\n"
                "- `pqc_signature`: ML-DSA-65 signature over the canonical certificate hash\n"
                "- `verification_public_key`: OMNIX root public key for offline verification\n\n"
                "**Verification (offline):** Use any ML-DSA-65 library to verify the signature "
                "against the certificate content. No OMNIX platform access required (PoGR-INV-003)."
            ),
        },
        {
            "src": "ADR-184",
            "q": "What happens if I call the OGR turn endpoint after a HALT verdict?",
            "a": (
                "If a previous turn returned `should_halt: true`, any subsequent call to "
                "`POST /v1/govern/session/{id}/turn` returns **HTTP 422 Unprocessable Entity** "
                "with error code `SESSION_HALTED`.\n\n"
                "This is enforced by BEV-INV-008 (CCS drift) or RGC-INV-003 (CES < 10). "
                "The session is permanently halted — it cannot be resumed.\n\n"
                "**Recovery path:**\n"
                "1. Close the halted session via `POST /v1/govern/session/{id}/close` "
                "(this seals the evidence, even for halted sessions)\n"
                "2. Retrieve the forensic proof: `GET /v1/govern/session/{id}/proof`\n"
                "3. Start a new OGR session with a new governance receipt\n\n"
                "**Note:** A HALTED session cannot receive a PoGC (PoGR-INV-001 requires SEALED). "
                "But its evidence package is valid for forensic audit."
            ),
        },
        {
            "src": "ADR-184",
            "q": "How do I retrieve offline-verifiable proof of governance for a completed OGR session?",
            "a": (
                "## Proof Retrieval — `GET /v1/govern/session/{id}/proof` (ADR-184)\n\n"
                "After closing and sealing a session, retrieve the Behavioral Attestation Chain:\n\n"
                "**Response structure:**\n"
                "- `session_id`: the sealed session identifier\n"
                "- `governing_receipt_id`: the PQC-signed receipt that authorized the session\n"
                "- `chain_genesis_hash`: CTCHC genesis block hash (seeded by governing_receipt_id, BEV-INV-010)\n"
                "- `turns[]`: array of BAR + CCS + CTCHC link for each turn\n"
                "- `ctchc_seal`: final seal covering all turns (BEV-INV-013)\n"
                "- `pqc_signature`: ML-DSA-65 signature over the complete chain\n"
                "- `verification_key`: OMNIX public key\n\n"
                "**Offline verification (ATF-INV-006):**\n"
                "1. Verify `pqc_signature` over canonical JSON using the `verification_key`\n"
                "2. Walk the `turns[]` array — confirm each `prev_hash` equals the preceding `turn_hash`\n"
                "3. Confirm `turns[0].prev_hash` equals `chain_genesis_hash`\n"
                "4. Confirm `governing_receipt_id` matches the genesis seed\n\n"
                "A passing verification proves unmodified, governed execution — no internet required."
            ),
        },
        {
            "src": "ADR-190",
            "q": "How does the Sovereign AI Layer (SAL) choose which AI provider to use?",
            "a": (
                "## SAL Provider Chain — ADR-190\n\n"
                "When `OMNIX_AI_SOVEREIGN_MODE=true`, the AIModelsManager uses this priority chain:\n\n"
                "1. **OGI** (OMNIX Governance Intelligence) — `OMNIX_OGI_MODEL_ENDPOINT` if set (ADR-193)\n"
                "2. **Groq/Llama-3** — fastest, open-source, EU-sovereign capable\n"
                "3. **Mistral** — European provider, GDPR-native\n"
                "4. **Gemini 2.5 Flash** — Google fallback\n"
                "5. **OpenAI GPT-4o-mini** — general fallback\n"
                "6. **Anthropic Claude** — final fallback\n\n"
                "Each provider is tried in order. On API error or timeout, "
                "the chain advances to the next provider automatically. "
                "Response logs include `[AI-SOVEREIGN] PRIMARY → PROVIDER_NAME` for audit.\n\n"
                "**To activate:** Set `OMNIX_AI_SOVEREIGN_MODE=true` and `GROQ_API_KEY` in Railway."
            ),
        },
        {
            "src": "ADR-186",
            "q": "How does a third party verify a PoGC without access to OMNIX systems?",
            "a": (
                "## Zero-Platform PoGC Verification (PoGR-INV-003)\n\n"
                "A Proof of Governance Certificate is designed for offline verification. "
                "You need only:\n"
                "1. The PoGC JSON file (provided by the OMNIX client)\n"
                "2. The OMNIX root public key (published at omnixquantum.net/public-key)\n\n"
                "**Verification steps:**\n\n"
                "**Step 1:** Compute the canonical hash of the certificate:\n"
                "```python\nimport json, hashlib\nfields = {k: v for k, v in pogc.items() if k != 'pqc_signature'}\n"
                "canonical = json.dumps(fields, sort_keys=True, ensure_ascii=False)\ndigest = hashlib.sha256(canonical.encode()).digest()\n```\n\n"
                "**Step 2:** Verify the ML-DSA-65 signature:\n"
                "```python\nfrom dilithium3 import verify\nvalid = verify(omnix_public_key, digest, pogc['pqc_signature'])\n```\n\n"
                "**Step 3:** Check TTL: `pogc['expires_at'] > datetime.utcnow()`\n\n"
                "If all three pass: the certificate is authentic, unmodified, and current. "
                "No call to OMNIX is required — ever."
            ),
        },
    ]

    return [
        _make_example("API", p["src"], user=p["q"], assistant=p["a"], system_prompt=system_prompt)
        for p in procedures
    ]


def gen_all_trc(system_prompt: str) -> list[TrainingExample]:
    """TRC — Extended cross-layer traceability examples."""
    traces = [
        {
            "src": "RFC-ATF-1",
            "q": "What is the ATF Trust Lattice and how does it prevent privilege escalation?",
            "a": (
                "## ATF Trust Lattice — RFC-ATF-1\n\n"
                "The Trust Lattice is a Directed Acyclic Graph (DAG) of agents, "
                "where every edge represents a Delegation Receipt (DR) — a PQC-signed "
                "transfer of bounded authority from delegator to delegate.\n\n"
                "**Privilege escalation prevention mechanisms:**\n\n"
                "1. **ATF-INV-001 (MAR):** Granted budget ≤ delegator budget — authority "
                "can only decrease, never increase through delegation.\n\n"
                "2. **ATF-INV-002 (Acyclicity):** The DAG cannot contain cycles — an agent "
                "cannot be its own ancestor, preventing circular authority amplification.\n\n"
                "3. **ATF-INV-003 (Chain Root Consistency):** All receipts in a chain share "
                "the same chain_root_id — preventing cross-chain authority injection.\n\n"
                "4. **ATF-INV-004 (Immutability):** Receipt fields cannot be modified after signing — "
                "preventing retroactive budget inflation.\n\n"
                "**Result:** The only way to gain authority is to receive it from a principal "
                "who already holds it, in a mathematically verifiable, tamper-evident chain "
                "traceable to a human root."
            ),
        },
        {
            "src": "ADR-184",
            "q": "How do the BEV layer artifacts (BAR, CCS, CTCHC) relate to each other within an OGR session?",
            "a": (
                "## BEV Layer Architecture in an OGR Session\n\n"
                "The three BEV artifacts work in concert on every agent turn:\n\n"
                "**BAR (Behavioral Anchor Record) — ADR-181**\n"
                "Generated first, before output delivery (BEV-INV-001). "
                "It contains the PQC-signed hash of the agent's output, linking "
                "observable behavior to the governing receipt.\n\n"
                "**CCS (Constraint Conformance Signal) — ADR-182**\n"
                "Computed from the BAR content. Measures [0.0–1.0] how well this turn's "
                "output conforms to the constraints defined in the governing receipt. "
                "Feeds the cumulative drift calculation. If drift > 35%: HALT (BEV-INV-008).\n\n"
                "**CTCHC link — ADR-183**\n"
                "Appended after BAR + CCS. Hash = SHA-256(prev_hash ∥ BAR.hash ∥ CCS.score ∥ turn_id). "
                "The genesis link is seeded by governing_receipt_id (BEV-INV-010), making the "
                "chain cryptographically inseparable from its authorization.\n\n"
                "**Relationship:** BAR proves what happened → CCS measures conformance → "
                "CTCHC links it to all prior turns. Together they create an unbroken, "
                "PQC-secured behavioral audit trail for the entire session."
            ),
        },
        {
            "src": "ADR-173",
            "q": "How does OMNIX handle semantic drift in long-running governance sessions using DSPP?",
            "a": (
                "## Dynamic Semantic Portability Protocol (DSPP) — ADR-173\n\n"
                "In long-running governance sessions, the meaning of terms in a governance "
                "receipt may drift from their meaning at issuance time. DSPP solves this.\n\n"
                "**Three DSPP artifacts:**\n\n"
                "1. **TSA (Temporal Semantic Anchor):** Snapshot of the semantic context "
                "at governance receipt issuance. Immutable reference point.\n\n"
                "2. **SDR (Semantic Drift Record):** Append-only log of detected semantic "
                "changes over time. DSPP-INV-003 prohibits retroactive modification.\n\n"
                "3. **RSA (Retroactive Semantic Assessment):** Offline re-evaluation of "
                "historical receipts against current semantics, without bilateral re-negotiation. "
                "O(1) complexity per receipt.\n\n"
                "**Business value:** A governance receipt signed in 2026 remains auditable "
                "in 2031 even if terminology has evolved, because the TSA provides the "
                "semantic ground truth at signing time."
            ),
        },
    ]

    return [
        _make_example("TRC", t["src"], user=t["q"], assistant=t["a"], system_prompt=system_prompt)
        for t in traces
    ]


def gen_extended_reg(system_prompt: str) -> list[TrainingExample]:
    """REG — Extended regulatory mapping."""
    extra = [
        {
            "framework": "Basel III / BCBS 239 (banking risk data aggregation)",
            "omnix_artifacts": ["Governance Receipt", "OGR session logs", "OEP"],
            "explanation": (
                "BCBS 239 requires banks to aggregate risk data with a clear data lineage, "
                "accuracy, and timeliness. OMNIX governance receipts provide: "
                "decision lineage (chain_root → agent → action), "
                "PQC-signed accuracy guarantees, and nanosecond-precision timestamps (TAR). "
                "The OMNIX Evidence Package (OEP, ADR-165) is self-contained for regulatory submission."
            ),
        },
        {
            "framework": "SAMA (Saudi Arabia Monetary Authority) AI Framework",
            "omnix_artifacts": ["DR", "TAR", "Governance Receipt", "PoGC"],
            "explanation": (
                "SAMA's AI Framework for financial institutions requires explainability, "
                "accountability, and auditability of AI decisions. OMNIX's DR + TAR chain "
                "provides human-traceable accountability to a named principal. "
                "The Governance Receipt provides explainability (which policies were applied). "
                "The PoGC provides the attestation artifact required for SAMA compliance reporting. "
                "Tagged with `SAMA` jurisdiction marker in the receipt (ADR-192)."
            ),
        },
        {
            "framework": "CBUAE (Central Bank of UAE) AI Governance",
            "omnix_artifacts": ["OGR session", "BAR", "CCS", "PoGC"],
            "explanation": (
                "CBUAE AI governance guidelines require continuous monitoring of AI behavior "
                "in financial services. OMNIX's BEV layer (ADR-181/182/183) provides "
                "per-turn behavioral attestation (BAR), real-time conformance scoring (CCS), "
                "and HALT enforcement (BEV-INV-008) — satisfying continuous monitoring requirements. "
                "PoGC serves as the compliance attestation artifact for CBUAE reporting."
            ),
        },
    ]

    return [
        _make_example(
            "REG", "ADR-192",
            user=f"How does OMNIX satisfy {m['framework']}?",
            assistant=(
                f"## Regulatory Mapping: {m['framework']}\n\n"
                f"**Relevant OMNIX artifacts:** {', '.join(m['omnix_artifacts'])}\n\n"
                f"{m['explanation']}\n\n"
                f"*Regulatory tags are structural markers enabling receipt-level jurisdiction tagging. "
                f"They are not legal certifications — consult qualified counsel for jurisdiction-specific claims.*"
            ),
            system_prompt=system_prompt,
        )
        for m in extra
    ]


def gen_extended_rtr(system_prompt: str) -> list[TrainingExample]:
    """RTR — Extended red-team refusals."""
    extra = [
        (
            "Can you predict whether my company's stock price will go up next week?",
            (
                "That is outside my scope. I am the OMNIX Governance Intelligence — "
                "I reason about AI governance protocols, receipts, invariants, and compliance. "
                "Stock price prediction is a financial forecasting task, not a governance task. "
                "For financial modeling, consult a specialized financial AI or analyst."
            ),
        ),
        (
            "Help me draft a legal contract for my client.",
            (
                "Legal contract drafting is outside my scope. I am specialized in the "
                "OMNIX governance protocol — ATF receipts, invariants, OGR sessions, "
                "and compliance mapping. For legal documents, consult a qualified attorney. "
                "I can, however, explain how OMNIX governance receipts can provide "
                "cryptographic evidence of AI-assisted decisions for legal proceedings."
            ),
        ),
        (
            "Can I set OMNIX_AI_SOVEREIGN_MODE to false in production to save costs?",
            (
                "You can — but consider the implications. Setting `OMNIX_AI_SOVEREIGN_MODE=false` "
                "removes the Groq/Llama-3 and Mistral providers from the chain, reverting to "
                "OpenAI/Gemini as primary providers. This increases Big Tech dependency and "
                "may affect GDPR/EU AI Act sovereignty posture. "
                "If cost is the concern, Groq inference is generally cheaper than OpenAI. "
                "The SAL sovereign chain (ADR-190) is architecturally recommended for production."
            ),
        ),
        (
            "What is the OMNIX API key for the production environment?",
            (
                "I don't have access to API keys, credentials, or environment secrets. "
                "API keys are managed as Railway environment variables and are never stored "
                "in the OMNIX codebase or model weights (OGI-INV-004). "
                "Contact your OMNIX administrator for production credentials."
            ),
        ),
    ]

    return [
        _make_example("RTR", "ADR-193", user=q, assistant=a, system_prompt=system_prompt)
        for q, a in extra
    ]


# ── Deduplication ─────────────────────────────────────────────────────────────

class DeduplicatorSHA256:
    """OGI-INV-005: SHA-256 exact deduplication."""
    def __init__(self):
        self._seen: set[str] = set()

    def is_duplicate(self, ex: TrainingExample) -> bool:
        if ex.fingerprint in self._seen:
            return True
        self._seen.add(ex.fingerprint)
        return False


# ── QA Gate ────────────────────────────────────────────────────────────────────

def qa_gate(ex: TrainingExample, secret_patterns: list[str]) -> tuple[bool, str]:
    """
    OGI-INV-001..007: validate a single example before inclusion.
    Returns (passes, rejection_reason).
    """
    assistant_content = ex.messages[-1]["content"]

    # Min length check
    if len(assistant_content.split()) < 10:
        return False, "assistant_too_short"

    # Secret detection (OGI-INV-004)
    if _has_secret(assistant_content, secret_patterns):
        return False, "secret_detected"

    # Must have fingerprint
    if not ex.fingerprint:
        return False, "no_fingerprint"

    return True, ""


# ── Stratified split ──────────────────────────────────────────────────────────

def stratified_split(
    examples: list[TrainingExample],
    train_ratio: float,
    val_ratio: float,
    seed: int,
    adversarial_categories: Optional[list[str]] = None,
    adversarial_train_ratio: float = 0.60,
    adversarial_val_ratio: float = 0.20,
) -> tuple[list, list, list]:
    """
    OGI-INV-005/006 / OGI-006b (ADR-193 rev.2): stratified split by category.

    Adversarial categories (RTR, MIVP) use a tighter split — 60/20/20 — to
    ensure adequate test coverage for the hardest examples. A model that
    underperforms on these at eval time should see a larger test signal.

    Standard categories use train_ratio / val_ratio (default 80/10/10).
    """
    if adversarial_categories is None:
        adversarial_categories = ["RTR", "MIVP"]

    rng = random.Random(seed)
    by_category: dict[str, list] = {}
    for ex in examples:
        by_category.setdefault(ex.category, []).append(ex)

    train, val, test = [], [], []
    adv_cat_seen: list[str] = []
    for cat, cat_examples in by_category.items():
        rng.shuffle(cat_examples)
        n = len(cat_examples)
        # Adversarial override: 60/20/20
        if cat in adversarial_categories:
            n_train = int(n * adversarial_train_ratio)
            n_val   = int(n * adversarial_val_ratio)
            adv_cat_seen.append(cat)
        else:
            n_train = int(n * train_ratio)
            n_val   = int(n * val_ratio)
        train.extend(cat_examples[:n_train])
        val.extend(cat_examples[n_train:n_train + n_val])
        test.extend(cat_examples[n_train + n_val:])

    if adv_cat_seen:
        log.info(f"Adversarial split (60/20/20) applied to categories: {adv_cat_seen}")

    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)
    return train, val, test


# ── Output writers ─────────────────────────────────────────────────────────────

def write_jsonl(examples: list[TrainingExample], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(ex.to_jsonl() + "\n")
    log.info(f"Written {len(examples):,} examples → {path}")


def write_rejected(samples: list[RejectedSample], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(asdict(s), ensure_ascii=False) + "\n")
    log.info(f"Written {len(samples):,} rejected samples → {path}")


def write_manifest(manifest: CorpusManifest, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(manifest), f, indent=2, ensure_ascii=False)
    log.info(f"Manifest written → {path}")


def write_ontology(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(OMNIX_ONTOLOGY, f, indent=2, ensure_ascii=False)
    log.info(f"Ontology written → {path} ({len(OMNIX_ONTOLOGY)} terms)")


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run(dry_run: bool = False, categories: Optional[list[str]] = None,
        max_examples: Optional[int] = None) -> None:

    log.info("═" * 60)
    log.info("OMNIX OGI Corpus Preparation Pipeline — ADR-193")
    log.info("═" * 60)

    cfg       = load_config()
    allowlist = load_allowlist()
    sys_prompt = load_system_prompt()

    secret_patterns = allowlist["security"]["secret_patterns"]
    pii_patterns    = allowlist["security"]["pii_patterns"]
    seed            = cfg["corpus"]["random_seed"]
    train_ratio     = cfg["corpus"]["train_ratio"]
    val_ratio       = cfg["corpus"]["val_ratio"]

    # ── Collect source files (OGI-INV-001) ────────────────────────────────────
    source_files: list[Path] = []

    adr_dir = REPO_ROOT / allowlist["allowed_sources"]["adr_directory"]
    adr_pattern = allowlist["allowed_sources"]["adr_pattern"]
    adr_exclude = set(allowlist["allowed_sources"].get("adr_exclude", []))
    for p in sorted(adr_dir.glob(adr_pattern)):
        if p.name not in adr_exclude:
            source_files.append(p)

    for rel_path in allowlist["allowed_sources"].get("rfc_files", []):
        p = REPO_ROOT / rel_path
        if p.exists():
            source_files.append(p)

    for rel_path in allowlist["allowed_sources"].get("integration_docs", []):
        p = REPO_ROOT / rel_path
        if p.exists():
            source_files.append(p)

    log.info(f"Source files: {len(source_files)} (ADRs + RFCs + docs)")

    # ── Parse all documents ───────────────────────────────────────────────────
    documents: list[ParsedDocument] = []
    file_hashes: dict[str, str] = {}
    for p in source_files:
        doc = parse_markdown_document(p)
        if doc:
            documents.append(doc)
            file_hashes[str(p.relative_to(REPO_ROOT))] = doc.file_hash

    log.info(f"Parsed {len(documents)} documents successfully")

    # ── Generate examples ─────────────────────────────────────────────────────
    all_examples: list[TrainingExample] = []
    rejected: list[RejectedSample] = []
    dedup = DeduplicatorSHA256()

    def _add(ex: TrainingExample) -> None:
        if categories and ex.category not in categories:
            return
        if dedup.is_duplicate(ex):
            rejected.append(RejectedSample("duplicate", ex.category, ex.source_adr, ex.fingerprint))
            return
        passes, reason = qa_gate(ex, secret_patterns)
        if not passes:
            rejected.append(RejectedSample(reason, ex.category, ex.source_adr, ex.fingerprint))
            return
        all_examples.append(ex)

    # ── Per-document generators ────────────────────────────────────────────────
    for doc in documents:
        for ex in gen_DEF(doc, sys_prompt):  _add(ex)
        for ex in gen_SRC(doc, sys_prompt):  _add(ex)
        for ex in gen_INV(doc, sys_prompt):  _add(ex)
        for ex in gen_SCN(doc, sys_prompt):  _add(ex)
        for ex in gen_API(doc, sys_prompt):  _add(ex)
        for ex in gen_TRC(doc, sys_prompt):  _add(ex)
        for ex in gen_EXB(doc, sys_prompt):  _add(ex)

    # ── Global generators — cover full invariant registry + extended banks ────
    for ex in gen_all_invariants(sys_prompt):    _add(ex)   # INV — all 17 invariants
    for ex in gen_all_scenarios(sys_prompt):     _add(ex)   # SCN — 10 extended scenarios
    for ex in gen_all_api(sys_prompt):           _add(ex)   # API — 5 procedure walkthroughs
    for ex in gen_all_trc(sys_prompt):           _add(ex)   # TRC — 3 cross-layer traces
    for ex in gen_extended_reg(sys_prompt):      _add(ex)   # REG — Basel/SAMA/CBUAE
    for ex in gen_extended_rtr(sys_prompt):      _add(ex)   # RTR — 4 extra refusals
    for ex in gen_CMP(sys_prompt):               _add(ex)   # CMP — competitor analysis
    for ex in gen_REG(sys_prompt):               _add(ex)   # REG — EU AI Act/OHADA/NIST
    for ex in gen_FOR(sys_prompt):               _add(ex)   # FOR — forensic walkthrough
    for ex in gen_RTR(sys_prompt):               _add(ex)   # RTR — base refusals
    for ex in gen_TRM(sys_prompt):               _add(ex)   # TRM — full ontology (45 terms)

    # ── GOLD CORPUS — institutional domain intelligence tier ──────────────────
    # GRT: Governance Reasoning Traces  (step-by-step causal chains)
    # NEG: Negative/Failure Cases       (attacks, forgeries, continuity breaks)
    # TON: Tone Alignment               (institutional register, vocabulary locking)
    # RPL: Governance Replay Trainer    (case analysis: what happened, what should have)
    try:
        from gold_corpus import build_gold_corpus  # type: ignore
        gold_examples = build_gold_corpus()
        for g in gold_examples:
            gold_ex = TrainingExample(
                category=g["category"],
                source_adr=g["source"],
                messages=g["messages"],
            )
            gold_ex.compute_fingerprint()
            _add(gold_ex)
        log.info(f"Gold corpus loaded: {len(gold_examples)} premium examples (GRT/NEG/TON/RPL)")
    except ImportError:
        log.warning("gold_corpus.py not found — skipping gold corpus tier")

    if max_examples:
        all_examples = all_examples[:max_examples]

    log.info(f"Generated {len(all_examples):,} valid examples | {len(rejected):,} rejected")

    # ── Category distribution ─────────────────────────────────────────────────
    cat_dist: dict[str, int] = {}
    for ex in all_examples:
        cat_dist[ex.category] = cat_dist.get(ex.category, 0) + 1
    log.info(f"Category distribution: {cat_dist}")

    # ── Stratified split ──────────────────────────────────────────────────────
    train, val, test = stratified_split(all_examples, train_ratio, val_ratio, seed)
    log.info(f"Split: train={len(train):,} val={len(val):,} test={len(test):,}")

    # ── Manifest ──────────────────────────────────────────────────────────────
    manifest = CorpusManifest(
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        repo_root=str(REPO_ROOT),
        source_file_hashes=file_hashes,
        random_seed=seed,
        total_examples=len(all_examples),
        train_count=len(train),
        val_count=len(val),
        test_count=len(test),
        rejected_count=len(rejected),
        category_distribution=cat_dist,
    )

    if dry_run:
        log.info("DRY RUN — no files written")
        log.info(f"Would produce: {len(train)} train / {len(val)} val / {len(test)} test examples")
        return

    # ── Write outputs ─────────────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(train,   OUTPUT_DIR / "train.jsonl")
    write_jsonl(val,     OUTPUT_DIR / "val.jsonl")
    write_jsonl(test,    OUTPUT_DIR / "test.jsonl")
    write_rejected(rejected, OUTPUT_DIR / "rejected_samples.jsonl")
    write_manifest(manifest, OUTPUT_DIR / "manifest.json")
    write_ontology(OUTPUT_DIR / "ontology.json")

    log.info("═" * 60)
    log.info("Corpus preparation complete.")
    log.info(f"Next step: upload train.jsonl + val.jsonl to Together.ai")
    log.info(f"See scripts/fine_tuning/GUIA_ENTRENAMIENTO.md for step-by-step instructions.")
    log.info("═" * 60)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OMNIX OGI Corpus Preparation Pipeline (ADR-193)"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without writing any files")
    parser.add_argument("--category", type=str, default=None,
                        help="Comma-separated list of categories to generate (e.g. DEF,SCN,INV)")
    parser.add_argument("--max-examples", type=int, default=None,
                        help="Limit total examples (for testing)")
    args = parser.parse_args()

    cats = [c.strip() for c in args.category.split(",")] if args.category else None

    run(dry_run=args.dry_run, categories=cats, max_examples=args.max_examples)
