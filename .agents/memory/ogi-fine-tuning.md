---
name: OGI Fine-Tuning Pipeline
description: Pipeline completo para entrenar el modelo OMNIX Governance Intelligence en Together.ai. ADR-193 con OGI-INV-001..010.
---

## Decisión clave
Modelo base: Llama-3.1-8B-Instruct (MVP ~$20-30) o Llama-3.3-70B (producción ~$300).
Formato: chat SFT JSONL (mensajes system/user/assistant). Plataforma: Together.ai.

## Archivos creados
- `docs/adr/ADR-193-ogi-fine-tuning-pipeline.md` — spec completa con OGI-INV-001..010
- `scripts/fine_tuning/prepare_corpus.py` — genera corpus desde 138 ADRs/RFCs
- `scripts/fine_tuning/eval_suite_generator.py` — 29 preguntas fijas para 5 gates de deployment
- `scripts/fine_tuning/training_config.yaml` — hiperparámetros Together.ai
- `scripts/fine_tuning/corpus_allowlist.yaml` — lista blanca de seguridad (OGI-INV-001/004)
- `scripts/fine_tuning/ogi_system_prompt.txt` — system prompt canónico del modelo
- `scripts/fine_tuning/GUIA_ENTRENAMIENTO.md` — guía paso a paso en español

## Estado del pipeline (validado con dry-run)
- Corpus actual: ~852 ejemplos válidos de 138 documentos
- Categorías: DEF(374) SCN(176) EXB(109) SRC(106) INV(29) TRM(31) RTR(7) API(6) REG(6) TRC(4) CMP(3) FOR(1)
- Split: 80/10/10 estratificado por categoría

## Lo que falta para ejecutar
1. Cuenta en Together.ai (gratis)
2. $20-30 de crédito
3. Ejecutar: `pip install pyyaml together` y luego los scripts en orden (ver GUIA_ENTRENAMIENTO.md)
4. Tras fine-tune: añadir OMNIX_OGI_MODEL_ENDPOINT + TOGETHER_API_KEY en Railway

## Integración SAL (ADR-190)
Cuando OMNIX_OGI_MODEL_ENDPOINT está configurado, la cadena SAL se convierte en:
OGI (modelo propio) → Groq/Llama-3 → Mistral → Gemini → OpenAI → Anthropic

**Why:** El modelo OGI elimina alucinaciones en vocabulario OMNIX (ATF-INV-*, BEV-INV-*, etc.)
y crea un moat competitivo que crece con cada ADR nuevo publicado.

**How to apply:** Cuando Harold tenga cuenta Together.ai, implementar el provider OGI
en AIModelsManager (ai_models.py) — solo requiere añadir ~40 líneas siguiendo el patrón
de los providers existentes en ADR-190.
