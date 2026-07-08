"""Supported languages.

Each stage of the pipeline uses a different code for the same language:
  - Whisper (speech->text) uses ISO 639-1 ("hi")
  - NLLB (text translation) uses FLORES-200 ("hin_Deva")
  - MMS-TTS (text->speech) uses ISO 639-3 ("hin")

This registry keeps all of them in one place so the pipeline can look up the
right code for each step. A language only appears here if all three stages
support it, so the UI never offers something that will fail downstream.

Every MMS voice we ship speaks its own native script, and NLLB already outputs
that script, so no romanisation is needed. (The TTS layer still romanises
automatically for the rare voice whose tokenizer asks for it.)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    code: str  # canonical id used in the API and UI (ISO 639-1)
    name: str  # human-readable name
    whisper: str  # faster-whisper language code
    nllb: str  # NLLB FLORES-200 code
    mms: str  # MMS-TTS ISO 639-3 code


LANGUAGES: list[Language] = [
    Language("en", "English", "en", "eng_Latn", "eng"),
    Language("hi", "Hindi", "hi", "hin_Deva", "hin"),
    Language("es", "Spanish", "es", "spa_Latn", "spa"),
    Language("fr", "French", "fr", "fra_Latn", "fra"),
    Language("de", "German", "de", "deu_Latn", "deu"),
    Language("it", "Italian", "it", "ita_Latn", "ita"),
    Language("pt", "Portuguese", "pt", "por_Latn", "por"),
    Language("ru", "Russian", "ru", "rus_Cyrl", "rus"),
    Language("ar", "Arabic", "ar", "arb_Arab", "ara"),
    Language("bn", "Bengali", "bn", "ben_Beng", "ben"),
    Language("ta", "Tamil", "ta", "tam_Taml", "tam"),
    Language("mr", "Marathi", "mr", "mar_Deva", "mar"),
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


# Hinglish is a special output: Hindi translated, then written in Latin letters
# ("Roman Hindi") while still spoken as Hindi. It's a target option only.
HINGLISH = {"code": "hi-Latn", "name": "Hinglish (Roman Hindi)"}


def is_latin_script(lang: Language) -> bool:
    """True if the language is written in the Latin alphabet."""
    return lang.nllb.endswith("_Latn")


def is_valid_target(code: str | None) -> bool:
    """Valid 'To' options are the 12 languages plus Hinglish."""
    return code == HINGLISH["code"] or get(code) is not None


def target_list() -> list[dict]:
    """Options for the 'To' dropdown: the languages plus Hinglish."""
    return public_list() + [HINGLISH]
