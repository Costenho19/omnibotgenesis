# RFC-ATF-6 — Datos de Publicación

## DOIs

| | DOI |
|---|---|
| **DOI canónico (usar siempre este)** | https://doi.org/10.5281/zenodo.20393088 |
| DOI versión 3 (PDF con DOI canónico impreso) | https://doi.org/10.5281/zenodo.20393127 |

**Registro público:** https://zenodo.org/record/20393127

---

## Título completo

RFC-ATF-6: Agent Trust Fabric — Behavioral Execution Verification Protocol:
Behavioral Anchor Record, Constraint Conformance Signal,
and Cross-Turn Coherence Hash Chain

---

## Los 3 componentes del RFC

| Componente | Descripción corta |
|---|---|
| **BAR** — Behavioral Anchor Record | Registro firmado PQC de los outputs reales del modelo, vinculado criptográficamente al receipt de gobernanza que autorizó la acción |
| **CCS** — Constraint Conformance Signal | Señal continua que mide si los outputs del modelo se mantienen dentro de los límites definidos en el receipt de gobernanza |
| **CTCHC** — Cross-Turn Coherence Hash Chain | Cadena de hashes turno a turno de los outputs del modelo, vinculada al receipt de gobernanza para verificación forense post-hoc |

---

## Invariantes (18 nuevas — familia BEV)

- BAR: BEV-INV-001 a 004, 015, 016 (6 invariantes)
- CCS: BEV-INV-005 a 009, 017 (6 invariantes)
- CTCHC: BEV-INV-010 a 014, 018 (6 invariantes)

**Total acumulado OMNIX:** 106 invariantes BEV + 125 previas = **completo**

---

## Serie completa de RFCs publicados

| RFC | DOI Zenodo | DOI Figshare |
|---|---|---|
| RFC-ATF-1 | https://doi.org/10.5281/zenodo.20155016 | https://doi.org/10.6084/m9.figshare.32308077 |
| RFC-ATF-2 | https://doi.org/10.5281/zenodo.20241344 | https://doi.org/10.6084/m9.figshare.32308095 |
| RFC-ATF-3 | https://doi.org/10.5281/zenodo.20247342 | https://doi.org/10.6084/m9.figshare.32308119 |
| RFC-ATF-4 | https://doi.org/10.5281/zenodo.20368895 | https://doi.org/10.6084/m9.figshare.32394192 |
| RFC-ATF-5 | https://doi.org/10.5281/zenodo.20391721 | pendiente Figshare |
| RFC-ATF-6 | https://doi.org/10.5281/zenodo.20393088 | pendiente Figshare |

---

## Pendiente

- [ ] Verificar que https://doi.org/10.5281/zenodo.20393088 resuelve y está en estado Published
- [ ] Publicar en Figshare para tener el segundo DOI (como RFC-ATF-1 a 4)

---

## Archivos del paquete

| Archivo | Descripción |
|---|---|
| `RFC-ATF-6.pdf` | Documento principal — 41 páginas · 284 KB |
| `RFC-ATF-6.md` | Spec completo en texto plano |
| `conformance_vectors.json` | 18 invariantes BEV con vectores de conformidad |
| `RFC-ATF-6_SUBMISSION_PACKAGE.zip` | Paquete completo |
