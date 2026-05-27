# OMNIX QUANTUM — Decision Governance Infrastructure

Plataforma de gobernanza de decisiones auditable, con IA y criptografía post-cuántica (Dilithium-3).
Empresa: OMNIX QUANTUM LTD (UK) · Fundador: Harold Nunes.

**Índice de arquitectura completo:** `docs/ARCHITECTURE_INDEX.md`

**RFCs publicados — DOIs canónicos:**
| RFC | Zenodo | Figshare |
|---|---|---|
| RFC-ATF-1 | https://doi.org/10.5281/zenodo.20155016 | https://doi.org/10.6084/m9.figshare.32308077 |
| RFC-ATF-2 | https://doi.org/10.5281/zenodo.20241344 | https://doi.org/10.6084/m9.figshare.32308095 |
| RFC-ATF-3 | https://doi.org/10.5281/zenodo.20247342 | https://doi.org/10.6084/m9.figshare.32308119 |
| RFC-ATF-4 | https://doi.org/10.5281/zenodo.20368895 | https://doi.org/10.6084/m9.figshare.32394192 |
| RFC-ATF-5 | https://doi.org/10.5281/zenodo.20391721 | — (pendiente Figshare) |
| RFC-ATF-6 | https://doi.org/10.5281/zenodo.20393088 | https://doi.org/10.6084/m9.figshare.32407080 |

---

## Run & Operate

- **Desarrollo:** `python run_services.py` (bot, Flask dashboard, simulators)
- **API Producción:** `python api/server.py`
- **Build Frontend:** `cd omnix_web && npm run build` — hacer commit del `dist/` después de cada cambio React
- **DB Migrations:** Railway ejecuta DDL automáticamente via `CREATE TABLE IF NOT EXISTS` en primer request

---

## Stack

- **Frontend:** React 18 · Vite 7 · TypeScript · Tailwind CSS
- **Backend:** Python 3.11 · Flask
- **Database:** PostgreSQL (Railway managed)
- **Cache / Anti-replay:** Redis (Railway managed)
- **PQC:** Dilithium-3 (ML-DSA-65, FIPS 204) · Kyber-768
- **AI fallback chain:** OpenAI GPT-4o-mini → GPT-4o → Gemini 2.5 Flash → Anthropic Claude

---

## Where Things Live

- `/omnix_web/` — React SPA + Flask API (`api/server.py`, `api/gov_blueprint.py`, `api/sandbox.py`)
  - `omnix_web/src/pages/` — 65 páginas React · `App.tsx` tiene todas las rutas
  - `omnix_web/dist/` — Build compilado. Flask lo sirve en producción
- `/omnix_dashboard/` — Dashboard operacional Flask (Jinja2) · `/terminal` y `/classic` viven aquí
- `/omnix_services/` — Telegram bot · AI service · coherence · trading
- `/omnix_core/` — Governance engine · PQC security · receipts · AVM · ATF
  - `omnix_core/agents/atf/` — Agent Trust Fabric: DR · TAR · DTR · RCR · AFG · RC
  - `omnix_core/bev/` — Behavioral Execution Verification: BAR · CCS · CTCHC (RFC-ATF-6, ADR-181/182/183)
  - `omnix_core/govern/` — OGR Orchestrator: `governance_runtime.py` — 6-layer session lifecycle (ADR-184)
- `/docs/adr/` — **132 archivos ADR, último numerado ADR-195**. Fuente de verdad de arquitectura
- `/docs/standards/` — RFC-ATF-1 (publicado) · RFC-ATF-2 (publicado) · RFC-ATF-3 (publicado) · RFC-ATF-4 (publicado) · RFC-ATF-5 (pendiente publicación Zenodo)
- `/docs/integration/` — `OMNIX_GOVERNANCE_RUNTIME.md` · `GETTING_STARTED.md` — integration product docs
- `/sdk/` — Python SDK · Node.js SDK

---

## Variables de Entorno — Referencia Canónica

### Flask Web API (`omnix_web/api/server.py`)

| Variable | Descripción | Estado |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | **REQUIRED** |
| `REDIS_URL` | Redis anti-replay + cache | **REQUIRED** |
| `GEMINI_API_KEY` | AI governance engine | **REQUIRED** — billing activo en GCP |
| `OMNIX_WEB_URL` | Webhook callbacks base URL | **REQUIRED** |
| `VITE_RAILWAY_API_URL` | Frontend build-time API URL | **REQUIRED** |
| `OMNIX_SIGNING_SECRET_KEY_B64` | Dilithium-3 private key (base64) | **REQUIRED** — presente en Railway ✓ |
| `OMNIX_SIGNING_PUBLIC_KEY_B64` | Dilithium-3 public key (base64) | **REQUIRED** — presente en Railway ✓ |
| `PAYLOAD_ENCRYPTION_KEY` | Fernet webhook encryption | REQUIRED para webhooks cifrados |
| `OPENAI_API_KEY` | AI fallback | Optional |
| `ANTHROPIC_API_KEY` | AI fallback | Optional |
| `ADMIN_ALLOWED_IPS` | IPs para endpoints admin | Optional — default: solo 127.0.0.1 |
| `OMNIX_ANTI_REPLAY_MODE` | `strict` o `best_effort` | Optional — producción: usar `strict` |
| `AVM_FAIL_CLOSED` | `true` = halt on DB failure | Optional |
| `FORENSIC_EXPORT_ALLOW_CALLER_KEYS` | `true` = acepta claves del caller en `/export` | **NUNCA en producción** — solo dev/test (ADR-166 FEA-INV-005) |
| `MIVP_MAS_HALT_THRESHOLD` | MIVP: MAS por debajo del cual se emite HALT de mandato (ADR-194 MIVP-INV-005) | Optional — default: `0.30` · mínimo: `0.05` · debe ser < WARNING threshold |
| `MIVP_MAS_WARNING_THRESHOLD` | MIVP: MAS por debajo del cual se emite WARNING de mandato | Optional — default: `0.65` · debe ser > HALT threshold |

### Flask Dashboard (`omnix_dashboard/app.py`)

| Variable | Descripción |
|---|---|
| `SESSION_SECRET` | Flask session key — **NO es `SECRET_KEY`** |
| `DATABASE_URL` | Compartida con web API |
| `GEMINI_API_KEY` | AI analysis |

### Telegram Bot

| Variable | Descripción |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token — presente en Railway ✓ |
| `TELEGRAM_ADMIN_USER_ID` | Gate para comandos admin — presente en Replit ✓ |

---

## Database Tables (auto-created)

| Tabla | Módulo | ADR |
|---|---|---|
| `decision_receipts` | Governance pipeline | ADR-028 |
| `b2b_clients` | B2B API | ADR-052 |
| `avm_calibration_snapshots` | Adaptive Veto Machine | ADR-074/120 |
| `execution_receipts` | Execution Integrity Layer | ADR-131 |
| `udcl_control_receipts` | Unified Decision Control Layer | ADR-138 |
| `governance_scope_authorizations` | Scope Authorization Record | ADR-147 |
| `atf_delegations` | Agent Trust Fabric | ADR-156 |
| `atf_temporal_records` | Temporal Authority | ADR-157 |
| `atf_domain_bridges` | Cross-Domain Trust | ADR-158 |
| `atf_runtime_continuity` | Runtime Governance Continuity | ADR-159 |
| `atf_continuity_escalations` | RGC escalations | ADR-159 |
| `atf_temporal_semantic_anchors` | DSPP — TSA | ADR-173 |
| `atf_semantic_drift_records` | DSPP — SDR append-only | ADR-173 |
| `atf_retroactive_semantic_assessments` | DSPP — RSA offline | ADR-173 |
| `avm_anticipatory_veto_receipts` | AGVP — PVR proactive veto | ADR-174 |
| `atf_behavioral_anchor_records` | BEV — BAR per-turn behavioral attestation | ADR-181 |
| `atf_constraint_conformance_signals` | BEV — CCS conformance history projection | ADR-182 |
| `atf_coherence_hash_chains` | BEV — CTCHC session integrity proof | ADR-183 |
| `atf_coherence_chain_links` | BEV — CTCHC per-turn hash links | ADR-183 |
| `atf_ogr_sessions` | OGR — Governance Runtime sessions | ADR-184 |
| `book_leads` | CRM / lead capture | — |
| `pogr_certificates` | Proof of Governance Registry | ADR-186/187 |
| `osg_validation_receipts` | Settlement Gate — VR append-only | ADR-188 |
| `atf_mandate_binding_records` | MIVP — MBR per-session | ADR-194 |
| `atf_mandate_alignment_scores` | MIVP — MAS per-turn | ADR-194 |
| `atf_mbr_seals` | MIVP — MBRSeal al cierre de sesión | ADR-194 |
| `atf_counterfactual_forks` | CGE — Counterfactual Fork Record (CFR) | ADR-178 / RFC-ATF-5 |
| `atf_counterfactual_tokens` | CGE — Counterfactual Token per decision path | ADR-178 / RFC-ATF-5 |
| `gugt_universal_invariant_receipts` | GUGT — Universal Invariant Receipt (UIR) | ADR-179 / RFC-ATF-5 |
| `atf_temporal_context_snapshots` | TGB — Temporal Context Snapshot (TCS) | ADR-180 / RFC-ATF-5 |
| `atf_regulatory_alignment_receipts` | TGB — Regulatory Alignment Receipt (RAR) | ADR-180 / RFC-ATF-5 |
| `atf_temporal_migration_records` | TGB — Temporal Migration Record (TMR) | ADR-180 / RFC-ATF-5 |

---

## Gotchas Críticos

- **Variable names matter:** Dashboard usa `SESSION_SECRET` (no `SECRET_KEY`). Webhooks usan `PAYLOAD_ENCRYPTION_KEY`. Nombres incorrectos = fallos silenciosos.
- **React Build:** Siempre hacer `npm run build` en `omnix_web/` y commitear `dist/`. Railway sirve desde ahí. Build usa `React.lazy()` + `Suspense` en todas las rutas (67 páginas) desde Mayo 2026.
- **TESTING=true en producción:** NUNCA. Desactiva alertas AVM, scheduler de snapshots y simuladores.
- **PQC Keys sin Railway:** Sin `OMNIX_SIGNING_SECRET_KEY_B64/PUBLIC`, cada restart genera claves efímeras y todos los receipts previos dejan de ser verificables permanentemente (FMR-001).
- **Anti-replay en Railway:** Configurar `OMNIX_ANTI_REPLAY_MODE=strict`. El default `best_effort` permite replay cross-dyno cuando Redis no está disponible.
- **AVM_AUTO_APPROVE:** Nunca en producción. Deshabilita el AMG approval gate completo.
- **AMG thresholds:** `AVM_MAX_CUMULATIVE_DRIFT_PCT` y `AVM_APPROVAL_THRESHOLD_PCT` nunca por encima de 50% en producción — son parámetros de seguridad, no config operacional.
- **B2B API Keys:** Al provisionar via `provision_b2b_client.py`, copiar la key inmediatamente — solo se muestra una vez.
- **OMNIX-DEMO-DASHBOARD-KEY:** Las páginas de dashboard (Anomaly, Breach, Risk, Execution) envían esta key como identidad read-only. Es intencional. Override con `DASHBOARD_API_KEY` en Railway.
- **crisis-replay page:** UI muestra datos hardcoded (hashes reales, generados por GovernanceReplayEngine en build). El engine es funcional via Python — la UI no lo llama en runtime.
- **AFG_FRAGMENTATION_LIMIT:** Default 0.90. Nunca por encima de 0.95. Valores > 1.0 son rechazados.
- **Gemini Billing:** Requiere activación en Google Cloud Console.

---

## OMNIX Governance Intelligence (OGI) — ADR-193 + ADR-195

**El primer modelo de IA entrenado exclusivamente en un protocolo de gobernanza formal.**
OGI = Llama-3.x fine-tuned sobre 194 ADRs + 6 RFCs + 125 invariantes + 13 categorías de corpus.
Slot en el SAL (ADR-190): **OGI → Groq → Mistral → Gemini → OpenAI → Anthropic**

| Artefacto | Archivo |
|---|---|
| ADR-193 (corpus architecture) | `docs/adr/ADR-193-ogi-fine-tuning-pipeline.md` |
| ADR-195 (Gate C deployment protocol) | `docs/adr/ADR-195-ogi-gate-c-deployment-protocol.md` |
| Product Spec | `docs/products/OGI_SPEC.md` |
| One-Pager ejecutivo | `docs/products/OGI_ONEPAGER.md` |

**Gate B:** ✅ CLEARED (2026-05-26) — 11 findings resueltos  
**Gate C:** ⏳ PENDING — corpus generation → Together.ai fine-tune → 7 evaluation gates → Railway deploy  
**Corpus scripts:** `scripts/fine_tuning/` — `prepare_corpus.py` · `generate_ontology.py` · `eval_suite_generator.py`  
**7 evaluation gates:** factual accuracy ≥ 90% · citation F1 ≥ 0.92 · verdict acc ≥ 85% · HALT recall ≥ 80% · hallucination ≤ 3% · refusal ≥ 95% · MIVP acc ≥ 80%

---

## Proof of Governance Registry (PoGR) — ADR-186

**Primera capa de confianza pública del mundo para gobernanza de decisiones de IA.**  
El "SSL para decisiones de agentes de IA" — verificable offline, firmado PQC, append-only.  
**Product ID:** OMNIX-POGR-2026-001  

| Artefacto | Archivo |
|---|---|
| ADR-186 (spec arquitectónica) | `docs/adr/ADR-186-proof-of-governance-registry.md` |
| Product Spec B2B | `docs/products/POG_REGISTRY_SPEC.md` |
| One-Pager ejecutivo | `docs/products/POG_ONEPAGER.md` |

**Nuevo artifact class:** `PoG Certificate (PoGC)` · ID: `POGC-{HEX16}` · PQC-signed ML-DSA-65  
**6 invariantes:** PoGR-INV-001–006 (append-only · zero-trust verify · TTL explícito · 3-channel trust anchor · issuer-only revocation)  
**DB table:** `pogr_certificates` (auto-created en Railway)  
**Implementación pendiente:** ADR-187 (endpoints `/v1/pogr/*`) · React page `/proof-of-governance`  
**Go-to-market:** primer PoGC emitido antes del 1 julio 2026 — 32 días antes del EU AI Act enforcement

---

## Arquitectura — Principios Inamovibles

- **React SPA = único frontend.** Flask solo sirve APIs y `dist/index.html` para el SPA catch-all.
- **Nunca** `render_template` para páginas que existen en React. Nunca rutas de página en blueprints Flask.
- **Excepción:** `/terminal` y `/classic` son dashboards operacionales internos en Jinja2. No aplica la regla React.
- **PQC-first:** Todos los receipts de gobernanza se firman con Dilithium-3.
- **ATF stack (L1–L4):** Identity (AIR) → Delegation (DR) → Temporal (TAR) → Runtime Continuity (RCR). Cada capa extiende sin reemplazar la anterior.
- **125 invariantes totales:** ATF-INV-001–006 (RFC-ATF-1) + RGC-INV-001–008 (RFC-ATF-2) + GPIL-INV-001–003 + ELR-INV-001–004 + EAP-INV-001–007 + OEP-INV-001–006 + FEA-INV-001–005 + FVP-INV-007 (RFC-ATF-3) + GECR-INV-001–006 + SGIP-INV-001–004 + DSPP-INV-001–007 (ADR-173) + AGV-INV-001–006 (ADR-174) + SSD-INV-001–003 (ADR-175) + FVS-INV-001–003 (ADR-177) + **CGE-INV-001–007** (ADR-178) + **GUGT-INV-001–006** (ADR-179) + **TGB-INV-001–005** (ADR-180) — RFC-ATF-5 Cognitive Governance Layer + **BEV-INV-001–018** (ADR-181/182/183) — RFC-ATF-6 Behavioral Execution Verification Layer + **OGR-INV-001** (ADR-184) — OMNIX Governance Runtime simultaneous-layer invariant + **MIVP-INV-001–009** (ADR-194) — Mandate Integrity Verification Protocol: proxy-optimization detection + tres niveles de certificación de mandato (MANDATE-BOUND · MANDATE-ALIGNED · UNCERTIFIED) + **OGI-INV-001–010** (ADR-193) — OGI Fine-Tuning Pipeline: corpus integrity + model evaluation gates. BEV breakdown: BAR 001–004+015–016 · CCS 005–009+017 · CTCHC 010–014+018 · MIVP 001–009 · OGI 001–010.

---

---

## Pipeline de Patentes — RFC-ATF-1 a RFC-ATF-6

Cada RFC introduce conceptos novedosos patentables. Mantener este registro actualizado para futuras solicitudes de patente.

### RFC-ATF-1 (publicado)
- Monotonic Authority Reduction (MAR) — reducción jerárquica de autoridad con prueba Z3
- Agent Identity Record (AIR) — vinculación inmutable agente-humano con firma PQC
- Offline-verifiable governance receipts (ATF-INV-006)

### RFC-ATF-2 (publicado)
- Runtime Continuity Record (RCR) — continuidad de autoridad en tiempo real con attestation PQC
- Authority Fragmentation Guard (AFG) — prevención de fragmentación de autoridad
- Reauthorization Challenge (RC) — mecanismo de reautorización con HALT propagation

### RFC-ATF-3 (publicado)
- Governance Policy Interoperability Layer (GPIL) — contratos de interoperabilidad cross-dominio
- COLD/WARM/HOT evidence lifecycle classification
- OMNIX Evidence Package (OEP) — formato forense sellado con hash chain

### RFC-ATF-4 (pendiente Zenodo — domingo)
- Anticipatory Governance Veto Receipt (PVR) — primer artefacto de gobernanza proactiva firmado antes de que llegue la solicitud
- Component Rank Stability Index (CRSI) — métrica continua de estabilidad topológica de señales
- DSPP Retroactive Semantic Assessment (RSA) — portabilidad semántica O(1) sin negociación bilateral
- Dual-methodology formal verification (Z3 + TLA+) sobre el mismo stack de protocolo

### RFC-ATF-5 (pendiente Zenodo — jueves)
- Counterfactual Governance Engine (CGE) — documentación del espacio de decisión con alternativas contrafactuales firmadas
- Grand Unified Governance Theory (GUGT) — certificación multi-jurisdicción universal
- Temporal Governance Bridge (TGB) — interpretabilidad longitudinal de evidencia

### RFC-ATF-6 — Behavioral Execution Verification Protocol (a diseñar)
Conceptos nuevos identificados en sesión 23 mayo 2026 — ninguno existe como estándar publicado:
- **Behavioral Anchor Record (BAR):** registro firmado PQC de los outputs reales del modelo durante ejecución, vinculado criptográficamente al receipt de gobernanza que autorizó la acción. Los ingredientes (ML monitoring, output logging) existen; la combinación con firma PQC + receipt linkage es nueva.
- **Constraint Conformance Signal (CCS):** señal continua que mide si los outputs del modelo se mantienen dentro de los límites definidos en el receipt de gobernanza, diseñada para alimentar el AGVP watchdog y permitir emisión de PVRs conductuales anticipatorios. El concepto de señal de drift existe; la integración arquitectónica con AGVP es nueva.
- **Cross-Turn Coherence Hash Chain:** cadena de hashes turno a turno de los outputs del modelo en interacciones multi-turno, vinculada al receipt de gobernanza de la sesión para verificación forense post-hoc. Los audit log hash chains existen; el vínculo con governance receipts para verificación forense de comportamiento es nuevo.
- Fundamento existente en OMNIX: ADR-131 (Execution Integrity Layer) + ADR-155 (Chain Completeness Score) son la base sobre la que construiría RFC-ATF-6.

---

## User Preferences

- Siempre responder a Harold en español.
- **DOI verification rule:** Antes de incluir cualquier link DOI (Zenodo, Figshare) en un comentario de LinkedIn u otro canal público, recordar a Harold que verifique que el link resuelve y el registro está en estado Published (no Draft). Si no está verificado, omitir el link del mensaje hasta confirmarlo.
- **Regla absoluta — no asumir datos:** NUNCA escribir en ningún documento, archivo, PDF, metadata o cualquier artefacto información que Harold no haya dicho explícitamente (localización, sede operativa, país, ciudad, dirección adicional, afiliaciones, etc.). Ante cualquier duda, preguntar antes de escribir. Prohibido inventar o asumir.
- **Regla de traducción:** Todo contenido redactado en inglés (comentarios LinkedIn, mensajes WhatsApp, respuestas, etc.) debe ir acompañado inmediatamente de su traducción al español para revisión de Harold antes de publicar.
- **Regla de botón de copiar:** Todo texto listo para publicar (posts LinkedIn, comentarios, mensajes, respuestas) debe presentarse dentro de un bloque de código para que tenga botón de copiar.
