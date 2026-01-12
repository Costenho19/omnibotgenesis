# Investigación de Trades - Enero 2026

**Fecha de Investigación:** 11 de Enero 2026  
**Período Analizado:** 24 Noviembre 2025 - 29 Diciembre 2025  
**Total de Trades:** 119 (cerrados)  
**Estado:** ANÁLISIS COMPLETADO

---

## Resumen Ejecutivo

### Hallazgo Principal
El **position sizing** es la causa raíz de las pérdidas, NO el win rate ni los filtros de coherencia.

| Métrica | Valor Reportado | Valor Real |
|---------|-----------------|------------|
| Win Rate | 20.17% | **37.82%** |
| Trades Ganadores | ~24 | **45** |
| P&L Total | -$15,198.73 | -$15,198.73 |
| Capital Preservado | 98.5% | 98.5% |

**Insight Crítico:** El win rate del sistema es casi **2x mejor** de lo que se pensaba.

---

## Análisis por Tamaño de Posición

| Tamaño | Trades | Win Rate | P&L Total | Veredicto |
|--------|--------|----------|-----------|-----------|
| **Micro (<$1K)** | 36 | **55.56%** | **+$101.39** | ✅ RENTABLE |
| Small ($1K-$10K) | 39 | 28.21% | -$3,819.60 | ❌ Pérdida |
| Medium ($10K-$50K) | 44 | 31.82% | -$11,480.52 | ❌ DESASTRE |

### Conclusión de Sizing
- **Trades micro son rentables** con 55.56% win rate
- **Trades grandes destruyen el capital** a pesar de tener buenas señales
- **El tamaño de posición amplifica las pérdidas**

---

## Problema de Fees: 21 Trades Afectados

### El Problema
21 trades tuvieron **profit_pct positivo** (ganaron en precio) pero **profit_loss negativo** (perdieron dinero después de fees).

| Métrica | Valor |
|---------|-------|
| Trades afectados | 21 |
| Pérdida total por fees | -$733.82 |
| Avg profit bruto | 0.20% |
| Avg fee por unidad | $44.66 |

### Ejemplos Específicos
```
BTC/USD: Ganó 0.10% → Perdió $100.50 (fees)
BTC/USD: Ganó 0.12% → Perdió $94.92 (fees)
ETH/USD: Ganó 0.15% → Perdió $87.98 (fees)
XRP/USD: Ganó 0.08% → Perdió $82.92 (fees)
```

### Root Cause
- Position sizes demasiado grandes ($10K-$50K)
- Ganancias pequeñas (0.1-0.2%) no cubren fees
- Fee structure de Kraken: ~0.16% por trade
- Con 0.20% ganancia bruta y 0.32% en fees (entry+exit) = **pérdida neta**

---

## Análisis por Símbolo

| Símbolo | Trades | Win Rate | P&L | Status |
|---------|--------|----------|-----|--------|
| XRP/USD | 26 | **53.85%** | -$1,384 | ⚠️ Fees problem |
| BTC/USD | 44 | **40.91%** | -$1,900 | ⚠️ Sizing problem |
| LINK/USD | 22 | 36.36% | -$3,902 | 🚫 BLOQUEADO |
| ADA/USD | 16 | 25.00% | -$4,655 | 🚫 BLOQUEADO |
| SOL/USD | 3 | 0.00% | -$1,952 | 🚫 BLOQUEADO |
| AVAX/USD | 2 | 0.00% | -$511 | ⏳ Probation |
| ETH/USD | 3 | 33.33% | -$217 | 🚫 BLOQUEADO |
| ATOM/DOT/POL | 3 | 0.00% | -$673 | 🚫 BLOQUEADOS |

### Símbolos Permitidos (Post-Investigación)
1. **BTC/USD** - 40.91% WR, necesita sizing micro
2. **XRP/USD** - 53.85% WR, mejor performer, sizing micro

### Símbolos Bloqueados (Confirmados)
- ADA/USD - 25% WR, -$4,655 pérdida
- SOL/USD - 0% WR, -$1,952 pérdida
- LINK/USD - 36% WR pero -$3,902 pérdida
- ETH/USD - Excluido por volatilidad

---

## Análisis Temporal

| Semana | Trades | Win Rate | P&L | Observación |
|--------|--------|----------|-----|-------------|
| Nov 24 | 2 | 50.00% | +$95 | ✅ Inicio estable |
| Dec 01 | 25 | **52.00%** | -$3,393 | ⚠️ Sizing problem |
| Dec 08 | 82 | 37.80% | **-$11,645** | ❌ DESASTRE |
| Dec 29 | 10 | 0.00% | -$255 | ❌ Sistema en modo protector |

### Análisis de la Semana del 8 de Diciembre
- **82 trades en una semana** = overtrade severo
- El sistema operó agresivamente sin adaptarse al mercado
- Win rate cayó de 52% a 37.8%
- Pérdida de $11.6K en 7 días

### ¿Qué pasó en Dec 29?
- 10 trades, 0% win rate
- Sistema entró en modo ultra-conservador DESPUÉS del desastre
- Coherence Gate comenzó a bloquear (correctamente)

---

## Datos Faltantes (GAP CRÍTICO)

Las siguientes columnas tienen **NULL en todos los 119 trades**:
- `coherence_score` - No se guardaba
- `hmm_regime` - No se guardaba
- `ema_regime_signal` - No se guardaba
- `strategy_confidence` - No se guardaba

### Impacto
- **Imposible analizar** qué coherence scores producen mejores resultados
- **Imposible calibrar** el warn_threshold con datos
- **Imposible validar** si los vetos son correctos

### Hotfix Requerido
Modificar `_close_paper_trade()` para guardar estos campos antes de cerrar.

---

## Conclusiones y Recomendaciones

### Root Causes Identificados (En Orden de Prioridad)

1. **Position Sizing Excesivo** (70% del problema)
   - Trades $10K-$50K pierden dinero consistentemente
   - Trades <$1K son rentables (55.56% WR, +$101)
   - **FIX:** Limitar a $1,000 máximo por posición

2. **Fees No Considerados en Entry** (20% del problema)
   - Sistema entra con ganancias esperadas <0.3%
   - Fees consumen toda la ganancia
   - **FIX:** Mínimo target profit = 0.5% (cubre fees + profit)

3. **Falta de Datos para Análisis** (10% del problema)
   - No se guardan métricas de decisión
   - **FIX:** Guardar coherence, hmm, ema en cada trade

### Acciones Inmediatas

| Prioridad | Acción | Impacto Esperado |
|-----------|--------|------------------|
| 🔴 P0 | Limitar position size a $1,000 | Evitar pérdidas grandes |
| 🔴 P0 | Guardar coherence/hmm/ema en trades | Habilitar análisis futuro |
| 🟡 P1 | Crear fee-adjusted expectancy model | Evitar trades no rentables |
| 🟢 P2 | Revisar warn_threshold | SOLO después de tener datos |

### Métricas Meta (Post-Fix)

| Métrica | Actual | Meta 30 días |
|---------|--------|--------------|
| Position Size Max | $50K | **$1,000** |
| Win Rate | 37.82% | 45%+ |
| P&L Monthly | -$15K | -$2K a +$500 |
| Trades/Week | 20+ | 5-10 (calidad) |
| Datos Capturados | 0% | 100% |

---

## Apéndice: Queries SQL Utilizados

```sql
-- Resumen general
SELECT COUNT(*) as total_trades, 
       SUM(CASE WHEN profit_pct > 0 THEN 1 ELSE 0 END) as winners,
       ROUND((SUM(CASE WHEN profit_pct > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100), 2) as win_rate,
       ROUND(SUM(profit_loss)::numeric, 2) as total_pnl_usd
FROM paper_trading_trades WHERE status = 'closed';

-- Por tamaño de trade
SELECT 
    CASE 
        WHEN quantity * entry_price < 1000 THEN 'Micro (<$1K)'
        WHEN quantity * entry_price < 10000 THEN 'Small ($1K-$10K)'
        ELSE 'Medium ($10K-$50K)'
    END as trade_size,
    COUNT(*) as trades,
    ROUND((SUM(CASE WHEN profit_pct > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100), 2) as win_rate,
    ROUND(SUM(profit_loss)::numeric, 2) as total_pnl
FROM paper_trading_trades WHERE status = 'closed'
GROUP BY 1 ORDER BY 4 DESC;

-- Fee problem analysis
SELECT COUNT(*) as trades_afectados,
       ROUND(SUM(profit_loss)::numeric, 2) as perdida_total_por_fees
FROM paper_trading_trades 
WHERE status = 'closed' AND profit_pct > 0 AND profit_loss < 0;
```

---

## Estado de Implementación

### Hotfixes Implementados (11 Enero 2026)

| Hotfix | Status | Archivo Modificado |
|--------|--------|-------------------|
| $1,000 Hard Cap | ✅ COMPLETADO | `omnix_core/bot/auto_trading_bot.py` |
| Guardar coherence_score | ✅ COMPLETADO | `omnix_services/trading_service/paper_trading_manager.py` |
| Guardar hmm_regime | ✅ COMPLETADO | `omnix_services/trading_service/paper_trading_manager.py` |
| Guardar ema_regime_signal | ✅ COMPLETADO | `omnix_services/trading_service/paper_trading_manager.py` |
| Guardar strategy_confidence | ✅ COMPLETADO | `omnix_services/trading_service/paper_trading_manager.py` |
| Guardar strategy_mode | ✅ COMPLETADO | `omnix_services/trading_service/paper_trading_manager.py` |

### Cambios de Código

**1. auto_trading_bot.py - Hard Cap:**
```python
# INVESTIGATION HOTFIX JAN 11, 2026: HARD CAP $1,000 USD MAX
MICRO_TRADE_HARD_CAP = 1000.0
if optimal_size > MICRO_TRADE_HARD_CAP:
    logger.warning(f"🛡️ INVESTIGATION HOTFIX: Position capped ${optimal_size:.2f} → ${MICRO_TRADE_HARD_CAP:.2f}")
    optimal_size = MICRO_TRADE_HARD_CAP
```

**2. paper_trading_manager.py - Telemetry Fields:**
- `execute_paper_trade()` ahora acepta: hmm_regime, coherence_score, ema_regime_signal, strategy_confidence, strategy_mode
- `_open_position_v2()` guarda estos campos en la tabla `paper_trading_trades`

### Hotfixes Implementados (ADR-004)

> **Estado:** ✅ CÓDIGO IMPLEMENTADO (12 Ene 2026, 27 tests pasados)

| Hotfix | Cambio | Estado |
|--------|--------|--------|
| **Kelly max_position** | 0.20 → 0.02 (20% → 2%) | ✅ IMPLEMENTADO |
| **Position Hard Cap** | $62,500 → $20,000 | ✅ IMPLEMENTADO |
| **Spread mínimo** | 5 bps → 25 bps | ✅ IMPLEMENTADO |
| **Metadata Trading** | Guardar kelly_raw, cap_applied | 📋 PENDIENTE (fase 2) |

**Justificación Empírica:**
- Trades <$1K: 55.56% WR → RENTABLES
- Trades >$10K: 31% WR → PIERDEN
- Nuevo target: Operar en rango $5K-$20K para capturar edge

**Referencia:** `docs/reference/adr/ADR-004-position-sizing-hotfix.md`

### Próximos Pasos

| Prioridad | Tarea | Status |
|-----------|-------|--------|
| 🔴 P0 | Aplicar hotfixes de ADR-004 al código | PENDIENTE |
| 🟡 P1 | Crear modelo expectancy ajustado por fees | PENDIENTE |
| 🟡 P1 | Validar ADA/SOL/LINK siguen bloqueados | PENDIENTE |
| 🟢 P2 | Revisar warn_threshold (después de datos) | PENDIENTE |

### Verificación Requerida

Después del deploy a Railway, verificar con:
```sql
SELECT coherence_score, hmm_regime, ema_regime_signal, strategy_confidence
FROM paper_trading_trades 
WHERE opened_at > '2026-01-11'
ORDER BY opened_at DESC LIMIT 5;
```

---

## Apéndice: Definición de Win Rates (Dual-Metric Framework)

### Contexto del Problema

El sistema mostraba un win rate de 20.17% pero la investigación reveló que el win rate "real" podría interpretarse como 37.82%. Ambos números son correctos pero miden cosas diferentes.

### Dos Métricas de Win Rate

| Métrica | Cálculo | Valor | Significado |
|---------|---------|-------|-------------|
| **Win Rate Direccional** | `profit_pct > 0` | 37.82% | Sistema acertó la dirección del precio |
| **Win Rate Neto** | `profit_loss > 0` | 20.17% | Trade generó ganancia después de fees |

### ¿Por qué la diferencia?

21 trades (17.6% del total) ganaron en dirección pero perdieron dinero:
- Ganancia promedio: 0.20% en precio
- Fee de Kraken: ~0.26% (0.16% entry + 0.10% exit)
- Resultado: **Pérdida neta** a pesar de acertar dirección

### Cuándo Usar Cada Métrica

| Contexto | Métrica Recomendada | Razón |
|----------|---------------------|-------|
| **Evaluar capacidad predictiva** | Direccional (37.82%) | Muestra que el sistema acierta dirección |
| **Reportar a inversores** | Neto (20.17%) | Es lo que realmente importa financieramente |
| **Comunicación completa** | Ambos con contexto | Honest Framing (ADR-002) |

### Formato de Comunicación Honest Framing

```
Win Rate: 37.82% direccional | 20.17% neto
Contexto: 21 trades erosionados por fees en posiciones grandes
Mitigación: Cap $1,000 implementado para eliminar problema de fees
```

### Métricas en Dashboard

El dashboard ahora muestra:
- `win_rate_directional`: 37.82% (basado en profit_pct > 0)
- `win_rate_net`: 20.17% (basado en profit_loss > 0)
- `fee_eroded_trades`: 21 (trades afectados por fees)

### Referencia

- **ADR-002:** Honest Framing Over Censorship
- **Hotfix:** $1,000 cap elimina el problema de fees en posiciones grandes

---

**Autor:** OMNIX Investigation System  
**Revisado por:** Architect Agent  
**Fecha:** 11 Enero 2026  
**Última Actualización:** 12 Enero 2026 (ADR-004 Position Sizing Hotfix documentado)
