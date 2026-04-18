# OMNIX Advanced Tier: Arquitectura, Implementación y Visión Fundacional

**Autor**: Harold A. Nunes  
**Versión**: Advanced Tier  
**Última actualización**: Enero 24, 2026  
**Clasificación**: Investor Confidential

---

## 1. Origen e Inspiración

OMNIX nació como una idea muy clara: crear una infraestructura de control de riesgo de grado institucional que no dependa de nadie, capaz de analizar, decidir y proteger capital con un nivel institucional, pero con alma humana.

Desde el principio, mi objetivo fue construir algo real, funcional y escalable, que uniera tres pilares fundamentales:

1. **Autonomía** — un sistema que se autoajusta, aprende y actúa 24/7
2. **Seguridad** — módulos PQC integrados en producción (Kyber-768, Dilithium-3) para firma de órdenes
3. **Ética y transparencia** — auditorías verificables y principios Sharia-compliant

**OMNIX no es un bot de trading; es una infraestructura de preservación de capital** donde cada módulo tiene un propósito claro: mantener coherencia, precisión y seguridad en cada decisión.

> **Filosofía Central**: "Preservar capital antes de optimizar retornos"

---

## 2. Arquitectura General

OMNIX está organizado en capas modulares con arquitectura hexagonal (V7.0 en progreso):

### 2.1 Capa Cognitiva (IA Conversacional y Analítica)
- **Google Gemini 2.0 Flash**: Modelo primario de IA
- **OpenAI GPT-4o + Whisper**: Servicios de IA y transcripción de voz
- **Anthropic Claude**: Fallback de IA
- **ElevenLabs**: Text-to-speech multilingüe (español, inglés, árabe)
- **Tavily**: Búsqueda web en tiempo real para respuestas contextuales

### 2.2 Capa Cuantitativa (Decision Engine)

**Scoring Architecture** (100 puntos totales):

| Componente | Peso | Función |
|------------|------|---------|
| EMA Regime Signal | 40 pts | Driver principal - detecta tendencia |
| HMM Regime | 25 pts | Estado del mercado (Bull/Bear/Ranging) |
| Kalman Filter | 15 pts | Reducción de ruido |
| Non-Markovian Memory | 15 pts | Contexto temporal no lineal |
| Kelly Criterion | 10 pts | Sizing de posición |

**Capa de Veto/Penalización** (solo aplica penalizaciones):
- Monte Carlo Validator (10,000 simulaciones)
- Black Swan Detector
- Sentiment Analyzer
- Quantum Momentum

### 2.3 Capa de Gobernanza (Control Lógico)

**Flujo Jerárquico de Veto** (orden de ejecución):

```
1. MC VETO → 2. RMS VETO → 3. COHERENCE GATE → 4. ECW GATE → 5. Scoring → 6. Decision
```

| Gate | Función | Umbral |
|------|---------|--------|
| MC VETO | Bloquea si Monte Carlo WR < 50% o ER < 0 | Automático |
| RMS VETO | Risk Management System enforcement | Automático |
| COHERENCE GATE | Bloquea señales de baja calidad | Coherence < 45% |
| ECW GATE | Edge Confirmation Window - requiere persistencia | 3 ciclos consecutivos |

### 2.4 Capa de Infraestructura (Datos y Seguridad)

- **PostgreSQL (Railway)**: 45+ tablas con integridad referencial >91%
- **Redis (Railway)**: Caching, rate limiting, estado de sesiones
- **Post-Quantum Cryptography**: 
  - Módulos integrados en producción (NIST 2024)
  - Kyber-768 (key exchange) + Dilithium-3 (firmas de órdenes)
- **Deployment**: Railway (producción 24/7), Replit (desarrollo)

### 2.5 Capa Ética (Sharia & Auditoría)
- **Sharia Screening Engine en producción** — basado en AAOIFI Standard 62
- Filtro Halal automático (40+ criptoactivos evaluados en 12 categorías)
- **Bloqueo automático de activos Haram**: Maysir (especulación pura — meme coins), Riba (instrumentos con interés), Gharar (incertidumbre excesiva)
- Fuentes académicas citadas por activo: AAOIFI Standard 62, Mufti Taqi Usmani 2018, Shariyah Review Bureau
- Ejemplos: Bitcoin → Halal confirmado (alta confianza). Dogecoin → Haram bloqueado (Maysir)
- Registro auditable de cada operación
- Checksums criptográficos inmutables
- **Nota**: Motor de screening interno basado en estándares AAOIFI. No es certificación formal de junta Sharia (proceso externo separado).

---

## 3. Módulos Principales

### 3.1 Non-Markovian Temporal Memory (Memory Kernel)

Diseñado para detectar regímenes de mercado no lineales. Guarda patrones de comportamiento autocorrelacionados integrando:
- Datos on-chain
- Precios y volumen
- Volatilidad histórica

**Parámetros**:
- τ (tau): 12h
- ε (epsilon): 0.35
- Ω (omega): 0.523
- Window: 168h

### 3.2 Adaptive Parameter Engine V6.5 ULTRA

Sistema de autocalibración que incluye:

| Subcomponente | Función |
|---------------|---------|
| RegimeSignalProcessor | Detecta cambios de régimen |
| ParameterCalibrator | Ajusta SL/TP y sizing |
| CooldownManager | Evita sobrecalibración |
| MicrostructureAnalyzer | Analiza liquidez, spread, volumen |

### 3.3 Risk Guardian V5.4

El "guardián" del sistema:
- Supervisa drawdowns (hard cap 15%, observado en baseline 1.5%)
- Detecta overtrading (límite 20 trades/día)
- Activa circuit breaker automático
- Bloquea órdenes si hay incoherencia

### 3.4 Coherence Engine V6.5

Fusiona señales y decide cuándo operar:
- **Umbral mínimo**: 45% coherencia
- Si la coherencia entre estrategias baja del umbral, OMNIX NO opera

### 3.5 Edge Confirmation Window (ECW) - ADR-019

Sistema de "paciencia de capital" que requiere:
- MC Win Rate ≥ 52%
- MC Expected Return > 0%
- Black Swan ≤ MEDIUM
- **Por 3 ciclos consecutivos**

> Transforma "capital preservation" en "capital patience"

### 3.6 Decision Contradiction Index (DCI) - ADR-018

Métrica observacional que mide divergencia interna de señales:
- **DCI ≥ 70**: Alta contradicción → HOLD obligatorio
- Explica por qué el sistema NO opera

**Umbrales de ejecución realistas**:
- MC WR > 50%
- MC ER > 0%
- Coherence > 50%
- DCI < 70

### 3.7 Shadow Portfolio + Learning Engine - ADR-008

Sistema contrafactual que:
1. Trackea trades vetados
2. Analiza movimiento de precio post-veto
3. Determina si el veto fue correcto
4. Recomienda ajustes de umbrales

**Opportunity Tracker**:
- Missed Opportunities vs Losses Avoided
- Net Opportunity calculation
- Review date: Día 30

### 3.8 CAES (Confidence-Adaptive Entry System)

Ajusta sizing según nivel de confianza del sistema.

### 3.9 Modo Sniper

Modo de precisión con:
- ATR-Based Sizing (riesgo máximo 0.5% del balance)
- Volume Veto (bloquea si volumen 5-min < promedio 1-hora)

### 3.10 Veto Tracking System

Persistencia en PostgreSQL de todos los eventos de veto:
- **89,000+ ciclos de evaluación bloqueados** (no oportunidades de trading perdidas)
- Deduplicación automática
- Reporting para inversores

### 3.11 Post-Quantum Cryptography - ADR-022

**Módulos PQC integrados en producción** alineados con estándares NIST 2024:

| Componente | Algoritmo | Estándar | Propósito |
|------------|-----------|----------|-----------|
| Key Encapsulation | Kyber-768 (ML-KEM-768) | NIST-standardized | Intercambio seguro de claves |
| Digital Signatures | Dilithium-3 (ML-DSA-65) | NIST-standardized | Autenticación de órdenes |

- Las órdenes de trading se firman con Dilithium-3 antes de ejecución
- Nivel de seguridad NIST Level 3 (~192-bit equivalente clásico)
- Módulo: `omnix_core/security/pqc_security.py`

> **Nota**: Aplicado actualmente a autenticación de órdenes y capas de seguridad internas. No se comercializa como garantía de compliance ni certificación de seguridad externa.

### 3.12 Sharia Compliance System

- 40+ criptoactivos evaluados
- Clasificación automática por apalancamiento, liquidez, exposición
- Registro auditable sincronizado con Risk Guardian

---

## 4. Track Record y Métricas

### 4.1 Distinción de Períodos (CRÍTICO)

| Período | Fechas | Trades | P&L | Propósito |
|---------|--------|--------|-----|-----------|
| **Learning Baseline** | Nov 2025 - 14 Ene 2026 | 119 | -$15,198.73 | Calibración agresiva |
| **Track Record Oficial** | 15 Ene 2026 - presente | ~0 | $0 | Validación recalibrada |

> **Nota**: El Learning Baseline fue intencionalmente agresivo para stress-test. El Track Record Oficial opera con parámetros recalibrados.

> **Nota de Período**: Estos datos corresponden al Learning Baseline (Nov-Dic 2025), fase de calibración. Desde el 15 de enero 2026, el sistema opera con parámetros recalibrados en el Track Record Oficial.

### 4.2 Métricas Actuales

| Métrica | Valor |
|---------|-------|
| Capital Preservado | **98.5%** |
| Ciclos de Evaluación Bloqueados | **89,000+** |
| Win Rate (Baseline) | 20.2% |
| Max Drawdown (observed) | 1.5% |
| Max Drawdown (hard cap) | 15% |
| Días en Track Record | 10/30 |

### 4.3 KPIs Primarios (Orden de Importancia)

1. **Capital Preservation**: 98.5% del capital inicial preservado
2. **Evaluation Cycles Blocked**: 89,000+ ciclos de evaluación bloqueados (no oportunidades de trading)
3. **System Integrity**: Integridad referencial >91%, trail de auditoría completo
4. **Win Rate**: 20.17% (métrica diagnóstica del Learning Baseline, no de marketing)

> *Nota: Métricas 1-4 incluyen datos del Learning Baseline. Ver Nota de Período arriba.*

---

## 5. Dashboard Institucional

### 5.1 Panel Flask (Puerto 5000)

Muestra en tiempo real:
- System Health Score (0-100)
- VaR, CVaR, P&L, Coherence
- Live Status con precios de mercado
- Calibration Progress
- Recommended Actions

### 5.2 Widgets Implementados

| Widget | Función |
|--------|---------|
| Equity Curve | Comparación OMNIX vs BTC Hold |
| P&L Breakdown | Por símbolo y outcome |
| Time Heatmap | P&L por hora/día |
| Correlation Heatmap | Correlación entre pares |
| Opportunity Tracker | Missed vs Avoided |
| Veto Activity | Distribución de vetos 24h/7d |
| Quick Insights | Alertas priorizadas |
| Recommended Actions | Sugerencias del sistema |

### 5.3 Streamlit Shadow Analytics (Puerto 8080)

Página dedicada que responde: "¿Cómo decide OMNIX y por qué NO opera?"

Incluye:
- System Overview
- Decision Quality metrics
- Governance/Risk metrics
- v_shadow_trade_metrics VIEW

---

## 6. Integraciones Externas

### 6.1 Trading & Datos

| Servicio | Función |
|----------|---------|
| Kraken | Crypto trading (real y paper) |
| Alpaca | Stocks y derivados |
| CoinGecko | Precios backup |
| Alternative.me | Fear & Greed Index |
| Finnhub | News y sentiment |
| Alpha Vantage | Indicadores técnicos |

### 6.2 IA & Servicios

| Servicio | Función |
|----------|---------|
| Google Gemini 2.0 Flash | IA primaria |
| OpenAI GPT-4o | IA secundaria |
| Anthropic Claude | Fallback |
| Whisper | Transcripción de voz |
| ElevenLabs | Text-to-speech |
| Tavily | Búsqueda web real-time |

### 6.3 Infraestructura

| Servicio | Función |
|----------|---------|
| ANU QRNG | Números aleatorios cuánticos |
| Railway | Deployment producción |
| GitHub | Control de versiones |
| Stripe | Procesamiento de pagos |

---

## 7. Decisiones Arquitectónicas (ADRs)

OMNIX documenta todas las decisiones importantes en ADRs:

| ADR | Tema | Estado |
|-----|------|--------|
| ADR-001 | Brutal Honesty Monitoring | Adoptado |
| ADR-003 | Official Positioning | Adoptado |
| ADR-004 | Position Sizing Hotfix | Adoptado |
| ADR-005 | Dual Win Rate Framework | Adoptado |
| ADR-007 | Coherence Threshold Calibration | Adoptado |
| ADR-008 | Opportunity Tracker | Adoptado |
| ADR-012 | Learning Baseline Freeze | Adoptado |
| ADR-018 | Decision Contradiction Index | Adoptado |
| ADR-019 | Edge Confirmation Window | Adoptado |
| ADR-021 | Shadow Trade Metrics VIEW | Adoptado |
| ADR-022 | Post-Quantum Cryptography | Adoptado |
| ADR-023 | Investor Positioning Refinement | Adoptado |

---

## 8. Filosofía Operativa

OMNIX no busca solo ganar operaciones; busca mantener coherencia, ética y sostenibilidad.

**Principios**:
- Si hay duda → **NO opera**
- Si hay riesgo → **se ajusta**
- Si hay incoherencia → **se pausa**
- Si hay contradicción interna (DCI alto) → **HOLD**

> "Prefiero mil trades buenos que un millón sin control. OMNIX es precisión por principio."

**Identidad**:
- **OMNIX ES**: Infraestructura de control de riesgo, sistema de preservación de capital
- **OMNIX NO ES**: "Trading bot", "AI trader", "sistema para hacer dinero"

---

## 9. Visión 2026 – 2027

Meta: Llevar OMNIX a Dubái como plataforma institucional de IA financiera ética.

**Objetivos**:
1. Completar Track Record de 30 días (Feb 14, 2026)
2. Presentar a inversores para seed de $500K
3. Certificación ADGM
4. Conexión con instituciones MENA
5. Portafolios Sharia-compliant en tiempo real
6. Expansión a mercados asiáticos y europeos

---

## 10. Información de Contacto

**Creador y Arquitecto**: Harold A. Nunes

---

*Este documento es confidencial y está destinado exclusivamente para propósitos de due diligence de inversores.*

**Clasificación**: Investor Confidential
