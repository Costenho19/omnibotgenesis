# RFC-ATF-6 — Zenodo Submission Review
## OMNIX QUANTUM LTD — Harold Nunes, Editor

**Status:** PUBLISHED ✅ — DOI: 10.5281/zenodo.20393089 — Record: https://zenodo.org/record/20393089

---

## Package Contents

| File | Status | Description |
|------|--------|-------------|
| `docs/zenodo/rfc_atf_6/RFC-ATF-6.pdf` | ✅ Generated | PDF premium — 8 diagrams |
| `docs/standards/RFC-ATF-6.md` | ✅ Ready | Full RFC spec — 3388 lines |
| `docs/zenodo/rfc_atf_6/metadata.json` | ✅ Updated | Abu Dhabi removed · DOIs actualizados |
| `docs/zenodo/rfc_atf_6/conformance_vectors.json` | ✅ Created | 18 BEV invariants estructurados |
| `docs/zenodo/rfc_atf_6/publish_to_zenodo.py` | ✅ Created | Listo pero NO ejecutar aún |
| `docs/zenodo/rfc_atf_6/SUBMISSION_REVIEW.md` | ✅ This file | Checklist de revisión |

---

## Pre-Publication Checklist

### Contenido
- [ ] Harold ha revisado el PDF y aprueba el contenido
- [ ] Los 8 diagramas son correctos y visualmente aceptables
- [ ] Los 18 invariantes están completos y correctos
- [ ] Las fórmulas técnicas (content_hash, chain_link, genesis_hash) son correctas
- [ ] La tabla de compliance hierarchy es correcta (6 tiers, 106 invariantes)
- [ ] Las references incluyen los DOIs correctos de RFC-ATF-1 a RFC-ATF-5

### Metadata
- [ ] Abu Dhabi eliminado del metadata.json ✅
- [ ] RFC-ATF-4 DOI: `10.5281/zenodo.20368895` — **VERIFICAR que resuelve en Zenodo**
- [ ] RFC-ATF-5 DOI: `10.5281/zenodo.20391721` — **VERIFICAR que resuelve en Zenodo**
- [ ] Licencia: `CC-BY-4.0` (igual que los anteriores) ✅
- [ ] Fecha de publicación: `2026-05-26` — ajustar si se publica en otra fecha

### Spec (RFC-ATF-6.md)
- [ ] Abu Dhabi eliminado del Author's Address ✅
- [ ] DOI header actualizado con el DOI real después de publicar
- [ ] STATUS cambiado de DRAFT a PUBLISHED después de publicar

---

## DOIs de Referencias — Estado

| RFC | Zenodo DOI | Estado requerido |
|-----|-----------|-----------------|
| RFC-ATF-1 | 10.5281/zenodo.20155016 | Verificado Published ✅ |
| RFC-ATF-2 | 10.5281/zenodo.20241344 | Verificado Published ✅ |
| RFC-ATF-3 | 10.5281/zenodo.20247342 | Verificado Published ✅ |
| RFC-ATF-4 | 10.5281/zenodo.20368895 | **VERIFICAR antes de publicar** |
| RFC-ATF-5 | 10.5281/zenodo.20391721 | **VERIFICAR antes de publicar** |

---

## 8 Diagramas del PDF

| # | Figura | Contenido |
|---|--------|-----------|
| 1 | ATF 6-Layer Stack | Las 6 capas del protocol stack — BEV en dorado arriba |
| 2 | Three Behavioral Gaps | Gap_BAG → BAR · Gap_COP → CCS · Gap_MCP → CTCHC |
| 3 | BAR Architecture Flow | pipeline de creación del BAR con fórmulas |
| 4 | CCS Score Breakdown | 4 componentes (OBS/CSS/SDS/AAS) + verdict ladder |
| 5 | CCS-AGVP Integration Loop | Behavioral conformance → anticipatory veto |
| 6 | CTCHC Chain Structure | Genesis → Links → Chain Seal (SIP) |
| 7 | ATF Compliance Hierarchy | 6 tiers de compliance (pirámide) |
| 8 | BEV Turn Execution Timeline | 9 pasos ordenados por turno |

---

## Cómo publicar cuando Harold apruebe

```bash
# 1. Verificar que el PDF existe
ls -lh docs/zenodo/rfc_atf_6/RFC-ATF-6.pdf

# 2. Verificar DOIs de RFC-ATF-4 y RFC-ATF-5 en zenodo.org

# 3. Publicar
export ZENODO_TOKEN=<tu_token_de_zenodo>
python docs/zenodo/rfc_atf_6/publish_to_zenodo.py

# 4. Copiar DOI del output

# 5. Actualizar replit.md tabla RFC-ATF-6

# 6. Actualizar docs/standards/RFC-ATF-6.md header DOI field
```

---

## Diferencias con RFC-ATF-5

| Aspecto | RFC-ATF-5 | RFC-ATF-6 |
|---------|-----------|-----------|
| Diagramas | 5 | 8 |
| Invariantes nuevos | 18 (CGE/GUGT/TGB) | 18 (BAR/CCS/CTCHC) |
| Compliance tier | ATF-CGL-Compliant | ATF-BEV-Compliant (6to, más alto) |
| Total invariantes ATF | 88 | 106 |
| DOI Figshare | Pendiente | Pendiente (publicar después de Zenodo) |
| Abu Dhabi | Eliminado ✅ | Eliminado ✅ |

---

*Generado: 2026-05-26 — OMNIX QUANTUM LTD*
