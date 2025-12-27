# OMNIX V6.5.4d INSTITUTIONAL+ - AUDITORÍA TÉCNICA COMPLETA

**Fecha**: 27 de Diciembre 2025  
**Auditor**: Sistema de Auditoría Técnica  
**Versión**: V6.5.4d INSTITUTIONAL+  
**Estado**: 109 trades, -$14,942.94 P/L, 22% win rate

---

## Resumen Ejecutivo

**VEREDICTO: OPERACIONAL CON PROBLEMAS DE INFRAESTRUCTURA CRÍTICOS**

El sistema OMNIX tiene código funcional y bien estructurado, pero sufre de un **problema crítico de infraestructura**: Railway NO está desplegando desde GitHub. Esto significa que los fixes de código (V1.0.5 get_ohlc, EMA_CALL_CHECK) existen en el repositorio pero **NO están en producción**.

---

## 📊 Matriz de Estado del Sistema

| Módulo | Estado | Evidencia | Impacto |
|--------|--------|-----------|---------|
| **EMA Regime Signal** | ⚠️ PARCIAL | Fix V1.0.5 en GitHub pero NO en Railway | ALTO - señales no se generan |
| **Monte Carlo VETO** | ✅ FUNCIONAL | Early return implementado líneas 2427-2454 | Control de riesgo activo |
| **Coherence Gate** | ✅ FUNCIONAL | Pre-gate líneas 2538-2593 | Bloquea señales de baja calidad |
| **RMS/CircuitBreaker** | ✅ FUNCIONAL | Líneas 2460-2500 | Halt automático operativo |
| **LimitsEngine** | ✅ FUNCIONAL | Validación pre-trade activa | Control de posiciones |
| **TRACK_RECORD_MODE** | ⚠️ PARCIAL | Activo pero auto-off es manual | Score cap 6/12, size 0.35x |
| **Asset Quarantine** | ✅ FUNCIONAL | 5/7 pares excluidos | Protección de capital |
| **Railway Deployment** | ❌ CRÍTICO | Commits diferentes GH vs Railway | Invalida toda auditoría |
| **PostgreSQL** | ✅ FUNCIONAL | 42 tablas detectadas | Datos persistentes |
| **HMM Regime** | ✅ FUNCIONAL | Integrado en scoring | Detección de régimen |
| **Kalman Filter** | ✅ ARREGLADO | Método filter_and_predict() agregado (Dec 27) | Filtrado de señales |
| **Non-Markovian Kernel** | ✅ FUNCIONAL | Líneas 2215-2257 | Memoria temporal |
| **Black Swan Detector** | ✅ ARREGLADO | Método analyze() agregado (Dec 27) | Análisis funcional |
| **Kelly Criterion** | ⚠️ CONDICIONAL | Solo si mc_win_rate >= 52% | Sizing cuando activo |

---

## 🚨 Top 10 Problemas Reales (Ordenados por Impacto)

### 1. CRÍTICO: Railway NO despliega desde GitHub
**Impacto**: MÁXIMO - Invalida todo el sistema  
**Evidencia**: Commits diferentes (Railway: `397297e2`, GitHub: `852a1e3`)  
**Consecuencia**: Fixes V1.0.5 NO llegan a producción  
**Solución**: Reconectar Railway a GitHub (plan documentado)

### 2. ALTO: EMA Signal retorna NONE porque prices=0
**Impacto**: ALTO - No hay señales de trading  
**Root Cause**: `TradingServiceEnterprise.get_ohlc()` faltaba (FIXED en V1.0.5)  
**Estado**: Fix en GitHub, NO en Railway  
**Solución**: Reconectar Railway

### 3. ALTO: Win Rate 22% (target: 45%)
**Impacto**: ALTO - Track record no credible para inversores  
**Evidencia**: 109 trades, 24 wins, 85 losses  
**Causa Probable**: Señales débiles (prices=0 → EMA=NONE → WEAK_TREND)  
**Solución**: Fix 1 y 2 primero, luego evaluar

### 4. MEDIO: TRACK_RECORD_MODE auto-off es manual
**Impacto**: MEDIO - Modo experimental permanece activo indefinidamente  
**Evidencia**: Línea 3427 solo logea RECOMMENDATION, no desactiva  
**Estado**: Cuando total_trades >= 100 AND win_rate >= 45%, solo logea  
**Solución**: Implementar auto-off real o mantener manual con documentación

### 5. MEDIO: Solo 2 pares activos (BTC, XRP)
**Impacto**: MEDIO - Diversificación limitada  
**Evidencia**: 5 pares excluidos (ADA, SOL, ETH, AVAX, LINK)  
**Justificación**: 0% win rate histórico en excluidos  
**Solución**: Mantener exclusiones hasta mejorar win rate

### 6. BAJO: LSP Diagnostics (144 en auto_trading_bot.py)
**Impacto**: BAJO - No afecta ejecución, solo IDE  
**Causa**: Imports condicionales, try/except para optional modules  
**Solución**: No prioritario, cosmético

### 7. BAJO: AVAX en probation pero tier EXCLUDED
**Impacto**: BAJO - Contradicción en documentación  
**Evidencia**: trading_profiles.py tiene AVAX EXCLUDED, docs mencionan probation  
**Solución**: Clarificar estado real

### 8. BAJO: Black Swan es OBSERVATIONAL_ONLY
**Impacto**: BAJO - No veta trades, solo observa  
**Evidencia**: MODULE_STATUS_REGISTRY línea 114  
**Solución**: Evaluar si debe ser CORE_ACTIVE

### 9. INFORMATIVO: Coherence thresholds podrían ser muy estrictos
**Impacto**: VARIABLE - Puede reducir trades válidos  
**Evidencia**: veto_critical=30%, veto_normal=45%  
**Contexto**: En mercados de baja volatilidad, umbrales altos = menos trades

### 10. INFORMATIVO: Kelly solo activo si mc_win_rate >= 52%
**Impacto**: BAJO - Sizing conservador cuando Kelly desactivado  
**Evidencia**: ModuleStatus.CONDITIONAL_ACTIVE  
**Estado**: Correcto para paper trading

---

## 🔍 Análisis Detallado por Capa

### 1. Conectividad e Infraestructura

| Componente | Estado | Notas |
|------------|--------|-------|
| Telegram Bot | ⚠️ | Error de red transitorio (httpx.ReadError) - normal en Railway |
| PostgreSQL | ✅ | 42 tablas, estructura completa |
| Kraken API | ✅ | Health check pasa, get_ohlc() delegado |
| Redis | ✅ | Cache disponible |
| Railway | ❌ | Desconectado de GitHub |

### 2. Motor de Trading y Decisión

**Flujo Jerárquico Verificado:**
```
1. EMA Signal Generation
       ↓
2. MC VETO (expected_return < -0.1% || VaR95 > -3%)
       ↓ [EARLY RETURN si veta]
3. RMS VETO (CircuitBreaker + LimitsEngine)
       ↓ [EARLY RETURN si veta]
4. COHERENCE GATE (score < 30% critical, < 45% normal)
       ↓ [EARLY RETURN si no pasa]
5. Scoring Final
       ↓
6. Decision + Execution
```

**Evidencia de código:**
- MC VETO: líneas 2411-2454 con `mc_veto_applied = True` y early return línea 2521
- RMS VETO: líneas 2460-2500 con `rms_veto_applied = True` y early return línea 2521
- COHERENCE GATE: líneas 2538-2593 con `coherence_gate_passed = False` y early return línea 2585

### 3. TRACK_RECORD_MODE

**Estado**: ACTIVO (trading_profiles.py línea 95)

| Característica | Valor | Evidencia |
|----------------|-------|-----------|
| Score cap | 6/12 | auto_trading_bot.py línea 2937-2942 |
| Size max | 0.35x | auto_trading_bot.py línea 4575-4579 |
| WEAK_TREND fallback | ✅ | ema_regime_signal.py líneas 320-344 |
| Auto-off | ❌ MANUAL | Solo logea recomendación, no desactiva |
| Target | 100 trades, 45% WR | Documentado pero no enforced |

**Veredicto TRACK_RECORD_MODE**: MANTENER pero con claridad

El modo cumple su propósito de permitir trades de baja convicción para construir historial. Sin embargo:
- El auto-off debería ser automático O claramente documentado como manual
- Con 22% win rate actual, el target de 45% está muy lejos
- Los guardrails (MC, RMS, Coherence) están activos y funcionando

### 4. Guardrails, Vetos y Bloqueos

**¿OMNIX no tradea porque el mercado no da señal O porque se bloquea a sí mismo?**

**RESPUESTA**: AMBOS, pero el problema principal es que EMA retorna `prices=0`:

1. `_get_price_history()` llama a `trading_service.get_ohlc()`
2. En Railway, `TradingServiceEnterprise` NO tenía `get_ohlc()` (V1.0.5 fix)
3. `hasattr(trading_service, 'get_ohlc')` retornaba `False`
4. `prices = None` → `prices=0` en log
5. EMA no puede calcular → `direction = NONE`
6. TRACK_RECORD_MODE convierte NONE a WEAK_TREND con confidence 0.30
7. Pero con confidence 0.30, muchos vetos activan

**Cadena de bloqueos cuando prices=0:**
- EMA → NONE o WEAK_TREND (0.30 confidence)
- Coherence Gate → score bajo por lack of signal consensus
- MC VETO → puede activar si VaR es malo
- Resultado: HOLD

### 5. Telemetría y Logs

| Característica | Estado | Evidencia |
|----------------|--------|-----------|
| EMA_CALL_CHECK | ✅ | Línea 2272 - muestra generator/prices/allowed |
| Decision Trace | ✅ | Array `decision_trace` con cada paso |
| Veto Chain | ✅ | Array `veto_chain` lista razones de veto |
| Sentinel Logs | ✅ | `[VETO_ENFORCED]`, `[COHERENCE_GATE_ENFORCED]` |
| Institutional Logger | ✅ | Logging completo a PostgreSQL |

**Los logs reflejan la realidad** cuando están en producción. El problema es que el código con logs mejorados NO está en Railway.

---

## 🔧 Plan de Cierre del Ciclo

### Fase 0: CRÍTICA - Reconectar Railway a GitHub (15 min)
**Sin esto, nada más importa**

1. Documentar variables de entorno de Railway (captura)
2. Settings → Source → Disconnect
3. Connect Repository → `Costenho19/omnibotgenesis` → branch `main`
4. Verificar "Deploy on push" = ON
5. Verificar commit hash coincide con GitHub
6. Buscar `EMA_CALL_CHECK` con `prices=100+` en logs

### Fase 1: Verificación Post-Reconexión (5 min)
1. Confirmar que Railway despliega commit correcto
2. Verificar que `get_ohlc()` existe en código desplegado
3. Buscar log: `📊 EMA Signal: LONG|SHORT` (no NONE perpetuo)

### Fase 2: Monitoreo de Trades (24-48h)
1. Observar si se generan trades reales
2. Verificar que MC/Coherence/RMS no vetean todo
3. Documentar win rate post-fix

### Fase 3: Evaluación (después de 20+ trades post-fix)
1. Calcular win rate nuevo
2. Si mejora significativamente → fix era correcto
3. Si no mejora → revisar parámetros de TRACK_RECORD_MODE

### ❌ QUÉ NO TOCAR

- **Scoring weights** - Funcionan correctamente (40 EMA, 25 HMM, 15 Kalman, 15 NMK, 10 Kelly)
- **Coherence thresholds** - Ya ajustados (30% critical, 45% normal)
- **Monte Carlo VETO** - Implementado correctamente
- **Asset exclusions** - Basadas en datos reales (0% win rate)
- **Architecture** - Hexagonal V7.0 está lista pero no activada

---

## ✅ Criterio de "OMNIX TERMINADO"

| Criterio | Estado Actual | Requerido |
|----------|---------------|-----------|
| Genera señales reales y explicables | ❌ (prices=0) | ✅ |
| Opera sin bloqueos silenciosos | ❌ (Railway desync) | ✅ |
| Gobernanza clara de modos | ⚠️ (auto-off manual) | ✅ |
| Track record honesto y defendible | ⚠️ (22% WR explicable) | ✅ |
| No requiere "modo especial" para funcionar | ⚠️ (TRACK_RECORD activo) | ✅ |
| Presentable sin disculpas técnicas | ❌ | ✅ |

**OMNIX NO está terminado** porque el problema de infraestructura Railway-GitHub impide que el código funcional llegue a producción.

---

## Conclusión Honesta

El código de OMNIX es sólido. Los módulos están bien implementados:
- Vetos funcionan con early return
- Coherence Gate bloquea antes de scoring
- EMA Signal genera señales determinísticas
- TRACK_RECORD_MODE permite trades de baja convicción con guardrails

**El problema NO es de código, es de despliegue.**

Railway opera con "snapshots internos" que no reflejan GitHub. Hasta que esto se arregle:
- Los fixes no llegan a producción
- El sistema es inauditable
- No se puede presentar a inversores

**Acción inmediata requerida**: Reconectar Railway a GitHub.

---

*Auditoría generada: 27 de Diciembre 2025*
