"""Supported languages.

Each stage of the pipeline uses a different code for the same language:
  - Whisper (speech->text) uses ISO 639-1 ("hi")
  - NLLB (text translation) uses FLORES-200 ("hin_Deva")
  - MMS-TTS (text->speech) uses ISO 639-3 ("hin")

This registry keeps all of them in one place so the pipeline can look up the
right code for each step. A language only appears here if all three stages
support it, so the UI never offers something that will fail downstream.

`uroman` marks languages whose script must be romanised before MMS-TTS.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    code: str  # canonical id used in the API and UI (ISO 639-1)
    name: str  # human-readable name
    whisper: str  # faster-whisper language code
    nllb: str  # NLLB FLORES-200 code
    mms: str  # MMS-TTS ISO 639-3 code
    uroman: bool  # TTS input must be romanised first


LANGUAGES: list[Language] = [
    Language("en", "English", "en", "eng_Latn", "eng", False),
    Language("hi", "Hindi", "hi", "hin_Deva", "hin", True),
    Language("es", "Spanish", "es", "spa_Latn", "spa", False),
    Language("fr", "French", "fr", "fra_Latn", "fra", False),
    Language("de", "German", "de", "deu_Latn", "deu", False),
    Language("it", "Italian", "it", "ita_Latn", "ita", False),
    Language("pt", "Portuguese", "pt", "por_Latn", "por", False),
    Language("ru", "Russian", "ru", "rus_Cyrl", "rus", True),
    Language("ar", "Arabic", "ar", "arb_Arab", "ara", True),
    Language("bn", "Bengali", "bn", "ben_Beng", "ben", True),
    Language("ta", "Tamil", "ta", "tam_Taml", "tam", True),
    Language("mr", "Marathi", "mr", "mar_Deva", "mar", True),
]

_BY_CODE = {lang.code: lang for lang in LANGUAGES}
_BY_WHISPER = {lang.whisper: lang for lang in LANGUAGES}


def get(code: str | None) -> Language | None:
    """Look up a language by its canonical code."""
    if not code:
        return None
    return _BY_CODE.get(code)


def get_by_whisper(whisper_code: str | None) -> Language | None:
    """Look up a language by the code Whisper reports."""
    if not whisper_code:
        return None
    return _BY_WHISPER.get(whisper_code)


def public_list() -> list[dict]:
    """The list handed to the UI dropdowns."""
    return [{"code": lang.code, "name": lang.name} for lang in LANGUAGES]
