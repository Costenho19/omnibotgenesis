# ADR-193 — OMNIX Governance Intelligence (OGI) Fine-Tuning Pipeline & Corpus Governance

**Status:** Accepted (rev.2 — 2026-05-26)
**Author:** Harold Nunes
**Date:** 2026-05-25
**Related:** ADR-190 (SAL — Sovereign AI Layer), ADR-184 (OGR), ADR-181/182/183 (BEV), ADR-194 (MIVP)
**RFC:** RFC-ATF-6 (Behavioral Execution Verification — corpus foundation)

**Revision history:**
- rev.1 (2026-05-25): Initial ADR — OGI-INV-001–010, 12 corpus categories, 5 evaluation gates
- rev.2 (2026-05-26): B-001 resolved (Gate 3b HALT recall), B-002 resolved (inter-annotator protocol), F-C-004 resolved (adversarial split 60/20/20), F-C-005 resolved (MIVP 13th corpus category), F-C-007 resolved (canonical rejected_samples path), OGI-006b + OGI-006c + Gate 6 (MIVP) added, invariant counts updated to 125 / 13 families + OGI

---

## Context

The OMNIX Sovereign AI Layer (ADR-190) introduced Groq/Llama-3 and Mistral as
provider-independent AI backends. These are commodity open-source models with no
knowledge of the OMNIX protocol, invariants, or governance vocabulary.

The next evolution is **OMNIX Governance Intelligence (OGI)** — a domain-expert model
fine-tuned on the entire OMNIX corpus:

- 194 Architecture Decision Records (ADRs)
- 6 published RFCs (RFC-ATF-1 through RFC-ATF-6)
- **125 formal invariants across 24 invariant families** (ATF · TAR · RGC · GPIL · ELR · EAP · OEP · FEA · FVP · GECR · SGIP · DSPP · AGV · SSD · FVS · CGE · GUGT · TGB · BEV · OGR · PoGR · OSG · MIVP · OGI)
- ATF vocabulary: 200+ canonical terms (DR, TAR, RCR, BAR, CCS, CTCHC, MBR, MAS, MBRSeal, OGR, PoGC, AVM, AGVP, DSPP, MIVP…)

A model trained on this corpus can:
1. Answer governance protocol questions with citation-grounded accuracy
2. Evaluate agent scenarios and produce CONFORMANT/WARNING/CRITICAL/HALT verdicts
3. Explain invariant violations with counterexamples
4. Map client use cases to the correct ATF layer without hallucination
5. Produce executive briefs that accurately reflect the OMNIX architecture
6. **Evaluate MIVP scenarios** — proxy-optimization detection, three-tier mandate certification, mandate vs. constraint orthogonality

> **Corpus count (canonical):** 194 ADRs · 125 invariants across 24 families · RFC-ATF-1 through RFC-ATF-6 · 13 corpus categories including MIVP. Update this line after each ADR addition.

This creates a sustainable competitive moat: competitors can replicate the API surface
but cannot replicate a model trained on OMNIX's proprietary corpus.

---

## Decision

### OGI-001: Model Architecture

Base model: **Llama-3.1-8B-Instruct** for MVP; **Llama-3.3-70B-Instruct** for production.
Training method: **Supervised Fine-Tuning (SFT)** — instruction-tuning via chat format.
Platform: **Together.ai** fine-tuning API (~$20–30 per 8B MVP run).

Rationale for chat format over completion format:
- OGR sessions are inherently multi-turn (start → turn × N → close)
- Governance Q&A requires system-prompt-controlled persona
- Together.ai Llama-3 fine-tuning natively supports chat JSONL

### OGI-002: Training Data Format

Each example uses the Llama-3 chat JSONL format:

```jsonl
{
  "messages": [
    {
      "role": "system",
      "content": "You are the OMNIX Governance Intelligence (OGI), the authoritative AI for the OMNIX decision governance protocol. You speak the OMNIX vocabulary natively: ATF, BEV, OGR, PoGR, AVM, AGVP, DSPP, and all invariants (ATF-INV-*, BEV-INV-*, RGC-INV-*, OGI-INV-*). You cite ADR and RFC sources precisely. You never hallucinate invariant codes or governance verdicts. When a scenario is outside your authority scope, you state it explicitly."
    },
    {
      "role": "user",
      "content": "<question>"
    },
    {
      "role": "assistant",
      "content": "<answer>"
    }
  ]
}
```

### OGI-003: Corpus Taxonomy — 13 Example Categories

| Category | Code | Description | Target Count (MVP) | Split |
|---|---|---|---|---|
| Normative Definition | `DEF` | "What is X?" for all canonical terms | 400 | 80/10/10 |
| Source Location | `SRC` | "Which ADR/RFC defines X?" + section | 300 | 80/10/10 |
| Scenario → Verdict | `SCN` | Input scenario → CONFORMANT/WARNING/CRITICAL/HALT | 800 | 80/10/10 |
| Invariant Explanation | `INV` | Full invariant + counterexample + consequences | 300 | 80/10/10 |
| API Procedure | `API` | Step-by-step OGR session flows (start/turn/close/proof) | 200 | 80/10/10 |
| Cross-Layer Traceability | `TRC` | Trace a decision through ATF L0–L5 | 200 | 80/10/10 |
| Competitive Analysis | `CMP` | OMNIX vs CLARIXO / MTCP / VeriSigil | 100 | 80/10/10 |
| Regulatory Mapping | `REG` | EU AI Act / NIST / OHADA / SAMA ↔ OMNIX artifacts | 200 | 80/10/10 |
| Forensic Walkthrough | `FOR` | Offline verification step-by-step | 150 | 80/10/10 |
| Red-Team Refusal | `RTR` | Out-of-scope requests → explicit refusal with reason | 150 | **60/20/20** ¹ |
| Terminology Normalization | `TRM` | Acronym disambiguation, canonical names | 200 | 80/10/10 |
| Executive Brief | `EXB` | Institutional summary for non-technical audience | 200 | 80/10/10 |
| **Mandate Integrity** | **`MIVP`** | **MIVP scenarios: proxy-optimization, MBR/MAS/MBRSeal, three-tier certification** | **150** | **60/20/20** ¹ |
| **Total MVP** | | | **~3,350** | |

¹ **Adversarial categories (RTR, MIVP) use 60/20/20** — see OGI-006b. The harder the category, the more test examples needed for reliable evaluation signal.

Premium target: 15,000–30,000 examples (full ADR coverage × all categories).

**OGI-INV-010:** MIVP category MUST reach ≥ 150 examples before Gate 6 (MIVP scenario accuracy) is evaluated.

### OGI-004: OMNIX System Prompt (Canonical)

The OGI system prompt is the single source of truth for model persona and scope.
It is stored at `scripts/fine_tuning/ogi_system_prompt.txt` and injected into
every training example and every runtime inference call when
`OMNIX_AI_SOVEREIGN_MODE=true` and the OGI model is active.

### OGI-005: Corpus Security Controls

**CRITICAL — Architect finding:** Training on the full repository without filtering
risks leaking partner information, NDA content, proprietary prompts, API keys, or PII.

Mandatory controls:
- `corpus_allowlist.yaml` — explicit list of files approved for training (`scripts/fine_tuning/corpus_allowlist.yaml`)
- Automatic secret redaction (regex scan for key patterns before JSONL generation)
- PII scanner (email addresses, phone numbers, individual names except Harold Nunes as author)
- `rejected_samples.jsonl` — **canonical path: `scripts/fine_tuning/output/rejected_samples.jsonl`** (F-C-007) — all rejected samples logged with reason, category, source ADR, and fingerprint

### OGI-006: Train/Val/Test Split

**Standard categories (80/10/10):**

| Split | Ratio | Purpose |
|---|---|---|
| `train.jsonl` | 80% | Fine-tuning |
| `val.jsonl` | 10% | Loss monitoring during training |
| `test.jsonl` | 10% | Post-training evaluation (never seen during training) |

Split is **stratified by category** — each standard category maintains 80/10/10 ratio.

### OGI-006b: Adversarial Split Override (F-C-004 resolution)

Adversarial categories (RTR and MIVP) use a **60/20/20** split:

| Split | Ratio | Rationale |
|---|---|---|
| `train.jsonl` | 60% | Sufficient adversarial training signal |
| `val.jsonl` | 20% | Better generalization monitoring |
| `test.jsonl` | 20% | Reliable evaluation signal for hardest examples |

**Rationale:** A model that underperforms on adversarial scenarios (proxy-optimization, red-team refusals)
must fail evaluation with high statistical confidence. 10% test coverage is insufficient for categories
with ≤ 150 examples — 20% test set yields ~30 examples per adversarial category, adequate for Gate 3b
(HALT-class recall ≥ 80%) and Gate 6 (MIVP scenario accuracy ≥ 80%) to be statistically meaningful.

Implementation: `stratified_split()` in `prepare_corpus.py` checks `ex.category in adversarial_categories`
and applies the override ratio. Logged at runtime: `"Adversarial split (60/20/20) applied to: [RTR, MIVP]"`.

### OGI-006c: Inter-Annotator Agreement Protocol (B-002 resolution)

Ground truth labels for INV, SCN, and MIVP categories require dual annotation:

| Requirement | Value | Rationale |
|---|---|---|
| Minimum annotators | 2 | Single annotator introduces systematic bias |
| Cohen's κ threshold | ≥ 0.80 | Below this: re-annotate before F1 gate computation |
| Spot-check (Type 3 hallucinations) | 10% of test responses | Citation mismatch requires human review |

**Process:**
1. Annotator A labels the full test set for INV, SCN, MIVP categories
2. Annotator B independently labels the same set
3. Cohen's κ is computed for each category
4. Categories with κ < 0.80 are flagged for re-annotation — Gate 2 (F1 ≥ 0.92) cannot be evaluated until κ ≥ 0.80
5. For Gate 4 (hallucination), automated check covers Type 1 and 2 (invented IDs vs. `ontology.json`); 10% human spot-check covers Type 3 (citation mismatch)

### OGI-007: Evaluation Gates (Must Pass Before Deployment)

| Gate | Metric | Target | Measurement |
|---|---|---|---|
| Gate 1 | Factual accuracy (invariant codes) | ≥ 90% | Weighted: exact=1.0, right family=0.5, wrong=0.0 |
| Gate 2 | Invariant-citation F1 | ≥ 0.92 | Dual-annotator labels required (κ ≥ 0.80) |
| Gate 3 | Scenario → Verdict accuracy | ≥ 85% | SCN category test set (4-class: CONFORMANT/WARNING/CRITICAL/HALT) |
| **Gate 3b** | **HALT-class recall** | **≥ 0.80** | **Per-class recall for HALT verdict — B-001 resolution** |
| Gate 4 | Hallucination rate | ≤ 3% | Auto-checked vs. `ontology.json` (Types 1+2); 10% human spot-check (Type 3) |
| Gate 5 | Refusal correctness | ≥ 95% | Bilateral: ≥95% correct refusal AND ≤5% false refusal |
| **Gate 6** | **MIVP scenario accuracy** | **≥ 0.80** | **MIVP category test set — proxy-optimization, three-tier certification** |

**Gate 3b rationale (B-001):** A model that always outputs CONFORMANT can pass Gate 3 (85% accuracy)
if the test set is dominated by CONFORMANT scenarios. Gate 3b enforces that HALT scenarios are
evaluated as a separate class — missed HALT has higher severity than missed CONFORMANT.
Implementation: `eval_suite_generator.py` Block 3b (HALT-001 through HALT-005).

**Gate 6 rationale:** MIVP introduces a new invariant family (MIVP-INV-001–009) with no prior model
training. Gate 6 ensures the model can evaluate proxy-optimization scenarios and correctly apply
three-tier mandate certification logic before deployment (OGI-INV-010).

If any gate fails, the model is NOT deployed to SAL. The prior Groq/Mistral chain
remains active until a passing model is available (OGI-INV-008).

---

## Invariants

### OGI-INV-001 — Source Allowlist
Every file contributing to the training corpus MUST appear in `corpus_allowlist.yaml`.
No file is included by default. Opt-in only.

### OGI-INV-002 — Canonical Term Integrity
Training examples MUST use canonical OMNIX identifiers (ATF-INV-001, BEV-INV-008,
etc.). No paraphrased or abbreviated invariant codes in assistant responses.

### OGI-INV-003 — Citation Grounding
Every factual claim in an assistant response MUST be grounded in a real ADR or RFC.
Ungrounded factual claims are rejected at QA gate.

### OGI-INV-004 — No Data Leakage
No secret, API key, PII, partner name under NDA, or proprietary prompt content
may appear in any training example. Violation triggers corpus rebuild.

### OGI-INV-005 — Split Purity
No example may appear in both train and val/test. Deduplication is SHA-256 based
on the full messages array. Duplicates are logged to `rejected_samples.jsonl`.

### OGI-INV-006 — Deduplication Threshold
Examples with cosine similarity > 0.97 to any existing example are rejected.

### OGI-INV-007 — Reproducibility
`manifest.json` MUST include: corpus version, source file hashes, generation timestamp,
random seed, split counts, and Together.ai job ID. Allows exact corpus reproduction.

### OGI-INV-008 — Evaluation Gate Before Deployment
No OGI model version may be deployed to `OMNIX_AI_SOVEREIGN_MODE` without passing
all **seven** evaluation gates (OGI-007: Gates 1, 2, 3, 3b, 4, 5, 6). Gate results are stored in `eval_results.json`.

### OGI-INV-009 — SAL Compatibility
The OGI model endpoint MUST be OpenAI API-compatible (Together.ai deployed models
expose this interface). Integration requires only changing model name in SAL config.

### OGI-INV-010 — MIVP Corpus Minimum (F-C-005 resolution)
The MIVP corpus category MUST reach ≥ 150 examples before Gate 6 (MIVP scenario accuracy ≥ 0.80)
is evaluated. If `gen_MIVP()` produces fewer than 150 examples, corpus generation fails with an
explicit error. Rollback: reverting `OMNIX_OGI_MODEL_ENDPOINT` to empty restores the Groq/Mistral chain.

---

## Pipeline Architecture

```
docs/adr/*.md                    ┐
docs/standards/RFC-ATF-*.md      ├─→ [ingest] → [parse] → [chunk] → [generate]
corpus_allowlist.yaml            ┘
                                          ↓
                                   [dedup + sanitize]
                                          ↓
                               [stratified split 80/10/10]
                                          ↓
                             [QA gate — OGI-INV-001..007]
                                          ↓
               ┌──────────────────────────────────────────┐
               │  train.jsonl  val.jsonl  test.jsonl       │
               │  manifest.json  ontology.json             │
               │  eval_suite.jsonl  rejected_samples.jsonl │
               └──────────────────────────────────────────┘
                                          ↓
                              [Together.ai fine-tune API]
                                          ↓
                              [eval_suite → gate check]
                                          ↓
                         [deploy: OMNIX_OGI_MODEL_ENDPOINT]
```

---

## Environment Variables (New — ADR-193)

| Variable | Description |
|---|---|
| `OMNIX_OGI_MODEL_ENDPOINT` | Together.ai endpoint for deployed OGI model |
| `OMNIX_OGI_MODEL_NAME` | Model name (e.g., `harold-nunes/ogi-llama3-8b-v1`) |
| `TOGETHER_API_KEY` | Together.ai API key for fine-tuning and inference |

When `OMNIX_AI_SOVEREIGN_MODE=true` and `OMNIX_OGI_MODEL_ENDPOINT` is set,
the SAL chain becomes: **OGI → Groq/Llama-3 → Mistral → Gemini → OpenAI → Anthropic**.

---

## Consequences

**Positive:**
- OMNIX becomes the only governance platform with a domain-expert AI model
  trained exclusively on its own protocol corpus
- Eliminates hallucinations on OMNIX-specific vocabulary
- Creates a moat that deepens with every new ADR and RFC published
- Enables "OMNIX Certified" answers with citation traceability

**Negative:**
- Corpus preparation requires ~1–2 days of engineering work
- Fine-tuning costs ~$20–30 per 8B run on Together.ai
- Model must be re-trained when major protocol changes occur (new RFC, new invariant family)

**Mitigations:**
- `prepare_corpus.py` is fully automated — re-running generates updated corpus
- Versioning in `manifest.json` tracks corpus → model traceability
- `OMNIX_OGI_MODEL_ENDPOINT` empty = automatic fallback, zero downtime
