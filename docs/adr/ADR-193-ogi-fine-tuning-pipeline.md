# ADR-193 — OMNIX Governance Intelligence (OGI) Fine-Tuning Pipeline & Corpus Governance

**Status:** Accepted
**Author:** Harold Nunes
**Date:** 2026-05-25
**Related:** ADR-190 (SAL — Sovereign AI Layer), ADR-184 (OGR), ADR-181/182/183 (BEV)
**RFC:** RFC-ATF-6 (Behavioral Execution Verification — corpus foundation)

---

## Context

The OMNIX Sovereign AI Layer (ADR-190) introduced Groq/Llama-3 and Mistral as
provider-independent AI backends. These are commodity open-source models with no
knowledge of the OMNIX protocol, invariants, or governance vocabulary.

The next evolution is **OMNIX Governance Intelligence (OGI)** — a domain-expert model
fine-tuned on the entire OMNIX corpus:

- 192 Architecture Decision Records (ADRs)
- 6 published RFCs (RFC-ATF-1 through RFC-ATF-6)
- 51 formal invariants across 10 invariant families
- ATF vocabulary: 200+ canonical terms (DR, TAR, RCR, BAR, CCS, CTCHC, OGR, PoGC, AVM, AGVP, DSPP…)

A model trained on this corpus can:
1. Answer governance protocol questions with citation-grounded accuracy
2. Evaluate agent scenarios and produce CONFORMANT/WARNING/CRITICAL/HALT verdicts
3. Explain invariant violations with counterexamples
4. Map client use cases to the correct ATF layer without hallucination
5. Produce executive briefs that accurately reflect the OMNIX architecture

> **Corpus count (updated automatically):** 194 ADRs · 55+ active invariants across 11 families (ATF · TAR · RGC · GPIL · ELR · EAP · OEP · FEA · FVP · GECR · MIVP) · RFC-ATF-1 through RFC-ATF-6. Update this line after each ADR addition.

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

### OGI-003: Corpus Taxonomy — 12 Example Categories

| Category | Code | Description | Target Count (MVP) |
|---|---|---|---|
| Normative Definition | `DEF` | "What is X?" for all canonical terms | 400 |
| Source Location | `SRC` | "Which ADR/RFC defines X?" + section | 300 |
| Scenario → Verdict | `SCN` | Input scenario → CONFORMANT/WARNING/CRITICAL/HALT | 800 |
| Invariant Explanation | `INV` | Full invariant + counterexample + consequences | 300 |
| API Procedure | `API` | Step-by-step OGR session flows (start/turn/close/proof) | 200 |
| Cross-Layer Traceability | `TRC` | Trace a decision through ATF L0–L5 | 200 |
| Competitive Analysis | `CMP` | OMNIX vs CLARIXO / MTCP / VeriSigil | 100 |
| Regulatory Mapping | `REG` | EU AI Act / NIST / OHADA / SAMA ↔ OMNIX artifacts | 200 |
| Forensic Walkthrough | `FOR` | Offline verification step-by-step | 150 |
| Red-Team Refusal | `RTR` | Out-of-scope requests → explicit refusal with reason | 150 |
| Terminology Normalization | `TRM` | Acronym disambiguation, canonical names | 200 |
| Executive Brief | `EXB` | Institutional summary for non-technical audience | 200 |
| **Total MVP** | | | **~3,200** |

Premium target: 15,000–30,000 examples (full ADR coverage × all categories).

### OGI-004: OMNIX System Prompt (Canonical)

The OGI system prompt is the single source of truth for model persona and scope.
It is stored at `scripts/fine_tuning/ogi_system_prompt.txt` and injected into
every training example and every runtime inference call when
`OMNIX_AI_SOVEREIGN_MODE=true` and the OGI model is active.

### OGI-005: Corpus Security Controls

**CRITICAL — Architect finding:** Training on the full repository without filtering
risks leaking partner information, NDA content, proprietary prompts, API keys, or PII.

Mandatory controls:
- `corpus_allowlist.yaml` — explicit list of files approved for training
- Automatic secret redaction (regex scan for key patterns before JSONL generation)
- PII scanner (email addresses, phone numbers, individual names except Harold Nunes as author)
- `rejected_samples.jsonl` — all rejected samples logged for audit

### OGI-006: Train/Val/Test Split

| Split | Ratio | Purpose |
|---|---|---|
| `train.jsonl` | 80% | Fine-tuning |
| `val.jsonl` | 10% | Loss monitoring during training |
| `test.jsonl` | 10% | Post-training evaluation (never seen during training) |

Split is **stratified by category** — each category maintains 80/10/10 ratio.

### OGI-007: Evaluation Gates (Must Pass Before Deployment)

| Metric | Target | Measurement |
|---|---|---|
| Factual accuracy (invariant codes) | ≥ 90% | `eval_suite.jsonl` factuality block |
| Invariant-citation F1 | ≥ 0.92 | Citation precision/recall |
| Scenario → Verdict accuracy | ≥ 85% | SCN category test set |
| Hallucination rate | ≤ 3% | Auto-checked against canonical ontology |
| Refusal correctness | ≥ 95% | RTR category test set |

If any gate fails, the model is NOT deployed to SAL. The prior Groq/Mistral chain
remains active until a passing model is available (OGI-INV-009).

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
all five evaluation gates (OGI-007). Gate results are stored in `eval_results.json`.

### OGI-INV-009 — SAL Compatibility
The OGI model endpoint MUST be OpenAI API-compatible (Together.ai deployed models
expose this interface). Integration requires only changing model name in SAL config.

### OGI-INV-010 — Rollback Required
Every OGI deployment MUST document the rollback procedure: reverting
`OMNIX_OGI_MODEL_ENDPOINT` to empty restores the standard Groq/Mistral chain.

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
