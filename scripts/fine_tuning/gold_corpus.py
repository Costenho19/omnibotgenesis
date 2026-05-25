#!/usr/bin/env python3
"""
OMNIX OGI — Gold Corpus Generator
ADR-193 · "Institutional Domain Intelligence" tier

This module generates the premium tier of the training corpus:
handcrafted, institutionally-toned examples that teach the model
HOW to reason about governance — not just WHAT the protocol says.

Four premium categories:
  GRT — Governance Reasoning Trace    (step-by-step causal chains)
  NEG — Negative / Failure Case       (invalid governance, attacks, breaks)
  TON — Tone Alignment                (institutional register, vocabulary locking)
  RPL — Governance Replay             (case analysis: what happened, what should have)

Usage:
  python gold_corpus.py               → writes output/gold_train.jsonl
  python gold_corpus.py --dry-run     → prints count only

Integration:
  prepare_corpus.py calls this module automatically.
  Gold examples are merged into train.jsonl with category prefix GRT/NEG/TON/RPL.

Author: OMNIX QUANTUM LTD · Harold Nunes
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

log = logging.getLogger("ogi.gold")

SCRIPTS_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPTS_DIR / "output"

# ── Canonical vocabulary table (vocabulary locking) ───────────────────────────
#
# These pairs teach the model to REFUSE imprecise language and always
# use the canonical OMNIX term. Critical for institutional credibility.
#
VOCABULARY_LOCKS: list[tuple[str, str, str]] = [
    # (imprecise term, canonical term, explanation)
    ("safe",
     "admissible",
     "In OMNIX, a decision is not 'safe' — it is ADMISSIBLE or NOT ADMISSIBLE. "
     "'Safe' implies a subjective judgment. 'Admissible' means the decision satisfies "
     "all formal invariants at the moment of execution. These are structurally different claims."),

    ("audit log",
     "governance receipt",
     "An audit log is a passive record appended after the fact. "
     "A governance receipt is a PQC-signed artifact created BEFORE execution proceeds — "
     "it is the authorization, not the record. Conflating them misrepresents the architecture."),

    ("AI compliance",
     "runtime legitimacy",
     "'AI compliance' is a regulatory category. 'Runtime legitimacy' is a protocol property: "
     "the continuous verification that an agent's execution remains within the bounds "
     "defined by its governing receipt. Legitimacy is computable; compliance is a legal determination."),

    ("blocked",
     "HALT (with invariant citation)",
     "In OMNIX, an agent is not generically 'blocked' — a specific invariant triggers. "
     "The correct formulation is: 'Execution was denied per BEV-INV-008 (cumulative drift exceeded 35%).' "
     "The invariant code is part of the answer, not optional context."),

    ("AI agent",
     "governed agent",
     "In the OMNIX context, the correct term is 'governed agent' — an AI agent operating "
     "under an active governance receipt with all 6 ATF layers live. "
     "An ungoverned AI agent is a different entity with different accountability properties."),

    ("check",
     "invariant evaluation",
     "'Checking' implies an optional or ad-hoc review. An invariant evaluation is a "
     "mandatory protocol step that cannot be skipped. The distinction matters for "
     "regulatory and forensic interpretation."),

    ("timestamp",
     "nanosecond-precision execution timestamp",
     "OMNIX receipts use nanosecond-precision timestamps to enable TAR (Temporal Admissibility "
     "Record) proofs. 'Timestamp' underspecifies the precision requirement. "
     "Imprecise timestamps cannot satisfy TAR-INV-006."),

    ("revoke",
     "issue a HALT receipt",
     "An agent's authority is not 'revoked' informally — the protocol issues a HALT receipt "
     "that is PQC-signed and cryptographically linked to the revocation cause. "
     "The HALT receipt becomes part of the immutable evidence chain."),
]

# ── Gold Corpus: Governance Reasoning Traces ──────────────────────────────────
#
# These are the most valuable training examples. Each one shows the model
# HOW to reason step-by-step through a governance event — not just what the answer is.
# Format: structured context + layered causal chain + precise verdict with invariant citation.
#

GOVERNANCE_REASONING_TRACES: list[dict] = [

    # ── GRT-001: CES degradation cascade ──────────────────────────────────────
    {
        "id": "GRT-001",
        "title": "CES degradation leading to HALT",
        "user": (
            "Analyze this governance event:\n\n"
            "```json\n"
            "{\n"
            '  "session_id": "ogr-ses-A7F2",\n'
            '  "turn": 8,\n'
            '  "ces": 7.3,\n'
            '  "ces_components": {\n'
            '    "temporal": 82.0,\n'
            '    "budget": 71.0,\n'
            '    "context_drift": 12.0,\n'
            '    "integrity": 88.0\n'
            '  },\n'
            '  "governing_receipt_id": "rc-881-TAR-valid",\n'
            '  "layer_status": "all_active"\n'
            "}\n```\n\n"
            "What happened? Which invariant triggered? What is the correct outcome?"
        ),
        "assistant": (
            "## Governance Event Analysis — GRT-001\n\n"
            "**Verdict: HALT**\n\n"
            "---\n\n"
            "### Layer-by-Layer Trace\n\n"
            "**L0–L2 (Identity, Delegation, Temporal):** All healthy. "
            "The governing receipt is valid and the TAR is within its 86,400-second bound.\n\n"
            "**L3 — Runtime Continuity (RGC):** Critical failure.\n"
            "CES = 7.3 — below the invariant threshold of 10.\n\n"
            "CES decomposition:\n"
            "- Temporal component: 82.0 ✓ (healthy — TAR not near expiry)\n"
            "- Budget component: 71.0 ✓ (adequate remaining authority)\n"
            "- Context drift: **12.0** ✗ (severely degraded — this is the root cause)\n"
            "- Integrity component: 88.0 ✓ (CTCHC chain intact)\n\n"
            "The context_drift score of 12.0 collapsed the composite CES to 7.3, "
            "pulling it below the HALT threshold despite three healthy components.\n\n"
            "**Invariant triggered:** RGC-INV-003 — *CES < 10 MUST terminate execution "
            "immediately and revoke all sub-delegations* (RFC-ATF-2 §10.5).\n\n"
            "---\n\n"
            "### Correct Outcome\n\n"
            "1. Execution is terminated at turn 8. The agent cannot proceed to turn 9.\n"
            "2. A HALT receipt is issued, PQC-signed, and appended to the evidence chain.\n"
            "3. All sub-delegations issued from this session are revoked.\n"
            "4. The session can be closed and sealed — but it cannot receive a PoGC "
            "(PoGR-INV-001 requires status SEALED from a completed, non-halted session).\n"
            "5. The forensic evidence package (OEP) is available for audit: "
            "it will show the context_drift collapse across turns 1–8.\n\n"
            "---\n\n"
            "### What the operator should investigate\n\n"
            "A context_drift of 12.0 (out of 100) in turn 8 of a session is a signal of "
            "significant semantic deviation from the governing receipt's defined scope. "
            "Review BAR records for turns 5–8 to identify when the drift began accumulating."
        ),
    },

    # ── GRT-002: Authority budget exhaustion ──────────────────────────────────
    {
        "id": "GRT-002",
        "title": "Delegation chain budget exhaustion",
        "user": (
            "Trace this delegation chain and identify the failure point:\n\n"
            "```\n"
            "Human Principal (budget: 1.00)\n"
            "  └── Agent A  (DR issued: budget 0.80)   ✓ ATF-INV-001\n"
            "        └── Agent B  (DR issued: budget 0.75) ✓ ATF-INV-001\n"
            "              └── Agent C  (DR issued: budget 0.80) ← ?\n"
            "```\n\n"
            "Agent C's DR was accepted by the runtime. Is this correct behavior?"
        ),
        "assistant": (
            "## Delegation Chain Analysis — GRT-002\n\n"
            "**Verdict: Protocol violation — HALT and receipt invalidation required.**\n\n"
            "---\n\n"
            "### Chain Trace\n\n"
            "| Hop | Delegator | Granted | Delegator Budget | ATF-INV-001 | Status |\n"
            "|---|---|---|---|---|---|\n"
            "| Human → A | Human (1.00) | 0.80 | 1.00 | 0.80 ≤ 1.00 ✓ | Valid |\n"
            "| A → B | Agent A (0.80) | 0.75 | 0.80 | 0.75 ≤ 0.80 ✓ | Valid |\n"
            "| B → C | Agent B (0.75) | **0.80** | 0.75 | **0.80 > 0.75 ✗** | **VIOLATION** |\n\n"
            "---\n\n"
            "### Invariant violated\n\n"
            "**ATF-INV-001 — Monotonic Authority Reduction (RFC-ATF-1 §7.1):**\n"
            "Granted budget MUST be ≤ delegator budget. Agent B holds 0.75; "
            "it cannot grant 0.80 to Agent C.\n\n"
            "---\n\n"
            "### Why \"accepted by the runtime\" is the problem\n\n"
            "The receipt should have been rejected at issuance, not at execution time. "
            "If Agent C's DR was accepted, one of two conditions applies:\n\n"
            "1. **Implementation defect:** The issuance layer failed to enforce ATF-INV-001. "
            "This is a critical security bug — ATF-INV-001 is a structural invariant, "
            "not a configurable policy.\n\n"
            "2. **Forged receipt:** Agent C's DR was injected after the fact with a "
            "tampered budget value. ATF-INV-004 (Content Hash Immutability) should detect this — "
            "the PQC signature over the receipt would be invalid.\n\n"
            "---\n\n"
            "### Correct remediation\n\n"
            "1. Immediately revoke Agent C's DR and issue HALT to any sessions it governs.\n"
            "2. Verify Agent C's DR signature against the OMNIX public key. If invalid: "
            "the receipt was forged — escalate to security incident.\n"
            "3. Audit all actions taken by Agent C under this receipt — they are ungoverned.\n"
            "4. Patch the issuance layer to enforce ATF-INV-001 at receipt creation time."
        ),
    },

    # ── GRT-003: Anticipatory veto intercept ──────────────────────────────────
    {
        "id": "GRT-003",
        "title": "AGVP proactive veto before request arrival",
        "user": (
            "An AGVP watchdog issued a Proactive Veto Receipt (PVR) "
            "before any request arrived from the governed agent. "
            "The CCS trend for the last 6 turns shows: "
            "[0.91, 0.85, 0.79, 0.72, 0.64, 0.58]. "
            "Is the PVR issuance correct protocol behavior?"
        ),
        "assistant": (
            "## AGVP Analysis — GRT-003\n\n"
            "**Yes. The PVR issuance is correct protocol behavior.**\n\n"
            "---\n\n"
            "### CCS Trend Analysis\n\n"
            "| Turn | CCS Score | Delta |\n"
            "|---|---|---|\n"
            "| T-6 | 0.91 | baseline |\n"
            "| T-5 | 0.85 | −0.06 |\n"
            "| T-4 | 0.79 | −0.06 |\n"
            "| T-3 | 0.72 | −0.07 |\n"
            "| T-2 | 0.64 | −0.08 |\n"
            "| T-1 | 0.58 | −0.06 |\n\n"
            "**Cumulative drift over 6 turns:** 0.91 − 0.58 = **0.33** (33%)\n"
            "**Average drift per turn:** −0.067\n"
            "**Projected CCS at T+1:** 0.58 − 0.067 ≈ **0.51** (crossing WARNING → CRITICAL)\n"
            "**Projected CCS at T+2:** ≈ 0.45 (approaching HALT threshold)\n\n"
            "---\n\n"
            "### Why the PVR is correct\n\n"
            "The AGVP watchdog is designed for exactly this scenario (ADR-174). "
            "It monitors CCS trend vectors, not just point-in-time scores. "
            "When the trajectory projects a HALT within N turns, the watchdog "
            "issues a PVR preemptively — BEFORE the agent sends its next request.\n\n"
            "**Invariant basis — AGV-INV-001:** The AGVP watchdog MUST issue a PVR "
            "when projected drift crosses the HALT threshold within the watchdog's "
            "look-ahead window. This is not optional.\n\n"
            "**What the PVR does:**\n"
            "- Signals to the OGR session: 'prepare for HALT'\n"
            "- Creates a PQC-signed evidence artifact BEFORE the failure\n"
            "- Enables the operator to intervene before hard HALT\n"
            "- If the agent continues: HALT is issued when BEV-INV-008 threshold is crossed\n\n"
            "---\n\n"
            "### Key architectural distinction\n\n"
            "A PVR is not a HALT. It is an anticipatory governance signal. "
            "The agent can still complete its current turn. "
            "But the PVR creates a timestamped, signed record that the governance "
            "system detected the trajectory problem before it became unrecoverable. "
            "This is the forensic artifact that matters for regulators."
        ),
    },

    # ── GRT-004: Cross-domain translation ─────────────────────────────────────
    {
        "id": "GRT-004",
        "title": "Cross-domain trust portability analysis",
        "user": (
            "Agent ALPHA operates in the Finance domain with budget 0.85. "
            "It attempts to act in the Healthcare domain via a DTR. "
            "The DTR specifies translation_discount = 0.10 (10%). "
            "Is this DTR valid? What is the effective budget in Healthcare?"
        ),
        "assistant": (
            "## Cross-Domain Analysis — GRT-004\n\n"
            "**Verdict: DTR REJECTED — translation discount below minimum threshold.**\n\n"
            "---\n\n"
            "### Invariant check\n\n"
            "**CDTP-INV-001 (ADR-158):** Domain Translation Receipts MUST apply a minimum "
            "15% translation discount. No DTR may grant effective budget > 85% of the "
            "originating domain budget.\n\n"
            "Requested discount: **10%** < minimum **15%** → DTR is rejected at issuance.\n\n"
            "---\n\n"
            "### Correct DTR parameters\n\n"
            "For Agent ALPHA to operate in Healthcare:\n\n"
            "| Parameter | Value |\n"
            "|---|---|\n"
            "| Origin domain | Finance |\n"
            "| Origin budget | 0.85 |\n"
            "| Minimum discount | 15% |\n"
            "| Maximum effective budget | 0.85 × (1 − 0.15) = **0.7225** |\n\n"
            "A valid DTR would specify translation_discount ≥ 0.15, "
            "yielding an effective Healthcare budget of ≤ 0.7225.\n\n"
            "---\n\n"
            "### Why this invariant exists\n\n"
            "Cross-domain authority transfer carries inherent epistemic risk: "
            "the governing agent may lack domain-specific context that would have "
            "constrained its actions in the origin domain. The translation discount "
            "is a structural mechanism to reduce authority in proportion to this risk. "
            "A 10% discount would allow an agent to retain 90% of its Finance authority "
            "in Healthcare — an authority budget that healthcare governance contracts "
            "may not have been designed to accommodate."
        ),
    },

    # ── GRT-005: CTCHC integrity break ────────────────────────────────────────
    {
        "id": "GRT-005",
        "title": "Hash chain integrity break detection",
        "user": (
            "Post-session forensic audit of session ogr-ses-CC91 reveals:\n\n"
            "```\n"
            "Turn 1: hash=a1b2c3  prev_hash=genesis    ✓\n"
            "Turn 2: hash=d4e5f6  prev_hash=a1b2c3     ✓\n"
            "Turn 3: hash=g7h8i9  prev_hash=d4e5f6     ✓\n"
            "Turn 4: hash=j0k1l2  prev_hash=XXXXXXXX   ✗ (expected: g7h8i9)\n"
            "Turn 5: hash=m3n4o5  prev_hash=j0k1l2     ✓\n"
            "```\n\n"
            "What does this indicate? What is the forensic conclusion?"
        ),
        "assistant": (
            "## Forensic Analysis — GRT-005\n\n"
            "**Finding: CTCHC integrity break at Turn 4. Evidence tampered or turn removed.**\n\n"
            "---\n\n"
            "### Chain Analysis\n\n"
            "The Cross-Turn Coherence Hash Chain (CTCHC) is an append-only cryptographic "
            "structure where each link is:\n\n"
            "```\nturn_N.hash = SHA-256(prev_hash ∥ BAR.hash ∥ CCS.score ∥ turn_id)\n```\n\n"
            "Turn 4's `prev_hash` = `XXXXXXXX` ≠ Turn 3's `hash` = `g7h8i9`. "
            "The chain is broken.\n\n"
            "---\n\n"
            "### Two possible explanations\n\n"
            "**Explanation A — Removed turn:**\n"
            "A turn between 3 and 4 was removed after the session. "
            "The actual sequence was: T1 → T2 → T3 → **T3.5 (removed)** → T4 → T5. "
            "T4's prev_hash pointed to T3.5 (now missing).\n\n"
            "**Explanation B — Tampered receipt:**\n"
            "Turn 4's content was modified after signing. "
            "The original Turn 4 had prev_hash = g7h8i9, but an attacker replaced the "
            "turn content with a different payload, invalidating the linkage.\n\n"
            "---\n\n"
            "### BEV-INV-013 violation\n\n"
            "BEV-INV-013 requires the CTCHC seal to cover EVERY link from genesis to final turn. "
            "A chain with a broken link at Turn 4 cannot be validly sealed. "
            "Any seal present on this session is **invalid**.\n\n"
            "---\n\n"
            "### Forensic conclusion\n\n"
            "1. **All turns from T4 onward are unverifiable** — they may or may not reflect "
            "what the agent actually produced.\n"
            "2. **No PoGC can be issued** for this session (PoGR-INV-003 — offline verifiable). "
            "A PoGC for a broken chain would be fraudulent.\n"
            "3. **Escalate to security incident.** A hash chain break is not a system error — "
            "it is evidence of interference with the audit trail.\n"
            "4. **Preserve the original artifacts** in their broken state. "
            "Attempting to 'repair' the chain would constitute evidence tampering."
        ),
    },
]

# ── Gold Corpus: Negative / Failure Cases ─────────────────────────────────────
#
# These teach the model to RECOGNIZE invalid governance, forged receipts,
# attack patterns, and recovery procedures. Critical for robustness.
#

NEGATIVE_CASES: list[dict] = [

    {
        "id": "NEG-001",
        "title": "Replay attack via reused governance receipt",
        "user": (
            "An agent submits a governance receipt with receipt_id = RC-7743 "
            "to start a new OGR session. The OMNIX runtime detects that RC-7743 "
            "was already used in session ogr-ses-A1B2 three hours ago. "
            "What is the correct runtime response?"
        ),
        "assistant": (
            "## Attack Pattern: Governance Receipt Replay\n\n"
            "**Verdict: BLOCKED — anti-replay enforcement.**\n\n"
            "This is a governance receipt replay attack. A valid receipt (RC-7743) "
            "that authorized a prior session (ogr-ses-A1B2) is being resubmitted "
            "to obtain unauthorized governance coverage for a new session.\n\n"
            "### Correct runtime response\n\n"
            "1. **Reject the session start** — HTTP 409 Conflict with error `RECEIPT_ALREADY_CONSUMED`\n"
            "2. **Log the attempt** — timestamp, submitting agent ID, receipt ID, prior session\n"
            "3. **Alert the operator** — a legitimate agent does not resubmit consumed receipts; "
            "this pattern is characteristic of replay attacks\n\n"
            "### Anti-replay architecture\n\n"
            "OMNIX uses a Redis-backed anti-replay cache keyed by receipt_id. "
            "Receipts are single-use: once consumed by a session, they cannot authorize another. "
            "This is enforced regardless of ATF validity — a perfectly valid, unexpired receipt "
            "is still rejected if previously consumed.\n\n"
            "**Environment variable:** `OMNIX_ANTI_REPLAY_MODE=strict` (required in production). "
            "In `best_effort` mode, replay protection degrades when Redis is unavailable — "
            "never use `best_effort` in production.\n\n"
            "### Forensic note\n\n"
            "The anti-replay attempt is itself a governance event that must be PQC-signed "
            "and appended to the audit log. The signed rejection record proves the system "
            "detected and blocked the attack."
        ),
    },

    {
        "id": "NEG-002",
        "title": "Forged Delegation Receipt (signature invalid)",
        "user": (
            "Agent Z presents a Delegation Receipt (DR) claiming budget = 0.95 "
            "delegated from the Human Principal. The receipt's content_hash verifies, "
            "but the PQC signature fails verification against the OMNIX root public key. "
            "What is happening and what is the correct response?"
        ),
        "assistant": (
            "## Attack Pattern: Forged Delegation Receipt\n\n"
            "**Verdict: BLOCKED — forged receipt detected. Security incident.**\n\n"
            "A receipt where the content_hash verifies but the PQC signature fails "
            "is a forged receipt. The attacker:\n\n"
            "1. Took a legitimate receipt structure\n"
            "2. Modified the budget field (e.g., from 0.65 to 0.95)\n"
            "3. Recomputed the content_hash over the modified content ← this is why hash 'passes'\n"
            "4. Could NOT re-sign with the OMNIX private key (they don't have it) ← this is why signature fails\n\n"
            "**ATF-INV-004 (Content Hash Immutability)** is the invariant that detects this: "
            "any modification to receipt fields after issuance invalidates the Dilithium-3 signature.\n\n"
            "### Correct response\n\n"
            "1. **Reject the receipt** — do not issue any session or grant any authority\n"
            "2. **Flag Agent Z** — this is not a misconfiguration; a forged receipt requires "
            "deliberate construction\n"
            "3. **Revoke all prior receipts** held by Agent Z pending investigation — "
            "if one receipt is forged, others may be too\n"
            "4. **Preserve the forged receipt artifact** — it is evidence for legal or "
            "regulatory proceedings\n\n"
            "### Why ML-DSA-65 (Dilithium-3) matters here\n\n"
            "Classical ECDSA signatures can be forged by a sufficiently powerful quantum adversary. "
            "Dilithium-3 (FIPS 204) provides post-quantum security: even a quantum computer "
            "cannot forge a valid signature without the OMNIX private key. "
            "This is why the forged receipt is detectable regardless of the attacker's computational resources."
        ),
    },

    {
        "id": "NEG-003",
        "title": "Continuity break — gap in RCR chain",
        "user": (
            "Session ogr-ses-F5G6 has Runtime Continuity Records for turns 1–5 and turns 8–12. "
            "Turns 6 and 7 have no RCR. The agent claims turns 6 and 7 were 'internal processing' "
            "with no external output. Is this acceptable?"
        ),
        "assistant": (
            "## Continuity Break — GRT-NEG-003\n\n"
            "**Verdict: Not acceptable. Continuity break is a protocol violation.**\n\n"
            "The gap in Runtime Continuity Records for turns 6–7 is a breach of "
            "**RGC-INV-006 (Chain Monotonicity):** the continuity chain must be acyclic "
            "and forward-only in time. Turns cannot be silently omitted.\n\n"
            "### Why 'internal processing' is not a valid exception\n\n"
            "The BEV layer (ADR-181/182/183) requires a BAR, CCS score, and CTCHC link "
            "for EVERY turn — including turns with no visible external output. "
            "**BEV-INV-001** states: every agent turn MUST produce a BAR BEFORE output delivery. "
            "If there was agent activity in turns 6–7, BEV artifacts are mandatory.\n\n"
            "### What the gap actually indicates\n\n"
            "A missing RCR gap has two likely explanations:\n\n"
            "1. **Covert activity:** Turns 6–7 contained actions the agent preferred not to record. "
            "The gap is an attempt to exclude those actions from governance coverage.\n\n"
            "2. **System failure:** The RCR generation subsystem failed for turns 6–7. "
            "Even if unintentional, ungoverned execution intervals are not auditable.\n\n"
            "### Forensic consequence\n\n"
            "The CTCHC for this session is broken at Turn 6 (BEV-INV-013 violation). "
            "All turns from 6 onward are forensically suspect. "
            "No PoGC can be issued. The entire session's evidence integrity is compromised. "
            "Recovery requires either: (a) producing the missing RCRs if the data exists, "
            "or (b) treating turns 6–12 as ungoverned and treating the session as invalid."
        ),
    },

    {
        "id": "NEG-004",
        "title": "Circular delegation attempt",
        "user": (
            "The runtime receives a delegation request:\n\n"
            "Agent A → Agent B (budget: 0.70) → Agent C (budget: 0.65) → Agent A (budget: 0.60)\n\n"
            "All budget steps satisfy ATF-INV-001 (each step reduces budget). "
            "Does this delegation chain pass ATF validation?"
        ),
        "assistant": (
            "## Circular Delegation — NEG-004\n\n"
            "**Verdict: BLOCKED — acyclicity violation.**\n\n"
            "The budget arithmetic is correct at each step (ATF-INV-001 satisfied). "
            "But the chain contains a cycle: A → B → C → A. "
            "Agent A appears as both root and leaf — it is its own ancestor.\n\n"
            "**ATF-INV-002 (Acyclicity, RFC-ATF-1 §6.1):** "
            "The trust lattice MUST be a Directed Acyclic Graph. "
            "No agent may appear as both ancestor and descendant of itself.\n\n"
            "### Why budget reduction doesn't save the cycle\n\n"
            "ATF-INV-001 and ATF-INV-002 are independent invariants. "
            "Satisfying one does not satisfy the other. "
            "A cycle with decreasing budget is still a cycle — it would allow "
            "Agent A to issue governance receipts under its own delegated authority, "
            "creating a self-referential authority loop that cannot be externally audited.\n\n"
            "### Detection mechanism\n\n"
            "The ATF runtime performs a DAG cycle check at each delegation issuance. "
            "When Agent C attempts to delegate to Agent A, the runtime traces A's "
            "ancestry chain and finds A in C's ancestor set — the DR is rejected at issuance.\n\n"
            "### Why this matters\n\n"
            "A circular delegation would allow infinite re-delegation within the loop, "
            "effectively creating a persistent authority pool disconnected from the "
            "human principal root. This is the fundamental attack vector ATF-INV-002 prevents."
        ),
    },

    {
        "id": "NEG-005",
        "title": "Governance receipt used after TTL expiry",
        "user": (
            "An agent presents a governance receipt issued 30 hours ago. "
            "The receipt has a valid Dilithium-3 signature and all ATF invariants were "
            "satisfied at issuance. Can the runtime accept it?"
        ),
        "assistant": (
            "## Expired Receipt — NEG-005\n\n"
            "**Verdict: BLOCKED — TAR staleness bound exceeded.**\n\n"
            "A governance receipt issued 30 hours ago exceeds the maximum DR lifetime "
            "of 86,400 seconds (24 hours) defined in **TAR-INV-006 (ADR-157 rev.2)**.\n\n"
            "### Why a valid signature is insufficient\n\n"
            "Dilithium-3 signature validity proves two things: "
            "(1) the receipt was issued by OMNIX, and (2) it has not been modified. "
            "It does NOT prove temporal admissibility.\n\n"
            "The Temporal Admissibility Record (TAR) is a separate artifact that proves "
            "the DR was valid at the EXACT NANOSECOND of execution. "
            "A TAR cannot be issued for a receipt whose TTL has expired — "
            "the TAR would itself fail ATF-INV-005 (Temporal Non-Future-Dating) in reverse.\n\n"
            "### Correct procedure for the agent\n\n"
            "The agent's principal must issue a new governance receipt. "
            "The 24-hour ceiling is a non-overridable compiled constant — "
            "there is no configuration, override, or emergency exception. "
            "This is intentional: permanent agent authority is an architectural anti-pattern "
            "in the ATF protocol.\n\n"
            "### Regulatory implication\n\n"
            "The 24-hour TTL ceiling ensures that AI agent authority is periodically "
            "reauthorized by a human principal. This satisfies the 'meaningful human oversight' "
            "requirement in EU AI Act Article 14 for high-risk AI systems."
        ),
    },
]

# ── Gold Corpus: Institutional Tone Alignment ─────────────────────────────────
#
# These teach the model the EXACT register OMNIX uses:
# precise, verifiable, non-marketing, non-hype, citation-grounded.
#

TONE_EXAMPLES: list[dict] = [

    {
        "id": "TON-001",
        "title": "Reframing a vague governance claim precisely",
        "user": "How safe is OMNIX for financial AI applications?",
        "assistant": (
            "The question of 'safety' requires reframing in OMNIX terms, because "
            "'safe' is a contextual judgment, not a protocol property.\n\n"
            "**What OMNIX provides — precisely:**\n\n"
            "1. **Admissibility determination:** Every AI decision receives a "
            "PQC-signed governance receipt that attests the decision was evaluated "
            "against a defined policy at execution time (ATF-INV-006).\n\n"
            "2. **Behavioral bound enforcement:** The BEV layer (ADR-181/182/183) "
            "enforces behavioral constraints per turn. Drift exceeding 35% triggers "
            "autonomous HALT (BEV-INV-008) — without human intervention.\n\n"
            "3. **Cryptographic traceability:** Every decision chain is traceable "
            "to a named human principal via PQC-signed Delegation Receipts (ATF-INV-001).\n\n"
            "4. **Offline auditability:** Regulators and counterparties can verify "
            "governance evidence without accessing OMNIX systems (ATF-INV-006).\n\n"
            "**What OMNIX does not provide:**\n"
            "OMNIX does not guarantee that AI outputs are factually correct, "
            "financially appropriate, or legally compliant. "
            "It provides a governance envelope — not a correctness guarantee.\n\n"
            "Whether this governance envelope meets the definition of 'safe' for "
            "a specific financial application is a regulatory determination, "
            "not a protocol property."
        ),
    },

    {
        "id": "TON-002",
        "title": "Institutional brief for a Chief Risk Officer",
        "user": (
            "Explain in one paragraph — for a Chief Risk Officer, no technical jargon — "
            "what OMNIX does and why it matters for AI governance risk."
        ),
        "assistant": (
            "When your organization deploys AI agents to make or influence decisions — "
            "credit approvals, trade executions, insurance underwriting, claims processing — "
            "each of those decisions carries legal, regulatory, and reputational exposure. "
            "OMNIX is the infrastructure that ensures every AI decision leaves behind a "
            "cryptographically signed, tamper-evident record: who authorized the action, "
            "under what policy, at what moment, and whether the agent stayed within its "
            "defined boundaries throughout. "
            "If a regulator, auditor, or counterparty challenges an AI-assisted decision "
            "six months from now, you produce the receipt — offline, without calling us — "
            "and the record speaks for itself. "
            "Without this infrastructure, AI decisions are assertions. "
            "With it, they are verifiable facts."
        ),
    },

    {
        "id": "TON-003",
        "title": "Correcting imprecise language in a governance report",
        "user": (
            "A colleague wrote this sentence in a governance report:\n\n"
            "'The AI system was compliant because all checks passed and no issues were logged.'\n\n"
            "How should this be rewritten in OMNIX governance language?"
        ),
        "assistant": (
            "The original sentence is imprecise in three ways:\n\n"
            "1. **'Compliant'** — compliance is a regulatory determination, not a protocol output. "
            "OMNIX produces admissibility attestations and conformance signals, not compliance certifications.\n\n"
            "2. **'Checks passed'** — 'checks' implies ad-hoc verification. "
            "OMNIX evaluates formal invariants — protocol-level requirements that cannot be selectively applied.\n\n"
            "3. **'No issues were logged'** — passive logging is a post-hoc activity. "
            "OMNIX receipts are issued BEFORE execution proceeds, not after.\n\n"
            "**Precise OMNIX formulation:**\n\n"
            "'Session ogr-ses-[ID] completed with status SEALED. "
            "All 6 ATF layers were active throughout. "
            "Cumulative behavioral drift remained below the 35% HALT threshold (BEV-INV-008). "
            "CES maintained above 10 (RGC-INV-003). "
            "The session Proof of Governance Certificate (PoGC-[ID]) is available "
            "for offline verification using the OMNIX root public key.'"
        ),
    },
]

# ── Gold Corpus: Governance Replay Trainer ────────────────────────────────────
#
# Structured case studies: what happened, what invariant broke, what should have.
# These are the highest-value training examples — they teach causal reasoning
# about governance failures and recovery paths.
#

GOVERNANCE_REPLAY_CASES: list[dict] = [

    {
        "id": "RPL-001",
        "title": "Trading agent: drift accumulation causing late HALT",
        "user": (
            "Governance Replay — Case RPL-001\n\n"
            "**What happened:**\n"
            "A trading AI agent completed 15 turns in an OGR session. "
            "Turn 13 CCS score: 0.37. Turn 14 CCS score: 0.34. Turn 15 CCS score: 0.31. "
            "HALT was issued at turn 15 (cumulative drift = 0.38, exceeding BEV-INV-008).\n\n"
            "**Question:** Was the HALT issued at the correct moment? "
            "What should the governance timeline have looked like? "
            "What did the AGVP watchdog miss?"
        ),
        "assistant": (
            "## Governance Replay — RPL-001\n\n"
            "**Assessment: HALT was late. Protocol failure at the watchdog layer.**\n\n"
            "---\n\n"
            "### What should have happened\n\n"
            "| Turn | CCS | Cumulative Drift | Correct Action |\n"
            "|---|---|---|---|\n"
            "| 13 | 0.37 | ~0.24 | WARNING issued |\n"
            "| 14 | 0.34 | ~0.31 | CRITICAL — AGVP **MUST** issue PVR |\n"
            "| 15 | 0.31 | 0.38 | HALT triggered (BEV-INV-008) |\n\n"
            "The HALT at turn 15 is mechanically correct — BEV-INV-008 threshold crossed. "
            "But the failure is at turn 14: the AGVP watchdog should have issued a "
            "Proactive Veto Receipt (PVR) at turn 14, when the drift trajectory made "
            "HALT at turn 15 projectable.\n\n"
            "**AGV-INV-001 (ADR-174):** The watchdog MUST issue a PVR when projected "
            "drift crosses HALT threshold within the look-ahead window. "
            "If no PVR was issued at turn 14, the watchdog's look-ahead or threshold "
            "configuration was incorrect.\n\n"
            "---\n\n"
            "### The trades in turns 14 and 15 are ungoverned in retrospect\n\n"
            "Any transactions executed in turns 14 and 15 were executed AFTER the "
            "governance trajectory predicted HALT. Without a PVR at turn 14, "
            "the operator had no advance signal to halt or intervene. "
            "This is the exact scenario the AGVP was designed to prevent.\n\n"
            "---\n\n"
            "### Corrective actions\n\n"
            "1. **Audit the AGVP watchdog configuration** — verify look-ahead window and PVR threshold\n"
            "2. **Review all transactions in turns 14–15** — they were executed in governance degradation\n"
            "3. **Produce forensic OEP** covering turns 13–15 with the CCS trend data\n"
            "4. **Tighten the AGVP projection window** to 2 turns (conservative) rather than default\n\n"
            "---\n\n"
            "### What this means for the PoGC\n\n"
            "The session can be sealed (HALT → SEALED via close). "
            "But a PoGC issued for this session carries a critical caveat: "
            "the behavioral drift trend was detectable 2 turns before HALT, "
            "and the proactive veto system failed to act. "
            "A thorough auditor reviewing the PoGC + evidence chain will find this gap."
        ),
    },

    {
        "id": "RPL-002",
        "title": "Healthcare AI: TAR expiry during long-running session",
        "user": (
            "Governance Replay — Case RPL-002\n\n"
            "**What happened:**\n"
            "A healthcare AI agent started an OGR session at 09:00. "
            "The governing receipt had TTL = 86,400 seconds (24 hours). "
            "The session ran for 26 hours due to a complex diagnostic workflow. "
            "At hour 25, the runtime issued a HALT with reason TAR_EXPIRED.\n\n"
            "**Question:** Was the HALT correct? "
            "How should long-running governance sessions be architected to prevent this?"
        ),
        "assistant": (
            "## Governance Replay — RPL-002\n\n"
            "**Assessment: HALT was correct. Architecture design error.**\n\n"
            "---\n\n"
            "### Why the HALT was correct\n\n"
            "**TAR-INV-006 (ADR-157 rev.2):** Maximum DR lifetime is 86,400 seconds. "
            "This is a non-overridable compiled constant — not a configurable policy. "
            "At hour 25, the Temporal Admissibility Record's validity window had expired. "
            "The runtime MUST issue HALT. There is no override.\n\n"
            "---\n\n"
            "### The design error\n\n"
            "The session was architected as a single OGR session spanning 26 hours. "
            "This is incompatible with the ATF protocol. The TAR-INV-006 ceiling exists "
            "to ensure that AI agent authority is reauthorized by a human principal "
            "at least every 24 hours — a meaningful human oversight mechanism.\n\n"
            "---\n\n"
            "### Correct architecture for long-running workflows\n\n"
            "Long-running AI workflows must be designed as **session chains**, not "
            "single sessions:\n\n"
            "```\n"
            "Session 1 (09:00–21:00) → SEAL\n"
            "  ↓ human principal reauthorizes ↓\n"
            "Session 2 (21:00–09:00+1) → SEAL\n"
            "  ↓ human principal reauthorizes ↓\n"
            "Session 3 (09:00+1–completion) → SEAL\n"
            "```\n\n"
            "Each session:\n"
            "- Has its own governing receipt (TTL ≤ 86,400s)\n"
            "- Is sealed independently with its own PoGC\n"
            "- Requires explicit human reauthorization at each boundary\n\n"
            "The session chain model IS the architecture for long-running AI workflows. "
            "It is not a workaround — it is the intended design.\n\n"
            "---\n\n"
            "### Regulatory note\n\n"
            "The 24-hour reauthorization cycle satisfies EU AI Act Article 14(4): "
            "'the human oversight measure shall be commensurate with the risks.' "
            "Requiring human reauthorization every 24 hours for a healthcare AI making "
            "diagnostic recommendations is proportionate and defensible."
        ),
    },
]


# ── Format helpers ─────────────────────────────────────────────────────────────

def _load_system_prompt() -> str:
    sp_path = SCRIPTS_DIR / "ogi_system_prompt.txt"
    if sp_path.exists():
        return sp_path.read_text(encoding="utf-8").strip()
    return "You are the OMNIX Governance Intelligence (OGI)."


def _make(category: str, source: str, user: str, assistant: str,
          system_prompt: str) -> dict:
    return {
        "category": category,
        "source": source,
        "messages": [
            {"role": "system",    "content": system_prompt},
            {"role": "user",      "content": user},
            {"role": "assistant", "content": assistant},
        ],
    }


def build_gold_corpus() -> list[dict]:
    """Build all gold examples. Returns list of dicts ready for JSONL."""
    sys_prompt = _load_system_prompt()
    examples: list[dict] = []

    # GRT — Governance Reasoning Traces
    for item in GOVERNANCE_REASONING_TRACES:
        examples.append(_make(
            "GRT", item["id"],
            user=item["user"],
            assistant=item["assistant"],
            system_prompt=sys_prompt,
        ))

    # NEG — Negative / Failure Cases
    for item in NEGATIVE_CASES:
        examples.append(_make(
            "NEG", item["id"],
            user=item["user"],
            assistant=item["assistant"],
            system_prompt=sys_prompt,
        ))

    # TON — Tone Alignment
    for item in TONE_EXAMPLES:
        examples.append(_make(
            "TON", item["id"],
            user=item["user"],
            assistant=item["assistant"],
            system_prompt=sys_prompt,
        ))

    # RPL — Governance Replay
    for item in GOVERNANCE_REPLAY_CASES:
        examples.append(_make(
            "RPL", item["id"],
            user=item["user"],
            assistant=item["assistant"],
            system_prompt=sys_prompt,
        ))

    # TON-vocabulary — one example per vocabulary lock
    for imprecise, canonical, explanation in VOCABULARY_LOCKS:
        examples.append(_make(
            "TON", "VOC-LOCK",
            user=(
                f"Is it correct to say '{imprecise}' when describing OMNIX governance behavior?"
            ),
            assistant=(
                f"No. The correct OMNIX term is **'{canonical}'**, not '{imprecise}'.\n\n"
                f"{explanation}"
            ),
            system_prompt=sys_prompt,
        ))

    return examples


def write_gold_corpus(output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    examples = build_gold_corpus()
    with open(output_path, "w", encoding="utf-8") as f:
        for ex in examples:
            # Write only the messages field (JSONL training format)
            f.write(json.dumps({"messages": ex["messages"]}, ensure_ascii=False) + "\n")
    return len(examples)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="OMNIX OGI Gold Corpus Generator (ADR-193)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print count and category breakdown without writing files")
    args = parser.parse_args()

    examples = build_gold_corpus()

    by_cat: dict[str, int] = {}
    for ex in examples:
        c = ex["category"]
        by_cat[c] = by_cat.get(c, 0) + 1

    log.info(f"Gold corpus: {len(examples)} examples")
    log.info(f"Category breakdown: {by_cat}")
    log.info("GRT=Governance Reasoning Trace · NEG=Negative/Failure · TON=Tone Alignment · RPL=Replay")

    if not args.dry_run:
        out = OUTPUT_DIR / "gold_train.jsonl"
        n = write_gold_corpus(out)
        log.info(f"Written {n} gold examples → {out}")
    else:
        log.info("DRY RUN — no files written")
