# OMNIX ATF — Public Submission Guide
## Step-by-Step for: Zenodo · arXiv · SSRN · GitHub Tagged Release

**Document:** OMNIX-SUB-ATF-2026-001  
**Date:** May 2026  
**Purpose:** Actionable submission checklist for establishing immutable public priority

---

## Overview — What You're Establishing

Each platform creates a different form of immutability:

| Platform | What it creates | Time to index |
|---|---|---|
| Zenodo | DOI (permanent URL, version-controlled) | Minutes |
| arXiv | Preprint with searchable abstract (cs.CR) | 24-48h |
| SSRN | Social science / legal / institutional reach | Hours |
| GitHub Release | Tagged commit with release notes | Immediate |
| git commit hash | Cryptographic anchor of exact content | Immediate |

**Do them in this order:** GitHub → Zenodo → SSRN → arXiv
(GitHub and Zenodo can link to each other; arXiv abstract can cite the DOI)

---

## STEP 1 — GitHub Tagged Release (15 minutes)

This creates the immutable content anchor that all other submissions point to.

### 1.1 Create the tag

```bash
cd /path/to/omnix-repo
git tag -a v1.0.0-rfc-atf-1 -m "RFC-ATF-1: Agent Trust Fabric Protocol v1.0.0 — May 2026"
git push origin v1.0.0-rfc-atf-1
```

### 1.2 Create the GitHub Release

Go to: `https://github.com/omnixquantum/OMNIX/releases/new`

**Tag:** `v1.0.0-rfc-atf-1`  
**Title:** `RFC-ATF-1: Agent Trust Fabric Protocol — v1.0.0`  
**Mark as:** "Latest release"

**Release body** (copy exactly):

```markdown
## RFC-ATF-1 — Agent Trust Fabric Protocol v1.0.0

Published May 12, 2026 · OMNIX QUANTUM LTD · Harold Nunes, Dubai UAE

### What This Release Establishes

RFC-ATF-1 is a formally specified, post-quantum cryptographic protocol for
authority governance of autonomous AI agents before execution. It answers four
questions for every AI agent action:

1. Who authorized this agent? (ML-DSA-65 signed Delegation Receipt)
2. What authority did it hold? (Monotonic Authority Reduction, TLA+ model-checked)
3. Was the authority valid at execution? (Temporal Admissibility Record, ADR-157)
4. Is the chain independently verifiable? (Offline CLI, no platform access required)

### Documents in This Release

| File | Description |
|---|---|
| `docs/standards/RFC-ATF-1.md` | Full protocol specification (16 sections, ABNF, 6 invariants) |
| `docs/adr/ADR-157-temporal-authority-admissibility.md` | ADR-157: Temporal Admissibility |
| `docs/adr/ADR-158-cross-domain-trust-portability.md` | ADR-158: Cross-Domain Trust |
| `docs/formal/ATF-TLA-SPEC.tla` | TLA+ formal specification (5 properties) |
| `docs/formal/ATF-FORMAL-VERIFICATION.md` | Formal verification documentation |
| `docs/atf/OMNIX-ATF-WHITEPAPER.md` | Institutional whitepaper (~22pp) |
| `docs/atf/ATF-THREAT-MODEL.md` | Formal threat model (9 threat classes) |
| `docs/zenodo/OMNIX-ATF-PRIORITY-RECORD.md` | Priority and prior art record |
| `omnix_core/agents/atf/` | Reference implementation (Python) |
| `omnix_web/public/omnix_atf_verify.py` | Public CLI verifier (offline, no account needed) |

### Key Properties

- **ML-DSA-65** (Dilithium-3, NIST FIPS 204) post-quantum signatures
- **TLA+ model-checked** invariants (MAR, Acyclicity, Chain Consistency, Immutability)
- **Independent offline verification** — ATF-INV-006
- **Compliance:** ATF-COMPLIANT-LEVEL-1/2/3 framework

### Anchor Hash (SHA-256 of all ATF source files)

`d7082c2c1df7b0a2bd3c6f586f6f59143df8eaede369354e3f8afeb7c0c2b2f5`

To verify:
```bash
find omnix_core/agents/atf/ docs/standards/ docs/formal/ docs/adr/ \
  -name "*.py" -o -name "*.md" -o -name "*.tla" | \
  sort | xargs sha256sum | sha256sum
```

### Prior Art Claim

To the best of our knowledge, based on review of published AI agent frameworks
and relevant IETF/W3C specifications, no prior publicly available system provides
all four properties (authorization chain, monotonic authority bound, pre-execution
temporal admissibility record, independent offline verifiability) in a single
formally specified, reference-implemented protocol using post-quantum signatures.

### Citation

```bibtex
@misc{omnix-atf-2026,
  author    = {Harold Nunes},
  title     = {RFC-ATF-1: Agent Trust Fabric Delegation Protocol},
  year      = {2026},
  month     = {May},
  publisher = {OMNIX QUANTUM LTD},
  url       = {https://github.com/omnixquantum/OMNIX/releases/tag/v1.0.0-rfc-atf-1},
  note      = {Version 1.0.0}
}
```
```

### 1.3 Download the source ZIP from the GitHub release page

Save the URL: `https://github.com/omnixquantum/OMNIX/archive/refs/tags/v1.0.0-rfc-atf-1.zip`

---

## STEP 2 — Zenodo (20 minutes)

Zenodo assigns a permanent DOI (e.g., `10.5281/zenodo.XXXXXXX`).

### 2.1 Go to zenodo.org

- URL: https://zenodo.org/deposit/new
- Login with GitHub or create account

### 2.2 Upload files

Upload these files from the repo:

```
RFC-ATF-1.md                    (from docs/standards/)
ADR-157-temporal-authority-admissibility.md
ADR-158-cross-domain-trust-portability.md
ATF-TLA-SPEC.tla                (from docs/formal/)
ATF-FORMAL-VERIFICATION.md
OMNIX-ATF-WHITEPAPER.md         (from docs/atf/)
ATF-THREAT-MODEL.md             (from docs/atf/)
OMNIX-ATF-PRIORITY-RECORD.md   (from docs/zenodo/)
omnix_atf_verify.py             (from omnix_web/public/)
```

Or upload the GitHub source ZIP as a single archive.

### 2.3 Fill in the metadata

| Field | Value |
|---|---|
| **Upload type** | Software |
| **Basic information > Title** | RFC-ATF-1: Agent Trust Fabric Delegation Protocol — A Post-Quantum Cryptographic Framework for Autonomous AI Agent Authority Governance |
| **Authors** | Harold Nunes, OMNIX QUANTUM LTD, Dubai UAE |
| **Description** | [Copy the abstract from OMNIX-ATF-PRIORITY-RECORD.md §Abstract] |
| **License** | Creative Commons Attribution 4.0 (CC-BY-4.0) |
| **Version** | 1.0.0 |
| **Publication date** | 2026-05-12 |
| **Language** | English |
| **Access** | Open access |
| **Related identifiers** | GitHub release URL (isIdenticalTo) |

**Keywords** (add each separately):
```
agent trust fabric
AI agent governance
post-quantum cryptography
autonomous AI
delegation protocol
formal verification
TLA+
Dilithium-3
ML-DSA-65
authority delegation
AI accountability
EU AI Act
```

**Communities:** Search for "AI" or "cryptography" and add relevant Zenodo communities.

### 2.4 Click "Publish"

Save the DOI. It will look like: `https://doi.org/10.5281/zenodo.XXXXXXX`

Add the DOI to:
- `docs/zenodo/OMNIX-ATF-PRIORITY-RECORD.md` (replace "pending" in the Zenodo section)
- GitHub release description
- RFC-ATF-1.md header

---

## STEP 3 — SSRN (15 minutes)

SSRN reaches legal scholars, compliance professionals, and policy researchers.

### 3.1 Go to ssrn.com

- URL: https://www.ssrn.com/index.cfm/en/
- Create an account or log in
- Click: "Submit a Paper"

### 3.2 Choose network

Select: **"Computer Science Research Network (CSRN)"**  
Also add: **"Legal Scholarship Network"** (for regulatory reach)

### 3.3 Fill in metadata

| Field | Value |
|---|---|
| **Title** | RFC-ATF-1: A Post-Quantum Cryptographic Protocol for Autonomous AI Agent Authority Governance Before Execution |
| **Authors** | Harold Nunes (OMNIX QUANTUM LTD) |
| **Abstract** | [Use the arXiv abstract from OMNIX-ATF-PRIORITY-RECORD.md §arXiv] |
| **Classification** | K.6.5 Security and Protection; I.2.1 Artificial Intelligence — Applications |
| **JEL Codes** | G28 (Financial regulation), K29 (Law and economics — other) |
| **Keywords** | AI agent governance, post-quantum cryptography, delegation protocol, formal verification, EU AI Act, DORA, authority delegation |
| **Available date** | 2026-05-12 |

### 3.4 Upload PDF

Convert `docs/atf/OMNIX-ATF-WHITEPAPER.md` to PDF using pandoc:

```bash
pandoc docs/atf/OMNIX-ATF-WHITEPAPER.md \
  -o OMNIX-ATF-WHITEPAPER.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V fontsize=11pt
```

Or use any Markdown → PDF converter.

Upload the PDF as the paper.

---

## STEP 4 — arXiv (30-60 minutes)

arXiv is the primary preprint server for cs.CR (cryptography). Papers here are
indexed by Google Scholar, Semantic Scholar, and LLM training datasets.

### 4.1 Prepare the submission

You need a LaTeX or plain text abstract. Use this:

**Title:**
> RFC-ATF-1: A Post-Quantum Cryptographic Protocol for Autonomous AI Agent Authority Delegation with Formally Verified Monotonic Authority Reduction

**Authors:**
> Harold Nunes (OMNIX QUANTUM LTD)

**Abstract** (copy exactly from corrected version in Priority Record):
> We present RFC-ATF-1, the Agent Trust Fabric (ATF) protocol — a formally
> specified, post-quantum-secured protocol for authority delegation in autonomous
> AI agent systems. ATF defines Agent Identity Records (AIR), Delegation Receipts
> (DR), and Temporal Admissibility Records (TAR) that together provide
> cryptographically verifiable evidence of: (1) who authorized each agent
> (PQC-signed delegation chain traceable to a human principal), (2) what
> authority it held (Monotonic Authority Reduction invariant, model-checked in
> TLA+), (3) the delegation's status at execution time (nanosecond-resolution
> TAR, ADR-157), and (4) whether execution was formally admitted at that moment
> (ADMITTED/REJECTED TAR status). We also define Cross-Domain Trust Portability
> (ADR-158) for multi-domain agent governance. The protocol uses the ML-DSA-65
> algorithm (as specified in NIST FIPS 204) for digital signatures. All
> invariants are formally specified in TLA+ and verified by model checking.
> A reference implementation and public CLI verifier are provided. To the best
> of our knowledge, no prior publicly available system provides all four
> properties in a single formally specified, reference-implemented protocol.

**Primary category:** cs.CR (Cryptography and Security)  
**Cross-list:** cs.AI (Artificial Intelligence), cs.SE (Software Engineering)

### 4.2 Submit

- URL: https://arxiv.org/submit
- Upload: PDF of the whitepaper, or LaTeX source
- The submission goes through a 24-48h moderation queue
- You receive an arXiv ID (e.g., `arXiv:2026.XXXXX`)

### 4.3 After acceptance

Add the arXiv ID to:
- `docs/zenodo/OMNIX-ATF-PRIORITY-RECORD.md`
- GitHub release description
- RFC-ATF-1.md header

---

## STEP 5 — Update All Documents with Final IDs

After all submissions are live, update these fields:

```markdown
# In docs/zenodo/OMNIX-ATF-PRIORITY-RECORD.md

**Zenodo DOI:** https://doi.org/10.5281/zenodo.XXXXXXX
**arXiv:** https://arxiv.org/abs/2026.XXXXX
**SSRN:** https://ssrn.com/abstract=XXXXXXX
**GitHub:** https://github.com/omnixquantum/OMNIX/releases/tag/v1.0.0-rfc-atf-1
```

And in RFC-ATF-1.md header:

```
DOI: 10.5281/zenodo.XXXXXXX
arXiv: 2026.XXXXX
```

---

## Citation Block (Ready to Use)

Once all IDs are available, use this citation in any communication:

```bibtex
@misc{nunes2026atf,
  author       = {Harold Nunes},
  title        = {RFC-ATF-1: Agent Trust Fabric Delegation Protocol — A Post-Quantum Cryptographic Framework for Autonomous AI Agent Authority Governance},
  year         = {2026},
  month        = {May},
  publisher    = {OMNIX QUANTUM LTD},
  doi          = {10.5281/zenodo.XXXXXXX},
  url          = {https://arxiv.org/abs/2026.XXXXX},
  note         = {Version 1.0.0. ADR-156/157/158. TLA+ formal verification.}
}
```

---

## Timeline

| Day | Action |
|---|---|
| Day 0 (Today) | GitHub tag + release (immediate) |
| Day 0 | Zenodo upload + publish (minutes) |
| Day 0 | SSRN submission (same day, visible within hours) |
| Day 0-1 | arXiv submission (24-48h moderation) |
| Day 2 | Update all documents with final IDs |
| Day 2 | Announce on LinkedIn, X/Twitter with DOI link |

---

**Document ID:** OMNIX-SUB-ATF-2026-001  
**Version:** 1.0.0  
**Date:** May 12, 2026
