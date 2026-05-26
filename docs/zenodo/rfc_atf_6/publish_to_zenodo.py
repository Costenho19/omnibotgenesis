#!/usr/bin/env python3
"""
RFC-ATF-6 Zenodo Publisher
OMNIX QUANTUM LTD — Harold Nunes

IMPORTANT: Do NOT run until Harold has reviewed and approved all files.

Usage (when ready):
    export ZENODO_TOKEN=<your_token>
    python docs/zenodo/rfc_atf_6/publish_to_zenodo.py

Files uploaded:
    - docs/zenodo/rfc_atf_6/RFC-ATF-6.pdf
    - docs/standards/RFC-ATF-6.md
    - docs/zenodo/rfc_atf_6/conformance_vectors.json
"""
import os, sys, json, requests
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent
ZENODO_API = "https://zenodo.org/api"
TOKEN = os.environ.get("ZENODO_TOKEN", "")

if not TOKEN:
    print("ERROR: ZENODO_TOKEN not set. Export it before running.")
    sys.exit(1)

FILES_TO_UPLOAD = [
    ROOT / "docs/zenodo/rfc_atf_6/RFC-ATF-6.pdf",
    ROOT / "docs/standards/RFC-ATF-6.md",
    ROOT / "docs/zenodo/rfc_atf_6/conformance_vectors.json",
]

METADATA_FILE = ROOT / "docs/zenodo/rfc_atf_6/metadata.json"

HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def load_metadata():
    with open(METADATA_FILE) as f:
        raw = json.load(f)
    meta = {k: v for k, v in raw.items() if not k.startswith("_")}
    if "communities" in meta:
        del meta["communities"]
    return meta


def create_deposition():
    print("Creating new Zenodo deposition...")
    r = requests.post(
        f"{ZENODO_API}/deposit/depositions",
        json={},
        headers={**HEADERS, "Content-Type": "application/json"},
    )
    r.raise_for_status()
    dep = r.json()
    dep_id = dep["id"]
    bucket_url = dep["links"]["bucket"]
    print(f"  Deposition ID: {dep_id}")
    print(f"  Bucket URL:    {bucket_url}")
    return dep_id, bucket_url


def upload_files(bucket_url):
    for fpath in FILES_TO_UPLOAD:
        if not fpath.exists():
            print(f"  WARN: File not found — skipping: {fpath}")
            continue
        fname = fpath.name
        print(f"  Uploading {fname} ({fpath.stat().st_size // 1024} KB)...")
        with open(fpath, "rb") as f:
            r = requests.put(
                f"{bucket_url}/{fname}",
                data=f,
                headers=HEADERS,
            )
        r.raise_for_status()
        print(f"  OK: {fname}")


def set_metadata(dep_id, meta):
    print("Setting metadata...")
    r = requests.put(
        f"{ZENODO_API}/deposit/depositions/{dep_id}",
        json={"metadata": meta},
        headers={**HEADERS, "Content-Type": "application/json"},
    )
    if r.status_code not in (200, 201):
        print(f"  ERROR setting metadata: {r.status_code} {r.text[:500]}")
        r.raise_for_status()
    print("  Metadata set OK.")


def publish_deposition(dep_id):
    print("Publishing deposition...")
    r = requests.post(
        f"{ZENODO_API}/deposit/depositions/{dep_id}/actions/publish",
        headers=HEADERS,
    )
    if r.status_code not in (200, 202):
        print(f"  ERROR publishing: {r.status_code} {r.text[:500]}")
        r.raise_for_status()
    result = r.json()
    doi = result.get("doi") or result.get("metadata", {}).get("doi", "UNKNOWN")
    concept_doi = result.get("conceptdoi", doi)
    record_url = result.get("links", {}).get("record_html", "")
    print()
    print("=" * 60)
    print(f"  PUBLISHED SUCCESSFULLY")
    print(f"  DOI (version):  {doi}")
    print(f"  DOI (concept):  {concept_doi}")
    print(f"  Record URL:     {record_url}")
    print("=" * 60)
    print()
    print("NEXT STEPS:")
    print("  1. Verify DOI resolves at zenodo.org")
    print("  2. Update replit.md RFC-ATF-6 row in DOI table")
    print("  3. Update docs/standards/RFC-ATF-6.md header DOI field")
    print("  4. Notify Harold — do NOT post DOI publicly until verified Published (not Draft)")
    return doi, concept_doi, record_url


def main():
    print()
    print("RFC-ATF-6 Zenodo Submission")
    print("OMNIX QUANTUM LTD")
    print("-" * 60)
    print()

    missing = [f for f in FILES_TO_UPLOAD if not f.exists()]
    if missing:
        print("Missing files:")
        for f in missing:
            print(f"  {f}")
        print()
        print("Generate PDF first: python scripts/generate_atf6_pdf.py")
        sys.exit(1)

    meta = load_metadata()
    dep_id, bucket_url = create_deposition()
    upload_files(bucket_url)
    set_metadata(dep_id, meta)
    doi, concept_doi, record_url = publish_deposition(dep_id)

    result = {
        "deposition_id": dep_id,
        "doi": doi,
        "concept_doi": concept_doi,
        "record_url": record_url,
    }
    out = ROOT / "docs/zenodo/rfc_atf_6/submission_result.json"
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Result saved to: {out}")


if __name__ == "__main__":
    main()
