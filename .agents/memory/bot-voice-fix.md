---
name: Bot Voice Fix
description: gTTS genera MP3; voice_controller enviaba como sendAudio (música) en vez de sendVoice (nota de voz). Fix aplicado 2026-05-27.
---

## Problema
`voice_service.py` usa gTTS → genera archivos `.mp3`.
`voice_controller.py` tenía lógica: si `.mp3` → `sendAudio` (aparece como archivo de música en Telegram, no se escucha como nota de voz).

## Fix
Cambiar ambos paths (sync en línea ~294 y async en línea ~448) para usar siempre `sendVoice` con `audio/mpeg`. Telegram acepta MP3 en `sendVoice` desde versiones recientes — se renderiza como nota de voz con forma de onda.

**Why:** `sendAudio` = reproductor de música (título, artista, barra de progreso). `sendVoice` = nota de voz (forma de onda). Harold veía el mensaje pero sin sonido porque era un archivo de audio, no una nota de voz interactiva.

**How to apply:** Si se cambia el TTS a uno que genere OGG/Opus, mantener `sendVoice` — solo cambiar el MIME type a `audio/ogg`.
