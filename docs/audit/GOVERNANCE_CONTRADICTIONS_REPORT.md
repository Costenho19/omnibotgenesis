# GOVERNANCE_CONTRADICTIONS_REPORT.md
## OMNIX QUANTUM — Governance Correctness & Contradictions Audit
**Date:** 2026-05-27 | **Method:** Invariant cross-reference + protocol trace

---

## EXECUTIVE SUMMARY

**4 confirmed governance contradictions** found. The most severe: BAR records are issued without PQC signatures, violating BEV-INV-015 (which requires PQC attestation of agent output). A stub DR can result in a TAR admission with `authority_budget_granted=0.0`, creating a governance receipt that claims authority enforcement while having zero budget to enforce.

---

## GOV-001 — BEV-INV-015 Violation: BAR Records Issued Without PQC Signature
- **Severity:** CRITICAL
- **Invariant Violated:** BEV-INV-015 (BAR must carry a valid PQC signature)
- **File:** `omnix_core/bev/behavioral_anchor_record.py:266`
- **Description:** BEV-INV-015 requires that every Behavioral Anchor Record (BAR) is PQC-signed with ML-DSA-65 before persistence. In practice, `PostQuantumSecurity.sign_receipt()` does not exist — the call fails and BAR records are stored with `pqc_signature = None`. This is a systematic invariant violation on every governance session.
- **State Created:** Governance sessions appear complete. BAR records exist in DB. CTCHC chain is valid. But the individual turn attestations lack signatures. An offline verifier checking BEV-INV-015 will reject every session.
- **Contradiction:** The system simultaneously: (a) issues PoGC certificates that claim "PQC-attested behavioral chain" and (b) stores BAR records with null signatures.
- **Remediation:** Fix `sign_receipt` → correct method name. Verify full signing path end-to-end.

---

## GOV-002 — ATF-INV-001 Contradiction: TAR Issued to UNKNOWN Delegator
- **Severity:** HIGH
- **Invariant Violated:** ATF-INV-001 (chain root integrity — every TAR must trace to a valid human root)
- **File:** `omnix_core/agents/atf/atf_connector.py:223–241`
- **Description:** When an agent_id is not found in the lattice, ATF Connector creates a stub DR with `delegator_id="UNKNOWN"` and `chain_root_id=""`. The TAR issued against this stub cannot trace to a valid human root. ATF-INV-001 requires that every TAR traces back to a human-controlled identity (L0).
- **State Created:** A TAR with `delegator_id=UNKNOWN` and `chain_root_id=""` is PQC-signed and stored. It appears as a legitimate governance artifact.
- **Contradiction:** ATF claims zero-trust chain from human root. TARs with UNKNOWN delegators break the chain.
- **Remediation:** Reject TAR issuance if DR is synthetic. Return error to caller.

---

## GOV-003 — MIVP-INV-009 vs. Corpus Stale Certification Counts
- **Severity:** MEDIUM
- **Invariant:** MIVP-INV-009 (MANDATE-BOUND and MANDATE-ALIGNED are mutually exclusive)
- **File:** `scripts/fine_tuning/output/train.jsonl` (OGI system prompt)
- **Description:** The OGI corpus system prompt states "125 formal invariants" and "194 ADRs." Since ADR-196–199 were added (27 new invariants, total now 169), OGI will cite incorrect numbers when asked about the invariant count. This is not a runtime contradiction in the protocol, but creates a semantic drift: the trained model is an authority that will confidently state wrong invariant counts.
- **Contradiction:** The governance infrastructure enforces 169 invariants. The AI model trained to explain it says 125.
- **Remediation:** Regenerate OGI corpus after each ADR batch. Or add an ADR/invariant count lookup tool to OGI's retrieval context.

---

## GOV-004 — OGR-INV-001 Cannot Be Verified When GOL Is Unwired
- **Severity:** MEDIUM
- **Invariant:** OGR-INV-001 (simultaneous-layer invariant — all ATF layers must execute within each OGR session turn)
- **File:** `omnix_core/govern/governance_runtime.py` + `omnix_core/observability/metrics.py`
- **Description:** OGR-INV-001 requires that all 6 ATF protocol layers execute within each session turn. Verifying this invariant requires phase-level timing data from the GOL. Since the GOL is never called from governance_runtime.py, there is no instrumentation data to verify whether all layers completed. OGR-INV-001 is technically unverifiable in production.
- **Contradiction:** ADR-184 defines OGR-INV-001 as enforceable. ADR-198 builds the tooling to enforce it. The tooling is never connected.
- **Remediation:** Wire GOL to governance_runtime.py (see GAP-001). Gate OGR-INV-001 verification on phase timer data.

---

## GOV-005 — HALT Propagation: Verified Correct ✅
- **Status:** CONFIRMED CORRECT
- **Description:** HALT state propagation through ATF L1–L4 was traced. A HALT issued by AVM propagates correctly: AVM → approval gate blocks → receipt not issued. HALT does not silently degrade.

---

## GOV-006 — MANDATE-BOUND / MANDATE-ALIGNED Mutual Exclusivity: Verified Correct ✅
- **Status:** CONFIRMED CORRECT
- **File:** `omnix_core/bev/mandate_integrity_verification.py:472–474`
- **Description:** DB CHECK constraint `chk_seal_tier_consistency` enforces mutual exclusivity of MANDATE-BOUND and MANDATE-ALIGNED at the database level. MIVP-INV-009 enforced at persistence layer. ✅

---

## GOV-007 — TTL Enforcement in AGVP: Verified with Caveat
- **Status:** PARTIALLY CONFIRMED
- **Description:** PVR TTL is set at issuance. However, TTL expiry enforcement depends on the caller checking `expires_at` at lookup time. There is no background TTL purge job. Expired PVRs remain in the DB and could be retrieved if a caller does not check expiry.
- **Severity:** LOW
- **Remediation:** Add `WHERE expires_at > NOW()` to all PVR retrieval queries. Add a periodic cleanup job.

---

## GOV-008 — Continuity Degradation Formula: Verified Correct ✅
- **Status:** CONFIRMED CORRECT
- **Description:** CES (Continuity Eligibility Score) degradation formula in `rcr_performance.py` is mathematically correct: multi-component weighted score with proper normalization. RCR-INV-* satisfied at implementation level.

---

## GOV-009 — AFG Fragmentation Limit at 0.90 Default: Verified with Caveat
- **Status:** CONFIRMED — with documentation risk
- **Description:** `AFG_FRAGMENTATION_LIMIT` default is 0.90 with documented maximum of 0.95. Values > 1.0 are rejected. Documentation in replit.md states this correctly.
- **Caveat:** The "never above 0.95" documentation is in replit.md but not in code comments or startup validation. An operator could accidentally set 0.96–0.99 (rejected at >1.0 but not at 0.96–0.99) without knowing the informal 0.95 ceiling.
- **Remediation:** Add startup validation: `if afg_limit > 0.95: logger.warning("[AFG] fragmentation limit > 0.95 — institutional safety ceiling exceeded")`.

---

*Report generated: 2026-05-27 | OMNIX QUANTUM Zero-Assumption Audit*
