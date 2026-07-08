# Usage walk-through

## Start the app

```bash
./start.sh
```

It launches the server with the project's virtualenv, preloads the models, and
opens http://localhost:8000. A **"Warming up models"** banner shows until the
models are loaded (~20–30s, first start only); Translate is disabled until then.

## Translate speech

1. Click the **Speak / upload** tab. (Only the **To** language is shown — the
   spoken language is detected for you.)
2. Press **● Record** and talk. Words appear **live** as you speak. Press
   **■ Stop**. (Or **Upload file**.)
3. Pick the **To** language (e.g. English).
4. Keep **Speak result** on to hear it back.
5. Press **Translate**.

You'll see what was heard, the detected language with a confidence score, the
translation, and an audio player that plays automatically. The detected language
is filled into **From** for reference.

### Helping with your accent

If a name or word is misheard, type the words you use into the
**Accent / vocabulary hints** box before translating — for example
`Nitin, Bengaluru, Inclusio`. Whisper uses them as a hint and gets those words
right more often.

## Translate typed text

1. Click the **Type text** tab.
2. Type your text.
3. Choose **From** (or leave it on Auto-detect) and **To**.
4. Press **Translate** — you get the translated text and its spoken version.

## Hinglish

Pick **Hinglish (Roman Hindi)** as the **To** language. You get the translation
written in Latin letters (e.g. `aapka swagat hai`) but spoken as Hindi. Handy for
reading Hindi without knowing Devanagari.

## Mixed English + Hindi

English words or names inside a Hindi result (e.g. `Inclusio में आपका स्वागत है`)
are spoken with the English voice, so nothing is dropped from the audio.

## Tips

- The **live words** while recording come from your browser and are a quick
  preview; the final, accurate transcript is from the on-device Whisper model.
- Turn **Speak result** off for text-only output (a bit faster).
- Only the first request after startup is slow (models load once); the warmup
  banner hides that from you.

## Changing the models or device

Copy `.env.example` to `.env` (loaded by `start.sh`). Useful settings:

- `DEVICE=cpu` to force CPU, `mps` for Apple GPU, `auto` to choose.
- `HF_HOME=/Volumes/External/hf-cache` to keep downloaded models off your main
  disk.
- `HF_TOKEN=...` for faster, rate-limit-free model downloads.
- `MAX_AUDIO_MB` to raise/lower the upload size limit.
- `PORT` to run on a different port.
