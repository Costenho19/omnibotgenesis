# 🚀 OMNIX V6.0 Environment Variables Migration Guide

## 📋 Overview
This guide documents the centralized environment variable system migration completed on November 25, 2025.

## 🎯 What Changed

### Before (9 .env files - CHAOS)
- `.env` - Mixed credentials
- `.env.deployment` - Railway config (DELETED)
- `.env.example` - Template
- `.env.kraken` - Kraken specific (DELETED)
- `.env.migracion` - Migration temp (DELETED)
- `.env.persistent` - Old config (DELETED)
- `.env.pro` - Production config (DELETED)
- `.env.railway` - Railway specific
- `.env.template` - Current template

### After (4 .env files - CLEAN)
- `.env` - Protected by Replit (DO NOT EDIT)
- `.env.example` - Example template
- `.env.railway` - Railway-specific config
- `.env.template` - **Main reference template** (140 lines, 19 variables)

## 🏗️ New Architecture

### EnvConfig System (`omnix_config/env_manager.py`)
**442 lines of enterprise-grade configuration management**

#### Precedence Order (Highest to Lowest):
1. **Replit Secrets** (Production) - Encrypted, secure
2. **`.env.local`** (Development) - Local overrides (gitignored)
3. **Environment Defaults** - Hardcoded fallbacks

#### Features:
- ✅ Thread-safe singleton pattern
- ✅ Type casting (str, int, bool, float)
- ✅ Validation rules per variable
- ✅ Secure logging (masks sensitive values)
- ✅ Category-based organization
- ✅ Runtime error detection

## 📦 Environment Variables Catalog (19 Total)

### 1. TELEGRAM (1 variable)
```python
TELEGRAM_BOT_TOKEN  # Required, format: [0-9]+:.*
```

### 2. AI APIS (3 variables)
```python
GEMINI_API_KEY      # Optional, format: AIza.*
OPENAI_API_KEY      # Optional, format: sk-.*
ANTHROPIC_API_KEY   # Optional, format: sk-ant-.*
```

### 3. TRADING APIS (3 variables)
```python
KRAKEN_API_KEY      # Optional, any string
KRAKEN_API_SECRET   # Optional, any string
KRAKEN_STATUS       # Optional, default: 'active'
```

### 4. DATABASE (2 variables)
```python
DATABASE_URL        # Optional, format: postgresql://...
REDIS_URL           # Optional, format: redis://... or rediss://...
```

### 5. SECURITY (2 variables)
```python
SESSION_SECRET      # Optional, min 32 chars
ENCRYPTION_KEY      # Optional, min 32 chars
```

### 6. APP SETTINGS (5 variables)
```python
PORT                # Optional, default: 8000, range: 1-65535
HOST                # Optional, default: '0.0.0.0'
STOCK_TRADING_ENABLED  # Optional, default: 'true', values: true/false
PAPER_MODE          # Optional, default: 'true', values: true/false
LOG_LEVEL           # Optional, default: 'INFO', values: DEBUG/INFO/WARNING/ERROR/CRITICAL
```

### 7. MONITORING (2 variables)
```python
ENABLE_METRICS      # Optional, default: 'true', values: true/false
METRICS_PORT        # Optional, default: 9090, range: 1-65535
```

## 🔐 Security Best Practices

### Replit Environment (Current Setup)
✅ **All credentials in Replit Secrets:**
- TELEGRAM_BOT_TOKEN
- GEMINI_API_KEY
- OPENAI_API_KEY
- KRAKEN_API_KEY
- KRAKEN_API_SECRET

✅ **`.env` file protected** - Cannot be edited (Replit security)

### Railway Deployment

#### Step 1: Add Environment Variables in Railway Dashboard
```bash
# Required
TELEGRAM_BOT_TOKEN=your_token_here

# AI (at least one)
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Trading (for live trading)
KRAKEN_API_KEY=your_key_here
KRAKEN_API_SECRET=your_secret_here

# Database (auto-provided by Railway PostgreSQL addon)
DATABASE_URL=postgresql://...
```

#### Step 2: Verify Railway Config
Ensure `.env.railway` has correct settings:
```bash
# App Settings
PORT=8000
HOST=0.0.0.0
PAPER_MODE=true  # Set to 'false' for live trading
LOG_LEVEL=INFO

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

## 🔄 Migration Checklist for Railway

### Pre-Deployment
- [ ] All secrets added to Railway dashboard
- [ ] `.env.railway` reviewed and updated
- [ ] `PAPER_MODE=true` for testing
- [ ] `DATABASE_URL` added (from Railway PostgreSQL addon)

### Post-Deployment Verification
```bash
# Check logs for EnvConfig initialization
railway logs | grep "EnvConfig"

# Verify bot started successfully
railway logs | grep "BOT TELEGRAM OPERATIVO"

# Check Signal Contribution system
railway logs | grep "Signal Contribution ACTIVADO"

# Verify ARES strategies loaded
railway logs | grep "ARES QUANTUM PROTOCOLS LOADED"
```

## 🎯 Usage Examples

### Basic Usage (main.py)
```python
from omnix_config import env_config

# Simple get with default
bot_token = env_config.get('TELEGRAM_BOT_TOKEN')

# Get with type casting
port = env_config.get('PORT', default=8000, cast_type=int)

# Get boolean
paper_mode = env_config.get('PAPER_MODE', default='true', cast_type=bool)

# Get required value (raises error if missing)
telegram_token = env_config.get_required('TELEGRAM_BOT_TOKEN')

# Get all variables by category
ai_vars = env_config.get_category(EnvCategory.AI_APIS)
```

### Backward Compatibility
```python
# Old code still works
import os
kraken_key = os.environ.get('KRAKEN_API_KEY')

# But new code is better
kraken_key = env_config.get('KRAKEN_API_KEY')
```

## 📊 Impact Metrics

### File Reduction
- **Before**: 9 .env files
- **After**: 4 .env files  
- **Reduction**: -5 files (-55.6%)

### Code Quality
- **Centralization**: All env config in 1 module (442 lines)
- **Validation**: 19 variables with type checking
- **Security**: Masked logging, no credential exposure

### Zero Downtime
✅ Bot remained **RUNNING** during entire migration  
✅ All features operational: Signal Contribution, ARES V1+V2, Arbitrage, AI

## 🐛 Troubleshooting

### Issue: "EnvConfig.get() got unexpected keyword argument"
**Solution**: Use `cast_type=` not `cast=`
```python
# ❌ Wrong
port = env_config.get('PORT', cast=int)

# ✅ Correct
port = env_config.get('PORT', cast_type=int)
```

### Issue: "Required variable TELEGRAM_BOT_TOKEN not found"
**Solution**: Add to Railway environment variables dashboard

### Issue: Bot not connecting to database
**Solution**: Verify `DATABASE_URL` in Railway (auto-added by PostgreSQL addon)

## 📞 Support

For Railway deployment issues:
1. Check Railway logs: `railway logs --tail`
2. Verify env vars: `railway variables`
3. Restart service: `railway restart`

For Replit issues:
1. Check workflow logs in Replit dashboard
2. Verify Replit Secrets are configured
3. Restart workflow: "Stop" → "Run"

---

**Last Updated**: November 25, 2025  
**Version**: OMNIX V6.0 ULTRA  
**Status**: ✅ Production Ready
