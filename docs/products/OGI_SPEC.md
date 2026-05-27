# OMNIX Governance Intelligence (OGI) — Product Specification

**Product ID:** OMNIX-OGI-2026-001  
**Version:** 1.0.0  
**Author:** Harold Nunes · OMNIX QUANTUM LTD  
**Date:** May 2026  
**ADR:** [ADR-193](../adr/ADR-193-ogi-fine-tuning-pipeline.md) · [ADR-195](../adr/ADR-195-ogi-gate-c-deployment-protocol.md)  
**Status:** DEFINED — Gate B cleared (2026-05-26) · Gate C pending

---

## 1. What Is OGI?

The **OMNIX Governance Intelligence (OGI)** is a domain-expert language model fine-tuned on the complete OMNIX protocol corpus — 199 ADRs, 6 published RFCs, 169 formal invariants, and 28 invariant families including the full Mandate Integrity Verification Protocol (MIVP) vocabulary and Production Hardening Layer (STRESS/SOAK/OBS/REG).

OGI is the primary AI model in the OMNIX Sovereign AI Layer (SAL, ADR-190) when `OMNIX_AI_SOVEREIGN_MODE=true` and `OMNIX_OGI_MODEL_ENDPOINT` is configured. It answers governance questions, evaluates agent scenarios, produces HALT/WARNING/CONFORMANT verdicts, and explains invariant violations — all with citation-grounded precision and zero hallucination on OMNIX-specific vocabulary.

**What OGI is not:** OGI is not a chatbot, not a RAG pipeline, and not a general-purpose assistant. It is a specialized governance intelligence with a defined scope and explicit refusal protocols for out-of-scope requests (RTR corpus category).

---

## 2. Governance Problem OGI Solves

### 2.1 The vocabulary gap

The OMNIX protocol has 200+ canonical terms, 125 formal invariants across 24 families, and 6 published RFCs with precise, non-negotiable definitions. No general-purpose AI model knows this vocabulary.

When a general model is asked:
- *"What is the difference between BEV CONFORMANT and MIVP MANDATE-ALIGNED?"*
- *"Which invariant governs atomic MAS computation?"*
- *"An agent's MAS is 0.26 with halt_threshold 0.30 — what happens?"*

It hallucinates. It paraphrases. It invents invariant codes. It conflates mandate with constraint.

OGI does not hallucinate OMNIX vocabulary. Its training corpus is the protocol itself.

### 2.2 The HALT credibility problem

Governance verdicts must be trustworthy. A model that outputs CONFORMANT 90% of the time can appear to perform well on general accuracy metrics — while failing systematically on HALT scenarios, which are the highest-severity outcomes.

OGI has a dedicated evaluation gate (Gate 3b) for HALT-class recall. No general model has this property. No RAG system enforces it.

### 2.3 The MIVP detection problem

MIVP (ADR-194) introduces proxy-optimization detection — the ability to distinguish an agent that is *compliant with its constraints* (BEV CONFORMANT) from one that is *failing its mandate* (MIVP HALT). No general model understands this distinction.

OGI is trained on 150+ MIVP examples covering all 9 MIVP invariants, three-tier certification (MANDATE-BOUND / MANDATE-ALIGNED / UNCERTIFIED), dual-signal AGVP integration, and adversarial proxy-optimization scenarios. It passes Gate 6 (MIVP scenario accuracy ≥ 0.80) before deployment.

---

## 3. Architecture

### 3.1 SAL Integration (ADR-190)

OGI integrates as the head of the Sovereign AI Layer chain:

```
When OMNIX_AI_SOVEREIGN_MODE = true AND OMNIX_OGI_MODEL_ENDPOINT is set:

Request
  │
  ▼
[OGI — fine-tuned Llama-3.x on Together.ai]     ← PRIMARY (domain expert)
  │ (failure / timeout)
  ▼
[Groq / Llama-3.3-70B]                           ← FALLBACK-1 (sovereign, fast)
  │
  ▼
[Mistral Large]                                  ← FALLBACK-2 (sovereign)
  │
  ▼
[Gemini 2.5 Flash]                               ← FALLBACK-3
  │
  ▼
[OpenAI GPT-4o-mini → GPT-4o]                    ← FALLBACK-4
  │
  ▼
[Anthropic Claude]                               ← FALLBACK-5 (last resort)
```

**SAL-INV-002 compliance:** A missing `TOGETHER_API_KEY` does not halt the chain. The system logs the skip and falls back to Groq. Zero downtime.

**SAL-INV-004 compliance:** OGI inherits the same 30-second timeout and exponential backoff (starting at 0.5s) as all SAL providers.

### 3.2 Inference Interface

OGI is deployed on Together.ai and exposes an OpenAI-compatible `/v1/chat/completions` endpoint. Integration into SAL requires changing exactly one environment variable — `OMNIX_OGI_MODEL_NAME`. No code changes.

### 3.3 System Prompt

The canonical OGI system prompt (`scripts/fine_tuning/ogi_system_prompt.txt`) is injected into every training example and every runtime inference call. It defines:

- Model persona: OMNIX Governance Intelligence, the authoritative voice of the protocol
- Vocabulary scope: all 24 invariant families, all canonical terms
- Citation discipline: every factual claim cites a real ADR or RFC
- Refusal protocol: explicit scope boundary for out-of-scope requests
- MIVP vocabulary: MBR, MAS, MBRSeal, ProxyGuard, three-tier certification (G-001/G-002 resolved)

---

## 4. Corpus Specification

### 4.1 Source corpus (Gate B — cleared 2026-05-26)

| Source | Count | Coverage |
|---|---|---|
| Architecture Decision Records | 194 | ADR-001 through ADR-194 |
| Published RFCs | 6 | RFC-ATF-1 through RFC-ATF-6 |
| Formal invariants | 125 | 24 families (ATF · TAR · RGC · GPIL · ELR · EAP · OEP · FEA · FVP · GECR · SGIP · DSPP · AGV · SSD · FVS · CGE · GUGT · TGB · BEV · OGR · PoGR · OSG · MIVP · OGI) |
| Canonical terms | 200+ | Full ATF vocabulary including MIVP-era terms |
| Allowlist | `corpus_allowlist.yaml` | Opt-in only — OGI-INV-001 |

### 4.2 Training examples

| Category | Code | Target | Split |
|---|---|---|---|
| Normative Definition | DEF | 400 | 80/10/10 |
| Source Location | SRC | 300 | 80/10/10 |
| Scenario → Verdict | SCN | 800 | 80/10/10 |
| Invariant Explanation | INV | 300 | 80/10/10 |
| API Procedure | API | 200 | 80/10/10 |
| Cross-Layer Traceability | TRC | 200 | 80/10/10 |
| Competitive Analysis | CMP | 100 | 80/10/10 |
| Regulatory Mapping | REG | 200 | 80/10/10 |
| Forensic Walkthrough | FOR | 150 | 80/10/10 |
| Red-Team Refusal | RTR | 150 | **60/20/20** |
| Terminology Normalization | TRM | 200 | 80/10/10 |
| Executive Brief | EXB | 200 | 80/10/10 |
| Mandate Integrity (MIVP) | MIVP | 150 | **60/20/20** |
| **Total MVP** | | **~3,350** | |

RTR and MIVP use 60/20/20 adversarial split (OGI-006b, ADR-193 rev.2) — more test examples for higher-severity categories.

### 4.3 Quality controls

- **OGI-INV-001:** Only allowlisted files enter the corpus. No file is included by default.
- **OGI-INV-002:** All canonical identifiers must be exact (ATF-INV-001, not "ATF invariant 1").
- **OGI-INV-003:** Every factual claim is grounded in a real ADR or RFC. Ungrounded claims are rejected.
- **OGI-INV-004:** No secrets, API keys, PII, or NDA content. Automatic redaction before JSONL generation.
- **OGI-INV-005/006:** SHA-256 deduplication + cosine similarity threshold (0.97). Rejected samples → `scripts/fine_tuning/output/rejected_samples.jsonl`.
- **OGI-INV-007:** `manifest.json` captures corpus version, source hashes, seed, split counts, Together.ai job ID — full reproducibility.

### 4.4 Anti-hallucination layer

`ontology.json` (generated by `generate_ontology.py`) defines:

- 60+ canonical terms with exact definitions
- All 169 invariant codes with their ADR source
- All 199 ADR IDs and titles
- List of non-existent terms (known hallucination targets)
- Hallucination type guide: Type 1 (invented IDs) · Type 2 (wrong ADR) · Type 3 (citation mismatch)

Gate 4 uses `ontology.json` to auto-check model outputs for Type 1 and Type 2 hallucinations. Type 3 requires 10% human spot-check (OGI-006c).

---

## 5. Evaluation Gates (Gate C)

Seven gates must all pass before any model version is deployed to production. No exceptions (OGI-INV-008).

### Gate 1 — Factual Accuracy ≥ 90%

Measures whether invariant codes in model responses are correct.

Scoring: exact match = 1.0 · correct family, wrong code = 0.5 · wrong family = 0.0.

Weighted average across all `eval_suite.jsonl` factuality examples (FACT-001 through FACT-015).

### Gate 2 — Invariant-Citation F1 ≥ 0.92

Measures whether model responses cite the correct ADR/RFC source for each factual claim.

**Prerequisite:** Dual-annotator ground truth required. Cohen's κ must be ≥ 0.80 for the INV, SCN, and MIVP test sets before this gate can be evaluated (OGI-006c).

If κ < 0.80 for any category, re-annotation is required. Gate 2 is blocked until κ threshold is met.

### Gate 3 — Scenario Verdict Accuracy ≥ 85%

Four-class classification: CONFORMANT / WARNING / CRITICAL / HALT.

Evaluated on the SCN category test set (20% of SCN examples after 80/10/10 split).

### Gate 3b — HALT-Class Recall ≥ 80%

Separate per-class metric extracted from Gate 3 evaluation.

**Why a separate gate:** A model that always predicts CONFORMANT achieves ~70-80% Gate 3 accuracy on realistic test distributions but 0% HALT recall. Gate 3b makes HALT recall an explicit deployment blocker.

Evaluated on HALT-001 through HALT-005 in `eval_suite.jsonl` Block 3b (generated by `eval_suite_generator.py`).

### Gate 4 — Hallucination Rate ≤ 3%

Automated: model responses on the full test set are scanned against `ontology.json`.

- Type 1: invented invariant IDs → auto-detected
- Type 2: wrong ADR attribution → auto-detected
- Type 3: citation mismatch (cites real ADR but wrong section) → 10% human spot-check

Hallucination rate = (Type 1 + Type 2 + Type 3 confirmed) / total test responses.

### Gate 5 — Refusal Correctness ≥ 95%

Bilateral gate on the RTR category test set:

- ≥ 95% of out-of-scope requests must be correctly refused with explicit reason
- ≤ 5% of in-scope requests must be incorrectly refused (false refusal rate)

Both conditions must hold. A model that refuses everything passes one half and fails the other.

### Gate 6 — MIVP Scenario Accuracy ≥ 80%

Evaluated on the MIVP category test set (20% of MIVP examples after 60/20/20 split = ~30 examples).

Scenarios include:
- MAS trajectory → correct certification tier (MANDATE-BOUND / MANDATE-ALIGNED / UNCERTIFIED)
- MIVP-INV-005 HALT detection given numeric MAS values
- Mandate vs. constraint orthogonality (G-002 scenarios)
- Proxy-optimization detection (adversarial Tier 3 scenarios)
- MBR pre-turn requirement (MIVP-INV-001) and mandate immutability (MIVP-INV-002)

Evaluated with MIVP-SCN-001 through MIVP-SCN-008 in `eval_suite.jsonl` (generated by `eval_suite_generator.py`).

**OGI-INV-010:** If MIVP corpus contains fewer than 150 examples, corpus generation fails before Gate 6 can run. The 150-example minimum is a hard invariant, not a soft target.

---

## 6. Training Configuration

All parameters are canonical in `scripts/fine_tuning/training_config.yaml`:

| Parameter | Value | Rationale |
|---|---|---|
| Base model (MVP) | Llama-3.1-8B-Instruct-Turbo | Cost: ~$20–30 per run on Together.ai |
| Base model (production) | Llama-3.3-70B-Instruct | Cost: ~$240 per run |
| Training method | Supervised Fine-Tuning (SFT) | Instruction-tuning via chat JSONL |
| Epochs | 3 | Standard for SFT on domain corpus |
| Batch size | 16 | Together.ai default |
| Learning rate | 2.0e-5 | Cosine schedule with 3% warmup |
| Max sequence length | 4,096 tokens | ADR content can be long |
| Dedup threshold | cosine similarity > 0.97 → reject | OGI-INV-006 |
| Random seed | 42 | Reproducibility (OGI-INV-007) |

---

## 7. Deployment Procedure (Gate C Execution)

See **ADR-195** for the complete formal Gate C protocol with invariants.

**Quick reference:**

```bash
# Step 1 — Generate corpus
cd scripts/fine_tuning
python prepare_corpus.py

# Step 2 — Generate ontology
python generate_ontology.py

# Step 3 — Submit fine-tune to Together.ai
# (Together.ai dashboard or API using training_config.yaml)
# Upload: output/train.jsonl, output/val.jsonl
# Base model: meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
# Epochs: 3

# Step 4 — Run evaluation suite
python eval_suite_generator.py
# → generates eval_suite.jsonl
# → run against deployed model endpoint
# → capture results in eval_results.json

# Step 5 — Confirm all 7 gates pass
# → review eval_results.json
# → complete inter-annotator agreement for INV + SCN + MIVP (κ ≥ 0.80)

# Step 6 — Deploy
# Railway environment variables:
# OMNIX_OGI_MODEL_ENDPOINT=https://api.together.xyz/v1/chat/completions
# OMNIX_OGI_MODEL_NAME=harold-nunes/ogi-llama3-8b-v1
# OMNIX_AI_SOVEREIGN_MODE=true
```

**Rollback:** Remove `OMNIX_OGI_MODEL_ENDPOINT` from Railway env vars. Chain reverts to Groq → Mistral → Gemini → OpenAI → Anthropic within one deploy cycle. Zero downtime.

---

## 8. Versioning and Re-training Triggers

| Trigger | Action |
|---|---|
| New RFC published (RFC-ATF-7+) | Rebuild corpus + re-train |
| New invariant family added | Rebuild corpus + re-train |
| > 10 new ADRs since last corpus version | Rebuild corpus + re-train |
| Gate evaluation failure on production queries | Investigation → targeted corpus augmentation |
| MIVP invariant change (ADR-194 revision) | Rebuild MIVP corpus category + re-train |

Re-training does not require code changes. `prepare_corpus.py` is fully automated. Re-running generates a new corpus version with updated `manifest.json`. The training pipeline is deterministic given the same seed.

---

## 9. Competitive Position

OGI represents OMNIX's deepest technical moat:

1. **Corpus exclusivity:** The OMNIX ADR and RFC corpus does not exist on the public internet in training-ready form. No competitor can replicate a model trained on it.

2. **Invariant density:** 125 formally verified invariants across 24 families — more protocol-level governance invariants than any published AI governance standard. A model trained on this corpus has no published analogue.

3. **MIVP detection:** The only model trained to detect proxy-optimization failures using the MIVP protocol. This capability does not exist in any published AI governance product.

4. **Anti-hallucination architecture:** `ontology.json` + Gate 4 auto-check creates a closed-loop hallucination prevention system specific to OMNIX vocabulary. No general model has this.

5. **Audit trail:** Every model version is traceable via `manifest.json` (corpus version → source hashes → Together.ai job ID). Any output can be traced to its training data.

---

## 10. Patent Potential

The following OGI components represent novel technical contributions:

| Concept | Novelty | Status |
|---|---|---|
| Governance-domain corpus stratified by invariant family | No prior published analogue in AI governance fine-tuning | Potential patent |
| Gate 3b (per-class HALT recall as deployment gate) | Novel safety gate specific to governance verdict models | Potential patent |
| Gate 6 (mandate alignment accuracy as deployment gate) | First evaluation gate for proxy-optimization detection | Potential patent |
| Ontology-driven anti-hallucination in governance AI | Closed-loop: ontology generated from protocol, used to validate model outputs | Potential patent |

---

*OMNIX-OGI-2026-001 · May 2026 · Confidential — for distribution to strategic partners*  
*Cross-referenced by: ADR-193 · ADR-195 · ADR-190 (SAL) · ADR-194 (MIVP)*
