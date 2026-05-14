# Zenodo Submission Guide — RFC-ATF-2

**Referencia interna:** OMNIX-SUB-ZENODO-2026-002
**Fecha de preparación:** Mayo 2026
**Documento base:** `docs/standards/RFC-ATF-2.md`
**Referencia RFC-ATF-1 DOI:** 10.5281/zenodo.20155016

---

## Paso 1 — Preparar el archivo

Exportar `docs/standards/RFC-ATF-2.md` a PDF con el siguiente encabezado de portada:

```
RFC-ATF-2: Agent Trust Fabric — Runtime Governance Continuity
Extension to RFC-ATF-1 · Version 1.0.0
OMNIX QUANTUM Open Standard · May 2026
Harold Nunes (Editor) · OMNIX QUANTUM LTD
DOI: [se asigna después del upload]
Extends: RFC-ATF-1 (DOI: 10.5281/zenodo.20155016)
```

Archivos a incluir en el upload:
- `RFC-ATF-2.pdf` — el documento principal
- `RFC-ATF-2.md` — el source Markdown
- `ADR-159-runtime-governance-continuity.md` — el ADR de referencia

---

## Paso 2 — Metadata exacta para Zenodo

**Upload type:** Software / Publication → Publication → Technical Note

**Title:**
```
RFC-ATF-2: Agent Trust Fabric — Runtime Governance Continuity Extension
```

**Authors:**
```
Nunes, Harold
Affiliation: OMNIX QUANTUM LTD
ORCID: [añadir si disponible]
```

**Description (pegar exactamente):**
```
RFC-ATF-2 extends the Agent Trust Fabric (ATF) delegation protocol defined
in RFC-ATF-1 (DOI: 10.5281/zenodo.20155016) to cover the full execution
lifecycle of long-running autonomous agent workflows.

RFC-ATF-1 established cryptographic boundary attestation: proof that an
agent possessed a valid, human-originated authority grant at the moment of
execution admission. RFC-ATF-2 addresses the Runtime Governance Gap — the
structural absence of continuous governability supervision between admission
and completion.

This extension introduces:

(1) Runtime Continuity Record (RCR) — PQC-signed, TAR-anchored authority
health snapshots forming a cryptographic continuity chain throughout
execution.

(2) Continuity Eligibility Score (CES) — a composite metric
(T×0.30 + B×0.30 + D×0.20 + I×0.20) quantifying runtime authority health
across temporal, budget, context, and integrity dimensions.

(3) Authority Fragmentation Guard (AFG) — aggregate budget enforcement
across concurrent sub-agents sharing a delegation chain root, closing an
attack vector that individual-level MAR cannot detect.

(4) Reauthorization Challenge (RC) Protocol — cryptographically signed
mid-execution authority renewal with automatic HALT on TTL expiry.

Eight new invariants (RGC-INV-001–008) extend the six invariants of
RFC-ATF-1 to a total of 14 formally model-checkable invariants.

The reference implementation is currently running in production.
Formally acknowledged contribution: Akhilesh Warik (Runtime AI Governance
Research, May 2026) for independent identification of the boundary
attestation / continuous governability supervision architectural seam.
```

**Version:** 1.0.0

**Publication date:** [fecha de publicación]

**Keywords:**
```
AI governance, runtime governance, agent delegation, post-quantum cryptography,
Dilithium-3, ML-DSA-65, authority delegation, autonomous agents, continuity
eligibility score, authority fragmentation, reauthorization protocol,
cryptographic receipts, FIPS 204
```

**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)

**Related identifiers:**
```
Is supplement to: 10.5281/zenodo.20155016 (RFC-ATF-1)
Is related to: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6757339
```

---

## Paso 3 — Tras la publicación

Una vez Zenodo asigne el DOI:

1. Actualizar `docs/standards/RFC-ATF-2.md` — añadir el DOI en el campo "DOI: pending"
2. Actualizar `docs/ARCHITECTURE_INDEX.md` — cambiar "Pendiente Zenodo" por el DOI
3. Actualizar `replit.md` — añadir el DOI al pointer de RFC-ATF-2
4. Crear GitHub Release v1.1.0 (ver `docs/submissions/GITHUB_RELEASE_v1.1.0.md`)
5. Actualizar SSRN: 6763978 para referenciar RFC-ATF-2 como extensión

---

## BibTeX (completar con DOI real)

```bibtex
@techreport{nunes2026rfcatf2,
  title       = {{RFC-ATF-2}: {Agent Trust Fabric} ---
                 Runtime Governance Continuity Extension},
  author      = {Harold Nunes},
  institution = {{OMNIX QUANTUM LTD}},
  year        = {2026},
  month       = {May},
  type        = {{OMNIX QUANTUM Open Standard}},
  number      = {v1.0.0},
  doi         = {<DOI-aquí>},
  note        = {Extends RFC-ATF-1 (DOI: 10.5281/zenodo.20155016)}
}
```
