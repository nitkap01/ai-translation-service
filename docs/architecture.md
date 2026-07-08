# Architecture

## Overview

The service is a single FastAPI app that serves a static web UI and a small JSON
API. The API runs a three-stage pipeline over three local models.

```
Browser (web/)                    FastAPI (app/main.py)
  │  record / type                   │
  │  POST /api/translate/{text,audio}│
  ▼                                  ▼
                          app/pipeline.py
                                     │
      ┌──────────────┬──────────────┴───────────────┐
      ▼              ▼                               ▼
 app/models/asr  app/models/translate          app/models/tts
  Whisper v3        NLLB-200                     MMS-TTS
 (speech→text)    (text→text)                  (text→speech)
```

## The two flows

**Audio in**

1. `audio.decode_to_16k_mono` uses ffmpeg to turn the upload (webm/mp3/wav/…)
   into the 16 kHz mono float array Whisper expects.
2. `asr.transcribe` returns the text plus the detected language.
3. If the source and target differ, `translate.translate` (NLLB) translates the
   text.
4. If "speak" is on, `tts.synthesize` produces a waveform, encoded to WAV and
   returned as a base64 data URI.

**Text in**

1. Source language is taken from the dropdown, or guessed with `langdetect`.
2. Steps 3–4 above are the same.

## Why three separate models

- **Whisper** is excellent at speech recognition and language detection, but its
  only translation direction is *to English*.
- **NLLB-200** fills that gap: any of its 200 languages to any other. This is
  what makes real Hindi → French (etc.) possible.
- **MMS-TTS** gives spoken output in the target language, one small model each.

Keeping them as separate modules means each can be swapped (e.g. a different TTS)
without touching the rest.

## Language codes

The same language has a different code in each stage. `app/languages.py` is the
single source of truth that maps between them:

| Canonical | Whisper | NLLB (FLORES) | MMS (ISO 639-3) |
| --- | --- | --- | --- |
| `hi` | `hi` | `hin_Deva` | `hin` |
| `en` | `en` | `eng_Latn` | `eng` |

A language appears in the registry only if all three stages support it, so the
UI can never offer a combination that breaks mid-pipeline.

## Lazy model loading

The `app/models/*` modules import torch / transformers / faster-whisper *inside*
their functions, and cache the loaded model with `functools.lru_cache`. Benefits:

- The web app and the test suite import cleanly without the multi-GB ML stack.
- Each model is loaded once, on first use, then reused.

## Device selection

`config.resolve_device()` returns `mps` on Apple Silicon (with a CPU fallback
for unsupported ops), else `cpu`. Whisper runs on CPU via faster-whisper's int8
build, which is fast and light; NLLB and MMS-TTS use the resolved torch device.

## Graceful degradation

If a TTS voice fails to load for some language, the pipeline still returns the
translated **text** and adds a note, rather than failing the whole request.
