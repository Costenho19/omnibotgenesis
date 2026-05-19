# OMNIX QUANTUM — RFC Publication Release Manifest

**Author:** Harold Nunes · OMNIX QUANTUM LTD · Dubai, UAE  
**Document ID:** OMNIX-RELEASE-MANIFEST-2026-05  
**Purpose:** Cryptographically anchors each RFC-ATF publication to its exact git commit and document SHA-256, enabling independent verification of the canonical release artifact.

This manifest applies OMNIX's own governance principles — immutable receipts, auditable chains, explicit provenance — to its own RFC publication process.

---

## RFC-ATF-1 · v1.0.0

| Field | Value |
|---|---|
| **Title** | Agent Trust Fabric — Post-Quantum Cryptographic Protocol for AI Agent Authority Governance |
| **Version** | 1.0.0 |
| **Published** | May 2026 |
| **Git Tag** | `v1.0.0-rfc-atf-1` |
| **Git Commit** | `54e3988dfd11c8ab2bc9f625c1ac8d03e5dc6b21` |
| **Document SHA-256** | `978f946ab066600efb8b20ab82bb1f8609af0cc70fe96cd0e98ac23dd5dad495` |
| **Zenodo DOI** | https://doi.org/10.5281/zenodo.20155016 |
| **Figshare DOI** | https://doi.org/10.6084/m9.figshare.32308077 |
| **File** | `docs/standards/RFC-ATF-1.md` |

---

## RFC-ATF-2 · v1.0.0

| Field | Value |
|---|---|
| **Title** | Agent Trust Fabric — Runtime Continuity Governance: CES, AFG, and Reauthorization Challenge Protocol |
| **Version** | 1.0.0 |
| **Published** | May 2026 |
| **Git Tag** | `v1.0.0-rfc-atf-2` |
| **Git Commit** | `5acbfbc0f801d0211a84726d05edb16cb0ae15e1` |
| **Document SHA-256** | `e54820be86c1a33da8c141d419ecb5096ebb9086580e66d6ff02dbcc50331ab8` |
| **Zenodo DOI** | https://doi.org/10.5281/zenodo.20241344 |
| **Figshare DOI** | https://doi.org/10.6084/m9.figshare.32308095 |
| **File** | `docs/standards/RFC-ATF-2.md` |

---

## RFC-ATF-3 · v1.0.0

| Field | Value |
|---|---|
| **Title** | Agent Trust Fabric — Governance Policy Interoperability, Evidence Lifecycle, and Forensic Verification Protocol |
| **Version** | 1.0.0 |
| **Published** | May 2026 |
| **Git Tag** | `v1.0.0-rfc-atf-3` |
| **Git Commit** | `5acbfbc0f801d0211a84726d05edb16cb0ae15e1` |
| **Document SHA-256** | `ccd4108f8dd58c729b550a719909330fe8fbd27a044d55e97d078e0429b43415` |
| **Zenodo DOI** | https://doi.org/10.5281/zenodo.20247342 |
| **Figshare DOI** | https://doi.org/10.6084/m9.figshare.32308119 |
| **File** | `docs/standards/RFC-ATF-3.md` |

---

## Verification Instructions

Any reviewer can independently verify a release artifact:

```bash
# 1. Clone the repository
git clone https://github.com/omnixquantum/omnix-quantum.git
cd omnix-quantum

# 2. Checkout the exact release commit
git checkout v1.0.0-rfc-atf-3

# 3. Verify document SHA-256
sha256sum docs/standards/RFC-ATF-3.md
# Expected: ccd4108f8dd58c729b550a719909330fe8fbd27a044d55e97d078e0429b43415

# 4. Compare against Zenodo artifact
# Download from https://doi.org/10.5281/zenodo.20247342 and sha256sum both files
```

---

## Manifest Integrity

This manifest is included in the repository at commit `5acbfbc0f801d0211a84726d05edb16cb0ae15e1` and is itself part of the auditable record. Any modification to this file after the tagged release would be detectable via git history.

**OMNIX QUANTUM LTD** · omnixquantum.net · May 2026
