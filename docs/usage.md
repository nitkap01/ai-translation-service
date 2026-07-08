# Usage walk-through

## Start the app

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Open http://localhost:8000.

## Translate speech

1. Click the **Speak / upload** tab.
2. Press **● Record**, talk, press **■ Stop**. (Or **Upload file**.)
3. Pick the **To** language (e.g. English).
4. Leave **From** on *Auto-detect* — Whisper figures out you spoke Hindi.
5. Keep **Speak result** on to hear it back.
6. Press **Translate**.

You'll see what was heard, the detected language with a confidence score, the
translation, and an audio player that plays automatically.

### Helping with your accent

If a name or word is misheard, type the words you use into the
**Accent / vocabulary hints** box before translating — for example
`Nitin, Bengaluru, Inclusio`. Whisper uses them as a hint and gets those words
right more often.

## Translate typed text

1. Click the **Type text** tab.
2. Type your text.
3. Choose **From** and **To** (or leave **From** on Auto-detect).
4. Press **Translate** — you get the translated text and its spoken version.

## Tips

- **Hinglish** (mixing Hindi and English) can fool auto-detect. If the result
  looks off, set **From** manually.
- Turn **Speak result** off for text-only output (a bit faster).
- The first translation after starting the server is slower because the models
  load into memory once; later ones are quick.

## Changing the models or device

Everything is configurable via `.env` (copy from `.env.example`):

- `DEVICE=cpu` to force CPU, `mps` for Apple GPU, `auto` to choose.
- `HF_HOME=/Volumes/External/hf-cache` to keep downloaded models off your main
  disk.
- `MAX_AUDIO_MB` to raise/lower the upload size limit.
