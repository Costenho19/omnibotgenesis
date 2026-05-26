# Governance Semantics Report — Institutional Deep Audit
**Date:** 2026-05-25  
**Auditor:** OMNIX Internal Governance Audit  
**Scope:** MIVP semantic coherence vs ATF · RGC · OSG · PoGR · OGI · SGIP  
**Verdict:** ✅ NO CRITICAL SEMANTIC CONFLICT — 2 vocabulary drift risks, 1 invariant duplication candidate

---

## Executive Summary

MIVP introduces three new artifact classes (MBR, MAS, MBRSeal) and one new PoGC tag (MANDATE-BOUND). The vocabulary is distinct from all existing artifact families. No invariant duplication detected. No conflicting enforcement paths. Two vocabulary drift risks identified that could confuse external reviewers if not addressed in ADR-194 or RFC-ATF-6.

---

## Layer-by-Layer Semantic Analysis

### MIVP vs ATF (ADR-156/157/158/159/160)

**Verdict:** ✅ No conflict.

ATF defines the identity and delegation chain (AIR → DR → TAR → RCR). MIVP operates at the session behavior layer — it binds a mandate to a session that already has a governing receipt issued by ATF. MIVP does not modify, duplicate, or reinterpret any ATF artifact.

**Artifact IDs:** MBR-{HEX16}, MAS-{HEX16}, MBRS-{HEX16} — all distinct from ATF identifiers (DR-*, TAR-*, RCR-*).

**Vocabulary note:** ATF uses "authority" as its core concept; MIVP uses "mandate." These are semantically distinct: authority is about who can act; mandate is about what the agent must optimize for. No overlap.

---

### MIVP vs RGC (ADR-159/RFC-ATF-2)

**Verdict:** ✅ No conflict.

RGC handles runtime continuity — session recovery, CES (Chain Completeness Score), AFG (Authority Fragmentation Guard). MIVP is additive to RGC: a session can be RGC-NOMINAL and MIVP-VIOLATED simultaneously, or RGC-DEGRADED and MIVP-ALIGNED simultaneously.

**No invariant duplication:** MIVP-INV-005 (HALT on mandate drift) and RGC-INV-001–008 operate on different signals (MAS vs CES/ContinuityRecord). No overlapping enforcement.

---

### MIVP vs OSG (ADR-188)

**Verdict:** ✅ No conflict.

OSG (OMNIX Settlement Gate) validates post-execution settlement decisions. MIVP operates during execution (per-turn). OSG reads the PoGC tags at settlement validation time — MANDATE-BOUND would be a valid input to OSG's validation logic, but OSG does not currently consume it. No conflict; future integration is a planned extension.

---

### MIVP vs PoGR (ADR-186/187)

**Verdict:** ✅ No conflict. One integration note.

MANDATE-BOUND is added to `pogc_tags` list in `close_session()`. The PoGR blueprint reads `pogc_tags` when issuing a PoGC certificate. This is the correct integration pattern. The MANDATE-BOUND tag will appear in PoGC certificates when earned.

**Integration note:** The PoGR spec (ADR-186) defines 6 invariants (PoGR-INV-001–006). None of them are violated or duplicated by MIVP. However, PoGR-INV-003 (TTL explicit) and PoGR-INV-004 (3-channel trust anchor) should be verified to cover MANDATE-BOUND tagged certificates — the MBR provides the third trust channel. This should be documented in ADR-186 rev.2.

---

### MIVP vs OGI (ADR-193)

**Verdict:** ⚠️ Vocabulary gap — not a conflict.

ADR-193 was written before ADR-194. The OGI system prompt and corpus categories do not include MIVP vocabulary. This is not a semantic conflict but a corpus gap: the OGI model, when trained, will not know about MBR, MAS, MANDATE-BOUND, or MIVP-INV-001–008.

**Risk:** An institutional reviewer asking OGI "What is the Mandate Binding Record?" will receive a hallucinated or refusal response. This undermines the OGI value proposition precisely where MIVP is most novel.

**Remediation:** Update `ogi_system_prompt.txt` and add MIVP corpus category before training (see OGI_CORPUS_AUDIT.md F-C-005).

---

### MIVP vs SGIP (ADR-171)

**Verdict:** ✅ No conflict.

SGIP (Semantic Governance Interoperability Protocol) defines how cross-runtime semantic alignment is certified (STR, SPV, SAC). MIVP operates within a single session. No semantic overlap.

---

## Vocabulary Drift Risk 1 — "Admissibility" overloading

**Severity:** MEDIUM  
**Location:** ATF context admission (ADR-050/Context Admission Gate) vs MIVP (mandate threshold)

**Finding:** The term "admissibility" is used in two semantically different ways in OMNIX:
1. **ATF/CAG:** "Is this session admitted based on market conditions, volatility, and governance scope?" (binary: ADMITTED / REJECTED)
2. **MIVP:** "Is the agent's output admissible relative to the declared mandate?" (implicit in MAS < halt_threshold → HALT)

An institutional reviewer reading ADR-194 alongside ADR-050 may conflate these two concepts. The MIVP HALT path does not use the term "admissibility" in code, but the framing in ADR-194 §Addressing Brian Hodak's Six Questions ("Admissibility gate blocks bad paths?") could cause confusion.

**Remediation:** In ADR-194, rename the description of MIVP-INV-005 enforcement as "mandate HALT gate" explicitly, distinguishing it from the "context admissibility gate" (ADR-050). Add a cross-reference note.

---

## Vocabulary Drift Risk 2 — "Mandate" vs "Constraint"

**Severity:** LOW  
**Location:** ADR-194 vs BEV (ADR-181/182/183)

**Finding:** BEV uses "constraint" (constraint_set in governing receipt, CCS = Constraint Conformance Signal). MIVP uses "mandate" (mandate_objective, mandate_binding). These are semantically distinct but external reviewers may ask: "Is a mandate a type of constraint?"

Technically no: constraints define what the agent must NOT do (negative bounds); mandates define what the agent MUST optimize for (positive objective). MIVP enforces that the agent's optimization target matches the mandate, not just that it avoids constraint violations.

**Remediation:** Add a one-paragraph definitional note to ADR-194 §Context section explicitly distinguishing mandate (positive objective) from constraint (negative bound). This distinction is the core innovation — it should be stated explicitly.

---

## Invariant Duplication Analysis

| MIVP Invariant | Closest Existing Invariant | Overlap? |
|---|---|---|
| MIVP-INV-001 (MBR before turn 1) | BEV-INV-001 (BAR issued before output delivery) | No — different artifacts, different timing |
| MIVP-INV-002 (mandate hash immutable) | ATF-INV-004 (content hash immutability) | Conceptually similar, different scope — not a duplicate |
| MIVP-INV-003 (MAS per turn) | BEV-INV-005 (CCS per turn) | Parallel structure, different signals — not a duplicate |
| MIVP-INV-004 (MAS in [0,1]) | None | Unique |
| MIVP-INV-005 (HALT on mandate drift) | AGV-INV-001 (proactive veto on drift) | Enforcement mechanism is different — AGVP is anticipatory, MIVP is reactive per-turn |
| MIVP-INV-006 (MAS append-only) | BEV-INV-010 (CTCHC append-only) | Same pattern, different chain — not a duplicate |
| MIVP-INV-007 (seal at close) | BEV-INV-014 (CTCHC seal at close) | Same pattern, different artifact — not a duplicate |
| MIVP-INV-008 (MANDATE-BOUND conditions) | PoGR-INV-002 (zero-trust verify) | Complementary, not duplicated |

**Conclusion:** Zero invariant duplications. MIVP invariants are all novel in their enforcement scope.

---

## Conflicting Enforcement Path Analysis

**Scenario: MAS HALT + AVM APPROVE simultaneously**

If MIVP-INV-005 triggers HALT but AVM independently approves the same action, which gate prevails?

**Answer:** Both gates are evaluated in `record_turn()`. The OGR verdict logic (`governance_runtime.py:509–513`) combines them as:
```python
mivp_halt = mas is not None and mas.verdict == "HALT"
should_halt = (bar.verdict == "HALT") or (ccs_signal and ccs_signal.verdict == "HALT") or mivp_halt
```
MIVP HALT overrides AVM APPROVE — the ORed condition means any HALT source halts the session. This is correct: MIVP operates at a layer above AVM (mandate vs. context admission). No conflict.

**Scenario: MANDATE-BOUND + OSG REJECTED simultaneously**

A session can earn MANDATE-BOUND (zero mandate violations) but have its settlement rejected by OSG. These are orthogonal: MANDATE-BOUND certifies execution intent alignment; OSG certifies settlement validity. No conflict. Both can be true independently.

---

## Verdict

**✅ Semantically coherent.** MIVP introduces a clean new vocabulary layer with no conflicts against ATF, RGC, OSG, PoGR, or SGIP. Two vocabulary drift risks (admissibility overloading, mandate vs constraint) should be addressed in ADR-194 before RFC-ATF-6 publication to prevent external reviewer confusion. The OGI vocabulary gap is a corpus implementation issue, not a semantic architecture issue.
