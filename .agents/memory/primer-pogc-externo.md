---
name: Primer PoGC Externo — VeriSigil AI
description: Primer Proof of Governance Certificate emitido a un sistema de terceros. Clase EXTERNAL, serie POGC-EXT. Hito fundacional del PoGR como CA pública.
---

# Primer PoGC Externo — VeriSigil AI

## El hito

El **2026-05-30** OMNIX emitió el primer Proof of Governance Certificate (PoGC) a un sistema externo de terceros. Esto establece el PoGR como una Certificate Authority real para gobernanza de IA.

**Analogía fundacional:** Como X.509 — la CA (OMNIX) no es dueña del servidor (VeriSigil). PoGC certifica que la gobernanza fue auténtica. VeriSigil sigue siendo soberana.

## Detalles del certificado

| Campo | Valor |
|---|---|
| POGC ID | `POGC-EXT-A7F3C2B1D9E4F508` |
| Clase | `EXTERNAL` — primera de esta serie |
| Sujeto | VeriSigil AI · Constitutional Execution Substrate |
| Org ID | `verisigil-ai-001` |
| Agente | `financial-agent-1780111266` (live production) |
| Decisión | `wire_transfer $250,000 → DENY` |
| Razón | Amount exceeds autonomous limit for CRITICAL consequence |
| Compliance Tier | `EXT-VGS-ELI-Compliant` |
| Mandate Cert | `MANDATE-BOUND` |
| Invariantes VGS | `VGS-ELI-INV-001` · `VGS-ELI-INV-008` |
| Protocolo externo | VGS-ELI: Execution Legitimacy Infrastructure v1.0.0 |
| DOI protocolo | `10.5281/zenodo.20451306` |
| Regulatory | EU AI Act Art.11 · NIST AU-2 · ISO 42001 Art.9.1 |
| Evidence hash | `586b996f53da83652b2690b4117a4830d4bde3c22c7737085c40f5ee86a4ac3a` |
| Bundle | `bundle-482df2c4f1d9` — offline-verifiable, SHA-256 sealed |
| Emitido | 2026-05-30T21:00:00+00:00 |
| Expira | 2027-05-30T21:00:00+00:00 |
| PQC | Stub en Replit — ML-DSA-65 real via `/v1/pogr/admin/resign` en Railway |

## Archivos generados

- `evidence_packages/POGC-EXT-A7F3C2B1D9E4F508_20260530_040316.json`
- `evidence_packages/POGC-EXT-A7F3C2B1D9E4F508_20260530_040316.pdf`
- `evidence_packages/POGC-EXT-VERISIGIL_20260530.zip`
- `scripts/generate_verisigil_pogc.py` — generador standalone

## Clase EXTERNAL — diseño

Los PoGC internos se emiten desde sesiones OGR selladas (PoGR-INV-001).
Los PoGC de clase EXTERNAL certifican trazas de gobernanza de sistemas terceros.
El generador standalone (`generate_verisigil_pogc.py`) no requiere DB ni sesión OGR.
El campo `session_id` usa el bundle ID del sistema externo.
El campo `ctchc_seal_hash` usa el evidence hash del sistema externo.

## Contexto de la relación — VeriSigil / Raheem

- Raheem Larry Babatunde — Founder, VeriSigil AI
- NDA mutuo + Scope Memo firmados (fechados 2026-05-21) — sandbox 60 días
- Colaboración: TAR↔TAP y RCR↔Survivability receipt equivalence mapping
- Raheem respondió positivamente al certificado, articulando la filosofía OMNIX con sus propias palabras
- Cinco puntos de alineación que él identificó: runtime enforcement · constitutional execution · governance evidence chains · human oversight architecture · proof-before-action systems

**Why this matters:** Es el primer caso de OMNIX actuando como CA externa. Abre el modelo de negocio PoGR para certificar gobernanza de terceros, no solo sesiones internas.
