# Development guide

## First-time setup

```bash
# Native arm64 Python 3.12 — NOT the system python3 (see docs/decisions.md)
uv venv .venv --python 3.12
uv pip install -p .venv/bin/python -r requirements.txt -r requirements-ml.txt -r requirements-dev.txt

# Download the models once (~7 GB)
.venv/bin/python scripts/download_models.py
```

## Run

```bash
./start.sh                 # preferred: venv + warmup + opens browser
# or, manually:
.venv/bin/python -m uvicorn app.main:app --reload
```

## Test

```bash
.venv/bin/python -m pytest              # fast unit tests, models mocked
.venv/bin/python scripts/e2e_check.py   # real end-to-end, writes samples/*.wav
```

- Unit tests never load real models: `tests/conftest.py` sets `DISABLE_WARMUP=1`
  and monkeypatches `asr.transcribe`, `translate.translate`, `tts.synthesize`,
  and `tts.romanize` with fast fakes. Keep those fakes' signatures in sync with
  the real functions.
- Lint (optional): `ruff check . && ruff format .`

## Project layout

```
app/
  main.py         FastAPI app: routes, lifespan (warmup), serves the UI
  config.py       settings + startup env defaults (MPS fallback, HF Xet off)
  languages.py    language registry + Hinglish + target/source helpers
  audio.py        ffmpeg decode -> 16k mono; encode WAV
  pipeline.py     orchestration: _resolve_target, _build, translate_text/audio
  warmup.py       background model preload + readiness state
  models/
    asr.py        Whisper large-v3 (faster-whisper)   + preload()
    translate.py  NLLB-200                             + preload()
    tts.py        MMS-TTS, synthesize_segmented, romanize + preload()
web/              index.html, styles.css, app.js (no build step)
scripts/          download_models.py, e2e_check.py
tests/            unit tests (models mocked)
docs/             architecture, api, usage, decisions, development, roadmap
```

## Common tasks

### Add a language

1. Add a `Language(...)` row in `app/languages.py` with its Whisper (ISO 639-1),
   NLLB (FLORES-200), and MMS (ISO 639-3) codes. Only add it if **all three**
   exist, or a stage will fail.
2. That's it — the UI dropdowns, translation, and TTS pick it up automatically.
   The voice downloads on first use (or add it to `warmup.DEFAULT_VOICES` /
   `scripts/download_models.py` to prefetch).

### Add an API field

Endpoints are in `app/main.py`; the work happens in `app/pipeline.py`. Keep the
response shape identical for text and audio so the UI stays simple.

### Change a model

Each model is isolated in `app/models/*.py` behind `lru_cache`. Swap the model id
in `app/config.py` or the loader, keeping the function signatures the same.

## Gotchas

Read [`decisions.md`](decisions.md) — especially the arm64/Rosetta Python issue,
the `HF_HUB_DISABLE_XET` download stall, the MMS native-script requirement, and
the `.gitignore` `/models/` anchoring. These have already cost time once.

## Git

- Committed directly to `main` in this project.
- Commit style: `type(scope): summary` (`feat`, `fix`, `docs`, `refactor`, …).
  Messages describe *what* changed. No AI/tool attribution.
- Never commit weights (ignored) or `.env` (secrets).
