# OMNIX V6.5 INSTITUTIONAL+ - Environment Configuration Guide

**Version:** V6.5 INSTITUTIONAL+  
**Last Updated:** December 2024  
**Status:** Production Ready

---

## Overview

This guide documents the centralized environment variable system for OMNIX V6.5, featuring:
- 30+ environment variables cataloged
- Thread-safe singleton configuration
- Type casting and validation
- Secure credential logging

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  DEPLOYMENT PLATFORM                                         │
│  ├─ Replit Secrets (production)                             │
│  ├─ Railway Environment Variables                            │
│  └─ .env.local (development)                                │
└────────────────────────────────────────┬────────────────────┘
                                         │
                ┌────────────────────────▼────────────────────┐
                │  omnix_config/env_manager.py                │
                │  ┌────────────────────────────────────────┐ │
                │  │  EnvConfig (Singleton Thread-Safe)     │ │
                │  │  ├─ Load priority (Secrets > .env)     │ │
                │  │  ├─ Type casting (str/int/bool/float)  │ │
                │  │  ├─ Validation (format, length)        │ │
                │  │  └─ Secure logging (mask credentials)  │ │
                │  └────────────────────────────────────────┘ │
                └────────────────────────────────────────────┘
                                         │
                ┌────────────────────────▼────────────────────┐
                │  omnix_config/settings.py                   │
                │  ┌────────────────────────────────────────┐ │
                │  │  Dataclass Interface (Clean API)       │ │
                │  │  ├─ settings.redis.host                │ │
                │  │  ├─ settings.ai.openai_key             │ │
                │  │  └─ settings.trading.kraken_key        │ │
                │  └────────────────────────────────────────┘ │
                └────────────────────────────────────────────┘
```

---

## Environment Variables Catalog (30+)

### 1. TELEGRAM (2 variables)
```bash
TELEGRAM_BOT_TOKEN         # Required, format: [0-9]+:.*
TELEGRAM_ADMIN_USER_ID     # Required, format: [0-9]{8,10}
```

### 2. AI APIs (3 variables)
```bash
GEMINI_API_KEY             # Optional, format: AIza.*
OPENAI_API_KEY             # Optional, format: sk-.*
ANTHROPIC_API_KEY          # Optional, format: sk-ant-.*
```

### 3. TRADING APIs (4 variables)
```bash
KRAKEN_API_KEY             # Optional, 30+ chars
KRAKEN_API_SECRET          # Optional, 30+ chars
ALPACA_API_KEY             # Optional, 15+ chars (stock trading)
ALPACA_SECRET_KEY          # Optional, 30+ chars
```

### 4. DATABASE (6 variables)
```bash
DATABASE_URL               # Required, format: postgresql://...
REDIS_URL                  # Optional, format: redis://...
REDIS_HOST                 # Optional, default: localhost
REDIS_PORT                 # Optional, default: 6379
REDIS_DB                   # Optional, default: 0
REDIS_PASSWORD             # Optional
```

### 5. SECURITY (3 variables)
```bash
SESSION_SECRET             # Required, min 32 chars
ENCRYPTION_KEY             # Optional, min 32 chars
SECRET_KEY                 # Optional, for Flask sessions
```

### 6. MARKET INTELLIGENCE (2 variables)
```bash
FINNHUB_API_KEY            # Required, for news/sentiment
ALPHA_VANTAGE_API_KEY      # Required, for technical indicators
```

### 7. APP SETTINGS (7 variables)
```bash
PORT                       # Optional, default: 5000
HOST                       # Optional, default: 0.0.0.0
STOCK_TRADING_ENABLED      # Optional, default: true
PAPER_MODE                 # Optional, default: true
LOG_LEVEL                  # Optional, default: INFO
ENVIRONMENT                # Optional, default: development
DEBUG                      # Optional, default: false
```

### 8. MONITORING (3 variables)
```bash
ENABLE_METRICS             # Optional, default: true
METRICS_PORT               # Optional, default: 9090
SENTRY_DSN                 # Optional, for error tracking
```

---

## Usage Examples

### Basic Usage
```python
from omnix_config import env_config

# Simple get with default
bot_token = env_config.get('TELEGRAM_BOT_TOKEN')

# Get with type casting
port = env_config.get('PORT', default=5000, cast_type=int)

# Get boolean
paper_mode = env_config.get('PAPER_MODE', default='true', cast_type=bool)

# Get required value (raises error if missing)
db_url = env_config.get_required('DATABASE_URL')
```

### Using Settings Interface
```python
from omnix_config import settings

# Clean dataclass access
redis_host = settings.redis.host
kraken_key = settings.trading.kraken_key
openai_key = settings.ai.openai_key
```

---

## Deployment Workflows

### Local Development
```bash
# 1. Create .env.local (gitignored)
cp .env.example .env.local

# 2. Edit with your credentials
nano .env.local

# 3. Run bot
python main.py

# EnvConfig loads: .env.local > defaults
```

### Railway Production
```bash
# 1. Add secrets in Railway Dashboard:
#    Settings → Variables → Add Variable
TELEGRAM_BOT_TOKEN=your_token
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# 2. Deploy automatically
git push origin main

# EnvConfig loads: Railway Env Vars (os.environ)
```

### Replit Production
```bash
# 1. Use Replit Secrets (Tools → Secrets)
TELEGRAM_BOT_TOKEN=your_token
DATABASE_URL=postgresql://...

# 2. .env is protected (read-only)

# EnvConfig loads: Replit Secrets > .env
```

---

## Adding New Variables

### Step 1: Define in env_manager.py
```python
'NEW_API_KEY': {
    'category': EnvCategory.AI_APIS,
    'required': False,
    'validator': lambda x: x.startswith('nk-') and len(x) > 30,
    'description': 'API Key for new service'
}
```

### Step 2: Add to settings.py
```python
@dataclass
class AISettings:
    new_api_key: Optional[str] = env_config.get('NEW_API_KEY')
```

### Step 3: Document in .env.example
```bash
# NEW SERVICE (Optional)
# NEW_API_KEY=nk-your-api-key-here
```

---

## Troubleshooting

### Error: "Variable XXX is required but not found"
**Solution**: Add to Replit Secrets or Railway environment variables

### Error: "Validation failed for XXX"
**Solution**: Check format requirements in VARIABLE_CATALOG

### Variables not updating after .env change
**Solution**: Restart workflow (EnvConfig is singleton, loads once)

### Credentials exposed in logs
**Solution**: Always use `env_config.get()` which auto-masks sensitive values

---

## Security Best Practices

### Credential Rotation
If credentials were exposed, rotate immediately:

1. **TELEGRAM_BOT_TOKEN**: BotFather → /token → Revoke
2. **KRAKEN_API_KEY**: Kraken.com → Settings → API → Revoke
3. **GEMINI_API_KEY**: Google Cloud Console → Credentials → Delete/Create
4. **OPENAI_API_KEY**: OpenAI Dashboard → API Keys → Revoke

### Never Commit
- `.env` files with real credentials
- API keys in code comments
- Secrets in logs or error messages

---

## Deployment Checklist

### Pre-Deployment
- [ ] All required variables configured
- [ ] `.env.local` NOT committed
- [ ] Credentials rotated if exposed
- [ ] `PAPER_MODE=true` for testing
- [ ] `LOG_LEVEL=INFO` for production

### Post-Deployment
- [ ] Logs show: `EnvConfig initialized successfully`
- [ ] Logs show: `BOT TELEGRAM OPERATIVO`
- [ ] Test `/start` command in Telegram
- [ ] Verify Kraken connection
- [ ] Verify database connection

---

**Document Version:** 3.0  
**OMNIX V6.5 INSTITUTIONAL+**  
**Last Updated:** December 2024
