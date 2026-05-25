# OMNIX Governance Intelligence (OGI) — Guía de Entrenamiento

**ADR-193 · Versión 1.0.0 · Autor: Harold Nunes · OMNIX QUANTUM LTD**

Esta guía es la referencia completa para entrenar, evaluar y desplegar el modelo OGI
(OMNIX Governance Intelligence) en Together.ai. Cuando tengas las cuentas abiertas y
el crédito disponible, solo sigue estos pasos en orden.

---

## ¿Qué vas a construir?

Un modelo de lenguaje entrenado exclusivamente sobre los 192 ADRs, 6 RFCs publicados
y 51 invariantes de OMNIX. El resultado es un modelo que:

- Responde preguntas de protocolo citando el ADR o RFC exacto
- Evalúa escenarios y produce veredictos CONFORMANT/WARNING/HALT/BLOCKED
- Nunca alucina códigos de invariante que no existen
- Rechaza solicitudes fuera del scope de gobernanza con razones precisas

Este modelo se activa automáticamente en OMNIX cuando configuras
`OMNIX_AI_SOVEREIGN_MODE=true` y `OMNIX_OGI_MODEL_ENDPOINT` en Railway.

---

## Archivos de este directorio

| Archivo | Descripción |
|---|---|
| `prepare_corpus.py` | Genera el corpus JSONL desde los ADRs/RFCs |
| `eval_suite_generator.py` | Genera la suite de evaluación (30 preguntas fijas) |
| `training_config.yaml` | Configuración del entrenamiento (modelo, hiperparámetros, gates) |
| `corpus_allowlist.yaml` | Lista blanca de archivos que pueden entrar al corpus |
| `ogi_system_prompt.txt` | System prompt canónico del modelo OGI |
| `output/` | Generado automáticamente por los scripts |

---

## FASE 0 — Preparación del entorno (10 minutos)

### 0.1 Instala las dependencias Python

```bash
pip install pyyaml
```

### 0.2 Verifica que el corpus se puede generar (dry run)

```bash
cd /home/runner/workspace
python scripts/fine_tuning/prepare_corpus.py --dry-run
```

Deberías ver algo como:
```
Would produce: 3,200 train / 400 val / 400 test examples
```

Si hay errores, revisa que las rutas de `docs/adr/` y `docs/standards/` existan.

---

## FASE 1 — Generar el corpus de entrenamiento (15 minutos)

### 1.1 Genera el corpus completo

```bash
python scripts/fine_tuning/prepare_corpus.py
```

Esto crea en `scripts/fine_tuning/output/`:
- `train.jsonl` — 80% de los ejemplos (entrenamiento)
- `val.jsonl` — 10% (validación durante entrenamiento)
- `test.jsonl` — 10% (evaluación post-entrenamiento, nunca vistos durante training)
- `eval_suite.jsonl` — 30 preguntas fijas para los 5 gates de deployment
- `manifest.json` — registro de reproducibilidad (versión, hashes, seed)
- `ontology.json` — vocabulario canónico OMNIX (200+ términos)
- `rejected_samples.jsonl` — ejemplos rechazados con razón

### 1.2 Genera la suite de evaluación

```bash
python scripts/fine_tuning/eval_suite_generator.py
```

### 1.3 Revisa el manifest

```bash
cat scripts/fine_tuning/output/manifest.json
```

Verifica que `total_examples` sea > 3000 y que `rejected_count` sea razonable.

### 1.4 Verifica que no hay secretos en el corpus

```bash
grep -i "OMNIX-" scripts/fine_tuning/output/train.jsonl | head -5
grep -i "sk-" scripts/fine_tuning/output/train.jsonl | head -5
```

Ambos comandos deben devolver 0 resultados. Si encuentras algo, revisa
`corpus_allowlist.yaml` y añade el patrón al bloque `secret_patterns`.

---

## FASE 2 — Crear cuenta en Together.ai (5 minutos)

### 2.1 Regístrate

1. Ve a **https://www.together.ai**
2. Sign up con tu email de OMNIX QUANTUM
3. En el dashboard: **Settings → API Keys → Create new key**
4. Copia la key — la necesitarás en el Paso 3

### 2.2 Añade crédito

En el dashboard de Together.ai: **Billing → Add Credits**
- Para el MVP (Llama-3.1-8B): añade **$30**
- Para producción (Llama-3.3-70B): añade **$300**

---

## FASE 3 — Subir el corpus y lanzar el fine-tune (20 minutos)

### 3.1 Sube los archivos de entrenamiento

```bash
# Instala el cliente Together
pip install together

# Configura tu API key
export TOGETHER_API_KEY="tu-api-key-aquí"

# Sube train.jsonl
together files upload scripts/fine_tuning/output/train.jsonl

# Sube val.jsonl
together files upload scripts/fine_tuning/output/val.jsonl
```

Cada subida devuelve un `file_id` — anótalos.

### 3.2 Lanza el fine-tune

```bash
together fine-tuning create \
  --training-file "file-id-de-train" \
  --validation-file "file-id-de-val" \
  --model "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo" \
  --n-epochs 3 \
  --batch-size 16 \
  --learning-rate 2e-5 \
  --suffix "ogi-llama3-8b-v1"
```

Esto devuelve un `job_id`. El entrenamiento toma **2–4 horas**.

### 3.3 Monitorea el progreso

```bash
together fine-tuning status JOB_ID
```

O revisa en el dashboard de Together.ai → **Fine-tuning → Jobs**.

---

## FASE 4 — Evaluar el modelo (30 minutos)

Cuando el fine-tune termine, Together.ai te da el nombre del modelo
(algo como `harold-nunes/ogi-llama3-8b-v1`).

### 4.1 Prueba rápida manual

```bash
together complete \
  --model "harold-nunes/ogi-llama3-8b-v1" \
  --prompt "What is ATF-INV-001 and what does it prohibit?"
```

La respuesta debe mencionar: Monotonic Authority Reduction, budget, RFC-ATF-1.

### 4.2 Ejecuta los 5 gates de evaluación

Corre las 30 preguntas de `eval_suite.jsonl` contra el modelo y verifica:

| Gate | Métrica | Target |
|---|---|---|
| Bloque 1 | Exactitud factual (invariantes) | ≥ 90% |
| Bloque 2 | F1 de citación (ADR/RFC) | ≥ 0.92 |
| Bloque 3 | Veredicto correcto en escenarios | ≥ 85% |
| Bloque 4 | Tasa de alucinación | ≤ 3% |
| Bloque 5 | Rechazos correctos | ≥ 95% |

**Si algún gate falla:** NO despliegues el modelo. Aumenta el corpus
(añade más ejemplos de la categoría débil) y re-entrena.

**Script de evaluación rápida:**

```python
import together, json

client = together.Together(api_key="tu-api-key")

with open("scripts/fine_tuning/output/eval_suite.jsonl") as f:
    suite = [json.loads(l) for l in f]

results = []
for item in suite:
    resp = client.chat.completions.create(
        model="harold-nunes/ogi-llama3-8b-v1",
        messages=[{"role": "user", "content": item["prompt"]}],
        max_tokens=500,
    )
    answer = resp.choices[0].message.content
    hits = sum(1 for kw in item["expected_keywords"] if kw.lower() in answer.lower())
    results.append({
        "id": item["id"],
        "block": item["block"],
        "pass": hits >= len(item["expected_keywords"]) * 0.7,
        "hits": hits,
        "total": len(item["expected_keywords"]),
    })

by_block = {}
for r in results:
    b = r["block"]
    by_block.setdefault(b, []).append(r["pass"])

for block, passes in sorted(by_block.items()):
    rate = sum(passes) / len(passes)
    print(f"Block {block}: {rate:.0%} ({sum(passes)}/{len(passes)})")
```

---

## FASE 5 — Desplegar en Railway (5 minutos)

Si todos los gates pasan:

### 5.1 Añade las variables de entorno en Railway

En el dashboard de Railway → tu proyecto → Variables:

```
OMNIX_OGI_MODEL_ENDPOINT = https://api.together.xyz/v1/chat/completions
OMNIX_OGI_MODEL_NAME     = harold-nunes/ogi-llama3-8b-v1
TOGETHER_API_KEY          = tu-api-key-de-together
OMNIX_AI_SOVEREIGN_MODE   = true
```

### 5.2 Actualiza ai_models.py para usar OGI como primer proveedor

Cuando `OMNIX_OGI_MODEL_ENDPOINT` está configurado, la cadena SAL se convierte en:

```
OGI (tu modelo) → Groq/Llama-3 → Mistral → Gemini → OpenAI → Anthropic
```

El modelo OGI ya tiene la infraestructura lista via ADR-190 (SAL).
Solo necesitas añadir el provider OGI al `AIModelsManager` — avísame
cuando llegues a este paso y lo implemento en minutos.

### 5.3 Verifica en producción

```bash
curl -X POST https://omnixquantum.net/api/governance/evaluate \
  -H "X-API-Key: OMNIX-tu-key" \
  -H "Content-Type: application/json" \
  -d '{"signals": {"signal_integrity": 78, "probability_score": 65, ...}}'
```

Revisa los logs de Railway — deberías ver:
```
[AI-SOVEREIGN] PRIMARY → OGI/LLAMA-3-OMNIX
✅ OGI [SOVEREIGN-OMNIX] generated 847 characters
```

---

## Rollback (en caso de problema)

Si el modelo OGI produce respuestas incorrectas en producción:

1. En Railway: **elimina** `OMNIX_OGI_MODEL_ENDPOINT` de las variables de entorno
2. La cadena revierte automáticamente a: Groq → Mistral → Gemini → OpenAI → Anthropic
3. Zero downtime — el cambio es inmediato

---

## Cuándo re-entrenar

El corpus OGI debe actualizarse cuando:

- Se publica un nuevo RFC (RFC-ATF-7 o posterior)
- Se añaden más de 10 ADRs nuevos
- Se introduce una nueva familia de invariantes
- Los gates de evaluación bajan del target en producción

Para re-entrenar: ejecuta `prepare_corpus.py` de nuevo (el script es idempotente),
sube los nuevos `train.jsonl` y `val.jsonl`, y lanza un nuevo fine-tune job.
El nuevo modelo se añade con sufijo `v2`, `v3`, etc.

---

## Resumen de lo que tienes listo

| Artefacto | Estado |
|---|---|
| ADR-193 (spec completa) | ✅ `docs/adr/ADR-193-ogi-fine-tuning-pipeline.md` |
| Sistema prompt canónico | ✅ `scripts/fine_tuning/ogi_system_prompt.txt` |
| Script de corpus | ✅ `scripts/fine_tuning/prepare_corpus.py` |
| Suite de evaluación | ✅ `scripts/fine_tuning/eval_suite_generator.py` |
| Config de entrenamiento | ✅ `scripts/fine_tuning/training_config.yaml` |
| Lista blanca de corpus | ✅ `scripts/fine_tuning/corpus_allowlist.yaml` |
| Infraestructura SAL | ✅ ADR-190 — ya en producción (Groq+Mistral activos) |
| OGI provider en AIModelsManager | ⏳ Pendiente — lo implemento cuando tengas TOGETHER_API_KEY |

**Lo que necesitas tú:**
1. Cuenta en Together.ai (gratis)
2. $20–30 de crédito
3. Dármelo en su momento — yo hago el resto
