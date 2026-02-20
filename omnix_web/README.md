# OMNIX QUANTUM - Public Institutional Website

**Version**: 1.0.0  
**Last Updated**: January 28, 2026  
**Status**: Production Ready

## Overview

Landing page institucional para OMNIX QUANTUM, diseñada para inversores y prospectos B2B. Presenta la propuesta de valor del sistema de control de riesgo institucional.

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | 18.x |
| Language | TypeScript | 5.x |
| Build Tool | Vite | 6.x |
| Styling | Tailwind CSS | 3.x |
| Icons | Lucide React | Latest |

## Architecture

```
omnix_web/
├── public/
│   ├── logo.png          # OMNIX QUANTUM official logo
│   └── favicon.ico       # Browser favicon
├── src/
│   ├── App.tsx           # Main application component
│   ├── index.css         # Global styles + Tailwind
│   └── main.tsx          # React entry point
├── api/                  # Proxy endpoints (Flask integration)
├── vite.config.ts        # Vite configuration
└── package.json          # Dependencies
```

## Design System

### Color Palette (Institutional)
| Name | Hex | Usage |
|------|-----|-------|
| Gold | #C9A227 | Primary accents, CTAs |
| Navy | #0A1628 | Backgrounds |
| Platinum | #E5E4E2 | Secondary text |
| Dark Navy | #050D18 | Deep backgrounds |

### Typography
- **Headings**: Inter, bold
- **Body**: Inter, regular
- **Monospace**: System monospace

## Key Features

### 1. Hero Section
- Animated count-up statistics
- Real-time system status indicator
- Primary CTAs: Schedule Demo, Technical Brief

### 2. Problem Statement
- "Why 73% of algo traders lose money"
- Three key failure points visualization

### 3. 4-Layer Validation Architecture
- Monte Carlo Simulation
- Coherence Engine
- Risk Management
- Execution Protocol

### 4. Track Record Transparency
- Learning Baseline (Nov 2025 - Jan 14, 2026): 119 trades, calibration phase
- Official Track Record (Jan 15, 2026+): Institutional-grade metrics

### 5. Live Market Data
- BTC/ETH prices via CoinGecko API
- Fear & Greed Index via Alternative.me
- Market news via Finnhub (proxied)

### 6. Risk Calculator
- Position size calculation based on:
  - Capital
  - Risk percentage
  - Stop loss percentage

### 7. Pricing Tiers
**B2C SaaS:**
- Starter: $49/mo
- Pro: $149/mo
- Advanced: $499/mo

**B2B Enterprise:**
- Risk Guardian API: $10K-50K/mo
- White-Label Engine: $100K+ setup

### 8. Certifications
- NIST PQC Standards: **Implemented** (Kyber-768/Dilithium-3)
- ADGM: Target Jurisdiction
- Sharia Compliant: In Development

## External API Integrations

| API | Endpoint | Purpose |
|-----|----------|---------|
| CoinGecko | `/api/v3/simple/price` | BTC/ETH prices |
| Alternative.me | `/fng/` | Fear & Greed Index |
| Finnhub | `/api/v1/news` | Market news (via Flask proxy) |
| Flask Dashboard | `localhost:8000/api/*` | Backend metrics (proxied) |

## Development

### Prerequisites
- Node.js 20+
- npm 10+

### Installation
```bash
cd omnix_web
npm install
```

### Run Development Server
```bash
npm run dev
```
Server runs on `http://localhost:5000`

### Build for Production
```bash
npm run build
```
Output: `dist/` folder

## Configuration

### vite.config.ts
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

## Workflows

| Workflow | Command | Port |
|----------|---------|------|
| Development | `npm run dev` | 5000 |
| Flask Dashboard | Separate workflow | 8000 |
| Streamlit Analytics | Separate workflow | 8080 |

## Track Record Progress

| Metric | Current | Target |
|--------|---------|--------|
| Day | 12 | 30 |
| Period | Jan 15 - Feb 13, 2026 | - |
| Goal | $500K seed | $5M pre-money |
| Capital Preserved | 98.5% | ≥98% |

## Related Documentation

- [Web Infrastructure](../docs/current/WEB_INFRASTRUCTURE.md)
- [ADR-023: Investor Positioning](../docs/reference/adr/ADR-023-investor-positioning-refinement.md)
- [Business Model](../docs/business/investor/PRODUCT_OVERVIEW.md)

## Changelog

### v1.0.0 (Jan 28, 2026)
- Initial institutional landing page
- 8 content sections
- Live market data integration
- Risk calculator tool
- Multi-tier pricing display
- Certification transparency
