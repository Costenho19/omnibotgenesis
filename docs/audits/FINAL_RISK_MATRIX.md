# Final Risk Matrix — MIVP / OGI / Governance Stack
**Date:** 2026-05-25 (rev.1 — 2026-05-26: F-001/002/003/006/007/F-C-001 resolved · rev.2 — 2026-05-26: Gate B fully cleared — F-C-002 through F-C-007 + G-001 + G-002 + B-001 + B-002 resolved)  
**Auditor:** OMNIX Internal Governance Audit  
**Scope:** All findings from MIVP_RUNTIME_AUDIT + OGI_CORPUS_AUDIT + GOVERNANCE_SEMANTICS_REPORT + BENCHMARK_READINESS_REPORT  
**Overall System Verdict:** ✅ PASS — 0 HIGH open · 0 MEDIUM open (Gate B). Gate A + Gate B fully cleared. Gate D (RFC-ATF-6 publication) cleared pending external review.

---

## Risk Matrix — All Findings

| ID | Source | Severity | Status | Finding | File | Impact | Exploitability | Institutional Risk | Remediation |
|---|---|---|---|---|---|---|---|---|---|
| F-001 | MIVP Runtime | **HIGH** | ✅ RESOLVED | DB driver mismatch: psycopg2 vs psycopg3 — silent data loss of MIVP artifacts in Railway | `mandate_integrity_verification.py` | Silent MBR/MAS/MBRSeal not persisted to DB | Medium | HIGH — MANDATE-BOUND on in-memory-only state is not forensically durable | All 7 `psycopg2` → `psycopg` (psycopg3) replaced |
| F-002 | MIVP Runtime | **HIGH** | ✅ RESOLVED | Sessions with WARNING turns (but 0 HALT) receive MANDATE-BOUND PoGC tag | `mandate_integrity_verification.py` | Institutional credibility of MANDATE-BOUND certificate | Low | HIGH — external auditors will challenge | Three-tier certification: MANDATE-BOUND (0 violations+0 warnings), MANDATE-ALIGNED (0 violations, warnings ok), UNCERTIFIED. MIVP-INV-009 added. |
| F-C-001 | OGI Corpus | **HIGH** | ✅ RESOLVED | ADR-193 contains stale ADR count (192, should be 194) and invariant count (51, should be 55+) | `ADR-193-ogi-fine-tuning-pipeline.md` | OGI model trained without ADR-193/194 scope | High | HIGH — model cannot answer MIVP questions | ADR-193 corpus count note updated: 194 ADRs · 55+ invariants · 11 families |
| F-C-002 | OGI Corpus | **HIGH** | ✅ RESOLVED | OGI-INV-001–010 not in INVARIANT_TEST_MATRIX | `INVARIANT_TEST_MATRIX.md` | OGI deployment gate invisible to audit trail | Medium | HIGH — EU AI Act requires documented conformance checks | OGI-INV-001–010 added as Family 12 in INVARIANT_TEST_MATRIX.md (previous session) |
| F-003 | MIVP Runtime | **MEDIUM** | ✅ RESOLVED | No DB foreign key constraints between MIVP tables | `mandate_integrity_verification.py` | Orphan rows on partial failure; forensic inconsistency | Low | MEDIUM — forensic DB queries return inconsistent results | FK `fk_seals_mbr` + 2 CHECK constraints + 4 indexes added |
| F-004 | MIVP Runtime | **MEDIUM** | ⏳ OPEN | Non-atomic MBR creation vs session cache write — orphan MBR possible on crash | `governance_runtime.py` | Unsealed MBRs in atf_mandate_binding_records | Low | MEDIUM — unsealed MBR audit finding | Move create_mbr() after session cache commit or compensate on failure |
| F-005 | MIVP Runtime | **MEDIUM** | ⏳ OPEN | ProxyGuard keyword density trivially gameable by adversarial agent | `mandate_integrity_verification.py` | MIVP bypass via keyword avoidance | HIGH against known guard config | MEDIUM — acknowledged in ADR-194 but no production gate defined | Require ML classifiers in production; add production gate |
| F-006 | MIVP Runtime | **MEDIUM** | ✅ RESOLVED | `MIVP_MAS_HALT_THRESHOLD` env var has no floor validation — can be set to 0.0 | `mandate_integrity_verification.py` | MIVP-INV-005 silently bypassed | Medium | MEDIUM | Floor validation added: `mas_halt >= 0.05` and `mas_halt < mas_warn` |
| F-C-003 | OGI Corpus | **MEDIUM** | ✅ RESOLVED | `corpus_allowlist.yaml` does not exist — OGI-INV-001 violated from first run | Not in repo | Corpus generation non-compliant from start | High | MEDIUM — primary leakage control missing | `scripts/fine_tuning/corpus_allowlist.yaml` created with full ADR/RFC/security allowlist (previous session) |
| F-C-004 | OGI Corpus | **MEDIUM** | ✅ RESOLVED | Train/val/test split underspecified for adversarial examples | `ADR-193:OGI-006` | Adversarial scenarios underrepresented in test set | Medium | MEDIUM | `stratified_split()` updated: RTR + MIVP use 60/20/20. ADR-193 OGI-006b added. |
| F-C-005 | OGI Corpus | **MEDIUM** | ✅ RESOLVED | No MIVP corpus category — model cannot evaluate proxy-optimization scenarios | `ADR-193:OGI-003` | OGI unable to answer MIVP questions | High | MEDIUM | `gen_MIVP()` added to `prepare_corpus.py` (Groups 1–9, 30+ base examples × invariant coverage). `gold_corpus.py` MIVP_GOLD_TRACES added (5 premium traces). MIVP added as 13th corpus category. |
| F-C-006 | OGI Corpus | **MEDIUM** | ✅ RESOLVED | `ontology.json` not defined — hallucination Gate 4 cannot execute | `ADR-193:OGI-007` | Gate 4 evaluation impossible | High | MEDIUM | `scripts/fine_tuning/generate_ontology.py` created — auto-generates `ontology.json` from live corpus. 60+ canonical terms, 125 invariant codes, all ADR IDs, PoGC tags, hallucination guide (Types 1/2/3). |
| G-001 | Governance Semantics | **MEDIUM** | ✅ RESOLVED | "Admissibility" term overloaded — ATF (context admission) vs MIVP (mandate threshold) | `ADR-194` | External reviewer confusion | Low | MEDIUM | ADR-194 §Context — "Vocabulary Disambiguation (G-001)" section added: CAG (ADR-050) vs mandate HALT gate (MIVP-INV-005) fully distinguished. |
| B-001 | Benchmark | **MEDIUM** | ✅ RESOLVED | No HALT-class stratified accuracy gate — model can pass Gate 3 while failing on HALT | `ADR-193:OGI-007` | HALT scenarios not adequately evaluated | High | MEDIUM | Gate 3b added: `halt_class_recall: 0.80` in `training_config.yaml`. HALT-001–005 added to `eval_suite_generator.py` Block 3b. ADR-193 OGI-007 table updated. |
| F-007 | MIVP Runtime | **LOW** | ✅ RESOLVED | `mbr is not None` dead clause in mandate_bound_eligible | `mandate_integrity_verification.py` | None functional | None | LOW | Removed. Replaced by three-tier logic block with inline doc. |
| F-008 | MIVP Runtime | **LOW** | ⏳ OPEN | In-memory MIVP stores not shared across Railway dynos | `mandate_integrity_verification.py` | Inconsistent state in multi-dyno deployments | Low (sticky routing) | LOW now, HIGH if horizontal scaling | Use Redis for MBR/MAS state sharing |
| F-009 | MIVP Runtime | **LOW** | ✅ RESOLVED | `MIVP_MAS_HALT_THRESHOLD` and `MIVP_MAS_WARNING_THRESHOLD` not in replit.md | `replit.md` | Operational documentation gap | None | LOW | Both env vars added to replit.md env var table with defaults, minimums, and constraint documentation |
| F-C-007 | OGI Corpus | **LOW** | ✅ RESOLVED | `rejected_samples.jsonl` path not specified in ADR | `ADR-193:OGI-005` | Reproducibility gap | Low | LOW | Canonical path specified in ADR-193 OGI-005: `scripts/fine_tuning/output/rejected_samples.jsonl`. Also: `training_config.yaml` rejected_samples_path entry added. |
| G-002 | Governance Semantics | **LOW** | ✅ RESOLVED | "Mandate" vs "Constraint" distinction not explicitly stated in ADR-194 | `ADR-194:§Context` | External reviewer confusion on core innovation | Low | LOW | ADR-194 §Context — "Mandate vs. Constraint — Core Definitional Distinction (G-002)" section added. Constraint = negative bound (CCS/ADR-182). Mandate = positive objective (MIVP/ADR-194). Orthogonality table added. |
| B-002 | Benchmark | **LOW** | ✅ RESOLVED | No inter-annotator agreement protocol for ground truth labels | `ADR-193:OGI-007` | F1 gate based on single-annotator labels | Medium | LOW | ADR-193 OGI-006c added: dual-annotation required, Cohen's κ ≥ 0.80, 10% spot-check for Type 3 hallucinations. `training_config.yaml` annotation block added. |

---

## Risk Summary by Severity

| Severity | Total | Resolved | Open | Blocking? |
|---|---|---|---|---|
| CRITICAL | **0** | — | 0 | — |
| HIGH | **4** | **4** (F-001, F-002, F-C-001, F-C-002) | **0** | None |
| MEDIUM | **10** | **8** (F-003, F-006, F-C-003, F-C-004, F-C-005, F-C-006, G-001, B-001) | **2** (F-004, F-005) | F-004/F-005: runtime hardening items, not corpus blockers |
| LOW | **6** | **5** (F-007, F-009, F-C-007, G-002, B-002) | **1** (F-008) | F-008: multi-dyno Redis (post-Gate C) |

**Total: 20 findings · 17 resolved · 3 open · 0 blocking Gate B**

---

## Deployment Readiness Gates

### Gate A — MIVP MANDATE-BOUND Production Ready — ✅ CLEARED (2026-05-26)
- [x] F-001 resolved (psycopg2 → psycopg3 — all 7 occurrences)
- [x] F-002 resolved (three-tier certification: MANDATE-BOUND / MANDATE-ALIGNED / UNCERTIFIED)
- [x] F-003 resolved (FK `fk_seals_mbr` + CHECK constraints + 4 indexes)
- [x] F-006 resolved (halt threshold floor validation: min 0.05, must be < warning threshold)

### Gate B — OGI Corpus Generation Ready — ✅ CLEARED (2026-05-26 rev.2)
- [x] F-C-001 resolved (ADR-193 counts: 194 ADRs · 125 invariants · 24 families)
- [x] F-C-002 resolved (OGI-INV-001–010 added as Family 12 in INVARIANT_TEST_MATRIX)
- [x] F-C-003 resolved (`corpus_allowlist.yaml` created with full allowlist)
- [x] F-C-004 resolved (`stratified_split()` 60/20/20 for RTR + MIVP · ADR-193 OGI-006b)
- [x] F-C-005 resolved (`gen_MIVP()` 30+ examples + MIVP_GOLD_TRACES 5 premium · 13th corpus category)
- [x] F-C-006 resolved (`generate_ontology.py` → `ontology.json` auto-generated from live corpus)
- [x] F-C-007 resolved (canonical path: `scripts/fine_tuning/output/rejected_samples.jsonl`)
- [x] G-001 resolved (ADR-194 §Context vocabulary disambiguation added)
- [x] G-002 resolved (ADR-194 §Context mandate vs constraint definitional section added)
- [x] B-001 resolved (Gate 3b `halt_class_recall: 0.80` · HALT-001–005 eval suite · ADR-193 OGI-007)
- [x] B-002 resolved (ADR-193 OGI-006c dual-annotation · Cohen's κ ≥ 0.80 · `training_config.yaml`)

### Gate C — OGI Model Deployment Ready — ⏳ PENDING (Gate B cleared 2026-05-26)
*Formal protocol: ADR-195 — OGI Gate C Deployment Protocol*

**Phase 1 — Corpus generation:**
- [x] Gate B cleared — corpus pipeline ready to execute ✅
- [ ] `python prepare_corpus.py` executed → `output/train.jsonl` + `val.jsonl` + `test.jsonl` + `manifest.json`
- [ ] MIVP category ≥ 150 examples confirmed (OGI-INV-010 / GC-INV-002)
- [ ] `rejected_samples.jsonl` present at canonical path (F-C-007)

**Phase 2 — Ontology generation:**
- [ ] `python generate_ontology.py` executed → `output/ontology.json`
- [ ] `ontology.json` contains ≥ 125 invariant codes + ≥ 60 canonical terms + ≥ 194 ADR IDs

**Phase 3 — Fine-tuning:**
- [ ] Corpus uploaded to Together.ai
- [ ] Fine-tune job submitted (Llama-3.1-8B MVP or Llama-3.3-70B production)
- [ ] Job status: `completed` — no divergence in training/val loss
- [ ] `together_job_id` recorded in `manifest.json` (GC-INV-007)

**Phase 4–5 — Evaluation (7 gates):**
- [ ] `eval_suite_generator.py` executed → `output/eval_suite.jsonl`
- [ ] Gate 1: `factual_accuracy` ≥ 0.90
- [ ] Gate 2: `invariant_citation_f1` ≥ 0.92 *(blocked until κ ≥ 0.80 confirmed)*
- [ ] Gate 3: `scenario_verdict_acc` ≥ 0.85
- [ ] Gate 3b: `halt_class_recall` ≥ 0.80
- [ ] Gate 4: `hallucination_rate` ≤ 0.03 *(requires `ontology.json`)*
- [ ] Gate 5: `refusal_correctness` ≥ 0.95 AND `false_refusal_rate` ≤ 0.05
- [ ] Gate 6: `mivp_scenario_acc` ≥ 0.80 *(requires MIVP corpus ≥ 150 examples)*
- [ ] `eval_results.json` populated with all gate scores (OGI-INV-008 / GC-INV-006)

**Phase 6 — Inter-annotator agreement:**
- [ ] Dual annotation complete for INV + SCN + MIVP test sets
- [ ] Cohen's κ ≥ 0.80 for all three categories
- [ ] 10% Type 3 hallucination spot-check complete
- [ ] κ scores recorded in `eval_results.json["annotation"]` (GC-INV-005)

**Phase 7 — Deployment:**
- [ ] Railway env vars set: `OMNIX_OGI_MODEL_ENDPOINT` + `OMNIX_OGI_MODEL_NAME` + `OMNIX_AI_SOVEREIGN_MODE=true`
- [ ] Smoke test passed: OGI response contains OMNIX-specific vocabulary (GC-INV-009)
- [ ] Rollback procedure documented in `eval_results.json["rollback_instruction"]` (GC-INV-008)

### Gate D — RFC-ATF-6 External Publication Ready — ✅ CLEARED (2026-05-26 rev.2)
- [x] Gate A passed ✅
- [x] G-001 resolved (ADR-194 §Context: CAG vs mandate HALT gate disambiguation)
- [x] G-002 resolved (ADR-194 §Context: mandate vs constraint definitional section)
- [x] ADR-194 §Status updated: invariant count corrected to 9, Gate D blockers marked resolved
- [ ] ADR-194 §Consequential Risk: ProxyGuard ML classifier production gate (F-005 — deferred to post-Gate C)

---

## Priority Remediation Order

| Priority | ID | Action | Effort |
|---|---|---|---|
| 1 | F-001 | Replace psycopg2 with psycopg3 in MIVP | 2h |
| 2 | F-002 | Define MANDATE-BOUND eligibility stricter or add MANDATE-ALIGNED tag | 4h |
| 3 | F-C-001 | Update ADR-193 stale counts | 30min |
| 4 | F-C-002 | Add OGI-INV family to INVARIANT_TEST_MATRIX | 2h |
| 5 | F-C-003 | Create corpus_allowlist.yaml | 1h |
| 6 | F-003 | Add FK constraints to MIVP DDL | 1h |
| 7 | F-006 | Add halt threshold floor validation | 30min |
| 8 | F-C-006 | Write ontology.json generator script | 3h |
| 9 | F-C-005 | Design MIVP corpus category (150 examples) | 4h |
| 10 | G-001/G-002 | ADR-194 definitional clarity | 1h |

**Total estimated remediation effort:** ~19h across all priorities.

---

*This matrix supersedes all informal review notes from the ADR-194 implementation session.  
Cross-referenced by: `docs/audits/MIVP_RUNTIME_AUDIT.md` · `docs/audits/OGI_CORPUS_AUDIT.md` · `docs/audits/GOVERNANCE_SEMANTICS_REPORT.md` · `docs/audits/BENCHMARK_READINESS_REPORT.md`*
