# OMNIX Governance Intelligence (OGI) — One Pager

**OMNIX QUANTUM LTD · Harold Nunes · May 2026**  
**omnixquantum.net · OMNIX-OGI-2026-001**

---

## The Problem

Enterprise AI deployments have a knowledge gap that no general-purpose model can close:

> *"Our AI governance platform speaks a domain language. Our AI model doesn't know it exists."*

GPT-4o doesn't know what a Mandate Binding Record is. Gemini doesn't know the difference between a CCS WARNING and a HALT. Llama-3 cannot tell you which ADR governs cross-domain trust delegation or whether an agent's output violates BEV-INV-008.

When your governance infrastructure is more sophisticated than the model interpreting it, you have a credibility gap — in regulatory submissions, in B2B sales, and in every client conversation where the protocol is challenged.

---

## The Solution

**OMNIX Governance Intelligence (OGI)** — the world's first AI model fine-tuned exclusively on a formal AI governance protocol corpus.

OGI is not a RAG system. It is not a chatbot with documents attached. It is a fine-tuned domain expert with 194 ADRs, 6 published RFCs, 125 formal invariants, and 13 corpus categories baked directly into its weights.

OGI knows the OMNIX protocol the way a senior engineer knows it — natively, precisely, without hallucination.

---

## What OGI Can Do That No General Model Can

```
General model asked "What is MIVP?"     → Hallucinates a definition.
OGI asked "What is MIVP?"              → Cites ADR-194. Explains the three-tier
                                          certification hierarchy. Names all 9 invariants.
                                          Distinguishes mandate from constraint.
                                          Gives a counterexample for MIVP-INV-005.

General model asked to evaluate:        → "This appears to be a compliance issue."
  "Agent: MAS = 0.26, MAS_halt = 0.30"

OGI asked the same:                     → "HALT — MIVP-INV-005 triggered. MAS 0.26 is
                                          below the halt threshold. Session must be
                                          suspended. turns_in_violation = 1. No MIVP
                                          tag on PoGC. AGVP watchdog should have issued
                                          PVR with reason MANDATE_DRIFT_PROJECTED at
                                          prior turn based on declining trajectory."
```

---

## The Architecture

OGI slots into the OMNIX Sovereign AI Layer (SAL, ADR-190) as the primary model — the first in the chain:

```
OMNIX_AI_SOVEREIGN_MODE = true
OMNIX_OGI_MODEL_ENDPOINT = set

AI chain:
  OGI (fine-tuned, Together.ai)
    → Groq / Llama-3.3-70B
    → Mistral Large
    → Gemini 2.5 Flash
    → OpenAI GPT-4o-mini
    → Anthropic Claude
```

OGI handles every governance question that falls within its training domain. The commodity chain only fires when OGI is unavailable — zero downtime, zero vendor lock-in.

**Rollback in 10 seconds:** Remove `OMNIX_OGI_MODEL_ENDPOINT` from Railway env vars. Chain reverts automatically.

---

## Training Corpus

| Dimension | Value |
|---|---|
| ADRs in corpus | 194 |
| RFCs in corpus | 6 (RFC-ATF-1 through RFC-ATF-6) |
| Invariants covered | 125 across 24 families |
| Corpus categories | 13 (DEF · SRC · SCN · INV · API · TRC · CMP · REG · FOR · RTR · TRM · EXB · MIVP) |
| Target examples (MVP) | ~3,350 |
| Premium target | 15,000–30,000 |
| Adversarial categories | RTR + MIVP (60/20/20 split — harder evaluation bar) |
| Gold tier | Curated institutional reasoning traces (GRT) + failure cases (NEG) |

Every training example uses canonical OMNIX identifiers, cites real ADRs and RFCs, and is verified against `ontology.json` for hallucination prevention (OGI-INV-002/003).

---

## Evaluation — 7 Gates Before Deployment

No model version is deployed without passing every gate. There are no exceptions (OGI-INV-008).

| Gate | Metric | Bar |
|---|---|---|
| 1 | Factual accuracy — invariant codes | ≥ 90% |
| 2 | Invariant-citation F1 | ≥ 0.92 |
| 3 | Scenario → Verdict accuracy (4-class) | ≥ 85% |
| 3b | HALT-class recall (separate gate) | ≥ 80% |
| 4 | Hallucination rate vs. ontology | ≤ 3% |
| 5 | Refusal correctness (bilateral) | ≥ 95% |
| 6 | MIVP scenario accuracy | ≥ 80% |

**Gate 3b exists because a model that always outputs CONFORMANT can pass Gate 3** on an unbalanced test set. Gate 3b forces HALT to be evaluated as a separate class — missed HALT carries higher severity than missed CONFORMANT.

**Gate 6 exists because no general model understands proxy-optimization detection.** It is OGI's most novel capability and the hardest to evaluate. It gets its own gate.

---

## What Makes OGI Different

| | OGI | RAG on docs | GPT-4o | Llama-3 | Fine-tuned competitor |
|---|:---:|:---:|:---:|:---:|:---:|
| Native OMNIX vocabulary | ✅ | ❌ | ❌ | ❌ | ❌ |
| Citation-grounded answers | ✅ | partial | ❌ | ❌ | ❌ |
| HALT verdict evaluation | ✅ | ❌ | ❌ | ❌ | ❌ |
| MIVP proxy-optimization detection | ✅ | ❌ | ❌ | ❌ | ❌ |
| Anti-hallucination gate (ontology) | ✅ | ❌ | ❌ | ❌ | — |
| Reproducible corpus (manifest.json) | ✅ | ❌ | ❌ | ❌ | — |
| Versioned, auditable training pipeline | ✅ | ❌ | ❌ | ❌ | — |
| AI sovereignty — no Big Tech dependency | ✅ | ❌ | ❌ | partial | — |

**The moat:** competitors can replicate OMNIX's API surface. They cannot replicate a model fine-tuned on 194 proprietary ADRs and 125 formally verified invariants that do not exist anywhere else on the internet.

---

## The Competitive Claim

> **OGI is the only AI model in existence that knows what MIVP-INV-005 means, can evaluate a session's MAS trajectory, and produce a verdict consistent with ADR-194 — with citation.**

That is not a marketing statement. It is a falsifiable claim. Run the evaluation suite. Check Gate 6. The score either passes or it doesn't.

---

## Deployment

**Platform:** Together.ai (SFT fine-tuning API)  
**Base model (MVP):** Llama-3.1-8B-Instruct-Turbo (~$20–30 per training run)  
**Base model (production):** Llama-3.3-70B-Instruct (~$240 per training run)  
**Inference:** Together.ai OpenAI-compatible endpoint — drop-in replacement in SAL config  
**Re-training trigger:** New RFC, new invariant family, or >10 new ADRs since last corpus version  

---

## Standards Foundation

| RFC | What it covers | DOI (Zenodo) |
|---|---|---|
| RFC-ATF-1 | Agent Identity · MAR · AIR | 10.5281/zenodo.20155016 |
| RFC-ATF-2 | Runtime Continuity · AFG · RCR | 10.5281/zenodo.20241344 |
| RFC-ATF-3 | Interoperability · OEP · GPIL | 10.5281/zenodo.20247342 |
| RFC-ATF-4 | AGVP · DSPP · CRSI | 10.5281/zenodo.20368895 |
| RFC-ATF-5 | CGE · GUGT · TGB | pending |
| RFC-ATF-6 | BEV · BAR · CCS · CTCHC · MIVP | pending |

Six RFCs. The entire OMNIX protocol stack. OGI is trained on all of it.

---

## Contact

**Harold Nunes** · Founder · OMNIX QUANTUM LTD  
OMNIX QUANTUM LTD · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
Operational HQ: Abu Dhabi, UAE  
omnixquantum.net

---

*"Every governance platform will eventually need a model that speaks its language.  
We built ours first — on a corpus that no competitor can replicate."*

**OGI is that model.**

---

*OMNIX-OGI-2026-001 · May 2026 · Confidential — for distribution to strategic partners*
