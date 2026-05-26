"""
OMNIX QUANTUM — RFC-ATF-5 Zenodo Publisher
Run: python docs/zenodo/rfc_atf_5/publish_to_zenodo.py

Requires: ZENODO_TOKEN environment variable
  export ZENODO_TOKEN=your_personal_access_token

Files uploaded:
  - RFC-ATF-5.pdf (primary document with visual diagrams)
  - RFC-ATF-5.md  (copy from docs/standards/ into this dir first)
  - conformance_vectors.json (this directory)
"""

import os, json, sys, requests, shutil
from pathlib import Path

TOKEN = os.environ.get('ZENODO_TOKEN')
if not TOKEN:
    print("ERROR: Set ZENODO_TOKEN environment variable")
    sys.exit(1)

BASE    = "https://zenodo.org/api"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
DIR     = Path(__file__).parent
ROOT    = DIR.parent.parent.parent

# Copy RFC-ATF-5.md from docs/standards/ if not already here
rfc_src = ROOT / "docs" / "standards" / "RFC-ATF-5.md"
rfc_dst = DIR / "RFC-ATF-5.md"
if not rfc_dst.exists() and rfc_src.exists():
    shutil.copy(rfc_src, rfc_dst)
    print(f"  Copied RFC-ATF-5.md from docs/standards/")

# Load metadata — strip private _keys before sending
with open(DIR / "metadata.json") as f:
    META_RAW = json.load(f)

META = {k: v for k, v in META_RAW.items() if not k.startswith("_")}
# Also strip _note fields inside nested objects
for key in ["creators", "subjects"]:
    if key in META and isinstance(META[key], list):
        META[key] = [{k2: v2 for k2, v2 in item.items() if not k2.startswith("_")} for item in META[key]]
# Remove communities — Zenodo returns 422 if identifier doesn't exist.
# Add to a community manually from the Zenodo UI after publishing.
META.pop("communities", None)

FILES_TO_UPLOAD = [
    DIR / "RFC-ATF-5.pdf",
    DIR / "RFC-ATF-5.md",
    DIR / "conformance_vectors.json",
]

def check(r, step):
    if not r.ok:
        print(f"FAILED at {step}: {r.status_code} — {r.text[:500]}")
        sys.exit(1)
    print(f"  OK [{r.status_code}] {step}")
    return r.json()

print("\n=== RFC-ATF-5 Zenodo Publication ===\n")
print("Files to upload:")
for f in FILES_TO_UPLOAD:
    status = "✓ found" if f.exists() else "✗ NOT FOUND"
    print(f"  {f.name}: {status}")

missing = [f for f in FILES_TO_UPLOAD if not f.exists()]
if missing:
    print(f"\nERROR: Missing files: {[f.name for f in missing]}")
    print("  Copy RFC-ATF-5.md from docs/standards/ into this directory first.")
    sys.exit(1)

print()

# 1. Create new deposition
print("1. Creating deposition...")
r = requests.post(f"{BASE}/deposit/depositions", headers=HEADERS, json={})
dep = check(r, "create deposition")
dep_id  = dep["id"]
bucket  = dep["links"]["bucket"]
html    = dep["links"]["html"]
print(f"   Deposition ID: {dep_id}")
print(f"   Draft URL:     {html}")

# 2. Upload files
print("\n2. Uploading files...")
for fpath in FILES_TO_UPLOAD:
    with open(fpath, 'rb') as fp:
        r = requests.put(
            f"{bucket}/{fpath.name}",
            headers=HEADERS,
            data=fp
        )
    check(r, f"upload {fpath.name}")

# 3. Set metadata
print("\n3. Setting metadata...")
payload = {"metadata": META}
r = requests.put(
    f"{BASE}/deposit/depositions/{dep_id}",
    headers={**HEADERS, "Content-Type": "application/json"},
    data=json.dumps(payload)
)
check(r, "set metadata")

# 4. Confirm before publishing
print(f"\n4. Ready to publish.")
print(f"   Review your draft first at: {html}")
print(f"\n   Type 'PUBLISH' to confirm and publish:")
confirm = input("   > ").strip()
if confirm != 'PUBLISH':
    print("   Aborted. Draft saved — publish manually from Zenodo.")
    sys.exit(0)

# 5. Publish
print("\n5. Publishing...")
r = requests.post(
    f"{BASE}/deposit/depositions/{dep_id}/actions/publish",
    headers=HEADERS
)
result = check(r, "publish")
doi    = result.get("doi", "—")
url    = result.get("links", {}).get("record_html", html)

print(f"\n{'='*55}")
print(f"  PUBLISHED SUCCESSFULLY")
print(f"  DOI: {doi}")
print(f"  URL: {url}")
print(f"{'='*55}")
print(f"\nNext steps:")
print(f"  1. Update RFC-ATF-5.md lines 4+111: replace [PENDING] with {doi}")
print(f"  2. Update replit.md RFC table with the new DOI")
print(f"  3. Update RFC-ATF-6.md references with {doi}")
print(f"  4. Share on LinkedIn")
