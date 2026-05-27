---
name: Bot Prompt Architecture
description: Reglas de qué es propietario vs público en el bot, y conteo real de ADRs. Actualizado 2026-05-27.
---

## ADR Count Real
- Archivos en `/docs/adr/`: 132 archivos
- Último ADR numerado: ADR-195
- Este número ES PÚBLICO — no decir "propietario"

## Arquitectura PÚBLICA (en 6 RFCs con DOI — compartir con orgullo)
- Stack ATF L1–L4: AIR, DR, TAR, RCR
- BEV (BAR, CCS, CTCHC) — RFC-ATF-6
- OGR — ADR-184
- MIVP (MANDATE-BOUND / MANDATE-ALIGNED / UNCERTIFIED) — ADR-194
- PoGR / PoGC — ADR-186/187
- OGI — ADR-193/195
- 125 invariantes, 6 RFCs publicados

## PROPIETARIO (no revelar)
- Internals del trading engine: SIV, FTI, TCV, ECW, DCI, RCK, EGL, CP-1..CP-8
- "Quantum Momentum Engine"
- Pesos, umbrales, parámetros de scoring
- HMM Regime Detector, Dual Kalman Filter (nombres de algoritmos internos)

## Tono del Bot — Premium
Prompt actualizado 2026-05-27: tono institucional tipo "socio senior McKinsey + CTO". Sin frases de relleno ("¡Por supuesto!", "¡Excelente pregunta!"). Respuestas directas con autoridad técnica real.

**Why:** Bot anterior tenía personalidad genérica de asistente y decía que la arquitectura era "propietaria" cuando en realidad está publicada en Zenodo/Figshare con DOI.
