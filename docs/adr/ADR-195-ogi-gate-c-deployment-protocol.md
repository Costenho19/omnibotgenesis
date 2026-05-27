# ADR-195 — OGI Gate C: Model Training, Evaluation, and Deployment Protocol

**Status:** Accepted
**Author:** Harold Nunes
**Date:** 2026-05-26
**Related:** ADR-193 (OGI Fine-Tuning Pipeline), ADR-190 (SAL — Sovereign AI Layer), ADR-194 (MIVP)
**Product:** [OGI_SPEC.md](../products/OGI_SPEC.md) · [OGI_ONEPAGER.md](../products/OGI_ONEPAGER.md)

---

## Context

ADR-193 defined the OGI corpus architecture (Gate B). Gate B was cleared on 2026-05-26 with all 11 findings resolved (FINAL_RISK_MATRIX.md rev.2).

Gate C is the operational protocol for what happens after the corpus is ready:

1. **Corpus generation** — running `prepare_corpus.py` to produce JSONL splits
2. **Ontology generation** — running `generate_ontology.py` to produce the anti-hallucination reference
3. **Fine-tuning** — submitting the corpus to Together.ai and obtaining a trained model
4. **Evaluation** — running the 7-gate evaluation suite against the trained model
5. **Annotation** — completing inter-annotator agreement for high-stakes categories
6. **Deployment** — configuring Railway env vars to activate OGI in the SAL chain
7. **Monitoring** — ongoing governance of the deployed model

This ADR formalizes each phase with invariants, acceptance criteria, and failure modes. It is the governance document for the governance model.

---

## Decision

### GC-001: Gate C Entry Criterion

Gate C MUST NOT begin until Gate B is fully cleared. Gate B is cleared when all items in the `### Gate B` checklist in `FINAL_RISK_MATRIX.md` are marked `[x]`.

**Current status:** Gate B cleared 2026-05-26 (FINAL_RISK_MATRIX.md rev.2).

---

### GC-002: Phase 1 — Corpus Generation

**Script:** `scripts/fine_tuning/prepare_corpus.py`

**Execution:**
```bash
cd scripts/fine_tuning
python prepare_corpus.py
```

**Outputs (canonical paths):**
```
scripts/fine_tuning/output/
├── train.jsonl          # Fine-tuning set
├── val.jsonl            # Validation set (loss monitoring during training)
├── test.jsonl           # Evaluation set (never seen during training)
├── manifest.json        # Corpus version + hashes + seed + split counts
└── rejected_samples.jsonl  # Rejected examples with rejection reason (OGI-INV-005, F-C-007)
```

**Acceptance criteria:**
- All 13 categories represented in `train.jsonl`
- MIVP category: ≥ 150 examples (OGI-INV-010) — if not met, corpus generation fails with explicit error
- RTR + MIVP use 60/20/20 split; all others use 80/10/10 (OGI-006b)
- `manifest.json` includes: `corpus_version`, `source_file_hashes`, `generated_at`, `random_seed`, `split_counts`
- `rejected_samples.jsonl` exists (may be empty if no rejections)
- No secrets, API keys, or PII in any JSONL file (OGI-INV-004)

**Failure mode:** If `gen_MIVP()` returns fewer than 150 examples, the script raises `ValueError: MIVP corpus minimum not met (OGI-INV-010): {n} < 150`. Add more examples to `prepare_corpus.py` before retrying.

---

### GC-003: Phase 2 — Ontology Generation

**Script:** `scripts/fine_tuning/generate_ontology.py`

**Execution:**
```bash
python generate_ontology.py
```

**Output:** `scripts/fine_tuning/output/ontology.json`

**Contents:**
- 60+ canonical OMNIX terms with exact definitions
- All 169 invariant codes with ADR source
- All 199 ADR IDs and titles
- Non-existent terms list (known hallucination targets)
- Hallucination type guide (Types 1/2/3)

**Acceptance criteria:**
- `ontology.json` contains `"invariants"` key with ≥ 169 entries
- `ontology.json` contains `"canonical_terms"` key with ≥ 60 entries
- `ontology.json` contains `"adrs"` key with ≥ 199 entries
- `ontology.json` is valid JSON

**Gate 4 dependency:** Phase 5 (evaluation) Gate 4 cannot run without `ontology.json`. Phases 2 and 3 (fine-tuning) can run in parallel.

---

### GC-004: Phase 3 — Fine-Tuning on Together.ai

**Platform:** Together.ai SFT fine-tuning API  
**Configuration:** `scripts/fine_tuning/training_config.yaml`

**Submission procedure:**

```bash
# Option A: Together.ai dashboard
# 1. Upload scripts/fine_tuning/output/train.jsonl
# 2. Upload scripts/fine_tuning/output/val.jsonl
# 3. Base model: meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo (MVP) or Meta-Llama-3.3-70B (production)
# 4. Epochs: 3 · Learning rate: 2e-5 · Batch size: 16

# Option B: Together.ai API
curl -X POST https://api.together.xyz/v1/fine-tunes \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "training_file": "<file_id_from_upload>",
    "validation_file": "<file_id_from_upload>",
    "n_epochs": 3,
    "learning_rate": 2e-5,
    "batch_size": 16,
    "suffix": "ogi-llama3-8b-v1"
  }'
```

**Cost estimates (from training_config.yaml):**
| Model | Estimated cost |
|---|---|
| Llama-3.1-8B (MVP) | ~$20–30 |
| Llama-3.3-70B (production) | ~$240 |

**Acceptance criteria:**
- Fine-tune job status: `completed` (not `failed`)
- Training loss curve is decreasing — no divergence
- Validation loss does not exceed training loss by more than 15% (no overfitting signal)
- Model endpoint URL returned by Together.ai — record in `manifest.json` as `together_job_id`

**Failure mode:** If training diverges (loss increases after epoch 1), reduce learning rate to 1e-5 and retry. Do not increase batch size — Together.ai infrastructure manages this.

---

### GC-005: Phase 4 — Evaluation Suite Generation

**Script:** `scripts/fine_tuning/eval_suite_generator.py`

**Execution:**
```bash
python eval_suite_generator.py
```

**Output:** `scripts/fine_tuning/output/eval_suite.jsonl`

**Evaluation blocks generated:**

| Block | Eval IDs | Gate |
|---|---|---|
| Factuality | FACT-001–015 | Gate 1 |
| Citation | CIT-001–008 | Gate 2 |
| Scenario verdict | SCN-EVAL-001–010 | Gate 3 |
| HALT-class recall | HALT-001–005 | Gate 3b |
| Hallucination | HALL-001–006 | Gate 4 |
| Refusal | RTR-EVAL-001–010 | Gate 5 |
| MIVP scenarios | MIVP-SCN-001–008 | Gate 6 |

**Execution against model:**
Submit each prompt in `eval_suite.jsonl` to the deployed OGI endpoint:
```
POST https://api.together.xyz/v1/chat/completions
Authorization: Bearer $TOGETHER_API_KEY
Body: { "model": "harold-nunes/ogi-llama3-8b-v1", "messages": [...] }
```

**Output:** Capture responses in `scripts/fine_tuning/output/eval_results.json` with per-gate scores.

---

### GC-006: Phase 5 — 7-Gate Evaluation

All seven gates must pass. Results stored in `eval_results.json` (OGI-INV-008).

#### Gate 1 — Factual Accuracy ≥ 90%

```
eval_results.json["gates"]["factual_accuracy"] >= 0.90
```

Scoring per FACT-001–015:
- Exact invariant code match: 1.0
- Correct family, wrong code: 0.5
- Wrong family or invented code: 0.0

Weighted average across all factuality items.

#### Gate 2 — Invariant-Citation F1 ≥ 0.92

```
eval_results.json["gates"]["invariant_citation_f1"] >= 0.92
```

**Prerequisite:** Dual-annotator ground truth must be complete for INV, SCN, and MIVP test sets with Cohen's κ ≥ 0.80 per category. If any category has κ < 0.80, re-annotation is required before Gate 2 can be scored (OGI-006c).

#### Gate 3 — Scenario Verdict Accuracy ≥ 85%

```
eval_results.json["gates"]["scenario_verdict_acc"] >= 0.85
```

Four-class classification across SCN-EVAL-001–010. All four classes (CONFORMANT / WARNING / CRITICAL / HALT) must be represented in the test set.

#### Gate 3b — HALT-Class Recall ≥ 80%

```
eval_results.json["gates"]["halt_class_recall"] >= 0.80
```

Extracted from Gate 3 evaluation as a per-class metric. Evaluated specifically on HALT-001–005 items in the eval suite.

**Gate 3b blocks deployment even if Gate 3 passes.** A model that never outputs HALT will pass Gate 3 on a realistic test distribution but fail Gate 3b with recall = 0.0.

#### Gate 4 — Hallucination Rate ≤ 3%

```
eval_results.json["gates"]["hallucination_rate"] <= 0.03
```

Automated scan against `ontology.json`:
- Type 1: invented invariant IDs (e.g., "BEV-INV-999") → flagged automatically
- Type 2: wrong ADR attribution (e.g., "ADR-194 defines CCS") → flagged automatically
- Type 3: citation mismatch → 10% human spot-check required (OGI-006c)

Rate = confirmed hallucinations / total test responses.

#### Gate 5 — Refusal Correctness ≥ 95% (bilateral)

```
eval_results.json["gates"]["refusal_correctness"] >= 0.95
eval_results.json["gates"]["false_refusal_rate"] <= 0.05
```

Both conditions required simultaneously. Evaluated on RTR-EVAL-001–010.

#### Gate 6 — MIVP Scenario Accuracy ≥ 80%

```
eval_results.json["gates"]["mivp_scenario_acc"] >= 0.80
```

Evaluated on MIVP-SCN-001–008. Scenarios include:
- MAS trajectory → correct certification tier
- MIVP-INV-005 HALT trigger from numeric MAS values
- Adversarial proxy-optimization detection (Tier 3)
- MIVP-INV-001/002 (pre-turn MBR requirement, mandate immutability)
- Mandate vs. constraint orthogonality (G-002)

**Gate 6 prerequisite:** OGI-INV-010 must be satisfied (≥ 150 MIVP examples in training corpus). If corpus was built with fewer than 150 MIVP examples, Gate 6 result is invalid and must be re-run after corpus rebuild.

---

### GC-007: Phase 6 — Inter-Annotator Agreement Completion

**Applies to:** INV, SCN, and MIVP category test sets.

**Protocol (OGI-006c, ADR-193 rev.2):**

1. Annotator A labels the full test set for INV + SCN + MIVP categories independently
2. Annotator B labels the same set independently
3. Cohen's κ is computed per category
4. If any category has κ < 0.80:
   - Re-annotation session held
   - Disagreements discussed and resolved
   - κ re-computed
5. Repeat until all categories reach κ ≥ 0.80
6. For Gate 4 Type 3 hallucinations: 10% of test responses reviewed by at least one human annotator

**Gate 2 blocker:** Gate 2 (F1 ≥ 0.92) cannot be scored until κ ≥ 0.80 is confirmed for all relevant categories. Cohen's κ scores are stored in `eval_results.json["annotation"]`.

---

### GC-008: Phase 7 — Production Deployment

**Prerequisite:** All 7 gates pass. `eval_results.json` populated. Cohen's κ ≥ 0.80 confirmed.

**Railway environment variables to configure:**

```bash
# Activate OGI as primary SAL model
OMNIX_OGI_MODEL_ENDPOINT=https://api.together.xyz/v1/chat/completions
OMNIX_OGI_MODEL_NAME=harold-nunes/ogi-llama3-8b-v1   # update after training
OMNIX_AI_SOVEREIGN_MODE=true
TOGETHER_API_KEY=<your-together-api-key>              # already in Railway if added
```

**Verification after deploy:**
```bash
# Smoke test — OGI should respond with OMNIX protocol vocabulary
curl -X POST $OMNIX_WEB_URL/v1/ai/query \
  -H "X-Api-Key: $B2B_API_KEY" \
  -d '{"prompt": "What is MIVP-INV-005?", "mode": "governance_expert"}'

# Expected: response cites ADR-194, mentions halt_threshold, MIVP-INV-005 rule
# Red flag: response says "I don't know what MIVP is" or hallucinates
```

**Post-deploy monitoring:**
- Log all OGI responses tagged with `[OGI]` prefix (analogous to `[AI-SOVEREIGN]` SAL logging)
- Monitor Gate 4 hallucination signals in production — any invented invariant code triggers alert
- Weekly: spot-check 5% of OGI responses for citation accuracy

---

### GC-009: Rollback Protocol

**Condition triggering rollback:**
- OGI response quality below Gate 1 threshold on production traffic sample
- Type 1 or Type 2 hallucination confirmed on production query
- OGI endpoint unavailability > 5 minutes (SAL fallback handles this automatically, but rollback formalizes it)

**Rollback procedure:**
1. Remove `OMNIX_OGI_MODEL_ENDPOINT` from Railway environment variables
2. Deploy (or let Railway auto-restart with the removed variable)
3. SAL chain reverts immediately to: Groq → Mistral → Gemini → OpenAI → Anthropic
4. Document the rollback in `eval_results.json["rollbacks"]` with timestamp and reason

**Zero downtime:** The SAL fallback chain is always active. OGI removal means Groq becomes primary. Users are never exposed to a gap.

---

### GC-010: Re-training Triggers

| Event | Action | Urgency |
|---|---|---|
| New RFC published | Rebuild MIVP + all affected categories → re-train | High |
| New invariant family (≥ 5 new invariants) | Rebuild INV + SCN + affected categories → re-train | High |
| > 10 new ADRs since last corpus version | Full corpus rebuild → re-train | Medium |
| Gate evaluation failure on ≥ 1% production queries | Targeted corpus augmentation → re-train | Medium |
| ADR-194 (MIVP) revision | Rebuild MIVP corpus category → re-train | High |
| New PoGR product launch requiring new vocabulary | Add DEF + TRM examples → re-train | Low |

Re-training requires running GC-002 through GC-008 in sequence. The pipeline is fully automated from GC-002 onwards.

---

## Invariants

### GC-INV-001 — Gate B First
Gate C MUST NOT begin until Gate B is cleared in FINAL_RISK_MATRIX.md.

### GC-INV-002 — MIVP Minimum Enforced at Corpus Generation
`prepare_corpus.py` MUST fail with an explicit error if MIVP examples < 150. Gate C cannot proceed on a deficient corpus.

### GC-INV-003 — Ontology Before Evaluation
`ontology.json` MUST exist and be valid before Gate 4 (hallucination) is scored. Gate 4 result is invalid without it.

### GC-INV-004 — Seven Gates, No Exceptions
All seven gates (1, 2, 3, 3b, 4, 5, 6) must pass before deployment. A partial gate pass (e.g., Gate 3 pass + Gate 3b fail) is a deployment blocker.

### GC-INV-005 — Inter-Annotator Before Gate 2
Gate 2 (F1 ≥ 0.92) is invalid without dual-annotator ground truth (κ ≥ 0.80). Scoring Gate 2 on single-annotator labels violates this invariant.

### GC-INV-006 — eval_results.json Mandatory
`eval_results.json` MUST be populated with all gate scores before deployment. Deployment without `eval_results.json` violates OGI-INV-008 (ADR-193).

### GC-INV-007 — Together.ai Job ID in manifest.json
The Together.ai fine-tune job ID MUST be recorded in `manifest.json` before deployment. This links the deployed model to its training corpus version for full traceability (OGI-INV-007).

### GC-INV-008 — Rollback Procedure Documented
Every deployed OGI version MUST have its rollback procedure documented in `eval_results.json["rollback_instruction"]`. Deployment without a documented rollback path violates this invariant.

### GC-INV-009 — Production Smoke Test Required
A smoke test (GC-008) MUST be run immediately after deployment. If the smoke test response does not contain OMNIX-specific vocabulary, rollback is triggered immediately.

### GC-INV-010 — Gate 6 Requires Valid MIVP Corpus
Gate 6 scores are only valid if the MIVP corpus used in training had ≥ 150 examples (OGI-INV-010). If corpus was built with fewer examples, Gate 6 must be invalidated and re-run after corpus rebuild.

---

## Pipeline Architecture (Gate C)

```
[Gate B CLEARED — FINAL_RISK_MATRIX.md]
                │
                ▼
        ┌───────────────────────────────────────────────┐
        │  Phase 1: prepare_corpus.py                   │
        │  → train.jsonl · val.jsonl · test.jsonl       │
        │  → manifest.json · rejected_samples.jsonl     │
        └──────────────┬────────────────────────────────┘
                       │                    │
                       ▼                    ▼
        ┌──────────────────┐   ┌────────────────────────┐
        │  Phase 2:        │   │  Phase 3: Together.ai  │
        │  generate_       │   │  Fine-Tune             │
        │  ontology.py     │   │  → trained model       │
        │  → ontology.json │   │  → together_job_id     │
        └────────┬─────────┘   └────────────┬───────────┘
                 │                          │
                 └──────────────┬───────────┘
                                ▼
        ┌───────────────────────────────────────────────┐
        │  Phase 4: eval_suite_generator.py             │
        │  → eval_suite.jsonl                           │
        │  → run against model endpoint                 │
        │  → capture responses                          │
        └──────────────┬────────────────────────────────┘
                       │
                       ▼
        ┌───────────────────────────────────────────────┐
        │  Phase 5: 7-Gate Evaluation                   │
        │  Gate 1: factual_accuracy ≥ 0.90              │
        │  Gate 2: citation_f1 ≥ 0.92  ← needs κ ≥ 0.80│
        │  Gate 3: verdict_acc ≥ 0.85                   │
        │  Gate 3b: halt_recall ≥ 0.80                  │
        │  Gate 4: hallucination ≤ 0.03 ← needs ontology│
        │  Gate 5: refusal ≥ 0.95 (bilateral)           │
        │  Gate 6: mivp_acc ≥ 0.80 ← needs MIVP corpus │
        └──────────────┬────────────────────────────────┘
                       │
                       ▼
        ┌───────────────────────────────────────────────┐
        │  Phase 6: Inter-Annotator Agreement           │
        │  INV + SCN + MIVP · Cohen's κ ≥ 0.80         │
        │  → unblocks Gate 2 if κ was pending           │
        └──────────────┬────────────────────────────────┘
                       │
                       ▼
        ┌───────────────────────────────────────────────┐
        │  Phase 7: Production Deployment               │
        │  Railway: OMNIX_OGI_MODEL_ENDPOINT set        │
        │  OMNIX_AI_SOVEREIGN_MODE=true                 │
        │  Smoke test → verify OMNIX vocabulary present │
        └──────────────┬────────────────────────────────┘
                       │
              ┌────────┴─────────┐
              │                  │
              ▼                  ▼
       [OGI ACTIVE]         [ROLLBACK]
       SAL chain:           Remove endpoint →
       OGI → Groq →         Groq becomes primary
       Mistral → Gemini →   Zero downtime
       OpenAI → Anthropic
```

---

## Environment Variables (Gate C — New)

| Variable | Where | Description |
|---|---|---|
| `OMNIX_OGI_MODEL_ENDPOINT` | Railway | Together.ai inference endpoint — activates OGI in SAL |
| `OMNIX_OGI_MODEL_NAME` | Railway | Fine-tuned model name (e.g., `harold-nunes/ogi-llama3-8b-v1`) |
| `TOGETHER_API_KEY` | Railway | Together.ai API key for training and inference |
| `OMNIX_AI_SOVEREIGN_MODE` | Railway | `true` = Groq-first chain; OGI becomes primary when endpoint is set |

---

## Consequences

**Positive:**
- OMNIX becomes the only AI governance platform with a domain-expert model that natively speaks its own protocol
- OGI eliminates hallucinations on OMNIX vocabulary in all SAL responses
- Gate 6 makes MIVP evaluation capability a verifiable deployment gate — not a marketing claim
- The `eval_results.json` audit trail satisfies EU AI Act Article 9 documentation requirements for the AI model used in the governance runtime itself

**Negative:**
- Gate C execution requires ~4–6 hours total (corpus generation + training + evaluation + annotation)
- Fine-tuning costs $20–240 per run depending on model tier
- Every major protocol change (new RFC, new invariant family) requires re-training

**Mitigations:**
- `prepare_corpus.py` is fully automated — corpus rebuild is a one-command operation
- `training_config.yaml` canonicalizes all parameters — no manual configuration needed
- `OMNIX_OGI_MODEL_ENDPOINT` empty = instant fallback — zero downtime on rollback
- Re-training cost is fixed and predictable; it does not scale with usage

---

*Cross-referenced by: ADR-193 (OGI corpus) · ADR-190 (SAL) · ADR-194 (MIVP) · FINAL_RISK_MATRIX.md · OGI_SPEC.md · OGI_ONEPAGER.md*
