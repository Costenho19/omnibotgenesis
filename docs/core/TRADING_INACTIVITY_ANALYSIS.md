# OMNIX V6.5.4 - Análisis de Inactividad de Trading

**Fecha**: 9 de Diciembre, 2025  
**Versión**: V6.5.4b INSTITUTIONAL+  
**Estado**: 🔄 BAJO EVALUACIÓN - Umbrales ajustados, pendiente verificación en Railway

---

## Resumen Ejecutivo

El bot de auto-trading está operativo y analizando correctamente los 4 pares configurados (BTC/USD, XRP/USD, ADA/USD, LINK/USD), pero no genera nuevos trades desde el 6 de Diciembre, 2025. Este documento analiza las causas y propone soluciones.

---

## Estado Actual del Sistema

### Métricas al 9 de Diciembre, 2025

| Métrica | Valor |
|---------|-------|
| Total Trades | 27 |
| Win Rate Reportado | 29.6% |
| P/L Total | -$3,297.79 |
| Primer Trade | 5 Dic, 23:19 UTC |
| Último Trade | 6 Dic, 07:28 UTC |
| Días sin Trades | 3 días |

### Configuración Activa

- **Perfil**: `PRODUCTION_STABLE`
- **Modo**: PAPER TRADING ($1M virtual)
- **Pares Permitidos**: BTC/USD, XRP/USD, ADA/USD, LINK/USD
- **Intervalo de Escaneo**: 15 segundos
- **ARES V1/V2**: Desactivados (correcto para PRODUCTION_STABLE)

---

## Diagnóstico

### Evidencia de Logs de Railway (9 Dic 2025, 09:25-09:27 UTC)

```log
[INFO] omnix_core.bot.auto_trading_bot - 🔍 Escaneando BTC/USD (2/4)
[INFO] omnix_core.bot.auto_trading_bot - 💰 Precio actual de BTC/USD: $90,359.90
[INFO] omnix_services.trading_service.monte_carlo - ✅ Monte Carlo complete: Win rate=50.1%, VaR95=-0.46%, Expected return=-0.00%
[INFO] omnix_core.bot.auto_trading_bot - 📊 PRODUCTION_STABLE: ARES V1=False, V2=False
[INFO] omnix_core.bot.auto_trading_bot - 📊 Análisis V5.2 completado: HOLD - Confianza: 76.5%
[INFO] omnix_core.bot.auto_trading_bot -    📊 Análisis: HOLD | Confianza: 76.50% | Trade: NO | Razón: []
```

### Observaciones Clave

1. **El sistema está funcionando correctamente**: El bot escanea los 4 pares cada 15 segundos
2. **Monte Carlo muestra señales neutrales**: Win rate ~50%, Expected return ~0%
3. **Todas las decisiones son HOLD**: Ningún análisis genera BUY o SELL
4. **Razón vacía `[]`**: Las estrategias no encuentran condiciones de entrada

---

## 10 Posibles Causas de Bloqueo de Trades

El sistema tiene múltiples mecanismos de protección que pueden detener la generación de trades:

### 1. Parada de Emergencia (Emergency Stop)
- **Trigger**: Pérdidas diarias exceden `max_daily_loss_pct`
- **Log**: `🚨 PARADA DE EMERGENCIA - Pérdidas excesivas`
- **Estado**: NO ACTIVADO (no hay log)

### 2. ARP Rollback (Algorithmic Rollback Protocol)
- **Trigger**: Degradación de performance post-deploy >1%
- **Log**: `🔄 ARP ROLLBACK TRIGGERED`
- **Estado**: NO ACTIVADO

### 3. Circuit Breaker por Par
- **Trigger**: Drawdown diario de un par excede límite calibrado
- **Log**: `🔌 CIRCUIT BREAKER: BLOQUEADO`
- **Estado**: NO ACTIVADO

### 4. Límite de Posiciones Abiertas
- **Trigger**: Ya hay 20 posiciones abiertas
- **Log**: `🛑 LÍMITE ALCANZADO: X/20 posiciones abiertas`
- **Estado**: NO ACTIVADO

### 5. AI Risk Guardian
- **Trigger**: Overtrading, revenge trading, o pérdidas excesivas
- **Log**: `🛡️ AI RISK GUARDIAN BLOQUEÓ TRADE`
- **Estado**: NO ACTIVADO (solo bloquea en REAL MODE)

### 6. Coherence Engine Veto
- **Trigger**: Score de coherencia < umbral crítico (30%)
- **Log**: `⚠️ COHERENCE ENGINE VETO`
- **Estado**: NO HAY VETOS (análisis termina antes)

### 7. Symbol Filter
- **Trigger**: Par no permitido en perfil activo
- **Log**: `🚫 SYMBOL FILTER: BLOQUEADO`
- **Estado**: NO ACTIVADO (4 pares permitidos están siendo escaneados)

### 8. Sin Posición para SELL
- **Trigger**: Intento de SELL sin posición abierta
- **Log**: `SELL→HOLD (no open position)`
- **Estado**: NO APLICA (no hay señales SELL)

### 9. Bot Pausado Manualmente
- **Trigger**: Usuario ejecutó `/stop` o `running = False`
- **Log**: Bot no escanea pares
- **Estado**: NO ACTIVADO (bot está escaneando)

### 10. ⚠️ Estrategias No Generan Señales (CAUSA IDENTIFICADA)
- **Trigger**: Las 10 estrategias de producción no encuentran oportunidades
- **Evidencia**: Todos los análisis terminan en HOLD con Razón: `[]`
- **Estado**: ACTIVO - Esta es la causa del problema

---

## Análisis de Causa Raíz

### Por qué las estrategias deciden HOLD

El perfil `PRODUCTION_STABLE` utiliza 10 estrategias conservadoras:

1. QuantumMomentum
2. Monte Carlo
3. Kelly Criterion
4. Black Swan Detector
5. Hidden Markov Model (HMM)
6. Kalman Filter
7. Non-Markovian Kernel
8. Coherence Engine
9. Risk Guardian
10. SentimentAnalysis

**Problema**: Monte Carlo muestra consistentemente:
- Win rate: ~50% (neutral)
- VaR95: -0.46% (riesgo moderado)
- Expected return: 0.00% (sin ventaja estadística)

Esto indica que el mercado está en condiciones donde las estrategias no detectan una ventaja clara.

### Umbrales Posiblemente Muy Restrictivos

El perfil `PRODUCTION_STABLE` está diseñado para minimizar pérdidas, pero esto puede resultar en:
- Muy pocas señales de entrada
- Requisitos de consenso muy altos entre estrategias
- Umbrales de confianza demasiado conservadores

---

## Soluciones Propuestas

### Opción 1: Ajustar Umbrales en PRODUCTION_STABLE (Recomendado)

Modificar `omnix_core/config/trading_profiles.py`:

```python
# Reducir umbral de score mínimo
score_threshold_min = 55.0  # Actual: posiblemente más alto

# Reducir umbral de coherencia para veto
coherence_veto_critical = 25.0  # Actual: 30.0
coherence_veto_normal = 40.0    # Actual: 45.0

# Aumentar agresividad del CAES
caes_aggression_min = 0.7  # Actual: 0.5
```

### Opción 2: Crear Perfil PAPER_MODERATE

Un perfil intermedio entre PRODUCTION_STABLE y PAPER_AGGRESSIVE:

```python
PAPER_MODERATE = TradingProfile(
    name="PAPER_MODERATE",
    description="Perfil moderado para generar track record",
    coherence_veto_enabled=True,
    coherence_veto_critical=25.0,
    coherence_veto_normal=35.0,
    score_threshold_min=50.0,
    enable_ares_v1=False,
    enable_ares_v2=False,
    ...
)
```

### Opción 3: Temporalmente Usar PAPER_AGGRESSIVE

Para acelerar la generación de trades durante el período de paper trading:

```bash
# En Railway, cambiar variable de entorno
TRADING_PROFILE=PAPER_AGGRESSIVE
```

**Riesgo**: Más trades pero posiblemente menor win rate.

### Opción 4: Reducir Requisitos de Consenso

Modificar el número mínimo de estrategias que deben estar de acuerdo:

```python
min_strategies_agree = 4  # Actual: posiblemente 6+
```

---

## Proyección de Tiempo para 200 Trades

| Escenario | Trades/Día | Días para 200 |
|-----------|------------|---------------|
| Actual (HOLD siempre) | 0 | ∞ |
| Umbrales Ajustados | 20-30 | 6-9 días |
| PAPER_AGGRESSIVE | 50-80 | 2-3 días |
| PAPER_MODERATE | 30-50 | 4-6 días |

---

## Recomendación Final

1. **Corto Plazo**: Ajustar umbrales en PRODUCTION_STABLE para permitir más trades mientras se mantiene la calidad
2. **Mediano Plazo**: Monitorear win rate después de ajustes
3. **Largo Plazo**: Calibrar umbrales basándose en datos reales de 100+ trades

---

## Archivos Relevantes

- `omnix_core/config/trading_profiles.py` - Definición de perfiles
- `omnix_core/bot/auto_trading_bot.py` - Lógica de decisión de trades
- `omnix_services/coherence_service/coherence_engine.py` - Sistema de consenso
- `omnix_services/trading_service/monte_carlo.py` - Simulaciones Monte Carlo

---

## 🔄 Solución Implementada (9 Dic 2025) - BAJO EVALUACIÓN

Se ajustaron los umbrales del perfil `PRODUCTION_STABLE` en `omnix_core/config/trading_profiles.py`.

**IMPORTANTE**: Los cambios requieren verificación en Railway después del deploy:
1. Hacer push a GitHub
2. Esperar auto-deploy en Railway
3. Verificar logs por señales BUY/SELL
4. Confirmar generación de trades en 24-48 horas

### Cambios Realizados en PRODUCTION_STABLE

| Parámetro | Antes | Después | Justificación |
|-----------|-------|---------|---------------|
| `coherence_veto_critical` | 50% | **25%** | Umbral anterior inalcanzable |
| `coherence_veto_normal` | 65% | **40%** | Alineado con BALANCED |
| `coherence_warning` | 78% | **55%** | Proporcional |
| `coherence_good` | 90% | **75%** | Proporcional |
| `min_confidence` | 0.25 | **0.15** | Mayor permisividad |
| `score_very_strong` | 30 | **15** | Señales más alcanzables |
| `score_strong` | 20 | **8** | Señales más alcanzables |
| `score_moderate` | 12 | **4** | Señales más alcanzables |
| `trades_per_day_target` | 12 | **15** | Más oportunidades |
| `hmm_veto_confidence_threshold` | 0.70 | **0.90** | Solo veta con 90%+ confianza |
| `ramp_up_phase1_trades` | 10 | **5** | Aceleración inicial |

### Cambios en Calibraciones por Par

| Par | min_confidence Antes | min_confidence Después |
|-----|---------------------|----------------------|
| BTC/USD | 0.25 | **0.18** |
| XRP/USD | 0.25 | **0.18** |
| ADA/USD | 0.30 | **0.22** |
| LINK/USD | 0.28 | **0.20** |

### Proyección Post-Ajuste

| Métrica | Estimación |
|---------|------------|
| Trades esperados/día | 15-25 |
| Win Rate objetivo | 55%+ |
| Días para 200 trades | 8-13 días |
| Días para 500 trades | 20-35 días |

---

## Historial de Cambios

| Fecha | Cambio | Impacto |
|-------|--------|---------|
| 5 Dic 2025 | Primer trade del sistema | Inicio de track record |
| 6 Dic 2025 | Último trade registrado | 27 trades totales |
| 6-9 Dic 2025 | Sin actividad | Estrategias en HOLD constante |
| 9 Dic 2025 | Diagnóstico completado | Identificación de causa raíz |
| **9 Dic 2025** | **Umbrales ajustados V6.5.4b** | **Pendiente verificación en Railway** |

---

*Documento generado automáticamente por OMNIX V6.5.4b INSTITUTIONAL+*
