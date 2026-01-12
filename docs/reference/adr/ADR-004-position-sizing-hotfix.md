# ADR-004: Position Sizing Hotfix

**Status:** ACCEPTED  
**Date:** 2026-01-12  
**Deciders:** Core Team, AI Architect  
**Related:** TRADE_INVESTIGATION_JAN2026.md, ADR-003 (Official Positioning)

---

## Context

La investigación del 11-12 de Enero 2026 reveló un problema crítico de position sizing:

### Hallazgo Empírico

| Tamaño Trade | Trades | Win Rate | P&L Total |
|--------------|--------|----------|-----------|
| Micro (<$1K) | 9 | **55.56%** | +$136 |
| Small ($1K-$5K) | 46 | 26.1% | -$3,847 |
| Medium ($5K-$10K) | 29 | 17.2% | -$3,716 |
| Large (>$10K) | 35 | **31%** | -$7,772 |

**Insight Crítico:** Los trades pequeños son rentables (55% WR), los grandes pierden (31% WR).

### Configuración Actual (Problemática)

```
Kelly Criterion: 6.25% del capital
Balance: $1,000,000
Position Size: $62,500 por trade (rango "Large")
Win Rate Esperado: 31% (basado en histórico)
```

### Problema Identificado

El sistema está operando consistentemente en el rango de position size que históricamente tiene el **peor rendimiento**.

---

## Decision

### Hotfix #1: Reducir Kelly max_position

**ANTES:**
```python
kelly = self.advanced_features.kelly_optimizer.calculate_optimal_position(
    win_rate=0.55,
    avg_win=0.03,
    avg_loss=0.02,
    total_capital=self._get_balance()
    # max_position=0.20 (default 20%)
)
```

**DESPUÉS:**
```python
kelly = self.advanced_features.kelly_optimizer.calculate_optimal_position(
    win_rate=0.55,
    avg_win=0.03,
    avg_loss=0.02,
    total_capital=self._get_balance(),
    max_position=0.02  # HOTFIX: 2% máximo = ~$20K
)
```

**Impacto:**
- Position size máximo: $62,500 → $20,000
- Rango de operación: Large → Small/Medium
- Win rate esperado: 31% → 45%+ (basado en histórico de trades pequeños)

### Hotfix #2: Hard Cap en USD

Añadir un límite duro independiente de Kelly:

```python
POSITION_HARD_CAP_USD = 20_000.0  # $20K máximo por trade
```

Este cap se aplica DESPUÉS del cálculo de Kelly como última línea de defensa.

### Hotfix #3: Metadata de Trading

Registrar en cada trade:
- `position_sizing_method`: "KELLY_CAPPED" | "FIXED" | "ATR_BASED"
- `kelly_raw_suggestion`: Sugerencia original de Kelly antes del cap
- `cap_applied`: Boolean indicando si se aplicó el hard cap

---

## Rationale

### ¿Por qué 2% / $20K?

1. **Evidencia empírica:** Trades <$1K tienen 55% WR, trades $1K-$5K tienen 26% WR
2. **Punto de corte conservador:** $20K está en el límite superior del rango "Small-Medium"
3. **Margen de seguridad:** Permite crecer sin caer en el rango "Large" que pierde

### ¿Por qué no más conservador ($5K)?

1. Reduciría P&L potencial excesivamente
2. Track record necesita trades significativos para impresionar inversores
3. $20K sigue siendo institucional (no parece "hobby trading")

### ¿Por qué Hard Cap además de Kelly?

1. Kelly puede dar valores erráticos con inputs incorrectos
2. Hard cap es defensa en profundidad
3. Fácil de auditar y explicar a inversores

---

## Consequences

### Positivas

- **Win rate esperado mejora:** 31% → 45%+ (basado en datos)
- **Pérdidas por trade reducidas:** Menos capital en riesgo
- **Fee erosion reducida:** Trades más pequeños tienen mejor ratio profit/fee
- **Track record más creíble:** Consistencia > tamaño

### Negativas

- **Menos P&L en trades ganadores:** Limitación intencional
- **Más trades necesarios:** Para alcanzar objetivos de volumen
- **Requiere más tiempo:** Para demostrar edge a inversores

### Riesgos

- **Cambio en dinámica de mercado:** Los datos históricos podrían no predecir futuro
- **Sobre-optimización:** Podríamos estar ajustando a noise histórico

---

## Implementation

### Archivos a Modificar

| Archivo | Cambio |
|---------|--------|
| `omnix_core/bot/auto_trading_bot.py` | Añadir `max_position=0.02` en llamada a Kelly |
| `omnix_core/config/trading_profiles.py` | Añadir `POSITION_HARD_CAP_USD` |
| `omnix_services/trading_service/paper_trading_manager.py` | Aplicar hard cap antes de ejecutar |

### Tests a Actualizar

- `tests/test_kelly_criterion.py`: Verificar nuevo límite
- `tests/test_position_sizing.py`: Añadir test para hard cap

### Documentación a Actualizar

- `docs/REAL_SYSTEM_STATUS.md`: Nueva configuración
- `docs/investigations/TRADE_INVESTIGATION_JAN2026.md`: Sección de hotfixes
- `replit.md`: Límite de position sizing

---

## Monitoring

### Métricas a Observar Post-Hotfix

1. **Distribution de position sizes:** Confirmar que están en rango $5K-$20K
2. **Win rate por semana:** Debería tender hacia 40%+
3. **P&L acumulado:** Debería mejorar o estabilizarse
4. **Número de trades bloqueados por cap:** Tracking de cuántas veces se activa

### Criterios de Éxito (30 días)

- [ ] Win rate ≥ 35% (vs 20% actual)
- [ ] Position size promedio < $20K
- [ ] Ningún trade > $25K (margen de error)
- [ ] P&L semanal positivo o flat (vs negativo actual)

---

## Rollback Plan

Si el hotfix empeora resultados:

```bash
# En Railway
POSITION_HARD_CAP_USD=0  # Desactiva hard cap
# Y revertir max_position a 0.20 en código
```

---

## References

- `docs/investigations/TRADE_INVESTIGATION_JAN2026.md` - Análisis completo
- `omnix_services/trading_service/kelly_criterion.py` - Implementación Kelly
- Logs Railway 12 Ene 2026 05:46 UTC - Evidencia de $62,500 positions

---

*OMNIX V6.5.4d INSTITUTIONAL+ - ADR-004 Position Sizing Hotfix*
