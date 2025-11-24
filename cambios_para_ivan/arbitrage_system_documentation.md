# 💱 DOCUMENTACIÓN TÉCNICA: Sistema de Arbitraje Multi-Exchange Premium V6.0

## 📋 Índice
1. [Arquitectura del Sistema](#arquitectura)
2. [Componentes Principales](#componentes)
3. [Flujo de Datos](#flujo)
4. [API Reference](#api)
5. [Configuración](#configuración)
6. [Troubleshooting](#troubleshooting)

---

## <a id="arquitectura"></a>🏗️ Arquitectura del Sistema

### Diagrama de Componentes
```
┌─────────────────────────────────────────────┐
│         Telegram Bot (Usuario)              │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│    enterprise_bot.py (Comandos)             │
│  - /arbitrage                                │
│  - /arbitrage_scan                           │
│  - /arbitrage_execute                        │
│  - /arbitrage_stats                          │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│ arbitrage_       │  │ arbitrage_       │
│ scanner.py       │  │ executor.py      │
│                  │  │                  │
│ - Escaneo        │  │ - Ejecución      │
│ - Análisis       │  │ - Paper/Live     │
│ - Filtrado       │  │ - Historial      │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         ▼                     ▼
┌─────────────────────────────────────────────┐
│         8 Exchanges (CCXT)                  │
│  Kraken | Binance | Coinbase | Bybit       │
│  KuCoin | OKX | Gate.io | Bitfinex         │
└─────────────────────────────────────────────┘
```

### Principios de Diseño
1. **Modularidad:** Scanner y Executor separados
2. **Seguridad:** Paper trading por default
3. **Performance:** Escaneo paralelo con ThreadPoolExecutor
4. **Reliability:** Manejo individual de errores por exchange
5. **Transparency:** Logging detallado de cada operación

---

## <a id="componentes"></a>⚙️ Componentes Principales

### 1. MultiExchangeArbitragePremium (Scanner)

**Ubicación:** `omnix_services/market_data/intelligence/arbitrage_scanner.py`

**Responsabilidades:**
- Escanear precios en 8 exchanges simultáneamente
- Detectar diferencias de precio (spreads)
- Calcular profit neto (después de fees)
- Filtrar oportunidades rentables (>0.3%)

**Métodos Principales:**
```python
class MultiExchangeArbitragePremium:
    def __init__(self):
        """
        Inicializa scanner con 8 exchanges.
        Configura fees y min_profit_threshold.
        """
        
    async def scan_arbitrage(self, symbol: str) -> List[Dict]:
        """
        Escanea un par de trading en todos los exchanges.
        
        Args:
            symbol: Par de trading (ej: 'BTC/USD', 'ETH/USDT')
            
        Returns:
            Lista de oportunidades ordenadas por profit DESC
            
        Example:
            opportunities = await scanner.scan_arbitrage('BTC/USD')
            # [
            #   {
            #     'symbol': 'BTC/USD',
            #     'buy_exchange': 'binance',
            #     'sell_exchange': 'kraken',
            #     'buy_price': 87800,
            #     'sell_price': 88100,
            #     'profit_percentage': 0.34,
            #     'profit_usd_per_btc': 300
            #   }
            # ]
        """
```

**Configuración de Fees (por exchange):**
```python
EXCHANGE_FEES = {
    'kraken': 0.26,    # 0.26% maker/taker
    'binance': 0.1,    # 0.1% con BNB
    'coinbase': 0.5,   # 0.5% taker
    'bybit': 0.1,      # 0.1% maker/taker
    'kucoin': 0.1,     # 0.1% maker/taker
    'okx': 0.1,        # 0.1% maker/taker
    'gateio': 0.2,     # 0.2% maker/taker
    'bitfinex': 0.2    # 0.2% maker/taker
}
```

### 2. ArbitrageExecutorPremium (Executor)

**Ubicación:** `omnix_services/market_data/intelligence/arbitrage_executor.py`

**Responsabilidades:**
- Ejecutar trades de arbitraje (compra + venta paralela)
- Gestionar modos Paper Trading / Live Trading
- Aplicar límites de seguridad
- Mantener historial de ejecuciones

**Métodos Principales:**
```python
class ArbitrageExecutorPremium:
    def __init__(self, paper_trading: bool = True):
        """
        Inicializa executor.
        
        Args:
            paper_trading: Si True, simula trades sin ejecutar (default)
        """
        
    async def execute_arbitrage(
        self, 
        opportunity: Dict, 
        amount_usd: float
    ) -> Dict:
        """
        Ejecuta un trade de arbitraje.
        
        Args:
            opportunity: Dict con datos de oportunidad (del scanner)
            amount_usd: Cantidad en USD a tradear
            
        Returns:
            Resultado de la ejecución con profit realizado
            
        Example:
            result = await executor.execute_arbitrage(
                opportunity={'buy_exchange': 'binance', ...},
                amount_usd=1000
            )
            # {
            #   'success': True,
            #   'profit_usd': 3.4,
            #   'buy_order': {...},
            #   'sell_order': {...}
            # }
        """
```

**Límites de Seguridad:**
```python
self.max_trade_size_usd = 10000      # Máximo $10K por trade
self.max_daily_volume_usd = 100000   # Máximo $100K por día
self.min_profit_threshold = 0.3      # Mínimo 0.3% profit
```

---

## <a id="flujo"></a>🔄 Flujo de Datos

### Flujo de Escaneo (Scan Flow)
```
Usuario → /arbitrage_scan BTC/USD
   ↓
enterprise_bot.arbitrage_scan_command()
   ↓
arbitrage_scanner.scan_arbitrage('BTC/USD')
   ↓
Paralelo: Fetch prices de 8 exchanges
   ↓
Calcular spreads y fees
   ↓
Filtrar: profit > 0.3%
   ↓
Ordenar por profit DESC
   ↓
Return top opportunities
   ↓
Format y enviar a Telegram
```

### Flujo de Ejecución (Execution Flow)
```
Usuario → /arbitrage_execute 1000
   ↓
enterprise_bot.arbitrage_execute_command()
   ↓
Tomar mejor oportunidad del último scan
   ↓
executor.execute_arbitrage(opp, 1000)
   ↓
if paper_trading:
    Simular órdenes
else:
    Paralelo: Place buy + sell orders
   ↓
Calcular profit real
   ↓
Guardar en historial
   ↓
Return resultado
   ↓
Format y enviar a Telegram
```

---

## <a id="api"></a>📚 API Reference

### Scanner API

#### `scan_arbitrage(symbol: str) -> List[Dict]`
Escanea oportunidades de arbitraje para un símbolo.

**Parameters:**
- `symbol` (str): Par de trading (ej: 'BTC/USD')

**Returns:**
- List[Dict]: Lista de oportunidades con estructura:
  ```python
  {
      'symbol': str,           # 'BTC/USD'
      'buy_exchange': str,     # 'binance'
      'sell_exchange': str,    # 'kraken'
      'buy_price': float,      # 87800.0
      'sell_price': float,     # 88100.0
      'spread': float,         # 300.0
      'profit_percentage': float,  # 0.34
      'profit_usd_per_unit': float,  # 300.0
      'timestamp': str         # '2025-11-24T20:15:30Z'
  }
  ```

**Example:**
```python
scanner = MultiExchangeArbitragePremium()
opps = await scanner.scan_arbitrage('ETH/USDT')
if opps:
    best = opps[0]
    print(f"Buy at {best['buy_exchange']}: ${best['buy_price']}")
    print(f"Sell at {best['sell_exchange']}: ${best['sell_price']}")
    print(f"Profit: {best['profit_percentage']}%")
```

### Executor API

#### `execute_arbitrage(opportunity: Dict, amount_usd: float) -> Dict`
Ejecuta un trade de arbitraje.

**Parameters:**
- `opportunity` (Dict): Oportunidad del scanner
- `amount_usd` (float): Cantidad en USD a tradear

**Returns:**
- Dict: Resultado de ejecución:
  ```python
  {
      'success': bool,
      'profit_usd': float,
      'buy_order': Dict,
      'sell_order': Dict,
      'execution_time': float,
      'timestamp': str
  }
  ```

**Example:**
```python
executor = ArbitrageExecutorPremium(paper_trading=True)
result = await executor.execute_arbitrage(opportunity, 5000)
if result['success']:
    print(f"Profit realizado: ${result['profit_usd']}")
```

---

## <a id="configuración"></a>⚙️ Configuración

### Variables de Entorno

**Replit Secrets (Requeridas para Live Trading):**
```bash
# Exchange API Keys (formato: EXCHANGE_API_KEY, EXCHANGE_SECRET)
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret
KRAKEN_API_KEY=your_key
KRAKEN_SECRET=your_secret
# ... etc para cada exchange
```

**Environment Variables:**
```bash
# Modo de trading
ARBITRAGE_LIVE_MODE=false        # false=paper, true=live

# Límites de seguridad
MAX_TRADE_SIZE_USD=10000         # Máximo por trade
MAX_DAILY_VOLUME_USD=100000      # Máximo por día
MIN_PROFIT_THRESHOLD=0.3         # Mínimo profit %
```

### Activar Live Trading
```python
# 1. Configurar API keys en Replit Secrets
# 2. Cambiar modo en main.py:
arbitrage_executor = ArbitrageExecutorPremium(paper_trading=False)

# 3. O usar variable de entorno:
ARBITRAGE_LIVE_MODE=true
```

---

## <a id="troubleshooting"></a>🔧 Troubleshooting

### Problema: "No opportunities found"
**Causa:** Spreads muy pequeños o fees altos  
**Solución:** Reducir `min_profit_threshold` o esperar mejor momento de mercado

### Problema: "Exchange timeout"
**Causa:** API del exchange lenta o caída  
**Solución:** El sistema maneja esto automáticamente, continúa con exchanges disponibles

### Problema: "Insufficient balance"
**Causa:** Balance insuficiente en exchange para ejecutar  
**Solución:** Depositar fondos o reducir `amount_usd`

### Problema: "API key invalid"
**Causa:** API keys mal configuradas en Replit Secrets  
**Solución:** Verificar y actualizar keys en Secrets tab

---

**Última actualización:** 24 de Noviembre 2025  
**Autor:** Harold Nunes  
**Versión:** 6.0
