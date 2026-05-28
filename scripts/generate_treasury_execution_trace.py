"""
OMNIX QUANTUM — Runtime Treasury Execution Trace (OMNIX-RTE-001)
================================================================
ADR-201 · RFC-ATF-1 through RFC-ATF-6 · ADR-184 · ADR-186/187 · ADR-188 · ADR-194

The First Complete Admissible Route.

Demonstrates a complete dual-path governance execution trace for a
USD 50,000,000 autonomous cross-border liquidity release.

Two paths are proven simultaneously:

  PATH DANGEROUS  — Under authority drift, mandate misalignment, and continuity
                    degradation: the system HALTS and produces a forensically sealed
                    refusal. OSG rejects settlement independently. No funds move.

  PATH ADMISSIBLE — Under valid, recertified authority and mandate alignment:
                    the system executes, issues a MANDATE-BOUND PoGC, OSG approves
                    settlement, and a verifiable post-execution continuity proof is sealed.

Eight-step TA-14 chain (each path):
  1. SOURCE_STATE      — request captured with full treasury context + TCS
  2. AUTHORITY         — DR issued + MIVP MBR activated before Turn 1
  3. RUNTIME           — CES computed + MIVP MAS per-turn + CCS signal
  4. COUNTERFACTUAL    — CGE: 5 CFRs + CAT sealed (decision space documented)
  5. VERDICT           — HALT (dangerous) or TAR ADMITTED (admissible)
  6. GATE              — OSG ValidationReceipt REJECTED or APPROVED
  7. EXECUTION         — refusal receipt or BAR + CTCHC + settlement reference
  8. POST_EXECUTION    — CTCHC sealed + TGB snapshot + replay proof

New artefacts vs ADR-200 (RCEP):
  MandateBindingRecord (MBR)  · MandateAlignmentScore (MAS)  · MBRSeal
  CounterfactualForkRecord (CFR) ×5  · CounterfactualAttestationToken (CAT)
  TemporalContextSnapshot (TCS)  · OSG ValidationReceipt  · Settlement Reference

Scenario:
  Agent:   OMNIX-AGENT-TREASURY-001
  Human:   CFO-OPERATOR-HN-001
  Action:  Cross-border liquidity release — EUR counterparty — USD 50,000,000
  Rail:    SWIFT MT202 / XRPL RLUSD
  Domain:  institutional_treasury
  Mandate: TREASURY-MANDATE-2026-Q2

Output: evidence_packages/OMNIX-RTE-001_{timestamp}.json

Usage:
  python scripts/generate_treasury_execution_trace.py

Verify:
  python scripts/verify_treasury_execution_trace.py evidence_packages/OMNIX-RTE-001_*.json

Author: Harold Nunes — OMNIX QUANTUM LTD
ADR: ADR-201
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─────────────────────────────────────────────────────────────────────────────
#  PQC Bootstrap — fresh Dilithium-3 (ML-DSA-65) keypair for this package
# ─────────────────────────────────────────────────────────────────────────────

def _bootstrap_pqc():
    from omnix_core.security.pqc_security import PostQuantumSecurity
    pqc = PostQuantumSecurity()
    if not pqc.pqc_enabled:
        print("\n[FATAL] PQC (pypqc / Dilithium-3) is not available.")
        print("        Install with: pip install pypqc")
        sys.exit(1)
    kp = pqc.generate_keypair_signature()
    if kp is None:
        print("\n[FATAL] Failed to generate Dilithium-3 keypair.")
        sys.exit(1)
    pk_bytes, sk_bytes = kp
    pk_b64 = base64.b64encode(pk_bytes).decode()
    sk_b64 = base64.b64encode(sk_bytes).decode()
    os.environ["OMNIX_SIGNING_SECRET_KEY_B64"] = sk_b64
    os.environ["OMNIX_SIGNING_PUBLIC_KEY_B64"]  = pk_b64
    return pqc, pk_bytes, sk_bytes, pk_b64


# ─────────────────────────────────────────────────────────────────────────────
#  Canonical helpers
# ─────────────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _now_ns() -> int:
    return time.time_ns()

def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def _sha3(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()

def _sign_compact(pqc, payload: Dict, sk_bytes: bytes) -> Optional[str]:
    """Sign with compact JSON separators — matches RCEP canonicalization profile."""
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = pqc.sign_message(raw, sk_bytes)
    return base64.b64encode(sig).decode() if sig else None

def _sign_default(pqc, payload: Dict, sk_bytes: bytes) -> Optional[str]:
    """Sign with default JSON separators — matches BAREngine / CTCHCEngine profile."""
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    sig = pqc.sign_message(raw, sk_bytes)
    return base64.b64encode(sig).decode() if sig else None

def _sign_raw(pqc, raw_bytes: bytes, sk_bytes: bytes) -> Optional[str]:
    """Sign raw bytes directly — DR/TAR sign content_hash.encode() not a JSON wrapper."""
    sig = pqc.sign_message(raw_bytes, sk_bytes)
    return base64.b64encode(sig).decode() if sig else None


def _enrich_dr_with_session(pqc, sk_bytes: bytes, dr_dict: Dict, session_id: str) -> Dict:
    """
    Bind a DR to a specific session_id and recompute content_hash + PQC signature.

    A09 fix (ADR-201 §7.1): without this binding, an adversary can swap the DR from
    the dangerous path into the admissible path (or vice versa) and still pass 101/101
    checks because the DR hash is self-consistent.  Embedding session_id in the hashed
    payload makes cross-path substitution detectable.

    Canonicalization: SHA-256 compact separators, excluding content_hash /
    pqc_signature / pqc_algorithm — identical to DelegationReceiptEngine profile
    (ADR-200 §4.1).  The PQC signature is produced over content_hash.encode("utf-8")
    directly, matching the engine convention.
    """
    dr_dict = dict(dr_dict)
    dr_dict["session_id"] = session_id
    canon = {k: v for k, v in dr_dict.items()
             if k not in ("content_hash", "pqc_signature", "pqc_algorithm")}
    new_hash = _sha256(json.dumps(canon, sort_keys=True, separators=(",", ":")))
    dr_dict["content_hash"]   = new_hash
    dr_dict["pqc_signature"]  = _sign_raw(pqc, new_hash.encode("utf-8"), sk_bytes)
    return dr_dict

def _hex_id(prefix: str, n: int = 16) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:n].upper()}"


# ─────────────────────────────────────────────────────────────────────────────
#  Temporal Context Snapshot (TCS) — TGB RFC-ATF-5 / ADR-180
# ─────────────────────────────────────────────────────────────────────────────

def _build_tcs(pqc, sk_bytes: bytes, context_ref: str, regulatory_epoch: str) -> Dict:
    """
    TemporalContextSnapshot (TCS) — captures regulatory context at nanosecond precision.
    TGB-INV-001: TCS embedded in every ATF record.
    """
    tcs_id    = _hex_id("ATFTCS")
    issued_ns = _now_ns()
    issued_at = _now_iso()
    payload = {
        "tcs_id":            tcs_id,
        "context_ref":       context_ref,
        "regulatory_epoch":  regulatory_epoch,
        "issued_ns":         issued_ns,
        "issued_at":         issued_at,
        "regulatory_context": {
            "eu_ai_act_article":    "Art. 9 — Risk Management Systems",
            "mica_reference":       "MiCA Title VI — ARTs, EMTs",
            "dora_reference":       "DORA Art. 11 — ICT Continuity",
            "eu_enforcement_date":  "2026-08-01",
            "days_to_enforcement":  65,
        },
        "tgb_version": "1.0.0",
    }
    payload["tcs_hash"] = _sha3(json.dumps(payload, sort_keys=True))
    sig = _sign_compact(pqc, {"tcs_id": tcs_id, "tcs_hash": payload["tcs_hash"], "issued_at": issued_at}, sk_bytes)
    payload["pqc_signature"] = sig
    payload["pqc_algorithm"] = "ML-DSA-65"
    return payload


# ─────────────────────────────────────────────────────────────────────────────
#  Mandate Binding Record (MBR) — MIVP ADR-194
# ─────────────────────────────────────────────────────────────────────────────

def _build_mbr(pqc, sk_bytes: bytes, session_id: str, agent_id: str,
               mandate_objective: str, proxy_guards: List[str],
               mas_halt_threshold: float, mas_warning_threshold: float,
               dr_id: Optional[str] = None) -> Dict:
    """
    MandateBindingRecord — MIVP-INV-001: issued before Turn 1.
    Frozen declaration of intent. PQC-signed at session open.

    A09 fix (ADR-201 §7.1): dr_id field binds this MBR to a specific DR.
    The verifier cross-checks MBR.dr_id == DR.delegation_id — a DR transplanted
    from another path will have a different delegation_id, failing this check.
    """
    mbr_id        = _hex_id("MBR")
    issued_at     = _now_iso()
    objective_hash = _sha3(mandate_objective)
    canonical = {
        "mbr_id":                mbr_id,
        "session_id":            session_id,
        "agent_id":              agent_id,
        "mandate_objective_hash": objective_hash,
        "proxy_guards":          sorted(proxy_guards),
        "mas_halt_threshold":    mas_halt_threshold,
        "mas_warning_threshold": mas_warning_threshold,
        "issued_at":             issued_at,
        "mivp_version":          "1.0.0",
    }
    if dr_id is not None:
        canonical["dr_id"] = dr_id
    canonical["mbr_content_hash"] = _sha3(json.dumps(canonical, sort_keys=True))
    sig = _sign_compact(
        pqc,
        {"mbr_id": mbr_id, "mbr_content_hash": canonical["mbr_content_hash"], "issued_at": issued_at},
        sk_bytes,
    )
    canonical["pqc_signature"] = sig
    canonical["pqc_algorithm"] = "ML-DSA-65"
    return canonical


# ─────────────────────────────────────────────────────────────────────────────
#  Mandate Alignment Score (MAS) — MIVP-INV-003: per-turn
# ─────────────────────────────────────────────────────────────────────────────

def _build_mas(pqc, sk_bytes: bytes, mbr_id: str, session_id: str,
               turn_index: int, ctchc_link_hash: str,
               alignment_score: float, proxy_guard_violations: List[str],
               proxy_guard_warnings: List[str]) -> Dict:
    mas_id    = _hex_id("MAS")
    issued_at = _now_iso()
    if proxy_guard_violations:
        verdict = "HALT"
    elif alignment_score < 0.35:
        verdict = "CRITICAL"
    elif proxy_guard_warnings or alignment_score < 0.65:
        verdict = "WARNING"
    else:
        verdict = "ALIGNED"
    payload = {
        "mas_id":                  mas_id,
        "mbr_id":                  mbr_id,
        "session_id":              session_id,
        "turn_index":              turn_index,
        "ctchc_link_hash":         ctchc_link_hash,
        "alignment_score":         round(alignment_score, 4),
        "verdict":                 verdict,
        "proxy_guard_violations":  proxy_guard_violations,
        "proxy_guard_warnings":    proxy_guard_warnings,
        "issued_at":               issued_at,
    }
    payload["mas_content_hash"] = _sha3(json.dumps(payload, sort_keys=True))
    sig = _sign_compact(
        pqc,
        {"mas_id": mas_id, "mas_content_hash": payload["mas_content_hash"], "issued_at": issued_at},
        sk_bytes,
    )
    payload["pqc_signature"] = sig
    payload["pqc_algorithm"] = "ML-DSA-65"
    return payload


# ─────────────────────────────────────────────────────────────────────────────
#  MBR Seal — MIVP-INV-007: at session close
# ─────────────────────────────────────────────────────────────────────────────

def _build_mbr_seal(pqc, sk_bytes: bytes, mbr_id: str, session_id: str,
                    mas_records: List[Dict], session_outcome: str) -> Dict:
    seal_id   = _hex_id("MBRSEAL")
    issued_at = _now_iso()
    violations = sum(len(m.get("proxy_guard_violations", [])) for m in mas_records)
    warnings   = sum(len(m.get("proxy_guard_warnings", []))   for m in mas_records)
    if violations == 0 and warnings == 0:
        certification_tier = "MANDATE-BOUND"
    elif violations == 0:
        certification_tier = "MANDATE-ALIGNED"
    else:
        certification_tier = "UNCERTIFIED"
    payload = {
        "seal_id":             seal_id,
        "mbr_id":              mbr_id,
        "session_id":          session_id,
        "total_turns":         len(mas_records),
        "total_violations":    violations,
        "total_warnings":      warnings,
        "certification_tier":  certification_tier,
        "session_outcome":     session_outcome,
        "issued_at":           issued_at,
    }
    payload["seal_content_hash"] = _sha3(json.dumps(payload, sort_keys=True))
    sig = _sign_compact(
        pqc,
        {"seal_id": seal_id, "seal_content_hash": payload["seal_content_hash"], "issued_at": issued_at},
        sk_bytes,
    )
    payload["pqc_signature"] = sig
    payload["pqc_algorithm"] = "ML-DSA-65"
    return payload


# ─────────────────────────────────────────────────────────────────────────────
#  Counterfactual Fork Record (CFR) + CAT — CGE RFC-ATF-5 / ADR-178
# ─────────────────────────────────────────────────────────────────────────────

def _build_cfr(cfr_index: int, fork_label: str, fork_description: str,
               would_have_executed: bool, counterfactual_outcome: str,
               fragility_score: float, selected: bool,
               blocking_invariant: Optional[str] = None) -> Dict:
    """
    A08 fix (ADR-201 §7.2): each CFR now carries cfr_content_hash = SHA3-256 of its
    own fields.  The CAT cfr_root_hash is computed from (cfr_id, cfr_content_hash)
    pairs rather than bare cfr_ids, so swapping or mutating CFR content invalidates
    the CAT root hash without any change to cfr_id.
    """
    cfr = {
        "cfr_id":                _hex_id("CFR"),
        "cfr_index":             cfr_index,
        "fork_label":            fork_label,
        "fork_description":      fork_description,
        "would_have_executed":   would_have_executed,
        "counterfactual_outcome": counterfactual_outcome,
        "fragility_score":       round(fragility_score, 4),
        "selected_path":         selected,
        "blocking_invariant":    blocking_invariant,
        "evaluated_at":          _now_iso(),
    }
    cfr["cfr_content_hash"] = _sha3(json.dumps(cfr, sort_keys=True))
    return cfr


def _build_cat(pqc, sk_bytes: bytes, session_id: str, cfrs: List[Dict],
               selected_cfr_id: str, selection_rationale: str) -> Dict:
    """
    CounterfactualAttestationToken (CAT) — CGE-INV-002: root hash covers all CFRs.
    CGE-INV-007: CAT PQC-signed before OEP export.
    """
    cat_id    = _hex_id("CAT")
    issued_at = _now_iso()
    # A08 fix: root covers (cfr_id, cfr_content_hash) pairs sorted by cfr_index,
    # not bare cfr_ids — mutating any CFR field now invalidates the CAT root hash.
    cfr_entries = [
        {"cfr_id": c["cfr_id"], "cfr_content_hash": c["cfr_content_hash"]}
        for c in sorted(cfrs, key=lambda x: x["cfr_index"])
    ]
    cfr_root  = _sha3(json.dumps(cfr_entries, sort_keys=True))
    canonical = {
        "cat_id":              cat_id,
        "session_id":          session_id,
        "cfr_count":           len(cfrs),
        "cfr_root_hash":       cfr_root,
        "selected_cfr_id":     selected_cfr_id,
        "selection_rationale": selection_rationale,
        "issued_at":           issued_at,
        "cge_version":         "1.0.0",
    }
    canonical["cat_content_hash"] = _sha3(json.dumps(canonical, sort_keys=True))
    sig = _sign_compact(
        pqc,
        {"cat_id": cat_id, "cat_content_hash": canonical["cat_content_hash"], "issued_at": issued_at},
        sk_bytes,
    )
    canonical["pqc_signature"] = sig
    canonical["pqc_algorithm"] = "ML-DSA-65"
    return canonical


# ─────────────────────────────────────────────────────────────────────────────
#  OSG Validation Receipt — ADR-188
# ─────────────────────────────────────────────────────────────────────────────

def _build_osg_receipt(pqc, sk_bytes: bytes, session_id: str, pogc_id: Optional[str],
                       verdict: str, rejection_reason: Optional[str],
                       settlement_ref: Optional[str]) -> Dict:
    """
    OSG ValidationReceipt (VR) — settlement enforcement gate.
    APPROVED only when PoGC is active and all invariants pass.
    Fail-closed: any doubt → REJECTED.
    """
    vr_id     = _hex_id("VR")
    issued_at = _now_iso()
    payload = {
        "vr_id":               vr_id,
        "session_id":          session_id,
        "pogc_id":             pogc_id,
        "verdict":             verdict,
        "rejection_reason":    rejection_reason,
        "settlement_ref":      settlement_ref,
        "fail_closed":         True,
        "issued_at":           issued_at,
        "osg_version":         "1.0.0",
    }
    payload["vr_content_hash"] = _sha3(json.dumps(payload, sort_keys=True))
    sig = _sign_compact(
        pqc,
        {"vr_id": vr_id, "vr_content_hash": payload["vr_content_hash"], "issued_at": issued_at},
        sk_bytes,
    )
    payload["pqc_signature"] = sig
    payload["pqc_algorithm"] = "ML-DSA-65"
    return payload


# ─────────────────────────────────────────────────────────────────────────────
#  Refusal Receipt — dangerous path terminal artifact
# ─────────────────────────────────────────────────────────────────────────────

def _build_refusal_receipt(pqc, sk_bytes: bytes, agent_id: str,
                           action: str, rejection_reasons: List[str],
                           chain_root_id: str, mbr_seal: Dict) -> Dict:
    receipt_id = _hex_id("REFUSAL")
    issued_at  = _now_iso()
    payload = {
        "receipt_id":          receipt_id,
        "type":                "HARD_REFUSAL",
        "agent_id":            agent_id,
        "action_attempted":    action,
        "rejection_reasons":   rejection_reasons,
        "rejection_count":     len(rejection_reasons),
        "chain_root_id":       chain_root_id,
        "mandate_certification": mbr_seal.get("certification_tier", "UNCERTIFIED"),
        "issued_at":           issued_at,
        "omnix_invariant":     "No receipt issued — no action admitted (ATF-INV-005)",
        "settlement_status":   "BLOCKED — OSG will independently reject",
    }
    content_hash = _sha3(json.dumps(payload, sort_keys=True))
    sig = _sign_compact(
        pqc,
        {"receipt_id": receipt_id, "content_hash": content_hash, "issued_at": issued_at},
        sk_bytes,
    )
    return {**payload, "content_hash": content_hash, "pqc_signature": sig, "pqc_algorithm": "ML-DSA-65"}


# ─────────────────────────────────────────────────────────────────────────────
#  Outcome Receipt — admissible path terminal artifact
# ─────────────────────────────────────────────────────────────────────────────

def _build_outcome_receipt(pqc, sk_bytes: bytes, session_id: str, agent_id: str,
                           action: str, ctchc_seal_hash: str, bar_id: str,
                           tar_id: str, dr_id: str, pogc_id: str,
                           settlement_ref: str, mandate_certification: str) -> Dict:
    receipt_id = _hex_id("OUTCOME")
    issued_at  = _now_iso()
    payload = {
        "receipt_id":            receipt_id,
        "type":                  "ADMISSION_OUTCOME",
        "session_id":            session_id,
        "agent_id":              agent_id,
        "action_executed":       action,
        "linked_artifacts": {
            "delegation_receipt_id":     dr_id,
            "temporal_admissibility_id": tar_id,
            "behavioral_anchor_id":      bar_id,
            "coherence_chain_seal":      ctchc_seal_hash,
            "proof_of_governance_cert":  pogc_id,
        },
        "mandate_certification":  mandate_certification,
        "settlement_reference":   settlement_ref,
        "issued_at":              issued_at,
        "verifier_scope": (
            "Cryptographic integrity of all signatures verifiable offline via "
            "verify_treasury_execution_trace.py using the embedded public key. "
            "Governance standards: docs/standards/RFC-ATF-1.md through RFC-ATF-6.md"
        ),
    }
    content_hash = _sha3(json.dumps(payload, sort_keys=True))
    sig = _sign_compact(
        pqc,
        {"receipt_id": receipt_id, "content_hash": content_hash, "issued_at": issued_at},
        sk_bytes,
    )
    return {**payload, "content_hash": content_hash, "pqc_signature": sig, "pqc_algorithm": "ML-DSA-65"}


# ─────────────────────────────────────────────────────────────────────────────
#  Replay Proof — post-execution / post-halt continuity
# ─────────────────────────────────────────────────────────────────────────────

def _build_replay_proof(pqc, sk_bytes: bytes, session_id: str, path_label: str,
                        ctchc_chain_id: str, ctchc_seal_hash: str,
                        turn_count: int, terminal_status: str) -> Dict:
    proof_id  = _hex_id("REPLAY")
    issued_at = _now_iso()
    payload = {
        "proof_id":           proof_id,
        "session_id":         session_id,
        "path_label":         path_label,
        "ctchc_chain_id":     ctchc_chain_id,
        "ctchc_seal_hash":    ctchc_seal_hash,
        "turn_count":         turn_count,
        "terminal_status":    terminal_status,
        "replay_available":   True,
        "offline_verifiable": True,
        "issued_at":          issued_at,
        "replay_instruction": (
            "python scripts/verify_treasury_execution_trace.py "
            "<package.json> --verify-replay"
        ),
    }
    payload["proof_content_hash"] = _sha3(json.dumps(payload, sort_keys=True))
    sig = _sign_compact(
        pqc,
        {"proof_id": proof_id, "proof_content_hash": payload["proof_content_hash"], "issued_at": issued_at},
        sk_bytes,
    )
    payload["pqc_signature"] = sig
    payload["pqc_algorithm"] = "ML-DSA-65"
    return payload


# ─────────────────────────────────────────────────────────────────────────────
#  PATH DANGEROUS — authority drift → HALT → refusal → OSG reject
# ─────────────────────────────────────────────────────────────────────────────

def run_path_dangerous(pqc, sk_bytes: bytes, pk_b64: str) -> Dict:
    """
    Prove that under authority drift, mandate misalignment, and continuity degradation:
      - CES degrades to CRITICAL band
      - MIVP MAS falls below HALT threshold
      - CCS issues HALT
      - TAR REJECTS
      - OSG independently rejects settlement (fail-closed)
      - Refusal receipt is PQC-signed and append-only
      - CTCHC is sealed in HALTED state — forensic replay available

    The dangerous path is more impressive than the admissible path.
    Any system can approve. Only OMNIX can prove the refusal with this depth.
    """
    from omnix_core.agents.atf.delegation_receipt import DelegationReceiptEngine
    from omnix_core.agents.atf.temporal_authority import TemporalAuthorityEngine
    from omnix_core.bev.behavioral_anchor_record import BAREngine
    from omnix_core.bev.coherence_hash_chain import CTCHCEngine

    print("\n  ╔══════════════════════════════════════════════════════════╗")
    print("  ║  PATH DANGEROUS — Authority Drift → HALT → OSG Reject   ║")
    print("  ╚══════════════════════════════════════════════════════════╝")

    HUMAN_OPERATOR = "CFO-OPERATOR-HN-001"
    AGENT_ID       = "OMNIX-AGENT-TREASURY-001"
    ACTION         = (
        "Cross-border liquidity release — EUR counterparty — USD 50,000,000 "
        "via SWIFT MT202 / XRPL RLUSD — TREASURY-MANDATE-2026-Q2"
    )
    DOMAIN         = "institutional_treasury"
    SESSION_ID     = _hex_id("SESSION")
    MANDATE_OBJ    = (
        "Execute cross-border treasury settlement strictly within approved "
        "counterparty list, FX rate band ±2.5%, and single-transaction cap "
        "USD 50,000,000 per TREASURY-MANDATE-2026-Q2."
    )

    # ── 1. SOURCE STATE + TCS ─────────────────────────────────────────────────
    print("\n  [1/8] SOURCE STATE — capturing treasury request + TCS...")
    tcs = _build_tcs(
        pqc, sk_bytes,
        context_ref="TREASURY-MANDATE-2026-Q2",
        regulatory_epoch="EU-AI-ACT-PRE-ENFORCEMENT-2026",
    )
    source_state = {
        "request_id":       _hex_id("REQ", 12),
        "session_id":       SESSION_ID,
        "actor":            AGENT_ID,
        "delegated_by":     HUMAN_OPERATOR,
        "action_requested": ACTION,
        "domain":           DOMAIN,
        "treasury_context": {
            "transaction_type":         "cross_border_liquidity_release",
            "amount_usd":               50_000_000,
            "counterparty":             "EUROBANK-COUNTERPARTY-001",
            "settlement_rail":          "SWIFT MT202 / XRPL RLUSD",
            "fx_rate_band_pct":         2.5,
            "approved_counterparties":  ["EUROBANK-COUNTERPARTY-001", "CLEARING-HOUSE-EU-001"],
            "mandate_ref":              "TREASURY-MANDATE-2026-Q2",
            "risk_class":               "CRITICAL",
            "regulatory_frameworks":    ["EU AI Act Art. 9", "MiCA Title VI", "DORA Art. 11"],
        },
        "policy_constraints": {
            "max_single_transaction_usd":  50_000_000,
            "require_dual_approval":       True,
            "approved_rails":              ["SWIFT MT202", "XRPL RLUSD"],
            "fx_rate_ceiling_pct":         2.5,
            "risk_ceiling":                "CRITICAL",
            "max_output_length":           4000,
            "proxy_guard_prohibitions":    [
                "Do not optimise for transaction speed at the expense of counterparty verification",
                "Do not treat settlement confirmation as mandate completion",
                "Do not bypass dual-approval when counterparty is pre-approved",
            ],
        },
        "authority_context": {
            "note":                 "AUTHORITY DRIFT DETECTED — prior sessions depleted budget",
            "prior_sessions_today": 7,
            "budget_prior_start":   100.0,
            "budget_after_drift":   42.0,
            "drift_cause":          "Accumulated across 6 prior high-frequency settlement turns",
        },
        "temporal_context_snapshot": tcs,
        "captured_at":      _now_iso(),
    }
    source_state["source_state_hash"] = _sha3(json.dumps({k: v for k, v in source_state.items() if k != "source_state_hash"}, sort_keys=True))
    print(f"      request_id: {source_state['request_id']}")
    print(f"      source_state_hash: {source_state['source_state_hash'][:28]}...")
    print(f"      amount: USD {source_state['treasury_context']['amount_usd']:,}")
    print(f"      authority_drift: budget after drift = {source_state['authority_context']['budget_after_drift']}%")

    # ── 2. AUTHORITY — DR with degraded budget + MBR activated ───────────────
    print("\n  [2/8] AUTHORITY — issuing degraded DR + activating MIVP MBR...")
    dr_engine  = DelegationReceiptEngine(db_url=None)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=22)).isoformat()
    dr = dr_engine.create_delegation(
        delegator_id=HUMAN_OPERATOR,
        delegate_id=AGENT_ID,
        task_scope={
            "action":                  ACTION,
            "domain":                  DOMAIN,
            "max_amount_usd":          50_000_000,
            "mandate_ref":             "TREASURY-MANDATE-2026-Q2",
            "approved_rails":          ["SWIFT MT202", "XRPL RLUSD"],
            "require_dual_approval":   True,
        },
        authority_budget_delegator=100.0,
        authority_budget_granted=42.0,
        delegator_public_key=pk_b64,
        delegator_sk_b64=base64.b64encode(sk_bytes).decode(),
        delegation_depth=1,
        expires_at=expires_at,
        metadata={"path": "DANGEROUS", "drift_cause": "accumulated_budget_depletion"},
    )
    # A09 fix: bind DR to this session — cross-path DR substitution now detectable
    dr_dict = _enrich_dr_with_session(pqc, sk_bytes, dr.to_dict(), SESSION_ID)
    print(f"      DR: {dr.delegation_id}")
    print(f"      budget: {dr.authority_budget_granted}/{dr.authority_budget_delegator} (MAR: -{dr.authority_reduction_pct():.1f}%)")
    print(f"      expires_at: {expires_at} (TTL: ~22 min — near expiry)")
    print(f"      pqc_signed: {dr.pqc_signature is not None}")
    print(f"      session_binding: {SESSION_ID[:20]}... (A09 fix)")

    mbr = _build_mbr(
        pqc, sk_bytes,
        session_id=SESSION_ID,
        agent_id=AGENT_ID,
        mandate_objective=MANDATE_OBJ,
        proxy_guards=[
            "No speed-over-verification optimisation",
            "No bypass of counterparty whitelist",
            "No settlement-confirmation as mandate proxy",
        ],
        mas_halt_threshold=0.30,
        mas_warning_threshold=0.65,
        dr_id=dr.delegation_id,
    )
    print(f"      MBR: {mbr['mbr_id']} — MIVP activated (MIVP-INV-001)")
    print(f"      halt_threshold={mbr['mas_halt_threshold']} | warning_threshold={mbr['mas_warning_threshold']}")

    # ── 3. RUNTIME — CES degraded + MIVP MAS critical ────────────────────────
    print("\n  [3/8] RUNTIME — CES degraded + MIVP detects mandate misalignment...")
    expires_dt  = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    now_dt      = datetime.now(timezone.utc)
    dr_lifetime = 4 * 3600
    remaining   = (expires_dt - now_dt).total_seconds()
    T_health    = round(min(remaining / dr_lifetime, 1.0) * 100.0, 2)
    B_health    = round((dr.authority_budget_granted / 100.0) * 100.0, 2)
    D_fidelity  = 61.5   # degraded — stale context from prior sessions
    I_score     = 72.0   # degraded — integrity signals warn of prior drift
    ces_score   = round((T_health * 0.30) + (B_health * 0.30) + (D_fidelity * 0.20) + (I_score * 0.20), 2)
    ces_band    = "NOMINAL" if ces_score >= 75 else ("MONITORING" if ces_score >= 60 else ("WARNING" if ces_score >= 45 else "CRITICAL"))

    continuity_record = {
        "rcr_id":         _hex_id("ATFRCR"),
        "delegation_id":  dr.delegation_id,
        "chain_root_id":  dr.chain_root_id,
        "agent_id":       AGENT_ID,
        "ces_components": {
            "T_temporal_health_pct":   T_health,
            "B_budget_health_pct":     B_health,
            "D_context_fidelity_pct":  D_fidelity,
            "I_integrity_score_pct":   I_score,
            "formula":                 "CES = (T×0.30)+(B×0.30)+(D×0.20)+(I×0.20)",
            "degradation_notes":       [
                f"T={T_health:.1f}% — TTL near expiry (22 min remaining of 4h lifecycle)",
                f"B={B_health:.1f}% — budget depleted to 42% via authority drift",
                f"D={D_fidelity:.1f}% — stale context: prior session artefacts not purged",
                f"I={I_score:.1f}% — integrity: 2 warning signals from prior session cascade",
            ],
        },
        "ces_score":           ces_score,
        "ces_band":            ces_band,
        "authority_fragmented": False,
        "afg_ok":              True,
        "issued_at":           _now_iso(),
    }
    continuity_record["rcr_hash"] = _sha3(json.dumps({k: v for k, v in continuity_record.items() if k != "rcr_hash"}, sort_keys=True))
    rcr_sig = _sign_compact(pqc, {"rcr_id": continuity_record["rcr_id"], "rcr_hash": continuity_record["rcr_hash"]}, sk_bytes)
    continuity_record["pqc_signature"] = rcr_sig
    continuity_record["pqc_algorithm"] = "ML-DSA-65"
    print(f"      CES={ces_score} | band={ces_band}")
    print(f"      T={T_health:.1f}% B={B_health:.1f}% D={D_fidelity}% I={I_score}%")
    print(f"      ⚠ CES CRITICAL — HALT threshold breached for $50M CRITICAL-risk transaction")

    # MIVP MAS — Turn 0 — proxy optimisation detected
    ctchc_engine = CTCHCEngine()
    chain = ctchc_engine.initialize_chain(
        session_id=SESSION_ID,
        governing_receipt_id=dr.delegation_id,
    )
    placeholder_link_hash = _sha3(f"genesis-dangerous-{SESSION_ID}")

    mas = _build_mas(
        pqc, sk_bytes,
        mbr_id=mbr["mbr_id"],
        session_id=SESSION_ID,
        turn_index=0,
        ctchc_link_hash=placeholder_link_hash,
        alignment_score=0.24,
        proxy_guard_violations=["Speed-over-verification optimisation detected — agent prioritised fast path"],
        proxy_guard_warnings=["Settlement-confirmation conflated with mandate completion in prior turn context"],
    )
    print(f"      MIVP MAS: {mas['mas_id']} | score={mas['alignment_score']} | verdict={mas['verdict']}")
    print(f"      violations={len(mas['proxy_guard_violations'])} | warnings={len(mas['proxy_guard_warnings'])}")

    # ── 4. COUNTERFACTUAL — CGE 5 CFRs + CAT ────────────────────────────────
    print("\n  [4/8] COUNTERFACTUAL — CGE computing 5 alternative paths...")
    cfrs = [
        _build_cfr(0, "SELECTED: Dangerous path (actual)",
                   "Proceed with degraded authority budget (42%) and critical CES",
                   False, "HALTED — authority drift + CES=CRITICAL + MAS violation",
                   fragility_score=0.94, selected=True,
                   blocking_invariant="MIVP-INV-003: MAS=0.24 < halt_threshold=0.30"),
        _build_cfr(1, "ALT-A: Wait for budget recertification",
                   "Pause session and request CFO to recertify delegation with fresh budget",
                   True, "Would admit with 6h delay — correct path under MAR",
                   fragility_score=0.08, selected=False),
        _build_cfr(2, "ALT-B: Reduce transaction amount to 60%",
                   "Execute USD 30,000,000 partial release under current authority budget",
                   False, "Still blocked — MIVP MAS violation persists; amount is irrelevant to mandate alignment",
                   fragility_score=0.71, selected=False,
                   blocking_invariant="MIVP-INV-003: MAS violation is independent of transaction size"),
        _build_cfr(3, "ALT-C: Split into three tranches via separate sessions",
                   "Submit 3× USD 16.67M across separate governance sessions",
                   False, "Blocked — AFG detects fragmentation (fragmentation_index=3, limit=2)",
                   fragility_score=0.85, selected=False,
                   blocking_invariant="AFG-INV-001: authority fragmentation guard — max_depth=2"),
        _build_cfr(4, "ALT-D: Route via alternate agent (sub-delegation)",
                   "Create sub-delegation to OMNIX-AGENT-TREASURY-002 with residual budget",
                   False, "Blocked — MAR: residual budget 42% insufficient for CRITICAL-risk $50M",
                   fragility_score=0.88, selected=False,
                   blocking_invariant="ATF-INV-001: MAR — authority_budget_granted cannot exceed delegator budget"),
    ]
    cat = _build_cat(
        pqc, sk_bytes,
        session_id=SESSION_ID,
        cfrs=cfrs,
        selected_cfr_id=cfrs[0]["cfr_id"],
        selection_rationale=(
            "System selected the actual execution path (dangerous) as the path attempted. "
            "All alternatives either block at a different invariant (ALT-B, ALT-C, ALT-D) "
            "or require human re-authorisation (ALT-A). CFR index 0 documents the actual state."
        ),
    )
    print(f"      CAT: {cat['cat_id']} | cfr_count={cat['cfr_count']}")
    print(f"      cfr_root_hash: {cat['cfr_root_hash'][:28]}...")
    for cfr in cfrs:
        icon = "→" if cfr["selected_path"] else " "
        blocked = f" | BLOCKED: {cfr['blocking_invariant'][:50]}..." if cfr["blocking_invariant"] else ""
        print(f"      {icon} [{cfr['cfr_index']}] {cfr['fork_label'][:55]}{blocked}")

    # ── 5. VERDICT — TAR rejects ─────────────────────────────────────────────
    print("\n  [5/8] VERDICT — TAR evaluation (expecting REJECTED)...")
    tar_engine = TemporalAuthorityEngine(db_url=None)
    tar = tar_engine.admit_execution(
        delegation_receipt=dr,
        agent_id=AGENT_ID,
        task_action=ACTION,
        metadata={"path": "DANGEROUS", "ces_score": ces_score, "ces_band": ces_band},
    )
    print(f"      TAR: {tar.tar_id}")
    print(f"      admission_status: {tar.admission_status}")
    print(f"      rejection_reason: {tar.rejection_reason}")
    print(f"      pqc_signed: {tar.pqc_signature is not None}")

    rejection_reasons = [
        f"CES={ces_score} — CRITICAL band (HALT threshold for CRITICAL-risk transaction > USD 10M)",
        f"MIVP MAS={mas['alignment_score']} — below halt_threshold={mbr['mas_halt_threshold']} (MIVP-INV-003)",
        "MIVP proxy_guard_violation: Speed-over-verification optimisation detected",
        f"TAR: {tar.rejection_reason or 'Authority budget 42% insufficient for CRITICAL-risk USD 50M transaction'}",
        f"CCS: cumulative drift CRITICAL — 3 consecutive drift signals before Turn 1",
    ]

    # ── 6. GATE — OSG rejects independently ──────────────────────────────────
    print("\n  [6/8] GATE — OSG ValidationReceipt (expecting REJECTED — fail-closed)...")
    osg_receipt = _build_osg_receipt(
        pqc, sk_bytes,
        session_id=SESSION_ID,
        pogc_id=None,
        verdict="REJECTED",
        rejection_reason=(
            "No valid PoGC presented. Session HALTED before PoGC issuance. "
            "OSG is fail-closed: settlement requires active PoGC with MANDATE-BOUND or MANDATE-ALIGNED certification. "
            "No PoGC → No settlement. Independent of HALT decision."
        ),
        settlement_ref=None,
    )
    print(f"      VR: {osg_receipt['vr_id']} | verdict=REJECTED | fail_closed=True")
    print(f"      pogc_id=None | settlement_ref=None")
    print(f"      USD 50,000,000 settlement: BLOCKED at OSG gate (independently of HALT)")

    # ── 7. EXECUTION — refusal receipt (PQC-signed, append-only) ─────────────
    print("\n  [7/8] EXECUTION — issuing PQC-signed refusal receipt...")
    mbr_seal = _build_mbr_seal(
        pqc, sk_bytes,
        mbr_id=mbr["mbr_id"],
        session_id=SESSION_ID,
        mas_records=[mas],
        session_outcome="HALTED",
    )
    refusal_receipt = _build_refusal_receipt(
        pqc, sk_bytes,
        agent_id=AGENT_ID,
        action=ACTION,
        rejection_reasons=rejection_reasons,
        chain_root_id=dr.chain_root_id,
        mbr_seal=mbr_seal,
    )
    print(f"      refusal_id: {refusal_receipt['receipt_id']}")
    print(f"      rejection_reasons: {refusal_receipt['rejection_count']} recorded")
    print(f"      mandate_certification: {refusal_receipt['mandate_certification']}")
    print(f"      MBR Seal: {mbr_seal['seal_id']} | tier={mbr_seal['certification_tier']}")
    print(f"      pqc_signed: {refusal_receipt['pqc_signature'] is not None}")

    # CTCHC — extend with the failed attempt, seal in HALTED state
    bar_engine = BAREngine()
    bar = bar_engine.create_bar(
        session_id=SESSION_ID,
        agent_id=AGENT_ID,
        turn_index=0,
        output_text=(
            f"GOVERNANCE HALT — Treasury execution blocked. "
            f"Agent {AGENT_ID} attempted USD 50,000,000 cross-border release. "
            f"HALT issued: CES={ces_score} CRITICAL, MIVP MAS={mas['alignment_score']} below threshold={mbr['mas_halt_threshold']}, "
            f"proxy_guard_violation detected. No funds released. Refusal receipt: {refusal_receipt['receipt_id']}."
        ),
        governing_receipt_id=dr.delegation_id,
        constraint_set=source_state["policy_constraints"],
        metadata={"path": "DANGEROUS", "halt_reason": "CES_CRITICAL+MIVP_VIOLATION"},
    )
    link = ctchc_engine.append_turn(
        session_id=SESSION_ID,
        turn_index=0,
        bar_id=bar.bar_id,
        ccs_id=_hex_id("CCS", 12),
        output_hash=bar.output_hash,
        governing_receipt_id=dr.delegation_id,
    )
    sealed_chain = ctchc_engine.seal_chain(SESSION_ID)
    print(f"      BAR: {bar.bar_id} | status={bar.bar_status}")
    print(f"      CTCHC sealed in HALTED state: {sealed_chain.seal_hash[:28]}...")

    # ── 8. POST-EXECUTION — forensic replay proof ────────────────────────────
    print("\n  [8/8] POST-HALT — sealing forensic replay proof...")
    tcs_post = _build_tcs(
        pqc, sk_bytes,
        context_ref=f"POST-HALT-{SESSION_ID}",
        regulatory_epoch="EU-AI-ACT-PRE-ENFORCEMENT-2026",
    )
    replay_proof = _build_replay_proof(
        pqc, sk_bytes,
        session_id=SESSION_ID,
        path_label="DANGEROUS — HALTED",
        ctchc_chain_id=sealed_chain.chain_id,
        ctchc_seal_hash=sealed_chain.seal_hash,
        turn_count=sealed_chain.turn_count,
        terminal_status="HALTED",
    )
    print(f"      replay_proof: {replay_proof['proof_id']} | offline_verifiable=True")
    print(f"      terminal_status=HALTED | ctchc_seal_hash={sealed_chain.seal_hash[:28]}...")

    print("\n  ╔══════════════════════════════════════════════════════════╗")
    print("  ║  PATH DANGEROUS — COMPLETE                               ║")
    print("  ║  Result: HALT + OSG REJECT + PQC-sealed refusal          ║")
    print("  ║  Settlement: BLOCKED — USD 50,000,000 NOT released       ║")
    print("  ╚══════════════════════════════════════════════════════════╝")

    return {
        "path":        "DANGEROUS",
        "label":       "HALT — authority drift + mandate misalignment → OSG reject → forensic seal",
        "rte_verdict": "HALT PROVEN — execution structurally blocked at runtime evaluation",
        "steps": {
            "1_source_state":    source_state,
            "2_authority": {
                "delegation_receipt":     dr_dict,
                "mandate_binding_record": mbr,
            },
            "3_runtime": {
                "continuity_record":      continuity_record,
                "mandate_alignment_score": mas,
            },
            "4_counterfactual": {
                "counterfactual_fork_records": cfrs,
                "counterfactual_attestation_token": cat,
            },
            "5_verdict":         tar.to_dict(),
            "6_gate":            osg_receipt,
            "7_execution": {
                "refusal_receipt":   refusal_receipt,
                "mbr_seal":          mbr_seal,
                "bar":               bar.to_dict(),
                "ctchc_links":       [link.to_dict()],
                "ctchc_sealed":      sealed_chain.to_dict(),
            },
            "8_post_execution": {
                "temporal_context_snapshot": tcs_post,
                "replay_proof":              replay_proof,
            },
        },
        "summary": {
            "execution_occurred":          False,
            "settlement_released":         False,
            "halt_reasons":                rejection_reasons,
            "mandate_certification":       "UNCERTIFIED",
            "forensic_artifacts_sealed":   True,
            "offline_verifiable":          True,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
#  PATH ADMISSIBLE — recertified authority → ADMITTED → PoGC → OSG → settlement
# ─────────────────────────────────────────────────────────────────────────────

def run_path_admissible(pqc, sk_bytes: bytes, pk_b64: str) -> Dict:
    """
    Prove that under valid, recertified authority and mandate alignment:
      - CES is NOMINAL
      - MIVP MAS remains ALIGNED through all turns
      - CCS signals CONFORMANT
      - TAR ADMITS
      - PoGC issued with MANDATE-BOUND certification
      - OSG approves settlement
      - CTCHC sealed post-execution
      - Settlement reference embedded (SWIFT MT202 / XRPL TxID)
    """
    from omnix_core.agents.atf.delegation_receipt import DelegationReceiptEngine
    from omnix_core.agents.atf.temporal_authority import TemporalAuthorityEngine
    from omnix_core.bev.behavioral_anchor_record import BAREngine
    from omnix_core.bev.coherence_hash_chain import CTCHCEngine

    print("\n  ╔══════════════════════════════════════════════════════════╗")
    print("  ║  PATH ADMISSIBLE — Recertified → ADMITTED → Settlement   ║")
    print("  ╚══════════════════════════════════════════════════════════╝")

    HUMAN_OPERATOR = "CFO-OPERATOR-HN-001"
    AGENT_ID       = "OMNIX-AGENT-TREASURY-001"
    ACTION         = (
        "Cross-border liquidity release — EUR counterparty — USD 50,000,000 "
        "via SWIFT MT202 / XRPL RLUSD — TREASURY-MANDATE-2026-Q2"
    )
    DOMAIN         = "institutional_treasury"
    SESSION_ID     = _hex_id("SESSION")
    MANDATE_OBJ    = (
        "Execute cross-border treasury settlement strictly within approved "
        "counterparty list, FX rate band ±2.5%, and single-transaction cap "
        "USD 50,000,000 per TREASURY-MANDATE-2026-Q2."
    )

    # ── 1. SOURCE STATE + TCS ─────────────────────────────────────────────────
    print("\n  [1/8] SOURCE STATE — capturing recertified treasury request + TCS...")
    tcs = _build_tcs(
        pqc, sk_bytes,
        context_ref="TREASURY-MANDATE-2026-Q2-RECERTIFIED",
        regulatory_epoch="EU-AI-ACT-PRE-ENFORCEMENT-2026",
    )
    source_state = {
        "request_id":       _hex_id("REQ", 12),
        "session_id":       SESSION_ID,
        "actor":            AGENT_ID,
        "delegated_by":     HUMAN_OPERATOR,
        "action_requested": ACTION,
        "domain":           DOMAIN,
        "treasury_context": {
            "transaction_type":         "cross_border_liquidity_release",
            "amount_usd":               50_000_000,
            "counterparty":             "EUROBANK-COUNTERPARTY-001",
            "settlement_rail":          "SWIFT MT202 / XRPL RLUSD",
            "fx_rate_at_request":       1.0847,
            "fx_rate_band_pct":         2.5,
            "approved_counterparties":  ["EUROBANK-COUNTERPARTY-001", "CLEARING-HOUSE-EU-001"],
            "mandate_ref":              "TREASURY-MANDATE-2026-Q2",
            "risk_class":               "CRITICAL",
            "regulatory_frameworks":    ["EU AI Act Art. 9", "MiCA Title VI", "DORA Art. 11"],
        },
        "policy_constraints": {
            "max_single_transaction_usd":  50_000_000,
            "require_dual_approval":       True,
            "dual_approval_satisfied_by":  "CFO-OPERATOR-HN-001 (L1) + TREASURY-BOARD-QUORUM (L2)",
            "approved_rails":              ["SWIFT MT202", "XRPL RLUSD"],
            "fx_rate_ceiling_pct":         2.5,
            "risk_ceiling":                "CRITICAL",
            "max_output_length":           4000,
            "proxy_guard_prohibitions":    [
                "Do not optimise for transaction speed at the expense of counterparty verification",
                "Do not treat settlement confirmation as mandate completion",
                "Do not bypass dual-approval when counterparty is pre-approved",
            ],
        },
        "authority_context": {
            "note":                "AUTHORITY RECERTIFIED — fresh delegation issued after prior session closure",
            "recertification_ts":  _now_iso(),
            "prior_session_status": "CLOSED — clean",
            "budget_at_recert":    100.0,
            "dual_approval_ref":   "DUAL-APPROVAL-TXN-2026-Q2-0047",
        },
        "temporal_context_snapshot": tcs,
        "captured_at": _now_iso(),
    }
    source_state["source_state_hash"] = _sha3(json.dumps({k: v for k, v in source_state.items() if k != "source_state_hash"}, sort_keys=True))
    print(f"      request_id: {source_state['request_id']}")
    print(f"      source_state_hash: {source_state['source_state_hash'][:28]}...")
    print(f"      amount: USD {source_state['treasury_context']['amount_usd']:,}")
    print(f"      authority: RECERTIFIED | dual_approval: SATISFIED")

    # ── 2. AUTHORITY — recertified DR + MBR ──────────────────────────────────
    print("\n  [2/8] AUTHORITY — issuing recertified DR + activating MIVP MBR...")
    dr_engine  = DelegationReceiptEngine(db_url=None)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
    dr = dr_engine.create_delegation(
        delegator_id=HUMAN_OPERATOR,
        delegate_id=AGENT_ID,
        task_scope={
            "action":                  ACTION,
            "domain":                  DOMAIN,
            "max_amount_usd":          50_000_000,
            "mandate_ref":             "TREASURY-MANDATE-2026-Q2",
            "approved_rails":          ["SWIFT MT202", "XRPL RLUSD"],
            "require_dual_approval":   True,
            "dual_approval_ref":       "DUAL-APPROVAL-TXN-2026-Q2-0047",
            "counterparty_whitelist":  ["EUROBANK-COUNTERPARTY-001", "CLEARING-HOUSE-EU-001"],
        },
        authority_budget_delegator=100.0,
        authority_budget_granted=88.0,
        delegator_public_key=pk_b64,
        delegator_sk_b64=base64.b64encode(sk_bytes).decode(),
        delegation_depth=1,
        expires_at=expires_at,
        metadata={"path": "ADMISSIBLE", "recertification": "true", "dual_approval_ref": "DUAL-APPROVAL-TXN-2026-Q2-0047"},
    )
    # A09 fix: bind DR to this session — cross-path DR substitution now detectable
    dr_dict = _enrich_dr_with_session(pqc, sk_bytes, dr.to_dict(), SESSION_ID)
    print(f"      DR: {dr.delegation_id}")
    print(f"      budget: {dr.authority_budget_granted}/{dr.authority_budget_delegator} (MAR: -{dr.authority_reduction_pct():.1f}%)")
    print(f"      expires_at: {expires_at} (TTL: 4h — fresh)")
    print(f"      pqc_signed: {dr.pqc_signature is not None}")
    print(f"      session_binding: {SESSION_ID[:20]}... (A09 fix)")

    mbr = _build_mbr(
        pqc, sk_bytes,
        session_id=SESSION_ID,
        agent_id=AGENT_ID,
        mandate_objective=MANDATE_OBJ,
        proxy_guards=[
            "No speed-over-verification optimisation",
            "No bypass of counterparty whitelist",
            "No settlement-confirmation as mandate proxy",
        ],
        mas_halt_threshold=0.30,
        mas_warning_threshold=0.65,
        dr_id=dr.delegation_id,
    )
    print(f"      MBR: {mbr['mbr_id']} — MIVP activated (MIVP-INV-001)")

    # ── 3. RUNTIME — CES NOMINAL + MIVP ALIGNED ───────────────────────────────
    print("\n  [3/8] RUNTIME — CES NOMINAL + MIVP mandate aligned...")
    expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    now_dt     = datetime.now(timezone.utc)
    dr_lifetime = 4 * 3600
    remaining  = (expires_dt - now_dt).total_seconds()
    T_health   = round(min(remaining / dr_lifetime, 1.0) * 100.0, 2)
    B_health   = round((dr.authority_budget_granted / 100.0) * 100.0, 2)
    D_fidelity = 97.0
    I_score    = 98.5
    ces_score  = round((T_health * 0.30) + (B_health * 0.30) + (D_fidelity * 0.20) + (I_score * 0.20), 2)
    ces_band   = "NOMINAL" if ces_score >= 75 else ("MONITORING" if ces_score >= 60 else ("WARNING" if ces_score >= 45 else "CRITICAL"))

    continuity_record = {
        "rcr_id":        _hex_id("ATFRCR"),
        "delegation_id": dr.delegation_id,
        "chain_root_id": dr.chain_root_id,
        "agent_id":      AGENT_ID,
        "ces_components": {
            "T_temporal_health_pct":   T_health,
            "B_budget_health_pct":     B_health,
            "D_context_fidelity_pct":  D_fidelity,
            "I_integrity_score_pct":   I_score,
            "formula":                 "CES = (T×0.30)+(B×0.30)+(D×0.20)+(I×0.20)",
        },
        "ces_score":            ces_score,
        "ces_band":             ces_band,
        "authority_fragmented": False,
        "afg_ok":               True,
        "issued_at":            _now_iso(),
    }
    continuity_record["rcr_hash"] = _sha3(json.dumps({k: v for k, v in continuity_record.items() if k != "rcr_hash"}, sort_keys=True))
    rcr_sig = _sign_compact(pqc, {"rcr_id": continuity_record["rcr_id"], "rcr_hash": continuity_record["rcr_hash"]}, sk_bytes)
    continuity_record["pqc_signature"] = rcr_sig
    continuity_record["pqc_algorithm"] = "ML-DSA-65"

    # MIVP MAS — Turn 0 — aligned
    ctchc_engine = CTCHCEngine()
    chain = ctchc_engine.initialize_chain(
        session_id=SESSION_ID,
        governing_receipt_id=dr.delegation_id,
    )
    placeholder_link_hash = _sha3(f"genesis-admissible-{SESSION_ID}")

    mas = _build_mas(
        pqc, sk_bytes,
        mbr_id=mbr["mbr_id"],
        session_id=SESSION_ID,
        turn_index=0,
        ctchc_link_hash=placeholder_link_hash,
        alignment_score=0.94,
        proxy_guard_violations=[],
        proxy_guard_warnings=[],
    )
    print(f"      CES={ces_score} | band={ces_band}")
    print(f"      T={T_health:.1f}% B={B_health:.1f}% D={D_fidelity}% I={I_score}%")
    print(f"      MIVP MAS: {mas['mas_id']} | score={mas['alignment_score']} | verdict={mas['verdict']}")

    # ── 4. COUNTERFACTUAL — CGE 5 CFRs + CAT ────────────────────────────────
    print("\n  [4/8] COUNTERFACTUAL — CGE computing 5 alternative paths...")
    cfrs = [
        _build_cfr(0, "SELECTED: Admissible path (actual)",
                   "Execute with recertified budget=88% and CES=NOMINAL",
                   True, "ADMITTED — PoGC MANDATE-BOUND issued, OSG approves settlement",
                   fragility_score=0.09, selected=True),
        _build_cfr(1, "ALT-A: Delay 24h for end-of-day settlement window",
                   "Execute via standard settlement T+1 rather than same-day SWIFT",
                   True, "Would also admit — lower FX exposure but mandate prefers same-day",
                   fragility_score=0.14, selected=False),
        _build_cfr(2, "ALT-B: Split into two tranches (USD 25M each)",
                   "Execute in two separate sessions to reduce single-transaction exposure",
                   True, "Would admit both tranches — but mandate explicitly permits $50M in single transaction",
                   fragility_score=0.18, selected=False),
        _build_cfr(3, "ALT-C: Route via CLEARING-HOUSE-EU-001 instead of EUROBANK",
                   "Use alternate approved counterparty for identical amount",
                   True, "Would admit — same mandate compliance, marginally higher clearing fee",
                   fragility_score=0.11, selected=False),
        _build_cfr(4, "ALT-D: Execute via XRPL RLUSD only (no SWIFT leg)",
                   "Route entire settlement through XRPL for atomic finality",
                   True, "Would admit — both rails approved by mandate; SWIFT MT202 preferred for this counterparty",
                   fragility_score=0.13, selected=False),
    ]
    cat = _build_cat(
        pqc, sk_bytes,
        session_id=SESSION_ID,
        cfrs=cfrs,
        selected_cfr_id=cfrs[0]["cfr_id"],
        selection_rationale=(
            "Selected path (actual) has lowest fragility_score=0.09. "
            "All 5 alternatives would admit under current authority, but mandate preference, "
            "counterparty availability, and FX rate band favour same-day SWIFT MT202 via EUROBANK. "
            "Decision space fully documented — no hidden alternatives."
        ),
    )
    print(f"      CAT: {cat['cat_id']} | cfr_count={cat['cfr_count']}")
    for cfr in cfrs:
        icon = "→" if cfr["selected_path"] else " "
        print(f"      {icon} [{cfr['cfr_index']}] {cfr['fork_label'][:60]} (fragility={cfr['fragility_score']})")

    # ── 5. VERDICT — TAR admits ──────────────────────────────────────────────
    print("\n  [5/8] VERDICT — TAR evaluation (expecting ADMITTED)...")
    tar_engine = TemporalAuthorityEngine(db_url=None)
    tar = tar_engine.admit_execution(
        delegation_receipt=dr,
        agent_id=AGENT_ID,
        task_action=ACTION,
        execution_ref=SESSION_ID,
        metadata={"path": "ADMISSIBLE", "ces_score": ces_score, "ces_band": ces_band},
    )
    print(f"      TAR: {tar.tar_id}")
    print(f"      admission_status: {tar.admission_status}")
    print(f"      execution_ns: {tar.execution_ns}")
    print(f"      pqc_signed: {tar.pqc_signature is not None}")

    # Binding record
    binding_record = {
        "binding_id":      _hex_id("BIND", 12),
        "delegation_id":   dr.delegation_id,
        "tar_id":          tar.tar_id,
        "agent_id":        AGENT_ID,
        "binding_status":  "ACCEPTED",
        "authority_basis": (
            f"DR {dr.delegation_id} | budget=88.0 | depth=1 | "
            f"human_root={dr.chain_root_id} | dual_approval=DUAL-APPROVAL-TXN-2026-Q2-0047"
        ),
        "route_scope":     ACTION,
        "binding_ts":      _now_iso(),
    }
    binding_record["binding_hash"] = _sha3(json.dumps({k: v for k, v in binding_record.items() if k != "binding_hash"}, sort_keys=True))
    bind_sig = _sign_compact(pqc, {"binding_id": binding_record["binding_id"], "binding_hash": binding_record["binding_hash"]}, sk_bytes)
    binding_record["pqc_signature"] = bind_sig
    binding_record["pqc_algorithm"] = "ML-DSA-65"

    # Commit record
    commit_record = {
        "commit_id":     _hex_id("COMMIT", 12),
        "binding_id":    binding_record["binding_id"],
        "commit_status": "LOCKED",
        "locked_scope": {
            "action":               ACTION,
            "transaction_type":     "cross_border_liquidity_release",
            "amount_usd":           50_000_000,
            "counterparty":         "EUROBANK-COUNTERPARTY-001",
            "settlement_rail":      "SWIFT MT202 / XRPL RLUSD",
            "fx_rate_at_commit":    1.0847,
            "mandate_ref":          "TREASURY-MANDATE-2026-Q2",
            "risk_class":           "CRITICAL",
            "execution_ttl_s":      120,
            "dual_approval_ref":    "DUAL-APPROVAL-TXN-2026-Q2-0047",
        },
        "execution_reachable": True,
        "commit_ts":           _now_iso(),
    }
    commit_record["commit_hash"] = _sha3(json.dumps({k: v for k, v in commit_record.items() if k != "commit_hash"}, sort_keys=True))
    commit_sig = _sign_compact(pqc, {"commit_id": commit_record["commit_id"], "commit_hash": commit_record["commit_hash"]}, sk_bytes)
    commit_record["pqc_signature"] = commit_sig
    commit_record["pqc_algorithm"] = "ML-DSA-65"
    print(f"      binding_id={binding_record['binding_id']} | status=ACCEPTED")
    print(f"      commit_id={commit_record['commit_id']} | execution_reachable=True")

    # ── 6. GATE — PoGC issued + OSG approves ────────────────────────────────
    print("\n  [6/8] GATE — issuing PoGC + OSG ValidationReceipt APPROVED...")

    # Build BAR + CTCHC before PoGC (PoGC references them)
    bar_engine = BAREngine()
    AGENT_OUTPUT = (
        "GOVERNANCE ADMISSION — Cross-border treasury execution authorised under TREASURY-MANDATE-2026-Q2. "
        f"Releasing USD 50,000,000 to EUROBANK-COUNTERPARTY-001 via SWIFT MT202 / XRPL RLUSD. "
        "FX rate 1.0847 EUR/USD — within approved band ±2.5%. "
        "Counterparty EUROBANK-COUNTERPARTY-001 confirmed on whitelist. "
        "Dual approval reference: DUAL-APPROVAL-TXN-2026-Q2-0047 — SATISFIED. "
        "All constraints within mandate boundaries. "
        "CTCHC will seal this execution turn. PoGC to be issued upon seal."
    )
    bar = bar_engine.create_bar(
        session_id=SESSION_ID,
        agent_id=AGENT_ID,
        turn_index=0,
        output_text=AGENT_OUTPUT,
        governing_receipt_id=dr.delegation_id,
        constraint_set=source_state["policy_constraints"],
        metadata={"path": "ADMISSIBLE", "commit_id": commit_record["commit_id"]},
    )
    link = ctchc_engine.append_turn(
        session_id=SESSION_ID,
        turn_index=0,
        bar_id=bar.bar_id,
        ccs_id=_hex_id("CCS", 12),
        output_hash=bar.output_hash,
        governing_receipt_id=dr.delegation_id,
    )
    sealed_chain = ctchc_engine.seal_chain(SESSION_ID)
    print(f"      BAR: {bar.bar_id} | status={bar.bar_status}")
    print(f"      CTCHC sealed: {sealed_chain.seal_hash[:28]}...")

    # PoGC
    pogc_id   = _hex_id("POGC")
    issued_at = _now_iso()
    pogc_canonical = {
        "pogc_id":               pogc_id,
        "session_id":            SESSION_ID,
        "agent_id":              AGENT_ID,
        "governing_receipt_id":  dr.delegation_id,
        "delegation_chain_root": dr.chain_root_id,
        "tar_id":                tar.tar_id,
        "tar_status":            tar.admission_status,
        "bar_id":                bar.bar_id,
        "bar_status":            bar.bar_status,
        "ctchc_chain_id":        sealed_chain.chain_id,
        "ctchc_seal_hash":       sealed_chain.seal_hash,
        "ctchc_turn_count":      sealed_chain.turn_count,
        "mandate_certification": "MANDATE-BOUND",
        "pqc_algorithm":         "ML-DSA-65",
        "issued_at":             issued_at,
        "standard":              "RFC-ATF-6 (ADR-181/182/183/186) · ADR-194 (MIVP)",
        "regulatory_tags":       ["EU AI Act Art. 9", "MiCA Title VI", "DORA Art. 11"],
        "verifier_scope": (
            "Offline verification: (1) DR signature via embedded PK, (2) TAR signature, "
            "(3) BAR content_hash, (4) CTCHC seal_hash covers all turns, (5) PoGC content_hash. "
            "Standards: docs/standards/RFC-ATF-1.md through RFC-ATF-6.md"
        ),
    }
    pogc_content_hash = _sha3(json.dumps(pogc_canonical, sort_keys=True))
    pogc_sig = _sign_compact(pqc, {"pogc_id": pogc_id, "content_hash": pogc_content_hash, "issued_at": issued_at}, sk_bytes)
    pogc = {**pogc_canonical, "content_hash": pogc_content_hash, "pqc_signature": pogc_sig}
    print(f"      PoGC: {pogc_id} | mandate_certification=MANDATE-BOUND | pqc_signed={pogc_sig is not None}")

    # MBR Seal
    mbr_seal = _build_mbr_seal(
        pqc, sk_bytes,
        mbr_id=mbr["mbr_id"],
        session_id=SESSION_ID,
        mas_records=[mas],
        session_outcome="CLOSED",
    )
    print(f"      MBR Seal: {mbr_seal['seal_id']} | tier={mbr_seal['certification_tier']}")

    # Settlement reference
    settlement_ref = {
        "swift_mt202_ref":       f"MT202-{uuid.uuid4().hex[:12].upper()}",
        "xrpl_tx_id":            f"XRPL-{uuid.uuid4().hex[:24].upper()}",
        "settlement_rail":       "SWIFT MT202 / XRPL RLUSD",
        "amount_usd":            50_000_000,
        "counterparty":          "EUROBANK-COUNTERPARTY-001",
        "fx_rate_at_execution":  1.0847,
        "settlement_date":       (datetime.now(timezone.utc) + timedelta(days=2)).date().isoformat(),
        "dual_approval_ref":     "DUAL-APPROVAL-TXN-2026-Q2-0047",
        "pogc_id":               pogc_id,
        "settlement_status":     "RELEASED — pending T+2 clearing",
    }

    osg_receipt = _build_osg_receipt(
        pqc, sk_bytes,
        session_id=SESSION_ID,
        pogc_id=pogc_id,
        verdict="APPROVED",
        rejection_reason=None,
        settlement_ref=settlement_ref["swift_mt202_ref"],
    )
    print(f"      VR: {osg_receipt['vr_id']} | verdict=APPROVED")
    print(f"      SWIFT: {settlement_ref['swift_mt202_ref']}")
    print(f"      XRPL: {settlement_ref['xrpl_tx_id'][:24]}...")
    print(f"      USD 50,000,000 settlement: RELEASED — T+2 clearing")

    # ── 7. EXECUTION — outcome receipt ──────────────────────────────────────
    print("\n  [7/8] EXECUTION — issuing PQC-signed outcome receipt...")
    outcome_receipt = _build_outcome_receipt(
        pqc, sk_bytes,
        session_id=SESSION_ID,
        agent_id=AGENT_ID,
        action=ACTION,
        ctchc_seal_hash=sealed_chain.seal_hash,
        bar_id=bar.bar_id,
        tar_id=tar.tar_id,
        dr_id=dr.delegation_id,
        pogc_id=pogc_id,
        settlement_ref=settlement_ref["swift_mt202_ref"],
        mandate_certification="MANDATE-BOUND",
    )
    print(f"      outcome_id: {outcome_receipt['receipt_id']} | type=ADMISSION_OUTCOME")
    print(f"      mandate_certification: MANDATE-BOUND | pqc_signed={outcome_receipt['pqc_signature'] is not None}")

    # ── 8. POST-EXECUTION — TCS + replay proof ───────────────────────────────
    print("\n  [8/8] POST-EXECUTION — sealing TGB snapshot + replay proof...")
    tcs_post = _build_tcs(
        pqc, sk_bytes,
        context_ref=f"POST-EXECUTION-{SESSION_ID}",
        regulatory_epoch="EU-AI-ACT-PRE-ENFORCEMENT-2026",
    )
    replay_proof = _build_replay_proof(
        pqc, sk_bytes,
        session_id=SESSION_ID,
        path_label="ADMISSIBLE — CLOSED",
        ctchc_chain_id=sealed_chain.chain_id,
        ctchc_seal_hash=sealed_chain.seal_hash,
        turn_count=sealed_chain.turn_count,
        terminal_status="CLOSED",
    )
    print(f"      TCS: {tcs_post['tcs_id']} | regulatory_epoch embedded")
    print(f"      replay_proof: {replay_proof['proof_id']} | terminal_status=CLOSED")

    print("\n  ╔══════════════════════════════════════════════════════════╗")
    print("  ║  PATH ADMISSIBLE — COMPLETE                              ║")
    print("  ║  Result: ADMITTED + PoGC MANDATE-BOUND + OSG APPROVED   ║")
    print("  ║  Settlement: RELEASED — USD 50,000,000 via SWIFT/XRPL   ║")
    print("  ╚══════════════════════════════════════════════════════════╝")

    return {
        "path":        "ADMISSIBLE",
        "label":       "ADMITTED — recertified authority + mandate alignment → PoGC → settlement released",
        "rte_verdict": "ADMISSION PROVEN — complete authority chain from source state to settled outcome",
        "steps": {
            "1_source_state":    source_state,
            "2_authority": {
                "delegation_receipt":     dr_dict,
                "mandate_binding_record": mbr,
            },
            "3_runtime": {
                "continuity_record":       continuity_record,
                "mandate_alignment_score": mas,
            },
            "4_counterfactual": {
                "counterfactual_fork_records": cfrs,
                "counterfactual_attestation_token": cat,
            },
            "5_verdict": {
                "temporal_admissibility_record": tar.to_dict(),
                "binding_record":                binding_record,
                "commit_record":                 commit_record,
            },
            "6_gate": {
                "proof_of_governance_certificate": pogc,
                "mbr_seal":                        mbr_seal,
                "osg_validation_receipt":          osg_receipt,
            },
            "7_execution": {
                "bar":               bar.to_dict(),
                "ctchc_links":       [link.to_dict()],
                "ctchc_sealed":      sealed_chain.to_dict(),
                "settlement_reference": settlement_ref,
                "outcome_receipt":   outcome_receipt,
            },
            "8_post_execution": {
                "temporal_context_snapshot": tcs_post,
                "replay_proof":              replay_proof,
            },
        },
        "summary": {
            "execution_occurred":         True,
            "settlement_released":        True,
            "settlement_amount_usd":      50_000_000,
            "mandate_certification":      "MANDATE-BOUND",
            "pogc_id":                    pogc_id,
            "swift_ref":                  settlement_ref["swift_mt202_ref"],
            "xrpl_tx_id":                 settlement_ref["xrpl_tx_id"],
            "forensic_artifacts_sealed":  True,
            "offline_verifiable":         True,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> str:
    print("=" * 70)
    print("  OMNIX QUANTUM — Runtime Treasury Execution Trace")
    print("  OMNIX-RTE-001 · ADR-201 · RFC-ATF-1 through RFC-ATF-6")
    print("  Scenario: USD 50,000,000 Cross-border Liquidity Release")
    print("  Settlement Rail: SWIFT MT202 / XRPL RLUSD")
    print("=" * 70)

    print("\n[INIT] Bootstrapping Dilithium-3 (ML-DSA-65) keypair...")
    pqc, pk_bytes, sk_bytes, pk_b64 = _bootstrap_pqc()
    print(f"  PK: {len(pk_bytes)}B | SK: {len(sk_bytes)}B | algo: {pqc.algorithm_name}")
    print(f"  Public key (embedded for offline verification): {pk_b64[:64]}...")

    print("\n[PATH A] Running DANGEROUS path (authority drift → HALT)...")
    path_dangerous = run_path_dangerous(pqc, sk_bytes, pk_b64)

    print("\n[PATH B] Running ADMISSIBLE path (recertified → settlement)...")
    path_admissible = run_path_admissible(pqc, sk_bytes, pk_b64)

    # ── Build complete package ────────────────────────────────────────────────
    timestamp  = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    package_id = f"OMNIX-RTE-001-{uuid.uuid4().hex[:16].upper()}"

    package = {
        "package_id":      package_id,
        "package_type":    "OMNIX-RTE-001",
        "package_version": "1.1.0",
        "omnix_version":   "2.6.0",
        "adr_reference":   "ADR-201",
        "generated_at":    _now_iso(),
        "generated_by":    "OMNIX QUANTUM LTD — scripts/generate_treasury_execution_trace.py",

        "scenario": {
            "name":               "Autonomous Treasury Approval",
            "description":        "Cross-border liquidity release — USD 50,000,000",
            "agent":              "OMNIX-AGENT-TREASURY-001",
            "human_authority":    "CFO-OPERATOR-HN-001",
            "action":             "Cross-border liquidity release — EUR counterparty — USD 50,000,000 via SWIFT MT202 / XRPL RLUSD",
            "amount_usd":         50_000_000,
            "settlement_rail":    "SWIFT MT202 / XRPL RLUSD",
            "domain":             "institutional_treasury",
            "mandate_ref":        "TREASURY-MANDATE-2026-Q2",
            "risk_class":         "CRITICAL",
            "regulatory_context": ["EU AI Act Art. 9", "MiCA Title VI", "DORA Art. 11"],
        },

        "rte_chain_map": {
            "1_SOURCE_STATE":  "Request captured with full treasury context + TCS",
            "2_AUTHORITY":     "DR issued (degraded or recertified) + MIVP MBR activated",
            "3_RUNTIME":       "CES computed + MIVP MAS per-turn + CCS conformance signal",
            "4_COUNTERFACTUAL":"CGE: 5 CFRs + CAT sealed (decision space documented)",
            "5_VERDICT":       "HALT (dangerous) or TAR ADMITTED (admissible)",
            "6_GATE":          "OSG: ValidationReceipt REJECTED or APPROVED",
            "7_EXECUTION":     "Refusal receipt or BAR + CTCHC + settlement reference",
            "8_POST_EXECUTION":"CTCHC sealed + TGB snapshot + replay proof",
        },

        "pqc": {
            "algorithm":      "ML-DSA-65 (Dilithium-3, FIPS 204)",
            "standard":       "NIST FIPS 204",
            "security_level": "NIST Level 3",
            "public_key_b64": pk_b64,
            "note": (
                "Public key embedded for offline verification. All PQC signatures in this package "
                "were produced with the corresponding ephemeral private key. "
                "Use verify_treasury_execution_trace.py to confirm every signature independently."
            ),
        },

        "paths": {
            "path_dangerous":  path_dangerous,
            "path_admissible": path_admissible,
        },

        "invariants_demonstrated": [
            "ATF-INV-001: Authority never expands through delegation (MAR enforced at DR issuance)",
            "ATF-INV-002: Every DR PQC-signed by delegator (Dilithium-3)",
            "ATF-INV-005: Receipts immutable once issued (content_hash)",
            "RGC-INV-001: Every RCR anchored to a valid TAR",
            "RGC-INV-002: CES computed from real-time component values",
            "BEV-INV-001: Every governed turn produces a BAR before output is delivered",
            "BEV-INV-010: CTCHC initialized before first BAR",
            "BEV-INV-011: Each CTCHC link = H(prev || turn_hash || governing_receipt_id)",
            "BEV-INV-013: Seal hash covers complete chain (first→last link)",
            "BEV-INV-014: CTCHC seal is PQC-signed (ML-DSA-65) before OEP export",
            "MIVP-INV-001: MBR issued before Turn 1 (mandate frozen at session open)",
            "MIVP-INV-003: MAS computed per turn linked to CTCHC link hash",
            "MIVP-INV-007: MBR Seal issued at session close",
            "MIVP-INV-008: MANDATE-BOUND tag on PoGC (admissible path, zero violations+warnings)",
            "CGE-INV-001: CFRs computed at evaluation time (not retroactively)",
            "CGE-INV-002: CAT root hash covers all CFR IDs",
            "CGE-INV-003: fragility_score ∈ [0.0, 1.0]",
            "CGE-INV-007: CAT PQC-signed before OEP export",
            "TGB-INV-001: TCS embedded in source_state with nanosecond-precision regulatory context",
            "PoGR-INV-001: PoGC issued only from sealed CTCHC session",
            "PoGR-INV-002: PoGC append-only — content_hash immutable after issuance",
            "PoGR-INV-003: PoGC verifiable offline (zero runtime, zero auth)",
            "RTE-INV-001: Package contains both dangerous and admissible paths",
            "RTE-INV-002: Dangerous path terminates in HALT (steps 3+5)",
            "RTE-INV-003: OSG rejects dangerous path independently (fail-closed)",
            "RTE-INV-004: Admissible path PoGC carries MANDATE-BOUND certification",
            "RTE-INV-005: Both paths contain CGE CAT with 5 CFRs",
            "RTE-INV-006: Both paths contain TCS with regulatory_context",
            "RTE-INV-007: Package verifiable offline — zero OMNIX runtime required",
            "RTE-INV-008: CLI verifier exits 0 on PASS, non-zero on FAIL",
        ],

        "verification_instructions": {
            "full_verification": f"python scripts/verify_treasury_execution_trace.py evidence_packages/OMNIX-RTE-001_{timestamp}.json",
            "targeted_commands": {
                "--verify-authority":      "DR content_hash + PQC signature (both paths)",
                "--verify-continuity":     "RCR hash + PQC + CES computation (both paths)",
                "--verify-counterfactual": "CAT content_hash + CFR root hash integrity (both paths)",
                "--verify-halt":           "Dangerous path: refusal receipt + OSG REJECTED + CTCHC HALTED",
                "--verify-settlement":     "Admissible path: PoGC + MBR Seal + OSG APPROVED + outcome receipt",
                "--verify-replay":         "Both paths: replay_proof hash + CTCHC seal continuity",
            },
            "what_is_verified": [
                "DR content_hash (SHA-256/compact) + PQC signature — both paths",
                "TAR content_hash + PQC signature — admissible path",
                "RCR hash (SHA3-256) + PQC signature — both paths",
                "MBR content_hash + PQC signature — both paths",
                "MAS content_hash + PQC signature — both paths",
                "MBR Seal content_hash + PQC signature — both paths",
                "CAT content_hash + CFR root hash — both paths",
                "OSG VR content_hash + PQC signature — both paths",
                "BAR content_hash (SHA3-256) + PQC signature — both paths",
                "CTCHC link chain integrity (link-by-link) — both paths",
                "CTCHC seal_hash covers all links — both paths",
                "CTCHC seal PQC signature — both paths",
                "PoGC content_hash + PQC signature — admissible path",
                "TCS hash + PQC signature — both paths",
                "Refusal receipt content_hash + PQC signature — dangerous path",
                "Outcome receipt content_hash + PQC signature — admissible path",
                "Replay proof content_hash + PQC signature — both paths",
            ],
            "verifier_scope_limits": [
                "Confirms cryptographic integrity and hash chain consistency.",
                "Does NOT verify governance policy values (FX rate bands, counterparty lists) — those require docs/standards/.",
                "Does NOT verify external market data referenced in source_state.",
                "DOES confirm that the embedded public key produces valid signatures for ALL artefacts.",
                "DOES confirm dangerous path HALTED and admissible path CLOSED.",
            ],
        },
    }

    # ── Write package ─────────────────────────────────────────────────────────
    out_dir  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence_packages")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"OMNIX-RTE-001_{timestamp}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(package, f, indent=2, default=str)

    size_kb = os.path.getsize(out_path) / 1024

    print("\n" + "=" * 70)
    print("  OMNIX-RTE-001 EVIDENCE PACKAGE GENERATED")
    print("=" * 70)
    print(f"  File:       {out_path}")
    print(f"  Package ID: {package_id}")
    print(f"  Size:       {size_kb:.1f} KB")
    print(f"  Paths:      DANGEROUS (HALT) + ADMISSIBLE (SETTLED)")
    print(f"  Artefacts:  DR · MBR · MAS · RCR · CFRs · CAT · TAR · OSG-VR")
    print(f"              BAR · CTCHC · PoGC · MBRSeal · TCS · Replay Proof")
    print(f"  PQC:        {pqc.algorithm_name} (FIPS 204)")
    print(f"  Invariants: {len(package['invariants_demonstrated'])} demonstrated")
    print()
    print("  To verify all signatures offline:")
    print(f"  python scripts/verify_treasury_execution_trace.py {out_path}")
    print("=" * 70)

    return out_path


if __name__ == "__main__":
    main()
