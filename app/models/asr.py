"""Speech-to-text with Whisper large-v3 (via faster-whisper).

faster-whisper is an optimised build of the same OpenAI Whisper large-v3 model.
It is smaller on disk and fast on CPU, and it conveniently reports the language
it detected, which the pipeline needs to drive translation.
"""

from functools import lru_cache

from app import config


@lru_cache(maxsize=1)
def _model():
    from faster_whisper import WhisperModel

    # int8 keeps the memory and disk footprint small while staying accurate.
    return WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")


def transcribe(
    samples,
    initial_prompt: str | None = None,
    language: str | None = None,
) -> dict:
    """Transcribe a 16 kHz mono float array.

    `initial_prompt` biases decoding toward names/words you often say — the
    practical way to tune Whisper to your own accent and vocabulary.
    `language` forces the spoken language; leave it None to auto-detect.
    """
    model = _model()
    segments, info = model.transcribe(
        samples,
        language=language,
        initial_prompt=initial_prompt or None,
        vad_filter=True,
        beam_size=5,
    )
    text = "".join(segment.text for segment in segments).strip()
    return {
        "text": text,
        "language": info.language,
        "language_probability": round(float(info.language_probability), 3),
    }


def preload() -> None:
    """Load the model into memory now, so the first request isn't slow."""
    _model()
