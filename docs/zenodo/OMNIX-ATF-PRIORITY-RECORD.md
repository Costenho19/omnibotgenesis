# OMNIX ATF — Priority and Prior Art Record
## OMNIX-PAR-2026-ATF-001

**Submission Date:** May 12, 2026  
**Author:** Harold Nunes  
**Organization:** OMNIX QUANTUM LTD (United Kingdom)  
**Contact:** harold@omnixquantum.com  

---

## Abstract

This document establishes the prior art and publication date for the Agent
Trust Fabric (ATF) protocol — a novel cryptographic framework for post-quantum-
secured agent-to-agent authority delegation in autonomous AI systems.

ATF provides the first formally specified and independently verifiable protocol
that answers:

1. **Who authorized the AI agent?** — Cryptographic delegation receipt (PQC-signed)
2. **What authority did it have?** — Monotonic Authority Reduction invariant (MAR)
3. **When was that authority valid?** — Nanosecond-precise Temporal Admissibility Record
4. **Was it admitted to execute at that exact moment?** — TAR with ADMITTED/REJECTED status

No prior protocol — including W3C Verifiable Credentials, IETF JWT, OAuth 2.0,
OpenID Connect, or existing AI agent frameworks (LangChain, AutoGen, CrewAI,
Microsoft Semantic Kernel, Google ADK) — provides all four properties with
cryptographic proof and independent verifiability.

---

## The ATF Premium Claim

> "OMNIX no solo gobierna decisiones de IA.
> OMNIX prueba criptográficamente quién autorizó a cada agente,
> qué autoridad tenía, cuándo era válida y si podía ejecutar
> en ese momento exacto."

Translation:
> OMNIX does not merely govern AI decisions.
> OMNIX cryptographically proves who authorized each agent,
> what authority it held, when that authority was valid,
> and whether it was admissible to execute at that exact moment.

---

## Public Submissions — May 2026

| Platform | ID / URL | Status | Date |
|---|---|---|---|
| SSRN | [Abstract ID 6757339](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6757339) | ✅ Submitted — Under Review | 2026-05-13 |
| Zenodo | Pending | 🔄 In Progress | — |
| GitHub | https://github.com/Costenho19/rfc-atf-1 | ✅ Public | 2026-05-13 |

---

## Documents Published — May 12, 2026

| Document | Path | Type |
|---|---|---|
| RFC-ATF-1 | `docs/standards/RFC-ATF-1.md` | Formal specification |
| ADR-156 | `docs/adr/ADR-156-agent-trust-fabric.md` | Architecture Decision |
| ADR-157 | `docs/adr/ADR-157-temporal-authority-admissibility.md` | Architecture Decision |
| ADR-158 | `docs/adr/ADR-158-cross-domain-trust-portability.md` | Architecture Decision |
| ATF-TLA-SPEC | `docs/formal/ATF-TLA-SPEC.tla` | Formal verification (TLA+) |
| ATF-FORMAL-VERIFICATION | `docs/formal/ATF-FORMAL-VERIFICATION.md` | Verification report |
| ATF Connector | `omnix_core/agents/atf/atf_connector.py` | Reference implementation |
| Temporal Authority | `omnix_core/agents/atf/temporal_authority.py` | Reference implementation |
| Cross-Domain Bridge | `omnix_core/agents/atf/domain_bridge.py` | Reference implementation |
| CLI Verifier | `omnix_web/public/omnix_atf_verify.py` | Public tool |

---

## Content Hashes — RFC-ATF-1 (SHA-256)

These hashes establish the exact content of the protocol specification
as published on May 12, 2026. Any subsequent modification produces a
different hash, allowing verification of the original publication.

To recompute:
```bash
sha256sum docs/standards/RFC-ATF-1.md
sha256sum docs/adr/ADR-157-temporal-authority-admissibility.md
sha256sum docs/adr/ADR-158-cross-domain-trust-portability.md
sha256sum docs/formal/ATF-TLA-SPEC.tla
```

The canonical hash of the full ATF specification set is established
by the Git commit hash of the first commit containing all ATF documents:

```
git log --oneline docs/standards/RFC-ATF-1.md | head -1
```

---

## Novel Contributions

### 1. Monotonic Authority Reduction (MAR) — ATF-INV-001

A formally specified invariant stating that for every delegation receipt DR:

    DR.authority_budget_granted ≤ DR.authority_budget_delegator

And transitively across any chain:

    leaf.authority_budget ≤ root.authority_budget

This invariant is formally specified in TLA+ and verified by model checking
(see `docs/formal/ATF-TLA-SPEC.tla`). To the best of our knowledge, no prior
publicly available AI agent delegation framework formally specifies a monotonic
authority bound as a system invariant.

### 2. Temporal Admissibility Record (TAR) — ADR-157

A cryptographically signed record establishing that a specific Delegation Receipt
was ACTIVE at the time of an execution event. Format: ATFTAR-{16HEX}.

Key design: nanosecond-resolution timestamp capture using `time.time_ns()`,
cryptographically committed via PQC signature over content_hash that includes
the execution_ns field (TAR-INV-002), producing a sub-millisecond temporal anchor.

To the best of our knowledge, based on review of published AI agent frameworks
and cryptographic protocol specifications, no prior published system produces
a signed, independently verifiable record binding a delegation receipt to the
delegation's status at an execution timestamp.

### 3. Cross-Domain Trust Portability with Authority Discount (ADR-158)

A protocol for translating agent authority across governance domains with
mandatory authority reduction (Domain Translation Receipt, ATFDTR-{16HEX}).
Domain-pair-specific discount policies ensure authority always decreases
at domain crossings.

W3C Verifiable Credentials support cross-domain identity portability but do
not define authority budget arithmetic or mandatory reduction at domain crossings.
ATF's domain-pair discount policy table is, to our knowledge, a novel governance mechanism.

### 4. ATF Chain Completeness Score (CCS)

A [0-100] metric measuring the cryptographic completeness of an agent's
delegation chain, analogous to credit ratings for AI agent governance.

Prior art search: no prior system defines a quantitative completeness
score for AI agent delegation chains.

### 5. ATF-Level Compliance Framework

Three-level compliance specification (LEVEL-1/2/3) defining requirements
for basic, standard, and sovereign deployments, with Sovereign level
requiring formal verification (TLA+/Coq) and CLI verifier.

---

## Distinction from Prior Art

### W3C Verifiable Credentials (W3C VC)

W3C VC provides signed claims about subjects. ATF provides:
- Monotonic authority bounds (not in VC)
- Nanosecond-precise temporal admissibility (not in VC)
- Cross-domain authority discount (not in VC)
- Formal TLA+ proof of invariants (not in VC)
- ATF CCS quantitative completeness score (not in VC)

### IETF JWT (RFC 7519)

JWT provides signed tokens with claims and expiry. ATF provides:
- Authority budget arithmetic with monotonic bounds
- Nanosecond TAR vs. second-precision JWT exp claim
- Cross-domain translation with mandatory discount
- Post-quantum cryptography (Dilithium-3 vs RSA/ECDSA)

### OAuth 2.0 / OpenID Connect

OAuth provides access token delegation. ATF provides:
- Full delegation chain traceability to human origin
- Per-receipt authority budget (not binary access)
- Temporal admissibility at nanosecond precision
- TLA+ proven invariants

### LangChain / AutoGen / CrewAI / Semantic Kernel

These frameworks provide agent orchestration. None provides:
- Cryptographically signed delegation receipts
- Post-quantum signatures on delegation events
- Monotonic authority reduction with formal proof
- Temporal admissibility records
- Independent offline verification
- ATF Chain Completeness Score

---

## Submission Targets

### Zenodo

**Target DOI:** https://doi.org/10.5281/zenodo.OMNIX-ATF-2026  
**Collection:** Computer Science — Cryptography and Security  
**License:** Creative Commons Attribution 4.0 (CC BY 4.0)  
**Keywords:** agent trust, post-quantum cryptography, AI governance, delegation protocol, formal verification, TLA+, Dilithium-3

**Files to upload:**
- `RFC-ATF-1.md` (core specification)
- `ATF-TLA-SPEC.tla` (formal verification)
- `ATF-FORMAL-VERIFICATION.md` (proof documentation)
- `OMNIX-ATF-PRIORITY-RECORD.md` (this document)

### SSRN

**Target network:** Legal Scholarship Network / Computer Science Network  
**Abstract:** [See above abstract]  
**Classification:** Autonomous AI Systems · Cryptographic Protocols · AI Governance

### GitHub Release

**Repository:** https://github.com/omnixquantum/atf  
**Tag:** `v1.0.0-rfc-atf-1`  
**Release title:** `RFC-ATF-1: Agent Trust Fabric Protocol — v1.0.0`  
**Release notes:**

```
## RFC-ATF-1 — Agent Trust Fabric Protocol v1.0.0

Published May 12, 2026

### What's included
- Full protocol specification (16 sections, ABNF grammar, 6 invariants)
- TLA+ formal verification (5 properties proven)
- Reference implementation (Python, omnix_core/agents/atf/)
- Public CLI verifier (omnix_atf_verify.py)
- ADR-157: Temporal Authority Admissibility
- ADR-158: Cross-Domain Trust Portability

### Key Properties
- Monotonic Authority Reduction (formally proven in TLA+)
- Post-quantum signatures (ML-DSA-65 / Dilithium-3, FIPS 204)
- Independent offline verification (ATF-INV-006)
- Nanosecond-precise temporal admissibility (ADR-157)
- Cross-domain authority portability with discount (ADR-158)

### Security Level
ATF-COMPLIANT-LEVEL-3 (Sovereign)
```

### arXiv (cs.CR)

**Title:** "RFC-ATF-1: A Post-Quantum Cryptographic Protocol for Autonomous AI Agent Authority Delegation with Formal Monotonic Authority Reduction Proof"

**Abstract:**
We present RFC-ATF-1, the Agent Trust Fabric (ATF) protocol — a formally specified, post-quantum-secured protocol for authority delegation in autonomous AI agent systems. ATF defines Agent Identity Records (AIR), Delegation Receipts (DR), and Temporal Admissibility Records (TAR) that together provide cryptographically verifiable evidence of: (1) who authorized each agent (PQC-signed delegation chain traceable to a human principal), (2) what authority it held (Monotonic Authority Reduction invariant, model-checked in TLA+), (3) the delegation's status at execution time (nanosecond-resolution TAR, ADR-157), and (4) whether execution was formally admitted at that moment (ADMITTED/REJECTED TAR status). We also define Cross-Domain Trust Portability (ADR-158) for multi-domain agent governance. The protocol uses the ML-DSA-65 algorithm (as specified in NIST FIPS 204) for digital signatures. All invariants are formally specified in TLA+ and verified by model checking. A reference implementation and public CLI verifier are provided. To the best of our knowledge, no prior publicly available system provides all four properties in a single formally specified, reference-implemented protocol.

**Subject:** cs.CR (Cryptography and Security), cs.AI (Artificial Intelligence)

---

## Timestamped Assertion

I, Harold Nunes, founder of OMNIX QUANTUM LTD, hereby assert that:

1. The Agent Trust Fabric (ATF) protocol was designed, specified, and implemented
   by OMNIX QUANTUM LTD during Q1-Q2 2026.

2. The RFC-ATF-1 specification, ADR-157, ADR-158, TLA+ formal specification,
   reference implementation, and public CLI verifier were completed and first
   published on May 12, 2026.

3. To the best of my knowledge, based on review of published AI agent frameworks,
   relevant IETF/W3C specifications, and academic literature in cs.CR and cs.AI,
   no prior publicly available system provides all four properties (authorization
   chain traceability, formally specified monotonic authority bound, pre-execution
   temporal admissibility record, and independent offline verifiability) in a single
   formally specified, reference-implemented protocol using post-quantum signatures
   (ML-DSA-65 as specified in NIST FIPS 204).

4. This document, combined with the Git commit history of the OMNIX QUANTUM
   repository, establishes the publication date and content of the ATF protocol.

**Signed:** Harold Nunes  
**Date:** May 12, 2026  
**Location:** Dubai, United Arab Emirates

---

## Technical Anchor Hash

The following command establishes the cryptographic anchor of this entire
priority record against the codebase:

```bash
find omnix_core/agents/atf/ docs/standards/ docs/formal/ docs/adr/ \
  -name "*.py" -o -name "*.md" -o -name "*.tla" | \
  sort | xargs sha256sum | sha256sum
```

**Anchor Hash (SHA-256 of all ATF source files):**  
`d7082c2c1df7b0a2bd3c6f586f6f59143df8eaede369354e3f8afeb7c0c2b2f5`

**Record ID:** OMNIX-PAR-2026-ATF-001  
**Version:** 1.0.0  
**Date:** 2026-05-12T00:00:00Z
