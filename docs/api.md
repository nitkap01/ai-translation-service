# HTTP API

Base URL: `http://localhost:8000`

All responses are JSON. Errors use standard HTTP codes with a `{"detail": "..."}`
body.

---

## `GET /api/health`

Liveness plus **model warmup** state. The UI polls this on load and keeps the
Translate button disabled until `ready` is `true`.

```json
{ "status": "ok", "ready": false, "progress": "loading translator (NLLB-200)", "error": null }
```

| Field | Meaning |
| --- | --- |
| `status` | always `"ok"` if the server is up |
| `ready` | `true` once all startup models are loaded |
| `progress` | human-readable current step (or `"ready"`, `"error"`) |
| `error` | a string if warmup failed, else `null` |

---

## `GET /api/languages`

Options for the dropdowns. `languages` are valid **sources**; `targets` are the
same list **plus Hinglish**.

```json
{
  "languages": [
    { "code": "en", "name": "English" },
    { "code": "hi", "name": "Hindi" }
  ],
  "targets": [
    { "code": "en", "name": "English" },
    { "code": "hi", "name": "Hindi" },
    { "code": "hi-Latn", "name": "Hinglish (Roman Hindi)" }
  ]
}
```

---

## `POST /api/translate/text`

Translate typed text, optionally with spoken output.

**Request (JSON)**

| Field | Type | Notes |
| --- | --- | --- |
| `text` | string | required |
| `target_lang` | string | required; a language code or `"hi-Latn"` (Hinglish) |
| `source_lang` | string \| null | optional; auto-detected (langdetect) if omitted |
| `speak` | bool | default `true` |

**Response**

```json
{
  "source_text": "hello",
  "source_lang": "en",
  "target_text": "नमस्ते",
  "target_lang": "hi",
  "audio": "data:audio/wav;base64,UklGRi...",
  "notes": []
}
```

- `audio` is a base64 WAV data URI, or `null` when `speak` is false or no voice
  is available (a reason is then added to `notes`).
- For `target_lang: "hi-Latn"`, `target_text` is Roman Hindi but `audio` speaks
  Hindi.

**Errors:** `400` for empty text or an unknown language code.

---

## `POST /api/translate/audio`

Transcribe speech, translate it, optionally speak the result.

**Request (multipart/form-data)**

| Field | Type | Notes |
| --- | --- | --- |
| `file` | file | required; any browser/ffmpeg audio format (webm, mp3, wav, m4a…) |
| `target_lang` | string | required; code or `"hi-Latn"` |
| `source_lang` | string | optional; Whisper auto-detects if omitted |
| `hints` | string | optional; accent/vocabulary bias for Whisper (`initial_prompt`) |
| `speak` | bool | default `true` |

**Response** — same as text, plus `source_lang_confidence` (0–1) from Whisper.

```json
{
  "source_text": "नमस्ते दुनिया",
  "source_lang": "hi",
  "source_lang_confidence": 0.98,
  "target_text": "Hello world",
  "target_lang": "en",
  "audio": "data:audio/wav;base64,UklGRi...",
  "notes": []
}
```

**Errors:** `400` empty file / unknown language, `413` file over `MAX_AUDIO_MB`.

---

## Examples

```bash
# Text: English -> Hindi, with speech
curl -s localhost:8000/api/translate/text \
  -H 'Content-Type: application/json' \
  -d '{"text":"Good morning","target_lang":"hi"}'

# Text: English -> Hinglish (Roman Hindi text, Hindi audio)
curl -s localhost:8000/api/translate/text \
  -H 'Content-Type: application/json' \
  -d '{"text":"Welcome to Inclusio","target_lang":"hi-Latn"}'

# Audio: a clip -> English text + speech, with accent hints
curl -s localhost:8000/api/translate/audio \
  -F file=@clip.wav -F target_lang=en -F hints="Nitin, Bengaluru"
```
