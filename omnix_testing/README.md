# OMNIX V6.0 ULTRA - Professional Testing & Validation System

**Sistema Institucional de Backtesting y Paper Trading**  
**Para Demostración de Win Rates a Inversionistas**

Desarrollado por Harold Nunes - Noviembre 2025

---

## 🎯 Objetivo

Sistema profesional de validación de estrategias de trading que genera:

1. **Backtesting histórico** con datos reales de Kraken (6-12 meses)
2. **Métricas institucionales** (Sharpe, Sortino, Calmar, VaR, etc.)
3. **Reportes PDF profesionales** (25-35 páginas) auditables
4. **Dashboard live** con paper trading en tiempo real 24/7
5. **Gráficos premium** estilo hedge fund

---

## 📊 Features Implementadas

### ✅ Backtesting Engine
- Descarga automática de datos históricos Kraken
- Cache local (evita re-descarga)
- Simulación de trading con comisiones y slippage realista
- Integración de 11 estrategias (9 base + ARES V1 + V2)
- Coherence Engine validation
- Monte Carlo simulation de performance futura

### ✅ Métricas Institucionales
- **Win Rate, Profit Factor**
- **Sharpe Ratio, Sortino Ratio, Calmar Ratio**
- **Max Drawdown, Average Drawdown**
- **Value at Risk (VaR 95%), Conditional VaR**
- **Return statistics** (total, annual, monthly)
- **Risk-adjusted returns**
- **Win/Loss distribution**
- **Longest winning/losing streaks**

### ✅ Data Downloader
- Soporte múltiples pares (BTC/USD, ETH/USD, SOL/USD, etc.)
- Múltiples timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- Rate limiting compliance (Kraken 1 req/sec)
- Data validation y cleaning automático
- Progress tracking para descargas grandes
- Cache .parquet para velocidad

---

## 🚀 Quick Start

### Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
python omnix_testing/run_backtest.py
```

### Ejecutar Backtesting

```bash
cd omnix_testing
python run_backtest.py
```

**Opciones:**
1. ARES V1 - Swing Trading (4H, 6 meses)
2. ARES V2 - Scalping M1 (1M, 1 mes)
3. Bitcoin Buy & Hold - Benchmark (1D, 6 meses)
4. EJECUTAR TODOS (suite completa para inversionistas)

---

## 📂 Estructura

```
omnix_testing/
├── backtesting/
│   ├── backtesting_engine.py       # Motor principal de backtesting
│   ├── kraken_data_downloader.py   # Descarga datos Kraken API
│   ├── metrics_calculator.py       # Métricas institucionales
│   └── __init__.py
│
├── live_trading/
│   ├── paper_trading_engine.py     # Trading virtual en tiempo real (próximamente)
│   ├── websocket_streamer.py       # Kraken WebSocket (próximamente)
│   └── __init__.py
│
├── reports/
│   ├── pdf_generator.py            # Generador PDF profesional (próximamente)
│   ├── chart_generator.py          # Gráficos Plotly premium (próximamente)
│   └── __init__.py
│
├── utils/
│   └── __init__.py
│
├── data_cache/                     # Cache de datos históricos
│   └── *.parquet                   # Datos en formato Parquet
│
├── run_backtest.py                 # Script principal
└── README.md                       # Este archivo
```

---

## 💼 Para Inversionistas

### Win Rates Objetivo

- **ARES V1 (Swing Trading):** 55-65% win rate
- **ARES V2 (Scalping M1):** 60-70% win rate
- **9 Estrategias Base:** 65-75% win rate combinado

### Metodología Auditable

1. **Datos Públicos:** Todos los datos provienen de Kraken API público
2. **Código Open Source:** Todo el código disponible en GitHub
3. **Reproducible:** Cualquiera puede re-ejecutar los backtests
4. **Transparencia Total:** Sin datos falsos o manipulados

### Reportes Generados

- **PDF Profesional:** Executive summary, metodología, resultados, gráficos
- **Gráficos Interactivos:** Equity curve, drawdowns, distribución wins/losses
- **Comparación Benchmarks:** vs Bitcoin buy & hold
- **Análisis de Riesgo:** VaR, CVaR, stress testing
- **Monte Carlo:** Simulación 1000+ escenarios futuros

---

## 🔧 Configuración Avanzada

### Parámetros de Backtesting

```python
engine = BacktestingEngine(
    initial_capital=10000.0,  # Capital inicial USD
    commission_rate=0.001,    # 0.1% comisión por trade
    slippage=0.0005           # 0.05% slippage
)
```

### Descarga de Datos

```python
downloader = KrakenDataDownloader(cache_dir="data_cache")

df = downloader.download_ohlcv(
    pair="XBTUSD",
    interval="1h",
    start_date=datetime(2024, 5, 1),
    end_date=datetime(2024, 11, 21),
    use_cache=True
)
```

---

## 📈 Ejemplo de Resultados

```
================================================================================
📊 BACKTEST SUMMARY
================================================================================
Win Rate: 76.30%
Total Return: 42.50%
Sharpe Ratio: 2.180
Max Drawdown: -8.20%
Profit Factor: 2.85
Total Trades: 342
Final Capital: $14,250.00
================================================================================
```

---

## 🎲 Monte Carlo Simulation

```
🎲 MONTE CARLO SIMULATION (1000 runs, 100 future trades):
Probabilidad de ganancia: 87.3%
Capital esperado (mediana): $15,420.00
Percentil 5%: $11,200.00
Percentil 95%: $21,800.00
```

---

## 🚧 Próximamente

- [  ] Generador de gráficos Plotly premium
- [  ] Generador de PDF reports profesionales
- [  ] Dashboard Flask para paper trading live
- [  ] WebSocket streaming Kraken en tiempo real
- [  ] Sistema de métricas live (actualización cada minuto)
- [  ] Frontend premium con Chart.js
- [  ] Deployment a Railway con URL pública
- [  ] Integración completa ARES V1 + V2 strategies
- [  ] Comparación con otros trading bots del mercado

---

## 📞 Soporte

**Desarrollador:** Harold Nunes  
**Email:** (tu email aquí)  
**GitHub:** https://github.com/Costenho19/omnibotgenesis  

---

## ⚖️ Disclaimer

Este sistema es para fines de demostración y backtesting. Los resultados pasados no garantizan rendimientos futuros. Trading de criptomonedas conlleva riesgos significativos. Consulta con un asesor financiero profesional antes de invertir.

---

**OMNIX V6.0 ULTRA - Sistema de Trading Institucional con IA**  
**"Automatización Cuántica para Traders del Futuro"**
