# Decisions & gotchas

Why things are the way they are, and the traps we already hit. Read this before
changing the model layer, the environment, or `.gitignore`.

## Environment

- **This Mac is Apple Silicon (M3), but the shell runs under Rosetta**, so
  `uname -m` prints `x86_64` and the system `python3` is an x86_64 build (3.14,
  which has no PyTorch wheels). ML deps must use a **native arm64 Python**. The
  project venv `.venv` is built on arm64 Python 3.12. Always use
  `.venv/bin/python` (or `./start.sh`). This is the #1 cause of confusing errors
  like `ModuleNotFoundError: No module named 'torch'` — the code is fine, the
  interpreter is wrong.

- **`HF_HUB_DISABLE_XET=1`** is set in `app/config.py`. Hugging Face's newer Xet
  transfer backend stalled downloads at 0 bytes on this network (process alive,
  no progress). Classic HTTPS downloads work fine. If downloads ever hang,
  confirm this is set.

- **`PYTORCH_ENABLE_MPS_FALLBACK=1`** is set in `app/config.py` so unsupported
  Apple-GPU ops fall back to CPU instead of erroring.

## Model choices

- **ASR: `faster-whisper` large-v3**, not the raw `transformers` whisper. It's
  the same model, but ~1.5 GB (vs ~3 GB), fast on CPU (int8), and it cleanly
  reports the detected language + confidence, which the pipeline needs. Whisper
  runs on CPU; NLLB and TTS use MPS.

- **Translation: NLLB-200-distilled-600M.** Whisper alone only translates *to
  English*; NLLB does any-language → any-language, which is the whole point.

- **TTS: Meta MMS-TTS** (one small VITS model per language). Chosen because it
  stays on the same `transformers`/torch runtime (no dependency conflicts) and
  each voice is small.

## TTS: the two bugs we hit

1. **uroman is (mostly) not needed.** MMS voices for our languages report
   `tokenizer.is_uroman == False` and expect their **native script**
   (Devanagari, Cyrillic, …). NLLB already outputs that script. We first
   romanised Hindi with uroman → the tokenizer produced **zero tokens** → VITS
   crashed (`narrow(): length must be non-negative` on CPU, `numel overflow` on
   MPS). Fix: only romanise when `tokenizer.is_uroman` is true (which, for the
   shipped languages, is never).

2. **A voice drops any script it doesn't know.** The Hindi voice silently
   dropped the Latin word "Inclusio" from `Inclusio में आपका स्वागत है`, so only
   half the sentence was spoken. Fix: `tts.synthesize_segmented` splits text by
   script and speaks each run with the right voice (Latin → English voice), then
   joins the clips. This also enables Hinglish/code-mixed speech.

## Hinglish

Implemented as a **target-only** pseudo-language `hi-Latn`: translate to Hindi
(Devanagari), **display** it romanised via uroman ("Roman Hindi"), but **speak**
the Devanagari. Romanisation is uroman's literal phonetic spelling — readable but
rough ("mem aapakaa" rather than "mein aapka"). Improving this is on the roadmap.

## Live speech preview

The live words while recording use the **browser's** `SpeechRecognition` (fast,
but cloud-backed and best in Chrome). It's a preview only; the real transcript is
always the local Whisper model. This is the one non-local piece, and it's
optional (degrades to nothing if unsupported).

## Warmup

Models are preloaded at startup in a background thread (`app/warmup.py`), not on
the first request, so the first translation isn't slow. `/api/health` reports
readiness; the UI disables Translate until ready. Tests set `DISABLE_WARMUP=1`.

## .gitignore trap (already bit us)

A `models/` rule (meant for downloaded weights) also matched the **`app/models/`
source package**, so `asr.py`/`translate.py`/`tts.py` were silently left out of
two commits — the pushed repo was missing its core code. The rule is now
`/models/` (root-anchored). **Lesson: anchor directory ignores with a leading
slash**, and after committing, sanity-check `git ls-files app/` if a whole
folder looks absent.

## Disk

Model weights total ~7 GB in `~/.cache/huggingface`. Set `HF_HOME` to an
external drive if the main disk is tight. Never commit weights (`/models/`,
`*.bin`, `*.safetensors` are ignored).
