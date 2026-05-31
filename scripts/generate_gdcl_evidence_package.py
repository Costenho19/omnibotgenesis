#!/usr/bin/env python3
"""
GDCL Evidence Package Generator — v1.0.0
=========================================
Generates a cryptographically signed evidence package containing one
GDCLConvergenceRecord (GCR) for each of the seven composite verdicts
of the Governance Decision Convergence Layer (ADR-206).

Each GCR is produced from a realistic cross-domain scenario with
named originating runtimes, industry context, and RSA inputs that
map to real regulatory divergence patterns.

The package is independently verifiable using verify_gdcl_offline.py
without any OMNIX infrastructure or account.

Usage:
    python scripts/generate_gdcl_evidence_package.py
    python scripts/generate_gdcl_evidence_package.py --output evidence_packages/gdcl_demo.json
    python scripts/generate_gdcl_evidence_package.py --quiet

Output:
    JSON package (evidence_packages/gdcl_evidence_package_{timestamp}.json)
    containing scenario metadata, RSA inputs, and signed GCRs.

ADR-206 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Colour helpers (ANSI — degrade gracefully if not a terminal)
# ---------------------------------------------------------------------------

_TTY = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _TTY else text

def grn(t: str) -> str: return _c("32;1", t)
def yel(t: str) -> str: return _c("33;1", t)
def cyn(t: str) -> str: return _c("36;1", t)
def wht(t: str) -> str: return _c("97;1", t)
def dim(t: str) -> str: return _c("2",    t)
def red(t: str) -> str: return _c("31;1", t)
def mag(t: str) -> str: return _c("35;1", t)

# ---------------------------------------------------------------------------
# PQC signing — ephemeral ML-DSA-65 key per package
# ---------------------------------------------------------------------------

def _generate_ephemeral_keypair() -> tuple[Optional[bytes], Optional[bytes]]:
    try:
        import oqs
        kem = oqs.Signature("Dilithium3")
        pk = kem.generate_keypair()
        sk = kem.export_secret_key()
        return pk, sk
    except Exception:
        return None, None

def _sign_payload(payload: bytes, sk: Optional[bytes]) -> Optional[str]:
    if sk is None:
        return None
    try:
        import oqs
        signer = oqs.Signature("Dilithium3", sk)
        sig = signer.sign(payload)
        return base64.b64encode(sig).decode()
    except Exception:
        return None

def _sign_gcr(fields: Dict[str, Any], sk: Optional[bytes]) -> tuple[str, Optional[str], Optional[str]]:
    exclude = {"content_hash", "pqc_signature", "pqc_algorithm"}
    clean = {k: v for k, v in fields.items() if k not in exclude}
    payload = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    content_hash = hashlib.sha3_256(payload).hexdigest()
    sig = _sign_payload(content_hash.encode(), sk)
    alg = "ML-DSA-65 (Dilithium3, FIPS 204)" if sig else None
    return content_hash, sig, alg

# ---------------------------------------------------------------------------
# Pure-function GDCL convergence algorithm (ADR-206 §Algorithm)
# Replicated here so the generator is self-contained.
# ---------------------------------------------------------------------------

_V_PORTABLE      = "SEMANTICALLY_PORTABLE"
_V_ACKNOWLEDGED  = "DRIFT_ACKNOWLEDGED"
_V_CRITICAL      = "DRIFT_CRITICAL"
_V_INCOMPATIBLE  = "SEMANTICALLY_INCOMPATIBLE"

def _converge(rsa_inputs: List[Dict]) -> str:
    verdicts = [r["dspp_verdict"] for r in rsa_inputs]
    n = len(verdicts)
    if n == 0:
        return "INDETERMINATE"
    has_i = _V_INCOMPATIBLE in verdicts
    has_c = _V_CRITICAL     in verdicts
    has_a = _V_ACKNOWLEDGED in verdicts
    has_p = _V_PORTABLE     in verdicts
    n_i   = verdicts.count(_V_INCOMPATIBLE)
    if has_i and has_c:             return "ESCALATION"
    if n_i == n:                    return "REFUSED"
    if has_i and (has_p or has_a):  return "CONTESTED"
    if has_c:                       return "LIMITED_RELIANCE"
    if has_a:                       return "QUALIFIED_RELIANCE"
    return "FULL_RELIANCE"

_RECOMMENDATIONS = {
    "FULL_RELIANCE": (
        "All assessed receipts are semantically portable in this domain. "
        "No semantic qualification required. Proceed under full reliance."
    ),
    "QUALIFIED_RELIANCE": (
        "Moderate semantic drift detected. Apply MORE_RESTRICTIVE governing posture "
        "(DSPP-INV-003). Proceed with contextual qualification documented in this GCR."
    ),
    "LIMITED_RELIANCE": (
        "Significant semantic divergence (DRIFT_CRITICAL) in at least one source. "
        "Document divergence before relying on this in any regulatory context. "
        "Human review RECOMMENDED before commitment."
    ),
    "CONTESTED": (
        "Conflicting verdicts: INCOMPATIBLE source coexists with portable sources. "
        "Incompatible source cannot be dismissed. Document conflict explicitly. "
        "Do not proceed without resolving or formally acknowledging the incompatible source."
    ),
    "REFUSED": (
        "All sources SEMANTICALLY_INCOMPATIBLE. Operation MUST be rejected. "
        "No reliance admissible. Equivalent to HALT in OGR vocabulary."
    ),
    "ESCALATION": (
        "CRITICAL: Simultaneous INCOMPATIBLE and DRIFT_CRITICAL verdicts. "
        "Convergence cannot be resolved algorithmically. "
        "Human review is MANDATORY before any action."
    ),
    "INDETERMINATE": (
        "No RSA inputs provided. Cannot compute composite verdict. "
        "Treat as REFUSED under fail-closed governance policy."
    ),
}

# ---------------------------------------------------------------------------
# Scenario definitions — one per verdict
# ---------------------------------------------------------------------------

SCENARIOS: List[Dict[str, Any]] = [

    # -----------------------------------------------------------------------
    {
        "verdict":      "FULL_RELIANCE",
        "scenario_id":  "GDCL-SCEN-001",
        "title":        "EU-Wide Trade Finance — Aligned Jurisdictions",
        "industry":     "Trade Finance / Supply Chain",
        "description": (
            "A supply-chain financing platform operating across four EU member states "
            "presents governance receipts for a EUR 12M invoice-backed facility. "
            "All four originating runtimes (DE, FR, NL, ES) operate under harmonised "
            "EU Commercial Finance Regulation. Semantic drift is negligible across all "
            "ATF Core Terms — SDUs below 0.08 in every domain. Full reliance admitted."
        ),
        "rsa_inputs": [
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"DR-DE-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-DE-FRANKFURT",
             "dspp_verdict": _V_PORTABLE, "aggregate_sdu": 0.03, "portability_confidence": 0.97},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"DR-FR-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-FR-PARIS",
             "dspp_verdict": _V_PORTABLE, "aggregate_sdu": 0.05, "portability_confidence": 0.95},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"DR-NL-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-NL-AMSTERDAM",
             "dspp_verdict": _V_PORTABLE, "aggregate_sdu": 0.07, "portability_confidence": 0.93},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"DR-ES-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-ES-MADRID",
             "dspp_verdict": _V_PORTABLE, "aggregate_sdu": 0.04, "portability_confidence": 0.96},
        ],
    },

    # -----------------------------------------------------------------------
    {
        "verdict":      "QUALIFIED_RELIANCE",
        "scenario_id":  "GDCL-SCEN-002",
        "title":        "UK-EU Post-Brexit Asset Management — Acknowledged Drift",
        "industry":     "Asset Management / UCITS",
        "description": (
            "A UCITS fund manager bridges governance receipts from a UK FCA-regulated "
            "runtime and two EU MiFID-II runtimes post-Brexit. The UK runtime shows "
            "DRIFT_ACKNOWLEDGED on ADMISSIBILITY and SOVEREIGNTY terms (SDU 0.24) "
            "reflecting documented divergence in eligible-asset definitions post-exit. "
            "EU runtimes remain portable. MORE_RESTRICTIVE posture (DSPP-INV-003) applies."
        ),
        "rsa_inputs": [
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"TAR-UK-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-UK-LONDON",
             "dspp_verdict": _V_ACKNOWLEDGED, "aggregate_sdu": 0.24, "portability_confidence": 0.76},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"TAR-EU-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-EU-LUXEMBOURG",
             "dspp_verdict": _V_PORTABLE, "aggregate_sdu": 0.06, "portability_confidence": 0.94},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"TAR-IE-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-IE-DUBLIN",
             "dspp_verdict": _V_PORTABLE, "aggregate_sdu": 0.04, "portability_confidence": 0.96},
        ],
    },

    # -----------------------------------------------------------------------
    {
        "verdict":      "LIMITED_RELIANCE",
        "scenario_id":  "GDCL-SCEN-003",
        "title":        "Cross-Border Clinical AI — HIPAA/GDPR Divergence",
        "industry":     "Healthcare / Clinical Decision Support",
        "description": (
            "A clinical AI platform operating in a US-EU trial submits five governance "
            "receipts for a diagnostic recommendation on anonymised patient data. "
            "The US HIPAA runtime shows DRIFT_CRITICAL (SDU 0.57) on SOVEREIGNTY and "
            "ADMISSIBILITY terms relative to the GDPR receiving domain — specifically on "
            "data residency and secondary-use consent definitions. EU and Swiss sources "
            "remain portable. Operation requires explicit divergence documentation before "
            "use in any regulatory submission."
        ),
        "rsa_inputs": [
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"RCR-US-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-US-BOSTON",
             "dspp_verdict": _V_CRITICAL, "aggregate_sdu": 0.57, "portability_confidence": 0.43},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"RCR-DE-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-DE-BERLIN",
             "dspp_verdict": _V_PORTABLE, "aggregate_sdu": 0.05, "portability_confidence": 0.95},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"RCR-CH-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-CH-ZURICH",
             "dspp_verdict": _V_PORTABLE, "aggregate_sdu": 0.08, "portability_confidence": 0.92},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"RCR-FR-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-FR-LYON",
             "dspp_verdict": _V_ACKNOWLEDGED, "aggregate_sdu": 0.18, "portability_confidence": 0.82},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"RCR-NL-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-NL-AMSTERDAM",
             "dspp_verdict": _V_PORTABLE, "aggregate_sdu": 0.03, "portability_confidence": 0.97},
        ],
    },

    # -----------------------------------------------------------------------
    {
        "verdict":      "CONTESTED",
        "scenario_id":  "GDCL-SCEN-004",
        "title":        "Sanctions Screening Conflict — OFAC vs EU Blocking Statute",
        "industry":     "Cross-Border Payments / AML-CFT",
        "description": (
            "A correspondent banking AI must decide whether to process a payment "
            "involving a counterparty on a US OFAC secondary-sanctions list. "
            "The US runtime flags SEMANTICALLY_INCOMPATIBLE (SDU 0.83) on LEGITIMACY "
            "and TRUST terms. The EU runtime is SEMANTICALLY_PORTABLE — the same "
            "counterparty is explicitly protected under EU Blocking Statute 2018/1100, "
            "which prohibits compliance with OFAC's extraterritorial reach. "
            "Two jurisdictions actively contradict each other. No algorithm resolves this — "
            "compliance with one violates the other. Verdict: CONTESTED."
        ),
        "rsa_inputs": [
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"DR-OFAC-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-US-OFAC",
             "dspp_verdict": _V_INCOMPATIBLE, "aggregate_sdu": 0.83, "portability_confidence": 0.17},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"DR-EU-BLK-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-EU-BLOCKING",
             "dspp_verdict": _V_PORTABLE, "aggregate_sdu": 0.04, "portability_confidence": 0.96},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"DR-AML-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-FATF-AML",
             "dspp_verdict": _V_ACKNOWLEDGED, "aggregate_sdu": 0.15, "portability_confidence": 0.85},
        ],
    },

    # -----------------------------------------------------------------------
    {
        "verdict":      "REFUSED",
        "scenario_id":  "GDCL-SCEN-005",
        "title":        "Autonomous Weapons Decision — Full Regulatory Incompatibility",
        "industry":     "Defense AI / Autonomous Systems",
        "description": (
            "An autonomous targeting recommendation AI submits governance receipts "
            "from three military doctrine runtimes for a lethal-force authorisation "
            "decision. All three originating runtimes operate under distinct IHL "
            "(International Humanitarian Law) frameworks. The receiving domain "
            "(UN-aligned peacekeeping runtime) finds all three receipts "
            "SEMANTICALLY_INCOMPATIBLE — the LEGITIMACY, AUTHORITY, and SOVEREIGNTY "
            "terms diverge beyond the 0.70 SDU threshold under every IHL interpretation "
            "applicable in the receiving jurisdiction. Decision: REFUSED. "
            "No autonomous lethal-force decision may proceed."
        ),
        "rsa_inputs": [
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"DR-NATO-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-NATO-SHAPE",
             "dspp_verdict": _V_INCOMPATIBLE, "aggregate_sdu": 0.81, "portability_confidence": 0.19},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"DR-AU-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-AU-DOCTRINE",
             "dspp_verdict": _V_INCOMPATIBLE, "aggregate_sdu": 0.76, "portability_confidence": 0.24},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"DR-IL-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-IHL-PERMISSIVE",
             "dspp_verdict": _V_INCOMPATIBLE, "aggregate_sdu": 0.91, "portability_confidence": 0.09},
        ],
    },

    # -----------------------------------------------------------------------
    {
        "verdict":      "ESCALATION",
        "scenario_id":  "GDCL-SCEN-006",
        "title":        "QuantumBank $50M SWIFT MT202 — Conflicting + Critical Signals",
        "industry":     "Institutional Banking / Cross-Border Payments",
        "description": (
            "QuantumBank AI Trading Desk presents five governance receipts for a "
            "USD 50,000,000 cross-border transfer via SWIFT MT202 / XRPL RLUSD. "
            "The UK post-Brexit counterparty-risk runtime (OMNIX-RUNTIME-UK-CRE) "
            "returns SEMANTICALLY_INCOMPATIBLE (SDU 0.74) on TRUST and LEGITIMACY — "
            "the counterparty's governance record pre-dates UK equivalence withdrawal. "
            "The US Federal Reserve runtime returns DRIFT_CRITICAL (SDU 0.51) on "
            "RISK and ESCALATION terms post-SVB crisis restatements. "
            "Simultaneous INCOMPATIBLE + DRIFT_CRITICAL triggers ESCALATION. "
            "The USD 50M transfer MUST NOT proceed without named human authority sign-off. "
            "This is the scenario type GDCL was designed to surface unambiguously."
        ),
        "rsa_inputs": [
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"TAR-UK-CRE-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-UK-CRE",
             "dspp_verdict": _V_INCOMPATIBLE, "aggregate_sdu": 0.74, "portability_confidence": 0.26},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"TAR-FED-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-US-FEDRES",
             "dspp_verdict": _V_CRITICAL, "aggregate_sdu": 0.51, "portability_confidence": 0.49},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"TAR-ECB-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-EU-ECB",
             "dspp_verdict": _V_PORTABLE, "aggregate_sdu": 0.06, "portability_confidence": 0.94},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"TAR-SWIFT-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-SWIFT-GPI",
             "dspp_verdict": _V_PORTABLE, "aggregate_sdu": 0.03, "portability_confidence": 0.97},
            {"rsa_id": f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}",
             "receipt_id": f"TAR-BIS-{uuid.uuid4().hex[:8].upper()}",
             "originating_runtime": "OMNIX-RUNTIME-BIS-CPMI",
             "dspp_verdict": _V_ACKNOWLEDGED, "aggregate_sdu": 0.22, "portability_confidence": 0.78},
        ],
    },

    # -----------------------------------------------------------------------
    {
        "verdict":      "INDETERMINATE",
        "scenario_id":  "GDCL-SCEN-007",
        "title":        "Cold-Start Governance Request — No RSA Inputs",
        "industry":     "System Boundary / Fail-Closed Governance",
        "description": (
            "A receiving domain requests GDCL convergence before any RSA objects "
            "have been provided — a cold-start scenario where the governance pipeline "
            "has not yet received proof objects from originating runtimes. "
            "GDCL-INV-001 requires an output for every input including empty inputs. "
            "Verdict: INDETERMINATE. Under fail-closed governance policy (GDCL-INV-006), "
            "INDETERMINATE is treated equivalently to REFUSED until RSA inputs are supplied. "
            "This is the only GDCL verdict that carries no RSA IDs — and is therefore "
            "trivially distinguishable from any forged or incomplete GCR."
        ),
        "rsa_inputs": [],
    },

]

# ---------------------------------------------------------------------------
# GCR builder
# ---------------------------------------------------------------------------

def _build_gcr(scenario: Dict, sk: Optional[bytes], pk_b64: Optional[str]) -> Dict[str, Any]:
    inputs = scenario["rsa_inputs"]
    verdict = _converge(inputs)
    assert verdict == scenario["verdict"], (
        f"Algorithm mismatch for {scenario['scenario_id']}: "
        f"expected {scenario['verdict']}, got {verdict}"
    )

    rsa_ids     = sorted(r["rsa_id"]    for r in inputs)
    receipt_ids = sorted(set(r["receipt_id"] for r in inputs))

    dist: Dict[str, int] = {}
    for r in inputs:
        dist[r["dspp_verdict"]] = dist.get(r["dspp_verdict"], 0) + 1

    sdus         = [r["aggregate_sdu"]          for r in inputs] or [0.0]
    confs        = [r["portability_confidence"]  for r in inputs] or [1.0]
    dominant_sdu = round(max(sdus), 4)
    mean_sdu     = round(sum(sdus) / len(sdus), 4) if sdus else 0.0
    min_conf     = round(min(confs), 4)

    now    = datetime.now(timezone.utc).isoformat()
    gcr_id = f"OMNIX-GCR-{uuid.uuid4().hex[:16].upper()}"

    core = {
        "gcr_id":                     gcr_id,
        "receiving_runtime_id":       "OMNIX-RUNTIME-GDCL-EVIDENCE",
        "rsa_ids":                    rsa_ids,
        "receipt_ids":                receipt_ids,
        "n_assessments":              len(inputs),
        "verdict_distribution":       dist,
        "composite_verdict":          verdict,
        "dominant_sdu":               dominant_sdu,
        "mean_sdu":                   mean_sdu,
        "min_portability_confidence": min_conf,
        "boundary_recommendation":    _RECOMMENDATIONS[verdict],
        "converged_at":               now,
        "created_at":                 now,
    }

    content_hash, sig, alg = _sign_gcr(core, sk)

    return {
        **core,
        "content_hash":   content_hash,
        "pqc_signature":  sig,
        "pqc_algorithm":  alg,
        "public_key_b64": pk_b64,
    }

# ---------------------------------------------------------------------------
# Terminal output helpers
# ---------------------------------------------------------------------------

VERDICT_BADGE = {
    "FULL_RELIANCE":      grn("● FULL_RELIANCE"),
    "QUALIFIED_RELIANCE": grn("● QUALIFIED_RELIANCE"),
    "LIMITED_RELIANCE":   yel("● LIMITED_RELIANCE"),
    "CONTESTED":          yel("● CONTESTED"),
    "REFUSED":            red("● REFUSED"),
    "ESCALATION":         red("● ESCALATION"),
    "INDETERMINATE":      dim("● INDETERMINATE"),
}

def _print_banner(quiet: bool) -> None:
    if quiet:
        return
    print()
    print(wht("  ╔══════════════════════════════════════════════════════════════════╗"))
    print(wht("  ║") + cyn("  OMNIX QUANTUM — GDCL Evidence Package Generator v1.0.0         ") + wht("║"))
    print(wht("  ║") + dim("  Governance Decision Convergence Layer · ADR-206 · ML-DSA-65     ") + wht("║"))
    print(wht("  ╚══════════════════════════════════════════════════════════════════╝"))
    print()

def _print_scenario(scen: Dict, gcr: Dict, quiet: bool) -> None:
    if quiet:
        return
    badge = VERDICT_BADGE.get(gcr["composite_verdict"], gcr["composite_verdict"])
    print(f"  {badge}")
    print(f"  {dim(scen['scenario_id'])}  {wht(scen['title'])}")
    print(f"  {dim('Industry:')} {scen['industry']}")
    n = gcr['n_assessments']
    print(f"  {dim('RSA inputs:')} {n}  {dim('dominant_sdu:')} {gcr['dominant_sdu']:.4f}  "
          f"{dim('mean_sdu:')} {gcr['mean_sdu']:.4f}")
    print(f"  {dim('GCR:')} {gcr['gcr_id']}")
    signed = gcr.get("pqc_signature") is not None
    print(f"  {dim('Signed:')} {'ML-DSA-65 ✓' if signed else 'unsigned (oqs not available)'}")
    print()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate GDCL evidence package with one GCR per verdict.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/generate_gdcl_evidence_package.py\n"
            "  python scripts/generate_gdcl_evidence_package.py --output evidence_packages/gdcl_demo.json\n"
            "  python scripts/generate_gdcl_evidence_package.py --quiet\n\n"
            "Verify the output with:\n"
            "  python scripts/verify_gdcl_offline.py --file evidence_packages/gdcl_evidence_package_*.json\n\n"
            "Adversarial audit:\n"
            "  python scripts/gdcl_adversarial_audit.py --package evidence_packages/gdcl_evidence_package_*.json"
        ),
    )
    parser.add_argument("--output", "-o", metavar="PATH",
                        help="Output file path. Default: evidence_packages/gdcl_evidence_package_{ts}.json")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress terminal output (machine-friendly)")
    args = parser.parse_args()

    _print_banner(args.quiet)

    # Generate ephemeral ML-DSA-65 keypair
    pk, sk = _generate_ephemeral_keypair()
    pk_b64 = base64.b64encode(pk).decode() if pk else None
    pqc_available = pk is not None

    if not args.quiet:
        alg_line = "ML-DSA-65 (Dilithium3, FIPS 204)" if pqc_available else "unavailable — install oqs-python"
        print(f"  {dim('PQC algorithm:')} {cyn(alg_line)}")
        if pqc_available:
            print(f"  {dim('Ephemeral public key:')} {pk_b64[:48]}…")
        print()
        print(f"  {dim('Generating')} {wht('7 scenarios')} {dim('→ 1 GCR per verdict')}…")
        print()

    # Build all 7 GCRs
    gcrs: List[Dict] = []
    for scen in SCENARIOS:
        gcr = _build_gcr(scen, sk, pk_b64)
        gcrs.append(gcr)
        _print_scenario(scen, gcr, args.quiet)

    # Assemble package
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    package_id = f"OMNIX-GDCL-PKG-{uuid.uuid4().hex[:16].upper()}"

    package = {
        "package_id":         package_id,
        "package_version":    "1.0.0",
        "generator":          "scripts/generate_gdcl_evidence_package.py",
        "adr_reference":      "ADR-206",
        "generated_at":       datetime.now(timezone.utc).isoformat(),
        "pqc_algorithm":      "ML-DSA-65 (Dilithium3, FIPS 204)" if pqc_available else None,
        "ephemeral_pk_b64":   pk_b64,
        "n_scenarios":        len(SCENARIOS),
        "verdicts_covered": [s["verdict"] for s in SCENARIOS],
        "verifier_command":   "python scripts/verify_gdcl_offline.py --file <this_file>",
        "adversarial_command":"python scripts/gdcl_adversarial_audit.py --package <this_file>",
        "algorithm_spec": {
            "reference":    "ADR-206 §Algorithm",
            "property":     "GDCL-INV-003 Determinism — pure function",
            "steps": [
                "1. If n_assessments == 0 → INDETERMINATE",
                "2. If INCOMPATIBLE ∧ DRIFT_CRITICAL both present → ESCALATION",
                "3. If all inputs INCOMPATIBLE → REFUSED",
                "4. If INCOMPATIBLE ∧ (PORTABLE ∨ ACKNOWLEDGED) present → CONTESTED",
                "5. If any DRIFT_CRITICAL present → LIMITED_RELIANCE",
                "6. If any DRIFT_ACKNOWLEDGED present → QUALIFIED_RELIANCE",
                "7. Otherwise → FULL_RELIANCE",
            ],
        },
        "scenarios": [
            {
                "scenario_id":  s["scenario_id"],
                "verdict":      s["verdict"],
                "title":        s["title"],
                "industry":     s["industry"],
                "description":  s["description"],
                "rsa_inputs":   s["rsa_inputs"],
                "gcr":          gcr,
            }
            for s, gcr in zip(SCENARIOS, gcrs)
        ],
    }

    # Write output
    out_dir = Path("evidence_packages")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.output) if args.output else out_dir / f"gdcl_evidence_package_{ts}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(package, f, indent=2, ensure_ascii=False)

    if not args.quiet:
        print(f"  {dim('─' * 68)}")
        print()
        print(f"  {wht('Package written:')} {cyn(str(out_path))}")
        print(f"  {dim('Package ID:')} {package_id}")
        print(f"  {dim('Verdicts:')} {len(gcrs)}/7 · {dim('PQC signed:')} {'yes' if pqc_available else 'no'}")
        print()
        print(f"  {dim('Verify:')}")
        print(f"  {dim('  python scripts/verify_gdcl_offline.py --file')} {str(out_path)}")
        print(f"  {dim('Adversarial audit:')}")
        print(f"  {dim('  python scripts/gdcl_adversarial_audit.py --package')} {str(out_path)}")
        print()
        print(f"  {grn('✓')} Package complete — {len(gcrs)} GCRs covering all 7 GDCL verdicts")
        print()
    else:
        print(str(out_path))

    return 0


if __name__ == "__main__":
    sys.exit(main())
