# 🗣️ AI Translation Service

Speak or type in one language, get the translation as **text and spoken audio**
in another. Built for Hindi ↔ English first, with ten more languages included.

It runs three open models locally, chained into one pipeline:

| Stage | Model | Job |
| --- | --- | --- |
| Speech → text | **Whisper large-v3** (via faster-whisper) | Transcribe audio, detect the language |
| Text → text | **NLLB-200** | Translate between any two languages |
| Text → speech | **Meta MMS-TTS** | Say the translation out loud |

Whisper on its own can only translate *to English*. Adding NLLB is what makes
this a real **any-language → any-language** service.

---

## What you can do

- **Speak → translated audio.** Record from the mic (or upload a file), pick a
  target language, hear it spoken back.
- **Type → translated audio.** Type text, choose the language, get the
  translation plus a spoken version.
- **Auto language detection** for both speech and text. Audio mode shows only
  "To" and detects the spoken language for you; the detected language is filled
  into "From".
- **Live words while you record** — a fast in-browser preview shows what you're
  saying; the final transcript comes from the on-device Whisper model.
- **Hinglish output** — translate to **Roman Hindi** (shown in Latin letters,
  still spoken as Hindi).
- **Mixed English + Hindi spoken correctly** — English words or names inside a
  Hindi sentence are voiced (with the English voice) instead of being dropped.
- **Accent / vocabulary hints.** Give Whisper a few words you often say (names,
  places, jargon) to help it understand your accent — no training needed.

---

## Requirements

- **Apple Silicon Mac** (tested on M3) — uses Metal (MPS) for translation + TTS.
- **Python 3.11 or 3.12** (arm64 build). Python 3.14 does not yet have PyTorch
  wheels, so use 3.12.
- **ffmpeg** on your PATH (for decoding audio).
- **~8 GB free disk** for the models:
  Whisper ≈ 1.5 GB · NLLB ≈ 2.4 GB · PyTorch ≈ 1.5 GB · voices ≈ 0.7 GB.

> Tight on disk? Point `HF_HOME` in `.env` at an external drive, and the model
> downloads land there instead of your main disk.

---

## Setup

```bash
# 1. Create an arm64 virtual environment (Python 3.12)
uv venv .venv --python 3.12
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt        # web + audio (small, fast)
pip install -r requirements-ml.txt     # models: torch, transformers, ... (large)
pip install -r requirements-dev.txt    # test tooling

# 3. Download the models (~8 GB, one time)
python scripts/download_models.py

# 4. (Optional) copy the env template
cp .env.example .env
```

## Run

```bash
./start.sh
```

Runs the server with the project's virtualenv and opens
**http://localhost:8000**. On boot it **preloads the models** (Whisper + NLLB +
the English/Hindi voices) so the first translation is fast — the page shows a
"warming up" banner until they're ready.

> Always start with `./start.sh` (or `.venv/bin/python -m uvicorn app.main:app`).
> Launching with a system `python`/`uvicorn` gives `ModuleNotFoundError: No
> module named 'torch'`, because the ML packages live in `.venv`, not the
> system Python.

**Local vs cloud:** everything runs **on your machine**. Hugging Face is
contacted only the first time a model is downloaded (then it's cached on disk);
all transcription, translation, and speech happen locally with no network calls.

## Test

```bash
pytest                          # 21 fast tests — models mocked, no download needed
python scripts/e2e_check.py     # real end-to-end run with the actual models
```

The end-to-end check translates text to Hindi and runs a full
speech → translate → speech round-trip, saving the spoken output to `samples/`
so you can listen.

---

## Supported languages

English, Hindi, Spanish, French, German, Italian, Portuguese, Russian, Arabic,
Bengali, Tamil, Marathi — plus **Hinglish (Roman Hindi)** as an output option.

A language is only listed if **all three** stages (speech, translation, speech
output) support it, so the UI never offers something that fails halfway.

## Getting the best results with your accent

1. Whisper large-v3 already handles Indian / Hindi accents well — just try it.
2. If it mishears specific words, put them in the **hints** box (names, places,
   terms you use). This biases recognition without any training.
3. For the last mile you could fine-tune Whisper on your own voice — a separate,
   larger project not included here.

## Limitations

- **Hinglish** (Hindi + English mixed in one sentence) can confuse the language
  detector. Set the source language manually when that happens.
- **MMS-TTS voices** are clear but a little robotic. Each voice speaks its own
  native script (Devanagari, Cyrillic, Arabic, …), which NLLB already produces.
- CPU/MPS inference: fine for short clips; long audio takes proportionally longer.

---

## How it fits together

```
  ┌────────┐   audio   ┌─────────────┐ text ┌──────────┐ text ┌──────────┐ audio
  │  Web   │──────────▶│  Whisper    │─────▶│  NLLB-200│─────▶│ MMS-TTS  │──────▶ result
  │  UI    │   /text   │ (transcribe)│      │(translate)│      │ (speak)  │
  └────────┘           └─────────────┘      └──────────┘      └──────────┘
        typed text ─────────────────────────────▲
```

See [`docs/architecture.md`](docs/architecture.md) for detail,
[`docs/api.md`](docs/api.md) for the HTTP API, and
[`docs/usage.md`](docs/usage.md) for a walk-through.

## Project layout

```
app/
  main.py         FastAPI app: API + serves the UI
  config.py       settings (models, device, limits)
  languages.py    the supported-language registry
  audio.py        decode uploads / encode WAV (ffmpeg)
  pipeline.py     ties the three models together
  models/
    asr.py        Whisper large-v3 (speech → text)
    translate.py  NLLB-200 (text → text)
    tts.py        MMS-TTS (text → speech)
web/              the UI (plain HTML/CSS/JS, no build step)
scripts/          model downloader
tests/            fast tests (models mocked)
docs/             architecture, API, usage
```

## License

MIT — see [LICENSE](LICENSE).
