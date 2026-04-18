# Type Safety Hotfix - Coherence Engine

**Fecha:** 30 de Diciembre 2025  
**Severidad:** CRÍTICA (bloqueaba trades en producción)  
**Estado:** ✅ RESUELTO

---

## Resumen Ejecutivo

Error en producción `TypeError: '>=' not supported between instances of 'str' and 'int'` causaba que el Coherence Gate entrara en fail-closed, bloqueando todos los trades sin validación real.

**Root Cause:** `StrategySignal.signal` llegaba como string "BUY" en lugar del Enum `Signal.BUY` desde algún llamador upstream.

**Solución:** Normalización defensiva de tipos al inicio de todos los métodos del CoherenceEngine.

---

## Detalles Técnicos

### Error Original

```python
# En analyze_coherence()
bullish = [s for s in signals if s.signal.value > 0]
#                                 ^^^^^^^^
# Si s.signal es "BUY" (string), no tiene .value → AttributeError
# Si s.signal es comparado directamente con int → TypeError
```

### Solución Implementada

**Nuevas funciones en `omnix_services/coherence_service/coherence_engine.py`:**

#### 1. `normalize_signal(value)`
```python
def normalize_signal(value: Union[str, 'Signal', int, None]) -> 'Signal':
    """Convierte cualquier valor de señal a Enum Signal de forma segura."""
    if value is None:
        return Signal.HOLD
    if isinstance(value, Signal):
        return value
    if isinstance(value, int):
        try:
            return Signal(value)
        except ValueError:
            return Signal.HOLD
    if isinstance(value, str):
        signal_map = {
            'STRONG_BUY': Signal.STRONG_BUY,
            'BUY': Signal.BUY,
            'HOLD': Signal.HOLD,
            'SELL': Signal.SELL,
            'STRONG_SELL': Signal.STRONG_SELL,
            'NONE': Signal.HOLD,
            '': Signal.HOLD,
        }
        return signal_map.get(value.upper().strip(), Signal.HOLD)
    return Signal.HOLD
```

#### 2. `normalize_strategy_signal(s)`
```python
def normalize_strategy_signal(s: 'StrategySignal') -> 'StrategySignal':
    """Normaliza todos los campos de StrategySignal a tipos seguros."""
    return StrategySignal(
        name=str(s.name) if s.name else 'unknown',
        signal=normalize_signal(s.signal),
        confidence=max(0.0, min(1.0, safe_float(s.confidence, 0.0, 'confidence'))),
        strength=safe_float(s.strength, 0.0, 'strength'),
        reasoning=str(s.reasoning) if s.reasoning else ''
    )
```

#### 3. `safe_float()` mejorado
```python
# Ahora remueve '%' de strings numéricos
clean_value = value.strip().replace('%', '')
return float(clean_value)
```

### Puntos de Normalización

| Método | Línea | Cambio |
|--------|-------|--------|
| `analyze_coherence()` | Inicio | `signals = [normalize_strategy_signal(s) for s in signals]` |
| `validate_trade_coherence()` | Después de fallback | `signals = [normalize_strategy_signal(s) for s in signals]` |
| `_classify_coherence_level()` | Antes de comparaciones | `score = safe_float(score, 0.0, 'coherence_score')` |
| `get_coherence_emoji()` | Antes de comparaciones | `score = safe_float(score, 0.0, 'emoji_score')` |

---

## Tests Añadidos

**Archivo:** `tests/test_coherence_type_safety.py`

| Clase | Tests | Cobertura |
|-------|-------|-----------|
| `TestNormalizeSignal` | 8 | String BUY/SELL/HOLD, Enum passthrough, int, None, invalid |
| `TestNormalizeStrategySignal` | 2 | String signal, string confidence/strength |
| `TestCoherenceEngineTypeSafety` | 4 | analyze_coherence con strings, classify_level, emoji |
| `TestSafeFloat` | 2 | Remoción de '%', manejo de espacios |

**Total:** 16 tests pasando

---

## Verificación

```bash
python -m pytest tests/test_coherence_type_safety.py -v
# 16 passed in 0.35s
```

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `omnix_services/coherence_service/coherence_engine.py` | +60 líneas (normalize_*, safe_float mejorado) |
| `tests/test_coherence_type_safety.py` | Nuevo archivo (160 líneas) |

---

## Lecciones Aprendidas

1. **Fail-closed es bueno pero necesita normalización defensiva** - El Coherence Gate correctamente bloqueaba trades cuando ocurría una excepción, pero el bloqueo era por un bug de tipos, no por una señal real.

2. **Validar tipos en boundaries** - Los datos que llegan de otros componentes (estrategias, parsers) deben normalizarse antes de procesarse.

3. **Tests de tipo explícitos** - Añadir tests que específicamente prueben el manejo de tipos incorrectos previene regresiones.

---

## Próximos Pasos

- [x] Fix implementado
- [x] Tests añadidos
- [x] Documentación actualizada
- [ ] Identificar llamador upstream que envía strings (opcional - fix es defensivo)
- [ ] Monitorear logs de producción para detectar normalizaciones frecuentes
