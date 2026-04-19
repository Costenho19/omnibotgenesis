# EVIDENCE PACK — FAMILY 13
## OMNIX-PAT-2026-013

**Invention:** Exit Governance Layer (EGL) — April 19, 2026

## KEY SOURCE FILES
| File | Description |
|---|---|
| `omnix_core/governance/exit_governance.py` | Complete EGL implementation (ADR-036) |
| `omnix_core/temporal/coherence_validator.py` | TCV reused in Gate 3 (ADR-032) |
| `omnix_core/evidence/decision_receipt.py` | Exit receipt generation |

**Git commit hash:** [RETRIEVE BEFORE FILING]

## ARCHITECTURE DECISION RECORDS
| ADR | Title | Date |
|---|---|---|
| ADR-036 | Exit Governance Layer | March 2026 |

## PRIOR ART SEARCH
**Searched:** USPTO, Google Patents, arXiv (q-fin, cs.AI), FinTech governance literature
**Terms:** "exit governance pipeline", "regime-adjusted take-profit stop-loss", "exit decision governance", "stop-loss governance checkpoint", "exit receipt governance"
**Result:** Regime-conditioned position sizing exists (Kelly variants). Fixed stop-loss / take-profit mechanisms are well-known. No prior art found applying a multi-gate governance pipeline with regime-adaptive threshold scaling, exit coherence validation, and PQC-signed receipt generation specifically to exit decisions in automated governance systems.

## FILING CHECKLIST
- [ ] Retrieve git commit hashes
- [ ] Confirm address and email in cover sheet
- [ ] File at patentcenter.uspto.gov
- [ ] Record application number immediately
