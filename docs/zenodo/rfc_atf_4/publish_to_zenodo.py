"""
OMNIX QUANTUM — RFC-ATF-4 Zenodo Publisher
Run: python docs/zenodo/rfc_atf_4/publish_to_zenodo.py

Requires: ZENODO_TOKEN environment variable
  export ZENODO_TOKEN=your_personal_access_token
"""

import os, json, sys, requests
from pathlib import Path

TOKEN = os.environ.get('ZENODO_TOKEN')
if not TOKEN:
    print("ERROR: Set ZENODO_TOKEN environment variable")
    sys.exit(1)

BASE    = "https://zenodo.org/api"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
DIR     = Path(__file__).parent

# ── Load metadata ─────────────────────────────────────────────────────────────
with open(DIR / "metadata.json") as f:
    META = json.load(f)

FILES_TO_UPLOAD = [
    DIR / "RFC-ATF-4.pdf",
    DIR / "proof_report.json",
    DIR / "conformance_vectors.json",
]

def check(r, step):
    if not r.ok:
        print(f"FAILED at {step}: {r.status_code} — {r.text[:500]}")
        sys.exit(1)
    print(f"  OK [{r.status_code}] {step}")
    return r.json()

print("\n=== RFC-ATF-4 Zenodo Publication ===\n")

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
    if not fpath.exists():
        print(f"   SKIP (not found): {fpath.name}")
        continue
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

print(f"\n{'='*50}")
print(f"  PUBLISHED SUCCESSFULLY")
print(f"  DOI: {doi}")
print(f"  URL: {url}")
print(f"{'='*50}")
print(f"\nNext steps:")
print(f"  1. Update RFC-ATF-4.md line 4: replace [PENDING] with {doi}")
print(f"  2. Update replit.md RFC table with the new DOI")
print(f"  3. Share on LinkedIn")
