---
name: Replit deploy image size limit
description: Cómo resolver el error "image size is over the limit of 8 GiB" en Replit autoscale deployments.
---

## El problema

El build del deployment de Replit empaqueta TODO el sistema de archivos del workspace en el "Repl layer". El límite es 8 GiB. Cuando el workspace incluye `.pythonlibs/` (1.7 GB) + `.git/` (365 MB) + `node_modules/` (315 MB), el container supera el límite.

El error aparece al final del log del build:
```
2026-05-31T03:07:40Z error: image size is over the limit of 8 GiB
```

## Lo que NO funciona

`.replit_ignore` — Replit NO respeta este archivo para reducir el Repl layer. El archivo existe y tiene sintaxis correcta, pero el build incluye los directorios igualmente. No usar como solución.

## La solución correcta

**Eliminar físicamente los directorios pesados del workspace antes del deploy:**

```bash
rm -rf .pythonlibs/          # 1.7 GB — pip los reinstala desde requirements.txt
rm -rf omnix_web/node_modules/ # 315 MB — npm los reinstala en el build
```

**Actualizar el build command para incluir `npm ci`** (porque node_modules ya no están):
```javascript
await deployConfig({
  deploymentTarget: "autoscale",
  build: ["bash", "-c", "cd omnix_web && npm ci && npm run build"],
  run: ["bash", "-c", "gunicorn --bind=0.0.0.0:${PORT:-5000} --reuse-port --workers=2 --timeout=120 omnix_dashboard.app:app"]
});
```

## Consecuencia en el entorno de desarrollo

Después de eliminar `.pythonlibs/`, todos los workflows fallan con "No module named flask". Replit reinstala los paquetes automáticamente, pero tarda. Para restaurar más rápido:

```bash
pip install flask gunicorn flask-cors flask-limiter redis psycopg2-binary oqs cryptography openai anthropic google-genai python-dotenv PyJWT
pip install -r requirements.txt --quiet &  # en background para el resto
```

**Why:** El Repl layer de Replit es una snapshot completa del filesystem del workspace, no solo el código del repo. Los directorios generados (`.pythonlibs/`, `node_modules/`) crecen con el tiempo y eventualmente superan el límite de 8 GiB.

**How to apply:** Antes de cada deploy cuando el build falle con "image size is over the limit", ejecutar los dos `rm -rf` y luego publicar.
