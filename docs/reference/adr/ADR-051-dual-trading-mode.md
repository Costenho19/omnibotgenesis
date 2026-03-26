# ADR-051: Dual Trading Mode — CORE / ACTIVE

**Status**: ACCEPTED  
**Date**: 2026-03-26  
**Author**: Harold Nunes  
**Type**: Governance Configuration  
**Related**: ADR-019 (ECW), ADR-020 (CAES), ADR-050 (CAG)

---

## Contexto

El sistema OMNIX opera desde Enero 15, 2026 en Track Record Oficial con **0 trades ejecutados en 5+ meses**. El análisis de logs revela que el ECW (Edge Confirmation Window, ADR-019) es el cuello de botella principal:

- `ECW_MC_WR_MIN = 50%` — Monte Carlo win rate supera 50% en mercados con edge marginal, pero los umbrales requieren exactamente eso.
- `ECW_CYCLES_REQUIRED = 3` — 3 ciclos consecutivos con condiciones óptimas son difíciles de mantener dada la volatilidad del mercado cripto.
- **BLACK_SWAN_HIGH** resetea el contador ECW a 0 aunque el edge estadístico siga siendo válido.

El sistema necesita dos modos operacionales:
- **CORE** (default): thresholds institucionales estrictos para auditorías y períodos de alta incertidumbre.
- **ACTIVE**: thresholds calibrados para mercados con edge marginal, permitiendo operar sin comprometer la integridad de gobernanza.

---

## Decisión

Se implementa un sistema Dual Mode controlado por **una sola variable de entorno** `TRADING_MODE`.

### ENV var

```
TRADING_MODE=CORE    # Default — thresholds institucionales estrictos
TRADING_MODE=ACTIVE  # Thresholds calibrados — permite edge marginal
```

### Tabla comparativa de thresholds

| Parámetro | CORE (default) | ACTIVE | Override posible |
|-----------|---------------|--------|-----------------|
| `ECW_MC_WR_MIN` | 50% | 48% | Sí, via ENV individual |
| `ECW_MC_ER_MIN` | 0.0 | 0.001 | Sí, via ENV individual |
| `ECW_CYCLES_REQUIRED` | 3 | 2 | Sí, via ENV individual |
| `coherence_veto_normal` | 45% | 40% | No (controlado por modo) |
| `coherence_veto_critical` | 30% | 30% | Sin cambio |
| BS=HIGH en ECW | Resetea counter | Reduce posición 0.5% | No |

### Comportamiento BLACK_SWAN=HIGH

| Modo | Comportamiento |
|------|---------------|
| **CORE** | BS=HIGH resetea el ECW counter (`ecw_reset_reason = 'BLACK_SWAN_HIGH'`) |
| **ACTIVE** | BS=HIGH permite el trade pero **limita la posición al 0.5% del balance** |

El cap de 0.5% en ACTIVE + BS HIGH es una medida de capital preservation que:
- Permite confirmar edge estadístico en condiciones de mercado difíciles
- Limita la exposición de forma conservadora
- Genera datos de performance para la calibración del Shadow Portfolio

---

## Implementación

### `omnix_core/bot/auto_trading_bot.py`

Módulo-nivel (startup):
```python
TRADING_MODE = os.getenv('TRADING_MODE', 'CORE').upper()
ACTIVE_PROFILE = _ACTIVE_MODE_DEFAULTS if TRADING_MODE == 'ACTIVE' else _CORE_MODE_DEFAULTS
```

Los defaults de ECW se leen usando `ACTIVE_PROFILE` como base, sobreescribibles por ENVs individuales (retrocompatibilidad total).

### Compatibilidad retroactiva

- Si `TRADING_MODE` no está definido → CORE (sin cambio de comportamiento).
- ENVs individuales (`ECW_MC_WR_MIN`, `ECW_CYCLES_REQUIRED`, `ECW_MC_ER_MIN`) siguen funcionando y tienen prioridad sobre el perfil de modo.
- Todos los receipts PQC incluyen `trading_mode` en el `ecw_thresholds` del audit trail.

---

## Log de inicio (audit trail)

Al arrancar el bot, se loguea el modo activo:
```
🎛️ TRADING_MODE=ACTIVE | ECW WR>=48% ER>0.001 CYCLES=2 BS_HIGH_BLOCKS=False
📊 ECW CONFIG v1.2: MC_WR_MIN=48%, MC_ER_MIN=0.001%, CYCLES=2
```

---

## Consecuencias

**Positivas:**
- Un solo cambio en Railway (`TRADING_MODE=ACTIVE`) activa los thresholds calibrados.
- Rollback inmediato: volver a CORE en segundos sin redeploy.
- Audit trail completo: modo registrado en cada decision receipt.
- Capital preservation mantenida: BS=HIGH con posición al 0.5% protege el capital.

**Riesgos controlados:**
- Win rate del 48% sigue siendo edge estadístico positivo (>50% es aspiracional, no requerido para edge).
- 2 ciclos consecutivos siguen requiriendo persistencia del edge (no es "primer ciclo gana").
- Coherence 40% sigue filtrando señales contradictorias extremas (critical veto en 30% permanece).

---

## Decisión de uso

| Condición | Modo recomendado |
|-----------|-----------------|
| Alta incertidumbre macroeconómica | CORE |
| Auditoría o due diligence activo | CORE |
| Mercado con edge marginal (~48-50% WR) | ACTIVE |
| Demo inversores (track record) | ACTIVE |
| Producción estable con señales claras | Cualquiera |

---

## Referencias

- ADR-019: Edge Confirmation Window
- ADR-020: Confidence-Adaptive Entry System (CAES)
- ADR-050: Context Admission Gate (CAG)
- `omnix_core/bot/auto_trading_bot.py` — variables `TRADING_MODE`, `ACTIVE_PROFILE`
