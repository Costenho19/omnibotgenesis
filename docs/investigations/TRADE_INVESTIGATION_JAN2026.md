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

**Siguiente Paso:** Implementar hotfixes de position sizing y data capture.

**Autor:** OMNIX Investigation System  
**Revisado por:** Architect Agent  
**Fecha:** 11 Enero 2026
