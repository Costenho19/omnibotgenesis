# OMNIX Web — Railway Deployment Guide

## What This Is
React + Vite frontend + Flask API server, configured to deploy on Railway via GitHub.
One Railway service handles everything: builds the frontend and serves it alongside the API.

## Steps to Deploy

### 1. Create GitHub Repository
Create a new repository on GitHub (can be private).
Upload the contents of this `omnix_web/` folder as the root of that repository.

> The repo root should contain: `package.json`, `railway.toml`, `requirements.txt`, `api/`, `src/`, etc.

### 2. Connect to Railway
1. Go to [railway.app](https://railway.app)
2. Create a new project → "Deploy from GitHub repo"
3. Select your new repository
4. Railway will auto-detect `railway.toml` and configure the deployment

### 3. Set Environment Variables in Railway
In the Railway dashboard for this service, add these variables:

| Variable | Value | Required |
|----------|-------|----------|
| `DATABASE_URL` | Your PostgreSQL connection string | Yes |
| `FINNHUB_API_KEY` | Your Finnhub API key | Yes (for news feed) |

> Copy the `DATABASE_URL` from your existing Railway bot service — it's the same database.

### 4. Deploy
Railway will automatically:
1. Run `npm install && npm run build` (builds the React app into `dist/`)
2. Start `gunicorn api.server:app` (serves the API + static files)

### 5. Configure Your Domain (omnixquantum.net)

In your **Cloudflare dashboard**:
1. Go to DNS settings for `omnixquantum.net`
2. Find the A or CNAME record for `@` (root domain)
3. Change the value to your Railway service URL (shown in Railway dashboard after deploy)
4. Keep proxy status: Proxied (orange cloud)

For `www.omnixquantum.net`: point to the same Railway URL or keep on Replit Static Deployment.

## Routes Available After Deployment

| Route | Content |
|-------|---------|
| `/` | Commercial Landing Page |
| `/institutional` | Institutional Investor Page |
| `/governance-demo` | Credit Governance Demo |
| `/governance-demo-insurance` | Insurance Governance Demo |
| `/governance-demo-energy` | Energy Governance Demo |
| `/api/live-metrics` | Live metrics from DB (JSON) |
| `/api/news` | Crypto news from Finnhub (JSON) |
| `/api/health` | Health check (JSON) |

## Live Data
The landing page shows live metrics fetched from the same PostgreSQL database as the bot.
If the local API fails, the site automatically falls back to Railway's verification server.

## Local Development
For local development (unchanged):
```bash
npm run dev
```
The dev proxy forwards `/api/live-metrics` and `/api/news` to the local Flask server:
```bash
python api/server.py
```
