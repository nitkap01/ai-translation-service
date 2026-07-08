"""The translation pipeline — ties the three models together.

Two entry points:
  - translate_text:  text  -> translate -> (optional) speak
  - translate_audio: audio -> transcribe -> translate -> (optional) speak

Both return the same shape of result so the UI can handle them the same way.
"""

import base64

from app import audio, languages
from app.models import asr
from app.models import translate as mt
from app.models import tts


def _speak(text: str, target_code: str) -> tuple[str | None, str | None]:
    """Best-effort text-to-speech. Returns (data_uri, note).

    If a voice isn't available we return no audio plus a short note instead of
    failing the whole request — the translated text is still useful.
    """
    lang = languages.get(target_code)
    if not text.strip():
        return None, None
    try:
        samples, sample_rate = tts.synthesize(text, lang.mms, uroman=lang.uroman)
        wav = audio.encode_wav(samples, sample_rate)
        data_uri = "data:audio/wav;base64," + base64.b64encode(wav).decode("ascii")
        return data_uri, None
    except Exception as exc:  # noqa: BLE001 - degrade gracefully, never crash
        return None, f"Speech unavailable for {lang.name}: {exc}"


def detect_text_language(text: str) -> str:
    """Best-effort guess of what language some typed text is in.

    Returns a supported canonical code, defaulting to English when unsure.
    """
    try:
        from langdetect import DetectorFactory, detect

        DetectorFactory.seed = 0
        guess = detect(text)
        # langdetect uses ISO 639-1, same as our canonical codes for this set.
        if languages.get(guess):
            return guess
    except Exception:
        pass
    return "en"


def translate_text(
    text: str,
    target_lang: str,
    source_lang: str | None = None,
    speak: bool = True,
) -> dict:
    """Translate typed text and optionally speak the result."""
    target = languages.get(target_lang)
    source_code = source_lang if languages.get(source_lang) else detect_text_language(text)
    source = languages.get(source_code)

    if source.code == target.code:
        target_text = text.strip()
    else:
        target_text = mt.translate(text, source.nllb, target.nllb)

    result = {
        "source_text": text.strip(),
        "source_lang": source.code,
        "target_text": target_text,
        "target_lang": target.code,
        "audio": None,
        "notes": [],
    }
    if speak:
        data_uri, note = _speak(target_text, target.code)
        result["audio"] = data_uri
        if note:
            result["notes"].append(note)
    return result


def translate_audio(
    data: bytes,
    target_lang: str,
    source_lang: str | None = None,
    hints: str | None = None,
    speak: bool = True,
) -> dict:
    """Transcribe speech, translate it, and optionally speak the result."""
    target = languages.get(target_lang)
    samples = audio.decode_to_16k_mono(data)

    forced = languages.get(source_lang)
    asr_out = asr.transcribe(
        samples,
        initial_prompt=hints,
        language=forced.whisper if forced else None,
    )
    transcript = asr_out["text"]

    detected = languages.get_by_whisper(asr_out["language"])
    notes: list[str] = []
    if detected is None:
        # Whisper heard a language we don't translate; fall back to English.
        source = languages.get("en")
        notes.append(
            f"Detected language '{asr_out['language']}' isn't supported; "
            "assuming English for translation."
        )
    else:
        source = detected

    if source.code == target.code:
        target_text = transcript
    else:
        target_text = mt.translate(transcript, source.nllb, target.nllb)

    result = {
        "source_text": transcript,
        "source_lang": source.code,
        "source_lang_confidence": asr_out["language_probability"],
        "target_text": target_text,
        "target_lang": target.code,
        "audio": None,
        "notes": notes,
    }
    if speak:
        data_uri, note = _speak(target_text, target.code)
        result["audio"] = data_uri
        if note:
            result["notes"].append(note)
    return result
