---
name: Sovereign AI Layer
description: Groq/Llama-3 y Mistral añadidos como proveedores soberanos en AIModelsManager. Controlado por OMNIX_AI_SOVEREIGN_MODE env var.
---

# ADR-190 — OMNIX Sovereign AI Layer

**Why:** OMNIX dependía 100% de Google/OpenAI/Anthropic. Regulados (defensa, banca central) no pueden aceptar eso. Competidores (UHG-Tech OMNEX) usan esto como diferenciador.

**How to apply:**
- Proveedores añadidos: Groq (Llama-3.3-70b-versatile) + Mistral (mistral-large-latest)
- Ambos usan AsyncOpenAI con base_url override — API OpenAI-compatible
- Archivo: `omnix_services/ai_service/ai_models.py`
- Métodos: `_initialize_groq()`, `_initialize_mistral()`, `_generate_groq_async()`, `_generate_mistral_async()`
- En `generate()`: routing via `'groq' in model_name.lower()` y `'mistral' in model_name.lower()`
- `health_check()` ahora incluye groq y mistral
- Variables Railway necesarias: `GROQ_API_KEY`, `MISTRAL_API_KEY`, `OMNIX_AI_SOVEREIGN_MODE`
- Sin las keys, los proveedores se saltan silenciosamente (SAL-INV-002)
