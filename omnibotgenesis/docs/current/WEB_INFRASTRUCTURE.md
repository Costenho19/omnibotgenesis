# Web Infrastructure - OMNIX QUANTUM

**Last Updated**: March 15, 2026  
**Status**: Production Ready

## Overview

OMNIX utiliza una arquitectura multi-puerto para servir diferentes interfaces a diferentes audiencias:

| Puerto | Servicio | Audiencia | Tecnología |
|--------|----------|-----------|------------|
| 5000 | Landing Page Institucional | Inversores, prospectos B2B | React + Vite |
| 8000 | Flask Dashboard | Internal demos, due diligence | Flask + Jinja2 |
| 8080 | Streamlit Analytics | Shadow analytics, métricas | Streamlit |

## Arquitectura de Servicios

```
┌─────────────────────────────────────────────────────────────────┐
│                        OMNIX QUANTUM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   OMNIX Web     │  │  Flask Dashboard │  │    Streamlit    │ │
│  │   (Port 5000)   │  │   (Port 8000)    │  │   (Port 8080)   │ │
│  │                 │  │                  │  │                 │ │
│  │  React + Vite   │  │  Flask + Jinja2  │  │   Streamlit     │ │
│  │  TypeScript     │  │  Python          │  │   Python        │ │
│  │  Tailwind CSS   │  │                  │  │                 │ │
│  └────────┬────────┘  └────────┬─────────┘  └────────┬────────┘ │
│           │                    │                     │          │
│           └────────────────────┼─────────────────────┘          │
│                                │                                │
│                    ┌───────────▼───────────┐                    │
│                    │   PostgreSQL (Railway) │                    │
│                    │   Redis (Railway)      │                    │
│                    └───────────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 1. Landing Page Institucional (Port 5000)

### Ubicación
```
omnix_web/
```

### Stack Tecnológico
- **React 18** + TypeScript
- **Vite 6** (build tool)
- **Tailwind CSS 3** (styling)
- **Lucide React** (icons)

### Características
1. **Hero Section**: Estadísticas animadas en tiempo real
2. **Problem Statement**: Por qué 73% de traders algorítmicos pierden
3. **4-Layer Architecture**: Visualización del sistema de validación
4. **Track Record**: Transparencia Learning Baseline vs Official
5. **Live Market Data**: Precios BTC/ETH, Fear & Greed Index
6. **Risk Calculator**: Herramienta de cálculo de posiciones
7. **Pricing**: B2C SaaS ($49-$499/mo) + B2B Enterprise ($10K-$100K+)
8. **Certifications**: NIST FIPS (Implemented), ADGM (Target), Sharia (In Development)

### APIs Externas
| API | Propósito | Endpoint |
|-----|-----------|----------|
| CoinGecko | Precios BTC/ETH | `api.coingecko.com/api/v3/simple/price` |
| Alternative.me | Fear & Greed | `api.alternative.me/fng/` |
| Finnhub | Noticias (proxy) | Via Flask backend |

### Configuración Vite
```typescript
export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 5000,
    allowedHosts: true,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

### Design System
| Color | Hex | Uso |
|-------|-----|-----|
| Gold | #C9A227 | Acentos primarios, CTAs |
| Navy | #0A1628 | Fondos |
| Platinum | #E5E4E2 | Texto secundario |
| Dark Navy | #050D18 | Fondos profundos |

## 2. Flask Dashboard (Port 8000)

### Ubicación
```
omnix_dashboard/
├── app.py              # Flask application
├── templates/          # Jinja2 templates
├── static/             # CSS, JS assets
└── utils/              # Helper modules
```

### Características
- Trade history y métricas
- System health monitoring
- Real-time veto tracking
- Investor demo mode

### Seguridad (ADR-015)
- Basic HTTP Authentication
- Rate limiting (60 req/min)
- IP allowlist opcional
- Security headers

## 3. Streamlit Analytics (Port 8080)

### Ubicación
```
omnix_dashboard/streamlit_app.py
```

### Características
- Shadow Portfolio Analysis
- Decision quality metrics (DCI, ECW, Coherence)
- Veto accuracy tracking
- Counterfactual trade analysis

### Páginas
1. **Overview**: KPIs principales
2. **Trade History**: Historial detallado
3. **Shadow Analytics**: Análisis de decisiones vetadas
4. **Regime Detection**: Estado del mercado

## Workflows Configurados

| Nombre | Comando | Puerto |
|--------|---------|--------|
| OMNIX Web | `cd omnix_web && npm run dev` | 5000 |
| Flask Dashboard | `cd omnix_dashboard && python -m flask run --host=0.0.0.0 --port=8000` | 8000 |
| Streamlit Dashboard | `cd omnix_dashboard && streamlit run streamlit_app.py --server.port 8080` | 8080 |

## Deployment

### Desarrollo (Replit) - Estado Actual
Los tres servicios corren simultáneamente en Replit (desarrollo/demos):
- Puerto 5000: Landing page institucional (expuesto para demos)
- Puerto 8000: Dashboard Flask (demos internos)
- Puerto 8080: Streamlit Analytics (accesible internamente)

> **Nota**: "Website LIVE" en docs/REAL_SYSTEM_STATUS.md indica que el sitio está operativo en desarrollo para demos de inversores. No hay hosting de producción separado aún.

### Producción (Railway)
- **Bot Telegram**: Railway (24/7)
- **Website (omnixquantum.net)**: Railway — `omnix_web/api/server.py` (gunicorn) sirve React compilado + API endpoints
- **Public Governance Sandbox (`/try`)**: Endpoint público sin autenticación, Gemini AI + 8-checkpoint pipeline, receipts almacenados en `decision_receipts` (`client_id='PUBLIC'`, `domain='public_sandbox'`), verificables en el servidor de verificación Railway
- **Variables requeridas en Railway**: `DATABASE_URL`, `FINNHUB_API_KEY`, `GOOGLE_AI_API_KEY`

## Troubleshooting

### Website no visible en iframe
1. Verificar `allowedHosts: true` en vite.config.ts
2. Reiniciar workflow OMNIX Web
3. Verificar que el puerto 5000 esté libre

### NaN en estadísticas
El hook `useCountUp` tiene validación para prevenir NaN:
```typescript
const safeEnd = isNaN(end) || end === null || end === undefined ? 0 : end
```

### API calls fallan
Los datos de fallback están configurados para CoinGecko y Alternative.me.
El sistema mantiene valores por defecto si las APIs externas no responden.

## Referencias

- [omnix_web/README.md](../../omnix_web/README.md) - Documentación del landing page
- [ADR-015: Dashboard Security](../reference/adr/ADR-015-dashboard-security.md)
- [replit.md](../../replit.md) - Configuración general
