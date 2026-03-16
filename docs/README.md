# OMNIX — Documentación

**Identidad**: Decision Governance Infrastructure for Automated Systems  
**Actualizado**: 19 de Febrero 2026  
**Estado**: Producción 24/7 en Railway | Track Record COMPLETADO (30 días) | Fase 1 Operativa  
**Versión interna (dev)**: V6.5.4e

---

## PROTOCOLO OBLIGATORIO

> **ANTES de hacer cambios de código**: Revisar esta documentación para entender el estado actual del sistema.
>
> **DESPUÉS de cambios significativos**: Actualizar la documentación correspondiente.

Ver `replit.md` para el checklist completo de prioridades de revisión.

---

## Documentación para Inversores

> **NEW**: Documentos de producto institucional disponibles en `docs/business/investor/`

| Documento | Propósito | Audiencia |
|-----------|-----------|-----------|
| [PRODUCT_OVERVIEW.md](business/investor/PRODUCT_OVERVIEW.md) | Qué es OMNIX, qué problema resuelve, qué NO hace | Inversores, Family Offices |
| [RISK_GUARDIAN_PRODUCT.md](business/investor/RISK_GUARDIAN_PRODUCT.md) | Sistema de riesgo empaquetado como producto | Risk Officers, Due Diligence |
| [TRACK_RECORD_CASE_STUDY.md](business/investor/TRACK_RECORD_CASE_STUDY.md) | Narrativa: cómo OMNIX protege capital | Prospectos, Pitch Meetings |
| [PITCH_DECK_OUTLINE.md](business/investor/PITCH_DECK_OUTLINE.md) | Esqueleto de 12 slides para presentación | Pitch Meetings |
| [OMNIX_PITCH_SCRIPTS.md](business/OMNIX_PITCH_SCRIPTS.md) | Scripts 60s y 90s (EN/ES) con notas de entrega | Eureka Dubai, Elevator, Networking |
| [OMNIX_GOVERNANCE_BEHAVIOR_SNAPSHOT.md](business/OMNIX_GOVERNANCE_BEHAVIOR_SNAPSHOT.md) | Evidencia real de gobernanza activa con datos de producción | Pitch, Due Diligence, Auditoría |
| [INSTITUTIONAL_GOVERNANCE_STRUCTURE.md](business/investor/INSTITUTIONAL_GOVERNANCE_STRUCTURE.md) | Estructura de gobernanza institucional: 3 layers (Human Authority, Control Architecture, Future Expansion) | Due Diligence, Compliance, Board |

**Posicionamiento**: OMNIX = **Decision Governance Infrastructure for Automated Systems** — building the category of Decision Governance Infrastructure.  
Primer vertical validado: Digital Asset Trading. Arquitectura domain-agnostic para expansión multi-vertical.

**Referencia**: [ADR-023](reference/adr/ADR-023-investor-positioning-refinement.md) - Reglas de posicionamiento investor  
**Referencia**: [ADR-025](reference/adr/ADR-025-decision-governance-platform.md) - Repositioning como Decision Governance Platform  
**Referencia**: [ADR-026](reference/adr/ADR-026-multi-vertical-governance-architecture.md) - Multi-Vertical Governance Architecture (Domain Adapter Pattern)  
**Referencia**: [ADR-027](reference/adr/ADR-027-decision-governance-infrastructure.md) - Decision Governance Infrastructure for Automated Systems (Category Creation)  
**Referencia**: [ADR-028](reference/adr/ADR-028-external-signal-evaluation-api.md) - External Signal Evaluation API — POST /api/governance/evaluate (B2B product endpoint, PQC-signed receipts)  
**Referencia**: [ADR-029](reference/adr/ADR-029-governance-compliance-modules.md) - Governance Compliance Modules — NIST AI RMF + ISO/IEC 42001 + EU AI Act (5 módulos, 21 endpoints, 7 tablas)  
**Referencia**: [ADR-030](reference/adr/ADR-030-insurance-domain-pilot.md) - Insurance Domain Pilot — tercer dominio validado con 3 receipts PQC reales (Mar 1, 2026)  
**Referencia**: [ADR-032](reference/adr/ADR-032-temporal-coherence-validation.md) - Temporal Coherence Validation (TCV) — Checkpoint 7 del trading pipeline. Evalúa admisibilidad temporal de decisiones (Mar 2026). 49 tests pasando.  
**Referencia**: [ADR-033](reference/adr/ADR-033-signal-integrity-validator.md) - Signal Integrity Validator (SIV) — Checkpoint 0. Data quality gate pre-análisis: freshness + completeness + anomaly + cross-source. 46 tests pasando (Mar 2026).  
**Referencia**: [ADR-034](reference/adr/ADR-034-forward-trajectory-implication.md) - Forward Trajectory Implicator (FTI) — Checkpoint 7b. Forward-looking complement to TCV: Regime Transition Risk + Implied Consistency + Signal Momentum. 45 tests pasando (Mar 2026).  
**Referencia**: [ADR-035](reference/adr/ADR-035-regime-conditioned-kelly.md) - Regime-Conditioned Kelly (RCK). Kelly inputs segmentados por régimen HMM con 3-level fallback chain. 36 tests pasando (Mar 2026).  
**Referencia**: [ADR-036](reference/adr/ADR-036-exit-governance-layer.md) - Exit Governance Layer (EGL). 3-gate exit pipeline + PQC-signed exit receipts. Exit governance parity with entry governance. 44 tests pasando (Mar 2026).  
**Referencia**: [ADR-041](reference/adr/ADR-041-multi-agent-decision-governance.md) - Multi-Agent Decision Governance. 3 agentes especializados (SignalAgent 45%, RiskAgent 30%, SentimentAgent 25%) con consenso ponderado paralelo. Feature flag `ENABLE_MULTI_AGENT_GOVERNANCE`. 19 tests pasando (Mar 2026).  
**Referencia**: [ADR-042](reference/adr/ADR-042-hybrid-cryptography.md) - Hybrid Cryptography. X25519 (ECDH clásico) + Kyber-768 (PQC KEM) combinados via HKDF. Secreto combinado = HKDF(kyber_secret || ecdh_secret). Degradación grácil: hybrid → kyber_only → ecdh_only. 8 tests pasando (Mar 2026).  
**Referencia**: [ADR-043](reference/adr/ADR-043-crypto-agility-layer.md) - Crypto-Agility Layer. CryptoProvider interface + registry (dilithium3, dilithium5, ed25519). Swap de algoritmo vía `ACTIVE_SIGNING_PROVIDER` env var sin cambios de código. Backward-compatible. 10 tests pasando (Mar 2026).  
**Referencia**: [ADR-044](reference/adr/ADR-044-quantum-secure-decision-receipts.md) - Quantum-Secure Decision Receipts. Timestamping RFC 3161-style interno, rolling Merkle root, transparency log (`governance_transparency_log`). Receipts auto-verificables sin infraestructura OMNIX. 18 tests pasando (Mar 2026).

---

## Cambios Recientes

### ADR-044: Quantum-Secure Decision Receipts (Mar 16, 2026)
- **ESTADO**: ✅ COMPLETADO — Transparency log, timestamping RFC-3161-style, rolling Merkle root
- **Nuevo módulo**: `omnix_core/evidence/transparency_chain.py` — TransparencyChain + InternalTimestamp
- **Nueva tabla**: `governance_transparency_log` (log_id, receipt_id, symbol, payload_hash, prev_log_hash, merkle_root, signing_provider, ts_utc)
- **Actualizado**: `decision_receipt.py` → append automático al transparency log en cada receipt
- **Auto-verificable**: Receipts contienen todos los datos para verificación independiente sin OMNIX

### ADR-043: Crypto-Agility Layer (Mar 16, 2026)
- **ESTADO**: ✅ COMPLETADO — Provider registry + interface abstracta
- **Nuevo módulo**: `omnix_core/security/crypto_providers.py` — CryptoProvider ABC + 3 providers + registry
- **Providers**: dilithium3 (enterprise default), dilithium5 (high-assurance), ed25519 (dev/test)
- **Activación**: `ACTIVE_SIGNING_PROVIDER=dilithium5` — sin reescritura de código

### ADR-042: Hybrid Cryptography (Mar 16, 2026)
- **ESTADO**: ✅ COMPLETADO — X25519 + Kyber-768 + HKDF combiner
- **Nuevo módulo**: `omnix_core/security/hybrid_crypto.py` — HybridKEM class
- **Fórmula**: `combined_secret = HKDF(kyber_secret || ecdh_secret, label=OMNIX-ADR042-v1)`
- **Degradación**: hybrid → kyber768_only → x25519_only (fail-safe, nunca bloquea)

### ADR-041: Multi-Agent Decision Governance (Mar 16, 2026)
- **ESTADO**: ✅ COMPLETADO — Sistema multi-agente aditivo implementado
- **Agentes**: SignalAgent (Kraken+AlphaVantage, 0.45) + RiskAgent (DB+Redis, 0.30) + SentimentAgent (Finnhub+Tavily+FearGreed, 0.25)
- **Orquestador**: `asyncio.gather`, consenso ponderado, umbral BUY>+0.20 / SELL<-0.20
- **Integración**: Hook en `auto_trading_bot.py` línea ~3524, detrás de `ENABLE_MULTI_AGENT_GOVERNANCE=false`
- **DB**: Tabla `agent_orchestrator_runs` (JSONB por agente, trazabilidad completa)
- **Tests**: 19/19 pasando — cobertura de éxito, timeout, API caída, desacuerdo total, serialización
- **Diseño**: Arquitecto consultado antes de escribir código — fallback graceful, no bloquea pipeline
- **ADR**: [ADR-041](reference/adr/ADR-041-multi-agent-decision-governance.md)

### 4 Architectural Gaps — Pipeline Completeness (Mar 5, 2026)
- **ESTADO**: ✅ COMPLETADO — ADR-033 · ADR-034 · ADR-035 · ADR-036 | 171 nuevos tests pasando
- **SIV (CP-0, ADR-033)**: `omnix_core/data/signal_integrity_validator.py` — 4 validation categories, score 0-100, threshold 60, fail-safe pass-through. 46 tests.
- **FTI (CP-7b, ADR-034)**: `omnix_core/temporal/forward_trajectory.py` — 3-dimension forward implication (Regime Transition Risk 40%, Implied Consistency 35%, Signal Momentum 25%). Threshold 25/100. 45 tests.
- **RCK (ADR-035)**: `omnix_core/sizing/regime_conditioned_kelly.py` — Kelly inputs segmented by HMM regime, 3-level fallback chain. Replaces hardcoded win_rate=0.55. 36 tests.
- **EGL (ADR-036)**: `omnix_core/governance/exit_governance.py` — 3-gate exit pipeline + PQC-signed exit receipts in `exit_governance_receipts`. Emergency SL bypasses EGL. 44 tests.
- **Pipeline**: Entry governance = 8 checkpoints (CP-0 SIV through CP-8 ECW). Exit governance = 3 gates (EGL).
- **ADR count**: 40 (ADR-001 → ADR-040)

### Public Governance Sandbox — "Try OMNIX" (Mar 15, 2026)
- **ESTADO**: ✅ COMPLETADO — ADR-040
- **Ruta**: `/try` (público, sin autenticación)
- **Flujo**: Texto libre (EN/ES, max 500 chars) → Gemini AI → 8 señales → Pipeline REAL 8 checkpoints → Receipt PQC-firmado → Verificable en Railway `/verify/{receipt_id}`
- **Fail-closed**: Si receipt falla, evaluación retorna 500
- **Archivos**: `omnix_dashboard/blueprints/public_sandbox.py`, `omnix_web/src/pages/PublicGovernanceSandbox.tsx`
- **DOCUMENTACIÓN**: [ADR-040](reference/adr/ADR-040-public-governance-sandbox.md)

### Insurance Domain Pilot — Multi-Domain Extensibility Validated (Mar 1, 2026)
- **ESTADO**: ✅ COMPLETADO - ADR-030 + 3 PQC-signed receipts reales
- **Evidencia**: 3 escenarios reales vía External Governance API — AUTO-POL-2847 (APPROVED), AUTO-POL-9999 (BLOCKED 6/6), LIFE-POL-4521 (BLOCKED 2/6)
- **Receipt IDs**: `OMNIX-AB1D878EC56A` · `OMNIX-B5782882E993` · `OMNIX-C23154E3D1B0`
- **Domain Adapter**: `docs/reference/domain-adapters/insurance-domain-adapter.md`
- **Posicionamiento**: "OMNIX governance engine validated across 3 domains — trading (699K+ cycles) + insurance (real receipts) + HealthTech (framework)"
- **DOCUMENTACIÓN**: [ADR-030](reference/adr/ADR-030-insurance-domain-pilot.md)

### Multi-Vertical Governance Architecture (Feb 15, 2026)
- **ESTADO**: ✅ COMPLETADO - ADR-026 + 2 Interactive Demos
- **ADR-026**: Documenta arquitectura Domain Adapter para expansión multi-vertical del motor de gobernanza
- **Credit Demo**: Página interactiva en `/governance-demo` — 6 checkpoints aplicados a decisiones de crédito/préstamo
- **Insurance Demo**: Página interactiva en `/governance-demo-insurance` — 6 checkpoints aplicados a underwriting de seguros (BIND/REFER/DECLINE)
- **Patrón**: Domain Adapter + Normalized Governance Signals — misma arquitectura de 6 checkpoints, diferentes señales por dominio
- **Navegación**: Links añadidos desde CommercialLanding, InstitutionalPage, y entre demos
- **DOCUMENTACIÓN**: [ADR-026](reference/adr/ADR-026-multi-vertical-governance-architecture.md)

### CRITICAL FIX - Gemini Model Migration (Feb 7, 2026)
- **ESTADO**: ✅ DESPLEGADO - Migración de modelo AI deprecado
- **PROBLEMA**: Google deprecó `gemini-2.0-flash-exp` (retirement March 31, 2026), causando fallo total de AI ("System busy")
- **SOLUCIÓN**:
  - Actualizado TODAS las instancias de `gemini-2.0-flash-exp` → `gemini-2.5-flash` (modelo estable GA)
  - 6 archivos actualizados: settings.py, ai_models.py, conversational_ai_adapter.py, community_analyzer.py, advanced_intelligence.py, enterprise_bot.py
  - Cadena de fallback: Gemini 2.5 Flash (primary) → GPT-4o → Claude Sonnet 4
- **OpenAI Key Validator**: Relajado de `startswith('sk-') and len > 40` a `len > 20` para soportar nuevos formatos
- **AI Startup Diagnostics**: Log de resumen al inicio mostrando modelos disponibles y cadena de fallback

### AI Response Speed Optimization (Jan 30, 2026)
- **ESTADO**: ✅ DESPLEGADO - Optimización de velocidad de respuesta AI
- **PROBLEMA**: Timeout de OpenAI a 15s causando respuestas incompletas
- **SOLUCIÓN**:
  - Timeout aumentado a 30s (OpenAI, Gemini, Anthropic)
  - GPT-4o-mini fast path para consultas simples (3x más rápido)
  - Selección inteligente: simples → 4o-mini, complejas → 4o
  - Validación relajada para respuestas cortas (10 chars vs 50)
- **DOCUMENTACIÓN**: [2026-01-30-ai-speed-optimization.md](history/2026-01/2026-01-30-ai-speed-optimization.md)

### ECW Calibration v1.1 (Jan 29, 2026)
- **ESTADO**: ✅ ACTIVO - Reducción de umbral MC_WR de 52% a 50%
- **PROPÓSITO**: Permitir trades en mercados con edge marginal
- **ENV-CONFIGURABLE**: `ECW_MC_WR_MIN=52` para rollback
- **DOCUMENTACIÓN**: [2026-01-29-ecw-calibration.md](history/2026-01/2026-01-29-ecw-calibration.md)

### Sitio Web Institucional Lanzado (Jan 28, 2026)
- **ESTADO**: ✅ OPERATIVO - Landing page institucional en Puerto 5000
- **STACK**: React 18 + TypeScript + Vite + Tailwind CSS
- **CARACTERÍSTICAS**:
  - Hero con estadísticas animadas (Cycles, Vetos, Capital Preserved)
  - Visualización 4-Layer Validation Architecture
  - Track Record Transparency (Learning Baseline vs Official)
  - Live Market Data (CoinGecko, Alternative.me)
  - Risk Calculator tool
  - Pricing: B2C SaaS ($49-$499/mo) + B2B Enterprise ($10K-$100K+)
  - Certifications: NIST FIPS 203/204 (Implemented), ADGM (Target), Sharia (In Development)
- **DOCUMENTACIÓN**:
  - [WEB_INFRASTRUCTURE.md](current/WEB_INFRASTRUCTURE.md) - Arquitectura multi-puerto
  - [omnix_web/README.md](../omnix_web/README.md) - Documentación técnica

### Shadow Portfolio Runner Activado (Jan 27, 2026)
- **ESTADO**: ✅ ACTIVADO - Análisis contrafactual operativo
- **PROPÓSITO**: Validar que los vetos del sistema fueron correctos usando precios históricos reales
- **TABLAS**:
  - `shadow_trade_events`: 670,000+ eventos capturados
  - `shadow_trade_outcomes`: 50+ procesados (100% accuracy)
- **FIX APLICADO**: Timezone bug (`datetime.utcnow()` → `datetime.now(timezone.utc)`)
- **EJECUCIÓN**: `python -m omnix_services.database_service.shadow_portfolio_runner --max-events 500`
- **RUNBOOKS**:
  - [RUNBOOK_SHADOW_PORTFOLIO.md](operations/RUNBOOK_SHADOW_PORTFOLIO.md) - Operación del runner
  - [RAILWAY_SHADOW_PORTFOLIO_CRON.md](operations/RAILWAY_SHADOW_PORTFOLIO_CRON.md) - Configuración cron Railway
- **RESULTADOS INICIALES**:
  - BLACK_SWAN vetos: 100% accuracy
  - COHERENCE_GATE vetos: 100% accuracy
  - Total validados: 50/50 correctos

### ADR-022: Post-Quantum Cryptography Status (Jan 23, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - PQC operativo desde Nov 2025
- **CRÍTICO**: PQC YA ESTÁ IMPLEMENTADO - NO es roadmap. La IA no debe decir "PQC planificado para Q3 2026"
- **ALGORITMOS**:
  - Kyber-768 (ML-KEM-768) - NIST FIPS 203 - Encriptación
  - Dilithium-3 (ML-DSA-65) - NIST FIPS 204 - Firmas digitales
- **INTEGRACIÓN**: Órdenes de trading firmadas con Dilithium-3 antes de ejecución
- **NIVEL SEGURIDAD**: NIST Level 3 (~192-bit classical security)
- **ARCHIVOS**: `omnix_core/security/pqc_security.py`, `omnix_config/system_state_manifest.json`
- **REFERENCIA**: `docs/reference/adr/ADR-022-post-quantum-cryptography.md`

### ADR-021: Shadow Trade Metrics View (Jan 22, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - VIEW SQL para parsing de decision_trace + Dashboard
- **PROBLEMA**: Análisis retroactivo de DCI requería extraer métricas de decision_trace JSONB
- **SOLUCIÓN**: VIEW `v_shadow_trade_metrics` con regex parsing:
  - `mc_win_rate`: Monte Carlo Win Rate %
  - `mc_expected_return`: Monte Carlo Expected Return %
  - `coherence_score`: Coherence Engine Score %
  - `ecw_cycles`: ECW cycles (0-3)
  - `ecw_status`: WAITING / OPEN
  - `black_swan_severity`: LOW / MEDIUM / HIGH / EXTREME
  - `approx_dci`: DCI aproximado (0-100)
- **DISEÑO**: VIEW (no tabla física) - zero risk, 100% reversible
- **DATOS**: 76,910+ eventos parseados desde Jan 15, 2026
- **DASHBOARD**: Nueva página "Shadow Analytics" en Streamlit con:
  - Block A: 4 KPIs (Total Events, Avg WR, Avg Coherence, % ECW Blocked)
  - Block B: Charts (WR histogram, Coherence by Symbol, Coherence vs DCI scatter)
  - Block C: Governance tables (ECW waiting, Low coherence, Top vetos)
  - Disclaimer institucional sobre data source
- **REFERENCIA**: `docs/reference/adr/ADR-021-shadow-trade-metrics-view.md`

### ADR-020: Institutional Response Quality Standards (Jan 21, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - Filtros de calidad para respuestas de inversores
- **PROBLEMA**: Respuesta de bot incluía cifras infladas ($82M), umbrales irreales (WR 60%), lenguaje arbitrario ("ignorar módulos")
- **SOLUCIÓN**: Sistema multi-capa de calidad de respuestas:
  - **Layer 1 - Post-Processing**: Blacklist de cifras infladas, reemplazos de lenguaje institucional
  - **Layer 2 - Prompt Rules**: RULE 15 con umbrales realistas (ADR-018) y criterio ECW (ADR-019)
  - **Layer 3 - Prohibiciones**: "Es difícil cuantificar" bloqueado, fórmula explícita requerida
- **UMBRALES REALISTAS**: WR ≥52%, ER >0%, DCI <70, Black Swan ≤MEDIUM, 3 ciclos consecutivos
- **FÓRMULA**: `Pérdida Evitada = Position_Size × max(VaR95, Historical_Avg_Loss)`
- **ARCHIVOS**: `omnix_services/ai_service/conversational_ai_adapter.py`, `prompt_templates.py`
- **REFERENCIA**: `docs/reference/adr/ADR-020-institutional-response-quality.md`

### ADR-019: Edge Confirmation Window (ECW) (Jan 21, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - Gate de confirmación de edge persistente
- **PROBLEMA**: Sistema ejecutaba en edge momentáneo sin confirmar persistencia
- **SOLUCIÓN**: Requiere 3 ciclos consecutivos con WR≥52%, ER>0%, BS≤MEDIUM antes de ejecutar
- **FLUJO**: MC VETO → RMS VETO → COHERENCE GATE → [ECW GATE] → Scoring → Decision
- **ARCHIVOS**: `omnix_core/bot/auto_trading_bot.py`, `omnix_config/system_state_manifest.json`
- **REFERENCIA**: `docs/reference/adr/ADR-019-edge-confirmation-window.md`

### ADR-018: Decision Contradiction Index (DCI) (Jan 21, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - Shadow metric observacional
- **PROBLEMA**: Inversores preguntaban "si había señal BUY fuerte, ¿por qué no entró?"
- **SOLUCIÓN**: DCI mide contradicción interna entre señales locales y edge global:
  - Local Signal Strength (0-40 pts): promedio Non-Markovian + EMA
  - Global Edge Penalty (0-30 pts): inverso de calidad MC_ER/WR
  - Regime Penalty (0-15 pts): VOLATILE/RANGING penalizado
  - Risk Overlay (0-15 pts): severidad Black Swan
- **OUTPUT**: Score 0-100, Niveles: ALIGNED (<35) / TENSIONED (35-69) / CONTRADICTORY (≥70)
- **MODO**: Shadow only - NO afecta decisiones de trading
- **VALIDACIÓN**: Day 9 análisis de correlación con win rate
- **ARCHIVOS**: `omnix_core/bot/auto_trading_bot.py`
- **REFERENCIA**: `docs/reference/adr/ADR-018-decision-contradiction-index.md`
- **ANÁLISIS**: `docs/investigations/DCI_ANALYSIS.md`

### ADR-017: FINAL_DECISION_REASON Summary (Jan 21, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - Bloque consolidado de razón de decisión
- **PROBLEMA**: Rationale de decisiones disperso en múltiples líneas de log
- **SOLUCIÓN**: Bloque estructurado consolidando signals, edge, regime, risk, coherence, action
- **REFERENCIA**: `docs/reference/adr/ADR-017-final-decision-reason-summary.md`

### ADR-016: Log Semantics & Decision Clarity (Jan 21, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - Etiquetas semánticas mejoradas
- **CAMBIOS**: Kelly skip label, DecisionConf/CoherenceScore rename, BYPASSED gate text
- **REFERENCIA**: `docs/reference/adr/ADR-016-log-semantics-decision-clarity.md`

### ADR-015: Dashboard Security Enhancement (Jan 21, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - Basic Auth + Rate Limiting + Security Headers
- **PROBLEMA**: Dashboard sin autenticación (calificación C+ en auditoría de seguridad)
- **SOLUCIÓN**: Middleware de seguridad centralizado:
  - Basic HTTP Authentication con env vars (DASHBOARD_USER, DASHBOARD_PASSWORD)
  - Rate limiting por IP (60 req/min configurable via DASHBOARD_RATE_LIMIT)
  - IP allowlist opcional (DASHBOARD_IP_ALLOWLIST)
  - Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
  - Endpoints exentos: /api/health, /static/*, /favicon.ico
- **ARCHIVOS**: `omnix_dashboard/utils/auth.py`, `omnix_dashboard/app.py`
- **REFERENCIA**: `docs/reference/adr/ADR-015-dashboard-security.md`

### ADR-014: Provider Resilience Enhancement (Jan 20, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - Mejoras TYPE_C basadas en feedback de inversores
- **PROBLEMA**: Respuestas sobre proveedores calificadas 7/10 por inversores sofisticados
- **GAPS IDENTIFICADOS**:
  - Fallos silenciosos no cubiertos (timeouts ≠ datos corruptos)
  - Cross-validation sin umbrales concretos
  - Single-tenant no resuelve fuentes compartidas corruptas
  - Falta transparencia sobre limitaciones residuales
- **SOLUCIÓN**: TYPE_C override mejorado con:
  - Validación de timestamps (>60s = stale data)
  - Cross-validation con umbrales (>3% discrepancia = pausa)
  - Sanity checks de volumen (10x promedio = anomalía)
  - Honestidad sobre limitación single-tenant
  - Riesgo residual + fail-closed + intervención humana
  - Roadmap: oráculos blockchain (Chainlink, Band Protocol)
- **SCORE ESPERADO**: 7/10 → 9/10
- **REFERENCIA**: `docs/reference/adr/ADR-014-provider-resilience-enhancement.md`

### ADR-013: Systemic Framing Router (Jan 19, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - Routing determinístico de preguntas sistémicas
- **PROBLEMA**: Bot usaba misma apertura ("no genera señales sincronizadas") para TODAS las preguntas sistémicas
- **SOLUCIÓN**: Clasificador determinístico con 4 tipos de riesgo sistémico:
  - **TYPE_A (Coordination)**: Señales sincronizadas, venta masiva → "OMNIX no genera señales sincronizadas..."
  - **TYPE_B (Software)**: Defectos de código, bugs, despliegue → "OMNIX implementa múltiples capas de defensa..."
  - **TYPE_C (Dependencies)**: Proveedores, APIs, datos → "OMNIX valida cada fuente de datos..."
  - **TYPE_D (Governance)**: Reguladores, compliance, auditorías → "Desde perspectiva de gobernanza..."
- **PRIORIDAD**: A > D > C > B (para preguntas que coinciden con múltiples tipos)
- **TESTS**: 23 tests en `tests/test_systemic_router.py`
- **REFERENCIA**: `docs/reference/adr/ADR-013-systemic-framing-router.md`

### ADR-012: Learning Baseline Freeze & Official Day 1 (Jan 15, 2026)
- **ESTADO**: ✅ ADOPTADO - Day 1 oficial declarado
- **DECLARACIÓN**: 15 de Enero 2026 = Day 1 del track record oficial
- **LEARNING BASELINE**: Nov 2025 - Jan 14, 2026 (119 trades, LEGACY_ESTIMATED)
- **TRACK RECORD OFICIAL**: Jan 15, 2026+ (telemetría REAL)
- **MÉTRICAS RESET**: Trade count, win rate, profit factor (desde Day 1)
- **MÉTRICAS CARRY-OVER**: Balance ($984K), capital preservation (98.5%), config
- **DAY 30 REVIEW**: 13 de Febrero 2026 (meta: 100 trades, WR >45%)
- **REFERENCIA**: `docs/reference/adr/ADR-012-learning-baseline-freeze.md`

### ADR-011: Legacy Telemetry Backfill (Jan 15, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - Data Quality corregido
- **PROBLEMA**: 119 trades sin coherence_score ni hmm_regime (pre-telemetría)
- **SOLUCIÓN**:
  - Track A: Backfill estimado basado en profit_pct/profit_loss
  - Track B: Columna `telemetry_source` (LEGACY_ESTIMATED vs REAL)
  - Track C: Métrica segmentada en Health Score
- **RESULTADO**: Data Quality 25% → 100% (con telemetría estimada marcada)
- **REFERENCIA**: `docs/reference/adr/ADR-011-legacy-telemetry-backfill.md`

### ADR-010: Capital Protection Metric Standard (Jan 15, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - Métricas unificadas
- **PROBLEMA**: Inconsistencia entre "$1.2B Protected" vs "$267K Avoided"
- **SOLUCIÓN**: Sistema de dos métricas:
  - Primaria: "Est. Loss Avoided*" = Notional × 0.6%
  - Secundaria: "Notional Blocked" (transparencia)
- **WIDGETS ACTUALIZADOS**: quarantine.js, learninginsights.js, regimedetection.js, streamlit_app.py
- **REFERENCIA**: `docs/reference/adr/ADR-010-capital-protection-metric-standard.md`

### ADR-008: Opportunity Tracker (Jan 14, 2026)
- **ESTADO**: ✅ ADOPTADO - Framework de validación Day 30
- **PROPÓSITO**: Documentar oportunidades perdidas vs pérdidas evitadas sin cambiar thresholds
- **MÉTRICAS**:
  - Missed Opportunities: Trades bloqueados con buenas condiciones (Coh >50%, RANGING)
  - Losses Avoided: Trades correctamente bloqueados (Coh <30%, VOLATILE)
  - Net Opportunity: Balance diario para decisión data-driven
- **CRITERIO DAY 30**: Si missed > 20 AND profit > $3K → Test threshold 35%
- **FECHA REVISIÓN**: 13 de Febrero 2026
- **REFERENCIA**: `docs/reference/adr/ADR-008-opportunity-tracker.md`

### ADR-007: Coherence Threshold Calibration (Jan 14, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - V6.5.4e
- **DIAGNÓSTICO**: Sistema sobre-protector bloqueando 48,937 trades en 7 días ($978.7M bloqueados)
- **CAUSA RAÍZ**: COHERENCE_GATE promedio 26.3% coherencia, BLACK_SWAN bloqueando 21,402 señales
- **SOLUCIÓN Phase 1**: Reducción de 5 puntos en umbrales adaptativos
  - LOW: 35% → 30%, MEDIUM: 45% → 40%, HIGH: 55% → 50%, EXTREME: 65% → 60%
  - EMA trigger: 25 → 20 puntos
- **IMPACTO ESPERADO**: Tasa de veto -15-20%, Win rate 37.8% → 42-45%
- **GUARDRAIL**: Rollback si drawdown > 3% en 48h
- **REFERENCIA**: `docs/reference/adr/ADR-007-coherence-threshold-calibration.md`

### ADR-006: Dashboard Improvement Proposals (Jan 13, 2026)
- **ESTADO**: Documentado, pendiente implementación
- **ANÁLISIS EXTERNO**: Dashboard evaluado en 7.5/10, objetivo 9.5/10
- **BUGS CRÍTICOS IDENTIFICADOS**:
  - WR Dir muestra 0.0% en Trade History (debería ser 37.8%)
  - Fee Eroded muestra 0 (debería ser 21)
  - "Protected" es métrica engañosa (renombrar a "Notional Blocked")
- **MEJORAS UX PROPUESTAS**:
  - System Health Score (indicador visual 0-100)
  - Live Status (qué hace el sistema ahora)
  - Quick Insights (insights auto-generados)
  - Calibration Progress (barra de progreso)
- **DOCUMENTACIÓN**:
  - ADR: `docs/reference/adr/ADR-006-dashboard-improvement-proposals.md`
  - Backlog: `docs/DASHBOARD_IMPROVEMENT_BACKLOG.md`
  - Auditoría: `docs/compliance/audits/DASHBOARD_UX_AUDIT_JAN13_2026.md`

### ADR-004: Position Sizing Hotfix (Jan 12, 2026)
- **ESTADO**: ✅ IMPLEMENTADO (27 tests pasados)
- **PROBLEMA DETECTADO**: Kelly operaba con max_position=20% ($62,500), cayendo en rango de trades que pierden
- **EVIDENCIA EMPÍRICA**:
  - Trades <$1K: **55.56% WR** → RENTABLES
  - Trades >$10K: **31% WR** → PIERDEN
- **HOTFIXES PROPUESTOS**:
  - Kelly max_position: 20% → **2%** ($62,500 → $20,000)
  - Position Hard Cap: **$20,000** máximo por trade
  - Spread mínimo: 5 bps → 25 bps
- **REFERENCIA**: `docs/reference/adr/ADR-004-position-sizing-hotfix.md`

### Dual Win Rate Framework - Dashboard UI Update (Jan 12, 2026)
- **INVESTIGACIÓN**: Descubierto que 21 trades ganaron en dirección pero perdieron por fees de Kraken (~0.26%)
- **DOS MÉTRICAS**:
  - **Precisión (37.82%)**: % de trades donde el precio se movió en la dirección predicha (pnl_percent > 0)
  - **Rentable (20.17%)**: % de trades rentables después de comisiones (profit_loss > 0)
- **UI ACTUALIZADA**:
  - Terminal Header: Muestra "Precisión" y "Rentable" con tooltips explicativos en español
  - Trade History Widget: Muestra ambos win rates + contador de "Fee Eroded" trades
  - Streamlit Overview: 5 columnas con ambas métricas y tooltips explicativos
- **FEE EROSION**: 21 trades identificados que acertaron dirección pero perdieron a fees
- **MITIGACIÓN**: Cap de $1,000 implementado para reducir impacto de fees en trades pequeños
- **ALINEACIÓN ADR-002**: Ambas métricas visibles con contexto claro (Honest Framing)
- **DOCUMENTACIÓN**: Ver `docs/investigations/TRADE_INVESTIGATION_JAN2026.md` para análisis completo

### Official Positioning & Language Guide (Jan 10, 2026)
- **ADR-003**: OMNIX officially positioned as "Decision Governance Infrastructure for Automated Systems" (updated by ADR-027)
- **NEW DOCUMENT**: `docs/reference/omnix_official_language.md` - Complete language guide
- **TWO RESPONSE MODES**: 
  - Mode 1 (Positioning): Lead with architecture/preservation for general inquiries
  - Mode 2 (Honest Metrics): Show all data when specifically asked
- **KPI HIERARCHY**: Capital Preservation > Risk Events Blocked > System Integrity > Win Rate
- **Combined with ADR-002**: Honest Framing ensures transparency when metrics requested

### Daily Report Service - Brutal Honesty Monitoring (Jan 9, 2026)
- **NUEVO SERVICIO**: `DailyReportService` para monitoreo diario con honestidad brutal
- **MÉTRICAS REALES**: Conectado a PostgreSQL para win rate, balance, P&L reales
- **TABLA**: `paper_trading_daily_reports` para historial de auditoría
- **TELEGRAM**: Comando `/reporte_diario` para generar reporte
- **KELLY HONESTO**: Muestra "Modo Aprendizaje" cuando Kelly es negativo con tracking de costo
- **ADR**: `docs/reference/adr/ADR-001-brutal-honesty-monitoring.md`
- **RUNBOOK**: `docs/operations/runbooks/daily_monitor_report.md`

### Balance Precision Correction (Jan 10, 2026)
- **BALANCE CORREGIDO**: $984,188.74 → $984,801.27 (+$612.53 precisión)
- **P&L CORREGIDO**: -$19,848.65 → -$15,198.73 (suma real de 119 trades)
- **ROI CORREGIDO**: -1.98% → -1.52%
- **VERIFICADO**: Balance = $1M + P&L = $984,801.27 (diferencia $0.00)
- **AUDIT LOG**: Registrado en `balance_history` y `DATA_INTEGRITY_AUDIT_JAN2026.md`

### Data Integrity Audit Remediation (Jan 9, 2026)
- **BALANCE CORREGIDO**: $880,918 → $984,188.74 (gap de $103K resuelto)
- **WIN RATE CORREGIDO**: 37.8% → 20.17% (criterio: profit_loss > 0)
- **COHERENCE GATE FIX**: Removida condición CRITICAL que bloqueaba trades válidos
- **AUDIT REPORT**: `docs/compliance/audits/DATA_INTEGRITY_AUDIT_JAN2026.md`

### Shadow Portfolio + Cron Job + Dashboard Widget (Jan 9, 2026)
- **SHADOW PORTFOLIO COMPLETE**: Sistema de análisis contrafactual de trades bloqueados
- **CRON JOB**: `scripts/operations/run_shadow_portfolio.sh` para Railway (05:00 UTC diario)
- **DASHBOARD WIDGET**: Nueva pestaña "Shadow Portfolio" en Streamlit con:
  - Accuracy por tipo de veto (gráfico de barras)
  - Top missed opportunities (trades rentables bloqueados)
  - Recomendaciones de calibración de filtros
- **RUNBOOKS ACTUALIZADOS (Jan 27, 2026)**:
  - [RUNBOOK_SHADOW_PORTFOLIO.md](operations/RUNBOOK_SHADOW_PORTFOLIO.md) - Operación completa
  - [RAILWAY_SHADOW_PORTFOLIO_CRON.md](operations/RAILWAY_SHADOW_PORTFOLIO_CRON.md) - Cron job Railway
- Ver [REAL_SYSTEM_STATUS.md](REAL_SYSTEM_STATUS.md) para detalles

### Veto Tracking System + psycopg v3 Fix (Jan 7, 2026)
- **SISTEMA VETO TRACKING**: Persistencia real de capital protegido en PostgreSQL
- **FIX psycopg v3**: VetoRepository ahora compatible con `psycopg[binary]` (v3) y fallback a psycopg2
- **Dashboard Metrics Fix**: Panel superior ahora muestra ALL trades (119), no solo últimos 30 días
- Ver [REAL_SYSTEM_STATUS.md](REAL_SYSTEM_STATUS.md) para detalles completos

### Telegram Voice Service Fix (Dec 31, 2025)
- **ERROR CORREGIDO**: `UnboundLocalError: cannot access local variable 'asyncio'`
- **CAUSA RAÍZ**: Imports condicionales de `asyncio` dentro de `if`/`try` causaban conflictos de scope
- **FIX**: Eliminados 3 imports redundantes (líneas 3545, 4835, 6489) de `enterprise_bot.py`
- **REGLA**: Solo un `import asyncio` global (línea 10) - nunca imports condicionales
- Ver [REAL_SYSTEM_STATUS.md](REAL_SYSTEM_STATUS.md) para detalles

### Type Safety Hotfix - Coherence Engine (Dec 30, 2025)
- **ERROR CORREGIDO**: `">= not supported between instances of 'str' and 'int'"` en Coherence Gate
- **NUEVAS FUNCIONES**:
  - `normalize_signal()` - Convierte strings "BUY"/"SELL" a Enum Signal
  - `normalize_strategy_signal()` - Normaliza StrategySignal completo (signal→Enum, confidence→float)
- **BLINDAJE safe_float()** en todas las comparaciones >= de CoherenceEngine
- **16 tests nuevos** en `tests/test_coherence_type_safety.py`
- **Total tests Dec 30**: 43 (27 críticos + 16 type safety)
- Ver [TYPE_SAFETY_HOTFIX_DEC30_2025.md](history/2025-12/TYPE_SAFETY_HOTFIX_DEC30_2025.md) para detalles

### Critical Audit Fixes + ENV Control (Dec 30, 2025)
- **AUDITORÍA CRÍTICA COMPLETADA**: 4 fixes de seguridad implementados
  - Coherence Gate ahora FAIL-CLOSED (excepciones → BLOCKED)
  - MC Veto semántica corregida: ER<0% → BLOCKED, WR<50% → SIZE_REDUCE
  - DecisionPayload extendido con campos de auditoría
- **TRACK_RECORD_MODE controlado por ENV** (default=false)
  - Rollback sin redeploy: `TRACK_RECORD_MODE=true` en Railway Variables
- **27/27 tests pasando** incluyendo verificación de código fuente
- **Campos de auditoría** en cada decisión: `track_record_mode`, `low_vol_mode`
- Ver [REAL_SYSTEM_STATUS.md](REAL_SYSTEM_STATUS.md) para detalles completos

### V1.0.5 - OHLC Data Fix (Dec 26, 2025)
- **CRÍTICO**: `generate_signal()` nunca se ejecutaba porque `prices=0`
- **Root Cause**: `TradingServiceEnterprise` faltaba método `get_ohlc()` delegado
- **Fix**: Añadido método delegado que reenvía a `self.kraken.get_ohlc()`
- **Resultado**: EMA Signal ahora puede generar señales reales
- Ver [REAL_SYSTEM_STATUS.md](REAL_SYSTEM_STATUS.md) para detalles completos

### Multi-User Phase 3b COMPLETADA (Dec 22, 2025)
- **AuthorizationService INTEGRADO** en 5 archivos con RBAC completo
- **17 hardcoded checks reemplazados** con verificación de permisos
- **5 roles B2C SaaS**: FREE < BASIC < PRO < PREMIUM < OWNER
- **15 permisos granulares** para trading, análisis, alertas
- **Harold = OWNER** en BD con paper trading activo
- **39/39 authorization tests passing**
- **Documento**: [MULTI_USER_ARCHITECTURE.md](current/MULTI_USER_ARCHITECTURE.md) - Guía completa de uso

### Language Detection AI-First (Dec 22, 2025)
- **ELIMINADOS** diccionarios hardcodeados de detección de idioma
- **INSTALADO** `fast-langdetect` (FastText-based, 80x más rápido)
- **FLUJO**: Textos largos (≥50 chars) → FastText | Textos cortos (<50 chars) → Gemini AI
- **MAPEO gTTS**: ISO codes a códigos gTTS válidos (ej: zh → zh-CN)
- **12/12 tests pasando**

### Nuevos Componentes Hexagonales (Dec 22, 2025)
| Componente | Ubicación |
|------------|-----------|
| `AuthorizationPort` | `src/omnix/ports/driven/authorization_port.py` |
| `AuthorizationAdapter` | `src/omnix/infrastructure/adapters/authorization_adapter.py` |
| `UserSessionPort` | `src/omnix/ports/driven/user_session_port.py` |
| `UserSessionAdapter` | `src/omnix/infrastructure/adapters/user_session_adapter.py` |

### AI-First Multilingual Concurrency (Dec 19, 2025)
- **Detección de idioma segura para concurrencia**: `threading.Lock` + `asyncio.to_thread()`
- **Persistencia Redis por usuario**: `omnix:user_language:{chat_id}` con TTL 24h
- **Placeholders universales en inglés**: AI genera respuestas localizadas

---

## Navegación Rápida

### Estado Actual
| Documento | Descripción |
|-----------|-------------|
| [Migración V7.0](MIGRATION_STATUS.md) | Estado de arquitectura hexagonal (20 ports, 22 adapters, 0% activación) |
| [Estado REAL](REAL_SYSTEM_STATUS.md) | **FUENTE DE VERDAD** - Estado de producción Railway |
| [Hexagonal Status](current/HEXAGONAL_MIGRATION_STATUS.md) | Detalle técnico de ports y adapters |
| [Mapa Funcional](current/COMPLETE_FUNCTIONALITY_MAP.md) | Sistema legacy (11 dominios, 346 archivos) |
| [Multi-Usuario](current/MULTI_USER_ARCHITECTURE.md) | **CRÍTICO** - Auditoría y plan multi-tenant |

### Sitio Web Público (Jan 28, 2026)
| Documento | Descripción |
|-----------|-------------|
| [Web Infrastructure](current/WEB_INFRASTRUCTURE.md) | **NUEVO** - Arquitectura multi-puerto (5000, 8000, 8080) |
| [OMNIX Web README](../omnix_web/README.md) | Landing page institucional (React + Vite) |

**Sitio Web Institucional**: Landing page para inversores con estadísticas en tiempo real, arquitectura de 4 capas, track record transparente, y precios B2C/B2B.

### Operaciones
| Documento | Descripción |
|-----------|-------------|
| [Deployment](operations/DEPLOYMENT.md) | Guía Railway |
| [Runbooks](operations/) | Runbooks de activación de ports |
| [Trading Operations](current/TRADING_OPERATIONS.md) | Perfiles y risk management |

### Inversores
| Documento | Descripción |
|-----------|-------------|
| [Executive Fact Sheet](business/EXECUTIVE_FACT_SHEET.md) | Day 1 oficial - documento institucional |
| [Risk Mitigation Log](business/investor/risk_mitigation_log.md) | Eventos de protección de capital (Day 1-4) |
| [OMNIX vs Market](business/investor/omnix_vs_market.md) | Comparativa Alpha vs Beta |
| [Shadow Performance](business/investor/shadow_performance_report.md) | Análisis contrafactual de trades vetados |
| [4-Layer Architecture](business/investor/architecture_4_layers.md) | Arquitectura de seguridad para Hub71 |
| [One Pager](business/investor/one_pager.md) | Resumen ejecutivo |
| [Proyecciones](business/investor/financial_projections.md) | Forecast financiero |
| [Pitch Deck Hub71](business/PITCH_DECK_HUB71.md) | Presentación para Hub71 |

### Referencia Técnica
| Documento | Descripción |
|-----------|-------------|
| [Trazabilidad](reference/TRACEABILITY_MATRIX.md) | 123 componentes mapeados |
| [ADR-001](reference/adr/ADR-001-hexagonal.md) | Decisión hexagonal |
| [ADR-004](reference/adr/ADR-004-position-sizing-hotfix.md) | Position sizing hotfix |
| [ADR-007](reference/adr/ADR-007-coherence-threshold-calibration.md) | Coherence threshold calibration |
| [ADR-008](reference/adr/ADR-008-opportunity-tracker.md) | Opportunity Tracker (Day 30 Review) |
| [ADR-009](reference/adr/ADR-009-brevity-first-policy.md) | Brevity First - Respuestas directas |
| [Deuda Técnica](current/TECHNICAL_DEBT.md) | Issues conocidos |

---

## Estructura de Carpetas

```
docs/
├── README.md                 <- Este archivo (índice)
├── REAL_SYSTEM_STATUS.md     <- Estado REAL de producción (fuente de verdad)
├── MIGRATION_STATUS.md       <- Estado V7.0 consolidado (arquitectura)
│
├── current/                  <- Documentos "vivos" (estado actual)
│   ├── HEXAGONAL_MIGRATION_STATUS.md  <- Ports/Adapters detallado
│   ├── COMPLETE_FUNCTIONALITY_MAP.md  <- Referencia sistema legacy
│   ├── TECHNICAL_DEBT.md              <- Issues conocidos
│   ├── TRADING_OPERATIONS.md          <- Operaciones de trading
│   ├── MULTI_USER_ARCHITECTURE.md     <- Auditoría multi-tenant
│   └── WEB_INFRASTRUCTURE.md          <- Arquitectura multi-puerto (Jan 28)
│
├── operations/               <- Runbooks y guías operativas
│   ├── DEPLOYMENT.md
│   ├── RUNBOOK_*_ACTIVATION.md        <- Runbooks por port
│   └── CONFIGURACION_OPTIMIZADA.md
│
├── reference/                <- Referencia técnica estática
│   ├── TRACEABILITY_MATRIX.md
│   └── adr/                           <- Architecture Decision Records
│
├── business/                 <- Documentos de negocio
│   ├── EXECUTIVE_FACT_SHEET.md        <- Day 1 oficial (institucional)
│   └── investor/                      <- Pitch deck, proyecciones
│
├── compliance/               <- Auditorías (solo actuales)
│   └── audits/
│
└── history/                  <- Archivo histórico (congelado)
    ├── 2025-11/                       <- Noviembre 2025
    └── 2025-12/                       <- Diciembre 2025
```

---

## Estado del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    OMNIX — Decision Governance Infrastructure     │
├─────────────────────────────────────────────────────────────────┤
│  PRODUCCIÓN (Railway)                                            │
│  ├── 100% código legacy operando 24/7                           │
│  ├── 0% arquitectura hexagonal activa                           │
│  └── Feature flags: TODOS en false                              │
├─────────────────────────────────────────────────────────────────┤
│  ARQUITECTURA V7.0 (Implementada, no activa)                    │
│  ├── 17 Driven Ports + 3 Driver Ports = 20 ports                │
│  ├── 22 Adapters implementados                                  │
│  ├── 164 tests totales (10 críticos en CI workflow)             │
│  └── Patrón: Strangler Fig (activación gradual)                 │
├─────────────────────────────────────────────────────────────────┤
│  INTERFACES                                                      │
│  ├── Telegram Bot (enterprise_bot.py)                           │
│  ├── Flask Dashboard (puerto 5000)                              │
│  └── Streamlit Dashboard (puerto 8080)                          │
├─────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                      │
│  ├── PostgreSQL (42+ tablas)                                    │
│  ├── Redis (cache + estado)                                     │
│  └── DatabaseGateway (connection pool)                          │
├─────────────────────────────────────────────────────────────────┤
│  EXTERNAL APIs                                                   │
│  ├── Kraken (crypto)                                            │
│  ├── Gemini 2.0 Flash (AI)                                      │
│  └── Tavily (web search)                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Próximo Paso: Activación de Ports

| Paso | Flag | Estado |
|------|------|--------|
| 1 | `USE_AI_PORT=true` | PRÓXIMO - Riesgo bajo, tiene fallback |
| 2-12 | Resto de ports | Pendiente (ver MIGRATION_STATUS.md) |

Ver [MIGRATION_STATUS.md](MIGRATION_STATUS.md) para plan completo de activación.

---

## Track Record

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Trades | 119 | 500+ |
| Win Rate | 20.17% | 55%+ |
| P&L | -$15,811.26 | Positive |
| Timeline | - | 8-9 semanas |

**Meta**: Track record para $1M seed @ $11.5M pre-money.

---

*OMNIX — Decision Governance Infrastructure - Última actualización: Febrero 2026*
