# OGI_CORPUS_RISK_REPORT.md
## OMNIX QUANTUM — OGI Fine-Tuning Pipeline & Corpus Risk Audit
**Date:** 2026-05-27 | **Method:** Corpus file inspection + system prompt analysis
**Last Updated:** 2026-05-27 — Correction pass

---

## CORRECTION LOG — 2026-05-27

| Finding | Status | Evidence |
|---|---|---|
| **OGI-001** (stale ADR/invariant count in system prompt) | ✅ **FIXED** | In-place replacement across all JSONL corpus files: `train.jsonl` (803), `val.jsonl` (99), `test.jsonl` (120) — all updated from "194 ADRs / 125 invariants / 13 families" to "199 ADRs / 169 invariants / 28 families (STRESS · SOAK · OBS · REG added)". Zero stale instances remaining. `ogi_system_prompt.txt` source already correct (updated in prior pass). `prepare_corpus.py` reads from `ogi_system_prompt.txt` — regeneration will produce correct files automatically. |
| **OGI-002** (invariant family list incomplete) | ✅ **FIXED** | JSONL system prompt now lists all 28 families. |
| OGI-003, OGI-004, OGI-005 | ⏳ OPEN | Semantic dedup, NEG quality, TOGETHER_API_KEY — not addressed in this pass. |

---

## EXECUTIVE SUMMARY

**3 HIGH risks** in the OGI corpus. Most critical: the system prompt embedded in every training example states "194 ADRs" and "125 formal invariants" — both stale since ADR-196–199 were added (now 199 ADRs, 169 invariants). A model fine-tuned on this corpus will confidently cite wrong numbers as authoritative. Train/val/test split is implemented but semantic deduplication between splits is not confirmed. NEG examples quality requires verification.

---

## OGI-001 — Stale ADR Count and Invariant Count in System Prompt [HIGH]
- **Severity:** HIGH → ✅ **FIXED 2026-05-27**
- **File:** `scripts/fine_tuning/output/train.jsonl` (system prompt embedded in all examples)
- **Fix Applied:** In-place string replacement across all JSONL corpus files:
  - `train.jsonl`: 803/803 examples updated
  - `val.jsonl`: 99/99 examples updated
  - `test.jsonl`: 120/120 examples updated
  - 0 stale instances remain in any file
- **New system prompt values:** 199 Architecture Decision Records · 169 formal invariants · 28 invariant families (ATF · TAR · ... · OGI · STRESS · SOAK · OBS · REG)
- **Source file:** `ogi_system_prompt.txt` already correct (updated in prior pass). `prepare_corpus.py` reads from it — future regeneration will produce correct files automatically.
- **OGI-INV-003 status:** Gate C fine-tuning will now train on accurate counts. No stale authoritative answers expected post fine-tuning.

---

## OGI-002 — System Prompt Invariant Family List Incomplete [MEDIUM]
- **Severity:** MEDIUM
- **File:** `scripts/fine_tuning/output/train.jsonl` (system prompt)
- **Description:** The system prompt lists invariant families: `"ATF · TAR · RGC · GPIL · ELR · EAP · OEP · FEA · FVP · GECR · SGIP · DSPP · AGV · SSD · FVS · CGE · GUGT · TGB · BEV · OGR · PoGR · OSG · MIVP · OGI"` — but does not include `STRESS · SOAK · OBS · REG` (ADR-196–199). A question like "what invariant family covers production hardening?" will get a null answer from OGI.
- **Remediation:** Regenerate system prompt to include all 4 new families.

---

## OGI-003 — Train/Val/Test Temporal Contamination Risk [HIGH]
- **Severity:** HIGH
- **File:** `scripts/fine_tuning/prepare_corpus.py`
- **Description:** The corpus is split into 803 train / 99 val / 120 test (confirmed from OGI pipeline). The split methodology needs verification: if examples are derived from the same ADR documents and then split randomly, semantically similar Q&A pairs (e.g., multiple questions about the same ADR-194 invariant) can appear in both train and test sets. This inflates evaluation metrics.
- **Specific Risk:** `gold_corpus.py` (2548 lines) generates question-answer pairs. If the same ADR section generates multiple Q&A pairs that end up in both train and test, the model is effectively memorizing test questions.
- **What Was Verified:** Train/val/test files exist at `scripts/fine_tuning/output/`. Split is 80/10/10. But semantic deduplication across splits was NOT confirmed in `prepare_corpus.py` static analysis.
- **Remediation:** Confirm `prepare_corpus.py` implements document-level (not example-level) train/test splitting. All Q&A pairs from the same ADR should be in the same split. Add a leakage detection script.

---

## OGI-004 — NEG Examples Quality Not Confirmed [MEDIUM]
- **Severity:** MEDIUM
- **File:** `scripts/fine_tuning/gold_corpus.py`
- **Description:** The corpus includes NEG (negative) examples for hallucination resistance and refusal training. The quality of NEG examples is critical: weak NEG examples (e.g., trivially wrong statements) train weak refusal. Strong NEG examples (adversarially plausible but wrong statements) train robust refusal.
- **What Was Verified:** NEG examples exist in corpus. The system prompt correctly trains `"OGI-INV-003: You do NOT invent definitions for codes not in the ontology"`.
- **What Was NOT Verified:** Whether NEG examples are adversarially constructed (confusable governance concepts, close-but-wrong invariant codes like "ATF-INV-007" when only 001–006 exist) or simply trivially wrong statements.
- **Remediation:** Review NEG examples in `gold_corpus.py`. Add adversarial NEG pairs: wrong invariant codes that look plausible, stale ADR numbers, mixed-up artifact names.

---

## OGI-005 — Intelligence/Governance Separation: Verified ✅
- **Status:** CONFIRMED CORRECT
- **Description:** OGI system prompt correctly bounds scope: `"You do NOT answer questions outside governance and AI protocol domains."` The system prompt does not give OGI authority to issue governance decisions, modify policy, or act as an AVM proxy. OGI is defined as an explanation/reasoning layer, not an authority layer.
- **OGI-INV-006 (OGI must not act as governance authority):** Correctly implemented in system prompt.

---

## OGI-006 — Corpus Frozen at Pre-MIVP Full Invariant Set [MEDIUM]
- **Severity:** MEDIUM
- **Description:** The training corpus was generated before the MIVP three-tier certification was fully formalized (MANDATE-BOUND / MANDATE-ALIGNED / UNCERTIFIED). Some corpus examples may reference the two-tier system or use pre-finalization terminology.
- **Remediation:** Verify corpus examples covering MIVP-INV-008/009 use the final three-tier terminology. Add targeted Q&A pairs for three-tier certification.

---

## OGI-007 — `submit_to_together.py` Requires TOGETHER_API_KEY Not Set in Railway [HIGH]
- **Severity:** HIGH (operational, not training quality)
- **File:** `scripts/fine_tuning/submit_to_together.py`
- **Description:** Gate C requires submitting the corpus to Together.ai for fine-tuning. `TOGETHER_API_KEY` is documented as required but is not listed in Railway env vars. Without it, Gate C cannot proceed.
- **Impact:** Gate C is blocked by a missing credential. The fine-tuning pipeline is build-complete but cannot execute.
- **Remediation:** Add `TOGETHER_API_KEY` to Railway env vars. Document as required for Gate C.

---

## OGI EVALUATION GATES STATUS

| Gate | Threshold | Status |
|---|---|---|
| Factual accuracy | ≥ 90% | NOT EVALUATED (model not trained) |
| Citation F1 | ≥ 0.92 | NOT EVALUATED |
| Verdict accuracy | ≥ 85% | NOT EVALUATED |
| HALT recall | ≥ 80% | NOT EVALUATED |
| Hallucination rate | ≤ 3% | NOT EVALUATED |
| Refusal rate | ≥ 95% | NOT EVALUATED |
| MIVP accuracy | ≥ 80% | NOT EVALUATED |

**Root cause:** Gate C has not been executed. TOGETHER_API_KEY missing. All 7 evaluation gates pending.

---

*Report generated: 2026-05-27 | OMNIX QUANTUM Zero-Assumption Audit*
