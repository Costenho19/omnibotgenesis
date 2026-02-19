# OMNIX B2C Implementation Plan

**Version:** 1.0
**Created:** December 10, 2025
**Status:** ARCHIVED — SUPERSEDED BY B2B-FIRST STRATEGY
**Target Product:** OMNIX Asesor Personal IA

> **ARCHIVAL NOTE (Feb 19, 2026):** This document reflects an earlier strategy focused on B2C SaaS as the primary revenue model. As of February 2026, OMNIX has repositioned as **Decision Governance Infrastructure** with an 80% B2B / 20% B2C revenue split. The current business model prioritizes enterprise licensing to prop firms, trading platforms, and regulated funds. B2C SaaS remains a secondary revenue stream (Pro $149/mo, Advanced $499/mo) that launches after enterprise validation. See `OMNIX_BUSINESS_MODEL_CANVAS.md` and `OMNIX_EUREKA_PITCH_FINAL.md` for the current strategy. The B2C pricing below ($49 Basic tier) is no longer in the active plan.

> **Note (Dec 24, 2025):** This plan is on the roadmap but NOT yet implemented. No Stripe, Auth0, or Clerk integration exists. Multi-tenant infrastructure is planned but not built.

---

## Executive Summary

Este documento define el roadmap para transformar OMNIX de un sistema de trading institucional a un producto B2C monetizable. El objetivo es alcanzar:

| Milestone | Usuarios | MRR | Timeline |
|-----------|----------|-----|----------|
| MVP | 50 | $950 | Mes 2 |
| Growth | 200 | $5,800 | Mes 6 |
| Scale | 500+ | $24,500 | Mes 12 |

---

## Table of Contents

1. [Gap Analysis](#1-gap-analysis)
2. [Target Product Definition](#2-target-product-definition)
3. [Architecture for SaaS](#3-architecture-for-saas)
4. [Implementation Roadmap](#4-implementation-roadmap)
5. [Infrastructure & DevOps](#5-infrastructure--devops)
6. [Financial Projections](#6-financial-projections)
7. [Risk Assessment](#7-risk-assessment)

---

## 1. Gap Analysis

### 1.1 Existing Capabilities (Ready)

| Funcionalidad | Ubicación en Código | Estado | Preparado B2C |
|---------------|---------------------|--------|---------------|
| Análisis de mercado | `omnix_core/strategies/` | ✅ Completo | ⚠️ Solo API interna |
| Señales de trading | QuantumMomentum, Monte Carlo, HMM | ✅ Completo | ⚠️ Solo Telegram |
| Alertas de riesgo | Risk Guardian V5.4, Coherence Engine | ✅ Completo | ⚠️ Sin push notifications |
| Voz automática (TTS) | `omnix_services/ai_service/` | ✅ Funcional | ✅ Listo |
| Multilenguaje | ConversationalAIService | ✅ ES/EN | ✅ Listo |
| Análisis técnico | 10 estrategias institucionales | ✅ Completo | ⚠️ Sin UI amigable |
| Riesgo avanzado | Risk Guardian, CAES | ✅ Completo | ⚠️ Solo logs internos |
| On-chain analytics | `on_chain_intelligence.py` | ⚠️ Parcial | ❌ Sin UI |
| Microestructura | Execution Protocol V6.5.4 | ✅ Completo | ⚠️ Oculto al usuario |
| Panel premium | Flask + Streamlit | ✅ Funcional | ⚠️ Sin autenticación |
| Portfolio optimization | `portfolio_management/` | ✅ Completo | ⚠️ Sin workflow usuario |
| Monte Carlo predictions | `strategies/monte_carlo.py` | ✅ Completo | ⚠️ Sin exposición API |

### 1.2 Missing Capabilities (Required for B2C)

| Componente | Impacto | Esfuerzo | Prioridad |
|------------|---------|----------|-----------|
| **Autenticación multi-usuario** | BLOQUEANTE | 8h | P0 |
| **Integración Stripe (billing)** | BLOQUEANTE | 12h | P0 |
| **Planes de suscripción ($19/$29/$49)** | BLOQUEANTE | 4h | P0 |
| **Tenant isolation (multi-tenant)** | CRÍTICO | 8h | P0 |
| **Rate limiting por plan** | ALTO | 4h | P1 |
| **Dashboard web autenticado** | ALTO | 12h | P1 |
| **Onboarding automático** | ALTO | 8h | P1 |
| **Portfolio advisor API** | ALTO | 8h | P1 |
| **Push notifications** | MEDIO | 6h | P2 |
| **API pública documentada** | MEDIO | 12h | P2 |

### 1.3 Code Quality Assessment

| Aspecto | Estado Actual | Requerido para SaaS |
|---------|---------------|---------------------|
| ConversationalAIService | 371 líneas monolíticas | Refactorizar con DI |
| Dashboard auth | ⚠️ API KEY opcional | ✅ JWT obligatorio |
| Telegram bot | Single-tenant | Multi-tenant con user_id |
| Database isolation | Shared tables | Row-Level Security |
| Feature flags | Básico | Por plan de usuario |
| Error handling | Logs internos | User-facing messages |

---

## 2. Target Product Definition

### 2.1 OMNIX Asesor Personal IA

**Propuesta de valor:** Asesor financiero IA 24/7 con análisis institucional a precio accesible.

### 2.2 Feature Matrix by Plan

| Feature | Free | Basic ($19) | Pro ($29) | Premium ($49) |
|---------|------|-------------|-----------|---------------|
| Análisis de mercado | 3/día | 20/día | 100/día | Ilimitado |
| Señales de trading | ❌ | 5/día | 20/día | Ilimitado |
| Alertas personalizadas | ❌ | 3 activas | 10 activas | Ilimitado |
| Voz automática | ❌ | ❌ | ✅ | ✅ |
| Análisis técnico avanzado | ❌ | ✅ | ✅ | ✅ |
| Portfolio advisor | ❌ | ❌ | Básico | Completo |
| Predicciones probabilísticas | ❌ | ❌ | ✅ | ✅ + histórico |
| Riesgo avanzado | ❌ | ❌ | ✅ | ✅ |
| On-chain analytics | ❌ | ❌ | ❌ | ✅ |
| Reportes PDF | ❌ | ❌ | Mensual | Semanal |
| Soporte | Community | Email 48h | Email 24h | Prioritario |

### 2.3 User Journeys

**Journey 1: Nuevo usuario Free → Basic**
```
Landing → Signup → Onboarding quiz → Free trial (7 días Pro)
→ Recibe 3 señales exitosas → Upgrade prompt → Pago → Basic
```

**Journey 2: Usuario Basic busca análisis**
```
Login → Dashboard → "Analiza BTC" → Respuesta IA con gráfico
→ "¿Debería comprar?" → Señal con confianza → Alerta configurada
```

**Journey 3: Usuario Premium portfolio**
```
Login → Conecta Kraken API (read-only) → Import portfolio
→ Análisis riesgo automático → Recomendaciones diversificación
→ Reporte PDF semanal → Alertas proactivas
```

---

## 3. Architecture for SaaS

### 3.1 Current Architecture (Institutional)

```
                    ESTADO ACTUAL
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   Telegram Bot     Flask API      Streamlit
   (single user)   (no auth)     (no auth)
        │                │                │
        └────────┬───────┴────────────────┘
                 │
        ┌────────▼────────┐
        │ DatabaseGateway │ ← Todos comparten
        │   (shared)      │
        └─────────────────┘
```

### 3.2 Target Architecture (B2C SaaS)

```
                    ARQUITECTURA B2C
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   Web App          Mobile App       Telegram
   (Next.js)         (futuro)        (multi-tenant)
        │                │                │
        └────────┬───────┴────────────────┘
                 │
        ┌────────▼────────┐
        │   API Gateway   │ ← Rate limiting por plan
        │  (Kong/Nginx)   │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │   Auth Layer    │ ← JWT + Refresh Tokens
        │  (Clerk/Auth0)  │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Subscription   │ ← Stripe Billing
        │    Manager      │
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
 Flask API   Background    Telegram
(endpoints)   Workers       Bot
    │            │            │
    └────────────┼────────────┘
                 │
        ┌────────▼────────┐
        │ DatabaseGateway │ ← Row-Level Security
        │ (tenant_id)     │
        └─────────────────┘
```

### 3.3 Database Schema Changes

**Nueva tabla: subscriptions**
```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id),
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    plan VARCHAR(50), -- 'free', 'basic', 'pro', 'premium'
    status VARCHAR(50), -- 'active', 'cancelled', 'past_due'
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Nueva tabla: usage_tracking**
```sql
CREATE TABLE usage_tracking (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id),
    feature VARCHAR(100), -- 'analysis', 'signal', 'alert', 'voice'
    count INTEGER DEFAULT 0,
    period_start DATE,
    period_end DATE,
    UNIQUE(user_id, feature, period_start)
);
```

**Modificación: Agregar tenant_id a tablas existentes**
```sql
-- Ejemplo para paper_trading_trades
ALTER TABLE paper_trading_trades 
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(255);

-- Row-Level Security
ALTER TABLE paper_trading_trades ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON paper_trading_trades
    USING (tenant_id = current_setting('app.current_tenant'));
```

### 3.4 API Endpoints (New)

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/api/v1/auth/signup` | POST | User registration | Public |
| `/api/v1/auth/login` | POST | User login | Public |
| `/api/v1/auth/refresh` | POST | Refresh token | JWT |
| `/api/v1/subscription/plans` | GET | List available plans | Public |
| `/api/v1/subscription/checkout` | POST | Create Stripe checkout | JWT |
| `/api/v1/subscription/portal` | POST | Stripe customer portal | JWT |
| `/api/v1/subscription/webhook` | POST | Stripe webhooks | Stripe signature |
| `/api/v1/advisor/analyze` | POST | Market analysis | JWT + Plan check |
| `/api/v1/advisor/portfolio` | POST | Portfolio analysis | JWT + Pro/Premium |
| `/api/v1/advisor/predict` | POST | Probabilistic forecast | JWT + Pro/Premium |
| `/api/v1/signals` | GET | Get user signals | JWT + Basic+ |
| `/api/v1/alerts` | GET/POST/DELETE | Manage alerts | JWT + Basic+ |
| `/api/v1/reports/pdf` | GET | Generate PDF report | JWT + Pro/Premium |

---

## 4. Implementation Roadmap

### Phase 1: SaaS Foundation (Weeks 1-3) 🔴 CRITICAL

**Objective:** Enable user registration and payment

| ID | Task | Hours | Priority | Dependencies |
|----|------|-------|----------|--------------|
| 1.1 | Integrate Clerk/Auth0 for authentication | 8 | P0 | None |
| 1.2 | Add tenant_id to critical tables (migrations) | 4 | P0 | 1.1 |
| 1.3 | Implement Row-Level Security in PostgreSQL | 4 | P0 | 1.2 |
| 1.4 | Integrate Stripe with 3 plans | 12 | P0 | 1.1 |
| 1.5 | Create subscriptions and usage_tracking tables | 2 | P0 | 1.2 |
| 1.6 | Build web signup/login flow | 8 | P1 | 1.1, 1.4 |
| 1.7 | Protect dashboards with mandatory auth | 4 | P0 | 1.1 |
| 1.8 | Implement rate limiting per plan | 4 | P1 | 1.4 |

**Deliverable:** User can signup, pay, and access authenticated dashboard.

**Verification Checklist:**
- [ ] User can register with email/password or OAuth
- [ ] User can subscribe to Basic/Pro/Premium plan
- [ ] Stripe webhook correctly updates subscription status
- [ ] Dashboard requires authentication
- [ ] API returns 401 for unauthenticated requests
- [ ] Rate limits enforced per plan

---

### Phase 2: Product Workflows (Weeks 3-6) 🟡 HIGH

**Objective:** Deliver differentiated value

| ID | Task | Hours | Priority | Dependencies |
|----|------|-------|----------|--------------|
| 2.1 | Create Portfolio Advisor API endpoint | 8 | P0 | Phase 1 |
| 2.2 | Build Probabilistic Predictions service | 6 | P0 | 2.1 |
| 2.3 | Implement voice alert pipeline | 6 | P1 | 2.1 |
| 2.4 | Create personalized user dashboard | 12 | P0 | 1.6 |
| 2.5 | Expose On-Chain analytics in UI | 8 | P1 | 2.4 |
| 2.6 | Build push notifications (Telegram + Email + Web) | 8 | P1 | 2.1 |
| 2.7 | Create user portfolio risk evaluator | 6 | P0 | 2.1 |
| 2.8 | Build signal history and performance tracking | 6 | P1 | 2.1 |

**Deliverable:** User receives personalized analysis, signals, and recommendations.

**Verification Checklist:**
- [ ] User can request portfolio analysis
- [ ] User receives probabilistic predictions with confidence levels
- [ ] Voice alerts work for Pro/Premium users
- [ ] Dashboard shows personalized metrics
- [ ] On-chain data visible for Premium users
- [ ] Push notifications delivered successfully

---

### Phase 3: Reliability & Compliance (Weeks 5-8) 🟡 MEDIUM

**Objective:** Scale safely with legal protection

| ID | Task | Hours | Priority | Dependencies |
|----|------|-------|----------|--------------|
| 3.1 | Add investment disclaimers to all advice | 4 | P0 | Phase 2 |
| 3.2 | Implement audit logging for all advice given | 6 | P0 | 2.1 |
| 3.3 | Set up monitoring with SLOs (99.5% uptime) | 8 | P1 | Phase 1 |
| 3.4 | Implement GDPR data retention policies | 4 | P1 | 1.2 |
| 3.5 | Create incident response runbooks | 4 | P2 | 3.3 |
| 3.6 | Load testing (1K concurrent users) | 6 | P1 | Phase 2 |
| 3.7 | Security audit and penetration testing | 8 | P1 | Phase 2 |

**Deliverable:** Robust system with legal compliance and traceability.

**Verification Checklist:**
- [ ] All advice includes legal disclaimer
- [ ] Audit logs capture every recommendation
- [ ] Prometheus/Grafana dashboards operational
- [ ] User can request data export (GDPR)
- [ ] User can delete account (GDPR)
- [ ] Load test passes for 1K users

---

### Phase 4: Growth Enablement (Weeks 7-10) 🟢 LOW

**Objective:** Optimize conversion and retention

| ID | Task | Hours | Priority | Dependencies |
|----|------|-------|----------|--------------|
| 4.1 | Analytics funnel (signup → paid) | 8 | P1 | Phase 1 |
| 4.2 | A/B testing on onboarding | 6 | P2 | 4.1 |
| 4.3 | Referral program implementation | 8 | P2 | 1.4 |
| 4.4 | Public API documentation (OpenAPI) | 12 | P2 | Phase 2 |
| 4.5 | Premium signal marketplace | 16 | P3 | Phase 2 |
| 4.6 | Mobile app (React Native) | 40 | P3 | Phase 2 |

**Deliverable:** Optimized conversion funnel and growth tools.

---

## 5. Infrastructure & DevOps

### 5.1 Environment Configuration

| Tier | Users | Hosting | Database | Redis | Cost/month |
|------|-------|---------|----------|-------|------------|
| **Starter** | 50 | Railway Hobby | Railway Postgres | Railway Redis | ~$25 |
| **Growth** | 200 | Railway Pro | Railway Postgres | Redis Cloud | ~$100 |
| **Scale** | 500+ | Railway Pro + Workers | Neon Pro | Redis Cloud Pro | ~$300 |

### 5.2 Required Environment Variables

```bash
# Authentication
AUTH_PROVIDER=clerk  # or auth0
CLERK_PUBLISHABLE_KEY=pk_live_xxx
CLERK_SECRET_KEY=sk_live_xxx
JWT_SECRET=xxx

# Stripe Billing
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_BASIC=price_xxx
STRIPE_PRICE_PRO=price_xxx
STRIPE_PRICE_PREMIUM=price_xxx

# Rate Limiting
RATE_LIMIT_FREE=3
RATE_LIMIT_BASIC=20
RATE_LIMIT_PRO=100
RATE_LIMIT_PREMIUM=1000

# Feature Flags
ENABLE_VOICE_ALERTS=true
ENABLE_ONCHAIN=true
ENABLE_PORTFOLIO_ADVISOR=true
```

### 5.3 CI/CD Pipeline (Railway Auto-Deploy)

**OMNIX utiliza Railway con auto-deploy nativo.** No se usa GitHub Actions.

#### Flujo de Deploy

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Git Push   │ ──▶ │   Railway   │ ──▶ │    Build    │ ──▶ │   Deploy    │
│  to main    │     │   Detect    │     │  Container  │     │  Production │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

#### Archivos de Configuración

**Procfile** (para Gunicorn/Flask):
```
web: gunicorn wsgi:app -b 0.0.0.0:$PORT --workers 2 --threads 4
```

**railway.json** (para Bot principal):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python -u main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### Proceso de Deploy

| Paso | Acción | Automático |
|------|--------|------------|
| 1 | Push a branch `main` | Manual |
| 2 | Railway detecta cambio | ✅ Auto |
| 3 | Nixpacks build (instala requirements.txt) | ✅ Auto |
| 4 | Deploy a producción | ✅ Auto |
| 5 | Health check | ✅ Auto |

#### Rollback

Si hay errores después del deploy:

1. **Railway Dashboard** → Deployments → Seleccionar deploy anterior
2. Click **"Redeploy"** en la versión estable
3. El rollback es instantáneo (no rebuild)

#### Ambientes

| Ambiente | Branch | URL |
|----------|--------|-----|
| Production | `main` | omnix-production.up.railway.app |
| Staging (futuro) | `staging` | omnix-staging.up.railway.app |

#### Pre-Deploy Checklist (Manual)

Antes de push a main:
- [ ] Tests locales pasan (`pytest tests/ -v`)
- [ ] Sin errores de lint (`ruff check .`)
- [ ] Variables de entorno actualizadas en Railway
- [ ] Migraciones de DB verificadas

### 5.4 Monitoring Stack

| Tool | Purpose | Cost |
|------|---------|------|
| Sentry | Error tracking | Free tier |
| Prometheus | Metrics collection | Self-hosted |
| Grafana | Dashboards | Free tier |
| Uptime Robot | Uptime monitoring | Free tier |
| LogDNA/Papertrail | Log aggregation | ~$20/month |

---

## 6. Financial Projections

### 6.1 Cost Structure

| Category | Starter | Growth | Scale |
|----------|---------|--------|-------|
| Hosting | $25 | $100 | $300 |
| Auth (Clerk) | $0 | $25 | $99 |
| Stripe fees (2.9%) | $28 | $168 | $711 |
| Monitoring | $0 | $20 | $50 |
| Support tools | $0 | $0 | $50 |
| **Total** | **$53** | **$313** | **$1,210** |

### 6.2 Revenue Projections

| Month | Free | Basic | Pro | Premium | MRR | Costs | Profit |
|-------|------|-------|-----|---------|-----|-------|--------|
| 1 | 100 | 10 | 5 | 2 | $433 | $53 | $380 |
| 2 | 200 | 30 | 15 | 5 | $1,000 | $80 | $920 |
| 3 | 400 | 60 | 30 | 10 | $2,079 | $150 | $1,929 |
| 6 | 1000 | 120 | 60 | 20 | $4,158 | $313 | $3,845 |
| 12 | 2500 | 300 | 150 | 50 | $10,395 | $600 | $9,795 |

### 6.3 Break-even Analysis

| Metric | Value |
|--------|-------|
| Development cost | ~$9,000 (180 hours @ $50/h) |
| Monthly fixed costs | ~$300 at scale |
| Break-even point | Month 5-6 |
| 12-month cumulative profit | ~$60,000 |

---

## 7. Risk Assessment

### 7.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Auth provider downtime | LOW | HIGH | Fallback to local JWT validation |
| Stripe API issues | LOW | HIGH | Queue webhooks, retry logic |
| Database overload at scale | MEDIUM | HIGH | Connection pooling, read replicas |
| AI service rate limits | MEDIUM | MEDIUM | Caching, request batching |
| Telegram bot conflicts | LOW | MEDIUM | Multi-instance with user routing |

### 7.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low conversion rate | MEDIUM | HIGH | A/B testing, free trial |
| High churn | MEDIUM | HIGH | Engagement notifications, value delivery |
| Regulatory issues | LOW | HIGH | Disclaimers, no "advice" wording |
| Competition | MEDIUM | MEDIUM | Feature differentiation, community |

### 7.3 Legal Considerations

**CRITICAL:** OMNIX provides "analysis" and "information", NOT "financial advice".

Required disclaimers:
- "OMNIX no proporciona asesoramiento financiero. Las señales son informativas."
- "El rendimiento pasado no garantiza resultados futuros."
- "Invierte solo lo que puedas permitirte perder."

---

## Appendix A: Technology Stack

| Layer | Current | Target | Reason |
|-------|---------|--------|--------|
| Auth | None | Clerk | Plug-and-play, multi-tenant |
| Billing | None | Stripe | Industry standard |
| Frontend | Streamlit | Next.js + Streamlit | Web app + analytics |
| API Gateway | None | Nginx/Kong | Rate limiting, auth |
| Backend | Flask | Flask + Celery | Async workers |
| Database | PostgreSQL | PostgreSQL + RLS | Tenant isolation |
| Cache | Redis | Redis Cluster | HA for 500+ users |
| Monitoring | None | Prometheus + Grafana | Already have JSON |

---

## Appendix B: Migration Checklist

### Pre-Launch
- [ ] Auth integration tested
- [ ] Stripe webhook verified
- [ ] Rate limiting confirmed
- [ ] Dashboard protected
- [ ] Legal disclaimers added
- [ ] GDPR compliance verified
- [ ] Load testing passed
- [ ] Monitoring operational

### Launch Day
- [ ] DNS configured
- [ ] SSL certificates valid
- [ ] Error tracking enabled
- [ ] Team on standby
- [ ] Rollback plan ready

### Post-Launch (Week 1)
- [ ] Monitor conversion funnel
- [ ] Check error rates
- [ ] Gather user feedback
- [ ] Iterate on onboarding

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 10, 2025 | OMNIX Team | Initial B2C implementation plan |
