# EVIDENCE PACK — FAMILY 10
## OMNIX-PAT-2026-010

**Invention:** PQC Merkle Transparency Chain — April 19, 2026

## KEY SOURCE FILES
| File | Description |
|---|---|
| `omnix_core/evidence/transparency_chain.py` | Complete chain implementation — ADR-044 |
| `omnix_core/evidence/verification_server.py` | Public verification API |
| `omnix_core/evidence/decision_receipt.py` | Receipt structure integrated with chain |

**Git commit hash:** [RETRIEVE: `git log --oneline omnix_core/evidence/transparency_chain.py`]

## ARCHITECTURE DECISION RECORDS
| ADR | Title | Date |
|---|---|---|
| ADR-044 | Quantum-Secure Decision Receipts — Transparency Log | March 2026 |

## PRIOR ART SEARCH
**Searched:** USPTO, Google Patents, IETF RFC database, arXiv (cs.CR)
**Terms:** "rolling merkle governance", "append-only receipt chain PQC", "internal RFC 3161 no TSA", "tamper-evident governance audit"
**Result:** No prior art combining rolling Merkle accumulation + internal timestamping without TSA + PQC entry signing + public verification without content disclosure specifically for governance decision receipt chains.

## FILING CHECKLIST
- [ ] Retrieve git commit hashes
- [ ] Confirm address and email in cover sheet
- [ ] File at patentcenter.uspto.gov
- [ ] Record application number immediately
