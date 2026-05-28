"""
OMNIX-RTE-001 Reviewer Package Builder
=======================================
Creates a self-contained ZIP for external reviewers.

Contents:
  OMNIX-RTE-001-REVIEWER/
  ├── README_FIRST.md
  ├── VERIFY.md
  ├── QUICKSTART.md
  ├── verify.py          (standalone verifier — stdlib only)
  └── evidence/
      ├── OMNIX-RTE-001_*.json
      └── OMNIX-RTE-001_*.pdf

Requirements: Python 3.9+ — no dependencies.

Usage:
  python scripts/package_reviewer.py
  python scripts/package_reviewer.py --package evidence_packages/OMNIX-RTE-001_*.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import sys
import zipfile
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_latest_rte_package() -> tuple[str, str]:
    """Return (json_path, pdf_path) for the most recent RTE-001 package."""
    pattern = os.path.join(ROOT, "evidence_packages", "OMNIX-RTE-001_*.json")
    candidates = sorted(glob.glob(pattern))
    if not candidates:
        raise FileNotFoundError(
            "No OMNIX-RTE-001_*.json found in evidence_packages/\n"
            "Run: GIT_DIR=/dev/null python scripts/generate_treasury_execution_trace.py"
        )
    json_path = candidates[-1]
    pdf_path = json_path.replace(".json", ".pdf")
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}\n"
            "Run: python scripts/generate_rte_pdf.py"
        )
    return json_path, pdf_path


def build_package(json_path: str, pdf_path: str) -> str:
    """Build the reviewer ZIP. Returns the output path."""
    # Read package metadata
    with open(json_path, encoding="utf-8") as f:
        pkg = json.load(f)

    if pkg.get("package_type") != "OMNIX-RTE-001":
        raise ValueError(f"Not an OMNIX-RTE-001 package: {json_path}")

    pkg_id      = pkg.get("package_id", "UNKNOWN")
    generated   = pkg.get("generated_at", "")[:10].replace("-", "")
    timestamp   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    zip_name    = f"OMNIX-RTE-001-REVIEWER_{timestamp}.zip"
    zip_path    = os.path.join(ROOT, "evidence_packages", zip_name)
    inner_dir   = "OMNIX-RTE-001-REVIEWER"

    # Source files
    docs_reviewer = os.path.join(ROOT, "docs", "reviewer")
    verifier_src  = os.path.join(ROOT, "scripts", "verify_treasury_execution_trace.py")

    required_docs = ["README_FIRST.md", "VERIFY.md", "QUICKSTART.md"]
    for doc in required_docs:
        path = os.path.join(docs_reviewer, doc)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing reviewer doc: {path}")

    if not os.path.exists(verifier_src):
        raise FileNotFoundError(f"Verifier not found: {verifier_src}")

    print(f"[INFO]  Building reviewer package...")
    print(f"[INFO]  Package: {pkg_id}")
    print(f"[INFO]  JSON:    {os.path.basename(json_path)} ({os.path.getsize(json_path) // 1024} KB)")
    print(f"[INFO]  PDF:     {os.path.basename(pdf_path)} ({os.path.getsize(pdf_path) // 1024} KB)")
    print()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:

        # Docs
        for doc in required_docs:
            zf.write(
                os.path.join(docs_reviewer, doc),
                arcname=f"{inner_dir}/{doc}",
            )

        # Verifier — renamed to verify.py for simplicity
        zf.write(verifier_src, arcname=f"{inner_dir}/verify.py")

        # Evidence files
        zf.write(json_path, arcname=f"{inner_dir}/evidence/{os.path.basename(json_path)}")
        zf.write(pdf_path,  arcname=f"{inner_dir}/evidence/{os.path.basename(pdf_path)}")

    zip_size = os.path.getsize(zip_path)

    # Print manifest
    print("=" * 65)
    print("  OMNIX-RTE-001 REVIEWER PACKAGE")
    print("=" * 65)
    print(f"  Output:  {zip_path}")
    print(f"  Size:    {zip_size // 1024} KB")
    print()
    print("  Contents:")
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            size_kb = info.file_size // 1024
            print(f"    {info.filename:<60} {size_kb:>5} KB")
    print()
    print("  Verification commands (after unzip):")
    print()
    print("    cd OMNIX-RTE-001-REVIEWER")
    print("    python verify.py                    # 101 / 101 PASS")
    print("    python verify.py --verify-halt      #  25 /  25 PASS")
    print("    python verify.py --verify-settlement#  33 /  33 PASS")
    print()
    print("  Anchor artifact:")
    adm = pkg["paths"]["path_admissible"]
    pogc = adm["steps"]["6_gate"]["proof_of_governance_certificate"]
    seal = adm["steps"]["6_gate"].get("mbr_seal", {})
    settle = adm["steps"]["7_execution"]["settlement_reference"]
    print(f"    POGC ID:    {pogc.get('pogc_id', '-')}")
    print(f"    Tier:       {seal.get('certification_tier', pogc.get('mandate_certification', '-'))}")
    print(f"    Settlement: USD {int(settle.get('amount_usd', 0)):,}")
    print(f"    SWIFT:      {settle.get('swift_mt202_ref', '-')}")
    print(f"    XRPL:       {settle.get('xrpl_tx_id', '-')}")
    print("=" * 65)

    return zip_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OMNIX-RTE-001 Reviewer Package Builder"
    )
    parser.add_argument(
        "--package", "-p",
        help="Path to OMNIX-RTE-001 JSON package (default: most recent)"
    )
    args = parser.parse_args()

    try:
        if args.package:
            json_path = args.package
            pdf_path  = json_path.replace(".json", ".pdf")
        else:
            json_path, pdf_path = find_latest_rte_package()

        zip_path = build_package(json_path, pdf_path)
        return 0

    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
