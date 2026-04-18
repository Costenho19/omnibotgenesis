# OMNIX Dashboard Improvement Backlog

**Created:** January 13, 2026 
**Last Updated:** January 14, 2026 
**Reference:** ADR-006-dashboard-improvement-proposals.md

## Priority Legend

| Priority | Timeline | Description |
|----------|----------|-------------|
| P0 | TODAY | Critical bugs affecting credibility |
| P1 | THIS WEEK | High-impact UX improvements |
| P2 | NEXT WEEK | Nice-to-have features |
| P3 | BACKLOG | Future considerations |

---

## P0: Critical Fixes (TODAY)

### BUG-001: WR Dir Shows 0.0% Instead of 37.8%

**Location:** Trade History Widget 
**File:** `omnix_dashboard/blueprints/core.py` 
**Problem:** Trade History API didn't return `win_rate_directional` 
**Fix:** Added SQL aggregate `SUM(CASE WHEN profit_pct > 0 THEN 1 ELSE 0 END)` to API 
**Status:** [x] COMPLETED (Jan 13, 2026)

### BUG-002: Fee Eroded Shows 0 Instead of 21

**Location:** Trade History Widget 
**File:** `omnix_dashboard/blueprints/core.py` 
**Problem:** Fee-eroded count not returned by API 
**Fix:** Added SQL aggregate `SUM(CASE WHEN profit_pct > 0 AND profit_loss < 0 THEN 1 ELSE 0 END)` to API 
**Status:** [x] COMPLETED (Jan 13, 2026)

### BUG-003: "Protected" Metric is Misleading

**Location:** Header 
**Files:** `omnix_dashboard/templates/terminal.html` 
**Problem:** "$31.4M Protected" implies $31.4M at risk when capital is $1M 
**Fix:** Renamed to "Notional Blocked" with explanatory tooltip 
**Status:** [x] COMPLETED (Jan 13, 2026)

---

## P1: UX Improvements (THIS WEEK)

### FEAT-001: System Health Score Widget

**Description:** Visual health indicator showing system status at a glance 
**Components:**
- Risk Controls score (35% weight) - Capital preservation tracking
- Data Quality score (25% weight) - Database connection status
- Win Rate Progress score (25% weight) - Progress toward 40% target
- Uptime score (15% weight) - System monitoring status
- Overall score (weighted average, 0-100)

**Implementation:**
- API: `/api/system/health-score` in `omnix_dashboard/blueprints/core.py`
- Widget: `omnix_dashboard/static/js/components/healthscore.js`
- CSS: `omnix_dashboard/static/css/components/healthscore.css`
- SVG ring animation with status badge (EXCELLENT/GOOD/CALIBRATING/NEEDS ATTENTION/CRITICAL)

**Status:** [x] COMPLETED (Jan 13, 2026)

### FEAT-002: Live Status Section

**Description:** Real-time view of what the system is doing NOW 
**Components:**
- Current action (ANALYZING/EXECUTING/MONITORING)
- Status detail message
- Last action with result (WIN/LOSS)
- System state (Veto ON/OFF, Regime, Open Positions)
- LIVE indicator with pulse animation

**Implementation:**
- API: `/api/system/live-status` in `omnix_dashboard/blueprints/core.py`
- Widget: `omnix_dashboard/static/js/components/livestatus.js`
- CSS: `omnix_dashboard/static/css/components/livestatus.css`

**Status:** [x] COMPLETED (Jan 13, 2026)

### FEAT-003: Quick Insights (Auto-Generated)

**Description:** Auto-generated actionable insights based on real trading data 
**Components:**
- Priority-ranked insights (1-5)
- Type badges (SUCCESS/WARNING/INFO/PROGRESS/CAUTION)
- Capital protection status (98.5%)
- Win rate progress toward 40% target
- Fee impact analysis (21 fee-eroded trades)
- Regime-specific recommendations

**Implementation:**
- API: `/api/system/quick-insights` in `omnix_dashboard/blueprints/core.py`
- Widget: `omnix_dashboard/static/js/components/quickinsights.js`
- CSS: `omnix_dashboard/static/css/components/quickinsights.css`

**Status:** [x] COMPLETED (Jan 13, 2026)

### FEAT-004: Calibration Progress Bar

**Description:** Visual progress toward system optimization 
**Components:**
- Phase 1: Data Collection (119/100 trades) - 100%
- Phase 2: Pattern Analysis (profitable patterns identified) - 100%
- Phase 3: Threshold Optimization (37.8% → 40% target) - 30%
- Phase 4: Live Deployment (ready when phases 1-3 complete) - 0%
- Overall Progress: 60.5%

**Implementation:**
- API: `/api/system/calibration-progress` in `omnix_dashboard/blueprints/core.py`
- Widget: `omnix_dashboard/static/js/components/calibrationprogress.js`
- CSS: `omnix_dashboard/static/css/components/calibrationprogress.css`

**Status:** [x] COMPLETED (Jan 13, 2026)

### FEAT-005: Recommended Actions

**Description:** Suggested next steps for Harold 
**Status:** [x] COMPLETED (Jan 13, 2026)

**Implementation:**
- API: `/api/system/recommended-actions` in `omnix_dashboard/blueprints/core.py`
- Widget: `omnix_dashboard/static/js/components/recommendedactions.js`
- CSS: `omnix_dashboard/static/css/components/recommendedactions.css`

**Features:**
- Priority-based sorting (HIGH → MEDIUM → LOW)
- Dynamic action generation based on trading metrics
- 4 action types: progress, calibration, optimization, status
- Color-coded priority badges
- Auto-refresh every 10 seconds

**Current Actions Shown:** 
**Components:**
- Urgent actions with reasoning
- Review items with context
- Confirmation of correct decisions

**Status:** [ ] Not Started

---

## P2: Nice-to-Have (NEXT WEEK)

### FEAT-006: Comparative Metrics Table

**Description:** OMNIX vs BTC Hold vs Average Bot comparison 
**Metrics:** Return, Max DD, Win Rate, Capital Preserved %, Risk Blocked

**Implementation:**
- API: `/api/metrics/comparative` in `omnix_dashboard/blueprints/core.py`
- Widget: `omnix_dashboard/static/js/components/comparativemetrics.js`
- CSS: `omnix_dashboard/static/css/components/comparativemetrics.css`

**Features:**
- Period-aligned BTC comparison (uses OMNIX trading window, not arbitrary 30 days)
- Honest investor messaging per ADR-003
- `data_available` flags for transparency
- Auto-refresh every 10 seconds
- Responsive table with color-coded highlights

**Status:** [x] COMPLETED (Jan 14, 2026)

### FEAT-007: P&L Breakdown Visual

**Description:** Detailed P&L by symbol and by reason 
**Components:** Bar charts, percentages, trend indicators

**Implementation:**
- API: `/api/metrics/pnl-breakdown` in `omnix_dashboard/blueprints/core.py`
- Widget: `omnix_dashboard/static/js/components/pnlbreakdown.js`
- CSS: `omnix_dashboard/static/css/components/pnlbreakdown.css`

**Features:**
- P&L by symbol with horizontal bar visualization
- Trade outcomes: Pure Wins (20.2%), Fee Eroded (17.6%), Pure Losses (62.2%)
- Directional accuracy tracking
- Auto-refresh every 30 seconds

**Status:** [x] COMPLETED (Jan 14, 2026)

### FEAT-008: Correlation Heatmap

**Description:** Asset performance matrix with correlation analysis 
**Components:** Per-symbol metrics, hourly P&L correlation, diversification score

**Implementation:**
- API: `/api/metrics/correlation` in `omnix_dashboard/blueprints/core.py`
- Widget: `omnix_dashboard/static/js/components/correlationheatmap.js`
- CSS: `omnix_dashboard/static/css/components/correlationheatmap.css`

**Features:**
- Per-symbol performance metrics (trades, win rate, P&L, volatility)
- Correlation matrix using hourly buckets for statistical validity
- Diversification score (0-100) based on average correlation
- Auto-refresh every 60 seconds

**Status:** [x] COMPLETED (Jan 14, 2026)

### FEAT-009: Time Heatmap

**Description:** P&L analysis by hour and day of week 
**Components:** 7x24 heatmap grid, best/worst time identification

**Implementation:**
- API: `/api/metrics/time-heatmap` in `omnix_dashboard/blueprints/core.py`
- Widget: `omnix_dashboard/static/js/components/timeheatmap.js`
- CSS: `omnix_dashboard/static/css/components/timeheatmap.css`

**Features:**
- 7x24 grid showing P&L by hour and day of week
- Color-coded cells (green=profit, red=loss)
- Best/worst time identification with P&L amounts
- Trade count per cell
- Auto-refresh every 60 seconds

**Status:** [x] COMPLETED (Jan 14, 2026)

### FEAT-010: Regime Detection Dashboard

**Description:** Current market regime with historical performance 
**Components:** Regime indicator, confidence, duration, performance by regime

**Implementation:**
- API: `/api/regime/dashboard` in `omnix_dashboard/blueprints/core.py`
- Widget: `omnix_dashboard/static/js/components/regimedetection.js`
- CSS: `omnix_dashboard/static/css/components/regimedetection.css`

**Features:**
- Current regime detection (BULLISH/BEARISH/RANGING) inferred from EMA signals
- Confidence and coherence metrics display
- Veto activity summary (24h) with capital protected
- Signal distribution visualization (24h)
- Recent regime transitions timeline
- System status message explaining current behavior
- Investor-friendly messaging per ADR-003

**Data Source:** `shadow_trade_events` table (48K+ events since Jan 9)

**Status:** [x] COMPLETED (Jan 14, 2026)

### FEAT-011: Opportunity Tracker (formerly Learning Engine Insights)

**Description:** Shadow Portfolio analysis for missed opportunities vs losses avoided 
**Components:** Two-sided accounting, Day 30 review framework, veto effectiveness

**Implementation:**
- API: `/api/learning/insights` in `omnix_dashboard/blueprints/core.py`
- Widget: `omnix_dashboard/static/js/components/learninginsights.js`
- CSS: `omnix_dashboard/static/css/components/learninginsights.css`

**Features:**
- Veto effectiveness by type (BLACK_SWAN, COHERENCE_GATE, MC, RMS)
- **Missed Opportunities tracking** (trades blocked with good conditions)
- **Losses Avoided tracking** (trades correctly blocked)
- **Net Opportunity calculation** (missed - avoided)
- Day 30 review summary and recommendation
- Average EMA/coherence scores per veto type
- Top vetoed symbols analysis
- 7-day and 30-day rolling window analysis
- Auto-refresh every 60 seconds

**Day 30 Review Criteria (ADR-008):**
- If missed > 20 AND estimated profit > $3K → Test lower thresholds
- If missed < 10 OR avoided >> missed → Keep conservative
- Review date: February 13, 2026

**Data Source:** `shadow_trade_events` table (48K+ events)

**Reference:** `docs/reference/adr/ADR-008-opportunity-tracker.md`

**Status:** [x] COMPLETED (Jan 14, 2026) - Enhanced with Opportunity Tracker

**Widget Visual (10-second investor view):**
```
🎯 OPPORTUNITY TRACKER | Day 1/30
┌─────────────────────────────────────────────┐
│ 💎 MISSED ⚖️ VS ✅ AVOIDED │
│ +$0 ⚖️ -$239.5K │
│ 0 trades 479 trades │
├─────────────────────────────────────────────┤
│ NET: -$239.5K = Sistema protegiendo ✅ │
│ 📅 Review: Feb 13, 2026 | Mantener │
└─────────────────────────────────────────────┘
```

### FEAT-012: Collapsible Advanced Sections

**Description:** Mobile-friendly collapsed sections 
**Sections:** Advanced Metrics, Detailed History, Model Parameters

---

## P3: Backlog (Future)

### FEAT-013: Expected vs Actual Analysis

**Description:** Monte Carlo predictions vs actual results

### FEAT-014: Model Confidence Dashboard

**Description:** Per-strategy reliability scores

### FEAT-015: Veto Effectiveness Analysis

**Description:** Detailed veto breakdown with effectiveness metrics

---

## Progress Tracking

| ID | Description | Priority | Status | Assigned | Completed |
|----|-------------|----------|--------|----------|-----------|
| BUG-001 | WR Dir 0.0% | P0 | DONE | Agent | Jan 13, 2026 |
| BUG-002 | Fee Eroded 0 | P0 | DONE | Agent | Jan 13, 2026 |
| BUG-003 | Protected misleading | P0 | DONE | Agent | Jan 13, 2026 |
| FEAT-001 | System Health Score | P1 | DONE | Agent | Jan 13, 2026 |
| FEAT-002 | Live Status | P1 | DONE | Agent | Jan 13, 2026 |
| FEAT-003 | Quick Insights | P1 | DONE | Agent | Jan 13, 2026 |
| FEAT-004 | Calibration Progress | P1 | DONE | Agent | Jan 13, 2026 |
| FEAT-005 | Recommended Actions | P1 | DONE | Agent | Jan 13, 2026 |
| FEAT-006 | Comparative Metrics | P2 | DONE | Agent | Jan 14, 2026 |
| FEAT-007 | P&L Breakdown | P2 | DONE | Agent | Jan 14, 2026 |
| FEAT-008 | Correlation Heatmap | P2 | DONE | Agent | Jan 14, 2026 |
| FEAT-009 | Time Heatmap | P2 | DONE | Agent | Jan 14, 2026 |
| FEAT-010 | Regime Detection Dashboard | P2 | DONE | Agent | Jan 14, 2026 |
| FEAT-011 | Learning Engine Insights | P2 | DONE | Agent | Jan 14, 2026 |

---

## Summary

**Dashboard Status: 23/23 Widgets Operational**

| Priority | Total | Completed | Remaining |
|----------|-------|-----------|-----------|
| P0 (Bugs) | 3 | 3 | 0 |
| P1 (UX) | 5 | 5 | 0 |
| P2 (Features) | 6 | 6 | 0 |
| **Total** | **14** | **14** | **0** |

All critical, high-priority, and nice-to-have features have been delivered.

---

## Notes

- All fixes must maintain ADR-002 (Honest Framing)
- All metrics must follow ADR-005 (Dual Win Rate Framework)
- Dashboard target score: 9.5/10 (current: 7.5/10)

---

## GOVERNANCE MODULES ROADMAP (Mar 2026)

**Contexto:** Módulos de gobernanza identificados como expansión natural de OMNIX hacia dominios no-financieros y cumplimiento regulatorio global. Documentados aquí para demostrar capacidad de escalabilidad ante inversores.

**Fuente:** Sesión estratégica Harold Nunes — 25 Mar 2026

---

### PRIORIDAD ALTA — Construir antes de 

#### MOD-009: Regulatory-Aware Decision Engine (Sharia Gate)
- **Descripción:** Valida decisiones contra marcos regulatorios específicos por cliente: AML, impuestos, jurisdicción, y cumplimiento Sharia para mercados del Golfo
- **Implementación:** CP-6 configurable como "Sharia Governance Gate"
- **Reglas Sharia:** Screening halal/haram, sin riba, sin gharar excesivo, ratio de deuda ≤ 33%
- **Output:** Recibo PQC con sello de cumplimiento Sharia verificable públicamente
- **Mercado objetivo:** Fondos islámicos UAE, Arabia Saudita, Qatar
- **Status:** ✅ IMPLEMENTADO — Mar 25, 2026 (ADR-046 / CP-6)

#### MOD-019: AML Compliance Gate
- **Descripción:** Screening anti-lavado: monedas de privacidad, mixer tokens, volumen anómalo, patrones de structuring
- **Implementación:** CP-9 — `omnix_core/governance/aml_gate.py`. Activar: `AML_GATE_ENABLED=true`
- **Regulación:** FATF Rec.15, FinCEN, UAE Central Bank AML/CFT Framework
- **Status:** ✅ IMPLEMENTADO — Mar 25, 2026 (ADR-047 / CP-9)

#### MOD-020: Fraud Detection Gate
- **Descripción:** Detección de manipulación de mercado: DCI extremo, divergencia técnica/sentimiento, reversiones rápidas
- **Implementación:** CP-10 — `omnix_core/governance/fraud_gate.py`. Activar: `FRAUD_GATE_ENABLED=true`
- **Regulación:** EU AI Act Art. 6, MiFID II, SEC Rule 10b-5
- **Status:** ✅ IMPLEMENTADO — Mar 25, 2026 (ADR-048 / CP-10)

#### MOD-021: Jurisdiction Compliance Gate
- **Descripción:** Validación jurisdiccional: activos prohibidos y tipos de operación por país (UAE, EU, US, GCC)
- **Implementación:** CP-11 — `omnix_core/governance/jurisdiction_gate.py`. Activar: `JURISDICTION_GATE_ENABLED=true` + `JURISDICTION=UAE`
- **Regulación:** UAE VARA, EU MiCA, FinCEN/SEC, OFAC sanctions
- **Status:** ✅ IMPLEMENTADO — Mar 25, 2026 (ADR-049 / CP-11)

---

### PRIORIDAD MEDIA — Siguientes 90 días

#### MOD-010: Breach Containment Engine
- **Descripción:** Modifica el comportamiento del pipeline bajo condición de ciberataque detectado. Bloquea decisiones automáticamente si el entorno de ejecución está comprometido.
- **Status:** BACKLOG

#### MOD-014: Unified Decision Control Layer
- **Descripción:** API externa que coordina todos los pilares de gobernanza y bloquea si cualquiera falla. Versión formalizada del pipeline actual para consumo B2B.
- **Status:** BACKLOG

#### MOD-013: Multi-Domain Risk Governance
- **Descripción:** Unifica riesgo financiero, técnico, legal y humano en un único score de gobernanza. Permite a clientes no-financieros usar OMNIX como capa de control.
- **Status:** BACKLOG

---

### PRIORIDAD BAJA — Visión a largo plazo (6-18 meses)

#### MOD-001: Tail Risk Veto Engine
- Bloquea eventos no previstos / Black swans
- Ya implementado parcialmente como Black Swan Detector — formalizar como módulo separado

#### MOD-002: Stability Illusion Detector
- Detecta falsa sensación de seguridad en entornos "demasiado perfectos"
- Penaliza señales de baja volatilidad artificial

#### MOD-003: Survival Core™
- Prioriza supervivencia del sistema sobre crecimiento
- Bloquea decisiones que ponen en riesgo la continuidad operacional

#### MOD-004: Regime Shift Sentinel
- Detecta cambios de régimen de mercado/entorno
- Ya implementado parcialmente como HMM Regime — formalizar

#### MOD-005: Behavioral Risk Engine
- Detecta cambios en comportamiento humano o patrones anómalos de uso
- Evita decisiones basadas en datos desactualizados por cambio de comportamiento

#### MOD-006: Uncertainty Governance Engine
- Actúa bajo información incompleta: bloquea, retrasa, o exige validación humana
- Ya implementado parcialmente como DCI (Decision Contradiction Index)

#### MOD-008: Dependency Risk Engine
- Detecta dependencias críticas: AWS, clientes concentrados, proveedores únicos
- Evita puntos únicos de fallo en la cadena de decisión

#### MOD-011: Pressure Point Detection Engine
- Detecta el punto donde el sistema se rompe bajo carga extrema
- Protege el checkpoint más vulnerable del pipeline

#### MOD-012: Safe Speed Execution Layer
- Permite velocidad de ejecución sin errores fatales
- Balance dinámico entre rapidez y nivel de control

#### MOD-015: Proof-of-Execution Governance
- Valida ejecución en tiempo real, no confía en documentos post-hoc
- Extensión natural de los recibos PQC actuales

#### MOD-016: Impact-Only Governance Layer
- Ignora probabilidad, prioriza impacto absoluto
- Complemento al modelo de Kelly actual

#### MOD-017: Response-Time Governance
- Decide dinámicamente qué tan rápido actuar y con qué nivel de control
- Ajusta latencia del pipeline según urgencia del contexto

#### MOD-018: Adaptive Rebuild Engine
- Permite reconstrucción estructural tras crisis
- Evolución del sistema sin pérdida de integridad histórica

---

### Mensaje para inversores — Escalabilidad demostrable

> "OMNIX no es un producto de trading. Es infraestructura de gobernanza de decisiones. Cada módulo en este roadmap representa una vertical nueva donde el mismo pipeline de 8 checkpoints, los mismos recibos PQC, y la misma arquitectura fail-closed pueden desplegarse sin rediseño. Sharia compliance, AML, EU AI Act, ISO 42001 — todos son configuraciones del mismo motor."
