# OMNIX Protocol Architecture — Implementation Report

**Documento:** PROTOCOL-VISUALIZATION-IMPLEMENTATION-REPORT  
**Fecha:** 2026-05-14  
**Responsable:** OMNIX Governance Integrity Process  
**Estado:** COMPLETADO

---

## 1. Objetivo

Implementar el sistema premium de visualización de arquitectura de protocolo de OMNIX, incluyendo:

1. Cinco diagramas institucionales interactivos
2. ADR-163 — Immutable Evidence Archive Pipeline
3. Página web `/protocol` premium en React
4. Documentación completa en sus ubicaciones canónicas
5. Sin cambios a lógica crítica; sin borrado de datos; sin regresiones

---

## 2. Artefactos Creados

### 2.1 ADRs

| ADR | Título | Archivo | Estado |
|---|---|---|---|
| ADR-163 | Immutable Evidence Archive Pipeline | `docs/adr/ADR-163-immutable-evidence-archive-pipeline.md` | Accepted |

**ADR-163 define:**
- Pipeline HOT→WARM→COLD con reglas de transformación explícitas
- Estructura de bloque COLD (Parquet + SHA-256 block chain + ML-DSA-65 signature)
- 6 invariantes nuevos (EAP-INV-001–006)
- WARM manifest schema (`warm_archive_manifest`)
- Evidence custody log schema (`evidence_custody_log`)
- Trigger de EMERGENCY_COLD en HALT de RGC-INV-003
- Extensión `--archive-block` para el verificador offline (`omnix_atf_verify.py`)
- Modelo de trigger (daily/weekly/on-demand/on-halt)

### 2.2 Frontend — Página `/protocol`

| Artefacto | Archivo | Ruta |
|---|---|---|
| Componente React | `omnix_web/src/pages/ProtocolVisualizationPage.tsx` | `/protocol` |
| Ruta registrada | `omnix_web/src/App.tsx` | `<Route path="/protocol" ...>` |
| Build compilado | `omnix_web/dist/` | Actualizado |

### 2.3 Documentación

| Documento | Cambio |
|---|---|
| `docs/ARCHITECTURE_INDEX.md` | ADR-163 + entrada de página `/protocol` + contador 163 |

---

## 3. Los 5 Diagramas

### Diagrama 1 — Runtime Legitimacy Stack

**Propósito:** Diagrama institucional primario. Arquitectura en 6 capas que representa el stack completo de gobernanza en tiempo de ejecución.

| Capa | Nombre | Color | ADRs |
|---|---|---|---|
| L0 | Human Authority Root | Sovereign Gold | RFC-ATF-1 |
| L1 | Agent Trust Fabric (ATF) | Quantum Cyan | ADR-156/157/158 |
| L2 | Temporal Admissibility | Purple | ADR-157 |
| L3 | Runtime Governance Continuity | Continuity Green | ADR-159/160/161 |
| L4 | Governance Execution Gate | Sovereign Gold | ADR-131/138/147 |
| L5 | Immutable Evidence Lifecycle | Blue | ADR-162/163 |

**Interacción:** Click en cada capa expande artefactos, descripción y referencias ADR.

---

### Diagrama 2 — Execution Legitimacy Chain

**Propósito:** Mostrar cómo se construye la legitimidad de ejecución paso a paso.

**Flow:** Root → DR → TAR → RCR → GovernanceReceipt → COLD Archive

Cada nodo muestra campos canónicos, descripción formal y referencia al invariante aplicable (ATF-INV-006 / EAP-INV-001–005).

**Interacción:** Click en cada nodo del flow muestra panel de detalle con campos clave.

---

### Diagrama 3 — Sovereign Runtime Divergence (GPIL)

**Propósito:** Explicar ADR-161 visualmente. Tres runtimes soberanos con parámetros de política distintos que producen veredictos diferentes (REJECT / ESCALATE / APPROVE) mientras permanecen criptográficamente interoperables.

| Runtime | AFG | TTL | Sampling | Veredicto |
|---|---|---|---|---|
| A — Strict | 0.70 | 120s | DENSE | REJECT |
| B — Balanced | 0.85 | 300s | STANDARD | ESCALATE |
| C — Throughput | 0.95 | 600s | SPARSE | APPROVE |

**Interacción:** Toggle para mostrar la superficie de divergencia completa (5 parámetros).

---

### Diagrama 4 — Runtime Authority Degradation

**Propósito:** Timeline de degradación CES desde admisión hasta HALT. Demuestra continuidad en tiempo de ejecución (RFC-ATF-2).

| Evento | CES | Status | Color |
|---|---|---|---|
| T₀ TAR Admitted | 100 | NOMINAL | Green |
| T₁ Budget Consumption | 74 | MONITORING | Blue |
| T₂ DR Expiry Approaching | 48 | WARNING | Gold |
| T₃ Fragmentation Event | 19 | CRITICAL | Orange |
| T₄ HALT Executed | 0 | HALT | Red |

**Interacción:** 5 botones de timeline. Gauge animado de CES. Anotaciones de invariantes RGC en HALT.

---

### Diagrama 5 — Evidence Custody Lifecycle

**Propósito:** 8 clases de evidencia mapeadas a HOT/WARM/COLD con políticas de retención exactas.

Clases: LEGAL · PQC · CONTRACT · EXCEPTION · TELEMETRY · SAMPLE · SHADOW_NOMINAL · OPS

**Interacción:** Tabla clickeable por fila. Panel de tiers HOT/WARM/COLD arriba. Barra de invariantes ELR/EAP abajo.

---

## 4. Sistema Visual

| Token | Valor | Uso |
|---|---|---|
| OMNIX Black | `#05070B` | Fondo principal |
| Quantum Cyan | `#00E5FF` | Integridad criptográfica · rutas PQC |
| Sovereign Gold | `#F5B942` | Autoridad · delegación · receipts firmados |
| Runtime Red | `#FF4D4D` | HALT · escalación · fragmentación |
| Continuity Green | `#3CFF8F` | Runtime nominal · CES estable |
| Purple | `#A78BFA` | Admisibilidad temporal |
| Blue | `#38BDF8` | Telemetría · MONITORING |

**Tipografía:** Space Grotesk (títulos), Inter (cuerpo). Monospace para IDs y campos de artefactos.

**Estética:** Aerospace-grade dark UI. Bordes con opacidad reducida. Glow dots. Backdrop blur. Sin neon cyberpunk ni dashboard overload.

---

## 5. Nuevos Invariantes Definidos

### ADR-163 — EAP-INV-001–006

| Invariante | Descripción |
|---|---|
| EAP-INV-001 | Verification Preservation — `content_hash` registrado antes de cualquier transformación |
| EAP-INV-002 | PQC Signature Preservation — `pqc_signatures` array intacto en COLD |
| EAP-INV-003 | Block Chain Integrity — `predecessor_block_hash` chain sin interrupciones |
| EAP-INV-004 | Immutable Class Permanence — LEGAL/PQC/CONTRACT/EXCEPTION sin stripping |
| EAP-INV-005 | Offline Reconstructability — verificación completa sin runtime, DB, ni APIs |
| EAP-INV-006 | Manifest Completeness — toda transición crea entrada en manifest |

**Total de invariantes OMNIX tras ADR-163:** ATF-INV-001–006 (RFC-ATF-1) + RGC-INV-001–008 (RFC-ATF-2) + ELR-INV-001–004 (ADR-162) + EAP-INV-001–006 (ADR-163) = **24 invariantes formales**.

---

## 6. Posicionamiento Arquitectural

La página `/protocol` cierra con el posicionamiento correcto de OMNIX:

> *"Runtime legitimacy infrastructure for autonomous systems. Not after execution. Not reconstructed later. At the exact moment authority is exercised — and preserved immutably afterward."*

**OMNIX no es:**
- AI assistant, agent platform, orchestration tool, governance dashboard, observability wrapper

**OMNIX es:**
- Runtime legitimacy infrastructure
- Operational governance protocol
- Autonomous systems trust architecture
- Cryptographically verifiable authority layer
- Immutable evidence custody infrastructure

---

## 7. Integridad — Verificación de Restricciones

| Restricción | Cumplimiento |
|---|---|
| No cambiar lógica crítica sin auditar | ✓ — Cero cambios a código de producción |
| No borrar datos | ✓ — Solo artefactos nuevos creados |
| Crear tests si se toca código | ✓ — No se tocó código de producción |
| Build sin errores | ✓ — `npm run build` exitoso |
| Coherencia con stack ATF/RGC/GPIL/ELR | ✓ — Todos los ADRs referenciados correctamente |

---

## 8. URLs Disponibles

| URL | Contenido |
|---|---|
| `/protocol` | Página de visualización — 5 diagramas premium |
| `/atf-standard` | ATF Standard (RFC-ATF-1/2) |
| `/atf-verify` | Verificador de receipts |
| `/atf-explained` | ATF explicado |
| `/agent-trust-fabric` | ATF con simulación live |

---

## 9. Resumen de Archivos Modificados/Creados

| Archivo | Operación |
|---|---|
| `docs/adr/ADR-163-immutable-evidence-archive-pipeline.md` | CREADO |
| `omnix_web/src/pages/ProtocolVisualizationPage.tsx` | CREADO |
| `omnix_web/src/App.tsx` | EDITADO — ruta `/protocol` agregada |
| `omnix_web/dist/` | ACTUALIZADO — build compilado |
| `docs/ARCHITECTURE_INDEX.md` | EDITADO — ADR-163 + `/protocol` |

---

*Implementación completada. OMNIX Protocol Architecture Visualization System operacional en `/protocol`.*
