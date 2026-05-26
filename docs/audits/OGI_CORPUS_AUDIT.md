# OGI Corpus Audit — Institutional Deep Audit
**Date:** 2026-05-25  
**Auditor:** OMNIX Internal Governance Audit  
**Scope:** ADR-193 · OGI Fine-Tuning Pipeline & Corpus Governance  
**Verdict:** ⚠️ SPEC-ONLY — Pipeline is designed, not implemented. No actual corpus files exist. All findings are pre-implementation risks.

---

## Executive Summary

ADR-193 defines a comprehensive, well-structured corpus governance framework. The invariant set (OGI-INV-001–010) covers the critical failure modes: data leakage, split contamination, hallucination, and deployment without evaluation gate. However, the corpus does not yet exist — no `train.jsonl`, `val.jsonl`, `test.jsonl`, `manifest.json`, or `eval_suite.jsonl` files are present in the repository. All findings below are architectural risks that must be addressed during implementation.

Additionally, ADR-193 contains stale counts that must be corrected before corpus generation begins.

---

## F-C-001 — HIGH — ADR-193 contains stale ADR and invariant counts

**File:** `docs/adr/ADR-193-ogi-fine-tuning-pipeline.md` — line 23

**Finding:** ADR-193 states:
- "192 Architecture Decision Records (ADRs)" — **stale, correct count is 194**
- "51 formal invariants across 10 invariant families" — **stale, correct count is 55+ active (11 families including MIVP)**

If corpus generation begins from these stale counts, the OGI model will be trained without ADR-193 and ADR-194 in scope, and without MIVP-INV-001–008 in the invariant ontology.

**Impact:** The OGI model will not be able to answer questions about MIVP, MBR, MAS, MBRSeal, or MANDATE-BOUND.  
**Institutional Risk:** HIGH — the corpus is the foundation of the model's knowledge. Stale counts produce a stale model.

**Remediation:** Update ADR-193 lines 23–24 to reflect 194 ADRs and 55 active invariants across 11 families. Re-run corpus generation after each major ADR addition.

---

## F-C-002 — HIGH — OGI-INV-* family not in INVARIANT_TEST_MATRIX

**File:** `docs/compliance/INVARIANT_TEST_MATRIX.md`

**Finding:** ADR-193 defines 10 invariants (OGI-INV-001–010). These are not listed in the INVARIANT_TEST_MATRIX. OGI-INV-008 (Evaluation Gate Before Deployment) is particularly critical — it is a hard gate that prevents a model from going live without passing all 5 evaluation metrics.

**Impact:** OGI invariants are invisible to the institutional audit trail. A regulatory reviewer auditing the invariant matrix would not see the model deployment gate.  
**Institutional Risk:** HIGH — the EU AI Act requires documented conformance checks before AI system deployment.

**Remediation:** Add OGI-INV-001–010 as Family 12 in INVARIANT_TEST_MATRIX.md. Mark all as ❌ Pending (pipeline not implemented).

---

## F-C-003 — MEDIUM — No `corpus_allowlist.yaml` exists

**File:** Expected at `/home/runner/workspace/corpus_allowlist.yaml` or `scripts/fine_tuning/corpus_allowlist.yaml`

**Finding:** OGI-INV-001 requires every training file to appear in `corpus_allowlist.yaml`. This file does not exist. If corpus generation begins without it, OGI-INV-001 is violated from the first run.

**Impact:** Corpus generation is not possible in a compliant manner until this file is created.  
**Institutional Risk:** MEDIUM — the allowlist is the primary control against accidental leakage of NDA content or proprietary prompts.

**Remediation:** Create `scripts/fine_tuning/corpus_allowlist.yaml` before corpus generation. Initial scope: all `docs/adr/ADR-*.md` + `docs/standards/RFC-ATF-*.md` + `docs/ARCHITECTURE_INDEX.md`.

---

## F-C-004 — MEDIUM — Train/Val/Test split strategy underspecified for adversarial examples

**File:** `docs/adr/ADR-193-ogi-fine-tuning-pipeline.md` — OGI-006

**Finding:** The 80/10/10 stratified split is specified by category, not by semantic content. For the `SCN` (Scenario → Verdict) and `RTR` (Red-Team Refusal) categories, adversarial examples should be overrepresented in the test set to properly measure model robustness — not randomly split. A 10% random test sample of adversarial examples may be too small to detect systematic refusal failures.

**Impact:** The model may pass evaluation gates on benign scenarios while failing on adversarial inputs not well-represented in the test set.  
**Institutional Risk:** MEDIUM — governance QA reviewers will test adversarial scenarios first.

**Remediation:** Add OGI-006b: adversarial examples (RTR + hardest SCN tier) use a 60/20/20 split to ensure adequate test coverage.

---

## F-C-005 — MEDIUM — No proxy example complexity tier defined

**File:** `docs/adr/ADR-193-ogi-fine-tuning-pipeline.md` — OGI-003

**Finding:** The `SCN` category (Scenario → Verdict) covers 800 examples with no complexity tiering. A model trained on uniformly simple scenarios will struggle with multi-step proxy optimization cases — exactly the scenarios MIVP was designed to detect. There is no category for "agent satisfies all constraints but optimizes prohibited proxy" — the MIVP-specific failure mode.

**Impact:** The OGI model will not be able to correctly evaluate MIVP-specific scenarios (MAS WARNING / HALT cases).  
**Institutional Risk:** MEDIUM — the first external question to the OGI model after RFC-ATF-6 publication will likely be a MIVP scenario.

**Remediation:** Add `MIVP` as a 13th corpus category: mandate-proxy conflict scenarios (suggested: 150 examples, 80/10/10 split). Include GRT (Governance Reasoning Trace) and NEG (Negative — correct refusal/halt) sub-types for MIVP.

---

## F-C-006 — MEDIUM — Hallucination check against canonical ontology: ontology not defined

**File:** `docs/adr/ADR-193-ogi-fine-tuning-pipeline.md` — OGI-007

**Finding:** OGI-007 evaluation gate #4 specifies "Hallucination rate ≤ 3% — Auto-checked against canonical ontology." No `ontology.json` file exists. The canonical ontology (all valid ADR IDs, invariant codes, RFC section identifiers, canonical artifact names) has not been generated.

**Impact:** The hallucination evaluation gate cannot be executed without this file.  
**Institutional Risk:** MEDIUM — without the ontology, hallucination detection is manual and subjective.

**Remediation:** Add to corpus pipeline: auto-generate `ontology.json` from all ADR filenames, all invariant codes extracted by regex, all RFC section headers, and all canonical artifact IDs (MBR-, MAS-, MBRS-, BAR-, CCS-, CTCHC-, OGR-, PoGC-, etc.).

---

## F-C-007 — LOW — `rejected_samples.jsonl` logging path not specified

**File:** `docs/adr/ADR-193-ogi-fine-tuning-pipeline.md` — OGI-005

**Finding:** OGI-INV-005 requires that all rejected samples be logged to `rejected_samples.jsonl`. The ADR does not specify the file path relative to the repository. Pipeline implementations may place it in different locations, breaking audit reproducibility.

**Remediation:** Specify canonical path: `scripts/fine_tuning/rejected_samples.jsonl`. Add to OGI-007 manifest requirements.

---

## Train/Val/Test Contamination Analysis

**Status:** Not applicable — corpus does not exist yet. Contamination controls are specified (SHA-256 dedup, OGI-INV-005, OGI-INV-006 cosine similarity threshold 0.97) but cannot be audited pre-implementation.

**Pre-implementation risk:** The cosine similarity threshold (0.97) applies between examples within the corpus. It does not protect against a train example that is semantically equivalent to a test example but uses different wording. Recommend adding a governance-term-aware dedup that checks exact match on (invariant_code, scenario_type, verdict) triple.

---

## Vocabulary Consistency Risk

The OGI system prompt (OGI-004) instructs the model to "speak OMNIX vocabulary natively." However, ADR-193 was written before ADR-194 (MIVP). The system prompt does not include MIVP vocabulary: MBR, MAS, MBRSeal, ProxyGuard, MANDATE-BOUND, MIVP-INV-001–008.

**Risk:** An OGI model trained without MIVP-specific examples will produce hallucinated answers to MIVP questions while presenting itself as authoritative.

**Remediation:** Update system prompt to include MIVP vocabulary before corpus generation. The system prompt is stored at `scripts/fine_tuning/ogi_system_prompt.txt` — verify this file exists and is updated.

---

## Verdict

**BLOCKED — Pre-implementation.** The corpus pipeline is well-designed but no artifacts exist. Three actions must occur before corpus generation:
1. Update ADR-193 stale counts (F-C-001)
2. Create `corpus_allowlist.yaml` (F-C-003)
3. Generate `ontology.json` (F-C-006)

Then: add OGI-INV family to INVARIANT_TEST_MATRIX (F-C-002) and add MIVP corpus category (F-C-005).
