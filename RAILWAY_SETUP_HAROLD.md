# 🚂 QUÉ HACER PARA QUE OMNIX FUNCIONE EN RAILWAY

Harold, aquí tienes los pasos EXACTOS para desplegar OMNIX en Railway:

---

## ✅ CHECKLIST DE DEPLOYMENT

### 1. CREAR CUENTA EN RAILWAY (2 minutos)

1. Ve a **railway.app**
2. Haz click en **"Login"** o **"Start a New Project"**
3. Conecta tu cuenta de GitHub
4. Ya tienes cuenta ✅

---

### 2. SUBIR OMNIX A GITHUB (5 minutos)

**Si ya tienes GitHub conectado a Replit:**
- Replit → Git → Push to GitHub
- Tu código se sube automáticamente

**Si NO tienes GitHub:**
1. Ve a **github.com**
2. Click **"New repository"**
3. Nombra: `omnix-v5-trading-bot`
4. En Replit: Git → Connect to GitHub → Selecciona el repo
5. Push changes

---

### 3. CREAR PROYECTO EN RAILWAY (3 minutos)

1. En Railway Dashboard → **"New Project"**
2. Click **"Deploy from GitHub repo"**
3. Selecciona tu repo `omnix-v5-trading-bot`
4. Railway detecta automáticamente que es Python ✅

---

### 4. AGREGAR BASES DE DATOS (2 minutos)

#### PostgreSQL:
1. En tu proyecto → Click **"+ New"**
2. Selecciona **"Database"** → **"Add PostgreSQL"**
3. Railway crea `DATABASE_URL` automáticamente ✅

#### Redis:
1. Click **"+ New"** de nuevo
2. Selecciona **"Database"** → **"Add Redis"**
3. Railway crea `REDIS_URL` automáticamente ✅

---

### 5. CONFIGURAR VARIABLES DE ENTORNO (5 minutos)

En Railway → Tu servicio principal → Tab **"Variables"**:

**OBLIGATORIAS (Para empezar):**
```
TELEGRAM_BOT_TOKEN = tu_token_de_botfather
OPENAI_API_KEY = sk-proj-...
GEMINI_API_KEY = ...
```

**OPCIONALES (Para trading real después):**
```
KRAKEN_API_KEY = tu_api_key
KRAKEN_API_SECRET = tu_api_secret
```

### Cómo obtener cada variable:

**TELEGRAM_BOT_TOKEN:**
1. Abre Telegram
2. Busca **@BotFather**
3. Envía `/newbot`
4. Sigue instrucciones
5. Copia el token que te da

**OPENAI_API_KEY:**
1. Ve a **platform.openai.com**
2. API Keys → Create new secret key
3. Copia la key (empieza con `sk-proj-...`)

**GEMINI_API_KEY:**
1. Ve a **aistudio.google.com/app/apikey**
2. Create API Key
3. Copia la key

---

### 6. DEPLOY AUTOMÁTICO (1 minuto)

Railway despliega automáticamente cuando configuras todo.

**Verifica en Logs:**
- Click en tu servicio → Tab **"Deployments"** → **"View Logs"**
- Deberías ver:
  ```
  ✅ OMNIX V5.4 iniciado
  ✅ Telegram Bot conectado
  ✅ PostgreSQL conectado
  ✅ Redis conectado
  ```

---

### 7. PROBAR QUE FUNCIONA (2 minutos)

Abre Telegram y envía a tu bot:

```
/start
```

Si responde, **¡FUNCIONA!** 🎉

Luego prueba:
```
/status
/balance
```

---

### 8. CARGAR ESTRATEGIA PROFESIONAL 73% WIN RATE (1 minuto)

Envía este mensaje a tu bot en Telegram:

```
📊 ESTRATEGIA PROFESIONAL - 73% WIN RATE

RSI Sobreventa: 30
RSI Sobrecompra: 70
EMA Rápida: 9
EMA Media: 21
EMA Lenta: 50

Fuente: https://www.quantifiedstrategies.com/macd-and-rsi-strategy/
```

Luego:
```
/ver_propuestas
/aprobar_ajustes
```

**¡YA ESTÁ!** La estrategia profesional está cargada ✅

---

### 9. INICIAR AUTO-TRADING (30 segundos)

En Telegram:

```
/autotrading start
```

OMNIX empezará a operar 24/7 con Paper Trading ($1M virtuales).

---

## 💰 COSTOS

**Railway:** $5/mes (incluye PostgreSQL + Redis)
**OpenAI API:** ~$10-30/mes
**Gemini:** GRATIS hasta 60 req/min
**Kraken:** $0 (solo comisiones si operas real)

**TOTAL: ~$15-35/mes**

---

## 🆘 SI ALGO FALLA

### Error: "Database connection failed"
➡️ Verifica que agregaste PostgreSQL en Railway
➡️ La variable `DATABASE_URL` debe aparecer en "Variables"

### Error: "Redis connection failed"
➡️ Verifica que agregaste Redis
➡️ La variable `REDIS_URL` debe aparecer en "Variables"

### Error: "Telegram bot token invalid"
➡️ Revisa que copiaste bien el token de @BotFather
➡️ Sin espacios extra al inicio o final

### Error: "OpenAI API key invalid"
➡️ Verifica que la key empieza con `sk-proj-`
➡️ Verifica que tienes créditos en platform.openai.com

---

## 📱 COMANDOS ÚTILES POST-DEPLOY

```
/status              # Ver estado completo
/balance             # Balance paper trading
/autotrading start   # Iniciar trading 24/7
/autotrading stop    # Detener trading
/performance         # Ver rendimiento
/risk_status         # Ver protecciones activas
/coherence           # Ver validación de estrategias
/quantum_stats       # Ver stats quantum
```

---

## ✅ RESUMEN RÁPIDO

1. ✅ Crea cuenta Railway
2. ✅ Sube código a GitHub
3. ✅ Deploy from GitHub en Railway
4. ✅ Agrega PostgreSQL
5. ✅ Agrega Redis
6. ✅ Configura variables (TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, GEMINI_API_KEY)
7. ✅ Verifica logs
8. ✅ Prueba `/start` en Telegram
9. ✅ Carga estrategia 73%
10. ✅ `/autotrading start`

**¡LISTO! OMNIX corriendo en la nube 24/7** 🚀

---

**DOCUMENTACIÓN COMPLETA:** Ver `RAILWAY_QUICKSTART.md`
**ARQUITECTURA:** Ver `replit.md`
**ESTRATEGIA 73%:** Documentada en ambos archivos arriba
