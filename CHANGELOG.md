# Changelog

## 0.2.0 — 2026-07-08

Added
- **Startup model preload** (`app/warmup.py`) in a background thread; `/api/health`
  reports readiness; the UI disables Translate and shows a warmup banner until
  ready — so the first request is fast.
- **`start.sh`** launcher that uses the project venv (prevents "No module named
  'torch'"), loads `.env`, and opens the browser.
- **Hinglish output** target (`hi-Latn`): Hindi translation shown as Roman Hindi,
  spoken as Hindi.
- **Script-aware TTS** (`tts.synthesize_segmented`): mixed-script text (e.g. an
  English name in a Hindi sentence) is spoken by voicing each script with the
  right voice, instead of dropping the foreign words.
- **Live speech preview** while recording (browser `SpeechRecognition`).
- **Auto-detect UX**: detected language fills "From"; audio mode shows only "To".
- **White/black light theme.**
- Docs: `decisions.md`, `development.md`, `roadmap.md`, this changelog; updated
  `architecture.md`, `api.md`, `usage.md`, README.

Fixed
- MMS-TTS crashed / dropped Hindi because we romanised text the voice expected in
  native Devanagari. Now we only romanise when `tokenizer.is_uroman` is true.
- The Hindi voice silently dropped Latin words (e.g. "Inclusio"). Fixed by
  script-segmented synthesis.
- **`.gitignore`**: `models/` also matched the `app/models/` source package, so
  the model wrappers were never committed. Rule anchored to `/models/`; package
  restored to version control.

Changed
- `/api/languages` now returns `{languages, targets}` (targets include Hinglish).
- `config.py` sets `HF_HUB_DISABLE_XET=1` and `PYTORCH_ENABLE_MPS_FALLBACK=1`.

## 0.1.0 — initial

- Speech + text translation with spoken output: Whisper large-v3 (faster-whisper)
  → NLLB-200 → MMS-TTS.
- FastAPI backend + dependency-free web UI (record / upload / type).
- 12 languages including Hindi; language registry keeps Whisper/NLLB/MMS codes
  consistent.
- Accent/vocabulary hints for Whisper; unit tests (models mocked); model
  downloader and end-to-end check scripts.
