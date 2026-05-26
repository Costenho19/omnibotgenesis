# Final Risk Matrix — MIVP / OGI / Governance Stack
**Date:** 2026-05-25  
**Auditor:** OMNIX Internal Governance Audit  
**Scope:** All findings from MIVP_RUNTIME_AUDIT + OGI_CORPUS_AUDIT + GOVERNANCE_SEMANTICS_REPORT + BENCHMARK_READINESS_REPORT  
**Overall System Verdict:** ⚠️ CONDITIONAL PASS — No CRITICAL findings. Deployment blocked on F-001 (psycopg2) and F-002 (MANDATE-BOUND eligibility) resolution.

---

## Risk Matrix — All Findings

| ID | Source | Severity | Finding | File | Impact | Exploitability | Institutional Risk | Remediation |
|---|---|---|---|---|---|---|---|---|
| F-001 | MIVP Runtime | **HIGH** | DB driver mismatch: psycopg2 vs psycopg3 — silent data loss of MIVP artifacts in Railway | `mandate_integrity_verification.py:432,770,798,820,852,892,930` | Silent MBR/MAS/MBRSeal not persisted to DB | Medium | HIGH — MANDATE-BOUND on in-memory-only state is not forensically durable | Replace all `psycopg2` with `psycopg` (psycopg3) |
| F-002 | MIVP Runtime | **HIGH** | Sessions with WARNING turns (but 0 HALT) receive MANDATE-BOUND PoGC tag | `mandate_integrity_verification.py:664` | Institutional credibility of MANDATE-BOUND certificate | Low (requires adversarial calibration) | HIGH — external auditors will challenge | Add warning-turn ratio gate or introduce MANDATE-ALIGNED secondary tag |
| F-C-001 | OGI Corpus | **HIGH** | ADR-193 contains stale ADR count (192, should be 194) and invariant count (51, should be 55+) | `ADR-193-ogi-fine-tuning-pipeline.md:23` | OGI model trained without ADR-193/194 scope | High (corpus generated before fix) | HIGH — model cannot answer MIVP questions | Update ADR-193 counts before corpus generation |
| F-C-002 | OGI Corpus | **HIGH** | OGI-INV-001–010 not in INVARIANT_TEST_MATRIX | `INVARIANT_TEST_MATRIX.md` | OGI deployment gate invisible to audit trail | Medium | HIGH — EU AI Act requires documented conformance checks | Add OGI-INV family as Family 12 in matrix |
| F-003 | MIVP Runtime | **MEDIUM** | No DB foreign key constraints between MIVP tables | `mandate_integrity_verification.py:359–417` | Orphan rows on partial failure; forensic inconsistency | Low | MEDIUM — forensic DB queries return inconsistent results | Add FK constraints with DEFERRABLE INITIALLY DEFERRED |
| F-004 | MIVP Runtime | **MEDIUM** | Non-atomic MBR creation vs session cache write — orphan MBR possible on crash | `governance_runtime.py:393–409` | Unsealed MBRs in atf_mandate_binding_records | Low | MEDIUM — unsealed MBR audit finding | Move create_mbr() after session cache commit or compensate on failure |
| F-005 | MIVP Runtime | **MEDIUM** | ProxyGuard keyword density trivially gameable by adversarial agent | `mandate_integrity_verification.py:66–87` | MIVP bypass via keyword avoidance | HIGH against known guard config | MEDIUM — acknowledged in ADR-194 but no production gate defined | Require ML classifiers in production; add MIVP-INV-009 or formal production gate |
| F-006 | MIVP Runtime | **MEDIUM** | `MIVP_MAS_HALT_THRESHOLD` env var has no floor validation — can be set to 0.0 | `mandate_integrity_verification.py:41–42` | MIVP-INV-005 silently bypassed | Medium | MEDIUM — equivalent to disabling mandate HALT | Add validation: `mas_halt >= 0.05` and `mas_halt < mas_warn` |
| F-C-003 | OGI Corpus | **MEDIUM** | `corpus_allowlist.yaml` does not exist — OGI-INV-001 violated from first run | Not found in repo | Corpus generation non-compliant from start | High (run before fix) | MEDIUM — primary leakage control missing | Create `scripts/fine_tuning/corpus_allowlist.yaml` |
| F-C-004 | OGI Corpus | **MEDIUM** | Train/val/test split underspecified for adversarial examples | `ADR-193:OGI-006` | Adversarial scenarios underrepresented in test set | Medium | MEDIUM — model may pass gates on benign scenarios only | Add 60/20/20 split for RTR + Tier 3 SCN categories |
| F-C-005 | OGI Corpus | **MEDIUM** | No MIVP corpus category — model cannot evaluate proxy-optimization scenarios | `ADR-193:OGI-003` | OGI unable to answer MIVP questions | High | MEDIUM — first question after RFC-ATF-6 will be MIVP | Add MIVP as 13th corpus category (150 examples) |
| F-C-006 | OGI Corpus | **MEDIUM** | `ontology.json` not defined — hallucination Gate 4 cannot execute | `ADR-193:OGI-007` | Gate 4 evaluation impossible | High | MEDIUM — hallucination detection is manual without it | Auto-generate ontology.json from ADR/RFC/invariant corpus |
| G-001 | Governance Semantics | **MEDIUM** | "Admissibility" term overloaded — ATF (context admission) vs MIVP (mandate threshold) | `ADR-194` + `ADR-050` | External reviewer confusion | Low | MEDIUM — regulatory reviewer will ask | Add explicit disambiguation in ADR-194 §Context |
| B-001 | Benchmark | **MEDIUM** | No HALT-class stratified accuracy gate — model can pass Gate 3 while failing on HALT | `ADR-193:OGI-007` | HALT scenarios not adequately evaluated | High | MEDIUM — most dangerous failure mode undetected | Add Gate 3b: per-class HALT recall ≥ 0.80 |
| F-007 | MIVP Runtime | **LOW** | `mbr is not None` clause in mandate_bound_eligible always True — dead code | `mandate_integrity_verification.py:664` | None functional | None | LOW | Remove clause or add explanatory comment |
| F-008 | MIVP Runtime | **LOW** | In-memory MIVP stores not shared across Railway dynos | `mandate_integrity_verification.py:423–425` | Inconsistent state in multi-dyno deployments | Low (sticky routing) | LOW now, HIGH if horizontal scaling | Use Redis for MBR/MAS state sharing |
| F-009 | MIVP Runtime | **LOW** | `MIVP_MAS_HALT_THRESHOLD` and `MIVP_MAS_WARNING_THRESHOLD` not in replit.md | `replit.md` | Operational documentation gap | None | LOW | Add both vars to env var table |
| F-C-007 | OGI Corpus | **LOW** | `rejected_samples.jsonl` path not specified in ADR | `ADR-193:OGI-005` | Reproducibility gap | Low | LOW | Specify canonical path in ADR-193 |
| G-002 | Governance Semantics | **LOW** | "Mandate" vs "Constraint" distinction not explicitly stated in ADR-194 | `ADR-194:§Context` | External reviewer confusion on core innovation | Low | LOW | Add definitional paragraph to ADR-194 |
| B-002 | Benchmark | **LOW** | No inter-annotator agreement protocol for ground truth labels | `ADR-193:OGI-007` | F1 gate based on single-annotator labels | Medium | LOW | Add dual-annotation + Cohen's κ ≥ 0.80 requirement |

---

## Risk Summary by Severity

| Severity | Count | Blocking for production? |
|---|---|---|
| CRITICAL | **0** | — |
| HIGH | **4** | F-001, F-002 block MANDATE-BOUND issuance; F-C-001, F-C-002 block OGI corpus generation |
| MEDIUM | **10** | Not individually blocking but collectively represent institutional audit risk |
| LOW | **6** | Cleanup items |

---

## Deployment Readiness Gates

### Gate A — MIVP MANDATE-BOUND Production Ready
- [ ] F-001 resolved (psycopg2 → psycopg3)
- [ ] F-002 resolved (WARNING-turn gate or MANDATE-ALIGNED tag)
- [ ] F-003 resolved (FK constraints)
- [ ] F-006 resolved (halt threshold floor validation)

### Gate B — OGI Corpus Generation Ready
- [ ] F-C-001 resolved (ADR-193 counts updated)
- [ ] F-C-003 resolved (corpus_allowlist.yaml created)
- [ ] F-C-006 resolved (ontology.json auto-generated)
- [ ] F-C-005 in progress (MIVP corpus category designed)

### Gate C — OGI Model Deployment Ready
- [ ] Gate B passed
- [ ] All 5 OGI-007 evaluation gates passing
- [ ] Gate 3b (HALT-class recall) added and passing
- [ ] Inter-annotator agreement completed for INV + SCN test set

### Gate D — RFC-ATF-6 External Publication Ready
- [ ] Gate A passed
- [ ] G-001 resolved (admissibility disambiguation in ADR-194)
- [ ] G-002 resolved (mandate vs constraint definition)
- [ ] ADR-194 §Consequential Risk updated with ProxyGuard production gate requirement

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
