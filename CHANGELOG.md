# OMNIX V6.5.4 INSTITUTIONAL+ - Changelog

Registro de cambios, correcciones y mejoras del sistema.

---

## [2025-12-04] - Documentation Consolidation & Database Optimization

### Documentation Cleanup
| Action | File | Reason |
|--------|------|--------|
| DELETED | `scripts/README.md` | Empty placeholder |
| DELETED | `docs/core/PROJECT_STRUCTURE.md` | Duplicate of TECHNICAL_REFERENCE |
| DELETED | `docs/core/MIGRATION_GUIDE.md` | Covered by deployment docs |
| DELETED | `omnix_dashboard/ARCHITECTURE.md` | Duplicate of DASHBOARD_TECHNICAL_REFERENCE |
| DELETED | `omnix_testing/PREMIUM_VALIDATION_README.md` | Outdated V6.0, covered by README.md |

### Database Table Consolidation
| Table Dropped | Reason |
|---------------|--------|
| `circuit_breaker_states` | Duplicate of `circuit_breaker_status` |
| `risk_guardian_logs` | Duplicate of `risk_guardian_events` |
| `trading_history` | Duplicate of `paper_trading_trades` |

**Result:** 45 → 42 tables, 38 FKs (90% coverage)

### Legacy Code Cleanup
| Action | Location | Result |
|--------|----------|--------|
| DELETED | `omnix_core/models/` | Empty folder removed |
| DELETED | `omnix_core/queue/` | Empty folder removed |
| DELETED | `omnix_services/trading_service/pqc_security.py` | 162-line duplicate removed |
| FIXED | `omnix_core/strategies/__init__.py` | Added exports |
| FIXED | `omnix_core/security/__init__.py` | Added exports |
| FIXED | `omnix_services/__init__.py` | Added exports |

### Dependency Updates
| Package | Old | New | Risk |
|---------|-----|-----|------|
| anthropic | 0.51.0 | 0.75.0 | LOW |
| python-telegram-bot | 20.7 | 21.9 | LOW |
| psycopg | 3.2.4 | 3.3.1 | LOW |
| pandas | 2.2.2 | 2.2.3 | LOW |
| scipy | 1.14.0 | 1.14.1 | LOW |
| ccxt | 4.4.35 | 4.5.24 | MEDIUM |
| httpx | 0.27.0 | 0.27.2 | LOW |

### References Updated
- `docs/README.md` - Fixed table counts (45→42)
- `docs/core/Omnix_TECHNICAL_REFERENCE.md` - FK coverage updated (90%)
- `replit.md` - Dec 2025 changes documented

---

## [2025-12-02] - ARES Strategies Import Fix

### Bug Critico Resuelto

**Problema**: El auto-trading estaba completamente detenido porque las estrategias ARES V1 y V2 no cargaban. El sistema mostraba `ARES_STRATEGIES_AVAILABLE = False`.

**Causa Raiz**: Los nombres de clase en los imports no coincidian con las clases reales definidas en los archivos de estrategia.

| Import Incorrecto | Clase Real |
|-------------------|------------|
| `AresQuantumProtocol` | `AresProtocolV1` |
| `AresScalpingV2` | `AresProtocolV2` |

### Archivos Corregidos (6)

| Archivo | Cambio |
|---------|--------|
| `main.py` | Import principal y fallback (lineas 256-274) |
| `omnix_core/trading_system.py` | Instanciacion global (lineas 5194-5195) |
| `omnix_core/strategies/ares_v1.py` | Bloque de test local (linea 644) |
| `omnix_core/strategies/ares_v2.py` | Bloque de test local (linea 546) |
| `omnix_testing/validate_ares_strategies.py` | Adaptadores de validacion (lineas 114-118, 165-169) |
| `omnix_testing/backtesting/backtesting_engine.py` | Imports de backtesting (lineas 30-35, 76-81) |

### Verificacion

```
✅ ARES QUANTUM PROTOCOLS LOADED:
   🧬 ARES V1: AresProtocolV1 (v1.1.0) - Win Rate 55%-65%
   🧨 ARES V2: AresProtocolV2 (v2.1.0) - Win Rate 60%-70%
✅ Instancias creadas correctamente
   V1 version: 1.1.0
   V2 version: 2.1.0
```

### Impacto

- El bot ahora puede generar senales de trading usando ambas estrategias ARES
- Requiere push a GitHub para deploy automatico en Railway
- El sistema volvera a ejecutar trades con las estrategias institucionales activas

### Estado

- [x] Codigo corregido
- [x] Verificacion de sintaxis pasada
- [x] Test de imports exitoso
- [ ] Push a GitHub pendiente
- [ ] Deploy en Railway pendiente

---

## Historial de Versiones

| Version | Fecha | Cambios Principales |
|---------|-------|---------------------|
| V6.5 | Dic 2024 | Adaptive Parameter Engine, On-Chain Intelligence |
| V6.4 | Nov 2024 | Portfolio INSTITUTIONAL+, Market Intelligence |
| V6.3 | Nov 2024 | Stock Trading ULTRA, Real Data Integration |
| V6.2 | Oct 2024 | RMS Memory-Enhanced, Derivatives |
| V6.1 | Oct 2024 | Non-Markovian Kernel, Coherence Engine |
| V6.0 | Sep 2024 | Multi-Exchange Arbitrage, Institutional Compliance |

---

*OMNIX V6.5 INSTITUTIONAL+ | Sistema de Trading Automatizado*
