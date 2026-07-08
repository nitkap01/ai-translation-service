"""The translation pipeline — ties the three models together.

Two entry points:
  - translate_text:  text  -> translate -> (optional) speak
  - translate_audio: audio -> transcribe -> translate -> (optional) speak

Both return the same shape of result so the UI can handle them the same way.

The "target" can be one of the 12 languages or Hinglish. Hinglish translates to
Hindi, shows the text in Latin letters (Roman Hindi), but still speaks Hindi.
"""

import base64

from app import audio, languages
from app.models import asr, tts
from app.models import translate as mt


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


def _resolve_target(target_code: str) -> dict:
    """Work out how to translate and speak for a given 'To' option."""
    if target_code == languages.HINGLISH["code"]:
        hindi = languages.get("hi")
        return {
            "nllb": hindi.nllb,      # translate to Hindi
            "mms": hindi.mms,        # speak Hindi
            "romanize": True,        # but show the text in Latin letters
            "latin_script": False,   # spoken script is not Latin -> segment voices
            "name": "Hinglish",
        }
    lang = languages.get(target_code)
    return {
        "nllb": lang.nllb,
        "mms": lang.mms,
        "romanize": False,
        "latin_script": languages.is_latin_script(lang),
        "name": lang.name,
    }


def _speak(native_text: str, target: dict) -> tuple[str | None, str | None]:
    """Best-effort text-to-speech. Returns (data_uri, note).

    Uses the native-script text (so pronunciation is right, even for Hinglish).
    For a non-Latin target we speak each script with its own voice so embedded
    English words / names aren't dropped.
    """
    if not native_text.strip():
        return None, None
    try:
        if target["latin_script"]:
            samples, sample_rate = tts.synthesize(native_text, target["mms"])
        else:
            samples, sample_rate = tts.synthesize_segmented(native_text, target["mms"])
        wav = audio.encode_wav(samples, sample_rate)
        data_uri = "data:audio/wav;base64," + base64.b64encode(wav).decode("ascii")
        return data_uri, None
    except Exception as exc:  # noqa: BLE001 - degrade gracefully, never crash
        return None, f"Speech unavailable for {target['name']}: {exc}"


def _build(source_text: str, source, target_code: str, speak: bool) -> dict:
    """Shared tail: translate source_text into the target and optionally speak."""
    target = _resolve_target(target_code)
    if source.nllb == target["nllb"]:
        native = source_text.strip()
    else:
        native = mt.translate(source_text, source.nllb, target["nllb"])

    # What the user reads. Hinglish shows Roman Hindi; everything else is native.
    display = tts.romanize(native) if target["romanize"] else native

    result = {
        "source_text": source_text.strip(),
        "source_lang": source.code,
        "target_text": display,
        "target_lang": target_code,
        "audio": None,
        "notes": [],
    }
    if speak:
        data_uri, note = _speak(native, target)
        result["audio"] = data_uri
        if note:
            result["notes"].append(note)
    return result


def translate_text(
    text: str,
    target_lang: str,
    source_lang: str | None = None,
    speak: bool = True,
) -> dict:
    """Translate typed text and optionally speak the result."""
    source_code = source_lang if languages.get(source_lang) else detect_text_language(text)
    source = languages.get(source_code)
    return _build(text, source, target_lang, speak)


def translate_audio(
    data: bytes,
    target_lang: str,
    source_lang: str | None = None,
    hints: str | None = None,
    speak: bool = True,
) -> dict:
    """Transcribe speech, translate it, and optionally speak the result."""
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

    result = _build(transcript, source, target_lang, speak)
    result["source_lang_confidence"] = asr_out["language_probability"]
    result["notes"] = notes + result["notes"]
    return result
