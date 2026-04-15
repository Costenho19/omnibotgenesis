# OMNIX — Decision Governance Infrastructure - Changelog

Registro de cambios, correcciones y mejoras del sistema.
**Internal Build Reference**: 6.5.4e

---

## [2026-04-15] — Fix Crítico: Telegram Command Handlers + Double Init

### Problema
El path V7 del bot llamaba `app.updater.start_polling()` directamente, saltándose `enterprise_bot.start_polling()` donde se registran los ~50 handlers de comandos. El bot podía ENVIAR mensajes (auto-trading funcionaba) pero no podía RECIBIR ningún comando — ningún handler estaba conectado.

Adicionalmente, `main_entry.py` llamaba `telegram_adapter.start()` antes de `run_polling()`, inicializando la `Application` dos veces.

### Corrección

| Archivo | Cambio |
|---------|--------|
| `src/omnix/infrastructure/adapters/telegram_adapter.py` | `run_polling()` ahora siempre usa `enterprise_bot.start_polling()` — registra todos los handlers antes de iniciar el updater |
| `src/omnix/bootstrap/main_entry.py` | Eliminada llamada prematura a `telegram_adapter.start()` — `enterprise_bot.start_polling()` maneja su propia inicialización |

### Commits
- `a0fa97e8` — telegram_adapter.py: fix run_polling → enterprise_bot.start_polling()
- `d2334b8e` — main_entry.py: remove premature start() call

### Estado
- Bot en Railway responde a todos los comandos (`/start`, `/status`, `/auto_start`, `/evaluar`, etc.)
- Auto-trading sigue activo (XRP/USD paper trades)
- PAPER_MODE=TRUE sin cambios

---

## [2026-04-14] — ADR-085: Cross-Border Semantic Governance Framework

### Contexto
Objeción técnica identificada por Antonio Socorro: los recibos PQC eran criptográficamente correctos pero el bloque `jurisdiction_semantics` solo cubría 5 frameworks y no delimitaba explícitamente qué certifica el recibo vs. qué queda sujeto a interpretación local.

### Solución — 3 capas

**Capa 1 — 10 frameworks regulatorios, 6 regiones**
- EU AI Act, GDPR Art. 22, DORA, FATF R.10/16/20/29, UK FCA COBS 11.2 + SM&CR, US SEC Rule 15c3-5 + Reg SCI, MAS FEAT, UAE CBUAE 2024, SAMA 2023, FSB G20

**Capa 2 — `proof_scope` en cada recibo**
- `what_this_receipt_proves` — 5 ítems explícitos
- `what_this_receipt_does_not_claim` — 4 ítems (no reclama equivalencia semántica ni certificado de cumplimiento)
- `verifier_guidance` — instrucción a verificadores externos

**Capa 3 — `cross_jurisdiction_concordance`**
- Status: BROADLY_ALIGNED / ALIGNED_WITH_LOCAL_REPORTING_OBLIGATIONS / FULLY_ALIGNED
- `divergence_risk` cuantificado

### Bugs adicionales corregidos

| Bug | Corrección |
|-----|-----------|
| `trust_score` nunca llegaba a 1.0 — `jurisdiction_semantics` se computaba DESPUÉS del score | Ahora se computa antes → trust_score correcto hasta 1.0 |
| `gov_blueprint._load_engine()` usaba `importlib.util.spec_from_file_location()` → keypair diferente al del trust registry → verificación independiente siempre fallaba | Import directo `from omnix_engine.decision_receipt import DecisionReceiptEngine` |
| `verification_server.py` hardcodeado en puerto 8000 — Railway asigna `$PORT` dinámicamente → omnibotgenesis crasheaba | Lee `$PORT` del entorno (fallback 8000 para dev local) |
| `verification_server.py` sin ruta `/health` — Railway health check fallaba | Añadida ruta `GET /health` |
| `runtime.py` llamaba `execute_one()` (función inexistente) | Corregido a `execute_query()` |

### Archivos modificados
- `omnix_web/api/omnix_engine/receipt_to_vc.py` — `build_jurisdiction_semantics()`: 10 frameworks, proof_scope, concordance
- `omnix_web/api/omnix_engine/federated_trust.py` — trust_score fix (jurisdiction_semantics primero)
- `omnix_web/api/gov_blueprint.py` — `_load_engine()`: import directo
- `omnix_core/evidence/decision_receipt.py` — `_STABLE_SIGNING_KEYS` + `_init_keys()`
- `omnix_core/evidence/verification_server.py` — `$PORT` dinámico + ruta `/health`
- `src/omnix/bootstrap/main_entry.py` — `start_verification_server_task()` lee `$PORT`
- `src/omnix/bootstrap/runtime.py` — `execute_one` → `execute_query`

### Documentación
- `docs/adr/ADR-085-cross-border-semantic-governance.md` — ADR completo
- `docs/compliance/CROSS_JURISDICTION_GOVERNANCE.md` — documento institucional de referencia

---

## [2026-04-14] — nixpacks.toml + railway.json: Fix Crash omnibotgenesis en Railway

### Problema
El servicio `omnibotgenesis` en Railway crasheaba en startup. Dos causas:
1. `nixpacks.toml` ejecutaba npm durante la fase de build — innecesario para el bot Python
2. `railway.json` tenía startCommand incorrecto

### Corrección

| Archivo | Cambio |
|---------|--------|
| `nixpacks.toml` | `[phases.build] cmds=[]` — suprime npm; venv setup en `[phases.install]` |
| `railway.json` | `startCommand: ".venv/bin/python3 -u main.py"` |

### Regla permanente
`[phases.build] cmds=[]` en `nixpacks.toml` NUNCA debe eliminarse. Su ausencia reactiva npm y crashea el bot.

### Verificación
- XRP/USD COMPRA EJECUTADA confirmada en Telegram (paper trade)
- Bot 24/7 activo en Railway, PAPER_MODE=TRUE

---

## [2026-01-14] - ADR-007 Coherence Threshold Calibration

### Diagnóstico
Sistema sobre-protector bloqueando demasiados trades:
- 48,937 vetos en 7 días ($978.7M en capital notional bloqueado)
- COHERENCE_GATE promedio 26.3% coherencia
- BLACK_SWAN bloqueando 21,402 señales

### Solución Phase 1: Reducción de 5 puntos

| Umbral | Antes | Después |
|--------|-------|---------|
| LOW | 35% | 30% |
| MEDIUM | 45% | 40% |
| HIGH | 55% | 50% |
| EXTREME | 65% | 60% |
| EMA trigger | 25 pts | 20 pts |

### Impacto Esperado
- Tasa de veto: -15-20%
- Win rate: 37.8% → 42-45%
- Profit factor: 0.13 → 0.8-1.2

### Guardrails
- Rollback si drawdown > 3% en 48h
- Monitoreo vía Learning Engine widget

### Archivos Modificados
- `omnix_services/coherence_service/coherence_engine.py`
- `omnix_services/risk_management/memory_risk_adapter.py`

### Documentación
- `docs/reference/adr/ADR-007-coherence-threshold-calibration.md`
- Actualizados: replit.md, TRADING_OPERATIONS.md, REAL_SYSTEM_STATUS.md, DECISION_CONTRACT.md, feature_catalog.md

---

## [2025-12-24] - ARES Code Complete Removal & Scoring Simplification

### GPT Expert 3-Step Optimization

Per GPT Expert recommendations, the following changes were implemented:

**1. Coherence Thresholds Raised:**
| Threshold | Before | After |
|-----------|--------|-------|
| veto_critical | 25% | 35% |
| veto_normal | 40% | 50% |
| warning | 55% | 60% |
| good | 75% | 78% |

**2. Scoring Simplified to 5 Inputs:**
| Input | Weight | Role |
|-------|--------|------|
| EMA Regime Signal | 40 pts | PRIMARY DRIVER |
| HMM Regime | 25 pts | Core (up from 15) |
| Kalman Filter | 15 pts | Core |
| Non-Markovian Memory | 15 pts | Core (up from 12) |
| Kelly Criterion | 10 pts | Modifier |

Monte Carlo, Black Swan, Sentiment, Quantum Momentum converted to **veto/penalty layer** (no additive scoring).

**3. ARES Code Completely Removed:**
| Action | Detail |
|--------|--------|
| Code deleted | ~90 lines removed from auto_trading_bot.py |
| EMA weight | Increased 25 → 40 points (absorbed ARES weight) |
| Trace | `ARES_REMOVED: Code eliminated Dec 24, 2025` |

### Documentation Cleaned
All references to ARES removed from:
- Pitch decks (EN/ES)
- Architecture docs
- Trading operations
- Compliance/audit reports

### New Documentation
- `docs/current/DECISION_CONTRACT.md` - Formal decision rules for investor audits

---

## [2025-12-04] - Documentation Consolidation & Database Optimization

### Documentation Cleanup
| Action | File | Reason |
|--------|------|--------|
| DELETED | `scripts/README.md` | Empty placeholder |
| DELETED | `docs/core/PROJECT_STRUCTURE.md` | Duplicate of TECHNICAL_REFERENCE |
| DELETED | `docs/core/MIGRATION_GUIDE.md` | Covered by deployment docs |
| DELETED | `omnix_dashboard/ARCHITECTURE.md` | Duplicate of DASHBOARD_TECHNICAL_REFERENCE |
| DELETED | `omnix_testing/PREMIUM_VALIDATION_README.md` | Outdated V6.0, covered by README.md |

### Database Table Consolidation
| Table Dropped | Reason |
|---------------|--------|
| `circuit_breaker_states` | Duplicate of `circuit_breaker_status` |
| `risk_guardian_logs` | Duplicate of `risk_guardian_events` |
| `trading_history` | Duplicate of `paper_trading_trades` |

**Result:** 45 → 42 tables, 38 FKs (90% coverage)

### Legacy Code Cleanup
| Action | Location | Result |
|--------|----------|--------|
| DELETED | `omnix_core/models/` | Empty folder removed |
| DELETED | `omnix_core/queue/` | Empty folder removed |
| DELETED | `omnix_services/trading_service/pqc_security.py` | 162-line duplicate removed |
| FIXED | `omnix_core/strategies/__init__.py` | Added exports |
| FIXED | `omnix_core/security/__init__.py` | Added exports |
| FIXED | `omnix_services/__init__.py` | Added exports |

### Dependency Updates
| Package | Old | New | Risk |
|---------|-----|-----|------|
| anthropic | 0.51.0 | 0.75.0 | LOW |
| python-telegram-bot | 20.7 | 21.9 | LOW |
| psycopg | 3.2.4 | 3.3.1 | LOW |
| pandas | 2.2.2 | 2.2.3 | LOW |
| scipy | 1.14.0 | 1.14.1 | LOW |
| ccxt | 4.4.35 | 4.5.24 | MEDIUM |
| httpx | 0.27.0 | 0.27.2 | LOW |

### References Updated
- `docs/README.md` - Fixed table counts (45→42)
- `docs/core/Omnix_TECHNICAL_REFERENCE.md` - FK coverage updated (90%)
- `replit.md` - Dec 2025 changes documented

---

## [2025-12-24] - ARES Strategies DEPRECATED & ARCHIVED

### ARES Complete Removal

**Decision**: ARES V1 and V2 strategies have been deprecated and archived. The system now uses only production-proven strategies.

**Reason**: ARES was experimental and underperforming. Simplifying the codebase for investor presentation.

### Files Archived (to `archive/deprecated_ares/`)

| Original Location | Archived To |
|-------------------|-------------|
| `omnix_core/strategies/ares_v1.py` | `archive/deprecated_ares/strategies/` |
| `omnix_core/strategies/ares_v2.py` | `archive/deprecated_ares/strategies/` |
| `src/omnix/domain/trading/strategies/ares_v1.py` | `archive/deprecated_ares/strategies/` |
| `src/omnix/domain/trading/strategies/ares_v2.py` | `archive/deprecated_ares/strategies/` |
| `omnix_testing/validate_ares_strategies.py` | `archive/deprecated_ares/testing/` |
| `omnix_testing/run_premium_validation.py` | `archive/deprecated_ares/testing/` |
| `omnix_services/stock_trading/premium/modules/ares_stock.py` | `archive/deprecated_ares/stock_trading/` |
| `docs/operations/experimental/ares_development.md` | `docs/history/2025-12/` |

### Code Cleaned

| File | Change |
|------|--------|
| `omnix_core/config/trading_profiles.py` | Removed all `ares_*` keys from all profiles |
| `src/omnix/config/settings.py` | Removed `enable_ares_v1`, `enable_ares_v2` fields |
| `tests/test_parity_harness.py` | Removed ARES import tests |
| `tests/test_domain_entities.py` | Changed strategy to `quantum_momentum` |
| `tests/integration/test_railway_startup.py` | Removed ARES validation checks |
| `omnix_services/telegram_service/inline_keyboards.py` | Updated docstrings |
| `omnix_services/telegram_service/callback_handler.py` | Updated docstrings |

### Active Strategies (V6.5.4d)

| Strategy | Points | Role |
|----------|--------|------|
| EMA Regime Signal | 40 | Primary Driver |
| HMM Regime | 25 | Regime Detection |
| Kalman Filter | 15 | Price Prediction |
| Non-Markovian Memory | 15 | Temporal Memory |
| Kelly Criterion | 10 | Position Sizing |

---

## [2025-12-02] - ARES Strategies Import Fix (OBSOLETE)

> **Note**: This entry is obsolete. ARES was deprecated on Dec 24, 2025. See above.

---

## Historial de Versiones

| Version | Fecha | Cambios Principales |
|---------|-------|---------------------|
| V6.5 | Dic 2024 | Adaptive Parameter Engine, On-Chain Intelligence |
| V6.4 | Nov 2024 | Portfolio Management, Market Intelligence |
| V6.3 | Nov 2024 | Stock Trading ULTRA, Real Data Integration |
| V6.2 | Oct 2024 | RMS Memory-Enhanced, Derivatives |
| V6.1 | Oct 2024 | Non-Markovian Kernel, Coherence Engine |
| V6.0 | Sep 2024 | Multi-Exchange Arbitrage, Institutional Compliance |

---

*OMNIX — Decision Governance Infrastructure*
