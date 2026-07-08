# HTTP API

Base URL: `http://localhost:8000`

All responses are JSON. Errors use standard HTTP codes with a `{"detail": "..."}`
body.

---

## `GET /api/health`

Liveness check.

```json
{ "status": "ok" }
```

---

## `GET /api/languages`

The languages offered in the dropdowns.

```json
{
  "languages": [
    { "code": "en", "name": "English" },
    { "code": "hi", "name": "Hindi" }
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
| `target_lang` | string | required, e.g. `"hi"` |
| `source_lang` | string \| null | optional; auto-detected if omitted |
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

`audio` is `null` when `speak` is false or no voice is available (a reason is
added to `notes`).

**Errors:** `400` for empty text or an unknown language code.

---

## `POST /api/translate/audio`

Transcribe speech, translate it, optionally speak the result.

**Request (multipart/form-data)**

| Field | Type | Notes |
| --- | --- | --- |
| `file` | file | required; any browser/ffmpeg audio format |
| `target_lang` | string | required |
| `source_lang` | string | optional; Whisper auto-detects if omitted |
| `hints` | string | optional; accent/vocabulary bias for Whisper |
| `speak` | bool | default `true` |

**Response**

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

# Audio: a clip -> English text + speech
curl -s localhost:8000/api/translate/audio \
  -F file=@clip.wav -F target_lang=en -F hints="Nitin, Bengaluru"
```
