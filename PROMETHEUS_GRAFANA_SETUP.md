# 📊 OMNIX METRICS ENGINE - PROMETHEUS + GRAFANA

## Sistema de Métricas Institucional para Trading Bot

Este documento explica cómo configurar y usar el sistema de métricas profesional de OMNIX V5.2 Quantum Ultimate.

---

## 🎯 **¿QUÉ ES ESTO?**

Un sistema de monitoreo en tiempo real que te permite ver:

- **Trades ejecutados** (buy/sell)
- **Win rate** en tiempo real
- **Profit/Loss acumulado**
- **Señales** generadas por cada estrategia
- **Rendimiento** de Kalman Filter, Quantum Momentum, Monte Carlo, etc.
- **Latencia** de Kraken API
- **Errores** de sistema
- **Auto-learning** changes aplicados
- **Videos** analizados

**Todo en dashboards profesionales que impresionan a inversores** 🚀

---

## 📦 **COMPONENTES**

### 1. **MetricsEngine** (`metrics_engine.py`)

Motor de métricas que exporta datos en formato Prometheus:

```python
from metrics_engine import get_metrics_engine

metrics = get_metrics_engine()

# Registrar trade
metrics.record_trade('buy', 'paper', 'BTC/USD', 100.0, 0.85)

# Actualizar P/L
metrics.update_pnl('paper', 1250.50)

# Actualizar win rate
metrics.update_win_rate('paper', 67.3)
```

### 2. **Endpoint `/metrics`** (en `main.py`)

Endpoint HTTP que Prometheus usa para obtener métricas:

```
http://tu-dominio.com/metrics
```

### 3. **Dashboard Grafana** (`config/grafana/omnix_dashboard.json`)

Configuración JSON lista para importar en Grafana con 20+ gráficos.

---

## ⚡ **INSTALACIÓN RÁPIDA**

### **Opción 1: Railway (Recomendado para Producción)**

1. **Agregar Prometheus a Railway:**
   ```bash
   # En Railway dashboard:
   # New → Database → Prometheus
   ```

2. **Configurar scraping:**
   ```yaml
   # prometheus.yml
   scrape_configs:
     - job_name: 'omnix'
       scrape_interval: 15s
       static_configs:
         - targets: ['omnix-bot.railway.app:5000']
       metrics_path: '/metrics'
   ```

3. **Agregar Grafana:**
   ```bash
   # En Railway dashboard:
   # New → Database → Grafana
   ```

4. **Importar dashboard:**
   - Grafana → Dashboards → Import
   - Subir `config/grafana/omnix_dashboard.json`

### **Opción 2: Docker Local (Testing)**

```bash
# Prometheus
docker run -d --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Grafana
docker run -d --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

**Prometheus config (`prometheus.yml`):**

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'omnix'
    static_configs:
      - targets: ['host.docker.internal:5000']
    metrics_path: '/metrics'
```

### **Opción 3: Manual (Linux/Mac)**

```bash
# Instalar Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvf prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64

# Configurar
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'omnix'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
EOF

# Ejecutar
./prometheus --config.file=prometheus.yml

# Instalar Grafana
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install grafana

# Ejecutar
sudo systemctl start grafana-server
```

---

## 🎨 **CONFIGURACIÓN GRAFANA**

### **Paso 1: Agregar Data Source**

1. Grafana → Configuration → Data Sources
2. Add data source → Prometheus
3. URL: `http://localhost:9090` (o tu Prometheus URL)
4. Save & Test

### **Paso 2: Importar Dashboard**

1. Grafana → Dashboards → Import
2. Upload JSON file: `config/grafana/omnix_dashboard.json`
3. Select Prometheus data source
4. Import

### **Paso 3: Personalizar (Opcional)**

Edita los paneles para ajustar:
- Intervalos de tiempo
- Colores de umbrales
- Alertas
- Layout

---

## 📊 **MÉTRICAS DISPONIBLES**

### **Trading Métricas**

| Métrica | Tipo | Labels | Descripción |
|---------|------|--------|-------------|
| `omnix_trades_total` | Counter | action, mode, pair | Trades ejecutados |
| `omnix_trades_outcome_total` | Counter | outcome, mode | Win/loss trades |
| `omnix_pnl_usd` | Gauge | mode | P/L acumulado |
| `omnix_win_rate_percent` | Gauge | mode | Win rate % |
| `omnix_balance_usd` | Gauge | mode, asset | Balance por asset |

### **Estrategias Métricas**

| Métrica | Tipo | Labels | Descripción |
|---------|------|--------|-------------|
| `omnix_signals_total` | Counter | strategy, signal | Señales generadas |
| `omnix_strategy_confidence` | Gauge | strategy | Confianza promedio |
| `omnix_strategy_win_rate` | Gauge | strategy | Win rate individual |

### **V5.2 Quantum Métricas**

| Métrica | Tipo | Descripción |
|---------|------|-------------|
| `omnix_adaptive_omega` | Gauge | Peso ω adaptativo |
| `omnix_hurst_exponent` | Gauge | Exponente Hurst |
| `omnix_alpha_stable` | Gauge | Índice α-stable |
| `omnix_quantum_signal` | Gauge | Señal Quantum (-10 a +10) |
| `omnix_kalman_trend_strength` | Gauge | Fuerza trend Kalman |
| `omnix_monte_carlo_win_rate` | Gauge | Win rate Monte Carlo |
| `omnix_black_swan_risk` | Gauge | Riesgo Black Swan (0-2) |

### **Sistema Métricas**

| Métrica | Tipo | Labels | Descripción |
|---------|------|--------|-------------|
| `omnix_kraken_api_latency_seconds` | Histogram | endpoint | Latencia Kraken |
| `omnix_bot_uptime_seconds` | Gauge | - | Uptime del bot |
| `omnix_api_errors_total` | Counter | service, error_type | Errores API |
| `omnix_auto_learning_changes_total` | Counter | parameter | Cambios auto-learning |
| `omnix_video_analyses_total` | Counter | status | Videos analizados |

---

## 🔍 **QUERIES ÚTILES (PROMQL)**

### **Win Rate en las últimas 24h:**

```promql
omnix_win_rate_percent{mode="paper"}
```

### **Trades por minuto:**

```promql
rate(omnix_trades_total[1m])
```

### **P/L diario:**

```promql
increase(omnix_pnl_usd[1d])
```

### **Señales más generadas:**

```promql
topk(5, sum by (strategy) (omnix_signals_total))
```

### **Latencia p95 de Kraken:**

```promql
histogram_quantile(0.95, rate(omnix_kraken_api_latency_seconds_bucket[5m]))
```

### **Error rate por servicio:**

```promql
rate(omnix_api_errors_total[5m])
```

---

## 🚨 **ALERTAS RECOMENDADAS**

### **1. Win Rate Bajo**

```yaml
alert: LowWinRate
expr: omnix_win_rate_percent < 40
for: 15m
annotations:
  summary: "Win rate bajo en {{ $labels.mode }} mode"
```

### **2. Pérdidas Altas**

```yaml
alert: HighLosses
expr: omnix_pnl_usd < -5000
for: 5m
annotations:
  summary: "Pérdidas > $5000 en {{ $labels.mode }} mode"
```

### **3. Bot Down**

```yaml
alert: BotDown
expr: up{job="omnix"} == 0
for: 1m
annotations:
  summary: "OMNIX bot está down"
```

### **4. API Errors Altos**

```yaml
alert: HighAPIErrors
expr: rate(omnix_api_errors_total[5m]) > 0.1
for: 2m
annotations:
  summary: "Errores API elevados: {{ $labels.service }}"
```

---

## 📈 **DASHBOARD PANELS**

El dashboard incluye:

1. **Total Trades** - Stat
2. **Win Rate %** - Gauge (40-55-100%)
3. **P/L USD** - Stat con colores
4. **Bot Uptime** - Stat
5. **Trades Over Time** - Graph
6. **Win vs Loss** - Pie chart
7. **Signals by Strategy** - Graph
8. **Strategy Win Rates** - Bar gauge
9. **Adaptive Omega** - Graph (0-1)
10. **Hurst Exponent** - Graph
11. **Alpha Stable** - Graph
12. **Quantum Signal** - Graph (-10 a +10)
13. **Kalman Trend** - Gauge
14. **Black Swan Risk** - Stat (LOW/MEDIUM/HIGH)
15. **Kraken Latency** - Graph
16. **API Errors** - Graph
17. **Balance by Asset** - Graph
18. **Monte Carlo Win Rate** - Gauge
19. **Auto-Learning Changes** - Stat
20. **Video Analyses** - Pie chart

---

## 🛠️ **USO EN CÓDIGO**

### **Registrar Trade:**

```python
from metrics_engine import get_metrics_engine

metrics = get_metrics_engine()

# Cuando ejecutas un trade
metrics.record_trade(
    action='buy',
    mode='paper',
    pair='BTC/USD',
    amount_usd=500.0,
    confidence=0.78,
    outcome='win'  # opcional
)
```

### **Actualizar Métricas de Estrategia:**

```python
# Señal generada
metrics.record_signal('quantum_momentum', 'buy')

# Confianza de estrategia
metrics.update_strategy_confidence('kalman_filter', 0.85)

# Win rate de estrategia
metrics.update_strategy_win_rate('monte_carlo', 67.5)
```

### **Métricas V5.2 Quantum:**

```python
# Adaptive weights
metrics.update_adaptive_weights(omega=0.67, hurst=0.82, alpha=1.65)

# Régimen de mercado
metrics.update_market_regime('TRENDING', 'NORMAL')

# Quantum signal
metrics.update_quantum_signal(8.5)

# Black Swan risk
metrics.update_black_swan_risk('LOW')
```

### **Tracking de API:**

```python
import time

start = time.time()
# ... llamada a Kraken API ...
duration = time.time() - start

metrics.record_kraken_api_call('get_ticker', duration)
```

---

## 💡 **PARA INVERSORES**

### **¿Por qué esto es brutal?**

1. **Transparencia Total**: Los inversores ven métricas en vivo
2. **Profesionalismo**: Dashboards de nivel institucional
3. **Auditabilidad**: Histórico completo de todas las métricas
4. **Confianza**: Sistema estándar de la industria (Prometheus)

### **Screenshots para Pitch Deck:**

1. Dashboard completo (vista general)
2. Win rate gauge (destacar >55%)
3. P/L acumulado (destacar crecimiento)
4. Quantum metrics (mostrar sofisticación)
5. Uptime 99.9% (destacar confiabilidad)

---

## 🔧 **TROUBLESHOOTING**

### **Problema: No se ven métricas en Grafana**

```bash
# 1. Verificar que /metrics funciona
curl http://localhost:5000/metrics

# 2. Verificar que Prometheus está scraping
curl http://localhost:9090/api/v1/targets

# 3. Verificar logs de Prometheus
docker logs prometheus
```

### **Problema: Latencia alta en dashboard**

```bash
# Reducir scrape interval
# En prometheus.yml:
scrape_interval: 30s  # en vez de 5s
```

### **Problema: Métricas duplicadas**

```python
# Usar singleton
from metrics_engine import get_metrics_engine
metrics = get_metrics_engine()  # Siempre usa la misma instancia
```

---

## 📚 **RECURSOS**

- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/)

---

## ✅ **CHECKLIST DE DEPLOYMENT**

- [ ] Prometheus instalado y corriendo
- [ ] Configurado scraping a `/metrics`
- [ ] Grafana instalado y corriendo
- [ ] Data source Prometheus agregado
- [ ] Dashboard importado
- [ ] Alertas configuradas
- [ ] Screenshots tomados para pitch deck
- [ ] Documentación compartida con equipo
- [ ] Acceso a Grafana configurado (readonly para inversores)

---

## 🎯 **PRÓXIMOS PASOS**

1. **Backtesting Dashboard**: Agregar panel con resultados de backtests
2. **ML Performance**: Métricas de accuracy de predicciones AI
3. **Multi-Asset**: Expandir a ETH, SOL, etc.
4. **Custom Annotations**: Marcar eventos importantes en gráficos
5. **Mobile App**: Grafana mobile para monitoreo on-the-go

---

**Desarrollado por Harold Nunes - OMNIX V5.2 Quantum Ultimate**
**Noviembre 2025**
