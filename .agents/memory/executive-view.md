---
name: Executive View Page
description: Página React premium /executive para C-suite — sin jerga técnica, métricas visuales, narrativa en lenguaje ejecutivo.
---

# ADR-191 — Executive View

**Why:** Todos los dashboards OMNIX hablan el idioma de ingenieros. El comprador económico es el C-suite. Gap identificado vs UHG-Tech L'OMBRE.

**How to apply:**
- Archivo: `omnix_web/src/pages/ExecutiveViewPage.tsx`
- Ruta: `/executive` en App.tsx
- Datos: demo estático (illustrative) — para datos reales necesita API key integration
- Diseño: dark #060F1E, gold #C9A227, health ring SVG, timeline, FAQ toggles
- EV-INV-001: NO mostrar hashes/firmas en viewport principal
- EV-INV-003: accesible sin autenticación (modo demo público)
