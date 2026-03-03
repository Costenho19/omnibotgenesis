# OMNIX — Mentor Feedback: Eureka Dubai 2026

**Classification**: Internal — Competition Preparation  
**Date**: March 3, 2026  
**Context**: Mentor reviewed the 5-7 minute presentation script acting as a simulated Eureka Dubai judge  
**Audience**: Harold Nunes — internal preparation only

---

## Overall Assessment

| Dimension | Score |
|-----------|-------|
| Estructura | 9/10 |
| Narrativa | 9/10 |
| Claridad | 8/10 |
| Riesgo técnico percibido | 7/10 |
| Confianza del fundador | Depende del delivery |
| **Promedio actual** | **8.3/10** |
| **Proyectado con ajustes** | **9.2/10** |

**Veredicto del mentor:** "¿Está listo para escenario? Sí. Está arriba del promedio. Pero para FINALISTA necesitas: 10% más claridad, 5% menos técnico en Tech Moat, 10% más visión en cierre."

---

## What the Mentor Said Is EXCELLENT (Do Not Change)

### 1. El Hook — "When should I NOT act?"
> "Eso es brillante. Eso hace que la gente piense. Eso te diferencia. Mantén eso."

### 2. La estructura por bloques cortos
> "Frases simples. Pausas. Lenguaje claro. Eso es oro en escenario."

### 3. El ejemplo de Bitcoin (Feb 3, 2026)
> "Eso es lo que hace que el jurado entienda. No es abstracto. Es real. Es visual. Muy bien."

### 4. La línea de cierre
> "'The best decision is often the one you don't make.' — Eso se queda en la cabeza. Eso es pitch ganador."

---

## The 3 Adjustments (Applied March 3, 2026)

### Adjustment #1: "47 high-risk trades" — Add methodological clarity

**Mentor's concern:**
> "Cuidado con 'Forty-seven high-risk trades blocked.' Eso puede generar preguntas duras como: ¿Qué es high-risk? ¿Cómo defines correct? ¿Quién valida? ¿Qué dataset? ¿Auditado por quién? Tienes que estar listo con respuesta técnica precisa."

**Risk identified:** The term "high-risk" is ambiguous and invites aggressive follow-up from judges who want to see methodology.

**Change applied:**
- Removed: `"high-risk signals"`
- Added: `"signals blocked by the governance engine"` + `"validated against subsequent 48-hour price data"` + `"Internal dataset"`

**Files modified:**
- `docs/business/EUREKA_PRESENTATION_SCRIPT.md` — Traction section (line 98)
- `docs/business/OMNIX_EUREKA_PITCH_FINAL.md` — Slide 6, Traction table
- `docs/business/EUREKA_JUDGE_QA_PREPARATION.md` — Added 2 new defensive Q&As

---

### Adjustment #2: "Why Me" — Key-person risk framing

**Mentor's concern:**
> "El 'Why Me' es fuerte pero vulnerable. 'Three months. Personal capital. No team.' — Eso es épico. Pero también suena a 'key person risk.' En Dubai, eso importa."
>
> "Instead of: 'No team. No investors.' — Di algo más estratégico: 'Lean, focused build. Governance-first architecture.'"
>
> "Porque algunos jueces pueden pensar: ¿Y si tú desapareces?"

**Risk identified:** "No team. No investors." signals vulnerability to judges focused on key-person risk, which is a known concern for ADGM/institutional investors.

**Change applied:**
- Removed: `"No team. No investors. No safety net."`
- Added: `"Lean, focused build. Governance-first architecture."`

**Files modified:**
- `docs/business/EUREKA_PRESENTATION_SCRIPT.md` — Why Me section (line 110)
- `docs/business/OMNIX_EUREKA_PITCH_FINAL.md` — Slide 12, Founder Why Me paragraph

**Note:** Key-person risk is still addressed directly in `EUREKA_JUDGE_QA_PREPARATION.md` (Category 2). The adjustment changes the proactive framing in the pitch — the defensive answer remains available for Q&A.

---

### Adjustment #3: Business Model — Add urgency line

**Mentor's concern:**
> "El Business Model está bien… pero no emociona. Es correcto. Es lógico. Pero no muestra urgencia."
>
> "Agrega una frase así: 'Institutions are not asking if they need governance. They are asking how soon they can implement it.' — Eso cambia el tono."

**Risk identified:** Revenue projections without urgency framing read as theoretical. The mentor wants the audience to feel the demand is live, not anticipated.

**Change applied:**
- Added line after Year 3 revenue projection:
- `"Institutions are not asking if they need governance. They are asking how soon they can implement it."`

**Files modified:**
- `docs/business/EUREKA_PRESENTATION_SCRIPT.md` — Business Model section (after Year 3 line)
- `docs/business/OMNIX_EUREKA_PITCH_FINAL.md` — Slide 9, after Revenue Projections table

---

## Delivery Notes (Mentor's Exact Words)

| Condition | Mentor's Statement |
|-----------|-------------------|
| Timing | "Lo dices lento. No suenas memorizado. Lo dices con convicción real. No corres." |
| Key numbers | Pause BEFORE "670,000+". Pause AFTER "98.5%". |
| Closing line | "Final. Slow. No trailing off." |
| Standing | "Stand still. Plant your feet." |
| Voice | "Voice low and steady. Confidence comes from calm, not volume." |

---

## Files Modified in This Review Cycle

| File | Changes Applied |
|------|----------------|
| `docs/business/EUREKA_PRESENTATION_SCRIPT.md` | Adjustments #1, #2, #3 |
| `docs/business/OMNIX_EUREKA_PITCH_FINAL.md` | Adjustments #1, #2, #3 |
| `docs/business/EUREKA_JUDGE_QA_PREPARATION.md` | 2 new Q&As: methodology + external audit |
| `docs/business/OMNIX_PITCH_SCRIPTS.md` | Metadata: Version 1.1, MENTOR-REVIEWED, Mar 3, 2026 |
| `docs/business/MENTOR_FEEDBACK_EUREKA_2026.md` | This file (created) |

---

## Compliance Check (Post-Adjustment)

| ADR-027 Rule | Status After Adjustments |
|--------------|--------------------------|
| No supremacy claims | PASS |
| "Building the category" language | PASS |
| Anti-abstraction rule (metric within 2 sentences) | PASS |
| "First validated in digital asset trading" present | PASS |
| "Internal dataset" disclosed where applicable | PASS — added to 47-signal reference |
| Key-person risk framing strategic, not defensive | PASS — "Lean, focused build" |
| Urgency in business model | PASS — urgency line added |

---

*OMNIX — Governing Decisions Under Uncertainty*  
*Eureka Dubai 2026 — Semifinalist*  
*Deadline: March 15, 2026*
