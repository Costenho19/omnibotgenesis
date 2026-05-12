# OMNIX ATF — Internal Claims Audit
## OMNIX-AUDIT-ATF-2026-001

**Classification:** INTERNAL — NOT FOR PUBLIC DISTRIBUTION  
**Date:** May 12, 2026  
**Author:** OMNIX QUANTUM — Strategic Technical Review  
**Purpose:** Separate defensible novel claims from standard/known approaches and
identify language requiring care in public communication.

---

## Executive Summary

The ATF protocol occupies a genuinely valuable and defensible position in a
real gap: **AI agent authority governance before execution**. No publicly
available, formally specified, reference-implemented system provides the
combination OMNIX ATF provides.

However, several public claims are currently phrased with more certainty than
the technical facts support. Fixing these does not weaken OMNIX's position —
it makes the position more credible to the institutional audience OMNIX targets
(legal, regulatory, enterprise security). Overreach in public claims is the
single biggest risk to institutional credibility.

**Core defensible position (word it exactly like this):**

> OMNIX ATF is the only publicly available, reference-implemented,
> formally specified protocol that cryptographically links the authorization
> chain, authority bound, temporal admissibility, and governance decision
> into a single independently verifiable audit artifact — using post-quantum
> cryptography (ML-DSA-65, FIPS 204).

---

## Audit Framework

| Color | Meaning |
|---|---|
| 🟢 GREEN | Clearly novel, defensible, supported by technical evidence |
| 🟡 YELLOW | Valid claim, but public language needs qualification |
| 🔴 RED | Overreach — remove or fundamentally rephrase for public use |

---

## 🟢 GREEN — Genuinely Novel, Defensible Claims

These can be stated with confidence in public, investor, and regulatory contexts.

### G-001: Monotonic Authority Reduction as a Formally Specified AI Delegation Invariant

**Claim:** ATF defines and formally specifies MAR — the invariant that authority
budget can only decrease through a delegation chain — as a system requirement
for AI agent delegation.

**Why it's real:** No published AI agent framework (LangChain, AutoGen, CrewAI,
Semantic Kernel, Google ADK, Amazon Bedrock Agents) specifies a monotonic
authority bound at all, let alone as a formal invariant. Classical RBAC/ABAC
systems have scopes, but not monotonic budget arithmetic with chain-level proofs.

**Safe public language:**
> "ATF defines Monotonic Authority Reduction (MAR) — a formally specified
> invariant requiring that authority budget can only decrease through any
> delegation chain — as a structural requirement for AI agent governance.
> This invariant is machine-checked using TLA+."

---

### G-002: Pre-Execution Temporal Admissibility Record (TAR)

**Claim:** ATF issues a cryptographically signed record (TAR) BEFORE the
governance pipeline executes, binding the exact delegation state at the moment
of execution.

**Why it's real:** JWT has an `exp` claim, but it is checked — not committed
cryptographically as a separate signed artifact that survives the execution.
OAuth tokens verify at point of use. None produces a signed, independently
verifiable "snapshot of authority at execution time" as a separate persistent artifact.

**Safe public language:**
> "ATF issues a Temporal Admissibility Record (TAR) at the moment of execution
> admission — before any governance logic runs — creating a signed, persistent
> record of the delegation's state at that exact moment."

---

### G-003: Three-Artifact Governance Chain (DR + TAR + GovernanceReceipt)

**Claim:** The combination of DelegationReceipt + TemporalAdmissibilityRecord
+ GovernanceReceipt as a single, cross-referenced, independently verifiable
audit artifact chain is novel for AI governance systems.

**Why it's real:** Each artifact exists elsewhere in isolation. Combining them
into a mandatory, cross-referenced chain for every AI governance decision — with
PQC signatures and CLI verifiability — is the novel contribution.

**Safe public language:**
> "Every OMNIX governance decision produces three cryptographically linked
> artifacts: a Delegation Receipt (who authorized the agent), a Temporal
> Admissibility Record (authority confirmed at execution time), and a
> Governance Receipt (the decision itself) — all independently verifiable."

---

### G-004: ATF Chain Completeness Score (CCS)

**Claim:** A [0-100] quantitative metric for the cryptographic completeness
of an agent's delegation chain.

**Why it's real:** No prior system defines a quantitative completeness score
for AI agent delegation chains. The concept is genuinely novel in this context.

**Safe public language:**
> "ATF Chain Completeness Score quantifies the cryptographic integrity of an
> agent's delegation chain on a [0-100] scale, enabling at-a-glance auditability."

---

### G-005: Cross-Domain Authority Discount (DTR)

**Claim:** ATF defines a cross-domain trust portability protocol that mandates
authority reduction at every domain crossing, with domain-pair-specific policies.

**Why it's real:** Cross-domain trust translation with mandatory reduction is
a genuinely new policy mechanism. SAML federation handles identity portability,
not authority budget reduction.

**Safe public language:**
> "ATF's Cross-Domain Trust Portability defines mandatory authority discount
> policies for every domain crossing — FINANCE→HEALTHCARE carries a 30%
> reduction — preserving governance integrity across organizational boundaries."

---

### G-006: Independent Offline Verifiability as a Design Requirement (ATF-INV-006)

**Claim:** ATF explicitly specifies that any party MUST be able to verify the
full delegation chain with no access to the OMNIX platform, using only the
receipt artifacts and a known public key.

**Why it's real:** Most governance platforms require an API call to verify
anything. Making offline verifiability a specified protocol invariant — not just
a feature — is structurally important for regulators who can't trust the platform.

**Safe public language:**
> "ATF Invariant 6 (ATF-INV-006): Any regulator, auditor, or counterparty
> can verify the complete governance chain using only the receipt documents
> and the root public key. No API call, no account, no platform access required."

---

## 🟡 YELLOW — Valid Claims Requiring Qualified Language

These claims are technically supported but the current phrasing could be
challenged in academic peer review or legal adversarial contexts.

### Y-001: "First formally specified protocol" — the "first" claim

**Current public language:**
> "ATF provides the first formally specified and independently verifiable protocol..."

**The risk:** "First" claims require exhaustive literature review. An adversarial
reviewer will immediately ask: "Did you search all IETF drafts? ACM DL? IEEE
Xplore? USENIX papers?" If you haven't done an exhaustive search, you can't say "first."

**Adjusted language:**
> "ATF is the first publicly available, reference-implemented protocol that provides
> all four properties: PQC-signed delegation chain, formally proven monotonic authority
> bound, pre-execution temporal admissibility record, and independent offline verification.
> To the best of our knowledge based on review of published AI agent frameworks and
> cryptographic protocol specifications, no prior system provides this combination."

**Why this is still very strong:** You moved from a falsifiable absolute claim
to a conditional claim with scope. It's actually *harder* to challenge.

---

### Y-002: "TLA+ proven" vs "model-checked under assumptions"

**Current language:**
> "All invariants are formally specified and proven using TLA+ model checking."

**The risk:** TLA+ model checking proves properties for bounded state spaces
under the model's assumptions. It is not a mathematical proof in the theorem-prover
sense (Coq, Lean, Isabelle). Academic reviewers will distinguish between
"verified by model checking" and "proven formally."

**Adjusted language:**
> "ATF invariants are formally specified in TLA+ and verified by model checking
> for bounded state spaces. The specification uses the same methodology as Amazon
> DynamoDB's formal verification."

**Why the AWS comparison matters:** It immediately signals methodology credibility
to engineers and academics without overclaiming proof-theoretic completeness.

---

### Y-003: "128-bit post-quantum security" and "FIPS 204 compliance"

**Current language:**
> "The protocol uses ML-DSA-65 (Dilithium-3, FIPS 204) for 128-bit post-quantum security."

**The risk:** Two issues:
1. The OMNIX implementation uses a Python library (`pqc`), which is NOT NIST-validated
   software. FIPS 204 is the algorithm standard; FIPS compliance requires NIST-validated
   implementation. These are different things.
2. "128-bit post-quantum security" is the claimed security level of ML-DSA-65, but
   this is a design target, not a formally verified security reduction.

**Adjusted language:**
> "ATF uses the ML-DSA-65 algorithm (as specified in NIST FIPS 204, post-quantum
> cryptography standard) for digital signatures. This provides Dilithium-3
> security parameters targeting NIST security Level 3."

**Internal note:** If OMNIX ever goes through actual FIPS 140-3 validation or
uses a validated HSM, the stronger claim becomes available.

---

### Y-004: "Nanosecond-precise" temporal claim

**Current language:**
> "nanosecond-precise TAR" / "nanosecond-precise admission timestamp"

**The risk:** `time.time_ns()` provides nanosecond *resolution*, not nanosecond
*precision*. OS scheduling jitter means the actual precision is typically
microseconds to low milliseconds in a containerized environment. A metrologist
or systems engineer will immediately flag this.

**Adjusted language:**
> "TAR captures a nanosecond-resolution timestamp at the moment of admission
> using the system's monotonic clock (`time.time_ns()`), providing sub-millisecond
> temporal granularity for governance audit records."

**Why it still matters:** Sub-millisecond granularity is genuinely useful for
audit ordering. You don't need nanosecond precision to make the temporal claim
meaningful. "Nanosecond-resolution" is accurate; "nanosecond-precise" is not.

---

### Y-005: Comparison with LangChain, AutoGen, etc.

**Current language in Priority Record:**
> "Prior art search: no prior system [LangChain, AutoGen, etc.] produces a
> cryptographic proof binding a delegation receipt..."

**The risk:** LangChain, AutoGen, etc. don't *claim* to solve this problem.
Comparing OMNIX ATF with them is like comparing a contract law system with
a word processor. The comparison is technically correct but strategically
weak — it could read as attacking strawmen.

**Better framing:**
> "Existing AI agent orchestration frameworks (LangChain, AutoGen, CrewAI,
> Semantic Kernel) focus on agent execution and tool use, not on cryptographic
> governance of the authority chain before execution. ATF addresses the
> governance gap that precedes these frameworks' operation."

**This is stronger** because it positions ATF as complementary infrastructure,
not as a competitor that does the same thing better.

---

### Y-006: "Cryptographically proves" vs "cryptographically records"

**Current hero phrase:**
> "OMNIX prueba criptográficamente quién autorizó a cada agente..."

**The nuance:** A PQC signature proves that a specific key signed a specific
document. It proves that *someone with the corresponding private key* created
that receipt. It does NOT prove that the person who holds that key actually
authorized the action in a legal sense.

**Is this a problem?** For the public hero phrase — no. It's acceptable marketing
language that is directionally accurate. The signature is the cryptographic evidence
of authorization.

**Where it matters:** In legal proceedings or regulatory submissions, say:
> "The Delegation Receipt provides cryptographic evidence of authorization,
> as it bears the digital signature of the principal's key under ML-DSA-65.
> The key custody and identity binding to the named principal is the
> responsibility of the deploying organization's key management infrastructure."

**The hero phrase is fine as marketing language.** Just have the legal nuance
available for enterprise conversations.

---

### Y-007: "Prior art — no prior published work"

**Current language in Priority Record:**
> "To the best of my knowledge, no prior published work provides all four
> cryptographic proofs..."

**This is the right phrasing.** Keep it exactly as is. The qualifier
"to the best of my knowledge" is the correct legal and academic hedge.
The claim is still strong.

**Recommendation:** Before Zenodo/arXiv submission, do a targeted search:
- arXiv cs.CR: "agent delegation" + "formal verification"
- ACM DL: "AI agent authority" + "cryptographic"
- IETF drafts: agent identity, AI governance
- NIST: AI governance frameworks
- IEEE: agent trust management

Even if you find related work, OMNIX's combination remains distinctive.

---

## 🔴 RED — Overreach — Remove or Fundamentally Rephrase

### R-001: "Proven" without qualifier in formal context

**Found in:** RFC-ATF-1 and ATF-FORMAL-VERIFICATION.md  
**Pattern:** "proven property" / "proven invariant"

**The problem:** In formal methods, "proven" means theorem-prover proof
(Coq, Lean, Isabelle). TLA+ model checking is "verified" or "model-checked",
not "proven" in the formal sense.

**Action:** Replace "proven" → "model-checked" or "verified by model checking"
in all formal specification documents. Keep "proven" only in marketing language
where the distinction is contextually understood.

---

### R-002: Implicit claim that OMNIX ATF is production-security-ready for critical infrastructure without qualification

**Context:** The `/atf-standard` page and RFC-ATF-1 position ATF for
defense, healthcare, finance — critical infrastructure domains.

**The risk:** The Python `pqc` library used for Dilithium-3 has a patent
warning in its own code. It is explicitly NOT for production use without
independent legal review. This creates a gap between the protocol specification
(which is sound) and the current reference implementation (which has a patent
caveat).

**Action needed:** Add a disclaimer to RFC-ATF-1 implementation notes:
> "The ATF reference implementation uses the `pqc` Python library for ML-DSA-65
> signatures. Deployments in regulated environments should evaluate whether
> a FIPS 140-3 validated cryptographic library is required for their compliance
> context. The protocol specification is library-agnostic."

This is a minor but important gap for institutional credibility.

---

### R-003: Implied exhaustive prior art search

**Current language:**
> "Prior art search: no prior system produces..."

**The risk:** "Prior art search" implies a thorough search was conducted.
If challenged by an academic or patent attorney, "we searched" needs to be
substantiated.

**Action:** Either:
(a) Do the actual search (arXiv, ACM DL, IEEE, IETF) and document it, or
(b) Change language to "To the best of our knowledge, based on review of
publicly available AI agent frameworks and relevant IETF/W3C specifications..."

---

## Summary Table

| ID | Claim | Status | Action |
|---|---|---|---|
| G-001 | MAR as AI delegation invariant | 🟢 | State confidently |
| G-002 | Pre-execution TAR before governance runs | 🟢 | State confidently |
| G-003 | DR+TAR+Receipt triple chain | 🟢 | State confidently |
| G-004 | ATF Chain Completeness Score | 🟢 | State confidently |
| G-005 | Cross-domain authority discount | 🟢 | State confidently |
| G-006 | Offline verifiability as protocol invariant | 🟢 | State confidently |
| Y-001 | "First formally specified protocol" | 🟡 | Qualify + bound scope |
| Y-002 | "TLA+ proven" | 🟡 | → "model-checked" |
| Y-003 | "FIPS 204 compliance" / "128-bit" | 🟡 | → "ML-DSA-65 algorithm per FIPS 204" |
| Y-004 | "Nanosecond-precise" | 🟡 | → "nanosecond-resolution" |
| Y-005 | Comparison with LangChain etc. | 🟡 | Reframe as complementary |
| Y-006 | "Cryptographically proves" in hero phrase | 🟡 | Fine for marketing, qualify for legal |
| Y-007 | "To the best of my knowledge" hedge | 🟢 | Keep exactly as is |
| R-001 | "Proven" in formal spec context | 🔴 | → "model-checked" in specs |
| R-002 | Production-ready without PQC library caveat | 🔴 | Add implementation disclaimer |
| R-003 | Implied exhaustive prior art search | 🔴 | Qualify or conduct search |

---

## Recommended Public Positioning Statement

This is the language that will hold up in front of:
- Enterprise legal counsel
- CISO and compliance officers
- Academic peer reviewers
- Regulators (EU AI Act, financial regulators)
- Patent attorneys

> **OMNIX ATF (RFC-ATF-1)** is a formally specified, reference-implemented
> open protocol for post-quantum cryptographic governance of AI agent authority
> before execution.
>
> ATF addresses the question that existing AI governance frameworks leave open:
> *"When an AI agent executes, was the authorization chain complete, was the
> authority bound respected, and was the agent validly admitted at that
> exact moment?"*
>
> Key properties, each independently verifiable:
>
> 1. **Authorization chain** — ML-DSA-65 (NIST FIPS 204 algorithm) signed
>    Delegation Receipts trace every agent to a Tier-1 human principal.
> 2. **Monotonic Authority Bound** — formally specified invariant, model-checked
>    in TLA+: authority can only decrease through delegation.
> 3. **Temporal Admissibility** — a signed record issued before governance
>    execution, capturing the delegation's state at admission.
> 4. **Decision linkage** — every governance decision embeds the complete
>    ATF context, creating an audit artifact that answers all four questions.
>
> To the best of our knowledge, no prior publicly available system provides
> all four properties in a single formally specified, reference-implemented protocol.

---

## Strategic Recommendation

OMNIX is entering the space of **AI agent authority governance before execution**.
This is a real gap, the timing is right (EU AI Act, DORA, emerging multi-agent AI
frameworks), and OMNIX's implementation is technically solid.

The premium position is not "we invented everything." The premium position is:

> "We are the only team that has formally specified, reference-implemented,
> and independently deployed this exact combination — and every governance
> decision we produce is verifiable without trusting us."

The last part — "without trusting us" — is what makes this institutional-grade.
It is the hardest property to achieve and the one most valuable to regulators.

**That** is OMNIX's genuine moat in this space.

---

## Recommended Next Actions

1. **Immediate:** Adjust "nanosecond-precise" → "nanosecond-resolution" in all public docs
2. **Immediate:** Adjust "proven" → "model-checked" in RFC-ATF-1 formal sections
3. **Immediate:** Add PQC library implementation disclaimer to RFC-ATF-1 §14
4. **Before Zenodo/arXiv submission:** Conduct targeted prior art search (2-4 hours)
5. **Before enterprise demos:** Prepare the "without trusting us" narrative with live
   CLI verifier demonstration
6. **Optional (strengthens position significantly):** Port the TLA+ spec to Coq/Lean
   for one invariant (MAR). This converts "model-checked" → "formally proven" for that claim.

---

**Document ID:** OMNIX-AUDIT-ATF-2026-001  
**Date:** May 12, 2026  
**Classification:** INTERNAL
