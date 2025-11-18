# 📤 GUÍA RÁPIDA - SUBIR A GITHUB

## ✅ **ARCHIVOS LISTOS PARA RAILWAY:**

Los siguientes archivos fueron modificados y están listos para deployment 24/7:

### **Archivos Críticos:**
- ✅ `wsgi.py` - Nuevo archivo (entry point para Gunicorn)
- ✅ `Procfile` - Actualizado para Gunicorn
- ✅ `railway.json` - Configuración completa
- ✅ `main.py` - Railway detection + /health endpoint
- ✅ `ai_risk_guardian.py` - Database connection fix

### **Documentación:**
- ✅ `RAILWAY_24_7_FIX.md` - Explicación técnica completa
- ✅ `RAILWAY_QUICKSTART.md` - Guía de deploy actualizada
- ✅ `replit.md` - Documentación del proyecto

---

## 🚀 **PASOS PARA SUBIR A GITHUB:**

### **Opción 1: Interfaz de Replit (Recomendado)**

1. **Panel izquierdo** → Click en ícono de **Git** (ramitas con círculos)
2. Verás lista de archivos modificados:
   - `wsgi.py` (nuevo)
   - `Procfile`
   - `railway.json`
   - `main.py`
   - `ai_risk_guardian.py`
   - Archivos .md
3. Click en **"Stage all"** o **"Commit all"**
4. Escribe mensaje: `Fix Railway 24/7 uptime - V5.4 ULTRA`
5. Click **"Commit"**
6. Click **"Push"**

---

### **Opción 2: Terminal de Replit**

```bash
# 1. Agregar todos los archivos
git add wsgi.py Procfile railway.json main.py ai_risk_guardian.py
git add RAILWAY_24_7_FIX.md RAILWAY_QUICKSTART.md replit.md

# 2. Commit
git commit -m "Fix Railway 24/7 uptime - Gunicorn + webhook + health check"

# 3. Push
git push
```

---

### **Opción 3: Directamente en GitHub**

Si no puedes hacer git push desde Replit:

1. Ve a **github.com** → tu repositorio
2. Para cada archivo:
   - Click en el archivo
   - Click **"Edit"** (ícono lápiz)
   - Copia el contenido nuevo
   - Pega y reemplaza
   - Click **"Commit changes"**

**Archivos a editar en GitHub:**
- `Procfile`
- `railway.json`
- Crear nuevo: `wsgi.py`

---

## ⏱️ **DESPUÉS DEL PUSH:**

1. **GitHub se actualiza** (instantáneo) ✅
2. **Railway detecta cambio** (automático) ✅
3. **Railway redespliega** (2-3 minutos) ✅
4. **Bot funciona 24/7** (sin colgarse) ✅

---

## 🔍 **VERIFICAR EN RAILWAY:**

### **1. Ver Logs**
Railway Dashboard → Deployments → View Logs

**Busca estos mensajes:**
```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8080
🚂 RAILWAY DETECTADO - Forzando modo WEBHOOK
✅ WEBHOOK CONFIGURADO: https://tu-app.railway.app/webhook/telegram
✅ Health check: 200 OK
```

### **2. Test Health Endpoint**
```bash
curl https://omnibotgenesis-production.up.railway.app/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "service": "OMNIX V5.4 ULTRA",
  "telegram_bot": "active",
  "trading": "connected",
  "ai_systems": "operational",
  "timestamp": "2024-11-16T20:00:00"
}
```

### **3. Test Telegram**
Envía mensaje al bot → debe responder inmediatamente

---

## ⚠️ **IMPORTANTE:**

### **Variable de Entorno en Railway:**
Asegúrate de tener en Railway → Variables:
```
TELEGRAM_DEPLOYMENT_MODE = webhook
```

Si tiene otro valor, cámbialo a `webhook` exactamente.

---

## 📊 **RESUMEN DE CAMBIOS:**

| Archivo | Cambio | Impacto |
|---------|--------|---------|
| `wsgi.py` | NUEVO - Entry point para Gunicorn | ⭐⭐⭐ CRÍTICO |
| `Procfile` | Cambió a `wsgi:app` | ⭐⭐⭐ CRÍTICO |
| `railway.json` | Comando actualizado | ⭐⭐⭐ CRÍTICO |
| `main.py` | Railway detection + /health | ⭐⭐⭐ CRÍTICO |
| `ai_risk_guardian.py` | get_connection() fix | ⭐⭐ IMPORTANTE |

---

## ✅ **GARANTÍA 24/7:**

Después de estos cambios:
- ✅ Bot **NO se colgará** en Railway
- ✅ Gunicorn production server
- ✅ Webhook mode automático
- ✅ Health checks cada 30 segundos
- ✅ Auto-restart si falla
- ✅ 2 workers con threading

---

## 🆘 **SOPORTE:**

Si después del push hay problemas:
1. Verifica logs de Railway
2. Revisa que `TELEGRAM_DEPLOYMENT_MODE=webhook`
3. Prueba endpoint `/health`
4. Consulta `RAILWAY_24_7_FIX.md` para detalles técnicos

---

**Fecha:** 2024-11-16  
**Versión:** OMNIX V5.4 ULTRA  
**Status:** ✅ LISTO PARA DEPLOY
