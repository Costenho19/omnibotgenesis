#!/usr/bin/env python3
"""
OMNIX COLD Archive Block Demo Generator
========================================
ADR-163 — Immutable Evidence Archive Pipeline
EAP-INV-005 — Offline Reconstructability

Generates a self-contained demo COLD archive block with synthetic but
cryptographically valid artifacts, signs it with a freshly generated
ML-DSA-65 key pair, and immediately verifies it using the same logic
as the public verifier (omnix_atf_verify.py --archive-block).

This script demonstrates that any third party — regulator, auditor, partner —
can independently verify a COLD block using only:
  · The block JSON file
  · The issuer's public key (.b64 file)
  · The omnix_atf_verify.py CLI

Output:
  cold_archive_demo/
    OMNIX-BLOCK-{date}-000001.json   ← The sealed COLD block
    omnix_demo_public_key.b64        ← Public key for external verification
    omnix_demo_private_key.b64       ← Private key (demo only — destroy after use)
    verify_block.sh                  ← Ready-to-run verification script

Usage:
  python tools/generate_demo_block.py
  python tools/generate_demo_block.py --output ./my_demo --artifacts 20
  python tools/generate_demo_block.py --chain 3   (generate 3-block chain)
  python tools/generate_demo_block.py --skip-verify

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add workspace root to path so we can import the sealer
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from omnix_core.evidence.cold_block_sealer import (
    ColdBlockSealer,
    compute_merkle_root,
    compute_canonical_hash,
    OMNIX_VERSION,
    HASH_ALGORITHM_V1,
    PQC_ALGORITHM,
    GENESIS_PREDECESSOR,
    IMMUTABLE_CLASSES,
)

# ─────────────────────────────────────────────────────────────────────────────
# Terminal colours
# ─────────────────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
GRAY   = "\033[90m"
GOLD   = "\033[33m"
RED    = "\033[91m"

# ─────────────────────────────────────────────────────────────────────────────
# PQC key generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_demo_keypair() -> Tuple[Optional[str], Optional[str], str]:
    """
    Generate an ML-DSA-65 (Dilithium-3) key pair for demo purposes.
    Returns (public_key_b64, secret_key_b64, algorithm_label).
    Returns (None, None, label) if PQC library is unavailable.
    """
    try:
        from pqc.sign import dilithium3 as dil
        pk, sk = dil.keypair()
        return (
            base64.b64encode(pk).decode(),
            base64.b64encode(sk).decode(),
            "ML-DSA-65 (Dilithium-3, FIPS 204)",
        )
    except ImportError:
        pass

    try:
        from omnix_core.security.crypto_providers import get_active_provider
        provider = get_active_provider()
        pk, sk = provider.keypair()
        return (
            base64.b64encode(pk).decode(),
            base64.b64encode(sk).decode(),
            provider.algorithm_name(),
        )
    except Exception:
        pass

    return None, None, "UNAVAILABLE"


# ─────────────────────────────────────────────────────────────────────────────
# Demo artifact factory
# ─────────────────────────────────────────────────────────────────────────────

def _sha256_prefixed(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_json(obj: Dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def make_demo_artifact(
    evidence_class: str,
    index: int,
    chain_root_id: str,
    public_key_b64: Optional[str],
    secret_key_b64: Optional[str],
) -> Dict[str, Any]:
    """
    Generate a realistic synthetic artifact matching OMNIX's receipt format.
    PQC-signs the artifact if a key pair is available.
    """
    now_ns     = time.time_ns()
    now_iso    = datetime.now(timezone.utc).isoformat()
    art_id     = f"ATFDR-DEMO-{uuid.uuid4().hex[:14].upper()}"
    domain     = ["trading", "compliance", "execution", "risk", "governance"][index % 5]
    agent_id   = f"AID-{domain.upper()}-DEMO{index:04d}"

    base_fields: Dict[str, Any] = {
        "artifact_id":     art_id,
        "evidence_class":  evidence_class,
        "domain":          domain,
        "agent_id":        agent_id,
        "chain_root_id":   chain_root_id,
        "created_at":      now_iso,
        "created_at_ns":   now_ns,
        "omnix_version":   OMNIX_VERSION,
        "index":           index,
    }

    # Add class-specific fields to make the artifact realistic
    if evidence_class == "LEGAL":
        base_fields.update({
            "receipt_type":    "governance_decision",
            "decision":        "APPROVED" if index % 3 != 0 else "REJECTED",
            "avm_score":       round(0.62 + (index % 5) * 0.06, 4),
            "authority_budget": round(100.0 - index * 1.5, 1),
            "task_scope":      {"action": "execute_trade", "asset": "BTC-USD", "qty": 0.1},
        })
    elif evidence_class == "PQC":
        base_fields.update({
            "receipt_type":       "delegation_receipt",
            "delegation_depth":   index % 4,
            "delegator_id":       f"OPERATOR-{index:03d}",
            "delegate_id":        agent_id,
            "authority_budget_delegator": 80.0,
            "authority_budget_granted":   60.0,
        })
        if public_key_b64:
            base_fields["delegator_public_key"] = public_key_b64
    elif evidence_class == "CONTRACT":
        base_fields.update({
            "receipt_type":       "cross_runtime_contract",
            "runtime_a":          "OMNIX-RT-001",
            "runtime_b":          "PARTNER-RT-002",
            "policy_params":      {"ces_threshold": 75.0, "afg_limit": 0.90},
            "bilateral_agreement": True,
        })
    elif evidence_class == "EXCEPTION":
        base_fields.update({
            "receipt_type":       "halt_event",
            "halt_reason":        "FRAGMENTATION" if index % 2 == 0 else "CRITICAL",
            "ces_score":          round((index % 3) * 4.5, 2),
            "fragmentation_score": round(0.91 + (index % 3) * 0.01, 4),
        })
    elif evidence_class == "TELEMETRY":
        base_fields.update({
            "receipt_type": "runtime_continuity_record",
            "status":       "MONITORING",
            "ces_score":    round(52.0 + index * 0.3, 2),
            "sample_count": index * 10 + 1,
        })
    elif evidence_class == "SAMPLE":
        base_fields.update({
            "receipt_type": "runtime_continuity_record",
            "status":       "NOMINAL",
            "ces_score":    round(88.0 + (index % 8), 2),
        })

    # Compute content hash (canonical, excludes signature fields)
    exclude = {"content_hash", "pqc_signature", "pqc_algorithm", "pqc_signatures"}
    clean   = {k: v for k, v in base_fields.items() if k not in exclude}
    ch_hex  = hashlib.sha256(_canonical_json(clean)).hexdigest()
    base_fields["content_hash"] = ch_hex

    # PQC sign if key available
    if secret_key_b64:
        try:
            from pqc.sign import dilithium3 as dil
            sk  = base64.b64decode(secret_key_b64)
            sig = dil.sign(ch_hex.encode("utf-8"), sk)
            base_fields["pqc_signatures"] = [base64.b64encode(sig).decode()]
            base_fields["pqc_algorithm"]  = "dilithium3"
        except Exception:
            pass

    return base_fields


def make_demo_artifacts(
    n: int,
    public_key_b64: Optional[str],
    secret_key_b64: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Generate n demo artifacts distributed across all evidence classes,
    with immutable classes guaranteed to be represented.
    """
    chain_root = f"ATFDR-ROOT-DEMO-{uuid.uuid4().hex[:8].upper()}"
    classes    = ["LEGAL", "PQC", "CONTRACT", "EXCEPTION", "TELEMETRY", "SAMPLE"]
    artifacts  = []
    for i in range(n):
        cls = classes[i % len(classes)]
        artifacts.append(make_demo_artifact(cls, i, chain_root, public_key_b64, secret_key_b64))
    return artifacts


# ─────────────────────────────────────────────────────────────────────────────
# Shell verification script writer
# ─────────────────────────────────────────────────────────────────────────────

def write_verify_script(
    output_dir: Path,
    block_files: List[str],
    public_key_file: str,
) -> str:
    """Write a ready-to-run shell script that verifies all demo blocks."""
    lines = [
        "#!/usr/bin/env bash",
        "#",
        "# OMNIX COLD Archive Block — Independent Verification",
        "# Generated by tools/generate_demo_block.py",
        "# ADR-163 / EAP-INV-005: Offline Reconstructability",
        "#",
        "# This script verifies all demo blocks without any OMNIX platform access.",
        "# Requirements: Python 3.9+ · pypqc (pip install pypqc)",
        "#",
        "",
        'VERIFIER="omnix_atf_verify.py"',
        f'PUBLIC_KEY="{public_key_file}"',
        "",
        "echo '═══════════════════════════════════════════════════════'",
        "echo ' OMNIX COLD Archive Block — Independent Verification'",
        "echo '═══════════════════════════════════════════════════════'",
        "echo ''",
        "PASS=0",
        "FAIL=0",
        "",
    ]

    if len(block_files) == 1:
        lines += [
            f'echo "Verifying: {block_files[0]}"',
            f'python "$VERIFIER" --archive-block "{block_files[0]}" --public-key "$PUBLIC_KEY"',
            'if [ $? -eq 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi',
            "",
        ]
    else:
        for i, bf in enumerate(block_files):
            if i == 0:
                lines += [
                    f'echo "Verifying genesis block: {bf}"',
                    f'python "$VERIFIER" --archive-block "{bf}" --public-key "$PUBLIC_KEY"',
                    'if [ $? -eq 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi',
                    "",
                ]
            else:
                pred = block_files[i - 1]
                lines += [
                    f'echo "Verifying block {i+1}/{len(block_files)}: {bf}"',
                    f'python "$VERIFIER" \\',
                    f'  --archive-block "{bf}" \\',
                    f'  --public-key "$PUBLIC_KEY" \\',
                    f'  --verify-chain \\',
                    f'  --predecessor-block "{pred}"',
                    'if [ $? -eq 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi',
                    "",
                ]

    lines += [
        'echo ""',
        'echo "═══════════════════════════════════════════════════════"',
        'echo "Results: $PASS passed, $FAIL failed"',
        'if [ "$FAIL" -eq 0 ]; then',
        '  echo "VERDICT: PASS — All blocks verified (ADR-163 / EAP-INV-005)"',
        '  exit 0',
        'else',
        '  echo "VERDICT: FAIL — One or more blocks failed verification"',
        '  exit 1',
        'fi',
    ]

    script_path = output_dir / "verify_block.sh"
    with open(script_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(script_path, 0o755)
    return str(script_path)


# ─────────────────────────────────────────────────────────────────────────────
# In-process verification (uses same logic as omnix_atf_verify.py)
# ─────────────────────────────────────────────────────────────────────────────

def verify_block_in_process(
    block: Dict[str, Any],
    public_key_b64: Optional[str],
    predecessor_block: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Verify a block using omnix_atf_verify.py's verify_archive_block function.
    Returns True if PASS, False otherwise.
    """
    verifier_path = ROOT / "docs" / "zenodo" / "submission_package" / "omnix_atf_verify.py"
    if verifier_path.exists():
        import importlib.util
        import sys as _sys
        spec   = importlib.util.spec_from_file_location("omnix_atf_verify", verifier_path)
        module = importlib.util.module_from_spec(spec)
        _sys.modules["omnix_atf_verify"] = module
        spec.loader.exec_module(module)
        result = module.verify_archive_block(block, public_key_b64, predecessor_block)
        return result.verdict == "PASS"
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate OMNIX COLD Archive Block demo files (ADR-163 / EAP-INV-005)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--output",    default="cold_archive_demo",
                        help="Output directory (default: cold_archive_demo)")
    parser.add_argument("--artifacts", type=int, default=12,
                        help="Number of artifacts per block (default: 12)")
    parser.add_argument("--chain",     type=int, default=1,
                        help="Number of blocks to chain together (default: 1)")
    parser.add_argument("--skip-verify", action="store_true",
                        help="Skip in-process verification after generation")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{BOLD}{GOLD}╔══════════════════════════════════════════════════════════╗")
    print(f"║    OMNIX COLD Archive Block Generator  ·  ADR-163        ║")
    print(f"║    EAP-INV-005: Offline Reconstructability Demo          ║")
    print(f"╚══════════════════════════════════════════════════════════╝{RESET}\n")

    # ── Generate key pair ────────────────────────────────────────────────────
    print(f"{CYAN}[1/4]{RESET} Generating ML-DSA-65 (Dilithium-3) key pair...")
    pub_b64, sec_b64, algo_label = generate_demo_keypair()

    if pub_b64:
        print(f"      {GREEN}✓{RESET} Key pair generated — {algo_label}")
        pub_key_file = output_dir / "omnix_demo_public_key.b64"
        sec_key_file = output_dir / "omnix_demo_private_key.b64"
        pub_key_file.write_text(pub_b64)
        sec_key_file.write_text(sec_b64 or "")
        print(f"      {GRAY}Public key  → {pub_key_file}{RESET}")
        print(f"      {GRAY}Private key → {sec_key_file}  (demo only — destroy after use){RESET}")
    else:
        print(f"      {YELLOW}⚠{RESET} pypqc not available — blocks will be generated without PQC signatures")
        print(f"      {GRAY}Install: pip install pypqc{RESET}")
        pub_key_file = None

    # ── Generate artifacts and seal blocks ───────────────────────────────────
    print(f"\n{CYAN}[2/4]{RESET} Generating {args.artifacts} artifacts × {args.chain} block(s)...")

    sealer = ColdBlockSealer(
        output_dir=str(output_dir),
        secret_key_b64=sec_b64 or "",
    )

    sealed_blocks: List[Dict[str, Any]] = []
    block_files:   List[str] = []
    predecessor_block: Optional[Dict] = None

    for block_idx in range(args.chain):
        artifacts = make_demo_artifacts(args.artifacts, pub_b64, sec_b64)
        result    = sealer.seal(
            artifacts=artifacts,
            trigger="admin",
            predecessor_block=predecessor_block,
            sealed_by="generate_demo_block.py",
        )

        if not result.success:
            print(f"  {RED}✗{RESET} Block {block_idx + 1} seal FAILED: {result.errors}")
            return 1

        block_dict = result.block.to_dict()
        sealed_blocks.append(block_dict)
        block_files.append(result.block_file)
        predecessor_block = block_dict

        pqc_icon = f"{GREEN}✓{RESET}" if result.block.is_pqc_signed else f"{YELLOW}–{RESET}"
        print(
            f"  {GREEN}✓{RESET}  {result.block.block_id}"
            f"  |  {result.block.artifact_count} artifacts"
            f"  |  PQC: {pqc_icon}"
            f"  |  {result.seal_duration_ms:.1f}ms"
        )
        if result.warnings:
            for w in result.warnings:
                print(f"     {YELLOW}⚠{RESET}  {w}")

    # ── Write verification script ────────────────────────────────────────────
    print(f"\n{CYAN}[3/4]{RESET} Writing verification script...")
    relative_blocks  = [Path(bf).name for bf in block_files]
    pub_key_rel      = pub_key_file.name if pub_key_file else "omnix_demo_public_key.b64"
    script_path      = write_verify_script(output_dir, relative_blocks, pub_key_rel)
    print(f"      {GREEN}✓{RESET} {script_path}")

    # ── In-process verification ──────────────────────────────────────────────
    print(f"\n{CYAN}[4/4]{RESET} Verifying generated blocks (EAP-INV-005)...")

    if args.skip_verify:
        print(f"      {GRAY}–{RESET}  Verification skipped (--skip-verify)")
    else:
        all_pass = True
        prev: Optional[Dict] = None
        for i, block in enumerate(sealed_blocks):
            ok = verify_block_in_process(block, pub_b64, prev)
            icon = f"{GREEN}✓ PASS{RESET}" if ok else f"{RED}✗ FAIL{RESET}"
            print(f"  {icon}  {block['block_id']}")
            if not ok:
                all_pass = False
            prev = block

        if all_pass:
            print(f"\n  {GREEN}{BOLD}All blocks pass independent verification.{RESET}")
            print(f"  {GRAY}Any auditor with the public key can reproduce this result.{RESET}")
        else:
            print(f"\n  {RED}{BOLD}WARNING: One or more blocks FAILED verification.{RESET}")
            return 1

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"""
{BOLD}{GOLD}──────────────────────────────────────────────────────────────{RESET}
{BOLD}Demo Output:{RESET}  {output_dir}/

{BOLD}Block files:{RESET}""")
    for bf in block_files:
        print(f"  {GRAY}{Path(bf).name}{RESET}")

    if pub_key_file:
        print(f"""
{BOLD}Public key:{RESET}   {pub_key_file.name}
""")

    print(f"""{BOLD}To verify independently (from {output_dir}/):{RESET}

  {CYAN}# Single block:{RESET}
  python ../docs/zenodo/submission_package/omnix_atf_verify.py \\
    --archive-block {Path(block_files[0]).name} \\
    --public-key {pub_key_rel}""")

    if len(block_files) >= 2:
        print(f"""
  {CYAN}# With chain verification:{RESET}
  python ../docs/zenodo/submission_package/omnix_atf_verify.py \\
    --archive-block {Path(block_files[-1]).name} \\
    --public-key {pub_key_rel} \\
    --verify-chain \\
    --predecessor-block {Path(block_files[-2]).name}""")

    print(f"""
  {CYAN}# Or use the generated script:{RESET}
  bash {output_dir}/verify_block.sh

{BOLD}JSON output (programmatic):{RESET}
  python omnix_atf_verify.py --archive-block <BLOCK>.json \\
    --public-key {pub_key_rel} --json

{GRAY}──────────────────────────────────────────────────────────────
ADR-163 / EAP-INV-005 — Offline Reconstructability
OMNIX QUANTUM LTD · https://omnixquantum.com/atf/verify
──────────────────────────────────────────────────────────────{RESET}
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
