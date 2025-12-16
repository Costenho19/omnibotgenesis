# OMNIX V6.5.4d - Guía de Deployment (Railway)

**Versión**: V6.5.4d INSTITUTIONAL+  
**Actualizado**: Diciembre 2025  
**Estado**: Producción 24/7

---

## Arquitectura de Servicios

```
Railway Project: omnibotgenesis
├── App Service (main.py)      ← Bot Telegram + Dashboard Flask
├── PostgreSQL                 ← 42+ tablas
└── Redis                      ← Cache + estado
```

### Entrypoint Único

```
main.py
├── Telegram Bot (polling)     # Bot de trading principal
└── Dashboard (thread)         # Flask en puerto 5000
```

---

## Variables de Entorno

### Referencias Railway (Obligatorio)

```bash
# Base de datos (usar referencia, NO URL hardcodeada)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (red privada, sin cargos de egress)
REDIS_URL=${{Redis.REDIS_URL}}
```

### API Keys

```bash
# Telegram
TELEGRAM_BOT_TOKEN=<tu_token>

# AI Services
GEMINI_API_KEY=<gemini_key>
OPENAI_API_KEY=<openai_key>
ANTHROPIC_API_KEY=<anthropic_key>

# Exchange
KRAKEN_API_KEY=<kraken_key>
KRAKEN_API_SECRET=<kraken_secret>

# Market Intelligence
FINNHUB_API_KEY=<finnhub_key>
ALPHA_VANTAGE_API_KEY=<alpha_vantage_key>

# Trading
TRADING_MODE=paper
SESSION_SECRET=<session_secret>
```

---

## Deployment

### Paso 1: Conectar GitHub
1. Railway Dashboard → New Project → Deploy from GitHub
2. Seleccionar repositorio

### Paso 2: Agregar Servicios
1. **PostgreSQL**: + New → Database → PostgreSQL
2. **Redis**: + New → Database → Redis

### Paso 3: Configurar Variables
1. App Service → Variables
2. Usar sintaxis de referencia: `${{Postgres.DATABASE_URL}}`

### Paso 4: Deploy Automático
Railway detecta `requirements.txt` y ejecuta:
```bash
pip install -r requirements.txt
python main.py
```

---

## Verificación

### Logs Esperados
```
✅ PostgreSQL: 42+ tables active
✅ Redis connection established
✅ BOT TELEGRAM OPERATIVO
```

### Tests
```bash
# Telegram
/start

# SQL
SELECT COUNT(*) FROM paper_trading_trades;
```

---

## Dashboard Endpoints

| Endpoint | Descripción |
|----------|-------------|
| `/` | Dashboard principal |
| `/terminal` | Vista terminal |
| `/api/metrics` | Métricas de trading |
| `/api/trades` | Lista de trades |
| `/api/health` | Health check |

---

## Troubleshooting

| Error | Solución |
|-------|----------|
| "Cannot connect to PostgreSQL" | Verificar `DATABASE_URL=${{Postgres.DATABASE_URL}}` |
| "Redis connection failed" | Usar `${{Redis.REDIS_URL}}` (red privada) |
| "Telegram conflict" | NO correr bot en Replit y Railway simultáneamente |

---

## Rollback

1. **Redeploy anterior**: Deployments → Seleccionar versión → Redeploy
2. **Restore DB**: Postgres → Backups → Restore

---

*OMNIX V6.5.4d INSTITUTIONAL+*
