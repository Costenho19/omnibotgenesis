# OMNIX V5.2 - Estructura del Proyecto

## 📁 Estructura Limpia y Organizada

```
OMNIX/
├── main.py                          # Bot principal Telegram
├── auto_trading_bot.py              # Trading automático 24/7
├── requirements.txt                 # Dependencias Python
│
├── config/                          # Configuración centralizada
│   └── settings.py                  # Settings generales
│
├── omnix_services/                  # Servicios modulares
│   ├── ai_service/                  # IA multi-modelo (GPT-4o, Gemini, Claude)
│   ├── trading_service/             # Kraken API + WebSocket
│   ├── database_service/            # PostgreSQL + Redis
│   ├── voice_service/               # TTS/STT + biometría
│   ├── alerts/                      # Smart alerts
│   └── telegram_service/            # Telegram handlers
│
├── omnix_core/                      # Core utilities
│   ├── cache/                       # Redis state management
│   ├── utils/                       # Loggers, rate limiters
│   ├── models/                      # Data models
│   └── queue/                       # Task queues
│
├── advanced_features.py             # 9 estrategias V5.2
├── adaptive_weight_system.py        # Sistema de pesos adaptativos
├── auto_learning_system.py          # Auto-learning de videos
├── video_learning_analyzer.py       # Análisis de videos
├── video_analyzer_ultra.py          # GPT-4 Vision + Gemini
├── chart_pattern_detector.py        # Detección de patrones
├── sentiment_analyzer_advanced.py   # Análisis de sentimiento
├── paper_trading.py                 # Paper trading manager
├── pqc_security.py                  # Post-Quantum Crypto
├── stripe_integration.py            # Pagos Stripe
│
└── replit.md                        # Memoria del sistema
```

## 🎯 Archivos Principales

**Core Trading:**
- `main.py` - Bot Telegram con 100+ comandos
- `auto_trading_bot.py` - Trading automático REAL/PAPER
- `advanced_features.py` - 9 estrategias cuantitativas

**AI & ML:**
- `video_learning_analyzer.py` - Aprende de videos de trading
- `adaptive_weight_system.py` - Pesos dinámicos Hurst + α-stable
- `sentiment_analyzer_advanced.py` - Sentiment multi-dimensional

**Seguridad:**
- `pqc_security.py` - Kyber-768 + Dilithium-3 (NIST FIPS)

## ✅ Limpieza Completada

**Eliminado:**
- ❌ 300+ scripts duplicados
- ❌ Archivos temporales (temp/, audio_output/, logs/)
- ❌ Templates HTML no usados
- ❌ Assets de video/imágenes
- ❌ Configuraciones de deploy antiguas
- ❌ Backups y archivos _COPY_

**Mantenido:**
- ✅ 15 archivos Python core
- ✅ Estructura modular limpia
- ✅ Servicios organizados por función
- ✅ Configuración centralizada
