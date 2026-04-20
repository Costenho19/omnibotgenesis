"""
OMNIX Proof of Authorship Exporter — IP Timeline Evidence
Patent Reference: OMNIX-PAT-2026-015

Exports a machine-readable, tamper-evident timeline of the OMNIX codebase
development from git history. Designed for:
  • USPTO provisional patent filing evidence
  • UK IPO mediation — demonstrating prior art and development timeline
  • Investor due diligence — verifiable first-commit date + hash chain
  • Independent audit — self-contained JSON with SHA-256 integrity chain

Output: omnix_proof_export.json

Usage:
  python tools/proof_of_authorship.py
  python tools/proof_of_authorship.py --output docs/ip/omnix_proof_export.json
  python tools/proof_of_authorship.py --since 2024-01-01 --output evidence.json
  python tools/proof_of_authorship.py --verify omnix_proof_export.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

_WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_INVENTOR = "Harold Alberto Nunes Rodelo"
_COMPANY  = "OMNIX QUANTUM LTD, United Kingdom"
_PATENT   = "OMNIX-PAT-2026-015"
_PRODUCT  = "OMNIX Quantum — Decision Governance Infrastructure"


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=_WORKSPACE_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _sha256_file(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return "FILE_NOT_READABLE"


def _get_commits(since: str | None = None, max_commits: int = 2000) -> list[dict]:
    """Extract structured commit log from git history."""
    fmt = "%H|%ae|%an|%aI|%s"
    cmd = ["log", f"--pretty=format:{fmt}", f"--max-count={max_commits}"]
    if since:
        cmd.append(f"--since={since}")

    raw = _run_git(*cmd)
    commits = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        commits.append({
            "hash":      parts[0],
            "email":     parts[1],
            "author":    parts[2],
            "timestamp": parts[3],
            "message":   parts[4],
        })
    return commits


def _get_repo_stats() -> dict:
    """Collect overall repository statistics."""
    try:
        total_commits = int(_run_git("rev-list", "--count", "HEAD"))
    except Exception:
        total_commits = None

    try:
        first_commit_hash = _run_git("rev-list", "--max-parents=0", "HEAD")
        first_commit_ts   = _run_git("log", "-1", "--format=%aI", first_commit_hash)
        first_commit_msg  = _run_git("log", "-1", "--format=%s",  first_commit_hash)
    except Exception:
        first_commit_hash = first_commit_ts = first_commit_msg = None

    try:
        head_hash = _run_git("rev-parse", "HEAD")
    except Exception:
        head_hash = None

    try:
        branches_raw = _run_git("branch", "-a")
        branches = [b.strip().lstrip("* ") for b in branches_raw.splitlines() if b.strip()]
    except Exception:
        branches = []

    try:
        remote_url = _run_git("config", "--get", "remote.origin.url")
    except Exception:
        remote_url = None

    try:
        contributors_raw = _run_git("shortlog", "-sn", "--no-merges", "HEAD")
        contributors = []
        for line in contributors_raw.splitlines():
            parts = line.strip().split("\t", 1)
            if len(parts) == 2:
                contributors.append({"commits": int(parts[0].strip()), "name": parts[1].strip()})
    except Exception:
        contributors = []

    try:
        tag_raw = _run_git("describe", "--tags", "--always")
    except Exception:
        tag_raw = None

    return {
        "total_commits":      total_commits,
        "head_commit":        head_hash,
        "first_commit":       first_commit_hash,
        "first_commit_date":  first_commit_ts,
        "first_commit_msg":   first_commit_msg,
        "latest_tag":         tag_raw,
        "branches":           branches[:10],
        "remote_origin":      remote_url,
        "contributors":       contributors,
    }


def _get_key_files() -> list[dict]:
    """Hash and record the most critical IP-bearing files."""
    key_paths = [
        "omnix_core/governance/structural_admissibility_engine.py",
        "omnix_core/governance/external_evaluator.py",
        "omnix_core/governance/trajectory_invariant_engine.py",
        "omnix_core/governance/jurisdiction_gate.py",
        "omnix_core/governance/sharia_gate.py",
        "omnix_core/governance/aml_gate.py",
        "omnix_core/governance/fraud_gate.py",
        "omnix_core/evidence/decision_receipt.py",
        "omnix_core/quantum/physics_validator.py",
        "docs/adr/ADR-092-structural-admissibility-engine.md",
        "tools/stress_test.py",
        "tools/proof_of_authorship.py",
    ]

    result = []
    for rel_path in key_paths:
        abs_path = os.path.join(_WORKSPACE_ROOT, rel_path)
        file_hash = _sha256_file(abs_path)

        try:
            git_log = _run_git("log", "--follow", "--format=%H|%aI|%s",
                                "--max-count=1", "--", rel_path)
            parts = git_log.split("|", 2) if git_log else []
            first_seen_hash = parts[0] if len(parts) > 0 else None
            first_seen_date = parts[1] if len(parts) > 1 else None
            first_seen_msg  = parts[2] if len(parts) > 2 else None
        except Exception:
            first_seen_hash = first_seen_date = first_seen_msg = None

        result.append({
            "path":             rel_path,
            "sha256":           file_hash,
            "exists":           os.path.isfile(abs_path),
            "first_seen_commit": first_seen_hash,
            "first_seen_date":  first_seen_date,
            "first_seen_msg":   first_seen_msg,
        })

    return result


def _build_hash_chain(commits: list[dict]) -> list[dict]:
    """
    Build a cumulative SHA-256 chain over the commit sequence.
    Each link = SHA256(prev_chain_hash + commit_hash + timestamp).
    This makes any retroactive tampering of the chain detectable.
    """
    chain = []
    prev_hash = "OMNIX_GENESIS_0000000000000000000000000000000000000000000000000000000000000000"

    for commit in reversed(commits):
        link_input = f"{prev_hash}|{commit['hash']}|{commit['timestamp']}"
        link_hash  = _sha256(link_input)
        chain.append({
            "seq":        len(chain),
            "commit":     commit["hash"],
            "timestamp":  commit["timestamp"],
            "chain_hash": link_hash,
        })
        prev_hash = link_hash

    return chain


def export_proof(
    output_path: str        = "omnix_proof_export.json",
    since: str | None       = None,
    max_commits: int        = 2000,
    include_full_chain: bool = True,
) -> dict[str, Any]:

    export_ts = datetime.now(timezone.utc).isoformat()
    print(f"\n  OMNIX Proof of Authorship Exporter")
    print(f"  {export_ts}")
    print(f"  {'─'*50}")

    print("  [1/5] Reading repository stats...")
    repo_stats = _get_repo_stats()

    print(f"  [2/5] Extracting commit history (max {max_commits:,})...")
    commits = _get_commits(since=since, max_commits=max_commits)
    print(f"        Found {len(commits):,} commits")

    print("  [3/5] Hashing key IP files...")
    key_files = _get_key_files()

    print("  [4/5] Building tamper-evident hash chain...")
    hash_chain = _build_hash_chain(commits) if include_full_chain else []

    terminal_hash = hash_chain[-1]["chain_hash"] if hash_chain else None

    print("  [5/5] Assembling proof document...")

    document_body = {
        "proof_id":       f"OMNIX-PROOF-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "generated_at":   export_ts,
        "inventor":       _INVENTOR,
        "company":        _COMPANY,
        "product":        _PRODUCT,
        "patent_ref":     _PATENT,
        "repository": {
            "first_commit":      repo_stats.get("first_commit"),
            "first_commit_date": repo_stats.get("first_commit_date"),
            "first_commit_msg":  repo_stats.get("first_commit_msg"),
            "head_commit":       repo_stats.get("head_commit"),
            "total_commits":     repo_stats.get("total_commits"),
            "contributors":      repo_stats.get("contributors"),
            "latest_tag":        repo_stats.get("latest_tag"),
        },
        "key_ip_files":   key_files,
        "commit_sample": {
            "first":  commits[-1] if commits else None,
            "latest": commits[0]  if commits else None,
            "count":  len(commits),
            "since_filter": since,
        },
        "terminal_chain_hash": terminal_hash,
        "hash_chain": hash_chain if include_full_chain else [],
    }

    document_str  = json.dumps(document_body, sort_keys=True, ensure_ascii=False)
    document_hash = _sha256(document_str)

    proof = {
        **document_body,
        "document_integrity": {
            "sha256":       document_hash,
            "algorithm":    "SHA-256",
            "note":         "SHA-256 of the document body (excluding this integrity block), JSON-serialized with sorted keys",
        },
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(proof, f, indent=2, ensure_ascii=False)

    final_hash = _sha256_file(output_path)

    print(f"\n  {'─'*50}")
    print(f"  Output file      : {output_path}")
    print(f"  File SHA-256     : {final_hash}")
    print(f"  Commits exported : {len(commits):,}")
    print(f"  First commit     : {repo_stats.get('first_commit_date', 'N/A')}")
    print(f"  Terminal hash    : {(terminal_hash or 'N/A')[:32]}...")
    print(f"  Key files hashed : {len(key_files)}")
    print(f"  {'─'*50}")
    print(f"\n  Submit {output_path} as part of your USPTO provisional patent evidence.\n")

    return proof


def verify_proof(proof_path: str) -> bool:
    """
    Verify the integrity of a previously exported proof file.
    Returns True if the document hash matches the embedded SHA-256.
    """
    print(f"\n  Verifying: {proof_path}")
    with open(proof_path, "r", encoding="utf-8") as f:
        proof = json.load(f)

    embedded_hash = proof.get("document_integrity", {}).get("sha256")
    if not embedded_hash:
        print("  [FAIL] No embedded integrity hash found.")
        return False

    body = {k: v for k, v in proof.items() if k != "document_integrity"}
    recomputed = _sha256(json.dumps(body, sort_keys=True, ensure_ascii=False))

    if recomputed == embedded_hash:
        print(f"  [PASS] Document integrity verified — SHA-256 match")
        print(f"         {embedded_hash}")
        return True
    else:
        print(f"  [FAIL] Integrity mismatch!")
        print(f"         Expected : {embedded_hash}")
        print(f"         Got      : {recomputed}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OMNIX Proof of Authorship Exporter"
    )
    parser.add_argument("--output",   type=str, default="omnix_proof_export.json",
                        help="Output JSON file path (default: omnix_proof_export.json)")
    parser.add_argument("--since",    type=str, default=None,
                        help="Only include commits since this date (e.g. 2024-01-01)")
    parser.add_argument("--max",      type=int, default=2000,
                        help="Maximum commits to export (default: 2000)")
    parser.add_argument("--verify",   type=str, default=None,
                        help="Verify an existing proof file instead of generating")
    parser.add_argument("--no-chain", action="store_true",
                        help="Skip hash chain (faster, smaller file)")
    args = parser.parse_args()

    if args.verify:
        ok = verify_proof(args.verify)
        sys.exit(0 if ok else 1)
    else:
        export_proof(
            output_path=args.output,
            since=args.since,
            max_commits=args.max,
            include_full_chain=not args.no_chain,
        )
