# Roadmap & ideas

Candidate features for future work. Not committed to — a menu to pick from.

## Near-term polish

- **Better Hinglish spelling.** uroman gives literal phonetics ("mem aapakaa").
  Use a proper Devanagari→Roman scheme (or ai4bharat IndicXlit) for natural
  "mein aapka".
- **Live-preview language.** It currently uses the browser locale. Let it follow
  a small "spoken language" hint or the most-likely language, so the live words
  match what's actually being said.
- **Speak numbers/symbols.** `synthesize_segmented` skips runs with no letters,
  so digits aren't voiced. Handle numbers per language.
- **Export / copy.** Buttons to copy the translation and download the audio WAV.

## Features

- **Hinglish as an input** (Roman Hindi typed) → transliterate to Devanagari →
  translate. Needs a Latin→Devanagari transliterator.
- **More languages.** Telugu, Urdu, Punjabi, Gujarati, Kannada, Malayalam, etc.
  (add rows in `app/languages.py` once all three stages support them).
- **Long audio / files.** Chunked transcription with timestamps; export subtitles
  (SRT/VTT).
- **History.** Save recent translations locally.

## Quality

- **Nicer TTS voice.** MMS is a bit robotic. Try Coqui **XTTS-v2** (supports
  Hindi, higher quality, optional voice cloning) — watch for `transformers`
  version conflicts, so maybe isolate it.
- **Accent fine-tuning.** Fine-tune Whisper on the user's own voice for the last
  mile of accent accuracy (the step beyond the `hints` box).
- **Real-time local transcription.** Stream mic audio to the backend over
  WebSocket and decode incrementally, replacing the browser preview with the
  on-device model. Heavier; needs VAD + chunking.

## Infrastructure

- **Docker** image for portability / running off-Mac.
- **GPU host** (Modal / Replicate / a server) for speed at scale.
- **Auth** if it's ever hosted for others.
- **CI** to run `pytest` on push.

## Known limitations (carry forward)

- Hinglish romanisation is rough (see near-term polish).
- Mixed-voice speech switches timbre between English and the target voice.
- Live preview is browser-based (cloud, Chrome-best) and language-fixed.
- Cyrillic/Arabic targets: embedded Latin is routed to the English voice, which
  is fine, but embedded *other* non-target scripts aren't specially handled.
- First startup downloads ~7 GB of models.
