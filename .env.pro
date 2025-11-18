# OMNIX Pro System Environment Variables
# Configuración para versión profesional

# Kraken API
KRAKEN_API_KEY=tu_kraken_api_key_aqui
KRAKEN_API_SECRET=tu_kraken_api_secret_aqui

# Telegram Bot
TELEGRAM_BOT_TOKEN=tu_telegram_bot_token_aqui

# Webhook Configuration
WEBHOOK_URL=https://tu-dominio.com
WEBHOOK_PORT=5000

# Database
DATABASE_URL=sqlite:///omnix_pro.db
DATABASE_BACKUP_INTERVAL=3600

# AI Models
OPENAI_API_KEY=tu_openai_api_key_aqui
GEMINI_API_KEY=tu_gemini_api_key_aqui

# Trading Configuration
MAX_TRADES_PER_DAY=15
MAX_DAILY_LOSS=50.0
TARGET_DAILY_PROFIT=15.0
MIN_BALANCE_USD=150.0
TRADING_INTERVAL=120

# Security
SECRET_KEY=tu_secret_key_super_seguro_aqui
JWT_SECRET=tu_jwt_secret_aqui
ENCRYPTION_KEY=tu_encryption_key_aqui

# Logging
LOG_LEVEL=INFO
LOG_FILE=omnix_pro.log
LOG_ROTATION=midnight
LOG_RETENTION=30

# Dashboard
DASHBOARD_PORT=5050
DASHBOARD_HOST=0.0.0.0
DASHBOARD_DEBUG=false

# Monitoring
MONITORING_ENABLED=true
MONITORING_INTERVAL=300
HEALTH_CHECK_INTERVAL=60

# Performance
CACHE_TTL=30
MAX_WORKERS=4
REQUEST_TIMEOUT=30

# Features
VOICE_ENABLED=true
MULTILINGUAL_ENABLED=true
AUTO_TRADING_ENABLED=true
WEBHOOK_ENABLED=true

# Development
DEBUG=false
TESTING=false
ENVIRONMENT=production