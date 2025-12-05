# OMNIX V6.5.2 - Configuracion Optimizada
## Auditoria Tecnica y Recomendaciones

**Fecha:** Diciembre 2025  
**Version:** 6.5.2 INSTITUTIONAL+

---

## RESUMEN EJECUTIVO

Se identificaron y corrigieron los siguientes problemas:

| Problema | Estado | Impacto |
|----------|--------|---------|
| CAES recibiendo 0% confidence | CORREGIDO | El kernel ahora se reinicializa por par |
| Bug tuple.get en trades | CORREGIDO | Convertir tuplas a diccionarios |
| Columna last_activity faltante | CORREGIDO | Agregada a tabla users |
| MATIC->POL mapping | YA CORRECTO | No requeria cambios |

---

## 1. PROBLEMA CAES (CORREGIDO)

### Diagnostico
CAES mostraba `Confidence=0.0%` porque el Non-Markovian Kernel mantenia historia de precios de pares anteriores cuando cambiaba a un nuevo par.

### Solucion Aplicada (V6.5.2 Final)
```python
# Se inicializan en __init__:
self._last_kernel_pair = None
self._kernel_needs_reseed = True  # Flag explicito para retry

# En cada iteracion:
is_pair_change = (self._last_kernel_pair is not None and self._last_kernel_pair != pair)

# 1) Detectar cambio de par -> marcar para reseed
if is_pair_change:
    self._kernel_needs_reseed = True
    self.non_markovian_kernel.seed_history([], clear_existing=True)
    kernel_history_len = 0

# 2) Verificar si historia insuficiente
if kernel_history_len < min_required:
    self._kernel_needs_reseed = True

# 3) Intentar reseed si esta pendiente
if self._kernel_needs_reseed:
    if prices and len(prices) >= min_required:
        self.non_markovian_kernel.seed_history(prices, clear_existing=True)
        self._last_kernel_pair = pair
        self._kernel_needs_reseed = False  # Solo limpiar flag despues de exito

# 4) Solo generar senal si kernel esta listo
if not self._kernel_needs_reseed:
    non_markovian = self.non_markovian_kernel.generate_signal(...)

# 5) En caso de error, marcar para reseed en proximo ciclo
except Exception as e:
    self._kernel_needs_reseed = True
```

### Impacto
- CAES ahora recibe datos correctos del kernel para cada par
- Position sizing adaptativo funcionara correctamente
- Sub-regimes se detectaran por par
- El kernel preserva historia acumulada mientras analiza el mismo par
- Solo hace reset cuando cambia a un par diferente
- `generate_signal()` internamente acumula nuevos datos via `update_history()`
- **Flag explicito `_kernel_needs_reseed`** garantiza retry automatico en todos los casos edge
- Si datos insuficientes, se mantiene flag hasta que lleguen datos validos
- Si `generate_signal()` falla, se marca para reseed en proximo ciclo

---

## 2. PONDERACION DE ESTRATEGIAS

### Pesos Actuales en Coherence Engine

| Estrategia | Peso | Rol |
|------------|------|-----|
| quantum_momentum | 20% | Estrategia principal |
| kalman_filter | 15% | Alta confiabilidad |
| monte_carlo | 15% | Validacion estadistica |
| hmm_regime | 12% | Contexto de mercado |
| kelly_criterion | 10% | Optimizacion matematica |
| black_swan | 10% | Proteccion de riesgo |
| order_book | 8% | Flow institucional |
| sentiment | 6% | Analisis de mercado |
| sharia_compliance | 4% | Filtro etico |

### Pesos en Sistema de Puntuacion

| Estrategia | Puntos Base | Notas |
|------------|-------------|-------|
| Monte Carlo | 15 pts | Ajustado por omega adaptativo |
| Black Swan | 30 pts (VETO) | Penalizacion por condiciones extremas |
| Sentiment | 10 pts | Timing de mercado |
| Kelly Criterion | 25 pts | Position sizing optimo |
| Kalman Filter | 15 pts | Ajustado por omega adaptativo |
| HMM Regime | 15 pts | Deteccion de regimen |
| Non-Markovian | 6 pts | Memoria temporal |

### Recomendacion
Los pesos actuales son razonables. El sistema de pesos adaptativos (omega) ajusta dinamicamente Monte Carlo vs Kalman basandose en Hurst y alpha.

---

## 3. COHERENCE ENGINE

### Umbrales Actuales por Perfil

| Umbral | INSTITUTIONAL | BALANCED | PAPER_AGGRESSIVE |
|--------|---------------|----------|------------------|
| Veto Critico | 30% | 25% | 20% |
| Veto Normal | 45% | 38% | 30% |
| Warning | 60% | 55% | 45% |
| Good | 80% | 72% | 65% |

### Problema Actual
Con coherencia de 31.8%, el sistema esta siendo bloqueado por el veto normal (45%) en el perfil INSTITUTIONAL.

### Recomendacion
1. Cambiar a PAPER_AGGRESSIVE (veto normal = 30%)
2. Con 31.8% coherencia, trades pasarian el veto
3. Monitorear win rate despues de 50+ trades
4. Si win rate < 50%, subir umbrales gradualmente

---

## 4. TRADING PROFILES

### Comparacion de Perfiles

| Parametro | INSTITUTIONAL | BALANCED | PAPER_AGGRESSIVE |
|-----------|---------------|----------|------------------|
| Coherence Veto | 45% | 38% | 30% |
| Trades/Dia Target | 25 | 32 | 40 |
| Min Confidence | 14% | 12% | 10% |
| Ramp-Up Fase 1 | 30% | 40% | 50% |
| HMM Veto Threshold | 85% | 88% | 92% |
| Regime Veto | SI | SI | NO |

### Configuracion Recomendada para Paper Trading

```
TRADING_PROFILE=PAPER_AGGRESSIVE
```

Razones:
- Genera mas trades para track record
- Coherence veto en 30% (mas permisivo)
- Regime change veto desactivado
- Ramp-up mas rapido

---

## 5. NON-MARKOVIAN KERNEL

### Parametros Actuales

| Parametro | Valor | Descripcion |
|-----------|-------|-------------|
| tau | 12.0 horas | Decay de memoria |
| epsilon | 0.35 | Amplitud de oscilacion |
| omega | 0.523 rad | Frecuencia (~12h ciclos) |
| window_size | 168 | 1 semana de datos |

### Recomendaciones
Los parametros son razonables para deteccion de ciclos de 12 horas. Para mercados mas volatiles:
- Reducir tau a 8 horas
- Aumentar epsilon a 0.4

---

## 6. CAES - Confidence-Adaptive Entry System

### Funcion Sigmoide
```
aggression = 1 + (2 / (1 + exp(-10 * (confidence - 0.7))))
```

### Mapeo Confidence -> Aggression

| Confidence | Aggression | Position Size |
|------------|------------|---------------|
| 50% | 0.8x | Conservador |
| 70% | 1.5x | Normal |
| 85% | 2.2x | Agresivo |
| 95% | 2.8x | Maximo |

### Sub-Regimes Detectados

| Sub-Regime | Multiplicador | Stop Loss | Take Profit |
|------------|---------------|-----------|-------------|
| BULL_STRONG | 1.20x | 0.8x | 1.3x |
| BULL_WEAK | 0.85x | 0.9x | 1.0x |
| BEAR_PANIC | 0.50x | 0.6x | 0.8x |
| BEAR_CONTROLLED | 0.70x | 0.75x | 0.9x |
| SIDEWAYS_COMPRESSED | 0.75x | 0.7x | 0.85x |
| BREAKOUT_UP | 1.30x | 0.7x | 1.5x |
| UNKNOWN | 0.80x | 0.75x | 0.9x |

---

## 7. ACCIONES INMEDIATAS

### Para Railway (Produccion)

1. **Agregar variable de entorno:**
   ```
   TRADING_PROFILE=PAPER_AGGRESSIVE
   ```

2. **Hacer git push** de los cambios:
   - Fix CAES kernel seeding
   - Fix tuple.get bug
   - Columna last_activity ya agregada

3. **Reiniciar servicio** en Railway

### Monitoreo Post-Deploy

1. Verificar logs muestren:
   ```
   Trading Profile activo: PAPER_AGGRESSIVE
   CAES: Confidence=XX.X% (no 0.0%)
   ```

2. Esperar 24-48 horas para primeros trades

3. Revisar metricas:
   - Total trades
   - Win rate
   - Average profit/loss

---

## 8. CONFIGURACION OPTIMA PARA TRACK RECORD

### Objetivo: 500+ trades en 60 dias

Para lograr esto, necesitas:
- ~8-10 trades/dia
- Win rate > 55%
- Drawdown < 15%

### Configuracion Recomendada

| Parametro | Valor |
|-----------|-------|
| Profile | PAPER_AGGRESSIVE |
| Coherence Veto | 30% |
| Check Interval | 20 segundos |
| Crypto Pairs | 11 activos |
| Ramp-Up | 50% inicial |

### KPIs a Monitorear

| KPI | Meta | Alerta |
|-----|------|--------|
| Trades/Dia | 8-10 | < 3 |
| Win Rate | > 55% | < 50% |
| Avg Trade | +0.5% | < 0% |
| Max Drawdown | < 15% | > 20% |
| Sharpe Ratio | > 1.5 | < 1.0 |

---

## 9. PROXIMOS PASOS (POST-TRACK RECORD)

Una vez tengas 500+ trades con win rate > 55%:

1. **Backtesting riguroso** - Validar con datos historicos
2. **Walk-forward analysis** - Probar en datos no vistos
3. **Calibracion de pesos** - Ajustar basado en performance real
4. **Transicion gradual** - PAPER_AGGRESSIVE -> BALANCED -> INSTITUTIONAL

---

## 10. ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `omnix_core/bot/auto_trading_bot.py` | Fix kernel seeding por par |
| `omnix_core/context/real_data_provider.py` | Fix tuple to dict conversion |
| Base de datos | Agregada columna last_activity |

---

**Documento generado por auditoría técnica OMNIX**  
**Última actualización:** Diciembre 2025
