# ADR-013: Investor Data Provider

**Status:** ✅ IMPLEMENTADO  
**Date:** 2026-01-16  
**Authors:** OMNIX Team  
**Reviewers:** Harold (Owner)

---

## Context

Durante sesiones de due diligence con inversores institucionales (family offices, VCs), el bot OMNIX no podía proporcionar datos SQL reales cuando se le pedían métricas específicas como:

- Expectancy segmentada por régimen/coherence
- Breakdown de fees y break-even calculation
- Comparación pre vs post-hotfix (ADR-007)
- Análisis por tamaño de trade

El bot respondía: "No puedo ejecutar esa query en tiempo real" - lo cual generaba desconfianza en inversores quant que esperaban acceso a datos verificables.

## Decision

Implementar un `InvestorDataProvider` que:

1. **Ejecuta queries SQL read-only** contra PostgreSQL
2. **Se activa automáticamente** cuando detecta contexto de inversor
3. **Devuelve datos formateados** que el AI puede citar directamente
4. **Mantiene transparencia** sobre origen de datos (REAL vs LEGACY_ESTIMATED)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ConversationalAIAdapter                    │
├─────────────────────────────────────────────────────────────┤
│  _fetch_real_market_data()                                   │
│    ├── _fetch_trade_performance()  [existing]               │
│    ├── _fetch_veto_data()          [existing]               │
│    └── _fetch_investor_data()      [NEW - ADR-013]          │
│              │                                               │
│              ▼                                               │
│   ┌─────────────────────────────────────────┐               │
│   │      InvestorDataProvider               │               │
│   ├─────────────────────────────────────────┤               │
│   │  get_segmented_expectancy()             │               │
│   │  get_fee_breakdown()                    │               │
│   │  get_pre_post_hotfix_stats()            │               │
│   │  get_trade_size_analysis()              │               │
│   │  get_data_quality_metrics()             │               │
│   │  _format_for_ai_prompt()                │               │
│   └─────────────────────────────────────────┘               │
│              │                                               │
│              ▼                                               │
│        PostgreSQL (read-only)                                │
└─────────────────────────────────────────────────────────────┘
```

## Triggers

El InvestorDataProvider se activa cuando detecta:

| Trigger | Ejemplo |
|---------|---------|
| Investor keywords | "family office", "AUM", "seed", "pre-money", "valuation" |
| Due diligence terms | "due diligence", "hedge fund", "term sheet" |
| Technical queries | "expectancy segmented", "fee breakdown", "pre hotfix" |
| Numbered questions | "1. ¿Cuál es el win rate? 2. ¿Cómo se calcula? 3. ..." (3+) |
| Long questions | 80+ palabras |

## Metrics Provided

### 1. Segmented Expectancy

```sql
SELECT hmm_regime, coherence_bucket, 
       COUNT(*), wins, losses, avg_win, avg_loss
FROM paper_trading_trades
WHERE status = 'closed'
GROUP BY hmm_regime, coherence_bucket
```

Formula: `E = (Win% × AvgWin) - (Loss% × |AvgLoss|)`

### 2. Fee Breakdown

- Kraken fee: 0.26% per side
- Fee-eroded trades: Trades que ganaron en dirección pero perdieron a fees
- Break-even calculation: Trade must move >0.52% to profit

### 3. Pre vs Post-Hotfix (ADR-007)

Compara métricas antes y después de la calibración del 14 de enero 2026:
- Win rate delta
- P&L delta
- Coherence score average

### 4. Trade Size Analysis (ADR-004)

Win rate por bucket de tamaño:
- MICRO (<$100)
- SMALL ($100-$1K)
- MEDIUM ($1K-$10K)
- LARGE ($10K+)

### 5. Data Quality

- % trades con telemetría REAL (post-Jan 15, 2026)
- % trades con telemetría LEGACY_ESTIMATED (backfilled)

## Output Format

El provider genera texto formateado listo para inyección en el prompt del AI:

```markdown
## INVESTOR DATA (Real PostgreSQL Queries - 2026-01-16 15:30)

### Segmented Expectancy (Last 90 Days)
- **Best Segment**: BULLISH + HIGH (70%+) → Expectancy: $12.50/trade
- **Global Expectancy**: $-2.30/trade
- **Total Trades Analyzed**: 119

### Fee Analysis (Kraken 0.26% per side)
- **Fee-Eroded Trades**: 21 (17.6%)
- **Break-Even Move Required**: >0.52% to profit

### Pre vs Post-Hotfix (ADR-007: 2026-01-14)
| Period | Trades | Win Rate | P&L |
|--------|--------|----------|-----|
| Pre-Hotfix | 119 | 20.17% | -$15,198.73 |
| Post-Hotfix | 0 | 0% | $0 |
```

## Security

- **Read-only**: Solo operaciones SELECT
- **No SQL injection**: Queries parametrizadas
- **No raw SQL exposure**: Usuario ve datos formateados, no queries

## Files Modified

| File | Change |
|------|--------|
| `omnix_services/ai_service/providers/investor_data_provider.py` | NEW - Provider completo |
| `omnix_services/ai_service/conversational_ai_adapter.py` | Integración _fetch_investor_data() |
| `docs/current/ARCHITECTURE.md` | Documentación del componente |
| `docs/reference/adr/ADR-013-investor-data-provider.md` | Este documento |

## Consequences

### Positive

- Inversores obtienen datos SQL reales verificables
- Bot puede responder preguntas de due diligence con tablas y cálculos
- Transparencia sobre origen de datos (REAL vs LEGACY)
- Reutiliza DatabaseGateway existente

### Negative

- Queries adicionales a PostgreSQL (mitigado: solo se ejecuta para investor context)
- Complejidad añadida al flujo de AI

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | Initial implementation |

---

## Related ADRs

- [ADR-004](ADR-004-position-sizing-hotfix.md): Trade size analysis insights
- [ADR-007](ADR-007-coherence-threshold-calibration.md): Pre/post hotfix comparison
- [ADR-009](ADR-009-brevity-first-policy.md): Investor questions get unlimited responses
- [ADR-011](ADR-011-legacy-telemetry-backfill.md): Data quality metrics
