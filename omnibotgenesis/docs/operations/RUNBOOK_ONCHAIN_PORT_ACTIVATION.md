# Runbook: OnChainDataPort Activation

**Fecha**: 17 Dic 2025  
**Port**: OnChainDataPort  
**Feature Flag**: `USE_ONCHAIN_PORT`  
**Riesgo**: BAJO

---

## Descripción

El `OnChainDataPort` proporciona datos on-chain de blockchain para mejorar la inteligencia de trading:
- Métricas de red Bitcoin (hash rate, difficulty, volumen)
- Actividad de whales (transacciones grandes)
- Salud de la red (congestión, fees)
- Flujos de exchanges (futuro: Glassnode integration)

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│  OnChainDataPort (Protocol)                                  │
│  └── get_onchain_metrics(), get_whale_activity(),           │
│      get_network_health(), get_exchange_flows()              │
├─────────────────────────────────────────────────────────────┤
│  OnChainDataAdapter (Multi-provider con fallback)            │
│  ├── BlockchainInfoProvider (BTC, free, immediate)          │
│  ├── [Futuro] GlassnodeProvider (multi-chain, paid)         │
│  └── [Futuro] ArkhamProvider (entity tracking, paid)        │
├─────────────────────────────────────────────────────────────┤
│  Fallback: Legacy _get_on_chain_metrics() en analytics       │
│  Cooldown: 5 minutos después de fallo                        │
└─────────────────────────────────────────────────────────────┘
```

## Pre-requisitos

1. **Tests pasando**: `pytest tests/test_onchain_port.py -v` (24/24 tests)
2. **API disponible**: Blockchain.info no requiere API key
3. **Legacy funcionando**: `advanced_intelligence._get_on_chain_metrics()` operacional

## Plan de Activación

### Paso 1: Validar en Replit (Development)

```bash
# 1. Ejecutar tests
cd /home/runner/workspace
python -m pytest tests/test_onchain_port.py -v

# 2. Verificar que todos pasen (24/24)
```

### Paso 2: Activar temporalmente para testing

```bash
# En terminal de Replit
export USE_ONCHAIN_PORT=true

# Probar manualmente
python -c "
import asyncio
from src.omnix.bootstrap.container import get_container

async def test():
    container = get_container()
    adapter = container.onchain_adapter
    metrics = await adapter.get_onchain_metrics('BTC')
    print(f'Source: {metrics.source}')
    print(f'Hash Rate: {metrics.hash_rate}')
    print(f'Circulating: {metrics.circulating_supply} BTC')

asyncio.run(test())
"
```

### Paso 3: Activar en Railway (Production)

1. Ir a Railway Dashboard → Variables
2. Agregar: `USE_ONCHAIN_PORT=true`
3. Hacer redeploy automático

### Paso 4: Monitoreo (24h)

**Logs a monitorear:**
```
🔗 OnChainDataAdapter initialized (enabled=true)
✅ OnChainDataAdapter recovered, resetting failure count
```

**Errores a vigilar:**
```
⚠️ OnChainDataAdapter failure #N, entering cooldown
❌ BLOCKCHAIN.INFO [429] Rate limit exceeded
```

## Rollback

### Automático (Cooldown)
El adapter tiene cooldown automático de 5 minutos:
- Si Blockchain.info falla → usa legacy `_get_on_chain_metrics()`
- Después de 5 min → reintenta V7

### Manual (Desactivar flag)

```bash
# Railway Dashboard → Variables
USE_ONCHAIN_PORT=false
# Redeploy
```

## Métricas de Éxito

| Métrica | Criterio |
|---------|----------|
| Uptime V7 | >95% usando port V7 |
| Fallback rate | <5% usando legacy |
| Errores/hora | <10 errores por hora |
| Latencia | <2s por request |

## Troubleshooting

### Error: "Rate limit exceeded"

**Causa**: Blockchain.info tiene límite de ~5 req/s

**Solución**:
1. El adapter tiene rate limiting interno (0.2s entre requests)
2. Si persiste, aumentar `_min_request_interval` en `blockchain_info_provider.py`

### Error: "Asset not supported"

**Causa**: Blockchain.info solo soporta BTC

**Solución**:
1. Para ETH/SOL, esperar integración de Glassnode
2. O usar legacy fallback que retorna datos estimados

### Error: "Connection error"

**Causa**: Blockchain.info temporalmente caído

**Solución**:
1. Cooldown automático → fallback a legacy
2. Verificar status: https://status.blockchain.info/

## Próximos Pasos Post-Activación

1. **Monitorear 48h** sin errores críticos
2. **Integrar en analytics**: Conectar `OnChainAnalysisService` con dashboard
3. **Agregar Glassnode**: Para métricas avanzadas (requiere API key)
4. **Agregar Arkham**: Para tracking de entidades (requiere API key)

---

*Última actualización: 17 Dic 2025*
