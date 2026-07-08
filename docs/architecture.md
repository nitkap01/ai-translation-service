# Architecture

## Overview

The service is a single FastAPI app that serves a static web UI and a small JSON
API. The API runs a three-stage pipeline over three local models.

```
Browser (web/)                       FastAPI (app/main.py)
  │  record / type                      │  lifespan: warmup.start_background()
  │  POST /api/translate/{text,audio}   │  GET /api/health -> warmup state
  ▼                                     ▼
                             app/pipeline.py
                                        │
      ┌───────────────┬─────────────────┴──────────────────┐
      ▼               ▼                                     ▼
 app/models/asr   app/models/translate               app/models/tts
  Whisper v3         NLLB-200                          MMS-TTS
 (speech→text)     (text→text)                        (text→speech)
```

## The two flows

Both flows end in the shared `_build()` step in `app/pipeline.py`.

**Audio in** (`translate_audio`)

1. `audio.decode_to_16k_mono` uses ffmpeg to turn the upload (webm/mp3/wav/…)
   into the 16 kHz mono float array Whisper expects.
2. `asr.transcribe` returns the text plus the detected language + confidence.
3. `_build`: if source ≠ target, `translate.translate` (NLLB) translates.
4. If "speak" is on, the text is synthesised (see **Speaking** below).

**Text in** (`translate_text`)

1. Source language comes from the request, or is guessed with `langdetect`.
2. Straight into `_build` (steps 3–4 above).

## Targets and Hinglish

`_resolve_target(code)` decides how to translate and speak a chosen "To" option:

- A normal language → translate to its NLLB code, speak with its MMS voice.
- **Hinglish** (`hi-Latn`) → translate to Hindi, **show** the text romanised
  (uroman, "Roman Hindi"), but **speak** Hindi.

So the pipeline keeps two versions of the translation: the *native* text (for
speech) and the *display* text (for the UI). They're the same for every target
except Hinglish.

## Speaking (script-aware TTS)

Each MMS voice only speaks its own script — the Hindi voice ignores Latin
letters. So for a non-Latin target, `tts.synthesize_segmented`:

1. splits the text into runs by script,
2. speaks Latin runs (English words, names) with the **English** voice and the
   rest with the **target** voice,
3. joins the clips.

This is why a name like "Inclusio" inside a Hindi sentence, or code-mixed
Hinglish, is spoken instead of dropped. Latin-script targets skip this and use a
single voice.

## Why three separate models

- **Whisper** is excellent at speech recognition and language detection, but its
  only translation direction is *to English*.
- **NLLB-200** fills that gap: any of its 200 languages to any other. This is
  what makes real Hindi → French (etc.) possible.
- **MMS-TTS** gives spoken output, one small model per language.

Keeping them as separate modules means each can be swapped without touching the
rest.

## Language codes

The same language has a different code in each stage. `app/languages.py` is the
single source of truth:

| Canonical | Whisper | NLLB (FLORES) | MMS (ISO 639-3) |
| --- | --- | --- | --- |
| `hi` | `hi` | `hin_Deva` | `hin` |
| `en` | `en` | `eng_Latn` | `eng` |

A language appears only if all three stages support it, so the UI can never
offer a combination that breaks mid-pipeline.

## Model loading and warmup

- `app/models/*` import torch / transformers / faster-whisper **inside** their
  functions and cache the loaded model with `functools.lru_cache`. So the web
  app and the test suite import cleanly without the multi-GB ML stack, and each
  model loads once then is reused.
- `app/warmup.py` loads Whisper, NLLB, and the English + Hindi voices in a
  **background thread at startup** (via the FastAPI lifespan), so the first real
  request is fast. Progress is exposed through `/api/health`. Set
  `DISABLE_WARMUP=1` to skip it (the tests do).

## Device selection

`config.resolve_device()` returns `mps` on Apple Silicon (with a CPU fallback
for unsupported ops), else `cpu`. Whisper runs on CPU via faster-whisper's int8
build; NLLB and MMS-TTS use the resolved torch device.

## Startup env defaults

`app/config.py` sets these (overridable) before torch/HF import:

- `PYTORCH_ENABLE_MPS_FALLBACK=1` — unsupported MPS ops fall back to CPU.
- `HF_HUB_DISABLE_XET=1` — the HF Xet transfer backend stalled downloads at 0
  bytes on some networks; classic HTTPS is reliable.

## Live speech preview (browser)

While recording, `web/app.js` runs the browser's `SpeechRecognition` to show
words live. This is a *preview only* — the authoritative transcript always comes
from the on-device Whisper model when you press Translate.

## Graceful degradation

If a TTS voice fails, the pipeline still returns the translated **text** and adds
a note, rather than failing the whole request.
