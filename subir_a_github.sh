#!/bin/bash
# Script para subir módulo de bolsa a GitHub
# Creado por OMNIX V6.0 - Harold Nunes

echo "📊 Subiendo Módulo de Bolsa a GitHub..."
echo ""

# Agregar archivos nuevos
git add omnix_services/stock_trading/
git add STOCK_TRADING_README.md
git add main.py
git add .env.example

# Ver qué se va a subir
echo "✅ Archivos preparados:"
git status

echo ""
echo "📝 Haciendo commit..."
git commit -m "feat: Stock Trading Module V6.0 - NYSE/NASDAQ integration

- Added Alpaca Markets API integration
- Created stock technical analyzer (RSI, MACD, EMA)
- Created fundamental analyzer (P/E, earnings, ratios)
- Added market hours manager for NYSE/NASDAQ
- Integrated 5 new Telegram commands for stock trading
- Updated help system with stock commands
- Complete documentation in STOCK_TRADING_README.md
- Dual-market architecture: Crypto (24/7) + Stocks (market hours)"

echo ""
echo "🚀 Subiendo a GitHub..."
git push origin main

echo ""
echo "✅ ¡Listo! Módulo de bolsa subido a GitHub"
