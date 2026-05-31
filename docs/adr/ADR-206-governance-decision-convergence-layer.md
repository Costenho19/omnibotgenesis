# ADR-206 — Governance Decision Convergence Layer (GDCL)

**Status:** ACCEPTED  
**Fecha:** 2026-05-31  
**Autor:** Harold Nunes — OMNIX QUANTUM LTD  
**Relates to:** ADR-173 (DSPP) · RFC-ATF-4 (RSA/DSPP) · ADR-184 (OGR) · ADR-194 (MIVP)

---

## Context

El Dynamic Semantic Portability Protocol (DSPP, RFC-ATF-4, ADR-173) define la
Retroactive Semantic Assessment (RSA) como un artefacto computado localmente y offline
que responde la pregunta: *¿es este recibo semánticamente portable en este dominio?*

La RSA opera **por recibo**: una entrada, un veredicto (`SEMANTICALLY_PORTABLE` /
`DRIFT_ACKNOWLEDGED` / `DRIFT_CRITICAL` / `SEMANTICALLY_INCOMPATIBLE`).

En escenarios reales de producción, un dominio receptor no evalúa un solo objeto de prueba.
Evalúa **N objetos heterogéneos simultáneamente** antes de comprometer una decisión local.
Ejemplo canónico (sector salud, trazado por Peter Cranstone / 3PMobile):

> Farmacia (PORTABLE) + Pagador (DRIFT_CRITICAL) + Urgencias (PORTABLE) +  
> Reclamaciones (DRIFT_ACKNOWLEDGED) + Auditoría (PORTABLE) → **una sola decisión local**

RFC-ATF-4 no especifica un protocolo de agregación multi-RSA. Eso es intencional: el RFC
define el primitive (RSA individual); la composición es la siguiente capa. Este ADR
formaliza esa capa.

**El problema de convergencia:** dado un conjunto arbitrario de RSAs de fuentes
heterogéneas, ¿cuál es el resultado de boundary tipado que debe guiar la decisión local?
Sin un protocolo formal, cada implementación construye su propia heurística, destruyendo
la interoperabilidad y la auditabilidad.

---

## Decision

Introducir el **Governance Decision Convergence Layer (GDCL)** como la capa de agregación
normativa sobre DSPP. El GDCL:

1. Ingiere N objetos `RetroactiveSemanticAssessment` de fuentes heterogéneas.
2. Aplica un algoritmo de convergencia determinista con prioridad de peor caso.
3. Emite un **`GDCLConvergenceRecord` (GCR)** — artefacto de gobernanza firmado PQC —
   con un único veredicto compuesto tipado.
4. Persiste el GCR en DB (append-only), referenciable por receipt_ids y rsa_ids.

El GDCL **no reemplaza** el DSPP. Opera sobre los outputs del DSPP. La relación es
exactamente análoga a la de OGR (ADR-184) sobre BAR+CCS+MAS: las capas primitivas
producen señales per-turn; la capa superior produce el veredicto de sesión compuesto.

---

## Taxonomía de Veredictos Compuestos

El GDCL emite uno de siete veredictos compuestos. La definición es exhaustiva y exclusiva
(GDCL-INV-001 + GDCL-INV-002).

| Veredicto Compuesto | Significado | Equivalente Peter Cranstone |
|---|---|---|
| `FULL_RELIANCE` | Todos los RSAs = SEMANTICALLY_PORTABLE | accepted |
| `QUALIFIED_RELIANCE` | Peor = DRIFT_ACKNOWLEDGED; sin CRITICAL ni INCOMPATIBLE | limited reliance (minor) |
| `LIMITED_RELIANCE` | Algún DRIFT_CRITICAL; sin INCOMPATIBLE | limited reliance (major) |
| `CONTESTED` | INCOMPATIBLE coexiste con PORTABLE/ACKNOWLEDGED; sin CRITICAL | conflict |
| `REFUSED` | Todos los RSAs = SEMANTICALLY_INCOMPATIBLE | refused |
| `ESCALATION` | INCOMPATIBLE + DRIFT_CRITICAL simultáneos | escalation (human review req.) |
| `INDETERMINATE` | Input vacío | indeterminate |

---

## Algoritmo de Convergencia

El algoritmo es una función pura (GDCL-INV-003): mismos inputs → mismo output.
Implementa prioridad de peor caso, ordenada de mayor a menor severidad:

```
converge(rsa_list: List[RSA]) → GDCLCompositeVerdict:

  si rsa_list = ∅:
    devolver INDETERMINATE

  sea has_incompatible = ∃ r ∈ rsa_list: r.dspp_verdict = SEMANTICALLY_INCOMPATIBLE
  sea has_critical     = ∃ r ∈ rsa_list: r.dspp_verdict = DRIFT_CRITICAL
  sea has_acknowledged = ∃ r ∈ rsa_list: r.dspp_verdict = DRIFT_ACKNOWLEDGED
  sea has_portable     = ∃ r ∈ rsa_list: r.dspp_verdict = SEMANTICALLY_PORTABLE
  sea n_incompatible   = |{r ∈ rsa_list: r.dspp_verdict = SEMANTICALLY_INCOMPATIBLE}|
  sea n                = |rsa_list|

  Paso 1: si has_incompatible ∧ has_critical:
    devolver ESCALATION  -- fuentes en conflicto severo; revisión humana obligatoria

  Paso 2: si n_incompatible = n:
    devolver REFUSED  -- unanimidad de incompatibilidad

  Paso 3: si has_incompatible ∧ (has_portable ∨ has_acknowledged):
    devolver CONTESTED  -- fuentes discrepan; ninguna puede prevalecer

  Paso 4: si has_critical:
    devolver LIMITED_RELIANCE  -- ninguna incompatibilidad pero divergencia significativa

  Paso 5: si has_acknowledged:
    devolver QUALIFIED_RELIANCE  -- drift resolvable bajo MORE_RESTRICTIVE

  Paso 6:
    devolver FULL_RELIANCE  -- todas las fuentes semánticamente portables
```

### Prueba de exhaustividad e independencia (Z3 provable)

Toda combinación posible de {PORTABLE, ACKNOWLEDGED, CRITICAL, INCOMPATIBLE}^N es
capturada por exactamente uno de los siete veredictos. Los 6 pasos son disjuntos porque
el Paso 1 es evaluado antes del Paso 2 (ESCALATION domina sobre REFUSED), etc.

---

## Artefacto: GDCLConvergenceRecord (GCR)

```
GCR
├── gcr_id              — "OMNIX-GCR-{16HEX}"
├── receiving_runtime_id — runtime que solicita la convergencia
├── rsa_ids             — [RSA IDs ingestados, ordenados]
├── receipt_ids         — [receipt IDs cubiertos por los RSAs]
├── n_assessments       — |rsa_ids|
├── verdict_distribution — {dspp_verdict: count} — breakdown completo
├── composite_verdict   — GDCLCompositeVerdict (uno de siete)
├── dominant_sdu        — max(aggregate_sdu) entre todos los RSAs
├── mean_sdu            — mean(aggregate_sdu)
├── min_portability_confidence — min(portability_confidence)
├── boundary_recommendation — recomendación operacional legible
├── converged_at        — timestamp ISO UTC
├── content_hash        — SHA3-256 de campos canónicos
├── pqc_signature       — ML-DSA-65 sobre content_hash
├── pqc_algorithm       — "ML-DSA-65"
└── created_at          — timestamp ISO UTC
```

**Tabla DB:** `atf_gdcl_convergence_records`

---

## Invariantes GDCL (GDCL-INV-001 a GDCL-INV-006)

### GDCL-INV-001 — Exhaustividad de Taxonomía
∀ conjunto de RSAs no vacío: exactamente un veredicto compuesto aplica.
Los siete veredictos forman una partición exhaustiva del espacio de inputs posibles.

### GDCL-INV-002 — Exclusividad Mutua
FULL_RELIANCE y REFUSED son mutuamente excluyentes.
ESCALATION implica ¬REFUSED (ESCALATION es más severo que REFUSED porque requiere
acción humana sobre un conflicto activo, mientras REFUSED es un rechazo limpio).

### GDCL-INV-003 — Determinismo
El GDCL es una función pura:
∀ (rsa_list_A, rsa_list_B): sorted(rsa_ids_A) = sorted(rsa_ids_B) →
  composite_verdict_A = composite_verdict_B.

### GDCL-INV-004 — Degradación N=1
Para N=1 RSA, el veredicto compuesto degenera al veredicto DSPP individual:
  SEMANTICALLY_PORTABLE     → FULL_RELIANCE
  DRIFT_ACKNOWLEDGED        → QUALIFIED_RELIANCE
  DRIFT_CRITICAL            → LIMITED_RELIANCE
  SEMANTICALLY_INCOMPATIBLE → REFUSED

### GDCL-INV-005 — Independencia de Reconstrucción Upstream
El GDCL opera únicamente sobre objetos RSAResult ya computados.
No accede a TSAs, SDRs, SPVs ni cadenas de delegación originantes.
No requiere contacto con runtimes originantes (extends DSPP-INV-004).

### GDCL-INV-006 — Trazabilidad de Artefacto
Todo GCR es persistido append-only, firmado PQC, y referencia explícitamente
todos los RSA IDs y receipt IDs que contribuyeron a su veredicto.
Un veredicto GDCL es siempre reconstructible desde los RSAs que lo originaron.

---

## Consecuencias Operacionales

**ESCALATION:** El dominio receptor DEBE detenerse y elevar a revisión humana.
Está prohibido comprometer la decisión local bajo ESCALATION sin autorización explícita.

**REFUSED:** El dominio receptor DEBE rechazar la operación. Equivale a HALT en el
vocabulario del OGR.

**CONTESTED:** El dominio receptor DEBE documentar el conflicto antes de cualquier
acción. Una fuente INCOMPATIBLE no puede ser ignorada solo porque otras son PORTABLE.

**LIMITED_RELIANCE:** Requiere documentación explícita del DRIFT_CRITICAL antes de
usar el resultado en contexto regulatorio (consistent with DSPP §7.4 DRIFT_CRITICAL
disposition).

**QUALIFIED_RELIANCE:** Aplicar MORE_RESTRICTIVE governing posture per DSPP-INV-003.

**FULL_RELIANCE:** Sin restricciones adicionales. El receipt puede usarse sin
calificación semántica en el dominio receptor.

---

## Correspondencia con DSPP-INV-006

`DSPP-INV-006` especifica que SEMANTICALLY_INCOMPATIBLE se propaga hacia arriba en
la cadena de delegación. El GDCL extiende esta semántica horizontalmente: en un conjunto
de N recibos heterogéneos, la presencia de INCOMPATIBLE contamina el resultado compuesto
hasta CONTESTED, REFUSED, o ESCALATION, dependiendo del contexto. La propagación
vertical (DSPP-INV-006) y la convergencia horizontal (GDCL) son complementarias.

---

## Tabla DB

```sql
CREATE TABLE IF NOT EXISTS atf_gdcl_convergence_records (
    gcr_id                      VARCHAR(128)    PRIMARY KEY,
    receiving_runtime_id        VARCHAR(128)    NOT NULL,
    rsa_ids                     JSONB           NOT NULL DEFAULT '[]',
    receipt_ids                 JSONB           NOT NULL DEFAULT '[]',
    n_assessments               INTEGER         NOT NULL CHECK (n_assessments >= 0),
    verdict_distribution        JSONB           NOT NULL DEFAULT '{}',
    composite_verdict           VARCHAR(32)     NOT NULL
                                    CHECK (composite_verdict IN (
                                        'FULL_RELIANCE','QUALIFIED_RELIANCE',
                                        'LIMITED_RELIANCE','CONTESTED',
                                        'REFUSED','ESCALATION','INDETERMINATE'
                                    )),
    dominant_sdu                NUMERIC(6,4)    NOT NULL,
    mean_sdu                    NUMERIC(6,4)    NOT NULL,
    min_portability_confidence  NUMERIC(6,4)    NOT NULL,
    boundary_recommendation     TEXT            NOT NULL,
    converged_at                TIMESTAMPTZ     NOT NULL,
    content_hash                VARCHAR(64)     NOT NULL,
    pqc_signature               TEXT            DEFAULT NULL,
    pqc_algorithm               VARCHAR(32)     DEFAULT NULL,
    created_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_atf_gcr_runtime
    ON atf_gdcl_convergence_records (receiving_runtime_id);
CREATE INDEX IF NOT EXISTS idx_atf_gcr_verdict
    ON atf_gdcl_convergence_records (composite_verdict);
CREATE INDEX IF NOT EXISTS idx_atf_gcr_converged_at
    ON atf_gdcl_convergence_records (converged_at DESC);
```

---

## Implementación

`omnix_core/atf/gdcl.py` — `GDCLEngine` class:

- `converge(rsa_results, receiving_runtime_id)` → `GDCLConvergenceRecord`
- `verify_convergence_record(gcr)` → `dict` (integrity check)
- `ensure_tables()` → idempotent DDL
- `get_record(gcr_id)` → `Optional[GDCLConvergenceRecord]`

Patrón: idéntico al `DSPPEngine` (ADR-173) — DB opcional, PQC-signed, pure-function core.

---

## Relación con RFC Future

El GDCL es candidato natural para inclusión en un futuro **RFC-ATF-7** que especifique
la capa de orquestación multi-fuente sobre el stack ATF L1–L6. Esta especificación
(ADR-206) es la referencia de implementación de OMNIX. Una especificación RFC completa
añadiría wire format, interoperabilidad cross-vendor, y protocolo de negociación de SDR
chains entre runtimes heterogéneos.

---

## Registro de Cambios

| Versión | Fecha | Autor | Cambio |
|---|---|---|---|
| 1.0.0 | 2026-05-31 | Harold Nunes | ADR inicial — GDCL spec completa |
