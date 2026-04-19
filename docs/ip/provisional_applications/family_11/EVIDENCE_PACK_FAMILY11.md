# EVIDENCE PACK — FAMILY 11
## OMNIX-PAT-2026-011

**Invention:** Crypto-Agility Provider Architecture + Hybrid KEM — April 19, 2026

## KEY SOURCE FILES
| File | Description |
|---|---|
| `omnix_core/security/crypto_providers.py` | Provider registry and CryptoProvider interface (ADR-043) |
| `omnix_core/security/hybrid_crypto.py` | Hybrid KEM: X25519 + Kyber-768 via HKDF (ADR-042) |
| `omnix_core/security/pqc_security.py` | PQC security orchestration |
| `omnix_core/security/pqc_config.py` | Provider configuration resolution |

**Git commit hashes:** [RETRIEVE BEFORE FILING]

## ARCHITECTURE DECISION RECORDS
| ADR | Title | Date |
|---|---|---|
| ADR-042 | Hybrid Classical + PQC Key Exchange | March 2026 |
| ADR-043 | Crypto-Agility Layer | March 2026 |

## PRIOR ART SEARCH
**Searched:** USPTO, Google Patents, NIST PQC standardization documents, IETF hybrid KEM drafts, arXiv (cs.CR, quant-ph)
**Terms:** "crypto agility provider governance", "algorithm bound receipt signing", "hybrid KEM governance", "HKDF kyber x25519 governance", "fail-safe degradation PQC KEM"
**Result:** Hybrid KEM concepts appear in NIST/IETF drafts but exclusively for TLS/communication protocols. No prior art found combining: (1) crypto-agility provider registry, (2) algorithm-bound signed governance receipts, and (3) fail-safe hybrid KEM with mode binding specifically for automated decision governance infrastructure.

## FILING CHECKLIST
- [ ] Retrieve git commit hashes
- [ ] Confirm address and email in cover sheet
- [ ] File at patentcenter.uspto.gov
- [ ] Record application number immediately
