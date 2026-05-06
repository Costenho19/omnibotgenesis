# ADR-137: Islamic Credit Governance Vertical

**Status:** Accepted  
**Date:** 2026-05-06  
**Author:** Harold Nunes, OMNIX QUANTUM  
**Resolves:** Extension of OMNIX governance to the Islamic Finance and Sharia-Compliant Credit domain

---

## Context

The global Islamic finance industry manages over $4 trillion in assets (IFSB 2024). Financing decisions under Sharia law must comply with AAOIFI Financial Accounting Standards, prohibit Riba (interest), Gharar (excessive uncertainty), and Maysir (speculation), and be certified by a qualified Sharia scholar or board.

The absence of automated, auditable Sharia compliance verification creates regulatory and reputational risk for Islamic financial institutions operating in the UAE (CBUAE/DFSA), Malaysia (BNM/IBFIM), UK (FCA Islamic Finance window), GCC (AAOIFI mandatory), Bahrain (CBB / AAOIFI HQ), and Pakistan (SBP/SECP).

OMNIX provides a cryptographically auditable governance layer that evaluates every Islamic financing application against AAOIFI standards, Sharia principles, and local regulatory requirements.

## Decision

OMNIX establishes a dedicated **Islamic Credit Governance Vertical** (`domain: credit`) with the following characteristics:

### 11-Checkpoint Fail-Closed Pipeline (AAOIFI / Sharia aligned)

| CP | Gate | Threshold | Standard |
|----|------|-----------|----------|
| CP-1 | Halal Asset Compliance | ≥60 | AAOIFI SS No. 21 |
| CP-2 | Sharia Structure Validity | ≥55 | AAOIFI FAS 1-38 |
| CP-3 | LTV Sharia Assessment | ≥42 | AAOIFI FAS 32 |
| CP-4 | Customer Creditworthiness | ≥45 | Basel III / IFSB |
| CP-5 | Gharar Detection | ≥50 | Quran 5:90 / AAOIFI SS No. 1 |
| CP-6 | Riba Screen | ≥55 | Quran 2:275 / AAOIFI |
| CP-7 | Maysir Gate | ≥48 | AAOIFI Sharia Standard No. 1 |
| CP-8 | AAOIFI Compliance Gate | ≥52 | AAOIFI FAS 2026 |
| CP-9 | AML / CFT Gate | ≥55 | FATF Recommendation 10 |
| CP-10 | Sharia Board Authorization | ≥60 | AAOIFI Governance Standard No. 1 |
| CP-11 | Jurisdiction Regulatory Gate | ≥48 | CBUAE / BNM / FCA / SBP |

### Hard Block Conditions (pre-evaluation, fail-closed)

1. **Halal compliance < 50%** — Haram asset detected; financing categorically prohibited (AAOIFI SS No. 21)
2. **Mixed conventional income + no Sharia review** — Riba contamination confirmed (Quran 2:275)
3. **LTV > 90%** — Exceeds maximum Islamic asset-backed financing limit (AAOIFI FAS 32)

### Supported Financing Structures

| Structure | Gharar Level | Description |
|-----------|-------------|-------------|
| Murabaha | 10% | Cost-plus sale — most common Islamic financing |
| Ijara | 12% | Islamic lease (vehicle, equipment) |
| Musharakah | 18% | Partnership financing |
| Diminishing Musharakah | 14% | Declining balance home finance |
| Istisna'a | 22% | Manufacturing / construction contract |
| Salam | 28% | Forward commodity purchase (highest Gharar) |

### Sharia Screening Criteria

- **Gharar**: Uncertainty in contract terms within AAOIFI permissible bounds
- **Riba**: Zero tolerance for conventional interest elements; mixed income streams trigger hard block
- **Maysir**: Speculative gambling elements absent from asset-backed contracts
- **AAOIFI FAS**: Full accounting standard compliance required for Murabaha, Ijara, Musharakah
- **Halal Assets**: Asset must be permissible under Islamic law (no alcohol, gambling, pork, weapons of mass destruction, pornography)

### Receipt Format

Every approved Islamic financing decision generates a PQC-signed receipt:
```
OMNIX-ISL-{12 uppercase hex chars}
Algorithm: Dilithium-3 (NIST FIPS 204 / ML-DSA-65)
```

### Supported Jurisdictions

| Jurisdiction | Authority | AAOIFI |
|-------------|-----------|--------|
| UAE | CBUAE / DFSA | Mandatory (×1.18) |
| Malaysia | BNM / IBFIM | Aligned (×1.15) |
| UK | FCA Islamic Finance | Aligned (×1.10) |
| GCC | AAOIFI Standard | Mandatory (×1.20) |
| Bahrain | CBB / AAOIFI HQ | Mandatory (×1.22) |
| Pakistan | SBP / SECP | Mandatory (×1.12) |

## Consequences

- Islamic Credit domain joins the 10-vertical OMNIX governance fleet under the key `credit`
- All Islamic financing receipts are independently verifiable via `/verify/{receipt_id}`
- Three hard block conditions prevent any Haram, Riba-contaminated, or over-leveraged financing from proceeding
- Sharia Board Authorization checkpoint (CP-10) ensures Fatwa validity before any approval
- Interactive demo available at `/governance-demo-islamic-credit`
- Domain key: `credit` — receipt prefix: `OMNIX-ISL`

## References

- ADR-115: Engine Unification — All Verticals
- ADR-131: Execution Integrity Layer
- AAOIFI Financial Accounting Standards (FAS) 1–38, 2026 edition
- AAOIFI Sharia Standards — particularly SS No. 1 (Gharar/Maysir), SS No. 21 (Halal compliance)
- AAOIFI Governance Standards — GS No. 1 (Sharia Supervisory Board)
- IFSB-17: Core Principles for Islamic Finance Regulation
- FATF Recommendation 10 — Customer Due Diligence
- Quran 2:275 (prohibition of Riba), 5:90 (prohibition of Maysir/Gharar)
- BNM Islamic Financial Services Act 2013
- CBUAE Islamic Finance Framework 2022
