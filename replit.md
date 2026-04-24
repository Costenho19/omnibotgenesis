# OMNIX QUANTUM — Decision Governance Infrastructure

**Harold Nunes · Founder & CEO · OMNIX QUANTUM LTD (UK)**
**Producción:** `omnixquantum.net` · **Repositorio:** `Costenho19/omnibotgenesis`
**Raising:** $500K pre-seed · $3M pre-money valuation

---

## ÍNDICE

1. [Estado Actual del Sistema](#1-estado-actual-del-sistema)
2. [Arquitectura Completa](#2-arquitectura-completa)
3. [Servicios y Módulos](#3-servicios-y-módulos)
4. [Base de Datos (44+ tablas)](#4-base-de-datos-44-tablas)
5. [APIs Usadas — Gratis vs Pagado](#5-apis-usadas--gratis-vs-pagado)
6. [Onboarding B2B — Cómo dar acceso a un cliente](#6-onboarding-b2b--cómo-dar-acceso-a-un-cliente)
7. [Despliegue Railway](#7-despliegue-railway)
8. [Verticales de Gobernanza (9 activos)](#8-verticales-de-gobernanza-9-activos)
9. [Seguridad Enterprise](#9-seguridad-enterprise)
10. [ADRs — Architecture Decision Records](#10-adrs--architecture-decision-records)
11. [Roadmap](#11-roadmap)

---

## 1. ESTADO ACTUAL DEL SISTEMA

### Semáforo — Producción (omnixquantum.net)

| Componente | Estado | Detalle |
|---|---|---|
| **Bot Telegram** `@omnixglobal2025_bot` | 🟢 OPERATIVO | Indestructible: pool×16, retry×4, error handler global |
| **Web Landing** `/` | 🟢 OPERATIVO | CommercialLanding con video demo, form de contacto, métricas live |
| **Governance Sandbox** `/try` | 🟢 OPERATIVO | 11 checkpoints, W3C VC, recibo PQC, email capture |
| **Investor Command Center** `/investor` | 🟢 OPERATIVO | Métricas en tiempo real desde PostgreSQL |
| **Audit Dashboard** `/audit` | 🟢 OPERATIVO | 327K+ decisiones, filtros por dominio |
| **Client Portal** `/client` | 🟢 OPERATIVO | Autenticación por API key, reportes de uso |
| **Verify Receipts** `/verify` | 🟢 OPERATIVO | Verificación pública de recibos PQC Dilithium-3 |
| **Flask Dashboard** `:5000` | 🟢 OPERATIVO | Panel AVM, governance, trade history |
| **B2B API** `/api/governance/evaluate` | 🟢 OPERATIVO | Auth, quotas, RBAC, webhooks, SDK Python/JS |
| **PostgreSQL** | 🟢 OPERATIVO | 44+ tablas, 327K+ decision_receipts, 0 NULLs |
| **Redis** | 🟢 OPERATIVO | Anti-replay (best_effort mode) |

### Métricas Clave (18 Abr 2026)

| Métrica | Valor |
|---|---|
| Decisiones gobernadas | 327,000+ |
| Verticales activos | **9** (Trading, Credit, Insurance, Robotics, Medical AI, Energy, Real Estate, Agents, **Stablecoin Reserve**) |
| Dominios públicos anunciados | 9 |
| ADRs publicados | 30 formalizados (incl. ADR-116 Fail-Closed Enforcement Policy, ADR-096 Expanded Canonical Receipt, ADR-SRG-001 Stablecoin Reserve Governance) |
| TAM total cubierto | $212B+ |
| Tests pasando | 93 pasando (post-audit fix 24 Abr) |
| Cobertura PQC | Dilithium-3 (CRYSTALS) + Kyber-768 |
| AVM snapshots activos | 9 (1 por dominio) |

### Cambios Críticos Recientes

| Fecha | Fix | Commit |
|---|---|---|
| 24 Abr 2026 | **AUDIT CRÍTICA — 8 bugs corregidos**: SAE ON por defecto, CAG ON por defecto, SAE error→fail-closed, FORCE_OFF eliminado (Zero-Bypass garantizado), PQC fail→raise, AML error→fail-closed, Fraud error→fail-closed, Dashboard metrics→503 real (sin números inventados) | pendiente push |
| 18 Abr 2026 | **AUDIT PROFUNDA**: 8→9 dominios en todos los archivos (AI prompts×15, React pages×12). Sección "Coste de no tener OMNIX" en CommercialLanding. SQL/secrets audit: sin vulnerabilidades críticas. Build React: 0 errores. | pendiente push |
| 18 Abr 2026 | Fix idioma bot: detector pt→es en msgs cortos, política idioma correcta | `26c1b959` |
| 17 Abr 2026 | Bot indestructible: pool×16, retry×4, error handler global sin re-raise | `fa8332ba` |
| 17 Abr 2026 | Video demo en CommercialLanding (`/public/omnix-demo.mp4`, 12MB) | `475cef96` |
| 17 Abr 2026 | Proxy `/api/public/*` en Flask Dashboard → puerto 8080 | — |
| 15 Abr 2026 | ADR-115: Engine Unification — 8 verticales enrutan por GovernanceEvaluationEngine | — |
| 13 Abr 2026 | ADR-081: Per-Client B2B Quota Enforcement (5K/día, 50K/mes) | — |
| 13 Abr 2026 | ADR-080: Strict Input Schema Validation en todos los endpoints | — |
| 11 Abr 2026 | 23 errores encontrados y corregidos en auditoría profunda | — |

---

## 2. ARQUITECTURA COMPLETA

### Infraestructura Railway (Producción)

```
omnixquantum.net
       │
       ├── stellar-hope (Railway Service 1)
       │     ├── React + Vite frontend (dist/ pre-compilado)
       │     ├── Python API server (omnix_web/api/server.py : 8080)
       │     └── Rutas: /, /try, /verify, /client, /investor, /audit,
       │                /governance-demo-*, /medical, /energy, /agents, /real-estate
       │
       └── omnibotgenesis (Railway Service 2)
             ├── Enterprise Telegram Bot (enterprise_bot.py : 8822 líneas)
             ├── Flask Dashboard (omnix_dashboard/app.py : 5000)
             └── 8 simuladores 24/7 (trading, credit, insurance, robotics,
                                     medical, agents, real_estate, energy)
```

### Arquitectura de Gobernanza — 4 Capas de Defensa

```
INPUT SIGNAL
     │
     ▼
[CAPA 1] Signal Intelligence
  ├── 10 estrategias core: Quantum Momentum, HMM Regime, Kalman Filter,
  │   Multi-fractal Vol, Cross-asset Coherence, Quantum Entropy,
  │   LSTM Temporal, Bayesian Regime, Adaptive Kelly, Adversarial Detection
  └── Output: 6 señales normalizadas (0-100 c/u)
     │
     ▼
[CAPA 2] Risk & Coherence Engine
  ├── 6-Tier Coherence Engine (coherence_engine.py)
  ├── Fail-Closed: cualquier error → BLOCK (no pass-through)
  └── Hard Blocks por vertical (AML, Sharia, RERA, Ethics, Safety...)
     │
     ▼
[CAPA 3] 11-Checkpoint Governance Pipeline (CP-1 a CP-11)
  ├── CP-1: Signal Quality Gate
  ├── CP-2: Risk Exposure Assessment
  ├── CP-3: Coherence Validation
  ├── CP-4: Trend Persistence Check
  ├── CP-5: Stress Resilience Test
  ├── CP-6: Sharia Compliance Gate
  ├── CP-7: Ethics & Domain Gate
  ├── CP-8: Threshold & Context Validator
  ├── CP-9: AVM Baseline Comparison
  ├── CP-10: Final Risk Adjudication
  └── CP-11: Jurisdiction Compliance Gate (13 jurisdicciones)
     │
     ▼
[CAPA 4] Audit & Cryptographic Receipt
  ├── Post-Quantum Signature (Dilithium-3 / CRYSTALS)
  ├── W3C Verifiable Credential (GovernanceDecisionCredential)
  ├── Receipt almacenado en PostgreSQL (decision_receipts)
  └── Verificable públicamente en /verify
```

### Flujo Completo de una Decisión B2B

```
Cliente → POST /api/governance/evaluate + X-API-Key
  ↓ Auth (SHA-256 hash lookup en b2b_clients)
  ↓ Rate limit (1000 req/min por IP)
  ↓ Schema validation (ADR-080)
  ↓ Quota check (5K/día, 50K/mes — ADR-081)
  ↓ GovernanceEvaluationEngine (11 checkpoints)
  ↓ PQC Receipt generated (Dilithium-3)
  ↓ Receipt stored in PostgreSQL
  ↓ Webhook push (si cliente tiene webhook registrado — ADR-053)
  → Response: {decision, receipt_id, checkpoints, w3c_vc}
```

---

## 3. SERVICIOS Y MÓDULOS

### omnix_services/ (24+ paquetes)

| Servicio | Archivo Principal | Función |
|---|---|---|
| `ai_service` | `ai_service.py`, `ai_models.py` | Orquestador SOLID: Gemini (primario), OpenAI, Anthropic. Honesty Guard |
| `coherence_service` | `coherence_engine.py` | 6-Tier veto logic, fail-closed, thresholds adaptativos |
| `trading_service` | `auto_trading_bot.py` | Estrategias trading, Kraken/Alpaca, Kelly sizing |
| `governance_service` | `governance_commands.py` | Gates: Sharia, AML, Fraud, Jurisdiction |
| `adaptive_engine` | — | Auto-calibración AVM basada en rendimiento histórico |
| `security` | `bot_security.py` | BotSecurityMiddleware: anti-injection, rate limit, length limit |
| `telegram_service` | `enterprise_bot.py` | Bot Enterprise: 8822 líneas, 85+ comandos, multi-user |

### omnix_core/ (núcleo de gobernanza)

| Módulo | Función |
|---|---|
| `governance/governance_engine.py` | GovernanceEvaluationEngine: motor de 11 checkpoints |
| `governance/jurisdiction_gate.py` | CP-11: 13 jurisdicciones (UAE, EU, US, UK, SG, JP, AU, CA, BR, KR, CH, GCC, GLOBAL) |
| `governance/avm_engine.py` | Adaptive Veto Machine: calibración dinámica de thresholds |
| `security/pqc_security.py` | Kyber-768 (encapsulación) + Dilithium-3 (firma) |
| `decision_receipt.py` | DecisionReceiptEngine: genera, firma y almacena recibos |
| `anti_replay.py` | Redis anti-replay (NX PX atómico, fallback in-memory) |

### omnix_web/api/ (API Railway — puerto 8080)

| Endpoint | Archivo | Función |
|---|---|---|
| `POST /api/governance/evaluate` | `gov_blueprint.py` | Motor B2B: auth, quota, 11 checkpoints, webhook |
| `POST /api/sandbox/evaluate` | `sandbox.py` | Sandbox público: sin auth, W3C VC, email capture |
| `GET /api/metrics/live` | `server.py` | Métricas en tiempo real para InvestorCommandCenter |
| `GET /api/governance/receipts/<id>` | `gov_blueprint.py` | Receipt por ID (tenant-isolated) |
| `GET /api/receipts/public-key` | `receipt_verification.py` | Clave pública Dilithium-3 |
| `POST /api/receipts/verify` | `receipt_verification.py` | Verificación de firma |
| `PUT /api/governance/admin/clients/<id>/webhook` | `gov_blueprint.py` | Registro webhook por cliente |
| `GET /api/governance/admin/usage` | `gov_blueprint.py` | Uso por cliente (admin only) |
| `GET /api/governance/quickstart` | `gov_blueprint.py` | Guía de integración 5 pasos |
| `POST /api/contact` | `server.py` | Lead capture → PostgreSQL `contact_leads` |

### omnix_dashboard/ (Flask — puerto 5000)

| Blueprint | Prefijo API | Función |
|---|---|---|
| `governance.py` | `/api/governance/*` | KPIs, AVM status, audit trail |
| `trading.py` | `/api/trading/*` | Historial trades, P&L |
| `real_estate_governance.py` | `/api/real-estate/*` | Vertical Real Estate |
| `energy_governance.py` | `/api/energy/*` | Vertical Energy (SCADA) |
| `medical_governance.py` | `/api/medical/*` | Vertical Medical AI |
| `agents_governance.py` | `/api/agents/*` | Vertical Autonomous Agents |
| `receipt_verification.py` | `/api/receipts/*` | PKI verification |

---

## 4. BASE DE DATOS (44+ tablas)

### Tablas Principales

| Tabla | Función | Rows (aprox) |
|---|---|---|
| `decision_receipts` | Todos los recibos PQC firmados (FUENTE DE VERDAD) | 327,000+ |
| `b2b_clients` | Clientes B2B: ID, API key hash, rol, expiry, webhook | n/a |
| `client_thresholds` | Thresholds personalizados por cliente (ADR-037) | n/a |
| `avm_calibration_snapshots` | AVM baselines + SHA-256 integrity per domain | 8 |
| `avm_baseline_change_log` | Audit trail de cambios AVM | n/a |
| `webhook_delivery_log` | Log de entregas webhook por cliente | n/a |
| `contact_leads` | Leads del formulario de contacto web | activo |
| `shadow_portfolio` | Trades vetados (análisis contrafactual) | activo |

### Tablas por Vertical

| Vertical | Tablas |
|---|---|
| Trading | `shadow_trade_events`, `trade_history`, `signal_snapshots` |
| Credit | `credit_applications`, `credit_cycle_metrics` |
| Insurance | `insurance_decisions`, `insurance_cycle_metrics` |
| Robotics | `robotics_decisions`, `robotics_cycle_metrics` |
| Medical AI | `medical_decisions`, `medical_cycle_metrics` |
| Autonomous Agents | `agent_decisions`, `agent_cycle_metrics` |
| Real Estate | `property_decisions`, `property_cycle_metrics` |
| Energy | `energy_decisions`, `energy_cycle_metrics` |

### Índices Clave

```sql
CREATE INDEX idx_decision_receipts_domain ON decision_receipts(domain);
CREATE INDEX idx_decision_receipts_created ON decision_receipts(created_at);
```

### Conexión

- **Dev (Replit):** `OMNIX_DB_URL` secret → Railway PostgreSQL
- **Prod (Railway):** `DATABASE_URL` env var inyectado automáticamente

---

## 5. APIs USADAS — Gratis vs Pagado

### Estado Actual y Coste para 5 Clientes

| API | Uso | Tier Actual | Límite Gratis | Coste Recomendado | Acción |
|---|---|---|---|---|---|
| **Google Gemini 2.5 Flash** | Respuestas del bot (principal) | **Free** | ~1,500 req/día, 15 req/min | Pay-as-you-go: ~$0.075/1M tokens input | **⚠️ ACTIVAR BILLING** |
| **OpenAI GPT-4o mini** | Fallback IA | Configurado | Requiere key | ~$0.15/1M tokens input | Backup útil |
| **Anthropic Claude** | Fallback IA | Configurado | Requiere key | — | Backup |
| **Finnhub** | Noticias de mercado | Free | 60 req/min | Starter: gratis | OK por ahora |
| **CoinGecko** | Precios crypto | Free | 30 req/min | Analyst: $129/mes | Escalar si hay cliente crypto |
| **Kraken API** | Trading live | Depende credenciales | — | Variable | Ya integrado |
| **Alpaca API** | Trading US equities | Depende credenciales | — | Variable | Ya integrado |

### Estimación de Coste Gemini con 5 Clientes

Asumiendo 5 clientes moderadamente activos (bot + evaluaciones):

| Escenario | Req/día | Coste/mes estimado |
|---|---|---|
| Solo demo / reuniones | ~100 req/día | < $1/mes |
| 5 clientes usando el bot | ~500 req/día | ~$3-5/mes |
| 5 clientes + API evaluate | ~2,000 req/día | ~$15-25/mes |

**Gemini 2.5 Flash** es el modelo más eficiente (velocidad + coste). Ya está configurado en `ai_models.py`.

### Cómo Activar Gemini Billing (Harold lo hace en 5 minutos)

1. Ir a [console.cloud.google.com](https://console.cloud.google.com)
2. Seleccionar el proyecto donde está la API key de Gemini
3. Ir a **Billing** → **Link a billing account**
4. Añadir tarjeta de crédito (Google cobra al uso, no hay mínimo)
5. Ir a **APIs & Services** → confirmar que **Generative Language API** está habilitada
6. Listo — la misma API key funciona, sin límite de 1,500/día

> El bot ya usa `gemini-2.5-flash` (el modelo más nuevo y eficiente). No hay que cambiar código.

---

## 6. ONBOARDING B2B — Cómo dar acceso a un cliente

### Lo que OMNIX ya tiene construido para B2B

- ✅ Autenticación por API key (`X-API-Key` header)
- ✅ RBAC: roles `standard` y `admin`
- ✅ Quotas per-client: 5,000 eval/día, 50,000 eval/mes
- ✅ Brute force lockout: 5 intentos → bloqueo 15 min
- ✅ API key expiry: 90 días (rotación automática)
- ✅ Webhooks por cliente (firma HMAC-SHA256)
- ✅ Receipt by ID con aislamiento de tenant
- ✅ Usage reporting: `GET /api/governance/admin/usage`
- ✅ SDK Python y JavaScript
- ✅ Portal `/client` con API key input, reportes de uso, ejemplos de código

### Pasos para Añadir un Nuevo Cliente (5 minutos)

**Paso 1 — Provisionar en Railway:**
```bash
railway run python scripts/provision_b2b_client.py \
  --client-id  "nombre-empresa-01" \
  --name       "Nombre Empresa" \
  --email      "cto@empresa.com" \
  --role       standard
```

> El script imprime la API key **UNA SOLA VEZ**. Copiarla inmediatamente.
> OMNIX solo guarda el hash SHA-256, nunca la clave en texto plano.

**Paso 2 — Entregar al cliente:**
```
Tu API key de OMNIX: OMNIX-xxxxxxxxxxxx

Endpoint: https://omnixquantum.net/api/governance/evaluate
Documentación: https://omnixquantum.net/api/governance/quickstart

Ejemplo rápido:
curl -X POST https://omnixquantum.net/api/governance/evaluate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: OMNIX-xxxxxxxxxxxx" \
  -d '{"signals": {"probability_score": 72, "risk_exposure": 38, ...}}'
```

**Paso 3 — Verificar acceso:**
```bash
railway run python scripts/provision_b2b_client.py --list
```

**Paso 4 (opcional) — Configurar webhook:**
```bash
curl -X PUT https://omnixquantum.net/api/governance/admin/clients/nombre-empresa-01/webhook \
  -H "X-API-Key: OMNIX-ADMIN-KEY" \
  -d '{"url": "https://cliente.com/webhook/omnix", "secret": "secreto-hmac"}'
```

### Gestión de Clientes desde el Bot (comandos admin)

Harold puede gestionar clientes directamente desde Telegram:

```
/clientes           — Ver todos los clientes activos con su uso
/nuevo_cliente      — Provisionar un nuevo cliente (guiado)
```

### Portal del Cliente

Los clientes acceden a `omnixquantum.net/client` e introducen su API key.
Ven: evaluaciones usadas hoy/mes, últimas decisiones, ejemplos de integración SDK.

### Thresholds Personalizados por Cliente

Si un cliente necesita thresholds distintos (ej. más permisivo en CP-1):
```sql
INSERT INTO client_thresholds (client_id, checkpoint, threshold_value)
VALUES ('nombre-empresa-01', 'CP-1', 60.0);
```

---

## 7. DESPLIEGUE RAILWAY

### Servicios Railway

| Servicio | Nombre | Comando | Puerto |
|---|---|---|---|
| React + Python API | `stellar-hope` | `nixpacks.toml` → `python api/server.py` | 8080 |
| Bot + Flask | `omnibotgenesis` | `railway.toml` → `python run_services.py` | 5000 |
| PostgreSQL | `omnix-db` | Managed | 5432 |
| Redis | `omnix-redis` | Managed | 6379 |

### Variables de Entorno Críticas (Railway)

| Variable | Servicio | Descripción |
|---|---|---|
| `DATABASE_URL` | Ambos | PostgreSQL connection string (auto-inject) |
| `REDIS_URL` | omnibotgenesis | Redis connection (anti-replay) |
| `TELEGRAM_BOT_TOKEN` | omnibotgenesis | Token del bot |
| `TELEGRAM_ADMIN_USER_ID` | omnibotgenesis | ID de Harold (admin) |
| `GEMINI_API_KEY` | Ambos | Clave Gemini (activar billing) |
| `OMNIX_WEB_URL` | omnibotgenesis | URL del API (https://omnixquantum.net) |
| `B2B_API_KEY` | stellar-hope | Fallback dev key (cuando b2b_clients está vacío) |
| `ADMIN_ALLOWED_IPS` | stellar-hope | IPs permitidas para `/api/governance/admin/*` |
| `WEBHOOK_ENCRYPTION_KEY` | stellar-hope | Fernet key para cifrar secrets de webhooks |
| `VELOS_GATEWAY_TOKEN` | stellar-hope | Token para partner Velos |
| `OMNIX_ANTI_REPLAY_MODE` | stellar-hope | `strict` o `best_effort` (default) |
| `AVM_FAIL_CLOSED` | Ambos | `true` → halt si DB falla o snapshot tampered |

### CI/CD

- Push a `main` → Railway auto-deploy
- `dist/` NO está en `.gitignore` → hay que compilar React y commitear antes del push
- Build React: `cd omnix_web && npm run build && cd .. && git add omnix_web/dist && git commit -m "build: dist" && git push`

### Monitoreo de Producción

```bash
# Logs en tiempo real
railway logs --service stellar-hope
railway logs --service omnibotgenesis

# Health check
curl https://omnixquantum.net/api/health
curl https://omnixquantum.net/api/governance/evaluate/health
```

---

## 8. VERTICALES DE GOBERNANZA (8 activos)

### Verticales Públicos Anunciados (7)

| Vertical | Dominio DB | Prefix Receipt | Ruta Demo | Dashboard |
|---|---|---|---|---|
| Trading | `trading` | `OMNIX-TRD` | `/governance-demo` | `/investor` |
| Islamic Credit | `credit` | `OMNIX-CRD` | `/governance-demo-credit` | `/credit` |
| Insurance Claims | `insurance` | `OMNIX-INS` | `/governance-demo-insurance` | `/insurance` |
| Robotics Safety | `robotics` | `OMNIX-RBT` | `/governance-demo-robotics` | `/robotics` |
| Medical AI | `medical_ai` | `OMNIX-MED` | `/governance-demo-medical` | `/medical` |
| Autonomous Agents | `autonomous_agent` | `OMNIX-AGT` | `/governance-demo-agents` | `/agents` |
| Energy Governance | `energy_governance` | `OMNIX-EGV` | `/governance-demo-energy` | `/energy` |

### Verticales Internos (no anunciados)

| Vertical | Dominio DB | Prefix Receipt | Ruta Demo | Notas |
|---|---|---|---|---|
| Real Estate | `real_estate` | `OMNIX-REP` | `/governance-demo-real-estate` | Activo, modo prueba interna |

### Motor Unificado (ADR-115)

Todos los verticales enrutan por `GovernanceEvaluationEngine` desde el 15 Abr 2026.
Cada vertical tiene su `SignalAdapter` que mapea parámetros propios a las 6 señales OMNIX estándar.
Hard blocks pre-engine: no pueden ser overrideados por thresholds.

### AVM (Adaptive Veto Machine) — ADR-074

Cada vertical tiene su propio snapshot de calibración:
- SHA-256 integrity hash → snapshot tampered → rechazado
- 8 snapshots activos (uno por vertical)
- Versioning + fail-closed configurable
- `AVM_FAIL_CLOSED=true` → halt en DB failure o tampered snapshot

---

## 9. SEGURIDAD ENTERPRISE

### Capas de Seguridad

| Capa | Mecanismo | ADR |
|---|---|---|
| **Criptografía PQC** | Dilithium-3 (firma) + Kyber-768 (encapsulación) | ADR-074 |
| **Anti-replay** | Redis NX PX atómico, fallback in-memory | ADR-077 |
| **Key persistence** | Env vars `OMNIX_SIGNING_SECRET_KEY_B64`, ephemeral_dev fallback | ADR-078 |
| **PKI verification** | `GET /api/receipts/public-key`, `POST /api/receipts/verify` | ADR-079 |
| **Input validation** | Schema validation en todos los endpoints antes de lógica | ADR-080 |
| **Per-client quotas** | 5K/día, 50K/mes, circuit breaker DB | ADR-081 |
| **W3C Verifiable Credentials** | Interop con EUDI wallets, DID resolvers | ADR-082 |
| **Bot security middleware** | Anti-injection, rate limit, length limit, memory cap | ADR-083 |
| **Brute force lockout** | 5 intentos → 15 min lockout por IP | ADR-052 |
| **API key expiry** | 90 días, rotación vía `--rotate` flag | ADR-052 |
| **Security headers** | HSTS, XSS, X-Frame-Options, Referrer-Policy | ADR-052 |
| **Admin IP allowlist** | `ADMIN_ALLOWED_IPS` env var | ADR-052 |
| **SSRF guard** | Webhook URLs: rechaza IPs privadas/loopback | ADR-053 |
| **IDOR protection** | Receipt by ID con tenant isolation estricto | ADR-053 |
| **AVM integrity** | SHA-256 baseline hash por snapshot | ADR-074 |

### Bot Security (BotSecurityMiddleware)

8 vulnerabilidades enterprise corregidas (ADR-083):
- C1 (CRÍTICO): Prompt injection vía user_message → bloqueado
- C2 (CRÍTICO): Rate limit por usuario — riesgo AI cost + DoS
- C3 (ALTO): Límite de longitud de mensaje
- C4 (ALTO): Memory leak en `_message_buffers` — límite implementado
- C5-C8: Sanitización, logging, validación adicional

### Resiliencia del Bot (Fix 17 Abr 2026)

- `connection_pool_size`: 1 → **16** (elimina PoolTimeout)
- `send_message_with_retry`: retry×4, **never re-raises** (silent fail)
- `error_handler`: captura TimedOut / NetworkError / RetryAfter / Forbidden / BadRequest / PoolTimeout
- **Resultado**: bot indestructible, nunca crashea por errores de red Telegram

---

## 10. ADRs — Architecture Decision Records

### Índice Rápido (79+ ADRs)

| ADR | Título | Estado |
|---|---|---|
| ADR-007 | Adaptive Thresholds por Market Regime | ✅ |
| ADR-015 | Rate Limiting por IP | ✅ |
| ADR-028 | External Signal Evaluation API (B2B) | ✅ |
| ADR-037 | Per-Client Custom Thresholds | ✅ |
| ADR-051 | B2B Client Usage Reporting & Billing | ✅ |
| ADR-052 | Security Hardening (4 medidas) | ✅ |
| ADR-053 | Generic Webhook System + Receipt-by-ID | ✅ |
| ADR-057 | Critical Override Hybrid Expansion | ✅ |
| ADR-058 | Bot Governance Integration | ✅ |
| ADR-059 | Executive Audit Dashboard | ✅ |
| ADR-060 | Guided Investor Demo | ✅ |
| ADR-074 | Enterprise Governance Baseline (AVM) | ✅ |
| ADR-077 | Redis Anti-Replay Phase 2 | ✅ |
| ADR-078 | Signing Key Persistence | ✅ |
| ADR-079 | PKI Verification Endpoint | ✅ |
| ADR-080 | Strict Input Schema Validation | ✅ |
| ADR-081 | Per-Client B2B Quota Enforcement | ✅ |
| ADR-082 | W3C Verifiable Credentials (Sandbox) | ✅ |
| ADR-083 | Enterprise Bot Security Middleware | ✅ |
| ADR-091 | Autonomous Agent Governance Vertical | ✅ |
| ADR-112 | Energy Governance Vertical | ✅ |
| ADR-113 | Medical AI Governance Vertical | ✅ |
| ADR-114 | Real Estate Property Governance | ✅ |
| ADR-115 | Engine Unification (8 verticales) | ✅ |
| ADR-116 | Fail-Closed Enforcement Policy (SAE ON por defecto, FORCE_OFF removido, AML/Fraud/PQC fail-closed) | ✅ |
| AGL-MED-001 | Medical AI Governance Full Stack | ✅ |
| AGL-AGT-001 | Autonomous Agent Governance Full Stack | ✅ |
| ADR-RES-001 | Real Estate Property Governance Internal | ✅ |
| ADR-ENG-001 | Energy Governance Internal | ✅ |
| ADR-SRG-001 | Stablecoin Reserve Governance Internal | ✅ |

### Detalles ADR por Sección

---

## ADR-RES-001 — Real Estate Property Governance Vertical (INTERNAL — 11-Apr-2026)

### Estrategia
Vertical construido internamente para testing y validación. **No anunciado públicamente.** Se libera cuando llegue el cliente correcto.

### Config
- `domain: real_estate` · `code: REP` · `receipt_prefix: OMNIX-REP` · `color: #38bdf8` · `icon: 🏢`
- Rutas internas: `/real-estate` (dashboard live) · `/governance-demo-real-estate` (demo 11 checkpoints)
- **NO** añadido a `live_metrics.py` (no va en el Investor Command Center público)

### Backend
- `omnix_core/real_estate/real_estate_signal_adapter.py` — 6 señales:
  - AVM confidence → probability_score · transaction risk → risk_exposure · data alignment → signal_coherence
  - market trajectory → trend_persistence · stress resilience → stress_resilience · regulatory compliance → logic_consistency
  - Hard blocks: AML flag | RERA non-compliant | Sharia parameter screening failed | LTV > límite según modo (90% Conv / 85% Murabaha+Ijarah / 80% Musharaka)
- `omnix_core/real_estate/real_estate_simulator.py` — 24/7 simulator: 300s cycles, 3-8 decisiones/ciclo
  - Tipos: property_valuation · mortgage_approval · tenant_screening · AML_property · rental_yield
  - Tipos propiedad: Residential, Commercial, Industrial, Mixed_Use, Land
  - Jurisdicciones: UAE, UK, GCC, EU, International · Modos financiamiento: Conventional, Murabaha, Ijarah, Musharaka
  - Tablas: `property_decisions` + `property_cycle_metrics`
- `omnix_dashboard/blueprints/real_estate_governance.py` — Flask API /api/real-estate/*:
  - /metrics · /decisions · /by-type · /by-jurisdiction · /by-property-type · /timeline · /live-feed · /evaluate · /health

### Frontend (interno)
- `RealEstateDashboard.tsx` — 8 KPIs, signal health strip, breakdown por tipo/jurisdicción/propiedad, live feed
- `RealEstateGovernanceDemo.tsx` — selectores interactivos, sliders (AVM/LTV/AML/trend/liquidity), hard block toggles (AML/RERA/Sharia/UBO), pipeline 11 checkpoints animado, receipt PQC

---

## ADR-ENG-001 / ADR-112 — Energy Governance Vertical (INTERNAL — 11-Apr-2026)

### Config
- `domain: energy_governance` · `code: EGV` · `receipt_prefix: OMNIX-EGV` · `color: #00B4D8` (electric blue) · `icon: ⚡` · `badge: ADR-112`
- Rutas internas: `/energy` (dashboard live SCADA) · `/governance-demo-energy` (demo existente, público)

### Backend
- `omnix_core/energy/energy_signal_adapter.py` — 6 señales mapeadas a LMP forecast, MW concentration, spread convergence, load accuracy, renewable buffer, regulatory compliance
- `omnix_core/energy/energy_simulator.py` — 24/7 simulator: 180s cycles, 4-10 decisiones/ciclo
  - Tipos: dispatch_order(35%), curtailment_order(20%), ppa_contract(15%), capacity_trade(15%), carbon_credit(10%), balancing_action(5%)
  - Regiones: PJM, UK, EU_ENTSO_E, ERCOT, GCC, AEMO
  - Hard blocks: freq_deviation > 0.5Hz | capacity_margin < 5% | counterparty_default | carbon_cap_breach
- Flask API `/api/energy/*`: metrics, decisions, by-type, by-source, by-region, timeline, live-feed, evaluate, health

---

## AUDITORÍA PROFUNDA — Correcciones 11-Apr-2026 (23 errores encontrados y corregidos)

| # | Categoría | Error | Corrección | Prioridad |
|---|-----------|-------|------------|-----------|
| 1 | PITCH | PitchDeck "Live · 4 Domains" | → "Live · 7 Domains" | P1 |
| 2-5 | PITCH | Stats, tarjetas, traction desactualizados (4→7 dominios, 57→79 ADRs) | Actualizados | P1 |
| 6-9 | LANDING | CommercialLanding: referencias a 4 dominios, navbar incompleta | → 7 dominios, Medical + Agents añadidos | P1 |
| 10-12 | INVESTOR | InvestorCommandCenter fallbacks: `verticals_live: 4`, `adr_count: 57` | → 7, 79 | P1 |
| 13-16 | BACKEND P0 | `live_metrics.py`: ADR_COUNT, docstring, VERTICALS_META, IMPACT_PHRASES desactualizados | → 7 verticales, 79 ADRs | P0 |
| 17-18 | BACKEND P0 | `core.py` evaluation_cycles: solo contaba trading (~825K) | → suma todos los verticales (~1.01M) | P0 |
| 19-20 | DB P0 | 138,400 filas `decision_receipts.domain = NULL` | Backfill + índice creado | P0 |
| 21-23 | CORE P0 | `_DOMAIN_CODES` sin medical/agents, simuladores sin campo `domain` | Añadidos MED + AGT | P0 |

### Segunda Auditoría (6 errores adicionales)

| # | Categoría | Fix |
|---|---|---|
| 24-26 | CORE P0 | `generate_receipt` + `auto_trading_bot.py` sin `domain` en receipt dict → NULL en DB |
| 27-28 | FRONTEND P1 | ClientDashboard + AuditDashboard: solo 4 dominios (sin medical_ai, autonomous_agent) |
| 29-30 | PITCH + API | Market slide, TAM actualizado: $137B+ → $212B+, "7 live domains" |
| 31 | SECURITY | `public_verify.py` regex rechazaba formato `OMNIX-TRD-{hex}` → regex actualizado |
| 32 | DB P0 | 30 receipts adicionales con domain=NULL → backfill final |

---

## ADR-074 — Enterprise Governance Baseline (COMPLETED)
- **AVM PostgreSQL persistence**: `avm_calibration_snapshots` + `avm_baseline_change_log` tables
- **SHA-256 hash integrity**: `baseline_hash` stored per snapshot; verified on every load; TAMPERED → snapshot rejected
- **Baseline versioning**: `version INT` + `is_active BOOLEAN`; RECALIBRATE increments version
- **Fail-closed configurable**: `AVM_FAIL_CLOSED=true` env var → halts on DB failure or tampered snapshot
- **Audit trail**: `avm_baseline_change_log` records every change with reason, actor, host, hash
- **force=True requires reason**: `initialize_avm_baselines(force=True, reason="...")` or ValueError
- **DEGRADED_MODE**: logged clearly when DB unavailable or tampered snapshots detected
- **receipt_id canónico**: `OMNIX-TRD/INS/RBT/CRD/PUB-{12hex}` via `DecisionReceiptEngine.build_receipt_id(domain)`

## ADR-077 — Redis Anti-Replay Phase 2 (COMPLETED April 2026)
- **Backend Redis**: `SET key 1 NX PX ttl_ms` — atómico, cross-process, restart-safe
- **Modo `best_effort`** (default): Redis falla → in-memory fallback + WARNING
- **Modo `strict`**: Redis falla → fail-closed (replay rechazado)
- **Env var**: `OMNIX_ANTI_REPLAY_MODE=strict|best_effort`
- **Clave Redis**: `omnix:ar:{receipt_id}`

## ADR-078 — Signing Key Persistence (COMPLETED April 2026)
- **Carga desde env vars**: `OMNIX_SIGNING_SECRET_KEY_B64` + `OMNIX_SIGNING_PUBLIC_KEY_B64`
- **Modo `ephemeral_dev`** (default): genera efímeras, log WARNING + fingerprint de public key
- **Modo `required`**: falla si env vars no están
- **Self-test obligatorio**: sign/verify en cada startup
- **key_id**: SHA-256 fingerprint (16 hex chars) en cada receipt y endpoint
- **Key gen util**: `python -m omnix_core.tools.key_gen`

## ADR-079 — PKI Verification Endpoint (COMPLETED April 2026)
- **`GET /api/receipts/public-key`**: key metadata pública (algorithm, public_key_b64, key_id, active_since)
- **`POST /api/receipts/verify`**: verifica signature Dilithium-3 + cross-reference DB
- **Input validation**: receipt_id format, 64-char hex hash, signature max 8 KB
- **Rate limiting**: 60 req/min per IP (`OMNIX_VERIFY_RATE_LIMIT`)

## ADR-080 — Strict Input Schema Validation (COMPLETED 13-Apr-2026)
Validates every API request at the boundary, before any logic, Gemini calls, or DB access. Rejects malformed or unexpected input with clear 400 errors.

- **Public Sandbox**: `scenario_text` (10–1500 chars), `company_name` (≤120), `language` (16 idiomas), `email` (RFC 5321)
- **B2B API**: `signals`, `asset`, `domain`, `metadata` (≤50 keys, ≤8192 bytes serializado)
- **Política de mensajes**: mensajes neutros (no revelan campo names ni listas internas)

## ADR-081 — Per-Client B2B Quota Enforcement (COMPLETED 13-Apr-2026)
- **Daily quota**: `OMNIX_B2B_DAILY_QUOTA` = 5,000 eval/cliente/24h (rolling window)
- **Monthly quota**: `OMNIX_B2B_MONTHLY_QUOTA` = 50,000 eval/cliente/mes
- **Fail-open**: si DB no disponible → quota check pasa (no bloquea)
- **Circuit breaker**: 3 errores DB en 60s → fail-closed (`'Service temporarily unavailable'`)
- **Response 429**: `{"error": "...", "type": "quota_exceeded", "reference": "<ref_id>"}`
- **Harold alert**: aviso Telegram a 500 evaluaciones/mes (`_check_monthly_alert`)

## ADR-082 — W3C Verifiable Credentials — Public Governance Sandbox (COMPLETED Apr-2026)
- `type`: `["VerifiableCredential", "GovernanceDecisionCredential"]`
- `issuer.id`: `https://did.omnixquantum.net`
- `proof.type`: `Dilithium3Signature2024` (PQC) o `SHA256HashChain2024` (fallback)
- Respuesta API: campo `verifiable_credential` junto al `receipt` nativo

## ADR-083 — Enterprise Bot Security Middleware (COMPLETED Apr-2026)
- **Archivo**: `omnix_services/security/bot_security.py`
- **8 vulnerabilidades corregidas**: inyección prompt, rate limit, longitud, memory leak...
- **BotSecurityMiddleware**: único punto de entrada antes de cualquier handler o llamada AI

## ADR-053 — Generic Webhook System (COMPLETED Apr-2026)
- Webhook URL per-client vía `PUT /api/governance/admin/clients/<id>/webhook`
- Payload firmado HMAC-SHA256 en `X-OMNIX-Signature` header
- SSRF guard: rechaza IPs privadas/loopback
- Secrets cifrados en reposo con Fernet (`WEBHOOK_ENCRYPTION_KEY`)
- Delivery log: `webhook_delivery_log` table con latency_ms, status, skip_reason

## ADR-052 — Security Hardening (COMPLETED Apr-2026b)
- **Brute force lockout**: 5 fallos desde misma IP → 15 min lockout
- **API key expiry**: 90 días; `key_expires_at` en `b2b_clients`
- **Security headers**: X-Content-Type-Options, X-Frame-Options, HSTS, XSS-Protection
- **Admin IP allowlist**: `ADMIN_ALLOWED_IPS` env var → solo tu IP puede usar `/api/governance/admin/*`

## ADR-051 — B2B Usage Reporting (COMPLETED)
- `GET /api/governance/admin/usage` — uso por cliente
- `scripts/provision_b2b_client.py` — provisioning script
- Billing audit trail en `decision_receipts`

## ADR-058 — Bot Governance Integration (COMPLETED)
- `/evaluar [escenario]` — 11 checkpoints, receipt ID
- `/gobernanza` — alias inglés `/governance`
- `/velos` — admin-only, query a PostgreSQL
- `/recibo` — admin-only, receipt lookup
- `/impact` — impacto de gobernanza
- Rate limit: 5 evaluaciones/hora/usuario

## ADR-057 — Critical Override Hybrid Expansion (COMPLETED)
- Group 5 (No Human Oversight) y Group 7 (PEP) añadidos a `financial_crime_complex`
- Summary Quality Guard: captura "moderate risk", "acceptable risk", "low risk profile"

## ADR-059 — Executive Audit Dashboard (COMPLETED)
- `/audit`: KPIs, domain breakdown, tabla filtrable, panel de detalle
- `/api/public/audit-demo` (público, sintético) + `/api/governance/audit/decisions` (API key)
- Badge PQC SIGNED + CHAIN LINKED por decisión

## ADR-060 — Guided Investor Demo (COMPLETED)
- `/demo`: 4 stages — scenario selection, animated 11-checkpoint pipeline, decision receipt, narrative

---

## AGL-MED-001 — Medical AI Governance Vertical (COMPLETED)

| Campo | Valor |
|---|---|
| Domain | `medical_ai` |
| Prefix | `OMNIX-MED` |
| Rutas | `/governance-demo-medical`, `/medical` |
| Hard blocks | `ethics_flag=True` o `consent_verified=False` |
| Simulador | 24/7, ciclos 4 min, 4-10 decisiones/ciclo |
| Regulaciones | FDA SaMD, EU AI Act High-Risk, UAE DOH, MHRA, ISO 14971 |

Señales: diagnostic_confidence → probability_score, patient_risk → risk_exposure, multi-signal coherence, recovery trend, comorbidity resilience, care_plan + ethics alignment.

## AGL-AGT-001 — Autonomous Agent Governance Vertical (COMPLETED)

| Campo | Valor |
|---|---|
| Domain | `autonomous_agent` |
| Prefix | `OMNIX-AGT` |
| Rutas | `/governance-demo-agents`, `/agents` |
| Hard blocks | `safety_critical_flag=True` o `human_approval_required + not approved` |
| Simulador | 24/7, ciclos 200s, 3-8 decisiones/ciclo |
| Agent types | Financial, Enterprise, Logistics, Infrastructure, Research |

---

## 11. ROADMAP

### Quick Wins (hacer pronto)

| ID | Tarea | Tiempo | Estado |
|---|---|---|---|
| ROAD-005 | Google Analytics G-1S23G6K2YS | Hecho | ✅ EN PRODUCCIÓN |
| ROAD-006 | Formulario "¿Cómo nos encontraste?" + lead capture DB | Hecho | ✅ EN PRODUCCIÓN |
| ROAD-007 | Email field en sandbox `/try` | Hecho | ✅ EN PRODUCCIÓN |
| — | Video demo en CommercialLanding | Hecho | ✅ EN PRODUCCIÓN |
| — | Bot indestructible (pool×16, retry, error handler) | Hecho | ✅ EN PRODUCCIÓN |
| — | Fix idioma bot español/portugués | Hecho | ✅ EN PRODUCCIÓN |
| — | Gemini billing activation | 5 min (Harold) | ⚠️ PENDIENTE — requiere console.cloud.google.com |
| — | Comandos `/clientes` + `/nuevo_cliente` en bot | Implementado | ✅ EN PRODUCCIÓN |

### Mejoras Media Prioridad (activar con cliente confirmado)

| ID | Idea | Prioridad |
|---|---|---|
| ROAD-002 | Webhook retry con backoff exponencial (3 intentos: 5s, 30s, 5min) | Media |
| ROAD-008 | ✅ DONE (ADR-063) — Filtrar recibos inválidos en `/verify` | COMPLETADO |
| ROAD-010 | CP-6 Sharia Audit Trail completo → receipt PQC con flag Sharia | Media — cliente islámico |
| ROAD-009 | Context Admission Gate (CAG) — evaluación pre-pipeline de condiciones globales | Baja — post-ronda |
| ROAD-011 | Breach Containment Engine (MOD-010) — bloqueo automático bajo ciberataque | Baja — post-ronda |
| ROAD-012 | Multi-Domain Risk Governance (MOD-013) — score unificado financiero+técnico+legal | Baja — post-ronda |
| ROAD-001 | CP-0 Privacy Gate — escaneo PII antes del pipeline (EdTech / HealthTech) | Media — cliente EdTech |
| ROAD-003 | SDK Java / Go — para bancos (Java) y fintechs (Go) | Baja — post-ronda |
| ROAD-004 | Multi-tenant Client Portal — admin ve todos sus sub-clientes | Baja — post-ronda |

### A Nivel de Infraestructura para Escalar

| Mejora | Cuándo activar |
|---|---|
| Gemini pay-as-you-go billing | Ahora — antes de que llegue el primer cliente |
| Redis en modo `strict` (anti-replay) | Con primer cliente de pago |
| `OMNIX_SIGNING_KEY_*` en env vars (modo `required`) | Con primer cliente de pago |
| Admin IP allowlist (`ADMIN_ALLOWED_IPS`) | Ahora |
| Monitoreo Railway con alertas de downtime | Con primer cliente de pago |
| Backup PostgreSQL programado | Ahora |

---

> **Referencia completa de módulos de largo plazo (MOD-001 a MOD-018):** ver `docs/DASHBOARD_IMPROVEMENT_BACKLOG.md` § GOVERNANCE MODULES ROADMAP (Mar 2026)

> **Arquitectura completa:** `docs/current/ARCHITECTURE.md`
> **Operations:** `docs/operations/DEPLOYMENT.md`
> **Paper académico:** Zenodo/SSRN — 11-checkpoint pipeline alineado con `b9d6606f`

---

## ADR-SRG-001 — Stablecoin Reserve Governance (Vertical 9)

**Fecha**: 2026-04-18 | **Status**: ACTIVE | **Mercado objetivo**: $150B stablecoins + $16T RWA tokenization

### Descripción
9º vertical de OMNIX Quantum. Gobernanza de reservas de stablecoins con cumplimiento MiCA.
Prefix de recibo: `OMNIX-SRG-{12HEX}` | Color: `#8B5CF6` (violet) | Icono: 🪙

### Archivos Principales
| Archivo | Descripción |
|---|---|
| `omnix_core/stablecoin/stablecoin_signal_adapter.py` | 6 señales, 6 hard blocks (peg>2%, coverage<100%, liquid<60% MiCA, AML, sanctions, counterparty_default) |
| `omnix_core/stablecoin/stablecoin_simulator.py` | 24/7 background simulator — ciclos 240s, 3–7 decisiones/ciclo, 8 assets, 6 jurisdicciones |
| `omnix_dashboard/blueprints/stablecoin_governance.py` | 9 REST endpoints: /metrics, /decisions, /by-type, /by-asset, /by-jurisdiction, /timeline, /live-feed, /evaluate, /health |
| `omnix_web/src/pages/StablecoinDashboard.tsx` | Live dashboard React |
| `omnix_web/src/pages/StablecoinGovernanceDemo.tsx` | Demo interactivo 11-checkpoints |

### Señales de Gobernanza
1. `peg_stability` — Desviación del peg (hard block >2%)
2. `reserve_coverage` — Cobertura de reservas (hard block <100% MiCA)
3. `liquidity_ratio` — Liquidez inmediata (hard block <60%)
4. `counterparty_risk` — Riesgo de contraparte
5. `regulatory_compliance` — AML/KYC/sanciones (hard block)
6. `market_depth` — Profundidad de mercado

### Assets soportados
USDC, USDT, BUSD, PYUSD, EURC, GUSD, FRAX, DAI

### Jurisdicciones
EU (MiCA), UK (FCA), US (OCC), UAE (CBUAE), Singapore (MAS), International

### Rutas React
- `/stablecoin` — Live Governance Dashboard
- `/governance-demo-stablecoin` — Interactive 11-Checkpoint Demo

### Integración Backend
- Blueprint registrado en `omnix_dashboard/blueprints/__init__.py`
- Tablas inicializadas en `omnix_dashboard/app.py`
- Simulador iniciado en background thread al arranque
- Receipt prefix `"stablecoin": "SRG"` en `decision_receipt.py`
- **server.py (puerto 8080 producción Railway):** tablas en `_ensure_vertical_tables`, simulador en `_start_vertical_simulators`, 6 rutas `/api/stablecoin/*` (metrics, live-feed, by-type, by-asset, by-jurisdiction, timeline)

### Dashboard React (StablecoinDashboard.tsx) — v2 completo (Abr 2026)
- 8 KPIs: Volume Governed, Approved Volume, Decisions/24h, Peg Deviation, Reserve Coverage, Liquid Reserves, Hard Blocks, Gov Score
- PegGauge SVG semicircular, CoverageMeter, LiquidRatio bar, SignalStrip pipeline health
- Reserve Asset Breakdown (8 assets con iconos y colores), Jurisdiction Breakdown (6 jurisdicciones con banderas y barras)
- Decision Type Performance grid (5 tipos)
- Hard Block Alerts section (MiCA / AML / sanciones)
- Live Decision Feed tabla (12 columnas: ID, tipo, asset, jurisdicción, monto, peg, coverage, liquid, score, veredicto, receipt, tiempo)
- Auto-refresh cada 10s, helper `pct()` para normalizar rates decimal/porcentaje de PostgreSQL
- Proxy Vite `/api/stablecoin` → `:5000` en `vite.config.ts`
