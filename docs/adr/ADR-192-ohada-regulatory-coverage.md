# ADR-192 — OHADA Regulatory Coverage

**Status:** Accepted
**Author:** Harold Nunes
**Date:** 2026-05-25
**Related:** ADR-028 (External Signal Evaluation), ADR-172 (ATF Open Receipt Schema),
             ADR-176 (Governance API Product)

---

## Context

OMNIX currently supports the following regulatory frameworks as receipt tags:
EU AI Act, MiFID II, Basel III, GDPR, HIPAA, SOX, SAMA, CBUAE, PCI-DSS, eIDAS.

**Gap:** The OHADA zone (Organisation pour l'Harmonisation en Afrique du Droit des Affaires)
covers 17 countries across West and Central Africa with a unified commercial legal framework.
This market represents:

- ~400 million people
- A unified commercial code adopted across: Benin, Burkina Faso, Cameroon, Central African
  Republic, Chad, Comoros, Democratic Republic of Congo, Congo, Côte d'Ivoire, Equatorial
  Guinea, Gabon, Guinea, Guinea-Bissau, Mali, Niger, Senegal, Togo
- Growing fintech and AI adoption with regulatory gaps OMNIX can address
- Strategic geographic alignment with UHG-Tech Ltd (London–Dubai–Abidjan) partners

The OHADA legal framework includes:
- **AUDCG** — Uniform Act on General Commercial Law
- **SYSCOHADA** — Uniform accounting system (IFRS-aligned)
- **AUDSG** — Uniform Act on Commercial Companies
- **AUPCAP** — Uniform Act on Insolvency

AI governance decisions in OHADA-jurisdiction companies must be auditable under SYSCOHADA
accounting standards and traceable under AUDCG commercial law.

---

## Decision

### OHADA-001: Regulatory Tag Set

Add the following tags to the OMNIX receipt regulatory framework registry:

| Tag | Full Name | Scope |
|---|---|---|
| `OHADA` | Organisation Harmonisation Afrique Droit Affaires | All 17 member states |
| `SYSCOHADA` | Système Comptable OHADA | Financial/accounting decisions |
| `AUDCG` | Acte Uniforme Droit Commercial Général | Commercial decisions |
| `IFRS-OHADA` | IFRS as adopted under SYSCOHADA | Financial reporting |
| `CCJA` | Cour Commune de Justice et d'Arbitrage | Dispute resolution traceability |

### OHADA-002: Country Code Coverage

```python
OHADA_MEMBER_STATES = [
    "BJ",  # Benin
    "BF",  # Burkina Faso
    "CM",  # Cameroon
    "CF",  # Central African Republic
    "TD",  # Chad
    "KM",  # Comoros
    "CD",  # Democratic Republic of Congo
    "CG",  # Congo
    "CI",  # Côte d'Ivoire
    "GQ",  # Equatorial Guinea
    "GA",  # Gabon
    "GN",  # Guinea
    "GW",  # Guinea-Bissau
    "ML",  # Mali
    "NE",  # Niger
    "SN",  # Senegal
    "TG",  # Togo
]
```

### OHADA-003: Schema Exposure

The `/api/governance/schema` endpoint MUST include OHADA tags in the
`supported_regulatory_frameworks` array. Clients submitting signals with
`regulatory_context: ["OHADA", "SYSCOHADA"]` receive receipts tagged for
OHADA-jurisdiction auditability.

---

## Invariants

- **OHADA-INV-001:** OHADA tags MUST appear in the public schema endpoint so that
  African fintech clients can discover them without contacting OMNIX sales.
- **OHADA-INV-002:** OHADA-tagged receipts use the same PQC signing (Dilithium-3)
  as all other receipts. No degraded signing for any jurisdiction.

---

## Consequences

**Positive:**
- Opens 17-country market currently unaddressed by OMNIX
- Aligns with Beenish Fatima (MaqasidAI) GCC strategy — OHADA + GCC creates a
  combined emerging-market governance narrative
- Directly counters UHG-Tech competitive advantage in Abidjan/francophone Africa
- SYSCOHADA tag is immediately relevant to any AI system touching financial records
  in the OHADA zone

**Negative:**
- No dedicated legal review of OHADA compliance requirements conducted — tags are
  structural markers, not legal certifications. Harold to consult OHADA-qualified
  counsel before making compliance claims to OHADA-jurisdiction clients.
